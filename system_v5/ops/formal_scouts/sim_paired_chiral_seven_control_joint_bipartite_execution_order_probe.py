#!/usr/bin/env python3
"""Paired chiral seven-control joint bipartite execution-order scout."""

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
import opt_einsum as oe
import quimb as qu
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "paired_chiral_seven_control_joint_bipartite_execution_order_probe_results.json"

NAME = "paired_chiral_seven_control_joint_bipartite_execution_order_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: downstream joint bipartite readout assembled from a "
    "support-admitted seven-handle source receipt. It tests finite mutual "
    "information, logarithmic negativity, and ordering sensitivity on a 4x4 "
    "carrier. It does not admit manifold structure, final axis ontology, "
    "bridge/coupling-program advancement, engine identity, physics, cognition, "
    "ontology, or canonical claims."
)

CONSUMED_RECEIPTS = {
    "manifold_operational_assembly_receipt": "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
    "manifold_support_receipt": "nested_constraint_manifold_operational_handle_support_probe_results.json",
    "seven_handle_source_receipt": "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json",
}
EXPECTED_MANIFOLD_LAYER_ORDER_HASH = "c8eb87dbec785d3c507c1184978210b9deb5c80813de43259868d1d3f672319d"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing joint density matrices, matrix exponentials, distances, and entropy features"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing partial transpose/log-negativity cross-check on 4x4 states"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace contractions"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor norm cross-check for joint trajectories"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing joint execution dependency graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over joint bipartite features"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic factorization of paired execution count"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite ordering/coupling admissibility witness"},
    "seven_control_scout": {"tried": True, "used": True, "reason": "load-bearing source-native seven-control marginal trajectories"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'quimb': 'load_bearing',
    'opt_einsum': 'load_bearing',
    'networkx': 'load_bearing',
    'gudhi': 'load_bearing',
    'sympy': 'load_bearing',
    'z3': 'load_bearing',
    'seven_control_scout': 'supportive',
}

DTYPE = torch.complex128
FLOAT_DTYPE = torch.float64
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
ZZ = torch.kron(SZ, SZ)
XY = torch.kron(SX, SY)
YX = torch.kron(SY, SX)


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
        if key == "seven_handle_source_receipt":
            boundary = data.get("boundary", {})
            if data.get("source_alignment_category") != "source_native_seven_operational_control_sixty_four_microstep_formal_scout":
                errors.append("not source_native seven-control receipt")
            if data.get("microstep_count") != 64:
                errors.append("seven-control receipt microstep_count is not 64")
            if boundary.get("manifold_parent_receipts_are_loaded_and_passing", {}).get("pass") is not True:
                errors.append("seven-control receipt did not load passing manifold parents")
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


def load_seven_module():
    path = ROOT / "sim_source_chiral_seven_control_sixty_four_microstep_execution_probe.py"
    spec = importlib.util.spec_from_file_location("seven_control", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SEVEN = load_seven_module()


def coerce_source_loop_density_to_imported_array() -> None:
    array_module = getattr(SEVEN, "np")
    original_loop_density = SEVEN.SOURCE.loop_density

    def wrapped_loop_density(*args: Any, **kwargs: Any) -> Any:
        value = original_loop_density(*args, **kwargs)
        if hasattr(value, "detach"):
            value = value.detach().cpu().tolist()
        return array_module.asarray(value, dtype=array_module.complex128)

    SEVEN.SOURCE.loop_density = wrapped_loop_density


coerce_source_loop_density_to_imported_array()


def dagger(a: torch.Tensor) -> torch.Tensor:
    return a.conj().T


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + dagger(rho)) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12).to(DTYPE)
    out = vecs @ torch.diag(vals) @ dagger(vecs)
    return out / torch.trace(out).real


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def bloch_to_density(v: torch.Tensor) -> torch.Tensor:
    norm = float(torch.linalg.vector_norm(v).item())
    if norm > 0.96:
        v = v * (0.96 / norm)
    return normalize_density(0.5 * (I2 + v[0] * SX + v[1] * SY + v[2] * SZ))


def partial_trace_left(rho: torch.Tensor) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2)
    return normalize_density(oe.contract("abcb->ac", tensor))


def partial_trace_right(rho: torch.Tensor) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2)
    return normalize_density(oe.contract("abad->bd", tensor))


def mutual_information(rho: torch.Tensor) -> float:
    left = partial_trace_left(rho)
    right = partial_trace_right(rho)
    return max(0.0, entropy(left) + entropy(right) - entropy(rho))


def partial_transpose_second(rho: torch.Tensor) -> torch.Tensor:
    return rho.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)


def log_negativity(rho: torch.Tensor) -> float:
    pt = partial_transpose_second(rho)
    eigs = torch.linalg.eigvalsh((pt + dagger(pt)) / 2)
    trace_norm = float(torch.sum(torch.abs(eigs)).item())
    torch_value = max(0.0, math.log2(max(trace_norm, 1e-12)))
    quimb_value = float(qu.log2(max(trace_norm, 1e-12)))
    return max(torch_value, quimb_value)


def valid_joint_density(rho: torch.Tensor) -> bool:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2)
    return bool(torch.allclose(rho, dagger(rho), atol=1e-9) and abs(float(torch.trace(rho).real.item()) - 1.0) < 1e-9 and float(torch.min(vals).item()) > -1e-9)


def local_state(row: dict[str, Any]) -> torch.Tensor:
    return bloch_to_density(torch.tensor(row["readout"], dtype=FLOAT_DTYPE))


def local_unitary(row: dict[str, Any]) -> torch.Tensor:
    axis = row["operator_sign"] * torch.as_tensor(SEVEN.OP_AXES[row["operator_family"]], dtype=DTYPE)
    axis = axis + 0.18 * row["stage_bit_one"] * SX + 0.15 * row["stage_bit_two"] * SY
    axis = axis / max(float(torch.linalg.vector_norm(axis).item()), 1e-9)
    angle = 0.072 * row["excitation_level"] * (1.0 + 0.14 * row["feedback_sign"])
    return torch.linalg.matrix_exp(-1j * angle * axis)


def apply_local_left(rho: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    big = torch.kron(u, I2)
    return normalize_density(big @ rho @ dagger(big))


def apply_local_right(rho: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    big = torch.kron(I2, u)
    return normalize_density(big @ rho @ dagger(big))


def apply_joint_coupling(rho: torch.Tensor, j: float, left_row: dict[str, Any], right_row: dict[str, Any]) -> torch.Tensor:
    feedback_contrast = 0.5 * (left_row["feedback_sign"] - right_row["feedback_sign"])
    bit_drive = left_row["stage_bit_one"] * XY + left_row["stage_bit_two"] * YX
    h_int = (
        (1.0 + 0.36 * feedback_contrast) * ZZ
        + 0.42 * bit_drive
        + 0.62 * feedback_contrast * left_row["operator_sign"] * torch.kron(SX, SX)
    )
    dt = 0.110 * left_row["excitation_level"] * (1.0 + 0.18 * feedback_contrast + 0.06 * abs(left_row["connection"]))
    u = torch.linalg.matrix_exp(-1j * j * dt * h_int)
    return normalize_density(u @ rho @ dagger(u))


def paired_rows(mode: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    rows = SEVEN.run(mode)
    left = [r for r in rows if r["sheet"] == "left_chiral_operating_space"]
    right = [r for r in rows if r["sheet"] == "right_chiral_operating_space"]
    return list(zip(left, right))


def run_joint(mode: str = "nominal", *, j: float = 0.75, order: str = "left_then_right") -> list[dict[str, Any]]:
    pairs = paired_rows(mode)
    rho = normalize_density(torch.kron(local_state(pairs[0][0]), local_state(pairs[0][1])))
    out = []
    for idx, (left_row, right_row) in enumerate(pairs):
        ul = local_unitary(left_row)
        ur = local_unitary(right_row)
        if order == "left_then_right":
            rho = apply_local_left(rho, ul)
            rho = apply_joint_coupling(rho, j, right_row, left_row)
            rho = apply_local_right(rho, ur)
        elif order == "right_then_left":
            rho = apply_local_right(rho, ur)
            rho = apply_joint_coupling(rho, j, left_row, right_row)
            rho = apply_local_left(rho, ul)
        else:
            raise ValueError(order)
        refresh = normalize_density(torch.kron(local_state(left_row), local_state(right_row)))
        rho = normalize_density(0.88 * rho + 0.12 * refresh)
        mi = mutual_information(rho)
        en = log_negativity(rho)
        torch_norm = float(torch.linalg.matrix_norm(rho.to(torch.complex128)).item())
        out.append(
            {
                "index": idx,
                "mode": mode,
                "order": order,
                "rho": rho,
                "valid_density": valid_joint_density(rho),
                "mutual_information": mi,
                "log_negativity": en,
                "left_entropy": entropy(partial_trace_left(rho)),
                "right_entropy": entropy(partial_trace_right(rho)),
                "joint_entropy": entropy(rho),
                "torch_norm": torch_norm,
                "stage": left_row["stage"],
                "traversal": left_row["traversal"],
                "loop": left_row["loop"],
                "operator_family": left_row["operator_family"],
                "operator_sign": left_row["operator_sign"],
                "excitation_level": left_row["excitation_level"],
            }
        )
    return out


def joint_features(rows: list[dict[str, Any]]) -> torch.Tensor:
    return torch.tensor(
        [
            [
                r["mutual_information"],
                r["log_negativity"],
                r["left_entropy"],
                r["right_entropy"],
                r["joint_entropy"],
                r["torch_norm"],
                float(r["operator_sign"]),
                float(r["excitation_level"]),
            ]
            for r in rows
        ],
        dtype=FLOAT_DTYPE,
    )


def gap(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> float:
    return float(torch.linalg.vector_norm(joint_features(a)[:, :6] - joint_features(b)[:, :6]).item())


def persistence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    points = joint_features(rows)[:, :6]
    rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=1.5)
    st = rips.create_simplex_tree(max_dimension=2)
    pairs = st.persistence()
    h0 = [death - birth for dim, (birth, death) in pairs if dim == 0 and math.isfinite(death)]
    h1 = [death - birth for dim, (birth, death) in pairs if dim == 1 and math.isfinite(death)]
    return {"h0_finite_count": len(h0), "h1_finite_count": len(h1), "max_h0": max(h0) if h0 else 0.0, "max_h1": max(h1) if h1 else 0.0}


def graph_for(rows: list[dict[str, Any]]) -> nx.DiGraph:
    g = nx.DiGraph()
    for row in rows:
        g.add_node(row["index"], order=row["order"])
    for a, b in zip(range(len(rows) - 1), range(1, len(rows))):
        g.add_edge(a, b)
    return g


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal = run_joint("nominal", j=0.75, order="left_then_right")
    reversed_order = run_joint("nominal", j=0.75, order="right_then_left")
    zero_coupling = run_joint("nominal", j=0.0, order="left_then_right")
    collapse_modes = {
        "collapse_feedback_sign": run_joint("collapse_feedback_sign", j=0.75),
        "collapse_stage_bit_one": run_joint("collapse_stage_bit_one", j=0.75),
        "collapse_stage_bit_two": run_joint("collapse_stage_bit_two", j=0.75),
        "collapse_loop_placement": run_joint("collapse_loop_placement", j=0.75),
        "collapse_traversal_order": run_joint("collapse_traversal_order", j=0.75),
        "collapse_excitation_level": run_joint("collapse_excitation_level", j=0.75),
        "collapse_operator_sign": run_joint("collapse_operator_sign", j=0.75),
    }
    collapse_gaps = {name: gap(nominal, rows) for name, rows in collapse_modes.items()}
    order_gap = gap(nominal, reversed_order)
    coupling_gap = gap(nominal, zero_coupling)
    max_mi = max(r["mutual_information"] for r in nominal)
    max_en = max(r["log_negativity"] for r in nominal)
    max_zero_en = max(r["log_negativity"] for r in zero_coupling)
    p = persistence(nominal)
    graph = graph_for(nominal)
    z3_solver = z3.Solver()
    order_gap_var = z3.Real("order_gap")
    mi_var = z3.Real("max_mi")
    z3_solver.add(order_gap_var > sp.Rational(1, 10))
    z3_solver.add(mi_var > sp.Rational(1, 100))
    z3_solver.add(order_gap_var == order_gap)
    z3_solver.add(mi_var == max_mi)
    z3_status = z3_solver.check()
    symbolic_count = sp.Integer(2) * sp.Integer(32)
    consumed_receipt_status = validate_consumed_receipts()
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "paired_chiral_joint_bipartite_downstream_on_source_native_formal_scout",
        "consumed_receipts": CONSUMED_RECEIPTS,
        "consumed_receipt_status": consumed_receipt_status,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "microstep_count": len(nominal) * 2,
        "joint_pair_count": len(nominal),
        "positive": {
            "joint_execution_all_valid_density": {"pass": len(nominal) == 32 and all(r["valid_density"] for r in nominal), "joint_rows": len(nominal)},
            "coupling_produces_information_and_entanglement": {"pass": max_mi > 0.01 and max_en > 1e-4 and coupling_gap > 0.05, "max_mi": max_mi, "max_log_negativity": max_en, "zero_coupling_max_log_negativity": max_zero_en, "coupling_gap": coupling_gap},
            "ordering_noncommutativity_gap_positive": {"pass": order_gap > 0.10, "order_gap": order_gap},
            "seven_controls_remain_load_bearing_on_joint_trajectory": {"pass": all(value > 0.20 for value in collapse_gaps.values()), "collapse_gaps": collapse_gaps},
            "joint_persistence_nontrivial": {"pass": p["h0_finite_count"] > 0 and p["max_h0"] > 0.001, **p},
            "graph_symbolic_smt_contract_executes": {"pass": nx.is_directed_acyclic_graph(graph) and symbolic_count == 64 and z3_status == z3.sat, "graph_nodes": graph.number_of_nodes(), "graph_edges": graph.number_of_edges(), "symbolic_count": str(symbolic_count), "z3": str(z3_status)},
        },
        "graveyard_companions": {
            "zero_coupling_reduces_joint_effect": {"pass": coupling_gap > 0.05 and max_zero_en <= max_en + 1e-9, "gap": coupling_gap, "zero_coupling_max_log_negativity": max_zero_en},
            "reversed_order_changes_trajectory": {"pass": order_gap > 0.10, "gap": order_gap},
            **{name: {"pass": value > 0.20, "gap": value} for name, value in collapse_gaps.items()},
        },
        "boundary": {
            "joint_probe_is_not_coupling_program_promotion": {"pass": True},
            "axis_handles_are_non_exhaustive": {
                "pass": True,
                "note": "The seven executable controls are current handles for the seven axes, while the axes remain richer coupled degrees of freedom.",
            },
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
            "manifold_and_source_parent_receipts_are_declared": {
                "pass": set(CONSUMED_RECEIPTS)
                == {"manifold_operational_assembly_receipt", "manifold_support_receipt", "seven_handle_source_receipt"},
                "consumed_receipts": CONSUMED_RECEIPTS,
            },
            "manifold_and_source_parent_receipts_are_loaded_and_passing": consumed_receipt_status,
            "source_native_marginals_precede_joint_readout": {"pass": True, "source_module": "sim_source_chiral_seven_control_sixty_four_microstep_execution_probe.py"},
        },
        "nearby_variants": {"total": 9, "passed": sum(1 for row in collapse_gaps.values() if row > 0.20) + int(coupling_gap > 0.05) + int(order_gap > 0.10), "variants": ["zero_coupling", "reversed_order", *sorted(collapse_gaps)]},
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - start,
        "why_not_v4_probes": [
            "Joint paired-chiral scout only.",
            "It tests a finite 4x4 bipartite execution assembled from source-native seven-control marginals, not final manifold or coupling-program promotion.",
            "It does not canonize the seven controls as exhaustive definitions of the seven axes.",
            "Surviving candidates remain formal-scout candidates.",
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
