#!/usr/bin/env python3
# object_id: division_algebra_ratchet_ladder
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

import jax

jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "division_algebra_ratchet_ladder"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "division_algebra_ratchet_ladder_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "division_algebra_ratchet_ladder_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
NORM_PROBE_COUNT = 64
STRUCTURE_PROBE_COUNT = 16
ZERO_WITNESS_LIMIT = 8
FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def setprod(table: jax.Array, a: int, b: int, c: int, s: float) -> jax.Array:
    return table.at[c, a, b].set(s)


def add_identity(table: jax.Array, dim: int) -> jax.Array:
    for a in range(dim):
        table = setprod(table, 0, a, a, 1.0)
        table = setprod(table, a, 0, a, 1.0)
    return table


def real_table() -> jax.Array:
    return setprod(jnp.zeros((1, 1, 1), dtype=jnp.float64), 0, 0, 0, 1.0)


def complex_table() -> jax.Array:
    table = add_identity(jnp.zeros((2, 2, 2), dtype=jnp.float64), 2)
    return setprod(table, 1, 1, 0, -1.0)


def quaternion_table() -> jax.Array:
    table = add_identity(jnp.zeros((4, 4, 4), dtype=jnp.float64), 4)
    for a in range(1, 4):
        table = setprod(table, a, a, 0, -1.0)
    for i, j, k in [(1, 2, 3)]:
        for a, b, c, s in [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]:
            table = setprod(table, a, b, c, s)
    return table


def octonion_table() -> jax.Array:
    table = add_identity(jnp.zeros((8, 8, 8), dtype=jnp.float64), 8)
    for a in range(1, 8):
        table = setprod(table, a, a, 0, -1.0)
    for i, j, k in FANO:
        for a, b, c, s in [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]:
            table = setprod(table, a, b, c, s)
    return table


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def conjugate_cd(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)])
    return x * signs


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
    n = parent.shape[0]
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cayley_dickson_multiply(parent, eye[i], eye[j]))
    return table


def associator(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def probe_vector(dim: int, sample_idx: int, side: int) -> jax.Array:
    vals: list[float] = []
    for j in range(1, dim + 1):
        raw = (
            (sample_idx + 17) * (j + 3) * (side + 5) * 37
            + (j + 1) ** 2 * 19
            + sample_idx * 11
            + side * 13
        ) % 101
        vals.append((float(raw) - 50.0) / 37.0)
    return jnp.asarray(vals, dtype=jnp.float64)


def probe_family(dim: int) -> list[jax.Array]:
    vectors = [basis(dim, idx) for idx in range(dim)]
    for sample_idx in range(1, STRUCTURE_PROBE_COUNT + 1):
        vectors.append(probe_vector(dim, sample_idx, 7))
    return vectors


def commutator_max(table: jax.Array) -> float:
    diff = table - jnp.swapaxes(table, 1, 2)
    return py_float(jnp.max(jnp.linalg.norm(diff, axis=0)))


def associator_max(table: jax.Array) -> float:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    return py_float(jnp.max(jnp.linalg.norm(left - right, axis=0)))


def alternator_residual(table: jax.Array) -> tuple[float, float, float, dict[str, Any], dict[str, Any], int]:
    vectors = probe_family(table.shape[0])
    max_xxy = 0.0
    max_xyy = 0.0
    xxy_witness: dict[str, Any] = {"kind": "none"}
    xyy_witness: dict[str, Any] = {"kind": "none"}
    for ix, x in enumerate(vectors, start=1):
        for iy, y in enumerate(vectors, start=1):
            xxy = py_float(jnp.linalg.norm(associator(table, x, x, y)))
            if xxy > max_xxy:
                max_xxy = xxy
                xxy_witness = {"x_probe_index": ix, "y_probe_index": iy, "residual": xxy}
            xyy = py_float(jnp.linalg.norm(associator(table, x, y, y)))
            if xyy > max_xyy:
                max_xyy = xyy
                xyy_witness = {"x_probe_index": ix, "y_probe_index": iy, "residual": xyy}
    return max(max_xxy, max_xyy), max_xxy, max_xyy, xxy_witness, xyy_witness, len(vectors)


def terms_from_vector(v: jax.Array) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for idx in range(v.shape[0]):
        value = py_float(v[idx])
        if abs(value) > TOL:
            terms.append({"basis_index": idx, "coefficient": value, "label": f"e{idx}"})
    return terms


def zero_witness_dict(kind: str, left: jax.Array, right: jax.Array, product: jax.Array) -> dict[str, Any]:
    return {
        "kind": kind,
        "left_terms": terms_from_vector(left),
        "right_terms": terms_from_vector(right),
        "product_terms": terms_from_vector(product),
        "left_norm": py_float(jnp.linalg.norm(left)),
        "right_norm": py_float(jnp.linalg.norm(right)),
        "product_norm": py_float(jnp.linalg.norm(product)),
    }


def pair_vector(dim: int, i: int, j: int, si: float = 1.0, sj: float = 1.0) -> jax.Array:
    v = jnp.zeros((dim,), dtype=jnp.float64)
    v = v.at[i].set(si)
    v = v.at[j].set(sj)
    return v


def pure_imaginary_pairs(dim: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(1, dim) for j in range(i + 1, dim)]


def signed_two_term_zero_search(table: jax.Array) -> tuple[int, float, dict[str, Any] | None, list[dict[str, Any]]]:
    dim = table.shape[0]
    pairs = pure_imaginary_pairs(dim)
    sign_rows = [(i, j, si, sj) for i, j in pairs for si in (-1.0, 1.0) for sj in (-1.0, 1.0)]
    if not sign_rows:
        return 0, float("inf"), None, []
    sign_array = jnp.asarray(sign_rows, dtype=jnp.float64)
    left_idx = jnp.repeat(jnp.arange(len(sign_rows), dtype=jnp.int32), len(sign_rows))
    right_idx = jnp.tile(jnp.arange(len(sign_rows), dtype=jnp.int32), len(sign_rows))
    li = sign_array[left_idx, 0].astype(jnp.int32)
    lj = sign_array[left_idx, 1].astype(jnp.int32)
    lsi = sign_array[left_idx, 2]
    lsj = sign_array[left_idx, 3]
    ri = sign_array[right_idx, 0].astype(jnp.int32)
    rj = sign_array[right_idx, 1].astype(jnp.int32)
    rsi = sign_array[right_idx, 2]
    rsj = sign_array[right_idx, 3]
    products = (
        (lsi * rsi)[None, :] * table[:, li, ri]
        + (lsi * rsj)[None, :] * table[:, li, rj]
        + (lsj * rsi)[None, :] * table[:, lj, ri]
        + (lsj * rsj)[None, :] * table[:, lj, rj]
    )
    norms = jnp.linalg.norm(products, axis=0)
    mask = norms < TOL
    count = int(jax.device_get(jnp.sum(mask)))
    min_norm = py_float(jnp.min(norms))
    if count == 0:
        return count, min_norm, None, []
    indices = [int(x) for x in jax.device_get(jnp.nonzero(mask, size=ZERO_WITNESS_LIMIT, fill_value=-1)[0]) if int(x) >= 0]
    first_index = indices[0]
    examples: list[dict[str, Any]] = []
    first: dict[str, Any] | None = None
    for idx in indices:
        li_row = sign_rows[int(jax.device_get(left_idx[idx]))]
        ri_row = sign_rows[int(jax.device_get(right_idx[idx]))]
        i, j, si, sj = li_row
        k, l, sk, sl = ri_row
        left = pair_vector(dim, i, j, si, sj)
        right = pair_vector(dim, k, l, sk, sl)
        product = multiply(table, left, right)
        witness = zero_witness_dict("signed_two_term_pure_imaginary_pair", left, right, product)
        witness["pair_indices"] = {"left": [i, j], "right": [k, l]}
        examples.append(witness)
        if idx == first_index:
            first = witness
    return count, min_norm, first, examples


def zero_divisor_search(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    min_product_norm = float("inf")
    first_witness: dict[str, Any] | None = None
    examples: list[dict[str, Any]] = []
    basis_zero_count = 0
    probe_zero_count = 0

    for a in range(dim):
        for b in range(dim):
            left = basis(dim, a)
            right = basis(dim, b)
            product = multiply(table, left, right)
            product_norm = py_float(jnp.linalg.norm(product))
            min_product_norm = min(min_product_norm, product_norm)
            if product_norm < TOL:
                basis_zero_count += 1
                witness = zero_witness_dict("basis_pair", left, right, product)
                witness["pair_indices"] = {"left": [a], "right": [b]}
                if first_witness is None:
                    first_witness = witness
                if len(examples) < ZERO_WITNESS_LIMIT:
                    examples.append(witness)

    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        left = probe_vector(dim, sample_idx, 1)
        right = probe_vector(dim, sample_idx, 2)
        product = multiply(table, left, right)
        product_norm = py_float(jnp.linalg.norm(product))
        min_product_norm = min(min_product_norm, product_norm)
        if product_norm < TOL and py_float(jnp.linalg.norm(left)) > TOL and py_float(jnp.linalg.norm(right)) > TOL:
            probe_zero_count += 1
            witness = zero_witness_dict("deterministic_probe_pair", left, right, product)
            witness["sample_idx"] = sample_idx
            if first_witness is None:
                first_witness = witness
            if len(examples) < ZERO_WITNESS_LIMIT:
                examples.append(witness)

    signed_count, signed_min, signed_first, signed_examples = signed_two_term_zero_search(table)
    min_product_norm = min(min_product_norm, signed_min)
    if first_witness is None and signed_first is not None:
        first_witness = signed_first
    for witness in signed_examples:
        if len(examples) < ZERO_WITNESS_LIMIT:
            examples.append(witness)

    return {
        "search_kind": "basis_pairs_plus_probe_pairs_plus_signed_two_term_pure_imaginary_pairs",
        "basis_pair_search_size": dim * dim,
        "probe_pair_search_size": NORM_PROBE_COUNT,
        "signed_pair_search_size": len(pure_imaginary_pairs(dim)) ** 2 * 16,
        "basis_zero_divisor_count": basis_zero_count,
        "probe_zero_divisor_count": probe_zero_count,
        "signed_zero_divisor_count": signed_count,
        "min_product_norm_seen": min_product_norm,
        "zero_divisors_exist": first_witness is not None,
        "first_witness": first_witness,
        "examples": examples,
    }


def norm_mult_residual(table: jax.Array, zero_search: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    max_seen = 0.0
    witness: dict[str, Any] = {"kind": "none"}
    dim = table.shape[0]
    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = py_float(jnp.abs(jnp.linalg.norm(multiply(table, x, y)) - jnp.linalg.norm(x) * jnp.linalg.norm(y)))
        if residual > max_seen:
            max_seen = residual
            witness = {"kind": "deterministic_probe_pair", "sample_idx": sample_idx, "residual": residual}
    if zero_search["first_witness"] is not None:
        zw = zero_search["first_witness"]
        residual = abs(float(zw["product_norm"]) - float(zw["left_norm"]) * float(zw["right_norm"]))
        if residual > max_seen:
            max_seen = residual
            witness = {**zw, "norm_multiplicative_residual": residual}
    return max_seen, witness


def analyze_algebra(symbol: str, label: str, table: jax.Array) -> dict[str, Any]:
    zero_search = zero_divisor_search(table)
    norm_resid, norm_witness = norm_mult_residual(table, zero_search)
    alt_resid, alt_xxy, alt_xyy, xxy_witness, xyy_witness, alt_probe_count = alternator_residual(table)
    comm = commutator_max(table)
    assoc = associator_max(table)
    properties = {
        "commutative": comm < TOL,
        "associative": assoc < TOL,
        "alternative": alt_resid < TOL,
        "normed_division": norm_resid < TOL and not zero_search["zero_divisors_exist"],
    }
    return {
        "name": symbol,
        "label": label,
        "dim": table.shape[0],
        "commutator_max": comm,
        "associator_max": assoc,
        "alternator_residual": alt_resid,
        "alternator_xxy_max": alt_xxy,
        "alternator_xyy_max": alt_xyy,
        "norm_mult_residual": norm_resid,
        "has_zero_divisors": zero_search["zero_divisors_exist"],
        "zero_divisor_check": zero_search,
        "alternator_check": {
            "probe_kind": "basis_vectors_plus_deterministic_pseudorandom_vectors",
            "probe_count": alt_probe_count,
            "xxy_witness": xxy_witness,
            "xyy_witness": xyy_witness,
        },
        "norm_multiplicative_check": {"witness": norm_witness},
        "properties": properties,
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


def hopf_fibration_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, dim in [("R", 1), ("C", 2), ("H", 4), ("O", 8)]:
        rows.append({
            "algebra": name,
            "algebra_dim": dim,
            "total_unit_sphere_dim": 2 * dim - 1,
            "base_sphere_dim": dim,
            "fiber_sphere_dim": dim - 1,
            "correspondence": f"S^{2 * dim - 1} total, S^{dim} base, S^{dim - 1} fiber",
        })
    return rows


def property_loss_verdicts(algebras: dict[str, Any]) -> dict[str, Any]:
    normed = [name for name in ["R", "C", "H", "O", "S"] if algebras[name]["properties"]["normed_division"]]
    return {
        "R_C_commutative_no_loss": algebras["R"]["properties"]["commutative"] and algebras["C"]["properties"]["commutative"],
        "H_loses_commutativity": algebras["C"]["properties"]["commutative"] and not algebras["H"]["properties"]["commutative"],
        "O_loses_associativity": algebras["H"]["properties"]["associative"] and not algebras["O"]["properties"]["associative"],
        "S_loses_alternativity": algebras["O"]["properties"]["alternative"] and not algebras["S"]["properties"]["alternative"],
        "S_loses_division": algebras["O"]["properties"]["normed_division"] and not algebras["S"]["properties"]["normed_division"] and algebras["S"]["has_zero_divisors"],
        "normed_division_exactly_R_C_H_O": normed == ["R", "C", "H", "O"],
        "finite_hurwitz_witness_reproduced": (
            normed == ["R", "C", "H", "O"]
            and algebras["R"]["properties"]["commutative"]
            and algebras["C"]["properties"]["commutative"]
            and not algebras["H"]["properties"]["commutative"]
            and not algebras["O"]["properties"]["associative"]
            and not algebras["S"]["properties"]["alternative"]
            and algebras["S"]["has_zero_divisors"]
        ),
        "normed_division_algebras_seen": normed,
    }


def build_shared_scalars(algebras: dict[str, Any], verdicts: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in ["R", "C", "H", "O", "S"]:
        for key in ["dim", "commutator_max", "associator_max", "alternator_residual", "alternator_xxy_max", "alternator_xyy_max", "norm_mult_residual"]:
            out[f"{name}.{key}"] = algebras[name][key]
        out[f"{name}.zero.signed_zero_divisor_count"] = algebras[name]["zero_divisor_check"]["signed_zero_divisor_count"]
    out["verdict.normed_division_count"] = len(verdicts["normed_division_algebras_seen"])
    return out


def build_shared_booleans(algebras: dict[str, Any], verdicts: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in ["R", "C", "H", "O", "S"]:
        for key in ["commutative", "associative", "alternative", "normed_division"]:
            out[f"{name}.property.{key}"] = bool(algebras[name]["properties"][key])
        out[f"{name}.has_zero_divisors"] = bool(algebras[name]["has_zero_divisors"])
    for key, value in verdicts.items():
        if isinstance(value, bool):
            out[f"verdict.{key}"] = value
    for key, value in controls.items():
        if isinstance(value, bool):
            out[f"control.{key}"] = value
    return out


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "missing_julia_reference",
            "shared_scalar_rows": [],
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jv = float(value)
        pv = float(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jv, "julia": pv, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    h_table = quaternion_table()
    o_prior = octonion_table()
    o_cd = cayley_dickson_double(h_table)
    s_table = cayley_dickson_double(o_cd)
    o_cd_vs_prior = py_float(jnp.max(jnp.abs(o_cd - o_prior)))
    algebras = {
        "R": analyze_algebra("R", "real_numbers", real_table()),
        "C": analyze_algebra("C", "complex_numbers", complex_table()),
        "H": analyze_algebra("H", "quaternions", h_table),
        "O": analyze_algebra("O", "octonions_cayley_dickson_checked_against_fano", o_cd),
        "S": analyze_algebra("S", "sedenions_cayley_dickson_from_O", s_table),
    }
    verdicts = property_loss_verdicts(algebras)
    controls = {
        "R_commutative_control_ok": algebras["R"]["properties"]["commutative"],
        "C_commutative_control_ok": algebras["C"]["properties"]["commutative"],
        "S_zero_divisor_control_ok": algebras["S"]["has_zero_divisors"],
        "O_cd_matches_prior_table": o_cd_vs_prior < TOL,
    }
    controls["control_miswired"] = not (
        controls["R_commutative_control_ok"]
        and controls["C_commutative_control_ok"]
        and controls["S_zero_divisor_control_ok"]
        and controls["O_cd_matches_prior_table"]
    )
    shared_scalars = build_shared_scalars(algebras, verdicts)
    s_checksum = table_checksum(s_table)
    shared_scalars["O_cd_vs_prior_max_abs_diff"] = o_cd_vs_prior
    shared_scalars["S.table.weighted_checksum"] = s_checksum["weighted_checksum"]
    shared_scalars["S.table.nonzero_entry_count"] = s_checksum["nonzero_entry_count"]
    shared_booleans = build_shared_booleans(algebras, verdicts, controls)
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_full_sim",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite R,C,H,O,S division-algebra ratchet witness only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind": "classical",
        "sim_class": "finite_division_algebra_geometry_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "probe_source": "basis vectors plus deterministic pseudorandom vectors; same formulas mirrored from Julia without plain NumPy compute",
        "tool_manifest": {
            "JAX": "load_bearing finite table construction, Cayley-Dickson doubling, and scalar checks",
            "jax.numpy": "load_bearing x64 array algebra and residual reductions",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive"},
        "controls": controls,
        "construction_checks": {
            "O_cd_vs_prior_max_abs_diff": o_cd_vs_prior,
            "O_cd_matches_prior_table": o_cd_vs_prior < TOL,
            "S_table_checksum": s_checksum,
        },
        "algebras": algebras,
        "property_loss_table": {name: algebras[name]["properties"] for name in ["R", "C", "H", "O", "S"]},
        "hopf_fibration_correspondence": hopf_fibration_rows(),
        "verdicts": verdicts,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "divergence_log": [
            "R and C remain commutative under the finite table check.",
            "H is the first rung with nonzero commutator residual.",
            "O keeps alternativity/normed-division in these probes but has nonzero basis associator residual.",
            "S has explicit signed two-term zero divisors and nonzero alternator residual.",
        ],
        "plain_sentence": (
            "The finite ladder reproduces the R,C,H,O normed-division rungs and shows S as the first sampled Cayley-Dickson non-division rung."
            if verdicts["finite_hurwitz_witness_reproduced"]
            else "The finite ladder did not reproduce the expected R,C,H,O/S property-loss pattern; inspect controls and witnesses."
        ),
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not verdicts["finite_hurwitz_witness_reproduced"]
        or bool(result["parity"]["stop_condition_fired"])
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    print("division_algebra_ratchet_ladder - JAX full sim")
    for name in ["R", "C", "H", "O", "S"]:
        a = result["algebras"][name]
        p = a["properties"]
        print(
            f"{name}: dim={a['dim']} commutator_max={a['commutator_max']} "
            f"associator_max={a['associator_max']} alternator_residual={a['alternator_residual']} "
            f"norm_mult_residual={a['norm_mult_residual']} has_zero_divisors={str(a['has_zero_divisors']).lower()} "
            f"commutative={str(p['commutative']).lower()} associative={str(p['associative']).lower()} "
            f"alternative={str(p['alternative']).lower()} normed_division={str(p['normed_division']).lower()}"
        )
    print(f"verdicts={json.dumps(result['verdicts'], sort_keys=True)}")
    print(f"controls={json.dumps(result['controls'], sort_keys=True)}")
    parity = result["parity"]
    print(f"parity_max_diff={parity['parity_max_diff']} within_1e-9={str(parity['within_1e_9']).lower()} max_diff_key={parity.get('max_diff_key')}")
    if parity["strict_divergence_gt_1e_6"] or parity["boolean_mismatches"] or parity["missing_keys"]:
        print("STOP: JAX and Julia disagree beyond the strict parity stop condition:")
        print(json.dumps({
            "strict_divergence_gt_1e_6": parity["strict_divergence_gt_1e_6"],
            "boolean_mismatches": parity["boolean_mismatches"],
            "missing_keys": parity["missing_keys"],
        }, indent=2, sort_keys=True))
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
