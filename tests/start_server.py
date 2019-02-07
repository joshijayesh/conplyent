import logging
from pyosexec import server_executor


logging.basicConfig(level=logging.WARNING)
server_executor.start()
