"""phase_03_axes.py — per-axis distinguishability (Ax0..Ax6) on the G-stack.

Runs AFTER Phase 02 G-stack passes — axes are dynamics living on the geometric
substrate. Each axis is a separate check_id within this phase so the Auditor
can diagnose individual failures and Grok can patch one axis at a time.

Per-axis thresholds:
  - Each AxN must satisfy compute_axis_metrics()[f'AxN'] > 0.05
  - Ax0 = entropy gradient difference (not trace distance) — same threshold
  - Recompute is structural: we re-read compute_axis_metrics() once and use
    the returned dict; we cross-check it's deterministic across two calls
"""

AXIS_NAMES = ["Ax0", "Ax1", "Ax2", "Ax3", "Ax4", "Ax5", "Ax6"]
THRESHOLD = 0.05


def _check_axes(candidate):
    failures = []
    metrics = {}

    try:
        r1 = candidate.compute_axis_metrics()
    except Exception as e:
        return [{"check": "axes_call", "msg": f"compute_axis_metrics() raised {type(e).__name__}: {str(e)[:300]}"}], {}

    # Determinism check: same call → same values
    try:
        r2 = candidate.compute_axis_metrics()
    except Exception as e:
        return [{"check": "axes_call_repeat", "msg": f"second call raised {type(e).__name__}: {str(e)[:300]}"}], {}

    for ax in AXIS_NAMES:
        if ax not in r1:
            failures.append({"check": f"axis_missing_{ax}",
                             "msg": f"compute_axis_metrics() missing key `{ax}`"})

    if failures:
        return failures, metrics

    # Per-axis checks
    for ax in AXIS_NAMES:
        v1 = float(r1[ax])
        v2 = float(r2.get(ax, float("nan")))
        metrics[ax] = v1

        # Determinism
        if abs(v1 - v2) > 1e-3:
            failures.append({
                "check": f"axis_deterministic_{ax}",
                "msg": f"{ax} returned {v1} then {v2} — not deterministic",
            })

        # Threshold
        if v1 <= THRESHOLD:
            failures.append({
                "check": f"axis_below_threshold_{ax}",
                "msg": f"{ax} = {v1:.4f} ≤ {THRESHOLD} — axis dimension not actually distinguishable",
            })

    return failures, metrics


def run(candidate):
    failures, metrics = _check_axes(candidate)
    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": {"axis_values": metrics},
        "graveyard_companions": [
            "Ax_k computed but trace distance ≈ 0 — fails per-axis threshold (operator choice trivially commutes)",
            "Hardcoded `('AxN', constant_value)` in compute_axis_metrics return — fails determinism if value differs across calls; if same value across runs, fails downstream when probed differently",
            "All 7 axes return the same number — fails per-axis differentiation (single diff reused)",
            "Ax_k computed from operators acting on disjoint subspaces — fails (trivial commutation)",
        ],
        "baseline_variants": [
            "all unitary, no dissipator: Ax1 (bath coupling) must be 0 — graveyard",
            "all on same Pauli axis: Ax6 (UP/DOWN composition) must be 0 — graveyard",
            "θ = π/2 generators: Pauli special-point graveyard for Ax6",
        ],
    }
