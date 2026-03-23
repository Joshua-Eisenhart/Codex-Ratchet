"""
E2E Smoke test for run_real_ratchet.py.

Verifies that the main pipeline loop can initialize, resolve skills from the
registry, load graph fuel (even if empty to simulate dry-run/skip LLM calls),
and correctly invoke the final wrapup phases like Overseer, Lawyer, and Bridge.

Usage:
    cd "/Users/joshuaeisenhart/Desktop/Codex Ratchet"
    python -m system_v4.skills.test_run_real_ratchet_smoke
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Import main loop
from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.skill_registry import SkillRegistry


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
    ready_packet_path = a2_state / "A1_WORKER_LAUNCH_PACKET__CURRENT__TEST__v1.json"
    graph_path = root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
    _write_json(
        ready_packet_path,
        {
            "schema": "A1_WORKER_LAUNCH_PACKET_v1",
            "model": "GPT-5.4 Medium",
            "thread_class": "A1_WORKER",
            "mode": "PROPOSAL_ONLY",
            "queue_status": "READY_FROM_EXISTING_FUEL",
            "dispatch_id": "A1_DISPATCH__SMOKE__v1",
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
    _write_json(
        a2_state / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__TEST__v1.json",
        {
            "schema": "A2_CONTROLLER_LAUNCH_SPINE_v1",
            "launch_gate_status": "LAUNCH_READY",
            "mode": "CONTROLLER_ONLY",
            "current_a1_queue_status": "A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL",
        },
    )
    _write_json(
        a2_state / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__TEST__v1.json",
        {
            "schema": "A2_CONTROLLER_LAUNCH_HANDOFF_v1",
            "thread_class": "A2_CONTROLLER",
            "mode": "CONTROLLER_ONLY",
            "dispatch_rule": "substantive processing belongs in a bounded worker packet whenever a worker expression already exists",
            "stop_rule": "stop after one bounded controller action unless one exact worker dispatch is issued",
        },
    )
    _write_json(
        a2_state / "A1_QUEUE_STATUS_PACKET__CURRENT__TEST__v1.json",
        {
            "schema": "A1_QUEUE_STATUS_PACKET_v1",
            "queue_status": "READY_FROM_EXISTING_FUEL",
            "reason": "bounded A2 family slice compiled into one ready A1 packet surface",
            "dispatch_id": "A1_DISPATCH__SMOKE__v1",
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
            "maker_intent": "Preserve maker intent in the graph and witness spine during live runs.",
            "notes": "Startup queue notes should also survive as first-class intent.",
        },
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
    temp_root = Path(tempfile.mkdtemp(prefix="rr_smoke_"))
    original_repo = rr.REPO
    rr.REPO = str(temp_root)

    try:
        print("run_real_ratchet E2E smoke verification")
        print(f"Repo: {original_repo}")
        print(f"Temp root: {temp_root}")

        # 1. Provide minimal graph fuel (empty) to skip real LLM extraction
        a2_dir = temp_root / "system_v4" / "a2_state" / "graphs"
        a2_dir.mkdir(parents=True, exist_ok=True)
        graph_path = a2_dir / "system_graph_a2_refinery.json"
        graph_path.write_text(json.dumps(_minimal_graph("V4_SYSTEM_GRAPH_v1")), encoding="utf-8")
        _write_json(a2_dir / "identity_registry_v1.json", _minimal_graph("IDENTITY_REGISTRY_v1"))
        _write_json(temp_root / "system_v4" / "a1_state" / "a1_stripped_graph_v1.json", _minimal_stripped_graph())

        # 2. Provide a mock skill registry copied from real one
        a1_dir = temp_root / "system_v4" / "a1_state"
        a1_dir.mkdir(parents=True, exist_ok=True)
        real_registry_path = REPO_ROOT / "system_v4" / "a1_state" / "skill_registry_v1.json"
        if real_registry_path.exists():
            shutil.copyfile(real_registry_path, a1_dir / "skill_registry_v1.json")
            
        real_rosetta = REPO_ROOT / "system_v4" / "a1_state" / "rosetta_v2_store.json"
        if real_rosetta.exists():
            shutil.copyfile(real_rosetta, a1_dir / "rosetta_v2_store.json")

        runtime_dir = temp_root / "system_v4" / "runtime_state"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        _write_procedure_surfaces(temp_root)

        print("\nFiring run_real_ratchet main loop...")
        try:
            exit_code = rr.main()
            if exit_code != 0:
                raise AssertionError(f"run_real_ratchet returned non-zero exit code {exit_code}")
            cartridge_graph_path = temp_root / "system_v4" / "a1_state" / "a1_cartridge_graph_v1.json"
            if not cartridge_graph_path.exists():
                raise AssertionError("cartridge owner graph report missing from smoke run")
            cartridge_graph = json.loads(cartridge_graph_path.read_text(encoding="utf-8"))
            if cartridge_graph.get("schema") != "A1_CARTRIDGE_GRAPH_v1":
                raise AssertionError("unexpected cartridge owner graph schema in smoke run")
            if cartridge_graph.get("build_status") != "FAIL_CLOSED":
                raise AssertionError(
                    "expected cartridge owner preflight to fail closed on doctrinal cartridge block"
                )
            if cartridge_graph.get("materialized") is not False:
                raise AssertionError(
                    "expected cartridge owner preflight to remain non-materialized in smoke workspace"
                )
            blocked_terms = cartridge_graph.get("blocked_terms", [])
            if len(blocked_terms) != 1:
                raise AssertionError(
                    "expected one blocked stripped term in cartridge owner preflight smoke report"
                )
            if blocked_terms[0].get("term") != "pairwise_correlation_spread_functional":
                raise AssertionError(
                    "expected seeded stripped term to be the doctrinally blocked term"
                )
            bridged_graph_path = temp_root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
            bridged_graph = json.loads(bridged_graph_path.read_text(encoding="utf-8"))
            bridged_nodes = bridged_graph.get("nodes", {})
            intent_nodes = [
                n for n in bridged_nodes.values()
                if n.get("node_type") == "INTENT_SIGNAL"
            ]
            context_nodes = [
                n for n in bridged_nodes.values()
                if n.get("node_type") == "CONTEXT_SIGNAL"
            ]
            if not intent_nodes:
                raise AssertionError("expected runtime bridge to materialize intent witness nodes")
            if not context_nodes:
                raise AssertionError("expected runtime bridge to materialize context witness nodes")
            control_surface_path = temp_root / "system_v4" / "a2_state" / "A2_INTENT_CONTROL__CURRENT__v1.json"
            if not control_surface_path.exists():
                raise AssertionError("expected current intent control surface to be written")
            control_surface = json.loads(control_surface_path.read_text(encoding="utf-8"))
            if control_surface.get("schema") != "A2_INTENT_CONTROL_SURFACE_v1":
                raise AssertionError("unexpected intent control surface schema")
            if control_surface.get("self_audit", {}).get("maker_intent_count") != 2:
                raise AssertionError("expected maker intent + queue notes in control surface")
            if control_surface.get("self_audit", {}).get("runtime_context_count") != 1:
                raise AssertionError("expected one startup runtime context in control surface")
            if control_surface.get("self_audit", {}).get("refined_intent_count", 0) < 1:
                raise AssertionError("expected graph-backed refined intent in control surface")
            witness_path = temp_root / "system_v4" / "a2_state" / "witness_corpus_v1.json"
            witness_corpus = json.loads(witness_path.read_text(encoding="utf-8"))
            intent_entries = [e for e in witness_corpus if e.get("witness", {}).get("kind") == "intent"]
            context_entries = [e for e in witness_corpus if e.get("witness", {}).get("kind") == "context"]
            if len(intent_entries) != 2:
                raise AssertionError("expected two startup intent witnesses in corpus")
            if len(context_entries) != 1:
                raise AssertionError("expected one startup context witness in corpus")
            intent_notes = [
                str(e.get("witness", {}).get("trace", [{}])[0].get("notes", [""])[0])
                for e in intent_entries
            ]
            if "Preserve maker intent in the graph and witness spine during live runs." not in intent_notes:
                raise AssertionError("maker_intent text missing from witness corpus")
            if "Startup queue notes should also survive as first-class intent." not in intent_notes:
                raise AssertionError("queue notes text missing from witness corpus")
            batch_values = {str(e.get("tags", {}).get("batch", "")) for e in intent_entries + context_entries}
            if len(batch_values - {""}) != 1:
                raise AssertionError("expected one shared batch id across startup intent/context witnesses")
            if not all(e.get("tags", {}).get("phase") == "STARTUP" for e in intent_entries + context_entries):
                raise AssertionError("expected startup phase tags on startup witnesses")
            queue_note_entries = [e for e in intent_entries if e.get("tags", {}).get("type") == "queue_notes"]
            if len(queue_note_entries) != 1:
                raise AssertionError("expected queue notes to remain separately tagged in witness corpus")
            print("\nPASS: run_real_ratchet e2e loop completed successfully without crashing.")
        except Exception as e:
            print(f"\nFAIL: run_real_ratchet e2e loop crashed: {e}")
            raise

    finally:
        rr.REPO = original_repo
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
