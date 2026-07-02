#!/usr/bin/env python3
"""Read-only v4.3 object-drift monitor for the retrocausal shell-field lane."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


classification = "controller_audit"
TOOL_MANIFEST = {
    "python_stdlib": {
        "reason": "Read-only monitor over v4.3 object packet and formal-scout result receipts."
    }
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "supportive",
}

REPO_ROOT = Path(__file__).resolve().parents[3]
FORMAL_SCOUTS = REPO_ROOT / "system_v5" / "ops" / "formal_scouts"
RESULTS = FORMAL_SCOUTS / "results"
DEFAULT_PACKET = FORMAL_SCOUTS / "retrocausal_shell_field_v43_object_packet_20260527.json"
DEFAULT_HEARTBEAT = FORMAL_SCOUTS / "retrocausal_shell_field_v43_monitor_heartbeat_20260527.json"
DEFAULT_RECEIPT = FORMAL_SCOUTS / "retrocausal_shell_field_v43_monitor_launch_receipt_20260527.json"
DEFAULT_SPAWN_RECEIPT = FORMAL_SCOUTS / "retrocausal_shell_field_v43_monitor_spawn_receipt_20260527.json"
DEFAULT_STATUS = FORMAL_SCOUTS / "retrocausal_shell_field_v43_monitor_status_20260527.json"
DEFAULT_LOG = Path("/private/tmp/retrocausal_shell_field_v43_monitor.log")
VALIDATOR = REPO_ROOT / "scripts" / "wizard_v4_3_object_preservation.py"

AUTOMATION_ID = "monitor-v4-3-formal-shell-sim"
PRIMARY_FIELDS = {
    "event_x",
    "shells",
    "shell_radius_r",
    "shell_orientation",
    "future_continuations",
    "branch_states",
    "compatibility_weights",
    "compression_map",
    "present_survivor",
    "outward_record",
}
FIELD_ALIASES = {
    "future_continuations": {"future_continuations", "Omega_r", "omega_r", "future_continuations/Omega_r"},
    "branch_states": {"branch_states", "rho_omega", "branch_states/rho_omega"},
    "present_survivor": {"present_survivor", "rho_present", "present_survivor/rho_present"},
}
BLOCKED_CONSUMER_TERMS = {
    "stacking",
    "flux",
    "xi",
    "phi0",
    "axis0",
    "holodeck",
    "fep",
    "physics",
    "gravity",
    "final manifold",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def validate_packet(packet_path: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("wizard_v4_3_object_preservation", VALIDATOR)
    if spec is None or spec.loader is None:
        return {"ok": False, "errors": [{"code": "validator_import_failed", "message": str(VALIDATOR)}]}
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.validate_packet(read_json(packet_path))


def all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(all_keys(item))
    return keys


def text_blob(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(f"{key} {text_blob(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(text_blob(item) for item in value)
    return str(value)


def field_present(keys: set[str], blob: str, field: str) -> bool:
    aliases = FIELD_ALIASES.get(field, {field})
    lowered = blob.lower()
    return bool(keys.intersection(aliases)) or any(alias.lower() in lowered for alias in aliases)


def result_candidates() -> list[Path]:
    paths: set[Path] = set()
    exact = [
        RESULTS / "retrocausal_shell_field_seed_probe_results.json",
        RESULTS / "m_rpf_cross_row_order_closure_probe_results.json",
    ]
    for path in exact:
        if path.exists():
            paths.add(path)
    if RESULTS.exists():
        paths.update(RESULTS.glob("*retrocausal_shell_field*results.json"))
        paths.update(RESULTS.glob("*m_rpf*results.json"))
    return sorted(paths)


def blocked_consumers_ok(payload: dict[str, Any]) -> bool:
    consumer_text = text_blob(
        payload.get("blocked_consumers")
        or payload.get("blocked_downstream_consumers")
        or payload.get("downstream_blocks")
        or payload.get("primary_object_card", {}).get("blocked_downstream_consumers")
        or ""
    ).lower()
    terms = set(BLOCKED_CONSUMER_TERMS)
    if "m_rpf_stack_0_8" in text_blob(payload).lower():
        terms.discard("stacking")
    return all(term in consumer_text for term in terms)


def inspect_result(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    keys = all_keys(payload)
    blob = text_blob(payload)
    missing = sorted(field for field in PRIMARY_FIELDS if not field_present(keys, blob, field))
    primary_text = text_blob(payload.get("primary_object") or payload.get("object_type") or payload.get("primary_object_card", {}))
    primary_blob = " ".join([primary_text, text_blob(payload.get("finite_map") or ""), text_blob(payload.get("primary_object") or "")]).lower()
    primary_ok = (
        "retrocausal_possibility_field" in primary_blob
        or "retrocausalpossibilityfield" in primary_blob
        or "retrocausal_shell_constraint_manifold" in primary_blob
        or "m_rpf" in primary_blob
    )
    return {
        "blocked_consumers_ok": blocked_consumers_ok(payload),
        "missing_primary_fields": missing,
        "path": str(path.relative_to(REPO_ROOT)),
        "primary_object_ok": primary_ok,
        "preserves_object": primary_ok and not missing and blocked_consumers_ok(payload),
    }


def inspect_packet(packet_path: Path) -> dict[str, Any]:
    payload = read_json(packet_path)
    card = payload.get("primary_object_card", {})
    lateral = payload.get("lateral_mappings", [])
    adapter_probe_locks = [
        {
            "label": mapping.get("label"),
            "primary_object_promotion_allowed": mapping.get("primary_object_promotion_allowed"),
            "promotion_allowed": mapping.get("promotion_allowed"),
            "use_type": mapping.get("use_type"),
        }
        for mapping in lateral
    ]
    return {
        "blocked_consumers_ok": blocked_consumers_ok(card),
        "first_class_fields_ok": PRIMARY_FIELDS.issubset(set(card.get("first_class_fields", []))),
        "lateral_role_locks": adapter_probe_locks,
        "object_type": card.get("object_type"),
        "packet_path": str(packet_path.relative_to(REPO_ROOT)),
    }


def build_heartbeat(packet_path: Path, interval_sec: int, launch_receipt_path: Path) -> dict[str, Any]:
    packet_validation = validate_packet(packet_path)
    packet_inspection = inspect_packet(packet_path)
    result_reports = [inspect_result(path) for path in result_candidates() if path != DEFAULT_PACKET]
    drift_findings = [report for report in result_reports if not report["preserves_object"]]

    if not packet_validation.get("ok"):
        status = "packet_invalid"
    elif drift_findings:
        status = "object_drift_detected"
    elif result_reports:
        status = "active_preserved"
    else:
        status = "active_waiting_for_formal_results"

    now = utc_now()
    return {
        "automation_id": AUTOMATION_ID,
        "blocked_downstream_consumers": sorted(BLOCKED_CONSUMER_TERMS),
        "cadence_sec": interval_sec,
        "checked_at": now,
        "kind": "retrocausal_shell_field_v43_monitor_heartbeat",
        "launch_receipt_path": rel(launch_receipt_path),
        "next_check_after": datetime.fromtimestamp(time.time() + interval_sec, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "packet_inspection": packet_inspection,
        "packet_validation_ok": bool(packet_validation.get("ok")),
        "primary_object_watch_fields": sorted(PRIMARY_FIELDS),
        "process_pid": os.getpid(),
        "result_reports": result_reports,
        "role": "read_only_object_drift_monitor",
        "status": status,
        "wizard_truth": "monitor only; no Wizard v4.2 FULL topology claimed",
    }


def write_launch_receipt(args: argparse.Namespace) -> None:
    payload = {
        "automation_id": AUTOMATION_ID,
        "cadence_sec": args.interval_sec,
        "command": " ".join(args.original_argv),
        "created_at": utc_now(),
        "heartbeat_path": rel(args.heartbeat),
        "kind": "monitor_launch_receipt",
        "no_formal_scout_started": True,
        "object_packet_path": rel(args.packet),
        "process_pid": os.getpid(),
        "role": "read_only monitor for whether the formal run preserves the shell-field object or drifts back into proxies",
        "status": "active" if args.daemon else "one_shot_validation",
        "wizard_truth": "monitor launch only; no Wizard v4.2 FULL topology claimed",
    }
    write_json(args.launch_receipt, payload)


def run_once(args: argparse.Namespace) -> dict[str, Any]:
    heartbeat = build_heartbeat(args.packet, args.interval_sec, args.launch_receipt)
    write_json(args.heartbeat, heartbeat)
    return heartbeat


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except Exception as exc:  # noqa: BLE001
        return {"read_error": str(exc)}


def write_monitor_status(args: argparse.Namespace, spawn_payload: dict[str, Any]) -> None:
    active = spawn_payload.get("status") == "active"
    heartbeat = spawn_payload.get("heartbeat_snapshot", {})
    payload = {
        "automation_id": AUTOMATION_ID,
        "blocked_downstream_consumers": [
            "stacking closure",
            "flux closure",
            "Xi closure",
            "Phi0 closure",
            "Axis0 closure",
            "Holodeck/FEP admission",
            "physics/gravity proof",
            "final manifold admission",
        ],
        "cadence_claim": "every 30 minutes",
        "cadence_sec": args.interval_sec,
        "created_at": "2026-05-27T05:20:00Z",
        "evidence_checked": [
            {
                "check": "spawn_daemon",
                "finding": "active detached daemon verified" if active else "daemon spawn failed",
            },
            {
                "check": "launch_receipt",
                "finding": "active launch receipt process_pid matches spawned pid"
                if spawn_payload.get("launch_receipt_pid_matches")
                else "launch receipt missing or process_pid mismatch",
            },
            {
                "check": "heartbeat",
                "finding": "heartbeat process_pid and cadence match spawned daemon"
                if spawn_payload.get("heartbeat_pid_matches") and heartbeat.get("cadence_sec") == args.interval_sec
                else "heartbeat missing or mismatch",
            },
            {
                "check": "formal_scout_competition",
                "finding": "monitor spawn command starts only the read-only daemon, not a formal scout",
            },
        ],
        "heartbeat_path": rel(args.heartbeat),
        "kind": "monitor_status",
        "log_path": str(args.log_path),
        "monitor_process_pid": spawn_payload.get("process_pid"),
        "next_admissible_step": (
            "Leave the side monitor active while the formal TUI uses the v4.3 goal prompt; "
            "inspect the heartbeat/launch receipts for object drift."
        ),
        "primary_object_watch_fields": [
            "Omega_r future continuations remain first-class",
            "future-inward and past-outward orientation preserved",
            "compatibility weights precede compression",
            "rho_present derived from weighted futures",
            "outward_record emitted from survivor provenance",
            "readouts preserve Omega_r-to-compression provenance",
            "Axis0, flux, FEP/Holodeck, physics, PEPS3D labels, and scalar entropy stay typed as downstream/proxy/adapter surfaces",
        ],
        "spawn_receipt_path": rel(args.spawn_receipt),
        "status": "active_verified_by_spawn_receipt" if active else "spawn_failed",
        "updated_at": utc_now(),
        "wizard_truth": "No Wizard v4.2 FULL topology receipt was run or claimed for this monitor-status audit.",
    }
    write_json(args.status, payload)


def spawn_daemon(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--daemon",
        "--interval-sec",
        str(args.interval_sec),
        "--packet",
        str(args.packet),
        "--heartbeat",
        str(args.heartbeat),
        "--launch-receipt",
        str(args.launch_receipt),
    ]
    args.log_path.parent.mkdir(parents=True, exist_ok=True)
    with args.log_path.open("ab") as log:
        proc = subprocess.Popen(
            cmd,
            cwd=REPO_ROOT,
            stdout=log,
            stderr=log,
            start_new_session=True,
            close_fds=True,
        )

    status = "spawned_unverified"
    launch: dict[str, Any] = {}
    heartbeat: dict[str, Any] = {}
    deadline = time.time() + 5.0
    while time.time() < deadline:
        launch = read_json_if_exists(args.launch_receipt)
        heartbeat = read_json_if_exists(args.heartbeat)
        alive = process_alive(proc.pid)
        launch_pid_matches = launch.get("status") == "active" and launch.get("process_pid") == proc.pid
        heartbeat_pid_matches = heartbeat.get("process_pid") == proc.pid and heartbeat.get("cadence_sec") == args.interval_sec
        if alive and launch_pid_matches and heartbeat_pid_matches:
            status = "active"
            break
        if not alive:
            status = "process_exited_before_verification"
            break
        time.sleep(0.25)
    else:
        status = "verification_timeout"

    payload = {
        "automation_id": AUTOMATION_ID,
        "cadence_sec": args.interval_sec,
        "command": " ".join(cmd),
        "created_at": utc_now(),
        "heartbeat_path": rel(args.heartbeat),
        "heartbeat_pid_matches": heartbeat.get("process_pid") == proc.pid,
        "heartbeat_snapshot": heartbeat,
        "kind": "monitor_spawn_receipt",
        "launch_receipt_path": rel(args.launch_receipt),
        "launch_receipt_pid_matches": launch.get("status") == "active" and launch.get("process_pid") == proc.pid,
        "launch_receipt_snapshot": launch,
        "log_path": str(args.log_path),
        "no_formal_scout_started": True,
        "object_packet_path": rel(args.packet),
        "process_alive": process_alive(proc.pid),
        "process_pid": proc.pid,
        "role": "detached read-only object-drift monitor launcher",
        "status": status,
        "wizard_truth": "spawn receipt only; no Wizard v4.2 FULL topology claimed",
    }
    write_json(args.spawn_receipt, payload)
    write_monitor_status(args, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if status == "active" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--heartbeat", type=Path, default=DEFAULT_HEARTBEAT)
    parser.add_argument("--launch-receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--spawn-receipt", type=Path, default=DEFAULT_SPAWN_RECEIPT)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--interval-sec", type=int, default=1800)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--spawn-daemon", action="store_true")
    args = parser.parse_args()
    args.original_argv = [Path(__file__).name] + sys.argv[1:]

    if args.interval_sec < 60:
        raise SystemExit("--interval-sec must be at least 60")
    if sum(bool(flag) for flag in (args.once, args.daemon, args.spawn_daemon)) != 1:
        raise SystemExit("choose exactly one of --once, --daemon, or --spawn-daemon")

    if args.spawn_daemon:
        return spawn_daemon(args)

    write_launch_receipt(args)
    if args.once:
        print(json.dumps(run_once(args), indent=2, sort_keys=True))
        return 0

    while True:
        run_once(args)
        time.sleep(args.interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
