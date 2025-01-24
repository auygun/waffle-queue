import re

from . import runner


async def init_or_update(git_dir, name, url, logger=None):
    if (git_dir / "config").exists():
        existing_url = None
        remotes = await list_remotes(git_dir, logger=logger)
        for existing_remote in remotes.splitlines():
            remote_name, remote_url, _ = existing_remote.split()
            if remote_name == name:
                existing_url = remote_url
                break

        if existing_url is None:
            await add_remote(git_dir, name, url, logger=logger)
        elif existing_url != url:
            await set_remote_url(git_dir, name, url, logger=logger)
    else:
        await init(git_dir, logger=logger)
        await add_remote(git_dir, name, url, logger=logger)


async def add_remote(git_dir, remote, url, logger=None):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "add",
        remote, url], logger=logger)


async def set_remote_url(git_dir, remote, url, logger=None):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "set-url",
        remote, url], logger=logger)


async def list_remotes(git_dir, logger=None):
    return await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "-v"], output=runner.PIPE, logger=logger)


async def fetch(git_dir, remote, refspec, recurse_submodules="no", logger=None):
    options = []
    if recurse_submodules is not None:
        options.append(f"--recurse-submodules={recurse_submodules}")
    cmd = [
        "git",
        f"--git-dir={git_dir}",
        "fetch",
        "-fnpP"
    ]
    await runner.run(cmd + options + [remote, refspec], logger=logger)


async def init(git_dir, logger=None):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "init"], logger=logger)


async def clean(git_dir, work_tree, logger=None):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "clean",
        "-dffqx"], logger=logger)


async def checkout(git_dir, work_tree, commit_or_branch, logger=None):
    await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "checkout",
        "--force",
        "--detach",
        commit_or_branch], logger=logger)


async def last_commit_timestamp(git_dir, logger=None):
    return await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "log",
        "-n1",
        "--format=%ct"], output=runner.PIPE, logger=logger)


async def init_submodules(git_dir, work_tree, logger=None):
    await unregister_submodules(git_dir, logger=logger)

    output = await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "submodule",
        "init"], cwd=work_tree, output=runner.PIPE, logger=logger)
    submodule_list = re.findall(
        r"'([^']*)'\s*\(([^)]*)\).*?'([^']*)'", output)
    submodules = {}
    for sm in submodule_list:
        submodules[sm[2]] = list(sm[1:2])

    status = await submodule_status(git_dir, work_tree, logger=logger)
    for s in status:
        submodules[s[1]].append(s[0])

    return submodules


async def unregister_submodules(git_dir, logger=None):
    output = await runner.run([
        "git",
        f"--git-dir={git_dir}",
        "config",
        "list",
        "--name-only"], output=runner.PIPE, logger=logger)
    for line in output.splitlines():
        if line.startswith("submodule."):
            await runner.run([
                "git",
                f"--git-dir={git_dir}",
                "config",
                "unset",
                line], logger=logger)


async def submodule_status(git_dir, work_tree, logger=None):
    output = await runner.run([
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "submodule",
        "status",
        "--cached"], cwd=work_tree, output=runner.PIPE, logger=logger)
    submodules = []
    for line in output.splitlines():
        submodules.append(line.split())
        submodules[-1][0] = submodules[-1][0][1:]
    return submodules
