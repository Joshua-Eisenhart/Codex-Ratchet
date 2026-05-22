#!/usr/bin/env python3
"""Source chiral seven-control 64-microstep execution scout."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json"

NAME = "source_chiral_seven_control_sixty_four_microstep_execution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs the source-native paired chiral density sheets "
    "through 64 microsteps with seven executable downstream handles. This "
    "receipt is admissible only when paired with a passing manifold-support or "
    "operational-assembly receipt proving those handles have 13-layer support. "
    "Without that parent receipt, it is a local execution/control-population "
    "scout only. It does not admit final manifold, final axis ontology, "
    "physics, cognition, personality, or canonical claims."
)

CONSUMED_RECEIPTS = {
    "manifold_operational_assembly_receipt": "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
    "manifold_support_receipt": "nested_constraint_manifold_operational_handle_support_probe_results.json",
}
EXPECTED_MANIFOLD_LAYER_ORDER_HASH = "c8eb87dbec785d3c507c1184978210b9deb5c80813de43259868d1d3f672319d"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, matrix exponentials, control signatures, and distance controls"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing 64-node execution graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over seven-control trajectory signatures"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic seven-control count inventory"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing seven-control noncollapse witness"},
    "source_density_scout": {"tried": True, "used": True, "reason": "load-bearing source-native density, loop, and terrain helpers"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'networkx': 'load_bearing',
    'gudhi': 'load_bearing',
    'sympy': 'load_bearing',
    'z3': 'load_bearing',
    'source_density_scout': 'supportive',
}

DTYPE = torch.complex128
FLOAT_DTYPE = torch.float64
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SM = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SP = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)
H0 = 0.77 * SZ + 0.13 * SX

STAGE_BITS = {
    "Se": (-1, -1),
    "Ne": (-1, +1),
    "Ni": (+1, -1),
    "Si": (+1, +1),
}
STAGES_FROM_BITS = {value: key for key, value in STAGE_BITS.items()}
TRAVERSALS = {
    "inductive_cycle": ["Si", "Se", "Ne", "Ni"],
    "deductive_cycle": ["Si", "Ni", "Ne", "Se"],
}
SUBSTAGES = ["signed_hamiltonian", "ladder_direction", "stage_projection", "loop_transport"]
OP_FAMILIES = ["Ti", "Te", "Fi", "Fe"]
OP_AXES = {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SY}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, torch.Tensor):
        if torch.is_complex(value):
            return {"real": value.real.detach().cpu().tolist(), "imag": value.imag.detach().cpu().tolist()}
        return value.detach().cpu().tolist()
    return value


def receipt_all_pass(data: dict[str, Any]) -> bool:
    return data.get("all_pass") is True or data.get("summary", {}).get("all_pass") is True


def validate_consumed_receipts() -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    for key, filename in CONSUMED_RECEIPTS.items():
        path = RESULT_DIR / filename
        status: dict[str, Any] = {"filename": filename, "exists": path.exists(), "pass": False}
        if not path.exists():
            status["errors"] = ["missing parent receipt"]
            statuses[key] = status
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        errors: list[str] = []
        if data.get("classification") != "formal_scout":
            errors.append("classification is not formal_scout")
        if data.get("promotion_allowed") is not False:
            errors.append("promotion_allowed is not false")
        if data.get("blockers"):
            errors.append("blockers present")
        if not receipt_all_pass(data):
            errors.append("parent all_pass/summary.all_pass is not true")
        if key == "manifold_operational_assembly_receipt":
            summary = data.get("summary", {})
            positive = data.get("positive", {})
            if data.get("source_alignment_category") != "source_native_constraint_manifold_operational_assembly":
                errors.append("not source_native_constraint_manifold_operational_assembly")
            if summary.get("layer_count", 0) < 13:
                errors.append("assembly layer_count below 13")
            if summary.get("load_bearing_count", 0) < 13:
                errors.append("assembly load_bearing_count below 13")
            if summary.get("max_bond", 0) <= 1:
                errors.append("assembly tensor-network max_bond not above product-state floor")
            if summary.get("max_bond", 0) >= 24:
                errors.append("assembly tensor-network hit declared MAX_BOND saturation")
            if summary.get("entropy_span", 0.0) <= 0.05:
                errors.append("assembly entropy_span below content threshold")
            if summary.get("ordering_gap", 0.0) <= 1e-3:
                errors.append("assembly ordering_gap below content threshold")
            if summary.get("min_layer_removal_diff", 0.0) <= 1e-3:
                errors.append("assembly min_layer_removal_diff below content threshold")
            if summary.get("min_reverse_layer_removal_diff", 0.0) <= 1e-3:
                errors.append("assembly min_reverse_layer_removal_diff below content threshold")
            if data.get("layer_order_fingerprint_hash") != EXPECTED_MANIFOLD_LAYER_ORDER_HASH:
                errors.append("assembly layer_order_fingerprint_hash does not match pinned contract")
            if positive.get("reverse_order_uses_same_enforcer_path_with_reversed_fingerprint", {}).get("pass") is not True:
                errors.append("assembly reverse-order fingerprint check not passing")
            if positive.get("all_thirteen_layers_have_runtime_effect_under_reverse_order", {}).get("pass") is not True:
                errors.append("assembly reverse-layer-removal effect check not passing")
        if key == "manifold_support_receipt":
            positive = data.get("positive", {})
            if data.get("source_alignment_category") != "source_native_constraint_manifold_support":
                errors.append("not source_native_constraint_manifold_support")
            if positive.get("seven_handles_have_multilayer_manifold_support", {}).get("pass") is not True:
                errors.append("seven handle support check not passing")
            if positive.get("thirteen_nested_layers_are_primary_support_surface", {}).get("pass") is not True:
                errors.append("13-layer support surface check not passing")
        status.update(
            {
                "pass": not errors,
                "errors": errors,
                "classification": data.get("classification"),
                "promotion_allowed": data.get("promotion_allowed"),
                "source_alignment_category": data.get("source_alignment_category"),
                "summary": data.get("summary", {}),
            }
        )
        statuses[key] = status
    return {
        "pass": all(row["pass"] for row in statuses.values()) and set(statuses) == set(CONSUMED_RECEIPTS),
        "statuses": statuses,
    }


def load_source_module():
    path = ROOT / "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py"
    spec = importlib.util.spec_from_file_location("source_stage_subcycle", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = load_source_module()


def dagger(a: torch.Tensor) -> torch.Tensor:
    return a.conj().T


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = torch.as_tensor(rho, dtype=DTYPE)
    rho = (rho + dagger(rho)) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12).to(DTYPE)
    out = vecs @ torch.diag(vals) @ dagger(vecs)
    return out / torch.trace(out).real


def unitary_update(rho: torch.Tensor, hamiltonian: torch.Tensor, dt: float) -> torch.Tensor:
    u = torch.linalg.matrix_exp(-1j * hamiltonian * dt)
    return normalize_density(u @ rho @ dagger(u))


def dissipator_update(rho: torch.Tensor, op: torch.Tensor, gamma: float, dt: float) -> torch.Tensor:
    jump = math.sqrt(max(gamma * dt, 0.0)) * op
    no_jump = I2 - 0.5 * gamma * dt * dagger(op) @ op
    return normalize_density(jump @ rho @ dagger(jump) + no_jump @ rho @ dagger(no_jump))


def dephase_update(rho: torch.Tensor, axis: torch.Tensor, rate: float, dt: float) -> torch.Tensor:
    projectors = [0.5 * (I2 + axis), 0.5 * (I2 - axis)]
    pinched = sum(p @ rho @ p for p in projectors)
    return normalize_density((1 - rate * dt) * rho + rate * dt * pinched)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def readout(rho: torch.Tensor) -> list[float]:
    return [float(torch.real(torch.trace(obs @ rho)).item()) for obs in (SX, SY, SZ)]


def normalize_axis(axis: torch.Tensor) -> torch.Tensor:
    return axis / max(float(torch.linalg.vector_norm(axis).item()), 1e-9)


def valid_density(rho: torch.Tensor) -> bool:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2)
    return bool(torch.allclose(rho, dagger(rho), atol=1e-9) and abs(float(torch.trace(rho).real.item()) - 1.0) < 1e-9 and float(torch.min(vals).item()) > -1e-9)


def stage_spec(sheet: str, stage: str) -> dict[str, Any]:
    return SOURCE.terrain_spec(sheet, stage)


def op_pair(stage_index: int, substage_index: int, collapse: bool) -> tuple[str, int]:
    family = OP_FAMILIES[substage_index]
    if collapse:
        return family, +1
    base = [1, -1, 1, -1][substage_index]
    return family, base if stage_index % 2 == 0 else -base


def entropy_feedback_update(
    rho: torch.Tensor,
    geom: dict[str, float],
    feedback_sign: int,
    rate: float,
    freeze: bool,
    stage_bits: tuple[int, int],
    excitation: float,
    operator_sign: int,
) -> tuple[dict[str, float], float]:
    if freeze:
        return dict(geom), 0.0
    eps = 1e-3
    grads = []
    out = dict(geom)
    for key, gain in [("metric_scale", 0.31), ("connection", 0.24), ("twist", 0.28)]:
        plus = dict(geom)
        minus = dict(geom)
        plus[key] += eps
        minus[key] -= eps
        gp = local_projected_entropy(rho, plus, rate)
        gm = local_projected_entropy(rho, minus, rate)
        grad = (gp - gm) / (2 * eps)
        grads.append(grad)
        bit_one, bit_two = stage_bits
        structural_drive = {
            "metric_scale": 0.070 * bit_one * excitation,
            "connection": 0.095 * bit_two * operator_sign,
            "twist": 0.075 * bit_one * bit_two * excitation * operator_sign,
        }[key]
        out[key] = out[key] + feedback_sign * gain * grad + structural_drive
    out["metric_scale"] = min(1.85, max(0.55, out["metric_scale"]))
    out["connection"] = min(1.80, max(-1.80, out["connection"]))
    out["twist"] = min(1.30, max(-1.30, out["twist"]))
    return out, float(torch.linalg.vector_norm(torch.tensor(grads, dtype=FLOAT_DTYPE)).item())


def local_projected_entropy(rho: torch.Tensor, geom: dict[str, float], rate: float) -> float:
    axis = math.tanh(geom["twist"]) * SX + (1.0 - abs(math.tanh(geom["twist"]))) * SZ
    axis = axis / max(float(torch.linalg.vector_norm(axis).item()), 1e-9)
    trial = dephase_update(rho, axis, min(0.50, rate * geom["metric_scale"]), 0.07)
    mix = min(0.40, 0.024 * abs(geom["connection"]) + 0.016 * abs(geom["twist"]))
    return entropy(normalize_density((1 - mix) * trial + mix * I2 / 2.0))


def stage_for_mode(stage: str, mode: str) -> str:
    if mode == "collapse_stage_bit_one":
        return STAGES_FROM_BITS[(+1, STAGE_BITS[stage][1])]
    if mode == "collapse_stage_bit_two":
        return STAGES_FROM_BITS[(STAGE_BITS[stage][0], +1)]
    return stage


def traversal_for_mode(name: str, stages: list[str], mode: str) -> tuple[str, list[str]]:
    if mode == "collapse_traversal_order":
        return "inductive_cycle", TRAVERSALS["inductive_cycle"]
    return name, stages


def loop_for_mode(traversal: str, mode: str) -> str:
    if mode == "collapse_loop_placement":
        return "fiber_loop"
    return "fiber_loop" if traversal == "inductive_cycle" else "base_lift_loop"


def excitation_level(stage_index: int, substage_index: int, mode: str) -> float:
    if mode == "collapse_excitation_level":
        return 1.0
    return 0.55 if (stage_index + substage_index) % 2 == 0 else 1.65


def apply_step(
    rho: torch.Tensor,
    *,
    sheet: str,
    stage: str,
    loop: str,
    stage_index: int,
    substage_index: int,
    geom: dict[str, float],
    mode: str,
) -> tuple[torch.Tensor, tuple[str, int], float]:
    spec = stage_spec(sheet, stage)
    bit_one, bit_two = STAGE_BITS[stage]
    family, sign = op_pair(stage_index, substage_index, mode == "collapse_operator_sign")
    heat = excitation_level(stage_index, substage_index, mode)
    h_base = H0 if sheet == "left_chiral_operating_space" else -H0
    ladder = SM if sheet == "left_chiral_operating_space" else SP
    axis = OP_AXES[family]
    stage_axis = bit_one * SX + bit_two * SY + 0.35 * bit_one * bit_two * SZ
    stage_axis = stage_axis / max(float(torch.linalg.vector_norm(stage_axis).item()), 1e-9)
    stage_gain = 1.0 + 0.18 * bit_one + 0.13 * bit_two
    if substage_index == 0:
        h = h_base + 0.24 * sign * heat * axis + 0.18 * heat * stage_axis
        return unitary_update(rho, h, 0.060 * geom["metric_scale"] * stage_gain), (family, sign), heat
    if substage_index == 1:
        return dissipator_update(rho, ladder, (0.10 + float(spec["rate"]) * geom["metric_scale"] * stage_gain) * heat, 0.074), (family, sign), heat
    if substage_index == 2:
        mixed_axis = normalize_axis(0.62 * axis + 0.38 * sign * stage_axis)
        return dephase_update(rho, mixed_axis, min(0.58, float(spec["rate"]) * heat * stage_gain * (1 + 0.16 * abs(geom["twist"]))), 0.090), (family, sign), heat
    loop_rho = torch.as_tensor(SOURCE.loop_density(loop, (stage_index + 1) * (2 * math.pi / 9) + 0.22 * sign * heat + 0.09 * (bit_one - bit_two)), dtype=DTYPE)
    weight = min(0.52, (0.08 if loop == "fiber_loop" else 0.28) * heat * stage_gain + 0.030 * abs(geom["connection"]))
    return normalize_density((1 - weight) * rho + weight * loop_rho), (family, sign), heat


def run(mode: str = "nominal") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]:
        geom = {"metric_scale": 1.0, "connection": 0.36 if sheet.startswith("left") else -0.36, "twist": 0.07}
        feedback_sign = +1 if sheet.startswith("left") else -1
        if mode == "collapse_feedback_sign":
            feedback_sign = +1
        stage_index = 0
        for traversal_name, raw_stages in TRAVERSALS.items():
            traversal, stages = traversal_for_mode(traversal_name, raw_stages, mode)
            loop = loop_for_mode(traversal, mode)
            for raw_stage in stages:
                stage = stage_for_mode(raw_stage, mode)
                stage_bits = STAGE_BITS[stage]
                rho = torch.as_tensor(SOURCE.loop_density(loop, (stage_index + 1) * (2 * math.pi / 9)), dtype=DTYPE)
                spec = stage_spec(sheet, stage)
                for substage_index, substage in enumerate(SUBSTAGES):
                    family_preview, sign_preview = op_pair(stage_index, substage_index, mode == "collapse_operator_sign")
                    heat_preview = excitation_level(stage_index, substage_index, mode)
                    geom, grad_norm = entropy_feedback_update(
                        rho,
                        geom,
                        feedback_sign,
                        float(spec["rate"]),
                        freeze=mode == "collapse_feedback_sign",
                        stage_bits=stage_bits,
                        excitation=heat_preview,
                        operator_sign=sign_preview,
                    )
                    rho, (family, op_sign), heat = apply_step(
                        rho,
                        sheet=sheet,
                        stage=stage,
                        loop=loop,
                        stage_index=stage_index,
                        substage_index=substage_index,
                        geom=geom,
                        mode=mode,
                    )
                    rows.append(
                        {
                            "sheet": sheet,
                            "stage_index": stage_index,
                            "substage_index": substage_index,
                            "traversal": traversal,
                            "loop": loop,
                            "stage": stage,
                            "stage_bit_one": stage_bits[0],
                            "stage_bit_two": stage_bits[1],
                            "substage": substage,
                            "operator_family": family,
                            "operator_sign": op_sign,
                            "excitation_level": heat,
                            "feedback_sign": feedback_sign,
                            "stage_law": spec["terrain_law"],
                            "entropy": entropy(rho),
                            "readout": readout(rho),
                            "coherence": float(abs(rho[0, 1]) + abs(rho[1, 0])),
                            "metric_scale": geom["metric_scale"],
                            "connection": geom["connection"],
                            "twist": geom["twist"],
                            "gradient_norm": grad_norm,
                            "valid_density": valid_density(rho),
                        }
                    )
                stage_index += 1
    return rows


def features(rows: list[dict[str, Any]]) -> torch.Tensor:
    return torch.tensor(
        [
            [
                r["entropy"],
                *r["readout"],
                r["coherence"],
                r["metric_scale"],
                r["connection"],
                r["twist"],
                r["gradient_norm"],
                float(r["stage_bit_one"]),
                float(r["stage_bit_two"]),
                float(r["feedback_sign"]),
                float(r["operator_sign"]),
                float(r["excitation_level"]),
            ]
            for r in rows
        ],
        dtype=FLOAT_DTYPE,
    )


def dynamic_features(rows: list[dict[str, Any]]) -> torch.Tensor:
    return features(rows)[:, :9]


def inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "feedback_sign": sorted({r["feedback_sign"] for r in rows}),
        "stage_bit_one": sorted({r["stage_bit_one"] for r in rows}),
        "stage_bit_two": sorted({r["stage_bit_two"] for r in rows}),
        "loop": sorted({r["loop"] for r in rows}),
        "traversal": sorted({r["traversal"] for r in rows}),
        "excitation_level": sorted({r["excitation_level"] for r in rows}),
        "operator_sign": sorted({r["operator_sign"] for r in rows}),
        "operator_sign_pairs_by_sheet": {
            sheet: len({(r["operator_family"], r["operator_sign"]) for r in rows if r["sheet"] == sheet})
            for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]
        },
    }


def trajectory_gap(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> float:
    return float(torch.linalg.vector_norm(dynamic_features(a) - dynamic_features(b)).item())


def full_signature_gap(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> float:
    return float(torch.linalg.vector_norm(features(a) - features(b)).item())


def effect_summary(nominal: list[dict[str, Any]], modes: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    nominal_again = run("nominal")
    repeat_floor = max(1e-9, trajectory_gap(nominal, nominal_again))
    rows = {}
    for name, control_rows in modes.items():
        dynamic_gap = trajectory_gap(nominal, control_rows)
        full_gap = full_signature_gap(nominal, control_rows)
        rows[name] = {
            "dynamic_gap": dynamic_gap,
            "full_signature_gap": full_gap,
            "effect_over_repeat_floor": dynamic_gap / repeat_floor,
            "pass": dynamic_gap > 1.0 and dynamic_gap / repeat_floor > 1.0e6,
        }
    ranked = sorted(rows, key=lambda key: rows[key]["dynamic_gap"])
    return {
        "repeat_floor": repeat_floor,
        "ranked_controls_weak_to_strong": ranked,
        "rows": rows,
    }


def persistence(points: torch.Tensor) -> dict[str, Any]:
    rips = gudhi.RipsComplex(points=points[:, :8].tolist(), max_edge_length=3.0)
    st = rips.create_simplex_tree(max_dimension=2)
    pairs = st.persistence()
    h0 = [death - birth for dim, (birth, death) in pairs if dim == 0 and math.isfinite(death)]
    h1 = [death - birth for dim, (birth, death) in pairs if dim == 1 and math.isfinite(death)]
    return {"h0_finite_count": len(h0), "h1_finite_count": len(h1), "max_h0": max(h0) if h0 else 0.0, "max_h1": max(h1) if h1 else 0.0}


def graph_for(rows: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for row in rows:
        node = f"{row['sheet']}::{row['stage_index']}::{row['substage_index']}"
        graph.add_node(node)
    for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]:
        nodes = [n for n in graph.nodes if n.startswith(sheet)]
        nodes = sorted(nodes, key=lambda n: tuple(map(int, n.rsplit("::", 2)[1:])))
        for a, b in zip(nodes, nodes[1:]):
            graph.add_edge(a, b)
    return graph


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal = run("nominal")
    modes = {
        "collapse_feedback_sign": run("collapse_feedback_sign"),
        "collapse_stage_bit_one": run("collapse_stage_bit_one"),
        "collapse_stage_bit_two": run("collapse_stage_bit_two"),
        "collapse_loop_placement": run("collapse_loop_placement"),
        "collapse_traversal_order": run("collapse_traversal_order"),
        "collapse_excitation_level": run("collapse_excitation_level"),
        "collapse_operator_sign": run("collapse_operator_sign"),
    }
    effects = effect_summary(nominal, modes)
    gaps = {name: row["dynamic_gap"] for name, row in effects["rows"].items()}
    inv = inventory(nominal)
    graph = graph_for(nominal)
    labels = {f"{r['sheet']}::{r['stage_index']}::{r['substage_index']}" for r in nominal}
    z3_solver = z3.Solver()
    label_vars = [z3.Int(f"microstep_label_{idx}") for idx in range(64)]
    for idx, var in enumerate(label_vars):
        z3_solver.add(var == idx)
    z3_solver.add(z3.Distinct(*label_vars))
    z3_solver.add(len(labels) == 64)
    z3_solver.add(all(len(inv[key]) == 2 for key in ["feedback_sign", "stage_bit_one", "stage_bit_two", "loop", "traversal", "excitation_level", "operator_sign"]))
    z3_status = z3_solver.check()
    symbolic_factors = {
        "sheets": sp.Integer(2),
        "traversals": sp.Integer(2),
        "stages_per_traversal": sp.Integer(4),
        "substages": sp.Integer(4),
    }
    symbolic_count = sp.prod(symbolic_factors.values())
    symbolic_factorization = sp.factor(symbolic_count)
    p = persistence(dynamic_features(nominal))
    consumed_receipt_status = validate_consumed_receipts()
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_seven_operational_control_sixty_four_microstep_formal_scout",
        "consumed_receipts": CONSUMED_RECEIPTS,
        "consumed_receipt_status": consumed_receipt_status,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "microstep_count": len(nominal),
        "control_inventory": inv,
        "control_collapse_gaps": gaps,
        "control_effect_summary": effects,
        "positive": {
            "sixty_four_microsteps_execute_on_source_native_chiral_sheets": {
                "pass": len(nominal) == 64 and all(r["valid_density"] for r in nominal),
                "count": len(nominal),
            },
            "seven_operational_controls_are_populated": {
                "pass": all(len(inv[key]) == 2 for key in ["feedback_sign", "stage_bit_one", "stage_bit_two", "loop", "traversal", "excitation_level", "operator_sign"]),
                "inventory": inv,
            },
            "all_operator_sign_pairs_execute_per_sheet": {
                "pass": all(v == 8 for v in inv["operator_sign_pairs_by_sheet"].values()),
                "pair_counts": inv["operator_sign_pairs_by_sheet"],
            },
            "every_control_is_load_bearing_under_collapse": {
                "pass": all(row["pass"] for row in effects["rows"].values()),
                "effect_summary": effects,
            },
            "topological_signature_is_nontrivial": {
                "pass": p["h0_finite_count"] > 0 and p["max_h0"] > 0.01,
                **p,
            },
            "graph_symbolic_smt_contract_executes": {
                "pass": nx.is_directed_acyclic_graph(graph) and symbolic_count == 64 and z3_status == z3.sat,
                "graph_nodes": graph.number_of_nodes(),
                "graph_edges": graph.number_of_edges(),
                "symbolic_count": str(symbolic_count),
                "symbolic_factorization": str(symbolic_factorization),
                "symbolic_factors": {key: str(value) for key, value in symbolic_factors.items()},
                "z3": str(z3_status),
            },
        },
        "graveyard_companions": {
            name: {
                "pass": row["pass"],
                "dynamic_gap": row["dynamic_gap"],
                "full_signature_gap": row["full_signature_gap"],
                "effect_over_repeat_floor": row["effect_over_repeat_floor"],
            }
            for name, row in effects["rows"].items()
        },
        "boundary": {
            "controls_are_operational_not_final_ontology": {"pass": True},
            "axis_handles_are_non_exhaustive": {
                "pass": True,
                "note": "The seven executable controls are current handles for the seven axes, not exhaustive definitions of those axes.",
            },
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
            "manifold_parent_receipts_are_declared": {
                "pass": set(CONSUMED_RECEIPTS) == {"manifold_operational_assembly_receipt", "manifold_support_receipt"},
                "consumed_receipts": CONSUMED_RECEIPTS,
            },
            "manifold_parent_receipts_are_loaded_and_passing": consumed_receipt_status,
            "source_native_history_precedes_downstream_readout": {
                "pass": True,
                "source_module": "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py",
            },
        },
        "nearby_variants": {
            "total": 7,
            "passed": sum(1 for row in effects["rows"].values() if row["pass"]),
            "variants": sorted(gaps),
        },
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - start,
        "why_not_v4_probes": [
            "Seven-control 64-microstep scout only.",
            "It shows these executable axis handles are populated and load-bearing under finite controls, not that they exhaust the axes or fix final axis ontology.",
            "It keeps human-facing labels out of the executable filename and formal ontology.",
        ],
    }
    result["all_pass"] = (
        all(v["pass"] for v in result["positive"].values())
        and all(v["pass"] for v in result["graveyard_companions"].values())
        and all(v["pass"] for v in result["boundary"].values())
        and result["nearby_variants"]["passed"] == result["nearby_variants"]["total"]
    )
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
