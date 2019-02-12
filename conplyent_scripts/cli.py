#!/usr/bin/env python

'''
:File: start_server.py
:Author: Jayesh Joshi
:Email: jayeshjo1@utexas.edu
'''

import os
import ast
import re
import logging

import click
import conplyent


def _install_windows(port):
    print("Detected Windows OS")
    print("Installing conplyent server listening to port # {}".format(port))
    user = os.getlogin()
    startup = "{}\\..\\Users\\{}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup".format(
        os.environ.get("windir"), user)  # This works for Windows 10... not sure about Windows 7-
    print("Assumming startup folder is in {}".format(startup))
    file_name = "{}\\conplyent_{}.bat".format(startup, port)
    with open(file_name, "w") as file:
        file.write("if not DEFINED IS_MINIMIZED set IS_MINIMIZED=1 && start \"\" /min \"%~dpnx0\" %* && exit\n"
                   "    conplyent start-server --port {}\n".format(port) +
                   "exit")
    print("Created new file {}".format(file_name))


def _install_linux(port):
    print("Detected Linux OS")
    print("Installing conplyent server listening to port # {}".format(port))
    ch = conplyent.ConsoleExecutor("whereis conplyent", shell=True)
    ptr = "conplyent"
    output = ch.read_output().decode("utf-8")
    match = re.search(r"conplyent: (.*)", output)
    if(match):
        ptr = match.group(1)
    file_name = "/etc/init.d/conplyent_{}.sh".format(port)
    with open(file_name, "w") as file:
        file.write("{} start-server --port {}".format(ptr, port))
    os.system("chmod +x {}".format(file_name))
    os.system("ln -s {} /etc/rc2.d/conplyent_{}.sh".format(file_name, port))
    os.system("update-rc.d conplyent_{}.sh defaults".format(port))


def _parse_args(arg_list):
    args = []
    kwargs = {}

    for arguments in arg_list[1:]:
        if(arguments):
            if("=" in arguments):
                key, value = arguments.split("=")
                try:
                    kwargs[key] = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    kwargs[key] = value
            else:
                try:
                    args.append(ast.literal_eval(arguments))
                except (ValueError, SyntaxError):
                    args.append(arguments)

    return args, kwargs


@click.group()
def cli():
    pass


@cli.command(help="Installs the server to startup on each boot")
@click.option("-p", "--port", help="Startup server will run on specified port", default=8001, type=int)
def install(port):
    '''
    Provides the means for users to start the server on startup.
    '''
    if(os.name == "nt"):
        _install_windows(port)
    elif(os.name == "posix"):
        _install_linux(port)
    else:
        raise NotImplementedError("Unknown OS... unsupported by conplyent at the moment")


@cli.command(name="start-server", help="Runs the server and starts listening on port")
@click.option("-p", "--port", help="Starts server on specified port", default=8001, type=int)
@click.option("--quiet", help="Sets the logging to quiet", default=False, is_flag=True)
@click.option("--debug", help="Sets the logging to debug (quiet must be false)", default=False, is_flag=True)
def start_server(port, quiet, debug):
    '''
    Starts the server.
    '''
    if(not(quiet)):
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    conplyent.server.start(port)


@cli.command(name="start-client", help="Run client to talk to server")
@click.option("-h", "--hostname", help="Host name of server to connect to", required=True, type=str)
@click.option("-p", "--port", help="Starts server on specified port", default=8001, type=int)
@click.option("-t", "--timeout", help="Timeout waiting for server to connect", default=None, type=int)
def start_client(hostname, port, timeout):
    '''
    Starts interactive client mode. Only keyword connected to this interactive mode is "commands" which will
    print out all available server commands.
    '''
    conn = conplyent.client.add(hostname, port)
    conn.connect(timeout=timeout)
    server_methods = conn.server_methods()

    while(True):
        response = input("Enter command: ")
        arg_list = re.split(r"\"(.*)\"|\'(.*)\'| ", response)
        if(arg_list and (arg_list[0] == "commands")):
            print("Server commands:\n{}".format("\n".join(server_methods)))
        elif(not(arg_list) or not(arg_list[0] in server_methods)):
            print("Unknown command")
        else:
            args, kwargs = _parse_args(arg_list)
            getattr(conn, arg_list[0])(*args, **kwargs, complete=True, echo_response=True)


if(__name__ == '__main__'):
    cli()
