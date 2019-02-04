from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from queue import Queue, Empty
from ._decorators import timeout
from .exceptions import ConsoleExecTimeout


class ConsoleExecutor():
    def __init__(self, cmd):
        self._cmd = cmd
        self.__popen = Popen(cmd, stdout=PIPE, stderr=STDOUT, stdin=PIPE, universal_newlines=True, shell=False)
        self.__queue = Queue()
        self.__bg_worker = Thread(target=ConsoleExecutor.__file_reader, args=(self.__queue, self.__popen.stdout),
                                  daemon=True)
        self.__bg_worker.start()
        self._alive = True

    @property
    def cmd(self):
        return self._cmd

    @property
    def returncode(self):
        return self.__popen.returncode

    @property
    def alive(self):
        return self._alive

    def read_output(self, timeout=None):
        while(True):
            try:
                if(self.__bg_worker.is_alive()):
                    self.__poll_queue(timeout=timeout, exception=ConsoleExecTimeout)
                    if(self.__queue.empty()):
                        return
                    else:
                        yield self.__queue.get(timeout=1)  # should never halt here...
                else:
                    return
            except (Empty, ConsoleExecTimeout):
                yield None

    def send_input(self, value):
        if(self.__bg_worker.is_alive()):
            self.__popen.stdin.write(value + "\n")
            self.__popen.stdin.flush()

    def kill(self, value):
        self.__popen.kill()
        self.__bg_worker.terminate()

    def __file_reader(queue, file):
        for line in iter(file.readline, ''):
            queue.put(line)
        file.close()

    @timeout(name="Polling Queue")
    def __poll_queue(self, **kwargs):
        while(self.__queue.empty() and self.__bg_worker.is_alive()):
            yield None
