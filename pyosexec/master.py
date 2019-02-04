import logging

from ._zmq_wrapper import ZMQPair
from ._msg import MSG, MSGType
from .exceptions import ZMQPairTimeout
from . import _master_pool as pool

logger = logging.getLogger(__name__)


def add(hostname, port=8001):
    new_pair = ZMQPair(hostname, port)
    return MasterConnection(pool.new_connection(new_pair))


def _wrap_slave_methods(cls, name):
    def wrapper(self, *args, **kwargs):
        return self._command_generic(name, *args, **kwargs)
    return wrapper


class MasterConnection():
    def __init__(self, conn_id):
        self.__conn_id = conn_id
        self.__synced = False

    def connect(self, timeout=None):
        connection = pool.get_connection(self.__conn_id)
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
        connection = pool.get_connection(self.__conn_id)
        connection.close()
        logger.info("Closing connection to {}".format(self.__conn_id))

    def _command_generic(self, cmd_id, *args, timeout=None, complete=True, **kwargs):
        listener = self.__send_command(cmd_id, timeout=timeout, *args, **kwargs)
        if(complete):
            while(not(listener.done)):
                response = listener.next()
                logger.info("Server response: {}".format(response))
        else:
            print("returning listener")
            return listener

    def __send_command(self, cmd_id, *args, timeout=None, **kwargs):
        connection = pool.get_connection(self.__conn_id)
        msg = MSG(MSGType.COMMAND, cmd_id=cmd_id, args=args, keywargs=kwargs)
        connection.send_msg(msg, timeout)
        logger.debug("Sent Message: {}".format(msg))
        return MasterConnection.ConnectionListener(self.__conn_id)

    def __sync_attr(self, timeout=None):
        connection = pool.get_connection(self.__conn_id)
        connection.send_msg(MSG(MSGType.SYNC, request=True))
        extra_list = list()
        while(True):
            msg = connection.recv_msg(timeout=timeout)
            if(msg.type == MSGType.SYNC):
                for name in msg.args[0]:
                    setattr(MasterConnection, name, _wrap_slave_methods(self, name))
                break
            else:
                extra_list.append(msg)
        for extra in extra_list:
            connection.requeue_msg(extra)

    class ConnectionListener():
        def __init__(self, conn_id):
            self.__conn_id = conn_id
            self.__find_ack()
            self._done = False
            self._exit_code = None

        @property
        def done(self):
            return self._done

        @property
        def exit_code(self):
            return self._exit_code

        def next(self, timeout=0):
            connection = pool.get_connection(self.__conn_id)
            extra_list = list()
            response = None
            while(True):
                try:
                    msg = connection.recv_msg(timeout=timeout)
                    if((msg.type == MSGType.COMPLETE or msg.type == MSGType.DETAILS) and msg.request_id == self.__id):
                        if(msg.type == MSGType.COMPLETE):
                            self._done = True
                            response = msg.exit_code
                            self._exit_code = msg.exit_code
                        else:
                            response = msg.details
                        break
                    else:
                        extra_list.append(msg)
                except ZMQPairTimeout:
                    response = None
            self.__return_list(connection, extra_list)
            return response

        def __find_ack(self, timeout=5):
            connection = pool.get_connection(self.__conn_id)
            extra_list = list()
            while(True):
                try:
                    msg = connection.recv_msg(timeout=5)
                    if(msg.type == MSGType.ACKNOWLEDGE):
                        self.__id = msg.request_id
                        break
                    else:
                        extra_list.append(msg)
                except ZMQPairTimeout:
                    raise ZMQPairTimeout("Slave did not acknowledge request in {}s".format(timeout))
            self.__return_list(connection, extra_list)

        def __return_list(self, connection, extra_list):
            for extra in extra_list:
                connection.requeue_msg(extra)
