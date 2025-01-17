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
                await self.set_remote(git_dir, name, url)
        else:
            await self.init(git_dir)
            await self.add_remote(git_dir, name, url)

    async def add_remote(self, git_dir, remote, url):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "remote",
            "add",
            remote, url
        ])

    async def set_remote(self, git_dir, remote, url):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "remote",
            "set-url",
            remote, url
        ])

    async def list_remotes(self, git_dir):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "remote",
            "-v"
        ])

    async def fetch(self, git_dir, remote, refspec, recurse_submodules=None):
        options = []
        if recurse_submodules is not None:
            options.append(f"--recurse-submodules={recurse_submodules}")
        cmd = [
            "git",
            f"--git-dir={git_dir}",
            "fetch",
            "-f",
            "-n",
            "-p",
            "-P"
        ]
        return await self._runner.run(cmd + options + [remote, refspec])

    async def init(self, git_dir):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "init"
        ])

    async def clean(self, git_dir, work_tree):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            f"--work-tree={work_tree}",
            "clean",
            "-dffqx"
        ])

    async def checkout(self, git_dir, work_tree, refspec):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            f"--work-tree={work_tree}",
            "checkout",
            "--force",
            "--detach",
            refspec
        ])

    async def last_commit_timestamp(self, git_dir):
        return await self._runner.run([
            "git",
            f"--git-dir={git_dir}",
            "log",
            "-n",
            "1",
            "--format=%ct"
        ])
