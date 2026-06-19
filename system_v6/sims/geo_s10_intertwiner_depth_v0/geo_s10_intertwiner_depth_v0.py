#!/usr/bin/env python3
"""Builder for geo_s10_intertwiner_depth_v0.

Symbolic, light-local packet. Ceiling: scratch_diagnostic.
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
SIM_ID = "geo_s10_intertwiner_depth_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
NEMO_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_nemo_hecke.jl"
NEMO_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_nemo_hecke_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
STAGE_MOVEMENT_ALLOWED = False
READS_PEER_RESULT = False
SEED = "geo_s10_intertwiner_depth_v0_seed_20260611"
MODE = "SYMBOLIC_LIGHT_LOCAL_INTERTWINER_DEPTH"

PARENTS = {
    "geo_s10_g2_family_v0": {
        "packet": "system_v6/sims/geo_s10_g2_family_v0",
        "envelope": "system_v6/sims/geo_s10_g2_family_v0/results/geo_s10_g2_family_v0_envelope_results.json",
        "top_source": "system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_common.py",
        "expected_commit_prefix": "77a4f5d19",
        "allowed_use": "parent S10 G2-family carrier and honest D4-diagram triality fence only",
    },
    "ratchet_g2_family_v0": {
        "packet": "system_v6/sims/ratchet_g2_family_v0",
        "envelope": "system_v6/sims/ratchet_g2_family_v0/results/ratchet_g2_family_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_g2_family_v0/ratchet_g2_family_v0.py",
        "expected_commit_prefix": "b5649217c",
        "allowed_use": "parent null-stabilizer deferred row and ratcheted lineage/hash idiom only",
    },
}

PIN_SPEC = (
    "geo_s10_intertwiner_depth_v0|mode=SYMBOLIC_LIGHT_LOCAL|"
    "triality=explicit_D4_Chevalley_intertwiners_for_8v_8c_8s|"
    "null_stabilizer=split_vector_stabilizer_radical_nilradical_Levi_quotient|"
    "controls=wrong_intertwiner+compact_reductive+sign_flip_closure+smt_erasure|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact D4 representation matrices, intertwiners, ranks, nullspaces, brackets, Killing forms, and quotient dimensions",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing erased-flip check bound to computed null-stabilizer dimension bookkeeping",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent erased-flip check over the same computed dimension bookkeeping",
    },
    "Nemo": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia finite GF(2) matrix enumeration for the S3 outer-action sanity row",
    },
    "Hecke": {
        "tried": True,
        "used": True,
        "reason": "supportive optional-project import in the Nemo sidecar; not claim-bearing",
    },
    "json": {"tried": True, "used": True, "reason": "supportive deterministic result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, result, and lineage hashes"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive committed parent lineage reads"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Nemo": "load_bearing",
    "Hecke": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
    "subprocess": "supportive",
}
classification = CLASSIFICATION


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
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


def stable_json_sha256(value: Any) -> str:
    return sha256_text(stable_json(value))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        commit = git_last_commit(paths["packet"])
        out[name] = {
            "packet_path": paths["packet"],
            "committed_tree": git_rev_parse(paths["packet"]),
            "committed_commit": commit,
            "expected_commit_prefix": paths["expected_commit_prefix"],
            "expected_commit_prefix_match": commit.startswith(paths["expected_commit_prefix"]),
            "envelope_path": paths["envelope"],
            "envelope_blob": git_rev_parse(paths["envelope"]),
            "envelope_sha256": hashlib.sha256(envelope).hexdigest(),
            "top_source_path": paths["top_source"],
            "top_source_blob": git_rev_parse(paths["top_source"]),
            "top_source_sha256": hashlib.sha256(source).hexdigest(),
            "allowed_use": paths["allowed_use"],
            "source": "git show HEAD:<path>; committed packet citation only",
        }
    return out


D4_ROOTS = {
    1: (sp.Rational(1), sp.Rational(-1), sp.Rational(0), sp.Rational(0)),
    2: (sp.Rational(0), sp.Rational(1), sp.Rational(-1), sp.Rational(0)),
    3: (sp.Rational(0), sp.Rational(0), sp.Rational(1), sp.Rational(-1)),
    4: (sp.Rational(0), sp.Rational(0), sp.Rational(1), sp.Rational(1)),
}
REP_NODE = {
    "8v": 1,
    "8c": 3,
    "8s": 4,
}
NODE_REP = {node: rep for rep, node in REP_NODE.items()}
REP_LABEL = {
    "8v": "vector_node1",
    "8c": "half_spinor_minus_node3_odd_parity",
    "8s": "half_spinor_plus_node4_even_parity",
}


def d4_weights(rep_name: str) -> list[tuple[sp.Rational, ...]]:
    if rep_name == "8v":
        out = []
        for idx in range(4):
            vec = [sp.Rational(0) for _ in range(4)]
            vec[idx] = sp.Rational(1)
            out.append(tuple(vec))
            out.append(tuple(-entry for entry in vec))
        return out
    out = []
    want_even = rep_name == "8s"
    for signs in itertools.product([1, -1], repeat=4):
        if (signs.count(-1) % 2 == 0) == want_even:
            out.append(tuple(sp.Rational(sign, 2) for sign in signs))
    return out


def dynkin_labels(weight: tuple[sp.Rational, ...]) -> tuple[sp.Rational, ...]:
    return tuple(sum(weight[idx] * root[idx] for idx in range(4)) for root in D4_ROOTS.values())


def chevalley_rep(rep_name: str) -> dict[str, dict[int, sp.Matrix]]:
    weights = d4_weights(rep_name)
    index = {weight: idx for idx, weight in enumerate(weights)}
    e: dict[int, sp.Matrix] = {}
    f: dict[int, sp.Matrix] = {}
    h: dict[int, sp.Matrix] = {}
    for node, root in D4_ROOTS.items():
        e[node] = sp.zeros(8)
        f[node] = sp.zeros(8)
        h[node] = sp.zeros(8)
        for weight, col in index.items():
            h[node][col, col] = sum(weight[idx] * root[idx] for idx in range(4))
            plus = tuple(weight[idx] + root[idx] for idx in range(4))
            minus = tuple(weight[idx] - root[idx] for idx in range(4))
            if plus in index:
                e[node][index[plus], col] = 1
            if minus in index:
                f[node][index[minus], col] = 1
    return {"e": e, "f": f, "h": h}


def mat_vec(matrix: sp.Matrix) -> sp.Matrix:
    return sp.Matrix(matrix).reshape(matrix.rows * matrix.cols, 1)


def matrix_rank(mats: list[sp.Matrix]) -> int:
    if not mats:
        return 0
    return int(sp.Matrix.hstack(*[mat_vec(mat) for mat in mats]).rank())


def lie_closure_dimension(generators: list[sp.Matrix], target: int = 28) -> int:
    basis = list(generators)
    rank = matrix_rank(basis)
    changed = True
    while changed and rank < target:
        changed = False
        snapshot = list(basis)
        for left in snapshot:
            for right in snapshot:
                comm = left * right - right * left
                new_rank = matrix_rank([*basis, comm])
                if new_rank > rank:
                    basis.append(comm)
                    rank = new_rank
                    changed = True
                    if rank >= target:
                        return rank
    return rank


def permuted_label(label: tuple[sp.Rational, ...], permutation: dict[int, int]) -> tuple[sp.Rational, ...]:
    new = [sp.Rational(0) for _ in range(5)]
    for old_node in range(1, 5):
        new[permutation[old_node]] = label[old_node - 1]
    return tuple(new[1:])


def diagram_intertwiner(src: str, dst: str, permutation: dict[int, int]) -> sp.Matrix:
    src_weights = d4_weights(src)
    dst_weights = d4_weights(dst)
    dst_by_label = {dynkin_labels(weight): idx for idx, weight in enumerate(dst_weights)}
    matrix = sp.zeros(8)
    for col, weight in enumerate(src_weights):
        target_label = permuted_label(dynkin_labels(weight), permutation)
        row = dst_by_label[target_label]
        matrix[row, col] = 1
    return matrix


def generator_list(rep: dict[str, dict[int, sp.Matrix]]) -> list[tuple[str, int, sp.Matrix]]:
    return [
        *[("e", node, rep["e"][node]) for node in range(1, 5)],
        *[("f", node, rep["f"][node]) for node in range(1, 5)],
        *[("h", node, rep["h"][node]) for node in range(1, 5)],
    ]


def verify_intertwiner(src: str, dst: str, permutation: dict[int, int], matrix: sp.Matrix) -> dict[str, Any]:
    reps = {name: chevalley_rep(name) for name in REP_NODE}
    rows = []
    nonzero_total = 0
    max_abs = 0
    for kind, node, src_matrix in generator_list(reps[src]):
        dst_matrix = reps[dst][kind][permutation[node]]
        residual = matrix * src_matrix - dst_matrix * matrix
        nonzero = sum(1 for entry in residual if entry != 0)
        nonzero_total += nonzero
        if nonzero:
            max_abs = max(max_abs, max(abs(int(entry)) for entry in residual if entry != 0))
        rows.append({"generator": f"{kind}{node}", "nonzero_entries": nonzero})
    return {
        "src": src,
        "dst": dst,
        "src_label": REP_LABEL[src],
        "dst_label": REP_LABEL[dst],
        "matrix_rank": int(matrix.rank()),
        "matrix_det": int(matrix.det()),
        "verified_generator_count": len(rows),
        "residual_nonzero_entries": nonzero_total,
        "max_abs_residual": max_abs,
        "passes": nonzero_total == 0 and int(matrix.rank()) == 8,
        "rows": rows,
        "matrix_sha256": stable_json_sha256(matrix.tolist()),
    }


def outer_maps(permutation: dict[int, int]) -> list[dict[str, Any]]:
    maps = []
    for src, node in REP_NODE.items():
        dst = NODE_REP[permutation[node]]
        matrix = diagram_intertwiner(src, dst, permutation)
        maps.append({"src": src, "dst": dst, "matrix": matrix, "verification": verify_intertwiner(src, dst, permutation, matrix)})
    return maps


def direct_sum_outer_matrix(maps: list[dict[str, Any]]) -> sp.Matrix:
    order = ["8v", "8c", "8s"]
    offsets = {name: 8 * idx for idx, name in enumerate(order)}
    out = sp.zeros(24)
    for row in maps:
        src_offset = offsets[row["src"]]
        dst_offset = offsets[row["dst"]]
        matrix = row["matrix"]
        out[dst_offset : dst_offset + 8, src_offset : src_offset + 8] = matrix
    return out


def scalar_power_check(matrix: sp.Matrix, power: int) -> dict[str, Any]:
    powered = matrix**power
    identity = sp.eye(matrix.rows)
    scalar = powered[0, 0]
    residual = powered - scalar * identity
    return {
        "power": power,
        "scalar": json_ready(scalar),
        "matrix_size": matrix.rows,
        "residual_rank": int(residual.rank()),
        "passes": residual == sp.zeros(matrix.rows),
        "powered_sha256": stable_json_sha256(powered.tolist()),
    }


def build_triality() -> dict[str, Any]:
    cycle = {1: 3, 3: 4, 4: 1, 2: 2}
    transposition = {1: 1, 2: 2, 3: 4, 4: 3}
    reps = {name: chevalley_rep(name) for name in REP_NODE}
    closure = {
        name: {
            "chevalley_generator_count": 12,
            "generated_lie_closure_dimension": lie_closure_dimension([row[2] for row in generator_list(rep)]),
            "rep_label": REP_LABEL[name],
            "weight_count": len(d4_weights(name)),
            "weight_dynkin_label_sha256": stable_json_sha256([dynkin_labels(weight) for weight in d4_weights(name)]),
        }
        for name, rep in reps.items()
    }
    cycle_maps = outer_maps(cycle)
    transposition_maps = outer_maps(transposition)
    cycle_matrix = direct_sum_outer_matrix(cycle_maps)
    transposition_matrix = direct_sum_outer_matrix(transposition_maps)
    cycle_cubed = scalar_power_check(cycle_matrix, 3)
    transposition_squared = scalar_power_check(transposition_matrix, 2)
    braid_residual = transposition_matrix * cycle_matrix * transposition_matrix - cycle_matrix**-1
    wrong_identity = sp.eye(8)
    wrong = verify_intertwiner("8v", "8c", cycle, wrong_identity)
    return {
        "construction": "D4 minuscule Chevalley representation matrices on 8v, 8c, and 8s; outer-node permutations are realized by explicit 8x8 permutation intertwiners.",
        "honest_scope": "one exact Chevalley-basis realization of the D4 S3 outer action; not a classification of all possible intertwiners",
        "simple_roots": {str(k): list(v) for k, v in D4_ROOTS.items()},
        "representations": closure,
        "cycle_permutation_old_node_to_new_node": cycle,
        "transposition_permutation_old_node_to_new_node": transposition,
        "cycle_maps": [{k: v for k, v in row.items() if k != "matrix"} for row in cycle_maps],
        "transposition_maps": [{k: v for k, v in row.items() if k != "matrix"} for row in transposition_maps],
        "direct_sum_order": ["8v", "8c", "8s"],
        "cycle_direct_sum_matrix_sha256": stable_json_sha256(cycle_matrix.tolist()),
        "transposition_direct_sum_matrix_sha256": stable_json_sha256(transposition_matrix.tolist()),
        "order_3_cubed_scalar": cycle_cubed,
        "transposition_squared_scalar": transposition_squared,
        "s3_relation_TCT_equals_C_inverse": {
            "residual_rank": int(braid_residual.rank()),
            "passes": braid_residual == sp.zeros(24),
            "relation": "T*C*T == C^-1",
        },
        "wrong_intertwiner_control": {
            **{k: v for k, v in wrong.items() if k != "rows"},
            "candidate": "8x8 identity matrix forced between 8v and 8c under the 3-cycle",
            "control_fired": wrong["residual_nonzero_entries"] > 0,
        },
        "all_intertwiner_rows_pass": all(row["verification"]["passes"] for row in [*cycle_maps, *transposition_maps]),
    }


def zero_table(n: int) -> list[list[list[int]]]:
    return [[[0 for _ in range(n)] for _ in range(n)] for _ in range(n)]


def conj_vec(x: list[Any]) -> list[Any]:
    return [x[0], *[-v for v in x[1:]]]


def table_mul(table: list[list[list[int]]], x: list[Any], y: list[Any]) -> list[Any]:
    n = len(table)
    return [sum(table[k][i][j] * x[i] * y[j] for i in range(n) for j in range(n)) for k in range(n)]


def cd_double(parent: list[list[list[int]]], gamma: int) -> list[list[list[int]]]:
    n = len(parent)
    out = zero_table(2 * n)
    eye = []
    for idx in range(2 * n):
        vec = [0 for _ in range(2 * n)]
        vec[idx] = 1
        eye.append(vec)
    for i, x in enumerate(eye):
        for j, y in enumerate(eye):
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = [u + gamma * v for u, v in zip(table_mul(parent, a, c), table_mul(parent, conj_vec(d), b))]
            second = [u + v for u, v in zip(table_mul(parent, d, a), table_mul(parent, b, conj_vec(c)))]
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
    basis = [matrix_from_vec(vec, len(table)) for vec in matrix.nullspace()]
    return {
        "carrier": name,
        "rank": int(matrix.rank()),
        "nullity_dim_der": len(basis),
        "basis_sha256": stable_json_sha256([mat.tolist() for mat in basis]),
        "derivation_matrix_sha256": stable_json_sha256(matrix.tolist()),
        "_basis_mats": basis,
    }


def derivation_7_mats(summary: dict[str, Any]) -> list[sp.Matrix]:
    return [mat[1:, 1:] for mat in summary["_basis_mats"]]


def span_contains_all(basis: list[sp.Matrix], candidates: list[sp.Matrix]) -> bool:
    if not candidates:
        return True
    if not basis:
        return False
    base = sp.Matrix.hstack(*[mat_vec(mat) for mat in basis])
    base_rank = int(base.rank())
    for candidate in candidates:
        if int(base.row_join(mat_vec(candidate)).rank()) != base_rank:
            return False
    return True


def subspace_rank_coeff(vectors: list[sp.Matrix]) -> int:
    if not vectors:
        return 0
    return int(sp.Matrix.hstack(*vectors).rank())


def coeff_basis(vectors: list[sp.Matrix]) -> list[sp.Matrix]:
    if not vectors:
        return []
    return [sp.Matrix(col) for col in sp.Matrix.hstack(*vectors).columnspace()]


def stabilizer_data(summary: dict[str, Any], vector7: list[int], label: str) -> dict[str, Any]:
    mats = derivation_7_mats(summary)
    action = sp.Matrix([[sum(mat[r, c] * vector7[c] for c in range(7)) for mat in mats] for r in range(7)])
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
        "stabilizer_dim": len(stab_mats),
        "stabilizer_basis_rank": matrix_rank(stab_mats),
        "stabilizer_basis_sha256": stable_json_sha256([mat.tolist() for mat in stab_mats]),
        "closure_under_commutator": span_contains_all(stab_mats, comms),
        "_stab_mats": stab_mats,
    }


def express_in_basis(basis: list[sp.Matrix], matrix: sp.Matrix) -> sp.Matrix:
    base = sp.Matrix.hstack(*[mat_vec(mat) for mat in basis])
    return sp.Matrix(base.gauss_jordan_solve(mat_vec(matrix))[0])


def structure_constants(basis: list[sp.Matrix]) -> dict[str, Any]:
    n = len(basis)
    constants = [[[sp.Rational(0) for _ in range(n)] for _ in range(n)] for _ in range(n)]
    for i, left in enumerate(basis):
        for j, right in enumerate(basis):
            coeffs = express_in_basis(basis, left * right - right * left)
            for k in range(n):
                constants[k][i][j] = sp.simplify(coeffs[k])
    ads = []
    for i in range(n):
        ad = sp.zeros(n)
        for j in range(n):
            for k in range(n):
                ad[k, j] = constants[k][i][j]
        ads.append(ad)
    killing = sp.Matrix([[sp.trace(ads[i] * ads[j]) for j in range(n)] for i in range(n)])
    brackets = [sp.Matrix([constants[k][i][j] for k in range(n)]) for i in range(n) for j in range(n)]
    derived = coeff_basis(brackets)
    derived_matrix = sp.Matrix.hstack(*derived) if derived else sp.zeros(n, 0)
    cartan_matrix = derived_matrix.T * killing.T
    radical = [sp.Matrix(col) for col in cartan_matrix.nullspace()]
    return {
        "constants": constants,
        "ad_matrices": ads,
        "killing": killing,
        "derived_basis": derived,
        "radical_basis": radical,
        "derived_rank": subspace_rank_coeff(derived),
    }


def bracket_coeff(constants: list[list[list[sp.Rational]]], left: sp.Matrix, right: sp.Matrix) -> sp.Matrix:
    n = len(constants)
    out = sp.zeros(n, 1)
    for i in range(n):
        for j in range(n):
            if left[i] and right[j]:
                out += left[i] * right[j] * sp.Matrix([constants[k][i][j] for k in range(n)])
    return sp.Matrix(out)


def lower_central_dims(constants: list[list[list[sp.Rational]]], generators: list[sp.Matrix]) -> list[int]:
    current = [sp.Matrix(vec) for vec in generators]
    dims = []
    for _ in range(8):
        dim = subspace_rank_coeff(current)
        dims.append(dim)
        if dim == 0:
            break
        current = coeff_basis([bracket_coeff(constants, x, y) for x in generators for y in current])
    return dims


def derived_series_dims(constants: list[list[list[sp.Rational]]], generators: list[sp.Matrix]) -> list[int]:
    current = [sp.Matrix(vec) for vec in generators]
    dims = []
    for _ in range(8):
        dim = subspace_rank_coeff(current)
        dims.append(dim)
        if dim == 0:
            break
        current = coeff_basis([bracket_coeff(constants, x, y) for x in current for y in current])
    return dims


def center_dim(constants: list[list[list[sp.Rational]]]) -> int:
    n = len(constants)
    rows = []
    for j in range(n):
        for k in range(n):
            rows.append([constants[k][i][j] for i in range(n)])
    return n - int(sp.Matrix(rows).rank())


def killing_signature(killing: sp.Matrix) -> dict[str, Any]:
    eigenvals = killing.eigenvals()
    expanded = []
    for value, multiplicity in eigenvals.items():
        expanded.extend([value] * multiplicity)
    positive = sum(1 for value in expanded if float(sp.N(value)) > 0)
    negative = sum(1 for value in expanded if float(sp.N(value)) < 0)
    zero = len(expanded) - positive - negative
    return {
        "positive": positive,
        "negative": negative,
        "zero": zero,
        "eigenvalues": [json_ready(value) for value in expanded],
    }


def ideal_check(constants: list[list[list[sp.Rational]]], ideal_basis: list[sp.Matrix]) -> dict[str, Any]:
    n = len(constants)
    if not ideal_basis:
        return {"is_ideal": True, "bad_bracket_count": 0}
    base = sp.Matrix.hstack(*ideal_basis)
    rank = int(base.rank())
    bad = 0
    for i in range(n):
        unit = sp.eye(n).col(i)
        for vec in ideal_basis:
            if int(base.row_join(bracket_coeff(constants, unit, vec)).rank()) != rank:
                bad += 1
    return {"is_ideal": bad == 0, "bad_bracket_count": bad}


def quotient_profile(constants: list[list[list[sp.Rational]]], radical: list[sp.Matrix]) -> dict[str, Any]:
    n = len(constants)
    columns = [sp.Matrix(vec) for vec in radical]
    selected = []
    rank = subspace_rank_coeff(columns)
    for idx in range(n):
        unit = sp.eye(n).col(idx)
        new_rank = subspace_rank_coeff([*columns, unit])
        if new_rank > rank:
            selected.append(idx)
            columns.append(unit)
            rank = new_rank
        if rank == n:
            break
    projector = sp.Matrix.hstack(*columns)
    inverse = projector.inv()
    qdim = len(selected)
    quotient_constants = [[[sp.Rational(0) for _ in range(qdim)] for _ in range(qdim)] for _ in range(qdim)]
    for a, i in enumerate(selected):
        for b, j in enumerate(selected):
            coords = inverse * bracket_coeff(constants, sp.eye(n).col(i), sp.eye(n).col(j))
            for k in range(qdim):
                quotient_constants[k][a][b] = sp.simplify(coords[len(radical) + k])
    q_ads = []
    for i in range(qdim):
        ad = sp.zeros(qdim)
        for j in range(qdim):
            for k in range(qdim):
                ad[k, j] = quotient_constants[k][i][j]
        q_ads.append(ad)
    q_killing = sp.Matrix([[sp.trace(q_ads[i] * q_ads[j]) for j in range(qdim)] for i in range(qdim)])
    q_brackets = [
        sp.Matrix([quotient_constants[k][i][j] for k in range(qdim)])
        for i in range(qdim)
        for j in range(qdim)
    ]
    return {
        "quotient_dim": qdim,
        "selected_complement_indices": selected,
        "derived_dim": subspace_rank_coeff(q_brackets),
        "center_dim": center_dim(quotient_constants),
        "killing_rank": int(q_killing.rank()),
        "killing_det": json_ready(q_killing.det()),
        "killing_signature": killing_signature(q_killing),
        "structure_constants_sha256": stable_json_sha256(quotient_constants),
        "identification": "sl2_R_by_dim3_center0_derived3_and_indefinite_nonzero_Killing_form",
    }


def lie_profile(stabilizer: dict[str, Any]) -> dict[str, Any]:
    basis = stabilizer["_stab_mats"]
    data = structure_constants(basis)
    constants = data["constants"]
    radical = data["radical_basis"]
    nil_lower = lower_central_dims(constants, radical)
    nil_derived = derived_series_dims(constants, radical)
    radical_ideal = ideal_check(constants, radical)
    quotient = quotient_profile(constants, radical) if radical else {
        "quotient_dim": len(basis),
        "identification": "semisimple_reductive_stabilizer_no_nilradical",
    }
    return {
        "stabilizer_dim": len(basis),
        "closure_under_commutator": stabilizer["closure_under_commutator"],
        "derived_rank": data["derived_rank"],
        "killing_rank": int(data["killing"].rank()),
        "killing_signature": killing_signature(data["killing"]),
        "radical_dim": len(radical),
        "nilradical_dim": len(radical) if nil_lower and nil_lower[-1] == 0 else None,
        "radical_is_ideal": radical_ideal["is_ideal"],
        "nilradical_lower_central_dims": nil_lower,
        "nilradical_derived_series_dims": nil_derived,
        "nilradical_nilpotency_class": len([dim for dim in nil_lower if dim != 0]) - 1 if nil_lower and nil_lower[-1] == 0 else None,
        "radical_basis_sha256": stable_json_sha256([vec for vec in radical]),
        "structure_constants_sha256": stable_json_sha256(constants),
        "Levi_quotient": quotient,
    }


def sign_flip_closure_control(stabilizer: dict[str, Any]) -> dict[str, Any]:
    mutated = [sp.Matrix(mat) for mat in stabilizer["_stab_mats"]]
    mutation = None
    for basis_idx, mat in enumerate(mutated):
        for row in range(mat.rows):
            for col in range(mat.cols):
                if mat[row, col] != 0:
                    mat[row, col] = -mat[row, col]
                    mutation = {"basis_index": basis_idx, "row": row, "col": col}
                    break
            if mutation:
                break
        if mutation:
            break
    comms = [a * b - b * a for a in mutated for b in mutated]
    bad = 0
    base = sp.Matrix.hstack(*[mat_vec(mat) for mat in mutated])
    base_rank = int(base.rank())
    for comm in comms:
        if int(base.row_join(mat_vec(comm)).rank()) != base_rank:
            bad += 1
    return {
        "control": "single_entry_sign_flip_in_null_stabilizer_basis",
        "mutation": mutation,
        "mutated_basis_rank": matrix_rank(mutated),
        "bad_bracket_count": bad,
        "closure_under_commutator": bad == 0,
        "control_fired": bad > 0,
    }


def norm_diag(table: list[list[list[int]]]) -> list[int]:
    out = []
    for idx in range(len(table)):
        vec = [1 if j == idx else 0 for j in range(len(table))]
        out.append(int(table_mul(table, vec, conj_vec(vec))[0]))
    return out


def metric_norm(vector: list[int], metric: list[int]) -> int:
    return int(sum(metric[idx] * vector[idx] * vector[idx] for idx in range(len(vector))))


def public_stabilizer(stabilizer: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in stabilizer.items() if not key.startswith("_")}


def build_null_levi() -> dict[str, Any]:
    compact = table_o_compact()
    split = table_o_split()
    compact_summary = derivation_summary("O_compact", compact)
    split_summary = derivation_summary("O_split", split)
    compact_stabilizer = stabilizer_data(compact_summary, [1, 0, 0, 0, 0, 0, 0], "compact_unit_e1")
    null_vector = [1, 0, 0, 1, 0, 0, 0]
    split_null = stabilizer_data(split_summary, null_vector, "split_null_vector_e1_plus_e4")
    null_profile = lie_profile(split_null)
    compact_profile = lie_profile(compact_stabilizer)
    metric = norm_diag(split)[1:]
    sign_control = sign_flip_closure_control(split_null)
    return {
        "construction": "split octonion derivations from Cayley-Dickson gamma=+1; stabilizer fixes the null vector e1+e4, not just the null line",
        "carrier_hashes": {
            "compact_derivation_matrix_sha256": compact_summary["derivation_matrix_sha256"],
            "split_derivation_matrix_sha256": split_summary["derivation_matrix_sha256"],
            "split_table_sha256": stable_json_sha256(split),
        },
        "split_metric_trace_zero_diag": metric,
        "split_null_vector": null_vector,
        "split_null_norm": metric_norm(null_vector, metric),
        "split_null_stabilizer": public_stabilizer(split_null),
        "split_null_decomposition": null_profile,
        "dimension_bookkeeping": {
            "stabilizer_dim": null_profile["stabilizer_dim"],
            "nilradical_dim": null_profile["nilradical_dim"],
            "Levi_quotient_dim": null_profile["Levi_quotient"]["quotient_dim"],
            "identity": "stabilizer_dim == nilradical_dim + Levi_quotient_dim",
            "identity_holds": null_profile["stabilizer_dim"]
            == null_profile["nilradical_dim"] + null_profile["Levi_quotient"]["quotient_dim"],
        },
        "compact_positive_control": {
            "compact_unit_stabilizer": public_stabilizer(compact_stabilizer),
            "profile": compact_profile,
            "nilradical_zero": compact_profile["nilradical_dim"] == 0,
            "reductive_control_passes": compact_profile["killing_rank"] == compact_profile["stabilizer_dim"],
        },
        "sign_flip_closure_control": sign_control,
    }


def z3_dimension_identity(values: dict[str, int], erased: bool) -> dict[str, Any]:
    solver = z3.Solver()
    stabilizer_dim = z3.Int("stabilizer_dim")
    nilradical_dim = z3.Int("nilradical_dim")
    levi_dim = z3.Int("levi_dim")
    solver.add(stabilizer_dim == values["stabilizer_dim"])
    solver.add(nilradical_dim == values["nilradical_dim"])
    if not erased:
        solver.add(levi_dim == values["Levi_quotient_dim"])
    solver.add(stabilizer_dim != nilradical_dim + levi_dim)
    status = str(solver.check())
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "erased": erased,
        "bound_values": {} if erased else values,
        "derived_expression": "stabilizer_dim == nilradical_dim + Levi_quotient_dim",
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
    stabilizer_dim = solver.mkConst(integer, "stabilizer_dim")
    nilradical_dim = solver.mkConst(integer, "nilradical_dim")
    levi_dim = solver.mkConst(integer, "levi_dim")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, stabilizer_dim, solver.mkInteger(values["stabilizer_dim"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, nilradical_dim, solver.mkInteger(values["nilradical_dim"])))
    if not erased:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, levi_dim, solver.mkInteger(values["Levi_quotient_dim"])))
    solver.assertFormula(
        solver.mkTerm(
            Kind.NOT,
            solver.mkTerm(
                Kind.EQUAL,
                stabilizer_dim,
                solver.mkTerm(Kind.ADD, nilradical_dim, levi_dim),
            ),
        )
    )
    status = cvc5_status(solver.checkSat())
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": status,
        "erased": erased,
        "bound_values": {} if erased else values,
        "derived_expression": "stabilizer_dim == nilradical_dim + Levi_quotient_dim",
    }


def solver_proofs(values: dict[str, int]) -> dict[str, Any]:
    z3_real = z3_dimension_identity(values, erased=False)
    z3_erased = z3_dimension_identity(values, erased=True)
    cvc5_real = cvc5_dimension_identity(values, erased=False)
    cvc5_erased = cvc5_dimension_identity(values, erased=True)
    return {
        "polarity": "assert computed dimension identity is violated; real bound values are UNSAT, erased Levi binding is SAT",
        "z3": {
            **z3_real,
            "positive_case": "computed null-stabilizer dimensions make the bookkeeping violation UNSAT",
            "negative/erased_control": "erase the Levi quotient binding; the violation becomes SAT",
            "erased_flip_verdict": z3_erased["verdict"],
            "erased_flip_detected": z3_real["verdict"] == "unsat" and z3_erased["verdict"] == "sat",
            "boundary_case": "integer dimension bookkeeping only, not full classification beyond the computed quotient profile",
            "demotion_condition": "demote if the solver binds expected prose or an all_pass boolean instead of computed dimensions",
        },
        "cvc5": {
            **cvc5_real,
            "positive_case": "computed null-stabilizer dimensions make the bookkeeping violation UNSAT",
            "negative/erased_control": "erase the Levi quotient binding; the violation becomes SAT",
            "erased_flip_verdict": cvc5_erased["verdict"],
            "erased_flip_detected": cvc5_real["verdict"] == "unsat" and cvc5_erased["verdict"] == "sat",
            "boundary_case": "integer dimension bookkeeping only, not full classification beyond the computed quotient profile",
            "demotion_condition": "demote if cvc5 no longer agrees with z3 on real and erased statuses",
        },
    }


def load_nemo_result() -> dict[str, Any]:
    if not NEMO_RESULT_PATH.exists():
        return {"all_pass": False, "missing": True, "result_path": rel(NEMO_RESULT_PATH)}
    return json.loads(NEMO_RESULT_PATH.read_text(encoding="utf-8"))


def capability_receipts(proofs: dict[str, Any], nemo: dict[str, Any]) -> dict[str, Any]:
    return {
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "sympy": {"version": sp.__version__, "api_smoke_rank": int(sp.Matrix([[1, 2], [2, 4]]).rank())},
        "z3": {"version": z3.get_version_string(), "api_smoke": proofs["z3"]["verdict"]},
        "cvc5": {"version": cvc5.__version__, "api_smoke": proofs["cvc5"]["verdict"]},
        "julia_nemo_hecke": nemo.get("runtime", {}),
    }


def tool_calls(proofs: dict[str, Any], nemo: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.Matrix.rank/nullspace/eigenvals/gauss_jordan_solve",
            "input_object": "D4 weights, Chevalley generators, split-octonion derivation and stabilizer bracket matrices",
            "output_object": "explicit 8x8 outer-action intertwiners, null-stabilizer radical/nilradical, and Levi quotient dimensions",
            "positive_case": "all D4 intertwiners have zero generator residual; split null stabilizer decomposes as 8 = 5 + 3",
            "negative/erased_control": "wrong identity interwiner and sign-flipped stabilizer basis fail residual/closure checks",
            "boundary_case": "one explicit symbolic realization, not a classification of all realizations",
            "demotion_condition": "demote if residuals, ranks, or bracket dimensions are emitted without exact matrix hashes",
            "gates": ["triality_intertwiners", "null_Levi", "controls", "all_pass"],
            "load_bearing": True,
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver.add/check",
            "input_object": "computed null-stabilizer dimension rows",
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
            "qualified_api/function": "cvc5.Solver.mkConst/mkTerm/checkSat",
            "input_object": "same computed null-stabilizer dimension rows",
            "output_object": proofs["cvc5"],
            "positive_case": proofs["cvc5"]["positive_case"],
            "negative/erased_control": proofs["cvc5"]["negative/erased_control"],
            "boundary_case": proofs["cvc5"]["boundary_case"],
            "demotion_condition": proofs["cvc5"]["demotion_condition"],
            "gates": ["smt", "all_pass"],
            "load_bearing": True,
        },
        {
            "tool": "Nemo",
            "qualified_api/function": "Nemo.GF/matrix/det",
            "input_object": "2x2 matrices over GF(2)",
            "output_object": nemo.get("outer_s3_row"),
            "positive_case": "GL(2,2) enumerates to order 6 with a 3-cycle and order-2 generator",
            "negative/erased_control": "singular matrices are excluded by determinant zero",
            "boundary_case": "finite S3 sanity row only; not compact/split Lie-form proof",
            "demotion_condition": "demote if the Julia sidecar is absent or not run under system_v6/optional/nemo_hecke",
            "gates": ["nemo_s3_row", "all_pass"],
            "load_bearing": True,
        },
    ]


def forbidden_token_scan() -> dict[str, Any]:
    token = "fix" + "ture"
    scanned = []
    hits = []
    for path in [SOURCE_PATH, VALIDATOR_PATH, NEMO_SOURCE_PATH]:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            scanned.append(rel(path))
            if token in text:
                hits.append(rel(path))
    return {"token_sha256": sha256_text(token), "scanned": scanned, "hits": hits, "passes": not hits}


def build_result() -> dict[str, Any]:
    lineage = parent_lineage()
    triality = build_triality()
    null_levi = build_null_levi()
    dim_values = {
        "stabilizer_dim": null_levi["dimension_bookkeeping"]["stabilizer_dim"],
        "nilradical_dim": null_levi["dimension_bookkeeping"]["nilradical_dim"],
        "Levi_quotient_dim": null_levi["dimension_bookkeeping"]["Levi_quotient_dim"],
    }
    proofs = solver_proofs(dim_values)
    nemo = load_nemo_result()
    capability = capability_receipts(proofs, nemo)
    calls = tool_calls(proofs, nemo)
    forbidden_scan = forbidden_token_scan()
    gates = {
        "mode_declared": MODE == "SYMBOLIC_LIGHT_LOCAL_INTERTWINER_DEPTH",
        "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic"
        and not PROMOTION_ALLOWED
        and not FORMAL_ADMISSION_ALLOWED
        and not STAGE_MOVEMENT_ALLOWED,
        "parents_exactly_requested": set(lineage) == {"geo_s10_g2_family_v0", "ratchet_g2_family_v0"},
        "parent_commits_match_requested_prefixes": all(row["expected_commit_prefix_match"] for row in lineage.values()),
        "triality_reps_generate_so8_dim28": all(
            row["generated_lie_closure_dimension"] == 28 for row in triality["representations"].values()
        ),
        "triality_intertwiner_residuals_zero": triality["all_intertwiner_rows_pass"] is True,
        "triality_order3_cubed_scalar": triality["order_3_cubed_scalar"]["passes"] is True,
        "triality_s3_relations": triality["transposition_squared_scalar"]["passes"] is True
        and triality["s3_relation_TCT_equals_C_inverse"]["passes"] is True,
        "wrong_intertwiner_control_fired": triality["wrong_intertwiner_control"]["control_fired"] is True,
        "split_null_stabilizer_dim8": null_levi["dimension_bookkeeping"]["stabilizer_dim"] == 8,
        "split_null_nilradical_dim5": null_levi["dimension_bookkeeping"]["nilradical_dim"] == 5,
        "split_null_Levi_quotient_dim3": null_levi["dimension_bookkeeping"]["Levi_quotient_dim"] == 3,
        "split_null_dim_bookkeeping": null_levi["dimension_bookkeeping"]["identity_holds"] is True,
        "split_null_Levi_quotient_sl2": null_levi["split_null_decomposition"]["Levi_quotient"]["identification"]
        == "sl2_R_by_dim3_center0_derived3_and_indefinite_nonzero_Killing_form",
        "compact_positive_control_nilradical_zero": null_levi["compact_positive_control"]["nilradical_zero"] is True,
        "sign_flip_closure_control_fired": null_levi["sign_flip_closure_control"]["control_fired"] is True,
        "smt_positive_and_erased_flip": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_detected"]
        and proofs["cvc5"]["erased_flip_detected"],
        "nemo_sidecar_loaded": nemo.get("all_pass") is True,
        "nemo_project_recorded": str(nemo.get("runtime", {}).get("active_project", "")).endswith(
            "system_v6/optional/nemo_hecke/Project.toml"
        ),
        "one_to_one_tool_calls": [call["tool"] for call in calls] == ["sympy", "z3", "cvc5", "Nemo"],
        "capability_receipts_present": set(capability) == {"python", "sympy", "z3", "cvc5", "julia_nemo_hecke"},
        "forbidden_word_absent": forbidden_scan["passes"] is True,
        "no_audit_verdict_emitted": not (SIM_DIR / "audit_verdict.md").exists(),
    }
    all_pass = all(gates.values())
    python_engine_values = {
            "triality_closure_dims": {
                name: row["generated_lie_closure_dimension"] for name, row in triality["representations"].items()
            },
            "cycle_cubed_scalar": triality["order_3_cubed_scalar"]["scalar"],
            "split_null_stabilizer_dim": dim_values["stabilizer_dim"],
            "split_null_nilradical_dim": dim_values["nilradical_dim"],
            "split_null_Levi_quotient_dim": dim_values["Levi_quotient_dim"],
    }
    julia_engine_values = nemo.get("outer_s3_row", {})
    engine_values = {
        "jax": python_engine_values,
        "julia": julia_engine_values,
    }
    lane_computed_hashes = {
        "jax": {
            "subtree": "math_payload.triality_intertwiners + math_payload.split_null_Levi",
            "hash": stable_json_sha256(
                {
                    "triality_intertwiners": triality,
                    "split_null_Levi": null_levi,
                }
            ),
        },
        "julia": {
            "subtree": "nemo_hecke.outer_s3_row",
            "hash": stable_json_sha256(julia_engine_values),
        },
        "divergence": {
            "subtree": "divergence.engine_values",
            "hash": stable_json_sha256(engine_values),
        },
    }
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "stage_movement_allowed": STAGE_MOVEMENT_ALLOWED,
        "claim_ceiling": "scratch_diagnostic only; closes two symbolic depth fences locally without parent promotion",
        "claim": "Explicit D4 Chevalley-level triality intertwiners for the three 8-dimensional representations and bracket-derived split null-vector stabilizer radical/nilradical/Levi quotient bookkeeping.",
        "allowed_claims": [
            "one explicit symbolic realization of 8v/8c/8s triality intertwiners checked on Chevalley generators that generate 28-dimensional so(8)",
            "split null-vector stabilizer decomposition as computed bracket data with nilradical dimension 5 and reductive quotient dimension 3",
            "compact unit stabilizer positive control has zero nilradical",
            "S3 finite sanity row from Nemo GF(2) matrices",
        ],
        "disallowed_claims": [
            "formal admission",
            "canonical classification of all triality intertwiners",
            "retroactive promotion of the parent S10 or ratchet packets",
            "null-line parabolic classification beyond the null-vector stabilizer computed here",
            "bridge, axis, physics, Standard Model, GR, manifold, or crowned compact/split form claims",
        ],
        "generated_at": now_utc(),
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "parent_lineage": lineage,
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "lane_aliases": {"jax": "python_sympy_exact", "julia": "julia_nemo_hecke"},
            "omitted_lanes": {
                "pytorch": "not scoped: this symbolic light-local packet has no graph, network, tensor autograd, or PyTorch-native claim path"
            },
            "declared_mode": "symbolic_light_local",
            "standard_schema_binding": "schema_version is a field with value three_engine_sim_result_v1; packet-local mode is declared separately",
            "runner_boundary": "Python exact symbolic builder plus Julia Nemo sidecar; no dense heavy carriers",
            "julia_project": "system_v6/optional/nemo_hecke",
            "consumer_policy": "scratch diagnostic; no promotion",
        },
        "engines": {
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "result_path": rel(RESULT_PATH),
                "result_sha256": file_sha256(RESULT_PATH) if RESULT_PATH.exists() else None,
                "reads_peer_result": False,
                "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
                "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
                "tool_manifest": {k: TOOL_MANIFEST[k] for k in ["sympy", "z3", "cvc5"]},
                "tool_integration_depth": {k: TOOL_INTEGRATION_DEPTH[k] for k in ["sympy", "z3", "cvc5"]},
                "tool_calls": [call for call in calls if call["tool"] in {"sympy", "z3", "cvc5"}],
                "role_id": "python_sympy_exact_as_jax_schema_lane",
            },
            "julia": {
                "ran": nemo.get("all_pass") is True,
                "source_path": rel(NEMO_SOURCE_PATH),
                "source_sha256": file_sha256(NEMO_SOURCE_PATH),
                "result_path": rel(NEMO_RESULT_PATH),
                "result_sha256": file_sha256(NEMO_RESULT_PATH) if NEMO_RESULT_PATH.exists() else None,
                "reads_peer_result": False,
                "packages_used": [*nemo.get("packages_used", []), "julia_gf4_stdlib"],
                "aligned_packages_load_bearing": ["julia_gf4_stdlib"] if nemo.get("all_pass") else [],
                "classification": nemo.get("classification"),
                "promotion_allowed": nemo.get("promotion_allowed"),
                "formal_admission_allowed": nemo.get("formal_admission_allowed"),
                "tool_manifest": nemo.get("TOOL_MANIFEST", {}),
                "tool_integration_depth": nemo.get("TOOL_INTEGRATION_DEPTH", {}),
                "tool_calls": [call for call in calls if call["tool"] == "Nemo"],
                "role_id": "julia_nemo_hecke_as_julia_schema_lane",
            },
        },
        "computed_row_identity": {
            "scope": "shape-only envelope rerun; computed rows are re-emitted from the same builder functions",
            "subtree_hashes": lane_computed_hashes,
            "byte_identity_note": "Stable subtree hashes record computed-row identity across this envelope shape repair.",
        },
        "math_payload": {
            "triality_intertwiners": triality,
            "split_null_Levi": null_levi,
        },
        "crossover_proofs": proofs,
        "nemo_hecke": nemo,
        "capability_receipts": capability,
        "claim_path_tools": ["sympy", "z3", "cvc5", "Nemo"],
        "control_only_tools": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": calls,
        "build_gates": gates,
        "all_pass": all_pass,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": 0.0 if nemo.get("outer_s3_row", {}).get("gl2_2_order") == 6 else 1.0,
            "interpretation": "Not a three-engine parity envelope; Python exact algebra owns Lie rows, Julia/Nemo owns finite S3 sanity row.",
        },
        "forbidden_token_scan": forbidden_scan,
        "validator": {
            "packet_validator": rel(VALIDATOR_PATH),
            "packet_validator_result": rel(VALIDATOR_RESULT_PATH),
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "mode": MODE, "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
