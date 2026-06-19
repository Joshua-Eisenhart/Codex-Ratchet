#!/usr/bin/env python3
# object_id: hopf_three_ways
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


OBJECT_ID = "hopf_three_ways"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "hopf_three_ways_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "hopf_three_ways_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
SAMPLE_COUNT = 96


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


def unit_quaternion_samples() -> list[jax.Array]:
    samples = [
        jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 1.0, 0.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0, 1.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0, 0.0, 1.0], dtype=jnp.float64),
    ]
    for sample_idx in range(1, SAMPLE_COUNT + 1):
        v = probe_vector(4, sample_idx, 11)
        samples.append(v / jnp.linalg.norm(v))
    return samples


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


def quaternion_hopf(q: jax.Array) -> jax.Array:
    raw = qmul(qmul(q, jnp.asarray([0.0, 1.0, 0.0, 0.0], dtype=jnp.float64)), qconj(q))
    i_coeff = raw[1]
    j_coeff = raw[2]
    k_coeff = raw[3]
    return jnp.asarray([-k_coeff, j_coeff, i_coeff], dtype=jnp.float64)


def spinor_bloch(q: jax.Array) -> jax.Array:
    a, b, c, d = q
    z = a + 1j * b
    w = c + 1j * d
    psi = jnp.asarray([jnp.conj(z), w], dtype=jnp.complex128)
    sigma_x = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    sigma_y = jnp.asarray([[0.0, -1j], [1j, 0.0]], dtype=jnp.complex128)
    sigma_z = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    return jnp.asarray(
        [
            jnp.real(jnp.vdot(psi, sigma_x @ psi)),
            jnp.real(jnp.vdot(psi, sigma_y @ psi)),
            jnp.real(jnp.vdot(psi, sigma_z @ psi)),
        ],
        dtype=jnp.float64,
    )


def complex_hopf(q: jax.Array) -> jax.Array:
    a, b, c, d = q
    z = a + 1j * b
    w = c + 1j * d
    zw = z * w
    return jnp.asarray([2.0 * jnp.real(zw), 2.0 * jnp.imag(zw), jnp.abs(z) ** 2 - jnp.abs(w) ** 2], dtype=jnp.float64)


def cl_even_mul(x: jax.Array, y: jax.Array) -> jax.Array:
    """Multiply in the even Cl(3,0) basis [1, E23, E31, E12]."""
    a, b, c, d = x
    e, f, g, h = y
    return jnp.asarray(
        [
            a * e - b * f - c * g - d * h,
            a * f + b * e - c * h + d * g,
            a * g + b * h + c * e - d * f,
            a * h - b * g + c * f + d * e,
        ],
        dtype=jnp.float64,
    )


def cl_even_reverse(x: jax.Array) -> jax.Array:
    return x * jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def clifford_hopf(q: jax.Array) -> jax.Array:
    a, b, c, d = q
    rotor = jnp.asarray([a, -b, -c, -d], dtype=jnp.float64)
    e23 = jnp.asarray([0.0, 1.0, 0.0, 0.0], dtype=jnp.float64)
    bivector = cl_even_mul(cl_even_mul(rotor, e23), cl_even_reverse(rotor))
    i_coeff = bivector[1]
    j_coeff = bivector[2]
    k_coeff = bivector[3]
    return jnp.asarray([-k_coeff, j_coeff, i_coeff], dtype=jnp.float64)


def right_phase(q: jax.Array, theta: float) -> jax.Array:
    return qmul(q, jnp.asarray([jnp.cos(theta), jnp.sin(theta), 0.0, 0.0], dtype=jnp.float64))


def spinor_pair(q: jax.Array) -> jax.Array:
    a, b, c, d = q
    z = a + 1j * b
    w = c + 1j * d
    return jnp.asarray([jnp.conj(z), w], dtype=jnp.complex128)


def linf(x: jax.Array, y: jax.Array) -> float:
    return py_float(jnp.max(jnp.abs(x - y)))


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
    samples = unit_quaternion_samples()
    max_input_unit_norm_error = 0.0
    quaternion_s2_norm_max_error = 0.0
    spinor_s2_norm_max_error = 0.0
    complex_s2_norm_max_error = 0.0
    clifford_s2_norm_max_error = 0.0
    quat_spinor_max_linf = 0.0
    quat_complex_max_linf = 0.0
    spinor_complex_max_linf = 0.0
    clifford_quat_max_linf = 0.0
    fiber_invariance_max_linf = 0.0
    right_phase_global_phase_max_linf = 0.0
    thetas = [float(x) for x in jnp.linspace(0.0, 2.0 * jnp.pi, 13, endpoint=False)]
    for q in samples:
        hq = quaternion_hopf(q)
        hs = spinor_bloch(q)
        hc = complex_hopf(q)
        hcl = clifford_hopf(q)
        max_input_unit_norm_error = max(max_input_unit_norm_error, abs(py_float(jnp.linalg.norm(q)) - 1.0))
        quaternion_s2_norm_max_error = max(quaternion_s2_norm_max_error, abs(py_float(jnp.linalg.norm(hq)) - 1.0))
        spinor_s2_norm_max_error = max(spinor_s2_norm_max_error, abs(py_float(jnp.linalg.norm(hs)) - 1.0))
        complex_s2_norm_max_error = max(complex_s2_norm_max_error, abs(py_float(jnp.linalg.norm(hc)) - 1.0))
        clifford_s2_norm_max_error = max(clifford_s2_norm_max_error, abs(py_float(jnp.linalg.norm(hcl)) - 1.0))
        quat_spinor_max_linf = max(quat_spinor_max_linf, linf(hq, hs))
        quat_complex_max_linf = max(quat_complex_max_linf, linf(hq, hc))
        spinor_complex_max_linf = max(spinor_complex_max_linf, linf(hs, hc))
        clifford_quat_max_linf = max(clifford_quat_max_linf, linf(hcl, hq))
        psi = spinor_pair(q)
        for theta in thetas:
            qp = right_phase(q, theta)
            fiber_invariance_max_linf = max(fiber_invariance_max_linf, linf(quaternion_hopf(qp), hq))
            psi_phase = spinor_pair(qp)
            right_phase_global_phase_max_linf = max(
                right_phase_global_phase_max_linf,
                py_float(jnp.max(jnp.abs(psi_phase - jnp.exp(-1j * theta) * psi))),
            )

    nonunit_q = 1.7 * samples[-1]
    nonunit_output_norm = py_float(jnp.linalg.norm(quaternion_hopf(nonunit_q)))
    nonunit_s2_norm_error = abs(nonunit_output_norm - 1.0)
    max_pairwise_disagreement = max(quat_spinor_max_linf, quat_complex_max_linf, spinor_complex_max_linf)
    verdicts = {
        "hopf_three_ways_agree": max_pairwise_disagreement < TOL,
        "fiber_invariant": fiber_invariance_max_linf < TOL,
        "clifford_rotor_agrees": clifford_quat_max_linf < TOL,
        "nonunit_control_pass": nonunit_s2_norm_error > 0.5,
    }
    controls = {
        "unit_inputs_control_ok": max_input_unit_norm_error < TOL,
        "nonunit_quaternion_off_s2_control_ok": verdicts["nonunit_control_pass"],
        "control_miswired": not (max_input_unit_norm_error < TOL and verdicts["nonunit_control_pass"]),
    }
    shared_scalars = {
        "max_input_unit_norm_error": max_input_unit_norm_error,
        "quaternion_s2_norm_max_error": quaternion_s2_norm_max_error,
        "spinor_s2_norm_max_error": spinor_s2_norm_max_error,
        "complex_s2_norm_max_error": complex_s2_norm_max_error,
        "clifford_s2_norm_max_error": clifford_s2_norm_max_error,
        "quat_spinor_max_linf": quat_spinor_max_linf,
        "quat_complex_max_linf": quat_complex_max_linf,
        "spinor_complex_max_linf": spinor_complex_max_linf,
        "clifford_quat_max_linf": clifford_quat_max_linf,
        "max_pairwise_disagreement": max_pairwise_disagreement,
        "fiber_invariance_max_linf": fiber_invariance_max_linf,
        "right_phase_global_phase_max_linf": right_phase_global_phase_max_linf,
        "nonunit_output_norm": nonunit_output_norm,
        "nonunit_s2_norm_error": nonunit_s2_norm_error,
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
        "claim_ceiling": "Finite S3->S2 Hopf convention check only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind": "classical",
        "sim_class": "hopf_geometry_convention_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "sample_count": len(samples),
        "convention": {
            "quaternion": "q=a+b*i+c*j+d*k; compute q*i*qbar = I*i + J*j + K*k, then compare S2 coordinates as (-K,J,I)",
            "spinor": "z=a+b*i, w=c+d*i, psi_R=(conj(z),w)",
            "complex_hopf": "(2*Re(z*w), 2*Im(z*w), |z|^2-|w|^2)",
            "right_fiber_action": "q -> q*exp(i*theta), equivalent to z->z*exp(i*theta), w->w*exp(-i*theta), psi_R->exp(-i*theta)*psi_R",
        },
        "tool_manifest": {
            "JAX": "load-bearing quaternion, spinor, and complex Hopf computations",
            "jax.numpy": "load-bearing x64 norms, disagreements, and fiber residuals",
            "json": "supportive result serialization",
            "CliffordAlgebras": "not available in JAX; same Cl(3)-equivalent q*i*qbar sandwich computed explicitly",
        },
        "tool_integration_depth": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive", "CliffordAlgebras": "None"},
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": "The three Hopf maps agree after fixing one S2 coordinate convention: unit quaternions, the paired spinor, and the complex formula are the same finite S3->S2 object with an S1 fiber.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not verdicts["hopf_three_ways_agree"]
        or not verdicts["fiber_invariant"]
        or not verdicts["clifford_rotor_agrees"]
        or bool(result["parity"]["stop_condition_fired"])
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    n = result["numbers"]
    print("hopf_three_ways - JAX full sim")
    print(f"hopf_three_ways_agree={str(result['verdicts']['hopf_three_ways_agree']).lower()} max_pairwise_disagreement={n['max_pairwise_disagreement']}")
    print(f"fiber_invariant={str(result['verdicts']['fiber_invariant']).lower()} fiber_invariance_max_linf={n['fiber_invariance_max_linf']}")
    print(f"clifford_rotor_agrees={str(result['verdicts']['clifford_rotor_agrees']).lower()} clifford_quat_max_linf={n['clifford_quat_max_linf']}")
    print(
        f"nonunit_control_pass={str(result['verdicts']['nonunit_control_pass']).lower()} "
        f"nonunit_output_norm={n['nonunit_output_norm']} nonunit_s2_norm_error={n['nonunit_s2_norm_error']}"
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
