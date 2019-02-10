from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from queue import Queue

from ._decorators import timeout
from .exceptions import ConsoleExecTimeout


class ConsoleExecutor():
    def __init__(self, cmd):
        self._cmd = cmd
        self.__popen = Popen(cmd, stdout=PIPE, stderr=STDOUT, stdin=PIPE, universal_newlines=True, shell=False,
                             start_new_session=True)
        self.__queue = Queue()
        self.__bg_worker = Thread(target=ConsoleExecutor.__file_reader, args=(self.__queue, self.__popen.stdout),
                                  daemon=True)
        self.__bg_worker.start()
        self._alive = True

    def __del__(self):
        self.close()

    @property
    def cmd(self):
        return self._cmd

    @property
    def returncode(self):
        return self.__popen.returncode

    @property
    def alive(self):
        return self.__bg_worker.is_alive()

    def read_output(self, timeout=None):
        while(True):
            if(self.alive):
                self.__poll_queue(timeout=timeout, exception=ConsoleExecTimeout)
                if(self.__queue.empty()):
                    if(not(self.alive)):
                        self.__popen.wait()
                    return None
                else:
                    return self.__queue.get(timeout=1)  # should never halt here...
            else:
                self.__popen.wait()
                return None

    def send_input(self, value):
        if(self.alive):
            self.__popen.stdin.write(value + "\n")
            self.__popen.stdin.flush()

    def kill(self):
        self.__popen.terminate()
        self.__popen.wait()

    def close(self):
        if(self.alive):
            self.kill()
        self.__popen.stdin.close()
        self.__popen.stdout.close()

    def __file_reader(queue, file):
        for line in iter(file.readline, ''):
            queue.put(line)
        file.close()

    @timeout(name="Polling Queue")
    def __poll_queue(self, **kwargs):
        while(self.__queue.empty() and self.__bg_worker.is_alive()):
            yield None
