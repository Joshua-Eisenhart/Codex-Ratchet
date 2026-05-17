"""phase_41_factorization_attempt.py — can the architecture FACTOR composites?

The architecture detects primes (Phase 27/29/40). Does it also encode factorization
structure? For each composite n with smallest prime factor p, is signature(n) more
similar to signature(p) than to other primes?

Test: for each composite n in 4..50 with smallest prime factor p:
  - Compute sig(n), sig(p), and sig(q) for all other primes q ≤ sqrt(n)
  - Score: nearest prime by L2 distance from sig(n)
  - Correct if nearest prime is p

Expected: chance ≈ 1/π(sqrt(50)) ≈ 1/4 for n≤50 (4 primes ≤ 7). If accuracy is
≥ 0.40 (well above 25% chance), architecture encodes some factorization. If
≈ 0.25, the prime signal is detection-only.

This is a designed-to-likely-fail test. Honest research-negative is the expected
outcome; passing would be a major surprise.
"""
import math
import numpy as np


def _is_prime(n):
    if n < 2: return False
    for d in range(2, int(math.isqrt(n)) + 1):
        if n % d == 0: return False
    return True


def _smallest_prime_factor(n):
    for d in range(2, int(math.isqrt(n)) + 1):
        if n % d == 0:
            return d
    return n


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "prime_resonance"):
        return {"pass": False, "failures": [
            {"check": "prime_resonance_exists", "msg": "see Phase 98"}], "metrics": metrics}

    # Cache signatures
    sigs = {}
    for n in range(2, 51):
        try:
            sigs[n] = np.asarray(
                candidate.prime_resonance(n)["signature_vector"], dtype=float)
        except Exception as e:
            failures.append({"check": f"sig_{n}", "msg": str(e)[:80]})

    composites = [n for n in range(4, 51) if not _is_prime(n)]
    correct = 0
    total = 0
    chance_baseline = 0.0  # accumulate per-composite chance
    for n in composites:
        if n not in sigs: continue
        p_true = _smallest_prime_factor(n)
        candidates = [q for q in range(2, int(math.isqrt(n)) + 1) if _is_prime(q) and q in sigs]
        if not candidates: continue
        # Score by L2 distance from sig(n)
        dists = [(q, float(np.linalg.norm(sigs[n] - sigs[q]))) for q in candidates]
        dists.sort(key=lambda kv: kv[1])
        nearest = dists[0][0]
        total += 1
        if nearest == p_true:
            correct += 1
        chance_baseline += 1.0 / len(candidates)

    if total == 0:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": "no composites scored"}], "metrics": metrics}

    accuracy = correct / total
    chance = chance_baseline / total
    metrics["factorization_accuracy"] = accuracy
    metrics["chance_baseline"] = chance
    metrics["correct"] = correct
    metrics["total"] = total
    metrics["lift_over_chance"] = accuracy - chance

    # Pass if accuracy is ≥ 40% AND well above chance
    if accuracy < 0.40 or (accuracy - chance) < 0.10:
        failures.append({
            "check": "factorization_encoded",
            "msg": f"factorization accuracy {accuracy:.1%} vs chance {chance:.1%} "
                   f"(lift {accuracy-chance:+.3f}). Architecture detects primes but does NOT "
                   f"encode factorization structure. This is the expected bound: the prime "
                   f"signal is detection-only.",
        })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "chance-level factorization — fails as expected (detection-only)",
            "above-chance factorization — would be a major surprise",
        ],
        "baseline_variants": [
            "trial-division baseline (cheating) — would pass at 100%",
            "random-pick baseline — passes at chance",
        ],
    }
