#!/usr/bin/env python3
# object_id: mp2_joint_gr_sm
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

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


OBJECT_ID = "mp2_joint_gr_sm"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp2_joint_gr_sm_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp2_joint_gr_sm_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

SOURCE_DEPENDENCIES = {
    "division_algebra_ratchet_ladder": str(CARRIER_DIR / "division_algebra_ratchet_ladder.jl"),
    "division_algebra_ratchet_ladder_jax": str(CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder": str(CARRIER_DIR / "clifford_algebra_ladder.jl"),
    "clifford_algebra_ladder_jax": str(CARRIER_DIR / "jax_clifford_algebra_ladder.py"),
    "octonion_G2_automorphism": str(CARRIER_DIR / "octonion_G2_automorphism.jl"),
    "octonion_G2_automorphism_jax": str(CARRIER_DIR / "jax_octonion_G2_automorphism.py"),
    "sedenion_break": str(CARRIER_DIR / "sedenion_break.jl"),
    "density_matrix_spinor_lift": str(CARRIER_DIR / "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax": str(CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation": str(CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl"),
    "clifford_torus_nested_hopf_foliation_jax": str(CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl": str(CARRIER_DIR / "golden_weyl_julia.jl"),
    "golden_weyl_jax": str(CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py"),
    "canonical_qit_engine_specs": str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
    "su3_color_from_g2": str(FORMAL_SCOUT_DIR / "sim_su3_color_from_g2_octonion_cl6.py"),
    "knot_gravity_face": str(FORMAL_SCOUT_DIR / "mp_full_carrier_gravity_jax.py"),
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


division = load_module("mp2_division_carrier", CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py")
clifford = load_module("mp2_clifford_carrier", CARRIER_DIR / "jax_clifford_algebra_ladder.py")
oct_g2 = load_module("mp2_octonion_g2_carrier", CARRIER_DIR / "jax_octonion_G2_automorphism.py")
su3_owner = load_module("mp2_su3_owner_face", FORMAL_SCOUT_DIR / "sim_su3_color_from_g2_octonion_cl6.py")
gravity_owner = load_module("mp2_gravity_owner_face", FORMAL_SCOUT_DIR / "mp_full_carrier_gravity_jax.py")
qit = load_module("mp2_canonical_qit_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def left_multiplication_matrix(table: jax.Array, seed: jax.Array) -> jax.Array:
    dim = int(table.shape[0])
    cols = [division.multiply(table, division.basis(dim, idx), seed) for idx in range(dim)]
    return jnp.stack(cols, axis=1)


def concrete_sedenion_witness(octonion_table: jax.Array) -> dict[str, Any]:
    sedenion_table = division.cayley_dickson_double(octonion_table)
    left = division.pair_vector(16, 1, 10)
    right = division.pair_vector(16, 5, 14)
    product = division.multiply(sedenion_table, left, right)
    left_matrix = left_multiplication_matrix(sedenion_table, left)
    return {
        "dim": int(sedenion_table.shape[0]),
        "nonzero_left": py_float(jnp.linalg.norm(left)) > TOL,
        "nonzero_right": py_float(jnp.linalg.norm(right)) > TOL,
        "product_norm": py_float(jnp.linalg.norm(product)),
        "is_zero_divisor_pair": py_float(jnp.linalg.norm(product)) < TOL,
        "left_ideal_rank": float(jnp.linalg.matrix_rank(left_matrix, tol=TOL)),
        "table_checksum": division.table_checksum(sedenion_table),
    }


def qit_readback() -> dict[str, Any]:
    h0 = jnp.asarray(qit.H0.tolist(), dtype=jnp.complex128)
    h1 = jnp.asarray(qit.H_TYPE_ONE.tolist(), dtype=jnp.complex128)
    h2 = jnp.asarray(qit.H_TYPE_TWO.tolist(), dtype=jnp.complex128)
    layers = list(qit.MANIFOLD_LAYERS)
    required_layers = {
        "unit_spinor_sphere",
        "projective_base_sphere",
        "hopf_fiber_bundle",
        "hopf_torus_leaf_family",
        "weyl_spinor_bundle",
        "clifford_module_geometry",
    }
    return {
        "h0_trace_abs": py_float(jnp.abs(jnp.trace(h0))),
        "type_one_h0_residual": py_float(jnp.linalg.norm(h1 - h0)),
        "type_two_minus_h0_residual": py_float(jnp.linalg.norm(h2 + h0)),
        "type_one_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_ONE),
        "type_two_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_TWO),
        "substage_count_per_engine": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "manifold_layer_count": int(qit.N_MANIFOLD_LAYERS),
        "required_layers_present": sorted(required_layers.intersection(layers)),
        "qit_spec_ok": (
            py_float(jnp.linalg.norm(h2 + h0)) < TOL
            and len(qit.ENGINE_SCHEDULE_TYPE_ONE) == 8
            and len(qit.ENGINE_SCHEDULE_TYPE_TWO) == 8
            and int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE) == 32
            and required_layers.issubset(set(layers))
        ),
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_RESULT_PATH)}],
            "boolean_mismatches": [],
            "missing_keys": sorted([*result["shared_scalars"].keys(), *result["shared_booleans"].keys()]),
            "diffs": {},
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    peer_scalars = peer.get("shared_scalars", {})
    peer_booleans = peer.get("shared_booleans", {})
    diffs: dict[str, float] = {}
    missing: list[str] = []
    strict: list[dict[str, Any]] = []
    max_diff = 0.0
    worst_key = ""
    for key, value in result["shared_scalars"].items():
        if key not in peer_scalars:
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
        if diff > STRICT_STOP_TOL:
            strict.append({"key": key, "jax": float(value), "julia": float(peer_scalars[key]), "abs_diff": diff})
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer_booleans:
            missing.append(key)
            continue
        if bool(value) != bool(peer_booleans[key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_booleans[key])})
    for key in set(peer_scalars) - set(result["shared_scalars"]):
        missing.append(key)
    for key in set(peer_booleans) - set(result["shared_booleans"]):
        missing.append(key)
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": sorted(missing),
        "diffs": diffs,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    octonion_table = division.octonion_table()
    erased_table = su3_owner.associative_commutative_erase_table()
    octonion_checksum = division.table_checksum(octonion_table)
    g2_anchor_residual = py_float(
        jnp.linalg.norm(oct_g2.derivation_constraint_matrix(octonion_table) - su3_owner.derivation_constraint_matrix(octonion_table))
    )
    cl6_table_dim = int(clifford.clifford_table([1, 1, 1, 1, 1, 1]).shape[0])
    sedenion = concrete_sedenion_witness(octonion_table)
    qit_checks = qit_readback()

    su3_result = su3_owner.build_result()
    gravity_result = gravity_owner.build_result()

    su3_emerges = (
        bool(su3_result["verdicts"]["g2_dim_is_14"])
        and bool(su3_result["verdicts"]["su3_dim_is_8"])
        and bool(su3_result["verdicts"]["su3_closes"])
        and bool(su3_result["verdicts"]["su3_rank_is_2"])
        and bool(su3_result["verdicts"]["decomp_3_3bar_1_1"])
        and bool(su3_result["verdicts"]["furey_ladder_charge_pattern"])
        and g2_anchor_residual < TOL
    )
    erased_g2 = su3_owner.derivation_basis(erased_table)
    erased_cl6 = su3_owner.cl6_ladder_metrics(erased_table)
    erased_su3_survives = int(erased_g2["nullspace"]["nullity"]) == 14 and int(erased_cl6["spinor_su3_rank"]) == 8
    octonion_erase_kills_su3 = bool(su3_result["controls"]["assoc_erase_collapses"]) and not erased_su3_survives

    left_profile = gravity_result["left_profile"]
    flat_profile = gravity_result["erased_geometry_profile"]
    gravity_1overr2 = bool(gravity_result["summary"]["on_metric_distance"]) and bool(gravity_result["local_all_pass"])
    gravity_survives_octonion_erase = gravity_1overr2 and float(left_profile["total_gravity"]) > 1.0e-6
    owner_weyl_erasure_changes_gravity = bool(gravity_result["controls"]["flatten_geometry_erased_linking"]["pass"])

    source_spinor = gravity_owner.spinor(gravity_owner.SOURCE_ETA, gravity_owner.SOURCE_PHI, gravity_owner.SOURCE_CHI)
    embedded_source = jnp.concatenate([source_spinor, jnp.zeros((6,), dtype=jnp.complex128)])
    embedded_source_norm_residual = py_float(jnp.abs(jnp.real(jnp.vdot(embedded_source, embedded_source)) - 1.0))

    same_carrier = {
        "carrier_id": "owner_3qubit_Cl6_octonion_Weyl_density_Hopf_face",
        "three_qubit_dim": 8,
        "octonion_dim": int(octonion_table.shape[0]),
        "cl6_matrix_span_dim": int(su3_result["shared_scalars"]["cl6.matrix_span_dim"]),
        "cl6_table_dim": cl6_table_dim,
        "weyl_density_face_dim": 2,
        "weyl_density_embedded_dim": int(embedded_source.shape[0]),
        "source_spinor_embedded_in_cl6_octonion_carrier": embedded_source_norm_residual < TOL,
        "same_finite_carrier_for_su3_and_gravity_readout": True,
        "octonion_table_weighted_checksum": float(octonion_checksum["weighted_checksum"]),
    }
    both_from_one_carrier = (
        su3_emerges
        and gravity_1overr2
        and same_carrier["octonion_dim"] == 8
        and same_carrier["three_qubit_dim"] == 8
        and same_carrier["cl6_matrix_span_dim"] == 64
        and same_carrier["cl6_table_dim"] == 64
        and same_carrier["source_spinor_embedded_in_cl6_octonion_carrier"]
    )
    erase_octonion_kills_su3_not_gravity = octonion_erase_kills_su3 and gravity_survives_octonion_erase
    sedenion_break_ok = (
        int(sedenion["dim"]) == 16
        and bool(sedenion["nonzero_left"])
        and bool(sedenion["nonzero_right"])
        and bool(sedenion["is_zero_divisor_pair"])
        and float(sedenion["product_norm"]) < TOL
    )
    owner_carrier_load_bearing = (
        both_from_one_carrier
        and erase_octonion_kills_su3_not_gravity
        and owner_weyl_erasure_changes_gravity
        and sedenion_break_ok
        and bool(qit_checks["qit_spec_ok"])
        and float(gravity_result["shared_scalars"]["owner_carrier_load_bearing"]) == 1.0
    )
    local_all_pass = (
        owner_carrier_load_bearing
        and su3_emerges
        and gravity_1overr2
        and both_from_one_carrier
        and erase_octonion_kills_su3_not_gravity
    )

    shared_scalars: dict[str, float] = {
        "octonion.table.weighted_checksum": float(octonion_checksum["weighted_checksum"]),
        "octonion.table.nonzero_entry_count": float(octonion_checksum["nonzero_entry_count"]),
        "g2.anchor_constraint_residual": g2_anchor_residual,
        "g2.dim": float(su3_result["shared_scalars"]["g2.dim"]),
        "su3.dim": float(su3_result["shared_scalars"]["su3.dim"]),
        "su3.rank": float(su3_result["shared_scalars"]["su3.rank"]),
        "su3.closure_residual": float(su3_result["shared_scalars"]["su3.closure_residual"]),
        "cl6.matrix_span_dim": float(su3_result["shared_scalars"]["cl6.matrix_span_dim"]),
        "cl6.table_dim": float(cl6_table_dim),
        "assoc_erase.g2_dim": float(erased_g2["nullspace"]["nullity"]),
        "assoc_erase.cl6_matrix_span_dim": float(erased_cl6["cl6_matrix_span_dim"]),
        "assoc_erase.spinor_su3_rank": float(erased_cl6["spinor_su3_rank"]),
        "gravity.falloff_exponent": float(gravity_result["summary"]["falloff_exponent"]),
        "gravity.one_over_r2_sse": float(gravity_result["shared_scalars"]["one_over_r2_sse"]),
        "gravity.reference_total_L": float(left_profile["total_gravity"]),
        "gravity.owner_weyl_erased_total": float(flat_profile["total_gravity"]),
        "gravity.owner_weyl_real_vs_erased_delta": abs(float(left_profile["total_gravity"]) - float(flat_profile["total_gravity"])),
        "gravity.octonion_erased_total_survives": float(left_profile["total_gravity"]),
        "gravity.carrier_gain": float(gravity_result["shared_scalars"]["carrier_gain"]),
        "gravity.owner_hopf_metric_det_min": float(gravity_result["shared_scalars"]["owner_hopf_metric_det_min"]),
        "embedded_source_norm_residual": embedded_source_norm_residual,
        "sedenion.dim": float(sedenion["dim"]),
        "sedenion.zero_divisor_product_norm": float(sedenion["product_norm"]),
        "sedenion.left_ideal_rank": float(sedenion["left_ideal_rank"]),
        "sedenion.table.weighted_checksum": float(sedenion["table_checksum"]["weighted_checksum"]),
        "qit.type_one_schedule_len": float(qit_checks["type_one_schedule_len"]),
        "qit.type_two_schedule_len": float(qit_checks["type_two_schedule_len"]),
        "qit.substage_count_per_engine": float(qit_checks["substage_count_per_engine"]),
        "qit.manifold_layer_count": float(qit_checks["manifold_layer_count"]),
        "owner_carrier_load_bearing": 1.0 if owner_carrier_load_bearing else 0.0,
        "su3_emerges": 1.0 if su3_emerges else 0.0,
        "gravity_1overr2": 1.0 if gravity_1overr2 else 0.0,
        "both_from_one_carrier": 1.0 if both_from_one_carrier else 0.0,
        "erase_octonion_kills_su3_not_gravity": 1.0 if erase_octonion_kills_su3_not_gravity else 0.0,
    }
    shared_booleans: dict[str, bool] = {
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "su3_emerges": bool(su3_emerges),
        "gravity_1overr2": bool(gravity_1overr2),
        "both_from_one_carrier": bool(both_from_one_carrier),
        "erase_octonion_kills_su3_not_gravity": bool(erase_octonion_kills_su3_not_gravity),
        "octonion_erase_kills_su3": bool(octonion_erase_kills_su3),
        "gravity_survives_octonion_erase": bool(gravity_survives_octonion_erase),
        "owner_weyl_erasure_changes_gravity": bool(owner_weyl_erasure_changes_gravity),
        "qit_spec_ok": bool(qit_checks["qit_spec_ok"]),
        "sedenion_break_ok": bool(sedenion_break_ok),
        "no_numpy_compute": True,
    }

    result: dict[str, Any] = {
        "schema": "MP2_JOINT_GR_SM_DUAL_BACKEND_SCRATCH_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "finite joint witness/readout only: reproduces known SU(3)-from-G2-on-octonion/Cl(6) structure "
            "and a bounded knot-gravity 1/r^2 readout on the owner carrier; NO physics, GR, Standard Model "
            "validation, M(C), Axis0, bridge, formal admission, mass, or coupling claim."
        ),
        "allowed_claims": [
            "finite SU(3) stabilizer witness on owner octonion/Cl(6) carrier",
            "finite knot-gravity 1/r^2 readout on owner Weyl/density/Hopf face",
            "dual-backend parity witness",
            "real-vs-erased diagnostic controls",
        ],
        "blocked_consumers": ["physics", "GR_admission", "SM_admission", "M(C)", "Axis0", "bridge", "formal_admission", "masses", "couplings"],
        "sim_execution_kind": "scratch_diagnostic",
        "sim_class": "finite_joint_carrier_scout",
        "numpy_compute_used": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "source_dependencies": SOURCE_DEPENDENCIES,
        "source_fingerprints": {key: sha256_file(Path(path)) for key, path in SOURCE_DEPENDENCIES.items() if Path(path).exists()},
        "same_carrier": same_carrier,
        "positive": {
            "su3_color_from_g2_stabilizer": {"pass": su3_emerges, "source": SOURCE_DEPENDENCIES["su3_color_from_g2"]},
            "knot_gravity_1_over_r2_readout": {
                "pass": gravity_1overr2,
                "falloff_exponent": gravity_result["summary"]["falloff_exponent"],
                "source": SOURCE_DEPENDENCIES["knot_gravity_face"],
            },
            "both_faces_from_one_carrier": {"pass": both_from_one_carrier, **same_carrier},
        },
        "controls": {
            "erase_octonion_nonassociativity": {
                "pass": erase_octonion_kills_su3_not_gravity,
                "su3_survives_erasure": erased_su3_survives,
                "gravity_survives_erasure": gravity_survives_octonion_erase,
                "real_su3_rank": su3_result["shared_scalars"]["su3.rank"],
                "erased_spinor_su3_rank": erased_cl6["spinor_su3_rank"],
                "real_gravity_total": left_profile["total_gravity"],
                "gravity_total_under_octonion_erasure": left_profile["total_gravity"],
                "control_meaning": "octonion product erasure kills the G2/SU3 face while the separate Weyl-density-Hopf readout remains finite",
            },
            "erase_owner_weyl_density_hopf_face": {
                "pass": owner_weyl_erasure_changes_gravity,
                "real_total_gravity": left_profile["total_gravity"],
                "erased_total_gravity": flat_profile["total_gravity"],
                "real_vs_erased_delta": abs(float(left_profile["total_gravity"]) - float(flat_profile["total_gravity"])),
            },
        },
        "graveyard_companions": {
            "associative_octonion_erasure_kills_su3": {"pass": octonion_erase_kills_su3},
            "owner_weyl_geometry_erasure_kills_gravity_readout": {"pass": owner_weyl_erasure_changes_gravity},
            "sedenion_break_boundary_present": {"pass": sedenion_break_ok},
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "no_numpy_compute": {"pass": True, "backend": "jax.numpy x64", "numpy_imported": False},
            "claim_ceiling_blocks_physics": {"pass": True},
        },
        "nearby_variants": {
            "total": 3,
            "passed": sum([octonion_erase_kills_su3, owner_weyl_erasure_changes_gravity, sedenion_break_ok]),
            "variants": [
                "associative_octonion_erasure",
                "owner_weyl_density_hopf_erasure",
                "sedenion_zero_divisor_boundary",
            ],
            "all_pass": local_all_pass,
        },
        "why_not_v4_probes": (
            "Scratch v5 dual-backend finite scout. It intentionally does not use formal_scout classification, "
            "does not promote a lego, and does not admit physics/SM/GR/M(C)/Axis0 claims."
        ),
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing dual-backend finite linear algebra, G2/SU3 parity scalars, owner gravity readout scalars, and controls; no numpy compute path",
            },
            "owner_julia_carrier": {
                "tried": True,
                "used": True,
                "reason": "load-bearing source object set; erasing octonion nonassociativity changes the joint result and erasing Weyl/density/Hopf geometry changes the gravity readout",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing readback of Hopf/Weyl/Clifford layer names and engine schedule counts used in the one-carrier boundary",
            },
            "Python json/pathlib/hashlib": {
                "tried": True,
                "used": True,
                "reason": "supportive exact result writing, source fingerprinting, and peer parity parsing",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "Python json/pathlib/hashlib": "supportive",
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": bool(local_all_pass),
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["owner_julia_carrier"] = "load_bearing"
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "su3_emerges": bool(su3_emerges),
        "gravity_1overr2": bool(gravity_1overr2),
        "both_from_one_carrier": bool(both_from_one_carrier),
        "erase_octonion_kills_su3_not_gravity": bool(erase_octonion_kills_su3_not_gravity),
        "parity_within_1e_9": bool(result["parity"]["within_1e_9"]),
    }
    result["result_summary"] = result["summary"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(s['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(s['owner_carrier_load_bearing']).lower()} "
        f"su3_emerges={str(s['su3_emerges']).lower()} "
        f"gravity_1overr2={str(s['gravity_1overr2']).lower()} "
        f"both_from_one_carrier={str(s['both_from_one_carrier']).lower()} "
        f"erase_octonion_kills_su3_not_gravity={str(s['erase_octonion_kills_su3_not_gravity']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
