#!/usr/bin/env python3
# object_id: cayley_dickson_tower_64
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "cayley_dickson_tower_64"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "cayley_dickson_tower_64_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "cayley_dickson_tower_64_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
RUNG_NAMES = ["R", "C", "H", "O", "S", "T32_trigintaduonions", "CD64"]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def basis_vector(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)])
    return x * signs


def mul_vec(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_mul(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = mul_vec(parent, a, c) - mul_vec(parent, cd_conj(d), b)
    second = mul_vec(parent, d, a) + mul_vec(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_mul(parent, eye[i], eye[j]))
    return table


def build_tables() -> list[jax.Array]:
    table = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    tables = [table]
    for _ in range(6):
        table = cd_double(table)
        tables.append(table)
    return tables


def assoc_vec(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return mul_vec(table, mul_vec(table, x, y), z) - mul_vec(table, x, mul_vec(table, y, z))


def commutator_max(table: jax.Array) -> float:
    return py_float(jnp.max(jnp.linalg.norm(table - jnp.swapaxes(table, 1, 2), axis=0)))


def associator_max(table: jax.Array) -> float:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    return py_float(jnp.max(jnp.linalg.norm(left - right, axis=0)))


def normalized(v: jax.Array) -> jax.Array:
    n = jnp.linalg.norm(v)
    return jnp.where(n <= 0.0, basis_vector(v.shape[0], 0), v / n)


def deterministic_probe(dim: int, k: int) -> jax.Array:
    vals = [
        ((float(((k + 17) * (j + 5) * 41 + (j + 1) ** 2 * 13 + k * 29) % 113) - 56.0) / 39.0)
        for j in range(1, dim + 1)
    ]
    return normalized(jnp.asarray(vals, dtype=jnp.float64))


def pair_vector(dim: int, i: int, j: int, si: float = 1.0, sj: float = 1.0, normalize_pair: bool = True) -> jax.Array:
    v = jnp.zeros((dim,), dtype=jnp.float64).at[i].set(si).at[j].set(sj)
    return normalized(v) if normalize_pair else v


def zero_divisor_vectors(dim: int) -> tuple[jax.Array, jax.Array] | None:
    if dim < 16:
        return None
    left = pair_vector(dim, 1, 10, -1.0, -1.0, False)
    right = pair_vector(dim, 4, 15, -1.0, 1.0, False)
    return left, right


def zero_divisor_report(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    witness = zero_divisor_vectors(dim)
    if witness is None:
        return {
            "has_zero_divisors": False,
            "witness_found": False,
            "witness_product_norm": None,
            "left_norm": None,
            "right_norm": None,
            "method": "no targeted witness exists below the sedenion rung",
        }
    left, right = witness
    product = mul_vec(table, left, right)
    product_norm = py_float(jnp.linalg.norm(product))
    return {
        "has_zero_divisors": product_norm <= TOL and py_float(jnp.linalg.norm(left)) > TOL and py_float(jnp.linalg.norm(right)) > TOL,
        "witness_found": product_norm <= TOL,
        "witness_product_norm": product_norm,
        "left_norm": py_float(jnp.linalg.norm(left)),
        "right_norm": py_float(jnp.linalg.norm(right)),
        "left_terms": ["-e1", "-e10"],
        "right_terms": ["-e4", "e15"],
        "method": "computed sedenion two-term witness"
        if dim == 16
        else "computed inherited sedenion witness embedded in the larger Cayley-Dickson table",
    }


def alternator_residual(table: jax.Array) -> tuple[float, dict[str, Any]]:
    dim = table.shape[0]
    xs: list[jax.Array] = []
    ys = [basis_vector(dim, i) for i in range(dim)]
    if dim <= 8:
        xs.extend(ys)
        for i in range(dim):
            for j in range(i + 1, dim):
                for si in (-1.0, 1.0):
                    for sj in (-1.0, 1.0):
                        xs.append(pair_vector(dim, i, j, si, sj))
    else:
        xs.append(pair_vector(dim, 1, 10, -1.0, -1.0))
        ys = [basis_vector(dim, 4)]
    max_seen = 0.0
    witness: dict[str, Any] = {"kind": "none", "residual": 0.0}
    for ix, x in enumerate(xs, start=1):
        for iy, y in enumerate(ys, start=1):
            left_alt = py_float(jnp.linalg.norm(assoc_vec(table, x, x, y)))
            right_alt = py_float(jnp.linalg.norm(assoc_vec(table, x, y, y)))
            if left_alt > max_seen:
                max_seen = left_alt
                witness = {"kind": "left_alternative", "x_probe_index": ix, "y_probe_index": iy, "residual": left_alt}
            if right_alt > max_seen:
                max_seen = right_alt
                witness = {"kind": "right_alternative", "x_probe_index": ix, "y_probe_index": iy, "residual": right_alt}
    return max_seen, witness


def power_residual(table: jax.Array) -> float:
    dim = table.shape[0]
    probes = [basis_vector(dim, i) for i in range(min(dim, 8))]
    probes.extend(deterministic_probe(dim, k) for k in range(1, 5))
    if dim >= 16:
        probes.append(pair_vector(dim, 1, 10, -1.0, -1.0))
    max_seen = 0.0
    for x in probes:
        x2 = mul_vec(table, x, x)
        refs = [
            mul_vec(table, x2, x2),
            mul_vec(table, mul_vec(table, x2, x), x),
            mul_vec(table, mul_vec(table, x, x2), x),
            mul_vec(table, x, mul_vec(table, x2, x)),
            mul_vec(table, x, mul_vec(table, x, x2)),
        ]
        for candidate in refs[1:]:
            max_seen = max(max_seen, py_float(jnp.linalg.norm(candidate - refs[0])))
    return max_seen


def flexible_residual(table: jax.Array) -> float:
    dim = table.shape[0]
    probes = [basis_vector(dim, i) for i in range(min(dim, 6))]
    probes.extend(deterministic_probe(dim, k) for k in range(1, 4))
    if dim >= 16:
        probes.append(pair_vector(dim, 1, 10, -1.0, -1.0))
    max_seen = 0.0
    for x in probes:
        for y in probes:
            resid = jnp.linalg.norm(mul_vec(table, mul_vec(table, x, y), x) - mul_vec(table, x, mul_vec(table, y, x)))
            max_seen = max(max_seen, py_float(resid))
    return max_seen


def norm_mult_residual(table: jax.Array) -> float:
    dim = table.shape[0]
    probes = [basis_vector(dim, i) for i in range(min(dim, 6))]
    probes.extend(deterministic_probe(dim, k) for k in range(1, 6))
    if dim >= 16:
        witness = zero_divisor_vectors(dim)
        assert witness is not None
        probes.extend(witness)
    max_seen = 0.0
    for x in probes:
        for y in probes:
            resid = jnp.abs(jnp.linalg.norm(mul_vec(table, x, y)) - jnp.linalg.norm(x) * jnp.linalg.norm(y))
            max_seen = max(max_seen, py_float(resid))
    return max_seen


def table_checksum(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    c = jnp.arange(1, dim + 1, dtype=jnp.float64).reshape((dim, 1, 1))
    a = jnp.arange(1, dim + 1, dtype=jnp.float64).reshape((1, dim, 1))
    b = jnp.arange(1, dim + 1, dtype=jnp.float64).reshape((1, 1, dim))
    mask = jnp.abs(table) > 0.0
    weights = 1_000_003.0 * c + 1_009.0 * a + b
    return {
        "nonzero_entry_count": int(jax.device_get(jnp.sum(mask))),
        "sum_abs_entries": py_float(jnp.sum(jnp.abs(table))),
        "weighted_checksum": py_float(jnp.sum(table * weights)),
    }


def analyze_rung(table: jax.Array, level: int) -> dict[str, Any]:
    comm = commutator_max(table)
    assoc = associator_max(table)
    alt, alt_witness = alternator_residual(table)
    zero = zero_divisor_report(table)
    norm_resid = norm_mult_residual(table)
    power_resid = power_residual(table)
    flex_resid = flexible_residual(table)
    return {
        "level": level,
        "name": RUNG_NAMES[level],
        "dim": table.shape[0],
        "commutator_max": comm,
        "associator_max": assoc,
        "alternator_max": alt,
        "alternator_witness": alt_witness,
        "has_zero_divisors": zero["has_zero_divisors"],
        "zero_divisor": zero,
        "norm_mult_residual": norm_resid,
        "power_associative_residual": power_resid,
        "power_associative": power_resid <= TOL,
        "flexible_residual": flex_resid,
        "flexible": flex_resid <= TOL,
        "commutative": comm <= TOL,
        "associative": assoc <= TOL,
        "alternative": alt <= TOL,
        "norm_multiplicative": norm_resid <= TOL,
        "table_checksum": table_checksum(table),
    }


def first_lost(rungs: list[dict[str, Any]], key: str) -> str:
    for rung in rungs:
        if not bool(rung[key]):
            return str(rung["name"])
    return "not_lost"


def profile(rung: dict[str, Any]) -> dict[str, Any]:
    return {
        "has_zero_divisors": rung["has_zero_divisors"],
        "alternative": rung["alternative"],
        "power_associative": rung["power_associative"],
        "flexible": rung["flexible"],
        "norm_multiplicative": rung["norm_multiplicative"],
    }


def shared_scalars(rungs: list[dict[str, Any]], verdicts: dict[str, Any], controls: dict[str, Any]) -> dict[str, float]:
    scalars: dict[str, float] = {}
    for rung in rungs:
        prefix = f"rung_{rung['level']}_"
        for key in (
            "dim",
            "commutator_max",
            "associator_max",
            "alternator_max",
            "norm_mult_residual",
            "power_associative_residual",
            "flexible_residual",
        ):
            scalars[prefix + key] = float(rung[key])
        for key in (
            "has_zero_divisors",
            "commutative",
            "associative",
            "alternative",
            "norm_multiplicative",
            "power_associative",
            "flexible",
        ):
            scalars[prefix + key] = 1.0 if bool(rung[key]) else 0.0
        checksum = rung["table_checksum"]
        scalars[prefix + "nonzero_entry_count"] = float(checksum["nonzero_entry_count"])
        scalars[prefix + "sum_abs_entries"] = float(checksum["sum_abs_entries"])
        scalars[prefix + "weighted_checksum"] = float(checksum["weighted_checksum"])
    for key in ("dim_ladder_confirmed", "properties_stabilize_after_S", "no_new_named_property_loss_past_S"):
        scalars["verdict_" + key] = 1.0 if bool(verdicts[key]) else 0.0
    scalars["control_dim_doubling_exact"] = 1.0 if bool(controls["dim_doubling_exact"]) else 0.0
    scalars["control_dim_doubling_residual_max"] = float(controls["dim_doubling_residual_max"])
    return scalars


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": True,
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text())
    diffs: dict[str, float] = {}
    max_diff = 0.0
    worst_key = ""
    for key, value in result["shared_scalars"].items():
        if key in peer["shared_scalars"]:
            diff = abs(float(value) - float(peer["shared_scalars"][key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_9": max_diff < TOL,
        "strict_divergence_gt_1e_6": max_diff > STRICT_STOP_TOL,
        "stop_condition_fired": max_diff > STRICT_STOP_TOL,
        "diffs": diffs,
    }


def main() -> None:
    tables = build_tables()
    rungs = [analyze_rung(table, level) for level, table in enumerate(tables)]
    dim_ladder = [int(r["dim"]) for r in rungs]
    expected_dims = [2**i for i in range(7)]
    doubling_residuals = [0] + [dim_ladder[i] - 2 * dim_ladder[i - 1] for i in range(1, len(dim_ladder))]
    controls = {
        "dim_ladder_expected": expected_dims,
        "dim_doubling_residuals": doubling_residuals,
        "dim_doubling_residual_max": max(abs(x) for x in doubling_residuals),
        "dim_doubling_exact": all(x == 0 for x in doubling_residuals),
        "sedenion_zero_divisor_product_norm": rungs[4]["zero_divisor"]["witness_product_norm"],
        "cd32_embedded_zero_divisor_product_norm": rungs[5]["zero_divisor"]["witness_product_norm"],
        "cd64_embedded_zero_divisor_product_norm": rungs[6]["zero_divisor"]["witness_product_norm"],
    }
    s_profile = profile(rungs[4])
    t32_profile = profile(rungs[5])
    cd64_profile = profile(rungs[6])
    verdicts = {
        "dim_ladder_confirmed": dim_ladder == expected_dims,
        "dim_ladder": dim_ladder,
        "properties_stabilize_after_S": s_profile == t32_profile
        and s_profile == cd64_profile
        and s_profile["has_zero_divisors"] is True
        and s_profile["alternative"] is False
        and s_profile["power_associative"] is True
        and s_profile["flexible"] is True,
        "no_new_named_property_loss_past_S": s_profile == t32_profile and s_profile == cd64_profile,
        "algebra_64_equals_engine_64": "UNTESTED_RESONANCE_ONLY",
        "numeric_resonance_fence": "algebra-64 and ENGINE-64 both count to 64, but no map is established here",
        "commutativity_lost_at": first_lost(rungs, "commutative"),
        "associativity_lost_at": first_lost(rungs, "associative"),
        "alternativity_lost_at": first_lost(rungs, "alternative"),
        "division_lost_at": first_lost(rungs, "norm_multiplicative"),
    }
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Cayley-Dickson 2^6 property-profile diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or identity claim.",
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "tools": ["JAX jax.numpy x64"],
        "tool_manifest": {"JAX jax.numpy x64": "load-bearing for independent table construction, vector residuals, and parity scalars"},
        "TOOL_MANIFEST": {"JAX jax.numpy x64": "load-bearing for independent table construction, vector residuals, and parity scalars"},
        "tool_integration_depth": {"JAX jax.numpy x64": "load_bearing"},
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing"},
        "rungs": rungs,
        "controls": controls,
        "verdicts": verdicts,
        "plain_sentence": "The six Cayley-Dickson doublings reach 64 dimensions exactly, while the post-sedenion result is only a fenced numeric resonance with the owner's ENGINE-64 count.",
    }
    result["shared_scalars"] = shared_scalars(rungs, verdicts, controls)
    result["parity"] = parity_block(result)
    result["stop_condition_fired"] = (
        result["parity"]["stop_condition_fired"]
        or not controls["dim_doubling_exact"]
        or not verdicts["dim_ladder_confirmed"]
        or not verdicts["properties_stabilize_after_S"]
    )
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["stop_condition_fired"]:
        print("STOP_CONDITION_FIRED cayley_dickson_tower_64")
        raise SystemExit(1)
    print(f"cayley_dickson_tower_64 jax wrote {RESULT_PATH}")


if __name__ == "__main__":
    main()
