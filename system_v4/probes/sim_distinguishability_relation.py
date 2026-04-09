#!/usr/bin/env python3
"""
PURE LEGO: Distinguishability Relation
======================================
Direct local probe/state distinguishability lego on a bounded one-qubit carrier.
"""

import json
import pathlib
from fractions import Fraction

import numpy as np
from z3 import Bool, If, Or, RealVal, Solver, Sum, sat, unsat


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for bounded probe-relative distinguishability on a one-qubit "
    "carrier, using finite measurement families and solver-backed separation checks."
)

LEGO_IDS = [
    "distinguishability_relation",
]

PRIMARY_LEGO_IDS = [
    "distinguishability_relation",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "checks finite separation or non-separation across bounded probe families using exact rational outcome probabilities",
    },
    "cvc5": {"tried": False, "used": False, "reason": "saved for richer channel/garbling comparison rows"},
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
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def prob(effect, rho):
    return float(np.real(np.trace(effect @ rho)))


def frac_term(x):
    q = Fraction(float(x)).limit_denominator(1000)
    return RealVal(f"{q.numerator}/{q.denominator}")


def z_projective():
    return [
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex),
    ]


def x_projective():
    ket_plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
    ket_minus = np.array([1.0, -1.0], dtype=complex) / np.sqrt(2)
    return [dm(ket_plus), dm(ket_minus)]


def family_outcomes(rho, family):
    return [prob(effect, rho) for effect in family]


def z3_relation_check(rho_a, rho_b, families):
    solver_same = Solver()
    solver_sep = Solver()
    sep_flags = []

    for family_name, effects in families.items():
        family_total = sum(prob(effect, rho_a) for effect in effects)
        solver_same.add(frac_term(family_total) == RealVal("1"))
        solver_sep.add(frac_term(family_total) == RealVal("1"))

        for idx, effect in enumerate(effects):
            pa = prob(effect, rho_a)
            pb = prob(effect, rho_b)
            solver_same.add(frac_term(pa) == frac_term(pb))

            sep_flag = Bool(f"{family_name}_{idx}_separates")
            sep_flags.append(sep_flag)
            solver_sep.add(
                sep_flag
                == If(
                    frac_term(pa) != frac_term(pb),
                    True,
                    False,
                )
            )

    solver_sep.add(Or(*sep_flags) if sep_flags else False)
    return {
        "same_status": str(solver_same.check()),
        "separation_status": str(solver_sep.check()),
        "equivalent_under_family": solver_same.check() == sat,
        "distinguishable_under_family": solver_sep.check() == sat,
    }


def max_gap(rho_a, rho_b, families):
    return max(
        abs(prob(effect, rho_a) - prob(effect, rho_b))
        for effects in families.values()
        for effect in effects
    )


def main():
    rho_0 = dm([1, 0])
    rho_1 = dm([0, 1])
    rho_plus = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])
    rho_minus = dm([1 / np.sqrt(2), -1 / np.sqrt(2)])
    rho_mix = np.eye(2, dtype=complex) / 2.0

    z_only = {"Z": z_projective()}
    zx = {"Z": z_projective(), "X": x_projective()}

    positive = {
        "same_state_is_not_distinguishable": {
            "max_gap": max_gap(rho_0, rho_0, zx),
            **z3_relation_check(rho_0, rho_0, zx),
            "pass": (
                max_gap(rho_0, rho_0, zx) < EPS
                and z3_relation_check(rho_0, rho_0, zx)["equivalent_under_family"]
                and not z3_relation_check(rho_0, rho_0, zx)["distinguishable_under_family"]
            ),
        },
        "orthogonal_basis_states_are_distinguishable": {
            "max_gap": max_gap(rho_0, rho_1, z_only),
            **z3_relation_check(rho_0, rho_1, z_only),
            "pass": (
                max_gap(rho_0, rho_1, z_only) > 1.0 - EPS
                and z3_relation_check(rho_0, rho_1, z_only)["distinguishable_under_family"]
            ),
        },
        "mixed_and_pure_states_separate_under_projective_probes": {
            "max_gap": max_gap(rho_mix, rho_plus, zx),
            **z3_relation_check(rho_mix, rho_plus, zx),
            "pass": (
                max_gap(rho_mix, rho_plus, zx) > 0.0
                and z3_relation_check(rho_mix, rho_plus, zx)["distinguishable_under_family"]
            ),
        },
    }

    negative = {
        "plus_and_minus_are_not_distinguished_by_z_only": {
            "z_outcomes_plus": family_outcomes(rho_plus, z_only["Z"]),
            "z_outcomes_minus": family_outcomes(rho_minus, z_only["Z"]),
            **z3_relation_check(rho_plus, rho_minus, z_only),
            "pass": (
                np.allclose(family_outcomes(rho_plus, z_only["Z"]), family_outcomes(rho_minus, z_only["Z"]), atol=EPS)
                and z3_relation_check(rho_plus, rho_minus, z_only)["equivalent_under_family"]
                and not z3_relation_check(rho_plus, rho_minus, z_only)["distinguishable_under_family"]
            ),
        },
        "same_probe_family_does_not_overclaim_separation": {
            **z3_relation_check(rho_mix, rho_mix, z_only),
            "pass": (
                z3_relation_check(rho_mix, rho_mix, z_only)["equivalent_under_family"]
                and not z3_relation_check(rho_mix, rho_mix, z_only)["distinguishable_under_family"]
            ),
        },
    }

    boundary = {
        "adding_x_refines_equivalence_classes": {
            "under_z_only": z3_relation_check(rho_plus, rho_minus, z_only),
            "under_zx": z3_relation_check(rho_plus, rho_minus, zx),
            "pass": (
                z3_relation_check(rho_plus, rho_minus, z_only)["equivalent_under_family"]
                and z3_relation_check(rho_plus, rho_minus, zx)["distinguishable_under_family"]
            ),
        },
        "all_probability_vectors_remain_normalized": {
            "pass": all(
                abs(sum(family_outcomes(rho, fam)) - 1.0) < EPS
                for rho in [rho_0, rho_1, rho_plus, rho_minus, rho_mix]
                for fam in [z_only["Z"], zx["X"]]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "distinguishability_relation",
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
            "scope_note": "Direct local probe-relative distinguishability lego on one-qubit states and bounded Z/X projective probe families.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "distinguishability_relation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
