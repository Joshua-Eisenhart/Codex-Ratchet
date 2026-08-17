#!/usr/bin/env python3
"""Keep looping the wave estate while it improves and does not drift."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
BOX = Path(os.environ.get("CB_BOX_ROOT", Path(__file__).resolve().parents[4]))
PY = Path(os.environ.get("CB_LIGHT_PYTHON", BOX / ".venv" / "bin" / "python"))
HERE = Path(__file__).resolve().parent
SCORE = HERE / "score_estate.py"
EXPLORE = SKILLS / "cb-exploration-wave" / "scripts" / "run_exploration.py"
CONTEXT = SKILLS / "cb-context-strategy-wave" / "scripts" / "run_context_strategy.py"
PROXY = SKILLS / "goodhart-proxy-guard" / "scripts" / "check_proxy.py"
PAPER = SKILLS / "paperclip-scope-guard" / "scripts" / "check_paperclip.py"
DRIFT = SKILLS / "mass-drift-guard" / "scripts" / "check_drift.py"
OUT = Path(
    os.environ.get(
        "CB_WAVE_SELF_LOOP_STATE_DIR",
        str(BOX / "receipts" / "wave_self_loop" / "state"),
    )
)
ROUND_CAP = 8


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _json_cmd(argv: list[str]) -> dict:
    env = os.environ.copy()
    env["CB_WAVE_SELF_LOOP_STATE_DIR"] = str(OUT)
    proc = subprocess.run(argv, check=False, capture_output=True, text=True, env=env)
    text = (proc.stdout or "").strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {"returncode": proc.returncode, "raw": text[-400:]}
    except json.JSONDecodeError:
        return {"returncode": proc.returncode, "stderr": (proc.stderr or "")[-400:], "stdout": text[-400:]}


def _score() -> dict:
    return _json_cmd([str(PY), str(SCORE)])


def _context() -> dict:
    dest = OUT / "context.receipt.json"
    return _json_cmd(
        [
            str(PY),
            str(CONTEXT),
            "--root",
            str(BOX),
            "--prompt-path",
            "integrated_system/context/current",
            "--prompt-path",
            "integrated_system/context/full/prompt_plan_progress_corpus.jsonl",
            "--output-path",
            "integrated_system/runs",
            "--out",
            str(dest),
        ]
    )


def _harvest() -> dict:
    dest = OUT / "receipt.json"
    body = _json_cmd(
        [
            str(PY),
            str(EXPLORE),
            "--root",
            str(BOX),
            "--seed",
            "fixtures/cr/manifold_time_first_seed_v1.json",
            "--out",
            str(dest),
        ]
    )
    return {
        **body,
        "files_touched": [str(dest), str(OUT / "distinguish.packet.json")],
        "claim_ceiling": "harvest compile and Light decide; not measured distinguishability; not promotion",
    }


def _gates(before: dict, after: dict, mutation: dict) -> dict:
    before_path = OUT / "before.score.json"
    after_path = OUT / "after.score.json"
    mut_path = OUT / "mutation.json"
    _write(before_path, before)
    _write(after_path, after)
    _write(mut_path, mutation)
    proxy = _json_cmd([str(PY), str(PROXY), "--before", str(before_path), "--after", str(after_path)])
    paper = _json_cmd([str(PY), str(PAPER), "--mutation", str(mut_path)])
    drift = _json_cmd(
        [
            str(PY),
            str(DRIFT),
            "--context",
            str(OUT / "context.receipt.json"),
            "--harvest",
            str(OUT / "receipt.json"),
        ]
    )
    refused = [
        name
        for name, body in (("proxy", proxy), ("paperclip", paper), ("drift", drift))
        if body.get("status") == "REFUSE"
    ]
    return {"proxy": proxy, "paperclip": paper, "drift": drift, "refused": refused}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    context = _context()
    rounds = [{"round": 0, "name": "context_strategy", "context": context, "kept": False}]
    current = _score()
    rounds.append({"round": 0, "name": "baseline", "score": current, "kept": False})
    baseline = current.get("score", 0)
    stop = None

    mutations = [
        ("harvest_then_light_decide", _harvest),
    ]

    for index, (name, apply) in enumerate(mutations, start=1):
        if index > ROUND_CAP:
            stop = "round_cap"
            break
        before = current
        mutation = apply()
        after = _score()
        gates = _gates(before, after, mutation)
        improved = after.get("score", 0) > before.get("score", 0) and after.get("light_gate")
        keep = improved and not gates["refused"]
        rounds.append(
            {
                "round": index,
                "name": name,
                "mutation": mutation,
                "score": after,
                "gates": gates,
                "kept": keep,
                "delta": after.get("score", 0) - before.get("score", 0),
            }
        )
        if gates["refused"]:
            stop = "goodhart_or_drift"
            current = before
            break
        if keep:
            current = after
            continue
        stop = "no_improve"
        break

    if stop is None:
        stop = "mutation_set_exhausted"

    status = "IMPROVED" if current.get("score", 0) > baseline else "UNCHANGED"
    if stop == "goodhart_or_drift":
        status = "STOPPED_ALIGNMENT"
    captured_at = _now()
    source_bindings = {
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scorer_sha256": hashlib.sha256(SCORE.read_bytes()).hexdigest(),
    }
    source_set_sha256 = hashlib.sha256(
        json.dumps(source_bindings, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    run_id = f"wave-self-loop-{captured_at.replace(':', '').replace('-', '')}-{source_set_sha256[:12]}"
    receipt = {
        "schema": "constraintbox.wave-self-loop.v2",
        "run_id": run_id,
        "captured_at": captured_at,
        "status": status,
        "stop": stop,
        "rounds": rounds,
        "baseline_score": baseline,
        "final_score": current.get("score"),
        "light_gate_final": current.get("light_gate"),
        "alignment_ready": current.get("alignment_ready"),
        "source_bindings": source_bindings,
        "source_set_sha256": source_set_sha256,
        "state_dir": str(OUT),
        "state_artifacts": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(OUT.iterdir())
            if path.is_file() and path.name != "loop.receipt.json"
        },
        "claim_ceiling": (
            "bounded keep/discard while score rises and Goodhart/paperclip/drift "
            "gates stay clean; not model self-improvement; not promotion"
        ),
        "promotion_allowed": False,
    }
    dest = BOX / "receipts" / "wave_self_loop" / "latest.json"
    archive = BOX / "receipts" / "wave_self_loop" / "runs" / f"{run_id}.json"
    _write(archive, receipt)
    _write(dest, receipt)
    _write(OUT / "loop.receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if current.get("light_gate") and status != "STOPPED_ALIGNMENT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
