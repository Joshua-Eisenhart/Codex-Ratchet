#!/usr/bin/env python3
"""Packet-local validator for ring_checkerboard_qca_v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ring_checkerboard_qca_v1_common import (
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
    "ring_checkerboard_qca_v1_common.py",
    "ring_checkerboard_qca_v1_julia.jl",
    "ring_checkerboard_qca_v1_jax.py",
    "ring_checkerboard_qca_v1_pytorch.py",
    "ring_checkerboard_qca_v1_envelope.py",
    "validate_ring_checkerboard_qca_v1.py",
    "tests/test_ring_checkerboard_qca_v1.py",
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
        build_card.is_file() and "ring_checkerboard_qca_v1" in build_card.read_text(encoding="utf-8"),
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
    require(errors, values.get("right_shift_index") == 1, f"{name} right shift index drift")
    require(errors, values.get("left_shift_index") == -1, f"{name} left shift index drift")
    require(errors, values.get("zero_index") == 0, f"{name} zero index drift")
    require(errors, values.get("L_engine_index") == -1, f"{name} L engine index drift")
    require(errors, values.get("R_engine_index") == 1, f"{name} R engine index drift")
    require(errors, values.get("local_terminal_count") == 1600, f"{name} local terminal count drift")
    require(errors, values.get("global_terminal_count") == 160, f"{name} global terminal count drift")


def row_by_id(index_table: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("rule_id")): row for row in index_table}


def validate_index_rows(errors: list[str], env: dict[str, Any]) -> None:
    rows = row_by_id(env.get("index_table", []))
    expected = {
        "calibration_right_shift": (1, "2/1"),
        "calibration_left_shift": (-1, "1/2"),
        "calibration_nonshifting_onsite": (0, "1/1"),
        "engine_L_flux_in_left": (-1, "1/2"),
        "engine_R_flux_out_right": (1, "2/1"),
        "engine_L_index0_control": (0, "1/1"),
        "engine_R_index0_control": (0, "1/1"),
        "gauge_reparameterized_right_shift": (1, "2/1"),
        "paired_block_index0": (0, "1/1"),
    }
    require(errors, set(expected) <= set(rows), "index table missing required rows")
    for rule_id, (signed, ratio) in expected.items():
        row = rows.get(rule_id, {})
        require(errors, row.get("signed_log2_index") == signed, f"{rule_id} signed index drift")
        require(errors, row.get("standard_index_ratio") == ratio, f"{rule_id} index ratio drift")
        overlap = row.get("overlap_rank_data", {})
        require(errors, overlap.get("rank_ratio_exact") == ratio, f"{rule_id} overlap-rank ratio drift")
    controls = env.get("index_controls", {})
    require(errors, controls.get("all_pass") is True, "index controls did not all pass")
    require(errors, controls.get("L_R_realization", {}).get("opposite_signs") is True, "L/R signs are not opposite")
    require(errors, controls.get("L_R_realization", {}).get("expectation_2_status") == "earned", "expectation 2 not earned")
    require(errors, controls.get("index0_control", {}).get("lr_distinction_detected") is False, "index-zero control shows L/R distinction")
    require(errors, controls.get("gauge_local_basis_invariance", {}).get("same_index") is True, "gauge index changed")
    require(errors, controls.get("gauge_local_basis_invariance", {}).get("same_ratio") is True, "gauge ratio changed")
    falsifier = controls.get("falsifier_branch", {})
    require(errors, falsifier.get("reachable") is True, "falsifier branch not reachable")
    require(errors, falsifier.get("expectation_2_status") == "killed_as_expected", "falsifier branch did not kill expectation")


def validate_locality_and_classical_limit(errors: list[str], env: dict[str, Any]) -> None:
    locality = env.get("locality_comparison", {})
    require(errors, locality.get("matched_state_count") == 6400, "matched state count drift")
    require(errors, locality.get("terminal_or_orbit_structure_differs") is True, "local/global structures did not differ")
    require(errors, locality.get("order_shuffle_changes_local_structure") is True, "order shuffle did not change local structure")
    local_sig = locality.get("local_brickwork", {}).get("signature", {})
    global_sig = locality.get("global_v3_style", {}).get("signature", {})
    require(errors, local_sig.get("terminal_class_count") == 1600, "local terminal class count drift")
    require(errors, global_sig.get("terminal_class_count") == 160, "global terminal class count drift")
    require(errors, local_sig.get("period_histogram") == {"4": 6400}, "local period histogram drift")
    require(errors, global_sig.get("period_histogram") == {"40": 6400}, "global period histogram drift")

    classical = env.get("classical_limit", {})
    require(errors, classical.get("v0_verdict") == "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR", "v0 classical verdict drift")
    require(errors, classical.get("phase_structure_reproduced") is True, "classical limit did not reproduce v0 phase structure")
    require(errors, classical.get("alternating_period_histogram") == {"2": 576}, "alternating classical period drift")
    require(errors, classical.get("paired_period_histogram") == {"4": 576}, "paired classical period drift")


def validate_typed_and_smt(errors: list[str], env: dict[str, Any]) -> None:
    typed = {row.get("rule_id"): row for row in env.get("typed_information_flux_rows", [])}
    require(errors, typed.get("engine_L_flux_in_left", {}).get("information_flux_qubits_per_step") == -1, "L typed flux drift")
    require(errors, typed.get("engine_R_flux_out_right", {}).get("information_flux_qubits_per_step") == 1, "R typed flux drift")
    require(errors, typed.get("engine_L_index0_control", {}).get("von_neumann_entropy_flux_nats_exact") == "0", "L zero-control typed flux drift")
    require(errors, typed.get("engine_R_index0_control", {}).get("von_neumann_entropy_flux_nats_exact") == "0", "R zero-control typed flux drift")

    proofs = env.get("crossover_proofs", {})
    for solver_name in ("z3", "cvc5"):
        proof = proofs.get(solver_name, {})
        require(errors, proof.get("ran") is True, f"{solver_name} proof did not run")
        require(errors, proof.get("load_bearing") is True, f"{solver_name} proof not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{solver_name} verdict drift")
        require(errors, proof.get("computed_perturbation_flip_verdict") == "sat", f"{solver_name} flip verdict drift")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 verdict drift")


def validate_tool_rows(errors: list[str], env: dict[str, Any]) -> None:
    require(errors, bool(env.get("TOOL_INTENT_MATRIX")), "TOOL_INTENT_MATRIX missing")
    require(errors, bool(env.get("tool_intent", {}).get("claim_classes")), "tool_intent claim classes missing")
    require(errors, env.get("TOOL_MANIFEST", {}).get("build_three_engine_envelope", {}).get("used") is True, "envelope helper manifest missing")
    require(errors, env.get("TOOL_INTEGRATION_DEPTH", {}).get("build_three_engine_envelope") == "load_bearing", "envelope helper depth drift")
    required_depths = {
        "julia": ["QuantumOptics", "QuantumClifford", "Graphs", "Z3"],
        "jax": ["qutip", "sympy", "z3", "cvc5"],
        "pytorch": ["torch_geometric", "torch.func", "sympy", "z3", "cvc5"],
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
    require(errors, env.get("object", {}).get("same_support_as_v0") is True, "same-support object row missing")
    require(
        errors,
        env.get("object", {}).get("index_definition_status") == "standard_math_alignment_not_owner_source",
        "index definition source-status boundary missing",
    )
    require(errors, env.get("engine_comparison", {}).get("engine_values_agree") is True, "engine values disagree")
    require(errors, env.get("divergence", {}).get("max_divergence") == 0.0, "engine divergence not zero")
    validate_index_rows(errors, env)
    validate_locality_and_classical_limit(errors, env)
    validate_typed_and_smt(errors, env)
    validate_tool_rows(errors, env)


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
