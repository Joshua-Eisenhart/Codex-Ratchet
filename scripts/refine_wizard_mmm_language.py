#!/usr/bin/env python3
"""Refine generated Wizard MMM language bodies.

This is a local artifact repair script for the v2.7 candidate packet. It keeps
machine fields in JSON while making Markdown files useful as boot-visible
language bodies instead of metadata dumps.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "work"
    / "mmm_wizard_repair"
    / "mmm_wizard_complete_system_packet_v2_7_candidate"
)

SECTION_ORDER = ("words", "couplings", "triplets")
THINKERS = ("Hume", "Zhuangzi", "Popper", "Feynman", "Orwell")
PROVENANCE = "v2.7"

STOPWORDS = {
    "a",
    "about",
    "above",
    "across",
    "after",
    "again",
    "against",
    "all",
    "along",
    "also",
    "an",
    "and",
    "any",
    "apart",
    "around",
    "as",
    "at",
    "back",
    "before",
    "beside",
    "between",
    "both",
    "but",
    "by",
    "down",
    "each",
    "else",
    "for",
    "from",
    "if",
    "in",
    "inside",
    "into",
    "later",
    "near",
    "next",
    "no",
    "not",
    "of",
    "off",
    "on",
    "or",
    "out",
    "over",
    "through",
    "to",
    "under",
    "until",
    "up",
    "where",
    "while",
    "with",
    "within",
    "without",
    "yet",
}

WEAK_SINGLE_TERMS = {
    "abstract",
    "accepted",
    "actual",
    "active",
    "also",
    "appears",
    "basic",
    "become",
    "both",
    "carried",
    "central",
    "changed",
    "checked",
    "careful",
    "category",
    "current",
    "even",
    "exists",
    "found",
    "held",
    "inferred",
    "known",
    "later",
    "live",
    "local",
    "named",
    "narrow",
    "next",
    "object",
    "option",
    "plain",
    "provide",
    "reading",
    "returned",
    "set",
    "stale",
    "surface",
    "term",
    "test",
    "them",
    "they",
    "thing",
    "unknown",
    "using",
    "way",
    "warm",
}

TERM_REPLACEMENTS = {
    "andon": "alert",
    "andon visible problem": "visible alert",
    "drum buffer rope": "bottleneck control",
    "culminating point": "decisive point",
    "line of operation": "work path",
    "fog of war": "uncertainty",
    "careful friend": "evidence-scoped judgment",
    "gentle push": "scope correction",
    "kind correction": "scope correction",
    "kind correction with scope note": "scope correction with scope note",
    "low drama": "calm judgment",
    "trust but check": "bounded confidence",
    "warm refusal": "scope refusal",
    "notthat": "unruled option",
    "heart mind": "separate readings",
    "heart mind response": "separate readings response",
    "self so": "unruled option",
    "thing transformation": "changed reading",
    "walking in pairs": "separate readings",
    "walking two paths": "two readings kept distinct",
}

DROP_EXACT_TERMS = {
    "among",
    "careful",
    "even",
    "exists",
    "found",
    "held",
    "inferred",
    "provide",
    "returned",
    "them",
    "they",
    "unknown",
    "using",
    "warm",
}

KEEP_SINGLE_TERMS = {
    "admission",
    "audit",
    "boundary",
    "branch",
    "cvc5",
    "claim",
    "confidence",
    "constraint",
    "controller",
    "council",
    "evidence",
    "falsifier",
    "gate",
    "graph",
    "harness",
    "hypothesis",
    "ledger",
    "measurement",
    "observable",
    "packet",
    "proof",
    "probe",
    "qit",
    "receipt",
    "route",
    "runner",
    "schema",
    "scope",
    "security",
    "sim",
    "source",
    "status",
    "test",
    "tool",
    "truth",
    "validator",
    "wave",
    "wiki",
    "z3",
}

WEAK_STARTS = STOPWORDS | {
    "check",
    "observe",
    "test",
    "verify",
}

WEAK_ENDS = {
    "candidate",
    "path",
    "status",
    "surface",
}

ACTION_SUFFIXES = ("ing", "ed", "ize", "ise")

CURATED_SEEDS: dict[str, dict[str, list[str]]] = {
    "MMM_MAIN_": {
        "words": [
            "constraint-admissibility",
            "probe family",
            "status ladder",
            "receipt truth",
            "bounded work",
            "admission gate",
            "local rerun",
            "canonical label",
            "tool integration",
            "load-bearing tool",
            "proof witness",
            "z3 unsat",
            "graph evidence",
            "qit engine",
            "sim frontier",
            "skip-ahead guard",
            "negative battery",
            "behavior comparison",
        ],
        "couplings": [
            "wiki source of truth",
            "packet derived from wiki",
            "proof gate before promotion",
            "graph evidence before bridge claim",
            "tool integration before nonclassical sim",
            "local winner before pairwise coupling",
        ],
        "triplets": [
            "wiki packet adapter",
            "probe receipt status",
            "sim proof graph",
            "local pairwise bridge",
            "tool lego engine",
        ],
    },
    "MMM_VOICE_HUME_": {
        "words": [
            "evidence-scoped judgment",
            "claim ceiling",
            "support level",
            "receipt grounded",
            "credible but open",
            "bounded confidence",
        ],
        "couplings": [
            "observed support before confidence",
            "claim ceiling named early",
            "support gap kept open",
        ],
        "triplets": [
            "claim support limit",
            "receipt scope judgment",
            "checked evidence confidence",
        ],
    },
    "MMM_VOICE_ZHUANGZI_": {
        "words": [
            "live reading",
            "surviving alternative",
            "held apart",
            "separate readings",
            "not-yet-excluded",
            "unforced choice",
            "open branch",
            "anti-collapse",
            "coexisting candidates",
            "premature closure",
            "reading under probe",
            "unruled option",
        ],
        "couplings": [
            "two readings kept distinct",
            "alternative held until excluded",
            "unforced branch before synthesis",
            "anti-collapse under receipt",
        ],
        "triplets": [
            "live alternatives preserved",
            "reading probe exclusion",
            "branch before synthesis",
            "not-yet-excluded option",
        ],
    },
}

CURATED_TERMS = {
    term.lower()
    for sections in CURATED_SEEDS.values()
    for terms in sections.values()
    for term in terms
}


def _words(term: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", term.lower())


def _variant_limit(path: Path, section: str) -> int | None:
    text = str(path).lower()
    if "main_mmm" in text:
        return {"words": 260, "couplings": 180, "triplets": 90}.get(section)
    if "/full/" in text:
        return {"words": 240, "couplings": 160, "triplets": 80}.get(section)
    if "/ultra/" in text:
        return {"words": 220, "couplings": 140, "triplets": 70}.get(section)
    if "/standard/" in text:
        return {"words": 160, "couplings": 100, "triplets": 50}.get(section)
    if "/compact/" in text:
        return {"words": 90, "couplings": 60, "triplets": 30}.get(section)
    return None


def _contains_thinker(term: str) -> bool:
    return any(
        re.search(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", term, re.IGNORECASE)
        for name in THINKERS
    )


def _row_kind(term: str, section: str) -> str:
    parts = _words(term)
    if _contains_thinker(term):
        return "thinker"
    if section == "couplings":
        return "coupling"
    if section == "triplets":
        return "triplet"
    if len(parts) > 1:
        return "phrase"
    if parts and (parts[0].endswith(ACTION_SUFFIXES) or parts[0] in {"act", "check", "compare", "compose", "move"}):
        return "action"
    return "noun"


def _row_type(term: str, section: str) -> str:
    if section in {"couplings", "triplets"} or _contains_thinker(term):
        return "correlated"
    return "aligned"


def _canonical_term(term: str) -> str:
    result = term.strip()
    replacement = TERM_REPLACEMENTS.get(result.lower())
    if replacement is not None:
        result = replacement
    for name in THINKERS:
        result = re.sub(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", name, result, flags=re.IGNORECASE)
    return result


def _weak_term(term: str, section: str) -> bool:
    parts = _words(term)
    if not parts:
        return True
    if term.lower().strip() in DROP_EXACT_TERMS:
        return True
    if len(parts) == 1:
        word = parts[0]
        if word in KEEP_SINGLE_TERMS:
            return False
        return word in STOPWORDS or word in WEAK_SINGLE_TERMS or len(word) <= 2
    if len(set(parts)) < len(parts):
        return True
    if parts[0] in WEAK_STARTS:
        return True
    if parts[-1] in WEAK_ENDS and section != "words":
        return True
    content = [part for part in parts if part not in STOPWORDS]
    if len(content) < max(1, len(parts) - 2):
        return True
    return False


def _score(term: str, section: str) -> int:
    parts = _words(term)
    score = 0
    if term.lower().strip() in CURATED_TERMS:
        score += 24
    if _contains_thinker(term):
        score += 30
    if section == "words":
        score += 8 if len(parts) > 1 else 3
    elif section == "couplings":
        score += 10
    else:
        score += 7
    score += min(len([part for part in parts if part not in STOPWORDS]), 4)
    if len(parts) > 5:
        score -= len(parts) - 5
    return score


def _fit_label(path: Path) -> str:
    parts = path.parts
    if "main_mmm" in parts:
        return "main MMM"
    if "mini_mmms" not in parts:
        return path.stem
    try:
        category = parts[parts.index("mini_mmms") + 2]
    except (ValueError, IndexError):
        category = "mini"
    name = path.stem
    name = re.sub(r"^MMM_(VOICE|LANE)_", "", name)
    name = re.sub(r"_(COMPACT|STANDARD|FULL|ULTRA)_v2_7$", "", name)
    return f"{category}:{name.lower()}"


def _weight_for(term: str, section: str) -> int:
    score = _score(term, section)
    base = 48 if section == "words" else 56
    if _contains_thinker(term):
        base = 70
    return max(35, min(95, base + score * 3))


def _gloss(term: str, section: str, path: Path) -> str:
    fit = _fit_label(path)
    if section == "words":
        return f"{fit} cue used inside receipt/probe/status grammar: {term}"
    if section == "couplings":
        return f"{fit} relation phrase that should pull a sentence toward bounded work: {term}"
    return f"{fit} cadence for keeping three-part reasoning aligned: {term}"


def _aligned_use(term: str, path: Path) -> str:
    fit = _fit_label(path)
    return f"In {fit}, use '{term}' only with an explicit probe, receipt, status, or bounded next move."


def _unsafe_use(term: str) -> str:
    return f"Bare '{term}' as vibe, conclusion, or authority without a probe/receipt/status."


def _source_class(path: Path) -> str:
    if "main_mmm" in path.parts:
        return "authority"
    if "voices" in path.parts or "lanes" in path.parts:
        return "technique"
    if "checks_guards" in path.parts:
        return "caution"
    return "support"


def _add_curated_seeds(path: Path, data: dict[str, Any]) -> None:
    name = path.stem
    for marker, sections in CURATED_SEEDS.items():
        if marker not in name:
            continue
        for section, terms in sections.items():
            rows = data.setdefault(section, [])
            if not isinstance(rows, list):
                continue
            existing = {str(row.get("term", "")).strip().lower() for row in rows if isinstance(row, dict)}
            for term in terms:
                if term.lower() in existing:
                    continue
                rows.append({"term": term, "weight": 100})
                existing.add(term.lower())


def _compact_rows(path: Path, section: str, rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []

    seen: set[str] = set()
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            continue
        term = str(raw.get("term", "")).strip()
        term = _canonical_term(term)
        key = term.lower()
        if not term or key in seen or _weak_term(term, section):
            continue
        seen.add(key)
        row = dict(raw)
        row["term"] = term
        row["weight"] = _weight_for(term, section)
        row["row_type"] = _row_type(term, section)
        row["row_kind"] = _row_kind(term, section)
        row["gloss"] = _gloss(term, section, path)
        row["provenance"] = PROVENANCE
        row["status"] = "candidate"
        row["source_class"] = _source_class(path)
        row["voice_lane_fit"] = _fit_label(path)
        row["aligned_use"] = _aligned_use(term, path)
        row["unsafe_use"] = _unsafe_use(term)
        row["admission_test"] = "lexical_compaction_v2_7"
        row["provenance_run"] = "codex_refine_wizard_mmm_language_2026-04-28"
        candidates.append((_score(term, section), index, row))

    limit = _variant_limit(path, section)
    if limit is not None and len(candidates) > limit:
        keep_indexes = {
            index
            for _, index, _ in sorted(candidates, key=lambda item: (-item[0], item[1]))[:limit]
        }
        candidates = [item for item in candidates if item[1] in keep_indexes]

    refined: list[dict[str, Any]] = []
    for new_id, (_, _, row) in enumerate(sorted(candidates, key=lambda item: (-item[0], item[1])), start=1):
        row["id"] = new_id
        refined.append(row)
    return refined


def _ensure_main_thinkers(path: Path, data: dict[str, Any]) -> None:
    if "main_mmm" not in str(path).lower():
        return
    rows = data.setdefault("words", [])
    if not isinstance(rows, list):
        return
    existing = {str(row.get("term", "")).lower() for row in rows if isinstance(row, dict)}
    for name in THINKERS:
        if name.lower() in existing:
            continue
        rows.append(
            {
                "id": len(rows) + 1,
                "term": name,
                "weight": 100,
                "row_type": "correlated",
                "row_kind": "thinker",
                "gloss": f"main MMM correlated thinker cue: {name}",
                "provenance": PROVENANCE,
                "status": "candidate",
                "source_class": "support",
                "voice_lane_fit": "main MMM",
                "aligned_use": f"Use {name} as a correlated thinking style, not as an authority label.",
                "unsafe_use": f"Bare {name} name-dropping without a receipt.",
                "admission_test": "lexical_compaction_v2_7",
                "provenance_run": "codex_refine_wizard_mmm_language_2026-04-28",
            }
        )
        existing.add(name.lower())


def _ensure_main_thinkers_after_compaction(path: Path, data: dict[str, Any]) -> None:
    if "main_mmm" not in str(path).lower():
        return
    rows = data.setdefault("words", [])
    if not isinstance(rows, list):
        return
    existing = {str(row.get("term", "")).lower() for row in rows if isinstance(row, dict)}
    for name in THINKERS:
        if name.lower() in existing:
            continue
        rows.append(
            {
                "id": len(rows) + 1,
                "term": name,
                "weight": 100,
                "row_type": "correlated",
                "row_kind": "thinker",
                "gloss": f"main MMM correlated thinker cue: {name}",
                "provenance": PROVENANCE,
                "status": "candidate",
                "source_class": "support",
                "voice_lane_fit": "main MMM",
                "aligned_use": f"Use {name} as a correlated thinking style, not as an authority label.",
                "unsafe_use": f"Bare {name} name-dropping without a receipt.",
                "admission_test": "lexical_compaction_v2_7",
                "provenance_run": "codex_refine_wizard_mmm_language_2026-04-28",
            }
        )
        existing.add(name.lower())
    for new_id, row in enumerate(rows, start=1):
        if isinstance(row, dict):
            row["id"] = new_id


def _schema() -> dict[str, Any]:
    return {
        "fields": ["id", "term", "weight", "row_type", "row_kind", "gloss", "provenance"],
        "extended_fields": [
            "status",
            "source_class",
            "voice_lane_fit",
            "aligned_use",
            "unsafe_use",
            "admission_test",
            "provenance_run",
        ],
        "variant_semantics": "independent variants; sizes are not assumed to be nested supersets",
        "row_type_values": ["aligned", "correlated"],
        "row_kind_values": ["noun", "phrase", "action", "thinker", "coupling", "triplet"],
        "display_contract": "Markdown renders terms only; JSON carries metadata.",
    }


def _render_markdown(title: str, data: dict[str, Any]) -> str:
    groups: list[tuple[str, list[dict[str, Any]]]] = []
    for section in SECTION_ORDER:
        rows = data.get(section)
        if not isinstance(rows, list) or not rows:
            continue
        if section == "words":
            thinker_rows = [row for row in rows if row.get("row_kind") == "thinker"]
            aligned_rows = [row for row in rows if row.get("row_kind") != "thinker"]
            if aligned_rows:
                groups.append(("aligned nouns and phrases", aligned_rows))
            if thinker_rows:
                groups.append(("correlated thinkers", thinker_rows))
        elif section == "couplings":
            groups.append(("correlated couplings", rows))
        elif section == "triplets":
            groups.append(("three-part cues", rows))

    lines = [f"# {title}", ""]
    for heading, rows in groups:
        lines.extend([f"## {heading}", ""])
        for row in rows:
            term = str(row.get("term", "")).strip()
            if term:
                lines.append(f"- {term}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _json_to_md_path(path: Path) -> Path:
    parts = list(path.parts)
    try:
        index = parts.index("json")
    except ValueError:
        raise ValueError(f"cannot derive markdown path for {path}") from None
    parts[index] = "md"
    return Path(*parts).with_suffix(".md")


def refine_packet(root: Path) -> dict[str, Any]:
    json_files = [
        path
        for path in sorted(root.rglob("*.json"))
        if any(part in {"main_mmm", "mini_mmms"} for part in path.parts)
    ]
    touched_json = 0
    touched_md = 0
    rows_before = 0
    rows_after = 0

    for path in json_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or not any(section in data for section in SECTION_ORDER):
            continue

        _add_curated_seeds(path, data)
        _ensure_main_thinkers(path, data)
        rows_before += sum(len(data.get(section, [])) for section in SECTION_ORDER if isinstance(data.get(section), list))
        data["schema"] = _schema()
        for section in SECTION_ORDER:
            if section in data:
                data[section] = _compact_rows(path, section, data.get(section))
        _ensure_main_thinkers_after_compaction(path, data)
        rows_after += sum(len(data.get(section, [])) for section in SECTION_ORDER if isinstance(data.get(section), list))
        path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        touched_json += 1

        md_path = _json_to_md_path(path)
        if md_path.exists():
            title = md_path.stem
            md_path.write_text(_render_markdown(title, data), encoding="utf-8")
            touched_md += 1

    return {
        "candidate_root": str(root),
        "json_files_refined": touched_json,
        "markdown_files_refined": touched_md,
        "rows_before": rows_before,
        "rows_after": rows_after,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_root", nargs="?", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    result = refine_packet(args.candidate_root.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
