import asyncio
from pathlib import Path
from collections import deque
from pymysql.err import OperationalError, InterfaceError
from . import db
from .. import runner, git
from ..shutdown_handler import ShutdownHandler
from ..task import Task
from ..build import Build
from ..server import Server
from ..logger import Logger


class Worker:
    def __init__(self, task_group, server_id):
        self._current_build = None
        self._current_build_task = Task(
            task_group, self._start_build, self._on_build_finished)
        self._server = Server.create(server_id)
        self._logger = Logger(server_id)

    def result_dir(self):
        return Path.home() / "waffle_worker" / "result"

    def project_dir(self):
        return Path.home() / "waffle_worker" / "proj"

    def git_root(self):
        return self.project_dir() / "git"

    def work_tree_root(self):
        return self.project_dir() / "work_tree"

    async def shutdown(self):
        await self._current_build_task.cancel()
        self._server.set_status('OFFLINE')
        db.commit()

    async def update(self):
        self._server.update_heartbeat()
        db.commit()

        # Cancel task if the current build request was aborted.
        if (self._current_build is not None and
                self._current_build_task.running()):
            state = self._current_build.state()
            if state is None or state == 'ABORTED':
                await self._current_build_task.cancel()

        # Check for new requests if this worker is idle.
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
              f"{self._current_build.source_branch()}")
        self._logger.info("Starting build! id: "
                          f"{self._current_build.id()}, "
                          f"branch: {self._current_build.source_branch()}")

        try:
            self._server.set_status('BUSY')
            db.commit()
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            pass

        modules = deque([[
            Path("."),  # git_dir
            Path("."),  # work_tree
            self._current_build.remote_url(),  # remote url
            "origin/" + self._current_build.source_branch()  # branch
        ]])

        try:
            # Fetch and checkout root module and all submodules.
            while True:
                try:
                    module = modules.popleft()
                except IndexError:
                    break
                print(module)
                submodules = await self._prepare_module(*module)
                for sm in submodules:
                    modules.append(sm)

            # Run the build script.
            result_dir = self.result_dir() / str(self._current_build.id())
            result_dir.mkdir(parents=True, exist_ok=True)
            log_file = result_dir / "build.log"
            build_script = Path(self._current_build.build_script())
            cwd = Path(self._current_build.work_dir())
            with open(log_file, "wt", encoding="utf-8") as log_file_fd:
                await runner.run(["python3",
                                  str(self.work_tree_root() / build_script)],
                                 cwd=self.work_tree_root() / cwd,
                                 output=log_file_fd,
                                 logger=self._logger)
        except runner.RunProcessError as e:
            return e.returncode

        return 0

    def _on_build_finished(self, result, _):
        try:
            if result == 'CANCELED':
                print("Build canceled!")
                self._logger.info("Build canceled!")
            elif result == 0:
                print("Build succeeded!")
                self._current_build.set_state('SUCCEEDED')
                self._logger.info("Build succeeded!")
            else:
                print("Build failed!")
                self._current_build.set_state('FAILED')
                self._logger.info("Build failed!")
            self._server.set_status('IDLE')
            db.commit()
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            pass
        finally:
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


async def _main(server_id):
    shutdown = ShutdownHandler()

    async with asyncio.TaskGroup() as group:
        worker = Worker(group, server_id)

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


def run(server_id):
    asyncio.run(_main(server_id))
