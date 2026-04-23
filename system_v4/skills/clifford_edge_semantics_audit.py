"""
clifford_edge_semantics_audit.py

Audit the smallest honest Clifford or geometric-algebra edge-semantics sidecar
the current graph stack can support.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

LOW_CONTROL_GRAPH = "system_v4/a2_state/graphs/a2_low_control_graph_v1.json"
PYG_AUDIT_JSON = "system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json"
TOPONETX_AUDIT_JSON = "system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json"
SKILL_POLICY_JSON = "system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_AUDIT__CURRENT__v1.json"
REPORT_JSON = "system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.json"
REPORT_MD = "system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.md"
PACKET_JSON = "system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_PACKET__CURRENT__v1.json"

PREFERRED_INTERPRETER = sys.executable
ADMITTED_RELATIONS = ("DEPENDS_ON", "EXCLUDES", "STRUCTURALLY_RELATED", "RELATED_TO")
FORBIDDEN_RELATIONS = ("OVERLAPS",)
DEFERRED_GA_FIELDS = [
    "entropy_state",
    "correlation_entropy",
    "orientation_basis",
    "clifford_grade",
    "obstruction_score",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_math_env(root: Path) -> None:
    cache_root = root / "work" / "audit_tmp" / "mplcache"
    cache_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_root))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_root))


def _verify_math_sidecars(root: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    _prepare_math_env(root)
    result: dict[str, Any] = {}
    code = """
import json
from clifford import Cl
import clifford, kingdon
layout, blades = Cl(3)
e1 = blades['e1']; e2 = blades['e2']; e3 = blades['e3']
mv = 1 + 2*e1 + 3*(e1 ^ e2) + 4*(e1 ^ e2 ^ e3)
alg = kingdon.Algebra(3)
a = alg.vector([1,0,0]); b = alg.vector([0,1,0])
print(json.dumps({
  "clifford": {
    "available": True,
    "version": getattr(clifford, "__version__", "unknown"),
    "proof_signature": "Cl(3)",
    "grade_count": len(layout.gradeList),
    "sample_multivector": str(mv),
  },
  "kingdon": {
    "available": True,
    "version": getattr(kingdon, "__version__", "unknown"),
    "proof_signature": "Algebra(3)",
    "sample_product": str(a * b),
  }
}))
""".strip()
    interpreter = root / PREFERRED_INTERPRETER
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", os.environ.get("MPLCONFIGDIR", str(root / "work" / "audit_tmp" / "mplcache")))
    env.setdefault("XDG_CACHE_HOME", os.environ.get("XDG_CACHE_HOME", str(root / "work" / "audit_tmp" / "mplcache")))

    if interpreter.exists():
        completed = subprocess.run(
            [str(interpreter), "-c", code],
            capture_output=True,
            text=True,
            env=env,
        )
        if completed.returncode == 0:
            try:
                parsed = json.loads((completed.stdout or "").strip())
                return parsed, issues
            except json.JSONDecodeError as exc:
                issues.append(f"preferred interpreter emitted unreadable math-sidecar proof: {exc}")
        else:
            issues.append(
                f"preferred interpreter math-sidecar proof failed: {(completed.stderr or completed.stdout).strip()}"
            )
    else:
        issues.append(f"preferred interpreter missing: {interpreter}")

    result["clifford"] = {"available": False}
    result["kingdon"] = {"available": False}
    return result, issues


def _collect_edge_payload_truth(root: Path) -> dict[str, Any]:
    low_control = _load_json(root / LOW_CONTROL_GRAPH)
    edges = low_control.get("edges", []) if isinstance(low_control, dict) else []
    if not isinstance(edges, list):
        edges = []

    relation_attr_counts: dict[str, Counter[str]] = defaultdict(Counter)
    relation_numeric_attr_counts: dict[str, Counter[str]] = defaultdict(Counter)
    all_attr_keys = Counter()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        relation = str(edge.get("relation", "?"))
        attrs = edge.get("attributes", {}) or {}
        for key, value in attrs.items():
            all_attr_keys[key] += 1
            relation_attr_counts[relation][key] += 1
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                relation_numeric_attr_counts[relation][key] += 1

    return {
        "all_attr_keys": dict(all_attr_keys),
        "relation_attr_counts": {rel: dict(counter) for rel, counter in relation_attr_counts.items()},
        "relation_numeric_attr_counts": {rel: dict(counter) for rel, counter in relation_numeric_attr_counts.items()},
    }


def _render_markdown(report: dict[str, Any]) -> str:
    safe_lines = [f"- {item}" for item in report.get("safe_now", [])]
    deferred_lines = [f"- {item}" for item in report.get("deferred_now", [])]
    forbidden_lines = [f"- {item}" for item in report.get("forbidden_now", [])]
    next_lines = [f"- {item}" for item in report.get("recommended_next_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# Clifford Edge Semantics Audit",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- audit_only: `{report['audit_only']}`",
            f"- do_not_promote: `{report['do_not_promote']}`",
            "",
            "## Safe Now",
            *safe_lines,
            "",
            "## Deferred Now",
            *deferred_lines,
            "",
            "## Forbidden Now",
            *forbidden_lines,
            "",
            "## Recommended Next Actions",
            *next_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_clifford_edge_semantics_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = ctx or {}
    root = Path(repo_root).resolve()
    issues: list[str] = []

    for rel in (LOW_CONTROL_GRAPH, PYG_AUDIT_JSON, TOPONETX_AUDIT_JSON, SKILL_POLICY_JSON):
        if not (root / rel).exists():
            issues.append(f"missing required surface: {rel}")

    payload_truth = _collect_edge_payload_truth(root)
    math_check, math_issues = _verify_math_sidecars(root)
    issues.extend(math_issues)

    status = "ok" if not issues else "attention_required"
    report = {
        "schema": "CLIFFORD_EDGE_SEMANTICS_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "preferred_interpreter": PREFERRED_INTERPRETER,
        "low_control_probe": LOW_CONTROL_GRAPH,
        "supporting_pyg_audit": PYG_AUDIT_JSON,
        "supporting_toponetx_audit": TOPONETX_AUDIT_JSON,
        "supporting_skill_policy_audit": SKILL_POLICY_JSON,
        "math_sidecar_check": math_check,
        "edge_payload_truth": payload_truth,
        "safe_now": [
            "Treat Clifford semantics as a read-only sidecar over admitted low-control relations only: DEPENDS_ON, EXCLUDES, STRUCTURALLY_RELATED, RELATED_TO.",
            "Use current scalar/string edge attributes only as carriers or source fields for future GA payload construction; keep canonical graph storage unchanged.",
            "Prefer clifford as the primary GA math sidecar now that it is installed and passes a live Cl(3) multivector check.",
            "Treat kingdon as an optional PyTorch-coupled bridge sidecar, not the primary semantic owner.",
        ],
        "deferred_now": [
            "Keep entropy_state, correlation_entropy, orientation_basis, clifford_grade, and obstruction_score as deferred edge payload fields rather than live canonical attributes.",
            "Keep any grade-specific or basis-specific encoding in sidecar packets or projections until an explicit edge payload schema lands.",
            "Keep SKILL edges out of GA semantics while skill-to-kernel seeding remains fail-closed.",
        ],
        "forbidden_now": [
            "Do not treat Clifford or GA structures as canonical graph storage.",
            "Do not attach GA semantics to OVERLAPS while that relation remains quarantined out of equal-weight topology.",
            "Do not use Clifford semantics as a workaround for missing owner-bound skill-to-kernel identity.",
        ],
        "recommended_next_actions": [
            "If the graph lane continues, land one bounded edge-payload-schema audit or probe over admitted low-control relations before any runtime mutation or training claim.",
            "Keep kingdon in optional bridge status until a concrete PyG-coupled payload path is needed.",
            "Hold run_real_ratchet dispatch/refactor debt in watch-only mode; it remains secondary to the current graph-side bounded tranche.",
        ],
        "issues": issues,
    }
    packet = {
        "schema": "CLIFFORD_EDGE_SEMANTICS_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "allow_training": False,
        "allow_canonical_graph_replacement": False,
        "allow_read_only_ga_sidecar": True,
        "preferred_interpreter": PREFERRED_INTERPRETER,
        "recommended_next_slice_ids": [
            "edge-payload-schema-audit",
        ],
        "deferred_ga_fields": DEFERRED_GA_FIELDS,
    }
    return report, packet


def run_clifford_edge_semantics_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT
    root = Path(repo_root).resolve()
    report, packet = build_clifford_edge_semantics_report(root, ctx)
    report_path = Path(ctx.get("report_json_path") or (root / REPORT_JSON))
    markdown_path = Path(ctx.get("report_md_path") or (root / REPORT_MD))
    packet_path = Path(ctx.get("packet_path") or (root / PACKET_JSON))
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report))
    _write_json(packet_path, packet)
    return {
        "status": report["status"],
        "report_json_path": str(report_path),
        "report_md_path": str(markdown_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    result = run_clifford_edge_semantics_audit({"repo_root": str(REPO_ROOT)})
    print(json.dumps(result, indent=2, sort_keys=True))
