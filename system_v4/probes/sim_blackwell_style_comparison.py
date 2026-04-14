#!/usr/bin/env python3
"""
PURE LEGO: Blackwell-Style Comparison
=====================================
Direct local measurement/distinguishability lego.

Compare finite qubit POVM families by whether one can be obtained from another
by classical post-processing.
"""

import json
import pathlib

import numpy as np

import cvc5
from cvc5 import Kind
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local cvc5 lego for operational comparison of finite probe families "
    "via stochastic post-processing synthesis."
)

LEGO_IDS = [
    "blackwell_style_comparison",
    "povm_measurement_family",
    "measurement_instrument",
]

PRIMARY_LEGO_IDS = [
    "blackwell_style_comparison",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is the primary synthesis engine here"},
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "synthesizes or refutes stochastic post-processing maps between POVM families",
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


def diag_effect(a, b):
    return np.array([[a, 0.0], [0.0, b]], dtype=float)


def ket_dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def born_probs(rho, povm):
    return [float(np.real(np.trace(rho @ e))) for e in povm]


def cvc5_real_to_float(term):
    text = str(term).strip()
    if text.startswith("(/ ") and text.endswith(")"):
        inner = text[3:-1].strip().split()
        return float(inner[0]) / float(inner[1])
    return float(text)


def synthesize_post_processing(E, F):
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    slv.setOption("produce-models", "true")

    rows = len(F)
    cols = len(E)
    real = tm.getRealSort()
    zero = tm.mkReal(0)
    one = tm.mkReal(1)

    K = [[tm.mkConst(real, f"k_{j}_{i}") for i in range(cols)] for j in range(rows)]

    for i in range(cols):
        slv.assertFormula(tm.mkTerm(Kind.GEQ, K[0][i], zero))
        for j in range(1, rows):
            slv.assertFormula(tm.mkTerm(Kind.GEQ, K[j][i], zero))
        col_sum = tm.mkTerm(Kind.ADD, *[K[j][i] for j in range(rows)])
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, col_sum, one))

    for j in range(rows):
        for r in range(2):
            for c in range(2):
                target = tm.mkReal(str(float(F[j][r, c])))
                terms = []
                for i in range(cols):
                    coeff = tm.mkReal(str(float(E[i][r, c])))
                    terms.append(tm.mkTerm(Kind.MULT, K[j][i], coeff))
                total = terms[0] if len(terms) == 1 else tm.mkTerm(Kind.ADD, *terms)
                slv.assertFormula(tm.mkTerm(Kind.EQUAL, total, target))

    result = slv.checkSat()
    if not result.isSat():
        return {"sat": False, "K": None}

    model = []
    for j in range(rows):
        row = []
        for i in range(cols):
            val = slv.getValue(K[j][i])
            row.append(cvc5_real_to_float(val))
        model.append(row)
    return {"sat": True, "K": model}


def main():
    E_z = [diag_effect(1.0, 0.0), diag_effect(0.0, 1.0)]
    F_noisy_z = [diag_effect(0.8, 0.2), diag_effect(0.2, 0.8)]
    F_x = [
        np.array([[0.5, 0.5], [0.5, 0.5]], dtype=float),
        np.array([[0.5, -0.5], [-0.5, 0.5]], dtype=float),
    ]

    coarse = synthesize_post_processing(E_z, F_noisy_z)
    impossible = synthesize_post_processing(E_z, F_x)

    rho0 = ket_dm([1, 0])
    rho1 = ket_dm([0, 1])
    rho_plus = ket_dm([1 / np.sqrt(2), 1 / np.sqrt(2)])

    positive = {
        "noisy_z_measurement_is_postprocessing_of_projective_z": {
            "sat": coarse["sat"],
            "K": coarse["K"],
            "pass": bool(coarse["sat"]),
        },
        "postprocessing_reproduces_probabilities_on_test_states": {
            "rho0_E": born_probs(rho0, E_z),
            "rho0_F": born_probs(rho0, F_noisy_z),
            "rho1_E": born_probs(rho1, E_z),
            "rho1_F": born_probs(rho1, F_noisy_z),
            "rho_plus_E": born_probs(rho_plus, E_z),
            "rho_plus_F": born_probs(rho_plus, F_noisy_z),
            "pass": bool(
                coarse["sat"]
                and np.allclose(np.array(coarse["K"]) @ np.array(born_probs(rho0, E_z)), born_probs(rho0, F_noisy_z), atol=EPS)
                and np.allclose(np.array(coarse["K"]) @ np.array(born_probs(rho1, E_z)), born_probs(rho1, F_noisy_z), atol=EPS)
                and np.allclose(np.array(coarse["K"]) @ np.array(born_probs(rho_plus, E_z)), born_probs(rho_plus, F_noisy_z), atol=EPS)
            ),
        },
    }

    negative = {
        "x_basis_measurement_is_not_postprocessing_of_projective_z": {
            "sat": impossible["sat"],
            "pass": not impossible["sat"],
        },
    }

    boundary = {
        "identity_postprocessing_exists_for_same_measurement": {
            "pass": synthesize_post_processing(E_z, E_z)["sat"],
        },
        "stochastic_kernel_columns_sum_to_one": {
            "pass": bool(coarse["sat"] and np.allclose(np.sum(np.array(coarse["K"]), axis=0), np.ones(len(E_z)), atol=EPS)),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "blackwell_style_comparison",
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
            "scope_note": "Direct local operational-comparison lego on bounded qubit POVM families.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "blackwell_style_comparison_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
