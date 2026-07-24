#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — bounded periodic 4x4 Ising comparator.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: bounded Ising/Metropolis comparator — NOT an engine, NOT an
oracle, NOT the manifold

This is a finite comparator only: JAX x64 supplies the local Metropolis path,
while dimod ExactSolver and neal provide independent BQM checks.
"""
import json
import math
import time
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dimod
import neal

HERE = Path(__file__).resolve().parent
N = 4
NSITES = N * N
NREADS = 100


def idx(r, c):
    return (r % N) * N + (c % N)


def bonds(diagonal=False):
    edges = {(min(idx(r, c), idx(r, c + 1)), max(idx(r, c), idx(r, c + 1)), 1.0)
             for r in range(N) for c in range(N)}
    edges |= {(min(idx(r, c), idx(r + 1, c)), max(idx(r, c), idx(r + 1, c)), 1.0)
              for r in range(N) for c in range(N)}
    if diagonal:
        # One antiferromagnetic diagonal (J=-1) makes an odd plaquette.
        edges.add((idx(0, 0), idx(1, 1), -1.0))
    return sorted(edges)


def energy(spins, edge_list):
    return -sum(j * spins[i] * spins[k] for i, k, j in edge_list)


def delta_energy(spins, site, edge_list):
    # E(s with site flipped) - E(s), including each bond exactly once.
    return 2.0 * sum(j * spins[other] * spins[site]
                     for i, other, j in edge_list if i == site) + 2.0 * sum(
                         j * spins[i] * spins[site]
                         for i, other, j in edge_list if other == site)


def bqm(edge_list):
    model = dimod.BinaryQuadraticModel.empty(dimod.SPIN)
    for i, k, j in edge_list:
        model.add_interaction(i, k, -j)
    return model


def exact_ground(edge_list):
    best = math.inf
    best_state = None
    for mask in range(1 << NSITES):
        spins = [1 if mask & (1 << i) else -1 for i in range(NSITES)]
        e = energy(spins, edge_list)
        if e < best:
            best, best_state = e, spins
    return best, best_state


def metropolis_anneal(edge_list, seed, sweeps=300):
    coupling = jnp.zeros((NSITES, NSITES), dtype=jnp.float64)
    for i, k, j in edge_list:
        coupling = coupling.at[i, k].add(j).at[k, i].add(j)
    key = jax.random.key(seed)

    def body(sweep, state):
        key, spins, best = state
        temperature = 4.0 * (0.02 / 4.0) ** (sweep / max(1, sweeps - 1))
        key, site_key, accept_key = jax.random.split(key, 3)
        site = jnp.mod(sweep, NSITES)
        de = 2.0 * spins[site] * jnp.dot(coupling[site], spins)
        accept = (de <= 0.0) | (jax.random.uniform(accept_key) < jnp.exp(-de / temperature))
        spins = spins.at[site].set(jnp.where(accept, -spins[site], spins[site]))
        current = -0.5 * spins @ coupling @ spins
        return key, spins, jnp.minimum(best, current)

    init = jnp.where(jax.random.bernoulli(key, 0.5, (NSITES,)), 1.0, -1.0)
    initial = -0.5 * init @ coupling @ init
    return float(jax.jit(lambda x: jax.lax.fori_loop(0, sweeps, body, x))
                 ( (key, init, initial) )[2])


def run_case(name, edge_list, naive_guess):
    exact, _ = exact_ground(edge_list)
    exact_sample = dimod.ExactSolver().sample(bqm(edge_list))
    dimod_best = float(exact_sample.first.energy)
    jax_best = min(metropolis_anneal(edge_list, 1000 + i) for i in range(NREADS))
    neal_sample = neal.SimulatedAnnealingSampler().sample(bqm(edge_list), num_reads=NREADS,
                                                          seed=7000)
    neal_best = float(neal_sample.first.energy)
    return {
        "exact_ground_energy": exact,
        "dimod_exactsolver_energy": dimod_best,
        "jax_metropolis_best_energy": jax_best,
        "neal_best_of_100_energy": neal_best,
        "naive_ferro_ground_guess": naive_guess,
        "naive_guess_fails": naive_guess != exact,
        "exact_and_annealers_agree": exact == dimod_best == jax_best == neal_best,
    }


def main():
    t0 = time.perf_counter()
    ferro = bonds()
    frustrated = bonds(diagonal=True)
    # Exhaustive analytic-vs-full delta verification: 50 states × 16 sites.
    rng = jax.random.key(4242)
    max_delta_error = 0.0
    for _ in range(50):
        rng, subkey = jax.random.split(rng)
        spins = jnp.where(jax.random.bernoulli(subkey, 0.5, (NSITES,)), 1.0, -1.0)
        for site in range(NSITES):
            flipped = spins.at[site].set(-spins[site])
            max_delta_error = max(max_delta_error, abs(
                delta_energy(spins, site, ferro) - (energy(flipped, ferro) - energy(spins, ferro))))
    checks = {
        "delta_e_exhaustive": {"states": 50, "sites_per_state": NSITES,
                               "max_abs_error": max_delta_error,
                               "atol": 1e-12, "pass": max_delta_error <= 1e-12},
        "ferro": run_case("ferro", ferro, -32.0),
        "frustrated_negative_control": run_case("frustrated", frustrated, -32.0),
    }
    checks["ground_truth_crosscheck"] = checks["ferro"]["exact_and_annealers_agree"]
    checks["negative_control"] = (checks["frustrated_negative_control"]["naive_guess_fails"]
                                   and checks["frustrated_negative_control"]["exact_and_annealers_agree"])
    receipt = {
        "classification": "unofficial_stress_probe",
        "promotion_allowed": False,
        "claim_ceiling": "bounded Ising/Metropolis comparator — NOT an engine, NOT an oracle, NOT the manifold",
        "lattice": {"shape": [N, N], "periodic": True, "sites": NSITES,
                    "ferro_bonds": len(ferro), "frustrated_bonds": len(frustrated)},
        "checks": checks,
        "all_checks_pass": all(v if isinstance(v, bool) else v["pass"]
                                for k, v in checks.items() if k in ("delta_e_exhaustive",))
                            and checks["ground_truth_crosscheck"] and checks["negative_control"],
        "seconds": round(time.perf_counter() - t0, 3),
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    path = out / "ising_comparator_probe.json"
    path.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"[*] Ising comparator COMPLETED — checks {'ALL HOLD' if receipt['all_checks_pass'] else 'FAIL'}; receipt: {path}")
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
