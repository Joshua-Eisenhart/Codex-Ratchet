#!/usr/bin/env python3
import jax

jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "sedenion_break_prelim"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "sedenion_break_prelim_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "sedenion_break_prelim_julia_results.json"
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


def quaternion_table() -> jax.Array:
    table = jnp.zeros((4, 4, 4), dtype=jnp.float64)
    table = add_identity(table, 4)
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


def prior_octonion_table() -> jax.Array:
    table = jnp.zeros((8, 8, 8), dtype=jnp.float64)
    table = add_identity(table, 8)
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


def conjugate(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)])
    return x * signs


def cayley_dickson_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a = x[:n]
    b = x[n:]
    c = y[:n]
    d = y[n:]
    first = multiply(parent, a, c) - multiply(parent, conjugate(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate(c))
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


def table_checksum(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    c = jnp.arange(1, dim + 1, dtype=jnp.float64)[:, None, None]
    a = jnp.arange(1, dim + 1, dtype=jnp.float64)[None, :, None]
    b = jnp.arange(1, dim + 1, dtype=jnp.float64)[None, None, :]
    weights = 1_000_003.0 * c + 1_009.0 * a + b
    nonzero = int(jax.device_get(jnp.count_nonzero(jnp.abs(table) > 0.0)))
    return {
        "dim": dim,
        "nonzero_entry_count": nonzero,
        "sum_abs_entries": py_float(jnp.sum(jnp.abs(table))),
        "weighted_checksum": py_float(jnp.sum(table * weights)),
    }


def terms_from_vector(v: jax.Array) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for idx in range(v.shape[0]):
        value = py_float(v[idx])
        if abs(value) > TOL:
            terms.append({"basis_index": idx, "coefficient": value, "label": f"e{idx}"})
    return terms


def pair_vector(dim: int, i: int, j: int, si: float = 1.0, sj: float = 1.0) -> jax.Array:
    v = jnp.zeros((dim,), dtype=jnp.float64)
    v = v.at[i].set(si)
    v = v.at[j].set(sj)
    return v


def pure_imaginary_pairs(dim: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(1, dim) for j in range(i + 1, dim)]


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


def zero_divisor_search(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    pairs = pure_imaginary_pairs(dim)
    pair_array = jnp.asarray(pairs, dtype=jnp.int32)
    left_pair_idx = jnp.repeat(jnp.arange(len(pairs), dtype=jnp.int32), len(pairs))
    right_pair_idx = jnp.tile(jnp.arange(len(pairs), dtype=jnp.int32), len(pairs))
    li = pair_array[left_pair_idx, 0]
    lj = pair_array[left_pair_idx, 1]
    rk = pair_array[right_pair_idx, 0]
    rl = pair_array[right_pair_idx, 1]
    plus_products = table[:, li, rk] + table[:, li, rl] + table[:, lj, rk] + table[:, lj, rl]
    plus_norms = jnp.linalg.norm(plus_products, axis=0)
    plus_mask = plus_norms < TOL
    plus_count = int(jax.device_get(jnp.sum(plus_mask)))
    min_plus_product_norm = py_float(jnp.min(plus_norms))

    sign_rows = [(i, j, si, sj) for i, j in pairs for si in (-1.0, 1.0) for sj in (-1.0, 1.0)]
    sign_array = jnp.asarray(sign_rows, dtype=jnp.float64)
    signed_left_idx = jnp.repeat(jnp.arange(len(sign_rows), dtype=jnp.int32), len(sign_rows))
    signed_right_idx = jnp.tile(jnp.arange(len(sign_rows), dtype=jnp.int32), len(sign_rows))
    sli = sign_array[signed_left_idx, 0].astype(jnp.int32)
    slj = sign_array[signed_left_idx, 1].astype(jnp.int32)
    ssi = sign_array[signed_left_idx, 2]
    ssj = sign_array[signed_left_idx, 3]
    srk = sign_array[signed_right_idx, 0].astype(jnp.int32)
    srl = sign_array[signed_right_idx, 1].astype(jnp.int32)
    ssk = sign_array[signed_right_idx, 2]
    ssl = sign_array[signed_right_idx, 3]
    signed_products = (
        (ssi * ssk)[None, :] * table[:, sli, srk]
        + (ssi * ssl)[None, :] * table[:, sli, srl]
        + (ssj * ssk)[None, :] * table[:, slj, srk]
        + (ssj * ssl)[None, :] * table[:, slj, srl]
    )
    signed_norms = jnp.linalg.norm(signed_products, axis=0)
    signed_mask = signed_norms < TOL
    signed_count = int(jax.device_get(jnp.sum(signed_mask)))
    min_signed_product_norm = py_float(jnp.min(signed_norms))

    plus_first: dict[str, Any] | None = None
    signed_first: dict[str, Any] | None = None
    plus_examples: list[dict[str, Any]] = []
    signed_examples: list[dict[str, Any]] = []

    if plus_count > 0:
        plus_first_index = int(jax.device_get(jnp.argmax(plus_mask)))
        plus_example_indices = [int(x) for x in jax.device_get(jnp.nonzero(plus_mask, size=ZERO_WITNESS_LIMIT, fill_value=-1)[0]) if int(x) >= 0]
        for idx in plus_example_indices:
            i, j = pairs[int(jax.device_get(left_pair_idx[idx]))]
            k, l = pairs[int(jax.device_get(right_pair_idx[idx]))]
            left = pair_vector(dim, i, j)
            right = pair_vector(dim, k, l)
            product = multiply(table, left, right)
            witness = zero_witness_dict("plus_two_term_pure_imaginary_pair", left, right, product)
            witness["pair_indices"] = {"left": [i, j], "right": [k, l]}
            plus_examples.append(witness)
            if idx == plus_first_index:
                plus_first = witness

    if signed_count > 0:
        signed_first_index = int(jax.device_get(jnp.argmax(signed_mask)))
        signed_example_indices = [int(x) for x in jax.device_get(jnp.nonzero(signed_mask, size=ZERO_WITNESS_LIMIT, fill_value=-1)[0]) if int(x) >= 0]
        for idx in signed_example_indices:
            li_row = sign_rows[int(jax.device_get(signed_left_idx[idx]))]
            ri_row = sign_rows[int(jax.device_get(signed_right_idx[idx]))]
            i, j, si, sj = li_row
            k, l, sk, sl = ri_row
            left = pair_vector(dim, i, j, si, sj)
            right = pair_vector(dim, k, l, sk, sl)
            product = multiply(table, left, right)
            witness = zero_witness_dict("signed_two_term_pure_imaginary_pair", left, right, product)
            witness["pair_indices"] = {"left": [i, j], "right": [k, l]}
            signed_examples.append(witness)
            if idx == signed_first_index:
                signed_first = witness

    return {
        "search_kind": "pure_imaginary_two_basis_term_pairs",
        "basis_index_range": [1, dim - 1],
        "ordered_plus_pair_search_size": len(pairs) ** 2,
        "ordered_signed_pair_search_size": len(pairs) ** 2 * 16,
        "plus_zero_divisor_count": plus_count,
        "signed_zero_divisor_count": signed_count,
        "min_plus_product_norm_seen": min_plus_product_norm,
        "min_signed_product_norm_seen": min_signed_product_norm,
        "plus_first_witness": plus_first,
        "signed_first_witness": signed_first,
        "plus_examples": plus_examples,
        "signed_examples": signed_examples,
        "zero_divisors_exist": plus_first is not None or signed_first is not None,
    }


def structure_checks(table: jax.Array, zero_search: dict[str, Any]) -> dict[str, Any]:
    dim = table.shape[0]
    vectors = probe_family(dim)
    max_alternative = 0.0
    max_alternative_witness: dict[str, Any] = {"kind": "none"}
    max_power = 0.0
    max_power_witness: dict[str, Any] = {"kind": "none"}
    max_flexible = 0.0
    max_flexible_witness: dict[str, Any] = {"kind": "none"}
    max_norm_residual = 0.0
    max_norm_witness: dict[str, Any] = {"kind": "none"}

    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = py_float(jnp.abs(jnp.linalg.norm(multiply(table, x, y)) - jnp.linalg.norm(x) * jnp.linalg.norm(y)))
        if residual > max_norm_residual:
            max_norm_residual = residual
            max_norm_witness = {"kind": "deterministic_pseudorandom_pair", "sample_idx": sample_idx, "residual": residual}

    if zero_search["plus_first_witness"] is not None:
        witness = zero_search["plus_first_witness"]
        residual = abs(float(witness["product_norm"]) - float(witness["left_norm"]) * float(witness["right_norm"]))
        if residual > max_norm_residual:
            max_norm_residual = residual
            max_norm_witness = {**witness, "norm_multiplicative_residual": residual}

    for ix, x in enumerate(vectors, start=1):
        x2 = multiply(table, x, x)
        power_residual = py_float(jnp.linalg.norm(multiply(table, x, multiply(table, x, x2)) - multiply(table, x2, x2)))
        if power_residual > max_power:
            max_power = power_residual
            max_power_witness = {"probe_index": ix, "residual": power_residual}
        for iy, y in enumerate(vectors, start=1):
            alternative_residual = py_float(jnp.linalg.norm(associator(table, x, x, y)))
            if alternative_residual > max_alternative:
                max_alternative = alternative_residual
                max_alternative_witness = {"x_probe_index": ix, "y_probe_index": iy, "residual": alternative_residual}
            flexible_residual = py_float(jnp.linalg.norm(multiply(table, x, multiply(table, y, x)) - multiply(table, multiply(table, x, y), x)))
            if flexible_residual > max_flexible:
                max_flexible = flexible_residual
                max_flexible_witness = {"a_probe_index": ix, "b_probe_index": iy, "residual": flexible_residual}

    return {
        "probe_count": len(vectors),
        "probe_kind": "basis_vectors_plus_deterministic_pseudorandom_vectors",
        "max_norm_mult_residual": max_norm_residual,
        "norm_multiplicative_holds_in_probe": max_norm_residual < TOL,
        "norm_multiplicative_fail_witness": max_norm_witness,
        "max_associator_xxy": max_alternative,
        "alternative_holds": max_alternative < TOL,
        "alternative_witness": max_alternative_witness,
        "max_power_four_residual": max_power,
        "power_associative_holds": max_power < TOL,
        "power_associative_witness": max_power_witness,
        "max_flexible_residual": max_flexible,
        "flexible_holds": max_flexible < TOL,
        "flexible_witness": max_flexible_witness,
    }


def build_shared_scalars(
    table_checks: dict[str, Any],
    o_checks: dict[str, Any],
    s_checks: dict[str, Any],
    o_zero: dict[str, Any],
    s_zero: dict[str, Any],
) -> dict[str, Any]:
    return {
        "tables.O_cd_vs_prior_max_abs_diff": table_checks["octonion_cd_vs_prior_max_abs_diff"],
        "tables.O_cd.weighted_checksum": table_checks["O_cd"]["weighted_checksum"],
        "tables.O_cd.nonzero_entry_count": table_checks["O_cd"]["nonzero_entry_count"],
        "tables.S.weighted_checksum": table_checks["S"]["weighted_checksum"],
        "tables.S.nonzero_entry_count": table_checks["S"]["nonzero_entry_count"],
        "O.dim": 8,
        "S.dim": 16,
        "O.zero.plus_zero_divisor_count": o_zero["plus_zero_divisor_count"],
        "S.zero.plus_zero_divisor_count": s_zero["plus_zero_divisor_count"],
        "S.zero.signed_zero_divisor_count": s_zero["signed_zero_divisor_count"],
        "O.max_norm_mult_residual": o_checks["max_norm_mult_residual"],
        "S.max_norm_mult_residual": s_checks["max_norm_mult_residual"],
        "O.max_associator_xxy": o_checks["max_associator_xxy"],
        "S.max_associator_xxy": s_checks["max_associator_xxy"],
        "S.max_power_four_residual": s_checks["max_power_four_residual"],
        "S.max_flexible_residual": s_checks["max_flexible_residual"],
    }


def build_shared_booleans(
    o_checks: dict[str, Any],
    s_checks: dict[str, Any],
    o_zero: dict[str, Any],
    s_zero: dict[str, Any],
    verdicts: dict[str, Any],
) -> dict[str, Any]:
    return {
        "O.zero_divisors_in_search": o_zero["zero_divisors_exist"],
        "S.zero_divisors_in_search": s_zero["zero_divisors_exist"],
        "O.norm_multiplicative_holds_in_probe": o_checks["norm_multiplicative_holds_in_probe"],
        "S.norm_multiplicative_holds_in_probe": s_checks["norm_multiplicative_holds_in_probe"],
        "O.alternative_holds": o_checks["alternative_holds"],
        "S.alternative_holds": s_checks["alternative_holds"],
        "S.power_associative_holds": s_checks["power_associative_holds"],
        "S.flexible_holds": s_checks["flexible_holds"],
        "sedenion_is_normed_division": verdicts["sedenion_is_normed_division"],
        "sedenion_zero_divisors": verdicts["sedenion_zero_divisors"],
        "ladder_stops_at_O": verdicts["ladder_stops_at_O"],
    }


def shared_scalar_diffs(jax_result: dict[str, Any], julia_reference: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    divergences_1e6: list[dict[str, Any]] = []
    boolean_mismatches: list[dict[str, Any]] = []
    missing_keys: list[str] = []

    for key, value in jax_result["shared_scalars"].items():
        if key not in julia_reference.get("shared_scalars", {}):
            missing_keys.append(key)
            continue
        jv = float(value)
        rv = float(julia_reference["shared_scalars"][key])
        diff = abs(jv - rv)
        max_diff = max(max_diff, diff)
        row = {"key": key, "jax": jv, "julia": rv, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            divergences_1e6.append(row)

    for key, value in jax_result["shared_booleans"].items():
        if key not in julia_reference.get("shared_booleans", {}):
            missing_keys.append(key)
            continue
        if bool(value) != bool(julia_reference["shared_booleans"][key]):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(julia_reference["shared_booleans"][key])})

    return {
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not missing_keys and not boolean_mismatches,
        "strict_divergence_gt_1e_6": divergences_1e6,
        "boolean_mismatches": boolean_mismatches,
        "missing_keys": missing_keys,
        "stop_condition_fired": bool(divergences_1e6) or bool(boolean_mismatches) or bool(missing_keys),
    }


def build_result() -> dict[str, Any]:
    h_table = quaternion_table()
    o_cd = cayley_dickson_double(h_table)
    o_prior = prior_octonion_table()
    s_table = cayley_dickson_double(o_cd)
    octonion_cd_diff = py_float(jnp.max(jnp.abs(o_cd - o_prior)))

    o_zero = zero_divisor_search(o_cd)
    s_zero = zero_divisor_search(s_table)
    o_checks = structure_checks(o_cd, o_zero)
    s_checks = structure_checks(s_table, s_zero)

    o_normed_division_alt = (
        not o_zero["zero_divisors_exist"]
        and o_checks["norm_multiplicative_holds_in_probe"]
        and o_checks["alternative_holds"]
    )
    s_normed_division = not s_zero["zero_divisors_exist"] and s_checks["norm_multiplicative_holds_in_probe"]
    verdicts = {
        "sedenion_is_normed_division": s_normed_division,
        "sedenion_zero_divisors": s_zero["zero_divisors_exist"],
        "ladder_stops_at_O": (
            o_normed_division_alt
            and not s_normed_division
            and s_zero["zero_divisors_exist"]
            and not s_checks["alternative_holds"]
        ),
    }

    table_checks = {
        "H": table_checksum(h_table),
        "O_cd": table_checksum(o_cd),
        "S": table_checksum(s_table),
        "octonion_cd_vs_prior_max_abs_diff": octonion_cd_diff,
        "octonion_cd_matches_prior_table": octonion_cd_diff < TOL,
    }
    shared_scalars = build_shared_scalars(table_checks, o_checks, s_checks, o_zero, s_zero)
    shared_booleans = build_shared_booleans(o_checks, s_checks, o_zero, s_zero, verdicts)

    stop_reasons: list[str] = []
    if octonion_cd_diff > STRICT_STOP_TOL:
        stop_reasons.append("O-level Cayley-Dickson construction disagrees with prior octonion table.")
    if o_zero["zero_divisors_exist"]:
        stop_reasons.append("O-level control found zero divisors; multiplication is miswired.")
    if not s_zero["zero_divisors_exist"]:
        stop_reasons.append("No concrete S zero divisor found in the bounded search set.")

    contrast = [
        {
            "algebra": "O",
            "dim": 8,
            "zero_divisors_in_search": o_zero["zero_divisors_exist"],
            "max_norm_mult_residual": o_checks["max_norm_mult_residual"],
            "alternative_holds": o_checks["alternative_holds"],
            "max_associator_xxy": o_checks["max_associator_xxy"],
            "normed_division_control": o_normed_division_alt,
        },
        {
            "algebra": "S",
            "dim": 16,
            "zero_divisors_in_search": s_zero["zero_divisors_exist"],
            "max_norm_mult_residual": s_checks["max_norm_mult_residual"],
            "alternative_holds": s_checks["alternative_holds"],
            "max_associator_xxy": s_checks["max_associator_xxy"],
            "normed_division_control": s_normed_division,
        },
    ]

    plain = (
        "At scratch_diagnostic ceiling, the normed-division ladder stops at O; S is a non-division Cayley-Dickson algebra with zero divisors, non-multiplicative norm, failed alternativity, and finite-probe power-associative/flexible behavior."
        if verdicts["ladder_stops_at_O"]
        else "At scratch_diagnostic ceiling, the O/S break did not pass all controls; inspect stop reasons and bounded search coverage."
    )

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_mirror",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "question": "Where does the Cayley-Dickson normed-division carrier ladder break one rung past octonions?",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "PRELIM finite Cayley-Dickson S diagnostic only; no forcing proof, basin, admission, engine, bridge, Axis0, or manifold closure claim",
        "sim_execution_kind": "classical",
        "sim_class": "carrier_break_control",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "norm_probe_count": NORM_PROBE_COUNT,
        "structure_probe_count": STRUCTURE_PROBE_COUNT,
        "construction": {
            "formula": "(a,b)(c,d) = (ac - conj(d)b, da + b conj(c))",
            "basis_order": "Cayley-Dickson doubling appends the new component after the parent component; indices are zero-based e0..e15.",
            "octonion_control": table_checks,
        },
        "tool_manifest": {
            "jax": "load_bearing finite table construction and scalar probes",
            "jax.numpy": "load_bearing mirror computation with x64 enabled",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "json": "supportive",
        },
        "divergence_log": [
            "O control: no zero divisors in bounded two-term search, norm multiplicativity residual near machine epsilon, alternative residual near machine epsilon.",
            "S break: concrete zero divisors found, norm multiplicativity fails, alternativity fails.",
        ],
        "fences": [
            "This reproduces Hurwitz known math as a finite witness, not a new claim.",
            "S is excluded as a normed-division carrier: no conserved norm means no probability readout, and zero divisors mean no clean inverse.",
            "The zero-divisor structure of S is a candidate separate object for annihilation/interference-style diagnostics, not promoted here.",
            "scratch_diagnostic only, promotion_allowed=false, no engine, Axis0, bridge, basin, forcing, admission, or manifold claim.",
            "The 64=2^6 Cayley-Dickson-vs-engine resonance is not asserted as identity.",
        ],
        "zero_divisor_search": {"O": o_zero, "S": s_zero},
        "checks": {"O": o_checks, "S": s_checks},
        "contrast": contrast,
        "verdicts": verdicts,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "control_status": {
            "octonion_cd_matches_prior_table": octonion_cd_diff < TOL,
            "O_zero_divisor_control_ok": not o_zero["zero_divisors_exist"],
            "S_zero_divisor_witness_found": s_zero["zero_divisors_exist"],
            "control_miswired": octonion_cd_diff > STRICT_STOP_TOL or o_zero["zero_divisors_exist"],
        },
        "stop_reasons": stop_reasons,
        "plain_sentence": plain,
    }

    if JULIA_REFERENCE_PATH.exists():
        julia_reference = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
        parity = shared_scalar_diffs(result, julia_reference)
    else:
        parity = {
            "shared_scalar_rows": [],
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_REFERENCE_PATH), "reason": "Julia reference JSON must exist before JAX parity can run."}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    result["parity"] = parity
    if parity["stop_condition_fired"]:
        result["stop_reasons"] = [*result["stop_reasons"], "JAX/Julia parity stop condition fired."]
    result["stop_condition_fired"] = bool(result["stop_reasons"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    print("Sedenion break prelim - JAX mirror")
    print(
        f"classification: {result['classification']} | "
        f"promotion_allowed: {str(result['promotion_allowed']).lower()} | "
        f"jax_enable_x64: {str(result['jax_enable_x64']).lower()}"
    )
    z = result["zero_divisor_search"]["S"]
    first_norm = "none" if z["plus_first_witness"] is None else z["plus_first_witness"]["product_norm"]
    print(
        f"S zero_divisors_exist={str(z['zero_divisors_exist']).lower()} "
        f"plus_count={z['plus_zero_divisor_count']} "
        f"signed_count={z['signed_zero_divisor_count']} "
        f"first_plus_product_norm={first_norm}"
    )
    for row in result["contrast"]:
        print(
            f"{row['algebra']}: dim={row['dim']} "
            f"zero_divisors_in_search={str(row['zero_divisors_in_search']).lower()} "
            f"max_norm_mult_residual={row['max_norm_mult_residual']} "
            f"alternative_holds={str(row['alternative_holds']).lower()} "
            f"max_associator_xxy={row['max_associator_xxy']} "
            f"normed_division_control={str(row['normed_division_control']).lower()}"
        )
    s_checks = result["checks"]["S"]
    print(
        f"S power_associative_holds={str(s_checks['power_associative_holds']).lower()} "
        f"max_power_four_residual={s_checks['max_power_four_residual']} "
        f"flexible_holds={str(s_checks['flexible_holds']).lower()} "
        f"max_flexible_residual={s_checks['max_flexible_residual']}"
    )
    parity = result["parity"]
    print(f"parity_max_diff={parity['parity_max_diff']} within_1e-9={str(parity['within_1e_9']).lower()}")
    if parity["strict_divergence_gt_1e_6"] or parity["boolean_mismatches"] or parity["missing_keys"]:
        print("STOP: JAX and Julia disagree beyond the strict parity stop condition:")
        print(json.dumps({
            "strict_divergence_gt_1e_6": parity["strict_divergence_gt_1e_6"],
            "boolean_mismatches": parity["boolean_mismatches"],
            "missing_keys": parity["missing_keys"],
        }, indent=2, sort_keys=True))
    print(f"verdicts={json.dumps(result['verdicts'], sort_keys=True)}")
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")
    if not result["stop_condition_fired"]:
        print("CODEX2_SEDENION_DONE")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
