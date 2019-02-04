import logging

from pyosexec import master


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


master_connection = master.add("localhost")
master_connection.connect()

master_connection.cd(dest="test")
#  master_connection.wrfile("test.txt", "Some form of data\n", append=True)
#  master_connection.touch("test.txt")
t1 = master_connection.exec("python paused_multiple_output.py", complete=False)
t2 = master_connection.exec("python paused_multiple_output.py", complete=False)
t3 = master_connection.exec("python paused_multiple_output.py", complete=False)

master_connection.jobs()


while(not(t1.done)):
    print(t1.next())
while(not(t2.done)):
    print(t1.next())
while(not(t3.done)):
    print(t1.next())


#  listener = master_connection.ls(complete=False)
#
#  while(not(listener.done)):
#      logger.info(listener.next())
#
#  logger.info("Exit code: {}".format(listener.exit_code))
