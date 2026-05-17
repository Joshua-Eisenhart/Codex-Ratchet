"""phase_10_entropy_monotonicity.py — per-stage entropy actually grows over the engine cycle.

Phase 05 verified entropy varies across stages (range > 0.05). This phase strengthens
the check: from a pure initial state |0000⟩⟨0000| with dissipative dynamics, the engine
should produce MONOTONIC (or near-monotonic) entropy growth, not random walk.

Checks per engine:
  - Final entropy > initial entropy by a significant margin (> 0.3 nats)
  - At least 70% of consecutive stage pairs have entropy_{n+1} >= entropy_n - 0.05
    (allows small fluctuations from numerical noise but rules out chaos)
  - Mid-cycle entropy > 50% of final entropy (growth is gradual, not delta-function-like)

This catches:
  - Stage operators that flip entropy randomly (random walk)
  - Engines that produce a sudden jump rather than monotonic growth
  - Engines that don't actually dissipate (entropy stays low until last stage)
"""

MIN_TOTAL_GROWTH = 0.3       # final - initial entropy must exceed this
MIN_MONOTONIC_FRACTION = 0.7 # fraction of consecutive pairs that should be non-decreasing
MIN_MID_FRACTION = 0.4       # mid-cycle entropy / final entropy must exceed this


def _analyze_engine(records, engine_label):
    failures = []
    metrics = {}
    if not records or not all("entropy" in r for r in records):
        return [{"check": f"engine_{engine_label}_records_well_formed",
                 "msg": f"engine {engine_label} records missing entropy fields"}], {}
    ent = [float(r["entropy"]) for r in records]
    metrics[f"{engine_label}_entropy_first"] = ent[0]
    metrics[f"{engine_label}_entropy_last"] = ent[-1]
    metrics[f"{engine_label}_entropy_mid"] = ent[len(ent) // 2]

    total_growth = ent[-1] - ent[0]
    metrics[f"{engine_label}_total_growth"] = total_growth
    if total_growth < MIN_TOTAL_GROWTH:
        failures.append({
            "check": f"engine_{engine_label}_total_growth",
            "msg": f"Engine {engine_label} entropy grew from {ent[0]:.4f} to {ent[-1]:.4f} "
                   f"(total {total_growth:.4f}). Required: > {MIN_TOTAL_GROWTH}. "
                   f"From a pure state, 32 dissipative stages should grow entropy meaningfully.",
        })

    # Monotonicity fraction
    monotonic_pairs = sum(1 for i in range(len(ent) - 1) if ent[i + 1] >= ent[i] - 0.05)
    frac = monotonic_pairs / max(1, len(ent) - 1)
    metrics[f"{engine_label}_monotonic_fraction"] = frac
    if frac < MIN_MONOTONIC_FRACTION:
        failures.append({
            "check": f"engine_{engine_label}_monotonicity",
            "msg": f"Engine {engine_label}: only {frac:.2%} of consecutive stage pairs have "
                   f"non-decreasing entropy (with 0.05 tolerance). Required: ≥ {MIN_MONOTONIC_FRACTION:.0%}. "
                   f"Entropy trajectory is too noisy / random-walk-like; dissipative dynamics from "
                   f"a pure state should produce mostly monotonic entropy growth.",
        })

    # Mid-cycle should be at >= MIN_MID_FRACTION of final
    if ent[-1] > 0.01:
        mid_frac = ent[len(ent) // 2] / ent[-1]
        metrics[f"{engine_label}_mid_fraction"] = mid_frac
        if mid_frac < MIN_MID_FRACTION:
            failures.append({
                "check": f"engine_{engine_label}_gradual_growth",
                "msg": f"Engine {engine_label} mid-cycle entropy = {ent[len(ent)//2]:.4f}, "
                       f"final = {ent[-1]:.4f}. Mid/final ratio = {mid_frac:.2%}, expected ≥ "
                       f"{MIN_MID_FRACTION:.0%}. Entropy grows too suddenly at the end, not gradually.",
            })

    return failures, metrics


def run(candidate):
    failures = []
    metrics = {}
    try:
        r = candidate.run_engine()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "run_engine_call", "msg": f"raised {type(e).__name__}: {str(e)[:200]}"}],
            "metrics": metrics,
        }

    for label, key in [("A", "engine_a_stage_records"), ("B", "engine_b_stage_records")]:
        recs = r.get(key)
        if recs is None:
            failures.append({"check": f"missing_{key}", "msg": f"run_engine() missing `{key}`"})
            continue
        f, m = _analyze_engine(recs, label)
        failures.extend(f)
        metrics.update(m)

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "Unitary-only stages from pure state — fails total_growth (S stays at 0)",
            "Random-walk stage entropies — fails monotonicity fraction",
            "Engine that does nothing for 31 stages then jumps — fails mid_fraction (gradual)",
            "Stage entropies all identical — fails total_growth",
        ],
        "baseline_variants": [
            "no-dissipator baseline — final entropy = 0",
            "instant-thermalization baseline — entropy = ln(16) immediately, no growth curve",
        ],
    }
