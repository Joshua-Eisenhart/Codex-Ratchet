#!/usr/bin/env python3
"""JAX-only flux direction + impedance falsifier.

This is a diagnostic repair candidate, not an official layer repair.  It reads no
Julia files at runtime and imports no PyTorch.  The finite carrier is a qubit
density matrix.  Flux is measured as a signed order-commutator current for two
noncommuting channel factors, and impedance is measured from trace-distance
decay under the same finite flow family.
"""

from __future__ import annotations

import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


SIM_ID = "jax_flux_impedance_falsifier"
RESULT_PATH = Path(__file__).with_name("jax_flux_impedance_falsifier_results.json")

STEPS = 64
ALPHA = 0.73
BETA = 0.62
P_OPEN = 0.12
P_CLOSED = 0.025

C = jnp.complex128
I2 = jnp.eye(2, dtype=C)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=C)
SY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=C)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=C)

RHO_Z_PLUS = jnp.array([[1.0, 0.0], [0.0, 0.0]], dtype=C)
RHO_X_PLUS = 0.5 * (I2 + SX)
RHO_X_MINUS = 0.5 * (I2 - SX)
RHO_MIXED = 0.5 * I2

TERRAINS = [
    {"sheet": "L", "topo": "Se", "name": "Funnel", "chi": +1.0, "open": True},
    {"sheet": "L", "topo": "Ne", "name": "Vortex", "chi": +1.0, "open": False},
    {"sheet": "L", "topo": "Ni", "name": "Pit", "chi": +1.0, "open": True},
    {"sheet": "L", "topo": "Si", "name": "Hill", "chi": +1.0, "open": False},
    {"sheet": "R", "topo": "Se", "name": "Cannon", "chi": -1.0, "open": True},
    {"sheet": "R", "topo": "Ne", "name": "Spiral", "chi": -1.0, "open": False},
    {"sheet": "R", "topo": "Ni", "name": "Source", "chi": -1.0, "open": True},
    {"sheet": "R", "topo": "Si", "name": "Citadel", "chi": -1.0, "open": False},
]


def unitary_x(theta):
    return jnp.cos(theta / 2.0) * I2 - 1.0j * jnp.sin(theta / 2.0) * SX


def unitary_z(theta):
    return jnp.cos(theta / 2.0) * I2 - 1.0j * jnp.sin(theta / 2.0) * SZ


def conj(U, rho):
    return U @ rho @ jnp.conjugate(U.T)


def depolarize(rho, p):
    return (1.0 - p) * rho + p * RHO_MIXED


def ordered_step(rho, chi, p):
    """Noncommuting order: Ux then chirality-signed Uz, then finite damping."""
    rho1 = conj(unitary_x(BETA), rho)
    rho2 = conj(unitary_z(chi * ALPHA), rho1)
    return depolarize(rho2, p)


def shuffled_step(rho, chi, p):
    """Order-shuffled control: Uz then Ux, then the same finite damping."""
    rho1 = conj(unitary_z(chi * ALPHA), rho)
    rho2 = conj(unitary_x(BETA), rho1)
    return depolarize(rho2, p)


def commuting_ordered_step(rho, chi, p):
    """Commuting negative: both channel factors are z-rotations."""
    rho1 = conj(unitary_z(BETA), rho)
    rho2 = conj(unitary_z(chi * ALPHA), rho1)
    return depolarize(rho2, p)


def commuting_shuffled_step(rho, chi, p):
    rho1 = conj(unitary_z(chi * ALPHA), rho)
    rho2 = conj(unitary_z(BETA), rho1)
    return depolarize(rho2, p)


def hs_norm(a):
    return jnp.sqrt(jnp.maximum(jnp.real(jnp.trace(jnp.conjugate(a.T) @ a)), 0.0))


def trace_drift(rho):
    return jnp.abs(jnp.trace(rho) - 1.0)


def hermitian_drift(rho):
    return hs_norm(rho - jnp.conjugate(rho.T))


def flux_current(ordered, shuffled):
    # Signed current of the order commutator.  This is zero if the channel
    # factors commute or if the input is the maximally mixed product state.
    return jnp.real(jnp.trace(SY @ (ordered - shuffled)))


@jax.jit
def evolve_flux(rho0, chi, p):
    def body(rho, _):
        ordered = ordered_step(rho, chi, p)
        shuffled = shuffled_step(rho, chi, p)
        current = flux_current(ordered, shuffled)
        shuffle_gap = hs_norm(ordered - shuffled)
        return ordered, (current, shuffle_gap, trace_drift(ordered), hermitian_drift(ordered))

    final_rho, (currents, shuffle_gaps, trace_drifts, herm_drifts) = jax.lax.scan(
        body, rho0, xs=None, length=STEPS
    )
    evals = jnp.linalg.eigvalsh(0.5 * (final_rho + jnp.conjugate(final_rho.T)))
    return {
        "flux": jnp.sum(currents),
        "mean_abs_current": jnp.mean(jnp.abs(currents)),
        "min_shuffle_gap": jnp.min(shuffle_gaps),
        "max_trace_drift": jnp.max(trace_drifts),
        "max_hermitian_drift": jnp.max(herm_drifts),
        "min_final_eigenvalue": jnp.min(jnp.real(evals)),
    }


@jax.jit
def evolve_flux_swapped_readout(rho0, chi, p):
    def body(rho, _):
        ordered = ordered_step(rho, chi, p)
        shuffled = shuffled_step(rho, chi, p)
        current = flux_current(shuffled, ordered)
        return shuffled, current

    _, currents = jax.lax.scan(body, rho0, xs=None, length=STEPS)
    return jnp.sum(currents)


@jax.jit
def evolve_flux_commuting_negative(rho0, chi, p):
    def body(rho, _):
        ordered = commuting_ordered_step(rho, chi, p)
        shuffled = commuting_shuffled_step(rho, chi, p)
        current = flux_current(ordered, shuffled)
        return ordered, current

    _, currents = jax.lax.scan(body, rho0, xs=None, length=STEPS)
    return jnp.sum(currents)


@jax.jit
def estimate_impedance(chi, p, use_shuffled):
    def step_pair(pair, _):
        a, b = pair
        next_a_ordered = ordered_step(a, chi, p)
        next_b_ordered = ordered_step(b, chi, p)
        next_a_shuffled = shuffled_step(a, chi, p)
        next_b_shuffled = shuffled_step(b, chi, p)
        next_a = jax.lax.select(use_shuffled, next_a_shuffled, next_a_ordered)
        next_b = jax.lax.select(use_shuffled, next_b_shuffled, next_b_ordered)
        return (next_a, next_b), hs_norm(next_a - next_b)

    d0 = hs_norm(RHO_X_PLUS - RHO_X_MINUS)
    (_, _), distances = jax.lax.scan(step_pair, (RHO_X_PLUS, RHO_X_MINUS), xs=None, length=STEPS)
    d_final = distances[-1]
    gamma = jnp.where(d_final > 1e-14, -jnp.log(d_final / d0) / STEPS, jnp.inf)
    gamma = jnp.where(jnp.abs(gamma) < 1e-12, 0.0, gamma)
    impedance = jnp.where(gamma > 1e-12, 1.0 / gamma, jnp.inf)
    return gamma, impedance, d0, d_final


def f64(x):
    y = jax.device_get(x)
    if bool(jnp.isinf(y)):
        return "Inf"
    return float(y)


def sign_label(x, eps=1e-7):
    value = float(jax.device_get(x))
    if value > eps:
        return +1
    if value < -eps:
        return -1
    return 0


def rounded_float(x, digits=10):
    value = f64(x)
    if value == "Inf":
        return value
    return round(value, digits)


def terrain_probability(row):
    return P_OPEN if row["open"] else P_CLOSED


def main():
    per_terrain = {}
    fluxes = []
    signs = []
    impedances = []

    for row in TERRAINS:
        p = terrain_probability(row)
        metrics = evolve_flux(RHO_Z_PLUS, row["chi"], p)
        gamma, impedance, d0, d_final = estimate_impedance(row["chi"], p, False)
        gamma_shuf, impedance_shuf, _, d_final_shuf = estimate_impedance(row["chi"], p, True)
        swapped_flux = evolve_flux_swapped_readout(RHO_Z_PLUS, row["chi"], p)
        sign = sign_label(metrics["flux"])
        fluxes.append(float(jax.device_get(metrics["flux"])))
        signs.append(sign)
        impedances.append(float(jax.device_get(impedance)))
        per_terrain[row["name"]] = {
            "sheet": row["sheet"],
            "topology": row["topo"],
            "class": "open/isothermal" if row["open"] else "closed/adiabatic",
            "chirality": "L(+)" if row["chi"] > 0 else "R(-)",
            "depolarizing_probability": p,
            "flux": rounded_float(metrics["flux"]),
            "flux_sign": sign,
            "mean_abs_order_current": rounded_float(metrics["mean_abs_current"]),
            "min_order_shuffle_gap": rounded_float(metrics["min_shuffle_gap"]),
            "swapped_order_flux": rounded_float(swapped_flux),
            "gamma_measured": rounded_float(gamma),
            "impedance_Z": rounded_float(impedance),
            "gamma_shuffled_order": rounded_float(gamma_shuf),
            "impedance_shuffled_order": rounded_float(impedance_shuf),
            "trace_distance_initial": rounded_float(d0),
            "trace_distance_final_ordered": rounded_float(d_final),
            "trace_distance_final_shuffled": rounded_float(d_final_shuf),
            "max_trace_drift": rounded_float(metrics["max_trace_drift"], 12),
            "max_hermitian_drift": rounded_float(metrics["max_hermitian_drift"], 12),
            "min_final_density_eigenvalue": rounded_float(metrics["min_final_eigenvalue"], 12),
        }

    left_signs = [per_terrain[row["name"]]["flux_sign"] for row in TERRAINS if row["sheet"] == "L"]
    right_signs = [per_terrain[row["name"]]["flux_sign"] for row in TERRAINS if row["sheet"] == "R"]
    flux_abs = [abs(v) for v in fluxes]
    open_z = [per_terrain[row["name"]]["impedance_Z"] for row in TERRAINS if row["open"]]
    closed_z = [per_terrain[row["name"]]["impedance_Z"] for row in TERRAINS if not row["open"]]
    open_z_float = [float(z) for z in open_z]
    closed_z_float = [float(z) for z in closed_z]

    commuting_l = evolve_flux_commuting_negative(RHO_Z_PLUS, +1.0, P_OPEN)
    commuting_r = evolve_flux_commuting_negative(RHO_Z_PLUS, -1.0, P_OPEN)
    product_l = evolve_flux(RHO_MIXED, +1.0, P_OPEN)
    product_r = evolve_flux(RHO_MIXED, -1.0, P_OPEN)
    forward_l = evolve_flux(RHO_Z_PLUS, +1.0, P_OPEN)
    reversed_l = evolve_flux(RHO_Z_PLUS, -1.0, P_OPEN)
    swapped_l = evolve_flux_swapped_readout(RHO_Z_PLUS, +1.0, P_OPEN)
    ham_gamma, ham_z, ham_d0, ham_d_final = estimate_impedance(+1.0, 0.0, False)

    directional_flux_pass = (
        all(s == left_signs[0] and s != 0 for s in left_signs)
        and all(s == -left_signs[0] and s != 0 for s in right_signs)
        and min(flux_abs) > 1e-3
    )
    impedance_pass = max(open_z_float) < min(closed_z_float)
    reverse_control_pass = sign_label(forward_l["flux"]) == -sign_label(reversed_l["flux"])
    shuffled_control_pass = (
        sign_label(forward_l["flux"]) == -sign_label(swapped_l)
        and abs(float(jax.device_get(forward_l["flux"] + swapped_l))) < 1e-8
        and float(jax.device_get(forward_l["min_shuffle_gap"])) > 1e-4
    )
    commuting_negative_pass = (
        abs(float(jax.device_get(commuting_l))) < 1e-9
        and abs(float(jax.device_get(commuting_r))) < 1e-9
    )
    product_negative_pass = (
        abs(float(jax.device_get(product_l["flux"]))) < 1e-9
        and abs(float(jax.device_get(product_r["flux"]))) < 1e-9
    )
    hamiltonian_only_impedance_pass = f64(ham_z) == "Inf" and float(jax.device_get(ham_gamma)) == 0.0
    density_valid_pass = all(
        per_terrain[name]["max_trace_drift"] < 1e-10
        and per_terrain[name]["max_hermitian_drift"] < 1e-10
        and per_terrain[name]["min_final_density_eigenvalue"] > -1e-10
        for name in per_terrain
    )

    verdicts = {
        "directional_flux_LR_opposite": bool(directional_flux_pass),
        "impedance_open_lower_than_closed": bool(impedance_pass),
        "reverse_chirality_control_flips_flux": bool(reverse_control_pass),
        "order_shuffled_control_flips_order_current": bool(shuffled_control_pass),
        "commuting_negative_kills_flux": bool(commuting_negative_pass),
        "product_mixed_negative_kills_flux": bool(product_negative_pass),
        "hamiltonian_only_impedance_Z_inf": bool(hamiltonian_only_impedance_pass),
        "density_matrix_validity": bool(density_valid_pass),
    }
    audit_pass = all(verdicts.values())

    results = {
        "sim_id": SIM_ID,
        "name": "JAX finite flux direction and impedance falsifier",
        "version": "1.0",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_read_only": {
            "source": "system_v5/julia_carrier/layers/flux_direction_impedance.jl",
            "result": "system_v5/julia_carrier/layers/flux_direction_impedance_results.json",
            "reference_all_pass": False,
            "red_fields_noted": [
                "A_flux_direction.flux_opposite_LR_directions=false",
                "A2_radial_expansion_compression.radial_is_topology_axis_not_chirality=false",
                "B_impedance.open_lower_Z_than_closed=false",
            ],
        },
        "finite_map": {
            "domain": "8 finite L/R terrain placements over 2x2 density matrices; ordered and shuffled finite channels",
            "codomain_or_output": "signed flux order-current, measured damping gamma, impedance Z=1/gamma, controls",
            "carrier": "qubit density matrix rho in D(C^2)",
            "noncommuting_operation": "ordered U_z(chi*alpha) after U_x(beta) versus shuffled U_x(beta) after U_z(chi*alpha)",
            "flow_steps": STEPS,
            "alpha": ALPHA,
            "beta": BETA,
        },
        "tool_manifest": {
            "jax": "load_bearing: jit/scan density-matrix channel evolution and measured trace-distance damping",
            "jax.numpy": "load_bearing: complex matrix products, eigvalsh positivity check, trace/Hilbert-Schmidt readouts",
            "json": "supportive: writes the finite receipt",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "json": "supportive",
        },
        "per_terrain": per_terrain,
        "flux_summary": {
            "left_flux_signs": left_signs,
            "right_flux_signs": right_signs,
            "min_abs_flux": round(min(flux_abs), 10),
            "max_abs_flux": round(max(flux_abs), 10),
            "directional_flux_LR_opposite": bool(directional_flux_pass),
        },
        "impedance_summary": {
            "open_Z_values": open_z,
            "closed_Z_values": closed_z,
            "max_open_Z": round(max(open_z_float), 10),
            "min_closed_Z": round(min(closed_z_float), 10),
            "open_lower_than_closed": bool(impedance_pass),
        },
        "controls": {
            "reverse_chirality_forward_flux": rounded_float(forward_l["flux"]),
            "reverse_chirality_reversed_flux": rounded_float(reversed_l["flux"]),
            "swapped_order_flux": rounded_float(swapped_l),
            "order_erased_forward_plus_swapped": rounded_float(forward_l["flux"] + swapped_l),
            "commuting_negative_L_flux": rounded_float(commuting_l),
            "commuting_negative_R_flux": rounded_float(commuting_r),
            "product_mixed_negative_L_flux": rounded_float(product_l["flux"]),
            "product_mixed_negative_R_flux": rounded_float(product_r["flux"]),
            "hamiltonian_only_gamma": rounded_float(ham_gamma),
            "hamiltonian_only_Z": rounded_float(ham_z),
            "hamiltonian_only_trace_distance_initial": rounded_float(ham_d0),
            "hamiltonian_only_trace_distance_final": rounded_float(ham_d_final),
        },
        "verdicts": verdicts,
        "AUDIT_PASS": bool(audit_pass),
        "allowed_claims": [
            "JAX diagnostic falsifier/repair candidate for flux direction plus impedance",
            "finite density-matrix order-sensitivity witness with commuting/product negatives",
        ],
        "blocked_consumers": [
            "official_flux_repair",
            "Axis0",
            "FEP",
            "physics/gravity",
            "final_manifold_admission",
        ],
    }

    RESULT_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(
        f"{SIM_ID} flux={directional_flux_pass} impedance={impedance_pass} "
        f"controls={all(v for k, v in verdicts.items() if k not in {'directional_flux_LR_opposite', 'impedance_open_lower_than_closed'})} "
        f"AUDIT_PASS={audit_pass}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
