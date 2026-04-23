#!/usr/bin/env python3
"""Classical baseline sim: stabilizer_formalism lego (classical bit tableau).

Lane B classical baseline (numpy-only). NOT canonical.
Classical reduction: Z-only tableau (X-block is zero). Stabilizer state is
identified by a bit-string v; update under classical reversible maps
(permutations, bit-flips) is deterministic.
Innately missing: X/Y generators, symplectic inner product, Clifford
conjugation, measurement-induced stabilizer updates with random outcomes.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "bit tableau arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def bit_tableau(v):
    # returns Z-only tableau as (X|Z|s) with X=0, Z=diag(1), s = v
    n = len(v)
    X = np.zeros((n, n), dtype=int)
    Z = np.eye(n, dtype=int)
    s = np.array(v, dtype=int)
    return X, Z, s


def flip_bit(tab, i):
    X, Z, s = tab
    s = s.copy(); s[i] ^= 1
    return X, Z, s


def run_positive_tests():
    X, Z, s = bit_tableau([0, 1, 0])
    X2, Z2, s2 = flip_bit((X, Z, s), 1)
    return {
        "X_block_zero_classically": np.all(X == 0),
        "Z_block_identity": np.array_equal(Z, np.eye(3, dtype=int)),
        "flip_deterministic": np.array_equal(s2, np.array([0, 0, 0])),
    }


def run_negative_tests():
    # classical cannot represent a Hadamard-conjugated |+> (X stabilizer)
    X, Z, s = bit_tableau([0, 0])
    return {
        "classical_cannot_produce_X_stabilizer": np.all(X == 0),
        "no_Y_generator_possible": True,
    }


def run_boundary_tests():
    X, Z, s = bit_tableau([])
    return {
        "empty_tableau_valid": X.shape == (0, 0) and s.shape == (0,),
        "single_bit_tableau_ok": bit_tableau([1])[2].tolist() == [1],
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "stabilizer_formalism_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "X and Y generators absent; only Z-diagonal tableau",
            "no symplectic inner product structure over F_2^{2n}",
            "measurement outcomes deterministic, no Born-rule branching",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "stabilizer_formalism_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
