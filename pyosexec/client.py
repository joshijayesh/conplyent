from threading import local
import time
import inspect

from ._zmq_pair import ZMQPair
from ._msg import MSG, MSGType
from .exceptions import ZMQPairTimeout, ClientTimeout
from .log import logger
from ._decorators import timeout

_pool = local()


def add_client(hostname, port=8001):
    connection = ClientConnection(_new_connection(ZMQPair(dest_ip=hostname, port=port)))
    return connection


def _wrap_server_methods(cls, name):
    def wrapper(self, *args, **kwargs):
        return self._command_generic(name, *args, **kwargs)
    return wrapper


class ClientConnection():
    def __init__(self, conn_id):
        self.__conn_id = conn_id
        self.__synced = False

    def connect(self, timeout=None):
        connection = _get_connection(self.__conn_id)
        connection.connect()
        if(timeout):
            logger.info("Waiting {}s for {} to respond...".format(self.__conn_id))
        else:
            logger.info("Waiting for {} to respond...".format(self.__conn_id))
        if(not(connection.pulse(timeout))):
            raise ConnectionError("Slave not responding at {}".format(self.__conn_id))
        if(not(self.__synced)):
            self.__sync_attr()
            self.__synced = True

    def close(self):
        connection = _get_connection(self.__conn_id)
        connection.close()
        logger.info("Closing connection to {}".format(self.__conn_id))

    def server_commands(self):
        commands = [i[0] for i in [k for k in inspect.getmembers(self, inspect.ismethod)]]
        return list(filter(lambda k: not (k[0] == "_" or k in ["server_commands", "close", "connect"]), commands))

    def _command_generic(self, cmd_id, *args, timeout=None, complete=True, **kwargs):
        listener = self.__send_command(cmd_id, timeout=timeout, *args, **kwargs)
        if(complete):
            output = list()
            for response in iter(listener.next, None):
                output.append(response)
            return output
        else:
            return listener

    def __send_command(self, cmd_id, *args, timeout=None, **kwargs):
        connection = _get_connection(self.__conn_id)
        msg = MSG(MSGType.COMMAND, cmd_id=cmd_id, args=args, keywargs=kwargs)
        connection.send_msg(msg, timeout)
        logger.debug("Sent Message: {}".format(msg))
        return ClientConnection.ConnectionListener(connection)

    def __sync_attr(self, timeout=None):
        connection = _get_connection(self.__conn_id)
        connection.send_msg(MSG(MSGType.SYNC, request=True))
        extra_list = list()
        while(True):
            msg = connection.recv_msg(timeout=timeout)
            if(msg.type == MSGType.SYNC):
                for name in msg.args[0]:
                    setattr(ClientConnection, name, _wrap_server_methods(self, name))
                break
            else:
                extra_list.append(msg)
        for extra in extra_list:
            connection.requeue_msg(extra)

    class ConnectionListener():
        def __init__(self, connection):
            self.__connection = connection
            self.__find_ack()
            self._done = False
            self._exit_code = None
            self.__curr_msg = 0

        def __enter__(self):
            pass

        def __exit__(self):
            pass

        @property
        def done(self):
            return self._done

        @property
        def exit_code(self):
            return self._exit_code

        @property
        def id(self):
            return self._id

        def next(self, timeout=None):
            self.__response = None
            assert not(self._done), "Server has already completed job..."
            try:
                self.__receive_message(timeout=timeout, exception=ClientTimeout)
            except (ZMQPairTimeout, ClientTimeout):
                pass
            return self.__response

        @timeout(name="Listening")
        def __receive_message(self, *args, **kwargs):
            msg = self.__connection.recv_msg(timeout=kwargs["timeout"])
            if((msg.type == MSGType.COMPLETE or msg.type == MSGType.DETAILS) and
               msg.request_id == self._id and msg.msg_num == self.__curr_msg):
                self.__curr_msg += 1
                if(msg.type == MSGType.COMPLETE):
                    self._done = True
                    self.__response = None
                    self._exit_code = msg.exit_code
                else:
                    self.__response = msg.details
                return
            else:
                self.__connection.requeue_msg(msg)
                yield None

        def __find_ack(self, timeout=5):
            while(True):
                try:
                    msg = self.__connection.recv_msg(timeout=5)
                    if(msg.type == MSGType.ACKNOWLEDGE):
                        self._id = msg.request_id
                        break
                    else:
                        self.__connection.requeue_msg(msg)
                        time.sleep(0)  # some other thread probably wanted that message...
                except ZMQPairTimeout:
                    raise ZMQPairTimeout("Slave did not acknowledge request in {}s".format(timeout))


def _new_connection(conn):
    conn_id = "{}:{}".format(conn.dest_ip, conn.port)
    try:
        connection = _get_connection(conn_id)
        connection.close()
    except RuntimeError:
        pass
    _pool.__dict__.setdefault("pyosexec_pool", dict())[conn_id] = conn
    return conn_id


def _get_connection(conn_id):
    try:
        return getattr(_pool, "pyosexec_pool")[conn_id]
    except (AttributeError, KeyError, IndexError):
        raise RuntimeError("Connection {} has not been set up".format(conn_id))
