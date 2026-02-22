#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List


REQUIRED_RULE_FAMILIES = {
    "MESSAGE_DISCIPLINE",
    "SCHEMA_CHECK",
    "LEXEME_FENCE",
    "UNDEFINED_TERM_FENCE",
    "DERIVED_ONLY_FENCE",
    "FORMULA_GLYPH_FENCE",
    "PROBE_PRESSURE",
    "EVIDENCE_INGEST",
    "DEPENDENCY_FORWARD_REF",
    "NEAR_DUPLICATE_PARK",
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compute_fixture_pack_hash(pack_root: Path) -> str:
    hashable_files: List[Path] = []
    expected = pack_root / "expected_outcomes.json"
    if expected.exists():
        hashable_files.append(expected)
    fixtures_dir = pack_root / "fixtures"
    if fixtures_dir.exists():
        hashable_files.extend(sorted([p for p in fixtures_dir.rglob("*") if p.is_file()]))

    rows: List[str] = []
    for p in sorted(hashable_files, key=lambda x: str(x.relative_to(pack_root))):
        rel = str(p.relative_to(pack_root))
        sha = _sha256_bytes(p.read_bytes())
        rows.append(f"{rel}:{sha}")
    payload = "\n".join(rows).encode("ascii")
    return _sha256_bytes(payload)


def _normalize_tags(tags: List[str]) -> List[str]:
    return sorted(set(tags))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic conformance fixture comparison.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-pack", default="system_v3/conformance/fixtures_v1")
    parser.add_argument("--bootpack-hash", required=True)
    parser.add_argument("--observed-results", default="")
    parser.add_argument("--use-expected-as-observed", action="store_true")
    parser.add_argument("--write-manifest-hash", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    pack_root = Path(args.fixture_pack).resolve()

    manifest_path = pack_root / "manifest.json"
    expected_path = pack_root / "expected_outcomes.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing manifest: {manifest_path}")
    if not expected_path.exists():
        raise FileNotFoundError(f"missing expected outcomes: {expected_path}")

    manifest = _read_json(manifest_path)
    expected_obj = _read_json(expected_path)
    expected_rows = expected_obj.get("expected_outcomes", [])
    if not isinstance(expected_rows, list):
        raise ValueError("expected_outcomes must be a list")

    fixture_pack_hash = _compute_fixture_pack_hash(pack_root)
    if args.write_manifest_hash:
        manifest["fixture_pack_hash"] = fixture_pack_hash
        manifest["fixture_count"] = len(expected_rows)
        _write_json(manifest_path, manifest)

    observed_index: Dict[str, dict] = {}
    if args.use_expected_as_observed:
        for row in expected_rows:
            observed_index[row["fixture_id"]] = {
                "observed_status": row["expected_status"],
                "observed_tags": list(row.get("expected_tags", [])),
                "diagnostics": [],
            }
    elif args.observed_results:
        observed_obj = _read_json(Path(args.observed_results).resolve())
        for row in observed_obj.get("results", []):
            observed_index[row["fixture_id"]] = row

    seen_ids = set()
    results: List[dict] = []
    covered_rule_families = set()

    for row in sorted(expected_rows, key=lambda x: x["fixture_id"]):
        fixture_id = row["fixture_id"]
        if fixture_id in seen_ids:
            raise ValueError(f"duplicate fixture_id in expected_outcomes: {fixture_id}")
        seen_ids.add(fixture_id)

        artifact_path = pack_root / row["artifact_path"]
        if not artifact_path.exists():
            raise FileNotFoundError(f"fixture artifact missing: {artifact_path}")

        expected_status = row["expected_status"]
        expected_tags = _normalize_tags(row.get("expected_tags", []))
        rule_families = row.get("rule_families", [])
        for fam in rule_families:
            covered_rule_families.add(fam)

        observed = observed_index.get(fixture_id, {})
        observed_status = observed.get("observed_status", "MISSING")
        observed_tags = _normalize_tags(observed.get("observed_tags", []))
        diagnostics = list(observed.get("diagnostics", []))

        mismatch_reasons: List[str] = []
        if observed_status != expected_status:
            mismatch_reasons.append(
                f"status_mismatch expected={expected_status} observed={observed_status}"
            )
        if observed_tags != expected_tags:
            mismatch_reasons.append(
                f"tag_mismatch expected={expected_tags} observed={observed_tags}"
            )

        match = len(mismatch_reasons) == 0
        results.append(
            {
                "fixture_id": fixture_id,
                "expected_status": expected_status,
                "observed_status": observed_status,
                "expected_tags": expected_tags,
                "observed_tags": observed_tags,
                "match": match,
                "diagnostics": sorted(diagnostics + mismatch_reasons),
            }
        )

    missing_rule_families = sorted(REQUIRED_RULE_FAMILIES - covered_rule_families)
    mismatch_count = sum(1 for r in results if not r["match"])
    status = "PASS" if mismatch_count == 0 and not missing_rule_families else "FAIL"

    report = {
        "schema": "CONFORMANCE_RESULTS_v1",
        "run_id": run_dir.name,
        "bootpack_hash": args.bootpack_hash,
        "fixture_pack_hash": fixture_pack_hash,
        "fixture_pack_version": manifest.get("fixture_pack_version", "UNKNOWN"),
        "declared_fixture_pack_hash": manifest.get("fixture_pack_hash", "UNKNOWN"),
        "missing_rule_families": missing_rule_families,
        "totals": {
            "fixture_count": len(results),
            "pass_count": sum(1 for r in results if r["match"]),
            "fail_count": sum(1 for r in results if not r["match"]),
            "mismatch_count": mismatch_count,
        },
        "status": status,
        "results": results,
    }

    out_path = run_dir / "reports" / "conformance_results.json"
    _write_json(out_path, report)

    conformance_summary_path = run_dir / "reports" / "conformance_report.json"
    summary = {
        "schema": "CONFORMANCE_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "fixture_suite_refs": [str(expected_path), str(pack_root / "fixtures")],
        "passed": [r["fixture_id"] for r in results if r["match"]],
        "failures": [r["fixture_id"] for r in results if not r["match"]],
    }
    _write_json(conformance_summary_path, summary)

    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
