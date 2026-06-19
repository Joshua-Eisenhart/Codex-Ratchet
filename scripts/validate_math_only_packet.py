#!/usr/bin/env python3
"""Math-only admission gate for sim result packets.

CEILING (read this first): this gate checks LANGUAGE, not correctness.
It enforces that a sim's executable/result SURFACE is pure math: project
owner-jargon and nicknames (terrain, engine-tier, axis, stage, runtime, shell,
flux, rpf, retrocausal, possibility_field, axis0, ratchet, basin, gcm,
allostatic, homeostatic, holodeck, rosetta) must NOT appear in any
computational KEY, the sim NAME, or a formula/predicate string. They may
appear ONLY inside an explicit quarantine field (legacy_project_labels,
legacy_paths, legacy_labels).

The banned jargon object is the project "engine-tier", which appears as a
COMPOUND identifier (terrain_engine, engine_consensus, engine_tier, engines,
...). The bare standalone key `engine` whose value names a numerical compute
BACKEND (jax / julia / pytorch) is STANDARD usage — it is the leg label of the
project's own three-engine architecture — and is NOT jargon. The gate allows
the exact whole key `engine` and the schema fragment `engine_leg` while still
flagging every compounded `engine` token; a compound that drops `engine` but
carries a different jargon word (terrain/axis/...) is caught by that word.

This gate does NOT and CANNOT judge whether the math is right, whether a
claim is admissible, or whether a tool is load-bearing. A packet can be
fully wrong and still pass this gate; a packet can be fully correct and
still fail it. It is the mechanical wall that holds an ambiguity an LLM
cannot reliably hold for itself: pure-math naming discipline.

Standard math/physics vocabulary is ALLOWED and is NEVER flagged
(hopf, weyl, bloch, pauli, clifford, spinor, ghz, w_state, monogamy, ckw,
hilbert, density, unitary, lindblad, cptp, trace, tensor, entropy,
mutual_information, negativity, partial_transpose, eigenvalue, curvature,
holonomy, connection, ...). When unsure, ban only the explicit owner-jargon
list above, never a standard math term.

Usage:
    python3 scripts/validate_math_only_packet.py <result.json | sim_dir>
    python3 scripts/validate_math_only_packet.py --selftest

Output: JSON {"ok": bool, "violations": [{"path", "token", "context"}]}.
Exit code: 0 if clean, 1 if any violation, 2 on usage error.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

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

# Owner-jargon / project nicknames that must not appear on the math surface.
# Whole-word (token) match, case-insensitive. `axis0`..`axisN` and similar are
# caught because trailing digits are peeled off each token before comparison.
BANNED_TOKENS = frozenset(
    {
        # owner-jargon
        "terrain",
        "engine",  # banned as the "engine-tier" jargon object; the bare
        # standalone backend-leg key `engine` (value jax/julia/pytorch) is
        # exempted in banned_hits via ENGINE_LEG_LABEL_EXEMPT.
        "axis",
        "stage",
        "runtime",
        "shell",
        "flux",
        # project nicknames
        "rpf",
        "retrocausal",
        "possibility_field",
        "axis0",  # redundant with digit-peel of "axis", kept explicit for clarity
        "ratchet",
        "basin",
        "gcm",
        "sector",
        "chirality",
        # owner MBTI nicknames / cognitive-function labels
        "se",
        "ne",
        "ni",
        "si",
        "te",
        "ti",
        "fe",
        "fi",
        "allostatic",
        "homeostatic",
        "holodeck",
        "rosetta",
    }
)

# Legacy coarse allow-list retained only as a non-authoritative prefilter. The
# authoritative registry is scripts/admitted_math_terms.py.
ALLOWED_MATH_TOKENS = frozenset(
    {
        "hopf",
        "weyl",
        "bloch",
        "pauli",
        "clifford",
        "spinor",
        "ghz",
        "w_state",
        "w",
        "monogamy",
        "ckw",
        "hilbert",
        "density",
        "unitary",
        "lindblad",
        "cptp",
        "trace",
        "tensor",
        "entropy",
        "mutual_information",
        "mutual",
        "information",
        "negativity",
        "partial_transpose",
        "partial",
        "transpose",
        "eigenvalue",
        "curvature",
        "holonomy",
        "connection",
    }
)

# Keys whose VALUES are treated as formula/predicate strings and scanned too.
# A value is only scanned when its key name signals a formula/expression.
FORMULA_KEY_HINT = re.compile(r"(formula|expr|equation|predicate|ansatz|symbolic)", re.IGNORECASE)

# Quarantine fields: any subtree under one of these keys is exempt entirely.
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


def tokenize(text: str) -> list[str]:
    """Split an identifier into lowercase word-tokens.

    Splits on any non-alphanumeric boundary, then peels trailing digits off
    each token so that 'axis0', 'axis3', 'stage2' reduce to the banned base
    ('axis', 'stage'). A pure-digit fragment yields no token.
    """
    raw = [t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t]
    tokens: list[str] = []
    for t in raw:
        tokens.append(t)
        stripped = t.rstrip("0123456789")
        if stripped and stripped != t:
            tokens.append(stripped)
    return tokens


# The bare backend-leg label. When the FULL identifier being scanned is exactly
# `engine` (the leg label whose value is jax/julia/pytorch) or names the
# `engine_leg` schema fragment, the `engine` token is standard usage, not the
# "engine-tier" jargon object, and is exempt. Any other identifier carrying
# `engine` (engines, engine_consensus, terrain_engine, engine_tier, ...) is NOT
# exempt and is flagged.
def _engine_token_exempt(full_identifier: str) -> bool:
    ident = full_identifier.strip().lower()
    if ident == "engine" or ident in ENVELOPE_INFRA_EXEMPT_KEYS or ident in EXACT_INFRA_KEYS:
        return True
    if ident == "engine_leg" or ident == "engine_leg_result":
        return True
    if ident.startswith("engine_leg_"):
        suffix = ident.removeprefix("engine_leg_")
        return suffix in {"result", "results"} or is_admitted_compound(suffix)
    return False


def _surface_violations(
    text: str,
    *,
    path: str,
    context: str,
    key_context: bool,
    include_undefined: bool = True,
) -> list[dict]:
    """Classify a JSON-surface identifier/string by the admitted-term registry.

    `include_undefined=False` suppresses the undefined-term class. KEYS are the
    math-naming surface and are scanned for both jargon and undefined coinage.
    String VALUES are scanned for JARGON only: a value may be a free-prose
    description ("Finite set S of single-qubit density matrices ...") whose
    ordinary English words are not undefined math coinages. This mirrors
    validate_name_math_correlation.py, which already suppresses undefined in
    values, so the two gates agree and the pure-math GOLD fixture passes both.
    """
    if _engine_token_exempt(text) or is_admitted_compound(text):
        return []

    kind_suffix = "json_key" if key_context else "json_value"
    violations: list[dict] = []
    seen: set[str] = set()
    for tok in split_identifier(text):
        if not tok or tok in seen:
            continue
        stripped = tok.rstrip("0123456789")
        report_tok = stripped if stripped and stripped != tok and is_jargon_token(stripped) else tok
        if tok == "engine" and not key_context:
            cls = "admitted"
        elif tok == "engine" and not _engine_token_exempt(text):
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
            {"path": path, "token": report_tok, "context": context, "kind": kind, "class": cls}
        )
    return violations


def banned_hits(text: str, *, value_context: bool = False) -> list[str]:
    """Return legacy/coarse jargon tokens present in `text`.

    This remains for directory-name checks and fast legacy jargon matching. It
    is no longer the authority for JSON-surface admission.
    """
    engine_exempt = _engine_token_exempt(text)
    hits: list[str] = []
    for tok in tokenize(text):
        if tok in ALLOWED_MATH_TOKENS or is_admitted_token(tok):
            continue
        if tok == "engine" and (engine_exempt or value_context):
            continue
        if tok == "runtime" and text.strip().lower() in RUNTIME_EXEMPT_KEYS:
            continue
        if tok in BANNED_TOKENS or is_jargon_token(tok):
            hits.append(tok)
    # de-dup, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def walk(node: object, path: str, violations: list[dict], *, is_name_context: bool = False) -> None:
    """Recursively scan keys and formula-string values for banned tokens.

    `path` is a JSON-pointer-ish breadcrumb for citing the exact location.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            child_path = f"{path}/{key_str}"

            # Quarantine: skip the whole subtree (keys and values) under it.
            if key_str in QUARANTINE_KEYS:
                continue

            # Scan the KEY itself under the registry allow-list.
            violations.extend(
                _surface_violations(
                    key_str, path=child_path, context=f"key:{key_str}", key_context=True
                )
            )

            # Scan scalar string VALUES too.  The top-level schema identifier is
            # structural metadata and may use the codex_ratchet.* namespace.
            if isinstance(value, str) and key_str != "schema":
                context_kind = "formula" if FORMULA_KEY_HINT.search(key_str) else "value"
                violations.extend(
                    _surface_violations(
                        value,
                        path=child_path,
                        context=f"{context_kind}:{value[:120]}",
                        key_context=False,
                        include_undefined=False,
                    )
                )

            if isinstance(value, (dict, list)):
                walk(value, child_path, violations)

    elif isinstance(node, list):
        for idx, item in enumerate(node):
            walk(item, f"{path}[{idx}]", violations)
    elif isinstance(node, str):
        violations.extend(
            _surface_violations(
                node,
                path=path,
                context=f"value:{node[:120]}",
                key_context=False,
                include_undefined=False,
            )
        )
    # Non-string scalars have no token surface to scan.


def scan_packet(result_path: Path) -> list[dict]:
    """Scan one result JSON file. Returns a list of violation dicts."""
    violations: list[dict] = []

    # The sim NAME is derived from the file name (and its parent sim dir).
    # Both are part of the executable surface, so both are scanned.
    name_str = result_path.stem
    for tok in banned_hits(name_str):
        violations.append(
            {"path": f"{result_path}::NAME", "token": tok, "context": f"result-name:{name_str}"}
        )
    if result_path.name == "spec.json":
        parent = result_path.parent.name
    elif result_path.parent.name == "results":
        parent = result_path.parent.parent.name
    else:
        parent = result_path.parent.name
    if parent and parent not in {"results", "sims", ""}:
        for tok in banned_hits(parent):
            violations.append(
                {"path": f"{result_path}::SIM_NAME", "token": tok, "context": f"sim-name:{parent}"}
            )

    try:
        data = json.loads(result_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        violations.append(
            {"path": str(result_path), "token": "<unreadable>", "context": f"load-error:{exc}"}
        )
        return violations

    # An explicit name field, if present, is also part of the surface.
    walk(data, str(result_path), violations)
    return violations


def collect_result_files(target: Path) -> list[Path]:
    """Resolve the input to result JSON files plus the sim spec.json, if any."""
    if target.is_file():
        return [target]
    if target.is_dir():
        files: list[Path] = []
        spec = target / "spec.json"
        if spec.is_file():
            files.append(spec)
        results_dir = target / "results"
        search_root = results_dir if results_dir.is_dir() else target
        files.extend(sorted(search_root.glob("*.json")))
        return files
    return []


def run(target: Path) -> dict:
    files = collect_result_files(target)
    if not files:
        return {"ok": False, "violations": [
            {"path": str(target), "token": "<no-input>", "context": "no result JSON found"}
        ]}
    violations: list[dict] = []
    for f in files:
        violations.extend(scan_packet(f))
    return {"ok": len(violations) == 0, "violations": violations}


# --------------------------------------------------------------------------- #
# Self-test                                                                    #
# --------------------------------------------------------------------------- #

def _selftest() -> int:
    import tempfile

    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # GOOD packet: pure-math surface; standard math tokens present; owner
        # jargon only inside a quarantine field.
        good = {
            "all_pass": True,
            "density_matrix_trace": 1.0,
            "weyl_chirality_holonomy": -1,
            "hopf_holonomy": {"connection_curvature": 0.5},
            "entropy_formula": "trace density matrix",
            "schema": "codex_ratchet.engine_leg_result.v1",
            "spinor_connection_curvature": 0.1875,
            "fe_lattice": True,
            "legacy_project_labels": {"axis": "axis0", "engine": "ratchet", "shell": "terrain"},
            "legacy_paths": ["system_v6/sims/gcm_basin_flux_engine_v0"],
        }
        good_path = tmp / "hopf_weyl_density_probe_v0_pytorch_results.json"
        good_path.write_text(json.dumps(good))
        res_good = run(good_path)
        if not res_good["ok"]:
            failures.append(f"GOOD packet flagged: {res_good['violations']}")

        envelope_infra = {
            "all_pass": True,
            "density_matrix_trace": 1.0,
            "entropy_formula": "trace density matrix",
            "engines": ["jax", "julia", "pytorch"],
            "engine_values": {"jax": 1.0, "julia": 1.0, "pytorch": 1.0},
            "engine_rows_match": True,
            "engine_consensus": {"all_equal": True},
            "canon_runtime": "julia",
            "foreign_runtime": "jax",
        }
        envelope_path = tmp / "density_trace_envelope_results.json"
        envelope_path.write_text(json.dumps(envelope_infra))
        res_envelope = run(envelope_path)
        if not res_envelope["ok"]:
            failures.append(f"envelope infra keys flagged: {res_envelope['violations']}")

        engine_jargon = {
            "terrain_engine": 1,
            "engine_tier": 2,
            "terrain_runtime": 3,
        }
        engine_jargon_path = tmp / "density_trace_engine_jargon_results.json"
        engine_jargon_path.write_text(json.dumps(engine_jargon))
        res_engine_jargon = run(engine_jargon_path)
        engine_jargon_tokens = {v["token"] for v in res_engine_jargon["violations"]}
        for expected in {"terrain", "engine", "runtime"}:
            if expected not in engine_jargon_tokens:
                failures.append(f"engine over-exemption missed expected token: {expected}")

        # BAD packet: owner jargon in a KEY, a nested list-embedded KEY, a
        # formula string, and the file/sim name.
        bad = {
            "all_pass": True,
            "terrain_count": 8,  # banned key
            "engine_stack": [
                {"runtime_flux": 1},  # banned keys nested in a list
            ],
            "channel_formula": "rho strip flux to previous shell",  # banned in formula
            "density_trace": 1.0,  # allowed, must NOT flag
            "axis3_predicate": {"basin_id": 2},  # axis-family + basin nickname
        }
        bad_dir = tmp / "rpf_retrocausal_basin_v0" / "results"
        bad_dir.mkdir(parents=True)
        bad_path = bad_dir / "rpf_retrocausal_basin_v0_jax_results.json"
        bad_path.write_text(json.dumps(bad))
        res_bad = run(bad_dir.parent)  # pass the sim dir
        if res_bad["ok"]:
            failures.append("BAD packet passed (expected violations)")
        tokens = {v["token"] for v in res_bad["violations"]}
        for expected in {"terrain", "engine", "runtime", "flux", "shell", "axis", "basin", "rpf", "retrocausal"}:
            if expected not in tokens:
                failures.append(f"BAD packet missed expected token: {expected}")
        # Standard-math token must NOT appear as a violation.
        if "density" in tokens or "trace" in tokens:
            failures.append("standard-math token wrongly flagged in BAD packet")

        # BAD spec: MBTI nicknames hidden in spec VALUES and KEYS outside the
        # legacy quarantine must be caught when scanning a sim directory.
        spec_bad = tmp / "clean_name_v0"
        (spec_bad / "results").mkdir(parents=True)
        (spec_bad / "spec.json").write_text(json.dumps({
            "orientation_tables": {
                "plus": {"radix_digit_0_word_rows": [["Se", "Ne", "Ni", "Si"]]},
            },
            "word_readout_components": {
                "Te": ["win", "loss"],
            },
            "legacy_project_labels": {"Se": "allowed here", "axis": "allowed here"},
        }))
        (spec_bad / "results" / "clean_name_v0_results.json").write_text(json.dumps({
            "schema": "codex_ratchet.agreement_result.v1",
            "engine": "jax",
            "engine_leg_result": True,
        }))
        res_spec_bad = run(spec_bad)
        if res_spec_bad["ok"]:
            failures.append("BAD spec with MBTI key/value jargon passed")
        spec_tokens = {v["token"] for v in res_spec_bad["violations"]}
        for expected in {"se", "ne", "ni", "si", "te"}:
            if expected not in spec_tokens:
                failures.append(f"BAD spec missed expected MBTI token: {expected}")
        if "engine" in spec_tokens:
            failures.append("engine prose/schema/backend exemption failed in spec scan")

        allow_list_good = tmp / "allow_list_good_results.json"
        allow_list_good.write_text(json.dumps({
            "density_matrix_trace": 1.0,
            "von_neumann_entropy": 0.0,
            "partial_transpose_negativity": 0.0,
            "weyl_chirality_holonomy": 1.0,
            "spinor_connection_curvature": 0.0,
            "schmidt_rank": 1,
            "fe_lattice": True,
        }))
        res_allow_list_good = run(allow_list_good)
        if not res_allow_list_good["ok"]:
            failures.append(f"allow-list standard math packet flagged: {res_allow_list_good['violations']}")

        undefined_bad = tmp / "undefined_bad_results.json"
        undefined_bad.write_text(json.dumps({"florble_undefined": 1}))
        res_undefined_bad = run(undefined_bad)
        if not any(v.get("kind") == "undefined_term_in_json_key" and v["token"] == "florble" for v in res_undefined_bad["violations"]):
            failures.append(f"undefined coinage not caught as undefined_term: {res_undefined_bad['violations']}")

        engine_leg_good = tmp / "engine_leg_good_results.json"
        engine_leg_good.write_text(json.dumps({"engine_leg_result": True}))
        if not run(engine_leg_good)["ok"]:
            failures.append("engine_leg_result should be exempt")
        engine_leg_bad = tmp / "engine_leg_bad_results.json"
        engine_leg_bad.write_text(json.dumps({"engine_leg_tier": True}))
        res_engine_leg_bad = run(engine_leg_bad)
        if res_engine_leg_bad["ok"] or not any(v["token"] == "tier" for v in res_engine_leg_bad["violations"]):
            failures.append(f"engine_leg_tier should be flagged: {res_engine_leg_bad['violations']}")

    if failures:
        print("SELFTEST FAILED")
        for f in failures:
            print("  -", f)
        return 1
    print("SELFTEST PASSED")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Math-only admission gate (language gate, not correctness).")
    p.add_argument("target", nargs="?", help="result-JSON path OR a sim dir (scans results/*.json).")
    p.add_argument("--selftest", action="store_true", help="run the built-in self-test and exit.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return _selftest()
    if not args.target:
        print(json.dumps({"ok": False, "violations": [
            {"path": "<none>", "token": "<no-input>", "context": "provide a result JSON or sim dir"}
        ]}))
        return 2
    result = run(Path(args.target))
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
