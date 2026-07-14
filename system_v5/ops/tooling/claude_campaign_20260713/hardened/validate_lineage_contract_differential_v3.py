#!/usr/bin/env python3
"""Fail-closed validator for the H lineage contract differential receipt."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
DEFAULT_RECEIPT = HERE / "results" / "lineage_contract_differential_v3_results.json"
DEFAULT_SOURCE = HERE / "lineage_contract_differential_v3.py"
DEFAULT_VALIDATOR = Path(__file__).resolve()
DEFAULT_VALIDATION_OUTPUT = HERE / "results" / "lineage_contract_differential_v3_validation.json"
DEFAULT_ARCHIVE = Path(
    "/Users/joshuaeisenhart/Desktop/166_reconciled_ratchet_v0_11_7_cold_verified (1).zip"
)
EXPECTED_PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")

EXPECTED_SCHEMA = "codex-ratchet.lineage-contract-differential-result.v3"
EXPECTED_ARCHIVE_SHA256 = "42fc2629e076b4cd5b8015514fb1c9027aa7c751702ebc7a719a6b808141b9da"
EXPECTED_POOL_SHA256 = "73f152e646e6cd9e0e989c4b0f7ce1f6ca2c39359c951f40648b0a3909a954e8"
EXPECTED_LEDGER_SHA256 = "850e975c1d3e7aee2a78d5614a4d64e21bd0309ef61683ed150c77c209870553"
EXPECTED_CLAIM_CEILING = "contract semantics only; no production integrity defect"
EXPECTED_POOL_MEMBER = "ratchet/purgatory_pool.py"
EXPECTED_LEDGER_MEMBER = "sims_and_scripts/living_purgatory_ledger_r2_results.json"
NATIVE_MODE = "packet_native_integrity_v3"
STRICT_MODE = "audit_only_strict_ancestry_dag_v1"

EXPECTED_TOP_LEVEL_KEYS = {
    "schema",
    "created_at",
    "command",
    "runner_identity",
    "classification",
    "evidence_level",
    "promotion_allowed",
    "formal_admission_allowed",
    "native_verifier_change_attempted",
    "integrity_defect_admitted",
    "h_integrity_defect_claim_pass",
    "h_lane_status",
    "all_pass",
    "contract_differential_closed",
    "claim_ceiling",
    "sources",
    "mode_contracts",
    "same_packet_cycle_ledger",
    "fixture_controls",
    "actual_packet_topology_mutations",
    "tampered_hash_control",
    "checks",
    "semantic_verdict",
    "tool_manifest",
    "blocked_consumers",
    "process_exit_semantics",
    "receipt_content_sha256",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def receipt_content_sha256(receipt: Mapping[str, Any]) -> str:
    core = copy.deepcopy(dict(receipt))
    core.pop("receipt_content_sha256", None)
    return sha256_bytes(canonical_json(core).encode("utf-8"))


def semantic_snapshot(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Return every deterministic producer field.

    ``created_at`` is historical receipt metadata, ``command`` contains the
    caller-selected output path, and ``receipt_content_sha256`` seals those two
    fields.  Everything else must equal a fresh producer rerun.
    """
    snapshot = copy.deepcopy(dict(receipt))
    snapshot.pop("created_at", None)
    snapshot.pop("command", None)
    snapshot.pop("receipt_content_sha256", None)
    return snapshot


def differing_paths(expected: Any, actual: Any, prefix: str = "") -> list[str]:
    """Name bounded semantic differences without trusting receipt summaries."""
    if type(expected) is not type(actual):
        return [prefix or "<root>"]
    if isinstance(expected, Mapping):
        paths: list[str] = []
        keys = set(expected) | set(actual)
        for key in sorted(keys):
            child = f"{prefix}.{key}" if prefix else str(key)
            if key not in expected or key not in actual:
                paths.append(child)
            else:
                paths.extend(differing_paths(expected[key], actual[key], child))
        return paths
    if isinstance(expected, list):
        paths = []
        if len(expected) != len(actual):
            paths.append(f"{prefix}.length")
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            paths.extend(differing_paths(expected_item, actual_item, f"{prefix}[{index}]"))
        return paths
    return [] if expected == actual else [prefix or "<root>"]


@lru_cache(maxsize=1)
def recompute_expected_receipt() -> dict[str, Any]:
    """Rerun the pinned producer into temporary storage.

    This is the validator's independent execution boundary.  The candidate
    receipt cannot supply the source, archive, validator, runtime, or output
    path used for this recomputation.
    """
    with tempfile.TemporaryDirectory(prefix="ratchet-h-validator-v3-") as directory_name:
        output = Path(directory_name) / "fresh-lineage-contract-differential-v3.json"
        command = [
            str(EXPECTED_PYTHON),
            "-B",
            str(DEFAULT_SOURCE.resolve()),
            "--archive",
            str(DEFAULT_ARCHIVE.resolve()),
            "--output",
            str(output),
            "--validator",
            str(DEFAULT_VALIDATOR),
        ]
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONNOUSERSITE"] = "1"
        subprocess.run(
            command,
            cwd=HERE.parents[4],
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return json.loads(output.read_text(encoding="utf-8"))


def require_boolean(errors: list[str], raw: Mapping[str, Any], key: str, expected: bool) -> None:
    if raw.get(key) is not expected:
        errors.append(f"{key} must be {expected}")


def require_scenario(
    errors: list[str],
    name: str,
    scenario: Mapping[str, Any] | None,
    *,
    native_accepts: bool,
    strict_accepts: bool,
    is_dag: bool,
) -> None:
    if not isinstance(scenario, Mapping):
        errors.append(f"{name} missing")
        return
    native = scenario.get("native_mode", {})
    strict = scenario.get("strict_ancestry_dag_mode", {})
    topology = scenario.get("topology_observation", {})
    if native.get("mode") != NATIVE_MODE or native.get("authority") != "packet_native":
        errors.append(f"{name} native mode identity mismatch")
    if native.get("accepted") is not native_accepts:
        errors.append(f"{name} native accepted must be {native_accepts}")
    if strict.get("mode") != STRICT_MODE:
        errors.append(f"{name} strict mode identity mismatch")
    if strict.get("authority") != "audit_only_hypothetical_policy_not_packet_native":
        errors.append(f"{name} strict authority mismatch")
    if strict.get("accepted") is not strict_accepts:
        errors.append(f"{name} strict accepted must be {strict_accepts}")
    if topology.get("is_dag") is not is_dag:
        errors.append(f"{name} topology is_dag must be {is_dag}")
    if not is_dag and topology.get("one_cycle") is None:
        errors.append(f"{name} must name a cycle")


def validate(
    receipt: Mapping[str, Any],
    *,
    receipt_path: Path = DEFAULT_RECEIPT,
    source_path: Path = DEFAULT_SOURCE,
    archive_path: Path = DEFAULT_ARCHIVE,
    validator_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    validator_path = DEFAULT_VALIDATOR if validator_path is None else validator_path.resolve()
    receipt_path = receipt_path.resolve()
    source_path = source_path.resolve()
    archive_path = archive_path.resolve()

    pinned_paths_ok = True
    if source_path != DEFAULT_SOURCE.resolve():
        errors.append("source path must be the pinned H differential producer")
        pinned_paths_ok = False
    if archive_path != DEFAULT_ARCHIVE.resolve():
        errors.append("archive path must be the pinned packet archive")
        pinned_paths_ok = False
    if validator_path != DEFAULT_VALIDATOR:
        errors.append("validator path must be this pinned validator")
        pinned_paths_ok = False
    if Path(sys.executable).resolve() != EXPECTED_PYTHON.resolve():
        errors.append("validator Python runtime mismatch")
        pinned_paths_ok = False

    if set(receipt) != EXPECTED_TOP_LEVEL_KEYS:
        errors.append("top-level receipt keys mismatch")
    if receipt.get("schema") != EXPECTED_SCHEMA:
        errors.append("schema mismatch")
    if receipt.get("classification") != "contract_semantics_audit":
        errors.append("classification mismatch")
    if receipt.get("claim_ceiling") != EXPECTED_CLAIM_CEILING:
        errors.append("claim_ceiling mismatch")
    require_boolean(errors, receipt, "promotion_allowed", False)
    require_boolean(errors, receipt, "formal_admission_allowed", False)
    require_boolean(errors, receipt, "native_verifier_change_attempted", False)
    require_boolean(errors, receipt, "integrity_defect_admitted", False)
    require_boolean(errors, receipt, "h_integrity_defect_claim_pass", False)
    require_boolean(errors, receipt, "all_pass", False)
    require_boolean(errors, receipt, "contract_differential_closed", True)
    if receipt.get("h_lane_status") != "red_unadmitted_contract_difference":
        errors.append("H lane must remain red and unadmitted")

    expected_command = [
        str(EXPECTED_PYTHON),
        str(DEFAULT_SOURCE.resolve()),
        "--archive",
        str(DEFAULT_ARCHIVE.resolve()),
        "--output",
        str(receipt_path),
        "--validator",
        str(DEFAULT_VALIDATOR),
    ]
    if receipt.get("command") != expected_command:
        errors.append("producer command mismatch")
    try:
        created_at = datetime.fromisoformat(str(receipt.get("created_at")))
        if created_at.tzinfo is None:
            errors.append("created_at must be timezone-aware")
    except ValueError:
        errors.append("created_at must be ISO-8601")

    expected_content_hash = receipt_content_sha256(receipt)
    if receipt.get("receipt_content_sha256") != expected_content_hash:
        errors.append("receipt_content_sha256 mismatch")

    sources = receipt.get("sources", {})
    expected_source_paths = {
        "archive_path": str(DEFAULT_ARCHIVE.resolve()),
        "native_verifier_member": EXPECTED_POOL_MEMBER,
        "ledger_member": EXPECTED_LEDGER_MEMBER,
        "audit_source_path": str(DEFAULT_SOURCE.resolve()),
        "validator_source_path": str(DEFAULT_VALIDATOR),
    }
    for key, expected in expected_source_paths.items():
        if sources.get(key) != expected:
            errors.append(f"sources.{key} mismatch")
    if sources.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256:
        errors.append("pinned archive sha256 mismatch in receipt")
    if sources.get("native_verifier_sha256") != EXPECTED_POOL_SHA256:
        errors.append("pinned native verifier sha256 mismatch in receipt")
    if sources.get("ledger_sha256") != EXPECTED_LEDGER_SHA256:
        errors.append("pinned ledger sha256 mismatch in receipt")
    if not source_path.is_file() or sources.get("audit_source_sha256") != sha256_file(source_path):
        errors.append("audit source sha256 mismatch")
    if not validator_path.is_file() or sources.get("validator_source_sha256") != sha256_file(validator_path):
        errors.append("validator source sha256 mismatch")
    if not archive_path.is_file() or sha256_file(archive_path) != EXPECTED_ARCHIVE_SHA256:
        errors.append("live archive sha256 mismatch")

    modes = receipt.get("mode_contracts", {})
    native_contract = modes.get("native_mode", {})
    strict_contract = modes.get("strict_ancestry_dag_mode", {})
    if native_contract.get("mode") != NATIVE_MODE or native_contract.get("authority") != "packet_native":
        errors.append("native contract identity mismatch")
    if native_contract.get("dag_requirement") is not False:
        errors.append("native contract must not be rewritten as DAG-bearing")
    if strict_contract.get("mode") != STRICT_MODE:
        errors.append("strict contract identity mismatch")
    if strict_contract.get("authority") != "audit_only_hypothetical_policy_not_packet_native":
        errors.append("strict contract must remain audit-only")
    if strict_contract.get("production_change") is not False:
        errors.append("strict contract must not claim a production change")

    require_scenario(
        errors,
        "same_packet_cycle_ledger",
        receipt.get("same_packet_cycle_ledger"),
        native_accepts=True,
        strict_accepts=False,
        is_dag=False,
    )
    fixtures = receipt.get("fixture_controls", {})
    require_scenario(
        errors,
        "valid_dag_positive",
        fixtures.get("valid_dag_positive"),
        native_accepts=True,
        strict_accepts=True,
        is_dag=True,
    )
    require_scenario(
        errors,
        "cycle_negative",
        fixtures.get("cycle_negative"),
        native_accepts=True,
        strict_accepts=False,
        is_dag=False,
    )
    require_scenario(
        errors,
        "isolated_boundary",
        fixtures.get("isolated_boundary"),
        native_accepts=True,
        strict_accepts=True,
        is_dag=True,
    )

    mutations = receipt.get("actual_packet_topology_mutations", {})
    projection = mutations.get("dag_projection", {})
    if not isinstance(projection.get("removed_edge_count"), int) or projection.get("removed_edge_count", 0) < 1:
        errors.append("actual packet DAG projection must remove at least one cycle-closing edge")
    if len(projection.get("removed_variation_ids", [])) != projection.get("removed_edge_count"):
        errors.append("DAG projection removed edge count mismatch")
    require_scenario(
        errors,
        "actual_packet_dag_projection",
        projection.get("result"),
        native_accepts=True,
        strict_accepts=True,
        is_dag=True,
    )
    injection = mutations.get("rehash_consistent_reverse_edge_injection", {})
    injected_edge = injection.get("mutation", {}).get("injected_edge", {})
    if injected_edge.get("operator") != "audit_only_reverse_edge_injection":
        errors.append("actual packet topology mutation identity mismatch")
    require_scenario(
        errors,
        "rehash_consistent_reverse_edge_injection",
        injection.get("result"),
        native_accepts=True,
        strict_accepts=False,
        is_dag=False,
    )

    require_scenario(
        errors,
        "tampered_hash_control",
        receipt.get("tampered_hash_control"),
        native_accepts=False,
        strict_accepts=False,
        is_dag=False,
    )
    tampered_strict = receipt.get("tampered_hash_control", {}).get("strict_ancestry_dag_mode", {})
    if tampered_strict.get("reason") != "native_integrity_precondition_failed":
        errors.append("tampered hash must fail the strict native-integrity precondition")
    if tampered_strict.get("dag_predicate_evaluated_for_policy") is not False:
        errors.append("strict DAG policy must fail closed before topology on a native-integrity failure")

    checks = receipt.get("checks", {})
    if not checks or not all(value is True for value in checks.values()):
        errors.append("all bounded differential checks must be true")
    semantic = receipt.get("semantic_verdict", {})
    if semantic.get("production_integrity_defect_admitted") is not False:
        errors.append("semantic verdict must not admit a production integrity defect")
    if semantic.get("status") != "contract_semantics_differential_closed_h_remains_red":
        errors.append("semantic status mismatch")
    if semantic.get("contract_difference_reproduced") is not True:
        errors.append("contract difference must be reproduced")
    blocked = set(receipt.get("blocked_consumers", []))
    required_blocked = {
        "packet integrity defect escalation",
        "production verifier change",
        "scientific memory-layer crack claim",
        "Ratchet promotion",
        "Lev promotion",
    }
    if not required_blocked.issubset(blocked):
        errors.append("blocked consumers are incomplete")

    if pinned_paths_ok:
        try:
            fresh_receipt = recompute_expected_receipt()
        except (
            OSError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            json.JSONDecodeError,
        ) as error:
            errors.append(f"fresh producer recomputation failed: {type(error).__name__}")
        else:
            differences = differing_paths(
                semantic_snapshot(fresh_receipt),
                semantic_snapshot(receipt),
            )
            if differences:
                errors.append(
                    "fresh producer semantic mismatch: " + ", ".join(differences[:20])
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_VALIDATION_OUTPUT)
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    errors = validate(
        receipt,
        receipt_path=args.receipt,
        source_path=args.source,
        archive_path=args.archive,
        validator_path=DEFAULT_VALIDATOR,
    )
    try:
        fresh_receipt = recompute_expected_receipt()
        fresh_semantic_sha256 = sha256_bytes(
            canonical_json(semantic_snapshot(fresh_receipt)).encode("utf-8")
        )
        fresh_recompute_performed = True
    except (
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ):
        fresh_semantic_sha256 = None
        fresh_recompute_performed = False
    validation = {
        "schema": "codex-ratchet.lineage-contract-differential-validation.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": [
            str(Path(__file__).resolve()),
            "--receipt",
            str(args.receipt.resolve()),
            "--source",
            str(args.source.resolve()),
            "--archive",
            str(args.archive.resolve()),
            "--output",
            str(args.output.resolve()),
        ],
        "receipt_path": str(args.receipt.resolve()),
        "receipt_file_sha256": sha256_file(args.receipt.resolve()),
        "fresh_recompute_performed": fresh_recompute_performed,
        "fresh_semantic_sha256": fresh_semantic_sha256,
        "validated": not errors,
        "error_count": len(errors),
        "errors": errors,
        "claim_ceiling": EXPECTED_CLAIM_CEILING,
        "h_all_pass": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"validated": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
