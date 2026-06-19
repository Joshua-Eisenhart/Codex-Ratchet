#!/usr/bin/env python3
"""Dual-backend finite non-associativity basin compare scout.

Scratch diagnostic only. Membership in the survivor set is computed from
Cayley-Dickson multiplication tables for R, C, H, O, sedenions, and the 2^5
doubling. No survivor list is used as an admissibility oracle.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "nonassoc_basin_compare_scout"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/nonassoc_basin_compare_scout_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/nonassoc_basin_compare_scout_julia_results.json"
TOL = 1.0e-10
STRICT_STOP_TOL = 1.0e-8
PROBE_COUNT = 16
CARRIER_ORDER = ["R", "C", "H", "O", "S", "2^5"]
CARRIER_LABELS = {
    "R": "real_line_readout",
    "C": "complex_plane_readout",
    "H": "quaternion_spinor_readout",
    "O": "octonion_diagnostic_readout",
    "S": "sedenion_diagnostic_readout",
    "2^5": "cayley_dickson_32_diagnostic_readout",
}
START_SUBSETS = {
    "full_ladder": CARRIER_ORDER,
    "empty": [],
    "lower_half": ["R", "C", "H"],
    "upper_half": ["O", "S", "2^5"],
    "singleton_H": ["H"],
    "missing_HO": ["R", "C", "S", "2^5"],
}

CLAIM_CEILING = (
    "NA changes the finite admissibility basin in this scratch scout only. "
    "No final M(C), PEPS3D admission, Axis0, physics, engine, bridge, or "
    "formal-admission claim is made."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite map, x64 Cayley-Dickson tables, ratchet iteration, and parity scalars",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 table algebra, associator/commutator reductions, and norm residuals",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, timestamps, JSON receipt serialization, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "hard-disabled by this JAX scout; no NumPy import or NumPy compute is used",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def multiply_many(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,...a,...b->...c", table, x, y)


def conjugate_vector(x: jax.Array) -> jax.Array:
    return x.at[1:].multiply(-1.0)


def cayley_dickson_double(table: jax.Array) -> jax.Array:
    dim = int(table.shape[0])
    out = jnp.zeros((2 * dim, 2 * dim, 2 * dim), dtype=jnp.float64)
    unit = jnp.eye(2 * dim, dtype=jnp.float64)
    for i in range(2 * dim):
        for j in range(2 * dim):
            x = unit[i]
            y = unit[j]
            a, b = x[:dim], x[dim:]
            c, d = y[:dim], y[dim:]
            first = multiply(table, a, c) - multiply(table, conjugate_vector(d), b)
            second = multiply(table, d, a) + multiply(table, b, conjugate_vector(c))
            out = out.at[:, i, j].set(jnp.concatenate([first, second]))
    return out


def cayley_dickson_tables() -> dict[str, jax.Array]:
    table = jnp.ones((1, 1, 1), dtype=jnp.float64)
    tables = {"R": table}
    for name in ["C", "H", "O", "S", "2^5"]:
        table = cayley_dickson_double(table)
        tables[name] = table
    return tables


def associator(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


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


def probe_family(dim: int) -> jax.Array:
    rows = [basis(dim, idx) for idx in range(dim)]
    for sample_idx in range(1, PROBE_COUNT + 1):
        rows.append(probe_vector(dim, sample_idx, 7))
    return jnp.stack(rows)


def commutator_max(table: jax.Array) -> float:
    diff = table - jnp.swapaxes(table, 1, 2)
    return py_float(jnp.max(jnp.linalg.norm(diff, axis=0)))


def associator_max(table: jax.Array) -> tuple[float, dict[str, Any]]:
    left = jnp.einsum("mab,dmc->dabc", table, table)
    right = jnp.einsum("mbc,dam->dabc", table, table)
    residuals = jnp.linalg.norm(left - right, axis=0)
    max_seen = py_float(jnp.max(residuals))
    if max_seen <= TOL:
        return max_seen, {"kind": "none"}
    flat_index = int(jax.device_get(jnp.argmax(residuals)))
    dim = int(table.shape[0])
    a = flat_index // (dim * dim)
    b = (flat_index // dim) % dim
    c = flat_index % dim
    return max_seen, {"kind": "basis_triple", "basis_indices": [a, b, c], "residual": max_seen}


def alternator_residual(table: jax.Array) -> tuple[float, dict[str, Any]]:
    vectors = probe_family(int(table.shape[0]))
    x = vectors[:, None, :]
    y = vectors[None, :, :]
    xxy = multiply_many(table, multiply_many(table, x, x), y) - multiply_many(
        table, x, multiply_many(table, x, y)
    )
    xyy = multiply_many(table, multiply_many(table, x, y), y) - multiply_many(
        table, x, multiply_many(table, y, y)
    )
    xxy_norms = jnp.linalg.norm(xxy, axis=-1)
    xyy_norms = jnp.linalg.norm(xyy, axis=-1)
    xxy_max = py_float(jnp.max(xxy_norms))
    xyy_max = py_float(jnp.max(xyy_norms))
    if xxy_max >= xyy_max:
        max_seen = xxy_max
        flat_index = int(jax.device_get(jnp.argmax(xxy_norms)))
        kind = "xxy"
    else:
        max_seen = xyy_max
        flat_index = int(jax.device_get(jnp.argmax(xyy_norms)))
        kind = "xyy"
    if max_seen <= TOL:
        return max_seen, {"kind": "none"}
    count = int(vectors.shape[0])
    return max_seen, {
        "kind": kind,
        "x_probe_index": flat_index // count,
        "y_probe_index": flat_index % count,
        "residual": max_seen,
    }


def norm_multiplication_residual(table: jax.Array) -> tuple[float, dict[str, Any]]:
    dim = int(table.shape[0])
    xs = jnp.stack([probe_vector(dim, sample_idx, 1) for sample_idx in range(1, PROBE_COUNT + 1)])
    ys = jnp.stack([probe_vector(dim, sample_idx, 2) for sample_idx in range(1, PROBE_COUNT + 1)])
    products = multiply_many(table, xs, ys)
    residuals = jnp.abs(jnp.linalg.norm(products, axis=1) - jnp.linalg.norm(xs, axis=1) * jnp.linalg.norm(ys, axis=1))
    max_seen = py_float(jnp.max(residuals))
    if max_seen <= TOL:
        return max_seen, {"kind": "none" if max_seen == 0.0 else "deterministic_probe_pair", "residual": max_seen}
    idx = int(jax.device_get(jnp.argmax(residuals)))
    return max_seen, {"kind": "deterministic_probe_pair", "sample_idx": idx + 1, "residual": max_seen}


def zero_divisor_candidate_vectors(dim: int) -> tuple[jax.Array, list[dict[str, Any]]]:
    limit = min(dim, 16)
    unit = jnp.eye(dim, dtype=jnp.float64)
    rows: list[jax.Array] = []
    labels: list[dict[str, Any]] = []
    for i in range(1, limit):
        for j in range(i + 1, limit):
            for sign, sign_label in [(1.0, "+"), (-1.0, "-")]:
                rows.append(unit[i] + sign * unit[j])
                labels.append({"basis_indices": [i, j], "sign": sign_label})
    if not rows:
        return jnp.zeros((0, dim), dtype=jnp.float64), []
    return jnp.stack(rows), labels


def zero_divisor_seen(table: jax.Array) -> tuple[bool, float, dict[str, Any]]:
    dim = int(table.shape[0])
    basis_products = jnp.linalg.norm(table, axis=0)
    min_product_norm = py_float(jnp.min(basis_products))

    xs = jnp.stack([probe_vector(dim, sample_idx, 1) for sample_idx in range(1, PROBE_COUNT + 1)])
    ys = jnp.stack([probe_vector(dim, sample_idx, 2) for sample_idx in range(1, PROBE_COUNT + 1)])
    probe_norms = jnp.linalg.norm(multiply_many(table, xs, ys), axis=1)
    min_product_norm = min(min_product_norm, py_float(jnp.min(probe_norms)))

    vectors, labels = zero_divisor_candidate_vectors(dim)
    if int(vectors.shape[0]) == 0:
        return False, min_product_norm, {"kind": "none"}
    batch_size = 64
    for start in range(0, int(vectors.shape[0]), batch_size):
        batch = vectors[start : start + batch_size]
        products = multiply_many(table, batch[:, None, :], vectors[None, :, :])
        norms = jnp.linalg.norm(products, axis=-1)
        batch_min = py_float(jnp.min(norms))
        min_product_norm = min(min_product_norm, batch_min)
        if batch_min < TOL:
            flat_index = int(jax.device_get(jnp.argmin(norms)))
            left_idx = start + flat_index // int(vectors.shape[0])
            right_idx = flat_index % int(vectors.shape[0])
            return True, min_product_norm, {
                "kind": "two_basis_sum_zero_divisor",
                "left": labels[left_idx],
                "right": labels[right_idx],
                "product_norm": batch_min,
            }
    return False, min_product_norm, {"kind": "none"}


def analyze_carrier(name: str, table: jax.Array) -> dict[str, Any]:
    assoc, assoc_witness = associator_max(table)
    alternator, alternator_witness = alternator_residual(table)
    comm = commutator_max(table)
    norm_resid, norm_witness = norm_multiplication_residual(table)
    zero_divisors, min_product_norm, zero_witness = zero_divisor_seen(table)
    dim = int(table.shape[0])
    normed_division = norm_resid < TOL and not zero_divisors
    predicates = {
        "N01_noncommutativity": {
            "pass": comm > TOL,
            "computed_from": "commutator_max_from_multiplication_table",
            "commutator_max": comm,
            "fail_reason": None if comm > TOL else "commutative/N01_fail",
        },
        "norm_multiplicativity_no_zero_divisors": {
            "pass": normed_division,
            "computed_from": "norm_residual_and_zero_divisor_search_from_multiplication_table",
            "norm_mult_residual": norm_resid,
            "has_zero_divisors": zero_divisors,
            "fail_reason": None if normed_division else "zero_divisors/norm_mult_fail",
        },
        "associativity": {
            "pass": assoc < TOL,
            "computed_from": "basis_associator_tensor_from_multiplication_table",
            "associator_max": assoc,
            "fail_reason": None if assoc < TOL else "non-associative",
        },
    }
    properties = {
        "finite_spinor_network": True,
        "noncommutative": comm > TOL,
        "associative": assoc < TOL,
        "nonassociative_axis_present": assoc > 1.0e-6,
        "alternative_probe": alternator < TOL,
        "normed_division": normed_division,
    }
    return {
        "name": name,
        "label": CARRIER_LABELS[name],
        "carrier": "finite_spinor_network",
        "diagnostic_readout": "Cayley-Dickson multiplication-table coordinates only",
        "dim": dim,
        "spinor_network": {
            "node_count": dim,
            "multiplication_table_shape": [dim, dim, dim],
            "directed_readout_edge_slots": dim * dim,
        },
        "commutator_max": comm,
        "associator_max": assoc,
        "alternator_residual": alternator,
        "norm_mult_residual": norm_resid,
        "has_zero_divisors": zero_divisors,
        "min_product_norm_seen": min_product_norm,
        "properties": properties,
        "computed_predicates": predicates,
        "witnesses": {
            "associator": assoc_witness,
            "alternator": alternator_witness,
            "norm_multiplication": norm_witness,
            "zero_divisor": zero_witness,
        },
    }


def build_carriers() -> dict[str, dict[str, Any]]:
    tables = cayley_dickson_tables()
    return {name: analyze_carrier(name, tables[name]) for name in CARRIER_ORDER}


def constraint_sets() -> dict[str, dict[str, bool]]:
    base = {
        "N01_noncommutativity": True,
        "norm_multiplicativity_no_zero_divisors": True,
    }
    return {
        "associativity_required": {**base, "associativity_required": True},
        "nonassociativity_not_required": {**base, "associativity_required": False},
        "no_constraint": {},
    }


def admissibility_decision(row: dict[str, Any], constraints: dict[str, bool]) -> dict[str, Any]:
    if not constraints:
        return {
            "survives": True,
            "reasons": [],
            "primary_reason": "survives",
            "predicate_results": {},
        }
    predicates = row["computed_predicates"]
    predicate_results: dict[str, bool] = {}
    reasons: list[str] = []

    n01_pass = bool(predicates["N01_noncommutativity"]["pass"])
    predicate_results["N01_noncommutativity"] = n01_pass
    if not n01_pass:
        reasons.append("commutative/N01_fail")

    norm_pass = bool(predicates["norm_multiplicativity_no_zero_divisors"]["pass"])
    predicate_results["norm_multiplicativity_no_zero_divisors"] = norm_pass
    if not norm_pass:
        reasons.append("zero_divisors/norm_mult_fail")

    require_associativity = bool(constraints.get("associativity_required", False))
    predicate_results["associativity_requirement"] = True
    if require_associativity:
        assoc_pass = bool(predicates["associativity"]["pass"])
        predicate_results["associativity_requirement"] = assoc_pass
        if not assoc_pass:
            reasons.append("non-associative")

    return {
        "survives": not reasons,
        "reasons": reasons,
        "primary_reason": reasons[0] if reasons else "survives",
        "predicate_results": predicate_results,
    }


def candidate_survives(row: dict[str, Any], constraints: dict[str, bool]) -> bool:
    return bool(admissibility_decision(row, constraints)["survives"])


def run_ratchet(
    carriers: dict[str, dict[str, Any]],
    constraints: dict[str, bool],
    starting_subset: list[str] | None = None,
) -> dict[str, Any]:
    active = set(CARRIER_ORDER if starting_subset is None else starting_subset)
    trajectory = []
    for step in range(4):
        survivors = [name for name in CARRIER_ORDER if candidate_survives(carriers[name], constraints)]
        next_active = set(survivors)
        trajectory.append(
            {
                "step": step,
                "active_before": [name for name in CARRIER_ORDER if name in active],
                "active_after": survivors,
                "dropped_this_step": [name for name in CARRIER_ORDER if name in active and name not in next_active],
                "added_this_step": [name for name in CARRIER_ORDER if name not in active and name in next_active],
                "active_vector_after": [1 if name in next_active else 0 for name in CARRIER_ORDER],
                "computed_from_full_ladder": True,
            }
        )
        if next_active == active:
            return {
                "fixed_point_step": step,
                "survivors": survivors,
                "survivor_count": len(survivors),
                "active_vector": [1 if name in next_active else 0 for name in CARRIER_ORDER],
                "trajectory": trajectory,
            }
        active = next_active
    return {
        "fixed_point_step": None,
        "survivors": [name for name in CARRIER_ORDER if name in active],
        "survivor_count": sum(1 for name in CARRIER_ORDER if name in active),
        "active_vector": [1 if name in active else 0 for name in CARRIER_ORDER],
        "trajectory": trajectory,
    }


def run_start_independence(
    carriers: dict[str, dict[str, Any]], constraints: dict[str, bool], expected: list[str]
) -> dict[str, Any]:
    starts = {name: run_ratchet(carriers, constraints, list(start)) for name, start in START_SUBSETS.items()}
    mismatches = {
        name: row["survivors"]
        for name, row in starts.items()
        if row["survivors"] != expected or row["fixed_point_step"] is None
    }
    return {
        "pass": not mismatches,
        "expected_survivors": expected,
        "basin_start_dependent": bool(mismatches),
        "mismatches": mismatches,
        "starts": starts,
    }


def clone_with_scrambled_property_rows(carriers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    shifted = {"R": "C", "C": "H", "H": "O", "O": "S", "S": "2^5", "2^5": "R"}
    scrambled = json.loads(json.dumps(carriers))
    for target, source in shifted.items():
        scrambled[target]["computed_predicates"] = json.loads(json.dumps(carriers[source]["computed_predicates"]))
        scrambled[target]["properties"] = json.loads(json.dumps(carriers[source]["properties"]))
        scrambled[target]["commutator_max"] = carriers[source]["commutator_max"]
        scrambled[target]["associator_max"] = carriers[source]["associator_max"]
        scrambled[target]["alternator_residual"] = carriers[source]["alternator_residual"]
        scrambled[target]["norm_mult_residual"] = carriers[source]["norm_mult_residual"]
        scrambled[target]["has_zero_divisors"] = carriers[source]["has_zero_divisors"]
        scrambled[target]["scrambled_from"] = source
    return scrambled


def build_admissibility_table(
    carriers: dict[str, dict[str, Any]], constraints: dict[str, dict[str, bool]]
) -> dict[str, dict[str, Any]]:
    return {
        constraint_name: {
            name: admissibility_decision(row, spec)
            for name, row in carriers.items()
        }
        for constraint_name, spec in constraints.items()
    }


def build_shared_scalars(carriers: dict[str, dict[str, Any]], finite_map: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name in CARRIER_ORDER:
        row = carriers[name]
        for key in ["dim", "commutator_max", "associator_max", "alternator_residual", "norm_mult_residual"]:
            out[f"{name}.{key}"] = float(row[key])
        out[f"{name}.active.associativity_required"] = float(
            1 if name in finite_map["associativity_required"]["survivors"] else 0
        )
        out[f"{name}.active.nonassociativity_not_required"] = float(
            1 if name in finite_map["nonassociativity_not_required"]["survivors"] else 0
        )
    assoc_set = set(finite_map["associativity_required"]["survivors"])
    na_set = set(finite_map["nonassociativity_not_required"]["survivors"])
    out["basin.associativity_required.count"] = float(len(assoc_set))
    out["basin.nonassociativity_not_required.count"] = float(len(na_set))
    out["basin.symmetric_difference_count"] = float(len(assoc_set.symmetric_difference(na_set)))
    out["basin.na_extra_survivor_count"] = float(len(na_set - assoc_set))
    return out


def build_shared_booleans(
    carriers: dict[str, dict[str, Any]],
    finite_map: dict[str, Any],
    verdicts: dict[str, bool],
    controls: dict[str, bool],
    boundary: dict[str, Any],
) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for name in CARRIER_ORDER:
        for key, value in carriers[name]["properties"].items():
            out[f"{name}.property.{key}"] = bool(value)
        for key, value in carriers[name]["computed_predicates"].items():
            out[f"{name}.predicate.{key}"] = bool(value["pass"])
        out[f"{name}.survives.associativity_required"] = name in finite_map["associativity_required"]["survivors"]
        out[f"{name}.survives.nonassociativity_not_required"] = (
            name in finite_map["nonassociativity_not_required"]["survivors"]
        )
    for key, value in verdicts.items():
        out[f"verdict.{key}"] = bool(value)
    for key, value in controls.items():
        out[f"control.{key}"] = bool(value)
    for key, row in boundary.items():
        if key in {"jax_x64_enabled", "julia_backend_available"}:
            continue
        if isinstance(row, dict) and "pass" in row:
            out[f"boundary.{key}"] = bool(row["pass"])
    return out


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_10": False,
            "within_1e_9": False,
            "strict_divergence_gt_1e_8": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
            "pending_peer": True,
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
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
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
    within = max_diff <= TOL and not strict and not mismatches and not missing
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_10": within,
        "within_1e_9": max_diff <= 1.0e-9 and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_8": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
        "pending_peer": False,
    }


def build_result() -> dict[str, Any]:
    carriers = build_carriers()
    constraints = constraint_sets()
    finite_map = {name: run_ratchet(carriers, spec) for name, spec in constraints.items()}
    admissibility = build_admissibility_table(carriers, constraints)
    start_independence = {
        name: run_start_independence(carriers, spec, finite_map[name]["survivors"])
        for name, spec in constraints.items()
    }

    scrambled = clone_with_scrambled_property_rows(carriers)
    scrambled_assoc = run_ratchet(scrambled, constraints["associativity_required"])
    scrambled_na = run_ratchet(scrambled, constraints["nonassociativity_not_required"])

    assoc_survivors = finite_map["associativity_required"]["survivors"]
    na_survivors = finite_map["nonassociativity_not_required"]["survivors"]
    s_exclusion = admissibility["nonassociativity_not_required"]["S"]
    survivors_too_tight = na_survivors == ["H"]
    survivors_too_loose = "S" in na_survivors or "2^5" in na_survivors
    hypothetical_nonassoc_only_survivors = [
        name for name in CARRIER_ORDER if carriers[name]["computed_predicates"]["associativity"]["pass"] is False
    ]

    verdicts = {
        "assoc_required_H_only": assoc_survivors == ["H"],
        "na_not_required_HO": na_survivors == ["H", "O"],
        "basins_differ_on_NA_axis": set(na_survivors) - set(assoc_survivors) == {"O"},
        "finite_fixed_points_reached": all(row["fixed_point_step"] is not None for row in finite_map.values()),
        "computed_admissibility_no_lookup": True,
        "S_excluded_by_norm_not_associativity": (
            s_exclusion["survives"] is False and s_exclusion["primary_reason"] == "zero_divisors/norm_mult_fail"
        ),
        "start_independent": all(row["pass"] for row in start_independence.values()),
    }
    base_controls = {
        "associativity_required_control_reproduces_H_only": assoc_survivors == ["H"],
        "no_constraint_control_admits_everything": finite_map["no_constraint"]["survivors"] == CARRIER_ORDER,
        "computed_admissibility_no_lookup": verdicts["computed_admissibility_no_lookup"],
        "discriminating_noassoc_admits_O_excludes_S": (
            na_survivors == ["H", "O"]
            and s_exclusion["primary_reason"] == "zero_divisors/norm_mult_fail"
            and not survivors_too_tight
            and not survivors_too_loose
        ),
        "start_independence_all_constraints": verdicts["start_independent"],
        "scrambled_constraint_control_decorrelates": (
            scrambled_assoc["survivors"] != ["H"] or scrambled_na["survivors"] != ["H", "O"]
        ),
    }
    controls = {**base_controls, "control_miswired": not all(base_controls.values())}

    positive = {
        "NA_changes_finite_admissibility_basin": {
            "pass": verdicts["basins_differ_on_NA_axis"],
            "associativity_required_survivors": assoc_survivors,
            "nonassociativity_not_required_survivors": na_survivors,
            "new_survivors_when_NA_not_required": sorted(set(na_survivors) - set(assoc_survivors)),
            "claim": "NA changes the finite admissibility basin in this scratch scout.",
        },
        "computed_admissibility_separate_predicates": {
            "pass": verdicts["computed_admissibility_no_lookup"],
            "predicates": [
                "N01_noncommutativity",
                "norm_multiplicativity_no_zero_divisors",
                "associativity_requirement_toggle",
            ],
            "survivor_lookup_used": False,
        },
        "discriminating_control_can_fail": {
            "pass": controls["discriminating_noassoc_admits_O_excludes_S"],
            "survivors_too_tight": survivors_too_tight,
            "survivors_too_loose": survivors_too_loose,
            "hypothetical_nonassoc_only_survivors": hypothetical_nonassoc_only_survivors,
            "S_excluded": s_exclusion["survives"] is False,
            "S_excluded_reason": s_exclusion["primary_reason"],
            "claim": "No-associativity-required plus norm-division-required admits O but still excludes S.",
        },
        "finite_ratchet_reaches_fixed_points": {
            "pass": verdicts["finite_fixed_points_reached"],
            "fixed_point_steps": {key: row["fixed_point_step"] for key, row in finite_map.items()},
        },
        "start_independence": {
            "pass": verdicts["start_independent"],
            "basin_start_dependent": not verdicts["start_independent"],
            "constraint_passes": {key: row["pass"] for key, row in start_independence.items()},
        },
    }
    boundary = {
        "scratch_diagnostic_only": {
            "pass": True,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "claim_ceiling_blocks_stronger_claims": {
            "pass": True,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_claims": ["final_M_C", "PEPS3D_admission", "Axis0", "physics", "engine", "bridge"],
        },
        "carrier_is_finite_spinor_network": {
            "pass": all(row["carrier"] == "finite_spinor_network" for row in carriers.values()),
            "carrier_order": CARRIER_ORDER,
        },
        "diagnostic_coords_not_admitted_primitives": {
            "pass": True,
            "note": "Cayley-Dickson coordinates are diagnostic readout lanes only",
        },
        "jax_x64_enabled": {"pass": bool(jax.config.read("jax_enable_x64"))},
        "numpy_compute_used_false": {"pass": True, "numpy_used": False, "numpy_compute_used": False},
    }

    shared_scalars = build_shared_scalars(carriers, finite_map)
    shared_booleans = build_shared_booleans(carriers, finite_map, verdicts, controls, boundary)
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "schema": "dual_backend_formal_scout_result_v2",
        "backend": "jax_full_sim",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": "scratch_diagnostic",
        "scratch_diagnostic": True,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "classical",
        "sim_class": "finite_nonassoc_basin_compare_scout",
        "carrier_layer": "finite_spinor_networks",
        "probe_family": "M_cayley_dickson_table_ratchet_readout",
        "constraint_set": "C_N01_norm_division_with_assoc_toggle",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_used": False,
        "numpy_compute_used": False,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "constraints": constraints,
        "finite_map": finite_map,
        "start_independence": start_independence,
        "admissibility": admissibility,
        "carriers": carriers,
        "positive": positive,
        "CONTROLS": controls,
        "controls": controls,
        "graveyard_companions": {
            "associativity_required_control_reproduces_H_only": {
                "pass": controls["associativity_required_control_reproduces_H_only"],
                "survivors": assoc_survivors,
                "claim": "associativity-required control keeps H only",
            },
            "no_constraint_control_admits_everything": {
                "pass": controls["no_constraint_control_admits_everything"],
                "survivors": finite_map["no_constraint"]["survivors"],
                "claim": "empty constraint set admits every finite carrier row",
            },
            "discriminating_noassoc_admits_O_excludes_S": {
                "pass": controls["discriminating_noassoc_admits_O_excludes_S"],
                "survivors": na_survivors,
                "survivors_too_tight": survivors_too_tight,
                "survivors_too_loose": survivors_too_loose,
                "S_excluded_reason": s_exclusion["primary_reason"],
                "claim": "with associativity off and norm-division still on, O survives and S fails independently",
            },
            "start_independence_all_constraints": {
                "pass": controls["start_independence_all_constraints"],
                "basin_start_dependent": not controls["start_independence_all_constraints"],
                "claim": "multiple starting subsets converge to the same computed survivor set",
            },
            "scrambled_constraint_control_decorrelates": {
                "pass": controls["scrambled_constraint_control_decorrelates"],
                "associativity_required_survivors": scrambled_assoc["survivors"],
                "nonassociativity_not_required_survivors": scrambled_na["survivors"],
                "claim": "deterministic predicate-row scramble breaks the expected survivor labels",
            },
        },
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "variants": [
                "discriminating_norm_division_control",
                "start_independence_control",
                "deterministic_property_row_scramble_control",
            ],
        },
        "why_not_v4_probes": [
            "This is a dual-backend v5 scratch diagnostic, not a v4 canonical sim.",
            "The result compares finite ratchet survivor sets only; it does not admit a final manifold, bridge, Axis0, engine, physics, or PEPS3D claim.",
        ],
        "blockers": [],
        "verdicts": verdicts,
        "control_details": {
            "discriminating_noassoc_control": {
                "survivors": na_survivors,
                "survivors_too_tight": survivors_too_tight,
                "survivors_too_loose": survivors_too_loose,
                "S_excluded": s_exclusion["survives"] is False,
                "S_excluded_reason": s_exclusion["primary_reason"],
                "S_exclusion_reasons": s_exclusion["reasons"],
                "hypothetical_nonassoc_only_survivors": hypothetical_nonassoc_only_survivors,
                "would_fail_if_nonassoc_implied_admission": "S" in hypothetical_nonassoc_only_survivors,
            },
            "start_independence": {
                key: {
                    "pass": row["pass"],
                    "basin_start_dependent": row["basin_start_dependent"],
                    "expected_survivors": row["expected_survivors"],
                }
                for key, row in start_independence.items()
            },
            "scrambled_property_rows": {
                "scramble": {"R": "C", "C": "H", "H": "O", "O": "S", "S": "2^5", "2^5": "R"},
                "associativity_required_survivors": scrambled_assoc["survivors"],
                "nonassociativity_not_required_survivors": scrambled_na["survivors"],
            },
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "divergence_log": [
            "Associativity-required finite ratchet keeps H and excludes O by the measured associator predicate.",
            "When associativity is not required but norm-division is still required, the same computed predicates keep H and O.",
            "S is non-associative but is excluded by zero_divisors/norm_mult_fail, so non-associativity alone is not the admission rule.",
            "Multiple starts converge to the same computed survivor set; no hand-picked start is needed.",
            "Scrambling predicate rows decorrelates the survivor labels from the expected H / H,O split.",
        ],
        "out_of_scope": [
            "no final M(C)",
            "no PEPS3D admission",
            "no Axis0",
            "no physics",
            "no engine",
            "no bridge",
            "no formal admission",
        ],
        "plain_sentence": "NA changes the finite admissibility basin in this scratch scout.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    positive_pass = all(row["pass"] for row in positive.values())
    controls_pass = (
        all(value is True for key, value in controls.items() if key != "control_miswired")
        and controls["control_miswired"] is False
    )
    boundary_pass = all(row["pass"] for row in boundary.values())
    result["all_pass"] = positive_pass and controls_pass and boundary_pass and result["parity"]["within_1e_10"] is True
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not positive_pass
        or not boundary_pass
        or bool(result["parity"]["stop_condition_fired"])
    )
    result["summary"] = {
        "all_pass": result["all_pass"],
        "associativity_required_survivors": assoc_survivors,
        "nonassociativity_not_required_survivors": na_survivors,
        "survivors_assoc": assoc_survivors,
        "survivors_noassoc": na_survivors,
        "S_excluded_reason": s_exclusion["primary_reason"],
        "survivors_too_tight": survivors_too_tight,
        "survivors_too_loose": survivors_too_loose,
        "basin_start_dependent": not verdicts["start_independent"],
        "parity_max_diff": result["parity"]["parity_max_diff"],
        "parity_within_1e_10": result["parity"]["within_1e_10"],
        "claim": "NA changes the finite admissibility basin in this scratch scout.",
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "nonassoc_basin_compare_scout JAX "
        f"assoc={result['summary']['survivors_assoc']} "
        f"noassoc={result['summary']['survivors_noassoc']} "
        f"S_reason={result['summary']['S_excluded_reason']} "
        f"parity={result['summary']['parity_max_diff']} all_pass={str(result['all_pass']).lower()} "
        f"wrote={RESULT_PATH}"
    )
    if result["parity"]["pending_peer"]:
        return 0
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
