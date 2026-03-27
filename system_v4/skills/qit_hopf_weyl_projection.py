#!/usr/bin/env python3
"""
QIT Hopf–Weyl Projection Sidecar (Bounded Read-Only)
=====================================================
Derives bounded sidecar summaries over admitted torus/chirality owner
structure using TopoNetX candidate cell-complex views and clifford
Cl(3,0) candidate multivector mappings.

This is a BOUNDED READ-ONLY SIDECAR:
  - Reads owner truth: qit_engine_graph_v1.json
  - Reads engine runtime geometry: hopf_manifold.py constants
  - Outputs projection reports to a2_state/audit_logs/
  - Never writes to owner truth
  - Never claims promotion-ready status

Projection surfaces:
  1. TopoNetX candidate cell-complex view — models each admitted torus carrier
     as a provisional 2-cell with stage-boundary 1-cells
  2. Stage-Torus carrier groupings — which stages attach to which admitted torus
  3. Chirality coupling candidate mapping — Cl(3,0) pseudoscalar e₁₂₃ sidecar view
  4. Weyl-readiness annotation — derived branch/coupling notes, not live owner semantics

Usage:
    python3 system_v4/skills/qit_hopf_weyl_projection.py
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_JSON = REPO_ROOT / "system_v4" / "a2_state" / "graphs" / "qit_engine_graph_v1.json"
AUDIT_DIR = REPO_ROOT / "system_v4" / "a2_state" / "audit_logs"
OUTPUT_JSON = AUDIT_DIR / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json"
OUTPUT_MD = AUDIT_DIR / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.md"

# Torus latitudes from hopf_manifold.py (canonical constants)
TORUS_INNER_ETA = math.pi / 8
TORUS_CLIFFORD_ETA = math.pi / 4
TORUS_OUTER_ETA = 3 * math.pi / 8

TORUS_RADII = {
    "inner": (math.cos(TORUS_INNER_ETA), math.sin(TORUS_INNER_ETA)),
    "clifford": (math.cos(TORUS_CLIFFORD_ETA), math.sin(TORUS_CLIFFORD_ETA)),
    "outer": (math.cos(TORUS_OUTER_ETA), math.sin(TORUS_OUTER_ETA)),
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain(paths: list[Path] | None = None) -> list[str]:
    cmd = ["git", "status", "--short"]
    if paths:
        cmd.append("--")
        cmd.extend(str(path) for path in paths)
    try:
        output = subprocess.check_output(
            cmd,
            cwd=str(REPO_ROOT),
            text=True,
        )
    except Exception:
        return []
    return [line.rstrip() for line in output.splitlines() if line.strip()]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. TORUS CELL COMPLEX PROJECTION (TopoNetX)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _build_torus_cell_complex(
    torus_nodes: dict[str, dict],
    nesting_edges: list[dict],
    stage_torus_edges: list[dict],
    stage_nodes: dict[str, dict],
) -> dict[str, Any]:
    """Build a TopoNetX candidate CellComplex over admitted torus/stage structure."""
    try:
        import toponetx as tnx
    except ImportError:
        return {"available": False, "error": "TopoNetX not installed"}

    cc = tnx.CellComplex()

    # 0-cells: stage nodes that sit on tori
    stage_ids_on_tori = set()
    torus_to_stages: dict[str, list[str]] = defaultdict(list)

    for e in stage_torus_edges:
        stage_pid = e["source_public_id"]
        torus_pid = e["target_public_id"]
        torus_label = torus_pid.split("::")[-1]  # inner, clifford, outer
        stage_label = stage_pid.split("::")[-1]
        stage_ids_on_tori.add(stage_label)
        torus_to_stages[torus_label].append(stage_label)
        cc.add_node(stage_label)

    # 1-cells: stage sequence edges that form loops within each engine type
    # Group stages by engine type to find the 8-stage cycles
    type1_stages = sorted([s for s in stage_ids_on_tori if "type1" in s])
    type2_stages = sorted([s for s in stage_ids_on_tori if "type2" in s])

    # Add sequence edges forming the 8-stage loop per engine type
    for cycle in [type1_stages, type2_stages]:
        for i in range(len(cycle)):
            cc.add_cell([cycle[i], cycle[(i + 1) % len(cycle)]], rank=1)

    # 2-cells: each torus becomes a 2-cell bounded by stages on that torus
    torus_2cells = {}
    for torus_label, stages in torus_to_stages.items():
        unique_stages = sorted(set(stages))
        if len(unique_stages) >= 3:
            try:
                # Need to ensure all boundary 1-cells exist
                for i in range(len(unique_stages)):
                    s1, s2 = unique_stages[i], unique_stages[(i + 1) % len(unique_stages)]
                    cc.add_cell([s1, s2], rank=1)
                cc.add_cell(unique_stages, rank=2)
                torus_2cells[torus_label] = {
                    "stages": unique_stages,
                    "stage_count": len(unique_stages),
                }
            except Exception as ex:
                torus_2cells[torus_label] = {
                    "stages": unique_stages,
                    "stage_count": len(unique_stages),
                    "cell_error": str(ex),
                }

    return {
        "available": True,
        "shape": [int(s) for s in cc.shape],
        "stage_0cells": sorted(stage_ids_on_tori),
        "stage_0cell_count": len(stage_ids_on_tori),
        "torus_2cells": torus_2cells,
        "engine_type1_cycle": type1_stages,
        "engine_type2_cycle": type2_stages,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. STAGE-TORUS CYCLE GROUPINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _build_stage_torus_groupings(
    stage_torus_edges: list[dict],
    stage_nodes: dict[str, dict],
) -> dict[str, Any]:
    """Group stages by their torus membership and loop type."""
    stage_to_tori: dict[str, list[str]] = defaultdict(list)
    torus_to_stages: dict[str, list[str]] = defaultdict(list)

    for e in stage_torus_edges:
        stage_label = e["source_public_id"].split("::")[-1]
        torus_label = e["target_public_id"].split("::")[-1]
        if torus_label not in stage_to_tori[stage_label]:
            stage_to_tori[stage_label].append(torus_label)
        if stage_label not in torus_to_stages[torus_label]:
            torus_to_stages[torus_label].append(stage_label)

    # Classify: fiber stages touch inner+clifford, base stages touch outer+clifford
    fiber_stages = [s for s, tori in stage_to_tori.items() if "inner" in tori]
    base_stages = [s for s, tori in stage_to_tori.items() if "outer" in tori]
    clifford_only = [s for s, tori in stage_to_tori.items()
                     if "clifford" in tori and "inner" not in tori and "outer" not in tori]

    return {
        "stage_to_tori": dict(stage_to_tori),
        "torus_to_stages": {k: sorted(v) for k, v in torus_to_stages.items()},
        "fiber_stages": sorted(fiber_stages),
        "base_stages": sorted(base_stages),
        "fiber_stage_count": len(fiber_stages),
        "base_stage_count": len(base_stages),
        "all_stages_touch_clifford": all("clifford" in tori for tori in stage_to_tori.values()),
        "clifford_is_universal_bridge": "clifford" in torus_to_stages and len(torus_to_stages["clifford"]) == len(stage_to_tori),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. CHIRALITY COUPLING PROJECTION (clifford Cl(3,0))
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _build_chirality_projection(
    engine_nodes: dict[str, dict],
    chirality_edges: list[dict],
) -> dict[str, Any]:
    """Map the admitted chirality edge into a bounded Cl(3,0) sidecar representation."""
    try:
        from clifford import Cl
        layout, blades = Cl(3)
        e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
        e123 = blades["e123"]  # pseudoscalar

        # Sidecar candidate mapping: chirality coupling is represented by the
        # pseudoscalar e123 in this Cl(3,0) view.
        coupling_mv = e123

        # Engine-family distinction maps to the two orientations in this sidecar.
        type1_orientation = +1.0 * e123  # positive pseudoscalar
        type2_orientation = -1.0 * e123  # negative (conjugate)

        # The coupling edge connects them
        coupling_product = type1_orientation * type2_orientation

        projection = {
            "available": True,
            "algebra": "Cl(3,0)",
            "pseudoscalar_blade": "e123",
            "type1_deductive": {
                "orientation": "+e123",
                "projected_branch_label": "left_like",
                "conventional_rule_annotation": "psi_L -> U·psi_L",
                "non_owner_phase_note": "positive phase convention in sidecar view",
                "operator_dominance": "Fe/Ti on base, Te/Fi on fiber",
            },
            "type2_inductive": {
                "orientation": "-e123",
                "projected_branch_label": "right_like",
                "conventional_rule_annotation": "psi_R -> U*·psi_R",
                "non_owner_phase_note": "negative phase convention in sidecar view",
                "operator_dominance": "Te/Fi on base, Fe/Ti on fiber",
            },
            "coupling_product_grade": list(coupling_product.grades())[0] if coupling_product.grades() else 0,
            "coupling_is_scalar": bool(coupling_product.grades() == {0}),
            "physical_meaning": (
                "This sidecar maps the admitted chirality-coupling edge to a Cl(3,0) "
                "pseudoscalar candidate. In this representation the projected product "
                "is scalar, which is useful as a bounded complementary-orientation annotation."
            ),
        }
    except ImportError:
        projection = {
            "available": False,
            "error": "clifford not installed",
            "fallback_summary": {
                "type1_deductive": "Fe/Ti dominant on base, ψ_L → U·ψ_L",
                "type2_inductive": "Te/Fi dominant on base, ψ_R → U*·ψ_R",
                "coupling": "complementary_dominance (flat owner edge, sidecar annotation only)",
            },
        }

    # Always include the owner-graph facts regardless of clifford availability
    projection["owner_graph_chirality_edges"] = len(chirality_edges)
    projection["owner_graph_engine_nodes"] = {
        pid.split("::")[-1]: {
            "description": n.get("description", ""),
            "public_id": pid,
        }
        for pid, n in engine_nodes.items()
    }

    return projection


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. TORUS GEOMETRY SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _build_torus_geometry() -> dict[str, Any]:
    """Summarize the physical torus geometry from hopf_manifold constants."""
    torus_data = {}
    for name, (r_major, r_minor) in TORUS_RADII.items():
        area = r_major * r_minor
        flatness = 1.0 - abs(r_major - r_minor) / max(r_major, r_minor)
        torus_data[name] = {
            "R_major": round(r_major, 6),
            "R_minor": round(r_minor, 6),
            "area": round(area, 6),
            "flatness": round(flatness, 6),
            "loop_assignment": "fiber" if name == "inner" else ("base" if name == "outer" else "bridge"),
        }

    eta_values = {
        "inner": TORUS_INNER_ETA,
        "clifford": TORUS_CLIFFORD_ETA,
        "outer": TORUS_OUTER_ETA,
    }

    return {
        "tori": torus_data,
        "eta_values": {k: round(v, 6) for k, v in eta_values.items()},
        "nesting_order": ["inner", "clifford", "outer"],
        "clifford_is_flat": abs(TORUS_RADII["clifford"][0] - TORUS_RADII["clifford"][1]) < 1e-10,
        "transport_distance_inner_to_outer": round(
            min(abs(TORUS_OUTER_ETA - TORUS_INNER_ETA) / (math.pi / 4), 1.0), 6
        ),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. NEGATIVE EVIDENCE RELEVANT TO TORUS/CHIRALITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _relevant_negative_evidence(nodes: dict, edges: list) -> dict[str, Any]:
    """Extract negative witnesses that target torus or chirality structures."""
    relevant = []
    for nid, n in nodes.items():
        if n.get("node_type") != "NEG_WITNESS":
            continue
        target = n.get("target_structure", "")
        if target in ("TORUS", "CHIRALITY"):
            # Find the NEGATIVE_PROVES edges from this witness
            proves_targets = []
            for e in edges:
                if e["relation"] == "NEGATIVE_PROVES" and e["source_public_id"] == n["public_id"]:
                    proves_targets.append(e["target_public_id"])

            relevant.append({
                "witness_id": n["public_id"],
                "label": n.get("label", ""),
                "description": n.get("description", ""),
                "target_structure": target,
                "owner_edge_emission": n.get("owner_edge_emission", "unknown"),
                "proves_label": n.get("proves_label", ""),
                "proves_targets": proves_targets,
            })

    return {
        "torus_witnesses": [w for w in relevant if w["target_structure"] == "TORUS"],
        "chirality_witnesses": [w for w in relevant if w["target_structure"] == "CHIRALITY"],
        "total": len(relevant),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def build_projection() -> dict[str, Any]:
    """Build the complete Hopf/Weyl projection from the owner graph."""
    script_path = Path(__file__).resolve()
    g = _load_json(GRAPH_JSON)
    nodes = g.get("nodes", {})
    edges = g.get("edges", [])

    # Extract relevant structures
    torus_nodes = {n["public_id"]: n for n in nodes.values() if n.get("node_type") == "TORUS"}
    engine_nodes = {n["public_id"]: n for n in nodes.values() if n.get("node_type") == "ENGINE"}
    stage_nodes = {n["public_id"]: n for n in nodes.values() if n.get("node_type") == "MACRO_STAGE"}

    nesting_edges = [e for e in edges if e["relation"] == "TORUS_NESTING"]
    stage_torus_edges = [e for e in edges if e["relation"] == "STAGE_ON_TORUS"]
    chirality_edges = [e for e in edges if e["relation"] == "CHIRALITY_COUPLING"]

    # Build projections
    cell_complex = _build_torus_cell_complex(torus_nodes, nesting_edges, stage_torus_edges, stage_nodes)
    cycle_groupings = _build_stage_torus_groupings(stage_torus_edges, stage_nodes)
    chirality = _build_chirality_projection(engine_nodes, chirality_edges)
    torus_geometry = _build_torus_geometry()
    neg_evidence = _relevant_negative_evidence(nodes, edges)

    return {
        "schema": "QIT_HOPF_WEYL_PROJECTION_v1",
        "generated_utc": _utc_iso(),
        "status": "present_bounded_projection",
        "source": str(GRAPH_JSON),
        "source_content_hash": g.get("content_hash", "unknown"),
        "owner_snapshot": {
            "qit_graph_json": str(GRAPH_JSON),
            "qit_graph_schema": g.get("schema", ""),
            "qit_graph_content_hash": g.get("content_hash", "unknown"),
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "report_surface": {
            "surface_class": "tracked_current_workspace_report",
            "represents": (
                "current workspace Hopf/Weyl sidecar state at generation time; may differ from the last "
                "committed snapshot until tracked CURRENT artifacts are committed"
            ),
            "tracked_report_files": [
                str(OUTPUT_JSON),
                str(OUTPUT_MD),
            ],
            "tracked_report_files_dirty_before_generation": _git_status_porcelain([OUTPUT_JSON, OUTPUT_MD]),
            "script_path": str(script_path),
            "script_sha256": _sha256_path(script_path),
            "git_sha": _git_sha(),
        },

        # ── Sidecar boundary metadata ──
        "sidecar_boundary": {
            "mode": "bounded_read_only",
            "do_not_promote": True,
            "audit_only": True,
            "nonoperative": True,
            "reads_from": [str(GRAPH_JSON)],
            "writes_to": [str(OUTPUT_JSON), str(OUTPUT_MD)],
            "never_writes_to": [str(GRAPH_JSON)],
            "purpose": (
                "Derive bounded carrier/annotation summaries over admitted torus and chirality "
                "owner structure. This is sidecar context for future promotion decisions, not proof."
            ),
        },

        "hopf_stage_projection": {
            "stage_count": len(stage_nodes),
            "fiber_stage_count": cycle_groupings["fiber_stage_count"],
            "base_stage_count": cycle_groupings["base_stage_count"],
            "shared_clifford_stage_count": len(cycle_groupings["torus_to_stages"].get("clifford", [])),
            "torus_carriers": [
                {
                    "torus_public_id": pid,
                    "label": node.get("label", ""),
                    "nesting_rank": node.get("nesting_rank"),
                    "description": node.get("description", ""),
                }
                for pid, node in sorted(torus_nodes.items(), key=lambda item: item[1].get("nesting_rank", 999))
            ],
        },
        "weyl_projection_readiness": {
            "projection_status": "engine_pair_only_derived",
            "weyl_branch_nodes_present": False,
            "chirality_coupling_edge_present": len(chirality_edges) > 0,
            "engine_pair_public_ids": sorted(engine_nodes.keys()),
            "missing_owner_anchors": ["WEYL_BRANCH"],
        },

        # ── Projections ──
        "torus_cell_complex": cell_complex,
        "stage_torus_groupings": cycle_groupings,
        "chirality_coupling": chirality,
        "torus_geometry": torus_geometry,
        "relevant_negative_evidence": neg_evidence,

        # ── Owner graph counts used ──
        "owner_summary": {
            "torus_nodes": len(torus_nodes),
            "engine_nodes": len(engine_nodes),
            "stage_nodes": len(stage_nodes),
            "nesting_edges": len(nesting_edges),
            "stage_torus_edges": len(stage_torus_edges),
            "chirality_edges": len(chirality_edges),
        },
    }


def _render_markdown(proj: dict[str, Any]) -> str:
    """Render the projection as a human-readable markdown report."""
    boundary = proj["sidecar_boundary"]
    surface = proj["report_surface"]
    cc = proj["torus_cell_complex"]
    groups = proj["stage_torus_groupings"]
    chiral = proj["chirality_coupling"]
    geom = proj["torus_geometry"]
    neg = proj["relevant_negative_evidence"]
    owner = proj["owner_summary"]

    lines = [
        "# QIT Hopf–Weyl Projection (Bounded Read-Only Sidecar)",
        "",
        f"- generated_utc: `{proj['generated_utc']}`",
        f"- source_content_hash: `{proj['source_content_hash']}`",
        f"- do_not_promote: `{boundary['do_not_promote']}`",
        f"- mode: `{boundary['mode']}`",
        "",
        "## Report Surface",
        f"- surface_class: `{surface['surface_class']}`",
        f"- represents: `{surface['represents']}`",
        f"- git_sha: `{surface['git_sha']}`",
        "",
        "## Owner Graph Inputs",
        f"- Torus nodes: `{owner['torus_nodes']}`",
        f"- Engine nodes: `{owner['engine_nodes']}`",
        f"- Macro-stage nodes: `{owner['stage_nodes']}`",
        f"- TORUS_NESTING edges: `{owner['nesting_edges']}`",
        f"- STAGE_ON_TORUS edges: `{owner['stage_torus_edges']}`",
        f"- CHIRALITY_COUPLING edges: `{owner['chirality_edges']}`",
        "",
        "## 1. TopoNetX Candidate Cell-Complex View",
        f"- available: `{cc.get('available', False)}`",
    ]

    if cc.get("available"):
        lines.append(f"- shape: `{cc['shape']}`  (0-cells, 1-cells, provisional 2-cells)")
        lines.append(f"- stage 0-cells: `{cc['stage_0cell_count']}`")
        for torus, info in cc.get("torus_2cells", {}).items():
            lines.append(f"- torus `{torus}`: {info['stage_count']} stages in provisional sidecar boundary")
    else:
        lines.append(f"- error: `{cc.get('error', 'unknown')}`")

    lines.extend([
        "",
        "## 2. Stage–Torus Cycle Groupings",
        f"- fiber stages (inner+clifford): `{groups['fiber_stage_count']}`",
        f"- base stages (outer+clifford): `{groups['base_stage_count']}`",
        f"- all admitted stages attach to Clifford: `{groups['all_stages_touch_clifford']}`",
        f"- Clifford is universal bridge in current owner scaffold: `{groups['clifford_is_universal_bridge']}`",
    ])

    for torus, stages in groups.get("torus_to_stages", {}).items():
        lines.append(f"- `{torus}`: {len(stages)} stages")

    lines.extend([
        "",
        "## 3. Chirality Coupling Candidate Mapping (Cl(3,0))",
        f"- available: `{chiral.get('available', False)}`",
    ])

    if chiral.get("available"):
        lines.append(f"- pseudoscalar: `{chiral['pseudoscalar_blade']}`")
        lines.append(f"- Type-1 orientation: `{chiral['type1_deductive']['orientation']}`")
        lines.append(f"- Type-2 orientation: `{chiral['type2_inductive']['orientation']}`")
        lines.append(f"- coupling product is scalar: `{chiral['coupling_is_scalar']}`")
    else:
        fb = chiral.get("fallback_summary", {})
        for k, v in fb.items():
            lines.append(f"- {k}: `{v}`")

    lines.extend([
        "",
        "## 4. Torus Geometry",
    ])
    for name, torus in geom.get("tori", {}).items():
        lines.append(f"- `{name}`: R_major={torus['R_major']:.4f}, R_minor={torus['R_minor']:.4f}, "
                     f"area={torus['area']:.4f}, flatness={torus['flatness']:.4f}, "
                     f"loop={torus['loop_assignment']}")
    lines.append(f"- Clifford equal-radii under imported constants: `{geom['clifford_is_flat']}`")
    lines.append(f"- Normalized eta-separation inner→outer: `{geom['transport_distance_inner_to_outer']}`")

    lines.extend([
        "",
        "## 5. Relevant Negative Evidence",
        f"- Torus witnesses: `{len(neg['torus_witnesses'])}`",
        f"- Chirality witnesses: `{len(neg['chirality_witnesses'])}`",
    ])
    for w in neg["torus_witnesses"] + neg["chirality_witnesses"]:
        emission = w["owner_edge_emission"]
        lines.append(f"- `{w['label']}` ({w['target_structure']}, {emission}): {w['description']}")

    lines.append("")
    lines.append("## Boundary Note")
    lines.append("- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    print(f"\n{'='*60}")
    print("QIT HOPF–WEYL PROJECTION SIDECAR")
    print(f"{'='*60}")

    proj = build_projection()

    _write_json(OUTPUT_JSON, proj)
    _write_text(OUTPUT_MD, _render_markdown(proj))

    cc = proj["torus_cell_complex"]
    chiral = proj["chirality_coupling"]

    print(f"  TopoNetX: available={cc.get('available', False)}")
    if cc.get("available"):
        print(f"    shape: {cc['shape']}")
        for t, info in cc.get("torus_2cells", {}).items():
            print(f"    torus {t}: {info['stage_count']} stage boundary")
    print(f"  Clifford: available={chiral.get('available', False)}")
    print(f"  Sidecar: do_not_promote={proj['sidecar_boundary']['do_not_promote']}")
    print(f"  JSON: {OUTPUT_JSON}")
    print(f"  MD:   {OUTPUT_MD}")


if __name__ == "__main__":
    main()
