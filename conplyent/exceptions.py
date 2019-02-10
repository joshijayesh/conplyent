import sys
import traceback


class ZMQPairTimeout(RuntimeError):
    pass


class ConsoleExecTimeout(RuntimeError):
    pass


class ClientTimeout(RuntimeError):
    pass


def exception_to_str():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))


def min_exception_to_str():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return exc_value