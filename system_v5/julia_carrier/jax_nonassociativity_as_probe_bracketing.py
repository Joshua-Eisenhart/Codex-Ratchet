#!/usr/bin/env python3
# object_id: nonassociativity_as_probe_bracketing
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


OBJECT_ID = "nonassociativity_as_probe_bracketing"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "nonassociativity_as_probe_bracketing_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "nonassociativity_as_probe_bracketing_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
SAMPLE_COUNT = 64
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


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def conj_alg(x: jax.Array) -> jax.Array:
    signs = [1.0] + [-1.0] * (x.shape[0] - 1)
    return x * jnp.asarray(signs, dtype=jnp.float64)


def associator(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def probe_readout(table: jax.Array, m: jax.Array, v: jax.Array) -> jax.Array:
    return multiply(table, conj_alg(m), v)[0]


def probe_metrics(table: jax.Array, assoc: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    values = jnp.asarray([probe_readout(table, basis(dim, idx), assoc) for idx in range(dim)], dtype=jnp.float64)
    basis_reconstructed_norm = jnp.sqrt(jnp.sum(values * values))
    assoc_norm = jnp.linalg.norm(assoc)
    assoc_norm_value = py_float(assoc_norm)
    basis_max = jnp.max(jnp.abs(values))
    best_idx = int(jax.device_get(jnp.argmax(jnp.abs(values))))
    if assoc_norm_value > TOL:
        optimal_value = py_float(jnp.abs(probe_readout(table, assoc / assoc_norm, assoc)))
    else:
        optimal_value = 0.0
    return {
        "assoc_norm": assoc_norm_value,
        "basis_max_probe_abs": py_float(basis_max),
        "basis_reconstructed_norm": py_float(basis_reconstructed_norm),
        "basis_reconstruction_error": py_float(jnp.abs(basis_reconstructed_norm - assoc_norm)),
        "best_basis_probe_index0": best_idx,
        "optimal_unit_probe_abs": optimal_value,
        "optimal_unit_probe_norm_error": abs(optimal_value - assoc_norm_value),
    }


def analyze_table(name: str, table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    max_assoc_norm = 0.0
    max_basis_probe = 0.0
    max_optimal_probe = 0.0
    max_basis_reconstruction_error = 0.0
    max_optimal_probe_norm_error = 0.0
    witness: dict[str, Any] = {"kind": "none"}
    for sample_idx in range(1, SAMPLE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 3)
        y = probe_vector(dim, sample_idx, 5)
        z = probe_vector(dim, sample_idx, 7)
        assoc = associator(table, x, y, z)
        metrics = probe_metrics(table, assoc)
        if metrics["assoc_norm"] > max_assoc_norm:
            max_assoc_norm = metrics["assoc_norm"]
            witness = {
                "sample_idx": sample_idx,
                "assoc_norm": metrics["assoc_norm"],
                "best_basis_probe_index0": metrics["best_basis_probe_index0"],
                "basis_max_probe_abs": metrics["basis_max_probe_abs"],
                "optimal_unit_probe_abs": metrics["optimal_unit_probe_abs"],
            }
        max_basis_probe = max(max_basis_probe, metrics["basis_max_probe_abs"])
        max_optimal_probe = max(max_optimal_probe, metrics["optimal_unit_probe_abs"])
        max_basis_reconstruction_error = max(max_basis_reconstruction_error, metrics["basis_reconstruction_error"])
        max_optimal_probe_norm_error = max(max_optimal_probe_norm_error, metrics["optimal_unit_probe_norm_error"])

    alt_xxy = 0.0
    alt_xyy = 0.0
    for sample_idx in range(1, SAMPLE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 11)
        y = probe_vector(dim, sample_idx, 13)
        alt_xxy = max(alt_xxy, py_float(jnp.linalg.norm(associator(table, x, x, y))))
        alt_xyy = max(alt_xyy, py_float(jnp.linalg.norm(associator(table, x, y, y))))

    return {
        "name": name,
        "max_assoc_norm": max_assoc_norm,
        "max_basis_probe_abs": max_basis_probe,
        "max_optimal_unit_probe_abs": max_optimal_probe,
        "max_basis_reconstruction_error": max_basis_reconstruction_error,
        "max_optimal_unit_probe_norm_error": max_optimal_probe_norm_error,
        "alternativity_xxy_max_norm": alt_xxy,
        "alternativity_xyy_max_norm": alt_xyy,
        "witness": witness,
    }


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
    h = analyze_table("H", quaternion_table())
    o = analyze_table("O", octonion_table())
    verdicts = {
        "H_bracketing_probe_indistinguishable": h["max_assoc_norm"] < TOL and h["max_basis_probe_abs"] < TOL,
        "O_bracketing_probe_distinguishable": (
            o["max_assoc_norm"] > STRICT_STOP_TOL
            and o["max_basis_probe_abs"] > TOL
            and o["max_optimal_unit_probe_norm_error"] < TOL
        ),
    }
    controls = {
        "H_associativity_control_ok": h["max_assoc_norm"] < TOL,
        "O_general_nonassociativity_control_ok": o["max_assoc_norm"] > STRICT_STOP_TOL,
        "O_alternativity_control_ok": max(o["alternativity_xxy_max_norm"], o["alternativity_xyy_max_norm"]) < TOL,
    }
    controls["control_miswired"] = not (
        controls["H_associativity_control_ok"]
        and controls["O_general_nonassociativity_control_ok"]
        and controls["O_alternativity_control_ok"]
    )
    shared_scalars = {
        "sample_count": SAMPLE_COUNT,
        "H_max_assoc_norm": h["max_assoc_norm"],
        "H_max_basis_probe_abs": h["max_basis_probe_abs"],
        "H_max_basis_reconstruction_error": h["max_basis_reconstruction_error"],
        "H_max_optimal_unit_probe_abs": h["max_optimal_unit_probe_abs"],
        "O_max_assoc_norm": o["max_assoc_norm"],
        "O_max_basis_probe_abs": o["max_basis_probe_abs"],
        "O_max_optimal_unit_probe_abs": o["max_optimal_unit_probe_abs"],
        "O_max_basis_reconstruction_error": o["max_basis_reconstruction_error"],
        "O_max_optimal_unit_probe_norm_error": o["max_optimal_unit_probe_norm_error"],
        "O_alternativity_xxy_max_norm": o["alternativity_xxy_max_norm"],
        "O_alternativity_xyy_max_norm": o["alternativity_xyy_max_norm"],
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
        "claim_ceiling": "Finite bracketing/probe diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind": "classical",
        "sim_class": "probe_relative_bracketing_concept_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "probe_note": "Basis probes f_M(v)=Re(conj(M)v) recover the associator components; sqrt(sum basis readouts^2)=||associator||. The optimal unit probe M=assoc/||assoc|| attains ||assoc|| when assoc is nonzero.",
        "tool_manifest": {
            "JAX": "load-bearing quaternion/octonion multiplication, associators, and probe readouts",
            "jax.numpy": "load-bearing x64 associator norms and probe reconstruction norms",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive"},
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "witness": {"H": h["witness"], "O": o["witness"]},
        "plain_sentence": "Quaternion bracketings are probe-indistinguishable because the associator vanishes, while generic octonion bracketings have a nonzero associator resolved by component probes and by the optimal unit probe; alternativity still kills repeated-input associators.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not verdicts["H_bracketing_probe_indistinguishable"]
        or not verdicts["O_bracketing_probe_distinguishable"]
        or bool(result["parity"]["stop_condition_fired"])
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    n = result["numbers"]
    print("nonassociativity_as_probe_bracketing - JAX full sim")
    print(
        f"H_bracketing_probe_indistinguishable={str(result['verdicts']['H_bracketing_probe_indistinguishable']).lower()} "
        f"H_max_assoc_norm={n['H_max_assoc_norm']} H_max_basis_probe_abs={n['H_max_basis_probe_abs']}"
    )
    print(
        f"O_bracketing_probe_distinguishable={str(result['verdicts']['O_bracketing_probe_distinguishable']).lower()} "
        f"O_max_assoc_norm={n['O_max_assoc_norm']} O_max_basis_probe_abs={n['O_max_basis_probe_abs']} "
        f"O_max_optimal_unit_probe_abs={n['O_max_optimal_unit_probe_abs']}"
    )
    print(
        f"O_alternativity_control_ok={str(result['controls']['O_alternativity_control_ok']).lower()} "
        f"O_alternativity_xxy_max_norm={n['O_alternativity_xxy_max_norm']} O_alternativity_xyy_max_norm={n['O_alternativity_xyy_max_norm']}"
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
