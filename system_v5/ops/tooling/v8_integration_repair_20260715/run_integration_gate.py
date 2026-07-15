#!/usr/bin/env python3
"""Replay and receipt the bounded V8 QIT plus Julia-carrier integration repair."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RESULTS = HERE / "results"
OUT = RESULTS / "integration_gate_receipt.json"
SIM_DIR = ROOT / "system_v7/sims/qit_projection_battery_v0"
QIT_RESULTS = SIM_DIR / "results"
PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = ROOT / "system_v5/julia_carrier"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def execute(step_id: str, command: list[str], timeout: int = 360) -> dict[str, Any]:
    env = dict(os.environ)
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "JULIA_LOAD_PATH": "@:@stdlib",
            "JULIA_PKG_OFFLINE": "true",
        }
    )
    started = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        return {
            "step_id": step_id,
            "command": command,
            "returncode": proc.returncode,
            "timed_out": False,
            "pass": proc.returncode == 0,
            "duration_seconds": round(time.monotonic() - started, 6),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "step_id": step_id,
            "command": command,
            "returncode": None,
            "timed_out": True,
            "pass": False,
            "duration_seconds": round(time.monotonic() - started, 6),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    py = str(PYTHON)
    steps = [
        ("env_doctor", [py, "-B", "scripts/codex_runtime_env_doctor.py", "--json"], 360),
        ("stack_shakedown", [py, "-B", "scripts/codex_engine_stack_shakedown.py"], 600),
        ("qit_main", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0.py"), "--fresh"], 180),
        ("qit_jax", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0_jax.py")], 180),
        ("qit_pytorch", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0_pytorch.py")], 360),
        (
            "qit_julia",
            [
                str(JULIA),
                "--startup-file=no",
                f"--project={JULIA_PROJECT}",
                str(SIM_DIR / "qit_projection_battery_v0_julia.jl"),
            ],
            360,
        ),
        ("qit_envelope", [py, "-B", str(SIM_DIR / "qit_projection_battery_v0_envelope.py")], 120),
        ("qit_packet_validator", [py, "-B", str(SIM_DIR / "validate_qit_projection_battery_v0.py")], 120),
        (
            "shared_strict_validator",
            [
                py,
                "-B",
                "scripts/validate_three_engine_sim_result.py",
                str(QIT_RESULTS / "qit_projection_battery_v0_envelope_results.json"),
                "--require-pytorch",
                "--strict-source-backed",
                "--require-tool-intent",
            ],
            120,
        ),
        (
            "focused_tests",
            [
                py,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "system_v5/tests/test_codex_runtime_env_doctor.py",
                "system_v5/tests/test_three_engine_sim_result_validator.py",
                "system_v7/sims/qit_projection_battery_v0/tests",
            ],
            300,
        ),
        (
            "contract_lint",
            [
                py,
                "-B",
                "scripts/lint_sim_contract.py",
                str(SIM_DIR / "qit_projection_battery_v0.py"),
                str(SIM_DIR / "qit_projection_battery_v0_envelope.py"),
            ],
            120,
        ),
    ]
    records: list[dict[str, Any]] = []
    for step_id, command, timeout in steps:
        record = execute(step_id, command, timeout)
        records.append(record)
        if not record["pass"]:
            break

    pre_path = RESULTS / "pre_manifest_shakedown.json"
    post_path = ROOT / "system_v5/ops/tooling/codex_runtime_capability_shakedown_results.json"
    envelope_path = QIT_RESULTS / "qit_projection_battery_v0_envelope_results.json"
    manifest_path = JULIA_PROJECT / "Manifest.toml"
    pre = load(pre_path)
    post = load(post_path)
    envelope = load(envelope_path)
    pre_summary = pre.get("summary", {})
    post_summary = post.get("summary", {})
    manifest_tracked = git(
        "ls-files", "--error-unmatch", "--", "system_v5/julia_carrier/Manifest.toml", check=False
    ).returncode == 0
    manifest_ignored = git(
        "check-ignore", "--quiet", "--", "system_v5/julia_carrier/Manifest.toml", check=False
    ).returncode == 0
    content_checks = {
        "pre_manifest_reproduced_26_pass_3_fail": (
            pre_summary.get("counts", {}).get("pass") == 26
            and pre_summary.get("counts", {}).get("fail") == 3
            and set(pre_summary.get("failed_checks", []))
            == {
                "codex_runtime_env_doctor",
                "strict_julia_carrier_api_probe",
                "julia_jax_torch_octonion_associator_agreement",
            }
        ),
        "post_manifest_shakedown_29_pass_0_fail": (
            post_summary.get("counts", {}).get("pass") == 29
            and post_summary.get("counts", {}).get("fail") == 0
            and post_summary.get("ok") is True
        ),
        "post_doctor_green": post.get("doctor_summary", {}).get("ok") is True,
        "carrier_manifest_tracked": manifest_tracked,
        "carrier_manifest_not_ignored": not manifest_ignored,
        "carrier_manifest_no_absolute_paths": not any(
            line.lstrip().startswith("path =")
            and ("/Users/" in line or line.split("=", 1)[-1].strip().startswith(('"/', "'/")))
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
        ),
        "qit_envelope_scratch_green": (
            envelope.get("all_pass") is True
            and envelope.get("classification") == "scratch_diagnostic"
            and envelope.get("promotion_allowed") is False
            and envelope.get("formal_admission_allowed") is False
        ),
        "qit_jaxlib_load_bearing_and_intent_bound": (
            "jaxlib" in envelope.get("claim_path_tools", [])
            and envelope.get("TOOL_INTEGRATION_DEPTH", {}).get("jaxlib") == "load_bearing"
            and bool(
                envelope.get("tool_intent", {})
                .get("engine_tool_intent", {})
                .get("jax", {})
                .get("jaxlib")
            )
        ),
    }
    source_paths = [
        ROOT / ".gitignore",
        ROOT / "scripts/audit_three_engine_source_claims.py",
        ROOT / "scripts/codex_runtime_env_doctor.py",
        ROOT / "scripts/codex_engine_stack_shakedown.py",
        ROOT / "scripts/validate_three_engine_sim_result.py",
        ROOT / "system_v5/tests/test_codex_runtime_env_doctor.py",
        ROOT / "system_v5/tests/test_three_engine_sim_result_validator.py",
        ROOT / "system_v5/julia_carrier/Project.toml",
        manifest_path,
        SIM_DIR / "qit_projection_battery_v0_jax.py",
        SIM_DIR / "qit_projection_battery_v0_envelope.py",
        Path(__file__).resolve(),
        HERE / "validate_integration_gate.py",
    ]
    artifact_paths = [
        pre_path,
        post_path,
        QIT_RESULTS / "qit_projection_battery_v0_results.json",
        QIT_RESULTS / "qit_projection_battery_v0_jax_results.json",
        QIT_RESULTS / "qit_projection_battery_v0_pytorch_results.json",
        QIT_RESULTS / "qit_projection_battery_v0_julia_results.json",
        envelope_path,
    ]
    source_head = git("rev-parse", "HEAD").stdout.strip()
    source_tree = git("rev-parse", "HEAD^{tree}").stdout.strip()
    all_steps_pass = len(records) == len(steps) and all(row["pass"] for row in records)
    receipt = {
        "schema": "codex_ratchet.v8_integration_repair.gate_receipt.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": "isolated_integration_repair",
        "source_head": source_head,
        "source_tree": source_tree,
        "source_bindings": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in source_paths
        ],
        "artifact_bindings": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in artifact_paths
        ],
        "steps": records,
        "content_checks": content_checks,
        "all_steps_pass": all_steps_pass,
        "all_content_checks_pass": all(content_checks.values()),
        "integration_gate_pass": all_steps_pass and all(content_checks.values()),
        "frozen_campaign_rewritten": False,
        "install_attempted": False,
        "llm_gate_used": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "official_launch_allowed": False,
        "release_eligible": False,
        "scientific_claim_proven": False,
        "claim_ceiling": (
            "isolated source/runtime integration repair only; QIT remains scratch diagnostic, "
            "the frozen V8 campaign remains red, and Ratchet tooth promotion remains blocked"
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "step_count": len(records),
                "integration_gate_pass": receipt["integration_gate_pass"],
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["integration_gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
