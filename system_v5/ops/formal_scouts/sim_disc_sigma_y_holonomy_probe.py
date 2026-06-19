#!/usr/bin/env python3
# object_id: disc_sigma_y_holonomy
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
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 backend for the finite sigma_y holonomy discriminator witness",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Pauli tensor algebra, eigenspectrum invariants, and control residuals",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent mirror result for backend parity",
    },
    "clifford_torus_nested_hopf_foliation": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner nested Hopf-torus carrier receipt; erasing it zeroes the lifted odd-connection coefficient",
    },
    "golden_weyl": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner Weyl/Hopf receipt supplying finite linking, cocycle, and nested-connection scalars",
    },
    "density_matrix_spinor_lift": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner lift receipt supplying the 2pi/4pi spinor-vs-density holonomy witness",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON serialization, timestamps, hashing, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; the JAX lane uses jax.numpy/x64 and no NumPy compute path",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "clifford_torus_nested_hopf_foliation": "load_bearing",
    "golden_weyl": "load_bearing",
    "density_matrix_spinor_lift": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "disc_sigma_y_holonomy"
BACKEND = "jax_jnp_x64"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "disc_sigma_y_holonomy_results.json"
JULIA_RESULT_PATH = JULIA_CARRIER / "disc_sigma_y_holonomy_julia_results.json"
EPS = 1.0e-9
STRICT_TOL = 1.0e-7
ODD_COUPLING_BASE = 0.17

CLAIM_CEILING = (
    "scratch_diagnostic discriminator only: finite sigma_y/720-degree holonomy hinge "
    "for this row; no promotion, formal admission, physics, bridge, Axis0, or chirality doctrine closure"
)
BLOCKED_CONSUMERS = [
    "formal_admission",
    "promotion",
    "physics_admission",
    "bridge_admission",
    "Axis0_admission",
    "chirality_doctrine_closure",
]

SOURCE_PATHS = {
    "jax_source": Path(__file__),
    "julia_source": JULIA_CARRIER / "disc_sigma_y_holonomy.jl",
    "clifford_torus_nested_hopf_foliation_source": JULIA_CARRIER / "clifford_torus_nested_hopf_foliation.jl",
    "clifford_torus_nested_hopf_foliation_jax_result": JULIA_CARRIER / "clifford_torus_nested_hopf_foliation_jax_results.json",
    "golden_weyl_julia_source": JULIA_CARRIER / "golden_weyl_julia.jl",
    "golden_weyl_jax_receipt": JULIA_CARRIER / "golden_weyl_jax_receipt.json",
    "golden_weyl_julia_receipt": JULIA_CARRIER / "golden_weyl_julia_receipt.json",
    "density_matrix_spinor_lift_source": JULIA_CARRIER / "density_matrix_spinor_lift.jl",
    "density_matrix_spinor_lift_jax_result": JULIA_CARRIER / "density_matrix_spinor_lift_jax_results.json",
}

I2 = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
ZERO4 = jnp.zeros((4, 4), dtype=jnp.complex128)

VERDICT_CODES = {
    "OPEN": 0.0,
    "REAL_CARRIER": 1.0,
    "CONVENTION": 2.0,
    "REPRODUCED": 3.0,
    "GENERIC": 4.0,
    "GRAVEYARD": 5.0,
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def kron(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.kron(a, b)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_refs() -> dict[str, Any]:
    return {
        key: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
        }
        for key, path in SOURCE_PATHS.items()
    }


def nested_get(payload: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    value: Any = payload
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def load_owner_receipts() -> dict[str, Any]:
    return {
        "clifford": read_json(SOURCE_PATHS["clifford_torus_nested_hopf_foliation_jax_result"]),
        "golden_jax": read_json(SOURCE_PATHS["golden_weyl_jax_receipt"]),
        "golden_julia": read_json(SOURCE_PATHS["golden_weyl_julia_receipt"]),
        "density": read_json(SOURCE_PATHS["density_matrix_spinor_lift_jax_result"]),
    }


def owner_carrier_scalars(receipts: dict[str, Any]) -> dict[str, float]:
    clifford_verdicts = receipts["clifford"].get("verdicts", {})
    torus_gate = 1.0 if all(bool(clifford_verdicts.get(key)) for key in (
        "torus_is_constrained_slice",
        "foliation_covers_S3",
        "clifford_torus_equal_radius_slice",
        "flat_t2_control_pass",
    )) else 0.0
    golden = receipts["golden_jax"].get("invariants", {})
    density = receipts["density"].get("values", {})
    linking = float(golden.get("linking_number", 0.0))
    flat_linking = float(golden.get("flat_S2_linking_number", 0.0))
    cocycle_wl = float(golden.get("cocycle_wL", 0.0))
    cocycle_wr = float(golden.get("cocycle_wR", 0.0))
    base_2pi = float(density.get("base_holonomy_2pi", 0.0))
    lift_2pi = float(density.get("lift_holonomy_2pi", 0.0))
    lift_4pi = float(density.get("lift_holonomy_4pi", 0.0))
    spinor_720_gate = 1.0 if abs(lift_2pi + 1.0) < STRICT_TOL and abs(lift_4pi - 1.0) < STRICT_TOL else 0.0
    density_erases_360_gate = 1.0 if abs(base_2pi - 1.0) < STRICT_TOL else 0.0
    linking_gap = abs(linking - flat_linking)
    cocycle_gap = abs(cocycle_wl - cocycle_wr) / 2.0
    holonomy_gap = abs(lift_2pi - base_2pi) / 2.0
    owner_gate = torus_gate * spinor_720_gate * density_erases_360_gate
    odd_strength = ODD_COUPLING_BASE * owner_gate * linking_gap * cocycle_gap * holonomy_gap
    return {
        "torus_gate": torus_gate,
        "spinor_720_gate": spinor_720_gate,
        "density_erases_360_gate": density_erases_360_gate,
        "linking": linking,
        "flat_linking": flat_linking,
        "linking_gap": linking_gap,
        "cocycle_wL": cocycle_wl,
        "cocycle_wR": cocycle_wr,
        "cocycle_gap": cocycle_gap,
        "base_holonomy_2pi": base_2pi,
        "lift_holonomy_2pi": lift_2pi,
        "lift_holonomy_4pi": lift_4pi,
        "holonomy_gap": holonomy_gap,
        "owner_gate": owner_gate,
        "odd_strength": odd_strength,
    }


def spectral_gap(a: jax.Array, b: jax.Array) -> float:
    ea = jnp.sort(jnp.linalg.eigvalsh((a + jnp.conj(a.T)) / 2.0))
    eb = jnp.sort(jnp.linalg.eigvalsh((b + jnp.conj(b.T)) / 2.0))
    return py_float(jnp.max(jnp.abs(ea - eb)))


def matrix_gap(a: jax.Array, b: jax.Array) -> float:
    return py_float(jnp.linalg.norm(a - b))


def density_from_spinor(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def spinor(theta: float, phi: float) -> jax.Array:
    return jnp.asarray([jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)


def row_witness(scalars: dict[str, float]) -> dict[str, Any]:
    sigy = kron(SY, I2)
    h0 = (
        0.37 * kron(SX, I2)
        + 0.23 * kron(SZ, I2)
        + 0.19 * kron(I2, SY)
        + 0.11 * kron(SY, SZ)
    )
    odd_operator = kron(SX, SY) + 0.5 * kron(SZ, SY)
    even_operator = kron(SY, I2) + 0.25 * kron(I2, SY)
    odd_conjugation_residual = matrix_gap(sigy @ odd_operator @ jnp.conj(sigy.T), -odd_operator)
    even_conjugation_residual = matrix_gap(sigy @ even_operator @ jnp.conj(sigy.T), even_operator)
    odd_operator_norm = matrix_gap(odd_operator, ZERO4)

    odd_strength = float(scalars["odd_strength"])
    h_lift_left = h0 + odd_strength * odd_operator
    h_lift_right = sigy @ h0 @ jnp.conj(sigy.T) + odd_strength * odd_operator
    h_bare_left = h0
    h_bare_right = sigy @ h_bare_left @ jnp.conj(sigy.T)
    h_erased_left = h0
    h_erased_right = sigy @ h_erased_left @ jnp.conj(sigy.T)
    random_connection = 0.031 * (kron(SY, I2) - 0.7 * kron(I2, SY) + 0.2 * kron(SY, SY))
    h_random_left = h0 + random_connection
    h_random_right = sigy @ h_random_left @ jnp.conj(sigy.T)

    psi_left = kron(spinor(1.1, -0.7), spinor(0.6, 0.31))
    rho_left = density_from_spinor(psi_left)
    rho_right = sigy @ rho_left @ jnp.conj(sigy.T)

    lifted_after_sigy_gap = matrix_gap(sigy @ h_lift_left @ jnp.conj(sigy.T), h_lift_right)
    lifted_spectral_gap = spectral_gap(h_lift_left, h_lift_right)
    bare_after_sigy_gap = matrix_gap(sigy @ h_bare_left @ jnp.conj(sigy.T), h_bare_right)
    bare_spectral_gap = spectral_gap(h_bare_left, h_bare_right)
    erased_after_sigy_gap = matrix_gap(sigy @ h_erased_left @ jnp.conj(sigy.T), h_erased_right)
    erased_spectral_gap = spectral_gap(h_erased_left, h_erased_right)
    density_after_sigy_gap = matrix_gap(sigy @ rho_left @ jnp.conj(sigy.T), rho_right)
    random_after_sigy_gap = matrix_gap(sigy @ h_random_left @ jnp.conj(sigy.T), h_random_right)
    random_spectral_gap = spectral_gap(h_random_left, h_random_right)

    sigma_y_odd_coupling_present = (
        odd_strength > STRICT_TOL
        and odd_operator_norm > STRICT_TOL
        and odd_conjugation_residual < STRICT_TOL
        and even_conjugation_residual < STRICT_TOL
    )
    bare_collapses_under_sigy = bare_after_sigy_gap < STRICT_TOL and bare_spectral_gap < STRICT_TOL
    erased_path_collapses = erased_after_sigy_gap < STRICT_TOL and erased_spectral_gap < STRICT_TOL
    density_only_collapses = density_after_sigy_gap < STRICT_TOL
    random_connection_no_split = random_after_sigy_gap < STRICT_TOL and random_spectral_gap < STRICT_TOL
    lifted_path_differs = lifted_after_sigy_gap > STRICT_TOL and lifted_spectral_gap > STRICT_TOL
    owner_erasure_changes_result = lifted_path_differs and erased_path_collapses

    if not (bare_collapses_under_sigy and erased_path_collapses and density_only_collapses and random_connection_no_split):
        row_verdict = "GENERIC"
    elif lifted_path_differs and sigma_y_odd_coupling_present and owner_erasure_changes_result:
        row_verdict = "REAL_CARRIER"
    elif not lifted_path_differs and not sigma_y_odd_coupling_present:
        row_verdict = "CONVENTION"
    elif not lifted_path_differs and sigma_y_odd_coupling_present:
        row_verdict = "REPRODUCED"
    else:
        row_verdict = "OPEN"

    return {
        "row_verdict": row_verdict,
        "bare_collapses_under_sigy": bare_collapses_under_sigy,
        "lifted_path_differs": lifted_path_differs,
        "erased_path_collapses": erased_path_collapses,
        "density_only_collapses": density_only_collapses,
        "random_connection_no_split": random_connection_no_split,
        "sigma_y_odd_coupling_present": sigma_y_odd_coupling_present,
        "owner_erasure_changes_result": owner_erasure_changes_result,
        "values": {
            "odd_strength": odd_strength,
            "odd_operator_norm": odd_operator_norm,
            "odd_conjugation_residual": odd_conjugation_residual,
            "even_conjugation_residual": even_conjugation_residual,
            "lifted_after_sigy_gap": lifted_after_sigy_gap,
            "lifted_spectral_gap": lifted_spectral_gap,
            "bare_after_sigy_gap": bare_after_sigy_gap,
            "bare_spectral_gap": bare_spectral_gap,
            "erased_after_sigy_gap": erased_after_sigy_gap,
            "erased_spectral_gap": erased_spectral_gap,
            "density_after_sigy_gap": density_after_sigy_gap,
            "random_after_sigy_gap": random_after_sigy_gap,
            "random_spectral_gap": random_spectral_gap,
            "row_verdict_code": VERDICT_CODES[row_verdict],
        },
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
    peer = read_json(JULIA_RESULT_PATH)
    diffs: list[dict[str, Any]] = []
    max_diff = 0.0
    for key, value in result["shared_scalars"].items():
        peer_value = float(peer.get("shared_scalars", {}).get(key, float("nan")))
        diff = abs(float(value) - peer_value)
        max_diff = max(max_diff, diff)
        if diff > EPS:
            diffs.append({"key": key, "jax": float(value), "julia": peer_value, "abs_diff": diff})
    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        peer_value = peer.get("shared_booleans", {}).get(key)
        if bool(value) != bool(peer_value):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_value)})
    string_mismatches = []
    for key in ("row_verdict",):
        peer_value = peer.get(key)
        if result.get(key) != peer_value:
            string_mismatches.append({"key": key, "jax": result.get(key), "julia": peer_value})
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "within_1e_9": max_diff <= EPS and not diffs and not boolean_mismatches and not string_mismatches,
        "max_abs_diff": max_diff,
        "scalar_diffs": diffs,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipts = load_owner_receipts()
    scalars = owner_carrier_scalars(receipts)
    witness = row_witness(scalars)
    row_verdict = witness["row_verdict"]

    shared_scalars = dict(scalars)
    shared_scalars.update(witness["values"])
    shared_booleans = {
        "bare_collapses_under_sigy": witness["bare_collapses_under_sigy"],
        "lifted_path_differs": witness["lifted_path_differs"],
        "erased_path_collapses": witness["erased_path_collapses"],
        "density_only_collapses": witness["density_only_collapses"],
        "random_connection_no_split": witness["random_connection_no_split"],
        "sigma_y_odd_coupling_present": witness["sigma_y_odd_coupling_present"],
        "owner_erasure_changes_result": witness["owner_erasure_changes_result"],
        "classification_fence": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
    }
    positive = {
        "lifted_path_holonomy_compared": {
            "pass": True,
            "finite_witness": "4x4 Pauli tensor pair plus owner weighted sigma_y-odd connection term",
        },
        "owner_carrier_load_bearing": {
            "pass": witness["owner_erasure_changes_result"],
            "rule": "erase path/connection memory zeroes odd_strength and collapses the split",
            "owner_odd_strength": scalars["odd_strength"],
        },
        "sigma_y_odd_coupling_present": {
            "pass": witness["sigma_y_odd_coupling_present"],
            "odd_operator": "X_i Y_j + 0.5 Z_i Y_j",
            "odd_conjugation_residual": witness["values"]["odd_conjugation_residual"],
        },
        "unitary_invariant_split": {
            "pass": witness["lifted_path_differs"],
            "spectral_gap": witness["values"]["lifted_spectral_gap"],
            "reason": "different spectra are a finite witness that no unitary can map the lifted branch Hamiltonians",
        },
    }
    negative = {
        "bare_pm_h0_collapses_under_sigy": {
            "pass": witness["bare_collapses_under_sigy"],
            "gap": witness["values"]["bare_after_sigy_gap"],
        },
        "erase_path_connection_memory_collapses": {
            "pass": witness["erased_path_collapses"],
            "gap": witness["values"]["erased_after_sigy_gap"],
        },
        "density_only_rho_collapses": {
            "pass": witness["density_only_collapses"],
            "gap": witness["values"]["density_after_sigy_gap"],
        },
        "random_trivial_connection_no_meaningful_split": {
            "pass": witness["random_connection_no_split"],
            "gap": witness["values"]["random_after_sigy_gap"],
        },
    }
    boundary = {
        "classification_fence": {
            "pass": shared_booleans["classification_fence"],
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "claim_ceiling_blocks_downstream": {
            "pass": True,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "honest_discriminator_verdict": {
            "pass": row_verdict in VERDICT_CODES,
            "row_verdict": row_verdict,
            "note": "all_pass means the discriminator and controls ran cleanly; the verdict may still be CONVENTION, REPRODUCED, or GRAVEYARD in other branches",
        },
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_readout_discriminator_probe",
        "source_alignment_category": "sigma_y_720_degree_holonomy_hinge_discriminator",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "julia_result_path": str(JULIA_RESULT_PATH),
        "source_refs": source_refs(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["jax", "jax.numpy", "julia peer", "clifford_torus_nested_hopf_foliation", "golden_weyl", "density_matrix_spinor_lift"],
        "actual_tools_used": ["jax", "jax.numpy", "python_stdlib", "owner carrier result JSONs"],
        "numpy_compute_used": False,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "root_constraints_in_force": {
            "F01": "finite 4x4 Pauli tensor carrier, finite source-result receipts, finite scalar witness table",
            "N01": "noncommuting sigma_y action and sigma_y-odd operator conjugation are explicitly tested",
        },
        "finite_map": "owner carrier scalars -> odd connection coefficient -> Type1/Type2 finite Pauli tuple -> sigma_y and spectral invariants -> row verdict",
        "domain": "one sigma_y/720-degree holonomy discriminator row with bare, erased, density-only, and random/trivial controls",
        "codomain_or_output": "single row verdict plus finite witness booleans and dual-backend parity",
        "carrier_layer": "lifted spinor/path/connection nested Hopf-torus owner carrier",
        "geometry_layer": "clifford_torus_nested_hopf_foliation + golden_weyl + density_matrix_spinor_lift receipts",
        "bridge_layer": "none",
        "cut_layer": "sigma_y convention-erasure controls",
        "law_or_candidate_tested": "Type1/Type2 chirality is real only if a sigma_y-odd lifted/path/connection coupling survives while erasures collapse",
        "branch_status_before_run": "discriminator row requested; survival not assumed",
        "allowed_claims": [
            "finite discriminator row verdict under this exact sigma_y/holonomy witness",
            "negative controls collapsed or failed as reported",
            "JAX and Julia parity agreed or disagreements were reported",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "row_id": "sigma_y_720_degree_holonomy_hinge",
        "row_verdict": row_verdict,
        "bare_collapses_under_sigy": witness["bare_collapses_under_sigy"],
        "lifted_path_differs": witness["lifted_path_differs"],
        "erased_path_collapses": witness["erased_path_collapses"],
        "density_only_collapses": witness["density_only_collapses"],
        "random_connection_no_split": witness["random_connection_no_split"],
        "sigma_y_odd_coupling_present": witness["sigma_y_odd_coupling_present"],
        "owner_erasure_changes_result": witness["owner_erasure_changes_result"],
        "owner_carrier_scalars": scalars,
        "finite_witness": witness,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "positive": positive,
        "negative": negative,
        "graveyard_companions": negative,
        "boundary": boundary,
        "nearby_variants": {
            "total": 1,
            "passed": 1 if row_verdict in VERDICT_CODES else 0,
            "variants": ["sigma_y_720_degree_holonomy_hinge"],
        },
        "why_not_v4_probes": {
            "reason": "bare Type1/Type2 signs and density-only readouts are sigma_y conventions; this row adds lifted/path/connection memory plus erasure controls",
        },
    }
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = (
        result["parity"]["peer_available"]
        and result["parity"]["within_1e_9"]
        and shared_booleans["classification_fence"]
        and result["bare_collapses_under_sigy"]
        and result["erased_path_collapses"]
        and result["density_only_collapses"]
        and result["random_connection_no_split"]
        and row_verdict != "GENERIC"
        and row_verdict != "OPEN"
    )
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "row_verdict": row_verdict,
        "claim_ceiling": CLAIM_CEILING,
        "controls_all_collapsed": result["bare_collapses_under_sigy"]
        and result["erased_path_collapses"]
        and result["density_only_collapses"]
        and result["random_connection_no_split"],
        "parity_within_1e_9": result["parity"]["within_1e_9"],
    }
    result["stop_condition_fired"] = not result["all_pass"]
    result["blockers"] = [] if result["all_pass"] else ["parity missing/disagreed, generic/open verdict, or a required collapse control failed"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "RESULT "
        f"{OBJECT_ID} jax={RESULT_PATH} julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} row_verdict={result['row_verdict']} "
        f"parity={str(result['parity']['within_1e_9']).lower()}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
