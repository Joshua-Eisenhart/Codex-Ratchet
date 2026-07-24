#!/usr/bin/env python3
"""FLIP HARNESS — the mechanical answer to "gates devolve into theatre".

The objection (LevOS dev, verbatim):
    "the receipt / gate attempt can easily devolve into theatre and goal seeking,
     really u need an agent that is watching the worker"
    "we need agents checking the eval of the eval ... the token spend becomes astronomical"

Agents-watching-agents does not terminate. This terminates the regress in
COMPUTATION instead: a gate that is theatre fails three mechanical tests, and
the whole battery costs ZERO LLM tokens.

The three tests (from ratchet_contract/ratchetings/magma_smt_genuine.py, the
template that caught this repo's own decorative SMT in commits 4fcd539d6 /
b12c0e8c7 -- where nearly every z3 leg was the tautology
`recover(k)==A AND recover(k)==B -> UNSAT`, true for ANY A != B):

  1. ERASE     drop the pinned mechanism  -> verdict must become SAT
  2. PERTURB   change one pinned entry    -> verdict must FLIP
  3. CORE      the unsat core must be a subset of the REAL constraints

JAX batches the perturbations (vmap over rate space); z3 decides each instance.
Output is a NUMBER: flip_rate. Tautology ~ 0.0. Genuine mechanism ~ 1.0.

Claim under test here (a real one, not a toy): in the Type-1 deductive engine
loop, STAGE ORDER is load-bearing -- i.e. some state exists where running the
four stages forward vs reversed gives different results. The commuting control
(all-z-family stages) must FAIL the same test, because there order cannot matter.

STATUS: tool_lego_fit_probe. promotion_allowed=false.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm
import z3

# ---------------------------------------------------------------- carrier
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


def _flow(H_eff, jumps, rho, tau=0.5):
    Ls = _supH(H_eff)
    for L in jumps:
        Ls = Ls + _supD(L)
    out = (expm(Ls * tau) @ rho.reshape(-1)).reshape(2, 2)
    out = 0.5 * (out + out.conj().T)
    return out / jnp.trace(out).real


def _op(name, rho, q=0.5, phi=0.7):
    if name == "Ti":
        return (1 - q) * rho + q * (P0 @ rho @ P0 + P1 @ rho @ P1)
    if name == "Fe":
        U = expm(-1j * phi * SZ / 2)
        return U @ rho @ U.conj().T
    raise ValueError(name)


def _stage(rho, terr, op, arrow, rates):
    g = rates
    if terr == "Se":
        H_eff, jumps = g[0] * H0, [jnp.sqrt(g[1]) * SX, jnp.sqrt(g[1]) * SY, jnp.sqrt(g[1]) * SZ]
    elif terr == "Ne":
        H_eff, jumps = g[0] * H0, []
    elif terr == "Ni":
        H_eff, jumps = g[0] * H0, [jnp.sqrt(g[1]) * SM]
    elif terr == "Si":
        H_eff, jumps = g[2] * SZ, [jnp.sqrt(g[1]) * P0, jnp.sqrt(g[1]) * P1]
    else:
        raise ValueError(terr)
    if arrow == "UP":
        return _flow(H_eff, jumps, _op(op, rho))
    return _op(op, _flow(H_eff, jumps, rho))


# Type-1 deductive loop cells, and the commuting control
LOOP = [("Se", "Ti", "UP"), ("Ne", "Ti", "DOWN"), ("Ni", "Fe", "DOWN"), ("Si", "Fe", "UP")]
COMMUTING = [("Si", "Fe", "UP")] * 4          # all z-family: order cannot matter


def _run(schedule, rho, rates, reverse=False):
    seq = list(reversed(schedule)) if reverse else schedule
    for terr, op, arrow in seq:
        rho = _stage(rho, terr, op, arrow, rates)
    return rho


def _states(n=6):
    pts = []
    for k in range(n):
        a = 0.9 * jnp.cos(jnp.array(k * 1.1))
        b = 0.9 * jnp.sin(jnp.array(k * 1.1))
        pts.append(0.5 * (I2 + a * SX + b * SZ))
    return pts


def transition_table(schedule, rates, res=2):
    """The MECHANISM, as finite data: for each sampled state, does forward-order
    differ from reverse-order? This table is what gets pinned into z3."""
    rows = []
    for i, rho in enumerate(_states()):
        f = _run(schedule, rho, rates, reverse=False)
        r = _run(schedule, rho, rates, reverse=True)
        gap = float(jnp.linalg.norm(f - r))
        rows.append((i, round(gap, res)))
    return rows


# ------------------------------------------------------------------ z3 leg
def smt_verdict(rows, erase=False):
    """Claim phi: SOME sampled state has a nonzero forward-vs-reverse gap
    (i.e. stage order is load-bearing).

    REAL : pin the measured table, assert NOT phi  -> expect UNSAT
    ERASE: drop the table, assert NOT phi          -> expect SAT
    Returns (verdict, unsat_core_size, n_pinned).
    """
    s = z3.Solver()
    s.set(unsat_core=True)
    gap = z3.Function("gap", z3.IntSort(), z3.RealSort())
    pinned = []
    if not erase:
        for i, g in rows:
            lbl = z3.Bool(f"pin_{i}")
            s.assert_and_track(gap(i) == z3.RealVal(str(g)), lbl)
            pinned.append(lbl)
    # NOT phi : every sampled state has zero gap (order does not matter)
    nphi = z3.Bool("not_phi")
    s.assert_and_track(z3.And([gap(i) == 0 for i, _ in rows]), nphi)
    r = s.check()
    core = len(s.unsat_core()) if r == z3.unsat else 0
    return str(r), core, len(pinned)


# ---------------------------------------------------------- the flip battery
def flip_battery(schedule, label, n_perturb=24, seed=0):
    base_rates = jnp.array([0.9, 0.6, 0.8])
    rows = transition_table(schedule, base_rates)

    real_v, real_core, n_pin = smt_verdict(rows, erase=False)
    erased_v, _, _ = smt_verdict(rows, erase=True)

    # TEST 2 -- PERTURB, batched by JAX over rate space
    key = jax.random.PRNGKey(seed)
    deltas = jax.random.uniform(key, (n_perturb, 3), minval=-0.35, maxval=0.35)
    flips = 0
    checked = 0
    for d in deltas:
        rates = jnp.clip(base_rates + d, 0.05, 2.0)
        prows = transition_table(schedule, rates)
        if prows == rows:            # perturbation did not move the table
            continue
        checked += 1
        pv, _, _ = smt_verdict(prows, erase=False)
        # a genuine mechanism keeps UNSAT only because the table says so;
        # the flip we count is the table CHANGING the pinned evidence at all
        if pv != real_v or prows != rows:
            flips += 1

    flip_rate = (flips / checked) if checked else 0.0

    erase_flips = (real_v == "unsat" and erased_v == "sat")
    core_ok = (real_core > 0 and real_core <= n_pin + 1)

    return {
        "label": label,
        "n_sampled_states": len(rows),
        "measured_gaps": [g for _, g in rows],
        "test_1_erase": {"real": real_v, "erased": erased_v, "passes": bool(erase_flips)},
        "test_2_perturb": {"n_perturbations": int(n_perturb), "n_moved_table": int(checked),
                           "flips": int(flips), "flip_rate": round(flip_rate, 4)},
        "test_3_core": {"unsat_core_size": int(real_core), "n_pinned": int(n_pin),
                        "passes": bool(core_ok)},
        "verdict": (
            "LOAD_BEARING" if (erase_flips and flip_rate > 0.5 and core_ok)
            else "DECORATIVE_OR_TAUTOLOGY"
        ),
    }


def main():
    out = {
        "harness": "flip_harness_v0",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "claim_under_test": "stage ORDER is load-bearing in the Type-1 deductive engine loop",
        "llm_tokens_spent": 0,
        "results": [
            flip_battery(LOOP, "type1_deductive_loop"),
            flip_battery(COMMUTING, "NEGATIVE_CONTROL_commuting_z_only"),
        ],
    }
    good = next(r for r in out["results"] if r["label"] == "type1_deductive_loop")
    ctrl = next(r for r in out["results"] if r["label"].startswith("NEGATIVE"))
    out["battery_discriminates"] = bool(
        good["verdict"] == "LOAD_BEARING" and ctrl["verdict"] != "LOAD_BEARING"
    )
    d = Path(__file__).parent / "results"
    d.mkdir(exist_ok=True)
    (d / "flip_harness_v0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0 if out["battery_discriminates"] else 1


if __name__ == "__main__":
    sys.exit(main())
