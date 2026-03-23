#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

from a1_selector_warning_snapshot import build_process_warning_snapshot, build_selector_warning_snapshot


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
TRANSIENT_A1_COLD_CORE_ROOT = REPO / "work" / "a1_transient_cold_core"

BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
PLANNER_PATH = BOOTPACK / "tools" / "a1_adaptive_ratchet_planner.py"
CORE_PROBE_ANCHORS = (
    "finite_dimensional_hilbert_space",
    "density_matrix",
    "probe_operator",
    "cptp_channel",
    "unitary_operator",
    "partial_trace",
    "correlation_polarity",
    "qit_master_conjunction",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _transient_cold_core_dir(*, run_id: str) -> Path:
    return TRANSIENT_A1_COLD_CORE_ROOT / str(run_id).strip() / "cold_core"


def _run_local_cold_core_dir(*, run_dir: Path) -> Path:
    return run_dir / "a1_sandbox" / "cold_core"


def _default_cold_core_path(*, run_dir: Path, run_id: str) -> Path:
    searched: list[Path] = []
    for cold_dir in (
        _run_local_cold_core_dir(run_dir=run_dir),
        _transient_cold_core_dir(run_id=run_id),
    ):
        searched.append(cold_dir)
        if not cold_dir.is_dir():
            continue
        candidates = sorted(cold_dir.glob("*_A1_COLD_CORE_PROPOSALS_v1.json"))
        if candidates:
            return candidates[-1]
    search_str = ", ".join(str(path) for path in searched)
    raise SystemExit(f"no cold core proposals found in: {search_str}")


def _cold_core_path_class(*, cold_core_path: Path, run_dir: Path, run_id: str) -> str:
    path = cold_core_path.resolve()
    if path.parent == _run_local_cold_core_dir(run_dir=run_dir).resolve():
        return "run_local_sandbox"
    if path.parent == _transient_cold_core_dir(run_id=run_id).resolve():
        return "transient_store"
    return "external_path"


def _cold_core_source_label(*, cold_core_path: Path, run_dir: Path, run_id: str, explicit_override: bool) -> str:
    path_class = _cold_core_path_class(cold_core_path=cold_core_path, run_dir=run_dir, run_id=run_id)
    if explicit_override:
        return "explicit_arg"
    if path_class == "run_local_sandbox":
        return "run_local_sandbox"
    if path_class == "transient_store":
        return "transient_fallback"
    return "external_path"


def _cold_core_basename_sequence(cold_core_path: Path) -> int:
    m = re.match(r"^(\d+)_A1_COLD_CORE_PROPOSALS_v1\.json$", str(cold_core_path.name).strip())
    if not m:
        return 0
    return int(m.group(1) or 0)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


_DEF_FIELD_PROBE_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+PROBE_TERM\s+(.+)$")
_DEF_FIELD_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+TERM\s+(.+)$")
_DEF_FIELD_GOAL_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+GOAL_TERM\s+(.+)$")
_MATH_REF_TERM_RE = re.compile(r"Z_MATH_([A-Z0-9_]+)")
_TERM_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{0,120}$")
_JSON_CODE_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_term_from_item_text(item_text: str) -> str:
    goal_term = ""
    term_field = ""
    probe_term = ""
    for raw_line in str(item_text or "").splitlines():
        line = raw_line.strip()
        m = _DEF_FIELD_GOAL_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if _TERM_TOKEN_RE.fullmatch(value):
                goal_term = value
                continue
        m = _DEF_FIELD_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if _TERM_TOKEN_RE.fullmatch(value):
                term_field = value
                continue
        m = _DEF_FIELD_PROBE_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if _TERM_TOKEN_RE.fullmatch(value):
                probe_term = value
                continue
        m = _MATH_REF_TERM_RE.search(line)
        if m:
            value = str(m.group(1)).strip().lower()
            if _TERM_TOKEN_RE.fullmatch(value):
                return value
    return goal_term or term_field or probe_term


def _rescue_terms_from_targets(state: dict, targets: list[str]) -> list[str]:
    if not targets:
        return []
    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    survivor = state.get("survivor_ledger", {}) if isinstance(state.get("survivor_ledger", {}), dict) else {}
    parked = state.get("park_set", {}) if isinstance(state.get("park_set", {}), dict) else {}
    out: list[str] = []
    for raw in targets:
        target = str(raw).strip()
        if not target:
            continue
        if _TERM_TOKEN_RE.fullmatch(target):
            out.append(target)
            continue
        row = graveyard.get(target) or survivor.get(target) or parked.get(target)
        if isinstance(row, dict):
            term = _extract_term_from_item_text(str(row.get("item_text", "")))
            if term:
                out.append(term)
    dedup: list[str] = []
    seen: set[str] = set()
    for term in out:
        if term in seen:
            continue
        seen.add(term)
        dedup.append(term)
    return dedup


def _filter_rescue_targets_and_terms(
    state: dict,
    rescue_targets: list[str],
    rescue_terms: list[str],
    *,
    allowed_terms: set[str],
) -> tuple[list[str], list[str]]:
    if not allowed_terms:
        return rescue_targets, rescue_terms
    allowed = {str(x).strip() for x in allowed_terms if _TERM_TOKEN_RE.fullmatch(str(x).strip())}
    if not allowed:
        return [], []
    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    survivor = state.get("survivor_ledger", {}) if isinstance(state.get("survivor_ledger", {}), dict) else {}
    parked = state.get("park_set", {}) if isinstance(state.get("park_set", {}), dict) else {}
    filtered_targets: list[str] = []
    for raw in rescue_targets:
        target = str(raw).strip()
        if not target:
            continue
        target_term = ""
        if _TERM_TOKEN_RE.fullmatch(target):
            target_term = target
        else:
            row = graveyard.get(target) or survivor.get(target) or parked.get(target)
            if isinstance(row, dict):
                target_term = _extract_term_from_item_text(str(row.get("item_text", "")))
        if target_term and target_term in allowed and target not in filtered_targets:
            filtered_targets.append(target)
    filtered_terms: list[str] = []
    for term in rescue_terms:
        candidate = str(term).strip()
        if candidate and candidate in allowed and candidate not in filtered_terms:
            filtered_terms.append(candidate)
    return filtered_targets, filtered_terms


def _graveyard_terms(state: dict) -> set[str]:
    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    out: set[str] = set()
    for row in graveyard.values():
        if not isinstance(row, dict):
            continue
        term = _extract_term_from_item_text(str(row.get("item_text", "")))
        if term:
            out.add(term)
    return out


def _support_bootstrap_terms(
    proposals: dict,
    *,
    allowed_terms: list[str],
    canon: set[str],
) -> list[str]:
    support_raw = [
        str(x).strip()
        for x in (proposals.get("support_term_candidates", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(x).strip())
    ]
    bootstrap_raw = {
        str(x).strip()
        for x in (proposals.get("need_atomic_bootstrap", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(x).strip())
    }
    if not support_raw or not bootstrap_raw:
        return []
    required_components: set[str] = set()
    for term in allowed_terms:
        candidate = str(term).strip()
        if not candidate or "_" not in candidate:
            continue
        for comp in candidate.split("_"):
            if _TERM_TOKEN_RE.fullmatch(comp):
                required_components.add(comp)
    out: list[str] = []
    for raw in support_raw:
        term = str(raw).strip()
        if not term or "_" in term or term in canon:
            continue
        if term not in bootstrap_raw:
            continue
        if required_components and term not in required_components:
            continue
        if term not in out:
            out.append(term)
    return out


@lru_cache(maxsize=1)
def _family_hint_sources() -> tuple[Path, ...]:
    out: list[Path] = []
    for path in sorted((SYSTEM_V3 / "a1_state").glob("A1*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if "A1_ADMISSIBILITY_HINTS_v1" in text:
            out.append(path)
    return tuple(out)


def _load_family_admissibility_hints(*, selected_terms: list[str]) -> dict:
    selected = {str(t).strip() for t in selected_terms if _TERM_TOKEN_RE.fullmatch(str(t).strip())}
    if not selected:
        return {}
    matched_blocks: list[dict[str, object]] = []
    merged: dict[str, object] = {
        "activation_terms": [],
        "active_companion_floor_terms": [],
        "strategy_head_terms": [],
        "forbid_strategy_head_terms": [],
        "late_passenger_terms": [],
        "witness_only_terms": [],
        "residue_only_terms": [],
        "landing_blocker_overrides": {},
    }
    for path in _family_hint_sources():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in _JSON_CODE_BLOCK_RE.finditer(text):
            try:
                obj = json.loads(match.group(1))
            except Exception:
                continue
            if str(obj.get("schema", "")).strip() != "A1_ADMISSIBILITY_HINTS_v1":
                continue
            activation_terms = {
                str(raw).strip()
                for raw in (obj.get("activation_terms", []) or [])
                if _TERM_TOKEN_RE.fullmatch(str(raw).strip())
            }
            if activation_terms and selected.isdisjoint(activation_terms):
                continue
            related_terms: set[str] = set()
            for key in (
                "strategy_head_terms",
                "forbid_strategy_head_terms",
                "late_passenger_terms",
                "witness_only_terms",
                "residue_only_terms",
            ):
                for raw in (obj.get(key, []) or []):
                    term = str(raw).strip()
                    if _TERM_TOKEN_RE.fullmatch(term):
                        related_terms.add(term)
            for term in (obj.get("landing_blocker_overrides", {}) or {}).keys():
                t = str(term).strip()
                if _TERM_TOKEN_RE.fullmatch(t):
                    related_terms.add(t)
            if selected.isdisjoint(related_terms):
                continue
            companion_terms = _extract_terms_from_markdown_section(
                text,
                section_label="active_companion_floor",
                before_index=match.start(),
            )
            matched_blocks.append(
                {
                    "obj": obj,
                    "family": str(obj.get("family", "") or obj.get("family_label", "")).strip(),
                    "companion_terms": companion_terms,
                    "strategy_head_terms": [
                        str(raw).strip()
                        for raw in (obj.get("strategy_head_terms", []) or [])
                        if _TERM_TOKEN_RE.fullmatch(str(raw).strip())
                    ],
                    "is_executable": "executable" in str(obj.get("family", "") or obj.get("family_label", "")).strip().lower(),
                }
            )
    prefer_executable_blocks = any(bool(block.get("is_executable")) for block in matched_blocks)
    for block in matched_blocks:
        obj = block.get("obj", {})
        if not isinstance(obj, dict):
            continue
        is_executable = bool(block.get("is_executable"))
        current_companions = list(merged.get("active_companion_floor_terms", []))
        for term in (block.get("companion_terms", []) or []):
            if isinstance(term, str) and term not in current_companions:
                current_companions.append(term)
        merged["active_companion_floor_terms"] = current_companions
        for key in (
            "activation_terms",
            "strategy_head_terms",
            "forbid_strategy_head_terms",
            "late_passenger_terms",
            "witness_only_terms",
            "residue_only_terms",
        ):
            current = list(merged.get(key, []))
            for raw in (obj.get(key, []) or []):
                term = str(raw).strip()
                if not _TERM_TOKEN_RE.fullmatch(term):
                    continue
                if (
                    key in {"activation_terms", "late_passenger_terms", "witness_only_terms"}
                    and prefer_executable_blocks
                    and not is_executable
                    and term not in selected
                ):
                    continue
                if term not in current:
                    current.append(term)
            merged[key] = current
        blocker_map = dict(merged.get("landing_blocker_overrides", {}))
        for raw_term, raw_msg in (obj.get("landing_blocker_overrides", {}) or {}).items():
            term = str(raw_term).strip()
            msg = str(raw_msg).strip()
            if _TERM_TOKEN_RE.fullmatch(term) and msg:
                blocker_map[term] = msg
        merged["landing_blocker_overrides"] = blocker_map
    return merged


def _extract_terms_from_markdown_section(text: str, *, section_label: str, before_index: int) -> list[str]:
    marker = f"- `{section_label}`"
    prefix = text[: max(0, int(before_index))]
    start = prefix.rfind(marker)
    if start < 0:
        return []
    tail = text[start:].splitlines()
    out: list[str] = []
    for line in tail[1:]:
        if not line.startswith("  "):
            break
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        if stripped.startswith("- `"):
            end = stripped.find("`", 3)
            if end > 3:
                term = stripped[3:end].strip()
                if _TERM_TOKEN_RE.fullmatch(term) and term not in out:
                    out.append(term)
    return out


def _strategy_observed_terms(strategy: dict) -> list[str]:
    out: list[str] = []
    if not isinstance(strategy, dict):
        return out
    for bucket in ("targets", "alternatives"):
        for item in (strategy.get(bucket, []) or []):
            if not isinstance(item, dict):
                continue
            for row in (item.get("def_fields", []) or []):
                if not isinstance(row, dict):
                    continue
                name = str(row.get("name", "")).strip()
                if name not in {"GOAL_TERM", "TERM", "PROBE_TERM"}:
                    continue
                value = str(row.get("value", "")).strip()
                if _TERM_TOKEN_RE.fullmatch(value) and value not in out:
                    out.append(value)
    return out


def _resolve_target_terms(
    *,
    goal_terms: list[str],
    observed_terms: list[str],
    family_hints: dict,
    target_scope_terms: list[str] | None = None,
) -> list[str]:
    goal_order = [str(t).strip() for t in goal_terms if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    observed_order = [str(t).strip() for t in observed_terms if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    scope_order = [str(t).strip() for t in (target_scope_terms or []) if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    scope_set = set(scope_order)
    goal_set = set(goal_order)
    observed_set = set(observed_order)
    hinted_terms: set[str] = set()
    target_role_terms: set[str] = set()
    for key in (
        "activation_terms",
        "strategy_head_terms",
        "forbid_strategy_head_terms",
        "late_passenger_terms",
        "witness_only_terms",
        "residue_only_terms",
    ):
        for raw in (family_hints.get(key, []) or []):
            term = str(raw).strip()
            if _TERM_TOKEN_RE.fullmatch(term):
                hinted_terms.add(term)
                if key in {"strategy_head_terms", "forbid_strategy_head_terms", "late_passenger_terms"}:
                    target_role_terms.add(term)
    for raw in (family_hints.get("landing_blocker_overrides", {}) or {}).keys():
        term = str(raw).strip()
        if _TERM_TOKEN_RE.fullmatch(term):
            hinted_terms.add(term)
            target_role_terms.add(term)

    out: list[str] = []

    def add(term: str) -> None:
        t = str(term).strip()
        if not _TERM_TOKEN_RE.fullmatch(t):
            return
        if t not in out:
            out.append(t)

    for raw in (family_hints.get("strategy_head_terms", []) or []):
        term = str(raw).strip()
        if term in goal_set or term in observed_set:
            add(term)
    for term in goal_order:
        if "_" in term or term in hinted_terms or term in observed_set:
            add(term)
    for term in observed_order:
        if term in target_role_terms or term in goal_set:
            add(term)
    if out:
        if scope_set:
            filtered = [t for t in out if t in scope_set]
            return filtered if filtered else scope_order
        return out
    for term in goal_order + observed_order:
        add(term)
    if scope_set:
        filtered = [t for t in out if t in scope_set]
        return filtered if filtered else scope_order
    return out


def _filter_fragment_focus_terms(goal_terms: list[str]) -> list[str]:
    ordered = [str(t).strip() for t in goal_terms if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    if not ordered:
        return []
    family_hints = _load_family_admissibility_hints(selected_terms=ordered)
    hinted_terms: set[str] = set()
    for key in (
        "activation_terms",
        "active_companion_floor_terms",
        "strategy_head_terms",
        "forbid_strategy_head_terms",
        "late_passenger_terms",
        "witness_only_terms",
        "residue_only_terms",
    ):
        for raw in (family_hints.get(key, []) or []):
            term = str(raw).strip()
            if _TERM_TOKEN_RE.fullmatch(term):
                hinted_terms.add(term)
    for raw in (family_hints.get("landing_blocker_overrides", {}) or {}).keys():
        term = str(raw).strip()
        if _TERM_TOKEN_RE.fullmatch(term):
            hinted_terms.add(term)
    anchored_compounds = [
        term for term in ordered
        if "_" in term and term in hinted_terms
    ]
    if not anchored_compounds:
        return ordered
    drop_atoms: set[str] = set()
    for term in ordered:
        if "_" in term or term in hinted_terms:
            continue
        if any(term in compound.split("_") for compound in anchored_compounds):
            drop_atoms.add(term)
    return [term for term in ordered if term not in drop_atoms]


def _family_scope_terms(
    *,
    selected_terms: list[str],
    observed_terms: list[str],
    support_bootstrap_candidates: list[str],
    rescue_terms: list[str],
    family_hints: dict,
) -> list[str]:
    out: list[str] = []
    anchored_terms = {
        str(t).strip()
        for t in list(selected_terms) + list(observed_terms) + list(support_bootstrap_candidates) + list(rescue_terms)
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    }
    activation_terms = {
        str(t).strip()
        for t in (family_hints.get("activation_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    }

    def add(term: str) -> None:
        t = str(term).strip()
        if not _TERM_TOKEN_RE.fullmatch(t):
            return
        if t not in out:
            out.append(t)

    for term in selected_terms:
        add(term)
    for key in (
        "activation_terms",
        "strategy_head_terms",
        "forbid_strategy_head_terms",
        "late_passenger_terms",
    ):
        for term in (family_hints.get(key, []) or []):
            add(str(term).strip())
    for term in (family_hints.get("witness_only_terms", []) or []):
        t = str(term).strip()
        if t in activation_terms or t in anchored_terms:
            add(t)
    for term in (family_hints.get("landing_blocker_overrides", {}) or {}).keys():
        add(str(term).strip())
    for term in (family_hints.get("residue_only_terms", []) or []):
        t = str(term).strip()
        if t in anchored_terms:
            add(t)

    scope_set = set(out)
    for term in list(observed_terms) + list(support_bootstrap_candidates) + list(rescue_terms):
        t = str(term).strip()
        if t in scope_set:
            add(t)
    if not out:
        for term in observed_terms:
            add(term)
    return out


def _build_admissibility_block(
    *,
    strategy: dict,
    state: dict,
    selected_terms: list[str],
    observed_terms: list[str],
    canon: set[str],
    support_bootstrap_candidates: list[str],
    rescue_terms: list[str],
    family_hints: dict,
    cold_core_source: str,
    cold_core_path_class: str,
    cold_core_sha256: str,
    cold_core_sequence: int,
    cold_core_basename_sequence: int,
    selector_sequence: int,
    target_scope_terms: list[str],
) -> dict:
    selected = [str(t).strip() for t in selected_terms if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    observed = [str(t).strip() for t in observed_terms if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    target_scope_order = [
        str(t).strip()
        for t in target_scope_terms
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    ]
    target_scope_set = set(target_scope_order)
    if not selected and not observed:
        return {}
    family_scope = _family_scope_terms(
        selected_terms=selected,
        observed_terms=observed,
        support_bootstrap_candidates=support_bootstrap_candidates,
        rescue_terms=rescue_terms,
        family_hints=family_hints,
    )
    scope_set = set(family_scope)
    if not scope_set:
        return {}

    all_hint_heads = [
        str(t).strip()
        for t in (family_hints.get("strategy_head_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    ]
    hint_heads = [t for t in all_hint_heads if t in scope_set]
    forbid_heads = {
        str(t).strip() for t in (family_hints.get("forbid_strategy_head_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    }
    hinted_witnesses = {
        str(t).strip()
        for t in (family_hints.get("witness_only_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    }
    hinted_activations = {
        str(t).strip()
        for t in (family_hints.get("activation_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    }
    active_witness_hints = {
        t for t in hinted_witnesses
        if t in scope_set or t in hinted_activations or t in selected or t in observed
    }
    hinted_companions = [
        str(t).strip()
        for t in (family_hints.get("active_companion_floor_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    ]
    hinted_late_all = {
        str(t).strip()
        for t in (family_hints.get("late_passenger_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    }
    hinted_residue = {
        str(t).strip() for t in (family_hints.get("residue_only_terms", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip())
    }
    hinted_fallback = [t for t in all_hint_heads if t not in forbid_heads and t in scope_set]
    use_hinted_head = bool(
        hinted_fallback
        and any(t in scope_set for t in forbid_heads | active_witness_hints | hinted_late_all)
    )

    head_source = selected or observed or family_scope
    head = hint_heads[:1] if hint_heads else (hinted_fallback[:1] if use_hinted_head else head_source[:1])
    if head and head[0] in forbid_heads:
        fallback = [t for t in head_source if t not in forbid_heads]
        if fallback:
            head = fallback[:1]
        else:
            head = hinted_fallback[:1]
    if not head:
        head = head_source[:1]
    companions: list[str] = []
    hinted_late = [
        t for t in (family_hints.get("late_passenger_terms", []) or [])
        if t in scope_set and t not in head and t not in companions and t not in active_witness_hints
    ]
    late_passengers = hinted_late + [
        t
        for t in selected
        if t not in companions and t not in hinted_late and t not in head and t not in active_witness_hints
    ]
    for term in hinted_companions:
        if term in head or term in companions or term in late_passengers or term in hinted_residue:
            continue
        companions.append(term)
        if len(companions) >= 2:
            break
    for term in family_scope:
        if term in head or term not in canon:
            continue
        if term in companions or term in forbid_heads or term in hinted_late_all or term in hinted_residue:
            continue
        if term in active_witness_hints and term not in hinted_companions:
            continue
        companions.append(term)
        if len(companions) >= 2:
            break

    witness_only_terms: list[str] = []
    for term in list(family_hints.get("witness_only_terms", []) or []) + list(support_bootstrap_candidates) + list(rescue_terms):
        t = str(term).strip()
        if not _TERM_TOKEN_RE.fullmatch(t):
            continue
        if t not in scope_set and t not in active_witness_hints:
            continue
        if t in head or t in companions or t in late_passengers:
            continue
        if t in hinted_residue and t not in hinted_witnesses and t not in support_bootstrap_candidates:
            continue
        if target_scope_set and t not in target_scope_set and t not in hinted_witnesses and t not in support_bootstrap_candidates:
            continue
        if t not in witness_only_terms:
            witness_only_terms.append(t)
    selected_witness_only_terms = [t for t in selected if t in witness_only_terms]
    if selected_witness_only_terms:
        witness_only_terms = selected_witness_only_terms + [
            t for t in witness_only_terms
            if t not in selected_witness_only_terms
        ]

    residue_terms: list[str] = []
    for t in family_scope:
        if t not in hinted_residue:
            continue
        if t in head or t in companions or t in late_passengers or t in witness_only_terms:
            continue
        residue_terms.append(t)

    landing_blockers: list[str] = []
    blocker_overrides = dict(family_hints.get("landing_blocker_overrides", {}) or {})
    selected_non_head = [t for t in selected if t not in head]
    selected_witness_only_terms = [t for t in selected_non_head if t in witness_only_terms]
    selected_passenger_terms = [
        t for t in selected_non_head
        if t in late_passengers and t not in selected_witness_only_terms
    ]
    for t in selected_non_head:
        msg = str(blocker_overrides.get(t, "")).strip()
        if msg and msg not in landing_blockers:
            landing_blockers.append(msg)
    if selected_passenger_terms and not landing_blockers:
        landing_blockers.append("non-head selected terms still require clearer landing support before promotion")
    selected_witness_without_override = [
        t for t in selected_witness_only_terms
        if not str(blocker_overrides.get(t, "")).strip()
    ]
    if selected_witness_without_override:
        landing_blockers.append("witness-only selected terms remain support-side and should not be treated as executable heads")

    current_readiness_status: dict[str, str] = {}
    for term in head:
        current_readiness_status[term] = "HEAD_READY"
    for term in companions:
        if term not in current_readiness_status:
            current_readiness_status[term] = "COMPANION_FLOOR"
    for term in late_passengers:
        if term not in current_readiness_status:
            current_readiness_status[term] = "PASSENGER_ONLY"
    for term in witness_only_terms:
        if term not in current_readiness_status:
            current_readiness_status[term] = "WITNESS_ONLY"
    for term in selected:
        if term not in current_readiness_status:
            current_readiness_status[term] = "PROPOSAL_ONLY"
    for term in residue_terms:
        if term not in current_readiness_status:
            current_readiness_status[term] = "RESIDUE_ONLY"

    sims = strategy.get("sims", {}) if isinstance(strategy.get("sims", {}), dict) else {}
    positive_sims = sims.get("positive", []) if isinstance(sims.get("positive", []), list) else []
    negative_sims = sims.get("negative", []) if isinstance(sims.get("negative", []), list) else []
    inputs = strategy.get("inputs", {}) if isinstance(strategy.get("inputs", {}), dict) else {}
    evidence_summary_hash = str(inputs.get("evidence_summary_hash", "")).strip()
    state_sim_results = state.get("sim_results", {}) if isinstance(state.get("sim_results", {}), dict) else {}
    state_sim_evidence_hash = ""
    if state_sim_results:
        state_sim_evidence_hash = hashlib.sha256(
            json.dumps(state_sim_results, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    wiggle_minimum_content_ok = bool(
        strategy.get("targets")
        and strategy.get("alternatives")
        and positive_sims
        and negative_sims
    )
    evidence_gated_promotion_ok = bool(head) and not any(
        term in head for term in late_passengers + witness_only_terms + residue_terms
    )
    sim_evidence_boundary_ok = isinstance(sims, dict) and bool(positive_sims or negative_sims)
    hash_anchored_sim_evidence_ok = bool(evidence_summary_hash or state_sim_evidence_hash)
    classified_family_terms = len({*head, *companions, *late_passengers, *witness_only_terms})
    movement_over_throughput_ok = len(head) + len(companions) >= 1 and len(residue_terms) <= max(8, classified_family_terms)
    canonical_recovery_anchors = [
        t for t in rescue_terms
        if t in canon and t in scope_set
    ]
    pending_frontier_terms = [
        t for t in selected
        if t not in canon
    ]
    witness_floor: list[str] = []
    for term in companions:
        if term not in witness_floor:
            witness_floor.append(term)
    support_witness_candidates = [
        t for t in witness_only_terms
        if t not in canonical_recovery_anchors and t not in pending_frontier_terms
    ]
    if companions and support_witness_candidates:
        witness_floor.append(support_witness_candidates[0])
    elif not companions:
        for term in witness_only_terms:
            if term not in witness_floor:
                witness_floor.append(term)

    out_of_scope_family_terms: list[str] = []
    if target_scope_set:
        for term in head + companions + late_passengers + witness_only_terms:
            if term not in target_scope_set and term not in out_of_scope_family_terms:
                out_of_scope_family_terms.append(term)

    process_warnings: list[str] = []
    if not wiggle_minimum_content_ok:
        process_warnings.append("wiggle minimum content is incomplete: targets, alternatives, and both positive/negative sim lanes should be present")
    if not movement_over_throughput_ok:
        process_warnings.append("residue/load is dominating strategy output; do not treat term volume as movement")
    if not evidence_gated_promotion_ok:
        process_warnings.append("non-head material is still too close to executable promotion lanes")
    if not sim_evidence_boundary_ok:
        process_warnings.append("sim evidence boundary is weak: strategy is not carrying a clear positive/negative sims split")
    if sim_evidence_boundary_ok and not hash_anchored_sim_evidence_ok:
        process_warnings.append("sim evidence is not hash-anchored by either inputs.evidence_summary_hash or state-backed sim digest")
    if str(cold_core_source).strip() == "transient_fallback":
        process_warnings.append("selector used transient cold-core fallback; regenerate run-local cold_core when possible")
    if str(cold_core_path_class).strip() == "external_path":
        process_warnings.append("selector used external cold-core path; run-local regeneration provenance is bypassed")
    if (
        str(cold_core_source).strip() == "explicit_arg"
        and int(cold_core_basename_sequence) > 0
        and int(cold_core_basename_sequence) != int(cold_core_sequence)
    ):
        process_warnings.append("explicit cold-core basename sequence mismatches payload sequence; provenance may reflect a renamed or swapped artifact")
    if (
        int(selector_sequence) > 0
        and int(cold_core_sequence) > 0
        and int(selector_sequence) != int(cold_core_sequence)
    ):
        process_warnings.append("selector output sequence differs from cold-core payload sequence; direct caller override may have split regeneration provenance")
    if target_scope_set and out_of_scope_family_terms:
        process_warnings.append("target scope clamp is narrower than family role context; use target_terms for local selection and admissibility for surrounding family context")

    process_audit = {
        "wiggle_minimum_content_ok": wiggle_minimum_content_ok,
        "movement_over_throughput_ok": movement_over_throughput_ok,
        "evidence_gated_promotion_ok": evidence_gated_promotion_ok,
        "sim_evidence_boundary_ok": sim_evidence_boundary_ok,
        "hash_anchored_sim_evidence_ok": hash_anchored_sim_evidence_ok,
        "canonical_recovery_anchors": canonical_recovery_anchors,
        "cold_core_sequence": int(cold_core_sequence),
        "cold_core_basename_sequence": int(cold_core_basename_sequence),
        "selector_sequence": int(selector_sequence),
        "target_scope_terms": target_scope_order,
        "out_of_scope_family_terms": out_of_scope_family_terms,
        "cold_core_source": str(cold_core_source).strip(),
        "cold_core_path_class": str(cold_core_path_class).strip(),
        "cold_core_sha256": str(cold_core_sha256).strip(),
        "state_sim_evidence_hash": state_sim_evidence_hash,
        "warnings": process_warnings,
    }
    process_audit.update(build_process_warning_snapshot(process_warnings))

    return {
        "executable_head": head,
        "active_companion_floor": companions,
        "late_passengers": late_passengers,
        "witness_only_terms": witness_only_terms,
        "residue_terms": residue_terms,
        "witness_floor": witness_floor,
        "current_readiness_status": current_readiness_status,
        "landing_blockers": landing_blockers,
        "process_audit": process_audit,
    }


def _filter_family_recovery_rescue_terms(*, raw_candidates: list[str], rescue_terms: list[str]) -> list[str]:
    frontier = [str(t).strip() for t in raw_candidates if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    if not frontier:
        return rescue_terms
    family_hints = _load_family_admissibility_hints(selected_terms=frontier)
    anchored = set(frontier)
    for key in (
        "activation_terms",
        "active_companion_floor_terms",
        "strategy_head_terms",
        "late_passenger_terms",
        "witness_only_terms",
    ):
        for raw in (family_hints.get(key, []) or []):
            term = str(raw).strip()
            if _TERM_TOKEN_RE.fullmatch(term):
                anchored.add(term)
    filtered: list[str] = []
    for raw in rescue_terms:
        term = str(raw).strip()
        if term in anchored and term not in filtered:
            filtered.append(term)
    return filtered


def _refine_handoff_target_terms(*, target_terms: list[str], admissibility: dict, canon: set[str]) -> list[str]:
    ordered = [str(t).strip() for t in target_terms if _TERM_TOKEN_RE.fullmatch(str(t).strip())]
    if not ordered or not isinstance(admissibility, dict):
        return ordered
    pending_frontier_terms = [
        t for t in ordered
        if t not in canon
    ]
    canonical_heads = {
        str(t).strip()
        for t in (admissibility.get("executable_head", []) or [])
        if _TERM_TOKEN_RE.fullmatch(str(t).strip()) and str(t).strip() in canon
    }
    # Local handoff should emphasize unresolved frontier work when multiple
    # pending structure terms remain. Canonical executable heads still remain
    # visible in admissibility and family_terms.
    if len(pending_frontier_terms) >= 2 and canonical_heads:
        refined = [t for t in pending_frontier_terms if t in ordered or t not in canon]
        if refined:
            return refined
    return ordered


def _strategy_family_terms(strategy_terms: list[str], admissibility: dict) -> list[str]:
    out: list[str] = []

    def add(term: str) -> None:
        t = str(term).strip()
        if not _TERM_TOKEN_RE.fullmatch(t):
            return
        if t not in out:
            out.append(t)

    if not isinstance(admissibility, dict):
        for term in strategy_terms:
            add(term)
        return out

    for key in (
        "executable_head",
        "active_companion_floor",
        "late_passengers",
        "witness_only_terms",
        "witness_floor",
    ):
        for term in (admissibility.get(key, []) or []):
            add(term)

    for term in strategy_terms:
        add(term)

    return out


def _negative_markers_for_class(neg_cls: str) -> tuple[tuple[str, str], ...]:
    c = str(neg_cls).strip().upper()
    if c == "CLASSICAL_TIME":
        return (("TIME_PARAM", "T"),)
    if c == "INFINITE_SET":
        return (("ASSUME_INFINITE", "TRUE"), ("INFINITE_SET", "TRUE"))
    if c == "CONTINUOUS_BATH":
        return (("CONTINUOUS_BATH", "TRUE"),)
    if c == "INFINITE_RESOLUTION":
        return (("INFINITE_RESOLUTION", "TRUE"),)
    if c == "PRIMITIVE_EQUALS":
        return (("EQUALS_PRIMITIVE", "TRUE"), ("ASSUME_IDENTITY_EQUIVALENCE", "TRUE"))
    if c == "EUCLIDEAN_METRIC":
        return (("EUCLIDEAN_METRIC", "TRUE"), ("CARTESIAN_COORDINATE", "TRUE"))
    if c == "CLASSICAL_TEMPERATURE":
        return (("TEMPERATURE_BATH", "TRUE"), ("TEMPERATURE_PARAM", "K"))
    # Default: commutation smuggle.
    return (("ASSUME_COMMUTATIVE", "TRUE"),)


def _parse_csv_terms(raw: str) -> set[str]:
    out: set[str] = set()
    for part in str(raw or "").split(","):
        t = part.strip()
        if not t:
            continue
        if _TERM_TOKEN_RE.fullmatch(t):
            out.add(t)
    return out


def _parse_csv_terms_ordered(raw: str) -> list[str]:
    out: list[str] = []
    for part in str(raw or "").split(","):
        t = part.strip()
        if not t:
            continue
        if _TERM_TOKEN_RE.fullmatch(t) and t not in out:
            out.append(t)
    return out


@dataclass(frozen=True)
class Goal:
    term: str
    track: str
    negative_class: str
    negative_markers: tuple[tuple[str, str], ...]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Select a batch from cold-core proposals and emit A1_STRATEGY_v1 (schema-valid).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--cold-core", default="", help="Path to A1_COLD_CORE_PROPOSALS_v1.json. Default: run sandbox cold_core latest.")
    ap.add_argument("--sequence", type=int, default=0, help="Sequence for naming only (0 means infer from cold-core).")
    ap.add_argument("--track", default="ENGINE_ENTROPY_EXPLORATION")
    ap.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="graveyard_first")
    ap.add_argument("--goal-selection", choices=["interleaved", "closure_first"], default="interleaved")
    ap.add_argument(
        "--graveyard-fill-policy",
        choices=["anchor_replay", "fuel_full_load"],
        default="anchor_replay",
        help="In graveyard_first mode, choose anchor replay (legacy) or fuel_full_load (prioritize un-graveyarded fuel terms).",
    )
    ap.add_argument(
        "--forbid-rescue-in-graveyard-first",
        action="store_true",
        help="If set, remove RESCUE_FROM bindings from alternatives while in graveyard_first mode.",
    )
    ap.add_argument(
        "--max-terms",
        type=int,
        default=0,
        help="Optional override for max number of term goals selected in this strategy.",
    )
    ap.add_argument(
        "--graveyard-library-terms",
        default="",
        help="Comma-separated term tokens that should be treated as graveyard-library only (never rescued).",
    )
    ap.add_argument(
        "--allowed-terms",
        default="",
        help="Optional comma-separated hard allowlist for term goals after cold-core filtering.",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    runs_root = Path(args.runs_root).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"missing run dir: {run_dir}")

    sandbox_root = run_dir / "a1_sandbox"
    cold_core_arg = str(args.cold_core).strip()
    cold_core_path = Path(cold_core_arg).expanduser().resolve() if cold_core_arg else None
    if cold_core_path is None:
        cold_core_path = _default_cold_core_path(run_dir=run_dir, run_id=run_id)
    cold_core_source = _cold_core_source_label(
        cold_core_path=cold_core_path,
        run_dir=run_dir,
        run_id=run_id,
        explicit_override=bool(cold_core_arg),
    )
    cold_core_path_class = _cold_core_path_class(
        cold_core_path=cold_core_path,
        run_dir=run_dir,
        run_id=run_id,
    )
    cold_core_sha256 = _sha256_file(cold_core_path)

    proposals = _read_json(cold_core_path)
    if str(proposals.get("schema", "")).strip() != "A1_COLD_CORE_PROPOSALS_v1":
        raise SystemExit("cold-core schema mismatch")
    mining_support_terms = [
        str(x).strip()
        for x in (proposals.get("mining_support_terms", []) or [])
        if isinstance(x, str) and str(x).strip()
    ]
    mining_artifact_inputs = [
        str(x).strip()
        for x in (proposals.get("mining_artifact_inputs", []) or [])
        if isinstance(x, str) and str(x).strip()
    ]
    mining_negative_pressure_witnesses = [
        row
        for row in (proposals.get("mining_negative_pressure_witnesses", []) or [])
        if isinstance(row, dict)
    ]

    cold_core_sequence = int(proposals.get("sequence", 0) or 0)
    cold_core_basename_sequence = _cold_core_basename_sequence(cold_core_path)
    sequence = int(args.sequence) if int(args.sequence) > 0 else int(cold_core_sequence)
    if sequence <= 0:
        sequence = 1

    state = _load_state(run_dir)
    canon = _canonical_terms(state)
    allowed_terms = _parse_csv_terms_ordered(str(args.allowed_terms))
    allowed_term_set = set(allowed_terms)
    support_bootstrap_candidates = _support_bootstrap_terms(
        proposals,
        allowed_terms=allowed_terms,
        canon=canon,
    )
    support_bootstrap_set = set(support_bootstrap_candidates)

    raw_candidates = [t for t in proposals.get("admissible_term_candidates", []) if isinstance(t, str) and t.strip()]
    rescue_targets = [t for t in proposals.get("graveyard_rescue_targets", []) if isinstance(t, str) and t.strip()]
    rescue_terms = _rescue_terms_from_targets(state, rescue_targets)
    graveyard_library_terms = _parse_csv_terms(str(args.graveyard_library_terms))
    if graveyard_library_terms:
        rescue_terms = [t for t in rescue_terms if t not in graveyard_library_terms]
    graveyard_terms = _graveyard_terms(state)

    term_candidates = [t for t in raw_candidates if t not in canon]
    canonical_nonroot = sorted({t for t in canon if t not in {"f01_finitude", "n01_noncommutation"}})
    fuel_unseen_set: set[str] = set()
    if str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "anchor_replay":
        # Graveyard-fill should primarily exercise already-admitted anchors so the
        # run builds failure topology first, then recovers. Only bootstrap fresh
        # terms when there are not enough canonical anchors yet.
        anchor_candidates = rescue_terms if rescue_terms else canonical_nonroot
        if anchor_candidates and len(canonical_nonroot) >= 4:
            term_candidates = list(anchor_candidates)
    if str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "fuel_full_load":
        unseen_terms = [t for t in term_candidates if t not in graveyard_terms]
        seen_terms = [t for t in term_candidates if t in graveyard_terms]
        fuel_unseen_set = set(unseen_terms)
        if unseen_terms:
            term_candidates = unseen_terms + seen_terms
    if str(args.debate_mode) == "graveyard_recovery" and rescue_terms:
        rescue_terms = _filter_family_recovery_rescue_terms(
            raw_candidates=raw_candidates,
            rescue_terms=rescue_terms,
        )
        # Recovery mode intentionally allows canonical terms as anchors, because
        # rescue lanes are about re-working killed branches around those anchors.
        merged: list[str] = []
        for term in rescue_terms + raw_candidates:
            if term and term not in merged:
                merged.append(term)
        term_candidates = merged
    if str(args.debate_mode) == "graveyard_recovery":
        # Planner intentionally skips rescue expansion when the goal term is master conjunction.
        # In recovery phase we prioritize non-master rescue targets to force active graveyard work,
        # but allow periodic master-conjunction attempts so recovery can still close the top witness.
        allow_master = (
            "qit_master_conjunction" not in canon
            and len(canon) >= 20
            and (int(sequence) % 5 == 0)
        )
        non_master = [t for t in term_candidates if t != "qit_master_conjunction" or allow_master]
        if non_master:
            term_candidates = non_master
    if str(args.debate_mode) == "graveyard_recovery" and graveyard_library_terms:
        term_candidates = [t for t in term_candidates if t not in graveyard_library_terms]
    if not term_candidates:
        # Recovery mode needs to keep moving even when all proposed terms are already canonical.
        # In that case, we re-target a canonical term (preferably a “system segment” term)
        # to generate explicit rescue SIMs via the planner's graveyard_recovery wiring.
        if str(args.debate_mode) == "graveyard_recovery":
            fallback = sorted({t for t in canon if t and t not in {"f01_finitude", "n01_noncommutation"}})
            if graveyard_library_terms:
                fallback = [t for t in fallback if t not in graveyard_library_terms]
            if fallback:
                term_candidates = fallback
        if not term_candidates:
            raise SystemExit("no admissible term candidates (all canonical or filtered)")

    if allowed_term_set:
        rescue_targets, rescue_terms = _filter_rescue_targets_and_terms(
            state,
            rescue_targets,
            rescue_terms,
            allowed_terms=allowed_term_set,
        )
        filtered_candidates = [
            t for t in term_candidates
            if t in allowed_term_set or t in support_bootstrap_set
        ]
        if not filtered_candidates:
            raise SystemExit("no admissible term candidates after allowed-terms filter")
        ordered_candidates: list[str] = []
        seen_candidates: set[str] = set()
        for term in support_bootstrap_candidates + allowed_terms + filtered_candidates:
            if term in filtered_candidates and term not in seen_candidates:
                seen_candidates.add(term)
                ordered_candidates.append(term)
        term_candidates = ordered_candidates

    neg_classes = [c for c in proposals.get("proposed_negative_classes", []) if isinstance(c, str) and c.strip()]
    neg_classes = [c.strip().upper() for c in neg_classes]
    # Prefer commutation-smuggling as baseline, but in graveyard-first mode we
    # intentionally rotate across all available negative classes to build a wider
    # classical-failure graveyard surface.
    track_upper = str(args.track).upper()
    if str(args.debate_mode) == "graveyard_first" and neg_classes:
        sequence_idx = max(0, int(sequence) - 1)
        primary_neg = neg_classes[sequence_idx % len(neg_classes)]
    else:
        if "SZILARD" in track_upper or "CARNOT" in track_upper:
            if "CONTINUOUS_BATH" in neg_classes:
                primary_neg = "CONTINUOUS_BATH"
            elif "CLASSICAL_TIME" in neg_classes:
                primary_neg = "CLASSICAL_TIME"
            elif "COMMUTATIVE_ASSUMPTION" in neg_classes:
                primary_neg = "COMMUTATIVE_ASSUMPTION"
            else:
                primary_neg = neg_classes[0] if neg_classes else "COMMUTATIVE_ASSUMPTION"
        else:
            if "COMMUTATIVE_ASSUMPTION" in neg_classes:
                primary_neg = "COMMUTATIVE_ASSUMPTION"
            else:
                primary_neg = neg_classes[0] if neg_classes else "COMMUTATIVE_ASSUMPTION"
    if primary_neg not in {
        "COMMUTATIVE_ASSUMPTION",
        "CLASSICAL_TIME",
        "INFINITE_SET",
        "CONTINUOUS_BATH",
        "INFINITE_RESOLUTION",
        "PRIMITIVE_EQUALS",
        "EUCLIDEAN_METRIC",
        "CLASSICAL_TEMPERATURE",
    }:
        primary_neg = "COMMUTATIVE_ASSUMPTION"

    preferred = (
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "probe_operator",
        "cptp_channel",
        "unitary_operator",
        "partial_trace",
        "correlation_polarity",
        # “Glue” term needed for higher-tier probes/sims and the semantic gate.
        "qit_master_conjunction",
        "nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
        "information_work_extraction_bound",
        "erasure_channel_entropy_cost_lower_bound",
        # Szilard/Carnot bridge primitives (ratchet-safe: have real SIM probes).
        "measurement_operator",
        "observable_operator",
        "projector_operator",
        "pauli_operator",
        "bloch_sphere",
        "hopf_fibration",
        "hopf_torus",
        "berry_flux",
        "spinor_double_cover",
        "left_weyl_spinor",
        "right_weyl_spinor",
        "left_action_superoperator",
        "right_action_superoperator",
        "noncommutative_composition_order",
        "lindblad_generator",
        "liouvillian_superoperator",
        "channel_realization",
        "left_right_action_entropy_production_rate_orthogonality",
        "variance_order_trajectory_correlation_orthogonality",
        "channel_realization_correlation_polarity_orthogonality",
        "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
        "kraus_representation",
        "density_purity",
        "density_entropy",
        "von_neumann_entropy",
        "coherence_decoherence",
        "trajectory_correlation",
        "entropy_production_rate",
        "engine_cycle",
        "kraus_operator",
        "kraus_channel",
        "measurement_operator",
        "observable_operator",
        "commutator_operator",
        "von_neumann_entropy",
        "eigenvalue_spectrum",
        "positive_semidefinite",
        "trace_one",
        "lindblad_generator",
        "hamiltonian_operator",
        "noncommutative_composition_order",
    )
    if "CORRELATION_EXECUTABLE" in track_upper:
        correlation_first = (
            "correlation",
            "correlation_polarity",
            "density_entropy",
            "erasure_channel_entropy_cost_lower_bound",
            "information_work_extraction_bound",
        )
        preferred = correlation_first + tuple(t for t in preferred if t not in correlation_first)
    probe_capable_terms = set(preferred)
    rank = {t: i for i, t in enumerate(preferred)}
    rescue_rank = {t: i for i, t in enumerate(rescue_terms)}
    support_bootstrap_rank = {t: i for i, t in enumerate(support_bootstrap_candidates)}
    term_candidates = sorted(
        term_candidates,
        key=lambda t: (
            0 if t in support_bootstrap_rank else 1,
            support_bootstrap_rank.get(t, 10_000),
            (0 if (str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "fuel_full_load" and t in fuel_unseen_set) else 1),
            0 if t in rescue_rank else 1,
            rescue_rank.get(t, 10_000),
            rank.get(t, 10_000),
            t,
        ),
    )
    if str(args.debate_mode) == "graveyard_recovery":
        rescue_bucket = [t for t in term_candidates if t in rescue_rank]
        frontier_bucket = [
            t for t in term_candidates if t not in rescue_rank and t in raw_candidates and t not in canon
        ]
        other_bucket = [t for t in term_candidates if t not in rescue_bucket and t not in frontier_bucket]
        # Recovery must stay tied to graveyard, but still advance frontier terms.
        blended = rescue_bucket[:8] + frontier_bucket[:8]
        for t in rescue_bucket[8:] + frontier_bucket[8:] + other_bucket:
            if t not in blended:
                blended.append(t)
        term_candidates = blended
        # Recovery mode should primarily exercise terms with real probe implementations
        # so semantic pressure reflects math behavior rather than fallback probe noise.
        probe_first = [t for t in term_candidates if t in probe_capable_terms]
        non_probe_tail = [t for t in term_candidates if t not in probe_capable_terms]
        if probe_first:
            term_candidates = probe_first + non_probe_tail[:2]
        filtered_frontier_terms = _filter_fragment_focus_terms(
            [str(term).strip() for term in raw_candidates if _TERM_TOKEN_RE.fullmatch(str(term).strip())]
        )
        suppressed_frontier_terms = {
            str(term).strip()
            for term in raw_candidates
            if _TERM_TOKEN_RE.fullmatch(str(term).strip())
            and str(term).strip() not in filtered_frontier_terms
        }
        if suppressed_frontier_terms:
            term_candidates = [t for t in term_candidates if t not in suppressed_frontier_terms]

    max_terms = int(args.max_terms) if int(args.max_terms) > 0 else (24 if str(args.debate_mode) == "graveyard_first" else 16)
    if str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "fuel_full_load":
        anchor_candidates: list[str] = []
        source_pool = list(raw_candidates) + list(canonical_nonroot) + list(canon)
        for t in CORE_PROBE_ANCHORS:
            if t in source_pool:
                anchor_candidates.append(t)
        anchor_set = set(anchor_candidates)
        non_anchor = [t for t in term_candidates if t not in anchor_set]
        unseen_now = [t for t in non_anchor if t not in graveyard_terms]
        seen_now = [t for t in non_anchor if t in graveyard_terms]
        if unseen_now and len(unseen_now) > max_terms:
            # Deterministic rotation prevents starvation of long unseen-term frontiers.
            block = max(1, int(max_terms))
            offset = ((max(1, int(sequence)) - 1) * block) % len(unseen_now)
            unseen_now = unseen_now[offset:] + unseen_now[:offset]
        ordered = anchor_candidates + unseen_now + seen_now
        dedup: list[str] = []
        seen_terms: set[str] = set()
        for t in ordered:
            if t in seen_terms:
                continue
            seen_terms.add(t)
            dedup.append(t)
        term_candidates = dedup

    goals: list[Goal] = []
    for term in term_candidates[: max_terms]:
        goals.append(
            Goal(
                term=str(term),
                track=str(args.track),
                negative_class=str(primary_neg),
                negative_markers=_negative_markers_for_class(primary_neg),
            )
        )
    focus_goal_terms = [
        str(term).strip()
        for term in raw_candidates
        if _TERM_TOKEN_RE.fullmatch(str(term).strip())
        and (not allowed_term_set or term in allowed_term_set or term in support_bootstrap_set)
    ]
    focus_goal_terms = _filter_fragment_focus_terms(focus_goal_terms)
    if not focus_goal_terms:
        focus_goal_terms = [goal.term for goal in goals]

    # Import planner builder directly (keeps strategy schema identical to known-good emission).
    # Use sys.path import to avoid dataclass issues from ad-hoc module loading.
    tools_dir = (BOOTPACK / "tools").resolve()
    bootpack_base = BOOTPACK.resolve()
    for p in (str(tools_dir), str(bootpack_base)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import a1_adaptive_ratchet_planner as mod  # type: ignore
    except Exception as exc:
        raise SystemExit(f"failed to import planner: {exc}")

    strategy = mod.build_strategy_from_state(
        state=state,
        run_id=run_id,
        sequence=int(sequence),
        goals=tuple(goals),
        goal_selection=str(args.goal_selection),
        debate_mode=str(args.debate_mode),
    )

    if isinstance(strategy, dict):
        observed_terms = _strategy_observed_terms(strategy)
        family_hint_terms = (
            list(focus_goal_terms)
            if allowed_term_set
            else list(focus_goal_terms) + list(observed_terms)
        )
        family_hints = _load_family_admissibility_hints(selected_terms=family_hint_terms)
        strategy_terms = _resolve_target_terms(
            goal_terms=focus_goal_terms,
            observed_terms=observed_terms,
            family_hints=family_hints,
            target_scope_terms=(focus_goal_terms if allowed_term_set else []),
        )
        admissibility = _build_admissibility_block(
            strategy=strategy,
            state=state,
            selected_terms=strategy_terms,
            observed_terms=observed_terms,
            canon=canon,
            support_bootstrap_candidates=support_bootstrap_candidates,
            rescue_terms=rescue_terms,
            family_hints=family_hints,
            cold_core_source=cold_core_source,
            cold_core_path_class=cold_core_path_class,
            cold_core_sha256=cold_core_sha256,
            cold_core_sequence=cold_core_sequence,
            cold_core_basename_sequence=cold_core_basename_sequence,
            selector_sequence=sequence,
            target_scope_terms=(focus_goal_terms if allowed_term_set else []),
        )
        strategy_terms = _refine_handoff_target_terms(
            target_terms=strategy_terms,
            admissibility=admissibility,
            canon=canon,
        )
        if strategy_terms != list(strategy.get("target_terms", []) or []):
            admissibility = _build_admissibility_block(
                strategy=strategy,
                state=state,
                selected_terms=strategy_terms,
                observed_terms=observed_terms,
                canon=canon,
                support_bootstrap_candidates=support_bootstrap_candidates,
                rescue_terms=rescue_terms,
                family_hints=family_hints,
                cold_core_source=cold_core_source,
                cold_core_path_class=cold_core_path_class,
                cold_core_sha256=cold_core_sha256,
                cold_core_sequence=cold_core_sequence,
                cold_core_basename_sequence=cold_core_basename_sequence,
                selector_sequence=sequence,
                target_scope_terms=(focus_goal_terms if allowed_term_set else []),
            )
        strategy["target_terms"] = strategy_terms
        strategy["admissibility"] = admissibility
        strategy["family_terms"] = _strategy_family_terms(strategy_terms, admissibility)
        process_audit = strategy["admissibility"].get("process_audit", {}) if isinstance(strategy.get("admissibility", {}), dict) else {}
        if isinstance(process_audit, dict):
            process_audit["mining_support_terms"] = list(mining_support_terms)
            process_audit["mining_artifact_inputs"] = list(mining_artifact_inputs)
            process_audit["mining_negative_pressure_count"] = int(len(mining_negative_pressure_witnesses))
            process_warnings = process_audit.get("warnings", []) if isinstance(process_audit.get("warnings", []), list) else []
            if (mining_support_terms or mining_negative_pressure_witnesses) and "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority" not in process_warnings:
                process_warnings.append("noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority")
            process_audit["warnings"] = process_warnings
            process_audit.update(build_process_warning_snapshot(process_warnings))

    if str(args.debate_mode) == "graveyard_first" and bool(args.forbid_rescue_in_graveyard_first):
        for item in strategy.get("alternatives", []) if isinstance(strategy, dict) else []:
            if not isinstance(item, dict):
                continue
            defs = item.get("def_fields", [])
            if not isinstance(defs, list):
                continue
            item["def_fields"] = [
                row
                for row in defs
                if not (isinstance(row, dict) and str(row.get("name", "")).strip() == "RESCUE_FROM")
            ]

    out_dir = sandbox_root / "outgoing"
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in sorted(out_dir.glob("*_A1_STRATEGY_v1__PACK_SELECTOR.json")):
        stale.unlink(missing_ok=True)
    out_path = out_dir / f"{sequence:06d}_A1_STRATEGY_v1__PACK_SELECTOR.json"
    out_path.write_text(json.dumps(strategy, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    selector_process_warnings: list[str] = []
    selector_warning_codes: list[str] = []
    selector_warning_categories: list[str] = []
    selector_warning_details: list[dict] = []
    if isinstance(strategy, dict):
        admissibility = strategy.get("admissibility", {}) if isinstance(strategy.get("admissibility", {}), dict) else {}
        process_audit = admissibility.get("process_audit", {}) if isinstance(admissibility.get("process_audit", {}), dict) else {}
        raw_warnings = process_audit.get("warnings", []) if isinstance(process_audit.get("warnings", []), list) else []
        for raw in raw_warnings:
            msg = str(raw).strip()
            if msg and msg not in selector_process_warnings:
                selector_process_warnings.append(msg)
        raw_warning_codes = process_audit.get("warning_codes", []) if isinstance(process_audit.get("warning_codes", []), list) else []
        for raw in raw_warning_codes:
            code = str(raw).strip()
            if code and code not in selector_warning_codes:
                selector_warning_codes.append(code)
        raw_warning_categories = process_audit.get("warning_categories", []) if isinstance(process_audit.get("warning_categories", []), list) else []
        for raw in raw_warning_categories:
            category = str(raw).strip()
            if category and category not in selector_warning_categories:
                selector_warning_categories.append(category)
        raw_warning_details = process_audit.get("warning_details", []) if isinstance(process_audit.get("warning_details", []), list) else []
        for raw in raw_warning_details:
            if isinstance(raw, dict):
                selector_warning_details.append(dict(raw))
    result = {
        "schema": "A1_PACK_SELECTOR_RESULT_v1",
        "sequence": int(sequence),
        "out": str(out_path),
        "cold_core": str(cold_core_path),
        "cold_core_sequence": int(cold_core_sequence),
        "cold_core_source": str(cold_core_source),
        "cold_core_path_class": str(cold_core_path_class),
        "cold_core_sha256": str(cold_core_sha256),
        "selector_process_warnings": list(selector_process_warnings),
    }
    result.update(
        build_selector_warning_snapshot(
            selector_process_warnings,
            warning_codes=selector_warning_codes,
            warning_categories=selector_warning_categories,
            warning_details=selector_warning_details,
        )
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
