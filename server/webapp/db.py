from collections import deque
import logging

import lazy_object_proxy
import pymysql


def _init_logger(level='WARNING'):
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        fmt='%(name)s %(lineno)s %(funcName)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def _create_pool():
    _logger.setLevel('DEBUG')
    return ConnectionPool(host='127.0.0.1', port=3306,
                          user='mysql', password='mysql',
                          db='waffle_queue', autocommit=True,
                          cursorclass=pymysql.cursors.DictCursor)


_logger = lazy_object_proxy.Proxy(_init_logger)
_pool = lazy_object_proxy.Proxy(_create_pool)


class ConnectionPoolFull(Exception):
    """Cannot create new connection. The pool is full"""


class Connection(pymysql.connections.Connection):
    """Context manager that returns a connection object back to the connection
    pool in __exit__() method.
    """

    _pool = None

    def __init__(self, pool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pool = pool
        self._returned = False

    def __enter__(self):
        if self._sock is None:
            _logger.debug("reconnecting")
            self.connect()
        self._returned = False
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        self._pool._return_connection(self)


class ConnectionPool:
    """Keeps a pool of connections. Provides a method to get a connection from
    the pool. Creates a new connection if the pool is empty.
    """

    def __init__(self, max_size=1000, *args, **kwargs):
        self._pool = deque()
        self._num_connections = 0
        self._max_size = max_size
        self._args = args
        self._kwargs = kwargs

    def get_connection(self):
        _logger.debug(f"pool size: {len(self._pool)}")
        try:
            return self._pool.popleft()
        except IndexError:
            return self._create_connection()

    def _create_connection(self):
        _logger.debug(f"_num_connections: {self._num_connections}")
        if self._num_connections < self._max_size:
            self._num_connections += 1
            return Connection(self, *self._args, **self._kwargs)
        raise ConnectionPoolFull()

    def _return_connection(self, conn):
        _logger.debug(f"pool size: {len(self._pool)}")
        assert conn._returned == False
        conn._returned = True
        self._pool.append(conn)


def connection():
    return _pool.get_connection()


def now():
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT NOW()")
        return cursor.next()[0]
