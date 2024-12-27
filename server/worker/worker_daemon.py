import multiprocessing as mp
import asyncio
import sys

from pymysql.err import OperationalError
import db
import signal


_proc = None
_queue = None


class Entity:
    def __init__(self, id):
        self.id = id
        self._valid = False

    def __eq__(self, other):
        return isinstance(other, Entity) and self.id == other.id

    def __hash__(self):
        return hash(self._id)

    @classmethod
    async def create(cls, id, refresh = True):
        self = cls(id)
        if refresh:
            await self.refresh()
        return self

    def is_valid(self):
        return self._valid


class Build(Entity):
    @staticmethod
    async def fetch(state, count=1, refresh=True):
        async with db.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT id FROM builds WHERE state=%s ORDER BY id LIMIT %s', (state, count))
                rows = await cur.fetchall()
                return [await Build.create(r[0], refresh) for r in rows]

    async def refresh(self):
        async with db.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT * FROM builds WHERE id=%s', self.id)
                if (cur.rowcount > 0):
                    r = await cur.fetchone()
                    self.branch = r[1]
                    self.state = r[2]
                    self._valid = True
                else:
                    self._valid = False


class Worker:
    def __init__(self):
        self._current_build = None
        self._current_build_task = None

    async def shutdown(self):
        pass

    async def update(self, group):
        for i in range(1, 10):
            b = await Build.create(i)
            if b.is_valid():
                print([b.id, b.branch, b.state])
            else:
                print(f'No build found with id {b.id}')

        if self._current_build is not None:
            await self._current_build.refresh()
            if self._current_build.state == 5:
                self._current_build_task.cancel()
                try:
                    await self._current_build_task
                except asyncio.CancelledError:
                    print("_current_build_task is cancelled now")
                    self._current_build = None
                    self._current_build_task = None

        if self._current_build is None:
            builds = await Build.fetch(1)
            if not builds:
                print("No build found in the queue")
            else:
                self._current_build_task = group.create_task(
                    self._start_build(builds[0]))

    async def _start_build(self, build):
        self._current_build = build
        print(f'Building: {build.id}, {build.branch}, {build.state}')


class ShutdownHandler:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self.signal_caught)
        signal.signal(signal.SIGTERM, self.signal_caught)

    def signal_caught(self, *args):
        self.shutdown_gracefully("Signal caught")

    def shutdown_gracefully(self, reason):
        print(f"{reason}, shuting down gracefully.", file=sys.stderr)
        self.shutdown = True


async def _main():
    shutdown = ShutdownHandler()
    worker = Worker()

    async with asyncio.TaskGroup() as group:
        while not shutdown.shutdown:
            try:
                await db.open_db()
            except OperationalError:
                await asyncio.sleep(5)
                continue

            while not shutdown.shutdown:
                try:
                    await worker.update(group)
                except OperationalError as e:
                    print(f'db error: {e.args}')
                    break
                await asyncio.sleep(5)

        await worker.shutdown()
        await db.close_db()


def _run():
    print("Worker process running.")
    asyncio.run(_main())
    print("Worker process stopped.")


if __name__ == "__main__":
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    _run()
