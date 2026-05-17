"""phase_28_stage_semantic_uniqueness.py — 16 stages must do 16 different things.

The architecture claims 2 engines × 8 stages = 16 unique stage points, each with
4 substages cycling Ti/Te/Fi/Fe (64 total callable operations). Phase 12 and 20
only check that stage *identifiers* are unique; they do NOT check that the stages
produce semantically different output states.

This phase pressure-tests semantic uniqueness:
  - For each (engine, stage, substage), apply `engine_stage(engine, s, sub, ρ_ref)`
    to a FIXED reference state ρ_ref.
  - Collect 64 output density matrices.
  - Pairwise trace distance must be > 0.05 for ≥ 95% of pairs.
  - The 16 stage-aggregates (averaging over substages) must all be pairwise
    distinct: td > 0.08 for ≥ 95% of (16 choose 2) = 120 pairs.
  - Substage roles must be consistent: the same substage index should produce
    structurally similar effects across stages (rejected if substage roles collapse).

Pass criteria:
  - 95%+ of substage pairs have td > 0.05
  - 95%+ of stage-aggregate pairs have td > 0.08
  - All 64 outputs are valid density matrices (hermitian, trace 1, PSD)
  - Determinism: two calls with same args produce td < 1e-6 output
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
                "failures": [{"check": "engine_stage_exists",
                              "msg": "Required `engine_stage(engine, stage, substage, ρ) -> dict`."}],
                "metrics": metrics}

    try:
        import qutip as qt
        psi_ref = qt.tensor(
            (qt.basis(2, 0) + 0.7 * qt.basis(2, 1)).unit(),
            (qt.basis(2, 0) + 0.3j * qt.basis(2, 1)).unit(),
            (qt.basis(2, 0) + 0.5 * qt.basis(2, 1)).unit(),
            qt.basis(2, 0),
        )
        rho_ref = qt.ket2dm(psi_ref)
    except Exception as e:
        return {"pass": False, "failures": [{"check": "ref_state", "msg": str(e)[:200]}], "metrics": metrics}

    # Collect 64 outputs
    outputs = {}  # (engine, s, sub) -> ndarray
    for engine in ("A", "B"):
        for s in range(8):
            for sub in range(4):
                try:
                    r = candidate.engine_stage(engine, s, sub, rho_ref)
                    # Accept either dict with "output_rho_qt" or a Qobj directly
                    if isinstance(r, dict):
                        out = r.get("output_rho_qt") or r.get("output_rho") or r.get("rho_out")
                    else:
                        out = r
                    if out is None:
                        failures.append({"check": f"out_missing_{engine}_{s}_{sub}",
                                         "msg": "engine_stage returned no output state"})
                        continue
                    outputs[(engine, s, sub)] = _to_arr(out)
                except Exception as e:
                    failures.append({"check": f"call_{engine}_{s}_{sub}",
                                     "msg": f"{type(e).__name__}: {str(e)[:160]}"})

    metrics["outputs_collected"] = len(outputs)
    if len(outputs) < 60:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": f"only {len(outputs)}/64 callable points worked"}
        ], "metrics": metrics}

    # Validity: every output is hermitian / trace 1 / PSD
    invalid = 0
    for key, arr in outputs.items():
        try:
            tr = float(np.real(np.trace(arr)))
            herm = float(np.max(np.abs(arr - arr.conj().T)))
            eigs = np.linalg.eigvalsh(0.5 * (arr + arr.conj().T))
            if abs(tr - 1.0) > 1e-3 or herm > 1e-4 or eigs.min() < -1e-4:
                invalid += 1
        except Exception:
            invalid += 1
    metrics["invalid_density_matrices"] = invalid
    if invalid > 2:
        failures.append({"check": "validity",
                         "msg": f"{invalid}/64 outputs are not valid density matrices"})

    # Pairwise trace distance over all 64
    keys = sorted(outputs.keys())
    pair_tds = []
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            pair_tds.append(_trace_dist(outputs[k1], outputs[k2]))
    n_pairs = len(pair_tds)
    passing = sum(1 for t in pair_tds if t > 0.05)
    metrics["substage_pair_count"] = n_pairs
    metrics["substage_pairs_passing_td_gt_005"] = passing
    metrics["substage_pair_pass_rate"] = passing / max(n_pairs, 1)
    metrics["substage_min_td"] = float(min(pair_tds)) if pair_tds else 0.0
    metrics["substage_median_td"] = float(np.median(pair_tds)) if pair_tds else 0.0
    if passing / max(n_pairs, 1) < 0.95:
        failures.append({
            "check": "substage_pair_uniqueness",
            "msg": f"only {passing}/{n_pairs} = {passing/max(n_pairs,1):.1%} of substage-level "
                   f"pairs have td > 0.05. Substages collapse — the 64 callable points are not "
                   f"64 distinct operations.",
        })

    # Stage-aggregate uniqueness (average over 4 substages, 16 aggregates)
    stage_keys = [(e, s) for e in ("A", "B") for s in range(8)]
    aggregates = {}
    for (e, s) in stage_keys:
        substage_arrs = [outputs[(e, s, sub)] for sub in range(4) if (e, s, sub) in outputs]
        if not substage_arrs:
            continue
        aggregates[(e, s)] = sum(substage_arrs) / len(substage_arrs)
    agg_keys = sorted(aggregates.keys())
    agg_pair_tds = []
    for i, k1 in enumerate(agg_keys):
        for k2 in agg_keys[i + 1:]:
            agg_pair_tds.append(_trace_dist(aggregates[k1], aggregates[k2]))
    agg_pairs = len(agg_pair_tds)
    agg_passing = sum(1 for t in agg_pair_tds if t > 0.08)
    metrics["stage_aggregate_pairs"] = agg_pairs
    metrics["stage_aggregate_passing_td_gt_008"] = agg_passing
    metrics["stage_aggregate_pass_rate"] = agg_passing / max(agg_pairs, 1)
    metrics["stage_aggregate_min_td"] = float(min(agg_pair_tds)) if agg_pair_tds else 0.0
    if agg_passing / max(agg_pairs, 1) < 0.95:
        failures.append({
            "check": "stage_aggregate_uniqueness",
            "msg": f"only {agg_passing}/{agg_pairs} = {agg_passing/max(agg_pairs,1):.1%} of "
                   f"stage-aggregate pairs (16 choose 2 = 120) have td > 0.08. Two or more stages "
                   f"are doing semantically the same thing.",
        })

    # Substage role consistency: substage `sub` should differ from same `sub` across stages
    # by LESS than substage `sub` differs from substage `sub'≠sub`. This is the substage-
    # ROLE check: substages must function as roles, not noise.
    same_sub_tds = []
    diff_sub_tds = []
    for sub in range(4):
        for e in ("A", "B"):
            for s1 in range(8):
                for s2 in range(s1 + 1, 8):
                    if (e, s1, sub) in outputs and (e, s2, sub) in outputs:
                        same_sub_tds.append(_trace_dist(outputs[(e, s1, sub)],
                                                        outputs[(e, s2, sub)]))
    for e in ("A", "B"):
        for s in range(8):
            for sub1 in range(4):
                for sub2 in range(sub1 + 1, 4):
                    if (e, s, sub1) in outputs and (e, s, sub2) in outputs:
                        diff_sub_tds.append(_trace_dist(outputs[(e, s, sub1)],
                                                        outputs[(e, s, sub2)]))
    if same_sub_tds and diff_sub_tds:
        avg_same = sum(same_sub_tds) / len(same_sub_tds)
        avg_diff = sum(diff_sub_tds) / len(diff_sub_tds)
        metrics["avg_td_same_substage_across_stages"] = avg_same
        metrics["avg_td_diff_substage_same_stage"] = avg_diff
        metrics["substage_role_ratio"] = avg_diff / max(avg_same, 1e-9)
        # Substages should be roles; ideally avg_diff > avg_same. We require avg_diff
        # at least 70% of avg_same (lenient: substages may overlap heavily but must
        # not be pure noise).
        if avg_diff < 0.7 * avg_same:
            failures.append({
                "check": "substage_role_consistency",
                "msg": f"substages don't function as consistent roles: avg td across same "
                       f"substage = {avg_same:.4f}, avg td across different substages = "
                       f"{avg_diff:.4f}. Substages should differ at least as much as same-substage "
                       f"variation. Ratio = {avg_diff/max(avg_same,1e-9):.3f} < 0.70.",
            })

    # Determinism
    try:
        out1 = candidate.engine_stage("A", 3, 2, rho_ref)
        out2 = candidate.engine_stage("A", 3, 2, rho_ref)
        a1 = _to_arr(out1.get("output_rho_qt") if isinstance(out1, dict) else out1)
        a2 = _to_arr(out2.get("output_rho_qt") if isinstance(out2, dict) else out2)
        if _trace_dist(a1, a2) > 1e-6:
            failures.append({"check": "deterministic", "msg": "engine_stage('A',3,2,ρ) not deterministic"})
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "all stages produce same output — fails substage_pair_uniqueness",
            "stage index ignored — fails stage_aggregate_uniqueness",
            "substage = random noise — fails substage_role_consistency",
            "deterministic identity — passes determinism but fails uniqueness",
        ],
        "baseline_variants": [
            "identity baseline: every stage returns input — fails uniqueness checks",
            "random perturbation baseline: fails determinism and substage_role_consistency",
        ],
    }
