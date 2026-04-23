"""
a2_next_state_signal_adaptation_audit_operator.py

Bounded audit over the OpenClaw-RL paper and repo.

This slice processes the source into Ratchet's broad skill corpus and maps the
paper's next-state and directive-correction ideas onto existing Ratchet seams.
It does not import the OpenClaw runtime, online RL trainer, or policy-serving
stack.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

PAPER_URL = "https://arxiv.org/abs/2603.10165"
REPO_URL = "https://github.com/Gen-Verse/OpenClaw-RL"
PAPER_TITLE = "OpenClaw-RL: Train Any Agent Simply by Talking"

REFERENCE_NOTE_PATH = "work/external_refs/OPENCLAW_RL__REFERENCE_NOTE__2026_03_21__v1.md"
LOCAL_REPO_PATH = "work/reference_repos/Gen-Verse/OpenClaw-RL"
CORPUS_PATH = "SKILL_SOURCE_CORPUS.md"
TRACKER_PATH = "REPO_SKILL_INTEGRATION_TRACKER.md"
BACKLOG_PATH = "SKILL_CANDIDATES_BACKLOG.md"
CLUSTER_MAP_PATH = "system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md"

REPORT_JSON = "system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_PACKET__CURRENT__v1.json"

CLUSTER_ID = "SKILL_CLUSTER::next-state-signal-adaptation"
SLICE_ID = "a2-next-state-signal-adaptation-audit-operator"

RATCHET_SEAM_SPECS = [
    {
        "skill_id": "witness-recorder",
        "path": "system_v4/skills/witness_recorder.py",
        "mapping": "captures post-action witness traces, replies, tool outputs, and context updates",
    },
    {
        "skill_id": "runtime-state-kernel",
        "path": "system_v4/skills/runtime_state_kernel.py",
        "mapping": "provides an explicit transition/state substrate instead of opaque interaction logs",
    },
    {
        "skill_id": "bounded-improve-operator",
        "path": "system_v4/skills/bounded_improve_operator.py",
        "mapping": "keeps improvement loops gated and measurable instead of unfenced online training",
    },
    {
        "skill_id": "a2-skill-improver-readiness-operator",
        "path": "system_v4/skills/a2_skill_improver_readiness_operator.py",
        "mapping": "audits whether an improvement lane is ready before any mutation claim",
    },
    {
        "skill_id": "a2-skill-improver-first-target-proof-operator",
        "path": "system_v4/skills/a2_skill_improver_first_target_proof_operator.py",
        "mapping": "proves one bounded improvement loop with exact restore instead of admitting a general live learner",
    },
]

IMPORTED_MEMBER_DISPOSITION = {
    "next-state-signals": {
        "classification": "adapt",
        "keep": "treat user reply, tool output, terminal state, and GUI state as first-class post-action evidence",
        "adapt_away_from": [
            "live RL trainer coupling",
            "OpenClaw runtime requirements",
            "always-on policy update claims",
        ],
    },
    "directive-correction-supervision": {
        "classification": "adapt",
        "keep": "separate richer directive correction from scalar evaluative judgment",
        "adapt_away_from": [
            "teacher-student distillation stack import",
            "judge model training assumptions",
            "token-level training claims without bounded proof",
        ],
    },
    "async-serving-judging-training-loop": {
        "classification": "mine",
        "keep": "decouple capture, review, and improvement work as an architectural pattern",
        "adapt_away_from": [
            "concurrent online trainer runtime",
            "background serving stack import",
            "claims that Ratchet already improves live from use",
        ],
    },
}

EXTRACTED_PATTERNS = [
    {
        "pattern": "unified_next_state_signal",
        "source": "paper_abstract",
        "ratchet_translation": "treat post-action witness evidence as a broad signal family, not just as passive logging",
    },
    {
        "pattern": "evaluative_and_directive_split",
        "source": "paper_abstract_and_repo_readme",
        "ratchet_translation": "keep scalar judgment and textual correction as distinct lanes for later bounded improvement work",
    },
    {
        "pattern": "async_improvement_architecture",
        "source": "paper_abstract_and_repo_readme",
        "ratchet_translation": "mine decoupled background improvement as a pattern, but keep Ratchet claims audit-only until a later proof lane exists",
    },
]

DEFAULT_RECOMMENDED_ACTIONS = [
    "Keep this slice audit-only and use it as a pattern-mapping bridge, not as an imported RL runtime.",
    "Use the report to scope a later bounded next-state / directive-signal probe over Ratchet witness and skill-improver surfaces.",
    "Do not widen this source into online training, PRM/judge stack import, or automatic policy mutation claims.",
]

DEFAULT_NON_GOALS = [
    "No OpenClaw runtime or server import.",
    "No PRM / judge / trainer stack import.",
    "No claim that Ratchet now improves online simply by being used.",
    "No unfenced live mutation or policy-update loop.",
    "No claim that the local OpenClaw repo checkout is stable until it is verified.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _local_repo_status(root: Path) -> dict[str, Any]:
    repo_path = root / LOCAL_REPO_PATH
    git_dir = repo_path / ".git"
    readme_path = repo_path / "README.md"
    shallow_lock_path = git_dir / "shallow.lock"
    if readme_path.exists() and git_dir.exists() and not shallow_lock_path.exists():
        state = "ready"
    elif repo_path.exists():
        state = "incomplete_clone"
    else:
        state = "url_only"
    return {
        "path": LOCAL_REPO_PATH,
        "exists": repo_path.exists(),
        "git_dir_exists": git_dir.exists(),
        "readme_exists": readme_path.exists(),
        "shallow_lock_present": shallow_lock_path.exists(),
        "checkout_state": state,
    }


def _doc_alignment(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    checks = [
        {
        "label": "reference_note",
            "path": REFERENCE_NOTE_PATH,
            "required_substrings": ["OpenClaw-RL", "Ratchet Translation Target"],
        },
        {
            "label": "skill_source_corpus",
            "path": CORPUS_PATH,
            "required_substrings": ["OpenClaw-RL", CLUSTER_ID],
        },
        {
            "label": "integration_tracker",
            "path": TRACKER_PATH,
            "required_substrings": ["OpenClaw-RL", SLICE_ID],
        },
        {
            "label": "candidates_backlog",
            "path": BACKLOG_PATH,
            "required_substrings": ["OpenClaw-RL", SLICE_ID],
        },
        {
            "label": "imported_cluster_map",
            "path": CLUSTER_MAP_PATH,
            "required_substrings": [CLUSTER_ID, SLICE_ID],
        },
    ]
    status_rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for check in checks:
        path = root / check["path"]
        text = _read_text(path)
        missing = [item for item in check["required_substrings"] if item not in text]
        status_rows.append(
            {
                "label": check["label"],
                "path": check["path"],
                "exists": path.exists(),
                "missing_required_markers": missing,
            }
        )
        if not path.exists():
            issues.append(f"missing required corpus surface: {check['label']}")
        elif missing:
            issues.append(f"corpus surface missing markers: {check['label']}")
    return status_rows, issues


def _ratchet_seam_mapping(root: Path) -> list[dict[str, Any]]:
    mapping: list[dict[str, Any]] = []
    for spec in RATCHET_SEAM_SPECS:
        path = root / spec["path"]
        mapping.append(
            {
                "skill_id": spec["skill_id"],
                "path": spec["path"],
                "exists": path.exists(),
                "mapping": spec["mapping"],
            }
        )
    return mapping


def _render_markdown(report: dict[str, Any]) -> str:
    local_repo = report["local_repo_status"]
    disposition_lines = [
        f"- `{name}`: {info['classification']} -> {info['keep']}"
        for name, info in report["imported_member_disposition"].items()
    ]
    seam_lines = [
        f"- `{item['skill_id']}`: exists={item['exists']} -> {item['mapping']}"
        for item in report["ratchet_seam_mapping"]
    ]
    action_lines = [f"- {item}" for item in report["recommended_actions"]]
    non_goal_lines = [f"- {item}" for item in report["non_goals"]]
    issue_lines = [f"- {item}" for item in report["issues"]] or ["- none"]
    return "\n".join(
        [
            "# A2 Next-State Signal Adaptation Audit Report",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- cluster_id: `{report['cluster_id']}`",
            f"- first_slice: `{report['first_slice']}`",
            f"- paper: `{report['paper']['title']}`",
            f"- repo_url: `{report['paper']['repo_url']}`",
            f"- local_repo_state: `{local_repo['checkout_state']}`",
            f"- recommended_next_step: `{report['gate']['recommended_next_step']}`",
            "",
            "## Imported Member Disposition",
            *disposition_lines,
            "",
            "## Ratchet Seam Mapping",
            *seam_lines,
            "",
            "## Recommended Actions",
            *action_lines,
            "",
            "## Non-Goals",
            *non_goal_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_a2_next_state_signal_adaptation_audit_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    local_repo_status = _local_repo_status(root)
    doc_alignment, issues = _doc_alignment(root)
    seam_mapping = _ratchet_seam_mapping(root)

    missing_seams = [item["skill_id"] for item in seam_mapping if not item["exists"]]
    if missing_seams:
        issues.append(f"missing Ratchet seam files: {', '.join(missing_seams)}")

    recommended_actions = list(DEFAULT_RECOMMENDED_ACTIONS)
    if local_repo_status["checkout_state"] != "ready":
        recommended_actions.append(
            "Verify the local OpenClaw-RL checkout later if network conditions allow, but do not block the bounded paper-derived slice on that clone."
        )

    allow_bounded_pattern_mining = not issues
    report = {
        "schema": "A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if allow_bounded_pattern_mining else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "first_slice": SLICE_ID,
        "source_family": "OpenClaw-RL-derived next-state signal family",
        "paper": {
            "arxiv_id": "2603.10165",
            "title": PAPER_TITLE,
            "paper_url": PAPER_URL,
            "repo_url": REPO_URL,
            "submitted_date": "2026-03-10",
        },
        "local_repo_status": local_repo_status,
        "doc_alignment": doc_alignment,
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITION,
        "extracted_patterns": EXTRACTED_PATTERNS,
        "ratchet_seam_mapping": seam_mapping,
        "gate": {
            "safe_to_continue": allow_bounded_pattern_mining,
            "allow_bounded_pattern_mining": allow_bounded_pattern_mining,
            "allow_runtime_import_claims": False,
            "allow_online_training_claims": False,
            "allow_policy_mutation_claims": False,
            "recommended_next_step": (
                "candidate_next_state_directive_probe"
                if allow_bounded_pattern_mining
                else "repair_next_state_signal_corpus_alignment"
            ),
            "reason": (
                "paper-to-system mapping is source-bound, corpus-held, and constrained to existing Ratchet seams"
                if allow_bounded_pattern_mining
                else "one or more required corpus or seam surfaces are still missing"
            ),
            "blocking_issues": issues,
        },
        "recommended_actions": recommended_actions,
        "non_goals": list(DEFAULT_NON_GOALS),
        "staged_output_targets": {
            "json_report": REPORT_JSON,
            "md_report": REPORT_MD,
            "packet_json": PACKET_JSON,
        },
        "issues": issues,
    }

    packet = {
        "schema": "A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "first_slice": SLICE_ID,
        "allow_bounded_pattern_mining": report["gate"]["allow_bounded_pattern_mining"],
        "allow_runtime_import_claims": False,
        "allow_online_training_claims": False,
        "allow_policy_mutation_claims": False,
        "recommended_next_step": report["gate"]["recommended_next_step"],
        "blocking_issues": issues,
        "recommended_actions": recommended_actions,
    }
    return report, packet


def run_a2_next_state_signal_adaptation_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo", REPO_ROOT)
    root = Path(repo_root).resolve()
    report, packet = build_a2_next_state_signal_adaptation_audit_report(root, ctx)

    report_path = _resolve_output_path(root, ctx.get("report_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("markdown_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report))
    _write_json(packet_path, packet)

    report["report_path"] = str(report_path)
    report["markdown_path"] = str(markdown_path)
    report["packet_path"] = str(packet_path)
    return report


if __name__ == "__main__":
    report, packet = build_a2_next_state_signal_adaptation_audit_report(REPO_ROOT)
    assert report["cluster_id"] == CLUSTER_ID
    assert report["first_slice"] == SLICE_ID
    assert packet["allow_runtime_import_claims"] is False
    print("PASS: a2_next_state_signal_adaptation_audit_operator self-test")
