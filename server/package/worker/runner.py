import asyncio


class RunProcessError(Exception):
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output


async def run(cmd, output, cwd=None, env=None, encoding="utf-8",
              return_stdout=False):
    output.write(f"RUNNER: Run '{' '.join(cmd)}'\n")
    output.flush()

    proc = await asyncio.create_subprocess_exec(
        cmd[0], *cmd[1:],
        cwd=cwd, env=env,
        stdout=asyncio.subprocess.PIPE if return_stdout else output,
        stderr=asyncio.subprocess.STDOUT,
        process_group=0)

    try:
        if return_stdout:
            stdout, _ = await proc.communicate()
            stdout = stdout.decode(encoding)
            output.write(stdout)
            output.flush()
        else:
            await proc.wait()
            stdout = None

        output.write(f"RUNNER: Exit code: {proc.returncode}\n")
        output.flush()
        if proc.returncode:
            raise RunProcessError(proc.returncode, stdout)
        return stdout
    except asyncio.CancelledError:
        output.write(f"RUNNER: Terminating {cmd[0]}\n")
        output.flush()
        try:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except TimeoutError:
                proc.kill()
                output.write(f"RUNNER: Killed {cmd[0]}\n")
                output.flush()
        except ProcessLookupError:
            pass
        raise
    finally:
        await proc.communicate()
