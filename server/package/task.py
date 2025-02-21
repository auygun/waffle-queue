import asyncio


class Task:
    def __init__(self, task_group, coro_func, done_cb=None):
        self._task_group = task_group
        self._coro_func = coro_func
        self._task = None
        self._done_cb = done_cb
        self._args = None

    def running(self):
        return self._task is not None

    def start(self, *args):
        if not self._task:
            self._args = args
            self._task = self._task_group.create_task(self._coro_func(*args))
            self._task.add_done_callback(self._done)

    async def cancel(self):
        if self._task:
            task = self._task
            self._task = None
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def _done(self, task):
        self._task = None
        if self._done_cb:
            try:
                result = task.result()
            except asyncio.CancelledError:
                self._done_cb('CANCELED', *self._args)
            else:
                self._done_cb(result, *self._args)
