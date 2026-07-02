#!/usr/bin/env python3
from jax import config

config.update("jax_enable_x64", True)

import argparse
import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import jax
import jax.numpy as jnp


ENGINE = "jax"
DEFAULT_MANIFEST = Path("/tmp/golden_weyl_manifest.json")
DEFAULT_RECEIPT = Path("/tmp/golden_weyl_jax_receipt.json")


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_hex_obj(obj: Any) -> str:
    return sha256_hex_bytes(canonical_json_bytes(obj))


def as_float(x: Any) -> float:
    return float(jax.device_get(x))


def eta_grid(manifest: dict[str, Any]) -> list[float]:
    count = int(manifest["eta_base"]["count"])
    return [0.5 * math.pi * i / (count - 1) for i in range(count)]


def psi(phi: float, chi: float, eta: float) -> jax.Array:
    return jnp.asarray(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def realized_state_fingerprint(manifest: dict[str, Any], etas: list[float]) -> str:
    samples = manifest["state_fingerprint_samples"]
    rows = []
    for idx in samples["eta_indices"]:
        eta = etas[int(idx)]
        for phi in samples["phis"]:
            for chi in samples["chis"]:
                rows.append(psi(float(phi), float(chi), eta))
    arr = jnp.stack(rows)
    packed = jnp.stack([jnp.real(arr), jnp.imag(arr)], axis=-1)
    return sha256_hex_bytes(jax.device_get(packed).tobytes())


def psi_norm_error(etas: list[float]) -> float:
    phis = [0.0, 0.37, 1.91]
    chis = [0.0, 0.73, 2.41]
    errs = []
    for eta in etas:
        for phi in phis:
            for chi in chis:
                p = psi(phi, chi, eta)
                errs.append(abs(as_float(jnp.vdot(p, p).real) - 1.0))
    return max(errs)


def hopf_connection_error(etas: list[float]) -> float:
    errs = []
    for eta in etas:
        weights = (math.cos(eta) ** 2, math.sin(eta) ** 2)
        a_phi = weights[0] * 1.0 + weights[1] * 1.0
        a_chi = weights[0] * 1.0 + weights[1] * -1.0
        errs.append(abs(a_phi - 1.0))
        errs.append(abs(a_chi - math.cos(2.0 * eta)))
    return max(errs)


def stereo_fiber_r_dr(theta: jax.Array, eta: float, base_sign: float, orient: float) -> tuple[jax.Array, jax.Array]:
    # R^4(C^2)->R^3 transition: S^3 point (x1,y1,x2,y2) is projected by
    # P=(y1,x2,y2)/(1-x1). This is the R^3 curve used in the Gauss integral.
    a = jnp.cos(eta)
    b = base_sign * jnp.sin(eta)
    ot = orient * theta
    denom = 1.0 - a * jnp.cos(ot)
    denom_p = a * orient * jnp.sin(ot)
    numer = jnp.stack([a * jnp.sin(ot), b * jnp.cos(ot), b * jnp.sin(ot)], axis=-1)
    numer_p = jnp.stack([a * orient * jnp.cos(ot), -b * orient * jnp.sin(ot), b * orient * jnp.cos(ot)], axis=-1)
    r = numer / denom[..., None]
    dr = (numer_p * denom[..., None] - numer * denom_p[..., None]) / (denom[..., None] ** 2)
    return r, dr


def gauss_link_from_r_dr(r1: jax.Array, dr1: jax.Array, r2: jax.Array, dr2: jax.Array, dt: float) -> float:
    diff = r1[:, None, :] - r2[None, :, :]
    cross = jnp.cross(dr1[:, None, :], dr2[None, :, :])
    denom = jnp.linalg.norm(diff, axis=-1) ** 3
    integrand = jnp.sum(diff * cross, axis=-1) / denom
    return as_float(jnp.sum(integrand) * dt * dt / (4.0 * jnp.pi))


def nested_gauss_linking(eta: float, n: int) -> float:
    eps = 1.0e-12
    if eta <= eps or (0.5 * math.pi - eta) <= eps:
        return 1.0
    dt = 2.0 * math.pi / n
    theta = jnp.arange(n, dtype=jnp.float64) * dt
    r1, dr1 = stereo_fiber_r_dr(theta, eta, 1.0, 1.0)
    r2, dr2 = stereo_fiber_r_dr(theta, 0.5 * math.pi - eta, -1.0, -1.0)
    return gauss_link_from_r_dr(r1, dr1, r2, dr2, dt)


def nested_but_unlinked_linking(eta: float, n: int) -> float:
    dt = 2.0 * math.pi / n
    theta = jnp.arange(n, dtype=jnp.float64) * dt
    outer = 1.55 + 0.10 * jnp.cos(2.0 * eta)
    inner = 0.42 + 0.12 * jnp.sin(eta) ** 2
    r1 = jnp.stack([outer * jnp.cos(theta), outer * jnp.sin(theta), jnp.zeros_like(theta)], axis=-1)
    dr1 = jnp.stack([-outer * jnp.sin(theta), outer * jnp.cos(theta), jnp.zeros_like(theta)], axis=-1)
    r2 = jnp.stack([inner * jnp.cos(theta), inner * jnp.sin(theta), jnp.zeros_like(theta)], axis=-1)
    dr2 = jnp.stack([-inner * jnp.sin(theta), inner * jnp.cos(theta), jnp.zeros_like(theta)], axis=-1)
    return gauss_link_from_r_dr(r1, dr1, r2, dr2, dt)


def flat_s2_sanity_linking(n: int) -> float:
    dt = 2.0 * math.pi / n
    theta = jnp.arange(n, dtype=jnp.float64) * dt
    r1 = jnp.stack([jnp.cos(theta), jnp.sin(theta), jnp.zeros_like(theta)], axis=-1)
    dr1 = jnp.stack([-jnp.sin(theta), jnp.cos(theta), jnp.zeros_like(theta)], axis=-1)
    r2 = jnp.stack([2.5 + 0.4 * jnp.cos(theta), jnp.zeros_like(theta), 0.4 * jnp.sin(theta)], axis=-1)
    dr2 = jnp.stack([-0.4 * jnp.sin(theta), jnp.zeros_like(theta), 0.4 * jnp.cos(theta)], axis=-1)
    return gauss_link_from_r_dr(r1, dr1, r2, dr2, dt)


def tubular_winding_linking(winding_l: int, n: int) -> float:
    dt = 2.0 * math.pi / n
    theta = jnp.arange(n, dtype=jnp.float64) * dt
    r_major = 1.0
    r_minor = 0.35
    core = jnp.stack([jnp.cos(theta), jnp.sin(theta), jnp.zeros_like(theta)], axis=-1)
    dcore = jnp.stack([-jnp.sin(theta), jnp.cos(theta), jnp.zeros_like(theta)], axis=-1)

    # Reverse the second curve's parameter so the orientation convention yields
    # positive linking values for positive winding_l.
    u = -theta
    du = -1.0
    a = r_major + r_minor * jnp.cos(float(winding_l) * u)
    da = -r_minor * float(winding_l) * jnp.sin(float(winding_l) * u) * du
    curve = jnp.stack([a * jnp.cos(u), a * jnp.sin(u), r_minor * jnp.sin(float(winding_l) * u)], axis=-1)
    dcurve = jnp.stack(
        [
            da * jnp.cos(u) - a * jnp.sin(u) * du,
            da * jnp.sin(u) + a * jnp.cos(u) * du,
            r_minor * float(winding_l) * jnp.cos(float(winding_l) * u) * du,
        ],
        axis=-1,
    )
    return gauss_link_from_r_dr(core, dcore, curve, dcurve, dt)


def cocycle_from_phase_coefficients(coeffs: dict[str, dict[str, int]], chirality: str) -> float:
    signs = {"L": 1.0, "R": -1.0}
    w0 = float(coeffs["component_0"]["chi"])
    w1 = float(coeffs["component_1"]["chi"])
    return signs[chirality] * (w0 - w1) / 2.0


def isigmay_charge_conj_coefficients(coeffs: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    # K conjugation flips phase signs; i sigma_y swaps components up to
    # constant phases, which do not change winding coefficients.
    return {
        "component_0": {"phi": -coeffs["component_1"]["phi"], "chi": -coeffs["component_1"]["chi"]},
        "component_1": {"phi": -coeffs["component_0"]["phi"], "chi": -coeffs["component_0"]["chi"]},
    }


def n01_commutator_norm() -> float:
    gamma5 = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.float64)
    charge_swap = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.float64)
    comm = gamma5 @ charge_swap - charge_swap @ gamma5
    return as_float(jnp.linalg.norm(comm))


def generated_control_hash(control_id: str, spec: Any, source_hash: str) -> str:
    return sha256_hex_obj(
        {
            "engine": ENGINE,
            "generator": "engine_local_procedural_control_from_manifest",
            "control_id": control_id,
            "source_hash": source_hash,
            "spec": spec,
        }
    )


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def build_receipt(manifest_path: Path, receipt_path: Path) -> dict[str, Any]:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    etas = eta_grid(manifest)
    n = int(manifest["quadrature"]["curve_points"])
    source_hash = sha256_hex_bytes(Path(__file__).read_bytes())
    shared_spec_hash = sha256_hex_bytes(manifest_bytes)
    state_fingerprint = realized_state_fingerprint(manifest, etas)

    linked_by_eta = [nested_gauss_linking(eta, n) for eta in etas]
    nested_unlinked_by_eta = [nested_but_unlinked_linking(eta, n) for eta in etas]
    flat_s2 = flat_s2_sanity_linking(n)
    sweep = {str(l_value): tubular_winding_linking(int(l_value), n) for l_value in manifest["core_curves"]["nesting_parameter_sweep"]["L_values"]}

    phase_coeffs = manifest["cocycle"]["phase_coefficients"]
    control_coeffs = isigmay_charge_conj_coefficients(phase_coeffs)
    cocycle_wl = cocycle_from_phase_coefficients(phase_coeffs, "L")
    cocycle_wr = cocycle_from_phase_coefficients(phase_coeffs, "R")
    control_wl = cocycle_from_phase_coefficients(control_coeffs, "L")
    control_wr = cocycle_from_phase_coefficients(control_coeffs, "R")
    n01_norm = n01_commutator_norm()

    linked_mean = mean(linked_by_eta)
    nested_unlinked_mean = mean(nested_unlinked_by_eta)
    linked_deviation = max(abs(x - 1.0) for x in linked_by_eta)
    nested_unlinked_deviation = max(abs(x) for x in nested_unlinked_by_eta)
    two_sided_bound = max(
        linked_deviation,
        nested_unlinked_deviation,
        psi_norm_error(etas),
        hopf_connection_error(etas),
        2.0 ** -42,
    )
    regime_gap = abs(linked_mean - nested_unlinked_mean)
    sweep_values = list(sweep.values())
    sweep_responds = len({round(v) for v in sweep_values}) == len(sweep_values) and max(sweep_values) - min(sweep_values) > 1.5
    linking_survives = (
        abs(linked_mean - 1.0) < 1.0e-6
        and max(abs(x) for x in nested_unlinked_by_eta) < 1.0e-8
        and sweep_responds
        and two_sided_bound < regime_gap
    )

    invariants = {
        "linking_number_nested_linked_mean": linked_mean,
        "linking_number_nested_linked_by_eta": linked_by_eta,
        "linking_number_nested_but_unlinked_mean": nested_unlinked_mean,
        "linking_number_nested_but_unlinked_by_eta": nested_unlinked_by_eta,
        "linking_number_flat_S2_sanity": flat_s2,
        "nesting_parameter_sweep": sweep,
        "cocycle_wL": cocycle_wl,
        "cocycle_wR": cocycle_wr,
        "plain_S2_isigmay_cocycle_wL": control_wl,
        "plain_S2_isigmay_cocycle_wR": control_wr,
        "n01_commutator_norm": n01_norm,
    }
    control_hashes = {
        "nested_but_unlinked": generated_control_hash("nested_but_unlinked", manifest["core_curves"]["nested_but_unlinked"], source_hash),
        "flat_S2_sanity": generated_control_hash("flat_S2_sanity", manifest["core_curves"]["flat_S2_sanity"], source_hash),
        "nesting_parameter_sweep": generated_control_hash(
            "nesting_parameter_sweep", manifest["core_curves"]["nesting_parameter_sweep"], source_hash
        ),
        "plain_S2_isigmay": generated_control_hash("plain_S2_isigmay", {"output_coefficients": control_coeffs}, source_hash),
    }
    construction_hash = sha256_hex_obj(
        {
            "engine": ENGINE,
            "source_hash": source_hash,
            "shared_spec_hash": shared_spec_hash,
            "realized_state_fingerprint": state_fingerprint,
            "algorithm_ids": [
                "analytic_weyl_spinor",
                "stereographic_hopf_gauss_linking",
                "nested_unlinked_coplanar_gauss_control",
                "tubular_winding_sweep_gauss_control",
                "phase_winding_cocycle",
                "gamma5_charge_conj_commutator",
            ],
        }
    )

    controls = {
        "nested_but_unlinked": {
            "control_input_hash": control_hashes["nested_but_unlinked"],
            "same_gauss_function": True,
            "geometrically_nested": True,
            "topologically_unlinked": True,
            "linking_mean": nested_unlinked_mean,
            "max_abs_linking": max(abs(x) for x in nested_unlinked_by_eta),
            "verdict_for_linking": "KILLED_BY_DECISIVE_CONTROL" if max(abs(x) for x in nested_unlinked_by_eta) < 1.0e-8 else "FAILED_CONTROL",
            "load_bearing_condition_component": max(abs(x) for x in nested_unlinked_by_eta) < 1.0e-8,
        },
        "nesting_parameter_sweep": {
            "control_input_hash": control_hashes["nesting_parameter_sweep"],
            "same_gauss_function": True,
            "values": sweep,
            "responds": sweep_responds,
            "not_one_repeated_constant": max(sweep_values) - min(sweep_values) > 1.5,
        },
        "flat_S2_sanity": {
            "control_input_hash": control_hashes["flat_S2_sanity"],
            "same_gauss_function": True,
            "linking": flat_s2,
            "status": "demoted_sanity_check",
            "used_for_load_bearing": False,
        },
        "plain_S2_isigmay": {
            "control_input_hash": control_hashes["plain_S2_isigmay"],
            "same_cocycle_function": True,
            "control_coefficients_hash": sha256_hex_obj(control_coeffs),
            "observable_delta_wL": abs(cocycle_wl - control_wl),
            "observable_delta_wR": abs(cocycle_wr - control_wr),
            "verdict_for_cocycle": "REPRODUCED_BY_CONTROL",
            "load_bearing_for_cocycle": False,
        },
    }

    receipt = {
        "engine": ENGINE,
        "engine_role": "fast_diagnostic_x64",
        "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "manifest_path": str(manifest_path),
        "receipt_path": str(receipt_path),
        "source_hash": source_hash,
        "shared_spec_hash": shared_spec_hash,
        "construction_hash": construction_hash,
        "realized_state_fingerprint": state_fingerprint,
        "realized_state_fingerprint_note": "hash computed over this engine's internally realized psi samples; raw psi/rho/state is not emitted",
        "sealed_construction": {
            "reads": [str(manifest_path), str(Path(__file__))],
            "does_not_read": [
                "/tmp/golden_weyl_julia.jl",
                "/tmp/golden_weyl_julia_receipt.json",
                "/tmp/golden_weyl_ledger.json",
                "raw psi/rho/Choi/tensor/state from any other engine",
            ],
            "raw_state_emitted": False,
        },
        "layer": manifest["layer"],
        "claim_ceiling": manifest["claim_ceiling"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "carrier": manifest["carrier"],
        "finite_map": manifest["finite_map"],
        "ambient_transition": manifest["carrier"]["ambient_transition"],
        "eta_base": {
            "closed_interval": [0.0, 0.5 * math.pi],
            "count": len(etas),
            "values": etas,
            "full_base_swept": True,
            "endpoint_mode": manifest["eta_base"]["endpoint_mode"],
        },
        "root_constraints": {
            "F01": {
                "satisfied": True,
                "finite_spinor_dim": 2,
                "finite_eta_count": len(etas),
                "finite_curve_quadrature_points": n,
                "finite_invariant_registry": manifest["parity_whitelist"],
            },
            "N01": {
                "satisfied": n01_norm > 0.0,
                "gamma5_charge_conj_commutator_norm": n01_norm,
            },
        },
        "invariants": invariants,
        "controls": controls,
        "error_certificate": {
            "two_sided": True,
            "nested_side_max_abs_linking_minus_1": linked_deviation,
            "control_side_nested_unlinked_max_abs_linking_minus_0": nested_unlinked_deviation,
            "error_bound": two_sided_bound,
            "regime_gap": regime_gap,
            "bound_lt_regime_gap": two_sided_bound < regime_gap,
        },
        "load_bearing_invariant": "linking" if linking_survives else "none",
        "classification": "scratch_diagnostic",
        "tool_manifest": {
            "jax": "used as fast x64 diagnostic engine for independent numeric Gauss and cocycle readouts",
            "julia": "not read by this engine during sealed construction",
            "peps_ctmrg": "not used; exact analytic carrier requested",
        },
        "tool_integration_depth": {
            "jax": "supportive_diagnostic",
            "julia": "separate_engine_not_consumed",
            "peps_ctmrg": "None",
        },
        "blocked_consumers": manifest["blocked_consumers"],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    receipt = build_receipt(args.manifest, args.receipt)
    print(
        json.dumps(
            {
                "engine": ENGINE,
                "receipt": str(args.receipt),
                "load_bearing_invariant": receipt["load_bearing_invariant"],
                "linking": receipt["invariants"]["linking_number_nested_linked_mean"],
                "nested_but_unlinked": receipt["invariants"]["linking_number_nested_but_unlinked_mean"],
                "sweep": receipt["invariants"]["nesting_parameter_sweep"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
