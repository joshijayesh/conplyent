import logging
from pyosexec import server_executor


logging.basicConfig(level=logging.INFO)
server_executor.start()
