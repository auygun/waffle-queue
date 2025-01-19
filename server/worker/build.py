import db_async as db
from entity import Entity


class Build(Entity):
    async def branch(self):
        return await self._fetch('branch')

    async def state(self):
        return await self._fetch('state')

    async def set_state(self, value):
        return await self._update('state', value)

    @staticmethod
    async def pop_next_build_request():
        # Fetch the next available build request from the queue and mark it as
        # building.
        build = None
        async with db.cursor() as cursor:
            build_ids = await cursor.execute("SELECT id FROM builds "
                                             "WHERE state='REQUESTED' "
                                             "ORDER BY id "
                                             "FOR UPDATE SKIP LOCKED")
            build_ids = await cursor.fetchone()
            if build_ids is not None:
                build = Build(build_ids[0])
                await build.set_state('BUILDING')
            await db.commit()
        return build

    async def _fetch(self, field):
        async with db.cursor() as cursor:
            await cursor.execute(f"SELECT {field} FROM builds "
                                 "WHERE id=%s",
                                 (self.id()))
            r = await cursor.fetchone()
            return r[0] if r is not None else None

    async def _update(self, field, value):
        async with db.cursor() as cursor:
            await cursor.execute("UPDATE builds "
                                 f"SET {field}=%s "
                                 "WHERE id=%s",
                                 (value, self.id()))
