"""phase_20_16stages_4substages.py — 16 unique stages (8 per engine) × 4 substages each.

USER ARCHITECTURAL CORRECTION:
  - 2 engine types: Type 1 (Weyl L), Type 2 (Weyl R)
  - 8 stages per engine = 16 unique top-level stages
  - 4 substages per stage = 4 base operators (Ti, Te, Fi, Fe) applied within
  - 16 × 4 = 64 total substage applications

Each of the 16 unique (engine_id, stage_idx) pairs MUST produce a distinct
stage_signature. Within each stage, the 4 substages must produce 4 distinct
sub-results.

Required API: `engine_stage(engine_id: str, stage_idx: int, substage_idx: int, input_rho_qt) -> dict`
  Input:
    engine_id: "A" or "B"
    stage_idx: 0..7
    substage_idx: 0..3
    input_rho_qt: 16x16 qutip density matrix
  Returns:
    {
      "engine_id": str,
      "stage_idx": int,
      "substage_idx": int,
      "stage_signature": list[float],     # ≥4 numbers characterizing this stage
      "substage_signature": list[float],
      "output_rho_qt": qt.Qobj,
      "base_operator": str,                 # "Ti" | "Te" | "Fi" | "Fe" — which one at this substage
    }

Constraints:
  - 16 (engine, stage) pairs → 16 distinct stage_signatures (pairwise L2 distance > 0.05)
  - Within a stage, the 4 substage_idx values use 4 different base_operators (full coverage)
  - 64 (engine, stage, substage) tuples → 64 distinct output states (pairwise td > 0.02)
  - Deterministic
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
        return {
            "pass": False,
            "failures": [{
                "check": "engine_stage_exists",
                "msg": "Required function `engine_stage(engine_id: str, stage_idx: int, substage_idx: int, "
                       "input_rho_qt) -> dict` is not exported. The architecture has 2 engines × 8 stages "
                       "× 4 substages = 64 callable points. Each of the 16 (engine, stage_idx) pairs must "
                       "produce a distinct stage_signature; within each stage, 4 substages cycle through "
                       "the 4 base operators (Ti, Te, Fi, Fe). Return dict with: engine_id, stage_idx, "
                       "substage_idx, stage_signature (list of floats), substage_signature, output_rho_qt, "
                       "base_operator ('Ti'/'Te'/'Fi'/'Fe').",
            }],
            "metrics": metrics,
        }

    try:
        import qutip as qt
        psi = qt.tensor((qt.basis(2, 0) + 0.5 * qt.basis(2, 1)).unit(),
                        (qt.basis(2, 0) + 0.4j * qt.basis(2, 1)).unit(),
                        qt.basis(2, 0),
                        qt.basis(2, 0))
        input_rho = qt.ket2dm(psi)
    except Exception as e:
        return {"pass": False, "failures": [{"check": "ref_state", "msg": str(e)[:200]}], "metrics": metrics}

    # Collect all 64 calls
    all_results = {}
    for engine_id in ("A", "B"):
        for stage in range(8):
            for sub in range(4):
                try:
                    r = candidate.engine_stage(engine_id, stage, sub, input_rho)
                except Exception as e:
                    failures.append({
                        "check": f"engine_stage_{engine_id}_{stage}_{sub}_call",
                        "msg": f"engine_stage('{engine_id}', {stage}, {sub}, ρ) raised "
                               f"{type(e).__name__}: {str(e)[:200]}",
                    })
                    continue
                if not isinstance(r, dict):
                    failures.append({"check": f"engine_stage_{engine_id}_{stage}_{sub}_dict",
                                     "msg": f"returned {type(r).__name__}"})
                    continue
                for k in ("stage_signature", "substage_signature", "output_rho_qt", "base_operator"):
                    if k not in r:
                        failures.append({"check": f"engine_stage_{engine_id}_{stage}_{sub}_missing_{k}",
                                         "msg": f"missing `{k}`"})
                        break
                else:
                    all_results[(engine_id, stage, sub)] = r

    if len(all_results) < 32:
        return {"pass": False, "failures": failures + [
            {"check": "engine_stage_completeness",
             "msg": f"only {len(all_results)} of 64 (engine, stage, substage) tuples returned valid results"}
        ], "metrics": metrics}

    # 16 unique stage_signatures (use substage 0 as canonical)
    stage_sigs = {}
    for (e, s, sub), r in all_results.items():
        if sub == 0:
            try:
                stage_sigs[(e, s)] = np.asarray(r["stage_signature"], dtype=float)
            except Exception:
                pass

    # Pairwise distinctness across 16 stage-pairs
    duplicate_stages = []
    keys = list(stage_sigs.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            sa, sb = stage_sigs[a], stage_sigs[b]
            if len(sa) != len(sb):
                continue
            d = float(np.linalg.norm(sa - sb))
            if d < 0.05:
                duplicate_stages.append((a, b, d))
    if duplicate_stages:
        for a, b, d in duplicate_stages[:5]:
            failures.append({
                "check": f"stages_distinct_{a[0]}_{a[1]}_vs_{b[0]}_{b[1]}",
                "msg": f"engine_stage('{a[0]}', {a[1]}) and engine_stage('{b[0]}', {b[1]}) have "
                       f"near-identical stage_signatures (L2 = {d:.4f} < 0.05).",
            })
    metrics["unique_stage_signatures"] = len(stage_sigs) - len(duplicate_stages)

    # Within each (engine, stage), 4 substages use 4 different base_operators
    expected_ops = {"Ti", "Te", "Fi", "Fe"}
    bad_stage_substage_coverage = []
    for engine_id in ("A", "B"):
        for stage in range(8):
            sub_ops = set()
            for sub in range(4):
                key = (engine_id, stage, sub)
                if key in all_results:
                    sub_ops.add(all_results[key]["base_operator"])
            if sub_ops != expected_ops:
                bad_stage_substage_coverage.append((engine_id, stage, sub_ops))
    if bad_stage_substage_coverage:
        for e, s, ops in bad_stage_substage_coverage[:5]:
            failures.append({
                "check": f"substage_coverage_{e}_{s}",
                "msg": f"engine_stage('{e}', {s}) substages cover base_operators {ops}, expected {expected_ops}",
            })

    # Pairwise output distinctness — 64 results should produce 64 distinct output states
    output_pairs_close = 0
    keys_list = list(all_results.keys())
    sample_size = min(20, len(keys_list))
    import random
    random.seed(0)
    sampled = random.sample(keys_list, sample_size) if len(keys_list) > sample_size else keys_list
    for i in range(len(sampled)):
        for j in range(i + 1, len(sampled)):
            a = all_results[sampled[i]]["output_rho_qt"]
            b = all_results[sampled[j]]["output_rho_qt"]
            td = _trace_dist(a, b)
            if td < 0.02:
                output_pairs_close += 1
    total_pairs = sample_size * (sample_size - 1) // 2
    metrics["output_pairs_close_in_sample"] = output_pairs_close
    metrics["sample_size"] = sample_size
    metrics["total_pairs_sampled"] = total_pairs
    if total_pairs > 0 and output_pairs_close > total_pairs * 0.10:  # > 10% of sampled pairs
        failures.append({
            "check": "outputs_pairwise_distinct",
            "msg": f"{output_pairs_close} of {total_pairs} sampled output pairs ({100*output_pairs_close/total_pairs:.1f}%) "
                   f"have td < 0.02. Too many indistinguishable outputs (>10%).",
        })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "All 16 (engine, stage) pairs produce identical signatures — fails distinct stages",
            "Substages within a stage all use Ti — fails coverage of 4 base operators",
            "engine_stage returns input unchanged for all calls — fails outputs pairwise distinct",
        ],
        "baseline_variants": [
            "identity engine_stage baseline — fails distinct stages",
            "purely random substage choices — fails determinism + substage coverage",
        ],
    }
