#!/usr/bin/env python

'''
:File: start_server.py
:Author: Jayesh Joshi
:Email: jayeshjo1@utexas.edu
'''

import os
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
                   "    conplyent start_server --port {}\n".format(port) +
                   "exit")
    print("Created new file {}".format(file_name))


def _install_linux(port):
    print("Detected Linux OS")


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


@cli.command(name="start_server", help="Runs the server and starts listening on port")
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


if(__name__ == '__main__'):
    cli()
