import asyncio
import db_async as db


class RunProcessError(Exception):
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output


class Runner:
    def __init__(self, logger=None):
        self._logger = logger

    async def run(self, cmd, cwd=None, env=None, output=None, decode="latin-1"):
        await self._log('INFO', f"Run: '{' '.join(cmd)}'")

        stdout = asyncio.subprocess.PIPE if output is None else output
        proc = await asyncio.create_subprocess_exec(
            cmd[0],
            *cmd[1:],
            cwd=cwd,
            env=env,
            stdout=stdout,
            stderr=asyncio.subprocess.STDOUT,
            process_group=0
        )

        try:
            if stdout == asyncio.subprocess.PIPE:
                output, _ = await proc.communicate()
                for line in output.splitlines():
                    await self._log('TRACE', line)
                if decode is not None:
                    output = output.decode("latin-1")
            else:
                await proc.wait()
                output = None

            await self._log('INFO', f"Exit code: {proc.returncode}")
            if proc.returncode:
                raise RunProcessError(proc.returncode, output)
            return output
        except asyncio.CancelledError:
            async with db.acquire():
                await self._log('INFO', f"Terminating {cmd[0]}")
                try:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=10)
                    except TimeoutError:
                        proc.kill()
                        await self._log('WARNING', f"Killed {cmd[0]}")
                except ProcessLookupError:
                    pass
            raise
        finally:
            await proc.communicate()

    async def _log(self, severity, message):
        if self._logger is not None:
            await self._logger.log(severity, message)
