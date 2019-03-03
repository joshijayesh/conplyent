import conplyent


with conplyent.client.add("localhost") as client_connection:
    client_connection.connect()

    client_connection.cd("..")
    client_connection.cd("tests")
    try:
        client_connection.cd("some_random_location")
    except FileNotFoundError:
        pass  # This shouldn't exist lol

    client_connection.ls()
    client_connection.ls("non_existing_dir")

    client_connection.cwd()

    client_connection.mkdir("random_dir")
    client_connection.mkdir("random_dir")
    client_connection.mkdirs("random_multiple_dirs/multiple_dirs")
    client_connection.touch("random_dir")
    client_connection.touch("some_file.txt")

    client_connection.rm("random_multiple_dirs", recursive=True)
    client_connection.rm("random_dir")
    client_connection.rm("some_file.txt")

    client_connection.mkdir("random_dir")
    client_connection.touch("random_dir/some_file.txt")
    client_connection.wrfile("random_dir", b"hi")
    try:
        client_connection.rm("random_dir", raise_error=True)
    except ValueError:
        pass  # did not pass recursive so should error out
    client_connection.rm("random_dir", recursive=True)
    client_connection.rm("random_dir")

    client_connection.wrfile("some_file.txt", b"some data")
    client_connection.wrfile("some_file.txt", b"some data", append=True)
    client_connection.rm("some_file.txt")

    client_connection.rdfile("test_console_executor.py")
    client_connection.rdfile("no existing file")

    client_connection.jobs()
    client_connection.exec("python multiple_output.py 2")

    assert client_connection.heartbeat(), "Should not fail"
    with client_connection.exec("python wait_input.py", complete=False, max_interval=0.5) as listener:
        client_connection.jobs()
        client_connection.ls()

        assert client_connection.is_alive(listener.id)[0], "Job should still be alive"

        assert client_connection.heartbeat(), "Should not fail"
        listener.clear_messages()
        assert client_connection.heartbeat(), "Should not fail"
        client_connection.send_input(listener.id, "Continue")
        assert client_connection.heartbeat(), "Should not fail"
        listener.clear_messages()
        assert client_connection.heartbeat(), "Should not fail"
        client_connection.send_input(listener.id, "Are you alive?")
        client_connection.send_input(0xFFFF, "HI")

    assert client_connection.heartbeat(), "Should not fail"
    assert not(client_connection.is_alive(listener.id)[0]), "Job should still be finished"

    listener = client_connection.exec("python wait_input.py", complete=False)
    client_connection.kill(listener.id)
    client_connection.kill(listener.id)
    client_connection.kill(0xFFFF)

    listener = client_connection.exec("python wait_input.py", complete=False)

    client_connection.os_info()

    client_connection.user_name()

    client_connection.exec("python paused_multiple_output.py 5 5 0.25", complete=False)
    client_connection.disconnect()
    client_connection.connect()

    client_connection.exec("python throw_error.py")

    client_connection.close_server()
    client_connection.disconnect()
