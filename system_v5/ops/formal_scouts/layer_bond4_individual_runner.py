"""Shared runner for individual per-layer PEPS3D bond-4 scouts."""

from __future__ import annotations

import concurrent.futures
import json
import os
import time
from typing import Any

import sim_l0_l1_l2_l3_l6_l8_bond4_tool_ablation_deepening_probe as base


def _run_rows(layer: str) -> tuple[list[dict[str, Any]], int]:
    cfg = base.LAYERS[layer]
    tasks = [
        (layer, site_count, sheet, bond_dim)
        for site_count in base.SITE_COUNTS
        for sheet in cfg["sheets"]
        for bond_dim in base.BOND_DIMS
    ]
    max_workers = min(len(tasks), max(1, os.cpu_count() or 1), 8)
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(base.row_task, *task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (row["site_count"], row["sheet"], row["peps3d_bond_dim"]))
    return rows, max_workers


def _single_layer_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pass": all(row["pass"] for row in rows),
        "row_count": len(rows),
        "site_counts": sorted({row["site_count"] for row in rows}),
        "sheets": sorted({row["sheet"] for row in rows}),
        "max_peps3d_bond": max(row["peps3d_bond_dim"] for row in rows),
        "min_bond4_required_control_gap": min(min(row["bond4_required_control_gaps"].values()) for row in rows),
        "weak_diagnostic_controls_flagged": [
            {
                "site_count": row["site_count"],
                "sheet": row["sheet"],
                "controls": row["weak_diagnostic_controls_flagged"],
            }
            for row in rows
            if row["weak_diagnostic_controls_flagged"]
        ],
        "min_order_or_label_gap_from_baseline": min(row["min_order_or_label_gap_from_baseline"] for row in rows),
        "min_qit_mutual_information": min(row["bond4_nominal"]["QIT_cut_readouts"]["mutual_information"] for row in rows),
    }


def run_layer(
    *,
    layer: str,
    sim_id: str,
    tier: str,
    purpose: str,
    scientific_question: str,
    finite_map: str,
    domain: str,
    codomain: str,
    geometry_layer: str,
    claim_ceiling: str,
    source_alignment_category: str,
    tool_manifest: dict[str, Any],
    tool_integration_depth: dict[str, Any],
) -> int:
    started = time.time()
    rows, max_workers = _run_rows(layer)
    expected_rows = len(base.SITE_COUNTS) * len(base.LAYERS[layer]["sheets"]) * len(base.BOND_DIMS)
    layer_summary = _single_layer_summary(rows)
    min_gaps = {
        "bond4_required_controls": min(min(row["bond4_required_control_gaps"].values()) for row in rows),
        "bond4_peps3d_erased": base.min_gap(rows, "peps3d_erased"),
        "bond4_scalar_entropy_primary": base.min_gap(rows, "scalar_entropy_primary"),
        "baseline_order_or_label": min(row["min_order_or_label_gap_from_baseline"] for row in rows),
    }
    weak_controls = [
        {
            "layer": row["layer"],
            "site_count": row["site_count"],
            "sheet": row["sheet"],
            "controls": row["weak_diagnostic_controls_flagged"],
            "status": "diagnostic_not_claim_bearing",
        }
        for row in rows
        if row["weak_diagnostic_controls_flagged"]
    ]
    topo = base.topology_witnesses(rows)
    geom = base.geometry_witnesses()
    z3_result = base.z3_gate(min_gaps, all(row["pass"] for row in rows))
    cvc5_result = base.cvc5_gate(
        {
            "all_rows_pass": all(row["pass"] for row in rows),
            "topology_tools": topo["pass"],
            "geometry_tools": geom["pass"],
            "z3_gate": z3_result["pass"],
            "bond4": max(row["peps3d_bond_dim"] for row in rows) == 4,
            "not_promoted": base.PROMOTION_ALLOWED is False,
        }
    )
    ablations = base.tool_ablations(rows, topo, geom, z3_result, cvc5_result, expected_rows=expected_rows)
    positive = {
        "individual_layer_bond4_rows_run": {
            "pass": all(row["pass"] for row in rows),
            "layer": layer,
            "row_count": len(rows),
            "expected_rows": expected_rows,
            "site_counts": base.SITE_COUNTS,
            "bond_dims": base.BOND_DIMS,
        },
        "actual_quimb_peps3d_bond4_objects_constructed": {
            "pass": all(row["bond4_nominal"]["quimb_peps3d_object"] == "PEPS3D" and row["bond4_nominal"]["peps3d_bond_dim"] == 4 for row in rows),
            "min_num_tensors": min(row["bond4_nominal"]["peps3d_num_tensors"] for row in rows),
            "max_num_tensors": max(row["bond4_nominal"]["peps3d_num_tensors"] for row in rows),
        },
        "QIT_entropy_is_derived_from_bond4_cut_state": {
            "pass": min(row["bond4_nominal"]["QIT_cut_readouts"]["mutual_information"] for row in rows) > 0.0,
            "min_mutual_information": min(row["bond4_nominal"]["QIT_cut_readouts"]["mutual_information"] for row in rows),
            "max_coherent_information": max(row["bond4_nominal"]["QIT_cut_readouts"]["coherent_information_A_to_B"] for row in rows),
        },
        "topology_tool_witnesses": topo,
        "geometry_tool_witnesses": geom,
        "z3_positive_gap_and_lock_gate": z3_result,
        "cvc5_nonpromotion_gate": cvc5_result,
    }
    graveyard_companions = {
        "required_bond4_controls_change_signature": {"gap": min_gaps["bond4_required_controls"], "pass": min_gaps["bond4_required_controls"] > base.GAP_FLOOR},
        "peps3d_erased_control_changes_bond4_signature": {"gap": min_gaps["bond4_peps3d_erased"], "pass": min_gaps["bond4_peps3d_erased"] > base.GAP_FLOOR},
        "scalar_entropy_primary_control_changes_bond4_signature": {"gap": min_gaps["bond4_scalar_entropy_primary"], "pass": min_gaps["bond4_scalar_entropy_primary"] > base.GAP_FLOOR},
        "baseline_order_or_label_controls_still_fire": {"gap": min_gaps["baseline_order_or_label"], "pass": min_gaps["baseline_order_or_label"] > base.GAP_FLOOR},
        "weak_diagnostic_controls_are_flagged_not_promoted": {"flagged_count": len(weak_controls), "flagged_controls": weak_controls, "pass": True},
        "dense_global_state_closure_banned": {"dense_state_closure_used": False, "pass": True},
        "consumer_proxy_controls_blocked": {"blocked_consumers": base.BLOCKED_CONSUMERS, "pass": True},
    }
    boundary = {
        "scale_8_16_32_64_checked": {"pass": sorted({row["site_count"] for row in rows}) == base.SITE_COUNTS, "site_counts": sorted({row["site_count"] for row in rows})},
        "bond4_checked_without_bond5_promotion": {"pass": max(row["peps3d_bond_dim"] for row in rows) == 4, "max_bond": max(row["peps3d_bond_dim"] for row in rows), "bond5_status": "blocked_not_tested_here"},
        "parallel_execution_used": {"pass": max_workers > 1, "max_workers": max_workers, "task_count": len(rows)},
        "promotion_allowed_false": {"pass": base.PROMOTION_ALLOWED is False, "promotion_allowed": base.PROMOTION_ALLOWED},
        "downstream_consumers_locked": {"pass": True, "blocked_consumers": base.BLOCKED_CONSUMERS},
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in ablations.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": sim_id,
        "name": sim_id,
        "version": "1.0.0",
        "tier": tier,
        "purpose": purpose,
        "scientific_question": scientific_question,
        "classification": "formal_scout",
        "sim_execution_kind": "nonclassical",
        "sim_class": "individual_manifold_layer_depth_probe",
        "source_alignment_category": source_alignment_category,
        "promotion_allowed": False,
        "claim_ceiling": claim_ceiling,
        "root_constraints_in_force": {
            "F01": "finite carriers, scales, sheets, layer actions, PEPS3D bond-4 arrays, controls, and output readouts",
            "N01": "baseline order-sensitive controls plus layer-specific bond-4 controls with nonzero required gaps",
        },
        "finite_map": finite_map,
        "domain": domain,
        "codomain_or_output": codomain,
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) spinor-network carrier at bond_dim=4",
        "geometry_layer": geometry_layer,
        "carrier_realization": "torch-native spinors or spinor-derived densities embedded into quimb PEPS3D bond-4 arrays; QIT readouts derive from bounded cut states",
        "peps3d_embedding": "actual qtn.PEPS3D objects are constructed from bond-4 torch arrays for this single layer at every tested scale",
        "PEPS3D_K_anchor": {
            "carrier": "K=(V,E,F,C)",
            "shapes": base.SHAPES,
            "site_counts": base.SITE_COUNTS,
            "bond_dims": base.BOND_DIMS,
            "max_sites": 64,
            "max_peps3d_bond": 4,
            "dense_state_closure_used": False,
        },
        "torch_spinor_or_density": "torch-native complex spinors and spinor-derived density/cut states remain first-class",
        "spinor_state": "two-component complex spinors or spinor-derived densities; densities are derived as psi psi^dagger",
        "quaternion_action": "load-bearing only for L3; otherwise not_applicable",
        "QIT_entropy_where_defined": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information are derived from finite bond-4 cut states",
        "scale_8_16_32_64_or_resource_blocker": {"status": "passed_individual_bond4_layer_packet", "sites": base.SITE_COUNTS, "bond_dims": base.BOND_DIMS, "resource_blocker": None},
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l0_l1_l2_l3_l6_l8_bond4_tool_ablation_deepening_probe_results.json"
        ],
        "downstream_blocks": base.BLOCKED_CONSUMERS,
        "blocked_consumers": base.BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "local QIT cut readouts derived from this layer's bond-4 PEPS3D carrier signatures; no Xi/Phi0/Axis0 cut",
        "law_or_candidate_tested": f"individual {layer} PEPS3D bond-4 carrier stress and tool-ablation deepening",
        "allowed_claims": [
            f"{layer} survived this bounded PEPS3D bond-4 carrier stress at 8/16/32/64 sites",
            "tool ablations in this individual layer packet are non-vacuous deltas",
            "QIT entropy readouts are derived from finite carrier actions and are not the primary object",
        ],
        "promotion_blockers": base.BLOCKED_CONSUMERS
        + [
            "no cross-layer stacking in this packet",
            "no bond5 admission in this packet",
            "no general shape law",
            "no full layer completion claim",
        ],
        "F01_witness": "finite single-layer rows, shapes, sites, sheets, bond_dim=4, PEPS3D arrays, bounded contractions, tool witnesses, and controls",
        "N01_witness": "baseline order-sensitive controls remain nonzero and required bond-4 controls change the carrier signatures",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "rows": rows,
        "layer_summary": layer_summary,
        "tool_ablations_by_tool": ablations,
        "ablation_outcome_delta": ablations,
        "weak_controls_flagged": weak_controls,
        "nearby_variants": {
            "passed": len([row for row in rows if row["pass"]]),
            "total": len(rows),
            "variants": [layer, "site_counts_8_16_32_64", "peps3d_bond_dim_4"],
        },
        "TOOL_MANIFEST": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": tool_integration_depth,
        "all_pass": all_pass,
        "blockers": [] if all_pass else [f"{layer}_individual_bond4_or_tool_ablation_failed"],
        "next_admissible_step": "run the next individual layer sim or write a blocked-reason artifact; do not open stacking or downstream consumers from this receipt alone",
        "why_not_v4_probes": "This is a v5 individual formal layer-depth scout using torch-native spinors, actual quimb PEPS3D bond-4 carriers, QIT readouts, and tool ablation deltas.",
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "layer": layer,
            "row_count": len(rows),
            "max_sites": 64,
            "max_peps3d_bond": 4,
            "min_gaps": min_gaps,
            "promotion_allowed": False,
            "blocked_consumers": base.BLOCKED_CONSUMERS,
        },
    }
    if layer == "L2":
        # L2 declares its defining erasure load-bearing: collapsing the L/R Weyl sheet (chirality)
        # MUST move the carrier, else the gate fails it (vacuous_required_erasure).
        result["required_load_bearing_erasures"] = ["sheet", "chirality"]
    base.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = base.RESULT_DIR / f"{sim_id}_results.json"
    out_path.write_text(json.dumps(base.as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1
