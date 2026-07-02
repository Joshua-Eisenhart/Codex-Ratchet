#!/usr/bin/env python3
"""JAX-only multi-shell coexistence mirror.

Julia reference, read-only:
    system_v5/julia_carrier/layers/multishell_coexistence.jl
    system_v5/julia_carrier/layers/multishell_coexistence_results.json

This diagnostic mirrors the finite object from the Julia lane without running
Julia and without importing or touching PyTorch:

    three nested leaves theta={pi/6, pi/4, pi/3}
    local terrains = Pit, Hill, Source
    coherent inter-leaf hopping = J * sin(2 theta_mid) * X_k X_{k+1}
    readout = reduced per-leaf Bloch vectors from the joint density matrix.

It is an audit/scout surface only. It does not promote a layer, G-structure,
Axis0, flux, bridge, or physics claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


OUT = Path("jax_multishell_coexistence_mirror_results.json")
JULIA_REFERENCE = [
    "system_v5/julia_carrier/layers/multishell_coexistence.jl",
    "system_v5/julia_carrier/layers/multishell_coexistence_results.json",
]

DT = 0.01
T_FINAL = 60.0
N_STEPS = int(T_FINAL / DT)
SNAP_STEP = int(0.75 * N_STEPS)

GAM = 1.0
KAP = 1.0
EPS = 0.2
THETAS = jnp.asarray([jnp.pi / 6.0, jnp.pi / 4.0, jnp.pi / 3.0], dtype=jnp.float64)
JHOPS = (0.0, 0.1, 0.3, 1.0, 3.0)

SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1j], [1j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
ID2 = jnp.eye(2, dtype=jnp.complex128)
SM = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)
SP = jnp.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128)
PXP = 0.5 * (ID2 + SX)
PXM = 0.5 * (ID2 - SX)
ZERO2 = jnp.zeros((2, 2), dtype=jnp.complex128)

PAULIS = (SX, SY, SZ)
SINKS_GENUINE = jnp.asarray(
    [
        [0.0, 0.0, -1.0],  # Pit
        [1.0, 0.0, 0.0],   # Hill
        [0.0, 0.0, 1.0],   # Source
    ],
    dtype=jnp.float64,
)
SINKS_IDENTICAL = jnp.asarray(
    [
        [0.0, 0.0, -1.0],
        [0.0, 0.0, -1.0],
        [0.0, 0.0, -1.0],
    ],
    dtype=jnp.float64,
)


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def _round_list(x: Any, ndigits: int = 6) -> list[float]:
    return [round(float(v), ndigits) for v in jax.device_get(x).reshape(-1)]


def kron3(a: jax.Array, b: jax.Array, c: jax.Array) -> jax.Array:
    return jnp.kron(jnp.kron(a, b), c)


def emb(op: jax.Array, site: int) -> jax.Array:
    ops = [ID2, ID2, ID2]
    ops[site] = op
    return kron3(ops[0], ops[1], ops[2])


def two_site(op_a: jax.Array, site_a: int, op_b: jax.Array, site_b: int) -> jax.Array:
    ops = [ID2, ID2, ID2]
    ops[site_a] = op_a
    ops[site_b] = op_b
    return kron3(ops[0], ops[1], ops[2])


X_OPS = jnp.stack([emb(SX, k) for k in range(3)])
Y_OPS = jnp.stack([emb(SY, k) for k in range(3)])
Z_OPS = jnp.stack([emb(SZ, k) for k in range(3)])


def gamma_weight(theta_mid: jax.Array) -> jax.Array:
    return jnp.sin(2.0 * theta_mid)


W12 = gamma_weight((THETAS[0] + THETAS[1]) / 2.0)
W23 = gamma_weight((THETAS[1] + THETAS[2]) / 2.0)
HOP_XX = W12 * two_site(SX, 0, SX, 1) + W23 * two_site(SX, 1, SX, 2)
HOP_ZZ = W12 * two_site(SZ, 0, SZ, 1) + W23 * two_site(SZ, 1, SZ, 2)


def ket(v: list[float]) -> jax.Array:
    x = jnp.asarray(v, dtype=jnp.complex128)
    return x / jnp.linalg.norm(x)


PSI0 = jnp.kron(jnp.kron(ket([0.8, 0.6]), ket([0.5, 0.5])), ket([0.6, 0.8]))
RHO0 = jnp.outer(PSI0, PSI0.conj())
RHO0_DIAGONAL = jnp.diag(jnp.diag(RHO0))


def build_genuine() -> tuple[jax.Array, jax.Array]:
    h_on = EPS * emb(SZ, 0) + emb(SX, 1) + EPS * emb(SZ, 2)
    jumps = jnp.stack(
        [
            jnp.sqrt(GAM) * emb(SM, 0),
            jnp.sqrt(KAP) * emb(PXP, 1),
            jnp.sqrt(KAP) * emb(PXM, 1),
            jnp.sqrt(GAM) * emb(SP, 2),
            jnp.zeros((8, 8), dtype=jnp.complex128),
            jnp.zeros((8, 8), dtype=jnp.complex128),
        ]
    )
    return h_on, jumps


def build_identical_pit() -> tuple[jax.Array, jax.Array]:
    h_on = EPS * emb(SZ, 0) + EPS * emb(SZ, 1) + EPS * emb(SZ, 2)
    jumps = jnp.stack(
        [
            jnp.sqrt(GAM) * emb(SM, 0),
            jnp.sqrt(GAM) * emb(SM, 1),
            jnp.sqrt(GAM) * emb(SM, 2),
            jnp.zeros((8, 8), dtype=jnp.complex128),
            jnp.zeros((8, 8), dtype=jnp.complex128),
            jnp.zeros((8, 8), dtype=jnp.complex128),
        ]
    )
    return h_on, jumps


def build_commuting_z() -> tuple[jax.Array, jax.Array]:
    """A commuting/diagonal negative: no terrain coherence should be generated."""
    h_on = EPS * emb(SZ, 0) - 0.1 * emb(SZ, 1) - EPS * emb(SZ, 2)
    jumps = jnp.stack(
        [
            jnp.sqrt(GAM) * emb(SM, 0),
            jnp.sqrt(KAP) * emb(SZ, 1),
            jnp.sqrt(GAM) * emb(SP, 2),
            jnp.zeros((8, 8), dtype=jnp.complex128),
            jnp.zeros((8, 8), dtype=jnp.complex128),
            jnp.zeros((8, 8), dtype=jnp.complex128),
        ]
    )
    return h_on, jumps


def dissipator(l: jax.Array, rho: jax.Array) -> jax.Array:
    ll = l.conj().T @ l
    return l @ rho @ l.conj().T - 0.5 * (ll @ rho + rho @ ll)


def lindblad_rhs(rho: jax.Array, h: jax.Array, jumps: jax.Array) -> jax.Array:
    drho = -1j * (h @ rho - rho @ h)
    drho = drho + jnp.sum(jax.vmap(lambda l: dissipator(l, rho))(jumps), axis=0)
    return drho


def project_density(rho: jax.Array) -> jax.Array:
    rho = 0.5 * (rho + rho.conj().T)
    tr = jnp.real(jnp.trace(rho))
    return rho / tr


def rk4_step(rho: jax.Array, h: jax.Array, jumps: jax.Array) -> jax.Array:
    k1 = lindblad_rhs(rho, h, jumps)
    k2 = lindblad_rhs(rho + 0.5 * DT * k1, h, jumps)
    k3 = lindblad_rhs(rho + 0.5 * DT * k2, h, jumps)
    k4 = lindblad_rhs(rho + DT * k3, h, jumps)
    return project_density(rho + (DT / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))


@jax.jit
def evolve(rho0: jax.Array, h_on: jax.Array, jumps: jax.Array, jhop: jax.Array, hop: jax.Array) -> tuple[jax.Array, jax.Array]:
    h = h_on + jhop * hop

    def body(carry: tuple[jax.Array, jax.Array], i: jax.Array) -> tuple[tuple[jax.Array, jax.Array], None]:
        rho, snap = carry
        rho_next = rk4_step(rho, h, jumps)
        snap_next = jnp.where(i == SNAP_STEP, rho_next, snap)
        return (rho_next, snap_next), None

    (rho_f, rho_snap), _ = jax.lax.scan(body, (project_density(rho0), project_density(rho0)), jnp.arange(N_STEPS))
    return rho_f, rho_snap


def blochs(rho: jax.Array) -> jax.Array:
    return jnp.stack(
        [
            jnp.real(jnp.asarray([jnp.trace(rho @ X_OPS[k]), jnp.trace(rho @ Y_OPS[k]), jnp.trace(rho @ Z_OPS[k])]))
            for k in range(3)
        ],
        axis=0,
    )


def rho_from_bloch(r: jax.Array) -> jax.Array:
    return 0.5 * (ID2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def product_from_blochs(rs: jax.Array) -> jax.Array:
    return jnp.kron(jnp.kron(rho_from_bloch(rs[0]), rho_from_bloch(rs[1])), rho_from_bloch(rs[2]))


def pairwise_sep(rs: jax.Array) -> jax.Array:
    return jnp.asarray(
        [
            jnp.linalg.norm(rs[0] - rs[1]),
            jnp.linalg.norm(rs[0] - rs[2]),
            jnp.linalg.norm(rs[1] - rs[2]),
        ],
        dtype=jnp.float64,
    )


def detector(rs: jax.Array, sinks: jax.Array, sep_tol: float = 0.3) -> tuple[bool, bool, bool, float]:
    seps = pairwise_sep(rs)
    all_distinct = _b(jnp.min(seps) > sep_tol)
    nearest = jnp.argmin(jnp.linalg.norm(rs[:, None, :] - sinks[None, :, :], axis=-1), axis=1)
    own = _b(jnp.all(nearest == jnp.arange(3)))
    return all_distinct and own, all_distinct, own, _f(jnp.min(seps))


def state_metrics(rho: jax.Array, rho_snap: jax.Array) -> dict[str, Any]:
    rs = blochs(rho)
    product = product_from_blochs(rs)
    ev = jnp.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    drift = jnp.real(jnp.trace((rho - rho_snap) @ (rho - rho_snap).conj().T))
    coher = jnp.linalg.norm(rho - jnp.diag(jnp.diag(rho)))
    product_defect = jnp.linalg.norm(rho - product)
    c12 = jnp.real(jnp.trace(rho @ two_site(SX, 0, SX, 1))) - rs[0, 0] * rs[1, 0]
    c23 = jnp.real(jnp.trace(rho @ two_site(SX, 1, SX, 2))) - rs[1, 0] * rs[2, 0]
    c13 = jnp.real(jnp.trace(rho @ two_site(SX, 0, SX, 2))) - rs[0, 0] * rs[2, 0]
    return {
        "blochs": [[round(float(v), 6) for v in row] for row in jax.device_get(rs)],
        "trace_error": _f(jnp.abs(jnp.trace(rho) - 1.0)),
        "min_eigenvalue": _f(jnp.min(ev)),
        "steady_drift": _f(drift),
        "l1_offdiag_coherence_norm": _f(coher),
        "product_defect_norm": _f(product_defect),
        "connected_xx": {
            "c12": _f(c12),
            "c23": _f(c23),
            "c13": _f(c13),
        },
        "min_pairwise_sep": _f(jnp.min(pairwise_sep(rs))),
    }


def run_case(h_on: jax.Array, jumps: jax.Array, jhop: float, hop: jax.Array, rho0: jax.Array = RHO0) -> tuple[jax.Array, dict[str, Any]]:
    rho, snap = evolve(rho0, h_on, jumps, jnp.asarray(jhop, dtype=jnp.float64), hop)
    return rho, state_metrics(rho, snap)


def row_for(h_on: jax.Array, jumps: jax.Array, jhop: float, hop: jax.Array, sinks: jax.Array, rho0: jax.Array = RHO0) -> dict[str, Any]:
    rho, metrics = run_case(h_on, jumps, jhop, hop, rho0)
    rs = blochs(rho)
    coex, distinct, own, sepmin = detector(rs, sinks)
    z_gap = _f(jnp.abs(rs[0, 2] - rs[2, 2]))
    metrics.update(
        {
            "Jhop": jhop,
            "coexist": coex,
            "all_distinct": distinct,
            "each_at_own_sink": own,
            "pit_source_z_gap": z_gap,
            "min_pairwise_sep": sepmin,
        }
    )
    return metrics


def main() -> int:
    h_genuine, j_genuine = build_genuine()
    h_identical, j_identical = build_identical_pit()
    h_commuting, j_commuting = build_commuting_z()

    decoupled = row_for(h_genuine, j_genuine, 0.0, HOP_XX, SINKS_GENUINE)
    sweep = [row_for(h_genuine, j_genuine, jhop, HOP_XX, SINKS_GENUINE) for jhop in JHOPS]
    kill_rows = [row_for(h_identical, j_identical, jhop, HOP_XX, SINKS_IDENTICAL) for jhop in (0.0, 0.3, 1.0)]
    product_negative = row_for(h_genuine, j_genuine, 0.0, HOP_XX, SINKS_GENUINE)
    commuting_negative = row_for(h_commuting, j_commuting, 0.3, HOP_ZZ, SINKS_GENUINE, rho0=RHO0_DIAGONAL)

    weak = {row["Jhop"]: row["coexist"] for row in sweep}
    coupled_03 = next(row for row in sweep if abs(row["Jhop"] - 0.3) < 1.0e-12)
    coupled_30 = next(row for row in sweep if abs(row["Jhop"] - 3.0) < 1.0e-12)

    sink_errors = [
        float(jnp.linalg.norm(jnp.asarray(decoupled["blochs"][k]) - SINKS_GENUINE[k]))
        for k in range(3)
    ]
    max_trace_error = max(row["trace_error"] for row in sweep + kill_rows + [commuting_negative])
    min_eig = min(row["min_eigenvalue"] for row in sweep + kill_rows + [commuting_negative])
    max_drift = max(row["steady_drift"] for row in sweep + kill_rows + [commuting_negative])

    decoupled_offdiag = decoupled["l1_offdiag_coherence_norm"]
    coupled_local_coherence_shift = abs(coupled_03["l1_offdiag_coherence_norm"] - decoupled_offdiag)

    checks = {
        "decoupled_anchor_matches_known_sinks": max(sink_errors) < 0.025,
        "decoupled_three_terrains_distinct": decoupled["coexist"],
        "coupled_weak_moderate_coexistence": bool(weak[0.1] and weak[0.3]),
        "strong_coupling_reports_collapse_not_coexist": not bool(weak[3.0]),
        "identical_terrain_kill_not_3distinct": all(not row["all_distinct"] and not row["coexist"] for row in kill_rows),
        "product_negative_factorizes_when_uncoupled": product_negative["product_defect_norm"] < 1.0e-8,
        "coupled_shells_reshape_local_coherence": coupled_local_coherence_shift > 1.0e-2,
        "coupled_steady_state_not_misread_as_nonproduct": coupled_03["product_defect_norm"] < 1.0e-8,
        "commuting_negative_no_offdiagonal_coherence": commuting_negative["l1_offdiag_coherence_norm"] < 1.0e-9,
        "commuting_negative_not_coexistence_positive": not commuting_negative["coexist"],
        "steady_state_converged_all": max_drift < 1.0e-8,
        "density_trace_preserved": max_trace_error < 1.0e-8,
        "density_psd_within_tolerance": min_eig > -1.0e-7,
    }
    audit_pass = all(checks.values())

    receipt = {
        "object": "jax_multishell_coexistence_mirror",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_read_only": JULIA_REFERENCE,
        "sim_execution_kind": "nonclassical_diagnostic_jax_density_matrix",
        "finite_map": "3 finite shell density rho(t) under local Lindblad terrains plus finite nearest-neighbour hopping, read out as reduced Bloch vectors and product/coherence defects",
        "domain": {
            "hilbert_dim": 8,
            "shells": 3,
            "thetas": _round_list(THETAS),
            "terrains": ["Pit", "Hill", "Source"],
            "Jhop_sweep": list(JHOPS),
        },
        "codomain_or_output": "per-shell reduced Bloch vectors, coexistence flags, coherence/product defects, kill/control verdicts",
        "root_constraints_in_force": {
            "F01": "finite 3-shell Hilbert space, finite operator set, finite Jhop sweep, finite RK4 trajectory",
            "N01": "noncommuting X_k X_{k+1} hopping pressures z-sink terrains; commuting/product negatives included",
        },
        "carrier_realization": "JAX complex128 density matrix on (C^2)^3",
        "peps3d_embedding": "not_admitted; finite 3-shell diagnostic only, downstream PEPS3D/G-structure consumers blocked",
        "spinor_state": "spinor-derived three-qubit density matrix diagnostic",
        "quaternion_action": "not_applicable_in_this_density_mirror",
        "tool_manifest": {
            "jax": "load_bearing finite density-matrix ODE, matrix operators, vmap/scan/JIT",
            "json": "receipt emission only",
            "julia": "read-only reference paths only; not executed",
            "pytorch": "not imported, not executed, not touched",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "json": "supportive",
            "julia": "read_only_reference",
            "pytorch": "None",
        },
        "decoupled_reference": {
            "row": decoupled,
            "sink_errors": [round(x, 8) for x in sink_errors],
        },
        "coupled_sweep": {
            "coexist_by_coupling": {str(row["Jhop"]): row["coexist"] for row in sweep},
            "rows": sweep,
        },
        "controls": {
            "identical_terrain_kill": kill_rows,
            "product_negative_uncoupled": product_negative,
            "commuting_negative_diagonal_ZZ": commuting_negative,
        },
        "diagnostics": {
            "max_trace_error": max_trace_error,
            "min_eigenvalue": min_eig,
            "max_steady_drift": max_drift,
            "coupled_0p3_product_defect": coupled_03["product_defect_norm"],
            "coupled_0p3_local_coherence_shift_vs_decoupled": coupled_local_coherence_shift,
            "strong_3p0_pit_source_z_gap": coupled_30["pit_source_z_gap"],
        },
        "checks": checks,
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "status": "passes local rerun" if audit_pass else "runs_with_failed_checks",
        "allowed_claims": [
            "JAX diagnostic mirror of finite 3-shell coexistence/coherence readout",
            "coupled-shell local Bloch/coherence deformation with product/nonproduct boundary kept explicit",
            "read-only comparison target for Julia receipt invariants",
        ],
        "blocked_consumers": [
            "layer_completion",
            "official_g_structure_selection",
            "Axis0",
            "FEP",
            "flux",
            "bridge",
            "physics_gravity",
            "final_manifold_admission",
        ],
    }

    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(
        "jax_multishell_coexistence_mirror "
        f"AUDIT_PASS={audit_pass} "
        f"A={decoupled['coexist']} "
        f"weak={weak[0.1] and weak[0.3]} "
        f"strong_collapse={not weak[3.0]} "
        f"product_negative={checks['product_negative_factorizes_when_uncoupled']} "
        f"commuting_negative={checks['commuting_negative_no_offdiagonal_coherence']} "
        f"identical_kill={checks['identical_terrain_kill_not_3distinct']}"
    )
    print(f"wrote {OUT}")
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
