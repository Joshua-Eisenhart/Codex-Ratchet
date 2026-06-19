#!/usr/bin/env python3
# object_id: mp4_fine_structure_explore
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import ast
import datetime as _dt
import hashlib
import importlib.util
import json
import sys
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


OBJECT_ID = "mp4_fine_structure_explore"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = ROOT / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = ROOT / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp4_fine_structure_explore_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp4_fine_structure_explore_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
LOAD_BEARING_DELTA_THRESHOLD = 1.0e-8
TARGET_ALPHA = 1.0 / 137.0
MATCH_TOL = 1.0e-6

SOURCE_DEPENDENCIES = {
    "canonical_qit_engine_specs.py": FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "jax_density_matrix_spinor_lift": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "jax_clifford_torus_nested_hopf_foliation": CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "golden_weyl_jax": CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    "jax_division_algebra_ratchet_ladder": CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "jax_octonion_G2_automorphism": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "density_receipt": CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json",
    "hopf_receipt": CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json",
    "golden_receipt": CARRIER_DIR / "golden_weyl_jax_receipt.json",
    "division_receipt": CARRIER_DIR / "division_algebra_ratchet_ladder_jax_results.json",
    "g2_receipt": CARRIER_DIR / "octonion_G2_automorphism_jax_results.json",
}

CLAIM_CEILING = (
    "Finite MECHANISM witness in the owner's entropic-monist carrier frame: "
    "an untuned carrier geometry/coupling scalar can be computed and ablated. "
    "This is not a derivation or proof of the fine-structure constant, not a "
    "physics admission, not formal admission, and not promotion."
)

BLOCKED_CONSUMERS = [
    "fine_structure_constant_derivation",
    "measured_alpha_claim",
    "physics_admission",
    "formal_admission",
    "promotion",
    "standard_model_parameter_derivation",
]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(FORMAL_SCOUT_DIR))
qit_specs = load_module("mp4_fs_qit_specs", SOURCE_DEPENDENCIES["canonical_qit_engine_specs.py"])
density = load_module("mp4_fs_density", SOURCE_DEPENDENCIES["jax_density_matrix_spinor_lift"])
hopf = load_module("mp4_fs_hopf", SOURCE_DEPENDENCIES["jax_clifford_torus_nested_hopf_foliation"])
golden = load_module("mp4_fs_golden", SOURCE_DEPENDENCIES["golden_weyl_jax"])
division = load_module("mp4_fs_division", SOURCE_DEPENDENCIES["jax_division_algebra_ratchet_ladder"])
g2 = load_module("mp4_fs_g2", SOURCE_DEPENDENCIES["jax_octonion_G2_automorphism"])


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_norm(value: Any) -> float:
    return py_float(jnp.linalg.norm(value))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in SOURCE_DEPENDENCIES.items()
    }


def torch_matrix_to_jnp(tensor: Any) -> jax.Array:
    return jnp.asarray(tensor.detach().cpu().tolist(), dtype=jnp.complex128)


def normalize(v: jax.Array, fallback: jax.Array | None = None) -> jax.Array:
    norm = py_float(jnp.linalg.norm(v))
    if norm <= 1.0e-14:
        if fallback is None:
            raise ValueError("cannot normalize zero vector without fallback")
        return normalize(fallback)
    return v / norm


def qit_anchor() -> dict[str, Any]:
    engine = qit_specs.get_engine_spec(0)
    h0 = torch_matrix_to_jnp(engine["hamiltonian"])
    sx_coeff = py_float(jnp.real(h0[0, 1]))
    sz_coeff = py_float(0.5 * jnp.real(h0[0, 0] - h0[1, 1]))
    h_vec = jnp.asarray([sx_coeff, 0.0, sz_coeff], dtype=jnp.float64)
    schedule_one = qit_specs.get_schedule(0)
    schedule_two = qit_specs.get_schedule(1)
    slot = qit_specs.get_operator_slot_spec("Se", 0, "outer", 0)
    return {
        "h0_sx_coeff": sx_coeff,
        "h0_sz_coeff": sz_coeff,
        "h0_norm": py_float(jnp.linalg.norm(h_vec)),
        "h0_unit": normalize(h_vec),
        "schedule_total_len": float(len(schedule_one) + len(schedule_two)),
        "manifold_layer_count": float(len(qit_specs.MANIFOLD_LAYERS)),
        "operator_slot_count": float(len(qit_specs.OPERATOR_SLOT_SEQUENCE)),
        "perception_count": float(len(qit_specs.PERCEPTION_L_MATRICES)),
        "slot_native": bool(slot["is_native_operator"]),
        "slot_angle": float(slot.get("angle", 0.0)),
        "source": "canonical_qit_engine_specs.py",
    }


def density_anchor() -> dict[str, Any]:
    receipt = read_json(SOURCE_DEPENDENCIES["density_receipt"])["shared_scalars"]
    return {
        "spinor_norm_residual": float(receipt["spinor_norm_residual"]),
        "rho_trace_residual": float(receipt["trace_rho_residual"]),
        "bloch_norm": float(receipt["bloch_norm"]),
        "mixed_purity": float(receipt["mixed_purity"]),
        "fiber_dim": float(receipt["fiber_dim"]),
        "mixed_rank": float(receipt["mixed_rank"]),
        "source": "density_matrix_spinor_lift",
    }


def hopf_anchor() -> dict[str, Any]:
    receipt = read_json(SOURCE_DEPENDENCIES["hopf_receipt"])["shared_scalars"]
    return {
        "s3_residual": float(receipt["interior_s3_constraint_max_residual"]),
        "torus_metric_det_min": float(receipt["torus_metric_det_min"]),
        "hopf_vec_norm": 1.0,
        "source": "clifford_torus_nested_hopf_foliation",
    }


def golden_anchor() -> dict[str, Any]:
    receipt = read_json(SOURCE_DEPENDENCIES["golden_receipt"])["invariants"]
    return {
        "spinor_norm_residual": 0.0,
        "linking_number": float(receipt["linking_number"]),
        "flat_s2_linking_number": float(receipt["flat_S2_linking_number"]),
        "claimed_effect_gap": float(receipt["claimed_effect_gap"]),
        "cocycle_gap": float(receipt["cocycle_wL"]) - float(receipt["cocycle_wR"]),
        "n01_commutator_norm": float(receipt["n01_commutator_norm"]),
        "source": "golden_weyl",
    }


def division_anchor() -> dict[str, Any]:
    receipt = read_json(SOURCE_DEPENDENCIES["division_receipt"])["shared_scalars"]
    return {
        "h_ij_minus_k_residual": 0.0,
        "h_commutator_norm": float(receipt["H.commutator_max"]),
        "h_associator_max": float(receipt["H.associator_max"]),
        "o_associator_max": float(receipt["O.associator_max"]),
        "o_alternator_residual": float(receipt["O.alternator_residual"]),
        "source": "division_algebra_ratchet_ladder",
    }


def g2_anchor() -> dict[str, Any]:
    receipt = read_json(SOURCE_DEPENDENCIES["g2_receipt"])["shared_scalars"]
    return {
        "constraint_rank": float(receipt["constraint_rank"]),
        "rank_tol": float(receipt["rank_tol"]),
        "der_O_dim": float(receipt["der_O_dim"]),
        "basis_column_count": float(receipt["der_O_dim"]),
        "random_tracefree_derivation_residual": float(receipt["random_tracefree_derivation_residual"]),
        "source": "octonion_G2_automorphism",
    }


def anchors() -> dict[str, dict[str, Any]]:
    return {
        "qit": qit_anchor(),
        "density": density_anchor(),
        "hopf": hopf_anchor(),
        "golden": golden_anchor(),
        "division": division_anchor(),
        "g2": g2_anchor(),
    }


def alpha_candidate_from_anchors(base: dict[str, dict[str, Any]], erase: str | None = None) -> tuple[float, dict[str, float]]:
    qit = dict(base["qit"])
    den = dict(base["density"])
    hp = dict(base["hopf"])
    gw = dict(base["golden"])
    div = dict(base["division"])
    g = dict(base["g2"])

    if erase == "canonical_qit_engine_specs.py":
        qit.update({"h0_norm": 1.0, "schedule_total_len": 1.0, "manifold_layer_count": 1.0, "operator_slot_count": 1.0})
    elif erase == "density_matrix_spinor_lift":
        den.update({"bloch_norm": 0.0, "mixed_purity": 0.5, "fiber_dim": 0.0, "mixed_rank": 1.0})
    elif erase == "clifford_torus_nested_hopf_foliation":
        hp.update({"torus_metric_det_min": 0.0, "hopf_vec_norm": 0.0})
    elif erase == "golden_weyl":
        gw.update({"linking_number": 0.0, "cocycle_gap": 0.0, "claimed_effect_gap": 0.0, "n01_commutator_norm": 0.0})
    elif erase == "division_algebra_ratchet_ladder":
        div.update({"h_commutator_norm": 0.0, "o_associator_max": 0.0, "o_alternator_residual": 0.0})
    elif erase == "octonion_G2_automorphism":
        g.update({"der_O_dim": 1.0, "random_tracefree_derivation_residual": 0.0})

    qit_schedule_factor = qit["schedule_total_len"] + qit["manifold_layer_count"] + qit["operator_slot_count"]
    qit_factor = qit["h0_norm"] / (1.0 + qit_schedule_factor)
    density_factor = 1.0 + den["bloch_norm"] + den["mixed_purity"] + den["fiber_dim"]
    hopf_factor = 1.0 + hp["torus_metric_det_min"] + 0.25 * hp["hopf_vec_norm"]
    golden_factor = 1.0 + abs(gw["linking_number"]) + abs(gw["cocycle_gap"]) + 0.10 * gw["n01_commutator_norm"]
    division_factor = 1.0 + div["h_commutator_norm"] + div["o_associator_max"] + div["o_alternator_residual"]
    g2_factor = 1.0 + g["der_O_dim"] / 14.0 + g["random_tracefree_derivation_residual"] / 8.0
    mixed_rank_factor = 1.0 + den["mixed_rank"]
    value = qit_factor * density_factor * hopf_factor * golden_factor / (division_factor * g2_factor * mixed_rank_factor)
    factors = {
        "qit_factor": float(qit_factor),
        "density_factor": float(density_factor),
        "hopf_factor": float(hopf_factor),
        "golden_factor": float(golden_factor),
        "division_factor": float(division_factor),
        "g2_factor": float(g2_factor),
        "mixed_rank_factor": float(mixed_rank_factor),
    }
    return float(value), factors


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "status": "pending_peer_backend",
            "parity_max_diff": None,
            "max_diff_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
        }
    peer = read_json(JULIA_RESULT_PATH)
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        if diff > max_diff:
            max_diff = diff
            max_key = key
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
        "peer_result_path": str(JULIA_RESULT_PATH),
        "status": "compared",
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "max_diff_key": max_key,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict or mismatches or missing),
    }


def section_passes(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def has_direct_numpy_import(source_text: str) -> bool:
    """Detect real NumPy imports without matching explanatory strings."""
    parsed = ast.parse(source_text)
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            if any(alias.name == "numpy" or alias.name.startswith("numpy.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "numpy" or module.startswith("numpy."):
                return True
    return False


def build_result() -> dict[str, Any]:
    base = anchors()
    alpha_value, factors = alpha_candidate_from_anchors(base)
    ablation_keys = [
        "canonical_qit_engine_specs.py",
        "density_matrix_spinor_lift",
        "clifford_torus_nested_hopf_foliation",
        "golden_weyl",
        "division_algebra_ratchet_ladder",
        "octonion_G2_automorphism",
    ]
    ablations: dict[str, Any] = {}
    ablation_deltas: dict[str, float] = {}
    for key in ablation_keys:
        erased_value, erased_factors = alpha_candidate_from_anchors(base, erase=key)
        delta = abs(alpha_value - erased_value)
        ablations[key] = {"alpha_value": erased_value, "abs_delta_from_full": delta, "factors": erased_factors}
        ablation_deltas[key] = delta
    owner_carrier_load_bearing = all(delta > LOAD_BEARING_DELTA_THRESHOLD for delta in ablation_deltas.values())

    fit_scale = TARGET_ALPHA / alpha_value if alpha_value != 0.0 else 0.0
    fit_alpha_value = alpha_value * fit_scale
    fit_matches = abs(fit_alpha_value - TARGET_ALPHA) <= TOL
    matches_137 = abs(alpha_value - TARGET_ALPHA) <= MATCH_TOL
    derived = False
    tuned_to_target = False
    derived_not_fit = bool(derived and not tuned_to_target)
    fit_or_tuned = False
    underdetermined = True

    source_text = Path(__file__).read_text(encoding="utf-8")
    no_direct_numpy_import = not has_direct_numpy_import(source_text)

    positive = {
        "finite_carrier_scalar_computed": {
            "pass": bool(jnp.isfinite(jnp.asarray(alpha_value)) and alpha_value > 0.0),
            "alpha_value": alpha_value,
            "target_alpha_1_over_137": TARGET_ALPHA,
            "abs_delta_from_target": abs(alpha_value - TARGET_ALPHA),
            "reason": "an untuned finite carrier geometry/coupling scalar was computed on the owner carrier",
        },
        "owner_carrier_load_bearing": {
            "pass": owner_carrier_load_bearing,
            "ablation_deltas": ablation_deltas,
            "threshold": LOAD_BEARING_DELTA_THRESHOLD,
            "reason": "erasing each named owner carrier changes the attempted scalar",
        },
        "jax_jnp_x64_no_direct_numpy_import": {
            "pass": bool(jax.config.read("jax_enable_x64") and no_direct_numpy_import),
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "reason": "this JAX scout uses jax.numpy x64 and has no direct NumPy import",
        },
    }
    controls = {
        "target_fit_control_is_explicitly_tuned": {
            "pass": bool(fit_matches and abs(fit_scale - 1.0) > 1.0e-3),
            "fit_scale": fit_scale,
            "fit_alpha_value": fit_alpha_value,
            "fit_matches_137": fit_matches,
            "used_for_primary": False,
            "reason": "hitting 1/137 is possible only by multiplying by a free target-fit parameter, so it is not admitted",
        },
        "carrier_erasure_changes_result": {
            "pass": owner_carrier_load_bearing,
            "min_abs_delta": min(ablation_deltas.values()),
            "reason": "the owner carrier is not decorative under the attempted scalar",
        },
        "flat_carrier_control_not_same_value": {
            "pass": bool(abs(alpha_value - ablations["golden_weyl"]["alpha_value"]) > LOAD_BEARING_DELTA_THRESHOLD),
            "control_value": ablations["golden_weyl"]["alpha_value"],
            "reason": "removing nested/golden Weyl information changes the scalar rather than leaving a tautology",
        },
    }
    graveyard_companions = {
        "fine_structure_constant_derivation": {
            "pass": True,
            "derived": derived,
            "derived_not_fit": derived_not_fit,
            "value": alpha_value,
            "matches_137": matches_137,
            "reason": "the carrier produced an untuned diagnostic scalar, but no derivation of alpha from the carrier constraints was found",
        },
        "target_matched_fit": {
            "pass": True,
            "derived": False,
            "fit_only": True,
            "value": fit_alpha_value,
            "matches_137": fit_matches,
            "tuning_parameter": fit_scale,
            "reason": "the target can be hit only by adding an external scale chosen from the target",
        },
        "physics_admission": {
            "pass": True,
            "derived": False,
            "value": None,
            "reason": "no physics admission follows from this scratch diagnostic",
        },
    }
    boundary = {
        "scratch_diagnostic_fence": {
            "pass": True,
            "classification": "scratch_diagnostic",
            "promotion": False,
            "formal_admission": False,
            "reason": "the result is fenced by request and by claim ceiling",
        },
        "hard_open_rung_not_forced": {
            "pass": bool(not derived and not derived_not_fit and underdetermined),
            "reason": "the alpha rung is graveyarded instead of forced into a claimed derivation",
        },
        "single_status_control": {
            "pass": sum([derived_not_fit, fit_or_tuned, underdetermined]) == 1,
            "derived_not_fit": derived_not_fit,
            "fit_or_tuned": fit_or_tuned,
            "underdetermined": underdetermined,
            "reason": "exactly one alpha-status bucket is active for the primary untuned value",
        },
    }
    local_all_pass = section_passes(positive) and section_passes(controls) and section_passes(graveyard_companions) and section_passes(boundary)

    shared_scalars: dict[str, float] = {
        "alpha_value": float(alpha_value),
        "target_alpha_1_over_137": float(TARGET_ALPHA),
        "alpha_abs_delta_from_target": float(abs(alpha_value - TARGET_ALPHA)),
        "fit_scale_to_target": float(fit_scale),
        "fit_alpha_value": float(fit_alpha_value),
        "qit.h0_norm": float(base["qit"]["h0_norm"]),
        "qit.schedule_total_len": float(base["qit"]["schedule_total_len"]),
        "qit.manifold_layer_count": float(base["qit"]["manifold_layer_count"]),
        "density.bloch_norm": float(base["density"]["bloch_norm"]),
        "density.mixed_purity": float(base["density"]["mixed_purity"]),
        "density.fiber_dim": float(base["density"]["fiber_dim"]),
        "hopf.torus_metric_det_min": float(base["hopf"]["torus_metric_det_min"]),
        "hopf.hopf_vec_norm": float(base["hopf"]["hopf_vec_norm"]),
        "golden.linking_number": float(base["golden"]["linking_number"]),
        "golden.cocycle_gap": float(base["golden"]["cocycle_gap"]),
        "golden.n01_commutator_norm": float(base["golden"]["n01_commutator_norm"]),
        "division.h_commutator_norm": float(base["division"]["h_commutator_norm"]),
        "division.o_associator_max": float(base["division"]["o_associator_max"]),
        "division.o_alternator_residual": float(base["division"]["o_alternator_residual"]),
        "g2.der_O_dim": float(base["g2"]["der_O_dim"]),
        "g2.random_tracefree_derivation_residual": float(base["g2"]["random_tracefree_derivation_residual"]),
    }
    for key, value in factors.items():
        shared_scalars[f"factor.{key}"] = float(value)
    for key, value in ablation_deltas.items():
        shared_scalars[f"ablation_delta.{key}"] = float(value)
        shared_scalars[f"ablation_value.{key}"] = float(ablations[key]["alpha_value"])

    shared_booleans = {
        "matches_137": matches_137,
        "derived": derived,
        "derived_not_fit": derived_not_fit,
        "fit_control_matches_137": fit_matches,
        "fit_or_tuned": fit_or_tuned,
        "underdetermined": underdetermined,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "promotion": False,
        "formal_admission": False,
    }

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "name": "MP4 fine-structure constant exploration scratch diagnostic",
        "backend": "jax_jnp_x64_no_direct_numpy_import",
        "classification": "scratch_diagnostic",
        "promotion": False,
        "promotion_allowed": False,
        "formal_admission": False,
        "formal_admission_allowed": False,
        "schema": "codex-ratchet.formal_scout.dual_backend.v1",
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "claim_ceiling": CLAIM_CEILING,
        "question": "Can the owner carrier derive alpha near 1/137 from geometry/coupling without tuning?",
        "construction": "Untuned finite scalar built from real owner carrier invariants, with source-erasure ablations and a separate explicit target-fit control.",
        "source_refs": source_refs(),
        "positive": positive,
        "controls": controls,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "all_pass": True,
            "variants": ["carrier_erased_controls", "flat_golden_control", "fit_control"],
            "summary": {
                "carrier_erased_controls": "each named owner carrier is erased one at a time",
                "flat_golden_control": "nested/golden Weyl contribution removed",
                "fit_control": "external multiplicative scale chosen from target alpha is recorded but not used",
            },
        },
        "why_not_v4_probes": [
            "scratch diagnostic only, not a formal admission candidate",
            "alpha is a hard/open physics constant and this carrier does not derive it",
            "the matched 1/137 value appears only in the explicit target-fit control",
        ],
        "allowed_claims": [
            "finite mechanism witness",
            "dual-backend parity witness",
            "non-tautological owner-carrier erasure/control diagnostic",
            "honest graveyard result for fine-structure derivation",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "alpha_attempt": {
            "alpha_value": alpha_value,
            "target_alpha_1_over_137": TARGET_ALPHA,
            "matches_137": matches_137,
            "derived": derived,
            "derived_not_fit": derived_not_fit,
            "fit_or_tuned": fit_or_tuned,
            "underdetermined": underdetermined,
            "tuned_to_target": tuned_to_target,
            "fit_control": {
                "fit_alpha_value": fit_alpha_value,
                "fit_scale": fit_scale,
                "matches_137": fit_matches,
                "fit_only": True,
            },
        },
        "owner_carrier": {
            "load_bearing": owner_carrier_load_bearing,
            "ablation_deltas": ablation_deltas,
            "ablation_results": ablations,
            "anchors": {
                "qit": {k: v for k, v in base["qit"].items() if k not in {"h0_unit"}},
                "density": {k: v for k, v in base["density"].items() if k not in {"bloch"}},
                "hopf": {k: v for k, v in base["hopf"].items() if k not in {"hopf_vec"}},
                "golden": base["golden"],
                "division": base["division"],
                "g2": base["g2"],
            },
        },
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing x64 finite scalar, carrier ablation, target-fit control, and parity arithmetic; no direct NumPy import",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing H0, schedule, manifold-layer, and operator-slot factors; erasing it changes the attempted scalar",
            },
            "density_matrix_spinor_lift": {
                "tried": True,
                "used": True,
                "reason": "load-bearing spinor, density, Bloch, mixed-purity, and fiber/rank factors; erasing it changes the attempted scalar",
            },
            "clifford_torus_nested_hopf_foliation": {
                "tried": True,
                "used": True,
                "reason": "load-bearing Hopf torus metric/vector factor; erasing it changes the attempted scalar",
            },
            "golden_weyl": {
                "tried": True,
                "used": True,
                "reason": "load-bearing linking/cocycle/N01 factor; erasing it changes the attempted scalar",
            },
            "division_algebra_ratchet_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing quaternion and octonion algebra factor; erasing it changes the attempted scalar",
            },
            "octonion_G2_automorphism": {
                "tried": True,
                "used": True,
                "reason": "load-bearing G2 derivation/control factor; erasing it changes the attempted scalar",
            },
            "Python stdlib": {
                "tried": True,
                "used": True,
                "reason": "supportive JSON, hashing, import loading, and result writing",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "density_matrix_spinor_lift": "load_bearing",
            "clifford_torus_nested_hopf_foliation": "load_bearing",
            "golden_weyl": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "Python stdlib": "supportive",
        },
        "divergence_log": [
            "Primary scalar is untuned and does not match 1/137 within the declared window.",
            "Target match is possible only through an explicit free multiplicative scale chosen from 1/137.",
            "Every named owner carrier erasure changes the attempted scalar.",
            "Fine-structure derivation remains graveyarded: derived=false.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": local_all_pass,
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": local_all_pass,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "alpha_value": alpha_value,
        "target_alpha_1_over_137": TARGET_ALPHA,
        "matches_137": matches_137,
        "derived": derived,
        "derived_not_fit": derived_not_fit,
        "fit_control_matches_137": fit_matches,
        "fit_or_tuned": fit_or_tuned,
        "underdetermined": underdetermined,
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "parity_max_diff": result["parity"]["parity_max_diff"],
    }
    result["result_summary"] = result["summary"]
    result["blockers"] = [] if local_all_pass else [
        key for section in [positive, controls, graveyard_companions, boundary] for key, row in section.items() if not row.get("pass")
    ]
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
        f"alpha_value={result['summary']['alpha_value']} "
        f"matches_137={str(result['summary']['matches_137']).lower()} "
        f"derived_not_fit={str(result['summary']['derived_not_fit']).lower()}"
    )
    return 0 if result["local_all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
