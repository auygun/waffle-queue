import aiomysql


_create_db = '''
CREATE DATABASE IF NOT EXISTS builder;
DROP TABLE IF EXISTS builder.builds;
CREATE TABLE IF NOT EXISTS builder.builds (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    branch TEXT NOT NULL,
    state ENUM ('REQUESTED', 'BUILDING', 'SUCCEEDED', 'FAILED', 'ABORTED') NOT NULL);
INSERT INTO builder.builds (branch, state) VALUES ("master1", 1);
INSERT INTO builder.builds (branch, state) VALUES ("stable2", 2);
INSERT INTO builder.builds (branch, state) VALUES ("master3", 3);
INSERT INTO builder.builds (branch, state) VALUES ("stable4", 4);
INSERT INTO builder.builds (branch, state) VALUES ("master5", 5);
INSERT INTO builder.builds (branch, state) VALUES ("stable6", 1);
INSERT INTO builder.builds (branch, state) VALUES ("master7", 2);
INSERT INTO builder.builds (branch, state) VALUES ("stable8", 3);
'''

_pool = None


async def open_db():
    print("Opening db")
    global _pool
    _pool = await aiomysql.create_pool(host='127.0.0.1', port=3306,
                                       user='mysql', password='mysql',
                                       db='builder', autocommit=False)
    # async with _pool.acquire() as conn:
    #     async with conn.cursor() as cursor:
    #         await cursor.execute(_create_db)
    #     await conn.commit()


async def close_db():
    global _pool
    if _pool is not None:
        print("Closing db")
        _pool.close()
        await _pool.wait_closed()
        _pool = None


def conn():
    return _pool.acquire()


async def now():
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT NOW()")
            return await cur.next()[0]
