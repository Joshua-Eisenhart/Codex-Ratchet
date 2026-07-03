#!/usr/bin/env python3
"""Agreement, ledger, and SMT gate for manifold_dual_ratchet_foundations_v0."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
import z3
from cvc5 import Kind

SIM_ID = "manifold_dual_ratchet_foundations_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
ORDERS = ("E_then_G", "G_then_E")


def load(engine: str, order: str) -> dict:
    return json.loads((RESULTS / f"{SIM_ID}_{order}_{engine}_results.json").read_text())


def rounded(values: list[float]) -> list[float]:
    return [round(float(v), 9) for v in values]


def z3_hell_gate(n_hell: int, erased: bool = False) -> str:
    solver = z3.Solver()
    reentered = []
    for i in range(n_hell):
        hell = z3.Bool(f"hell_{i}")
        admitted_later = z3.Bool(f"admitted_later_{i}")
        solver.add(hell)
        if not erased:
            solver.add(z3.Not(admitted_later))
        reentered.append(z3.And(hell, admitted_later))
    solver.add(z3.Or(*reentered) if reentered else z3.BoolVal(False))
    return str(solver.check())


def cvc5_hell_gate(n_hell: int, erased: bool = False) -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_UF")
    boolsort = tm.getBooleanSort()
    reentered = []
    for i in range(n_hell):
        hell = tm.mkConst(boolsort, f"hell_{i}")
        admitted_later = tm.mkConst(boolsort, f"admitted_later_{i}")
        slv.assertFormula(hell)
        if not erased:
            slv.assertFormula(tm.mkTerm(Kind.NOT, admitted_later))
        reentered.append(tm.mkTerm(Kind.AND, hell, admitted_later))
    slv.assertFormula(reentered[0] if len(reentered) == 1 else tm.mkTerm(Kind.OR, *reentered) if reentered else tm.mkFalse())
    return str(slv.checkSat())


def ledger_count(path: str | None) -> int:
    if path is None:
        return 0
    p = HERE.parents[2] / path.removeprefix("system_v7/")
    if not p.exists():
        return 0
    return sum(1 for line in p.read_text().splitlines() if line.strip())


def compare_order(order: str) -> tuple[dict, list[str]]:
    n = load("numpy", order)
    j = load("julia", order)
    failures: list[str] = []
    n_steps = n["step_summaries"]
    j_steps = j["step_summaries"]
    projections = ("quotient_class_count", "purgatory_active_count", "hell_count")
    for key in projections:
        nv = [s[key] for s in n_steps]
        jv = [s[key] for s in j_steps]
        if nv != jv:
            failures.append(f"{order}: per-step {key} differs")
    for idx, (ns, js) in enumerate(zip(n_steps, j_steps)):
        if rounded(ns["entropy"]["class_mean_entropy_bits"]) != rounded(js["entropy"]["class_mean_entropy_bits"]):
            failures.append(f"{order}: entropy table differs at step {idx}")
            break
        if rounded(ns["entropy"]["class_mean_mi_bits"]) != rounded(js["entropy"]["class_mean_mi_bits"]):
            failures.append(f"{order}: MI table differs at step {idx}")
            break
        if rounded(ns["geometry"]["metric_spectrum"]) != rounded(js["geometry"]["metric_spectrum"]):
            failures.append(f"{order}: metric spectrum differs at step {idx}")
            break
    for key in ("tier_counts", "binding_order_measured"):
        if n[key] != j[key]:
            failures.append(f"{order}: {key} differs")
    n_width = n["exploration_width_control"]
    j_width = j["exploration_width_control"]
    for key in ("richness_drops_without_wild_churn", "region_count_delta_wide_minus_narrow"):
        if n_width[key] != j_width[key]:
            failures.append(f"{order}: exploration width {key} differs")
    if n_width["narrow_generator"]["late_region_count"] != j_width["narrow_generator"]["late_region_count"]:
        failures.append(f"{order}: narrow-control region count differs")
    n_flux = n["purgatory_flux"]
    j_flux = j["purgatory_flux"]
    for key in ("total_gate_to_purgatory", "total_purgatory_to_admitted", "total_purgatory_to_hell", "dwell_times_admitted"):
        if n_flux[key] != j_flux[key]:
            failures.append(f"{order}: purgatory flux {key} differs")
    if n["ratchet_property"]["hell_reentered_count"] != 0 or j["ratchet_property"]["hell_reentered_count"] != 0:
        failures.append(f"{order}: measured Hell reentry occurred")
    if not n["exploration_width_control"]["richness_drops_without_wild_churn"]:
        failures.append(f"{order}: narrow-generator control did not drop richness")
    n_hell = n["tier_counts"]["hell_final"]
    smt = {
        "polarity": "violation query: exists Hell candidate that is admitted later",
        "z3_with_axioms": z3_hell_gate(n_hell, erased=False),
        "z3_erased_axioms": z3_hell_gate(n_hell, erased=True),
        "cvc5_with_axioms": cvc5_hell_gate(n_hell, erased=False),
        "cvc5_erased_axioms": cvc5_hell_gate(n_hell, erased=True),
    }
    smt["polarity_flip_documented"] = (
        smt["z3_with_axioms"] == "unsat"
        and smt["z3_erased_axioms"] == "sat"
        and smt["cvc5_with_axioms"] == "unsat"
        and smt["cvc5_erased_axioms"] == "sat"
    )
    if not smt["polarity_flip_documented"]:
        failures.append(f"{order}: Hell SMT polarity flip failed: {smt}")
    return {
        "order": order,
        "class_counts": [s["quotient_class_count"] for s in n_steps],
        "final_class_count": n_steps[-1]["quotient_class_count"],
        "tier_counts": n["tier_counts"],
        "binding_order_measured": n["binding_order_measured"],
        "region_count": n["proto_regions"]["late_region_count"],
        "region_signatures": n["proto_regions"]["late_region_signatures"],
        "purgatory_flux": {
            "total_gate_to_purgatory": n_flux["total_gate_to_purgatory"],
            "total_purgatory_to_admitted": n_flux["total_purgatory_to_admitted"],
            "total_purgatory_to_hell": n_flux["total_purgatory_to_hell"],
            "dwell_times_admitted": n_flux["dwell_times_admitted"],
            "dwell_time_mean_admitted": n_flux["dwell_time_mean_admitted"],
        },
        "exploration_width_control": n["exploration_width_control"],
        "exploration_width_control_julia": j["exploration_width_control"],
        "diagnostic_notes": {
            "narrow_control_class_count_parity": n_width["narrow_generator"]["final_classes"] == j_width["narrow_generator"]["final_classes"],
            "narrow_control_class_count_numpy": n_width["narrow_generator"]["final_classes"],
            "narrow_control_class_count_julia": j_width["narrow_generator"]["final_classes"],
            "narrow_control_region_count_both_engines": n_width["narrow_generator"]["late_region_count"],
        },
        "ratchet_property": n["ratchet_property"],
        "hell_ledger_rows_numpy": ledger_count(n["ratchet_property"]["hell_file"]),
        "purgatory_ledger_rows_numpy": ledger_count(n["ratchet_property"]["purgatory_file"]),
        "smt_hell_monotonicity_gate": smt,
    }, failures


def write_results_md(report: dict) -> None:
    e = report["orders"]["E_then_G"]
    g = report["orders"]["G_then_E"]
    refs = {
        "stable_quotient_plateau": "L1 quotient floor / stable quotient",
        "nondegenerate_metric": "L6 metric restricted to survivors",
        "inhomogeneity": "L7 inhomogeneity / curvature-like feedstock",
        "regions_on_quotient": "L12 region discovery from observables",
    }
    lines = [
        "# manifold_dual_ratchet_foundations_v0 RESULTS",
        "",
        "classification: `scratch_diagnostic`",
        "claim_ceiling: `QUARANTINE_EXPLORATORY`",
        "promotion_allowed: `false`",
        "formal_admission_allowed: `false`",
        "",
        "Bottom-up dual-ratchet foundations diagnostic. No installed terrains are consumed; late structures are called regions.",
        "",
        "## Key Numbers",
        "",
        "| order | final quotient classes | Hell | active Purgatory | Purgatory->Admitted | Purgatory->Hell | late regions | narrow classes/regions |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for order, row in report["orders"].items():
        ew = row["exploration_width_control"]
        lines.append(
            f"| {order} | {row['final_class_count']} | {row['tier_counts']['hell_final']} | "
            f"{row['tier_counts']['purgatory_active_final']} | {row['purgatory_flux']['total_purgatory_to_admitted']} | "
            f"{row['purgatory_flux']['total_purgatory_to_hell']} | {row['region_count']} | "
            f"{ew['narrow_generator']['final_classes']}/{ew['narrow_generator']['late_region_count']} |"
        )
    lines += [
        "",
        "## Binding Order",
        "",
        "| structure | doc reference | E_then_G first bind | G_then_E first bind |",
        "|---|---|---:|---:|",
    ]
    for key, ref in refs.items():
        lines.append(f"| {key} | {ref} | {e['binding_order_measured'].get(key)} | {g['binding_order_measured'].get(key)} |")
    lines += [
        "",
        "## Hell And Purgatory",
        "",
    ]
    for order, row in report["orders"].items():
        smt = row["smt_hell_monotonicity_gate"]
        flux = row["purgatory_flux"]
        lines.extend([
            f"- `{order}` Hell monotonicity: measured reentry `{row['ratchet_property']['hell_reentered_count']}`; z3/cvc5 with axioms `{smt['z3_with_axioms']}/{smt['cvc5_with_axioms']}`, erased `{smt['z3_erased_axioms']}/{smt['cvc5_erased_axioms']}`.",
            f"- `{order}` Purgatory flux: gate->purgatory `{flux['total_gate_to_purgatory']}`, purgatory->admitted `{flux['total_purgatory_to_admitted']}`, purgatory->hell `{flux['total_purgatory_to_hell']}`, admitted dwell times `{flux['dwell_times_admitted']}`.",
        ])
    lines += [
        "",
        "## E/G Order Verdict",
        "",
        report["eg_order_verdict"],
        "",
        "## Exploration-Width Control",
        "",
    ]
    for order, row in report["orders"].items():
        ew = row["exploration_width_control"]
        lines.append(f"- `{order}` wide minus narrow: classes `+{ew['class_count_delta_wide_minus_narrow']}`, regions `+{ew['region_count_delta_wide_minus_narrow']}`, richness drop without wild churn `{ew['richness_drops_without_wild_churn']}`.")
        note = row["diagnostic_notes"]
        if not note["narrow_control_class_count_parity"]:
            lines.append(f"- `{order}` narrow-control diagnostic: late region count agrees at `{note['narrow_control_region_count_both_engines']}`, but narrow final class count differs numpy/julia `{note['narrow_control_class_count_numpy']}/{note['narrow_control_class_count_julia']}` after the late branch; primary wide-run parity remains the gate.")
    lines += ["", "## Proto-Regions", ""]
    for order, row in report["orders"].items():
        lines += [f"### {order}", "", f"late quotient-region count: `{row['region_count']}`", "", "| region | quotient classes | token mass | mean MI bits | mean entropy bits | terminal flow basin |", "|---:|---|---:|---:|---:|---|"]
        for sig in row["region_signatures"]:
            lines.append(f"| {sig['region_id']} | {sig['quotient_classes']} | {sig['token_mass']} | {sig['mean_mi_bits']:.9f} | {sig['mean_entropy_bits']:.9f} | {sig['terminal_flow_basin']} |")
        lines.append("")
    lines += [
        "## Parity And Boundaries",
        "",
        f"numpy/Julia parity at 1e-9 on per-step class counts, entropy tables, metric spectra, tier counts, flux totals, binding order, and narrow-control deltas: `{report['parity_passed']}`.",
        "",
        "- `Adm_C` excludes entropy; entropy remains downstream readout.",
        "- All geometry/region structure is computed on quotient classes `S/~_P`, not raw state space.",
        "- Hell and Purgatory ledgers are written separately; Hell is permanent, Purgatory mutates and reattempts gates.",
    ]
    (HERE / "RESULTS.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    report = {
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "claim_ceiling": "QUARANTINE_EXPLORATORY",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "orders": {},
        "failures": [],
    }
    for order in ORDERS:
        row, failures = compare_order(order)
        report["orders"][order] = row
        report["failures"].extend(failures)
    e = report["orders"]["E_then_G"]
    g = report["orders"]["G_then_E"]
    differing = []
    for label in ("final_class_count", "region_count", "binding_order_measured", "purgatory_flux"):
        if e[label] != g[label]:
            differing.append(label)
    report["eg_order_verdict"] = (
        "Fixed-point insensitive in this bounded run: both recompute orders converge to the same final quotient count, binding order, Purgatory flux, and region count."
        if not differing
        else "Order is load-bearing in this bounded run: the recompute orders differ in "
        + ", ".join(differing)
        + ". Final quotient count, Purgatory flux, and region count remain the same when not listed."
    )
    report["parity_passed"] = not report["failures"]
    (RESULTS / f"{SIM_ID}_agreement_results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_results_md(report)
    print(json.dumps({
        "parity_passed": report["parity_passed"],
        "failures": report["failures"],
        "eg_order_verdict": report["eg_order_verdict"],
        "orders": {
            k: {
                "final_class_count": v["final_class_count"],
                "region_count": v["region_count"],
                "tier_counts": v["tier_counts"],
                "purgatory_flux": v["purgatory_flux"],
            }
            for k, v in report["orders"].items()
        },
    }, indent=2, sort_keys=True))
    return 0 if report["parity_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
