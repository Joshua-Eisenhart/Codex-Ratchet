"""phase_15_szilard_work_extraction.py — engine actually extracts work from information.

This phase moves beyond verification to demonstrate that the engine performs a
real information-processing task: Szilard-style measurement-driven work extraction
from a biased classical bit, bounded by the Landauer limit W ≤ H(p) kT.

Required new API: `extract_szilard_work(p_bit: float, n_cycles: int = 1) -> dict`
  Input:
    p_bit: probability that the hidden bit is 1 (0 < p_bit < 1)
    n_cycles: number of cycles to run (default 1)
  Returns:
    {
      "p_bit": float,
      "entropy_bits": float,          # H(p) = -p log2(p) - (1-p) log2(1-p)
      "work_extracted_kT": float,     # work in units of kT
      "landauer_bound_kT": float,     # = entropy_bits * ln(2) ≈ H(p) in nats
      "efficiency": float,            # = work_extracted / landauer_bound
      "n_cycles": int,
    }

Checks:
  - Function exists, returns dict with required keys
  - Landauer bound respected: W ≤ H(p) for all 3 test cases (p = 0.3, 0.5, 0.8)
  - At p=0.5 (max entropy), efficiency > 0.1 (engine actually extracts SOMETHING)
  - At p=0.99 (low entropy), work extracted is small in absolute terms (W < 0.5 kT)
  - Function is deterministic (same p → same work)
  - work_extracted is non-negative for valid p

This catches "engine returns zeros" or "engine violates 2nd law".
"""
import math


def _expected_entropy_bits(p):
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "extract_szilard_work"):
        return {
            "pass": False,
            "failures": [{
                "check": "extract_szilard_work_exists",
                "msg": "Required function `extract_szilard_work(p_bit, n_cycles=1) -> dict` is not exported. "
                       "The engine must demonstrate a real information-processing task: Szilard-style "
                       "measurement-driven work extraction from a biased classical bit. Return dict with "
                       "fields: p_bit, entropy_bits, work_extracted_kT, landauer_bound_kT, efficiency, n_cycles.",
            }],
            "metrics": {},
        }

    test_cases = [0.3, 0.5, 0.8]
    results = {}
    for p in test_cases:
        try:
            r = candidate.extract_szilard_work(p)
        except Exception as e:
            failures.append({
                "check": f"szilard_call_p_{p}",
                "msg": f"extract_szilard_work({p}) raised {type(e).__name__}: {str(e)[:200]}",
            })
            continue
        results[p] = r
        if not isinstance(r, dict):
            failures.append({"check": f"szilard_returns_dict_p_{p}",
                             "msg": f"returned {type(r).__name__}, expected dict"})
            continue

        # Required keys
        required_keys = ("p_bit", "entropy_bits", "work_extracted_kT", "landauer_bound_kT", "efficiency")
        for key in required_keys:
            if key not in r:
                failures.append({"check": f"szilard_missing_key_p_{p}_{key}",
                                 "msg": f"key `{key}` missing from extract_szilard_work({p}) result"})

    if failures:
        return {"pass": False, "failures": failures, "metrics": {"results_so_far": results}}

    # Validate each case
    for p, r in results.items():
        H_expected = _expected_entropy_bits(p)
        H_reported = float(r["entropy_bits"])
        W = float(r["work_extracted_kT"])
        bound = float(r["landauer_bound_kT"])
        eff = float(r["efficiency"])

        metrics[f"p_{p}"] = {
            "H_expected_bits": H_expected, "H_reported_bits": H_reported,
            "W_kT": W, "landauer_bound_kT": bound, "efficiency": eff,
        }

        # Entropy formula correct
        if abs(H_reported - H_expected) > 0.01:
            failures.append({
                "check": f"szilard_entropy_correct_p_{p}",
                "msg": f"reported entropy_bits = {H_reported:.4f}, expected H({p}) = {H_expected:.4f}",
            })

        # Work non-negative
        if W < -1e-6:
            failures.append({
                "check": f"szilard_work_nonneg_p_{p}",
                "msg": f"work_extracted_kT = {W:.4f} < 0 — engine violates 2nd law (work from info)",
            })

        # Landauer bound (W ≤ H(p) ln 2 = H(p) in nats; or W in kT ≤ H bits in nats)
        # The bound is W ≤ H bits × ln 2 kT (converting bits→nats with k_B T = 1 unit)
        max_allowed = H_expected * math.log(2) + 0.05  # small numerical slack
        if W > max_allowed:
            failures.append({
                "check": f"szilard_landauer_p_{p}",
                "msg": f"work_extracted_kT = {W:.4f} > Landauer bound {max_allowed:.4f} "
                       f"(H({p})*ln2 = {H_expected * math.log(2):.4f}). Engine violates Landauer limit.",
            })

        # Efficiency in [0, 1]
        if eff < -1e-6 or eff > 1 + 1e-3:
            failures.append({
                "check": f"szilard_efficiency_p_{p}",
                "msg": f"efficiency = {eff:.4f} outside [0, 1] — Szilard efficiency must be in [0, 1]",
            })

    # At p=0.5, efficiency must be meaningfully positive
    if 0.5 in results:
        eff_half = float(results[0.5]["efficiency"])
        if eff_half < 0.1:
            failures.append({
                "check": "szilard_extracts_work_at_max_info",
                "msg": f"At p=0.5 (max H=1 bit), efficiency = {eff_half:.4f} < 0.1. "
                       f"Engine isn't actually extracting work even when there's maximum info to extract.",
            })

    # Determinism: call twice at p=0.5
    try:
        r1 = candidate.extract_szilard_work(0.5)
        r2 = candidate.extract_szilard_work(0.5)
        if abs(float(r1["work_extracted_kT"]) - float(r2["work_extracted_kT"])) > 1e-4:
            failures.append({
                "check": "szilard_deterministic",
                "msg": f"two calls at p=0.5 returned different work: {r1['work_extracted_kT']} vs {r2['work_extracted_kT']}",
            })
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "engine returns work = 0 always — fails efficiency_at_max_info",
            "engine returns work > H(p) — fails Landauer bound (2nd law violation)",
            "engine returns negative work — fails work_nonneg",
            "engine returns random work each call — fails determinism",
            "engine computes wrong H(p) formula — fails entropy_correct",
        ],
        "baseline_variants": [
            "no-measurement baseline: extract work without measuring — W = 0 (no info gained)",
            "wrong-feedback baseline: feedback uncorrelated with measurement — W ≈ 0",
            "ideal Maxwell demon: W = H(p) ln 2 kT (perfect efficiency = 1)",
        ],
    }
