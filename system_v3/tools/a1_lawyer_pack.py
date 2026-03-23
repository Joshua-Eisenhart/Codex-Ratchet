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

MAX_TEXT_FILE_BYTES = 65_536
MAX_TEXT_FILE_LINES = 2_000


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
    "substrate5": (
        ("STEELMAN_CORE", "Generate the strongest finite noncommutative QIT substrate path using only the requested core substrate terms plus minimal density support terms."),
        ("DEVIL_CLASSICAL_TIME", "Generate plausible substrate variants that smuggle global time primitives and should be killed."),
        ("DEVIL_COMMUTATIVE", "Generate plausible substrate variants that smuggle commutative collapse and should be killed."),
        ("BOUNDARY_REPAIR", "Generate minimal admissibility-edge variants near the core substrate family without importing superoperator or manifold expansion terms."),
        ("RESCUER_MINIMAL_EDIT", "Rescue core substrate failures with minimal edits and explicit ancestry."),
        ("PACK_SELECTOR", "Select a batch and output one schema-valid A1_STRATEGY_v1 JSON object only."),
    ),
    "mass_wiggle_1000": (
        (
            "STEELMAN_MASS",
            "Generate an overcaptured list of admissible term candidates (>=400) across multiple targets. "
            "Do NOT be cautious; false positives are acceptable. Include source anchors when possible. "
            "Lexeme gate: use only known lexemes (L0/canonical) OR explicitly include atomic bootstrap "
            "candidates for any new lexemes you introduce (same cycle).",
        ),
        (
            "ADVERSARIAL_NEG_MASS",
            "Generate a large set of negative-class stress candidates (>=250) that should fail under SIM/KILL_IF. "
            "Explicitly target: TIME, COMMUTATIVE, INFINITE_SET, PRIMITIVE_EQUALS, EUCLIDEAN_METRIC. "
            "Lexeme gate: same as STEELMAN_MASS.",
        ),
        (
            "RESCUER_MASS",
            "Generate rescue transforms (>=200) for known-failed or borderline candidates. "
            "Each rescue should reference the original candidate and a minimal edit. "
            "Prefer lexeme-safe edits that reuse existing tokens.",
        ),
        (
            "ALT_FORMALISM_MASS",
            "Generate alternative-formalism candidates (>=150) that re-express targets with different structures. "
            "Do not collapse to a single narrative. Lexeme gate applies.",
        ),
        (
            "PACK_SELECTOR_MASS",
            "Output ONE A1_STRATEGY_v1 JSON with massive batch size. Hard requirements:\n"
            "- targets + alternatives total >= 1000\n"
            "- alternatives >= 300 (negative_class populated)\n"
            "- sims.positive >= 50 and sims.negative >= 50\n"
            "- budget.max_items >= total candidates; budget.max_sims >= total sims\n"
            "- candidate_count and alternative_count must match lengths exactly\n"
            "- include multiple lanes in operator_ids_used\n"
            "- Lexeme gate: every new lexeme must be bootstrapped with an atomic TERM_DEF in the same strategy\n"
            "Do not be cautious. If unsure, over-generate.\n",
        ),
    ),
    # A1 wiggle preset intended to move toward the attractor basin instead of
    # generating kernel-safe filler. This is enforced again at ingest time in
    # a1_lawyer_sink.py via BRANCH_TRACK coverage checks.
    "attractor_wiggle_1000": (
        ("STEELMAN_MASS", "Generate a large set of positive-class candidates (>=350) grounded in the current ratchet constraints. "
            "Prefer reuse of already-permitted rosetta terms (no lexeme invention unless bootstrapped). "
            "Targets must explicitly cover the BRANCH_TRACK anchors listed in PACK_SELECTOR."),
        ("ADVERSARIAL_NEG_MASS", "Generate a large set of negative-class stress candidates (>=250) that should die under SIM/KILL_IF. "
            "Explicitly target: TIME, COMMUTATIVE, INFINITE_SET, PRIMITIVE_EQUALS, EUCLIDEAN_METRIC. "
            "Negative candidates must also be labeled with BRANCH_TRACK anchors."),
        ("RESCUER_MASS", "Generate rescue transforms (>=200) for known-failed or borderline candidates. "
            "Each rescue should reference the original candidate and a minimal edit. "
            "Rescues must be tagged to a BRANCH_TRACK anchor."),
        ("ALT_FORMALISM_MASS", "Generate alternative-formalism candidates (>=150) that re-express targets with different structures. "
            "Do not collapse to a single narrative. "
            "Alternative formalisms must be tagged to a BRANCH_TRACK anchor."),
        (
            "PACK_SELECTOR_MASS",
            "Output ONE A1_STRATEGY_v1 JSON with massive batch size.\n\n"
            "Hard size requirements:\n"
            "- targets + alternatives total >= 1000\n"
            "- alternatives >= 300 (negative_class populated)\n"
            "- sims.positive >= 50 and sims.negative >= 50\n"
            "- budget.max_items >= total candidates; budget.max_sims >= total sims\n"
            "- candidate_count and alternative_count must match lengths exactly\n"
            "- include multiple lanes in operator_ids_used\n\n"
            "Hard substance requirements (FAIL if you cannot satisfy):\n"
            "- Every candidate MUST include a DEF_FIELD with name=BRANCH_TRACK.\n"
            "- BRANCH_TRACK must be one of these exact tokens (do not invent new ones):\n"
            "  * TRACK_IGT_TYPE1_ENGINE\n"
            "  * TRACK_IGT_TYPE2_ENGINE\n"
            "  * TRACK_AXIS0_PERTURBATION\n"
            "  * TRACK_CONSTRAINT_LADDER\n"
            "  * TRACK_PHYSICS_OVERLAY_OPERATORIZATION\n"
            "  * TRACK_GRAVEYARD_RESCUE\n"
            "- Coverage: at least 4 of the 6 tracks must appear.\n"
            "- Minimum counts: each used track must have >= 20 candidates.\n"
            "- At least 200 candidates must target IGT (TYPE1 or TYPE2) and include invariants about:\n"
            "  outer/inner, deductive/inductive, WIN/LOSE vs win/lose, and topology (Ne/Si/Se/Ni).\n"
            "- At least 150 candidates must target Axis-0 as an operator-ordered perturbation classifier (no time primitives).\n\n"
            "Lexeme gate:\n"
            "- Prefer reuse of already-permitted rosetta terms.\n"
            "- If you introduce a new lexeme, bootstrap it with an atomic TERM_DEF in the same strategy.\n\n"
            "Do not be cautious. If unsure, over-generate.\n",
        ),
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


def _base_prompt(*, run_id: str, fuel_max_bytes: int, runs_root: Path, a2_state_dir: Path, wiggle_profile: str) -> str:
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
            "--wiggle-profile",
            str(wiggle_profile),
        ]
    )


def _wrap_role_prompt(
    *,
    context_rel_paths: list[str],
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
        "CONTEXT (HARD):",
        "- Before answering, read ALL of these files (in order):",
        *[f"- {p}" for p in context_rel_paths],
        "",
        "Output discipline:",
        "- Output EXACTLY one JSON object only.",
        "- No markdown, no prose outside JSON.",
        "",
    ]
    role_upper = role.strip().upper()
    is_pack_selector = role_upper.startswith("PACK_SELECTOR")
    if not is_pack_selector or not final_outputs_strategy:
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
    return "\n".join(header).rstrip("\n") + "\n"


def _shard_text(*, text: str, max_bytes: int, max_lines: int) -> list[str]:
    """
    Split text into shards that each satisfy:
      - <= max_bytes (UTF-8)
      - <= max_lines

    Shards split on line boundaries; if a single line exceeds max_bytes, it is
    hard-sliced into smaller lines.
    """

    lines = text.splitlines(keepends=False)
    shards: list[list[str]] = []
    cur: list[str] = []
    cur_bytes = 0
    cur_lines = 0

    def _flush() -> None:
        nonlocal cur, cur_bytes, cur_lines
        if cur:
            shards.append(cur)
        cur = []
        cur_bytes = 0
        cur_lines = 0

    for ln in lines:
        b = (ln + "\n").encode("utf-8", errors="replace")
        if len(b) > int(max_bytes):
            if cur:
                _flush()
            chunk = ln
            while chunk:
                take = max(1, int(max_bytes) - 1)
                piece = chunk[:take]
                chunk = chunk[take:]
                shards.append([piece])
            continue

        if (cur_lines + 1) > int(max_lines) or (cur_bytes + len(b)) > int(max_bytes):
            _flush()
        cur.append(ln)
        cur_lines += 1
        cur_bytes += len(b)

    if cur:
        _flush()

    return ["\n".join(s).rstrip("\n") + "\n" for s in shards]


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
    ap.add_argument("--preset", choices=sorted(PRESET_ROLE_ORDERS.keys()), default="attractor_wiggle_1000")
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

    preset = str(args.preset)
    wiggle_profile = "mass1000" if preset.endswith("_1000") else "micro5"
    base = _base_prompt(
        run_id=run_id,
        fuel_max_bytes=int(args.fuel_max_bytes),
        runs_root=runs_root,
        a2_state_dir=a2_state_dir,
        wiggle_profile=wiggle_profile,
    )
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

    # When emitting a PACK_SELECTOR strategy directly (LLM lane), align the prompt
    # sequence with the next A1 inbox packet sequence. This avoids drift where
    # prompt "SEQUENCE" and packet sequence diverge and makes operator audit simpler.
    sequence = (
        int(fallback_seq)
        if bool(args.final_outputs_strategy)
        else _next_sandbox_sequence(sandbox_root=sandbox_root, fallback=fallback_seq)
    )
    stamp = _now_utc_compact()
    prompt_queue = Path(args.out_dir).expanduser().resolve() if str(args.out_dir).strip() else (sandbox_root / "prompt_queue")
    memos_dir = sandbox_root / "lawyer_memos"
    incoming_dir = sandbox_root / "incoming"
    outgoing_dir = sandbox_root / "outgoing"
    for d in (prompt_queue, memos_dir, incoming_dir, outgoing_dir):
        d.mkdir(parents=True, exist_ok=True)

    role_order = PRESET_ROLE_ORDERS[str(args.preset)]

    # Write the base context once (sharded), then keep role prompts small and
    # within MEGABOOT text limits. Docs may shard; ZIPs do not split.
    context_chunks = _shard_text(text=base, max_bytes=MAX_TEXT_FILE_BYTES, max_lines=MAX_TEXT_FILE_LINES)
    context_paths: list[str] = []
    for i, chunk in enumerate(context_chunks, start=1):
        ctx_name = f"{sequence:06d}_{stamp}_BASE_CONTEXT__A1_CONTEXT_{i:04d}.md"
        ctx_path = prompt_queue / ctx_name
        _write_text(ctx_path, chunk)
        context_paths.append(str(ctx_path))
    context_rel_paths = [f"context/{Path(p).name}" for p in context_paths]

    prompt_paths: list[str] = []
    for idx, (role, desc) in enumerate(role_order, start=1):
        name = f"{sequence:06d}_{stamp}_ROLE_{idx}_{role}__A1_PROMPT.txt"
        path = prompt_queue / name
        _write_text(
            path,
            _wrap_role_prompt(
                context_rel_paths=context_rel_paths,
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
        "context_paths": context_paths,
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
