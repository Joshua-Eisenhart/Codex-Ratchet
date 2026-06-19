from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "gate_object_binding.py"
REGISTRY = REPO_ROOT / "system_v4" / "probes" / "a2_state" / "sim_results" / "actual_lego_registry.json"
EXTRACT_REGISTRY = REPO_ROOT / "system_v4" / "probes" / "extract_actual_lego_registry.py"


def ensure_registry() -> None:
    if REGISTRY.exists():
        return
    subprocess.run(
        [sys.executable, str(EXTRACT_REGISTRY)],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_gate(*args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    ensure_registry()
    assert SCRIPT.exists(), "gate_object_binding.py is missing"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc, json.loads(proc.stdout)


def finding_kinds(payload: dict) -> set[str]:
    return {finding["kind"] for finding in payload.get("findings", [])}


def test_self_test_discriminates_real_toy_and_tmp_paths() -> None:
    proc, payload = run_gate("--self-test")

    assert proc.returncode == 0, proc.stderr
    assert payload["ok"] is True
    cases = {case["label"]: case for case in payload["cases"]}

    assert cases["real_registry_member"]["ok"] is True
    assert cases["real_registry_member"]["exit_code"] == 0
    assert cases["real_registry_member"]["findings"] == []

    toy = cases["toy_order_sensitivity"]
    assert toy["ok"] is False
    assert toy["exit_code"] == 1
    assert "not_registry_member" in finding_kinds(toy)
    assert "off_canonical_location" not in finding_kinds(toy)

    fake = cases["tmp_fake"]
    assert fake["ok"] is False
    assert fake["exit_code"] == 1
    assert {"off_canonical_location", "not_registry_member"} <= finding_kinds(fake)


def test_normal_cli_rejects_tmp_fake_with_required_findings() -> None:
    proc, payload = run_gate("--sim-path", "/tmp/fake_obj.py")

    assert proc.returncode == 1
    assert payload["ok"] is False
    assert {"off_canonical_location", "not_registry_member"} <= finding_kinds(payload)
