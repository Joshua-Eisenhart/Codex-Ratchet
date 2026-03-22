"""
a2_skill_improver_readiness_operator.py

Audit-only readiness slice for the live skill-improver operator.

This keeps the native maintenance/meta-skill lane honest by comparing the
registry claims around `skill-improver-operator` with its actual code,
dispatch wiring, and proof surfaces before anyone treats it as a safe live
repo-mutating skill.
"""

from __future__ import annotations

import ast
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TARGET_SKILL_ID = "skill-improver-operator"
TARGET_SKILL_PATH = "system_v4/skills/skill_improver_operator.py"
TARGET_SPEC_PATH = "system_v4/skill_specs/skill-improver-operator/SKILL.md"
TARGET_SMOKE_PATH = "system_v4/skills/test_skill_improver_operator_smoke.py"
REGISTRY_PATH = "system_v4/a1_state/skill_registry_v1.json"
RUNNER_PATH = "system_v4/skills/run_real_ratchet.py"

READINESS_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json"
)
READINESS_REPORT_MD = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.md"
)
READINESS_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_PACKET__CURRENT__v1.json"
)

DEFAULT_NON_GOALS = [
    "Do not mutate the target skill or any other repo file from this readiness slice.",
    "Do not claim that skill-improver-operator is safe for live repo mutation yet.",
    "Do not auto-promote this audit result into a live mutation loop.",
    "Do not treat syntax-only compile checks as proof of safe improvement behavior.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ast_name_set(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _registry_claims(registry_entry: dict[str, Any]) -> dict[str, Any]:
    capabilities = registry_entry.get("capabilities", {})
    return {
        "entry_present": bool(registry_entry),
        "skill_type": registry_entry.get("skill_type", ""),
        "source_path": registry_entry.get("source_path", ""),
        "is_phase_runner": bool(capabilities.get("is_phase_runner", False)),
        "can_write_repo": bool(capabilities.get("can_write_repo", False)),
        "requires_human_gate": bool(capabilities.get("requires_human_gate", False)),
        "reads_graph": bool(capabilities.get("reads_graph", False)),
        "mutates_graph": bool(capabilities.get("mutates_graph", False)),
        "inputs": registry_entry.get("inputs", []),
        "outputs": registry_entry.get("outputs", []),
        "tags": registry_entry.get("tags", []),
    }


def _implementation_flags(source_text: str) -> dict[str, Any]:
    names = _ast_name_set(source_text)
    runtime_gate_markers = {
        "approved",
        "approval",
        "allow_write",
        "approval_token",
        "dry_run",
        "human_gate",
        "allowed_targets",
    }
    scoring_markers = {"score", "scores", "best_score", "candidate_scores", "ranking"}
    test_markers = {"pytest", "unittest", "TestCase", "run_tests", "test_command"}
    return {
        "source_exists": bool(source_text),
        "placeholder_mutation_present": "mutated_code = original_code" in source_text,
        "direct_writeback_present": "skill_path.write_text(mutated_code)" in source_text,
        "temp_compile_check_present": "py_compile" in source_text,
        "real_test_selection_present": any(marker in source_text for marker in test_markers),
        "explicit_runtime_gate_present": any(marker in names for marker in runtime_gate_markers),
        "explicit_scoring_logic_present": any(marker in names for marker in scoring_markers),
        "stub_self_test_present": "self-test (stub)" in source_text,
        "witness_recording_present": "ctx[\"recorder\"].record(" in source_text,
        "subprocess_usage_present": "subprocess.run(" in source_text,
    }


def _build_required_repairs(flags: dict[str, Any], spec_exists: bool, smoke_exists: bool) -> list[str]:
    repairs: list[str] = []
    if not spec_exists:
        repairs.append("Add a dedicated skill spec for skill-improver-operator.")
    if flags["placeholder_mutation_present"]:
        repairs.append("Replace the placeholder mutation path with bounded candidate generation and selection.")
    if not flags["explicit_runtime_gate_present"]:
        repairs.append("Add an explicit runtime gate or dry-run/allowlist control before any repo write.")
    if flags["direct_writeback_present"]:
        repairs.append("Stage candidate outputs and proof surfaces before any target file writeback.")
    if not flags["real_test_selection_present"]:
        repairs.append("Run a real target smoke or test selection path instead of syntax-only validation.")
    if not flags["explicit_scoring_logic_present"]:
        repairs.append("Add explicit scoring or acceptance logic rather than relying on compile success alone.")
    if not smoke_exists:
        repairs.append("Add a dedicated smoke test that proves bounded behavior for the improver itself.")
    return repairs


def _dispatch_binding_present() -> bool:
    try:
        from system_v4.runners import run_real_ratchet as rr
    except Exception:
        return False

    original_dispatch = dict(rr.SKILL_DISPATCH)
    try:
        rr._register_dispatch()
        return TARGET_SKILL_PATH in rr.SKILL_DISPATCH
    except Exception:
        return False
    finally:
        rr.SKILL_DISPATCH.clear()
        rr.SKILL_DISPATCH.update(original_dispatch)


def build_skill_improver_readiness_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root)
    target_skill_path = _resolve_output_path(root, ctx.get("target_skill_path"), TARGET_SKILL_PATH)
    target_spec_path = root / TARGET_SPEC_PATH
    target_smoke_path = root / TARGET_SMOKE_PATH
    registry_path = root / REGISTRY_PATH
    runner_path = root / RUNNER_PATH

    registry_payload = _safe_load_json(registry_path)
    registry_entry = registry_payload.get(TARGET_SKILL_ID, {}) if isinstance(registry_payload, dict) else {}
    registry_entry = registry_entry if isinstance(registry_entry, dict) else {}
    source_text = target_skill_path.read_text(encoding="utf-8") if target_skill_path.exists() else ""
    flags = _implementation_flags(source_text)
    registry_claims = _registry_claims(registry_entry)
    dispatch_binding_present = _dispatch_binding_present()
    spec_exists = target_spec_path.exists()
    smoke_exists = target_smoke_path.exists()

    blocking_issues: list[str] = []
    if not target_skill_path.exists():
        blocking_issues.append("target skill source is missing")
    if not registry_entry:
        blocking_issues.append("registry row for skill-improver-operator is missing")
    if registry_claims["requires_human_gate"] and not flags["explicit_runtime_gate_present"]:
        blocking_issues.append("registry claims a human gate, but no explicit runtime gate is implemented")
    if flags["placeholder_mutation_present"]:
        blocking_issues.append("mutation path is still a placeholder")
    if flags["direct_writeback_present"]:
        blocking_issues.append("target file writeback is direct and unstaged")
    if not flags["real_test_selection_present"]:
        blocking_issues.append("validation is syntax-only and does not select real target tests")
    if not flags["explicit_scoring_logic_present"]:
        blocking_issues.append("acceptance/scoring logic is not implemented")
    if not spec_exists:
        blocking_issues.append("dedicated skill spec for skill-improver-operator is missing")
    if not smoke_exists:
        blocking_issues.append("dedicated smoke proof surface for skill-improver-operator is missing")
    if not dispatch_binding_present:
        blocking_issues.append("dispatch binding for skill-improver-operator is missing")

    required_repairs = _build_required_repairs(flags, spec_exists, smoke_exists)
    target_readiness = (
        "not_ready_for_live_mutation" if blocking_issues else "bounded_ready_for_first_target"
    )

    report = {
        "schema": "skill_improver_readiness_report_v1",
        "generated_utc": _utc_iso(),
        "status": "ok",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": "SKILL_CLUSTER::a2-skill-truth-maintenance",
        "first_slice": "a2-skill-improver-readiness-operator",
        "source_family": "Ratchet-native A2 truth maintenance",
        "target_skill_id": TARGET_SKILL_ID,
        "target_skill_path": str(target_skill_path.relative_to(root)) if target_skill_path.is_absolute() else str(target_skill_path),
        "registry_path": REGISTRY_PATH,
        "runner_path": RUNNER_PATH,
        "target_readiness": target_readiness,
        "dispatch_binding_present": dispatch_binding_present,
        "registry_claims": registry_claims,
        "implementation_flags": flags,
        "proof_surfaces": {
            "skill_spec_path": TARGET_SPEC_PATH,
            "skill_spec_exists": spec_exists,
            "dedicated_smoke_path": TARGET_SMOKE_PATH,
            "dedicated_smoke_exists": smoke_exists,
        },
        "blocking_issues": blocking_issues,
        "required_repairs": required_repairs,
        "recommended_first_target_class": (
            "one native Python skill with an existing smoke test and an explicit allowlist"
        ),
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "skill_improver_readiness_packet_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": report["cluster_id"],
        "skill_id": TARGET_SKILL_ID,
        "readiness_operator": report["first_slice"],
        "allow_audit_only_readiness_slice": True,
        "allow_live_repo_mutation": False,
        "allow_dispatch_as_mutator": False,
        "target_ready_for_live_mutation": False,
        "target_readiness": target_readiness,
        "blocking_issue_count": len(blocking_issues),
        "required_repairs": required_repairs,
        "recommended_first_target_class": report["recommended_first_target_class"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    claims = report.get("registry_claims", {})
    flags = report.get("implementation_flags", {})
    proof = report.get("proof_surfaces", {})
    blocking_issues = report.get("blocking_issues", [])
    repairs = report.get("required_repairs", [])
    return "\n".join(
        [
            "# Skill Improver Readiness Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- cluster_id: `{report.get('cluster_id', '')}`",
            f"- first_slice: `{report.get('first_slice', '')}`",
            f"- target_skill_id: `{report.get('target_skill_id', '')}`",
            f"- target_readiness: `{report.get('target_readiness', '')}`",
            f"- audit_only: `{report.get('audit_only', False)}`",
            f"- nonoperative: `{report.get('nonoperative', False)}`",
            f"- do_not_promote: `{report.get('do_not_promote', False)}`",
            "",
            "## Registry Claims",
            "",
            f"- entry_present: `{claims.get('entry_present', False)}`",
            f"- can_write_repo: `{claims.get('can_write_repo', False)}`",
            f"- requires_human_gate: `{claims.get('requires_human_gate', False)}`",
            f"- is_phase_runner: `{claims.get('is_phase_runner', False)}`",
            f"- dispatch_binding_present: `{report.get('dispatch_binding_present', False)}`",
            "",
            "## Implementation Flags",
            "",
            f"- placeholder_mutation_present: `{flags.get('placeholder_mutation_present', False)}`",
            f"- direct_writeback_present: `{flags.get('direct_writeback_present', False)}`",
            f"- temp_compile_check_present: `{flags.get('temp_compile_check_present', False)}`",
            f"- real_test_selection_present: `{flags.get('real_test_selection_present', False)}`",
            f"- explicit_runtime_gate_present: `{flags.get('explicit_runtime_gate_present', False)}`",
            f"- explicit_scoring_logic_present: `{flags.get('explicit_scoring_logic_present', False)}`",
            f"- stub_self_test_present: `{flags.get('stub_self_test_present', False)}`",
            "",
            "## Proof Surfaces",
            "",
            f"- skill_spec_exists: `{proof.get('skill_spec_exists', False)}`",
            f"- dedicated_smoke_exists: `{proof.get('dedicated_smoke_exists', False)}`",
            "",
            "## Blocking Issues",
            "",
            *([f"- {issue}" for issue in blocking_issues] or ["- none"]),
            "",
            "## Required Repairs",
            "",
            *([f"- {repair}" for repair in repairs] or ["- none"]),
            "",
            "## Packet",
            "",
            f"- allow_live_repo_mutation: `{packet.get('allow_live_repo_mutation', False)}`",
            f"- allow_dispatch_as_mutator: `{packet.get('allow_dispatch_as_mutator', False)}`",
            f"- target_ready_for_live_mutation: `{packet.get('target_ready_for_live_mutation', False)}`",
            "",
        ]
    )


def run_a2_skill_improver_readiness(ctx: dict[str, Any]) -> dict[str, Any]:
    root = Path(ctx.get("repo") or ctx.get("repo_root") or REPO_ROOT)
    report_json_path = _resolve_output_path(root, ctx.get("report_json_path"), READINESS_REPORT_JSON)
    report_md_path = _resolve_output_path(root, ctx.get("report_md_path"), READINESS_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), READINESS_PACKET_JSON)

    report, packet = build_skill_improver_readiness_report(root, ctx)
    _write_json(report_json_path, report)
    _write_json(packet_path, packet)
    _write_text(report_md_path, _render_markdown(report, packet))

    return {
        "status": report["status"],
        "target_readiness": report["target_readiness"],
        "blocking_issue_count": len(report["blocking_issues"]),
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    result = run_a2_skill_improver_readiness({})
    print(
        "PASS: a2_skill_improver_readiness_operator"
        f" status={result['status']}"
        f" readiness={result['target_readiness']}"
        f" blockers={result['blocking_issue_count']}"
    )
