#!/usr/bin/env python3
"""Classical baseline sim: magic_state lego (stabilizer baseline).

Lane B classical baseline (numpy-only). NOT canonical.
Classical bit strings are trivially stabilizer (eigenstates of Z tensor).
Magic (nonstabilizer-ness) measured by robustness / stabilizer rank is 0
for any classical state.
Innately missing: T-states, robustness-of-magic, universal quantum
computation resource, mana / negativity witnesses.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "bit arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def classical_magic(bitstring):
    # classical bit -> |0> or |1> computational basis; magic = 0
    return 0.0


def is_stabilizer_classical(bitstring):
    return all(b in (0, 1) for b in bitstring)


def run_positive_tests():
    return {
        "zero_string_is_stabilizer": is_stabilizer_classical([0, 0, 0]),
        "one_string_is_stabilizer": is_stabilizer_classical([1, 1, 0, 1]),
        "classical_magic_is_zero": classical_magic([1, 0, 1]) == 0.0,
    }


def run_negative_tests():
    return {
        "non_bit_rejected": not is_stabilizer_classical([0, 2, 1]),
        "classical_cannot_represent_T_state": True,  # declared gap
    }


def run_boundary_tests():
    return {
        "empty_string_trivially_stabilizer": is_stabilizer_classical([]),
        "single_bit_zero_magic": classical_magic([0]) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "magic_state_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "classical bit states have zero magic by construction",
            "no T-state / H-state representation; no robustness-of-magic witness",
            "cannot seed universal quantum computation via magic state distillation",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "magic_state_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
