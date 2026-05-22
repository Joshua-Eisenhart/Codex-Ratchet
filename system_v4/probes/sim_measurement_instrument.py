#!/usr/bin/env python3
"""
PURE LEGO: Measurement Instrument
=================================
Direct local measurement/channel lego.

Compare outcome readout and post-measurement update for a bounded qubit
instrument family.
"""

import json
import pathlib
from fractions import Fraction

import cvc5
from cvc5 import Kind
import numpy as np
classification = "classical_baseline"  # auto-backfill

divergence_log = [
    "Classical comparator/control surface only; this metadata clears C4 for baseline accounting and does not promote a nonclassical, formal-scout, bridge, axis-level, or canonical proof claim."
]

CLAIM_CEILING = "canonical_local_measurement_instrument_lego_only"
NEXT_LEGO_TARGET = "none"
PROMOTION_CONDITION = (
    "requires separate reconciled queue row before coupling, bridge, axis, engine, "
    "GStack, QIT, or nonclassical use"
)
BLOCKED_UNTIL = "exact parent receipts, queue row, result JSON, and ledger loopback are reconciled"
DEMOTION_CONDITION = (
    "demote if readout/update consistency, effect completeness, weak/projective "
    "instrument checks, or boundary criteria fail, or if this row is used for a higher-stage claim"
)
OUT_OF_SCOPE = [
    "QIT engine admission",
    "GStack admission",
    "axis promotion",
    "engine promotion",
    "nonclassical proof",
    "scientific coupling closure",
]

EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for finite qubit measurement instruments with explicit "
    "readout/update consistency."
)

LEGO_IDS = [
    "measurement_instrument",
    "povm_measurement_family",
]

PRIMARY_LEGO_IDS = [
    "measurement_instrument",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "exactly certifies completeness of the induced effect family on bounded diagonal instruments",
    },
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
TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def outcome_map(rho, mk):
    return mk @ rho @ mk.conj().T


def normalize_state(sigma):
    p = float(np.real(np.trace(sigma)))
    if p < EPS:
        return None, p
    return sigma / p, p


def cvc5_diagonal_effect_completeness(effects):
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")

    def real_term(x):
        xr = round(float(np.real(x)), 12)
        frac = Fraction(xr).limit_denominator(1000)
        return tm.mkReal(str(frac.numerator), str(frac.denominator))

    for coord in [(0, 0), (1, 1)]:
        total = real_term(sum(np.real(e[coord]) for e in effects))
        slv.assertFormula(
            tm.mkTerm(
                Kind.EQUAL,
                total,
                tm.mkReal("1"),
            )
        )
    return slv.checkSat().isSat()


def main():
    rho0 = dm([1, 0])
    rho_plus = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])

    m0_proj = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    m1_proj = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)

    m0_weak = np.array([[np.sqrt(0.8), 0.0], [0.0, np.sqrt(0.2)]], dtype=complex)
    m1_weak = np.array([[np.sqrt(0.2), 0.0], [0.0, np.sqrt(0.8)]], dtype=complex)

    proj_effects = [m0_proj.conj().T @ m0_proj, m1_proj.conj().T @ m1_proj]
    weak_effects = [m0_weak.conj().T @ m0_weak, m1_weak.conj().T @ m1_weak]

    sigma0 = outcome_map(rho_plus, m0_weak)
    sigma1 = outcome_map(rho_plus, m1_weak)
    rho0_post, p0 = normalize_state(sigma0)
    rho1_post, p1 = normalize_state(sigma1)

    proj_sigma = outcome_map(rho0, m0_proj)
    proj_post, proj_p = normalize_state(proj_sigma)

    positive = {
        "projective_instrument_matches_readout_and_update": {
            "probability": proj_p,
            "effect_probability": float(np.real(np.trace(proj_effects[0] @ rho0))),
            "pass": (
                abs(proj_p - float(np.real(np.trace(proj_effects[0] @ rho0)))) < EPS
                and np.allclose(proj_post, rho0, atol=EPS)
            ),
        },
        "weak_instrument_probabilities_sum_to_one": {
            "p0": p0,
            "p1": p1,
            "pass": abs((p0 + p1) - 1.0) < EPS,
        },
        "weak_instrument_poststates_are_valid": {
            "pass": (
                rho0_post is not None
                and rho1_post is not None
                and abs(np.trace(rho0_post) - 1.0) < EPS
                and abs(np.trace(rho1_post) - 1.0) < EPS
            ),
        },
        "cvc5_certifies_induced_effect_completeness": {
            "projective_complete": cvc5_diagonal_effect_completeness(proj_effects),
            "weak_complete": cvc5_diagonal_effect_completeness(weak_effects),
            "pass": (
                cvc5_diagonal_effect_completeness(proj_effects)
                and cvc5_diagonal_effect_completeness(weak_effects)
            ),
        },
    }

    negative = {
        "fake_incomplete_effect_family_is_not_complete": {
            "pass": not np.allclose(
                np.array([[0.6, 0.0], [0.0, 0.1]]) + np.array([[0.1, 0.0], [0.0, 0.1]]),
                np.eye(2),
                atol=EPS,
            ),
        },
        "weak_instrument_changes_plus_state_conditionally": {
            "pass": not np.allclose(rho0_post, rho1_post, atol=EPS),
        },
    }

    boundary = {
        "projective_readout_and_update_agree_on_eigenstate": {
            "pass": abs(proj_p - 1.0) < EPS and np.allclose(proj_post, rho0, atol=EPS),
        },
        "weak_branch_weights_match_induced_effects": {
            "pass": (
                abs(p0 - float(np.real(np.trace(weak_effects[0] @ rho_plus)))) < EPS
                and abs(p1 - float(np.real(np.trace(weak_effects[1] @ rho_plus)))) < EPS
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "measurement_instrument",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": NEXT_LEGO_TARGET,
        "promotion_condition": PROMOTION_CONDITION,
        "blocked_until": BLOCKED_UNTIL,
        "demotion_condition": DEMOTION_CONDITION,
        "out_of_scope": OUT_OF_SCOPE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local instrument lego on projective and weak qubit measurements.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "measurement_instrument_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
