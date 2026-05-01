#!/usr/bin/env python3
"""Run all Wizard General sizes and choose the best runtime default."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if (ROOT / "MMM_PACKET_MANIFEST_v2_7.json").exists():
    DEFAULT_CANDIDATE = ROOT
    DEFAULT_OUT_DIR = ROOT / "runs" / "wizard_general_bakeoff_latest"
else:
    DEFAULT_CANDIDATE = (
        ROOT
        / "work"
        / "mmm_wizard_repair"
        / "mmm_wizard_complete_system_packet_v2_7_candidate"
    )
    DEFAULT_OUT_DIR = ROOT / "work" / "mmm_wizard_repair" / "runs" / "wizard_general_bakeoff_latest"


def _load_runner():
    for path in (ROOT / "tools" / "run_wizard_system.py", ROOT / "scripts" / "run_wizard_system.py"):
        if path.exists():
            break
    else:
        raise FileNotFoundError("run_wizard_system.py")
    spec = importlib.util.spec_from_file_location("run_wizard_system_bakeoff", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _word_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").split())


def _score_run(result: dict[str, Any], final_words: int) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []
    size = str(result["general_size"])
    general_words = int(result["general_words"])

    if result["ok"]:
        score += 100
        notes.append("validation passed")
    else:
        score -= 100
        notes.append("validation failed")

    if 120 <= general_words <= 500:
        score += 35
        notes.append("runtime-sized prompt")
    elif general_words < 80:
        score -= 25
        notes.append("too small to carry output shape")
    elif general_words > 1000:
        score -= 45
        notes.append("too large for routine runtime")
    else:
        score += 10
        notes.append("usable but not ideal size")

    if 250 <= final_words <= 1600:
        score += 15
        notes.append("complete but scannable output")
    elif final_words < 200:
        score -= 10
        notes.append("output likely too thin")
    else:
        score -= 10
        notes.append("output likely too long")

    if size == "standard":
        score += 8
        notes.append("preferred default when tied")
    if size == "full":
        score -= 15
        notes.append("reference/debugging size")
    if size == "ultra":
        score -= 15
        notes.append("emergency shorthand only")

    return score, notes


def run_bakeoff(candidate_root: Path, out_dir: Path, task: str, feedback: list[str]) -> dict[str, Any]:
    runner = _load_runner()
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for size in ("ultra", "compact", "standard", "full"):
        run_dir = out_dir / size
        result = runner.run_wizard(
            candidate_root,
            run_dir,
            task,
            general_size=size,
            feedback=feedback,
        )
        final_path = Path(result["final_answer_path"])
        final_words = _word_count(final_path)
        score, notes = _score_run(result, final_words)
        results.append(
            {
                "size": size,
                "score": score,
                "notes": notes,
                "ok": result["ok"],
                "general_words": result["general_words"],
                "final_words": final_words,
                "out_dir": str(run_dir),
                "final_answer_path": str(final_path),
                "validation_path": result["final_validation_path"],
            }
        )

    best = sorted(results, key=lambda item: (-int(item["score"]), str(item["size"])))[0]
    best_final = Path(str(best["final_answer_path"]))
    copied_best = out_dir / "best_final_answer.md"
    shutil.copyfile(best_final, copied_best)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "candidate_root": str(candidate_root.resolve()),
        "out_dir": str(out_dir.resolve()),
        "task": task,
        "best_size": best["size"],
        "results": results,
        "best_final_answer_path": str(copied_best),
    }
    (out_dir / "bakeoff_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Wizard General Bakeoff",
        "",
        f"Best size: {best['size']}",
        "",
        "| Size | Score | General words | Final words | OK | Notes |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in results:
        lines.append(
            f"| {row['size']} | {row['score']} | {row['general_words']} | "
            f"{row['final_words']} | {row['ok']} | {', '.join(row['notes'])} |"
        )
    lines.append("")
    (out_dir / "bakeoff_report.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--feedback", action="append", default=[])
    parser.add_argument(
        "--task",
        default="Compare Wizard General sizes and choose the best local runtime surface.",
    )
    args = parser.parse_args(argv)
    report = run_bakeoff(args.candidate_root.resolve(), args.out_dir.resolve(), args.task, args.feedback)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
