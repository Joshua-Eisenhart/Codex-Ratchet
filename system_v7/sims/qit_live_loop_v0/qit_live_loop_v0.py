#!/usr/bin/env python3
"""QUARANTINE_EXPLORATORY live QIT-loop stream driver.

classification='scratch_diagnostic'; promotion_allowed=false.

This is a live driver, not a gated canonical sim. It imports LevBridge from
system_v7/constraint_core/sims_and_scripts/lev_bridge_sim.py for tick mechanics:
belief update, Hill-cell store, belief_bloch, surprise_bits, and fe_gradient.
It minimally reimplements a reactive-risk + entropy cost surrogate action score
(labeled EFE-analogue, not full active-inference EFE) from agent_loop_sim.py
because that file executes a demo at import time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SIM_ID = "qit_live_loop_v0"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
STREAM_ID = "qit_live_loop_v0.live_300"
DEFAULT_START_TIME = "2026-07-03T00:00:00Z"
TRUE_SHIFT_TICKS = [100, 200]

sys.path.insert(0, str(REPO / "system_v7" / "constraint_core" / "sims_and_scripts"))
sys.path.insert(0, str(REPO / "system_v7" / "sims" / "qit_surprise_stream_v0"))
sys.path.insert(0, str(REPO / "system_v7" / "sims" / "online_regime_shift_detector_v0"))

from lev_bridge_sim import I2, LevBridge, _F, sx, sy, sz  # noqa: E402
from qit_surprise_stream_emitter import (  # noqa: E402
    DEFAULT_SEGMENT_LINES,
    TICK_SCHEMA,
    choose_segment,
    encode_tick_line,
    load_manifest,
    parse_utc,
    segment_sha,
    verify_stream,
    write_manifest,
)
from online_regime_shift_detector_v0_exact import (  # noqa: E402
    derive_parameters,
    detect,
    stationary_values,
    values_from_ticks,
)


def hermitian_trace_one(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / float(np.trace(rho).real)


def bloch_state(x: float, y: float, z: float) -> np.ndarray:
    vec = np.asarray([x, y, z], dtype=np.float64)
    norm = float(np.linalg.norm(vec))
    if norm >= 0.98:
        vec = vec * (0.98 / norm)
    return hermitian_trace_one(0.5 * (I2 + vec[0] * sx + vec[1] * sy + vec[2] * sz))


def world_obs(tick: int, rng: np.random.Generator) -> tuple[np.ndarray, str]:
    """Three deterministic regimes: A stationary, B stationary, C drifting."""
    if tick < 100:
        center = np.asarray([0.08, -0.05, 0.72], dtype=np.float64)
        segment = "A_stationary"
        jitter_scale = 0.0015
    elif tick < 200:
        center = np.asarray([0.25, -0.20, 0.72], dtype=np.float64)
        segment = "B_stationary"
        jitter_scale = 0.0015
    else:
        phase = (tick - 200) / 99.0
        center = np.asarray(
            [
                -0.48 + 0.58 * phase,
                0.28 - 0.44 * phase,
                -0.33 + 0.70 * phase,
            ],
            dtype=np.float64,
        )
        segment = "C_drifting"
        jitter_scale = 0.001
    jitter = rng.normal(0.0, jitter_scale, size=3)
    return bloch_state(*(center + jitter)), segment


def von_neumann_entropy(rho: np.ndarray) -> float:
    evals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    evals = evals[evals > 1.0e-12]
    return float(-np.sum(evals * np.log2(evals)))


def efe(pred: np.ndarray, belief: np.ndarray, preference: np.ndarray, rate: float = 0.5) -> float:
    risk = _F(pred, preference)
    post = hermitian_trace_one((1.0 - rate) * belief + rate * pred)
    epistemic_value = von_neumann_entropy(belief) - von_neumann_entropy(post)
    return risk - epistemic_value


def pick_action(belief: np.ndarray) -> tuple[str, dict[str, float]]:
    preference = bloch_state(0.0, 0.0, 0.88)
    actions = {
        "+z": bloch_state(0.0, 0.0, 0.85),
        "-z": bloch_state(0.0, 0.0, -0.85),
        "+x": bloch_state(0.85, 0.0, 0.0),
        "-x": bloch_state(-0.85, 0.0, 0.0),
        "+y": bloch_state(0.0, 0.85, 0.0),
        "-y": bloch_state(0.0, -0.85, 0.0),
    }
    scores = {name: efe(pred, belief, preference) for name, pred in actions.items()}
    return min(scores, key=scores.__getitem__), {k: round(v, 12) for k, v in scores.items()}


def append_stream_row(out_dir: Path, manifest: dict[str, Any], row: dict[str, Any]) -> None:
    _, segment_path, entry = choose_segment(out_dir, manifest)
    segment_path.parent.mkdir(parents=True, exist_ok=True)
    line = encode_tick_line(row)
    with segment_path.open("ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    entry["line_count"] = int(entry["line_count"]) + 1
    entry["first_tick"] = row["tick"] if entry["first_tick"] is None else entry["first_tick"]
    entry["last_tick"] = row["tick"]
    entry["segment_sha256"] = segment_sha(segment_path)
    manifest["next_tick"] = row["tick"] + 1
    write_manifest(out_dir, manifest)


def read_stream_ticks(out_dir: Path) -> list[dict[str, Any]]:
    ticks: list[dict[str, Any]] = []
    manifest = json.loads((out_dir / "segments_manifest.json").read_text(encoding="utf-8"))
    for segment in manifest["segments"]:
        for raw in (out_dir / segment["path"]).read_text(encoding="utf-8").splitlines():
            ticks.append(json.loads(raw))
    return ticks


def run_detector(ticks: list[dict[str, Any]]) -> dict[str, Any]:
    spec = {
        "declared_false_positive_rate": 0.001,
        "calibration_window": 64,
        "bootstrap_horizon": 256,
        "agreement_window": 8,
        "stream_period": 128,
    }
    calibration = stationary_values(1024, spec["stream_period"])[: spec["calibration_window"]]
    params = derive_parameters(calibration, spec)
    first = detect(values_from_ticks(ticks), params, spec)
    second = detect(values_from_ticks(ticks[128:]), params, spec)
    if second["dual_detection_tick"] is not None:
        second["dual_detection_tick_global"] = int(second["dual_detection_tick"]) + 128
        second["page_hinkley_detection_tick_global"] = (
            None if second["page_hinkley_detection_tick"] is None else int(second["page_hinkley_detection_tick"]) + 128
        )
        second["cusum_detection_tick_global"] = None if second["cusum_detection_tick"] is None else int(second["cusum_detection_tick"]) + 128
    else:
        second["dual_detection_tick_global"] = None
    return {
        "schema": "cr.qit_live_loop_detector_report.v1",
        "detector_source": "online_regime_shift_detector_v0_exact.py detect() with local 64-tick calibration",
        "true_shift_ticks": TRUE_SHIFT_TICKS,
        "first_window": first,
        "second_window_start_tick": 128,
        "second_window": second,
        "fires_near_first_shift": first["dual_detection_tick"] is not None and abs(first["dual_detection_tick"] - 100) <= 8,
        "fires_near_second_shift": second["dual_detection_tick_global"] is not None and abs(second["dual_detection_tick_global"] - 200) <= 8,
        "detector_parameters": params,
    }


def summarize(ticks: list[dict[str, Any]], detector_report: dict[str, Any]) -> dict[str, Any]:
    surprises = np.asarray([float(row["surprise_bits"]) for row in ticks], dtype=np.float64)
    def window_stats(start: int, end: int) -> dict[str, float]:
        values = surprises[start:end]
        return {
            "mean": round(float(np.mean(values)), 12),
            "max": round(float(np.max(values)), 12),
            "last": round(float(values[-1]), 12),
        }

    return {
        "schema": "cr.qit_live_loop_summary.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": "runs / scratch_diagnostic; explicitly NOT a sim per the gated process",
        "ticks": len(ticks),
        "true_shift_ticks": TRUE_SHIFT_TICKS,
        "stationary_tail_A_80_99": window_stats(80, 100),
        "stationary_tail_B_180_199": window_stats(180, 200),
        "drift_tail_C_280_299": window_stats(280, 300),
        "shift_spikes": {
            "tick_100": round(float(surprises[100]), 12),
            "tick_200": round(float(surprises[200]), 12),
            "tick_101": round(float(surprises[101]), 12),
            "tick_201": round(float(surprises[201]), 12),
        },
        "detector": {
            "first_dual_tick": detector_report["first_window"]["dual_detection_tick"],
            "second_dual_tick_global": detector_report["second_window"]["dual_detection_tick_global"],
            "fires_near_first_shift": detector_report["fires_near_first_shift"],
            "fires_near_second_shift": detector_report["fires_near_second_shift"],
        },
    }


def write_results_md(out_dir: Path, summary: dict[str, Any], verification: dict[str, Any]) -> None:
    verdict = (
        "Detector fires near both true shift points."
        if summary["detector"]["fires_near_first_shift"] and summary["detector"]["fires_near_second_shift"]
        else "Detector does not fire near both true shift points."
    )
    near_zero = (
        summary["stationary_tail_A_80_99"]["max"] < 0.01
        and summary["stationary_tail_B_180_199"]["max"] < 0.01
    )
    lines = [
        "# qit_live_loop_v0 Results",
        "",
        "QUARANTINE_EXPLORATORY.",
        "",
        f"- classification: `{CLASSIFICATION}`",
        f"- promotion_allowed: `{str(PROMOTION_ALLOWED).lower()}`",
        "- ceiling: `runs / scratch_diagnostic`",
        "- process status: explicitly NOT a sim per the gated process",
        "",
        "## What Ran",
        "",
        f"- Live driver: `{Path(__file__).name}`",
        "- Mechanics: imported `LevBridge.tick()` from `lev_bridge_sim.py`; minimally reimplemented reactive-risk + entropy cost surrogate action score (labeled EFE-analogue, not full active-inference EFE) from `agent_loop_sim.py` to avoid import-time demo execution.",
        f"- Ticks: `{summary['ticks']}`",
        f"- True regime shifts: `{summary['true_shift_ticks']}`",
        f"- local stream integrity check ok: `{verification['ok']}` over `{verification['ticks_verified']}` ticks",
        "",
        "## Exact Numbers",
        "",
        f"- A stationary tail ticks 80-99 surprise max/mean/last: `{summary['stationary_tail_A_80_99']['max']}` / `{summary['stationary_tail_A_80_99']['mean']}` / `{summary['stationary_tail_A_80_99']['last']}`",
        f"- B stationary tail ticks 180-199 surprise max/mean/last: `{summary['stationary_tail_B_180_199']['max']}` / `{summary['stationary_tail_B_180_199']['mean']}` / `{summary['stationary_tail_B_180_199']['last']}`",
        f"- C drifting tail ticks 280-299 surprise max/mean/last: `{summary['drift_tail_C_280_299']['max']}` / `{summary['drift_tail_C_280_299']['mean']}` / `{summary['drift_tail_C_280_299']['last']}`",
        f"- Shift spike tick 100: `{summary['shift_spikes']['tick_100']}`",
        f"- Shift spike tick 200: `{summary['shift_spikes']['tick_200']}`",
        f"- Detector first dual tick: `{summary['detector']['first_dual_tick']}`",
        f"- Detector second dual tick global: `{summary['detector']['second_dual_tick_global']}`",
        "",
        "## Honest Verdict",
        "",
        f"{verdict} Stationary tails are {'near-zero' if near_zero else 'not near-zero'} by a <0.01 max-surprise diagnostic. Surprise spikes at abrupt shift tick 100; tick 200 starts a drift segment, so the detector report is interpreted as drift-onset detection, not a second abrupt-step proof.",
        "",
    ]
    (out_dir / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def run(out_dir: Path, ticks: int, seed: int, fresh: bool) -> dict[str, Any]:
    if fresh and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "segments").mkdir(exist_ok=True)
    rng = np.random.default_rng(seed)
    bridge = LevBridge(rate=0.5)
    start_time = parse_utc(DEFAULT_START_TIME)
    manifest = load_manifest(out_dir, STREAM_ID, DEFAULT_SEGMENT_LINES)
    if int(manifest["next_tick"]) != 0:
        raise ValueError("output stream is not empty; rerun with --fresh or choose a new out dir")

    actions_path = out_dir / "actions.jsonl"
    for tick in range(ticks):
        obs, segment = world_obs(tick, rng)
        action, efe_scores = pick_action(bridge.bel)
        rec = bridge.tick(obs)
        row = {
            "tick": rec["tick"],
            "t_iso": (start_time + dt.timedelta(seconds=tick)).isoformat().replace("+00:00", "Z"),
            "belief_bloch": rec["belief_bloch"],
            "surprise_bits": rec["surprise_bits"],
            "fe_gradient": rec["fe_gradient"],
            "stream_id": STREAM_ID,
            "schema": TICK_SCHEMA,
        }
        append_stream_row(out_dir, manifest, row)
        action_row = {
            "tick": tick,
            "segment": segment,
            "action": action,
            "efe_scores": efe_scores,
        }
        with actions_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(action_row, sort_keys=True, separators=(",", ":")) + "\n")

    verification = verify_stream(out_dir)
    (out_dir / "verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stream_ticks = read_stream_ticks(out_dir)
    detector_report = run_detector(stream_ticks)
    (out_dir / "detector_report.json").write_text(json.dumps(detector_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = summarize(stream_ticks, detector_report)
    summary["verification_ok"] = verification["ok"]
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results_md(out_dir, summary, verification)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20260703)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=HERE / "results" / "live_300")
    args = parser.parse_args()
    if args.ticks != 300:
        raise SystemExit("qit_live_loop_v0 is fixed to 300 ticks for this diagnostic")
    summary = run(args.out_dir, args.ticks, args.seed, args.fresh)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["verification_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
