import asyncio
from pymysql.err import OperationalError
from . import db
from ..shutdown_handler import ShutdownHandler
from ..project import Project
from ..request import Request
from ..build import Build
from ..task import Task


class Scheduler:
    def __init__(self, task_group):
        self._task_group = task_group
        # (project_id, target_branch or request_id): (request, task)
        self._requests = {}

    async def update(self):
        # Cancel tasks for aborted requests.
        for value in self._requests.values():
            db.commit()  # Needed for query to be up-to-date
            state = value[0].state()
            if state is None or state == 'ABORTED':
                await value[1].cancel()

        # Check for new requests.
        db.commit()  # Needed for query to be up-to-date
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
                self._requests[key] = (request, task)
                task.start(request)

    async def disconnected(self):
        for value in self._requests.values():
            await value[1].cancel()

    async def shutdown(self):
        for value in self._requests.values():
            await value[1].cancel()

    async def _process_request(self, request):
        print("Processing request: " f"{request.id()}")
        # Create a build job for each build configuration in the project. Jobs
        # will be picked up by workers.
        builds = []
        project = Project(request.project())
        for bc in project.build_configs():
            b = Build.create(request.id(), bc.name, project.remote_url(),
                             request.source_branch(), bc.build_script,
                             bc.work_dir)
            builds.append(b)
        db.commit()

        # Wait for workers to build all configurations.
        while any(b.is_open() for b in builds):
            await asyncio.sleep(2)

        succeeded = all(b.is_succeeded() for b in builds)
        request.set_state('SUCCEEDED' if succeeded else 'FAILED')
        db.commit()
        return succeeded

    def _on_request_complete(self, result, request):
        print(f"Request complete: {request.id()} result: {str(result)}")
        # TODO: abort builds if canceled
        key = (request.project(), request.target_branch()
               if request.integration() else request.id())
        del self._requests[key]


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
