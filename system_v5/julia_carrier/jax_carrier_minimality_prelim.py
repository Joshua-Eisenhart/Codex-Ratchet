#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "carrier_minimality_prelim"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "carrier_minimality_prelim_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "carrier_minimality_prelim_julia_results.json"
GUIDE_PATH = (
    "/Users/joshuaeisenhart/wiki/projects/codex-ratchet/"
    "qit-igt-engine-valid-results-and-running-guide-2026-06-05.md"
)
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.array([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)


def f64(x: Any) -> jax.Array:
    return jnp.asarray(x, dtype=jnp.float64)


AXIS = f64([1.0, 1.0, 1.0])
AXIS = AXIS / jnp.linalg.norm(AXIS)
QUOTIENT_THETA = 2.0 * jnp.pi / 3.0


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def py_list(x: Any) -> list[float]:
    return [float(v) for v in jax.device_get(x)]


def su2(axis: jax.Array, theta: jax.Array) -> jax.Array:
    generator = axis[0] * SX + axis[1] * SY + axis[2] * SZ
    return jnp.cos(theta / 2.0) * I2 - 1j * jnp.sin(theta / 2.0) * generator


def rodrigues(axis: jax.Array, theta: jax.Array) -> jax.Array:
    x, y, z = axis
    k = jnp.array(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=jnp.float64,
    )
    return jnp.eye(3, dtype=jnp.float64) + jnp.sin(theta) * k + (1.0 - jnp.cos(theta)) * (k @ k)


def so3_expm_series(axis: jax.Array, theta: jax.Array, terms: int = 32) -> jax.Array:
    x, y, z = axis
    a = theta * jnp.array(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=jnp.float64,
    )
    out = jnp.eye(3, dtype=jnp.float64)
    term = jnp.eye(3, dtype=jnp.float64)
    for n in range(1, terms + 1):
        term = (term @ a) / float(n)
        out = out + term
    return out


def dm(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def bloch_vec(rho: jax.Array) -> jax.Array:
    return jnp.array(
        [
            jnp.real(jnp.trace(rho @ SX)),
            jnp.real(jnp.trace(rho @ SY)),
            jnp.real(jnp.trace(rho @ SZ)),
        ],
        dtype=jnp.float64,
    )


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return jnp.array(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=jnp.float64,
    )


def qconj(q: jax.Array) -> jax.Array:
    return jnp.array([q[0], -q[1], -q[2], -q[3]], dtype=jnp.float64)


def qrot(q: jax.Array, v: jax.Array) -> jax.Array:
    out = qmul(qmul(q, jnp.array([0.0, v[0], v[1], v[2]], dtype=jnp.float64)), qconj(q))
    return out[1:4]


def qaxis(axis: jax.Array, theta: jax.Array) -> jax.Array:
    return jnp.array(
        [
            jnp.cos(theta / 2.0),
            axis[0] * jnp.sin(theta / 2.0),
            axis[1] * jnp.sin(theta / 2.0),
            axis[2] * jnp.sin(theta / 2.0),
        ],
        dtype=jnp.float64,
    )


def qmatrix(q: jax.Array) -> jax.Array:
    basis = jnp.eye(3, dtype=jnp.float64)
    cols = [qrot(q, basis[i]) for i in range(3)]
    return jnp.stack(cols, axis=1)


def maxabs(x: jax.Array) -> float:
    return py_float(jnp.max(jnp.abs(x)))


def approx_equal(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol


def return_factor_complex(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.vdot(start, stop) / jnp.vdot(start, start)


def matrix_overlap_factor(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(jnp.conj(start.T) @ stop)) / jnp.real(jnp.trace(jnp.conj(start.T) @ start))


def vector_overlap_factor(start: jax.Array, stop: jax.Array) -> jax.Array:
    return jnp.dot(start, stop) / jnp.dot(start, start)


def spinor_carrier() -> dict[str, Any]:
    psi0 = jnp.array([1.0 + 0.0j, 0.37 + 0.21j], dtype=jnp.complex128)
    psi0 = psi0 / jnp.sqrt(jnp.real(jnp.vdot(psi0, psi0)))
    psi2 = su2(AXIS, 2.0 * jnp.pi) @ psi0
    psi4 = su2(AXIS, 4.0 * jnp.pi) @ psi0
    f2 = return_factor_complex(psi0, psi2)
    f4 = return_factor_complex(psi0, psi4)

    uq = su2(AXIS, QUOTIENT_THETA)
    rq = bloch_vec(dm(uq @ psi0))
    rtarget = rodrigues(AXIS, QUOTIENT_THETA) @ bloch_vec(dm(psi0))

    ux = su2(f64([1.0, 0.0, 0.0]), jnp.pi / 3.0)
    uy = su2(f64([0.0, 1.0, 0.0]), jnp.pi / 4.0)

    return {
        "status": "computed",
        "holonomy_2pi": py_float(jnp.real(f2)),
        "holonomy_2pi_imag": py_float(jnp.imag(f2)),
        "holonomy_4pi": py_float(jnp.real(f4)),
        "holonomy_4pi_imag": py_float(jnp.imag(f4)),
        "return_residual_2pi": py_float(jnp.linalg.norm(psi2 - f2 * psi0)),
        "return_residual_4pi": py_float(jnp.linalg.norm(psi4 - f4 * psi0)),
        "quotient_residual": maxabs(rq - rtarget),
        "quotient_target": "Bloch r=Tr(rho sigma), compared with SO(3) Rodrigues rotation",
        "n01_commutator_norm": py_float(jnp.linalg.norm(ux @ uy - uy @ ux)),
        "presumption_ledger": {
            "field": "C",
            "form_metric_type": "Hermitian",
            "carrier_real_dim": 4,
            "unit_state_real_dim": 3,
            "quotient_real_dim": 2,
            "group": "SU(2)",
            "simply_connected": True,
        },
    }


def density_carrier() -> dict[str, Any]:
    psi0 = jnp.array([1.0 + 0.0j, 0.37 + 0.21j], dtype=jnp.complex128)
    psi0 = psi0 / jnp.sqrt(jnp.real(jnp.vdot(psi0, psi0)))
    rho0 = dm(psi0)
    u2 = su2(AXIS, 2.0 * jnp.pi)
    u4 = su2(AXIS, 4.0 * jnp.pi)
    rho2 = u2 @ rho0 @ jnp.conj(u2.T)
    rho4 = u4 @ rho0 @ jnp.conj(u4.T)

    uq = su2(AXIS, QUOTIENT_THETA)
    rq = bloch_vec(uq @ rho0 @ jnp.conj(uq.T))
    rtarget = rodrigues(AXIS, QUOTIENT_THETA) @ bloch_vec(rho0)

    rx = rodrigues(f64([1.0, 0.0, 0.0]), jnp.pi / 3.0)
    ry = rodrigues(f64([0.0, 1.0, 0.0]), jnp.pi / 4.0)

    return {
        "status": "computed",
        "holonomy_2pi": py_float(matrix_overlap_factor(rho0, rho2)),
        "holonomy_4pi": py_float(matrix_overlap_factor(rho0, rho4)),
        "return_residual_2pi": py_float(jnp.linalg.norm(rho2 - rho0)),
        "return_residual_4pi": py_float(jnp.linalg.norm(rho4 - rho0)),
        "quotient_residual": maxabs(rq - rtarget),
        "quotient_target": "Bloch r=Tr(rho sigma), compared with SO(3) Rodrigues rotation",
        "n01_commutator_norm": py_float(jnp.linalg.norm(rx @ ry - ry @ rx)),
        "presumption_ledger": {
            "field": "C",
            "form_metric_type": "Hermitian trace-one positive density form",
            "carrier_real_dim": 3,
            "tested_pure_orbit_real_dim": 2,
            "group": "SO(3) adjoint readout of SU(2) action",
            "simply_connected": False,
        },
    }


def real_vector_carrier() -> dict[str, Any]:
    v0 = f64([0.23, -0.71, 0.48])
    v0 = v0 / jnp.linalg.norm(v0)
    r2 = rodrigues(AXIS, 2.0 * jnp.pi)
    r4 = rodrigues(AXIS, 4.0 * jnp.pi)
    rq = so3_expm_series(AXIS, QUOTIENT_THETA)

    rx = rodrigues(f64([1.0, 0.0, 0.0]), jnp.pi / 3.0)
    ry = rodrigues(f64([0.0, 1.0, 0.0]), jnp.pi / 4.0)

    return {
        "status": "computed",
        "holonomy_2pi": py_float(vector_overlap_factor(v0, r2 @ v0)),
        "holonomy_4pi": py_float(vector_overlap_factor(v0, r4 @ v0)),
        "return_residual_2pi": py_float(jnp.linalg.norm(r2 @ v0 - v0)),
        "return_residual_4pi": py_float(jnp.linalg.norm(r4 @ v0 - v0)),
        "quotient_residual": maxabs(rq - rodrigues(AXIS, QUOTIENT_THETA)),
        "quotient_target": "SO(3) matrix exponential series compared with closed-form Rodrigues rotation",
        "n01_commutator_norm": py_float(jnp.linalg.norm(rx @ ry - ry @ rx)),
        "presumption_ledger": {
            "field": "R",
            "form_metric_type": "Euclidean symmetric",
            "carrier_real_dim": 3,
            "group": "SO(3)",
            "simply_connected": False,
        },
    }


def quaternion_carrier() -> dict[str, Any]:
    q0 = f64([1.0, 0.0, 0.0, 0.0])
    q2 = qaxis(AXIS, 2.0 * jnp.pi)
    q4 = qaxis(AXIS, 4.0 * jnp.pi)
    qtarget = qaxis(AXIS, QUOTIENT_THETA)
    rq = qmatrix(qtarget)
    rtarget = rodrigues(AXIS, QUOTIENT_THETA)

    qx = qaxis(f64([1.0, 0.0, 0.0]), jnp.pi / 3.0)
    qy = qaxis(f64([0.0, 1.0, 0.0]), jnp.pi / 4.0)

    return {
        "status": "computed",
        "holonomy_2pi": py_float(vector_overlap_factor(q0, q2)),
        "holonomy_4pi": py_float(vector_overlap_factor(q0, q4)),
        "return_residual_2pi": py_float(jnp.linalg.norm(q2 - (-1.0 * q0))),
        "return_residual_4pi": py_float(jnp.linalg.norm(q4 - q0)),
        "quotient_residual": maxabs(rq - rtarget),
        "quotient_target": "quaternion conjugation q v q*, compared with SO(3) Rodrigues rotation",
        "n01_commutator_norm": py_float(jnp.linalg.norm(qmul(qx, qy) - qmul(qy, qx))),
        "presumption_ledger": {
            "field": "H",
            "form_metric_type": "quaternionic norm",
            "carrier_real_dim": 4,
            "unit_state_real_dim": 3,
            "quotient_real_dim": 3,
            "group": "Sp(1)",
            "simply_connected": True,
        },
    }


def finite_subgroup_2t_carrier() -> dict[str, Any]:
    q0 = f64([1.0, 0.0, 0.0, 0.0])
    a = f64([0.5, 0.5, 0.5, 0.5])
    a2 = qmul(a, a)
    a3 = qmul(a2, a)
    a6 = qmul(a3, a3)
    rq = qmatrix(a)
    rtarget = rodrigues(AXIS, QUOTIENT_THETA)
    qi = f64([0.0, 1.0, 0.0, 0.0])
    qj = f64([0.0, 0.0, 1.0, 0.0])

    return {
        "status": "computed_optional",
        "holonomy_2pi": py_float(vector_overlap_factor(q0, a3)),
        "holonomy_4pi": py_float(vector_overlap_factor(q0, a6)),
        "return_residual_2pi": py_float(jnp.linalg.norm(a3 - (-1.0 * q0))),
        "return_residual_4pi": py_float(jnp.linalg.norm(a6 - q0)),
        "quotient_residual": maxabs(rq - rtarget),
        "quotient_target": "2T generator projected by quaternion conjugation to tetrahedral SO(3) rotation",
        "n01_commutator_norm": py_float(jnp.linalg.norm(qmul(qi, qj) - qmul(qj, qi))),
        "presumption_ledger": {
            "field": "H finite subset",
            "form_metric_type": "restricted quaternionic norm",
            "carrier_real_dim": 0,
            "carrier_cardinality": 24,
            "group": "2T binary tetrahedral subgroup of SU(2)",
            "simply_connected": False,
            "note": "discrete finite group; not path-connected",
        },
    }


def compute_verdicts(carriers: dict[str, Any]) -> dict[str, Any]:
    spinor = carriers["spinor_C2"]
    density = carriers["density_C2"]
    realv = carriers["real_vector_SO3"]
    quat = carriers["quaternion_Sp1"]

    rho_invisible = approx_equal(density["holonomy_2pi"], 1.0) and approx_equal(
        spinor["holonomy_2pi"], -1.0
    )
    quaternion_ties = approx_equal(quat["holonomy_2pi"], spinor["holonomy_2pi"]) and (
        quat["quotient_residual"] < TOL
    )
    real_vector_loses = approx_equal(realv["holonomy_2pi"], 1.0)
    spinor_uniquely_minimal = rho_invisible and real_vector_loses and not quaternion_ties

    return {
        "rho_invisible": {
            "value": rho_invisible,
            "numbers": {
                "density_C2.holonomy_2pi": density["holonomy_2pi"],
                "spinor_C2.holonomy_2pi": spinor["holonomy_2pi"],
            },
        },
        "quaternion_ties": {
            "value": quaternion_ties,
            "numbers": {
                "quaternion_Sp1.holonomy_2pi": quat["holonomy_2pi"],
                "spinor_C2.holonomy_2pi": spinor["holonomy_2pi"],
                "quaternion_Sp1.quotient_residual": quat["quotient_residual"],
                "tol": TOL,
            },
        },
        "real_vector_loses": {
            "value": real_vector_loses,
            "numbers": {"real_vector_SO3.holonomy_2pi": realv["holonomy_2pi"]},
        },
        "spinor_uniquely_minimal": {
            "value": spinor_uniquely_minimal,
            "numbers": {"quaternion_ties": quaternion_ties},
        },
    }


def shared_scalar_diffs(jax_result: dict[str, Any], julia_reference: dict[str, Any]) -> dict[str, Any]:
    keys = jax_result["shared_scalar_keys"]
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    divergences_1e6: list[dict[str, Any]] = []
    for carrier_name, carrier in jax_result["carriers"].items():
        julia_carrier = julia_reference["carriers"][carrier_name]
        for key in keys:
            jv = float(carrier[key])
            rv = float(julia_carrier[key])
            diff = abs(jv - rv)
            max_diff = max(max_diff, diff)
            row = {
                "carrier": carrier_name,
                "key": key,
                "jax": jv,
                "julia": rv,
                "abs_diff": diff,
            }
            rows.append(row)
            if diff > STRICT_STOP_TOL:
                divergences_1e6.append(row)
    return {
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL,
        "strict_divergence_gt_1e_6": divergences_1e6,
        "stop_condition_fired": bool(divergences_1e6),
    }


def build_result() -> dict[str, Any]:
    carriers = {
        "spinor_C2": spinor_carrier(),
        "density_C2": density_carrier(),
        "real_vector_SO3": real_vector_carrier(),
        "quaternion_Sp1": quaternion_carrier(),
        "finite_subgroup_2T": finite_subgroup_2t_carrier(),
    }
    verdicts = compute_verdicts(carriers)
    density_bad = approx_equal(carriers["density_C2"]["holonomy_2pi"], -1.0)
    real_bad = approx_equal(carriers["real_vector_SO3"]["holonomy_2pi"], -1.0)
    negative_stop = density_bad or real_bad
    sentence = (
        "At scratch_diagnostic ceiling, the spinor preference TIES the quaternion carrier; "
        "the unique-spinor claim is falsified down to psi-level surplus."
        if verdicts["quaternion_ties"]["value"]
        else "At scratch_diagnostic ceiling, the spinor preference SURVIVES this quaternion comparison."
    )
    shared_scalar_keys = [
        "holonomy_2pi",
        "holonomy_4pi",
        "return_residual_2pi",
        "return_residual_4pi",
        "quotient_residual",
        "n01_commutator_norm",
    ]
    shared_scalars: dict[str, float] = {}
    shared_booleans: dict[str, bool] = {}
    for carrier_name, carrier in carriers.items():
        for scalar_key in shared_scalar_keys:
            shared_scalars[f"{carrier_name}.{scalar_key}"] = float(carrier[scalar_key])
    for key, value in verdicts.items():
        shared_booleans[f"verdict.{key}"] = bool(value["value"])
    shared_booleans["control.density_C2_shows_minus_sign"] = bool(density_bad)
    shared_booleans["control.real_vector_SO3_shows_minus_sign"] = bool(real_bad)
    shared_booleans["control.negative_control_miswired"] = bool(negative_stop)

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_mirror",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "guide_reference": {
            "path": GUIDE_PATH,
            "line_start": 879,
            "line_end": 929,
            "box": "spinor-vector visibility fence and falsifier",
        },
        "question": "Under F01 finite + N01 noncommutation, does C2 spinor uniquely beat density/Bloch, real-vector SO(3), and quaternion Sp(1) carriers?",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "PRELIM finite-map falsifier only; no basin/admission/proof/engine-forcing claim",
        "root_constraints": {
            "F01": "finite carrier representation and finite sampled map theta in {0,2pi,4pi} plus quotient test theta",
            "N01": "noncommuting action witness recorded as n01_commutator_norm for each carrier",
        },
        "axis": py_list(AXIS),
        "quotient_theta": py_float(QUOTIENT_THETA),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "shared_scalar_keys": shared_scalar_keys,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "carriers": carriers,
        "verdicts": verdicts,
        "negative_control_status": {
            "density_C2_shows_minus_sign": density_bad,
            "real_vector_SO3_shows_minus_sign": real_bad,
            "negative_control_miswired": negative_stop,
        },
        "plain_sentence": sentence,
    }

    if JULIA_REFERENCE_PATH.exists():
        with JULIA_REFERENCE_PATH.open("r", encoding="utf-8") as f:
            julia_reference = json.load(f)
        parity = shared_scalar_diffs(result, julia_reference)
    else:
        parity = {
            "shared_scalar_rows": [],
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [
                {
                    "missing": str(JULIA_REFERENCE_PATH),
                    "reason": "Julia reference JSON must exist before JAX parity can run.",
                }
            ],
            "stop_condition_fired": True,
        }

    result["parity"] = parity
    result["stop_condition_fired"] = negative_stop or bool(parity["stop_condition_fired"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    print("Carrier minimality prelim — JAX mirror")
    print(
        f"classification: {result['classification']} | "
        f"promotion_allowed: {str(result['promotion_allowed']).lower()} | "
        f"jax_enable_x64: {str(result['jax_enable_x64']).lower()}"
    )
    for name in [
        "spinor_C2",
        "density_C2",
        "real_vector_SO3",
        "quaternion_Sp1",
        "finite_subgroup_2T",
    ]:
        c = result["carriers"][name]
        ledger = c["presumption_ledger"]
        print(
            f"{name}: holonomy_2pi={c['holonomy_2pi']} "
            f"holonomy_4pi={c['holonomy_4pi']} "
            f"quotient_residual={c['quotient_residual']} "
            f"ledger(field={ledger['field']}, form={ledger['form_metric_type']}, "
            f"real_dim={ledger['carrier_real_dim']}, group={ledger['group']}, "
            f"simply_connected={ledger['simply_connected']})"
        )
    for key in ["rho_invisible", "quaternion_ties", "real_vector_loses", "spinor_uniquely_minimal"]:
        verdict = result["verdicts"][key]
        print(f"{key}={str(verdict['value']).lower()} numbers={json.dumps(verdict['numbers'], sort_keys=True)}")
    parity = result["parity"]
    print(f"parity_max_diff={parity['parity_max_diff']} within_1e-9={str(parity['within_1e_9']).lower()}")
    if parity["strict_divergence_gt_1e_6"]:
        print("STOP: JAX and Julia disagree beyond 1e-6 on shared scalar(s):")
        print(json.dumps(parity["strict_divergence_gt_1e_6"], indent=2, sort_keys=True))
    if result["negative_control_status"]["negative_control_miswired"]:
        print("STOP: negative control showed the lifted -1 sign; test is miswired.")
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")
    if not result["stop_condition_fired"]:
        print("CODEX2_CARRIER_MINIMALITY_DONE")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
