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
    _logger.setLevel('DEBUG')
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

    def _prepare(self):
        self._returned = False
        if self._sock is None:
            _logger.debug("reconnecting")
            self.connect()


class ConnectionPool:
    def __init__(self, max_size=1000, *args, **kwargs):
        self._pool = deque()
        self._num_connections = 0
        self._max_size = max_size
        self._args = args
        self._kwargs = kwargs

    def _get_connection(self):
        _logger.debug(f"pool size: {len(self._pool)}")
        try:
            conn = self._pool.popleft()
            conn._prepare()
            return conn
        except IndexError:
            return self._create_connection()

    def _create_connection(self):
        _logger.debug(f"_num_connections: {self._num_connections}")
        if self._num_connections < self._max_size:
            self._num_connections += 1
            return Connection(*self._args, **self._kwargs)
        raise CreateConnectionError()

    def _return_connection(self, conn):
        _logger.debug(f"pool size: {len(self._pool)}")
        assert conn._returned == False
        conn._returned = True
        self._pool.append(conn)


def connection():
    if '_conn' not in g:
        g._conn = _pool._get_connection()
    return g._conn


def recycle(e=None):
    conn = g.pop('_conn', None)
    if conn is not None:
        _pool._return_connection(conn)


def cursor():
    return connection().cursor()


def commit():
    return connection().commit()


def rollback():
    return connection().rollback()


def now():
    with connection().cursor() as cursor:
        cursor.execute("SELECT NOW()")
        return cursor.next()[0]
