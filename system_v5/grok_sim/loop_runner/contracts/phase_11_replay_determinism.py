"""phase_11_replay_determinism.py — full engine replay must produce identical per-stage records.

Phase 07 verified summary values (cycle_closure_a, cross_engine_observable) are
deterministic across two run_engine() calls. This phase verifies the FULL per-stage
records are identical across runs — each stage's (obs, entropy) must match within tolerance.

This catches:
  - Random initialization in engine evolution (Grok adding randn for "diversity")
  - Non-deterministic ordering of stage operations
  - Floating-point non-associativity drift exceeding tolerance

Tolerance: 1e-6 per per-stage observable/entropy value. Sum-of-absolute-differences
across all 64 stage records must stay below 64 * 1e-6 = 6.4e-5.
"""

PER_STAGE_TOL = 1e-6
TOTAL_TOL = 64 * PER_STAGE_TOL


def _diff_records(records_a, records_b, label):
    failures = []
    metrics = {}
    if len(records_a) != len(records_b):
        return [{"check": f"engine_{label}_record_count_match",
                 "msg": f"two runs returned {len(records_a)} vs {len(records_b)} stage records"}], {}
    total_diff = 0.0
    per_stage_max = 0.0
    for i, (a, b) in enumerate(zip(records_a, records_b)):
        for field in ("obs", "entropy"):
            if field not in a or field not in b:
                failures.append({
                    "check": f"engine_{label}_field_{field}_present",
                    "msg": f"stage {i} missing `{field}` field in at least one of two runs",
                })
                continue
            d = abs(float(a[field]) - float(b[field]))
            total_diff += d
            per_stage_max = max(per_stage_max, d)
    metrics[f"{label}_total_abs_diff"] = total_diff
    metrics[f"{label}_max_per_stage_diff"] = per_stage_max

    if per_stage_max > PER_STAGE_TOL:
        failures.append({
            "check": f"engine_{label}_per_stage_deterministic",
            "msg": f"Engine {label}: max per-stage |Δ| = {per_stage_max:.2e} across two runs, "
                   f"exceeds {PER_STAGE_TOL:.2e}. Indicates non-deterministic evolution "
                   f"(random initialization in stage operators, or floating-point drift > tolerance).",
        })
    if total_diff > TOTAL_TOL:
        failures.append({
            "check": f"engine_{label}_total_deterministic",
            "msg": f"Engine {label}: total absolute drift = {total_diff:.2e} across 32 stages, "
                   f"exceeds {TOTAL_TOL:.2e}. Cumulative non-determinism.",
        })
    return failures, metrics


def run(candidate):
    failures = []
    metrics = {}

    try:
        r1 = candidate.run_engine()
        r2 = candidate.run_engine()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "run_engine_two_calls",
                          "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}],
            "metrics": metrics,
        }

    for label, key in [("A", "engine_a_stage_records"), ("B", "engine_b_stage_records")]:
        rec1 = r1.get(key, [])
        rec2 = r2.get(key, [])
        f, m = _diff_records(rec1, rec2, label)
        failures.extend(f)
        metrics.update(m)

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "Engine using torch.randn / np.random in stage construction — fails determinism",
            "Engine reading from a global mutable counter — fails first/second call mismatch",
            "Engine using uninitialized memory — fails large total_diff",
        ],
        "baseline_variants": [
            "explicit-RNG-without-seed baseline — must fail",
            "explicit-RNG-with-fixed-seed baseline — should pass",
        ],
    }
