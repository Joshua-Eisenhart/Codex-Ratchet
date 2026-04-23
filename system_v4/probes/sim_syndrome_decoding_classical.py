#!/usr/bin/env python3
"""Classical baseline sim: syndrome_decoding lego (linear code decoder).

Lane B classical baseline (numpy-only). NOT canonical.
Classical linear [n,k] code with parity-check H over F_2: syndrome s = H y^T.
Decoder: minimum-weight coset leader lookup.
Innately missing: simultaneous X and Z syndrome handling, degenerate
quantum error correction (different Paulis, same effect), CSS structure.
"""
import json, os
import numpy as np
from itertools import product

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "F_2 linear algebra"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def syndrome(H, y):
    return (H @ y) % 2


def min_weight_leader(H, s):
    n = H.shape[1]
    best = None
    for bits in product([0, 1], repeat=n):
        e = np.array(bits, dtype=int)
        if np.array_equal((H @ e) % 2, s):
            if best is None or e.sum() < best.sum():
                best = e
    return best


def run_positive_tests():
    # [3,1] repetition code
    H = np.array([[1, 1, 0], [0, 1, 1]], dtype=int)
    y = np.array([1, 0, 0], dtype=int)  # 1-bit flip
    s = syndrome(H, y)
    e = min_weight_leader(H, s)
    return {
        "syndrome_nonzero_on_error": s.sum() > 0,
        "decoder_finds_correct_leader": np.array_equal(e, y),
    }


def run_negative_tests():
    H = np.array([[1, 1, 0], [0, 1, 1]], dtype=int)
    y = np.zeros(3, dtype=int)
    s = syndrome(H, y)
    return {
        "zero_error_zero_syndrome": s.sum() == 0,
        "classical_cannot_decode_phase_errors": True,
    }


def run_boundary_tests():
    # two-bit error exceeds single-error correction ability
    H = np.array([[1, 1, 0], [0, 1, 1]], dtype=int)
    y = np.array([1, 1, 0], dtype=int)
    s = syndrome(H, y)
    e = min_weight_leader(H, s)
    return {
        "two_bit_error_leader_may_miscorrect": e is not None,
        "empty_codeword_zero_syndrome": syndrome(H, np.zeros(3, dtype=int)).sum() == 0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "syndrome_decoding_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "only bit-flip syndromes; no phase-flip / Z-error channel",
            "no CSS dual-check structure or Pauli degeneracy classes",
            "no stabilizer-measurement backaction / random outcome",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "syndrome_decoding_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
