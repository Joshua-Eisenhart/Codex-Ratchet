"""phase_40_prime_chain_wide.py — does the prime-classifier chain hold at n=2..100?

Phase 39 showed 68.97% accuracy on n=2..30. Phase 40 tests whether the chain
holds at 3× the range AND across the prime_resonance regime transition (small-n
mod-7 vs large-n gated globals).

Range: n=2..100 (99 ns)
Pass: best mapping accuracy ≥ 60%
Stricter: ≥ 65% across the full range (allowing some degradation from 69%)

This is the cleanest scaling test for chained composability.
"""
import math
import numpy as np


def _is_prime(n):
    if n < 2: return False
    for d in range(2, int(math.isqrt(n)) + 1):
        if n % d == 0: return False
    return True


def run(candidate):
    failures = []
    metrics = {}

    needs = ["prime_resonance", "classify_state", "signature_to_density_matrix"]
    for fn in needs:
        if not hasattr(candidate, fn):
            return {"pass": False, "failures": [
                {"check": f"{fn}_exists", "msg": "see Phase 39"}], "metrics": metrics}

    test_ns = list(range(2, 101))
    primes = [n for n in test_ns if _is_prime(n)]
    composites = [n for n in test_ns if not _is_prime(n)]
    metrics["n_primes"] = len(primes)
    metrics["n_composites"] = len(composites)
    metrics["range"] = [2, 100]

    labels = {}
    for n in test_ns:
        try:
            sig = candidate.prime_resonance(n)["signature_vector"]
            rho = candidate.signature_to_density_matrix(sig)
            labels[n] = candidate.classify_state(rho).get("engine_label")
        except Exception as e:
            failures.append({"check": f"chain_{n}", "msg": str(e)[:80]})

    if len(labels) < len(test_ns) * 0.9:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": f"{len(labels)}/{len(test_ns)} ns succeeded"}
        ], "metrics": metrics}

    prime_a = sum(1 for n in primes if labels.get(n) == "A")
    prime_b = sum(1 for n in primes if labels.get(n) == "B")
    comp_a = sum(1 for n in composites if labels.get(n) == "A")
    comp_b = sum(1 for n in composites if labels.get(n) == "B")
    metrics["prime_labels"] = {"A": prime_a, "B": prime_b, "n": len(primes)}
    metrics["composite_labels"] = {"A": comp_a, "B": comp_b, "n": len(composites)}

    map_AA = (prime_a + comp_b) / (len(primes) + len(composites))
    map_BB = (prime_b + comp_a) / (len(primes) + len(composites))
    best = max(map_AA, map_BB)
    metrics["best_mapping_accuracy"] = best
    metrics["mapping_choice"] = "primes_to_A" if map_AA >= map_BB else "primes_to_B"

    # Split by regime: small-n (≤16, pure mod-7 hash) vs large-n (>16, gated globals)
    small_ns = [n for n in test_ns if n <= 16 and n in labels]
    large_ns = [n for n in test_ns if n > 16 and n in labels]
    def _acc(ns, mapping):
        a_to_prime, b_to_prime = (mapping == "primes_to_A"), (mapping == "primes_to_B")
        correct = 0
        for n in ns:
            is_p = _is_prime(n)
            if labels.get(n) == "A":
                if (is_p and a_to_prime) or (not is_p and b_to_prime):
                    correct += 1
            elif labels.get(n) == "B":
                if (is_p and b_to_prime) or (not is_p and a_to_prime):
                    correct += 1
        return correct / max(len(ns), 1)
    mapping = "primes_to_A" if map_AA >= map_BB else "primes_to_B"
    metrics["small_n_accuracy"] = _acc(small_ns, mapping)
    metrics["large_n_accuracy"] = _acc(large_ns, mapping)

    if best < 0.60:
        failures.append({"check": "chain_at_scale",
                         "msg": f"best mapping {best:.1%} < 60% on n=2..100. Chain doesn't scale."})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "chain works only at n≤16 — small-n accuracy high, large-n accuracy ≈ 50%",
            "chain fails entirely past gated-globals threshold — accuracy crashes at n=17",
        ],
        "baseline_variants": [
            "φ(n)/n direct embed baseline — would pass chain test trivially",
        ],
    }
