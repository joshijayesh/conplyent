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
        self._client_connection.connect()
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


if(__name__ == "__main__"):
    main()
