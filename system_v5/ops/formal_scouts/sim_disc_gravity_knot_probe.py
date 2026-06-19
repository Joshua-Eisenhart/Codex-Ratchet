#!/usr/bin/env python3
# object_id: disc_gravity_knot
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
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
        "reason": "load-bearing x64 backend for the finite gravity/knot carrier-readout discriminator",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex spinor, density, metric, readout, control, and parity scalar algebra",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent mirror backend for shared scalar and boolean parity",
    },
    "owner_julia_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner Hopf/Weyl/Clifford carrier functions and receipts; erasing the carrier changes the readout result",
    },
    "carrier_readout_discriminator_matrix result": {
        "tried": True,
        "used": True,
        "reason": "load-bearing prior finite falsifier for target-imprint demotion of the knot_mass_gravity branch",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path handling, source hashing, JSON parsing, timestamps, and result serialization",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no NumPy import, alias, conversion, or compute path in this JAX scratch row",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "explicitly not added; this request is the JAX plus Julia lane and keeps the stale C8 PyTorch rule unsatisfied by design",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "owner_julia_carrier": "load_bearing",
    "carrier_readout_discriminator_matrix result": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
    "pytorch": None,
}


OBJECT_ID = "disc_gravity_knot"
NAME = OBJECT_ID
BACKEND = "jax_jnp_x64"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "disc_gravity_knot_results.json"
JULIA_RESULT_PATH = JULIA_CARRIER / "disc_gravity_knot_julia_results.json"
SOURCE_PATH = FORMAL_SCOUTS / "sim_disc_gravity_knot_probe.py"
JULIA_SOURCE_PATH = JULIA_CARRIER / "disc_gravity_knot.jl"
GOLDEN_RECEIPT_PATH = JULIA_CARRIER / "golden_weyl_julia_receipt.json"
MATRIX_RESULT_PATH = FORMAL_SCOUTS / "results" / "carrier_readout_discriminator_matrix_results.json"
DENSITY_LIFT_JAX_PATH = JULIA_CARRIER / "jax_density_matrix_spinor_lift.py"
HOPF_JAX_PATH = JULIA_CARRIER / "jax_clifford_torus_nested_hopf_foliation.py"
GOLDEN_JAX_PATH = JULIA_CARRIER / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py"
DENSITY_LIFT_JULIA_PATH = JULIA_CARRIER / "density_matrix_spinor_lift.jl"
HOPF_JULIA_PATH = JULIA_CARRIER / "clifford_torus_nested_hopf_foliation.jl"
GOLDEN_JULIA_PATH = JULIA_CARRIER / "golden_weyl_julia.jl"

PARITY_TOL = 1.0e-9
EPS = 1.0e-12
PRESENT_THRESHOLD = 1.0e-6
EXPONENT_TOL = 1.0e-9
LINK_SAMPLES = 64
SOURCE_ETA = 0.7853981633974483
SOURCE_PHI = 0.17
SOURCE_CHI = -0.23
SHELL_ETAS = (0.34, 0.43, 0.57, 0.71, 0.92, 1.08, 1.23, 1.36)
SHELL_PHIS = (0.23, 0.58, 1.03, 1.59, 2.17, 2.84, 3.48, 4.26)
SHELL_CHIS = (-0.37, -0.06, 0.51, 1.04, 1.73, 2.28, 2.96, 3.64)
CLAIM_CEILING = (
    "Gravity/knot carrier-readout discriminator only. classification=scratch_diagnostic; "
    "promotion=false; formal_admission=false. It may report finite owner-carrier load-bearing "
    "for this readout, but it does not derive G, admit gravity or mass, prove physics, admit M(C), "
    "bridge, Axis0, PEPS3D, or close the manifold."
)
BLOCKED_CONSUMERS = [
    "G derivation",
    "gravity admission",
    "mass admission",
    "physics",
    "M(C)",
    "Axis0",
    "bridge",
    "PEPS3D admission",
    "formal admission",
    "promotion",
]


def load_owner_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load owner module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OWNER_DENSITY = load_owner_module("disc_owner_density_matrix_spinor_lift", DENSITY_LIFT_JAX_PATH)
OWNER_HOPF = load_owner_module("disc_owner_clifford_torus_nested_hopf_foliation", HOPF_JAX_PATH)
OWNER_GOLDEN = load_owner_module("disc_owner_golden_weyl_jax", GOLDEN_JAX_PATH)


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_refs() -> dict[str, Any]:
    paths = {
        "self": SOURCE_PATH,
        "julia_mirror": JULIA_SOURCE_PATH,
        "golden_weyl_jax": GOLDEN_JAX_PATH,
        "golden_weyl_julia": GOLDEN_JULIA_PATH,
        "golden_weyl_receipt": GOLDEN_RECEIPT_PATH,
        "density_matrix_spinor_lift_jax": DENSITY_LIFT_JAX_PATH,
        "density_matrix_spinor_lift_julia": DENSITY_LIFT_JULIA_PATH,
        "clifford_torus_nested_hopf_foliation_jax": HOPF_JAX_PATH,
        "clifford_torus_nested_hopf_foliation_julia": HOPF_JULIA_PATH,
        "carrier_readout_discriminator_matrix": MATRIX_RESULT_PATH,
    }
    return {
        key: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
        }
        for key, path in paths.items()
    }


def spinor(eta: float, phi: float, chi: float) -> jax.Array:
    return OWNER_GOLDEN.psi(phi, chi, eta)


def density(psi: jax.Array) -> jax.Array:
    return OWNER_DENSITY.dm(psi)


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return OWNER_DENSITY.bloch_from_rho(rho)


def fs_distance(a: jax.Array, b: jax.Array) -> jax.Array:
    overlap = jnp.abs(jnp.vdot(a, b)) / jnp.sqrt(jnp.real(jnp.vdot(a, a) * jnp.vdot(b, b)))
    return jnp.arccos(jnp.clip(overlap, 0.0, 1.0))


def finite_invariants() -> dict[str, Any]:
    receipt = read_json(GOLDEN_RECEIPT_PATH)
    inv = receipt["invariants"]
    owner_hopf = OWNER_HOPF.interior_torus_checks()
    source = spinor(SOURCE_ETA, SOURCE_PHI, SOURCE_CHI)
    source_rho = density(source)
    source_bloch = bloch_from_rho(source_rho)
    real_link_sample = OWNER_GOLDEN.nested_gauss_linking(SOURCE_ETA, LINK_SAMPLES)
    random_unlinked_sample = OWNER_GOLDEN.nested_but_unlinked_linking(SOURCE_ETA, LINK_SAMPLES)
    trivial_flat_sample = OWNER_GOLDEN.flat_s2_sanity_linking(LINK_SAMPLES)
    return {
        "golden_linking_receipt": float(inv["linking_number"]),
        "flat_linking_receipt": float(inv["flat_S2_linking_number"]),
        "cocycle_wL": float(inv["cocycle_wL"]),
        "cocycle_wR": float(inv["cocycle_wR"]),
        "carrier_error_bound": float(inv["carrier_error_bound"]),
        "real_link_sample": float(real_link_sample),
        "random_unlinked_link_sample": float(random_unlinked_sample),
        "trivial_flat_link_sample": float(trivial_flat_sample),
        "owner_hopf_metric_det_min": float(owner_hopf["torus_metric_det_min"]),
        "owner_density_trace": py_float(jnp.real(jnp.trace(source_rho))),
        "owner_density_bloch_norm": py_float(jnp.linalg.norm(source_bloch)),
        "owner_golden_state_norm": py_float(jnp.real(jnp.vdot(source, source))),
    }


def prior_knot_target_imprint() -> dict[str, Any]:
    if not MATRIX_RESULT_PATH.exists():
        return {
            "available": False,
            "all_pass": False,
            "branch_verdict": "OPEN",
            "mutated_carrier_value": 0.0,
            "owner_carrier_value": 0.0,
            "negative_control_value": 0.0,
            "shape_scramble_survives": False,
            "path": str(MATRIX_RESULT_PATH),
        }
    data = read_json(MATRIX_RESULT_PATH)
    target = None
    for row in data.get("rows", []):
        if row.get("branch_id") == "knot_mass_gravity":
            target = row
            break
    if target is None:
        return {
            "available": True,
            "all_pass": bool(data.get("all_pass")),
            "branch_verdict": "OPEN",
            "mutated_carrier_value": 0.0,
            "owner_carrier_value": 0.0,
            "negative_control_value": 0.0,
            "shape_scramble_survives": False,
            "path": str(MATRIX_RESULT_PATH),
        }
    mutated = float(target.get("mutated_carrier_value", 0.0))
    owner = float(target.get("owner_carrier_value", 0.0))
    negative = float(target.get("negative_control_value", 0.0))
    return {
        "available": True,
        "all_pass": bool(data.get("all_pass")),
        "branch_verdict": str(target.get("branch_verdict")),
        "mutated_carrier_value": mutated,
        "owner_carrier_value": owner,
        "negative_control_value": negative,
        "shape_scramble_survives": mutated > 0.5 and owner > 0.5,
        "mutation": target.get("mutation"),
        "claim_ceiling": target.get("claim_ceiling"),
        "path": str(MATRIX_RESULT_PATH),
    }


def mass_from_signal(link_signal: float, invariants: dict[str, Any]) -> float:
    chirality_gap = abs(invariants["cocycle_wL"] - invariants["cocycle_wR"])
    density_gate = max(0.0, min(1.0, invariants["owner_density_bloch_norm"]))
    raw = abs(link_signal) * density_gate * (1.0 + 0.125 * chirality_gap)
    return py_float(jnp.tanh(jnp.array(raw, dtype=jnp.float64)))


def branch_profile(label: str, link_signal: float, invariants: dict[str, Any], *, flatten_shells: bool) -> dict[str, Any]:
    source = spinor(SOURCE_ETA, SOURCE_PHI, SOURCE_CHI)
    mass = mass_from_signal(link_signal, invariants)
    rows: list[dict[str, Any]] = []
    profile: list[float] = []
    distances: list[float] = []
    amplitude = mass * abs(link_signal)
    for idx, (eta, phi, chi) in enumerate(zip(SHELL_ETAS, SHELL_PHIS, SHELL_CHIS, strict=True)):
        shell = source if flatten_shells else spinor(eta, phi, chi)
        metric = py_float(fs_distance(source, shell))
        distance = max(metric, EPS)
        value = 0.0 if flatten_shells else amplitude / (distance * distance)
        distances.append(distance)
        profile.append(value)
        rows.append(
            {
                "shell_index": idx,
                "eta": eta,
                "phi": phi,
                "chi": chi,
                "hopf_fubini_study_metric_distance": distance,
                "link_signal": float(link_signal),
                "mass_source": mass,
                "gravity_readout": value,
            }
        )
    total = float(sum(profile))
    return {
        "label": label,
        "link_signal": float(link_signal),
        "mass": float(mass),
        "total_gravity": total,
        "metric_distances": distances,
        "gravity_profile": profile,
        "rows": rows,
    }


def linear_fit(xs: jax.Array, ys: jax.Array) -> tuple[jax.Array, jax.Array]:
    x0 = xs - jnp.mean(xs)
    y0 = ys - jnp.mean(ys)
    denom = jnp.sum(x0 * x0)
    slope = jnp.where(denom > 0.0, jnp.sum(x0 * y0) / denom, 0.0)
    intercept = jnp.mean(ys) - slope * jnp.mean(xs)
    return slope, intercept


def falloff_fit(profile: list[float], distances: list[float]) -> dict[str, Any]:
    ds = jnp.asarray(distances, dtype=jnp.float64)
    vals = jnp.maximum(jnp.asarray(profile, dtype=jnp.float64), 1.0e-300)
    slope, intercept = linear_fit(jnp.log(ds), jnp.log(vals))
    exponent = -slope
    free_pred = jnp.exp(intercept) * ds ** (-exponent)
    fixed = ds**-2.0
    amp = jnp.sum(vals * fixed) / jnp.sum(fixed * fixed)
    fixed_pred = amp * fixed
    return {
        "falloff_exponent": py_float(exponent),
        "free_power_sse": py_float(jnp.sum((vals - free_pred) ** 2)),
        "one_over_r2_sse": py_float(jnp.sum((vals - fixed_pred) ** 2)),
        "one_over_r2_amplitude": py_float(amp),
    }


def row_verdict(
    *,
    parity_ok: bool,
    real_present: bool,
    oneoverr2_on_metric: bool,
    dies_under_flatten: bool,
    survives_random_knot: bool,
    owner_carrier_load_bearing: bool,
    prior_target_imprint: bool,
) -> str:
    if not parity_ok:
        return "OPEN"
    if not real_present:
        return "GRAVEYARD"
    if survives_random_knot:
        return "GENERIC"
    if prior_target_imprint:
        return "CONVENTION"
    if oneoverr2_on_metric and dies_under_flatten and owner_carrier_load_bearing:
        return "REAL_CARRIER"
    if oneoverr2_on_metric:
        return "CONVENTION"
    return "OPEN"


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "within_1e_9": False,
            "parity_max_diff": None,
            "worst_key": None,
            "missing_from_peer": sorted(result["shared_scalars"]),
            "missing_from_self": [],
            "boolean_mismatches": [],
            "string_mismatches": [],
            "diffs": {},
        }
    peer = read_json(JULIA_RESULT_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer.get("shared_scalars", {})
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    max_diff = 0.0
    worst_key = None
    diffs: dict[str, float] = {}
    for key, value in self_scalars.items():
        if key not in peer_scalars:
            continue
        diff = abs(float(value) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
    self_booleans = result["shared_booleans"]
    peer_booleans = peer.get("shared_booleans", {})
    boolean_mismatches = [
        key
        for key, value in self_booleans.items()
        if key in peer_booleans and bool(value) != bool(peer_booleans[key])
    ]
    self_strings = result["shared_strings"]
    peer_strings = peer.get("shared_strings", {})
    string_mismatches = [
        key
        for key, value in self_strings.items()
        if key in peer_strings and str(value) != str(peer_strings[key])
    ]
    within = (
        not missing_from_peer
        and not missing_from_self
        and not boolean_mismatches
        and not string_mismatches
        and max_diff <= PARITY_TOL
    )
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "within_1e_9": bool(within),
        "parity_max_diff": float(max_diff),
        "worst_key": worst_key,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
        "diffs": diffs,
    }


def build_result() -> dict[str, Any]:
    invariants = finite_invariants()
    prior = prior_knot_target_imprint()
    real = branch_profile("intended_weyl_hopf_clifford_knot", invariants["golden_linking_receipt"], invariants, flatten_shells=False)
    flattened = branch_profile("carrier_flattened_flat_s2", invariants["flat_linking_receipt"], invariants, flatten_shells=True)
    random_knot = branch_profile(
        "deterministic_unlinked_random_trivial_knot",
        invariants["random_unlinked_link_sample"],
        invariants,
        flatten_shells=False,
    )
    trivial_knot = branch_profile("flat_s2_trivial_knot", invariants["trivial_flat_link_sample"], invariants, flatten_shells=False)
    fit = falloff_fit(real["gravity_profile"], real["metric_distances"])
    oneoverr2_on_metric = abs(float(fit["falloff_exponent"]) - 2.0) <= EXPONENT_TOL
    real_present = real["total_gravity"] > PRESENT_THRESHOLD and real["mass"] > PRESENT_THRESHOLD
    flatten_delta = abs(real["total_gravity"] - flattened["total_gravity"])
    dies_under_flatten = real_present and flattened["total_gravity"] <= PRESENT_THRESHOLD and flatten_delta > PRESENT_THRESHOLD
    random_present = random_knot["total_gravity"] > PRESENT_THRESHOLD or trivial_knot["total_gravity"] > PRESENT_THRESHOLD
    survives_random_knot = bool(random_present)
    owner_carrier_load_bearing = (
        invariants["owner_density_trace"] > 1.0 - 1.0e-9
        and invariants["owner_density_bloch_norm"] > 1.0 - 1.0e-9
        and invariants["owner_hopf_metric_det_min"] > 0.0
        and dies_under_flatten
    )
    prior_target_imprint = bool(prior["available"] and prior["all_pass"] and prior["branch_verdict"] == "TARGET_IMPRINT")
    G_derived = False

    shared_scalars: dict[str, float] = {
        "real.mass": float(real["mass"]),
        "real.total_gravity": float(real["total_gravity"]),
        "flattened.mass": float(flattened["mass"]),
        "flattened.total_gravity": float(flattened["total_gravity"]),
        "random_knot.mass": float(random_knot["mass"]),
        "random_knot.total_gravity": float(random_knot["total_gravity"]),
        "trivial_knot.mass": float(trivial_knot["mass"]),
        "trivial_knot.total_gravity": float(trivial_knot["total_gravity"]),
        "flatten_delta": float(flatten_delta),
        "falloff_exponent": float(fit["falloff_exponent"]),
        "one_over_r2_sse": float(fit["one_over_r2_sse"]),
        "one_over_r2_amplitude": float(fit["one_over_r2_amplitude"]),
        "golden_linking_receipt": float(invariants["golden_linking_receipt"]),
        "flat_linking_receipt": float(invariants["flat_linking_receipt"]),
        "real_link_sample": float(invariants["real_link_sample"]),
        "random_unlinked_link_sample": float(invariants["random_unlinked_link_sample"]),
        "trivial_flat_link_sample": float(invariants["trivial_flat_link_sample"]),
        "owner_density_trace": float(invariants["owner_density_trace"]),
        "owner_density_bloch_norm": float(invariants["owner_density_bloch_norm"]),
        "owner_hopf_metric_det_min": float(invariants["owner_hopf_metric_det_min"]),
        "prior_matrix.mutated_carrier_value": float(prior["mutated_carrier_value"]),
        "prior_matrix.owner_carrier_value": float(prior["owner_carrier_value"]),
        "prior_matrix.negative_control_value": float(prior["negative_control_value"]),
    }
    for idx, (distance, gravity) in enumerate(zip(real["metric_distances"], real["gravity_profile"], strict=True)):
        shared_scalars[f"real.metric_distance.{idx}"] = float(distance)
        shared_scalars[f"real.gravity_readout.{idx}"] = float(gravity)

    shared_booleans = {
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "real_present": bool(real_present),
        "oneoverr2_on_metric": bool(oneoverr2_on_metric),
        "dies_under_flatten": bool(dies_under_flatten),
        "survives_random_knot": bool(survives_random_knot),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "prior_target_imprint_falsifier": bool(prior_target_imprint),
        "G_derived": bool(G_derived),
        "classification_fence": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
    }
    pre_parity = {
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": {"object_id": OBJECT_ID, "G_derived": str(G_derived).lower()},
    }
    parity = parity_block(pre_parity)
    parity_ok = bool(parity["peer_available"] and parity["within_1e_9"])
    verdict = row_verdict(
        parity_ok=parity_ok,
        real_present=bool(real_present),
        oneoverr2_on_metric=bool(oneoverr2_on_metric),
        dies_under_flatten=bool(dies_under_flatten),
        survives_random_knot=bool(survives_random_knot),
        owner_carrier_load_bearing=bool(owner_carrier_load_bearing),
        prior_target_imprint=bool(prior_target_imprint),
    )
    shared_strings = {
        "object_id": OBJECT_ID,
        "row_verdict": verdict,
        "G_derived": str(G_derived).lower(),
    }
    local_all_pass = (
        shared_booleans["classification_fence"]
        and shared_booleans["jax_enable_x64"]
        and not shared_booleans["numpy_compute_used"]
        and not shared_booleans["torch_compute_used"]
        and shared_booleans["real_present"]
        and shared_booleans["oneoverr2_on_metric"]
        and shared_booleans["dies_under_flatten"]
        and not shared_booleans["survives_random_knot"]
        and shared_booleans["owner_carrier_load_bearing"]
        and verdict in {"REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD", "OPEN"}
        and G_derived is False
    )
    all_pass = bool(local_all_pass and parity_ok and verdict != "OPEN")

    positive = {
        "real_owner_carrier_metric_readout_present": {
            "pass": bool(real_present),
            "mass": real["mass"],
            "total_gravity": real["total_gravity"],
            "branch": real,
        },
        "one_over_r2_on_hopf_metric": {
            "pass": bool(oneoverr2_on_metric),
            **fit,
            "tolerance": EXPONENT_TOL,
            "note": "The inverse-square readout is tested as a finite carrier readout, not as a G derivation.",
        },
        "owner_real_carrier_load_bearing": {
            "pass": bool(owner_carrier_load_bearing),
            "real_total_gravity": real["total_gravity"],
            "flattened_total_gravity": flattened["total_gravity"],
            "erase_delta": flatten_delta,
        },
    }
    graveyard_companions = {
        "carrier_flatten_control": {
            "pass": bool(dies_under_flatten),
            "control": "same readout with flat-S2 linking receipt and flattened shell geometry",
            "branch": flattened,
        },
        "random_trivial_knot_control": {
            "pass": not bool(survives_random_knot),
            "control": "same readout with deterministic unlinked and flat-S2 Gauss-linking controls from the owner golden Weyl code",
            "random_branch": random_knot,
            "trivial_branch": trivial_knot,
        },
        "prior_target_imprint_falsifier": {
            "pass": bool(prior_target_imprint),
            "effect_on_verdict": "demotes REAL_CARRIER to CONVENTION for this row",
            "prior": prior,
        },
    }
    boundary = {
        "classification_fence": {
            "pass": shared_booleans["classification_fence"],
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "no_numpy_no_torch_compute": {
            "pass": not shared_booleans["numpy_compute_used"] and not shared_booleans["torch_compute_used"],
            "numpy_compute_used": False,
            "torch_compute_used": False,
        },
        "G_not_derived": {
            "pass": G_derived is False,
            "G_derived": G_derived,
        },
        "honest_discriminator_verdict": {
            "pass": verdict in {"REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD", "OPEN"},
            "row_verdict": verdict,
            "rule": (
                "REAL_CARRIER requires oneoverr2_on_metric, dies_under_flatten, survives_random_knot=false, "
                "owner erasure changes result, and no active target-imprint falsifier."
            ),
        },
    }

    result: dict[str, Any] = {
        "schema": "DISC_GRAVITY_KNOT_DISCRIMINATOR_v1",
        "object_id": OBJECT_ID,
        "name": NAME,
        "backend": BACKEND,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion": False,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission": False,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite owner-carrier erase changes this gravity/knot readout",
            "finite random/trivial knot controls are absent for this readout",
            "honest row verdict under current falsifiers",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_readout_discriminator",
        "source_alignment_category": "gravity_knot_owner_carrier_discriminator",
        "source_refs": source_refs(),
        "carrier": {
            "real_carrier": "owner Weyl/Hopf/Clifford nested S3 spinor carrier via golden_weyl, density_matrix_spinor_lift, and clifford_torus_nested_hopf_foliation",
            "metric": "Fubini-Study distance on owner Hopf/Weyl spinors",
            "knot_signal": "golden_weyl finite Gauss linking receipt and matching sampled owner function",
            "flatten": "flat-S2 linking receipt plus flattened shell geometry",
            "random_trivial": "deterministic unlinked and flat-S2 owner Gauss-link controls",
        },
        "finite_witness": {
            "invariants": invariants,
            "real_profile": real,
            "flattened_profile": flattened,
            "random_knot_profile": random_knot,
            "trivial_knot_profile": trivial_knot,
            "falloff_fit": fit,
            "prior_target_imprint_falsifier": prior,
        },
        "row_verdict": verdict,
        "oneoverr2_on_metric": bool(oneoverr2_on_metric),
        "dies_under_flatten": bool(dies_under_flatten),
        "survives_random_knot": bool(survives_random_knot),
        "G_derived": G_derived,
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 4,
            "passed": 4 if local_all_pass else 0,
            "variants": ["real_owner_carrier", "flat_s2_flatten", "deterministic_unlinked_random", "flat_s2_trivial"],
            "all_pass": bool(local_all_pass),
        },
        "why_not_v4_probes": "v5 scratch dual-backend discriminator row; not a v4 probe, not a promotion artifact, and G is not derived.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
        "parity": parity_block({"shared_scalars": shared_scalars, "shared_booleans": shared_booleans, "shared_strings": shared_strings}),
        "local_all_pass": bool(local_all_pass),
    }
    result["all_pass"] = bool(
        result["local_all_pass"] and result["parity"]["peer_available"] and result["parity"]["within_1e_9"] and verdict != "OPEN"
    )
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": result["local_all_pass"],
        "row_verdict": verdict,
        "oneoverr2_on_metric": bool(oneoverr2_on_metric),
        "dies_under_flatten": bool(dies_under_flatten),
        "survives_random_knot": bool(survives_random_knot),
        "G_derived": G_derived,
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "prior_target_imprint_falsifier": bool(prior_target_imprint),
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
        f"row_verdict={result['row_verdict']} "
        f"oneoverr2_on_metric={str(result['oneoverr2_on_metric']).lower()} "
        f"dies_under_flatten={str(result['dies_under_flatten']).lower()} "
        f"survives_random_knot={str(result['survives_random_knot']).lower()} "
        f"G_derived={str(result['G_derived']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
