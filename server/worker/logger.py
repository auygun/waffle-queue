import db_async as db


class Logger:
    def __init__(self, build_id_cb):
        self._build_id_cb = build_id_cb

    async def log(self, severity, message):
        async with db.cursor() as cursor:
            await cursor.execute("INSERT INTO logs "
                                 "(build_id, severity, message) "
                                 "VALUES (%s, %s, %s)",
                                 (self._build_id_cb(), severity, message))
        await db.commit()
