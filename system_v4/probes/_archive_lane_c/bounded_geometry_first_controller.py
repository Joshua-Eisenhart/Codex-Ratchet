#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROBES = REPO / "system_v4" / "probes"
RESULTS = PROBES / "a2_state" / "sim_results"
PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
MPLCONFIGDIR = "/tmp/codex-mpl"
NUMBA_CACHE_DIR = "/tmp/codex-numba"


@dataclass(frozen=True)
class Packet:
    lego_id: str
    sim_file: str | None
    current_state: str
    note: str


ACTIVE_LAYER = "successor-hardening/first-pairwise-coupling"

PACKETS: list[Packet] = [
    Packet(
        "operator_geometry_compatibility",
        "sim_operator_geometry_compatibility.py",
        "supporting_only",
        "First supporting-only successor from carrier/same-carrier geometry into pairwise operator/geometry compatibility; stop if it remains supporting-only after honest schema/truth hardening.",
    ),
    Packet(
        "compound_operator_geometry",
        "sim_compound_operator_geometry.py",
        "supporting_only",
        "Second supporting-only successor from same-carrier geometry into compound operator/geometry coupling; stop if it remains supporting-only after honest schema/truth hardening.",
    ),
]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def emit(msg: str) -> None:
    print(msg, flush=True)


def env() -> dict[str, str]:
    base = os.environ.copy()
    base["MPLCONFIGDIR"] = MPLCONFIGDIR
    base["NUMBA_CACHE_DIR"] = NUMBA_CACHE_DIR
    return base


def worker_prompt(packet: Packet) -> str:
    assert packet.sim_file is not None
    sim_path = f"system_v4/probes/{packet.sim_file}"
    return (
        f"Project root: {REPO}. "
        "Read first: system_v5/new docs/LLM_CONTROLLER_CONTRACT.md, "
        "system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md, "
        "system_v5/new docs/plans/sim_backlog_matrix.md, "
        "system_v5/new docs/plans/sim_truth_audit.md, "
        "system_v5/new docs/plans/corrected-bounded-automation-plan.md, "
        "system_v5/new docs/plans/launch-ready-claude-worker-orchestration-spec.md, "
        "system_v5/new docs/plans/launch-ready-automated-run-manifest.md, "
        f"and {REPO}/Makefile. "
        f"Bounded target lego: {packet.lego_id}. "
        f"Use only the direct packet {sim_path}. "
        "Do not substitute any nearby useful packet. "
        f"If this direct packet is wrong for the target, report blocked and stop. "
        f"Run exactly: {PYTHON} system_v4/probes/cleanup_first_guard.py --context sim ; then {PYTHON} {sim_path} ; then {PYTHON} system_v4/probes/probe_truth_audit.py ; then {PYTHON} system_v4/probes/controller_alignment_audit.py. "
        "Do not widen into Carnot/Szilard, graph deepeners, bridge, axis, or flux. "
        "Report only: docs read; exact commands run; result file path(s); whether the packet achieved exists/runs/passes local rerun/canonical by process; blockers if any."
    )


def packet_command(packet: Packet) -> list[str]:
    return [
        "claude",
        "-p",
        worker_prompt(packet),
        "--model",
        "sonnet",
        "--effort",
        "low",
        "--allowedTools",
        "Read,Bash",
        "--max-turns",
        "18",
    ]


def launch_worker(packet: Packet) -> subprocess.Popen[str]:
    cmd = packet_command(packet)
    emit(f"RUN-WORKER START {now()} lego={packet.lego_id} mode=claude-print")
    emit("RUN-WORKER CMD " + shlex.join(cmd))
    return subprocess.Popen(cmd, cwd=REPO, env=env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def choose_packets(include_canonical: bool = False) -> tuple[list[Packet], list[Packet]]:
    runnable: list[Packet] = []
    blocked: list[Packet] = []
    for packet in PACKETS:
        if packet.sim_file is None:
            blocked.append(packet)
            continue
        if not include_canonical and packet.current_state == "canonical_by_process":
            continue
        runnable.append(packet)
    return runnable, blocked


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded geometry-first Claude worker controller")
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--transport", default="local")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-canonical", action="store_true")
    args = parser.parse_args()

    os.makedirs(MPLCONFIGDIR, exist_ok=True)
    os.makedirs(NUMBA_CACHE_DIR, exist_ok=True)

    runnable, blocked = choose_packets(include_canonical=args.include_canonical)
    deadline = time.time() + max(args.minutes, 1) * 60

    emit(f"RUN-LAUNCH {now()} duration_minutes={args.minutes} transport={args.transport} active_layer={ACTIVE_LAYER}")
    emit(f"RUN-CONCURRENCY {args.concurrency}")
    for packet in blocked:
        emit(f"RUN-BLOCKED {packet.lego_id} reason=no_direct_probe note={packet.note}")
    if args.dry_run:
        for packet in runnable[: args.concurrency]:
            emit(f"RUN-READY {packet.lego_id} state={packet.current_state} sim={packet.sim_file} note={packet.note}")
        if not runnable:
            emit(f"RUN-LAYER-COMPLETE no_runnable_packets_remaining current_layer={ACTIVE_LAYER}")
        emit(f"RUN-DONE {now()} status=dry_run")
        return 0

    active: dict[str, tuple[Packet, subprocess.Popen[str]]] = {}
    queue = list(runnable)
    completed: list[str] = []
    degraded = False

    while time.time() < deadline and (queue or active):
        while queue and len(active) < args.concurrency:
            packet = queue.pop(0)
            proc = launch_worker(packet)
            active[packet.lego_id] = (packet, proc)
        time.sleep(2)
        finished = []
        for lego_id, (packet, proc) in active.items():
            code = proc.poll()
            if code is None:
                continue
            output = proc.stdout.read() if proc.stdout else ""
            emit(f"RUN-WORKER END {now()} lego={lego_id} exit={code}")
            if output:
                emit(output[:8000])
            if code != 0:
                degraded = True
            completed.append(lego_id)
            finished.append(lego_id)
        for lego_id in finished:
            active.pop(lego_id, None)
        emit(f"RUN-HEARTBEAT {now()} health={'degraded' if degraded else 'healthy'} active_workers={list(active.keys())} completed={completed}")
        # bounded current layer only; stop after queue drains, do not widen
        if not queue and not active:
            break

    emit(f"RUN-DONE {now()} status={'degraded' if degraded else 'healthy'} active_layer={ACTIVE_LAYER} completed={completed} blocked={[p.lego_id for p in blocked]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
