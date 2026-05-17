"""phase_42_factorization_wide.py — does the factorization signal hold at n=51..200?

Phase 41 surprised by passing at n=4..50 with +11.8pp lift over chance (55.9% vs
44.1%). The chance baseline was high there because most composites had only 2-3
candidate primes. At n=51..200, more candidate primes per composite → stricter
chance baseline (~15-20%) → sharper test.

Pass: accuracy ≥ 25% AND lift over chance ≥ +5pp
Strict: lift ≥ +10pp (matching Phase 41's strength at the sharper scale)

If Phase 41's lift was a sample-size artifact, this will collapse to chance.
If the architecture genuinely encodes multiplicative geometry, the lift survives.
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

    sigs = {}
    for n in range(2, 201):
        try:
            sigs[n] = np.asarray(
                candidate.prime_resonance(n)["signature_vector"], dtype=float)
        except Exception as e:
            failures.append({"check": f"sig_{n}", "msg": str(e)[:60]})

    composites = [n for n in range(51, 201) if not _is_prime(n)]
    correct = 0
    total = 0
    chance_sum = 0.0
    for n in composites:
        if n not in sigs: continue
        p_true = _smallest_prime_factor(n)
        candidates = [q for q in range(2, int(math.isqrt(n)) + 1)
                      if _is_prime(q) and q in sigs]
        if not candidates: continue
        dists = [(q, float(np.linalg.norm(sigs[n] - sigs[q]))) for q in candidates]
        dists.sort(key=lambda kv: kv[1])
        nearest = dists[0][0]
        total += 1
        if nearest == p_true:
            correct += 1
        chance_sum += 1.0 / len(candidates)

    if total == 0:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": "no composites scored"}], "metrics": metrics}

    accuracy = correct / total
    chance = chance_sum / total
    lift = accuracy - chance
    metrics["factorization_accuracy"] = accuracy
    metrics["chance_baseline"] = chance
    metrics["lift_over_chance"] = lift
    metrics["correct"] = correct
    metrics["total"] = total

    if accuracy < 0.25 or lift < 0.05:
        failures.append({
            "check": "factorization_persists",
            "msg": f"at n=51..200: accuracy {accuracy:.1%} vs chance {chance:.1%}, lift "
                   f"{lift:+.3f}. Phase 41's signal was sample-size dependent — the "
                   f"factorization geometry collapses at larger scale.",
        })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "chance-level at scale — Phase 41 was a small-n artifact",
            "lift survives at scale — factorization geometry is real",
        ],
        "baseline_variants": [
            "trial division (cheating) — 100% but not architecture-derived",
        ],
    }
