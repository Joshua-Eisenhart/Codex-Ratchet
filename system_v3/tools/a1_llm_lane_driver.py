#!/usr/bin/env python3
"""
A1 LLM lane driver (fail-closed).

Goal: run the ratchet loop ONLY when an LLM-provided A1 strategy exists.
This driver never uses deterministic memo autofill and never falls back to
deterministic pack selection.

Workflow per cycle:
  1) Ensure run surface exists (optionally clean).
  2) If the runtime is waiting for an A1 strategy packet, emit a lawyer-pack
     prompt set with --final-outputs-strategy enabled.
  3) Package those prompts into a single ZIP "REQUEST" artifact the operator
     can drop into any ChatUI thread (Pro/Instant/etc) to produce role JSONs.
  4) Driver stops with exit code 2 until role outputs are provided.
  5) When role outputs are present, ingest them via a1_lawyer_sink.py, then
     resume the runtime for one step (consuming the newly created A1 packet).

This is intentionally simple and strict. It is designed to be run repeatedly.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO_ROOT / "system_v3"
TOOLS = SYSTEM_V3 / "tools"
RUNNER = TOOLS / "run_real_loop.py"
LAWYER_PACK = TOOLS / "a1_lawyer_pack.py"
LAWYER_SINK = TOOLS / "a1_lawyer_sink.py"
PACKETIZER = TOOLS / "codex_json_to_a1_strategy_packet_zip.py"
A1_PROMPT = TOOLS / "a1_request_to_codex_prompt.py"


@dataclass(frozen=True)
class _CmdResult:
    code: int
    out: str


def _run(cmd: list[str], *, cwd: Path | None = None) -> _CmdResult:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return _CmdResult(code=int(p.returncode), out=str(p.stdout))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _zip_dir(zip_path: Path, root_dir: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(root_dir.rglob("*")):
            if p.is_dir():
                continue
            zf.write(p, p.relative_to(root_dir))


def _next_a1_seq(run_id: str, runs_root: Path, a2_state_dir: Path) -> int:
    r = _run(
        [
            "python3",
            str(A1_PROMPT),
            "--run-id",
            run_id,
            "--runs-root",
            str(runs_root),
            "--a2-state-dir",
            str(a2_state_dir),
            "--print-next-seq",
        ]
    )
    try:
        return int(r.out.strip().splitlines()[-1].strip())
    except Exception:
        return 1


def _emit_request_zip(
    *,
    run_dir: Path,
    sequence: int,
    prompt_queue_dir: Path,
    out_dir: Path,
) -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    req_root = out_dir / f"{sequence:06d}__A1_LLM_REQUEST__{stamp}"
    if req_root.exists():
        shutil.rmtree(req_root)
    req_root.mkdir(parents=True, exist_ok=True)

    # Copy prompts
    prompts_dst = req_root / "prompts"
    prompts_dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(prompt_queue_dir.glob("*_A1_PROMPT.txt")):
        shutil.copy2(p, prompts_dst / p.name)

    # Minimal operator instructions (kept tiny on purpose).
    _write_text(
        req_root / "README__HOW_TO_RUN.txt",
        "\n".join(
            [
                "A1 LLM lane request (fail-closed).",
                "",
                "You must produce one JSON file per prompt under: role_outputs/",
                "Each JSON MUST be the raw role output matching the prompt contract.",
                "",
                "Return a single ZIP containing role_outputs/ only.",
                "Do not add prose. Do not rename files. Do not omit roles.",
            ]
        )
        + "\n",
    )
    _write_text(
        req_root / "MANIFEST.json",
        json.dumps(
            {
                "schema": "A1_LLM_LANE_REQUEST_v1",
                "run_id": run_dir.name,
                "sequence": sequence,
                "expected_role_output_count": len(list(prompts_dst.glob("*_A1_PROMPT.txt"))),
                "expected_output_dir": "role_outputs/",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )

    zip_path = out_dir / f"{sequence:06d}__A1_LLM_LANE_REQUEST__v1.zip"
    _zip_dir(zip_path, req_root)
    return zip_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-closed A1 LLM lane driver (no fallback).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(SYSTEM_V3 / "runs"))
    ap.add_argument("--a2-state-dir", default=str(SYSTEM_V3 / "a2_state"))
    ap.add_argument("--preset", choices=["graveyard13", "entropy_lenses7", "lawyer4"], default="graveyard13")
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--one-step", action="store_true", help="Run at most one ratchet step and exit.")
    ap.add_argument("--request-out-dir", default=str(REPO_ROOT / "work" / "a1_llm_lane_requests"))
    ap.add_argument("--role-outputs-zip", help="ZIP containing role_outputs/ JSON files.")
    args = ap.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve()
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    run_id = str(args.run_id)
    run_dir = runs_root / run_id

    # Ensure run exists (runner initializes surfaces). We use the canonical runtime loop
    # entrypoint (run_real_loop.py). This will create the run surface and then stop as
    # soon as A1 strategy is required.
    init_cmd = ["python3", str(RUNNER), "--run-id", run_id, "--loops", "1"]
    if bool(args.clean):
        init_cmd.append("--clean-existing-run")
    _run(init_cmd, cwd=REPO_ROOT)

    # If role outputs ZIP is provided, ingest it now.
    if args.role_outputs_zip:
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / f"a1_llm_lane_ingest__{run_id}"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(str(Path(args.role_outputs_zip).expanduser().resolve()), "r") as zf:
            zf.extractall(tmp)
        role_dir = tmp / "role_outputs"
        if not role_dir.exists():
            print("ERROR: role_outputs/ not found in provided ZIP.", file=sys.stderr)
            return 2
        for role_json in sorted(role_dir.glob("*.json")):
            r = _run(
                ["python3", str(LAWYER_SINK), "--run-id", run_id, "--runs-root", str(runs_root), "--input-json", str(role_json)],
                cwd=REPO_ROOT,
            )
            if r.code != 0:
                print(r.out)
                return 2

    # If we already have an outgoing A1_STRATEGY_v1 from PACK_SELECTOR role, packetize it.
    outgoing = run_dir / "a1_sandbox" / "outgoing"
    outgoing.mkdir(parents=True, exist_ok=True)
    candidates = sorted(outgoing.glob("*A1_STRATEGY_v1*.json"))
    if candidates:
        strategy_json = candidates[-1]
        pkt = _run(
            [
                "python3",
                str(PACKETIZER),
                "--run-id",
                run_id,
                "--runs-root",
                str(runs_root),
                "--strategy-json",
                str(strategy_json),
            ],
            cwd=REPO_ROOT,
        )
        if pkt.code != 0:
            print(pkt.out)
            return 2
        # Advance one loop to consume packet.
        step = _run(["python3", str(RUNNER), "--run-id", run_id, "--loops", "1"], cwd=REPO_ROOT)
        print(step.out)
        return 0

    # Otherwise emit prompts + request ZIP and stop.
    seq = _next_a1_seq(run_id, runs_root, a2_state_dir)
    prompt_queue = run_dir / "a1_sandbox" / "prompt_queue"
    prompt_queue.mkdir(parents=True, exist_ok=True)
    pack = _run(
        [
            "python3",
            str(LAWYER_PACK),
            "--run-id",
            run_id,
            "--runs-root",
            str(runs_root),
            "--a2-state-dir",
            str(a2_state_dir),
            "--preset",
            str(args.preset),
            "--out-dir",
            str(prompt_queue),
            "--final-outputs-strategy",
        ],
        cwd=REPO_ROOT,
    )
    if pack.code != 0:
        print(pack.out)
        return 2

    req_out = Path(args.request_out_dir).expanduser().resolve()
    zip_path = _emit_request_zip(run_dir=run_dir, sequence=seq, prompt_queue_dir=prompt_queue, out_dir=req_out)
    print(json.dumps({"status": "NEEDS_LLM_ROLE_OUTPUTS", "request_zip": str(zip_path)}, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
