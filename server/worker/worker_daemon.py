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

    async def set_state(self, value):
        return await self._update('state', value)

    @staticmethod
    async def get_builds(state, count=1):
        rows = await db.query('SELECT id FROM builds WHERE state=%s ORDER BY id LIMIT %s', (state, count))
        return [Build(r[0]) for r in rows]

    async def _fetch(self, field):
        rows = await db.query(f'SELECT {field} FROM builds WHERE id=%s', (self.id()), one=True)
        return rows[0] if rows is not None else None

    async def _update(self, field, value):
        await db.update(f'UPDATE builds SET {field}=%s WHERE id=%s', (value, self.id()))


class Task:
    def __init__(self, task_group, coro_func, done_cb=None):
        self._task_group = task_group
        self._coro_func = coro_func
        self._task = None
        self._done_cb = done_cb

    def running(self):
        return self._task != None

    def start(self, *args):
        if not self._task:
            self._task = self._task_group.create_task(self._coro_func(args))
            self._task.add_done_callback(self._done)

    async def cancel(self):
        if self._task:
            task = self._task
            self._task = None
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def _done(self, task):
        self._task = None
        if self._done_cb:
            try:
                result = task.result()
            except asyncio.CancelledError as e:
                self._done_cb('CANCELED')
            else:
                self._done_cb(result)


class Worker:
    def __init__(self, task_group):
        self._current_build = None
        self._current_build_task = Task(
            task_group, self._start_build, self._on_build_finished)
        self._build_finished_task = Task(task_group, self._build_finished)

    async def shutdown(self):
        await self._current_build_task.cancel()
        pass

    async def update(self):
        if self._current_build is not None and self._current_build_task.running():
            if await self._current_build.state() == 'ABORTED':
                await self._current_build_task.cancel()

        if self._current_build is None:
            builds = await Build.get_builds(Build.State['BUILDING'], count=1000)
            if not builds:
                builds = await Build.get_builds(Build.State['REQUESTED'], count=1000)
            if not builds:
                print("No build found in the queue")
            else:
                for b in builds:
                    print([b.id(), await b.branch(), await b.state()])
                self._current_build_task.start(builds[0])

    async def disconnected(self):
        if self._current_build is not None:
            await self._build_finished_task.cancel()
            await self._current_build_task.cancel()
            await self._reset_current_build()

    async def _start_build(self, *args):
        self._current_build = args[0][0]
        await self._current_build.set_state(Build.State['BUILDING'])
        print(f'Building: {self._current_build.id()}, {await self._current_build.branch()}, {await self._current_build.state()}')
        await asyncio.sleep(1)
        return 1

    def _on_build_finished(self, result):
        self._build_finished_task.start(result)
        pass

    async def _build_finished(self, *args):
        result = args[0][0]
        try:
            if result == 'CANCELED':
                print(f"_build_finished: canceled")
            elif result == 0:
                print(f"_build_finished: succeeded")
                await self._current_build.set_state(Build.State['SUCCEEDED'])
            else:
                print(f"_build_finished: failed")
                await self._current_build.set_state(Build.State['FAILED'])
        except OperationalError:
            pass
        await self._reset_current_build()

    async def _reset_current_build(self):
        print("_reset_current_build()")
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

    async with asyncio.TaskGroup() as group:
        worker = Worker(group)

        while not shutdown.shutdown:
            try:
                await db.open()
            except OperationalError:
                await asyncio.sleep(5)
                continue

            while not shutdown.shutdown:
                try:
                    await worker.update()
                except OperationalError as e:
                    print(f'db error: {e.args}')
                    await worker.disconnected()
                    break
                await asyncio.sleep(5)

        await worker.shutdown()
    await db.close()


def _run():
    print("Worker process running.")
    asyncio.run(_main())
    print("Worker process stopped.")


if __name__ == "__main__":
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    _run()
