Server
======

Conplyent provides a client/server connection for running distributed applications. The purpose of this server is to create a compliant system that provides many universal commands that is os-independent, in term creating its own shell, and also allowing clients to run commands on the system. This is primarily created for automation processes where we can simply install a conplyent server on a system and set it up to run on startup so that clients can remotely connect to the system and run commands. This server is purely built on top of python so the only pre-requirement for the system under test is to install python and pip.

Conplyent Shell
===============

The default command set comes with commands that can be executed remotely to provide some form of shell-like activity. These are also written completely in python so they are os-independent and follow the naming convention similar to UNIX rather than DOS. These commands are listed below, see API for details on usage. These default set may be expanded in the future to provide more accessibility.

* cd -- Change current working directory of the server.

* ls -- LiSt the files and folders in the current working directory.

* cwd -- Current working directory of the server.

* rm -- Remove files and folders in the server. (would require elevation for certain directories)

* rdfile -- Reads the contents of a file.

* wrfile -- Writes contents to a file.

* touch -- Create file if not exist. Update its mod time if exists.

* jobs -- See background tasks (spawned from server).

* exec -- Runs a external command as background task.

* send_input -- Sends input to the background task spawned by exec.

* kill -- Terminates the background task spawned by exec.

* close_server -- Exits the server.

* os_info -- Name of the current OS on the server.

* reboot -- Issues a reboot to OS.

* shutdown -- Issues a shutdown to OS.

Custom Commands
---------------

Conplyent server is built on the premise of simple additions of new commands. There are two types of commands: foreground commands, and background commands. For tasks that are relatively quick and won't hold down the server, these should be used as foreground commands. For tasks that will take an unknown amount of time or are IO bound, these should be run in the background. For the Conplyent Shell, only exec is implemented as a background command.

To create your own custom command, you'll need to use either @register_command or @register_background_command. See the documentation on the detailed requirements for these commands.

Quick and short example:

>>> from conplyent import register_command, server, SUCCESS
>>>
>>> @register_command
>>> def echo(idx, string):
>>>     print(string)
>>>     server.update_client(idx, string)  # echo back to client, optional
>>>     return SUCCESS
>>>
>>> server.start()

Command echo now can be used from the client, both from python scripts and the client console script.

>>> Enter command: echo hi
>>> echo ('hi',) {}
>>> hi

Conplyent Extensions
--------------------

Planning to add extension files to conplyent which can interface other open source libraries, like pyautogui, and ability to start servers using these extensions easily.