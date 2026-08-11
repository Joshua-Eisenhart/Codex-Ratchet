#!/usr/bin/env python3
"""Strict, source-addressed artifact consumer for ConstraintBox candidates.

This is a deliberately narrower successor to Claude Code's schema-scanning
consumer.  It verifies a *sealed artifact scope*, not a scientific result:

* a controller supplies one receipt and its expected SHA-256 as the trust
  anchor;
* only explicit artifact-manifest fields are eligible to bind files;
* every bound path must resolve beneath ``--artifact-root``;
* the consumer's output must stay outside that scope; and
* undeclared files fail by default.

The receipt can contain producer ``passed`` values, but this program never
uses them for its verdict.  Its only positive verdict is byte-level integrity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from .ledger import HashChainLedger


HEX64 = re.compile(r"^[0-9a-f]{64}$")
IGNORE_DIRS = {"__pycache__", ".git", "mplconfig", "numba_cache"}
ARTIFACT_MAP_KEYS = {
    "artifacts",
    "artifact_hashes",
    "file_hashes",
    "input_hashes",
    "output_hashes",
    "source_hashes",
}
PATH_KEYS = ("path", "file", "relative", "name")
DIGEST_KEYS = ("sha256", "digest", "hash")
VERDICT_KEYS = {"passed", "all_pass", "all_consumer_checks_pass"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_beneath(root: Path, supplied: str) -> tuple[Path | None, str | None]:
    """Resolve a declared file without allowing absolute or ``..`` escapes."""
    raw = Path(supplied)
    if raw.is_absolute():
        return None, "absolute path"
    resolved = (root / raw).resolve()
    try:
        return resolved, str(resolved.relative_to(root))
    except ValueError:
        return None, "path escapes artifact root"


def record_declaration(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, dict):
        return None
    name = next((value.get(key) for key in PATH_KEYS if isinstance(value.get(key), str)), None)
    digest = next((value.get(key) for key in DIGEST_KEYS if isinstance(value.get(key), str)), None)
    if name and digest and HEX64.fullmatch(digest):
        return name, digest
    return None


def collect_entries(value: Any, scope: str, out: list[dict[str, str]]) -> None:
    """Collect only entries inside explicit artifact-manifest fields."""
    record = record_declaration(value)
    if record:
        out.append({"declared": record[0], "sha256": record[1], "scope": scope})
        return
    if isinstance(value, dict):
        for name, digest in value.items():
            if isinstance(digest, str) and HEX64.fullmatch(digest):
                out.append({"declared": str(name), "sha256": digest, "scope": scope})
            elif isinstance(digest, (dict, list)):
                collect_entries(digest, scope, out)
    elif isinstance(value, list):
        for item in value:
            collect_entries(item, scope, out)


def collect_manifest_entries(node: Any, out: list[dict[str, str]], scope: str = "$") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            child_scope = f"{scope}.{key}"
            if key.lower() in ARTIFACT_MAP_KEYS:
                collect_entries(value, child_scope, out)
            if isinstance(value, (dict, list)):
                collect_manifest_entries(value, out, child_scope)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            collect_manifest_entries(value, out, f"{scope}[{index}]")


def collect_producer_verdicts(node: Any, out: list[str], scope: str = "$") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            child_scope = f"{scope}.{key}"
            if key.lower() in VERDICT_KEYS and isinstance(value, bool):
                out.append(child_scope)
            collect_producer_verdicts(value, out, child_scope)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            collect_producer_verdicts(value, out, f"{scope}[{index}]")


def files_beneath(root: Path) -> tuple[set[str], list[str]]:
    found: set[str] = set()
    escaping_links: list[str] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in IGNORE_DIRS]
        for filename in filenames:
            lexical_path = Path(directory) / filename
            lexical_rel = str(lexical_path.relative_to(root))
            path = lexical_path.resolve()
            try:
                path.relative_to(root)
                found.add(lexical_rel)
            except ValueError:
                # An escaping link is neither an artifact nor safe control data.
                escaping_links.append(lexical_rel)
    return found, escaping_links


def verify_receipt_ledger(receipt: object, root: Path) -> tuple[bool, str, set[str]]:
    """Verify a retained receipt ledger with the canonical chain implementation."""
    if not isinstance(receipt, dict) or not isinstance(receipt.get("ledger"), dict):
        return True, "no ledger declaration", set()
    ledger = receipt["ledger"]
    path_text = ledger.get("path")
    head_text = ledger.get("head_path")
    if not isinstance(path_text, str) or not isinstance(head_text, str):
        return False, "ledger binding is incomplete", set()
    path = Path(path_text).resolve()
    head = Path(head_text).resolve()
    try:
        path.relative_to(root)
        head.relative_to(root)
    except ValueError:
        return False, "ledger binding escapes artifact root", set()
    valid, reason = HashChainLedger(path, head).verify()
    retained = ledger.get("retained_head_sha256")
    if valid and isinstance(retained, str) and head.read_text(encoding="ascii").strip() != retained:
        return False, "retained ledger head differs from receipt", set()
    return valid, reason, {str(path.relative_to(root)), str(head.relative_to(root))}


def write_output(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def configuration_error(message: str) -> int:
    print(f"CONFIGURATION ERROR: {message}", file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--allow-bare-declarations",
        action="store_true",
        help="compatibility only: permit an unqualified name if unique",
    )
    args = parser.parse_args()

    root = args.artifact_root.resolve()
    receipt_path = args.receipt.resolve()
    output_path = args.output.resolve()
    expected = args.expected_receipt_sha256.lower()
    if not root.is_dir():
        return configuration_error(f"artifact root does not exist: {root}")
    if not receipt_path.is_file():
        return configuration_error(f"receipt does not exist: {receipt_path}")
    if not HEX64.fullmatch(expected):
        return configuration_error("--expected-receipt-sha256 must be a 64-character lowercase SHA-256")
    try:
        output_path.relative_to(root)
    except ValueError:
        pass
    else:
        return configuration_error("--output must be outside --artifact-root")
    if output_path == receipt_path:
        return configuration_error("--output must not overwrite --receipt")

    actual_receipt_sha = sha256(receipt_path)
    try:
        receipt = json.loads(receipt_path.read_text())
        unreadable: str | None = None
    except Exception as exc:
        receipt = {}
        unreadable = f"unreadable receipt: {exc}"

    declarations: list[dict[str, str]] = []
    collect_manifest_entries(receipt, declarations)
    ledger_valid, ledger_reason, ledger_files = verify_receipt_ledger(receipt, root)
    producer_verdicts: list[str] = []
    collect_producer_verdicts(receipt, producer_verdicts)

    matched: list[dict[str, str]] = []
    mismatch: list[dict[str, str]] = []
    absent: list[dict[str, str]] = []
    escaped: list[dict[str, str]] = []
    bare_rejected: list[dict[str, str]] = []
    ambiguous: list[dict[str, Any]] = []
    seen: set[str] = set()
    conflicting: list[dict[str, str]] = []
    declared_by_path: dict[str, str] = {}

    for entry in declarations:
        name, digest = entry["declared"], entry["sha256"]
        previous = declared_by_path.get(name)
        if previous and previous != digest:
            conflicting.append({"declared": name, "first": previous, "second": digest})
            continue
        declared_by_path[name] = digest

        has_separator = "/" in name or "\\" in name
        if not has_separator and not args.allow_bare_declarations:
            bare_rejected.append({"declared": name, "sha256": digest})
            continue
        if has_separator:
            candidate, rel_or_error = resolve_beneath(root, name)
            if candidate is None:
                escaped.append({"declared": name, "reason": str(rel_or_error)})
                continue
        else:
            candidates = []
            for path in root.rglob(name):
                if not path.is_file():
                    continue
                resolved = path.resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    continue
                candidates.append(resolved)
            candidates = sorted(set(candidates))
            if len(candidates) == 0:
                absent.append({"declared": name, "sha256": digest})
                continue
            if len(candidates) > 1:
                ambiguous.append({"declared": name, "candidates": [str(path.relative_to(root)) for path in candidates[:8]]})
                continue
            candidate = candidates[0]
            rel_or_error = str(candidate.relative_to(root))

        assert candidate is not None
        assert rel_or_error is not None
        if not candidate.is_file():
            absent.append({"declared": name, "sha256": digest})
            continue
        actual = sha256(candidate)
        seen.add(str(rel_or_error))
        if actual == digest:
            matched.append({"path": str(rel_or_error), "sha256": digest})
        else:
            mismatch.append({"path": str(rel_or_error), "declared": digest, "actual": actual})

    control_files: set[str] = set()
    try:
        control_files.add(str(receipt_path.relative_to(root)))
    except ValueError:
        pass
    all_files, escaping_links = files_beneath(root)
    undeclared = sorted(all_files - seen - control_files - ledger_files)

    defects: list[str] = []
    if unreadable:
        defects.append(unreadable)
    if actual_receipt_sha != expected:
        defects.append("receipt SHA-256 does not match the controller-supplied trust anchor")
    if not declarations:
        defects.append("no declarations found in supported artifact-manifest fields")
    if escaped:
        defects.append(f"declared paths outside artifact root: {len(escaped)}")
    if bare_rejected:
        defects.append(f"bare artifact declarations rejected: {len(bare_rejected)}")
    if ambiguous:
        defects.append(f"ambiguous bare artifact declarations: {len(ambiguous)}")
    if conflicting:
        defects.append(f"conflicting declarations for one path: {len(conflicting)}")
    if absent:
        defects.append(f"declared-but-absent: {len(absent)}")
    if mismatch:
        defects.append(f"hash mismatch on declared artifacts: {len(mismatch)}")
    if escaping_links:
        defects.append(f"artifact root contains paths that escape through symlinks: {len(escaping_links)}")
    if undeclared:
        defects.append(f"present-but-undeclared: {len(undeclared)}")
    if not ledger_valid:
        defects.append(f"invalid-ledger-chain: {ledger_reason}")

    declared_artifacts_intact = not any(
        [
            unreadable,
            actual_receipt_sha != expected,
            not declarations,
            escaped,
            bare_rejected,
            ambiguous,
            conflicting,
            absent,
            mismatch,
        ]
    )
    sealed_scope_complete = not undeclared and not escaping_links

    result: dict[str, Any] = {
        "schema": "cb.strict-recomputing-consumer.v2",
        "artifact_root": str(root),
        "receipt": str(receipt_path),
        "expected_receipt_sha256": expected,
        "actual_receipt_sha256": actual_receipt_sha,
        "receipt_hash_match": actual_receipt_sha == expected,
        "supported_manifest_fields": sorted(ARTIFACT_MAP_KEYS),
        "declared_artifact_count": len(declarations),
        "recomputed_match_count": len(matched),
        "recomputed_mismatch_count": len(mismatch),
        "recomputed_mismatch": mismatch[:20],
        "declared_absent_count": len(absent),
        "declared_absent": absent[:20],
        "declared_path_escape_count": len(escaped),
        "declared_path_escapes": escaped[:20],
        "bare_declarations_rejected_count": len(bare_rejected),
        "ambiguous_declarations": ambiguous[:20],
        "conflicting_declarations": conflicting[:20],
        "present_but_undeclared_count": len(undeclared),
        "present_but_undeclared": undeclared[:40],
        "artifact_root_escape_paths": escaping_links[:20],
        "ledger_verified": ledger_valid,
        "ledger_verification": ledger_reason,
        "producer_verdicts_refused_as_evidence_count": len(set(producer_verdicts)),
        "producer_verdicts_refused_as_evidence": sorted(set(producer_verdicts))[:40],
        "declared_artifacts_intact": declared_artifacts_intact,
        "sealed_scope_complete": sealed_scope_complete,
        "integrity_pass": not defects,
        "semantic_verdict": "not_evaluated",
        "promotion_allowed": False,
        "claim_ceiling": "sealed byte-level artifact integrity only; no simulation, scientific, admission, or release claim",
        "defects": defects,
    }
    write_output(output_path, result)
    print(
        "declared=%d match=%d mismatch=%d absent=%d escaped=%d undeclared=%d integrity_pass=%s"
        % (
            len(declarations), len(matched), len(mismatch), len(absent), len(escaped), len(undeclared), result["integrity_pass"],
        )
    )
    for defect in defects:
        print(f"DEFECT: {defect}")
    return 0 if result["integrity_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
