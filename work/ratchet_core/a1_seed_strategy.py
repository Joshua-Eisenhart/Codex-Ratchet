import json
import re
from collections import Counter
from pathlib import Path

from validator import load_bootpack_rules


FORBIDDEN_OVERLAY_TERMS = {
    "axis", "axes", "engine", "engines", "spinor", "spinors", "weyl",
    "hopf", "tori", "bloch", "holodeck", "mbti", "igt", "persona",
    "personality",
}

HARD_REJECT_REASONS = {
    "DERIVED_ONLY_PRIMITIVE_USE",
    "DERIVED_ONLY_NOT_PERMITTED",
    "UNDEFINED_TERM_USE",
    "SCHEMA_FAIL",
    "SPEC_KIND_UNSUPPORTED",
}

RETRYABLE_REASONS = {
    "MISSING_DEPENDENCY",
    "PROBE_PRESSURE",
    "UNDEFINED_LEXEME",
    "NEAR_REDUNDANT",
}

_WORD_RE = re.compile(r"[a-z_]+")
_OBJECTS_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+OBJECTS\s+(.+)$")
_SPEC_KIND_MATH_DEF_RE = re.compile(r"^SPEC_KIND\s+\S+\s+CORR\s+MATH_DEF$")


def _tokenize_label(label):
    normalized = "_".join(_WORD_RE.findall(label.lower())).strip("_")
    if not normalized:
        return []
    words = []
    for token in normalized.split("_"):
        if len(token) < 3:
            continue
        if token in FORBIDDEN_OVERLAY_TERMS:
            continue
        words.append(token)
    return words


def _load_sim_seed_terms(repo_root):
    root = Path(repo_root)
    out = set()
    binding_path = root / "work" / "ratchet_core" / "constraint_sim_binding.json"
    if binding_path.exists():
        try:
            data = json.loads(binding_path.read_text(encoding="utf-8"))
            for key in data.keys():
                if key.startswith("SIM_TERM_"):
                    term = key[len("SIM_TERM_"):].lower()
                    if term and term not in FORBIDDEN_OVERLAY_TERMS:
                        out.add(term)
        except Exception:
            pass
    return out


def _extract_words(text):
    words = []
    for token in _WORD_RE.findall(text.lower()):
        for seg in token.split("_"):
            if len(seg) < 3:
                continue
            if seg in FORBIDDEN_OVERLAY_TERMS:
                continue
            words.append(seg)
    return words


def _ordered_unique(words):
    out = []
    seen = set()
    for w in words:
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


def _append_term(strategy, seen_terms, term, source_id="", source_doc=""):
    if term in seen_terms:
        return
    strategy["terms_to_admit"].append({
        "term": term,
        "alternatives": [],
        "source_id": source_id,
        "source_doc": source_doc,
    })
    seen_terms.add(term)


def _propose_compounds(entry_words, admitted, seen_terms, state, seen_compounds, max_compounds=6):
    compounds = []
    words = _ordered_unique(entry_words)
    if len(words) < 2:
        return compounds

    available = set(admitted).union(seen_terms)
    existing_specs = set(state.specs.keys())
    candidates = []
    for i in range(len(words) - 1):
        candidates.append([words[i], words[i + 1]])
    if len(words) >= 3:
        candidates.append(words[:3])

    for parts in candidates:
        if len(compounds) >= max_compounds:
            break
        if not all(p in available for p in parts):
            continue
        compound = "_".join(parts)
        if compound in admitted:
            continue
        if compound in seen_compounds:
            continue
        spec_id = f"S_TERM_{compound.upper()}"
        if spec_id in existing_specs:
            continue
        seen_compounds.add(compound)
        compounds.append(compound)
    return compounds


def _fallback_compounds_from_admitted(admitted_sorted, state, start, max_compounds):
    compounds = []
    if len(admitted_sorted) < 2:
        return compounds

    n = len(admitted_sorted)
    offset = (start + state.spec_count + state.sim_run_count) % n
    seen_local = set()

    for j in range(max_compounds * 16):
        if len(compounds) >= max_compounds:
            break
        i = (offset + 7 * j) % n
        k = (offset + 13 * j + 1) % n
        if i == k:
            continue
        compound = f"{admitted_sorted[i]}_{admitted_sorted[k]}"
        if compound in seen_local:
            continue
        spec_id = f"S_TERM_{compound.upper()}"
        if compound in state.terms or spec_id in state.specs:
            continue
        seen_local.add(compound)
        compounds.append(compound)

    for j in range(max_compounds * 16):
        if len(compounds) >= max_compounds:
            break
        i = (offset + 5 * j) % n
        k = (offset + 11 * j + 1) % n
        m = (offset + 17 * j + 2) % n
        if len({i, k, m}) != 3:
            continue
        compound = f"{admitted_sorted[i]}_{admitted_sorted[k]}_{admitted_sorted[m]}"
        if compound in seen_local:
            continue
        spec_id = f"S_TERM_{compound.upper()}"
        if compound in state.terms or spec_id in state.specs:
            continue
        seen_local.add(compound)
        compounds.append(compound)

    return compounds


def _word_admissible_for_math(word, admitted, lexeme_set, derived_only_terms, canonical_allowed):
    if word in lexeme_set:
        return True
    if word in admitted:
        if word in derived_only_terms:
            return word in canonical_allowed
        return True
    return False


def _reason_profile(state, window=400):
    recent_graveyard = state.graveyard[-window:]
    recent_parked = state.parked[-window:]
    reject_reasons = Counter(g.get("reason", "UNKNOWN") for g in recent_graveyard)
    park_reasons = Counter(p.get("reason", "UNKNOWN") for p in recent_parked)

    id_attempts = Counter(g.get("id", "") for g in state.graveyard if g.get("id"))
    id_last_reason = {}
    for g in state.graveyard:
        gid = g.get("id", "")
        if gid:
            id_last_reason[gid] = g.get("reason", "UNKNOWN")

    reject_total = sum(reject_reasons.values())
    hard_reject_total = sum(reject_reasons.get(r, 0) for r in HARD_REJECT_REASONS)
    hard_reject_ratio = (hard_reject_total / reject_total) if reject_total else 0.0

    return {
        "reject_reasons": reject_reasons,
        "park_reasons": park_reasons,
        "id_attempts": id_attempts,
        "id_last_reason": id_last_reason,
        "hard_reject_ratio": hard_reject_ratio,
    }


def _recovery_from_graveyard(
    state,
    admitted,
    seen,
    limit,
    reason_profile,
    lexeme_set,
    derived_only_terms,
    canonical_allowed,
):
    terms = []
    math_defs = []
    added_terms = 0
    added_math_defs = 0
    seen_math = set()
    id_attempts = reason_profile["id_attempts"]
    id_last_reason = reason_profile["id_last_reason"]

    for g in state.graveyard:
        raw_lines = g.get("raw_lines", [])
        has_math_def = any(_SPEC_KIND_MATH_DEF_RE.match(line.strip()) for line in raw_lines)
        objects_value = None
        for line in raw_lines:
            m = _OBJECTS_RE.match(line.strip())
            if m:
                objects_value = m.group(1).strip()
                break

        if objects_value:
            for word in _extract_words(objects_value):
                if word in admitted or word in seen:
                    continue
                terms.append(word)
                seen.add(word)
                added_terms += 1
                if added_terms >= limit:
                    break
        if added_terms >= limit:
            break

        gid = g.get("id", "")
        if has_math_def and gid.startswith("S_F") and objects_value:
            attempts = id_attempts.get(gid, 0)
            last_reason = id_last_reason.get(gid, "UNKNOWN")
            if attempts > 2:
                continue
            if last_reason in HARD_REJECT_REASONS and attempts > 1:
                continue
            if last_reason not in RETRYABLE_REASONS:
                words = _extract_words(objects_value)
                if not words:
                    continue
                if not all(
                    _word_admissible_for_math(
                        w, admitted, lexeme_set, derived_only_terms, canonical_allowed
                    )
                    for w in words
                ):
                    continue
            if gid not in seen_math and gid not in state.specs:
                math_defs.append({"id": gid, "objects": objects_value})
                seen_math.add(gid)
                added_math_defs += 1
                if added_math_defs >= limit:
                    break

    return terms, math_defs


def fuel_to_strategy(fuel_path, state, max_entries=20, start=0, repo_root=None):
    fuel = json.loads(Path(fuel_path).read_text(encoding="utf-8"))
    all_entries = fuel.get("entries", [])
    begin = max(0, start)
    end = min(len(all_entries), begin + max_entries)
    entries = all_entries[begin:end]

    strategy = {"terms_to_admit": [], "compounds_to_try": [], "math_defs": []}
    admitted = set(state.terms.keys()) if isinstance(state.terms, dict) else set()
    seen = set()
    seen_compounds = set()
    rules = load_bootpack_rules()
    lexeme_set = set(rules.lexeme_set)
    derived_only_terms = set(rules.derived_only_terms)
    canonical_allowed = {
        term for term, info in state.terms.items()
        if info.get("state") == "CANONICAL_ALLOWED"
    }
    reason_profile = _reason_profile(state)
    suppress_new_math_defs = reason_profile["hard_reject_ratio"] >= 0.60

    if repo_root:
        for term in sorted(_load_sim_seed_terms(repo_root)):
            if term in admitted or term in seen:
                continue
            _append_term(strategy, seen, term, source_id="SIM_SEED", source_doc="constraint_sim_binding")

    for entry in entries:
        source_id = str(entry.get("id", ""))
        source_doc = str(entry.get("source_doc", ""))
        label = entry.get("label", "")
        body = entry.get("body", "")
        words = _ordered_unique(_tokenize_label(label) + _extract_words(body))

        for word in words:
            if word in admitted or word in seen:
                continue
            _append_term(strategy, seen, word, source_id=source_id, source_doc=source_doc)

        for compound in _propose_compounds(
            words, admitted, seen, state, seen_compounds, max_compounds=4
        ):
            strategy["compounds_to_try"].append(compound)

        if entry.get("tag") in ("DERIVE", "CONSTRAINT"):
            spec_id = f"S_{entry.get('id', '')}"
            safe_words = [
                w for w in words
                if _word_admissible_for_math(
                    w, admitted, lexeme_set, derived_only_terms, canonical_allowed
                )
            ]
            if (
                not suppress_new_math_defs
                and spec_id
                and spec_id not in state.specs
                and len(safe_words) >= 2
            ):
                strategy["math_defs"].append({
                    "id": spec_id,
                    "objects": " ".join(safe_words[:6]),
                })

    # Adaptive recovery loop: mine rejected objects for missing term admissions and retries.
    recovery_terms, recovery_math_defs = _recovery_from_graveyard(
        state,
        admitted,
        seen,
        max_entries,
        reason_profile,
        lexeme_set,
        derived_only_terms,
        canonical_allowed,
    )
    for term in recovery_terms:
        _append_term(strategy, seen, term, source_id="GRAVEYARD_RECOVERY", source_doc="state.graveyard")
    for item in recovery_math_defs:
        strategy["math_defs"].append(item)

    if not strategy["compounds_to_try"]:
        admitted_sorted = sorted(
            t for t in admitted
            if len(t) >= 3 and t not in FORBIDDEN_OVERLAY_TERMS
        )
        strategy["compounds_to_try"].extend(
            _fallback_compounds_from_admitted(
                admitted_sorted=admitted_sorted,
                state=state,
                start=start,
                max_compounds=max_entries,
            )
        )

    strategy["_meta"] = {
        "hard_reject_ratio": round(reason_profile["hard_reject_ratio"], 3),
        "suppress_new_math_defs": suppress_new_math_defs,
        "recent_reject_reasons": dict(reason_profile["reject_reasons"]),
        "recent_park_reasons": dict(reason_profile["park_reasons"]),
    }

    return strategy, end, len(all_entries)
