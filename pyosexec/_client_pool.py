from threading import local


_pool = local()


def new_connection(conn):
    conn_id = "{}:{}".format(conn.dest_ip, conn.port)
    try:
        connection = get_connection(conn_id)
        connection.close()
    except RuntimeError:
        pass
    _pool.__dict__.setdefault("pyosexec_pool", dict())[conn_id] = conn
    return conn_id


def get_connection(conn_id):
    try:
        return getattr(_pool, "pyosexec_pool")[conn_id]
    except (AttributeError, KeyError, IndexError):
        raise RuntimeError("Connection {} has not been set up".format(conn_id))
