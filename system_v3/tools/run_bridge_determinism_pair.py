#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import hashlib
import re
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def _read_state_counts(run_dir: Path) -> dict:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        return {}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return {
        "survivor_order": len(state.get("survivor_order", [])),
        "specs": len(state.get("specs", [])),
        "terms": len(state.get("terms", [])),
        "graveyard": len(state.get("graveyard", [])),
        "parked": len(state.get("parked", [])),
        "pending_evidence": len(state.get("evidence_pending", {})),
        "sim_run_count": state.get("sim_run_count", 0),
    }


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalized_event_log_hash(run_dir: Path) -> str:
    logs = sorted((run_dir / "logs").glob("events.*.jsonl"))
    run_id = re.escape(run_dir.name)
    root = re.escape(str(run_dir.parents[2]))  # repo root
    buf: list[str] = []
    for path in logs:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            x = re.sub(run_id, "RUN_ID", line)
            x = re.sub(root, "/REPO_ROOT", x)
            buf.append(x)
    return hashlib.sha256("\n".join(buf).encode("utf-8")).hexdigest() if buf else ""


def _manual_review_required(payload: dict) -> bool:
    return bool(payload.get("controller_review_required"))


def _manual_review_details(payload: dict) -> dict:
    if not _manual_review_required(payload):
        return {
            "required": False,
            "decision": None,
            "reason": None,
        }
    return {
        "required": True,
        "decision": payload.get("controller_review_decision"),
        "reason": payload.get("controller_review_reason"),
    }


def _pair_status(
    *,
    rc_a: int,
    rc_b: int,
    same_state_hash: bool,
    same_counts: bool,
    same_event_hash_norm: bool,
    manual_review_required: bool,
) -> str:
    if manual_review_required:
        return "FAIL"
    if rc_a == 0 and rc_b == 0 and same_state_hash and same_counts and same_event_hash_norm:
        return "PASS"
    return "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run paired bridge campaigns and compare determinism.")
    parser.add_argument("--run-id-a", required=True)
    parser.add_argument("--run-id-b", required=True)
    parser.add_argument("--loops", type=int, default=15)
    parser.add_argument("--max-entries", type=int, default=20)
    parser.add_argument("--max-items", type=int, default=600)
    parser.add_argument("--sim-cap", type=int, default=8)
    parser.add_argument("--min-cycles", type=int, default=50)
    parser.add_argument("--adaptive-sim-cap", action="store_true")
    parser.add_argument("--sim-cap-min", type=int, default=8)
    parser.add_argument("--sim-cap-max", type=int, default=200)
    parser.add_argument("--sim-cap-headroom", type=int, default=16)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    bridge = repo_root / "system_v3" / "tools" / "run_real_loop.py"

    def run_one(run_id: str) -> tuple[dict, int]:
        cmd = [
            "python3",
            str(bridge),
            "--run-id",
            run_id,
            "--loops",
            str(args.loops),
            "--max-entries",
            str(args.max_entries),
            "--max-items",
            str(args.max_items),
            "--sim-cap",
            str(args.sim_cap),
            "--min-cycles",
            str(args.min_cycles),
            "--clean-existing-run",
        ]
        if args.adaptive_sim_cap:
            cmd.extend(
                [
                    "--adaptive-sim-cap",
                    "--sim-cap-min",
                    str(args.sim_cap_min),
                    "--sim-cap-max",
                    str(args.sim_cap_max),
                    "--sim-cap-headroom",
                    str(args.sim_cap_headroom),
                ]
            )
        cp = _run(cmd, repo_root)
        payload: dict
        try:
            payload = json.loads(cp.stdout.strip())
        except json.JSONDecodeError:
            payload = {"status": "FAIL", "stdout": cp.stdout, "stderr": cp.stderr}
        return payload, cp.returncode

    out_a, rc_a = run_one(args.run_id_a)
    out_b, rc_b = run_one(args.run_id_b)

    run_dir_a = Path(out_a.get("run_dir", str(repo_root / "system_v3" / "runs" / args.run_id_a)))
    run_dir_b = Path(out_b.get("run_dir", str(repo_root / "system_v3" / "runs" / args.run_id_b)))

    state_hash_a = out_a.get("replay_summary", {}).get("final_state_hash", "")
    state_hash_b = out_b.get("replay_summary", {}).get("final_state_hash", "")
    event_hash_a = out_a.get("replay_summary", {}).get("event_log_hash", "")
    event_hash_b = out_b.get("replay_summary", {}).get("event_log_hash", "")
    event_hash_norm_a = _normalized_event_log_hash(run_dir_a)
    event_hash_norm_b = _normalized_event_log_hash(run_dir_b)
    counts_a = _read_state_counts(run_dir_a)
    counts_b = _read_state_counts(run_dir_b)

    same_state_hash = bool(state_hash_a) and state_hash_a == state_hash_b
    same_counts = counts_a == counts_b and bool(counts_a)
    same_event_hash = bool(event_hash_a) and event_hash_a == event_hash_b
    same_event_hash_norm = bool(event_hash_norm_a) and event_hash_norm_a == event_hash_norm_b
    manual_review_a = _manual_review_details(out_a)
    manual_review_b = _manual_review_details(out_b)
    manual_review_required = manual_review_a["required"] or manual_review_b["required"]
    status = _pair_status(
        rc_a=rc_a,
        rc_b=rc_b,
        same_state_hash=same_state_hash,
        same_counts=same_counts,
        same_event_hash_norm=same_event_hash_norm,
        manual_review_required=manual_review_required,
    )

    report = {
        "schema": "BRIDGE_DETERMINISM_PAIR_REPORT_v1",
        "status": status,
        "run_a": {"run_id": args.run_id_a, "return_code": rc_a, "summary": out_a, "counts": counts_a},
        "run_b": {"run_id": args.run_id_b, "return_code": rc_b, "summary": out_b, "counts": counts_b},
        "compare": {
            "manual_review_required": manual_review_required,
            "manual_review_a": manual_review_a,
            "manual_review_b": manual_review_b,
            "same_final_state_hash": same_state_hash,
            "same_state_counts": same_counts,
            "same_event_log_hash_raw": same_event_hash,
            "same_event_log_hash_normalized": same_event_hash_norm,
            "final_state_hash_a": state_hash_a,
            "final_state_hash_b": state_hash_b,
            "event_log_hash_a": event_hash_a,
            "event_log_hash_b": event_hash_b,
            "event_log_hash_normalized_a": event_hash_norm_a,
            "event_log_hash_normalized_b": event_hash_norm_b,
        },
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }

    report_path = repo_root / "system_v3" / "runs" / f"DETERMINISM_PAIR__{args.run_id_a}__{args.run_id_b}.json"
    _write_json(report_path, report)
    print(json.dumps({"status": status, "report_path": str(report_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
