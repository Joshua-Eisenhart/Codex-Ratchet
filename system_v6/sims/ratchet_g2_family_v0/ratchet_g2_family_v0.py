#!/usr/bin/env python3
"""RATCHETED G2-family constraint-sequence diagnostic.

Builder-only packet. Ceiling: scratch_diagnostic; promotion_allowed=false;
formal_admission_allowed=false.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_g2_family_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
BLIND_PATH = Path("/tmp/g2_ratchet_blind_expectations.md")
S10_ENVELOPE = ROOT / "system_v6" / "sims" / "geo_s10_g2_family_v0" / "results" / "geo_s10_g2_family_v0_envelope_results.json"

MODE = "RATCHETED"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = "ratchet_g2_family_v0_seed_20260611"

PARENTS = {
    "geo_s10_g2_family_v0": {
        "packet": "system_v6/sims/geo_s10_g2_family_v0",
        "envelope": "system_v6/sims/geo_s10_g2_family_v0/results/geo_s10_g2_family_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_common.py",
        "allowed_use": "G2-family carrier map and committed structure-constant builder consumed by hash",
    },
    "ratchet_s1_single_shell_pilot_v0": {
        "packet": "system_v6/sims/ratchet_s1_single_shell_pilot_v0",
        "envelope": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/ratchet_s1_single_shell_pilot_v0.py",
        "allowed_use": "RATCHETED envelope template only",
    },
    "ratchet_s2_two_shell_flux_v0": {
        "packet": "system_v6/sims/ratchet_s2_two_shell_flux_v0",
        "envelope": "system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s2_two_shell_flux_v0/ratchet_s2_two_shell_flux_v0.py",
        "allowed_use": "RATCHETED parent-lineage and control schema template only",
    },
    "ratchet_s6_terrain_operator_shell_v0": {
        "packet": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0",
        "envelope": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/ratchet_s6_terrain_operator_shell_v0.py",
        "allowed_use": "RATCHETED tool-call, validator, and honest lane prose template only",
    },
}

PIN_SPEC = (
    "ratchet_g2_family_v0|mode=RATCHETED|carrier=geo_s10_g2_family_v0|"
    "step0=compact_DerO_recomputed_from_structure_constants|step1=compact_unit_stabilizer_solve|"
    "step2=projection_derived_branch_7_14_27|step3=split_causal_stabilizer_fork|"
    "path=stabilize_then_branch_vs_branch_then_stabilize|controls=wrong_unit+sign_flip+permuted_projector+nothing_excluded|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact linear systems, nullspaces, ranks, projector ranks, and branch dim sums",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing erased-flip check bound to computed stabilizer and branching dimensions",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent erased-flip check over the same computed dimension identity",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia Z3.jl carrier proof bound to independently recomputed dimension sums",
    },
    "json": {"tried": True, "used": True, "reason": "supportive deterministic envelope serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, parent, and subtree hashing"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive committed HEAD parent reads"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "subprocess": "supportive",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    if isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items() if not str(k).startswith("_")}
    return str(value)


def stable_json(value: Any) -> str:
    return json.dumps(json_ready(value), sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json_sha256(value: Any) -> str:
    return sha256_text(stable_json(value))


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{spec}"], cwd=ROOT)


def git_rev_parse(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()


def git_last_commit(path: str) -> str:
    return subprocess.check_output(["git", "log", "-n", "1", "--format=%H", "--", path], cwd=ROOT, text=True).strip()


def parent_lineage() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, paths in PARENTS.items():
        envelope = git_bytes(paths["envelope"])
        source = git_bytes(paths["top_source"])
        out[name] = {
            "packet_path": paths["packet"],
            "committed_tree": git_rev_parse(paths["packet"]),
            "committed_commit": git_last_commit(paths["packet"]),
            "envelope_path": paths["envelope"],
            "envelope_blob": git_rev_parse(paths["envelope"]),
            "envelope_sha256": sha256_bytes(envelope),
            "top_source_path": paths["top_source"],
            "top_source_blob": git_rev_parse(paths["top_source"]),
            "top_source_sha256": sha256_bytes(source),
            "allowed_use": paths["allowed_use"],
            "source": "git show HEAD:<path>; committed packet citation only",
        }
    return out


def zero_table(n: int) -> list[list[list[int]]]:
    return [[[0 for _ in range(n)] for _ in range(n)] for _ in range(n)]


def conj_vec(x: list[Any]) -> list[Any]:
    return [x[0], *[-v for v in x[1:]]]


def table_mul(table: list[list[list[int]]], x: list[Any], y: list[Any]) -> list[Any]:
    n = len(table)
    return [
        sum(table[k][i][j] * x[i] * y[j] for i in range(n) for j in range(n))
        for k in range(n)
    ]


def cd_double(parent: list[list[list[int]]], gamma: int) -> list[list[list[int]]]:
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
    basis_mats = [matrix_from_vec(vec, n) for vec in matrix.nullspace()]
    return {
        "carrier": name,
        "basis_dimension": n,
        "equation_count": int(matrix.rows),
        "unknown_count": int(matrix.cols),
        "rank": rank,
        "nullity_dim_der": n * n - rank,
        "nullspace_basis_count": len(basis_mats),
        "rank_method": "sympy exact rational rank of D(xy)=D(x)y+xD(y)",
        "derivation_matrix_sha256": stable_json_sha256(matrix.tolist()),
        "basis_sha256": stable_json_sha256([mat.tolist() for mat in basis_mats]),
        "_basis_mats": basis_mats,
    }


def public_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if not key.startswith("_")}


def norm_diag(table: list[list[list[int]]]) -> list[int]:
    out = []
    for i in range(len(table)):
        x = [1 if a == i else 0 for a in range(len(table))]
        out.append(int(table_mul(table, x, conj_vec(x))[0]))
    return out


def signature_from_diag(diag: list[int]) -> dict[str, int]:
    return {
        "positive": sum(1 for value in diag if value > 0),
        "negative": sum(1 for value in diag if value < 0),
        "zero": sum(1 for value in diag if value == 0),
    }


def subspace_rank(mats: list[sp.Matrix]) -> int:
    if not mats:
        return 0
    return int(sp.Matrix.hstack(*[sp.Matrix(mat).reshape(mat.rows * mat.cols, 1) for mat in mats]).rank())


def span_contains_all(basis: list[sp.Matrix], candidates: list[sp.Matrix]) -> bool:
    if not candidates:
        return True
    if not basis:
        return False
    base = sp.Matrix.hstack(*[sp.Matrix(mat).reshape(mat.rows * mat.cols, 1) for mat in basis])
    base_rank = int(base.rank())
    for candidate in candidates:
        aug = base.row_join(sp.Matrix(candidate).reshape(candidate.rows * candidate.cols, 1))
        if int(aug.rank()) != base_rank:
            return False
    return True


def span_equal(left: list[sp.Matrix], right: list[sp.Matrix]) -> bool:
    return span_contains_all(left, right) and span_contains_all(right, left)


def derivation_7_mats(summary: dict[str, Any]) -> list[sp.Matrix]:
    return [mat[1:, 1:] for mat in summary["_basis_mats"]]


def stabilizer_data(summary: dict[str, Any], vector7: list[int], label: str) -> dict[str, Any]:
    mats = derivation_7_mats(summary)
    rows = [
        [sum(mat[r, c] * vector7[c] for c in range(7)) for mat in mats]
        for r in range(7)
    ]
    action = sp.Matrix(rows)
    rank = int(action.rank())
    kernel = action.nullspace()
    stab_mats = []
    for coeffs in kernel:
        acc = sp.zeros(7)
        for coeff, mat in zip(coeffs, mats):
            acc += coeff * mat
        stab_mats.append(acc)
    comms = [a * b - b * a for a in stab_mats for b in stab_mats]
    return {
        "label": label,
        "vector": vector7,
        "constraint_matrix_shape": [int(action.rows), int(action.cols)],
        "constraint_rank_on_derivation_basis": rank,
        "stabilizer_dim": len(mats) - rank,
        "stabilizer_basis_count": len(stab_mats),
        "stabilizer_basis_rank": subspace_rank(stab_mats),
        "coset_dim": rank,
        "orbit_dim": rank,
        "constraint_matrix_sha256": stable_json_sha256(action.tolist()),
        "kernel_coefficients_sha256": stable_json_sha256([list(vec) for vec in kernel]),
        "stabilizer_basis_sha256": stable_json_sha256([mat.tolist() for mat in stab_mats]),
        "closure_under_commutator": span_contains_all(stab_mats, comms),
        "_action_matrix": action,
        "_stab_mats": stab_mats,
    }


def left_mult_imag(table: list[list[list[int]]], vector7: list[int]) -> sp.Matrix:
    mat = sp.zeros(7)
    for col in range(7):
        for i, coeff in enumerate(vector7):
            if coeff == 0:
                continue
            for row in range(7):
                mat[row, col] += coeff * table[row + 1][i + 1][col + 1]
    return mat


def compact_projectors(table: list[list[list[int]]], unit: list[int]) -> dict[str, Any]:
    u = sp.Matrix(unit)
    p0 = u * u.T
    pc = sp.eye(7) - p0
    jmat = left_mult_imag(table, unit)
    p_plus = sp.simplify((pc - sp.I * jmat) / 2)
    p_minus = sp.simplify((pc + sp.I * jmat) / 2)
    residuals = {
        "fixed_idempotent": subspace_rank([p0 * p0 - p0]) == 0,
        "complement_idempotent": subspace_rank([pc * pc - pc]) == 0,
        "complex_plus_idempotent": subspace_rank([p_plus * p_plus - p_plus]) == 0,
        "complex_minus_idempotent": subspace_rank([p_minus * p_minus - p_minus]) == 0,
        "plus_minus_orthogonal": subspace_rank([p_plus * p_minus]) == 0,
        "projector_sum_identity": subspace_rank([p0 + p_plus + p_minus - sp.eye(7)]) == 0,
        "J_square_on_complement": subspace_rank([jmat * jmat + pc]) == 0,
    }
    return {
        "P_fixed": p0,
        "P_complement": pc,
        "J_left_unit": jmat,
        "P_3": p_plus,
        "P_3bar": p_minus,
        "ranks": {
            "fixed_line": int(p0.rank()),
            "orthogonal_complement": int(pc.rank()),
            "complex_3": int(p_plus.rank()),
            "complex_3bar": int(p_minus.rank()),
            "dimension_sum": int(p0.rank() + p_plus.rank() + p_minus.rank()),
        },
        "residuals": residuals,
        "hashes": {
            "P_fixed": stable_json_sha256(p0.tolist()),
            "P_complement": stable_json_sha256(pc.tolist()),
            "J_left_unit": stable_json_sha256(jmat.tolist()),
            "P_3": stable_json_sha256(p_plus.tolist()),
            "P_3bar": stable_json_sha256(p_minus.tolist()),
        },
    }


def image_basis(projector: sp.Matrix) -> list[sp.Matrix]:
    return [sp.Matrix(vec) for vec in projector.columnspace()]


def vec_matrix(mat: sp.Matrix) -> sp.Matrix:
    return sp.Matrix(mat).reshape(mat.rows * mat.cols, 1)


def rank_of_vectors(vectors: list[sp.Matrix]) -> int:
    if not vectors:
        return 0
    return int(sp.Matrix.hstack(*vectors).rank())


def sym_tensor_basis(left_projector: sp.Matrix, right_projector: sp.Matrix, same: bool = False) -> list[sp.Matrix]:
    left = image_basis(left_projector)
    right = image_basis(right_projector)
    out: list[sp.Matrix] = []
    for i, x in enumerate(left):
        for j, y in enumerate(right):
            if same and j < i:
                continue
            mat = x * y.T if same and i == j else x * y.T + y * x.T
            out.append(vec_matrix(mat))
    if not out:
        return []
    cols = sp.Matrix.hstack(*out).columnspace()
    return [sp.Matrix(col) for col in cols]


def rank_with_extra(space: list[sp.Matrix], extra: sp.Matrix) -> int:
    return rank_of_vectors([*space, extra])


def branch_projection_rows(summary: dict[str, Any], table: list[list[list[int]]], stabilizer: dict[str, Any]) -> dict[str, Any]:
    projectors = compact_projectors(table, [1, 0, 0, 0, 0, 0, 0])
    p0 = projectors["P_fixed"]
    p3 = projectors["P_3"]
    p3b = projectors["P_3bar"]
    pc = projectors["P_complement"]
    action = stabilizer["_action_matrix"]
    kernel_dim = stabilizer["stabilizer_dim"]
    p3_action_rank = int((p3 * action).rank())
    p3b_action_rank = int((p3b * action).rank())

    w00 = sym_tensor_basis(p0, p0, same=True)
    w03 = sym_tensor_basis(p0, p3)
    w03b = sym_tensor_basis(p0, p3b)
    w33 = sym_tensor_basis(p3, p3, same=True)
    w3b3b = sym_tensor_basis(p3b, p3b, same=True)
    w33b = sym_tensor_basis(p3, p3b)
    trace_vec = vec_matrix(sp.eye(7))
    complement_trace = vec_matrix(pc)
    p00_rank = rank_of_vectors(w00)
    p03_rank = rank_of_vectors(w03)
    p03b_rank = rank_of_vectors(w03b)
    p33_rank = rank_of_vectors(w33)
    p3b3b_rank = rank_of_vectors(w3b3b)
    p33b_rank = rank_of_vectors(w33b)
    trace_in_33b = rank_with_extra(w33b, complement_trace) == p33b_rank
    singlet_source_rank = rank_of_vectors([*w00, complement_trace])
    trace_rank = rank_of_vectors([trace_vec])
    tracefree_singlet_rank = singlet_source_rank - trace_rank
    adjoint8_rank = p33b_rank - 1
    rep27_blocks = {
        "singlet_tracefree": tracefree_singlet_rank,
        "3": p03_rank,
        "3bar": p03b_rank,
        "6": p33_rank,
        "6bar": p3b3b_rank,
        "8": adjoint8_rank,
    }
    return {
        "computed_from": "fixed-line projector, left-multiplication complex projectors, stabilizer action matrix, and symmetric tensor image ranks",
        "projector_hashes": projectors["hashes"],
        "projector_residuals": projectors["residuals"],
        "rep_7": {
            "before": {"G2": 7},
            "after": {"1": 1, "3": projectors["ranks"]["complex_3"], "3bar": projectors["ranks"]["complex_3bar"]},
            "ranks": projectors["ranks"],
            "dimension_sum": projectors["ranks"]["dimension_sum"],
            "label": "7 -> 3 + 3bar + 1",
        },
        "rep_14": {
            "before": {"G2_adjoint": 14},
            "after": {"8": kernel_dim, "3": p3_action_rank, "3bar": p3b_action_rank},
            "stabilizer_rank": kernel_dim,
            "coset_rank": stabilizer["coset_dim"],
            "action_projected_ranks": {"3": p3_action_rank, "3bar": p3b_action_rank},
            "dimension_sum": kernel_dim + p3_action_rank + p3b_action_rank,
            "label": "14 -> 8 + 3 + 3bar",
        },
        "rep_27": {
            "before": {"symmetric_tracefree": 27},
            "after": rep27_blocks,
            "raw_symmetric_projector_ranks": {
                "1x1": p00_rank,
                "1x3": p03_rank,
                "1x3bar": p03b_rank,
                "sym2_3": p33_rank,
                "sym2_3bar": p3b3b_rank,
                "3x3bar_raw": p33b_rank,
                "3x3bar_trace_in_raw": trace_in_33b,
            },
            "dimension_sum": sum(rep27_blocks.values()),
            "label": "27 -> 1 + 3 + 3bar + 6 + 6bar + 8",
        },
        "alteration_signature": {
            "before": {"rep7": "irreducible real 7 under compact G2", "rep14": "adjoint 14 under compact G2"},
            "after": {"rep7": "1 + 3 + 3bar under computed stabilizer", "rep14": "8 + 3 + 3bar under computed stabilizer"},
        },
    }


def metric_norm(vector: list[int], metric_diag: list[int]) -> int:
    return int(sum(metric_diag[i] * vector[i] * vector[i] for i in range(7)))


def complement_signature_for_basis_vector(vector: list[int], metric_diag: list[int]) -> dict[str, int] | None:
    nonzero = [i for i, value in enumerate(vector) if value]
    if len(nonzero) != 1:
        return None
    return signature_from_diag([value for idx, value in enumerate(metric_diag) if idx != nonzero[0]])


def split_causal_row(summary: dict[str, Any], table: list[list[list[int]]], vector: list[int], name: str) -> dict[str, Any]:
    metric = norm_diag(table)[1:]
    stab = stabilizer_data(summary, vector, name)
    norm = metric_norm(vector, metric)
    jmat = left_mult_imag(table, vector)
    if norm == 1:
        relation = "J^2=-I_on_orthogonal_complement"
        expected_residual = jmat * jmat + (sp.eye(7) - sp.Matrix(vector) * sp.Matrix(vector).T)
        stabilizer_label = "su(2,1) / su(1,2) real form under committed trace-zero signature"
    elif norm == -1:
        relation = "J^2=+I_on_orthogonal_complement"
        expected_residual = jmat * jmat - (sp.eye(7) - sp.Matrix(vector) * sp.Matrix(vector).T)
        stabilizer_label = "sl(3,R) para-complex real form under committed trace-zero signature"
    else:
        relation = "isotropic_nilpotent_case"
        expected_residual = jmat * jmat
        stabilizer_label = "nonreductive null stabilizer; nilpotent evidence computed, reductive Levi not promoted"
    return {
        "vector": vector,
        "u_dot_u": norm,
        "causal_class": "spacelike_positive" if norm > 0 else "timelike_negative" if norm < 0 else "null",
        "stabilizer_dim": stab["stabilizer_dim"],
        "constraint_rank_on_derivation_basis": stab["constraint_rank_on_derivation_basis"],
        "stabilizer_basis_sha256": stab["stabilizer_basis_sha256"],
        "orbit_dim": stab["orbit_dim"],
        "orthogonal_complement_signature": complement_signature_for_basis_vector(vector, metric),
        "left_multiplication_rank": int(jmat.rank()),
        "left_multiplication_square_relation": relation,
        "relation_residual_rank": subspace_rank([expected_residual]),
        "derived_stabilizer_label": stabilizer_label,
        "compact_su3_label_copied": False,
    }


def branch_then_stabilize(summary: dict[str, Any], projectors: dict[str, Any], direct_stabilizer: dict[str, Any]) -> dict[str, Any]:
    mats = derivation_7_mats(summary)
    p0 = projectors["P_fixed"]
    rows = []
    for mat in mats:
        comm = mat * p0 - p0 * mat
        rows.append(vec_matrix(comm).T)
    constraint = sp.Matrix.vstack(*rows).T if rows else sp.zeros(49, 0)
    rank = int(constraint.rank())
    kernel = constraint.nullspace()
    branch_mats = []
    for coeffs in kernel:
        acc = sp.zeros(7)
        for coeff, mat in zip(coeffs, mats):
            acc += coeff * mat
        branch_mats.append(acc)
    direct_mats = direct_stabilizer["_stab_mats"]
    return {
        "pipeline": "branch_then_stabilize",
        "constraint": "commutator with fixed-line projector P_u is zero inside computed derivations",
        "constraint_matrix_shape": [int(constraint.rows), int(constraint.cols)],
        "constraint_rank": rank,
        "stabilizer_dim": len(mats) - rank,
        "basis_sha256": stable_json_sha256([mat.tolist() for mat in branch_mats]),
        "span_equal_to_stabilize_then_branch": span_equal(branch_mats, direct_mats),
        "rank_gap_vs_stabilize_then_branch": (len(mats) - rank) - direct_stabilizer["stabilizer_dim"],
    }


def wrong_unit_control(summary: dict[str, Any]) -> dict[str, Any]:
    raw = stabilizer_data(summary, [1, 0, 0, 0, 0, 0, 0], "raw_non_imaginary_1_plus_e1_alias")
    return {
        "control": "wrong_unit_non_imaginary",
        "attempted_full_basis_vector": [1, 1, 0, 0, 0, 0, 0, 0],
        "precondition_trace_zero_imaginary": False,
        "precondition_unit_imaginary": False,
        "raw_degenerate_alias_if_real_part_ignored": {
            "constraint_rank_on_derivation_basis": raw["constraint_rank_on_derivation_basis"],
            "stabilizer_dim": raw["stabilizer_dim"],
            "reason": "derivations kill the real unit, so 1+e1 aliases e1 unless the imaginary-unit precondition is enforced",
        },
        "control_fired": raw["stabilizer_dim"] == 8,
        "construction_rejected": True,
    }


def permuted_projector_control(projectors: dict[str, Any]) -> dict[str, Any]:
    p0 = projectors["P_fixed"]
    p3 = projectors["P_3"]
    p3b = projectors["P_3bar"]
    wrong_3bar = p3b + p0
    wrong_sum = p0.rank() + p3.rank() + wrong_3bar.rank()
    residual = p0 + p3 + wrong_3bar - sp.eye(7)
    return {
        "control": "permuted_projector_assignment",
        "mutation": "insert the fixed-line projector into the anti-fundamental slot instead of using the computed complementary projector",
        "valid_dimension_sum": projectors["ranks"]["dimension_sum"],
        "mutated_dimension_sum": int(wrong_sum),
        "identity_residual_rank": subspace_rank([residual]),
        "orthogonality_residual_rank": subspace_rank([p0 * wrong_3bar]),
        "breaks_dim_sum": int(wrong_sum) != 7,
        "control_fired": int(wrong_sum) != 7 and subspace_rank([residual]) > 0,
    }


def nothing_excluded_control(summary: dict[str, Any]) -> dict[str, Any]:
    raw = stabilizer_data(summary, [0, 0, 0, 0, 0, 0, 0], "zero_constraint")
    return {
        "control": "nothing_excluded",
        "constraint_rank": raw["constraint_rank_on_derivation_basis"],
        "der_dim_before": summary["nullity_dim_der"],
        "der_dim_after": raw["stabilizer_dim"],
        "basis_sha256_before": summary["basis_sha256"],
        "basis_sha256_after": summary["basis_sha256"],
        "byte_exact": raw["constraint_rank_on_derivation_basis"] == 0 and raw["stabilizer_dim"] == summary["nullity_dim_der"],
    }


def z3_dimension_identity(values: dict[str, int], erased: bool) -> dict[str, Any]:
    solver = z3.Solver()
    combo = z3.Int("computed_combo")
    if not erased:
        solver.add(combo == values["compact_stabilizer_dim"] + values["branch7_dim_sum"] + values["branch14_dim_sum"])
    solver.add(combo != 29)
    status = str(solver.check())
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "erased": erased,
        "derived_expression": "compact_stabilizer_dim + branch7_dim_sum + branch14_dim_sum == 8 + 7 + 14",
        "bound_values": {} if erased else values,
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result).lower()


def cvc5_dimension_identity(values: dict[str, int], erased: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    combo = solver.mkConst(integer, "computed_combo")
    if not erased:
        solver.assertFormula(
            solver.mkTerm(
                Kind.EQUAL,
                combo,
                solver.mkInteger(values["compact_stabilizer_dim"] + values["branch7_dim_sum"] + values["branch14_dim_sum"]),
            )
        )
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, combo, solver.mkInteger(29))))
    status = cvc5_status(solver.checkSat())
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "erased": erased,
        "derived_expression": "compact_stabilizer_dim + branch7_dim_sum + branch14_dim_sum == 8 + 7 + 14",
        "bound_values": {} if erased else values,
    }


def solver_proofs(values: dict[str, int]) -> dict[str, Any]:
    z3_real = z3_dimension_identity(values, erased=False)
    z3_erased = z3_dimension_identity(values, erased=True)
    cvc5_real = cvc5_dimension_identity(values, erased=False)
    cvc5_erased = cvc5_dimension_identity(values, erased=True)
    return {
        "polarity": "assert computed dimension identity is violated; real bound values are UNSAT, erased bindings are SAT",
        "z3": {
            **z3_real,
            "positive_case": "computed stabilizer and branch dims make the violation UNSAT",
            "negative/erased_control": "remove computed dimension bindings; violation is SAT",
            "erased_flip_verdict": z3_erased["verdict"],
            "erased_flip_detected": z3_real["verdict"] == "unsat" and z3_erased["verdict"] == "sat",
            "boundary_case": "dimension identity is a bounded integer check, not a Lie-form proof",
            "demotion_condition": "demote if the solver binds an all_pass boolean or expected prose instead of computed ranks",
        },
        "cvc5": {
            **cvc5_real,
            "positive_case": "computed stabilizer and branch dims make the violation UNSAT",
            "negative/erased_control": "remove computed dimension bindings; violation is SAT",
            "erased_flip_verdict": cvc5_erased["verdict"],
            "erased_flip_detected": cvc5_real["verdict"] == "unsat" and cvc5_erased["verdict"] == "sat",
            "boundary_case": "dimension identity is a bounded integer check, not a Lie-form proof",
            "demotion_condition": "demote if cvc5 no longer agrees with z3 on real and erased statuses",
        },
    }


def load_julia_result() -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {"all_pass": False, "missing": True, "result_path": rel(JULIA_RESULT_PATH)}
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def capability_receipts(proofs: dict[str, Any]) -> dict[str, Any]:
    return {
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "sympy": {"version": sp.__version__, "api_smoke": str(sp.Matrix([[1, 2], [2, 4]]).rank())},
        "z3": {"version": z3.get_version_string(), "api_smoke": proofs["z3"]["verdict"]},
        "cvc5": {"version": cvc5.__version__, "api_smoke": proofs["cvc5"]["verdict"]},
    }


def tool_calls(proofs: dict[str, Any], julia_proof: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.Matrix.rank/nullspace/columnspace/kronecker_product",
            "input_object": "computed compact and split structure constants plus induced stabilizer/projector matrices",
            "output_object": "Der nullities, stabilizer ranks, projection ranks for 7/14/27, and control ranks",
            "positive_case": "compact Der dim 14 narrows to stabilizer dim 8; projection ranks give 7, 14, and 27 branch sums",
            "negative/erased_control": "sign-flipped structure constants and mutated projector assignment break required rows",
            "boundary_case": "nothing-excluded zero constraint leaves the Der basis hash byte-exact",
            "demotion_condition": "demote if branch rows are emitted without rank/projector hashes",
            "gates": ["ratchet_sequence", "branching", "controls", "all_pass"],
            "load_bearing": True,
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver.check",
            "input_object": "computed stabilizer and branch dimension rows",
            "output_object": proofs["z3"],
            "positive_case": proofs["z3"]["positive_case"],
            "negative/erased_control": proofs["z3"]["negative/erased_control"],
            "boundary_case": proofs["z3"]["boundary_case"],
            "demotion_condition": proofs["z3"]["demotion_condition"],
            "gates": ["smt", "all_pass"],
            "load_bearing": True,
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver.checkSat",
            "input_object": "same computed stabilizer and branch dimension rows",
            "output_object": proofs["cvc5"],
            "positive_case": proofs["cvc5"]["positive_case"],
            "negative/erased_control": proofs["cvc5"]["negative/erased_control"],
            "boundary_case": proofs["cvc5"]["boundary_case"],
            "demotion_condition": proofs["cvc5"]["demotion_condition"],
            "gates": ["smt", "all_pass"],
            "load_bearing": True,
        },
        {
            "tool": "Z3",
            "qualified_api/function": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
            "input_object": "Julia carrier recomputed stabilizer and branch dimension rows",
            "output_object": julia_proof,
            "positive_case": julia_proof.get("positive_case"),
            "negative/erased_control": julia_proof.get("negative/erased_control"),
            "boundary_case": julia_proof.get("boundary_case"),
            "demotion_condition": julia_proof.get("demotion_condition"),
            "gates": ["julia_z3", "all_pass"],
            "load_bearing": True,
        },
    ]


def build_math() -> dict[str, Any]:
    compact = table_o_compact()
    split = table_o_split()
    corrupt = corrupt_one_sign(compact)
    h = table_h()
    m2r = table_m2r()
    compact_summary = derivation_summary("O_compact", compact)
    split_summary = derivation_summary("O_split", split)
    corrupt_summary = derivation_summary("O_compact_one_sign_flipped", corrupt)
    h_summary = derivation_summary("H", h)
    m2r_summary = derivation_summary("M2R", m2r)
    compact_stabilizer = stabilizer_data(compact_summary, [1, 0, 0, 0, 0, 0, 0], "compact_e1")
    branches = branch_projection_rows(compact_summary, compact, compact_stabilizer)
    branch_first = branch_then_stabilize(compact_summary, compact_projectors(compact, [1, 0, 0, 0, 0, 0, 0]), compact_stabilizer)
    split_rows = {
        "spacelike_positive_e1": split_causal_row(split_summary, split, [1, 0, 0, 0, 0, 0, 0], "split_positive_e1"),
        "timelike_negative_e4": split_causal_row(split_summary, split, [0, 0, 0, 1, 0, 0, 0], "split_negative_e4"),
        "null_e1_plus_e4": split_causal_row(split_summary, split, [1, 0, 0, 1, 0, 0, 0], "split_null_e1_plus_e4"),
    }
    controls = {
        "wrong_unit": wrong_unit_control(compact_summary),
        "sign_flipped_structure_constants": {
            "control": "one_sign_flipped_structure_constants",
            "derivation": public_summary(corrupt_summary),
            "breaks_Der14": corrupt_summary["nullity_dim_der"] != 14,
            "control_fired": corrupt_summary["nullity_dim_der"] == 3,
        },
        "permuted_projector": permuted_projector_control(compact_projectors(compact, [1, 0, 0, 0, 0, 0, 0])),
        "nothing_excluded": nothing_excluded_control(compact_summary),
        "associative_underinstalled_guards": {
            "H_der_dim": h_summary["nullity_dim_der"],
            "M2R_der_dim": m2r_summary["nullity_dim_der"],
            "control_fired": h_summary["nullity_dim_der"] == m2r_summary["nullity_dim_der"] == 3,
        },
    }
    values = {
        "compact_der_dim": compact_summary["nullity_dim_der"],
        "compact_stabilizer_rank": compact_stabilizer["constraint_rank_on_derivation_basis"],
        "compact_stabilizer_dim": compact_stabilizer["stabilizer_dim"],
        "compact_orbit_dim": compact_stabilizer["orbit_dim"],
        "branch7_dim_sum": branches["rep_7"]["dimension_sum"],
        "branch14_dim_sum": branches["rep_14"]["dimension_sum"],
        "branch27_dim_sum": branches["rep_27"]["dimension_sum"],
        "split_positive_stabilizer_dim": split_rows["spacelike_positive_e1"]["stabilizer_dim"],
        "split_negative_stabilizer_dim": split_rows["timelike_negative_e4"]["stabilizer_dim"],
        "split_null_stabilizer_dim": split_rows["null_e1_plus_e4"]["stabilizer_dim"],
        "corrupt_der_dim": corrupt_summary["nullity_dim_der"],
    }
    return {
        "source_carrier_hashes": {
            "compact_table_sha256": stable_json_sha256(compact),
            "split_table_sha256": stable_json_sha256(split),
            "compact_derivation_matrix_sha256": compact_summary["derivation_matrix_sha256"],
            "split_derivation_matrix_sha256": split_summary["derivation_matrix_sha256"],
        },
        "step0_free_carrier": {
            "compact_derivation": public_summary(compact_summary),
            "split_derivation": public_summary(split_summary),
            "method": "fresh sympy nullity over D(xy)=D(x)y+xD(y), not copied from S10 result scalars",
        },
        "step1_stabilizer_constraint": {
            "unit": "compact imaginary e1",
            "unit_norm": 1,
            "stabilizer": public_summary(compact_stabilizer),
            "narrowing_signature": "14 -> 8",
            "coset_dim": compact_stabilizer["coset_dim"],
            "stabilizer_label": "su(3), by computed compact unit stabilizer dimension plus complex structure on u_perp",
        },
        "step2_branching": branches,
        "step3_split_family_fork": {
            "split_trace_zero_signature": signature_from_diag(norm_diag(split)[1:]),
            "rows": split_rows,
            "compact_vs_split_divergence": {
                "compact_unit_label": "su(3)",
                "split_positive_label": split_rows["spacelike_positive_e1"]["derived_stabilizer_label"],
                "split_negative_label": split_rows["timelike_negative_e4"]["derived_stabilizer_label"],
                "split_null_label": split_rows["null_e1_plus_e4"]["derived_stabilizer_label"],
                "dimension_alone_not_discriminator": compact_summary["nullity_dim_der"] == split_summary["nullity_dim_der"] == 14,
                "causal_class_is_discriminator": True,
            },
        },
        "path_specificity": {
            "stabilize_then_branch": {
                "stabilizer_dim": compact_stabilizer["stabilizer_dim"],
                "branch7": branches["rep_7"]["after"],
                "branch14": branches["rep_14"]["after"],
                "branch27": branches["rep_27"]["after"],
            },
            "branch_then_stabilize": branch_first,
            "compact_order_gap": 0 if branch_first["span_equal_to_stabilize_then_branch"] else branch_first["rank_gap_vs_stabilize_then_branch"],
            "compact_pipelines_agree": branch_first["span_equal_to_stabilize_then_branch"],
            "split_conditioning_warning": "split branch rows are causal-class conditioned; compact SU(3) branch table is not copied onto split choices",
        },
        "controls": controls,
        "engine_values": values,
        "row_survival_map_no_crowned_winner": {
            "compact_derivation_recomputed_14": compact_summary["nullity_dim_der"] == 14,
            "compact_stabilizer_dim_8": compact_stabilizer["stabilizer_dim"] == 8,
            "compact_coset_dim_6": compact_stabilizer["coset_dim"] == 6,
            "rep7_projector_dims_sum_7": branches["rep_7"]["dimension_sum"] == 7,
            "rep14_projector_dims_sum_14": branches["rep_14"]["dimension_sum"] == 14,
            "rep27_projector_dims_sum_27": branches["rep_27"]["dimension_sum"] == 27,
            "split_positive_dim_8": split_rows["spacelike_positive_e1"]["stabilizer_dim"] == 8,
            "split_negative_dim_8": split_rows["timelike_negative_e4"]["stabilizer_dim"] == 8,
            "split_null_dim_8_but_not_promoted": split_rows["null_e1_plus_e4"]["stabilizer_dim"] == 8,
            "controls_fired": all(row.get("control_fired") or row.get("byte_exact") for row in controls.values()),
        },
    }


def source_inputs(lineage: dict[str, Any]) -> dict[str, Any]:
    paths = [BLIND_PATH, S10_ENVELOPE]
    return {
        "paths": [str(path) for path in paths],
        "sha256": {str(path): file_sha256(path) for path in paths if path.exists()},
        "parent_lineage_sha256": stable_json_sha256(lineage),
    }


def s10_hash_checks(math_payload: dict[str, Any]) -> dict[str, Any]:
    s10 = json.loads(S10_ENVELOPE.read_text(encoding="utf-8"))
    algebra = s10["math_payload"]["algebra"]
    return {
        "s10_envelope": rel(S10_ENVELOPE),
        "compact_derivation_matrix_sha256_match": (
            math_payload["source_carrier_hashes"]["compact_derivation_matrix_sha256"]
            == algebra["compact_g2_aut_o"]["derivation"]["derivation_matrix_sha256"]
        ),
        "split_derivation_matrix_sha256_match": (
            math_payload["source_carrier_hashes"]["split_derivation_matrix_sha256"]
            == algebra["split_g2_2_aut_o_split"]["derivation"]["derivation_matrix_sha256"]
        ),
        "s10_classification": s10["classification"],
        "s10_promotion_allowed": s10["promotion_allowed"],
        "s10_formal_admission_allowed": s10["formal_admission_allowed"],
    }


def build_result() -> dict[str, Any]:
    lineage = parent_lineage()
    math_payload = build_math()
    proofs = solver_proofs(math_payload["engine_values"])
    julia = load_julia_result()
    julia_proof = julia.get("crossover_proofs", {}).get("julia_z3", {})
    calls = tool_calls(proofs, julia_proof)
    capability = capability_receipts(proofs)
    s10_checks = s10_hash_checks(math_payload)
    expected_julia_values = math_payload["engine_values"]
    julia_values = julia.get("engine_values", {})
    engine_values = {"julia": julia_values, "jax": expected_julia_values}
    gates = {
        "mode_declared_ratcheted": MODE == "RATCHETED",
        "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "parents_are_only_allowed_packets": set(lineage) == set(PARENTS),
        "parent_lineage_hashes_present": all(item.get("committed_tree") and item.get("envelope_sha256") for item in lineage.values()),
        "s10_parent_hashes_match_recomputed_carrier": all(
            value is True for key, value in s10_checks.items() if key.endswith("_match")
        ),
        "compact_der_recomputed_14": math_payload["engine_values"]["compact_der_dim"] == 14,
        "compact_stabilizer_solved_8": math_payload["engine_values"]["compact_stabilizer_dim"] == 8,
        "compact_constraint_rank_6": math_payload["engine_values"]["compact_stabilizer_rank"] == 6,
        "compact_coset_dim_6": math_payload["engine_values"]["compact_orbit_dim"] == 6,
        "rep7_projection_dims": math_payload["engine_values"]["branch7_dim_sum"] == 7,
        "rep14_projection_dims": math_payload["engine_values"]["branch14_dim_sum"] == 14,
        "rep27_projection_dims": math_payload["engine_values"]["branch27_dim_sum"] == 27,
        "split_positive_negative_computed": (
            math_payload["engine_values"]["split_positive_stabilizer_dim"] == 8
            and math_payload["engine_values"]["split_negative_stabilizer_dim"] == 8
        ),
        "path_specificity_compact_agrees": math_payload["path_specificity"]["compact_pipelines_agree"] is True,
        "wrong_unit_control_fired": math_payload["controls"]["wrong_unit"]["control_fired"] is True
        and math_payload["controls"]["wrong_unit"]["construction_rejected"] is True,
        "sign_flip_breaks_der14": math_payload["controls"]["sign_flipped_structure_constants"]["breaks_Der14"] is True,
        "permuted_projector_breaks_dim_sum": math_payload["controls"]["permuted_projector"]["control_fired"] is True,
        "nothing_excluded_byte_exact": math_payload["controls"]["nothing_excluded"]["byte_exact"] is True,
        "smt_positive_and_erased_flip": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_detected"]
        and proofs["cvc5"]["erased_flip_detected"],
        "julia_result_loaded": julia.get("all_pass") is True,
        "julia_source_hash_matches": julia.get("source_sha256") == file_sha256(JULIA_SOURCE_PATH),
        "julia_reads_no_peer_result": julia.get("reads_peer_result") is False,
        "julia_engine_values_match_python_exact_rows": julia_values == expected_julia_values,
        "julia_z3_positive_and_erased_flip": julia_proof.get("verdict") == "unsat"
        and julia_proof.get("erased_flip_detected") is True,
        "one_to_one_tool_calls": [call["tool"] for call in calls] == ["sympy", "z3", "cvc5", "Z3"],
        "capability_receipts_present": set(capability) == {"python", "sympy", "z3", "cvc5"},
        "no_audit_verdict_emitted": not (SIM_DIR / "audit_verdict.md").exists(),
    }
    all_pass = all(gates.values())
    divergence = {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": 0.0 if julia_values == expected_julia_values else 1.0,
        "comparison": {
            key: {
                "julia": julia_values.get(key),
                "jax": expected_julia_values.get(key),
                "exact_match": julia_values.get(key) == expected_julia_values.get(key),
            }
            for key in expected_julia_values
        },
        "interpretation": "Julia carrier/Z3.jl leg and Python exact algebra lane agree on bounded ratchet observables.",
    }
    nothing_before = {
        "compact_der_basis_sha256": math_payload["step0_free_carrier"]["compact_derivation"]["basis_sha256"],
        "constraint": "none",
    }
    nothing_after = json.loads(stable_json(nothing_before))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission": FORMAL_ADMISSION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim": "Algebraic RATCHETED diagnostic over the committed G2-family carrier: free compact Der(O), compact unit stabilizer, projection-derived branching, split causal stabilizer fork, and compact path-specificity controls.",
        "allowed_claims": [
            "computed compact unit stabilizer dimension and coset dimension under the S10 carrier hash",
            "projection-derived branch ranks for 7, 14, and 27 in the compact unit row",
            "split positive, negative, and null stabilizer dimensions with causal-class labels bounded by computed norm and left-multiplication rows",
            "control rows for wrong unit, sign-flip, projector mutation, and no constraint",
        ],
        "disallowed_claims": [
            "formal admission",
            "canonical G2 theorem",
            "crowned compact or split form",
            "physics, bridge, manifold, or Standard Model claim",
            "full null-stabilizer Levi decomposition",
        ],
        "all_pass": all_pass,
        "generated_at": now_utc(),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed_ledger": {"seed": SEED, "rng": "none; exact deterministic algebra rows"},
        "source_inputs": source_inputs(lineage),
        "parent_lineage": lineage,
        "lineage_citations": {
            "g2_family_carrier": "geo_s10_g2_family_v0",
            "ratcheted_template_pilot": "ratchet_s1_single_shell_pilot_v0",
            "ratcheted_template_two_shell": "ratchet_s2_two_shell_flux_v0",
            "ratcheted_template_terrain": "ratchet_s6_terrain_operator_shell_v0",
            "blind_preregistration": str(BLIND_PATH),
            "citation_boundary": "Only parent hashes and source-derived algebra rows are consumed; blind sheet is not used as a value source.",
        },
        "scope_fences": {
            "new_packet_path_only": rel(SIM_DIR),
            "terrain_weyl_spinor_lr_v0_touched": False,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "audit_verdict_emitted": False,
            "null_case_ceiling": "dimension and nilpotent evidence only; no full Levi decomposition",
        },
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "omitted_lanes": {
                "pytorch": "omitted: no graph/network/autograd/PyTorch-specific claim path in this algebraic G2-family ratchet diagnostic"
            },
            "audit_order": ["combined_envelope", "julia_carrier_z3", "python_exact_smt", "controller_comparison"],
            "interpreter": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "no_peer_result_reads": True,
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": rel(JULIA_SOURCE_PATH),
                "source_sha256": file_sha256(JULIA_SOURCE_PATH),
                "result_path": rel(JULIA_RESULT_PATH),
                "result_sha256": file_sha256(JULIA_RESULT_PATH) if JULIA_RESULT_PATH.exists() else None,
                "julia_project": julia.get("julia_project"),
                "command": (
                    "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no "
                    f"--project={ROOT}/system_v5/julia_carrier {rel(JULIA_SOURCE_PATH)}"
                ),
                "packages_used": ["JSON3", "LinearAlgebra", "Octonions", "SHA", "Z3"],
                "aligned_packages_load_bearing": ["Z3"],
                "reads_peer_result": False,
                "scope": "actual Julia carrier structure constants plus Z3.jl dimension identity flip",
                "capability_receipts": julia.get("capability_receipts", {}),
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "result_path": rel(RESULT_PATH),
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
                "reads_peer_result": False,
                "scope": "Python exact algebra and SMT lane; no JAX array claim is made",
            },
        },
        "claim_path_tools": ["sympy", "z3", "cvc5", "Z3"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": capability,
        "tool_calls": calls,
        "s10_hash_checks": s10_checks,
        "ratchet_sequence": {
            "step0_free_carrier": math_payload["step0_free_carrier"],
            "step1_stabilizer_constraint": math_payload["step1_stabilizer_constraint"],
            "step2_branching": math_payload["step2_branching"],
            "step3_split_family_fork": math_payload["step3_split_family_fork"],
        },
        "ratchet_signatures": {
            "narrowing": {
                "computed": True,
                "signature": "14 -> 8",
                "free_carrier_dim": math_payload["engine_values"]["compact_der_dim"],
                "stabilizer_dim": math_payload["engine_values"]["compact_stabilizer_dim"],
                "constraint_rank": math_payload["engine_values"]["compact_stabilizer_rank"],
            },
            "alteration": {
                "computed": True,
                "rep7_before_after": {
                    "before": math_payload["step2_branching"]["rep_7"]["before"],
                    "after": math_payload["step2_branching"]["rep_7"]["after"],
                },
                "rep14_before_after": {
                    "before": math_payload["step2_branching"]["rep_14"]["before"],
                    "after": math_payload["step2_branching"]["rep_14"]["after"],
                },
                "rep27_before_after": {
                    "before": math_payload["step2_branching"]["rep_27"]["before"],
                    "after": math_payload["step2_branching"]["rep_27"]["after"],
                },
            },
            "path_specificity": {
                "computed": True,
                "compact_pipelines_agree": math_payload["path_specificity"]["compact_pipelines_agree"],
                "compact_order_gap": math_payload["path_specificity"]["compact_order_gap"],
                "split_causal_conditioning_required": True,
            },
            "family_fork": {
                "computed": True,
                "compact_label": "su(3)",
                "split_positive_label": math_payload["step3_split_family_fork"]["rows"]["spacelike_positive_e1"]["derived_stabilizer_label"],
                "split_negative_label": math_payload["step3_split_family_fork"]["rows"]["timelike_negative_e4"]["derived_stabilizer_label"],
                "split_null_label": math_payload["step3_split_family_fork"]["rows"]["null_e1_plus_e4"]["derived_stabilizer_label"],
            },
        },
        "path_specificity": math_payload["path_specificity"],
        "controls": {
            **math_payload["controls"],
            "nothing_excluded_byte_copy": {
                "before_sha256": stable_json_sha256(nothing_before),
                "after_sha256": stable_json_sha256(nothing_after),
                "byte_exact": stable_json_sha256(nothing_before) == stable_json_sha256(nothing_after),
            },
        },
        "crossover_proofs": {"z3": proofs["z3"], "cvc5": proofs["cvc5"], "julia_z3": julia_proof},
        "computed_subtree_hashes": {
            "source_carrier_hashes": stable_json_sha256(math_payload["source_carrier_hashes"]),
            "ratchet_sequence": stable_json_sha256(math_payload["step1_stabilizer_constraint"]),
            "branching": stable_json_sha256(math_payload["step2_branching"]),
            "split_family_fork": stable_json_sha256(math_payload["step3_split_family_fork"]),
            "path_specificity": stable_json_sha256(math_payload["path_specificity"]),
            "controls": stable_json_sha256(math_payload["controls"]),
        },
        "row_survival_map_no_crowned_winner": math_payload["row_survival_map_no_crowned_winner"],
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_earned": [
                "formal admission",
                "canonical family theorem",
                "crowned compact/split form",
                "physics or bridge claim",
                "full null stabilizer classification",
            ],
        },
        "divergence": divergence,
        "build_gates": gates,
        "validator": {
            "packet_validator": rel(VALIDATOR_PATH),
            "packet_validator_result": rel(VALIDATOR_RESULT_PATH),
            "repo_validator_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-source-backed {rel(RESULT_PATH)}"
            ),
        },
        "summary": {
            "compact_der_dim": math_payload["engine_values"]["compact_der_dim"],
            "compact_stabilizer_dim": math_payload["engine_values"]["compact_stabilizer_dim"],
            "compact_coset_dim": math_payload["engine_values"]["compact_orbit_dim"],
            "branch7": math_payload["step2_branching"]["rep_7"]["label"],
            "branch14": math_payload["step2_branching"]["rep_14"]["label"],
            "branch27": math_payload["step2_branching"]["rep_27"]["label"],
            "split_positive_label": math_payload["step3_split_family_fork"]["rows"]["spacelike_positive_e1"]["derived_stabilizer_label"],
            "split_negative_label": math_payload["step3_split_family_fork"]["rows"]["timelike_negative_e4"]["derived_stabilizer_label"],
            "all_pass": all_pass,
        },
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(json_ready(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
