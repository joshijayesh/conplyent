Client
======

Conplyent provides a client/server connection for running distributed applications. The client provides the means to connect to a remote server and execute commands remotely. The client module provides several useful features to develop a powerful library.

Client Pool
-----------
Firstly, the client module provides a pool of servers that users can connect to, which allows users to create multiple clients each connected to a different server. I typically use just a single client for each instance of python but this provides the flexibility to create a automation hub for any amount of clients.

To create a new connection:

>>> import conplyent
>>>
>>> connection = conplyent.client.add("localhost", port=9922)
>>> connection.connect(timeout=240)  # timeout if connection not established in 240s...
>>> ...
>>> connection.close()

Users should always run 'connect' before running any methods. Adding a new client does not automatically run a connect. This is because the connection class also provides the means to disconnect and reconnect for specific scenarios.

Alternatively, users can create a scope for this to run:

>>> import conplyent
>>>
>>> with conplyent.client.add("localhost", port=9922, enter_connect_timeout=240) as connection:
>>>     ...

This'll automatically connect entering into the connection class and close on exit.

Server Commands
---------------

Now that we've set up the connection, we can run commands on the server. These commands are added as method attributes to the connection class once 'connect' has been called. Conplyent provides a few keyword arguments processed in the client side before sending the command over to server. These are:

:complete:

    By default, complete is set to True. If complete is True, then the client will continually listen for the server to complete execution and return the output in a list format. If complete is set to False, then client will send the command to the server and provide the user with a listener class that the user can use to listen for any updates on the server, or use the ID of the listener for any job related commands. See more on listener below.

:timeout:

    By default, timeout is None. This is used to determine how long client should wait for a command to go through. None meaning wait until completion.

:echo_response:

    By default echo_response is set to False. This works in conjunction with complete. If echo_response is set to True while complete is set to True, output provided by the server will be printed on stdout in real time.

:max_interval:

    By default max_interval is set to None. This is a attribute used by the listener class to determine how long to wait between messages. This is particularly useful when running commands that may affect the runtime of the server. For example, if we expect that the command should return something~ in at most 5 seconds, we can set max_interval > 5 seconds to determine that the server is unresponsive and higher level handling should be called. This will throw a ClientError if listener times out.

:raise_error:

    By default raise_error is set to False. If raise_error is set to True, and the command sent to the server raises an error, such as FileNotFoundError, then the client will also throw this error. If set to False, will not raise any errors and user can use the listener class or output to determine error.

Client Commands
---------------

These commands are implemented in the client side as a superset communication with the server.

:heartbeat:

    Can be used to check if the server is alive by pulsing the server for a quick response. Returns True or False based on success.

:transfer:

    Transfer file from client to server.

Listener
--------

Listener class is created for each command sent to the server. This listener class is a unique identifier for each command and created by the ClientConnection class. If the user had specified complete=True, then the connection class will go through the listener and only provide the user with the output. This is useful for cases where user expects no interface for messages sent by the server. Complete can be set to False so uers can retrieve the listener themselves.

>>> listener = connection.exec("some command", complete=False)

or

>>> with connection.exec("some command", complete=False) as listener:

Extracting the listener provides the main thread to run any tasks on the foreground and check on the listener for any updates from the server. And also check for direct info about the command completion.

To go through messages, user can use:

>>> for msg in iter(listener.next, None):
>>>     ...

These messages are retrieved in real time for processing. Next will return None if the command has completed on the server side, otherwise will wait max_interval duration between each messages. This interval can be used to interrupt the listener mid way (for cases where the command may be waiting for input or such). Max_interval can be changed by the user directly once listener has been created if necessary.
