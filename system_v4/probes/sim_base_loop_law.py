#!/usr/bin/env python3
"""
PURE LEGO: Base Loop Law
========================
Direct local base-loop lego on one fixed Hopf-style sample.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: base-loop law is validated here as a "
    "pure numpy lego on one fixed sample, not a canonical nonclassical witness."
)
CLASSIFICATION_NOTE = divergence_log


EPS = 1e-10
CLASSIFICATION = "canonical"

LEGO_IDS = [
    "base_loop_law",
]

PRIMARY_LEGO_IDS = [
    "base_loop_law",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite array/matrix computation for this bounded classical lego receipt",
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def spinor(alpha):
    # simple lifted base loop sample: sigma_y rotation of |0>
    return np.array([np.cos(alpha / 2.0), np.sin(alpha / 2.0)], dtype=complex)


def density(psi):
    psi = np.array(psi, dtype=complex).reshape(-1, 1)
    return psi @ psi.conj().T


def fiber_spinor(theta, phase0=0.0):
    return np.exp(1j * (phase0 + theta)) * np.array([1.0, 0.0], dtype=complex)


def main():
    alphas = [0.0, np.pi / 2.0, np.pi, 2.0 * np.pi]
    base_states = [density(spinor(a)) for a in alphas]
    fiber_states = [density(fiber_spinor(t)) for t in [0.0, np.pi / 2.0, np.pi, 2.0 * np.pi]]

    start, quarter, half, end = base_states
    fiber_start, fiber_mid, _, fiber_end = fiber_states

    positive = {
        "closed_base_loop_is_well_defined": {
            "pass": np.allclose(end, start, atol=EPS),
        },
        "density_changes_along_base_motion": {
            "start_to_quarter": float(np.linalg.norm(start - quarter)),
            "start_to_half": float(np.linalg.norm(start - half)),
            "pass": np.linalg.norm(start - quarter) > 1e-3 and np.linalg.norm(start - half) > 1e-3,
        },
        "base_loop_returns_to_same_density_class_on_closure": {
            "pass": np.allclose(end, start, atol=EPS),
        },
    }

    negative = {
        "nontrivial_variation_exists_inside_base_loop": {
            "pass": not np.allclose(start, quarter, atol=EPS) and not np.allclose(quarter, half, atol=EPS),
        },
        "base_vs_fiber_contrast_is_visible": {
            "fiber_start_to_mid": float(np.linalg.norm(fiber_start - fiber_mid)),
            "pass": np.allclose(fiber_start, fiber_mid, atol=EPS) and np.linalg.norm(start - quarter) > 1e-3,
        },
    }

    boundary = {
        "all_sampled_states_stay_normalized": {
            "pass": all(abs(np.trace(rho) - 1.0) < EPS for rho in base_states + fiber_states),
        },
        "reparameterization_endpoints_do_not_change_loop_law": {
            "pass": np.allclose(density(spinor(4.0 * np.pi)), start, atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "base_loop_law",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission",
        "next_lego_target": "Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.",
        "promotion_condition": "Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.",
        "blocked_until": "tool-lego fit; coupling/coexistence evidence; stage-gate admission",
        "demotion_condition": "Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof"],
        "all_pass": all_pass,
        "criteria_checked": ["finite computation completed", "load-bearing numpy path exercised", "local pass/fail criteria satisfied"],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local base-loop lego on one fixed sample showing density traversal and closure.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "base_loop_law_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
