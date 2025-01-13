#!/usr/bin/env python3

import asyncio
import sys
from pymysql.err import OperationalError
import db_async as db
import signal
from async_path import AsyncPath
import git


class RunProcessError(Exception):
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output


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
            print(f'Starting build: {self._current_build.id()}, {await self._current_build.branch()}, {await self._current_build.state()}')
            await self._log('INFO', f'Starting build! id: {self._current_build.id()}, branch: {await self._current_build.branch()}')

            project_dir = await AsyncPath.home() / "worker"
            work_tree_dir = project_dir / "work_tree"
            await work_tree_dir.mkdir(parents=True, exist_ok=True)
            git_dir = project_dir / "git"

            try:
                if await (git_dir / "config").exists():
                    await self._set_remote(git_dir, "origin", "https://github.com/auygun/kaliber.git")
                else:
                    await self._run(git.init(git_dir))
                    await self._run(git.add_remote(git_dir, "origin", "https://github.com/auygun/kaliber.git"))
                await self._run(git.fetch(git_dir, "origin", "master"))
                await self._run(git.clean(git_dir, work_tree_dir))
                await self._run(git.checkout(git_dir, work_tree_dir, "master"))
            except RunProcessError as e:
                print(e.output.splitlines()[-1])
                return e.returncode

            return 0

    def _on_build_finished(self, result):
        self._build_finished_task.start(result)
        pass

    async def _build_finished(self, *args):
        result = args[0][0]
        async with db.acquire():
            if result == 'CANCELED':
                print(f"_build_finished: canceled")
                await self._log('INFO', "Build canceled!")
            else:
                # 1020, "Record has changed since last read in table 'builds'"
                await db.rollback()
                try:
                    if result == 0:
                        print("_build_finished: succeeded")
                        await self._current_build.set_state('SUCCEEDED')
                        await self._log('INFO', "Build succeeded!")
                    else:
                        print(f"_build_finished: failed")
                        await self._current_build.set_state('FAILED')
                        await self._log('INFO', "Build failed!")
                except OperationalError as e:
                    print(f'db error: {e.args}')
                await db.commit()
        await self._reset_current_build()

    async def _reset_current_build(self):
        print("_reset_current_build()")
        self._current_build = None

    async def _set_remote(self, git_dir, name, url):
        existing_url = None
        _, remotes = await self._run(git.list_remotes(git_dir))
        for existing_remote in remotes.splitlines():
            remote_name, remote_url, _ = existing_remote.split()
            if remote_name == name:
                existing_url = remote_url
                break

        if existing_url is None:
            await self._run(git.add_remote(git_dir, name, url))
        elif existing_url != url:
            await self._run(git.set_remote_url(git_dir, name, url))

    async def _log(self, severity, message):
        async with db.cursor() as cursor:
            await cursor.execute("INSERT INTO logs (build_id, severity, message) VALUES (%s, %s, %s)",
                                 (self._current_build.id(), severity, message))
        await db.commit()

    async def _run(self, cmd, cwd=None, env=None):
        await self._log('TRACE', f"Run: '{' '.join(cmd)}'")
        proc = await asyncio.create_subprocess_exec(
            cmd[0],
            *cmd[1:],
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            process_group=0
        )
        try:
            stdout, _ = await proc.communicate()
            output = stdout.decode("latin-1")
            for line in output.splitlines():
                await self._log('TRACE', line)
            await self._log('TRACE', f"Exit code: {proc.returncode}")
            if proc.returncode:
                raise RunProcessError(proc.returncode, output)
            return proc.returncode, output
        except asyncio.CancelledError:
            async with db.acquire():
                await self._log('TRACE', "Terminating")
                try:
                    proc.terminate()
                    await proc.wait()
                except ProcessLookupError:
                    await self._log('TRACE', "Terminated")
            raise


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
