"""
End-to-end smoke for run_real_ratchet.py using a temp workspace.

This is intentionally coarse-grained:
- runs the real batch loop against a tiny synthetic refinery graph
- verifies phase logging, cross-surface writes, and bridged graph integrity
- avoids mutating the main workspace by overriding RATCHET_REPO_ROOT
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _minimal_graph(schema: str) -> dict:
    return {
        "schema": schema,
        "nodes": {},
        "edges": [],
    }


def _minimal_stripped_graph() -> dict:
    stripped_id = "A1_STRIPPED::pairwise_correlation_spread_functional"
    return {
        "schema": "A1_STRIPPED_GRAPH_v1",
        "nodes": {
            stripped_id: {
                "id": stripped_id,
                "node_type": "DEPENDENCY_TERM",
                "layer": "A1_STRIPPED",
                "name": "pairwise_correlation_spread_functional",
                "lineage_refs": ["A1_JARGONED::pairwise_correlation_spread_functional"],
                "witness_refs": ["A2_TEST::density_matrix_channel"],
                "properties": {
                    "source_jargoned_id": "A1_JARGONED::pairwise_correlation_spread_functional",
                },
            }
        },
        "edges": [],
    }


def _build_temp_workspace(root: Path) -> None:
    registry_src = WORKSPACE_ROOT / "system_v4" / "a1_state" / "skill_registry_v1.json"
    registry = json.loads(registry_src.read_text(encoding="utf-8"))
    _write_json(root / "system_v4" / "a1_state" / "skill_registry_v1.json", registry)

    graph = {
        "schema": "V4_SYSTEM_GRAPH_v1",
        "nodes": {
            "A2_TEST::density_matrix_channel": {
                "id": "A2_TEST::density_matrix_channel",
                "node_type": "REFINED_CONCEPT",
                "layer": "A2_2_CANDIDATE",
                "name": "density_matrix_channel",
                "description": "Identity operator on finite dimensional hilbert space density matrix channel.",
                "authority": "SOURCE_CLAIM",
                "tags": ["MATH_CLASS", "TEST"],
                "trust_zone": "A2_2",
                "properties": {
                    "structural_form": "density_matrix_channel",
                },
                "status": "active",
                "admissibility_state": "PROPOSAL_ONLY",
            },
            "A2_TEST::pipeline_invariant_gate": {
                "id": "A2_TEST::pipeline_invariant_gate",
                "node_type": "REFINED_CONCEPT",
                "layer": "A2_2_CANDIDATE",
                "name": "pipeline_invariant_gate",
                "description": "Pipeline invariant gate for staged validation and execution audit.",
                "authority": "SOURCE_CLAIM",
                "tags": ["FENCE", "SPEC", "TEST"],
                "trust_zone": "A2_2",
                "properties": {},
                "status": "active",
                "admissibility_state": "PROPOSAL_ONLY",
            },
            "A2_TEST::soft_discourse_note": {
                "id": "A2_TEST::soft_discourse_note",
                "node_type": "EXTRACTED_CONCEPT",
                "layer": "A2_3_INTAKE",
                "name": "soft_discourse_note",
                "description": "This is a discussion note about context and framing.",
                "authority": "SOURCE_CLAIM",
                "tags": ["NOTE", "TEST"],
                "trust_zone": "A2_3",
                "properties": {},
                "status": "active",
                "admissibility_state": "PROPOSAL_ONLY",
            },
        },
        "edges": [],
    }
    _write_json(root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json", graph)
    _write_json(root / "system_v4" / "a2_state" / "graphs" / "identity_registry_v1.json", _minimal_graph("IDENTITY_REGISTRY_v1"))
    _write_json(root / "system_v4" / "a1_state" / "a1_stripped_graph_v1.json", _minimal_stripped_graph())

    (root / "system_v4" / "runtime_state").mkdir(parents=True, exist_ok=True)
    _write_procedure_surfaces(root)


def _write_procedure_surfaces(root: Path) -> None:
    a2_state = root / "system_v3" / "a2_state"
    a2_state.mkdir(parents=True, exist_ok=True)
    specs_dir = root / "system_v3" / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    a1_state = root / "system_v3" / "a1_state"
    a1_state.mkdir(parents=True, exist_ok=True)
    boot_path = specs_dir / "31_A1_THREAD_BOOT__v1.md"
    boot_path.write_text("# test boot\n", encoding="utf-8")
    family_slice_path = a2_state / "A2_TO_A1_FAMILY_SLICE__TEST__v1.json"
    _write_json(family_slice_path, {"schema": "A2_TO_A1_FAMILY_SLICE_v1"})
    graph_path = root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
    ready_packet_path = a2_state / "A1_WORKER_LAUNCH_PACKET__CURRENT__TEST__v1.json"
    _write_json(
        ready_packet_path,
        {
            "schema": "A1_WORKER_LAUNCH_PACKET_v1",
            "model": "GPT-5.4 Medium",
            "thread_class": "A1_WORKER",
            "mode": "PROPOSAL_ONLY",
            "queue_status": "READY_FROM_EXISTING_FUEL",
            "dispatch_id": "A1_DISPATCH__TEST__v1",
            "target_a1_role": "A1_PROPOSAL",
            "required_a1_boot": str(boot_path),
            "source_a2_artifacts": [str(graph_path)],
            "a1_reload_artifacts": [],
            "bounded_scope": "one bounded proposal cycle",
            "prompt_to_send": "Run one bounded A1 proposal pass from the provided graph fuel and stop.",
            "stop_rule": "one bounded proposal cycle",
            "go_on_count": 0,
            "go_on_budget": 1,
        },
    )

    controller_spine = {
        "schema": "A2_CONTROLLER_LAUNCH_SPINE_v1",
        "launch_gate_status": "LAUNCH_READY",
        "mode": "CONTROLLER_ONLY",
        "current_a1_queue_status": "A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL",
    }
    _write_json(
        a2_state / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__TEST__v1.json",
        controller_spine,
    )

    controller_handoff = {
        "schema": "A2_CONTROLLER_LAUNCH_HANDOFF_v1",
        "thread_class": "A2_CONTROLLER",
        "mode": "CONTROLLER_ONLY",
        "dispatch_rule": "substantive processing belongs in a bounded worker packet whenever a worker expression already exists",
        "stop_rule": "stop after one bounded controller action unless one exact worker dispatch is issued",
    }
    _write_json(
        a2_state / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__TEST__v1.json",
        controller_handoff,
    )

    queue_packet = {
        "schema": "A1_QUEUE_STATUS_PACKET_v1",
        "queue_status": "READY_FROM_EXISTING_FUEL",
        "reason": "bounded A2 family slice compiled into one ready A1 packet surface",
        "dispatch_id": "A1_DISPATCH__TEST__v1",
        "target_a1_role": "A1_PROPOSAL",
        "required_a1_boot": str(boot_path),
        "source_a2_artifacts": [str(graph_path)],
        "a1_reload_artifacts": [],
        "bounded_scope": "one bounded proposal cycle",
        "prompt_to_send": "Run one bounded A1 proposal pass from the provided graph fuel and stop.",
        "stop_rule": "one bounded proposal cycle",
        "go_on_count": 0,
        "go_on_budget": 1,
        "family_slice_json": str(family_slice_path),
        "ready_surface_kind": "A1_WORKER_LAUNCH_PACKET",
        "ready_packet_json": str(ready_packet_path),
        "ready_bundle_result_json": "",
        "ready_send_text_companion_json": "",
        "ready_launch_spine_json": "",
        "maker_intent": "Preserve maker intent continuously and keep it steering the live system.",
        "notes": "Queue context and maker notes should survive into graph-native control surfaces.",
    }
    _write_json(
        a2_state / "A1_QUEUE_STATUS_PACKET__CURRENT__TEST__v1.json",
        queue_packet,
    )
    launch_dir = (
        root
        / "system_v4"
        / "a2_state"
        / "launch_bundles"
        / "nested_graph_build_a1_cartridge"
    )
    _write_json(
        launch_dir / "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_CARTRIDGE__2026_03_20__v1.json",
        {
            "dispatch_id": "A1_CARTRIDGE__TEST__v1",
            "queue_status": "READY_FROM_EXISTING_FUEL",
        },
    )
    (a1_state / "A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md").write_text(
        "# cartridge review\n",
        encoding="utf-8",
    )
    (a1_state / "A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md").write_text(
        "# cross judgment\n",
        encoding="utf-8",
    )
    (a1_state / "A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md").write_text(
        "# alias lift\n",
        encoding="utf-8",
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="ratchet_e2e_smoke_"))
    try:
        _build_temp_workspace(temp_root)

        env = dict(os.environ)
        env["RATCHET_REPO_ROOT"] = str(temp_root)
        env["PYTHONPATH"] = str(WORKSPACE_ROOT)

        proc = subprocess.run(
            [sys.executable, "-m", "system_v4.skills.run_real_ratchet", "--runtime-model=gemini"],
            cwd=str(WORKSPACE_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        print("run_real_ratchet e2e smoke")
        print(f"Workspace: {WORKSPACE_ROOT}")
        print(f"Temp root:  {temp_root}")
        print(proc.stdout)
        if proc.stderr.strip():
            print(proc.stderr)

        _assert(proc.returncode == 0, f"run_real_ratchet exited {proc.returncode}")

        match = re.search(r"BATCH_LIVE_\d+", proc.stdout)
        _assert(match is not None, "batch id missing from output")
        batch_id = match.group(0)

        log_path = temp_root / "system_v4" / "a1_state" / "skill_invocation_log.jsonl"
        _assert(log_path.exists(), "invocation log not written")
        entries = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        batch_entries = [entry for entry in entries if entry.get("batch_id") == batch_id]
        phases = [entry.get("phase") for entry in batch_entries]
        selected_by_phase = {
            entry.get("phase"): entry.get("selected_skill_id")
            for entry in batch_entries
        }
        considered_by_phase = {
            entry.get("phase"): entry.get("considered_skill_ids", [])
            for entry in batch_entries
        }
        for phase in (
            "PHASE_A2_3_INTAKE",
            "PHASE_A2_2_CONTRADICTION",
            "PHASE_A2_1_PROMOTION",
            "PHASE_A1_ROSETTA",
            "PHASE_A1_STRIPPER",
            "A1_CARTRIDGE_OWNER_GRAPH",
            "A2_INTENT_GRAPH_SYNC",
            "A2_INTENT_CONTROL",
        ):
            _assert(phase in phases, f"missing upstream phase {phase} in invocation log")
        _assert(
            selected_by_phase.get("PHASE_A2_3_INTAKE") == "a2-high-intake-graph-builder",
            "expected PHASE_A2_3_INTAKE to select a2-high-intake-graph-builder",
        )
        _assert(
            selected_by_phase.get("PHASE_A2_2_CONTRADICTION") == "a2-mid-refinement-graph-builder",
            "expected PHASE_A2_2_CONTRADICTION to select a2-mid-refinement-graph-builder",
        )
        _assert(
            selected_by_phase.get("PHASE_A2_1_PROMOTION") == "a2-low-control-graph-builder",
            "expected PHASE_A2_1_PROMOTION to select a2-low-control-graph-builder",
        )
        _assert(
            selected_by_phase.get("PHASE_A1_ROSETTA") == "a1-jargoned-graph-builder",
            "expected PHASE_A1_ROSETTA to select a1-jargoned-graph-builder",
        )
        _assert(
            selected_by_phase.get("PHASE_A1_STRIPPER") == "a1-stripped-graph-builder",
            "expected PHASE_A1_STRIPPER to select a1-stripped-graph-builder",
        )
        _assert(
            selected_by_phase.get("A1_CARTRIDGE_OWNER_GRAPH") == "a1-cartridge-graph-builder",
            "expected cartridge owner preflight to select a1-cartridge-graph-builder",
        )
        _assert(
            "PHASE 1: A1 CARTRIDGE PACKAGING" in proc.stdout,
            "expected Phase 1 cartridge packaging banner in stdout",
        )
        _assert(
            "PRE-PHASE: A1 CARTRIDGE OWNER GRAPH" in proc.stdout,
            "expected cartridge owner preflight banner in stdout",
        )
        _assert(
            "build_status: FAIL_CLOSED" in proc.stdout,
            "expected cartridge owner preflight to surface FAIL_CLOSED semantics in stdout",
        )
        _assert(
            "Semantics: fail-closed owner-graph preflight; continuing to packaging operator" in proc.stdout,
            "expected cartridge owner preflight to continue honestly on semantic fail-closed output",
        )
        _assert(
            "Skill: a1-cartridge-assembler [dispatch]" in proc.stdout,
            "expected Phase 1 to dispatch a1-cartridge-assembler",
        )
        _assert(
            "Selector mode: generic-operator" in proc.stdout,
            "expected Phase 1 to stay generic-operator driven until a phase-bound owner builder exists",
        )
        _assert(
            considered_by_phase.get("PHASE_A1_ROSETTA") == [
                "a1-jargoned-graph-builder",
                "a1-rosetta-mapper",
            ],
            "expected PHASE_A1_ROSETTA considered set to include builder + mapper",
        )
        _assert(
            considered_by_phase.get("PHASE_A1_STRIPPER") == [
                "a1-rosetta-stripper",
                "a1-stripped-graph-builder",
            ],
            "expected PHASE_A1_STRIPPER considered set to include stripper + builder",
        )
        _assert(
            any(phase in phases for phase in ("A1_WIGGLE", "A1_EXTRACTION")),
            "expected A1_WIGGLE or A1_EXTRACTION in invocation log",
        )
        for phase in ("B_ENFORCEMENT", "RATCHET_OVERSEER", "GRAVEYARD_REVIEW", "GRAPH_BRIDGE"):
            _assert(phase in phases, f"missing phase {phase} in invocation log")
        _assert(
            "A2_BRAIN_SURFACE_REFRESH" in phases,
            "missing A2_BRAIN_SURFACE_REFRESH in invocation log",
        )
        _assert(
            all(entry.get("fallback_used") is False for entry in batch_entries),
            "expected no fallback dispatches in smoke batch",
        )
        if "A1_WIGGLE" in phases:
            _assert(
                "A1_EXTRACTION" not in phases,
                "wiggle batch should not also log executed A1_EXTRACTION",
            )

        cartridge_graph_path = temp_root / "system_v4" / "a1_state" / "a1_cartridge_graph_v1.json"
        _assert(cartridge_graph_path.exists(), "expected cartridge owner graph report to be written")
        cartridge_graph = json.loads(cartridge_graph_path.read_text(encoding="utf-8"))
        _assert(
            cartridge_graph.get("schema") == "A1_CARTRIDGE_GRAPH_v1",
            "expected cartridge owner graph schema",
        )
        _assert(
            cartridge_graph.get("build_status") == "FAIL_CLOSED",
            "expected smoke cartridge owner preflight to fail closed on doctrinal cartridge block",
        )
        _assert(
            cartridge_graph.get("materialized") is False,
            "expected smoke cartridge owner preflight to stay non-materialized",
        )
        blocked_terms = cartridge_graph.get("blocked_terms", [])
        _assert(
            len(blocked_terms) == 1,
            "expected smoke cartridge owner preflight to record one doctrinally blocked stripped term",
        )
        _assert(
            blocked_terms[0].get("term") == "pairwise_correlation_spread_functional",
            "expected blocked stripped term to match the seeded exact term",
        )
        _assert(
            len(blocked_terms[0].get("evidence", [])) > 0,
            "expected blocked stripped term to include doctrine evidence",
        )
        _assert(
            "A1_STRIPPED owner graph is missing or empty" not in cartridge_graph.get("blockers", []),
            "expected smoke cartridge owner preflight to exercise a non-empty stripped graph path",
        )

        b_state_path = temp_root / "system_v4" / "runtime_state" / "b_kernel_state.json"
        _assert(b_state_path.exists(), "b_kernel_state.json not written")
        b_state = json.loads(b_state_path.read_text(encoding="utf-8"))
        survivor_count = len(b_state.get("survivor_ledger", {}))
        park_count = len(b_state.get("park_set", {}))
        graveyard_count = len(b_state.get("graveyard", []))
        _assert(
            survivor_count + park_count + graveyard_count > 0,
            "expected at least one B outcome in smoke batch",
        )

        graph_path = temp_root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = graph.get("nodes", {})
        edges = graph.get("edges", [])
        runtime_node_types = {"B_SURVIVOR", "B_PARKED", "GRAVEYARD_RECORD", "SIM_KILL", "TERM_ADMITTED"}
        _assert(
            any(node.get("node_type") in runtime_node_types for node in nodes.values()),
            "expected at least one runtime node in bridged graph",
        )
        node_ids = set(nodes)
        dangling = [edge for edge in edges if edge["source_id"] not in node_ids or edge["target_id"] not in node_ids]
        _assert(not dangling, f"expected 0 dangling edges, found {len(dangling)}")
        evermem_state_path = temp_root / "system_v4" / "a2_state" / "EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json"
        evermem_report_json = temp_root / "system_v4" / "a2_state" / "audit_logs" / "EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json"
        evermem_report_md = temp_root / "system_v4" / "a2_state" / "audit_logs" / "EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md"
        _assert(evermem_state_path.exists(), "expected EverMem sync state file to be written")
        _assert(evermem_report_json.exists(), "expected EverMem sync report json to be written")
        _assert(evermem_report_md.exists(), "expected EverMem sync report markdown to be written")
        evermem_state = json.loads(evermem_state_path.read_text(encoding="utf-8"))
        _assert(
            evermem_state.get("schema") == "EVERMEM_WITNESS_SYNC_STATE_v1",
            "unexpected EverMem sync state schema",
        )
        _assert(
            evermem_state.get("last_sync_idx") == 0,
            "without a live EverMem backend, smoke should preserve cursor at 0",
        )
        _assert(
            evermem_state.get("status") == "sync_failed",
            "expected EverMem sync to fail closed without a local backend",
        )
        brain_refresh_report = (
            temp_root / "system_v4" / "a2_state" / "audit_logs" / "A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json"
        )
        brain_refresh_packet = (
            temp_root / "system_v4" / "a2_state" / "audit_logs" / "A2_BRAIN_SURFACE_REFRESH_PACKET__CURRENT__v1.json"
        )
        _assert(brain_refresh_report.exists(), "expected A2 brain refresh report json to be written")
        _assert(brain_refresh_packet.exists(), "expected A2 brain refresh packet json to be written")
        refresh_payload = json.loads(brain_refresh_report.read_text(encoding="utf-8"))
        _assert(refresh_payload.get("audit_only") is True, "brain refresh report should stay audit-only")
        _assert(
            refresh_payload.get("staged_output_targets", {}).get("packet_json"),
            "brain refresh report should record its packet target",
        )

        print("PASS: run_real_ratchet completed against temp workspace and wrote coherent state")
        print(
            f"  batch={batch_id} survivors={survivor_count} parks={park_count} "
            f"graveyard={graveyard_count} graph_nodes={len(nodes)} graph_edges={len(edges)}"
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
