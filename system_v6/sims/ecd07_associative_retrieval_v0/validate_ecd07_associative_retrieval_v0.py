#!/usr/bin/env python3
"""Packet-local validator for the ECD.07 associative retrieval discriminator."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import ecd07_associative_retrieval_v0_boundary as boundary
import ecd07_associative_retrieval_v0_common as common


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_envelope.py",
    f"{common.SIM_ID}_boundary.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_jax_results.json",
    f"results/{common.SIM_ID}_pytorch_results.json",
    f"results/{common.SIM_ID}_julia_results.json",
    f"results/{common.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], label: str) -> dict[str, Any]:
    require(errors, isinstance(value, dict), f"{label} must be an object")
    return value if isinstance(value, dict) else {}


def hash_exists_in_git_history(expected_hash: str | None, path: Any) -> bool:
    if not expected_hash:
        return False
    rel_path = common.rel(path)
    try:
        commits = subprocess.check_output(
            ["git", "log", "--format=%H", "--", rel_path],
            cwd=common.ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except (OSError, subprocess.CalledProcessError):
        return False
    for commit in commits:
        try:
            blob = subprocess.check_output(
                ["git", "show", f"{commit}:{rel_path}"],
                cwd=common.ROOT,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            continue
        if hashlib.sha256(blob).hexdigest() == expected_hash:
            return True
    return False


def source_hash_valid(name: str, row: dict[str, Any], path: Any) -> bool:
    if row.get("sha256") == common.sha256_file(path):
        return True
    return name == "ecd_supplement_1" and hash_exists_in_git_history(row.get("sha256"), path)


def validate_source_locks(errors: list[str], payload: dict[str, Any]) -> None:
    locks = as_dict(payload.get("source_locks"), errors, "source_locks")
    require(errors, set(locks) == set(common.AUTHORITY_PATHS), "source lock set mismatch")
    for name, path in common.AUTHORITY_PATHS.items():
        row = as_dict(locks.get(name), errors, f"source_locks.{name}")
        require(errors, row.get("exists") is True, f"{name} source missing")
        require(errors, source_hash_valid(name, row, path), f"{name} source hash drift")
        if common.USER_HASH_HINTS.get(name):
            require(errors, row.get("user_supplied_hash_hint") == common.USER_HASH_HINTS[name], f"{name} hint mismatch")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing packet file: {rel_path}")
    require(errors, payload.get("schema_version") == common.SCHEMA_VERSION, "schema version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim id mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    validate_source_locks(errors, payload)
    errors.extend(boundary.boundary_errors(payload, common.SIM_DIR))

    cap = as_dict(payload.get("capacity"), errors, "capacity")
    require(errors, len(cap.get("rows", [])) == len(common.CAPACITY_PATTERN_COUNTS), "capacity curve row count mismatch")
    require(errors, "qit_minus_classical_capacity" in cap, "capacity margin missing")
    controls = as_dict(payload.get("controls"), errors, "controls")
    require(errors, controls.get("pinned_random_base_rate", {}).get("chance_accuracy") == 0.25, "pinned random base rate drift")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof failed")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof failed")
    require(errors, proofs.get("z3", {}).get("accepted_relation") == proofs.get("cvc5", {}).get("accepted_relation"), "solver relation mismatch")

    if common.ENVELOPE_PATH.exists():
        env = common.load_json(common.ENVELOPE_PATH)
        require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "envelope schema mismatch")
        require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
        require(errors, env.get("mode") == "all_three_full_sims", "envelope mode mismatch")
        errors.extend(boundary.boundary_errors(env, common.SIM_DIR))
        cmd = [
            sys.executable,
            str(common.ROOT / "scripts" / "validate_three_engine_sim_result.py"),
            "--require-pytorch",
            str(common.ENVELOPE_PATH),
        ]
        proc = subprocess.run(cmd, cwd=common.ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0:
            errors.append("three-engine envelope validator failed: " + (proc.stdout + proc.stderr).strip())
    else:
        errors.append("missing envelope")
    return errors


def main() -> int:
    if not common.RESULT_PATH.exists():
        errors = ["missing base result"]
    else:
        errors = validate_payload(common.load_json(common.RESULT_PATH))
    result = {
        "ok": not errors,
        "result_json": common.rel(common.RESULT_PATH),
        "envelope_json": common.rel(common.ENVELOPE_PATH),
        "errors": errors,
    }
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
