import aiomysql


_pool = None


async def open_db():
    print("Opening db")
    global _pool
    pool = await aiomysql.create_pool(host='127.0.0.1', port=3306,
                                      user='mysql', password='mysql',
                                      db=None, autocommit=False)

async def close_db():
    global _pool
    if _pool is not None:
        print("Closing db")
        _pool.close()
        await _pool.wait_closed()

def get_db():
    return _pool.acquire()


async def now():
    async with _pool.acquire() as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT NOW()")
            return await cursor.next()[0]
