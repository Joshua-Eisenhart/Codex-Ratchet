"""
run_proto_loop.py — V4 Proto Loop Runner

Orchestrates the full ratchet pipeline:
  A2_1_KERNEL → A1_JARGONED → A1_STRIPPED → A1_CARTRIDGE
             → A0_COMPILED → B_ADJUDICATED → SIM_EVIDENCED

For the proto, A1 stripping and cartridge assembly use deterministic
extraction from the concept's existing description/tags (no LLM needed).
The full pipeline runs end-to-end with a single save at the end.

Usage:
  python3 -m system_v4.skills.run_proto_loop --top 5
  python3 -m system_v4.skills.run_proto_loop --node <id>
  python3 -m system_v4.skills.run_proto_loop --dry-run --top 3
"""

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ── Proto A1 Extraction (deterministic, no LLM) ─────────────────────

def proto_strip_concept(name: str, description: str, tags: list[str]) -> dict:
    """
    Deterministic A1 stripping: extract structural content from the concept's
    existing description and tags without an LLM.
    """
    # Strip jargon words (common narrative filler)
    JARGON = {
        "basically", "essentially", "framework", "paradigm", "holistic",
        "synergy", "leverage", "ecosystem", "robust", "comprehensive",
        "novel", "innovative", "state-of-the-art", "cutting-edge",
    }
    words = description.lower().split()
    dropped = [w for w in words if w.strip(".,;:()") in JARGON]

    # Create stripped name
    stripped_name = re.sub(r'[^A-Z0-9_]', '_', name.upper())
    stripped_name = re.sub(r'_+', '_', stripped_name).strip('_')

    # Extract structural anchors from description
    anchors = []
    for pattern in [r"depends on (\w+)", r"requires (\w+)", r"uses (\w+)",
                    r"extends (\w+)", r"implements (\w+)"]:
        found = re.findall(pattern, description.lower())
        anchors.extend(found)

    return {
        "stripped_name": stripped_name,
        "stripped_description": description[:200].strip(),
        "dropped_jargon": dropped[:10],
        "required_anchors": anchors[:5] if anchors else ["UNVERIFIED"],
    }


def proto_assemble_cartridge(name: str, description: str, tags: list[str]) -> dict:
    """
    Deterministic cartridge assembly: create adversarial envelope
    from the concept's structural content.
    """
    return {
        "candidate_shape": "TERM_DEF" if "DEFINITION" in (tags or []) else "SIM_SPEC",
        "steelman_positive": f"{name} is structurally necessary because: {description[:120]}",
        "adversarial_negative": f"If {name} is removed, the following breaks: "
                               f"{'dependency chain on ' + ', '.join(tags[:3]) if tags else 'none identified'}",
        "success_condition": f"SIM produces stable output when {name} is present",
        "fail_condition": f"SIM diverges or produces contradictory output without {name}",
    }


# ── Pipeline Runner ──────────────────────────────────────────────────

class ProtoLoopRunner:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

    def select_candidates(self, top_n: int = 5, node_id: Optional[str] = None) -> list[dict]:
        """Select kernel concepts to process, ranked by edge density."""
        from system_v4.skills.a2_graph_refinery import A2GraphRefinery

        r = A2GraphRefinery(self.workspace_root)
        nodes = r.builder.pydantic_model.nodes
        edges = r.builder.pydantic_model.edges

        # Build adjacency count
        adj_count = Counter()
        for e in edges:
            adj_count[e.source_id] += 1
            adj_count[e.target_id] += 1

        if node_id:
            # Specific node
            if node_id not in nodes:
                print(f"Error: Node {node_id} not found")
                return []
            n = nodes[node_id]
            return [{"id": node_id, "name": n.name, "description": n.description,
                     "tags": n.tags or [], "edges": adj_count.get(node_id, 0)}]

        # Select from A2_1_KERNEL, ranked by edge count
        candidates = []
        for nid, n in nodes.items():
            if n.trust_zone != "A2_1_KERNEL":
                continue
            if n.node_type != "KERNEL_CONCEPT":
                continue
            # Skip if already processed through the pipeline
            jargoned_id = f"A1_STRIPPED::{re.sub(r'[^A-Z0-9_]', '_', n.name.upper())}"
            if jargoned_id in nodes:
                continue
            candidates.append({
                "id": nid,
                "name": n.name,
                "description": n.description or "",
                "tags": n.tags or [],
                "edges": adj_count.get(nid, 0),
            })

        candidates.sort(key=lambda c: c["edges"], reverse=True)
        return candidates[:top_n]

    def run(self, top_n: int = 5, node_id: Optional[str] = None, dry_run: bool = False):
        """Run the full proto loop pipeline."""
        from system_v4.skills.a2_graph_refinery import A2GraphRefinery
        from system_v4.skills.a1_rosetta_stripper import A1RosettaStripper
        from system_v4.skills.a1_cartridge_assembler import A1CartridgeAssembler
        from system_v4.skills.a0_compiler import A0Compiler
        from system_v4.skills.b_adjudicator import BAdjudicator
        from system_v4.skills.sim_holodeck_engine import SIMHolodeckEngine

        candidates = self.select_candidates(top_n, node_id)
        if not candidates:
            print("No candidates found.")
            return

        print(f"{'='*60}")
        print(f"V4 PROTO LOOP RUNNER")
        print(f"{'='*60}")
        print(f"Candidates: {len(candidates)}")
        if dry_run:
            print(f"MODE: DRY RUN (no graph mutations)\n")
            for i, c in enumerate(candidates, 1):
                print(f"  [{i}] {c['name'][:50]:50s} edges={c['edges']}")
            return

        # Initialize pipeline
        r = A2GraphRefinery(self.workspace_root)
        sid = r.start_session(f"PROTO_LOOP_{time.strftime('%Y%m%d_%H%M%S')}")

        stripper = A1RosettaStripper(r)
        assembler = A1CartridgeAssembler(r)
        compiler = A0Compiler(r)
        adjudicator = BAdjudicator(r)
        holodeck = SIMHolodeckEngine(r)

        # Track results
        results = {
            "stripped": 0, "cartridged": 0, "compiled": 0,
            "accepted": 0, "parked": 0, "rejected": 0,
            "simulated": 0, "errors": 0,
        }
        details = []

        for i, c in enumerate(candidates, 1):
            print(f"\n{'─'*60}")
            print(f"[{i}/{len(candidates)}] {c['name']}")
            print(f"{'─'*60}")
            result = {"name": c["name"], "stages": []}

            try:
                # Stage 1: A1 Rosetta Strip
                print(f"  → A1 Rosetta Strip...")
                strip_data = proto_strip_concept(c["name"], c["description"], c["tags"])
                stripped_id = stripper.strip_concept(
                    node_id=c["id"],
                    stripped_name=strip_data["stripped_name"],
                    stripped_desc=strip_data["stripped_description"],
                    dropped_jargon=strip_data["dropped_jargon"],
                    required_anchors=strip_data["required_anchors"],
                )
                if not stripped_id:
                    result["stages"].append(("A1_STRIP", "FAILED"))
                    results["errors"] += 1
                    details.append(result)
                    continue
                result["stages"].append(("A1_STRIP", stripped_id))
                results["stripped"] += 1
                print(f"    ✓ {stripped_id}")

                # Stage 2: A1 Cartridge Assembly
                print(f"  → A1 Cartridge Assembly...")
                cart_data = proto_assemble_cartridge(c["name"], c["description"], c["tags"])
                cartridge_id = assembler.assemble_cartridge(
                    node_id=stripped_id,
                    **cart_data,
                )
                if not cartridge_id:
                    result["stages"].append(("A1_CARTRIDGE", "FAILED"))
                    results["errors"] += 1
                    details.append(result)
                    continue
                result["stages"].append(("A1_CARTRIDGE", cartridge_id))
                results["cartridged"] += 1
                print(f"    ✓ {cartridge_id}")

                # Stage 3: A0 Compile
                print(f"  → A0 Compile...")
                compiled_id = compiler.compile_cartridge(cartridge_id)
                if not compiled_id:
                    result["stages"].append(("A0_COMPILE", "FAILED"))
                    results["errors"] += 1
                    details.append(result)
                    continue
                result["stages"].append(("A0_COMPILE", compiled_id))
                results["compiled"] += 1
                print(f"    ✓ {compiled_id}")

                # Stage 4: B Adjudication
                print(f"  → B Adjudication...")
                adjudicated_id = adjudicator.adjudicate_block(compiled_id)
                if not adjudicated_id:
                    result["stages"].append(("B_ADJUDICATE", "FAILED"))
                    results["errors"] += 1
                    details.append(result)
                    continue
                # Check verdict
                adj_node = r.builder.get_node(adjudicated_id)
                verdict = adj_node.properties.get("b_verdict", "UNKNOWN") if adj_node else "UNKNOWN"
                result["stages"].append(("B_ADJUDICATE", f"{adjudicated_id} [{verdict}]"))
                if verdict == "ACCEPT":
                    results["accepted"] += 1
                elif verdict == "PARK":
                    results["parked"] += 1
                else:
                    results["rejected"] += 1
                print(f"    ✓ {adjudicated_id} → {verdict}")

                # Stage 5: SIM Holodeck (only for ACCEPT)
                if verdict == "ACCEPT":
                    print(f"  → SIM Holodeck Terminal...")
                    sim_id = holodeck.run_simulation(adjudicated_id)
                    if sim_id:
                        result["stages"].append(("SIM_HOLODECK", sim_id))
                        results["simulated"] += 1
                        print(f"    ✓ {sim_id}")
                    else:
                        result["stages"].append(("SIM_HOLODECK", "FAILED"))
                        results["errors"] += 1
                else:
                    print(f"    ⊘ SIM skipped (verdict={verdict})")

            except Exception as e:
                print(f"    ✗ ERROR: {e}")
                result["stages"].append(("ERROR", str(e)))
                results["errors"] += 1

            details.append(result)

        # Final save (batch)
        print(f"\n{'='*60}")
        print("Saving graph...")
        r._save()
        log = r.end_session()

        # Report
        print(f"\n{'='*60}")
        print(f"PROTO LOOP COMPLETE")
        print(f"{'='*60}")
        print(f"  A1 Stripped:    {results['stripped']}")
        print(f"  A1 Cartridged:  {results['cartridged']}")
        print(f"  A0 Compiled:    {results['compiled']}")
        print(f"  B Accepted:     {results['accepted']}")
        print(f"  B Parked:       {results['parked']}")
        print(f"  B Rejected:     {results['rejected']}")
        print(f"  SIM Evidenced:  {results['simulated']}")
        print(f"  Errors:         {results['errors']}")
        print(f"\n  Graph: {len(r.builder.pydantic_model.nodes)} nodes, "
              f"{len(r.builder.pydantic_model.edges)} edges")
        if log:
            print(f"  Session log: {log}")


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V4 Proto Loop Runner — full A2→A1→A0→B→SIM pipeline"
    )
    parser.add_argument(
        "--top", type=int, default=5,
        help="Process top N kernel concepts (default: 5)"
    )
    parser.add_argument(
        "--node", type=str, default=None,
        help="Process a specific node ID"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show candidates without processing"
    )

    args = parser.parse_args()
    runner = ProtoLoopRunner(str(REPO_ROOT))
    runner.run(top_n=args.top, node_id=args.node, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
