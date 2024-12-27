import multiprocessing as mp
import asyncio
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
        # builds = await db.query_db('select * from builds')
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


async def _main():
    shutdown = ShutdownHandler()
    worker = Worker()

    async with asyncio.TaskGroup() as fire_and_forget:
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

            await worker.shutdown()
            try:
                await db.close_db()
            except sqlite3.OperationalError as e:
                if shutdown.shutdown:
                    print(e)
            print("Worker shutdown.")


def _run():
    print("Worker process running.")
    asyncio.run(_main())
    print("Worker process stopped.")



if __name__ == "__main__":
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    _run()
