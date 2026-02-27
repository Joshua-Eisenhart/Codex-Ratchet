#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"

TERM_RE = re.compile(r"^[a-z][a-z0-9_]{0,120}$")
NEGCLASS_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,64}$")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_state(run_dir: Path) -> dict:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        return {}
    return _read_json(state_path)


def _canonical_terms(state: dict) -> set[str]:
    term_registry = state.get("term_registry", {}) if isinstance(state.get("term_registry", {}), dict) else {}
    out: set[str] = set()
    for term, row in term_registry.items():
        if not isinstance(row, dict):
            continue
        if str(row.get("state", "")) == "CANONICAL_ALLOWED":
            out.add(str(term))
    return out


def _l0_lexemes(state: dict) -> set[str]:
    return {str(x) for x in (state.get("l0_lexeme_set", []) or []) if str(x).strip()}


def _iter_memos(memos_dir: Path, sequence: int) -> list[Path]:
    prefix = f"{sequence:06d}_MEMO_"
    return sorted([p for p in memos_dir.glob(prefix + "*.json") if p.is_file()], key=lambda p: p.name)


def _extract_terms(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        t = item.strip()
        if TERM_RE.fullmatch(t):
            out.append(t)
    return out


def _extract_neg_classes(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        t = item.strip().upper()
        if NEGCLASS_RE.fullmatch(t):
            out.append(t)
    return out


def _extract_rescue_targets(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        t = item.strip()
        if t:
            out.append(t)
    return out


def _recent_kill_targets(state: dict, *, limit: int = 16) -> list[str]:
    out: list[str] = []
    for row in reversed(state.get("kill_log", []) if isinstance(state, dict) else []):
        if not isinstance(row, dict):
            continue
        if str(row.get("tag", "")).strip() != "KILL_SIGNAL":
            continue
        sid = str(row.get("id", "")).strip()
        if not sid:
            continue
        out.append(sid)
        if len(out) >= int(limit):
            break
    out.reverse()
    return out


def _dedup_keep_order(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in rows:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Strip A1 lawyer memos into cold-core proposals (ratchet-safe tokens only).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--sequence", type=int, default=0, help="Sequence to strip. 0 means infer from sandbox counter or inbox.")
    ap.add_argument("--max-memos", type=int, default=32)
    ap.add_argument("--min-corroboration", type=int, default=2, help="Minimum memo corroboration count for admitting a term candidate.")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    runs_root = Path(args.runs_root).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"missing run dir: {run_dir}")

    sandbox_root = run_dir / "a1_sandbox"
    memos_dir = sandbox_root / "lawyer_memos"
    if not memos_dir.is_dir():
        raise SystemExit(f"missing memos dir: {memos_dir}")

    sequence = int(args.sequence)
    if sequence <= 0:
        # Prefer sandbox counter, else default to 1.
        counter = sandbox_root / "sequence_counter.json"
        if counter.exists():
            try:
                raw = _read_json(counter)
                if isinstance(raw, dict) and isinstance(raw.get("last"), int):
                    sequence = int(raw["last"])
            except Exception:
                pass
    if sequence <= 0:
        sequence = 1

    state = _load_state(run_dir)
    canon = _canonical_terms(state)
    l0 = _l0_lexemes(state)

    memo_paths = _iter_memos(memos_dir, sequence)[: int(args.max_memos)]
    memo_objs: list[dict] = []
    for p in memo_paths:
        try:
            obj = _read_json(p)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        if str(obj.get("schema", "")).strip() != "A1_LAWYER_MEMO_v1":
            continue
        memo_objs.append(obj)

    proposed_terms: list[str] = []
    term_freq: dict[str, int] = {}
    proposed_neg_classes: list[str] = []
    rescue_targets: list[str] = []
    roles_present: set[str] = set()
    for obj in memo_objs:
        roles_present.add(str(obj.get("role", "")).strip().upper())
        terms = _extract_terms(obj.get("proposed_terms"))
        proposed_terms.extend(terms)
        for t in terms:
            term_freq[t] = int(term_freq.get(t, 0)) + 1
        proposed_neg_classes.extend(_extract_neg_classes(obj.get("proposed_negative_classes")))
        rescue_targets.extend(_extract_rescue_targets(obj.get("graveyard_rescue_targets")))

    # Deduplicate deterministically.
    proposed_terms = sorted({t for t in proposed_terms if t})
    proposed_neg_classes = sorted({c for c in proposed_neg_classes if c})
    rescue_targets = _dedup_keep_order([r for r in rescue_targets if r])
    # If memos didn't provide rescue hints, fall back to recent kills so the
    # graveyard becomes an active workspace rather than a passive sink.
    if not rescue_targets:
        rescue_targets = _recent_kill_targets(state, limit=16)

    # Classify term candidates into ratchet-safe buckets.
    need_atomic_bootstrap: set[str] = set()
    admissible_term_candidates: list[str] = []
    # Guardrail: allow bootstrapping new atomic lexemes, but only when the term
    # is corroborated across multiple memos. This prevents single-memo “doc explosion”
    # from leaking arbitrary new lexemes into the ratchet.
    min_corroboration = max(1, int(args.min_corroboration))
    for term in proposed_terms:
        if term in canon:
            continue
        freq = int(term_freq.get(term, 0) or 0)
        if freq < min_corroboration:
            # Still record components that appear to be missing, but don't emit the
            # term as an admissible candidate yet.
            if "_" in term:
                for comp in term.split("_"):
                    if comp and comp not in canon and comp not in l0:
                        need_atomic_bootstrap.add(comp)
            elif term and term not in canon and term not in l0:
                need_atomic_bootstrap.add(term)
            continue
        if "_" not in term:
            # Atomic terms: allow even if not in L0 so the planner can emit an
            # explicit T0 atomic bootstrap batch. Record as bootstrap-needed.
            if term not in l0:
                need_atomic_bootstrap.add(term)
            admissible_term_candidates.append(term)
            continue
        # Compound: allow if every component is canonical or in L0 OR is a simple
        # atomic lexeme that will be bootstrapped in this batch. Keep the term-level
        # candidate admission conservative to avoid huge missing-component swarms.
        ok = True
        missing_components: list[str] = []
        for comp in term.split("_"):
            if not comp:
                ok = False
                break
            if comp in canon or comp in l0:
                continue
            missing_components.append(comp)
            need_atomic_bootstrap.add(comp)
        # Hard cap: don't admit compounds that would require bootstrapping too many
        # new atomics in one shot.
        if len(missing_components) > 6:
            ok = False
        if ok:
            admissible_term_candidates.append(term)

    out_obj = {
        "schema": "A1_COLD_CORE_PROPOSALS_v1",
        "run_id": run_id,
        "sequence": sequence,
        "memo_count": len(memo_objs),
        "roles_present": sorted(roles_present),
        "proposed_terms_raw": proposed_terms,
        "admissible_term_candidates": sorted({t for t in admissible_term_candidates}),
        "need_atomic_bootstrap": sorted({t for t in need_atomic_bootstrap}),
        "min_corroboration": int(min_corroboration),
        "proposed_negative_classes": proposed_neg_classes,
        "graveyard_rescue_targets": rescue_targets,
        "state_hash": str(state.get("state_hash", "")) if isinstance(state, dict) else "",
    }
    out_bytes = (json.dumps(out_obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    out_obj["proposals_sha256"] = _sha256_bytes(out_bytes)
    out_bytes = (json.dumps(out_obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

    out_dir = sandbox_root / "cold_core"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{sequence:06d}_A1_COLD_CORE_PROPOSALS_v1.json"
    out_path.write_bytes(out_bytes)
    print(json.dumps({"schema": out_obj["schema"], "out": str(out_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
