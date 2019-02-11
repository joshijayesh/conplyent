import os
from unittest import TestCase, main

from conplyent import ConsoleExecutor, ConsoleExecTimeout


os.chdir(os.path.dirname(os.path.realpath(__file__)))


class TestConsoleExecutor(TestCase):
    @classmethod
    def setUp(self):
        self._console_executor = ConsoleExecutor(self._cmd)

    @classmethod
    def tearDown(self):
        self._console_executor.close()

    def get_output(self):
        complete_output = list()
        for output in iter(self._console_executor.read_output, None):
            complete_output.append(output)
        return complete_output


class TestMultipleOutput(TestConsoleExecutor):
    _cmd = "python multiple_output.py 5"

    def test_five_output(self):
        '''
        Thorough checkout of each of the properties of ConsoleExecutor and ensuring that
        return code is set after the executor exits
        '''
        complete_output = self.get_output()
        self.assertEqual(self._cmd, self._console_executor.cmd)
        self.assertEqual(len(complete_output), 5)
        self.assertEqual(self._console_executor.returncode, 0)
        self.assertFalse(self._console_executor.alive)

        complete_output = self.get_output()
        self.assertEqual(len(complete_output), 0)

    def test_second_run(self):
        '''
        Verification that previous ConsoleExecutor closed properly
        '''
        complete_output = self.get_output()
        self.assertEqual(len(complete_output), 5)
        self.assertEqual(self._console_executor.returncode, 0)

    def test_third_run(self):
        '''
        Extra verification that previous ConsoleExecutor closed properly
        '''
        complete_output = self.get_output()
        self.assertEqual(len(complete_output), 5)
        self.assertEqual(self._console_executor.returncode, 0)


class TestPausedOutput(TestConsoleExecutor):
    _cmd = "python paused_multiple_output.py 5 whatever 0.25"

    def test_paused_output(self):
        '''
        Verification that output that are sparsed across time are retrieved the same
        '''
        complete_output = self.get_output()
        self.assertEqual(self._cmd, self._console_executor.cmd)
        self.assertEqual(len(complete_output), 5)
        self.assertFalse(self._console_executor.alive)
        self.assertEqual(self._console_executor.returncode, 0)

    def test_timeout(self):
        '''
        Verify that ConsoleExecTimeout is raised if user verifies time
        '''
        with self.assertRaises(ConsoleExecTimeout) as context:
            while(True):
                self._console_executor.read_output(timeout=0.005)

        self.assertTrue("Polling Subprocess" in str(context.exception))

    def test_kill(self):
        '''
        Verify that the background test will complete if we kill the main subprocess.

        Also should return code 1
        '''

        self._console_executor.kill()

        self.assertFalse(self._console_executor.alive)
        self.assertEqual(self._console_executor.returncode, 1)


class TestInput(TestConsoleExecutor):
    _cmd = "python wait_input.py"

    def test_send_input(self):
        '''
        Verify that the process can receive input and still continue
        '''
        complete_output = list()
        try:
            while(True):
                complete_output.append(self._console_executor.read_output(timeout=0.5))
        except ConsoleExecTimeout:
            pass
        self.assertEqual(len(complete_output), 1)
        self.assertTrue(self._console_executor.alive)
        self._console_executor.send_input("Continue")
        complete_output = self.get_output()
        self.assertEqual(len(complete_output), 1)
        self.assertFalse(self._console_executor.alive)
        self.assertEqual(self._console_executor.returncode, 0)


if(__name__ == '__main__'):
    main()
