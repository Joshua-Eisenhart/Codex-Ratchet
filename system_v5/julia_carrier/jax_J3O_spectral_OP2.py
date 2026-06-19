#!/usr/bin/env python3
# object_id: J3O_spectral_OP2
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


OBJECT_ID = "J3O_spectral_OP2"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "J3O_spectral_OP2_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "J3O_spectral_OP2_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
SAMPLE_COUNT = 8
OFFDIAG_PAIRS = [(0, 1), (0, 2), (1, 2)]
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


def oct_conj(x: jax.Array) -> jax.Array:
    return x * jnp.asarray([1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def j3_zero() -> jax.Array:
    return jnp.zeros((3, 3, 8), dtype=jnp.float64)


def j3_identity() -> jax.Array:
    m = j3_zero()
    for i in range(3):
        m = m.at[i, i, 0].set(1.0)
    return m


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


def j3_probe_coords(sample_idx: int, side: int) -> jax.Array:
    vals: list[float] = []
    for j in range(1, 28):
        raw = (
            (sample_idx + 23) * (j + 11) * (side + 3) * 29
            + j ** 2 * 17
            + sample_idx * 31
            + side * 7
        ) % 113
        vals.append(0.25 * ((float(raw) - 56.0) / 41.0))
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


def j3_trace(a: jax.Array) -> jax.Array:
    return a[0, 0, 0] + a[1, 1, 0] + a[2, 2, 0]


def j3_residual(a: jax.Array, b: jax.Array) -> float:
    return py_float(jnp.linalg.norm(jnp.ravel(a - b)))


def spectral_data(table: jax.Array, a: jax.Array) -> dict[str, Any]:
    a2 = jordan(table, a, a)
    a3 = jordan(table, a2, a)
    t = j3_trace(a)
    tr2 = j3_trace(a2)
    tr3 = j3_trace(a3)
    sigma2 = 0.5 * (t * t - tr2)
    detv = (t ** 3 - 3.0 * t * tr2 + 2.0 * tr3) / 6.0
    return {
        "trace": t,
        "trace_square": tr2,
        "trace_cube": tr3,
        "sigma2": sigma2,
        "determinant": detv,
        "A2": a2,
        "A3": a3,
    }


def characteristic_residual(table: jax.Array, a: jax.Array) -> tuple[float, dict[str, Any]]:
    spec = spectral_data(table, a)
    ident = j3_identity()
    lhs = spec["A3"] - spec["trace"] * spec["A2"] + spec["sigma2"] * a - spec["determinant"] * ident
    return py_float(jnp.linalg.norm(jnp.ravel(lhs))), spec


def primitive_idempotent(table: jax.Array) -> jax.Array:
    del table
    u = basis(8, 1)
    p = j3_zero()
    p = p.at[0, 0, 0].set(0.5)
    p = p.at[1, 1, 0].set(0.5)
    p = p.at[0, 1, :].set(-0.5 * u)
    p = p.at[1, 0, :].set(oct_conj(p[0, 1, :]))
    return p


def rank2_idempotent() -> jax.Array:
    q = j3_zero()
    q = q.at[0, 0, 0].set(1.0)
    q = q.at[1, 1, 0].set(1.0)
    return q


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
    max_ch_residual = 0.0
    representative_spec: dict[str, Any] | None = None
    for sample_idx in range(1, SAMPLE_COUNT + 1):
        a = j3_from_coords(j3_probe_coords(sample_idx, 31))
        residual, spec = characteristic_residual(table, a)
        max_ch_residual = max(max_ch_residual, residual)
        if sample_idx == 1:
            representative_spec = spec
    assert representative_spec is not None

    p = primitive_idempotent(table)
    p2 = jordan(table, p, p)
    p_spec = spectral_data(table, p)
    p_idempotent_residual = j3_residual(p2, p)
    p_trace = py_float(p_spec["trace"])
    p_sigma2 = py_float(p_spec["sigma2"])
    p_det = py_float(p_spec["determinant"])
    p_trace_residual = abs(p_trace - 1.0)
    p_sigma2_abs = abs(p_sigma2)
    p_det_abs = abs(p_det)

    q = rank2_idempotent()
    q2 = jordan(table, q, q)
    q_spec = spectral_data(table, q)
    q_idempotent_residual = j3_residual(q2, q)
    q_trace = py_float(q_spec["trace"])
    q_sigma2 = py_float(q_spec["sigma2"])
    q_det = py_float(q_spec["determinant"])
    q_not_pure = q_idempotent_residual < TOL and (abs(q_trace - 1.0) > TOL or abs(q_sigma2) > TOL)

    verdicts = {
        "jordan_cubic_identity_holds": max_ch_residual < TOL,
        "primitive_idempotent_is_pure_state": p_idempotent_residual < TOL and p_trace_residual < TOL and p_sigma2_abs < TOL and p_det_abs < TOL,
    }
    controls = {
        "rank2_idempotent_not_primitive_control_ok": q_not_pure,
        "rank2_idempotent_trace_is_2": abs(q_trace - 2.0) < TOL,
        "rank2_idempotent_sigma2_nonzero": abs(q_sigma2 - 1.0) < TOL,
    }
    controls["control_miswired"] = not (
        controls["rank2_idempotent_not_primitive_control_ok"]
        and controls["rank2_idempotent_trace_is_2"]
        and controls["rank2_idempotent_sigma2_nonzero"]
    )
    shared_scalars = {
        "J3O_real_dim": int(p.shape[0] + (p.shape[0] * (p.shape[0] - 1) // 2) * p.shape[2]),
        "sample_count": SAMPLE_COUNT,
        "jordan_cubic_identity_max_residual": max_ch_residual,
        "representative_trace": py_float(representative_spec["trace"]),
        "representative_sigma2": py_float(representative_spec["sigma2"]),
        "representative_determinant": py_float(representative_spec["determinant"]),
        "primitive_idempotent_residual": p_idempotent_residual,
        "primitive_trace": p_trace,
        "primitive_trace_residual": p_trace_residual,
        "primitive_sigma2_abs": p_sigma2_abs,
        "primitive_det_abs": p_det_abs,
        "rank2_idempotent_residual": q_idempotent_residual,
        "rank2_trace": q_trace,
        "rank2_sigma2": q_sigma2,
        "rank2_det_abs": abs(q_det),
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
        "claim_ceiling": "Finite J3(O) spectral/OP2 diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind": "classical",
        "sim_class": "exceptional_jordan_spectral_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "tool_manifest": {
            "JAX": "load-bearing J3(O) Jordan product, spectral invariants, and idempotent checks",
            "jax.numpy": "load-bearing x64 residual norms for cubic identity and idempotence",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive"},
        "spectral_formula": {
            "trace": "T(A)",
            "sigma2": "(T(A)^2 - T(A^2))/2",
            "determinant": "(T(A)^3 - 3*T(A)*T(A^2) + 2*T(A^3))/6",
            "powers": "Jordan powers with A^2=A o A and A^3=A^2 o A",
        },
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": "The finite J3(O) Jordan product satisfies the rank-3 cubic identity on deterministic random elements, and a primitive trace-one idempotent behaves as an OP2 pure-state witness while a trace-two idempotent control is not primitive.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not verdicts["jordan_cubic_identity_holds"]
        or not verdicts["primitive_idempotent_is_pure_state"]
        or bool(result["parity"]["stop_condition_fired"])
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    n = result["numbers"]
    print("J3O_spectral_OP2 - JAX full sim")
    print(
        f"jordan_cubic_identity_holds={str(result['verdicts']['jordan_cubic_identity_holds']).lower()} "
        f"jordan_cubic_identity_max_residual={n['jordan_cubic_identity_max_residual']}"
    )
    print(
        f"primitive_idempotent_is_pure_state={str(result['verdicts']['primitive_idempotent_is_pure_state']).lower()} "
        f"primitive_idempotent_residual={n['primitive_idempotent_residual']} primitive_trace={n['primitive_trace']} "
        f"primitive_sigma2_abs={n['primitive_sigma2_abs']} primitive_det_abs={n['primitive_det_abs']}"
    )
    print(
        f"rank2_idempotent_not_primitive_control_ok={str(result['controls']['rank2_idempotent_not_primitive_control_ok']).lower()} "
        f"rank2_trace={n['rank2_trace']} rank2_sigma2={n['rank2_sigma2']} rank2_det_abs={n['rank2_det_abs']}"
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
