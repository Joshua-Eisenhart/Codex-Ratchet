#!/usr/bin/env python3
"""Static V8 FlowMind guard: deterministic commands only, fail closed, pinned Lev."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

import yaml


PINNED_LEV_ROOT = Path("/Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract")
PINNED_LEV = PINNED_LEV_ROOT / "core/poly/bin/lev"
EXPECTED_HEAD = "856acb1a5de42528a9a54272435d98a9fe226186"
EXPECTED_TREE = "3f3488781d48a64b22c43c08ccfaa2b503d49524"
EXPECTED_EXECUTABLE_SHA256 = "f258ae313d515cae4ff848a45df78cfcc6a2d48c9ce1ade9c316276b00ef0c61"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=PINNED_LEV_ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", type=Path, required=True)
    args = parser.parse_args()
    flow_path = args.flow.resolve()
    flow = yaml.safe_load(flow_path.read_text(encoding="utf-8"))
    findings: list[str] = []
    nodes = flow.get("nodes", {}) if isinstance(flow, dict) else {}
    if flow.get("policy", {}).get("determinism") is not True:
        findings.append("policy.determinism must be true")
    required_scripts = {"validate_lev_flow.py", "validate_preregistration.py", "run_pipeline.py", "validate_g0_g9_report.py"}
    seen_scripts: set[str] = set()
    for node_id, node in nodes.items():
        if node.get("terminal") is True:
            continue
        if node.get("op") != "lev.validate":
            findings.append(f"{node_id}: only lev.validate is allowed")
        inputs = node.get("inputs", {})
        command = inputs.get("command")
        if not isinstance(command, str) or not command.strip():
            findings.append(f"{node_id}: command is empty")
            continue
        if inputs.get("fail_closed") != "true":
            findings.append(f"{node_id}: fail_closed must be the string true")
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            findings.append(f"{node_id}: invalid command: {exc}")
            continue
        if not argv or not Path(argv[0]).is_absolute():
            findings.append(f"{node_id}: executable must be absolute")
        lowered = command.lower()
        forbidden = ["claude", "anthropic", "openai", "nvidia", "xai", "--model", "lev.exec", "op: lev.exec"]
        if any(token in lowered for token in forbidden):
            findings.append(f"{node_id}: model/provider or lev.exec token present")
        for token in argv:
            if token.endswith(".py"):
                seen_scripts.add(Path(token).name)
        branches = node.get("branches", {})
        failure = branches.get("fail")
        if not isinstance(failure, str) or not failure.startswith("blocked_"):
            findings.append(f"{node_id}: failure target must be blocked_*")
        if branches.get("pass") not in nodes:
            findings.append(f"{node_id}: pass target missing")
        if failure not in nodes or nodes.get(failure, {}).get("terminal") is not True:
            findings.append(f"{node_id}: blocked failure terminal missing")
    missing_scripts = required_scripts - seen_scripts
    if missing_scripts:
        findings.append(f"required deterministic gates missing: {sorted(missing_scripts)}")
    if not PINNED_LEV.is_file() or sha256(PINNED_LEV) != EXPECTED_EXECUTABLE_SHA256:
        findings.append("pinned Lev executable hash mismatch")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        findings.append("pinned Lev HEAD mismatch")
    if git("rev-parse", "HEAD^{tree}") != EXPECTED_TREE:
        findings.append("pinned Lev tree mismatch")
    if git("status", "--short"):
        findings.append("pinned Lev worktree is dirty")
    ok = not findings
    result = {
        "schema": "codex_ratchet.lev_flow_static_validation.v1",
        "ok": ok,
        "findings": findings,
        "flow_path": str(flow_path),
        "flow_sha256": sha256(flow_path),
        "lev": {
            "path": str(PINNED_LEV),
            "sha256": sha256(PINNED_LEV) if PINNED_LEV.is_file() else None,
            "head": git("rev-parse", "HEAD"),
            "tree": git("rev-parse", "HEAD^{tree}"),
            "clean": not bool(git("status", "--short")),
        },
        "action_node_count": sum(node.get("terminal") is not True for node in nodes.values()),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
