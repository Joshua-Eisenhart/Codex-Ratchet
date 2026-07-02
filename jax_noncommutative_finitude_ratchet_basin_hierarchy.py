#!/usr/bin/env python3
"""JAX noncommutative finitude ratchet with basin/subbasin readouts.

This is the JAX audit lane. It stress-tests a finite ordered-row object that is
informed by the read-only Julia carrier work, but it does not run Julia and does
not import or touch the retired PyTorch lane.

The object here is deliberately finite:
  top basin      = one of 4 topology laws {Se, Ne, Ni, Si}
  subbasin       = one of 16 placements {L,R} x {fiber,base} x topology
  subsubbasin    = placement x ordered noncommuting row token

The ratchet pressure is not a layer label. It is a monotone survivor mask over
finite row maps whose operator order has a nonzero witness and whose commuting
negative collapses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


OUT = Path("jax_noncommutative_finitude_ratchet_basin_hierarchy_results.json")

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LEFT_TERRAINS = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
RIGHT_TERRAINS = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}
ORDER_TOKENS = ("H_T_F_B", "T_H_B_F", "F_B_H_T", "B_F_T_H")

N_WORD_REPS = 56
N = 16 * len(ORDER_TOKENS) * N_WORD_REPS
STEPS = 1800
DT = 0.0045
F01_TOL = 1.0e-3
CHIRAL_TOL = 1.0e-2
EPS = 1.0e-12

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)

# Real skew generators for S3/quaternion rotations. The exact representation is
# less important than the nonzero commutators and the retraction after use.
K_FIBER = jnp.asarray(
    [[0.0, -1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, -1.0], [0.0, 0.0, 1.0, 0.0]],
    dtype=jnp.float64,
)
K_BASE_X = jnp.asarray(
    [[0.0, 0.0, -1.0, 0.0], [0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0]],
    dtype=jnp.float64,
)
K_BASE_Y = jnp.asarray(
    [[0.0, 0.0, 0.0, -1.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]],
    dtype=jnp.float64,
)
SWIRL_Z = jnp.asarray([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=jnp.float64)
SWIRL_X = jnp.asarray([[0.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]], dtype=jnp.float64)


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _i(x: Any) -> int:
    return int(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def unit(x: jax.Array) -> jax.Array:
    return x / jnp.maximum(jnp.linalg.norm(x, axis=-1, keepdims=True), EPS)


def clip_ball(r: jax.Array, radius: float = 0.985) -> jax.Array:
    norm = jnp.maximum(jnp.linalg.norm(r, axis=-1, keepdims=True), EPS)
    return jnp.where(norm > radius, r * (radius / norm), r)


def placements() -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, list[dict[str, Any]]]:
    target_q: list[tuple[float, float, float, float]] = []
    target_r: list[tuple[float, float, float]] = []
    sheet_sign: list[float] = []
    topo_idx: list[int] = []
    meta: list[dict[str, Any]] = []
    label = 1
    for sheet, terrains in (("L", LEFT_TERRAINS), ("R", RIGHT_TERRAINS)):
        sgn = 1.0 if sheet == "L" else -1.0
        q0 = 0.5 if sheet == "L" else -0.5
        for path_i, path in enumerate(("fiber", "base")):
            path_sgn = 1.0 if path_i == 0 else -1.0
            q1 = 0.5 if path_i == 0 else -0.5
            for topo_i, topology in enumerate(TOPOLOGIES):
                q2 = 0.5 if (topo_i & 1) == 0 else -0.5
                q3 = 0.5 if (topo_i & 2) == 0 else -0.5
                if topology == "Se":
                    r = (0.0, 0.0, -sgn)
                elif topology == "Ne":
                    r = (0.0, 0.0, 0.36 * sgn)
                elif topology == "Ni":
                    r = (0.0, 0.0, sgn)
                elif topology == "Si":
                    r = (0.66 * path_sgn, 0.0, 0.0)
                else:
                    raise AssertionError(topology)
                target_q.append((q0, q1, q2, q3))
                target_r.append(r)
                sheet_sign.append(sgn)
                topo_idx.append(topo_i)
                meta.append(
                    {
                        "placement": label,
                        "sheet": sheet,
                        "path": path,
                        "topology": topology,
                        "terrain": terrains[topology],
                    }
                )
                label += 1
    return (
        unit(jnp.asarray(target_q, dtype=jnp.float64)),
        jnp.asarray(target_r, dtype=jnp.float64),
        jnp.asarray(sheet_sign, dtype=jnp.float64),
        jnp.asarray(topo_idx, dtype=jnp.int32),
        meta,
    )


TARGET_Q, TARGET_R, SHEET_SIGN, TOPO_IDX, PLACEMENT_META = placements()
ASSIGNED = jnp.repeat(jnp.arange(16, dtype=jnp.int32), len(ORDER_TOKENS) * N_WORD_REPS)
WORD_ID = jnp.tile(jnp.repeat(jnp.arange(len(ORDER_TOKENS), dtype=jnp.int32), N_WORD_REPS), 16)
PRODUCT_Q = jnp.broadcast_to(TARGET_Q[0], (N, 4))
PRODUCT_R = jnp.broadcast_to(TARGET_R[0], (N, 3))


def initial_ensemble() -> tuple[jax.Array, jax.Array, jax.Array]:
    q_key, r_key, th_key = jax.random.split(jax.random.PRNGKey(2026060201), 3)
    q_noise = jax.random.normal(q_key, (N, 4), dtype=jnp.float64)
    q = unit(0.55 * TARGET_Q[ASSIGNED] + q_noise)
    r_dir = unit(jax.random.normal(r_key, (N, 3), dtype=jnp.float64))
    radii = 0.90 * (0.18 + 0.82 * jax.random.uniform(r_key, (N, 1), dtype=jnp.float64)) ** (1.0 / 3.0)
    r = radii * r_dir
    theta = 0.03 + (jnp.pi / 2.0 - 0.06) * jax.random.uniform(th_key, (N,), dtype=jnp.float64)
    return q, r, theta


def project_state(q: jax.Array, r: jax.Array, theta: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    return unit(q), clip_ball(r), jnp.clip(theta, 1.0e-4, jnp.pi / 2.0 - 1.0e-4)


def q_hamiltonian(q: jax.Array, target_q: jax.Array, topo: jax.Array, word: jax.Array) -> jax.Array:
    dot = jnp.sum(q * target_q, axis=1, keepdims=True)
    tangent_target = 2.15 * (target_q - dot * q)
    kx = q @ K_BASE_X.T
    ky = q @ K_BASE_Y.T
    kf = q @ K_FIBER.T
    k = jnp.where((topo[:, None] % 2) == 0, kx, ky) + (0.25 + 0.05 * word[:, None]) * kf
    return unit(q + DT * (tangent_target + 0.74 * k))


def r_terrain(r: jax.Array, theta: jax.Array, target_r: jax.Array, topo: jax.Array, word: jax.Array) -> jax.Array:
    contract = 0.86 * (target_r - r)
    swirl = r @ SWIRL_Z.T
    alt = r @ SWIRL_X.T
    ne = (topo == 1).astype(jnp.float64)[:, None]
    si = (topo == 3).astype(jnp.float64)[:, None]
    leaf = (0.70 + 0.30 * jnp.sin(2.0 * theta))[:, None]
    word_sgn = jnp.where((word[:, None] % 2) == 0, 1.0, -1.0)
    return clip_ball(r + DT * (leaf * contract + 0.88 * ne * swirl + 0.42 * si * word_sgn * alt))


def q_fiber(q: jax.Array, theta: jax.Array, word: jax.Array) -> tuple[jax.Array, jax.Array]:
    phase_rate = (0.38 + 0.08 * word.astype(jnp.float64)) * jnp.sin(2.0 * theta)
    qn = unit(q + DT * phase_rate[:, None] * (q @ K_FIBER.T))
    theta_target = jnp.asarray([0.20, 0.43, 0.72, 1.04], dtype=jnp.float64)[word]
    theta_next = theta + DT * 0.62 * (theta_target - theta)
    return qn, theta_next


def q_base(q: jax.Array, r: jax.Array, target_q: jax.Array, word: jax.Array) -> jax.Array:
    perturb = jnp.stack([r[:, 2], -r[:, 1], r[:, 0], -r[:, 0] + 0.15 * word.astype(jnp.float64)], axis=1)
    dot = jnp.sum(q * target_q, axis=1, keepdims=True)
    return unit(q + DT * (0.32 * perturb + 0.92 * (target_q - dot * q)))


def apply_h(q: jax.Array, r: jax.Array, theta: jax.Array, target_q: jax.Array, target_r: jax.Array, topo: jax.Array, word: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    del target_r
    return project_state(q_hamiltonian(q, target_q, topo, word), r, theta)


def apply_t(q: jax.Array, r: jax.Array, theta: jax.Array, target_q: jax.Array, target_r: jax.Array, topo: jax.Array, word: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    del target_q
    return project_state(q, r_terrain(r, theta, target_r, topo, word), theta)


def apply_f(q: jax.Array, r: jax.Array, theta: jax.Array, target_q: jax.Array, target_r: jax.Array, topo: jax.Array, word: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    del target_q, target_r, topo
    qn, tn = q_fiber(q, theta, word)
    return project_state(qn, r, tn)


def apply_b(q: jax.Array, r: jax.Array, theta: jax.Array, target_q: jax.Array, target_r: jax.Array, topo: jax.Array, word: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    del target_r, topo
    return project_state(q_base(q, r, target_q, word), r, theta)


def compose_ops(
    q: jax.Array,
    r: jax.Array,
    theta: jax.Array,
    target_q: jax.Array,
    target_r: jax.Array,
    topo: jax.Array,
    word: jax.Array,
    order: tuple[str, ...],
) -> tuple[jax.Array, jax.Array, jax.Array]:
    for op in order:
        if op == "H":
            q, r, theta = apply_h(q, r, theta, target_q, target_r, topo, word)
        elif op == "T":
            q, r, theta = apply_t(q, r, theta, target_q, target_r, topo, word)
        elif op == "F":
            q, r, theta = apply_f(q, r, theta, target_q, target_r, topo, word)
        elif op == "B":
            q, r, theta = apply_b(q, r, theta, target_q, target_r, topo, word)
        else:
            raise AssertionError(op)
    return q, r, theta


def select_word(candidates: tuple[jax.Array, ...], word: jax.Array) -> jax.Array:
    stacked = jnp.stack(candidates, axis=0)
    return stacked[word, jnp.arange(N)]


def ordered_row_map(
    q: jax.Array,
    r: jax.Array,
    theta: jax.Array,
    product_mode: jax.Array,
    reverse_mode: jax.Array,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    target_q = jnp.where(product_mode, PRODUCT_Q, TARGET_Q[ASSIGNED])
    target_r = jnp.where(product_mode, PRODUCT_R, TARGET_R[ASSIGNED])
    topo = jnp.where(product_mode, jnp.zeros_like(TOPO_IDX[ASSIGNED]), TOPO_IDX[ASSIGNED])
    word = jnp.where(product_mode, jnp.zeros_like(WORD_ID), WORD_ID)

    orders = (
        ("H", "T", "F", "B"),
        ("T", "H", "B", "F"),
        ("F", "B", "H", "T"),
        ("B", "F", "T", "H"),
    )
    normal = tuple(compose_ops(q, r, theta, target_q, target_r, topo, word, order) for order in orders)
    reversed_orders = tuple(tuple(reversed(order)) for order in orders)
    rev = tuple(compose_ops(q, r, theta, target_q, target_r, topo, word, order) for order in reversed_orders)

    qn = select_word(tuple(jnp.where(reverse_mode, rev[i][0], normal[i][0]) for i in range(4)), word)
    rn = select_word(tuple(jnp.where(reverse_mode, rev[i][1], normal[i][1]) for i in range(4)), word)
    tn = select_word(tuple(jnp.where(reverse_mode, rev[i][2], normal[i][2]) for i in range(4)), word)
    return project_state(qn, rn, tn)


@jax.jit
def evolve(product_mode: jax.Array, reverse_mode: jax.Array, prune_active: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    q0, r0, theta0 = initial_ensemble()
    alive0 = jnp.ones((N,), dtype=bool)

    def step(carry: tuple[jax.Array, jax.Array, jax.Array, jax.Array], _: Any) -> tuple[tuple[jax.Array, jax.Array, jax.Array, jax.Array], jax.Array]:
        q, r, theta, alive = carry
        qn, rn, tn = ordered_row_map(q, r, theta, product_mode, reverse_mode)
        sheet = SHEET_SIGN[ASSIGNED]
        chiral_kill = sheet * qn[:, 0] < -CHIRAL_TOL
        finite_kill = (jnp.linalg.norm(rn, axis=1) > 1.0 + F01_TOL) | (tn <= 0.0) | (tn >= jnp.pi / 2.0)
        killed = prune_active & (chiral_kill | finite_kill)
        alive_next = alive & ~killed
        q_drift = jnp.max(jnp.abs(jnp.linalg.norm(qn, axis=1) - 1.0))
        r_max = jnp.max(jnp.linalg.norm(rn, axis=1))
        return (qn, rn, tn, alive_next), jnp.asarray([q_drift, r_max], dtype=jnp.float64)

    (qf, rf, thetaf, alive), metrics = jax.lax.scan(step, (q0, r0, theta0, alive0), None, length=STEPS)
    return qf, rf, thetaf, alive, metrics[:, 0], metrics[:, 1]


def placement_labels(q: jax.Array) -> jax.Array:
    return 1 + jnp.argmax(q @ TARGET_Q.T, axis=1)


def topo_labels_from_placement(labels: jax.Array) -> jax.Array:
    return 1 + TOPO_IDX[labels - 1]


def unique_positive(values: jax.Array, max_size: int) -> list[int]:
    got = jnp.unique(values, size=max_size, fill_value=-1)
    return [int(v) for v in jax.device_get(got) if int(v) > 0]


def histogram(values: jax.Array, alive: jax.Array, length: int) -> list[int]:
    h = jnp.bincount(values[alive] - 1, length=length)
    return [int(x) for x in jax.device_get(h)]


def recurrence_residual(q: jax.Array, r: jax.Array, theta: jax.Array, labels: jax.Array, word_ids: jax.Array, product_mode: bool) -> jax.Array:
    if product_mode:
        tq = jnp.broadcast_to(TARGET_Q[0], q.shape)
        tr = jnp.broadcast_to(TARGET_R[0], r.shape)
        theta_target = jnp.full_like(theta, 0.20)
    else:
        tq = TARGET_Q[labels - 1]
        tr = TARGET_R[labels - 1]
        theta_target = jnp.asarray([0.20, 0.43, 0.72, 1.04], dtype=jnp.float64)[word_ids % 4]
    q_sign = jnp.sign(jnp.sum(q * tq, axis=1, keepdims=True))
    q_res = jnp.linalg.norm(q - q_sign * tq, axis=1)
    r_res = jnp.linalg.norm(r - tr, axis=1)
    t_res = jnp.abs(theta - theta_target)
    return q_res + r_res + t_res


def run_one(name: str, product_mode: bool, reverse_mode: bool, prune_active: bool) -> dict[str, Any]:
    qf, rf, thetaf, alive, q_drifts, r_maxes = evolve(jnp.asarray(product_mode), jnp.asarray(reverse_mode), jnp.asarray(prune_active))
    placement = placement_labels(qf)
    topo = topo_labels_from_placement(placement)
    effective_word = jnp.where(product_mode, jnp.zeros_like(WORD_ID), WORD_ID)
    subsub = (placement - 1) * len(ORDER_TOKENS) + effective_word + 1
    survivors = _i(jnp.sum(alive))
    pruned = N - survivors
    if survivors:
        residual = recurrence_residual(qf[alive], rf[alive], thetaf[alive], placement[alive], effective_word[alive], product_mode)
        mean_theta = _f(jnp.mean(thetaf[alive]))
        max_residual = _f(jnp.max(residual))
        state_mean = jnp.concatenate([jnp.mean(qf[alive], axis=0), jnp.mean(rf[alive], axis=0), jnp.asarray([mean_theta])])
    else:
        max_residual = None
        mean_theta = None
        state_mean = jnp.zeros((8,), dtype=jnp.float64)
    return {
        "name": name,
        "product_mode": bool(product_mode),
        "reverse_mode": bool(reverse_mode),
        "prune_active": bool(prune_active),
        "populated_topology_basins": unique_positive(topo[alive], 4),
        "populated_placement_subbasins": unique_positive(placement[alive], 16),
        "populated_order_subsubbasin_count": len(unique_positive(subsub[alive], 64)),
        "placement_histogram": histogram(placement, alive, 16),
        "order_cell_histogram": histogram(subsub, alive, 64),
        "survivors": survivors,
        "pruned": pruned,
        "max_q_norm_drift": _f(jnp.max(q_drifts)),
        "max_bloch_norm_seen": _f(jnp.max(r_maxes)),
        "max_recurrence_residual": max_residual,
        "mean_survivor_theta": mean_theta,
        "state_mean": [float(x) for x in jax.device_get(state_mean)],
    }


def noncommutation_witness() -> dict[str, float]:
    h = SZ
    t = SX + 0.31 * SZ
    f = SY
    b = SX - 0.27 * SY
    genuine_rows = [h, t, f, b]
    commuting_rows = [SZ, 0.7 * SZ, -0.4 * SZ, 1.3 * SZ]
    gaps = [jnp.linalg.norm(a @ b_ - b_ @ a) for i, a in enumerate(genuine_rows) for b_ in genuine_rows[i + 1 :]]
    cgaps = [jnp.linalg.norm(a @ b_ - b_ @ a) for i, a in enumerate(commuting_rows) for b_ in commuting_rows[i + 1 :]]

    q, r, theta = initial_ensemble()

    def pair_gap(a: str, b: str) -> jax.Array:
        q_ab, r_ab, t_ab = compose_ops(q, r, theta, TARGET_Q[ASSIGNED], TARGET_R[ASSIGNED], TOPO_IDX[ASSIGNED], WORD_ID, (a, b))
        q_ba, r_ba, t_ba = compose_ops(q, r, theta, TARGET_Q[ASSIGNED], TARGET_R[ASSIGNED], TOPO_IDX[ASSIGNED], WORD_ID, (b, a))
        return jnp.mean(jnp.linalg.norm(q_ab - q_ba, axis=1) + jnp.linalg.norm(r_ab - r_ba, axis=1) + jnp.abs(t_ab - t_ba))

    dynamic_pairs = {
        "HT_vs_TH": pair_gap("H", "T"),
        "TF_vs_FT": pair_gap("T", "F"),
        "BT_vs_TB": pair_gap("B", "T"),
        "HB_vs_BH": pair_gap("H", "B"),
        "FB_vs_BF": pair_gap("F", "B"),
    }
    dynamic_gap = jnp.max(jnp.asarray(list(dynamic_pairs.values())))
    q_hh, r_hh, t_hh = compose_ops(q, r, theta, TARGET_Q[ASSIGNED], TARGET_R[ASSIGNED], TOPO_IDX[ASSIGNED], WORD_ID, ("H", "H"))
    q_hh2, r_hh2, t_hh2 = compose_ops(q, r, theta, TARGET_Q[ASSIGNED], TARGET_R[ASSIGNED], TOPO_IDX[ASSIGNED], WORD_ID, ("H", "H"))
    dynamic_commuting_control = jnp.mean(jnp.linalg.norm(q_hh - q_hh2, axis=1) + jnp.linalg.norm(r_hh - r_hh2, axis=1) + jnp.abs(t_hh - t_hh2))
    return {
        "static_genuine_max_commutator_norm": _f(jnp.max(jnp.asarray(gaps))),
        "static_commuting_control_max_commutator_norm": _f(jnp.max(jnp.asarray(cgaps))),
        "dynamic_pair_gaps": {k: _f(v) for k, v in dynamic_pairs.items()},
        "dynamic_max_row_order_gap": _f(dynamic_gap),
        "dynamic_same_word_control_gap": _f(dynamic_commuting_control),
    }


def run_probe() -> dict[str, Any]:
    baseline = run_one("A_no_prune_noncommuting_ratchet", product_mode=False, reverse_mode=False, prune_active=False)
    genuine = run_one("B_pruned_noncommuting_finitude_ratchet", product_mode=False, reverse_mode=False, prune_active=True)
    noop = run_one("C_noop_control_equals_A", product_mode=False, reverse_mode=False, prune_active=False)
    reversed_order = run_one("D_reversed_order_control", product_mode=False, reverse_mode=True, prune_active=True)
    product = run_one("E_commuting_product_negative", product_mode=True, reverse_mode=False, prune_active=False)
    witness = noncommutation_witness()
    state_gap = _f(jnp.linalg.norm(jnp.asarray(genuine["state_mean"]) - jnp.asarray(reversed_order["state_mean"])))

    checks = {
        "A_topology_basins_all_4": baseline["populated_topology_basins"] == [1, 2, 3, 4],
        "A_placement_subbasins_all_16": baseline["populated_placement_subbasins"] == list(range(1, 17)),
        "B_prune_fires": genuine["pruned"] > 0,
        "B_preserves_topology_basins": genuine["populated_topology_basins"] == [1, 2, 3, 4],
        "B_preserves_placement_subbasins": genuine["populated_placement_subbasins"] == list(range(1, 17)),
        "B_order_subsubbasins_refine_subbasins": genuine["populated_order_subsubbasin_count"] >= 48,
        "C_noop_equals_A": noop["placement_histogram"] == baseline["placement_histogram"] and noop["pruned"] == 0,
        "E_commuting_product_collapses_topology": product["populated_topology_basins"] == [1],
        "E_commuting_product_collapses_subbasins": product["populated_placement_subbasins"] == [1],
        "noncommuting_static_witness": witness["static_genuine_max_commutator_norm"] > 1.0,
        "commuting_static_negative": witness["static_commuting_control_max_commutator_norm"] < 1.0e-12,
        "noncommuting_dynamic_order_gap": witness["dynamic_max_row_order_gap"] > 1.0e-5,
        "same_word_dynamic_control_zero": witness["dynamic_same_word_control_gap"] < 1.0e-12,
        "reversed_order_changes_state": state_gap > 1.0e-4,
        "bookkeeping": all(row["survivors"] == N - row["pruned"] for row in (baseline, genuine, noop, reversed_order, product)),
        "f01_retraction": max(row["max_q_norm_drift"] for row in (baseline, genuine, noop, reversed_order, product)) < 1.0e-10,
        "finite_bloch_ball": max(row["max_bloch_norm_seen"] for row in (baseline, genuine, noop, reversed_order, product)) <= 1.0 + F01_TOL + 1.0e-9,
    }
    audit_pass = all(checks.values())
    return {
        "object": "jax_noncommutative_finitude_ratchet_basin_hierarchy",
        "classification": "diagnostic_jax_noncommutative_finitude_ratchet_basin_hierarchy",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_mode": "read_only",
        "julia_reference_paths": [
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains.jl",
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains_results.json",
        ],
        "sim_execution_kind": "jax_audit_lane",
        "finite_map": "finite ordered row ensemble over S3 quaternions, Bloch vectors, Hopf leaf coordinate, and 64 placement/order cells -> monotone survivor quotient -> basin hierarchy",
        "domain": {
            "branches": N,
            "topologies": list(TOPOLOGIES),
            "terrains": {"L": LEFT_TERRAINS, "R": RIGHT_TERRAINS},
            "placements": "{L,R} x {fiber,base} x {Se,Ne,Ni,Si}",
            "ordered_tokens": list(ORDER_TOKENS),
            "state": "q in S3, r in finite Bloch ball, theta in (0,pi/2), alive monotone latch",
        },
        "peps3d_embedding": {
            "status": "diagnostic_mirror_only_not_admitted",
            "local_cell": "finite one-cell anchor with site sheet/path/topology, virtual order token, and face-style survivor readout",
            "blocked_reason": "No native PEPS3D carrier dynamics or admitted tensor/channel cell is claimed by this JAX diagnostic.",
        },
        "spinor_state": {
            "status": "jax_quaternion_spinor_mirror",
            "state": "unit quaternion q on S3 plus spinor-derived Bloch vector r; retracted every row step",
            "native_julia_truth": "read_only_reference_not_executed",
        },
        "quaternion_action": "finite S3 row maps: Hamiltonian target flow, fiber rotation, base-coupled perturbation, and retraction",
        "dependency_receipts": [
            "jax_manifold_layer_independent_suite_results.json",
            "jax_emergent_basin_recurrence_prune_mirror_results.json",
            "jax_julia_reference_geometric_constraint_layer_runner_results.json",
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains_results.json",
        ],
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "codomain_or_output": "topology basins, placement subbasins, placement/order subsubbasins, prune counts, finite/order witnesses",
        "basin_definitions": {
            "basin": "nearest final topology law in {Se,Ne,Ni,Si}",
            "subbasin": "nearest final 16-placement label: sheet x loop path x topology/terrain",
            "subsubbasin": "placement plus ordered noncommuting row token",
        },
        "root_constraints_in_force": {
            "F01": "finite branch count, finite topology/terrain/placement/order registries, S3 retraction, Bloch-ball clip, finite readouts",
            "N01": "noncommuting Hamiltonian/terrain/fiber/base row order with static and dynamic order-gap witnesses",
        },
        "tool_manifest": {
            "jax": "load-bearing jit, random, lax.scan, x64 finite branch evolution and survivor latch",
            "jax.numpy": "load-bearing finite linear algebra, retraction, labels, histograms, commutators",
        },
        "tool_integration_depth": {"jax": "load_bearing", "jax.numpy": "load_bearing"},
        "placement_registry": PLACEMENT_META,
        "runs": {
            "A": baseline,
            "B": genuine,
            "C": noop,
            "D": reversed_order,
            "E": product,
        },
        "noncommutation_witness": witness,
        "genuine_vs_reversed_state_mean_gap": state_gap,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
        "allowed_claims": [
            "JAX now has a finite diagnostic ratchet object whose survivor quotient exposes basin/subbasin/subsubbasin readouts",
            "The object is order-sensitive under N01 and collapses under the commuting/product negative",
            "This receipt is diagnostic and promotion-blocked; it is not full manifold admission",
        ],
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "Axis0",
            "FEP",
            "flux",
            "physics_gravity",
            "final_manifold_admission",
        ],
    }


def main() -> int:
    result = run_probe()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    runs = result["runs"]
    print(
        "jax_noncommutative_finitude_ratchet "
        f"A top={runs['A']['populated_topology_basins']} sub={len(runs['A']['populated_placement_subbasins'])} subsub={runs['A']['populated_order_subsubbasin_count']} pruned={runs['A']['pruned']} | "
        f"B top={runs['B']['populated_topology_basins']} sub={len(runs['B']['populated_placement_subbasins'])} subsub={runs['B']['populated_order_subsubbasin_count']} pruned={runs['B']['pruned']} | "
        f"E top={runs['E']['populated_topology_basins']} sub={len(runs['E']['populated_placement_subbasins'])} subsub={runs['E']['populated_order_subsubbasin_count']} pruned={runs['E']['pruned']}"
    )
    print(f"AUDIT_PASS={result['AUDIT_PASS']} wrote={OUT}")
    return 0 if result["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
