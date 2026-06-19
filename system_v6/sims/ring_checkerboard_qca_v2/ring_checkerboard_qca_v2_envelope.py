#!/usr/bin/env python3
"""Envelope builder for ring_checkerboard_qca_v2."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from ring_checkerboard_qca_v2_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PACKET,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    build_packet,
    parent_lineage,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}

spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_record(leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": leg["result_path"],
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "claim_path_tools": leg["claim_path_tools"],
        "one_to_one_tool_calls": leg["one_to_one_tool_calls"],
    }


def engine_value_divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: legs[engine]["engine_values"] for engine in ("julia", "jax", "pytorch")}
    all_keys = sorted(set().union(*(set(row) for row in values.values())))
    max_divergence = 0.0
    per_key: dict[str, dict[str, Any]] = {}
    for key in all_keys:
        key_values = {engine: values[engine].get(key) for engine in values}
        numeric = [float(value) for value in key_values.values() if isinstance(value, (int, float))]
        if numeric:
            key_div = max(numeric) - min(numeric)
            max_divergence = max(max_divergence, key_div)
        else:
            key_div = 0.0 if len(set(key_values.values())) == 1 else 1.0
            max_divergence = max(max_divergence, key_div)
        per_key[key] = {"values": key_values, "max_divergence": key_div}
    return {
        "julia_authoritative": True,
        "engine_values": values,
        "per_key": per_key,
        "max_divergence": max_divergence,
        "comparison": "integer rank/index, ring closure, and corrected v0 continuity scalars agree across all three engine files",
    }


def expected_commands() -> list[str]:
    sim_py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    julia = (
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no "
        "--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
        f"{rel(PACKET / (SIM_ID + '_julia.jl'))}"
    )
    return [
        julia,
        f"PYTHONDONTWRITEBYTECODE=1 {sim_py} {rel(PACKET / (SIM_ID + '_jax.py'))}",
        f"PYTHONDONTWRITEBYTECODE=1 {sim_py} {rel(PACKET / (SIM_ID + '_pytorch.py'))}",
        f"PYTHONDONTWRITEBYTECODE=1 {sim_py} {rel(PACKET / (SIM_ID + '_envelope.py'))}",
        f"PYTHONDONTWRITEBYTECODE=1 {sim_py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT_PATH)}",
        f"PYTHONDONTWRITEBYTECODE=1 {sim_py} {rel(PACKET / ('validate_' + SIM_ID + '.py'))} --phase builder",
        f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH={rel(PACKET)} {sim_py} -m pytest -q -p no:cacheprovider {rel(PACKET / 'tests')}",
    ]


def build_result() -> dict[str, Any]:
    legs = {engine: load_json(path) for engine, path in LEG_PATHS.items()}
    packet = build_packet()
    div = engine_value_divergence(legs)
    proofs = {
        "z3": packet["crossover_proofs"]["z3"],
        "cvc5": packet["crossover_proofs"]["cvc5"],
        "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        "jax_z3": legs["jax"]["engine_specific_checks"]["z3"],
        "jax_cvc5": legs["jax"]["engine_specific_checks"]["cvc5"],
        "pytorch_z3": legs["pytorch"]["engine_specific_checks"]["z3"],
        "pytorch_cvc5": legs["pytorch"]["engine_specific_checks"]["cvc5"],
    }
    builder_gate = builder_audit_boundary_ok(PACKET / "audit_verdict.md")
    rows_by_id = {row["rule_id"]: row for row in packet["index_table"]}
    build_gates = {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "build_card_copied": (PACKET / "build_card.md").is_file()
        and SIM_ID in (PACKET / "build_card.md").read_text(encoding="utf-8"),
        "no_builder_audit_verdict": builder_gate,
        "engine_lanes_pass": all(legs[engine]["all_pass"] is True for engine in legs),
        "engine_values_agree": div["max_divergence"] == 0.0,
        "right_shift_plus_one": rows_by_id["calibration_right_shift"]["signed_log2_index"] == 1,
        "left_shift_minus_one": rows_by_id["calibration_left_shift"]["signed_log2_index"] == -1,
        "onsite_zero": rows_by_id["calibration_nonshifting_onsite"]["signed_log2_index"] == 0,
        "paired_zero": rows_by_id["paired_block_index0"]["signed_log2_index"] == 0,
        "L_R_opposite_indices": packet["index_controls"]["L_R_realization"]["opposite_signs"] is True,
        "index0_no_LR_distinction": packet["index_controls"]["index0_control"]["lr_distinction_detected"] is False,
        "gauge_recomputed_same_index": packet["index_controls"]["gauge_local_basis_invariance"]["same_index"] is True,
        "ring_closure_trivial": packet["index_controls"]["ring_closure"]["automorphism_class_all_trivial"] is True
        and packet["index_controls"]["ring_closure"]["finite_cut_rows_all_zero"] is True,
        "real_unitary_falsifier_reachable": packet["index_controls"]["real_unitary_falsifier_branch"]["reachable_by_real_unitary_replacement"] is True,
        "classical_dephased_limit_reproduces_v0": packet["classical_dephased_limit"]["phase_structure_reproduced"] is True,
        "z3_unsat": proofs["z3"]["verdict"] == "unsat",
        "cvc5_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "z3_flip_sat": proofs["z3"]["computed_real_unitary_flip_verdict"] == "sat",
        "cvc5_flip_sat": proofs["cvc5"]["computed_real_unitary_flip_verdict"] == "sat",
        "julia_z3_unsat": proofs["julia_z3"]["verdict"] == "unsat",
    }
    all_pass = all(build_gates.values()) and packet["all_pass"] is True
    lanes = {engine: lane_record(leg) for engine, leg in legs.items()}
    tool_intent = {
        "claim_classes": [
            "open_chain_crossing_rank_extraction",
            "O1_L_R_opposite_local_unitary_fixture",
            "gauge_recomputed_rank_invariance",
            "finite_ring_triviality_boundary",
            "dephased_classical_floor_continuity",
            "SMT_rank_index_binding",
        ],
        "engine_tool_intent": {engine: legs[engine]["package_observables"] for engine in legs},
    }
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "amended open-chain QCA crossing-rank diagnostic with finite-ring closure triviality for the ring checkerboard O1 L/R fixture",
        "allowed_claims": packet["allowed_claims"],
        "disallowed_claims": packet["disallowed_claims"],
        "object": packet["object"],
        "index_table": packet["index_table"],
        "ring_closure_rows": packet["ring_closure_rows"],
        "index_controls": packet["index_controls"],
        "typed_information_flux_rows": packet["typed_information_flux_rows"],
        "classical_dephased_limit": packet["classical_dephased_limit"],
        "symbolic_gate_checks": packet["symbolic_gate_checks"],
        "positive_section": packet["positive_section"],
        "negative_section": packet["negative_section"],
        "boundary_section": packet["boundary_section"],
        "builder_gates": {
            "file_disjoint_packet": True,
            "file_boundary": rel(PACKET),
            "no_builder_audit_verdict": builder_gate,
            "no_builder_audit_verdict_envelope_gate": builder_gate,
            "boundary_helper": rel(ROOT / "scripts" / "builder_audit_boundary.py"),
        },
        "no_builder_audit_verdict": builder_gate,
        "no_builder_audit_verdict_envelope_gate": builder_gate,
        "build_gates": build_gates,
        "engine_comparison": {
            "engine_values": div["engine_values"],
            "engine_values_agree": div["max_divergence"] == 0.0,
            "leg_all_pass": {engine: legs[engine]["all_pass"] for engine in legs},
        },
        "TOOL_INTENT_MATRIX": {
            "julia": legs["julia"]["package_observables"],
            "jax": legs["jax"]["package_observables"],
            "pytorch": legs["pytorch"]["package_observables"],
            "shared_python": packet["TOOL_INTENT_MATRIX"],
            "build_three_engine_envelope": "standard helper constructs the result envelope; process/load-bearing, not mathematical evidence",
            "builder_audit_boundary": "builder/auditor file-boundary helper gates audit_verdict absence/independence",
        },
        "tool_intent": tool_intent,
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"tried": True, "used": True, "reason": "load-bearing standard envelope construction"},
            "builder_audit_boundary": {"tried": True, "used": True, "reason": "load-bearing builder/audit boundary check"},
            **{engine: legs[engine]["TOOL_MANIFEST"] for engine in legs},
            "shared_python": packet["TOOL_MANIFEST"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "builder_audit_boundary": "load_bearing",
            **{engine: legs[engine]["TOOL_INTEGRATION_DEPTH"] for engine in legs},
            "shared_python": packet["TOOL_INTEGRATION_DEPTH"],
        },
        "one_to_one_tool_calls": {
            "pass": all(legs[engine]["one_to_one_tool_calls"]["pass"] is True for engine in legs),
            "by_engine": {engine: legs[engine]["one_to_one_tool_calls"] for engine in legs},
        },
        "parent_lineage": parent_lineage(),
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "packet_index_table_hash": stable_sha256(packet["index_table"]),
            "packet_ring_closure_hash": stable_sha256(packet["ring_closure_rows"]),
            "packet_classical_limit_hash": stable_sha256(packet["classical_dephased_limit"]),
        },
        "validator_expected_commands": expected_commands(),
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
        },
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes=lanes,
        mode="amended_open_chain_qca_crossing_rank",
        claim_path_tools=[
            "QuantumOptics",
            "QuantumClifford",
            "qutip",
            "torch.func",
            "sympy",
            "z3",
            "cvc5",
        ],
        crossover_proofs={"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": proofs["julia_z3"]},
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        stability_pairs=[
            ("index_table", stable_sha256(packet["index_table"])),
            ("ring_closure_rows", stable_sha256(packet["ring_closure_rows"])),
            ("classical_dephased_limit", stable_sha256(packet["classical_dephased_limit"])),
        ],
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
