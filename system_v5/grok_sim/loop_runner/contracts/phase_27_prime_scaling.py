"""phase_27_prime_scaling.py — does the prime resonance signal persist at larger n?

Phase 98 established z > 2σ prime/composite clustering for n in [2..16] via Euler
totient φ(n)-indexed engine traversal. CRITICAL TEST: does the signal persist at
n in [17..50] where φ(n)/n flattens toward the Mertens asymptote 6/π² ≈ 0.608?

If YES: the architecture genuinely encodes a primality signal beyond small-n luck.
If NO: the finding is bounded to small n — still publishable, but not a deep claim.

We re-use the candidate's `prime_resonance(n)` API. Same checks as phase_98 but on
the extended range, with a stricter z ≥ 1.5σ threshold (signal may weaken but should
not disappear into noise).
"""
import math
import numpy as np


def _is_prime(n):
    if n < 2:
        return False
    for d in range(2, int(math.isqrt(n)) + 1):
        if n % d == 0:
            return False
    return True


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "prime_resonance"):
        return {
            "pass": False,
            "failures": [{"check": "prime_resonance_exists",
                          "msg": "Required by Phase 98; must extend cleanly to n=17..50."}],
            "metrics": metrics,
        }

    test_range = list(range(17, 51))
    signatures = {}
    for n in test_range:
        try:
            r = candidate.prime_resonance(n)
            sig = np.asarray(r["signature_vector"], dtype=float)
            signatures[n] = sig
        except Exception as e:
            failures.append({"check": f"call_n_{n}", "msg": str(e)[:200]})

    if len(signatures) < len(test_range) * 0.9:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": f"only {len(signatures)}/{len(test_range)} ns succeeded"}
        ], "metrics": metrics}

    # Distinct signatures
    distinct_n = len({tuple(round(float(x), 4) for x in signatures[n]) for n in signatures})
    metrics["distinct_signatures"] = distinct_n
    metrics["total_signatures"] = len(signatures)
    if distinct_n < len(signatures) * 0.7:
        failures.append({
            "check": "signatures_distinct_scaled",
            "msg": f"Only {distinct_n}/{len(signatures)} distinct at n=17..50 — hash collapse at scale.",
        })

    primes_in_range = [n for n in signatures if _is_prime(n)]
    composites_in_range = [n for n in signatures if not _is_prime(n)]
    metrics["primes_in_range"] = primes_in_range
    metrics["composites_in_range"] = composites_in_range
    metrics["num_primes"] = len(primes_in_range)
    metrics["num_composites"] = len(composites_in_range)

    pp_dists = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for i, a in enumerate(primes_in_range) for b in primes_in_range[i + 1:]]
    pc_dists = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for a in primes_in_range for b in composites_in_range]

    if not pp_dists or not pc_dists:
        return {"pass": False, "failures": failures + [
            {"check": "insufficient_pairs", "msg": "no pp/pc pairs at scale"}
        ], "metrics": metrics}

    avg_pp = sum(pp_dists) / len(pp_dists)
    avg_pc = sum(pc_dists) / len(pc_dists)
    ratio = avg_pc / max(avg_pp, 1e-9)
    metrics["avg_prime_prime_distance"] = avg_pp
    metrics["avg_prime_composite_distance"] = avg_pc
    metrics["cluster_advantage_ratio"] = ratio

    # Null distribution from random labels
    import random
    rng = random.Random(2026)
    all_ns = primes_in_range + composites_in_range
    null_ratios = []
    for _ in range(200):
        shuffled = list(all_ns)
        rng.shuffle(shuffled)
        fp = shuffled[:len(primes_in_range)]
        fc = shuffled[len(primes_in_range):]
        pp_f = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for i, a in enumerate(fp) for b in fp[i + 1:]]
        pc_f = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for a in fp for b in fc]
        if pp_f and pc_f:
            null_ratios.append((sum(pc_f)/len(pc_f)) / max(sum(pp_f)/len(pp_f), 1e-9))
    null_mean = sum(null_ratios) / len(null_ratios)
    null_std = (sum((x - null_mean) ** 2 for x in null_ratios) / len(null_ratios)) ** 0.5
    z_score = (ratio - null_mean) / max(null_std, 1e-9)
    metrics["null_mean"] = null_mean
    metrics["null_std"] = null_std
    metrics["z_score_vs_random"] = z_score

    # Slightly relaxed threshold at scale (signal may weaken in Mertens regime)
    if z_score < 1.5:
        failures.append({
            "check": "prime_signal_persists_at_scale",
            "msg": f"At n=17..50, prime cluster ratio={ratio:.4f}; null {null_mean:.4f}±{null_std:.4f}; "
                   f"z={z_score:.2f}σ (need ≥1.5σ). Signal collapses in the Mertens regime where "
                   f"φ(n)/n → 6/π² ≈ 0.608. The architecture's prime signature is small-n only.",
        })

    # Cross-check: top-k nearest neighbors of primes should be enriched for primes
    prime_neighbor_hits = 0
    total_checks = 0
    for p in primes_in_range:
        dists = sorted(
            [(n, float(np.linalg.norm(signatures[p] - signatures[n]))) for n in signatures if n != p],
            key=lambda kv: kv[1],
        )
        k = max(1, len(primes_in_range) - 1)
        topk = [n for n, _ in dists[:k]]
        prime_neighbor_hits += sum(1 for n in topk if _is_prime(n))
        total_checks += k
    if total_checks > 0:
        enrichment = prime_neighbor_hits / total_checks
        baseline = len(primes_in_range) / (len(signatures) - 1)
        metrics["knn_prime_enrichment"] = enrichment
        metrics["knn_prime_baseline"] = baseline
        metrics["knn_enrichment_lift"] = enrichment - baseline
        if enrichment - baseline < 0.05:
            failures.append({
                "check": "knn_prime_enrichment",
                "msg": f"k-NN prime enrichment {enrichment:.3f} barely above chance {baseline:.3f} "
                       f"(lift {enrichment-baseline:+.3f}); prime cluster geometry too weak at scale.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "small-n-only signal — passes Phase 98, fails at n=17..50",
            "noise-floor signature at scale — z drops below 1.5σ",
            "uniform-random signature — knn enrichment ≈ baseline",
        ],
        "baseline_variants": [
            "constant signature at scale — fails distinct + knn",
            "φ(n)/n scalar embedding — passes ratio test trivially but knn-lift may still be small",
        ],
    }
