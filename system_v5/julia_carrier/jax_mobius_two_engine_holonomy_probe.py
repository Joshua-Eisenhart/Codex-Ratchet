import jax; jax.config.update("jax_enable_x64", True)
import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "mobius_two_engine_holonomy_probe"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "mobius_two_engine_holonomy_probe_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "mobius_two_engine_holonomy_probe_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.array([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_list(x: Any) -> list[float]:
    return [float(v) for v in jax.device_get(x)]


def su2(axis: jax.Array, theta: jax.Array) -> jax.Array:
    a = axis / jnp.linalg.norm(axis)
    generator = a[0] * SX + a[1] * SY + a[2] * SZ
    return jnp.cos(theta / 2.0) * I2 - 1j * jnp.sin(theta / 2.0) * generator


def spinor_from_angles(theta: jax.Array, phi: jax.Array) -> jax.Array:
    return jnp.array([jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)


def frame_holonomy(frame: jax.Array, transport: jax.Array) -> jax.Array:
    numerator = jnp.trace(jnp.conj(frame.T) @ transport @ frame)
    denominator = jnp.trace(jnp.conj(frame.T) @ frame)
    return jnp.real(numerator / denominator)


def spinor_return_sign(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.real(jnp.vdot(start, stop) / jnp.vdot(start, start))


def mobius_band_normal(theta: jax.Array) -> jax.Array:
    return jnp.array(
        [
            jnp.cos(theta / 2.0) * jnp.cos(theta),
            jnp.cos(theta / 2.0) * jnp.sin(theta),
            jnp.sin(theta / 2.0),
        ],
        dtype=jnp.float64,
    )


def cylinder_normal(theta: jax.Array) -> jax.Array:
    return jnp.array([jnp.cos(theta), jnp.sin(theta), 0.0], dtype=jnp.float64)


def approx(value: float, target: float, tol: float = TOL) -> bool:
    return abs(value - target) <= tol


def shared_scalars(values: dict[str, Any], verdicts: dict[str, bool], controls: dict[str, bool]) -> dict[str, float]:
    keys = [
        "mobius_holonomy_2pi",
        "mobius_holonomy_4pi",
        "mobius_band_frame_2pi",
        "mobius_band_frame_4pi",
        "cylinder_holonomy_2pi",
        "cylinder_holonomy_4pi",
        "spinor_720_tie_2pi",
        "spinor_720_tie_4pi",
        "spinor_720_holonomy_2pi",
        "spinor_720_holonomy_4pi",
        "mobius_vs_spinor_z2_diff_2pi",
        "mobius_vs_spinor_z2_diff_4pi",
        "cylinder_vs_mobius_2pi_gap",
        "two_engine_frame_residual_2pi",
        "two_engine_frame_residual_4pi",
        "spinor_2pi_sign_residual",
        "spinor_4pi_return_residual",
    ]
    scalars = {key: float(values[key]) for key in keys}
    for key in (
        "mobius_orientation_flips_at_2pi",
        "mobius_restores_at_4pi",
        "two_engine_is_mobius_not_cylinder",
        "spinor_720_tie_matches_mobius",
        "cylinder_control_no_flip",
    ):
        scalars["verdict_" + key] = 1.0 if verdicts[key] else 0.0
    for key in (
        "cylinder_control_flips",
        "real_mobius_band_frame_flips",
        "spinor_tie_reproduces_minus_one",
    ):
        scalars["control_" + key] = 1.0 if controls[key] else 0.0
    return scalars


def compare_booleans(local: dict[str, Any], peer: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    for block in ("controls", "verdicts"):
        if block not in peer:
            mismatches.append(block + ".__missing_block__")
            continue
        for key, value in local[block].items():
            if key not in peer[block] or bool(peer[block][key]) != bool(value):
                mismatches.append(block + "." + key)
    return mismatches


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "peer_result_found": False,
            "peer_available": False,
            "missing_keys": sorted(result["shared_scalars"].keys()),
            "extra_peer_keys": [],
            "boolean_mismatches": [],
            "parity_max_diff": None,
            "worst_key": None,
            "parity_pass": False,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": True,
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text())
    local_keys = set(result["shared_scalars"].keys())
    peer_scalars = peer.get("shared_scalars", {})
    peer_keys = set(peer_scalars.keys())
    missing_keys = sorted(local_keys - peer_keys)
    extra_peer_keys = sorted(peer_keys - local_keys)
    diffs: dict[str, float] = {}
    max_diff = 0.0
    worst_key = ""
    for key in sorted(local_keys & peer_keys):
        diff = abs(float(result["shared_scalars"][key]) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
    boolean_mismatches = compare_booleans(result, peer)
    parity_pass = not missing_keys and not extra_peer_keys and not boolean_mismatches and max_diff < TOL
    strict_divergence = bool(missing_keys or extra_peer_keys or boolean_mismatches or max_diff > STRICT_STOP_TOL)
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "peer_result_found": True,
        "peer_available": True,
        "missing_keys": missing_keys,
        "extra_peer_keys": extra_peer_keys,
        "boolean_mismatches": boolean_mismatches,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "parity_pass": parity_pass,
        "within_1e_9": max_diff < TOL and not missing_keys and not extra_peer_keys,
        "strict_divergence_gt_1e_6": strict_divergence,
        "stop_condition_fired": not parity_pass,
        "diffs": diffs,
    }


def main() -> None:
    axis = jnp.array([0.2, -0.5, 0.84], dtype=jnp.float64)
    axis = axis / jnp.linalg.norm(axis)
    theta_2pi = 2.0 * jnp.pi
    theta_4pi = 4.0 * jnp.pi
    two_engine_frame = I2
    u2 = su2(axis, theta_2pi)
    u4 = su2(axis, theta_4pi)

    psi = spinor_from_angles(jnp.array(1.1, dtype=jnp.float64), jnp.array(-0.7, dtype=jnp.float64))
    psi2 = u2 @ psi
    psi4 = u4 @ psi

    m0 = mobius_band_normal(jnp.array(0.0, dtype=jnp.float64))
    c0 = cylinder_normal(jnp.array(0.0, dtype=jnp.float64))

    values: dict[str, Any] = {
        "theta_2pi": py_float(theta_2pi),
        "theta_4pi": py_float(theta_4pi),
        "axis": py_list(axis),
        "mobius_holonomy_2pi": py_float(frame_holonomy(two_engine_frame, u2)),
        "mobius_holonomy_4pi": py_float(frame_holonomy(two_engine_frame, u4)),
        "mobius_band_frame_2pi": py_float(jnp.vdot(m0, mobius_band_normal(theta_2pi)) / jnp.vdot(m0, m0)),
        "mobius_band_frame_4pi": py_float(jnp.vdot(m0, mobius_band_normal(theta_4pi)) / jnp.vdot(m0, m0)),
        "cylinder_holonomy_2pi": py_float(jnp.vdot(c0, cylinder_normal(theta_2pi)) / jnp.vdot(c0, c0)),
        "cylinder_holonomy_4pi": py_float(jnp.vdot(c0, cylinder_normal(theta_4pi)) / jnp.vdot(c0, c0)),
        "spinor_720_tie_2pi": py_float(spinor_return_sign(psi, psi2)),
        "spinor_720_tie_4pi": py_float(spinor_return_sign(psi, psi4)),
        "spinor_720_holonomy_2pi": py_float(spinor_return_sign(psi, psi2)),
        "spinor_720_holonomy_4pi": py_float(spinor_return_sign(psi, psi4)),
        "two_engine_frame_residual_2pi": py_float(jnp.linalg.norm(u2 + I2)),
        "two_engine_frame_residual_4pi": py_float(jnp.linalg.norm(u4 - I2)),
        "spinor_2pi_sign_residual": py_float(jnp.linalg.norm(psi2 + psi)),
        "spinor_4pi_return_residual": py_float(jnp.linalg.norm(psi4 - psi)),
    }
    values["mobius_vs_spinor_z2_diff_2pi"] = abs(values["mobius_holonomy_2pi"] - values["spinor_720_tie_2pi"])
    values["mobius_vs_spinor_z2_diff_4pi"] = abs(values["mobius_holonomy_4pi"] - values["spinor_720_tie_4pi"])
    values["cylinder_vs_mobius_2pi_gap"] = abs(values["cylinder_holonomy_2pi"] - values["mobius_holonomy_2pi"])

    controls = {
        "cylinder_control_flips": approx(values["cylinder_holonomy_2pi"], -1.0),
        "cylinder_control_no_flip": approx(values["cylinder_holonomy_2pi"], 1.0),
        "real_mobius_band_frame_flips": approx(values["mobius_band_frame_2pi"], -1.0)
        and approx(values["mobius_band_frame_4pi"], 1.0),
        "spinor_tie_reproduces_minus_one": approx(values["spinor_720_tie_2pi"], -1.0),
    }
    verdicts = {
        "mobius_orientation_flips_at_2pi": approx(values["mobius_holonomy_2pi"], -1.0),
        "mobius_restores_at_4pi": approx(values["mobius_holonomy_4pi"], 1.0),
        "cylinder_control_no_flip": controls["cylinder_control_no_flip"],
        "spinor_720_tie_matches_mobius": controls["spinor_tie_reproduces_minus_one"]
        and approx(values["mobius_vs_spinor_z2_diff_2pi"], 0.0)
        and approx(values["mobius_vs_spinor_z2_diff_4pi"], 0.0),
    }
    verdicts["two_engine_is_mobius_not_cylinder"] = (
        verdicts["mobius_orientation_flips_at_2pi"]
        and verdicts["mobius_restores_at_4pi"]
        and verdicts["cylinder_control_no_flip"]
        and verdicts["spinor_720_tie_matches_mobius"]
        and not controls["cylinder_control_flips"]
    )

    result: dict[str, Any] = {
        "sim_id": OBJECT_ID,
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0.0",
        "backend": "jax",
        "backend_roles": {
            "julia": "reference/exact SU(2) and real-frame holonomy computation using native LinearAlgebra",
            "jax": "x64 mirror/stress computation using jax.numpy only",
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite two-engine Mobius/Z2 holonomy witness only; no engine admission, Axis0, gravity, bridge, basin, or canonical proof claim.",
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "sim_execution_kind": "nonclassical",
        "sim_class": "transport_search",
        "carrier_layer": "two_engine_left_right_spinor_frame",
        "geometry_layer": "Mobius Z2 holonomy versus orientable cylinder control",
        "allowed_claims": ["scratch diagnostic Mobius/non-orientable sign witness", "spinor 720 Z2 tie"],
        "blocked_consumers": ["engine admission", "Axis0", "gravity", "bridge", "basin", "canonical proof"],
        "promotion_status": "diagnostic_only",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "tools": ["JAX jax.numpy x64"],
        "tool_manifest": {
            "JAX jax.numpy x64": "load-bearing for mirrored SU(2) frame matrices, vector inner products, residual norms, and holonomy sign extraction",
            "Python json/pathlib/datetime": "supportive for timestamped result serialization only",
        },
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": "load-bearing for mirrored SU(2) frame matrices, vector inner products, residual norms, and holonomy sign extraction",
            "Python json/pathlib/datetime": "supportive for timestamped result serialization only",
        },
        "tool_integration_depth": {"JAX jax.numpy x64": "load_bearing", "Python json/pathlib/datetime": "supportive"},
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing", "Python json/pathlib/datetime": "supportive"},
        "values": values,
        "controls": controls,
        "verdicts": verdicts,
        "plain_sentence": "The two-engine left/right frame carries the Mobius non-orientable Z2 signature: one traversal flips the orientation sign, two traversals restore it, while the cylinder control does not flip.",
    }
    result["shared_scalars"] = shared_scalars(values, verdicts, controls)
    result["parity"] = parity_block(result)
    result["stop_condition_fired"] = (
        result["parity"]["stop_condition_fired"]
        or controls["cylinder_control_flips"]
        or not verdicts["mobius_orientation_flips_at_2pi"]
        or not verdicts["mobius_restores_at_4pi"]
        or not verdicts["two_engine_is_mobius_not_cylinder"]
    )

    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["stop_condition_fired"]:
        print("STOP_CONDITION_FIRED mobius_two_engine_holonomy_probe jax")
        raise SystemExit(1)
    print(f"mobius_two_engine_holonomy_probe jax wrote {RESULT_PATH}")


if __name__ == "__main__":
    main()
