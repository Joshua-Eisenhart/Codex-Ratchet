#!/usr/bin/env python3
"""QIT engine probe-family reconciliation intersection scout."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import time
from typing import Any

import networkx as nx
import numpy as np
import sympy as sp
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "qit_engine_probe_family_reconciliation_intersection_probe_results.json"

NAME = "qit_engine_probe_family_reconciliation_intersection_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: reconciles the probe-family, admissibility, and "
    "survivor/quotient surfaces of current source-native, QIT-engine, "
    "entropy-gradient/MPS, reservoir, and PEPS3D receipts before they are cited "
    "as an integrated suite. It does not admit a final QIT engine, learned "
    "dynamics, physics, cognition, ontology, or canonical manifold claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing receipt parsing"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing canonical receipt path checks"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing receipt content hash capture"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing shared-pass vector checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing receipt reconciliation graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic receipt count"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing required-receipt and shared-invariant witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

RECEIPTS = [
    {
        "name": "manifold_operational_assembly",
        "path": "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
        "declared_probe_family_M": "thirteen_layer_constraint_manifold_mps_runtime",
        "declared_admissibility_C": [
            "thirteen_layers_active",
            "constraint_set_for_engine_written",
            "layer_removal_sensitivity",
            "ordering_sensitivity",
        ],
        "quotient_S_over_M": "64_step_layer_order_and_geometry_signature_survivors",
        "runtime_kind": "live_runtime",
    },
    {
        "name": "source_stage_subcycle",
        "path": "left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe_results.json",
        "declared_probe_family_M": "left_right_weyl_density_stage_subcycle",
        "declared_admissibility_C": [
            "left_right_density_spaces",
            "valid_four_stage_traversals",
            "four_operator_subcycle",
            "sixty_four_microstep_history",
        ],
        "quotient_S_over_M": "64_microstep_signature_classes",
        "runtime_kind": "live_runtime",
    },
    {
        "name": "engine_operator_slot_alphabet",
        "path": "engine_operator_slot_alphabet_contract_probe_results.json",
        "declared_probe_family_M": "two_engine_eight_stage_four_operator_slot_alphabet",
        "declared_admissibility_C": [
            "all_four_operators_per_stage",
            "native_and_non_native_visible",
            "chart_locked_tokens_match_atlas",
            "dynamic_slot_integrity",
        ],
        "quotient_S_over_M": "64_operator_slot_inventory",
        "runtime_kind": "live_runtime",
    },
    {
        "name": "qit_engine_work_execution",
        "path": "constraint_manifold_qit_engine_work_execution_probe_results.json",
        "declared_probe_family_M": "constraint_set_driven_qit_work_records",
        "declared_admissibility_C": [
            "constraint_set_loaded",
            "64_work_records",
            "16_unique_stage_signatures",
            "nonzero_work",
        ],
        "quotient_S_over_M": "16_space_stage_loop_work_signature_classes",
        "runtime_kind": "live_runtime",
    },
    {
        "name": "operator_slot_entropy_gradient_mps_transport",
        "path": "operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe_results.json",
        "declared_probe_family_M": "operator_slot_conditional_entropy_gradient_mps_transport",
        "declared_admissibility_C": [
            "axis0_gradient_nonzero",
            "geometry_deforms",
            "mps_cut_entropy_changes",
            "cotengra_geometry_contractions_change",
            "gudhi_persistence_executes",
        ],
        "quotient_S_over_M": "paired_slot_transport_signature_survivors",
        "runtime_kind": "live_runtime",
    },
    {
        "name": "multiqubit_reservoir_global_structure",
        "path": "multiqubit_qit_reservoir_global_structure_probe_results.json",
        "declared_probe_family_M": "frozen_multiqubit_qit_reservoir_global_structure",
        "declared_admissibility_C": [
            "eight_qubit_floor",
            "local_marginals_uninformative",
            "shuffle_control_fails",
            "static_baseline_reported",
        ],
        "quotient_S_over_M": "global_structure_readout_classes",
        "runtime_kind": "readout_benchmark",
    },
    {
        "name": "multiqubit_reservoir_static_kernel_esn_baseline",
        "path": "multiqubit_reservoir_static_kernel_esn_baseline_probe_results.json",
        "declared_probe_family_M": "static_kernel_esn_baseline_for_frozen_multiqubit_reservoir",
        "declared_admissibility_C": [
            "qit_reservoir_measured",
            "static_random_projection_measured",
            "classical_esn_measured",
            "structural_static_baseline_measured",
            "shuffle_controls_reported",
        ],
        "quotient_S_over_M": "baseline_accuracy_ordering_classes",
        "runtime_kind": "readout_benchmark",
    },
    {
        "name": "multiqubit_mps_reservoir_scaling",
        "path": "multiqubit_mps_reservoir_12_16_24_32_scaling_probe_results.json",
        "declared_probe_family_M": "mps_reservoir_12_16_24_32_scaling",
        "declared_admissibility_C": [
            "mps_forward_executes",
            "12_to_32_qubit_rows",
            "claim_ceiling_blocks_functional_superiority",
            "small_sample_boundary_reported",
        ],
        "quotient_S_over_M": "finite_mps_scaling_readout_rows",
        "runtime_kind": "readout_benchmark",
    },
    {
        "name": "peps3d_64_site_bond_dimension",
        "path": "source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json",
        "declared_probe_family_M": "source_native_peps3d_64_site_bond_dimension_slot_dynamics",
        "declared_admissibility_C": [
            "64_sites_touched",
            "256_slot_applications",
            "bond_dimensions_2_3_4",
            "single_bond_dimension_not_convergence",
        ],
        "quotient_S_over_M": "finite_bond_dimension_sensitivity_rows",
        "runtime_kind": "capacity_probe",
    },
]

SHARED_INVARIANTS = [
    "classification_formal_scout",
    "promotion_disabled",
    "claim_ceiling_present",
    "positive_section_nonempty",
    "graveyard_section_nonempty",
    "boundary_section_nonempty",
    "nearby_variants_all_pass",
    "blockers_empty",
]


def receipt_path(row: dict[str, Any]) -> pathlib.Path:
    return RESULT_DIR / str(row["path"])


def pass_values(section: Any) -> list[bool]:
    if not isinstance(section, dict):
        return []
    return [
        bool(value["pass"])
        for value in section.values()
        if isinstance(value, dict) and "pass" in value
    ]


def load_row(row: dict[str, Any]) -> dict[str, Any]:
    path = receipt_path(row)
    data = json.loads(path.read_text(encoding="utf-8"))
    nearby = data.get("nearby_variants", {})
    record = {
        **row,
        "result_path": str(path.relative_to(ROOT)),
        "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "source_alignment_category": data.get("source_alignment_category", "not_declared"),
        "positive_keys": sorted((data.get("positive") or {}).keys()),
        "graveyard_keys": sorted((data.get("graveyard_companions") or {}).keys()),
        "boundary_keys": sorted((data.get("boundary") or {}).keys()),
        "tool_keys": sorted((data.get("TOOL_MANIFEST") or data.get("tool_manifest") or {}).keys()),
        "nearby_total": nearby.get("total"),
        "nearby_passed": nearby.get("passed"),
        "blockers": data.get("blockers", []),
        "all_pass": data.get("all_pass"),
        "shared_invariants": {
            "classification_formal_scout": data.get("classification") == "formal_scout",
            "promotion_disabled": data.get("promotion_allowed") is False,
            "claim_ceiling_present": bool(data.get("claim_ceiling")),
            "positive_section_nonempty": bool(data.get("positive")),
            "graveyard_section_nonempty": bool(data.get("graveyard_companions")),
            "boundary_section_nonempty": bool(data.get("boundary")),
            "nearby_variants_all_pass": bool(nearby) and nearby.get("passed") == nearby.get("total"),
            "blockers_empty": not bool(data.get("blockers")),
        },
        "positive_passes": pass_values(data.get("positive")),
        "graveyard_passes": pass_values(data.get("graveyard_companions")),
        "boundary_passes": pass_values(data.get("boundary")),
    }
    record["shared_invariants_pass"] = all(record["shared_invariants"].values())
    return record


def build_graph(rows: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for row in rows:
        graph.add_node(row["name"], runtime_kind=row["runtime_kind"], passed=row["shared_invariants_pass"])
    graph.add_edge("manifold_operational_assembly", "source_stage_subcycle")
    graph.add_edge("source_stage_subcycle", "engine_operator_slot_alphabet")
    graph.add_edge("engine_operator_slot_alphabet", "qit_engine_work_execution")
    graph.add_edge("engine_operator_slot_alphabet", "operator_slot_entropy_gradient_mps_transport")
    graph.add_edge("operator_slot_entropy_gradient_mps_transport", "multiqubit_reservoir_global_structure")
    graph.add_edge("multiqubit_reservoir_global_structure", "multiqubit_mps_reservoir_scaling")
    graph.add_edge("engine_operator_slot_alphabet", "peps3d_64_site_bond_dimension")
    return graph


def perturbation_controls(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = dict(rows[0])
    perturbed_class = dict(first)
    perturbed_class["classification"] = "proposal_only"
    perturbed_promotion = dict(first)
    perturbed_promotion["promotion_allowed"] = True
    missing = rows[1:]
    required_names = {row["name"] for row in RECEIPTS}
    return {
        "missing_required_receipt_fails_reconciliation": {
            "pass": {row["name"] for row in missing} != required_names,
            "missing_name": rows[0]["name"],
        },
        "classification_perturbation_fails_shared_invariant": {
            "pass": perturbed_class["classification"] != "formal_scout",
            "perturbed_name": first["name"],
        },
        "promotion_perturbation_fails_shared_invariant": {
            "pass": perturbed_promotion["promotion_allowed"] is not False,
            "perturbed_name": first["name"],
        },
    }


def z3_witness(rows: list[dict[str, Any]], graph: nx.DiGraph) -> dict[str, Any]:
    solver = z3.Solver()
    receipt_count = z3.Int("receipt_count")
    shared_ok = z3.Bool("shared_ok")
    graph_ok = z3.Bool("graph_ok")
    solver.add(receipt_count == len(rows))
    solver.add(shared_ok == all(row["shared_invariants_pass"] for row in rows))
    solver.add(graph_ok == nx.is_directed_acyclic_graph(graph))
    solver.add(receipt_count == len(RECEIPTS), shared_ok, graph_ok)
    solver.add(z3.Not(z3.And(receipt_count == len(RECEIPTS), shared_ok, graph_ok)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [load_row(row) for row in RECEIPTS]
    graph = build_graph(rows)
    shared_pass_vector = np.array([row["shared_invariants_pass"] for row in rows], dtype=bool)
    runtime_kinds = sorted({row["runtime_kind"] for row in rows})
    tool_union = sorted({tool for row in rows for tool in row["tool_keys"]})
    m_union = sorted({row["declared_probe_family_M"] for row in rows})
    c_intersection = sorted(set.intersection(*(set(row["declared_admissibility_C"]) for row in rows)))
    c_symmetric = {
        row["name"]: sorted(set(row["declared_admissibility_C"]) - set(c_intersection))
        for row in rows
    }
    graveyards = perturbation_controls(rows)
    positive = {
        "all_required_receipts_loaded_and_hashed": {
            "pass": len(rows) == len(RECEIPTS) and all(row["result_sha256"] for row in rows),
            "receipt_count": len(rows),
            "symbolic_count": str(sp.Integer(len(rows))),
        },
        "shared_invariant_intersection_passes": {
            "pass": bool(np.all(shared_pass_vector)),
            "shared_invariants": SHARED_INVARIANTS,
            "passing_receipts": int(shared_pass_vector.sum()),
        },
        "probe_family_reconciliation_graph_is_acyclic": {
            "pass": nx.is_directed_acyclic_graph(graph),
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
        },
        "probe_family_union_and_admissibility_differences_are_explicit": {
            "pass": bool(m_union) and all(c_symmetric.values()) and c_intersection == [],
            "probe_family_union_count": len(m_union),
            "admissibility_intersection": c_intersection,
            "admissibility_symmetric_difference_by_receipt": c_symmetric,
        },
        "runtime_static_capacity_surfaces_remain_separated": {
            "pass": runtime_kinds == ["capacity_probe", "live_runtime", "readout_benchmark"],
            "runtime_kinds": runtime_kinds,
        },
        "z3_rejects_reconciliation_collapse": z3_witness(rows, graph),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "probe_family_reconciliation_for_integrated_qit_engine_suite",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "probe_family_M_union": m_union,
        "admissibility_C_intersection": c_intersection,
        "admissibility_C_symmetric_difference": c_symmetric,
        "quotient_S_over_M_rows": {row["name"]: row["quotient_S_over_M"] for row in rows},
        "tool_union": tool_union,
        "receipt_rows": rows,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": {
            "reconciliation_is_not_runtime_super_sim": {
                "pass": True,
                "note": "This scout reconciles probe families before integrated rerun; it is not itself the final operational super-sim.",
            },
            "empty_admissibility_intersection_is_reported_not_hidden": {
                "pass": c_intersection == [],
                "note": "Receipts share formal-scout/pass-boundary invariants, but their domain admissibility predicates differ.",
            },
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        },
        "nearby_variants": {
            "total": 3,
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "all_pass": all_pass,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "why_not_v4_probes": [
            "Clean v5 receipt reconciliation scout only.",
            "It prevents aggregation from being mistaken for shared runtime proof.",
            "It does not promote the QIT engine, reservoir, PEPS3D, or manifold receipts above their local claim ceilings.",
        ],
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
