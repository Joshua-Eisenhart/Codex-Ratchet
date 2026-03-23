"""
Graph Cross-Linker — Create structural edges between related concepts.

The refinery ingestion only creates source_doc → concept star edges.
This skill adds cross-concept edges to form real clusters:

  1. TAG_SHARED: concepts sharing ≥2 tags → RELATED_TO
  2. TERM_REFERENCE: concept name appears in another concept's description → DEPENDS_ON
  3. SOURCE_SIBLINGS: concepts from the same source doc → CO_SOURCED (weak)
  4. NAME_COMPONENT: concept names sharing structural components → STRUCTURALLY_RELATED

This is deterministic — no LLM needed. Pure graph computation.

Run:
  cd ~/Desktop/Codex\ Ratchet
  python3 -m system_v4.skills.run_graph_crosslinker
"""

import sys
import time
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.v4_graph_builder import GraphEdge
from system_v4.skills.a2_graph_refinery import A2GraphRefinery


def run_crosslink(max_tag_edges: int = 5000, max_term_edges: int = 3000):
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("SESSION_CROSSLINK_" + time.strftime("%Y%m%d_%H%M%S"))
    g = refinery.builder.pydantic_model

    print(f"Graph before: {len(g.nodes)} nodes, {len(g.edges)} edges")

    # Collect concept nodes (skip SOURCE_DOCUMENT, THREAD_SEAL, etc.)
    concept_types = {"EXTRACTED_CONCEPT", "REFINED_CONCEPT", "KERNEL_CONCEPT", "CONCEPT"}
    concepts = {
        nid: n for nid, n in g.nodes.items()
        if n.node_type in concept_types
    }
    print(f"Concept nodes: {len(concepts)}")

    # Track existing edge pairs to avoid duplicates
    existing_pairs = set()
    for e in g.edges:
        existing_pairs.add((e.source_id, e.target_id))
        existing_pairs.add((e.target_id, e.source_id))

    edges_added = 0

    # ── 1. TAG_SHARED: concepts sharing ≥2 tags → RELATED_TO ──
    print("\n--- Pass 1: Tag-based clustering ---")
    tag_to_concepts = defaultdict(list)
    for nid, n in concepts.items():
        tags = n.tags or []
        if isinstance(tags, list):
            for tag in tags:
                if tag and len(tag) > 2:  # skip trivial tags
                    tag_to_concepts[tag].append(nid)

    # Build co-occurrence matrix via shared tags
    pair_tag_count = defaultdict(int)
    for tag, nids in tag_to_concepts.items():
        if len(nids) > 100:
            continue  # skip overly common tags (noise)
        for i in range(len(nids)):
            for j in range(i + 1, len(nids)):
                a, b = min(nids[i], nids[j]), max(nids[i], nids[j])
                pair_tag_count[(a, b)] += 1

    # Create edges for pairs sharing ≥2 tags
    tag_edges = 0
    for (a, b), count in sorted(pair_tag_count.items(), key=lambda x: -x[1]):
        if count < 2:
            continue
        if (a, b) in existing_pairs:
            continue
        if tag_edges >= max_tag_edges:
            break

        shared_tags = []
        tags_a = set(concepts[a].tags or [])
        tags_b = set(concepts[b].tags or [])
        shared_tags = sorted(tags_a & tags_b)

        edge = GraphEdge(
            source_id=a,
            target_id=b,
            relation="RELATED_TO",
            relation_id=f"XLINK::TAG::{a}--{b}",
            trust_zone=concepts[a].trust_zone,
            attributes={
                "link_type": "TAG_SHARED",
                "shared_tags": shared_tags[:5],
                "shared_count": count,
            },
        )
        refinery.builder.add_edge(edge)
        existing_pairs.add((a, b))
        tag_edges += 1
        edges_added += 1

    print(f"  Tag-shared edges added: {tag_edges}")

    # ── 2. TERM_REFERENCE: concept name in another's description → DEPENDS_ON ──
    print("\n--- Pass 2: Term reference linking ---")
    # Build name → id lookup (normalized)
    name_to_id = {}
    for nid, n in concepts.items():
        norm = n.name.lower().replace("-", "_").replace(" ", "_")
        if len(norm) > 4:  # skip very short names
            name_to_id[norm] = nid

    term_edges = 0
    for nid, n in concepts.items():
        desc = (n.description or "").lower().replace("-", "_").replace(" ", "_")
        if not desc:
            continue
        for name, target_id in name_to_id.items():
            if target_id == nid:
                continue
            if name in desc and (nid, target_id) not in existing_pairs:
                if term_edges >= max_term_edges:
                    break
                edge = GraphEdge(
                    source_id=nid,
                    target_id=target_id,
                    relation="DEPENDS_ON",
                    relation_id=f"XLINK::TERM::{nid}--{target_id}",
                    trust_zone=n.trust_zone,
                    attributes={"link_type": "TERM_REFERENCE", "referenced_term": name},
                )
                refinery.builder.add_edge(edge)
                existing_pairs.add((nid, target_id))
                term_edges += 1
                edges_added += 1

    print(f"  Term-reference edges added: {term_edges}")

    # ── 3. NAME_COMPONENT: shared structural name components ──
    print("\n--- Pass 3: Name component clustering ---")
    component_to_concepts = defaultdict(list)
    for nid, n in concepts.items():
        parts = n.name.lower().replace("-", "_").split("_")
        # Use meaningful components (skip common prefixes like 'a0', 'a1', etc.)
        skip_parts = {"a0", "a1", "a2", "b", "sim", "v1", "v2", "v3", "v4", "the", "and", "of", "in", "to", "for", "is", "test"}
        for part in parts:
            if len(part) > 3 and part not in skip_parts:
                component_to_concepts[part].append(nid)

    component_pairs = defaultdict(int)
    for component, nids in component_to_concepts.items():
        if len(nids) > 50 or len(nids) < 2:
            continue
        for i in range(len(nids)):
            for j in range(i + 1, len(nids)):
                a, b = min(nids[i], nids[j]), max(nids[i], nids[j])
                component_pairs[(a, b)] += 1

    name_edges = 0
    for (a, b), count in sorted(component_pairs.items(), key=lambda x: -x[1]):
        if count < 2:
            continue
        if (a, b) in existing_pairs:
            continue
        if name_edges >= 2000:
            break

        edge = GraphEdge(
            source_id=a,
            target_id=b,
            relation="STRUCTURALLY_RELATED",
            relation_id=f"XLINK::NAME::{a}--{b}",
            trust_zone=concepts[a].trust_zone,
            attributes={"link_type": "NAME_COMPONENT", "shared_components": count},
        )
        refinery.builder.add_edge(edge)
        existing_pairs.add((a, b))
        name_edges += 1
        edges_added += 1

    print(f"  Name-component edges added: {name_edges}")

    # ── 4. ANTI-EDGES: concepts with shared name parts but ZERO shared tags ──
    # These look similar on the surface but are structurally unrelated.
    # Anti-edges prevent false clustering — they are the graph equivalent of
    # negative SIM evidence. "These things are NOT the same."
    print("\n--- Pass 4: Anti-edges (structural exclusion) ---")
    anti_edges = 0
    max_anti_edges = 1500
    for (a, b), comp_count in sorted(component_pairs.items(), key=lambda x: -x[1]):
        if comp_count < 2:
            continue
        if (a, b) in existing_pairs:
            continue
        if anti_edges >= max_anti_edges:
            break

        # Check if tags are DISJOINT — shared name parts but zero shared tags
        tags_a = set(concepts[a].tags or [])
        tags_b = set(concepts[b].tags or [])
        if not tags_a or not tags_b:
            continue
        shared = tags_a & tags_b
        if len(shared) == 0:
            # Anti-edge: looks similar, structurally different
            edge = GraphEdge(
                source_id=a,
                target_id=b,
                relation="EXCLUDES",
                relation_id=f"XLINK::ANTI::{a}--{b}",
                trust_zone=concepts[a].trust_zone,
                attributes={
                    "link_type": "ANTI_EDGE",
                    "reason": "shared_name_components_disjoint_tags",
                    "shared_name_parts": comp_count,
                    "tags_a_sample": sorted(tags_a)[:3],
                    "tags_b_sample": sorted(tags_b)[:3],
                },
            )
            refinery.builder.add_edge(edge)
            existing_pairs.add((a, b))
            anti_edges += 1
            edges_added += 1

    print(f"  Anti-edges (EXCLUDES) added: {anti_edges}")

    # ── Summary ──
    print(f"\n=== TOTAL CROSS-LINKS ADDED: {edges_added} ===")
    refinery.checkpoint()

    # Re-analyze connectivity
    from collections import Counter
    degree = defaultdict(int)
    for e in refinery.builder.pydantic_model.edges:
        degree[e.source_id] += 1
        degree[e.target_id] += 1

    degrees = sorted(degree.values(), reverse=True)
    connected = len(degree)
    leaves = sum(1 for d in degrees if d == 1)
    medium = sum(1 for d in degrees if 2 <= d <= 5)
    hubs = sum(1 for d in degrees if d >= 6)

    print(f"\n=== POST-CROSSLINK CONNECTIVITY ===")
    print(f"  Nodes: {len(refinery.builder.pydantic_model.nodes)}")
    print(f"  Edges: {len(refinery.builder.pydantic_model.edges)}")
    print(f"  Edge:Node ratio: {len(refinery.builder.pydantic_model.edges)/len(refinery.builder.pydantic_model.nodes):.2f}")
    print(f"  Connected: {connected}")
    print(f"  Degree 1 (leaf): {leaves} ({100*leaves/connected:.1f}%)")
    print(f"  Degree 2-5: {medium} ({100*medium/connected:.1f}%)")
    print(f"  Degree 6+ (hub): {hubs} ({100*hubs/connected:.1f}%)")
    print(f"  Top 10 degrees: {degrees[:10]}")

    # Edge type breakdown
    edge_types = Counter(e.relation for e in refinery.builder.pydantic_model.edges)
    print(f"\n=== EDGE TYPE BREAKDOWN ===")
    for t, c in edge_types.most_common():
        print(f"  {t}: {c}")

    log_path = refinery.end_session()
    print(f"\nSession log: {log_path}")


if __name__ == "__main__":
    run_crosslink()
