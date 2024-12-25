import multiprocessing as mp
import asyncio
import sqlite3
import sys
import db_async
import signal


_proc = None
_queue = None


async def builds():
    builds = await db_async.query_db('select * from builds')
    print(builds)


async def count():
    print("One")
    await asyncio.sleep(1)
    print("Two")


class ShutdownHandler:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self.signal_caught)
        signal.signal(signal.SIGTERM, self.signal_caught)

    def signal_caught(self, *args):
        self.shutdown_gracefully("Signal caught")

    def shutdown_gracefully(self, reason):
        print(f"{reason}, will shutdown gracefully soon...", file=sys.stderr)
        self.shutdown = True


async def _main(q):
    shutdown = ShutdownHandler()
    try:
        await db_async.open_db()
    except sqlite3.OperationalError:
        print("Worker process cannot open the db")
        sys.exit()

    async with asyncio.TaskGroup() as group:
        group.create_task(count())
        group.create_task(builds())
        group.create_task(builds())
        group.create_task(builds())

        while not shutdown.shutdown:
            await asyncio.sleep(0.1)

    await db_async.close_db()


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
