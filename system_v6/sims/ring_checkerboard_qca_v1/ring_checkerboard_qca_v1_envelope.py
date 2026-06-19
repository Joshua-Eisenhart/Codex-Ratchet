#!/usr/bin/env python3
"""Envelope builder for ring_checkerboard_qca_v1."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from ring_checkerboard_qca_v1_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PACKET,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
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
        "tool_calls": leg["one_to_one_tool_calls"]["calls"],
        "one_to_one_tool_calls": leg["one_to_one_tool_calls"],
    }


def engine_value_divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: legs[engine]["engine_values"] for engine in ("julia", "jax", "pytorch")}
    max_divergence = 0
    for key, base in values["julia"].items():
        for engine in ("jax", "pytorch"):
            max_divergence = max(max_divergence, abs(int(values[engine][key]) - int(base)))
    return {
        "julia_authoritative": True,
        "engine_values": values,
        "max_divergence": float(max_divergence),
        "comparison": "integer index and matched-locality terminal-count rows agree across all three engine files",
    }


def validator_expected_commands() -> list[str]:
    sim_py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    julia = (
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no "
        "--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
        f"{rel(PACKET / (SIM_ID + '_julia.jl'))}"
    )
    return [
        julia,
        f"{sim_py} {rel(PACKET / (SIM_ID + '_jax.py'))}",
        f"env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache {sim_py} {rel(PACKET / (SIM_ID + '_pytorch.py'))}",
        f"{sim_py} {rel(PACKET / (SIM_ID + '_envelope.py'))}",
        f"{sim_py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT_PATH)}",
        f"{sim_py} {rel(PACKET / ('validate_' + SIM_ID + '.py'))} --phase builder",
        f"PYTHONPATH={rel(PACKET)} {sim_py} -m pytest -q {rel(PACKET / 'tests')}",
    ]


def build_result() -> dict[str, Any]:
    legs = {engine: load_json(path) for engine, path in LEG_PATHS.items()}
    packet = legs["jax"]["packet"]
    div = engine_value_divergence(legs)
    proofs = {
        "z3": packet["crossover_proofs"]["z3"],
        "cvc5": packet["crossover_proofs"]["cvc5"],
        "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        "pytorch_z3": legs["pytorch"]["engine_specific_checks"]["z3"],
        "pytorch_cvc5": legs["pytorch"]["engine_specific_checks"]["cvc5"],
        "jax_z3": legs["jax"]["engine_specific_checks"]["z3"],
        "jax_cvc5": legs["jax"]["engine_specific_checks"]["cvc5"],
    }
    builder_gate = builder_audit_boundary_ok(PACKET / "audit_verdict.md")
    engine_values_agree = div["max_divergence"] == 0.0
    build_gates = {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "build_card_copied": (PACKET / "build_card.md").is_file()
        and "ring_checkerboard_qca_v1" in (PACKET / "build_card.md").read_text(encoding="utf-8"),
        "no_builder_audit_verdict": builder_gate,
        "engine_lanes_pass": all(legs[engine]["all_pass"] is True for engine in legs),
        "engine_values_agree": engine_values_agree,
        "index_calibrations_pass": packet["index_controls"]["calibration"]["right_shift_plus_one"]
        and packet["index_controls"]["calibration"]["left_shift_minus_one"]
        and packet["index_controls"]["calibration"]["onsite_zero"],
        "L_R_opposite_indices": packet["index_controls"]["L_R_realization"]["opposite_signs"] is True,
        "index0_no_LR_distinction": packet["index_controls"]["index0_control"]["lr_distinction_detected"] is False,
        "gauge_invariance_pass": packet["index_controls"]["gauge_local_basis_invariance"]["same_index"] is True,
        "classical_limit_reproduces_v0": packet["classical_limit"]["phase_structure_reproduced"] is True,
        "locality_comparison_differs": packet["locality_comparison"]["terminal_or_orbit_structure_differs"] is True,
        "order_shuffle_changes": packet["locality_comparison"]["order_shuffle_changes_local_structure"] is True,
        "falsifier_branch_reachable": packet["index_controls"]["falsifier_branch"]["reachable"] is True,
        "z3_unsat": proofs["z3"]["verdict"] == "unsat",
        "cvc5_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "z3_flip_sat": proofs["z3"]["computed_perturbation_flip_verdict"] == "sat",
        "cvc5_flip_sat": proofs["cvc5"]["computed_perturbation_flip_verdict"] == "sat",
        "julia_z3_unsat": proofs["julia_z3"]["verdict"] == "unsat",
    }
    all_pass = all(build_gates.values()) and packet["all_pass"] is True
    tool_intent = {
        "claim_classes": [
            "partitioned_QCA_local_channel_form",
            "standard_math_GNVW_signed_index_alignment",
            "L_R_opposite_information_flux",
            "index_zero_control",
            "locality_changes_coupling_comparison",
            "typed_information_flux",
            "smt_index_calibration_binding",
        ],
        "engine_tool_intent": {engine: legs[engine]["package_observables"] for engine in legs},
    }
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "finite partitioned QCA/index diagnostic on the committed ring-checkerboard support",
        "allowed_claims": [
            "same owner-shaped support as ring_checkerboard_automaton_v0",
            "qubit local systems and local unitary/CPTP gate controls",
            "standard-math signed log2 index for partitioned QCA wire-flow rows",
            "computed L/R opposite index signs and index-zero no-distinction control",
            "bounded matched-state locality-vs-global coupling comparison",
            "typed information flux rows in qubits and nats per step",
        ],
        "disallowed_claims": [
            "canonical QCA admission",
            "full all-cells binary QCA state-space enumeration",
            "v4 coupling-law admission",
            "owner-source status for GNVW/index terminology",
            "physics/cosmology/consciousness claim",
        ],
        "support": packet["support"],
        "object": packet["object"],
        "local_quantum_gates": packet["local_quantum_gates"],
        "index_table": packet["index_table"],
        "index_controls": packet["index_controls"],
        "typed_information_flux_rows": packet["typed_information_flux_rows"],
        "locality_comparison": packet["locality_comparison"],
        "classical_limit": packet["classical_limit"],
        "positive_section": packet["positive_section"],
        "negative_section": packet["negative_section"],
        "boundary_section": packet["boundary_section"],
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": builder_gate,
            "no_builder_audit_verdict_envelope_gate": builder_gate,
            "file_boundary": rel(PACKET),
        },
        "no_builder_audit_verdict": builder_gate,
        "no_builder_audit_verdict_envelope_gate": builder_gate,
        "build_gates": build_gates,
        "engine_comparison": {
            "engine_values": div["engine_values"],
            "engine_values_agree": engine_values_agree,
            "leg_all_pass": {engine: legs[engine]["all_pass"] for engine in legs},
        },
        "TOOL_INTENT_MATRIX": {
            **{engine: legs[engine]["package_observables"] for engine in legs},
            "build_three_engine_envelope": "standard helper constructs the envelope; process/load-bearing, not mathematical evidence",
        },
        "tool_intent": tool_intent,
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"tried": True, "used": True, "reason": "load-bearing standard envelope construction"},
            **{engine: legs[engine]["TOOL_MANIFEST"] for engine in legs},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            **{engine: legs[engine]["TOOL_INTEGRATION_DEPTH"] for engine in legs},
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
            "index_table_hash": stable_sha256(packet["index_table"]),
            "locality_comparison_hash": stable_sha256(packet["locality_comparison"]),
        },
        "runtime_versions": {"python": sys.version.split()[0], "platform": platform.platform()},
        "validator_expected_commands": validator_expected_commands(),
    }
    payload = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: lane_record(legs[engine]) for engine in ("julia", "jax", "pytorch")},
        mode="all_three_full_sims",
        claim_path_tools=[
            "QuantumOptics",
            "QuantumClifford",
            "Graphs",
            "Z3",
            "qutip",
            "sympy",
            "z3",
            "cvc5",
            "torch_geometric",
            "torch.func",
        ],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("index_table", stable_sha256(packet["index_table"])),
            ("index_controls", stable_sha256(packet["index_controls"])),
            ("locality_comparison", stable_sha256(packet["locality_comparison"])),
            ("classical_limit", stable_sha256(packet["classical_limit"])),
        ],
        extra_fields=extra_fields,
    )
    payload["all_pass"] = all_pass
    return payload


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(f"wrote: {rel(RESULT_PATH)}")
    print(
        "RING_CHECKERBOARD_QCA_V1_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"L={result['index_controls']['L_R_realization']['L_signed_index']} "
        f"R={result['index_controls']['L_R_realization']['R_signed_index']} "
        f"local_terminal={result['locality_comparison']['local_brickwork']['signature']['terminal_class_count']} "
        f"global_terminal={result['locality_comparison']['global_v3_style']['signature']['terminal_class_count']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
