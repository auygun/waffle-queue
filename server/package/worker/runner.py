import asyncio


PIPE = asyncio.subprocess.PIPE


class RunProcessError(Exception):
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output


# pylint:disable = too-many-branches
# pylint:disable = too-many-arguments
async def run(cmd, logger, cwd=None, env=None, output=None, encoding="utf-8"):
    logger.info(f"Run: '{' '.join(cmd)}'")

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
            with logger.bulk_logger('TRACE') as log:
                for line in stdout.splitlines():
                    log(line)
            if output is None:
                stdout = None
        else:
            await proc.wait()
            stdout = None

        logger.info(f"Exit code: {proc.returncode}")
        if proc.returncode:
            raise RunProcessError(proc.returncode, stdout)
        return stdout
    except asyncio.CancelledError:
        logger.info(f"Terminating {cmd[0]}")
        try:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except TimeoutError:
                proc.kill()
                logger.warning(f"Killed {cmd[0]}")
        except ProcessLookupError:
            pass
        raise
    finally:
        await proc.communicate()
