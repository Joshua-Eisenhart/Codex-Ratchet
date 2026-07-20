#!/usr/bin/env python3
"""
fuel_adequacy_gate.py -- deterministic FUEL-ADEQUACY gate (CODE, never LLM judgment).

This is "Principle Zero": it must pass BEFORE any ratchet (pairwise MSS)
comparison runs. It is fuel INFRASTRUCTURE, not the ratchet itself -- it never
ranks, admits, or compares candidates. Computing relative MSS / presumption /
any tooth is the ratchet's job (code run on executable finite structures),
never this gate. See README.md and
system_v8/candidates/RANKING_VOID_llm_did_ratchets_job.md for the incident
that makes this boundary explicit.

Usage:
    python3 fuel_adequacy_gate.py [--pool-dir DIR] [--manifest FILE]
                                   [--schema FILE] [--write-result FILE]
                                   [--min-diversity-floor N] [--file-pattern GLOB]

Exit codes (the only interface -- do not parse prose):
    0 = ADEQUATE               (nothing printed to stdout)
    1 = HOLD_INSUFFICIENT_FUEL (machine-readable JSON reasons printed to stdout)

Checks (all run every time; every failing check is reported, not just the first):
  (a) required_variation_slots  -- the pool must fill all six fuel-pool roles:
      incumbent, minimal_rival, structural_rival, order_nesting_rival,
      countermodel, ablation_control. Reports which are EMPTY.
  (b) real_diversity             -- at least --min-diversity-floor distinct
      model families (not prompts of one model) AND that many distinct
      generation paths AND that many effective candidates. Candidates that
      share model family AND carrier AND nesting_order collapse to one
      effective candidate ("a hundred near-identical proposals are one
      effective candidate"). Reports effective-candidate count vs raw count.
  (c) provenance_present          -- every candidate needs model, version,
      prompt_lineage, source_corpus, tools, saw_preferred_answer (a real
      bool), inherited_assumptions, code_lineage. A present-but-declared-
      "unknown" value is flagged as thin, not silently accepted as adequate.
  (d) executable_enough           -- grep each candidate FILE (not the
      manifest) for a probe/test section and a defeat-condition/witness
      section. Bare prose with neither is flagged.

Exit 0 only if (a), (b), (c), (d) all pass. This is a GENERAL validator: pool
membership is discovered by a NAMING CONVENTION (--file-pattern, default
'candidate_*.md'), never by hardcoding specific candidate filenames, and
every threshold is a named, CLI-overridable constant, never an inline magic
number keyed to one pool.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_DIR = Path(__file__).resolve().parent

REQUIRED_SLOTS = [
    "incumbent",
    "minimal_rival",
    "structural_rival",
    "order_nesting_rival",
    "countermodel",
    "ablation_control",
]

SLOT_DESCRIPTIONS = {
    "incumbent": "the candidate this round is defending or extending",
    "minimal_rival": "removes a presumed layer or assumption from the incumbent",
    "structural_rival": "a genuinely different carrier family, not a relabel",
    "order_nesting_rival": "same ingredients, different order / bracket / containment",
    "countermodel": "preserves the observed result WITHOUT the claimed mechanism",
    "ablation_control": "deletion / reversal / scramble / flatten control",
}

# Default floor for check (b). Rationale (documented, not reverse-engineered
# from any one pool): with 6 required slots, fewer than 4 distinct model
# families forces most slots to double up on the same generative source,
# which defeats the point of having independent slots. 4 is a conservative
# floor, not a proven-optimal number -- raise or lower it per pool with
# --min-diversity-floor.
DEFAULT_MIN_DIVERSITY_FLOOR = 4

DEFAULT_FILE_PATTERN = "candidate_*.md"

# A provenance value that is technically present and correctly typed but
# says, in effect, "we don't actually know this" -- flagged as thin rather
# than silently accepted, so unknown provenance cannot pass as adequate
# provenance just because a placeholder string was supplied.
THIN_VALUE_PATTERN = re.compile(
    r"^\s*(unknown|not[\s_-]*tracked|untracked|n/?a\b|none(?:\s+tracked)?|"
    r"not[\s_-]*captured|not[\s_-]*logged)\b",
    re.IGNORECASE,
)

# Check (d): general, content-based patterns -- never a filename or
# candidate-name literal. Any markdown file, from any pool, is checked the
# same way.
PROBE_TEST_PATTERNS = [
    re.compile(r"\bprobe\s*/\s*distinguishability\s+test\b", re.IGNORECASE),
    re.compile(r"\bdistinguishability\s+test\b", re.IGNORECASE),
    re.compile(r"#+\s*.*\bprobe\b", re.IGNORECASE),
    re.compile(r"\bprobe\b[^\n]{0,80}\btest\b", re.IGNORECASE),
    re.compile(r"\btest\b[^\n]{0,80}\bprobe\b", re.IGNORECASE),
]
WITNESS_PATTERNS = [
    re.compile(r"\bcan-fail\b", re.IGNORECASE),
    re.compile(r"\bdefeat[\s_-]*condition", re.IGNORECASE),
    re.compile(r"\bwitness\b", re.IGNORECASE),
    re.compile(r"\bwould\s+flip\b", re.IGNORECASE),
    re.compile(r"\bfalsifi\w*\b", re.IGNORECASE),
    re.compile(r"\bloses\s+its\b", re.IGNORECASE),
    re.compile(r"\bwins?\s+if\b", re.IGNORECASE),
]


def is_thin(value):
    """A present string that effectively says 'unknown'."""
    if not isinstance(value, str):
        return False
    return bool(THIN_VALUE_PATTERN.match(value.strip()))


def type_matches(value, declared_type):
    """Check value against a JSON-Schema 'type' (string or list-of-strings),
    read directly from candidate_package_schema.json -- no duplicated,
    hand-maintained type table that could drift from the schema file."""
    if declared_type is None:
        return True
    types = declared_type if isinstance(declared_type, list) else [declared_type]
    for t in types:
        if t == "string" and isinstance(value, str):
            return True
        if t == "null" and value is None:
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "object" and isinstance(value, dict):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
    return False


def has_probe_test_section(text):
    return any(p.search(text) for p in PROBE_TEST_PATTERNS)


def has_witness_section(text):
    return any(p.search(text) for p in WITNESS_PATTERNS)


# ---------------------------------------------------------------------------
# Discovery: pool membership is a NAMING CONVENTION (glob), never a
# hardcoded list of filenames. The manifest is consulted per discovered
# file, not treated as the authority on which files exist -- a thin
# manifest that simply omits an inconvenient candidate cannot buy that
# candidate a pass; it shows up as a provenance gap instead.
# ---------------------------------------------------------------------------
def discover_candidate_files(pool_dir: Path, file_pattern: str):
    if not pool_dir.exists():
        return []
    return sorted(p.name for p in pool_dir.glob(file_pattern) if p.is_file())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_entries(candidate_files, manifest_candidates):
    """One entry per discovered file: (filename, has_manifest, variation_slots, package)."""
    entries = []
    for filename in candidate_files:
        man = manifest_candidates.get(filename)
        if man is None:
            entries.append({"file": filename, "has_manifest": False, "variation_slots": [], "package": None})
        else:
            entries.append({
                "file": filename,
                "has_manifest": True,
                "variation_slots": man.get("variation_slots", []) or [],
                "package": man.get("package"),
            })
    return entries


# ---------------------------------------------------------------------------
# (a) required variation slots
# ---------------------------------------------------------------------------
def check_a_slots(entries):
    coverage = {slot: [] for slot in REQUIRED_SLOTS}
    unrecognized = []
    for e in entries:
        for slot in e["variation_slots"]:
            if slot in coverage:
                coverage[slot].append(e["file"])
            else:
                unrecognized.append({"file": e["file"], "slot": slot})
    missing = [slot for slot in REQUIRED_SLOTS if not coverage[slot]]
    return {
        "pass": len(missing) == 0,
        "required_slots": REQUIRED_SLOTS,
        "slot_descriptions": SLOT_DESCRIPTIONS,
        "slot_coverage": coverage,
        "missing_slots": missing,
        "unrecognized_slot_labels": unrecognized,
    }


# ---------------------------------------------------------------------------
# (b) real diversity
# ---------------------------------------------------------------------------
def check_b_diversity(entries, min_floor, raw_count):
    families = []
    generation_keys = []
    bucket_keys = []
    per_candidate = []

    for e in entries:
        pkg = e["package"]
        if not e["has_manifest"] or not isinstance(pkg, dict):
            bucket_keys.append(("__no_manifest__", e["file"]))  # can never collapse with anything
            per_candidate.append({
                "file": e["file"], "model": None, "carrier": None, "nesting_order": None,
                "note": "no manifest entry -- treated as its own singleton effective candidate",
            })
            continue

        prov = pkg.get("provenance", {}) if isinstance(pkg.get("provenance"), dict) else {}
        model = prov.get("model")
        carrier = pkg.get("carrier")
        order = pkg.get("nesting_order")
        bucket_keys.append((model, carrier, order))
        per_candidate.append({"file": e["file"], "model": model, "carrier": carrier, "nesting_order": order})

        if isinstance(model, str) and model.strip() and not is_thin(model):
            families.append(model.strip().lower())

        prompt_lineage = prov.get("prompt_lineage")
        code_lineage = prov.get("code_lineage")
        if isinstance(prompt_lineage, str) and prompt_lineage.strip() and not is_thin(prompt_lineage):
            key = (prompt_lineage.strip().lower(), (code_lineage or "").strip().lower() if isinstance(code_lineage, str) else None)
            generation_keys.append(key)

    distinct_families = sorted(set(families))
    distinct_generation_paths = len(set(generation_keys))

    bucket_map = {}
    for key, e in zip(bucket_keys, entries):
        bucket_map.setdefault(key, []).append(e["file"])
    effective_count = len(bucket_map)

    families_pass = len(distinct_families) >= min_floor
    generation_pass = distinct_generation_paths >= min_floor
    effective_pass = effective_count >= min_floor

    return {
        "pass": families_pass and generation_pass and effective_pass,
        "min_diversity_floor": min_floor,
        "distinct_model_families": distinct_families,
        "distinct_model_family_count": len(distinct_families),
        "distinct_model_families_pass": families_pass,
        "distinct_generation_paths": distinct_generation_paths,
        "distinct_generation_paths_pass": generation_pass,
        "raw_candidate_count": raw_count,
        "effective_candidate_count": effective_count,
        "effective_candidate_count_pass": effective_pass,
        "effective_vs_raw": [effective_count, raw_count],
        "effective_buckets": {
            (" | ".join(str(part) for part in key)): files
            for key, files in bucket_map.items()
        },
        "per_candidate": per_candidate,
    }


# ---------------------------------------------------------------------------
# (c) provenance present -- required-field list comes from the schema file
# itself (single source of truth), not a hand-duplicated constant.
# ---------------------------------------------------------------------------
def check_c_provenance(entries, schema):
    provenance_schema = schema.get("properties", {}).get("provenance", {})
    required_fields = provenance_schema.get("required", [])
    field_types = {k: v.get("type") for k, v in provenance_schema.get("properties", {}).items()}

    gaps = []
    for e in entries:
        filename = e["file"]
        if not e["has_manifest"] or not isinstance(e["package"], dict):
            gaps.append({"file": filename, "field": None, "code": "no_manifest_entry",
                         "detail": "no provenance recorded for this candidate at all"})
            continue
        prov = e["package"].get("provenance")
        if not isinstance(prov, dict):
            gaps.append({"file": filename, "field": "provenance", "code": "provenance_block_missing",
                         "detail": "candidate package has no 'provenance' object"})
            continue
        for field in required_fields:
            if field not in prov:
                gaps.append({"file": filename, "field": field, "code": "missing_field",
                             "detail": f"required provenance field '{field}' is absent"})
                continue
            value = prov[field]
            declared_type = field_types.get(field)
            if not type_matches(value, declared_type):
                gaps.append({"file": filename, "field": field, "code": "type_mismatch",
                             "detail": f"'{field}' = {value!r} does not match schema type {declared_type!r}"})
                continue
            if isinstance(value, str) and is_thin(value):
                gaps.append({"file": filename, "field": field, "code": "thin_value",
                             "detail": f"'{field}' is present but declared unknown/thin: {value!r}"})

    return {
        "pass": len(gaps) == 0,
        "required_provenance_fields": required_fields,
        "provenance_gaps": gaps,
    }


# ---------------------------------------------------------------------------
# (d) executable-enough -- grep the actual candidate FILES, independent of
# whatever the manifest claims.
# ---------------------------------------------------------------------------
def check_d_executable(pool_dir, candidate_files):
    nonexecutable = []
    for filename in candidate_files:
        path = pool_dir / filename
        if not path.exists():
            nonexecutable.append({"file": filename, "missing": ["file_not_found"]})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = []
        if not has_probe_test_section(text):
            missing.append("probe_test_section")
        if not has_witness_section(text):
            missing.append("defeat_condition_witness_section")
        if missing:
            nonexecutable.append({"file": filename, "missing": missing})
    return {
        "pass": len(nonexecutable) == 0,
        "nonexecutable": nonexecutable,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def evaluate(pool_dir: Path, manifest_path: Path, schema_path: Path,
             min_diversity_floor: int, file_pattern: str):
    warnings = []

    try:
        schema = load_json(schema_path)
    except Exception as e:
        return None, {"error": "unreadable_schema", "path": str(schema_path), "detail": str(e)}

    manifest_candidates = {}
    manifest_meta = {}
    if manifest_path.exists():
        try:
            manifest = load_json(manifest_path)
            manifest_candidates = manifest.get("candidates", {}) or {}
            manifest_meta = {k: v for k, v in manifest.items() if k != "candidates"}
        except Exception as e:
            return None, {"error": "unreadable_manifest", "path": str(manifest_path), "detail": str(e)}
    else:
        warnings.append(f"manifest file not found at {manifest_path} -- every discovered "
                         f"candidate is treated as having no provenance entry")

    candidate_files = discover_candidate_files(pool_dir, file_pattern)
    if not candidate_files:
        warnings.append(f"no files matching '{file_pattern}' found under {pool_dir}")

    orphan_manifest_entries = sorted(set(manifest_candidates) - set(candidate_files))
    if orphan_manifest_entries:
        warnings.append(f"manifest references files not present in pool_dir (ignored for "
                         f"scoring, pool membership comes from the directory): {orphan_manifest_entries}")

    entries = build_entries(candidate_files, manifest_candidates)
    raw_count = len(candidate_files)

    a = check_a_slots(entries)
    b = check_b_diversity(entries, min_diversity_floor, raw_count)
    c = check_c_provenance(entries, schema)
    d = check_d_executable(pool_dir, candidate_files)

    overall_pass = raw_count > 0 and a["pass"] and b["pass"] and c["pass"] and d["pass"]
    if raw_count == 0:
        warnings.append("empty pool -- HOLD forced regardless of sub-check results")

    result = {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pool_dir": str(pool_dir),
        "manifest_path": str(manifest_path),
        "schema_path": str(schema_path),
        "file_pattern": file_pattern,
        "min_diversity_floor": min_diversity_floor,
        "raw_candidate_count": raw_count,
        "candidate_files": candidate_files,
        "manifest_meta": manifest_meta,
        "warnings": warnings,
        "checks": {
            "a_required_variation_slots": a,
            "b_real_diversity": b,
            "c_provenance_present": c,
            "d_executable_enough": d,
        },
        "verdict": "ADEQUATE" if overall_pass else "HOLD_INSUFFICIENT_FUEL",
        # top-level mirrors matching the owner-specified stdout-on-fail shape exactly
        "missing_slots": a["missing_slots"],
        "effective_vs_raw": b["effective_vs_raw"],
        "provenance_gaps": c["provenance_gaps"],
        "nonexecutable": d["nonexecutable"],
    }
    return result, None


def main():
    parser = argparse.ArgumentParser(description="Deterministic fuel-adequacy gate (Principle Zero).")
    parser.add_argument("--pool-dir", type=Path, default=REPO_ROOT / "system_v8" / "candidates",
                         help="Candidate-pool directory (default: system_v8/candidates/)")
    parser.add_argument("--manifest", type=Path, default=GATE_DIR / "manifests" / "current_pool_provenance_manifest.json",
                         help="Provenance manifest JSON")
    parser.add_argument("--schema", type=Path, default=GATE_DIR / "candidate_package_schema.json",
                         help="candidate_package_schema.json path")
    parser.add_argument("--write-result", type=Path, default=None,
                         help="Always write the full diagnostic verdict JSON here, pass or fail")
    parser.add_argument("--min-diversity-floor", type=int, default=DEFAULT_MIN_DIVERSITY_FLOOR,
                         help=f"Minimum distinct model families / generation paths / effective "
                              f"candidates for check (b) (default {DEFAULT_MIN_DIVERSITY_FLOOR})")
    parser.add_argument("--file-pattern", type=str, default=DEFAULT_FILE_PATTERN,
                         help=f"Glob for pool membership, a naming convention not a file list "
                              f"(default '{DEFAULT_FILE_PATTERN}')")
    args = parser.parse_args()

    result, error = evaluate(args.pool_dir, args.manifest, args.schema,
                              args.min_diversity_floor, args.file_pattern)

    if error is not None:
        print(json.dumps(error, indent=2))
        sys.exit(1)

    if args.write_result is not None:
        args.write_result.parent.mkdir(parents=True, exist_ok=True)
        args.write_result.write_text(json.dumps(result, indent=2))

    if result["verdict"] == "ADEQUATE":
        sys.exit(0)
    else:
        stdout_payload = {
            "verdict": result["verdict"],
            "missing_slots": result["missing_slots"],
            "effective_vs_raw": result["effective_vs_raw"],
            "provenance_gaps": result["provenance_gaps"],
            "nonexecutable": result["nonexecutable"],
        }
        print(json.dumps(stdout_payload, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
