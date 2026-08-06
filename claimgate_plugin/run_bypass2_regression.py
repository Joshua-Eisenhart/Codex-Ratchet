#!/usr/bin/env python3
"""BYPASS2 REGRESSION — six known-open gate gaps captured end to end.

This runner records today's expected disposition per fixture and fails if a
fixture moves in either direction or stops being exercised.

Exit convention (intentionally different from run_bypass_regression.py):
  0  every declared case was exercised and matched its expected disposition
  1  one or more deviations occurred, or the coverage guard tripped
  2  usage error

The machine-readable summary is written beside the fixtures with
``promotion_allowed: false``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


REPO = Path(__file__).resolve().parent.parent
BYPASS2 = REPO / "claimgate_plugin" / "fixtures" / "bypass2"
HOOK = REPO / "claimgate_plugin" / "hooks" / "post_receipt_gate.sh"
LEDGER = REPO / "claimgate_plugin" / "results" / "gate_ledger.jsonl"
CONSTRAINTBOX_SRC = REPO / "constraint_box" / "src"
CONSTRAINTBOX_WORKERS = REPO / "constraint_box" / "workers" / "estate"
ESTATE_CONTROLLER = CONSTRAINTBOX_SRC / "constraintbox" / "estate.py"
PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
SUMMARY = BYPASS2 / "bypass2_regression_v1.json"
ADMITTING = {"PASS", "ADMITTED_PENDING_DEPTH", "ADMITTED_FLOOR_PARKED"}

CASES = [
    (
        "e1",
        "prose quantitative claim invisible to scalar walk",
        "ADMITTED",
        ["e1_prose_quantitative_claim.json"],
    ),
    (
        "e2",
        "jax_density import severed but claimed operation never executed",
        "ADMITTED",
        ["e2/capability_worker.py", "e2/fixture.json"],
    ),
    (
        "e3",
        "three capability_id labels manufacture engine independence",
        "ADMITTED",
        ["e3/same_formula.py"],
    ),
    (
        "e4",
        "lease binds write-tree identity but executes export archive",
        "ADMITTED",
        ["e4/reproduce.py"],
    ),
    (
        "e5",
        "nested input yields no disposition or ledger record",
        "ADMITTED",
        ["e5/nested_input.py"],
    ),
    (
        "e6",
        "equivalent Unicode keys survive duplicate-key guard",
        "ADMITTED",
        ["e6/unicode_keys.py"],
    ),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load fixture module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_json(argv: list[str], *, env: dict[str, str] | None = None) -> tuple[int, dict]:
    proc = subprocess.run(
        argv,
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        body = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"command returned unparseable JSON (exit {proc.returncode}): "
            f"{proc.stderr[-400:]}"
        ) from exc
    return proc.returncode, body


def chain(receipt: Path) -> dict[str, Any]:
    """Fire the hook and read the disposition durably appended to its ledger."""
    before = len(LEDGER.read_bytes().splitlines()) if LEDGER.exists() else 0
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(
        [
            str(PYTHON.parent),
            "/Users/joshuaeisenhart/.volta/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]
    )
    proc = subprocess.run(
        ["sh", str(HOOK), str(receipt)],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    disposition = None
    if LEDGER.exists():
        lines = LEDGER.read_bytes().splitlines()
        if len(lines) > before:
            disposition = json.loads(lines[-1]).get("disposition")
    if disposition is None:
        raise RuntimeError(
            f"hook wrote no ledger line (exit {proc.returncode}): {proc.stderr[-400:]}"
        )
    return {
        "admitted": disposition in ADMITTING,
        "hook_exit": proc.returncode,
        "disposition": disposition,
        "receipt_sha256": _sha(receipt),
    }


def run_e1() -> dict[str, Any]:
    result = chain(BYPASS2 / "e1_prose_quantitative_claim.json")
    result["reason"] = "post_receipt_gate.sh ledger disposition"
    return result


def run_e2() -> dict[str, Any]:
    fixture_dir = BYPASS2 / "e2"
    with tempfile.TemporaryDirectory(prefix="claimgate-e2-pack-") as temp:
        pack = Path(temp)
        workers = pack / "workers" / "estate"
        workers.mkdir(parents=True)
        worker = workers / "capability_worker.py"
        blocker = workers / "import_blocker.py"
        poisoner = workers / "operation_poisoner.py"
        shutil.copyfile(fixture_dir / "capability_worker.py", worker)
        shutil.copyfile(CONSTRAINTBOX_WORKERS / "import_blocker.py", blocker)
        shutil.copyfile(CONSTRAINTBOX_WORKERS / "operation_poisoner.py", poisoner)
        manifest = {
            "schema": "constraintbox.sim-estate.v2",
            "status": "REGRESSION_FIXTURE",
            "promotion_allowed": False,
            "controller_sha256": _sha(ESTATE_CONTROLLER),
            "worker_sha256": _sha(worker),
            "import_blocker_sha256": _sha(blocker),
            "tiers": [
                {
                    "tier_id": "E2",
                    "name": "operation-severance regression fixture",
                    "boot_budget_seconds": 30,
                    "capabilities": [
                        {
                            "id": "jax_density",
                            "locked_version": None,
                            "required": True,
                        }
                    ],
                }
            ],
        }
        manifest_path = pack / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(CONSTRAINTBOX_SRC)
        rc, body = _run_json(
            [
                str(PYTHON),
                "-m",
                "constraintbox.cli",
                "estate",
                "--pack-root",
                str(pack),
                "--manifest",
                str(manifest_path),
                "--fixture",
                str(fixture_dir / "fixture.json"),
                "--tier",
                "E2",
                "--mode",
                "acceptance",
                "--python",
                str(PYTHON),
                "--enforce",
            ],
            env=env,
        )
    capability = body.get("capabilities", [{}])[0]
    controls = capability.get("controls", {})
    admitted = (
        rc == 0
        and body.get("state") == "READY"
        and capability.get("state") == "READY"
        and controls.get("severance") is True
        and "operation" not in controls
    )
    return {
        "admitted": admitted,
        "cli_exit": rc,
        "tier_state": body.get("state"),
        "capability": capability.get("capability_id"),
        "capability_state": capability.get("state"),
        "controls": controls,
        "controls_not_measured": capability.get("evidence", {}).get(
            "controls_not_measured", []
        ),
        "reason": capability.get("reason"),
    }


def run_e3() -> dict[str, Any]:
    module = _load_module("bypass2_e3_same_formula", BYPASS2 / "e3" / "same_formula.py")
    with tempfile.TemporaryDirectory(prefix="claimgate-e3-receipts-") as temp:
        receipts = module.write_receipts(Path(temp))
        env = dict(os.environ)
        env["PYTHONPATH"] = str(CONSTRAINTBOX_SRC)
        rc, body = _run_json(
            [
                str(PYTHON),
                "-m",
                "constraintbox.cli",
                "estate-parity",
                *[str(path) for path in receipts],
                "--enforce",
            ],
            env=env,
        )
    expected = {"numpy_density", "jax_density", "torch_density"}
    admitted = (
        rc == 0
        and body.get("state") == "READY"
        and set(body.get("sources", [])) == expected
        and all(row.get("pass") for row in body.get("comparisons", []))
    )
    return {
        "admitted": admitted,
        "cli_exit": rc,
        "state": body.get("state"),
        "sources": body.get("sources"),
        "independent_families": body.get("independent_families"),
        "comparisons_pass": [row.get("pass") for row in body.get("comparisons", [])],
        "producer": "one same_formula.py computation",
    }


def run_e4() -> dict[str, Any]:
    sys.path.insert(0, str(CONSTRAINTBOX_SRC))
    module = _load_module("bypass2_e4_reproduce", BYPASS2 / "e4" / "reproduce.py")
    return module.reproduce()


def run_e5() -> dict[str, Any]:
    sys.path.insert(0, str(CONSTRAINTBOX_SRC))
    module = _load_module("bypass2_e5_nested_input", BYPASS2 / "e5" / "nested_input.py")
    return module.reproduce()


def run_e6() -> dict[str, Any]:
    sys.path.insert(0, str(CONSTRAINTBOX_SRC))
    module = _load_module("bypass2_e6_unicode_keys", BYPASS2 / "e6" / "unicode_keys.py")
    return module.reproduce()


RUNNERS = {
    "e1": run_e1,
    "e2": run_e2,
    "e3": run_e3,
    "e4": run_e4,
    "e5": run_e5,
    "e6": run_e6,
}


def main(argv: list[str]) -> int:
    if argv:
        print("usage: run_bypass2_regression.py", file=sys.stderr)
        return 2
    if not PYTHON.is_file() or not HOOK.is_file():
        print(
            "run_bypass2_regression: required interpreter or hook absent "
            "reason=PRECONDITION_ABSENT",
            file=sys.stderr,
        )
        return 1

    rows = []
    deviations = []
    for case_id, name, expected, required_paths in CASES:
        missing = [path for path in required_paths if not (BYPASS2 / path).is_file()]
        if missing:
            status = "MISSING"
            evidence = {"missing": missing}
        else:
            try:
                evidence = RUNNERS[case_id]()
                status = "ADMITTED" if evidence.get("admitted") else "CLOSED"
            except Exception as exc:
                status = "ERROR"
                evidence = {"error": f"{type(exc).__name__}: {exc}"}
        rows.append(
            {
                "id": case_id,
                "case": name,
                "expected": expected,
                "status": status,
                "evidence": evidence,
            }
        )
        print(f"  {case_id}  {status}  {name}")
        if status == "ERROR":
            print(f"      {evidence['error']}")
        if status == "MISSING":
            reason = "FIXTURE_MISSING"
        elif status == "ERROR":
            reason = "FIXTURE_ERROR"
        elif expected == "ADMITTED" and status == "CLOSED":
            reason = "HOLE_CLOSED_MOVE_TO_V1"
        elif expected == "CLOSED" and status == "ADMITTED":
            reason = "HOLE_REOPENED"
        else:
            reason = None
        if reason:
            deviations.append(
                {
                    "id": case_id,
                    "expected": expected,
                    "actual": status,
                    "reason": reason,
                }
            )

    declared_ids = {case_id for case_id, _, _, _ in CASES}
    row_ids = {row["id"] for row in rows}
    if not CASES:
        deviations.append(
            {
                "id": "coverage",
                "expected": "ONE_OR_MORE_FIXTURES",
                "actual": "NONE_DECLARED",
                "reason": "NO_FIXTURES_DECLARED",
            }
        )
    if len(rows) != len(CASES) or row_ids != declared_ids:
        deviations.append(
            {
                "id": "coverage",
                "expected": f"{len(CASES)}:{sorted(declared_ids)}",
                "actual": f"{len(rows)}:{sorted(row_ids)}",
                "reason": "COVERAGE_MISMATCH",
            }
        )

    admitted = sum(row["status"] == "ADMITTED" for row in rows)
    closed = sum(row["status"] == "CLOSED" for row in rows)
    errors = [row["id"] for row in rows if row["status"] == "ERROR"]
    print(
        f"\nrun_bypass2_regression: {admitted}/{len(CASES)} still ADMITTED "
        f"({closed} closed, {len(errors)} fixture errors, "
        f"{len(deviations)} deviations)"
    )
    for deviation in deviations:
        print(
            f"{deviation['id']}: expected={deviation['expected']} "
            f"actual={deviation['actual']} reason={deviation['reason']}"
        )
    summary = {
        "probe": "claimgate_bypass2_regression_v1",
        "classification": "acceptance_regression_fixture",
        "promotion_allowed": False,
        "expected_current_state": "all executable cases are ADMITTED until hardened",
        "exit_convention": (
            "0 means every declared case was exercised and matched its expected "
            "disposition; 1 means one or more deviations or a coverage mismatch; "
            "2 means usage error"
        ),
        "admitted": admitted,
        "closed": closed,
        "errors": errors,
        "total": len(CASES),
        "results": rows,
        "deviations": deviations,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if deviations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
