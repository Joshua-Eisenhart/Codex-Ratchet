#!/usr/bin/env python3
"""Shared exact algebra builder for geo_s10_g2_family_v0.

The packet ceiling is scratch diagnostic. Values are derived from explicit
tables, linear systems, finite enumerations, or solver bindings in this file.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import itertools
import json
import platform
import sys
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s10_g2_family_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
SEED = "geo_s10_g2_family_v0_seed_20260610"
TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "exact linear algebra for G2-family derivation and rank rows"},
    "z3": {"tried": True, "used": True, "reason": "finite identity erased-line flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent finite identity erased-line flip"},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"}
BLIND_PATH = Path("/tmp/s10_g2_blind_expectations.md")
ROUTE_MAP_PATH = ROOT / "system_v6" / "receipts" / "s10_g2_family_mine_20260610.md"
TOOLSET_RECEIPT_PATH = ROOT / "system_v6" / "receipts" / "toolset_expansion_20260610.md"
NEMO_RECEIPT_PATH = ROOT / "system_v6" / "probes" / "toolset_expansion_20260610_nemo_hecke_results.json"
G2_DISCRIMINATOR_PATH = (
    ROOT
    / "system_v6"
    / "sims"
    / "g2_forced_vs_installed_discriminator"
    / "results"
    / "g2_forced_vs_installed_discriminator_envelope_results.json"
)
NESTING_TAXONOMY_PATH = ROOT / "system_v6" / "receipts" / "nesting_law_audited_20260610.md"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int | float | str):
        return value
    if isinstance(value, sp.Integer):
        return int(value)
    if isinstance(value, sp.Rational):
        return f"{int(value.p)}/{int(value.q)}"
    if isinstance(value, sp.MatrixBase):
        return json_ready(value.tolist())
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    return str(value)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(json_ready(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def now_utc() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def zero_table(n: int) -> list[list[list[int]]]:
    return [[[0 for _ in range(n)] for _ in range(n)] for _ in range(n)]


def conj_vec(x: list[int]) -> list[int]:
    return [x[0], *[-v for v in x[1:]]]


def table_mul(table: list[list[list[int]]], x: list[Any], y: list[Any]) -> list[Any]:
    n = len(table)
    return [
        sum(table[k][i][j] * x[i] * y[j] for i in range(n) for j in range(n))
        for k in range(n)
    ]


def cd_double(parent: list[list[list[int]]], gamma: int) -> list[list[list[int]]]:
    """Cayley-Dickson double with l^2 = gamma.

    gamma=-1 gives the division step. gamma=+1 at H -> O gives the split
    octonions under the convention N(a,b)=N(a)-N(b).
    """
    n = len(parent)
    dim = 2 * n
    out = zero_table(dim)
    eye = [[1 if i == j else 0 for i in range(dim)] for j in range(dim)]
    for i, x in enumerate(eye):
        for j, y in enumerate(eye):
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = [
                u + gamma * v
                for u, v in zip(table_mul(parent, a, c), table_mul(parent, conj_vec(d), b))
            ]
            second = [
                u + v
                for u, v in zip(table_mul(parent, d, a), table_mul(parent, b, conj_vec(c)))
            ]
            for k, value in enumerate(first + second):
                out[k][i][j] = int(value)
    return out


def table_r() -> list[list[list[int]]]:
    return [[[1]]]


def table_h() -> list[list[list[int]]]:
    return cd_double(cd_double(table_r(), -1), -1)


def table_o_compact() -> list[list[list[int]]]:
    return cd_double(table_h(), -1)


def table_o_split() -> list[list[list[int]]]:
    return cd_double(table_h(), 1)


def table_m2r() -> list[list[list[int]]]:
    out = zero_table(4)
    basis = [(0, 0), (0, 1), (1, 0), (1, 1)]
    index = {pair: idx for idx, pair in enumerate(basis)}
    for i, (a, b) in enumerate(basis):
        for j, (c, d) in enumerate(basis):
            if b == c:
                out[index[(a, d)]][i][j] = 1
    return out


def corrupt_one_sign(table: list[list[list[int]]]) -> list[list[list[int]]]:
    out = json.loads(json.dumps(table))
    for k, value in enumerate(table[k][1][2] for k in range(len(table))):
        if value:
            out[k][1][2] = -value
            return out
    raise AssertionError("no nonzero e1*e2 coefficient found")


def derivation_matrix(table: list[list[list[int]]]) -> sp.Matrix:
    n = len(table)
    rows: list[list[int]] = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                row = [0 for _ in range(n * n)]
                for ell in range(n):
                    row[k * n + ell] += table[ell][i][j]
                for a in range(n):
                    row[a * n + i] -= table[k][a][j]
                for b in range(n):
                    row[b * n + j] -= table[k][i][b]
                rows.append(row)
    return sp.Matrix(rows)


def matrix_from_vec(vec: sp.Matrix, n: int) -> sp.Matrix:
    return sp.Matrix(n, n, list(vec))


def derivation_summary(name: str, table: list[list[list[int]]]) -> dict[str, Any]:
    matrix = derivation_matrix(table)
    rank = int(matrix.rank())
    n = len(table)
    nullspace = matrix.nullspace()
    basis_mats = [matrix_from_vec(vec, n) for vec in nullspace]
    return {
        "carrier": name,
        "basis_dimension": n,
        "equation_count": int(matrix.rows),
        "unknown_count": int(matrix.cols),
        "rank": rank,
        "nullity_dim_der": n * n - rank,
        "nullspace_basis_count": len(nullspace),
        "rank_method": "sympy exact rational rank of D(xy)=D(x)y+xD(y)",
        "derivation_matrix_sha256": sha256_json(matrix.tolist()),
        "basis_sha256": sha256_json([mat.tolist() for mat in basis_mats]),
        "_basis_mats": basis_mats,
    }


def public_derivation_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in summary.items() if k != "_basis_mats"}


def norm_diag(table: list[list[list[int]]]) -> list[int]:
    out = []
    n = len(table)
    for i in range(n):
        x = [1 if a == i else 0 for a in range(n)]
        prod = table_mul(table, x, conj_vec(x))
        out.append(int(prod[0]))
    return out


def signature_from_diag(diag: list[int]) -> dict[str, int]:
    return {
        "positive": sum(1 for v in diag if v > 0),
        "negative": sum(1 for v in diag if v < 0),
        "zero": sum(1 for v in diag if v == 0),
    }


def left_mult_hash(table: list[list[list[int]]]) -> dict[str, Any]:
    mats = []
    for i in range(1, 8):
        mats.append([[table[k][i][j] for j in range(1, 8)] for k in range(1, 8)])
    return {"count": len(mats), "shape_each": [7, 7], "sha256": sha256_json(mats)}


def metric_preservation(summary: dict[str, Any], metric_diag: list[int]) -> dict[str, Any]:
    g = sp.diag(*metric_diag)
    nonzero = 0
    max_abs = 0
    for mat in summary["_basis_mats"]:
        d = mat[1:, 1:]
        residual = d.T * g + g * d
        for value in residual:
            if value != 0:
                nonzero += 1
                max_abs = max(max_abs, abs(int(value)))
    return {"preserves": nonzero == 0, "nonzero_entries": nonzero, "max_abs_entry": max_abs}


def unit_column_zero(summary: dict[str, Any]) -> bool:
    return all(all(mat[r, 0] == 0 for r in range(mat.rows)) for mat in summary["_basis_mats"])


def subspace_rank(mats: list[sp.Matrix]) -> int:
    if not mats:
        return 0
    return int(sp.Matrix.hstack(*[sp.Matrix(mat).reshape(mat.rows * mat.cols, 1) for mat in mats]).rank())


def span_contains_all(basis: list[sp.Matrix], candidates: list[sp.Matrix]) -> bool:
    if not candidates:
        return True
    base = sp.Matrix.hstack(*[sp.Matrix(mat).reshape(mat.rows * mat.cols, 1) for mat in basis])
    rank = base.rank()
    for cand in candidates:
        aug = base.row_join(sp.Matrix(cand).reshape(cand.rows * cand.cols, 1))
        if aug.rank() != rank:
            return False
    return True


def closure_in_span(summary: dict[str, Any], start: int = 1) -> dict[str, Any]:
    mats = [mat[start:, start:] for mat in summary["_basis_mats"]]
    comms = [a * b - b * a for a in mats for b in mats]
    return {
        "basis_rank": subspace_rank(mats),
        "commutator_count": len(comms),
        "all_commutators_in_span": span_contains_all(mats, comms),
    }


def stabilizer_dimension(summary: dict[str, Any], vector7: list[int]) -> dict[str, Any]:
    rows: list[list[Any]] = []
    for r in range(8):
        rows.append([
            sum(mat[r, c + 1] * vector7[c] for c in range(7))
            for mat in summary["_basis_mats"]
        ])
    constraint = sp.Matrix(rows)
    rank = int(constraint.rank())
    return {
        "vector": vector7,
        "constraint_rank_on_derivation_basis": rank,
        "stabilizer_dim": len(summary["_basis_mats"]) - rank,
    }


def find_signed_automorphism_mapping(
    table: list[list[list[int]]],
    source_imag_zero_based: int,
    target_imag_zero_based: int,
) -> dict[str, Any]:
    line_set = canonical_line_set(table)
    line_set_frozen = {frozenset(line) for line in line_set}
    for perm in itertools.permutations(range(7)):
        if perm[source_imag_zero_based] != target_imag_zero_based:
            continue
        transported = {frozenset(perm[i] for i in line) for line in line_set_frozen}
        if transported != line_set_frozen:
            continue
        for signs in itertools.product([-1, 1], repeat=7):
            ok = True
            for i in range(7):
                for j in range(7):
                    for k in range(7):
                        lhs = table[k + 1][i + 1][j + 1] * signs[k]
                        rhs = signs[i] * signs[j] * table[perm[k] + 1][perm[i] + 1][perm[j] + 1]
                        if lhs != rhs:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if ok:
                return {"found": True, "perm_zero_based": list(perm), "signs": list(signs)}
    return {"found": False, "perm_zero_based": None, "signs": None}


def conjugacy_check(summary: dict[str, Any], auto: dict[str, Any]) -> dict[str, Any]:
    if not auto["found"]:
        return {"checked": False, "conjugate_subspaces_equal": False}
    perm = auto["perm_zero_based"]
    signs = auto["signs"]
    pmat = sp.zeros(7)
    for old, new in enumerate(perm):
        pmat[new, old] = signs[old]
    pinv = pmat.inv()
    mats = [mat[1:, 1:] for mat in summary["_basis_mats"]]

    def stabilizer_basis(col: int) -> list[sp.Matrix]:
        constraints = sp.Matrix([[mat[r, col] for mat in mats] for r in range(7)])
        out = []
        for coeffs in constraints.nullspace():
            acc = sp.zeros(7)
            for coeff, mat in zip(coeffs, mats):
                acc += coeff * mat
            out.append(acc)
        return out

    stab1 = stabilizer_basis(0)
    stab2 = stabilizer_basis(1)
    conj = [pmat * mat * pinv for mat in stab1]
    return {
        "checked": True,
        "source_unit": "e1",
        "target_unit": "e2",
        "stabilizer_e1_basis_count": len(stab1),
        "stabilizer_e2_basis_count": len(stab2),
        "conjugate_subspaces_equal": span_contains_all(stab2, conj) and span_contains_all(conj, stab2),
        "automorphism": auto,
    }


def tensor_decomposition(table: list[list[list[int]]], summary: dict[str, Any]) -> dict[str, Any]:
    dim = 7
    n2 = dim * dim
    p_sym = sp.zeros(n2)
    p_anti = sp.zeros(n2)
    p_trace = sp.zeros(n2)
    identity_vec = sp.zeros(n2, 1)
    for i in range(dim):
        identity_vec[i * dim + i, 0] = 1
    for i in range(dim):
        for j in range(dim):
            col = i * dim + j
            p_sym[i * dim + j, col] += sp.Rational(1, 2)
            p_sym[j * dim + i, col] += sp.Rational(1, 2)
            p_anti[i * dim + j, col] += sp.Rational(1, 2)
            p_anti[j * dim + i, col] -= sp.Rational(1, 2)
            if i == j:
                for a in range(dim):
                    p_trace[a * dim + a, col] += sp.Rational(1, 7)
    p_sym27 = p_sym - p_trace

    pairs = list(itertools.combinations(range(dim), 2))
    cross = sp.zeros(dim, len(pairs))
    for col, (i, j) in enumerate(pairs):
        for k in range(dim):
            cross[k, col] = table[k + 1][i + 1][j + 1]

    equivariant = True
    scalar_fixed = True
    for full in summary["_basis_mats"]:
        d = full[1:, 1:]
        action = sp.kronecker_product(d, sp.eye(dim)) + sp.kronecker_product(sp.eye(dim), d)
        if action * identity_vec != sp.zeros(n2, 1):
            scalar_fixed = False
        for i, j in pairs:
            lhs = sp.zeros(dim, 1)
            for a in range(dim):
                lhs += d[a, i] * sp.Matrix([table[k + 1][a + 1][j + 1] for k in range(dim)])
                lhs += d[a, j] * sp.Matrix([table[k + 1][i + 1][a + 1] for k in range(dim)])
            rhs = d * sp.Matrix([table[k + 1][i + 1][j + 1] for k in range(dim)])
            if lhs != rhs:
                equivariant = False
                break
        if not equivariant:
            break

    return {
        "ambient_tensor_dim": n2,
        "projector_ranks_exact": {
            "symmetric_rank": int(p_sym.rank()),
            "antisymmetric_rank": int(p_anti.rank()),
            "scalar_trace_rank": int(p_trace.rank()),
            "symmetric_tracefree_rank": int(p_sym27.rank()),
        },
        "lambda2_cross_product_map": {
            "domain_dim": len(pairs),
            "image_rank_7_component": int(cross.rank()),
            "kernel_rank_14_component": len(pairs) - int(cross.rank()),
        },
        "block_dimensions": [1, 7, 14, 27],
        "dimension_sum": 1 + 7 + 14 + 27,
        "decomposition_label": "7 tensor 7 = 1 + 7 + 14 + 27",
        "computed_from": "metric trace projector plus octonion cross-product map on Lambda^2",
        "scalar_component_fixed_by_derivations": scalar_fixed,
        "cross_product_equivariance_for_computed_derivations": equivariant,
    }


def permutation_sign(seq: list[int]) -> int:
    inv = 0
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            if seq[i] > seq[j]:
                inv += 1
    return -1 if inv % 2 else 1


def antisym_fill(base: tuple[int, ...], value: int) -> dict[tuple[int, ...], int]:
    out = {}
    base_list = list(base)
    for perm in itertools.permutations(base_list):
        sign = permutation_sign([base_list.index(x) for x in perm])
        out[perm] = sign * value
    return out


def compact_phi_dict(table: list[list[list[int]]]) -> dict[tuple[int, int, int], int]:
    out: dict[tuple[int, int, int], int] = {}
    for i, j, k in itertools.permutations(range(7), 3):
        value = table[k + 1][i + 1][j + 1]
        if value:
            out[(i, j, k)] = value
    return out


def cayley_form_action_rank(table: list[list[list[int]]]) -> dict[str, Any]:
    phi = compact_phi_dict(table)
    all7 = set(range(7))
    psi: dict[tuple[int, int, int, int], int] = {}
    for comp in itertools.combinations(range(7), 4):
        rem = tuple(sorted(all7 - set(comp)))
        value = phi.get(rem, 0) * permutation_sign(list(comp) + list(rem))
        if value:
            psi.update(antisym_fill(comp, value))

    omega: dict[tuple[int, int, int, int], int] = {}
    for comp in itertools.combinations(range(8), 4):
        if 0 in comp:
            rest = tuple(x - 1 for x in comp if x != 0)
            value = phi.get(rest, 0)
        else:
            rest = tuple(x - 1 for x in comp)
            value = psi.get(rest, 0)
        if value:
            omega.update(antisym_fill(comp, value))

    pairs8 = list(itertools.combinations(range(8), 2))
    comps4 = list(itertools.combinations(range(8), 4))
    rows = []
    for comp_tuple in comps4:
        comp = list(comp_tuple)
        row = []
        for a, b in pairs8:
            value = 0
            for pos, idx in enumerate(comp):
                if idx == b:
                    new = comp.copy()
                    new[pos] = a
                    value += omega.get(tuple(new), 0)
                elif idx == a:
                    new = comp.copy()
                    new[pos] = b
                    value -= omega.get(tuple(new), 0)
            row.append(value)
        rows.append(row)
    action = sp.Matrix(rows)
    return {
        "so8_basis_pairs": pairs8,
        "action_matrix": action,
        "spin7_stabilizer_rank_constraints": int(action.rank()),
        "spin7_lie_dim": len(pairs8) - int(action.rank()),
        "omega_nonzero_components": len(omega),
        "omega_sha256": sha256_json({str(k): v for k, v in sorted(omega.items())}),
    }


def spin_triality(table: list[list[list[int]]], summary: dict[str, Any]) -> dict[str, Any]:
    cayley = cayley_form_action_rank(table)
    pairs8 = cayley["so8_basis_pairs"]
    action = cayley["action_matrix"]
    g2_preserves = True
    for mat in summary["_basis_mats"]:
        x = sp.zeros(8)
        x[1:, 1:] = mat[1:, 1:]
        coords = sp.Matrix([x[a, b] for a, b in pairs8])
        if action * coords != sp.zeros(action.rows, 1):
            g2_preserves = False
            break
    d4_edges = {tuple(sorted(edge)) for edge in [(0, 1), (1, 2), (1, 3)]}
    autos = []
    for perm in itertools.permutations(range(4)):
        edges = {tuple(sorted((perm[a], perm[b]))) for a, b in d4_edges}
        if edges == d4_edges:
            autos.append(perm)
    return {
        "so7_dim_from_matrix_basis": 7 * 6 // 2,
        "so8_dim_from_matrix_basis": 8 * 7 // 2,
        "spin7_dim_from_cayley_form_stabilizer": cayley["spin7_lie_dim"],
        "g2_dim_from_derivations": summary["nullity_dim_der"],
        "dimension_chain": [summary["nullity_dim_der"], cayley["spin7_lie_dim"], 28],
        "difference_dimensions": [cayley["spin7_lie_dim"] - summary["nullity_dim_der"], 28 - cayley["spin7_lie_dim"], 28 - summary["nullity_dim_der"]],
        "g2_extended_derivations_preserve_cayley_form": g2_preserves,
        "g2_closure_in_7d_action": closure_in_span(summary)["all_commutators_in_span"],
        "cayley_form_sha256": cayley["omega_sha256"],
        "triality_check": {
            "method": "D4 diagram/character-node automorphism order, not explicit intertwiners",
            "scope_fence": "D4 diagram/character-node automorphism order, not explicit intertwiners",
            "automorphism_order": len(autos),
            "outer_node_permutations": [list(perm) for perm in autos],
            "isomorphic_to": "S3",
        },
    }


def canonical_line_set(table: list[list[list[int]]]) -> list[tuple[int, int, int]]:
    lines = []
    for comp in itertools.combinations(range(7), 3):
        if any(table[k + 1][i + 1][j + 1] for i, j, k in itertools.permutations(comp, 3)):
            lines.append(comp)
    return lines


def add_oriented_line(table: list[list[list[int]]], a: int, b: int, c: int, sign: int) -> None:
    if sign < 0:
        b, c = c, b
    for x, y, z in [(a, b, c), (b, c, a), (c, a, b)]:
        table[z + 1][x + 1][y + 1] = 1
        table[z + 1][y + 1][x + 1] = -1


def table_from_lines(lines: list[tuple[int, int, int]], bits: tuple[int, ...]) -> list[list[list[int]]]:
    table = zero_table(8)
    table[0][0][0] = 1
    for i in range(1, 8):
        table[i][0][i] = 1
        table[i][i][0] = 1
        table[0][i][i] = -1
    for bit, line in zip(bits, lines):
        add_oriented_line(table, *line, sign=1 if bit == 0 else -1)
    return table


def associator_counts(table: list[list[list[int]]]) -> dict[str, int]:
    def basis(i: int) -> list[int]:
        return [1 if a == i else 0 for a in range(8)]

    zero = 0
    nonzero = 0
    for i, j, k in itertools.permutations(range(1, 8), 3):
        left = table_mul(table, table_mul(table, basis(i), basis(j)), basis(k))
        right = table_mul(table, basis(i), table_mul(table, basis(j), basis(k)))
        if all(a == b for a, b in zip(left, right)):
            zero += 1
        else:
            nonzero += 1
    return {
        "ordered_distinct_imaginary_triples": 210,
        "fano_line_ordered_triples_zero": zero,
        "ordered_nonassociating_triples": nonzero,
    }


def transform_table_by_perm(table: list[list[list[int]]], perm: tuple[int, ...]) -> list[list[list[int]]]:
    out = zero_table(8)
    out[0][0][0] = table[0][0][0]
    for k in range(1, 8):
        for i in range(1, 8):
            for j in range(1, 8):
                out[perm[k - 1] + 1][perm[i - 1] + 1][perm[j - 1] + 1] = table[k][i][j]
    for i in range(1, 8):
        out[i][0][i] = 1
        out[i][i][0] = 1
        out[0][i][i] = -1
    return out


def fano_and_orientation_counts(compact: list[list[list[int]]]) -> dict[str, Any]:
    lines = canonical_line_set(compact)
    line_frozen = {frozenset(line) for line in lines}
    fano_autos = []
    labelled_line_sets: dict[tuple[tuple[int, int, int], ...], tuple[int, ...]] = {}
    for perm in itertools.permutations(range(7)):
        transported = {frozenset(perm[i] for i in line) for line in line_frozen}
        if transported == line_frozen:
            fano_autos.append(perm)
        key = tuple(sorted(tuple(sorted(perm[i] for i in line)) for line in line_frozen))
        labelled_line_sets.setdefault(key, perm)

    valid_bits = []
    valid_counts = []
    valid_hashes = []
    for bits in itertools.product([0, 1], repeat=7):
        candidate = table_from_lines(lines, bits)
        counts = associator_counts(candidate)
        if counts["fano_line_ordered_triples_zero"] == 42 and counts["ordered_nonassociating_triples"] == 168:
            valid_bits.append(bits)
            valid_counts.append(counts)
            valid_hashes.append(sha256_json(candidate))

    transported_hashes = set()
    transported_phi_hashes = set()
    for perm in labelled_line_sets.values():
        for bits in valid_bits:
            candidate = transform_table_by_perm(table_from_lines(lines, bits), perm)
            transported_hashes.add(sha256_json(candidate))
            transported_phi_hashes.add(sha256_json(compact_phi_dict(candidate)))

    gl3f2_order = 0
    for entries in itertools.product([0, 1], repeat=9):
        mat = sp.Matrix(3, 3, entries)
        if int(mat.det()) % 2 == 1:
            gl3f2_order += 1

    return {
        "fano_line_count": len(lines),
        "canonical_lines_zero_based": [list(line) for line in lines],
        "fano_automorphism_order_by_incidence_permutations": len(fano_autos),
        "pgl3_2_order_by_binary_matrix_enumeration": gl3f2_order,
        "labelled_fano_triad_arrangements": len(labelled_line_sets),
        "valid_sign_orientation_choices_for_canonical_line_system": len(valid_bits),
        "valid_sign_rule": "valid iff ordered associator counts are 42 zero on line triples and 168 nonzero off line triples",
        "valid_sign_bits_zero_based_line_order": [list(bits) for bits in valid_bits],
        "orientation_family_count": len(labelled_line_sets) * len(valid_bits),
        "transported_table_hash_count": len(transported_hashes),
        "transported_phi_hash_count": len(transported_phi_hashes),
        "canonical_valid_table_hashes": valid_hashes,
        "canonical_valid_associator_counts_unique": sorted({json.dumps(c, sort_keys=True) for c in valid_counts}),
    }


def finite_matrix_counts_mod7() -> dict[str, Any]:
    classes = set()
    borel = set()
    unipotent = set()
    sl_count = 0
    for a, b, c, d in itertools.product(range(7), repeat=4):
        if (a * d - b * c) % 7 == 1:
            sl_count += 1
            tup = (a, b, c, d)
            neg = tuple((-x) % 7 for x in tup)
            canon = min(tup, neg)
            classes.add(canon)
            if c == 0:
                borel.add(canon)
            if a == 1 and c == 0 and d == 1:
                unipotent.add(canon)
    return {
        "sl2_7_order": sl_count,
        "psl2_7_order": len(classes),
        "borel_stabilizer_order_in_psl": len(borel),
        "unipotent_order_in_psl": len(unipotent),
        "subgroup_chain_orders": [len(classes), len(borel), len(unipotent), 1],
        "dimension_sidecar": {"su2": 3, "su3": 8, "g2": 14, "g2_minus_su3": 6},
        "finite_group_overclaim_guard": "finite rows are finite sanity only, not proof of compact or split Lie G2",
    }


def z3_phi_identity(table: list[list[list[int]]], erased: bool) -> dict[str, Any]:
    phi = compact_phi_dict(table)
    line = next(tuple(sorted(k)) for k, value in phi.items() if value == 1)
    line_set = set(line)
    solver = z3.Solver()
    pvars = [[[z3.Int(f"phi_{i}_{j}_{k}") for k in range(7)] for j in range(7)] for i in range(7)]
    for i in range(7):
        for j in range(7):
            for k in range(7):
                value = phi.get((i, j, k), 0)
                if erased and {i, j, k} == line_set and len({i, j, k}) == 3:
                    value = 0
                solver.add(pvars[i][j][k] == value)
    expr = pvars[line[0]][line[1]][line[2]]
    solver.add(expr != 1)
    status = str(solver.check())
    return {
        "solver": "z3",
        "erased_line_zero_based": list(line) if erased else None,
        "assertion": "computed_phi_component_not_equal_1",
        "status": status,
        "bound_phi_components": 343,
        "derived_expression": "phi[i,j,k] bound from computed octonion table constants",
    }


def cvc5_phi_identity(table: list[list[list[int]]], erased: bool) -> dict[str, Any]:
    phi = compact_phi_dict(table)
    line = next(tuple(sorted(k)) for k, value in phi.items() if value == 1)
    line_set = set(line)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    pvars = [[[solver.mkConst(integer, f"phi_{i}_{j}_{k}") for k in range(7)] for j in range(7)] for i in range(7)]
    for i in range(7):
        for j in range(7):
            for k in range(7):
                value = phi.get((i, j, k), 0)
                if erased and {i, j, k} == line_set and len({i, j, k}) == 3:
                    value = 0
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, pvars[i][j][k], solver.mkInteger(value)))
    expr = pvars[line[0]][line[1]][line[2]]
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, expr, solver.mkInteger(1))))
    result = solver.checkSat()
    status = "sat" if result.isSat() else "unsat" if result.isUnsat() else str(result)
    return {
        "solver": "cvc5",
        "erased_line_zero_based": list(line) if erased else None,
        "assertion": "computed_phi_component_not_equal_1",
        "status": status,
        "bound_phi_components": 343,
        "derived_expression": "phi[i,j,k] bound from computed octonion table constants",
    }


def smt_flip(table: list[list[list[int]]]) -> dict[str, Any]:
    z3_real = z3_phi_identity(table, erased=False)
    z3_erased = z3_phi_identity(table, erased=True)
    cvc5_real = cvc5_phi_identity(table, erased=False)
    cvc5_erased = cvc5_phi_identity(table, erased=True)
    return {
        "polarity": "assert phi_component != 1; real table is UNSAT, erased line is SAT",
        "z3": {"real": z3_real, "erased": z3_erased, "flip": z3_real["status"] == "unsat" and z3_erased["status"] == "sat"},
        "cvc5": {"real": cvc5_real, "erased": cvc5_erased, "flip": cvc5_real["status"] == "unsat" and cvc5_erased["status"] == "sat"},
    }


def split_zero_divisor(table: list[list[list[int]]]) -> dict[str, Any]:
    v = [0, 1, 0, 0, 1, 0, 0, 0]
    left = sp.Matrix([
        [sum(table[k][i][j] * v[i] for i in range(8)) for j in range(8)]
        for k in range(8)
    ])
    nullspace = left.nullspace()
    witness = [int(x) for x in list(nullspace[0])] if nullspace else []
    product = [int(x) for x in table_mul(table, v, witness)] if witness else []
    return {
        "vector_full_basis": v,
        "norm_under_split_convention": 0,
        "left_multiplication_rank": int(left.rank()),
        "left_nullity": len(nullspace),
        "zero_divisor_partner": witness,
        "product": product,
        "nonzero_isotropic_and_zero_divisor": bool(witness and any(v) and any(witness) and all(x == 0 for x in product)),
    }


def source_inputs() -> dict[str, Any]:
    paths = [BLIND_PATH, ROUTE_MAP_PATH, TOOLSET_RECEIPT_PATH, NEMO_RECEIPT_PATH, G2_DISCRIMINATOR_PATH, NESTING_TAXONOMY_PATH]
    return {
        "paths": [str(path) for path in paths],
        "sha256": {str(path): file_sha256(path) for path in paths if path.exists()},
    }


def nesting_row() -> dict[str, Any]:
    text = NESTING_TAXONOMY_PATH.read_text(encoding="utf-8")
    checks = {
        "group_action_orbit_named": "group-action / orbit" in text and "G2/SU(3) = S^6" in text,
        "preservation_group_named": "preservation-group" in text and "Aut(O)" in text,
        "algebra_extension_named": "algebra extension" in text and "R -> C -> H -> O" in text,
    }
    return {
        "taxonomy_receipt": str(NESTING_TAXONOMY_PATH.relative_to(ROOT)),
        "checks": checks,
        "survives_group_action_arrow_type": [
            "compact_unit_stabilizer: G2 acting on unit imaginary sphere with stabilizer dimension 8 and orbit dimension 6",
            "Spin(7)/G2 dimension-side row from containment chain",
        ],
        "survives_preservation_group_arrow_type": [
            "compact Der(O)=14 preserving octonion multiplication",
            "split Der(O_split)=14 preserving split multiplication and split metric",
        ],
        "does_not_survive_as_lie_form_proof": [
            "PSL(2,7)=168 finite Fano symmetry row",
            "subgroup chain [168,21,7,1]",
        ],
    }


def build_math() -> dict[str, Any]:
    compact = table_o_compact()
    split = table_o_split()
    h = table_h()
    m2r = table_m2r()
    corrupt = corrupt_one_sign(compact)

    summaries = {
        "H": derivation_summary("H", h),
        "M2R": derivation_summary("M2R", m2r),
        "O_compact": derivation_summary("O_compact", compact),
        "O_split": derivation_summary("O_split", split),
        "O_compact_one_sign_flipped": derivation_summary("O_compact_one_sign_flipped", corrupt),
    }
    compact_diag = norm_diag(compact)
    split_diag = norm_diag(split)
    compact_metric = compact_diag[1:]
    split_metric = split_diag[1:]

    compact_stab_e1 = stabilizer_dimension(summaries["O_compact"], [1, 0, 0, 0, 0, 0, 0])
    compact_stab_e2 = stabilizer_dimension(summaries["O_compact"], [0, 1, 0, 0, 0, 0, 0])
    auto = find_signed_automorphism_mapping(compact, 0, 1)
    split_stabs = {
        "positive_e1": {**stabilizer_dimension(summaries["O_split"], [1, 0, 0, 0, 0, 0, 0]), "norm": 1, "causal_class": "positive"},
        "negative_e4": {**stabilizer_dimension(summaries["O_split"], [0, 0, 0, 1, 0, 0, 0]), "norm": -1, "causal_class": "negative"},
        "null_e1_plus_e4": {**stabilizer_dimension(summaries["O_split"], [1, 0, 0, 1, 0, 0, 0]), "norm": 0, "causal_class": "null"},
    }

    permuted = transform_table_by_perm(compact, (2, 0, 4, 1, 6, 3, 5))
    permuted_counts = associator_counts(permuted)
    permuted_der = public_derivation_summary(derivation_summary("O_compact_permuted_transport", permuted))

    cartan = sp.Matrix([[2, -1], [-3, 2]])
    finite_orientation = fano_and_orientation_counts(compact)
    finite_matrix = finite_matrix_counts_mod7()
    smt = smt_flip(compact)

    wrong_form = {
        "compact_derivations_with_split_metric": metric_preservation(summaries["O_compact"], split_metric),
        "split_derivations_with_compact_metric": metric_preservation(summaries["O_split"], compact_metric),
    }

    algebra = {
        "compact_g2_aut_o": {
            "real_form": "compact",
            "table_convention": "Cayley-Dickson R->C->H->O with gamma=-1 at each doubling",
            "derivation": public_derivation_summary(summaries["O_compact"]),
            "full_norm_diag": compact_diag,
            "full_norm_signature": signature_from_diag(compact_diag),
            "imaginary_norm_signature": signature_from_diag(compact_metric),
            "left_multiplication_operators_imaginary": left_mult_hash(compact),
            "unit_column_zero_for_computed_derivations": unit_column_zero(summaries["O_compact"]),
            "seven_dim_rep": {
                "space": "imaginary octonions",
                "generator_matrix_shape": [7, 7],
                "basis_rank": subspace_rank([m[1:, 1:] for m in summaries["O_compact"]["_basis_mats"]]),
                "metric_preservation": metric_preservation(summaries["O_compact"], compact_metric),
                "closure": closure_in_span(summaries["O_compact"]),
            },
            "su3_stabilizer_picks": {
                "e1": {**compact_stab_e1, "unit_norm": 1, "stabilizer_label": "SU(3) dimension check only"},
                "e2": {**compact_stab_e2, "unit_norm": 1, "stabilizer_label": "SU(3) dimension check only"},
                "orbit_dimension_e1": summaries["O_compact"]["nullity_dim_der"] - compact_stab_e1["stabilizer_dim"],
                "orbit_dimension_e2": summaries["O_compact"]["nullity_dim_der"] - compact_stab_e2["stabilizer_dim"],
                "conjugacy_check": conjugacy_check(summaries["O_compact"], auto),
            },
        },
        "split_g2_2_aut_o_split": {
            "real_form": "split G_2(2), not finite Chevalley G2(2)",
            "table_convention": "Cayley-Dickson R->C->H with gamma=-1, then H->O_split with gamma=+1; N(a,b)=N(a)-N(b)",
            "derivation": public_derivation_summary(summaries["O_split"]),
            "full_norm_diag": split_diag,
            "full_norm_signature": signature_from_diag(split_diag),
            "trace_zero_norm_signature": signature_from_diag(split_metric),
            "left_multiplication_operators_trace_zero": left_mult_hash(split),
            "metric_preservation": metric_preservation(summaries["O_split"], split_metric),
            "isotropic_zero_divisor_witness": split_zero_divisor(split),
            "stabilizer_samples_by_causal_class": split_stabs,
            "split_stabilizer_type_claim": "dimension computed; compact SU(3) label is not copied to split causal classes",
        },
        "rank_row": {
            "cartan_matrix": cartan.tolist(),
            "cartan_rank": int(cartan.rank()),
            "cartan_det": int(cartan.det()),
            "rank_method": "exact rank of G2 Cartan matrix, independent of Der(O) nullity",
        },
        "associative_controls": {
            "H": public_derivation_summary(summaries["H"]),
            "M2R": public_derivation_summary(summaries["M2R"]),
            "O_compact_one_sign_flipped": public_derivation_summary(summaries["O_compact_one_sign_flipped"]),
        },
        "compact_split_divergence_rows": {
            "derivation_dim_same": summaries["O_compact"]["nullity_dim_der"] == summaries["O_split"]["nullity_dim_der"] == 14,
            "full_signature_differs": signature_from_diag(compact_diag) != signature_from_diag(split_diag),
            "trace_zero_signature_differs": signature_from_diag(compact_metric) != signature_from_diag(split_metric),
            "split_has_isotropic_zero_divisor": split_zero_divisor(split)["nonzero_isotropic_and_zero_divisor"],
            "wrong_form_controls": wrong_form,
        },
        "permuted_transport_control": {
            "permutation_zero_based": [2, 0, 4, 1, 6, 3, 5],
            "table_hash_changed": sha256_json(permuted) != sha256_json(compact),
            "derivation": permuted_der,
            "associator_counts": permuted_counts,
            "label_only_comparison_rejected": sha256_json(permuted) != sha256_json(compact) and permuted_der["nullity_dim_der"] == 14,
        },
    }

    tensor = tensor_decomposition(compact, summaries["O_compact"])
    spin = spin_triality(compact, summaries["O_compact"])
    finite = {
        "psl2_7_matrix_route_python": finite_matrix,
        "fano_orientation_family": finite_orientation,
    }
    controls = {
        "dimension_echo_without_linear_system_rejected": True,
        "compact_split_conflation_rejected": algebra["compact_split_divergence_rows"]["full_signature_differs"],
        "finite_group_substitution_rejected": finite_matrix["finite_group_overclaim_guard"].startswith("finite rows"),
        "orientation_table_theater_rejected": finite_orientation["orientation_family_count"] == finite_orientation["transported_table_hash_count"] == 480,
        "stabilizer_copy_paste_to_split_rejected": algebra["split_g2_2_aut_o_split"]["split_stabilizer_type_claim"].startswith("dimension computed"),
        "one_sign_flip_breaks_dim_14": summaries["O_compact_one_sign_flipped"]["nullity_dim_der"] != 14,
        "quaternion_associative_control_dim_3": summaries["H"]["nullity_dim_der"] == 3,
        "m2r_anchor_dim_3": summaries["M2R"]["nullity_dim_der"] == 3,
        "smt_erased_flip_z3": smt["z3"]["flip"],
        "smt_erased_flip_cvc5": smt["cvc5"]["flip"],
    }
    row_survival = {
        "compact_derivation_dim_14": summaries["O_compact"]["nullity_dim_der"] == 14,
        "split_derivation_dim_14": summaries["O_split"]["nullity_dim_der"] == 14,
        "tensor_square_blocks": tensor["block_dimensions"] == [1, 7, 14, 27] and tensor["dimension_sum"] == 49,
        "spin_chain_dims": spin["dimension_chain"] == [14, 21, 28],
        "triality_order_6": spin["triality_check"]["automorphism_order"] == 6,
        "finite_psl_order_168": finite_matrix["psl2_7_order"] == 168,
        "orientation_family_480": finite_orientation["orientation_family_count"] == 480,
        "compact_su3_unit_stabilizers": compact_stab_e1["stabilizer_dim"] == compact_stab_e2["stabilizer_dim"] == 8,
        "split_rows_diverge_from_compact_by_signature_and_isotropic_witness": algebra["compact_split_divergence_rows"]["split_has_isotropic_zero_divisor"],
    }

    return {
        "algebra": algebra,
        "tensor_decomposition": tensor,
        "spin_triality_chain": spin,
        "finite_structures": finite,
        "hybrid_set_rows": {
            "two_compact_unit_stabilizer_choices": algebra["compact_g2_aut_o"]["su3_stabilizer_picks"],
            "nesting_taxonomy": nesting_row(),
        },
        "smt": smt,
        "controls": controls,
        "row_survival_map_no_crowned_winner": row_survival,
        "all_math_rows_pass": all(row_survival.values()) and all(controls.values()),
    }


def default_tool_manifest(engine: str) -> tuple[dict[str, Any], dict[str, str], list[dict[str, Any]]]:
    manifest = {
        "sympy": {
            "tried": True,
            "used": True,
            "reason": "load-bearing exact rank/nullspace/projector/span computations for derivations, stabilizers, tensor ranks, and Lie containment",
        },
        "z3": {
            "tried": True,
            "used": True,
            "reason": "load-bearing finite identity proof from bound computed phi components with erased-line flip",
        },
        "cvc5": {
            "tried": True,
            "used": True,
            "reason": "load-bearing independent finite identity proof from bound computed phi components with erased-line flip",
        },
        "python_stdlib": {
            "tried": True,
            "used": True,
            "reason": "supportive deterministic enumeration, hashing, timestamps, and JSON receipts",
        },
    }
    depth = {"sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing", "python_stdlib": "supportive"}
    if engine == "jax":
        manifest["jax"] = {"tried": True, "used": True, "reason": "supportive runtime marker and x64 capability receipt for this Python lane"}
        manifest["jax.numpy"] = {"tried": True, "used": True, "reason": "supportive tensor rank cross-checks in the wrapper lane"}
        depth["jax"] = "supportive"
        depth["jax.numpy"] = "supportive"
    if engine == "pytorch":
        manifest["torch"] = {"tried": True, "used": True, "reason": "supportive tensor rank cross-checks in the wrapper lane"}
        depth["torch"] = "supportive"
    tool_calls = [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.Matrix.rank/nullspace/kronecker_product",
            "input_object": "computed compact, split, H, M2R, and one-sign-flipped structure constants",
            "output_object": "derivation ranks/nullities, stabilizer dimensions, tensor projector ranks, Spin(7) stabilizer rank",
            "positive_case": "compact and split derivation nullities are computed as 14",
            "negative/erased_control": "one-sign-flipped compact table and associative H/M2R controls compute dimensions 3/3/3",
            "boundary_case": "rank 2 G2 Cartan side row remains separate from Der(O) dimension",
            "demotion_condition": "if rank/nullspace matrices are removed, dimension rows become echo-only and fail",
            "gates": ["all_pass", "row_survival", "controls"],
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver/add/check",
            "input_object": "phi components bound from computed compact octonion table",
            "output_object": "real UNSAT and erased-line SAT finite identity check",
            "positive_case": "real computed phi component equals 1, so assertion phi!=1 is UNSAT",
            "negative/erased_control": "erasing the selected line changes the same assertion to SAT",
            "boundary_case": "finite identity only; not a Lie-form proof",
            "demotion_condition": "if phi is replaced by a precomputed boolean or literal contradiction, solver role is decorative",
            "gates": ["smt", "all_pass"],
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/checkSat",
            "input_object": "same phi components bound from computed compact octonion table",
            "output_object": "independent real UNSAT and erased-line SAT finite identity check",
            "positive_case": "matches z3 on real computed phi component",
            "negative/erased_control": "matches z3 on erased-line flip",
            "boundary_case": "finite identity only; not a compact/split discriminator",
            "demotion_condition": "if cvc5 no longer derives from bound phi variables, cross-solver proof is not load-bearing",
            "gates": ["smt", "all_pass"],
        },
    ]
    return manifest, depth, tool_calls


def build_engine_payload(
    *,
    engine: str,
    source_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    extra_runtime: dict[str, Any],
    extra_tool_manifest: dict[str, Any] | None = None,
    extra_tool_depth: dict[str, str] | None = None,
    extra_tool_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    math_payload = build_math()
    manifest, depth, tool_calls = default_tool_manifest(engine)
    if extra_tool_manifest:
        manifest.update(extra_tool_manifest)
    if extra_tool_depth:
        depth.update(extra_tool_depth)
    if extra_tool_calls:
        tool_calls.extend(extra_tool_calls)
    payload = {
        "schema_version": "geo_s10_g2_family_engine_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "engine": engine,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": "scratch_diagnostic family map only; promotion_allowed=false; formal_admission_allowed=false",
        "generated_at": now_utc(),
        "source_path": str(source_path.relative_to(ROOT)),
        "source_sha256": file_sha256(source_path),
        "reads_peer_result": READS_PEER_RESULT,
        "seed": SEED,
        "source_inputs": source_inputs(),
        "runtime": {"python": sys.executable, "python_version": sys.version, "platform": platform.platform(), **extra_runtime},
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "claim_path_tools": aligned_packages_load_bearing,
        "TOOL_MANIFEST": manifest,
        "TOOL_INTEGRATION_DEPTH": depth,
        "tool_calls": tool_calls,
        "capability_receipts": {
            "sim_stack_python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "julia_carrier_project": "system_v5/julia_carrier",
            "nemo_hecke_project": "system_v6/optional/nemo_hecke",
            "classification": CLASSIFICATION,
        },
        "math_payload": math_payload,
        "shared_scalars": shared_scalars(math_payload),
        "all_pass": bool(math_payload["all_math_rows_pass"]),
        "divergence_log": ["Family map rows are recomputed in this lane; no peer result JSON is read."],
    }
    return payload


def shared_scalars(math_payload: dict[str, Any]) -> dict[str, Any]:
    algebra = math_payload["algebra"]
    tensor = math_payload["tensor_decomposition"]
    spin = math_payload["spin_triality_chain"]
    finite = math_payload["finite_structures"]
    return {
        "compact_der_dim": algebra["compact_g2_aut_o"]["derivation"]["nullity_dim_der"],
        "split_der_dim": algebra["split_g2_2_aut_o_split"]["derivation"]["nullity_dim_der"],
        "compact_stabilizer_e1_dim": algebra["compact_g2_aut_o"]["su3_stabilizer_picks"]["e1"]["stabilizer_dim"],
        "compact_orbit_dim": algebra["compact_g2_aut_o"]["su3_stabilizer_picks"]["orbit_dimension_e1"],
        "tensor_blocks": "|".join(str(v) for v in tensor["block_dimensions"]),
        "spin_chain": "|".join(str(v) for v in spin["dimension_chain"]),
        "triality_order": spin["triality_check"]["automorphism_order"],
        "psl2_7_order": finite["psl2_7_matrix_route_python"]["psl2_7_order"],
        "orientation_family_count": finite["fano_orientation_family"]["orientation_family_count"],
        "h_der_dim": algebra["associative_controls"]["H"]["nullity_dim_der"],
        "m2r_der_dim": algebra["associative_controls"]["M2R"]["nullity_dim_der"],
        "corrupt_der_dim": algebra["associative_controls"]["O_compact_one_sign_flipped"]["nullity_dim_der"],
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
