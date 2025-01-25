import asyncio
import signal
import sys
from pathlib import Path
from collections import deque

from pymysql.err import OperationalError
from . import db, runner, git
from .task import Task
from ..build import Build
from ..logger import Logger


class Worker:
    def __init__(self, task_group):
        self._current_build = None
        self._current_build_task = Task(
            task_group, self._start_build, self._on_build_finished)
        self._logger = Logger(self.get_current_build_id)

    def get_current_build_id(self):
        if self._current_build is not None:
            return self._current_build.id()
        return None

    def project_dir(self):
        return Path.home() / "waffle_worker" / "proj"

    def git_root(self):
        return self.project_dir() / "git"

    def work_tree_root(self):
        return self.project_dir() / "work_tree"

    async def shutdown(self):
        await self._current_build_task.cancel()

    async def update(self):
        if (self._current_build is not None and
                self._current_build_task.running()):
            db.commit()  # Needed for query to be up-to-date
            state = self._current_build.state()
            if state is None or state == 'ABORTED':
                await self._current_build_task.cancel()

        if self._current_build is None:
            build_request = Build.pop_next_build_request()
            if build_request is not None:
                self._current_build_task.start(build_request)

    async def disconnected(self):
        if self._current_build is not None:
            await self._current_build_task.cancel()

    async def _start_build(self, build_request):
        self._current_build = build_request
        print("Starting build: "
              f"{self._current_build.id()}, "
              f"{self._current_build.branch()}")
        self._logger.info("Starting build! id: "
                          f"{self._current_build.id()}, "
                          f"branch: {self._current_build.branch()}")

        modules = deque([[
            Path("."),                           # git_dir
            Path("."),                           # work_tree
            "/home/auygun/code/proj2/proj.git",  # remote url
            "origin/" + "master"                 # branch
        ]])

        try:
            while True:
                try:
                    module = modules.popleft()
                except IndexError:
                    break
                print(module)
                submodules = await self._prepare_module(*module)
                for sm in submodules:
                    modules.append(sm)

            build_script = Path("build/build.py")
            await runner.run(["python3", str(build_script)],
                             cwd=self.work_tree_root(), logger=self._logger)
        except runner.RunProcessError as e:
            print(e.output.splitlines()[-1])
            return e.returncode

        return 0

    def _on_build_finished(self, result):
        if result == 'CANCELED':
            print("Build canceled!")
            self._logger.info("Build canceled!")
        else:
            db.commit()
            try:
                if result == 0:
                    print("Build Succeeded!")
                    self._current_build.set_state('SUCCEEDED')
                    self._logger.info("Build succeeded!")
                else:
                    print("Build failed!")
                    self._current_build.set_state('FAILED')
                    self._logger.info("Build failed!")
            except OperationalError as e:
                print(e)
            db.commit()
        self._reset_current_build()

    def _reset_current_build(self):
        self._current_build = None

    async def _prepare_module(self, git_dir, work_tree, remote_url,
                              commit_or_branch):
        abs_work_tree = self.work_tree_root() / work_tree
        abs_work_tree.mkdir(parents=True, exist_ok=True)
        abs_git_dir = self.git_root() / git_dir
        abs_git_dir.mkdir(parents=True, exist_ok=True)

        await git.init_or_update(abs_git_dir, "origin", remote_url,
                                 logger=self._logger)
        await git.fetch(abs_git_dir, "origin", commit_or_branch.split("/")[-1],
                        logger=self._logger)
        await git.checkout(abs_git_dir, abs_work_tree, commit_or_branch,
                           logger=self._logger)
        await git.clean(abs_git_dir, abs_work_tree, logger=self._logger)
        output = await git.init_submodules(abs_git_dir, abs_work_tree,
                                           logger=self._logger)

        submodules = []
        for sm in output.items():
            submodules.append([git_dir / "modules" / sm[0],
                               work_tree / sm[0],
                               sm[1][0],
                               sm[1][1]])
        return submodules


class ShutdownHandler:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self.signal_caught)
        signal.signal(signal.SIGTERM, self.signal_caught)

    def signal_caught(self, *_args):
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
                db.ping()
            except OperationalError as e:
                print(e)
                await asyncio.sleep(5)
                continue

            while not shutdown.shutdown:
                try:
                    await worker.update()
                except OperationalError as e:
                    print(e)
                    await worker.disconnected()
                    break
                await asyncio.sleep(1)

        await worker.shutdown()


def run():
    asyncio.run(_main())
