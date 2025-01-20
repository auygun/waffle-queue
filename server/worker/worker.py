#!/usr/bin/env python3

import asyncio
import signal
import sys
from pathlib import Path
from collections import deque

from pymysql.err import OperationalError
import db_async as db
from git import Git
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
        return None

    async def shutdown(self):
        await self._current_build_task.cancel()

    async def update(self):
        async with db.acquire():
            await db.commit()  # Needed for query to be up-to-date

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

    async def _start_build(self, build_request):
        async with db.acquire():
            self._current_build = build_request
            print("Starting build: "
                  f"{self._current_build.id()}, "
                  f"{await self._current_build.branch()}, "
                  f"{await self._current_build.state()}")
            await self._log('INFO',
                            "Starting build! id: "
                            f"{self._current_build.id()}, "
                            f"branch: {await self._current_build.branch()}")

            modules = deque([[
                Path("."),                           # git_dir
                Path("."),                           # work_tree
                "/home/auygun/code/proj2/proj.git",  # remote url
                "origin/" + "master"                 # refspec
            ]])

            while True:
                try:
                    module = modules.popleft()
                    print(module)
                    submodules = await self.prepare_module(*module)
                    for sm in submodules:
                        modules.append(sm)
                except RunProcessError as e:
                    print(e.output.splitlines()[-1])
                    return e.returncode
                except IndexError:
                    break

            # await self._runner.run(["python3", "build.py"],
            #                        cwd=work_tree_dir)

            return 0

    async def prepare_module(self, git_dir, work_tree, remote_url,
                             commit_or_branch):
        project_dir = Path.home() / "waffle_worker" / "proj"
        abs_work_tree = project_dir / "work_tree" / work_tree
        abs_work_tree.mkdir(parents=True, exist_ok=True)
        abs_git_dir = project_dir / "git" / git_dir
        abs_git_dir.mkdir(parents=True, exist_ok=True)

        await self._git.init_or_update(abs_git_dir, "origin", remote_url)
        await self._git.fetch(abs_git_dir, "origin",
                              commit_or_branch.split("/")[-1])
        await self._git.checkout(abs_git_dir, abs_work_tree, commit_or_branch)
        await self._git.clean(abs_git_dir, abs_work_tree)
        output = await self._git.init_submodules(abs_git_dir, abs_work_tree)

        submodules = []
        for sm in output.items():
            submodules.append([git_dir / "modules" / sm[0],
                               work_tree / sm[0],
                               sm[1][0],
                               sm[1][1]])
        return submodules

    def _on_build_finished(self, result):
        self._build_finished_task.start(result)

    async def _build_finished(self, result):
        async with db.acquire():
            if result == 'CANCELED':
                print("Build canceled!")
                await self._log('INFO', "Build canceled!")
            else:
                await db.commit()  # Needed for query to be up-to-date
                try:
                    if result == 0:
                        print("Build Succeeded!")
                        await self._current_build.set_state('SUCCEEDED')
                        await self._log('INFO', "Build succeeded!")
                    else:
                        print("Build failed!")
                        await self._current_build.set_state('FAILED')
                        await self._log('INFO', "Build failed!")
                except OperationalError as e:
                    print(f'db error: {e.args}')
                await db.commit()
        await self._reset_current_build()

    async def _reset_current_build(self):
        self._current_build = None

    async def _log(self, severity, message):
        if self._logger is not None:
            await self._logger.log(severity, message)


class ShutdownHandler:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self.signal_caught)
        signal.signal(signal.SIGTERM, self.signal_caught)

    # pylint:disable = unused-argument
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
                await db.open_db()
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
    await db.close_db()


def _run():
    asyncio.run(_main())


if __name__ == "__main__":
    _run()
