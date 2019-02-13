import logging
from conplyent import register_command, server, SUCCESS

logging.basicConfig(level=logging.INFO)


@register_command
def echo(idx, string):
    print(string)
    server.update_client(idx, string)  # echo back to client, optional
    return SUCCESS


server.start()
