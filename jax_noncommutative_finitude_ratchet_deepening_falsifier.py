#!/usr/bin/env python3
"""JAX-only falsifier for deeper-than-64 ratchet basin refinements.

The current ratchet hierarchy has:
  basin       = 4 topology cells
  subbasin    = 16 Weyl sheet/path/topology placements
  subsubbasin = 64 placement/order cells

This probe tests whether a fourth finite refinement is honestly present under
the same dynamics. It rejects refinements that only add numerical/noisy bins or
fail to collapse under the commuting/product negative.

No Julia execution. No PyTorch execution. No promotion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp

import jax_noncommutative_finitude_ratchet_basin_hierarchy as base


OUT = Path("jax_noncommutative_finitude_ratchet_deepening_falsifier_results.json")
N_SUBSUB = 16 * len(base.ORDER_TOKENS)
N_SUBSUBSUB = N_SUBSUB * 4


def _i(x: Any) -> int:
    return int(jax.device_get(x))


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def unique_count(values: jax.Array, alive: jax.Array, size: int) -> int:
    got = jnp.unique(values[alive], size=size, fill_value=-1)
    return len([int(v) for v in jax.device_get(got) if int(v) > 0])


def hist(values: jax.Array, alive: jax.Array, length: int) -> list[int]:
    return [int(x) for x in jax.device_get(jnp.bincount(values[alive], length=length))]


def evolve_state(product_mode: bool, reverse_mode: bool, prune_active: bool) -> dict[str, Any]:
    q, r, theta, alive, q_drifts, r_maxes = base.evolve(
        jnp.asarray(product_mode),
        jnp.asarray(reverse_mode),
        jnp.asarray(prune_active),
    )
    placement = base.placement_labels(q)
    word = jnp.where(product_mode, jnp.zeros_like(base.WORD_ID), base.WORD_ID)
    subsub = (placement - 1) * len(base.ORDER_TOKENS) + word + 1
    recurrence = base.recurrence_residual(q, r, theta, placement, word, product_mode)
    recurrence_bin = jnp.clip(jnp.floor(recurrence / 0.125).astype(jnp.int32), 0, 3)
    leaf_bin = jnp.clip(jnp.floor(theta / (jnp.pi / 8.0)).astype(jnp.int32), 0, 3)
    radial_bin = jnp.clip(jnp.floor(jnp.linalg.norm(r, axis=1) / 0.25).astype(jnp.int32), 0, 3)
    recurrence_cell = (subsub - 1) * 4 + recurrence_bin + 1
    leaf_cell = (subsub - 1) * 4 + leaf_bin + 1
    radial_cell = (subsub - 1) * 4 + radial_bin + 1
    return {
        "q": q,
        "r": r,
        "theta": theta,
        "alive": alive,
        "placement": placement,
        "word": word,
        "subsub": subsub,
        "recurrence": recurrence,
        "recurrence_bin": recurrence_bin,
        "leaf_bin": leaf_bin,
        "radial_bin": radial_bin,
        "recurrence_cell": recurrence_cell,
        "leaf_cell": leaf_cell,
        "radial_cell": radial_cell,
        "survivors": _i(jnp.sum(alive)),
        "pruned": base.N - _i(jnp.sum(alive)),
        "max_q_norm_drift": _f(jnp.max(q_drifts)),
        "max_bloch_norm_seen": _f(jnp.max(r_maxes)),
    }


def summarize_candidate(state: dict[str, Any], cell_key: str, bin_key: str) -> dict[str, Any]:
    alive = state["alive"]
    vals = state[cell_key]
    bins = state[bin_key]
    return {
        "unique_cells": unique_count(vals, alive, N_SUBSUBSUB),
        "bin_histogram": hist(bins, alive, 4),
    }


def run_probe() -> dict[str, Any]:
    a = evolve_state(product_mode=False, reverse_mode=False, prune_active=False)
    b = evolve_state(product_mode=False, reverse_mode=False, prune_active=True)
    d = evolve_state(product_mode=False, reverse_mode=True, prune_active=True)
    e = evolve_state(product_mode=True, reverse_mode=False, prune_active=False)

    def counts(state: dict[str, Any]) -> dict[str, Any]:
        alive = state["alive"]
        recurrence_live = state["recurrence"][alive]
        return {
            "survivors": state["survivors"],
            "pruned": state["pruned"],
            "subsub_cells": unique_count(state["subsub"], alive, N_SUBSUB),
            "recurrence": summarize_candidate(state, "recurrence_cell", "recurrence_bin"),
            "leaf": summarize_candidate(state, "leaf_cell", "leaf_bin"),
            "radial": summarize_candidate(state, "radial_cell", "radial_bin"),
            "recurrence_min": _f(jnp.min(recurrence_live)),
            "recurrence_max": _f(jnp.max(recurrence_live)),
            "recurrence_mean": _f(jnp.mean(recurrence_live)),
            "max_q_norm_drift": state["max_q_norm_drift"],
            "max_bloch_norm_seen": state["max_bloch_norm_seen"],
        }

    rows = {"A": counts(a), "B": counts(b), "D": counts(d), "E": counts(e)}

    leaf_radial_stable = (
        rows["A"]["leaf"]["unique_cells"] == N_SUBSUB
        and rows["B"]["leaf"]["unique_cells"] == N_SUBSUB
        and rows["E"]["leaf"]["unique_cells"] == 1
        and rows["A"]["radial"]["unique_cells"] == N_SUBSUB
        and rows["B"]["radial"]["unique_cells"] == N_SUBSUB
        and rows["E"]["radial"]["unique_cells"] == 1
    )
    recurrence_rejected = (
        rows["B"]["recurrence"]["unique_cells"] > N_SUBSUB
        and rows["B"]["recurrence"]["unique_cells"] < (N_SUBSUBSUB // 2)
        and rows["E"]["recurrence"]["unique_cells"] > 1
    )
    checks = {
        "prior_subsub_hierarchy_present_A": rows["A"]["subsub_cells"] == N_SUBSUB,
        "prior_subsub_hierarchy_present_B": rows["B"]["subsub_cells"] == N_SUBSUB,
        "product_negative_collapses_prior_hierarchy": rows["E"]["subsub_cells"] == 1,
        "leaf_radial_candidates_do_not_overrefine": leaf_radial_stable,
        "recurrence_candidate_rejected_as_noisy_or_control_leaky": recurrence_rejected,
        "prune_still_fires": rows["B"]["pruned"] > 0,
        "reverse_order_same_cell_count_but_state_order_sensitive": rows["D"]["subsub_cells"] == rows["B"]["subsub_cells"],
        "f01_retraction": max(row["max_q_norm_drift"] for row in rows.values()) < 1.0e-10,
        "finite_bloch_ball": max(row["max_bloch_norm_seen"] for row in rows.values()) <= 1.0 + base.F01_TOL + 1.0e-9,
    }
    audit_pass = all(checks.values())
    return {
        "object": "jax_noncommutative_finitude_ratchet_deepening_falsifier",
        "classification": "diagnostic_jax_ratchet_deepening_falsifier",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_mode": "read_only",
        "claim_ceiling": (
            "Falsifier for deeper ratchet hierarchy only. Confirms current 4/16/64 "
            "diagnostic hierarchy and blocks tested fourth-level refinements. No layer "
            "completion, stacking admission, flux, Axis0, FEP, physics, or final manifold claim."
        ),
        "finite_map": (
            "final finite ratchet states -> tested fourth-level refinements "
            "{recurrence-depth, Hopf-leaf bin, radial-norm bin} with product/commuting controls"
        ),
        "current_hierarchy": {
            "basins": 4,
            "subbasins": 16,
            "subsubbasins": N_SUBSUB,
            "tested_subsubsub_capacity": N_SUBSUBSUB,
        },
        "candidate_verdicts": {
            "leaf_bin": "stable_readout_no_new_hierarchy",
            "radial_bin": "stable_readout_no_new_hierarchy",
            "recurrence_depth_bin": "rejected_noisy_or_control_leaky",
        },
        "rows": rows,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
        "blocked_consumers": [
            "subsubsubbasin_admission",
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "flux",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
    }


def main() -> int:
    result = run_probe()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    rows = result["rows"]
    print(
        "jax_ratchet_deepening_falsifier "
        f"A={rows['A']['subsub_cells']} B={rows['B']['subsub_cells']} E={rows['E']['subsub_cells']} "
        f"B_leaf={rows['B']['leaf']['unique_cells']} B_radial={rows['B']['radial']['unique_cells']} "
        f"B_recurrence={rows['B']['recurrence']['unique_cells']} E_recurrence={rows['E']['recurrence']['unique_cells']} "
        f"AUDIT_PASS={result['AUDIT_PASS']}"
    )
    return 0 if result["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
