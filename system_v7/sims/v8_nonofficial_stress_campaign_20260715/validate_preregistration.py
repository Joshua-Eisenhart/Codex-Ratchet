#!/usr/bin/env python3
"""Fail-closed validator for the frozen nonofficial campaign boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "campaign_spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
PREREG_PATH = HERE / "preregistration.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def main() -> int:
    failures: list[str] = []
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    root = Path(spec["frozen_source_state"]["repo_root"])
    deep_root = Path(spec["frozen_source_state"]["deep_stack_repo_root"])
    first_rung_root = Path(spec["frozen_source_state"]["first_rung_repo_root"])

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(prereg.get("schema") == "codex_ratchet.v8_nonofficial_stress_campaign.preregistration.v1", "bad preregistration schema")
    require(prereg.get("campaign_id") == spec.get("campaign_id"), "campaign id mismatch")
    for field in ("promotion_allowed", "formal_admission_allowed", "release_eligible", "official_launch_allowed", "scientific_claim_proven", "llm_gate_allowed"):
        require(spec.get(field) is False and prereg.get(field) is False, f"{field} must remain false")
    require(spec.get("runtime_contract", {}).get("no_install") is True, "no-install contract missing")
    require(git(root, "rev-parse", "HEAD") == spec["frozen_source_state"]["commit"], "repo commit drift")
    require(git(root, "rev-parse", "HEAD^{tree}") == spec["frozen_source_state"]["tree"], "repo tree drift")
    require(git(deep_root, "rev-parse", "HEAD") == prereg["source_state"]["deep_stack_commit"], "deep-stack commit drift")
    require(git(deep_root, "rev-parse", "HEAD^{tree}") == prereg["source_state"]["deep_stack_tree"], "deep-stack tree drift")
    require(git(first_rung_root, "rev-parse", "HEAD") == prereg["source_state"]["first_rung_commit"], "first-rung commit drift")
    require(git(first_rung_root, "rev-parse", "HEAD^{tree}") == prereg["source_state"]["first_rung_tree"], "first-rung tree drift")
    require(sha256(SPEC_PATH) == prereg["source_state"]["spec_sha256"], "campaign spec hash drift")
    require(sha256(CARD_PATH) == prereg["source_state"]["object_card_sha256"], "object card hash drift")

    for binding in prereg["source_state"]["source_bindings"]:
        path = Path(binding["absolute_path"])
        require(path.is_file(), f"missing source: {path}")
        if path.is_file():
            require(sha256(path) == binding["sha256"], f"source hash drift: {path}")

    require(len(prereg["source_state"].get("preflight_bindings", [])) == 2, "preflight receipt boundary changed")
    for binding in prereg["source_state"].get("preflight_bindings", []):
        path = Path(binding["absolute_path"])
        require(path.is_file(), f"missing preflight receipt: {path}")
        if path.is_file():
            require(sha256(path) == binding["sha256"], f"preflight receipt hash drift: {path}")
            payload = json.loads(path.read_text(encoding="utf-8"))
            require(payload.get("summary", {}).get("counts") == binding["expected_counts"], f"preflight counts drift: {path}")
            require(payload.get("promotion_allowed") is False, f"preflight promotion flag changed: {path}")
            require(payload.get("formal_admission_allowed") is False, f"preflight admission flag changed: {path}")

    finite = prereg["finite_registry"]
    require(finite == {
        "deep_stress_rows": 95,
        "distinct_representative_paths": 48,
        "edges_sha256": "fe05a9c397c9af38b2b46bc7d25898e5ef18a066c2d59b5f996b19806fc21f71",
        "integration_edges": 29,
        "roster_sha256": "f22763d2bd808750e64b1992a01bad09298c30256ca8573704c2e536d887de97",
        "tool_rows": 139,
    }, "finite registry boundary changed")

    case_ids = [case["case_id"] for case in spec["cases"]]
    require(len(case_ids) == len(set(case_ids)), "duplicate case ids")
    require(case_ids == prereg["case_ids"], "case order or membership drift")
    for case in spec["cases"]:
        for step in case["steps"]:
            require(step.get("expected_exit") in {"zero", "nonzero", "any"}, f"bad expected_exit: {case['case_id']}/{step.get('step_id')}")
            require(isinstance(step.get("command"), list) and bool(step["command"]), f"empty command: {case['case_id']}/{step.get('step_id')}")
            command_parts = [str(part).lower() for part in step.get("command", [])]
            executable = Path(command_parts[0]).name if command_parts else ""
            is_agent_executable = executable in {"claude", "codex"}
            is_lev_exec = executable == "lev" and "exec" in command_parts[1:]
            has_model_flag = "--model" in command_parts[1:]
            require(not (is_agent_executable or is_lev_exec or has_model_flag), f"model/agent gate forbidden: {case['case_id']}/{step.get('step_id')}")
            if step.get("expected_exit") == "nonzero":
                require(step.get("receipt_role") == "preserved_red", f"nonzero step must preserve red: {case['case_id']}/{step.get('step_id')}")

    wizard = subprocess.run(
        [sys.executable, str(root / "scripts/wizard_v4_3_object_preservation.py"), "validate", "--input", str(CARD_PATH)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    require(wizard.returncode == 0, "Wizard v4.3 object card no longer validates")
    result = {
        "schema": "codex_ratchet.v8_nonofficial_stress_campaign.preregistration_validation.v1",
        "ok": not failures,
        "failures": failures,
        "case_count": len(case_ids),
        "blocked_case_count": len(spec["blocked_cases"]),
        "source_binding_count": len(prereg["source_state"]["source_bindings"]),
        "wizard_v4_3_guard_passed": wizard.returncode == 0,
        "claim_ceiling": spec["claim_ceiling"],
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
