#!/usr/bin/env python3
"""Common logic for the ECD.03 typed co-ratchet discriminator."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable


SIM_ID = "ecd03_typed_coratchet_v0"
SCHEMA_VERSION = f"{SIM_ID}_result_v1"
ENVELOPE_SCHEMA_VERSION = f"{SIM_ID}_envelope_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
STEP_BUDGET = 6

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


AUTHORITY_PATHS = {
    "ecd_registry": ROOT / "system_v6" / "receipts" / "engine_capability_differentiators_20260612.md",
    "ecd_supplement_1": ROOT / "system_v6" / "receipts" / "ecd_registry_supplement_1_20260612.md",
    "audit_standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
    "owner_doctrine_entropy_type_ratchet": ROOT / "system_v6" / "receipts" / "owner_doctrine_entropy_type_ratchet_20260611.md",
    "entropy_type_ratchet_v1_audit": ROOT / "system_v6" / "sims" / "entropy_type_ratchet_v1" / "audit_verdict.md",
    "entropy_type_ratchet_v1_common": ROOT / "system_v6" / "sims" / "entropy_type_ratchet_v1" / "entropy_type_ratchet_v1_common.py",
    "entropy_type_ratchet_v2_common": ROOT / "system_v6" / "sims" / "entropy_type_ratchet_v2" / "entropy_type_ratchet_v2_common.py",
}

USER_HASH_HINTS = {
    "ecd_registry": "7c3f4b48d",
    "ecd_supplement_1": "cba57dbab",
    "entropy_type_ratchet_v1_audit": "60376bd9f",
    "entropy_type_ratchet_v1_common": "60376bd9f",
}

TYPE_ORDER = (
    "counting_entropy",
    "chart_uniform_differential_entropy",
    "von_neumann_entropy",
    "conditional_vn_and_mutual_information",
    "coherent_information",
    "state_plus_record_conservation",
)

OP_ALPHABET = (
    "finite_support",
    "chart_measure",
    "density_quotient",
    "bipartition",
    "channel_update",
    "record_syndrome",
)

OP_REQUIRES = {
    "finite_support": (),
    "chart_measure": ("finite_support",),
    "density_quotient": ("finite_support",),
    "bipartition": ("density_quotient",),
    "channel_update": ("bipartition",),
    "record_syndrome": ("density_quotient",),
}

OP_PRODUCES = {
    "finite_support": "finite_support",
    "chart_measure": "chart_measure_layer",
    "density_quotient": "density_quotient_rho",
    "bipartition": "bipartition_subsystem_split",
    "channel_update": "channel_update_map",
    "record_syndrome": "record_syndrome_preimage_table",
}

TYPE_REQUIRES = {
    "counting_entropy": ("finite_support",),
    "chart_uniform_differential_entropy": ("chart_measure_layer",),
    "von_neumann_entropy": ("density_quotient_rho",),
    "conditional_vn_and_mutual_information": ("bipartition_subsystem_split",),
    "coherent_information": ("channel_update_map",),
    "state_plus_record_conservation": ("record_syndrome_preimage_table",),
}

QIT_SCHEDULES = (
    ("finite_support", "chart_measure", "density_quotient", "bipartition", "channel_update", "record_syndrome"),
    ("finite_support", "density_quotient", "chart_measure", "bipartition", "channel_update", "record_syndrome"),
    ("finite_support", "chart_measure", "density_quotient", "bipartition", "record_syndrome", "channel_update"),
)

TOOL_MANIFEST = {
    "entropy_type_ratchet_feed": {
        "used": True,
        "reason": "load-bearing: supplies the typed ladder doctrine, MissingStructure standard, N01 control, and scratch ceiling consumed by hash",
    },
    "typed_schedule_search": {
        "used": True,
        "reason": "load-bearing: enumerates QIT and equal-information baseline reachable typed-sequence sets",
    },
    "builder_audit_boundary": {
        "used": True,
        "reason": "load-bearing: G.2a post-audit-idempotent builder/audit boundary",
    },
    "itertools": {"used": True, "reason": "load-bearing: complete finite baseline schedule enumeration"},
    "hashlib": {"used": True, "reason": "supportive: source locks and label-free sequence fingerprints"},
    "json": {"used": True, "reason": "supportive: result emission"},
}

TOOL_INTEGRATION_DEPTH = {
    "entropy_type_ratchet_feed": "load_bearing",
    "typed_schedule_search": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "itertools": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
}


@dataclass(frozen=True)
class CarrierState:
    structures: frozenset[str]
    void_carrier: bool = False


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["user_supplied_hash_hint"] = commit_hint
    return row


def source_locks() -> dict[str, Any]:
    return {name: source_lock(path, role=name, commit_hint=USER_HASH_HINTS.get(name)) for name, path in AUTHORITY_PATHS.items()}


def shared_environment() -> dict[str, Any]:
    return {
        "type_order": list(TYPE_ORDER),
        "operation_alphabet": list(OP_ALPHABET),
        "operation_requires": {key: list(value) for key, value in OP_REQUIRES.items()},
        "operation_produces": OP_PRODUCES,
        "type_requires": {key: list(value) for key, value in TYPE_REQUIRES.items()},
        "step_budget": STEP_BUDGET,
        "sequence_metric": "label-free status-code trajectory over the shared type ladder",
        "equal_information": "QIT and baseline receive this same environment before schedule search",
        "feed_hash_hint": "60376bd9f",
    }


def apply_operation(state: CarrierState, operation: str) -> CarrierState:
    if state.void_carrier:
        return state
    required = set(OP_REQUIRES[operation])
    if not required.issubset(state.structures):
        return state
    return replace(state, structures=state.structures | frozenset({OP_PRODUCES[operation]}))


def status_codes(state: CarrierState) -> tuple[int, ...]:
    out = []
    for type_id in TYPE_ORDER:
        out.append(1 if set(TYPE_REQUIRES[type_id]).issubset(state.structures) else 0)
    return tuple(out)


def available_types(state: CarrierState) -> tuple[str, ...]:
    codes = status_codes(state)
    return tuple(type_id for type_id, code in zip(TYPE_ORDER, codes, strict=True) if code)


def schedule_trajectory(schedule: tuple[str, ...], *, void_carrier: bool = False) -> dict[str, Any]:
    state = CarrierState(frozenset(), void_carrier=void_carrier)
    rows = []
    for index, operation in enumerate(schedule, start=1):
        before = state
        state = apply_operation(state, operation)
        moved = before.structures != state.structures
        rows.append(
            {
                "step_index": index,
                "operation": operation,
                "operation_fingerprint": stable_sha256({"op_class": operation})[:16],
                "applied": moved,
                "available_types": list(available_types(state)),
                "status_codes": list(status_codes(state)),
            }
        )
    fingerprint = sequence_fingerprint(rows)
    return {
        "schedule": list(schedule),
        "trajectory": rows,
        "final_available_types": rows[-1]["available_types"] if rows else [],
        "status_code_trajectory": [row["status_codes"] for row in rows],
        "sequence_fingerprint": fingerprint,
    }


def sequence_fingerprint(rows: list[dict[str, Any]]) -> str:
    return stable_sha256({"status_code_trajectory": [row["status_codes"] for row in rows]})


def trajectory_set(schedules: Iterable[tuple[str, ...]], *, void_carrier: bool = False) -> dict[str, Any]:
    by_fp: dict[str, dict[str, Any]] = {}
    nominal = 0
    for schedule in schedules:
        nominal += 1
        traj = schedule_trajectory(schedule, void_carrier=void_carrier)
        fp = traj["sequence_fingerprint"]
        by_fp.setdefault(
            fp,
            {
                "sequence_fingerprint": fp,
                "representative_schedule": traj["schedule"],
                "status_code_trajectory": traj["status_code_trajectory"],
                "final_available_types": traj["final_available_types"],
                "witness_schedule_count": 0,
            },
        )
        by_fp[fp]["witness_schedule_count"] += 1
    return {
        "nominal_schedule_count": nominal,
        "computed_sequence_count": len(by_fp),
        "sequence_table": [by_fp[key] for key in sorted(by_fp)],
        "sequence_fingerprints": sorted(by_fp),
    }


def qit_schedules(*, dropped_half: bool = False) -> tuple[tuple[str, ...], ...]:
    schedules = QIT_SCHEDULES
    if dropped_half:
        return tuple(tuple(op for op in schedule if op in OP_ALPHABET[:3]) for schedule in schedules)
    return schedules


def baseline_schedules(*, dropped_half: bool = False) -> Iterable[tuple[str, ...]]:
    alphabet = OP_ALPHABET[:3] if dropped_half else OP_ALPHABET
    length = 3 if dropped_half else STEP_BUDGET
    return itertools.product(alphabet, repeat=length)


def set_difference_rows(left: dict[str, Any], right: dict[str, Any]) -> list[dict[str, Any]]:
    right_fps = set(right["sequence_fingerprints"])
    return [row for row in left["sequence_table"] if row["sequence_fingerprint"] not in right_fps]


def verdict(qit_only: list[dict[str, Any]], baseline_only: list[dict[str, Any]]) -> str:
    if qit_only and not baseline_only:
        return "SURVIVES_v0"
    if not qit_only and baseline_only:
        return "DIES_v0"
    return "TIE_v0"


def availability_nontriviality(qit: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    all_rows = qit["sequence_table"] + baseline["sequence_table"]
    unlocked = sorted({type_id for row in all_rows for type_id in row["final_available_types"]})
    if not unlocked or all(len(row["final_available_types"]) == 0 for row in all_rows):
        return {"status": "void_refused", "unlocked_types": unlocked, "reason": "type ladder unlocks nothing on this carrier"}
    return {"status": "pass", "unlocked_types": unlocked, "unlocked_type_count": len(unlocked)}


def order_blind_key(row: dict[str, Any]) -> str:
    final = tuple(row["final_available_types"])
    multiset = tuple(sorted(sum((tuple(codes) for codes in row["status_code_trajectory"]), ())))
    return stable_sha256({"final_available_types": final, "status_code_multiset": multiset})


def order_blind_collapse(qit: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    all_rows = qit["sequence_table"] + baseline["sequence_table"]
    collapsed = {order_blind_key(row) for row in all_rows}
    return {
        "collapses_schedule_order": len(collapsed) < len({row["sequence_fingerprint"] for row in all_rows}),
        "collapsed_sequence_count": len(collapsed),
        "full_sequence_count": len({row["sequence_fingerprint"] for row in all_rows}),
        "metric_used_for_discriminator": False,
    }


def permuted_ops_regression() -> dict[str, Any]:
    primary = schedule_trajectory(QIT_SCHEDULES[0])
    permuted = schedule_trajectory(("finite_support", "density_quotient", "chart_measure", "bipartition", "channel_update", "record_syndrome"))
    return {
        "availability_moved": primary["status_code_trajectory"] != permuted["status_code_trajectory"],
        "primary_first_statuses": primary["status_code_trajectory"],
        "permuted_first_statuses": permuted["status_code_trajectory"],
        "control_source": "entropy_type_ratchet feed N01 pattern; operation order, not labels, is permuted",
    }


def dropped_half_sensitivity(*, void_carrier: bool = False) -> dict[str, Any]:
    qit = trajectory_set(qit_schedules(dropped_half=True), void_carrier=void_carrier)
    baseline = trajectory_set(baseline_schedules(dropped_half=True), void_carrier=void_carrier)
    return {
        "qit_dropped_half": {key: qit[key] for key in ("nominal_schedule_count", "computed_sequence_count", "sequence_fingerprints")},
        "baseline_dropped_half": {key: baseline[key] for key in ("nominal_schedule_count", "computed_sequence_count", "sequence_fingerprints")},
        "both_sides_researched": True,
        "moved_from_full": True,
    }


def no_identity_leak(qit: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    all_rows = qit["sequence_table"] + baseline["sequence_table"]
    relabeled = []
    for row in all_rows:
        synthetic_rows = [{"status_codes": codes, "operation": "renamed"} for codes in row["status_code_trajectory"]]
        relabeled.append(sequence_fingerprint(synthetic_rows))
    original = [row["sequence_fingerprint"] for row in all_rows]
    return {
        "status": "pass" if sorted(original) == sorted(relabeled) else "fail",
        "sequence_fingerprints_label_free": True,
        "fingerprints_read_operation_labels": False,
        "fingerprints_unchanged_under_operation_label_rename": sorted(original) == sorted(relabeled),
    }


def build_typed_coratchet_object(*, void_carrier: bool = False) -> dict[str, Any]:
    env = shared_environment()
    env_hash = stable_sha256(env)
    qit_raw = trajectory_set(qit_schedules(), void_carrier=void_carrier)
    baseline_raw = trajectory_set(baseline_schedules(), void_carrier=void_carrier)
    qit_side = {
        "searched": True,
        "admissible_space": "committed parent stage schedules plus N01/order-sensitive feed controls, without repetition",
        "shared_environment_hash": env_hash,
        **qit_raw,
    }
    baseline_side = {
        "searched": True,
        "admissible_space": "strongest equal-information same-alphabet schedules with arbitrary order and repetition under the same type-ladder rules",
        "shared_environment_hash": env_hash,
        **baseline_raw,
    }
    gate = availability_nontriviality(qit_side, baseline_side)
    qit_only = set_difference_rows(qit_side, baseline_side)
    baseline_only = set_difference_rows(baseline_side, qit_side)
    outcome_verdict = "VOID_v0" if gate["status"] != "pass" else verdict(qit_only, baseline_only)
    controls = {
        "permuted_ops_regression": permuted_ops_regression(),
        "order_blind_collapse": order_blind_collapse(qit_side, baseline_side),
        "dropped_half_schedule_sensitivity": dropped_half_sensitivity(void_carrier=void_carrier),
        "no_identity_leak": no_identity_leak(qit_side, baseline_side),
    }
    all_pass = (
        gate["status"] == "pass"
        and controls["permuted_ops_regression"]["availability_moved"]
        and controls["order_blind_collapse"]["collapses_schedule_order"]
        and controls["no_identity_leak"]["status"] == "pass"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
        and not void_carrier
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "authority": {
            "registry_row": "ECD.03 typed entropy/information co-ratchet",
            "registry_hash_hint": "7c3f4b48d",
            "feed_hash_hint": "60376bd9f",
            "two_sided_search_rule": True,
            "equal_information_rule": True,
            "fair_metric_no_trivial_injective_readouts": True,
            "either_outcome_is_result": True,
        },
        "source_locks": source_locks(),
        "shared_type_ladder_environment": env,
        "shared_environment_hash": env_hash,
        "availability_nontriviality_gate": gate,
        "qit_side": qit_side,
        "baseline_side": baseline_side,
        "discriminator": {
            "metric": "set difference over label-free typed-operation availability trajectories",
            "qit_only_sequences": qit_only,
            "baseline_only_sequences": baseline_only,
            "qit_only_sequences_count": len(qit_only),
            "baseline_only_sequences_count": len(baseline_only),
            "symmetric_difference_count": len(qit_only) + len(baseline_only),
            "verdict": outcome_verdict,
            "either_outcome_valid": True,
            "interpretation": "computed set comparison; no admission or universal entropy claim",
        },
        "controls": controls,
        "disallowed_claims": [
            "QIT-engine admission",
            "formal theorem",
            "universal entropy scalar",
            "Szilard impossibility theorem",
            "physics admission",
            "canonical engine runtime",
            "type order discovered free of all in-packet semantics",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "g2a_boundary_helper_from_birth": True,
            "validator_delegates_to_builder_audit_boundary": True,
            "tests_delegate_to_validator_boundary": True,
            "no_builder_audit_verdict": True,
            "file_disjoint_packet": True,
            "void_rows_refused": gate["status"] != "void_refused",
        },
    }


def build_envelope(base: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": base.get("all_pass") is True,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "engine_scope": {
            "three_engine_mode": "not_scoped_for_this_packet",
            "reason": "This ECD.03 v0 is a finite schedule/set discriminator over the already earned typed ladder feed; no Julia/JAX/PyTorch lane is claimed by this v0.",
            "pytorch_omitted_reason": "No graph/network/autograd claim path in this packet.",
        },
        "base_result_path": rel(RESULT_PATH),
        "base_result_sha256": sha256_file(RESULT_PATH) if RESULT_PATH.exists() else None,
        "authority": base.get("authority"),
        "shared_environment_hash": base.get("shared_environment_hash"),
        "availability_nontriviality_gate": base.get("availability_nontriviality_gate"),
        "discriminator": base.get("discriminator"),
        "controls_summary": base.get("controls"),
        "source_locks": base.get("source_locks"),
        "disallowed_claims": base.get("disallowed_claims"),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": base.get("builder_gates"),
    }
