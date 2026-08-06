#!/usr/bin/env python3
"""Verify a contained ConstraintBox core ZIP from a fresh extraction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "constraintbox.contained-core-verification.v2"
MANIFEST_NAME = "CONTAINMENT_MANIFEST.json"
BOUNDARY_NAME = "PRODUCT_BOUNDARY.md"
MANIFEST_KEYS = frozenset(
    {
        "schema",
        "bundle_kind",
        "package_name",
        "package_version",
        "top_level",
        "source_root",
        "file_count",
        "files",
        "included_directories",
        "excluded_parts",
        "external_estate_included",
        "promotion_allowed",
    }
)


class VerificationError(ValueError):
    """The archive is not the declared contained-core source artifact."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json_object(value: bytes, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value, object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError, VerificationError) as exc:
        raise VerificationError(f"invalid {label}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise VerificationError(f"{label} must be an object")
    return parsed


def _safe_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise VerificationError(f"unsafe archive path: {name!r}")
    return path


def _validate_archive(archive: zipfile.ZipFile) -> tuple[str, dict[str, Any], dict[str, int]]:
    names = archive.namelist()
    if not names or len(names) != len(set(names)):
        raise VerificationError("archive is empty or contains duplicate members")
    paths = [_safe_path(name) for name in names]
    for info, path in zip(archive.infolist(), paths, strict=True):
        if stat.S_ISLNK(info.external_attr >> 16):
            raise VerificationError(f"archive symlink member is forbidden: {path}")
    roots = {path.parts[0] for path in paths}
    if len(roots) != 1:
        raise VerificationError("archive must have exactly one top-level directory")
    top = next(iter(roots))
    manifest_member = f"{top}/{MANIFEST_NAME}"
    boundary_member = f"{top}/{BOUNDARY_NAME}"
    if manifest_member not in names or boundary_member not in names:
        raise VerificationError("archive is missing containment metadata")
    manifest = _json_object(archive.read(manifest_member), "containment manifest")
    if set(manifest) != MANIFEST_KEYS:
        raise VerificationError("containment manifest keys differ from v1 contract")
    if manifest["schema"] != "constraintbox.contained-core-manifest.v1":
        raise VerificationError("unsupported containment manifest schema")
    if manifest["bundle_kind"] != "contained-core-source":
        raise VerificationError("archive is not a contained core source bundle")
    if manifest["top_level"] != top or manifest["source_root"] != "constraint_box":
        raise VerificationError("manifest does not match archive layout")
    if manifest["external_estate_included"] is not False or manifest["promotion_allowed"] is not False:
        raise VerificationError("contained core has an invalid authority boundary")
    rows = manifest["files"]
    if not isinstance(rows, list) or type(manifest["file_count"]) is not int or len(rows) != manifest["file_count"]:
        raise VerificationError("manifest files/file_count mismatch")
    expected_members = {manifest_member, boundary_member}
    seen: set[str] = set()
    payload_bytes = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise VerificationError(f"manifest files[{index}] has invalid fields")
        path = row["path"]
        if not isinstance(path, str) or not path or path in seen:
            raise VerificationError(f"manifest files[{index}].path is invalid")
        relative = _safe_path(path)
        if any(
            part in {
                "external_sim_estate",
                "receipts",
                "results",
                ".DS_Store",
                ".AppleDouble",
            }
            for part in relative.parts
        ):
            raise VerificationError(f"forbidden payload path: {path}")
        if type(row["bytes"]) is not int or row["bytes"] < 0:
            raise VerificationError(f"manifest files[{index}].bytes is invalid")
        if not isinstance(row["sha256"], str) or len(row["sha256"]) != 64:
            raise VerificationError(f"manifest files[{index}].sha256 is invalid")
        member = f"{top}/constraint_box/{path}"
        if member not in names:
            raise VerificationError(f"manifest member is missing: {path}")
        payload = archive.read(member)
        if len(payload) != row["bytes"] or _sha256(payload) != row["sha256"]:
            raise VerificationError(f"manifest digest mismatch: {path}")
        expected_members.add(member)
        seen.add(path)
        payload_bytes += len(payload)
    if set(names) != expected_members:
        unexpected = sorted(set(names) - expected_members)
        missing = sorted(expected_members - set(names))
        raise VerificationError(f"archive membership differs from manifest: unexpected={unexpected[:3]}, missing={missing[:3]}")
    return top, manifest, {"payload_file_count": len(seen), "payload_bytes": payload_bytes}


def _run(
    root: Path,
    python: Path,
    name: str,
    argv: list[str],
    expected_exit: int,
    expected_fields: dict[str, Any] | None = None,
    *,
    constraintbox_cli: bool = True,
) -> dict[str, Any]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            [
                str(python),
                "-B",
                *(["-m", "constraintbox"] if constraintbox_cli else []),
                *argv,
            ],
            cwd=root,
            env=environment,
            capture_output=True,
            check=False,
            timeout=60,
        )
        code, stdout, stderr, timed_out = completed.returncode, completed.stdout, completed.stderr, False
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr, timed_out = 124, exc.stdout or b"", exc.stderr or b"", True
    parsed: dict[str, Any] | None
    try:
        parsed = _json_object(stdout, f"{name} stdout")
    except VerificationError:
        parsed = None
    field_match = True
    if expected_fields:
        field_match = parsed is not None and all(parsed.get(key) == value for key, value in expected_fields.items())
    result = {
        "name": name,
        "argv": argv,
        "expected_exit": expected_exit,
        "actual_exit": code,
        "timed_out": timed_out,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "expected_fields": expected_fields or {},
        "passed": code == expected_exit and not timed_out and field_match,
    }
    if not result["passed"]:
        result["stdout_head"] = stdout.decode("utf-8", errors="replace")[:1_000]
        result["stderr_head"] = stderr.decode("utf-8", errors="replace")[:1_000]
    return result


def verify_bundle(bundle: Path) -> dict[str, Any]:
    if not bundle.is_file():
        raise VerificationError(f"bundle does not exist: {bundle}")
    # The portable profile is evaluated by the interpreter that runs this
    # verifier.  The verifier must not accept a second, host-pinned executable
    # path or silently substitute a different interpreter.
    # Do not resolve a virtual-environment launcher symlink here.  Resolving it
    # can replace the active environment with its base interpreter and make
    # compatible installed core libraries disappear.  `sys.executable` is the
    # interpreter that owns this verifier's import environment; its resolved
    # target is recorded by `constraintbox runtime verify` as observation.
    python = Path(sys.executable).absolute()
    if not python.is_file():
        raise VerificationError(f"active verifier interpreter does not exist: {python}")
    with zipfile.ZipFile(bundle) as archive:
        top, manifest, inventory = _validate_archive(archive)
        with tempfile.TemporaryDirectory(prefix="constraintbox-contained-core-") as directory:
            destination = Path(directory)
            archive.extractall(destination)
            root = destination / top / "constraint_box"
            commands = [
                _run(
                    root,
                    python,
                    "runtime_verify",
                    ["runtime", "verify"],
                    0,
                    {"state": "ELIGIBLE", "promotion_allowed": False},
                ),
                _run(root, python, "demo", ["demo"], 0),
                _run(root, python, "mmm_smt", ["mmm", "smt", "--json"], 0),
                _run(
                    root,
                    python,
                    "request_missing_assumptions",
                    ["request", "--request", "fixtures/requests/needs_assumptions_v1.json"],
                    4,
                ),
                _run(
                    root,
                    python,
                    "formal_symbolic",
                    [
                        "formal",
                        "run",
                        "--task",
                        "formal.symbolic.polynomial_qq",
                        "--request-id",
                        "contained-core-symbolic",
                        "--payload",
                        "fixtures/formal/symbolic_polynomial_valid.json",
                        "--run-dir",
                        str(root / ".contained-verification" / "symbolic"),
                    ],
                    0,
                ),
                _run(
                    root,
                    python,
                    "formal_boundary_contract_valid",
                    [
                        "formal",
                        "run",
                        "--task",
                        "formal.boundary.constraintbox_scope",
                        "--request-id",
                        "contained-core-boundary-valid",
                        "--payload",
                        "fixtures/formal/boundary_contract_valid.json",
                        "--run-dir",
                        str(root / ".contained-verification" / "boundary-valid"),
                    ],
                    0,
                    {"disposition": "ELIGIBLE", "promotion_allowed": False},
                ),
                _run(
                    root,
                    python,
                    "formal_boundary_contract_conflation_blocks",
                    [
                        "formal",
                        "run",
                        "--task",
                        "formal.boundary.constraintbox_scope",
                        "--request-id",
                        "contained-core-boundary-conflated",
                        "--payload",
                        "fixtures/formal/boundary_contract_conflated_sim_as_cb_core.json",
                        "--run-dir",
                        str(root / ".contained-verification" / "boundary-conflated"),
                    ],
                    1,
                    {"disposition": "BLOCKED", "reason": "boundary_role_conflation"},
                ),
                _run(
                    root,
                    python,
                    "boundary_contract_regression_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_boundary_contract.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "formal_maude_transition",
                    [
                        "formal",
                        "run",
                        "--task",
                        "formal.transition.current_box_phase",
                        "--request-id",
                        "contained-core-maude",
                        "--payload",
                        "fixtures/formal/phase_transition_valid.json",
                        "--run-dir",
                        str(root / ".contained-verification" / "maude"),
                    ],
                    0,
                    {"disposition": "ELIGIBLE", "promotion_allowed": False},
                ),
                _run(
                    root,
                    python,
                    "formal_levos_flowmind_pinned_topology",
                    [
                        "formal",
                        "run",
                        "--task",
                        "formal.levos.flowmind_contract_structure",
                        "--request-id",
                        "contained-core-levos-flowmind",
                        "--payload",
                        "fixtures/formal/levos_flowmind_dna_compile_pinned_topology_fixture.json",
                        "--run-dir",
                        str(root / ".contained-verification" / "levos-flowmind"),
                    ],
                    0,
                    {"disposition": "ELIGIBLE", "promotion_allowed": False},
                ),
                _run(
                    root,
                    python,
                    "failure_repair_contained_contract_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_failure_repair_contained.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "execution_lease_minilev_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_execution_lease_minilev.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "integrated_receipt_lease_minilev_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_integrated_minilev.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "proposal_minilev_rustworkx_topology_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_proposal_minilev_flow.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "foreign_lev_eval_observation_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_lev_eval_observation.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "foreign_lev_eval_observation_minilev_flow_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_lev_eval_observation_flow.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "leviathan_minilev_reference_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_leviathan_reference.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "external_validation_runner_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_external_validation_runner.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "hypothesis_adversarial_intake_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_hypothesis_adversarial.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "external_validation_index_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_external_validation_index.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "contained_provider_harness_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_contained_provider_harness.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "proposal_provider_policy_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_proposal_provider_policy.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "attractor_basin_adapter_boundary_unit",
                    [
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_attractor_basin_adapter.py",
                        "-q",
                    ],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "attractor_basin_controller_cli_surface",
                    ["workers/attractor_basin_v1/basin_controller.py", "--help"],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "attractor_basin_envelope_verifier_cli_surface",
                    ["scripts/verify_attractor_basin_envelope.py", "--help"],
                    0,
                    constraintbox_cli=False,
                ),
                _run(
                    root,
                    python,
                    "external_estate_absent_is_parked",
                    [
                        "box",
                        "--request",
                        "fixtures/requests/assemble_constraintbox_v1.json",
                        "--run-dir",
                        str(root / ".contained-verification" / "external-estate-absent"),
                    ],
                    4,
                    {"disposition": "PARKED"},
                ),
                _run(
                    root,
                    python,
                    "in_box_claimgate_admitted_fixture",
                    ["gate", "claimgate_plugin/fixtures/hook_clean_receipt.json"],
                    0,
                    {"disposition": "ADMITTED", "chain_root_inside_box": True},
                ),
                _run(
                    root,
                    python,
                    "in_box_claimgate_insufficient_depth_fixture",
                    ["gate", "claimgate_plugin/fixtures/receipt_honest.json"],
                    3,
                    {"disposition": "INSUFFICIENT_DEPTH", "chain_root_inside_box": True},
                ),
            ]
    passed = all(command["passed"] for command in commands)
    return {
        "schema": SCHEMA,
        "bundle": str(bundle),
        "bundle_sha256": _sha256(bundle.read_bytes()),
        "verification_interpreter": str(python),
        "manifest": {
            "package_name": manifest["package_name"],
            "package_version": manifest["package_version"],
            **inventory,
        },
        "commands": commands,
        "state": "VERIFIED" if passed else "FAILED",
        "external_estate_included": False,
        "promotion_allowed": False,
    }


def _write_receipt(path: Path, result: dict[str, Any]) -> None:
    if path.exists():
        raise VerificationError(f"refusing to overwrite existing receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument(
        "--receipt",
        type=Path,
        help="new JSON receipt path; an existing file is never replaced",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = verify_bundle(args.bundle.resolve())
        if args.receipt is not None:
            receipt = args.receipt.expanduser()
            if not receipt.is_absolute():
                receipt = (Path.cwd() / receipt).absolute()
            _write_receipt(receipt, result)
    except (VerificationError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"schema": SCHEMA, "state": "FAILED", "error": str(exc), "promotion_allowed": False}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
