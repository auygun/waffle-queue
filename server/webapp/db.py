from collections import deque
import logging
import time

import lazy_object_proxy
import pymysql
from pymysql.err import OperationalError
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

    def query(self, sql, unbuffered=False):
        """Override query method. Try to reconnect if the connection was lost"""
        try:
            super().query(sql, unbuffered)
        except OperationalError:
            _logger.debug("reconnecting")
            self.ping(reconnect=True)
            super().query(sql, unbuffered)


class ConnectionPool:
    def __init__(self, *args, max_size=10, **kwargs):
        self._pool = deque()
        self._num_connections = 0
        self._max_size = max_size
        self._args = args
        self._kwargs = kwargs

    def get_connection(self):
        try:
            conn = self._pool.pop()
            _logger.debug(f"pool size: {len(self._pool)}")
            conn.set_in_use()
            return conn
        except IndexError:
            return self._create_connection()
        except:
            conn.set_returned()
            self._pool.append(conn)
            _logger.debug(f"pool size: {len(self._pool)}")
            raise

    # pylint:disable=try-except-raise
    def _create_connection(self):
        if self._num_connections >= self._max_size:
            # No room in the connection pool
            raise CreateConnectionError("CreateConnectionError")
        try:
            self._num_connections += 1
            _logger.debug(f"connections: {self._num_connections}")
            conn = Connection(*self._args, **self._kwargs)
            return conn
        except:
            # Cannot connect to SQL server
            self._num_connections -= 1
            _logger.debug(f"connections: {self._num_connections}")
            raise

    def return_connection(self, conn):
        conn.set_returned()
        self._pool.append(conn)
        _logger.debug(f"pool size: {len(self._pool)}")


def connection():
    elapsed_time = 0
    delay = 0.1
    while True:
        try:
            return _connection()
        except CreateConnectionError:
            # All connections are in use. Keep trying for a while.
            if elapsed_time > 5:
                raise
            time.sleep(delay)
            elapsed_time += delay


def _connection():
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
