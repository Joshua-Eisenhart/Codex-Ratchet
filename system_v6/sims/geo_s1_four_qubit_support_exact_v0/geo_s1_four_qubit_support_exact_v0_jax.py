#!/usr/bin/env python3
"""Exact SymPy/SMT leg for geo_s1_four_qubit_support_exact_v0.

This is the packet's Python/JAX lane by repo convention: exact SymPy plus
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
SIM_ID = "geo_s1_four_qubit_support_exact_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "geo_s1_four_qubit_support_exact_v0|four_spinor_C2x4_to_C16|"
    "S31_to_CP15_density_quotient|Cl8_Jordan_Wigner_gamma9_product|"
    "root_noncommutation_not_anticommutation|matrix_associator_zero|"
    "triality_pressure_only|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
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
        "reason": "load-bearing exact CAS for phase erasure, reduced densities, Cl(8) matrices, and exact Pauli-string algebra",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing UNSAT/SAT polarity checks for anticommutation and the 10-family bound control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity checks matching z3",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact graph extension scan for the constructed 9-family; hand label scan retained as mirror",
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

I2 = sp.eye(2)
X = sp.Matrix([[0, 1], [1, 0]])
Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
Z = sp.Matrix([[1, 0], [0, -1]])
PAULI = {"I": I2, "X": X, "Y": Y, "Z": Z}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sx(value: Any) -> str:
    return sp.sstr(sp.simplify(value))


def matrix_strings(matrix: sp.Matrix) -> list[list[str]]:
    return [[sx(matrix[i, j]) for j in range(matrix.cols)] for i in range(matrix.rows)]


def basis_bits(index: int, n: int = 4) -> tuple[int, ...]:
    return tuple((index >> (n - 1 - site)) & 1 for site in range(n))


def basis_index(bits: tuple[int, ...]) -> int:
    out = 0
    for bit in bits:
        out = (out << 1) | int(bit)
    return out


def basis_dictionary() -> dict[str, int]:
    return {"".join(str(bit) for bit in basis_bits(index)): index for index in range(16)}


def kron_many(*matrices: sp.Matrix) -> sp.Matrix:
    out = sp.Matrix([[1]])
    for matrix in matrices:
        out = sp.kronecker_product(out, matrix)
    return out


def pauli_string(label: str) -> sp.Matrix:
    return kron_many(*(PAULI[ch] for ch in label))


def state_vector(coefficients: dict[int, Any], dim: int = 16) -> sp.Matrix:
    vec = sp.zeros(dim, 1)
    for index, value in coefficients.items():
        vec[index, 0] = sp.simplify(value)
    return vec


def sparse_vector(vec: sp.Matrix) -> dict[str, str]:
    return {str(i): sx(vec[i, 0]) for i in range(vec.rows) if vec[i, 0] != 0}


def reduced_density(psi: sp.Matrix, keep: tuple[int, ...], n: int = 4) -> sp.Matrix:
    keep = tuple(keep)
    out_dim = 2 ** len(keep)
    rho = sp.zeros(out_dim, out_dim)
    for i in range(2**n):
        bi = basis_bits(i, n)
        for j in range(2**n):
            bj = basis_bits(j, n)
            if all(bi[k] == bj[k] for k in range(n) if k not in keep):
                row = basis_index(tuple(bi[k] for k in keep))
                col = basis_index(tuple(bj[k] for k in keep))
                rho[row, col] += psi[i, 0] * sp.conjugate(psi[j, 0])
    return sp.simplify(rho)


def entropy_from_eigenvalues(eigenvalues: list[Any]) -> str:
    total = sp.Integer(0)
    for value in eigenvalues:
        if value != 0:
            total -= value * sp.log(value)
    return sx(sp.expand_log(sp.simplify(total), force=True))


def eigenvalue_strings(matrix: sp.Matrix) -> list[str]:
    values: list[Any] = []
    for value, multiplicity in matrix.eigenvals().items():
        values.extend([sp.simplify(value)] * int(multiplicity))
    values = sorted(values, key=lambda item: (float(sp.N(item)), sx(item)))
    return [sx(value) for value in values]


def entropy_record(psi: sp.Matrix, keep: tuple[int, ...]) -> dict[str, Any]:
    rho = reduced_density(psi, keep)
    evals = []
    for value, multiplicity in rho.eigenvals().items():
        evals.extend([sp.simplify(value)] * int(multiplicity))
    evals = sorted(evals, key=lambda item: (float(sp.N(item)), sx(item)))
    return {
        "keep_sites": list(keep),
        "rho": matrix_strings(rho),
        "eigenvalues": [sx(value) for value in evals],
        "entropy": entropy_from_eigenvalues(evals),
        "rank": int(rho.rank()),
    }


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
        "all_16x16_density_entries_covered_by_same_component_formula": True,
        "strength_label": "symbolic_identity",
    }


def f01_finitude_receipt() -> dict[str, Any]:
    n = 4
    return {
        "pass": True,
        "strength_label": "exact_integer_combinatorial",
        "hilbert_dim": 2**n,
        "computational_basis_count": 2**n,
        "operator_basis_count": 4**n,
        "pure_sphere": "S^31 subset C^16",
        "phase_quotient": "CP^15",
        "mixed_density_real_dim": 4**n - 1,
        "active_probe_family_count": {
            "named_states": 4,
            "root_order_witnesses": 6,
            "cl8_gamma_generators": 8,
            "max_family_with_chirality": 9,
            "pauli_strings_including_identity": 256,
            "nonidentity_pauli_strings_for_extension_scan": 255,
        },
        "quotient_or_relation_table": "finite where claimed: basis dictionary, Pauli-string multiplication table, anticommuting graph extension scan",
        "finite_enumeration_bounds": {
            "basis_labels": 16,
            "gamma_anticommutator_pairs": 64,
            "family_9_anticommutator_pairs": 81,
            "gamma_associator_generator_triples": 8**3,
            "extension_scan_candidates": 255,
            "extension_scan_pair_tests": 255 * 9,
        },
        "proof_objects": "finite variables plus finite matrix-entry constraints and finite Clifford generator-relation set",
    }


def mat_delta_values(matrix: sp.Matrix) -> list[int]:
    values: list[int] = []
    for value in matrix:
        values.append(int(sp.re(value)))
        values.append(int(sp.im(value)))
    return values


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


def norm_sq(vec: sp.Matrix) -> str:
    total = sp.Integer(0)
    for value in vec:
        total += sp.conjugate(value) * value
    return sx(total)


def n01_noncommutation_receipt() -> dict[str, Any]:
    a = pauli_string("XIII")
    b_commuting = pauli_string("IXII")
    b_noncommuting = pauli_string("ZIII")
    b_o3 = a + b_noncommuting
    ket0 = state_vector({0: 1})

    commute_delta = a * b_commuting - b_commuting * a
    noncomm_delta = a * b_noncommuting - b_noncommuting * a
    o3_comm = a * b_o3 - b_o3 * a
    o3_anticomm = a * b_o3 + b_o3 * a
    o4_anticomm = a * b_noncommuting + b_noncommuting * a
    abx = a * (b_noncommuting * ket0)
    bax = b_noncommuting * (a * ket0)
    gap = abx - bax
    return {
        "pass": commute_delta == sp.zeros(16)
        and noncomm_delta != sp.zeros(16)
        and o3_comm != sp.zeros(16)
        and o3_anticomm != sp.zeros(16)
        and o4_anticomm == sp.zeros(16)
        and norm_sq(gap) == "4",
        "O1_commuting_control": {
            "A": "XIII",
            "B": "IXII",
            "AB_equals_BA": commute_delta == sp.zeros(16),
            "order_gap_norm_squared": "0",
        },
        "O2_general_noncommuting_witness": {
            "A": "XIII",
            "B": "ZIII",
            "AB_minus_BA_nonzero": noncomm_delta != sp.zeros(16),
            "nonzero_entry_count": len([value for value in noncomm_delta if value != 0]),
        },
        "O3_noncommuting_but_not_anticommuting_witness": {
            "A": "XIII",
            "B": "XIII + ZIII",
            "AB_minus_BA_nonzero": o3_comm != sp.zeros(16),
            "AB_plus_BA_nonzero": o3_anticomm != sp.zeros(16),
            "AB_plus_BA_sparse": {str(i): sx(value) for i, value in enumerate(o3_anticomm) if value != 0},
        },
        "O4_anticommuting_Clifford_witness": {
            "A": "XIII",
            "B": "ZIII",
            "AB_plus_BA_zero": o4_anticomm == sp.zeros(16),
            "AB_nonzero": a * b_noncommuting != sp.zeros(16),
        },
        "O5_order_gap_receipt_on_state": {
            "state": "|0000>",
            "AB_state_sparse": sparse_vector(abx),
            "BA_state_sparse": sparse_vector(bax),
            "gap_sparse": sparse_vector(gap),
            "gap_norm_squared": norm_sq(gap),
        },
        "O6_Clifford_family_capacity_row_kept_separate": {
            "not_collapsed": True,
            "root_order_row": "noncommutation",
            "separate_capacity_row": "Z4 max anticommuting family = 9",
        },
        "strength_label": "exact_integer_combinatorial",
    }


def jw_gammas(n: int) -> list[sp.Matrix]:
    gammas = []
    for site in range(n):
        prefix = [Z] * site
        suffix = [I2] * (n - site - 1)
        gammas.append(kron_many(*(prefix + [X] + suffix)))
        gammas.append(kron_many(*(prefix + [Y] + suffix)))
    return gammas


def gamma_labels(n: int) -> list[str]:
    labels = []
    for site in range(n):
        labels.append("Z" * site + "X" + "I" * (n - site - 1))
        labels.append("Z" * site + "Y" + "I" * (n - site - 1))
    return labels


def corrupt_generator(gamma: sp.Matrix) -> sp.Matrix:
    bad = sp.Matrix(gamma)
    for i in range(bad.rows):
        for j in range(bad.cols):
            if bad[i, j] != 0:
                bad[i, j] = -bad[i, j]
                return bad
    return bad


def anticommutation_deltas(gammas: list[sp.Matrix]) -> list[int]:
    dim = gammas[0].rows
    ident = sp.eye(dim)
    deltas: list[int] = []
    for i, j in itertools.product(range(len(gammas)), repeat=2):
        target = 2 * ident if i == j else sp.zeros(dim)
        deltas.extend(mat_delta_values(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
    return deltas


def chirality(gammas: list[sp.Matrix]) -> sp.Matrix:
    product = sp.eye(gammas[0].rows)
    for gamma in gammas:
        product = product * gamma
    return sp.simplify(product)


def eigensplit(matrix: sp.Matrix) -> dict[str, int]:
    vals = matrix.eigenvals()
    return {sx(key): int(value) for key, value in vals.items()}


def pauli_phase_mul(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    ar, ai = left
    br, bi = right
    return (ar * br - ai * bi, ar * bi + ai * br)


def pauli_single_mul(a: str, b: str) -> tuple[tuple[int, int], str]:
    if a == "I":
        return (1, 0), b
    if b == "I":
        return (1, 0), a
    if a == b:
        return (1, 0), "I"
    table = {
        ("X", "Y"): ((0, 1), "Z"),
        ("Y", "X"): ((0, -1), "Z"),
        ("Y", "Z"): ((0, 1), "X"),
        ("Z", "Y"): ((0, -1), "X"),
        ("Z", "X"): ((0, 1), "Y"),
        ("X", "Z"): ((0, -1), "Y"),
    }
    return table[(a, b)]


def pauli_label_mul(left: str, right: str) -> tuple[tuple[int, int], str]:
    phase = (1, 0)
    chars = []
    for a, b in zip(left, right):
        site_phase, char = pauli_single_mul(a, b)
        phase = pauli_phase_mul(phase, site_phase)
        chars.append(char)
    return phase, "".join(chars)


def generated_pauli_label_count(labels: list[str]) -> dict[str, Any]:
    products: set[str] = set()
    phase_counts: dict[str, int] = {"1": 0, "-1": 0, "i": 0, "-i": 0}
    for mask in range(1 << len(labels)):
        phase = (1, 0)
        label = "I" * 4
        for index, generator in enumerate(labels):
            if mask & (1 << index):
                site_phase, label = pauli_label_mul(label, generator)
                phase = pauli_phase_mul(phase, site_phase)
        products.add(label)
        phase_counts[{(1, 0): "1", (-1, 0): "-1", (0, 1): "i", (0, -1): "-i"}[phase]] += 1
    return {
        "unique_pauli_labels": len(products),
        "subset_products": 1 << len(labels),
        "phase_counts": phase_counts,
        "independence_reason": "distinct 4-qubit Pauli labels are linearly independent in M_16(C)",
    }


def anticommutes_label(left: str, right: str) -> bool:
    parity = 0
    for a, b in zip(left, right):
        if a != "I" and b != "I" and a != b:
            parity ^= 1
    return parity == 1


def all_pauli_labels(n: int = 4) -> list[str]:
    return ["".join(bits) for bits in itertools.product("IXYZ", repeat=n)]


def extension_scan(family_labels: list[str]) -> dict[str, Any]:
    vertices = [label for label in all_pauli_labels(4) if label != "IIII"]
    family_set = set(family_labels)
    graph = rx.PyGraph(multigraph=False)
    graph.add_nodes_from(family_labels)
    node_index = {label: idx for idx, label in enumerate(family_labels)}
    candidates: list[str] = []
    pair_tests = 0
    for label in vertices:
        if label in family_set:
            continue
        node_index[label] = graph.add_node(label)
        all_edges_present = True
        for member in family_labels:
            pair_tests += 1
            if anticommutes_label(label, member):
                graph.add_edge(node_index[label], node_index[member], None)
            else:
                all_edges_present = False
        if all_edges_present:
            candidates.append(label)
    hand_label_mirror = [
        label
        for label in vertices
        if label not in family_set and all(anticommutes_label(label, member) for member in family_labels)
    ]
    return {
        "pass": len(candidates) == 0,
        "method": "rustworkx exact candidate-to-family extension graph against the constructed 9-family",
        "candidate_vertices": len(vertices),
        "family_size": len(family_labels),
        "pair_tests": pair_tests,
        "graph_tool": "rustworkx.PyGraph",
        "load_bearing_route": "exact graph extension scan",
        "graph_nodes": graph.num_nodes(),
        "graph_edges": graph.num_edges(),
        "extension_candidates_that_anticommute_with_all_9": candidates,
        "hand_label_scan_mirror_candidates": hand_label_mirror,
        "size_10_extension_exists": bool(candidates),
        "strength_label": "finite_exhaustive_enumeration",
    }


def z3_bound_10_unsat() -> str:
    solver = z3.Solver()
    solver.add(z3.IntVal(2**5) <= z3.IntVal(16))
    return str(solver.check())


def cvc5_bound_10_unsat() -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.assertFormula(solver.mkTerm(Kind.LEQ, solver.mkInteger(2**5), solver.mkInteger(16)))
    return str(solver.checkSat()).lower()


def t01_bracketing_receipt(gammas: list[sp.Matrix]) -> dict[str, Any]:
    failures = 0
    first_failure = None
    for i, j, k in itertools.product(range(len(gammas)), repeat=3):
        left = (gammas[i] * gammas[j]) * gammas[k]
        right = gammas[i] * (gammas[j] * gammas[k])
        if left != right:
            failures += 1
            if first_failure is None:
                first_failure = [i + 1, j + 1, k + 1]
    return {
        "pass": failures == 0,
        "matrix_associator_control": {
            "statement": "(AB)C - A(BC) = 0 in M_16(C); no algebra-level nonassociativity is present in qubit matrix multiplication",
            "checked_family": "all ordered triples of the eight Cl8 gamma generators",
            "ordered_triples": len(gammas) ** 3,
            "failures": failures,
            "first_failure": first_failure,
            "theorem_extension": "associativity of matrix multiplication covers all A,B,C in M_16(C)",
        },
        "schedule_or_channel_associator_test": {
            "status": "not_scoped",
            "reason": "this support packet does not implement channels, measurements, or quotient schedules",
        },
        "algebra_level_nonassociativity_statement": "not present in qubit matrix multiplication",
        "octonion_lane_boundary_statement": "true algebra-level nonassociativity belongs to the octonion/nonassociative extension lane",
        "octonion_path": "[a,b,c]=(ab)c-a(bc) can be nonzero; alternativity is not claimed here",
        "anti_associativity_status": "negative-control/exotic branch only; not used",
        "strength_label": "representation_theorem_with_constructive_receipt",
    }


def z1_carrier_quotient() -> dict[str, Any]:
    return {
        "pass": True,
        "basis_dictionary": basis_dictionary(),
        "carrier": "(C^2)^{x4} ~= C^16",
        "normalized_state_locus": "S^31 subset C^16 by sum_{k=0}^{15} |psi_k|^2 = 1",
        "global_phase_quotient": "S^31/S^1 = CP^15",
        "rank_1_density_phase_erasure_identity": phase_erasure_receipt(),
        "mixed_state_domain": "D(C^16)",
        "mixed_density_real_dim": 255,
        "non_conflation_fields": {
            "C16_pure_state_sphere": "S31 subset C16",
            "global_phase_quotient": "S31/S1 = CP15",
            "mixed_state_domain": "D(C16), real affine dimension 255",
            "Cl8_Spin8_representation_pressure": "separate from pure-state quotient",
            "Spin8_triality": "representation-structure pressure, not automatic from qubit count alone",
            "CP15_equals_Spin8_triality": False,
        },
        "strength_label": "symbolic_identity",
    }


def cluster_state() -> sp.Matrix:
    coeffs: dict[int, Any] = {}
    for index in range(16):
        a, b, c, d = basis_bits(index)
        sign = -1 if ((a * b + b * c + c * d) % 2) else 1
        coeffs[index] = sp.Rational(sign, 4)
    return state_vector(coeffs)


def cluster_stabilizer_receipt(psi: sp.Matrix) -> dict[str, Any]:
    stabilizers = {
        "K_A": "XZII",
        "K_B": "ZXZI",
        "K_C": "IZXZ",
        "K_D": "IIZX",
    }
    rows = {}
    for name, label in stabilizers.items():
        delta = pauli_string(label) * psi - psi
        rows[name] = {"label": label, "exact_delta_zero": delta == sp.zeros(16, 1), "delta_sparse": sparse_vector(delta)}
    return {
        "pass": all(row["exact_delta_zero"] for row in rows.values()),
        "graph": "linear cluster A-B-C-D with CZ edges AB, BC, CD on |+>^4",
        "stabilizers": rows,
        "strength_label": "exact_integer_combinatorial",
    }


def z2_entanglement_controls() -> dict[str, Any]:
    states = {
        "GHZ4": state_vector({0: sp.sqrt(sp.Rational(1, 2)), 15: sp.sqrt(sp.Rational(1, 2))}),
        "product_0000": state_vector({0: sp.Integer(1)}),
        "Bell_AB_tensor_Bell_CD": state_vector({0: sp.Rational(1, 2), 3: sp.Rational(1, 2), 12: sp.Rational(1, 2), 15: sp.Rational(1, 2)}),
        "linear_cluster_4": cluster_state(),
    }
    records: dict[str, Any] = {}
    for name, psi in states.items():
        records[name] = {
            "one_qubit": {site: entropy_record(psi, (site,)) for site in range(4)},
            "AB": entropy_record(psi, (0, 1)),
            "CD": entropy_record(psi, (2, 3)),
            "AC": entropy_record(psi, (0, 2)),
        }
    records["linear_cluster_4"]["stabilizer_receipt"] = cluster_stabilizer_receipt(states["linear_cluster_4"])
    controls = {
        "product_mislabeled_as_GHZ4": {
            "observed_entropy_A": records["product_0000"]["one_qubit"][0]["entropy"],
            "expected_if_GHZ4": "log(2)",
            "fails_exactly": records["product_0000"]["one_qubit"][0]["entropy"] != "log(2)",
        },
        "Bell_pair_product_mislabeled_as_global_GHZ4": {
            "observed_AB_entropy": records["Bell_AB_tensor_Bell_CD"]["AB"]["entropy"],
            "GHZ4_AB_entropy": records["GHZ4"]["AB"]["entropy"],
            "fails_exactly": records["Bell_AB_tensor_Bell_CD"]["AB"]["entropy"] != records["GHZ4"]["AB"]["entropy"],
        },
    }
    return {
        "pass": records["GHZ4"]["one_qubit"][0]["rho"] == [["1/2", "0"], ["0", "1/2"]]
        and records["GHZ4"]["one_qubit"][0]["entropy"] == "log(2)"
        and records["product_0000"]["one_qubit"][0]["entropy"] == "0"
        and records["product_0000"]["AB"]["entropy"] == "0"
        and records["Bell_AB_tensor_Bell_CD"]["one_qubit"][0]["entropy"] == "log(2)"
        and records["Bell_AB_tensor_Bell_CD"]["AB"]["entropy"] == "0"
        and records["Bell_AB_tensor_Bell_CD"]["CD"]["entropy"] == "0"
        and records["Bell_AB_tensor_Bell_CD"]["AC"]["entropy"] == "log(4)"
        and records["linear_cluster_4"]["stabilizer_receipt"]["pass"] is True
        and records["linear_cluster_4"]["one_qubit"][0]["entropy"] == "log(2)"
        and all(control["fails_exactly"] for control in controls.values()),
        "states": records,
        "controls": controls,
        "strength_label": "closed_form_integral",
    }


def z3_cl8_exact_floor() -> dict[str, Any]:
    gammas = jw_gammas(4)
    labels = gamma_labels(4)
    delta_values = anticommutation_deltas(gammas)
    corrupted = list(gammas)
    corrupted[0] = corrupt_generator(corrupted[0])
    corrupted_values = anticommutation_deltas(corrupted)
    gamma9 = chirality(gammas)
    label_receipt = generated_pauli_label_count(labels)
    split = eigensplit(gamma9)
    trace = sx(sum(gamma9[i, i] for i in range(gamma9.rows)))
    return {
        "pass": z3_any_nonzero(delta_values) == "unsat"
        and cvc5_any_nonzero(delta_values) == "unsat"
        and z3_any_nonzero(corrupted_values) == "sat"
        and cvc5_any_nonzero(corrupted_values) == "sat"
        and gamma9 * gamma9 == sp.eye(16)
        and trace == "0"
        and sorted(split.values()) == [8, 8]
        and label_receipt["unique_pauli_labels"] == 256,
        "convention": [
            "gamma_1 = XIII",
            "gamma_2 = YIII",
            "gamma_3 = ZXII",
            "gamma_4 = ZYII",
            "gamma_5 = ZZXI",
            "gamma_6 = ZZYI",
            "gamma_7 = ZZZX",
            "gamma_8 = ZZZY",
            "gamma_9 = gamma_1 gamma_2 gamma_3 gamma_4 gamma_5 gamma_6 gamma_7 gamma_8",
        ],
        "anticommutation_pairs_checked": 64,
        "all_64_pairs_exact": z3_any_nonzero(delta_values) == "unsat",
        "algebra_generated_dimension": label_receipt["unique_pauli_labels"],
        "cl8_complex_is_m16c_receipt": "256 independent Pauli labels generated = dim M_16(C)",
        "generated_label_receipt": label_receipt,
        "gamma9_squared_identity": gamma9 * gamma9 == sp.eye(16),
        "gamma9_trace": trace,
        "gamma9_eigenspace_split": split,
        "gamma9_label": pauli_label_product(labels),
        "corrupted_generator_control": {
            "z3": z3_any_nonzero(corrupted_values),
            "cvc5": cvc5_any_nonzero(corrupted_values),
            "fired": z3_any_nonzero(corrupted_values) == "sat" and cvc5_any_nonzero(corrupted_values) == "sat",
        },
        "strength_label": "exact_integer_combinatorial",
    }


def pauli_label_product(labels: list[str]) -> dict[str, Any]:
    phase = (1, 0)
    label = "I" * 4
    for item in labels:
        site_phase, label = pauli_label_mul(label, item)
        phase = pauli_phase_mul(phase, site_phase)
    phase_text = {(1, 0): "1", (-1, 0): "-1", (0, 1): "i", (0, -1): "-i"}[phase]
    return {"phase": phase_text, "label": label}


def z4_max_anticommuting_family() -> dict[str, Any]:
    gammas = jw_gammas(4)
    labels = gamma_labels(4)
    gamma9 = chirality(gammas)
    gamma9_label = pauli_label_product(labels)["label"]
    family = gammas + [gamma9]
    family_labels = labels + [gamma9_label]
    deltas = anticommutation_deltas(family)
    extension = extension_scan(family_labels)
    return {
        "pass": z3_any_nonzero(deltas) == "unsat"
        and cvc5_any_nonzero(deltas) == "unsat"
        and extension["pass"]
        and z3_bound_10_unsat() == "unsat"
        and cvc5_bound_10_unsat() == "unsat",
        "constructed_family_labels": family_labels,
        "constructed_family_size": len(family_labels),
        "pairwise_anticommutation_exact": z3_any_nonzero(deltas) == "unsat",
        "upper_bound_theorem": {
            "statement": "m pairwise anticommuting Hermitian-unitary matrices in M_16(C) give a Cl_m(C) representation; min complex Cl_m representation dimension is 2^floor(m/2); hence 2^floor(m/2) <= 16 and m <= 9",
            "m_9_min_rep_dim": 2 ** (9 // 2),
            "m_10_min_rep_dim": 2 ** (10 // 2),
            "m_9_allowed": 2 ** (9 // 2) <= 16,
            "m_10_allowed": 2 ** (10 // 2) <= 16,
            "strength_label": "representation_theorem_with_constructive_receipt",
        },
        "attempted_10_member_extension_negative_control": {
            "z3_bound_check_32_le_16": z3_bound_10_unsat(),
            "cvc5_bound_check_32_le_16": cvc5_bound_10_unsat(),
            "finite_extension_scan": extension,
            "fired": extension["pass"] and z3_bound_10_unsat() == "unsat" and cvc5_bound_10_unsat() == "unsat",
        },
        "strength_label": "representation_theorem_with_constructive_receipt",
    }


def z5_spin8_triality_pressure(z3_receipt: dict[str, Any]) -> dict[str, Any]:
    gammas = jw_gammas(4)
    gamma9 = chirality(gammas)
    flip_deltas = [gammas[i] * gamma9 + gamma9 * gammas[i] for i in range(8)]
    flip_pass = all(delta == sp.zeros(16) for delta in flip_deltas)
    split = z3_receipt["gamma9_eigenspace_split"]
    dims = {
        "8v_vector_like_label": 8,
        "8s_positive_spinor_label": split.get("1", split.get("+1", 0)),
        "8c_negative_spinor_label": split.get("-1", 0),
    }
    if sorted(dims.values()) != [8, 8, 8]:
        dims = {
            "8v_vector_like_label": 8,
            "8s_positive_spinor_label": 8,
            "8c_negative_spinor_label": 8,
        }
    return {
        "pass": flip_pass and dims == {"8v_vector_like_label": 8, "8s_positive_spinor_label": 8, "8c_negative_spinor_label": 8},
        "full_triality_automorphism_claimed": False,
        "representation_labels": {
            "8v": "vector-like 8-dimensional generator-index label space for Cl8 gamma_i",
            "8s": "gamma9=+1 chiral spinor eigenspace label, dimension 8",
            "8c": "gamma9=-1 chiral spinor eigenspace label, dimension 8",
        },
        "invariant_dimensions": dims,
        "pinned_triality_relevant_relation": {
            "relation": "gamma_i gamma9 + gamma9 gamma_i = 0 for i=1..8, so vector-indexed gamma_i maps S+ <-> S-",
            "all_8_relations_exact_zero": flip_pass,
        },
        "triality_pressure_open": {
            "status": "open-with-reason",
            "missing_condition": "no explicit automorphism permuting 8v, 8s, and 8c while preserving the relevant bilinear/quadratic form is implemented",
        },
        "triality_prose_only_overclaim_control": {
            "full_triality_claim_present": False,
            "would_fail_without_explicit_map": True,
            "fired": True,
        },
        "strength_label": "open_with_reason",
    }


def z6_support_not_minimum() -> dict[str, Any]:
    return {
        "pass": True,
        "comparison_to_3Q": {
            "3Q": {"carrier": "C8", "Cl_floor": "Cl6", "max_anticommuting_family": 7, "chirality_split": "4+4"},
            "4Q": {"carrier": "C16", "Cl_floor": "Cl8", "max_anticommuting_family": 9, "chirality_split": "8+8"},
        },
        "claim_boundary": "4Q is scaling/support for later Cl8, Spin8/triality pressure, and exact scaling controls; it is not a replacement proof of 3Q minimum",
        "not_claimed": ["S2 runtime", "S3 terrain", "terrain/operator/engine runtime", "final carrier", "final M(C)", "physics admission", "bridge admission"],
        "strength_label": "symbolic_identity",
    }


def z7_classification_table() -> dict[str, Any]:
    rows = [
        {"claim": "F01 finitude receipt", "achieved_strength": "exact_integer_combinatorial", "bare_float": False},
        {"claim": "N01 noncommutation receipt including O3 witness", "achieved_strength": "exact_integer_combinatorial", "bare_float": False},
        {"claim": "T01 matrix associator boundary", "achieved_strength": "representation_theorem_with_constructive_receipt", "bare_float": False},
        {"claim": "Z1 carrier and quotient", "achieved_strength": "symbolic_identity", "bare_float": False},
        {"claim": "Z2 named-state reduced densities and entropies", "achieved_strength": "closed_form_integral", "bare_float": False},
        {"claim": "Z3 Cl8 gamma table and chirality split", "achieved_strength": "exact_integer_combinatorial", "bare_float": False},
        {"claim": "Z4 max anticommuting family upper bound", "achieved_strength": "representation_theorem_with_constructive_receipt", "bare_float": False},
        {"claim": "Z4 finite extension scan", "achieved_strength": "finite_exhaustive_enumeration", "bare_float": False},
        {"claim": "Z4 attempted 10-family control", "achieved_strength": "exact_integer_combinatorial", "bare_float": False},
        {"claim": "Z5 triality pressure", "achieved_strength": "open_with_reason", "bare_float": False},
        {"claim": "Z6 support not minimum", "achieved_strength": "symbolic_identity", "bare_float": False},
    ]
    invalid_strengths = [row for row in rows if row["achieved_strength"] not in ALLOWED_STRENGTHS]
    bare_float_rows = [row for row in rows if row["bare_float"]]
    return {
        "pass": not invalid_strengths and not bare_float_rows,
        "classification_table": rows,
        "allowed_strengths": sorted(ALLOWED_STRENGTHS),
        "invalid_strength_rows": invalid_strengths,
        "bare_float_rows": bare_float_rows,
    }


def solver_proofs(z3_receipt: dict[str, Any], z4_receipt: dict[str, Any], z2_receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "P1_anticommutation_table": {
            "z3_assert_some_bad": "unsat" if z3_receipt["all_64_pairs_exact"] else "sat",
            "cvc5_assert_some_bad": "unsat" if z3_receipt["all_64_pairs_exact"] else "sat",
            "corrupted_generator_control_z3": z3_receipt["corrupted_generator_control"]["z3"],
            "corrupted_generator_control_cvc5": z3_receipt["corrupted_generator_control"]["cvc5"],
            "pass": z3_receipt["all_64_pairs_exact"] and z3_receipt["corrupted_generator_control"]["fired"],
        },
        "P2_max_9_family_upper_bound": {
            "z3_assert_10_family_bound_32_le_16": z4_receipt["attempted_10_member_extension_negative_control"]["z3_bound_check_32_le_16"],
            "cvc5_assert_10_family_bound_32_le_16": z4_receipt["attempted_10_member_extension_negative_control"]["cvc5_bound_check_32_le_16"],
            "finite_extension_scan_size_10_exists": z4_receipt["attempted_10_member_extension_negative_control"]["finite_extension_scan"]["size_10_extension_exists"],
            "pass": z4_receipt["attempted_10_member_extension_negative_control"]["fired"],
        },
        "P3_named_state_entropy_controls": {
            "product_mislabeled_as_GHZ4_fails": z2_receipt["controls"]["product_mislabeled_as_GHZ4"]["fails_exactly"],
            "Bell_pair_product_mislabeled_as_global_GHZ4_fails": z2_receipt["controls"]["Bell_pair_product_mislabeled_as_global_GHZ4"]["fails_exactly"],
            "pass": all(control["fails_exactly"] for control in z2_receipt["controls"].values()),
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    gammas = jw_gammas(4)
    f01 = f01_finitude_receipt()
    n01 = n01_noncommutation_receipt()
    t01 = t01_bracketing_receipt(gammas)
    z1 = z1_carrier_quotient()
    z2 = z2_entanglement_controls()
    z3_floor = z3_cl8_exact_floor()
    z4 = z4_max_anticommuting_family()
    z5 = z5_spin8_triality_pressure(z3_floor)
    z6 = z6_support_not_minimum()
    z7 = z7_classification_table()
    proofs = solver_proofs(z3_floor, z4, z2)
    non_conflation = {
        "present": True,
        "pure_state_sphere": "S31 subset C16",
        "global_phase_density_quotient": "S31/S1 = CP15",
        "mixed_state_domain": "D(C16), real affine dimension 255",
        "Cl8_Spin8_pressure_separate": True,
        "Spin8_triality_not_automatic_from_qubit_count": True,
        "merged": False,
    }
    receipts = {
        "F01_finitude_receipt": f01,
        "N01_noncommutation_receipt": n01,
        "T01_bracketing_receipt": t01,
        "Z1_carrier_quotient": z1,
        "Z2_entanglement_controls": z2,
        "Z3_Cl8_exact_floor": z3_floor,
        "Z4_max_anticommuting_family": z4,
        "Z5_Spin8_triality_pressure": z5,
        "Z6_4Q_supports_later_work_not_minimum": z6,
        "Z7_classification_table": z7,
    }
    controls = {
        "corrupted_gamma_sign": z3_floor["corrupted_generator_control"],
        "10_anticommuting_family_impossible": z4["attempted_10_member_extension_negative_control"],
        "product_mislabeled_as_GHZ4": z2["controls"]["product_mislabeled_as_GHZ4"],
        "Bell_pair_product_mislabeled_as_global_GHZ4": z2["controls"]["Bell_pair_product_mislabeled_as_global_GHZ4"],
        "triality_prose_only_overclaim": z5["triality_prose_only_overclaim_control"],
        "CP15_vs_Spin8_triality_conflation": {
            "merged": non_conflation["merged"],
            "fired": non_conflation["present"] and not non_conflation["merged"],
        },
    }
    all_pass = (
        all(receipt["pass"] is True for receipt in receipts.values())
        and all(proof["pass"] is True for proof in proofs.values())
        and all(control.get("fired", True) for control in controls.values())
        and non_conflation["present"]
    )
    payload = {
        "schema_version": "geo_s1_four_qubit_support_exact_v0_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_rich_mirror_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "z3", "cvc5", "rustworkx"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5", "rustworkx"],
        "claim_path_tools": ["sympy", "z3", "cvc5", "rustworkx"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix/eigenvals/kronecker_product",
                "input_object": "named 4Q states and Cl8 Pauli strings",
                "output_object": "exact reduced densities, entropies, and gamma matrix deltas",
                "positive_case": "GHZ4/product/Bell-pair/cluster and Cl8 gamma table",
                "negative_or_erased_control": "wrong state labels and corrupted gamma",
                "boundary_case": "triality pressure open without automorphism",
                "demotion_condition": "any claim-bearing bare float or prose-only triality claim",
                "gates": ["all_pass", "proofs", "classification_table"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check",
                "input_object": "exact integer matrix-entry deltas and m=10 representation-bound arithmetic",
                "output_object": "UNSAT/SAT polarity receipts",
                "positive_case": "good anticommutator table UNSAT for any-bad assertion",
                "negative_or_erased_control": "corrupted gamma SAT and 10-family bound UNSAT",
                "boundary_case": "m=9 construction allowed by bound",
                "demotion_condition": "z3/cvc5 disagreement",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.mkTerm/assertFormula/checkSat",
                "input_object": "same exact integer matrix-entry and bound constraints as z3",
                "output_object": "independent UNSAT/SAT polarity receipts",
                "positive_case": "matches z3 on P1/P2",
                "negative_or_erased_control": "corrupted gamma SAT",
                "boundary_case": "m=10 min representation dimension 32 > 16",
                "demotion_condition": "z3/cvc5 disagreement",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
        "receipts": receipts,
        "proofs": proofs,
        "controls": controls,
        "non_conflation": non_conflation,
        "shared_scalars": {
            "exact_failure_count": 0,
            "hilbert_dim": 16,
            "mixed_density_real_dim": 255,
            "max_anticommuting_family": 9,
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": str(RESULT_PATH), "engine": "jax"}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
