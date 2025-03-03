import asyncio
from dataclasses import dataclass
from datetime import timedelta
from pymysql.err import OperationalError, InterfaceError
from . import db
from ..shutdown_handler import ShutdownHandler
from ..task import Task
from ..project import Project
from ..request import Request
from ..build import Build
from ..server import Server
from ..logger import Logger


@dataclass
class RequestTraits:
    request: Request
    task: Task
    builds: list[Build]


# (project_id, target_branch | request_id): RequestTraits
type ScheduledRequests = dict[(int, str | int), RequestTraits]


class Scheduler:
    def __init__(self, task_group):
        self._task_group = task_group
        self._scheduled_requests: ScheduledRequests = {}
        self._server: Server = None
        self._logger = Logger(0)
        self._clear_log_task = Task(task_group, self._clear_log)

    def connected(self):
        # Server id 0 is the scheduler
        self._server = Server.create(0)

        self._clear_log_task.start()

        # Abort orphaned requests.
        for request in Request.get_building_requests():
            self._logger.info("Aborting orphaned requests! id: "
                              f"{request.id()}", commit=False)
            for build in Build.list(request.id()):
                build.set_aborted()
            request.set_aborted()
        db.commit()

    async def disconnected(self):
        await self._clear_log_task.cancel()

        for request_traits in self._scheduled_requests.copy().values():
            await request_traits.task.cancel()

    async def shutdown(self):
        await self._clear_log_task.cancel()

        for request_traits in self._scheduled_requests.copy().values():
            await request_traits.task.cancel()
        if self._server is not None:
            self._server.set_offline()
        db.commit()

    async def update(self):
        self._server.update_heartbeat()
        db.commit()

        # Set builds with offline workers as failed
        for build in Build.builds_in_progress():
            if Server(build.worker_id()).is_offline():
                self._logger.info("Set build failed (offline worker)! id: "
                                  f"{build.id()}", commit=False)
                build.set_failed()
        db.commit()

        # Cancel tasks for aborted requests.
        for request_traits in self._scheduled_requests.copy().values():
            if request_traits.request.is_aborted():
                await request_traits.task.cancel()

        # Check for new requests.
        for request in Request.get_new_requests():
            # Start processing build requests right away. Integration requests
            # that are for the same branch must wait until the previous request
            # completes.
            key = (request.project(), request.target_branch()
                   if request.integration() else request.id())
            if key not in self._scheduled_requests:
                request.set_building()
                db.commit()
                task = Task(
                    self._task_group, self._process_request,
                    self._on_request_complete)
                self._scheduled_requests[key] = RequestTraits(
                    request, task, [])
                task.start(key)

    async def _process_request(self, request_key):
        request_traits = self._scheduled_requests[request_key]
        print("Processing request: " f"{request_traits.request.id()}")
        self._logger.info("Processing request! id: "
                          f"{request_traits.request.id()}, "
                          f"branch: {request_traits.request.source_branch()}",
                          commit=False)

        try:
            self._server.set_busy()

            # Create a build job for each build configuration in the project.
            # Jobs will be picked up by workers.
            project = Project(request_traits.request.project())
            for config in project.build_configs():
                build = Build.create(request_traits.request.id(), config.name,
                                     project.remote_url(), project.name(),
                                     request_traits.request.source_branch(),
                                     config.build_script, config.work_dir,
                                     config.output_file
                                     if not request_traits.request.integration()
                                     and config.output_file else None)
                request_traits.builds.append(build)
            db.commit()

            # Wait for workers to build all configurations.
            while any(build.is_open() for build in request_traits.builds):
                await asyncio.sleep(2)

            return all(build.is_succeeded() for build in request_traits.builds)
        except (OperationalError, InterfaceError):
            # Can happen when task gets canceled due to disconnection
            pass

    def _on_request_complete(self, result, request_key):
        request_traits = self._scheduled_requests[request_key]
        print(f"Request complete: {request_traits.request.id()}"
              f" result: {str(result)}")
        self._logger.info(f"Request complete: {request_traits.request.id()}"
                          f" result: {str(result)}", commit=False)
        try:
            # Abort builds if request was canceled
            if result == 'CANCELED':
                for build in request_traits.builds:
                    build.set_aborted()
                request_traits.request.set_aborted()
            elif result:
                request_traits.request.set_succeeded()
            else:
                request_traits.request.set_failed()
            self._server.set_idle()
            db.commit()
        except (OperationalError, InterfaceError):
            # Can happen when task gets canceled due to disconnection
            pass
        finally:
            del self._scheduled_requests[request_key]

    async def _clear_log(self):
        while True:
            Logger.clear()
            db.commit()
            await asyncio.sleep(timedelta(days=1).total_seconds())


async def _main():
    shutdown = ShutdownHandler()

    async with asyncio.TaskGroup() as group:
        scheduler = Scheduler(group)

        while not shutdown.shutdown:
            try:
                db.ping()
            except OperationalError as e:
                print(e)
                await asyncio.sleep(5)
                continue

            try:
                scheduler.connected()
            except OperationalError as e:
                print(e)

            while not shutdown.shutdown:
                try:
                    await scheduler.update()
                except OperationalError as e:
                    print(e)
                    await scheduler.disconnected()
                    break
                await asyncio.sleep(1)

        try:
            await scheduler.shutdown()
        except (OperationalError, InterfaceError) as e:
            print(e)


def run():
    asyncio.run(_main())
