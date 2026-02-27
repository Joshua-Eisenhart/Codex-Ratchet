#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
A2_STATE_DEFAULT = SYSTEM_V3 / "a2_state"
PROMPT_TOOL = SYSTEM_V3 / "tools" / "a1_request_to_codex_prompt.py"


PRESET_ROLE_ORDERS: dict[str, tuple[tuple[str, str], ...]] = {
    "lawyer4": (
        ("STEELMAN", "Generate the strongest admissible path. No adversarial intent."),
        ("DEVIL", "Generate a sincere adversarial lane intended to die under SIM/KILL_IF."),
        ("BOUNDARY", "Generate boundary/perturb/stress ideas and rescue targets from graveyard/park."),
        ("PACK_SELECTOR", "Select a batch and output one schema-valid A1_STRATEGY_v1 JSON object only."),
    ),
    "entropy_lenses7": (
        ("LENS_VN", "Commit to von Neumann entropy view: what is measured, what is invariant, what is allowed to go negative (if any)."),
        ("LENS_MUTUAL_INFO", "Commit to correlation/mutual-information view: emphasize cut structure and conditional regimes."),
        ("LENS_CONDITIONAL", "Commit to conditional entropy view: include regimes where conditional entropy can be negative."),
        ("LENS_THERMO_ANALOGY", "Map Carnot/Szilard motifs as quarantined analogies into QIT terms/probes (no baths/time primitives)."),
        ("DEVIL_CLASSICAL_SMUGGLER", "Generate the strongest classical smuggling lanes that look plausible but violate constraints."),
        ("RESCUER", "Pick graveyard/park targets and propose rescue attempts without narrative smoothing."),
        ("PACK_SELECTOR", "Select a batch and output one schema-valid A1_STRATEGY_v1 JSON object only."),
    ),
    "graveyard13": (
        ("STEELMAN_CORE", "Generate the strongest finite noncommutative QIT path toward admissible terms/probes."),
        ("STEELMAN_ALT_FORMALISM", "Generate a distinct but admissible formalism for the same target with different structural choices."),
        ("DEVIL_CLASSICAL_TIME", "Generate plausible candidates that smuggle global time primitives and should be killed."),
        ("DEVIL_COMMUTATIVE", "Generate plausible candidates that smuggle commutative collapse and should be killed."),
        ("DEVIL_CONTINUUM", "Generate plausible candidates that smuggle infinite/continuous primitives and should be killed."),
        ("DEVIL_EQUALS_SMUGGLE", "Generate plausible identity/equality smuggling candidates expected to die."),
        ("BOUNDARY_REPAIR", "Generate boundary variants near known failures to map admissibility edges."),
        ("RESCUER_MINIMAL_EDIT", "Rescue graveyard items with minimal edits and explicit ancestry."),
        ("RESCUER_OPERATOR_REFACTOR", "Rescue graveyard items by operator refactor while preserving constraints."),
        ("ENTROPY_LENS_VN", "Push entropy witnesses via density operators and spectrum constraints."),
        ("ENTROPY_LENS_MUTUAL", "Push entropy/correlation witnesses via cuts, partial traces, and trajectory terms."),
        ("ENGINE_LENS_SZILARD_CARNOT", "Propose engine-style candidates as QIT witnesses without classical bath/time."),
        ("PACK_SELECTOR", "Select a batch and output one schema-valid A1_STRATEGY_v1 JSON object only."),
    ),
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8")


def _run_cmd(cmd: list[str]) -> str:
    import subprocess

    return subprocess.check_output(cmd, cwd=str(REPO), text=True).strip()


def _base_prompt(*, run_id: str, fuel_max_bytes: int, runs_root: Path, a2_state_dir: Path) -> str:
    return _run_cmd(
        [
            "python3",
            str(PROMPT_TOOL),
            "--run-id",
            run_id,
            "--fuel-max-bytes",
            str(int(fuel_max_bytes)),
            "--runs-root",
            str(runs_root),
            "--a2-state-dir",
            str(a2_state_dir),
            "--context-only",
        ]
    )


def _wrap_role_prompt(
    *,
    base_prompt: str,
    run_id: str,
    sequence: int,
    role: str,
    role_desc: str,
    final_outputs_strategy: bool,
) -> str:
    # Keep the base prompt intact; prepend a small, deterministic header that
    # forces role separation inside the A1 sandbox.
    header = [
        "A1_SANDBOX_MODE: LAWYER_PACK_v1",
        f"RUN_ID: {run_id}",
        f"SEQUENCE: {sequence}",
        f"ROLE: {role}",
        "",
        "Output discipline:",
        "- Output EXACTLY one JSON object only.",
        "- No markdown, no prose outside JSON.",
        "",
    ]
    if role != "PACK_SELECTOR" or not final_outputs_strategy:
        header += [
            "Schema to output (sandbox-only; NOT consumed by A0/B/SIM):",
            "- schema MUST equal \"A1_LAWYER_MEMO_v1\"",
            "- required keys: schema,run_id,sequence,role,claims,risks,graveyard_rescue_targets,proposed_negative_classes,proposed_terms",
            "",
            "Role objective:",
            f"- {role_desc}",
            "",
        ]
    else:
        header += [
            "Schema to output (this WILL be consumed downstream):",
            "- schema MUST equal \"A1_STRATEGY_v1\"",
            "- Must pass strict A0 validation. No extra keys. No commentary.",
            "",
            "Role objective:",
            f"- {role_desc}",
            "",
            "Before you output the strategy, you MUST internally reconcile the other roles.",
            "Do NOT output their memos here. Only output the final A1_STRATEGY_v1 JSON.",
            "",
        ]
    return "\n".join(header).rstrip("\n") + "\n\n" + base_prompt.strip() + "\n"


def _now_utc_compact() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _next_sandbox_sequence(*, sandbox_root: Path, fallback: int) -> int:
    state_path = sandbox_root / "sequence_counter.json"
    if state_path.exists():
        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("last"), int):
                last = int(raw["last"])
                nxt = last + 1
                state_path.write_text(json.dumps({"last": nxt}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
                return nxt
        except Exception:
            pass
    # Initialize from fallback.
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"last": int(fallback)}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return int(fallback)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Emit a sequential lawyer-pack prompt set into the run-local A1 sandbox. "
            "This is heat-buffered: by default PACK_SELECTOR produces a memo, and the deterministic pack selector tool emits A1_STRATEGY_v1."
        )
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--fuel-max-bytes", type=int, default=60_000)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT), help="Override A2 state dir for prompt fuel (default: system_v3/a2_state).")
    ap.add_argument("--out-dir", default="", help="Override sandbox prompt queue directory.")
    ap.add_argument("--preset", choices=sorted(PRESET_ROLE_ORDERS.keys()), default="lawyer4")
    ap.add_argument(
        "--final-outputs-strategy",
        action="store_true",
        help="If set, PACK_SELECTOR role outputs A1_STRATEGY_v1 directly (strict). Default is memo-only + deterministic pack selector tool.",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("missing run-id")

    runs_root = Path(args.runs_root).expanduser().resolve()
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.exists():
        raise SystemExit(f"missing run dir: {run_dir}")

    base = _base_prompt(run_id=run_id, fuel_max_bytes=int(args.fuel_max_bytes), runs_root=runs_root, a2_state_dir=a2_state_dir)
    sandbox_root = run_dir / "a1_sandbox"
    fallback_seq = 1
    try:
        raw = _run_cmd(
            [
                "python3",
                str(PROMPT_TOOL),
                "--run-id",
                run_id,
                "--runs-root",
                str(runs_root),
                "--a2-state-dir",
                str(a2_state_dir),
                "--print-next-seq",
            ]
        )
        fallback_seq = int(raw.strip())
    except Exception:
        fallback_seq = 1
    sequence = _next_sandbox_sequence(sandbox_root=sandbox_root, fallback=fallback_seq)
    stamp = _now_utc_compact()
    prompt_queue = Path(args.out_dir).expanduser().resolve() if str(args.out_dir).strip() else (sandbox_root / "prompt_queue")
    memos_dir = sandbox_root / "lawyer_memos"
    incoming_dir = sandbox_root / "incoming"
    outgoing_dir = sandbox_root / "outgoing"
    for d in (prompt_queue, memos_dir, incoming_dir, outgoing_dir):
        d.mkdir(parents=True, exist_ok=True)

    role_order = PRESET_ROLE_ORDERS[str(args.preset)]
    prompt_paths: list[str] = []
    for idx, (role, desc) in enumerate(role_order, start=1):
        name = f"{sequence:06d}_{stamp}_ROLE_{idx}_{role}__A1_PROMPT.txt"
        path = prompt_queue / name
        _write_text(
            path,
            _wrap_role_prompt(
                base_prompt=base,
                run_id=run_id,
                sequence=sequence,
                role=role,
                role_desc=desc,
                final_outputs_strategy=bool(args.final_outputs_strategy),
            ),
        )
        prompt_paths.append(str(path))

    out = {
        "schema": "A1_LAWYER_PACK_PROMPT_SET_v1",
        "run_id": run_id,
        "sequence": sequence,
        "preset": str(args.preset),
        "prompt_paths": prompt_paths,
        "sandbox_root": str(sandbox_root),
        "incoming_dir": str(incoming_dir),
        "memos_dir": str(memos_dir),
        "outgoing_dir": str(outgoing_dir),
        "note": "Put each role JSON output into incoming_dir; use a1_lawyer_sink.py to file it. Then run a1_cold_core_strip.py + a1_pack_selector.py to produce A1_STRATEGY_v1 for packetization.",
    }
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
