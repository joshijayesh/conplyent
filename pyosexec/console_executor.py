from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from queue import Queue, Empty


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

    def read_output(self, timeout=1):
        while(True):
            try:
                if(self.__bg_worker.is_alive()):
                    line = self.__queue.get(timeout=timeout)
                    yield line[:-1]
                else:
                    return
            except Empty:
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
