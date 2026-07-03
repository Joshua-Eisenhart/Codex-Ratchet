"""QUARANTINE_EXPLORATORY: orchestrator and validator for qit_live_loop_3q_v1.

classification='scratch_diagnostic'; promotion_allowed=false.

This lane validates NumPy oracle, JAX, PyTorch, and Julia substrates.
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

from common_3q import BASE_DIR, CLASSIFICATION, PROMOTION_ALLOWED, REPO_ROOT, RESULTS_DIR, read_jsonl
from world_fixture_3q import write_fixture

PYTHON_SUBSTRATES = {
    "numpy_oracle_loop": BASE_DIR / "substrates" / "numpy_oracle_loop.py",
    "jax_loop": BASE_DIR / "substrates" / "jax_loop.py",
    "torch_loop": BASE_DIR / "substrates" / "torch_loop.py",
}
JULIA_SUBSTRATE = {"julia_loop": BASE_DIR / "substrates" / "julia_loop.jl"}
SUBSTRATES = {**PYTHON_SUBSTRATES, **JULIA_SUBSTRATE}
TRIO_BAR = 1e-10
JULIA_BAR = 1e-9
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = REPO_ROOT / "system_v5" / "julia_carrier"
LEV_SEGMENT_LINES = 100


def safe_fresh_dir(out_dir: Path) -> None:
    resolved = out_dir.resolve()
    results_root = (BASE_DIR / "results").resolve()
    if results_root not in resolved.parents and resolved != results_root:
        raise ValueError(f"refusing to fresh outside {results_root}: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def run_substrate(name: str, script: Path, fixture: Path, out_dir: Path) -> dict:
    out = out_dir / f"{name}.jsonl"
    env = os.environ.copy()
    if script.suffix == ".jl":
        julia = os.environ.get("JULIA") or (str(JULIA) if JULIA.exists() else "julia")
        env["JULIA_LOAD_PATH"] = "@:@stdlib"
        cmd = [julia, "--startup-file=no", f"--project={JULIA_PROJECT}", str(script), "--fixture", str(fixture), "--out", str(out)]
    else:
        python = os.environ.get("SIM_PY") or (str(SIM_PY) if SIM_PY.exists() else sys.executable)
        cmd = [python, str(script), "--fixture", str(fixture), "--out", str(out)]
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


def build_lev_bridge_stream(out_dir: Path, source_name: str = "numpy_oracle_loop") -> dict:
    rows = read_jsonl(out_dir / f"{source_name}.jsonl")
    stream_root = out_dir / "lev_bridge_stream"
    segments_dir = stream_root / "segments"
    if stream_root.exists():
        shutil.rmtree(stream_root)
    segments_dir.mkdir(parents=True, exist_ok=True)
    segments = []
    for start in range(0, len(rows), LEV_SEGMENT_LINES):
        chunk = rows[start : start + LEV_SEGMENT_LINES]
        segment_path = segments_dir / f"segment_{start // LEV_SEGMENT_LINES:04d}.jsonl"
        with segment_path.open("w") as handle:
            for row in chunk:
                bridge_row = {
                    "tick": row["tick"],
                    "t_iso": row["t_iso"],
                    "schema": row["schema"],
                    "stream_id": row["stream_id"],
                    "belief_bloch": row["belief_bloch"],
                    "surprise_bits": row["surprise_bits"],
                    "fe_gradient": row["fe_gradient"],
                    "chosen_action_index": row["chosen_action_index"],
                    "chosen_stage": row["chosen_stage"],
                    "efe_scores_16": row["efe_scores_16"],
                    "world_segment": row["world_segment"],
                    "signal_povm": row["signal_povm"],
                    "classification": row["classification"],
                    "promotion_allowed": row["promotion_allowed"],
                }
                handle.write(json.dumps(bridge_row, sort_keys=True, separators=(",", ":")) + "\n")
        segments.append(
            {
                "path": str(segment_path.relative_to(stream_root)),
                "first_tick": chunk[0]["tick"],
                "last_tick": chunk[-1]["tick"],
                "line_count": len(chunk),
                "segment_sha256": sha256_path(segment_path),
            }
        )
    manifest = {
        "schema": "cr.qit_live_loop_3q_v1.lev_bridge_manifest.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_substrate": source_name,
        "stream_id": "qit_live_loop_3q_v1.live_300",
        "segment_lines": LEV_SEGMENT_LINES,
        "next_tick": len(rows),
        "segments": segments,
    }
    (stream_root / "segments_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return verify_lev_bridge_stream(out_dir, expected_ticks=len(rows))


def verify_lev_bridge_stream(out_dir: Path, expected_ticks: int) -> dict:
    stream_root = out_dir / "lev_bridge_stream"
    manifest_path = stream_root / "segments_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    ticks_verified = 0
    errors = []
    for segment in manifest.get("segments", []):
        path = stream_root / segment["path"]
        if not path.exists():
            errors.append(f"missing segment {path}")
            continue
        actual_sha = sha256_path(path)
        if actual_sha != segment.get("segment_sha256"):
            errors.append(f"sha mismatch {path}: {actual_sha} != {segment.get('segment_sha256')}")
        lines = path.read_text().splitlines()
        if len(lines) != int(segment.get("line_count", -1)):
            errors.append(f"line_count mismatch {path}")
        for raw in lines:
            row = json.loads(raw)
            if row.get("classification") != CLASSIFICATION or row.get("promotion_allowed") is not PROMOTION_ALLOWED:
                errors.append(f"classification boundary mismatch tick {row.get('tick')}")
            ticks_verified += 1
    if ticks_verified != expected_ticks:
        errors.append(f"ticks_verified {ticks_verified} != expected {expected_ticks}")
    return {
        "ok": not errors,
        "manifest": str(manifest_path),
        "ticks_verified": ticks_verified,
        "segment_count": len(manifest.get("segments", [])),
        "errors": errors,
    }


def validate_outputs(out_dir: Path, ticks: int | None = None) -> dict:
    paths = {name: out_dir / f"{name}.jsonl" for name in SUBSTRATES}
    rows = {name: read_jsonl(path) for name, path in paths.items()}
    counts = {name: len(value) for name, value in rows.items()}
    expected_ticks = ticks or next(iter(counts.values()))
    missing = [name for name, count in counts.items() if count != expected_ticks]
    if missing:
        raise ValueError(f"tick count mismatch: {counts}, expected {expected_ticks}")

    python_pairs = [("numpy_oracle_loop", "jax_loop"), ("numpy_oracle_loop", "torch_loop"), ("jax_loop", "torch_loop")]
    julia_pair = ("numpy_oracle_loop", "julia_loop")
    pairs = python_pairs + [julia_pair]
    pair_reports = {}
    max_pauli = 0.0
    max_surprise = 0.0
    max_fe_gradient = 0.0
    max_efe = 0.0
    action_match_count = 0
    python_trio_action_match_count = 0
    mismatch_ticks = []
    python_trio_mismatch_ticks = []

    for tick in range(expected_ticks):
        action_indices = [rows[name][tick]["chosen_action_index"] for name in SUBSTRATES]
        if len(set(action_indices)) == 1:
            action_match_count += 1
        else:
            mismatch_ticks.append({"tick": tick, "actions": dict(zip(SUBSTRATES, action_indices))})
        trio_action_indices = [rows[name][tick]["chosen_action_index"] for name in PYTHON_SUBSTRATES]
        if len(set(trio_action_indices)) == 1:
            python_trio_action_match_count += 1
        else:
            python_trio_mismatch_ticks.append({"tick": tick, "actions": dict(zip(PYTHON_SUBSTRATES, trio_action_indices))})
        for a, b in pairs:
            ra = rows[a][tick]
            rb = rows[b][tick]
            pair = pair_reports.setdefault(
                f"{a}_vs_{b}",
                {
                    "belief_pauli_63_max_abs_dev": 0.0,
                    "surprise_bits_max_abs_dev": 0.0,
                    "fe_gradient_max_abs_dev": 0.0,
                    "efe_scores_16_max_abs_dev": 0.0,
                    "action_index_exact_match": True,
                },
            )
            pauli_dev = max_abs(ra["belief_pauli_63"], rb["belief_pauli_63"])
            surprise_dev = abs(float(ra["surprise_bits"]) - float(rb["surprise_bits"]))
            gradient_dev = abs(float(ra["fe_gradient"]) - float(rb["fe_gradient"]))
            efe_dev = max_abs(ra["efe_scores_16"], rb["efe_scores_16"])
            pair["belief_pauli_63_max_abs_dev"] = max(pair["belief_pauli_63_max_abs_dev"], pauli_dev)
            pair["surprise_bits_max_abs_dev"] = max(pair["surprise_bits_max_abs_dev"], surprise_dev)
            pair["fe_gradient_max_abs_dev"] = max(pair["fe_gradient_max_abs_dev"], gradient_dev)
            pair["efe_scores_16_max_abs_dev"] = max(pair["efe_scores_16_max_abs_dev"], efe_dev)
            pair["action_index_exact_match"] = pair["action_index_exact_match"] and ra["chosen_action_index"] == rb["chosen_action_index"]
            max_pauli = max(max_pauli, pauli_dev)
            max_surprise = max(max_surprise, surprise_dev)
            max_fe_gradient = max(max_fe_gradient, gradient_dev)
            max_efe = max(max_efe, efe_dev)

    python_pair_reports = {f"{a}_vs_{b}": pair_reports[f"{a}_vs_{b}"] for a, b in python_pairs}
    julia_report = pair_reports[f"{julia_pair[0]}_vs_{julia_pair[1]}"]
    lev_stream = verify_lev_bridge_stream(out_dir, expected_ticks) if (out_dir / "lev_bridge_stream" / "segments_manifest.json").exists() else {
        "ok": False,
        "manifest": str(out_dir / "lev_bridge_stream" / "segments_manifest.json"),
        "ticks_verified": 0,
        "segment_count": 0,
        "errors": ["lev bridge stream manifest missing"],
    }
    python_trio_passed = (
        max(pair["belief_pauli_63_max_abs_dev"] for pair in python_pair_reports.values()) <= TRIO_BAR
        and max(pair["surprise_bits_max_abs_dev"] for pair in python_pair_reports.values()) <= TRIO_BAR
        and max(pair["fe_gradient_max_abs_dev"] for pair in python_pair_reports.values()) <= TRIO_BAR
        and python_trio_action_match_count == expected_ticks
        and lev_stream["ok"]
    )
    julia_passed = (
        julia_report["belief_pauli_63_max_abs_dev"] <= JULIA_BAR
        and julia_report["surprise_bits_max_abs_dev"] <= JULIA_BAR
        and julia_report["fe_gradient_max_abs_dev"] <= JULIA_BAR
        and julia_report["action_index_exact_match"]
    )
    report = {
        "schema": "cr.qit_live_loop_3q_v1.parity_report.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "substrates": list(SUBSTRATES),
        "julia_status": {"scoped": True, "threshold": JULIA_BAR, "passed": julia_passed},
        "ticks": expected_ticks,
        "thresholds": {"python_trio_bar": TRIO_BAR, "julia_bar": JULIA_BAR},
        "pair_reports": pair_reports,
        "julia_vs_oracle": julia_report,
        "max_belief_pauli_63_abs_dev": max_pauli,
        "max_surprise_bits_abs_dev": max_surprise,
        "max_fe_gradient_abs_dev": max_fe_gradient,
        "max_efe_scores_16_abs_dev": max_efe,
        "action_match_count": action_match_count,
        "action_mismatch_ticks": mismatch_ticks,
        "python_trio_action_match_count": python_trio_action_match_count,
        "python_trio_action_mismatch_ticks": python_trio_mismatch_ticks,
        "lev_bridge_stream": lev_stream,
        "python_trio_passed": python_trio_passed,
        "julia_passed": julia_passed,
        "all_parity_passed": python_trio_passed and julia_passed,
    }
    (out_dir / "parity_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def write_summary(out_dir: Path, fixture: Path, substrate_metrics: list[dict], parity_report: dict) -> dict:
    fixture_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
    summary = {
        "schema": "cr.qit_live_loop_3q_v1.summary.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "fixture": str(fixture),
        "fixture_sha256": fixture_hash,
        "substrate_metrics": substrate_metrics,
        "parity_report": str(out_dir / "parity_report.json"),
        "lev_bridge_stream": parity_report["lev_bridge_stream"],
        "python_trio_passed": parity_report["python_trio_passed"],
        "julia_passed": parity_report["julia_passed"],
        "all_parity_passed": parity_report["all_parity_passed"],
        "julia_vs_oracle": parity_report["julia_vs_oracle"],
        "action_match_count": parity_report["action_match_count"],
        "python_trio_action_match_count": parity_report["python_trio_action_match_count"],
        "ticks": parity_report["ticks"],
        "max_belief_pauli_63_abs_dev": parity_report["max_belief_pauli_63_abs_dev"],
        "max_surprise_bits_abs_dev": parity_report["max_surprise_bits_abs_dev"],
        "max_fe_gradient_abs_dev": parity_report["max_fe_gradient_abs_dev"],
        "max_efe_scores_16_abs_dev": parity_report["max_efe_scores_16_abs_dev"],
        "honest_boundaries": [
            "Julia loop is an independent scratch diagnostic parity leg, not promotion evidence.",
            "scratch_diagnostic; promotion_allowed=false.",
            "belief_bloch is q0 reduced projection, not full 3q state.",
            "L/R dual engine not claimed.",
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_results_md(out_dir, summary, parity_report)
    return summary


def previous_substrate_metrics(out_dir: Path) -> list[dict] | None:
    summary_path = out_dir / "summary.json"
    if not summary_path.exists():
        return None
    try:
        previous = json.loads(summary_path.read_text())
    except json.JSONDecodeError:
        return None
    metrics = previous.get("substrate_metrics")
    return metrics if isinstance(metrics, list) else None


def validate_only_metrics(out_dir: Path) -> list[dict]:
    previous = previous_substrate_metrics(out_dir) or []
    by_name = {item.get("substrate"): item for item in previous if isinstance(item, dict)}
    metrics = []
    for name in SUBSTRATES:
        metrics.append(by_name.get(name) or {"substrate": name, "output": str(out_dir / f"{name}.jsonl"), "ran": "preexisting"})
    return metrics


def write_results_md(out_dir: Path, summary: dict, parity_report: dict) -> None:
    lines = [
        "# QUARANTINE_EXPLORATORY: qit_live_loop_3q_v1 results",
        "",
        "classification='scratch_diagnostic'; promotion_allowed=false.",
        "",
        "`belief_bloch` is the reduced q0/signal-qubit projection of the 3q belief state, not the full 3q state.",
        "",
        "L/R non-claim: 3q files expose the 16-stage contract, not separate runnable L/R sheet engines.",
        "",
        f"Python trio passed: `{parity_report['python_trio_passed']}`.",
        f"Julia passed: `{parity_report['julia_passed']}`.",
        f"All-substrate action match count: `{parity_report['action_match_count']}/{parity_report['ticks']}`.",
        f"Python trio action match count: `{parity_report['python_trio_action_match_count']}/{parity_report['ticks']}`.",
        f"Max belief_pauli_63 abs dev: `{parity_report['max_belief_pauli_63_abs_dev']}`.",
        f"Max surprise_bits abs dev: `{parity_report['max_surprise_bits_abs_dev']}`.",
        f"Max fe_gradient abs dev: `{parity_report['max_fe_gradient_abs_dev']}`.",
        f"Lev stream verifies: `{parity_report['lev_bridge_stream']['ok']}` over `{parity_report['lev_bridge_stream']['ticks_verified']}` ticks.",
        "",
        "## Julia parity",
        "",
        f"Julia bar: `{parity_report['thresholds']['julia_bar']}`.",
        f"Julia vs oracle belief_pauli_63 max abs dev: `{parity_report['julia_vs_oracle']['belief_pauli_63_max_abs_dev']}`.",
        f"Julia vs oracle surprise_bits max abs dev: `{parity_report['julia_vs_oracle']['surprise_bits_max_abs_dev']}`.",
        f"Julia vs oracle fe_gradient max abs dev: `{parity_report['julia_vs_oracle']['fe_gradient_max_abs_dev']}`.",
        f"Julia vs oracle efe_scores_16 max abs dev: `{parity_report['julia_vs_oracle']['efe_scores_16_max_abs_dev']}`.",
        f"Julia action indices exact: `{parity_report['julia_vs_oracle']['action_index_exact_match']}`.",
        "",
        f"Fixture sha256: `{summary['fixture_sha256']}`.",
    ]
    (out_dir / "RESULTS.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run/validate qit_live_loop_3q_v1 Python trio")
    parser.add_argument("--ticks", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20260703)
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
        build_lev_bridge_stream(out_dir)

    parity_report = validate_outputs(out_dir, ticks=args.ticks)
    if args.validate_only:
        substrate_metrics = validate_only_metrics(out_dir)
    summary = write_summary(out_dir, fixture, substrate_metrics, parity_report)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if parity_report["all_parity_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
