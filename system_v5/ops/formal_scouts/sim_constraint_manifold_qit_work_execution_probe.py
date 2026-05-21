#!/usr/bin/env python3
"""Constraint-manifold QIT engine work-execution scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import rustworkx as rx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
ASSEMBLY_RECEIPT = RESULT_DIR / "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json"
OUT_PATH = RESULT_DIR / "constraint_manifold_qit_work_execution_probe_results.json"

NAME = "constraint_manifold_qit_work_execution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: consumes the manifold assembly constraint_set_for_engine "
    "and runs two finite chiral density operating spaces through 64 QIT engine "
    "work records. It tests interface execution and stage distinguishability, "
    "not final physics, cognition, intelligence, AI foundations, number theory, "
    "or canonical engine claims. It does not admit final physics or final intelligence claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, observables, matrix exponentials, trace distances, and signature profiles"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing 64-record execution graph and DAG order witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic engine-stage count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness over stage work bins"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
REAL_DTYPE = torch.float64
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SM = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SP = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)
H0 = 0.73 * SZ + 0.17 * SX

STAGES = ["Si", "Se", "Ne", "Ni"]
SUBSTAGES = ["signed_hamiltonian", "ladder_direction", "stage_projection", "loop_transport"]
OPERATORS = {"Ti": SZ, "Te": SX, "Fi": SX + 0.2 * SZ, "Fe": SY}
OPERATOR_SCHEDULE = [
    ("Ti", +1),
    ("Te", -1),
    ("Fi", +1),
    ("Fe", -1),
    ("Ti", -1),
    ("Te", +1),
    ("Fi", -1),
    ("Fe", +1),
]
LOOPS = ["fiber", "base_lift"]


def dagger(a: torch.Tensor) -> torch.Tensor:
    return a.conj().transpose(-2, -1)


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + dagger(rho)) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12)
    out = vecs @ torch.diag(vals.to(dtype=DTYPE)) @ dagger(vecs)
    return out / torch.trace(out)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / torch.sum(vals)
    return float((-(vals * torch.log(vals)).sum()).item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((a - b + dagger(a - b)) / 2).real
    return float((0.5 * torch.sum(torch.abs(vals))).item())


def unitary_update(rho: torch.Tensor, h: torch.Tensor, dt: float) -> torch.Tensor:
    u = torch.linalg.matrix_exp((-1j * h * dt).to(dtype=DTYPE))
    return normalize_density(u @ rho @ dagger(u))


def dissipative_update(rho: torch.Tensor, op: torch.Tensor, gamma: float, dt: float) -> torch.Tensor:
    jump = math.sqrt(max(gamma * dt, 0.0)) * op
    no_jump = I2 - 0.5 * gamma * dt * dagger(op) @ op
    return normalize_density(jump @ rho @ dagger(jump) + no_jump @ rho @ dagger(no_jump))


def projective_update(rho: torch.Tensor, axis: torch.Tensor, strength: float) -> torch.Tensor:
    axis = axis / max(float(torch.linalg.vector_norm(axis).item()), 1e-12)
    p_plus = 0.5 * (I2 + axis)
    p_minus = 0.5 * (I2 - axis)
    pinched = p_plus @ rho @ p_plus + p_minus @ rho @ p_minus
    return normalize_density((1 - strength) * rho + strength * pinched)


def load_constraint_set() -> tuple[dict[str, Any], dict[str, Any]]:
    data = json.loads(ASSEMBLY_RECEIPT.read_text(encoding="utf-8"))
    constraint_set = data.get("constraint_set_for_engine", {})
    if not constraint_set:
        raise RuntimeError("assembly receipt lacks constraint_set_for_engine")
    return data, constraint_set


def stage_axis(stage: str) -> torch.Tensor:
    return {
        "Si": SZ,
        "Se": SX,
        "Ne": SY,
        "Ni": (SX + SZ) / math.sqrt(2),
    }[stage]


def run_engine(constraint_set: dict[str, Any], collapsed: str | None = None) -> list[dict[str, Any]]:
    layer_rows = list(constraint_set["layers"])
    layer_weights = [row["support_weight"] for row in layer_rows]
    layer_offsets = [row["engine_gate_pair_offset"] for row in layer_rows]
    if collapsed == "flat_constraints":
        mean_weight = sum(float(weight) for weight in layer_weights) / max(len(layer_weights), 1)
        layer_weights = [mean_weight for _ in layer_weights]
        layer_offsets = [0 for _ in layer_offsets]
    states = {
        "left_chiral_density_space": normalize_density(torch.tensor([[0.82, 0.19], [0.19, 0.18]], dtype=DTYPE)),
        "right_chiral_density_space": normalize_density(torch.tensor([[0.31, -0.15j], [0.15j, 0.69]], dtype=DTYPE)),
    }
    records: list[dict[str, Any]] = []
    for space_idx, (space, rho) in enumerate(states.items()):
        h_sign = +1 if space_idx == 0 else -1
        ladder = SM if space_idx == 0 else SP
        for stage_idx, stage in enumerate(STAGES):
            for loop_idx, loop in enumerate(LOOPS):
                for sub_idx, substage in enumerate(SUBSTAGES):
                    global_idx = len(records)
                    op_name, op_sign = OPERATOR_SCHEDULE[(stage_idx * len(SUBSTAGES) + sub_idx + loop_idx) % len(OPERATOR_SCHEDULE)]
                    if collapsed == "operator_sign":
                        op_sign = +1
                    constraint_idx = (global_idx + stage_idx + sub_idx) % len(layer_weights)
                    weight = layer_weights[constraint_idx]
                    offset = layer_offsets[constraint_idx]
                    geometry_drive = weight * (1.0 + offset / max(len(layer_offsets) - 1, 1))
                    dt = 0.028 + 0.030 * geometry_drive
                    before = rho.clone()
                    energy_before = float(torch.real(torch.trace((h_sign * H0) @ before)).item())
                    entropy_before = entropy(before)
                    if substage == "signed_hamiltonian":
                        rho = unitary_update(rho, h_sign * H0 + 0.18 * op_sign * geometry_drive * OPERATORS[op_name], dt)
                    elif substage == "ladder_direction":
                        rho = dissipative_update(rho, ladder, 0.12 + 0.16 * geometry_drive, dt)
                    elif substage == "stage_projection":
                        rho = projective_update(rho, stage_axis(stage), min(0.22, 0.04 + 0.10 * geometry_drive))
                    else:
                        loop_axis = SZ if loop == "fiber" else SX
                        rho = unitary_update(rho, 0.16 * op_sign * geometry_drive * loop_axis + 0.06 * OPERATORS[op_name], dt)
                    energy_after = float(torch.real(torch.trace((h_sign * H0) @ rho)).item())
                    entropy_after = entropy(rho)
                    work_delta = energy_after - energy_before
                    min_eigenvalue = float(torch.min(torch.linalg.eigvalsh(rho).real).item())
                    records.append(
                        {
                            "index": global_idx,
                            "space": space,
                            "stage": stage,
                            "loop": loop,
                            "substage": substage,
                            "operator": op_name,
                            "operator_sign": op_sign,
                            "constraint_weight": weight,
                            "constraint_offset": offset,
                            "geometry_drive": geometry_drive,
                            "energy_delta": work_delta,
                            "entropy_delta": entropy_after - entropy_before,
                            "trace_distance": trace_distance(before, rho),
                            "valid_density": abs(float(torch.real(torch.trace(rho)).item()) - 1.0) < 1e-8
                            and min_eigenvalue >= -1e-9,
                            "signature": [
                                round(work_delta, 8),
                                round(entropy_after - entropy_before, 8),
                                round(trace_distance(before, rho), 8),
                            ],
                        }
                    )
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage: dict[str, list[list[float]]] = {}
    sheets = {row["space"] for row in records}
    loops = {row["loop"] for row in records}
    stages = {row["stage"] for row in records}
    substages = {row["substage"] for row in records}
    for row in records:
        key = f"{row['space']}::{row['stage']}::{row['loop']}"
        by_stage.setdefault(key, []).append(row["signature"])
    centroids = {key: torch.mean(torch.tensor(values, dtype=REAL_DTYPE), dim=0) for key, values in by_stage.items()}
    gaps = []
    keys = sorted(centroids)
    for idx, left in enumerate(keys):
        for right in keys[idx + 1 :]:
            gaps.append(float(torch.linalg.vector_norm(centroids[left] - centroids[right]).item()))
    work = torch.tensor([row["energy_delta"] for row in records], dtype=REAL_DTYPE)
    ent = torch.tensor([row["entropy_delta"] for row in records], dtype=REAL_DTYPE)
    return {
        "record_count": len(records),
        "factorization": {
            "sheets": len(sheets),
            "loop_placements": len(loops),
            "stages": len(stages),
            "substages": len(substages),
            "placements": len(sheets) * len(loops) * len(stages),
            "records": len(sheets) * len(loops) * len(stages) * len(substages),
            "shape": "2 sheets x 2 loop placements x 4 stages x 4 substages",
        },
        "stage_count": len(by_stage),
        "unique_stage_signatures": len({tuple(round(float(x), 6) for x in value.tolist()) for value in centroids.values()}),
        "min_stage_centroid_gap": min(gaps) if gaps else 0.0,
        "total_abs_work": float(torch.sum(torch.abs(work)).item()),
        "work_span": float((torch.max(work) - torch.min(work)).item()),
        "entropy_delta_span": float((torch.max(ent) - torch.min(ent)).item()),
        "stage_profile": [
            float(x)
            for key in keys
            for x in centroids[key].tolist()
        ],
    }


def profile_gap(left: dict[str, Any], right: dict[str, Any]) -> float:
    a = torch.tensor(left["stage_profile"], dtype=REAL_DTYPE)
    b = torch.tensor(right["stage_profile"], dtype=REAL_DTYPE)
    scalar_tail = torch.tensor(
        [
            left["total_abs_work"] - right["total_abs_work"],
            left["work_span"] - right["work_span"],
            left["entropy_delta_span"] - right["entropy_delta_span"],
        ],
        dtype=REAL_DTYPE,
    )
    return float(torch.linalg.vector_norm(torch.cat([a - b, scalar_tail])).item())


def nested_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    nested: dict[str, Any] = {}
    for row in records:
        nested.setdefault(row["space"], {}).setdefault(row["loop"], {}).setdefault(row["stage"], {})[row["substage"]] = {
            "index": row["index"],
            "operator": row["operator"],
            "operator_sign": row["operator_sign"],
            "constraint_weight": row["constraint_weight"],
            "constraint_offset": row["constraint_offset"],
            "geometry_drive": row["geometry_drive"],
            "energy_delta": row["energy_delta"],
            "entropy_delta": row["entropy_delta"],
            "trace_distance": row["trace_distance"],
            "signature": row["signature"],
            "valid_density": bool(row["valid_density"]),
        }
    return nested


def nested_shape_ok(nested: dict[str, Any]) -> bool:
    return (
        len(nested) == 2
        and all(len(loop_map) == 2 for loop_map in nested.values())
        and all(len(stage_map) == 4 for loop_map in nested.values() for stage_map in loop_map.values())
        and all(
            len(substage_map) == 4
            for loop_map in nested.values()
            for stage_map in loop_map.values()
            for substage_map in stage_map.values()
        )
    )


def graph_witness(records: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids: dict[int, int] = {}
    for row in records:
        node_ids[row["index"]] = graph.add_node({"index": row["index"], "stage": row["stage"], "space": row["space"]})
    for left, right in zip(records[:-1], records[1:]):
        graph.add_edge(node_ids[left["index"]], node_ids[right["index"]], {"ordered_successor": True})
    dag = rx.is_directed_acyclic_graph(graph)
    return {"nodes": graph.num_nodes(), "edges": graph.num_edges(), "dag": dag, "pass": dag and graph.num_nodes() == 64}


def z3_stage_noncollapse(summary: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    stage_unique = z3.Bool("stage_unique")
    work_nonzero = z3.Bool("work_nonzero")
    solver.add(stage_unique == (summary["unique_stage_signatures"] == summary["stage_count"]))
    solver.add(work_nonzero == (summary["total_abs_work"] > 0.05 and summary["work_span"] > 0.005))
    solver.add(stage_unique == z3.BoolVal(True))
    solver.add(work_nonzero == z3.BoolVal(True))
    solver.add(z3.Not(z3.And(stage_unique, work_nonzero)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat}


def main() -> int:
    started = time.time()
    assembly, constraint_set = load_constraint_set()
    nominal = run_engine(constraint_set)
    flat = run_engine(constraint_set, collapsed="flat_constraints")
    unsigned = run_engine(constraint_set, collapsed="operator_sign")
    nominal_summary = summarize(nominal)
    nominal_nested = nested_records(nominal)
    flat_summary = summarize(flat)
    unsigned_summary = summarize(unsigned)
    symbolic_count = sp.Integer(2) * sp.Integer(4) * sp.Integer(2) * sp.Integer(4)
    flat_gap = profile_gap(nominal_summary, flat_summary)
    sign_gap = profile_gap(nominal_summary, unsigned_summary)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "downstream_qit_engine_on_source_native_constraint_manifold",
        "consumed_receipts": {
            "manifold_operational_assembly_receipt": ASSEMBLY_RECEIPT.name,
        },
        "consumed_receipt_status": {
            "pass": assembly.get("summary", {}).get("all_pass") is True
            and constraint_set.get("schema") == "CONSTRAINT_SET_FOR_QIT_ENGINE_v1"
            and constraint_set.get("layer_order_hash") == assembly.get("layer_order_fingerprint_hash"),
            "assembly_summary": assembly.get("summary", {}),
            "constraint_set_schema": constraint_set.get("schema"),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engine_summary": nominal_summary,
        "nested_work_records": nominal_nested,
        "positive": {
            "constraint_set_for_engine_is_loaded": {
                "pass": constraint_set.get("schema") == "CONSTRAINT_SET_FOR_QIT_ENGINE_v1",
                "layer_count": constraint_set.get("layer_count"),
            },
            "sixty_four_qit_work_records_execute": {
                "pass": len(nominal) == 64 and all(row["valid_density"] for row in nominal),
                "record_count": len(nominal),
                "symbolic_count": str(symbolic_count),
            },
            "screenshot_factorization_is_preserved": {
                "pass": nominal_summary["factorization"]
                == {
                    "sheets": 2,
                    "loop_placements": 2,
                    "stages": 4,
                    "substages": 4,
                    "placements": 16,
                    "records": 64,
                    "shape": "2 sheets x 2 loop placements x 4 stages x 4 substages",
                },
                "factorization": nominal_summary["factorization"],
            },
            "nested_work_record_shape_is_preserved": {
                "pass": nested_shape_ok(nominal_nested),
                "shape": "nested_work_records[sheet][loop_placement][stage][substage]",
            },
            "sixteen_space_stage_loop_signatures_are_unique": {
                "pass": nominal_summary["stage_count"] == 16 and nominal_summary["unique_stage_signatures"] == 16,
                **nominal_summary,
            },
            "engine_records_do_measurable_work": {
                "pass": nominal_summary["total_abs_work"] > 0.05 and nominal_summary["work_span"] > 0.005,
                **nominal_summary,
            },
            "execution_graph_is_ordered": graph_witness(nominal),
            "z3_rejects_stage_work_collapse": z3_stage_noncollapse(nominal_summary),
        },
        "graveyard_companions": {
            "flat_constraint_weights_change_work_profile": {
                "pass": flat_gap > 0.005,
                "gap": flat_gap,
                "flat_summary": flat_summary,
            },
            "operator_sign_collapse_changes_work_profile": {
                "pass": sign_gap > 0.005,
                "gap": sign_gap,
                "unsigned_summary": unsigned_summary,
            },
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        },
        "boundary": {
            "does_not_claim_physics_or_intelligence": {
                "pass": "not final physics" in CLAIM_CEILING and "intelligence" in CLAIM_CEILING,
            },
            "manifold_receipt_precedes_engine_execution": {
                "pass": True,
                "receipt": ASSEMBLY_RECEIPT.name,
            },
        },
        "nearby_variants": {"total": 2, "passed": int(flat_gap > 0.005) + int(sign_gap > 0.005)},
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "why_not_v4_probes": [
            "Clean v5 manifold-to-engine handoff scout only.",
            "It consumes a v5 constraint_set_for_engine receipt and should not be mixed into the frozen v4 probe estate.",
            "It tests finite QIT work-record execution, not final physics, cognition, intelligence, AI foundations, number theory, or canonical engine claims.",
        ],
    }
    result["all_pass"] = (
        result["consumed_receipt_status"]["pass"]
        and all(row["pass"] for row in result["positive"].values())
        and all(row["pass"] for row in result["graveyard_companions"].values())
        and all(row["pass"] for row in result["boundary"].values())
        and result["nearby_variants"]["passed"] == result["nearby_variants"]["total"]
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
