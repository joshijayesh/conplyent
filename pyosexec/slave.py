import logging
from zmq import Again

from ._zmq_wrapper import ZMQPair
from ._slave_executor import MSG_PORT
from ._msg import MSGType, MSG


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def start():
    zp = ZMQPair()
    zp.bind()
    idx = 0

    while(True):
        msg = zp.recv_msg()
        try:
            if(msg.type == MSGType.COMMAND):
                zp.send_msg(MSG(MSGType.ACKNOWLEDGE, request_id=idx))
                MSG_PORT[msg.cmd_id](zp, idx, *msg.args, **msg.kwargs)
                idx = (idx + 1) % 0xFFFFFFFF
            elif(msg.type == MSGType.SYNC):
                zp.send_msg(MSG(MSGType.SYNC, args=(list(MSG_PORT.keys()),)))
        except Again:
            logger.info("Lost connection with host...")
