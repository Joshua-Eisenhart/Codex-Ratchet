#!/usr/bin/env python3
"""
sim_weyl_ambient_vs_engine_overlay.py
=====================================

Lane A discriminator for the Weyl-manifold shift.

Purpose
-------
Test whether the current executable stack supports a two-layer reading:

1. ambient manifold-side Weyl geometry is real and nontrivial
2. engine overlay / loop grammar is also real and nontrivial
3. raw local L|R remains a control-only object at initialization

This sim does NOT promote doctrine. It only checks whether the existing engine
supports a meaningful separation between ambient geometry variation and
engine-overlay variation.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np

classification = "canonical"

from engine_core import GeometricEngine
from geometric_operators import trace_distance_2x2
from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    hopf_map,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    torus_coordinates,
    torus_radii,
)
from proto_ratchet_sim_runner import EvidenceToken


RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "weyl_ambient_vs_engine_overlay_results.json",
)


def von_neumann_entropy(rho: np.ndarray) -> float:
    vals = np.real(np.linalg.eigvalsh((rho + rho.conj().T) / 2))
    vals = vals[vals > 1e-15]
    return float(-np.sum(vals * np.log2(vals))) if len(vals) else 0.0


def partial_trace_A(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def mutual_information(rho_ab: np.ndarray) -> float:
    rho_a = partial_trace_B(rho_ab)
    rho_b = partial_trace_A(rho_ab)
    return von_neumann_entropy(rho_a) + von_neumann_entropy(rho_b) - von_neumann_entropy(rho_ab)


def ambient_signature(eta: float, theta1: float = 0.0, theta2: float = 0.0) -> dict:
    q = torus_coordinates(eta, theta1, theta2)
    psi_L = left_weyl_spinor(q)
    psi_R = right_weyl_spinor(q)
    rho_L = left_density(q)
    rho_R = right_density(q)
    rho_pair = np.kron(rho_L, rho_R)
    base = hopf_map(q)
    R_major, R_minor = torus_radii(eta)
    overlap = abs(np.vdot(psi_L, psi_R))
    return {
        "eta": float(eta),
        "theta1": float(theta1),
        "theta2": float(theta2),
        "hopf_base": [float(x) for x in base],
        "R_major": float(R_major),
        "R_minor": float(R_minor),
        "rho_LR_trace_distance": float(trace_distance_2x2(rho_L, rho_R)),
        "spinor_overlap_abs": float(overlap),
        "raw_LR_mutual_information": float(mutual_information(rho_pair)),
    }


def run_engine_case(engine_type: int, eta: float, theta1: float = 0.0, theta2: float = 0.0) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    state0 = engine.init_state(eta=eta, theta1=theta1, theta2=theta2)
    axes_before = engine.read_axes(state0)
    state1 = engine.run_cycle(state0)
    axes_after = engine.read_axes(state1)
    axis_delta_l2 = float(
        np.linalg.norm(
            np.array([axes_after[k] - axes_before[k] for k in sorted(axes_before.keys())], dtype=float)
        )
    )
    return {
        "engine_type": engine_type,
        "axes_before": {k: float(v) for k, v in axes_before.items()},
        "axes_after": {k: float(v) for k, v in axes_after.items()},
        "axis_delta_l2": axis_delta_l2,
        "total_dphi_L": float(sum(h["dphi_L"] for h in state1.history)),
        "total_dphi_R": float(sum(h["dphi_R"] for h in state1.history)),
        "stages_run": int(len(state1.history)),
    }


def compare_axis_maps(a: dict, b: dict) -> dict:
    diffs = {k: float(abs(a[k] - b[k])) for k in a}
    return {
        "per_axis_abs_diff": diffs,
        "l2": float(np.linalg.norm(np.array(list(diffs.values()), dtype=float))),
        "max_abs_diff": float(max(diffs.values())),
    }


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    print("=" * 72)
    print("WEYL AMBIENT VS ENGINE OVERLAY")
    print("=" * 72)

    torus_cases = [
        ("inner", TORUS_INNER),
        ("clifford", TORUS_CLIFFORD),
        ("outer", TORUS_OUTER),
    ]

    cases = {
        "ambient_fixed_engine_varied": [],
        "engine_fixed_ambient_varied": [],
        "guardrail": [],
    }

    # A. Hold ambient geometry fixed; vary engine overlay via engine_type.
    overlay_nontrivial_count = 0
    for name, eta in torus_cases:
        ambient = ambient_signature(eta)
        type1 = run_engine_case(engine_type=1, eta=eta)
        type2 = run_engine_case(engine_type=2, eta=eta)
        diff = compare_axis_maps(type1["axes_after"], type2["axes_after"])
        nontrivial = diff["max_abs_diff"] > 1e-4
        overlay_nontrivial_count += int(nontrivial)
        cases["ambient_fixed_engine_varied"].append({
            "torus": name,
            "ambient_signature": ambient,
            "engine_type_1": type1,
            "engine_type_2": type2,
            "axes_after_diff": diff,
            "overlay_nontrivial": nontrivial,
        })

    # B. Hold engine overlay fixed; vary ambient torus placement.
    fixed_overlay_cases = []
    for name, eta in torus_cases:
        ambient = ambient_signature(eta)
        fixed_overlay_cases.append({
            "torus": name,
            "ambient_signature": ambient,
            "engine_type_1": run_engine_case(engine_type=1, eta=eta),
        })
    cases["engine_fixed_ambient_varied"] = fixed_overlay_cases

    ambient_pairwise = []
    ambient_nontrivial_count = 0
    for i in range(len(fixed_overlay_cases)):
        for j in range(i + 1, len(fixed_overlay_cases)):
            a = fixed_overlay_cases[i]
            b = fixed_overlay_cases[j]
            diff = compare_axis_maps(a["engine_type_1"]["axes_after"], b["engine_type_1"]["axes_after"])
            ambient_changed = diff["max_abs_diff"] > 1e-4
            ambient_nontrivial_count += int(ambient_changed)
            ambient_pairwise.append({
                "pair": [a["torus"], b["torus"]],
                "axes_after_diff": diff,
                "ambient_nontrivial": ambient_changed,
            })
    cases["engine_fixed_ambient_varied_pairwise"] = ambient_pairwise

    # C. Guardrail: raw local L|R should stay MI-trivial at initialization.
    guardrail_ok = True
    max_raw_mi = 0.0
    for name, eta in torus_cases:
        ambient = ambient_signature(eta)
        raw_mi = ambient["raw_LR_mutual_information"]
        max_raw_mi = max(max_raw_mi, raw_mi)
        ok = raw_mi < 1e-9
        guardrail_ok = guardrail_ok and ok
        cases["guardrail"].append({
            "torus": name,
            "raw_LR_mutual_information": raw_mi,
            "pass": ok,
        })

    overlay_pass = overlay_nontrivial_count >= 2
    ambient_pass = ambient_nontrivial_count >= 2
    overall_pass = overlay_pass and ambient_pass and guardrail_ok

    summary = {
        "overlay_nontrivial_count": overlay_nontrivial_count,
        "overlay_pass": overlay_pass,
        "ambient_nontrivial_count": ambient_nontrivial_count,
        "ambient_pass": ambient_pass,
        "guardrail_pass": guardrail_ok,
        "max_raw_LR_mutual_information": max_raw_mi,
    }

    verdict = {
        "result": "PASS" if overall_pass else "KILL",
        "read": (
            "Current executable stack supports a nontrivial separation between ambient geometry variation "
            "and engine-overlay variation while keeping raw local L|R control-only at initialization."
            if overall_pass
            else
            "Current executable stack does not yet support a clean ambient-vs-overlay separation under this discriminator."
        ),
    }

    token = EvidenceToken(
        token_id="E_SIM_WEYL_AMBIENT_ENGINE_SPLIT_OK" if overall_pass else "",
        sim_spec_id="S_SIM_WEYL_AMBIENT_ENGINE_SPLIT",
        status="PASS" if overall_pass else "KILL",
        measured_value=float(overlay_nontrivial_count + ambient_nontrivial_count),
        kill_reason=None if overall_pass else "AMBIENT_OVERLAY_DISCRIMINATOR_NOT_STRONG_ENOUGH",
    )

    results = {
        "metadata": {
            "name": "weyl_ambient_vs_engine_overlay",
            "timestamp": datetime.now(UTC).isoformat(),
            "results_path": RESULTS_PATH,
        },
        "cases": cases,
        "summary": summary,
        "verdict": verdict,
        "evidence_token": asdict(token),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nSummary")
    print(f"  Overlay-nontrivial cases: {overlay_nontrivial_count}/3")
    print(f"  Ambient-nontrivial pairs: {ambient_nontrivial_count}/3")
    print(f"  Max raw L|R MI at init: {max_raw_mi:.6e}")
    print("\nVerdict")
    print(f"  {verdict['result']}: {verdict['read']}")
    print(f"\nResults saved: {RESULTS_PATH}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
