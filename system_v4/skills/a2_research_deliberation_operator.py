"""
a2_research_deliberation_operator.py

Bounded local research/deliberation cluster slice that composes the existing
autoresearch and llm-council skills without importing external research
backends or persistent multi-agent workflow scaffolding.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.autoresearch_operator import run_autoresearch
from system_v4.skills.llm_council_operator import run_llm_council
from system_v4.skills.runtime_state_kernel import RuntimeState

A2_RESEARCH_DELIBERATION_JSON = (
    "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json"
)
A2_RESEARCH_DELIBERATION_MD = (
    "system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.md"
)

IMPORTED_MEMBER_DISPOSITION = {
    "lev-research": {
        "classification": "adapt",
        "keep": "bounded route discipline and local-first research framing",
        "adapt_away_from": [
            "timetravel",
            "valyu",
            "oracle",
            "external search adapters",
            "session filesystem assumptions",
        ],
    },
    "cdo": {
        "classification": "mine",
        "keep": "adaptive deliberation and explicit perspective-synthesis pattern",
        "adapt_away_from": [
            "team dashboards",
            "bd tracking",
            "persistent team state",
            "agent brief filesystem layout",
        ],
    },
    "workflow-cited-research": {
        "classification": "skip",
        "keep": "later cited-research workflow idea only",
        "adapt_away_from": [
            "full workflow scaffolding",
            "external notebook projection",
        ],
    },
}

DEFAULT_NEXT_ACTIONS = [
    "Keep the first research/deliberation slice local and bounded over existing Ratchet runtime skills.",
    "Use explicit candidates or a seeded local search space instead of pretending external research backends are already ported.",
    "Treat this slice as a live cluster seam for autoresearch plus council, not as the full lev-research or CDO stack.",
]

DEFAULT_NON_GOALS = [
    "No external search or timetravel backend calls.",
    "No persistent team dashboard, bd board, or session tree import.",
    "No claim that lev-research or CDO is fully ported.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _state_from_raw(raw: Any, index: int = 0) -> RuntimeState:
    if isinstance(raw, RuntimeState):
        return raw
    if isinstance(raw, dict):
        return RuntimeState(
            region=str(raw.get("region", f"candidate_{index:02d}")),
            phase_index=int(raw.get("phase_index", 0)),
            phase_period=int(raw.get("phase_period", 8)),
            invariants=list(raw.get("invariants", [])),
            dof=dict(raw.get("dof", {})),
            context=dict(raw.get("context", {})),
        )
    return RuntimeState(region=f"candidate_{index:02d}", context={"raw": str(raw)})


def _dedupe_states(states: list[RuntimeState]) -> list[RuntimeState]:
    seen: set[str] = set()
    deduped: list[RuntimeState] = []
    for state in states:
        marker = state.hash()
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(state)
    return deduped


def _candidate_summary(states: list[RuntimeState], evaluator: Any | None) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for state in states:
        score = None
        if callable(evaluator):
            try:
                score = float(evaluator(state))
            except Exception:
                score = None
        summary.append(
            {
                "region": state.region,
                "hash": state.hash(),
                "score_hint": score,
            }
        )
    return summary


def _render_markdown(report: dict[str, Any]) -> str:
    execution = report.get("execution", {})
    disposition_lines = []
    for skill_id, info in report.get("imported_member_disposition", {}).items():
        disposition_lines.append(
            f"- `{skill_id}`: {info.get('classification')} -> {info.get('keep')}"
        )
    next_action_lines = [f"- {line}" for line in report.get("next_actions", [])]
    non_goal_lines = [f"- {line}" for line in report.get("non_goals", [])]
    issue_lines = [f"- {line}" for line in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# A2 Research Deliberation Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- question: `{report.get('question', '')}`",
            f"- route: `{execution.get('route', '')}`",
            f"- candidate_count: `{execution.get('candidate_count', 0)}`",
            f"- accepted_count: `{execution.get('accepted_count', 0)}`",
            "",
            "## Imported Member Disposition",
            *disposition_lines,
            "",
            "## Next Actions",
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


def build_a2_research_deliberation_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    ctx = ctx or {}
    issues: list[str] = []

    cluster_map_text = _load_text(root / "system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md")
    corpus_text = _load_text(root / "SKILL_SOURCE_CORPUS.md")
    if "research-deliberation" not in cluster_map_text:
        issues.append("research / deliberation cluster missing from imported cluster map")
    if "Research / deliberation cluster" not in corpus_text:
        issues.append("research / deliberation cluster missing from umbrella corpus")

    question = str(ctx.get("question", "")).strip() or "bounded local research / deliberation slice"
    random_seed = ctx.get("random_seed", 42)

    evaluator = ctx.get("evaluator")
    raw_candidates = ctx.get("candidates", [])
    candidates = _dedupe_states([_state_from_raw(item, index) for index, item in enumerate(raw_candidates)])

    seed_state = ctx.get("state")
    generator = ctx.get("generator")
    max_breadth = int(ctx.get("max_breadth", 3))
    max_depth = int(ctx.get("max_depth", 2))
    consensus_threshold = float(ctx.get("consensus_threshold", 0.51))

    route = "empty"
    used_autoresearch = False
    used_llm_council = False
    autoresearch_summary: dict[str, Any] | None = None

    if not candidates and seed_state is not None and callable(generator) and callable(evaluator):
        route = "local-autoresearch-then-council"
        ar_ctx = {
            "state": seed_state,
            "generator": generator,
            "evaluator": evaluator,
            "max_breadth": max_breadth,
            "max_depth": max_depth,
        }
        if ctx.get("recorder") is not None and ctx.get("witness_tags") is not None:
            ar_ctx["recorder"] = ctx["recorder"]
            ar_ctx["witness_tags"] = ctx["witness_tags"]
        ar_result = run_autoresearch(ar_ctx)
        if "error" in ar_result:
            issues.append(f"autoresearch dispatch error: {ar_result['error']}")
        else:
            used_autoresearch = True
            best_state = ar_result["best_state"]
            frontier = generator(seed_state)[:max_breadth]
            candidates = _dedupe_states([best_state, *frontier])
            autoresearch_summary = {
                "best_region": best_state.region,
                "best_hash": best_state.hash(),
                "best_score": ar_result["stats"].get("best_score"),
                "improved": ar_result["stats"].get("improved", False),
                "trace_tail": ar_result["stats"].get("trace", [])[-5:],
            }
    elif candidates:
        route = "candidate-deliberation"
    else:
        issues.append("no candidates supplied and no seeded state/generator/evaluator route available")

    council_result: dict[str, Any] = {"accepted": [], "rejected": [], "proceedings": []}
    if candidates:
        random.seed(random_seed)
        council_ctx = {
            "candidates": candidates,
            "consensus_threshold": consensus_threshold,
        }
        if ctx.get("recorder") is not None and ctx.get("witness_tags") is not None:
            council_ctx["recorder"] = ctx["recorder"]
            council_ctx["witness_tags"] = ctx["witness_tags"]
        council_result = run_llm_council(council_ctx)
        if "error" in council_result:
            issues.append(f"llm-council dispatch error: {council_result['error']}")
        else:
            used_llm_council = True

    report = {
        "schema": "A2_RESEARCH_DELIBERATION_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if not issues else "attention_required",
        "cluster_id": "SKILL_CLUSTER::research-deliberation",
        "question": question,
        "imported_member_disposition": IMPORTED_MEMBER_DISPOSITION,
        "execution": {
            "route": route,
            "used_autoresearch": used_autoresearch,
            "used_llm_council": used_llm_council,
            "random_seed": random_seed,
            "candidate_count": len(candidates),
            "candidate_summary": _candidate_summary(candidates, evaluator),
            "accepted_count": len(council_result.get("accepted", [])),
            "accepted_regions": [state.region for state in council_result.get("accepted", [])],
            "rejected_count": len(council_result.get("rejected", [])),
            "rejected_regions": [state.region for state in council_result.get("rejected", [])],
            "council_summary": [
                {
                    "region": item.get("region"),
                    "avg_score": item.get("avg_score"),
                    "accept_ratio": item.get("accept_ratio"),
                    "accepted": item.get("accepted"),
                }
                for item in council_result.get("proceedings", [])
            ],
            "autoresearch": autoresearch_summary,
        },
        "staged_output_targets": {
            "json_report": A2_RESEARCH_DELIBERATION_JSON,
            "md_report": A2_RESEARCH_DELIBERATION_MD,
        },
        "next_actions": DEFAULT_NEXT_ACTIONS,
        "non_goals": DEFAULT_NON_GOALS,
        "issues": issues,
    }
    return report


def run_a2_research_deliberation(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo", REPO_ROOT)
    root = Path(repo_root).resolve()
    report = build_a2_research_deliberation_report(root, ctx)
    report_path = Path(ctx.get("report_path") or (root / A2_RESEARCH_DELIBERATION_JSON))
    markdown_path = Path(ctx.get("markdown_path") or (root / A2_RESEARCH_DELIBERATION_MD))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    report["report_path"] = str(report_path)
    report["markdown_path"] = str(markdown_path)
    return report


if __name__ == "__main__":
    seed = RuntimeState(region="research_seed", dof={"val": 0.4})

    def _gen(state: RuntimeState) -> list[RuntimeState]:
        value = float(state.dof.get("val", 0.0))
        return [
            RuntimeState(region=f"cand_{value + 0.2:.2f}", dof={"val": value + 0.2}),
            RuntimeState(region=f"cand_{value + 0.1:.2f}", dof={"val": value + 0.1}),
            RuntimeState(region=f"cand_{value - 0.1:.2f}", dof={"val": value - 0.1}),
        ]

    report = build_a2_research_deliberation_report(
        REPO_ROOT,
        {
            "question": "self-test",
            "state": seed,
            "generator": _gen,
            "evaluator": lambda state: float(state.dof.get("val", 0.0)),
            "random_seed": 42,
            "consensus_threshold": 0.34,
        },
    )
    assert report["status"] == "ok", report["issues"]
    assert report["execution"]["used_autoresearch"]
    assert report["execution"]["used_llm_council"]
    print("PASS: a2_research_deliberation_operator self-test")
