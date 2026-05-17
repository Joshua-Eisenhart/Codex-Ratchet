"""phase_32_axis_cliff.py -- seven tangent-direction check.

The earlier version SVD'd the raw state matrix and required the strongest cliff
at position 7. That mixed three effects: the constant density baseline, the
reference-state family, and the engine/stage tangent directions.

This phase now preserves the 64 microstep surface and reports both:
  - raw spectrum: diagnostic only
  - tangent-centered spectrum: subtract the per-reference-state mean before SVD

Pass criterion:
  - centered tangent sigma_7 / sigma_8 >= 1.5 across all substage outputs
  - at least seven nontrivial centered tangent modes
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _flatten_rho(arr):
    a = arr.astype(complex)
    return np.concatenate([a.real.flatten(), a.imag.flatten()])


def _spectrum(M):
    s = np.linalg.svd(M, compute_uv=False)
    ratios = [
        float(s[k] / s[k + 1])
        for k in range(min(14, len(s) - 1))
        if s[k + 1] > 0
    ]
    cliff_pos = int(np.argmax(ratios)) + 1 if ratios else None
    cliff_val = float(max(ratios)) if ratios else None
    return s, ratios, cliff_pos, cliff_val


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "engine_stage"):
        return {"pass": False,
                "failures": [{"check": "engine_stage_exists", "msg": "see Phase 28."}],
                "metrics": metrics}

    try:
        import qutip as qt
    except Exception as e:
        return {"pass": False, "failures": [{"check": "qutip", "msg": str(e)[:160]}], "metrics": metrics}

    np.random.seed(20260513)
    ref_states = []
    for k in range(8):
        amps = [
            (qt.basis(2, 0) + (0.3 + 0.1 * k + 0.05j * (k + 1)) * qt.basis(2, 1)).unit()
            for _ in range(4)
        ]
        ref_states.append(qt.ket2dm(qt.tensor(*amps)))

    grouped_rows = []
    for rho_ref in ref_states:
        ref_rows = []
        for engine in ("A", "B"):
            for s in range(8):
                for sub in range(4):
                    try:
                        r = candidate.engine_stage(engine, s, sub, rho_ref)
                        out = r.get("output_rho_qt") if isinstance(r, dict) else r
                        ref_rows.append(_flatten_rho(_to_arr(out)))
                    except Exception as e:
                        failures.append({"check": f"call_{engine}_{s}_{sub}", "msg": str(e)[:120]})
        if ref_rows:
            grouped_rows.append(np.array(ref_rows))

    rows = [row for group in grouped_rows for row in group]
    if len(rows) < 100:
        return {"pass": False, "failures": failures + [
            {"check": "samples", "msg": f"{len(rows)} samples"}], "metrics": metrics}

    M_raw = np.array(rows)
    raw_s, raw_ratios, raw_cliff_pos, raw_cliff_val = _spectrum(M_raw)

    centered_groups = [group - group.mean(axis=0, keepdims=True) for group in grouped_rows]
    M_tangent = np.vstack(centered_groups)
    tan_s, tan_ratios, tan_cliff_pos, tan_cliff_val = _spectrum(M_tangent)

    metrics["raw_top_15_singular_values"] = [float(x) for x in raw_s[:15]]
    metrics["rows_per_reference"] = int(grouped_rows[0].shape[0]) if grouped_rows else 0
    metrics["total_microstep_rows"] = int(M_raw.shape[0])
    metrics["raw_consecutive_ratios_1_to_14"] = raw_ratios
    metrics["raw_strongest_cliff_position"] = raw_cliff_pos
    metrics["raw_strongest_cliff_value"] = raw_cliff_val
    metrics["raw_ratio_at_position_7"] = raw_ratios[6] if len(raw_ratios) >= 7 else None

    metrics["tangent_top_15_singular_values"] = [float(x) for x in tan_s[:15]]
    metrics["tangent_consecutive_ratios_1_to_14"] = tan_ratios
    metrics["tangent_strongest_cliff_position"] = tan_cliff_pos
    metrics["tangent_strongest_cliff_value"] = tan_cliff_val
    metrics["tangent_ratio_at_position_7"] = tan_ratios[6] if len(tan_ratios) >= 7 else None
    metrics["tangent_nontrivial_modes_eps_0p01"] = int(np.sum(tan_s > 0.01 * tan_s[0])) if len(tan_s) else 0

    if len(tan_ratios) < 7 or tan_ratios[6] < 1.5:
        failures.append({
            "check": "tangent_cliff_at_7_strength",
            "msg": f"centered tangent sigma_7/sigma_8 = {metrics['tangent_ratio_at_position_7']}; "
                   f"need >= 1.5 for seven dominant tangent directions.",
        })

    if metrics["tangent_nontrivial_modes_eps_0p01"] < 7:
        failures.append({
            "check": "tangent_mode_count",
            "msg": f"only {metrics['tangent_nontrivial_modes_eps_0p01']} nontrivial tangent modes at eps=0.01; need at least 7",
        })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "raw cliff at 1 only -- baseline/reference-state variation dominates",
            "centered smooth spectrum -- no privileged tangent count",
            "centered cliff before 7 -- fewer than 7 dominant tangent directions",
            "centered sigma7/sigma8 >= 1.5 -- supports seven tangent directions",
        ],
        "baseline_variants": [
            "identity baseline: centered rank 0/1 -- fails",
            "random axes baseline: centered cliff position unstable",
        ],
    }
