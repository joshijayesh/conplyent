import os
from glob import glob
from functools import wraps
from shutil import rmtree
from threading import Thread
from zmq import Again
from queue import Queue

from ._zmq_pair import ZMQPair
from ._msg import MSGType, MSG
from ._general import SynchronizedDict
from .exceptions import exception_to_str
from .console_executor import ConsoleExecutor
from .log import logger


MSG_PORT = {}
_JOBS = SynchronizedDict()
_MSG_NUM = {}  # Ensures that MSG queue in client can be properly ordered


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
        update_client(zp, idx, request)

        try:
            exit_code = func(zp, idx, *args, **kwargs)
        except Again:
            logger.info("Lost connection with host...")
            return
        except Exception:
            update_client(zp, idx, exception_to_str())
            exit_code = 1

        zp.send_msg(MSG(MSGType.COMPLETE, request_id=idx, exit_code=exit_code, msg_num=_MSG_NUM[idx]))

    MSG_PORT[function_name] = register_wrapper
    return register_wrapper


def register_executor_method_bg(func):
    function_name = func.__name__

    @wraps(func)
    def bg_server(zp, idx, args, kwargs):
        print("NAME, ARGS {}, kwargs {}".format(args, kwargs))
        request = "{} {} {}".format(function_name, args, kwargs)
        logger.info("Received BG Request: {}".format(request))
        update_client(zp, idx, request)

        try:
            exit_code = func(zp, idx, *args, **kwargs)
        except Again:
            logger.info("Lost connection with host...")
            return
        except Exception:
            update_client(zp, idx, exception_to_str())
            exit_code = 1

        zp.send_msg(MSG(MSGType.COMPLETE, request_id=idx, exit_code=exit_code, msg_num=_MSG_NUM[idx]))
        _JOBS[idx] = None

    @wraps(func)
    def register_wrapper(zp, idx, *args, **kwargs):
        queue = Queue()
        args = (queue,) + args
        t = Thread(target=bg_server, args=(zp, idx, args, kwargs,), daemon=True)
        _JOBS[idx] = (args, kwargs, queue)
        t.start()

    MSG_PORT[function_name] = register_wrapper
    return register_wrapper


def update_client(zp, idx, string):
    _MSG_NUM.setdefault(idx, 0)
    zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=string, msg_num=_MSG_NUM[idx]))
    _MSG_NUM[idx] += 1


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
        with open(path, 'rb') as file:
            update_client(zp, idx, "Contents of {}".format(path))
            while(True):
                chunk = file.read(1024)
                if(chunk):
                    update_client(zp, idx, chunk)
                else:
                    break
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
    for key, value in _JOBS.items():
        if(value is not None):
            output += "Running {}: {}\n".format(key, value[:2])
    if(output == ""):
        output = "No _JOBS running."
    update_client(zp, idx, output)
    return 0


@register_executor_method_bg
def exec(zp, idx, queue, cmd):
    m_executor = ConsoleExecutor(cmd)
    for line in iter(m_executor.read_output, None):
        update_client(zp, idx, line.rstrip("\r\n"))
    return 0
