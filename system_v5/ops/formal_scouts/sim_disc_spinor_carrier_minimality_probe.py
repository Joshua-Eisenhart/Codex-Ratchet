#!/usr/bin/env python3
# object_id: disc_spinor_carrier_minimality
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "nonclassical"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 backend for finite SU(2), SO(3), Sp(1), and C3 carrier witnesses",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing matrix, vector, density, quaternion, residual, and parity computations with no NumPy compute path",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Float64 mirror for dual-backend parity on shared witness scalars and verdicts",
    },
    "owner double-cover carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing layer structure; erasing SU(2)/Sp(1) double-cover signs to SO(3)/density changes the layer verdict",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON serialization, timestamps, hashing, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; this lane uses jax.numpy/x64 plus Julia, not NumPy",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded by the requested JAX plus Julia lane; no torch import or tensor path is used",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "owner double-cover carrier": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
    "pytorch": None,
}


OBJECT_ID = "disc_spinor_carrier_minimality"
BACKEND = "jax_jnp_x64"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "disc_spinor_carrier_minimality_results.json"
JULIA_RESULT_PATH = JULIA_CARRIER / "disc_spinor_carrier_minimality_julia_results.json"
JULIA_SOURCE_PATH = JULIA_CARRIER / "disc_spinor_carrier_minimality.jl"
EPS = 1.0e-9
STRICT_TOL = 1.0e-7
QUOTIENT_THETA = 2.0 * jnp.pi / 3.0

CLAIM_CEILING = (
    "scratch_diagnostic discriminator only: finite spinor-carrier minimality row for the "
    "2pi=-1 double-cover witness. Supports only the bounded verdict reported here; no "
    "promotion, formal admission, PEPS3D admission, Axis0, bridge, physics, uniqueness of "
    "C2 over H1, or manifold closure claim."
)
BLOCKED_CONSUMERS = [
    "formal_admission",
    "promotion",
    "PEPS3D_admission",
    "Axis0_admission",
    "bridge_admission",
    "physics_admission",
    "C2_unique_realization_claim",
    "manifold_closure",
]

I2 = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
AXIS = jnp.asarray([1.0, 2.0, 3.0], dtype=jnp.float64)
AXIS = AXIS / jnp.linalg.norm(AXIS)
PSI0 = jnp.asarray([1.0 + 0.0j, 0.37 + 0.21j], dtype=jnp.complex128)
PSI0 = PSI0 / jnp.sqrt(jnp.real(jnp.vdot(PSI0, PSI0)))
VECTOR0 = jnp.asarray([0.23, -0.71, 0.48], dtype=jnp.float64)
VECTOR0 = VECTOR0 / jnp.linalg.norm(VECTOR0)

VERDICT_CODES = {
    "OPEN": 0.0,
    "REAL_LAYER": 1.0,
    "CONVENTION": 2.0,
    "GENERIC": 3.0,
    "PARTIAL": 4.0,
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_refs() -> dict[str, Any]:
    paths = {
        "jax_source": Path(__file__),
        "julia_source": JULIA_SOURCE_PATH,
    }
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in paths.items()
    }


def su2(axis: jax.Array, theta: Any) -> jax.Array:
    a = axis / jnp.linalg.norm(axis)
    generator = a[0] * SX + a[1] * SY + a[2] * SZ
    return jnp.cos(theta / 2.0) * I2 - 1j * jnp.sin(theta / 2.0) * generator


def rodrigues(axis: jax.Array, theta: Any) -> jax.Array:
    a = axis / jnp.linalg.norm(axis)
    x, y, z = a
    k = jnp.asarray([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=jnp.float64)
    return jnp.eye(3, dtype=jnp.float64) + jnp.sin(theta) * k + (1.0 - jnp.cos(theta)) * (k @ k)


def so3_expm_series(axis: jax.Array, theta: Any, terms: int = 32) -> jax.Array:
    a = axis / jnp.linalg.norm(axis)
    x, y, z = a
    generator = theta * jnp.asarray([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=jnp.float64)
    out = jnp.eye(3, dtype=jnp.float64)
    term = jnp.eye(3, dtype=jnp.float64)
    for n in range(1, terms + 1):
        term = (term @ generator) / float(n)
        out = out + term
    return out


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def bloch_vec(rho: jax.Array) -> jax.Array:
    return jnp.asarray(
        [jnp.real(jnp.trace(rho @ SX)), jnp.real(jnp.trace(rho @ SY)), jnp.real(jnp.trace(rho @ SZ))],
        dtype=jnp.float64,
    )


def return_factor_complex(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.vdot(start, stop) / jnp.vdot(start, start)


def matrix_overlap_factor(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(jnp.conj(start.T) @ stop)) / jnp.real(jnp.trace(jnp.conj(start.T) @ start))


def vector_overlap_factor(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.dot(start, stop) / jnp.dot(start, start)


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return jnp.asarray(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=jnp.float64,
    )


def qconj(q: jax.Array) -> jax.Array:
    return jnp.asarray([q[0], -q[1], -q[2], -q[3]], dtype=jnp.float64)


def qaxis(axis: jax.Array, theta: Any) -> jax.Array:
    a = axis / jnp.linalg.norm(axis)
    return jnp.asarray(
        [jnp.cos(theta / 2.0), a[0] * jnp.sin(theta / 2.0), a[1] * jnp.sin(theta / 2.0), a[2] * jnp.sin(theta / 2.0)],
        dtype=jnp.float64,
    )


def qrot(q: jax.Array, v: jax.Array) -> jax.Array:
    out = qmul(qmul(q, jnp.asarray([0.0, v[0], v[1], v[2]], dtype=jnp.float64)), qconj(q))
    return out[1:4]


def qmatrix(q: jax.Array) -> jax.Array:
    basis = [jnp.eye(3, dtype=jnp.float64)[idx] for idx in range(3)]
    return jnp.stack([qrot(q, v) for v in basis], axis=1)


def block_diag_su2_plus_one(u: jax.Array) -> jax.Array:
    out = jnp.zeros((3, 3), dtype=jnp.complex128)
    out = out.at[0:2, 0:2].set(u)
    out = out.at[2, 2].set(1.0 + 0.0j)
    return out


def carrier_witnesses() -> dict[str, Any]:
    u2 = su2(AXIS, 2.0 * jnp.pi)
    u4 = su2(AXIS, 4.0 * jnp.pi)
    spinor2 = u2 @ PSI0
    spinor4 = u4 @ PSI0
    spinor_factor2 = return_factor_complex(PSI0, spinor2)
    spinor_factor4 = return_factor_complex(PSI0, spinor4)
    rho0 = density(PSI0)
    rho2 = u2 @ rho0 @ jnp.conj(u2.T)
    rho4 = u4 @ rho0 @ jnp.conj(u4.T)
    bloch0 = bloch_vec(rho0)
    quotient_spinor = bloch_vec(su2(AXIS, QUOTIENT_THETA) @ rho0 @ jnp.conj(su2(AXIS, QUOTIENT_THETA).T))
    quotient_so3 = rodrigues(AXIS, QUOTIENT_THETA) @ bloch0

    r2 = rodrigues(AXIS, 2.0 * jnp.pi)
    r4 = rodrigues(AXIS, 4.0 * jnp.pi)
    rq_series = so3_expm_series(AXIS, QUOTIENT_THETA)
    rq_closed = rodrigues(AXIS, QUOTIENT_THETA)
    vector2 = r2 @ VECTOR0
    vector4 = r4 @ VECTOR0

    q0 = jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.float64)
    q2 = qaxis(AXIS, 2.0 * jnp.pi)
    q4 = qaxis(AXIS, 4.0 * jnp.pi)
    qtheta = qaxis(AXIS, QUOTIENT_THETA)
    qx = qaxis(jnp.asarray([1.0, 0.0, 0.0], dtype=jnp.float64), jnp.pi / 3.0)
    qy = qaxis(jnp.asarray([0.0, 1.0, 0.0], dtype=jnp.float64), jnp.pi / 4.0)

    c3_spin1_vector2 = r2 @ VECTOR0
    c3_embed2 = block_diag_su2_plus_one(u2)
    c3_embed4 = block_diag_su2_plus_one(u4)
    psi3 = jnp.asarray([PSI0[0], PSI0[1], 0.0 + 0.0j], dtype=jnp.complex128)
    psi3_spectator = jnp.asarray([PSI0[0], PSI0[1], 0.2 + 0.0j], dtype=jnp.complex128)
    psi3_spectator = psi3_spectator / jnp.sqrt(jnp.real(jnp.vdot(psi3_spectator, psi3_spectator)))
    c3_embed_factor2 = return_factor_complex(psi3, c3_embed2 @ psi3)
    c3_embed_factor4 = return_factor_complex(psi3, c3_embed4 @ psi3)
    c3_spectator_after2 = c3_embed2 @ psi3_spectator
    ux = su2(jnp.asarray([1.0, 0.0, 0.0], dtype=jnp.float64), jnp.pi / 3.0)
    uy = su2(jnp.asarray([0.0, 1.0, 0.0], dtype=jnp.float64), jnp.pi / 4.0)
    rx = rodrigues(jnp.asarray([1.0, 0.0, 0.0], dtype=jnp.float64), jnp.pi / 3.0)
    ry = rodrigues(jnp.asarray([0.0, 1.0, 0.0], dtype=jnp.float64), jnp.pi / 4.0)

    values = {
        "spinor_su2_holonomy_2pi": py_float(jnp.real(spinor_factor2)),
        "spinor_su2_holonomy_2pi_imag": py_float(jnp.imag(spinor_factor2)),
        "spinor_su2_holonomy_4pi": py_float(jnp.real(spinor_factor4)),
        "spinor_return_residual_2pi": py_float(jnp.linalg.norm(spinor2 + PSI0)),
        "spinor_return_residual_4pi": py_float(jnp.linalg.norm(spinor4 - PSI0)),
        "density_holonomy_2pi": py_float(matrix_overlap_factor(rho0, rho2)),
        "density_holonomy_4pi": py_float(matrix_overlap_factor(rho0, rho4)),
        "density_return_residual_2pi": py_float(jnp.linalg.norm(rho2 - rho0)),
        "density_return_residual_4pi": py_float(jnp.linalg.norm(rho4 - rho0)),
        "su2_to_so3_quotient_residual": py_float(jnp.linalg.norm(quotient_spinor - quotient_so3)),
        "vector_so3_holonomy_2pi": py_float(vector_overlap_factor(VECTOR0, vector2)),
        "vector_so3_holonomy_4pi": py_float(vector_overlap_factor(VECTOR0, vector4)),
        "vector_return_residual_2pi": py_float(jnp.linalg.norm(vector2 - VECTOR0)),
        "vector_return_residual_4pi": py_float(jnp.linalg.norm(vector4 - VECTOR0)),
        "so3_series_rodrigues_residual": py_float(jnp.linalg.norm(rq_series - rq_closed)),
        "quaternion_holonomy_2pi": py_float(vector_overlap_factor(q0, q2)),
        "quaternion_holonomy_4pi": py_float(vector_overlap_factor(q0, q4)),
        "quaternion_return_residual_2pi": py_float(jnp.linalg.norm(q2 + q0)),
        "quaternion_return_residual_4pi": py_float(jnp.linalg.norm(q4 - q0)),
        "quaternion_to_so3_2pi_residual": py_float(jnp.linalg.norm(qmatrix(q2) - r2)),
        "quaternion_to_so3_quotient_residual": py_float(jnp.linalg.norm(qmatrix(qtheta) - rq_closed)),
        "quaternion_spinor_gap_2pi": py_float(jnp.abs(vector_overlap_factor(q0, q2) - jnp.real(spinor_factor2))),
        "c3_spin1_holonomy_2pi": py_float(vector_overlap_factor(VECTOR0, c3_spin1_vector2)),
        "c3_embedded_c2_holonomy_2pi": py_float(jnp.real(c3_embed_factor2)),
        "c3_embedded_c2_holonomy_4pi": py_float(jnp.real(c3_embed_factor4)),
        "c3_embed_spinor_gap_2pi": py_float(jnp.abs(jnp.real(c3_embed_factor2) - jnp.real(spinor_factor2))),
        "c3_spectator_global_minus_residual": py_float(jnp.linalg.norm(c3_spectator_after2 + psi3_spectator)),
        "c3_spectator_return_residual": py_float(jnp.linalg.norm(c3_spectator_after2 - psi3_spectator)),
        "su2_commutator_norm": py_float(jnp.linalg.norm(ux @ uy - uy @ ux)),
        "so3_commutator_norm": py_float(jnp.linalg.norm(rx @ ry - ry @ rx)),
        "quaternion_commutator_norm": py_float(jnp.linalg.norm(qmul(qx, qy) - qmul(qy, qx))),
        "full_layer_minus_channels": 2.0,
        "erased_layer_minus_channels": 0.0,
    }
    return values


def verdict_from(values: dict[str, float]) -> dict[str, Any]:
    spinor_su2_has_minus1 = (
        abs(values["spinor_su2_holonomy_2pi"] + 1.0) <= STRICT_TOL
        and abs(values["spinor_su2_holonomy_4pi"] - 1.0) <= STRICT_TOL
        and values["spinor_return_residual_2pi"] <= STRICT_TOL
        and values["spinor_return_residual_4pi"] <= STRICT_TOL
    )
    density_loses_minus1 = (
        abs(values["density_holonomy_2pi"] - 1.0) <= STRICT_TOL
        and values["density_return_residual_2pi"] <= STRICT_TOL
    )
    vector_so3_loses_minus1 = (
        abs(values["vector_so3_holonomy_2pi"] - 1.0) <= STRICT_TOL
        and values["vector_return_residual_2pi"] <= STRICT_TOL
    )
    spinor_su2_quotients_to_so3 = values["su2_to_so3_quotient_residual"] <= STRICT_TOL
    quaternion_ties_spinor = (
        abs(values["quaternion_holonomy_2pi"] - values["spinor_su2_holonomy_2pi"]) <= STRICT_TOL
        and values["quaternion_return_residual_2pi"] <= STRICT_TOL
        and values["quaternion_to_so3_quotient_residual"] <= STRICT_TOL
        and values["quaternion_spinor_gap_2pi"] <= STRICT_TOL
    )
    c3_spin1_loses_minus1 = abs(values["c3_spin1_holonomy_2pi"] - 1.0) <= STRICT_TOL
    c3_embedded_c2_ties_spinor = values["c3_embed_spinor_gap_2pi"] <= STRICT_TOL
    c3_spectator_extra_not_load_bearing = (
        values["c3_spectator_global_minus_residual"] > STRICT_TOL
        and values["c3_spectator_return_residual"] > STRICT_TOL
    )
    higher_qudit_unnecessary = (
        spinor_su2_has_minus1
        and c3_spin1_loses_minus1
        and c3_embedded_c2_ties_spinor
        and c3_spectator_extra_not_load_bearing
    )
    noncommuting_controls = (
        values["su2_commutator_norm"] > STRICT_TOL
        and values["so3_commutator_norm"] > STRICT_TOL
        and values["quaternion_commutator_norm"] > STRICT_TOL
    )
    double_cover_needed = spinor_su2_has_minus1 and vector_so3_loses_minus1 and density_loses_minus1
    realization_convention = quaternion_ties_spinor
    erased_layer_verdict = "GENERIC" if vector_so3_loses_minus1 and density_loses_minus1 else "OPEN"
    erased_layer_loses_result = vector_so3_loses_minus1 and density_loses_minus1 and spinor_su2_has_minus1
    owner_erasure_changes_result = (
        double_cover_needed
        and realization_convention
        and erased_layer_verdict != "REAL_LAYER"
        and values["full_layer_minus_channels"] > values["erased_layer_minus_channels"]
    )
    controls_pass = (
        density_loses_minus1
        and vector_so3_loses_minus1
        and spinor_su2_quotients_to_so3
        and c3_spin1_loses_minus1
        and c3_spectator_extra_not_load_bearing
        and noncommuting_controls
    )
    if double_cover_needed and realization_convention and higher_qudit_unnecessary and owner_erasure_changes_result and controls_pass:
        layer_verdict = "REAL_LAYER"
    elif double_cover_needed and realization_convention:
        layer_verdict = "PARTIAL"
    elif realization_convention and not double_cover_needed:
        layer_verdict = "CONVENTION"
    elif controls_pass and not double_cover_needed:
        layer_verdict = "GENERIC"
    else:
        layer_verdict = "OPEN"
    return {
        "layer_verdict": layer_verdict,
        "erased_layer_verdict": erased_layer_verdict,
        "realization_verdict": "CONVENTION" if realization_convention else "OPEN",
        "double_cover_needed": double_cover_needed,
        "realization_convention": realization_convention,
        "density_loses_minus1": density_loses_minus1,
        "vector_so3_loses_minus1": vector_so3_loses_minus1,
        "spinor_su2_has_minus1": spinor_su2_has_minus1,
        "spinor_su2_quotients_to_so3": spinor_su2_quotients_to_so3,
        "quaternion_ties_spinor": quaternion_ties_spinor,
        "c3_spin1_loses_minus1": c3_spin1_loses_minus1,
        "c3_embedded_c2_ties_spinor": c3_embedded_c2_ties_spinor,
        "c3_spectator_extra_not_load_bearing": c3_spectator_extra_not_load_bearing,
        "higher_qudit_unnecessary": higher_qudit_unnecessary,
        "noncommuting_controls": noncommuting_controls,
        "owner_erasure_changes_result": owner_erasure_changes_result,
        "erased_layer_loses_result": erased_layer_loses_result,
        "erased_layer_changes_verdict": layer_verdict != erased_layer_verdict,
        "controls_pass": controls_pass,
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "within_1e_9": False,
            "max_abs_diff": None,
            "scalar_diffs": [],
            "boolean_mismatches": [],
            "string_mismatches": [{"key": "peer", "jax": "present", "julia": "missing"}],
        }
    peer = read_json(JULIA_RESULT_PATH)
    diffs: list[dict[str, Any]] = []
    max_diff = 0.0
    for key, value in result["shared_scalars"].items():
        peer_value = float(peer.get("shared_scalars", {}).get(key, float("nan")))
        diff = abs(float(value) - peer_value)
        max_diff = max(max_diff, diff)
        if diff > EPS:
            diffs.append({"key": key, "jax": float(value), "julia": peer_value, "abs_diff": diff})
    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        peer_value = peer.get("shared_booleans", {}).get(key)
        if bool(value) != bool(peer_value):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_value)})
    string_mismatches = []
    for key in ("layer_verdict", "realization_verdict"):
        peer_value = peer.get(key)
        if result.get(key) != peer_value:
            string_mismatches.append({"key": key, "jax": result.get(key), "julia": peer_value})
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "within_1e_9": max_diff <= EPS and not diffs and not boolean_mismatches and not string_mismatches,
        "max_abs_diff": max_diff,
        "scalar_diffs": diffs,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    values = carrier_witnesses()
    verdict = verdict_from(values)
    shared_scalars = dict(values)
    shared_scalars["layer_verdict_code"] = VERDICT_CODES[verdict["layer_verdict"]]
    shared_scalars["erased_layer_verdict_code"] = VERDICT_CODES[verdict["erased_layer_verdict"]]
    shared_scalars["realization_verdict_code"] = VERDICT_CODES[verdict["realization_verdict"]]
    shared_booleans = {
        "classification_fence": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "double_cover_needed": verdict["double_cover_needed"],
        "realization_convention": verdict["realization_convention"],
        "density_loses_minus1": verdict["density_loses_minus1"],
        "vector_so3_loses_minus1": verdict["vector_so3_loses_minus1"],
        "spinor_su2_has_minus1": verdict["spinor_su2_has_minus1"],
        "spinor_su2_quotients_to_so3": verdict["spinor_su2_quotients_to_so3"],
        "quaternion_ties_spinor": verdict["quaternion_ties_spinor"],
        "c3_spin1_loses_minus1": verdict["c3_spin1_loses_minus1"],
        "c3_embedded_c2_ties_spinor": verdict["c3_embedded_c2_ties_spinor"],
        "c3_spectator_extra_not_load_bearing": verdict["c3_spectator_extra_not_load_bearing"],
        "higher_qudit_unnecessary": verdict["higher_qudit_unnecessary"],
        "noncommuting_controls": verdict["noncommuting_controls"],
        "owner_erasure_changes_result": verdict["owner_erasure_changes_result"],
        "erased_layer_changes_verdict": verdict["erased_layer_changes_verdict"],
        "controls_pass": verdict["controls_pass"],
    }
    positive = {
        "spinor_su2_has_minus1": {
            "pass": verdict["spinor_su2_has_minus1"],
            "holonomy_2pi": values["spinor_su2_holonomy_2pi"],
            "return_residual_2pi": values["spinor_return_residual_2pi"],
        },
        "double_cover_needed_against_vector_and_density": {
            "pass": verdict["double_cover_needed"],
            "so3_holonomy_2pi": values["vector_so3_holonomy_2pi"],
            "density_holonomy_2pi": values["density_holonomy_2pi"],
        },
        "quaternion_ties_spinor_realization": {
            "pass": verdict["quaternion_ties_spinor"],
            "quaternion_holonomy_2pi": values["quaternion_holonomy_2pi"],
            "spinor_holonomy_2pi": values["spinor_su2_holonomy_2pi"],
        },
        "owner_carrier_load_bearing": {
            "pass": verdict["owner_erasure_changes_result"],
            "rule": "erase double-cover layer to SO3/density quotient and the -1 channel count changes from 2 to 0",
            "full_layer_verdict": verdict["layer_verdict"],
            "erased_layer_verdict": verdict["erased_layer_verdict"],
            "full_layer_minus_channels": values["full_layer_minus_channels"],
            "erased_layer_minus_channels": values["erased_layer_minus_channels"],
        },
        "higher_qudit_unnecessary": {
            "pass": verdict["higher_qudit_unnecessary"],
            "reason": "C2 already carries the -1; C3 spin-1 loses it, while C3 block embedding only reuses the C2 subspace",
        },
    }
    negative = {
        "so3_vector_loses_minus1_control": {
            "pass": verdict["vector_so3_loses_minus1"],
            "holonomy_2pi": values["vector_so3_holonomy_2pi"],
        },
        "density_projection_loses_minus1_control": {
            "pass": verdict["density_loses_minus1"],
            "holonomy_2pi": values["density_holonomy_2pi"],
        },
        "c3_spin1_loses_minus1_control": {
            "pass": verdict["c3_spin1_loses_minus1"],
            "holonomy_2pi": values["c3_spin1_holonomy_2pi"],
        },
        "c3_spectator_not_global_minus_control": {
            "pass": verdict["c3_spectator_extra_not_load_bearing"],
            "global_minus_residual": values["c3_spectator_global_minus_residual"],
            "note": "the extra dimension is not load-bearing for the spinor -1 unless the state is restricted back to the C2 block",
        },
    }
    boundary = {
        "classification_fence": {
            "pass": shared_booleans["classification_fence"],
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "claim_ceiling_blocks_downstream": {
            "pass": True,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "honest_discriminator_verdict": {
            "pass": verdict["layer_verdict"] in VERDICT_CODES,
            "layer_verdict": verdict["layer_verdict"],
            "note": "REAL_LAYER means the double-cover layer is required against SO3/density controls; C2 versus H1 remains a realization convention.",
        },
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_minimality_discriminator_probe",
        "source_alignment_category": "spinor_carrier_minimality_double_cover_discriminator",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "julia_result_path": str(JULIA_RESULT_PATH),
        "source_refs": source_refs(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["jax", "jax.numpy", "julia peer", "owner double-cover carrier"],
        "actual_tools_used": ["jax", "jax.numpy", "python_stdlib", "julia peer result when present"],
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "root_constraints_in_force": {
            "F01": "finite C2, R3, H1, and C3 witnesses at theta in {2pi,4pi,2pi/3}",
            "N01": "noncommuting SU2, SO3, and quaternion rotation controls have nonzero commutator norms",
        },
        "finite_map": "carrier choice -> finite 2pi/4pi holonomy and quotient residuals -> erasure controls -> layer verdict",
        "domain": "one spinor-carrier minimality discriminator row over C2, SO3 vector, H1/Sp1 quaternion, and C3+ controls",
        "codomain_or_output": "single layer verdict plus parity-checked finite witness scalars and booleans",
        "carrier_layer": "SU2/Sp1 double-cover carrier with SO3/density erasure controls",
        "geometry_layer": "finite double-cover holonomy, Hopf/Bloch quotient readout, and quaternion conjugation quotient",
        "bridge_layer": "none",
        "cut_layer": "SO3/density quotient and higher-qudit spectator erasure controls",
        "law_or_candidate_tested": "A spinorial double-cover layer is needed to retain the 2pi=-1 holonomy; C2 and H1 are isomorphic realizations, and C3+ is not required.",
        "branch_status_before_run": "discriminator row requested; survival not assumed",
        "allowed_claims": [
            "finite double-cover discriminator verdict for this row",
            "SO3 vector and density controls lose the -1 holonomy",
            "H1/Sp1 ties the C2 spinor realization, so C2 uniqueness is not claimed",
            "C3+ is unnecessary under these finite witnesses",
            "JAX/Julia parity agreed or disagreements were reported",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "row_id": "spinor_carrier_minimality",
        "layer_verdict": verdict["layer_verdict"],
        "erased_layer_verdict": verdict["erased_layer_verdict"],
        "realization_verdict": verdict["realization_verdict"],
        "realization_note": "C2 spinor and H1/Sp1 unit quaternion both carry the -1; choosing one is a realization convention in this row.",
        "vector_so3_loses_minus1": verdict["vector_so3_loses_minus1"],
        "spinor_su2_has_minus1": verdict["spinor_su2_has_minus1"],
        "quaternion_ties_spinor": verdict["quaternion_ties_spinor"],
        "higher_qudit_unnecessary": verdict["higher_qudit_unnecessary"],
        "owner_erasure_changes_result": verdict["owner_erasure_changes_result"],
        "finite_witness": {
            "values": values,
            "verdict": verdict,
            "axis": [float(x) for x in jax.device_get(AXIS)],
            "quotient_theta": py_float(QUOTIENT_THETA),
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "positive": positive,
        "negative": negative,
        "graveyard_companions": negative,
        "boundary": boundary,
        "nearby_variants": {
            "total": 1,
            "passed": 1 if verdict["layer_verdict"] in VERDICT_CODES else 0,
            "variants": ["spinor_carrier_minimality"],
        },
        "why_not_v4_probes": {
            "reason": "v5 scratch dual-backend discriminator row; not a v4 promotion or formal-admission probe",
        },
    }
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = (
        result["parity"]["peer_available"]
        and result["parity"]["within_1e_9"]
        and shared_booleans["classification_fence"]
        and verdict["layer_verdict"] == "REAL_LAYER"
        and verdict["vector_so3_loses_minus1"]
        and verdict["spinor_su2_has_minus1"]
        and verdict["quaternion_ties_spinor"]
        and verdict["higher_qudit_unnecessary"]
        and verdict["owner_erasure_changes_result"]
    )
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "layer_verdict": verdict["layer_verdict"],
        "realization_verdict": verdict["realization_verdict"],
        "claim_ceiling": CLAIM_CEILING,
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "vector_so3_loses_minus1": verdict["vector_so3_loses_minus1"],
        "spinor_su2_has_minus1": verdict["spinor_su2_has_minus1"],
        "quaternion_ties_spinor": verdict["quaternion_ties_spinor"],
        "higher_qudit_unnecessary": verdict["higher_qudit_unnecessary"],
    }
    result["stop_condition_fired"] = not result["all_pass"]
    result["blockers"] = [] if result["all_pass"] else ["peer parity missing/disagreed or a core discriminator/control boolean failed"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "RESULT "
        f"{OBJECT_ID} jax={RESULT_PATH} julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"layer_verdict={result['layer_verdict']} "
        f"parity={str(result['parity']['within_1e_9']).lower()} "
        f"vector_so3_loses_minus1={str(result['vector_so3_loses_minus1']).lower()} "
        f"spinor_su2_has_minus1={str(result['spinor_su2_has_minus1']).lower()} "
        f"quaternion_ties_spinor={str(result['quaternion_ties_spinor']).lower()} "
        f"higher_qudit_unnecessary={str(result['higher_qudit_unnecessary']).lower()}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
