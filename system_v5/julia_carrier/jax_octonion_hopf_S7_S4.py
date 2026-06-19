#!/usr/bin/env python3
# object_id: octonion_hopf_S7_S4
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


OBJECT_ID = "octonion_hopf_S7_S4"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "octonion_hopf_S7_S4_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "octonion_hopf_S7_S4_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
SAMPLE_COUNT = 96
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


def qmul(x: jax.Array, y: jax.Array) -> jax.Array:
    a, b, c, d = x
    e, f, g, h = y
    return jnp.asarray(
        [
            a * e - b * f - c * g - d * h,
            a * f + b * e + c * h - d * g,
            a * g - b * h + c * e + d * f,
            a * h + b * g - c * f + d * e,
        ],
        dtype=jnp.float64,
    )


def qconj(q: jax.Array) -> jax.Array:
    return q * jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


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


def omul(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def oconj(o: jax.Array) -> jax.Array:
    return o * jnp.asarray([1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def sqnorm(x: jax.Array) -> jax.Array:
    return jnp.sum(x * x)


def linf(x: jax.Array, y: jax.Array) -> float:
    return py_float(jnp.max(jnp.abs(x - y)))


def h_hopf(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.concatenate([2.0 * qmul(a, qconj(b)), jnp.asarray([sqnorm(a) - sqnorm(b)], dtype=jnp.float64)])


def o_hopf(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.concatenate([2.0 * omul(table, a, oconj(b)), jnp.asarray([sqnorm(a) - sqnorm(b)], dtype=jnp.float64)])


def unit_h_pairs() -> list[tuple[jax.Array, jax.Array]]:
    pairs = [
        (jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.float64), jnp.zeros((4,), dtype=jnp.float64)),
        (jnp.zeros((4,), dtype=jnp.float64), jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.float64)),
    ]
    for sample_idx in range(1, SAMPLE_COUNT + 1):
        v = probe_vector(8, sample_idx, 19)
        v = v / jnp.linalg.norm(v)
        pairs.append((v[:4], v[4:]))
    return pairs


def unit_o_pairs() -> list[tuple[jax.Array, jax.Array]]:
    one = jnp.asarray([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=jnp.float64)
    zero = jnp.zeros((8,), dtype=jnp.float64)
    pairs = [(one, zero), (zero, one)]
    for sample_idx in range(1, SAMPLE_COUNT + 1):
        v = probe_vector(16, sample_idx, 23)
        v = v / jnp.linalg.norm(v)
        pairs.append((v[:8], v[8:]))
    return pairs


def unit_quaternion_samples() -> list[jax.Array]:
    samples = [
        jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 1.0, 0.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0, 1.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0, 0.0, 1.0], dtype=jnp.float64),
    ]
    for sample_idx in range(1, 17):
        v = probe_vector(4, sample_idx, 29)
        samples.append(v / jnp.linalg.norm(v))
    return samples


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
    hpairs = unit_h_pairs()
    opairs = unit_o_pairs()
    units = unit_quaternion_samples()

    h_input_unit_error = 0.0
    h_s4_landing_error = 0.0
    h_fiber_residual = 0.0
    for a, b in hpairs:
        out = h_hopf(a, b)
        h_input_unit_error = max(h_input_unit_error, abs(py_float(sqnorm(a) + sqnorm(b)) - 1.0))
        h_s4_landing_error = max(h_s4_landing_error, abs(py_float(jnp.linalg.norm(out)) - 1.0))
        for u in units:
            out_u = h_hopf(qmul(a, u), qmul(b, u))
            h_fiber_residual = max(h_fiber_residual, linf(out, out_u))

    nonunit_a, nonunit_b = hpairs[-1]
    nonunit_out = h_hopf(1.7 * nonunit_a, 1.7 * nonunit_b)
    nonunit_output_norm = py_float(jnp.linalg.norm(nonunit_out))
    nonunit_s4_norm_error = abs(nonunit_output_norm - 1.0)

    o_input_unit_error = 0.0
    o_s8_landing_error = 0.0
    for a, b in opairs:
        out = o_hopf(table, a, b)
        o_input_unit_error = max(o_input_unit_error, abs(py_float(sqnorm(a) + sqnorm(b)) - 1.0))
        o_s8_landing_error = max(o_s8_landing_error, abs(py_float(jnp.linalg.norm(out)) - 1.0))

    verdicts = {
        "hopf_S7_S4_lands_on_S4": h_s4_landing_error < TOL,
        "fiber_S3_invariant": h_fiber_residual < TOL,
        "octonion_S15_S8_base_lands_on_S8": o_s8_landing_error < TOL,
    }
    controls = {
        "unit_H_pair_inputs_ok": h_input_unit_error < TOL,
        "unit_O_pair_inputs_ok": o_input_unit_error < TOL,
        "nonunit_H_pair_off_S4_control_ok": nonunit_s4_norm_error > 0.5,
    }
    controls["control_miswired"] = not (
        controls["unit_H_pair_inputs_ok"] and controls["unit_O_pair_inputs_ok"] and controls["nonunit_H_pair_off_S4_control_ok"]
    )
    shared_scalars = {
        "H_pair_sample_count": len(hpairs),
        "H_fiber_unit_sample_count": len(units),
        "H_input_unit_error": h_input_unit_error,
        "H_S4_landing_max_norm_error": h_s4_landing_error,
        "H_S3_fiber_invariance_max_linf": h_fiber_residual,
        "nonunit_H_output_norm": nonunit_output_norm,
        "nonunit_H_S4_norm_error": nonunit_s4_norm_error,
        "O_pair_sample_count": len(opairs),
        "O_input_unit_error": o_input_unit_error,
        "O_S8_base_landing_max_norm_error": o_s8_landing_error,
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
        "claim_ceiling": "Finite Hopf-rung diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind": "classical",
        "sim_class": "hopf_geometry_rung_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "rung_note": "Standard Hopf fibrations: R:S1->S0, C:S3->S2, H:S7->S4, O:S15->S8. This sim verifies the H-Hopf S7->S4 map and only base-landing for the O-Hopf S15->S8 map.",
        "tool_manifest": {
            "JAX": "load-bearing quaternion and octonion pair Hopf computations",
            "jax.numpy": "load-bearing x64 S4/S8 norms and fiber residuals",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive"},
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": "The quaternion Hopf map sends unit H-pairs on S7 to S4 and is invariant under right multiplication by unit quaternions, while the octonion-pair rung lands on S8 without making a fiber claim here.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not verdicts["hopf_S7_S4_lands_on_S4"]
        or not verdicts["fiber_S3_invariant"]
        or not verdicts["octonion_S15_S8_base_lands_on_S8"]
        or bool(result["parity"]["stop_condition_fired"])
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    n = result["numbers"]
    print("octonion_hopf_S7_S4 - JAX full sim")
    print(
        f"hopf_S7_S4_lands_on_S4={str(result['verdicts']['hopf_S7_S4_lands_on_S4']).lower()} "
        f"H_S4_landing_max_norm_error={n['H_S4_landing_max_norm_error']}"
    )
    print(
        f"fiber_S3_invariant={str(result['verdicts']['fiber_S3_invariant']).lower()} "
        f"H_S3_fiber_invariance_max_linf={n['H_S3_fiber_invariance_max_linf']}"
    )
    print(
        f"octonion_S15_S8_base_lands_on_S8={str(result['verdicts']['octonion_S15_S8_base_lands_on_S8']).lower()} "
        f"O_S8_base_landing_max_norm_error={n['O_S8_base_landing_max_norm_error']}"
    )
    print(
        f"nonunit_H_pair_off_S4_control_ok={str(result['controls']['nonunit_H_pair_off_S4_control_ok']).lower()} "
        f"nonunit_H_output_norm={n['nonunit_H_output_norm']}"
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
