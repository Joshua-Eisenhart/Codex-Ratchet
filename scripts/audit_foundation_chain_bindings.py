#!/usr/bin/env python3
"""Fail-closed provenance audit for a root -> basin -> MSS receipt chain.

This tool does not promote any scientific result.  It answers one narrower
question: did one exact root candidate, with the required root constraints,
flow through the basin and MSS receipts by content hash?  Independently green
receipts are reported as unbound islands when their parent hashes are absent,
stale, replayed, or mismatched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import tempfile
from typing import Any, Iterable


SCHEMA = "foundation-chain-binding-audit/0.1"
HASH_KEYS = {
    "consumed_parent_receipt_sha256",
    "parent_receipt_sha256",
    "upstream_receipt_sha256",
    "root_receipt_sha256",
}
CANDIDATE_HASH_KEYS = {
    "consumed_candidate_content_sha256",
    "upstream_candidate_content_sha256",
    "root_candidate_content_sha256",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def read_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_items(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from iter_items(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_items(child)


def token_present(value: Any, token: str) -> bool:
    for key, child in iter_items(value):
        if key == token or child == token:
            return True
    return False


def keyed_values(value: Any, keys: set[str]) -> list[str]:
    out: list[str] = []
    for key, child in iter_items(value):
        if key in keys and isinstance(child, str):
            out.append(child.removeprefix("sha256:"))
    return out


def root_candidate(root: dict[str, Any]) -> dict[str, Any]:
    cache = root.get("frontier_cache") or {}
    members = cache.get("full_packet_frontier")
    digests = cache.get("full_packet_frontier_partition_digests")
    fingerprint = cache.get("full_packet_frontier_fingerprint")
    if isinstance(members, list) and members and isinstance(fingerprint, str):
        payload = {
            "members": members,
            "partition_digests": digests or [],
            "frontier_fingerprint": fingerprint,
        }
        return {
            "kind": "order_open_frontier",
            "members": members,
            "partition_digests": digests or [],
            "declared_fingerprint": fingerprint.removeprefix("sha256:"),
            "content_sha256": canonical_sha256(payload),
        }

    members = root.get("declared_frontier")
    candidates = root.get("candidates")
    if isinstance(members, list) and members and isinstance(candidates, list):
        selected = [row for row in candidates if isinstance(row, dict) and row.get("id") in members]
        if selected:
            payload = {"members": members, "candidate_payloads": selected}
            return {
                "kind": "declared_frontier_payload",
                "members": members,
                "partition_digests": [],
                "declared_fingerprint": None,
                "content_sha256": canonical_sha256(payload),
            }

    return {
        "kind": "missing",
        "members": [],
        "partition_digests": [],
        "declared_fingerprint": None,
        "content_sha256": None,
    }


def execution_shape(result: dict[str, Any], *, lane: str) -> dict[str, Any]:
    schema = result.get("schema") or result.get("schema_version")
    all_pass = result.get("all_pass")
    if lane == "basin":
        ran = isinstance(schema, str) and all_pass is True
    elif lane == "mss":
        counts = result.get("counts") or {}
        enumeration = result.get("enumeration") or {}
        enumerated = (
            counts.get("total_tables")
            or enumeration.get("tables_enumerated")
            or enumeration.get("operation_tables")
        )
        ran = isinstance(schema, str) and (
            all_pass is True
            or (
                enumerated == 19683
                and counts.get("candidate_count_n01") == 18954
                and counts.get("minimal_count_quotient_only") == 17752
            )
        )
    else:
        raise ValueError(lane)
    return {"schema": schema, "declared_all_pass": all_pass, "ran": bool(ran)}


def binding_check(
    child: dict[str, Any],
    *,
    expected_parent_sha256: str,
    expected_candidate_sha256: str,
) -> dict[str, Any]:
    parent_values = keyed_values(child, HASH_KEYS)
    candidate_values = keyed_values(child, CANDIDATE_HASH_KEYS)
    parent_match = expected_parent_sha256 in parent_values
    candidate_match = expected_candidate_sha256 in candidate_values

    if not parent_values:
        code = "missing_parent_receipt_hash"
    elif not parent_match:
        code = "stale_replayed_or_mismatched_parent_receipt"
    elif not candidate_values:
        code = "missing_candidate_content_hash"
    elif not candidate_match:
        code = "stale_replayed_or_mismatched_candidate_content"
    else:
        code = "bound"

    return {
        "pass": bool(parent_match and candidate_match),
        "code": code,
        "expected_parent_receipt_sha256": expected_parent_sha256,
        "observed_parent_receipt_sha256_values": sorted(set(parent_values)),
        "expected_candidate_content_sha256": expected_candidate_sha256,
        "observed_candidate_content_sha256_values": sorted(set(candidate_values)),
    }


def audit(
    root_path: pathlib.Path,
    basin_path: pathlib.Path,
    mss_path: pathlib.Path,
    *,
    required_constraints: tuple[str, ...] = ("F01", "N01"),
) -> dict[str, Any]:
    root = read_json(root_path)
    basin = read_json(basin_path)
    mss = read_json(mss_path)
    if not all(isinstance(value, dict) for value in (root, basin, mss)):
        raise ValueError("all three receipts must be JSON objects")

    root_sha = sha256_file(root_path)
    basin_sha = sha256_file(basin_path)
    mss_sha = sha256_file(mss_path)
    candidate = root_candidate(root)
    candidate_hash = candidate.get("content_sha256")
    constraint_checks = {name: token_present(root, name) for name in required_constraints}
    root_shape_pass = bool(candidate_hash and candidate.get("members"))
    constraints_pass = bool(constraint_checks and all(constraint_checks.values()))

    basin_shape = execution_shape(basin, lane="basin")
    mss_shape = execution_shape(mss, lane="mss")
    if candidate_hash:
        root_to_basin = binding_check(
            basin,
            expected_parent_sha256=root_sha,
            expected_candidate_sha256=candidate_hash,
        )
        basin_to_mss = binding_check(
            mss,
            expected_parent_sha256=basin_sha,
            expected_candidate_sha256=candidate_hash,
        )
    else:
        blocked = {
            "pass": False,
            "code": "root_candidate_content_hash_unavailable",
            "expected_parent_receipt_sha256": None,
            "observed_parent_receipt_sha256_values": [],
            "expected_candidate_content_sha256": None,
            "observed_candidate_content_sha256_values": [],
        }
        root_to_basin = dict(blocked)
        basin_to_mss = dict(blocked)

    ordered_checks = [
        ("root_candidate_extraction", root_shape_pass),
        ("root_constraint_binding", constraints_pass),
        ("basin_execution", basin_shape["ran"]),
        ("root_to_basin_binding", root_to_basin["pass"]),
        ("mss_execution", mss_shape["ran"]),
        ("basin_to_mss_binding", basin_to_mss["pass"]),
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
        "scientific_status": "joined_chain_bound" if all_pass else "blocked_unbound_islands",
        "break_stage": break_stage,
        "root_receipt_count": 1,
        "required_constraint_ids": list(required_constraints),
        "constraint_checks": constraint_checks,
        "input_receipts": {
            "root": {"path": str(root_path), "sha256": root_sha},
            "basin": {"path": str(basin_path), "sha256": basin_sha},
            "mss": {"path": str(mss_path), "sha256": mss_sha},
        },
        "root_candidate": candidate,
        "execution_shapes": {"basin": basin_shape, "mss": mss_shape},
        "bindings": {
            "root_to_basin": root_to_basin,
            "basin_to_mss": basin_to_mss,
        },
        "checks": [{"id": name, "pass": passed} for name, passed in ordered_checks],
        "claim_ceiling": (
            "Provenance binding audit only. Green child receipts do not compose unless exact parent receipt and "
            "candidate content hashes match. This receipt does not admit Axis0, a basin, MSS, a Ratchet tooth, "
            "a manifold layer, physics, or canon."
        ),
        "blocked_consumers": [
            "paired_engine_e2e",
            "full_ratchet_e2e",
            "scientific_manifold_admission",
            "lev_promotion",
        ],
    }


def synthetic_root() -> dict[str, Any]:
    return {
        "schema_version": "ratchet-order-open-run/0.5",
        "F01": {"pass": True},
        "N01": {"pass": True},
        "frontier_cache": {
            "full_packet_frontier": ["candidate-A"],
            "full_packet_frontier_partition_digests": ["partition-A"],
            "full_packet_frontier_fingerprint": "frontier-A",
        },
    }


def write_json(path: pathlib.Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="foundation-chain-binding-selftest-") as tmp:
        base = pathlib.Path(tmp)
        root_path = base / "root.json"
        basin_path = base / "basin.json"
        mss_path = base / "mss.json"
        write_json(root_path, synthetic_root())
        root = read_json(root_path)
        candidate_hash = root_candidate(root)["content_sha256"]
        root_sha = sha256_file(root_path)
        basin = {
            "schema": "basin-result/1",
            "all_pass": True,
            "input_binding": {
                "consumed_parent_receipt_sha256": root_sha,
                "consumed_candidate_content_sha256": candidate_hash,
            },
        }
        write_json(basin_path, basin)
        basin_sha = sha256_file(basin_path)
        mss = {
            "schema": "mss-result/1",
            "all_pass": True,
            "input_binding": {
                "consumed_parent_receipt_sha256": basin_sha,
                "consumed_candidate_content_sha256": candidate_hash,
            },
        }
        write_json(mss_path, mss)

        positive = audit(root_path, basin_path, mss_path)
        assert positive["all_pass"] is True
        assert positive["break_stage"] is None

        erased = dict(basin)
        erased["input_binding"] = {}
        write_json(basin_path, erased)
        erased_result = audit(root_path, basin_path, mss_path)
        assert erased_result["break_stage"] == "root_to_basin_binding"

        write_json(root_path, {"schema_version": "ratchet-order-open-run/0.5", "F01": {}, "N01": {}})
        boundary = audit(root_path, basin_path, mss_path)
        assert boundary["break_stage"] == "root_candidate_extraction"

        write_json(root_path, synthetic_root())
        root_sha = sha256_file(root_path)
        candidate_hash = root_candidate(read_json(root_path))["content_sha256"]
        demoted = dict(basin)
        demoted["input_binding"] = {
            "consumed_parent_receipt_sha256": "0" * 64,
            "consumed_candidate_content_sha256": candidate_hash,
        }
        write_json(basin_path, demoted)
        demotion_result = audit(root_path, basin_path, mss_path)
        assert demotion_result["break_stage"] == "root_to_basin_binding"
        assert demotion_result["bindings"]["root_to_basin"]["code"] == (
            "stale_replayed_or_mismatched_parent_receipt"
        )
        assert root_sha != "0" * 64

    print("PASS foundation_chain_binding_audit self-test: positive/erased/boundary/demotion")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-run", type=pathlib.Path)
    parser.add_argument("--basin-result", type=pathlib.Path)
    parser.add_argument("--mss-result", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--required-constraint", action="append", dest="required_constraints")
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
    required = tuple(args.required_constraints or ("F01", "N01"))
    result = audit(args.root_run, args.basin_result, args.mss_result, required_constraints=required)
    result["command"] = [sys.executable, *sys.argv]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"], "break_stage": result["break_stage"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
