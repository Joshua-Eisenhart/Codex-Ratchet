#!/usr/bin/env python3
"""
sim_weyl_delta_packet.py
========================

Emit raw pre-Axis Weyl-side delta surfaces without canonizing any final
"flux" doctrine object.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from engine_core import (
    GeometricEngine,
    STAGES,
    StageControls,
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
)
from geometric_operators import trace_distance_2x2


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "weyl_delta_packet_results.json"


def wrapped_delta(theta_after: float, theta_before: float) -> float:
    return float(np.arctan2(np.sin(theta_after - theta_before), np.cos(theta_after - theta_before)))


def torus_label(eta: float) -> str:
    if abs(eta - TORUS_INNER) < 1e-8:
        return "inner"
    if abs(eta - TORUS_CLIFFORD) < 1e-8:
        return "clifford"
    if abs(eta - TORUS_OUTER) < 1e-8:
        return "outer"
    return "unknown"


def stage_controls() -> dict[int, StageControls]:
    torus_values = [
        TORUS_INNER,
        TORUS_CLIFFORD,
        TORUS_OUTER,
        TORUS_CLIFFORD,
        TORUS_OUTER,
        TORUS_CLIFFORD,
        TORUS_INNER,
        TORUS_CLIFFORD,
    ]
    return {
        i: StageControls(
            piston=0.8,
            lever=(i % 2 == 0),
            torus=torus_values[i],
            spinor="both",
        )
        for i in range(8)
    }


def state_row(engine: GeometricEngine, before, after, terrain: dict) -> dict:
    bloch_before_L = before.bloch_L()
    bloch_before_R = before.bloch_R()
    bloch_after_L = after.bloch_L()
    bloch_after_R = after.bloch_R()
    chirality_before = trace_distance_2x2(before.rho_L, before.rho_R)
    chirality_after = trace_distance_2x2(after.rho_L, after.rho_R)
    history_row = after.history[-1]
    return {
        "terrain_name": terrain["name"],
        "terrain_loop": terrain["loop"],
        "terrain_topology": terrain["topo"],
        "loop_position": after.loop_position,
        "loop_role": after.loop_role,
        "seat_before": torus_label(before.eta),
        "seat_after": torus_label(after.eta),
        "eta_before": float(before.eta),
        "eta_after": float(after.eta),
        "delta_eta": float(after.eta - before.eta),
        "theta1_before": float(before.theta1),
        "theta1_after": float(after.theta1),
        "theta2_before": float(before.theta2),
        "theta2_after": float(after.theta2),
        "delta_theta1": wrapped_delta(after.theta1, before.theta1),
        "delta_theta2": wrapped_delta(after.theta2, before.theta2),
        "delta_rho_L_frob": float(np.linalg.norm(after.rho_L - before.rho_L)),
        "delta_rho_R_frob": float(np.linalg.norm(after.rho_R - before.rho_R)),
        "delta_bloch_L_norm": float(np.linalg.norm(bloch_after_L - bloch_before_L)),
        "delta_bloch_R_norm": float(np.linalg.norm(bloch_after_R - bloch_before_R)),
        "delta_bloch_differential_norm": float(np.linalg.norm((bloch_after_L - bloch_before_L) - (bloch_after_R - bloch_before_R))),
        "chirality_before": float(chirality_before),
        "chirality_after": float(chirality_after),
        "delta_chirality": float(chirality_after - chirality_before),
        "ga0_before": float(history_row["ga0_before"]),
        "ga0_after": float(history_row["ga0_after"]),
        "delta_ga0": float(history_row["ga0_after"] - history_row["ga0_before"]),
        "compat_dphi_L": float(history_row["dphi_L"]),
        "compat_dphi_R": float(history_row["dphi_R"]),
        "compat_dphi_gap": float(history_row["dphi_L"] - history_row["dphi_R"]),
        "const_sat": float(history_row["const_sat"]),
    }


def summarize_rows(rows: list[dict]) -> dict:
    def count(pred) -> int:
        return int(sum(1 for row in rows if pred(row)))

    loop_counts: dict[str, int] = {}
    seat_transition_counts: dict[str, int] = {}
    for row in rows:
        loop_counts[row["terrain_loop"]] = loop_counts.get(row["terrain_loop"], 0) + 1
        key = f'{row["seat_before"]}->{row["seat_after"]}'
        seat_transition_counts[key] = seat_transition_counts.get(key, 0) + 1

    transport_active = count(lambda row: abs(row["delta_eta"]) > 1e-6 or abs(row["delta_theta1"]) > 1e-6 or abs(row["delta_theta2"]) > 1e-6)
    chirality_active = count(lambda row: abs(row["delta_chirality"]) > 1e-4)
    lr_state_asymmetry = count(lambda row: abs(row["delta_rho_L_frob"] - row["delta_rho_R_frob"]) > 1e-4)
    lr_bloch_asymmetry = count(lambda row: row["delta_bloch_differential_norm"] > 1e-4)
    nonzero_delta_ga0 = count(lambda row: abs(row["delta_ga0"]) > 1e-6)

    return {
        "rows": len(rows),
        "transport_active_count": transport_active,
        "chirality_active_count": chirality_active,
        "lr_state_asymmetry_count": lr_state_asymmetry,
        "lr_bloch_asymmetry_count": lr_bloch_asymmetry,
        "nonzero_delta_ga0_count": nonzero_delta_ga0,
        "max_abs_delta_eta": float(max(abs(row["delta_eta"]) for row in rows)),
        "max_abs_delta_theta1": float(max(abs(row["delta_theta1"]) for row in rows)),
        "max_abs_delta_theta2": float(max(abs(row["delta_theta2"]) for row in rows)),
        "mean_abs_delta_chirality": float(np.mean([abs(row["delta_chirality"]) for row in rows])),
        "mean_delta_rho_L_frob": float(np.mean([row["delta_rho_L_frob"] for row in rows])),
        "mean_delta_rho_R_frob": float(np.mean([row["delta_rho_R_frob"] for row in rows])),
        "mean_delta_bloch_L_norm": float(np.mean([row["delta_bloch_L_norm"] for row in rows])),
        "mean_delta_bloch_R_norm": float(np.mean([row["delta_bloch_R_norm"] for row in rows])),
        "max_abs_compat_dphi_gap": float(max(abs(row["compat_dphi_gap"]) for row in rows)),
        "loop_counts": loop_counts,
        "seat_transition_counts": seat_transition_counts,
    }


def placement_hints(summary: dict) -> dict:
    return {
        "geometric_transport_delta": "pre-axis" if summary["transport_active_count"] > 0 else "not_owner_worthy",
        "chirality_differential_delta": "pre-axis" if summary["chirality_active_count"] > 0 else "not_owner_worthy",
        "bloch_differential_delta": "pre-axis" if summary["lr_bloch_asymmetry_count"] > 0 else "not_owner_worthy",
        "entropic_left_right_flux": "unresolved_not_owner_worthy_yet",
        "post_joint_cut_flux": "axis_internal_or_cross_axis",
    }


def flux_candidate_status(summary: dict) -> dict:
    return {
        "geometric_transport_flux": "candidate_ready" if summary["transport_active_count"] > 0 else "not_ready",
        "bloch_current_flux": "candidate_ready" if summary["lr_bloch_asymmetry_count"] > 0 else "not_ready",
        "chirality_differential_flux": "candidate_ready" if summary["chirality_active_count"] > 0 else "not_ready",
        "entropic_left_right_flux": "blocked_by_symmetric_compat_shim",
        "post_joint_cut_flux": "downstream_existing_branch",
    }


def branch_map(summary: dict) -> dict:
    return {
        "single_weyl_flux_object": {
            "status": "not_supported_yet",
            "reason": "current evidence resolves a compound delta family, not one isolated owner-worthy flux object",
        },
        "chirality_separated_transport_deltas": {
            "status": "surviving_pre_axis_candidate",
            "reason": "transport, chirality, and Bloch differential deltas are all mechanically active before Axis 0 readout",
        },
        "raw_delta_packet": {
            "status": "diagnostic_pre_axis_surface",
            "reason": "the packet surfaces pre-Axis objects without promoting them to final owner law",
        },
        "entropic_left_right_flux": {
            "status": "blocked",
            "reason": "runtime dphi_L/dphi_R are symmetric compatibility shims",
        },
        "post_joint_cut_flux": {
            "status": "downstream_branch",
            "reason": "cut/coupling flux depends on rho_AB and later bridge/readout structure",
        },
        "compound_owner_phrase_candidate": {
            "status": "survives_better_than_single_flux",
            "phrase": "chirality-separated loop-sensitive transport deltas",
            "support_rows": summary["transport_active_count"],
        },
    }


def pre_axis_object_inventory(summary: dict) -> dict:
    return {
        "hopf_carrier_point": {
            "status": "live_pre_axis_geometry",
            "math": "q in S^3",
        },
        "nested_torus_seat": {
            "status": "live_pre_axis_geometry",
            "math": "eta, theta1, theta2 with seat labels inner/clifford/outer",
        },
        "weyl_sheet_pair": {
            "status": "live_pre_axis_refinement",
            "math": "(psi_L(q), psi_R(q)) and (rho_L, rho_R)",
        },
        "loop_sensitive_transport_surface": {
            "status": "live_pre_axis_candidate",
            "math": "delta_eta, delta_theta1, delta_theta2 with base/fiber loop ownership",
            "support_rows": summary["transport_active_count"],
        },
        "chirality_differential_surface": {
            "status": "live_pre_axis_candidate",
            "math": "delta trace_distance(rho_L, rho_R)",
            "support_rows": summary["chirality_active_count"],
        },
        "bloch_differential_surface": {
            "status": "live_pre_axis_candidate",
            "math": "delta r_L - delta r_R",
            "support_rows": summary["lr_bloch_asymmetry_count"],
        },
        "raw_delta_packet": {
            "status": "diagnostic_surface_not_final_owner_law",
            "math": "stagewise before/after packet",
        },
        "bridge_ready_cut_object": {
            "status": "downstream_not_pre_axis",
            "math": "rho_AB / Xi / signed cut metrics",
        },
    }


def transport_embargo_boundary(summary: dict) -> dict:
    return {
        "object": "transport_embargo_boundary",
        "status": "candidate_pre_axis_law_not_owner_promoted",
        "surviving_candidate": "chirality_separated_transport_deltas",
        "lower_tier_law": "exact_loop_assigned_transport_only",
        "blocked_flux": "entropic_left_right_flux",
        "blocked_flux_reason": "blocked_by_symmetric_compat_shim",
        "unsupported_single_flux": "single_weyl_flux_object",
        "unsupported_single_flux_status": "not_supported_yet",
        "downstream_branch": "post_joint_cut_flux",
        "downstream_branch_status": "downstream_existing_branch",
        "promotion_boundary": "awaiting_owner_promotion_decision_after_nonproxy_support",
        "support_rows": {
            "transport_active_count": int(summary["transport_active_count"]),
            "chirality_active_count": int(summary["chirality_active_count"]),
            "lr_bloch_asymmetry_count": int(summary["lr_bloch_asymmetry_count"]),
        },
    }


def run_case(engine_type: int, init_eta: float, theta1: float, theta2: float) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    controls = stage_controls()
    state = engine.init_state(eta=init_eta, theta1=theta1, theta2=theta2, rng=np.random.default_rng(42))
    rows = []
    for stage_idx, terrain_idx in enumerate(engine.stages and range(8)):
        before = state
        state = engine.step(state, stage_idx=terrain_idx, controls=controls[stage_idx])
        rows.append(state_row(engine, before, state, STAGES[terrain_idx]))
    summary = summarize_rows(rows)
    return {
        "engine_type": engine_type,
        "initial_seat": torus_label(init_eta),
        "rows": rows,
        "summary": summary,
    }


def main() -> int:
    cases = []
    for engine_type in (1, 2):
        for eta in (TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER):
            cases.append(run_case(engine_type, eta, theta1=0.3, theta2=1.1))

    case_map = {f't{case["engine_type"]}_{case["initial_seat"]}': case for case in cases}
    all_rows = [row for case in cases for row in case["rows"]]
    global_summary = summarize_rows(all_rows)
    payload = {
        "name": "weyl_delta_packet_results",
        "timestamp": datetime.now(UTC).isoformat(),
        "cases": case_map,
        "global_summary": global_summary,
        "placement_hints": placement_hints(global_summary),
        "flux_candidate_status": flux_candidate_status(global_summary),
        "branch_map": branch_map(global_summary),
        "pre_axis_object_inventory": pre_axis_object_inventory(global_summary),
        "transport_embargo_boundary": transport_embargo_boundary(global_summary),
        "owner_read": {
            "delta_packet_status": "raw_pre_axis_objects_only",
            "note": "This packet exposes stagewise geometry/chirality deltas without promoting a final flux doctrine.",
        },
    }
    SIM_RESULTS.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
