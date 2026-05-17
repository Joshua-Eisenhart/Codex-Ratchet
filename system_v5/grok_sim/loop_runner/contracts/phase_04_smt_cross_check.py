"""phase_04_smt_cross_check.py — independent SMT verification of axis distinguishability.

After Phase 03 confirms `compute_axis_metrics()[AxN] > 0.05` for all 7 axes, this
phase performs INDEPENDENT SMT verification via z3 and cvc5 on the numerical values
returned by the candidate. The runner does the SMT itself — does not trust the
candidate to self-verify.

This catches the iter_63-style cheat where the candidate did its own z3/cvc5
"verification" via `z3.BoolVal(python_bool)` (tautological). The runner's
independent SMT uses `z3.Real` + threshold constraint.

Goal-stability: once green, the per-axis SMT verification is locked. Later
phases assume axis values + SMT agree.
"""
import z3
import cvc5

AXIS_NAMES = ["Ax0", "Ax1", "Ax2", "Ax3", "Ax4", "Ax5", "Ax6"]
THRESHOLD = 0.05


def _z3_axis_check(axis_name: str, td_value: float) -> bool:
    """Fresh z3 solver per axis (no resetAssertions on z3 — it doesn't have that)."""
    s = z3.Solver()
    td_var = z3.Real(f"{axis_name}_td")
    s.add(td_var == td_value)
    s.add(td_var > THRESHOLD)
    return s.check() == z3.sat


def _cvc5_axis_check(axis_name: str, td_value: float, solver) -> bool:
    """Use resetAssertions between axes (cvc5 has this; z3 doesn't)."""
    solver.resetAssertions()
    realSort = solver.getRealSort()
    td_var = solver.mkConst(realSort, f"{axis_name}_td")
    # Encode value as a Rational to avoid float-parsing issues
    int_val = int(round(td_value * 10**10))
    val_term = solver.mkReal(f"{int_val}/10000000000")
    threshold_term = solver.mkReal(f"{int(round(THRESHOLD * 10**10))}/10000000000")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, td_var, val_term))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GT, td_var, threshold_term))
    return solver.checkSat().isSat()


def run(candidate):
    failures = []
    metrics = {"z3_per_axis": {}, "cvc5_per_axis": {}, "axis_tds": {}}

    try:
        axis_values = candidate.compute_axis_metrics()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "compute_axis_metrics_call",
                          "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}],
            "metrics": metrics,
        }

    # z3 check (fresh solver per axis)
    for ax in AXIS_NAMES:
        if ax not in axis_values:
            failures.append({"check": f"smt_axis_missing_{ax}", "msg": f"compute_axis_metrics() missing key `{ax}`"})
            continue
        td = float(axis_values[ax])
        metrics["axis_tds"][ax] = td
        try:
            z3_result = _z3_axis_check(ax, td)
        except Exception as e:
            failures.append({"check": f"z3_check_{ax}",
                             "msg": f"z3 raised {type(e).__name__}: {str(e)[:200]}"})
            continue
        metrics["z3_per_axis"][ax] = z3_result
        if not z3_result:
            failures.append({
                "check": f"z3_unsat_{ax}",
                "msg": f"z3 says {ax} td={td:.4f} does NOT satisfy `td > {THRESHOLD}`. "
                       f"Either the value is below threshold, or encoding mismatch.",
            })

    # cvc5 check (single solver, resetAssertions between axes)
    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LRA")
    for ax in AXIS_NAMES:
        if ax not in axis_values:
            continue
        td = float(axis_values[ax])
        try:
            cvc5_result = _cvc5_axis_check(ax, td, cvc5_solver)
        except Exception as e:
            failures.append({"check": f"cvc5_check_{ax}",
                             "msg": f"cvc5 raised {type(e).__name__}: {str(e)[:200]}"})
            continue
        metrics["cvc5_per_axis"][ax] = cvc5_result
        if not cvc5_result:
            failures.append({
                "check": f"cvc5_unsat_{ax}",
                "msg": f"cvc5 says {ax} td={td:.4f} does NOT satisfy threshold constraint.",
            })

    # Cross-solver agreement
    for ax in AXIS_NAMES:
        z3r = metrics["z3_per_axis"].get(ax)
        c5r = metrics["cvc5_per_axis"].get(ax)
        if z3r is not None and c5r is not None and z3r != c5r:
            failures.append({
                "check": f"smt_disagreement_{ax}",
                "msg": f"z3 says {z3r}, cvc5 says {c5r} for {ax}. Solver encoding bug — "
                       f"likely missing resetAssertions on cvc5 or accumulated constraints.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "z3.BoolVal(python_bool) — tautological; this contract uses z3.Real + threshold instead",
            "cvc5 without resetAssertions — constraints accumulate and become UNSAT",
            "td value lying about its source — value reported but not actually > threshold",
        ],
        "baseline_variants": [
            "all td = 0.0 baseline — every axis fails the SMT check",
            "td just at threshold (0.05) — strict > means UNSAT",
        ],
    }
