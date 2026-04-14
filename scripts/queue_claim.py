#!/usr/bin/env python3
"""Two-queue + atomic-claim infrastructure.

Lanes:
    lane_A  — tool-capability queue (nonclassical, gated)
    lane_B  — classical baseline queue

States transition via os.rename (atomic on POSIX same-filesystem):
    queue/lane_X/<hash>.json
      -> queue/claimed/<orig_name>.<pid>.<host>
      -> queue/done/<orig_name>  OR  queue/blocked/<orig_name>

Functions:
    enqueue(lane, sim_path)
    claim(lane, worker_id) -> claimed_path | None
    complete(claim_path, exit_code, artifact_path)
    block(claim_path, reason)
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_ROOT = ROOT / "system_v4" / "probes" / "a2_state" / "queue"

LANES = ("lane_A", "lane_B")


def _ensure_dirs() -> None:
    for sub in ("lane_A", "lane_B", "claimed", "blocked", "done"):
        (QUEUE_ROOT / sub).mkdir(parents=True, exist_ok=True)


def _lane_dir(lane: str) -> Path:
    if lane not in LANES:
        raise ValueError(f"unknown lane: {lane}")
    return QUEUE_ROOT / lane


def enqueue(lane: str, sim_path: str) -> Path:
    _ensure_dirs()
    ld = _lane_dir(lane)
    payload = {
        "sim_path": str(sim_path),
        "lane": lane,
        "enqueued_at": time.time(),
    }
    h = hashlib.sha1(f"{lane}:{sim_path}".encode()).hexdigest()[:16]
    target = ld / f"{h}.json"
    tmp = ld / f".{h}.json.tmp"
    tmp.write_text(json.dumps(payload, sort_keys=True))
    os.rename(tmp, target)  # atomic publish
    return target


def claim(lane: str, worker_id: str) -> Path | None:
    """Atomic claim via os.rename. Returns claimed path or None if queue empty."""
    _ensure_dirs()
    ld = _lane_dir(lane)
    claimed_dir = QUEUE_ROOT / "claimed"
    pid = os.getpid()
    host = socket.gethostname().split(".")[0]
    # Snapshot then race; os.rename on same fs is atomic and fails if src missing
    for item in sorted(ld.glob("*.json")):
        target = claimed_dir / f"{item.name}.{pid}.{host}.{worker_id}"
        try:
            os.rename(item, target)
        except FileNotFoundError:
            continue  # another worker got it
        # append claim metadata
        data = json.loads(target.read_text())
        data["claimed_by"] = worker_id
        data["claimed_pid"] = pid
        data["claimed_host"] = host
        data["claimed_at"] = time.time()
        target.write_text(json.dumps(data, sort_keys=True))
        return target
    return None


def complete(claim_path: str | Path, exit_code: int, artifact_path: str) -> Path:
    claim_path = Path(claim_path)
    data = json.loads(claim_path.read_text())
    data["exit_code"] = exit_code
    data["artifact_path"] = str(artifact_path)
    data["completed_at"] = time.time()
    done = QUEUE_ROOT / "done" / claim_path.name
    claim_path.write_text(json.dumps(data, sort_keys=True))
    os.rename(claim_path, done)
    return done


def block(claim_path: str | Path, reason: str) -> Path:
    claim_path = Path(claim_path)
    data = json.loads(claim_path.read_text())
    data["blocked_reason"] = reason
    data["blocked_at"] = time.time()
    blocked = QUEUE_ROOT / "blocked" / claim_path.name
    claim_path.write_text(json.dumps(data, sort_keys=True))
    os.rename(claim_path, blocked)
    return blocked


def counts() -> dict:
    _ensure_dirs()
    return {
        sub: len(list((QUEUE_ROOT / sub).glob("*.json*")))
        for sub in ("lane_A", "lane_B", "claimed", "blocked", "done")
    }


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "counts"
    if cmd == "counts":
        print(json.dumps(counts(), indent=2))
    elif cmd == "enqueue":
        print(enqueue(sys.argv[2], sys.argv[3]))
    elif cmd == "claim":
        p = claim(sys.argv[2], sys.argv[3])
        print(p if p else "EMPTY")
    else:
        sys.exit(f"unknown cmd: {cmd}")
