#!/usr/bin/env python3

from argparse import ArgumentParser
import os
import subprocess

_config = {
    'database': 'waffle_queue',
    'host': '127.0.0.1',
    'port': '3306',
    'user': 'mysql',
    'password': 'mysql',
}


def run(filename):
    cmd = ["mariadb", _config["database"],
           "-h", _config["host"],
           "-P", _config["port"],
           "-u", _config["user"]]
    env = dict(os.environ)
    env["MYSQL_PWD"] = _config["password"]
    with open(filename, encoding="utf-8") as file:
        subprocess.run(cmd, check=True, env=env, stdin=file)


parser = ArgumentParser(
    description="Executes sql statements from a provided file via mariadb client"
)
parser.add_argument("filename", help="name of file to execute")
args = parser.parse_args()

run(args.filename)
