import zmq
import time
import logging
from threading import Thread
from queue import Queue

from ._msg import MSG, MSGType
from ._decorators import timeout
from .exceptions import ZMQPairTimeout
from . import _zmq_context


logger = logging.getLogger(__name__)


class ZMQPair(object):
    def __init__(self, dest_ip=None, port=8001):
        self._context = _zmq_context.get_context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.setsockopt(zmq.LINGER, 0)
        self._dest_ip = dest_ip
        self._port = port
        self._connected = False
        self.__queue = Queue()
        self.__bg_worker = Thread(target=ZMQPair.__bg_receiver, args=(self.__queue, self._socket), daemon=True)
        self.__bg_worker.start()

    @property
    def context(self):
        return self._context

    @property
    def socket(self):
        return self._socket

    @property
    def dest_ip(self):
        return self._dest_ip

    @property
    def port(self):
        return self._port

    @property
    def connected(self):
        return self._connected

    def close(self):
        if(self._connected and self._dest_ip):
            self.disconnect()
        self._socket.close()

    def bind(self):
        self._connected = self.__heartbeat(0.1)
        if(not(self._connected)):
            self._socket.bind("tcp://*:{}".format(self._port))
            self._connected = True

    def unbind(self):
        if(self._connected):
            self._socket.unbind()
            self._connected = False

    def connect(self):
        self._connected = self.__heartbeat(0.1)
        if(not(self._connected)):
            self._socket.connect("tcp://{}:{}".format(self._dest_ip, self._port))
            self._connected = True
            logger.debug("Main:: Connected: {}:{}".format(self._dest_ip, self._port))

    def disconnect(self):
        self._socket.disconnect("tcp://{}:{}".format(self._dest_ip, self._port))
        self._connected = False
        logger.debug("Main:: Disconnect: {}:{}".format(self._dest_ip, self._port))

    def send_msg(self, msg, timeout=None):
        assert type(msg) == MSG, "ZMQPair only communicates through MSG class"
        if(self._connected):
            logger.debug("Main:: Sending Message {}".format(str(msg)))
            self.__send_process(msg, timeout=timeout, exception=ZMQPairTimeout)
            return True
        else:
            self._connected = False
            return False

    def recv_msg(self, timeout=None):
        self.__check_mail(timeout=timeout, exception=ZMQPairTimeout)
        mail = self.__queue.get(timeout=10)
        logger.debug("Main:: Retrieved Message: {}".format(str(mail)))
        return mail

    def requeue_msg(self, msg):
        self.__queue.put(msg)

    def pulse(self, timeout=None):
        return self.__heartbeat(timeout=timeout)

    @timeout(name="Trasmitter")
    def __send_process(self, msg, **kwargs):
        tracker = self._socket.send_pyobj(msg, flags=zmq.NOBLOCK, track=True, copy=False)
        while(not(tracker.done)):
            yield None

    @timeout(name="Receiver")
    def __check_mail(self, **kwargs):
        if(self.__bg_worker.is_alive()):
            while(self.__queue.empty()):
                yield None
        else:
            raise RuntimeError("Recv thread died?")

    def __heartbeat(self, timeout):
        if(self._connected):
            self.send_msg(MSG(MSGType.HEARTBEAT, request=True), timeout=timeout)
            try:
                while(True):
                    msg = self.recv_msg(timeout=timeout)
                    if(msg.type == MSGType.HEARTBEAT):
                        return True
                    else:
                        self.__queue.put(msg)
            except ZMQPairTimeout:
                return False
        else:
            return False

    def __bg_receiver(queue, socket):
        logger.debug("Thread:: Starting")
        while(True):
            while(not(socket.poll(timeout=1, flags=zmq.POLLIN))):
                time.sleep(0)
            msg = socket.recv_pyobj()
            logger.debug("Thread:: {}".format(str(msg)))
            if(msg.request and msg.type == MSGType.HEARTBEAT):
                socket.send_pyobj(MSG(MSGType.HEARTBEAT, request=False))
            else:
                queue.put(msg)
