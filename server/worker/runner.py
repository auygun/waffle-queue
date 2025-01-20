import asyncio


PIPE = asyncio.subprocess.PIPE


class RunProcessError(Exception):
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output


async def run(cmd, cwd=None, env=None, output=None, encoding="utf-8",
              logger=None):
    if logger is not None:
        logger.log('INFO', f"Run: '{' '.join(cmd)}'")

    if output is None:
        if logger is None:
            stdout = asyncio.subprocess.DEVNULL
            stderr = asyncio.subprocess.DEVNULL
        else:
            stdout = asyncio.subprocess.PIPE
            stderr = asyncio.subprocess.STDOUT
    else:
        stdout = output
        stderr = asyncio.subprocess.STDOUT

    proc = await asyncio.create_subprocess_exec(
        cmd[0], *cmd[1:],
        cwd=cwd, env=env,
        stdout=stdout,
        stderr=stderr,
        process_group=0)

    try:
        if stdout == asyncio.subprocess.PIPE:
            stdout, _ = await proc.communicate()
            if encoding is not None:
                stdout = stdout.decode(encoding)
            if logger is not None:
                for line in stdout.splitlines():
                    logger.log('TRACE', line)
                if output is None:
                    stdout = None
        else:
            await proc.wait()
            stdout = None

        if logger is not None:
            logger.log('INFO', f"Exit code: {proc.returncode}")
        if proc.returncode:
            raise RunProcessError(proc.returncode, stdout)
        return stdout
    except asyncio.CancelledError:
        if logger is not None:
            logger.log('INFO', f"Terminating {cmd[0]}")
        try:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except TimeoutError:
                proc.kill()
                if logger is not None:
                    logger.log('WARNING', f"Killed {cmd[0]}")
        except ProcessLookupError:
            pass
        raise
    finally:
        await proc.communicate()
