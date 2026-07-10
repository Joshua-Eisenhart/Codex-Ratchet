#!/usr/bin/env python3
"""Fail-closed two-pass runner for the finite dual-solver formal scout."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = HERE / "results"
SPEC = HERE / "spec.json"
OBJECT_CARD = HERE / "wizard_v4_3_object_card.json"
Z3_SOURCE = HERE / "dual_ratchet_four_count_nonforcing_smt_v0_z3.py"
CVC5_SOURCE = HERE / "dual_ratchet_four_count_nonforcing_smt_v0_cvc5.py"
VALIDATOR = HERE / "validate_dual_ratchet_four_count_nonforcing_smt_v0.py"
WIZARD_VALIDATOR = REPO / "scripts" / "wizard_v4_3_object_preservation.py"

CANONICAL = {
    "wizard_validation": RESULTS / "wizard_v4_3_validation.json",
    "z3_raw": RESULTS / "z3_raw_solver_receipt.json",
    "cvc5_raw": RESULTS / "cvc5_raw_solver_receipt.json",
    "agreement": RESULTS / "agreement_validation.json",
    "malformed_selftest": RESULTS / "malformed_input_selftest.json",
}
DETERMINISM_RECEIPT = RESULTS / "deterministic_rerun_hashes.json"
FAILURE_RECEIPT = RESULTS / "run_failure.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
formal_admission_allowed = False
SIM_EXECUTION_KIND = "nonclassical"
TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing subprocess execution of the independent Z3 finite-cardinality search",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing subprocess execution of the independent cvc5 finite-cardinality search",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive fail-closed process control, artifact publication, hashing, and deterministic rerun comparison",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(command: list[str], logical_command: str) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    row = {
        "logical_command": logical_command,
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }
    if process.returncode != 0:
        raise RuntimeError(json.dumps(row, sort_keys=True))
    return row


def run_pass(label: str, run_dir: Path) -> tuple[dict[str, str], list[dict[str, Any]]]:
    run_dir.mkdir(parents=True, exist_ok=False)
    paths = {
        "wizard_validation": run_dir / "wizard_v4_3_validation.json",
        "z3_raw": run_dir / "z3_raw_solver_receipt.json",
        "cvc5_raw": run_dir / "cvc5_raw_solver_receipt.json",
        "agreement": run_dir / "agreement_validation.json",
        "malformed_selftest": run_dir / "malformed_input_selftest.json",
    }
    commands: list[dict[str, Any]] = []

    wizard = run_command(
        [sys.executable, str(WIZARD_VALIDATOR), "validate", "--input", str(OBJECT_CARD)],
        f"{sys.executable} scripts/wizard_v4_3_object_preservation.py validate --input {relative(OBJECT_CARD)}",
    )
    commands.append({"pass": label, **wizard})
    wizard_receipt = json.loads(wizard["stdout"])
    if wizard_receipt.get("ok") is not True:
        raise RuntimeError("Wizard v4.3 object-preservation validation did not pass")
    write_json(paths["wizard_validation"], wizard_receipt)

    commands.append(
        {
            "pass": label,
            **run_command(
                [sys.executable, str(Z3_SOURCE), "--output", str(paths["z3_raw"])],
                f"{sys.executable} {relative(Z3_SOURCE)} --output <RUN_DIR>/z3_raw_solver_receipt.json",
            ),
        }
    )
    commands.append(
        {
            "pass": label,
            **run_command(
                [sys.executable, str(CVC5_SOURCE), "--output", str(paths["cvc5_raw"])],
                f"{sys.executable} {relative(CVC5_SOURCE)} --output <RUN_DIR>/cvc5_raw_solver_receipt.json",
            ),
        }
    )
    commands.append(
        {
            "pass": label,
            **run_command(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--z3",
                    str(paths["z3_raw"]),
                    "--cvc5",
                    str(paths["cvc5_raw"]),
                    "--output",
                    str(paths["agreement"]),
                ],
                f"{sys.executable} {relative(VALIDATOR)} --z3 <RUN_DIR>/z3_raw_solver_receipt.json --cvc5 <RUN_DIR>/cvc5_raw_solver_receipt.json --output <RUN_DIR>/agreement_validation.json",
            ),
        }
    )
    commands.append(
        {
            "pass": label,
            **run_command(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--z3",
                    str(paths["z3_raw"]),
                    "--cvc5",
                    str(paths["cvc5_raw"]),
                    "--self-test",
                    "--self-test-output",
                    str(paths["malformed_selftest"]),
                ],
                f"{sys.executable} {relative(VALIDATOR)} --z3 <RUN_DIR>/z3_raw_solver_receipt.json --cvc5 <RUN_DIR>/cvc5_raw_solver_receipt.json --self-test --self-test-output <RUN_DIR>/malformed_input_selftest.json",
            ),
        }
    )

    for artifact, path in paths.items():
        if not path.is_file():
            raise RuntimeError(f"pass {label} did not emit {artifact}")
    agreement = json.loads(paths["agreement"].read_text(encoding="utf-8"))
    selftest = json.loads(paths["malformed_selftest"].read_text(encoding="utf-8"))
    if agreement.get("all_pass") is not True or selftest.get("all_pass") is not True:
        raise RuntimeError(f"pass {label} failed agreement or malformed-input validation")
    return {artifact: sha256(path) for artifact, path in paths.items()}, commands


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    missing = [name for name in ("z3", "cvc5") if importlib.util.find_spec(name) is None]
    if missing:
        failure = {
            "schema": "codex_ratchet.dual_ratchet_four_count_nonforcing_smt_v0.failure.v1",
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "reason": "required_solver_missing",
            "missing_python_modules": missing,
            "all_pass": False,
        }
        write_json(FAILURE_RECEIPT, failure)
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 1

    run_dirs = [RESULTS / "_determinism_run_a", RESULTS / "_determinism_run_b"]
    for run_dir in run_dirs:
        if run_dir.exists():
            shutil.rmtree(run_dir)
    if FAILURE_RECEIPT.exists():
        FAILURE_RECEIPT.unlink()

    try:
        hashes_a, commands_a = run_pass("A", run_dirs[0])
        hashes_b, commands_b = run_pass("B", run_dirs[1])
        artifact_matches = {
            artifact: hashes_a[artifact] == hashes_b[artifact] for artifact in hashes_a
        }
        if not all(artifact_matches.values()):
            raise RuntimeError(f"deterministic rerun hash mismatch: {artifact_matches}")

        for artifact, canonical_path in CANONICAL.items():
            shutil.copyfile(run_dirs[0] / canonical_path.name, canonical_path)
        agreement = json.loads(CANONICAL["agreement"].read_text(encoding="utf-8"))
        z3_receipt = json.loads(CANONICAL["z3_raw"].read_text(encoding="utf-8"))
        cvc5_receipt = json.loads(CANONICAL["cvc5_raw"].read_text(encoding="utf-8"))
        determinism = {
            "schema": "codex_ratchet.dual_ratchet_four_count_nonforcing_smt_v0.determinism.v1",
            "sim_id": json.loads(SPEC.read_text(encoding="utf-8"))["sim_id"],
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "python_executable": sys.executable,
            "required_solver_modules": {"z3": True, "cvc5": True},
            "solver_versions": {
                "z3": z3_receipt["solver"]["version"],
                "cvc5": cvc5_receipt["solver"]["version"],
            },
            "source_hashes": {
                relative(SPEC): sha256(SPEC),
                relative(OBJECT_CARD): sha256(OBJECT_CARD),
                relative(Z3_SOURCE): sha256(Z3_SOURCE),
                relative(CVC5_SOURCE): sha256(CVC5_SOURCE),
                relative(VALIDATOR): sha256(VALIDATOR),
                relative(Path(__file__).resolve()): sha256(Path(__file__).resolve()),
            },
            "run_a_hashes": hashes_a,
            "run_b_hashes": hashes_b,
            "artifact_hashes_match": artifact_matches,
            "canonical_artifact_hashes": {
                artifact: sha256(path) for artifact, path in CANONICAL.items()
            },
            "commands": [*commands_a, *commands_b],
            "scientific_verdict": agreement["scientific_verdict"],
            "all_pass": agreement["all_pass"] is True and all(artifact_matches.values()),
        }
        write_json(DETERMINISM_RECEIPT, determinism)
        for run_dir in run_dirs:
            shutil.rmtree(run_dir)
        print(
            json.dumps(
                {
                    "scientific_verdict": determinism["scientific_verdict"],
                    "solver_versions": determinism["solver_versions"],
                    "artifact_hashes_match": artifact_matches,
                    "canonical_artifact_hashes": determinism["canonical_artifact_hashes"],
                    "all_pass": determinism["all_pass"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if determinism["all_pass"] else 1
    except Exception as exc:
        failure = {
            "schema": "codex_ratchet.dual_ratchet_four_count_nonforcing_smt_v0.failure.v1",
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "reason": "fail_closed_runner_error",
            "error": str(exc),
            "all_pass": False,
        }
        write_json(FAILURE_RECEIPT, failure)
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
