#!/usr/bin/env python3
# object_id: octonion_G2_automorphism
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
from jax.scipy.linalg import expm


OBJECT_ID = "octonion_G2_automorphism"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "octonion_G2_automorphism_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "octonion_G2_automorphism_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
DIM = 8
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


def octonion_table() -> jax.Array:
    table = jnp.zeros((DIM, DIM, DIM), dtype=jnp.float64)
    table = add_identity(table, DIM)
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


def varidx(row: int, col: int) -> int:
    return row + col * DIM


def derivation_constraint_matrix(table: jax.Array) -> jax.Array:
    mat = jnp.zeros((DIM * DIM * DIM, DIM * DIM), dtype=jnp.float64)
    row = 0
    for a in range(DIM):
        for b in range(DIM):
            for c in range(DIM):
                for k in range(DIM):
                    mat = mat.at[row, varidx(c, k)].add(table[k, a, b])
                    mat = mat.at[row, varidx(k, a)].add(-table[c, k, b])
                    mat = mat.at[row, varidx(k, b)].add(-table[c, a, k])
                row += 1
    return mat


def vec_to_matrix(v: jax.Array) -> jax.Array:
    cols = [v[c * DIM:(c + 1) * DIM] for c in range(DIM)]
    return jnp.stack(cols, axis=1)


def nullspace_data(mat: jax.Array) -> tuple[int, float, jax.Array, jax.Array]:
    _, s, vh = jnp.linalg.svd(mat, full_matrices=False)
    rank_tol = py_float(max(mat.shape) * jnp.finfo(jnp.float64).eps * jnp.max(s) * 100.0)
    rank = int(jax.device_get(jnp.sum(s > rank_tol)))
    ns = vh.T[:, rank:]
    return rank, rank_tol, ns, s


def derivation_residual(table: jax.Array, d: jax.Array) -> float:
    max_seen = 0.0
    for a in range(DIM):
        for b in range(DIM):
            ea = basis(DIM, a)
            eb = basis(DIM, b)
            left = d @ multiply(table, ea, eb)
            right = multiply(table, d @ ea, eb) + multiply(table, ea, d @ eb)
            max_seen = max(max_seen, py_float(jnp.linalg.norm(left - right)))
    return max_seen


def automorphism_residual(table: jax.Array, phi: jax.Array) -> float:
    max_seen = 0.0
    for a in range(DIM):
        for b in range(DIM):
            ea = basis(DIM, a)
            eb = basis(DIM, b)
            left = phi @ multiply(table, ea, eb)
            right = multiply(table, phi @ ea, phi @ eb)
            max_seen = max(max_seen, py_float(jnp.linalg.norm(left - right)))
    return max_seen


def deterministic_tracefree_map() -> jax.Array:
    d = jnp.zeros((DIM, DIM), dtype=jnp.float64)
    for r in range(1, DIM):
        for c in range(1, DIM):
            raw = ((r + 1 + 5) * (c + 1 + 11) * 37 + (r + 1) ** 2 * 17 + (c + 1) * 19) % 101
            d = d.at[r, c].set((float(raw) - 50.0) / 31.0)
    tr = jnp.trace(d[1:, 1:]) / 7.0
    for i in range(1, DIM):
        d = d.at[i, i].add(-tr)
    return d


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "missing_julia_reference",
            "shared_scalar_rows": [],
            "max_diff_key": None,
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
    table = octonion_table()
    constraint = derivation_constraint_matrix(table)
    rank, rank_tol, ns, singular_values = nullspace_data(constraint)
    der_dim = ns.shape[1]
    d = vec_to_matrix(ns[:, 0])
    d_residual = derivation_residual(table, d)
    phi = expm(0.375 * d)
    phi_residual = automorphism_residual(table, phi)
    control_d = deterministic_tracefree_map()
    control_residual = derivation_residual(table, control_d)

    verdicts = {
        "der_O_dim_is_14": der_dim == 14,
        "automorphism_preserves_product": phi_residual < TOL,
        "automorphism_invertible": py_float(jnp.abs(jnp.linalg.det(phi))) > TOL,
    }
    controls = {
        "random_tracefree_linear_map_not_derivation": control_residual > TOL,
        "derivation_identity_action_zero": py_float(jnp.linalg.norm(d @ basis(DIM, 0))) < TOL,
        "derivation_tracefree": py_float(jnp.abs(jnp.trace(d))) < TOL,
    }
    controls["control_miswired"] = not (
        controls["random_tracefree_linear_map_not_derivation"]
        and controls["derivation_identity_action_zero"]
        and controls["derivation_tracefree"]
    )
    shared_scalars = {
        "constraint_rows": constraint.shape[0],
        "constraint_cols": constraint.shape[1],
        "constraint_rank": rank,
        "der_O_dim": der_dim,
        "rank_tol": rank_tol,
        "smallest_nonzero_singular_value": py_float(singular_values[rank - 1]),
        "largest_zero_singular_value": py_float(singular_values[rank]),
        "derivation_residual": d_residual,
        "derivation_norm": py_float(jnp.linalg.norm(d)),
        "derivation_trace_abs": py_float(jnp.abs(jnp.trace(d))),
        "derivation_identity_action_norm": py_float(jnp.linalg.norm(d @ basis(DIM, 0))),
        "automorphism_product_residual": phi_residual,
        "automorphism_det_abs": py_float(jnp.abs(jnp.linalg.det(phi))),
        "random_tracefree_derivation_residual": control_residual,
        "random_trace_abs": py_float(jnp.abs(jnp.trace(control_d))),
    }
    shared_booleans = {f"verdict.{key}": value for key, value in verdicts.items()}
    shared_booleans.update({f"control.{key}": value for key, value in controls.items()})
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
        "claim_ceiling": "Finite G2=Der(O) diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind": "classical",
        "sim_class": "octonion_exceptional_structure_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "tool_manifest": {
            "JAX": "load-bearing construction of the octonion multiplication table, derivation constraints, and automorphism residuals",
            "jax.numpy": "load-bearing x64 SVD inputs, determinant, and residual norms",
            "jax.scipy.linalg.expm": "load-bearing matrix exponential for the automorphism witness",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
            "json": "supportive",
        },
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "witness": {
            "automorphism_delta_norm": py_float(jnp.linalg.norm(phi - jnp.eye(DIM, dtype=jnp.float64))),
            "derivation_matrix": jax.device_get(d).tolist(),
            "automorphism_matrix": jax.device_get(phi).tolist(),
            "control_tracefree_matrix": jax.device_get(control_d).tolist(),
        },
        "plain_sentence": "The octonion multiplication table cuts the 64-dimensional linear-map space down to a 14-dimensional derivation algebra, and exponentiating one computed derivation gives a concrete product-preserving automorphism.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not verdicts["der_O_dim_is_14"]
        or not verdicts["automorphism_preserves_product"]
        or not verdicts["automorphism_invertible"]
        or bool(result["parity"]["stop_condition_fired"])
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    n = result["numbers"]
    print("octonion_G2_automorphism - JAX full sim")
    print(
        f"der_O_dim_is_14={str(result['verdicts']['der_O_dim_is_14']).lower()} "
        f"der_O_dim={n['der_O_dim']} constraint_rank={n['constraint_rank']}"
    )
    print(
        f"automorphism_preserves_product={str(result['verdicts']['automorphism_preserves_product']).lower()} "
        f"automorphism_product_residual={n['automorphism_product_residual']} det_abs={n['automorphism_det_abs']}"
    )
    print(
        f"random_tracefree_linear_map_not_derivation={str(result['controls']['random_tracefree_linear_map_not_derivation']).lower()} "
        f"random_tracefree_derivation_residual={n['random_tracefree_derivation_residual']}"
    )
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
