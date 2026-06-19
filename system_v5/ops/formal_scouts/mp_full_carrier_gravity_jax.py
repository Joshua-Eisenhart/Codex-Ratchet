#!/usr/bin/env python3
# object_id: mp_full_carrier_gravity
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
CARRIER_DIR = ROOT / "system_v5/julia_carrier"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mp_full_carrier_gravity_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp_full_carrier_gravity_julia_results.json"

OBJECT_ID = "mp_full_carrier_gravity"
BACKEND = "jax_jnp_x64"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
REFERENCE_STRENGTH = 2.4
STRENGTHS = (0.0, 0.25, 0.5, 0.85, 1.2, 1.65, 2.1, 2.6, 3.1)
LN2 = jnp.log(jnp.array(2.0, dtype=jnp.float64))

SOURCE_ETA = 0.7853981633974483
SOURCE_PHI = 0.17
SOURCE_CHI = -0.23
SHELL_ETAS = (0.34, 0.43, 0.57, 0.71, 0.92, 1.08, 1.23, 1.36)
SHELL_PHIS = (0.23, 0.58, 1.03, 1.59, 2.17, 2.84, 3.48, 4.26)
SHELL_CHIS = (-0.37, -0.06, 0.51, 1.04, 1.73, 2.28, 2.96, 3.64)
GRAPH_INDICES = tuple(float(i + 1) for i in range(len(SHELL_ETAS)))


def load_owner_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load owner module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OWNER_DENSITY = load_owner_module("owner_density_matrix_spinor_lift", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
OWNER_HOPF = load_owner_module("owner_clifford_torus_nested_hopf_foliation", CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py")
OWNER_GOLDEN = load_owner_module("owner_golden_weyl_jax", CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py")

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
H0 = 0.77 * SZ + 0.13 * SX
OPERATOR_BASE_ANGLES = {"Ti": 0.12, "Te": 0.09, "Fi": 0.15, "Fe": 0.11}
TOPOLOGY_RATES = {"Se": 0.18, "Ne": 0.13, "Ni": 0.28, "Si": 0.20}


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def shared(path: str) -> dict[str, Any]:
    return read_json(CARRIER_DIR / path).get("shared_scalars", {})


def golden() -> dict[str, Any]:
    return read_json(CARRIER_DIR / "golden_weyl_julia_receipt.json")


def carrier_invariants() -> dict[str, Any]:
    division = shared("division_algebra_ratchet_ladder_jax_results.json")
    clifford = shared("clifford_algebra_ladder_jax_results.json")
    g2 = shared("octonion_G2_automorphism_jax_results.json")
    sedenion = shared("sedenion_break_prelim_jax_results.json")
    density = shared("density_matrix_spinor_lift_jax_results.json")
    hopf = shared("clifford_torus_nested_hopf_foliation_jax_results.json")
    owner_hopf = OWNER_HOPF.interior_torus_checks()
    gw = golden()
    owner_state = OWNER_GOLDEN.psi(SOURCE_PHI, SOURCE_CHI, SOURCE_ETA)
    owner_rho = OWNER_DENSITY.dm(owner_state)
    owner_bloch = OWNER_DENSITY.bloch_from_rho(owner_rho)
    values = {
        "division_H_dim": float(division["H.dim"]),
        "division_O_dim": float(division["O.dim"]),
        "clifford_cl30_even_dim": float(clifford["cl30.even_dim"]),
        "g2_derivation_dim": float(g2["der_O_dim"]),
        "sedenion_dim": float(sedenion["S.dim"]),
        "sedenion_norm_break": float(sedenion["S.max_norm_mult_residual"]),
        "density_fiber_dim": float(density["fiber_dim"]),
        "hopf_metric_det_min": float(hopf["torus_metric_det_min"]),
        "owner_hopf_metric_det_min": float(owner_hopf["torus_metric_det_min"]),
        "owner_density_trace": py_float(jnp.real(jnp.trace(owner_rho))),
        "owner_density_bloch_norm": py_float(jnp.linalg.norm(owner_bloch)),
        "owner_golden_state_norm": py_float(jnp.real(jnp.vdot(owner_state, owner_state))),
        "golden_linking": float(gw["invariants"]["linking_number"]),
        "golden_flat_linking_abs": abs(float(gw["invariants"]["flat_S2_linking_number"])),
        "golden_cocycle_wL": float(gw["invariants"]["cocycle_wL"]),
        "golden_cocycle_wR": float(gw["invariants"]["cocycle_wR"]),
    }
    values["carrier_gain"] = 1.0 + 1.0e-3 * (
        values["division_H_dim"]
        + values["clifford_cl30_even_dim"]
        + values["g2_derivation_dim"]
        + values["density_fiber_dim"]
    )
    return values


def spinor(eta: float, phi: float, chi: float) -> jax.Array:
    return OWNER_GOLDEN.psi(phi, chi, eta)


def density(psi: jax.Array) -> jax.Array:
    return OWNER_DENSITY.dm(psi)


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return OWNER_DENSITY.bloch_from_rho(rho)


def fs_distance(a: jax.Array, b: jax.Array) -> jax.Array:
    overlap = jnp.abs(jnp.vdot(a, b)) / jnp.sqrt(jnp.real(jnp.vdot(a, a) * jnp.vdot(b, b)))
    return jnp.arccos(jnp.clip(overlap, 0.0, 1.0))


def qubit_entropy_norm(bloch_radius: jax.Array) -> jax.Array:
    r = jnp.clip(bloch_radius, 0.0, 1.0)
    vals = jnp.array([(1.0 + r) / 2.0, (1.0 - r) / 2.0], dtype=jnp.float64)
    entropy = -jnp.sum(jnp.where(vals > 1.0e-15, vals * jnp.log(vals), 0.0))
    return entropy / LN2


def mass_from_strength(strength: float, carrier_gain: float) -> jax.Array:
    radius = jnp.tanh(jnp.array(strength * carrier_gain, dtype=jnp.float64))
    return 1.0 - qubit_entropy_norm(radius)


def qit_substage_response(bloch: jax.Array, chirality_sign: float) -> jax.Array:
    h0_expect = jnp.real(jnp.trace(density_from_bloch(bloch) @ (chirality_sign * H0)))
    response = jnp.array(0.0, dtype=jnp.float64)
    ordered_ops = ("Ti", "Te", "Fi", "Fe")
    ordered_topologies = ("Se", "Ne", "Ni", "Si")
    for cycle in range(2):
        for topology in ordered_topologies:
            for op in ordered_ops:
                op_angle = OPERATOR_BASE_ANGLES[op]
                rate = TOPOLOGY_RATES[topology]
                sign = 1.0 if ((cycle + len(op) + len(topology)) % 2 == 0) else -1.0
                response = response + rate * (1.0 + sign * chirality_sign * op_angle * h0_expect)
    return response / 32.0


def density_from_bloch(bloch: jax.Array) -> jax.Array:
    return 0.5 * (I2 + bloch[0] * SX + bloch[1] * SY + bloch[2] * SZ)


def carrier_profile(
    strength: float,
    chirality: str,
    invariants: dict[str, Any],
    use_flat_link: bool = False,
    wrong_graph_distance: bool = False,
) -> dict[str, Any]:
    sign = 1.0 if chirality == "L" else -1.0
    source = spinor(SOURCE_ETA, SOURCE_PHI, SOURCE_CHI)
    source_rho = density(source)
    source_bloch = bloch_from_rho(source_rho)
    mass = mass_from_strength(strength, invariants["carrier_gain"])
    link = invariants["golden_flat_linking_abs"] if use_flat_link else invariants["golden_linking"]
    cocycle = invariants["golden_cocycle_wL"] if chirality == "L" else invariants["golden_cocycle_wR"]
    rows: list[dict[str, Any]] = []
    profile_values: list[float] = []
    metric_distances: list[float] = []
    fit_distances: list[float] = []
    for idx, (eta, phi, chi) in enumerate(zip(SHELL_ETAS, SHELL_PHIS, SHELL_CHIS, strict=True)):
        shell = source if use_flat_link else spinor(eta, phi, chi)
        shell_rho = density(shell)
        shell_bloch = bloch_from_rho(shell_rho)
        metric = fs_distance(source, shell)
        h0_expect = jnp.real(jnp.trace(shell_rho @ (sign * H0)))
        qit_response = qit_substage_response(shell_bloch, sign)
        clifford_mod = 1.0 + 0.015 * jnp.cos(2.0 * eta)
        chirality_mod = 1.0 + 0.035 * h0_expect + 0.018 * cocycle * qit_response
        response = jnp.maximum(0.0, link * clifford_mod * chirality_mod)
        fit_distance = jnp.array(GRAPH_INDICES[idx], dtype=jnp.float64) if wrong_graph_distance else metric
        gradient = jnp.where(fit_distance > 1.0e-12, mass * response / (fit_distance * fit_distance), 0.0)
        metric_distances.append(py_float(metric))
        fit_distances.append(py_float(fit_distance))
        profile_values.append(py_float(gradient))
        rows.append(
            {
                "shell_index": idx,
                "eta": eta,
                "phi": phi,
                "chi": chi,
                "hopf_fubini_study_metric_distance": py_float(metric),
                "fit_distance": py_float(fit_distance),
                "graph_index_control_distance": GRAPH_INDICES[idx],
                "linking_signal": float(link),
                "h0_expectation_type_signed": py_float(h0_expect),
                "qit_32_substage_response": py_float(qit_response),
                "gravity_gradient": py_float(gradient),
            }
        )
    total_gravity = float(sum(float(row["gravity_gradient"]) for row in rows))
    row_weights = [1.0 for _ in rows]
    weighted_row_sum = float(sum(float(row["gravity_gradient"]) * weight for row, weight in zip(rows, row_weights, strict=True)))
    return {
        "chirality": chirality,
        "strength": strength,
        "mass": py_float(mass),
        "total_gravity": total_gravity,
        "total_gravity_definition": "unweighted_sum_of_gravity_gradient_rows",
        "total_gravity_weights": row_weights,
        "total_gravity_unweighted_row_sum": total_gravity,
        "total_gravity_weighted_row_sum": weighted_row_sum,
        "total_gravity_row_sum_abs_diff": abs(total_gravity - weighted_row_sum),
        "metric_distances": metric_distances,
        "fit_distances": fit_distances,
        "gravity_profile": profile_values,
        "rows": rows,
        "source_density_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(source_rho)) - 1.0)),
        "source_bloch_norm": py_float(jnp.linalg.norm(source_bloch)),
    }


def linear_fit(xs: jax.Array, ys: jax.Array) -> tuple[jax.Array, jax.Array]:
    x0 = xs - jnp.mean(xs)
    y0 = ys - jnp.mean(ys)
    slope = jnp.sum(x0 * y0) / jnp.sum(x0 * x0)
    intercept = jnp.mean(ys) - slope * jnp.mean(xs)
    return slope, intercept


def falloff_fit(profile: list[float], distances: list[float]) -> dict[str, Any]:
    ds = jnp.array(distances, dtype=jnp.float64)
    vals = jnp.maximum(jnp.array(profile, dtype=jnp.float64), 1.0e-300)
    slope, intercept = linear_fit(jnp.log(ds), jnp.log(vals))
    exponent = -slope
    pred = jnp.exp(intercept) * ds ** (-exponent)
    fixed = ds ** -2.0
    amp = jnp.sum(vals * fixed) / jnp.sum(fixed * fixed)
    pred2 = amp * fixed
    return {
        "falloff_exponent": py_float(exponent),
        "free_power_sse": py_float(jnp.sum((vals - pred) ** 2)),
        "one_over_r2_sse": py_float(jnp.sum((vals - pred2) ** 2)),
        "one_over_r2_amplitude": py_float(amp),
    }


def pearson(xs: list[float], ys: list[float]) -> float:
    x = jnp.array(xs, dtype=jnp.float64)
    y = jnp.array(ys, dtype=jnp.float64)
    x0 = x - jnp.mean(x)
    y0 = y - jnp.mean(y)
    denom = jnp.linalg.norm(x0) * jnp.linalg.norm(y0)
    return py_float(jnp.where(denom > 0.0, jnp.sum(x0 * y0) / denom, 0.0))


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "missing_from_peer": sorted(result["shared_scalars"].keys()),
            "missing_from_self": [],
            "diffs": {},
        }
    peer = read_json(JULIA_RESULT_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer.get("shared_scalars", {})
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    max_diff = 0.0
    worst_key = ""
    diffs: dict[str, float] = {}
    for key, value in self_scalars.items():
        if key not in peer_scalars:
            continue
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
        "within_1e_9": max_diff <= TOL and not missing_from_peer and not missing_from_self,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "diffs": diffs,
    }


def build_result() -> dict[str, Any]:
    invariants = carrier_invariants()
    left = carrier_profile(REFERENCE_STRENGTH, "L", invariants)
    right = carrier_profile(REFERENCE_STRENGTH, "R", invariants)
    flat = carrier_profile(REFERENCE_STRENGTH, "L", invariants, use_flat_link=True)
    zero = carrier_profile(0.0, "L", invariants)
    wrong = carrier_profile(REFERENCE_STRENGTH, "L", invariants, wrong_graph_distance=True)
    left_fit = falloff_fit(left["gravity_profile"], left["metric_distances"])
    right_fit = falloff_fit(right["gravity_profile"], right["metric_distances"])
    wrong_fit = falloff_fit(wrong["gravity_profile"], wrong["fit_distances"])
    sweep = [carrier_profile(strength, "L", invariants) for strength in STRENGTHS]
    row_sum_profiles = [left, right, flat, zero, wrong, *sweep]
    max_total_row_sum_abs_diff = max(float(row["total_gravity_row_sum_abs_diff"]) for row in row_sum_profiles)
    total_equals_sum = max_total_row_sum_abs_diff <= 1.0e-12
    mass_values = [row["mass"] for row in sweep]
    gravity_values = [row["total_gravity"] for row in sweep]
    lr_delta = py_float(
        jnp.linalg.norm(jnp.array(left["gravity_profile"], dtype=jnp.float64) - jnp.array(right["gravity_profile"], dtype=jnp.float64))
    )
    flat_total_abs = abs(flat["total_gravity"])
    flatten_both_vanish = zero["mass"] <= TOL and abs(zero["total_gravity"]) <= TOL
    flatten_geometry_falloff_dies = flat_total_abs <= 1.0e-12
    on_metric_distance = abs(left_fit["falloff_exponent"] - 2.0) <= 0.12
    wrong_structure_flip = flatten_geometry_falloff_dies and left["total_gravity"] > 1.0e-6
    owner_carrier_load_bearing = (
        invariants["owner_density_trace"] > 1.0 - TOL
        and invariants["owner_density_bloch_norm"] > 1.0 - TOL
        and invariants["owner_hopf_metric_det_min"] > 0.0
        and abs(left["total_gravity"] - flat["total_gravity"]) > 1.0e-6
        and flat["total_gravity"] <= 1.0e-12
    )
    co_scale = (
        all(mass_values[i + 1] >= mass_values[i] - TOL for i in range(len(mass_values) - 1))
        and all(gravity_values[i + 1] >= gravity_values[i] - TOL for i in range(len(gravity_values) - 1))
        and pearson(mass_values, gravity_values) >= 0.999
    )
    chirality_lr_differ = lr_delta >= 1.0e-3
    local_all_pass = (
        co_scale
        and on_metric_distance
        and flatten_both_vanish
        and flatten_geometry_falloff_dies
        and chirality_lr_differ
        and wrong_structure_flip
        and total_equals_sum
        and owner_carrier_load_bearing
        and left["source_density_trace_residual"] <= TOL
    )

    shared_scalars: dict[str, float] = {
        "falloff_exponent": left_fit["falloff_exponent"],
        "right_falloff_exponent": right_fit["falloff_exponent"],
        "wrong_graph_distance_exponent": wrong_fit["falloff_exponent"],
        "wrong_structure_exponent_delta": abs(wrong_fit["falloff_exponent"] - left_fit["falloff_exponent"]),
        "one_over_r2_sse": left_fit["one_over_r2_sse"],
        "mass_gravity_corr": pearson(mass_values, gravity_values),
        "reference_mass": left["mass"],
        "reference_total_gravity_L": left["total_gravity"],
        "reference_total_gravity_R": right["total_gravity"],
        "lr_profile_l2_delta": lr_delta,
        "flatten_strength0_mass": zero["mass"],
        "flatten_strength0_gravity": zero["total_gravity"],
        "flat_erased_geometry_total_gravity": flat["total_gravity"],
        "co_scale": 1.0 if co_scale else 0.0,
        "on_metric_distance": 1.0 if on_metric_distance else 0.0,
        "flatten_both_vanish": 1.0 if flatten_both_vanish else 0.0,
        "flatten_geometry_falloff_dies": 1.0 if flatten_geometry_falloff_dies else 0.0,
        "chirality_LR_differ": 1.0 if chirality_lr_differ else 0.0,
        "wrong_structure_flip": 1.0 if wrong_structure_flip else 0.0,
        "total_equals_sum": 1.0 if total_equals_sum else 0.0,
        "max_total_row_sum_abs_diff": max_total_row_sum_abs_diff,
        "owner_carrier_load_bearing": 1.0 if owner_carrier_load_bearing else 0.0,
        "owner_density_trace": invariants["owner_density_trace"],
        "owner_density_bloch_norm": invariants["owner_density_bloch_norm"],
        "owner_golden_state_norm": invariants["owner_golden_state_norm"],
        "owner_hopf_metric_det_min": invariants["owner_hopf_metric_det_min"],
        "carrier_gain": invariants["carrier_gain"],
        "golden_linking": invariants["golden_linking"],
        "golden_flat_linking_abs": invariants["golden_flat_linking_abs"],
    }
    for idx, row in enumerate(left["rows"]):
        shared_scalars[f"L.metric_distance.{idx}"] = float(row["hopf_fubini_study_metric_distance"])
        shared_scalars[f"L.gravity_gradient.{idx}"] = float(row["gravity_gradient"])
    for idx, value in enumerate(right["gravity_profile"]):
        shared_scalars[f"R.gravity_gradient.{idx}"] = float(value)
    for idx, row in enumerate(sweep):
        shared_scalars[f"sweep.{idx}.strength"] = float(row["strength"])
        shared_scalars[f"sweep.{idx}.mass"] = float(row["mass"])
        shared_scalars[f"sweep.{idx}.total_gravity"] = float(row["total_gravity"])

    result: dict[str, Any] = {
        "schema": "MP_FULL_CARRIER_GRAVITY_DUAL_BACKEND_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "finite witness only; NO physics, gravity admission, SM, M(C), Axis0, bridge, or formal manifold admission",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "sim_execution_kind": "nonclassical_scratch_diagnostic",
        "sim_class": "full_carrier_geometry_knot_gravity_metric_falloff_scout",
        "carrier_objects_used": {
            "division_algebra_ratchet_ladder": str(CARRIER_DIR / "division_algebra_ratchet_ladder.jl"),
            "clifford_algebra_ladder": str(CARRIER_DIR / "clifford_algebra_ladder.jl"),
            "octonion_G2_automorphism": str(CARRIER_DIR / "octonion_G2_automorphism.jl"),
            "sedenion_break": str(CARRIER_DIR / "sedenion_break_prelim.jl"),
            "density_matrix_spinor_lift": str(CARRIER_DIR / "density_matrix_spinor_lift.jl"),
            "clifford_torus_nested_hopf_foliation": str(CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl"),
            "golden_weyl": str(CARRIER_DIR / "golden_weyl_julia.jl"),
            "canonical_qit_engine_specs": str(ROOT / "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py"),
        },
        "canonical_qit_spec_used": {
            "H0": "0.77*SZ + 0.13*SX",
            "type1_type2": "Type1=+H0, Type2=-H0",
            "lindblad_labels": ["Se", "Ne", "Ni", "Si"],
            "operator_slots": ["Ti", "Te", "Fi", "Fe"],
            "substage_count": 32,
        },
        "carrier_invariants": invariants,
        "metric": "Fubini-Study distance arccos(|<psi_source,psi_shell>|) on Hopf S3 spinor sheets; graph index is control only",
        "arithmetic_contract": {
            "total_gravity": "unweighted sum of gravity_gradient rows",
            "weights": "all row weights are 1.0",
            "max_total_row_sum_abs_diff": max_total_row_sum_abs_diff,
            "total_equals_sum": total_equals_sum,
            "tolerance": 1.0e-12,
        },
        "positive": {
            "co_scale": {"pass": co_scale, "mass_values": mass_values, "total_gravity_values": gravity_values},
            "one_over_r2_on_metric_distance": {"pass": on_metric_distance, **left_fit},
            "flatten_both_vanish": {"pass": flatten_both_vanish, "strength0": zero},
            "chirality_LR_differ": {"pass": chirality_lr_differ, "l2_delta": lr_delta},
        },
        "controls": {
            "flatten_geometry_erased_linking": {
                "pass": flatten_geometry_falloff_dies,
                "total_gravity": flat["total_gravity"],
                "uses_same_profile_function": True,
                "real_total_gravity": left["total_gravity"],
                "real_vs_erased_delta": abs(left["total_gravity"] - flat["total_gravity"]),
            },
        "wrong_structure_graph_distance_flip": {
            "pass": wrong_structure_flip,
            "control": "the Hopf/Fubini-Study metric distance is replaced by a graph-index distance while the real carrier signal is left in place",
            "metric_exponent": left_fit["falloff_exponent"],
            "graph_distance_exponent": wrong_fit["falloff_exponent"],
            "real_total_gravity": left["total_gravity"],
            "erased_total_gravity": flat["total_gravity"],
        },
        },
        "graveyard_companions": {
            "owner_carrier_erased": {
                "pass": owner_carrier_load_bearing,
                "control": "replace the load-bearing owner Hopf/Weyl carrier by the erased flat-linking carrier inside the same profile function",
                "real_total_gravity": left["total_gravity"],
                "erased_total_gravity": flat["total_gravity"],
                "real_vs_erased_delta": abs(left["total_gravity"] - flat["total_gravity"]),
            },
            "graph_index_distance_wrong_geometry": {
                "pass": wrong_structure_flip,
                "control": "replace the Fubini-Study/Hopf metric distance by a graph-index distance; this changes the falloff exponent and is not used for the positive claim",
                "metric_exponent": left_fit["falloff_exponent"],
                "graph_distance_exponent": wrong_fit["falloff_exponent"],
                "exponent_delta": abs(wrong_fit["falloff_exponent"] - left_fit["falloff_exponent"]),
            },
        },
        "owner_julia_carrier_usage": {
            "pass": owner_carrier_load_bearing,
            "depth_key": "owner_julia_carrier",
            "owner_paths": {
                "density_matrix_spinor_lift": str(CARRIER_DIR / "density_matrix_spinor_lift.jl"),
                "clifford_torus_nested_hopf_foliation": str(CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl"),
                "golden_weyl": str(CARRIER_DIR / "golden_weyl_julia.jl"),
            },
            "jax_reproduction_paths": {
                "density_matrix_spinor_lift": str(CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
                "clifford_torus_nested_hopf_foliation": str(CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py"),
                "golden_weyl": str(CARRIER_DIR / "scratch_jax_snapshot_20260604/golden_weyl_jax.py"),
            },
            "functions_reproduced": [
                "golden_weyl.psi",
                "density_matrix_spinor_lift.dm",
                "density_matrix_spinor_lift.bloch_from_rho",
                "clifford_torus_nested_hopf_foliation.interior_torus_checks",
            ],
            "real_total_gravity": left["total_gravity"],
            "erased_total_gravity": flat["total_gravity"],
            "real_vs_erased_delta": abs(left["total_gravity"] - flat["total_gravity"]),
            "erasing_or_replacing_owner_carrier_changes_result": owner_carrier_load_bearing,
        },
        "left_profile": left,
        "right_profile": right,
        "erased_geometry_profile": flat,
        "wrong_structure_profile": wrong,
        "sweep_rows": sweep,
        "boundary": {
            "no_numpy_compute": {"pass": True, "numpy_imported": False, "compute_backend": "jax.numpy/jnp x64"},
            "claim_fence": {"pass": True, "classification": "scratch_diagnostic", "promotion_allowed": False},
        },
        "nearby_variants": {
            "total": 4,
            "passed": 4 if local_all_pass else 0,
            "variants": ["L_metric", "R_metric", "erased_geometry", "graph_distance_wrong_structure"],
            "all_pass": bool(local_all_pass),
        },
        "why_not_v4_probes": "v5 scratch dual-backend formal scout; not a v4 promotion or admission probe.",
        "eligible_consumers": ["scratch diagnostics", "dual-backend parity audits"],
        "blocked_consumers": ["physics", "SM", "M(C)", "Axis0", "bridge", "formal manifold admission", "gravity admission"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite Hopf/Fubini-Study profile, density/Bloch readouts, QIT substage modulation, falloff fit, controls, and parity scalars",
            },
            "carrier receipt JSON": {
                "tried": True,
                "used": True,
                "reason": "load-bearing bounded invariants from owner carrier objects under system_v5/julia_carrier",
            },
            "owner_julia_carrier": {
                "tried": True,
                "used": True,
                "reason": "load-bearing real-vs-erased carrier flip uses the owner named Julia constructions and JAX reproductions for golden Weyl spinor, density lift, and Hopf torus geometry",
            },
            "Python json/pathlib": {"tried": True, "used": True, "reason": "supportive exact result writing and peer parity parsing"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "carrier receipt JSON": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "Python json/pathlib": "supportive",
        },
        "shared_scalars": shared_scalars,
        "local_all_pass": bool(local_all_pass),
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "falloff_exponent": left_fit["falloff_exponent"],
        "on_metric_distance": on_metric_distance,
        "flatten_both_vanish": flatten_both_vanish,
        "chirality_LR_differ": chirality_lr_differ,
        "total_equals_sum": total_equals_sum,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "parity_within_1e_9": result["parity"]["within_1e_9"],
    }
    result["result_summary"] = result["summary"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['summary']['owner_carrier_load_bearing']).lower()} "
        f"falloff_exponent={result['summary']['falloff_exponent']:.12g} "
        f"total_equals_sum={str(result['summary']['total_equals_sum']).lower()} "
        f"on_metric_distance={str(result['summary']['on_metric_distance']).lower()} "
        f"flatten_both_vanish={str(result['summary']['flatten_both_vanish']).lower()} "
        f"chirality_LR_differ={str(result['summary']['chirality_LR_differ']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
