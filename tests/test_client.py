import os
from unittest import TestCase, main

import conplyent

os.chdir(os.path.dirname(os.path.realpath(__file__)))


def setUpModule():
    global server
    server = conplyent.ConsoleExecutor("python start_server.py")


def tearDownModule():
    server.kill()


class TestClient(TestCase):
    @classmethod
    def setUp(self):
        self._client_connection = conplyent.client.add("localhost")

    @classmethod
    def tearDown(self):
        self._client_connection.close()


class TestSimpleCommands(TestClient):
    def test_client_retrieved_commands(self):
        self._client_connection.connect(timeout=5)
        server_commands = self._client_connection.server_methods()
        for command in server_commands:
            if(command == 'transfer'):
                continue
            self.assertIn(command, conplyent.MSG_PORT.keys())

    def test_cd_cwd(self):
        self._client_connection.connect()
        output = self._client_connection.cd("..")
        os.chdir("..")
        self.assertEqual(output[0], os.getcwd())
        output = self._client_connection.cd("tests")
        os.chdir("tests")
        self.assertEqual(output[0], os.getcwd())

    def test_ls(self):
        self._client_connection.connect()
        output = self._client_connection.ls()
        self.assertIn("f test_client.py", output[0])

    def test_transfer(self):
        # This'll throw errors if unable to transfer/rm couldn't find file
        self._client_connection.connect()
        self._client_connection.cd("..")
        self._client_connection.transfer("start_server.py", "start_server.py", raise_error=True)
        self._client_connection.rm("start_server.py", raise_error=True)
        self._client_connection.cd("tests")


class TestWith(TestCase):
    def test_with(self):
        with conplyent.client.add("localhost") as connection:
            with connection.exec("python multiple_output.py 2", echo=True, complete=False) as listener:
                listener.clear_messages()


if(__name__ == "__main__"):
    main()
