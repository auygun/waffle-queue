import asyncio
from functools import cached_property, partial
from pathlib import Path


async def to_thread(func, *args, loop=None, executor=None, **kwargs):
    if loop is None:
        loop = asyncio.get_running_loop()
    pfunc = partial(func, *args, **kwargs)
    return await loop.run_in_executor(executor, pfunc)


class AsyncPath(Path):
    """An asynchronous implementation of pathlib.Path."""

    @cached_property
    def _path(self) -> Path:
        return Path(self)

    @classmethod
    async def cwd(cls):
        return AsyncPath(await to_thread(Path.cwd))

    @classmethod
    async def home(cls):
        return AsyncPath(await to_thread(Path.home))

    async def exists(self, *, follow_symlinks=True):
        return await to_thread(self._path.exists, follow_symlinks=follow_symlinks)

    async def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        return await to_thread(self._path.mkdir, mode, parents, exist_ok)
