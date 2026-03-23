"""
Smoke checks for:
- graveyard-lawyer reopen marking
- draft sequential wiggle envelope construction
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from system_v4.skills.a1_brain import A1Brain
from system_v4.skills.a1_routing_state import A1RouteRecord, A1RoutingState
from system_v4.skills.b_kernel import GraveyardRecord
from system_v4.skills.graveyard_lawyer import build_rescue_report
from system_v4.skills.wiggle_lane_runner import build_wiggle_envelope


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    temp_root = Path(tempfile.mkdtemp(prefix="reopen_wiggle_smoke_"))

    try:
        # Minimal repo state copy
        (temp_root / "system_v4" / "a1_state").mkdir(parents=True, exist_ok=True)
        (temp_root / "system_v4" / "runtime_state").mkdir(parents=True, exist_ok=True)

        # Seed routing state with a concept eligible for reopen
        routing = A1RoutingState(str(temp_root))
        routing.upsert(A1RouteRecord(
            source_concept_id="A2_TEST::concept_1",
            source_name="concept_1",
            source_node_type="REFINED_CONCEPT",
            route_status="KERNEL_EXTRACTED",
            classification_kind="MATH_DEF",
            route_reason="initial_extract",
        ))
        routing.save()

        # Build a real brain on temp root and admit the derived term needed to reopen
        brain = A1Brain(str(temp_root), eval_mode=True)
        brain.term_registry["identity"] = {
            "state": "TERM_PERMITTED",
            "bound_math_def": "F999",
            "provenance": "SMOKE",
        }

        class KernelStub:
            graveyard = [
                GraveyardRecord(
                    candidate_id="F123",
                    reason_tag="DERIVED_ONLY_NOT_PERMITTED",
                    raw_lines=[],
                    failure_class="B_KILL",
                    source_concept_id="A2_TEST::concept_1",
                    primary_candidate_id="F120",
                    target_ref="F120",
                    stage="DERIVED_ONLY_GUARD",
                    detail="Derived-only term 'identity' in BARE value 'equality_identity'",
                    timestamp_utc="2026-03-20T00:00:00Z",
                )
            ]

        report = build_rescue_report(
            repo=str(temp_root),
            batch_id="SMOKE_BATCH",
            kernel=KernelStub(),
            brain=brain,
            limit=5,
            apply_reopens=True,
        )
        _assert(report["reopen_count"] == 1, "expected one reopen proposal")
        _assert(report["reopened_source_concept_ids"] == ["A2_TEST::concept_1"], "expected reopened source concept id")

        routing2 = A1RoutingState(str(temp_root))
        rec = routing2.get("A2_TEST::concept_1")
        _assert(rec is not None and rec.reopen_requested, "routing state did not record reopen")

        # Wiggle smoke: use a real concept that emits multiple candidate kinds
        wiggle_brain = A1Brain(str(repo_root), eval_mode=True)
        graph_nodes = {
            "A2_TEST::graph_1": {
                "name": "identity operator on finite dimensional hilbert space",
                "description": "identity operator on finite dimensional hilbert space",
                "tags": [],
                "properties": {},
            }
        }
        wiggle = build_wiggle_envelope(
            repo=str(repo_root),
            brain=wiggle_brain,
            concept_ids=["A2_TEST::graph_1"],
            graph_nodes=graph_nodes,
        )
        _assert(len(wiggle.lane_packets) >= 2, "expected at least two lane packets")
        _assert("merged_strategy_packet" in wiggle.to_dict(), "wiggle envelope missing merged packet")
        merged = wiggle.merged_strategy_packet
        _assert("targets" in merged and isinstance(merged["targets"], list), "merged packet missing targets")
        _assert("merge_report" in wiggle.to_dict(), "wiggle envelope missing merge report")

        print("PASS: graveyard reopen marks routing state and wiggle builds a merged envelope")
        print(json.dumps({
            "reopen_count": report["reopen_count"],
            "reopened_source_concept_ids": report["reopened_source_concept_ids"],
            "lane_count": len(wiggle.lane_packets),
            "merged_target_count": len(merged["targets"]),
        }, indent=2))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
