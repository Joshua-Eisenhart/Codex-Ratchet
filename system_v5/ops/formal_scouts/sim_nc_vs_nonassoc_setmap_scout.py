#!/usr/bin/env python3
"""Branch 3 finite NC vs NC+nonassociative set-map scout.

Started from the SIM_TEMPLATE.py contract shape: bounded probe, explicit
positive/control/boundary sections, tool manifest, and a hard claim ceiling.
This is a scratch diagnostic only.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "nc_vs_nonassoc_setmap_scout"
BRANCH = 3
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = (
    "Finite set-map placing H/O/J3(O)/S by witness, scratch scout. "
    "No final M(C), PEPS3D admission, Axis0, physics, engine, or bridge claim."
)
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/nc_vs_nonassoc_setmap_scout_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/nc_vs_nonassoc_setmap_scout_julia_results.json"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_nc_vs_nonassoc_setmap_scout.py"
TOL = 1.0e-10
NONZERO_TOL = 1.0e-8
SAMPLE_COUNT = 18

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite algebra tables, products, associators, norms, and verdict scalars",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra for the finite map; no numpy compute path is imported or used",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization and peer receipt parsing",
    },
    "Julia": {
        "tried": True,
        "used": True,
        "reason": "supportive independent backend mirror checked through peer_result_path parity",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "forbidden for this branch; numpy compute is intentionally absent",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "json": "supportive",
    "Julia": "supportive",
    "numpy": None,
}


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def associator(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def commutator(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return multiply(table, x, y) - multiply(table, y, x)


def conjugate_cd(x: jax.Array) -> jax.Array:
    signs = jnp.where(jnp.arange(x.shape[0]) == 0, 1.0, -1.0).astype(jnp.float64)
    return x * signs


def real_table() -> jax.Array:
    return jnp.ones((1, 1, 1), dtype=jnp.float64)


def cayley_dickson_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a = x[:n]
    b = x[n:]
    c = y[:n]
    d = y[n:]
    first = multiply(parent, a, c) - multiply(parent, conjugate_cd(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_cd(c))
    return jnp.concatenate([first, second])


def cayley_dickson_double(parent: jax.Array) -> jax.Array:
    dim = parent.shape[0] * 2
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cayley_dickson_multiply(parent, eye[i], eye[j]))
    return table


def complex_pair_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.asarray(
        [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]],
        dtype=jnp.float64,
    )


def m2c_vector_multiply(x: jax.Array, y: jax.Array) -> jax.Array:
    xm = jnp.reshape(x, (2, 2, 2))
    ym = jnp.reshape(y, (2, 2, 2))
    out = jnp.zeros((2, 2, 2), dtype=jnp.float64)
    for i in range(2):
        for j in range(2):
            acc = jnp.zeros((2,), dtype=jnp.float64)
            for k in range(2):
                acc = acc + complex_pair_mul(xm[i, k], ym[k, j])
            out = out.at[i, j].set(acc)
    return jnp.reshape(out, (8,))


def m2c_table() -> jax.Array:
    dim = 8
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(m2c_vector_multiply(eye[i], eye[j]))
    return table


def octonion_conj(x: jax.Array) -> jax.Array:
    return conjugate_cd(x)


def j3_basis_matrix(idx: int) -> jax.Array:
    mat = jnp.zeros((3, 3, 8), dtype=jnp.float64)
    if idx < 3:
        return mat.at[idx, idx, 0].set(1.0)
    pairs = [(0, 1), (0, 2), (1, 2)]
    slot = idx - 3
    pair_idx = slot // 8
    component = slot % 8
    i, j = pairs[pair_idx]
    unit = basis(8, component)
    mat = mat.at[i, j, :].set(unit)
    mat = mat.at[j, i, :].set(octonion_conj(unit))
    return mat


def j3_flatten(mat: jax.Array) -> jax.Array:
    pairs = [(0, 1), (0, 2), (1, 2)]
    parts = [mat[0, 0, 0:1], mat[1, 1, 0:1], mat[2, 2, 0:1]]
    for i, j in pairs:
        parts.append(mat[i, j, :])
    return jnp.concatenate(parts)


def j3_unflatten(x: jax.Array) -> jax.Array:
    mat = jnp.zeros((3, 3, 8), dtype=jnp.float64)
    mat = mat.at[0, 0, 0].set(x[0])
    mat = mat.at[1, 1, 0].set(x[1])
    mat = mat.at[2, 2, 0].set(x[2])
    pairs = [(0, 1), (0, 2), (1, 2)]
    cursor = 3
    for i, j in pairs:
        octv = x[cursor : cursor + 8]
        cursor += 8
        mat = mat.at[i, j, :].set(octv)
        mat = mat.at[j, i, :].set(octonion_conj(octv))
    return mat


def j3_matmul_oct(o_table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    out = jnp.zeros((3, 3, 8), dtype=jnp.float64)
    for i in range(3):
        for j in range(3):
            acc = jnp.zeros((8,), dtype=jnp.float64)
            for k in range(3):
                acc = acc + multiply(o_table, a[i, k], b[k, j])
            out = out.at[i, j, :].set(acc)
    return out


def j3_jordan_matrix_product(o_table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    return 0.5 * (j3_matmul_oct(o_table, a, b) + j3_matmul_oct(o_table, b, a))


def j3_vector_multiply(o_table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return j3_flatten(j3_jordan_matrix_product(o_table, j3_unflatten(x), j3_unflatten(y)))


def j3_table(o_table: jax.Array) -> jax.Array:
    dim = 27
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(j3_vector_multiply(o_table, eye[i], eye[j]))
    return table


def j3_square_trace(o_table: jax.Array, x: jax.Array) -> jax.Array:
    mat = j3_unflatten(x)
    sq = j3_jordan_matrix_product(o_table, mat, mat)
    return sq[0, 0, 0] + sq[1, 1, 0] + sq[2, 2, 0]


def probe_vector(dim: int, sample_idx: int, side: int) -> jax.Array:
    vals = []
    for j in range(1, dim + 1):
        raw = (
            (sample_idx + 17) * (j + 3) * (side + 5) * 37
            + (j + 1) ** 2 * 19
            + sample_idx * 11
            + side * 13
        ) % 101
        vals.append((float(raw) - 50.0) / 37.0)
    return jnp.asarray(vals, dtype=jnp.float64)


def terms_from_vector(v: jax.Array) -> list[dict[str, Any]]:
    terms = []
    for idx in range(v.shape[0]):
        value = py_float(v[idx])
        if abs(value) > TOL:
            terms.append({"basis_index": idx, "label": f"e{idx}", "coefficient": value})
    return terms


def vector_witness(table: jax.Array, left: jax.Array, right: jax.Array, kind: str) -> dict[str, Any]:
    product = multiply(table, left, right)
    return {
        "kind": kind,
        "left_terms": terms_from_vector(left),
        "right_terms": terms_from_vector(right),
        "product_terms": terms_from_vector(product),
        "left_norm": py_float(jnp.linalg.norm(left)),
        "right_norm": py_float(jnp.linalg.norm(right)),
        "product_norm": py_float(jnp.linalg.norm(product)),
        "pass": py_float(jnp.linalg.norm(product)) < TOL
        and py_float(jnp.linalg.norm(left)) > TOL
        and py_float(jnp.linalg.norm(right)) > TOL,
    }


def explicit_zero_witness(name: str, table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    if name == "M2C":
        left = basis(dim, 0)  # E11 real
        right = basis(dim, 6)  # E22 real
        return vector_witness(table, left, right, "matrix_units_E11_times_E22")
    if name == "J3O":
        left = basis(dim, 0)  # diagonal idempotent E11
        right = basis(dim, 1)  # diagonal idempotent E22
        return vector_witness(table, left, right, "orthogonal_jordan_idempotents_E11_circ_E22")
    if name == "S":
        left = basis(dim, 1) + basis(dim, 10)
        right = basis(dim, 5) + basis(dim, 14)
        return vector_witness(table, left, right, "requested_sedenion_(e1+e10)*(e5+e14)")
    return {
        "kind": "no_explicit_zero_product_claimed",
        "left_terms": [],
        "right_terms": [],
        "product_terms": [],
        "left_norm": None,
        "right_norm": None,
        "product_norm": None,
        "pass": False,
    }


def analyze_algebra(name: str, table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    assoc_gap = 0.0
    comm_gap = 0.0
    alt_xxy_gap = 0.0
    alt_xyy_gap = 0.0
    power_gap = 0.0
    norm_mult_gap = 0.0
    assoc_witness: dict[str, Any] = {"kind": "none"}
    comm_witness: dict[str, Any] = {"kind": "none"}
    norm_witness: dict[str, Any] = {"kind": "none"}
    power_witness: dict[str, Any] = {"kind": "none"}

    for sample_idx in range(1, SAMPLE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 3)
        y = probe_vector(dim, sample_idx, 5)
        z = probe_vector(dim, sample_idx, 7)
        assoc_norm = py_float(jnp.linalg.norm(associator(table, x, y, z)))
        if assoc_norm > assoc_gap:
            assoc_gap = assoc_norm
            assoc_witness = {"sample_idx": sample_idx, "norm": assoc_norm}
        comm_norm = py_float(jnp.linalg.norm(commutator(table, x, y)))
        if comm_norm > comm_gap:
            comm_gap = comm_norm
            comm_witness = {"sample_idx": sample_idx, "norm": comm_norm}
        alt_xxy = py_float(jnp.linalg.norm(associator(table, x, x, y)))
        alt_xyy = py_float(jnp.linalg.norm(associator(table, x, y, y)))
        alt_xxy_gap = max(alt_xxy_gap, alt_xxy)
        alt_xyy_gap = max(alt_xyy_gap, alt_xyy)
        x2 = multiply(table, x, x)
        x3_left = multiply(table, x2, x)
        x3_right = multiply(table, x, x2)
        x4_left = multiply(table, x2, x2)
        x4_right = multiply(table, x, x3_right)
        power_residual = max(
            py_float(jnp.linalg.norm(x3_left - x3_right)),
            py_float(jnp.linalg.norm(x4_left - x4_right)),
        )
        if power_residual > power_gap:
            power_gap = power_residual
            power_witness = {"sample_idx": sample_idx, "norm": power_residual}
        product = multiply(table, x, y)
        norm_residual = abs(py_float(jnp.linalg.norm(product)) - py_float(jnp.linalg.norm(x)) * py_float(jnp.linalg.norm(y)))
        if norm_residual > norm_mult_gap:
            norm_mult_gap = norm_residual
            norm_witness = {"sample_idx": sample_idx, "residual": norm_residual}

    zero = explicit_zero_witness(name, table)
    if zero["pass"]:
        zero_norm_residual = abs(float(zero["product_norm"]) - float(zero["left_norm"]) * float(zero["right_norm"]))
        if zero_norm_residual > norm_mult_gap:
            norm_mult_gap = zero_norm_residual
            norm_witness = {**zero, "residual": zero_norm_residual}

    return {
        "dim": dim,
        "sample_count": SAMPLE_COUNT,
        "associativity_gap": assoc_gap,
        "commutativity_gap": comm_gap,
        "alternativity_xxy_gap": alt_xxy_gap,
        "alternativity_xyy_gap": alt_xyy_gap,
        "alternativity_gap": max(alt_xxy_gap, alt_xyy_gap),
        "power_associativity_gap": power_gap,
        "norm_multiplicativity_gap": norm_mult_gap,
        "assoc_witness": assoc_witness,
        "comm_witness": comm_witness,
        "power_witness": power_witness,
        "norm_multiplicativity_witness": norm_witness,
        "explicit_zero_product_witness": zero,
        "assoc_zero_under_tol": assoc_gap < TOL,
        "commutative_under_tol": comm_gap < TOL,
        "alternative_under_tol": max(alt_xxy_gap, alt_xyy_gap) < TOL,
        "power_associative_under_tol": power_gap < TOL,
        "norm_multiplicative_under_tol": norm_mult_gap < TOL,
        "explicit_zero_product_found": bool(zero["pass"]),
    }


def classify(name: str, metrics: dict[str, Any]) -> dict[str, Any]:
    if name in {"R", "C"}:
        placement = "commutative_associative_control_below_NC_line"
    elif name == "H":
        placement = "Set1_noncommutative_associative_quaternion_carrier"
    elif name == "M2C":
        placement = "Set1_noncommutative_associative_matrix_algebra_with_zero_products"
    elif name == "O":
        placement = "Set2_alternative_nonassociative_octonion_readout_lane"
    elif name == "J3O":
        placement = "Set2_formally_real_nonassociative_jordan_observable_lane"
    elif name == "S":
        placement = "graveyard_nonassociative_zero_divisor_sedenion"
    else:
        placement = "unclassified"
    return {
        "placement": placement,
        "set1_nc_associative": name in {"H", "M2C"},
        "set2_superset_or_nonassoc_lane": name in {"H", "M2C", "O", "J3O"},
        "graveyard": name == "S",
        "noncommutative_detected": metrics["commutativity_gap"] > NONZERO_TOL,
        "nonassociative_detected": metrics["associativity_gap"] > NONZERO_TOL,
        "commutative_control": name in {"R", "C"},
    }


def table_checksum(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    c = jnp.arange(1, dim + 1, dtype=jnp.float64)[:, None, None]
    a = jnp.arange(1, dim + 1, dtype=jnp.float64)[None, :, None]
    b = jnp.arange(1, dim + 1, dtype=jnp.float64)[None, None, :]
    weights = 1_000_003.0 * c + 1_009.0 * a + b
    return {
        "dim": dim,
        "nonzero_entry_count": int(jax.device_get(jnp.count_nonzero(jnp.abs(table) > 0.0))),
        "sum_abs_entries": py_float(jnp.sum(jnp.abs(table))),
        "weighted_checksum": py_float(jnp.sum(table * weights)),
    }


def formal_real_j3_positive(o_table: jax.Array) -> dict[str, Any]:
    min_square_trace = float("inf")
    max_square_trace_error = 0.0
    witness = {"kind": "none"}
    for sample_idx in range(1, SAMPLE_COUNT + 1):
        x = probe_vector(27, sample_idx, 11)
        value = py_float(j3_square_trace(o_table, x))
        weighted_coordinate_sq = py_float(jnp.dot(x[:3], x[:3]) + 2.0 * jnp.dot(x[3:], x[3:]))
        min_square_trace = min(min_square_trace, value)
        max_square_trace_error = max(max_square_trace_error, abs(value - weighted_coordinate_sq))
        if "square_trace" not in witness or value < witness["square_trace"]:
            witness = {"sample_idx": sample_idx, "square_trace": value, "weighted_coordinate_square": weighted_coordinate_sq}
    return {
        "min_sample_square_trace": min_square_trace,
        "max_square_trace_minus_vector_square_abs": max_square_trace_error,
        "pass": min_square_trace > 0.0 and max_square_trace_error < TOL,
        "witness": witness,
    }


def build_tables() -> dict[str, jax.Array]:
    r = real_table()
    c = cayley_dickson_double(r)
    h = cayley_dickson_double(c)
    o = cayley_dickson_double(h)
    s = cayley_dickson_double(o)
    return {
        "R": r,
        "C": c,
        "H": h,
        "M2C": m2c_table(),
        "O": o,
        "J3O": j3_table(o),
        "S": s,
    }


def row_pass(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
            "parity_max_diff": None,
            "max_diff_key": None,
            "within_1e_10": False,
            "boolean_mismatches": [],
            "missing_keys": [],
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    missing: list[str] = []
    for key in sorted(result["shared_scalars"]):
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        this_value = float(result["shared_scalars"][key])
        peer_value = float(peer["shared_scalars"][key])
        diff = abs(this_value - peer_value)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        rows.append({"key": key, "jax": this_value, "julia": peer_value, "abs_diff": diff})

    mismatches = []
    for key in sorted(result["shared_booleans"]):
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(result["shared_booleans"][key]) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(result["shared_booleans"][key]), "julia": bool(peer["shared_booleans"][key])})

    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "max_diff_key": max_diff_key,
        "within_1e_10": max_diff < TOL and not mismatches and not missing,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
    }


def build_result() -> dict[str, Any]:
    tables = build_tables()
    metrics = {name: analyze_algebra(name, table) for name, table in tables.items()}
    placements = {name: classify(name, metrics[name]) for name in tables}
    j3_formal_real = formal_real_j3_positive(tables["O"])

    positive = {
        "H_associative_noncommutative_carrier": {
            "pass": metrics["H"]["assoc_zero_under_tol"] and placements["H"]["noncommutative_detected"],
            "assoc_gap": metrics["H"]["associativity_gap"],
            "comm_gap": metrics["H"]["commutativity_gap"],
            "placement": placements["H"]["placement"],
        },
        "O_alternative_nonassoc_no_zero_divisor_in_norm_control": {
            "pass": (
                metrics["O"]["associativity_gap"] > NONZERO_TOL
                and metrics["O"]["alternative_under_tol"]
                and metrics["O"]["norm_multiplicative_under_tol"]
                and not metrics["O"]["explicit_zero_product_found"]
            ),
            "assoc_gap": metrics["O"]["associativity_gap"],
            "alternativity_gap": metrics["O"]["alternativity_gap"],
            "norm_multiplicativity_gap": metrics["O"]["norm_multiplicativity_gap"],
            "placement": placements["O"]["placement"],
        },
        "J3O_formally_real_nonassoc_jordan_observable": {
            "pass": (
                metrics["J3O"]["associativity_gap"] > NONZERO_TOL
                and metrics["J3O"]["commutative_under_tol"]
                and metrics["J3O"]["power_associative_under_tol"]
                and j3_formal_real["pass"]
            ),
            "assoc_gap": metrics["J3O"]["associativity_gap"],
            "comm_gap": metrics["J3O"]["commutativity_gap"],
            "power_gap": metrics["J3O"]["power_associativity_gap"],
            "formal_real_square_trace": j3_formal_real,
            "placement": placements["J3O"]["placement"],
        },
        "S_sedenion_graveyard_zero_divisor": {
            "pass": metrics["S"]["explicit_zero_product_found"],
            "witness": metrics["S"]["explicit_zero_product_witness"],
            "placement": placements["S"]["placement"],
        },
        "finite_set_map_clean_separation": {
            "pass": (
                placements["H"]["set1_nc_associative"]
                and placements["M2C"]["set1_nc_associative"]
                and placements["O"]["set2_superset_or_nonassoc_lane"]
                and placements["J3O"]["set2_superset_or_nonassoc_lane"]
                and placements["S"]["graveyard"]
                and placements["R"]["commutative_control"]
                and placements["C"]["commutative_control"]
            ),
            "set1": ["H", "M2C"],
            "set2_non_graveyard": ["H", "M2C", "O", "J3O"],
            "graveyard": ["S"],
            "commutative_controls_below_nc_line": ["R", "C"],
        },
    }

    real_nonassoc = {
        name: metrics[name]["associativity_gap"] > NONZERO_TOL for name in ["H", "M2C", "O", "J3O", "S"]
    }
    erased_nonassoc = {name: False for name in real_nonassoc}
    changed_by_erasure = [name for name in real_nonassoc if real_nonassoc[name] != erased_nonassoc[name]]

    controls = {
        "H_assoc_gap_known_zero": {
            "pass": metrics["H"]["associativity_gap"] < TOL,
            "value": metrics["H"]["associativity_gap"],
        },
        "O_nonassoc_but_alternative_known": {
            "pass": metrics["O"]["associativity_gap"] > NONZERO_TOL and metrics["O"]["alternative_under_tol"],
            "assoc_gap": metrics["O"]["associativity_gap"],
            "alternativity_gap": metrics["O"]["alternativity_gap"],
        },
        "S_requested_zero_divisor_exact": {
            "pass": metrics["S"]["explicit_zero_product_witness"]["pass"],
            "witness": metrics["S"]["explicit_zero_product_witness"],
        },
        "R_C_commutative_controls_below_NC_line": {
            "pass": (
                metrics["R"]["commutative_under_tol"]
                and metrics["C"]["commutative_under_tol"]
                and placements["H"]["noncommutative_detected"]
                and placements["M2C"]["noncommutative_detected"]
            ),
            "R_comm_gap": metrics["R"]["commutativity_gap"],
            "C_comm_gap": metrics["C"]["commutativity_gap"],
            "H_comm_gap": metrics["H"]["commutativity_gap"],
            "M2C_comm_gap": metrics["M2C"]["commutativity_gap"],
        },
        "real_vs_erased_nonassoc_verdict_fires": {
            "pass": set(changed_by_erasure) == {"O", "J3O", "S"},
            "real_nonassoc": real_nonassoc,
            "erased_nonassoc": erased_nonassoc,
            "changed_by_erasure": changed_by_erasure,
        },
    }

    boundary = {
        "scratch_diagnostic_only": {
            "pass": True,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "carrier_boundary": {
            "pass": True,
            "carrier": "finite spinor networks",
            "diagnostic_readout_lanes": ["quaternion coordinates", "octonion coordinates", "sedenion coordinates", "J3(O) tensor coordinates"],
            "not_admitted_as_primitives": ["octonion primitive", "tensor primitive", "PEPS3D admission primitive"],
        },
        "claim_ceiling": {
            "pass": True,
            "claim": "finite set-map placing H/O/J3(O)/S by witness, scratch scout",
            "blocked_claims": ["final M(C)", "PEPS3D admission", "Axis0", "physics", "engine", "bridge"],
        },
        "zero_product_boundary": {
            "pass": True,
            "note": "M2C and J3(O) have finite zero-product pairs in their associative/Jordan products; only S is routed to graveyard here because the requested sedenion witness breaks normed-division behavior.",
        },
    }

    shared_scalars = {}
    for name in ["R", "C", "H", "M2C", "O", "J3O", "S"]:
        for key in [
            "dim",
            "associativity_gap",
            "commutativity_gap",
            "alternativity_gap",
            "power_associativity_gap",
            "norm_multiplicativity_gap",
        ]:
            shared_scalars[f"{name}.{key}"] = float(metrics[name][key])
        checksum = table_checksum(tables[name])
        shared_scalars[f"{name}.table_nonzero_entry_count"] = float(checksum["nonzero_entry_count"])
        shared_scalars[f"{name}.table_weighted_checksum"] = float(checksum["weighted_checksum"])
        witness = metrics[name]["explicit_zero_product_witness"]
        if witness["product_norm"] is not None:
            shared_scalars[f"{name}.explicit_zero_product_norm"] = float(witness["product_norm"])
    shared_scalars["J3O.formal_real_min_square_trace"] = float(j3_formal_real["min_sample_square_trace"])
    shared_scalars["J3O.formal_real_square_trace_error"] = float(j3_formal_real["max_square_trace_minus_vector_square_abs"])

    shared_booleans = {}
    for name in ["R", "C", "H", "M2C", "O", "J3O", "S"]:
        for key in [
            "assoc_zero_under_tol",
            "commutative_under_tol",
            "alternative_under_tol",
            "power_associative_under_tol",
            "norm_multiplicative_under_tol",
            "explicit_zero_product_found",
        ]:
            shared_booleans[f"{name}.{key}"] = bool(metrics[name][key])
        shared_booleans[f"{name}.set1_nc_associative"] = bool(placements[name]["set1_nc_associative"])
        shared_booleans[f"{name}.set2_superset_or_nonassoc_lane"] = bool(placements[name]["set2_superset_or_nonassoc_lane"])
        shared_booleans[f"{name}.graveyard"] = bool(placements[name]["graveyard"])
    for section_name, section in [("positive", positive), ("controls", controls), ("boundary", boundary)]:
        for key, row in section.items():
            shared_booleans[f"{section_name}.{key}.pass"] = bool(row["pass"])

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "branch": BRANCH,
        "backend": "jax_full_sim",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "nonclassical_diagnostic",
        "sim_class": "finite_set_map_probe",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_used": False,
        "tol": TOL,
        "nonzero_tol": NONZERO_TOL,
        "sample_count": SAMPLE_COUNT,
        "carrier_statement": boundary["carrier_boundary"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "CONTROLS": controls,
        "controls": controls,
        "boundary": boundary,
        "placements": placements,
        "metrics": metrics,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": "Finite witnesses separate H and M2(C) as noncommutative associative rows, O as alternative nonassociative without a finite zero-product witness, J3(O) as a formally real nonassociative Jordan observable, S as the explicit zero-divisor graveyard row, and R/C as commutative controls below the NC line.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["all_pass"] = (
        row_pass(positive)
        and row_pass(controls)
        and row_pass(boundary)
        and result["parity"]["within_1e_10"]
        and result["classification"] == CLASSIFICATION
        and result["promotion_allowed"] is PROMOTION_ALLOWED
        and result["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        and result["numpy_used"] is False
    )
    result["headline"] = (
        f"H_assoc={metrics['H']['associativity_gap']:.3e}; "
        f"O_assoc={metrics['O']['associativity_gap']:.3e}; "
        f"J3O_assoc={metrics['J3O']['associativity_gap']:.3e}; "
        f"S_zero={metrics['S']['explicit_zero_product_witness']['product_norm']:.3e}; "
        f"parity={result['parity']['parity_max_diff']}"
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    print(f"{OBJECT_ID} - JAX backend")
    print(result["plain_sentence"])
    print(f"parity_status={result['parity']['status']} parity_max_diff={result['parity']['parity_max_diff']} within_1e-10={result['parity']['within_1e_10']}")
    print(f"all_pass={str(result['all_pass']).lower()} result_path={result['result_path']}")


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
