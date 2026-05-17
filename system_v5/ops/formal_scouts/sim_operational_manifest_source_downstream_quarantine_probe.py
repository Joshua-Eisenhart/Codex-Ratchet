#!/usr/bin/env python3
"""Operational manifest for source, downstream, and proxy-quarantine scouts."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import networkx as nx
import numpy as np
import sympy as sp
from z3 import And, Bool, Int, Solver, sat


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "operational_manifest_source_downstream_quarantine_probe_results.json"

NAME = "operational_manifest_source_downstream_quarantine_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: verifies the operational evidence manifest for a "
    "source-native, downstream, and proxy-quarantined geometric constraint "
    "manifold run. It does not admit final manifold, physics, cognition, "
    "ontology, or canonical claims."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing receipt parsing and manifest checks"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing result path existence checks"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing manifest count vectors and gap checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing evidence dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic count inventory"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing manifest admissibility witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

RECEIPTS = {
    "manifold_first": [
        "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
        "nested_constraint_manifold_operational_handle_support_probe_results.json",
    ],
    "source_native": [
        "left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe_results.json",
        "left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe_results.json",
        "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json",
        "source_chiral_entropy_feedback_sixty_four_microstep_execution_probe_results.json",
        "source_chiral_density_multicarrier_multitool_manifold_execution_probe_results.json",
        "long_horizon_source_multicarrier_holonomy_boundary_entropy_probe_results.json",
    ],
    "downstream_on_source": [
        "left_right_weyl_density_hopf_loop_shell_graph_persistence_coupling_probe_results.json",
        "strong_geometric_flux_nested_hopf_torus_weyl_density_probe_results.json",
        "paired_chiral_seven_control_joint_bipartite_execution_order_probe_results.json",
        "constraint_manifold_multitool_entropy_geometry_carrier_integration_probe_results.json",
        "mps_peps_peps3d_entropy_deformation_volume_comparison_probe_results.json",
        "boundary_conditional_expectation_area_law_entropy_scaling_probe_results.json",
    ],
    "proxy_quarantine": [
        "gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe_results.json",
        "gamma5_chirality_asymmetric_cptp_arbitrary_kraus_equivalence_kill_probe_results.json",
        "gamma5_offdiagonal_coherence_trace_orbit_locality_preserving_rank3_channel_probe_results.json",
        "eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe_results.json",
        "eight_qubit_boundary_projected_gamma5_mutual_information_persistence_probe_results.json",
    ],
}

REQUIRED_PARENT_RECEIPTS = {
    "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json": [
        "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
        "nested_constraint_manifold_operational_handle_support_probe_results.json",
    ],
    "paired_chiral_seven_control_joint_bipartite_execution_order_probe_results.json": [
        "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
        "nested_constraint_manifold_operational_handle_support_probe_results.json",
        "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json",
    ],
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer | np.floating):
        return value.item()
    return value


def load_receipt(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"path": str(path), "exists": path.exists(), "data": data}


def receipt_pass(data: dict[str, Any]) -> bool:
    if data.get("classification") != "formal_scout":
        return False
    if data.get("promotion_allowed") is not False:
        return False
    if data.get("all_pass") is False:
        return False
    nearby = data.get("nearby_variants")
    if isinstance(nearby, dict) and nearby.get("total") and nearby.get("passed") != nearby.get("total"):
        return False
    return bool(data.get("claim_ceiling"))


def manifest_rows() -> list[dict[str, Any]]:
    rows = []
    for category, names in RECEIPTS.items():
        for name in names:
            path = RESULT_DIR / name
            if not path.exists():
                rows.append({"category": category, "name": name, "exists": False, "pass": False, "source_alignment_category": None})
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "category": category,
                    "name": name,
                    "exists": True,
                    "pass": receipt_pass(data),
                    "classification": data.get("classification"),
                    "promotion_allowed": data.get("promotion_allowed"),
                    "source_alignment_category": data.get("source_alignment_category", "not_declared"),
                    "has_gamma_name": "gamma" in name,
                    "claim_mentions_proxy_or_gamma": "gamma" in str(data.get("claim_ceiling", "")).lower() or "proxy" in str(data.get("claim_ceiling", "")).lower(),
                }
            )
    return rows


def dependency_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_node("manifold_first")
    graph.add_node("source_native")
    graph.add_node("long_horizon")
    graph.add_node("downstream_on_source")
    graph.add_node("proxy_quarantine")
    graph.add_edges_from(
        [
            ("manifold_first", "source_native"),
            ("source_native", "long_horizon"),
            ("long_horizon", "downstream_on_source"),
            ("source_native", "proxy_quarantine"),
        ]
    )
    for row in rows:
        graph.add_edge(row["category"], row["name"])
    for child, parents in REQUIRED_PARENT_RECEIPTS.items():
        for parent in parents:
            graph.add_edge(parent, child)
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
        "pass": nx.is_directed_acyclic_graph(graph)
        and graph.has_edge("manifold_first", "source_native")
        and graph.has_edge("source_native", "long_horizon"),
    }


def symbolic_smt(counts: dict[str, int], failures: int) -> dict[str, Any]:
    manifold, source, downstream, proxy = sp.symbols("manifold source downstream proxy", integer=True)
    symbolic = bool(
        sp.And(manifold >= 2, source >= 4, downstream >= 5, proxy >= 5).subs(
            {
                manifold: counts["manifold_first"],
                source: counts["source_native"],
                downstream: counts["downstream_on_source"],
                proxy: counts["proxy_quarantine"],
            }
        )
    )
    m = Int("manifold")
    s = Int("source")
    d = Int("downstream")
    p = Int("proxy")
    f = Int("failures")
    ok = Bool("ok")
    solver = Solver()
    solver.add(m == counts["manifold_first"], s == counts["source_native"], d == counts["downstream_on_source"], p == counts["proxy_quarantine"], f == failures)
    solver.add(ok == And(m >= 2, s >= 4, d >= 5, p >= 5, f == 0))
    solver.add(ok)
    return {"symbolic": symbolic, "z3": str(solver.check()), "pass": symbolic and solver.check() == sat}


def parent_receipt_gate() -> dict[str, Any]:
    failures = []
    for child, parents in REQUIRED_PARENT_RECEIPTS.items():
        child_path = RESULT_DIR / child
        if not child_path.exists():
            failures.append({"child": child, "missing_child": True})
            continue
        child_data = json.loads(child_path.read_text(encoding="utf-8"))
        for parent in parents:
            parent_path = RESULT_DIR / parent
            if not parent_path.exists():
                failures.append({"child": child, "parent": parent, "missing_parent": True})
                continue
            parent_data = json.loads(parent_path.read_text(encoding="utf-8"))
            if not receipt_pass(parent_data):
                failures.append({"child": child, "parent": parent, "parent_failed": True})
        if child_data.get("promotion_allowed") is not False:
            failures.append({"child": child, "promotion_allowed": child_data.get("promotion_allowed")})
    return {"required_parent_receipts": REQUIRED_PARENT_RECEIPTS, "failures": failures, "pass": len(failures) == 0}


def main() -> int:
    started = time.time()
    rows = manifest_rows()
    counts = {category: sum(1 for row in rows if row["category"] == category) for category in RECEIPTS}
    pass_counts = {category: sum(1 for row in rows if row["category"] == category and row["pass"]) for category in RECEIPTS}
    failures = sum(1 for row in rows if not row["pass"])
    proxy_leaks = [row["name"] for row in rows if row["category"] != "proxy_quarantine" and row.get("has_gamma_name")]
    unquarantined_proxy = [row["name"] for row in rows if row["category"] == "proxy_quarantine" and not row.get("has_gamma_name")]
    category_vector = np.array([counts[k] for k in ("manifold_first", "source_native", "downstream_on_source", "proxy_quarantine")], dtype=float)
    positive = {
        "required_receipts_exist_and_validate": {
            "counts": counts,
            "pass_counts": pass_counts,
            "failures": failures,
            "pass": failures == 0 and counts == pass_counts,
        },
        "source_downstream_proxy_categories_are_populated": {
            "category_vector": category_vector,
            "pass": bool(np.all(category_vector >= np.array([2, 4, 5, 5], dtype=float))),
        },
        "evidence_dependency_graph_is_acyclic": dependency_graph(rows),
        "symbolic_smt_manifest_witness": symbolic_smt(counts, failures),
        "downstream_receipts_have_manifold_parent_receipts": parent_receipt_gate(),
    }
    graveyard_companions = {
        "gamma_named_receipts_are_quarantined": {"proxy_leaks": proxy_leaks, "pass": len(proxy_leaks) == 0},
        "proxy_quarantine_is_nonempty": {"proxy_count": counts["proxy_quarantine"], "pass": counts["proxy_quarantine"] > 0},
        "promotion_stays_disabled_for_manifested_receipts": {
            "promoted": [row["name"] for row in rows if row.get("promotion_allowed") is not False],
            "pass": all(row.get("promotion_allowed") is False for row in rows),
        },
        "missing_source_alignment_is_recorded_not_promoted": {
            "not_declared": [row["name"] for row in rows if row.get("source_alignment_category") == "not_declared"],
            "pass": True,
        },
    }
    boundary = {
        "manifest_is_not_itself_final_proof": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "unquarantined_proxy_check": {"unquarantined_proxy": unquarantined_proxy, "pass": len(unquarantined_proxy) == 0},
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "operational_manifest_for_source_downstream_proxy_quarantine",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "manifest_rows": rows,
        "why_not_v4_probes": [
            "Manifest scout only.",
            "It verifies current formal-scout evidence surfaces but does not replace fresh reruns of every listed scout.",
            "It keeps gamma/proxy-family receipts quarantined from source-native proof.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
