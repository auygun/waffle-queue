from collections import deque
import logging

import lazy_object_proxy
import pymysql
from flask import g


def _init_logger(level='WARNING'):
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        fmt='%(name)s %(lineno)s %(funcName)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def _create_pool():
    # _logger.setLevel('DEBUG')
    return ConnectionPool(host='127.0.0.1', port=3306,
                          user='mysql', password='mysql',
                          db='waffle_queue', autocommit=False,
                          cursorclass=pymysql.cursors.DictCursor)


_logger = lazy_object_proxy.Proxy(_init_logger)
_pool = lazy_object_proxy.Proxy(_create_pool)


class CreateConnectionError(Exception):
    """The connection pool is full"""


class Connection(pymysql.connections.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._returned = False

    def set_in_use(self):
        self._returned = False
        if self._sock is None:
            _logger.debug("reconnecting")
            self.connect()

    def set_returned(self):
        assert not self._returned
        self._returned = True


class ConnectionPool:
    def __init__(self, *args, max_size=100, **kwargs):
        self._pool = deque()
        self._num_connections = 0
        self._max_size = max_size
        self._args = args
        self._kwargs = kwargs

    def get_connection(self):
        _logger.debug(f"pool size: {len(self._pool)}")
        try:
            conn = self._pool.popleft()
            conn.set_in_use()
            return conn
        except IndexError:
            return self._create_connection()

    def _create_connection(self):
        _logger.debug(f"_num_connections: {self._num_connections}")
        if self._num_connections < self._max_size:
            self._num_connections += 1
            return Connection(*self._args, **self._kwargs)
        raise CreateConnectionError()

    def return_connection(self, conn):
        _logger.debug(f"pool size: {len(self._pool)}")
        conn.set_returned()
        self._pool.append(conn)


def connection():
    if 'sql_conn' not in g:
        g.sql_conn = _pool.get_connection()
    return g.sql_conn


def recycle(_e=None):
    conn = g.pop('sql_conn', None)
    if conn is not None:
        _pool.return_connection(conn)


def cursor():
    return connection().cursor()


def commit():
    return connection().commit()


def rollback():
    return connection().rollback()


def now():
    with connection().cursor() as cur:
        cur.execute("SELECT NOW()")
        return cur.next()[0]
