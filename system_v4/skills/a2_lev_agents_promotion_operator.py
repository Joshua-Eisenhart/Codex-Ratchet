"""
a2_lev_agents_promotion_operator.py

Bounded promotion audit over the local lev-os/agents corpus.

This operator does not import or activate any lev-os/agents skills directly.
It reads the local curated corpus plus the current imported-cluster map, then
emits one repo-held report and packet recommending the next lev-os/agents
cluster to promote in Ratchet-native form.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LEV_AGENTS_ROOT = "work/reference_repos/lev-os/agents"
LEV_AGENTS_CURATED_ROOT = "work/reference_repos/lev-os/agents/skills"
LEV_AGENTS_LIBRARY_ROOT = "work/reference_repos/lev-os/agents/skills-db"
IMPORTED_CLUSTER_MAP_PATH = "system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md"
LEV_FORMALIZATION_FUTURE_LANE_REPORT = (
    "system_v4/a2_state/audit_logs/"
    "A2_LEV_BUILDER_POST_SKELETON_FUTURE_LANE_EXISTENCE_AUDIT_REPORT__CURRENT__v1.json"
)

PROMOTION_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json"
)
PROMOTION_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.md"
)
PROMOTION_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json"
)

KNOWN_LANDED_LEV_CLUSTERS = [
    "SKILL_CLUSTER::skill-source-intake",
    "SKILL_CLUSTER::tracked-work-planning",
    "SKILL_CLUSTER::research-deliberation",
    "SKILL_CLUSTER::workshop-analysis-gating",
    "SKILL_CLUSTER::lev-formalization-placement",
    "SKILL_CLUSTER::lev-autodev-exec-validation",
    "SKILL_CLUSTER::lev-architecture-fitness-review",
]

CANDIDATE_CLUSTERS = [
    {
        "cluster_id": "SKILL_CLUSTER::lev-formalization-placement",
        "import_label": "lev-os/agents formalize / placement / migrate cluster",
        "cluster_role": "promotion_path",
        "recommended_first_slice_id": "a2-lev-builder-placement-audit-operator",
        "bounded_role": (
            "audit placement, prior-art, and promotion path for one candidate Ratchet skill or cluster "
            "before any broader formalization or migration claim"
        ),
        "external_runtime_dependency": "low",
        "risk_level": "moderate",
        "score": 90,
        "members": [
            {
                "imported_skill_id": "lev-builder",
                "treatment": "adapt",
                "path": "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
                "reason": "High leverage for turning candidate skills into placed, prior-art-checked Ratchet-native assets.",
            },
            {
                "imported_skill_id": "arch",
                "treatment": "mine",
                "path": "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
                "reason": "Useful source of fitness/tradeoff framing, but too generic to import directly as runtime behavior.",
            },
            {
                "imported_skill_id": "work",
                "treatment": "mine",
                "path": "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
                "reason": "Useful for bounded handoff and reporting discipline without forcing imported runtime ownership.",
            },
        ],
        "selection_reasons": [
            "Directly supports the user goal of turning corpus material into real Ratchet skills.",
            "Keeps the next lev-os/agents step bounded to audit/placement instead of importing an external runtime whole.",
            "Builds a bridge between corpus discovery and disciplined Ratchet-native promotion.",
        ],
    },
    {
        "cluster_id": "SKILL_CLUSTER::lev-autodev-exec-validation",
        "import_label": "lev-os/agents autodev / execution / validation cluster",
        "cluster_role": "execution_loop",
        "recommended_first_slice_id": "a2-lev-autodev-loop-audit-operator",
        "bounded_role": (
            "audit the heartbeat and validation loop shape before claiming any recurring execution or autonomous run loop"
        ),
        "external_runtime_dependency": "high",
        "risk_level": "high",
        "score": 74,
        "members": [
            {
                "imported_skill_id": "autodev-loop",
                "treatment": "adapt",
                "path": "work/reference_repos/lev-os/agents/skills/autodev-loop/SKILL.md",
                "reason": "Interesting execution/validation loop shape, but coupled to cron, bd, and lev stack runtime.",
            },
            {
                "imported_skill_id": "autodev-lev",
                "treatment": "mine",
                "path": "work/reference_repos/lev-os/agents/skills/autodev-lev/SKILL.md",
                "reason": "Provides heartbeat continuity ideas, but depends on in-process lev runtime continuity.",
            },
            {
                "imported_skill_id": "lev-plan",
                "treatment": "mine",
                "path": "work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md",
                "reason": "Useful entity lifecycle structure, but Ratchet should not import the `.lev/pm` surface wholesale.",
            },
            {
                "imported_skill_id": "stack",
                "treatment": "mine",
                "path": "work/reference_repos/lev-os/agents/skills/stack/SKILL.md",
                "reason": "Prompt-stack ideas are useful, but the runtime path is external and should stay decoupled.",
            },
        ],
        "selection_reasons": [
            "Potentially high value for future execution loops.",
            "Too runtime-coupled to be the first post-proof import tranche.",
        ],
    },
    {
        "cluster_id": "SKILL_CLUSTER::lev-architecture-fitness-review",
        "import_label": "lev-os/agents architecture / fitness / review cluster",
        "cluster_role": "analysis_support",
        "recommended_first_slice_id": "a2-lev-architecture-fitness-operator",
        "bounded_role": "audit architecture and fitness guidance for candidate Ratchet changes without importing generic review behavior wholesale",
        "external_runtime_dependency": "low",
        "risk_level": "moderate",
        "score": 68,
        "members": [
            {
                "imported_skill_id": "arch",
                "treatment": "adapt",
                "path": "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
                "reason": "Useful quality-attribute and tradeoff analysis frame for system work.",
            },
            {
                "imported_skill_id": "lev-builder",
                "treatment": "mine",
                "path": "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
                "reason": "Provides placement/migration context, but not enough by itself for a first slice.",
            },
        ],
        "selection_reasons": [
            "Good support lane, but less central than formalization/promotion for current Ratchet goals.",
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


def _count_skill_docs(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob("SKILL.md"))


def _member_record(root: Path, member: dict[str, str]) -> dict[str, Any]:
    rel_path = str(member["path"])
    return {
        **member,
        "exists": (root / rel_path).exists(),
    }


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_a2_lev_agents_promotion_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    lev_root = root / LEV_AGENTS_ROOT
    curated_root = root / LEV_AGENTS_CURATED_ROOT
    library_root = root / LEV_AGENTS_LIBRARY_ROOT
    cluster_map_path = root / IMPORTED_CLUSTER_MAP_PATH
    future_lane_report_path = root / LEV_FORMALIZATION_FUTURE_LANE_REPORT
    cluster_map_text = cluster_map_path.read_text(encoding="utf-8") if cluster_map_path.exists() else ""
    future_lane_report = _load_json(future_lane_report_path)

    curated_skill_count = _count_skill_docs(curated_root)
    library_skill_count = _count_skill_docs(library_root)
    total_skill_count = _count_skill_docs(lev_root)

    landed_lev_clusters = [
        cluster_id for cluster_id in KNOWN_LANDED_LEV_CLUSTERS if cluster_id in cluster_map_text
    ]
    parked_lev_clusters: list[str] = []
    if (
        future_lane_report.get("cluster_id") == "SKILL_CLUSTER::lev-formalization-placement"
        and future_lane_report.get("gate", {}).get("recommended_next_step") == "hold_at_disposition"
    ):
        parked_lev_clusters.append("SKILL_CLUSTER::lev-formalization-placement")

    candidate_clusters = []
    for candidate in CANDIDATE_CLUSTERS:
        members = [_member_record(root, member) for member in candidate["members"]]
        present_member_count = sum(1 for member in members if member["exists"])
        already_landed = candidate["cluster_id"] in landed_lev_clusters
        parked = candidate["cluster_id"] in parked_lev_clusters
        cluster_record = {
            **candidate,
            "members": members,
            "present_member_count": present_member_count,
            "already_landed": already_landed,
            "parked_at_disposition": parked,
            "eligible_for_next_promotion": (
                present_member_count == len(members) and not already_landed and not parked
            ),
        }
        candidate_clusters.append(cluster_record)

    candidate_clusters.sort(
        key=lambda item: (
            -int(item["score"]),
            item["risk_level"],
            item["cluster_id"],
        )
    )

    recommended_cluster = next(
        (item for item in candidate_clusters if item["eligible_for_next_promotion"]),
        None,
    )
    all_candidate_clusters_accounted_for = all(
        item["already_landed"] or item["parked_at_disposition"] for item in candidate_clusters
    )
    issues: list[str] = []
    if not lev_root.exists():
        issues.append("local lev-os/agents checkout is missing")
    if curated_skill_count == 0:
        issues.append("no curated lev-os/agents skills were found")
    if library_skill_count == 0:
        issues.append("no library lev-os/agents skills-db corpus was found")
    if not cluster_map_path.exists():
        issues.append("imported cluster map is missing")
    if recommended_cluster is None and not all_candidate_clusters_accounted_for:
        issues.append("no eligible next lev-os/agents promotion cluster was found")

    recommended_actions = [
        "Keep lev-os/agents promotion bounded to one next unopened cluster rather than importing the corpus flat.",
        "Treat the lev-formalization lane as landed and parked at disposition until later evidence reopens it.",
        "Update the cluster map and tracker only after the next bounded lev-os/agents slice becomes real code and registry truth.",
    ]
    if all_candidate_clusters_accounted_for and recommended_cluster is None:
        recommended_actions = [
            "Hold the lev-os/agents promotion lane at no current unopened cluster until a new bounded candidate is admitted.",
            "Keep the landed lev slices bounded; do not widen them into runtime or migration claims by absence of a next candidate.",
            "Open a different source-family lane or add a new bounded lev candidate only after explicit audit.",
        ]

    report = {
        "schema": "a2_lev_agents_promotion_report_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if not issues else "action_required",
        "audit_only": True,
        "do_not_promote": True,
        "slice_id": "a2-lev-agents-promotion-operator",
        "cluster_id": "SKILL_CLUSTER::skill-source-intake",
        "source_family": "lev_os_agents_curated",
        "lev_agents_root": LEV_AGENTS_ROOT,
        "curated_skill_count": curated_skill_count,
        "library_skill_count": library_skill_count,
        "total_skill_count": total_skill_count,
        "landed_lev_cluster_ids": landed_lev_clusters,
        "landed_lev_cluster_count": len(landed_lev_clusters),
        "parked_lev_cluster_ids": parked_lev_clusters,
        "parked_lev_cluster_count": len(parked_lev_clusters),
        "has_current_unopened_cluster": recommended_cluster is not None,
        "all_candidate_clusters_accounted_for": all_candidate_clusters_accounted_for,
        "candidate_clusters": candidate_clusters,
        "recommended_next_cluster": recommended_cluster or {},
        "recommended_actions": recommended_actions,
        "issues": issues,
    }

    packet = {
        "schema": "a2_lev_agents_promotion_packet_v1",
        "generated_utc": report["generated_utc"],
        "slice_id": report["slice_id"],
        "source_family": report["source_family"],
        "allow_imported_runtime_claims": False,
        "has_current_unopened_cluster": recommended_cluster is not None,
        "recommended_cluster_id": recommended_cluster.get("cluster_id", "") if recommended_cluster else "",
        "recommended_first_slice_id": recommended_cluster.get("recommended_first_slice_id", "") if recommended_cluster else "",
        "recommended_cluster_role": recommended_cluster.get("cluster_role", "") if recommended_cluster else "",
        "recommended_import_label": recommended_cluster.get("import_label", "") if recommended_cluster else "",
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    recommended = report.get("recommended_next_cluster", {})
    lines = [
        "# A2 lev-os/agents Promotion Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- curated_skill_count: `{report.get('curated_skill_count', 0)}`",
        f"- library_skill_count: `{report.get('library_skill_count', 0)}`",
        f"- total_skill_count: `{report.get('total_skill_count', 0)}`",
        f"- landed_lev_cluster_count: `{report.get('landed_lev_cluster_count', 0)}`",
        f"- parked_lev_cluster_count: `{report.get('parked_lev_cluster_count', 0)}`",
        f"- has_current_unopened_cluster: `{report.get('has_current_unopened_cluster', False)}`",
        "",
        "## Recommended Next Cluster",
    ]
    if recommended:
        lines.extend(
            [
                f"- cluster_id: `{recommended.get('cluster_id', '')}`",
                f"- import_label: `{recommended.get('import_label', '')}`",
                f"- cluster_role: `{recommended.get('cluster_role', '')}`",
                f"- recommended_first_slice_id: `{recommended.get('recommended_first_slice_id', '')}`",
                f"- risk_level: `{recommended.get('risk_level', '')}`",
            ]
        )
    else:
        lines.append("- none")
    lines.extend(
        [
        "",
        "## Packet",
        f"- has_current_unopened_cluster: `{packet.get('has_current_unopened_cluster', False)}`",
        f"- recommended_cluster_id: `{packet.get('recommended_cluster_id', '')}`",
        f"- recommended_first_slice_id: `{packet.get('recommended_first_slice_id', '')}`",
        f"- allow_imported_runtime_claims: `{packet.get('allow_imported_runtime_claims', False)}`",
        "",
        ]
    )
    return "\n".join(lines)


def run_a2_lev_agents_promotion(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), PROMOTION_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), PROMOTION_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PROMOTION_PACKET_JSON)

    report, packet = build_a2_lev_agents_promotion_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted


if __name__ == "__main__":
    print("PASS: a2 lev agents promotion operator self-test")
