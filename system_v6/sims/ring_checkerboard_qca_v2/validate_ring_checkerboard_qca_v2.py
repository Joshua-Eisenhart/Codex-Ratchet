#!/usr/bin/env python3
"""Packet-local validator for ring_checkerboard_qca_v2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ring_checkerboard_qca_v2_common import (
    PACKET,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    rel,
    sha256_file,
    write_json,
)


RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
REQUIRED_PACKET_FILES = [
    "build_card.md",
    "ring_checkerboard_qca_v2_common.py",
    "ring_checkerboard_qca_v2_julia.jl",
    "ring_checkerboard_qca_v2_jax.py",
    "ring_checkerboard_qca_v2_pytorch.py",
    "ring_checkerboard_qca_v2_envelope.py",
    "validate_ring_checkerboard_qca_v2.py",
    "tests/test_ring_checkerboard_qca_v2.py",
]

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_packet_files(errors: list[str], phase: str) -> None:
    require(errors, phase in {"builder", "post_audit"}, "phase must be builder or post_audit")
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (PACKET / rel_path).is_file(), f"missing required packet file: {rel_path}")
    build_card = PACKET / "build_card.md"
    require(
        errors,
        build_card.is_file() and SIM_ID in build_card.read_text(encoding="utf-8"),
        "build_card.md must contain the copied build card",
    )


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} load-bearing packages missing")
    require(errors, bool(payload.get("package_observables")), f"{name} package_observables missing")
    require(errors, payload.get("one_to_one_tool_calls", {}).get("pass") is True, f"{name} one-to-one tool calls failed")
    source = ROOT / str(payload.get("source_path", ""))
    require(errors, source.is_file(), f"{name} source path missing")
    if source.is_file():
        require(errors, payload.get("source_sha256") == sha256_file(source), f"{name} source sha drift")
    values = payload.get("engine_values", {})
    expected = {
        "right_shift_index": 1,
        "left_shift_index": -1,
        "zero_index": 0,
        "paired_index": 0,
        "L_engine_index": -1,
        "R_engine_index": 1,
        "gauge_engine_R_index": 1,
        "ring_right_shift_index": 0,
        "classical_alt_transient_scc": 352,
        "classical_paired_transient_scc": 128,
    }
    for key, value in expected.items():
        require(errors, values.get(key) == value, f"{name} engine value drift: {key}")


def row_by_id(index_table: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("rule_id")): row for row in index_table}


def validate_index_rows(errors: list[str], env: dict[str, Any]) -> None:
    rows = row_by_id(env.get("index_table", []))
    expected = {
        "calibration_right_shift": (4, 1, 1, "2/1"),
        "calibration_left_shift": (1, 4, -1, "1/2"),
        "calibration_nonshifting_onsite": (1, 1, 0, "1/1"),
        "paired_block_index0": (4, 4, 0, "1/1"),
        "engine_L_flux_IN_left_O1": (1, 4, -1, "1/2"),
        "engine_R_flux_OUT_right_O1": (4, 1, 1, "2/1"),
        "engine_L_index0_control": (1, 1, 0, "1/1"),
        "engine_R_index0_control": (1, 1, 0, "1/1"),
        "gauge_engine_R_inserted_H": (4, 1, 1, "2/1"),
        "falsifier_R_engine_forced_left_unitary": (1, 4, -1, "1/2"),
    }
    require(errors, set(expected) <= set(rows), "index table missing required rows")
    for rule_id, (right_rank, left_rank, signed, ratio) in expected.items():
        row = rows.get(rule_id, {})
        require(errors, row.get("signed_log2_index") == signed, f"{rule_id} signed index drift")
        require(errors, row.get("standard_index_ratio") == ratio, f"{rule_id} ratio drift")
        require(
            errors,
            row.get("right_crossing_rank", {}).get("support_factor_vector_space_dim") == right_rank,
            f"{rule_id} right support rank drift",
        )
        require(
            errors,
            row.get("left_crossing_rank", {}).get("support_factor_vector_space_dim") == left_rank,
            f"{rule_id} left support rank drift",
        )
        require(errors, row.get("metadata_flow_fields_present") is False, f"{rule_id} metadata-flow gate failed")
        require(errors, "wire_flow" not in row, f"{rule_id} must not carry v1 wire_flow metadata")
    controls = env.get("index_controls", {})
    require(errors, controls.get("all_pass") is True, "index controls did not all pass")
    require(errors, controls.get("L_R_realization", {}).get("opposite_signs") is True, "L/R signs are not opposite")
    require(
        errors,
        controls.get("L_R_realization", {}).get("expectation_2_status") == "earned_for_this_open_chain_fixture",
        "expectation 2 open-chain fixture status drift",
    )
    require(errors, controls.get("index0_control", {}).get("lr_distinction_detected") is False, "index-zero control shows L/R distinction")
    require(errors, controls.get("gauge_local_basis_invariance", {}).get("same_index") is True, "gauge index changed")
    require(errors, controls.get("gauge_local_basis_invariance", {}).get("same_ratio") is True, "gauge ratio changed")
    require(
        errors,
        controls.get("real_unitary_falsifier_branch", {}).get("opposite_signs_after_mutation") is False,
        "real-unitary falsifier did not kill opposite-sign predicate",
    )


def validate_ring_and_classical(errors: list[str], env: dict[str, Any]) -> None:
    ring_rows = env.get("ring_closure_rows", [])
    require(errors, len(ring_rows) >= 6, "ring closure rows missing")
    for row in ring_rows:
        require(errors, row.get("signed_log2_index") == 0, f"{row.get('rule_id')} finite-cut closure index must be zero")
        boundary = row.get("ring_triviality_boundary", {})
        require(errors, boundary.get("automorphism_class_signed_log2_index") == 0, f"{row.get('rule_id')} automorphism-class closure drift")
        require(
            errors,
            boundary.get("any_nonzero_ring_index_status") == "circuit_presentation_or_phase_convention_relative_only_not_claimed_here",
            f"{row.get('rule_id')} ring nonzero-index label missing",
        )
    ring_control = env.get("index_controls", {}).get("ring_closure", {})
    require(errors, ring_control.get("automorphism_class_all_trivial") is True, "ring automorphism class not all trivial")
    require(errors, ring_control.get("finite_cut_rows_all_zero") is True, "ring finite-cut rows not all zero")
    require(errors, ring_control.get("nonzero_ring_index_claimed") is False, "ring nonzero index must not be claimed")

    classical = env.get("classical_dephased_limit", {})
    require(errors, classical.get("phase_structure_reproduced") is True, "classical dephased limit did not reproduce v0")
    floor = classical.get("corrected_structural_floor", {})
    require(errors, floor.get("alternating_transient_scc_count") == 352, "alternating transient SCC drift")
    require(errors, floor.get("paired_transient_scc_count") == 128, "paired transient SCC drift")
    periods = classical.get("period_rows_kept_as_implementation_checks", {})
    require(errors, periods.get("alternating_period_histogram") == {"2": 576}, "alternating period drift")
    require(errors, periods.get("paired_period_histogram") == {"4": 576}, "paired period drift")


def validate_smt_and_tools(errors: list[str], env: dict[str, Any]) -> None:
    proofs = env.get("crossover_proofs", {})
    for solver_name in ("z3", "cvc5"):
        proof = proofs.get(solver_name, {})
        require(errors, proof.get("ran") is True, f"{solver_name} proof did not run")
        require(errors, proof.get("load_bearing") is True, f"{solver_name} proof not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{solver_name} verdict drift")
        require(errors, proof.get("computed_real_unitary_flip_verdict") == "sat", f"{solver_name} real flip verdict drift")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 verdict drift")

    require(errors, bool(env.get("TOOL_INTENT_MATRIX")), "TOOL_INTENT_MATRIX missing")
    require(errors, bool(env.get("tool_intent", {}).get("claim_classes")), "tool_intent claim classes missing")
    require(errors, env.get("TOOL_MANIFEST", {}).get("build_three_engine_envelope", {}).get("used") is True, "envelope helper manifest missing")
    require(errors, env.get("TOOL_INTEGRATION_DEPTH", {}).get("build_three_engine_envelope") == "load_bearing", "envelope helper depth drift")
    require(errors, env.get("TOOL_MANIFEST", {}).get("builder_audit_boundary", {}).get("used") is True, "boundary helper manifest missing")
    require(errors, env.get("TOOL_INTEGRATION_DEPTH", {}).get("builder_audit_boundary") == "load_bearing", "boundary helper depth drift")
    required_depths = {
        "julia": ["QuantumOptics", "QuantumClifford", "Z3"],
        "jax": ["qutip", "sympy", "z3", "cvc5"],
        "pytorch": ["torch.func", "sympy", "z3", "cvc5"],
    }
    manifest = env.get("TOOL_MANIFEST", {})
    depth = env.get("TOOL_INTEGRATION_DEPTH", {})
    for engine, packages in required_depths.items():
        for package in packages:
            require(errors, manifest.get(engine, {}).get(package, {}).get("used") is True, f"TOOL_MANIFEST missing {engine}.{package}")
            require(errors, depth.get(engine, {}).get(package) == "load_bearing", f"TOOL_INTEGRATION_DEPTH drift for {engine}.{package}")
            require(
                errors,
                bool(env.get("tool_intent", {}).get("engine_tool_intent", {}).get(engine, {}).get(package)),
                f"tool_intent missing {engine}.{package}",
            )


def validate_envelope(errors: list[str], env: dict[str, Any], phase: str) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "all three engines required")
    if phase == "builder":
        errors.extend(builder_audit_boundary_errors(env, PACKET / "audit_verdict.md"))
        require(errors, env.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
        require(errors, env.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
        require(errors, env.get("builder_gates", {}).get("no_builder_audit_verdict") is True, "builder no-audit gate false")

    generic_errors = validate_three_engine(
        env,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {error}" for error in generic_errors)

    source = ROOT / str(env.get("source_path", ""))
    require(errors, source.is_file(), "envelope source path missing")
    if source.is_file():
        require(errors, env.get("source_sha256") == sha256_file(source), "envelope source sha drift")
    for key, value in env.get("build_gates", {}).items():
        require(errors, value is True, f"build gate {key} must be true")
    require(errors, env.get("builder_gates", {}).get("file_boundary") == rel(PACKET), "file boundary gate drift")
    require(errors, env.get("object", {}).get("automorphism_class_index_on_finite_ring") == "trivial_by_amendment", "finite-ring boundary missing")
    validate_index_rows(errors, env)
    validate_ring_and_classical(errors, env)
    validate_smt_and_tools(errors, env)


def validate_packet(phase: str) -> dict[str, Any]:
    errors: list[str] = []
    validate_packet_files(errors, phase)

    payloads: dict[str, dict[str, Any]] = {}
    for name, path in RESULT_PATHS.items():
        if not path.is_file():
            errors.append(f"missing result: {rel(path)}")
            continue
        payloads[name] = load_json(path)

    for engine in ("julia", "jax", "pytorch"):
        if engine in payloads:
            validate_leg(errors, engine, payloads[engine])
    if "envelope" in payloads:
        validate_envelope(errors, payloads["envelope"], phase)

    result = {
        "schema": f"{SIM_ID}_validator_v1",
        "sim_id": SIM_ID,
        "phase": phase,
        "ok": not errors,
        "errors": errors,
        "validated_path": rel(RESULT_PATHS["envelope"]),
        "validator": rel(Path(__file__).resolve()),
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["builder", "post_audit"], default="builder")
    args = parser.parse_args()
    result = validate_packet(args.phase)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
