import os
import time
from unittest import TestCase, main

import pyosexec

os.chdir(os.path.dirname(os.path.realpath(__file__)))


class TestThorough(TestCase):
    @classmethod
    def setUp(self):
        self._client = pyosexec.ConsoleExecutor("python thorough_client.py")

    @classmethod
    def tearDown(self):
        self._client.kill()

    def test_server(self):
        result = pyosexec.start_server()
        self.assertEqual(result, 0)
        time.sleep(2)


if(__name__ == '__main__'):
    main()
