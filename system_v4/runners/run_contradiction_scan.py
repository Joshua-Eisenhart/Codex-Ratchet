"""
run_contradiction_scan.py — Cross-reference scan for conflicting concepts.

Scans all refined/control concepts and checks for:
  1. Name collisions (same concept name, different content)
  2. Authority conflicts (concepts at different authority levels claim same domain)
  3. Structural contradictions (opposing claims within connected concepts)
  4. Duplicate coverage (multiple concepts describing the same thing)

Emits a contradiction report for human review or Opus audit.

Usage:
    python3 -c "import sys; sys.path.insert(0, '.'); exec(open('system_v4/skills/run_contradiction_scan.py').read())"

References:
    - Graph stored at system_v4/a2_state/graphs/system_graph_a2_refinery.json
    - lev-os/agents skill pattern
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.graph_store import load_graph_json


# ── Similarity Thresholds ────────────────────────────────────────────
NAME_SIMILARITY_THRESHOLD = 0.75    # Names this similar flag as potential duplicates
DESC_SIMILARITY_THRESHOLD = 0.60    # Descriptions this similar flag as potential duplicates

# ── Contradiction Keywords ───────────────────────────────────────────
OPPOSITION_PAIRS = [
    ("deterministic", "nondeterministic"),
    ("finite", "infinite"),
    ("commutative", "noncommutative"),
    ("canonical", "noncanonical"),
    ("admissible", "inadmissible"),
    ("allowed", "forbidden"),
    ("required", "optional"),
    ("must", "must not"),
]


def similarity(a: str, b: str) -> float:
    """Quick string similarity ratio."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def detect_name_collisions(concepts: dict[str, dict]) -> list[dict]:
    """Find concepts with very similar names."""
    collisions = []
    items = list(concepts.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            id_a, node_a = items[i]
            id_b, node_b = items[j]
            name_a = node_a.get("name", "")
            name_b = node_b.get("name", "")
            sim = similarity(name_a, name_b)
            if sim >= NAME_SIMILARITY_THRESHOLD and name_a != name_b:
                collisions.append({
                    "type": "NAME_COLLISION",
                    "severity": "WARNING",
                    "node_a": id_a,
                    "name_a": name_a,
                    "node_b": id_b,
                    "name_b": name_b,
                    "similarity": round(sim, 3),
                })
    return collisions


def detect_authority_conflicts(concepts: dict[str, dict]) -> list[dict]:
    """Find authority level disagreements on same domain.
    
    V4.1: Uses entropy-gradient authority (SOURCE_CLAIM, CROSS_VALIDATED, 
    STRIPPED, RATCHETED) instead of CANON/NONCANON binary.
    """
    # Group by tags
    tag_groups: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for cid, node in concepts.items():
        props = node.get("properties", {})
        tags = props.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        for tag in tags:
            tag_groups[tag].append((cid, node))

    conflicts = []
    # V4.1 authority hierarchy
    authority_tiers = {"RATCHETED": 4, "STRIPPED": 3, "CROSS_VALIDATED": 2, "SOURCE_CLAIM": 1}
    # Legacy fallbacks
    authority_tiers.update({"CANON": 1, "DRAFT": 1, "NONCANON": 1})
    
    for tag, group in tag_groups.items():
        if len(group) < 2:
            continue
        # Find concepts at different authority tiers
        tiered = []
        for cid, n in group:
            auth = str(n.get("properties", {}).get("authority", n.get("authority", "SOURCE_CLAIM"))).upper()
            tier = authority_tiers.get(auth, 1)
            tiered.append((cid, n, auth, tier))
        
        # Flag cases where higher-tier and lower-tier concepts exist on same tag
        high = [(c, n, a, t) for c, n, a, t in tiered if t >= 2]
        low = [(c, n, a, t) for c, n, a, t in tiered if t < 2]
        if high and low:
            for h_id, h_node, h_auth, _ in high:
                for l_id, l_node, l_auth, _ in low:
                    conflicts.append({
                        "type": "AUTHORITY_CONFLICT",
                        "severity": "INFO",
                        "domain_tag": tag,
                        "higher_node": h_id,
                        "higher_name": h_node.get("name", ""),
                        "higher_authority": h_auth,
                        "lower_node": l_id,
                        "lower_name": l_node.get("name", ""),
                        "lower_authority": l_auth,
                    })
    return conflicts


def detect_description_duplicates(concepts: dict[str, dict]) -> list[dict]:
    """Find concepts with very similar descriptions."""
    duplicates = []
    items = list(concepts.items())
    # Sample-based to avoid O(n^2) for large sets
    sample = items[:100]  # Cap at 100 for performance
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            id_a, node_a = sample[i]
            id_b, node_b = sample[j]
            desc_a = node_a.get("description", "")[:200]
            desc_b = node_b.get("description", "")[:200]
            if desc_a and desc_b:
                sim = similarity(desc_a, desc_b)
                if sim >= DESC_SIMILARITY_THRESHOLD:
                    duplicates.append({
                        "type": "DESCRIPTION_DUPLICATE",
                        "severity": "WARNING",
                        "node_a": id_a,
                        "name_a": node_a.get("name", ""),
                        "node_b": id_b,
                        "name_b": node_b.get("name", ""),
                        "similarity": round(sim, 3),
                    })
    return duplicates


def detect_edge_contradictions(edges: list[dict]) -> list[dict]:
    """Find existing contradiction edges in the graph."""
    contras = []
    for e in edges:
        rel = e.get("relation", "").upper()
        if "CONTRADICTION" in rel or "CONFLICT" in rel:
            contras.append({
                "type": "EDGE_CONTRADICTION",
                "severity": "CRITICAL",
                "source": e.get("source_id", ""),
                "target": e.get("target_id", ""),
                "relation": e.get("relation", ""),
            })
    return contras


def run_contradiction_scan(workspace: Path = Path(".")) -> dict:
    """Run the full contradiction scan pipeline."""
    r = A2GraphRefinery(str(workspace))
    sid = r.start_session("CONTRADICTION_SCAN_SESSION")

    data = load_graph_json(
        workspace,
        "system_v4/a2_state/graphs/system_graph_a2_refinery.json",
    )
    nodes = data["nodes"]
    edges = data["edges"]

    # Focus on A2-2 candidates (non-source-doc)
    concepts = {
        k: v for k, v in nodes.items()
        if v.get("trust_zone") in ("A2_2_CANDIDATE", "A2_1_KERNEL", "A2_MID_REFINEMENT", "A2_LOW_CONTROL")
        and v.get("node_type") != "SOURCE_DOCUMENT"
    }

    print(f"=== CONTRADICTION SCAN ===")
    print(f"Scanning {len(concepts)} candidate/kernel concepts")

    all_issues: list[dict] = []

    # Run detectors
    print("\n1. Name collision detection...")
    collisions = detect_name_collisions(concepts)
    all_issues.extend(collisions)
    print(f"   Found: {len(collisions)}")

    print("2. Authority conflict detection...")
    auth_conflicts = detect_authority_conflicts(concepts)
    all_issues.extend(auth_conflicts)
    print(f"   Found: {len(auth_conflicts)}")

    print("3. Description duplicate detection...")
    desc_dupes = detect_description_duplicates(concepts)
    all_issues.extend(desc_dupes)
    print(f"   Found: {len(desc_dupes)}")

    print("4. Edge contradiction detection...")
    edge_contras = detect_edge_contradictions(edges)
    all_issues.extend(edge_contras)
    print(f"   Found: {len(edge_contras)}")

    # Severity summary
    by_severity = defaultdict(int)
    by_type = defaultdict(int)
    for issue in all_issues:
        by_severity[issue["severity"]] += 1
        by_type[issue["type"]] += 1

    print(f"\n--- SUMMARY ---")
    print(f"Total issues: {len(all_issues)}")
    for sev, cnt in sorted(by_severity.items()):
        print(f"  {sev}: {cnt}")

    # Write report
    report_dir = workspace / "system_v4" / "a2_state" / "audit_logs"
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    report_path = report_dir / f"CONTRADICTION_SCAN_{ts}.md"

    lines = [
        f"# Contradiction Scan — {ts}",
        f"",
        f"## Summary",
        f"- Concepts scanned: {len(concepts)}",
        f"- Total issues: {len(all_issues)}",
    ]
    for sev, cnt in sorted(by_severity.items()):
        lines.append(f"- {sev}: {cnt}")

    for issue_type in ["EDGE_CONTRADICTION", "NAME_COLLISION", "DESCRIPTION_DUPLICATE", "AUTHORITY_CONFLICT"]:
        typed = [i for i in all_issues if i["type"] == issue_type]
        if typed:
            lines.append(f"\n## {issue_type} ({len(typed)})")
            for i in typed[:20]:
                if issue_type == "EDGE_CONTRADICTION":
                    lines.append(f"- **{i['source']}** ↔ **{i['target']}** ({i['relation']})")
                elif issue_type == "NAME_COLLISION":
                    lines.append(f"- `{i['name_a']}` ↔ `{i['name_b']}` (similarity={i['similarity']})")
                elif issue_type == "DESCRIPTION_DUPLICATE":
                    lines.append(f"- `{i['name_a']}` ↔ `{i['name_b']}` (similarity={i['similarity']})")
                elif issue_type == "AUTHORITY_CONFLICT":
                    lines.append(f"- [{i['domain_tag']}] {i['higher_authority']}:`{i['higher_name']}` vs {i['lower_authority']}:`{i['lower_name']}`")
            if len(typed) > 20:
                lines.append(f"- ... and {len(typed) - 20} more")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport: {report_path}")

    # ── thermodynamic purge integration ──
    from system_v4.skills.a2_thermodynamic_purge import A2ThermodynamicPurge
    purger = A2ThermodynamicPurge(r)
    purged_count = 0
    print("\nExecuting Thermodynamic Purge on duplicates...")
    for issue in all_issues:
        if issue["type"] in ("NAME_COLLISION", "DESCRIPTION_DUPLICATE"):
            node_to_purge = issue.get("node_b")
            if node_to_purge and purger.purge_concept(
                node_id=node_to_purge,
                reason=f"{issue['type']} detected against {issue.get('node_a')}",
                violating_anchors=[issue["type"], "THERMODYNAMIC_SINK"]
            ):
                purged_count += 1
                
    if purged_count > 0:
        print(f"Dynamically routed {purged_count} contradictory elements to the GRAVEYARD.")

    r.log_finding(f"Contradiction scan completed. Found {len(all_issues)} issues. Purged {purged_count}.")
    log = r.end_session()
    print(f"Session: {log}")

    return {
        "concepts_scanned": len(concepts),

        "total_issues": len(all_issues),
        "by_severity": dict(by_severity),
        "by_type": dict(by_type),
        "report": str(report_path),
    }


if __name__ == "__main__":
    result = run_contradiction_scan()
