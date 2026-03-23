"""
a2_boot.py — A2 Refinery Boot Sequence

Run this at the start of any new A2 thread to:
  1. Load the full graph state and display layer/authority summary
  2. Read the latest thread context extract for continuity
  3. Show pending work from the doc queue
  4. Start a new session and seal the boot
  5. Print a REBOOT KEY that the new thread should read first

Usage:
    python3 -c "import sys; sys.path.insert(0, '.'); exec(open('system_v4/skills/a2_boot.py').read())"

    Or from a new LLM thread:
    >>> exec(open('system_v4/skills/a2_boot.py').read())
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2] if "__file__" in dir() else Path(".")
sys.path.insert(0, str(WORKSPACE))

from system_v4.skills.a2_graph_refinery import (
    A2GraphRefinery,
    RefineryLayer,
    LAYER_ADMISSIBILITY,
    AUTHORITY_LEVELS,
    LAYER_MIGRATION,
    LEGACY_AUTHORITY,
)


def a2_boot(workspace: Path = WORKSPACE, session_name: str = "") -> dict:
    """
    Boot the A2 refinery and print full state summary.
    Returns a dict with all state info for the calling thread.
    """
    r = A2GraphRefinery(str(workspace))

    # ── 1. Graph State ───────────────────────────────────────────────
    print("=" * 70)
    print("  A2 GRAPH REFINERY — BOOT SEQUENCE")
    print("=" * 70)
    print()

    total_nodes = r.builder.graph.number_of_nodes()
    total_edges = r.builder.graph.number_of_edges()
    print(f"Graph: {total_nodes} nodes, {total_edges} edges")
    print()

    # Layer distribution
    layer_counts: dict[str, int] = Counter()
    authority_counts: dict[str, int] = Counter()
    type_counts: dict[str, int] = Counter()
    for nid, node in r.builder.graph.nodes(data=True):
        # trust_zone may be stored as flat attr or missing; fall back to layer then ID prefix
        tz = node.get("trust_zone", node.get("layer", ""))
        if not tz or tz == "A2":
            # Infer from node ID prefix
            if nid.startswith("A2_3::") or nid.startswith("A2_3_"):
                tz = "A2_3_INTAKE"
            elif nid.startswith("A2_2::"):
                tz = "A2_2_CANDIDATE"
            elif nid.startswith("A2_1::"):
                tz = "A2_1_KERNEL"
            elif nid.startswith("INDEX::"):
                tz = "INDEX"
            else:
                tz = "A2_3_INTAKE"  # default for mass-ingested
        layer_counts[tz] += 1
        
        auth = node.get("authority", "")
        if auth:
            authority_counts[auth] += 1
        
        ntype = node.get("type", node.get("node_type", "?"))
        type_counts[ntype] += 1

    print("── Layer Distribution ──")
    # Show new layers first, then legacy
    new_layers = ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL",
                  "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE",
                  "A0_COMPILED", "B_ADJUDICATED", "SIM_EVIDENCED", "GRAVEYARD"]
    legacy_layers = ["A2_3_INTAKE", "A2_2_CANDIDATE", "A2_1_KERNEL"]

    for layer in new_layers:
        count = layer_counts.get(layer, 0)
        if count:
            print(f"  {layer:25s} {count:6d}")
    for layer in legacy_layers:
        count = layer_counts.get(layer, 0)
        if count:
            print(f"  (legacy) {layer:18s} {count:6d}")

    # Show any unknown layers
    known = set(new_layers + legacy_layers)
    for layer, count in sorted(layer_counts.items()):
        if layer not in known and count > 0:
            print(f"  (?) {layer:23s} {count:6d}")

    print()
    print("── Authority Distribution ──")
    for auth, count in authority_counts.most_common():
        print(f"  {auth:20s} {count:6d}")

    print()
    print("── Node Types ──")
    for ntype, count in type_counts.most_common():
        print(f"  {ntype:25s} {count:6d}")

    # ── 2. Latest Thread Context ─────────────────────────────────────
    print()
    print("── Latest Thread Context Extracts ──")
    a2_state = workspace / "system_v4" / "a2_state"
    extracts = sorted(a2_state.glob("THREAD_CONTEXT_EXTRACT__*.md"), reverse=True)
    for extract in extracts[:5]:
        # Read first 3 lines for summary
        lines = extract.read_text(encoding="utf-8").splitlines()[:3]
        print(f"  {extract.name}")
        for line in lines:
            if line.strip():
                print(f"    {line.strip()[:80]}")
    if not extracts:
        print("  (none found)")

    # ── 3. Doc Queue Status ──────────────────────────────────────────
    print()
    print("── Doc Queue Status ──")
    qs = r.get_queue_status()
    print(f"  Total: {qs['total']}, Done: {qs['done']}, Skip: {qs['skip']}, Pending: {qs['pending']}")
    if qs.get("by_class"):
        for ec, counts in sorted(qs["by_class"].items()):
            print(f"    {ec}: {counts}")

    # ── 4. Batch Summary ─────────────────────────────────────────────
    print()
    print("── Batch Summary ──")
    bs = r.get_batch_summary()
    total_batches = sum(bs.values())
    print(f"  Total batches: {total_batches}")
    for layer, count in sorted(bs.items()):
        print(f"    {layer}: {count}")

    # ── 5. Recent Session Logs ───────────────────────────────────────
    print()
    print("── Recent Sessions ──")
    session_dir = a2_state / "session_logs"
    if session_dir.exists():
        logs = sorted(session_dir.glob("SESSION_*.md"), reverse=True)
        for log in logs[:5]:
            print(f"  {log.name}")
    else:
        print("  (no session logs)")

    # ── 6. Architecture Summary ──────────────────────────────────────
    print()
    print("── V4.1 Architecture ──")
    print("  Layers: INDEX → A2_HIGH/MID/LOW → A1_JARGONED/STRIPPED/CARTRIDGE")
    print("          → A0 → B → SIM → GRAVEYARD")
    print("  Authority: SOURCE_CLAIM → CROSS_VALIDATED → STRIPPED → RATCHETED")
    print("  Rule: Nothing is canon until ratcheted through B + SIM + graveyard")
    print("  Principle: Every layer manages entropy bidirectionally")
    print()

    # ── 7. Start Session & Seal Persistent Brain ─────────────────────
    if not session_name:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        session_name = f"A2_BOOT_{ts}"

    sid = r.start_session(session_name)
    r.log_finding(f"A2 boot completed: {total_nodes} nodes, {total_edges} edges")
    print(f"Session started: {session_name}")
    
    # Instantiate and seal boot state per JOB_003 Audit
    try:
        from system_v4.skills.a2_persistent_brain import A2PersistentBrain
        pb = A2PersistentBrain(str(workspace))
        boot_report = pb.generate_boot_state_report()
        state_hash = pb._sha256_dict(boot_report)
        pb.seal_context(
            source_thread_id=session_name,
            pending_actions=["CONTINUE_REFINEMENT"],
            next_read_set=[],
            state_digest_hash=state_hash
        )
        print(f"Persistent Brain: Boot State Sealed ({state_hash[:8]})")
    except Exception as e:
        print(f"Persistent Brain: Failed to seal ({e})")
        
    print("=" * 70)
    print()

    # ── REBOOT KEY ───────────────────────────────────────────────────
    print("REBOOT KEY (read this first):")
    print("─" * 50)
    print(f"  Graph: {total_nodes} nodes, {total_edges} edges")
    print(f"  Architecture: V4.1, 12-layer model")
    print(f"  Authority: entropy-gradient (SOURCE_CLAIM → RATCHETED)")
    print(f"  Pending docs: {qs['pending']}")
    print(f"  Recent extracts: {extracts[0].name if extracts else 'none'}")
    print(f"  Session: {session_name}")
    print("─" * 50)

    return {
        "refinery": r,
        "session_name": session_name,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "layer_counts": dict(layer_counts),
        "authority_counts": dict(authority_counts),
        "type_counts": dict(type_counts),
        "queue_status": qs,
        "batch_summary": bs,
        "latest_extract": str(extracts[0]) if extracts else None,
    }


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    result = a2_boot(session_name=name)
