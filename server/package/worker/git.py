import re

from . import runner


async def init_or_update(git_dir, name, url, output):
    if (git_dir / "config").exists():
        existing_url = None
        remotes = await list_remotes(git_dir, output)
        for existing_remote in remotes.splitlines():
            remote_name, remote_url, _ = existing_remote.split()
            if remote_name == name:
                existing_url = remote_url
                break

        if existing_url is None:
            await add_remote(git_dir, name, url, output)
        elif existing_url != url:
            await set_remote_url(git_dir, name, url, output)
    else:
        await init(git_dir, output)
        await add_remote(git_dir, name, url, output)


async def add_remote(git_dir, remote, url, output):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "add",
        remote, url], output)


async def set_remote_url(git_dir, remote, url, output):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "set-url",
        remote, url], output)


async def list_remotes(git_dir, output):
    return await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "-v"], output, return_stdout=True)


async def fetch(git_dir, remote, refspec, output, recurse_submodules="no"):
    options = []
    if recurse_submodules is not None:
        options.append(f"--recurse-submodules={recurse_submodules}")
    cmd = [
        "git",
        f"--git-dir={git_dir}",
        "fetch",
        "-fnpP"
    ]
    await runner.run(cmd + options + [remote, refspec], output)


async def init(git_dir, output):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "init"], output)


async def clean(git_dir, work_tree, output):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "clean",
        "-dffqx"], output)


async def checkout(git_dir, work_tree, commit_or_branch, output):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "checkout",
        "--force",
        "--detach",
        commit_or_branch], output)


async def last_commit_timestamp(git_dir, output):
    return await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "log",
        "-n1",
        "--format=%ct"], output, return_stdout=True)


async def init_submodules(git_dir, work_tree, output):
    await unregister_submodules(git_dir, output)

    stdout = await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "submodule",
        "init"], output, cwd=work_tree, return_stdout=True)
    submodule_list = re.findall(r"'([^']*)'\s*\(([^)]*)\).*?'([^']*)'", stdout)
    submodules = {}
    for sm in submodule_list:
        submodules[sm[2]] = list(sm[1:2])

    status = await submodule_status(git_dir, work_tree, output)
    for s in status:
        submodules[s[1]].append(s[0])

    return submodules


async def unregister_submodules(git_dir, output):
    stdout = await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "config",
        "list",
        "--name-only"], output, return_stdout=True)
    for line in stdout.splitlines():
        if line.startswith("submodule."):
            await runner.run([
                "git",
                f"--git-dir={git_dir}",
                "config",
                "unset",
                line], output)


async def submodule_status(git_dir, work_tree, output):
    stdout = await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "submodule",
        "status",
        "--cached"], output, cwd=work_tree, return_stdout=True)
    submodules = []
    for line in stdout.splitlines():
        submodules.append(line.split())
        submodules[-1][0] = submodules[-1][0][1:]
    return submodules
