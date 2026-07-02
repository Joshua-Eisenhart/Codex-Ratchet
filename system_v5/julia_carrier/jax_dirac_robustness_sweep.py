#!/usr/bin/env python3
"""Batched JAX robustness sweep for the Dirac chirality branch/prune result."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


SEEDS = (1, 42, 99, 2026)
ENSEMBLE_SIZES = (300, 600, 1200)
DT_VALUES = (0.02, 0.01, 0.005)
T_FINAL = 12.0
PRUNE_THRESHOLD = -0.01
INIT_Q_MIN = 0.1
RESULT_PATH = Path("jax_dirac_robustness_sweep_results.json")


def normalized_targets() -> jnp.ndarray:
    raw = jnp.asarray(
        [
            [0.0, 0.0, 1.0, 0.3],
            [0.0, 0.0, 0.3, 1.0],
            [1.0, 0.3, 0.0, 0.0],
            [0.3, 1.0, 0.0, 0.0],
        ],
        dtype=jnp.complex128,
    )
    return raw / jnp.linalg.norm(raw, axis=1, keepdims=True)


TARGETS = normalized_targets()
GAMMA5_DIAG = jnp.asarray([-1.0, -1.0, 1.0, 1.0], dtype=jnp.float64)


def normalize(psi: jnp.ndarray) -> jnp.ndarray:
    return psi / jnp.linalg.norm(psi, axis=-1, keepdims=True)


def chiral_charge(psi: jnp.ndarray) -> jnp.ndarray:
    return jnp.real(jnp.sum(jnp.conj(psi) * (GAMMA5_DIAG * psi), axis=-1))


def basins(psi: jnp.ndarray) -> jnp.ndarray:
    overlaps = jnp.abs(psi @ jnp.conj(TARGETS.T)) ** 2
    return jnp.argmax(overlaps, axis=-1) + 1


def populated_basin_list(psi: jnp.ndarray, active: jnp.ndarray | None = None) -> list[int]:
    basin_ids = basins(psi)
    if active is not None:
        basin_ids = basin_ids[active]
    present = [int(k) for k in range(1, 5) if bool(jnp.any(basin_ids == k))]
    return present


def make_initial_ensemble(seed: int, n: int) -> jnp.ndarray:
    key = jax.random.PRNGKey(seed)
    oversample = max(16 * n, n + 4096)
    real_key, imag_key = jax.random.split(key)
    z = jax.random.normal(real_key, (oversample, 4), dtype=jnp.float64)
    z = z + 1j * jax.random.normal(imag_key, (oversample, 4), dtype=jnp.float64)
    psi = normalize(z.astype(jnp.complex128))
    keep = chiral_charge(psi) > INIT_Q_MIN
    kept_count = int(jnp.sum(keep))
    if kept_count < n:
        raise RuntimeError(
            f"seed={seed} N={n}: only {kept_count} filtered q>{INIT_Q_MIN} "
            f"states found from oversample={oversample}"
        )
    selected = jnp.nonzero(keep, size=n, fill_value=0)[0]
    return psi[selected]


@jax.jit
def euler_step(psi: jnp.ndarray) -> jnp.ndarray:
    basin_ids = basins(psi) - 1
    nearest = TARGETS[basin_ids]
    inner = jnp.sum(jnp.conj(psi) * nearest, axis=-1, keepdims=True)
    return 2.0 * (nearest - inner * psi)


def simulate(psi0: jnp.ndarray, dt: float, prune: bool) -> tuple[jnp.ndarray, jnp.ndarray, float]:
    steps = int(round(T_FINAL / dt))
    if abs(steps * dt - T_FINAL) > 1e-12:
        raise ValueError(f"dt={dt} does not divide T_FINAL={T_FINAL}")

    def scan_step(
        carry: tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray],
        _: Any,
    ) -> tuple[tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray], None]:
        psi, pruned, max_drift = carry
        proposed = normalize(psi + dt * euler_step(psi))
        if prune:
            next_pruned = jnp.logical_or(pruned, chiral_charge(proposed) < PRUNE_THRESHOLD)
            psi_next = jnp.where(pruned[:, None], psi, proposed)
            pruned_next = next_pruned
        else:
            psi_next = proposed
            pruned_next = pruned
        drift = jnp.max(jnp.abs(jnp.linalg.norm(psi_next, axis=-1) - 1.0))
        return (psi_next, pruned_next, jnp.maximum(max_drift, drift)), None

    init_pruned = jnp.zeros((psi0.shape[0],), dtype=bool)
    init_drift = jnp.asarray(0.0, dtype=jnp.float64)
    (psi_final, pruned_final, max_drift), _ = jax.lax.scan(
        scan_step,
        (psi0, init_pruned, init_drift),
        xs=None,
        length=steps,
    )
    return psi_final, pruned_final, float(max_drift)


def row_for(seed: int, n: int, dt: float) -> dict[str, Any]:
    psi0 = make_initial_ensemble(seed, n)
    a_final, a_pruned, a_drift = simulate(psi0, dt, prune=False)
    b_final, b_pruned, b_drift = simulate(psi0, dt, prune=True)
    c_final, c_pruned, c_drift = simulate(psi0, dt, prune=False)

    row = {
        "seed": seed,
        "N": n,
        "dt": dt,
        "A": {
            "populated": populated_basin_list(a_final, ~a_pruned),
            "pruned": int(jnp.sum(a_pruned)),
        },
        "B": {
            "populated": populated_basin_list(b_final, ~b_pruned),
            "pruned": int(jnp.sum(b_pruned)),
        },
        "C": {
            "populated": populated_basin_list(c_final, ~c_pruned),
            "pruned": int(jnp.sum(c_pruned)),
        },
        "max_norm_drift": max(a_drift, b_drift, c_drift),
    }
    row["accepted"] = (
        row["A"]["populated"] == [1, 2, 3, 4]
        and row["B"]["populated"] == [1, 2]
        and row["C"]["populated"] == row["A"]["populated"]
        and row["B"]["pruned"] > 0
        and row["max_norm_drift"] < 1.0e-3
    )
    return row


def main() -> None:
    rows = [
        row_for(seed, n, dt)
        for seed, n, dt in itertools.product(SEEDS, ENSEMBLE_SIZES, DT_VALUES)
    ]
    breaking = [
        {
            "seed": row["seed"],
            "N": row["N"],
            "dt": row["dt"],
            "A.populated": row["A"]["populated"],
            "B.populated": row["B"]["populated"],
            "C.populated": row["C"]["populated"],
            "B.pruned": row["B"]["pruned"],
            "max_norm_drift": row["max_norm_drift"],
        }
        for row in rows
        if not row["accepted"]
    ]
    robust = len(breaking) == 0
    receipt = {
        "object": "Dirac 4-spinor chirality branch/prune JAX robustness sweep",
        "seeds": list(SEEDS),
        "ensemble_sizes": list(ENSEMBLE_SIZES),
        "dt_values": list(DT_VALUES),
        "t_final": T_FINAL,
        "acceptance": {
            "A.populated": [1, 2, 3, 4],
            "B.populated": [1, 2],
            "C.populated": "A.populated",
            "B.pruned": ">0",
            "max_norm_drift": "<1e-3",
        },
        "ROBUST": robust,
        "breaking_combinations": breaking,
        "rows": rows,
    }
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"combinations={len(rows)}")
    print(f"ROBUST={str(robust).lower()}")
    print(f"breaking_combinations={json.dumps(breaking, sort_keys=True)}")


if __name__ == "__main__":
    main()
