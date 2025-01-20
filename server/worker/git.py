import re


class Git:
    def __init__(self, runner):
        self._runner = runner

    async def init_or_update(self, git_dir, name, url):
        if (git_dir / "config").exists():
            existing_url = None
            remotes = await self.list_remotes(git_dir)
            for existing_remote in remotes.splitlines():
                remote_name, remote_url, _ = existing_remote.split()
                if remote_name == name:
                    existing_url = remote_url
                    break

            if existing_url is None:
                await self.add_remote(git_dir, name, url)
            elif existing_url != url:
                await self.set_remote_url(git_dir, name, url)
        else:
            await self.init(git_dir)
            await self.add_remote(git_dir, name, url)

    async def add_remote(self, git_dir, remote, url):
        await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "remote",
            "add",
            remote, url])

    async def set_remote_url(self, git_dir, remote, url):
        await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "remote",
            "set-url",
            remote, url])

    async def list_remotes(self, git_dir):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "remote",
            "-v"])

    async def fetch(self, git_dir, remote, refspec, recurse_submodules="no"):
        options = []
        if recurse_submodules is not None:
            options.append(f"--recurse-submodules={recurse_submodules}")
        cmd = [
            "git",
            f"--git-dir={git_dir}",
            "fetch",
            "-fnpP"
        ]
        await self._runner.run(cmd + options + [remote, refspec])

    async def init(self, git_dir):
        await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "init"])

    async def clean(self, git_dir, work_tree):
        await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            f"--work-tree={work_tree}",
            "clean",
            "-dffqx"])

    async def checkout(self, git_dir, work_tree, commit_or_branch):
        await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            f"--work-tree={work_tree}",
            "checkout",
            "--force",
            "--detach",
            commit_or_branch])

    async def last_commit_timestamp(self, git_dir):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "log",
            "-n1",
            "--format=%ct"])

    async def init_submodules(self, git_dir, work_tree):
        await self.unregister_submodules(git_dir)

        output = await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            f"--work-tree={work_tree}",
            "submodule",
            "init"], cwd=work_tree)
        submodule_list = re.findall(
            r"'([^']*)'\s*\(([^)]*)\).*?'([^']*)'", output)
        submodules = {}
        for sm in submodule_list:
            submodules[sm[2]] = list(sm[1:2])

        status = await self.submodule_status(git_dir, work_tree)
        for s in status:
            submodules[s[1]].append(s[0])

        return submodules

    async def unregister_submodules(self, git_dir):
        output = await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "config",
            "list",
            "--name-only"])
        for line in output.splitlines():
            if line.startswith("submodule."):
                await self._runner.run([
                    "git",
                    f"--git-dir={git_dir}",
                    "config",
                    "unset",
                    line])

    async def submodule_status(self, git_dir, work_tree):
        output = await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            f"--work-tree={work_tree}",
            "submodule",
            "status",
            "--cached"], cwd=work_tree)
        submodules = []
        for line in output.splitlines():
            submodules.append(line.split())
            submodules[-1][0] = submodules[-1][0][1:]
        return submodules
