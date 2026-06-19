#!/usr/bin/env python3
"""Envelope builder for ring_checkerboard_automaton_v0."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from ring_checkerboard_automaton_v0_common import (
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
        "role_id": leg["role_id"],
        "claim_path_tools": leg["claim_path_tools"],
        "tool_calls": leg["tool_calls"],
        "one_to_one_tool_calls": leg["one_to_one_tool_calls"],
    }


def merge_tool_manifest(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg["TOOL_MANIFEST"] for engine, leg in legs.items()}


def merge_tool_depth(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg["TOOL_INTEGRATION_DEPTH"] for engine, leg in legs.items()}


def engine_comparison(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        engine: {
            "primary_state_count": int(leg["engine_values"]["primary_state_count"]),
            "primary_intrinsic_terminal_count": int(leg["engine_values"]["primary_intrinsic_terminal_count"]),
        }
        for engine, leg in legs.items()
    }
    return {
        "values": values,
        "primary_state_count_agreement": len({row["primary_state_count"] for row in values.values()}) == 1,
        "primary_intrinsic_terminal_count_agreement": len({row["primary_intrinsic_terminal_count"] for row in values.values()}) == 1,
        "partition_signature_sha256": {engine: leg["partition_signature_sha256"] for engine, leg in legs.items()},
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        engine: float(leg["engine_values"]["primary_intrinsic_terminal_count"])
        for engine, leg in legs.items()
    }
    return {
        "julia_authoritative": True,
        "metric": "primary_intrinsic_terminal_count",
        "engine_values": values,
        "max_divergence": max(values.values()) - min(values.values()),
    }


def expected_commands() -> list[str]:
    sim_py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    julia_cmd = (
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no "
        "--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
        f"{rel(PACKET / (SIM_ID + '_julia.jl'))}"
    )
    return [
        julia_cmd,
        f"env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache {sim_py} {rel(PACKET / (SIM_ID + '_jax.py'))}",
        f"env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache {sim_py} {rel(PACKET / (SIM_ID + '_pytorch.py'))}",
        f"{sim_py} {rel(PACKET / (SIM_ID + '_envelope.py'))}",
        f"{sim_py} {rel(PACKET / ('validate_' + SIM_ID + '.py'))} --phase builder",
        f"{sim_py} -m pytest -q {rel(PACKET / 'tests')}",
        f"{sim_py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT_PATH)}",
    ]


def build_result() -> dict[str, Any]:
    legs = {engine: load_json(path) for engine, path in LEG_PATHS.items()}
    jax_packet = legs["jax"]["packet"]
    proofs = {
        "z3": jax_packet["crossover_proofs"]["z3"],
        "cvc5": jax_packet["crossover_proofs"]["cvc5"],
        "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        "pytorch_z3": legs["pytorch"]["crossover_proofs"]["z3"],
        "pytorch_cvc5": legs["pytorch"]["crossover_proofs"]["cvc5"],
    }
    comparison = engine_comparison(legs)
    div = divergence(legs)
    builder_gate = builder_audit_boundary_ok(PACKET / "audit_verdict.md")
    control_gates = {
        "similarity_only_cluster_fails_as_basin": jax_packet["controls"]["similarity_only_cluster"]["fired"] is True,
        "non_partitioned_scramble_changes": jax_packet["controls"]["non_partitioned_scramble"]["fired"] is True,
        "order_shuffle_changes": jax_packet["controls"]["order_shuffle"]["fired"] is True,
        "label_permutation_count_invariant": jax_packet["controls"]["label_permutation"]["counts_invariant"] is True,
        "ring_off_changes": jax_packet["controls"]["ring_off"]["fired"] is True,
        "checkerboard_off_changes": jax_packet["controls"]["checkerboard_off"]["fired"] is True,
        "nesting_off_changes": jax_packet["controls"]["nesting_off"]["fired"] is True,
        "frozen_phase_degenerate_changes": jax_packet["controls"]["frozen_phase"]["fired"] is True,
    }
    build_gates = {
        "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
        "no_builder_audit_verdict": builder_gate,
        "phase_test_pass": jax_packet["phase_test"]["verdict"] == "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR",
        "alternating_order_preserved": jax_packet["phase_test"]["alternating_order"]["preserved"] is True,
        "paired_order_preserved": jax_packet["phase_test"]["paired_order"]["preserved"] is True,
        "phase_terminal_structure_distinguishable": jax_packet["phase_test"]["terminal_structure_distinguishable"] is True,
        "phase_orbit_structure_distinguishable": jax_packet["phase_test"]["orbit_structure_distinguishable"] is True,
        "nesting_changes_terminal_structure": jax_packet["nesting_comparison"]["terminal_structure_changed"] is True,
        "controls_pass": all(control_gates.values()),
        "z3_unsat": proofs["z3"]["verdict"] == "unsat",
        "cvc5_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "z3_flip_sat": proofs["z3"]["computed_perturbation_flip_verdict"] == "sat",
        "cvc5_flip_sat": proofs["cvc5"]["computed_perturbation_flip_verdict"] == "sat",
        "julia_z3_unsat": proofs["julia_z3"]["verdict"] == "unsat",
        "engine_primary_counts_agree": comparison["primary_state_count_agreement"] and comparison["primary_intrinsic_terminal_count_agreement"],
    }
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all(leg["all_pass"] for leg in legs.values()) and all(build_gates.values()) and div["max_divergence"] == 0.0,
        "claim": "classical partitioned ring-checkerboard automaton floor over the owner-source support, with alternating/deductive and paired/inductive phase-test separation",
        "correction_28fc221a1": {
            "phase_period_result": "definitional_implementation_check",
            "structural_result": "transient_scc_topology_difference",
            "state_population_scope": "alternating and paired traverse disjoint complementary single-token populations: deductive-order tokens vs inductive-order tokens, with matching cardinality on the same ring cell geometry",
            "single_token_scope": "period and SCC rows are for one active readout-token cursor, not full cellular-automaton field dynamics over the full binary configuration space",
            "period_caveat": "period-2 versus period-4 follows from two stage advances per alternating transition versus one stage advance per paired transition",
        },
        "allowed_claims": [
            "finite single-active readout-token probe family over base ring plus one attached-ring level",
            "local even/odd and paired-block update disciplines using ring and immediate attachment neighbors",
            "computed SCC, terminal class, absent-exit, may/must, and orbit rows for the declared probe family",
            "computed size table for steps-per-ring 4, 8, and 16",
            "computed one-level nesting comparison against the bare ring",
        ],
        "disallowed_claims": jax_packet["boundary_section"]["must_not_claim"],
        "object": jax_packet["object"],
        "finite_S": jax_packet["finite_S"],
        "Adm_C": jax_packet["finite_S"]["Adm_C"],
        "M_C": jax_packet["finite_S"]["M_C"],
        "R_C_explicit": jax_packet["R_C_explicit"],
        "phase_test": jax_packet["phase_test"],
        "basin_partition_tables": jax_packet["basin_partition_tables"],
        "nesting_comparison": jax_packet["nesting_comparison"],
        "microstate_count_rows": jax_packet["microstate_count_rows"],
        "controls": jax_packet["controls"],
        "control_gates": control_gates,
        "positive_section": jax_packet["positive_section"],
        "negative_section": jax_packet["negative_section"],
        "boundary_section": jax_packet["boundary_section"],
        "guard": jax_packet["guard"],
        "builder_gates": {
            "no_builder_audit_verdict": builder_gate,
            "no_builder_audit_verdict_envelope_gate": builder_gate,
            "file_boundary": rel(PACKET),
        },
        "no_builder_audit_verdict": builder_gate,
        "no_builder_audit_verdict_envelope_gate": builder_gate,
        "build_gates": build_gates,
        "engine_comparison": comparison,
        "TOOL_INTENT_MATRIX": {engine: legs[engine]["package_observables"] for engine in legs},
        "tool_intent": {
            "claim_classes": [
                "finite_transition_graph",
                "phase_separation",
                "basin_partition",
                "nesting_comparison",
                "smt_count_binding",
            ],
            "engine_tool_intent": {engine: legs[engine]["package_observables"] for engine in legs},
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"tried": True, "used": True, "reason": "load-bearing standard envelope construction"},
            **merge_tool_manifest(legs),
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            **merge_tool_depth(legs),
        },
        "tool_calls": {engine: legs[engine]["tool_calls"] for engine in legs},
        "one_to_one_tool_calls": {
            "pass": all(legs[engine]["one_to_one_tool_calls"]["pass"] is True for engine in legs),
            "by_engine": {engine: legs[engine]["one_to_one_tool_calls"] for engine in legs},
        },
        "parent_lineage": parent_lineage(),
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "phase_test_hash": stable_sha256(jax_packet["phase_test"]),
            "controls_hash": stable_sha256(jax_packet["controls"]),
        },
        "summary_corrections": {
            "phase_period_result": "definitional_implementation_check",
            "structural_result": "transient_scc_topology_difference",
            "state_population_scope": "disjoint complementary deductive-order and inductive-order single-token populations on the same ring cell geometry",
            "single_token_scope": "single active readout-token trajectory only; full CA binary field dynamics not enumerated",
        },
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "validator_expected_commands": expected_commands(),
    }
    payload = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: lane_record(legs[engine]) for engine in ("julia", "jax", "pytorch")},
        mode="all_three_full_sims",
        claim_path_tools=["Graphs", "networkx", "sympy", "z3", "cvc5", "torch_geometric"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=parent_lineage(),
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("phase_test", stable_sha256(jax_packet["phase_test"])),
            ("controls", stable_sha256(jax_packet["controls"])),
            ("microstate_count_rows", stable_sha256(jax_packet["microstate_count_rows"])),
            ("nesting_comparison", stable_sha256(jax_packet["nesting_comparison"])),
        ],
        extra_fields=extra_fields,
    )
    payload["all_pass"] = bool(extra_fields["all_pass"])
    return payload


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
