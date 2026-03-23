#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path

from a2_state_surfaces import iter_a2_state_surfaces


def _iter_watch_files(a2_state_dir: Path) -> list[Path]:
    return iter_a2_state_surfaces(a2_state_dir)


def _fingerprint(files: list[Path]) -> dict[str, int]:
    fp: dict[str, int] = {}
    for p in files:
        try:
            fp[p.as_posix()] = int(p.stat().st_mtime_ns)
        except FileNotFoundError:
            fp[p.as_posix()] = -1
    return fp


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a2-state-dir", default="system_v3/a2_state")
    ap.add_argument("--interval-sec", type=int, default=60)
    ap.add_argument("--debounce-sec", type=int, default=10)
    ap.add_argument("--write-latest-zip", action="store_true")
    ap.add_argument("--max-memory-bytes", type=int, default=1_000_000)
    ap.add_argument("--retain-shards", type=int, default=64)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args(argv)

    repo_root = Path.cwd().resolve()
    a2_state_dir = (repo_root / args.a2_state_dir).resolve()
    tick_script = (repo_root / "system_v3" / "tools" / "a2_state_persist_tick.py").resolve()

    if not a2_state_dir.is_dir():
        raise SystemExit(f"missing a2_state_dir: {a2_state_dir}")
    if not tick_script.is_file():
        raise SystemExit(f"missing tick script: {tick_script}")

    watch_files = _iter_watch_files(a2_state_dir)
    last_fp = _fingerprint(watch_files)
    last_snapshot_at = 0.0

    def maybe_tick(force: bool) -> None:
        nonlocal last_fp, last_snapshot_at, watch_files

        watch_files = _iter_watch_files(a2_state_dir)
        now_fp = _fingerprint(watch_files)
        changed = now_fp != last_fp
        now = time.time()
        if not force and not changed:
            return
        if not force and (now - last_snapshot_at) < float(args.debounce_sec):
            return

        cmd = [
            "python3",
            str(tick_script),
            "--a2-state-dir",
            str(a2_state_dir),
            "--max-memory-bytes",
            str(int(args.max_memory_bytes)),
            "--retain-shards",
            str(int(args.retain_shards)),
        ]
        if args.write_latest_zip:
            cmd.append("--write-latest-zip")
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        last_fp = now_fp
        last_snapshot_at = now

    maybe_tick(force=True)
    if args.once:
        return 0

    while True:
        time.sleep(max(1, int(args.interval_sec)))
        maybe_tick(force=False)


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
