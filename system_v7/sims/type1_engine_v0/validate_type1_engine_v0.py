#!/usr/bin/env python3
"""Parity validator and report writer for Type-1 engine v0."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import type1_engine_common as common


SIM_ID = common.SIM_ID
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
ATOL = 1e-9


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_result(engine: str) -> dict[str, Any]:
    return json.loads((RESULTS / f"{SIM_ID}_{engine}_results.json").read_text(encoding="utf-8"))


def numeric_close(a: float, b: float, atol: float = ATOL) -> bool:
    return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a) - float(b)) <= atol


def compare_numbers(path: str, a: Any, b: Any, failures: list[str], max_diff: dict[str, Any]) -> None:
    if isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            failures.append(f"{path}: bool mismatch {a!r} vs {b!r}")
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        diff = abs(float(a) - float(b))
        if diff > max_diff["value"]:
            max_diff["value"] = diff
            max_diff["path"] = path
        if not numeric_close(float(a), float(b)):
            failures.append(f"{path}: {a!r} vs {b!r} diff={diff}")
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            failures.append(f"{path}: list length mismatch {len(a)} vs {len(b)}")
            return
        for idx, (av, bv) in enumerate(zip(a, b)):
            compare_numbers(f"{path}[{idx}]", av, bv, failures, max_diff)
        return
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            failures.append(f"{path}: dict keys mismatch")
            return
        for key in sorted(a):
            compare_numbers(f"{path}.{key}", a[key], b[key], failures, max_diff)
        return
    if a != b:
        failures.append(f"{path}: value mismatch {a!r} vs {b!r}")


def compare_stage_fingerprints(numpy_result: dict[str, Any], julia_result: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    max_diff = {"value": 0.0, "path": None}
    nfp = numpy_result["stage_fingerprints"]
    jfp = julia_result["stage_fingerprints"]
    if set(nfp) != set(jfp):
        failures.append("stage_fingerprints: stage id sets differ")
        return failures, max_diff
    for sid in sorted(nfp):
        for key in ("affine_A", "affine_b", "entropy_injected", "fixed_point_bloch", "fixed_point_residual"):
            compare_numbers(f"stage_fingerprints.{sid}.{key}", nfp[sid][key], jfp[sid][key], failures, max_diff)
    return failures, max_diff


def compare_order_sensitivity(numpy_result: dict[str, Any], julia_result: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    max_diff = {"value": 0.0, "path": None}
    compare_numbers(
        "order_sensitivity_by_terrain",
        numpy_result["order_sensitivity_by_terrain"],
        julia_result["order_sensitivity_by_terrain"],
        failures,
        max_diff,
    )
    return failures, max_diff


def compare_traversals(numpy_result: dict[str, Any], julia_result: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    max_diff = {"value": 0.0, "path": None}
    for traversal in ("outer", "inner", "double_outer_then_inner"):
        n_states = numpy_result["traversals"][traversal]["per_initial_state"]
        j_states = julia_result["traversals"][traversal]["per_initial_state"]
        if set(n_states) != set(j_states):
            failures.append(f"traversals.{traversal}: initial state sets differ")
            continue
        for pname in sorted(n_states):
            for key in ("trajectory", "closure_norm", "final_minus_initial_bloch"):
                compare_numbers(
                    f"traversals.{traversal}.{pname}.{key}",
                    n_states[pname][key],
                    j_states[pname][key],
                    failures,
                    max_diff,
                )
    return failures, max_diff


def headline_numbers(result: dict[str, Any]) -> dict[str, Any]:
    order = result["order_sensitivity_by_terrain"]
    traversals = result["traversals"]
    return {
        "min_pairwise_distance": result["distinctness"]["min_pairwise_distance"],
        "min_pair": result["distinctness"]["min_pair"],
        "order_sensitivity_max_by_terrain": {k: v["max_norm"] for k, v in order.items()},
        "closure_mean": {k: v["closure_summary"]["mean"] for k, v in traversals.items()},
        "closure_max": {k: v["closure_summary"]["max"] for k, v in traversals.items()},
    }


def validate() -> dict[str, Any]:
    numpy_result = load_result("numpy")
    julia_result = load_result("julia")
    failures: list[str] = []

    for name, result in (("numpy", numpy_result), ("julia", julia_result)):
        if result.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification is not scratch_diagnostic")
        if result.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed is not false")
        if result.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: formal_admission_allowed is not false")
        if result.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result is not false")
        if result["distinctness"]["all_8_distinct"] is not True:
            failures.append(f"{name}: all_8_distinct is not true")

    fp_failures, fp_diff = compare_stage_fingerprints(numpy_result, julia_result)
    os_failures, os_diff = compare_order_sensitivity(numpy_result, julia_result)
    tr_failures, tr_diff = compare_traversals(numpy_result, julia_result)
    failures.extend(fp_failures)
    failures.extend(os_failures)
    failures.extend(tr_failures)

    max_diff = max((fp_diff, os_diff, tr_diff), key=lambda x: x["value"])
    raw_case_disagreements = [
        row for row in common.build_casing_cross_check() if not row["raw_case_agree"]
    ]
    normalized_case_disagreements = [
        row for row in common.build_casing_cross_check() if not row["normalized_agree"]
    ]

    report = {
        "schema": "codex_ratchet.type1_engine_v0.validator_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "claim_ceiling": "QUARANTINE_EXPLORATORY",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_file(Path(__file__)),
        "engines": ["numpy", "julia"],
        "parity_tolerance": ATOL,
        "parity_pass": len(failures) == 0,
        "max_abs_diff": max_diff["value"],
        "max_abs_diff_path": max_diff["path"],
        "fingerprint_parity_pass": not fp_failures,
        "order_sensitivity_parity_pass": not os_failures,
        "traversal_parity_pass": not tr_failures,
        "distinctness_pass": numpy_result["distinctness"]["all_8_distinct"] and julia_result["distinctness"]["all_8_distinct"],
        "headline_numbers": headline_numbers(numpy_result),
        "casing_cross_check": {
            "rows": common.build_casing_cross_check(),
            "raw_case_disagreements": raw_case_disagreements,
            "normalized_case_disagreements": normalized_case_disagreements,
            "all_normalized_agree": len(normalized_case_disagreements) == 0,
            "all_raw_case_agree": len(raw_case_disagreements) == 0,
        },
        "open_gaps_repeated": [
            "Terrain parameters and L operators remain candidate terrain math (ATLAS:82-85; ATLAS:118-129).",
            "MBTI labels come from owner_xlsx_pre_llm, not the four markdown engine docs; labels are not load-bearing.",
            "Axis-0 Xi/rho_AB bridge is not built here.",
            "JAX and torch legs are queued, not included in v0.",
            "No 720 closure is asserted; only measured finite traversal closure norms are reported.",
        ],
        "failures": failures,
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "load-bearing readback and parity envelope serialization"},
            "markdown": {"tried": True, "used": True, "reason": "supportive human-readable RESULTS.md emission"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "load_bearing", "markdown": "supportive"},
    }
    return report


def fmt_float(value: float) -> str:
    return f"{float(value):.12g}"


def write_results_md(validator: dict[str, Any], numpy_result: dict[str, Any]) -> None:
    lines = [
        "# Type-1 Engine v0 Results",
        "",
        "Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic. promotion_allowed=false.",
        "",
        f"Parity pass: {validator['parity_pass']} at {validator['parity_tolerance']}",
        f"Max abs diff: {fmt_float(validator['max_abs_diff'])} at `{validator['max_abs_diff_path']}`",
        "",
        "## Fingerprints",
        "",
        f"All 8 distinct: {numpy_result['distinctness']['all_8_distinct']}",
        f"Min pairwise distance: {fmt_float(numpy_result['distinctness']['min_pairwise_distance'])} for {numpy_result['distinctness']['min_pair']}",
        "",
        "| Stage | Terrain | Operator | Casing | Fixed point | Entropy injected generic_a |",
        "|---|---|---|---|---|---|",
    ]
    for stage in common.STAGES:
        fp = numpy_result["stage_fingerprints"][stage["stage_id"]]
        fixed = ", ".join(fmt_float(x) for x in fp["fixed_point_bloch"])
        lines.append(
            f"| {stage['stage_id']} | {stage['terrain']} | {stage['operator']} | {stage['casing']} | "
            f"`[{fixed}]` | {fmt_float(fp['entropy_injected']['generic_a'])} |"
        )

    lines.extend(["", "## Order Sensitivity", "", "| Terrain | Outer | Inner | Max norm | Mean norm |", "|---|---|---|---:|---:|"])
    for terrain, row in numpy_result["order_sensitivity_by_terrain"].items():
        lines.append(
            f"| {terrain} | {row['outer_stage']} | {row['inner_stage']} | "
            f"{fmt_float(row['max_norm'])} | {fmt_float(row['mean_norm'])} |"
        )

    lines.extend(["", "## Traversal Closure", "", "| Traversal | Mean closure | Max closure | Note |", "|---|---:|---:|---|"])
    for name, row in numpy_result["traversals"].items():
        lines.append(
            f"| {name} | {fmt_float(row['closure_summary']['mean'])} | "
            f"{fmt_float(row['closure_summary']['max'])} | no 720 assertion |"
        )

    lines.extend(["", "## Casing Cross-Check", "", "| Stage | Doc casing | xlsx casing | Raw case | Normalized | MBTI |", "|---|---|---|---|---|---|"])
    for row in validator["casing_cross_check"]["rows"]:
        lines.append(
            f"| {row['stage_id']} | {row['doc_casing']} | {row['xlsx_raw_casing']} | "
            f"{row['raw_case_agree']} | {row['normalized_agree']} | {row['mbti']} |"
        )

    lines.extend(["", "## Open Gaps", ""])
    for gap in validator["open_gaps_repeated"]:
        lines.append(f"- {gap}")
    lines.extend(["", "## Verdict", ""])
    if validator["parity_pass"]:
        lines.append("NumPy and Julia legs agree on stage fingerprints, order sensitivity, and traversal trajectories at 1e-9.")
    else:
        lines.append("Parity failed; see validator JSON failures.")
    lines.append("This is a source-faithful diagnostic implementation of the Type-1 chart, not promotion evidence.")
    (RESULTS / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    report = validate()
    (RESULTS / "type1_engine_v0_validator_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    numpy_result = load_result("numpy")
    write_results_md(report, numpy_result)
    print(json.dumps({
        "validator": "type1_engine_v0",
        "parity_pass": report["parity_pass"],
        "max_abs_diff": report["max_abs_diff"],
        "max_abs_diff_path": report["max_abs_diff_path"],
        "failures": report["failures"][:10],
        "results_md": str(RESULTS / "RESULTS.md"),
    }, indent=2))
    return 0 if report["parity_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
