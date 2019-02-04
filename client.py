import logging

from pyosexec import client


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


client_connection = client.add("localhost")
client_connection.connect()

client_connection.cd(dest="test")
#  client_connection.wrfile("test.txt", "Some form of data\n", append=True)
#  client_connection.touch("test.txt")
#  t1 = client_connection.exec("python paused_multiple_output.py Thread1")
#  t2 = client_connection.exec("python paused_multiple_output.py Thread2")
#  t3 = client_connection.exec("python paused_multiple_output.py Thread3")

t1 = client_connection.exec("python paused_multiple_output.py Thread1", complete=False)
t2 = client_connection.exec("python paused_multiple_output.py Thread2", complete=False)
t3 = client_connection.exec("python paused_multiple_output.py Thread3", complete=False)

client_connection.jobs()


for msg in iter(t1.next, None):
    print(msg)
for msg in iter(t2.next, None):
    print(msg)
for msg in iter(t3.next, None):
    print(msg)


#  listener = client_connection.ls(complete=False)
#
#  while(not(listener.done)):
#      logger.info(listener.next())
#
#  logger.info("Exit code: {}".format(listener.exit_code))
