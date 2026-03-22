"""
a2_source_family_lane_selector_operator.py

Audit-only selector that recommends the next bounded non-lev source-family lane
from current corpus and hold state.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_CORPUS_PATH = "SKILL_SOURCE_CORPUS.md"
TRACKER_PATH = "REPO_SKILL_INTEGRATION_TRACKER.md"
BUILD_PLAN_PATH = "SYSTEM_SKILL_BUILD_PLAN.md"
CLUSTER_MAP_PATH = "system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md"
LEV_PROMOTION_REPORT = "system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json"
NEXT_STATE_CONSUMER_REPORT = (
    "system_v4/a2_state/audit_logs/"
    "A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json"
)
WITNESS_MEMORY_RETRIEVER_REPORT = (
    "system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json"
)
A2_EVERMEM_REACHABILITY_REPORT = (
    "system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json"
)

LANE_SELECTION_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_SOURCE_FAMILY_LANE_SELECTION_REPORT__CURRENT__v1.json"
)
LANE_SELECTION_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_SOURCE_FAMILY_LANE_SELECTION_REPORT__CURRENT__v1.md"
)
LANE_SELECTION_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_SOURCE_FAMILY_LANE_SELECTION_PACKET__CURRENT__v1.json"
)

DEFAULT_NON_GOALS = [
    "Do not widen a held lane into live runtime, training, or service-bootstrap claims.",
    "Do not reopen lev by inertia when the current lev selector reports no open candidate.",
    "Do not treat a selector recommendation as proof that the recommended first slice is already landed.",
    "Do not mutate registry, graph, or external services from this selector slice.",
]

CANDIDATE_CLUSTERS: list[dict[str, Any]] = [
    {
        "cluster_id": "SKILL_CLUSTER::context-spec-workflow-memory",
        "import_label": "Context-Engineering / spec-kit / superpowers / mem0 source set",
        "cluster_role": "context_spec_memory_support",
        "recommended_first_slice_id": "a2-context-spec-workflow-pattern-audit-operator",
        "bounded_role": (
            "audit append-safe context, live spec coupling, workflow discipline, and scoped memory-sidecar "
            "patterns before any substrate or doctrine claim"
        ),
        "external_runtime_dependency": "low",
        "risk_level": "low",
        "score": 92,
        "members": [
            {
                "imported_skill_id": "Context-Engineering",
                "treatment": "adapt",
                "path": "work/reference_repos/external_audit/Context-Engineering",
                "reason": "Direct source for append-safe context/state structure and hierarchical orchestration.",
            },
            {
                "imported_skill_id": "spec-kit",
                "treatment": "adapt",
                "path": "work/reference_repos/external_audit/spec-kit",
                "reason": "Direct source for executable spec, task coupling, and spec/runtime discipline.",
            },
            {
                "imported_skill_id": "superpowers",
                "treatment": "mine",
                "path": "work/reference_repos/external_audit/superpowers",
                "reason": "Useful workflow and review discipline without importing plugin/runtime assumptions.",
            },
            {
                "imported_skill_id": "mem0",
                "treatment": "mine",
                "path": "work/reference_repos/external_audit/mem0",
                "reason": "Useful scoped memory-sidecar/history patterns without canonical-brain or graph-substrate claims.",
            },
        ],
        "selection_reasons": [
            "Directly matches the current user pressure around append-safe context, live specs, low-bloat continuity, and richer persistent brain behavior.",
            "All source repos are already local, audited, and low-risk compared with runtime-coupled families.",
            "A bounded pattern-audit first slice can produce value without opening runtime, service, or migration claims.",
        ],
    },
    {
        "cluster_id": "SKILL_CLUSTER::karpathy-meta-research-runtime",
        "import_label": "Karpathy autoresearch / llm-council / minimal-core family",
        "cluster_role": "meta_research_runtime_proof",
        "recommended_first_slice_id": "a2-autoresearch-council-runtime-proof-operator",
        "bounded_role": (
            "prove the existing autoresearch plus llm-council seams as honest local runtime helpers "
            "before broader self-improvement or agent-swarm claims"
        ),
        "external_runtime_dependency": "low",
        "risk_level": "moderate",
        "score": 84,
        "members": [
            {
                "imported_skill_id": "autoresearch",
                "treatment": "adapt",
                "path": "work/reference_repos/karpathy/autoresearch",
                "reason": "Direct source for local search over candidate spaces.",
            },
            {
                "imported_skill_id": "llm-council",
                "treatment": "adapt",
                "path": "work/reference_repos/karpathy/llm-council",
                "reason": "Direct source for bounded local deliberation and perspective synthesis.",
            },
            {
                "imported_skill_id": "nanochat",
                "treatment": "mine",
                "path": "work/reference_repos/karpathy/nanochat",
                "reason": "Useful controller/chat-shell pattern source without needing runtime import.",
            },
            {
                "imported_skill_id": "llm.c",
                "treatment": "mine",
                "path": "work/reference_repos/karpathy/llm.c",
                "reason": "Useful minimal-core runtime pattern source for later, not the first slice.",
            },
        ],
        "selection_reasons": [
            "Directly supports the user goal of having autoresearch and related helpers strengthen self-improvement.",
            "The source family is already local and partially integrated, so a runtime-proof slice is concrete and bounded.",
            "This stays narrower and more honest than claiming broad online self-improvement.",
        ],
    },
    {
        "cluster_id": "SKILL_CLUSTER::outside-memory-control",
        "import_label": "EverMemOS / outside-memory control",
        "cluster_role": "outside_memory_support",
        "recommended_first_slice_id": "witness-memory-retriever",
        "bounded_role": "outside memory/control support with witness retrieval and backend reachability",
        "external_runtime_dependency": "high",
        "risk_level": "high",
        "score": 40,
        "members": [
            {
                "imported_skill_id": "EverMemOS",
                "treatment": "adapt",
                "path": "work/reference_repos/EverMind-AI/EverMemOS",
                "reason": "Memory-sidecar and witness backend source family.",
            }
        ],
        "selection_reasons": [
            "Potentially valuable later for memory-sidecar work.",
            "Currently blocked by local backend reachability and intentionally side-project-scoped.",
        ],
    },
    {
        "cluster_id": "SKILL_CLUSTER::next-state-signal-adaptation",
        "import_label": "OpenClaw-RL next-state signal family",
        "cluster_role": "next_state_support",
        "recommended_first_slice_id": "a2-next-state-signal-adaptation-audit-operator",
        "bounded_role": "next-state and directive-correction support lane",
        "external_runtime_dependency": "moderate",
        "risk_level": "moderate",
        "score": 35,
        "members": [
            {
                "imported_skill_id": "OpenClaw-RL",
                "treatment": "adapt",
                "path": "work/reference_repos/Gen-Verse/OpenClaw-RL",
                "reason": "Source family for bounded next-state signal patterns.",
            }
        ],
        "selection_reasons": [
            "Current bounded work is useful but explicitly held at audit-only / first-target-context-only.",
            "Not the right lane to widen next by momentum.",
        ],
    },
    {
        "cluster_id": "SKILL_CLUSTER::graph-control-sidecars",
        "import_label": "Graph/control sidecar tranche",
        "cluster_role": "graph_support_sidecar",
        "recommended_first_slice_id": "pyg-heterograph-projection-audit",
        "bounded_role": "read-only graph/control support sidecars",
        "external_runtime_dependency": "low",
        "risk_level": "moderate",
        "score": 30,
        "members": [
            {
                "imported_skill_id": "graph-sidecars",
                "treatment": "adapt",
                "path": "system_v4/a2_state/audit_logs",
                "reason": "Repo-held graph/control support tranche.",
            }
        ],
        "selection_reasons": [
            "Useful support work, but the current tranche is explicitly held outside live admission.",
            "Not the right lane to widen again until a later explicit controller decision.",
        ],
    },
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


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _already_landed_in_cluster_map(cluster_id: str, cluster_map_text: str) -> bool:
    section_pattern = re.compile(r"## Cluster \d+.*?(?=\n## Cluster \d+|\n## Working Rule|\Z)", re.S)
    for match in section_pattern.finditer(cluster_map_text):
        section = match.group(0)
        if cluster_id in section and "first bounded slice now exists" in section:
            return True
    return False


def _member_record(root: Path, member: dict[str, Any]) -> dict[str, Any]:
    rel_path = str(member["path"])
    path = Path(rel_path)
    full = path if path.is_absolute() else (root / rel_path)
    return {
        **member,
        "exists": full.exists(),
    }


def _candidate_blockers(cluster_id: str, reports: dict[str, dict[str, Any]], combined_text: str) -> list[str]:
    blockers: list[str] = []
    if cluster_id == "SKILL_CLUSTER::outside-memory-control":
        if reports["witness_memory_retriever"].get("status") != "ok":
            blockers.append("witness-memory-retriever is not currently green")
        if reports["evermem_backend"].get("status") != "ok":
            blockers.append("EverMem backend reachability is not currently green")
    elif cluster_id == "SKILL_CLUSTER::next-state-signal-adaptation":
        if reports["next_state_consumer"].get("recommended_next_step") == "hold_consumer_as_audit_only":
            blockers.append("current next-state consumer step is explicitly hold_consumer_as_audit_only")
    elif cluster_id == "SKILL_CLUSTER::graph-control-sidecars":
        if "not yet batch-admitted into the active runtime skill registry" in combined_text:
            blockers.append("current graph/control tranche is explicitly held outside the live runtime skill set")
    return blockers


def build_a2_source_family_lane_selection_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    selection_scope = str(ctx.get("selection_scope", "bounded_source_family_lane")).strip()
    scope_valid = selection_scope == "bounded_source_family_lane"

    source_corpus_text = _load_text(root / SOURCE_CORPUS_PATH)
    tracker_text = _load_text(root / TRACKER_PATH)
    build_plan_text = _load_text(root / BUILD_PLAN_PATH)
    cluster_map_text = _load_text(root / CLUSTER_MAP_PATH)
    combined_text = "\n".join([source_corpus_text, tracker_text, build_plan_text, cluster_map_text])

    reports = {
        "lev_promotion": _load_json(root / LEV_PROMOTION_REPORT),
        "next_state_consumer": _load_json(root / NEXT_STATE_CONSUMER_REPORT),
        "witness_memory_retriever": _load_json(root / WITNESS_MEMORY_RETRIEVER_REPORT),
        "evermem_backend": _load_json(root / A2_EVERMEM_REACHABILITY_REPORT),
    }

    issues: list[str] = []
    hold_reasons: list[str] = []
    if not scope_valid:
        issues.append("selection_scope widened beyond bounded source-family lane reselection")
    lev_closed = reports["lev_promotion"].get("has_current_unopened_cluster") is False
    if not lev_closed:
        issues.append("lev promotion lane still has an unopened candidate; non-lev reselection would be premature")

    candidate_clusters: list[dict[str, Any]] = []
    for candidate in CANDIDATE_CLUSTERS:
        members = [_member_record(root, member) for member in candidate["members"]]
        present_member_count = sum(1 for member in members if member["exists"])
        blockers = _candidate_blockers(candidate["cluster_id"], reports, combined_text)
        cluster_record = {
            **candidate,
            "members": members,
            "present_member_count": present_member_count,
            "already_landed": _already_landed_in_cluster_map(candidate["cluster_id"], cluster_map_text),
            "eligible_for_next_selection": False,
            "blocking_reasons": blockers,
        }
        if cluster_record["already_landed"]:
            cluster_record["blocking_reasons"] = [
                *cluster_record["blocking_reasons"],
                "cluster already has a bounded landed first slice",
            ]
        cluster_record["eligible_for_next_selection"] = (
            scope_valid
            and present_member_count == len(members)
            and not cluster_record["blocking_reasons"]
        )
        candidate_clusters.append(cluster_record)

    candidate_clusters.sort(
        key=lambda item: (
            not bool(item["eligible_for_next_selection"]),
            -int(item["score"]),
            item["risk_level"],
            item["cluster_id"],
        )
    )

    recommended_cluster = next(
        (item for item in candidate_clusters if item["eligible_for_next_selection"]),
        None,
    )
    fallback_cluster = None
    if recommended_cluster is not None:
        for item in candidate_clusters:
            if item["cluster_id"] == recommended_cluster["cluster_id"]:
                continue
            if item["eligible_for_next_selection"]:
                fallback_cluster = item
                break

    if recommended_cluster is None and not issues:
        hold_reasons.append("no bounded source-family lane is currently eligible for explicit reselection")

    if not scope_valid or not lev_closed:
        selection_state = "blocked_scope_or_lev"
        recommended_next_step = ""
        status = "attention_required"
    elif recommended_cluster is None:
        selection_state = "hold_no_eligible_lane"
        recommended_next_step = "hold_all_non_lev_lanes_until_explicit_reopen"
        status = "ok"
    else:
        selection_state = "recommend_bounded_lane"
        recommended_next_step = "open_one_bounded_first_slice_only"
        status = "ok"

    report = {
        "schema": "A2_SOURCE_FAMILY_LANE_SELECTION_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": "SKILL_CLUSTER::skill-source-intake",
        "slice_id": "a2-source-family-lane-selector-operator",
        "source_family": "front_door_corpus_and_imported_cluster_map",
        "selection_scope": selection_scope,
        "selection_state": selection_state,
        "recommended_next_step": recommended_next_step,
        "lev_selector_closed": lev_closed,
        "candidate_count": len(candidate_clusters),
        "candidate_clusters": candidate_clusters,
        "recommended_next_cluster": recommended_cluster or {},
        "fallback_cluster": fallback_cluster or {},
        "recommended_actions": [
            "Keep this selector audit-only and treat the recommendation as a bounded controller input, not as an already-landed slice.",
            "If the recommended lane is opened next, land one first audit slice only and keep runtime, training, service, and migration claims out.",
            "Keep the currently held lev, next-state, graph-sidecar, and EverMem lanes fenced until their own explicit blockers change.",
        ],
        "issues": issues,
        "hold_reasons": hold_reasons,
        "non_goals": list(DEFAULT_NON_GOALS),
    }

    packet = {
        "schema": "A2_SOURCE_FAMILY_LANE_SELECTION_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "selection_operator": report["slice_id"],
        "selection_scope": selection_scope,
        "selection_state": selection_state,
        "recommended_next_step": recommended_next_step,
        "allow_selector_slice": True,
        "allow_runtime_live_claims": False,
        "allow_training": False,
        "allow_external_runtime_import": False,
        "allow_registry_mutation": False,
        "recommended_next_cluster_id": recommended_cluster.get("cluster_id", "") if recommended_cluster else "",
        "recommended_first_slice_id": recommended_cluster.get("recommended_first_slice_id", "") if recommended_cluster else "",
        "fallback_cluster_id": fallback_cluster.get("cluster_id", "") if fallback_cluster else "",
        "fallback_first_slice_id": fallback_cluster.get("recommended_first_slice_id", "") if fallback_cluster else "",
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 Source-Family Lane Selection Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- selection_scope: `{report.get('selection_scope', '')}`",
        f"- selection_state: `{report.get('selection_state', '')}`",
        f"- lev_selector_closed: `{report.get('lev_selector_closed', False)}`",
        f"- candidate_count: `{report.get('candidate_count', 0)}`",
        f"- recommended_next_cluster_id: `{packet.get('recommended_next_cluster_id', '')}`",
        f"- recommended_first_slice_id: `{packet.get('recommended_first_slice_id', '')}`",
        f"- fallback_cluster_id: `{packet.get('fallback_cluster_id', '')}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        "",
        "## Recommended Actions",
    ]
    lines.extend(f"- {line}" for line in report.get("recommended_actions", []))
    lines.extend(["", "## Hold Reasons"])
    hold_reasons = report.get("hold_reasons", [])
    lines.extend(f"- {item}" for item in hold_reasons) if hold_reasons else lines.append("- none")
    lines.extend(["", "## Issues"])
    issues = report.get("issues", [])
    lines.extend(f"- {item}" for item in issues) if issues else lines.append("- none")
    lines.extend(["", "## Candidate Clusters"])
    for candidate in report.get("candidate_clusters", []):
        lines.append(f"- `{candidate.get('cluster_id', '')}`")
        lines.append(f"  - eligible_for_next_selection: `{candidate.get('eligible_for_next_selection', False)}`")
        lines.append(f"  - recommended_first_slice_id: `{candidate.get('recommended_first_slice_id', '')}`")
        blockers = candidate.get("blocking_reasons", [])
        if blockers:
            lines.append(f"  - blocking_reasons: `{'; '.join(blockers)}`")
    lines.extend(["", "## Non-Goals"])
    lines.extend(f"- {line}" for line in report.get("non_goals", []))
    lines.append("")
    return "\n".join(lines)


def run_a2_source_family_lane_selection(ctx: dict[str, Any]) -> dict[str, Any]:
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_a2_source_family_lane_selection_report(root, ctx)

    json_path = _resolve_output_path(root, ctx.get("report_json_path"), LANE_SELECTION_REPORT_JSON)
    md_path = _resolve_output_path(root, ctx.get("report_md_path"), LANE_SELECTION_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), LANE_SELECTION_PACKET_JSON)

    _write_json(json_path, report)
    _write_text(md_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    return {
        "status": report["status"],
        "report_json_path": str(json_path),
        "report_md_path": str(md_path),
        "packet_path": str(packet_path),
        "recommended_next_cluster_id": packet["recommended_next_cluster_id"],
        "recommended_first_slice_id": packet["recommended_first_slice_id"],
    }


if __name__ == "__main__":
    print(json.dumps(run_a2_source_family_lane_selection({}), indent=2, sort_keys=True))
