from zmq import Context
from threading import local


_ctx = local()


def get_context():
    try:
        return getattr(_ctx, "zmq_context")
    except (AttributeError, IndexError):
        _ctx.__dict__["zmq_context"] = Context()
        return _ctx.zmq_context


def close_context():
    try:
        getattr(_ctx, "zmq_context").term()
    except (AttributeError, IndexError):
        pass  # No need to close context?
