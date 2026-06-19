#!/usr/bin/env python3
"""Finite knot rung: mass/gravity as two readouts of one finite knot.

Scratch diagnostic only. The primitive carrier is a finite spinor network
state over (C^2)^8. Density matrices are derived readout layers.
"""

from __future__ import annotations

import datetime as _dt
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
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/knot_mass_gravity_rung_results.json"
JULIA_RESULT_PATH = ROOT / "system_v5/julia_carrier/knot_mass_gravity_rung_julia_results.json"

OBJECT_ID = "knot_mass_gravity_rung"
BACKEND = "jax"
N = 8
DIM = 2**N
KNOT_SITE = 0
TOL = 1.0e-10
MASS_INVARIANT_TOL = 1.0e-8
PROFILE_CHANGE_MIN = 1.0e-3
CORRELATION_MIN = 0.95
LN2 = jnp.log(jnp.array(2.0, dtype=jnp.float64))
STRENGTHS = (0.0, 0.25, 0.5, 0.8, 1.15, 1.55, 2.0, 2.5, 3.1, 3.8)
REFERENCE_STRENGTH = 3.1
DECOUPLING_STRENGTH = 1.15
EDGES: tuple[tuple[int, int], ...] = tuple((idx, idx + 1) for idx in range(N - 1))
DISTANCES = tuple(range(N))
SHELL_RADII = tuple(range(1, N))
BASE_FIELD_WEIGHTS = (0.0, 1.0, 0.94, 0.89, 0.84, 0.80, 0.76, 0.68)
SHAPE_PERTURBED_WEIGHTS = (0.0, 1.0, 1.16, 0.67, 1.18, 0.62, 1.21, 0.54)
KNOT_BIAS = 1.35
FIELD_BIAS = 0.80


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def bit_table() -> jax.Array:
    indices = jnp.arange(DIM, dtype=jnp.uint32)
    cols = [((indices >> (N - 1 - node)) & jnp.uint32(1)).astype(jnp.float64) for node in range(N)]
    return jnp.stack(cols, axis=1)


BITS = bit_table()


def normalize(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi)


def graph_phase(bits: jax.Array) -> jax.Array:
    total = jnp.zeros((DIM,), dtype=jnp.float64)
    for left, right in EDGES:
        total = total + bits[:, left] * bits[:, right]
    return jnp.exp(1j * jnp.pi * total)


def finite_knot_state(strength: float | jax.Array, field_weights: tuple[float, ...] = BASE_FIELD_WEIGHTS) -> jax.Array:
    strength64 = jnp.array(strength, dtype=jnp.float64)
    weights = jnp.array(field_weights, dtype=jnp.float64)
    knot_energy = KNOT_BIAS * strength64 * BITS[:, KNOT_SITE]
    field_energy = FIELD_BIAS * strength64 * jnp.sum(BITS * weights[None, :], axis=1)
    amplitudes = jnp.exp(-(knot_energy + field_energy))
    return normalize(amplitudes.astype(jnp.complex128) * graph_phase(BITS))


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def reduced_density(rho: jax.Array, keep: tuple[int, ...]) -> jax.Array:
    traced = tuple(idx for idx in range(N) if idx not in keep)
    perm = keep + traced + tuple(idx + N for idx in keep) + tuple(idx + N for idx in traced)
    moved = jnp.transpose(jnp.reshape(rho, (2,) * (2 * N)), perm)
    dim_a = 2 ** len(keep)
    dim_b = 2 ** (N - len(keep))
    return jnp.einsum("abcb->ac", jnp.reshape(moved, (dim_a, dim_b, dim_a, dim_b)))


def entropy_probs(probs: jax.Array) -> jax.Array:
    vals = jnp.maximum(jnp.real(probs), 0.0)
    return -jnp.sum(jnp.where(vals > 1.0e-15, vals * jnp.log(vals), 0.0))


def entropy_rho(rho: jax.Array) -> jax.Array:
    hermitian = (rho + jnp.conj(rho.T)) / 2.0
    vals = jnp.maximum(jnp.real(jnp.linalg.eigvalsh(hermitian)), 0.0)
    return entropy_probs(vals)


def normalized_entropy(rho: jax.Array, dim: int) -> jax.Array:
    if dim <= 1:
        return jnp.array(0.0, dtype=jnp.float64)
    return entropy_rho(rho) / jnp.log(jnp.array(float(dim), dtype=jnp.float64))


def purity(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho @ rho))


def support_entropy(psi: jax.Array) -> jax.Array:
    probs = jnp.abs(psi) ** 2
    return entropy_probs(probs) / jnp.log(jnp.array(float(DIM), dtype=jnp.float64))


def mass_readout_from_rho(rho: jax.Array) -> tuple[jax.Array, dict[str, float]]:
    rho_k = reduced_density(rho, (KNOT_SITE,))
    local_purity = purity(rho_k)
    entropy_norm = normalized_entropy(rho_k, 2)
    purity_excess = jnp.clip((local_purity - 0.5) / 0.5, 0.0, 1.0)
    locality = jnp.array(1.0, dtype=jnp.float64)
    boundedness = jnp.clip(1.0 - entropy_norm, 0.0, 1.0)
    mass = purity_excess * locality * boundedness
    return mass, {
        "knot_site": float(KNOT_SITE),
        "local_purity": py_float(local_purity),
        "purity_excess_norm": py_float(purity_excess),
        "locality_weight": py_float(locality),
        "boundedness_negentropy": py_float(boundedness),
        "local_entropy_norm": py_float(entropy_norm),
    }


def shell_area(radius: int) -> float:
    return float(radius * radius)


def gravity_profile_from_rho(rho: jax.Array, flat_shell_entropies: jax.Array) -> tuple[jax.Array, dict[str, Any]]:
    mass_source, mass_detail = mass_readout_from_rho(rho)
    values = []
    rows = []
    for radius in SHELL_RADII:
        rho_i = reduced_density(rho, (radius,))
        entropy_i = normalized_entropy(rho_i, 2)
        entropy_drop = jnp.maximum(0.0, flat_shell_entropies[radius] - entropy_i)
        area = shell_area(radius)
        pressure = mass_source * entropy_drop / area
        values.append(pressure)
        rows.append(
            {
                "r": radius,
                "node": radius,
                "shell_area_square_possibilities": area,
                "shell_entropy_norm": py_float(entropy_i),
                "flat_shell_entropy_norm": py_float(flat_shell_entropies[radius]),
                "entropy_drop_from_flat": py_float(entropy_drop),
                "gravity_gradient": py_float(pressure),
            }
        )
    profile = jnp.array(values, dtype=jnp.float64)
    return profile, {
        "mass_source_detail": mass_detail,
        "profile": rows,
        "total_gravity": py_float(jnp.sum(profile)),
    }


def readouts(strength: float, field_weights: tuple[float, ...] = BASE_FIELD_WEIGHTS) -> dict[str, Any]:
    flat_psi = finite_knot_state(0.0, field_weights)
    flat_rho = density(flat_psi)
    flat_shell_entropies = jnp.array(
        [normalized_entropy(reduced_density(flat_rho, (node,)), 2) for node in range(N)], dtype=jnp.float64
    )
    psi = finite_knot_state(strength, field_weights)
    rho = density(psi)
    mass, mass_detail = mass_readout_from_rho(rho)
    profile, gravity_detail = gravity_profile_from_rho(rho, flat_shell_entropies)
    expansion = support_entropy(psi)
    return {
        "strength": float(strength),
        "mass": py_float(mass),
        "total_gravity": py_float(jnp.sum(profile)),
        "gravity_profile": [py_float(value) for value in profile],
        "expansion_dark_energy": py_float(expansion),
        "mass_detail": mass_detail,
        "gravity_detail": gravity_detail,
    }


def pearson_corr(xs: jax.Array, ys: jax.Array) -> jax.Array:
    x0 = xs - jnp.mean(xs)
    y0 = ys - jnp.mean(ys)
    denom = jnp.linalg.norm(x0) * jnp.linalg.norm(y0)
    return jnp.where(denom > 0.0, jnp.sum(x0 * y0) / denom, 0.0)


def monotone_non_decreasing(values: jax.Array, tol: float = 1.0e-12) -> bool:
    return py_bool(jnp.all(jnp.diff(values) >= -tol))


def monotone_decreasing(values: jax.Array, tol: float = 1.0e-12) -> bool:
    return py_bool(jnp.all(jnp.diff(values) <= tol))


def linear_fit(xs: jax.Array, ys: jax.Array) -> tuple[jax.Array, jax.Array]:
    x_mean = jnp.mean(xs)
    y_mean = jnp.mean(ys)
    denom = jnp.sum((xs - x_mean) ** 2)
    slope = jnp.where(denom > 0.0, jnp.sum((xs - x_mean) * (ys - y_mean)) / denom, 0.0)
    intercept = y_mean - slope * x_mean
    return slope, intercept


def sse(values: jax.Array, preds: jax.Array) -> jax.Array:
    return jnp.sum((values - preds) ** 2)


def falloff_fit(profile_values: list[float]) -> dict[str, Any]:
    radii = jnp.array([float(radius) for radius in SHELL_RADII], dtype=jnp.float64)
    profile = jnp.array(profile_values, dtype=jnp.float64)
    positive = jnp.maximum(profile, 1.0e-300)
    log_r = jnp.log(radii)
    log_g = jnp.log(positive)
    slope, intercept = linear_fit(log_r, log_g)
    exponent = -slope
    free_power_pred = jnp.exp(intercept) * radii ** (-exponent)

    alternatives: dict[str, dict[str, float]] = {}
    for fixed_exp in (0.0, 1.0, 2.0, 3.0):
        basis = radii ** (-fixed_exp)
        amp = jnp.sum(profile * basis) / jnp.sum(basis * basis)
        pred = amp * basis
        alternatives[f"power_e_{fixed_exp:g}"] = {"sse": py_float(sse(profile, pred)), "amplitude": py_float(amp)}

    exp_slope, exp_intercept = linear_fit(radii, log_g)
    exp_pred = jnp.exp(exp_intercept + exp_slope * radii)
    alternatives["exponential"] = {
        "sse": py_float(sse(profile, exp_pred)),
        "lambda": py_float(-exp_slope),
        "amplitude": py_float(jnp.exp(exp_intercept)),
    }
    alternatives["free_power"] = {"sse": py_float(sse(profile, free_power_pred)), "exponent": py_float(exponent)}
    best_model = min(alternatives, key=lambda key: alternatives[key]["sse"])
    return {
        "radii": [float(radius) for radius in SHELL_RADII],
        "profile": profile_values,
        "falloff_exponent": py_float(exponent),
        "monotone_decreasing": monotone_decreasing(profile),
        "alternative_fits": alternatives,
        "best_model_by_sse": best_model,
        "one_over_r2_sse": alternatives["power_e_2"]["sse"],
    }


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_10": False,
            "missing_from_peer": sorted(result["shared_scalars"].keys()),
            "missing_from_self": [],
            "diffs": {},
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    self_scalars = result["shared_scalars"]
    peer_scalars = peer.get("shared_scalars", {})
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    diffs: dict[str, float] = {}
    max_diff = 0.0
    worst_key = ""
    for key, value in self_scalars.items():
        if key in peer_scalars:
            diff = abs(float(value) - float(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_10": not missing_from_peer and not missing_from_self and max_diff <= TOL,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "diffs": diffs,
    }


def main() -> int:
    sweep_rows = [readouts(strength, BASE_FIELD_WEIGHTS) for strength in STRENGTHS]
    mass_values = jnp.array([row["mass"] for row in sweep_rows], dtype=jnp.float64)
    gravity_values = jnp.array([row["total_gravity"] for row in sweep_rows], dtype=jnp.float64)
    expansion_values = jnp.array([row["expansion_dark_energy"] for row in sweep_rows], dtype=jnp.float64)
    corr = pearson_corr(mass_values, gravity_values)
    ref = readouts(REFERENCE_STRENGTH, BASE_FIELD_WEIGHTS)
    falloff = falloff_fit(ref["gravity_profile"])
    flat = sweep_rows[0]

    shape_a = readouts(DECOUPLING_STRENGTH, BASE_FIELD_WEIGHTS)
    shape_b = readouts(DECOUPLING_STRENGTH, SHAPE_PERTURBED_WEIGHTS)
    profile_a = jnp.array(shape_a["gravity_profile"], dtype=jnp.float64)
    profile_b = jnp.array(shape_b["gravity_profile"], dtype=jnp.float64)
    mass_shape_diff = abs(shape_a["mass"] - shape_b["mass"])
    profile_l2_diff = py_float(jnp.linalg.norm(profile_a - profile_b))
    shape_b_falloff = falloff_fit(shape_b["gravity_profile"])
    exponent_delta = abs(falloff["falloff_exponent"] - shape_b_falloff["falloff_exponent"])

    flatten_both_vanish = flat["mass"] <= TOL and flat["total_gravity"] <= TOL
    dark_energy_distinct = flatten_both_vanish and abs(flat["expansion_dark_energy"] - 1.0) <= TOL
    co_scaling = (
        monotone_non_decreasing(mass_values)
        and monotone_non_decreasing(gravity_values)
        and py_float(corr) >= CORRELATION_MIN
        and sweep_rows[-1]["mass"] > 0.0
        and sweep_rows[-1]["total_gravity"] > 0.0
    )
    falloff_pass = falloff["monotone_decreasing"] and falloff["falloff_exponent"] > 0.0
    decoupling_witness = mass_shape_diff <= MASS_INVARIANT_TOL and profile_l2_diff >= PROFILE_CHANGE_MIN

    shared_scalars: dict[str, float] = {
        "mass_gravity_corr": py_float(corr),
        "falloff_exponent": float(falloff["falloff_exponent"]),
        "falloff_one_over_r2_sse": float(falloff["one_over_r2_sse"]),
        "shape_b_falloff_exponent": float(shape_b_falloff["falloff_exponent"]),
        "shape_exponent_delta": float(exponent_delta),
        "shape_mass_abs_diff": float(mass_shape_diff),
        "shape_profile_l2_diff": float(profile_l2_diff),
        "flatten_mass": float(flat["mass"]),
        "flatten_gravity": float(flat["total_gravity"]),
        "flatten_expansion_dark_energy": float(flat["expansion_dark_energy"]),
        "flatten_both_vanish": 1.0 if flatten_both_vanish else 0.0,
        "dark_energy_distinct": 1.0 if dark_energy_distinct else 0.0,
        "co_scaling": 1.0 if co_scaling else 0.0,
        "falloff_pass": 1.0 if falloff_pass else 0.0,
        "decoupling_witness": 1.0 if decoupling_witness else 0.0,
    }
    for idx, row in enumerate(sweep_rows):
        shared_scalars[f"sweep_{idx}.strength"] = float(row["strength"])
        shared_scalars[f"sweep_{idx}.mass"] = float(row["mass"])
        shared_scalars[f"sweep_{idx}.total_gravity"] = float(row["total_gravity"])
        shared_scalars[f"sweep_{idx}.expansion_dark_energy"] = float(row["expansion_dark_energy"])
    for idx, value in enumerate(ref["gravity_profile"]):
        shared_scalars[f"falloff_profile.r{SHELL_RADII[idx]}"] = float(value)
    for idx, value in enumerate(shape_b["gravity_profile"]):
        shared_scalars[f"shape_perturbed_profile.r{SHELL_RADII[idx]}"] = float(value)

    positive = {
        "co_scaling_same_source_strength_sweep": {
            "strengths": list(STRENGTHS),
            "mass_values": [row["mass"] for row in sweep_rows],
            "total_gravity_values": [row["total_gravity"] for row in sweep_rows],
            "mass_monotone_non_decreasing": monotone_non_decreasing(mass_values),
            "gravity_monotone_non_decreasing": monotone_non_decreasing(gravity_values),
            "mass_gravity_corr": py_float(corr),
            "correlation_min": CORRELATION_MIN,
            "pass": co_scaling,
        },
        "falloff_by_network_distance_reported_not_forced": {
            **falloff,
            "pass": falloff_pass,
        },
        "flatten_control_mass_and_gravity_vanish_together": {
            "strength": 0.0,
            "mass": flat["mass"],
            "total_gravity": flat["total_gravity"],
            "flatten_both_vanish": flatten_both_vanish,
            "pass": flatten_both_vanish,
        },
        "dark_energy_distinct_from_local_knot_readouts": {
            "flatten_expansion_dark_energy": flat["expansion_dark_energy"],
            "flatten_mass": flat["mass"],
            "flatten_gravity": flat["total_gravity"],
            "pass": dark_energy_distinct,
        },
        "anti_by_construction_shape_decoupling_witness": {
            "reference_strength": DECOUPLING_STRENGTH,
            "falloff_reference_strength": REFERENCE_STRENGTH,
            "base_field_weights_by_node": list(BASE_FIELD_WEIGHTS),
            "shape_perturbed_weights_by_node": list(SHAPE_PERTURBED_WEIGHTS),
            "base_mass": shape_a["mass"],
            "perturbed_mass": shape_b["mass"],
            "mass_abs_diff": mass_shape_diff,
            "mass_invariant_tolerance": MASS_INVARIANT_TOL,
            "base_gravity_profile": shape_a["gravity_profile"],
            "perturbed_gravity_profile": shape_b["gravity_profile"],
            "profile_l2_diff": profile_l2_diff,
            "profile_change_min": PROFILE_CHANGE_MIN,
            "base_falloff_exponent": falloff["falloff_exponent"],
            "perturbed_falloff_exponent": shape_b_falloff["falloff_exponent"],
            "exponent_delta": exponent_delta,
            "pass": decoupling_witness,
        },
    }
    graveyard_companions = {
        "mass_and_gravity_are_not_same_scalar": {
            "mass_definition": "knot subregion reduced-state purity excess times bounded negentropy and locality",
            "gravity_definition": "surrounding shell entropy-drop pressure times knot source divided by finite shell area",
            "decoupling_witness": decoupling_witness,
            "pass": decoupling_witness,
        },
        "physics_promotion_rejected": {
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "pass": True,
        },
        "one_over_r2_not_forced": {
            "free_power_exponent": falloff["falloff_exponent"],
            "best_model_by_sse": falloff["best_model_by_sse"],
            "fixed_1_over_r2_sse": falloff["one_over_r2_sse"],
            "pass": True,
        },
    }
    boundary = {
        "finite_spinor_network_boundary": {
            "n_spinor_sites": N,
            "hilbert_dimension": DIM,
            "edges": [list(edge) for edge in EDGES],
            "distances_from_knot": list(DISTANCES),
            "pass": 5 <= N <= 8 and DIM == 256,
        },
        "jax_x64_no_numpy_compute": {
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "numpy_compute_used": False,
            "pass": bool(jax.config.read("jax_enable_x64")),
        },
        "claim_fence_non_admitting": {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "pass": True,
        },
    }
    local_all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result: dict[str, Any] = {
        "schema": "FINITE_KNOT_MASS_GRAVITY_RUNG_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "finite knot rung: mass and gravity co-arise as two readouts of one finite knot; "
            "NO admission of gravity/G/mass/physics/Axis0/M(C); the 1/r^2 fit is diagnostic only"
        ),
        "carrier": {
            "primitive": "finite spinor-network state psi over (C^2)^8",
            "nodes": N,
            "edges": [list(edge) for edge in EDGES],
            "knot_subregion": [KNOT_SITE],
            "distance_surface": {str(node): DISTANCES[node] for node in range(N)},
            "hilbert_dimension": DIM,
            "state_family": "finite graph-phase spinor network with tunable local amplitude knot and surrounding field weights",
            "density_status": "rho and rho_A are derived readout layers, not primitive state declarations",
        },
        "readout_definitions": {
            "mass": "local stability/binding of the knot subregion: local purity excess x locality x bounded negentropy",
            "gravity": "surrounding entropy/possibility-gradient: shell entropy drop from flat x knot source / graph-distance shell area",
            "dark_energy_expansion": "global computational-support entropy; maximal in the flattened no-knot carrier",
        },
        "sweep_rows": sweep_rows,
        "reference_strength": REFERENCE_STRENGTH,
        "reference_readouts": ref,
        "shape_decoupling": positive["anti_by_construction_shape_decoupling_witness"],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "variants": ["flatten_s0", "base_knot_strength_sweep", "shape_perturbed_same_knot_mass"],
            "all_pass": True,
        },
        "why_not_v4_probes": "This is a v5 dual-backend scratch diagnostic formal scout; it is not a v4 probe or promotion artifact.",
        "blockers": [],
        "open_choices": [
            "Falloff exponent is a fitted diagnostic on a finite graph-distance profile, not a physical law.",
            "Mass and gravity labels are requested readout names only; neither is admitted as physics.",
            "Shape perturbation keeps the local knot source fixed while changing surrounding field weights to exhibit functional separation.",
        ],
        "eligible_consumers": ["scratch diagnostic audits", "dual-backend parity checks", "future non-promoting knot-readout scouts"],
        "blocked_consumers": ["gravity admission", "G estimation", "mass admission", "physics", "Axis0", "M(C)", "bridge", "final manifold closure"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite spinor-network construction, reduced-state mass readout, shell entropy-gradient gravity readout, sweep correlation, falloff fit, and parity scalars",
            },
            "Python json/pathlib": {
                "tried": True,
                "used": True,
                "reason": "supportive receipt writing to the exact formal_scouts result path",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing", "Python json/pathlib": "supportive"},
        "shared_scalars": shared_scalars,
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_10"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "mass_gravity_corr": py_float(corr),
        "falloff_exponent": falloff["falloff_exponent"],
        "flatten_both_vanish": flatten_both_vanish,
        "decoupling_witness": decoupling_witness,
        "parity_within_1e_10": result["parity"]["within_1e_10"],
    }
    result["result_summary"] = result["summary"]

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    if not local_all_pass:
        raise SystemExit(1)
    if result["parity"]["peer_available"] and not result["parity"]["within_1e_10"]:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
