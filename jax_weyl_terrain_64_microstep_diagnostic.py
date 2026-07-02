#!/usr/bin/env python3
"""JAX-only diagnostic for the source-native Weyl terrain 64-microstep object.

This is an audit/stress lane, not the Julia truth lane and not a PyTorch port.
It keeps the object finite:

  2 Weyl operating spaces (L/R)
  x 2 Hopf loop placements (fiber/base-lift)
  x 4 terrain families (Se/Ne/Ni/Si)
  x 4 operator substages (Ti/Te/Fi/Fe)
  = 64 finite density-channel microsteps.

The receipt is deliberately nonpromotional. It tests whether the JAX lane can
run the source-shaped density dynamics without collapsing sheet sign, ladder
swap, loop placement, or noncommuting operator order.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_PATH = ROOT / "jax_weyl_terrain_64_microstep_diagnostic_results.json"

SIM_ID = "jax_weyl_terrain_64_microstep_diagnostic"
CLASSIFICATION = "diagnostic_jax_64_microstep_suite"
PROMOTION_ALLOWED = False
BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "bridge",
    "basin_admission",
    "physics_gravity",
    "physics/gravity",
    "final_manifold_admission",
]

RTYPE = jnp.float64
CTYPE = jnp.complex128
EPS = 1.0e-12

I2 = jnp.eye(2, dtype=CTYPE)
SX = jnp.array([[0, 1], [1, 0]], dtype=CTYPE)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=CTYPE)
SZ = jnp.array([[1, 0], [0, -1]], dtype=CTYPE)
SIGMA_MINUS = jnp.array([[0, 0], [1, 0]], dtype=CTYPE)
SIGMA_PLUS = jnp.array([[0, 1], [0, 0]], dtype=CTYPE)

H0_AXIS = jnp.array([0.31, 0.19, 0.77], dtype=RTYPE)
H0 = H0_AXIS[0] * SX + H0_AXIS[1] * SY + H0_AXIS[2] * SZ

OPERATORS = ["Ti", "Te", "Fi", "Fe"]


PLACEMENTS = [
    {
        "placement": 1,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^L",
        "stage": "Se",
        "terrain": "Funnel",
        "terrain_law": "X_F^L",
        "igt_label": "LOSEwin",
        "realized_word": "win",
        "source_pair": "SeFi",
        "source_precedence": "DOWN",
    },
    {
        "placement": 2,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^L",
        "stage": "Ne",
        "terrain": "Vortex",
        "terrain_law": "X_V^L",
        "igt_label": "WINlose",
        "realized_word": "lose",
        "source_pair": "FiNe",
        "source_precedence": "UP",
    },
    {
        "placement": 3,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^L",
        "stage": "Ni",
        "terrain": "Pit",
        "terrain_law": "X_P^L",
        "igt_label": "loseLOSE",
        "realized_word": "lose",
        "source_pair": "TeNi",
        "source_precedence": "UP",
    },
    {
        "placement": 4,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^L",
        "stage": "Si",
        "terrain": "Hill",
        "terrain_law": "X_H^L",
        "igt_label": "winWIN",
        "realized_word": "win",
        "source_pair": "SiTe",
        "source_precedence": "DOWN",
    },
    {
        "placement": 5,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^L",
        "stage": "Se",
        "terrain": "Funnel",
        "terrain_law": "X_F^L",
        "igt_label": "LOSEwin",
        "realized_word": "LOSE",
        "source_pair": "TiSe",
        "source_precedence": "UP",
    },
    {
        "placement": 6,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^L",
        "stage": "Ne",
        "terrain": "Vortex",
        "terrain_law": "X_V^L",
        "igt_label": "WINlose",
        "realized_word": "WIN",
        "source_pair": "NeTi",
        "source_precedence": "DOWN",
    },
    {
        "placement": 7,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^L",
        "stage": "Ni",
        "terrain": "Pit",
        "terrain_law": "X_P^L",
        "igt_label": "loseLOSE",
        "realized_word": "LOSE",
        "source_pair": "NiFe",
        "source_precedence": "DOWN",
    },
    {
        "placement": 8,
        "sheet": "L",
        "sheet_label": "left_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^L",
        "stage": "Si",
        "terrain": "Hill",
        "terrain_law": "X_H^L",
        "igt_label": "winWIN",
        "realized_word": "WIN",
        "source_pair": "FeSi",
        "source_precedence": "UP",
    },
    {
        "placement": 9,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^R",
        "stage": "Se",
        "terrain": "Cannon",
        "terrain_law": "X_C^R",
        "igt_label": "loseWIN",
        "realized_word": "lose",
        "source_pair": "SeTi",
        "source_precedence": "DOWN",
    },
    {
        "placement": 10,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^R",
        "stage": "Ne",
        "terrain": "Spiral",
        "terrain_law": "X_S^R",
        "igt_label": "winLOSE",
        "realized_word": "win",
        "source_pair": "TiNe",
        "source_precedence": "UP",
    },
    {
        "placement": 11,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^R",
        "stage": "Ni",
        "terrain": "Source",
        "terrain_law": "X_So^R",
        "igt_label": "LOSElose",
        "realized_word": "lose",
        "source_pair": "FeNi",
        "source_precedence": "UP",
    },
    {
        "placement": 12,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "fiber_loop",
        "loop_symbol": "gamma_f^R",
        "stage": "Si",
        "terrain": "Citadel",
        "terrain_law": "X_Ci^R",
        "igt_label": "WINwin",
        "realized_word": "win",
        "source_pair": "SiFe",
        "source_precedence": "DOWN",
    },
    {
        "placement": 13,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^R",
        "stage": "Se",
        "terrain": "Cannon",
        "terrain_law": "X_C^R",
        "igt_label": "loseWIN",
        "realized_word": "WIN",
        "source_pair": "FiSe",
        "source_precedence": "UP",
    },
    {
        "placement": 14,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^R",
        "stage": "Ne",
        "terrain": "Spiral",
        "terrain_law": "X_S^R",
        "igt_label": "winLOSE",
        "realized_word": "LOSE",
        "source_pair": "NeFi",
        "source_precedence": "DOWN",
    },
    {
        "placement": 15,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^R",
        "stage": "Ni",
        "terrain": "Source",
        "terrain_law": "X_So^R",
        "igt_label": "LOSElose",
        "realized_word": "LOSE",
        "source_pair": "NiTe",
        "source_precedence": "DOWN",
    },
    {
        "placement": 16,
        "sheet": "R",
        "sheet_label": "right_chiral_operating_space",
        "loop": "base_lift_loop",
        "loop_symbol": "gamma_b^R",
        "stage": "Si",
        "terrain": "Citadel",
        "terrain_law": "X_Ci^R",
        "igt_label": "WINwin",
        "realized_word": "WIN",
        "source_pair": "TeSi",
        "source_precedence": "UP",
    },
]


def dagger(a: jax.Array) -> jax.Array:
    return jnp.conj(jnp.swapaxes(a, -1, -2))


def trace_real(a: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(a))


def hermitize(rho: jax.Array) -> jax.Array:
    return 0.5 * (rho + dagger(rho))


def normalize_density(rho: jax.Array) -> jax.Array:
    rho = hermitize(rho)
    return rho / jnp.trace(rho)


def spinor(phi: float, chi: float, eta: float) -> jax.Array:
    return jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=CTYPE,
    )


def density_from_spinor(psi: jax.Array) -> jax.Array:
    psi = psi.reshape(2, 1)
    return normalize_density(psi @ dagger(psi))


def loop_density(sheet: str, loop: str, u: float) -> jax.Array:
    eta0 = 0.39 if sheet == "L" else 0.57
    phi0 = 0.23 if sheet == "L" else -0.37
    chi0 = -0.41 if sheet == "L" else 0.29
    if loop == "fiber_loop":
        return density_from_spinor(spinor(phi0 + u, chi0, eta0))
    if loop == "base_lift_loop":
        return density_from_spinor(spinor(phi0 - float(jnp.cos(2.0 * eta0)) * u, chi0 + u, eta0))
    raise ValueError(loop)


def pauli_unitary(generator: jax.Array, dt: float) -> jax.Array:
    coeff_norm = jnp.sqrt(jnp.maximum(0.0, 0.5 * trace_real(generator @ generator)))
    return jnp.cos(coeff_norm * dt) * I2 - 1j * jnp.sin(coeff_norm * dt) * generator / coeff_norm


def unitary_channel(rho: jax.Array, generator: jax.Array, dt: float) -> jax.Array:
    u = pauli_unitary(generator, dt)
    return normalize_density(u @ rho @ dagger(u))


def dephase_axis(rho: jax.Array, axis_op: jax.Array, strength: float) -> jax.Array:
    p_plus = 0.5 * (I2 + axis_op)
    p_minus = 0.5 * (I2 - axis_op)
    pinched = p_plus @ rho @ p_plus + p_minus @ rho @ p_minus
    return normalize_density((1.0 - strength) * rho + strength * pinched)


def depolarize(rho: jax.Array, strength: float) -> jax.Array:
    return normalize_density((1.0 - strength) * rho + strength * 0.5 * I2)


def amplitude_channel(rho: jax.Array, jump: jax.Array, gamma: float) -> jax.Array:
    effect = dagger(jump) @ jump
    vals, vecs = jnp.linalg.eigh(I2 - gamma * effect)
    vals = jnp.clip(jnp.real(vals), 0.0, 1.0)
    k0 = vecs @ jnp.diag(jnp.sqrt(vals).astype(CTYPE)) @ dagger(vecs)
    k1 = jnp.sqrt(jnp.array(gamma, dtype=RTYPE)).astype(CTYPE) * jump
    return normalize_density(k0 @ rho @ dagger(k0) + k1 @ rho @ dagger(k1))


def operator_channel(rho: jax.Array, op_name: str, placement_index: int) -> jax.Array:
    theta = 0.055 + 0.002 * placement_index
    if op_name == "Ti":
        return dephase_axis(rho, SZ, 0.17)
    if op_name == "Te":
        return dephase_axis(rho, SX, 0.19)
    if op_name == "Fi":
        return unitary_channel(rho, SX, theta)
    if op_name == "Fe":
        return unitary_channel(rho, SZ, theta * 1.21)
    raise ValueError(op_name)


def terrain_channel(
    rho: jax.Array,
    placement: dict[str, Any],
    *,
    sign_only_control: bool = False,
    swap_only_control: bool = False,
) -> jax.Array:
    sheet = placement["sheet"]
    stage = placement["stage"]
    generator_sheet = "L" if sign_only_control else sheet
    h_sheet = "L" if swap_only_control else sheet
    h = H0 if h_sheet == "L" else -H0

    if stage == "Se":
        strength = 0.095 if generator_sheet == "L" else 0.145
        return depolarize(unitary_channel(rho, h, 0.037), strength)
    if stage == "Ne":
        if generator_sheet == "L":
            return unitary_channel(rho, h, 0.083)
        return dephase_axis(unitary_channel(rho, h, 0.074), SY, 0.045)
    if stage == "Ni":
        jump = SIGMA_MINUS if generator_sheet == "L" else SIGMA_PLUS
        gamma = 0.13 if generator_sheet == "L" else 0.18
        return amplitude_channel(unitary_channel(rho, h, 0.031), jump, gamma)
    if stage == "Si":
        axis = normalize_axis(0.39 * SX + 0.21 * SY + 0.89 * SZ) if generator_sheet == "L" else normalize_axis(0.72 * SX - 0.18 * SY + 0.61 * SZ)
        k = 0.12 if generator_sheet == "L" else 0.16
        return dephase_axis(unitary_channel(rho, axis, 0.052), axis, k)
    raise ValueError(stage)


def normalize_axis(op: jax.Array) -> jax.Array:
    norm = jnp.sqrt(jnp.maximum(EPS, 0.5 * trace_real(op @ op)))
    return op / norm


def trace_distance(a: jax.Array, b: jax.Array) -> float:
    diff = hermitize(a - b)
    ev = jnp.linalg.eigvalsh(diff)
    return float(0.5 * jnp.sum(jnp.abs(jnp.real(ev))))


@jax.jit
def density_health(rho: jax.Array) -> jax.Array:
    h = hermitize(rho)
    ev = jnp.linalg.eigvalsh(h)
    trace_err = jnp.abs(trace_real(h) - 1.0)
    herm_err = jnp.max(jnp.abs(rho - dagger(rho)))
    return jnp.array([trace_err, herm_err, jnp.min(jnp.real(ev))], dtype=RTYPE)


@jax.jit
def bloch_entropy_purity(rho: jax.Array) -> jax.Array:
    h = hermitize(rho)
    ev = jnp.clip(jnp.real(jnp.linalg.eigvalsh(h)), EPS, 1.0)
    entropy = -jnp.sum(ev * jnp.log2(ev))
    purity = jnp.real(jnp.trace(h @ h))
    bx = jnp.real(jnp.trace(SX @ h))
    by = jnp.real(jnp.trace(SY @ h))
    bz = jnp.real(jnp.trace(SZ @ h))
    coh_z = 2.0 * jnp.abs(h[0, 1])
    coh_x = trace_distance_jit(h, dephase_axis(h, SX, 1.0))
    return jnp.array([bx, by, bz, entropy, purity, coh_z, coh_x], dtype=RTYPE)


@jax.jit
def trace_distance_jit(a: jax.Array, b: jax.Array) -> jax.Array:
    diff = hermitize(a - b)
    ev = jnp.linalg.eigvalsh(diff)
    return 0.5 * jnp.sum(jnp.abs(jnp.real(ev)))


def source_order() -> list[dict[str, Any]]:
    return [dict(p) for p in PLACEMENTS]


def scrambled_order() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for sheet in ["L", "R"]:
        for loop in ["fiber_loop", "base_lift_loop"]:
            chunk = [p for p in PLACEMENTS if p["sheet"] == sheet and p["loop"] == loop]
            out.extend(reversed(chunk))
    return [dict(p) for p in out]


def initial_states() -> dict[str, jax.Array]:
    return {
        "L": density_from_spinor(spinor(0.11, -0.31, 0.42)),
        "R": density_from_spinor(spinor(-0.27, 0.24, 0.61)),
    }


def run_sequence(
    placements: list[dict[str, Any]],
    *,
    sign_only_control: bool = False,
    swap_only_control: bool = False,
    loop_erased_control: bool = False,
) -> dict[str, Any]:
    states = initial_states()
    rows: list[dict[str, Any]] = []
    sig_parts: list[jax.Array] = []
    order_gaps: list[float] = []

    for placement_order, placement in enumerate(placements):
        sheet = placement["sheet"]
        for op_index, op_name in enumerate(OPERATORS):
            u = 0.071 * (placement_order + 1) + 0.029 * (op_index + 1)
            actual_loop = "fiber_loop" if loop_erased_control else placement["loop"]
            loop_rho = loop_density(sheet, actual_loop, u)
            loop_weight = 0.0 if loop_erased_control else (0.055 if placement["loop"] == "fiber_loop" else 0.245)
            rho0 = normalize_density((1.0 - loop_weight) * states[sheet] + loop_weight * loop_rho)

            terr_then_op = operator_channel(
                terrain_channel(
                    rho0,
                    placement,
                    sign_only_control=sign_only_control,
                    swap_only_control=swap_only_control,
                ),
                op_name,
                placement["placement"],
            )
            op_then_terr = terrain_channel(
                operator_channel(rho0, op_name, placement["placement"]),
                placement,
                sign_only_control=sign_only_control,
                swap_only_control=swap_only_control,
            )
            order_gap = trace_distance(terr_then_op, op_then_terr)
            order_gaps.append(order_gap)
            rho1 = terr_then_op if placement["source_precedence"] == "UP" else op_then_terr
            rho1 = normalize_density(rho1)
            states[sheet] = rho1

            health = density_health(rho1)
            readout = bloch_entropy_purity(rho1)
            pass_row = bool(
                float(health[0]) < 1.0e-9
                and float(health[1]) < 1.0e-9
                and float(health[2]) > -1.0e-9
                and all(jnp.isfinite(readout))
            )
            sig_parts.append(readout)
            rows.append(
                {
                    "microstep": len(rows) + 1,
                    "placement": placement["placement"],
                    "placement_order": placement_order + 1,
                    "sheet": sheet,
                    "sheet_label": placement["sheet_label"],
                    "loop": placement["loop"],
                    "actual_loop": actual_loop,
                    "loop_symbol": placement["loop_symbol"],
                    "stage": placement["stage"],
                    "terrain": placement["terrain"],
                    "terrain_law": placement["terrain_law"],
                    "igt_label": placement["igt_label"],
                    "realized_word": placement["realized_word"],
                    "source_pair": placement["source_pair"],
                    "source_precedence": placement["source_precedence"],
                    "operator_substage": op_name,
                    "trace_err": float(health[0]),
                    "hermitian_err": float(health[1]),
                    "min_eval": float(health[2]),
                    "bloch": [float(readout[0]), float(readout[1]), float(readout[2])],
                    "entropy": float(readout[3]),
                    "purity": float(readout[4]),
                    "coherence_z_basis": float(readout[5]),
                    "coherence_x_basis_distance": float(readout[6]),
                    "noncommuting_order_gap": order_gap,
                    "pass": pass_row,
                }
            )

    signature = jnp.concatenate(sig_parts)
    return {
        "rows": rows,
        "signature": signature,
        "order_gaps": order_gaps,
        "final_states": states,
    }


def signature_gap(a: jax.Array, b: jax.Array) -> float:
    return float(jnp.linalg.norm(a - b) / jnp.sqrt(a.shape[0]))


def row_group_gap(rows: list[dict[str, Any]]) -> float:
    left = jnp.array([[*r["bloch"], r["entropy"], r["purity"]] for r in rows if r["sheet"] == "L"], dtype=RTYPE)
    right = jnp.array([[*r["bloch"], r["entropy"], r["purity"]] for r in rows if r["sheet"] == "R"], dtype=RTYPE)
    return float(jnp.linalg.norm(jnp.mean(left, axis=0) - jnp.mean(right, axis=0)))


def summarize() -> dict[str, Any]:
    t0 = time.time()
    canonical = run_sequence(source_order())
    sign_only = run_sequence(source_order(), sign_only_control=True)
    swap_only = run_sequence(source_order(), swap_only_control=True)
    loop_erased = run_sequence(source_order(), loop_erased_control=True)
    scrambled = run_sequence(scrambled_order())

    rows = canonical["rows"]
    placement_keys = {(r["sheet"], r["loop"], r["stage"]) for r in rows}
    sheet_keys = {r["sheet"] for r in rows}
    qit_keys = {"entropy", "purity", "coherence_z_basis", "coherence_x_basis_distance"}
    max_trace_err = max(r["trace_err"] for r in rows)
    max_hermitian_err = max(r["hermitian_err"] for r in rows)
    min_eval = min(r["min_eval"] for r in rows)
    order_gaps = jnp.array(canonical["order_gaps"], dtype=RTYPE)
    row_pass_count = sum(bool(r["pass"]) for r in rows)
    lr_gap = row_group_gap(rows)

    sign_gap = signature_gap(canonical["signature"], sign_only["signature"])
    swap_gap = signature_gap(canonical["signature"], swap_only["signature"])
    loop_gap = signature_gap(canonical["signature"], loop_erased["signature"])
    scramble_gap = signature_gap(canonical["signature"], scrambled["signature"])

    checks = {
        "microstep_rows_64": len(rows) == 64,
        "sixteen_placements_times_four_substages": len(placement_keys) == 16 and len(rows) == 16 * 4,
        "left_right_spaces_present": sheet_keys == {"L", "R"},
        "all_density_rows_finite_trace_psd": (
            row_pass_count == 64 and max_trace_err < 1.0e-9 and max_hermitian_err < 1.0e-9 and min_eval > -1.0e-9
        ),
        "noncommuting_order_gap_positive": float(jnp.mean(order_gaps)) > 1.0e-4 and int(jnp.sum(order_gaps > 1.0e-6)) >= 32,
        "left_right_distinct": lr_gap > 0.05,
        "sign_only_control_changes_signature": sign_gap > 1.0e-3,
        "swap_only_control_changes_signature": swap_gap > 1.0e-3,
        "loop_erased_control_changes_signature": loop_gap > 1.0e-3,
        "stage_order_scramble_changes_signature": scramble_gap > 1.0e-3,
        "qit_readouts_present": all(q in rows[0] for q in qit_keys),
        "promotion_blocked": PROMOTION_ALLOWED is False,
        "julia_not_used": True,
        "pytorch_not_used": True,
    }
    audit_pass = all(checks.values())

    return {
        "sim_id": SIM_ID,
        "name": "JAX Weyl terrain 64-microstep diagnostic",
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "AUDIT_PASS": bool(audit_pass),
        "purpose": "JAX stress/audit of finite source-native L/R Weyl density terrain placements and four operator substages.",
        "scientific_question": "Can the JAX lane execute the 64 source-shaped density microsteps without collapsing chirality sign, ladder/source-sink swap, loop placement, or noncommuting order?",
        "sim_execution_kind": "diagnostic_jax_audit",
        "root_constraints_in_force": {
            "F01": "finite C2 density matrices, 16 placements, 4 operator substages, finite control signatures",
            "N01": "Ti/Te/Fi/Fe operator channels composed before/after noncommuting terrain channels; order-gap control recorded",
        },
        "finite_map": "({rho_L,rho_R}, placement, operator_substage) -> rho_s' plus QIT single-density readouts",
        "domain": {
            "carrier": "rho_L,rho_R in D(C2) derived from Hopf S3 spinors",
            "placements": 16,
            "operator_substages": OPERATORS,
        },
        "codomain_or_output": "64 finite density-channel rows, signature vectors, and control gaps",
        "carrier_layer": "left/right Weyl density operating spaces over Hopf S3 spinor chart",
        "geometry_layer": "fiber/base-lift Hopf loop placement quotient",
        "carrier_realization": "JAX complex128 C2 density matrices; no PyTorch and no NumPy import",
        "peps3d_embedding": "not claimed in this diagnostic; downstream PEPS3D carrier admission remains blocked",
        "spinor_state": "psi_s(phi,chi,eta) in C2; rho_s=psi_s psi_s^dagger",
        "quaternion_action": "not_applicable in this density-only JAX diagnostic",
        "dependency_receipts": [
            "system_v5/READ ONLY Reference Docs/terrain math.md",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md",
            "jax_manifold_layer_independent_suite_results.json",
            "jax_dirac_gamma5_chirality_branch_prune_audit_results.json",
        ],
        "allowed_claims": [
            "JAX diagnostic executes the finite 64-row Weyl terrain/operator object",
            "controls show sheet sign, ladder/source-sink swap, loop placement, and stage order are not collapsed",
        ],
        "promotion_blockers": [
            "no Julia-native Grassmann/full-spinor carrier in this file",
            "no PEPS3D carrier anchor",
            "no joint rho_AB coherent-information/log-negativity readout",
            "no layer completion claim gate",
        ],
        "eligible_consumers": ["JAX/Julia cross-audit planning", "next joint-carrier diagnostic design"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": ["jax", "python_stdlib"],
        "actual_tools_used": ["jax", "python_stdlib"],
        "TOOL_MANIFEST": {
            "jax": {
                "tried": True,
                "used": True,
                "reason": "load-bearing complex128 density channels, x64 health/readout kernels, and signature controls",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "reason": "JSON receipt and bounded file output only",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jax": {
                "tried": True,
                "used": True,
                "reason": "load-bearing complex128 density channels, x64 health/readout kernels, and signature controls",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "reason": "JSON receipt and bounded file output only",
            },
        },
        "tool_integration_depth": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "divergence_log": [
            "Counts/signatures are diagnostic and not a Julia-native full-spinor proof.",
            "Single-density readouts include entropy/purity/coherence; coherent information remains blocked until a finite joint rho_AB is supplied.",
        ],
        "microstep_count": len(rows),
        "row_pass_count": row_pass_count,
        "metrics": {
            "max_trace_err": max_trace_err,
            "max_hermitian_err": max_hermitian_err,
            "min_eval": min_eval,
            "mean_noncommuting_order_gap": float(jnp.mean(order_gaps)),
            "nonzero_order_gap_count": int(jnp.sum(order_gaps > 1.0e-6)),
            "left_right_signature_gap": lr_gap,
            "sign_only_control_gap": sign_gap,
            "swap_only_control_gap": swap_gap,
            "loop_erased_control_gap": loop_gap,
            "stage_order_scramble_gap": scramble_gap,
            "wall_seconds": time.time() - t0,
        },
        "checks": checks,
        "controls": {
            "sign_only": "right sheet keeps H_R=-H0 but collapses right terrain dissipators/projectors to left laws",
            "swap_only": "right sheet keeps right sigma_+/terrain families but collapses Hamiltonian sign to H_L",
            "loop_erased": "all loop injection removed; base-lift visibility cannot contribute",
            "stage_order_scramble": "source stage order reversed inside each sheet/loop block",
        },
        "qit_readout_note": "This diagnostic reads finite single-density QIT quantities S(rho), purity, x/z coherence, and trace-distance signatures. Coherent information/log-negativity are intentionally blocked here because they require a finite joint rho_AB.",
        "microsteps": rows,
    }


def main() -> None:
    result = summarize()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    metrics = result["metrics"]
    print(
        "microsteps={microsteps} pass={passed}/{microsteps} "
        "lr_gap={lr:.6f} sign_gap={sg:.6f} swap_gap={sw:.6f} loop_gap={lg:.6f} order_gap={og:.6f}".format(
            microsteps=result["microstep_count"],
            passed=result["row_pass_count"],
            lr=metrics["left_right_signature_gap"],
            sg=metrics["sign_only_control_gap"],
            sw=metrics["swap_only_control_gap"],
            lg=metrics["loop_erased_control_gap"],
            og=metrics["mean_noncommuting_order_gap"],
        )
    )
    print(f"AUDIT_PASS={result['AUDIT_PASS']}")


if __name__ == "__main__":
    main()
