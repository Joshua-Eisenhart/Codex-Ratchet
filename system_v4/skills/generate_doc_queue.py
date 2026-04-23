"""
Generate the initial doc_queue.json for the A2 Graph Refinery.

Corrected entropy ordering — ALIGNED with refinery ENTROPY_CLASS_ORDER:
   0: SPEC_CORE        — manifest core specs
   1: SPEC_SUPPLEMENT   — manifest supplements + process specs
   2: CONTROL_PLANE     — control plane bundle specs
   3: A2_STATE_FORMAL   — a2_state surfaces (V3 distillation)
   4: A1_STATE          — a1 campaigns, packs, families
   5: REFINED_FUEL      — a1_refined_Ratchet Fuel
   6: CORE_DOCS_RAW     — bootpack, remaining core_docs
   7: RUN_ANCHOR        — run anchors and regen witnesses
   8: UPGRADE_DOCS      — v4 upgrades, upgrade docs, archived A2 state
   9: HIGH_ENTROPY      — chat logs, .txt files (last)
  10: SYSTEM_V4         — v4 boot/process docs

NOTE: work/audit_tmp, zip_dropins, zip_subagents, INBOX, and skill_drafts
      are intentionally EXCLUDED — those are controller scratch, not V3 fuel.

.md files first, .txt files last.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def main():
    from system_v4.skills.a2_graph_refinery import A2GraphRefinery

    refinery = A2GraphRefinery(str(REPO_ROOT))

    # ── Already-processed paths ──────────────────────────────────────
    # Distinguish DONE (has concepts) from SOURCE_REGISTERED (source-only)
    processed_paths = set()
    source_registered_paths = set()
    # Build set of source document node IDs for filtering
    source_doc_ids = set()
    for nid, n in refinery.builder.pydantic_model.nodes.items():
        if n.node_type == "SOURCE_DOCUMENT":
            source_doc_ids.add(nid)

    for batch in refinery.batches:
        # A batch has real concepts only if it has non-source node IDs
        concept_ids = [nid for nid in batch.node_ids if nid not in source_doc_ids]
        has_concepts = len(concept_ids) > 0
        for sp in batch.source_paths:
            rp = str(Path(sp).resolve())
            if has_concepts:
                processed_paths.add(rp)
            else:
                source_registered_paths.add(rp)

    queue = []
    seen_paths = set()

    def add(path_str, entropy_class):
        p = Path(path_str)
        if not p.is_absolute():
            p = REPO_ROOT / p
        p = p.resolve()
        if not p.exists():
            return
        key = str(p)
        if key in seen_paths:
            return
        seen_paths.add(key)
        if key in processed_paths:
            status = "DONE"
        elif key in source_registered_paths:
            status = "SOURCE_REGISTERED"
        else:
            status = "PENDING"
        queue.append({
            "path": key,
            "entropy_class": entropy_class,
            "status": status,
            "processed_batch_id": None,
        })


    # ═══════════════════════════════════════════════════════════════════
    # TIER 0: SPEC_CORE — Manifest deterministic read order
    # ═══════════════════════════════════════════════════════════════════
    MANIFEST_ORDER = [
        "system_v3/specs/01_REQUIREMENTS_LEDGER.md",
        "system_v3/specs/02_OWNERSHIP_MAP.md",
        "system_v3/specs/03_B_KERNEL_SPEC.md",
        "system_v3/specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md",
        "system_v3/specs/04_A0_COMPILER_SPEC.md",
        "system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md",
        "system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md",
        "system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md",
        "system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md",
        "system_v3/specs/07_A2_OPERATIONS_SPEC.md",
        "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md",
        "system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md",
        "system_v3/specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md",
        "system_v3/specs/20_CONTROLLED_TUNING_AND_UPGRADE_CONTRACT.md",
        "system_v3/specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md",
    ]
    for p in MANIFEST_ORDER:
        add(p, "SPEC_CORE")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 1: SPEC_SUPPLEMENT
    # ═══════════════════════════════════════════════════════════════════
    specs_dir = REPO_ROOT / "system_v3" / "specs"
    if specs_dir.exists():
        for f in sorted(specs_dir.glob("*.md")):
            add(str(f), "SPEC_SUPPLEMENT")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 2: CONTROL_PLANE
    # ═══════════════════════════════════════════════════════════════════
    cp_base = REPO_ROOT / "system_v3" / "control_plane_bundle_work" / "system_v3_control_plane"
    for sub in ["specs", "flowmind_integration", "validator_contract"]:
        d = cp_base / sub
        if d.exists():
            for f in sorted(d.glob("*.md")):
                add(str(f), "CONTROL_PLANE")
    if cp_base.exists():
        for f in sorted(cp_base.glob("*.md")):
            add(str(f), "CONTROL_PLANE")

    pub = REPO_ROOT / "system_v3" / "public_facing_docs"
    if pub.exists():
        for f in sorted(pub.glob("*.md")):
            add(str(f), "CONTROL_PLANE")

    conf = REPO_ROOT / "system_v3" / "conformance"
    if conf.exists():
        for f in sorted(conf.glob("*.md")):
            add(str(f), "CONTROL_PLANE")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 3: A2_STATE_FORMAL (aligned with refinery vocabulary)
    # ═══════════════════════════════════════════════════════════════════
    a2_state = REPO_ROOT / "system_v3" / "a2_state"
    if a2_state.exists():
        for f in sorted(a2_state.glob("*.md")):
            add(str(f), "A2_STATE_FORMAL")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 4: A1_STATE
    # ═══════════════════════════════════════════════════════════════════
    a1_state = REPO_ROOT / "system_v3" / "a1_state"
    if a1_state.exists():
        for f in sorted(a1_state.glob("*.md")):
            add(str(f), "A1_STATE")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 5: REFINED_FUEL
    # ═══════════════════════════════════════════════════════════════════
    refined = REPO_ROOT / "core_docs" / "a1_refined_Ratchet Fuel"
    if refined.exists():
        for f in sorted(refined.glob("*.md")):
            add(str(f), "REFINED_FUEL")
        cl = refined / "constraint ladder"
        if cl.exists():
            for f in sorted(cl.glob("*.md")):
                add(str(f), "REFINED_FUEL")
        ts = refined / "THREAD_S_FULL_SAVE"
        if ts.exists():
            for f in sorted(ts.glob("*.md")):
                add(str(f), "REFINED_FUEL")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 6: CORE_DOCS_RAW
    # ═══════════════════════════════════════════════════════════════════
    core = REPO_ROOT / "core_docs"
    if core.exists():
        for f in sorted(core.glob("*.md")):
            add(str(f), "CORE_DOCS_RAW")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 7: RUN_ANCHOR
    # ═══════════════════════════════════════════════════════════════════
    run_anchor = REPO_ROOT / "system_v3" / "run_anchor_surface"
    if run_anchor.exists():
        for f in sorted(run_anchor.glob("*.md")):
            add(str(f), "RUN_ANCHOR")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 8: UPGRADE_DOCS
    # ═══════════════════════════════════════════════════════════════════
    for subdir in ["v4 upgrades", "upgrade docs"]:
        d = REPO_ROOT / "core_docs" / subdir
        if d.exists():
            for f in sorted(d.glob("*.md")):
                add(str(f), "UPGRADE_DOCS")

    archived = REPO_ROOT / "core_docs" / "a2_runtime_state archived old state"
    if archived.exists():
        for f in sorted(archived.glob("*.md")):
            add(str(f), "UPGRADE_DOCS")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 9: HIGH_ENTROPY
    # ═══════════════════════════════════════════════════════════════════
    high_entropy = REPO_ROOT / "core_docs" / "a2_feed_high entropy doc"
    if high_entropy.exists():
        for f in sorted(high_entropy.glob("*.txt")):
            add(str(f), "HIGH_ENTROPY")
        for f in sorted(high_entropy.glob("*.md")):
            add(str(f), "HIGH_ENTROPY")

    ultra_high_entropy = REPO_ROOT / "core_docs" / "ultra high entropy docs"
    if ultra_high_entropy.exists():
        for f in sorted(ultra_high_entropy.glob("*.*")):
            add(str(f), "HIGH_ENTROPY")

    a2_high = REPO_ROOT / "system_v3" / "a2_high_entropy_intake_surface"
    if a2_high.exists():
        for f in sorted(a2_high.glob("*.*")):
            add(str(f), "HIGH_ENTROPY")

    for subdir in ["v4 upgrades", "upgrade docs"]:
        d = REPO_ROOT / "core_docs" / subdir
        if d.exists():
            for f in sorted(d.glob("*.txt")):
                add(str(f), "HIGH_ENTROPY")

    # ═══════════════════════════════════════════════════════════════════
    # TIER 10: SYSTEM_V4
    # ═══════════════════════════════════════════════════════════════════
    v4 = REPO_ROOT / "system_v4" / "a2_state"
    if v4.exists():
        for f in sorted(v4.glob("*.md")):
            add(str(f), "SYSTEM_V4")

    # ═════════════════════════════════════════════════════════════════
    # Save — NOTE: work/ paths intentionally EXCLUDED
    # ═════════════════════════════════════════════════════════════════
    ENTROPY_ORDER = {
        "SPEC_CORE": 0, "SPEC_SUPPLEMENT": 1, "CONTROL_PLANE": 2,
        "A2_STATE_FORMAL": 3, "A1_STATE": 4, "REFINED_FUEL": 5,
        "CORE_DOCS_RAW": 6, "RUN_ANCHOR": 7, "UPGRADE_DOCS": 8,
        "HIGH_ENTROPY": 9, "SYSTEM_V4": 10,
    }

    queue.sort(key=lambda e: ENTROPY_ORDER.get(e["entropy_class"], 99))
    refinery.save_queue(queue)

    # Report
    done = sum(1 for e in queue if e["status"] == "DONE")
    source_reg = sum(1 for e in queue if e["status"] == "SOURCE_REGISTERED")
    pending = sum(1 for e in queue if e["status"] == "PENDING")
    by_class = {}
    for e in queue:
        ec = e["entropy_class"]
        if ec not in by_class:
            by_class[ec] = {"pending": 0, "done": 0, "source_registered": 0}
        st = e["status"].lower()
        by_class[ec][st] = by_class[ec].get(st, 0) + 1

    print(f"Total docs in queue: {len(queue)}")
    print(f"  Done: {done}")
    print(f"  Source registered: {source_reg}")
    print(f"  Pending: {pending}")
    print()
    for ec in sorted(by_class.keys(), key=lambda k: ENTROPY_ORDER.get(k, 99)):
        d = by_class[ec]
        print(f"  {ec:20s} {d.get('pending', 0):3d} pending, "
              f"{d.get('source_registered', 0):3d} registered, "
              f"{d.get('done', 0):3d} done")


if __name__ == "__main__":
    main()
