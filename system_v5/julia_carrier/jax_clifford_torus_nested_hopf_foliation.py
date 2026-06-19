#!/usr/bin/env python3
# object_id: clifford_torus_nested_hopf_foliation
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


OBJECT_ID = "clifford_torus_nested_hopf_foliation"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "clifford_torus_nested_hopf_foliation_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
COVERAGE_TOL = 1.0e-6
PHASE_COUNT = 24
VOLUME_STEPS = 16_384
S3_SAMPLE_COUNT = 512
ETA_BINS = 16


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def torus_point(eta: float, phi: float, chi: float) -> tuple[jax.Array, jax.Array]:
    z = jnp.cos(eta) * jnp.exp(1j * phi)
    w = jnp.sin(eta) * jnp.exp(1j * chi)
    return z, w


def s3_constraint_residual(z: jax.Array, w: jax.Array) -> float:
    return py_float(jnp.abs(jnp.abs(z) ** 2 + jnp.abs(w) ** 2 - 1.0))


def phase_grid() -> list[float]:
    return [py_float(2.0 * jnp.pi * i / PHASE_COUNT) for i in range(PHASE_COUNT)]


def interior_torus_checks() -> dict[str, Any]:
    etas = [py_float(jnp.pi / 10.0), py_float(jnp.pi / 6.0), py_float(jnp.pi / 4.0), py_float(jnp.pi / 3.0), py_float(2.0 * jnp.pi / 5.0)]
    phases = phase_grid()
    interior_s3_constraint_max_residual = 0.0
    eta_radius_max_residual = 0.0
    periodic_closure_max_residual = 0.0
    hopf_latitude_residual = 0.0
    torus_metric_det_min = float("inf")
    for eta in etas:
        torus_metric_det_min = min(torus_metric_det_min, py_float(jnp.cos(eta) ** 2 * jnp.sin(eta) ** 2))
        for phi in phases:
            for chi in phases:
                z, w = torus_point(eta, phi, chi)
                interior_s3_constraint_max_residual = max(interior_s3_constraint_max_residual, s3_constraint_residual(z, w))
                eta_radius_max_residual = max(
                    eta_radius_max_residual,
                    py_float(jnp.abs(jnp.abs(z) - jnp.cos(eta))),
                    py_float(jnp.abs(jnp.abs(w) - jnp.sin(eta))),
                )
                z_phi, w_phi = torus_point(eta, phi + py_float(2.0 * jnp.pi), chi)
                z_chi, w_chi = torus_point(eta, phi, chi + py_float(2.0 * jnp.pi))
                periodic_closure_max_residual = max(
                    periodic_closure_max_residual,
                    py_float(jnp.abs(z_phi - z)),
                    py_float(jnp.abs(w_phi - w)),
                    py_float(jnp.abs(z_chi - z)),
                    py_float(jnp.abs(w_chi - w)),
                )
                hopf_latitude_residual = max(
                    hopf_latitude_residual,
                    py_float(jnp.abs((jnp.abs(z) ** 2 - jnp.abs(w) ** 2) - jnp.cos(2.0 * eta))),
                )
    return {
        "eta_values": etas,
        "phase_count_per_circle": PHASE_COUNT,
        "interior_s3_constraint_max_residual": interior_s3_constraint_max_residual,
        "eta_radius_max_residual": eta_radius_max_residual,
        "periodic_closure_max_residual": periodic_closure_max_residual,
        "torus_metric_det_min": torus_metric_det_min,
        "hopf_latitude_residual": hopf_latitude_residual,
    }


def volume_check() -> dict[str, Any]:
    deta = (jnp.pi / 2.0) / VOLUME_STEPS
    i = jnp.arange(VOLUME_STEPS, dtype=jnp.float64)
    eta = (i + 0.5) * deta
    volume_estimate = jnp.sum(4.0 * jnp.pi ** 2 * jnp.cos(eta) * jnp.sin(eta) * deta)
    s3_volume_reference = 2.0 * jnp.pi ** 2
    return {
        "volume_steps": VOLUME_STEPS,
        "volume_estimate": py_float(volume_estimate),
        "s3_volume_reference": py_float(s3_volume_reference),
        "foliation_volume_residual": py_float(jnp.abs(volume_estimate - s3_volume_reference)),
    }


def deterministic_s3_sample(k: int) -> tuple[jax.Array, jax.Array, float]:
    u = (k - 0.5) / S3_SAMPLE_COUNT
    eta = py_float(jnp.arcsin(jnp.sqrt(u)))
    phi = py_float(2.0 * jnp.pi * ((k * 37) % S3_SAMPLE_COUNT) / S3_SAMPLE_COUNT)
    chi = py_float(2.0 * jnp.pi * ((k * 53) % S3_SAMPLE_COUNT) / S3_SAMPLE_COUNT)
    z, w = torus_point(eta, phi, chi)
    return z, w, eta


def sample_reconstruction_check() -> dict[str, Any]:
    sample_reconstruction_max_residual = 0.0
    min_eta = float("inf")
    max_eta = -float("inf")
    bins = [0 for _ in range(ETA_BINS)]
    for k in range(1, S3_SAMPLE_COUNT + 1):
        z, w, _ = deterministic_s3_sample(k)
        eta = py_float(jnp.arctan2(jnp.abs(w), jnp.abs(z)))
        phi = py_float(jnp.angle(z))
        chi = py_float(jnp.angle(w))
        zr, wr = torus_point(eta, phi, chi)
        residual = py_float(jnp.linalg.norm(jnp.asarray([jnp.real(z - zr), jnp.imag(z - zr), jnp.real(w - wr), jnp.imag(w - wr)], dtype=jnp.float64)))
        sample_reconstruction_max_residual = max(sample_reconstruction_max_residual, residual)
        min_eta = min(min_eta, eta)
        max_eta = max(max_eta, eta)
        bin_index = int(jnp.floor(eta / (jnp.pi / 2.0) * ETA_BINS))
        bin_index = max(0, min(ETA_BINS - 1, bin_index))
        bins[bin_index] += 1
    return {
        "sample_count": S3_SAMPLE_COUNT,
        "sample_reconstruction_max_residual": sample_reconstruction_max_residual,
        "eta_min": min_eta,
        "eta_max": max_eta,
        "eta_endpoint_gap": max(min_eta, py_float(jnp.pi / 2.0) - max_eta),
        "eta_bins": bins,
        "eta_bin_min_count": min(bins),
    }


def core_circle_checks() -> dict[str, Any]:
    phases = phase_grid()
    core_circle_s3_residual = 0.0
    core_zero_radius_residual = 0.0
    for phi in phases:
        z0, w0 = torus_point(0.0, phi, 0.0)
        z1, w1 = torus_point(py_float(jnp.pi / 2.0), 0.0, phi)
        core_circle_s3_residual = max(core_circle_s3_residual, s3_constraint_residual(z0, w0), s3_constraint_residual(z1, w1))
        core_zero_radius_residual = max(core_zero_radius_residual, py_float(jnp.abs(w0)), py_float(jnp.abs(z1)))
    return {
        "core_circle_s3_residual": core_circle_s3_residual,
        "core_zero_radius_residual": core_zero_radius_residual,
    }


def clifford_torus_check() -> dict[str, Any]:
    phases = phase_grid()
    eta = py_float(jnp.pi / 4.0)
    target = py_float(1.0 / jnp.sqrt(2.0))
    clifford_equal_radius_residual = 0.0
    clifford_target_radius_residual = 0.0
    clifford_hopf_equator_residual = 0.0
    for phi in phases:
        for chi in phases:
            z, w = torus_point(eta, phi, chi)
            clifford_equal_radius_residual = max(clifford_equal_radius_residual, py_float(jnp.abs(jnp.abs(z) - jnp.abs(w))))
            clifford_target_radius_residual = max(
                clifford_target_radius_residual,
                py_float(jnp.abs(jnp.abs(z) - target)),
                py_float(jnp.abs(jnp.abs(w) - target)),
            )
            clifford_hopf_equator_residual = max(clifford_hopf_equator_residual, py_float(jnp.abs(jnp.abs(z) ** 2 - jnp.abs(w) ** 2)))
    return {
        "eta": eta,
        "clifford_equal_radius_residual": clifford_equal_radius_residual,
        "clifford_target_radius_residual": clifford_target_radius_residual,
        "clifford_hopf_equator_residual": clifford_hopf_equator_residual,
    }


def flat_t2_control() -> dict[str, Any]:
    phases = phase_grid()
    flat_t2_s3_constraint_min_residual = float("inf")
    flat_t2_s3_constraint_max_residual = 0.0
    for phi in phases:
        for chi in phases:
            z = jnp.exp(1j * phi)
            w = jnp.exp(1j * chi)
            residual = py_float(jnp.abs(jnp.abs(z) ** 2 + jnp.abs(w) ** 2 - 1.0))
            flat_t2_s3_constraint_min_residual = min(flat_t2_s3_constraint_min_residual, residual)
            flat_t2_s3_constraint_max_residual = max(flat_t2_s3_constraint_max_residual, residual)
    return {
        "flat_t2_s3_constraint_min_residual": flat_t2_s3_constraint_min_residual,
        "flat_t2_s3_constraint_max_residual": flat_t2_s3_constraint_max_residual,
        "flat_t2_rejected": flat_t2_s3_constraint_min_residual > 0.5,
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
    interior = interior_torus_checks()
    volume = volume_check()
    samples = sample_reconstruction_check()
    core = core_circle_checks()
    clifford = clifford_torus_check()
    flat = flat_t2_control()
    verdicts = {
        "torus_is_constrained_slice": (
            interior["interior_s3_constraint_max_residual"] < TOL
            and interior["eta_radius_max_residual"] < TOL
            and interior["periodic_closure_max_residual"] < TOL
            and interior["torus_metric_det_min"] > 0.0
            and interior["hopf_latitude_residual"] < TOL
        ),
        "foliation_covers_S3": (
            volume["foliation_volume_residual"] < COVERAGE_TOL
            and samples["sample_reconstruction_max_residual"] < TOL
            and samples["eta_bin_min_count"] > 0
            and core["core_circle_s3_residual"] < TOL
        ),
        "clifford_torus_equal_radius_slice": (
            clifford["clifford_equal_radius_residual"] < TOL
            and clifford["clifford_target_radius_residual"] < TOL
            and clifford["clifford_hopf_equator_residual"] < TOL
        ),
        "flat_t2_control_pass": flat["flat_t2_rejected"],
    }
    controls = {
        "flat_t2_off_s3_control_ok": flat["flat_t2_rejected"],
        "core_circles_control_ok": core["core_circle_s3_residual"] < TOL and core["core_zero_radius_residual"] < TOL,
    }
    controls["control_miswired"] = not (controls["flat_t2_off_s3_control_ok"] and controls["core_circles_control_ok"])
    shared_scalars = {
        "interior_s3_constraint_max_residual": interior["interior_s3_constraint_max_residual"],
        "eta_radius_max_residual": interior["eta_radius_max_residual"],
        "periodic_closure_max_residual": interior["periodic_closure_max_residual"],
        "torus_metric_det_min": interior["torus_metric_det_min"],
        "hopf_latitude_residual": interior["hopf_latitude_residual"],
        "volume_estimate": volume["volume_estimate"],
        "s3_volume_reference": volume["s3_volume_reference"],
        "foliation_volume_residual": volume["foliation_volume_residual"],
        "sample_reconstruction_max_residual": samples["sample_reconstruction_max_residual"],
        "eta_endpoint_gap": samples["eta_endpoint_gap"],
        "eta_bin_min_count": samples["eta_bin_min_count"],
        "core_circle_s3_residual": core["core_circle_s3_residual"],
        "core_zero_radius_residual": core["core_zero_radius_residual"],
        "clifford_equal_radius_residual": clifford["clifford_equal_radius_residual"],
        "clifford_target_radius_residual": clifford["clifford_target_radius_residual"],
        "clifford_hopf_equator_residual": clifford["clifford_hopf_equator_residual"],
        "flat_t2_s3_constraint_min_residual": flat["flat_t2_s3_constraint_min_residual"],
        "flat_t2_s3_constraint_max_residual": flat["flat_t2_s3_constraint_max_residual"],
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
        "claim_ceiling": "Finite Hopf-torus foliation check inside S3 only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind": "classical",
        "sim_class": "hopf_torus_foliation_geometry_probe",
        "tol": TOL,
        "coverage_tol": COVERAGE_TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "parameterization": "F(eta,phi,chi)=(cos(eta)*exp(i*phi), sin(eta)*exp(i*chi)); eta in (0,pi/2) gives Hopf tori, eta=0 and pi/2 give core circles.",
        "tool_manifest": {
            "JAX": "load-bearing finite torus parameterization, volume quadrature, and reconstruction checks",
            "jax.numpy": "load-bearing x64 complex geometry and residual reductions",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive"},
        "interior_tori": interior,
        "foliation_volume": volume,
        "sample_reconstruction": samples,
        "core_circles": core,
        "clifford_torus": clifford,
        "flat_t2_control": flat,
        "verdicts": verdicts,
        "controls": controls,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": "A3 only shows that the Hopf latitude slices form a finite checked torus family inside S3, with the Clifford torus as the equal-radius slice; it does not promote any downstream manifold or admission claim.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (
        controls["control_miswired"]
        or not verdicts["torus_is_constrained_slice"]
        or not verdicts["foliation_covers_S3"]
        or not verdicts["clifford_torus_equal_radius_slice"]
        or bool(result["parity"]["stop_condition_fired"])
    )
    return result


def print_summary(result: dict[str, Any]) -> None:
    s = result["shared_scalars"]
    print("clifford_torus_nested_hopf_foliation - JAX full sim")
    print(
        f"torus_is_constrained_slice={str(result['verdicts']['torus_is_constrained_slice']).lower()} "
        f"interior_s3_constraint_max_residual={s['interior_s3_constraint_max_residual']} "
        f"torus_metric_det_min={s['torus_metric_det_min']}"
    )
    print(
        f"foliation_covers_S3={str(result['verdicts']['foliation_covers_S3']).lower()} "
        f"foliation_volume_residual={s['foliation_volume_residual']} "
        f"sample_reconstruction_max_residual={s['sample_reconstruction_max_residual']} "
        f"eta_bin_min_count={s['eta_bin_min_count']}"
    )
    print(
        f"clifford_torus_equal_radius_slice={str(result['verdicts']['clifford_torus_equal_radius_slice']).lower()} "
        f"clifford_target_radius_residual={s['clifford_target_radius_residual']}"
    )
    print(
        f"flat_t2_control_pass={str(result['verdicts']['flat_t2_control_pass']).lower()} "
        f"flat_t2_s3_constraint_min_residual={s['flat_t2_s3_constraint_min_residual']}"
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
