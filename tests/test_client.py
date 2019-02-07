import os
from unittest import TestCase, main

import pyosexec

os.chdir(os.path.dirname(os.path.realpath(__file__)))


def setUpModule():
    global server
    server = pyosexec.ConsoleExecutor("python start_server.py")


def tearDownModule():
    server.kill()


def Client(TestCase):
    @classmethod
    def setUp(self):
        self.__client_connection = pyosexec.add_client("localhost")

    @classmethod
    def tearDown(self):
        self.__client_connection.close()


class TestSimpleCommands(TestCase):
    def test_cd(self):
        pass


if(__name__ == "__main__"):
    main()
