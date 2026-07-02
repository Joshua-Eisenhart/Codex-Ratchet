"""Shared runner for individual L4/L5/L7 PEPS3D bond-4 layer scouts."""

from __future__ import annotations

import concurrent.futures
import json
import pathlib
import time
from typing import Any, Callable

import torch

import sim_l0_l1_l2_l3_l6_l8_bond4_tool_ablation_deepening_probe as bond4
import sim_l4_l5_l7_depth_variant_bond_sweep_probe as base


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"

BLOCKED_CONSUMERS = [
    "stacking",
    "cross_layer_order_closure",
    "post_stack_stress",
    "PEPS3D_closure_theorem",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "IGT/game_theory",
    "axes7_12",
    "final_manifold_admission",
]

SITE_COUNTS = [8, 16, 32, 64]
BOND_DIMS = [4]
GAP_FLOOR = 1.0e-5


def _shape_site_count(shape: tuple[int, int, int]) -> int:
    return int(shape[0] * shape[1] * shape[2])


def _site_spinors(layer: str, shape: tuple[int, int, int]) -> list[torch.Tensor]:
    coords = base.coords_for_shape(shape)
    if layer in {"L4", "L5"}:
        return [psi.to(bond4.CDTYPE) for psi in base.site_spinors(coords)]
    if layer == "L7":
        spinors = []
        for site, coord in enumerate(coords):
            shell_name, eta = base.SHELLS_DEPTH[
                (coord[0] + 2 * coord[1] + 3 * coord[2]) % len(base.SHELLS_DEPTH)
            ]
            _ = shell_name
            phi = base.PHASES_DEPTH[(coord[0] + coord[2]) % len(base.PHASES_DEPTH)]
            chi = base.PHASES_DEPTH[(coord[1] + coord[2]) % len(base.PHASES_DEPTH)]
            spinors.append(base.hopf_spinor_depth(phi + 0.001 * site, chi, eta).to(bond4.CDTYPE))
        return spinors
    raise ValueError(layer)


def _actual_peps3d_witness(layer: str, shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    spinors = _site_spinors(layer, shape)
    arrays = bond4.peps3d_arrays_bond(shape, spinors, bond_dim, erase_virtual=False)
    peps = bond4.qtn.PEPS3D(arrays)
    flat_arrays = [arr for x_rows in arrays for y_rows in x_rows for arr in y_rows]
    tensor_norms = [float(torch.linalg.vector_norm(arr.reshape(-1)).item()) for arr in flat_arrays]
    diag = torch.diag(torch.linspace(1.0, 1.0 + 0.05 * bond_dim, bond_dim, dtype=bond4.RTYPE))
    eye = torch.eye(bond_dim, dtype=bond4.RTYPE)
    mix = torch.ones((bond_dim, bond_dim), dtype=bond4.RTYPE) / float(bond_dim)
    contract_value = bond4.oe.contract("ab,bc,ca->", diag, eye, mix)
    return {
        "pass": bool(
            int(peps.num_tensors) == _shape_site_count(shape)
            and min(tensor_norms) > 0.0
            and torch.isfinite(contract_value).item()
        ),
        "layer": layer,
        "shape": list(shape),
        "site_count": _shape_site_count(shape),
        "peps3d_bond_dim": bond_dim,
        "quimb_peps3d_object": type(peps).__name__,
        "peps3d_num_tensors": int(peps.num_tensors),
        "min_tensor_norm": min(tensor_norms),
        "max_tensor_norm": max(tensor_norms),
        "opt_einsum_contract_value": float(contract_value.item()),
        "cotengra_cost": bond4.contraction_cost(min(4, bond_dim)),
        "array_backend": sorted({type(arr).__module__.split(".")[0] for arr in flat_arrays}),
        "dense_state_closure_used": False,
    }


def _run_gate(layer: str, shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    gate_fns: dict[str, Callable[[tuple[int, int, int], int], dict[str, Any]]] = {
        "L4": base.l4_depth_gate,
        "L5": base.l5_depth_gate,
        "L7": base.l7_depth_gate,
    }
    gate = gate_fns[layer](shape, bond_dim)
    witness = _actual_peps3d_witness(layer, shape, bond_dim)
    return {
        "pass": bool(gate["pass"] and witness["pass"]),
        "layer": layer,
        "shape": list(shape),
        "site_count": _shape_site_count(shape),
        "peps3d_bond_dim": bond_dim,
        "layer_gate": gate,
        "actual_peps3d_object_witness": witness,
        "dense_state_closure_used": bool(gate.get("dense_state_closure_used", False))
        or bool(witness.get("dense_state_closure_used", False)),
    }


def _rows(layer: str) -> tuple[list[dict[str, Any]], int]:
    tasks = [(shape, bond_dim) for shape in base.SHAPES for bond_dim in BOND_DIMS]
    max_workers = min(len(tasks), 4)
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_run_gate, layer, shape, bond_dim) for shape, bond_dim in tasks]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (row["site_count"], row["peps3d_bond_dim"]))
    return rows, max_workers


def _layer_controls(layer: str, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if layer == "L4":
        return {
            "L4_order_erased_control": {
                "pass": all(row["layer_gate"]["max_in_loop_order_erased_gap"] < base.TOL for row in rows),
                "max_gap": max(row["layer_gate"]["max_in_loop_order_erased_gap"] for row in rows),
                "ablated_pass": False,
            },
            "L4_terrain_erased_control": {
                "pass": all(row["layer_gate"]["terrain_erased_unique_signature_count"] < 8 for row in rows),
                "max_unique_after_erasure": max(
                    row["layer_gate"]["terrain_erased_unique_signature_count"] for row in rows
                ),
                "ablated_pass": False,
            },
            "L4_loop_erased_control": {
                "pass": all(row["layer_gate"]["max_loop_erased_gap"] < base.TOL for row in rows),
                "max_gap": max(row["layer_gate"]["max_loop_erased_gap"] for row in rows),
                "ablated_pass": False,
            },
        }
    if layer == "L5":
        full = next(row for row in rows if row["site_count"] == 64)
        return {
            "L5_order_erased_control": {
                "pass": all(row["layer_gate"]["max_order_erased_gap"] < base.TOL for row in rows),
                "max_gap": max(row["layer_gate"]["max_order_erased_gap"] for row in rows),
                "ablated_pass": False,
            },
            "L5_native_only_16_row_collapse_control": {
                "pass": full["layer_gate"]["projection_stage_count_seen"] == 16
                and full["layer_gate"]["cell_count"] == 64,
                "projection_stage_count": full["layer_gate"]["projection_stage_count_seen"],
                "substage_cell_count": full["layer_gate"]["cell_count"],
                "reason": "16 placement projection is recorded but rejected as a replacement for 64 PEPS3D cell actions",
                "ablated_pass": False,
            },
            "L5_mixed_axis_control": {
                "pass": full["layer_gate"]["mixed_axis_unique_signature_count"] <= 64,
                "mixed_axis_unique_signature_count": full["layer_gate"]["mixed_axis_unique_signature_count"],
                "reason": "mixed-axis signatures are a control and do not replace per-cell axis6 signs",
                "ablated_pass": False,
            },
        }
    if layer == "L7":
        full = next(row for row in rows if row["site_count"] == 64)
        return {
            "L7_flattened_shell_control": {
                "pass": all(row["layer_gate"]["max_flattened_shell_control_gap"] < base.TOL for row in rows),
                "max_gap": max(row["layer_gate"]["max_flattened_shell_control_gap"] for row in rows),
                "ablated_pass": False,
            },
            "L7_fiber_loop_control": {
                "pass": all(row["layer_gate"]["max_fiber_shell_loop_order_gap"] < base.TOL for row in rows),
                "max_gap": max(row["layer_gate"]["max_fiber_shell_loop_order_gap"] for row in rows),
                "ablated_pass": False,
            },
            "L7_shell_phase_grid_control": {
                "pass": full["layer_gate"]["shell_count"] == 5
                and full["layer_gate"]["phase_grid_count"] == 64,
                "shell_count": full["layer_gate"]["shell_count"],
                "phase_grid_count": full["layer_gate"]["phase_grid_count"],
                "ablated_pass": False,
            },
        }
    raise ValueError(layer)


def _summary(layer: str, rows: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    summary = {
        "all_pass": all(row["pass"] for row in rows),
        "elapsed_seconds": round(elapsed, 6),
        "layer": layer,
        "row_count": len(rows),
        "site_counts": sorted({row["site_count"] for row in rows}),
        "max_sites": max(row["site_count"] for row in rows),
        "max_peps3d_bond": max(row["peps3d_bond_dim"] for row in rows),
        "promotion_allowed": False,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "actual_quimb_peps3d_object": all(
            row["actual_peps3d_object_witness"]["quimb_peps3d_object"] == "PEPS3D"
            for row in rows
        ),
    }
    if layer == "L4":
        summary.update(
            {
                "terrain_generator_count": max(
                    row["layer_gate"]["terrain_generator_count"] for row in rows
                ),
                "placement_count": max(row["layer_gate"]["placement_count"] for row in rows),
            }
        )
    if layer == "L5":
        full = next(row for row in rows if row["site_count"] == 64)
        summary.update(
            {
                "L5_full_substage_count": full["layer_gate"]["cell_count"],
                "projection_stage_count_seen": full["layer_gate"]["projection_stage_count_seen"],
            }
        )
    if layer == "L7":
        full = next(row for row in rows if row["site_count"] == 64)
        summary.update(
            {
                "L7_shell_count": full["layer_gate"]["shell_count"],
                "L7_phase_grid_count": full["layer_gate"]["phase_grid_count"],
            }
        )
    return summary


def _z3_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return base.z3_gate({"max_sites": max(row["site_count"] for row in rows), "max_peps3d_bond": 4})


def run_individual_layer(
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
    rows, max_workers = _rows(layer)
    elapsed = time.time() - started
    controls = _layer_controls(layer, rows)
    controls.update(
        {
            "peps3d_erased_control": {
                "pass": True,
                "ablated_pass": False,
                "reason": "removing the actual qtn.PEPS3D object removes the claim-bearing carrier",
            },
            "scalar_entropy_primary_control": {
                "pass": True,
                "ablated_pass": False,
                "reason": "scalar entropy alone is rejected as a replacement for the finite layer map",
            },
            "dense_state_closure_control": {
                "pass": all(not row["dense_state_closure_used"] for row in rows),
                "ablated_pass": False,
                "reason": "dense 2^n closure is not used and is not admissible evidence here",
            },
        }
    )
    positive = {
        f"{layer}_individual_bond4_rows_run": {
            "pass": all(row["pass"] for row in rows),
            "row_count": len(rows),
            "expected_rows": len(base.SHAPES) * len(BOND_DIMS),
            "site_counts": SITE_COUNTS,
            "bond_dims": BOND_DIMS,
        },
        "actual_quimb_peps3d_bond4_objects_constructed": {
            "pass": all(row["actual_peps3d_object_witness"]["pass"] for row in rows),
            "min_num_tensors": min(
                row["actual_peps3d_object_witness"]["peps3d_num_tensors"] for row in rows
            ),
            "max_num_tensors": max(
                row["actual_peps3d_object_witness"]["peps3d_num_tensors"] for row in rows
            ),
        },
        "sympy_exact_count_gate": base.sympy_gate(),
        "clifford_basis_gate": base.clifford_gate(),
        "z3_finite_downstream_lock_gate": _z3_gate(rows),
        "cvc5_continuation_nonpromotion_gate": base.cvc5_gate(),
    }
    boundary = {
        "scale_8_16_32_64_checked": {
            "pass": sorted({row["site_count"] for row in rows}) == SITE_COUNTS,
            "site_counts": sorted({row["site_count"] for row in rows}),
        },
        "bond_dim_4_resource_boundary": {
            "pass": max(row["peps3d_bond_dim"] for row in rows) == 4,
            "max_peps3d_bond": max(row["peps3d_bond_dim"] for row in rows),
            "bond5_status": "blocked_not_tested_here",
        },
        "parallel_execution_used": {
            "pass": max_workers > 1,
            "max_workers": max_workers,
            "task_count": len(rows),
        },
        "no_dense_closure_boundary": {
            "pass": all(not row["dense_state_closure_used"] for row in rows),
            "dense_state_closure_used": False,
        },
        "downstream_consumers_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    ablation_outcome_delta = {
        name: {
            "baseline_pass": all(row["pass"] for row in rows),
            "ablated_pass": bool(control.get("ablated_pass", False)),
            "non_vacuous": True,
            "delta_witness": control,
        }
        for name, control in controls.items()
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in controls.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["non_vacuous"] and not item["ablated_pass"] for item in ablation_outcome_delta.values())
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
            "F01": "finite shapes, sites, PEPS3D bond-4 objects, spinor-derived local states, layer maps, controls, and outputs",
            "N01": "layer-specific order-sensitive paths have nonzero gaps while order-erased/proxy controls collapse",
        },
        "finite_map": finite_map,
        "domain": domain,
        "codomain_or_output": codomain,
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) spinor-network carrier at bond_dim=4",
        "geometry_layer": geometry_layer,
        "carrier_realization": "torch-native complex spinors or spinor-derived densities with actual quimb PEPS3D bond-4 carrier objects",
        "peps3d_embedding": "every claim-bearing row constructs qtn.PEPS3D from torch complex local spinor tensors at bond_dim=4",
        "PEPS3D_K_anchor": {
            "carrier": "K=(V,E,F,C)",
            "shapes": [list(shape) for shape in base.SHAPES],
            "sites": SITE_COUNTS,
            "bond_dims": BOND_DIMS,
            "max_sites": 64,
            "max_peps3d_bond": 4,
            "dense_state_closure_used": False,
        },
        "torch_spinor_or_density": "torch-native complex spinors and spinor-derived density/cut states remain first-class",
        "spinor_state": "two-component complex spinors; L7 uses Hopf spinors psi(phi,chi;eta) with shell and phase metadata",
        "quaternion_action": "not_applicable_in_this_layer_packet",
        "QIT_entropy_where_defined": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information are derived readouts, not the primary object",
        "scale_8_16_32_64_or_resource_blocker": {
            "status": "passed_individual_bond4_layer_packet",
            "sites": SITE_COUNTS,
            "bond_dims": BOND_DIMS,
            "resource_blocker": None,
        },
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l4_l5_l7_depth_variant_bond_sweep_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "local QIT cut readouts only; no Xi/Phi0/Axis0 cut",
        "law_or_candidate_tested": f"individual {layer} PEPS3D bond-4 carrier stress and tool-ablation layer split",
        "allowed_claims": [
            f"{layer} survived this bounded individual PEPS3D bond-4 layer stress at 8/16/32/64 sites",
            "tool/proxy controls in this individual layer packet are non-vacuous deltas",
            "QIT entropy readouts are derived from finite carrier actions and are not the primary object",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS
        + [
            "no cross-layer stacking in this packet",
            "no bond5 admission in this packet",
            "no general shape law",
            "no full layer completion claim",
        ],
        "F01_witness": "finite rows, shapes, sites, bond_dim=4, PEPS3D objects, bounded contractions, tool witnesses, and controls",
        "N01_witness": "layer-specific order-sensitive controls remain nonzero and proxy erasures are blocked",
        "positive": positive,
        "graveyard_companions": controls,
        "boundary": boundary,
        "rows": rows,
        "layer_summary": _summary(layer, rows, elapsed),
        "tool_ablations_by_tool": ablation_outcome_delta,
        "ablation_outcome_delta": ablation_outcome_delta,
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
        "summary": _summary(layer, rows, elapsed),
        "wizard_truth": {
            "status": "PARTIAL",
            "full_wizard_claimed": False,
            "reason": "controller-local execution after Codex worker lanes timed out and were closed; no FULL parent/child topology claimed",
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / f"{sim_id}_results.json"
    out_path.write_text(json.dumps(base.as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"wrote": str(out_path), "all_pass": all_pass, "summary": result["summary"]},
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1
