#!/usr/bin/env python3
"""Scope terrain/engine pseudo-basins and the E=8/E=16 tensor substrate.

Workstream 7 receipt. This is a scoping/audit scout, not a tensor-network
physics run. It encodes the terrain micro-pseudo-basin / engine pseudo-basin
architecture and prevents W3 finite-channel schedule counts from being reused
as PEPS/PEPS3D, full tensor-network, or multi-qubit Lindblad evidence.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope_probe_results.json"

NAME = "two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope"
CLAIM_CEILING = (
    "Formal scout only: scopes terrain micro-pseudo-basins, engine pseudo-basins, "
    "and the proposed E=8/E=16 terrain-stage/engine-stage tensor substrate. It does not run "
    "MPS, PEPS, PEPS3D, full tensor-network, or multi-qubit Lindblad dynamics; "
    "does not prove a real attractor basin; and does not admit Axis0, engine, "
    "physics, Holodeck, Clifford, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor feature matrix for the E=8/E=16 terrain-stage/engine-stage substrate mapping",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph witness for engine-site and paired-engine substrate connectivity",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scale-separation satisfiability checks for E, L, R, q, and N",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive formal receipt serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
CORRECTION = REPO / "system_v5" / "docs" / "CONSTRAINT_MANIFOLD_ORDERING_STATUS_CORRECTION_20260520.md"
HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"
W3_SOURCE = SCOUT_ROOT / "sim_constraint_manifold_terrain_lindblad_composition_bridge_probe.py"
W3_RESULT = RESULT_DIR / "constraint_manifold_terrain_lindblad_composition_bridge_probe_results.json"
LATE_GROK_RESULT = RESULT_DIR / "two_root_constraint_grok_115_124_tooling_violation_handoff_ingest_probe_results.json"

LEFT_ENGINE_ORDER = ["Funnel", "Vortex", "Pit", "Hill"]
RIGHT_ENGINE_ORDER = ["Cannon", "Spiral", "Source", "Citadel"]
TOPOLOGY_BY_TERRAIN = {
    "Funnel": "Se",
    "Cannon": "Se",
    "Vortex": "Ne",
    "Spiral": "Ne",
    "Pit": "Ni",
    "Source": "Ni",
    "Hill": "Si",
    "Citadel": "Si",
}
TYPE_BY_ENGINE = {"left_type1_engine": 1, "right_type2_engine": 2}
LOOPS = ["inner_loop", "outer_loop"]
TOPOLOGY_INDEX = {"Se": 0, "Ne": 1, "Ni": 2, "Si": 3}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def jsonable(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def source_hashes() -> dict[str, Any]:
    paths = {
        "active_plan": PLAN,
        "ordering_correction": CORRECTION,
        "active_handoff": HANDOFF,
        "w3_source": W3_SOURCE,
        "w3_result": W3_RESULT,
        "late_grok_ingest_result": LATE_GROK_RESULT,
    }
    return {
        key: {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)}
        for key, path in paths.items()
    }


def line_hits(path: pathlib.Path, needles: list[str], limit: int = 8) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    lowered = [needle.lower() for needle in needles]
    for lineno, line in enumerate(read_text(path).splitlines(), start=1):
        low = line.lower()
        if any(needle in low for needle in lowered):
            hits.append({"path": rel(path), "line": lineno, "text": line.strip()[:280]})
            if len(hits) >= limit:
                break
    return hits


def prerequisite_report() -> dict[str, Any]:
    w3 = read_json(W3_RESULT)
    late = read_json(LATE_GROK_RESULT)
    w3_text = read_text(W3_SOURCE)
    no_tensor_network_imports = all(token not in w3_text for token in ["import quimb", "PEPS", "PEPS3D", "MPS"])
    w3_summary = w3.get("summary", {})
    late_summary = late.get("summary", {})
    return {
        "pass": (
            W3_RESULT.exists()
            and LATE_GROK_RESULT.exists()
            and w3.get("all_pass") is True
            and w3.get("promotion_allowed") is False
            and no_tensor_network_imports
            and late_summary.get("multi_qubit_lindblad_evidence_allowed") is False
            and late_summary.get("peps_peps3d_evidence_allowed") is False
            and late_summary.get("pytorch_tensor_network_scale_evidence_allowed") is False
        ),
        "w3_result": {
            "path": rel(W3_RESULT),
            "all_pass": w3.get("all_pass"),
            "promotion_allowed": w3.get("promotion_allowed"),
            "claim_ceiling": w3.get("claim_ceiling"),
            "active_schedule_scales": w3_summary.get("active_schedule_scales"),
            "algebra_level_status": w3_summary.get("algebra_level_status"),
            "w3_source_has_no_tensor_network_imports": no_tensor_network_imports,
        },
        "late_grok_boundary": {
            "path": rel(LATE_GROK_RESULT),
            "all_pass": late.get("all_pass"),
            "claim_ceiling": late.get("claim_ceiling"),
            "multi_qubit_lindblad_evidence_allowed": late_summary.get("multi_qubit_lindblad_evidence_allowed"),
            "peps_peps3d_evidence_allowed": late_summary.get("peps_peps3d_evidence_allowed"),
            "pytorch_tensor_network_scale_evidence_allowed": late_summary.get("pytorch_tensor_network_scale_evidence_allowed"),
        },
    }


def stage_slots() -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    engines = [
        ("left_type1_engine", LEFT_ENGINE_ORDER),
        ("right_type2_engine", RIGHT_ENGINE_ORDER),
    ]
    site_id = 0
    for engine_idx, (engine_name, order) in enumerate(engines):
        for loop_idx, loop in enumerate(LOOPS):
            for stage_idx, terrain in enumerate(order):
                topology = TOPOLOGY_BY_TERRAIN[terrain]
                slots.append(
                    {
                        "site_id": f"E{site_id:02d}",
                        "engine": engine_name,
                        "engine_idx": engine_idx,
                        "loop": loop,
                        "loop_idx": loop_idx,
                        "stage_idx": stage_idx,
                        "terrain": terrain,
                        "topology": topology,
                        "topology_idx": TOPOLOGY_INDEX[topology],
                        "type_tag": TYPE_BY_ENGINE[engine_name],
                    }
                )
                site_id += 1
    return slots


def substrate_graph_report(slots: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    node_map = {slot["site_id"]: graph.add_node(slot) for slot in slots}
    sequential_edges: list[tuple[str, str, str]] = []
    for engine_name in sorted({slot["engine"] for slot in slots}):
        engine_slots = [slot for slot in slots if slot["engine"] == engine_name]
        engine_slots.sort(key=lambda row: (row["loop_idx"], row["stage_idx"]))
        for left, right in zip(engine_slots, engine_slots[1:]):
            graph.add_edge(node_map[left["site_id"]], node_map[right["site_id"]], "engine_schedule_order")
            sequential_edges.append((left["site_id"], right["site_id"], "engine_schedule_order"))
    paired_edges: list[tuple[str, str, str]] = []
    left_slots = [slot for slot in slots if slot["engine"] == "left_type1_engine"]
    right_slots = [slot for slot in slots if slot["engine"] == "right_type2_engine"]
    for left, right in zip(left_slots, right_slots):
        graph.add_edge(node_map[left["site_id"]], node_map[right["site_id"]], "paired_engine_alignment")
        paired_edges.append((left["site_id"], right["site_id"], "paired_engine_alignment"))

    features = torch.tensor(
        [
            [
                float(slot["engine_idx"]),
                float(slot["loop_idx"]),
                float(slot["stage_idx"]),
                float(slot["topology_idx"]),
                float(slot["type_tag"]),
                1.0,
            ]
            for slot in slots
        ],
        dtype=torch.float64,
    )
    per_engine_counts = {
        engine: int(sum(1 for slot in slots if slot["engine"] == engine))
        for engine in sorted({slot["engine"] for slot in slots})
    }
    components = rx.connected_components(graph)
    return {
        "pass": (
            graph.num_nodes() == 16
            and all(count == 8 for count in per_engine_counts.values())
            and len(components) == 1
            and list(features.shape) == [16, 6]
        ),
        "mapping": "one terrain-stage or engine-stage placement -> one qubit/tensor site",
        "one_engine_site_count_E": 8,
        "paired_engine_site_count_E_pair": 16,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "connected_component_count": len(components),
        "per_engine_counts": per_engine_counts,
        "feature_columns": ["engine_idx", "loop_idx", "stage_idx", "topology_idx", "type_tag", "site_present"],
        "feature_matrix_shape": list(features.shape),
        "feature_column_sums": jsonable(torch.sum(features, dim=0)),
        "sequential_edges": sequential_edges,
        "paired_edges": paired_edges,
        "first_four_slots": slots[:4],
    }


def scale_separation_report() -> dict[str, Any]:
    e_engine = z3.Int("E_engine_stage_sites")
    e_pair = z3.Int("E_paired_engine_stage_sites")
    schedule_repeats = z3.Int("R_schedule_repeats")
    tensor_sites = z3.Int("L_tensor_network_sites")
    pauli_qubits = z3.Int("q_pauli_substrate_qubits")
    selected_ops = z3.Int("N_selected_operators")

    base = [
        e_engine == 8,
        e_pair == 2 * e_engine,
        z3.Or(schedule_repeats == 8, schedule_repeats == 16, schedule_repeats == 64),
        tensor_sites >= 0,
        pauli_qubits >= 0,
        selected_ops >= 0,
    ]
    valid = z3.Solver()
    valid.add(*base)
    valid_status = valid.check()
    valid_model = valid.model() if valid_status == z3.sat else None

    not_same_as_tensor_sites = z3.Solver()
    not_same_as_tensor_sites.add(*base, tensor_sites == 0, schedule_repeats == 64)
    independent_status = not_same_as_tensor_sites.check()
    independent_model = not_same_as_tensor_sites.model() if independent_status == z3.sat else None

    impossible_pair_mismatch = z3.Solver()
    impossible_pair_mismatch.add(*base, e_pair != 16)
    mismatch_status = impossible_pair_mismatch.check()

    return {
        "pass": valid_status == z3.sat and independent_status == z3.sat and mismatch_status == z3.unsat,
        "variables": {
            "E": "engine-stage site count; E=8 for one engine in this substrate hypothesis",
            "E_pair": "paired-engine stage-site count; E_pair=16",
            "R": "schedule-repeat count in finite-channel W3 receipts; not a tensor-site count",
            "L": "tensor-network site count; requires actual MPS/PEPS/PEPS3D or equivalent representation",
            "q": "Pauli substrate qubit count; operator-pool scale",
            "N": "selected graph/operator count",
        },
        "valid_assignment": str(valid_model),
        "independence_witness_assignment": str(independent_model),
        "pair_mismatch_unsat": mismatch_status == z3.unsat,
    }


def claim_boundary_report() -> dict[str, Any]:
    plan_text = read_text(PLAN)
    correction_text = read_text(CORRECTION)
    handoff_text = read_text(HANDOFF)
    required_phrases = [
        "Terrain micro-pseudo-basin",
        "Engine pseudo-basin",
        "Constraint ratchet",
        "E=8",
        "E=16",
        "W3 finite-channel schedule composition is not PEPS",
    ]
    combined = "\n".join([plan_text, correction_text, handoff_text])
    rows = {phrase: (phrase.lower() in combined.lower()) for phrase in required_phrases}
    return {
        "pass": all(rows.values()),
        "phrase_checks": rows,
        "plan_hits": line_hits(PLAN, ["Terrain micro-pseudo-basin", "Engine pseudo-basin", "E=8", "R=8/16/64"], limit=10),
        "correction_hits": line_hits(CORRECTION, ["Pseudo-basin", "Natural tensor-substrate", "E=8", "W3 finite-channel"], limit=10),
        "handoff_hits": line_hits(HANDOFF, ["W7", "E=8", "pseudo-basin", "finite-channel"], limit=10),
    }


def future_sim_target_report() -> dict[str, Any]:
    target = {
        "first_substrate": ["E=8 one-engine stage-site substrate", "E=16 paired-engine stage-site substrate"],
        "allowed_implementations": [
            "torch-native vectorized-density tensor network",
            "quantum trajectories over E=8/E=16 sites with validated channel averages",
            "MPS Lindblad when sites are represented as sites, not schedule repeats",
            "PEPS/PEPS3D only after the implementation actually constructs those tensor-network geometries",
        ],
        "required_checks": [
            "trace preservation",
            "positivity and complete positivity or trajectory-equivalent validation",
            "fixed-state/fixed-observable/generated-channel evidence on the named substrate",
            "terrain-law ablation",
            "schedule-order ablation",
            "identity and commutative collapse controls",
            "matched fake bridge control",
        ],
    }
    return {
        "pass": len(target["first_substrate"]) == 2 and len(target["allowed_implementations"]) == 4 and len(target["required_checks"]) >= 7,
        "target": target,
    }


def main() -> dict[str, Any]:
    started = time.time()
    prereq = prerequisite_report()
    slots = stage_slots()
    substrate = substrate_graph_report(slots)
    scale = scale_separation_report()
    boundary_docs = claim_boundary_report()
    future_target = future_sim_target_report()

    positive = {
        "prerequisite_receipts_loaded_and_scoped": prereq,
        "terrain_and_engine_definitions_encoded": {
            "pass": True,
            "terrain_definition": "current operational scoping hypothesis: local/substage pseudo-attractor density-law component embedded on Weyl sheets",
            "engine_definition": "current operational scoping hypothesis: composite pseudo-attractor schedule over ordered terrain-stage placements",
            "constraint_ratchet_definition": "receipt/admission process across constraint layers, not a standalone physics flow",
            "missing_source_model_receipts": [
                "explicit eight-terrain generator receipt",
                "sixteen-placement Weyl-sheet/operator-layer receipt",
                "operator-layer receipt separate from topology/readout labels",
            ],
        },
        "stage_to_site_tensor_substrate_mapping": substrate,
        "scale_labels_are_separated": scale,
        "docs_contain_required_boundary_language": boundary_docs,
        "future_valid_sim_target_is_named": future_target,
    }

    graveyard_companions = {
        "w3_as_peps_or_full_tensor_network_claim_killed": {
            "pass": prereq["pass"],
            "reason": "W3 source has no PEPS/PEPS3D/MPS tensor-network implementation and W3 claim ceiling is finite terrain-channel composition only.",
            "claim_status": "blocked_from_promotion",
        },
        "schedule_repeats_equal_tensor_sites_claim_killed": {
            "pass": scale["pass"],
            "reason": "Z3 keeps R schedule repeats, E stage sites, and L tensor-network sites as separate variables.",
            "claim_status": "blocked_from_promotion",
        },
        "pseudo_basin_as_real_attractor_claim_killed": {
            "pass": True,
            "reason": "Pseudo-basin wording is architectural; real attractor-basin claims require fixed-state/fixed-observable/generated-channel evidence on the named substrate.",
            "claim_status": "blocked_until_substrate_evidence_exists",
        },
        "e8_e16_as_canon_claim_killed": {
            "pass": True,
            "reason": "E=8/E=16 is a natural simulation substrate hypothesis, not a canon layer count or final manifold theorem.",
            "claim_status": "candidate_substrate_only",
        },
        "grok_115_124_as_multiqubit_tensor_evidence_killed": {
            "pass": read_json(LATE_GROK_RESULT).get("summary", {}).get("peps_peps3d_evidence_allowed") is False,
            "reason": "Late grok_sim handoff ingest explicitly blocks multi-qubit Lindblad, PEPS/PEPS3D, and PyTorch tensor-network scale evidence.",
            "claim_status": "sidequest_context_only",
        },
    }

    boundary = {
        "promotion_allowed": {"pass": True, "value": PROMOTION_ALLOWED},
        "goal_complete_allowed": {"pass": True, "value": False},
        "w7_does_not_complete_goal_by_itself": {
            "pass": True,
            "reason": "W7 scopes the substrate but does not itself resolve broad NumPy/readiness/tool-role blockers or produce final synthesis. Current closeout is owned by the later D86 final synthesis.",
        },
        "full_tensor_network_evidence_allowed": {"pass": True, "value": False},
        "real_attractor_basin_claim_allowed": {"pass": True, "value": False},
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "math_object": "terrain/engine pseudo-basin tensor-substrate scope",
        "source_hashes": source_hashes(),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "Actual torch-native MPS/PEPS/PEPS3D or trajectory/vectorized-density implementation for E=8/E=16 remains open.",
            "Whether engine pseudo-basins become real attractor basins remains open until substrate-level fixed-state/fixed-observable/generated-channel evidence exists.",
            "Use the later D86 final synthesis for current tooling closeout; W7 remains scope-only evidence.",
        ],
        "why_not_v4_probes": "This is a v5 formal-scout scoping receipt over the W7 terrain/engine substrate correction, not a v4 proposal or canonical sim.",
        "summary": {
            "all_pass": all_pass,
            "completion_status": "terrain_engine_pseudo_basin_tensor_substrate_scoped",
            "claim_ceiling": "w7_scope_only_no_tensor_network_or_real_basin_proof",
            "one_engine_stage_site_count_E": 8,
            "paired_engine_stage_site_count_E": 16,
            "w3_finite_channel_only": True,
            "full_tensor_network_lindblad_evidence": False,
            "real_attractor_basin_claim_allowed": False,
            "goal_complete": False,
            "next_required_workstreams": [
                "rerun validation/gate cadence",
                "final synthesis only after W7 and broad blocker/readiness/tool-role scoping",
            ],
        },
        "all_pass": all_pass,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    receipt = main()
    print(
        json.dumps(
            {
                "all_pass": receipt["all_pass"],
                "completion_status": receipt["summary"]["completion_status"],
                "one_engine_stage_site_count_E": receipt["summary"]["one_engine_stage_site_count_E"],
                "paired_engine_stage_site_count_E": receipt["summary"]["paired_engine_stage_site_count_E"],
                "full_tensor_network_lindblad_evidence": receipt["summary"]["full_tensor_network_lindblad_evidence"],
                "goal_complete": receipt["summary"]["goal_complete"],
                "out_path": str(OUT_PATH.relative_to(REPO)),
            },
            indent=2,
            sort_keys=True,
        )
    )
