#!/usr/bin/env python3
"""JAX x SMT — what JAX can and cannot do for a solver, measured not asserted.

THREE LAYERS, only two of which are real:

  1. INSTANCE GENERATION -- REAL.  JAX vmap/jit batches the numeric work that
     PRODUCES SMT instances. One batched engine evolution over N perturbations
     instead of N sequential ones, then N solver calls. This is the win.

  2. INSIDE THE SOLVE -- IMPOSSIBLE.  z3 is not a JAX primitive. There is no
     jit, vmap or grad through a DPLL(T) search. Anyone claiming `import jax.z3`
     is wrong. The handshake is at the boundary: arrays out of JAX, constraints
     into z3, status back.

  3. DIFFERENTIABLE RELAXATION -- REAL, and different in kind.  Encode the
     constraint as a SOFT penalty, use grad to descend toward a near-violation,
     then hand the candidate to z3 for the EXACT verdict. JAX proposes where to
     look; z3 decides. Useful when the search space is continuous and large.

This file measures 1 and demonstrates 3. It does not pretend 2 exists.

Corrects an overclaim in flip_harness.py, whose docstring said "vmap over rate
space" while the code ran a sequential Python loop with no vmap and no jit.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm
import z3

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
SM = jnp.array([[0, 0], [1, 0]], dtype=jnp.complex128)
P0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
P1 = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
H0 = 0.6 * SX + 0.8 * SZ


def _supH(H):
    return -1j * (jnp.kron(H, I2) - jnp.kron(I2, H.T))


def _supD(L):
    Ld = L.conj().T
    LdL = Ld @ L
    return jnp.kron(L, L.conj()) - 0.5 * jnp.kron(LdL, I2) - 0.5 * jnp.kron(I2, LdL.T)


def _liou(terr, g):
    """Liouvillian for one terrain, as a pure function of the rate vector."""
    if terr == "Se":
        H, J = g[0] * H0, [jnp.sqrt(g[1]) * SX, jnp.sqrt(g[1]) * SY, jnp.sqrt(g[1]) * SZ]
    elif terr == "Ne":
        H, J = g[0] * H0, []
    elif terr == "Ni":
        H, J = g[0] * H0, [jnp.sqrt(g[1]) * SM]
    else:  # Si
        H, J = g[2] * SZ, [jnp.sqrt(g[1]) * P0, jnp.sqrt(g[1]) * P1]
    L = _supH(H)
    for j in J:
        L = L + _supD(j)
    return L


def _op(name, rho):
    if name == "Ti":
        return 0.5 * rho + 0.5 * (P0 @ rho @ P0 + P1 @ rho @ P1)
    U = expm(-1j * 0.7 * SZ / 2)          # Fe
    return U @ rho @ U.conj().T


SCHED = [("Se", "Ti", "UP"), ("Ne", "Ti", "DOWN"), ("Ni", "Fe", "DOWN"), ("Si", "Fe", "UP")]


def _stage(rho, terr, op, arrow, g):
    prop = expm(_liou(terr, g) * 0.5)

    def flow(r):
        out = (prop @ r.reshape(-1)).reshape(2, 2)
        out = 0.5 * (out + out.conj().T)
        return out / jnp.trace(out).real

    return flow(_op(op, rho)) if arrow == "UP" else _op(op, flow(rho))


def _loop(rho, g, reverse=False):
    seq = list(reversed(SCHED)) if reverse else SCHED
    for terr, op, arrow in seq:
        rho = _stage(rho, terr, op, arrow, g)
    return rho


def _states(n=6):
    ks = jnp.arange(n) * 1.1
    return jnp.stack([0.5 * (I2 + 0.9 * jnp.cos(k) * SX + 0.9 * jnp.sin(k) * SZ) for k in ks])


STATES = _states()


def gaps_for_rates(g):
    """Forward-vs-reverse gap per sampled state, for ONE rate vector."""
    def one(rho):
        return jnp.linalg.norm(_loop(rho, g, False) - _loop(rho, g, True))
    return jax.vmap(one)(STATES)


# LAYER 1: vmap over the rate batch, jit the whole thing.
BATCHED = jax.jit(jax.vmap(gaps_for_rates))


def smt_status(gaps, erase=False):
    """z3 decides ONE instance. Pins the measured gaps; asks whether all-zero
    (order irrelevant) is consistent. Erased = no pinned table."""
    s = z3.Solver()
    gap = z3.Function("gap", z3.IntSort(), z3.RealSort())
    if not erase:
        for i, v in enumerate(gaps):
            s.add(gap(i) == z3.RealVal(str(round(float(v), 3))))
    s.add(z3.And([gap(i) == 0 for i in range(len(gaps))]))
    return str(s.check())


def sequential(rate_batch):
    return [gaps_for_rates(g) for g in rate_batch]


def demo_layer3(n_steps=40):
    """LAYER 3: soft relaxation. grad descends toward a near-violation of
    'the order gap stays above eps'; z3 then gives the exact verdict on the
    candidate JAX found. JAX proposes where to look, z3 decides."""
    eps = 0.05

    def softloss(g):
        # penalize being ABOVE eps -> gradient walks toward a violating region
        return jnp.sum(jnp.maximum(gaps_for_rates(g) - eps, 0.0) ** 2)

    grad = jax.jit(jax.grad(softloss))
    g = jnp.array([0.9, 0.6, 0.8])
    for _ in range(n_steps):
        g = jnp.clip(g - 0.25 * grad(g), 0.02, 2.0)
    found = gaps_for_rates(g)
    return {
        "search": "jax.grad descent on a soft relaxation of the constraint",
        "rates_found": [round(float(x), 4) for x in g],
        "min_gap_at_candidate": round(float(jnp.min(found)), 6),
        "violates_eps": bool(float(jnp.min(found)) < eps),
        "z3_exact_verdict_on_candidate": smt_status(found),
        "note": "JAX proposed the region; z3 returned the exact status. "
                "The gradient never entered the solver.",
    }


def main():
    key = jax.random.PRNGKey(0)
    out = {"harness": "jax_smt_bridge_v0", "classification": "tool_lego_fit_probe",
           "promotion_allowed": False, "layers": {}}

    for n in (32, 128):
        base = jnp.array([0.9, 0.6, 0.8])
        deltas = jax.random.uniform(key, (n, 3), minval=-0.35, maxval=0.35)
        batch = jnp.clip(base + deltas, 0.05, 2.0)

        _ = BATCHED(batch[:2]).block_until_ready()          # warm the jit
        t0 = time.perf_counter()
        vres = BATCHED(batch).block_until_ready()
        t_vmap = time.perf_counter() - t0

        t0 = time.perf_counter()
        sres = sequential(batch)
        t_seq = time.perf_counter() - t0

        agree = float(jnp.max(jnp.abs(vres - jnp.stack(sres))))
        t0 = time.perf_counter()
        stats = [smt_status(row) for row in vres]
        t_smt = time.perf_counter() - t0

        out["layers"][f"n={n}"] = {
            "layer1_instance_generation": {
                "vmap_jit_seconds": round(t_vmap, 4),
                "sequential_seconds": round(t_seq, 4),
                "speedup_x": round(t_seq / t_vmap, 1) if t_vmap > 0 else None,
                "max_abs_disagreement": agree,
                "identical_within_1e_12": bool(agree < 1e-12),
            },
            "solver_leg": {
                "n_instances": n,
                "seconds": round(t_smt, 4),
                "unsat_count": sum(1 for s in stats if s == "unsat"),
                "note": "one z3 call per instance; the solver is NOT batched and cannot be",
            },
        }

    out["layer2_inside_the_solver"] = {
        "possible": False,
        "why": "z3 is a DPLL(T) search, not a JAX primitive: no jit, no vmap, no grad "
               "through it. The handshake is at the boundary.",
    }
    out["layer3_differentiable_relaxation"] = demo_layer3()

    d = Path(__file__).parent / "results"
    d.mkdir(exist_ok=True)
    (d / "jax_smt_bridge_v0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
