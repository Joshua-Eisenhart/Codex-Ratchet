#!/usr/bin/env python3
"""spinor_quotient_freedom_discriminator_v0 -- exact finite discriminator.

Levos target claim:
  Public vector/density readouts erase live distinctions that may be freedom-relevant.
  A spinor/lifted carrier is admitted only when quotient-erased distinctions are
  load-bearing.

This exact leg builds a finite model of a Hopf-style quotient:
  carrier rows = (base_id, fiber_phase_index)
  public quotient = base_id only, representing the Bloch/projective/density-visible row
  lifted future probe = a frame-relative phase probe cos(phi - theta)

The test is conditional and fenced:
  - public quotient merges fiber phases;
  - a frame-relative future probe splits some merged classes;
  - a no-frame control cannot split them;
  - the result does NOT admit spinor/lift generally; it only shows when a lifted
    frame probe is present, the quotient-erased fiber coordinate is load-bearing.
"""

from __future__ import annotations

import json
import math
import pathlib
from collections import defaultdict

SIM_ID = "spinor_quotient_freedom_discriminator_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT = HERE / "results" / f"{SIM_ID}_exact_results.json"

BASES = ("north", "equator_x", "equator_y", "south")
N_FIBER = 8
FRAME_THETA = 0.0


def states():
    return [(b, k) for b in BASES for k in range(N_FIBER)]


def public_key(state):
    b, _k = state
    return b


def fiber_phase(k):
    return 2.0 * math.pi * k / N_FIBER


def frame_probe_key(state):
    _b, k = state
    # Finite future probe row: sign of a frame-relative phase quadrature.
    # Three bins avoid fake precision: + / 0 / -.
    v = math.cos(fiber_phase(k) - FRAME_THETA)
    if v > 1e-9:
        return "+"
    if v < -1e-9:
        return "-"
    return "0"


def no_frame_key(state):
    # Without a phase reference / lifted frame, all fiber phases inside a public base remain invisible.
    return "unresolved"


def quotient(key_fn):
    groups = defaultdict(list)
    for s in states():
        groups[key_fn(s)].append(s)
    return groups


def split_counts(public_groups, future_key_fn):
    rows = {}
    split_classes = 0
    max_split = 0
    for base, group in public_groups.items():
        bins = defaultdict(list)
        for s in group:
            bins[future_key_fn(s)].append(s)
        rows[base] = {str(k): len(v) for k, v in sorted(bins.items())}
        if len(bins) > 1:
            split_classes += 1
        max_split = max(max_split, len(bins))
    return rows, split_classes, max_split


def label_shuffle_control():
    # Relabel fiber phases by a bijection k -> k+3 mod N. Public quotient counts are invariant;
    # frame-probe bins permute but do not disappear.
    public_before = {k: len(v) for k, v in quotient(public_key).items()}
    shuffled = [(b, (k + 3) % N_FIBER) for b, k in states()]
    groups = defaultdict(list)
    for b, k in shuffled:
        groups[b].append((b, k))
    public_after = {k: len(v) for k, v in groups.items()}
    split_after = 0
    for base, group in groups.items():
        bins = {frame_probe_key(s) for s in group}
        if len(bins) > 1:
            split_after += 1
    return public_before == public_after and split_after == len(BASES)


def main() -> int:
    S = states()
    public_groups = quotient(public_key)
    frame_rows, frame_split_classes, frame_max_split = split_counts(public_groups, frame_probe_key)
    no_frame_rows, no_frame_split_classes, no_frame_max_split = split_counts(public_groups, no_frame_key)

    tests = {
        "finite_carrier_exists": len(S) == len(BASES) * N_FIBER,
        "public_quotient_erases_fiber": len(public_groups) == len(BASES) and all(len(v) == N_FIBER for v in public_groups.values()),
        "frame_relative_future_probe_splits_public_classes": frame_split_classes == len(BASES) and frame_max_split == 3,
        "no_frame_control_does_not_split": no_frame_split_classes == 0 and no_frame_max_split == 1,
        "label_shuffle_preserves_public_quotient_but_not_frame_bins": label_shuffle_control(),
    }
    all_tests = all(tests.values())
    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "scratch_discriminator_only; not spinor admission; not physical freedom; not density-matrix necessity",
        "TOOL_INTEGRATION_DEPTH": "exact_finite_fixture",
        "source_target": "Levos packet sim_targets/spinor_quotient_freedom_discriminator_v0.md",
        "claim": "a lifted/frame-relative probe can make quotient-erased fiber distinctions load-bearing; absent such a probe, the public quotient remains sufficient",
        "carrier": {"base_count": len(BASES), "fiber_phase_count": N_FIBER, "state_count": len(S)},
        "quotients": {
            "public_class_count": len(public_groups),
            "public_class_size": N_FIBER,
            "frame_probe_bins_by_public_class": frame_rows,
            "no_frame_bins_by_public_class": no_frame_rows,
        },
        "tests": tests,
        "all_tests_pass": all_tests,
        "honest_scope": {
            "earns": "conditional discriminator: public quotient erases fiber phase; a named frame-relative future probe splits the erased fiber; no-frame control blocks the split",
            "does_not_earn": "general spinor admission, physical freedom, final Hopf/Weyl layer, density-matrix necessity, or any social/person/company/community claim",
        },
        "TOOL_MANIFEST": {"python_stdlib": {"used": True, "reason": "exact finite quotient classes and finite probe bins"}},
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} public_classes={len(public_groups)} frame_split_classes={frame_split_classes} no_frame_split={no_frame_split_classes}")
    return 0 if all_tests else 1


if __name__ == "__main__":
    raise SystemExit(main())
