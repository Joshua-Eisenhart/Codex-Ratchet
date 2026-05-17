"""phase_33_state_classifier.py — the architecture must DO something: classify states.

User's directive: "have ones that can actually do things. and do unique information
processing." So far the audits prove the architecture has structure. This phase
tests whether it produces a USEFUL classification capability:

  Given an unknown 4-qubit density matrix ρ_x, classify it as "engine A trajectory"
  vs "engine B trajectory" by which engine's 8-stage path it lies closest to.

This is real information processing — the candidate must export a function
`classify_state(rho)` that returns one of {"A", "B"} based on geometric distance
to the two stage paths.

Test protocol:
  1. Build 16 "labeled" states: for each engine, apply stages 0..7 to a known
     anchor state, get 8 path points per engine.
  2. Generate 30 "test" states by adding small perturbations to the path points
     (15 from each engine's path, with engine-correct ground truth labels).
  3. Call `candidate.classify_state(rho)` for each. Compare to ground truth.
  4. Pass: classification accuracy ≥ 80% (well above chance 50%).
  5. Determinism: same input always gives same output.

This converts "the architecture has structure" into "the architecture is useful
for a non-trivial task."

Required API:
  classify_state(rho_qt) -> dict:
    {
      "engine_label": "A" or "B",
      "distance_to_A": float,
      "distance_to_B": float,
      "confidence": float in [0, 1],
    }
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "classify_state"):
        return {
            "pass": False,
            "failures": [{
                "check": "classify_state_exists",
                "msg": "Required `classify_state(rho_qt) -> dict` not exported. "
                       "Classification primitive: given a 4-qubit density matrix, return which "
                       "engine's stage trajectory it lies closest to. Return dict with keys "
                       "{engine_label: 'A'|'B', distance_to_A: float, distance_to_B: float, "
                       "confidence: float in [0,1]}. Use engine_stage to build reference paths "
                       "and trace distance as the metric. This is the architecture's first "
                       "USE-CASE: state classification via stage-trajectory affinity.",
            }],
            "metrics": metrics,
        }

    if not hasattr(candidate, "engine_stage"):
        return {"pass": False,
                "failures": [{"check": "engine_stage_needed", "msg": "classify_state needs engine_stage"}],
                "metrics": metrics}

    try:
        import qutip as qt
        # Anchor: a fixed reference state used to seed both engines' paths
        psi_anchor = qt.tensor(
            (qt.basis(2, 0) + 0.6 * qt.basis(2, 1)).unit(),
            (qt.basis(2, 0) + 0.4j * qt.basis(2, 1)).unit(),
            qt.basis(2, 0), qt.basis(2, 0))
        rho_anchor = qt.ket2dm(psi_anchor)
    except Exception as e:
        return {"pass": False, "failures": [{"check": "anchor", "msg": str(e)[:160]}], "metrics": metrics}

    # Build 30 test states: 15 from engine A path, 15 from engine B path,
    # each with a small random perturbation so they don't trivially match.
    test_states = []  # list of (rho_qt, ground_truth_label)
    rng = np.random.default_rng(20260513)
    for engine in ("A", "B"):
        for trial in range(15):
            s = trial % 8
            sub = trial % 4
            try:
                r = candidate.engine_stage(engine, s, sub, rho_anchor)
                path_pt = r.get("output_rho_qt") if isinstance(r, dict) else r
            except Exception as e:
                failures.append({"check": f"build_test_{engine}_{trial}", "msg": str(e)[:120]})
                continue
            # Small random Hermitian perturbation
            path_arr = _to_arr(path_pt)
            A = rng.normal(scale=0.04, size=(16, 16)) + 1j * rng.normal(scale=0.04, size=(16, 16))
            H = (A + A.conj().T) / 2.0
            # Apply tiny unitary perturbation: exp(-i ε H) ρ exp(+i ε H)
            from scipy.linalg import expm
            U_pert = expm(-1j * 0.05 * H)
            perturbed = U_pert @ path_arr @ U_pert.conj().T
            # Renormalize trace
            perturbed /= np.trace(perturbed).real
            rho_test = qt.Qobj(perturbed, dims=[[2, 2, 2, 2], [2, 2, 2, 2]])
            test_states.append((rho_test, engine))

    if len(test_states) < 25:
        return {"pass": False, "failures": failures + [
            {"check": "test_coverage", "msg": f"only {len(test_states)} test states built"}
        ], "metrics": metrics}

    # Run classifier
    correct = 0
    answered = 0
    confidences = []
    for rho_test, truth in test_states:
        try:
            res = candidate.classify_state(rho_test)
        except Exception as e:
            failures.append({"check": "classify_call", "msg": f"{type(e).__name__}: {str(e)[:140]}"})
            continue
        if not isinstance(res, dict):
            failures.append({"check": "classify_returns_dict", "msg": f"got {type(res).__name__}"})
            continue
        label = res.get("engine_label")
        if label not in ("A", "B"):
            failures.append({"check": "classify_label",
                             "msg": f"engine_label={label!r}; must be 'A' or 'B'"})
            continue
        for k in ("distance_to_A", "distance_to_B", "confidence"):
            if k not in res:
                failures.append({"check": f"classify_missing_{k}", "msg": f"missing `{k}`"})
        conf = res.get("confidence", 0.0)
        confidences.append(float(conf) if isinstance(conf, (int, float)) else 0.0)
        answered += 1
        if label == truth:
            correct += 1

    if answered == 0:
        return {"pass": False, "failures": failures, "metrics": metrics}

    accuracy = correct / answered
    metrics["classification_accuracy"] = accuracy
    metrics["correct"] = correct
    metrics["answered"] = answered
    metrics["avg_confidence"] = float(np.mean(confidences)) if confidences else 0.0

    if accuracy < 0.80:
        failures.append({
            "check": "classification_accuracy",
            "msg": f"classify_state accuracy = {correct}/{answered} = {accuracy:.1%} < 80%. "
                   f"Architecture doesn't reliably distinguish engine-A trajectory states from "
                   f"engine-B trajectory states despite Phase 30 showing distinct paths.",
        })

    # Determinism
    if test_states:
        try:
            r1 = candidate.classify_state(test_states[0][0])
            r2 = candidate.classify_state(test_states[0][0])
            if r1.get("engine_label") != r2.get("engine_label") or \
               abs(r1.get("distance_to_A", 0) - r2.get("distance_to_A", 0)) > 1e-6:
                failures.append({"check": "classify_deterministic",
                                 "msg": "two identical calls produced different results"})
        except Exception:
            pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "always returns 'A' — 50% accuracy on balanced test set",
            "random output — 50% on average; fails determinism too",
            "uses metadata leak — passes accuracy but fails on unseen states",
        ],
        "baseline_variants": [
            "trace-distance to path centroid baseline: passes if Phase 30 paths are distinct",
            "naive partial-trace baseline: passes only if engines differ in reduced state",
        ],
    }
