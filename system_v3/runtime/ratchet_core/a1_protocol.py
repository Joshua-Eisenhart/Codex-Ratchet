import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

"""A1 protocol: the interface between LLM reasoning and deterministic expansion.

A1 has two halves:
  NONDETERMINISTIC (LLM):
    - Reads: B state, A2 fuel queue, rosetta mappings
    - Outputs: a STRATEGY file (JSON) listing concepts to target and formulations

  DETERMINISTIC (Python):
    - Reads: the strategy file
    - Expands each entry into B-grammar proposals + competing alternatives
    - Each term gets: the right formulation, wrong alternatives (graveyard fuel),
      a positive SIM_SPEC, and a negative SIM_SPEC

STRATEGY FORMAT:
{
  "terms_to_admit": [
    {
      "term": "entropy",
      "why": "von Neumann entropy S(rho) = -Tr(rho log rho)",
      "alternatives": [
        {"suffix": "NO_TRACE", "objects": "density operator", "flaw": "missing trace"},
        {"suffix": "COMMUTATIVE", "objects": "density matrix commutator", "flaw": "entropy is not a commutator"}
      ]
    }
  ],
  "compounds_to_try": ["density_entropy", "trace_fidelity"],
  "math_defs": [
    {
      "id": "S_001", "objects": "trace density operator channel",
      "alternatives": [
        {"suffix": "BAD_DOMAIN", "objects": "trace density", "flaw": "missing operator/channel"}
      ]
    }
  ]
}

Each term's alternatives are deliberately wrong. They go to the graveyard.
The graveyard becomes: for every survivor, what it is NOT and why.
"""

import json
import re
from pathlib import Path

from containers import build_export_block
from validator import load_bootpack_rules


_BASE_DIR = Path(__file__).resolve().parent
_SIMS_DIR = _BASE_DIR / "sims"
_SIM_BINDING_PATH = _BASE_DIR / "constraint_sim_binding.json"
_WORD_RE = re.compile(r"[a-z_]+")

FORBIDDEN_OVERLAY_TERMS = {
    "axis", "axes", "engine", "engines", "spinor", "spinors", "weyl",
    "hopf", "tori", "bloch", "holodeck", "mbti", "igt", "persona",
    "personality",
}

HARD_RETRY_BLOCK_REASONS = {
    "DERIVED_ONLY_PRIMITIVE_USE",
    "DERIVED_ONLY_NOT_PERMITTED",
    "UNDEFINED_TERM_USE",
    "SCHEMA_FAIL",
}


def _token_set(lines):
    schema_words = {
        "spec_hyp", "spec_kind", "requires", "def_field", "assert",
        "corr", "exists", "probe_kind", "binds",
    }
    tokens = set()
    for line in lines:
        for tok in re.findall(r"[a-z][a-z0-9_]*", line):
            for seg in tok.split("_"):
                if seg and seg not in schema_words and len(seg) > 1:
                    tokens.add(seg)
    return tokens


def _near_redundant_candidate(lines, spec_kind, state, proposed_by_kind):
    new_tokens = _token_set(lines)
    if not new_tokens:
        return False

    for existing in state.specs.values():
        if existing.get("kind", "") != spec_kind:
            continue
        existing_tokens = _token_set(existing.get("raw_lines", []))
        if not existing_tokens:
            continue
        intersection = len(new_tokens & existing_tokens)
        union = len(new_tokens | existing_tokens)
        if union > 0 and (intersection / union) > 0.80:
            return True

    for existing_tokens in proposed_by_kind.get(spec_kind, []):
        intersection = len(new_tokens & existing_tokens)
        union = len(new_tokens | existing_tokens)
        if union > 0 and (intersection / union) > 0.80:
            return True

    proposed_by_kind.setdefault(spec_kind, []).append(new_tokens)
    return False


def _load_sim_binding() -> dict:
    try:
        return json.loads(_SIM_BINDING_PATH.read_text())
    except Exception:
        return {}


def _has_positive_sim(binding: dict, term: str) -> bool:
    sim_spec_id = f"SIM_TERM_{term.upper()}"
    if sim_spec_id in binding:
        return True
    try:
        if len(term) <= 120 and (_SIMS_DIR / f"sim_{term.lower()}.py").exists():
            return True
    except OSError:
        pass
    return (_SIMS_DIR / "sim_term_generic.py").exists()


def _has_negative_sim(binding: dict, term: str) -> bool:
    sim_spec_id = f"SIM_NEG_{term.upper()}"
    if sim_spec_id in binding:
        return True
    try:
        if len(term) <= 120 and (_SIMS_DIR / f"sim_{term.lower()}_negative.py").exists():
            return True
    except OSError:
        pass
    return (_SIMS_DIR / "sim_term_generic_negative.py").exists()


def _canonical_allowed_terms(state) -> set:
    allowed = set()
    for term, info in state.terms.items():
        if info.get("state") == "CANONICAL_ALLOWED":
            allowed.add(term)
    return allowed


def _collect_words(value: str) -> list[str]:
    words = []
    normalized = "_".join(_WORD_RE.findall(str(value).lower())).strip("_")
    if not normalized:
        return words
    for token in normalized.split("_"):
        if len(token) < 3:
            continue
        if token in FORBIDDEN_OVERLAY_TERMS:
            continue
        words.append(token)
    return words


def _word_safe_for_math(word: str, rules, admitted: set, canonical_allowed: set) -> bool:
    if word in rules.lexeme_set:
        return True
    if word in admitted:
        if word in rules.derived_only_terms:
            return word in canonical_allowed
        return True
    return False


def _graveyard_retry_block(state) -> set[str]:
    attempts = {}
    last_reason = {}
    for row in state.graveyard:
        gid = row.get("id", "")
        if not gid:
            continue
        attempts[gid] = attempts.get(gid, 0) + 1
        last_reason[gid] = row.get("reason", "")
    blocked = set()
    for gid, count in attempts.items():
        if count <= 1:
            continue
        if last_reason.get(gid, "") in HARD_RETRY_BLOCK_REASONS:
            blocked.add(gid)
    return blocked


def load_strategy(path: Path) -> dict:
    """Load a strategy file produced by the A1 LLM."""
    return json.loads(path.read_text("utf-8"))


def expand_strategy(strategy: dict, state, max_items=1000) -> list:
    """Expand a strategy into B-grammar items.

    Returns list of (spec_id, lines) tuples ready for A0 to compile.
    """
    rules = load_bootpack_rules()
    binding = _load_sim_binding()
    admitted = set(state.terms.keys()) if isinstance(state.terms, dict) else set()
    canonical_allowed = _canonical_allowed_terms(state)
    blocked_retry_ids = _graveyard_retry_block(state)
    queued_term_specs = set(state.specs.keys())
    items = []
    proposed_by_kind = {}

    def _append_candidate(spec_id, lines, spec_kind):
        if _near_redundant_candidate(lines, spec_kind, state, proposed_by_kind):
            return False
        items.append((spec_id, lines))
        return True

    if "S_L0_MATH" not in state.specs:
        items.append(("S_L0_MATH", [
            "SPEC_HYP S_L0_MATH",
            "SPEC_KIND S_L0_MATH CORR MATH_DEF",
            "REQUIRES S_L0_MATH CORR F01_FINITUDE",
            "REQUIRES S_L0_MATH CORR N01_NONCOMMUTATION",
            "DEF_FIELD S_L0_MATH CORR OBJECTS finite hilbert space",
            "DEF_FIELD S_L0_MATH CORR OPERATIONS operator commutator",
            "DEF_FIELD S_L0_MATH CORR INVARIANTS trace",
            "DEF_FIELD S_L0_MATH CORR DOMAIN hilbert space",
            "DEF_FIELD S_L0_MATH CORR CODOMAIN hilbert space",
            "DEF_FIELD S_L0_MATH CORR SIM_CODE_HASH_SHA256 " + "0" * 64,
            "ASSERT S_L0_MATH CORR EXISTS MATH_TOKEN MT_S_L0_MATH",
        ]))

    graveyard_ids = {g.get("id", "") for g in state.graveyard}

    # Expand term admissions (supports old string format and new dict format).
    # SIM_SPECs are emitted only for already-admitted dependencies to avoid
    # large forward-dependency park surfaces in the same batch.
    for entry in strategy.get("terms_to_admit", []):
        if isinstance(entry, str):
            term, alternatives = entry, []
            source_tag = "fuel_unknown"
        else:
            term, alternatives = entry["term"], entry.get("alternatives", [])
            source_id = str(entry.get("source_id", "fuel")).lower()
            source_id = re.sub(r"[^a-z0-9_]", "_", source_id)
            source_tag = f"source_{source_id}"

        term = str(term).strip().lower()
        if not term or not re.fullmatch(r"[a-z_]+", term):
            continue

        if term in admitted:
            continue
        spec_id = f"S_TERM_{term.upper()}"
        if spec_id in state.specs or spec_id in queued_term_specs:
            continue

        comp_deps = []
        if "_" in term:
            parts = term.split("_")
            if not all(p in admitted or p in rules.lexeme_set for p in parts):
                continue
            comp_deps = [f"S_TERM_{p.upper()}" for p in parts
                         if f"S_TERM_{p.upper()}" in state.specs]

        term_is_admitted = term in admitted or spec_id in state.specs
        if not term_is_admitted:
            lines = [
                f"SPEC_HYP {spec_id}",
                f"SPEC_KIND {spec_id} CORR TERM_DEF",
                f"REQUIRES {spec_id} CORR S_L0_MATH",
            ]
            for dep in comp_deps:
                lines.append(f"REQUIRES {spec_id} CORR {dep}")
            lines += [
                f'DEF_FIELD {spec_id} CORR TERM "{term}"',
                f"DEF_FIELD {spec_id} CORR BINDS S_L0_MATH",
                f'DEF_FIELD {spec_id} CORR LABEL "{source_tag}"',
                f"ASSERT {spec_id} CORR EXISTS TERM_TOKEN TT_{spec_id}",
            ]
            if _append_candidate(spec_id, lines, "TERM_DEF"):
                queued_term_specs.add(spec_id)

        # Positive SIM_SPEC (only for admitted term specs)
        sim_id = f"SIM_TERM_{term.upper()}"
        if term_is_admitted and sim_id not in state.specs and _has_positive_sim(binding, term):
            _append_candidate(sim_id, [
                f"SPEC_HYP {sim_id}",
                f"SPEC_KIND {sim_id} CORR SIM_SPEC",
                f"REQUIRES {sim_id} CORR {spec_id}",
                f'DEF_FIELD {sim_id} CORR REQUIRES_EVIDENCE "EV_{term.upper()}"',
                f"ASSERT {sim_id} CORR EXISTS EVIDENCE_TOKEN EV_{term.upper()}",
            ], "SIM_SPEC")

        # Negative SIM_SPEC (only for admitted term specs)
        neg_id = f"SIM_NEG_{term.upper()}"
        if term_is_admitted and neg_id not in state.specs and _has_negative_sim(binding, term):
            _append_candidate(neg_id, [
                f"SPEC_HYP {neg_id}",
                f"SPEC_KIND {neg_id} CORR SIM_SPEC",
                f"REQUIRES {neg_id} CORR {spec_id}",
                f'DEF_FIELD {neg_id} CORR REQUIRES_EVIDENCE "NEG_EV_{term.upper()}"',
                f"ASSERT {neg_id} CORR EXISTS EVIDENCE_TOKEN NEG_EV_{term.upper()}",
            ], "SIM_SPEC")

        # Competing alternatives (graveyard fuel — similar but wrong)
        for alt in alternatives:
            alt_id = f"S_TERM_{term.upper()}_{alt['suffix']}"
            if alt_id in state.specs or alt_id in graveyard_ids:
                continue
            _append_candidate(alt_id, [
                f"SPEC_HYP {alt_id}",
                f"SPEC_KIND {alt_id} CORR MATH_DEF",
                f"REQUIRES {alt_id} CORR S_L0_MATH",
                f"DEF_FIELD {alt_id} CORR OBJECTS {alt['objects']}",
                f"DEF_FIELD {alt_id} CORR OPERATIONS operator",
                f"DEF_FIELD {alt_id} CORR INVARIANTS trace",
                f"DEF_FIELD {alt_id} CORR DOMAIN hilbert space",
                f"DEF_FIELD {alt_id} CORR CODOMAIN hilbert space",
                f"DEF_FIELD {alt_id} CORR SIM_CODE_HASH_SHA256 " + "0" * 64,
                f"ASSERT {alt_id} CORR EXISTS MATH_TOKEN MT_{alt_id}",
            ], "MATH_DEF")

        if len(items) >= max_items:
            return items

    # Expand compounds
    for term in strategy.get("compounds_to_try", []):
        if term in admitted:
            continue
        spec_id = f"S_TERM_{term.upper()}"
        if spec_id in state.specs:
            continue
        parts = term.split("_")
        if not all(p in admitted or p in rules.lexeme_set for p in parts):
            continue
        comp_deps = [f"S_TERM_{p.upper()}" for p in parts
                     if f"S_TERM_{p.upper()}" in state.specs]
        lines = [
            f"SPEC_HYP {spec_id}",
            f"SPEC_KIND {spec_id} CORR TERM_DEF",
            f"REQUIRES {spec_id} CORR S_L0_MATH",
        ]
        for dep in comp_deps:
            lines.append(f"REQUIRES {spec_id} CORR {dep}")
        lines += [
            f'DEF_FIELD {spec_id} CORR TERM "{term}"',
            f"DEF_FIELD {spec_id} CORR BINDS S_L0_MATH",
            f'DEF_FIELD {spec_id} CORR LABEL "source_compound_generator"',
            f"ASSERT {spec_id} CORR EXISTS TERM_TOKEN TT_{spec_id}",
        ]
        _append_candidate(spec_id, lines, "TERM_DEF")
        if len(items) >= max_items:
            return items

    # Expand MATH_DEFs (with optional alternatives)
    for mdef in strategy.get("math_defs", []):
        spec_id = mdef["id"]
        if spec_id in state.specs or spec_id in blocked_retry_ids:
            continue
        raw_words = _collect_words(mdef.get("objects", ""))
        safe_words = [
            word for word in raw_words
            if _word_safe_for_math(word, rules, admitted, canonical_allowed)
        ]
        missing_words = [word for word in raw_words if word not in safe_words]

        for word in missing_words:
            if word in admitted:
                continue
            term_spec_id = f"S_TERM_{word.upper()}"
            if term_spec_id in queued_term_specs:
                continue
            _append_candidate(term_spec_id, [
                f"SPEC_HYP {term_spec_id}",
                f"SPEC_KIND {term_spec_id} CORR TERM_DEF",
                f"REQUIRES {term_spec_id} CORR S_L0_MATH",
                f'DEF_FIELD {term_spec_id} CORR TERM "{word}"',
                f"DEF_FIELD {term_spec_id} CORR BINDS S_L0_MATH",
                f"ASSERT {term_spec_id} CORR EXISTS TERM_TOKEN TT_{term_spec_id}",
            ], "TERM_DEF")
            queued_term_specs.add(term_spec_id)
            if len(items) >= max_items:
                return items

        if len(safe_words) < 2:
            continue

        objects_val = " ".join(safe_words[:6])
        lines = [
            f"SPEC_HYP {spec_id}",
            f"SPEC_KIND {spec_id} CORR MATH_DEF",
            f"REQUIRES {spec_id} CORR S_L0_MATH",
            f"DEF_FIELD {spec_id} CORR OBJECTS {objects_val}",
            f"DEF_FIELD {spec_id} CORR OPERATIONS operator",
            f"DEF_FIELD {spec_id} CORR INVARIANTS trace",
            f"DEF_FIELD {spec_id} CORR DOMAIN hilbert space",
            f"DEF_FIELD {spec_id} CORR CODOMAIN hilbert space",
            f"DEF_FIELD {spec_id} CORR SIM_CODE_HASH_SHA256 " + "0" * 64,
            f"ASSERT {spec_id} CORR EXISTS MATH_TOKEN MT_{spec_id}",
        ]
        _append_candidate(spec_id, lines, "MATH_DEF")

        for alt in mdef.get("alternatives", []):
            alt_id = f"{spec_id}_{alt['suffix']}"
            if alt_id in state.specs or alt_id in graveyard_ids:
                continue
            alt_words = _collect_words(alt.get("objects", ""))
            alt_safe_words = [
                word for word in alt_words
                if _word_safe_for_math(word, rules, admitted, canonical_allowed)
            ]
            if len(alt_safe_words) < 2:
                continue
            _append_candidate(alt_id, [
                f"SPEC_HYP {alt_id}",
                f"SPEC_KIND {alt_id} CORR MATH_DEF",
                f"REQUIRES {alt_id} CORR S_L0_MATH",
                f"DEF_FIELD {alt_id} CORR OBJECTS {' '.join(alt_safe_words[:6])}",
                f"DEF_FIELD {alt_id} CORR OPERATIONS operator",
                f"DEF_FIELD {alt_id} CORR INVARIANTS trace",
                f"DEF_FIELD {alt_id} CORR DOMAIN hilbert space",
                f"DEF_FIELD {alt_id} CORR CODOMAIN hilbert space",
                f"DEF_FIELD {alt_id} CORR SIM_CODE_HASH_SHA256 " + "0" * 64,
                f"ASSERT {alt_id} CORR EXISTS MATH_TOKEN MT_{alt_id}",
            ], "MATH_DEF")

        if len(items) >= max_items:
            return items

    # Backfill SIM specs for already-admitted terms that still lack them.
    for term in sorted(admitted):
        spec_id = f"S_TERM_{term.upper()}"
        if spec_id not in state.specs:
            continue
        sim_id = f"SIM_TERM_{term.upper()}"
        if sim_id not in state.specs and _has_positive_sim(binding, term):
            _append_candidate(sim_id, [
                f"SPEC_HYP {sim_id}",
                f"SPEC_KIND {sim_id} CORR SIM_SPEC",
                f"REQUIRES {sim_id} CORR {spec_id}",
                f'DEF_FIELD {sim_id} CORR REQUIRES_EVIDENCE "EV_{term.upper()}"',
                f"ASSERT {sim_id} CORR EXISTS EVIDENCE_TOKEN EV_{term.upper()}",
            ], "SIM_SPEC")
        neg_id = f"SIM_NEG_{term.upper()}"
        if neg_id not in state.specs and _has_negative_sim(binding, term):
            _append_candidate(neg_id, [
                f"SPEC_HYP {neg_id}",
                f"SPEC_KIND {neg_id} CORR SIM_SPEC",
                f"REQUIRES {neg_id} CORR {spec_id}",
                f'DEF_FIELD {neg_id} CORR REQUIRES_EVIDENCE "NEG_EV_{term.upper()}"',
                f"ASSERT {neg_id} CORR EXISTS EVIDENCE_TOKEN NEG_EV_{term.upper()}",
            ], "SIM_SPEC")
        if len(items) >= max_items:
            return items

    # Backfill SIM specs for already-admitted math defs that still lack them.
    for spec_id in sorted(state.specs.keys()):
        if state.specs[spec_id].get("kind") != "MATH_DEF":
            continue
        if spec_id == "S_L0_MATH":
            continue
        sim_math_id = f"SIM_MATH_{spec_id}"
        if sim_math_id not in state.specs:
            _append_candidate(sim_math_id, [
                f"SPEC_HYP {sim_math_id}",
                f"SPEC_KIND {sim_math_id} CORR SIM_SPEC",
                f"REQUIRES {sim_math_id} CORR {spec_id}",
                f'DEF_FIELD {sim_math_id} CORR REQUIRES_EVIDENCE "EV_MATH_{spec_id}"',
                f"ASSERT {sim_math_id} CORR EXISTS EVIDENCE_TOKEN EV_MATH_{spec_id}",
            ], "SIM_SPEC")
        sim_math_neg_id = f"SIM_NEG_MATH_{spec_id}"
        if sim_math_neg_id not in state.specs:
            _append_candidate(sim_math_neg_id, [
                f"SPEC_HYP {sim_math_neg_id}",
                f"SPEC_KIND {sim_math_neg_id} CORR SIM_SPEC",
                f"REQUIRES {sim_math_neg_id} CORR {spec_id}",
                f'DEF_FIELD {sim_math_neg_id} CORR REQUIRES_EVIDENCE "NEG_EV_MATH_{spec_id}"',
                f"ASSERT {sim_math_neg_id} CORR EXISTS EVIDENCE_TOKEN NEG_EV_MATH_{spec_id}",
            ], "SIM_SPEC")
        if len(items) >= max_items:
            return items

    return items


def compile_batch(items: list, state) -> str:
    """Take expanded items and compile into an EXPORT_BLOCK string."""
    content = []

    # Probes: 1 per 10 specs
    spec_count = len(items)
    probes_needed = max(1, (spec_count + 9) // 10)
    for i in range(probes_needed):
        pid = f"P{1000 + state.probe_count + 1 + i}"
        content += [
            f"PROBE_HYP {pid}",
            f"PROBE_KIND {pid} CORR PROBE_HYP",
            f"ASSERT {pid} CORR EXISTS PROBE_TOKEN PT_{pid}",
        ]

    for _, lines in items:
        content.extend(lines)

    return build_export_block(
        f"A1_BATCH_{state.hash()[:8]}", "A1_BATCH", content, version="v1"
    )
