#!/usr/bin/env python3
"""JAX parity lane for npc_connection_geometry_julia.jl.

This replicates the same finite map as the Julia carrier:
locked Hopf/Weyl spinors -> quaternionic Hopfield/PEPS2D bonds -> unit links ->
plaquette holonomy, weighted graph Laplacian, heat trace, and terrain-axis
readouts.

Claim ceiling: scratch_diagnostic only. This file does not assert layer
completion, PEPS3D admission, manifold admission, flux, Axis0, FEP, bridge, or
physics.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


JULIA_REF = Path(
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/"
    "npc_connection_geometry_julia_results.json"
)
OUT = Path("/tmp/npc_connection_geometry_jax_results.json")
EPS = 1.0e-14
SIZES = (8, 16, 32)
SEEDS = (20260602, 20260603)
M_PATTERNS = 3


def q_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    aw, ax, ay, az = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bw, bx, by, bz = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return jnp.stack(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        axis=-1,
    )


def q_conj(q: jax.Array) -> jax.Array:
    return q * jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def q_normalize(q: jax.Array) -> jax.Array:
    n = jnp.linalg.norm(q, axis=-1, keepdims=True)
    unit = q / jnp.maximum(n, EPS)
    ident = jnp.zeros_like(q).at[..., 0].set(1.0)
    return jnp.where(n < EPS, ident, unit)


def qdiff_norm(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.linalg.norm(a - b, axis=-1)


def dot_q(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.sum(a * b, axis=-1)


def hopf_axis(q: jax.Array) -> jax.Array:
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack(
        [
            2.0 * (w * y + x * z),
            2.0 * (w * z - x * y),
            w * w + x * x - y * y - z * z,
        ],
        axis=-1,
    )


def normalize_vec3(v: jax.Array) -> jax.Array:
    n = jnp.linalg.norm(v, axis=-1, keepdims=True)
    fallback = jnp.zeros_like(v).at[..., 2].set(1.0)
    return jnp.where(n < EPS, fallback, v / jnp.maximum(n, EPS))


def torus_dims(n_sites: int) -> tuple[int, int]:
    best = (2, n_sites // 2)
    for lx in range(2, math.isqrt(n_sites) + 1):
        if n_sites % lx == 0:
            best = (lx, n_sites // lx)
    return best


def weyl_spinor_quat(phi: float, chi: float, eta: float, chirality: str) -> jax.Array:
    c = math.cos(eta)
    s = math.sin(eta)
    pp = phi + chi
    pm = phi - chi
    if chirality == "L":
        q = jnp.asarray(
            [c * math.cos(pp), c * math.sin(pp), s * math.cos(pm), s * math.sin(pm)],
            dtype=jnp.float64,
        )
    else:
        q = jnp.asarray(
            [c * math.cos(pp), -c * math.sin(pp), s * math.cos(pm), -s * math.sin(pm)],
            dtype=jnp.float64,
        )
    return q_normalize(q)


def make_hopf_patterns(n_sites: int, m_patterns: int, seed: int) -> jax.Array:
    lx, ly = torus_dims(n_sites)
    seed_phi = math.fmod(seed * 0.37, 2.0 * math.pi)
    seed_eta = math.fmod(seed * 0.17, 0.4)
    rows = []
    for mu0 in range(m_patterns):
        mu = mu0 + 1
        phi0 = 2.0 * math.pi * (mu - 1) / m_patterns + seed_phi * (mu + 1) / m_patterns
        sites = []
        for i0 in range(n_sites):
            x = i0 // ly + 1
            y = i0 % ly + 1
            phi = phi0 + 2.0 * math.pi * x / lx
            chi = 2.0 * math.pi * y / ly
            eta = math.pi / 4.0 + (0.2 + seed_eta * 0.1) * math.sin(phi + chi)
            chirality = "L" if mu % 2 == 0 else "R"
            sites.append(weyl_spinor_quat(phi, chi, eta, chirality))
        rows.append(jnp.stack(sites))
    return jnp.stack(rows)


def weyl_site_fields(n_sites: int, seed: int) -> tuple[jax.Array, jax.Array, jax.Array]:
    lx, ly = torus_dims(n_sites)
    seed_phi = math.fmod(seed * 0.37, 2.0 * math.pi)
    seed_eta = math.fmod(seed * 0.17, 0.4)
    left = []
    right = []
    etas = []
    for i0 in range(n_sites):
        x = i0 // ly + 1
        y = i0 % ly + 1
        phi = seed_phi + 2.0 * math.pi * x / lx
        chi = 2.0 * math.pi * y / ly
        eta = math.pi / 4.0 + (0.2 + seed_eta * 0.1) * math.sin(phi + chi)
        left.append(weyl_spinor_quat(phi, chi, eta, "L"))
        right.append(weyl_spinor_quat(phi, chi, eta, "R"))
        etas.append(eta)
    return jnp.stack(left), jnp.stack(right), jnp.asarray(etas, dtype=jnp.float64)


def hopfield_weights(patterns: jax.Array) -> jax.Array:
    m_patterns, n_sites, _ = patterns.shape
    weights = jnp.zeros((n_sites, n_sites, 4), dtype=jnp.float64)
    for mu in range(m_patterns):
        for i in range(n_sites):
            for j in range(n_sites):
                if i != j:
                    weights = weights.at[i, j].add(q_mul(patterns[mu, i], q_conj(patterns[mu, j])))
    return weights


def flat_weights(n_sites: int) -> jax.Array:
    weights = jnp.zeros((n_sites, n_sites, 4), dtype=jnp.float64).at[:, :, 0].set(1.0)
    return weights * (1.0 - jnp.eye(n_sites, dtype=jnp.float64))[:, :, None]


def torus_plaquettes(n_sites: int) -> list[tuple[int, int, int, int]]:
    lx, ly = torus_dims(n_sites)

    def idx(x: int, y: int) -> int:
        return (x % lx) * ly + (y % ly)

    return [
        (idx(x, y), idx(x + 1, y), idx(x + 1, y + 1), idx(x, y + 1))
        for x in range(lx)
        for y in range(ly)
    ]


def torus_edges(n_sites: int) -> list[tuple[int, int]]:
    lx, ly = torus_dims(n_sites)

    def idx(x: int, y: int) -> int:
        return (x % lx) * ly + (y % ly)

    edges: set[tuple[int, int]] = set()
    for x in range(lx):
        for y in range(ly):
            i = idx(x, y)
            for j in (idx(x + 1, y), idx(x, y + 1)):
                a, b = (i, j) if i < j else (j, i)
                edges.add((a, b))
    return sorted(edges)


def plaquette_holonomy_angles(weights: jax.Array, n_sites: int) -> jax.Array:
    angles = []
    for a, b, c, d in torus_plaquettes(n_sites):
        hol = q_mul(
            q_mul(q_mul(q_normalize(weights[a, b]), q_normalize(weights[b, c])), q_normalize(weights[c, d])),
            q_normalize(weights[d, a]),
        )
        hol = q_normalize(hol)
        angles.append(jnp.arccos(jnp.clip(jnp.abs(hol[0]), 0.0, 1.0)))
    return jnp.asarray(angles, dtype=jnp.float64)


def plaquette_noncommutator_gap(weights: jax.Array, n_sites: int) -> dict[str, float]:
    unit = q_normalize(weights)
    gaps = []
    for a, b, c, d in torus_plaquettes(n_sites):
        factors = (unit[a, b], unit[b, c], unit[c, d], unit[d, a])
        for i in range(4):
            for j in range(i + 1, 4):
                gaps.append(qdiff_norm(q_mul(factors[i], factors[j]), q_mul(factors[j], factors[i])))
    arr = jnp.asarray(gaps, dtype=jnp.float64)
    return {"mean_gap": float(jnp.mean(arr)), "max_gap": float(jnp.max(arr))}


def compose_links(a_weights: jax.Array, b_weights: jax.Array, order: str) -> jax.Array:
    a = q_normalize(a_weights)
    b = q_normalize(b_weights)
    composed = q_mul(a, b) if order == "AB" else q_mul(b, a)
    n_sites = a_weights.shape[0]
    return composed * (1.0 - jnp.eye(n_sites, dtype=jnp.float64))[:, :, None]


def link_order_gap(a_weights: jax.Array, b_weights: jax.Array, n_sites: int) -> dict[str, float]:
    gaps = []
    for i, j in torus_edges(n_sites):
        a = q_normalize(a_weights[i, j])
        b = q_normalize(b_weights[i, j])
        gaps.append(qdiff_norm(q_mul(a, b), q_mul(b, a)))
    arr = jnp.asarray(gaps, dtype=jnp.float64)
    return {"mean_gap": float(jnp.mean(arr)), "max_gap": float(jnp.max(arr))}


def weighted_laplacian(weights: jax.Array, n_sites: int) -> jax.Array:
    weighted_adj = jnp.zeros((n_sites, n_sites), dtype=jnp.float64)
    beta = 1.25
    for i, j in torus_edges(n_sites):
        u = q_normalize(weights[i, j])
        su2_mag = jnp.sqrt(u[1] * u[1] + u[2] * u[2] + u[3] * u[3])
        conductance = jnp.exp(beta * su2_mag)
        weighted_adj = weighted_adj.at[i, j].set(conductance)
        weighted_adj = weighted_adj.at[j, i].set(conductance)
    return jnp.diag(jnp.sum(weighted_adj, axis=1)) - weighted_adj


def terrain_signature(weights: jax.Array, n_sites: int, seed: int) -> dict[str, Any]:
    psi_l, psi_r, etas = weyl_site_fields(n_sites, seed)
    h_l = []
    h_r = []
    axes_l = []
    axes_r = []
    for a in range(n_sites):
        s_l = jnp.zeros((4,), dtype=jnp.float64)
        s_r = jnp.zeros((4,), dtype=jnp.float64)
        for b in range(n_sites):
            s_l = s_l + q_mul(weights[a, b], psi_l[b])
            s_r = s_r + q_mul(weights[a, b], psi_r[b])
        hl = q_normalize(s_l)
        hr = q_normalize(s_r)
        h_l.append(hl)
        h_r.append(hr)
        sheet_l = jnp.asarray([0.0, 0.0, math.cos(2.0 * float(etas[a]))], dtype=jnp.float64)
        sheet_r = jnp.asarray([0.0, 0.0, -math.cos(2.0 * float(etas[a]))], dtype=jnp.float64)
        axes_l.append(normalize_vec3(hopf_axis(psi_l[a]) + 0.7 * hopf_axis(hl) + 0.3 * sheet_l))
        axes_r.append(normalize_vec3(hopf_axis(psi_r[a]) + 0.7 * hopf_axis(hr) + 0.3 * sheet_r))
    h_l_arr = jnp.stack(h_l)
    h_r_arr = jnp.stack(h_r)
    axes_l_arr = jnp.stack(axes_l)
    axes_r_arr = jnp.stack(axes_r)
    alignment = jnp.concatenate([dot_q(h_l_arr, psi_l), dot_q(h_r_arr, psi_r)])
    axis_gap = jnp.linalg.norm(axes_l_arr - axes_r_arr, axis=-1)
    return {
        "mean_alignment": float(jnp.mean(alignment)),
        "std_alignment": float(jnp.std(alignment, ddof=1)),
        "mean_axis": [float(x) for x in jnp.mean(jnp.concatenate([axes_l_arr, axes_r_arr]), axis=0)],
        "lr_axis_gap_mean": float(jnp.mean(axis_gap)),
        "lr_axis_gap_max": float(jnp.max(axis_gap)),
    }


def readout(n_sites: int, seed: int, m_patterns: int = M_PATTERNS) -> dict[str, Any]:
    patterns = make_hopf_patterns(n_sites, m_patterns, seed)
    weights = hopfield_weights(patterns)
    angles = plaquette_holonomy_angles(weights, n_sites)
    n01 = plaquette_noncommutator_gap(weights, n_sites)
    lap = weighted_laplacian(weights, n_sites)
    evals = jnp.sort(jnp.linalg.eigvalsh(lap))
    heat = jnp.sum(jnp.exp(-evals))
    terrain = terrain_signature(weights, n_sites, seed)

    flat = flat_weights(n_sites)
    flat_angles = plaquette_holonomy_angles(flat, n_sites)
    flat_lap = weighted_laplacian(flat, n_sites)
    flat_evals = jnp.sort(jnp.linalg.eigvalsh(flat_lap))

    patterns2 = make_hopf_patterns(n_sites, m_patterns, seed + 7919)
    weights2 = hopfield_weights(patterns2)
    angles2 = plaquette_holonomy_angles(weights2, n_sites)
    structured_order = link_order_gap(weights, weights2, n_sites)

    erased_ab = compose_links(weights, weights, "AB")
    erased_ba = compose_links(weights, weights, "BA")
    erased_angle_diff = jnp.max(
        jnp.abs(plaquette_holonomy_angles(erased_ab, n_sites) - plaquette_holonomy_angles(erased_ba, n_sites))
    )
    erased_order = link_order_gap(weights, weights, n_sites)

    return {
        "plaquette_holonomy_mean_rad": float(jnp.mean(angles)),
        "plaquette_holonomy_std_rad": float(jnp.std(angles, ddof=1)),
        "plaquette_noncommutator_mean_gap": n01["mean_gap"],
        "plaquette_noncommutator_max_gap": n01["max_gap"],
        "laplacian_spectral_gap": float(evals[1] - evals[0]),
        "laplacian_gap": float(evals[1] - evals[0]),
        "heat_trace_t1": float(heat),
        "terrain_mean_alignment": terrain["mean_alignment"],
        "terrain_std_alignment": terrain["std_alignment"],
        "terrain_axis_mean": terrain["mean_axis"],
        "weyl_lr_axis_gap_mean": terrain["lr_axis_gap_mean"],
        "weyl_lr_axis_gap_max": terrain["lr_axis_gap_max"],
        "flat_holonomy_mean_rad": float(jnp.mean(flat_angles)),
        "flat_laplacian_gap": float(flat_evals[1] - flat_evals[0]),
        "flat_heat_trace": float(jnp.sum(jnp.exp(-flat_evals))),
        "erased_angle_diff_max": float(erased_angle_diff),
        "erased_ab_ba_commutator_gap": erased_order["max_gap"],
        "structured_ab_ba_commutator_gap": structured_order["mean_gap"],
        "input_dep_holonomy_delta": float(jnp.abs(jnp.mean(angles) - jnp.mean(angles2))),
    }


def mean_float(rows: list[dict[str, Any]], key: str) -> float:
    return float(sum(float(row[key]) for row in rows) / len(rows))


def mean_vec3(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [float(sum(float(row[key][i]) for row in rows) / len(rows)) for i in range(3)]


def parity_diff(julia_size: dict[str, Any], jax_size: dict[str, Any]) -> float:
    keys = [
        "plaquette_holonomy_mean_rad",
        "laplacian_gap",
        "laplacian_spectral_gap",
        "heat_trace_t1",
        "flat_holonomy_mean_rad",
        "flat_laplacian_gap",
        "flat_heat_trace",
        "erased_angle_diff_max",
        "erased_ab_ba_commutator_gap",
        "structured_ab_ba_commutator_gap",
        "input_dep_holonomy_delta",
        "terrain_mean_alignment",
        "weyl_lr_axis_gap_mean",
        "weyl_lr_axis_gap_max",
    ]
    diffs = [abs(float(julia_size[key]) - float(jax_size[key])) for key in keys if key in julia_size]
    if "terrain_axis_mean" in julia_size:
        diffs.extend(
            abs(float(julia_size["terrain_axis_mean"][i]) - float(jax_size["terrain_axis_mean"][i]))
            for i in range(3)
        )
    return max(diffs) if diffs else math.inf


def main() -> None:
    julia_ref = json.loads(JULIA_REF.read_text(encoding="utf-8")) if JULIA_REF.exists() else None
    size_results: dict[str, Any] = {}
    checks: list[str] = []
    all_pass = julia_ref is not None

    for n_sites in SIZES:
        rows = [readout(n_sites, seed) for seed in SEEDS]
        size = {
            "plaquette_holonomy_mean_rad": mean_float(rows, "plaquette_holonomy_mean_rad"),
            "plaquette_holonomy_std_rad": mean_float(rows, "plaquette_holonomy_std_rad"),
            "plaquette_noncommutator_mean_gap": mean_float(rows, "plaquette_noncommutator_mean_gap"),
            "plaquette_noncommutator_max_gap": max(float(row["plaquette_noncommutator_max_gap"]) for row in rows),
            "laplacian_spectral_gap": mean_float(rows, "laplacian_spectral_gap"),
            "laplacian_gap": mean_float(rows, "laplacian_gap"),
            "heat_trace_t1": mean_float(rows, "heat_trace_t1"),
            "flat_holonomy_mean_rad": mean_float(rows, "flat_holonomy_mean_rad"),
            "flat_laplacian_gap": mean_float(rows, "flat_laplacian_gap"),
            "flat_heat_trace": mean_float(rows, "flat_heat_trace"),
            "erased_angle_diff_max": max(float(row["erased_angle_diff_max"]) for row in rows),
            "erased_ab_ba_commutator_gap": max(float(row["erased_ab_ba_commutator_gap"]) for row in rows),
            "structured_ab_ba_commutator_gap": mean_float(rows, "structured_ab_ba_commutator_gap"),
            "input_dep_holonomy_delta": mean_float(rows, "input_dep_holonomy_delta"),
            "terrain_mean_alignment": mean_float(rows, "terrain_mean_alignment"),
            "terrain_axis_mean": mean_vec3(rows, "terrain_axis_mean"),
            "weyl_lr_axis_gap_mean": mean_float(rows, "weyl_lr_axis_gap_mean"),
            "weyl_lr_axis_gap_max": max(float(row["weyl_lr_axis_gap_max"]) for row in rows),
        }
        pos_pass = size["plaquette_holonomy_mean_rad"] > 0.1
        neg_pass = size["flat_holonomy_mean_rad"] < 0.05
        bnd_pass = size["erased_angle_diff_max"] < 1.0e-8 and size["erased_ab_ba_commutator_gap"] < 1.0e-10
        inp_pass = size["input_dep_holonomy_delta"] > 1.0e-4
        n01_pass = (
            size["plaquette_noncommutator_mean_gap"] > 1.0e-3
            and size["structured_ab_ba_commutator_gap"] > 1.0e-3
        )
        parity_max = None
        parity_pass = False
        if julia_ref is not None:
            parity_max = parity_diff(julia_ref["sizes"][str(n_sites)], size)
            parity_pass = parity_max < 1.0e-4
            julia_ref["sizes"][str(n_sites)]["parity_max_diff_vs_jax"] = parity_max
        size["parity_max_diff_vs_julia"] = parity_max
        size["tests"] = {
            "positive_structured_holonomy": pos_pass,
            "negative_flat_holonomy": neg_pass,
            "boundary_erased_symmetric": bnd_pass,
            "input_dependent": inp_pass,
            "noncommuting_quaternion_witness": n01_pass,
            "parity_vs_julia": parity_pass,
        }
        checks.append(
            "N={n} pos(hol>0.1)={pos} neg(flat<0.05)={neg} "
            "bnd(erased_AB_BA<1e-8)={bnd} inp_dep(>1e-4)={inp} "
            "n01(noncomm>1e-3)={n01} parity(<1e-4)={parity} diff={diff}".format(
                n=n_sites,
                pos=pos_pass,
                neg=neg_pass,
                bnd=bnd_pass,
                inp=inp_pass,
                n01=n01_pass,
                parity=parity_pass,
                diff="missing" if parity_max is None else f"{parity_max:.3e}",
            )
        )
        all_pass = all_pass and pos_pass and neg_pass and bnd_pass and inp_pass and n01_pass and parity_pass
        size_results[str(n_sites)] = size

    result = {
        "object_id": "npc_connection_geometry_jax_parity",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": (
            "JAX parity check for Julia npc_connection_geometry_julia. "
            "Does NOT assert layer completion, PEPS3D admission, manifold admission, "
            "flux, Axis0, FEP, bridge, or physics."
        ),
        "F01_witness": "finite N in {8,16,32}, M=3 Hopf-pattern fields",
        "N01_witness": "noncommuting quaternion plaquette holonomy products",
        "julia_ref_path": str(JULIA_REF),
        "sizes": size_results,
        "controls": {
            "flat_trivial_holonomy": "uniform W -> mean holonomy angle < 0.05 rad",
            "erased_symmetric": "B=A -> AB and BA geometry readout is symmetric",
            "input_dependent": all(size_results[str(n)]["input_dep_holonomy_delta"] > 1.0e-4 for n in SIZES),
        },
        "bonds_are_geometry": all(
            size_results[str(n)]["plaquette_holonomy_mean_rad"] > 0.1
            and size_results[str(n)]["flat_holonomy_mean_rad"] < 0.05
            for n in SIZES
        ),
        "checks": checks,
        "all_pass": all_pass,
    }

    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if julia_ref is not None:
        julia_ref["jax_parity"] = {
            "path": str(OUT),
            "all_pass": all_pass,
            "max_diff": max(
                float(size_results[str(n)]["parity_max_diff_vs_julia"])
                for n in SIZES
                if size_results[str(n)]["parity_max_diff_vs_julia"] is not None
            ),
        }
        julia_ref["all_pass"] = bool(julia_ref.get("all_pass", False) and all_pass)
        JULIA_REF.write_text(json.dumps(julia_ref, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({k: v for k, v in result.items() if k != "sizes"}, indent=2, sort_keys=True))
    print("Written:", OUT)


if __name__ == "__main__":
    main()
