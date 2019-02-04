from threading import Lock


class SynchronizedDict(object):
    def __init__(self, *args, **kwargs):
        self.__lock = Lock()
        super(SynchronizedDict, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        self.__lock.lock()
        try:
            super(SynchronizedDict, self).__getitem__(key)
        finally:
            self.__lock.unlock()

    def  __setitem__(self, key, value):
        self.__lock.lock()
        try:
            super(SynchronizedDict, self).__setitem(key)
        finally:
            self.__lock.unlock()
