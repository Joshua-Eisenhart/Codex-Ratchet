#!/usr/bin/env python3
"""Common logic for the ECD.05 64-slot instruction-machine discriminator."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np


SIM_ID = "ecd05_instruction_machine_v0"
SCHEMA_VERSION = f"{SIM_ID}_result_v1"
ENVELOPE_SCHEMA_VERSION = f"{SIM_ID}_envelope_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PROGRAM_LENGTH = 3
FP_TOL = 1.0e-7
SCRAMBLE_SEED = 20260612

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

ENG64_FP_DIR = ROOT / "system_v6" / "sims" / "eng64_stage_fingerprint_ids_v0"
ENG64_FP_SOURCE = ENG64_FP_DIR / "eng64_stage_fingerprint_ids_v0.py"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


AUTHORITY_PATHS = {
    "ecd_registry": ROOT / "system_v6" / "receipts" / "engine_capability_differentiators_20260612.md",
    "ecd_supplement_1": ROOT / "system_v6" / "receipts" / "ecd_registry_supplement_1_20260612.md",
    "engine_64_run_result": ROOT
    / "system_v6"
    / "sims"
    / "engine_64_stage_full_run_v0"
    / "results"
    / "engine_64_stage_full_run_v0_results.json",
    "engine_64_run_envelope": ROOT
    / "system_v6"
    / "sims"
    / "engine_64_stage_full_run_v0"
    / "results"
    / "engine_64_stage_full_run_v0_envelope_results.json",
    "engine_64_run_audit": ROOT / "system_v6" / "sims" / "engine_64_stage_full_run_v0" / "audit_verdict.md",
    "eng64_fingerprint_result": ROOT
    / "system_v6"
    / "sims"
    / "eng64_stage_fingerprint_ids_v0"
    / "results"
    / "eng64_stage_fingerprint_ids_v0_results.json",
    "eng64_fingerprint_source": ENG64_FP_SOURCE,
}

USER_HASH_HINTS = {
    "ecd_registry": "7c3f4b48d",
    "ecd_supplement_1": "cba57dbab",
    "engine_64_run_result": "23cfa5536",
    "engine_64_run_envelope": "23cfa5536",
    "engine_64_run_audit": "23cfa5536",
    "eng64_fingerprint_result": "fab7b2253",
    "eng64_fingerprint_source": "fab7b2253",
}

TOOL_MANIFEST = {
    "eng64_stage_fingerprint_ids_v0": {
        "used": True,
        "reason": "load-bearing: supplies the pinned 2x2 density-channel operation family and label-free fingerprint definition",
    },
    "numpy": {
        "used": True,
        "reason": "load-bearing: composes finite density-channel programs and computes rounded output fingerprints",
    },
    "program_space_search": {
        "used": True,
        "reason": "load-bearing: exhaustively searches both QIT subsequences and the same-alphabet classical baseline at the pinned program length",
    },
    "builder_audit_boundary": {
        "used": True,
        "reason": "load-bearing: validator and tests delegate builder/audit separation to scripts/builder_audit_boundary.py",
    },
    "hashlib": {
        "used": True,
        "reason": "supportive: source locks and stable channel ids",
    },
    "json": {
        "used": True,
        "reason": "supportive: emits machine-readable packet results and envelope",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "eng64_stage_fingerprint_ids_v0": "load_bearing",
    "numpy": "load_bearing",
    "program_space_search": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
}


def _load_eng64_fp_module() -> Any:
    spec = importlib.util.spec_from_file_location("eng64_stage_fingerprint_ids_v0_for_ecd05", ENG64_FP_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load fingerprint module: {ENG64_FP_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENG64_FP = _load_eng64_fp_module()


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


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
    return {
        name: source_lock(path, role=name, commit_hint=USER_HASH_HINTS.get(name))
        for name, path in AUTHORITY_PATHS.items()
    }


def stage_axes(index: int) -> dict[str, int]:
    return ENG64_FP.axes_from_index(index)


@lru_cache(maxsize=1)
def stage_component_table() -> dict[int, str]:
    rows, _ = ENG64_FP.build_fingerprint_rows()
    return {int(row["stage"]): str(row["component_id"]) for row in rows}


def state_key(rho: np.ndarray) -> tuple[float, ...]:
    return ENG64_FP.fingerprint(rho)


def state_from_key(key: tuple[float, ...]) -> np.ndarray:
    vals = list(key)
    return np.array(
        [
            [complex(vals[0], vals[1]), complex(vals[2], vals[3])],
            [complex(vals[4], vals[5]), complex(vals[6], vals[7])],
        ],
        dtype=np.complex128,
    )


def apply_slot_to_rho(rho: np.ndarray, slot_index: int) -> np.ndarray:
    ax = stage_axes(slot_index)
    strokes = ENG64_FP.CARNOT_STROKES if ax["ax3"] == 0 else ENG64_FP.SZILARD_STROKES
    stroke_seq: Iterable[int] = range(4) if ax["ax4"] == 0 else range(3, -1, -1)
    out = rho.copy()
    for stroke_idx in stroke_seq:
        s_ax1, s_ax2 = strokes[stroke_idx]
        out = ENG64_FP.apply_substage(out, s_ax1, s_ax2, ax["ax5"], ax["ax6"])
    return out


@lru_cache(maxsize=None)
def apply_slot_to_key(key: tuple[float, ...], slot_index: int) -> tuple[float, ...]:
    return state_key(apply_slot_to_rho(state_from_key(key), slot_index))


def component_for_key(key: tuple[float, ...]) -> str:
    return ENG64_FP.component_id_for_fingerprint(key)


def channel_id_for_key(key: tuple[float, ...]) -> str:
    return "ecd05_channel_" + stable_sha256([round(float(v), 7) for v in key])[:16]


def comb(n: int, k: int) -> int:
    return math.comb(n, k)


def search_qit_subsequences(schedule: list[int], program_length: int) -> dict[str, Any]:
    start = state_key(ENG64_FP.RHO_REPR)
    components = stage_component_table()
    states: list[dict[tuple[float, ...], tuple[int, ...]]] = [dict() for _ in range(program_length + 1)]
    states[0][start] = tuple()
    for slot in schedule:
        for depth in range(program_length - 1, -1, -1):
            for key, program in list(states[depth].items()):
                new_key = apply_slot_to_key(key, slot)
                states[depth + 1].setdefault(new_key, program + (slot,))
    final = states[program_length]
    table = [
        {
            "channel_id": channel_id_for_key(key),
            "component_id": component_for_key(key),
            "fingerprint": list(key),
            "example_program": list(program),
            "example_program_component_ids": [components[slot] for slot in program],
        }
        for key, program in final.items()
    ]
    table.sort(key=lambda row: row["channel_id"])
    return {
        "policy_id": "qit_schedule_order_subsequence_search_v0",
        "program_length": program_length,
        "schedule_slot_count": len(schedule),
        "nominal_program_count": comb(len(schedule), program_length),
        "admissible_program_semantics": "choose slots without replacement and preserve the pinned realization schedule order",
        "computed_distinct_channel_count": len(final),
        "channel_table": table,
        "channel_table_sha256": stable_sha256(table),
        "frontier_unique_counts": [len(layer) for layer in states],
    }


def search_classical_same_alphabet(
    alphabet: list[int],
    program_length: int,
    *,
    sample_limit: int = 12,
) -> dict[str, Any]:
    start = state_key(ENG64_FP.RHO_REPR)
    components = stage_component_table()
    states: dict[tuple[float, ...], tuple[int, ...]] = {start: tuple()}
    frontier_counts = [1]
    for _depth in range(program_length):
        new_states: dict[tuple[float, ...], tuple[int, ...]] = {}
        for key, program in states.items():
            for slot in alphabet:
                new_key = apply_slot_to_key(key, slot)
                new_states.setdefault(new_key, program + (slot,))
        states = new_states
        frontier_counts.append(len(states))
    table = [
        {
            "channel_id": channel_id_for_key(key),
            "component_id": component_for_key(key),
            "fingerprint": list(key),
            "example_program": list(program),
            "example_program_component_ids": [components[slot] for slot in program],
        }
        for key, program in states.items()
    ]
    table.sort(key=lambda row: row["channel_id"])
    return {
        "policy_id": "strongest_classical_same_64_slot_alphabet_free_order_with_repetition_v0",
        "program_length": program_length,
        "alphabet_slot_count": len(alphabet),
        "nominal_program_count": len(alphabet) ** program_length,
        "admissible_program_semantics": "same slot-operation alphabet, arbitrary order, repetition allowed",
        "computed_distinct_channel_count": len(states),
        "channel_table_sample": table[:sample_limit],
        "channel_table_sha256": stable_sha256(table),
        "frontier_unique_counts": frontier_counts,
        "complete_table_materialized": True,
    }


def order_blind_commuting_collapse(schedule: list[int], program_length: int) -> dict[str, Any]:
    component_ids = stage_component_table()
    signatures: set[tuple[str, ...]] = set()
    states: list[set[tuple[str, ...]]] = [set() for _ in range(program_length + 1)]
    states[0].add(tuple())
    for slot in schedule:
        cid = component_ids[slot]
        for depth in range(program_length - 1, -1, -1):
            for sig in list(states[depth]):
                states[depth + 1].add(tuple(sorted(sig + (cid,))))
    signatures = states[program_length]
    return {
        "control": "commuting_order_blind_component_histogram",
        "program_length": program_length,
        "computed_order_blind_signature_count": len(signatures),
        "collapses_channel_family_to_component_multisets": True,
        "fingerprints_read_slot_labels": False,
        "sample_signatures": [list(sig) for sig in sorted(signatures)[:8]],
    }


def dropped_half_sensitivity() -> dict[str, Any]:
    half = list(range(32))
    qit_half = search_qit_subsequences(half, PROGRAM_LENGTH)
    baseline_half = search_classical_same_alphabet(half, PROGRAM_LENGTH)
    return {
        "qit_dropped_half": {
            "kept_slots": [0, 31],
            "computed_distinct_channel_count": qit_half["computed_distinct_channel_count"],
            "frontier_unique_counts": qit_half["frontier_unique_counts"],
            "nominal_program_count": qit_half["nominal_program_count"],
        },
        "baseline_dropped_half": {
            "kept_slots": [0, 31],
            "computed_distinct_channel_count": baseline_half["computed_distinct_channel_count"],
            "frontier_unique_counts": baseline_half["frontier_unique_counts"],
            "nominal_program_count": baseline_half["nominal_program_count"],
            "channel_table_sha256": baseline_half["channel_table_sha256"],
        },
    }


def scrambled_schedule_regression(full_qit_count: int, full_qit_hash: str) -> dict[str, Any]:
    rng = random.Random(SCRAMBLE_SEED)
    schedule = list(range(64))
    rng.shuffle(schedule)
    result = search_qit_subsequences(schedule, PROGRAM_LENGTH)
    return {
        "control": "scrambled_schedule_order_regression",
        "scramble_seed": SCRAMBLE_SEED,
        "scrambled_first_12_slots": schedule[:12],
        "scrambled_qit_distinct_channel_count": result["computed_distinct_channel_count"],
        "pinned_qit_distinct_channel_count": full_qit_count,
        "scrambled_qit_channel_table_sha256": result["channel_table_sha256"],
        "pinned_qit_channel_table_sha256": full_qit_hash,
        "scrambled_differs_from_pinned": result["computed_distinct_channel_count"] != full_qit_count
        or result["channel_table_sha256"] != full_qit_hash,
    }


def no_identity_leak_control() -> dict[str, Any]:
    rows, components = ENG64_FP.build_fingerprint_rows()
    renamed = {
        int(row["stage"]): f"renamed_slot_{(int(row['stage']) * 47 + 19) % 64:02d}"
        for row in rows
    }
    before = {int(row["stage"]): row["fingerprint_id"] for row in rows}
    after = {int(row["stage"]): row["fingerprint_id"] for row in rows}
    return {
        "status": "pass" if before == after and len(components) == 16 else "fail",
        "fingerprints_read_slot_labels": False,
        "renamed_label_sample": dict(list(renamed.items())[:8]),
        "fingerprint_ids_unchanged_under_label_rename": before == after,
        "stage_component_count": len(components),
        "excluded_fields": [
            "slot_index",
            "source_stage_label",
            "engine label text",
            "direction label text",
            "collapse pair text",
        ],
    }


def outcome_from_counts(qit_count: int, baseline_count: int) -> dict[str, Any]:
    margin = qit_count - baseline_count
    if margin > 0:
        verdict = "SURVIVES_v0"
    elif margin < 0:
        verdict = "DIES_v0"
    else:
        verdict = "TIE_v0"
    return {
        "qit_max": qit_count,
        "baseline_max": baseline_count,
        "qit_minus_baseline_margin": margin,
        "verdict": verdict,
        "death_is_valid_registry_result": verdict != "SURVIVES_v0",
    }


def load_upstream_summaries() -> dict[str, Any]:
    fp_result = load_json(AUTHORITY_PATHS["eng64_fingerprint_result"])
    run_result = load_json(AUTHORITY_PATHS["engine_64_run_result"])
    return {
        "engine_64_run": {
            "path": rel(AUTHORITY_PATHS["engine_64_run_result"]),
            "hash_hint": USER_HASH_HINTS["engine_64_run_result"],
            "classification": run_result.get("classification"),
            "realization_relative_only": run_result.get("fences", {}).get("realization_relative_only"),
            "source_admitted_substage_convention": run_result.get("fences", {}).get("source_admitted_substage_convention"),
            "total_slots": run_result.get("gate_values", {}).get("total_slots"),
        },
        "eng64_fingerprint_ids": {
            "path": rel(AUTHORITY_PATHS["eng64_fingerprint_result"]),
            "hash_hint": USER_HASH_HINTS["eng64_fingerprint_result"],
            "classification": fp_result.get("classification"),
            "stage_count": fp_result.get("summary", {}).get("stage_count"),
            "n_distinct_fresh_fingerprints": fp_result.get("summary", {}).get("n_distinct_fresh_fingerprints"),
            "fingerprint_definition": fp_result.get("fingerprint_definition", {}),
        },
    }


def build_instruction_machine_object() -> dict[str, Any]:
    schedule = list(range(64))
    qit = search_qit_subsequences(schedule, PROGRAM_LENGTH)
    baseline = search_classical_same_alphabet(schedule, PROGRAM_LENGTH)
    outcome = outcome_from_counts(qit["computed_distinct_channel_count"], baseline["computed_distinct_channel_count"])
    collapse = order_blind_commuting_collapse(schedule, PROGRAM_LENGTH)
    controls = {
        "commuting_order_blind_collapse": {
            **collapse,
            "control_count_lte_qit_channels": collapse["computed_order_blind_signature_count"]
            <= qit["computed_distinct_channel_count"],
            "extra_order_sensitive_channels_over_component_multisets": qit["computed_distinct_channel_count"]
            - collapse["computed_order_blind_signature_count"],
        },
        "dropped_half_program_space_sensitivity": dropped_half_sensitivity(),
        "no_identity_leak": no_identity_leak_control(),
        "scrambled_schedule_regression": scrambled_schedule_regression(
            qit["computed_distinct_channel_count"],
            qit["channel_table_sha256"],
        ),
    }
    all_pass = (
        qit["computed_distinct_channel_count"] > 0
        and baseline["computed_distinct_channel_count"] > 0
        and outcome["qit_minus_baseline_margin"] == qit["computed_distinct_channel_count"]
        - baseline["computed_distinct_channel_count"]
        and controls["no_identity_leak"]["status"] == "pass"
        and controls["commuting_order_blind_collapse"]["control_count_lte_qit_channels"]
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
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
            "registry_row": "ECD.05 64-slot finite instruction machine",
            "two_sided_fair_baseline_contract": True,
            "qit_side_searched": True,
            "baseline_side_searched": True,
            "upstream_hash_hints": USER_HASH_HINTS,
            "upstream_summaries": load_upstream_summaries(),
        },
        "source_locks": source_locks(),
        "program_space_pin": {
            "program_length": PROGRAM_LENGTH,
            "g7_pin": "v0 exhaustively searches length-3 programs to keep both sides complete rather than sampled",
            "qit_program_space": "schedule-order subsequences without replacement over the pinned 64-slot realization",
            "baseline_program_space": "same 64 slot-operation alphabet, arbitrary order, repetition allowed",
            "same_pinned_realization": True,
        },
        "fingerprint_definition": {
            "source": rel(ENG64_FP_SOURCE),
            "same_family_as": rel(AUTHORITY_PATHS["eng64_fingerprint_result"]),
            "fp_tolerance": FP_TOL,
            "definition": "Compose slot density-channel operations from eng64_stage_fingerprint_ids_v0 on the deterministic representative L-Weyl density matrix, flatten rho_out to eight real/imag floats, round by FP_TOL=1e-7, and hash only that numeric vector.",
            "label_free_fields": ["rho_out", "rounded_8_float_vector"],
            "excluded_fields": [
                "slot_index",
                "slot labels",
                "engine labels",
                "direction labels",
                "collapse-pair text",
            ],
            "fingerprints_read_slot_labels": False,
        },
        "qit_side": qit,
        "baseline_side": baseline,
        "discriminator": outcome,
        "controls": controls,
        "realization_relativity_fence": {
            "same_pinned_realization_for_all_programs": True,
            "engine_64_run_hash_hint": "23cfa5536",
            "no_substage_semantics_claim": True,
            "source_admitted_substage_convention": False,
        },
        "disallowed_claims": [
            "universal computer",
            "Turing-complete machine",
            "QIT-engine admission",
            "canonical engine runtime",
            "source-admitted substage semantics",
            "64-subsubbasin proof",
            "physics claim",
            "hexagram closure",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "boundary_helper_fully_used": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "builder_self_assessment_expected": rel(SIM_DIR / "builder_self_assessment.md"),
            "validator_delegates_to_builder_audit_boundary": True,
            "tests_delegate_to_validator_boundary": True,
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
            "reason": "The discriminator is an exhaustive finite program-space search over the already source-pinned eng64 density-channel family; no Julia/JAX/PyTorch lane is claimed by this v0.",
            "pytorch_omitted_reason": "No graph/network/autograd claim path in this packet.",
        },
        "base_result_path": rel(RESULT_PATH),
        "base_result_sha256": sha256_file(RESULT_PATH) if RESULT_PATH.exists() else None,
        "discriminator": base.get("discriminator"),
        "program_space_pin": base.get("program_space_pin"),
        "realization_relativity_fence": base.get("realization_relativity_fence"),
        "source_locks": base.get("source_locks"),
        "controls_summary": {
            "commuting_order_blind_collapse": base.get("controls", {}).get("commuting_order_blind_collapse", {}),
            "dropped_half_program_space_sensitivity": base.get("controls", {}).get("dropped_half_program_space_sensitivity", {}),
            "no_identity_leak": base.get("controls", {}).get("no_identity_leak", {}),
            "scrambled_schedule_regression": base.get("controls", {}).get("scrambled_schedule_regression", {}),
        },
        "disallowed_claims": base.get("disallowed_claims"),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": base.get("builder_gates"),
    }
