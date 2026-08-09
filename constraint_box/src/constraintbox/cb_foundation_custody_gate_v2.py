#!/usr/bin/env python3
"""Receipt-bound custody gate for a contained CB external-workload packet.

This is intentionally not a release/admission/physics gate.  It binds three
already-produced objects to controller-recorded SHA-256 values:

1. a sealed-artifact integrity receipt from ``strict_receipt_consumer_v2``;
2. the CB-facing external-workload receipt; and
3. the cross-runtime NumPy/JAX/PyTorch/Julia receipt.

The program recomputes source/output bindings and lane-result hashes directly
from the artifact root.  It does not accept producer ``all_pass`` or
``consumer_verdict`` values as its own decision.  Its only green state is
``evidence_packet_ready``; manifold, engine admission, and Holodeck use remain
separate downstream gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_EXECUTIONS = {
    "fep",
    "hopfield",
    "hopf",
    "spinor",
    "type1",
    "type2",
    "cross_runtime",
    "hierarchy",
    "deformations",
}
EXPECTED_LANE_EXECUTIONS = {
    "1q_numpy_oracle",
    "1q_jax",
    "1q_torch",
    "1q_julia",
    "3q_numpy_oracle",
    "3q_jax",
    "3q_torch",
    "3q_julia",
}
EXPECTED_NUMERICAL_LANES = {"jax", "torch", "julia"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_beneath(root: Path, relative: str) -> tuple[Path | None, str | None]:
    raw = Path(relative)
    if raw.is_absolute():
        return None, "absolute path"
    candidate = (root / raw).resolve()
    try:
        return candidate, str(candidate.relative_to(root))
    except ValueError:
        return None, "path escapes artifact root"


def trusted_json(label: str, path: Path, expected_sha256: str) -> tuple[dict[str, Any], list[str], str]:
    errors: list[str] = []
    expected = expected_sha256.lower()
    if not HEX64.fullmatch(expected):
        return {}, [f"{label}: expected SHA-256 is invalid"], ""
    if not path.is_file():
        return {}, [f"{label}: receipt does not exist"], ""
    actual = sha256(path)
    if actual != expected:
        errors.append(f"{label}: receipt SHA-256 mismatches controller anchor")
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"{label}: receipt is not valid JSON: {type(exc).__name__}")
        data = {}
    if not isinstance(data, dict):
        errors.append(f"{label}: receipt root is not an object")
        data = {}
    return data, errors, actual


def hash_mapping(
    *,
    root: Path,
    mapping: Any,
    label: str,
    prefix: str = "",
) -> tuple[list[str], int]:
    """Recompute a path-qualified mapping, rejecting escapes and bare paths."""
    errors: list[str] = []
    matched = 0
    if not isinstance(mapping, dict) or not mapping:
        return [f"{label}: hash mapping missing or empty"], 0
    for relative, declared in mapping.items():
        if not isinstance(relative, str) or not isinstance(declared, str) or not HEX64.fullmatch(declared):
            errors.append(f"{label}: invalid declaration")
            continue
        combined = f"{prefix}/{relative}" if prefix else relative
        if "/" not in combined and "\\" not in combined:
            errors.append(f"{label}: bare path is not a stable artifact identity: {relative}")
            continue
        path, rel_or_error = resolve_beneath(root, combined)
        if path is None:
            errors.append(f"{label}: {relative}: {rel_or_error}")
            continue
        if not path.is_file():
            errors.append(f"{label}: declared file absent: {rel_or_error}")
            continue
        actual = sha256(path)
        if actual != declared:
            errors.append(f"{label}: digest mismatch: {rel_or_error}")
            continue
        matched += 1
    return errors, matched


def foundation_checks(root: Path, receipt: dict[str, Any]) -> tuple[dict[str, bool], list[str], dict[str, Any]]:
    errors: list[str] = []
    conditions: dict[str, bool] = {}
    detail: dict[str, Any] = {}
    conditions["foundation_schema"] = receipt.get("receipt_kind") == "candidate_cb_external_workload_gate"
    if not conditions["foundation_schema"]:
        errors.append("foundation: unexpected receipt_kind")
    source_errors, source_matched = hash_mapping(
        root=root, mapping=receipt.get("source_hashes"), label="foundation.source_hashes"
    )
    output_errors, output_matched = hash_mapping(
        root=root, mapping=receipt.get("output_hashes"), label="foundation.output_hashes"
    )
    errors.extend(source_errors)
    errors.extend(output_errors)
    conditions["foundation_hash_bindings"] = not source_errors and not output_errors
    executions = receipt.get("executions")
    if not isinstance(executions, dict):
        errors.append("foundation: executions map missing")
        executions = {}
    missing = sorted(EXPECTED_EXECUTIONS - set(executions))
    bad_execution = []
    for name in EXPECTED_EXECUTIONS & set(executions):
        entry = executions[name]
        if not isinstance(entry, dict) or entry.get("ran") is not True or entry.get("exit_code") != 0:
            bad_execution.append(name)
    if missing:
        errors.append("foundation: missing execution records: " + ", ".join(missing))
    if bad_execution:
        errors.append("foundation: nonzero or incomplete execution records: " + ", ".join(sorted(bad_execution)))
    conditions["foundation_execution_records"] = not missing and not bad_execution
    overall = receipt.get("overall") if isinstance(receipt.get("overall"), dict) else {}
    conditions["foundation_tooling_record"] = overall.get("all_workloads_executed") is True and overall.get("tooling_gate") is True
    if not conditions["foundation_tooling_record"]:
        errors.append("foundation: workload/tooling record is incomplete")
    conditions["foundation_policy_nonpromotion"] = (
        receipt.get("promotion_allowed") is False
        and overall.get("downstream_engine_consumption_allowed") is False
    )
    if not conditions["foundation_policy_nonpromotion"]:
        errors.append("foundation: promotion/downstream policy is not fail-closed")
    conditions["paired_genealogy_still_blocked"] = overall.get("paired_genealogy_gate") == "fail"
    if not conditions["paired_genealogy_still_blocked"]:
        errors.append("foundation: expected unclosed paired-genealogy state was not explicit")
    detail.update({
        "source_bindings_matched": source_matched,
        "output_bindings_matched": output_matched,
        "expected_execution_count": len(EXPECTED_EXECUTIONS),
        "recorded_execution_count": len(executions),
        "paired_genealogy_gate": overall.get("paired_genealogy_gate"),
    })
    return conditions, errors, detail


def cross_runtime_checks(root: Path, receipt: dict[str, Any]) -> tuple[dict[str, bool], list[str], dict[str, Any]]:
    errors: list[str] = []
    conditions: dict[str, bool] = {}
    detail: dict[str, Any] = {}
    conditions["cross_runtime_schema"] = receipt.get("receipt_kind") == "candidate_cb_cross_runtime_contract_gate"
    if not conditions["cross_runtime_schema"]:
        errors.append("cross-runtime: unexpected receipt_kind")
    engine_dir = receipt.get("engine_directory")
    if not isinstance(engine_dir, str) or not engine_dir:
        errors.append("cross-runtime: engine_directory missing")
        engine_dir = ""
    source_errors, source_matched = hash_mapping(
        root=root,
        mapping=receipt.get("source_hashes"),
        label="cross_runtime.source_hashes",
        prefix=engine_dir,
    )
    errors.extend(source_errors)
    conditions["cross_runtime_source_bindings"] = not source_errors
    executions = receipt.get("lane_executions")
    if not isinstance(executions, list):
        errors.append("cross-runtime: lane_executions missing")
        executions = []
    execution_map = {entry.get("name"): entry for entry in executions if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    missing_exec = sorted(EXPECTED_LANE_EXECUTIONS - set(execution_map))
    bad_exec = [name for name in EXPECTED_LANE_EXECUTIONS & set(execution_map) if execution_map[name].get("exit_code") != 0]
    if missing_exec:
        errors.append("cross-runtime: missing lane executions: " + ", ".join(missing_exec))
    if bad_exec:
        errors.append("cross-runtime: nonzero lane executions: " + ", ".join(sorted(bad_exec)))
    conditions["all_eight_lane_commands_exercised"] = not missing_exec and not bad_exec
    result_hash_errors: list[str] = []
    minimum_distances: dict[str, float] = {}
    for scale, section_name, suffix in (("1q", "one_qubit_contract", ""), ("3q", "three_qubit_contract", "_3q")):
        section = receipt.get(section_name)
        lanes = section.get("lanes") if isinstance(section, dict) else None
        if not isinstance(lanes, dict) or set(lanes) != EXPECTED_NUMERICAL_LANES:
            result_hash_errors.append(f"cross-runtime: {scale} lane set is not exactly jax/torch/julia")
            continue
        for lane in EXPECTED_NUMERICAL_LANES:
            lane_result = lanes[lane]
            if not isinstance(lane_result, dict):
                result_hash_errors.append(f"cross-runtime: {scale}/{lane} result missing")
                continue
            if lane_result.get("errors") != []:
                result_hash_errors.append(f"cross-runtime: {scale}/{lane} reports errors")
            digest_declared = lane_result.get("result_hash")
            result_path = f"{engine_dir}/{lane}_results{suffix}.json"
            path, rel_or_error = resolve_beneath(root, result_path)
            if path is None or not path.is_file() or not isinstance(digest_declared, str) or not HEX64.fullmatch(digest_declared):
                result_hash_errors.append(f"cross-runtime: {scale}/{lane} result binding invalid")
                continue
            if sha256(path) != digest_declared:
                result_hash_errors.append(f"cross-runtime: {scale}/{lane} result digest mismatch: {rel_or_error}")
            try:
                distance = float(lane_result["min_pairwise_distance"])
                minimum_distances[f"{scale}/{lane}"] = distance
                if distance <= 0.0:
                    result_hash_errors.append(f"cross-runtime: {scale}/{lane} has nonpositive separation")
            except (KeyError, TypeError, ValueError):
                result_hash_errors.append(f"cross-runtime: {scale}/{lane} separation is not numeric")
    errors.extend(result_hash_errors)
    conditions["cross_runtime_result_bindings"] = not result_hash_errors
    overall = receipt.get("overall") if isinstance(receipt.get("overall"), dict) else {}
    conditions["cross_runtime_fresh_record"] = receipt.get("fresh_rerun_requested") is True and overall.get("all_requested_lane_commands_exit_zero") is True
    if not conditions["cross_runtime_fresh_record"]:
        errors.append("cross-runtime: fresh execution record is incomplete")
    conditions["cross_runtime_policy_nonpromotion"] = (
        receipt.get("promotion_allowed") is False
        and receipt.get("formal_admission_allowed") is False
        and overall.get("downstream_engine_admission_allowed") is False
    )
    if not conditions["cross_runtime_policy_nonpromotion"]:
        errors.append("cross-runtime: policy is not fail-closed")
    detail.update({
        "source_bindings_matched": source_matched,
        "lane_execution_count": len(execution_map),
        "minimum_pairwise_distances": minimum_distances,
        "legacy_validator_diagnostic": overall.get("source_validator_integration"),
    })
    return conditions, errors, detail


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--integrity-receipt", required=True, type=Path)
    parser.add_argument("--expected-integrity-sha256", required=True)
    parser.add_argument("--foundation-receipt", required=True, type=Path)
    parser.add_argument("--expected-foundation-sha256", required=True)
    parser.add_argument("--cross-runtime-receipt", required=True, type=Path)
    parser.add_argument("--expected-cross-runtime-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    root = args.artifact_root.resolve()
    output = args.output.resolve()
    if not root.is_dir():
        print("CONFIGURATION ERROR: artifact root does not exist", file=sys.stderr)
        return 2
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        print("CONFIGURATION ERROR: output must be outside artifact root", file=sys.stderr)
        return 2

    integrity, integrity_errors, integrity_actual = trusted_json("integrity", args.integrity_receipt.resolve(), args.expected_integrity_sha256)
    foundation, foundation_errors, foundation_actual = trusted_json("foundation", args.foundation_receipt.resolve(), args.expected_foundation_sha256)
    cross, cross_errors, cross_actual = trusted_json("cross-runtime", args.cross_runtime_receipt.resolve(), args.expected_cross_runtime_sha256)
    for label, path, errors in (
        ("foundation", args.foundation_receipt.resolve(), foundation_errors),
        ("cross-runtime", args.cross_runtime_receipt.resolve(), cross_errors),
    ):
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"{label}: receipt must live inside the sealed artifact root")

    integrity_conditions = {
        "integrity_schema": integrity.get("schema") == "cb.strict-recomputing-consumer.v2",
        "integrity_root_matches": Path(str(integrity.get("artifact_root", ""))).resolve() == root,
        "integrity_receipt_anchor_matched": integrity.get("receipt_hash_match") is True,
        "sealed_scope_complete": integrity.get("sealed_scope_complete") is True,
        "integrity_pass": integrity.get("integrity_pass") is True,
        "integrity_is_not_semantic_verdict": integrity.get("semantic_verdict") == "not_evaluated",
    }
    for name, ok in integrity_conditions.items():
        if not ok:
            integrity_errors.append(f"integrity: {name} is false")

    foundation_conditions, foundation_check_errors, foundation_detail = foundation_checks(root, foundation)
    cross_conditions, cross_check_errors, cross_detail = cross_runtime_checks(root, cross)
    all_errors = integrity_errors + foundation_errors + cross_errors + foundation_check_errors + cross_check_errors
    custody_conditions = {**integrity_conditions, **foundation_conditions, **cross_conditions}
    evidence_packet_ready = not all_errors and all(custody_conditions.values())

    result = {
        "schema": "cb.foundation-custody-gate.v2",
        "artifact_root": str(root),
        "input_receipt_hashes": {
            "integrity": integrity_actual,
            "foundation": foundation_actual,
            "cross_runtime": cross_actual,
        },
        "conditions": custody_conditions,
        "detail": {
            "foundation": foundation_detail,
            "cross_runtime": cross_detail,
            "errors": all_errors,
        },
        "evidence_packet_ready": evidence_packet_ready,
        "package_release_allowed": False,
        "formal_admission_allowed": False,
        "downstream_engine_or_holodeck_allowed": False,
        "blocked_consumers": [
            "paired-nested-2-to-4-to-16-genealogy",
            "engine-admission",
            "holodeck-world-model-admission",
            "CR-or-physics-truth",
        ],
        "claim_ceiling": "fresh, sealed workload-custody and lane-execution evidence only; no manifold completion, engine admission, Holodeck claim, or scientific claim",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"evidence_packet_ready={evidence_packet_ready}")
    for name, ok in sorted(custody_conditions.items()):
        print(f"{name}={'PASS' if ok else 'FAIL'}")
    for error in all_errors:
        print(f"DEFECT: {error}")
    return 0 if evidence_packet_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
