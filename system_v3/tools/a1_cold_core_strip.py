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
TRANSIENT_A1_LAWYER_ROOT = REPO / "work" / "a1_transient_lawyer"
TRANSIENT_A1_COLD_CORE_ROOT = REPO / "work" / "a1_transient_cold_core"

TERM_RE = re.compile(r"^[a-z][a-z0-9_]{0,120}$")
NEGCLASS_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,64}$")
DEF_FIELD_PROBE_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+PROBE_TERM\s+(.+)$")
DEF_FIELD_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+TERM\s+(.+)$")
DEF_FIELD_GOAL_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+GOAL_TERM\s+(.+)$")
MATH_REF_TERM_RE = re.compile(r"Z_MATH_([A-Z0-9_]+)")
MINING_GENERIC_TERM_DENYLIST = {"a0", "a1", "a2", "sim"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _transient_memos_dir(*, run_id: str) -> Path:
    return TRANSIENT_A1_LAWYER_ROOT / str(run_id).strip() / "lawyer_memos"


def _transient_cold_core_dir(*, run_id: str) -> Path:
    return TRANSIENT_A1_COLD_CORE_ROOT / str(run_id).strip() / "cold_core"


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


def _extract_support_terms(value: object) -> list[str]:
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


def _extract_term_from_item_text(item_text: str) -> str:
    goal_term = ""
    term_field = ""
    probe_term = ""
    for raw_line in str(item_text or "").splitlines():
        line = raw_line.strip()
        match = DEF_FIELD_GOAL_TERM_RE.match(line)
        if match:
            value = str(match.group(1)).strip().strip('"')
            if TERM_RE.fullmatch(value):
                goal_term = value
                continue
        match = DEF_FIELD_TERM_RE.match(line)
        if match:
            value = str(match.group(1)).strip().strip('"')
            if TERM_RE.fullmatch(value):
                term_field = value
                continue
        match = DEF_FIELD_PROBE_TERM_RE.match(line)
        if match:
            value = str(match.group(1)).strip().strip('"')
            if TERM_RE.fullmatch(value):
                probe_term = value
                continue
        match = MATH_REF_TERM_RE.search(line)
        if match:
            value = str(match.group(1)).strip().lower()
            if TERM_RE.fullmatch(value):
                return value
    return goal_term or term_field or probe_term


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


def _filter_rescue_targets(
    state: dict,
    rescue_targets: list[str],
    *,
    allowed_terms: set[str] | None = None,
) -> list[str]:
    allowed = {str(x).strip() for x in (allowed_terms or set()) if TERM_RE.fullmatch(str(x).strip())}
    if not allowed:
        return _dedup_keep_order([str(x).strip() for x in rescue_targets if str(x).strip()])

    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    survivor = state.get("survivor_ledger", {}) if isinstance(state.get("survivor_ledger", {}), dict) else {}
    parked = state.get("park_set", {}) if isinstance(state.get("park_set", {}), dict) else {}
    out: list[str] = []
    for raw in rescue_targets:
        target = str(raw).strip()
        if not target:
            continue
        target_term = ""
        if TERM_RE.fullmatch(target):
            target_term = target
        else:
            row = graveyard.get(target) or survivor.get(target) or parked.get(target)
            if isinstance(row, dict):
                target_term = _extract_term_from_item_text(str(row.get("item_text", "")))
        if target_term and target_term in allowed:
            out.append(target)
    return _dedup_keep_order(out)


def _dedup_keep_order(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in rows:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _safe_term_token(value: object) -> str:
    token = str(value).strip().lower()
    if token in MINING_GENERIC_TERM_DENYLIST:
        return ""
    return token if TERM_RE.fullmatch(token) else ""


def _load_schema_json(path: Path, *, expected_schema: str) -> dict:
    payload = _read_json(path)
    if str(payload.get("schema", "")).strip() != expected_schema:
        raise SystemExit(f"schema mismatch for {path}: expected {expected_schema}")
    return payload


def _collect_export_pack_support_terms(path: Path) -> tuple[list[str], list[dict]]:
    payload = _load_schema_json(path, expected_schema="EXPORT_CANDIDATE_PACK_v1")
    terms: list[str] = []
    negative_pressure: list[dict] = []
    for row in payload.get("candidate_items", []) if isinstance(payload.get("candidate_items"), list) else []:
        if not isinstance(row, dict):
            continue
        if str(row.get("anchor_type", "")).strip() != "TERM":
            continue
        term = _safe_term_token(row.get("kernel_anchor") or row.get("source_term"))
        if term:
            terms.append(term)
    for row in payload.get("negative_pressure", []) if isinstance(payload.get("negative_pressure"), list) else []:
        if not isinstance(row, dict):
            continue
        negative_pressure.append(
            {
                "pressure_id": str(row.get("pressure_id", "")).strip(),
                "source_pointer": str(row.get("source_pointer", "")).strip(),
                "text": str(row.get("text", "")).strip(),
            }
        )
    return _dedup_keep_order(terms), negative_pressure


def _collect_fuel_digest_support_terms(path: Path) -> list[str]:
    payload = _load_schema_json(path, expected_schema="FUEL_DIGEST_v1")
    terms: list[str] = []
    for row in payload.get("kernel_candidate_suggestions", []) if isinstance(payload.get("kernel_candidate_suggestions"), list) else []:
        if not isinstance(row, dict):
            continue
        if str(row.get("candidate_type", "")).strip() != "TERM":
            continue
        term = _safe_term_token(row.get("kernel_candidate"))
        if term:
            terms.append(term)
    for row in payload.get("overlay_mapping_suggestions", []) if isinstance(payload.get("overlay_mapping_suggestions"), list) else []:
        if not isinstance(row, dict):
            continue
        if str(row.get("anchor_type", "")).strip() != "TERM":
            continue
        term = _safe_term_token(row.get("kernel_anchor_candidate") or row.get("source_term"))
        if term:
            terms.append(term)
    return _dedup_keep_order(terms)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Strip A1 lawyer memos into cold-core proposals (ratchet-safe tokens only).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--sequence", type=int, default=0, help="Sequence to strip. 0 means infer from sandbox counter or inbox.")
    ap.add_argument("--max-memos", type=int, default=32)
    ap.add_argument("--min-corroboration", type=int, default=2, help="Minimum memo corroboration count for admitting a term candidate.")
    ap.add_argument("--allowed-terms", default="", help="Optional comma-separated allowlist for rescue-target family filtering.")
    ap.add_argument("--export-candidate-pack", action="append", default=[], help="Optional EXPORT_CANDIDATE_PACK_v1 witness; only TERM anchors are admitted as support witnesses.")
    ap.add_argument("--fuel-digest-json", action="append", default=[], help="Optional FUEL_DIGEST_v1 witness; only TERM suggestions are admitted as support witnesses.")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    runs_root = Path(args.runs_root).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"missing run dir: {run_dir}")

    memos_dir = _transient_memos_dir(run_id=run_id)
    if not memos_dir.is_dir():
        raise SystemExit(f"missing memos dir: {memos_dir}")

    sequence = int(args.sequence)
    if sequence <= 0:
        # Prefer sandbox counter, else default to 1.
        counter = run_dir / "a1_sandbox" / "sequence_counter.json"
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
    allowed_terms = {str(x).strip() for x in str(args.allowed_terms).split(",") if TERM_RE.fullmatch(str(x).strip())}
    mining_artifact_inputs = sorted({str(Path(raw).expanduser().resolve()) for raw in [*args.export_candidate_pack, *args.fuel_digest_json] if str(raw).strip()})
    mining_support_terms: list[str] = []
    mining_negative_pressure_witnesses: list[dict] = []
    for raw in sorted(set(args.export_candidate_pack)):
        path = Path(raw).expanduser().resolve()
        terms, negative_pressure = _collect_export_pack_support_terms(path)
        mining_support_terms.extend(terms)
        mining_negative_pressure_witnesses.extend(negative_pressure)
    for raw in sorted(set(args.fuel_digest_json)):
        path = Path(raw).expanduser().resolve()
        mining_support_terms.extend(_collect_fuel_digest_support_terms(path))
    mining_support_terms = sorted({t for t in mining_support_terms if t})
    mining_negative_pressure_witnesses = [
        row for row in mining_negative_pressure_witnesses
        if any(str(row.get(key, "")).strip() for key in ("pressure_id", "source_pointer", "text"))
    ]
    mining_negative_pressure_witnesses = sorted(
        {json.dumps(row, sort_keys=True): row for row in mining_negative_pressure_witnesses}.values(),
        key=lambda row: (str(row.get("source_pointer", "")), str(row.get("pressure_id", "")), str(row.get("text", ""))),
    )

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
    support_terms: list[str] = []
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
        support_terms.extend(_extract_support_terms(obj.get("support_terms")))
        proposed_neg_classes.extend(_extract_neg_classes(obj.get("proposed_negative_classes")))
        rescue_targets.extend(_extract_rescue_targets(obj.get("graveyard_rescue_targets")))

    # Deduplicate deterministically.
    proposed_terms = sorted({t for t in proposed_terms if t})
    support_terms = sorted({t for t in support_terms if t})
    proposed_neg_classes = sorted({c for c in proposed_neg_classes if c})
    rescue_targets = _dedup_keep_order([r for r in rescue_targets if r])
    # If memos didn't provide rescue hints, fall back to recent kills so the
    # graveyard becomes an active workspace rather than a passive sink.
    if not rescue_targets:
        rescue_targets = _recent_kill_targets(state, limit=16)
    rescue_targets = _filter_rescue_targets(state, rescue_targets, allowed_terms=allowed_terms)

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

    # Derive support-role atomics from admissible compounds when the memos did
    # not provide enough explicit support structure. This gives downstream A1
    # consumers a cleaner witness/bootstrap floor instead of forcing them to
    # reconstruct it from `need_atomic_bootstrap` alone.
    derived_support_terms: list[str] = []
    support_seed = set(support_terms)
    for term in admissible_term_candidates:
        if "_" not in term:
            continue
        for comp in term.split("_"):
            if not comp:
                continue
            if comp in canon or comp in l0:
                continue
            if comp not in need_atomic_bootstrap:
                continue
            support_seed.add(comp)
    derived_support_terms = sorted({t for t in support_seed if t} | set(mining_support_terms))

    out_obj = {
        "schema": "A1_COLD_CORE_PROPOSALS_v1",
        "run_id": run_id,
        "sequence": sequence,
        "memo_count": len(memo_objs),
        "roles_present": sorted(roles_present),
        "proposed_terms_raw": proposed_terms,
        "support_terms_raw": support_terms,
        "admissible_term_candidates": sorted({t for t in admissible_term_candidates}),
        "support_term_candidates": derived_support_terms,
        "mining_support_terms": mining_support_terms,
        "need_atomic_bootstrap": sorted({t for t in need_atomic_bootstrap}),
        "min_corroboration": int(min_corroboration),
        "proposed_negative_classes": proposed_neg_classes,
        "graveyard_rescue_targets": rescue_targets,
        "mining_artifact_inputs": mining_artifact_inputs,
        "mining_negative_pressure_witnesses": mining_negative_pressure_witnesses,
        "state_hash": str(state.get("state_hash", "")) if isinstance(state, dict) else "",
    }
    out_bytes = (json.dumps(out_obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    out_obj["proposals_sha256"] = _sha256_bytes(out_bytes)
    out_bytes = (json.dumps(out_obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

    out_dir = _transient_cold_core_dir(run_id=run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{sequence:06d}_A1_COLD_CORE_PROPOSALS_v1.json"
    out_path.write_bytes(out_bytes)
    print(
        json.dumps(
            {
                "schema": out_obj["schema"],
                "sequence": int(sequence),
                "out": str(out_path),
                "cold_core_path_class": "transient_store",
                "cold_core_sha256": str(out_obj.get("proposals_sha256", "")).strip(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
