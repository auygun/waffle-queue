import multiprocessing as mp
import asyncio
import db_async

# class Worker:
#     def __init__(self):
#         self.aaa = 0


async def builds():
    builds = await db_async.query_db('select * from builds')
    print(builds)


async def count():
    print("One")
    await asyncio.sleep(1)
    print("Two")


async def main():
    await db_async.inti_db()
    await asyncio.gather(count(), builds(), builds(), builds())


def _run(q):
    asyncio.run(main())


def start():
    mp.set_start_method('fork')
    q = mp.Queue()
    p = mp.Process(target=_run, args=(q,))
    p.start()
