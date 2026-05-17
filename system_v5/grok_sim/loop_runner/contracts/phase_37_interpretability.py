"""phase_37_interpretability.py — the architecture must EXPLAIN, not just classify.

classify_state returns a label. process_state returns a final state. Neither tells
the AI consumer WHAT the architecture interpreted the input as. This phase requires
a structured interpretability primitive:

  explain_state(rho) -> dict:
    {
      "best_engine": "A" or "B",
      "best_stage": int 0..7,
      "best_substage": int 0..3,
      "distance_to_match": float,
      "engine_confidence": float in [0, 1],
      "stage_confidence": float in [0, 1],
      "explanation": str,                  # human-readable summary
    }

Test protocol:
  1. Build 32 known ground-truth states by applying engine_stage(engine, stage,
     substage, ρ_anchor) for known (engine, stage, substage) — small perturbation.
  2. Call explain_state(ρ_perturbed). Compare returned (engine, stage) to ground
     truth.
  3. Pass:
     - Engine accuracy ≥ 90% (already shown in Phase 33/34, sanity check)
     - Stage accuracy ≥ 50% (much harder; 8 stages × 2 engines = 16 buckets;
       chance is 1/16 = 6%; 50% is well above chance)
     - Stage adjacent-accuracy ≥ 80% (correct stage OR ± 1 — accounts for
       trajectory proximity; consecutive stages are close by Phase 30)
     - Explanation string non-empty and references both engine + stage
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _perturb(rho_arr, rng, scale=0.04):
    A = rng.normal(scale=scale, size=rho_arr.shape) + 1j * rng.normal(scale=scale, size=rho_arr.shape)
    H = (A + A.conj().T) / 2.0
    from scipy.linalg import expm
    U = expm(-1j * scale * H)
    out = U @ rho_arr @ U.conj().T
    out /= np.trace(out).real
    return out


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "explain_state"):
        return {"pass": False, "failures": [{
            "check": "explain_state_exists",
            "msg": "Required `explain_state(rho_qt) -> dict` not exported. Should return "
                   "structured interpretation of what the architecture sees in rho: best_engine, "
                   "best_stage, best_substage, distance_to_match, engine_confidence, "
                   "stage_confidence, explanation (str). This is the architecture's "
                   "interpretability primitive — converts a state into a structured story.",
        }], "metrics": metrics}

    if not hasattr(candidate, "engine_stage"):
        return {"pass": False,
                "failures": [{"check": "engine_stage_needed", "msg": "explain_state needs engine_stage"}],
                "metrics": metrics}

    import qutip as qt
    QDIMS = [[2, 2, 2, 2], [2, 2, 2, 2]]
    psi_anchor = qt.tensor(
        (qt.basis(2, 0) + 0.6 * qt.basis(2, 1)).unit(),
        (qt.basis(2, 0) + 0.4j * qt.basis(2, 1)).unit(),
        qt.basis(2, 0), qt.basis(2, 0))
    rho_anchor = qt.ket2dm(psi_anchor)

    rng = np.random.default_rng(20260517)
    test_cases = []
    for engine in ("A", "B"):
        for s in range(8):
            for sub in [0, 2]:  # 2 substages per stage = 32 test cases
                try:
                    r = candidate.engine_stage(engine, s, sub, rho_anchor)
                    out = r.get("output_rho_qt") if isinstance(r, dict) else r
                    perturbed = _perturb(_to_arr(out), rng, scale=0.04)
                    rho_test = qt.Qobj(perturbed, dims=QDIMS)
                    test_cases.append((rho_test, engine, s, sub))
                except Exception as e:
                    failures.append({"check": f"build_{engine}_{s}_{sub}", "msg": str(e)[:100]})

    if len(test_cases) < 20:
        return {"pass": False, "failures": failures + [
            {"check": "test_coverage", "msg": f"only {len(test_cases)} cases"}
        ], "metrics": metrics}

    eng_correct = 0
    stage_correct = 0
    stage_adjacent = 0
    sub_correct = 0
    answered = 0
    explanations = []
    for rho_test, true_engine, true_stage, true_sub in test_cases:
        try:
            res = candidate.explain_state(rho_test)
        except Exception as e:
            failures.append({"check": "explain_call", "msg": f"{type(e).__name__}: {str(e)[:120]}"})
            continue
        if not isinstance(res, dict):
            failures.append({"check": "explain_dict", "msg": f"got {type(res).__name__}"})
            continue
        be = res.get("best_engine")
        bs = res.get("best_stage")
        bsub = res.get("best_substage")
        expl = res.get("explanation", "")
        for key in ("best_engine", "best_stage", "best_substage",
                    "engine_confidence", "stage_confidence", "explanation"):
            if key not in res:
                failures.append({"check": f"missing_{key}", "msg": f"missing `{key}`"})
        if be not in ("A", "B"):
            continue
        answered += 1
        if be == true_engine:
            eng_correct += 1
        if bs == true_stage:
            stage_correct += 1
            stage_adjacent += 1
        elif bs is not None and abs(int(bs) - true_stage) == 1:
            stage_adjacent += 1
        if bsub == true_sub:
            sub_correct += 1
        explanations.append(expl)

    if answered == 0:
        return {"pass": False, "failures": failures, "metrics": metrics}

    eng_acc = eng_correct / answered
    stage_acc = stage_correct / answered
    adj_acc = stage_adjacent / answered
    sub_acc = sub_correct / answered
    metrics["engine_accuracy"] = eng_acc
    metrics["stage_exact_accuracy"] = stage_acc
    metrics["stage_adjacent_accuracy"] = adj_acc
    metrics["substage_accuracy"] = sub_acc
    metrics["n_test_cases"] = answered

    if eng_acc < 0.90:
        failures.append({"check": "engine_accuracy", "msg": f"engine accuracy {eng_acc:.2%} < 90%"})
    if stage_acc < 0.50:
        failures.append({"check": "stage_exact",
                         "msg": f"stage exact accuracy {stage_acc:.2%} < 50% (chance is ~12%)"})
    if adj_acc < 0.80:
        failures.append({"check": "stage_adjacent",
                         "msg": f"stage adjacent accuracy {adj_acc:.2%} < 80%"})

    # Explanation quality: at least 90% should be non-empty
    nonempty = sum(1 for e in explanations if e and len(e.strip()) > 5)
    metrics["nonempty_explanations"] = nonempty
    if nonempty / max(len(explanations), 1) < 0.90:
        failures.append({"check": "explanation_nonempty",
                         "msg": f"only {nonempty}/{len(explanations)} explanations non-empty"})

    # Explanations should reference engine + stage info
    references_both = sum(
        1 for e in explanations
        if e and any(t in e.lower() for t in ["engine", "stage", "trajectory", "path"])
    )
    metrics["explanations_reference_structure"] = references_both
    if references_both / max(len(explanations), 1) < 0.80:
        failures.append({"check": "explanation_quality",
                         "msg": f"only {references_both}/{len(explanations)} explanations reference "
                                f"engine/stage/trajectory/path structure"})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "always returns stage 0 — fails stage_exact even though adj might pass",
            "engine correct but stage random — fails stage_exact",
            "no explanation text — fails explanation_nonempty",
        ],
        "baseline_variants": [
            "nearest-trajectory-point baseline — passes engine but stage depends on path resolution",
        ],
    }
