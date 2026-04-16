#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from riplib.config import ConfigError, load_config
from riplib.router import RipRouter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RIP daemon for COSC364 assignment")
    parser.add_argument("config", help="Path to router config file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
    except (OSError, ConfigError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    router = RipRouter(config)
    try:
        router.run()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
