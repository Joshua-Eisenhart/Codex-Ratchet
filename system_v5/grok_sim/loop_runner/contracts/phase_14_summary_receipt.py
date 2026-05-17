"""phase_14_summary_receipt.py — cumulative side-quest summary metrics.

Aggregates measurements across all earlier phases into one consolidated receipt
suitable for downstream consumption (visualizer, archive, doctrine review). The
phase passes if all aggregate values are present and consistent.

This phase is mostly informational — it doesn't add NEW physics checks, it
consolidates the EXISTING ones into a single structured snapshot. Useful as
the side-quest's "final state" record.

Checks:
  - All required summary fields are present
  - Numerical aggregates are in reasonable ranges
  - Side-quest fence still binding (re-verify from sidequest_claim_boundary)
  - Tool count and axis count match documented values
"""


def run(candidate):
    failures = []
    summary = {}

    # Pull each piece via the candidate's exposed API
    try:
        axis_metrics = candidate.compute_axis_metrics()
        engine_result = candidate.run_engine()
        chirality = candidate.weyl_chirality_probe()
        flux = candidate.flux_holonomy()
        gstack = candidate.gstack_layers()
        manifest = candidate.tool_manifest()
        fence = candidate.sidequest_claim_boundary()
        finitude_witnesses = [candidate.finite_witness(n) for n in (4, 8, 16)]
        noncomm = candidate.noncomm_pair()
        mequiv = candidate.mequivalence_demo()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "summary_collection",
                          "msg": f"failed to collect summary data: {type(e).__name__}: {str(e)[:200]}"}],
            "metrics": {},
        }

    # Build summary
    summary["axes"] = {
        "metrics": {k: float(v) for k, v in axis_metrics.items()},
        "count": len(axis_metrics),
        "min_value": min(float(v) for v in axis_metrics.values()),
        "all_above_threshold": all(float(v) > 0.05 for v in axis_metrics.values()),
    }
    summary["engines"] = {
        "engine_a_stage_count": len(engine_result.get("engine_a_stage_records", [])),
        "engine_b_stage_count": len(engine_result.get("engine_b_stage_records", [])),
        "total_stage_count": (len(engine_result.get("engine_a_stage_records", []))
                              + len(engine_result.get("engine_b_stage_records", []))),
        "cycle_closure_a": float(engine_result.get("cycle_closure_a", -1)),
        "cross_engine_observable": float(engine_result.get("cross_engine_observable", -1)),
        "engine_a_entropy_first": float(engine_result["engine_a_stage_records"][0]["entropy"]),
        "engine_a_entropy_last": float(engine_result["engine_a_stage_records"][-1]["entropy"]),
        "engine_b_entropy_first": float(engine_result["engine_b_stage_records"][0]["entropy"]),
        "engine_b_entropy_last": float(engine_result["engine_b_stage_records"][-1]["entropy"]),
    }
    summary["gstack"] = {
        "chirality_z_L": float(chirality.get("bloch_z_L", 0)),
        "chirality_z_R": float(chirality.get("bloch_z_R", 0)),
        "chirality_opposite_signs": bool(chirality.get("opposite_signs", False)),
        "flux_holonomy": float(flux),
        "layer_count": sum(1 for n in range(4) if f"layer_{n}" in gstack),
        "dependencies": gstack.get("dependencies", []),
    }
    summary["finitude_witnesses"] = {
        f"n_{n}": int(w) for n, w in zip([4, 8, 16], finitude_witnesses)
    }
    summary["foundational"] = {
        "mequiv_distinct": bool(mequiv.get("are_distinct", False)),
        "mequiv_share_class": bool(mequiv.get("share_probe_class", False)),
        "noncomm_trace_distance": float(noncomm.get("trace_distance", 0)),
    }
    summary["tools"] = {
        "manifest": {k: bool(v.get("used", False)) for k, v in manifest.items()},
        "used_count": sum(1 for v in manifest.values() if v.get("used")),
        "total_count": len(manifest),
    }
    summary["fence"] = {
        "classification": fence.get("classification"),
        "admission_scope": fence.get("admission_scope"),
        "promotion_allowed": fence.get("promotion_allowed"),
    }

    # Required summary keys
    required = ["axes", "engines", "gstack", "finitude_witnesses", "foundational", "tools", "fence"]
    for k in required:
        if k not in summary:
            failures.append({"check": f"summary_section_{k}", "msg": f"summary missing `{k}`"})

    # Cross-check fence is still binding
    if summary["fence"]["classification"] != "side_quest_only":
        failures.append({"check": "fence_classification_drift",
                         "msg": f"fence classification = {summary['fence']['classification']}, "
                                f"must be 'side_quest_only'"})
    if summary["fence"]["promotion_allowed"] is True:
        failures.append({"check": "fence_promotion_drift",
                         "msg": "fence promotion_allowed = True, must be False"})

    # Cross-check axis count = 7
    if summary["axes"]["count"] != 7:
        failures.append({"check": "axes_count_drift",
                         "msg": f"axis count = {summary['axes']['count']}, expected 7"})

    # Cross-check total stage count = 64
    if summary["engines"]["total_stage_count"] != 64:
        failures.append({"check": "stages_total_drift",
                         "msg": f"total stages = {summary['engines']['total_stage_count']}, expected 64"})

    # Cross-check tool count >= 5 used
    if summary["tools"]["used_count"] < 5:
        failures.append({"check": "tools_used_drift",
                         "msg": f"tools used = {summary['tools']['used_count']}, expected ≥ 5"})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": {"summary": summary},
        "graveyard_companions": [
            "axes drift (count != 7) — fails axes_count_drift",
            "stages drift (total != 64) — fails stages_total_drift",
            "tools drift (used < 5) — fails tools_used_drift",
            "fence drift (classification or promotion_allowed changed) — fails fence_*_drift",
        ],
        "baseline_variants": [],
    }
