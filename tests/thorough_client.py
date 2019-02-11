import conplyent


client_connection = conplyent.client.add("localhost")
client_connection.connect()


client_connection.cd("..")
client_connection.cd("tests")
client_connection.cd("some_random_location")

client_connection.ls()

client_connection.cwd()

client_connection.mkdir("random_dir")
client_connection.mkdir("random_dir")
client_connection.touch("random_dir")
client_connection.touch("some_file.txt")

client_connection.rm("random_dir")
client_connection.rm("some_file.txt")

client_connection.mkdir("random_dir")
client_connection.touch("random_dir/some_file.txt")
client_connection.wrfile("random_dir", "hi")
client_connection.rm("random_dir")
client_connection.rm("random_dir", recursive=True)
client_connection.rm("random_dir")


client_connection.wrfile("some_file.txt", "some data")
client_connection.wrfile("some_file.txt", "some data", append=True)
client_connection.rm("some_file.txt")

client_connection.rdfile("test_console_executor.py")
client_connection.rdfile("no existing file")

client_connection.jobs()
client_connection.exec("python multiple_output.py 2")
listener = client_connection.exec("python wait_input.py", complete=False)
client_connection.jobs()
client_connection.ls()
while(True):
    if(listener.next(0.5) is None):
        break
client_connection.send_input(listener.id, "Continue")
for response in iter(listener.next, None):
    pass
client_connection.send_input(listener.id, "Are you alive?")
client_connection.send_input(0xFFFF, "HI")


listener = client_connection.exec("python wait_input.py", complete=False)
client_connection.kill(listener.id)
client_connection.kill(listener.id)
client_connection.kill(0xFFFF)

listener = client_connection.exec("python wait_input.py", complete=False)
client_connection.close_server()
