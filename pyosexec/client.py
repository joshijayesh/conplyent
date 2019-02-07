from threading import local
import time

from ._zmq_pair import ZMQPair
from ._msg import MSG, MSGType
from .exceptions import ZMQPairTimeout
from .log import logger

_pool = local()


def add_client(hostname, port=8001):
    try:
        connection = _get_connection("{}:{}".format(hostname, port))
    except RuntimeError:
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

    def _command_generic(self, cmd_id, *args, timeout=None, complete=True, **kwargs):
        listener = self.__send_command(cmd_id, timeout=timeout, *args, **kwargs)
        if(complete):
            for response in iter(listener.next, None):
                logger.info("<Server> {}".format(response))
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

        @property
        def done(self):
            return self._done

        @property
        def exit_code(self):
            return self._exit_code

        @property
        def id(self):
            return self._id

        def next(self, timeout=0):
            assert not(self._done), "Server has already completed job..."
            response = None
            while(True):
                try:
                    msg = self.__connection.recv_msg(timeout=timeout)
                    if((msg.type == MSGType.COMPLETE or msg.type == MSGType.DETAILS) and
                       msg.request_id == self._id and msg.msg_num == self.__curr_msg):
                        self.__curr_msg += 1
                        if(msg.type == MSGType.COMPLETE):
                            self._done = True
                            response = None
                            self._exit_code = msg.exit_code
                        else:
                            response = msg.details
                        break
                    else:
                        self.__connection.requeue_msg(msg)
                        time.sleep(0)  # some other thread probably wanted that message...
                except ZMQPairTimeout:
                    response = None
            return response

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
