"""phase_38_explain_confidence_honesty.py — does explain_state know when it doesn't know?

Phase 37 passed at 100% on perturbation 0.04. That's nearest-neighbor with comfort.
Phase 38 tests whether the confidence values are HONEST:

  1. PERTURBATION CURVE. Test explain_state at scales 0.04, 0.10, 0.20, 0.40.
     Stage accuracy should degrade (smaller perturbation → higher accuracy).
     Stage_confidence should ALSO degrade with perturbation (correlated).
     Pearson correlation between accuracy_at_scale and confidence_at_scale ≥ 0.5.

  2. HAAR HONESTY. On Haar-random states (truly novel, not on any path),
     avg stage_confidence should be LOW (< 0.5). If the architecture is honest
     it reports low confidence when input isn't near any reference.

  3. GRACEFUL DEGRADATION. Stage accuracy should drop monotonically as
     perturbation grows. No accuracy CLIFF (where one step drops > 50%).

This catches the "confident-but-wrong" failure mode where explain_state always
returns confidence ≈ 1.0 regardless of input quality.
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _perturb(rho_arr, rng, scale):
    A = rng.normal(scale=scale, size=rho_arr.shape) + 1j * rng.normal(scale=scale, size=rho_arr.shape)
    H = (A + A.conj().T) / 2.0
    from scipy.linalg import expm
    U = expm(-1j * scale * H)
    out = U @ rho_arr @ U.conj().T
    out /= np.trace(out).real
    return out


def _haar(rng, n=16):
    psi = rng.normal(size=n) + 1j * rng.normal(size=n)
    psi /= np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "explain_state") or not hasattr(candidate, "engine_stage"):
        return {"pass": False,
                "failures": [{"check": "prereq", "msg": "needs explain_state + engine_stage"}],
                "metrics": metrics}

    import qutip as qt
    QDIMS = [[2, 2, 2, 2], [2, 2, 2, 2]]
    psi_anchor = qt.tensor(
        (qt.basis(2, 0) + 0.6 * qt.basis(2, 1)).unit(),
        (qt.basis(2, 0) + 0.4j * qt.basis(2, 1)).unit(),
        qt.basis(2, 0), qt.basis(2, 0))
    rho_anchor = qt.ket2dm(psi_anchor)

    rng = np.random.default_rng(20260518)

    # ===== Test 1+3: perturbation curve =====
    scales = [0.04, 0.10, 0.20, 0.40]
    acc_by_scale = {}
    conf_by_scale = {}
    for scale in scales:
        correct = 0
        total = 0
        confs = []
        for engine in ("A", "B"):
            for s in range(8):
                try:
                    r = candidate.engine_stage(engine, s, 0, rho_anchor)
                    out = r.get("output_rho_qt") if isinstance(r, dict) else r
                    perturbed = _perturb(_to_arr(out), rng, scale)
                    rho_test = qt.Qobj(perturbed, dims=QDIMS)
                    res = candidate.explain_state(rho_test)
                    if res.get("best_engine") == engine and res.get("best_stage") == s:
                        correct += 1
                    total += 1
                    confs.append(float(res.get("stage_confidence", 0.0)))
                except Exception as e:
                    failures.append({"check": f"scale_{scale}", "msg": str(e)[:100]})
        if total > 0:
            acc_by_scale[scale] = correct / total
            conf_by_scale[scale] = sum(confs) / len(confs) if confs else 0.0
    metrics["accuracy_by_scale"] = acc_by_scale
    metrics["avg_confidence_by_scale"] = conf_by_scale

    # Pearson correlation between accuracy and confidence across scales
    if len(acc_by_scale) >= 3:
        accs = np.array([acc_by_scale[s] for s in scales if s in acc_by_scale])
        cs = np.array([conf_by_scale[s] for s in scales if s in conf_by_scale])
        if accs.std() > 0 and cs.std() > 0:
            r = float(np.corrcoef(accs, cs)[0, 1])
        else:
            r = 0.0
        metrics["pearson_accuracy_confidence"] = r
        if r < 0.5:
            failures.append({
                "check": "confidence_tracks_accuracy",
                "msg": f"Pearson r={r:.3f} between accuracy and stage_confidence across "
                       f"perturbation scales < 0.5. Confidence values don't track quality.",
            })

    # Monotonic accuracy degradation (no cliff)
    sorted_scales = sorted(acc_by_scale.keys())
    drops = []
    for i in range(len(sorted_scales) - 1):
        drops.append(acc_by_scale[sorted_scales[i]] - acc_by_scale[sorted_scales[i + 1]])
    metrics["consecutive_accuracy_drops"] = drops
    max_drop = max(drops) if drops else 0.0
    metrics["max_consecutive_drop"] = max_drop
    if max_drop > 0.50:
        failures.append({
            "check": "graceful_degradation",
            "msg": f"max single-step accuracy drop = {max_drop:.2%} > 50%. Cliff in "
                   f"performance — paths are razor-thin in some direction.",
        })

    # ===== Test 2: Haar honesty =====
    haar_confs = []
    haar_distances = []
    for _ in range(20):
        rho_arr = _haar(rng)
        rho_q = qt.Qobj(rho_arr, dims=QDIMS)
        try:
            res = candidate.explain_state(rho_q)
            haar_confs.append(float(res.get("stage_confidence", 0.0)))
            haar_distances.append(float(res.get("distance_to_match", 0.0)))
        except Exception as e:
            failures.append({"check": "haar_explain", "msg": str(e)[:100]})

    if haar_confs:
        avg_haar_conf = sum(haar_confs) / len(haar_confs)
        max_haar_conf = max(haar_confs)
        metrics["avg_haar_stage_confidence"] = avg_haar_conf
        metrics["max_haar_stage_confidence"] = max_haar_conf
        metrics["avg_haar_distance_to_match"] = sum(haar_distances) / len(haar_distances)
        if avg_haar_conf > 0.5:
            failures.append({
                "check": "haar_low_confidence",
                "msg": f"avg stage_confidence on Haar states = {avg_haar_conf:.3f} > 0.5. "
                       f"Architecture reports high confidence on truly novel states — it doesn't "
                       f"know when it doesn't know.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "always-confident classifier — fails haar_low_confidence",
            "constant-confidence classifier — fails confidence_tracks_accuracy",
            "cliff at perturbation 0.10 — fails graceful_degradation",
        ],
        "baseline_variants": [
            "fixed conf=0.5 — passes Haar honesty but fails accuracy correlation",
            "conf = 1/distance baseline — should pass both",
        ],
    }
