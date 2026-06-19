#!/usr/bin/env python3
import jax

jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "octonion_admissibility_prelim"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "octonion_admissibility_prelim_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "octonion_admissibility_prelim_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
NORM_PROBE_COUNT = 64
STRUCTURE_PROBE_COUNT = 12
FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]
OFFDIAG_PAIRS = [(0, 1), (0, 2), (1, 2)]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def setprod(table: jax.Array, a: int, b: int, c: int, s: float) -> jax.Array:
    return table.at[c, a, b].set(s)


def add_identity(table: jax.Array, dim: int) -> jax.Array:
    for a in range(dim):
        table = setprod(table, 0, a, a, 1.0)
        table = setprod(table, a, 0, a, 1.0)
    return table


def real_table() -> jax.Array:
    table = jnp.zeros((1, 1, 1), dtype=jnp.float64)
    return setprod(table, 0, 0, 0, 1.0)


def complex_table() -> jax.Array:
    table = jnp.zeros((2, 2, 2), dtype=jnp.float64)
    table = add_identity(table, 2)
    return setprod(table, 1, 1, 0, -1.0)


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


def octonion_table() -> jax.Array:
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


def associator(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def commutator_max(table: jax.Array) -> float:
    dim = table.shape[0]
    max_seen = 0.0
    for a in range(dim):
        for b in range(dim):
            value = py_float(jnp.linalg.norm(multiply(table, basis(dim, a), basis(dim, b)) - multiply(table, basis(dim, b), basis(dim, a))))
            max_seen = max(max_seen, value)
    return max_seen


def associator_max(table: jax.Array) -> float:
    dim = table.shape[0]
    max_seen = 0.0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                value = py_float(jnp.linalg.norm(associator(table, basis(dim, a), basis(dim, b), basis(dim, c))))
                max_seen = max(max_seen, value)
    return max_seen


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


def norm_mult_residual(table: jax.Array) -> float:
    dim = table.shape[0]
    max_seen = 0.0
    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = py_float(jnp.abs(jnp.linalg.norm(multiply(table, x, y)) - jnp.linalg.norm(x) * jnp.linalg.norm(y)))
        max_seen = max(max_seen, residual)
    return max_seen


def has_zero_divisors_sampled(table: jax.Array) -> tuple[bool, float, dict[str, Any] | None]:
    dim = table.shape[0]
    min_product_norm = float("inf")
    for a in range(dim):
        for b in range(dim):
            product_norm = py_float(jnp.linalg.norm(multiply(table, basis(dim, a), basis(dim, b))))
            min_product_norm = min(min_product_norm, product_norm)
            if product_norm < TOL:
                return True, min_product_norm, {"kind": "basis_pair", "a": a, "b": b, "product_norm": product_norm}
    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        if py_float(jnp.linalg.norm(x)) > TOL and py_float(jnp.linalg.norm(y)) > TOL:
            product_norm = py_float(jnp.linalg.norm(multiply(table, x, y)))
            min_product_norm = min(min_product_norm, product_norm)
            if product_norm < TOL:
                return True, min_product_norm, {"kind": "probe_pair", "sample_idx": sample_idx, "product_norm": product_norm}
    return False, min_product_norm, None


def analyze_algebra(name: str, label: str, table: jax.Array) -> dict[str, Any]:
    comm = commutator_max(table)
    assoc = associator_max(table)
    norm_resid = norm_mult_residual(table)
    has_zero, min_product_norm, zero_witness = has_zero_divisors_sampled(table)
    return {
        "name": name,
        "label": label,
        "dim": table.shape[0],
        "commutator_max": comm,
        "associator_max": assoc,
        "norm_mult_residual": norm_resid,
        "has_zero_divisors": has_zero,
        "zero_divisor_check": {
            "kind": "basis_pairs_plus_deterministic_pseudorandom_nonzero_probe_pairs",
            "probe_count": NORM_PROBE_COUNT,
            "min_product_norm_seen": min_product_norm,
            "witness": zero_witness,
        },
        "n01_pass": comm > TOL,
        "assoc_pass": assoc < TOL,
        "normed_division": norm_resid < TOL and not has_zero,
    }


def octonion_structure_checks(table: jax.Array) -> dict[str, Any]:
    vectors = probe_family(8)
    max_xxy = 0.0
    max_xyy = 0.0
    max_xxx = 0.0
    max_power_four = 0.0
    for x in vectors:
        x2 = multiply(table, x, x)
        max_xxx = max(max_xxx, py_float(jnp.linalg.norm(associator(table, x, x, x))))
        left_four = multiply(table, x, multiply(table, x, x2))
        right_four = multiply(table, x2, x2)
        max_power_four = max(max_power_four, py_float(jnp.linalg.norm(left_four - right_four)))
        for y in vectors:
            max_xxy = max(max_xxy, py_float(jnp.linalg.norm(associator(table, x, x, y))))
            max_xyy = max(max_xyy, py_float(jnp.linalg.norm(associator(table, x, y, y))))
    return {
        "alternative": max(max_xxy, max_xyy) < TOL,
        "power_associative": max(max_xxx, max_power_four) < TOL,
        "max_associator_xxy": max_xxy,
        "max_associator_xyy": max_xyy,
        "max_associator_xxx": max_xxx,
        "max_power_four_residual": max_power_four,
        "probe_count": len(vectors),
        "probe_kind": "basis_vectors_plus_deterministic_pseudorandom_vectors",
    }


def oct_conj(x: jax.Array) -> jax.Array:
    signs = jnp.asarray([1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)
    return x * signs


def j3_zero() -> jax.Array:
    return jnp.zeros((3, 3, 8), dtype=jnp.float64)


def j3_from_coords(coords: jax.Array) -> jax.Array:
    matrix = j3_zero()
    for i in range(3):
        matrix = matrix.at[i, i, 0].set(coords[i])
    idx = 3
    for i, j in OFFDIAG_PAIRS:
        v = coords[idx:idx + 8]
        matrix = matrix.at[i, j, :].set(v)
        matrix = matrix.at[j, i, :].set(oct_conj(v))
        idx += 8
    return matrix


def j3_coords_basis(idx: int) -> jax.Array:
    return j3_from_coords(jnp.eye(27, dtype=jnp.float64)[idx])


def j3_offdiag(i: int, j: int, v: jax.Array) -> jax.Array:
    matrix = j3_zero()
    matrix = matrix.at[i, j, :].set(v)
    matrix = matrix.at[j, i, :].set(oct_conj(v))
    return matrix


def j3_probe_coords(sample_idx: int, side: int) -> jax.Array:
    vals: list[float] = []
    for j in range(1, 28):
        raw = (
            (sample_idx + 23) * (j + 11) * (side + 3) * 29
            + j ** 2 * 17
            + sample_idx * 31
            + side * 7
        ) % 113
        vals.append((float(raw) - 56.0) / 41.0)
    return jnp.asarray(vals, dtype=jnp.float64)


def j3_matmul(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    out = j3_zero()
    for i in range(3):
        for k in range(3):
            acc = jnp.zeros((8,), dtype=jnp.float64)
            for j in range(3):
                acc = acc + multiply(table, a[i, j], b[j, k])
            out = out.at[i, k, :].set(acc)
    return out


def jordan(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    return 0.5 * (j3_matmul(table, a, b) + j3_matmul(table, b, a))


def j3_trace(a: jax.Array) -> float:
    return py_float(a[0, 0, 0] + a[1, 1, 0] + a[2, 2, 0])


def j3_residual(a: jax.Array, b: jax.Array) -> float:
    return py_float(jnp.linalg.norm(jnp.ravel(a - b)))


def j3_trace_square_expected(a: jax.Array) -> float:
    total = a[0, 0, 0] ** 2 + a[1, 1, 0] ** 2 + a[2, 2, 0] ** 2
    for i, j in OFFDIAG_PAIRS:
        total = total + 2.0 * jnp.sum(a[i, j, :] ** 2)
    return py_float(total)


def j3_probe_family() -> list[jax.Array]:
    matrices = [j3_coords_basis(idx) for idx in range(27)]
    for sample_idx in range(1, STRUCTURE_PROBE_COUNT + 1):
        matrices.append(j3_from_coords(j3_probe_coords(sample_idx, 5)))
    return matrices


def jordan_associator(table: jax.Array, a: jax.Array, b: jax.Array, c: jax.Array) -> jax.Array:
    return jordan(table, jordan(table, a, b), c) - jordan(table, a, jordan(table, b, c))


def jordan_associative_witness(table: jax.Array) -> tuple[float, dict[str, Any]]:
    explicit = [
        (j3_offdiag(0, 1, basis(8, 1)), j3_offdiag(1, 2, basis(8, 2)), j3_offdiag(0, 2, basis(8, 4))),
        (j3_offdiag(0, 1, basis(8, 1)), j3_offdiag(1, 2, basis(8, 4)), j3_offdiag(0, 2, basis(8, 2))),
    ]
    max_seen = 0.0
    best: dict[str, Any] = {"kind": "none"}
    for idx, (a, b, c) in enumerate(explicit, start=1):
        residual = py_float(jnp.linalg.norm(jnp.ravel(jordan_associator(table, a, b, c))))
        if residual > max_seen:
            max_seen = residual
            best = {"kind": "explicit_offdiag_cycle", "index": idx, "residual": residual}
    if max_seen > TOL:
        return max_seen, best
    probes = j3_probe_family()
    for ia, a in enumerate(probes, start=1):
        for ib, b in enumerate(probes, start=1):
            for ic, c in enumerate(probes, start=1):
                residual = py_float(jnp.linalg.norm(jnp.ravel(jordan_associator(table, a, b, c))))
                if residual > max_seen:
                    max_seen = residual
                    best = {"kind": "probe_search", "ia": ia, "ib": ib, "ic": ic, "residual": residual}
                if max_seen > TOL:
                    return max_seen, best
    return max_seen, best


def j3_checks(table: jax.Array) -> dict[str, Any]:
    probes = j3_probe_family()
    max_comm = 0.0
    max_power = 0.0
    max_trace_square_residual = 0.0
    min_nonzero_trace_square = float("inf")
    min_nonzero_sum_square_trace = float("inf")
    min_nonzero_sum_square_norm = float("inf")

    for a in probes:
        a2 = jordan(table, a, a)
        left_four = jordan(table, a, jordan(table, a, a2))
        right_four = jordan(table, a2, a2)
        max_power = max(max_power, j3_residual(left_four, right_four))

        expected_trace = j3_trace_square_expected(a)
        trace_square = j3_trace(a2)
        max_trace_square_residual = max(max_trace_square_residual, abs(trace_square - expected_trace))
        if expected_trace > TOL:
            min_nonzero_trace_square = min(min_nonzero_trace_square, trace_square)

    pair_limit = min(len(probes), 16)
    for ia in range(pair_limit):
        for ib in range(pair_limit):
            max_comm = max(max_comm, j3_residual(jordan(table, probes[ia], probes[ib]), jordan(table, probes[ib], probes[ia])))

    for sample_idx in range(1, STRUCTURE_PROBE_COUNT + 1):
        sumsq = j3_zero()
        expected_sum_trace = 0.0
        all_zero_inputs = True
        for side in range(1, 4):
            a = j3_from_coords(j3_probe_coords(sample_idx, side))
            all_zero_inputs = all_zero_inputs and py_float(jnp.linalg.norm(jnp.ravel(a))) < TOL
            sumsq = sumsq + jordan(table, a, a)
            expected_sum_trace += j3_trace_square_expected(a)
        if not all_zero_inputs:
            min_nonzero_sum_square_trace = min(min_nonzero_sum_square_trace, j3_trace(sumsq))
            min_nonzero_sum_square_norm = min(min_nonzero_sum_square_norm, py_float(jnp.linalg.norm(jnp.ravel(sumsq))))
            max_trace_square_residual = max(max_trace_square_residual, abs(j3_trace(sumsq) - expected_sum_trace))

    assoc_witness_residual, assoc_witness = jordan_associative_witness(table)

    u = basis(8, 1)
    p = j3_zero()
    p = p.at[0, 0, 0].set(0.5)
    p = p.at[1, 1, 0].set(0.5)
    p = p.at[0, 1, :].set(-0.5 * u)
    p = p.at[1, 0, :].set(oct_conj(p[0, 1, :]))
    p2 = jordan(table, p, p)
    rank1_residual = j3_residual(p2, p)
    rank1_trace_residual = abs(j3_trace(p) - 1.0)

    return {
        "real_dim": 3 + 3 * 8,
        "jordan_commutative": max_comm < TOL,
        "jordan_commutative_residual": max_comm,
        "power_associative": max_power < TOL,
        "power_associative_residual": max_power,
        "jordan_associative": assoc_witness_residual < TOL,
        "jordan_associative_witness_residual": assoc_witness_residual,
        "jordan_associative_witness": assoc_witness,
        "formally_real": (
            max_trace_square_residual < TOL
            and min_nonzero_trace_square > TOL
            and min_nonzero_sum_square_trace > TOL
            and min_nonzero_sum_square_norm > TOL
        ),
        "formally_real_test": {
            "kind": "finite_trace_square_identity_plus_nonzero_random_sum_square_probe",
            "max_trace_square_residual": max_trace_square_residual,
            "min_nonzero_trace_square": min_nonzero_trace_square,
            "min_nonzero_sum_square_trace": min_nonzero_sum_square_trace,
            "min_nonzero_sum_square_norm": min_nonzero_sum_square_norm,
            "random_set_count": STRUCTURE_PROBE_COUNT,
        },
        "rank1_idempotent_exists": rank1_residual < TOL and rank1_trace_residual < TOL,
        "rank1_idempotent_residual": rank1_residual,
        "rank1_trace_residual": rank1_trace_residual,
        "rank1_idempotent": {
            "kind": "offdiagonal_unit_octonion_projection",
            "trace": j3_trace(p),
            "imaginary_offdiag_norm": py_float(jnp.linalg.norm(p[0, 1, 1:])),
            "residual": rank1_residual,
        },
        "probe_count": len(probes),
    }


def filter_verdicts(algebras: dict[str, Any]) -> dict[str, Any]:
    survivors_no_assoc = [key for key in ["R", "C", "H", "O"] if algebras[key]["n01_pass"] and algebras[key]["normed_division"]]
    survivors_with_assoc = [
        key for key in ["R", "C", "H", "O"] if algebras[key]["n01_pass"] and algebras[key]["normed_division"] and algebras[key]["assoc_pass"]
    ]
    return {
        "survivors_NO_assoc": survivors_no_assoc,
        "survivors_with_assoc": survivors_with_assoc,
        "contrast_plain": "with associativity required -> {H}; without associativity -> {H,O}; O prior exclusion is the associativity axiom, not N01",
        "octonion_prior_exclusion_discriminator": "associativity_axiom",
    }


def build_shared_scalars(algebras: dict[str, Any], oct_props: dict[str, Any], j3: dict[str, Any]) -> dict[str, Any]:
    scalars: dict[str, Any] = {}
    for key in ["R", "C", "H", "O"]:
        for metric in ["dim", "commutator_max", "associator_max", "norm_mult_residual"]:
            scalars[f"part_a.{key}.{metric}"] = algebras[key][metric]
    for metric in ["max_associator_xxy", "max_associator_xyy", "max_associator_xxx", "max_power_four_residual"]:
        scalars[f"part_a.O.{metric}"] = oct_props[metric]
    for metric in [
        "real_dim",
        "jordan_commutative_residual",
        "power_associative_residual",
        "jordan_associative_witness_residual",
        "rank1_idempotent_residual",
        "rank1_trace_residual",
    ]:
        scalars[f"part_b.{metric}"] = j3[metric]
    scalars["part_b.formally_real.max_trace_square_residual"] = j3["formally_real_test"]["max_trace_square_residual"]
    scalars["part_b.formally_real.min_nonzero_trace_square"] = j3["formally_real_test"]["min_nonzero_trace_square"]
    scalars["part_b.formally_real.min_nonzero_sum_square_trace"] = j3["formally_real_test"]["min_nonzero_sum_square_trace"]
    return scalars


def build_shared_booleans(algebras: dict[str, Any], oct_props: dict[str, Any], j3: dict[str, Any], verdicts: dict[str, Any]) -> dict[str, Any]:
    booleans: dict[str, Any] = {}
    for key in ["R", "C", "H", "O"]:
        for metric in ["n01_pass", "assoc_pass", "normed_division"]:
            booleans[f"part_a.{key}.{metric}"] = algebras[key][metric]
    booleans["part_a.O.alternative"] = oct_props["alternative"]
    booleans["part_a.O.power_associative"] = oct_props["power_associative"]
    booleans["part_a.survivors_no_assoc_is_HO"] = verdicts["survivors_NO_assoc"] == ["H", "O"]
    booleans["part_a.survivors_with_assoc_is_H"] = verdicts["survivors_with_assoc"] == ["H"]
    for metric in ["jordan_commutative", "power_associative", "jordan_associative", "formally_real", "rank1_idempotent_exists"]:
        booleans[f"part_b.{metric}"] = j3[metric]
    return booleans


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
    tables = {
        "R": real_table(),
        "C": complex_table(),
        "H": quaternion_table(),
        "O": octonion_table(),
    }
    algebras = {
        "R": analyze_algebra("R", "real_numbers", tables["R"]),
        "C": analyze_algebra("C", "complex_numbers", tables["C"]),
        "H": analyze_algebra("H", "quaternions", tables["H"]),
        "O": analyze_algebra("O", "octonions", tables["O"]),
    }
    oct_props = octonion_structure_checks(tables["O"])
    part_a = filter_verdicts(algebras)
    part_b = j3_checks(tables["O"])
    shared_scalars = build_shared_scalars(algebras, oct_props, part_b)
    shared_booleans = build_shared_booleans(algebras, oct_props, part_b, part_a)

    controls = {
        "R_commutative_control_ok": not algebras["R"]["n01_pass"],
        "C_commutative_control_ok": not algebras["C"]["n01_pass"],
        "J3O_nonassociative_control_ok": not part_b["jordan_associative"],
        "survivor_contrast_ok": part_a["survivors_with_assoc"] == ["H"] and part_a["survivors_NO_assoc"] == ["H", "O"],
        "octonion_alternative_power_ok": oct_props["alternative"] and oct_props["power_associative"],
    }
    controls["control_miswired"] = not (
        controls["R_commutative_control_ok"]
        and controls["C_commutative_control_ok"]
        and controls["J3O_nonassociative_control_ok"]
        and controls["survivor_contrast_ok"]
        and controls["octonion_alternative_power_ok"]
    )

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_mirror",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "question": "Do octonions survive the N01+normed-division filter when associativity is dropped, and does the octonionic density matrix algebra J3(O) pass finite Jordan checks?",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "PRELIM octonion/J3(O) finite diagnostic only; no forcing proof, basin, admission, engine, bridge, Axis0, or manifold closure claim",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "norm_probe_count": NORM_PROBE_COUNT,
        "structure_probe_count": STRUCTURE_PROBE_COUNT,
        "probe_source": "basis vectors plus deterministic pseudorandom real vectors for reproducible Julia/JAX parity",
        "fences": [
            "Admitting O under the dropped-associativity filter does not force it; it shows associativity was the discriminator, nothing more.",
            "The engine may still require associativity for its operator/probe algebra; that remains open.",
            "scratch_diagnostic only, promotion_allowed=false, no Axis0/bridge/manifold/engine claim.",
            "J3(O) existing as a Jordan algebra is a known math fact reproduced here as a finite witness, not a new physics claim.",
        ],
        "root_constraints": {
            "F01": "finite explicit real multiplication tables / structure constants for R,C,H,O and finite J3(O) coordinate maps",
            "N01": "basis-pair commutator norm of scalar algebra multiplication table; associativity deliberately omitted in Part A no-assoc filter",
        },
        "algebras": algebras,
        "part_a": {**part_a, "octonion_properties": oct_props},
        "part_b": part_b,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "control_status": controls,
        "plain_sentence": (
            "At scratch_diagnostic ceiling, the octonion/J3(O) diagnostic did not pass all controls; inspect control_status before using the result."
            if controls["control_miswired"]
            else "At scratch_diagnostic ceiling, O is admissible under N01+normed-division when associativity is not required, and J3(O) exists as a formally-real nonassociative Jordan algebra finite witness; this is not an engine/admission/bridge/manifold claim."
        ),
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
    result["stop_condition_fired"] = controls["control_miswired"] or bool(parity["stop_condition_fired"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    print("Octonion admissibility prelim - JAX mirror")
    print(
        f"classification: {result['classification']} | "
        f"promotion_allowed: {str(result['promotion_allowed']).lower()} | "
        f"jax_enable_x64: {str(result['jax_enable_x64']).lower()}"
    )
    for key in ["R", "C", "H", "O"]:
        a = result["algebras"][key]
        print(
            f"{key}: dim={a['dim']} "
            f"commutator_max={a['commutator_max']} "
            f"associator_max={a['associator_max']} "
            f"norm_mult_residual={a['norm_mult_residual']} "
            f"n01_pass={str(a['n01_pass']).lower()} "
            f"normed_division={str(a['normed_division']).lower()}"
        )
    props = result["part_a"]["octonion_properties"]
    print(
        f"survivors_with_assoc={json.dumps(result['part_a']['survivors_with_assoc'])} "
        f"survivors_NO_assoc={json.dumps(result['part_a']['survivors_NO_assoc'])}"
    )
    print(
        f"O alternative={str(props['alternative']).lower()} "
        f"max_xxy={props['max_associator_xxy']} max_xyy={props['max_associator_xyy']} "
        f"power_associative={str(props['power_associative']).lower()} "
        f"max_power_four_residual={props['max_power_four_residual']}"
    )
    j3 = result["part_b"]
    print(
        f"J3(O): real_dim={j3['real_dim']} "
        f"jordan_commutative={str(j3['jordan_commutative']).lower()} "
        f"power_associative={str(j3['power_associative']).lower()} "
        f"jordan_associative={str(j3['jordan_associative']).lower()} "
        f"formally_real={str(j3['formally_real']).lower()} "
        f"rank1_idempotent_exists={str(j3['rank1_idempotent_exists']).lower()}"
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
    if result["control_status"]["control_miswired"]:
        print("STOP: octonion/J3(O) control failed; inspect multiplication/Jordan wiring.")
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")
    if not result["stop_condition_fired"]:
        print("CODEX2_OCTONION_DONE")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
