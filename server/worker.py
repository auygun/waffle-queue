#!/usr/bin/env python3

from argparse import ArgumentParser
from package.worker import worker

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Worker daemon"
    )
    parser.add_argument("server_id", type=int, help="unique server id")
    args = parser.parse_args()
    worker.run(args.server_id)
