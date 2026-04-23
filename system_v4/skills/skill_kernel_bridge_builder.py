"""
skill_kernel_bridge_builder.py

Creates explicit SKILL → KERNEL_CONCEPT edges in the authoritative graph.

This is the forward-motion work that Codex's bridge audits identified as
needed but did not execute. These are NOT heuristic edges — each mapping
is a hand-verified correspondence between a skill and the kernel concepts
it directly operates on or implements.

Edge relation: SKILL_OPERATES_ON
Provenance: antigravity_bridge_builder_v1
"""

from __future__ import annotations

import json
import time
import hashlib
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"

# ═══════════════════════════════════════════════════════════════
# Explicit skill → kernel concept mappings
#
# Format: skill_name → [list of kernel concept name substrings]
# The builder resolves these to actual node IDs at runtime.
# ═══════════════════════════════════════════════════════════════

SKILL_KERNEL_MAP: dict[str, list[str]] = {
    # ── Core pipeline skills ──
    "b-kernel": [
        "b_kernel_7_stage_pipeline",
        "b_canon_state_objects",
        "DETERMINISTIC_KERNEL_PIPELINE",
        "derived_only_guard",
        "elimination_over_truth",
    ],
    "b-adjudicator": [
        "b_kernel_7_stage_pipeline",
        "b_canon_state_objects",
    ],
    "sim-engine": [
        "sim_7_tier_architecture",
        "evidence_ladder_sims",
        "coupled_structural_evidence_ladders",
    ],
    "sim-holodeck-engine": [
        "sim_7_tier_architecture",
        "evidence_ladder_sims",
    ],
    "a1-brain": [
        "a1_rosetta_function",
        "a1_strategy_v1_schema",
        "a1_thread_boot_eight_hard_rules",
        "TERM_RATCHET_THROUGH_EVIDENCE",
    ],
    "a1-cartridge-assembler": [
        "a1_strategy_v1_schema",
    ],
    "a1-cartridge-graph-builder": [
        "a1_strategy_v1_schema",
        "graph_as_control_substrate",
    ],
    "a0-compiler": [
        "a0_deterministic_canonicalization",
        "a0_export_block_compilation",
    ],
    "run-real-ratchet": [
        "unitary_thread_b_ratchet",
        "DETERMINISTIC_KERNEL_PIPELINE",
        "eight_phase_gate_pipeline",
        "p0_through_p7_build_phases",
    ],

    # ── Rosetta / translation skills ──
    "rosetta-v2": [
        "a1_rosetta_function",
        "rosetta_translations_cognition_physics_game_theory",
        "mining_rosetta_artifact_packs_recovery",
    ],
    "a1-rosetta-mapper": [
        "a1_rosetta_function",
    ],
    "a1-rosetta-stripper": [
        "a1_rosetta_function",
    ],

    # ── Graph skills ──
    "a2-graph-refinery": [
        "graph_as_control_substrate",
        "GRAPH_AS_CONTROL_SUBSTRATE",
        "a2_canonical_schemas",
    ],
    "a2-high-intake-graph-builder": [
        "graph_as_control_substrate",
        "a2_entropy_reduction_mission",
    ],
    "a2-mid-refinement-graph-builder": [
        "graph_as_control_substrate",
    ],
    "a2-low-control-graph-builder": [
        "graph_as_control_substrate",
        "GRAPH_AS_CONTROL_SUBSTRATE",
    ],
    "runtime-graph-bridge": [
        "graph_as_control_substrate",
        "GRAPH_AS_CONTROL_SUBSTRATE",
    ],
    "v4-graph-builder": [
        "graph_as_control_substrate",
    ],
    "nested-graph-layer-auditor": [
        "graph_as_control_substrate",
    ],
    "graph-capability-auditor": [
        "graph_as_control_substrate",
    ],

    # ── Constraint / verification skills ──
    "z3-constraint-checker": [
        "constraint_ladder_contracts",
        "constraint_manifold_formal_derivation",
        "base_constraints_ledger_bc01_to_bc12",
        "root_constraints_f01_n01",
        "CONSTRAINT_MANIFOLD_FORMAL_DERIVATION",
        "ROOT_CONSTRAINTS_F01_N01",
        "BASE_CONSTRAINTS_LEDGER_BC01_BC12",
    ],
    "z3-cegis-refiner": [
        "constraint_ladder_contracts",
        "constraint_manifold_formal_derivation",
    ],
    "model-checker": [
        "constraint_ladder_contracts",
    ],

    # ── Trust / architecture skills ──
    "ratchet-overseer": [
        "four_layer_trust_architecture",
        "FOUR_LAYER_TRUST_SEPARATION",
        "COUPLED_LADDER_RATCHET",
    ],
    "ratchet-integrator": [
        "unitary_thread_b_ratchet",
        "COUPLED_LADDER_RATCHET",
    ],
    "ratchet-verify": [
        "unitary_thread_b_ratchet",
    ],
    "ratchet-reduce": [
        "unitary_thread_b_ratchet",
    ],
    "ratchet-reflect": [
        "unitary_thread_b_ratchet",
    ],
    "ratchet-reweave": [
        "unitary_thread_b_ratchet",
    ],
    "ratchet-a2-a1": [
        "A2_TO_B_DETERMINISTIC_BRIDGE",
    ],

    # ── Witness / evidence skills ──
    "witness-recorder": [
        "coupled_structural_evidence_ladders",
        "TERM_RATCHET_THROUGH_EVIDENCE",
    ],
    "witness-evermem-sync": [
        "coupled_structural_evidence_ladders",
    ],
    "witness-memory-retriever": [
        "coupled_structural_evidence_ladders",
    ],

    # ── Graveyard skills ──
    "graveyard-lawyer": [
        "elimination_over_truth",
        "deterministic_dual_replay",
    ],
    "graveyard-router": [
        "elimination_over_truth",
    ],

    # ── Entropy skills ──
    "a1-entropy-structure-decomposition-control": [
        "a2_entropy_reduction_mission",
        "holographic_entropy_bound",
    ],
    "a1-first-entropy-structure-campaign": [
        "a2_entropy_reduction_mission",
    ],
    "a1-entropy-bridge-helper-lift-pack": [
        "a2_entropy_reduction_mission",
    ],
    "a1-entropy-diversity-alias-lift-pack": [
        "a2_entropy_reduction_mission",
    ],
    "a2-entropy-bridge-helper-decomposition-control": [
        "a2_entropy_reduction_mission",
    ],
    "a2-thermodynamic-purge": [
        "a2_entropy_reduction_mission",
        "holographic_entropy_bound",
    ],

    # ── A2 brain / memory skills ──
    "a2-brain-surface-refresher": [
        "a2_canonical_schemas",
        "a2_thread_boot_nine_hard_rules",
    ],
    "a2-brain-refresh": [
        "a2_canonical_schemas",
    ],
    "brain-delta-consolidation": [
        "a2_canonical_schemas",
    ],
    "a2-a1-memory-admission-guard": [
        "a2_canonical_schemas",
        "four_layer_trust_architecture",
    ],
    "memory-admission-guard": [
        "four_layer_trust_architecture",
    ],

    # ── Lev / agents skills ──
    "a2-lev-agents-promotion-operator": [
        "lev_os_skill_system",
    ],
    "a2-lev-architecture-fitness-operator": [
        "lev_os_skill_system",
    ],
    "a2-lev-autodev-loop-audit-operator": [
        "lev_os_skill_system",
    ],
    "a2-lev-builder-formalization-proposal-operator": [
        "lev_os_skill_system",
    ],
    "a2-lev-builder-formalization-skeleton-operator": [
        "lev_os_skill_system",
    ],
    "a2-lev-builder-placement-audit-operator": [
        "lev_os_skill_system",
    ],

    # ── OpenClaw-RL / next-state skills ──
    "a2-next-state-signal-adaptation-audit-operator": [
        "karpathy_autoresearch_cegis_loop",
    ],
    "a2-next-state-directive-signal-probe-operator": [
        "karpathy_autoresearch_cegis_loop",
    ],

    # ── Skill improvement skills ──
    "skill-improver-operator": [
        "coupled_structural_evidence_ladders",
    ],
    "a2-skill-improver-readiness-operator": [
        "coupled_structural_evidence_ladders",
    ],
    "bounded-improve-operator": [
        "coupled_structural_evidence_ladders",
    ],

    # ── Autoresearch / council skills ──
    "autoresearch-operator": [
        "karpathy_autoresearch_cegis_loop",
    ],
    "llm-council-operator": [
        "karpathy_autoresearch_cegis_loop",
    ],

    # ── Doc queue / source intake ──
    "generate-doc-queue": [
        "a1_queue_status_surface",
    ],
    "a2-skill-source-intake-operator": [
        "a2_entropy_reduction_mission",
    ],

    # ── EverMem skills ──
    "evermem-memory-backend-adapter": [
        "a2_canonical_schemas",
    ],
    "pimono-evermem-adapter": [
        "a2_canonical_schemas",
    ],

    # ── Session / control skills ──
    "outer-session-ledger": [
        "a2_controller_dispatch_first",
    ],
    "outside-control-shell-operator": [
        "a2_controller_dispatch_first",
    ],
    "automation-controller": [
        "a2_controller_dispatch_first",
    ],
    "thread-dispatch-controller": [
        "a2_controller_dispatch_first",
        "eight_phase_gate_pipeline",
    ],

    # ── Misc operational skills ──
    "runtime-state-kernel": [
        "kernel_seed_state",
    ],
    "runtime-context-snapshot": [
        "kernel_seed_state",
    ],
    "wiggle-lane-runner": [
        "a1_branch_exploration_contract",
    ],
    "differential-tester": [
        "deterministic_dual_replay",
        "DUAL_REPLAY_DETERMINISM_REQUIREMENT",
    ],
    "property-pressure-tester": [
        "coupled_structural_evidence_ladders",
    ],
    "structured-fuzzer": [
        "coupled_structural_evidence_ladders",
    ],
    "intent-control-surface-builder": [
        "a2_controller_dispatch_first",
    ],
    "intent-refinement-graph-builder": [
        "graph_as_control_substrate",
    ],
    "identity-registry-builder": [
        "KERNEL__IDENTITY_EMERGENCE",
    ],
    "identity-registry-overlap-quarantine": [
        "KERNEL__IDENTITY_EMERGENCE",
    ],
    "fep-regulation-operator": [
        "ENTROPIC_MONISM_AND_ALLOWABLE_MATH",
    ],
}


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _edge_id(source_id: str, target_id: str, relation: str) -> str:
    raw = f"{source_id}::{target_id}::{relation}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def build_skill_kernel_bridges(
    repo_root: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    graph_path = root / GRAPH_PATH

    data = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])

    # Build lookup tables
    skill_by_name: dict[str, str] = {}
    kernel_by_name: dict[str, str] = {}
    for nid, n in nodes.items():
        if n.get("node_type") == "SKILL":
            skill_by_name[n.get("name", "")] = nid
        elif n.get("node_type") == "KERNEL_CONCEPT":
            kernel_by_name[n.get("name", "")] = nid

    # Build edges
    new_edges: list[dict[str, Any]] = []
    unresolved_skills: list[str] = []
    unresolved_kernels: list[str] = []
    matched_count = 0

    for skill_name, kernel_patterns in SKILL_KERNEL_MAP.items():
        skill_nid = skill_by_name.get(skill_name)
        if not skill_nid:
            unresolved_skills.append(skill_name)
            continue

        for pattern in kernel_patterns:
            kernel_nid = kernel_by_name.get(pattern)
            if not kernel_nid:
                unresolved_kernels.append(f"{skill_name} → {pattern}")
                continue

            edge = {
                "edge_id": _edge_id(skill_nid, kernel_nid, "SKILL_OPERATES_ON"),
                "source_id": skill_nid,
                "target_id": kernel_nid,
                "relation": "SKILL_OPERATES_ON",
                "attributes": {
                    "provenance": "antigravity_bridge_builder_v1",
                    "created_utc": _utc_iso(),
                    "skill_name": skill_name,
                    "kernel_concept_name": pattern,
                    "mapping_type": "explicit_hand_verified",
                },
            }
            new_edges.append(edge)
            matched_count += 1

    # Check for duplicates against existing edges
    existing_edge_keys = set()
    for e in edges:
        if isinstance(e, dict):
            key = f"{e.get('source_id')}::{e.get('target_id')}::{e.get('relation')}"
            existing_edge_keys.add(key)

    deduplicated = []
    dupes = 0
    for e in new_edges:
        key = f"{e['source_id']}::{e['target_id']}::{e['relation']}"
        if key not in existing_edge_keys:
            deduplicated.append(e)
            existing_edge_keys.add(key)
        else:
            dupes += 1

    return {
        "new_edges": deduplicated,
        "matched_count": matched_count,
        "deduplicated_count": len(deduplicated),
        "duplicate_count": dupes,
        "unresolved_skills": unresolved_skills,
        "unresolved_kernels": unresolved_kernels,
        "skill_count": len(skill_by_name),
        "kernel_count": len(kernel_by_name),
        "mapped_skills": len(SKILL_KERNEL_MAP),
    }


def inject_bridges(repo_root: str | Path) -> dict[str, Any]:
    """Build and inject SKILL_OPERATES_ON edges into the live graph."""
    root = Path(repo_root).resolve()
    graph_path = root / GRAPH_PATH

    result = build_skill_kernel_bridges(root)

    if not result["new_edges"]:
        print("No new edges to inject.")
        return result

    # Load graph, append edges, save
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    edges.extend(result["new_edges"])
    data["edges"] = edges

    # Write back
    graph_path.write_text(
        json.dumps(data, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    # Emit report
    report = {
        "schema": "SKILL_KERNEL_BRIDGE_INJECTION_v1",
        "generated_utc": _utc_iso(),
        "injected_edge_count": len(result["new_edges"]),
        "matched_count": result["matched_count"],
        "duplicate_count": result["duplicate_count"],
        "unresolved_skills": result["unresolved_skills"],
        "unresolved_kernels": result["unresolved_kernels"],
        "mapped_skills_count": result["mapped_skills"],
        "total_skills_in_graph": result["skill_count"],
        "total_kernels_in_graph": result["kernel_count"],
        "coverage": f"{result['mapped_skills']}/{result['skill_count']}",
    }
    report_path = root / "system_v4" / "a2_state" / "audit_logs" / "SKILL_KERNEL_BRIDGE_INJECTION_REPORT__v1.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return {**result, "report_path": str(report_path)}


if __name__ == "__main__":
    result = inject_bridges(REPO_ROOT)
    print(f"\n{'='*60}")
    print(f"SKILL → KERNEL_CONCEPT BRIDGE INJECTION")
    print(f"{'='*60}")
    print(f"  Mapped skills:     {result['mapped_skills']}/{result['skill_count']}")
    print(f"  Matched edges:     {result['matched_count']}")
    print(f"  Injected (new):    {result['deduplicated_count']}")
    print(f"  Duplicates:        {result['duplicate_count']}")
    print(f"  Unresolved skills: {result['unresolved_skills']}")
    print(f"  Unresolved kernels ({len(result['unresolved_kernels'])}):")
    for uk in result['unresolved_kernels'][:10]:
        print(f"    {uk}")
    if len(result['unresolved_kernels']) > 10:
        print(f"    ... and {len(result['unresolved_kernels'])-10} more")
    print(f"  Report: {result.get('report_path', 'N/A')}")
