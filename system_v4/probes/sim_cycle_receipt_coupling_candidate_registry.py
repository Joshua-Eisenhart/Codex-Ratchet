#!/usr/bin/env python3
"""Rosetta lego registry and coupling-candidate matrix.

This turns the current Carnot/Szilard/I Ching-64 Rosetta receipts into a
machine-readable lego registry.  It records which lego surfaces have classical,
bridge, and nonclassical-adjacent evidence, which tools support them, and which
couplings are allowed next.  It is a controller index, not QIT admission.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "controller_audit"
classification = CLASSIFICATION
divergence_log = (
    "Machine-readable Rosetta lego registry over current Carnot, Szilard, and "
    "I Ching-64 receipts. It indexes lego coverage and next coupling candidates "
    "without promoting any row to QIT/GStack/axis admission."
)

LEGO_IDS = [
    "carnot_cycle",
    "szilard_cycle",
    "iching_64_schedule",
    "dual_stacked_engine",
    "axis_schedule",
    "entropy_family",
    "operator_order",
    "graph_topology",
    "density_matrix",
    "proof_fence",
    "rosetta_correlation",
    "graveyard_variant",
]
PRIMARY_LEGO_IDS = ["rosetta_correlation", "entropy_family", "operator_order"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads exact source receipts and writes registry"},
    "pathlib": {"tried": True, "used": True, "reason": "deterministic receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(stem: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{stem}_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_receipt_path"] = str(path)
    return data


def load_sources() -> dict[str, dict[str, Any]]:
    names = [
        "two_bath_heat_work_reversible_cycle_pair",
        "measure_feedback_erasure_recovery_cycle_pair",
        "six_bit_gray_code_single_flip_cycle_invariant",
        "rosetta_triad_modes",
        "rosetta_triad_entropy_topology_sweep",
        "rosetta_triad_order_graveyard",
    ]
    return {name: load_result(name) for name in names}


def load_bearing_tools(result: dict[str, Any]) -> list[str]:
    return sorted(tool for tool, depth in result.get("tool_integration_depth", {}).items() if depth)


def triad_mode_coverage(triad: dict[str, Any]) -> dict[str, dict[str, bool]]:
    coverage: dict[str, dict[str, bool]] = {}
    for row in triad.get("mode_matrix", []):
        coverage.setdefault(row["engine"], {})[row["mode"]] = bool(row["pass"])
    return coverage


def entropy_by_engine(entropy_topology: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["engine"]: {
            "families": sorted(row.get("entropy_family", {})),
            "support_size": row.get("support_size"),
            "pass": row.get("family_pass"),
        }
        for row in entropy_topology.get("entropy_rows", [])
    }


def topology_by_engine(entropy_topology: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["engine"]: {
            "nodes": row.get("nodes"),
            "edges": row.get("edges"),
            "beta0": row.get("beta0_laplacian"),
            "beta1": row.get("beta1_cycle_rank"),
            "laplacian_spectral_gap": row.get("laplacian_spectral_gap"),
            "pass": row.get("topology_pass"),
        }
        for row in entropy_topology.get("topology_rows", [])
    }


def graveyard_by_engine(order_graveyard: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in order_graveyard.get("variant_rows", []):
        grouped.setdefault(row["engine"], []).append(
            {
                "variant": row["variant"],
                "status": row["status"],
                "expected": row["expected"],
                "survives_order_gate": row["survives_order_gate"],
            }
        )
    return grouped


def registry_rows(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    triad = sources["rosetta_triad_modes"]
    entropy_topology = sources["rosetta_triad_entropy_topology_sweep"]
    order_graveyard = sources["rosetta_triad_order_graveyard"]
    mode_coverage = triad_mode_coverage(triad)
    entropy = entropy_by_engine(entropy_topology)
    topology = topology_by_engine(entropy_topology)
    graveyard = graveyard_by_engine(order_graveyard)
    engine_sources = {
        "carnot": sources["two_bath_heat_work_reversible_cycle_pair"],
        "szilard": sources["measure_feedback_erasure_recovery_cycle_pair"],
        "iching_64": sources["six_bit_gray_code_single_flip_cycle_invariant"],
    }
    rows = []
    for engine, result in engine_sources.items():
        axis_slots = sorted(result.get("axes_candidate_model", {}).get("axes", {}))
        rows.append(
            {
                "lego_id": engine,
                "source_receipt": result["_receipt_path"],
                "source_all_pass": bool(result.get("summary", {}).get("all_pass")),
                "sim_type_coverage": mode_coverage.get(engine, {}),
                "tools_used": load_bearing_tools(result),
                "lego_ids": result.get("lego_ids", []),
                "entropy_families": entropy.get(engine, {}).get("families", []),
                "entropy_support_size": entropy.get(engine, {}).get("support_size"),
                "topology_signature": topology.get(engine, {}),
                "operators": {
                    "count": triad.get("engine_digests", {}).get(engine, {}).get("operator_count"),
                    "readout": triad.get("engine_digests", {}).get(engine, {}).get("entropy_readout"),
                },
                "axis_slots": axis_slots,
                "graveyard_variants": graveyard.get(engine, []),
                "claim_ceiling": "rosetta_lego_candidate_not_qit_admission",
            }
        )
    return rows


def coupling_matrix(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    by_id = {row["lego_id"]: row for row in registry}
    pairs = [("carnot", "szilard"), ("carnot", "iching_64"), ("szilard", "iching_64")]
    for left, right in pairs:
        a = by_id[left]
        b = by_id[right]
        shared_modes = sorted(
            mode
            for mode, ok in a["sim_type_coverage"].items()
            if ok and b["sim_type_coverage"].get(mode)
        )
        shared_tools = sorted(set(a["tools_used"]) & set(b["tools_used"]))
        shared_axis = sorted(set(a["axis_slots"]) & set(b["axis_slots"]))
        shared_entropy = sorted(set(a["entropy_families"]) & set(b["entropy_families"]))
        allowed = (
            len(shared_modes) == 3
            and len(shared_axis) == 7
            and len(shared_entropy) >= 6
            and a["source_all_pass"]
            and b["source_all_pass"]
        )
        blockers = []
        if len(shared_modes) < 3:
            blockers.append("missing full classical/bridge/nonclassical-adjacent overlap")
        if len(shared_axis) < 7:
            blockers.append("missing full Ax0-Ax6 comparison-slot overlap")
        if len(shared_entropy) < 6:
            blockers.append("thin shared entropy-family overlap")
        rows.append(
            {
                "left": left,
                "right": right,
                "allowed_next": allowed,
                "shared_modes": shared_modes,
                "shared_tool_count": len(shared_tools),
                "shared_tools": shared_tools,
                "shared_axis_slots": shared_axis,
                "shared_entropy_families": shared_entropy,
                "coupling_type": "bounded_rosetta_coupling",
                "blocked_or_deferred": blockers,
                "claim_ceiling": "couple_as_candidate_rosetta_surface_only",
            }
        )
    return rows


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "registry_rows": result["registry_rows"],
        "coupling_matrix": result["coupling_matrix"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.CYCLE_RECEIPT_COUPLING_CANDIDATE_REGISTRY_DATA = " + json.dumps(build_visual_payload(result), indent=2, default=str) + ";\n"
    (VIS_DIR / "cycle-receipt-coupling-candidate-registry-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    sources = load_sources()
    registry = registry_rows(sources)
    matrix = coupling_matrix(registry)
    all_pass = all(row["source_all_pass"] for row in registry) and all(row["allowed_next"] for row in matrix)
    result = {
        "name": "cycle_receipt_coupling_candidate_registry",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "controller_audit",
        "allowed_claims": [
            "current Rosetta engine legos have machine-readable registry rows",
            "pairwise coupling candidates are classified by shared modes, tools, axes, entropy, and receipts",
            "allowed couplings remain candidate Rosetta surfaces only",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": ["no QIT runtime admission", "no GStack nesting receipt", "no full axis admission"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {name: data["_receipt_path"] for name, data in sources.items()},
        "registry_rows": registry,
        "coupling_matrix": matrix,
        "summary": {
            "all_pass": bool(all_pass),
            "registry_row_count": len(registry),
            "coupling_candidate_count": len(matrix),
            "allowed_coupling_count": sum(row["allowed_next"] for row in matrix),
            "blocked_coupling_count": sum(not row["allowed_next"] for row in matrix),
            "visual_payload": "visualizer/cycle-receipt-coupling-candidate-registry-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "cycle_receipt_coupling_candidate_registry_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
