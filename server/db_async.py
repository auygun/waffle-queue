import aiomysql
import contextvars

_create_db = '''
CREATE DATABASE IF NOT EXISTS builder;
DROP TABLE IF EXISTS builder.builds;
CREATE TABLE IF NOT EXISTS builder.builds (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    branch TEXT NOT NULL,
    state ENUM ('REQUESTED', 'BUILDING', 'SUCCEEDED', 'FAILED', 'ABORTED') NOT NULL);
'''
# INSERT INTO builder.builds (branch, state) VALUES ("master1", 'REQUESTED');
# INSERT INTO builder.builds (branch, state) VALUES ("stable2", 'REQUESTED');
# INSERT INTO builder.builds (branch, state) VALUES ("master3", 'REQUESTED');
# INSERT INTO builder.builds (branch, state) VALUES ("stable4", 'REQUESTED');
# INSERT INTO builder.builds (branch, state) VALUES ("master5", 'REQUESTED');
# INSERT INTO builder.builds (branch, state) VALUES ("stable6", 'REQUESTED');
# INSERT INTO builder.builds (branch, state) VALUES ("master7", 'REQUESTED');
# INSERT INTO builder.builds (branch, state) VALUES ("stable8", 'REQUESTED');
# '''

_pool = None
_current_conn = contextvars.ContextVar('connection')


class PoolAcquireAndStoreContextManager:
    """Context manager wrapping around _PoolAcquireContextManager

    Stores the connection object in a context variable to make it available in
    the task that acquires it from the pool. This enables a single connection to
    be acquired and used in each task.
    It's stored in _current_conn context variable which is accessed by cursor(),
    commit() and rollback() functions below.
    """

    __slots__ = ('_token', '_man')

    def __init__(self, man):
        self._man = man
        self._token = None

    async def __aenter__(self):
        global _current_conn
        conn = await self._man.__aenter__()
        self._token = _current_conn.set(conn)
        return conn

    async def __aexit__(self, exc_type, exc, tb):
        global _current_conn
        _current_conn.reset(self._token)
        await self._man.__aexit__(exc_type, exc, tb)


async def open():
    print("Opening db")
    global _pool
    _pool = await aiomysql.create_pool(host='127.0.0.1', port=3306,
                                       user='mysql', password='mysql',
                                       db='builder', autocommit=False)
    # async with _pool.acquire() as conn:
    #     async with conn.cursor() as cursor:
    #         await cursor.execute(_create_db)


async def close():
    global _pool
    if _pool is not None:
        print("Closing db")
        _pool.close()
        await _pool.wait_closed()
        _pool = None


def acquire():
    return PoolAcquireAndStoreContextManager(_pool.acquire())


def cursor():
    return _current_conn.get().cursor()


def commit():
    return _current_conn.get().commit()


def rollback():
    return _current_conn.get().rollback()


async def now():
    async with cursor() as cur:
        await cur.execute("SELECT NOW()")
        return await cur.next()[0]
