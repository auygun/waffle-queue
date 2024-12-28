import asyncio
import sys

from pymysql.err import OperationalError
import db
import signal


_proc = None
_queue = None


class Entity:
    def __init__(self, id):
        self._id = id

    def __eq__(self, other):
        return isinstance(other, Entity) and self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def id(self):
        return self._id


class Build(Entity):
    # This needs to match with the db enum
    State = {'REQUESTED': 1, 'BUILDING': 2,
             'SUCCEEDED': 3, 'FAILED': 4, 'ABORTED': 5}

    async def branch(self):
        return await self._fetch('branch')

    async def state(self):
        return await self._fetch('state')

    @staticmethod
    async def get_builds(state, count=1):
        async with db.cursor() as cur:
            await cur.execute('SELECT id FROM builds WHERE state=%s ORDER BY id LIMIT %s', (state, count))
            rows = await cur.fetchall()
            return [Build(r[0]) for r in rows]

    async def _fetch(self, field):
        async with db.cursor() as cur:
            await cur.execute(f'SELECT {field} FROM builds WHERE id=%s', (self.id()))
            r = await cur.fetchone()
            return r[0] if r is not None else None


class Worker:
    def __init__(self):
        self._current_build = None
        self._current_build_task = None

    async def shutdown(self):
        print("canceling!!!!!!!!!!!!!!!!!!!!!")
        self._current_build_task.cancel()
        await self._current_build_task
        pass

    def build_task_done_cb(self, task):
        print("build_task_done_cb!!!!!!!!!!!!!!!!!1")
        self._reset_current_build()

    async def update(self, group):
        for i in range(1, 10):
            b = Build(i)
            print([b.id(), await b.branch(), await b.state()])

        if self._current_build is not None:
            print(await self._current_build.state())
            if await self._current_build.state() == 'REQUESTED':
                print("canceling!!!!!!!!!!!!!!!!!!!!!")
                self._current_build_task.cancel()
                await self._current_build_task

        if self._current_build is None:
            builds = await Build.get_builds(Build.State['REQUESTED'])
            if not builds:
                print("No build found in the queue")
            else:
                self._current_build_task = group.create_task(
                    self._start_build(builds[0]))
                self._current_build_task.add_done_callback(
                    self.build_task_done_cb)

    async def _start_build(self, build):
        try:
            self._current_build = build
            print(f'Building: {build.id()}, {await build.branch()}, {await build.state()}')
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("_current_build_task is cancelled now")

    def _reset_current_build(self):
        print("_reset_current_build is cancelled now")
        self._current_build = None


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
