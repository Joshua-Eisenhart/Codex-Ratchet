"""
Patched A2 Graph Refinery test suite.

Tests all 7 newly added capabilities:
  1. Batch index reload on init
  2. Query/search tools (find_nodes, find_edges, concept_exists)
  3. Authority field on concepts
  4. Jargon warnings
  5. Session logging
  6. Concept dedup/merge (OVERLAPS edges)
  7. Mid-session checkpointing

Usage:
    cd /Users/joshuaeisenhart/Desktop/Codex\ Ratchet
    python -m system_v4.skills.test_a2_graph_refinery_patched
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import (
    A2GraphRefinery,
    ExtractionMode,
    RefineryBatch,
    RefineryLayer,
)


def _make_workspace() -> Path:
    """Create a temporary workspace that mirrors the expected directory structure."""
    tmp = Path(tempfile.mkdtemp(prefix="a2_refinery_test_"))
    (tmp / "system_v4" / "a2_state" / "graphs").mkdir(parents=True, exist_ok=True)
    (tmp / "system_v4" / "a2_state" / "session_logs").mkdir(parents=True, exist_ok=True)
    return tmp


def _test_concepts() -> list[dict]:
    return [
        {
            "name": "entropic_monism",
            "description": "Identity is emergent from constraint compatibility.",
            "tags": ["FOUNDATION", "AXIOM"],
            "authority": "SOURCE_CLAIM",
        },
        {
            "name": "completed_infinity_ban",
            "description": "Classical completed infinites are prohibited.",
            "tags": ["FENCE", "MATH_CLASS"],
            "authority": "SOURCE_CLAIM",
        },
        {
            "name": "dual_szilard_engine",
            "description": "Left/Right engines with structurally unequal loops.",
            "tags": ["ENGINE", "TOPOLOGY"],
            "authority": "CROSS_VALIDATED",
        },
    ]


def test_batch_index_reload():
    """Gap 1: Batch index persists and reloads across init."""
    print("\n[1] Batch index reload...")
    ws = _make_workspace()
    try:
        r1 = A2GraphRefinery(str(ws))
        r1.ingest_document(
            doc_path=str(ws / "fake_doc.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_RELOAD_001",
            concepts=_test_concepts(),
        )
        assert len(r1.batches) == 1, f"Expected 1 batch, got {len(r1.batches)}"

        # Re-init — batches should reload from disk
        r2 = A2GraphRefinery(str(ws))
        assert len(r2.batches) == 1, f"Expected 1 batch after reload, got {len(r2.batches)}"
        assert r2.batches[0].batch_id == "BATCH_RELOAD_001"
        assert r2.batches[0].jargon_warnings == []
        print("   PASS ✓")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_query_tools():
    """Gap 2: find_nodes, find_edges, concept_exists."""
    print("\n[2] Query / search tools...")
    ws = _make_workspace()
    try:
        r = A2GraphRefinery(str(ws))
        r.ingest_document(
            doc_path=str(ws / "query_test.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_QUERY_001",
            concepts=_test_concepts(),
        )

        # find_nodes by name
        results = r.find_nodes(name_contains="monism")
        assert len(results) == 1, f"Expected 1 node for 'monism', got {len(results)}"
        assert "entropic_monism" in results[0]["name"]

        # find_nodes by tag
        results = r.find_nodes(tags_any=["ENGINE"])
        assert len(results) == 1, f"Expected 1 ENGINE node, got {len(results)}"

        # find_nodes by layer
        results = r.find_nodes(layer=RefineryLayer.A2_3_INTAKE)
        assert len(results) >= 4, f"Expected >=4 A2-3 nodes, got {len(results)}"

        # find_edges
        edges = r.find_edges(relation_type="SOURCE_MAP_PASS")
        assert len(edges) >= 3, f"Expected >=3 SOURCE_MAP edges, got {len(edges)}"

        # concept_exists
        existing = r.concept_exists("entropic_monism")
        assert existing is not None, "Expected to find entropic_monism"

        missing = r.concept_exists("nonexistent_concept")
        assert missing is None, "Should not find nonexistent concept"

        print("   PASS ✓")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_authority_field():
    """Gap 3: Authority field is persisted at the top-level of GraphNode."""
    print("\n[3] Authority field on concepts...")
    ws = _make_workspace()
    try:
        r = A2GraphRefinery(str(ws))
        r.ingest_document(
            doc_path=str(ws / "auth_test.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_AUTH_001",
            concepts=_test_concepts(),
        )

        source_claim_nodes = [
            n for n in r.builder.pydantic_model.nodes.values()
            if n.authority == "SOURCE_CLAIM" and n.node_type == "EXTRACTED_CONCEPT"
        ]
        cross_val_nodes = [
            n for n in r.builder.pydantic_model.nodes.values()
            if n.authority == "CROSS_VALIDATED" and n.node_type == "EXTRACTED_CONCEPT"
        ]
        assert len(source_claim_nodes) == 2, f"Expected 2 SOURCE_CLAIM nodes, got {len(source_claim_nodes)}"
        assert len(cross_val_nodes) == 1, f"Expected 1 CROSS_VALIDATED node, got {len(cross_val_nodes)}"
        print("   PASS ✓")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_jargon_warning():
    """Gap 4: Jargon warnings attach to batches and persist."""
    print("\n[4] Jargon warnings...")
    ws = _make_workspace()
    try:
        r = A2GraphRefinery(str(ws))
        r.ingest_document(
            doc_path=str(ws / "jargon_test.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_JARGON_001",
            concepts=_test_concepts(),
        )

        ok = r.warn_jargon("BATCH_JARGON_001", "Old Thread S jargon found: uses deprecated term 'Szilard'")
        assert ok, "warn_jargon should return True for existing batch"

        not_ok = r.warn_jargon("NONEXISTENT", "should fail")
        assert not not_ok, "warn_jargon should return False for missing batch"

        # Verify persistence
        r2 = A2GraphRefinery(str(ws))
        assert len(r2.batches[0].jargon_warnings) == 1
        assert "Szilard" in r2.batches[0].jargon_warnings[0]
        print("   PASS ✓")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_session_logging():
    """Gap 5: Session start/end writes markdown log."""
    print("\n[5] Session logging...")
    ws = _make_workspace()
    try:
        r = A2GraphRefinery(str(ws))
        sid = r.start_session("TEST_SESSION_001")
        assert sid == "TEST_SESSION_001"

        r.log_finding("Discovered dual-engine topology")

        r.ingest_document(
            doc_path=str(ws / "session_test.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_SESSION_001",
            concepts=_test_concepts(),
        )

        log_path = r.end_session()
        assert log_path is not None, "end_session should return log path"

        log_content = Path(log_path).read_text()
        assert "TEST_SESSION_001" in log_content
        assert "Nodes added:** 4" in log_content  # markdown bold format
        assert "dual-engine topology" in log_content
        assert "BATCH_SESSION_001" in log_content
        print("   PASS ✓")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_concept_dedup():
    """Gap 6: Duplicate concepts create OVERLAPS edges instead of new nodes."""
    print("\n[6] Concept dedup / OVERLAPS edges...")
    ws = _make_workspace()
    try:
        r = A2GraphRefinery(str(ws))

        # First ingest
        r.ingest_document(
            doc_path=str(ws / "dedup_doc1.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_DEDUP_001",
            concepts=[{
                "name": "entropic_monism",
                "description": "First appearance.",
                "tags": ["TEST"],
            }],
        )
        node_count_1 = len(r.builder.pydantic_model.nodes)

        # Second ingest with same concept name
        r.ingest_document(
            doc_path=str(ws / "dedup_doc2.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_DEDUP_002",
            concepts=[{
                "name": "entropic_monism",
                "description": "Duplicate from another doc.",
                "tags": ["TEST"],
            }],
        )
        node_count_2 = len(r.builder.pydantic_model.nodes)

        # Should have added only 1 source node (not a new concept node)
        assert node_count_2 == node_count_1 + 1, (
            f"Expected {node_count_1 + 1} nodes (only new source), got {node_count_2}"
        )

        # Should have an OVERLAPS edge
        overlaps = r.find_edges(relation_type="OVERLAPS")
        assert len(overlaps) == 1, f"Expected 1 OVERLAPS edge, got {len(overlaps)}"
        print("   PASS ✓")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_mid_session_checkpoint():
    """Gap 7: Checkpoint counter increments during session."""
    print("\n[7] Mid-session checkpointing...")
    ws = _make_workspace()
    try:
        r = A2GraphRefinery(str(ws))
        r.start_session("TEST_CHECKPOINT_001")

        r.ingest_document(
            doc_path=str(ws / "cp_test1.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_CP_001",
            concepts=_test_concepts(),
        )
        r.ingest_document(
            doc_path=str(ws / "cp_test2.txt"),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id="BATCH_CP_002",
            concepts=[{
                "name": "new_concept_here",
                "description": "Different concept.",
                "tags": ["TEST"],
            }],
        )

        assert r._active_session is not None
        assert r._active_session.checkpoints == 2, (
            f"Expected 2 checkpoints, got {r._active_session.checkpoints}"
        )

        log_path = r.end_session()
        log_content = Path(log_path).read_text()
        assert "Checkpoints:** 2" in log_content
        print("   PASS ✓")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def main():
    print("=" * 60)
    print("A2 Graph Refinery — Patched Feature Test Suite")
    print("=" * 60)

    tests = [
        test_batch_index_reload,
        test_query_tools,
        test_authority_field,
        test_jargon_warning,
        test_session_logging,
        test_concept_dedup,
        test_mid_session_checkpoint,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            print(f"   FAIL ✗ — {exc}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'=' * 60}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
