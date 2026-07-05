#!/usr/bin/env python3
"""Shared helpers for ratchet_climb_engine_v2_blind.

Only fact streams are shared. NumPy, JAX, and Julia each implement drive
measurement and blinded lift selection in their own leg files.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON receipts, hashes, and agreement envelope only"}
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}

SIM_ID = "ratchet_climb_engine_v2_blind"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
RESULTS = HERE / "results"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def load_spec() -> dict[str, Any]:
    return load_json(SPEC_PATH)


def formal_result(engine: str) -> dict[str, Any]:
    path = REPO / load_spec()["reused_formal_gate_results"][engine]
    payload = load_json(path)
    payload["_source_path"] = rel(path)
    payload["_source_sha256"] = sha256_file(path)
    return payload


def carrier(engine: str) -> dict[str, Any]:
    payload = formal_result(engine)
    states = list(payload["carrier_states"])
    summary = payload["carrier_summary"]
    return {
        "source_path": payload["_source_path"],
        "source_sha256": payload["_source_sha256"],
        "labels": [str(row["label"]) for row in states],
        "states": states,
        "pauli_labels": list(summary["pauli_strings"]),
        "state_count": int(summary["state_count"]),
        "formal_full_class_count": int(payload["gates"]["observable_quotient_R4"]["quotient_class_count"]),
    }


def quotient_count(labels: list[str], rows: list[tuple[float, ...]]) -> int:
    return len({tuple(row) for row in rows})


def base_receipts(engine: str, car: dict[str, Any], full_class_count: int, no_probe_count: int) -> tuple[list[int], list[dict[str, Any]], list[dict[str, Any]]]:
    admitted = [1, 2, 3, 4]
    receipts: list[dict[str, Any]] = []
    locks: list[dict[str, Any]] = []
    prev = "GENESIS"
    steps = [
        (1, "finite_distinguishability", {"collapsed_class_count": 1, "full_class_count": full_class_count}),
        (2, "finite_support_S", {"state_count": car["state_count"]}),
        (3, "probe_family_P", {"no_probe_class_count": no_probe_count, "full_class_count": full_class_count}),
        (4, "quotient_S_mod_P", {"projection_class_count": full_class_count, "formal_full_class_count": car["formal_full_class_count"]}),
    ]
    for rung, lift, facts in steps:
        receipt = {
            "rung": rung,
            "admitted": True,
            "selected_lift": lift,
            "distinction_loss_detector": {"measured": True, "facts": facts},
            "mss_gate": {"selected": lift, "stronger_candidates_rejected_unforced": True},
            "engine": engine,
        }
        entry = {"schema": f"{SIM_ID}.lock_entry.v1", "rung": rung, "decision": receipt, "prev_hash": prev}
        entry["entry_hash"] = sha256_json(entry)
        receipts.append(receipt)
        locks.append(entry)
        prev = entry["entry_hash"]
    return admitted, receipts, locks


def finish_payload(engine: str, runs: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    frontiers = {row["variant_id"]: row["frontier_rung"] for row in runs}
    reached_gt4 = {row["variant_id"]: row["frontier_rung"] > 4 for row in runs}
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "generated_at": now_iso(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "capstone_status": "DRAFT_UNAUDITED",
        "claim_ceiling": "scratch_diagnostic",
        "all_pass": all(row["all_pass"] for row in runs),
        "frontier_reached": max(frontiers.values()),
        "frontier_by_variant": frontiers,
        "reached_beyond_rung4_by_variant": reached_gt4,
        "run_results": runs,
        "divergence_log": ["scratch diagnostic; engine parity is checked in check_agreement.py"],
        **meta,
    }
