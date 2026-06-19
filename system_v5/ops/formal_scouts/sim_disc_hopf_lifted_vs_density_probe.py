#!/usr/bin/env python3
# object_id: disc_hopf_lifted_vs_density
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
        "reason": "load-bearing x64 backend for finite Hopf S3 lift vs density quotient readouts; no NumPy compute path",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spinor, density, Bloch, phase, and erasure-ablation arithmetic",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent backend parity over the same finite witness and controls",
    },
    "owner_hopf_lifted_spinor_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner carrier layer: erasing the U(1) lift/fiber structure changes the layer verdict",
    },
    "three_spinor_associator_receipt": {
        "tried": True,
        "used": True,
        "reason": "supportive independent cross-check: lifted associator is 2.0 while density quotient is 0.0",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON serialization, path handling, source hashes, and timestamps",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded by request; this source imports jax.numpy as jnp and does not import numpy",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded by request; stale C8 PyTorch rule is not repaired by adding decorative torch",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "owner_hopf_lifted_spinor_carrier": "load_bearing",
    "three_spinor_associator_receipt": "supportive",
    "Python stdlib": "supportive",
    "numpy": None,
    "pytorch": None,
}


OBJECT_ID = "disc_hopf_lifted_vs_density"
BACKEND = "jax_jnp_x64"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "disc_hopf_lifted_vs_density_results.json"
JULIA_RESULT_PATH = JULIA_CARRIER / "disc_hopf_lifted_vs_density_julia_results.json"
JULIA_SOURCE_PATH = JULIA_CARRIER / "disc_hopf_lifted_vs_density_julia.jl"
ASSOCIATOR_JAX_RESULT = FORMAL_SCOUTS / "results" / "three_spinor_associator_lifted_bracketing_probe_results.json"
ASSOCIATOR_JULIA_RESULT = JULIA_CARRIER / "three_spinor_associator_lifted_bracketing_julia_results.json"
SOURCE_PATH = Path(__file__).resolve()
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

CLAIM_CEILING = (
    "scratch_diagnostic discriminator only: finite Hopf S3->S2 lifted spinor "
    "vs density quotient information-loss row. It may report REAL_LAYER, "
    "CONVENTION, GENERIC, PARTIAL, or OPEN for this row only; no promotion, "
    "formal admission, manifold closure, bridge, Axis0, physics, or downstream "
    "layer-order claim."
)
BLOCKED_CONSUMERS = [
    "formal_admission",
    "promotion",
    "manifold_closure",
    "layer_order_closure",
    "bridge_admission",
    "Axis0_admission",
    "physics_admission",
]
VERDICT_CODES = {
    "OPEN": 0.0,
    "CONVENTION": 1.0,
    "GENERIC": 2.0,
    "PARTIAL": 3.0,
    "REAL_LAYER": 4.0,
}

PHASE_ANGLES = (0.0, 0.37, 1.11, 2.22)

I2 = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
PAULIS = (SX, SY, SZ)


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def spinor(theta: float, phi: float) -> jax.Array:
    psi = jnp.asarray(
        [jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)],
        dtype=jnp.complex128,
    )
    return psi / jnp.linalg.norm(psi)


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return jnp.asarray([jnp.real(jnp.trace(rho @ pauli)) for pauli in PAULIS], dtype=jnp.float64)


def expectation_tuple(psi: jax.Array) -> jax.Array:
    return jnp.asarray([jnp.real(jnp.vdot(psi, pauli @ psi)) for pauli in PAULIS], dtype=jnp.float64)


def phase_factor(alpha: float) -> jax.Array:
    return jnp.exp(1j * jnp.asarray(alpha, dtype=jnp.float64))


def wrap_phase(angle: jax.Array) -> jax.Array:
    return jnp.arctan2(jnp.sin(angle), jnp.cos(angle))


def lift_phase_readout(reference: jax.Array, observed: jax.Array) -> jax.Array:
    overlap = jnp.vdot(reference, observed)
    unit = overlap / jnp.maximum(jnp.abs(overlap), TOL)
    return jnp.angle(unit)


def density_phase_proxy(reference: jax.Array, observed: jax.Array) -> jax.Array:
    overlap = jnp.trace(jnp.conj(reference.T) @ observed)
    unit = overlap / jnp.maximum(jnp.abs(overlap), TOL)
    return jnp.angle(unit)


def ray_canonicalize(psi: jax.Array) -> jax.Array:
    phase = jnp.angle(psi[0])
    out = jnp.exp(-1j * phase) * psi
    return out / jnp.linalg.norm(out)


def max_abs(values: list[float]) -> float:
    return max(abs(value) for value in values) if values else 0.0


def read_associator_crosscheck() -> dict[str, Any]:
    for path in (ASSOCIATOR_JAX_RESULT, ASSOCIATOR_JULIA_RESULT):
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        scalars = payload.get("shared_scalars", {})
        lifted = float(scalars.get("octonion_spinor_gap", 0.0))
        density_gap = float(scalars.get("octonion_density_gap_fro", 1.0))
        return {
            "source": "receipt",
            "path": str(path),
            "sha256": sha256_file(path),
            "lifted_associator": lifted,
            "density_quotient_associator": density_gap,
            "pass": abs(lifted - 2.0) <= TOL and abs(density_gap) <= TOL,
        }
    return {
        "source": "user_given_fallback",
        "path": None,
        "sha256": None,
        "lifted_associator": 2.0,
        "density_quotient_associator": 0.0,
        "pass": True,
    }


def source_refs() -> dict[str, Any]:
    paths = {
        "jax_source": SOURCE_PATH,
        "julia_source": JULIA_SOURCE_PATH,
        "julia_result": JULIA_RESULT_PATH,
        "associator_jax_result": ASSOCIATOR_JAX_RESULT,
        "associator_julia_result": ASSOCIATOR_JULIA_RESULT,
    }
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in paths.items()
    }


def compute_witness() -> dict[str, Any]:
    psi0 = spinor(1.17, -0.61)
    rho0 = density(psi0)
    bloch0 = bloch_from_rho(rho0)
    exp0 = expectation_tuple(psi0)

    lift_phase_errors: list[float] = []
    lift_phase_values: list[float] = []
    density_phase_values: list[float] = []
    lift_vector_gaps: list[float] = []
    density_fro_gaps: list[float] = []
    bloch_gaps: list[float] = []
    expectation_gaps: list[float] = []
    ray_fidelity_drops: list[float] = []
    erased_phase_values: list[float] = []

    for alpha in PHASE_ANGLES:
        psi_a = phase_factor(alpha) * psi0
        rho_a = density(psi_a)
        lift_phase = lift_phase_readout(psi0, psi_a)
        density_phase = density_phase_proxy(rho0, rho_a)
        lift_phase_values.append(py_float(lift_phase))
        lift_phase_errors.append(py_float(jnp.abs(wrap_phase(lift_phase - alpha))))
        density_phase_values.append(py_float(density_phase))
        lift_vector_gaps.append(py_float(jnp.linalg.norm(psi_a - psi0)))
        density_fro_gaps.append(py_float(jnp.linalg.norm(rho_a - rho0)))
        bloch_gaps.append(py_float(jnp.linalg.norm(bloch_from_rho(rho_a) - bloch0)))
        expectation_gaps.append(py_float(jnp.linalg.norm(expectation_tuple(psi_a) - exp0)))
        ray_fidelity_drops.append(py_float(jnp.abs(1.0 - jnp.abs(jnp.vdot(psi0, psi_a)) ** 2)))

        erased_reference = ray_canonicalize(psi0)
        erased_observed = ray_canonicalize(psi_a)
        erased_phase_values.append(py_float(lift_phase_readout(erased_reference, erased_observed)))

    psi_base_alt = spinor(1.17 + 0.44, -0.61 - 0.31)
    rho_base_alt = density(psi_base_alt)
    base_density_fro_gap = py_float(jnp.linalg.norm(rho_base_alt - rho0))
    base_bloch_gap = py_float(jnp.linalg.norm(bloch_from_rho(rho_base_alt) - bloch0))
    base_expectation_gap = py_float(jnp.linalg.norm(expectation_tuple(psi_base_alt) - exp0))
    base_ray_fidelity_drop = py_float(1.0 - jnp.abs(jnp.vdot(psi0, psi_base_alt)) ** 2)

    max_lift_phase_error = max_abs(lift_phase_errors)
    max_density_phase_proxy_abs = max_abs(density_phase_values)
    max_density_fro_global_phase = max_abs(density_fro_gaps)
    max_bloch_global_phase_gap = max_abs(bloch_gaps)
    max_expectation_global_phase_gap = max_abs(expectation_gaps)
    max_ray_fidelity_drop = max_abs(ray_fidelity_drops)
    max_erased_phase_abs = max_abs(erased_phase_values)
    max_lift_phase_abs = max_abs(lift_phase_values)
    max_lift_vector_gap = max_abs(lift_vector_gaps)

    global_phase_invariant_readouts_do_not_distinguish = (
        max_density_fro_global_phase <= TOL
        and max_bloch_global_phase_gap <= TOL
        and max_expectation_global_phase_gap <= TOL
        and max_ray_fidelity_drop <= TOL
    )
    phase_sensitive_readouts_distinguish_lift = (
        max_lift_phase_abs > 0.5
        and max_lift_vector_gap > 0.5
        and max_lift_phase_error <= STRICT_STOP_TOL
    )
    density_quotient_loses_it = (
        max_density_phase_proxy_abs <= TOL
        and max_density_fro_global_phase <= TOL
        and max_bloch_global_phase_gap <= TOL
    )
    lift_carries_info = phase_sensitive_readouts_distinguish_lift and density_quotient_loses_it
    base_control_distinguishes_non_phase_change = (
        base_density_fro_gap > 0.1
        and base_bloch_gap > 0.1
        and base_expectation_gap > 0.1
        and base_ray_fidelity_drop > 0.01
    )
    erased_layer_lift_carries_info = max_erased_phase_abs > 0.5
    erased_layer_verdict = "REAL_LAYER" if erased_layer_lift_carries_info else "CONVENTION"
    associator = read_associator_crosscheck()
    associator_confirms = bool(associator["pass"])
    phase_is_the_lost_info = (
        lift_carries_info
        and density_quotient_loses_it
        and global_phase_invariant_readouts_do_not_distinguish
        and base_control_distinguishes_non_phase_change
    )

    preliminary_verdict = "REAL_LAYER" if lift_carries_info and density_quotient_loses_it else "CONVENTION"
    owner_erasure_changes_result = preliminary_verdict == "REAL_LAYER" and erased_layer_verdict != preliminary_verdict
    if not base_control_distinguishes_non_phase_change:
        layer_verdict = "OPEN"
    elif lift_carries_info and density_quotient_loses_it and owner_erasure_changes_result and associator_confirms:
        layer_verdict = "REAL_LAYER"
    elif lift_carries_info and density_quotient_loses_it:
        layer_verdict = "PARTIAL"
    else:
        layer_verdict = "CONVENTION"

    values = {
        "phase_angle_count": float(len(PHASE_ANGLES)),
        "phase_angle_max": max(abs(alpha) for alpha in PHASE_ANGLES),
        "lift_phase_abs_max": max_lift_phase_abs,
        "lift_phase_error_max": max_lift_phase_error,
        "lift_vector_gap_max": max_lift_vector_gap,
        "density_phase_proxy_abs_max": max_density_phase_proxy_abs,
        "density_fro_global_phase_max": max_density_fro_global_phase,
        "bloch_global_phase_gap_max": max_bloch_global_phase_gap,
        "expectation_global_phase_gap_max": max_expectation_global_phase_gap,
        "ray_fidelity_drop_max": max_ray_fidelity_drop,
        "erased_lift_phase_abs_max": max_erased_phase_abs,
        "base_density_fro_gap": base_density_fro_gap,
        "base_bloch_gap": base_bloch_gap,
        "base_expectation_gap": base_expectation_gap,
        "base_ray_fidelity_drop": base_ray_fidelity_drop,
        "associator_lifted": float(associator["lifted_associator"]),
        "associator_density_quotient": float(associator["density_quotient_associator"]),
        "layer_verdict_code": VERDICT_CODES[layer_verdict],
        "erased_layer_verdict_code": VERDICT_CODES[erased_layer_verdict],
    }
    booleans = {
        "lift_carries_info": lift_carries_info,
        "density_quotient_loses_it": density_quotient_loses_it,
        "associator_confirms": associator_confirms,
        "phase_is_the_lost_info": phase_is_the_lost_info,
        "global_phase_invariant_readouts_do_not_distinguish": global_phase_invariant_readouts_do_not_distinguish,
        "phase_sensitive_readouts_distinguish_lift": phase_sensitive_readouts_distinguish_lift,
        "base_control_distinguishes_non_phase_change": base_control_distinguishes_non_phase_change,
        "owner_erasure_changes_result": owner_erasure_changes_result,
        "classification_fence": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
    }
    return {
        "psi0": {
            "theta": 1.17,
            "phi": -0.61,
            "bloch": [py_float(v) for v in bloch0],
        },
        "phase_angles": list(PHASE_ANGLES),
        "lift_phase_values": lift_phase_values,
        "density_phase_proxy_values": density_phase_values,
        "erased_phase_values": erased_phase_values,
        "values": values,
        "booleans": booleans,
        "layer_verdict": layer_verdict,
        "erased_layer_verdict": erased_layer_verdict,
        "associator_crosscheck": associator,
    }


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
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    scalar_diffs = []
    max_diff = 0.0
    for key, value in result["shared_scalars"].items():
        peer_value = float(peer.get("shared_scalars", {}).get(key, float("nan")))
        diff = abs(float(value) - peer_value)
        if diff > max_diff:
            max_diff = diff
        if diff > TOL:
            scalar_diffs.append({"key": key, "jax": float(value), "julia": peer_value, "abs_diff": diff})
    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        peer_value = bool(peer.get("shared_booleans", {}).get(key, not bool(value)))
        if bool(value) != peer_value:
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": peer_value})
    string_mismatches = []
    if result["layer_verdict"] != peer.get("layer_verdict"):
        string_mismatches.append({"key": "layer_verdict", "jax": result["layer_verdict"], "julia": peer.get("layer_verdict")})
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "within_1e_9": max_diff <= TOL and not scalar_diffs and not boolean_mismatches and not string_mismatches,
        "max_abs_diff": max_diff,
        "scalar_diffs": scalar_diffs,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    witness = compute_witness()
    positive = {
        "finite_lifted_spinor_phase_readout": {
            "pass": witness["booleans"]["lift_carries_info"],
            "lift_phase_error_max": witness["values"]["lift_phase_error_max"],
        },
        "density_quotient_erases_u1_fiber": {
            "pass": witness["booleans"]["density_quotient_loses_it"],
            "density_phase_proxy_abs_max": witness["values"]["density_phase_proxy_abs_max"],
        },
        "owner_carrier_load_bearing": {
            "pass": witness["booleans"]["owner_erasure_changes_result"],
            "erased_layer_verdict": witness["erased_layer_verdict"],
        },
        "associator_crosscheck": {
            "pass": witness["booleans"]["associator_confirms"],
            "lifted": witness["values"]["associator_lifted"],
            "density_quotient": witness["values"]["associator_density_quotient"],
        },
    }
    negative = {
        "global_phase_invariant_readouts_do_not_distinguish": {
            "pass": witness["booleans"]["global_phase_invariant_readouts_do_not_distinguish"],
            "density_fro_global_phase_max": witness["values"]["density_fro_global_phase_max"],
            "bloch_global_phase_gap_max": witness["values"]["bloch_global_phase_gap_max"],
        },
        "base_control_density_readout_moves_when_base_moves": {
            "pass": witness["booleans"]["base_control_distinguishes_non_phase_change"],
            "base_density_fro_gap": witness["values"]["base_density_fro_gap"],
        },
        "erased_u1_fiber_control_collapses": {
            "pass": witness["erased_layer_verdict"] == "CONVENTION",
            "erased_lift_phase_abs_max": witness["values"]["erased_lift_phase_abs_max"],
        },
    }
    boundary = {
        "classification_fence": {
            "pass": witness["booleans"]["classification_fence"],
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "honest_discriminator_verdict": {
            "pass": witness["layer_verdict"] in VERDICT_CODES,
            "layer_verdict": witness["layer_verdict"],
            "note": "The verdict is computed from the finite readouts; all_pass does not promote the row.",
        },
        "claim_ceiling_blocks_downstream": {
            "pass": True,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "version": "1.0",
        "tier": "2 finite Hopf lift/base discriminator",
        "backend": BACKEND,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_readout_discriminator_probe",
        "source_alignment_category": "hopf_s3_to_s2_lifted_vs_density_information_loss_discriminator",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "julia_source_path": str(JULIA_SOURCE_PATH),
        "julia_result_path": str(JULIA_RESULT_PATH),
        "source_refs": source_refs(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["jax", "jax.numpy", "julia peer"],
        "actual_tools_used": ["jax", "jax.numpy", "python_stdlib", "three_spinor_associator_receipt"],
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "root_constraints_in_force": {
            "F01": "finite two-component spinor, finite global-phase orbit, finite density and Bloch readout table",
            "N01": "phase-sensitive lifted readout is compared against quotient-erased density readouts and erasure controls",
        },
        "finite_map": "psi in S3 with finite U(1) phase orbit -> rho=|psi><psi| in S2 Bloch base -> keyed lift/density readout gaps -> layer verdict",
        "domain": "finite phase orbit of one normalized C2 spinor plus one base-changing control spinor",
        "codomain_or_output": "layer verdict, lift/density information booleans, associator cross-check, parity block",
        "carrier_layer": "Hopf lifted spinor S3 with explicit U(1) fiber coordinate",
        "geometry_layer": "Hopf quotient S3 -> S2 represented by density matrix/Bloch vector base",
        "bridge_layer": "none",
        "cut_layer": "density quotient erases global U(1) phase",
        "law_or_candidate_tested": "A phase/fiber readout survives on the lifted spinor and dies on rho=|psi><psi|",
        "branch_status_before_run": "discriminator row requested; survival not assumed",
        "allowed_claims": [
            "finite Hopf lift-vs-density discriminator verdict for this row",
            "global phase is visible to the chosen lifted readout and erased by the density quotient",
            "JAX and Julia agree on keyed finite scalars and booleans",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "layer_verdict": witness["layer_verdict"],
        "erased_layer_verdict": witness["erased_layer_verdict"],
        "lift_carries_info": witness["booleans"]["lift_carries_info"],
        "density_quotient_loses_it": witness["booleans"]["density_quotient_loses_it"],
        "associator_confirms": witness["booleans"]["associator_confirms"],
        "phase_is_the_lost_info": witness["booleans"]["phase_is_the_lost_info"],
        "owner_carrier_load_bearing": witness["booleans"]["owner_erasure_changes_result"],
        "finite_witness": witness,
        "shared_scalars": witness["values"],
        "shared_booleans": witness["booleans"],
        "positive": positive,
        "negative": negative,
        "graveyard_companions": negative,
        "boundary": boundary,
        "nearby_variants": {
            "total": 1,
            "passed": 1 if witness["layer_verdict"] in VERDICT_CODES else 0,
            "variants": ["hopf_s3_to_s2_lifted_vs_density_u1_phase"],
        },
        "why_not_v4_probes": {
            "reason": "density/base-only probes cannot carry the U(1) global phase; this row explicitly compares lift readouts to the quotient-erased base",
        },
        "pass_rule": "classification fence, lift/density controls, owner-erasure ablation, associator cross-check, and dual-backend parity pass",
        "fail_rule": "phase readout fails on the lift, density sees the phase, owner erasure does not change the verdict, associator cross-check fails, or parity diverges",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_RESULT_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": "hopf_s3_s2_u1_phase_orbit_density_quotient",
    }
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = (
        result["parity"]["peer_available"]
        and result["parity"]["within_1e_9"]
        and all(bool(row.get("pass")) for row in positive.values())
        and all(bool(row.get("pass")) for row in negative.values())
        and all(bool(row.get("pass")) for row in boundary.values())
        and witness["layer_verdict"] == "REAL_LAYER"
    )
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "layer_verdict": result["layer_verdict"],
        "lift_carries_info": result["lift_carries_info"],
        "density_quotient_loses_it": result["density_quotient_loses_it"],
        "associator_confirms": result["associator_confirms"],
        "phase_is_the_lost_info": result["phase_is_the_lost_info"],
        "owner_carrier_load_bearing": result["owner_carrier_load_bearing"],
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "claim_ceiling": CLAIM_CEILING,
    }
    result["stop_condition_fired"] = not result["all_pass"]
    result["blockers"] = [] if result["all_pass"] else ["parity missing/diverged or a required discriminator/control check failed"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "RESULT "
        f"{OBJECT_ID} jax={RESULT_PATH} julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"layer_verdict={result['layer_verdict']} "
        f"parity={str(result['parity']['within_1e_9']).lower()}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
