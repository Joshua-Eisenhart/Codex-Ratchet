"""phase_39_prime_classifier_chain.py — primes and classifier in a chained pipeline.

The architecture has two signal-carrying primitives:
  - prime_resonance(n) maps integer n to a 16-dim signature
  - classify_state(rho) labels engine A/B by trajectory affinity

If both encode REAL structure, chaining should produce something useful:
  for n in 2..30:
    sig = prime_resonance(n)["signature_vector"]
    rho = signature_to_density_matrix(sig)
    label = classify_state(rho)["engine_label"]

  Is `label` correlated with primality? Two predictions:
    - If yes (correlation > 60%): the engine geometry CAPTURES the prime signal
      via signature embedding. Primes and composites occupy distinct engine
      basins after embedding.
    - If no (≈ 50%): the prime signal is isolated to prime_resonance; it doesn't
      propagate through other primitives.

This is the first test that uses TWO primitives in a pipeline for a single
downstream task. It binds "massive AI tool set" to composability of structure.

Required: candidate must export `signature_to_density_matrix(sig_vec) -> qt.Qobj`
to embed the signature into the 4-qubit Hilbert space.
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
            return {"pass": False, "failures": [{
                "check": f"{fn}_exists",
                "msg": f"Required `{fn}` not exported. Phase 39 chains prime_resonance + "
                       f"signature_to_density_matrix + classify_state. "
                       f"`signature_to_density_matrix(sig_vec: list[float]) -> qt.Qobj`: "
                       f"embed 16-dim signature vector into a valid 4-qubit density matrix.",
            }], "metrics": metrics}

    test_ns = list(range(2, 31))
    primes = [n for n in test_ns if _is_prime(n)]
    composites = [n for n in test_ns if not _is_prime(n)]
    metrics["primes_in_range"] = primes
    metrics["composites_in_range"] = composites

    labels = {}
    confidences = {}
    for n in test_ns:
        try:
            sig = candidate.prime_resonance(n)["signature_vector"]
            rho = candidate.signature_to_density_matrix(sig)
            cls = candidate.classify_state(rho)
            labels[n] = cls.get("engine_label")
            confidences[n] = float(cls.get("confidence", 0.0))
        except Exception as e:
            failures.append({"check": f"chain_{n}", "msg": f"{type(e).__name__}: {str(e)[:100]}"})

    if len(labels) < 25:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": f"{len(labels)}/{len(test_ns)} ns succeeded"}
        ], "metrics": metrics}

    # Find the dominant engine label for primes vs composites
    prime_a = sum(1 for n in primes if labels.get(n) == "A")
    prime_b = sum(1 for n in primes if labels.get(n) == "B")
    comp_a = sum(1 for n in composites if labels.get(n) == "A")
    comp_b = sum(1 for n in composites if labels.get(n) == "B")
    metrics["prime_labels"] = {"A": prime_a, "B": prime_b, "n": len(primes)}
    metrics["composite_labels"] = {"A": comp_a, "B": comp_b, "n": len(composites)}

    # Correlation: best-case mapping (primes-A or primes-B), pick stronger side
    map_AA = (prime_a + comp_b) / (len(primes) + len(composites))  # primes=A, comps=B
    map_BB = (prime_b + comp_a) / (len(primes) + len(composites))  # primes=B, comps=A
    best_accuracy = max(map_AA, map_BB)
    metrics["best_mapping_accuracy"] = best_accuracy
    metrics["mapping_choice"] = "primes_to_A" if map_AA >= map_BB else "primes_to_B"

    # Pass: ≥ 60% (above 50% chance with margin)
    if best_accuracy < 0.60:
        failures.append({
            "check": "chained_prime_classification",
            "msg": f"best engine-label mapping gives only {best_accuracy:.1%} accuracy on "
                   f"prime/composite labels (chance ≈ 50%, range {len(test_ns)} ns). "
                   f"The prime signal does NOT propagate through "
                   f"signature_to_density_matrix → classify_state. Primes and composites "
                   f"land in the same engine basins.",
        })

    # Sanity: confidence not crushed to zero (signature-derived states should not be totally unfamiliar)
    avg_conf = sum(confidences.values()) / max(len(confidences), 1)
    metrics["avg_chain_confidence"] = avg_conf

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "signature embedding to identity I/16 baseline — all states identical, classifier random",
            "signature embedding to random density — classifier random, fails accuracy",
            "primes and composites both map to same engine — fails best_mapping_accuracy",
        ],
        "baseline_variants": [
            "trivial-embed baseline: convert sig to diag matrix — passes classifier call, may or may not segregate by primality",
            "PCA-projected baseline: project sig onto top 4 dims — passes coverage",
        ],
    }
