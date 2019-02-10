from threading import Lock


class SynchronizedDict(dict):
    def __init__(self, *args, **kwargs):
        self.__lock = Lock()
        super(SynchronizedDict, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        self.__lock.acquire()
        try:
            return super(SynchronizedDict, self).__getitem__(key)
        finally:
            self.__lock.release()

    def __setitem__(self, key, value):
        self.__lock.acquire()
        try:
            super(SynchronizedDict, self).__setitem__(key, value)
        finally:
            self.__lock.release()
