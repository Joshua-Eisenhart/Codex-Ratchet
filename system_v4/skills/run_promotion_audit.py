"""
run_promotion_audit.py — Batch promotion pipeline for the A2 Graph Refinery.

Scans all A2-2 candidate nodes, applies deterministic promotion gates,
and identifies which candidates are ready for A2-1 kernel admission.

Gates (inspired by PROMOTION_BINDING_v1 spec):
  G1: Source coverage — candidate must be backed by >= MIN_SOURCES source docs
  G2: Cross-reference density — candidate must connect to >= MIN_EDGES other concepts
  G3: Authority check — CROSS_VALIDATED/STRIPPED concepts rank higher than SOURCE_CLAIM
  G4: Contradiction absence — no unresolved contradictions blocking promotion

V4.1: Authority is now entropy-gradient based (SOURCE_CLAIM → CROSS_VALIDATED →
STRIPPED → RATCHETED). Nothing is canon until ratcheted through B + SIM + graveyard.

Usage:
    python3 -c "import sys; sys.path.insert(0, '.'); exec(open('system_v4/skills/run_promotion_audit.py').read())"

References:
    - system_v3/control_plane_bundle_work/.../PROMOTION_BINDING_v1.md
    - lev-os/agents skill pattern (folder-per-skill, metadata, discovery)
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery, RefineryLayer


# ── Gate Thresholds ──────────────────────────────────────────────────
MIN_SOURCES = 1          # Gate G1: minimum source documents backing a concept
MIN_EDGES = 1            # Gate G2: minimum edge connections

# Gate G3: Authority level scoring (entropy-gradient)
# Nothing is canon until ratcheted — higher levels = more refinement done
AUTHORITY_SCORES = {
    "RATCHETED": 5,          # survived B + SIM + graveyard
    "STRIPPED": 3,           # Rosetta cold-core extracted, pure math
    "CROSS_VALIDATED": 2,    # verified against other sources
    "SOURCE_CLAIM": 0,       # first reading, no verification
}
# Legacy fallbacks
AUTHORITY_SCORES["CANON"] = 0     # was wrongly assigned, treat as SOURCE_CLAIM
AUTHORITY_SCORES["DRAFT"] = 0
AUTHORITY_SCORES["NONCANON"] = 0


def load_graph(workspace: Path) -> dict:
    """Load the graph JSON."""
    gpath = workspace / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
    return json.loads(gpath.read_text(encoding="utf-8"))


def build_edge_index(edges: list[dict]) -> dict[str, list[dict]]:
    """Build adjacency index: node_id -> list of edges touching it."""
    idx = defaultdict(list)
    for e in edges:
        src = e.get("source_id", "")
        tgt = e.get("target_id", "")
        if src:
            idx[src].append(e)
        if tgt:
            idx[tgt].append(e)
    return dict(idx)


def score_candidate(node: dict, edge_index: dict[str, list[dict]], node_id: str, all_nodes: dict) -> dict:
    """Score a candidate node for kernel promotion readiness."""
    edges = edge_index.get(node_id, [])
    desc = node.get("description", "")
    # Read authority from top-level field (post-migration)
    authority = node.get("authority", node.get("properties", {}).get("authority", "SOURCE_CLAIM")).upper()

    # Gate G1: Source coverage — check actual SOURCE_DOCUMENT lineage
    source_edges = []
    for e in edges:
        # Check if the OTHER end of this edge is a SOURCE_DOCUMENT
        other_id = e.get("target_id") if e.get("source_id") == node_id else e.get("source_id", "")
        other_node = all_nodes.get(other_id, {})
        if other_node.get("node_type") == "SOURCE_DOCUMENT":
            source_edges.append(e)
    source_count = len(source_edges)
    g1_pass = source_count >= MIN_SOURCES

    # Gate G2: Cross-reference density
    edge_count = len(edges)
    g2_pass = edge_count >= MIN_EDGES

    # Gate G3: Authority score (entropy-gradient)
    authority_score = AUTHORITY_SCORES.get(authority, 0)
    authority_label = authority if authority in AUTHORITY_SCORES else "SOURCE_CLAIM"
    g3_pass = authority_score >= 0  # All levels pass; higher = better ranking

    # Gate G4: No contradiction edges
    contradiction_edges = [e for e in edges if "CONTRADICTION" in e.get("relation", "").upper()]
    g4_pass = len(contradiction_edges) == 0

    # Composite score
    composite = source_count + edge_count + authority_score
    all_gates_pass = g1_pass and g2_pass and g3_pass and g4_pass

    return {
        "node_id": node_id,
        "name": node.get("name", node_id),
        "authority": authority_label,
        "source_count": source_count,
        "edge_count": edge_count,
        "contradiction_count": len(contradiction_edges),
        "authority_score": authority_score,
        "composite_score": composite,
        "g1_source_coverage": g1_pass,
        "g2_cross_reference": g2_pass,
        "g3_authority": g3_pass,
        "g4_no_contradictions": g4_pass,
        "all_gates_pass": all_gates_pass,
        "recommendation": "PROMOTE_TO_A2_LOW" if all_gates_pass and authority_score >= 2 else
                         "HOLD_CANDIDATE" if all_gates_pass else
                         "NEEDS_WORK",
    }


def run_promotion_audit(workspace: Path = Path("."), auto_promote: bool = False) -> dict:
    """Run the full promotion audit pipeline."""
    r = A2GraphRefinery(str(workspace))
    sid = r.start_session("PROMOTION_AUDIT_SESSION")

    data = load_graph(workspace)
    nodes = data["nodes"]
    edges = data["edges"]
    edge_index = build_edge_index(edges)

    # Find all A2-2 candidates
    candidates = {
        k: v for k, v in nodes.items()
        if v.get("trust_zone") == "A2_2_CANDIDATE"
        and v.get("node_type") != "SOURCE_DOCUMENT"
    }

    print(f"=== PROMOTION AUDIT ===")
    print(f"Total candidates: {len(candidates)}")

    # Score each
    scored = []
    for nid, node in candidates.items():
        result = score_candidate(node, edge_index, nid, nodes)
        scored.append(result)

    # Sort by composite score descending
    scored.sort(key=lambda x: (-x["composite_score"], x["name"]))

    # Categorize
    promote_ready = [s for s in scored if s["recommendation"] == "PROMOTE_TO_A2_LOW"]
    hold = [s for s in scored if s["recommendation"] == "HOLD_CANDIDATE"]
    needs_work = [s for s in scored if s["recommendation"] == "NEEDS_WORK"]

    print(f"\nResults:")
    print(f"  PROMOTE_TO_A2_LOW: {len(promote_ready)}")
    print(f"  HOLD_CANDIDATE:    {len(hold)}")
    print(f"  NEEDS_WORK:        {len(needs_work)}")

    if promote_ready:
        print(f"\n--- A2-LOW-READY (top 10) ---")
        for s in promote_ready[:10]:
            print(f"  [{s['authority']:8s}] {s['name']:50s} score={s['composite_score']:3d}  "
                  f"sources={s['source_count']}  edges={s['edge_count']}")

    if hold:
        print(f"\n--- HOLD (top 10) ---")
        for s in hold[:10]:
            print(f"  [{s['authority']:8s}] {s['name']:50s} score={s['composite_score']:3d}  "
                  f"sources={s['source_count']}  edges={s['edge_count']}")

    # Auto-promote if requested
    promoted_count = 0
    if auto_promote and promote_ready:
        print(f"\n--- AUTO-PROMOTING {len(promote_ready)} nodes ---")
        for s in promote_ready:
            ok = r.promote_node(
                s["node_id"],
                RefineryLayer.A2_LOW,
                f"PROMOTION_AUDIT: all gates pass, authority={s['authority']}, score={s['composite_score']}"
            )
            if ok:
                promoted_count += 1
                print(f"  ✅ {s['name']}")
            else:
                print(f"  ❌ {s['name']} (promote_node failed)")

    # Write audit report
    report_dir = workspace / "system_v4" / "a2_state" / "audit_logs"
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    report_path = report_dir / f"PROMOTION_AUDIT_{ts}.md"

    report_lines = [
        f"# Promotion Audit — {ts}",
        f"",
        f"## Summary",
        f"- Candidates scanned: {len(candidates)}",
        f"- PROMOTE_TO_A2_LOW: {len(promote_ready)}",
        f"- HOLD_CANDIDATE: {len(hold)}",
        f"- NEEDS_WORK: {len(needs_work)}",
        f"- Auto-promoted: {promoted_count}",
        f"",
        f"## Kernel-Ready Candidates",
    ]
    for s in promote_ready:
        report_lines.append(
            f"- **{s['name']}** [{s['authority']}] score={s['composite_score']} "
            f"(sources={s['source_count']}, edges={s['edge_count']})"
        )
    report_lines.append(f"\n## Hold Candidates")
    for s in hold[:20]:
        report_lines.append(
            f"- {s['name']} [{s['authority']}] score={s['composite_score']}"
        )
    if len(hold) > 20:
        report_lines.append(f"- ... and {len(hold) - 20} more")

    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"\nAudit report: {report_path}")

    r.log_finding(f"Promotion audit: {len(promote_ready)} kernel-ready, {len(hold)} hold, {len(needs_work)} needs-work")
    log = r.end_session()
    print(f"Session: {log}")

    return {
        "candidates": len(candidates),
        "promote_ready": len(promote_ready),
        "hold": len(hold),
        "needs_work": len(needs_work),
        "promoted": promoted_count,
        "report": str(report_path),
    }


if __name__ == "__main__":
    auto = "--auto" in sys.argv
    result = run_promotion_audit(auto_promote=auto)
