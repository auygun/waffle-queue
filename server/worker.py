import multiprocessing as mp
import asyncio
import sqlite3
import sys
import db_async
import signal


_proc = None
_queue = None


class Worker:
    def __init__(self, q):
        self._q = q

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def update(self, fire_and_forget):
        builds = await db_async.query_db('select * from builds')
        print(builds)


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


async def _main(q):
    shutdown = ShutdownHandler()
    worker = Worker(q)

    async with asyncio.TaskGroup() as fire_and_forget:
        while not shutdown.shutdown:
            try:
                await db_async.open_db()
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
                await db_async.close_db()
            except sqlite3.OperationalError as e:
                if shutdown.shutdown:
                    print(e)
            print("Worker shutdown.")


def _run(q):
    print("Worker process running.")
    asyncio.run(_main(q))
    print("Worker process stopped.")


def start():
    global _proc
    global _queue
    if _proc is None:
        mp.set_start_method('fork')
        _queue = mp.Queue()
        _proc = mp.Process(target=_run, args=(_queue,))
        _proc.start()


def stop():
    if _proc is not None:
        _queue.close()
        _proc.terminate()
        _proc.join()
