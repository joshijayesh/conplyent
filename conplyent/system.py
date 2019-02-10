import socket
import os


def ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        host_name = s.getsockname()[0]
        s.close()
        return host_name
    except KeyboardInterrupt:
        raise
    except Exception:
        return None


def os_name():
    return {"nt": "windows", "posix": "linux", "mac": "mac"}[os.name]


def reboot():
    my_os = os_name()
    if(my_os == "windows"):
        os.system("shutdown -t 0 -r -f")
    elif(my_os == "linux"):
        os.system("/sbin/reboot now")
    elif(my_os == "mac"):
        raise NotImplementedError("Macs not supported at the moment")


def shutdown():
    my_os = os_name()
    if(my_os == "windows"):
        os.system("shutdown -t 0 -s -f")
    elif(my_os == "linux"):
        os.system("/sbin/shutdown now")
    elif(my_os == "mac"):
        raise NotImplementedError("Macs not supported at the moment")
