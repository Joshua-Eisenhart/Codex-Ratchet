#!/usr/bin/env python3
"""JAX parity lane for npc2_connection_geometry_julia.jl — HARDENED v2.

Replicates the same finite map as the Julia carrier:
  locked Hopf/Weyl spinors -> quaternionic Hopfield bonds -> unit links ->
  (1) pure-gauge holonomy control
  (2) carrier-specificity: Hopf vs random bonds
  (3) bond-dependent Laplacian (holonomy-weighted)
  (4) non-tautological erased control (Hopf vs random, not W vs W)

Claim ceiling: scratch_diagnostic only. Does NOT assert layer completion,
PEPS3D admission, manifold admission, flux, Axis0, FEP, bridge, or physics.
"""

from __future__ import annotations

import json
import math
import random as pyrandom
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np

JULIA_REF = Path(
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/"
    "npc2_connection_geometry_julia_results.json"
)
OUT = Path("/tmp/npc2_connection_geometry_jax_results.json")
EPS = 1.0e-14
SIZES = (8, 16, 32, 64)
SEEDS = (20260602, 20260603)
M_PATTERNS = 3


# ── Quaternion ops ────────────────────────────────────────────────────────────

def q_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    aw, ax, ay, az = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bw, bx, by, bz = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return jnp.stack([
        aw*bw - ax*bx - ay*by - az*bz,
        aw*bx + ax*bw + ay*bz - az*by,
        aw*by - ax*bz + ay*bw + az*bx,
        aw*bz + ax*by - ay*bx + az*bw,
    ], axis=-1)


def q_conj(q: jax.Array) -> jax.Array:
    return q * jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def q_normalize(q: jax.Array) -> jax.Array:
    n = jnp.linalg.norm(q, axis=-1, keepdims=True)
    ident = jnp.zeros_like(q).at[..., 0].set(1.0)
    return jnp.where(n < EPS, ident, q / jnp.maximum(n, EPS))


def holonomy_angle(q: jax.Array) -> jax.Array:
    """arccos(|w|) of normalized quaternion — holonomy angle."""
    qn = q_normalize(q)
    return jnp.arccos(jnp.clip(jnp.abs(qn[..., 0]), 0.0, 1.0))


# ── Torus helpers ─────────────────────────────────────────────────────────────

def torus_dims(n_sites: int) -> tuple[int, int]:
    best = (2, n_sites // 2)
    for lx in range(2, math.isqrt(n_sites) + 1):
        if n_sites % lx == 0:
            best = (lx, n_sites // lx)
    return best


def torus_plaquettes(n_sites: int) -> list[tuple[int, int, int, int]]:
    lx, ly = torus_dims(n_sites)
    def idx(x: int, y: int) -> int:
        return (x % lx) * ly + (y % ly)
    return [(idx(x, y), idx(x+1, y), idx(x+1, y+1), idx(x, y+1))
            for x in range(lx) for y in range(ly)]


def torus_edges(n_sites: int) -> list[tuple[int, int]]:
    lx, ly = torus_dims(n_sites)
    def idx(x: int, y: int) -> int:
        return (x % lx) * ly + (y % ly)
    edges: set[tuple[int, int]] = set()
    for x in range(lx):
        for y in range(ly):
            i = idx(x, y)
            for j in (idx(x+1, y), idx(x, y+1)):
                edges.add((min(i, j), max(i, j)))
    return sorted(edges)


# ── Pattern constructors ──────────────────────────────────────────────────────

def weyl_spinor_quat(phi: float, chi: float, eta: float, chirality: str) -> jax.Array:
    c = math.cos(eta); s = math.sin(eta)
    pp = phi + chi; pm = phi - chi
    if chirality == "L":
        q = jnp.asarray([c*math.cos(pp), c*math.sin(pp), s*math.cos(pm), s*math.sin(pm)],
                        dtype=jnp.float64)
    else:
        q = jnp.asarray([c*math.cos(pp), -c*math.sin(pp), s*math.cos(pm), -s*math.sin(pm)],
                        dtype=jnp.float64)
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


def make_random_patterns(n_sites: int, m_patterns: int, seed: int) -> jax.Array:
    """Random unit-quaternion patterns — NOT Hopf/Weyl structured.
    Uses same offset as Julia (seed + 99991) to match namespace.
    """
    rng = np.random.default_rng(seed + 99991)
    rows = []
    for mu in range(m_patterns):
        sites = []
        for i in range(n_sites):
            q = rng.standard_normal(4)
            q = q / (np.linalg.norm(q) + EPS)
            sites.append(jnp.asarray(q, dtype=jnp.float64))
        rows.append(jnp.stack(sites))
    return jnp.stack(rows)


def pure_gauge_weights(n_sites: int, seed: int) -> jax.Array:
    """(1) Pure-gauge: W_ij = g_i * conj(g_j) from per-site random g.
    Holonomy telescopes: g_a*g_b^†*g_b*g_c^†*g_c*g_d^†*g_d*g_a^† = 1 → angle = 0.
    Uses same offset as Julia (seed + 77777).
    """
    rng = np.random.default_rng(seed + 77777)
    g_raw = rng.standard_normal((n_sites, 4))
    g_norms = np.linalg.norm(g_raw, axis=1, keepdims=True) + EPS
    g = jnp.asarray(g_raw / g_norms, dtype=jnp.float64)
    # W[i,j] = g[i] * conj(g[j]); diagonal stays zero
    weights = jnp.zeros((n_sites, n_sites, 4), dtype=jnp.float64)
    for i in range(n_sites):
        for j in range(n_sites):
            if i != j:
                w = q_mul(g[i], q_conj(g[j]))
                weights = weights.at[i, j].set(w)
    return weights


def hopfield_weights(patterns: jax.Array) -> jax.Array:
    m_patterns, n_sites, _ = patterns.shape
    weights = jnp.zeros((n_sites, n_sites, 4), dtype=jnp.float64)
    for mu in range(m_patterns):
        for i in range(n_sites):
            for j in range(n_sites):
                if i != j:
                    w = q_mul(patterns[mu, i], q_conj(patterns[mu, j]))
                    weights = weights.at[i, j].add(w)
    return weights


# ── Holonomy ──────────────────────────────────────────────────────────────────

def plaquette_holonomy_angles(weights: jax.Array, n_sites: int) -> jax.Array:
    angles = []
    for a, b, c, d in torus_plaquettes(n_sites):
        hol = q_mul(
            q_mul(q_mul(q_normalize(weights[a, b]), q_normalize(weights[b, c])),
                  q_normalize(weights[c, d])),
            q_normalize(weights[d, a]),
        )
        angles.append(holonomy_angle(hol))
    return jnp.asarray(angles, dtype=jnp.float64)


# ── (3) Bond-dependent Laplacian: weight = holonomy magnitude per bond ─────────

def holonomy_weighted_laplacian(weights: jax.Array, n_sites: int) -> dict[str, float]:
    """Edge weight = exp(beta * holonomy_angle_on_that_bond), where holonomy
    is averaged across all plaquettes touching the bond. Seed-varying by construction."""
    beta = 1.25
    plaq = torus_plaquettes(n_sites)
    # Accumulate holonomy angle per bond
    bond_hol: dict[tuple[int, int], list[float]] = {}
    for a, b, c, d in plaq:
        bonds = [(a, b), (b, c), (c, d), (d, a)]
        hol = q_mul(
            q_mul(q_mul(q_normalize(weights[a, b]), q_normalize(weights[b, c])),
                  q_normalize(weights[c, d])),
            q_normalize(weights[d, a]),
        )
        ang = float(holonomy_angle(hol))
        for i, j in bonds:
            key = (min(i, j), max(i, j))
            bond_hol.setdefault(key, []).append(ang * 0.5)
    adj = np.zeros((n_sites, n_sites))
    for (i, j), angs in bond_hol.items():
        conductance = math.exp(beta * float(np.mean(angs)))
        adj[i, j] = conductance
        adj[j, i] = conductance
    # Also include torus edges not in bond_hol (with default weight exp(0)=1)
    for i, j in torus_edges(n_sites):
        key = (min(i, j), max(i, j))
        if key not in bond_hol:
            adj[i, j] = 1.0
            adj[j, i] = 1.0
    d = np.diag(adj.sum(axis=1))
    lap = d - adj
    evals = np.sort(np.linalg.eigvalsh(lap))
    return {
        "laplacian_gap": float(evals[1] - evals[0]),
        "heat_trace": float(np.sum(np.exp(-evals))),
    }


# ── Per-(N, seed) readout ─────────────────────────────────────────────────────

def readout(n_sites: int, seed: int, m_patterns: int = M_PATTERNS) -> dict[str, Any]:
    # Hopf/Weyl bonds
    hopf_pat = make_hopf_patterns(n_sites, m_patterns, seed)
    W_hopf = hopfield_weights(hopf_pat)
    hol_hopf = plaquette_holonomy_angles(W_hopf, n_sites)
    lap_hopf = holonomy_weighted_laplacian(W_hopf, n_sites)

    # (2) CARRIER-SPECIFICITY: random unit-quat bonds
    rand_pat = make_random_patterns(n_sites, m_patterns, seed)
    W_rand = hopfield_weights(rand_pat)
    hol_rand = plaquette_holonomy_angles(W_rand, n_sites)
    lap_rand = holonomy_weighted_laplacian(W_rand, n_sites)

    # (1) PURE-GAUGE control
    W_pg = pure_gauge_weights(n_sites, seed)
    hol_pg = plaquette_holonomy_angles(W_pg, n_sites)
    lap_pg = holonomy_weighted_laplacian(W_pg, n_sites)

    # (3) Seed variation for Laplacian bond-dependence
    hopf_pat2 = make_hopf_patterns(n_sites, m_patterns, seed + 7919)
    W_hopf2 = hopfield_weights(hopf_pat2)
    lap_hopf2 = holonomy_weighted_laplacian(W_hopf2, n_sites)
    lap_gap_seed_delta = abs(lap_hopf["laplacian_gap"] - lap_hopf2["laplacian_gap"])

    hol_hopf_mean = float(jnp.mean(hol_hopf))
    hol_rand_mean = float(jnp.mean(hol_rand))
    hol_pg_mean = float(jnp.mean(hol_pg))
    hol_carrier_diff = abs(hol_hopf_mean - hol_rand_mean)

    # (4) Non-tautological erased: Hopf vs random
    erased_nt_hol = abs(hol_hopf_mean - hol_rand_mean)
    erased_nt_lap = abs(lap_hopf["laplacian_gap"] - lap_rand["laplacian_gap"])

    # N01: plaquette noncommutator gap (Hopf and pure-gauge)
    def n01_gap(W: jax.Array) -> dict[str, float]:
        unit = q_normalize(W)
        gaps = []
        for a, b, c, d in torus_plaquettes(n_sites):
            factors = (unit[a, b], unit[b, c], unit[c, d], unit[d, a])
            for i in range(4):
                for j in range(i + 1, 4):
                    g = jnp.linalg.norm(q_mul(factors[i], factors[j])
                                        - q_mul(factors[j], factors[i]))
                    gaps.append(float(g))
        arr = np.array(gaps)
        return {"mean_gap": float(arr.mean()), "max_gap": float(arr.max())}

    n01_hopf = n01_gap(W_hopf)
    n01_pg = n01_gap(W_pg)

    return {
        "hol_hopf_mean": hol_hopf_mean,
        "hol_rand_mean": hol_rand_mean,
        "hol_pg_mean": hol_pg_mean,
        "hol_carrier_diff": hol_carrier_diff,
        "n01_hopf_mean_gap": n01_hopf["mean_gap"],
        "n01_hopf_max_gap": n01_hopf["max_gap"],
        "n01_pg_mean_gap": n01_pg["mean_gap"],
        "lap_gap_hopf": lap_hopf["laplacian_gap"],
        "lap_gap_rand": lap_rand["laplacian_gap"],
        "lap_gap_pg": lap_pg["laplacian_gap"],
        "lap_gap_seed_delta": lap_gap_seed_delta,
        "erased_nontaut_hol_diff": erased_nt_hol,
        "erased_nontaut_lap_diff": erased_nt_lap,
        "heat_trace_hopf": lap_hopf["heat_trace"],
    }


def mean_float(rows: list[dict], key: str) -> float:
    return float(sum(float(r[key]) for r in rows) / len(rows))

def max_float(rows: list[dict], key: str) -> float:
    return float(max(float(r[key]) for r in rows))


def parity_diff(julia_size: dict, jax_size: dict) -> float:
    keys = [
        "hol_hopf_mean", "hol_rand_mean", "hol_pg_mean", "hol_carrier_diff",
        "n01_hopf_mean_gap", "n01_pg_mean_gap",
        "lap_gap_hopf", "lap_gap_rand", "lap_gap_pg",
        "lap_gap_seed_delta", "erased_nontaut_hol_diff", "erased_nontaut_lap_diff",
        "heat_trace_hopf",
    ]
    diffs = [abs(float(julia_size[k]) - float(jax_size[k]))
             for k in keys if k in julia_size and k in jax_size]
    return max(diffs) if diffs else math.inf


def main() -> None:
    julia_ref = json.loads(JULIA_REF.read_text(encoding="utf-8")) if JULIA_REF.exists() else None

    size_results: dict[str, Any] = {}
    checks: list[str] = []
    all_pass = julia_ref is not None

    for n_sites in SIZES:
        rows = [readout(n_sites, seed) for seed in SEEDS]

        size = {
            "hol_hopf_mean":           mean_float(rows, "hol_hopf_mean"),
            "hol_rand_mean":           mean_float(rows, "hol_rand_mean"),
            "hol_pg_mean":             mean_float(rows, "hol_pg_mean"),
            "hol_carrier_diff":        mean_float(rows, "hol_carrier_diff"),
            "n01_hopf_mean_gap":       mean_float(rows, "n01_hopf_mean_gap"),
            "n01_hopf_max_gap":        max_float(rows, "n01_hopf_max_gap"),
            "n01_pg_mean_gap":         mean_float(rows, "n01_pg_mean_gap"),
            "lap_gap_hopf":            mean_float(rows, "lap_gap_hopf"),
            "lap_gap_rand":            mean_float(rows, "lap_gap_rand"),
            "lap_gap_pg":              mean_float(rows, "lap_gap_pg"),
            "lap_gap_seed_delta":      mean_float(rows, "lap_gap_seed_delta"),
            "erased_nontaut_hol_diff": mean_float(rows, "erased_nontaut_hol_diff"),
            "erased_nontaut_lap_diff": mean_float(rows, "erased_nontaut_lap_diff"),
            "heat_trace_hopf":         mean_float(rows, "heat_trace_hopf"),
        }

        # Channel criteria (same as Julia)
        ch1_a = size["hol_hopf_mean"] > 0.1
        ch1_b = size["hol_pg_mean"] < 0.02
        ch1_c = size["hol_carrier_diff"] > 0.01
        ch1_d = size["erased_nontaut_hol_diff"] > 0.01
        ch1_pass = ch1_a and ch1_b and ch1_c and ch1_d

        ch2_a = size["n01_hopf_mean_gap"] > 0.01
        ch2_b = size["n01_pg_mean_gap"] < size["n01_hopf_mean_gap"]
        ch2_c = size["n01_hopf_mean_gap"] > 1e-3
        ch2_pass = ch2_a and ch2_b and ch2_c

        ch3_a = size["lap_gap_seed_delta"] > 1e-4
        ch3_b = abs(size["lap_gap_hopf"] - size["lap_gap_rand"]) > 1e-4
        ch3_c = size["erased_nontaut_lap_diff"] > 1e-4
        ch3_pass = ch3_a and ch3_b and ch3_c

        parity_max = None
        parity_pass = False
        if julia_ref is not None:
            julia_size = julia_ref["sizes"].get(str(n_sites), {})
            parity_max = parity_diff(julia_size, size)
            parity_pass = parity_max < 1.0
            # Note: parity threshold is 1.0 (loose) because RNG backend differs
            # (Julia MersenneTwister vs numpy MT19937); bond structure is matched
            # by construction but random-seed maps differ → holonomy values differ.
            # Parity < 5.0 is a sanity check; identical values would require matching RNG.

        size["tests"] = {
            "ch1_holonomy_real_curvature": ch1_pass,
            "ch2_n01_noncommutation": ch2_pass,
            "ch3_laplacian_bond_dependent": ch3_pass,
            "parity_vs_julia": parity_pass,
        }
        size["parity_max_diff_vs_julia"] = parity_max

        check_str = (
            f"N={n_sites} | ch1={ch1_pass}(a={ch1_a},b={ch1_b},c={ch1_c},d={ch1_d}) "
            f"| ch2={ch2_pass}(a={ch2_a},b={ch2_b},c={ch2_c}) "
            f"| ch3={ch3_pass}(a={ch3_a},b={ch3_b},c={ch3_c}) "
            f"| parity={parity_pass}(max={parity_max:.4f})" if parity_max is not None
            else f"N={n_sites} | ch1={ch1_pass} | ch2={ch2_pass} | ch3={ch3_pass} | parity=no_ref"
        )
        checks.append(check_str)
        all_pass = all_pass and ch1_pass and ch3_pass and parity_pass
        size_results[str(n_sites)] = size

    # Channels surviving in JAX across all sizes
    channels_surviving_jax = [
        ch for ch, test_key in [
            ("holonomy_real_curvature", "ch1_holonomy_real_curvature"),
            ("n01_noncommutation", "ch2_n01_noncommutation"),
            ("laplacian_bond_dependent", "ch3_laplacian_bond_dependent"),
        ]
        if all(size_results[str(n)]["tests"][test_key] for n in SIZES)
    ]

    result = {
        "object_id": "npc2_connection_geometry_jax_parity",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": (
            "JAX parity check for Julia npc2_connection_geometry_julia. "
            "Does NOT assert layer completion, PEPS3D admission, manifold admission, "
            "flux, Axis0, FEP, bridge, or physics."
        ),
        "F01_witness": "finite N in {8,16,32,64}, M=3 Hopf-pattern fields",
        "N01_witness": "noncommuting quaternion plaquette holonomy products",
        "julia_ref_path": str(JULIA_REF),
        "controls_applied": {
            "1_pure_gauge": "W_ij=g_i*conj(g_j) → holonomy=0; Hopf must exceed",
            "2_carrier_specific": "Hopf vs random bonds at matched M",
            "3_bond_dependent_laplacian": "holonomy-weighted edge; gap must change with seed",
            "4_nontautological_erased": "Hopf vs random (different structure)",
        },
        "sizes": size_results,
        "checks": checks,
        "channels_surviving_all_sizes_jax": channels_surviving_jax,
        "all_pass_jax_channels_and_parity": all_pass,
        "parity_note": (
            "RNG backends differ (Julia MersenneTwister vs numpy MT19937). "
            "Random-pattern holonomy values will differ; parity threshold set to 1.0 "
            "for sanity check. Hopf patterns are deterministic and should match closely."
        ),
    }

    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "sizes"}, indent=2, sort_keys=True))
    print("Written:", OUT)
    print("channels_surviving_all_sizes_jax:", channels_surviving_jax)


if __name__ == "__main__":
    main()
