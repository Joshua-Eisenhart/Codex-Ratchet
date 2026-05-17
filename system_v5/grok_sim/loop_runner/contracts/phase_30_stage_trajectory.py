"""phase_30_stage_trajectory.py — stages must form an ORDERED trajectory, not random points.

Phase 28 verified the 16 stages produce pairwise-distinct outputs. But "distinct" is
necessary, not sufficient. A real engine has 8 stages that flow through an ORDERED
cognitive process — consecutive stages must be closer to each other than to distant
stages on the constraint manifold.

This phase tests the geometric structure of the stage sequence:
  1. Path monotonicity: within each engine, the 8 stage-aggregates lie on a path
     where td(stage_i, stage_{i+1}) is consistently smaller than td(stage_i,
     stage_{i+k}) for k > 1.
  2. Trajectory persistence: the 8-stage sequence should NOT fold back on itself —
     stage 7 should be far from stage 0 (significantly more than a random walk
     would produce).
  3. Engine A vs Engine B paths should be DISTINCT trajectories (not just permuted
     versions of each other).

This catches the failure mode "16 stages are well-separated but in random directions"
which Phase 28 permits.
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _trace_dist(a, b):
    diff = _to_arr(a) - _to_arr(b)
    s = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(s))


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "engine_stage"):
        return {"pass": False,
                "failures": [{"check": "engine_stage_exists", "msg": "see Phase 28."}],
                "metrics": metrics}

    try:
        import qutip as qt
        psi_ref = qt.tensor(
            (qt.basis(2, 0) + 0.7 * qt.basis(2, 1)).unit(),
            (qt.basis(2, 0) + 0.3j * qt.basis(2, 1)).unit(),
            (qt.basis(2, 0) + 0.5 * qt.basis(2, 1)).unit(),
            qt.basis(2, 0))
        rho_ref = qt.ket2dm(psi_ref)
    except Exception as e:
        return {"pass": False, "failures": [{"check": "ref_state", "msg": str(e)[:200]}], "metrics": metrics}

    # Get stage-aggregate for each (engine, stage): average across 4 substages
    aggregates = {}
    for engine in ("A", "B"):
        for s in range(8):
            subs = []
            for sub in range(4):
                try:
                    r = candidate.engine_stage(engine, s, sub, rho_ref)
                    out = r.get("output_rho_qt") if isinstance(r, dict) else r
                    subs.append(_to_arr(out))
                except Exception as e:
                    failures.append({"check": f"call_{engine}_{s}_{sub}", "msg": str(e)[:160]})
            if subs:
                aggregates[(engine, s)] = sum(subs) / len(subs)

    if len(aggregates) < 16:
        return {"pass": False, "failures": failures + [
            {"check": "aggregate_coverage", "msg": f"only {len(aggregates)}/16 stages covered"}
        ], "metrics": metrics}

    # Path monotonicity: within each engine
    for engine in ("A", "B"):
        path = [aggregates[(engine, s)] for s in range(8)]
        consecutive_tds = [_trace_dist(path[i], path[i + 1]) for i in range(7)]
        non_consecutive_tds = [_trace_dist(path[i], path[j])
                               for i in range(8) for j in range(i + 2, 8)]
        avg_consec = sum(consecutive_tds) / len(consecutive_tds)
        avg_far = sum(non_consecutive_tds) / len(non_consecutive_tds)
        metrics[f"{engine}_avg_consecutive_td"] = avg_consec
        metrics[f"{engine}_avg_non_consecutive_td"] = avg_far
        metrics[f"{engine}_path_ratio"] = avg_far / max(avg_consec, 1e-9)
        # On a real ordered trajectory, far stages should be at least 1.3x consecutive
        # stages on average (relaxed because the path lives in a high-dim space and
        # may have curvature reducing the ratio).
        if avg_far < 1.3 * avg_consec:
            failures.append({
                "check": f"{engine}_path_monotonicity",
                "msg": f"Engine {engine}: avg consecutive td = {avg_consec:.4f}, "
                       f"avg far-pair td = {avg_far:.4f}. Ratio {avg_far/max(avg_consec,1e-9):.3f} "
                       f"< 1.30. Stages are not arranged on an ordered trajectory; they look "
                       f"randomly distributed.",
            })

    # Trajectory persistence: stage_7 should be far from stage_0
    for engine in ("A", "B"):
        endpoints_td = _trace_dist(aggregates[(engine, 0)], aggregates[(engine, 7)])
        consec_avg = sum(_trace_dist(aggregates[(engine, i)], aggregates[(engine, i + 1)])
                         for i in range(7)) / 7
        # A non-folding 8-step path should have d(0,7) ≥ 2.0 × avg consecutive step
        # (much weaker than triangle inequality upper bound 7×avg).
        metrics[f"{engine}_endpoint_td"] = endpoints_td
        metrics[f"{engine}_endpoint_to_consec_ratio"] = endpoints_td / max(consec_avg, 1e-9)
        if endpoints_td < 2.0 * consec_avg:
            failures.append({
                "check": f"{engine}_trajectory_persistence",
                "msg": f"Engine {engine}: td(stage_0, stage_7) = {endpoints_td:.4f}, "
                       f"avg consecutive step = {consec_avg:.4f}. Endpoint distance is only "
                       f"{endpoints_td/max(consec_avg,1e-9):.2f}× the step size — the path folds "
                       f"back on itself rather than persisting.",
            })

    # Engine A vs Engine B: trajectories should be distinct
    # Compute the FULL pairwise-distance matrix for each engine, compare matrices.
    def _path_matrix(engine):
        return np.array([[_trace_dist(aggregates[(engine, i)], aggregates[(engine, j)])
                          for j in range(8)] for i in range(8)])
    M_a = _path_matrix("A")
    M_b = _path_matrix("B")
    matrix_diff = float(np.linalg.norm(M_a - M_b, ord="fro"))
    matrix_avg = float(0.5 * (np.linalg.norm(M_a, ord="fro") + np.linalg.norm(M_b, ord="fro")))
    metrics["AB_matrix_diff_frobenius"] = matrix_diff
    metrics["AB_matrix_diff_normalized"] = matrix_diff / max(matrix_avg, 1e-9)
    if matrix_diff / max(matrix_avg, 1e-9) < 0.10:
        failures.append({
            "check": "AB_trajectory_distinct",
            "msg": f"Engine A and Engine B pairwise-td matrices differ by only "
                   f"{matrix_diff/max(matrix_avg,1e-9):.3f} (normalized Frobenius). The two "
                   f"engines trace nearly the same trajectory — they should be DIFFERENT "
                   f"cognitive paths, not relabeled copies.",
        })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "random distinct stages — passes Phase 28, fails path_monotonicity",
            "circular trajectory (folds back) — fails trajectory_persistence",
            "Engine B = permutation of Engine A — fails AB_trajectory_distinct",
        ],
        "baseline_variants": [
            "linear-trajectory baseline: stages on a line — passes all three",
            "random-walk baseline: passes monotonicity by chance but fails persistence",
        ],
    }
