#!/usr/bin/env python3
"""GATE 2 — COUNT-TAUTOLOGY SMT detector (mechanical, deterministic; NO LLM judgment).

WHAT IT DOES
  Parses each result JSON's SMT containers (crossover_proofs / proofs / smt /
  smt_rows / smt_verdicts / ... ) together with TOOL_INTEGRATION_DEPTH and FLAGS
  any z3 / cvc5 (and z3/cvc5-via-engine: julia_z3, pytorch_z3, pytorch_cvc5, ...)
  proof entry that is tagged `load_bearing` while the proof itself is a pure
  COUNT TAUTOLOGY, i.e. one of:

    (A) SAT of "computed count(s) == pinned/expected/frozen/finite count(s)"
        (trivially SAT: you assert two integers you just computed are equal to
        the constants you pinned them to).
    (B) UNSAT of "(count == N) AND (count != N)" or "computed count != expected"
        (trivially UNSAT: the inequality of a constant against itself).
    (C) UNSAT of "product of bound computed counts differs from a bound computed
        count" where the product equality is a numeric identity over those counts
        (e.g. 8*8 == 64 subsubbasins). An `erased_flip` that flips only by
        CHANGING A COUNT (collapsing classes) does NOT rescue this — it flips for
        a COUNT reason, not a MATH reason.

  Such SMT is decorative-as-proof and should be tagged `supportive`, not
  `load_bearing`. The gate reports each offending (result, solver) pair.

WHAT RESCUES A PROOF (NOT flagged — these are genuine math-load-bearing SMT):
  - a structural / free-variable proof (sign algebra like b6 == -b0*b3, closure
    of a unit set, additivity of phases, a winner/inequality relation between two
    DISTINCT measured real quantities like scaled errors / holonomy / cos values);
  - an `erased_flip` / control that flips for a NON-count (math/structural) reason
    (e.g. flipping a sign relation, negating additivity, breaking a closure).
  These have a derived expression, scaled real values, or a sign/relation
  predicate — not a bare count==constant or count==product.

CEILING (read this):
  This gate is a MECHANICAL TEXT+SHAPE classifier over the proof-row metadata that
  builders already wrote into the result JSON. It is NOT a re-execution of the SMT
  solver and NOT a semantic proof checker. It judges the DESCRIBED proof shape
  (claim/assertion/encoding strings + bound count integers + verdict + erased_flip
  text), so it can be defeated by a builder who lies in those strings (writes a
  count tautology but describes it as a sign relation), and it can mis-handle a
  novel proof phrasing not covered by its patterns. It establishes only:
  `the proof METADATA describes a count tautology` (a flag to demote a tool from
  load_bearing to supportive) — NOT `the underlying math is wrong` and NOT any
  promotion. It never mutates a sim. Verdict ladder it serves:
  exists < runs < passes local rerun < canonical by process — this gate sits below
  all of those as a load-bearing-honesty lint.

OUTPUT: JSON {"ok": bool, "violations": [{path, solver, container, reason, claim,
              counts, verdict}], "scanned": int}
EXIT: 0 if ok (no violations), 1 if any violation, 2 on bad/empty input.

USAGE:
  validate_smt_not_tautology.py                 # scan all 230 sims under system_v6/sims
  validate_smt_not_tautology.py <result.json>   # scan one result JSON
  validate_smt_not_tautology.py <sim_dir>       # scan one sim's results/*.json
  validate_smt_not_tautology.py --selftest      # built-in self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SIMS_GLOB = str(REPO / "system_v6" / "sims" / "*" / "results" / "*_results.json")

# Keys that hold SMT / proof payloads (observed repo-wide).
PROOF_CONTAINER_KEYS = {
    "crossover_proofs", "proofs", "smt", "smt_rows", "smt_verdicts",
    "smt_proofs", "exact_smt", "weld_relation_smt", "weld_smt_rows",
    "smt_by_engine", "crossover_proofs_by_source", "decisive_smt_cells",
    "n4_crossover_proofs", "n5_crossover_proofs", "n6_crossover_proofs",
    "n7_crossover_proofs", "n8_crossover_proofs", "gksl_all_t_proofs",
    "julia_z3_smt_row", "julia_z3_smt_rows", "proofs_flip",
    "smt_equivariance_flip", "equivariance_flip", "smt_flip",
    "z3_equivariance", "cvc5_equivariance",
}

# Solver names that count as a z3/cvc5 SMT leg (incl. engine-prefixed).
SOLVER_RE = re.compile(r"(?:^|_)(z3|cvc5)(?:_|$)")


def _is_solver_key(key: str) -> bool:
    return bool(SOLVER_RE.search(key.lower()))


# ---- text patterns -------------------------------------------------------

# A claim/assertion that asserts a computed count equals a pinned/expected one.
# NOTE: `count` is matched as a substring (e.g. survivor_count, quotient_class_count),
# so NO leading \b on `count` — `_count` has no word boundary before `count`.
COUNT_EQ_RE = re.compile(
    r"count\b.*\b(equal|match(es)?)\b.*"
    r"\b(pinned|expected|frozen|finite|precomputed)\b",
    re.IGNORECASE,
)
COUNT_EQ_RE2 = re.compile(  # "... equal the frozen ... expectations" / "equal pinned finite counts"
    r"\b(equal|match(es)?)\b.*\b(pinned|expected|frozen|finite|precomputed)\b.*"
    r"(count|expectation)",
    re.IGNORECASE,
)
# "computed survivor_count != expected" / "count == N and count != N"
COUNT_NEQ_RE = re.compile(
    r"\bcomputed\b.*count\b.*(!=|not\s*equal|differs).*\bexpected\b",
    re.IGNORECASE,
)
# product-of-counts vs count: "... product differs from computed ... count"
PRODUCT_COUNT_RE = re.compile(
    r"\bproduct\b.*(differs|!=|equals?|matches?).*count\b",
    re.IGNORECASE,
)

# Math escapes: a relation/structure predicate or a real-valued (non-count) quantity.
MATH_ESCAPE_RE = re.compile(
    r"\b("
    r"sign|relation|additivity|phi|cos|sin|holonomy|winner|"
    r"error|residual|spectrum|eigen|negativity|"
    r"b0|b3|b6|closure|chirality|anticommut|structure[_ ]?constant|"
    r"linking|cocycle|metric|invariant|lyapunov|gauss|interval|"
    r"derived[_ ]?expression"
    r")\b",
    re.IGNORECASE,
)

GROUND_BOUND_RE = re.compile(
    r"("
    r"(constrained|bound|fixed)\s+to\s+the\s+computed\s+images?\s+over\s+all\s+\d*\s*states?|"
    r"bound\s+to\s+the\s+computed|fully\s+bound|computed\s+literals?|"
    r"over\s+all\s+\d+\s+states?|all\s+\d+\s+states?"
    r")",
    re.IGNORECASE,
)
GROUND_DISEQUALITY_RE = re.compile(
    r"("
    r"disjunction\s+over.*disequal|"
    r"computed\s+image\s+disequal|"
    r"(exists?|any)\s+(a\s+)?state.*(!=|not\s+equal|disequal)|"
    r"query\s+is\s+a\s+disjunction.*(!=|disequal)"
    r")",
    re.IGNORECASE,
)
FREE_VARIABLE_RE = re.compile(
    r"\b(free\s+variable|universally\s+quantified|forall|for\s+all\s+symbolic|symbolic\s+variable)\b",
    re.IGNORECASE,
)

REAL_QUANTITY_KEY_RE = re.compile(
    r"("
    r"_error$|scaled.*(error|cos|value)|bound_scaled_cos_values|"
    r"residual|negativity|holonomy|eigenvalue|spectrum|metric|lyapunov"
    r")",
    re.IGNORECASE,
)


def _has_ground_bound_pattern(text: str) -> bool:
    if re.search(
        r"\bno\s+arrays?\s+(?:are\s+)?bound\s+to\s+computed\s+literals?\s+over\s+all\s+states?",
        text,
        re.IGNORECASE,
    ):
        return False
    return bool(GROUND_BOUND_RE.search(text))


def _collect_text(entry: dict) -> str:
    """Concatenate the descriptive fields of a proof entry (NOT nested rows)."""
    parts = []
    for k in ("claim", "assertion", "encoding", "positive_case",
              "boundary_case", "negative_control", "polarity",
              "derived_expression", "single_shell_verdict", "question"):
        v = entry.get(k)
        if isinstance(v, str):
            parts.append(v)
    pr = entry.get("proof_row")
    if isinstance(pr, dict):
        for k in ("encoding", "erased_flip", "claim"):
            v = pr.get(k)
            if isinstance(v, str):
                parts.append(v)
    return " || ".join(parts)


def _erased_flip_is_count_based(entry: dict) -> bool:
    """True if the entry's erased_flip flips by CHANGING A COUNT (collapsing
    classes / counts), i.e. a count reason — NOT a math reason."""
    texts = []
    for src in (entry, entry.get("proof_row") if isinstance(entry.get("proof_row"), dict) else {}):
        if isinstance(src, dict):
            v = src.get("erased_flip")
            if isinstance(v, str):
                texts.append(v.lower())
    blob = " ".join(texts)
    if not blob:
        return False
    # count-reason flip: collapse classes / counts / drop a class -> changes a count
    count_flip = bool(re.search(r"collapse|drop|merge|one[_ ]?erased[_ ]?class|"
                                r"class(es)?[_ ]?to[_ ]?(one|1)", blob))
    # math-reason flip: flip a sign / relation / additivity / closure
    math_flip = bool(MATH_ESCAPE_RE.search(blob))
    return count_flip and not math_flip


def _structural_sources(entry: dict) -> list[dict]:
    out = []
    for src in (entry, entry.get("proof_row"), entry.get("input_object")):
        if isinstance(src, dict):
            out.append(src)
    return out


def _is_numeric_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        not isinstance(v, bool) and isinstance(v, (int, float)) for v in value
    )


def _real_quantity_referenced(key: str, text: str) -> bool:
    text_l = text.lower()
    key_l = key.lower()
    compact_text = re.sub(r"[^a-z0-9]+", "", text_l)
    compact_key = re.sub(r"[^a-z0-9]+", "", key_l)
    if key_l in text_l or key_l.replace("_", " ") in text_l or compact_key in compact_text:
        return True
    text_tokens = set(re.findall(r"[a-z0-9]+", text_l))
    key_tokens = [
        tok
        for tok in re.findall(r"[a-z0-9]+", key_l)
        if tok not in {"bound", "baseline", "qit", "scaled", "value", "values"}
    ]
    return any(tok in text_tokens for tok in key_tokens)


def _has_separate_real_field(entry: dict, text: str) -> bool:
    for src in _structural_sources(entry):
        for key, value in src.items():
            key_l = str(key).lower()
            if "count" in key_l:
                continue
            if not REAL_QUANTITY_KEY_RE.search(key_l):
                continue
            if not _real_quantity_referenced(key_l, text):
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, float):
                return True
            if isinstance(value, int):
                return True
            if _is_numeric_list(value):
                return True
    return False


def _has_structural_relation_field(entry: dict, text: str) -> bool:
    if _erased_flip_is_count_based(entry):
        return False
    for src in _structural_sources(entry):
        for key, value in src.items():
            key_l = str(key).lower()
            if isinstance(value, bool):
                if value and key_l == "negated_additivity_unsat":
                    return True
                continue
            if key_l == "derived_expression" and _has_separate_real_field(entry, text):
                return True
            if key_l == "erased_flip" and isinstance(value, str) and MATH_ESCAPE_RE.search(value):
                return True
            if ("relation" in key_l or "sign" in key_l) and value not in (None, "", False):
                return True
            if key_l.endswith("_verdict") and value not in (None, "", False):
                if MATH_ESCAPE_RE.search(key_l) or "erased_flip" in key_l or "control" in key_l:
                    return True
    return False


def _has_math_escape(entry: dict, text: str) -> bool:
    """A genuine non-count math signal that rescues the proof from being a
    count tautology."""
    return (
        _has_free_variable_escape(entry, text)
        or _has_separate_real_field(entry, text)
        or _has_structural_relation_field(entry, text)
    )


def _is_ground_constant_fold_disjunction(text: str) -> bool:
    return bool(_has_ground_bound_pattern(text) and GROUND_DISEQUALITY_RE.search(text))


def _has_free_variable_escape(entry: dict, text: str) -> bool:
    if _erased_flip_is_count_based(entry):
        return False
    if not FREE_VARIABLE_RE.search(text):
        return False
    if _is_ground_constant_fold_disjunction(text) or _has_ground_bound_pattern(text):
        return False
    return True


def _bound_counts(entry: dict) -> dict:
    out = {}
    for src in (entry, entry.get("input_object") if isinstance(entry.get("input_object"), dict) else {},
                entry.get("proof_row") if isinstance(entry.get("proof_row"), dict) else {}):
        if not isinstance(src, dict):
            continue
        for k, v in src.items():
            kl = k.lower()
            if isinstance(v, bool):
                continue
            if isinstance(v, int) and ("count" in kl or kl == "bound_value"):
                out[k] = v
    return out


def classify_entry(entry: dict) -> dict | None:
    """Return a violation dict if this proof entry is a count-tautology
    load_bearing offender, else None."""
    if not isinstance(entry, dict):
        return None
    if entry.get("load_bearing") is not True:
        return None

    text = _collect_text(entry)
    verdict = str(entry.get("verdict") or entry.get("single_shell_verdict") or "").lower()
    counts = _bound_counts(entry)

    if _is_ground_constant_fold_disjunction(text):
        return {
            "reason": "ground constant-fold disjunction (all indices bound to computed literals; no free variable; ~Python any())",
            "claim": text,
            "counts": counts,
            "verdict": verdict or "metadata",
        }

    # (A) SAT count-equality tautology
    if verdict == "sat" and (COUNT_EQ_RE.search(text) or COUNT_EQ_RE2.search(text)):
        if not _has_math_escape(entry, text):
            return {"reason": "SAT count-equality tautology (computed count == pinned/expected count)",
                    "claim": text, "counts": counts, "verdict": verdict}

    # (B) UNSAT count-inequality tautology
    if verdict == "unsat" and COUNT_NEQ_RE.search(text):
        if not _has_math_escape(entry, text):
            return {"reason": "UNSAT count-inequality tautology (computed count != expected; flips for a count reason)",
                    "claim": text, "counts": counts, "verdict": verdict}

    # (C) product-of-counts UNSAT tautology (8*8 == 64 etc.), rescued ONLY by a
    #     math-reason erased flip; a count-reason erased flip does NOT rescue.
    if verdict == "unsat" and PRODUCT_COUNT_RE.search(text):
        if _erased_flip_is_count_based(entry) or not _has_math_escape(entry, text):
            return {"reason": "UNSAT product-of-counts tautology (bound counts; product==count numeric identity; erased_flip changes a count, not math)",
                    "claim": text, "counts": counts, "verdict": verdict}

    return None


def _iter_solver_entries(node, container_name, trail):
    """Yield (solver_name, container_name, entry_dict) for solver-keyed proof
    entries inside a container. Handles {solver: {...}} and lists of rows."""
    if isinstance(node, dict):
        for k, v in node.items():
            if _is_solver_key(k) and isinstance(v, dict):
                yield (k, container_name, v)
            elif isinstance(v, (dict, list)):
                # descend one level (e.g. crossover_proofs_by_source -> source -> {z3:..})
                yield from _iter_solver_entries(v, container_name, trail + "." + str(k))
    elif isinstance(node, list):
        for item in node:
            yield from _iter_solver_entries(item, container_name, trail)


def _solver_bases_in_tree(node) -> set[str]:
    solvers: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            key_l = str(key).lower()
            if "z3" in key_l:
                solvers.add("z3")
            if "cvc5" in key_l:
                solvers.add("cvc5")
            solvers.update(_solver_bases_in_tree(value))
    elif isinstance(node, list):
        for item in node:
            solvers.update(_solver_bases_in_tree(item))
    return solvers


def _container_text_entry(node: object) -> dict | None:
    if not isinstance(node, dict):
        return None
    if not _collect_text(node):
        return None
    return dict(node)


def scan_result(path: Path) -> list[dict]:
    try:
        data = json.load(open(path))
    except Exception as exc:  # noqa: BLE001
        return [{"path": str(path), "solver": "<n/a>", "container": "<parse>",
                 "reason": f"unreadable JSON: {exc}", "claim": "", "counts": {}, "verdict": ""}]
    if not isinstance(data, dict):
        return []
    tid = data.get("TOOL_INTEGRATION_DEPTH")
    tid = tid if isinstance(tid, dict) else {}
    violations: list[dict] = []
    seen: set[tuple] = set()
    for key, val in data.items():
        if key not in PROOF_CONTAINER_KEYS:
            continue
        container_entry = _container_text_entry(val)
        if container_entry is not None:
            solver_bases = _solver_bases_in_tree(val)
            solver_bases.update(base for base in ("z3", "cvc5") if tid.get(base) == "load_bearing")
            for solver in sorted(solver_bases):
                tid_lb = tid.get(solver) == "load_bearing"
                if container_entry.get("load_bearing") is not True and not tid_lb:
                    continue
                probe = dict(container_entry)
                probe["load_bearing"] = True
                v = classify_entry(probe)
                if v is None:
                    continue
                dedup = (solver, key, v["reason"], json.dumps(v["counts"], sort_keys=True))
                if dedup in seen:
                    continue
                seen.add(dedup)
                violations.append({
                    "path": str(path), "solver": solver, "container": key,
                    "reason": v["reason"], "claim": v["claim"][:300],
                    "counts": v["counts"], "verdict": v["verdict"],
                    "tid_load_bearing": tid_lb,
                })
        for solver, container, entry in _iter_solver_entries(val, key, key):
            # The solver leg is load_bearing if the entry says so OR TOOL_INTEGRATION_DEPTH
            # tags z3/cvc5 load_bearing for this result.
            base = "z3" if "z3" in solver.lower() else ("cvc5" if "cvc5" in solver.lower() else solver)
            tid_lb = tid.get(base) == "load_bearing"
            if entry.get("load_bearing") is not True and not tid_lb:
                continue
            # Ensure load_bearing flag reflects either source for classify_entry.
            probe = dict(entry)
            if tid_lb:
                probe["load_bearing"] = True
            v = classify_entry(probe)
            if v is None:
                continue
            dedup = (solver, container, v["reason"], json.dumps(v["counts"], sort_keys=True))
            if dedup in seen:
                continue
            seen.add(dedup)
            violations.append({
                "path": str(path), "solver": solver, "container": container,
                "reason": v["reason"], "claim": v["claim"][:300],
                "counts": v["counts"], "verdict": v["verdict"],
                "tid_load_bearing": tid_lb,
            })
    return violations


def _expand_targets(target: str) -> list[Path]:
    p = Path(target)
    if p.is_dir():
        rd = p / "results"
        if rd.is_dir():
            return sorted(rd.glob("*_results.json"))
        return sorted(p.glob("*_results.json"))
    return [p]


def run(targets: list[Path]) -> dict:
    violations: list[dict] = []
    scanned = 0
    for t in targets:
        scanned += 1
        violations.extend(scan_result(t))
    return {"ok": len(violations) == 0, "violations": violations, "scanned": scanned}


# ---- self test -----------------------------------------------------------

def _selftest() -> int:
    failures: list[str] = []

    # OFFENDER A: SAT count-equality
    offA = {"crossover_proofs": {"z3": {
        "claim": "computed survivor_count and quotient_class_count equal pinned finite carve counts and are nonempty",
        "load_bearing": True, "ran": True, "verdict": "sat",
        "input_object": {"survivor_count": 8, "quotient_class_count": 4}}}}
    if not [v for v in scan_dict(offA) if v]:
        failures.append("offender A (SAT count-eq) not flagged")

    # ATTACK 1: a math escape word inside the count claim is decoration only.
    decoratedCount = {"crossover_proofs": {"z3": {
        "claim": "computed survivor_count equal pinned finite count; sign algebra note included in prose",
        "load_bearing": True, "ran": True, "verdict": "sat",
        "input_object": {"survivor_count": 8}}}}
    if not [v for v in scan_dict(decoratedCount) if v]:
        failures.append("decorated count-tautology escaped via raw math keyword")

    # ATTACK 1b: a bare float under an unrelated key cannot rescue a count tautology.
    decoratedFloat = {"crossover_proofs": {"z3": {
        "claim": "computed survivor_count equal pinned finite count",
        "load_bearing": True, "ran": True, "verdict": "sat",
        "input_object": {"survivor_count": 8, "foo_blah": 1.5}}}}
    if not [v for v in scan_dict(decoratedFloat) if v]:
        failures.append("decorated count-tautology escaped via dummy float")

    # CLEAN 0: a real quantity named in the proof text can rescue.
    cleanNamedReal = {"crossover_proofs": {"z3": {
        "claim": "computed survivor_count equal pinned finite count with holonomy residual referenced",
        "load_bearing": True, "ran": True, "verdict": "sat",
        "input_object": {"survivor_count": 8, "holonomy_residual": 0.125}}}}
    if [v for v in scan_dict(cleanNamedReal) if v]:
        failures.append("named real quantity still flagged (false positive)")

    # OFFENDER B: UNSAT count-inequality (3q)
    offB = {"crossover_proofs": {"cvc5": {
        "assertion": "computed survivor_count != expected", "bound_value": 545,
        "load_bearing": True, "ran": True, "verdict": "unsat"}}}
    if not [v for v in scan_dict(offB) if v]:
        failures.append("offender B (UNSAT count-neq) not flagged")

    # OFFENDER C: product-of-counts (8*8==64), erased_flip collapses a COUNT
    offC = {"crossover_proofs": {"z3": {
        "load_bearing": True, "ran": True, "verdict": "unsat",
        "proof_row": {"computed_l_marginal_count": 8, "computed_r_marginal_count": 8,
                      "computed_subsubbasin_count": 64,
                      "encoding": "bind computed L marginal terminal count and R marginal terminal count; assert product differs from computed subsubbasin count",
                      "erased_flip": "collapse R marginal terminal classes to one erased class"}}}}
    if not [v for v in scan_dict(offC) if v]:
        failures.append("offender C (product-of-counts 8*8==64) not flagged")

    # OFFENDER D: ground constant-fold image disequality over fully bound arrays
    offD = {
        "TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing", "cvc5": "load_bearing"},
        "smt_equivariance_flip": {
            "encoding": "Integer arrays T and sigma are constrained to the computed images over all 64 states; the query is a disjunction over computed image disequalities, not a count tautology.",
            "question": "does there exist a state s with T(sigma(s)) != sigma(T(s))?",
            "z3_equivariant_map": "unsat",
            "cvc5_equivariant_map": "unsat",
        },
    }
    if not [v for v in scan_dict(offD) if v and "ground constant-fold" in v["reason"]]:
        failures.append("offender D (ground constant-fold disequality disjunction) not flagged")

    # ATTACK 2: free-variable prose cannot rescue a fully bound constant fold.
    decoratedFold = {
        "TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing"},
        "smt_equivariance_flip": {
            "encoding": "Integer arrays T and sigma are constrained to the computed images over all 64 states; forall symbolic free variable prose is present, but the query is a disjunction over computed image disequalities.",
            "question": "does there exist a state s with T(sigma(s)) != sigma(T(s))?",
            "z3_equivariant_map": "unsat",
        },
    }
    if not [v for v in scan_dict(decoratedFold) if v and "ground constant-fold" in v["reason"]]:
        failures.append("decorated ground-fold escaped via free-variable prose")

    # CLEAN 1: sign relation b6 == -b0*b3 (smt_rows)
    cleanSign = {"smt_rows": {"z3": {
        "claim": "row-local cover b0/b3/b6 values are bound; forcing the opposite relation status is unsat, while erased flips are sat",
        "load_bearing": True, "ran": True, "verdict": "unsat",
        "erased_flip_verdict": "sat"}}}
    if [v for v in scan_dict(cleanSign) if v]:
        failures.append("clean sign-relation flagged (false positive)")

    # CLEAN 2: additivity / cos-value flux emergence
    cleanFlux = {"crossover_proofs": {"cvc5": {
        "bound_scaled_cos_values": [707106781166, 156434465034, -453990499712],
        "derived_expression": "phi_ij_core = c_i - c_j; common 2*pi factor is outside the integer-scaled proof",
        "load_bearing": True, "ran": True, "negated_additivity_unsat": True,
        "single_shell_verdict": "unsat", "verdict": "unsat"}}}
    if [v for v in scan_dict(cleanFlux) if v]:
        failures.append("clean flux-additivity flagged (false positive)")

    # CLEAN 3: scaled-error winner relation (ecd06) — UNSAT over two distinct real errors
    cleanErr = {"crossover_proofs": {"z3": {
        "claim": "finite scaled adjusted-error winner relation agrees with discriminator",
        "baseline_scaled_error": 608433223, "qit_scaled_error": 1081028411,
        "load_bearing": True, "ran": True, "verdict": "unsat"}}}
    if [v for v in scan_dict(cleanErr) if v]:
        failures.append("clean scaled-error winner flagged (false positive)")

    # CLEAN 4: g2 closure discriminator (unit-set closure, controls flip)
    cleanG2 = {"crossover_proofs": {"z3": {
        "claim": "A 3-imaginary-unit carrier cannot satisfy the installed seven-unit closure constraint; bare-root H/M2R remain SAT.",
        "H_7unit_closure_verdict": "unsat", "H_bare_root_verdict": "sat",
        "erased_closure_control_verdict": "sat", "load_bearing": True, "ran": True, "verdict": "unsat"}}}
    if [v for v in scan_dict(cleanG2) if v]:
        failures.append("clean g2-closure flagged (false positive)")

    # CLEAN 5: free-variable / universally quantified structural relation
    cleanFree = {"smt_equivariance_flip": {"z3": {
        "claim": "universally quantified structural relation over a free variable s with symbolic T and sigma",
        "encoding": "forall symbolic state s, T(sigma(s)) == sigma(T(s)); no arrays are bound to computed literals over all states",
        "load_bearing": True, "ran": True, "verdict": "unsat"}}}
    if [v for v in scan_dict(cleanFree) if v]:
        failures.append("clean free-variable structural SMT flagged (false positive)")

    # GUARD: supportive (not load_bearing) count-eq must NOT flag
    suppt = {"crossover_proofs": {"z3": {
        "claim": "computed survivor_count equal pinned finite count",
        "load_bearing": False, "ran": True, "verdict": "sat",
        "input_object": {"survivor_count": 8}}}}
    if [v for v in scan_dict(suppt) if v]:
        failures.append("supportive count-eq flagged (should require load_bearing)")

    if failures:
        print(json.dumps({"ok": False, "selftest": "FAIL", "failures": failures}, indent=2))
        return 1
    print(json.dumps({"ok": True, "selftest": "PASS",
                      "checked": ["offender A SAT count-eq", "offender B UNSAT count-neq",
                                  "offender C product 8*8==64", "clean sign-relation",
                                  "clean flux-additivity", "clean scaled-error winner",
                                  "clean g2-closure", "ground constant-fold disjunction",
                                  "decorated count-tautology", "decorated dummy-float",
                                  "named real quantity", "decorated ground-fold",
                                  "clean free-variable structural relation",
                                  "supportive-not-flagged"]}, indent=2))
    return 0


def scan_dict(data: dict) -> list[dict]:
    """Selftest helper: run the scanner over an in-memory result dict."""
    tid = data.get("TOOL_INTEGRATION_DEPTH")
    tid = tid if isinstance(tid, dict) else {}
    out = []
    for key, val in data.items():
        if key not in PROOF_CONTAINER_KEYS:
            continue
        container_entry = _container_text_entry(val)
        if container_entry is not None:
            solver_bases = _solver_bases_in_tree(val)
            solver_bases.update(base for base in ("z3", "cvc5") if tid.get(base) == "load_bearing")
            for solver in sorted(solver_bases):
                tid_lb = tid.get(solver) == "load_bearing"
                if container_entry.get("load_bearing") is not True and not tid_lb:
                    continue
                probe = dict(container_entry)
                probe["load_bearing"] = True
                v = classify_entry(probe)
                if v:
                    out.append(v)
        for solver, container, entry in _iter_solver_entries(val, key, key):
            base = "z3" if "z3" in solver.lower() else ("cvc5" if "cvc5" in solver.lower() else solver)
            tid_lb = tid.get(base) == "load_bearing"
            if entry.get("load_bearing") is not True and not tid_lb:
                continue
            probe = dict(entry)
            if tid_lb:
                probe["load_bearing"] = True
            v = classify_entry(probe)
            if v:
                out.append(v)
    return out


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GATE 2 — count-tautology SMT detector (mechanical, no LLM).")
    p.add_argument("target", nargs="?",
                   help="result JSON OR sim dir OR omit to scan all system_v6/sims.")
    p.add_argument("--selftest", action="store_true", help="run built-in self-test and exit.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return _selftest()
    if args.target:
        targets = _expand_targets(args.target)
    else:
        targets = sorted(Path(p) for p in glob.glob(SIMS_GLOB))
    if not targets:
        print(json.dumps({"ok": False, "violations": [], "scanned": 0,
                          "error": "no result JSON found"}))
        return 2
    result = run(targets)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
