import os
import logging
from glob import glob
from functools import wraps
from shutil import rmtree
from threading import Thread
from zmq import Again

from ._zmq_wrapper import ZMQPair
from ._msg import MSGType, MSG
from ._general import SynchronizedDict
from .exceptions import exception_to_str
from .console_executor import ConsoleExecutor


MSG_PORT = {}
JOBS = SynchronizedDict()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def start():
    zp = ZMQPair()
    zp.bind()
    idx = 0

    while(True):
        msg = zp.recv_msg()
        try:
            if(msg.type == MSGType.COMMAND):
                zp.send_msg(MSG(MSGType.ACKNOWLEDGE, request_id=idx))
                MSG_PORT[msg.cmd_id](zp, idx, *msg.args, **msg.kwargs)
                idx = (idx + 1) % 0xFFFFFFFF
            elif(msg.type == MSGType.SYNC):
                zp.send_msg(MSG(MSGType.SYNC, args=(list(MSG_PORT.keys()),)))
        except Again:
            logger.info("Lost connection with host...")


def register_executor_method(func):
    function_name = func.__name__

    @wraps(func)
    def register_wrapper(zp, idx, *args, **kwargs):
        request = "{} {} {}".format(function_name, args, kwargs)
        logger.info("Received Request: {}".format(request))
        zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=request))

        try:
            exit_code = func(zp, idx, *args, **kwargs)
        except Exception:
            update_client(zp, idx, exception_to_str())
            exit_code = 1

        zp.send_msg(MSG(MSGType.COMPLETE, request_id=idx, exit_code=exit_code))

    MSG_PORT[function_name] = register_wrapper
    return register_wrapper


def register_executor_method_bg(func):
    function_name = func.__name__

    @wraps(func)
    def bg_server(zp, idx, args, kwargs):
        print("NAME, ARGS {}, kwargs {}".format(args, kwargs))
        request = "{} {} {}".format(function_name, args, kwargs)
        logger.info("Received BG Request: {}".format(request))
        zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=request))

        try:
            exit_code = func(zp, idx, *args, **kwargs)
        except Exception:
            update_client(zp, idx, exception_to_str())
            exit_code = 1

        zp.send_msg(MSG(MSGType.COMPLETE, request_id=idx, exit_code=exit_code))
        JOBS[idx] = None

    @wraps(func)
    def register_wrapper(zp, idx, *args, **kwargs):
        t = Thread(target=bg_server, args=(zp, idx, args, kwargs,), daemon=True)
        JOBS[idx] = (args, kwargs)
        t.start()

    MSG_PORT[function_name] = register_wrapper
    return register_wrapper


def update_client(zp, idx, string):
    zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=string))


@register_executor_method
def cd(zp, idx, dest):
    try:
        os.chdir(dest)
        update_client(zp, idx, os.getcwd())
        return 0
    except FileNotFoundError:
        update_client(zp, idx, "{}: No such file or directory.".format(dest))
        return -1


@register_executor_method
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
    update_client(zp, idx, name_list)
    return 0


@register_executor_method
def cwd(zp, idx):
    update_client(zp, idx, os.getcwd())
    return 0


@register_executor_method
def mkdir(zp, idx, path, *args):
    if(not(os.path.exists(path))):
        os.mkdir(path, *args)
        update_client(zp, idx, "Created directory: {}".format(path))
        return 0
    else:
        update_client(zp, idx, "Directory or File {} already exists".format(path))
        return -1


@register_executor_method
def rm(zp, idx, path, recursive=False):
    if(os.path.exists(path)):
        if((os.path.isdir(path) and recursive) or (os.path.isdir(path) and not(os.listdir(path)))):
            rmtree(path)
            update_client(zp, idx, "Removed directory {}".format(path))
            return 0
        elif(not(os.path.isdir(path))):
            os.remove(path)
            update_client(zp, idx, "Removed file {}".format(path))
            return 0
        else:
            update_client(zp, idx, "Non-Empty Directory... Pass recursive if you're certain")
            return -1
    else:
        update_client(zp, idx, "Directory or File {} doesn't exist?".format(path))
        return -1


@register_executor_method
def cat(zp, idx, path):
    if(os.path.exists(path) and not(os.path.isdir(path))):
        buffer = ""
        with open(path, 'r') as file:
            update_client(zp, idx, "Contents of {}".format(path))
            for line in file:
                buffer += line
                if(len(buffer) >= 1024):
                    update_client(zp, idx, buffer)
                    buffer = ""
        return 0
    else:
        update_client(zp, idx, "Unknown file: {}".format(path))
        return -1


@register_executor_method
def wrfile(zp, idx, path, data, append=False):
    if(os.path.exists(path) and os.path.isdir(path)):
        update_client(zp, idx, "wrfile: Path exists as a directory.")
        return -1
    else:
        with open(path, "a" if append else "w") as file:
            if(append):
                file.seek(0, 2)
            file.write(data)
        update_client(zp, idx, "Finished writing data to {}".format(path))
        return 0


@register_executor_method
def touch(zp, idx, path):
    if(os.path.exists(path) and os.path.isdir(path)):
        update_client(zp, idx, "wrfile: Path exists as a directory.")
        return -1
    else:
        file = open(path, "ab+" if os.path.exists(path) else "wb+")
        file.write(b" ")
        file.flush()
        file.seek(-1, 2)
        file.truncate()
        file.close()
        update_client(zp, idx, "Touched {}".format(path))
        return 0


@register_executor_method
def jobs(zp, idx):
    output = ""
    for key, value in JOBS.items():
        if(value is not None):
            output += "Running {}: {}\n".format(key, value)
    if(output == ""):
        output = "No jobs running."
    update_client(zp, idx, output)
    return 0


@register_executor_method_bg
def exec(zp, idx, cmd):
    m_executor = ConsoleExecutor(cmd)
    for line in m_executor.read_output():
        if(line is not None):
            update_client(zp, idx, line.rstrip("\r\n"))
    return 0
