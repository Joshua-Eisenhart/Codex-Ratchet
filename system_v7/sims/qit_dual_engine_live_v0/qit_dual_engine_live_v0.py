"""QUARANTINE_EXPLORATORY: orchestrator/validator for qit_dual_engine_live_v0.

classification='scratch_diagnostic'; promotion_allowed=false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from common_dual_engine import (
    BASE_DIR,
    CLASSIFICATION,
    MEMORY_READ_TICKS,
    PROMOTION_ALLOWED,
    QUARANTINE,
    RESULTS_DIR,
    SHEET_STAGE_DEFS,
    read_jsonl,
)
from world_fixture_3q import write_fixture

SUBSTRATES = {
    "numpy_oracle_loop": BASE_DIR / "substrates" / "numpy_oracle_loop.py",
    "jax_loop": BASE_DIR / "substrates" / "jax_loop.py",
    "torch_loop": BASE_DIR / "substrates" / "torch_loop.py",
    "julia_loop": BASE_DIR / "substrates" / "julia_loop.jl",
}
PYTHON_SUBSTRATES = {"numpy_oracle_loop", "jax_loop", "torch_loop"}
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = BASE_DIR.parents[2] / "system_v5" / "julia_carrier"
PYTHON_TRIO_PARITY_BAR = 1e-10
JULIA_PARITY_BAR = 1e-9


def safe_fresh_dir(out_dir: Path) -> None:
    resolved = out_dir.resolve()
    results_root = (BASE_DIR / "results").resolve()
    if results_root not in resolved.parents and resolved != results_root:
        raise ValueError(f"refusing to fresh outside {results_root}: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def run_substrate(name: str, script: Path, fixture: Path, out_dir: Path) -> dict:
    env = os.environ.copy()
    if script.suffix == ".jl":
        julia = os.environ.get("JULIA") or (str(JULIA) if JULIA.exists() else "julia")
        env["JULIA_LOAD_PATH"] = "@:@stdlib"
        cmd = [julia, "--startup-file=no", f"--project={JULIA_PROJECT}", str(script), "--fixture", str(fixture), "--out-dir", str(out_dir)]
    else:
        python = os.environ.get("SIM_PY") or (str(SIM_PY) if SIM_PY.exists() else sys.executable)
        cmd = [python, str(script), "--fixture", str(fixture), "--out-dir", str(out_dir)]
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=BASE_DIR.parents[2], text=True, capture_output=True, env=env)
    wall = time.perf_counter() - started
    if proc.returncode != 0:
        return {
            "substrate": name,
            "command": cmd,
            "returncode": proc.returncode,
            "wall_seconds": wall,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "ran": False,
        }
    last = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}"
    metrics = json.loads(last)
    metrics.update({"command": cmd, "returncode": proc.returncode, "wall_seconds": wall, "ran": True})
    return metrics


def max_abs(xs: list[float], ys: list[float]) -> float:
    return max(abs(float(a) - float(b)) for a, b in zip(xs, ys))


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_fields_report(a: dict, b: dict) -> dict:
    return {
        "belief_pauli_63": max_abs(a["belief_pauli_63"], b["belief_pauli_63"]),
        "surprise_bits": abs(float(a["surprise_bits"]) - float(b["surprise_bits"])),
        "fe_gradient": abs(float(a["fe_gradient"]) - float(b["fe_gradient"])),
        "entropy_bits": abs(float(a["entropy_bits"]) - float(b["entropy_bits"])),
        "efe_scores_8": max_abs(a["efe_scores_8"], b["efe_scores_8"]),
        "sheet_gap_trace_distance": abs(float(a["sheet_gap_trace_distance"]) - float(b["sheet_gap_trace_distance"])),
        "sheet_gap_abs_surprise_delta": abs(float(a["sheet_gap_abs_surprise_delta"]) - float(b["sheet_gap_abs_surprise_delta"])),
        "memory_bit_fidelity": abs(float(a["memory_bit_fidelity"]) - float(b["memory_bit_fidelity"])),
    }


def pair_threshold(left: str, right: str) -> float:
    if left in PYTHON_SUBSTRATES and right in PYTHON_SUBSTRATES:
        return PYTHON_TRIO_PARITY_BAR
    return JULIA_PARITY_BAR


def numeric_leaf_devs(a, b, prefix: str = "") -> list[tuple[str, float]]:
    if isinstance(a, bool) or isinstance(b, bool):
        return []
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return [(prefix or "$", abs(float(a) - float(b)))]
    if isinstance(a, list) and isinstance(b, list):
        devs: list[tuple[str, float]] = []
        for idx, (left, right) in enumerate(zip(a, b)):
            devs.extend(numeric_leaf_devs(left, right, f"{prefix}[{idx}]"))
        return devs
    if isinstance(a, dict) and isinstance(b, dict):
        devs = []
        for key in sorted(set(a) & set(b)):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            devs.extend(numeric_leaf_devs(a[key], b[key], next_prefix))
        return devs
    return []


def validate_outputs(out_dir: Path, ticks: int) -> dict:
    rows = {
        substrate: {engine: read_jsonl(out_dir / f"{substrate}_engine_{engine}.jsonl") for engine in ("D", "C")}
        for substrate in SUBSTRATES
    }
    counts = {f"{substrate}_{engine}": len(engine_rows) for substrate, by_engine in rows.items() for engine, engine_rows in by_engine.items()}
    if any(count != ticks for count in counts.values()):
        raise ValueError(f"tick count mismatch: {counts}, expected {ticks}")

    pair_reports = {}
    max_fields = {
        "belief_pauli_63": 0.0,
        "surprise_bits": 0.0,
        "fe_gradient": 0.0,
        "entropy_bits": 0.0,
        "efe_scores_8": 0.0,
        "sheet_gap_trace_distance": 0.0,
        "sheet_gap_abs_surprise_delta": 0.0,
        "memory_bit_fidelity": 0.0,
        "all_numeric_leaves": 0.0,
    }
    action_matches = {"D": 0, "C": 0}
    action_mismatch_ticks: dict[str, list[dict]] = {"D": [], "C": []}
    global_stage_matches = {"D": 0, "C": 0}
    global_stage_mismatch_ticks: dict[str, list[dict]] = {"D": [], "C": []}
    boundary_errors = []

    substrate_names = list(SUBSTRATES)
    pair_count_by_engine = {engine: 0 for engine in ("D", "C")}
    for engine in ("D", "C"):
        for left_idx, left in enumerate(substrate_names):
            for right in substrate_names[left_idx + 1 :]:
                pair_count_by_engine[engine] += 1
                threshold = pair_threshold(left, right)
                pair_key = f"{left}_vs_{right}_engine_{engine}"
                pair_reports[pair_key] = {field: 0.0 for field in max_fields}
                pair_reports[pair_key]["threshold"] = threshold
                pair_reports[pair_key]["action_index_exact_match"] = True
                pair_reports[pair_key]["global_stage_id_exact_match"] = True
                pair_reports[pair_key]["numeric_passed"] = True
                for tick in range(ticks):
                    a = rows[left][engine][tick]
                    b = rows[right][engine][tick]
                    for substrate, row in ((left, a), (right, b)):
                        if row.get("classification") != CLASSIFICATION:
                            boundary_errors.append(f"{substrate} {engine} tick {tick}: classification mismatch")
                        if row.get("promotion_allowed") is not PROMOTION_ALLOWED:
                            boundary_errors.append(f"{substrate} {engine} tick {tick}: promotion boundary mismatch")
                        if row.get("quarantine") != QUARANTINE:
                            boundary_errors.append(f"{substrate} {engine} tick {tick}: quarantine mismatch")
                    devs = numeric_fields_report(a, b)
                    for field, value in devs.items():
                        pair_reports[pair_key][field] = max(pair_reports[pair_key][field], value)
                        max_fields[field] = max(max_fields[field], value)
                        if value > threshold:
                            pair_reports[pair_key]["numeric_passed"] = False
                    leaf_devs = numeric_leaf_devs(a, b)
                    leaf_max = max((value for _, value in leaf_devs), default=0.0)
                    pair_reports[pair_key]["all_numeric_leaves"] = max(pair_reports[pair_key]["all_numeric_leaves"], leaf_max)
                    max_fields["all_numeric_leaves"] = max(max_fields["all_numeric_leaves"], leaf_max)
                    if leaf_max > threshold:
                        pair_reports[pair_key]["numeric_passed"] = False
                    if a["chosen_action_index"] == b["chosen_action_index"]:
                        action_matches[engine] += 1
                    else:
                        pair_reports[pair_key]["action_index_exact_match"] = False
                        action_mismatch_ticks[engine].append(
                            {"tick": tick, "left_substrate": left, "right_substrate": right, "left": a["chosen_action_index"], "right": b["chosen_action_index"]}
                        )
                    if a["chosen_global_stage_id"] == b["chosen_global_stage_id"]:
                        global_stage_matches[engine] += 1
                    else:
                        pair_reports[pair_key]["global_stage_id_exact_match"] = False
                        global_stage_mismatch_ticks[engine].append(
                            {"tick": tick, "left_substrate": left, "right_substrate": right, "left": a["chosen_global_stage_id"], "right": b["chosen_global_stage_id"]}
                        )

    passed = (
        all(pair["numeric_passed"] for pair in pair_reports.values())
        and all(action_matches[engine] == ticks * pair_count_by_engine[engine] for engine in ("D", "C"))
        and all(global_stage_matches[engine] == ticks * pair_count_by_engine[engine] for engine in ("D", "C"))
        and not boundary_errors
    )
    report = {
        "schema": "cr.qit_dual_engine_live_v0.parity_report.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "quarantine": QUARANTINE,
        "ticks": ticks,
        "thresholds": {
            "python_trio_numeric_bar": PYTHON_TRIO_PARITY_BAR,
            "julia_numeric_bar": JULIA_PARITY_BAR,
            "action_index": "exact",
            "global_stage_id": "exact",
        },
        "substrates": list(SUBSTRATES),
        "engines": {
            "D": {"sheet": "eps-sheet direct", "stage_defs": SHEET_STAGE_DEFS["D"]},
            "C": {"sheet": "eps-sheet conjugated", "stage_defs": SHEET_STAGE_DEFS["C"]},
        },
        "pair_reports": pair_reports,
        "max_numeric_abs_dev": max_fields,
        "action_match_count_by_engine": action_matches,
        "global_stage_match_count_by_engine": global_stage_matches,
        "pair_count_by_engine": pair_count_by_engine,
        "expected_exact_matches_by_engine": {engine: ticks * pair_count_by_engine[engine] for engine in ("D", "C")},
        "action_mismatch_ticks": action_mismatch_ticks,
        "global_stage_mismatch_ticks": global_stage_mismatch_ticks,
        "boundary_errors": boundary_errors,
        "all_parity_passed": passed,
    }
    (out_dir / "parity_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def summarize_sheet_gap(out_dir: Path, source_name: str = "numpy_oracle_loop") -> dict:
    d_rows = read_jsonl(out_dir / f"{source_name}_engine_D.jsonl")
    c_rows = read_jsonl(out_dir / f"{source_name}_engine_C.jsonl")
    gaps = [float(row["sheet_gap_trace_distance"]) for row in d_rows]
    surprise_deltas = [float(row["sheet_gap_abs_surprise_delta"]) for row in d_rows]
    entropy = {
        "D": [float(row["entropy_bits"]) for row in d_rows],
        "C": [float(row["entropy_bits"]) for row in c_rows],
    }
    memory = {
        "D": {str(row["tick"]): float(row["memory_bit_fidelity"]) for row in d_rows if row["memory_read_tick"]},
        "C": {str(row["tick"]): float(row["memory_bit_fidelity"]) for row in c_rows if row["memory_read_tick"]},
    }
    gap_summary = {
        "schema": "cr.qit_dual_engine_live_v0.sheet_gap_summary.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "quarantine": QUARANTINE,
        "source_substrate": source_name,
        "ticks": len(d_rows),
        "sheet_gap_trace_distance": {
            "min": min(gaps),
            "max": max(gaps),
            "mean": sum(gaps) / len(gaps),
            "initial": gaps[0],
            "final": gaps[-1],
            "at_ticks": {str(tick): gaps[tick] for tick in MEMORY_READ_TICKS},
        },
        "sheet_gap_abs_surprise_delta": {
            "min": min(surprise_deltas),
            "max": max(surprise_deltas),
            "mean": sum(surprise_deltas) / len(surprise_deltas),
            "initial": surprise_deltas[0],
            "final": surprise_deltas[-1],
            "at_ticks": {str(tick): surprise_deltas[tick] for tick in MEMORY_READ_TICKS},
        },
        "entropy_coherence": {
            engine: {
                "min": min(values),
                "max": max(values),
                "final": values[-1],
                "finite": all(math_is_finite(x) for x in values),
                "within_3q_bits": min(values) >= -1e-9 and max(values) <= 3.0 + 1e-9,
            }
            for engine, values in entropy.items()
        },
        "memory_bit_fidelity": memory,
        "verdicts": {
            "sheet_engines_diverge": max(gaps) > 1e-6,
            "surprise_profiles_diverge": max(surprise_deltas) > 1e-6,
            "entropy_coherent": all(min(values) >= -1e-9 and max(values) <= 3.0 + 1e-9 for values in entropy.values()),
            "memory_bits_differ_by_sheet": any(abs(memory["D"][str(t)] - memory["C"][str(t)]) > 1e-12 for t in MEMORY_READ_TICKS),
        },
    }
    (out_dir / "sheet_gap_summary.json").write_text(json.dumps(gap_summary, indent=2, sort_keys=True) + "\n")
    return gap_summary


def math_is_finite(value: float) -> bool:
    return value == value and value not in (float("inf"), float("-inf"))


def write_results_md(out_dir: Path, summary: dict, parity: dict, sheet_gap: dict) -> None:
    d_mem = sheet_gap["memory_bit_fidelity"]["D"]
    c_mem = sheet_gap["memory_bit_fidelity"]["C"]
    lines = [
        "# QUARANTINE_EXPLORATORY: qit_dual_engine_live_v0 results",
        "",
        "classification='scratch_diagnostic'; promotion_allowed=false.",
        "",
        "owner doctrine reads this partition as L/R chirality engines; that mapping is interpretive, not computed here.",
        "",
        "Engine D: eps-sheet direct, terrains 0-3 x {Ti,Fi}. Engine C: eps-sheet conjugated, terrains 4-7 x {Te,Fe}. Both consume the same world fixture and maintain separate 8x8 beliefs plus separate spinor-memory bits.",
        "",
        "## Verdicts",
        "",
        f"- Parity passed: `{parity['all_parity_passed']}` with Python-trio numeric bar `{parity['thresholds']['python_trio_numeric_bar']}` and Julia numeric bar `{parity['thresholds']['julia_numeric_bar']}`.",
        f"- Action matches D: `{parity['action_match_count_by_engine']['D']}/{parity['expected_exact_matches_by_engine']['D']}` pair-ticks.",
        f"- Action matches C: `{parity['action_match_count_by_engine']['C']}/{parity['expected_exact_matches_by_engine']['C']}` pair-ticks.",
        f"- Sheet-engines diverge by trace gap: `{sheet_gap['verdicts']['sheet_engines_diverge']}`.",
        f"- Surprise profiles diverge: `{sheet_gap['verdicts']['surprise_profiles_diverge']}`.",
        f"- Entropy coherent: `{sheet_gap['verdicts']['entropy_coherent']}`.",
        f"- Memory bits differ by sheet: `{sheet_gap['verdicts']['memory_bits_differ_by_sheet']}`.",
        "",
        "## Parity",
        "",
        f"- Max belief_pauli_63 abs dev: `{parity['max_numeric_abs_dev']['belief_pauli_63']}`.",
        f"- Max surprise_bits abs dev: `{parity['max_numeric_abs_dev']['surprise_bits']}`.",
        f"- Max fe_gradient abs dev: `{parity['max_numeric_abs_dev']['fe_gradient']}`.",
        f"- Max entropy_bits abs dev: `{parity['max_numeric_abs_dev']['entropy_bits']}`.",
        f"- Max efe_scores_8 abs dev: `{parity['max_numeric_abs_dev']['efe_scores_8']}`.",
        f"- Max sheet_gap_trace_distance abs dev: `{parity['max_numeric_abs_dev']['sheet_gap_trace_distance']}`.",
        f"- Max sheet_gap_abs_surprise_delta abs dev: `{parity['max_numeric_abs_dev']['sheet_gap_abs_surprise_delta']}`.",
        f"- Max memory_bit_fidelity abs dev: `{parity['max_numeric_abs_dev']['memory_bit_fidelity']}`.",
        "",
        "## Sheet Gap",
        "",
        f"- Trace distance min/mean/max/final: `{sheet_gap['sheet_gap_trace_distance']['min']}` / `{sheet_gap['sheet_gap_trace_distance']['mean']}` / `{sheet_gap['sheet_gap_trace_distance']['max']}` / `{sheet_gap['sheet_gap_trace_distance']['final']}`.",
        f"- |surprise_D - surprise_C| min/mean/max/final: `{sheet_gap['sheet_gap_abs_surprise_delta']['min']}` / `{sheet_gap['sheet_gap_abs_surprise_delta']['mean']}` / `{sheet_gap['sheet_gap_abs_surprise_delta']['max']}` / `{sheet_gap['sheet_gap_abs_surprise_delta']['final']}`.",
        "",
        "## Memory",
        "",
        f"- D fidelity at read ticks: `{d_mem}`.",
        f"- C fidelity at read ticks: `{c_mem}`.",
        "",
        "## Runtimes",
        "",
    ]
    for metric in summary["substrate_metrics"]:
        lines.append(f"- {metric['substrate']}: wall `{metric.get('wall_seconds')}`, substrate total `{metric.get('total_seconds')}`.")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- This is scratch diagnostic parity evidence only.",
            "- No promotion, admission, bridge, axis, or chirality computation claim is made.",
            "- The eps-sheet direct/conjugated naming is the computed partition; L/R is only the owner-doctrine interpretation line above.",
            f"- Fixture sha256: `{summary['fixture_sha256']}`.",
        ]
    )
    (out_dir / "RESULTS.md").write_text("\n".join(lines) + "\n")


def write_summary(out_dir: Path, fixture: Path, substrate_metrics: list[dict], parity: dict, sheet_gap: dict) -> dict:
    summary = {
        "schema": "cr.qit_dual_engine_live_v0.summary.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "quarantine": QUARANTINE,
        "fixture": str(fixture),
        "fixture_sha256": sha256_path(fixture),
        "substrate_metrics": substrate_metrics,
        "parity_report": str(out_dir / "parity_report.json"),
        "sheet_gap_summary": str(out_dir / "sheet_gap_summary.json"),
        "all_parity_passed": parity["all_parity_passed"],
        "action_match_count_by_engine": parity["action_match_count_by_engine"],
        "global_stage_match_count_by_engine": parity["global_stage_match_count_by_engine"],
        "max_numeric_abs_dev": parity["max_numeric_abs_dev"],
        "sheet_gap_trace_distance": sheet_gap["sheet_gap_trace_distance"],
        "sheet_gap_abs_surprise_delta": sheet_gap["sheet_gap_abs_surprise_delta"],
        "memory_bit_fidelity": sheet_gap["memory_bit_fidelity"],
        "honest_boundaries": [
            "scratch_diagnostic; promotion_allowed=false.",
            "QUARANTINE_EXPLORATORY.",
            "NumPy and Julia are independent implementations of the same diagnostic rules.",
            "eps-sheet direct/conjugated is computed; L/R chirality wording is interpretive only.",
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_results_md(out_dir, summary, parity, sheet_gap)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run/validate qit_dual_engine_live_v0")
    parser.add_argument("--ticks", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20260704)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    fixture = out_dir / "world_fixture.json"
    substrate_metrics = []
    if not args.validate_only:
        if args.fresh:
            safe_fresh_dir(out_dir)
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
        write_fixture(fixture, ticks=args.ticks, seed=args.seed)
        for name, script in SUBSTRATES.items():
            metrics = run_substrate(name, script, fixture, out_dir)
            substrate_metrics.append(metrics)
            if not metrics.get("ran"):
                (out_dir / "summary.json").write_text(json.dumps({"failed_substrate": metrics}, indent=2) + "\n")
                print(json.dumps(metrics, indent=2, sort_keys=True))
                return 1

    parity = validate_outputs(out_dir, ticks=args.ticks)
    sheet_gap = summarize_sheet_gap(out_dir)
    if args.validate_only:
        substrate_metrics = [{"substrate": name, "ran": "preexisting"} for name in SUBSTRATES]
    summary = write_summary(out_dir, fixture, substrate_metrics, parity, sheet_gap)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if parity["all_parity_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
