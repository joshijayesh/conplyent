import os
import logging
from glob import glob
from functools import wraps
from shutil import rmtree
from threading import Thread

from ._msg import MSG, MSGType
from ._general import SynchronizedDict
from .exceptions import exception_to_str
from .console_executor import ConsoleExecutor

MSG_PORT = {}
JOBS = SynchronizedDict()
logger = logging.getLogger()


def register_slave_method(func):
    function_name = func.__name__

    @wraps(func)
    def register_wrapper(zp, idx, *args, **kwargs):
        request = "{} {} {}".format(function_name, args, kwargs)
        logger.info("Received Request: {}".format(request))
        zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=request))

        try:
            exit_code = func(zp, idx, *args, **kwargs)
        except Exception:
            update_master(zp, idx, exception_to_str())
            exit_code = 1

        zp.send_msg(MSG(MSGType.COMPLETE, request_id=idx, exit_code=exit_code))

    MSG_PORT[function_name] = register_wrapper
    return register_wrapper


def register_slave_method_bg(func):
    function_name = func.__name__

    def bg_slave(zp, idx, *args, **kwargs):
        request = "{} {} {}".format(function_name, args, kwargs)
        logger.info("Received Request: {}".format(request))
        zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=request))

        try:
            exit_code = func(zp, idx, *args, **kwargs)
        except Exception:
            update_master(zp, idx, exception_to_str())
            exit_code = 1

        zp.send_msg(MSG(MSGType.COMPLETE, request_id=idx, exit_code=exit_code))
        JOBS[function_name] = None

    @wraps(func)
    def register_wrapper(zp, idx, *args, **kwargs):
        t = Thread(target=bg_slave, args=(zp, idx, args, kwargs,), daemon=True)
        JOBS[function_name] = (args, kwargs)
        t.start()

    MSG_PORT[function_name] = register_wrapper
    return register_wrapper


def update_master(zp, idx, string):
    zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=string))


@register_slave_method
def cd(zp, idx, dest):
    try:
        os.chdir(dest)
        update_master(zp, idx, os.getcwd())
        return 0
    except FileNotFoundError:
        update_master(zp, idx, "{}: No such file or directory.".format(dest))
        return -1


@register_slave_method
def ls(zp, idx):
    name_list = "Listing of Directory {}:\n\n".format(os.getcwd())
    dir_list = []
    file_list = []
    for file in glob("./*"):
        if(os.path.isdir(file)):
            dir_list.append(file)
        else:
            file_list.append(file)
    name_list += "\n".join(["d {}".format(i) for i in dir_list]) + "".join(["\nf {}".format(i) for i in file_list])
    update_master(zp, idx, name_list)
    return 0


@register_slave_method
def cwd(zp, idx):
    update_master(zp, idx, os.getcwd())
    return 0


@register_slave_method
def mkdir(zp, idx, path, *args):
    if(not(os.path.exists(path))):
        os.mkdir(path, *args)
        update_master(zp, idx, "Created directory: {}".format(path))
        return 0
    else:
        update_master(zp, idx, "Directory or File {} already exists".format(path))
        return -1


@register_slave_method
def rm(zp, idx, path, recursive=False):
    if(os.path.exists(path)):
        if((os.path.isdir(path) and recursive) or (os.path.isdir(path) and not(os.listdir(path)))):
            rmtree(path)
            update_master(zp, idx, "Removed directory {}".format(path))
            return 0
        elif(not(os.path.isdir(path))):
            os.remove(path)
            update_master(zp, idx, "Removed file {}".format(path))
            return 0
        else:
            update_master(zp, idx, "Non-Empty Directory... Pass recursive if you're certain")
            return -1
    else:
        update_master(zp, idx, "Directory or File {} doesn't exist?".format(path))
        return -1


@register_slave_method
def cat(zp, idx, path):
    if(os.path.exists(path) and not(os.path.isdir(path))):
        buffer = ""
        with open(path, 'r') as file:
            update_master(zp, idx, "Contents of {}".format(path))
            for line in file:
                buffer += line
                if(len(buffer) >= 1024):
                    update_master(zp, idx, buffer)
                    buffer = ""
        return 0
    else:
        update_master(zp, idx, "Unknown file: {}".format(path))
        return -1


@register_slave_method
def wrfile(zp, idx, path, data, append=False):
    if(os.path.exists(path) and os.path.isdir(path)):
        update_master(zp, idx, "wrfile: Path exists as a directory.")
        return -1
    else:
        with open(path, "a" if append else "w") as file:
            if(append):
                file.seek(0, 2)
            file.write(data)
        update_master(zp, idx, "Finished writing data to {}".format(path))
        return 0


@register_slave_method
def touch(zp, idx, path):
    if(os.path.exists(path) and os.path.isdir(path)):
        update_master(zp, idx, "wrfile: Path exists as a directory.")
        return -1
    else:
        file = open(path, "ab+" if os.path.exists(path) else "wb+")
        file.write(b" ")
        file.flush()
        file.seek(-1, 2)
        file.truncate()
        file.close()
        update_master(zp, idx, "Touched {}".format(path))
        return 0


@register_slave_method
def jobs(zp, idx):
    for key, value in JOBS.items():
        print("{}: {}".format(key, value))


@register_slave_method
def exec(zp, idx, cmd):
    m_executor = ConsoleExecutor(cmd)
    for line in m_executor.read_output():
        if(line is not None):
            update_master(zp, idx, line.rstrip("\r\n"))
    return 0
