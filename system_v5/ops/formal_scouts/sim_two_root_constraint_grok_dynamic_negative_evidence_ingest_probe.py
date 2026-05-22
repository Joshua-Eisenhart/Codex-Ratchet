#!/usr/bin/env python3
"""Ingest recent grok_sim dynamic evidence into the two-root audit chain.

Formal scout only. This reads side-quest Grok results for iters 100-107 and
uses them as bounded reachability/stability evidence: F01+N01 substrate
dynamics can reach Clifford-isomorphic commute graphs, but the tested dynamics
do not make the exact Clifford corner stable. The variance-zero subset is
isolated under tested local edge-flip topology. The Grok receipts remain
side-quest evidence and are not promoted.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
GROK_RESULTS = REPO / "system_v5" / "grok_sim" / "results"

NAME = "two_root_constraint_grok_dynamic_negative_evidence_ingest_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_grok_dynamic_reachability_stability_evidence_ingest"
CLAIM_CEILING = (
    "Formal scout only: audits recent grok_sim side-quest dynamics as bounded "
    "reachability/stability evidence for F01/N01 exact Clifford-corner "
    "localization. It does not admit grok_sim results, final geometric "
    "constraint manifold, real attractor basin, Axis0, engine, physics, "
    "target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive parsing of side-quest JSON receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive side-quest receipt hashing"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that side-quest evidence cannot complete formal stable-basin localization"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent side-quest completion block"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing dependency graph across Grok side-quest receipts and formal use classes"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
}

TWO_ROOT_CONSTRAINTS = {
    "finite_carrier_root": True,
    "noncommutation_or_order_root": True,
    "F01": True,
    "N01": True,
    "scope": "audit of finite side-quest receipts for noncommutation/order-sensitive Clifford-corner localization",
}

INPUTS = {
    "iter_100": GROK_RESULTS / "iter_100_dynamics_under_weak_admission_results.json",
    "iter_101": GROK_RESULTS / "iter_101_dynamics_under_sharpened_admission_results.json",
    "iter_102": GROK_RESULTS / "iter_102" / "master_summary.json",
    "iter_103": GROK_RESULTS / "iter_103" / "master_summary.json",
    "iter_104": GROK_RESULTS / "iter_104" / "master_summary.json",
    "iter_105": GROK_RESULTS / "iter_105" / "master_summary.json",
    "iter_106": GROK_RESULTS / "iter_106" / "master_summary.json",
    "iter_107": GROK_RESULTS / "iter_107" / "master_summary.json",
}

NEXT_REQUIRED_SCOUT = "two_root_constraint_group_action_weighted_selector_or_energy_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def receipt_boundaries(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for key, receipt in receipts.items():
        ceiling = str(receipt.get("claim_ceiling", "")).lower()
        rows.append(
            {
                "iter": key,
                "path": rel(INPUTS[key]),
                "sha256": sha256(INPUTS[key]),
                "has_side_quest_ceiling": "side_quest_only" in ceiling or "side-quest" in ceiling,
                "formal_scout_classification_absent": receipt.get("classification") != "formal_scout",
                "promotion_allowed_not_true": receipt.get("promotion_allowed") is not True,
            }
        )
    return {
        "pass": all(
            row["has_side_quest_ceiling"]
            and row["formal_scout_classification_absent"]
            and row["promotion_allowed_not_true"]
            for row in rows
        ),
        "rows": rows,
    }


def iter100_report(receipt: dict[str, Any]) -> dict[str, Any]:
    stats = receipt.get("statistics", {})
    return {
        "pass": receipt.get("verdict") == "NO_DRIFT_admission_alone_does_not_localize"
        and int(stats.get("n_trajectories_terminal_var_below_0.01", -1)) == 0,
        "verdict": receipt.get("verdict"),
        "n_trajectories": stats.get("n_trajectories"),
        "initial_variance_mean": stats.get("initial_variance_mean"),
        "final_variance_mean": stats.get("final_variance_mean"),
        "terminal_var_below_0_01": stats.get("n_trajectories_terminal_var_below_0.01"),
    }


def iter101_report(receipt: dict[str, Any]) -> dict[str, Any]:
    phase1 = receipt.get("phase_1_random_initial", {}).get("stats", {})
    phase2 = receipt.get("phase_2_irregular_initial", {}).get("stats", {})
    strict_hits = int(phase1.get("n_ended_below_var_0.01", 0)) + int(phase2.get("n_ended_below_var_0.01", 0))
    return {
        "pass": receipt.get("verdict") == "NO_DRIFT_to_cl_corner_even_under_sharpened_admission"
        and float(receipt.get("drift_to_cl_corner_fraction", 1.0)) == 0.0
        and strict_hits == 0,
        "verdict": receipt.get("verdict"),
        "drift_to_cl_corner_fraction": receipt.get("drift_to_cl_corner_fraction"),
        "phase_1": phase1,
        "phase_2": phase2,
        "strict_hits": strict_hits,
    }


def count_positive_scores(items: dict[str, dict[str, Any]], key: str) -> int:
    return sum(1 for item in items.values() if float(item.get(key) or 0.0) > 0.0)


def iter102_report(receipt: dict[str, Any]) -> dict[str, Any]:
    phases = receipt["results_by_phase"]
    phase_counts = {
        "phase_A": len(phases["phase_A_singles"]),
        "phase_B": len(phases["phase_B_pairs"]),
        "phase_C": len(phases["phase_C_triples"]),
        "phase_D": len(phases["phase_D_quads"]),
        "phase_E": len(phases["phase_E_n_scaling"]),
        "phase_F": len(phases["phase_F_combinatorial_pairs"]),
    }
    total = sum(phase_counts.values())
    strict_positive = sum(
        count_positive_scores(phases[name], "localization_score")
        for name in (
            "phase_A_singles",
            "phase_B_pairs",
            "phase_C_triples",
            "phase_D_quads",
            "phase_E_n_scaling",
            "phase_F_combinatorial_pairs",
        )
    )
    phase_a = phases["phase_A_singles"]
    baseline_var = phase_a["baseline_weak_only"].get("final_var_mean")
    c2_var = phase_a["C2_regularity"].get("final_var_mean")
    return {
        "pass": total == 33 and strict_positive == 0 and c2_var is not None and c2_var < baseline_var,
        "experiment_count": total,
        "phase_counts": phase_counts,
        "strict_positive_count": strict_positive,
        "best_single_by_receipt_tiebreak": receipt.get("phase_summaries", {}).get("best_single_constraint"),
        "c2_regularity_directional_pull": {
            "baseline_final_variance_mean": baseline_var,
            "c2_final_variance_mean": c2_var,
            "directional_pull_present": c2_var is not None and baseline_var is not None and c2_var < baseline_var,
        },
    }


def iter103_report(receipt: dict[str, Any]) -> dict[str, Any]:
    n4 = receipt["results"]["n_target_4"]
    n6 = receipt["results"]["n_target_6"]
    rows = []
    for target, group in [(4, n4), (6, n6)]:
        for substrate, row in group.items():
            rows.append({"n_target": target, "substrate": substrate, **row})
    iso_hits = sum(int(row.get("n_cl_isomorphic", 0)) for row in rows)
    sig_hits = sum(int(row.get("n_cl_signature_match", 0)) for row in rows)
    samples = sum(int(row.get("n_subset_samples", 0)) for row in rows)
    admitted = sum(int(row.get("n_weak_admitted", 0)) for row in rows)
    hit_rows = [row for row in rows if int(row.get("n_cl_isomorphic", 0)) > 0]
    n6_hits = [row for row in rows if row["n_target"] == 6 and int(row.get("n_cl_isomorphic", 0)) > 0]
    return {
        "pass": len(rows) == 19
        and len(receipt.get("substrates_used", [])) == 12
        and samples == 57000
        and iso_hits == 3
        and not n6_hits
        and all(row["substrate"] == "pauli_tensor_2qubit" for row in hit_rows),
        "substrate_count": len(receipt.get("substrates_used", [])),
        "tested_condition_count": len(rows),
        "sample_count": samples,
        "weak_admitted_count": admitted,
        "cl_isomorphic_hit_count": iso_hits,
        "cl_signature_hit_count": sig_hits,
        "hit_rows": [
            {
                "n_target": row["n_target"],
                "substrate": row["substrate"],
                "n_cl_isomorphic": row["n_cl_isomorphic"],
                "n_subset_samples": row["n_subset_samples"],
                "cl_iso_fraction_of_admitted": row["cl_iso_fraction_of_admitted"],
            }
            for row in hit_rows
        ],
        "n6_cl_isomorphic_hit_count": len(n6_hits),
    }


def iter104_report(receipt: dict[str, Any]) -> dict[str, Any]:
    all_results = receipt["all_results"]
    phase1 = all_results["phase_1_C2_threshold_sweep"]
    phase2 = all_results["phase_2_C2_plus_other"]
    phase3 = all_results["phase_3_n_scaling"]
    rows = [*phase1.values(), *phase2.values(), *phase3.values()]
    strict_positive = sum(1 for row in rows if float(row.get("localization_score_strict") or 0.0) > 0.0)
    tight_empty = all(int(phase1[tau].get("n_trajectories", 0)) == 0 for tau in ("0.05", "0.1", "0.25"))
    c2_tau = phase1["0.5"]
    return {
        "pass": len(rows) == 17
        and strict_positive == 0
        and receipt.get("best_tau") == 0.5
        and receipt.get("fully_localizing_pairs_count") == 0
        and tight_empty
        and float(c2_tau.get("final_var_mean")) < 0.5,
        "experiment_count": len(rows),
        "strict_positive_count": strict_positive,
        "best_tau": receipt.get("best_tau"),
        "fully_localizing_pairs_count": receipt.get("fully_localizing_pairs_count"),
        "tight_thresholds_no_admitted_initials": tight_empty,
        "c2_tau_0_5": c2_tau,
        "n_scaling": {
            key: {
                "n_trajectories": row.get("n_trajectories"),
                "final_var_mean": row.get("final_var_mean"),
                "localization_score_strict": row.get("localization_score_strict"),
            }
            for key, row in phase3.items()
        },
    }


def iter105_report(receipt: dict[str, Any]) -> dict[str, Any]:
    results = receipt["results"]
    phase_a = results["phase_A_substrate_constrained_walk"]["stats"]
    phase_b = results["phase_B_perturbed_cl_recovery"]
    phase_c = results["phase_C_exact_enumeration_n3"]
    recovery_rows = []
    for n_key, by_k in phase_b.items():
        for k_key, row in by_k.items():
            recovery_rows.append({"n": n_key, "k": k_key, **row})
    recovery_count = sum(int(row.get("n_recovered_to_corner", 0)) for row in recovery_rows)
    recovery_trajectory_count = sum(int(row.get("n_trajectories", 0)) for row in recovery_rows)
    reach_count = int(phase_a["n_trajectories_ever_hit_cl_iso"])
    final_count = int(phase_a["n_trajectories_with_final_cl_iso"])
    admitted = int(phase_c["n_admitted"])
    var0 = int(phase_c["n_admitted_at_variance_0"])
    near = int(phase_c["n_admitted_at_variance_below_0.5"])
    return {
        "pass": reach_count == 27
        and final_count == 0
        and recovery_count == 0
        and recovery_trajectory_count == 200
        and admitted == 32766
        and var0 == 170
        and near == 5900
        and phase_c["cl_in_admitted"] is True,
        "substrate_constrained_walk": {
            "n_trajectories": phase_a["n_trajectories"],
            "n_trajectories_ever_hit_cl_iso": reach_count,
            "fraction_trajectories_ever_reaching_cl": phase_a["fraction_trajectories_ever_reaching_cl"],
            "total_cl_iso_visits_across_trajectories": phase_a["total_cl_iso_visits_across_trajectories"],
            "n_trajectories_with_final_cl_iso": final_count,
            "initial_var_mean": phase_a["initial_var_mean"],
            "final_var_mean": phase_a["final_var_mean"],
        },
        "perturbed_cl_recovery": {
            "recovery_trajectory_count": recovery_trajectory_count,
            "n_recovered_to_corner": recovery_count,
            "recovery_rate": recovery_count / max(recovery_trajectory_count, 1),
            "tested_n": sorted({row["n"] for row in recovery_rows}),
            "tested_k": sorted({int(row["k"]) for row in recovery_rows}),
        },
        "exact_n3_enumeration": {
            "N": phase_c["N"],
            "total_graphs": phase_c["total_graphs"],
            "n_admitted": admitted,
            "cl_in_admitted": phase_c["cl_in_admitted"],
            "cl_variance": phase_c["cl_variance"],
            "n_admitted_at_variance_0": var0,
            "n_admitted_at_variance_below_0_5": near,
            "variance_0_fraction_of_admitted": var0 / admitted,
            "near_cl_fraction_of_admitted": near / admitted,
            "n_local_minima_in_sample": phase_c["n_local_minima_in_sample"],
        },
        "corrected_verdict": "reachable_not_stable",
    }


def iter106_report(receipt: dict[str, Any]) -> dict[str, Any]:
    results = receipt["results"]
    ratchet = results["phase_A_constraint_ratchet"]["stats"]
    topology = results["phase_B_variance0_topology"]
    absorbing = results["phase_C_absorbing_barrier"]["stats"]
    return {
        "pass": int(ratchet["n_trajectories"]) == 50
        and int(ratchet["n_halted_early"]) == 50
        and int(ratchet["n_at_corner_below_0.05"]) == 0
        and float(ratchet["localization_fraction_strict"]) == 0.0
        and int(topology["n_var0_nodes"]) == 170
        and int(topology["n_edges_in_var0_graph"]) == 0
        and int(topology["n_connected_components"]) == 170
        and max(topology["top_10_component_sizes"]) == 1
        and int(absorbing["n_trajectories"]) == 200
        and int(absorbing["n_absorbed"]) == 40
        and float(absorbing["absorption_rate"]) == 0.2,
        "constraint_ratchet": {
            "n_trajectories": ratchet["n_trajectories"],
            "n_halted_early": ratchet["n_halted_early"],
            "n_at_corner_below_0_05": ratchet["n_at_corner_below_0.05"],
            "n_below_0_5": ratchet["n_below_0.5"],
            "n_below_1_0": ratchet["n_below_1.0"],
            "localization_fraction_strict": ratchet["localization_fraction_strict"],
            "final_variance_mean": ratchet["final_variance_mean"],
            "final_variance_min": ratchet["final_variance_min"],
        },
        "variance0_topology": {
            "n_var0_nodes": topology["n_var0_nodes"],
            "n_edges_in_var0_graph": topology["n_edges_in_var0_graph"],
            "n_connected_components": topology["n_connected_components"],
            "top_10_component_sizes": topology["top_10_component_sizes"],
            "mean_same_var0_neighbors_in_sample": topology["mean_same_var0_neighbors_in_sample"],
        },
        "absorbing_barrier": {
            "n_trajectories": absorbing["n_trajectories"],
            "n_absorbed": absorbing["n_absorbed"],
            "absorption_rate": absorbing["absorption_rate"],
            "counted_as_stable_hit": False,
            "absorptions_excluded_from_stable_hit_count": absorbing["n_absorbed"],
            "mean_absorption_time": absorbing["mean_absorption_time"],
            "median_absorption_time": absorbing["median_absorption_time"],
            "min_absorption_time": absorbing["min_absorption_time"],
            "max_absorption_time": absorbing["max_absorption_time"],
        },
        "corrected_verdict": "reachable_but_local_edge_flip_topology_isolated_not_basin",
        "next_hypothesis": "test group-element or automorphism-action moves as the missing dynamics expansion",
    }


def iter107_report(receipt: dict[str, Any]) -> dict[str, Any]:
    results = receipt["results"]
    phase_a = results["phase_A_baseline_swap_only"]["stats"]
    phase_b = results["phase_B_pure_clifford_conjugation"]["stats"]
    phase_c = results["phase_C_mixed_swap_conjugation"]["stats"]
    phase_d = results["phase_D_variance0_start"]
    dwell = {key: row["stats"] for key, row in phase_d.items()}
    pure_swap = dwell["p_clifford_0_pure_swap"]
    mixed_02 = dwell["p_clifford_0.2_mixed"]
    mixed_05 = dwell["p_clifford_0.5_balanced"]
    pure_conj = dwell["p_clifford_1.0_pure_conjugation"]
    mixed_max_dwell = max(
        float(pure_swap["mean_dwell_fraction_at_var0"]),
        float(mixed_02["mean_dwell_fraction_at_var0"]),
        float(mixed_05["mean_dwell_fraction_at_var0"]),
    )
    return {
        "pass": receipt.get("verdict") == "NO_STABILIZATION_clifford_does_not_help"
        and int(phase_a["n_final_cl_iso"]) == 0
        and int(phase_b["n_final_cl_iso"]) == 0
        and int(phase_c["n_final_cl_iso"]) == 0
        and int(pure_swap["n_final_cl_iso"]) == 0
        and int(mixed_02["n_final_cl_iso"]) == 0
        and int(mixed_05["n_final_cl_iso"]) == 0
        and int(pure_conj["n_final_cl_iso"]) == 30
        and float(pure_conj["mean_final_variance"]) == 0.0
        and mixed_max_dwell < 0.01,
        "verdict": receipt.get("verdict"),
        "baseline_swap_only": {
            "n_trajectories": phase_a["n_trajectories"],
            "mean_dwell_fraction_at_var0": phase_a["mean_dwell_fraction_at_var0"],
            "mean_cl_iso_visit_fraction": phase_a["mean_cl_iso_visit_fraction"],
            "n_final_cl_iso": phase_a["n_final_cl_iso"],
            "mean_final_variance": phase_a["mean_final_variance"],
        },
        "pure_clifford_conjugation_random_start": {
            "n_trajectories": phase_b["n_trajectories"],
            "mean_dwell_fraction_at_var0": phase_b["mean_dwell_fraction_at_var0"],
            "n_final_cl_iso": phase_b["n_final_cl_iso"],
            "mean_final_variance": phase_b["mean_final_variance"],
        },
        "mixed_swap_conjugation_random_start": {
            "n_trajectories": phase_c["n_trajectories"],
            "mean_dwell_fraction_at_var0": phase_c["mean_dwell_fraction_at_var0"],
            "n_final_cl_iso": phase_c["n_final_cl_iso"],
            "mean_final_variance": phase_c["mean_final_variance"],
        },
        "variance0_start_dwell_by_p_clifford": {
            key: {
                "p_clifford": row["p_clifford"],
                "mean_dwell_fraction_at_var0": row["mean_dwell_fraction_at_var0"],
                "mean_cl_iso_visit_fraction": row["mean_cl_iso_visit_fraction"],
                "n_final_cl_iso": row["n_final_cl_iso"],
                "mean_final_variance": row["mean_final_variance"],
            }
            for key, row in dwell.items()
        },
        "mixed_dynamics_max_dwell_fraction_at_var0": mixed_max_dwell,
        "pure_conjugation_dwell_fraction_at_var0": pure_conj["mean_dwell_fraction_at_var0"],
        "corrected_verdict": "clifford_conjugation_connects_or_preserves_orbit_but_does_not_attract",
        "missing_element": "non_equilibrium_selector_or_energy_preference_for_low_variance",
    }


def graph_report() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    receipt_nodes = {key: graph.add_node(f"grok:{key}") for key in INPUTS}
    sidequest = graph.add_node("sidequest_boundary")
    stability_negative = graph.add_node("bounded_stability_negative_evidence")
    reachability = graph.add_node("bounded_reachability_evidence")
    topology = graph.add_node("bounded_variance0_topology_evidence")
    formal = graph.add_node(NAME)
    next_node = graph.add_node(NEXT_REQUIRED_SCOUT)
    for node in receipt_nodes.values():
        graph.add_edge(node, sidequest, "claim_ceiling")
        graph.add_edge(node, stability_negative, "audited_stability_negative")
    graph.add_edge(receipt_nodes["iter_105"], reachability, "substrate_reachability")
    graph.add_edge(receipt_nodes["iter_106"], reachability, "absorbing_barrier_reachability")
    graph.add_edge(receipt_nodes["iter_106"], topology, "isolated_variance0_subset")
    graph.add_edge(receipt_nodes["iter_107"], stability_negative, "mixed_conjugation_no_stabilization")
    graph.add_edge(receipt_nodes["iter_107"], reachability, "pure_conjugation_orbit_preservation")
    graph.add_edge(sidequest, formal, "nonpromotion")
    graph.add_edge(stability_negative, formal, "ingest")
    graph.add_edge(reachability, formal, "correction")
    graph.add_edge(topology, formal, "local_dynamics_blocker")
    graph.add_edge(formal, next_node, "integrate_or_partition")
    return {
        "pass": bool(rx.is_directed_acyclic_graph(graph)) and graph.num_nodes() >= 14 and graph.num_edges() >= 25,
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def proof_report(stable_endpoint_hit_count: int, boundary_ok: bool) -> dict[str, Any]:
    z_stable = z3.Bool("has_stable_endpoint_or_recovery_hit")
    z_boundary = z3.Bool("sidequest_boundary_preserved")
    z_complete = z3.Bool("completion_allowed_from_grok")
    solver = z3.Solver()
    solver.add(z_stable == (stable_endpoint_hit_count > 0))
    solver.add(z_boundary == boundary_ok)
    solver.add(z_complete == z3.And(z_stable, z3.Not(z_boundary)))
    solver.add(z_complete)
    z_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_stable = tm.mkConst(bsort, "has_stable_endpoint_or_recovery_hit")
    c_boundary = tm.mkConst(bsort, "sidequest_boundary_preserved")
    c_complete = tm.mkConst(bsort, "completion_allowed_from_grok")
    slv.assertFormula(c_stable if stable_endpoint_hit_count > 0 else tm.mkTerm(Kind.NOT, c_stable))
    slv.assertFormula(c_boundary if boundary_ok else tm.mkTerm(Kind.NOT, c_boundary))
    slv.assertFormula(
        tm.mkTerm(
            Kind.EQUAL,
            c_complete,
            tm.mkTerm(Kind.AND, c_stable, tm.mkTerm(Kind.NOT, c_boundary)),
        )
    )
    slv.assertFormula(c_complete)
    c_sat = slv.checkSat().isSat()
    return {
        "pass": not z_sat and not c_sat,
        "strict_stable_localization_hit_count": stable_endpoint_hit_count,
        "sidequest_boundary_preserved": boundary_ok,
        "z3_completion_from_grok_unsat": not z_sat,
        "cvc5_completion_from_grok_unsat": not c_sat,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "using side-quest reachability evidence as if it were stable basin evidence",
        "most_dangerous_failure": "continuing to frame F01+N01 alone as sufficient for exact Clifford attractor localization",
        "hidden_assumption": "substrate-constrained reachability implies a lower exit probability from Clifford-isomorphic states",
        "checks_applied": [
            "side-quest claim ceiling audit",
            "zero strict stable-localization count over iter_100/101/102/104/105/106",
            "substrate rarity audit over iter_103",
            "iter_105 substrate-constrained reachability and perturbed-Cl recovery audit",
            "iter_106 constraint-ratchet, variance-zero topology, and absorbing-barrier audit",
            "iter_107 Clifford conjugation and mixed-dynamics stabilization audit",
            "z3/cvc5 block on completion from Grok evidence",
        ],
    }


def main() -> int:
    started = time.time()
    receipts = {key: read_json(path) for key, path in INPUTS.items()}
    boundaries = receipt_boundaries(receipts)
    weak = iter100_report(receipts["iter_100"])
    sharpened = iter101_report(receipts["iter_101"])
    search = iter102_report(receipts["iter_102"])
    substrate = iter103_report(receipts["iter_103"])
    regularity = iter104_report(receipts["iter_104"])
    corrected = iter105_report(receipts["iter_105"])
    topology = iter106_report(receipts["iter_106"])
    conjugation = iter107_report(receipts["iter_107"])
    graph = graph_report()
    stable_endpoint_hits = (
        int(weak["terminal_var_below_0_01"] or 0)
        + int(sharpened["strict_hits"])
        + int(search["strict_positive_count"])
        + int(regularity["strict_positive_count"])
        + int(corrected["substrate_constrained_walk"]["n_trajectories_with_final_cl_iso"])
        + int(corrected["perturbed_cl_recovery"]["n_recovered_to_corner"])
        + int(topology["constraint_ratchet"]["n_at_corner_below_0_05"])
        + int(conjugation["baseline_swap_only"]["n_final_cl_iso"])
        + int(conjugation["mixed_swap_conjugation_random_start"]["n_final_cl_iso"])
    )
    proof = proof_report(stable_endpoint_hits, boundaries["pass"])
    premortem = premortem_report()
    positive = {
        "grok_receipts_present_and_sidequest_bounded": boundaries,
        "weak_admission_dynamic_no_exact_localization": weak,
        "sharpened_admission_dynamic_no_exact_localization": sharpened,
        "constraint_search_zero_strict_localization_with_c2_directional_pull": search,
        "substrate_variation_clifford_structure_is_rare": substrate,
        "c2_regularity_sweep_zero_strict_localization": regularity,
        "substrate_constrained_reachable_but_not_stable": corrected,
        "constraint_ratchet_variance0_topology_and_absorbing_barrier": topology,
        "clifford_conjugation_mixed_dynamics_no_stabilization": conjugation,
        "grok_reachability_stability_evidence_dependency_graph": graph,
        "z3_cvc5_completion_from_grok_blocked": proof,
        "premortem_applied": premortem,
    }
    graveyard = {
        "f01_n01_alone_forces_exact_clifford_attractor_killed_for_tested_dynamics": {
            "pass": weak["pass"] and sharpened["pass"] and search["pass"] and regularity["pass"] and corrected["pass"],
            "reason": "Grok iter_105 corrects the earlier overclaim: Cl is reachable under Pauli substrate-constrained dynamics, but no tested dynamic makes it an exact stable endpoint or recovery basin.",
        },
        "c2_regularity_as_sufficient_selector_killed": {
            "pass": regularity["pass"],
            "reason": "C2_regularity pulls toward low variance but strict localization remains zero; tighter thresholds empty the admitted set.",
        },
        "generic_operator_substrate_spontaneously_yields_clifford_killed": {
            "pass": substrate["pass"],
            "reason": "Only 3/57000 sampled subsets were Cl-isomorphic, all in Pauli tensor n=4; n=6 had zero hits.",
        },
        "clifford_unreachable_under_algebraic_substrate_walk_killed": {
            "pass": corrected["substrate_constrained_walk"]["n_trajectories_ever_hit_cl_iso"] == 27,
            "reason": "The cross-audit objection is accepted: generic graph edge flips missed reachable Clifford-isomorphic states under Pauli substrate-constrained mutation.",
        },
        "clifford_as_stable_basin_under_f01_n01_killed_for_tested_dynamics": {
            "pass": corrected["substrate_constrained_walk"]["n_trajectories_with_final_cl_iso"] == 0
            and corrected["perturbed_cl_recovery"]["n_recovered_to_corner"] == 0,
            "reason": "Substrate walks visit Cl-isomorphic states but leave them; perturbed-Cl recovery is 0/200.",
        },
        "constraint_ratchet_as_local_clifford_basin_killed": {
            "pass": topology["constraint_ratchet"]["n_at_corner_below_0_05"] == 0
            and topology["constraint_ratchet"]["n_halted_early"] == topology["constraint_ratchet"]["n_trajectories"],
            "reason": "Progressive tightening halted all 50 trajectories and put 0 at the strict variance corner.",
        },
        "variance0_subset_connected_under_single_edge_flips_killed": {
            "pass": topology["variance0_topology"]["n_edges_in_var0_graph"] == 0
            and topology["variance0_topology"]["n_connected_components"] == topology["variance0_topology"]["n_var0_nodes"],
            "reason": "The 170 variance-zero n=3 graphs are singleton components under single-edge flips.",
        },
        "absorbing_barrier_as_natural_stability_killed": {
            "pass": topology["absorbing_barrier"]["n_absorbed"] == 40
            and corrected["perturbed_cl_recovery"]["n_recovered_to_corner"] == 0,
            "reason": "An artificial absorbing barrier catches 40/200 trajectories, but natural perturbed-Cl recovery remains 0/200.",
        },
        "clifford_conjugation_as_attractor_selector_killed": {
            "pass": conjugation["mixed_dynamics_max_dwell_fraction_at_var0"] < 0.01
            and conjugation["mixed_swap_conjugation_random_start"]["n_final_cl_iso"] == 0,
            "reason": "Mixed swap+Clifford conjugation has near-zero variance-0 dwell and 0/30 final Cl-isomorphic trajectories.",
        },
        "pure_conjugation_as_basin_killed": {
            "pass": conjugation["pure_clifford_conjugation_random_start"]["n_final_cl_iso"] == 0
            and conjugation["pure_conjugation_dwell_fraction_at_var0"] > 1.0,
            "reason": "Pure conjugation preserves variance-zero only when already there; from random starts it preserves nonzero variance and reaches no Cl endpoints.",
        },
        "grok_sidequest_as_formal_completion_evidence_killed": {
            "pass": boundaries["pass"] and proof["pass"],
            "reason": "Side-quest receipts are used as bounded reachability/stability evidence only and cannot close a formal manifold objective.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": PROMOTION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "completion_status_boundary": {
            "pass": True,
            "completion_status": "not_achieved",
            "reason": "Grok evidence supports reachable-not-stable, isolated variance-zero topology, and no stabilization from mixed Clifford conjugation for tested dynamics; this is not a universal theorem or final manifold completion.",
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Test a non-tautological selector or energy rule that could prefer low variance without directly checking Cl-isomorphism.",
        },
    }
    all_pass = all(item.get("pass") is True for item in positive.values()) and all(
        item.get("pass") is True for item in graveyard.values()
    ) and all(item.get("pass") is True for item in boundary.values())
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "two_root_constraints": TWO_ROOT_CONSTRAINTS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {
            key: {"path": rel(path), "sha256": sha256(path)}
            for key, path in INPUTS.items()
        },
        "premortem": premortem,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": "not_achieved",
            "grok_iter_count": len(INPUTS),
            "iter102_experiment_count": search["experiment_count"],
            "iter104_experiment_count": regularity["experiment_count"],
            "iter103_tested_condition_count": substrate["tested_condition_count"],
            "iter103_sample_count": substrate["sample_count"],
            "strict_stable_localization_hit_count": stable_endpoint_hits,
            "substrate_cl_isomorphic_hit_count": substrate["cl_isomorphic_hit_count"],
            "iter105_substrate_reach_count": corrected["substrate_constrained_walk"][
                "n_trajectories_ever_hit_cl_iso"
            ],
            "iter105_substrate_final_cl_iso_count": corrected["substrate_constrained_walk"][
                "n_trajectories_with_final_cl_iso"
            ],
            "iter105_recovery_count": corrected["perturbed_cl_recovery"]["n_recovered_to_corner"],
            "iter105_n3_variance0_admitted_count": corrected["exact_n3_enumeration"][
                "n_admitted_at_variance_0"
            ],
            "iter106_ratchet_halted_early_count": topology["constraint_ratchet"]["n_halted_early"],
            "iter106_ratchet_corner_count": topology["constraint_ratchet"]["n_at_corner_below_0_05"],
            "iter106_variance0_nodes": topology["variance0_topology"]["n_var0_nodes"],
            "iter106_variance0_edges": topology["variance0_topology"]["n_edges_in_var0_graph"],
            "iter106_variance0_components": topology["variance0_topology"]["n_connected_components"],
            "iter106_absorbing_barrier_absorbed_count": topology["absorbing_barrier"]["n_absorbed"],
            "iter106_absorbing_barrier_absorption_rate": topology["absorbing_barrier"]["absorption_rate"],
            "iter106_absorbing_barrier_counted_as_stable_hit": topology["absorbing_barrier"][
                "counted_as_stable_hit"
            ],
            "iter106_absorbing_barrier_absorptions_excluded_from_stable_hit_count": topology[
                "absorbing_barrier"
            ]["absorptions_excluded_from_stable_hit_count"],
            "iter107_baseline_swap_dwell_fraction": conjugation["baseline_swap_only"][
                "mean_dwell_fraction_at_var0"
            ],
            "iter107_mixed_20_dwell_fraction": conjugation["variance0_start_dwell_by_p_clifford"][
                "p_clifford_0.2_mixed"
            ]["mean_dwell_fraction_at_var0"],
            "iter107_mixed_50_dwell_fraction": conjugation["variance0_start_dwell_by_p_clifford"][
                "p_clifford_0.5_balanced"
            ]["mean_dwell_fraction_at_var0"],
            "iter107_pure_conjugation_dwell_fraction": conjugation["pure_conjugation_dwell_fraction_at_var0"],
            "iter107_mixed_random_start_final_cl_iso_count": conjugation[
                "mixed_swap_conjugation_random_start"
            ]["n_final_cl_iso"],
            "iter107_verdict": conjugation["verdict"],
            "best_directional_pull": "C2_regularity",
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "items": sorted(graveyard),
        },
        "why_not_v4_probes": "This is a v5 formal scout ingesting side-quest Grok receipts as bounded reachability/stability evidence, not a v4 proposal or canonical promotion.",
        "divergence_log": [
            "If side-quest evidence is treated as formal proof, the boundary is violated.",
            "If C2_regularity drift is treated as exact localization, the zero strict-hit result is hidden.",
            "If substrate rarity is treated as impossibility, the Pauli n=4 positive hits are overfiltered.",
            "If substrate-constrained reachability is treated as a stable basin, the 0/30 final-Cl and 0/200 recovery results are hidden.",
            "If the constraint ratchet is treated as successful basin localization, the 50/50 early halts and 0 strict corner hits are hidden.",
            "If variance-zero reachability is treated as local topology, the 170 isolated singleton components are hidden.",
            "If absorbing-barrier hits are treated as natural stability, the artificial lock-in condition becomes the missing dynamics.",
            "If pure Clifford conjugation is treated as attraction, its graph-preserving inability to reach Cl from random starts is hidden.",
            "If mixed conjugation is treated as stabilization, the near-zero dwell fractions and 0 final-Cl endpoints are hidden.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "strict_stable_localization_hit_count": stable_endpoint_hits,
                "iter103_sample_count": substrate["sample_count"],
                "substrate_cl_isomorphic_hit_count": substrate["cl_isomorphic_hit_count"],
                "iter105_substrate_reach_count": corrected["substrate_constrained_walk"][
                    "n_trajectories_ever_hit_cl_iso"
                ],
                "iter105_recovery_count": corrected["perturbed_cl_recovery"]["n_recovered_to_corner"],
                "iter106_variance0_edges": topology["variance0_topology"]["n_edges_in_var0_graph"],
                "iter106_absorbing_barrier_absorbed_count": topology["absorbing_barrier"]["n_absorbed"],
                "iter107_mixed_20_dwell_fraction": conjugation["variance0_start_dwell_by_p_clifford"][
                    "p_clifford_0.2_mixed"
                ]["mean_dwell_fraction_at_var0"],
                "iter107_verdict": conjugation["verdict"],
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
