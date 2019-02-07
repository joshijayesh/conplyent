import os
from unittest import TestCase, main

import pyosexec
import tracemalloc

tracemalloc.start()

os.chdir(os.path.dirname(os.path.realpath(__file__)))


class TestServer(TestCase):
    @classmethod
    def setUp(self):
        self._client = pyosexec.ConsoleExecutor("python start_client.py")

    @classmethod
    def tearDown(self):
        self._client.kill()

    def test_server(self):
        result = pyosexec.start_server()
        self.assertEqual(result, 0)


if(__name__ == '__main__'):
    main()
