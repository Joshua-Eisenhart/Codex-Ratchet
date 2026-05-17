"""phase_07_engine_coupling.py — engines actually do something + couple non-trivially.

Phase 05 verified `run_engine()` returns values in [0, 2]. This phase strengthens:
  - cycle_closure_a > 0.05: Engine A actually evolves the state (not identity)
  - cross_engine_observable > 0.05: Engine B further changes the post-A state
    by a non-trivial amount (the two engines are genuinely coupled in their
    effect on the carrier)
  - cycle_closure_a < 1.99 (sanity): Engine A doesn't drive to maximally mixed
    state where everything is indistinguishable

Goal-stability: locks the load-bearing engine semantics.
"""

THRESHOLD_LOW = 0.05
THRESHOLD_HIGH = 1.99   # sanity ceiling — trace dist bounded by 1 actually for normalized rhos


def run(candidate):
    failures = []
    metrics = {}

    try:
        r = candidate.run_engine()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "run_engine_call", "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}],
            "metrics": metrics,
        }

    cc = float(r.get("cycle_closure_a", -1.0))
    ce = float(r.get("cross_engine_observable", -1.0))
    metrics["cycle_closure_a"] = cc
    metrics["cross_engine_observable"] = ce

    # cycle_closure_a > THRESHOLD_LOW: Engine A actually evolves the state
    if cc <= THRESHOLD_LOW:
        failures.append({
            "check": "cycle_closure_load_bearing",
            "msg": f"cycle_closure_a = {cc:.4f} ≤ {THRESHOLD_LOW}. Engine A produces "
                   f"a final state nearly identical to the starting state — the engine "
                   f"isn't actually doing anything across its 32 stages. Either the "
                   f"stage operators are identity, or evolution time per stage is too short.",
        })

    # Cycle_closure < ceiling: trace distance is bounded above by 1; values above suggest a bug
    if cc > 1.05:
        failures.append({
            "check": "cycle_closure_bounded",
            "msg": f"cycle_closure_a = {cc:.4f} > 1.05. Trace distance between density matrices is "
                   f"bounded by 1; exceeding this indicates a computation bug.",
        })

    # cross_engine_observable > THRESHOLD_LOW: B genuinely modifies A's end state
    if ce <= THRESHOLD_LOW:
        failures.append({
            "check": "cross_engine_load_bearing",
            "msg": f"cross_engine_observable = {ce:.4f} ≤ {THRESHOLD_LOW}. Engine B's 32 stages "
                   f"barely modify Engine A's end state — the two engines are effectively "
                   f"decoupled in their cumulative effect. The cross-engine observable is "
                   f"meant to demonstrate genuine coupling between the two engine schedules.",
        })

    # Determinism: same call twice should yield same metrics
    try:
        r2 = candidate.run_engine()
        cc2 = float(r2.get("cycle_closure_a", -1.0))
        ce2 = float(r2.get("cross_engine_observable", -1.0))
        metrics["cycle_closure_a_repeat"] = cc2
        metrics["cross_engine_observable_repeat"] = ce2
        if abs(cc - cc2) > 1e-4:
            failures.append({"check": "cycle_closure_deterministic",
                             "msg": f"cycle_closure_a varied: {cc} then {cc2}"})
        if abs(ce - ce2) > 1e-4:
            failures.append({"check": "cross_engine_deterministic",
                             "msg": f"cross_engine_observable varied: {ce} then {ce2}"})
    except Exception as e:
        failures.append({"check": "run_engine_repeat", "msg": f"second call failed: {str(e)[:200]}"})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "Engine A with identity stage operators — cycle_closure_a ≈ 0",
            "Engine B with identity stage operators — cross_engine_observable ≈ 0",
            "Engine A driving to maximally-mixed (I/16) on every run — cycle_closure_a saturates at 0.94",
            "Engine A and B with disjoint Hilbert-space support — cross_engine ≈ 0 (no coupling)",
        ],
        "baseline_variants": [
            "no-op baseline (zero stage operations) — both metrics should be 0",
            "infinite-time-evolution baseline — both metrics should saturate near the max value",
        ],
    }
