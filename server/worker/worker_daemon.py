import asyncio
from asyncio import events
import sqlite3
import sys
import db
import signal


_proc = None
_queue = None


class Worker:
    def __init__(self):
        pass

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def update(self, fire_and_forget):
        # builds = await db_async.query_db('select * from builds')
        # print(builds)
        pass


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

shutdown = ShutdownHandler()
worker = Worker()

async def check_finished():
    print("check_finished")
    await asyncio.sleep(2)
    await _shutdown()
    raise Exception("finished!!!!!!!")

async def _main():
    async with asyncio.TaskGroup() as fire_and_forget:
        fire_and_forget.create_task(check_finished())

        while not shutdown.shutdown:
            try:
                await db.open_db()
            except sqlite3.OperationalError:
                await asyncio.sleep(1)
                continue
            await worker.initialize()
            print("Worker initialized.")

            while not shutdown.shutdown:
                try:
                    await worker.update(fire_and_forget)
                except sqlite3.OperationalError as e:
                    print(f'db error: {e.sqlite_errorname}')
                    break
                await asyncio.sleep(1)

async def _shutdown():
            await worker.shutdown()
            await db.close_db()
            print("Worker shutdown.")


def _run():
    print("Worker process running.")
    auto_restart = True
    while auto_restart:
        auto_restart = False
        try:
            asyncio.run(_main())
        except ExceptionGroup as e:
            if not shutdown.shutdown:
                auto_restart = True
            print("Exception caught")
            print(e.exceptions[0])
        # finally:
        #     asyncio.run(_shutdown())
    print("Worker process stopped.")


if __name__ == "__main__":
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    _run()
