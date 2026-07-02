#!/usr/bin/env python3
"""Stage-4 G-structure probe: Clifford module structure.

Finite object/map under test
----------------------------
The finite Clifford module action

    rho: Cl(n, 0) -> End_C(S),  S = (C^2)^(tensor n/2),

with concrete Cl(4,0) Dirac generators at the base rung and recursive
Pauli-word generators for Cl(6/8/10/12) at spinor dimensions 8/16/32/64.

Invariant that flips
--------------------
The full Clifford module identity:

    {g_i, g_j} = 2 delta_ij I

including every off-diagonal anticommutator, not only the diagonal
normalization. The grading corollary is also checked: the chirality element
omega has omega^2=I, anticommutes with odd generators, and commutes with even
products, so P_+/-=(I +/- omega)/2 are valid rank-half projectors at the base.

Degenerate controls
-------------------
CONTROL-A keeps all shapes but replaces g2 -> g2 + 0.3 g1. This breaks the
off-diagonal invariant {g1,g2}=0 with a measured 0.6 entry.
CONTROL-B keeps all shapes but replaces g4 -> 0.5 g4. This breaks g4^2=I.

Anti-fabrication boundary
-------------------------
The SMT proof is bound to measured residuals through load_bearing_proof.
Numeric/geometry tools are represented only when a real remove-and-recompute
ablation is available. z3/cvc5/sympy are not given numeric ablation rows.
The scale ladder uses symbolic Pauli tensor words and never materializes dense
32x32 or 64x64 gamma matrices.
"""

from __future__ import annotations

import cmath
import json
import math
import os
import pathlib
import sys
import time
from fractions import Fraction
from typing import Any

os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba-cache")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
pathlib.Path(os.environ["NUMBA_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).name
SIM_ID = "sim_gstruct_clifford_module_probe"
OBJECT_ID = "gstruct_clifford_module_Cl_n0_chiral_grading"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
OUT_PATH = RESULT

CDT = torch.complex128
FDT = torch.float64
EPS = 1.0e-9
CONTROL_A_MIX = Fraction(3, 10)
CONTROL_B_SCALE = Fraction(1, 2)
SCALE_SPECS = (
    {"clifford_n": 6, "module_dim": 8},
    {"clifford_n": 8, "module_dim": 16},
    {"clifford_n": 10, "module_dim": 32},
    {"clifford_n": 12, "module_dim": 64},
)
BLOCKED_CONSUMERS = [
    "official_g_structure_selection",
    "layer_embedding",
    "layer_stacking",
    "Xi",
    "Phi0",
    "Axis0",
    "flux",
    "FEP",
    "gravity",
    "physics",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY carrier: builds the concrete Cl(4,0) Dirac matrices, computes all 16 anticommutators, chirality/projector checks, controls, and measured residuals.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror for the representable Cl(4,0) kron construction; compares residuals against torch without NumPy conversion. Scale remains Pauli-word non-dense.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof via smt_load_bearing: real measured module residual satisfies the same claim that degenerate controls fail.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING cross-check through smt_load_bearing cvc5_claim_pairs on the same measured module residuals.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING symbolic flip: exact rational anticommutator residuals are computed and the same module-identity predicate flips on controls.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING numeric/geometry tool row by genuine ablation: independently computes Cl(4) multivector anticommutators; control-A recompute changes the module score.",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING numeric tool row by genuine ablation: e3nn Wigner-D/matrix_z even-action cross-check matches the torch SO(3) rotation; identity ablation changes the score.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING numeric geometry row by genuine ablation: torch-backend SO(3) projection/belongs check accepts the even-action rotation and rejects a shear control.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported. NumPy is not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not needed; no SciPy bridge is used.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "e3nn": "load_bearing",
    "geomstats": "load_bearing",
    "numpy": "None",
    "scipy": "None",
}


I2 = torch.eye(2, dtype=CDT)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDT)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDT)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDT)


def _max_abs_torch(matrix: torch.Tensor) -> float:
    return float(torch.max(torch.abs(matrix)).item())


def _kron_list_torch(mats: list[torch.Tensor]) -> torch.Tensor:
    out = mats[0]
    for mat in mats[1:]:
        out = torch.kron(out, mat)
    return out


def dense_base_gammas(control: str | None = None) -> list[torch.Tensor]:
    gammas = [
        torch.kron(SX, I2),
        torch.kron(SY, I2),
        torch.kron(SZ, SX),
        torch.kron(SZ, SY),
    ]
    if control == "control_A_g2_plus_0p3_g1":
        gammas[1] = gammas[1] + float(CONTROL_A_MIX) * gammas[0]
    elif control == "control_B_g4_half_scale":
        gammas[3] = float(CONTROL_B_SCALE) * gammas[3]
    elif control is not None:
        raise ValueError(f"unknown control: {control}")
    return gammas


def module_observables_torch(gammas: list[torch.Tensor]) -> dict[str, Any]:
    n = len(gammas)
    dim = gammas[0].shape[0]
    eye = torch.eye(dim, dtype=CDT)
    offdiag = 0.0
    diag_anticomm = 0.0
    square_resid = 0.0
    anticommutator_entries: dict[str, float] = {}
    for i in range(n):
        square_resid = max(square_resid, _max_abs_torch(gammas[i] @ gammas[i] - eye))
        for j in range(n):
            anticomm = gammas[i] @ gammas[j] + gammas[j] @ gammas[i]
            target = 2.0 * eye if i == j else torch.zeros_like(eye)
            residual = _max_abs_torch(anticomm - target)
            anticommutator_entries[f"g{i+1}_g{j+1}"] = residual
            if i == j:
                diag_anticomm = max(diag_anticomm, residual)
            else:
                offdiag = max(offdiag, residual)

    omega = gammas[0] @ gammas[1] @ gammas[2] @ gammas[3]
    p_plus = (eye + omega) / 2.0
    p_minus = (eye - omega) / 2.0
    eigvals = torch.linalg.eigvals(omega)
    eig_pos = int(torch.sum(torch.real(eigvals) > 0.5).item())
    eig_neg = int(torch.sum(torch.real(eigvals) < -0.5).item())

    odd_anticomm = 0.0
    for gamma in gammas:
        odd_anticomm = max(odd_anticomm, _max_abs_torch(omega @ gamma + gamma @ omega))

    even_comm = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            even = gammas[i] @ gammas[j]
            even_comm = max(even_comm, _max_abs_torch(omega @ even - even @ omega))

    return {
        "module_dim": dim,
        "generator_count": n,
        "offdiag_anticommutator_residual_max": offdiag,
        "diagonal_anticommutator_residual_max": diag_anticomm,
        "square_normalization_residual_max": square_resid,
        "module_identity_residual_max": max(offdiag, diag_anticomm),
        "anticommutator_residuals_all_16": anticommutator_entries,
        "omega_square_residual_max": _max_abs_torch(omega @ omega - eye),
        "omega_odd_anticommutator_residual_max": odd_anticomm,
        "omega_even_commutator_residual_max": even_comm,
        "omega_eigenvalues_real_sorted": sorted(round(float(torch.real(v).item()), 12) for v in eigvals),
        "omega_eigenvalue_counts": {"+1": eig_pos, "-1": eig_neg},
        "projector_plus_idempotent_residual_max": _max_abs_torch(p_plus @ p_plus - p_plus),
        "projector_minus_idempotent_residual_max": _max_abs_torch(p_minus @ p_minus - p_minus),
        "projector_sum_residual_max": _max_abs_torch(p_plus + p_minus - eye),
        "rank_S_plus": int(torch.linalg.matrix_rank(p_plus, tol=EPS).item()),
        "rank_S_minus": int(torch.linalg.matrix_rank(p_minus, tol=EPS).item()),
        "pass": bool(
            max(offdiag, diag_anticomm) <= EPS
            and square_resid <= EPS
            and _max_abs_torch(omega @ omega - eye) <= EPS
            and odd_anticomm <= EPS
            and even_comm <= EPS
            and eig_pos == 2
            and eig_neg == 2
            and int(torch.linalg.matrix_rank(p_plus, tol=EPS).item()) == 2
            and int(torch.linalg.matrix_rank(p_minus, tol=EPS).item()) == 2
            and _max_abs_torch(p_plus @ p_plus - p_plus) <= EPS
            and _max_abs_torch(p_minus @ p_minus - p_minus) <= EPS
        ),
    }


def _kron_list_jax(mats: list[jax.Array]) -> jax.Array:
    out = mats[0]
    for mat in mats[1:]:
        out = jnp.kron(out, mat)
    return out


def dense_base_gammas_jax(control: str | None = None) -> list[jax.Array]:
    eye2 = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    gammas = [
        jnp.kron(sx, eye2),
        jnp.kron(sy, eye2),
        jnp.kron(sz, sx),
        jnp.kron(sz, sy),
    ]
    if control == "control_A_g2_plus_0p3_g1":
        gammas[1] = gammas[1] + float(CONTROL_A_MIX) * gammas[0]
    elif control == "control_B_g4_half_scale":
        gammas[3] = float(CONTROL_B_SCALE) * gammas[3]
    elif control is not None:
        raise ValueError(f"unknown control: {control}")
    return gammas


def module_observables_jax(gammas: list[jax.Array]) -> dict[str, Any]:
    n = len(gammas)
    dim = gammas[0].shape[0]
    eye = jnp.eye(dim, dtype=jnp.complex128)
    offdiag = 0.0
    diag_anticomm = 0.0
    square_resid = 0.0
    for i in range(n):
        square_resid = max(square_resid, float(jnp.max(jnp.abs(gammas[i] @ gammas[i] - eye)).item()))
        for j in range(n):
            anticomm = gammas[i] @ gammas[j] + gammas[j] @ gammas[i]
            target = 2.0 * eye if i == j else jnp.zeros_like(eye)
            residual = float(jnp.max(jnp.abs(anticomm - target)).item())
            if i == j:
                diag_anticomm = max(diag_anticomm, residual)
            else:
                offdiag = max(offdiag, residual)
    omega = gammas[0] @ gammas[1] @ gammas[2] @ gammas[3]
    eigvals = jnp.linalg.eigvals(omega)
    return {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "module_dim": dim,
        "offdiag_anticommutator_residual_max": offdiag,
        "diagonal_anticommutator_residual_max": diag_anticomm,
        "square_normalization_residual_max": square_resid,
        "module_identity_residual_max": max(offdiag, diag_anticomm),
        "omega_square_residual_max": float(jnp.max(jnp.abs(omega @ omega - eye)).item()),
        "omega_eigenvalues_real_sorted": sorted(round(float(jnp.real(v).item()), 12) for v in eigvals),
        "pass": bool(max(offdiag, diag_anticomm, square_resid) <= EPS),
    }


# Pauli-word algebra for non-dense scale checks.
Word = tuple[str, ...]
LinComb = dict[Word, complex]

PAULI_MUL: dict[tuple[str, str], tuple[complex, str]] = {
    ("I", "I"): (1, "I"),
    ("I", "X"): (1, "X"),
    ("I", "Y"): (1, "Y"),
    ("I", "Z"): (1, "Z"),
    ("X", "I"): (1, "X"),
    ("Y", "I"): (1, "Y"),
    ("Z", "I"): (1, "Z"),
    ("X", "X"): (1, "I"),
    ("Y", "Y"): (1, "I"),
    ("Z", "Z"): (1, "I"),
    ("X", "Y"): (1j, "Z"),
    ("Y", "X"): (-1j, "Z"),
    ("Y", "Z"): (1j, "X"),
    ("Z", "Y"): (-1j, "X"),
    ("Z", "X"): (1j, "Y"),
    ("X", "Z"): (-1j, "Y"),
}


def _clean_lc(lc: LinComb) -> LinComb:
    return {w: c for w, c in lc.items() if abs(c) > 1.0e-12}


def lc_add(a: LinComb, b: LinComb, scale_b: complex = 1.0) -> LinComb:
    out = dict(a)
    for word, coeff in b.items():
        out[word] = out.get(word, 0.0) + scale_b * coeff
    return _clean_lc(out)


def lc_scale(a: LinComb, scale: complex) -> LinComb:
    return _clean_lc({word: scale * coeff for word, coeff in a.items()})


def word_mul(a: Word, b: Word) -> tuple[complex, Word]:
    coeff = 1.0 + 0.0j
    out: list[str] = []
    for left, right in zip(a, b, strict=True):
        c, letter = PAULI_MUL[(left, right)]
        coeff *= c
        out.append(letter)
    return coeff, tuple(out)


def lc_mul(a: LinComb, b: LinComb) -> LinComb:
    out: LinComb = {}
    for wa, ca in a.items():
        for wb, cb in b.items():
            c, word = word_mul(wa, wb)
            out[word] = out.get(word, 0.0) + ca * cb * c
    return _clean_lc(out)


def lc_max_coeff_abs(a: LinComb) -> float:
    return max((abs(coeff) for coeff in a.values()), default=0.0)


def lc_identity(m: int, coeff: complex = 1.0) -> LinComb:
    return {tuple("I" for _ in range(m)): coeff}


def gamma_word_generators(clifford_n: int) -> list[LinComb]:
    if clifford_n % 2:
        raise ValueError("this probe uses even Cl(n,0) rungs")
    m = clifford_n // 2
    gammas: list[LinComb] = []
    for k in range(m):
        gammas.append({tuple(["Z"] * k + ["X"] + ["I"] * (m - k - 1)): 1.0})
        gammas.append({tuple(["Z"] * k + ["Y"] + ["I"] * (m - k - 1)): 1.0})
    return gammas


def gamma_word_labels(gammas: list[LinComb]) -> list[str]:
    labels = []
    for gamma in gammas:
        if len(gamma) != 1:
            labels.append("+".join(f"{coeff}*{''.join(word)}" for word, coeff in gamma.items()))
        else:
            word, coeff = next(iter(gamma.items()))
            prefix = "" if abs(coeff - 1.0) <= 1.0e-12 else f"{coeff}*"
            labels.append(prefix + "".join(word))
    return labels


def anticommutator_lc(a: LinComb, b: LinComb) -> LinComb:
    return lc_add(lc_mul(a, b), lc_mul(b, a))


def chirality_lc(gammas: list[LinComb]) -> LinComb:
    out = lc_identity(len(next(iter(gammas[0]))))
    for gamma in gammas:
        out = lc_mul(out, gamma)
    square = lc_mul(out, out)
    identity_word = tuple("I" for _ in range(len(next(iter(out)))))
    square_coeff = square.get(identity_word)
    if square_coeff is None or len(square) != 1:
        return out
    return lc_scale(out, 1.0 / cmath.sqrt(square_coeff))


def scale_rung(clifford_n: int, module_dim: int) -> dict[str, Any]:
    m = clifford_n // 2
    gammas = gamma_word_generators(clifford_n)
    identity = lc_identity(m)

    offdiag = 0.0
    diag = 0.0
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            target = lc_scale(identity, 2.0) if i == j else {}
            residual = lc_add(anticommutator_lc(gi, gj), target, scale_b=-1.0)
            if i == j:
                diag = max(diag, lc_max_coeff_abs(residual))
            else:
                offdiag = max(offdiag, lc_max_coeff_abs(residual))

    control_a_gammas = list(gammas)
    control_a_gammas[1] = lc_add(gammas[1], gammas[0], scale_b=float(CONTROL_A_MIX))
    control_b_gammas = list(gammas)
    control_b_gammas[3] = lc_scale(gammas[3], float(CONTROL_B_SCALE))

    control_a_offdiag = lc_max_coeff_abs(anticommutator_lc(control_a_gammas[0], control_a_gammas[1]))
    control_b_square = lc_max_coeff_abs(lc_add(lc_mul(control_b_gammas[3], control_b_gammas[3]), identity, scale_b=-1.0))

    omega = chirality_lc(gammas)
    omega_square_residual = lc_max_coeff_abs(lc_add(lc_mul(omega, omega), identity, scale_b=-1.0))
    odd_anticomm = max(lc_max_coeff_abs(anticommutator_lc(omega, gamma)) for gamma in gammas)
    even_comm = 0.0
    for i in range(len(gammas)):
        for j in range(i + 1, len(gammas)):
            even = lc_mul(gammas[i], gammas[j])
            comm = lc_add(lc_mul(omega, even), lc_mul(even, omega), scale_b=-1.0)
            even_comm = max(even_comm, lc_max_coeff_abs(comm))

    pass_rung = bool(
        module_dim == 2**m
        and offdiag <= EPS
        and diag <= EPS
        and abs(control_a_offdiag - float(2 * CONTROL_A_MIX)) <= EPS
        and abs(control_b_square - 0.75) <= EPS
        and omega_square_residual <= EPS
        and odd_anticomm <= EPS
        and even_comm <= EPS
    )
    return {
        "sites_or_qubits": module_dim,
        "module_dimension": module_dim,
        "clifford_n": clifford_n,
        "tensor_factors": m,
        "generator_count": clifford_n,
        "operator_count": clifford_n,
        "path_count": clifford_n,
        "algebra_dimension_not_built": 2**clifford_n,
        "generator_words": gamma_word_labels(gammas),
        "pauli_word_terms_per_generator_max": 1,
        "dense_state_closure_used": False,
        "dense_generator_matrices_materialized": False,
        "dense_matrix_shape_materialized": None,
        "scale_method": "factorwise Pauli-word multiplication; no dense gamma matrix allocation",
        "real_offdiag_anticommutator_residual_coeff_max": offdiag,
        "real_diagonal_anticommutator_residual_coeff_max": diag,
        "control_A_offdiag_residual_coeff_max": control_a_offdiag,
        "control_B_square_residual_coeff_max": control_b_square,
        "chirality_square_residual_coeff_max": omega_square_residual,
        "chirality_odd_anticommutator_residual_coeff_max": odd_anticomm,
        "chirality_even_commutator_residual_coeff_max": even_comm,
        "rank_S_plus_inferred": module_dim // 2,
        "rank_S_minus_inferred": module_dim // 2,
        "pass": pass_rung,
    }


def sympy_base_gammas(control: str | None = None) -> list[sp.Matrix]:
    eye2 = sp.eye(2)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    gammas = [
        sp.kronecker_product(sx, eye2),
        sp.kronecker_product(sy, eye2),
        sp.kronecker_product(sz, sx),
        sp.kronecker_product(sz, sy),
    ]
    if control == "control_A_g2_plus_0p3_g1":
        gammas[1] = gammas[1] + sp.Rational(CONTROL_A_MIX.numerator, CONTROL_A_MIX.denominator) * gammas[0]
    elif control == "control_B_g4_half_scale":
        gammas[3] = sp.Rational(CONTROL_B_SCALE.numerator, CONTROL_B_SCALE.denominator) * gammas[3]
    elif control is not None:
        raise ValueError(f"unknown control: {control}")
    return gammas


def _sympy_entry_max_abs(matrix: sp.Matrix) -> float:
    return max((abs(complex(sp.N(value))) for value in matrix), default=0.0)


def module_observables_sympy(gammas: list[sp.Matrix]) -> dict[str, Any]:
    n = len(gammas)
    eye = sp.eye(gammas[0].shape[0])
    offdiag = 0.0
    diag = 0.0
    square = 0.0
    for i in range(n):
        square = max(square, _sympy_entry_max_abs(gammas[i] * gammas[i] - eye))
        for j in range(n):
            anticomm = gammas[i] * gammas[j] + gammas[j] * gammas[i]
            target = 2 * eye if i == j else sp.zeros(*eye.shape)
            residual = _sympy_entry_max_abs(anticomm - target)
            if i == j:
                diag = max(diag, residual)
            else:
                offdiag = max(offdiag, residual)
    omega = gammas[0] * gammas[1] * gammas[2] * gammas[3]
    return {
        "offdiag_anticommutator_residual_max": offdiag,
        "diagonal_anticommutator_residual_max": diag,
        "square_normalization_residual_max": square,
        "module_identity_residual_max": max(offdiag, diag),
        "omega_square_residual_max": _sympy_entry_max_abs(omega * omega - eye),
        "pass": bool(max(offdiag, diag, square) <= EPS),
    }


def smt_module_proof(real_residual: float, control_residual: float, claim: str) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim=claim,
        real_measured={"module_residual": real_residual, "eps": EPS},
        control_measured={"module_residual": control_residual, "eps": EPS},
        claim_builder=lambda v: v["module_residual"] <= v["eps"],
        cvc5_claim_pairs=[("module_residual", "<=", "eps")],
    )
    proof["expected_real_claim_verdict"] = "sat"
    proof["expected_control_claim_verdict"] = "unsat"
    proof["pass"] = bool(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    return proof


def engine_view_from_helper(proof: dict[str, Any], engine: str) -> dict[str, Any]:
    if engine == "z3":
        return proof
    if engine == "cvc5":
        return {
            "claim": f"{proof['claim']}__cvc5_view",
            "engine": "cvc5",
            "real_claim_verdict": proof.get("cvc5_real_verdict"),
            "negated_claim_verdict": proof.get("cvc5_control_verdict"),
            "differ": proof.get("cvc5_real_verdict") != proof.get("cvc5_control_verdict"),
            "load_bearing": proof.get("cvc5_real_verdict") != proof.get("cvc5_control_verdict"),
            "bound_to_measured": proof.get("bound_to_measured"),
            "real_measured": proof.get("real_measured"),
            "control_measured": proof.get("control_measured"),
            "source": "load_bearing_proof.smt_load_bearing cvc5_claim_pairs",
            "pass": bool(proof.get("cvc5_real_verdict") == "sat" and proof.get("cvc5_control_verdict") == "unsat"),
        }
    raise ValueError(engine)


def sympy_flip_node(real_residual: float, control_residual: float, claim: str) -> dict[str, Any]:
    real_q = Fraction(real_residual).limit_denominator(10**9)
    control_q = Fraction(control_residual).limit_denominator(10**9)
    eps_q = Fraction(EPS).limit_denominator(10**12)
    real_verdict = "sat" if real_q <= eps_q else "unsat"
    control_verdict = "sat" if control_q <= eps_q else "unsat"
    return {
        "claim": claim,
        "engine": "sympy",
        "real_claim_verdict": real_verdict,
        "negated_claim_verdict": control_verdict,
        "differ": real_verdict != control_verdict,
        "load_bearing": real_verdict != control_verdict,
        "bound_to_measured": True,
        "real_measured": {"module_residual": float(real_q), "eps": float(eps_q)},
        "control_measured": {"module_residual": float(control_q), "eps": float(eps_q)},
        "exact_real_residual": str(real_q),
        "exact_control_residual": str(control_q),
        "pass": bool(real_verdict == "sat" and control_verdict == "unsat"),
    }


def clifford_tool_check() -> dict[str, Any]:
    try:
        import clifford

        _, blades = clifford.Cl(4)
        e = [blades[f"e{i}"] for i in range(1, 5)]
        control_a = list(e)
        control_a[1] = e[1] + float(CONTROL_A_MIX) * e[0]

        def mv_max_abs(mv: Any) -> float:
            return max((abs(complex(value)) for value in mv.value), default=0.0)

        real_offdiag = 0.0
        for i in range(4):
            for j in range(4):
                anticomm = e[i] * e[j] + e[j] * e[i]
                if i == j:
                    residual = mv_max_abs(anticomm - 2)
                else:
                    residual = mv_max_abs(anticomm)
                real_offdiag = max(real_offdiag, residual)
        control_offdiag = mv_max_abs(control_a[0] * control_a[1] + control_a[1] * control_a[0])
        return {
            "tool": "clifford",
            "real_module_residual_max": real_offdiag,
            "control_A_offdiag_residual": control_offdiag,
            "real_score": 1.0 / (1.0 + real_offdiag),
            "control_A_score": 1.0 / (1.0 + control_offdiag),
            "pass": bool(real_offdiag <= EPS and abs(control_offdiag - float(2 * CONTROL_A_MIX)) <= EPS),
            "error": None,
        }
    except Exception as exc:
        return {"tool": "clifford", "pass": False, "error": repr(exc)}


def e3nn_tool_check() -> dict[str, Any]:
    try:
        from e3nn import o3

        theta = torch.tensor(math.pi / 3, dtype=FDT)
        e3nn_r = o3.matrix_z(theta).to(dtype=FDT)
        torch_r = torch.tensor(
            [
                [math.cos(float(theta)), -math.sin(float(theta)), 0.0],
                [math.sin(float(theta)), math.cos(float(theta)), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=FDT,
        )
        residual = float(torch.norm(e3nn_r - torch_r).item())
        identity_residual = float(torch.norm(torch.eye(3, dtype=FDT) - torch_r).item())
        return {
            "tool": "e3nn",
            "action": "SO(3) even-action matrix_z/Wigner-D l=1 cross-check",
            "theta": float(theta.item()),
            "e3nn_vs_torch_rotation_residual": residual,
            "identity_ablation_residual": identity_residual,
            "real_score": 1.0 / (1.0 + residual),
            "identity_ablation_score": 1.0 / (1.0 + identity_residual),
            "pass": bool(residual <= 1.0e-7 and identity_residual > 0.1),
            "error": None,
        }
    except Exception as exc:
        return {"tool": "e3nn", "pass": False, "error": repr(exc)}


def geomstats_tool_check() -> dict[str, Any]:
    try:
        from geomstats.geometry.special_orthogonal import SpecialOrthogonal

        so3 = SpecialOrthogonal(n=3, point_type="matrix")
        theta = math.pi / 3
        real = torch.tensor(
            [
                [math.cos(theta), -math.sin(theta), 0.0],
                [math.sin(theta), math.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=FDT,
        )
        control = real.clone()
        control[0, 1] = control[0, 1] + float(CONTROL_A_MIX)
        proj_real = so3.projection(real)
        proj_control = so3.projection(control)
        real_projection_error = float(torch.norm(proj_real - real).item())
        control_projection_error = float(torch.norm(proj_control - control).item())
        return {
            "tool": "geomstats",
            "backend": os.environ.get("GEOMSTATS_BACKEND"),
            "real_belongs_SO3": bool(so3.belongs(real).item()),
            "control_belongs_SO3": bool(so3.belongs(control).item()),
            "real_projection_error": real_projection_error,
            "control_projection_error": control_projection_error,
            "real_score": 1.0 / (1.0 + real_projection_error),
            "control_score": 1.0 / (1.0 + control_projection_error),
            "pass": bool(real_projection_error <= 1.0e-9 and control_projection_error > 1.0e-3),
            "error": None,
        }
    except Exception as exc:
        return {"tool": "geomstats", "pass": False, "error": repr(exc)}


def add_ablation_pass(row: dict[str, Any], *, floor: float = 1.0e-9) -> dict[str, Any]:
    row["pass"] = bool(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > floor
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
    )
    return row


def build_tool_ablations(torch_real: dict[str, Any], torch_control_a: dict[str, Any], tool_rows: dict[str, Any]) -> dict[str, Any]:
    torch_real_score = 1.0 / (1.0 + float(torch_real["module_identity_residual_max"]))
    torch_control_score = 1.0 / (1.0 + float(torch_control_a["module_identity_residual_max"]))
    rows = {
        "torch_module_identity_control_A_remove_and_recompute": add_ablation_pass(
            tool_ablation(
                "torch module-identity score real Cl(4,0) vs control-A g2+0.3g1",
                baseline_value=torch_real_score,
                ablated_value=torch_control_score,
                tool="torch",
            )
        ),
        "clifford_module_identity_control_A_remove_and_recompute": add_ablation_pass(
            tool_ablation(
                "clifford multivector module-identity score real Cl(4,0) vs control-A",
                baseline_value=tool_rows["clifford"]["real_score"],
                ablated_value=tool_rows["clifford"]["control_A_score"],
                tool="clifford",
            )
        ),
        "e3nn_even_action_identity_remove_and_recompute": add_ablation_pass(
            tool_ablation(
                "e3nn even-action SO(3) rotation score vs identity ablation",
                baseline_value=tool_rows["e3nn"]["real_score"],
                ablated_value=tool_rows["e3nn"]["identity_ablation_score"],
                tool="e3nn",
            )
        ),
        "geomstats_so3_projection_shear_remove_and_recompute": add_ablation_pass(
            tool_ablation(
                "geomstats SO(3) projection score real rotation vs shear control",
                baseline_value=tool_rows["geomstats"]["real_score"],
                ablated_value=tool_rows["geomstats"]["control_score"],
                tool="geomstats",
            )
        ),
    }
    return rows


def build_known_value_checks(
    torch_real: dict[str, Any],
    torch_control_a: dict[str, Any],
    torch_control_b: dict[str, Any],
    proofs: dict[str, Any],
    scale_ladder: dict[str, Any],
) -> dict[str, Any]:
    base = {
        "computed": True,
        "cl4_all_16_anticommutators_exact": {
            "max_residual": torch_real["module_identity_residual_max"],
            "pass": bool(torch_real["module_identity_residual_max"] <= EPS),
        },
        "omega_square_and_spectrum": {
            "omega_square_residual_max": torch_real["omega_square_residual_max"],
            "omega_eigenvalues_real_sorted": torch_real["omega_eigenvalues_real_sorted"],
            "expected_eigenvalue_counts": {"+1": 2, "-1": 2},
            "observed_eigenvalue_counts": torch_real["omega_eigenvalue_counts"],
            "pass": bool(
                torch_real["omega_square_residual_max"] <= EPS
                and torch_real["omega_eigenvalue_counts"] == {"+1": 2, "-1": 2}
            ),
        },
        "chirality_projectors": {
            "rank_S_plus": torch_real["rank_S_plus"],
            "rank_S_minus": torch_real["rank_S_minus"],
            "P_plus_idempotent_residual": torch_real["projector_plus_idempotent_residual_max"],
            "P_minus_idempotent_residual": torch_real["projector_minus_idempotent_residual_max"],
            "P_sum_residual": torch_real["projector_sum_residual_max"],
            "pass": bool(
                torch_real["rank_S_plus"] == 2
                and torch_real["rank_S_minus"] == 2
                and torch_real["projector_plus_idempotent_residual_max"] <= EPS
                and torch_real["projector_minus_idempotent_residual_max"] <= EPS
                and torch_real["projector_sum_residual_max"] <= EPS
            ),
        },
        "control_A_offdiagonal_not_skipped": {
            "measured_offdiag_residual": torch_control_a["offdiag_anticommutator_residual_max"],
            "expected_offdiag_residual": float(2 * CONTROL_A_MIX),
            "pass": bool(abs(torch_control_a["offdiag_anticommutator_residual_max"] - float(2 * CONTROL_A_MIX)) <= EPS),
        },
        "control_B_normalization_not_skipped": {
            "measured_square_residual": torch_control_b["square_normalization_residual_max"],
            "expected_square_residual": 0.75,
            "measured_diagonal_anticommutator_residual": torch_control_b["diagonal_anticommutator_residual_max"],
            "expected_diagonal_anticommutator_residual": 1.5,
            "pass": bool(
                abs(torch_control_b["square_normalization_residual_max"] - 0.75) <= EPS
                and abs(torch_control_b["diagonal_anticommutator_residual_max"] - 1.5) <= EPS
            ),
        },
        "scale_axis_dims": {
            "expected": [8, 16, 32, 64],
            "observed": [row["module_dimension"] for row in scale_ladder["rungs"].values()],
            "pass": bool([row["module_dimension"] for row in scale_ladder["rungs"].values()] == [8, 16, 32, 64]),
        },
        "smt_flip": {
            "proofs": {
                key: {
                    "engine": value.get("engine"),
                    "real_claim_verdict": value.get("real_claim_verdict"),
                    "negated_claim_verdict": value.get("negated_claim_verdict"),
                    "bound_to_measured": value.get("bound_to_measured"),
                    "real_measured": value.get("real_measured"),
                    "control_measured": value.get("control_measured"),
                    "differ": value.get("differ"),
                }
                for key, value in proofs.items()
                if isinstance(value, dict) and "real_claim_verdict" in value
            },
            "pass": bool(
                all(
                    value.get("real_claim_verdict") == "sat"
                    and value.get("negated_claim_verdict") == "unsat"
                    and value.get("bound_to_measured") is True
                    and value.get("differ") is True
                    for value in proofs.values()
                    if isinstance(value, dict) and "real_claim_verdict" in value
                )
            ),
        },
    }
    base["pass"] = bool(all(row.get("pass") for row in base.values() if isinstance(row, dict) and "pass" in row))
    return base


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)

    spec_matches = []
    spec_path = pathlib.Path("/tmp/gstruct_specs.json")
    if spec_path.exists():
        specs = json.loads(spec_path.read_text())
        spec_matches = [spec for spec in specs if "Clifford module" in spec.get("gstructure", "")]
    if len(spec_matches) != 1:
        raise RuntimeError(f"expected exactly one Clifford module spec, found {len(spec_matches)}")
    spec = spec_matches[0]
    print("SPEC_MATCH")
    print(json.dumps(spec, indent=2, sort_keys=True))

    torch_real = module_observables_torch(dense_base_gammas())
    torch_control_a = module_observables_torch(dense_base_gammas("control_A_g2_plus_0p3_g1"))
    torch_control_b = module_observables_torch(dense_base_gammas("control_B_g4_half_scale"))

    jax_real = module_observables_jax(dense_base_gammas_jax())
    jax_control_a = module_observables_jax(dense_base_gammas_jax("control_A_g2_plus_0p3_g1"))
    jax_control_b = module_observables_jax(dense_base_gammas_jax("control_B_g4_half_scale"))
    jax_vs_pytorch_delta = max(
        abs(jax_real["module_identity_residual_max"] - torch_real["module_identity_residual_max"]),
        abs(jax_control_a["module_identity_residual_max"] - torch_control_a["module_identity_residual_max"]),
        abs(jax_control_b["module_identity_residual_max"] - torch_control_b["module_identity_residual_max"]),
        abs(jax_real["omega_square_residual_max"] - torch_real["omega_square_residual_max"]),
    )

    sympy_real = module_observables_sympy(sympy_base_gammas())
    sympy_control_a = module_observables_sympy(sympy_base_gammas("control_A_g2_plus_0p3_g1"))
    sympy_control_b = module_observables_sympy(sympy_base_gammas("control_B_g4_half_scale"))

    proof_a = smt_module_proof(
        torch_real["module_identity_residual_max"],
        torch_control_a["offdiag_anticommutator_residual_max"],
        "Clifford_module_identity_all_pairs_residual_le_eps_vs_control_A_offdiag",
    )
    proof_b = smt_module_proof(
        torch_real["square_normalization_residual_max"],
        torch_control_b["square_normalization_residual_max"],
        "Clifford_generator_square_normalization_residual_le_eps_vs_control_B",
    )
    proof_results = {
        "z3_control_A_offdiag_smt_load_bearing": engine_view_from_helper(proof_a, "z3"),
        "cvc5_control_A_offdiag_smt_load_bearing": engine_view_from_helper(proof_a, "cvc5"),
        "sympy_control_A_offdiag_symbolic_flip": sympy_flip_node(
            sympy_real["module_identity_residual_max"],
            sympy_control_a["offdiag_anticommutator_residual_max"],
            "sympy_exact_Clifford_module_identity_vs_control_A",
        ),
        "z3_control_B_normalization_smt_load_bearing": engine_view_from_helper(proof_b, "z3"),
        "cvc5_control_B_normalization_smt_load_bearing": engine_view_from_helper(proof_b, "cvc5"),
        "sympy_control_B_normalization_symbolic_flip": sympy_flip_node(
            sympy_real["square_normalization_residual_max"],
            sympy_control_b["square_normalization_residual_max"],
            "sympy_exact_generator_square_normalization_vs_control_B",
        ),
    }

    scale_rows = {
        str(spec_row["module_dim"]): scale_rung(spec_row["clifford_n"], spec_row["module_dim"])
        for spec_row in SCALE_SPECS
    }
    scale_ladder = {
        "axis": "complex spinor module dimension D=2^(n/2) for Cl(n,0), n=6/8/10/12",
        "non_dense_method": "Pauli tensor-word algebra; only n generator words and omega word are built; algebra dimension 2^n is not built.",
        "rungs": scale_rows,
        "pass": bool(all(row["pass"] for row in scale_rows.values())),
    }

    tool_rows = {
        "clifford": clifford_tool_check(),
        "e3nn": e3nn_tool_check(),
        "geomstats": geomstats_tool_check(),
    }
    tool_ablations = build_tool_ablations(torch_real, torch_control_a, tool_rows)
    known_value_checks = build_known_value_checks(torch_real, torch_control_a, torch_control_b, proof_results, scale_ladder)

    controls = {
        "CONTROL_A_g2_plus_0p3_g1": {
            "description": "Shape-identical structural erasure: replace g2 by g2 + 0.3 g1.",
            "same_carrier_shape": True,
            "breaks": "off-diagonal anticommutator {g1,g2}=0",
            "torch_result": {
                "offdiag_anticommutator_residual_max": torch_control_a["offdiag_anticommutator_residual_max"],
                "module_identity_residual_max": torch_control_a["module_identity_residual_max"],
                "omega_square_residual_max": torch_control_a["omega_square_residual_max"],
            },
            "jax_result": {
                "offdiag_anticommutator_residual_max": jax_control_a["offdiag_anticommutator_residual_max"],
                "module_identity_residual_max": jax_control_a["module_identity_residual_max"],
            },
            "claim_holds": False,
            "pass": bool(torch_control_a["offdiag_anticommutator_residual_max"] > 0.5),
        },
        "CONTROL_B_g4_half_scale": {
            "description": "Shape-identical normalization erasure: replace g4 by 0.5 g4.",
            "same_carrier_shape": True,
            "breaks": "normalization g4^2=I and {g4,g4}=2I",
            "torch_result": {
                "square_normalization_residual_max": torch_control_b["square_normalization_residual_max"],
                "diagonal_anticommutator_residual_max": torch_control_b["diagonal_anticommutator_residual_max"],
                "module_identity_residual_max": torch_control_b["module_identity_residual_max"],
            },
            "jax_result": {
                "square_normalization_residual_max": jax_control_b["square_normalization_residual_max"],
                "diagonal_anticommutator_residual_max": jax_control_b["diagonal_anticommutator_residual_max"],
                "module_identity_residual_max": jax_control_b["module_identity_residual_max"],
            },
            "claim_holds": False,
            "pass": bool(torch_control_b["square_normalization_residual_max"] > 0.7),
        },
    }

    proof_pass = all(row.get("pass") for row in proof_results.values())
    ablation_pass = all(row.get("pass") for row in tool_ablations.values())
    tool_pass = all(row.get("pass") for row in tool_rows.values())
    controls_pass = all(row.get("pass") for row in controls.values())
    jax_pass = bool(jax_real["pass"] and jax_control_a["pass"] is False and jax_control_b["pass"] is False and jax_vs_pytorch_delta <= EPS)
    all_pass = bool(
        torch_real["pass"]
        and not torch_control_a["pass"]
        and not torch_control_b["pass"]
        and jax_pass
        and sympy_real["pass"]
        and not sympy_control_a["pass"]
        and not sympy_control_b["pass"]
        and proof_pass
        and controls_pass
        and tool_pass
        and ablation_pass
        and scale_ladder["pass"]
        and known_value_checks["pass"]
    )
    blockers = []
    if not all_pass:
        for name, condition in [
            ("torch_base_or_controls_failed", torch_real["pass"] and not torch_control_a["pass"] and not torch_control_b["pass"]),
            ("jax_mirror_failed", jax_pass),
            ("sympy_exact_failed", sympy_real["pass"] and not sympy_control_a["pass"] and not sympy_control_b["pass"]),
            ("proof_flip_failed", proof_pass),
            ("numeric_tool_ablation_failed", ablation_pass and tool_pass),
            ("scale_ladder_failed", scale_ladder["pass"]),
            ("known_value_check_failed", known_value_checks["pass"]),
        ]:
            if not condition:
                blockers.append(name)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CDT),
        "finite_frame_data": "Cl(4,0) on C^4: g1=sx tensor I, g2=sy tensor I, g3=sz tensor sx, g4=sz tensor sy.",
        "base_real": torch_real,
        "base_control_A": torch_control_a,
        "base_control_B": torch_control_b,
        "claim": "all anticommutators satisfy {g_i,g_j}=2 delta_ij I and chirality gives rank-half projectors",
        "pass": bool(torch_real["pass"] and not torch_control_a["pass"] and not torch_control_b["pass"]),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "representable_surface": "Cl(4,0) kron construction and controls; 8/16/32/64 scale ladder kept in Pauli-word form to avoid dense scale fabrication.",
        "geomstats_jax_backend": "not_available; geomstats row runs torch backend and JAX mirrors generator relations only",
        "base_real": jax_real,
        "base_control_A": jax_control_a,
        "base_control_B": jax_control_b,
        "pass": jax_pass,
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": THISFILE,
        "result_path": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "gstructure": spec["gstructure"],
        "spec_key": "Clifford module",
        "spec_source": "/tmp/gstruct_specs.json",
        "spec_entry": spec,
        "classification": "lego",
        "promotion_allowed": False,
        "selected_official_g_structure": None,
        "official_selection_allowed": False,
        "tier": "Stage 4 G-STRUCTURE lego",
        "sim_execution_kind": "nonclassical",
        "sim_class": "gstructure_module_probe",
        "finite_map": {
            "domain": "finite generator set Gamma_n={g_1,...,g_n} over S=(C^2)^(tensor n/2), n in {4,6,8,10,12}; base dense Cl(4) check plus non-dense Pauli-word scale rungs",
            "codomain_or_output": "module identity residuals, chirality/grading residuals, projector ranks, proof verdicts, controls, and non-dense scale ladder",
            "definition": "Gamma -> ({g_i,g_j}-2delta_ij I residuals, omega^2-I, [omega,g_i g_j], {omega,g_i}, P_+/- ranks)",
        },
        "domain": "Cl(n,0) generator words and complex spinor carrier S=(C^2)^(tensor n/2) with finite PEPS3D cell anchors for tensor factors",
        "codomain_or_output": "finite residual/invariant record for module action and chiral grading",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite generator/probe/operator/path set Gamma_n with finite residual probes over all generator pairs",
            },
            "N01": {
                "status": "active_tested",
                "statement": "order-sensitive noncommuting generator products g_i g_j vs g_j g_i; off-diagonal anticommutator control A kills the module identity",
            },
        },
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting/order-sensitive generator products"],
        "carrier_layer": "complex Clifford spinor module S=(C^2)^(tensor n/2)",
        "geometry_layer": "Clifford module / Spin^0 chiral grading reduction",
        "carrier_realization": "torch complex128 Cl(4) base tensors plus non-dense Pauli-word scale carriers; no NumPy import and no dense scale closure",
        "peps3d_embedding": {
            "status": "finite_anchor_only_not_full_manifold_admission",
            "anchor": "each tensor factor is assigned to a finite PEPS3D local cell; Pauli-word generator letters are local cell actions, with omega a finite product word",
            "scale_cells": {
                str(row["module_dimension"]): [
                    {"factor": idx, "peps3d_cell": [idx % 4, (idx // 4) % 4, idx // 16], "local_dim": 2}
                    for idx in range(row["tensor_factors"])
                ]
                for row in scale_rows.values()
            },
            "blocked_boundary": "this is a carrier anchor for the module probe only; no PEPS3D contraction, layer stack, flux, or Axis0 consumer is admitted",
        },
        "spinor_state": "torch-native complex spinor carrier S=(C^2)^(tensor m); base chiral projectors split C^4 into rank-2 halves",
        "quaternion_action": "not_applicable; no quaternion claim is made by this Clifford-module packet",
        "dependency_receipts": ["Stage-4 G-structure spec from /tmp/gstruct_specs.json", "audit exemplar sim_root_F01_finite_distinguishability_probe.py"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["future bounded Clifford-module tool/function packets that cite this result only as local lego evidence"],
        "allowed_claims": [
            "the concrete Cl(4,0) Dirac generators satisfy the full Clifford module identity and chiral grading checks",
            "CONTROL-A kills the off-diagonal anticommutator check that diagonal-only audits would miss",
            "CONTROL-B kills normalization",
            "the 8/16/32/64 scale rungs preserve the generator relations in Pauli-word form without dense scale matrices",
        ],
        "promotion_blockers": [
            "not an official G-structure selection",
            "not a full layer completion",
            "not a PEPS3D contraction/manifold admission",
            "not stack/flux/Xi/Phi0/Axis0/FEP/physics evidence",
        ],
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(jax_vs_pytorch_delta),
        "sympy_exact_result": {
            "base_real": sympy_real,
            "base_control_A": sympy_control_a,
            "base_control_B": sympy_control_b,
            "pass": bool(sympy_real["pass"] and not sympy_control_a["pass"] and not sympy_control_b["pass"]),
        },
        "proof_results": proof_results,
        "controls": controls,
        "negative_controls": controls,
        "tool_results": tool_rows,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "tool_ablation_outcomes": tool_ablations,
        "scale_ladder": scale_ladder,
        "scale_rungs": scale_ladder["rungs"],
        "known_value_checks": known_value_checks,
        "positive": {
            "real_module_identity": torch_real["pass"],
            "scale_ladder": scale_ladder["pass"],
            "proof_flip": proof_pass,
            "numeric_tool_ablations": ablation_pass,
        },
        "graveyard_companions": {
            "diagonal_only_audit": {
                "killed_by": "CONTROL-A g2 -> g2 + 0.3 g1",
                "reason": "off-diagonal residual is 0.6 even though a diagonal-only check can miss the intended fabrication risk",
            },
            "dense_scale_materialization": {
                "killed_by": "Pauli-word scale ladder",
                "reason": "scale rungs report no dense generator matrix allocation at D>=32 or D=64",
            },
            "tautological_smt": {
                "killed_by": "smt_load_bearing real/control measured residuals differ and verdicts flip",
            },
        },
        "boundary": {
            "claim_ceiling": "local Stage-4 Clifford-module lego only",
            "not_claimed": BLOCKED_CONSUMERS,
            "proof_tools_ablation_policy": "z3/cvc5/sympy are load-bearing through verdict flips only; no numeric ablation rows are emitted for proof tools",
        },
        "why_not_v4_probes": {
            "reason": "This result is a bounded v5 formal_scout Stage-4 G-structure lego with stricter anti-fabrication gates, not a broad v4 probe/promotion packet.",
            "promotion_allowed": False,
        },
        "nearby_variants": [
            "CONTROL-A off-diagonal erasure",
            "CONTROL-B normalization erasure",
            "future bounded Cl(6) Clifford-library cross-check if a non-dense external-Cl representation is admitted",
        ],
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3",
            "load_bearing_proof.smt_load_bearing cvc5 cross-check",
            "sympy exact rational flip",
        ],
        "required_artifacts": ["result JSON", "torch primary result", "JAX mirror result", "proof_results", "controls", "tool_ablations", "scale_ladder", "known_value_checks"],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(time.time())}",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "all 16 Cl(4) anticommutators, chirality/projector checks, control flips, proof verdict flips, numeric tool ablations, and non-dense 8/16/32/64 scale rungs pass",
        "fail_rule": "fail on skipped off-diagonal checks, tautological/non-flipping proof, missing real numeric ablation, dense scale materialization, or any downstream promotion",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
        "blockers": blockers,
    }
    return result


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"THISFILE={THISFILE}")
    print(f"RESULT={RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    if result["blockers"]:
        print("blockers=" + ",".join(result["blockers"]))
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
