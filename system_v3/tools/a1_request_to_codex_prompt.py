#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import textwrap
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
CORE_DOCS = REPO / "core_docs"
A2_STATE_DEFAULT = SYSTEM_V3 / "a2_state"
RUNS_DEFAULT = SYSTEM_V3 / "runs"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_latest_save_zip(run_dir: Path) -> Path:
    pkt = run_dir / "zip_packets"
    if not pkt.is_dir():
        raise SystemExit(f"missing zip_packets dir: {pkt}")
    candidates = sorted(pkt.glob("*_A0_TO_A1_SAVE_ZIP.zip"))
    if not candidates:
        raise SystemExit(f"no A0_TO_A1_SAVE_ZIP found in: {pkt}")
    return candidates[-1]


def _load_a0_save_summary(save_zip: Path) -> dict:
    with zipfile.ZipFile(save_zip, "r") as zf:
        try:
            raw = zf.read("A0_SAVE_SUMMARY.json").decode("utf-8")
        except KeyError:
            raise SystemExit(f"missing A0_SAVE_SUMMARY.json in {save_zip}")
    return json.loads(raw)


def _next_a1_inbox_sequence(run_dir: Path, run_id: str) -> int:
    inbox = run_dir / "a1_inbox"
    state_path = inbox / "sequence_state.json"
    if not state_path.exists():
        return 1
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return 1
    if not isinstance(raw, dict):
        return 1
    key = f"{run_id}|A1"
    last = raw.get(key, 0)
    try:
        last_n = int(last)
    except Exception:
        last_n = 0
    return last_n + 1


def _print_next_seq(run_dir: Path, run_id: str) -> None:
    os.sys.stdout.write(str(_next_a1_inbox_sequence(run_dir, run_id)) + "\n")


def _canonical_terms(state: dict) -> list[str]:
    out: list[str] = []
    tr = state.get("term_registry", {}) if isinstance(state.get("term_registry", {}), dict) else {}
    for term, row in tr.items():
        if not isinstance(row, dict):
            continue
        if str(row.get("state", "")) == "CANONICAL_ALLOWED":
            out.append(str(term))
    out.sort()
    return out


def _recent_graveyard_surface(state: dict, *, kill_limit: int = 8, park_limit: int = 8) -> dict:
    kill_log = state.get("kill_log", []) if isinstance(state, dict) else []
    park_set = state.get("park_set", {}) if isinstance(state, dict) else {}
    spec_meta = state.get("spec_meta", {}) if isinstance(state, dict) else {}
    kills: list[dict] = []
    for row in reversed(kill_log if isinstance(kill_log, list) else []):
        if not isinstance(row, dict):
            continue
        if str(row.get("tag", "")).strip() != "KILL_SIGNAL":
            continue
        sid = str(row.get("id", "")).strip()
        meta = spec_meta.get(sid, {}) if isinstance(spec_meta, dict) else {}
        if not isinstance(meta, dict):
            meta = {}
        kills.append(
            {
                "id": sid,
                "token": str(row.get("token", "")).strip(),
                "target_class": str(meta.get("target_class", "")).strip(),
                "negative_class": str(meta.get("negative_class", "")).strip(),
            }
        )
        if len(kills) >= int(kill_limit):
            break
    kills.reverse()
    parked: list[dict] = []
    for sid in sorted(park_set.keys()):
        row = park_set.get(sid, {})
        if not isinstance(row, dict):
            continue
        parked.append(
            {
                "id": str(sid),
                "tag": str(row.get("tag", "")).strip(),
                "detail": str(row.get("detail", "")).strip(),
            }
        )
        if len(parked) >= int(park_limit):
            break
    return {"kills": kills, "parked": parked}


def _fuel_docs_for_a1(*, max_bytes_total: int, a2_state_dir: Path) -> list[dict]:
    fuel_root = CORE_DOCS / "a1_refined_Ratchet Fuel"
    ladder = fuel_root / "constraint ladder"
    sims = fuel_root / "sims"
    thread_save = fuel_root / "THREAD_S_FULL_SAVE"
    a2_model_context = a2_state_dir / "MODEL_CONTEXT.md"
    a2_intent_summary = a2_state_dir / "INTENT_SUMMARY.md"
    prioritized = [
        # A2 context/intent are authoritative steering fuel for A1 behavior.
        a2_intent_summary,
        a2_model_context,
        fuel_root / "PHYSICS_FUEL_DIGEST_v1.0.md",
        fuel_root / "AXIS_FOUNDATION_COMPANION_v1.4.md",
        fuel_root / "AXES_MASTER_SPEC_v0.2.md",
        fuel_root / "CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md",
        fuel_root / "AXIS0_PHYSICS_BRIDGE_v0.1.md",
        fuel_root / "AXIS0_SPEC_OPTIONS_v0.3.md",
        fuel_root / "AXIS0_SPEC_OPTIONS_v0.2.md",
        fuel_root / "AXIS0_SPEC_OPTIONS_v0.1.md",
        sims / "SIM_RUNBOOK_v1.4.md",
        sims / "SIM_CATALOG_v1.3.md",
        sims / "SIM_EVIDENCE_PACK_autogen_v2.txt",
        thread_save / "README.md",
        thread_save / "PROVENANCE.txt",
        ladder / "Constraints.md",
        ladder / "Base constraints ledger v1.md",
        ladder / "Simulation protocol v1.md",
        ladder / "CANDIDATE_PROPOSAL_v1.md",
        ladder / "REFINEMENT_CONTRACT_v1.1.md",
    ]
    candidates: list[Path] = []
    for p in prioritized:
        if p.is_file() and p.name != ".DS_Store":
            candidates.append(p)

    def add_tree(dir_path: Path, *, exts: set[str]) -> None:
        if not dir_path.is_dir():
            return
        for p in sorted(dir_path.rglob("*"), key=lambda x: x.as_posix()):
            if not p.is_file():
                continue
            if p.name == ".DS_Store":
                continue
            if p.suffix.lower() not in exts:
                continue
            if p in candidates:
                continue
            candidates.append(p)

    # We treat all of a1_refined_Ratchet Fuel as admissible A1 "brain upload" fuel.
    # Keep ordering deterministic: top-level docs first, then sims/runbook, then ladder.
    add_tree(fuel_root, exts={".md"})
    add_tree(sims, exts={".md", ".txt"})
    add_tree(thread_save, exts={".md", ".txt"})
    add_tree(ladder, exts={".md"})

    included: list[dict] = []
    used = 0
    for p in candidates:
        if used >= max_bytes_total:
            break
        try:
            data = p.read_bytes()
        except Exception:
            continue
        size = len(data)
        if size == 0:
            continue
        if size > 64_000:
            # Never embed huge docs into a prompt; reference only.
            included.append(
                {
                    "path": str(p.relative_to(REPO)),
                    "sha256": _sha256_bytes(data),
                    "byte_size": size,
                    "embedded": False,
                }
            )
            continue
        if used + size > max_bytes_total:
            continue
        included.append(
            {
                "path": str(p.relative_to(REPO)),
                "sha256": _sha256_bytes(data),
                "byte_size": size,
                "embedded": True,
                "text": data.decode("utf-8", errors="replace"),
            }
        )
        used += size
    return included


def _read_latest_a1_brain_summary(*, max_bytes: int, a2_state_dir: Path) -> dict | None:
    """
    A1 brain is persisted as noncanonical heat in system_v3/a2_state/a1_brain.jsonl.
    We include only a bounded, deterministic tail slice for A1 prompt context.
    """
    path = a2_state_dir / "a1_brain.jsonl"
    if not path.is_file():
        return None
    data = path.read_bytes()
    if not data:
        return None
    # Tail slice for bounded prompt size; then snap to line boundaries.
    tail = data[-int(max_bytes) :] if len(data) > int(max_bytes) else data
    text = tail.decode("utf-8", errors="ignore")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    # Keep last N events deterministically (line-based), independent of OS buffering.
    keep = lines[-12:]
    return {
        "path": str(path.relative_to(REPO)),
        "sha256": _sha256_bytes(data),
        "byte_size": len(data),
        "tail_lines": keep,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--fuel-max-bytes", type=int, default=60_000)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT), help="Override A2 persistent state dir (default: system_v3/a2_state).")
    ap.add_argument(
        "--print-next-seq",
        action="store_true",
        help="Print next expected A1 inbox sequence number and exit.",
    )
    ap.add_argument(
        "--context-only",
        action="store_true",
        help="Emit deterministic run+fuel context only (no output/schema instructions).",
    )
    ap.add_argument(
        "--a1-brain-max-bytes",
        type=int,
        default=24_000,
        help="Max bytes of A1 brain tail to include (from a2_state/a1_brain.jsonl).",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    runs_root = Path(args.runs_root).expanduser().resolve()
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"missing run dir: {run_dir}")
    if bool(args.print_next_seq):
        _print_next_seq(run_dir, run_id)
        return 0

    save_zip = _find_latest_save_zip(run_dir)
    save_summary = _load_a0_save_summary(save_zip)
    state_hash = str(save_summary.get("state_hash", "")).strip()
    step = int(save_summary.get("step", 0))
    last_tags = save_summary.get("last_reject_tags", [])
    if not isinstance(last_tags, list):
        last_tags = []

    next_seq = _next_a1_inbox_sequence(run_dir, run_id)
    state_path = run_dir / "state.json"
    state = _read_json(state_path) if state_path.exists() else {}
    canon_terms = _canonical_terms(state)
    l0_lexemes = sorted({str(x) for x in (state.get("l0_lexeme_set", []) or []) if str(x).strip()})
    derived_only_terms = sorted({str(x) for x in (state.get("derived_only_terms", []) or []) if str(x).strip()})
    graveyard_surface = _recent_graveyard_surface(state)

    fuel_docs = _fuel_docs_for_a1(max_bytes_total=int(args.fuel_max_bytes), a2_state_dir=a2_state_dir)
    a1_brain = _read_latest_a1_brain_summary(max_bytes=int(args.a1_brain_max_bytes), a2_state_dir=a2_state_dir)
    rosetta_path = a2_state_dir / "rosetta.json"
    rosetta_blob = None
    if rosetta_path.is_file():
        raw = rosetta_path.read_bytes()
        rosetta_blob = {
            "path": str(rosetta_path.relative_to(REPO)),
            "sha256": _sha256_bytes(raw),
            "byte_size": len(raw),
            "text": raw.decode("utf-8", errors="replace"),
        }

    # Deterministic prompt: no dynamic wording outside the extracted state+fuel.
    lines: list[str] = []
    if not bool(args.context_only):
        lines.append("Output EXACTLY one JSON object only.")
        lines.append("No markdown. No code fences. No explanation. No extra text.")
        lines.append("")
        lines.append("You are A1. You must output schema-valid A1_STRATEGY_v1 JSON.")
        lines.append("Strict requirements:")
        lines.append("- Root keys EXACTLY: schema,strategy_id,inputs,budget,policy,targets,alternatives,sims,self_audit")
        lines.append("- schema == \"A1_STRATEGY_v1\"")
        lines.append("- No unknown keys anywhere.")
        lines.append("- No auto-correction. No defaults beyond schema.")
        lines.append("")
    lines.append("Run context:")
    lines.append(f"- run_id={run_id}")
    lines.append(f"- requested_step={step}")
    lines.append(f"- state_hash={state_hash}")
    lines.append(f"- next_inbox_sequence={next_seq}")
    lines.append(f"- last_reject_tags={json.dumps(sorted({str(x) for x in last_tags if str(x).strip()}))}")
    lines.append("")
    lines.append("Canonical terms already admitted (do NOT re-define):")
    lines.append(json.dumps(canon_terms, ensure_ascii=True))
    lines.append("")
    lines.append("Allowed L0 lexemes (safe lowercase tokens in DEF_FIELD values):")
    lines.append(json.dumps(l0_lexemes, ensure_ascii=True))
    lines.append("")
    lines.append("Derived-only terms (do NOT use unless term is CANONICAL_ALLOWED):")
    lines.append(json.dumps(derived_only_terms, ensure_ascii=True))
    lines.append("")
    lines.append("Fuel ingestion rule:")
    lines.append("- Do NOT paste prose into DEF_FIELD values.")
    lines.append("- DEF_FIELD values must only contain lowercase tokens that are either:")
    lines.append("  - in L0 lexemes, OR")
    lines.append("  - already canonical terms.")
    lines.append("- If you need a new word, ratchet it as an atomic TERM_DEF first, then build compounds.")
    lines.append("")
    lines.append("ROSETTA / JARGON QUARANTINE RULE:")
    lines.append("- Jargon, metaphors, psychology labels, and narrative are NOT allowed in MATH_DEF/TERM_DEF/CANON_PERMIT/SIM_SPEC DEF_FIELD values.")
    lines.append("- The ONLY place you may carry high-entropy human labels is LABEL_DEF:")
    lines.append("  - LABEL_DEF.DEF_FIELD TERM \"<canonical_term>\"")
    lines.append("  - LABEL_DEF.DEF_FIELD LABEL \"<human label>\"")
    lines.append("- Keep LABEL ASCII and <= 120 characters.")
    lines.append("- This enables bidirectional lookup (term -> label) without contaminating math payloads.")
    lines.append("")
    lines.append("Recent graveyard surface to rescue/challenge:")
    lines.append(json.dumps(graveyard_surface, ensure_ascii=True))
    lines.append("")
    lines.append("WIGGLE / MULTI-NARRATIVE QUOTAS (hard):")
    lines.append("- targets: EXACTLY 1 (STEELMAN)")
    lines.append("- alternatives: EXACTLY 4 (BOUNDARY_SWEEP, PERTURBATION, COMPOSITION_STRESS, ADVERSARIAL_NEG)")
    lines.append("- Ensure structural distinctness across all 5 candidates (different FAMILY/TIER/fields).")
    lines.append("")
    lines.append("SEQUENTIAL LAWYER PROCEDURE (internal reasoning, still output one JSON object):")
    lines.append("1. Steelman: emit one coherent target chain.")
    lines.append("2. Devil: emit one sincere adversarial lane intended to die under SIM.")
    lines.append("3. Boundary/Perturb/Stress: emit three nearby alternatives.")
    lines.append("4. Rescue: at least one alternative should target a prior killed or parked surface.")
    lines.append("")
    lines.append("Role mapping (encoded ONLY via operator_id + DEF_FIELD FAMILY):")
    lines.append("- targets[0]: operator_id=OP_BIND_SIM, FAMILY=BASELINE")
    lines.append("- alternatives[0]: operator_id=OP_REPAIR_DEF_FIELD, FAMILY=BOUNDARY_SWEEP")
    lines.append("- alternatives[1]: operator_id=OP_MUTATE_LEXEME, FAMILY=PERTURBATION")
    lines.append("- alternatives[2]: operator_id=OP_REORDER_DEPENDENCIES, FAMILY=COMPOSITION_STRESS")
    lines.append("- alternatives[3]: operator_id=OP_NEG_SIM_EXPAND, FAMILY=ADVERSARIAL_NEG, NEGATIVE_CLASS must be non-empty")
    lines.append("")
    lines.append("Each candidate object must have EXACT keys:")
    lines.append("- item_class,id,kind,requires,def_fields,asserts,operator_id")
    lines.append("- item_class=\"SPEC_HYP\"")
    lines.append("- kind MUST be one of: MATH_DEF,TERM_DEF,LABEL_DEF,CANON_PERMIT,SIM_SPEC")
    lines.append("")
    lines.append("If you emit SIM_SPEC, include DEF_FIELDs for:")
    lines.append("- REQUIRES_EVIDENCE, SIM_ID, TIER, FAMILY, TARGET_CLASS, PROBE_KIND")
    lines.append("- and include ASSERT rows for PROBE_TOKEN and EVIDENCE_TOKEN (matching REQUIRES_EVIDENCE).")
    lines.append("")
    lines.append("IMPORTANT:")
    lines.append("- Do NOT directly admit or name axes as canon objects.")
    lines.append("- Admit mathematical terms and SIM_SPEC probes that build toward the ladder.")
    lines.append("- Negative lanes must be kill-bound via NEGATIVE_CLASS (A0 will emit KILL_IF).")
    lines.append("")
    lines.append("Fuel bundle (deterministic; use as your fuel, do not invent new terminology):")
    for doc in fuel_docs:
        lines.append("")
        lines.append(f"BEGIN_FUEL_DOC path={doc['path']} sha256={doc['sha256']} byte_size={doc['byte_size']} embedded={str(bool(doc.get('embedded'))).lower()}")
        if doc.get("embedded"):
            lines.append(doc.get("text", "").rstrip("\n"))
        lines.append("END_FUEL_DOC")
    lines.append("")
    if rosetta_blob:
        lines.append(
            f"BEGIN_ROSETTA_INDEX path={rosetta_blob['path']} sha256={rosetta_blob['sha256']} byte_size={rosetta_blob['byte_size']}"
        )
        lines.append(rosetta_blob["text"].rstrip("\n"))
        lines.append("END_ROSETTA_INDEX")
        lines.append("")
    if a1_brain:
        lines.append(
            f"BEGIN_A1_BRAIN_TAIL path={a1_brain['path']} sha256={a1_brain['sha256']} byte_size={a1_brain['byte_size']}"
        )
        for ln in a1_brain["tail_lines"]:
            lines.append(ln)
        lines.append("END_A1_BRAIN_TAIL")
        lines.append("")
    if not bool(args.context_only):
        lines.append("Now output the single JSON object.")

    os.sys.stdout.write("\n".join(lines).rstrip("\n") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
