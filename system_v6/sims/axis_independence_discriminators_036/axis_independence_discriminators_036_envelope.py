#!/usr/bin/env python3
"""Three-engine envelope for axis_independence_discriminators_036 v2."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "axis_independence_discriminators_036"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
AUDIT_VERDICT = SIM_DIR / "audit_verdict.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
AXIS0_STATUS = "readout_only_no_closure"
TOL = 1.0e-6

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independently regenerated leg receipts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hashing and audit-verdict history fingerprinting",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result path binding",
    },
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def passed(record: dict[str, Any] | None) -> bool:
    return isinstance(record, dict) and record.get("pass") is True


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "axis0_status": payload["axis0_status"],
        "pin_block_sha256": payload["pin_block_sha256"],
        "values": payload["shared_scalars"],
        "build_gates": payload["build_gates"],
        "v2_requirement_receipts": payload.get("v2_requirement_receipts", {}),
        "v3_hardening_receipts": payload.get("v3_hardening_receipts", {}),
        "controls": payload.get("controls", {}),
        "source_reuse_lineage": payload["source_reuse_lineage"],
    }


def compare_shared_scalars(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key_sets = {engine: set(payload["shared_scalars"]) for engine, payload in payloads.items()}
    common = sorted(set.intersection(*key_sets.values()))
    union = sorted(set.union(*key_sets.values()))
    rows: list[dict[str, Any]] = []
    max_divergence = 0.0
    max_key = None
    for key in common:
        values = {engine: float(payload["shared_scalars"][key]) for engine, payload in payloads.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_divergence:
            max_divergence = diff
            max_key = key
    return {
        "common_observable_count": len(common),
        "common_observables": common,
        "extra_by_engine": {engine: sorted(keys - set(common)) for engine, keys in key_sets.items()},
        "missing_by_engine": {engine: sorted(set(union) - keys) for engine, keys in key_sets.items()},
        "rows": rows,
        "max_divergence": max_divergence,
        "max_divergence_key": max_key,
        "common_within_tolerance": bool(common) and max_divergence <= TOL,
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def source_lineage_present(payloads: dict[str, dict[str, Any]]) -> bool:
    for payload in payloads.values():
        for packet in payload["source_reuse_lineage"].values():
            if packet.get("exists") is not True or not packet.get("source_sha256"):
                return False
    return True


def all_vary_purity_pass(jax: dict[str, Any]) -> bool:
    receipts = jax["controls"]["vary_operation_purity_receipts"]
    return len(receipts) == 9 and all(row.get("changed_only_requested_polarity") is True for row in receipts.values())


def can_fail_controls_pass(jax: dict[str, Any]) -> bool:
    controls = jax["controls"]
    erasures = controls["erasure_controls"]
    erasures_ok = all(
        row.get("pass") is True and isinstance(row.get("can_fail_evidence"), dict)
        for row in erasures.values()
    )
    commuting = controls["commuting_distinct_pair_control"]
    precedence = controls["erased_precedence_merge"]
    return (
        erasures_ok
        and commuting.get("pass") is True
        and isinstance(commuting.get("can_fail_evidence"), dict)
        and precedence.get("pass") is True
        and isinstance(precedence.get("can_fail_evidence"), dict)
    )


def build_v2_requirement_receipts(
    jax: dict[str, Any], julia: dict[str, Any], pytorch: dict[str, Any]
) -> dict[str, Any]:
    jax_v2 = jax["v2_requirement_receipts"]
    julia_v2 = julia["v2_requirement_receipts"]
    torch_v2 = pytorch["v2_requirement_receipts"]
    return {
        "V1_carrier_coupled_observables": {
            "pass": all(
                passed(payload.get("v2_requirement_receipts", {}).get("V1_carrier_coupled_observables"))
                for payload in (jax, julia, pytorch)
            ),
            "jax": jax_v2["V1_carrier_coupled_observables"],
            "julia": julia_v2["V1_carrier_coupled_observables"],
            "pytorch": torch_v2["V1_carrier_coupled_observables"],
        },
        "V2_recomputed_axis0": {
            "pass": all(
                passed(payload.get("v2_requirement_receipts", {}).get("V2_recomputed_axis0"))
                for payload in (jax, julia, pytorch)
            ),
            "blind_scale_comparison": {
                "jax": jax["blind_scale_comparison"],
                "julia": julia_v2["V2_recomputed_axis0"]["blind_scale_comparison"],
                "pytorch": torch_v2["V2_recomputed_axis0"]["blind_scale_comparison"],
            },
            "source_locked_terrain_paths": {
                "jax": jax["source_refs"]["axis0_committed_terrain_path"],
                "julia": julia["source_refs"]["axis0_committed_terrain_path"],
                "pytorch": pytorch["source_refs"]["axis0_committed_terrain_path"],
            },
            "no_finals_family_templates": True,
        },
        "V3_relabel_and_recompute_shuffle": {
            "pass": passed(jax_v2["V3_relabel_and_recompute_shuffle"]),
            "jax": jax_v2["V3_relabel_and_recompute_shuffle"],
        },
        "V4_can_fail_erasure_controls": {
            "pass": passed(jax_v2["V4_can_fail_erasure_controls"]) and can_fail_controls_pass(jax),
            "jax": jax_v2["V4_can_fail_erasure_controls"],
            "controls": jax["controls"],
        },
        "V5_raw_value_smt": {
            "pass": (
                passed(jax_v2["V5_raw_value_smt"])
                and passed(julia_v2["V5_julia_z3_raw_value_smt"])
                and jax["crossover_proofs"]["z3"]["verdict"] == "unsat"
                and jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
                and jax["crossover_proofs"]["z3"]["erased_control_verdict"] == "sat"
                and jax["crossover_proofs"]["cvc5"]["erased_control_verdict"] == "sat"
                and julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
            ),
            "jax_z3": jax["crossover_proofs"]["z3"],
            "jax_cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
            "scope": "class-level SMT pressure only; raw diagonal dominance is separately audited and not claimed",
        },
        "V8_any_row_raw_dominance_receipt": {
            "pass": passed(jax_v2["V8_any_row_raw_dominance_receipt"]),
            "jax": jax_v2["V8_any_row_raw_dominance_receipt"],
            "claim_status": "raw dominance not claimed; class-level 3x3 result is the claim",
        },
        "V9_honest_o0_o3_scope": {
            "pass": all(
                passed(payload.get("v2_requirement_receipts", {}).get("V8_honest_o0_o3_scope"))
                for payload in (julia, pytorch)
            )
            and "H1_honest_scope_fields" in jax.get("v3_hardening_receipts", {}),
            "jax": jax.get("v3_hardening_receipts", {}).get("H1_honest_scope_fields", {}),
            "julia": julia_v2.get("V8_honest_o0_o3_scope", {}),
            "pytorch": torch_v2.get("V8_honest_o0_o3_scope", {}),
        },
        "V6_honest_pytorch_role": {
            "pass": passed(torch_v2["V6_honest_pytorch_role"]),
            "pytorch": torch_v2["V6_honest_pytorch_role"],
        },
        "V7_real_axis4_cell": {
            "pass": all(
                passed(payload.get("v2_requirement_receipts", {}).get("V7_real_axis4_cell"))
                for payload in (jax, julia, pytorch)
            ),
            "jax": jax_v2["V7_real_axis4_cell"],
            "julia": julia_v2["V7_real_axis4_cell"],
            "pytorch": torch_v2["V7_real_axis4_cell"],
        },
    }


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    julia = payloads["julia"]
    jax = payloads["jax"]
    pytorch = payloads["pytorch"]
    comparison = compare_shared_scalars(payloads)
    pin_strings = {payload["pin_block_canonical_json"] for payload in payloads.values()}
    pin_hashes = {payload["pin_block_sha256"] for payload in payloads.values()}
    v2_receipts = build_v2_requirement_receipts(jax, julia, pytorch)
    v2_all_pass = all(record.get("pass") is True for record in v2_receipts.values())
    controls = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "classification_ceiling_exact": (
            CLASSIFICATION == "scratch_diagnostic"
            and PROMOTION_ALLOWED is False
            and FORMAL_ADMISSION_ALLOWED is False
            and AXIS0_STATUS == "readout_only_no_closure"
        ),
        "pin_blocks_byte_identical": len(pin_strings) == 1 and len(pin_hashes) == 1,
        "reuse_lineages_cited": source_lineage_present(payloads),
        "shared_common_scalars_within_tolerance": comparison["common_within_tolerance"],
        "v2_requirement_receipts_pass": v2_all_pass,
        "controls_fired_with_can_fail_evidence": can_fail_controls_pass(jax),
        "vary_purity_state_diffs_emitted": all_vary_purity_pass(jax),
        "blind_scale_comparison_row_present": passed(jax["blind_scale_comparison"]),
        "relabel_shuffle_both_directions_emitted": passed(jax["controls"]["relabel_and_recompute_shuffle"]),
        "axis4_distinct_from_axis6": passed(jax["axis4_boundary_cell"]) and jax["axis4_boundary_cell"]["axis4_distinct_from_axis6"] is True,
        "z3_cvc5_raw_value_smt": v2_receipts["V5_raw_value_smt"]["pass"] is True,
        "any_row_raw_dominance_reported_not_claimed": (
            v2_receipts["V8_any_row_raw_dominance_receipt"]["pass"] is True
            and v2_receipts["V8_any_row_raw_dominance_receipt"]["jax"]["raw_dominance"]["verdict"] == "sat"
            and v2_receipts["V8_any_row_raw_dominance_receipt"]["jax"]["raw_dominance"]["claim_status"] == "not_claimed"
        ),
        "honest_o0_o3_scope_reported": v2_receipts["V9_honest_o0_o3_scope"]["pass"] is True,
        "pytorch_honest_role": pytorch["pytorch_autograd_sensitivity"]["through_torch_native_recomputation"] is True,
        "audit_verdict_md_preserved_as_history": AUDIT_VERDICT.exists(),
        "no_axis_admission_or_closure": all(
            payload["promotion_fences"]["axis_admission_allowed"] is False
            and payload["promotion_fences"]["axis0_closure_allowed"] is False
            and payload["promotion_fences"]["formal_admission_allowed"] is False
            for payload in payloads.values()
        ),
        "no_IGT_content": all(payload["promotion_fences"]["IGT_content"] is False for payload in payloads.values()),
        "b6_not_cited_as_independence_proof": all(
            payload["promotion_fences"]["b6_scaffold_cited_as_independence_proof"] is False
            for payload in payloads.values()
        ),
    }
    all_pass = all(controls.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "validator"],
        },
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "axis0_status": AXIS0_STATUS,
        "axis0_status_detail": "readout_only_no_closure",
        "axis4_distinct_from_axis6": True,
        "promotion_fences": {
            "axis_admission_allowed": False,
            "axis0_closure_allowed": False,
            "formal_admission_allowed": False,
            "IGT_content": False,
            "b6_scaffold_cited_as_independence_proof": False,
        },
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "all_pass": all_pass,
        "claim_under_test": (
            "Axis 0, Axis 3, and Axis 6 class-level polarity independence under the named pins "
            "as the 3x3 vary/hold matrix class result; raw diagonal dominance is not claimed"
        ),
        "claim_ceiling": "scratch_diagnostic only; promotion_allowed=false; formal_admission_allowed=false; axis0_status=readout_only_no_closure",
        "result_language": "class-level independence under the named pins, medium strength",
        "claim_strength": "medium",
        "raw_dominance_claimed": False,
        "pin_block_canonical_json": next(iter(pin_strings)),
        "pin_block_sha256": next(iter(pin_hashes)),
        "audit_history": {
            "audit_verdict_path": str(AUDIT_VERDICT),
            "audit_verdict_sha256": sha256_file(AUDIT_VERDICT) if AUDIT_VERDICT.exists() else None,
            "action": "preserved_append_only_history_not_modified_by_envelope",
        },
        "source_reuse_lineage": {engine: payload["source_reuse_lineage"] for engine, payload in payloads.items()},
        "source_refs": {
            "jax": jax["source_refs"],
            "julia": julia["source_refs"],
            "pytorch": pytorch["source_refs"],
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "matrix_3x3": jax["matrix_3x3"],
        "axis4_boundary_cell": jax["axis4_boundary_cell"],
        "controls_with_values": jax["controls"],
        "blind_scale_comparison": jax["blind_scale_comparison"],
        "pytorch_autograd_sensitivity": pytorch["pytorch_autograd_sensitivity"],
        "v2_requirement_receipts": v2_receipts,
        "v3_hardening_receipts": {
            "H4a_axis0_erased_H_recompute": jax.get("v3_hardening_receipts", {}).get("H4a_axis0_erased_H_recompute", {}),
            "H1_honest_scope_fields": v2_receipts["V9_honest_o0_o3_scope"],
            "H5_any_row_raw_dominance": v2_receipts["V8_any_row_raw_dominance_receipt"],
            "claim_language": "class-level independence under the named pins, medium strength",
        },
        "build_gates": v2_receipts,
        "crossover_proofs": {
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "control_only_tools": [],
        "divergence_log": [
            "Divergence is computed over common shared scalar readouts; PyTorch's jacobian scalar is engine-specific evidence.",
            "Agreement is a smoke test only; class-level V1-V7 receipts carry the v2 rebuild criteria.",
            "The any-row raw-dominance receipt is SAT and raw diagonal dominance is not claimed.",
        ],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {engine: payload["shared_scalars"] for engine, payload in payloads.items()},
            "comparison": comparison,
            "max_divergence": comparison["max_divergence"],
            "max_divergence_key": comparison["max_divergence_key"],
        },
        "controls": controls,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "engine": "envelope",
                "all_pass": result["all_pass"],
                "result_path": str(RESULT_PATH),
                "v2_all_pass": result["controls"]["v2_requirement_receipts_pass"],
                "max_divergence": result["divergence"]["max_divergence"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
