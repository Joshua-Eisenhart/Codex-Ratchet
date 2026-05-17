#!/usr/bin/env python3
"""stall_monitor.py — detect and kill stalled multi_model_loop processes.

A "stall" = process has been running > MAX_WALL_SEC with no progress signal in
the output file in the last STALL_WINDOW_SEC. Kills with SIGTERM, logs to
~/.codex-ratchet-stalls.log.

Run periodically (e.g., from a wakeup): `python stall_monitor.py [--kill]`
Without --kill, reports only. With --kill, actually terminates stalled procs.
"""
import argparse
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

MAX_WALL_SEC = 1500       # 25 min — generous; Grok-4.3 + Codex review can take ~20
STALL_WINDOW_SEC = 600    # 10 min — if output file has not been modified, consider stalled
LOG = Path.home() / ".codex-ratchet-stalls.log"


def find_loop_procs():
    """Return [(pid, started_ts, cmd)] for currently running loop processes."""
    out = []
    r = subprocess.run(["ps", "-eo", "pid,lstart,command"], capture_output=True, text=True)
    for line in r.stdout.splitlines()[1:]:
        watched = (
            "multi_model_loop.py",
            "parallel_propose_loop.py",
            "propose_manifold_foundation_repair.py",
            "propose_axes_math_exploration.py",
            "cross_review_loop.py",
            "regen_audit.py",
            "regen_grok_fast",
            "regen_gemini",
            "hostile_search.py",
            "serial_hostile_search.sh",
        )
        if not any(name in line for name in watched):
            continue
        if "grep" in line:
            continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        pid = int(parts[0])
        try:
            ts = time.mktime(time.strptime(" ".join(parts[1:6]).split("  ")[0] if "  " in " ".join(parts[1:6]) else " ".join(parts[1:5]), "%a %b %d %H:%M:%S %Y"))
        except Exception:
            # Fallback: just use 0 (treats as "no timestamp parsed; check anyway")
            ts = 0
        cmd = parts[-1]
        out.append((pid, ts, cmd))
    return out


def find_output_file(pid):
    """Try to find the output file for a background task spawned via Claude harness."""
    # Claude's task output files live under /tmp/claude-*/.../tasks/<id>.output
    base = Path("/private/tmp")
    candidates = []
    try:
        for d in base.glob("claude-*"):
            for sub in d.rglob("tasks/*.output"):
                candidates.append(sub)
    except Exception:
        pass
    if not candidates:
        return None
    # Heuristic: pick the most recent that was opened by this pid (check /proc-equivalent)
    # On macOS, use lsof
    try:
        r = subprocess.run(["lsof", "-p", str(pid)], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            for c in candidates:
                if str(c) in line:
                    return c
    except Exception:
        pass
    return None


def check_one(pid, started_ts, cmd):
    """Return (is_stalled: bool, reason: str, wall_sec: float)."""
    now = time.time()
    wall = now - started_ts if started_ts > 0 else None
    if wall is not None and wall > MAX_WALL_SEC:
        return True, f"wall time {wall:.0f}s > {MAX_WALL_SEC}s", wall
    out = find_output_file(pid)
    if out is not None:
        mtime = out.stat().st_mtime
        idle = now - mtime
        if idle > STALL_WINDOW_SEC and wall is not None and wall > STALL_WINDOW_SEC:
            return True, f"output idle {idle:.0f}s > {STALL_WINDOW_SEC}s (wall {wall:.0f}s)", wall
    return False, "active", wall or 0


def log(msg):
    with open(LOG, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kill", action="store_true", help="actually SIGTERM stalled procs")
    args = ap.parse_args()
    procs = find_loop_procs()
    if not procs:
        print("No loop processes running.")
        return
    print(f"Found {len(procs)} loop process(es):")
    for pid, ts, cmd in procs:
        stalled, reason, wall = check_one(pid, ts, cmd)
        wall_str = f"{wall:.0f}s" if wall else "?"
        status = "STALLED" if stalled else "active"
        short_cmd = cmd[-80:]
        print(f"  pid={pid} wall={wall_str:>6s} [{status}] {reason}")
        print(f"     {short_cmd}")
        if stalled and args.kill:
            try:
                os.kill(pid, signal.SIGTERM)
                log(f"killed pid={pid} reason={reason} cmd_tail={short_cmd}")
                # If SIGTERM doesn't work in 3s, SIGKILL
                time.sleep(3)
                try:
                    os.kill(pid, 0)  # check alive
                    os.kill(pid, signal.SIGKILL)
                    log(f"escalated to SIGKILL on pid={pid}")
                except ProcessLookupError:
                    pass
            except ProcessLookupError:
                pass


if __name__ == "__main__":
    main()
