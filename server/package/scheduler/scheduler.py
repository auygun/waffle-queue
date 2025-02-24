import asyncio
from dataclasses import dataclass
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
class RequestData:
    request: Request
    task: Task
    builds: list[Build]


class Scheduler:
    def __init__(self, task_group):
        self._task_group = task_group
        # (project_id, target_branch or request_id): RequestData
        self._requests = {}
        # Server id 0 is the scheduler
        self._server = Server.create(0)
        self._logger = Logger(0)

    async def update(self):
        self._server.update_heartbeat()
        db.commit()

        # Cancel tasks for aborted requests.
        for request_data in self._requests.copy().values():
            state = request_data.request.state()
            if state is None or state == 'ABORTED':
                await request_data.task.cancel()

        # Check for new requests.
        new_requests = Request.get_new_requests()
        for request in new_requests:
            # Start processing build request right away. Integration requests
            # that are for the same branch must wait until the previous request
            # completes.
            key = (request.project(), request.target_branch()
                   if request.integration() else request.id())
            if key not in self._requests:
                request.set_state('BUILDING')
                db.commit()
                task = Task(
                    self._task_group, self._process_request,
                    self._on_request_complete)
                self._requests[key] = RequestData(request, task, [])
                task.start(key)

    async def disconnected(self):
        for request_data in self._requests.copy().values():
            await request_data.task.cancel()

    async def shutdown(self):
        for request_data in self._requests.copy().values():
            await request_data.task.cancel()
        self._server.set_status('OFFLINE')
        db.commit()

    async def _process_request(self, request_key):
        request_data = self._requests[request_key]
        print("Processing request: " f"{request_data.request.id()}")
        self._logger.info("Processing request! id: "
                          f"{request_data.request.id()}")

        try:
            self._server.set_status('BUSY')

            # Create a build job for each build configuration in the project.
            # Jobs will be picked up by workers.
            project = Project(request_data.request.project())
            for bc in project.build_configs():
                b = Build.create(request_data.request.id(), bc.name,
                                 project.remote_url(),
                                 request_data.request.source_branch(),
                                 bc.build_script, bc.work_dir)
                request_data.builds.append(b)
            db.commit()

            # Wait for workers to build all configurations.
            while any(b.is_open() for b in request_data.builds):
                await asyncio.sleep(2)

            return all(b.is_succeeded() for b in request_data.builds)
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            pass

    def _on_request_complete(self, result, request_key):
        request_data = self._requests[request_key]
        print(f"Request complete: {request_data.request.id()}"
              f" result: {str(result)}")
        self._logger.info(f"Request complete! result: {str(result)}")
        try:
            # Abort builds if request was canceled
            if result == 'CANCELED':
                for b in request_data.builds:
                    b.abort()
                self._logger.info("Request canceled!")
            elif result:
                request_data.request.set_state('SUCCEEDED')
                self._logger.info("Request succeeded!")
            else:
                request_data.request.set_state('FAILED')
                self._logger.info("Request failed!")
            self._server.set_status('BUSY')
            db.commit()
        except InterfaceError:
            # Can happen when task gets canceled due to disconnection
            pass
        finally:
            del self._requests[request_key]


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

            while not shutdown.shutdown:
                try:
                    await scheduler.update()
                except OperationalError as e:
                    print(e)
                    await scheduler.disconnected()
                    break
                await asyncio.sleep(1)

        await scheduler.shutdown()


def run():
    asyncio.run(_main())
