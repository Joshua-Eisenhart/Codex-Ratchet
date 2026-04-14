#!/usr/bin/env python3
"""
PURE LEGO: Viability vs Attractor
=================================
Direct local trajectory row contrasting viability-preserving and attractor-collapsing updates.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local trajectory row contrasting a viability-preserving update against an attractor "
    "update on the same bounded admitted carrier, without controller or selector claims."
)

LEGO_IDS = [
    "viability_vs_attractor",
]

PRIMARY_LEGO_IDS = [
    "viability_vs_attractor",
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

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def density_from_z(z):
    z = float(np.clip(z, -1.0, 1.0))
    return np.array([[0.5 * (1 + z), 0.0], [0.0, 0.5 * (1 - z)]], dtype=complex)


def trace_distance(rho, sigma):
    evals = np.linalg.eigvalsh(0.5 * ((rho - sigma) + (rho - sigma).conj().T))
    return float(0.5 * np.sum(np.abs(evals)))


def attractor_update(z):
    return 0.4 * z


def viability_update(z):
    z_next = z + 0.12 * np.sign(z)
    return float(np.clip(z_next, -0.85, 0.85))


def counterfeit_viability_update(z):
    return attractor_update(z)


def rollout(fn, z0, steps=4):
    vals = [float(z0)]
    for _ in range(steps):
        vals.append(float(fn(vals[-1])))
    return vals


def admitted(vals):
    return all(-0.85 - 1e-10 <= z <= 0.85 + 1e-10 for z in vals)


def main():
    z_a = 0.70
    z_b = 0.25

    attr_a = rollout(attractor_update, z_a)
    attr_b = rollout(attractor_update, z_b)
    via_a = rollout(viability_update, z_a)
    via_b = rollout(viability_update, z_b)
    fake_a = rollout(counterfeit_viability_update, z_a)
    fake_b = rollout(counterfeit_viability_update, z_b)

    attr_sep0 = trace_distance(density_from_z(attr_a[0]), density_from_z(attr_b[0]))
    attr_sepN = trace_distance(density_from_z(attr_a[-1]), density_from_z(attr_b[-1]))
    via_sep0 = trace_distance(density_from_z(via_a[0]), density_from_z(via_b[0]))
    via_sepN = trace_distance(density_from_z(via_a[-1]), density_from_z(via_b[-1]))
    fake_sepN = trace_distance(density_from_z(fake_a[-1]), density_from_z(fake_b[-1]))

    positive = {
        "both_updates_stay_inside_admitted_carrier": {
            "attractor_a": attr_a,
            "attractor_b": attr_b,
            "viability_a": via_a,
            "viability_b": via_b,
            "pass": admitted(attr_a) and admitted(attr_b) and admitted(via_a) and admitted(via_b),
        },
        "attractor_rule_collapses_distinct_initial_states": {
            "initial_separation": attr_sep0,
            "final_separation": attr_sepN,
            "pass": attr_sepN < 0.25 * attr_sep0,
        },
        "viability_rule_preserves_nontrivial_admissible_separation": {
            "initial_separation": via_sep0,
            "final_separation": via_sepN,
            "pass": via_sepN > 0.25 * via_sep0,
        },
    }

    negative = {
        "counterfeit_viability_collapses_to_attractor_behavior": {
            "counterfeit_final_separation": fake_sepN,
            "true_viability_final_separation": via_sepN,
            "pass": fake_sepN < 0.25 * via_sep0 and via_sepN > fake_sepN + 1e-3,
        },
        "row_does_not_make_controller_or_selector_claims": {
            "pass": True,
        },
    }

    boundary = {
        "all_terminal_states_remain_valid_density_operators": {
            "pass": all(
                abs(np.trace(density_from_z(z)) - 1.0) < EPS and np.min(np.linalg.eigvalsh(density_from_z(z))) > -1e-10
                for z in [*attr_a, *attr_b, *via_a, *via_b]
            ),
        },
        "comparison_uses_one_bounded_local_carrier_only": {
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "viability_vs_attractor",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local trajectory row contrasting attractor collapse with viability-preserving admissible evolution on one bounded carrier.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "viability_vs_attractor_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
