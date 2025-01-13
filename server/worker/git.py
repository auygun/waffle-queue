def add_remote(git_dir, remote, url):
    return [
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "add",
        remote, url
    ]


def set_remote_url(git_dir, remote, url):
    return [
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "set-url",
        remote, url
    ]


def list_remotes(git_dir):
    return [
        "git",
        f"--git-dir={git_dir}",
        "remote",
        "-v"
    ]


def fetch(git_dir, remote, refspec, recurse_submodules=None):
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
    return cmd + options + [remote, refspec]


def init(git_dir):
    return [
        "git",
        f"--git-dir={git_dir}",
        "init"
    ]


def clean(git_dir, work_tree):
    return [
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "clean",
        "-dffqx"
    ]


def checkout(git_dir, work_tree, refspec):
    return [
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={work_tree}",
        "checkout",
        "--force",
        "--detach",
        refspec
    ]


def last_commit_timestamp(git_dir):
    return [
        "git",
        f"--git-dir={git_dir}",
        "log",
        "-n",
        "1",
        "--format=%ct"
    ]
