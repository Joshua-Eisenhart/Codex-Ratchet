#!/usr/bin/env python3
"""JAX leg for spinor_quotient_freedom_discriminator_v0.

Independent representation from the exact leg:
- carrier is integer arrays `[base_index, fiber_phase_index]`;
- public quotient is computed by `jnp.unique` over base indices;
- frame-relative probe bins are vectorized from cos(2πk/N - theta);
- no-frame control is an explicit constant probe.

This remains a scratch discriminator. It does not admit spinors generally.
"""

from __future__ import annotations

import json
import pathlib

import jax
import jax.numpy as jnp

SIM_ID = "spinor_quotient_freedom_discriminator_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT = HERE / "results" / f"{SIM_ID}_jax_results.json"

BASE_COUNT = 4
N_FIBER = 8
FRAME_THETA = 0.0


def states_array() -> jnp.ndarray:
    rows = []
    for b in range(BASE_COUNT):
        for k in range(N_FIBER):
            rows.append((b, k))
    return jnp.array(rows, dtype=jnp.int32)


def phase(k: jnp.ndarray) -> jnp.ndarray:
    return 2.0 * jnp.pi * k.astype(jnp.float32) / float(N_FIBER)


def frame_bins(rows: jnp.ndarray) -> jnp.ndarray:
    v = jnp.cos(phase(rows[:, 1]) - FRAME_THETA)
    # encode + as 1, 0 as 0, - as -1
    return jnp.where(v > 1e-6, 1, jnp.where(v < -1e-6, -1, 0)).astype(jnp.int32)


def class_bin_counts(rows: jnp.ndarray, bins: jnp.ndarray) -> dict:
    out = {}
    for b in range(BASE_COUNT):
        mask = rows[:, 0] == b
        vals = bins[mask]
        uniq, counts = jnp.unique(vals, return_counts=True)
        out[str(b)] = {str(int(u)): int(c) for u, c in zip(uniq.tolist(), counts.tolist())}
    return out


def main() -> int:
    rows = states_array()
    public_bases, public_counts = jnp.unique(rows[:, 0], return_counts=True)
    public_class_count = int(public_bases.shape[0])
    public_class_size_ok = bool(jnp.all(public_counts == N_FIBER))

    bins = frame_bins(rows)
    frame_rows = class_bin_counts(rows, bins)
    frame_split_classes = sum(1 for d in frame_rows.values() if len(d) > 1)
    frame_max_split = max(len(d) for d in frame_rows.values())

    no_frame_bins = jnp.zeros((rows.shape[0],), dtype=jnp.int32)
    no_frame_rows = class_bin_counts(rows, no_frame_bins)
    no_frame_split_classes = sum(1 for d in no_frame_rows.values() if len(d) > 1)
    no_frame_max_split = max(len(d) for d in no_frame_rows.values())

    # Label-shuffle control: shift fiber by 3 and recompute frame bins. Public counts must remain;
    # each public class must still be split by frame bins.
    shuffled = rows.at[:, 1].set((rows[:, 1] + 3) % N_FIBER)
    shuf_bases, shuf_counts = jnp.unique(shuffled[:, 0], return_counts=True)
    shuf_bins = frame_bins(shuffled)
    shuf_rows = class_bin_counts(shuffled, shuf_bins)
    shuf_split_classes = sum(1 for d in shuf_rows.values() if len(d) > 1)
    label_shuffle_control = bool(jnp.all(shuf_counts == N_FIBER)) and int(shuf_bases.shape[0]) == BASE_COUNT and shuf_split_classes == BASE_COUNT

    tests = {
        "finite_carrier_exists": int(rows.shape[0]) == BASE_COUNT * N_FIBER,
        "public_quotient_erases_fiber": public_class_count == BASE_COUNT and public_class_size_ok,
        "frame_relative_future_probe_splits_public_classes": frame_split_classes == BASE_COUNT and frame_max_split == 3,
        "no_frame_control_does_not_split": no_frame_split_classes == 0 and no_frame_max_split == 1,
        "label_shuffle_preserves_public_quotient_but_not_frame_bins": label_shuffle_control,
    }
    all_tests = all(tests.values())
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "scratch_discriminator_only; not spinor admission; not physical freedom; not density-matrix necessity",
        "TOOL_INTEGRATION_DEPTH": "jax_vectorized_fixture",
        "source_target": "Levos packet sim_targets/spinor_quotient_freedom_discriminator_v0.md",
        "representation": "jax_integer_carrier_vectorized_phase_bins",
        "package_versions": {"jax": jax.__version__},
        "carrier": {"base_count": BASE_COUNT, "fiber_phase_count": N_FIBER, "state_count": int(rows.shape[0])},
        "quotients": {
            "public_class_count": public_class_count,
            "public_class_size": int(public_counts[0]),
            "frame_probe_bins_by_public_class": frame_rows,
            "no_frame_bins_by_public_class": no_frame_rows,
        },
        "tests": tests,
        "all_tests_pass": all_tests,
        "TOOL_MANIFEST": {"jax": {"used": True, "reason": "independent vectorized finite carrier, public quotient, frame/no-frame probes"}},
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} public_classes={public_class_count} frame_split_classes={frame_split_classes} no_frame_split={no_frame_split_classes}")
    return 0 if all_tests else 1


if __name__ == "__main__":
    raise SystemExit(main())
