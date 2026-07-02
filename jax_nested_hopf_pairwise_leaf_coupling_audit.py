#!/usr/bin/env python3
"""JAX-only pairwise adjacent Hopf-leaf coupling diagnostic.

This mirrors the read-only Julia reference
system_v5/julia_carrier/layers/pairwise_leaf_coupling.jl without running Julia.

Finite object:
  - two adjacent Clifford-torus leaves at theta1=pi/4-0.05 and theta2=pi/4+0.05
  - one qubit density matrix per leaf
  - Pit local Lindblad dynamics on leaf 1
  - Source local Lindblad dynamics on leaf 2
  - coherent exchange coupling g_eff * sigma_x tensor sigma_x, with g_eff=g/dtheta

Claim ceiling:
  Diagnostic/tool-lego-fit probe only. It is not a layer, stack, bridge, Axis0,
  flux, physics, or final-manifold admission result.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


SCRIPT_PATH = Path(__file__).resolve()
RESULT_PATH = SCRIPT_PATH.with_name("jax_nested_hopf_pairwise_leaf_coupling_audit_results.json")

THETA1 = math.pi / 4.0 - 0.05
THETA2 = math.pi / 4.0 + 0.05
DTHETA = THETA2 - THETA1
EPS = 0.2
GAM = 1.0
G_SWEEP = (0.0, 0.02, 0.05, 0.1, 0.2, 0.4, 0.8)
G_TEST = 0.4

CDTYPE = jnp.complex128
RDTYPE = jnp.float64

I2 = jnp.eye(2, dtype=CDTYPE)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
SM = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=CDTYPE)
SP = jnp.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=CDTYPE)

H1_LOC = EPS * SZ
J1_LOC = jnp.sqrt(jnp.asarray(GAM, dtype=RDTYPE)) * SM
H2_LOC = -EPS * SZ
J2_LOC = jnp.sqrt(jnp.asarray(GAM, dtype=RDTYPE)) * SP

PAULIS = (SX, SY, SZ)


def _jsonify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if hasattr(value, "tolist"):
        return _jsonify(value.tolist())
    if isinstance(value, (bool, str, int, float)) or value is None:
        return value
    return str(value)


def kron(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.kron(a, b)


def dagger(a: jax.Array) -> jax.Array:
    return jnp.conjugate(jnp.swapaxes(a, -1, -2))


def trace_real(a: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(a))


def op1(a: jax.Array) -> jax.Array:
    return kron(a, I2)


def op2(a: jax.Array) -> jax.Array:
    return kron(I2, a)


def lindblad_rhs(rho: jax.Array, hamiltonian: jax.Array, jumps: tuple[jax.Array, ...]) -> jax.Array:
    drho = -1.0j * (hamiltonian @ rho - rho @ hamiltonian)
    for jump in jumps:
        jdag_j = dagger(jump) @ jump
        drho = drho + jump @ rho @ dagger(jump) - 0.5 * (jdag_j @ rho + rho @ jdag_j)
    return drho


def liouvillian_matrix(hamiltonian: jax.Array, jumps: tuple[jax.Array, ...]) -> jax.Array:
    dim = hamiltonian.shape[0]
    basis = jnp.eye(dim * dim, dtype=CDTYPE).reshape((dim * dim, dim, dim))
    columns_as_rows = jax.vmap(lambda rho: lindblad_rhs(rho, hamiltonian, jumps).reshape(-1))(basis)
    return columns_as_rows.T


def trace_row(dim: int) -> jax.Array:
    row = jnp.zeros((dim * dim,), dtype=CDTYPE)
    return row.at[jnp.arange(dim) * dim + jnp.arange(dim)].set(1.0 + 0.0j)


def steady_state(hamiltonian: jax.Array, jumps: tuple[jax.Array, ...]) -> jax.Array:
    dim = hamiltonian.shape[0]
    liouvillian = liouvillian_matrix(hamiltonian, jumps)
    constrained = liouvillian.at[0, :].set(trace_row(dim))
    rhs = jnp.zeros((dim * dim,), dtype=CDTYPE).at[0].set(1.0 + 0.0j)
    vec = jnp.linalg.solve(constrained, rhs)
    rho = vec.reshape((dim, dim))
    rho = 0.5 * (rho + dagger(rho))
    return rho / jnp.trace(rho)


def joint_steady(g: float, coupler: jax.Array) -> tuple[jax.Array, float]:
    g_eff = g / DTHETA
    h_joint = op1(H1_LOC) + op2(H2_LOC) + g_eff * kron(coupler, coupler)
    jumps = (op1(J1_LOC), op2(J2_LOC))
    return steady_state(h_joint, jumps), g_eff


def expectation(rho: jax.Array, op: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho @ op))


def bloch(rho: jax.Array) -> jax.Array:
    return jnp.asarray([expectation(rho, op) for op in PAULIS], dtype=RDTYPE)


def partial_trace_leaf1(rho: jax.Array) -> jax.Array:
    return jnp.einsum("abcb->ac", rho.reshape((2, 2, 2, 2)))


def partial_trace_leaf2(rho: jax.Array) -> jax.Array:
    return jnp.einsum("abad->bd", rho.reshape((2, 2, 2, 2)))


def trace_distance(rho: jax.Array, sigma: jax.Array) -> jax.Array:
    diff = 0.5 * ((rho - sigma) + dagger(rho - sigma))
    evals = jnp.linalg.eigvalsh(diff)
    return 0.5 * jnp.sum(jnp.abs(evals))


def connected_corr(rho: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    full = expectation(rho, kron(a, b))
    r1 = expectation(partial_trace_leaf1(rho), a)
    r2 = expectation(partial_trace_leaf2(rho), b)
    return full - r1 * r2


def locking_scalar(rho: jax.Array) -> jax.Array:
    vals = [jnp.abs(connected_corr(rho, a, b)) for a in PAULIS for b in PAULIS]
    return jnp.sum(jnp.asarray(vals, dtype=RDTYPE))


def gamma_axioms(op: jax.Array) -> dict[str, bool]:
    return {
        "involutive_gamma2_eq_I": bool(jnp.allclose(op @ op, I2, atol=1.0e-10, rtol=1.0e-10)),
        "traceless": bool(jnp.abs(jnp.trace(op)) < 1.0e-10),
        "hermitian": bool(jnp.allclose(op, dagger(op), atol=1.0e-10, rtol=1.0e-10)),
    }


def row_for_g(g: float, rho_prod: jax.Array) -> dict[str, float]:
    rho, g_eff = joint_steady(g, SX)
    r1 = partial_trace_leaf1(rho)
    r2 = partial_trace_leaf2(rho)
    return {
        "g": float(g),
        "g_eff": float(g_eff),
        "shift": float(trace_distance(rho, rho_prod)),
        "locking": float(locking_scalar(rho)),
        "leaf1_z": float(expectation(r1, SZ)),
        "leaf2_z": float(expectation(r2, SZ)),
        "C_xx": float(connected_corr(rho, SX, SX)),
        "C_yy": float(connected_corr(rho, SY, SY)),
        "C_zz": float(connected_corr(rho, SZ, SZ)),
    }


def build_receipt() -> dict[str, Any]:
    rho1_iso = steady_state(H1_LOC, (J1_LOC,))
    rho2_iso = steady_state(H2_LOC, (J2_LOC,))
    rho_prod = kron(rho1_iso, rho2_iso)

    g0_rho, _ = joint_steady(0.0, SX)
    shift_g0 = float(trace_distance(g0_rho, rho_prod))
    locking_g0 = float(locking_scalar(g0_rho))

    sweep = [row_for_g(g, rho_prod) for g in G_SWEEP]
    small_g = [row for row in sweep if row["g"] <= 0.2]
    shift_rises = all(
        small_g[idx]["shift"] <= small_g[idx + 1]["shift"] + 1.0e-9
        for idx in range(len(small_g) - 1)
    ) and small_g[-1]["shift"] > 1.0e-4

    g_big = sweep[-1]
    z_gap_iso = abs(float(bloch(rho1_iso)[2]) - float(bloch(rho2_iso)[2]))
    z_gap_big = abs(g_big["leaf1_z"] - g_big["leaf2_z"])

    rho_real, g_eff_test = joint_steady(G_TEST, SX)
    rho_sham, _ = joint_steady(G_TEST, I2)
    shift_real = float(trace_distance(rho_real, rho_prod))
    shift_sham = float(trace_distance(rho_sham, rho_prod))
    lock_real = float(locking_scalar(rho_real))
    lock_sham = float(locking_scalar(rho_sham))

    sx_axioms = gamma_axioms(SX)
    id_axioms = gamma_axioms(I2)
    sx_axioms["is_dirac_gamma"] = all(sx_axioms.values())
    id_axioms["is_dirac_gamma"] = all(id_axioms.values())

    checks = {
        "ran_julia_false": True,
        "ran_pytorch_false": "torch" not in sys.modules,
        "theta_gap_matches_reference": abs(DTHETA - 0.1) < 1.0e-14,
        "g_eff_uses_g_over_dtheta": abs(g_eff_test - G_TEST / DTHETA) < 1.0e-14,
        "gamma_theta_is_sigma_x_dirac_gamma": sx_axioms["is_dirac_gamma"],
        "identity_is_not_dirac_gamma": not id_axioms["is_dirac_gamma"],
        "g0_joint_equals_product": shift_g0 < 1.0e-8 and locking_g0 < 1.0e-8,
        "g_positive_shifts_state": g_big["shift"] > 1.0e-3,
        "g_positive_turns_on_correlations": g_big["locking"] > 1.0e-3 and abs(g_big["C_xx"]) > 1.0e-4,
        "shift_rises_in_small_g_regime": shift_rises,
        "coupled_reductions_pull_together": z_gap_big < z_gap_iso - 1.0e-4,
        "identity_coupler_sham_lower_than_exchange": (
            shift_real > shift_sham + 1.0e-4 and lock_real > lock_sham + 1.0e-4
        ),
        "identity_coupler_sham_inert": shift_sham < 1.0e-8 and lock_sham < 1.0e-8,
    }
    verdict = "PASS" if all(checks.values()) else "FAIL"

    receipt = {
        "sim_id": "jax_nested_hopf_pairwise_leaf_coupling_audit",
        "name": "JAX nested Hopf pairwise adjacent leaf coupling audit",
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_reference_read_only": "system_v5/julia_carrier/layers/pairwise_leaf_coupling.jl",
        "ran_julia": False,
        "ran_pytorch": False,
        "classification": "diagnostic/tool_lego_fit_probe",
        "contract_classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "pairwise_coupling_diagnostic",
        "tier": "tool-stage bounded pairwise coupling diagnostic",
        "purpose": (
            "JAX-only mirror of the pairwise adjacent Hopf-leaf coupling reference: "
            "test whether sigma_x tensor sigma_x radial exchange shifts the joint "
            "steady state away from the product of isolated Pit/Source Lindblad leaves."
        ),
        "scientific_question": (
            "Does a finite two-leaf Lindblad object with g_eff=g/dtheta show real "
            "exchange-induced shift/correlation while g=0 and identity-coupler controls stay inert?"
        ),
        "root_constraints_in_force": {
            "F01": "finite two-leaf carrier, finite 2x2 local densities, finite 4x4 joint density, finite g sweep",
            "N01": "coherent exchange sigma_x tensor sigma_x does not commute with local Pit/Source dissipative fixed-point structure",
        },
        "finite_map": (
            "((rho1_iso, rho2_iso), g, coupler) -> Liouvillian nullspace steady state "
            "rho_joint plus trace-distance and connected-correlation readouts"
        ),
        "domain": {
            "theta1": THETA1,
            "theta2": THETA2,
            "dtheta": DTHETA,
            "leaf1": "Pit Lindblad density matrix from H=eps*sigma_z, J=sqrt(gamma)*sigma_minus",
            "leaf2": "Source Lindblad density matrix from H=-eps*sigma_z, J=sqrt(gamma)*sigma_plus",
            "couplers": ["sigma_x tensor sigma_x", "identity tensor identity sham"],
        },
        "codomain_or_output": {
            "rho_joint": "4x4 two-leaf steady-state density matrix",
            "rho_product": "rho1_iso tensor rho2_iso",
            "readouts": ["trace_distance_shift", "connected_XX_YY_ZZ_correlators", "leaf_reduced_bloch_z_gap"],
        },
        "carrier_layer": "two adjacent nested Hopf/Clifford-torus leaves as a finite two-qubit density carrier",
        "geometry_layer": "theta-adjacent Hopf leaf pair; dtheta sets finite-difference radial hopping strength",
        "carrier_realization": "JAX complex128 density matrices and Liouvillian linear solve",
        "peps3d_embedding": "not_admitted; diagnostic finite two-leaf object only",
        "spinor_state": "spinor-derived local qubit density matrices; not a torch-native manifold admission",
        "quaternion_action": "not_applicable",
        "bridge_layer": "none",
        "cut_layer": "none",
        "dependency_receipts": [
            "read-only reference: system_v5/julia_carrier/layers/pairwise_leaf_coupling.jl"
        ],
        "downstream_blocks": [
            "canonical_layer_admission",
            "layer_stacking_readiness",
            "coexistence_topology_emergence",
            "bridge",
            "xi_phi0",
            "axis0",
            "flux",
            "basin",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "allowed_claims": [
            "JAX executable diagnostic mirrors the Julia reference coupling shape",
            "g=0 product control remains inert",
            "g>0 sigma_x exchange shifts the joint steady state and turns on connected correlations",
            "equal-strength identity-coupler sham is lower than real exchange",
        ],
        "promotion_blockers": [
            "JAX-only diagnostic, not Julia-native QuantumOptics execution",
            "no PyTorch-native spinor/PEPS3D manifold carrier",
            "no tool-tool coupling receipt or broader parent lego admission",
            "promotion_allowed=false by design",
        ],
        "required_tools": ["jax"],
        "actual_tools_used": {
            "jax": "load_bearing: complex128 matrix construction, Liouvillian nullspace solve, eigvalsh trace distance",
        },
        "tool_manifest": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": (
                    "Builds the finite Lindblad superoperator, solves the trace-constrained "
                    "steady state, and computes density/correlation readouts."
                ),
            },
            "diffrax": {
                "used": False,
                "role": "not_relevant",
                "reason": "Steady states are solved as finite Liouvillian nullspaces; no ODE integration is needed.",
            },
            "julia": {
                "used": False,
                "role": "forbidden_this_task",
                "reason": "User required read-only Julia reference and no Julia run.",
            },
            "pytorch": {
                "used": False,
                "role": "forbidden_this_task",
                "reason": "User required no PyTorch import or run.",
            },
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "diffrax": "None",
            "julia": "None",
            "pytorch": "None",
        },
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": [
            "g=0 product/direct-sum control",
            "identity-coupler wrong-structure sham at equal operator norm",
        ],
        "negatives_run": {
            "g0_product_control": {"shift": shift_g0, "locking": locking_g0},
            "identity_coupler_sham": {
                "g": G_TEST,
                "shift": shift_sham,
                "locking": lock_sham,
            },
        },
        "kill_conditions": [
            "g=0 has nonzero shift or connected correlations",
            "g>0 real exchange leaves the joint state product-like",
            "identity sham matches or exceeds real exchange shift/correlation",
            "script imports/runs PyTorch or Julia",
        ],
        "geometry": {
            "theta1": THETA1,
            "theta2": THETA2,
            "dtheta": DTHETA,
            "g_eff_formula": "g/dtheta",
            "g_test": G_TEST,
            "g_eff_test": g_eff_test,
        },
        "local_steady_states": {
            "leaf1_pit": {
                "rho": rho1_iso,
                "bloch": bloch(rho1_iso),
            },
            "leaf2_source": {
                "rho": rho2_iso,
                "bloch": bloch(rho2_iso),
            },
        },
        "gamma_theta_axioms": sx_axioms,
        "identity_axioms": id_axioms,
        "sweep": sweep,
        "which_survives": {
            "isolated_z_gap": z_gap_iso,
            "coupled_z_gap_at_max_g": z_gap_big,
            "coupled_reductions_pull_together": z_gap_big < z_gap_iso - 1.0e-4,
        },
        "wrong_structure_kill": {
            "g_test": G_TEST,
            "opnorm_sigma_x": float(jnp.linalg.norm(SX, ord=2)),
            "opnorm_identity": float(jnp.linalg.norm(I2, ord=2)),
            "real_exchange_shift": shift_real,
            "identity_sham_shift": shift_sham,
            "real_exchange_locking": lock_real,
            "identity_sham_locking": lock_sham,
        },
        "checks": checks,
        "all_pass": all(checks.values()),
        "verdict": verdict,
        "result_summary": (
            f"{verdict}: g=0 shift={shift_g0:.3e}, real_exchange_shift_g{G_TEST}={shift_real:.6f}, "
            f"identity_sham_shift_g{G_TEST}={shift_sham:.3e}, promotion_allowed=false"
        ),
        "eligible_consumers": ["bounded diagnostic comparison only"],
        "blocked_consumers": [
            "canonical_layer_admission",
            "layer_stacking_readiness",
            "coexistence_topology_emergence",
            "bridge",
            "xi_phi0",
            "axis0",
            "flux",
            "basin",
            "physics_gravity",
            "final_manifold_admission",
        ],
    }
    receipt["TOOL_MANIFEST"] = receipt["tool_manifest"]
    receipt["TOOL_INTEGRATION_DEPTH"] = receipt["tool_integration_depth"]
    return receipt


def main() -> int:
    receipt = build_receipt()
    RESULT_PATH.write_text(json.dumps(_jsonify(receipt), indent=2, sort_keys=True) + "\n")
    line = (
        "JAX Hopf pairwise leaf coupling audit: "
        f"{receipt['verdict']} | g0_shift={receipt['negatives_run']['g0_product_control']['shift']:.3e} "
        f"| real_shift_g0.4={receipt['wrong_structure_kill']['real_exchange_shift']:.6f} "
        f"| sham_shift_g0.4={receipt['wrong_structure_kill']['identity_sham_shift']:.3e} "
        f"| promotion_allowed={str(receipt['promotion_allowed']).lower()} "
        f"| result={RESULT_PATH.name}"
    )
    print(line)
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
