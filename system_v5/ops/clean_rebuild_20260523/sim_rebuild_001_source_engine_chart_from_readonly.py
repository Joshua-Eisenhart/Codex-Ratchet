#!/usr/bin/env python3
"""Clean-room rebuild 001: source engine chart from read-only atlas.

This is a quarantine-safe rebuild scout. It does not read formal_scout result
JSON, grok_sim outputs, external-audit receipts, or cross-lane synthesis docs.

It reconstructs the engine chart tables from the read-only ENGINE_64 atlas and
checks the minimal runtime facts needed before rebuilding flux or Axis0:

* source table has 4 terrain families, 8 chart terrains, and 16 chart-locked
  macro-stage occupancies;
* Type-1 and Type-2 are distinct loop/orientation realizations of the same
  terrain families;
* the 64 chart slots are an index surface, not runtime truth;
* noncommuting operator/terrain order can matter under torch density maps;
* commuting controls erase the order gap.

Receipt is written to clean_rebuild_20260523/results, not formal_scouts/results.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_001_source_engine_chart_from_readonly_results.json"

classification = "clean_rebuild_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "source_engine_chart_readonly_rebuild"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild scout only. Reconstructs the source engine chart from "
    "read-only atlas tables and tests minimal torch order controls. It does "
    "not admit formal-scout evidence, Axis0, final terrain equations, or "
    "final engine ontology."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density operators, CPTP-style dephasing, unitaries, and noncommuting order controls",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive clean rebuild receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)


TYPE1_OUTER = [
    {"topology": "Se", "terrain": "Se-in", "token": "TiSe", "ax6": "UP", "signed_op": "Ti↑", "result": "LOSE"},
    {"topology": "Ne", "terrain": "Ne-in", "token": "NeTi", "ax6": "DOWN", "signed_op": "Ti↓", "result": "WIN"},
    {"topology": "Ni", "terrain": "Ni-in", "token": "NiFe", "ax6": "DOWN", "signed_op": "Fe↓", "result": "LOSE"},
    {"topology": "Si", "terrain": "Si-in", "token": "FeSi", "ax6": "UP", "signed_op": "Fe↑", "result": "WIN"},
]
TYPE1_INNER = [
    {"topology": "Se", "terrain": "Se-in", "token": "SeFi", "ax6": "DOWN", "signed_op": "Fi↓", "result": "win"},
    {"topology": "Si", "terrain": "Si-in", "token": "SiTe", "ax6": "DOWN", "signed_op": "Te↓", "result": "win"},
    {"topology": "Ni", "terrain": "Ni-in", "token": "TeNi", "ax6": "UP", "signed_op": "Te↑", "result": "lose"},
    {"topology": "Ne", "terrain": "Ne-in", "token": "FiNe", "ax6": "UP", "signed_op": "Fi↑", "result": "lose"},
]
TYPE2_OUTER = [
    {"topology": "Se", "terrain": "Se-out", "token": "FiSe", "ax6": "UP", "signed_op": "Fi↑", "result": "WIN"},
    {"topology": "Si", "terrain": "Si-out", "token": "TeSi", "ax6": "UP", "signed_op": "Te↑", "result": "WIN"},
    {"topology": "Ni", "terrain": "Ni-out", "token": "NiTe", "ax6": "DOWN", "signed_op": "Te↓", "result": "LOSE"},
    {"topology": "Ne", "terrain": "Ne-out", "token": "NeFi", "ax6": "DOWN", "signed_op": "Fi↓", "result": "LOSE"},
]
TYPE2_INNER = [
    {"topology": "Se", "terrain": "Se-out", "token": "SeTi", "ax6": "DOWN", "signed_op": "Ti↓", "result": "lose"},
    {"topology": "Ne", "terrain": "Ne-out", "token": "TiNe", "ax6": "UP", "signed_op": "Ti↑", "result": "win"},
    {"topology": "Ni", "terrain": "Ni-out", "token": "FeNi", "ax6": "UP", "signed_op": "Fe↑", "result": "lose"},
    {"topology": "Si", "terrain": "Si-out", "token": "SiFe", "ax6": "DOWN", "signed_op": "Fe↓", "result": "win"},
]

SOURCE_ROWS = [
    {"engine": "Type-1", "loop": "outer", "family": "deductive", **row} for row in TYPE1_OUTER
] + [
    {"engine": "Type-1", "loop": "inner", "family": "inductive", **row} for row in TYPE1_INNER
] + [
    {"engine": "Type-2", "loop": "outer", "family": "inductive", **row} for row in TYPE2_OUTER
] + [
    {"engine": "Type-2", "loop": "inner", "family": "deductive", **row} for row in TYPE2_INNER
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def density_from_bloch(x: float, y: float, z: float) -> torch.Tensor:
    r = torch.tensor([x, y, z], dtype=DTYPE)
    norm = torch.linalg.vector_norm(r).item()
    if norm >= 1.0:
        r = r / (norm + 1e-12) * 0.95
    return 0.5 * (I2 + r[0].item() * SX + r[1].item() * SY + r[2].item() * SZ)


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * axis


def rotate(rho: torch.Tensor, axis: torch.Tensor, theta: float) -> torch.Tensor:
    u = unitary(axis, theta)
    return hermitize(u @ rho @ torch.conj(u).T)


def dephase(rho: torch.Tensor, axis: torch.Tensor, q: float) -> torch.Tensor:
    return hermitize((1.0 - q) * rho + q * axis @ rho @ axis)


def fro_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).item())


def chart_gate() -> dict[str, Any]:
    tokens = [row["token"] for row in SOURCE_ROWS]
    chart_terrains = sorted({row["terrain"] for row in SOURCE_ROWS})
    topologies = sorted({row["topology"] for row in SOURCE_ROWS})
    type1 = [row for row in SOURCE_ROWS if row["engine"] == "Type-1"]
    type2 = [row for row in SOURCE_ROWS if row["engine"] == "Type-2"]
    type1_outer = [row["topology"] for row in type1 if row["loop"] == "outer"]
    type1_inner = [row["topology"] for row in type1 if row["loop"] == "inner"]
    type2_outer = [row["topology"] for row in type2 if row["loop"] == "outer"]
    type2_inner = [row["topology"] for row in type2 if row["loop"] == "inner"]
    expected_ax6 = {"UP", "DOWN"}
    return {
        "pass": bool(
            len(SOURCE_ROWS) == 16
            and len(set(tokens)) == 16
            and topologies == ["Ne", "Ni", "Se", "Si"]
            and len(chart_terrains) == 8
            and type1_outer == ["Se", "Ne", "Ni", "Si"]
            and type1_inner == ["Se", "Si", "Ni", "Ne"]
            and type2_outer == ["Se", "Si", "Ni", "Ne"]
            and type2_inner == ["Se", "Ne", "Ni", "Si"]
            and {row["ax6"] for row in SOURCE_ROWS} == expected_ax6
        ),
        "source": "system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md lines 67-78, 219-260, 268-287",
        "row_count": len(SOURCE_ROWS),
        "unique_token_count": len(set(tokens)),
        "topologies": topologies,
        "chart_terrain_count": len(chart_terrains),
        "chart_terrains": chart_terrains,
        "type1_outer_topology_order": type1_outer,
        "type1_inner_topology_order": type1_inner,
        "type2_outer_topology_order": type2_outer,
        "type2_inner_topology_order": type2_inner,
    }


def schedule_index_boundary_gate() -> dict[str, Any]:
    terrain_ids = ["Se-in", "Ne-in", "Ni-in", "Si-in", "Se-out", "Si-out", "Ni-out", "Ne-out"]
    signed_ops = ["Ti↑", "Ti↓", "Te↑", "Te↓", "Fi↑", "Fi↓", "Fe↑", "Fe↓"]
    chart_slots = [(terrain, op) for terrain in terrain_ids for op in signed_ops]
    starred = {(row["terrain"], row["signed_op"]) for row in SOURCE_ROWS}
    return {
        "pass": len(chart_slots) == 64 and len(starred) == 16 and len(chart_slots) - len(starred) == 48,
        "source": "ENGINE_64 atlas lines 268-287: 64-slot schedule index with 16 starred chart occupancies and 48 non-starred schedule slots",
        "chart_slot_count": len(chart_slots),
        "runtime_macro_occupancy_count": len(starred),
        "non_runtime_schedule_index_count": len(chart_slots) - len(starred),
        "boundary": "schedule slot identity is index metadata, not runtime truth",
    }


def order_control_gate() -> dict[str, Any]:
    rho0 = density_from_bloch(0.31, -0.42, 0.58)
    # Noncommuting fixture: z-dephasing terrain and x-rotation operator.
    terrain = lambda rho: dephase(rho, SZ, 0.23)
    operator = lambda rho: rotate(rho, SX, 0.71)
    up = terrain(operator(rho0))
    down = operator(terrain(rho0))
    noncommuting_gap = fro_gap(up, down)

    # Commuting control: z-dephasing and z-rotation commute.
    commuting_terrain = lambda rho: dephase(rho, SZ, 0.23)
    commuting_operator = lambda rho: rotate(rho, SZ, 0.71)
    commuting_up = commuting_terrain(commuting_operator(rho0))
    commuting_down = commuting_operator(commuting_terrain(rho0))
    commuting_gap = fro_gap(commuting_up, commuting_down)

    identity_gap = fro_gap(terrain(rho0), terrain(I2 @ rho0 @ I2))
    return {
        "pass": noncommuting_gap > 1e-3 and commuting_gap < 1e-12 and identity_gap < 1e-12,
        "source": "ENGINE_64 atlas line 202: UP=operator first, DOWN=terrain first; noncommuting order can matter",
        "noncommuting_order_gap": noncommuting_gap,
        "commuting_order_gap": commuting_gap,
        "identity_control_gap": identity_gap,
    }


def engine_distinction_gate() -> dict[str, Any]:
    type1_tokens = {row["token"] for row in SOURCE_ROWS if row["engine"] == "Type-1"}
    type2_tokens = {row["token"] for row in SOURCE_ROWS if row["engine"] == "Type-2"}
    shared_topologies = {
        engine: sorted({row["topology"] for row in SOURCE_ROWS if row["engine"] == engine})
        for engine in ("Type-1", "Type-2")
    }
    return {
        "pass": not bool(type1_tokens & type2_tokens) and shared_topologies["Type-1"] == shared_topologies["Type-2"],
        "source": "ENGINE_64 atlas lines 76-78 and 321-322: chart IDs differ by engine while terrain families are shared",
        "type1_token_count": len(type1_tokens),
        "type2_token_count": len(type2_tokens),
        "shared_token_count": len(type1_tokens & type2_tokens),
        "shared_topologies": shared_topologies,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    sections = {
        "source_chart_gate": chart_gate(),
        "schedule_index_boundary_gate": schedule_index_boundary_gate(),
        "order_control_gate": order_control_gate(),
        "engine_distinction_gate": engine_distinction_gate(),
    }
    all_pass = all(bool(section["pass"]) for section in sections.values())
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_001_source_engine_chart_from_readonly",
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "sections": sections,
        "source_boundary": {
            "reads_formal_scout_results": False,
            "reads_grok_sim": False,
            "reads_external_audits": False,
            "reads_cross_lane_synthesis_docs": False,
            "primary_reference_docs": [
                "system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md",
                "system_v5/READ ONLY Reference Docs/operator math explicit.md",
            ],
        },
        "next_clean_rebuild_targets": [
            "flux_as_hopf_weyl_manifold_binding",
            "spinor_carrier_entropy_controls",
            "axis0_candidate_family_from_clean_xi_fixture",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

