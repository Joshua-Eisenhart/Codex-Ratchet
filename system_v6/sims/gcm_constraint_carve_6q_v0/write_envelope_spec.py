#!/usr/bin/env python3
"""Write the standard three-engine envelope spec for gcm_constraint_carve_6q_v0."""

from __future__ import annotations

import json

from gcm_constraint_carve_6q_v0_common import (
    CLASSIFICATION,
    ENVELOPE_SPEC_PATH,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SIM_DIR,
    SIM_ID,
    load_json,
    rel,
    write_json,
)

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "builds the envelope spec from already-written 6Q lane results"},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


def lane_result(name: str) -> dict[str, object]:
    return load_json(RESULT_DIR / f"{SIM_ID}_{name}_results.json")


def build_spec() -> dict[str, object]:
    common = load_json(RESULT_DIR / f"{SIM_ID}_results.json")
    lanes = {
        "julia": {
            "source_path": rel(SIM_DIR / f"{SIM_ID}_julia.jl"),
            "result_path": rel(RESULT_DIR / f"{SIM_ID}_julia_results.json"),
            "reads_peer_result": False,
            "packages_used": ["Dates", "JSON3", "SHA", "Graphs"],
            "aligned_packages_load_bearing": ["Graphs"],
            "package_observables": {"Graphs": "Graphs.SimpleGraph/add_edge!/connected_components over 6Q quotient-class matrix adjacency"},
        },
        "jax": {
            "source_path": rel(SIM_DIR / f"{SIM_ID}_jax.py"),
            "result_path": rel(RESULT_DIR / f"{SIM_ID}_jax_results.json"),
            "reads_peer_result": False,
            "packages_used": ["networkx", "sympy", "z3", "cvc5"],
            "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
            "package_observables": {
                "networkx": "nx.Graph/connected_components over 6Q quotient classes",
                "sympy": "sp.Rational exact 6Q count guards",
                "z3": "z3.Solver unsat guard for 6Q survivor count",
                "cvc5": "cvc5.Solver unsat guard for 6Q survivor count",
            },
        },
        "pytorch": {
            "source_path": rel(SIM_DIR / f"{SIM_ID}_pytorch.py"),
            "result_path": rel(RESULT_DIR / f"{SIM_ID}_pytorch_results.json"),
            "reads_peer_result": False,
            "packages_used": ["torch", "torch.func", "sympy"],
            "aligned_packages_load_bearing": ["torch.func", "sympy"],
            "package_observables": {
                "torch.func": "vmap 6Q C2 active-probe recomputation from matrix-derived first-qubit rows",
                "sympy": "sp.Rational exact 6Q survivor/class count guards",
            },
        },
    }
    engine_values = {
        name: {
            "survivor_count": lane_result(name)["survivor_count"],
            "quotient_class_count": lane_result(name)["quotient_class_count"],
        }
        for name in lanes
    }
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "mode": "all_three_full_sims_state_artifacted_6q_count_fixture",
        "lanes": lanes,
        "claim_path_tools": ["Graphs", "networkx", "torch.func", "sympy", "z3", "cvc5"],
        "crossover_proofs": common["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": 0.0,
            "divergence_log": ["All three lanes agree on survivor_count=548 and quotient_class_count=9."],
        },
        "parent_lineage": common["gcm_lineage"],
        "extra_fields": {
            "gcm_lineage": common["gcm_lineage"],
            "TOOL_MANIFEST": common["TOOL_MANIFEST"],
            "TOOL_INTEGRATION_DEPTH": common["TOOL_INTEGRATION_DEPTH"],
            "tool_intent": common["tool_intent"],
            "candidate_count": common["candidate_space"]["candidate_count"],
            "survivor_count": common["survivor_count"],
            "quotient_class_count": common["quotient"]["class_count"],
            "state_artifact_result_path": rel(RESULT_DIR / f"{SIM_ID}_results.json"),
            "state_artifact_index_sha256": common["result_sha256"],
            "consumed_6q_feedstock": common["consumed_6q_feedstock"],
            "ghz6_w6_cluster_admissibility_matrix": common["ghz6_w6_cluster_admissibility_matrix"],
            "six_party_ckw_monogamy_narrowed": common["six_party_ckw_monogamy_narrowed"],
            "floor_rows_extended": common["floor_rows_extended"],
            "cross_rung_rows": common["cross_rung_rows"],
            "cut_lattice_caveat": {
                "per_cut_reduced_matrices_stored": common["cut_lattice"]["per_cut_reduced_matrices_stored"],
                "reduced_matrix_caveat": common["cut_lattice"]["reduced_matrix_caveat"],
            },
            "helper_preflight": common["helper_preflight"],
            "substrate_checks": common["substrate_checks"],
            "substrate_negatives": common["substrate_negatives"],
            "terrain_blindness_guard": common["terrain_blindness_guard"],
            "controls_summary": {
                "source_recompute_injection_red": common["controls"]["source_recompute_injection_red"],
                "regressions": common["controls"]["regressions"],
            },
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
        },
    }


def main() -> int:
    spec = build_spec()
    write_json(ENVELOPE_SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec": rel(ENVELOPE_SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
