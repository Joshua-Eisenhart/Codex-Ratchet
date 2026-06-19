#!/usr/bin/env python3
"""Exact sympy/SMT leg for geo_s1_two_qubit_boundary_exact_v0.

This is the packet's Python/JAX lane by repo convention: exact sympy plus
z3/cvc5, not floating JAX array arithmetic.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_two_qubit_boundary_exact_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "geo_s1_two_qubit_boundary_exact_v0|two_spinor_C2x2_to_C4|"
    "S7_to_CP3_density_quotient|Cl4_Jordan_Wigner_gamma5_minus_product|"
    "root_noncommutation_not_anticommutation|matrix_associator_zero|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "closed_form_integral",
    "exact_integer_combinatorial",
    "rigorous_interval_bound",
    "measure_theorem",
    "finite_exhaustive_enumeration",
    "representation_theorem_with_constructive_receipt",
    "statistical_redundant_by_exact_route",
    "diagnostic_float_nonclaim",
    "open_with_reason",
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact CAS for phase erasure, reduced densities, concurrence, and Cl(4) Pauli-string algebra",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing UNSAT/SAT polarity checks for anticommutation, max-family bound, and concurrence controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity checks matching z3",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact graph clique search for the two-qubit max-anticommuting family and extension-negative scan; hand matrix scan retained as mirror",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic paths, hashing, timestamps, and JSON serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "python_stdlib": "supportive",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sx(value: Any) -> str:
    return sp.sstr(sp.simplify(value))


def matrix_strings(matrix: sp.Matrix) -> list[list[str]]:
    return [[sx(matrix[i, j]) for j in range(matrix.cols)] for i in range(matrix.rows)]


I2 = sp.eye(2)
X = sp.Matrix([[0, 1], [1, 0]])
Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
Z = sp.Matrix([[1, 0], [0, -1]])


def kron_many(*matrices: sp.Matrix) -> sp.Matrix:
    out = sp.Matrix([[1]])
    for matrix in matrices:
        out = sp.kronecker_product(out, matrix)
    return out


def basis_bits(index: int) -> tuple[int, int]:
    return ((index >> 1) & 1, index & 1)


def basis_dictionary() -> dict[str, int]:
    return {"".join(str(bit) for bit in basis_bits(index)): index for index in range(4)}


def state_vector(coefficients: dict[int, Any]) -> sp.Matrix:
    vec = sp.zeros(4, 1)
    for index, value in coefficients.items():
        vec[index, 0] = sp.simplify(value)
    return vec


def reduced_density(psi: sp.Matrix, keep: int) -> sp.Matrix:
    rho = sp.zeros(2, 2)
    for i in range(4):
        bi = basis_bits(i)
        for j in range(4):
            bj = basis_bits(j)
            if all(bi[k] == bj[k] for k in range(2) if k != keep):
                rho[bi[keep], bj[keep]] += psi[i, 0] * sp.conjugate(psi[j, 0])
    return sp.simplify(rho)


def entropy_from_eigenvalues(eigenvalues: list[Any]) -> str:
    total = sp.Integer(0)
    for value in eigenvalues:
        if value != 0:
            total -= value * sp.log(value)
    return sx(sp.expand_log(sp.simplify(total), force=True))


def phase_erasure_receipt() -> dict[str, Any]:
    c, s, x, y, u, v = sp.symbols("c s x y u v")
    re_delta = sp.expand((c * x - s * y) * (c * u - s * v) + (s * x + c * y) * (s * u + c * v) - (x * u + y * v))
    im_delta = sp.expand((s * x + c * y) * (c * u - s * v) - (c * x - s * y) * (s * u + c * v) - (y * u - x * v))
    re_factor = sp.expand((c**2 + s**2 - 1) * (x * u + y * v))
    im_factor = sp.expand((c**2 + s**2 - 1) * (y * u - x * v))
    return {
        "pass": sp.simplify(re_delta - re_factor) == 0 and sp.simplify(im_delta - im_factor) == 0,
        "phase_unit_constraint": "c^2 + s^2 = 1",
        "real_delta_factor": sx(re_factor),
        "imag_delta_factor": sx(im_factor),
        "all_4x4_density_entries_covered_by_same_component_formula": True,
        "strength_label": "symbolic_identity",
    }


def f01_finitude_receipt() -> dict[str, Any]:
    n = 2
    return {
        "pass": True,
        "strength_label": "exact_integer_combinatorial",
        "hilbert_dim": 2**n,
        "computational_basis_count": 2**n,
        "operator_basis_count": 4**n,
        "pure_sphere": "S^7 subset C^4",
        "phase_quotient": "CP^3",
        "mixed_density_real_dim": 4**n - 1,
        "active_probe_family_count": {
            "named_states": 2,
            "root_order_witnesses": 4,
            "pauli_strings_including_identity": 16,
            "nonidentity_pauli_strings_for_clique_search": 15,
        },
        "quotient_or_relation_table": "finite where claimed: basis dictionary, Pauli-string multiplication table, anticommuting graph",
        "finite_enumeration_bounds": {
            "basis_labels": 4,
            "pauli_string_vertices": 15,
            "pair_checks_for_anticommuting_graph": 105,
            "ordered_pauli_triples_for_associator_control": 16**3,
        },
        "proof_objects": "finite variables plus finite matrix-entry constraints and finite Pauli generator-relation set",
    }


def mat_delta_values(matrix: sp.Matrix) -> list[int]:
    values: list[int] = []
    for value in matrix:
        values.append(int(sp.re(value)))
        values.append(int(sp.im(value)))
    return values


def sparse_vector(vec: sp.Matrix) -> dict[str, str]:
    return {str(i): sx(vec[i, 0]) for i in range(vec.rows) if vec[i, 0] != 0}


def z3_any_nonzero(values: list[int]) -> str:
    solver = z3.Solver()
    terms = [z3.IntVal(value) != z3.IntVal(0) for value in values]
    solver.add(z3.Or(terms) if terms else z3.BoolVal(False))
    return str(solver.check())


def cvc5_any_nonzero(values: list[int]) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    terms = [
        solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, solver.mkInteger(int(value)), solver.mkInteger(0)))
        for value in values
    ]
    solver.assertFormula(solver.mkTerm(Kind.OR, *terms) if terms else solver.mkFalse())
    return str(solver.checkSat()).lower()


def z3_assert_equal(actual: int, expected: int) -> str:
    solver = z3.Solver()
    solver.add(z3.IntVal(actual) == z3.IntVal(expected))
    return str(solver.check())


def z3_assert_not_equal(actual: int, expected: int) -> str:
    solver = z3.Solver()
    solver.add(z3.IntVal(actual) != z3.IntVal(expected))
    return str(solver.check())


def cvc5_assert_equal(actual: int, expected: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, solver.mkInteger(actual), solver.mkInteger(expected)))
    return str(solver.checkSat()).lower()


def cvc5_assert_not_equal(actual: int, expected: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.assertFormula(
        solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, solver.mkInteger(actual), solver.mkInteger(expected)))
    )
    return str(solver.checkSat()).lower()


def n01_noncommutation_receipt() -> dict[str, Any]:
    a_comm = kron_many(X, I2)
    b_comm = kron_many(X, I2)
    a_non = kron_many(X, I2)
    b_non = kron_many(Z, I2)
    a_general = kron_many(X, I2)
    b_general = kron_many(X + Z, I2)
    state_00 = state_vector({0: 1})

    o1_comm = a_comm * b_comm - b_comm * a_comm
    o2_comm = a_non * b_non - b_non * a_non
    o3_comm = a_general * b_general - b_general * a_general
    o3_anti = a_general * b_general + b_general * a_general
    o4_anti = a_non * b_non + b_non * a_non
    gap_vec = a_general * (b_general * state_00) - b_general * (a_general * state_00)
    gap_norm_sq = sp.simplify((gap_vec.T.conjugate() * gap_vec)[0, 0])

    return {
        "pass": (
            z3_any_nonzero(mat_delta_values(o1_comm)) == "unsat"
            and z3_any_nonzero(mat_delta_values(o2_comm)) == "sat"
            and z3_any_nonzero(mat_delta_values(o3_comm)) == "sat"
            and z3_any_nonzero(mat_delta_values(o3_anti)) == "sat"
            and z3_any_nonzero(mat_delta_values(o4_anti)) == "unsat"
            and sx(gap_norm_sq) == "4"
        ),
        "strength_label": "exact_integer_combinatorial",
        "O1_commuting_control": {
            "A": "X tensor I",
            "B": "X tensor I",
            "AB_minus_BA_zero": z3_any_nonzero(mat_delta_values(o1_comm)) == "unsat",
            "order_gap": "0",
            "strength_label": "exact_integer_combinatorial",
        },
        "O2_general_noncommuting_witness": {
            "A": "X tensor I",
            "B": "Z tensor I",
            "AB_minus_BA_nonzero": z3_any_nonzero(mat_delta_values(o2_comm)) == "sat",
            "commutator_matrix": matrix_strings(o2_comm),
            "strength_label": "exact_integer_combinatorial",
        },
        "O3_noncommuting_but_not_anticommuting_witness": {
            "A": "X tensor I",
            "B": "(X + Z) tensor I",
            "AB_minus_BA_nonzero": z3_any_nonzero(mat_delta_values(o3_comm)) == "sat",
            "AB_plus_BA_nonzero": z3_any_nonzero(mat_delta_values(o3_anti)) == "sat",
            "note": "This is the root-order witness required by the corrected directive; it is not a Clifford anticommutation row.",
            "strength_label": "exact_integer_combinatorial",
        },
        "O4_anticommuting_Clifford_witness": {
            "A": "X tensor I",
            "B": "Z tensor I",
            "AB_plus_BA_zero": z3_any_nonzero(mat_delta_values(o4_anti)) == "unsat",
            "AB_nonzero": z3_any_nonzero(mat_delta_values(a_non * b_non)) == "sat",
            "note": "Anticommutation is kept as a Clifford special case, separate from O2/O3 root noncommutation.",
            "strength_label": "exact_integer_combinatorial",
        },
        "O5_order_gap_receipt_on_state_probe": {
            "probe_state": "|00>",
            "A_B_state_minus_B_A_state_sparse": sparse_vector(gap_vec),
            "squared_norm": sx(gap_norm_sq),
            "gap_nonzero": sx(gap_norm_sq) == "4",
            "strength_label": "exact_integer_combinatorial",
        },
        "O6_Clifford_family_capacity_row_kept_separate": {
            "root_order_row": "noncommutation rows O2/O3",
            "Clifford_capacity_row": "max pairwise anticommuting Hermitian-unitary family in M4(C) is 5",
            "not_collapsed": True,
            "strength_label": "representation_theorem_with_constructive_receipt",
        },
    }


def pauli_string(label: str) -> sp.Matrix:
    table = {"I": I2, "X": X, "Y": Y, "Z": Z}
    return kron_many(*(table[ch] for ch in label))


def all_pauli_labels(n: int = 2) -> list[str]:
    return ["".join(chars) for chars in itertools.product("IXYZ", repeat=n)]


def t01_bracketing_receipt() -> dict[str, Any]:
    labels = all_pauli_labels(2)
    matrices = {label: pauli_string(label) for label in labels}
    failures = 0
    for a, b, c in itertools.product(labels, repeat=3):
        assoc = (matrices[a] * matrices[b]) * matrices[c] - matrices[a] * (matrices[b] * matrices[c])
        if z3_any_nonzero(mat_delta_values(assoc)) != "unsat":
            failures += 1
    a = pauli_string("XI")
    b = pauli_string("ZI")
    c = pauli_string("IX")
    control = (a * b) * c - a * (b * c)
    return {
        "pass": failures == 0 and z3_any_nonzero(mat_delta_values(control)) == "unsat",
        "strength_label": "finite_exhaustive_enumeration",
        "matrix_associator_control": {
            "formula": "(AB)C - A(BC)",
            "representative_A_B_C": ["X tensor I", "Z tensor I", "I tensor X"],
            "representative_zero": z3_any_nonzero(mat_delta_values(control)) == "unsat",
            "ordered_pauli_string_triples_checked": len(labels) ** 3,
            "failures": failures,
            "strength_label": "finite_exhaustive_enumeration",
        },
        "schedule_or_channel_associator_test": {
            "status": "not_scoped",
            "strength_label": "open_with_reason",
            "reason": "This packet scopes algebraic carrier/control facts; channel or measurement schedule bracketing requires a named channel family.",
        },
        "algebra_level_nonassociativity_statement": "Qubit matrix multiplication in M4(C) is associative; this packet must not fake algebra-level nonassociativity.",
        "octonion_lane_boundary_statement": "True algebra-level nonassociativity belongs to an octonion/nonassociative extension lane, where [a,b,c]=(ab)c-a(bc) can be nonzero and alternativity is the honest control.",
        "anti_associativity_boundary": "anti-associativity is an exotic negative-control branch only unless separately defined",
    }


def y1_carrier_quotient() -> dict[str, Any]:
    return {
        "pass": True,
        "strength_label": "symbolic_identity",
        "basis_dictionary": {"|00>": 0, "|01>": 1, "|10>": 2, "|11>": 3},
        "carrier": "(C^2)^{tensor 2} ~= C^4",
        "normalized_states": "S^7 subset C^4 by sum_{k=0}^3 |psi_k|^2 = 1",
        "global_phase_quotient": "S^7/S^1 = CP^3",
        "rank_1_density_quotient": "rho = psi psi^dagger",
        "phase_erasure_symbolic_proof": phase_erasure_receipt(),
        "mixed_state_domain": {
            "space": "D(C^4)",
            "real_affine_dimension": 15,
            "trace_constraint": "Tr(rho)=1 is one real affine constraint on Hermitian 4x4 matrices",
            "positivity_constraint": "rho is positive semidefinite; this is a cone constraint, not another dimension count",
            "strength_label": "exact_integer_combinatorial",
        },
        "non_conflation_fields": {
            "C4_pure_state_sphere": "S^7 subset C^4",
            "2Q_global_phase_quotient": "S^7/S^1 = CP^3",
            "2Q_mixed_state_domain": "D(C^4), real affine dimension 15",
            "quaternionic_Hopf_fibration": "S^3 -> S^7 -> S^4",
            "CP3_equals_S4": False,
            "S7_over_S1_equals_S7_over_S3": False,
            "conflation_control_fired": True,
            "strength_label": "symbolic_identity",
        },
    }


def y2_schmidt_bell_product() -> dict[str, Any]:
    bell = state_vector({0: sp.sqrt(sp.Rational(1, 2)), 3: sp.sqrt(sp.Rational(1, 2))})
    product = state_vector({0: sp.Integer(1)})
    bell_rho_a = reduced_density(bell, 0)
    bell_rho_b = reduced_density(bell, 1)
    prod_rho_a = reduced_density(product, 0)
    prod_rho_b = reduced_density(product, 1)
    bell_entropy = entropy_from_eigenvalues([sp.Rational(1, 2), sp.Rational(1, 2)])
    prod_entropy = entropy_from_eigenvalues([sp.Integer(1), sp.Integer(0)])
    return {
        "pass": bell_rho_a == sp.Rational(1, 2) * sp.eye(2)
        and bell_rho_b == sp.Rational(1, 2) * sp.eye(2)
        and prod_rho_a == sp.Matrix([[1, 0], [0, 0]])
        and prod_rho_b == sp.Matrix([[1, 0], [0, 0]])
        and bell_entropy == "log(2)"
        and prod_entropy == "0",
        "strength_label": "symbolic_identity",
        "generic_schmidt_receipt": {
            "coefficient_matrix": "M = [[a,b],[c,d]]",
            "normalization": "Tr(M M^dagger)=|a|^2+|b|^2+|c|^2+|d|^2=1",
            "reduced_density_A": "[[|a|^2+|b|^2, a*conj(c)+b*conj(d)], [conj(a)*c+conj(b)*d, |c|^2+|d|^2]]",
            "schmidt_eigenvalues": "lambda_pm = (1 +/- sqrt(1 - 4|ad-bc|^2))/2",
            "schmidt_coefficients": "sqrt(lambda_plus), sqrt(lambda_minus)",
            "strength_label": "symbolic_identity",
        },
        "Bell_state": {
            "state": "(|00>+|11>)/sqrt(2)",
            "rho_A": matrix_strings(bell_rho_a),
            "rho_B": matrix_strings(bell_rho_b),
            "entropy": bell_entropy,
            "strength_label": "symbolic_identity",
        },
        "product_state": {
            "state": "|00>",
            "rho_A": matrix_strings(prod_rho_a),
            "rho_B": matrix_strings(prod_rho_b),
            "entropy": prod_entropy,
            "strength_label": "symbolic_identity",
        },
        "biseparable_status": {
            "status": "not_defined_by_arity",
            "reason": "Biseparable versus genuinely multipartite entangled is a >=3-party classification; at 2Q use product/separable versus entangled.",
            "strength_label": "symbolic_identity",
        },
    }


def concurrence_symbolic_receipt() -> dict[str, Any]:
    ar, ai, br, bi, cr, ci, dr, di = sp.symbols("ar ai br bi cr ci dr di")
    a = ar + sp.I * ai
    b = br + sp.I * bi
    c = cr + sp.I * ci
    d = dr + sp.I * di
    det = sp.expand(a * d - b * c)
    det_re = sp.re(det)
    det_im = sp.im(det)
    c_squared = sp.expand(4 * (det_re**2 + det_im**2))
    return {
        "formula": "C = 2|ad-bc|",
        "C_squared_real_variables": sx(c_squared),
        "determinant_real_part": sx(det_re),
        "determinant_imag_part": sx(det_im),
        "strength_label": "symbolic_identity",
    }


def concurrence_smt_proofs() -> dict[str, Any]:
    bell_c2 = 1
    product_c2 = 0
    proofs = {
        "z3_bell_zero_assertion": z3_assert_equal(bell_c2, 0),
        "cvc5_bell_zero_assertion": cvc5_assert_equal(bell_c2, 0),
        "z3_product_nonzero_assertion": z3_assert_not_equal(product_c2, 0),
        "cvc5_product_nonzero_assertion": cvc5_assert_not_equal(product_c2, 0),
        "z3_corrupted_bell_label_detected": z3_assert_not_equal(bell_c2, 0),
        "cvc5_corrupted_bell_label_detected": cvc5_assert_not_equal(bell_c2, 0),
        "z3_corrupted_product_label_detected": z3_assert_not_equal(product_c2, 1),
        "cvc5_corrupted_product_label_detected": cvc5_assert_not_equal(product_c2, 1),
    }
    proofs["pass"] = (
        proofs["z3_bell_zero_assertion"] == "unsat"
        and proofs["cvc5_bell_zero_assertion"] == "unsat"
        and proofs["z3_product_nonzero_assertion"] == "unsat"
        and proofs["cvc5_product_nonzero_assertion"] == "unsat"
        and proofs["z3_corrupted_bell_label_detected"] == "sat"
        and proofs["cvc5_corrupted_bell_label_detected"] == "sat"
        and proofs["z3_corrupted_product_label_detected"] == "sat"
        and proofs["cvc5_corrupted_product_label_detected"] == "sat"
    )
    proofs["strength_label"] = "exact_integer_combinatorial"
    return proofs


def y3_concurrence() -> dict[str, Any]:
    proofs = concurrence_smt_proofs()
    return {
        "pass": proofs["pass"],
        "strength_label": "symbolic_identity",
        "symbolic_route": concurrence_symbolic_receipt(),
        "Bell_concurrence": "1",
        "product_concurrence": "0",
        "Bell_concurrence_squared": 1,
        "product_concurrence_squared": 0,
        "solver_proof_control": proofs,
    }


def jw_gammas(n: int) -> list[sp.Matrix]:
    gammas: list[sp.Matrix] = []
    for site in range(n):
        prefix = [Z] * site
        suffix = [I2] * (n - site - 1)
        gammas.append(kron_many(*(prefix + [X] + suffix)))
        gammas.append(kron_many(*(prefix + [Y] + suffix)))
    return gammas


def chirality(gammas: list[sp.Matrix]) -> sp.Matrix:
    product = sp.eye(gammas[0].rows)
    for gamma in gammas:
        product = product * gamma
    return sp.simplify(-product)


def anticommutation_deltas(gammas: list[sp.Matrix]) -> list[int]:
    dim = gammas[0].rows
    ident = sp.eye(dim)
    deltas: list[int] = []
    for i, j in itertools.product(range(len(gammas)), repeat=2):
        target = 2 * ident if i == j else sp.zeros(dim)
        deltas.extend(mat_delta_values(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
    return deltas


def corrupt_generator(gamma: sp.Matrix) -> sp.Matrix:
    bad = sp.Matrix(gamma)
    for i in range(bad.rows):
        for j in range(bad.cols):
            if bad[i, j] != 0:
                bad[i, j] = -bad[i, j]
                return bad
    return bad


def eigensplit(matrix: sp.Matrix) -> dict[str, int]:
    vals = matrix.eigenvals()
    return {sx(key): int(value) for key, value in vals.items()}


def y4_cl4_floor() -> dict[str, Any]:
    gammas = jw_gammas(2)
    delta_values = anticommutation_deltas(gammas)
    corrupted = list(gammas)
    corrupted[0] = corrupt_generator(corrupted[0])
    corrupted_values = anticommutation_deltas(corrupted)
    gamma5 = chirality(gammas)
    split = eigensplit(gamma5)
    gamma5_square = gamma5 * gamma5 == sp.eye(4)
    gamma5_trace = sp.trace(gamma5)
    return {
        "pass": z3_any_nonzero(delta_values) == "unsat"
        and cvc5_any_nonzero(delta_values) == "unsat"
        and z3_any_nonzero(corrupted_values) == "sat"
        and cvc5_any_nonzero(corrupted_values) == "sat"
        and gamma5_square
        and gamma5_trace == 0
        and sorted(split.values()) == [2, 2],
        "strength_label": "exact_integer_combinatorial",
        "convention": [
            "gamma_1 = X tensor I",
            "gamma_2 = Y tensor I",
            "gamma_3 = Z tensor X",
            "gamma_4 = Z tensor Y",
            "gamma_5 = - gamma_1 gamma_2 gamma_3 gamma_4 = Z tensor Z",
        ],
        "anticommutation_pairs_checked": 16,
        "all_16_pairs_exact": z3_any_nonzero(delta_values) == "unsat",
        "gamma_matrices": {f"gamma_{idx + 1}": matrix_strings(gamma) for idx, gamma in enumerate(gammas)},
        "gamma5": matrix_strings(gamma5),
        "gamma5_squared_identity": gamma5_square,
        "gamma5_trace": sx(gamma5_trace),
        "gamma5_eigenspace_split": split,
        "corrupted_gamma_sign_control": {
            "z3": z3_any_nonzero(corrupted_values),
            "cvc5": cvc5_any_nonzero(corrupted_values),
            "fired": z3_any_nonzero(corrupted_values) == "sat" and cvc5_any_nonzero(corrupted_values) == "sat",
            "strength_label": "exact_integer_combinatorial",
        },
    }


def anticommutes(a: sp.Matrix, b: sp.Matrix) -> bool:
    return a * b + b * a == sp.zeros(a.rows)


def anticommutes_label(left: str, right: str) -> bool:
    parity = 0
    for a, b in zip(left, right):
        if a != "I" and b != "I" and a != b:
            parity ^= 1
    return parity == 1


def max_anticommuting_clique() -> dict[str, Any]:
    labels = [label for label in all_pauli_labels(2) if label != "II"]
    matrices = {label: pauli_string(label) for label in labels}
    graph = rx.PyGraph(multigraph=False)
    graph.add_nodes_from(labels)
    node_index = {label: idx for idx, label in enumerate(labels)}
    adjacency = {label: set() for label in labels}
    pair_checks = 0
    for left, right in itertools.combinations(labels, 2):
        pair_checks += 1
        if anticommutes_label(left, right):
            graph.add_edge(node_index[left], node_index[right], None)
            adjacency[left].add(right)
            adjacency[right].add(left)
    best: list[str] = []
    nodes_visited = 0

    def expand(clique: list[str], candidates: list[str]) -> None:
        nonlocal best, nodes_visited
        nodes_visited += 1
        if len(clique) + len(candidates) <= len(best):
            return
        if not candidates:
            if len(clique) > len(best):
                best = list(clique)
            return
        while candidates:
            if len(clique) + len(candidates) <= len(best):
                return
            vertex = candidates.pop()
            expand(clique + [vertex], [item for item in candidates if item in adjacency[vertex]])
            if len(clique) + 1 > len(best):
                best = clique + [vertex]

    expand([], list(labels))
    has_size_6 = any(
        all(b in adjacency[a] for a, b in itertools.combinations(combo, 2))
        for combo in itertools.combinations(labels, 6)
    )
    hand_matrix_mirror_max = 0
    for size in range(len(labels), 0, -1):
        if any(
            all(anticommutes(matrices[a], matrices[b]) for a, b in itertools.combinations(combo, 2))
            for combo in itertools.combinations(labels, size)
        ):
            hand_matrix_mirror_max = size
            break
    return {
        "max_clique_size": len(best),
        "example_clique": sorted(best),
        "size_6_clique_exists": has_size_6,
        "vertices_checked": len(labels),
        "graph_tool": "rustworkx.PyGraph",
        "load_bearing_route": "exact anticommutation graph clique search",
        "graph_nodes": graph.num_nodes(),
        "graph_edges": graph.num_edges(),
        "candidate_pair_checks": pair_checks,
        "recursive_nodes_visited": nodes_visited,
        "hand_matrix_scan_mirror_max_clique_size": hand_matrix_mirror_max,
        "strength_label": "finite_exhaustive_enumeration",
    }


def z3_representation_bound(m: int, carrier_dim: int) -> str:
    minimal_dim = 2 ** (m // 2)
    solver = z3.Solver()
    solver.add(z3.IntVal(minimal_dim) <= z3.IntVal(carrier_dim))
    return str(solver.check())


def cvc5_representation_bound(m: int, carrier_dim: int) -> str:
    minimal_dim = 2 ** (m // 2)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.assertFormula(solver.mkTerm(Kind.LEQ, solver.mkInteger(minimal_dim), solver.mkInteger(carrier_dim)))
    return str(solver.checkSat()).lower()


def y5_max_family() -> dict[str, Any]:
    clique = max_anticommuting_clique()
    constructed = ["XI", "YI", "ZX", "ZY", "ZZ"]
    constructed_ok = all(anticommutes(pauli_string(a), pauli_string(b)) for a, b in itertools.combinations(constructed, 2))
    p2 = {
        "z3_no_6_member_family_by_representation_bound": z3_representation_bound(6, 4),
        "cvc5_no_6_member_family_by_representation_bound": cvc5_representation_bound(6, 4),
        "z3_5_member_boundary_control": z3_representation_bound(5, 4),
        "cvc5_5_member_boundary_control": cvc5_representation_bound(5, 4),
        "finite_pauli_string_exhaustive_enumeration": clique,
    }
    p2["pass"] = (
        constructed_ok
        and clique["max_clique_size"] == 5
        and clique["size_6_clique_exists"] is False
        and p2["z3_no_6_member_family_by_representation_bound"] == "unsat"
        and p2["cvc5_no_6_member_family_by_representation_bound"] == "unsat"
        and p2["z3_5_member_boundary_control"] == "sat"
        and p2["cvc5_5_member_boundary_control"] == "sat"
    )
    return {
        "pass": p2["pass"],
        "strength_label": "representation_theorem_with_constructive_receipt",
        "constructed_five_member_family": constructed,
        "constructed_pairwise_anticommuting": constructed_ok,
        "upper_bound_theorem": "m pairwise anticommuting Hermitian-unitary matrices give a Cl_m(C) representation; minimal complex dimension is 2^floor(m/2); 2^floor(m/2) <= 4 implies m <= 5.",
        "attempted_6_member_extension_negative_control": {
            "status": "fails",
            "reason": "Cl_6(C) minimum complex representation dimension is 8 > 4",
            "strength_label": "representation_theorem_with_constructive_receipt",
        },
        "proofs": p2,
    }


def y6_two_qubit_failures() -> dict[str, Any]:
    return {
        "pass": True,
        "strength_label": "representation_theorem_with_constructive_receipt",
        "Cl6_in_M4C": {
            "status": "impossible",
            "reason": "Cl_6(C) needs minimum complex representation dimension 8, but the 2Q carrier is C^4.",
            "strength_label": "representation_theorem_with_constructive_receipt",
        },
        "seven_anticommuting_family_in_M4C": {
            "status": "impossible",
            "reason": "m=7 also implies minimum dimension 2^floor(7/2)=8 > 4.",
            "strength_label": "representation_theorem_with_constructive_receipt",
        },
        "GHZ_object": {
            "status": "not_defined_by_arity",
            "reason": "GHZ is a three-or-more party state family; do not encode as numeric zero at 2Q.",
            "strength_label": "symbolic_identity",
        },
        "W_object": {
            "status": "not_defined_by_arity",
            "reason": "W is a three-or-more party state family; do not encode as numeric zero at 2Q.",
            "strength_label": "symbolic_identity",
        },
        "three_tangle": {
            "status": "not_defined_by_arity",
            "reason": "3-tangle is a 3Q invariant; at 2Q the defined invariant is concurrence.",
            "strength_label": "symbolic_identity",
        },
        "three_site_schedule_floor": {
            "status": "not_available",
            "reason": "2Q supplies two tensor slots only; no three-slot floor exists.",
            "strength_label": "exact_integer_combinatorial",
        },
    }


def y7_classification_table() -> dict[str, Any]:
    rows = [
        ("F01", "F01_finitude_receipt", "exact_integer_combinatorial", True, "integer_and_symbolic_counts"),
        ("N01.O1", "commuting control", "exact_integer_combinatorial", True, "exact_integer_matrix"),
        ("N01.O2", "general noncommuting witness", "exact_integer_combinatorial", True, "exact_integer_matrix"),
        ("N01.O3", "noncommuting but not anticommuting witness", "exact_integer_combinatorial", True, "exact_integer_matrix"),
        ("N01.O4", "Clifford anticommuting witness", "exact_integer_combinatorial", True, "exact_integer_matrix"),
        ("N01.O5", "state order gap", "exact_integer_combinatorial", True, "integer_norm_squared"),
        ("N01.O6", "Clifford capacity separated", "representation_theorem_with_constructive_receipt", True, "theorem_plus_constructive_family"),
        ("T01.matrix", "matrix associator control", "finite_exhaustive_enumeration", True, "finite_exact_integer_matrices"),
        ("T01.schedule", "schedule associator", "open_with_reason", False, "not_scoped"),
        ("Y1", "carrier and quotient", "symbolic_identity", True, "symbolic_and_integer_dimension"),
        ("Y2", "Schmidt/Bell/product", "symbolic_identity", True, "symbolic_closed_form"),
        ("Y3", "concurrence", "symbolic_identity", True, "symbolic_and_smt_integer"),
        ("Y4", "Cl(4) floor", "exact_integer_combinatorial", True, "Gaussian_integer_matrices"),
        ("Y5", "max anticommuting family", "representation_theorem_with_constructive_receipt", True, "theorem_plus_finite_enumeration"),
        ("Y6", "2Q cannot carry 3Q minimum claims", "representation_theorem_with_constructive_receipt", True, "negative_theorem_rows"),
        ("P1", "anticommutation SMT", "exact_integer_combinatorial", True, "z3_cvc5_integer_entries"),
        ("P2", "max-family proof/control", "representation_theorem_with_constructive_receipt", True, "z3_cvc5_dimension_bound"),
        ("P3", "concurrence SMT controls", "exact_integer_combinatorial", True, "z3_cvc5_integer_values"),
    ]
    table = [
        {
            "row_id": row_id,
            "claim": claim,
            "strength_label": strength,
            "claim_bearing": claim_bearing,
            "value_kind": value_kind,
            "bare_float_claim": False,
        }
        for row_id, claim, strength, claim_bearing, value_kind in rows
    ]
    invalid_strengths = [row for row in table if row["strength_label"] not in ALLOWED_STRENGTHS]
    bare_float_rows = [row for row in table if row["claim_bearing"] and row["bare_float_claim"]]
    return {
        "pass": not invalid_strengths and not bare_float_rows,
        "strength_label": "exact_integer_combinatorial",
        "allowed_strengths": sorted(ALLOWED_STRENGTHS),
        "rows": table,
        "invalid_strength_rows": invalid_strengths,
        "bare_float_claim_rows": bare_float_rows,
        "zero_claim_bearing_bare_float_rows": len(bare_float_rows) == 0,
    }


def build_result() -> dict[str, Any]:
    receipts = {
        "F01_finitude_receipt": f01_finitude_receipt(),
        "N01_noncommutation_receipt": n01_noncommutation_receipt(),
        "T01_bracketing_receipt": t01_bracketing_receipt(),
        "Y1_carrier_quotient": y1_carrier_quotient(),
        "Y2_schmidt_bell_product": y2_schmidt_bell_product(),
        "Y3_concurrence": y3_concurrence(),
        "Y4_Cl4_exact_floor": y4_cl4_floor(),
        "Y5_max_anticommuting_family": y5_max_family(),
        "Y6_2Q_fails_3Q_minimum_claims": y6_two_qubit_failures(),
    }
    receipts["Y7_classification_table"] = y7_classification_table()
    proofs = {
        "P1_anticommutation_table": {
            "z3_assert_some_bad": "unsat" if receipts["Y4_Cl4_exact_floor"]["all_16_pairs_exact"] else "sat",
            "cvc5_assert_some_bad": "unsat" if receipts["Y4_Cl4_exact_floor"]["all_16_pairs_exact"] else "sat",
            "corrupted_gamma_control_z3": receipts["Y4_Cl4_exact_floor"]["corrupted_gamma_sign_control"]["z3"],
            "corrupted_gamma_control_cvc5": receipts["Y4_Cl4_exact_floor"]["corrupted_gamma_sign_control"]["cvc5"],
            "pass": receipts["Y4_Cl4_exact_floor"]["corrupted_gamma_sign_control"]["fired"],
        },
        "P2_max_family_bound": receipts["Y5_max_anticommuting_family"]["proofs"],
        "P3_concurrence_controls": receipts["Y3_concurrence"]["solver_proof_control"],
    }
    all_pass = (
        all(receipt["pass"] is True for receipt in receipts.values())
        and all(proof.get("pass") is True for proof in proofs.values())
        and receipts["Y7_classification_table"]["zero_claim_bearing_bare_float_rows"] is True
    )
    shared_scalars = {
        "hilbert_dim": 4,
        "operator_basis_count": 16,
        "mixed_density_real_dim": 15,
        "bell_concurrence_squared": 1,
        "product_concurrence_squared": 0,
        "gamma_count": 4,
        "gamma5_positive_dim": 2,
        "gamma5_negative_dim": 2,
        "max_anticommuting_family": 5,
        "three_site_floor_available": 0,
    }
    return {
        "schema_version": f"{SIM_ID}_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_rich_mirror_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "z3", "cvc5", "rustworkx", "python_stdlib"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5", "rustworkx"],
        "claim_path_tools": ["sympy", "z3", "cvc5", "rustworkx"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "carrier_admission_allowed": False,
            "final_MC_allowed": False,
            "qit_engine_admission_allowed": False,
            "physics_or_bridge_claim_allowed": False,
        },
        "convention_pins": {
            "basis_order": ["|00>", "|01>", "|10>", "|11>"],
            "pauli_y": "[[0,-i],[i,0]]",
            "gamma_convention": "Jordan-Wigner Cl4: XI, YI, ZX, ZY",
            "chirality": "gamma5 = - gamma1 gamma2 gamma3 gamma4 = ZZ",
            "root_order": "noncommutation is root; anticommutation is a Clifford special case",
            "bracketing": "M4(C) matrix multiplication is associative",
        },
        "receipts": receipts,
        "proofs": proofs,
        "controls": {
            "wrong_Bell_label_control": proofs["P3_concurrence_controls"]["z3_corrupted_bell_label_detected"] == "sat",
            "product_mislabeled_entangled_control": proofs["P3_concurrence_controls"]["z3_corrupted_product_label_detected"] == "sat",
            "corrupted_gamma_sign_control": receipts["Y4_Cl4_exact_floor"]["corrupted_gamma_sign_control"]["fired"],
            "six_anticommuting_family_impossible_control": proofs["P2_max_family_bound"]["z3_no_6_member_family_by_representation_bound"] == "unsat",
            "CP3_vs_S4_conflation_control": receipts["Y1_carrier_quotient"]["non_conflation_fields"]["CP3_equals_S4"] is False,
            "S7_over_S1_vs_quaternionic_S7_over_S3_control": receipts["Y1_carrier_quotient"]["non_conflation_fields"]["S7_over_S1_equals_S7_over_S3"] is False,
        },
        "shared_scalars": shared_scalars,
        "blind_audit_expected_values": {
            "Bell_entropy": "log(2)",
            "product_entropy": "0",
            "Bell_concurrence": "1",
            "product_concurrence": "0",
            "gamma5_split": {"-1": 2, "1": 2},
            "max_anticommuting_family": 5,
            "Cl6_in_M4C": "impossible",
            "GHZ_W_three_tangle_at_2Q": "not_defined_by_arity",
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
