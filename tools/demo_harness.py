#!/usr/bin/env python3
from __future__ import annotations

import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "sample_configs"
LOG_DIR = ROOT / "logs"


_OPEN_LOG_FILES: list = []


def launch_router(config_name: str) -> subprocess.Popen[str]:
    LOG_DIR.mkdir(exist_ok=True)
    config_path = CONFIG_DIR / config_name
    log_path = LOG_DIR / f"{config_path.stem}.log"
    log_file = log_path.open("w", encoding="utf-8")
    _OPEN_LOG_FILES.append(log_file)

    process = subprocess.Popen(
        ["python3", "-u", str(ROOT / "ripd.py"), str(config_path)],
        cwd=str(ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process


def terminate_router(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def main() -> int:
    routers = {
        "r1": launch_router("r1.conf"),
        "r2": launch_router("r2.conf"),
        "r3": launch_router("r3.conf"),
        "r4": launch_router("r4.conf"),
        "r5": launch_router("r5.conf"),
        "r6": launch_router("r6.conf"),
        "r7": launch_router("r7.conf"),
    }

    try:
        time.sleep(14)  # initial convergence

        terminate_router(routers["r2"])
        time.sleep(18)  # failure detection + reconvergence

        routers["r2"] = launch_router("r2.conf")
        time.sleep(18)  # rejoin + reconvergence

    finally:
        for process in routers.values():
            terminate_router(process)
        for log_file in _OPEN_LOG_FILES:
            try:
                log_file.flush()
                log_file.close()
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
