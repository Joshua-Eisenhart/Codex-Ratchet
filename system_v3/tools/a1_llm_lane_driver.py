#!/usr/bin/env python3
"""
A1 LLM lane driver (fail-closed).

Goal: run the ratchet loop ONLY when an A1 strategy exists, and make generating
that strategy a deterministic, file-based subagent step.

Semantic correction (matches your system intent):
- "LLM" is not an API object here.
- The "LLM lane" is a process executed inside a host LLM surface (Codex chat,
  ChatGPT Pro, etc.) using ZIP request/return artifacts.

This driver never uses deterministic memo autofill and never falls back to
deterministic pack selection.

Workflow per cycle:
  1) Ensure run surface exists (optionally clean).
  2) If the runtime is waiting for an A1 strategy packet, emit a lawyer-pack
     prompt set with --final-outputs-strategy enabled.
  3) Package those prompts into a single ZIP "REQUEST" artifact the operator
     can drop into a host LLM surface (Codex chat / ChatGPT Pro / etc) to
     produce role JSONs.
  4) Driver stops with exit code 2 until role outputs are provided (unless you
     automate the host LLM surface yourself).
  5) When role outputs are present, ingest them via a1_lawyer_sink.py, then
     resume the runtime for one step (consuming the newly created A1 packet).

This is intentionally simple and strict. It is designed to be run repeatedly.
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
RUNNER = BOOTPACK / "a1_a0_b_sim_runner.py"
BOOTPACK_SAMPLE_STRATEGY = BOOTPACK / "a1_strategies" / "sample_strategy.json"
LAWYER_PACK = TOOLS / "a1_lawyer_pack.py"
LAWYER_SINK = TOOLS / "a1_lawyer_sink.py"
PACKETIZER = TOOLS / "codex_json_to_a1_strategy_packet_zip.py"
A1_PROMPT = TOOLS / "a1_request_to_codex_prompt.py"
TRANSIENT_A1_LLM_LANE_ROOT = REPO_ROOT / "work" / "a1_transient_llm_lane"

_A1_PACKET_RE = re.compile(r"^([0-9]{6})_A1_TO_A0_STRATEGY_ZIP[.]zip$")


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


def _expected_next_global_step(run_dir: Path) -> int:
    """
    The runner's next global_step is len(state.canonical_ledger) + 1.

    We use this to detect stale A0_TO_A1_SAVE_ZIP grounding artifacts so that
    A1 prompts always reflect the current ratchet state.
    """

    state_path = run_dir / "state.json"
    if not state_path.is_file():
        return 1
    try:
        state = _read_json(state_path)
    except Exception:
        return 1
    ledger = state.get("canonical_ledger", [])
    if not isinstance(ledger, list):
        return 1
    return len(ledger) + 1


def _latest_a0_to_a1_save_summary(run_dir: Path) -> dict:
    pkt_dir = run_dir / "zip_packets"
    if not pkt_dir.is_dir():
        return {}
    candidates = sorted(pkt_dir.glob("*_A0_TO_A1_SAVE_ZIP.zip"))
    if not candidates:
        return {}
    save_zip = candidates[-1]
    try:
        with zipfile.ZipFile(save_zip, "r") as zf:
            raw = zf.read("A0_SAVE_SUMMARY.json").decode("utf-8")
        obj = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(obj, dict):
        return {}
    obj.setdefault("_path", str(save_zip))
    return obj


def _a1_inbox_has_packets(run_dir: Path) -> bool:
    inbox = run_dir / "a1_inbox"
    if not inbox.is_dir():
        return False
    return any(p.is_file() for p in inbox.glob("*.zip"))


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
    prompt_paths: list[Path],
    context_paths: list[Path] | None = None,
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
    copied = 0
    for p in sorted(prompt_paths, key=lambda x: x.name):
        if not p.is_file():
            continue
        if p.name.endswith(".DS_Store"):
            continue
        shutil.copy2(p, prompts_dst / p.name)
        copied += 1

    # Copy context (sharded base prompt) if present.
    context_dst = req_root / "context"
    context_dst.mkdir(parents=True, exist_ok=True)
    ctx_copied = 0
    for p in sorted((context_paths or []), key=lambda x: x.name):
        if not p.is_file():
            continue
        if p.name.endswith(".DS_Store"):
            continue
        shutil.copy2(p, context_dst / p.name)
        ctx_copied += 1

    # Single attach-and-go prompt (small). Do NOT inline prompt contents, to
    # preserve MEGABOOT text limits and avoid duplicative bloat.
    combined_lines: list[str] = []
    combined_lines.append("# A1_LLM_LANE__COMBINED_PROMPT__v1")
    combined_lines.append("")
    combined_lines.append("You are executing a deterministic ZIP subagent request.")
    combined_lines.append("Read every file under `context/` first, then process `prompts/`.")
    combined_lines.append("")
    combined_lines.append("Hard requirements:")
    combined_lines.append("- Output files MUST be placed under `role_outputs/`.")
    combined_lines.append("- For each `prompts/<NAME>.txt`, output `role_outputs/<NAME>.json`.")
    combined_lines.append("- Output MUST be valid JSON. No trailing prose.")
    combined_lines.append("- If you cannot comply, STOP and say so explicitly.")
    combined_lines.append("")
    combined_lines.append("Return format:")
    combined_lines.append("- Preferred: return one ZIP containing `role_outputs/` only.")
    combined_lines.append("- Fallback: emit fenced blocks with exact relative file paths.")
    combined_lines.append("")
    combined_lines.append("Deterministic read order:")
    combined_lines.append("- Context files (read ALL):")
    for ctx in sorted(context_dst.glob("*"), key=lambda x: x.name):
        if ctx.is_file():
            combined_lines.append(f"  - context/{ctx.name}")
    combined_lines.append("- Prompt files (produce one JSON per .txt):")
    for prompt_file in sorted(prompts_dst.glob("*.txt"), key=lambda x: x.name):
        combined_lines.append(f"  - prompts/{prompt_file.name}")
    _write_text(req_root / "COMBINED_PROMPT__A1_LLM_LANE__v1.md", "\n".join(combined_lines) + "\n")

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
                "Filename rule (strict):",
                "- For each prompts/<NAME>.txt, output role_outputs/<NAME>.json (same basename, .txt -> .json).",
                "",
                "Return a single ZIP containing role_outputs/ only.",
                "Do not add prose. Do not rename files. Do not omit roles.",
                "",
                "If your host LLM surface prefers one instruction block, use:",
                "- COMBINED_PROMPT__A1_LLM_LANE__v1.md",
            ]
        )
        + "\n",
    )
    expected_role_output_filenames = []
    for p in sorted(prompts_dst.glob("*_A1_PROMPT.txt"), key=lambda x: x.name):
        name = p.name
        if name.endswith(".txt"):
            expected_role_output_filenames.append(name[:-4] + ".json")
    _write_text(
        req_root / "MANIFEST.json",
        json.dumps(
            {
                "schema": "A1_LLM_LANE_REQUEST_v1",
                "run_id": run_dir.name,
                "sequence": sequence,
                "expected_role_output_count": len(list(prompts_dst.glob("*_A1_PROMPT.txt"))),
                "expected_output_dir": "role_outputs/",
                "expected_role_output_filenames": expected_role_output_filenames,
                "host_llm_attach_and_go_prompt": "COMBINED_PROMPT__A1_LLM_LANE__v1.md",
                "context_file_count": ctx_copied,
                "prompt_file_count": copied,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )

    zip_path = out_dir / f"{sequence:06d}__A1_LLM_LANE_REQUEST__v1.zip"
    _zip_dir(zip_path, req_root)
    return zip_path


def _transient_prompt_queue(*, run_id: str) -> Path:
    return TRANSIENT_A1_LLM_LANE_ROOT / str(run_id).strip() / "prompt_queue"


def _quarantine_a1_inbox_gaps(*, run_dir: Path, run_id: str) -> None:
    inbox = run_dir / "a1_inbox"
    if not inbox.exists():
        return

    seq_state_path = inbox / "sequence_state.json"
    last = 0
    if seq_state_path.is_file():
        try:
            raw = json.loads(seq_state_path.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        if isinstance(raw, dict):
            try:
                last = int(raw.get(f"{run_id}|A1", 0))
            except Exception:
                last = 0
    expected = last + 1

    packets: dict[int, Path] = {}
    for p in sorted(inbox.glob("*.zip"), key=lambda x: x.name):
        m = _A1_PACKET_RE.match(p.name)
        if not m:
            continue
        try:
            seq = int(m.group(1))
        except Exception:
            continue
        packets[seq] = p

    # Keep only the contiguous prefix starting at expected (operator can prefill
    # 47,48,49,...). Anything beyond the first gap will deterministically cause
    # SEQUENCE_GAP and block a clean A1_NEEDS_EXTERNAL_STRATEGY stop.
    keep: set[int] = set()
    seq = expected
    while seq in packets:
        keep.add(seq)
        seq += 1

    quarantine = inbox / "quarantine"
    moved = []
    for seq, path in sorted(packets.items(), key=lambda row: row[0]):
        if seq in keep:
            continue
        quarantine.mkdir(parents=True, exist_ok=True)
        dst = quarantine / path.name
        if dst.exists():
            stem = path.stem
            n = 1
            while True:
                candidate = quarantine / f"{stem}__DUP{n:02d}.zip"
                if not candidate.exists():
                    dst = candidate
                    break
                n += 1
        path.replace(dst)
        moved.append(dst.name)

    if moved:
        (quarantine / "README__WHY_THIS_EXISTS.md").write_text(
            "\n".join(
                [
                    "# A1 inbox quarantine",
                    "",
                    "Files in this folder are A1 strategy packets that are out-of-sequence",
                    "relative to `a1_inbox/sequence_state.json`.",
                    "",
                    "They are preserved for audit, but moved aside so the packet runner can:",
                    "- consume a contiguous prefix of packets, or",
                    "- stop cleanly with A1_NEEDS_EXTERNAL_STRATEGY when the inbox is empty.",
                    "",
                    f"- last_consumed_seq={last}",
                    f"- next_expected_seq={expected}",
                    "",
                    "If you intentionally want to jump to a far-future sequence, you must",
                    "fill the gap with contiguous packets first.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )


def _ensure_run_surface(*, run_id: str, runs_root: Path, clean: bool) -> None:
    cmd = [
        "python3",
        str(RUNNER),
        "--a1-source",
        "packet",
        "--run-id",
        run_id,
        "--steps",
        "1",
        "--runs-root",
        str(runs_root),
        "--strategy",
        str(BOOTPACK_SAMPLE_STRATEGY),
    ]
    if clean:
        cmd.append("--clean")
    _run(cmd, cwd=REPO_ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-closed A1 LLM lane driver (no fallback).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(SYSTEM_V3 / "runs"))
    ap.add_argument("--a2-state-dir", default=str(SYSTEM_V3 / "a2_state"))
    ap.add_argument(
        "--preset",
        choices=["attractor_wiggle_1000", "mass_wiggle_1000", "graveyard13", "entropy_lenses7", "lawyer4"],
        default="attractor_wiggle_1000",
    )
    ap.add_argument("--fuel-max-bytes", type=int, default=200_000)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--one-step", action="store_true", help="Run at most one ratchet step and exit.")
    ap.add_argument("--request-out-dir", default=str(REPO_ROOT / "work" / "a1_llm_lane_requests"))
    ap.add_argument("--role-outputs-zip", help="ZIP containing role_outputs/ JSON files.")
    ap.add_argument(
        "--autogen",
        action="store_true",
        help="Generate a local role_outputs ZIP (no external ChatUI) and ingest it (smoke/testing only).",
    )
    args = ap.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve()
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    run_id = str(args.run_id)
    run_dir = runs_root / run_id
    role_outputs_provided = bool(args.role_outputs_zip) or bool(args.autogen)

    # Keep the A1 inbox fail-closed: quarantine any out-of-sequence packets so the
    # runner doesn't stop on SEQUENCE_GAP when we really mean "needs external A1".
    if run_dir.is_dir():
        _quarantine_a1_inbox_gaps(run_dir=run_dir, run_id=run_id)

    # Ensure run surface exists (bootpack runner creates it). Only do a runner
    # tick when (a) creating/cleaning the run, or (b) we need an A0_TO_A1_SAVE
    # zip to ground the A1 prompts.
    if bool(args.clean) or not run_dir.is_dir():
        _ensure_run_surface(run_id=run_id, runs_root=runs_root, clean=bool(args.clean))

    # If role outputs are provided (or autogen enabled), ingest them now.
    if args.role_outputs_zip or args.autogen:
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / f"a1_llm_lane_ingest__{run_id}"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True, exist_ok=True)
        if args.autogen:
            # Always generate a fresh request zip (with COMBINED_PROMPT) for this run,
            # then autogen against that exact artifact. Do not reuse older request zips
            # that may not include the combined prompt surface.
            req_out = Path(args.request_out_dir).expanduser().resolve()
            req_out.mkdir(parents=True, exist_ok=True)
            seq = _next_a1_seq(run_id, runs_root, a2_state_dir)
            prompt_queue = _transient_prompt_queue(run_id=run_id)
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
                    "--fuel-max-bytes",
                    str(int(args.fuel_max_bytes)),
                    "--out-dir",
                    str(prompt_queue),
                    "--final-outputs-strategy",
                ],
                cwd=REPO_ROOT,
            )
            if pack.code != 0:
                print(pack.out)
                return 2
            prompt_paths: list[Path] = []
            context_paths: list[Path] = []
            try:
                last = pack.out.strip().splitlines()[-1]
                obj = json.loads(last)
                if isinstance(obj, dict):
                    if isinstance(obj.get("prompt_paths"), list):
                        for raw in obj["prompt_paths"]:
                            if isinstance(raw, str) and raw.strip():
                                prompt_paths.append(Path(raw).expanduser().resolve())
                    if isinstance(obj.get("context_paths"), list):
                        for raw in obj["context_paths"]:
                            if isinstance(raw, str) and raw.strip():
                                context_paths.append(Path(raw).expanduser().resolve())
            except Exception:
                prompt_paths = []
                context_paths = []
            if not prompt_paths:
                prompt_paths = sorted(prompt_queue.glob("*_A1_PROMPT.txt"))
            if not context_paths:
                context_paths = sorted(prompt_queue.glob("*_A1_CONTEXT_*.md"))
            req_zip = _emit_request_zip(
                run_dir=run_dir,
                sequence=seq,
                prompt_paths=prompt_paths,
                context_paths=context_paths,
                out_dir=req_out,
            )
            req_tmp = tmp / "request_unpacked"
            req_tmp.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(str(req_zip), "r") as zf:
                zf.extractall(req_tmp)
            combined_prompt = req_tmp / "COMBINED_PROMPT__A1_LLM_LANE__v1.md"
            if not combined_prompt.is_file():
                print("ERROR: combined prompt missing in request zip.", file=sys.stderr)
                return 2
            role_dir = tmp / "role_outputs"
            role_dir.mkdir(parents=True, exist_ok=True)
            autogen = TOOLS / "a1_autogen_role_outputs_attractor.py"
            prompts_dir = req_tmp / "prompts"
            p = subprocess.run(
                [
                    "python3",
                    str(autogen),
                    "--run-id",
                    run_id,
                    "--combined-prompt",
                    str(combined_prompt),
                    "--prompts-dir",
                    str(prompts_dir),
                    "--out-dir",
                    str(role_dir),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            if p.returncode != 0:
                print("ERROR: autogen failed:\n" + (p.stdout or "") + (p.stderr or ""), file=sys.stderr)
                return 2
        else:
            with zipfile.ZipFile(str(Path(args.role_outputs_zip).expanduser().resolve()), "r") as zf:
                zf.extractall(tmp)
        role_dir = tmp / "role_outputs"
        if not role_dir.exists():
            print("ERROR: role_outputs/ not found in provided ZIP.", file=sys.stderr)
            return 2
        expected_seq = _next_a1_seq(run_id, runs_root, a2_state_dir)
        prompt_queue = _transient_prompt_queue(run_id=run_id)
        expected_outputs: list[Path] = []
        if prompt_queue.is_dir():
            prompt_files = sorted(prompt_queue.glob(f"{expected_seq:06d}_*_A1_PROMPT.txt"), key=lambda p: p.name)
            expected_outputs = [role_dir / (p.name[:-4] + ".json") for p in prompt_files if p.name.endswith(".txt")]
        if expected_outputs:
            missing = sorted([p.name for p in expected_outputs if not p.is_file()])
            if missing:
                print("ERROR: missing expected role output JSON files:", file=sys.stderr)
                for name in missing:
                    print(f"- {name}", file=sys.stderr)
                return 2
            role_json_paths = expected_outputs
        else:
            role_json_paths = sorted(role_dir.glob("*.json"), key=lambda p: p.name)
        for role_json in role_json_paths:
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
    if candidates and role_outputs_provided:
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
        step = _run(
            [
                "python3",
                str(RUNNER),
                "--a1-source",
                "packet",
                "--run-id",
                run_id,
                "--steps",
                "1",
                "--runs-root",
                str(runs_root),
                "--strategy",
                str(BOOTPACK_SAMPLE_STRATEGY),
            ],
            cwd=REPO_ROOT,
        )
        if step.code != 0:
            print(step.out)
            return 2

        # One-shot consume: do not silently reuse the same outgoing strategy on
        # subsequent invocations (fail-closed discipline).
        strategy_json.unlink(missing_ok=True)

        print(step.out)
        return 0

    # Otherwise emit prompts + request ZIP and stop.
    # Ensure we have a fresh A0_TO_A1_SAVE_ZIP as the canonical "needs strategy" anchor.
    # If the inbox already contains packets, do not emit prompts; consume one step.
    if _a1_inbox_has_packets(run_dir):
        step = _run(
            [
                "python3",
                str(RUNNER),
                "--a1-source",
                "packet",
                "--run-id",
                run_id,
                "--steps",
                "1",
                "--runs-root",
                str(runs_root),
                "--strategy",
                str(BOOTPACK_SAMPLE_STRATEGY),
            ],
            cwd=REPO_ROOT,
        )
        print(step.out)
        return 0

    expected_step = _expected_next_global_step(run_dir)
    save_summary = _latest_a0_to_a1_save_summary(run_dir)
    try:
        save_step = int(save_summary.get("step", 0))
    except Exception:
        save_step = 0
    if save_step != expected_step:
        # Emit a fresh SAVE_ZIP by invoking the runner in packet mode with an
        # empty inbox. This should stop cleanly with A1_NEEDS_EXTERNAL_STRATEGY.
        _ensure_run_surface(run_id=run_id, runs_root=runs_root, clean=False)

    seq = _next_a1_seq(run_id, runs_root, a2_state_dir)
    prompt_queue = _transient_prompt_queue(run_id=run_id)
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
            "--fuel-max-bytes",
            str(int(args.fuel_max_bytes)),
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
    prompt_paths: list[Path] = []
    context_paths: list[Path] = []
    try:
        last = pack.out.strip().splitlines()[-1]
        obj = json.loads(last)
        if isinstance(obj, dict):
            if isinstance(obj.get("prompt_paths"), list):
                for raw in obj["prompt_paths"]:
                    if not isinstance(raw, str) or not raw.strip():
                        continue
                    prompt_paths.append(Path(raw).expanduser().resolve())
            if isinstance(obj.get("context_paths"), list):
                for raw in obj["context_paths"]:
                    if not isinstance(raw, str) or not raw.strip():
                        continue
                    context_paths.append(Path(raw).expanduser().resolve())
    except Exception:
        prompt_paths = []
        context_paths = []
    if not prompt_paths:
        prompt_paths = sorted(prompt_queue.glob("*_A1_PROMPT.txt"))
    if not context_paths:
        context_paths = sorted(prompt_queue.glob("*_A1_CONTEXT_*.md"))
    zip_path = _emit_request_zip(
        run_dir=run_dir,
        sequence=seq,
        prompt_paths=prompt_paths,
        context_paths=context_paths,
        out_dir=req_out,
    )
    print(json.dumps({"status": "NEEDS_HOST_LLM_OUTPUTS", "request_zip": str(zip_path)}, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
