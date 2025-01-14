#!/usr/bin/env python3

import asyncio
import signal
import sys
from pymysql.err import OperationalError

import db_async as db
from git import Git
from async_path import AsyncPath
from task import Task
from build import Build
from runner import Runner
from runner import RunProcessError
from logger import Logger


class Worker:
    def __init__(self, task_group):
        self._current_build = None
        self._current_build_task = Task(
            task_group, self._start_build, self._on_build_finished)
        self._build_finished_task = Task(task_group, self._build_finished)
        self._logger = Logger(self.get_current_build_id)
        self._runner = Runner(self._logger)
        self._git = Git(self._runner)

    def get_current_build_id(self):
        if self._current_build is not None:
            return self._current_build.id()

    async def shutdown(self):
        await self._current_build_task.cancel()

    async def update(self):
        async with db.acquire():
            # 1020, "Record has changed since last read in table 'builds'"
            await db.rollback()

            if (self._current_build is not None and
                    self._current_build_task.running()):
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
            print("Starting build: "
                  f"{self._current_build.id()}, "
                  f"{await self._current_build.branch()}, "
                  f"{await self._current_build.state()}")
            await self._log('INFO',
                            "Starting build! id: "
                            f"{self._current_build.id()}, "
                            f"branch: {await self._current_build.branch()}")

            project_dir = await AsyncPath.home() / "worker"
            work_tree_dir = project_dir / "work_tree"
            await work_tree_dir.mkdir(parents=True, exist_ok=True)
            git_dir = project_dir / "git"

            try:
                await self._git.init_or_update(git_dir, "origin",
                                               "https://github.com/auygun/"
                                               "kaliber.git")
                await self._git.fetch(git_dir, "origin", "master")
                await self._git.clean(git_dir, work_tree_dir)
                await self._git.checkout(git_dir, work_tree_dir,
                                         "origin/master")
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

    async def _log(self, severity, message):
        if self._logger is not None:
            await self._logger.log(severity, message)


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
