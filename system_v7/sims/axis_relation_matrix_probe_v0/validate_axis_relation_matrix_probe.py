#!/usr/bin/env python3
"""Validate numpy/Julia parity and write RESULTS.md for axis_relation_matrix_probe_v0."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
TOL = 1e-9
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing parity artifact reads and validator result serialization"},
    "markdown": {"tried": True, "used": True, "reason": "supportive human-readable RESULTS.md emission"},
}
TOOL_INTEGRATION_DEPTH = {"json": "load_bearing", "markdown": "supportive"}


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def relation_keyed(result: dict) -> dict:
    return {tuple(row["pair"]): row for row in result["relation_matrix"]}


def compare(numpy_result: dict, julia_result: dict) -> dict:
    diffs = []
    nrel = relation_keyed(numpy_result)
    jrel = relation_keyed(julia_result)
    for pair in sorted(nrel):
        for field in ("nmi", "corr", "null95_nmi", "null95_abs_corr"):
            diff = abs(float(nrel[pair][field]) - float(jrel[pair][field]))
            if diff > TOL:
                diffs.append({"pair": list(pair), "field": field, "diff": diff})
        if nrel[pair]["verdict"] != jrel[pair]["verdict"]:
            diffs.append({"pair": list(pair), "field": "verdict", "numpy": nrel[pair]["verdict"], "julia": jrel[pair]["verdict"]})
    return {
        "parity_abs_tol": TOL,
        "parity_pass": not diffs,
        "diffs": diffs,
    }


def verdict_counts(result: dict) -> dict:
    counts = {"law": 0, "dependent": 0, "independent": 0, "undefinable": 1}
    for row in result["relation_matrix"]:
        if row["verdict"] == "dependent_above_95pct_null":
            counts["dependent"] += 1
        else:
            counts["independent"] += 1
    if result["laws"]["b6_equals_minus_b0_times_b3"]["holds"]:
        counts["law"] += 1
    return counts


def md_table(result: dict) -> str:
    lines = ["| pair | n | NMI | corr | null95 NMI | null95 abs corr | verdict |", "|---|---:|---:|---:|---:|---:|---|"]
    for row in result["relation_matrix"]:
        lines.append(
            "| {pair} | {n} | {nmi:.6f} | {corr:.6f} | {null_nmi:.6f} | {null_corr:.6f} | {verdict} |".format(
                pair="-".join(row["pair"]),
                n=row["n"],
                nmi=row["nmi"],
                corr=row["corr"],
                null_nmi=row["null95_nmi"],
                null_corr=row["null95_abs_corr"],
                verdict=row["verdict"],
            )
        )
    return "\n".join(lines)


def write_results(numpy_result: dict, julia_result: dict, parity: dict) -> None:
    stress = numpy_result["conflation_stress_test"]
    branch_reach = numpy_result["a1_branch_a5_reachability"]
    laws = numpy_result["laws"]
    above = [r for r in numpy_result["relation_matrix"] if r["verdict"] == "dependent_above_95pct_null"]
    relation_by_pair = relation_keyed(numpy_result)
    a1_branch_a5 = relation_by_pair[("a1_branch", "a5")]
    a1_opchar_a5 = relation_by_pair[("a1_opchar", "a5")]
    branch_verdict = (
        "trap confirmed; algebra orthogonality upheld at this depth"
        if a1_branch_a5["verdict"] == "independent_at_this_depth"
        else "genuine undocumented relation candidate; flag for discriminator sim"
    )
    counts = verdict_counts(numpy_result)
    lines = [
        "# axis_relation_matrix_probe_v0 RESULTS",
        "",
        "v0.1: terrain-branch A1 re-extraction applied.",
        "",
        "classification: `scratch_diagnostic`",
        "claim_ceiling: `QUARANTINE_EXPLORATORY`",
        "promotion_allowed: `false`",
        "formal_admission_allowed: `false`",
        "",
        "## Readout Scope",
        "",
        f"Rows: {numpy_result['readout_row_count']} = 8 Type-1 stages across both traversals x {numpy_result['probe_state_count']} fixed probe states.",
        "",
        "- a1_branch: terrain-branch kernel, chi1(Se)=chi1(Ni)=+1 and chi1(Ne)=chi1(Si)=-1.",
        "- a1_opchar: legacy comparison proxy only, Fi/Fe unitary=1 and Ti/Te proper CPTP/GKSL=0; this overlaps a5 and is not A1.",
        "- a2: terrain frame, Ni/Si conjugated=1 and Se/Ne direct=0.",
        "- a4: traversal order, outer/deductive=0 and inner/inductive=1.",
        "- a5: operator family, F=1 and T=0.",
        "- a6: local precedence, operator-first `terrain_after_operator`=1 and terrain-first `operator_after_terrain`=0.",
        "- b0: sign of probe-state `r_z`; zero is retained as 0 and excluded from b6 rows.",
        "- b3: chart-role loop, outer=+1 and inner=-1.",
        "- b6: derived only where b0 is nonzero as `-b0*b3`.",
        "- a0: undefinable here because Xi/cut bridge or an admitted a0 proxy is not present.",
        "",
        "## Laws",
        "",
        f"- b6 = -b0*b3: `{laws['b6_equals_minus_b0_times_b3']['holds']}` over {laws['b6_equals_minus_b0_times_b3']['defined_rows']} defined rows.",
        f"- a0 = a1_branch XOR a2: `{laws['a0_equals_a1_xor_a2']['status']}`.",
        "",
        "## Relation Matrix",
        "",
        md_table(numpy_result),
        "",
        "## A1/A5 Caveat Re-Test",
        "",
        f"Reachable (a1_branch, a5) combinations: {branch_reach['reachable_combination_count']} / {branch_reach['possible_combination_count']}.",
        f"Reachable combinations: `{branch_reach['reachable_combinations']}`.",
        f"a1_branch-a5: n={a1_branch_a5['n']}, NMI={a1_branch_a5['nmi']:.6f}, corr={a1_branch_a5['corr']:.6f}, null95 NMI={a1_branch_a5['null95_nmi']:.6f}, null95 abs corr={a1_branch_a5['null95_abs_corr']:.6f}, verdict=`{a1_branch_a5['verdict']}`.",
        f"a1_opchar-a5 comparison: n={a1_opchar_a5['n']}, NMI={a1_opchar_a5['nmi']:.6f}, corr={a1_opchar_a5['corr']:.6f}, verdict=`{a1_opchar_a5['verdict']}`.",
        "",
        f"Verdict: {branch_verdict}.",
        "",
        "## Conflation Stress Test",
        "",
        f"Reachable (a4, a6, b3) combinations: {stress['reachable_combination_count']} / {stress['possible_combination_count']}.",
        f"Reachable combinations: `{stress['reachable_combinations']}`.",
        "",
        "Verdict: fewer than 8 combinations are reachable. In this built Type-1 chart, a4 and b3 are structurally coupled by the outer/deductive and inner/inductive assignment; a6 remains separately realized across both loops.",
        "",
        "## SMT Gate",
        "",
        f"Above-null relation pairs gated: `{[r['pair'] for r in above]}`.",
        f"SMT status: `{numpy_result['dual_smt_gate']['status']}`.",
        "",
        "## Parity",
        "",
        f"numpy/Julia parity at 1e-9: `{parity['parity_pass']}`.",
        f"Parity diffs: `{parity['diffs']}`.",
        "",
        "## Honest Verdict Counts",
        "",
        f"- law: {counts['law']}",
        f"- dependent above 95% null: {counts['dependent']}",
        f"- independent at this depth: {counts['independent']}",
        f"- undefinable: {counts['undefinable']}",
        "",
        "Generated: " + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    ]
    (RESULTS / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    numpy_result = load("axis_relation_matrix_probe_numpy_results.json")
    julia_result = load("axis_relation_matrix_probe_julia_results.json")
    parity = compare(numpy_result, julia_result)
    validator = {
        "schema": "codex_ratchet.axis_relation_matrix_probe_v0.validator.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": classification,
        "claim_ceiling": "QUARANTINE_EXPLORATORY",
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "parity": parity,
        "all_pass": parity["parity_pass"],
    }
    (RESULTS / "axis_relation_matrix_probe_validator_results.json").write_text(json.dumps(validator, indent=2, sort_keys=True), encoding="utf-8")
    write_results(numpy_result, julia_result, parity)
    print(json.dumps({
        "validator_path": str(RESULTS / "axis_relation_matrix_probe_validator_results.json"),
        "results_md": str(RESULTS / "RESULTS.md"),
        "parity_pass": parity["parity_pass"],
        "diff_count": len(parity["diffs"]),
    }, indent=2))


if __name__ == "__main__":
    main()
