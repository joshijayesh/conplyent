import os
from unittest import TestCase, main

import pyosexec
from pyosexec import server_executor

os.chdir(os.path.dirname(os.path.realpath(__file__)))


def setUpModule():
    global server
    server = pyosexec.ConsoleExecutor("python start_server.py")


def tearDownModule():
    server.kill()


class TestClient(TestCase):
    @classmethod
    def setUp(self):
        self._client_connection = pyosexec.add_client("localhost")

    @classmethod
    def tearDown(self):
        self._client_connection.close()


class TestSimpleCommands(TestClient):
    def test_client_retrieved_commands(self):
        self._client_connection.connect()
        server_commands = self._client_connection.server_commands()
        for command in server_commands:
            self.assertIn(command, server_executor.MSG_PORT.keys())

    def test_cd_cwd(self):
        self._client_connection.connect()
        output = self._client_connection.cd("..")
        os.chdir("..")
        self.assertEqual(output[1], os.getcwd())
        output = self._client_connection.cd("tests")
        os.chdir("tests")
        self.assertEqual(output[1], os.getcwd())

    def test_ls(self):
        self._client_connection.connect()
        output = self._client_connection.ls()
        self.assertIn("f .\\test_client.py", output[1])


if(__name__ == "__main__"):
    main()
