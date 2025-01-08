#!/usr/bin/env python3

import asyncio
import sys
from pymysql.err import OperationalError
import db_async as db
import signal


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
            id = await cursor.execute(f"SELECT id FROM builds WHERE state='REQUESTED' ORDER BY id FOR UPDATE SKIP LOCKED")
            id = await cursor.fetchone()
            if id is not None:
                build = Build(id[0])
                await build.set_state('BUILDING')
            await db.commit()
        return build

    async def _fetch(self, field):
        async with db.cursor() as cursor:
            await cursor.execute(f'SELECT {field} FROM builds WHERE id=%s', (self.id()))
            r = await cursor.fetchone()
            return r[0] if r is not None else None

    async def _update(self, field, value):
        async with db.cursor() as cursor:
            await cursor.execute(f'UPDATE builds SET {field}=%s WHERE id=%s', (value, self.id()))


class Task:
    def __init__(self, task_group, coro_func, done_cb=None):
        self._task_group = task_group
        self._coro_func = coro_func
        self._task = None
        self._done_cb = done_cb

    def running(self):
        return self._task is not None

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

    async def update(self):
        async with db.acquire():
            # 1020, "Record has changed since last read in table 'builds'"
            await db.rollback()

            if self._current_build is not None and self._current_build_task.running():
                state = await self._current_build.state()
                if state is None or state == 'ABORTED':
                    await self._current_build_task.cancel()

            if self._current_build is None:
                build_request = await Build.pop_next_build_request()
                if build_request is not None:
                    self._current_build_task.start(build_request)
                else:
                    print("Idle")

    async def disconnected(self):
        if self._current_build is not None:
            await self._build_finished_task.cancel()
            await self._current_build_task.cancel()
            await self._reset_current_build()

    async def _start_build(self, *args):
        async with db.acquire():
            self._current_build = args[0][0]
            print(f'Building: {self._current_build.id()}, {await self._current_build.branch()}, {await self._current_build.state()}')
            await asyncio.sleep(5)
            return 1

    def _on_build_finished(self, result):
        self._build_finished_task.start(result)
        pass

    async def _build_finished(self, *args):
        result = args[0][0]
        if result == 'CANCELED':
            print(f"_build_finished: canceled")
        else:
            async with db.acquire():
                # 1020, "Record has changed since last read in table 'builds'"
                await db.rollback()
                try:
                    if result == 0:
                        print(f"_build_finished: succeeded")
                        await self._current_build.set_state('SUCCEEDED')
                    else:
                        print(f"_build_finished: failed")
                        await self._current_build.set_state('FAILED')
                except OperationalError as e:
                    print(f'db error: {e.args}')
                await db.commit()
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
                await asyncio.sleep(1)

        await worker.shutdown()
    await db.close()


def _run():
    asyncio.run(_main())


if __name__ == "__main__":
    _run()
