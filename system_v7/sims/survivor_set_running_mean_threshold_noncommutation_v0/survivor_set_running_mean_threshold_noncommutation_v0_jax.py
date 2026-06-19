#!/usr/bin/env python3
"""JAX leg -- independent recompute via a DISTINCT representation.

Computation style UNIQUE to this leg: the survivor set is a BOOLEAN MASK over
the full (2^N, N) enumeration, and every constraint is a jnp batched predicate
that updates the mask. This is a different data structure from the exact leg's
explicit Python-set operations, so agreement between the two legs is a genuine
cross-check, not a shared implementation.

It recomputes the LOAD-BEARING numbers:
  * running_mean_threshold under the running mask  -> 62/105 noncommute (real-valued mean, no rounding)
  * running_mean_threshold under the fixed reference -> 0/105 (isolator)
  * ensemble_consistency_majority (a confluence control) -> 0/105
It does NOT read the exact leg's result.
"""

import itertools
import json
import os
import hashlib
from datetime import datetime, timezone

import jax
import jax.numpy as jnp

jax.config.update("jax_enable_x64", True)

SIM_ID = "survivor_set_running_mean_threshold_noncommutation_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
OFFSETS = [-2, -1, 1, 2]


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def windows_for(n):
    seen = []
    for k in range(1, len(OFFSETS) + 1):
        for t in itertools.combinations(OFFSETS, k):
            comp = tuple(sorted(set(o % n for o in t)))
            if comp not in seen:
                seen.append(comp)
    return seen


def enumerate_configs(n):
    return jnp.array(list(itertools.product([0, 1], repeat=n)), dtype=jnp.int32)  # (2^n, n)


def count1(configs, comp):
    # number of 1-cells inside comp, per config -> (2^n,)
    return configs[:, jnp.array(comp)].sum(axis=1)


def step_density(configs, mask, comp, ref_mask):
    """survive iff count1 >= REAL-valued mean count1 over ref_mask (no rounding).
    ref_mask=mask -> running; ref_mask=all -> fixed reference."""
    c1 = count1(configs, comp)
    denom = jnp.maximum(ref_mask.sum(), 1)
    mean = (c1 * ref_mask).sum() / denom
    return mask & (c1 >= mean)


def step_density_floor(configs, mask, comp):
    """floor(mean) threshold -- state-dependent but confluent control."""
    c1 = count1(configs, comp)
    denom = jnp.maximum(mask.sum(), 1)
    mean = (c1 * mask).sum() / denom
    return mask & (c1 >= jnp.floor(mean))


def step_consistency(configs, mask, comp):
    """admit x iff every cell c equals the majority value of cell c among masked configs
    agreeing with x on (c+comp) excluding c. Vectorized over all configs at once."""
    n = configs.shape[1]
    new_keep = jnp.ones(configs.shape[0], dtype=bool)
    for c in range(n):
        w = [(c + o) % n for o in comp if (c + o) % n != c]
        if not w:
            continue
        wj = jnp.array(w)
        # agreement[i,j] = config i matches config j on all window cells w
        A = (configs[:, None, wj] == configs[None, :, wj]).all(axis=2)  # (M, M)
        Am = A & mask[None, :]  # only count masked neighbours j
        ones = jnp.where(Am & (configs[None, :, c] == 1), 1, 0).sum(axis=1)
        zeros = jnp.where(Am & (configs[None, :, c] == 0), 1, 0).sum(axis=1)
        tie = ones == zeros
        maj = jnp.where(ones > zeros, 1, 0)
        cell_ok = tie | (configs[:, c] == maj)  # unconstrained on tie/empty
        new_keep = new_keep & cell_ok
    return mask & new_keep


def noncommute_density(configs, windows, fixed):
    all_mask = jnp.ones(configs.shape[0], dtype=bool)
    nc = 0
    for a, b in ((a, b) for a in windows for b in windows if a < b):
        if fixed:
            AB = step_density(configs, step_density(configs, all_mask, a, all_mask), b, all_mask)
            BA = step_density(configs, step_density(configs, all_mask, b, all_mask), a, all_mask)
        else:
            sa = step_density(configs, all_mask, a, all_mask)
            AB = step_density(configs, sa, b, sa)
            sb = step_density(configs, all_mask, b, all_mask)
            BA = step_density(configs, sb, a, sb)
        if not bool(jnp.array_equal(AB, BA)):
            nc += 1
    return nc


def noncommute_consistency(configs, windows):
    all_mask = jnp.ones(configs.shape[0], dtype=bool)
    nc = 0
    for a, b in ((a, b) for a in windows for b in windows if a < b):
        AB = step_consistency(configs, step_consistency(configs, all_mask, a), b)
        BA = step_consistency(configs, step_consistency(configs, all_mask, b), a)
        if not bool(jnp.array_equal(AB, BA)):
            nc += 1
    return nc


def noncommute_floor(configs, windows):
    all_mask = jnp.ones(configs.shape[0], dtype=bool)
    nc = 0
    for a, b in ((a, b) for a in windows for b in windows if a < b):
        AB = step_density_floor(configs, step_density_floor(configs, all_mask, a), b)
        BA = step_density_floor(configs, step_density_floor(configs, all_mask, b), a)
        if not bool(jnp.array_equal(AB, BA)):
            nc += 1
    return nc


def run_for_n(n):
    configs = enumerate_configs(n)
    windows = windows_for(n)
    npairs = len(windows) * (len(windows) - 1) // 2
    return {
        "N": n,
        "pair_count": npairs,
        "running_mean_threshold_running_X_noncommute": noncommute_density(configs, windows, fixed=False),
        "running_mean_threshold_fixed_reference_noncommute": noncommute_density(configs, windows, fixed=True),
        "floor_mean_threshold_running_X_noncommute": noncommute_floor(configs, windows),
        "ensemble_consistency_noncommute": noncommute_consistency(configs, windows),
    }


def main():
    per_n = {n: run_for_n(n) for n in (5, 6, 7)}
    order_dependence = all(per_n[n]["running_mean_threshold_running_X_noncommute"] > 0 for n in per_n)
    isolator = all(per_n[n]["running_mean_threshold_fixed_reference_noncommute"] == 0 for n in per_n)
    necessary_not_sufficient = all(
        per_n[n]["floor_mean_threshold_running_X_noncommute"] == 0
        and per_n[n]["ensemble_consistency_noncommute"] == 0
        for n in per_n
    )

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "boolean_mask_over_full_enumeration_jnp_batched_predicate",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "per_N": per_n,
        "claims": {
            "running_X_admits_order_dependence": bool(order_dependence),
            "isolator_fixed_reference_commutes": bool(isolator),
            "state_dependence_necessary_not_sufficient": bool(necessary_not_sufficient),
            "rule": "convention-free: count1 >= real-valued mean over the running survivor set (no rounding)",
            "emergence_label": "REJECTED as overclaim by the full-fleet audit; this is order-dependent survivor-set filtering, not strong emergence",
        },
        "package_versions": {"jax": jax.__version__},
        "packages_used": ["jax"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "boolean-mask batched predicate recompute over the full enumeration (distinct representation from the exact leg)"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing"},
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_jax_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"jax leg wrote {out}")
    for n in (5, 6, 7):
        r = per_n[n]
        print(f"  N={n}: density(>=mean) running-X {r['running_mean_threshold_running_X_noncommute']}/{r['pair_count']} "
              f"| fixed-ref {r['running_mean_threshold_fixed_reference_noncommute']} | floor(mean) {r['floor_mean_threshold_running_X_noncommute']} | consistency {r['ensemble_consistency_noncommute']}")
    print(f"  order_dependence={order_dependence} isolator={isolator} necessary_not_sufficient={necessary_not_sufficient}")


if __name__ == "__main__":
    main()
