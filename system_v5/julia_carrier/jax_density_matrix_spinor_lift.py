#!/usr/bin/env python3
# object_id: density_matrix_spinor_lift
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


OBJECT_ID = "density_matrix_spinor_lift"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "density_matrix_spinor_lift_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "density_matrix_spinor_lift_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.array([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def dm(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return jnp.array(
        [jnp.real(jnp.trace(rho @ SX)), jnp.real(jnp.trace(rho @ SY)), jnp.real(jnp.trace(rho @ SZ))],
        dtype=jnp.float64,
    )


def rho_from_bloch(r: jax.Array) -> jax.Array:
    return 0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def spinor_from_angles(theta: float, phi: float) -> jax.Array:
    return jnp.array([jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)


def su2(axis: jax.Array, theta: float) -> jax.Array:
    a = axis / jnp.linalg.norm(axis)
    generator = a[0] * SX + a[1] * SY + a[2] * SZ
    return jnp.cos(theta / 2.0) * I2 - 1j * jnp.sin(theta / 2.0) * generator


def phase_factor(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.vdot(start, stop) / jnp.vdot(start, start)


def density_overlap(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(jnp.conj(start.T) @ stop)) / jnp.real(jnp.trace(jnp.conj(start.T) @ start))


def partial_trace_ancilla(psi4: jax.Array) -> jax.Array:
    psi_matrix = jnp.reshape(psi4, (2, 2))
    return psi_matrix @ jnp.conj(psi_matrix.T)


def mixed_purification(rho: jax.Array) -> jax.Array:
    values, vectors = jnp.linalg.eigh(rho)
    psi_matrix = vectors * jnp.sqrt(jnp.maximum(values, 0.0))[None, :]
    return jnp.reshape(psi_matrix, (4,))


def shared_scalars(values: dict[str, float], verdicts: dict[str, bool], controls: dict[str, bool]) -> dict[str, float]:
    keys = [
        "trace_rho_residual",
        "hermitian_residual",
        "rho_reconstruction_residual",
        "bloch_norm",
        "idempotency_residual",
        "spinor_norm_residual",
        "hopf_s2_residual",
        "phase_invariance_residual",
        "base_holonomy_2pi",
        "lift_holonomy_2pi",
        "base_holonomy_4pi",
        "lift_holonomy_4pi",
        "rho_2pi_return_residual",
        "psi_2pi_sign_residual",
        "rho_4pi_return_residual",
        "psi_4pi_return_residual",
        "pure_spinor_manifold_dim",
        "base_sphere_dim",
        "fiber_dim",
        "mixed_bloch_norm",
        "mixed_purity",
        "mixed_rank",
        "mixed_idempotency_residual",
        "ancilla_purification_residual",
        "c4_purification_norm_residual",
    ]
    scalars = {key: float(values[key]) for key in keys}
    for key in ("rho_is_base_spinor_is_lift", "pure_states_are_S2", "purification_lands_on_unit_c4"):
        scalars["verdict_" + key] = 1.0 if verdicts[key] else 0.0
    scalars["control_mixed_no_single_s3_point"] = 1.0 if controls["mixed_no_single_s3_point"] else 0.0
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
    psi = spinor_from_angles(1.1, -0.7)
    rho = dm(psi)
    r = bloch_from_rho(rho)
    rho_rebuilt = rho_from_bloch(r)
    phase = jnp.exp(1j * 0.83)
    rho_phase = dm(phase * psi)

    axis = jnp.array([0.2, -0.5, 0.84], dtype=jnp.float64)
    u2 = su2(axis, 2.0 * jnp.pi)
    u4 = su2(axis, 4.0 * jnp.pi)
    psi2 = u2 @ psi
    psi4 = u4 @ psi
    rho2 = u2 @ rho @ jnp.conj(u2.T)
    rho4 = u4 @ rho @ jnp.conj(u4.T)

    mixed_r = 0.4 * r
    mixed_rho = rho_from_bloch(mixed_r)
    mixed_eigs = jnp.linalg.eigvalsh(mixed_rho)
    mixed_rank = py_float(jnp.sum(mixed_eigs > TOL))
    psi4_mixed = mixed_purification(mixed_rho)
    mixed_from_ancilla = partial_trace_ancilla(psi4_mixed)

    values = {
        "trace_rho_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0)),
        "hermitian_residual": py_float(jnp.linalg.norm(rho - jnp.conj(rho.T))),
        "rho_reconstruction_residual": py_float(jnp.linalg.norm(rho - rho_rebuilt)),
        "bloch_norm": py_float(jnp.linalg.norm(r)),
        "idempotency_residual": py_float(jnp.linalg.norm(rho @ rho - rho)),
        "spinor_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(psi, psi)) - 1.0)),
        "hopf_s2_residual": py_float(jnp.abs(jnp.linalg.norm(r) - 1.0)),
        "phase_invariance_residual": py_float(jnp.linalg.norm(rho_phase - rho)),
        "base_holonomy_2pi": py_float(density_overlap(rho, rho2)),
        "lift_holonomy_2pi": py_float(jnp.real(phase_factor(psi, psi2))),
        "base_holonomy_4pi": py_float(density_overlap(rho, rho4)),
        "lift_holonomy_4pi": py_float(jnp.real(phase_factor(psi, psi4))),
        "rho_2pi_return_residual": py_float(jnp.linalg.norm(rho2 - rho)),
        "psi_2pi_sign_residual": py_float(jnp.linalg.norm(psi2 + psi)),
        "rho_4pi_return_residual": py_float(jnp.linalg.norm(rho4 - rho)),
        "psi_4pi_return_residual": py_float(jnp.linalg.norm(psi4 - psi)),
        "pure_spinor_manifold_dim": float(2 * psi.shape[0] - 1),
        "base_sphere_dim": float(r.shape[0] - 1),
        "fiber_dim": float(2 * psi.shape[0] - 1) - float(r.shape[0] - 1),
        "mixed_bloch_norm": py_float(jnp.linalg.norm(mixed_r)),
        "mixed_purity": py_float(jnp.real(jnp.trace(mixed_rho @ mixed_rho))),
        "mixed_rank": mixed_rank,
        "mixed_idempotency_residual": py_float(jnp.linalg.norm(mixed_rho @ mixed_rho - mixed_rho)),
        "ancilla_purification_residual": py_float(jnp.linalg.norm(mixed_from_ancilla - mixed_rho)),
        "c4_purification_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(psi4_mixed, psi4_mixed)) - 1.0)),
    }
    controls = {
        "mixed_no_single_s3_point": values["mixed_bloch_norm"] < 1.0 - TOL
        and values["mixed_purity"] < 1.0 - TOL
        and values["mixed_rank"] == 2.0
        and values["mixed_idempotency_residual"] > TOL,
        "mixed_requires_ancilla_for_purification": values["ancilla_purification_residual"] <= TOL,
    }
    verdicts = {
        "rho_is_base_spinor_is_lift": abs(values["base_holonomy_2pi"] - 1.0) <= TOL
        and abs(values["lift_holonomy_2pi"] + 1.0) <= TOL
        and values["fiber_dim"] == 1.0,
        "pure_states_are_S2": values["hopf_s2_residual"] <= TOL and values["idempotency_residual"] <= TOL,
        "purification_lands_on_unit_c4": values["c4_purification_norm_residual"] <= TOL
        and values["ancilla_purification_residual"] <= TOL,
    }
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Density-matrix base to spinor-lift diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or 720-engine claim.",
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "tools": ["JAX jax.numpy x64"],
        "tool_manifest": {"JAX jax.numpy x64": "load-bearing for independent density matrices, eigensystem rank control, residuals, and holonomy signs"},
        "TOOL_MANIFEST": {"JAX jax.numpy x64": "load-bearing for independent density matrices, eigensystem rank control, residuals, and holonomy signs"},
        "tool_integration_depth": {"JAX jax.numpy x64": "load_bearing"},
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing"},
        "values": values,
        "controls": controls,
        "verdicts": verdicts,
        "plain_sentence": "The density matrix is the phase-forgetting base: lifting a pure boundary state to a spinor adds the U(1) fiber where the 2pi sign lives.",
    }
    result["shared_scalars"] = shared_scalars(values, verdicts, controls)
    result["parity"] = parity_block(result)
    result["stop_condition_fired"] = (
        result["parity"]["stop_condition_fired"]
        or not controls["mixed_no_single_s3_point"]
        or not controls["mixed_requires_ancilla_for_purification"]
        or not verdicts["rho_is_base_spinor_is_lift"]
        or not verdicts["pure_states_are_S2"]
        or not verdicts["purification_lands_on_unit_c4"]
    )
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["stop_condition_fired"]:
        print("STOP_CONDITION_FIRED density_matrix_spinor_lift")
        raise SystemExit(1)
    print(f"density_matrix_spinor_lift jax wrote {RESULT_PATH}")


if __name__ == "__main__":
    main()
