#!/usr/bin/env python3
"""JAX density-operator terrain/sign probe over D(C^2).

This is the corrected Hilbert-space-only operator object:

    density operator -> projection/unitary channel -> terrain composition
    -> noncommuting signed difference.

The signed operators are not primitive channels. They are four primitive
Hilbert-space maps, each with two ordered placements against a terrain channel:
plus = Phi_tau o O, minus = O o Phi_tau.

It does not use coordinate-vector geometry. It does not run Julia or PyTorch.
It does not promote any layer, terrain, G-structure, flux, Axis0, FEP, physics,
or final manifold claim.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


RESULT = Path("system_v5/ops/formal_scouts/results/jax_density_operator_terrain_signed_commutator_probe_results.json")

CTYPE = jnp.complex128
RTYPE = jnp.float64
EPS = 1.0e-11

I2 = jnp.eye(2, dtype=CTYPE)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=CTYPE)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=CTYPE)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=CTYPE)

P0 = 0.5 * (I2 + SZ)
P1 = 0.5 * (I2 - SZ)
QP = 0.5 * (I2 + SX)
QM = 0.5 * (I2 - SX)

Q_BASE = jnp.asarray(0.37, dtype=RTYPE)
THETA = jnp.asarray(0.61, dtype=RTYPE)
PHI = jnp.asarray(-0.43, dtype=RTYPE)
KAPPA_I = jnp.asarray(0.71, dtype=RTYPE)
KAPPA_E = jnp.asarray(0.83, dtype=RTYPE)
TIME_T = jnp.asarray(1.25, dtype=RTYPE)

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "layer_stacking_readiness",
    "noncommutative_layer_order_claim",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics_gravity",
    "final_manifold_admission",
]


def _jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def dagger(x: jax.Array) -> jax.Array:
    return jnp.conj(jnp.swapaxes(x, -1, -2))


def hermitize(rho: jax.Array) -> jax.Array:
    return 0.5 * (rho + dagger(rho))


def normalize_density(rho: jax.Array) -> jax.Array:
    rho = hermitize(rho)
    return rho / jnp.trace(rho)


def hs_norm_sq(x: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(dagger(x) @ x))


def density_health(rho: jax.Array) -> dict[str, Any]:
    vals = jnp.linalg.eigvalsh(hermitize(rho))
    return {
        "trace_gap": jnp.abs(jnp.trace(rho) - 1.0),
        "hermitian_gap": jnp.max(jnp.abs(rho - dagger(rho))),
        "min_eval": jnp.min(jnp.real(vals)),
        "pass": bool(jnp.abs(jnp.trace(rho) - 1.0) < EPS and jnp.max(jnp.abs(rho - dagger(rho))) < EPS and jnp.min(jnp.real(vals)) > -EPS),
    }


def pinch_i(rho: jax.Array) -> jax.Array:
    return P0 @ rho @ P0 + P1 @ rho @ P1


def pinch_e(rho: jax.Array) -> jax.Array:
    return QP @ rho @ QP + QM @ rho @ QM


def channel_t_i(rho: jax.Array, q: jax.Array = Q_BASE) -> jax.Array:
    return normalize_density((1.0 - q) * rho + q * pinch_i(rho))


def channel_t_e(rho: jax.Array, q: jax.Array = Q_BASE) -> jax.Array:
    return normalize_density((1.0 - q) * rho + q * pinch_e(rho))


def unitary_x(theta: jax.Array = THETA) -> jax.Array:
    return jnp.cos(theta / 2.0) * I2 - 1j * jnp.sin(theta / 2.0) * SX


def unitary_z(phi: jax.Array = PHI) -> jax.Array:
    return jnp.cos(phi / 2.0) * I2 - 1j * jnp.sin(phi / 2.0) * SZ


def adjoint_channel(unitary: jax.Array, rho: jax.Array) -> jax.Array:
    return normalize_density(unitary @ rho @ dagger(unitary))


def channel_f_i(rho: jax.Array) -> jax.Array:
    return adjoint_channel(unitary_x(), rho)


def channel_f_e(rho: jax.Array) -> jax.Array:
    return adjoint_channel(unitary_z(), rho)


def d_t_i(rho: jax.Array) -> jax.Array:
    return hs_norm_sq(rho - pinch_i(rho))


def d_t_e(rho: jax.Array) -> jax.Array:
    return hs_norm_sq(rho - pinch_e(rho))


def flow_t_i(rho: jax.Array, t: jax.Array = TIME_T) -> jax.Array:
    decay = jnp.exp(-KAPPA_I * t)
    return normalize_density(pinch_i(rho) + decay * (rho - pinch_i(rho)))


def flow_t_e(rho: jax.Array, t: jax.Array = TIME_T) -> jax.Array:
    decay = jnp.exp(-KAPPA_E * t)
    return normalize_density(pinch_e(rho) + decay * (rho - pinch_e(rho)))


def terrain_se(rho: jax.Array) -> jax.Array:
    r1 = adjoint_channel(unitary_x(jnp.asarray(0.36, dtype=RTYPE)), rho)
    r2 = channel_t_e(r1, jnp.asarray(0.29, dtype=RTYPE))
    return adjoint_channel(unitary_z(jnp.asarray(0.47, dtype=RTYPE)), r2)


def terrain_ne(rho: jax.Array) -> jax.Array:
    return adjoint_channel(unitary_x(jnp.asarray(-0.52, dtype=RTYPE)), channel_t_i(rho, jnp.asarray(0.31, dtype=RTYPE)))


def terrain_ni(rho: jax.Array) -> jax.Array:
    r1 = adjoint_channel(unitary_z(jnp.asarray(0.22, dtype=RTYPE)), rho)
    r2 = channel_t_i(r1, jnp.asarray(0.27, dtype=RTYPE))
    return adjoint_channel(unitary_x(jnp.asarray(0.39, dtype=RTYPE)), r2)


def terrain_si(rho: jax.Array) -> jax.Array:
    return adjoint_channel(unitary_z(jnp.asarray(-0.58, dtype=RTYPE)), channel_t_e(rho, jnp.asarray(0.33, dtype=RTYPE)))


TERRAIN: dict[str, Callable[[jax.Array], jax.Array]] = {
    "Se": terrain_se,
    "Ne": terrain_ne,
    "Ni": terrain_ni,
    "Si": terrain_si,
}

OPERATORS: dict[str, Callable[[jax.Array], jax.Array]] = {
    "Ti": channel_t_i,
    "Te": channel_t_e,
    "Fi": channel_f_i,
    "Fe": channel_f_e,
}

# These are the eight signed operator families. They are ordered placements of
# four primitive maps, not eight primitive maps.
SIGNED_OPERATOR_FAMILIES = [
    {"operator": "Ti", "sign": "+", "map": "rho -> Phi_tau(Ti(rho))"},
    {"operator": "Ti", "sign": "-", "map": "rho -> Ti(Phi_tau(rho))"},
    {"operator": "Te", "sign": "+", "map": "rho -> Phi_tau(Te(rho))"},
    {"operator": "Te", "sign": "-", "map": "rho -> Te(Phi_tau(rho))"},
    {"operator": "Fi", "sign": "+", "map": "rho -> Phi_tau(Fi(rho))"},
    {"operator": "Fi", "sign": "-", "map": "rho -> Fi(Phi_tau(rho))"},
    {"operator": "Fe", "sign": "+", "map": "rho -> Phi_tau(Fe(rho))"},
    {"operator": "Fe", "sign": "-", "map": "rho -> Fe(Phi_tau(rho))"},
]

# Native terrain/operator pairings. Other pairings are controls/adapters unless
# an explicit conjugation/frame map is declared.
SIGNED_PAIRS = [
    ("Se", "Ti"),
    ("Se", "Fi"),
    ("Ne", "Ti"),
    ("Ne", "Fi"),
    ("Ni", "Te"),
    ("Ni", "Fe"),
    ("Si", "Te"),
    ("Si", "Fe"),
]


def finite_density_inputs() -> list[jax.Array]:
    rows = []
    params = [
        (0.31, 0.17, 0.08),
        (0.42, -0.73, 0.15),
        (0.57, 1.11, 0.22),
        (0.66, -1.37, 0.12),
        (0.49, 2.03, 0.18),
    ]
    for angle, phase, mix in params:
        a = jnp.asarray(angle, dtype=RTYPE)
        p = jnp.asarray(phase, dtype=RTYPE)
        m = jnp.asarray(mix, dtype=RTYPE)
        psi = jnp.asarray([jnp.cos(a), jnp.exp(1j * p) * jnp.sin(a)], dtype=CTYPE)
        pure = jnp.outer(psi, jnp.conj(psi))
        rows.append(normalize_density((1.0 - m) * pure + m * I2 / 2.0))
    return rows


def signed_pair_row(tau: str, op_name: str, inputs: list[jax.Array]) -> dict[str, Any]:
    phi_tau = TERRAIN[tau]
    op = OPERATORS[op_name]
    delta_norms = []
    plus_health = []
    minus_health = []
    delta_trace_gaps = []
    delta_hermitian_gaps = []
    for rho in inputs:
        plus = phi_tau(op(rho))
        minus = op(phi_tau(rho))
        delta = plus - minus
        delta_norms.append(jnp.sqrt(jnp.maximum(hs_norm_sq(delta), 0.0)))
        plus_health.append(density_health(plus))
        minus_health.append(density_health(minus))
        delta_trace_gaps.append(jnp.abs(jnp.trace(delta)))
        delta_hermitian_gaps.append(jnp.max(jnp.abs(delta - dagger(delta))))
    max_delta = jnp.max(jnp.asarray(delta_norms, dtype=RTYPE))
    min_delta = jnp.min(jnp.asarray(delta_norms, dtype=RTYPE))
    return {
        "terrain": tau,
        "operator": op_name,
        "plus": f"{tau}{op_name}+ = Phi_{tau} o {op_name}",
        "minus": f"{tau}{op_name}- = {op_name} o Phi_{tau}",
        "signed_difference": f"Delta_{tau}_{op_name}(rho)=Phi_{tau}({op_name}(rho))-{op_name}(Phi_{tau}(rho))",
        "max_delta_hs_norm": max_delta,
        "min_delta_hs_norm": min_delta,
        "plus_density_valid": all(row["pass"] for row in plus_health),
        "minus_density_valid": all(row["pass"] for row in minus_health),
        "delta_trace_zero": jnp.max(jnp.asarray(delta_trace_gaps, dtype=RTYPE)) < EPS,
        "delta_hermitian": jnp.max(jnp.asarray(delta_hermitian_gaps, dtype=RTYPE)) < EPS,
        "unique_noncommuting_readout": max_delta > 1.0e-5,
    }


def spectra(rho: jax.Array) -> jax.Array:
    return jnp.sort(jnp.real(jnp.linalg.eigvalsh(hermitize(rho))))


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    inputs = finite_density_inputs()

    decay_rows = []
    spectrum_rows = []
    for index, rho in enumerate(inputs):
        ti_left = d_t_i(flow_t_i(rho))
        ti_right = jnp.exp(-2.0 * KAPPA_I * TIME_T) * d_t_i(rho)
        te_left = d_t_e(flow_t_e(rho))
        te_right = jnp.exp(-2.0 * KAPPA_E * TIME_T) * d_t_e(rho)
        decay_rows.append(
            {
                "input_index": index,
                "D_Ti_flow": ti_left,
                "D_Ti_expected": ti_right,
                "D_Ti_abs_error": jnp.abs(ti_left - ti_right),
                "D_Te_flow": te_left,
                "D_Te_expected": te_right,
                "D_Te_abs_error": jnp.abs(te_left - te_right),
            }
        )
        spectrum_rows.append(
            {
                "input_index": index,
                "Fi_spectrum_error": jnp.max(jnp.abs(spectra(channel_f_i(rho)) - spectra(rho))),
                "Fe_spectrum_error": jnp.max(jnp.abs(spectra(channel_f_e(rho)) - spectra(rho))),
            }
        )

    signed_rows = [signed_pair_row(tau, op_name, inputs) for tau, op_name in SIGNED_PAIRS]
    signed_variant_rows = []
    for row in signed_rows:
        signed_variant_rows.append({"terrain": row["terrain"], "operator": row["operator"], "sign": "+", "map": row["plus"]})
        signed_variant_rows.append({"terrain": row["terrain"], "operator": row["operator"], "sign": "-", "map": row["minus"]})

    identity_delta_controls = []
    for op_name, op in OPERATORS.items():
        norms = []
        for rho in inputs:
            norms.append(jnp.sqrt(jnp.maximum(hs_norm_sq(op(rho) - op(rho)), 0.0)))
        identity_delta_controls.append({"operator": op_name, "max_delta_hs_norm": jnp.max(jnp.asarray(norms, dtype=RTYPE))})

    commuting_controls = []
    commuting_specs: list[tuple[str, Callable[[jax.Array], jax.Array], Callable[[jax.Array], jax.Array]]] = [
        ("Ti_with_z_pinching", channel_t_i, lambda rho: channel_t_i(rho, jnp.asarray(0.19, dtype=RTYPE))),
        ("Te_with_x_pinching", channel_t_e, lambda rho: channel_t_e(rho, jnp.asarray(0.23, dtype=RTYPE))),
        ("Fi_with_x_unitary", channel_f_i, lambda rho: adjoint_channel(unitary_x(jnp.asarray(-0.21, dtype=RTYPE)), rho)),
        ("Fe_with_z_unitary", channel_f_e, lambda rho: adjoint_channel(unitary_z(jnp.asarray(0.24, dtype=RTYPE)), rho)),
    ]
    for name, op, phi in commuting_specs:
        norms = []
        for rho in inputs:
            norms.append(jnp.sqrt(jnp.maximum(hs_norm_sq(phi(op(rho)) - op(phi(rho))), 0.0)))
        commuting_controls.append({"name": name, "max_delta_hs_norm": jnp.max(jnp.asarray(norms, dtype=RTYPE))})

    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_coordinate_word_absent = ("bl" + "och") not in source_text.lower()

    checks = {
        "finite_density_inputs_valid": all(density_health(rho)["pass"] for rho in inputs),
        "base_channels_preserve_density": all(
            density_health(op(rho))["pass"] for rho in inputs for op in OPERATORS.values()
        ),
        "terrain_maps_preserve_density": all(
            density_health(phi(rho))["pass"] for rho in inputs for phi in TERRAIN.values()
        ),
        "four_primitive_maps_only": len(OPERATORS) == 4,
        "signed_operator_family_count_is_8": len(SIGNED_OPERATOR_FAMILIES) == 8,
        "native_terrain_operator_row_count_is_8": len(signed_rows) == 8,
        "D_Ti_semigroup_decay": max(row["D_Ti_abs_error"] for row in decay_rows) < 1.0e-10,
        "D_Te_semigroup_decay": max(row["D_Te_abs_error"] for row in decay_rows) < 1.0e-10,
        "Fi_spectrum_preserved": max(row["Fi_spectrum_error"] for row in spectrum_rows) < 1.0e-10,
        "Fe_spectrum_preserved": max(row["Fe_spectrum_error"] for row in spectrum_rows) < 1.0e-10,
        "concrete_signed_terrain_placement_count_is_16": len(signed_variant_rows) == 16,
        "all_signed_outputs_valid_densities": all(row["plus_density_valid"] and row["minus_density_valid"] for row in signed_rows),
        "all_signed_differences_traceless_hermitian": all(row["delta_trace_zero"] and row["delta_hermitian"] for row in signed_rows),
        "all_signed_differences_nonzero": all(row["unique_noncommuting_readout"] for row in signed_rows),
        "identity_composition_control_zero": max(row["max_delta_hs_norm"] for row in identity_delta_controls) < EPS,
        "commuting_composition_controls_zero": max(row["max_delta_hs_norm"] for row in commuting_controls) < EPS,
        "coordinate_vector_word_absent_from_source": forbidden_coordinate_word_absent,
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    audit_pass = all(bool(v) for v in checks.values())

    out = {
        "sim_id": "jax_density_operator_terrain_signed_commutator_probe",
        "name": "JAX density-operator terrain signed commutator probe",
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "formal_scout",
        "sim_class": "density_operator_channel_order_probe",
        "sim_execution_kind": "diagnostic_jax_density_operator_formal_scout",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "purpose": "Implement the corrected Hilbert-space density-operator object for terrain/operator signed differences.",
        "scientific_question": "Do finite density-operator terrain maps make the signed variants unique only through noncommuting composition with Ti/Te/Fi/Fe?",
        "root_constraints_in_force": {
            "F01": "finite density states in D(C^2), finite projectors, finite unitary channels, finite terrain maps, finite signed rows",
            "N01": "signed readout is [Phi_tau,O](rho), with commuting and identity controls required to vanish",
        },
        "finite_map": "rho in D(C^2) -> O(rho) -> Phi_tau(O(rho)) and O(Phi_tau(rho)) -> Delta_{tau,O}(rho)",
        "domain": {
            "carrier": "D(C^2)",
            "primitive_operator_maps": ["Ti", "Te", "Fi", "Fe"],
            "signed_operator_families": SIGNED_OPERATOR_FAMILIES,
            "terrain_maps": ["Se", "Ne", "Ni", "Si"],
            "native_terrain_operator_pairings": SIGNED_PAIRS,
            "terrain_admissibility": {
                "Se": ["Ti", "Fi"],
                "Ne": ["Ti", "Fi"],
                "Ni": ["Te", "Fe"],
                "Si": ["Te", "Fe"],
            },
            "non_native_pairings": "controls/adapters only unless an explicit conjugation or frame map is declared",
        },
        "codomain_or_output": "eight signed operator families from four primitive maps, eight native terrain/operator rows, sixteen concrete terrain-signed placements, and Hilbert-Schmidt order-gap norms",
        "carrier_layer": "finite Hilbert-space density operators",
        "geometry_layer": "operator/terrain composition order only",
        "carrier_realization": "JAX complex128 2x2 density matrices; no coordinate-vector carrier; no Julia runtime; no PyTorch",
        "peps3d_embedding": "not claimed; PEPS3D carrier admission remains blocked",
        "spinor_state": "not claimed here; density-operator carrier only",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "law_or_candidate_tested": "Delta_{tau,O}(rho)=Phi_tau(O(rho))-O(Phi_tau(rho)); +=Phi_tau o O; -=O o Phi_tau; signs are ordered compositions, not scalar addition/subtraction",
        "allowed_claims": [
            "the corrected JAX density-operator channel object runs and passes local finite controls",
            "the operator object uses four primitive Hilbert-space maps and two ordered placements, not eight primitive channels",
            "Ti/Te distance functionals decay under their own semigroups with e^{-2 kappa t}",
            "Fi/Fe preserve the spectrum of rho",
            "signed variants are unique only when [Phi_tau,O]rho is nonzero",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["density-operator-only operator/terrain scout hardening"],
        "promotion_blockers": [
            "formal scout only",
            "no PEPS3D carrier cell/tensor/channel admission packet",
            "no official G-structure selection",
            "no layer stacking readiness",
            "no flux, Axis0, FEP, physics, or final manifold admission",
        ],
        "operator_definitions": {
            "Ti": "(1-q)rho + q(P0 rho P0 + P1 rho P1)",
            "Te": "(1-q)rho + q(Q+ rho Q+ + Q- rho Q-)",
            "Fi": "Ux(theta) rho Ux(theta)^dagger",
            "Fe": "Uz(phi) rho Uz(phi)^dagger",
            "D_Ti": "||rho-(P0 rho P0 + P1 rho P1)||_2^2",
            "D_Te": "||rho-(Q+ rho Q+ + Q- rho Q-)||_2^2",
            "Delta_tau_O": "Phi_tau(O(rho))-O(Phi_tau(rho))",
            "G_tau_O_optional": "||Delta_tau_O(rho)||_HS^2; custom_vjp only needed when differentiating this objective",
        },
        "required_tools": ["jax", "python_stdlib"],
        "actual_tools_used": ["jax", "python_stdlib"],
        "TOOL_MANIFEST": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes finite density channels, semigroup checks, spectra, signed differences, and controls.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing and source-boundary scan.",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes finite density channels, semigroup checks, spectra, signed differences, and controls.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing and source-boundary scan.",
            },
        },
        "tool_integration_depth": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "checks": checks,
        "metrics": {
            "max_D_Ti_decay_error": max(row["D_Ti_abs_error"] for row in decay_rows),
            "max_D_Te_decay_error": max(row["D_Te_abs_error"] for row in decay_rows),
            "max_Fi_spectrum_error": max(row["Fi_spectrum_error"] for row in spectrum_rows),
            "max_Fe_spectrum_error": max(row["Fe_spectrum_error"] for row in spectrum_rows),
            "min_signed_delta_hs_norm": min(row["min_delta_hs_norm"] for row in signed_rows),
            "max_signed_delta_hs_norm": max(row["max_delta_hs_norm"] for row in signed_rows),
            "max_identity_control_delta": max(row["max_delta_hs_norm"] for row in identity_delta_controls),
            "max_commuting_control_delta": max(row["max_delta_hs_norm"] for row in commuting_controls),
        },
        "signed_operator_families": SIGNED_OPERATOR_FAMILIES,
        "native_terrain_operator_pair_rows": signed_rows,
        "concrete_signed_terrain_placements": signed_variant_rows,
        "semigroup_decay_rows": decay_rows,
        "spectrum_rows": spectrum_rows,
        "identity_delta_controls": identity_delta_controls,
        "commuting_controls": commuting_controls,
        "claim_boundary": "Density-operator formal scout only; no layer completion, stacking readiness, official G-structure selection, flux, Axis0, FEP, physics, or final admission.",
    }
    RESULT.write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "density_operator_terrain_signed_commutator "
        f"AUDIT_PASS={audit_pass} pairs={len(signed_rows)} variants={len(signed_variant_rows)} "
        f"min_delta={float(out['metrics']['min_signed_delta_hs_norm']):.6e} "
        f"path={RESULT}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
