import aiosqlite
from datetime import datetime


_db = None


async def open_db():
    print("db_async: Opening db")
    global _db
    _db = await aiosqlite.connect("file:builder.db?mode=rw", uri=True)
    _db.row_factory = lambda cursor, row: dict(
        (cursor.description[idx][0], value) for idx, value in enumerate(row))
    aiosqlite.register_converter(
        "timestamp", lambda v: datetime.fromisoformat(v.decode()))


async def close_db():
    global _db
    if _db is not None:
        print("db_async:Closing db")
        await _db.commit()
        await _db.close()
        _db = None


def get_db():
    return _db


async def query_db(query, args=(), one=False):
    async with _db.execute(query, args) as cursor:
        rows = await cursor.fetchall()
    return (rows[0] if rows else None) if one else rows
