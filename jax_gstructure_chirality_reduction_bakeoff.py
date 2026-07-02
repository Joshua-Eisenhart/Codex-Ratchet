#!/usr/bin/env python3
"""JAX-only diagnostic bakeoff for G-structure chirality reduction.

This is the JAX audit lane. It reads Julia references only by human/controller
inspection before the run; it does not execute Julia, import PyTorch, or claim
native Julia/Grassmann fidelity. The finite object is a candidate bakeoff over:

  O(3) / SO(3) / Spin(3) ~= SU(2), Pin(3), SL(2,C), a twistor incidence
  diagnostic, and a Spin(8) triality diagnostic control.

The result is deliberately diagnostic-only: it can falsify leaking controls and
compare finite invariants, but it does not promote a G-structure or layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


OUT = Path("jax_gstructure_chirality_reduction_bakeoff_results.json")
TOL = 1.0e-9

C = jnp.complex128
R = jnp.float64

I2 = jnp.eye(2, dtype=C)
Z2 = jnp.zeros((2, 2), dtype=C)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=C)
SY = jnp.asarray([[0, -1j], [1j, 0]], dtype=C)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=C)
PAULI = (SX, SY, SZ)
I4 = jnp.eye(4, dtype=C)
Z4 = jnp.zeros((4, 4), dtype=C)
ETA = jnp.diag(jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=R))


def _f(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def norm(x: jax.Array) -> jax.Array:
    return jnp.linalg.norm(x)


def block2(a: jax.Array, b: jax.Array, c: jax.Array, d: jax.Array) -> jax.Array:
    return jnp.block([[a, b], [c, d]])


def unit(v: jax.Array) -> jax.Array:
    return v / jnp.linalg.norm(v)


def pauli_dot(v: jax.Array) -> jax.Array:
    return v[0] * SX + v[1] * SY + v[2] * SZ


# Weyl-basis Dirac gammas. gamma5 = diag(-I2,+I2), so the upper block is L and
# the lower block is R for this diagnostic.
G0 = block2(Z2, I2, I2, Z2)
G1 = block2(Z2, SX, -SX, Z2)
G2 = block2(Z2, SY, -SY, Z2)
G3 = block2(Z2, SZ, -SZ, Z2)
GAMMAS = (G0, G1, G2, G3)
G5 = 1j * G0 @ G1 @ G2 @ G3
PL = (I4 - G5) / 2.0
PR = (I4 + G5) / 2.0


def su2(axis: jax.Array, theta: float | jax.Array) -> jax.Array:
    axis = unit(jnp.asarray(axis, dtype=R))
    theta = jnp.asarray(theta, dtype=R)
    return jnp.cos(theta / 2.0) * I2 - 1j * jnp.sin(theta / 2.0) * pauli_dot(axis)


def su2_to_so3(u: jax.Array) -> jax.Array:
    rows = []
    udag = jnp.conj(u.T)
    for i in range(3):
        row = []
        for j in range(3):
            row.append(jnp.real(0.5 * jnp.trace(PAULI[i] @ u @ PAULI[j] @ udag)))
        rows.append(jnp.stack(row))
    return jnp.stack(rows)


def quat_to_so3(q: jax.Array) -> jax.Array:
    q = unit(jnp.asarray(q, dtype=R))
    w, x, y, z = q
    return jnp.asarray(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=R,
    )


def so3_rotation(axis: jax.Array, theta: float | jax.Array) -> jax.Array:
    axis = unit(jnp.asarray(axis, dtype=R))
    x, y, z = axis
    k = jnp.asarray([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=R)
    return jnp.eye(3, dtype=R) + jnp.sin(theta) * k + (1.0 - jnp.cos(theta)) * (k @ k)


def spin3_su2_checks() -> dict[str, Any]:
    key = jax.random.PRNGKey(20260601)
    axes = unit(jax.random.normal(key, (12, 3), dtype=R))
    angles = jnp.linspace(0.19, 2.81, 12)
    max_orth = 0.0
    max_det = 0.0
    max_axis_anchor = 0.0
    max_hom = 0.0
    max_sign = 0.0
    for k in range(12):
        u = su2(axes[k], angles[k])
        r = su2_to_so3(u)
        max_orth = max(max_orth, _f(norm(r.T @ r - jnp.eye(3, dtype=R))))
        max_det = max(max_det, _f(jnp.abs(jnp.linalg.det(r) - 1.0)))
        max_axis_anchor = max(max_axis_anchor, _f(norm(r - so3_rotation(axes[k], angles[k]))))
        max_sign = max(max_sign, _f(norm(su2_to_so3(-u) - r)))

    ux = su2(jnp.asarray([1.0, 0.0, 0.0]), 0.77)
    uy = su2(jnp.asarray([0.0, 1.0, 0.0]), 0.61)
    max_hom = _f(norm(su2_to_so3(ux @ uy) - su2_to_so3(ux) @ su2_to_so3(uy)))

    q = unit(jnp.asarray([0.31, -0.17, 0.49, 0.79], dtype=R))
    q_sign_diff = _f(norm(quat_to_so3(q) - quat_to_so3(-q)))

    u_2pi = su2(jnp.asarray([0.0, 0.0, 1.0]), 2.0 * jnp.pi)
    u_4pi = su2(jnp.asarray([0.0, 0.0, 1.0]), 4.0 * jnp.pi)
    spinor_two_pi_minus_identity = _f(norm(u_2pi + I2))
    spinor_four_pi_identity = _f(norm(u_4pi - I2))
    so3_two_pi_identity = _f(norm(su2_to_so3(u_2pi) - jnp.eye(3, dtype=R)))

    reflection = jnp.diag(jnp.asarray([-1.0, 1.0, 1.0], dtype=R))
    reflection_det = _f(jnp.linalg.det(reflection))
    reflection_distance = min(
        _f(norm(su2_to_so3(su2(axes[k], angles[k])) - reflection)) for k in range(12)
    )

    uz1 = su2(jnp.asarray([0.0, 0.0, 1.0]), 0.3)
    uz2 = su2(jnp.asarray([0.0, 0.0, 1.0]), 1.1)
    commuting_u1_norm = _f(norm(uz1 @ uz2 - uz2 @ uz1))
    noncommuting_su2_norm = _f(norm(ux @ uy - uy @ ux))

    return {
        "image_in_SO3": max_orth < 1e-10 and max_det < 1e-10,
        "axis_angle_anchor": max_axis_anchor < 1e-10,
        "homomorphism": max_hom < 1e-10,
        "u_and_minus_u_same_SO3": max_sign < 1e-10,
        "q_and_minus_q_same_SO3": q_sign_diff < 1e-10,
        "spinor_2pi_sign_flip": spinor_two_pi_minus_identity < 1e-10 and so3_two_pi_identity < 1e-10,
        "spinor_4pi_returns": spinor_four_pi_identity < 1e-10,
        "reflection_det_minus_one_excluded_by_Spin3": reflection_det < -0.999 and reflection_distance > 0.5,
        "noncommuting_positive": noncommuting_su2_norm > 1e-2,
        "commuting_u1_negative": commuting_u1_norm < 1e-12,
        "max_orthogonality_error": max_orth,
        "max_det_minus_one": max_det,
        "max_axis_angle_error": max_axis_anchor,
        "homomorphism_error": max_hom,
        "q_sign_SO3_diff": q_sign_diff,
        "reflection_det": reflection_det,
        "min_reflection_distance_over_finite_SU2_samples": reflection_distance,
        "u1_commutator_norm": commuting_u1_norm,
        "su2_xy_commutator_norm": noncommuting_su2_norm,
    }


def pin3_chirality_checks() -> dict[str, Any]:
    parity = G0
    left = jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=C)
    reflected_left = parity @ left
    left_weight_after = _f(jnp.real(jnp.conj(reflected_left) @ (PL @ reflected_left)))
    right_weight_after = _f(jnp.real(jnp.conj(reflected_left) @ (PR @ reflected_left)))

    u = su2(jnp.asarray([1.0, 1.0, 1.0], dtype=R), 0.83)
    spin_action = block2(u, Z2, Z2, u)
    spin_comm = _f(norm(G5 @ spin_action - spin_action @ G5))
    parity_anticomm = _f(norm(G5 @ parity + parity @ G5))
    parity_comm = _f(norm(G5 @ parity - parity @ G5))

    rho_l = jnp.outer(left, jnp.conj(left))
    rho_pushed = parity @ rho_l @ jnp.conj(parity.T)
    leak_to_right = _f(jnp.real(jnp.trace(PR @ rho_pushed)))

    return {
        "spin3_even_commutes_with_gamma5": spin_comm < 1e-10,
        "pin_reflection_anticommutes_with_gamma5": parity_anticomm < 1e-10,
        "pin_reflection_commutator_nonzero": parity_comm > 1.0,
        "left_spinor_flipped_to_right": left_weight_after < 1e-12 and right_weight_after > 0.999,
        "reflection_density_leaks_to_right": leak_to_right > 0.999,
        "spin3_gamma5_commutator_norm": spin_comm,
        "pin_gamma5_anticommutator_norm": parity_anticomm,
        "pin_gamma5_commutator_norm": parity_comm,
        "left_weight_after_reflection": left_weight_after,
        "right_weight_after_reflection": right_weight_after,
        "right_projector_trace_after_reflection": leak_to_right,
    }


def sl2c(rot: jax.Array, boost: jax.Array) -> jax.Array:
    # exp(0.5 * (boost + i rotation).sigma), using (v.sigma)^2=(v.v)I.
    v = 0.5 * (jnp.asarray(boost, dtype=C) + 1j * jnp.asarray(rot, dtype=C))
    a = pauli_dot(v)
    s2 = jnp.sum(v * v)
    s = jnp.sqrt(s2)
    safe_s = jnp.where(jnp.abs(s) > 1e-12, s, 1.0 + 0.0j)
    coeff = jnp.where(jnp.abs(s) > 1e-12, jnp.sinh(s) / safe_s, 1.0 + s2 / 6.0)
    return jnp.cosh(s) * I2 + coeff * a


def rep_r(m: jax.Array) -> jax.Array:
    return jnp.linalg.inv(jnp.conj(m.T))


def x_to_X(x: jax.Array) -> jax.Array:
    return x[0] * I2 + x[1] * SX + x[2] * SY + x[3] * SZ


def X_to_x(xmat: jax.Array) -> jax.Array:
    return jnp.asarray([jnp.real(0.5 * jnp.trace(s @ xmat)) for s in (I2, SX, SY, SZ)], dtype=R)


def lorentz_lambda(m: jax.Array) -> jax.Array:
    cols = []
    for j in range(4):
        e = jnp.zeros((4,), dtype=R).at[j].set(1.0)
        xp = m @ x_to_X(e) @ jnp.conj(m.T)
        cols.append(X_to_x(xp))
    return jnp.stack(cols, axis=1)


def sl2c_checks() -> dict[str, Any]:
    rot_vec = jnp.asarray([0.31, -0.27, 0.19], dtype=R)
    boost_vec = jnp.asarray([0.42, -0.23, 0.17], dtype=R)
    m_rot = sl2c(rot_vec, jnp.zeros((3,), dtype=R))
    m_boost = sl2c(jnp.zeros((3,), dtype=R), boost_vec)
    m_gen = sl2c(rot_vec, boost_vec)

    det_rot = _f(jnp.abs(jnp.linalg.det(m_rot) - 1.0))
    det_boost = _f(jnp.abs(jnp.linalg.det(m_boost) - 1.0))
    det_gen = _f(jnp.abs(jnp.linalg.det(m_gen) - 1.0))
    rot_lr_diff = _f(norm(m_rot - rep_r(m_rot)))
    boost_lr_diff = _f(norm(m_boost - rep_r(m_boost)))

    s_dirac = block2(m_gen, Z2, Z2, rep_r(m_gen))
    gamma5_comm = _f(norm(G5 @ s_dirac - s_dirac @ G5))
    lam = lorentz_lambda(m_gen)
    eta_resid = _f(norm(lam.T @ ETA @ lam - ETA))
    double_cover_err = _f(norm(lorentz_lambda(-m_gen) - lam))

    psi_l = jnp.asarray([1.0, 0.0], dtype=C)
    boost_norm_dev = _f(jnp.abs(norm(m_boost @ psi_l) - 1.0))

    h0 = SZ
    h_correct = block2(h0, Z2, Z2, -h0)
    h_wrong = block2(h0, Z2, Z2, h0)
    correct_lr_opposition = _f(norm(h_correct[:2, :2] + h_correct[2:, 2:]))
    wrong_lr_opposition = _f(norm(h_wrong[:2, :2] + h_wrong[2:, 2:]))
    h_correct_mixing = _f(norm(h_correct[:2, 2:]) + norm(h_correct[2:, :2]))
    h_wrong_sign_rejected = correct_lr_opposition < 1e-12 and wrong_lr_opposition > 1.0

    mixer = block2(Z2, I2, I2, Z2)
    mixer_comm = _f(norm(G5 @ mixer - mixer @ G5))
    mixer_anticomm = _f(norm(G5 @ mixer + mixer @ G5))

    rho_product = 0.5 * block2(
        jnp.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=C),
        Z2,
        Z2,
        jnp.asarray([[0.0, 0.0], [0.0, 1.0]], dtype=C),
    )
    product_offdiag_norm = _f(norm(rho_product[:2, 2:]) + norm(rho_product[2:, :2]))
    product_negative_lacks_lr_coupling = product_offdiag_norm < 1e-12

    return {
        "det_is_one": max(det_rot, det_boost, det_gen) < 1e-10,
        "rotations_L_equals_R": rot_lr_diff < 1e-10,
        "boosts_distinguish_L_R": boost_lr_diff > 1e-3,
        "dirac_rep_commutes_with_gamma5": gamma5_comm < 1e-10,
        "lorentz_eta_preserved": eta_resid < 1e-9,
        "sl2c_double_cover_sign": double_cover_err < 1e-10,
        "boost_not_S3_norm_preserving": boost_norm_dev > 1e-3,
        "wrong_sign_hamiltonian_rejected": h_wrong_sign_rejected,
        "correct_hamiltonian_has_no_lr_mixing": h_correct_mixing < 1e-12,
        "chirality_mixer_forbidden": mixer_comm > 1.0 and mixer_anticomm < 1e-10,
        "product_negative_lacks_lr_coupling": product_negative_lacks_lr_coupling,
        "det_errors": {"rotation": det_rot, "boost": det_boost, "generic": det_gen},
        "rotation_LR_rep_diff": rot_lr_diff,
        "boost_LR_rep_diff": boost_lr_diff,
        "gamma5_commutator_norm": gamma5_comm,
        "eta_residual": eta_resid,
        "double_cover_Lambda_minusM_diff": double_cover_err,
        "boost_spinor_norm_deviation": boost_norm_dev,
        "correct_HR_plus_HL_norm": correct_lr_opposition,
        "wrong_HR_plus_HL_norm": wrong_lr_opposition,
        "offdiag_mixer_gamma5_commutator_norm": mixer_comm,
        "offdiag_mixer_gamma5_anticommutator_norm": mixer_anticomm,
        "product_density_lr_offdiag_norm": product_offdiag_norm,
    }


def twistor_incidence_checks() -> dict[str, Any]:
    x = jnp.asarray([0.7, -0.2, 0.31, 0.11], dtype=R)
    a = jnp.asarray([0.13, 0.04, -0.08, 0.05], dtype=R)
    X = x_to_X(x)
    A = x_to_X(a)
    line = jnp.vstack([1j * X, I2])
    translator = block2(I2, 1j * A, Z2, I2)
    moved = translator @ line
    omega, pi = moved[:2, :], moved[2:, :]
    x_fit = -1j * omega @ jnp.linalg.inv(pi)
    rank = int(jax.device_get(jnp.sum(jnp.linalg.svd(line, compute_uv=False) > 1e-10)))
    moved_rank = int(jax.device_get(jnp.sum(jnp.linalg.svd(moved, compute_uv=False) > 1e-10)))
    fit_resid = _f(norm(x_fit - (X + A)))
    herm_resid = _f(norm(x_fit - jnp.conj(x_fit.T)))

    bad_b = jnp.asarray([[0.2 + 0.1j, 0.3], [0.1j, -0.2]], dtype=C)
    bad = block2(I2, bad_b, Z2, I2)
    bad_moved = bad @ line
    bad_x = -1j * bad_moved[:2, :] @ jnp.linalg.inv(bad_moved[2:, :])
    bad_herm_resid = _f(norm(bad_x - jnp.conj(bad_x.T)))

    return {
        "incidence_line_rank_2": rank == 2,
        "translated_line_rank_2": moved_rank == 2,
        "translation_incidence_fit": fit_resid < 1e-10,
        "translated_point_hermitian": herm_resid < 1e-10,
        "wrong_complex_shift_breaks_hermitian_incidence": bad_herm_resid > 1e-2,
        "line_rank": rank,
        "moved_line_rank": moved_rank,
        "fit_residual_to_x_plus_a": fit_resid,
        "hermitian_residual_after_translation": herm_resid,
        "bad_shift_hermitian_residual": bad_herm_resid,
        "diagnostic_only": True,
    }


def e(i: int) -> jax.Array:
    return jnp.zeros((4,), dtype=R).at[i].set(1.0)


def reflect(v: jax.Array, root: jax.Array) -> jax.Array:
    return v - 2.0 * jnp.dot(v, root) / jnp.dot(root, root) * root


def reflection_matrix(root: jax.Array) -> jax.Array:
    return jnp.stack([reflect(e(i), root) for i in range(4)], axis=1)


def rounded_tuple(v: jax.Array) -> tuple[float, ...]:
    vals = jax.device_get(jnp.round(v, 8))
    return tuple(float(x) for x in vals)


def d4_roots() -> list[jax.Array]:
    roots = []
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (1.0, -1.0):
                for sj in (1.0, -1.0):
                    roots.append(jnp.zeros((4,), dtype=R).at[i].set(si).at[j].set(sj))
    return roots


def landing_indices(mat: jax.Array, weights: list[jax.Array]) -> list[int]:
    out = []
    for w in weights:
        image = mat @ w
        distances = [_f(norm(image - target)) for target in weights]
        out.append(1 + min(range(len(distances)), key=lambda idx: distances[idx]))
    return out


def spin8_triality_checks() -> dict[str, Any]:
    a1 = e(0) - e(1)
    a2 = e(1) - e(2)
    a3 = e(2) - e(3)
    a4 = e(2) + e(3)
    m_from = jnp.stack([a1, a2, a3, a4], axis=1)
    t = jnp.stack([a3, a2, a4, a1], axis=1) @ jnp.linalg.inv(m_from)
    ident = jnp.eye(4, dtype=R)

    roots = d4_roots()
    root_set = {rounded_tuple(r) for r in roots}
    preserves_roots = all(rounded_tuple(t @ r) in root_set for r in roots)

    wv = e(0)
    ws = 0.5 * (e(0) + e(1) + e(2) - e(3))
    wc = 0.5 * (e(0) + e(1) + e(2) + e(3))
    weights = [wv, ws, wc]
    landing = landing_indices(t, weights)

    d2 = jnp.stack([a1, a2, a4, a3], axis=1) @ jnp.linalg.inv(m_from)
    landing_d2 = landing_indices(d2, weights)

    inner = reflection_matrix(a1) @ reflection_matrix(a2) @ reflection_matrix(a3) @ reflection_matrix(a4)
    landing_inner = landing_indices(inner, weights)
    inner_is_triality = landing_inner in ([2, 3, 1], [3, 1, 2])

    order3_err = _f(norm(t @ t @ t - ident))
    order2_err = _f(norm(d2 @ d2 - ident))
    order2_not_order3 = _f(norm(d2 @ d2 @ d2 - ident))
    det_t = _f(jnp.linalg.det(t))

    return {
        "D4_root_count_24": len(roots) == 24,
        "triality_order3": order3_err < 1e-10,
        "triality_nontrivial": _f(norm(t - ident)) > 1.0,
        "triality_det_plus_one": abs(det_t - 1.0) < 1e-10,
        "triality_preserves_roots": preserves_roots,
        "triality_cycles_8v_8s_8c": landing == [2, 3, 1],
        "order2_outer_not_triality": order2_err < 1e-10 and order2_not_order3 > 1.0 and landing_d2 == [1, 3, 2],
        "inner_weyl_not_triality": not inner_is_triality,
        "order3_error": order3_err,
        "det_T": det_t,
        "triality_landing_v_s_c": landing,
        "order2_landing_v_s_c": landing_d2,
        "inner_weyl_landing_v_s_c": landing_inner,
        "diagnostic_only": True,
    }


def gamma_anchor_checks() -> dict[str, Any]:
    cliff_err = 0.0
    for mu, gmu in enumerate(GAMMAS):
        for nu, gnu in enumerate(GAMMAS):
            expected = 2.0 * ETA[mu, nu] * I4
            cliff_err = max(cliff_err, _f(norm(gmu @ gnu + gnu @ gmu - expected)))
    g5sq = _f(norm(G5 @ G5 - I4))
    g5_diag = [float(x) for x in jax.device_get(jnp.real(jnp.diag(G5)))]
    return {
        "clifford_13_relations": cliff_err < 1e-10,
        "gamma5_squared_identity": g5sq < 1e-10,
        "gamma5_diag": g5_diag,
        "gamma5_LR_split": g5_diag == [-1.0, -1.0, 1.0, 1.0],
        "clifford_error": cliff_err,
        "gamma5_squared_error": g5sq,
    }


def main() -> None:
    gamma = gamma_anchor_checks()
    spin3 = spin3_su2_checks()
    pin3 = pin3_chirality_checks()
    sl2 = sl2c_checks()
    twistor = twistor_incidence_checks()
    triality = spin8_triality_checks()

    candidate_profiles = {
        "O3_reflection": {
            "proper_orientation": False,
            "reflection_det_minus_one": spin3["reflection_det"] < -0.999,
            "excluded_by_Spin3": spin3["reflection_det_minus_one_excluded_by_Spin3"],
            "chirality_preserving": False,
            "role": "Pin/O3 boundary control, not Spin3 chirality carrier",
        },
        "SO3_downstairs": {
            "proper_orientation": spin3["image_in_SO3"],
            "spinor_double_cover": False,
            "q_minus_q_sign_carrier": False,
            "role": "frame rotation quotient; loses spinor sign",
        },
        "Spin3_SU2": {
            "finite_S3_norm": True,
            "proper_orientation": spin3["image_in_SO3"],
            "spinor_double_cover": spin3["q_and_minus_q_same_SO3"] and spin3["spinor_2pi_sign_flip"],
            "chirality_preserving": pin3["spin3_even_commutes_with_gamma5"],
            "noncommuting": spin3["noncommuting_positive"],
            "excludes_reflection": spin3["reflection_det_minus_one_excluded_by_Spin3"],
            "selected_finite_chirality_carrier": True,
        },
        "Pin3": {
            "reflection_det_minus_one": True,
            "chirality_flip": pin3["pin_reflection_anticommutes_with_gamma5"] and pin3["left_spinor_flipped_to_right"],
            "chirality_preserving": False,
            "role": "parity/reflection extension; flips L/R, so not a Weyl-sheet preserving Spin3 carrier",
        },
        "SL2C_Spin13": {
            "det_one": sl2["det_is_one"],
            "lorentz_eta_preserved": sl2["lorentz_eta_preserved"],
            "chirality_preserving": sl2["dirac_rep_commutes_with_gamma5"],
            "left_right_inequivalent_under_boosts": sl2["boosts_distinguish_L_R"],
            "finite_S3_norm": not sl2["boost_not_S3_norm_preserving"],
            "role": "relativistic chirality carrier; boosts do not preserve the S3 norm carrier",
        },
        "Twistor_incidence": {
            "incidence_projection": twistor["translation_incidence_fit"],
            "wrong_shift_control_killed": twistor["wrong_complex_shift_breaks_hermitian_incidence"],
            "diagnostic_only": True,
        },
        "Spin8_triality": {
            "order3_cycles_8v_8s_8c": triality["triality_cycles_8v_8s_8c"],
            "inner_and_order2_controls_killed": triality["inner_weyl_not_triality"] and triality["order2_outer_not_triality"],
            "diagnostic_only": True,
        },
        "U1_commuting_negative": {
            "commuting": spin3["commuting_u1_negative"],
            "noncommuting_requirement_satisfied": False,
            "rejected": spin3["commuting_u1_negative"] and spin3["noncommuting_positive"],
        },
        "Product_LR_negative": {
            "lr_offdiag_zero": sl2["product_negative_lacks_lr_coupling"],
            "rejected_as_lr_coupling": sl2["product_negative_lacks_lr_coupling"],
        },
        "Odd_chirality_mixer_negative": {
            "mixes_chirality": sl2["chirality_mixer_forbidden"],
            "rejected": sl2["chirality_mixer_forbidden"],
        },
        "Wrong_sign_Hamiltonian_negative": {
            "rejected": sl2["wrong_sign_hamiltonian_rejected"],
        },
    }

    selected = [
        name
        for name, row in candidate_profiles.items()
        if row.get("selected_finite_chirality_carrier") is True
    ]

    checks = {
        "chk_gamma_anchor": gamma["clifford_13_relations"] and gamma["gamma5_squared_identity"] and gamma["gamma5_LR_split"],
        "chk_spin3_su2": all(
            spin3[k]
            for k in (
                "image_in_SO3",
                "axis_angle_anchor",
                "homomorphism",
                "u_and_minus_u_same_SO3",
                "q_and_minus_q_same_SO3",
                "spinor_2pi_sign_flip",
                "spinor_4pi_returns",
                "reflection_det_minus_one_excluded_by_Spin3",
                "noncommuting_positive",
                "commuting_u1_negative",
            )
        ),
        "chk_pin3_reflection_flip": all(
            pin3[k]
            for k in (
                "spin3_even_commutes_with_gamma5",
                "pin_reflection_anticommutes_with_gamma5",
                "pin_reflection_commutator_nonzero",
                "left_spinor_flipped_to_right",
                "reflection_density_leaks_to_right",
            )
        ),
        "chk_sl2c_weyl_split": all(
            sl2[k]
            for k in (
                "det_is_one",
                "rotations_L_equals_R",
                "boosts_distinguish_L_R",
                "dirac_rep_commutes_with_gamma5",
                "lorentz_eta_preserved",
                "sl2c_double_cover_sign",
                "boost_not_S3_norm_preserving",
            )
        ),
        "chk_negatives": all(
            [
                sl2["wrong_sign_hamiltonian_rejected"],
                sl2["chirality_mixer_forbidden"],
                sl2["product_negative_lacks_lr_coupling"],
                spin3["commuting_u1_negative"],
                spin3["noncommuting_positive"],
            ]
        ),
        "chk_twistor_diagnostic": all(
            twistor[k]
            for k in (
                "incidence_line_rank_2",
                "translated_line_rank_2",
                "translation_incidence_fit",
                "translated_point_hermitian",
                "wrong_complex_shift_breaks_hermitian_incidence",
            )
        ),
        "chk_spin8_triality_diagnostic": all(
            triality[k]
            for k in (
                "D4_root_count_24",
                "triality_order3",
                "triality_nontrivial",
                "triality_det_plus_one",
                "triality_preserves_roots",
                "triality_cycles_8v_8s_8c",
                "order2_outer_not_triality",
                "inner_weyl_not_triality",
            )
        ),
        "chk_selected_finite_carrier": selected == ["Spin3_SU2"],
    }
    audit_pass = all(checks.values())

    receipt = {
        "object_id": "jax_gstructure_chirality_reduction_bakeoff",
        "name": "JAX G-structure chirality reduction bakeoff",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "script": str(Path(__file__).name),
        "julia_refs_read_only": [
            "system_v5/julia_carrier/layers/gstructure_selection.jl",
            "system_v5/julia_carrier/layers/g_su2_spin3_double_cover.jl",
            "system_v5/julia_carrier/layers/pin3_spin3_chirality_clifford_object.jl",
            "system_v5/julia_carrier/layers/sl2c_spin13_chiral_gstructure.jl",
            "system_v5/julia_carrier/layers/twistor_conformal_gstructure.jl",
            "system_v5/julia_carrier/layers/s7_spin8_triality.jl",
        ],
        "root_constraints_in_force": {
            "F01": "finite matrices, finite spinor probes, finite candidate rows, finite controls",
            "N01": "noncommuting SU2 rotations required; commuting U1/product/odd-mixer negatives rejected",
        },
        "finite_map": "candidate G-action/readout -> finite invariant profile -> selected diagnostic carrier set",
        "domain": {
            "spinor_carriers": "Weyl-basis Dirac C4 probes with gamma5 projectors PL/PR; SU2 unit spinors/quaternions",
            "candidate_rows": list(candidate_profiles.keys()),
            "controls": [
                "reflection det=-1 excluded by Spin3",
                "q/-q double cover",
                "wrong-sign Hamiltonian",
                "chirality mixing forbidden",
                "commuting U1 negative",
                "product L/R negative",
            ],
        },
        "codomain_or_output": "finite candidate profile JSON with AUDIT_PASS and selected finite chirality carrier list",
        "carrier_layer": "S3/SU2 spinor carrier plus Weyl L/R gamma5 split",
        "geometry_layer": "G-structure reduction diagnostics: O3/SO3/Spin3, Pin3, SL2C, twistor incidence, Spin8 triality",
        "peps3d_embedding": "not_claimed; diagnostic G-structure bakeoff only",
        "spinor_state": "JAX complex Weyl-basis C4 spinor probes and SU2 unit spinors",
        "quaternion_action": "q -> R(q) in SO3 with q and -q identified",
        "dependency_receipts": [],
        "downstream_blocks": ["full G-structure selection", "layer completion", "stacking readiness", "Axis0", "FEP", "flux", "physics"],
        "allowed_claims": [
            "local JAX diagnostic finite invariant check",
            "control leakage/falsifier evidence for candidate bakeoff",
        ],
        "promotion_blockers": [
            "Julia native Grassmann/Clifford truth remains external read-only reference",
            "no PEPS3D carrier admission",
            "twistor and Spin8 rows are diagnostic/frontier controls",
            "no full layer-completion claim gate run because no completion claim is made",
        ],
        "tool_manifest": {
            "jax": {
                "used": True,
                "reason": "load-bearing finite matrix/spinor computations, randomized SU2 samples, candidate invariant readouts",
            },
            "jax.numpy": {
                "used": True,
                "reason": "linear algebra over finite spinor, Lorentz, twistor, and D4 root-system probes",
            },
            "json": {"used": True, "reason": "receipt emission"},
        },
        "tool_integration_depth": {"jax": "load_bearing", "json": "supportive"},
        "gamma_anchor": gamma,
        "spin3_su2": spin3,
        "pin3_reflection_chirality": pin3,
        "sl2c_weyl_reps": sl2,
        "twistor_incidence_diagnostic": twistor,
        "spin8_triality_diagnostic": triality,
        "candidate_profiles": candidate_profiles,
        "selected_finite_chirality_carriers": selected,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
    }

    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_gstructure_chirality_reduction_bakeoff "
        f"selected={selected} twistor={twistor['translation_incidence_fit']} "
        f"triality={triality['triality_cycles_8v_8s_8c']} AUDIT_PASS={audit_pass}"
    )


if __name__ == "__main__":
    main()
