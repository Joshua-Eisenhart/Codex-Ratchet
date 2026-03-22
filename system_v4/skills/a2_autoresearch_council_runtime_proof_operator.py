"""
a2_autoresearch_council_runtime_proof_operator.py

Bounded first runtime-proof slice for the karpathy-meta-research-runtime family.

This slice proves only the smallest honest local seam: seeded local composition
of the existing autoresearch and llm-council operators through the bounded
research/deliberation wrapper. It does not import hosted backends, training
loops, branch-experiment workflows, or external council services.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_research_deliberation_operator import (
    build_a2_research_deliberation_report,
)
from system_v4.skills.runtime_state_kernel import RuntimeState

CLUSTER_ID = "SKILL_CLUSTER::karpathy-meta-research-runtime"
SLICE_ID = "a2-autoresearch-council-runtime-proof-operator"

AUTORESEARCH_PATH = "work/reference_repos/karpathy/autoresearch"
LLM_COUNCIL_PATH = "work/reference_repos/karpathy/llm-council"
NANOCHAT_PATH = "work/reference_repos/karpathy/nanochat"
NANOGPT_PATH = "work/reference_repos/karpathy/nanoGPT"
LLM_C_PATH = "work/reference_repos/karpathy/llm.c"
MINBPE_PATH = "work/reference_repos/karpathy/minbpe"

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_AUTORESEARCH_COUNCIL_RUNTIME_PROOF_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_AUTORESEARCH_COUNCIL_RUNTIME_PROOF_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_AUTORESEARCH_COUNCIL_RUNTIME_PROOF_PACKET__CURRENT__v1.json"
)

IMPORTED_MEMBER_DISPOSITION = {
    "autoresearch": {
        "classification": "adapt",
        "keep": "seeded search-space exploration, fixed-scope improvement loop, and programmatic research framing",
        "adapt_away_from": [
            "GPU training loop ownership",
            "branch-per-run experiment workflow",
            "overnight autonomous experiment loop",
            "train.py mutation ownership",
            "cache/bootstrap requirements",
        ],
    },
    "llm-council": {
        "classification": "adapt",
        "keep": "multi-perspective review, ranking, and synthesis discipline",
        "adapt_away_from": [
            "OpenRouter or API-backed model calls",
            "frontend/backend web app ownership",
            "chairman model service assumptions",
            "hosted council runtime claims",
        ],
    },
    "nanochat": {
        "classification": "mine",
        "keep": "small-runtime shape and minimal local experimentation pressure",
        "adapt_away_from": [
            "training runtime ownership",
            "chat-shell or model-host claims",
        ],
    },
    "nanoGPT": {
        "classification": "mine",
        "keep": "minimal-core runtime and training-pattern source pressure only",
        "adapt_away_from": [
            "model-training integration claims",
            "full repo-family port claims",
        ],
    },
    "llm.c": {
        "classification": "defer",
        "keep": "later low-level runtime/minimal-core pattern source only",
        "adapt_away_from": [
            "current slice scope",
        ],
    },
    "minbpe": {
        "classification": "defer",
        "keep": "later tokenizer/boundary/compression pattern source only",
        "adapt_away_from": [
            "current slice scope",
        ],
    },
}

DEFAULT_RECOMMENDED_ACTIONS = [
    "Keep this first slice as a bounded local runtime proof only, not a claim that the Karpathy runtime family is fully ported.",
    "Use the current local autoresearch plus llm-council seam as the proof subject instead of widening to external backends, training loops, or branch experiments.",
    "If this family continues, choose one explicit follow-on only after reselection instead of widening multiple Karpathy repos at once.",
]

DEFAULT_NON_GOALS = [
    "No external search, OpenRouter, or hosted-model calls.",
    "No GPU training loop, data preparation, or overnight experiment run.",
    "No git branch, reset, or branch-advance workflow import.",
    "No web app, dashboard, or chairman service bootstrap.",
    "No claim that the full Karpathy family is ported or runtime-real.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo_status(root: Path, rel_path: str) -> dict[str, Any]:
    path = root / rel_path
    return {
        "path": rel_path,
        "exists": path.exists(),
        "is_dir": path.is_dir(),
    }


def _seed_state() -> RuntimeState:
    return RuntimeState(
        region="karpathy_runtime_seed",
        phase_index=0,
        phase_period=8,
        invariants=["bounded_local_runtime_only", "no_external_backend"],
        dof={"quality": 0.42, "simplicity": 0.63, "risk": 0.18},
        context={"lane": CLUSTER_ID, "slice": SLICE_ID},
    )


def _generator(state: RuntimeState) -> list[RuntimeState]:
    quality = float(state.dof.get("quality", 0.0))
    simplicity = float(state.dof.get("simplicity", 0.0))
    risk = float(state.dof.get("risk", 0.0))
    return [
        RuntimeState(
            region="karpathy_candidate_balanced",
            dof={"quality": quality + 0.15, "simplicity": simplicity + 0.10, "risk": risk + 0.04},
            context={"candidate_family": "balanced"},
        ),
        RuntimeState(
            region="karpathy_candidate_simple",
            dof={"quality": quality + 0.08, "simplicity": simplicity + 0.18, "risk": risk + 0.01},
            context={"candidate_family": "simple"},
        ),
        RuntimeState(
            region="karpathy_candidate_risky",
            dof={"quality": quality + 0.22, "simplicity": simplicity - 0.04, "risk": risk + 0.18},
            context={"candidate_family": "risky"},
        ),
    ]


def _evaluator(state: RuntimeState) -> float:
    quality = float(state.dof.get("quality", 0.0))
    simplicity = float(state.dof.get("simplicity", 0.0))
    risk = float(state.dof.get("risk", 0.0))
    return round((quality * 0.55) + (simplicity * 0.35) - (risk * 0.25), 6)


def build_a2_autoresearch_council_runtime_proof_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    proof_mode = str(ctx.get("proof_mode", "seeded_local_runtime_proof")).strip()
    issues: list[str] = []
    if proof_mode != "seeded_local_runtime_proof":
        issues.append("proof_mode widened beyond seeded local runtime proof")

    local_sources = {
        "autoresearch": _repo_status(root, AUTORESEARCH_PATH),
        "llm-council": _repo_status(root, LLM_COUNCIL_PATH),
        "nanochat": _repo_status(root, NANOCHAT_PATH),
        "nanoGPT": _repo_status(root, NANOGPT_PATH),
        "llm.c": _repo_status(root, LLM_C_PATH),
        "minbpe": _repo_status(root, MINBPE_PATH),
    }
    for required_member in ("autoresearch", "llm-council"):
        if not local_sources[required_member]["exists"]:
            issues.append(f"missing local source repo: {required_member}")

    proof_report: dict[str, Any] = {}
    if not issues:
        proof_report = build_a2_research_deliberation_report(
            root,
            {
                "question": "bounded karpathy runtime proof",
                "state": _seed_state(),
                "generator": _generator,
                "evaluator": _evaluator,
                "random_seed": int(ctx.get("random_seed", 42)),
                "consensus_threshold": float(ctx.get("consensus_threshold", 0.51)),
            },
        )
        if proof_report.get("status") != "ok":
            issues.extend(proof_report.get("issues", []))
        execution = proof_report.get("execution", {})
        if execution.get("route") != "local-autoresearch-then-council":
            issues.append("local runtime proof did not use the expected autoresearch-then-council route")
        if not execution.get("used_autoresearch"):
            issues.append("autoresearch operator was not exercised during runtime proof")
        if not execution.get("used_llm_council"):
            issues.append("llm-council operator was not exercised during runtime proof")
        if int(execution.get("candidate_count", 0)) <= 0:
            issues.append("runtime proof produced no candidates")

    report = {
        "schema": "A2_AUTORESEARCH_COUNCIL_RUNTIME_PROOF_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues else "attention_required",
        "audit_only": True,
        "proof_only": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "proof_mode": proof_mode,
        "local_sources": local_sources,
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITION,
        "runtime_proof": {
            "proof_subject": "local autoresearch plus llm-council composition through a2-research-deliberation-operator",
            "route": proof_report.get("execution", {}).get("route", ""),
            "used_autoresearch": proof_report.get("execution", {}).get("used_autoresearch", False),
            "used_llm_council": proof_report.get("execution", {}).get("used_llm_council", False),
            "candidate_count": proof_report.get("execution", {}).get("candidate_count", 0),
            "accepted_count": proof_report.get("execution", {}).get("accepted_count", 0),
            "accepted_regions": proof_report.get("execution", {}).get("accepted_regions", []),
            "candidate_summary": proof_report.get("execution", {}).get("candidate_summary", []),
            "autoresearch": proof_report.get("execution", {}).get("autoresearch"),
        },
        "recommended_next_step": "hold_first_slice_as_runtime_proof_only" if not issues else "",
        "recommended_actions": list(DEFAULT_RECOMMENDED_ACTIONS),
        "issues": issues,
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "A2_AUTORESEARCH_COUNCIL_RUNTIME_PROOF_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "proof_mode": proof_mode,
        "allow_external_runtime_import": False,
        "allow_training": False,
        "allow_service_bootstrap": False,
        "allow_branch_experiment_loop": False,
        "allow_git_mutation": False,
        "allow_registry_mutation": False,
        "allow_runtime_live_claims": False,
        "proof_route": report["runtime_proof"]["route"],
        "recommended_next_step": report["recommended_next_step"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    runtime = report.get("runtime_proof", {})
    member_lines = []
    for member_id, info in report.get("imported_member_disposition", {}).items():
        member_lines.append(
            f"- `{member_id}`: {info.get('classification')} -> {info.get('keep')}"
        )
    issue_lines = [f"- {line}" for line in report.get("issues", [])] or ["- none"]
    next_action_lines = [f"- {line}" for line in report.get("recommended_actions", [])]
    non_goal_lines = [f"- {line}" for line in report.get("non_goals", [])]
    return "\n".join(
        [
            "# A2 Autoresearch Council Runtime Proof Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- cluster_id: `{report.get('cluster_id', '')}`",
            f"- slice_id: `{report.get('slice_id', '')}`",
            f"- proof_mode: `{report.get('proof_mode', '')}`",
            f"- proof_route: `{runtime.get('route', '')}`",
            f"- used_autoresearch: `{runtime.get('used_autoresearch', False)}`",
            f"- used_llm_council: `{runtime.get('used_llm_council', False)}`",
            f"- candidate_count: `{runtime.get('candidate_count', 0)}`",
            f"- accepted_count: `{runtime.get('accepted_count', 0)}`",
            f"- recommended_next_step: `{packet.get('recommended_next_step', '')}`",
            "",
            "## Imported Member Disposition",
            *member_lines,
            "",
            "## Recommended Actions",
            *next_action_lines,
            "",
            "## Non-Goals",
            *non_goal_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def run_a2_autoresearch_council_runtime_proof(
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or REPO_ROOT).resolve()

    report, packet = build_a2_autoresearch_council_runtime_proof_report(root, ctx)

    report_json_path = _resolve_output_path(root, ctx.get("report_json_path"), REPORT_JSON)
    report_md_path = _resolve_output_path(root, ctx.get("report_md_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_json_path, report)
    _write_text(report_md_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    return {
        "status": report["status"],
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
        "packet_path": str(packet_path),
        "recommended_next_step": report.get("recommended_next_step", ""),
    }


if __name__ == "__main__":
    emitted = run_a2_autoresearch_council_runtime_proof({"repo_root": str(REPO_ROOT)})
    assert emitted["status"] == "ok", emitted
    print("PASS: a2_autoresearch_council_runtime_proof_operator self-test")
