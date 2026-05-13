#!/usr/bin/env python3
"""Heat-work and measurement-feedback cycle invariant correlation sim.

This row compares the two receipt-backed opposite-direction cycle-pair rows without
promoting either one into the QIT runtime.  It asks a narrower question:

- what structure is literally shared by the two sims;
- what structure is only an analogy;
- where the analogy breaks and should remain a negative/graveyard signal.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "audit"
classification = CLASSIFICATION
divergence_log = (
    "Cycle-invariant correlation layer over the heat-work and measurement-feedback cycle-pair rows. "
    "It compares loop polarity, tools, legos, graph/proof/density receipts, "
    "and local cycle-step invariant maps. It is not a QIT runtime promotion."
)

LEGO_IDS = [
    "two_bath_heat_work_cycle",
    "measure_feedback_erasure_cycle",
    "landauer_erasure",
    "opposite_direction_cycle_pair",
    "density_matrix",
    "graph_topology",
    "proof_fence",
    "cycle_invariant_correlation",
]
PRIMARY_LEGO_IDS = ["opposite_direction_cycle_pair", "cycle_invariant_correlation"]

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "loads the exact heat-work and measurement-feedback cycles result receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "keeps receipt paths deterministic under the probe result surface",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(stem: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{stem}_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_result(filename: str) -> dict[str, Any] | None:
    path = RESULT_DIR / filename
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def pass_at(result: dict[str, Any], *path: str) -> bool:
    node: Any = result
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return bool(isinstance(node, dict) and node.get("pass") is True)


def shared_load_bearing_tools(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    a_depth = a.get("tool_integration_depth", {})
    b_depth = b.get("tool_integration_depth", {})
    return sorted(
        tool for tool in set(a_depth) & set(b_depth)
        if a_depth.get(tool) == "load_bearing" and b_depth.get(tool) == "load_bearing"
    )


def cycle_invariant_rows(carnot: dict[str, Any], szilard: dict[str, Any]) -> list[dict[str, Any]]:
    heat_work_invariants = carnot["cycle_step_invariant_map"]["invariants"]
    measure_feedback_invariants = szilard["cycle_step_invariant_map"]["invariants"]
    invariant_rows = [
        {
            "row": invariant,
            "relation": "local_invariant_candidate",
            "carnot": heat_work_invariants[invariant]["local_name"],
            "szilard": measure_feedback_invariants[invariant]["local_name"],
            "status": "candidate_analogy_not_identity",
            "boundary": "same invariant row is only a local comparison slot",
        }
        for invariant in sorted(set(heat_work_invariants) & set(measure_feedback_invariants))
    ]
    structural_rows = [
        {
            "row": "dual_stack_polarity",
            "relation": "shared_mechanism_surface",
            "carnot": "work-producing versus work-consuming heat-work traversal",
            "szilard": "measurement-feedback-erasure vs reverse recovery bookkeeping",
            "status": "shared_two_direction_bookkeeping",
            "boundary": "opposite traversals do not make either row a QIT runtime",
        },
        {
            "row": "entropy_carrier",
            "relation": "analogy_with_different_observable",
            "carnot": "reservoir entropy, heat, work",
            "szilard": "record entropy, mutual information, erasure cost",
            "status": "shared_gradient_shape_different_readout",
            "boundary": "thermodynamic and information readouts are not collapsed",
        },
        {
            "row": "carrier_geometry",
            "relation": "density_matrix_overlap",
            "carnot": "finite qubit working substance",
            "szilard": "finite two-qubit system-memory carrier",
            "status": "shared_density_carrier_family",
            "boundary": "one-qubit thermal carrier is not the same topology as two-qubit memory",
        },
        {
            "row": "operator_schedule",
            "relation": "ordered_stage_surface",
            "carnot": "isothermal/adiabatic four-cycle",
            "szilard": "measurement/feedback/erasure protocol",
            "status": "ordered_operators_but_different_arity",
            "boundary": "heat-work is a closed four-cycle; measurement-feedback is a protocol path plus reverse bookkeeping",
        },
        {
            "row": "proof_fence",
            "relation": "shared_forbidden_region_gate",
            "carnot": "super-Carnot blocked by z3/cvc5",
            "szilard": "free Landauer erasure blocked by z3/cvc5",
            "status": "shared_negative_gate_shape",
            "boundary": "different forbidden claims, same proof-fence role",
        },
    ]
    return structural_rows + invariant_rows


def information_theoretic_analogue_map(carnot: dict[str, Any], szilard: dict[str, Any]) -> dict[str, Any]:
    return {
        "boundary": "candidate_search_prior_not_qit_runtime_admission",
        "shared_candidates": {
            "dual_loop_family": "both rows expose inductive_heating_loop and deductive_cooling_loop",
            "density_carrier": "both rows use density-matrix witnesses through qutip and qiskit",
            "graph_carrier": "both rows use rustworkx, PyG, XGI, and optional topology tools",
            "proof_fence": "both rows use z3 and cvc5 to block an impossible/free-lunch variant",
            "invariant_slots": "both rows expose local cycle-step invariant comparison slots",
        },
        "not_yet_claimed": [
            "no GStack nesting",
            "no Weyl/spinor/Hopf/torus/Clifford operator stack",
            "no final QIT runtime",
            "no bridge or admitted-axis claim",
        ],
    }


def triadic_information_rows(
    carnot: dict[str, Any],
    szilard: dict[str, Any],
    iching_64: dict[str, Any] | None,
    qit_companion: dict[str, Any] | None,
    qit_entropy: dict[str, Any] | None,
    clifford_capability: dict[str, Any] | None,
    weyl_topology: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    qit_summary = qit_companion.get("summary", {}) if qit_companion else {}
    entropy_summary = qit_entropy.get("summary", {}) if qit_entropy else {}
    iching_summary = iching_64.get("summary", {}) if iching_64 else {}
    gray_code_invariants = (
        sorted(iching_64.get("cycle_step_invariant_map", {}).get("invariants", {}))
        if iching_64
        else []
    )
    iching_cycle_invariant_rows = iching_64.get("cycle_invariant_rows", []) if iching_64 else []
    iching_pass = bool(iching_summary.get("all_pass"))
    return [
        {
            "row": "finite_carrier",
            "carnot": "finite qubit thermal working substance",
            "szilard": "finite two-qubit system-memory carrier",
            "qit_adjacent": "strict finite-carrier subset is partial",
            "status": "open",
            "evidence": {
                "carnot_pass": carnot["summary"]["all_pass"],
                "szilard_pass": szilard["summary"]["all_pass"],
                "qit_strict_subset_count": qit_summary.get("strict_qit_subset_count"),
                "missing_qit_strict_count": qit_summary.get("missing_strict_qit_subset_count"),
            },
            "boundary": "QIT carrier coverage is not complete because strict Szilard/QIT receipts are missing",
        },
        {
            "row": "operator_basis",
            "carnot": "thermal contact and adiabatic work operators",
            "szilard": "measurement, feedback, erasure operations",
            "qit_adjacent": "Clifford rotor/sandwich capability",
            "status": "supported_tool_micro_only" if clifford_capability and clifford_capability.get("summary", {}).get("all_pass") else "missing",
            "evidence": {
                "clifford_capability_all_pass": None if clifford_capability is None else clifford_capability.get("summary", {}).get("all_pass"),
                "clifford_scope": "tool_micro_clifford_capability_only",
            },
            "boundary": "Clifford capability does not yet couple the cycle loops to Weyl/spinor geometry",
        },
        {
            "row": "topology_variants",
            "carnot": "cycle/path graph and hypergraph leg grouping",
            "szilard": "protocol DAG/path and operation hyperedges",
            "qit_adjacent": "Weyl/holographic/symplectic topology-variant entropy stability",
            "status": "supported_topology_variant_only" if weyl_topology and weyl_topology.get("summary", {}).get("passed") == weyl_topology.get("summary", {}).get("total") else "missing",
            "evidence": {
                "weyl_topology_passed": None if weyl_topology is None else weyl_topology.get("summary", {}).get("passed"),
                "weyl_topology_total": None if weyl_topology is None else weyl_topology.get("summary", {}).get("total"),
            },
            "boundary": "Topology variants are not the GStack nesting order",
        },
        {
            "row": "entropy_readout_family",
            "carnot": "efficiency, COP, reservoir entropy and closure defects",
            "szilard": "record entropy, mutual information, free-energy gain, erasure cost",
            "qit_adjacent": "QIT entropy companion array is partial",
            "status": "open",
            "evidence": {
                "qit_entropy_all_pass": entropy_summary.get("all_pass"),
                "qit_entropy_present_rows": entropy_summary.get("strict_row_count"),
                "qit_entropy_missing_rows": entropy_summary.get("missing_strict_row_count"),
            },
            "boundary": "Entropy/readout coverage is not complete until missing QIT Szilard/readout receipts exist",
        },
        {
            "row": "local_invariant_schedule",
            "carnot": "local heat-work invariant comparison slots",
            "szilard": "local measurement-feedback invariant comparison slots",
            "qit_adjacent": "six-bit single-flip row supplies symbolic invariant comparison slots; active QIT axis doctrine remains open",
            "status": "sim_supported_symbolic_only" if iching_pass and len(gray_code_invariants) == 7 else "candidate_only",
            "evidence": {
                "shared_invariant_slots": sorted(set(carnot["cycle_step_invariant_map"]["invariants"]) & set(szilard["cycle_step_invariant_map"]["invariants"])),
                "gray_code_invariant_slots": gray_code_invariants,
                "iching_all_pass": iching_summary.get("all_pass"),
                "qit_admitted_axis_status": "blocked_until_QIT_grounded_and_negative_tested",
            },
            "boundary": "Local invariant labels are comparison slots, not admitted QIT axes",
        },
        {
            "row": "sixty_four_schedule",
            "carnot": "four heat-work legs times two traversals as a small cycle grammar",
            "szilard": "three operation protocol plus reverse bookkeeping as a small cycle grammar",
            "qit_adjacent": "six-bit Gray-code schedule with one-line flip operators and killed graveyard variants",
            "status": "sim_supported_symbolic_only" if iching_pass else "missing_symbolic_receipt",
            "evidence": {
                "iching_result": "six_bit_gray_code_single_flip_cycle_invariant_results.json" if iching_64 else None,
                "iching_all_pass": iching_summary.get("all_pass"),
                "state_count": iching_summary.get("state_count"),
                "invariant_count": iching_summary.get("invariant_count"),
                "cycle_invariant_row_count": len(iching_cycle_invariant_rows),
                "graveyard_variant_count": iching_summary.get("graveyard_variant_count"),
                "cycle_microsteps_claim": "not admitted here",
            },
            "boundary": "The 64-state schedule is a symbolic cycle-invariant sim, not I Ching proof or QIT runtime admission",
        },
    ]


def tier_correlations(carnot: dict[str, Any], szilard: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tier": 0,
            "name": "receipt_source",
            "carnot": "two_bath_heat_work_reversible_cycle_pair_results.json",
            "szilard": "measure_feedback_erasure_recovery_cycle_pair_results.json",
            "evidence": "both source rows pass and keep their own scope boundaries",
            "next_allowed": "compare receipts; do not promote either row",
        },
        {
            "tier": 1,
            "name": "micro_carrier",
            "carnot": "one finite qubit Gibbs carrier",
            "szilard": "finite two-qubit system-memory carrier",
            "evidence": "qutip/qiskit density witnesses pass on both rows",
            "next_allowed": "add more density-matrix operator probes",
        },
        {
            "tier": 2,
            "name": "graph_topology",
            "carnot": "closed four-state directed cycle plus leg hyperedges",
            "szilard": "directed protocol path plus operation hyperedges",
            "evidence": "rustworkx/PyG/XGI receipts pass on both rows",
            "next_allowed": "test graph nesting and stretchy topology variants",
        },
        {
            "tier": 3,
            "name": "operator_schedule",
            "carnot": "isothermal and adiabatic operators",
            "szilard": "measurement, feedback, erasure operators",
            "evidence": "ordered stage traces exist for both directions",
            "next_allowed": "cross-test schedule reorderings and negative variants",
        },
        {
            "tier": 4,
            "name": "entropy_gradient",
            "carnot": "heat/work reservoir entropy gradient",
            "szilard": "record entropy, mutual information, erasure cost gradient",
            "evidence": "opposite inductive/deductive loop bookkeeping passes",
            "next_allowed": "couple more entropy families to each geometry",
        },
        {
            "tier": 5,
            "name": "proof_fence",
            "carnot": "super-Carnot forbidden region",
            "szilard": "free Landauer erasure forbidden region",
            "evidence": "z3 and cvc5 fences pass on both rows",
            "next_allowed": "add proof-tool variants and contradiction/graveyard rows",
        },
        {
            "tier": 6,
            "name": "local_invariant_surface",
            "carnot": "local heat-work degrees of freedom",
            "szilard": "local measurement-feedback degrees of freedom",
            "evidence": "both rows expose seven comparison slots",
            "next_allowed": "compare against QIT axis candidates as priors only",
        },
        {
            "tier": 7,
            "name": "blocked_qit_runtime",
            "carnot": "not a QIT runtime",
            "szilard": "not a QIT runtime",
            "evidence": "no GStack, Weyl/spinor/Hopf/torus/Clifford stack receipt",
            "next_allowed": "micro-test those missing nonclassical operator stacks before promotion",
        },
    ]


def degree_of_freedom_comparison(carnot: dict[str, Any], szilard: dict[str, Any]) -> list[dict[str, Any]]:
    carnot_dofs = carnot["cycle_step_invariant_map"].get("degrees_of_freedom", [])
    szilard_dofs = szilard["cycle_step_invariant_map"].get("degrees_of_freedom", [])
    pairs = [
        ("temperature_ratio", "erasure_cost", "constraint intensity"),
        ("gap_ratio", "system_state", "carrier state spacing"),
        ("cycle_direction", "cycle_direction", "loop orientation"),
        ("bath_contact_branch", "memory_state", "branch/contact carrier"),
        ("leg_order", "feedback_order", "operator order"),
        ("heat_work_mode", "record_correlation", "entropy/work-information exchange"),
        ("stage_precedence", "protocol_precedence", "precedence constraint"),
        ("entropy_gradient_sign", "record_correlation", "gradient polarity"),
    ]
    return [
        {
            "carnot_degree": carnot_degree,
            "szilard_degree": szilard_degree,
            "relation": relation,
            "carnot_present": carnot_degree in carnot_dofs,
            "szilard_present": szilard_degree in szilard_dofs,
            "status": "candidate_pair" if carnot_degree in carnot_dofs and szilard_degree in szilard_dofs else "incomplete_pair",
        }
        for carnot_degree, szilard_degree, relation in pairs
    ]


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "cycle_invariant_rows": result["cycle_invariant_rows"],
        "tier_correlations": result["tier_correlations"],
        "degree_of_freedom_comparison": result["degree_of_freedom_comparison"],
        "triadic_information_rows": result["triadic_information_rows"],
        "qit_companion_summary": result["qit_companion_summary"],
        "qit_entropy_summary": result["qit_entropy_summary"],
        "iching_64_summary": result["iching_64_summary"],
        "iching_64_cycle_invariant_rows": result["iching_64_cycle_invariant_rows"],
        "iching_64_graveyard_variants": result["iching_64_graveyard_variants"],
        "information_theoretic_analogue_map": result["information_theoretic_analogue_map"],
        "graveyard_rows": result["graveyard_rows"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.CYCLE_INVARIANT_CORRELATION_DATA = " + json.dumps(build_visual_payload(result), indent=2) + ";\n"
    (VIS_DIR / "cycle-invariant-correlation-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    carnot = load_result("two_bath_heat_work_reversible_cycle_pair")
    szilard = load_result("measure_feedback_erasure_recovery_cycle_pair")
    qit_companion = load_optional_result("qit_engine_companion_array_results.json")
    qit_entropy = load_optional_result("qit_entropy_companion_array_results.json")
    iching_64 = load_optional_result("six_bit_gray_code_single_flip_cycle_invariant_results.json")
    clifford_capability = load_optional_result("clifford_capability_results.json")
    weyl_topology = load_optional_result("sim_weyl_holo_symplectic_topology_variants_results.json")

    shared_tools = shared_load_bearing_tools(carnot, szilard)
    shared_legos = sorted(set(carnot.get("lego_ids", [])) & set(szilard.get("lego_ids", [])))
    shared_invariants = sorted(
        set(carnot["cycle_step_invariant_map"]["invariants"])
        & set(szilard["cycle_step_invariant_map"]["invariants"])
    )
    evidence_flags = {
        "both_source_rows_pass": bool(carnot["summary"]["all_pass"] and szilard["summary"]["all_pass"]),
        "both_have_inductive_and_deductive_loops": bool(
            set(carnot["dual_stack"]) == {"inductive_heating_loop", "deductive_cooling_loop"}
            and set(szilard["dual_stack"]) == {"inductive_heating_loop", "deductive_cooling_loop"}
        ),
        "both_have_density_receipts": bool(
            pass_at(carnot, "boundary", "density_carriers")
            and pass_at(szilard, "boundary", "density_tools")
        ),
        "both_have_graph_receipts": bool(
            pass_at(carnot, "boundary", "graph_topology")
            and pass_at(szilard, "boundary", "graph_tools")
        ),
        "both_have_symbolic_receipts": bool(
            pass_at(carnot, "boundary", "symbolic_identities")
            and pass_at(szilard, "boundary", "symbolic_balance")
        ),
        "both_have_proof_fences": bool(
            pass_at(carnot, "negative", "super_carnot_blocked_by_z3")
            and pass_at(carnot, "negative", "super_carnot_blocked_by_cvc5_fixed_case")
            and pass_at(szilard, "negative", "landauer_free_erasure_blocked_by_z3")
            and pass_at(szilard, "negative", "landauer_free_erasure_blocked_by_cvc5")
        ),
        "shared_invariant_subset_nonempty": len(shared_invariants) >= 4,
        "nonidentity_invariant_maps_detected": bool(
            set(carnot["cycle_step_invariant_map"]["invariants"])
            != set(szilard["cycle_step_invariant_map"]["invariants"])
        ),
        "six_bit_symbolic_cycle_pass": bool(
            iching_64
            and iching_64.get("summary", {}).get("all_pass")
            and iching_64.get("summary", {}).get("state_count") == 64
            and iching_64.get("summary", {}).get("invariant_count") == 7
        ),
    }
    graveyard_rows = [
        {
            "claim": "heat-work and measurement-feedback cycles are identical",
            "status": "rejected",
            "reason": "the cycle-invariant layer finds shared slots and tool roles, not identity",
        },
        {
            "claim": "local invariant slots are admitted QIT axes",
            "status": "blocked",
            "reason": "the source rows label local invariants as candidate correlative mappings only",
        },
        {
            "claim": "graph topology is already a GStack",
            "status": "blocked",
            "reason": "current receipts show cycle/path/hypergraph carriers, not nested GStack constraint manifolds",
        },
    ]
    all_pass = all(evidence_flags.values()) and len(shared_tools) >= 10 and len(shared_legos) >= 3
    result = {
        "name": "heat_work_measure_feedback_cycle_invariant_correlation",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "allowed_claims": [
            "heat-work and measurement-feedback cycles dual-stack rows can be compared through a cycle-invariant surface",
            "both rows share tool, proof, density, graph, and local invariant-slot receipts",
            "shared structure is a candidate search prior, not identity or QIT admission",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "no GStack nesting receipt",
            "no nonclassical operator-stack coupling receipt",
            "no admitted QIT runtime",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "carnot": str(RESULT_DIR / "two_bath_heat_work_reversible_cycle_pair_results.json"),
            "szilard": str(RESULT_DIR / "measure_feedback_erasure_recovery_cycle_pair_results.json"),
            "iching_64": str(RESULT_DIR / "six_bit_gray_code_single_flip_cycle_invariant_results.json") if iching_64 else None,
        },
        "evidence_flags": evidence_flags,
        "cycle_invariant_rows": cycle_invariant_rows(carnot, szilard),
        "tier_correlations": tier_correlations(carnot, szilard),
        "degree_of_freedom_comparison": degree_of_freedom_comparison(carnot, szilard),
        "triadic_information_rows": triadic_information_rows(carnot, szilard, iching_64, qit_companion, qit_entropy, clifford_capability, weyl_topology),
        "qit_companion_summary": (
            qit_companion.get("summary", {})
            if qit_companion
            else {"all_pass": None, "missing": "qit_engine_companion_array_results.json"}
        ),
        "qit_entropy_summary": (
            qit_entropy.get("summary", {})
            if qit_entropy
            else {"all_pass": None, "missing": "qit_entropy_companion_array_results.json"}
        ),
        "iching_64_summary": (
            iching_64.get("summary", {})
            if iching_64
            else {"all_pass": None, "missing": "six_bit_gray_code_single_flip_cycle_invariant_results.json"}
        ),
        "iching_64_cycle_invariant_rows": iching_64.get("cycle_invariant_rows", []) if iching_64 else [],
        "iching_64_graveyard_variants": iching_64.get("graveyard_variants", []) if iching_64 else [],
        "information_theoretic_analogue_map": information_theoretic_analogue_map(carnot, szilard),
        "graveyard_rows": graveyard_rows,
        "summary": {
            "all_pass": all_pass,
            "shared_load_bearing_tool_count": len(shared_tools),
            "shared_load_bearing_tools": shared_tools,
            "shared_lego_count": len(shared_legos),
            "shared_legos": shared_legos,
            "shared_invariant_slots": shared_invariants,
            "cycle_invariant_row_count": 5 + len(shared_invariants),
            "tier_count": 8,
            "degree_pair_count": 8,
            "triadic_qit_row_count": 6,
            "qit_companion_all_pass": None if qit_companion is None else qit_companion.get("summary", {}).get("all_pass"),
            "qit_missing_strict_subset_count": None if qit_companion is None else qit_companion.get("summary", {}).get("missing_strict_qit_subset_count"),
            "qit_entropy_all_pass": None if qit_entropy is None else qit_entropy.get("summary", {}).get("all_pass"),
            "qit_entropy_missing_strict_row_count": None if qit_entropy is None else qit_entropy.get("summary", {}).get("missing_strict_row_count"),
            "iching_64_all_pass": None if iching_64 is None else iching_64.get("summary", {}).get("all_pass"),
            "iching_64_state_count": None if iching_64 is None else iching_64.get("summary", {}).get("state_count"),
            "iching_64_graveyard_variant_count": None if iching_64 is None else iching_64.get("summary", {}).get("graveyard_variant_count"),
            "clifford_capability_all_pass": None if clifford_capability is None else clifford_capability.get("summary", {}).get("all_pass"),
            "weyl_topology_passed": None if weyl_topology is None else weyl_topology.get("summary", {}).get("passed"),
            "graveyard_row_count": len(graveyard_rows),
            "visual_payload": "visualizer/cycle-invariant-correlation-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "heat_work_measure_feedback_cycle_invariant_correlation_results.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
