#!/usr/bin/env python3
"""Fail-closed provenance audit for a root -> basin -> MSS receipt chain.

This tool does not promote a scientific result.  It verifies one narrower
claim: an externally anchored authority manifest names the exact root, basin,
and MSS receipts, their producers, one validated root candidate, and explicit
F01/N01 evidence bindings; the child receipts then bind that exact chain at one
canonical input path.

A mutually self-consistent set of writable JSON files is not an authority
boundary.  Green therefore requires both ``--trust-manifest`` and the manifest
SHA-256 supplied independently through ``--trust-manifest-sha256``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import shutil
import sys
import tempfile
from typing import Any


SCHEMA = "foundation-chain-binding-audit/0.2"
TRUST_SCHEMA = "foundation-chain-binding-authority/0.1"
FINGERPRINT_ALGORITHM = "sha256-canonical-json-members-partition-digests-v1"

ROOT_SCHEMA = "ratchet-order-open-run/0.5"
ROOT_SOURCE_PACKET = "root-order-open-process-packet-v0.5"
ROOT_PRODUCER_ID = ROOT_SOURCE_PACKET
BASIN_SCHEMA = "attractors_basin_native_schedule_result_v1"
BASIN_SIM_ID = "attractors_basin_native_schedule_v0"
BASIN_PRODUCER_ID = BASIN_SIM_ID
MSS_SCHEMA = "mss_minimal_survivor_census_result_v1"
MSS_SIM_ID = "mss_minimal_survivor_census_v0"
MSS_PRODUCER_ID = MSS_SIM_ID

CONSTRAINT_MEANINGS = {
    "F01": "finite carrier/probe/operator/path set",
    "N01": "noncommuting/order-sensitive composition",
}
INPUT_BINDING_KEYS = {
    "chain_id",
    "run_nonce",
    "parent_receipt_sha256",
    "candidate_content_sha256",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def read_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: pathlib.Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def expected_frontier_fingerprint(members: list[str], partition_digests: list[str]) -> str:
    return canonical_sha256({"members": members, "partition_digests": partition_digests})


def root_candidate(root: dict[str, Any]) -> dict[str, Any]:
    cache = root.get("frontier_cache")
    if not isinstance(cache, dict):
        return _missing_candidate("missing_frontier_cache")

    members = cache.get("full_packet_frontier")
    digests = cache.get("full_packet_frontier_partition_digests")
    fingerprint = cache.get("full_packet_frontier_fingerprint")
    algorithm = cache.get("full_packet_frontier_fingerprint_algorithm")
    if algorithm != FINGERPRINT_ALGORITHM:
        return {
            **_missing_candidate("missing_or_unsupported_fingerprint_algorithm"),
            "fingerprint_algorithm": algorithm,
        }
    if not (
        isinstance(members, list)
        and members
        and all(isinstance(value, str) and value for value in members)
        and len(set(members)) == len(members)
    ):
        return _missing_candidate("invalid_frontier_members")
    if not (
        isinstance(digests, list)
        and len(digests) == len(members)
        and all(is_sha256(value) for value in digests)
    ):
        return _missing_candidate("invalid_partition_digests")
    if not is_sha256(fingerprint):
        return _missing_candidate("invalid_frontier_fingerprint")

    recomputed = expected_frontier_fingerprint(members, digests)
    if fingerprint != recomputed:
        return {
            **_missing_candidate("frontier_fingerprint_mismatch"),
            "members": members,
            "partition_digests": digests,
            "declared_fingerprint": fingerprint,
            "recomputed_fingerprint": recomputed,
            "fingerprint_algorithm": algorithm,
        }

    payload = {
        "kind": "order_open_frontier",
        "members": members,
        "partition_digests": digests,
        "frontier_fingerprint": fingerprint,
    }
    return {
        "pass": True,
        "code": "validated",
        "kind": "order_open_frontier",
        "members": members,
        "partition_digests": digests,
        "declared_fingerprint": fingerprint,
        "recomputed_fingerprint": recomputed,
        "fingerprint_algorithm": algorithm,
        "content_sha256": canonical_sha256(payload),
    }


def _missing_candidate(code: str) -> dict[str, Any]:
    return {
        "pass": False,
        "code": code,
        "kind": "missing",
        "members": [],
        "partition_digests": [],
        "declared_fingerprint": None,
        "recomputed_fingerprint": None,
        "fingerprint_algorithm": None,
        "content_sha256": None,
    }


def _producer_shape(value: Any, *, expected_id: str) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "source_sha256"}
        and value.get("id") == expected_id
        and is_sha256(value.get("source_sha256"))
    )


def _expected_receipt_profile(lane: str) -> dict[str, str]:
    if lane == "root":
        return {
            "schema_key": "schema_version",
            "schema": ROOT_SCHEMA,
            "identity_key": "source_packet",
            "identity": ROOT_SOURCE_PACKET,
            "producer_id": ROOT_PRODUCER_ID,
        }
    if lane == "basin":
        return {
            "schema_key": "schema",
            "schema": BASIN_SCHEMA,
            "identity_key": "sim_id",
            "identity": BASIN_SIM_ID,
            "producer_id": BASIN_PRODUCER_ID,
        }
    if lane == "mss":
        return {
            "schema_key": "schema",
            "schema": MSS_SCHEMA,
            "identity_key": "sim_id",
            "identity": MSS_SIM_ID,
            "producer_id": MSS_PRODUCER_ID,
        }
    raise ValueError(lane)


def validate_trust_manifest(
    path: pathlib.Path | None,
    externally_pinned_sha256: str | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    result: dict[str, Any] = {
        "pass": False,
        "code": "missing_trust_manifest",
        "path": str(path) if path else None,
        "externally_pinned_sha256": externally_pinned_sha256,
        "observed_sha256": None,
        "chain_id": None,
        "run_nonce": None,
    }
    if path is None:
        return result, None
    if not is_sha256(externally_pinned_sha256):
        result["code"] = "missing_or_invalid_external_manifest_pin"
        return result, None
    try:
        observed = sha256_file(path)
        manifest = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        result["code"] = "unreadable_trust_manifest"
        result["error"] = str(exc)
        return result, None
    result["observed_sha256"] = observed
    if observed != externally_pinned_sha256:
        result["code"] = "trust_manifest_sha256_mismatch"
        return result, None
    if not isinstance(manifest, dict):
        result["code"] = "trust_manifest_not_object"
        return result, None
    expected_keys = {
        "schema",
        "chain_id",
        "run_nonce",
        "candidate_fingerprint_algorithm",
        "candidate_content_sha256",
        "root_constraints",
        "receipts",
    }
    if set(manifest) != expected_keys or manifest.get("schema") != TRUST_SCHEMA:
        result["code"] = "invalid_trust_manifest_schema"
        return result, None
    chain_id = manifest.get("chain_id")
    run_nonce = manifest.get("run_nonce")
    if not (isinstance(chain_id, str) and chain_id and isinstance(run_nonce, str) and run_nonce):
        result["code"] = "invalid_chain_identity"
        return result, None
    if not is_sha256(manifest.get("candidate_content_sha256")):
        result["code"] = "invalid_manifest_candidate_hash"
        return result, None
    if manifest.get("candidate_fingerprint_algorithm") != FINGERPRINT_ALGORITHM:
        result["code"] = "invalid_manifest_fingerprint_algorithm"
        return result, None

    constraints = manifest.get("root_constraints")
    if not isinstance(constraints, dict) or set(constraints) != set(CONSTRAINT_MEANINGS):
        result["code"] = "invalid_manifest_constraint_set"
        return result, None
    for name, meaning in CONSTRAINT_MEANINGS.items():
        row = constraints.get(name)
        if not (
            isinstance(row, dict)
            and set(row) == {"status", "meaning", "evidence_receipt_sha256"}
            and row.get("status") == "passed"
            and row.get("meaning") == meaning
            and is_sha256(row.get("evidence_receipt_sha256"))
        ):
            result["code"] = f"invalid_manifest_constraint_{name}"
            return result, None

    receipts = manifest.get("receipts")
    if not isinstance(receipts, dict) or set(receipts) != {"root", "basin", "mss"}:
        result["code"] = "invalid_manifest_receipt_set"
        return result, None
    for lane in ("root", "basin", "mss"):
        profile = _expected_receipt_profile(lane)
        row = receipts.get(lane)
        expected_row_keys = {
            "schema",
            "receipt_sha256",
            "producer",
            profile["identity_key"],
        }
        if not isinstance(row, dict) or set(row) != expected_row_keys:
            result["code"] = f"invalid_manifest_{lane}_profile"
            return result, None
        if (
            row.get("schema") != profile["schema"]
            or row.get(profile["identity_key"]) != profile["identity"]
            or not is_sha256(row.get("receipt_sha256"))
            or not _producer_shape(row.get("producer"), expected_id=profile["producer_id"])
        ):
            result["code"] = f"invalid_manifest_{lane}_identity"
            return result, None

    result.update(
        {
            "pass": True,
            "code": "externally_pinned",
            "chain_id": chain_id,
            "run_nonce": run_nonce,
        }
    )
    return result, manifest


def receipt_identity_check(
    lane: str,
    receipt: dict[str, Any],
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    profile = _expected_receipt_profile(lane)
    manifest_row = ((manifest or {}).get("receipts") or {}).get(lane) or {}
    expected_producer = manifest_row.get("producer")
    checks = {
        "schema": receipt.get(profile["schema_key"]) == profile["schema"],
        "identity": receipt.get(profile["identity_key"]) == profile["identity"],
        "producer_shape": _producer_shape(receipt.get("producer"), expected_id=profile["producer_id"]),
        "producer_matches_manifest": isinstance(expected_producer, dict)
        and receipt.get("producer") == expected_producer,
    }
    passed = bool(checks and all(checks.values()))
    return {
        "pass": passed,
        "code": "identity_pinned" if passed else "schema_sim_or_producer_identity_mismatch",
        "expected_schema": profile["schema"],
        "observed_schema": receipt.get(profile["schema_key"]),
        "expected_identity": profile["identity"],
        "observed_identity": receipt.get(profile["identity_key"]),
        "observed_producer": receipt.get("producer"),
        "checks": checks,
    }


def receipt_authority_pin(
    lane: str,
    actual_sha256: str,
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    expected = ((((manifest or {}).get("receipts") or {}).get(lane) or {}).get("receipt_sha256"))
    passed = is_sha256(expected) and actual_sha256 == expected
    return {
        "pass": bool(passed),
        "code": "receipt_hash_pinned" if passed else "receipt_hash_not_authorized",
        "expected_receipt_sha256": expected,
        "observed_receipt_sha256": actual_sha256,
    }


def constraint_binding_check(
    root: dict[str, Any],
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    observed = root.get("root_constraint_bindings")
    expected = (manifest or {}).get("root_constraints")
    checks: dict[str, bool] = {}
    if not isinstance(observed, dict) or set(observed) != set(CONSTRAINT_MEANINGS):
        return {
            "pass": False,
            "code": "missing_or_noncanonical_constraint_bindings",
            "checks": {name: False for name in CONSTRAINT_MEANINGS},
            "observed": observed,
        }
    for name, meaning in CONSTRAINT_MEANINGS.items():
        row = observed.get(name)
        expected_row = (expected or {}).get(name) if isinstance(expected, dict) else None
        checks[name] = bool(
            isinstance(row, dict)
            and set(row) == {"status", "meaning", "evidence_receipt_sha256"}
            and row.get("status") == "passed"
            and row.get("meaning") == meaning
            and is_sha256(row.get("evidence_receipt_sha256"))
            and row == expected_row
        )
    passed = bool(checks and all(checks.values()))
    return {
        "pass": passed,
        "code": "semantic_constraints_pinned" if passed else "constraint_status_or_evidence_mismatch",
        "checks": checks,
        "observed": observed,
    }


def candidate_authority_pin(
    candidate: dict[str, Any],
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    expected = (manifest or {}).get("candidate_content_sha256")
    observed = candidate.get("content_sha256")
    passed = bool(candidate.get("pass") and is_sha256(expected) and observed == expected)
    return {
        "pass": passed,
        "code": "candidate_hash_pinned" if passed else "candidate_hash_not_authorized",
        "expected_candidate_content_sha256": expected,
        "observed_candidate_content_sha256": observed,
    }


def execution_shape(result: dict[str, Any], *, lane: str) -> dict[str, Any]:
    profile = _expected_receipt_profile(lane)
    all_pass = result.get("all_pass")
    ran = (
        result.get(profile["schema_key"]) == profile["schema"]
        and result.get(profile["identity_key"]) == profile["identity"]
        and all_pass is True
    )
    return {
        "schema": result.get(profile["schema_key"]),
        "identity": result.get(profile["identity_key"]),
        "declared_all_pass": all_pass,
        "ran": bool(ran),
    }


def binding_check(
    child: dict[str, Any],
    *,
    expected_parent_sha256: str,
    expected_candidate_sha256: str | None,
    chain_id: str | None,
    run_nonce: str | None,
) -> dict[str, Any]:
    binding = child.get("input_binding")
    base = {
        "pass": False,
        "expected_parent_receipt_sha256": expected_parent_sha256,
        "expected_candidate_content_sha256": expected_candidate_sha256,
        "expected_chain_id": chain_id,
        "expected_run_nonce": run_nonce,
        "observed": binding,
    }
    if not isinstance(binding, dict):
        return {**base, "code": "missing_input_binding"}
    if set(binding) != INPUT_BINDING_KEYS:
        return {**base, "code": "noncanonical_input_binding_fields"}
    if binding.get("chain_id") != chain_id or binding.get("run_nonce") != run_nonce:
        return {**base, "code": "chain_identity_mismatch"}
    parent_hash = binding.get("parent_receipt_sha256")
    candidate_hash = binding.get("candidate_content_sha256")
    if not is_sha256(parent_hash):
        return {**base, "code": "invalid_parent_receipt_hash"}
    if parent_hash != expected_parent_sha256:
        return {**base, "code": "stale_replayed_or_mismatched_parent_receipt"}
    if not is_sha256(candidate_hash):
        return {**base, "code": "invalid_candidate_content_hash"}
    if candidate_hash != expected_candidate_sha256:
        return {**base, "code": "stale_replayed_or_mismatched_candidate_content"}
    return {**base, "pass": True, "code": "bound"}


def audit(
    root_path: pathlib.Path,
    basin_path: pathlib.Path,
    mss_path: pathlib.Path,
    *,
    trust_manifest_path: pathlib.Path | None,
    trust_manifest_sha256: str | None,
) -> dict[str, Any]:
    root = read_json(root_path)
    basin = read_json(basin_path)
    mss = read_json(mss_path)
    if not all(isinstance(value, dict) for value in (root, basin, mss)):
        raise ValueError("all three receipts must be JSON objects")

    root_sha = sha256_file(root_path)
    basin_sha = sha256_file(basin_path)
    mss_sha = sha256_file(mss_path)
    trust, manifest = validate_trust_manifest(trust_manifest_path, trust_manifest_sha256)
    chain_id = trust.get("chain_id")
    run_nonce = trust.get("run_nonce")

    identities = {
        "root": receipt_identity_check("root", root, manifest),
        "basin": receipt_identity_check("basin", basin, manifest),
        "mss": receipt_identity_check("mss", mss, manifest),
    }
    authority_pins = {
        "root_receipt": receipt_authority_pin("root", root_sha, manifest),
        "basin_receipt": receipt_authority_pin("basin", basin_sha, manifest),
        "mss_receipt": receipt_authority_pin("mss", mss_sha, manifest),
    }
    candidate = root_candidate(root)
    candidate_pin = candidate_authority_pin(candidate, manifest)
    authority_pins["candidate"] = candidate_pin
    constraints = constraint_binding_check(root, manifest)
    basin_shape = execution_shape(basin, lane="basin")
    mss_shape = execution_shape(mss, lane="mss")

    root_to_basin = binding_check(
        basin,
        expected_parent_sha256=root_sha,
        expected_candidate_sha256=candidate.get("content_sha256"),
        chain_id=chain_id,
        run_nonce=run_nonce,
    )
    basin_to_mss = binding_check(
        mss,
        expected_parent_sha256=basin_sha,
        expected_candidate_sha256=candidate.get("content_sha256"),
        chain_id=chain_id,
        run_nonce=run_nonce,
    )

    ordered_checks = [
        ("trust_manifest", trust["pass"]),
        ("root_identity", identities["root"]["pass"]),
        ("root_candidate_extraction", candidate["pass"]),
        ("root_constraint_binding", constraints["pass"]),
        ("root_authority_pin", authority_pins["root_receipt"]["pass"] and candidate_pin["pass"]),
        ("basin_identity", identities["basin"]["pass"]),
        ("basin_execution", basin_shape["ran"]),
        ("root_to_basin_binding", root_to_basin["pass"]),
        ("basin_authority_pin", authority_pins["basin_receipt"]["pass"]),
        ("mss_identity", identities["mss"]["pass"]),
        ("mss_execution", mss_shape["ran"]),
        ("basin_to_mss_binding", basin_to_mss["pass"]),
        ("mss_authority_pin", authority_pins["mss_receipt"]["pass"]),
    ]
    break_stage = next((name for name, passed in ordered_checks if not passed), None)
    all_pass = break_stage is None
    return {
        "schema": SCHEMA,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "auditor": {
            "source_path": str(pathlib.Path(__file__).resolve()),
            "source_sha256": sha256_file(pathlib.Path(__file__).resolve()),
            "runner_identity": sys.executable,
        },
        "all_pass": all_pass,
        "scientific_status": "anchored_chain_bound" if all_pass else "blocked_unbound_or_unauthenticated",
        "break_stage": break_stage,
        "root_receipt_count": 1,
        "required_constraint_ids": list(CONSTRAINT_MEANINGS),
        "trust_manifest": trust,
        "constraint_binding": constraints,
        "input_receipts": {
            "root": {"path": str(root_path), "sha256": root_sha},
            "basin": {"path": str(basin_path), "sha256": basin_sha},
            "mss": {"path": str(mss_path), "sha256": mss_sha},
        },
        "identity_checks": identities,
        "authority_pins": authority_pins,
        "root_candidate": candidate,
        "execution_shapes": {"basin": basin_shape, "mss": mss_shape},
        "bindings": {
            "root_to_basin": root_to_basin,
            "basin_to_mss": basin_to_mss,
        },
        "checks": [{"id": name, "pass": passed} for name, passed in ordered_checks],
        "claim_ceiling": (
            "Integrity/provenance binding audit only. The audit cannot authenticate an unanchored triplet: "
            "green requires an externally supplied trust-manifest SHA-256. Even green does not admit Axis0, "
            "a basin, MSS, a Ratchet tooth, a manifold layer, physics, Lev promotion, or canon."
        ),
        "blocked_consumers": [
            "paired_engine_e2e",
            "full_ratchet_e2e",
            "scientific_manifold_admission",
            "lev_promotion",
        ],
    }


def _synthetic_constraint_bindings() -> dict[str, Any]:
    return {
        "F01": {
            "status": "passed",
            "meaning": CONSTRAINT_MEANINGS["F01"],
            "evidence_receipt_sha256": "d" * 64,
        },
        "N01": {
            "status": "passed",
            "meaning": CONSTRAINT_MEANINGS["N01"],
            "evidence_receipt_sha256": "e" * 64,
        },
    }


def synthetic_root(*, member: str = "candidate-A") -> dict[str, Any]:
    members = [member]
    digests = ["f" * 64]
    return {
        "schema_version": ROOT_SCHEMA,
        "source_packet": ROOT_SOURCE_PACKET,
        "producer": {"id": ROOT_PRODUCER_ID, "source_sha256": "a" * 64},
        "root_constraint_bindings": _synthetic_constraint_bindings(),
        "frontier_cache": {
            "full_packet_frontier": members,
            "full_packet_frontier_partition_digests": digests,
            "full_packet_frontier_fingerprint": expected_frontier_fingerprint(members, digests),
            "full_packet_frontier_fingerprint_algorithm": FINGERPRINT_ALGORITHM,
        },
    }


def _build_valid_triplet(base: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path, str]:
    chain_id = "foundation-chain-selftest"
    run_nonce = "preregistered-selftest-nonce"
    root_path = base / "root.json"
    basin_path = base / "basin.json"
    mss_path = base / "mss.json"
    manifest_path = base / "trust_manifest.json"

    root = synthetic_root()
    write_json(root_path, root)
    root_sha = sha256_file(root_path)
    candidate_hash = root_candidate(root)["content_sha256"]
    basin = {
        "schema": BASIN_SCHEMA,
        "sim_id": BASIN_SIM_ID,
        "all_pass": True,
        "producer": {"id": BASIN_PRODUCER_ID, "source_sha256": "b" * 64},
        "input_binding": {
            "chain_id": chain_id,
            "run_nonce": run_nonce,
            "parent_receipt_sha256": root_sha,
            "candidate_content_sha256": candidate_hash,
        },
    }
    write_json(basin_path, basin)
    basin_sha = sha256_file(basin_path)
    mss = {
        "schema": MSS_SCHEMA,
        "sim_id": MSS_SIM_ID,
        "all_pass": True,
        "producer": {"id": MSS_PRODUCER_ID, "source_sha256": "c" * 64},
        "input_binding": {
            "chain_id": chain_id,
            "run_nonce": run_nonce,
            "parent_receipt_sha256": basin_sha,
            "candidate_content_sha256": candidate_hash,
        },
    }
    write_json(mss_path, mss)
    manifest = {
        "schema": TRUST_SCHEMA,
        "chain_id": chain_id,
        "run_nonce": run_nonce,
        "candidate_fingerprint_algorithm": FINGERPRINT_ALGORITHM,
        "candidate_content_sha256": candidate_hash,
        "root_constraints": _synthetic_constraint_bindings(),
        "receipts": {
            "root": {
                "schema": ROOT_SCHEMA,
                "source_packet": ROOT_SOURCE_PACKET,
                "receipt_sha256": root_sha,
                "producer": copy.deepcopy(root["producer"]),
            },
            "basin": {
                "schema": BASIN_SCHEMA,
                "sim_id": BASIN_SIM_ID,
                "receipt_sha256": basin_sha,
                "producer": copy.deepcopy(basin["producer"]),
            },
            "mss": {
                "schema": MSS_SCHEMA,
                "sim_id": MSS_SIM_ID,
                "receipt_sha256": sha256_file(mss_path),
                "producer": copy.deepcopy(mss["producer"]),
            },
        },
    }
    write_json(manifest_path, manifest)
    return root_path, basin_path, mss_path, manifest_path, sha256_file(manifest_path)


def _clone_case(source: pathlib.Path, destination: pathlib.Path) -> tuple[pathlib.Path, ...]:
    destination.mkdir()
    names = ("root.json", "basin.json", "mss.json", "trust_manifest.json")
    for name in names:
        shutil.copyfile(source / name, destination / name)
    return tuple(destination / name for name in names)


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="foundation-chain-binding-selftest-") as tmp:
        base = pathlib.Path(tmp)
        valid = base / "valid"
        valid.mkdir()
        root_path, basin_path, mss_path, manifest_path, manifest_pin = _build_valid_triplet(valid)

        positive = audit(
            root_path,
            basin_path,
            mss_path,
            trust_manifest_path=manifest_path,
            trust_manifest_sha256=manifest_pin,
        )
        assert positive["all_pass"] is True

        no_trust = audit(
            root_path,
            basin_path,
            mss_path,
            trust_manifest_path=None,
            trust_manifest_sha256=None,
        )
        assert no_trust["break_stage"] == "trust_manifest"

        wrong_pin = audit(
            root_path,
            basin_path,
            mss_path,
            trust_manifest_path=manifest_path,
            trust_manifest_sha256="0" * 64,
        )
        assert wrong_pin["break_stage"] == "trust_manifest"

        case = base / "false_constraints"
        rp, bp, mp, tp = _clone_case(valid, case)
        root = read_json(rp)
        root["root_constraint_bindings"]["F01"]["status"] = "failed"
        root["root_constraint_bindings"]["N01"]["status"] = "failed"
        root["F01"] = False
        root["N01"] = False
        write_json(rp, root)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "root_constraint_binding"

        case = base / "tokens_in_notes"
        rp, bp, mp, tp = _clone_case(valid, case)
        root = read_json(rp)
        root.pop("root_constraint_bindings")
        root["notes"] = {"first": "F01", "second": "N01"}
        write_json(rp, root)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "root_constraint_binding"

        for name, lane, field, value, expected_stage in [
            ("wrong_root_schema", "root.json", "schema_version", "wrong-root", "root_identity"),
            (
                "wrong_root_source_packet",
                "root.json",
                "source_packet",
                "wrong-root-source-packet",
                "root_identity",
            ),
            ("wrong_basin_schema", "basin.json", "schema", "wrong-basin", "basin_identity"),
            ("wrong_basin_id", "basin.json", "sim_id", "wrong-basin-id", "basin_identity"),
            ("wrong_mss_schema", "mss.json", "schema", "wrong-mss", "mss_identity"),
            ("wrong_mss_id", "mss.json", "sim_id", "wrong-mss-id", "mss_identity"),
        ]:
            case = base / name
            rp, bp, mp, tp = _clone_case(valid, case)
            target = {"root.json": rp, "basin.json": bp, "mss.json": mp}[lane]
            receipt = read_json(target)
            receipt[field] = value
            write_json(target, receipt)
            result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
            assert result["break_stage"] == expected_stage

        for name, lane, expected_stage in [
            ("wrong_root_producer_source", "root", "root_identity"),
            ("wrong_basin_producer_source", "basin", "basin_identity"),
            ("wrong_mss_producer_source", "mss", "mss_identity"),
        ]:
            case = base / name
            rp, bp, mp, tp = _clone_case(valid, case)
            target = {"root": rp, "basin": bp, "mss": mp}[lane]
            receipt = read_json(target)
            receipt["producer"]["source_sha256"] = "9" * 64
            write_json(target, receipt)
            result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
            assert result["break_stage"] == expected_stage

        for name, lane, field, replacement, expected_stage, expected_code in [
            (
                "empty_basin_parent_hash",
                "basin",
                "parent_receipt_sha256",
                "",
                "root_to_basin_binding",
                "invalid_parent_receipt_hash",
            ),
            (
                "stale_basin_parent",
                "basin",
                "parent_receipt_sha256",
                "0" * 64,
                "root_to_basin_binding",
                "stale_replayed_or_mismatched_parent_receipt",
            ),
            (
                "empty_basin_candidate_hash",
                "basin",
                "candidate_content_sha256",
                "",
                "root_to_basin_binding",
                "invalid_candidate_content_hash",
            ),
            (
                "stale_basin_candidate",
                "basin",
                "candidate_content_sha256",
                "0" * 64,
                "root_to_basin_binding",
                "stale_replayed_or_mismatched_candidate_content",
            ),
            (
                "empty_mss_parent_hash",
                "mss",
                "parent_receipt_sha256",
                "",
                "basin_to_mss_binding",
                "invalid_parent_receipt_hash",
            ),
            (
                "stale_mss_parent",
                "mss",
                "parent_receipt_sha256",
                "0" * 64,
                "basin_to_mss_binding",
                "stale_replayed_or_mismatched_parent_receipt",
            ),
            (
                "empty_mss_candidate_hash",
                "mss",
                "candidate_content_sha256",
                "",
                "basin_to_mss_binding",
                "invalid_candidate_content_hash",
            ),
            (
                "stale_mss_candidate",
                "mss",
                "candidate_content_sha256",
                "0" * 64,
                "basin_to_mss_binding",
                "stale_replayed_or_mismatched_candidate_content",
            ),
        ]:
            case = base / name
            rp, bp, mp, tp = _clone_case(valid, case)
            target = bp if lane == "basin" else mp
            receipt = read_json(target)
            receipt["input_binding"][field] = replacement
            write_json(target, receipt)
            result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
            assert result["break_stage"] == expected_stage
            key = "root_to_basin" if lane == "basin" else "basin_to_mss"
            assert result["bindings"][key]["code"] == expected_code

        case = base / "stale_plus_smuggled"
        rp, bp, mp, tp = _clone_case(valid, case)
        basin = read_json(bp)
        correct_parent = basin["input_binding"]["parent_receipt_sha256"]
        correct_candidate = basin["input_binding"]["candidate_content_sha256"]
        basin["input_binding"]["parent_receipt_sha256"] = "0" * 64
        basin["input_binding"]["candidate_content_sha256"] = "1" * 64
        basin["untrusted_notes"] = {
            "parent_receipt_sha256": correct_parent,
            "candidate_content_sha256": correct_candidate,
        }
        write_json(bp, basin)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "root_to_basin_binding"

        case = base / "extra_binding_key"
        rp, bp, mp, tp = _clone_case(valid, case)
        basin = read_json(bp)
        basin["input_binding"]["upstream_receipt_sha256"] = basin["input_binding"]["parent_receipt_sha256"]
        write_json(bp, basin)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["bindings"]["root_to_basin"]["code"] == "noncanonical_input_binding_fields"

        case = base / "wrong_chain_identity"
        rp, bp, mp, tp = _clone_case(valid, case)
        basin = read_json(bp)
        basin["input_binding"]["run_nonce"] = "replayed-run-nonce"
        write_json(bp, basin)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["bindings"]["root_to_basin"]["code"] == "chain_identity_mismatch"

        case = base / "bad_frontier"
        rp, bp, mp, tp = _clone_case(valid, case)
        root = read_json(rp)
        root["frontier_cache"]["full_packet_frontier_fingerprint"] = "1" * 64
        write_json(rp, root)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "root_candidate_extraction"

        case = base / "unsupported_fingerprint_algorithm"
        rp, bp, mp, tp = _clone_case(valid, case)
        root = read_json(rp)
        root["frontier_cache"]["full_packet_frontier_fingerprint_algorithm"] = "unversioned"
        write_json(rp, root)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "root_candidate_extraction"

        case = base / "bad_digest_type"
        rp, bp, mp, tp = _clone_case(valid, case)
        root = read_json(rp)
        root["frontier_cache"]["full_packet_frontier_partition_digests"] = "not-a-list"
        write_json(rp, root)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "root_candidate_extraction"

        case = base / "magic_counts_no_pass"
        rp, bp, mp, tp = _clone_case(valid, case)
        mss = read_json(mp)
        mss["all_pass"] = False
        mss["counts"] = {
            "total_tables": 19683,
            "candidate_count_n01": 18954,
            "minimal_count_quotient_only": 17752,
        }
        write_json(mp, mss)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "mss_execution"

        case = base / "basin_declares_failure"
        rp, bp, mp, tp = _clone_case(valid, case)
        basin = read_json(bp)
        basin["all_pass"] = False
        write_json(bp, basin)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "basin_execution"

        case = base / "self_consistent_substitution"
        rp, bp, mp, tp = _clone_case(valid, case)
        root = synthetic_root(member="fabricated-candidate")
        write_json(rp, root)
        root_sha = sha256_file(rp)
        candidate_hash = root_candidate(root)["content_sha256"]
        basin = read_json(bp)
        basin["input_binding"]["parent_receipt_sha256"] = root_sha
        basin["input_binding"]["candidate_content_sha256"] = candidate_hash
        write_json(bp, basin)
        mss = read_json(mp)
        mss["input_binding"]["parent_receipt_sha256"] = sha256_file(bp)
        mss["input_binding"]["candidate_content_sha256"] = candidate_hash
        write_json(mp, mss)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "root_authority_pin"

        case = base / "forged_manifest"
        rp, bp, mp, tp = _clone_case(valid, case)
        manifest = read_json(tp)
        manifest["run_nonce"] = "attacker-selected-nonce"
        write_json(tp, manifest)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["break_stage"] == "trust_manifest"

        case = base / "wrong_manifest_schema_with_fresh_pin"
        rp, bp, mp, tp = _clone_case(valid, case)
        manifest = read_json(tp)
        manifest["schema"] = "attacker-manifest/1"
        write_json(tp, manifest)
        result = audit(
            rp,
            bp,
            mp,
            trust_manifest_path=tp,
            trust_manifest_sha256=sha256_file(tp),
        )
        assert result["break_stage"] == "trust_manifest"

        case = base / "wrong_manifest_fingerprint_algorithm"
        rp, bp, mp, tp = _clone_case(valid, case)
        manifest = read_json(tp)
        manifest["candidate_fingerprint_algorithm"] = "unversioned"
        write_json(tp, manifest)
        result = audit(
            rp,
            bp,
            mp,
            trust_manifest_path=tp,
            trust_manifest_sha256=sha256_file(tp),
        )
        assert result["break_stage"] == "trust_manifest"

        relocated = base / "relocated"
        rp, bp, mp, tp = _clone_case(valid, relocated)
        result = audit(rp, bp, mp, trust_manifest_path=tp, trust_manifest_sha256=manifest_pin)
        assert result["all_pass"] is True

    print(
        "PASS foundation_chain_binding_audit v0.2 self-test: "
        "anchored-positive/missing-trust/wrong-pin/semantic-status/schema-id/producer/"
        "empty-stale/smuggled/extra-key/fingerprint/digest/magic-counts/"
        "self-consistent-substitution/forged-manifest/relocation"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-run", type=pathlib.Path)
    parser.add_argument("--basin-result", type=pathlib.Path)
    parser.add_argument("--mss-result", type=pathlib.Path)
    parser.add_argument("--trust-manifest", type=pathlib.Path)
    parser.add_argument("--trust-manifest-sha256")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    missing = [
        name
        for name, value in [
            ("--root-run", args.root_run),
            ("--basin-result", args.basin_result),
            ("--mss-result", args.mss_result),
            ("--output", args.output),
        ]
        if value is None
    ]
    if missing:
        raise SystemExit(f"missing required arguments: {', '.join(missing)}")
    result = audit(
        args.root_run,
        args.basin_result,
        args.mss_result,
        trust_manifest_path=args.trust_manifest,
        trust_manifest_sha256=args.trust_manifest_sha256,
    )
    result["command"] = [sys.executable, *sys.argv]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"], "break_stage": result["break_stage"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
