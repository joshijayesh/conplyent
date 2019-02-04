import logging

from pyosexec import master


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


master_connection = master.add("localhost")
master_connection.connect()

master_connection.cd(dest="..")
master_connection.ls()
master_connection.mkdir("New folder")


#  listener = master_connection.ls(complete=False)
#
#  while(not(listener.done)):
#      logger.info(listener.next())
#
#  logger.info("Exit code: {}".format(listener.exit_code))
