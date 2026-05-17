"""phase_29_prime_scaling_extreme.py — does prime signal persist at n ∈ [50, 200]?

Phase 27 established z ≥ 1.5σ at n ∈ [17, 50]. Phase 29 pushes harder:
  - Range: n ∈ [50, 200] (150 integers, includes Mertens regime fully)
  - Threshold: z ≥ 2.0σ (stricter than Phase 27's 1.5σ)
  - k-NN enrichment lift ≥ 0.07 (stricter than Phase 27's 0.05)
  - Distinct signatures ≥ 60% (relaxed from 70% — some hash collapse expected
    at high n is acceptable, but not total)

If this passes, the architecture's prime encoding is verified across a 100-fold
range of n. If it fails, the side-quest finding is bounded at n ≲ 50.
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
        return {"pass": False,
                "failures": [{"check": "prime_resonance_exists", "msg": "see Phase 98."}],
                "metrics": metrics}

    test_range = list(range(50, 201))
    signatures = {}
    for n in test_range:
        try:
            r = candidate.prime_resonance(n)
            sig = np.asarray(r["signature_vector"], dtype=float)
            signatures[n] = sig
        except Exception as e:
            failures.append({"check": f"call_n_{n}", "msg": str(e)[:160]})

    if len(signatures) < len(test_range) * 0.9:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": f"only {len(signatures)}/{len(test_range)} ns succeeded"}
        ], "metrics": metrics}

    distinct_n = len({tuple(round(float(x), 4) for x in signatures[n]) for n in signatures})
    metrics["distinct_signatures"] = distinct_n
    metrics["total_signatures"] = len(signatures)
    if distinct_n < len(signatures) * 0.6:
        failures.append({"check": "signatures_distinct_extreme",
                         "msg": f"only {distinct_n}/{len(signatures)} distinct at n=50..200."})

    primes = [n for n in signatures if _is_prime(n)]
    composites = [n for n in signatures if not _is_prime(n)]
    metrics["num_primes"] = len(primes)
    metrics["num_composites"] = len(composites)

    pp = [float(np.linalg.norm(signatures[a] - signatures[b]))
          for i, a in enumerate(primes) for b in primes[i + 1:]]
    pc = [float(np.linalg.norm(signatures[a] - signatures[b]))
          for a in primes for b in composites]

    if not pp or not pc:
        return {"pass": False, "failures": failures + [
            {"check": "insufficient_pairs", "msg": "no pp/pc pairs"}
        ], "metrics": metrics}

    avg_pp = sum(pp) / len(pp)
    avg_pc = sum(pc) / len(pc)
    ratio = avg_pc / max(avg_pp, 1e-9)
    metrics["avg_prime_prime_distance"] = avg_pp
    metrics["avg_prime_composite_distance"] = avg_pc
    metrics["cluster_advantage_ratio"] = ratio

    # Null distribution
    import random
    rng = random.Random(20260513)
    all_ns = primes + composites
    null_ratios = []
    for _ in range(300):
        shuf = list(all_ns)
        rng.shuffle(shuf)
        fp = shuf[:len(primes)]
        fc = shuf[len(primes):]
        pp_f = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for i, a in enumerate(fp) for b in fp[i + 1:]]
        pc_f = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for a in fp for b in fc]
        if pp_f and pc_f:
            null_ratios.append((sum(pc_f)/len(pc_f)) / max(sum(pp_f)/len(pp_f), 1e-9))
    null_mean = sum(null_ratios) / len(null_ratios)
    null_std = (sum((x - null_mean) ** 2 for x in null_ratios) / len(null_ratios)) ** 0.5
    z = (ratio - null_mean) / max(null_std, 1e-9)
    metrics["null_mean"] = null_mean
    metrics["null_std"] = null_std
    metrics["z_score_vs_random"] = z

    if z < 2.0:
        failures.append({
            "check": "prime_signal_extreme",
            "msg": f"At n=50..200, ratio={ratio:.4f} vs null {null_mean:.4f}±{null_std:.4f}; "
                   f"z={z:.2f}σ (need ≥2.0σ). Signal does not persist at the 100x scale.",
        })

    # k-NN enrichment
    hits = 0
    total = 0
    for p in primes:
        dists = sorted(
            [(n, float(np.linalg.norm(signatures[p] - signatures[n])))
             for n in signatures if n != p],
            key=lambda kv: kv[1])
        k = max(1, len(primes) - 1)
        topk = [n for n, _ in dists[:k]]
        hits += sum(1 for n in topk if _is_prime(n))
        total += k
    if total > 0:
        enrich = hits / total
        baseline = len(primes) / (len(signatures) - 1)
        lift = enrich - baseline
        metrics["knn_prime_enrichment"] = enrich
        metrics["knn_prime_baseline"] = baseline
        metrics["knn_enrichment_lift"] = lift
        if lift < 0.07:
            failures.append({
                "check": "knn_extreme_enrichment",
                "msg": f"k-NN prime enrichment {enrich:.3f} above baseline {baseline:.3f} "
                       f"by only {lift:+.3f}; geometry too weak at extreme scale.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "small-n-only signal — passes Phase 98, 27; fails Phase 29",
            "saturated carrier — 4-qubit Hilbert too small at n=200",
            "feature-engineering artifact — passes by leakage of φ(n)/n, not architecture",
        ],
        "baseline_variants": [
            "φ(n)/n scalar embedding — passes ratio test trivially via Mertens divergence",
            "is_prime() lookup with noise — would pass perfectly but is the obvious cheat",
        ],
    }
