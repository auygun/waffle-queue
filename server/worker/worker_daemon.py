import multiprocessing as mp
import asyncio
import sys

from pymysql.err import OperationalError
import db
import signal


_proc = None
_queue = None


class Entity:
    def __init__(self, id):
        self.id = id

    @classmethod
    async def create(cls, id):
        self = cls(id)
        await self.refresh()
        return self


class Build(Entity):
    async def refresh(self):
        async with db.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT * FROM builds WHERE id=%s', self.id)
                r = await cur.fetchone()
                self.branch = r[1]
                self.state = r[2]


class Worker:
    def __init__(self):
        pass

    async def shutdown(self):
        pass

    async def update(self, fire_and_forget):
        try:
            b = await Build.create(13)
        except TypeError as e:
            print(e)
        else:
            print([b.id, b.branch, b.state])


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
            except OperationalError:
                await asyncio.sleep(5)
                continue

            while not shutdown.shutdown:
                try:
                    await worker.update(fire_and_forget)
                except OperationalError as e:
                    print(f'db error: {e.args}')
                    break
                await asyncio.sleep(5)

        await worker.shutdown()
        await db.close_db()


def _run():
    print("Worker process running.")
    asyncio.run(_main())
    print("Worker process stopped.")


if __name__ == "__main__":
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    _run()
