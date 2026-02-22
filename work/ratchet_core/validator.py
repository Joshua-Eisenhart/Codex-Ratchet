import re
from dataclasses import dataclass
from pathlib import Path

from containers import parse_export_block, split_items


_REPO_ROOT = Path(__file__).resolve().parents[2]
_BOOTPACK_PATH = _REPO_ROOT / "core_docs" / "BOOTPACK_THREAD_B_v3.9.13.md"


_QUOTED_RE = re.compile(r'"([^"]+)"')
_BEGIN_RE = re.compile(r"^BEGIN EXPORT_BLOCK (v\d+)")
_END_RE = re.compile(r"^END EXPORT_BLOCK (v\d+)")
_HEADER_RE = re.compile(r"^(AXIOM_HYP|PROBE_HYP|SPEC_HYP)\s+(\S+)$")
_SPEC_KIND_RE = re.compile(r"^SPEC_KIND\s+(\S+)\s+CORR\s+(\S+)$")
_PROBE_KIND_RE = re.compile(r"^PROBE_KIND\s+(\S+)\s+CORR\s+(\S+)$")
_ASSERT_RE = re.compile(r"^ASSERT\s+(\S+)\s+CORR\s+EXISTS\s+(\S+)\s+(\S+)$")
_REQUIRES_RE = re.compile(r"^REQUIRES\s+(\S+)\s+CORR\s+(\S+)$")
_DEF_FIELD_RE = re.compile(r"^DEF_FIELD\s+(\S+)\s+CORR\s+(\S+)\s+(.+)$")
_TERM_DEF_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+TERM\s+"([^"]+)"')
_LABEL_DEF_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+LABEL\s+"([^"]+)"')
_FORMULA_DEF_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+FORMULA\s+"([^"]*)"')
_SIM_HASH_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+SIM_CODE_HASH_SHA256\s+([0-9a-fA-F]{64})$")
_EXEMPT_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+(TERM|LABEL|FORMULA)\s+\"")

_LOWER_TOKEN_RE = re.compile(r"[a-z][a-z0-9_]*")
_SCHEMA_LITERALS = {
    "probe_kind",
    "requires_evidence",
    "evidence_token",
    "probe_token",
    "sim_spec",
}


@dataclass(frozen=True)
class BootpackRules:
    lexeme_set: set
    derived_only_terms: set
    allowed_spec_kinds: set


def _collect_quoted_literals(lines, marker, stop_tokens=None):
    stop_tokens = stop_tokens or ["RULE", "STATE", "====", "CONTAINER", "4."]
    tokens = []
    in_block = False
    for line in lines:
        if not in_block:
            if line.strip().startswith(marker):
                in_block = True
            continue
        if any(line.strip().startswith(t) for t in stop_tokens):
            break
        tokens.extend(_QUOTED_RE.findall(line))
    return tokens


def load_bootpack_rules(path=_BOOTPACK_PATH):
    lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    lexeme = set(t.lower() for t in _collect_quoted_literals(lines, "INIT L0_LEXEME_SET"))
    derived = set(t.lower() for t in _collect_quoted_literals(lines, "INIT DERIVED_ONLY_TERMS"))
    allowed = {"MATH_DEF", "TERM_DEF", "LABEL_DEF", "CANON_PERMIT", "SIM_SPEC"}
    return BootpackRules(lexeme_set=lexeme, derived_only_terms=derived, allowed_spec_kinds=allowed)


def _term_state_ok(state, term, allowed_states):
    info = state.terms.get(term)
    if not info:
        return False
    state_val = info.get("state") or "CANONICAL_ALLOWED"
    return state_val in allowed_states


def _line_is_exempt(line):
    if _EXEMPT_RE.match(line.strip()):
        return True
    if _SIM_HASH_RE.match(line.strip()):
        return True
    return False


def _has_mixedcase_token(line):
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_]*", line):
        if any(c.islower() for c in token) and any(c.isupper() for c in token):
            return True
    return False


def _scan_derived_only(line, rules, state):
    if _line_is_exempt(line):
        return None
    for tok in _LOWER_TOKEN_RE.findall(line):
        if tok in _SCHEMA_LITERALS:
            continue
        for seg in tok.split("_"):
            if not seg:
                continue
            if seg in rules.derived_only_terms and not _term_state_ok(state, seg, {"CANONICAL_ALLOWED"}):
                return "DERIVED_ONLY_PRIMITIVE_USE"
    return None


def _scan_undefined_terms(line, rules, state):
    if _line_is_exempt(line):
        return None
    if not all(ord(c) < 128 for c in line):
        return "SCHEMA_FAIL"
    if _has_mixedcase_token(line):
        return "SCHEMA_FAIL"
    for tok in _LOWER_TOKEN_RE.findall(line):
        if tok in _SCHEMA_LITERALS:
            continue
        for seg in tok.split("_"):
            if not seg:
                continue
            if seg.isdigit():
                continue
            if re.search(r"[a-z]", seg) and re.search(r"[0-9]", seg):
                if not _term_state_ok(state, "digit_sign", {"CANONICAL_ALLOWED"}):
                    return "DERIVED_ONLY_NOT_PERMITTED"
                continue
            if seg in rules.lexeme_set:
                continue
            if _term_state_ok(state, seg, {"TERM_PERMITTED", "LABEL_PERMITTED", "CANONICAL_ALLOWED"}):
                continue
            return "UNDEFINED_TERM_USE"
    return None


def _validate_item_schema(item, rules, state):
    header = item["header"]
    item_id = item["id"]
    lines = [l.strip() for l in item["lines"] if l.strip()]
    issues = []
    parks = []

    if header == "AXIOM_HYP":
        return issues, parks

    if header == "PROBE_HYP":
        has_kind = any(_PROBE_KIND_RE.match(l) for l in lines)
        has_token = any(_ASSERT_RE.match(l) and "PROBE_TOKEN" in l for l in lines)
        if not has_kind or not has_token:
            issues.append((item_id, "SCHEMA_FAIL"))
        return issues, parks

    if header != "SPEC_HYP":
        issues.append((item_id, "UNKNOWN_HEADER"))
        return issues, parks

    kind = None
    for l in lines:
        m = _SPEC_KIND_RE.match(l)
        if m:
            kind = m.group(2)
            break
    if kind is None or kind not in rules.allowed_spec_kinds:
        issues.append((item_id, "SPEC_KIND_UNSUPPORTED"))
        return issues, parks

    reqs = [m.group(2) for m in (_REQUIRES_RE.match(l) for l in lines) if m]
    defs = [(_DEF_FIELD_RE.match(l).group(2), _DEF_FIELD_RE.match(l).group(3)) for l in lines if _DEF_FIELD_RE.match(l)]
    asserts = [(_ASSERT_RE.match(l).group(2), _ASSERT_RE.match(l).group(3)) for l in lines if _ASSERT_RE.match(l)]

    if kind == "MATH_DEF":
        needed_fields = {"OBJECTS", "OPERATIONS", "INVARIANTS", "DOMAIN", "CODOMAIN", "SIM_CODE_HASH_SHA256"}
        present = {k for k, _ in defs}
        if not needed_fields.issubset(present):
            issues.append((item_id, "SCHEMA_FAIL"))
        if not any(tok == "MATH_TOKEN" for tok, _ in asserts):
            issues.append((item_id, "SCHEMA_FAIL"))
        return issues, parks

    if kind == "TERM_DEF":
        if not reqs:
            issues.append((item_id, "SCHEMA_FAIL"))
        term_literal = None
        binds = None
        for k, v in defs:
            if k == "TERM":
                m = _TERM_DEF_RE.match(f"DEF_FIELD X CORR TERM {v}")
                if m:
                    term_literal = m.group(1)
            if k == "BINDS":
                binds = v.strip()
        if not term_literal or not binds:
            issues.append((item_id, "SCHEMA_FAIL"))
        if not any(tok == "TERM_TOKEN" for tok, _ in asserts):
            issues.append((item_id, "SCHEMA_FAIL"))
        if term_literal and "_" in term_literal:
            components = [c for c in term_literal.split("_") if c]
            for comp in components:
                if comp in rules.lexeme_set:
                    continue
                if not _term_state_ok(state, comp, {"TERM_PERMITTED", "LABEL_PERMITTED", "CANONICAL_ALLOWED"}):
                    parks.append((item_id, "UNDEFINED_LEXEME"))
                    break
        return issues, parks

    if kind == "LABEL_DEF":
        if not reqs:
            issues.append((item_id, "SCHEMA_FAIL"))
        has_term = any(k == "TERM" for k, _ in defs)
        has_label = any(k == "LABEL" for k, _ in defs)
        if not has_term or not has_label:
            issues.append((item_id, "SCHEMA_FAIL"))
        if not any(tok == "LABEL_TOKEN" for tok, _ in asserts):
            issues.append((item_id, "SCHEMA_FAIL"))
        return issues, parks

    if kind == "CANON_PERMIT":
        if not reqs:
            issues.append((item_id, "SCHEMA_FAIL"))
        has_term = any(k == "TERM" for k, _ in defs)
        has_evidence = any(k == "REQUIRES_EVIDENCE" for k, _ in defs)
        if not has_term or not has_evidence:
            issues.append((item_id, "SCHEMA_FAIL"))
        if not any(tok == "PERMIT_TOKEN" for tok, _ in asserts):
            issues.append((item_id, "SCHEMA_FAIL"))
        return issues, parks

    if kind == "SIM_SPEC":
        evidence_fields = [v for k, v in defs if k == "REQUIRES_EVIDENCE"]
        if len(evidence_fields) == 0:
            parks.append((item_id, "SCHEMA_FAIL"))
            return issues, parks
        if len(evidence_fields) > 1:
            issues.append((item_id, "SCHEMA_FAIL"))
        if not any(tok == "EVIDENCE_TOKEN" for tok, _ in asserts):
            issues.append((item_id, "SCHEMA_FAIL"))
        return issues, parks

    return issues, parks


def validate_export_block(text, state, rules=None):
    rules = rules or load_bootpack_rules()
    reject = []
    park = []
    reasons = []

    lines = text.splitlines()
    if not lines:
        return {"ok": False, "park": [], "reject": ["EMPTY"], "reasons": ["EMPTY"]}
    if not _BEGIN_RE.match(lines[0].strip()) or not any(_END_RE.match(l.strip()) for l in lines):
        return {"ok": False, "park": [], "reject": ["SCHEMA_FAIL"], "reasons": ["SCHEMA_FAIL"]}

    try:
        block = parse_export_block(text)
    except Exception:
        return {"ok": False, "park": [], "reject": ["SCHEMA_FAIL"], "reasons": ["SCHEMA_FAIL"]}

    if not block.export_id or not block.target or not block.proposal_type:
        return {"ok": False, "park": [], "reject": ["SCHEMA_FAIL"], "reasons": ["SCHEMA_FAIL"]}

    items = split_items(block.content_lines)
    if not items:
        return {"ok": False, "park": [], "reject": ["SCHEMA_FAIL"], "reasons": ["SCHEMA_FAIL"]}

    # Line-level scans
    for item in items:
        for line in item["lines"]:
            dtag = _scan_derived_only(line, rules, state)
            if dtag:
                reject.append(item["id"])
                reasons.append(dtag)
            utag = _scan_undefined_terms(line, rules, state)
            if utag:
                reject.append(item["id"])
                reasons.append(utag)

    # Schema checks
    for item in items:
        issues, parks = _validate_item_schema(item, rules, state)
        for issue in issues:
            reject.append(issue[0])
            reasons.append(issue[1])
        for p in parks:
            park.append(p[0])
            reasons.append(p[1])

    # Probe pressure
    if not reject:
        spec_count = len([i for i in items if i["header"] == "SPEC_HYP"])
        probe_count = len([i for i in items if i["header"] == "PROBE_HYP"])
        allowed_specs = probe_count * 10 + 9
        if spec_count > allowed_specs:
            to_park = spec_count - allowed_specs
            for item in reversed(items):
                if to_park <= 0:
                    break
                if item["header"] == "SPEC_HYP":
                    park.append(item["id"])
                    reasons.append("PROBE_PRESSURE")
                    to_park -= 1

    ok = len(reject) == 0 and len(park) == 0
    return {"ok": ok, "park": park, "reject": reject, "reasons": reasons}
