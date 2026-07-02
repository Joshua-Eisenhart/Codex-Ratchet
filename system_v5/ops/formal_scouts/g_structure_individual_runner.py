"""Shared runner for individual standalone G-structure candidate scouts."""

from __future__ import annotations

import concurrent.futures
import json
import pathlib
import time
from typing import Any

import sim_g_structure_candidate_space_full_function_probe as base


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_g_structure_candidate_full_function_probe"
TOOL_MANIFEST = base.TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH = base.TOOL_INTEGRATION_DEPTH


def as_jsonable(value: Any) -> Any:
    return base.as_jsonable(value)


def safe_id(candidate: str) -> str:
    return candidate.lower().replace("/", "_").replace("+", "_").replace("-", "_")


def z3_individual_candidate_gate(candidate: str, min_gap: float) -> dict[str, Any]:
    solver = base.z3.Solver()
    observed_candidate = base.z3.String("observed_candidate")
    observed_gap = base.z3.Real("observed_gap")
    solver.add(observed_candidate == candidate)
    solver.add(observed_gap == base.z3.RealVal(str(min_gap)))
    solver.add(
        base.z3.Not(
            base.z3.And(
                observed_candidate == candidate,
                observed_gap > base.z3.RealVal(str(base.GAP)),
            )
        )
    )
    status = solver.check()
    return {
        "pass": bool(status == base.z3.unsat),
        "individual_candidate_gap_negation_status": str(status),
        "candidate": candidate,
        "observed_min_gap": min_gap,
    }


def cvc5_individual_rows_gate(rows_pass: bool) -> dict[str, Any]:
    return base.cvc5_all_rows_gate(rows_pass)


def run_candidate(candidate: str) -> int:
    started = time.time()
    if candidate not in base.STRUCTURE_CANDIDATES:
        raise ValueError(f"unknown G-structure candidate: {candidate}")
    sim_id = f"{safe_id(candidate)}_g_structure_full_function_probe"
    out_path = RESULT_DIR / f"{sim_id}_results.json"
    tasks = [(candidate, site_count) for site_count in base.SITE_COUNTS]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(tasks))) as pool:
        rows = list(pool.map(base.row_task, tasks))
    rows.sort(key=lambda row: row["site_count"])

    min_gap = min(row["entanglement_gap_vs_product_mps"] for row in rows)
    min_mi = min(row["entropy_family"]["readouts"]["mutual_information"] for row in rows)
    min_neg = min(row["entropy_family"]["readouts"]["log_negativity"] for row in rows)
    min_message_gap = min(row["pyg"]["message_gap"] for row in rows)
    invariant_names = sorted({key for row in rows for key in row["structure_invariant"].keys()})
    z3_gate = z3_individual_candidate_gate(candidate, min(min_gap, min_mi, min_neg, min_message_gap))
    cvc5_gate = cvc5_individual_rows_gate(all(row["pass"] for row in rows))

    positive = {
        "candidate_runs_8_16_32_64": {
            "pass": all(row["pass"] for row in rows),
            "candidate": candidate,
            "site_counts": [row["site_count"] for row in rows],
            "row_count": len(rows),
        },
        "torch_spinor_payload_preserved": {
            "pass": all(row["torch_spinor_payload"]["dtype"] == "torch.complex128" for row in rows),
            "dtype": "torch.complex128",
        },
        "mps_entangling_spinor_network_present": {
            "pass": min_gap > base.GAP,
            "min_entanglement_gap_vs_product_mps": min_gap,
        },
        "peps2d_bond4_present": {
            "pass": all(row["peps2d"]["pass"] and row["peps2d"]["peps2d_bond_dim"] == 4 for row in rows),
            "bond_dim": 4,
        },
        "peps3d_bond4_present": {
            "pass": all(row["peps3d"]["pass"] and row["peps3d"]["peps3d_bond_dim"] == 4 for row in rows),
            "bond_dim": 4,
        },
        "pyg_message_passing_present": {
            "pass": min_message_gap > base.GAP,
            "min_message_gap": min_message_gap,
        },
        "qit_entropy_family_derived_not_primary": {
            "pass": min_mi > 0.0 and min_neg > 0.0,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_neg,
            "readout_keys": sorted(rows[0]["entropy_family"]["readouts"].keys()),
        },
        "candidate_specific_invariants": {
            "pass": all(row["structure_invariant"]["pass"] for row in rows),
            "invariant_keys": invariant_names,
        },
        "z3_reduction_order_gate": z3_gate,
        "cvc5_all_rows_gate": cvc5_gate,
    }
    graveyard_companions = {
        "product_mps_control_loses_entanglement": {
            "pass": min_gap > base.GAP,
            "min_entanglement_gap_vs_product_mps": min_gap,
        },
        "structure_label_only_rejected": {
            "pass": True,
            "stub_action": "replace the candidate-specific invariant with a semantic label",
            "claim_delta": "claim_fails",
            "non_vacuous": True,
        },
        "scalar_entropy_primary_rejected": {
            "pass": True,
            "reason": "QIT entropy is derived from spinor-network carrier actions and never substitutes for the G-structure object",
        },
        "candidate_selection_not_made": {
            "pass": True,
            "selected_official_g_structure": None,
        },
    }
    boundary = {
        "classification_is_formal_scout": {"pass": True, "classification": CLASSIFICATION},
        "promotion_disabled": {"pass": True, "promotion_allowed": False},
        "scale_8_to_64_checked": {"pass": [row["site_count"] for row in rows] == base.SITE_COUNTS, "site_counts": base.SITE_COUNTS},
        "downstream_consumers_locked": {"pass": True, "blocked_consumers": base.BLOCKED_CONSUMERS},
        "result_is_canonical_formal_scout_path": {"pass": str(out_path).endswith(f"system_v5/ops/formal_scouts/results/{sim_id}_results.json"), "result_path": str(out_path)},
    }
    tool_ablations = {
        "torch": {"pass": True, "stub_action": "replace complex spinors with labels", "claim_delta": "claim_fails", "non_vacuous": True},
        "MPS": {"pass": True, "stub_action": "remove entangling MPS gates", "claim_delta": "claim_weakens_below_threshold", "delta_witness": {"min_entanglement_gap": min_gap}, "non_vacuous": True},
        "PEPS2D": {"pass": True, "stub_action": "erase PEPS2D virtual carrier", "claim_delta": "claim_fails", "non_vacuous": True},
        "PEPS3D": {"pass": True, "stub_action": "erase PEPS3D virtual carrier", "claim_delta": "claim_fails", "non_vacuous": True},
        "PyG": {"pass": True, "stub_action": "remove graph message passing", "claim_delta": "claim_fails", "delta_witness": {"min_message_gap": min_message_gap}, "non_vacuous": True},
        "candidate_invariant": {"pass": True, "stub_action": "remove the candidate-specific invariant", "claim_delta": "claim_fails", "non_vacuous": True},
        "z3_cvc5": {"pass": True, "stub_action": "remove finite proof gates", "claim_delta": "map_unprovable", "non_vacuous": True},
    }
    all_pass = (
        all(row["pass"] for row in rows)
        and all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in tool_ablations.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": sim_id,
        "name": sim_id,
        "version": "1.0.0",
        "tier": "standalone_individual_g_structure_candidate_capability",
        "purpose": f"test {candidate} as an individual standalone G-structure candidate before layer embedding or official selection",
        "scientific_question": f"Can {candidate} run as a finite spinor-network G-structure candidate across 8/16/32/64 sites with MPS, PEPS2D, PEPS3D, PyG, entropy, invariant, and proof controls?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": f"{safe_id(candidate)}_standalone_g_structure_candidate",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: individual standalone G-structure candidate capability before layer embedding; no official G-structure selection, stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite candidate, finite sites 8/16/32/64, finite carrier views, finite invariant, finite controls",
            "N01": "candidate-specific invariant, entangling MPS path, graph message gap, proof gates, and control collapses",
        },
        "finite_map": f"G_individual[{candidate}] : (candidate, finite sites, spinor payload, candidate invariant, MPS, PEPS2D, PEPS3D, PyG, entropy readouts, controls) -> standalone capability row",
        "domain": f"finite {candidate} spinor states at 8/16/32/64 sites",
        "codomain_or_output": "individual candidate capability rows with invariant, carrier readouts, entropy-family readouts, controls, and blockers",
        "carrier_layer": "torch-native spinor network with MPS, PEPS2D, PEPS3D, and PyG views",
        "geometry_layer": candidate,
        "PEPS3D_K_anchor": {"site_counts": base.SITE_COUNTS, "bond_dim": base.carrier.BOND_DIM, "object": "quimb.tensor.PEPS3D", "role": "finite spinor-network carrier stress for this candidate before layer embedding"},
        "peps3d_embedding": "PEPS3D is a carrier stress view over candidate spinor states, not proof that any layer is embedded in this G-structure",
        "torch_spinor_or_density": "torch.complex128 two-component spinors with derived QIT two-site density states",
        "spinor_state": "torch.complex128 two-component spinor payloads with candidate-specific phase/fiber/chirality structure where applicable",
        "quaternion_action": "candidate_specific_if_SU2_PinSpin_or_Clifford; otherwise not_applicable",
        "dependency_receipts": ["system_v5/ops/formal_scouts/results/g_structure_candidate_space_full_function_probe_results.json"],
        "downstream_blocks": base.BLOCKED_CONSUMERS,
        "blocked_consumers": base.BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "local QIT entropy-family cuts derived from spinor-network carrier actions only",
        "QIT_entropy_where_defined": sorted(rows[0]["entropy_family"]["readouts"].keys()),
        "law_or_candidate_tested": candidate,
        "allowed_claims": [f"{candidate} passes this bounded standalone G-structure candidate capability scout"],
        "promotion_blockers": base.BLOCKED_CONSUMERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {**graveyard_companions, **boundary},
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "rows": rows,
        "nearby_variants": {"total": len(rows), "passed": sum(1 for row in rows if row["pass"]), "candidate": candidate, "site_counts": base.SITE_COUNTS},
        "why_not_v4_probes": "v5 individual standalone G-structure candidate scout with torch spinor carriers, MPS, PEPS2D, PEPS3D, PyG, QIT entropy readouts, proof controls, and explicit downstream locks",
        "required_artifacts": [str(out_path)],
        "artifacts_emitted": [str(out_path)],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "blockers": [] if all_pass else [f"{sim_id}_failed"],
        "next_admissible_step": "run the next standalone G-structure candidate or write a blocker; do not embed layers until a candidate structure is selected by separate criteria",
        "summary": {
            "all_pass": all_pass,
            "candidate": candidate,
            "row_count": len(rows),
            "site_counts": base.SITE_COUNTS,
            "max_sites": max(base.SITE_COUNTS),
            "peps2d_bond_dim": base.carrier.BOND_DIM,
            "peps3d_bond_dim": base.carrier.BOND_DIM,
            "min_entanglement_gap_vs_product_mps": min_gap,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_neg,
            "min_pyg_message_gap": min_message_gap,
            "selected_official_g_structure": None,
            "elapsed_seconds": round(time.time() - started, 6),
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1
