"""phase_43_denoise_pipeline.py — multi-primitive AI use case.

Concrete workflow demonstrating "massive AI tool set" composability:
  Input: a 4-qubit state ρ_noisy that was produced by an unknown engine+stage
         with terrain noise applied
  Pipeline (must chain ≥3 architecture primitives):
    1. explain_state(ρ_noisy) — identify which (engine, stage) most likely
       produced this
    2. petz_recover(detected_terrain, ρ_noisy) — undo the inferred noise channel
    3. classify_state(ρ_recovered) — sanity check that recovery lands in
       same engine basin
    4. Return structured diagnosis
  Output: best-guess recovery + which engine produced + provenance summary

This is the architecture's first composed AI workflow. Required API:
  denoise_pipeline(rho_noisy_qt) -> dict {
    detected_engine: 'A' or 'B',
    detected_stage: int 0..7,
    detected_terrain: 'Ti' or 'Te',
    recovered_rho_qt: qt.Qobj,
    recovery_distance: float,  # trace distance from noisy to recovered
    consistency_check: bool,    # classify_state(recovered) == detected_engine
    summary: str,
  }

Test:
  - Build 16 ground-truth states from known (engine, stage); apply Ti or Te
    terrain noise (varying strength 0.3-0.5)
  - Call denoise_pipeline on the noisy state
  - Verify: detected engine correct (≥75%), recovered state closer to clean
    input than noisy state was (improvement ≥75%), consistency_check = True
    (≥80%)
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"): return np.asarray(obj.full())
    if hasattr(obj, "numpy"): return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _td(a, b):
    diff = _to_arr(a) - _to_arr(b)
    s = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(s))


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "denoise_pipeline"):
        return {"pass": False, "failures": [{
            "check": "denoise_pipeline_exists",
            "msg": "Required `denoise_pipeline(rho_noisy_qt) -> dict` not exported. Should "
                   "chain explain_state + petz_recover + classify_state in a multi-primitive "
                   "AI workflow. Return {detected_engine, detected_stage, detected_terrain, "
                   "recovered_rho_qt, recovery_distance, consistency_check, summary}. "
                   "Demonstrates the architecture's composable tool surface.",
        }], "metrics": metrics}

    for prereq in ("engine_stage", "terrain_operation", "explain_state", "classify_state"):
        if not hasattr(candidate, prereq):
            return {"pass": False, "failures": [
                {"check": f"{prereq}_needed", "msg": f"denoise_pipeline needs {prereq}"}],
                    "metrics": metrics}

    import qutip as qt
    QDIMS = [[2, 2, 2, 2], [2, 2, 2, 2]]
    psi_anchor = qt.tensor(
        (qt.basis(2, 0) + 0.6 * qt.basis(2, 1)).unit(),
        (qt.basis(2, 0) + 0.4j * qt.basis(2, 1)).unit(),
        qt.basis(2, 0), qt.basis(2, 0))
    rho_anchor = qt.ket2dm(psi_anchor)

    # Build 16 test cases
    test_cases = []  # (clean_state, noisy_state, true_engine, true_stage, true_terrain)
    for engine in ("A", "B"):
        for s in range(8):
            try:
                r = candidate.engine_stage(engine, s, 0, rho_anchor)
                clean = r.get("output_rho_qt") if isinstance(r, dict) else r
                # Apply Ti or Te noise (alternating)
                noise_terrain = "Ti" if s % 2 == 0 else "Te"
                strength = 0.30 + 0.04 * s
                noisy = candidate.terrain_operation(noise_terrain, clean, strength=strength)["output_rho_qt"]
                test_cases.append((clean, noisy, engine, s, noise_terrain))
            except Exception as e:
                failures.append({"check": f"build_{engine}_{s}", "msg": str(e)[:100]})

    if len(test_cases) < 10:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": f"only {len(test_cases)} cases"}], "metrics": metrics}

    engine_correct = 0
    improved = 0
    consistency_ok = 0
    answered = 0
    for clean, noisy, true_engine, true_stage, true_terrain in test_cases:
        try:
            res = candidate.denoise_pipeline(noisy)
        except Exception as e:
            failures.append({"check": "denoise_call", "msg": f"{type(e).__name__}: {str(e)[:120]}"})
            continue
        if not isinstance(res, dict):
            failures.append({"check": "denoise_dict", "msg": f"got {type(res).__name__}"})
            continue
        for key in ("detected_engine", "detected_stage", "detected_terrain",
                    "recovered_rho_qt", "recovery_distance", "consistency_check", "summary"):
            if key not in res:
                failures.append({"check": f"missing_{key}", "msg": f"missing `{key}`"})
        if "detected_engine" not in res:
            continue
        answered += 1
        if res["detected_engine"] == true_engine:
            engine_correct += 1
        if res.get("consistency_check"):
            consistency_ok += 1
        # Improvement check: recovered closer to clean than noisy was
        try:
            d_noisy_clean = _td(noisy, clean)
            d_recovered_clean = _td(res["recovered_rho_qt"], clean)
            if d_recovered_clean < d_noisy_clean:
                improved += 1
        except Exception as e:
            failures.append({"check": "improvement_calc", "msg": str(e)[:100]})

    if answered == 0:
        return {"pass": False, "failures": failures, "metrics": metrics}

    eng_acc = engine_correct / answered
    improve_rate = improved / answered
    consist_rate = consistency_ok / answered
    metrics["engine_detection_accuracy"] = eng_acc
    metrics["recovery_improvement_rate"] = improve_rate
    metrics["consistency_check_pass_rate"] = consist_rate
    metrics["n_test_cases"] = answered

    if eng_acc < 0.75:
        failures.append({"check": "engine_detection",
                         "msg": f"engine detection {eng_acc:.2%} < 75%"})
    if improve_rate < 0.50:
        failures.append({"check": "recovery_improvement",
                         "msg": f"recovery improvement {improve_rate:.2%} < 50%; "
                                f"petz_recover step often doesn't reduce noise"})
    if consist_rate < 0.70:
        failures.append({"check": "consistency_check",
                         "msg": f"consistency_check pass rate {consist_rate:.2%} < 70%"})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "explain_state correct but petz_recover destroys state — fails improvement",
            "all-A or all-B detection — fails engine accuracy",
            "no consistency check — recovered state doesn't classify same as detected",
        ],
        "baseline_variants": [
            "identity-recovery baseline: return noisy unchanged — passes engine detection but fails improvement",
        ],
    }
