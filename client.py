import logging
from threading import Thread

from pyosexec import client


def read_thread(listener):
    for value in iter(listener.next, None):
        print(value)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


client_connection = client.add("localhost")
client_connection.connect()

client_connection.cd(dest="test")
listener = client_connection.exec("python wait_input.py", complete=False)

Thread(target=read_thread, args=(listener,), daemon=True).start()


while(True):
    value = input("Enter Value")
    print("Sending Value")
    if(value == "kill"):
        client_connection.kill(listener.id)
    else:
        client_connection.send_input(listener.id, value)
