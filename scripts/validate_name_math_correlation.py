#!/usr/bin/env python3
"""Validate sim directory NAME <-> computed evidence correlation.

CEILING: this gate recomputes NO math; it checks NAME<->EVIDENCE
correlation only. It asks whether the sim directory name's math vocabulary has
corresponding computed structure in result JSONs, and whether the name is free
of project jargon. It enforces pure-math NAMING. It does NOT judge whether the
math is correct, admissible, or load-bearing. It does NOT run git and touches
no repo state. classification=scratch_diagnostic, promotion_allowed=false.

Depth-token rule: name tokens 1q/2q/3q/4q require an explicit Hilbert/state
dimension declaration of 2/4/8/16 respectively. This gate intentionally does
NOT treat finite_set_size as Hilbert dimension: in the v7 gold fixture,
finite_set_size=4 is the number of density-matrix states, not the Hilbert
dimension of a two-qubit system.

Usage:
  validate_name_math_correlation.py <sim_dir>
  validate_name_math_correlation.py --selftest
  validate_name_math_correlation.py --help

Output: JSON
  {"ok", "sim", "name_tokens", "math_tokens_satisfied", "violations"}
Exit: 0 if clean, 1 if any violation, 2 on usage error.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Callable

try:
    from admitted_math_terms import (
        EXACT_INFRA_KEYS,
        classify_token,
        is_admitted_compound,
        is_admitted_token,
        is_jargon_token,
        split_identifier,
    )
except ImportError:  # pragma: no cover - import path fallback for direct module loading
    _terms_path = Path(__file__).resolve().with_name("admitted_math_terms.py")
    _spec = importlib.util.spec_from_file_location("admitted_math_terms", _terms_path)
    if _spec is None or _spec.loader is None:
        raise
    _terms = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_terms)
    EXACT_INFRA_KEYS = _terms.EXACT_INFRA_KEYS
    classify_token = _terms.classify_token
    is_admitted_compound = _terms.is_admitted_compound
    is_admitted_token = _terms.is_admitted_token
    is_jargon_token = _terms.is_jargon_token
    split_identifier = _terms.split_identifier

BANNED_NAME_TOKENS = frozenset(
    {
        "terrain",
        "engine",
        "axis",
        "stage",
        "runtime",
        "shell",
        "flux",
        "gcm",
        "basin",
        "ratchet",
        "bridge",
        "manifold",
        "sector",
        "chirality",
        "se",
        "ne",
        "ni",
        "si",
        "te",
        "ti",
        "fe",
        "fi",
    }
)

BACKEND_ENGINE_VALUES = frozenset({"jax", "julia", "pytorch"})
DEPTH_DIMS = {"1q": 2, "2q": 4, "3q": 8, "4q": 16}
QUARANTINE_KEYS = frozenset({"legacy_project_labels", "legacy_paths", "legacy_labels"})
ENVELOPE_INFRA_EXEMPT_KEYS = frozenset(
    {
        "engines",
        "engine_values",
        "engine_rows_match",
        "engine_consensus",
        "canon_runtime",
        "foreign_runtime",
    }
)
RUNTIME_EXEMPT_KEYS = frozenset({"canon_runtime", "foreign_runtime"})

# The dict is intentionally data-shaped: each allowed standard-math name token
# maps to the structural evidence the gate requires if that token appears.
MATH_VOCAB: dict[str, str] = {
    "quotient": "quotient/equivalence/partition/classes key in result JSON",
    "distinguishability": "probe_expectations plus state/probe/separation evidence in result JSON",
    "entropy": "von_neumann_entropy/shannon_entropy/entropy key with numeric value in result JSON",
    "cut": "partition/cut key plus per-cut numeric observable in result JSON",
    "bipartition": "partition/bipartition key plus per-cut numeric observable in result JSON",
    "compatibility": "partial_trace plus compatibility/inverse-system/consistency key in result JSON",
    "inverse_system": "partial_trace plus compatibility/inverse-system/consistency key in result JSON",
    "geometry": "Bloch/correlation-matrix/connection/curvature structure in result JSON",
    "hopf": "connection plus curvature, or connection_1_form plus curvature_2_form, in result JSON",
    "curvature": "curvature/2_form/dA/field_strength key in result JSON",
    "holonomy": "holonomy/loop_integral/wilson_loop/parallel_transport key in result JSON",
    "floor": "affirmative F01/N01 lineage marker in result JSON or spec.json",
    "foundation": "affirmative F01/N01 lineage marker in result JSON or spec.json",
    "endofunction": "computed endofunction/transition table or map in result JSON",
    "scc": "computed strongly-connected-component classes/count in result JSON",
    "terminal": "computed terminal/absorbing structure in result JSON",
    "involution": "computed involution/sigma structure, and if paired with quotient then quotient-by-involution/orbit evidence",
    "radix": "computed mixed-radix/radix structure in result JSON",
    "z2": "computed Z/2/parity/mod-2 coordinate structure in result JSON",
    "1q": "explicit Hilbert/state dimension equals 2 in result JSON",
    "2q": "explicit Hilbert/state dimension equals 4 in result JSON",
    "3q": "explicit Hilbert/state dimension equals 8 in result JSON",
    "4q": "explicit Hilbert/state dimension equals 16 in result JSON",
}

LINEAGE_KEY_RE = re.compile(
    r"(ancestry|lineage|provenance|derived_from|grounded_in|rung)", re.IGNORECASE
)
ANCESTRY_MARKER_RE = re.compile(r"(?<![A-Za-z0-9])(F01|N01)(?![A-Za-z0-9])", re.IGNORECASE)
DENIAL_RE = re.compile(
    r"\b(no|not|none|never|without|absent|missing|lacks?|null|undefined|"
    r"unestablished|not\s+established|no\s+grounding|chosen)\b",
    re.IGNORECASE,
)


def tokenize(text: str) -> list[str]:
    """Split an identifier and peel trailing digits (axis0 -> axis)."""
    raw = [t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t]
    tokens: list[str] = []
    for t in raw:
        tokens.append(t)
        stripped = t.rstrip("0123456789")
        if stripped and stripped != t:
            tokens.append(stripped)
    return tokens


def _engine_token_exempt(full_identifier: str, value: object | None = None) -> bool:
    """Match validate_math_only_packet's bare backend-leg exemption style.

    The exact whole key/token `engine` whose value is jax/julia/pytorch is a
    backend leg label. Compound identifiers carrying engine are not exempt. In
    a directory name there is no backend value, so bare `engine` is treated as
    the jargon object and fails.
    """
    ident = full_identifier.strip().lower()
    if ident in ENVELOPE_INFRA_EXEMPT_KEYS or ident in EXACT_INFRA_KEYS:
        return True
    if ident == "engine_leg" or ident == "engine_leg_result":
        return True
    if ident.startswith("engine_leg_"):
        suffix = ident.removeprefix("engine_leg_")
        return suffix in {"result", "results"} or is_admitted_compound(suffix)
    if ident != "engine":
        return False
    return isinstance(value, str) and value.strip().lower() in BACKEND_ENGINE_VALUES


def _banned_hits(text: str, *, value: object | None = None, value_context: bool = False) -> list[str]:
    hits: list[str] = []
    for tok in tokenize(text):
        if tok == "engine" and (value_context or _engine_token_exempt(text, value)):
            continue
        if tok == "runtime" and text.strip().lower() in RUNTIME_EXEMPT_KEYS:
            continue
        if is_admitted_token(tok):
            continue
        if tok in BANNED_NAME_TOKENS or is_jargon_token(tok):
            hits.append(tok)
        elif tok.startswith("engine") and tok != "engine" and not value_context and not _engine_token_exempt(text, value):
            hits.append("engine")
    return _dedupe(hits)


def _json_surface_violations(
    text: str,
    *,
    detail_prefix: str,
    key_context: bool,
    value: object | None = None,
    include_undefined: bool = True,
) -> list[dict[str, str]]:
    if _engine_token_exempt(text, value) or is_admitted_compound(text):
        return []
    kind_suffix = "json_key" if key_context else "json_value"
    violations: list[dict[str, str]] = []
    seen: set[str] = set()
    for tok in split_identifier(text):
        if not tok or tok in seen:
            continue
        stripped = tok.rstrip("0123456789")
        report_tok = stripped if stripped and stripped != tok and is_jargon_token(stripped) else tok
        if tok == "engine" and not key_context:
            cls = "admitted"
        elif tok == "engine" and not _engine_token_exempt(text, value):
            cls = "jargon"
        else:
            cls = classify_token(tok)
        if cls == "admitted":
            seen.add(tok)
            continue
        if cls == "undefined" and not include_undefined:
            seen.add(tok)
            continue
        if cls == "jargon" and stripped and stripped != tok:
            seen.add(stripped)
        seen.add(tok)
        kind = f"jargon_in_{kind_suffix}" if cls == "jargon" else f"undefined_term_in_{kind_suffix}"
        violations.append(
            {
                "kind": kind,
                "class": cls,
                "token": report_tok,
                "detail": f"{detail_prefix} contains {cls} token '{report_tok}'",
            }
        )
    return violations


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def tokenize_sim_name(name: str) -> tuple[list[str], list[str]]:
    """Tokenize a sim directory name, peeling vN and recording q-depth tokens."""
    parts = [p.lower() for p in name.split("_") if p]
    if parts and re.fullmatch(r"v\d+", parts[-1]):
        parts = parts[:-1]

    name_tokens: list[str] = []
    depth_tokens: list[str] = []
    for part in parts:
        subtokens = tokenize(part)
        for tok in subtokens:
            if tok in DEPTH_DIMS and tok not in depth_tokens:
                depth_tokens.append(tok)
            name_tokens.append(tok)

    # The name split on "_" breaks inverse_system into two tokens; restore the
    # standard math phrase for evidence matching while preserving the pieces.
    for idx in range(len(parts) - 1):
        if parts[idx] == "inverse" and parts[idx + 1] == "system":
            name_tokens.append("inverse_system")

    return _dedupe(name_tokens), depth_tokens


def banned_name_hits(name: str) -> list[str]:
    hits: list[str] = []
    for tok in tokenize_sim_name(name)[0]:
        if tok == "engine" and _engine_token_exempt(tok):
            continue
        if tok in BANNED_NAME_TOKENS:
            hits.append(tok)
        elif tok.startswith("engine") and tok != "engine":
            hits.append("engine")
    return _dedupe(hits)


def collect_result_files(sim_dir: Path) -> list[Path]:
    results_dir = sim_dir / "results"
    search = results_dir if results_dir.is_dir() else sim_dir
    return sorted(search.glob("*.json"))


def collect_surface_files(sim_dir: Path) -> list[Path]:
    files: list[Path] = []
    spec = sim_dir / "spec.json"
    if spec.is_file():
        files.append(spec)
    files.extend(collect_result_files(sim_dir))
    return files


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def _walk_json_keys(node: object, entries: list[tuple[str, str, object]], path: str = "") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            key_s = str(key)
            child = f"{path}.{key_s}" if path else key_s
            entries.append((child.lower(), key_s.lower(), value))
            _walk_json_keys(value, entries, child)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _walk_json_keys(item, entries, f"{path}[{idx}]")


def _entries_from_files(files: list[Path]) -> list[tuple[str, str, object]]:
    entries: list[tuple[str, str, object]] = []
    for path in files:
        data = _load_json(path)
        if data is not None:
            _walk_json_keys(data, entries)
    return entries


def _walk_banned_json_surface(
    node: object,
    violations: list[dict[str, str]],
    file_path: Path,
    path: str = "",
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            key_s = str(key)
            child = f"{path}.{key_s}" if path else key_s
            if key_s in QUARANTINE_KEYS:
                continue
            violations.extend(
                _json_surface_violations(
                    key_s,
                    detail_prefix=f"{file_path}:{child} key",
                    key_context=True,
                    value=value,
                )
            )
            if isinstance(value, str) and key_s != "schema":
                violations.extend(
                    _json_surface_violations(
                        value,
                        detail_prefix=f"{file_path}:{child} value",
                        key_context=False,
                        include_undefined=False,
                    )
                )
            if isinstance(value, (dict, list)):
                _walk_banned_json_surface(value, violations, file_path, child)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _walk_banned_json_surface(item, violations, file_path, f"{path}[{idx}]")
    elif isinstance(node, str):
        violations.extend(
            _json_surface_violations(
                node,
                detail_prefix=f"{file_path}:{path} value",
                key_context=False,
                include_undefined=False,
            )
        )


def banned_json_surface_violations(files: list[Path]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path in files:
        data = _load_json(path)
        if data is not None:
            _walk_banned_json_surface(data, violations, path)
    return violations


def _has_numeric_leaf(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, dict):
        return any(_has_numeric_leaf(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_numeric_leaf(v) for v in value)
    return False


def _has_structural_value(value: object) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (dict, list)):
        return len(value) > 0
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _has_key(
    entries: list[tuple[str, str, object]],
    patterns: tuple[str, ...],
    value_predicate: Callable[[object], bool] = _has_structural_value,
) -> bool:
    for path, key, value in entries:
        haystacks = (path, key)
        if any(pattern in h for pattern in patterns for h in haystacks) and value_predicate(value):
            return True
    return False


def _is_denial_value(value: object) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return True
        return bool(DENIAL_RE.search(stripped))
    return False


def _value_has_affirmative_marker(value: object) -> bool:
    if _is_denial_value(value):
        return False
    if isinstance(value, str):
        return bool(ANCESTRY_MARKER_RE.search(value))
    if isinstance(value, dict):
        return _has_affirmative_lineage(value)
    if isinstance(value, list):
        return any(_value_has_affirmative_marker(item) for item in value)
    return False


def _has_affirmative_lineage(node: object) -> bool:
    if isinstance(node, dict):
        for key, value in node.items():
            key_s = str(key)
            key_has_marker = bool(ANCESTRY_MARKER_RE.search(key_s))
            key_is_lineage = bool(LINEAGE_KEY_RE.search(key_s))
            if key_has_marker and not _is_denial_value(value):
                return True
            if key_is_lineage and _value_has_affirmative_marker(value):
                return True
            if _has_affirmative_lineage(value):
                return True
    elif isinstance(node, list):
        return any(_has_affirmative_lineage(item) for item in node)
    return False


def _has_lineage_evidence(sim_dir: Path, result_files: list[Path]) -> bool:
    lineage_files = [*result_files]
    spec = sim_dir / "spec.json"
    if spec.is_file():
        lineage_files.append(spec)
    for path in lineage_files:
        data = _load_json(path)
        if data is not None and _has_affirmative_lineage(data):
            return True
    return False


def _collect_integer_leafs(value: object) -> list[int]:
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, float) and value.is_integer():
        return [int(value)]
    if isinstance(value, dict):
        out: list[int] = []
        for child in value.values():
            out.extend(_collect_integer_leafs(child))
        return out
    if isinstance(value, list):
        out: list[int] = []
        for child in value:
            out.extend(_collect_integer_leafs(child))
        return out
    return []


DIMENSION_KEYS = frozenset(
    {"dim", "dimension", "hilbert_dim", "hilbert_dimension", "state_dim", "state_dimension"}
)
DIMENSION_CONTAINER_KEYS = frozenset({"rungs", "by_depth", "hilbert_dimensions_by_depth"})


def _collect_nested_declared_dimensions(node: object) -> list[int]:
    dims: list[int] = []
    if isinstance(node, dict):
        for key, value in node.items():
            key_s = str(key).lower()
            if key_s == "finite_set_size":
                continue
            explicit = (
                key_s in DIMENSION_KEYS
                or "hilbert_dim" in key_s
                or "hilbert_dimension" in key_s
                or "state_dim" in key_s
                or "state_dimension" in key_s
            )
            if explicit:
                dims.extend(_collect_integer_leafs(value))
            elif isinstance(value, (dict, list)):
                dims.extend(_collect_nested_declared_dimensions(value))
    elif isinstance(node, list):
        for child in node:
            dims.extend(_collect_nested_declared_dimensions(child))
    return dims


def _declared_dimensions(entries: list[tuple[str, str, object]]) -> list[int]:
    dims: list[int] = []
    for _path, key, value in entries:
        if key == "finite_set_size":
            continue
        if key in DIMENSION_CONTAINER_KEYS:
            dims.extend(_collect_nested_declared_dimensions(value))
        explicit = (
            key in DIMENSION_KEYS
            or "hilbert_dim" in key
            or "hilbert_dimension" in key
            or "state_dim" in key
            or "state_dimension" in key
        )
        if not explicit:
            continue
        dims.extend(_collect_integer_leafs(value))
    return dims


def _has_involution_evidence(entries: list[tuple[str, str, object]]) -> bool:
    has_definition = _has_key(entries, ("involution_definition", "sigma"))
    has_computation = _has_key(
        entries,
        ("involution_is_equivariant", "equivariance", "sigma_orbit", "involution_orbit", "fixed_point"),
    )
    return has_definition and has_computation


def _has_quotient_under_involution_evidence(entries: list[tuple[str, str, object]]) -> bool:
    return _has_key(
        entries,
        (
            "quotient_by_involution",
            "involution_quotient",
            "quotient_under_involution",
            "quotient_with_respect_to_involution",
            "equivariant_quotient",
            "sigma_orbit",
            "sigma_quotient",
            "orbit_quotient",
            "z2_orbit",
            "involution_orbit_partition",
        ),
    )


def check_math_evidence(
    token: str,
    entries: list[tuple[str, str, object]],
    sim_dir: Path,
    result_files: list[Path],
    name_tokens: list[str] | None = None,
) -> bool:
    if token == "quotient":
        if name_tokens and "involution" in name_tokens:
            return _has_quotient_under_involution_evidence(entries)
        return _has_key(entries, ("quotient_classes", "quotient_class_count", "equivalence", "partition", "classes"))
    if token == "distinguishability":
        has_probe_expectations = _has_key(entries, ("probe_expectations",))
        has_family_or_separation = _has_key(
            entries,
            ("state_labels", "probe_family", "separation", "indistinguishability"),
        )
        return has_probe_expectations and has_family_or_separation
    if token == "entropy":
        return _has_key(entries, ("von_neumann_entropy", "shannon_entropy", "entropy"), _has_numeric_leaf)
    if token in {"cut", "bipartition"}:
        has_partition = _has_key(entries, ("cut", "bipartition", "partition"))
        has_per_cut_numeric = _has_key(
            entries,
            (
                "per_cut",
                "cut_entropy",
                "cut_value",
                "cut_observable",
                "cut_measure",
                "bipartition_entropy",
                "partition_entropy",
            ),
            _has_numeric_leaf,
        )
        return has_partition and has_per_cut_numeric
    if token in {"compatibility", "inverse_system"}:
        return _has_key(entries, ("partial_trace",)) and _has_key(
            entries, ("compatibility", "compatible", "inverse_system", "consistency")
        )
    if token == "geometry":
        return _has_key(entries, ("bloch", "correlation_matrix", "connection", "curvature"))
    if token == "hopf":
        return _has_key(entries, ("connection_1_form", "connection")) and _has_key(
            entries, ("curvature_2_form", "curvature")
        )
    if token == "curvature":
        return _has_key(entries, ("curvature", "2_form", "da", "field_strength"))
    if token == "holonomy":
        return _has_key(entries, ("holonomy", "loop_integral", "wilson_loop", "parallel_transport"))
    if token in {"floor", "foundation"}:
        return _has_lineage_evidence(sim_dir, result_files)
    if token == "endofunction":
        return _has_key(entries, ("endofunction_table", "transition_map", "transition_table"))
    if token == "scc":
        return _has_key(entries, ("scc_classes", "scc_count", "strongly_connected"))
    if token == "terminal":
        return _has_key(entries, ("terminal_scc", "terminal", "absorbing"))
    if token == "involution":
        if name_tokens and "quotient" in name_tokens:
            return _has_involution_evidence(entries) and _has_quotient_under_involution_evidence(entries)
        return _has_involution_evidence(entries)
    if token == "radix":
        return _has_key(entries, ("mixed_radix_shape", "radix"))
    if token == "z2":
        return _has_key(entries, ("z2", "parity", "mod_2", "mod2"))
    if token in DEPTH_DIMS:
        dims = _declared_dimensions(entries)
        expected = DEPTH_DIMS[token]
        # A sim name may honestly declare a depth range such as
        # ``1q_through_4q``.  In that case several Hilbert dimensions are
        # present in one result surface, so the token is backed when its
        # expected dimension appears explicitly.  ``finite_set_size`` remains
        # excluded above: a finite sample size is not a Hilbert dimension.
        return expected in dims
    return True


def _math_tokens_in_name(name_tokens: list[str], depth_tokens: list[str]) -> list[str]:
    tokens: list[str] = []
    for tok in name_tokens:
        if tok in MATH_VOCAB:
            tokens.append(tok)
    for tok in depth_tokens:
        if tok in MATH_VOCAB:
            tokens.append(tok)
    return _dedupe(tokens)


def evaluate(sim_dir: Path) -> dict:
    name_tokens, depth_tokens = tokenize_sim_name(sim_dir.name)
    result_files = collect_result_files(sim_dir)
    surface_files = collect_surface_files(sim_dir)
    entries = _entries_from_files(result_files)

    violations: list[dict[str, str]] = []
    for tok in banned_name_hits(sim_dir.name):
        violations.append(
            {
                "kind": "jargon_in_name",
                "token": tok,
                "detail": f"directory name contains banned project-jargon token '{tok}'",
            }
        )
    violations.extend(banned_json_surface_violations(surface_files))

    math_tokens_satisfied: list[str] = []
    for tok in _math_tokens_in_name(name_tokens, depth_tokens):
        if check_math_evidence(tok, entries, sim_dir, result_files, name_tokens):
            math_tokens_satisfied.append(tok)
        else:
            violations.append(
                {
                    "kind": "name_claims_math_absent",
                    "token": tok,
                    "detail": f"name token '{tok}' requires evidence: {MATH_VOCAB[tok]}",
                }
            )

    return {
        "ok": not violations,
        "sim": sim_dir.name,
        "name_tokens": name_tokens,
        "math_tokens_satisfied": math_tokens_satisfied,
        "violations": violations,
    }


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _selftest() -> int:
    import tempfile

    failures: list[str] = []

    def expect(condition: bool, label: str) -> None:
        if not condition:
            failures.append(label)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        def build(name: str, result: dict, spec: dict | None = None) -> Path:
            sim = root / name
            _write_json(sim / "results" / f"{name}_results.json", result)
            if spec is not None:
                _write_json(sim / "spec.json", spec)
            return sim

        lineage_spec = {"lineage": {"F01": "probe-relative distinguishability", "N01": "fixed finite rung"}}

        gold = build(
            "distinguishability_quotient_floor_v0",
            {
                "finite_set_size": 4,
                "state_labels": ["s0", "s1", "s2", "s3"],
                "probe_expectations_full": {"s0": [0.0, 0.0, 0.0]},
                "quotient_classes_full": [["s0"], ["s1"], ["s2"], ["s3"]],
                "quotient_class_count_full": 4,
            },
            lineage_spec,
        )
        report = evaluate(gold)
        expect(report["ok"], f"gold-style should pass: {report['violations']}")

        bad_name = build("axis0_terrain_engine_leap_v0", {"all_pass": True})
        report = evaluate(bad_name)
        tokens = {v["token"] for v in report["violations"] if v["kind"] == "jargon_in_name"}
        expect(not report["ok"] and {"axis", "terrain", "engine"} <= tokens, "bad twin name jargon not caught")

        missing_entropy = build("entropy_floor_v0", {"state_labels": ["s0"]}, lineage_spec)
        report = evaluate(missing_entropy)
        expect(
            any(v["kind"] == "name_claims_math_absent" and v["token"] == "entropy" for v in report["violations"]),
            "entropy claim without entropy observable should fail",
        )

        mismatched_2q = build("probe_2q_v0", {"hilbert_dim": 8})
        report = evaluate(mismatched_2q)
        expect(
            any(v["kind"] == "name_claims_math_absent" and v["token"] == "2q" for v in report["violations"]),
            "2q name with hilbert_dim=8 should fail",
        )

        geometry = build(
            "quotient_geometry_v0",
            {"quotient_classes": [["s0"]], "bloch_vector": {"s0": [0.0, 0.0, 1.0]}},
        )
        report = evaluate(geometry)
        expect(report["ok"], f"quotient_geometry should pass: {report['violations']}")

        good_2q = build("state_2q_v0", {"hilbert_dim": 4})
        report = evaluate(good_2q)
        expect(report["ok"] and "2q" in report["math_tokens_satisfied"], "2q with hilbert_dim=4 should pass")

        through_1q_4q = build(
            "state_1q_through_4q_v0",
            {"hilbert_dimensions_by_depth": {"1q": 2, "2q": 4, "3q": 8, "4q": 16}},
        )
        report = evaluate(through_1q_4q)
        expect(
            report["ok"] and {"1q", "4q"} <= set(report["math_tokens_satisfied"]),
            f"1q_through_4q with explicit 2/4/8/16 Hilbert dimensions should pass: {report['violations']}",
        )

        nested_rungs_only = build(
            "state_1q_2q_3q_4q_v0",
            {
                "rungs": {
                    "1q": {"hilbert_dimension": 2},
                    "2q": {"hilbert_dimension": 4},
                    "3q": {"hilbert_dimension": 8},
                    "4q": {"hilbert_dimension": 16},
                }
            },
        )
        report = evaluate(nested_rungs_only)
        expect(
            report["ok"] and {"1q", "2q", "3q", "4q"} <= set(report["math_tokens_satisfied"]),
            f"nested rungs-only Hilbert dimensions should satisfy depth tokens: {report['violations']}",
        )

        mbti_spec = build(
            "clean_math_name_v0",
            {"schema": "codex_ratchet.engine_leg_result.v1", "engine": "jax"},
            {
                "description": "Each engine leg reads the table.",
                "orientation_tables": {"plus": {"radix_digit_0_word_rows": [["Se", "Ne", "Ni", "Si"]]}},
                "word_readout_components": {"Te": ["win", "loss"]},
                "legacy_project_labels": {"Se": "quarantined", "axis": "quarantined"},
            },
        )
        report = evaluate(mbti_spec)
        mbti_tokens = {v["token"] for v in report["violations"]}
        expect(
            not report["ok"] and {"se", "ne", "ni", "si", "te"} <= mbti_tokens and "engine" not in mbti_tokens,
            f"MBTI key/value jargon outside quarantine should fail without engine/schema false positives: {report['violations']}",
        )

        envelope_infra = build(
            "plain_envelope_v0",
            {
                "density_matrix_trace": 1.0,
                "engines": ["jax", "julia", "pytorch"],
                "engine_values": {"jax": 1.0, "julia": 1.0, "pytorch": 1.0},
                "engine_rows_match": True,
                "engine_consensus": {"all_equal": True},
                "canon_runtime": "julia",
                "foreign_runtime": "jax",
            },
        )
        report = evaluate(envelope_infra)
        envelope_bad = [
            v for v in report["violations"]
            if v["kind"] in {"jargon_in_json_key", "jargon_in_json_value"}
            and v["token"] in {"engine", "runtime"}
        ]
        expect(report["ok"] and not envelope_bad, f"envelope infra keys should pass: {report['violations']}")

        engine_jargon = build(
            "plain_key_scan_v0",
            {
                "terrain_engine": 1,
                "engine_tier": 2,
                "terrain_runtime": 3,
            },
        )
        report = evaluate(engine_jargon)
        engine_jargon_tokens = {
            v["token"] for v in report["violations"] if v["kind"] == "jargon_in_json_key"
        }
        expect(
            not report["ok"] and {"terrain", "engine", "runtime"} <= engine_jargon_tokens,
            f"engine/runtime over-exemption should still fire: {report['violations']}",
        )

        engine_leg_result = build("plain_leg_result_v0", {"engine_leg_result": True})
        report = evaluate(engine_leg_result)
        expect(report["ok"], f"engine_leg_result should be exempt: {report['violations']}")

        engine_leg_tier = build("plain_leg_tier_v0", {"engine_leg_tier": True})
        report = evaluate(engine_leg_tier)
        expect(
            not report["ok"] and any(v["token"] == "tier" for v in report["violations"]),
            f"engine_leg_tier should be flagged: {report['violations']}",
        )

        quotient_under_involution = build(
            "mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0",
            {
                "endofunction_table": [0, 1],
                "scc_classes": [[0], [1]],
                "terminal_scc_count": 1,
                "quotient_classes": [[0], [1]],
                "involution_definition": {"sigma": [1, 0]},
                "involution_is_equivariant": {"ok": True},
                "mixed_radix_shape": [2, 4],
                "parity_coordinate": [0, 1],
            },
        )
        report = evaluate(quotient_under_involution)
        expect(
            any(
                v["kind"] == "name_claims_math_absent" and v["token"] in {"quotient", "involution"}
                for v in report["violations"]
            ),
            "quotient under involution must fail without quotient-by-involution/orbit evidence",
        )

        quotient_by_involution = build(
            "radix_endofunction_scc_terminal_quotient_under_z2_involution_v0",
            {
                "endofunction_table": [0, 1],
                "scc_classes": [[0], [1]],
                "terminal_scc_count": 1,
                "quotient_by_involution": [[0, 1]],
                "sigma_orbit": [[0, 1]],
                "involution_definition": {"sigma": [1, 0]},
                "involution_is_equivariant": {"ok": True},
                "mixed_radix_shape": [2, 4],
                "parity_coordinate": [0, 1],
            },
        )
        report = evaluate(quotient_by_involution)
        expect(report["ok"], f"quotient-by-involution evidence should pass: {report['violations']}")

        hopf_missing_curvature = build("hopf_v0", {"connection_1_form": [0.0, 1.0]})
        report = evaluate(hopf_missing_curvature)
        expect(
            any(v["kind"] == "name_claims_math_absent" and v["token"] == "hopf" for v in report["violations"]),
            "hopf with only connection should fail",
        )

        floor = build("floor_v0", {"lineage": {"F01": "affirmative root surface"}})
        report = evaluate(floor)
        expect(report["ok"] and "floor" in report["math_tokens_satisfied"], "floor with F01 lineage should pass")

        foundation_denial = build(
            "foundation_v0",
            {
                "f01_ancestry": None,
                "_ancestry_note": "foundation name chosen; no F01/N01 grounding established",
            },
        )
        report = evaluate(foundation_denial)
        expect(
            any(v["kind"] == "name_claims_math_absent" and v["token"] == "foundation" for v in report["violations"]),
            "foundation with null/denial ancestry should fail",
        )

        finite_size_depth = build("state_2q_v0_finite_only", {"finite_set_size": 4})
        report = evaluate(finite_size_depth)
        expect(
            any(v["kind"] == "name_claims_math_absent" and v["token"] == "2q" for v in report["violations"]),
            "finite_set_size must not satisfy 2q Hilbert-dim evidence",
        )

    if failures:
        print("SELFTEST FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELFTEST PASSED")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mechanical sim-name/math-evidence correlation gate for one sim directory."
    )
    parser.add_argument("sim_dir", nargs="?", help="path to a sim directory")
    parser.add_argument("--selftest", action="store_true", help="run the built-in self-test and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return _selftest()
    if not args.sim_dir:
        print(json.dumps({"ok": False, "error": "provide a sim dir (or --selftest)"}))
        return 2
    sim_dir = Path(args.sim_dir)
    if not sim_dir.is_dir():
        print(json.dumps({"ok": False, "error": f"not a directory: {sim_dir}"}))
        return 2
    report = evaluate(sim_dir)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
