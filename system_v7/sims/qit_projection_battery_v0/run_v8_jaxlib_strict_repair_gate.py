#!/usr/bin/env python3
"""Replay and receipt the isolated QIT jaxlib strict-gate repair candidate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
RESULTS = SIM_DIR / "results"
OUT = RESULTS / "v8_jaxlib_strict_repair_receipt.json"
BASE_COMMIT = "fe6487de5136d18e7471952a2aa70595cc0f5cf7"
PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def execute(step_id: str, command: list[str], env_overrides: dict[str, str] | None = None) -> dict[str, Any]:
    env = dict(os.environ)
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "JULIA_LOAD_PATH": "@:@stdlib",
        "JULIA_PKG_OFFLINE": "true",
    })
    env.update(env_overrides or {})
    started = time.monotonic()
    proc = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=300)
    return {
        "step_id": step_id,
        "command": command,
        "returncode": proc.returncode,
        "pass": proc.returncode == 0,
        "duration_seconds": round(time.monotonic() - started, 6),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    py = str(PYTHON)
    steps = [
        ("main", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0.py"), "--fresh"]),
        ("jax", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0_jax.py")]),
        ("pytorch", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0_pytorch.py")]),
        ("julia", [str(JULIA), "--startup-file=no", f"--project={JULIA_PROJECT}", str(SIM_DIR / "qit_projection_battery_v0_julia.jl")]),
        ("envelope", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0_envelope.py")]),
        ("packet_validator", [py, "-B", str(SIM_DIR / "validate_qit_projection_battery_v0.py")]),
        (
            "shared_strict_validator",
            [
                py,
                "-B",
                str(ROOT / "scripts/validate_three_engine_sim_result.py"),
                str(RESULTS / "qit_projection_battery_v0_envelope_results.json"),
                "--require-pytorch",
                "--strict-source-backed",
                "--require-tool-intent",
            ],
        ),
        (
            "validator_tests",
            [py, "-B", "-m", "pytest", "-p", "no:cacheprovider", "system_v5/tests/test_three_engine_sim_result_validator.py"],
        ),
        (
            "packet_tests",
            [py, "-B", "-m", "pytest", "-p", "no:cacheprovider", "system_v7/sims/qit_projection_battery_v0/tests"],
        ),
        (
            "contract_lint",
            [
                py,
                "-B",
                str(ROOT / "scripts/lint_sim_contract.py"),
                str(SIM_DIR / "qit_projection_battery_v0.py"),
                str(SIM_DIR / "qit_projection_battery_v0_envelope.py"),
            ],
        ),
    ]
    records: list[dict[str, Any]] = []
    for step_id, command in steps:
        record = execute(step_id, command)
        records.append(record)
        if not record["pass"]:
            break

    source_paths = [
        ROOT / "scripts/audit_three_engine_source_claims.py",
        ROOT / "scripts/validate_three_engine_sim_result.py",
        ROOT / "system_v5/tests/test_three_engine_sim_result_validator.py",
        SIM_DIR / "qit_projection_battery_v0_envelope.py",
        SIM_DIR / "qit_projection_battery_v0_jax.py",
        Path(__file__).resolve(),
        SIM_DIR / "validate_v8_jaxlib_strict_repair_receipt.py",
    ]
    result_paths = [
        RESULTS / "qit_projection_battery_v0_results.json",
        RESULTS / "qit_projection_battery_v0_jax_results.json",
        RESULTS / "qit_projection_battery_v0_pytorch_results.json",
        RESULTS / "qit_projection_battery_v0_julia_results.json",
        RESULTS / "qit_projection_battery_v0_envelope_results.json",
    ]
    envelope = json.loads(result_paths[-1].read_text(encoding="utf-8")) if result_paths[-1].is_file() else {}
    all_steps_pass = len(records) == len(steps) and all(record["pass"] for record in records)
    content_pass = bool(
        envelope.get("all_pass") is True
        and envelope.get("classification") == "scratch_diagnostic"
        and envelope.get("promotion_allowed") is False
        and envelope.get("formal_admission_allowed") is False
        and "jaxlib" in envelope.get("claim_path_tools", [])
        and envelope.get("TOOL_INTEGRATION_DEPTH", {}).get("jaxlib") == "load_bearing"
        and bool(envelope.get("tool_intent", {}).get("engine_tool_intent", {}).get("jax", {}).get("jaxlib"))
    )
    receipt = {
        "schema": "codex_ratchet.qit_projection_battery_v0.jaxlib_strict_repair_receipt.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": "isolated_repair_candidate",
        "base_commit": BASE_COMMIT,
        "observed_head": git("rev-parse", "HEAD"),
        "observed_tree": git("rev-parse", "HEAD^{tree}"),
        "source_bindings": [{"path": str(path), "sha256": sha256(path)} for path in source_paths],
        "result_bindings": [{"path": str(path), "sha256": sha256(path)} for path in result_paths if path.is_file()],
        "changed_paths": git("diff", "--name-only").splitlines(),
        "diff_sha256": hashlib.sha256(git("diff", "--binary").encode()).hexdigest(),
        "steps": records,
        "all_steps_pass": all_steps_pass,
        "content_pass": content_pass,
        "repair_gate_pass": all_steps_pass and content_pass and git("rev-parse", "HEAD") == BASE_COMMIT,
        "repaired_contract": "recognize direct jaxlib PJRT client/device observables while retaining import-only rejection",
        "negative_control": "unit test requires an import-only jaxlib source to remain source-token-thin",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "llm_gate_used": False,
        "install_attempted": False,
        "claim_ceiling": "isolated QIT shared-validator repair candidate only; frozen campaign red remains authoritative",
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "repair_gate_pass": receipt["repair_gate_pass"], "step_count": len(records)}, sort_keys=True))
    return 0 if receipt["repair_gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
