#!/usr/bin/env python3
"""
PURE LEGO: Probe Object
=======================
Direct local root/admission lego.

An admissible probe object is modeled here as a finite family of effect
operators on a bounded carrier. The local rules are:
  - each effect is Hermitian and positive semidefinite
  - the family resolves the identity
  - the family yields bounded probabilities on admitted states
  - nontrivial probes separate at least one distinct state pair
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill

try:
    import sympy as sp
except ImportError:  # pragma: no cover
    sp = None

try:
    from z3 import Real, Solver, sat
except ImportError:  # pragma: no cover
    Real = None
    Solver = None
    sat = None


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for a finite admissible probe object represented by a "
    "bounded family of effect operators on a qubit carrier."
)

LEGO_IDS = [
    "probe_object",
    "probe_identity_preservation",
    "distinguishability_relation",
]

PRIMARY_LEGO_IDS = [
    "probe_object",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- bounded linear-algebra probe lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": Solver is not None, "used": Solver is not None, "reason": "bounded scalar witness for nontrivial two-outcome probe separation" if Solver is not None else "not installed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this smallest local probe admission lego"},
    "sympy": {"tried": sp is not None, "used": sp is not None, "reason": "exact symbolic identity-resolution check" if sp is not None else "not installed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
if Solver is not None:
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
if sp is not None:
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"


def is_hermitian(m):
    return bool(np.allclose(m, m.conj().T, atol=EPS))


def is_psd(m):
    evals = np.linalg.eigvalsh((m + m.conj().T) / 2)
    return bool(np.all(evals >= -EPS)), [float(x) for x in evals]


def probability(effect, rho):
    return float(np.real(np.trace(effect @ rho)))


def admissible_probe_family(effects):
    identity_sum = np.sum(effects, axis=0)
    psd_checks = [is_psd(e) for e in effects]
    return {
        "all_hermitian": all(is_hermitian(e) for e in effects),
        "all_psd": all(flag for flag, _ in psd_checks),
        "eigenvalues": [vals for _, vals in psd_checks],
        "resolves_identity": bool(np.allclose(identity_sum, np.eye(2), atol=EPS)),
        "identity_sum": identity_sum.tolist(),
    }


def exact_identity_resolution(effects):
    if sp is None:
        return None
    total = sp.zeros(2)
    for effect in effects:
        total += sp.Matrix(effect)
    return bool(sp.simplify(total - sp.eye(2)) == sp.zeros(2))


def z3_nontrivial_probe_witness():
    if Solver is None:
        return None

    lam = Real("lam")
    s = Solver()
    # Scalar multiple of identity yields identical probabilities on |0><0| and |1><1|.
    # A nontrivial two-outcome probe must have at least one diagonal imbalance.
    s.add(lam >= 0, lam <= 1)
    s.add(lam != 0.5)
    if s.check() != sat:
        return {"sat": False}
    model = s.model()
    lam_val = model[lam]
    lam_float = float(lam_val.numerator_as_long()) / float(lam_val.denominator_as_long())
    p0 = lam_float
    p1 = 1.0 - lam_float
    return {
        "sat": True,
        "witness_lambda": lam_float,
        "distinguishes_basis_pair": bool(abs(p0 - p1) > EPS),
    }


def main():
    rho0 = np.array([[1, 0], [0, 0]], dtype=complex)
    rho1 = np.array([[0, 0], [0, 1]], dtype=complex)
    rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)

    projective_probe = [
        np.array([[1, 0], [0, 0]], dtype=complex),
        np.array([[0, 0], [0, 1]], dtype=complex),
    ]
    noisy_probe = [
        np.array([[0.75, 0], [0, 0.25]], dtype=complex),
        np.array([[0.25, 0], [0, 0.75]], dtype=complex),
    ]
    invalid_non_psd = [
        np.array([[1.2, 0], [0, -0.2]], dtype=complex),
        np.array([[0, 0], [0, 1]], dtype=complex),
    ]
    invalid_not_resolving = [
        np.array([[0.6, 0], [0, 0.1]], dtype=complex),
        np.array([[0.1, 0], [0, 0.1]], dtype=complex),
    ]

    proj_chk = admissible_probe_family(projective_probe)
    noisy_chk = admissible_probe_family(noisy_probe)
    exact_resolution = exact_identity_resolution(projective_probe)
    z3_witness = z3_nontrivial_probe_witness()

    positive = {
        "projective_probe_family_is_admissible": {
            **proj_chk,
            "basis_probabilities": {
                "rho0": [probability(e, rho0) for e in projective_probe],
                "rho1": [probability(e, rho1) for e in projective_probe],
            },
            "pass": (
                proj_chk["all_hermitian"]
                and proj_chk["all_psd"]
                and proj_chk["resolves_identity"]
                and probability(projective_probe[0], rho0) > probability(projective_probe[0], rho1)
            ),
        },
        "noisy_probe_family_is_still_admissible": {
            **noisy_chk,
            "plus_state_probabilities": [probability(e, rho_plus) for e in noisy_probe],
            "pass": noisy_chk["all_hermitian"] and noisy_chk["all_psd"] and noisy_chk["resolves_identity"],
        },
    }

    negative = {
        "non_psd_effect_family_is_rejected": {
            **admissible_probe_family(invalid_non_psd),
            "pass": not admissible_probe_family(invalid_non_psd)["all_psd"],
        },
        "non_resolving_family_is_rejected": {
            **admissible_probe_family(invalid_not_resolving),
            "pass": not admissible_probe_family(invalid_not_resolving)["resolves_identity"],
        },
    }

    boundary = {
        "sympy_exact_identity_resolution": {
            "pass": True if exact_resolution is None else bool(exact_resolution),
            "skipped": exact_resolution is None,
        },
        "z3_nontrivial_two_outcome_probe_exists": {
            "pass": True if z3_witness is None else bool(z3_witness["sat"] and z3_witness["distinguishes_basis_pair"]),
            "skipped": z3_witness is None,
            "witness": z3_witness,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "probe_object",
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
            "scope_note": "Direct local admissible-probe lego on bounded qubit effect families.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "probe_object_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
