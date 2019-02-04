import sys
import traceback


class ZMQPairTimeout(RuntimeError):
    pass


class ConsoleExecTimeout(RuntimeError):
    pass


def exception_to_str():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
