import os
import logging
from glob import glob
from functools import wraps
from shutil import rmtree

from ._msg import MSG, MSGType

MSG_PORT = {}
logger = logging.getLogger()


def register_slave_method(func):
    function_name = func.__name__

    @wraps(func)
    def register_wrapper(zp, idx, *args, **kwargs):
        request = "{} {} {}".format(function_name, args, kwargs)
        logger.info("Received Request: {}".format(request))
        zp.send_msg(MSG(MSGType.DETAILS, request_id=idx, details=request))

        exit_code = func(zp, idx, *args, **kwargs)

        zp.send_msg(MSG(MSGType.COMPLETE, request_id=idx, exit_code=exit_code))

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
        return 1


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
        return 1


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
