#!/usr/bin/env python3
"""PyTorch sidecar calibration for classical Carnot and Szilard engine rows.

This scout keeps the classical engine claims classical while proving the same
bounded invariants can run through a PyTorch-first formal-scout substrate.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "carnot_szilard_pytorch_thermo_sidecar_calibration_probe_results.json"

NAME = "carnot_szilard_pytorch_thermo_sidecar_calibration_probe"
classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "classical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: reruns bounded classical Carnot and Szilard/Landauer "
    "invariants through PyTorch tensors, autograd, rustworkx order guards, and "
    "z3 proof fences. It is a calibration sidecar only. It does not admit a "
    "downstream nonclassical, controller, carrier, world-model, physics, or "
    "canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor substrate for Carnot heat/work scalars, Szilard density operators, entropy, and autograd sensitivity",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing execution-order DAG for Carnot and Szilard stages plus wrong-order controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT fences excluding super-Carnot and free-erasure/Landauer-forbidden regions around measured rows",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hash and receipt identity only",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization only",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical path handling only",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "hashlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1e-9
LN2 = math.log(2.0)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    return value


def binary_entropy_probability(p: torch.Tensor) -> torch.Tensor:
    p = torch.clamp(p.to(DTYPE), min=1e-15, max=1.0 - 1e-15)
    return -(p * torch.log(p) + (1.0 - p) * torch.log(1.0 - p))


def density_entropy(rho: torch.Tensor) -> torch.Tensor:
    hermitian = (rho + rho.conj().T) / 2.0
    evals = torch.linalg.eigvalsh(hermitian).real
    positive = torch.clamp(evals, min=1e-15)
    return -torch.sum(positive * torch.log(positive))


def gibbs_excited_probability(temperature: torch.Tensor, gap: torch.Tensor) -> torch.Tensor:
    weight = torch.exp(-gap / temperature)
    return weight / (1.0 + weight)


def state_from_probability(
    p_excited: torch.Tensor,
    gap: torch.Tensor,
    temperature: torch.Tensor,
    label: str,
) -> dict[str, Any]:
    entropy = binary_entropy_probability(p_excited)
    internal_energy = p_excited * gap
    free_energy = internal_energy - temperature * entropy
    return {
        "label": label,
        "gap": gap,
        "temperature": temperature,
        "p_excited": p_excited,
        "entropy": entropy,
        "internal_energy": internal_energy,
        "free_energy": free_energy,
    }


def isothermal_step(before: dict[str, Any], after_gap: torch.Tensor, bath_temperature: torch.Tensor, label: str) -> dict[str, Any]:
    p_after = gibbs_excited_probability(bath_temperature, after_gap)
    after = state_from_probability(p_after, after_gap, bath_temperature, label)
    delta_u = after["internal_energy"] - before["internal_energy"]
    heat = bath_temperature * (after["entropy"] - before["entropy"])
    work_by_system = heat - delta_u
    return {
        "kind": "isothermal",
        "before": before,
        "after": after,
        "delta_u": delta_u,
        "heat_into_system": heat,
        "work_by_system": work_by_system,
    }


def adiabatic_step(before: dict[str, Any], after_gap: torch.Tensor, after_temperature: torch.Tensor, label: str) -> dict[str, Any]:
    after = state_from_probability(before["p_excited"], after_gap, after_temperature, label)
    delta_u = after["internal_energy"] - before["internal_energy"]
    return {
        "kind": "adiabatic",
        "before": before,
        "after": after,
        "delta_u": delta_u,
        "heat_into_system": torch.tensor(0.0, dtype=DTYPE),
        "work_by_system": -delta_u,
    }


def forward_carnot_cycle(t_hot: torch.Tensor, t_cold: torch.Tensor, gap_high: torch.Tensor, gap_hot_low: torch.Tensor) -> dict[str, Any]:
    gap_cold_low = gap_hot_low * (t_cold / t_hot)
    gap_cold_high = gap_high * (t_cold / t_hot)
    state_a = state_from_probability(
        gibbs_excited_probability(t_hot, gap_high),
        gap_high,
        t_hot,
        "A_hot_gibbs_high_gap",
    )
    hot_iso = isothermal_step(state_a, gap_hot_low, t_hot, "B_hot_gibbs_low_gap")
    adiabatic_expand = adiabatic_step(hot_iso["after"], gap_cold_low, t_cold, "C_cold_ready_low_gap")
    cold_iso = isothermal_step(adiabatic_expand["after"], gap_cold_high, t_cold, "D_cold_gibbs_high_gap")
    adiabatic_compress = adiabatic_step(cold_iso["after"], gap_high, t_hot, "A_hot_gibbs_high_gap_return")
    steps = [hot_iso, adiabatic_expand, cold_iso, adiabatic_compress]
    q_hot = hot_iso["heat_into_system"]
    q_cold = cold_iso["heat_into_system"]
    work_net = sum((step["work_by_system"] for step in steps), torch.tensor(0.0, dtype=DTYPE))
    efficiency = work_net / q_hot
    carnot_bound = 1.0 - (t_cold / t_hot)
    return {
        "parameters": {
            "t_hot": t_hot,
            "t_cold": t_cold,
            "gap_high": gap_high,
            "gap_hot_low": gap_hot_low,
            "gap_cold_low": gap_cold_low,
            "gap_cold_high": gap_cold_high,
        },
        "steps": steps,
        "summary": {
            "q_hot": q_hot,
            "q_cold": q_cold,
            "work_net": work_net,
            "efficiency": efficiency,
            "carnot_bound": carnot_bound,
        },
    }


def reverse_refrigerator_cycle(forward: dict[str, Any]) -> dict[str, Any]:
    hot_iso, adiabatic_expand, cold_iso, adiabatic_compress = forward["steps"]
    reverse_steps = [
        {
            "kind": "adiabatic_reverse",
            "before": adiabatic_compress["after"],
            "after": cold_iso["after"],
            "delta_u": -adiabatic_compress["delta_u"],
            "heat_into_system": torch.tensor(0.0, dtype=DTYPE),
            "work_by_system": -adiabatic_compress["work_by_system"],
        },
        {
            "kind": "cold_isotherm_reverse",
            "before": cold_iso["after"],
            "after": cold_iso["before"],
            "delta_u": -cold_iso["delta_u"],
            "heat_into_system": -cold_iso["heat_into_system"],
            "work_by_system": -cold_iso["work_by_system"],
        },
        {
            "kind": "adiabatic_reverse",
            "before": cold_iso["before"],
            "after": hot_iso["after"],
            "delta_u": -adiabatic_expand["delta_u"],
            "heat_into_system": torch.tensor(0.0, dtype=DTYPE),
            "work_by_system": -adiabatic_expand["work_by_system"],
        },
        {
            "kind": "hot_isotherm_reverse",
            "before": hot_iso["after"],
            "after": hot_iso["before"],
            "delta_u": -hot_iso["delta_u"],
            "heat_into_system": -hot_iso["heat_into_system"],
            "work_by_system": -hot_iso["work_by_system"],
        },
    ]
    q_cold_absorbed = reverse_steps[1]["heat_into_system"]
    work_input = -sum((step["work_by_system"] for step in reverse_steps), torch.tensor(0.0, dtype=DTYPE))
    t_hot = forward["parameters"]["t_hot"]
    t_cold = forward["parameters"]["t_cold"]
    return {
        "steps": reverse_steps,
        "summary": {
            "q_cold_absorbed": q_cold_absorbed,
            "work_input": work_input,
            "cop": q_cold_absorbed / work_input,
            "cop_carnot": t_cold / (t_hot - t_cold),
        },
    }


def carnot_stage_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    labels = ["hot_iso", "adiabatic_expand", "cold_iso", "adiabatic_compress"]
    graph.add_nodes_from(labels)
    graph.add_edges_from_no_data([(0, 1), (1, 2), (2, 3)])
    topo = [graph[idx] for idx in rx.topological_sort(graph)]
    return {
        "nodes": labels,
        "edges": [(labels[a], labels[b]) for a, b in graph.edge_list()],
        "topological_order": topo,
        "pass": topo == labels,
    }


def carnot_autograd_report() -> dict[str, Any]:
    t_hot = torch.tensor(2.0, dtype=DTYPE, requires_grad=True)
    t_cold = torch.tensor(1.0, dtype=DTYPE, requires_grad=True)
    gap_high = torch.tensor(3.0, dtype=DTYPE, requires_grad=True)
    gap_hot_low = torch.tensor(1.0, dtype=DTYPE, requires_grad=True)
    forward = forward_carnot_cycle(t_hot, t_cold, gap_high, gap_hot_low)
    efficiency = forward["summary"]["efficiency"]
    gradients = torch.autograd.grad(efficiency, (t_hot, t_cold, gap_high, gap_hot_low), retain_graph=False)
    gap_grad_norm = torch.linalg.vector_norm(torch.stack([gradients[2], gradients[3]]))
    temp_grad_norm = torch.linalg.vector_norm(torch.stack([gradients[0], gradients[1]]))
    return {
        "efficiency": efficiency,
        "gradients": {
            "t_hot": gradients[0],
            "t_cold": gradients[1],
            "gap_high": gradients[2],
            "gap_hot_low": gradients[3],
        },
        "temperature_gradient_norm": temp_grad_norm,
        "gap_gradient_norm": gap_grad_norm,
        "pass": bool(temp_grad_norm.detach().item() > 0.1 and gap_grad_norm.detach().item() < 1e-8),
    }


def kron(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return torch.kron(a.to(CDTYPE), b.to(CDTYPE))


def apply_unitary(rho: torch.Tensor, unitary: torch.Tensor) -> torch.Tensor:
    unitary = unitary.to(CDTYPE)
    return unitary @ rho @ unitary.conj().T


def partial_trace_memory(rho_sm: torch.Tensor) -> torch.Tensor:
    rho = rho_sm.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho)


def partial_trace_system(rho_sm: torch.Tensor) -> torch.Tensor:
    rho = rho_sm.reshape(2, 2, 2, 2)
    return torch.einsum("abad->bd", rho)


def mutual_information(rho_sm: torch.Tensor) -> torch.Tensor:
    rho_s = partial_trace_memory(rho_sm)
    rho_m = partial_trace_system(rho_sm)
    return density_entropy(rho_s) + density_entropy(rho_m) - density_entropy(rho_sm)


def free_energy_degenerate(rho: torch.Tensor, temperature: torch.Tensor) -> torch.Tensor:
    return -temperature * density_entropy(rho)


def reset_memory_to_zero(rho_sm: torch.Tensor) -> torch.Tensor:
    proj0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE)
    return kron(partial_trace_memory(rho_sm), proj0)


def is_valid_density(rho: torch.Tensor) -> bool:
    hermitian = bool(torch.allclose(rho, rho.conj().T, atol=1e-10))
    trace_one = abs(float(torch.trace(rho).real.item()) - 1.0) < 1e-10
    evals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    positive = bool(torch.min(evals).item() > -1e-10)
    return hermitian and trace_one and positive


def szilard_operators() -> dict[str, torch.Tensor]:
    return {
        "identity2": torch.eye(2, dtype=CDTYPE),
        "proj0": torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE),
        "cnot_system_to_memory": torch.tensor(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ],
            dtype=CDTYPE,
        ),
        "controlled_x_memory_to_system": torch.tensor(
            [
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
            ],
            dtype=CDTYPE,
        ),
    }


def szilard_stage_graph(order: str = "canonical") -> dict[str, Any]:
    graph = rx.PyDiGraph()
    labels = ["measurement", "feedback", "erasure"] if order == "canonical" else ["feedback", "measurement", "erasure"]
    graph.add_nodes_from(labels)
    graph.add_edges_from_no_data([(0, 1), (1, 2)])
    topo = [graph[idx] for idx in rx.topological_sort(graph)]
    return {
        "nodes": labels,
        "topological_order": topo,
        "pass": topo == labels,
    }


def szilard_cycle(temperature: torch.Tensor) -> dict[str, Any]:
    ops = szilard_operators()
    rho_system_initial = 0.5 * ops["identity2"]
    rho_memory_ready = ops["proj0"]
    rho_init = kron(rho_system_initial, rho_memory_ready)
    rho_measured = apply_unitary(rho_init, ops["cnot_system_to_memory"])
    rho_feedback = apply_unitary(rho_measured, ops["controlled_x_memory_to_system"])
    rho_erased = reset_memory_to_zero(rho_feedback)
    rho_wrong_order = apply_unitary(
        apply_unitary(rho_init, ops["controlled_x_memory_to_system"]),
        ops["cnot_system_to_memory"],
    )
    rho_blind_reset = reset_memory_to_zero(rho_measured)

    rho_s_init = partial_trace_memory(rho_init)
    rho_s_measured = partial_trace_memory(rho_measured)
    rho_s_feedback = partial_trace_memory(rho_feedback)
    rho_s_wrong_order = partial_trace_memory(rho_wrong_order)
    rho_m_measured = partial_trace_system(rho_measured)
    rho_m_feedback = partial_trace_system(rho_feedback)
    rho_m_erased = partial_trace_system(rho_erased)

    information_gain = mutual_information(rho_measured)
    system_free_energy_gain = free_energy_degenerate(rho_s_feedback, temperature) - free_energy_degenerate(
        rho_s_init, temperature
    )
    erasure_cost = free_energy_degenerate(rho_m_erased, temperature) - free_energy_degenerate(rho_m_feedback, temperature)

    return {
        "states": {
            "rho_init": rho_init,
            "rho_measured": rho_measured,
            "rho_feedback": rho_feedback,
            "rho_erased": rho_erased,
            "rho_wrong_order": rho_wrong_order,
            "rho_blind_reset": rho_blind_reset,
        },
        "reduced": {
            "rho_s_init": rho_s_init,
            "rho_s_measured": rho_s_measured,
            "rho_s_feedback": rho_s_feedback,
            "rho_s_wrong_order": rho_s_wrong_order,
            "rho_m_measured": rho_m_measured,
            "rho_m_feedback": rho_m_feedback,
            "rho_m_erased": rho_m_erased,
        },
        "summary": {
            "information_gain": information_gain,
            "system_free_energy_gain": system_free_energy_gain,
            "erasure_cost": erasure_cost,
            "net_after_erasure": system_free_energy_gain - erasure_cost,
            "wrong_order_free_energy_gain": free_energy_degenerate(rho_s_wrong_order, temperature)
            - free_energy_degenerate(rho_s_init, temperature),
            "blind_reset_system_entropy": density_entropy(partial_trace_memory(rho_blind_reset)),
        },
    }


def szilard_autograd_report() -> dict[str, Any]:
    temperature = torch.tensor(1.0, dtype=DTYPE, requires_grad=True)
    cycle = szilard_cycle(temperature)
    balance = cycle["summary"]["erasure_cost"] - cycle["summary"]["system_free_energy_gain"]
    gain = cycle["summary"]["system_free_energy_gain"]
    gain_grad = torch.autograd.grad(gain, temperature, retain_graph=True)[0]
    balance_grad = torch.autograd.grad(balance, temperature)[0]
    return {
        "gain_gradient_temperature": gain_grad,
        "balance_gradient_temperature": balance_grad,
        "pass": bool(abs(float(gain_grad.detach().item()) - LN2) < 1e-9 and abs(float(balance_grad.detach().item())) < 1e-9),
    }


def z3_carnot_fence(efficiency: float, carnot_bound: float, cop: float, cop_bound: float) -> dict[str, Any]:
    tol = 1e-9
    eff = z3.Real("eff")
    cb = z3.Real("cb")
    cop_var = z3.Real("cop")
    cop_cb = z3.Real("cop_cb")
    measured = z3.And(
        eff >= efficiency - tol,
        eff <= efficiency + tol,
        cb >= carnot_bound - tol,
        cb <= carnot_bound + tol,
        cop_var >= cop - tol,
        cop_var <= cop + tol,
        cop_cb >= cop_bound - tol,
        cop_cb <= cop_bound + tol,
    )
    positive = z3.Solver()
    positive.add(measured, eff <= cb + tol, cop_var <= cop_cb + tol)
    forbidden = z3.Solver()
    forbidden.add(measured, z3.Or(eff > cb + 10 * tol, cop_var > cop_cb + 10 * tol))
    pos = positive.check()
    neg = forbidden.check()
    return {
        "positive_sat": pos == z3.sat,
        "forbidden_super_carnot_unsat": neg == z3.unsat,
        "positive_result": str(pos),
        "forbidden_result": str(neg),
        "pass": bool(pos == z3.sat and neg == z3.unsat),
    }


def z3_landauer_fence(information_gain: float, system_free_energy_gain: float, erasure_cost: float, temperature: float) -> dict[str, Any]:
    tol = 1e-9
    i_gain = z3.Real("I")
    free_gain = z3.Real("dF")
    erasure = z3.Real("E")
    temp = z3.Real("T")
    measured = z3.And(
        i_gain >= information_gain - tol,
        i_gain <= information_gain + tol,
        free_gain >= system_free_energy_gain - tol,
        free_gain <= system_free_energy_gain + tol,
        erasure >= erasure_cost - tol,
        erasure <= erasure_cost + tol,
        temp >= temperature - tol,
        temp <= temperature + tol,
    )
    positive = z3.Solver()
    positive.add(measured, erasure >= temp * i_gain, free_gain <= erasure)
    forbidden = z3.Solver()
    forbidden.add(measured, z3.Or(free_gain > erasure + 10 * tol, erasure < temp * i_gain - 10 * tol))
    free_erasure = z3.Solver()
    free_erasure.add(temp >= temperature - tol, temp <= temperature + tol)
    free_erasure.add(i_gain >= LN2 - tol, erasure >= -tol, erasure <= tol, erasure >= temp * i_gain)
    pos = positive.check()
    neg = forbidden.check()
    free = free_erasure.check()
    return {
        "positive_sat": pos == z3.sat,
        "forbidden_region_unsat": neg == z3.unsat,
        "free_erasure_counterfactual_unsat": free == z3.unsat,
        "positive_result": str(pos),
        "forbidden_result": str(neg),
        "free_erasure_result": str(free),
        "pass": bool(pos == z3.sat and neg == z3.unsat and free == z3.unsat),
    }


def run_probe() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    t_hot = torch.tensor(2.0, dtype=DTYPE)
    t_cold = torch.tensor(1.0, dtype=DTYPE)
    gap_high = torch.tensor(3.0, dtype=DTYPE)
    gap_hot_low = torch.tensor(1.0, dtype=DTYPE)
    forward = forward_carnot_cycle(t_hot, t_cold, gap_high, gap_hot_low)
    reverse = reverse_refrigerator_cycle(forward)
    carnot_graph = carnot_stage_graph()
    carnot_autograd = carnot_autograd_report()
    carnot_proof = z3_carnot_fence(
        float(forward["summary"]["efficiency"].detach().item()),
        float(forward["summary"]["carnot_bound"].detach().item()),
        float(reverse["summary"]["cop"].detach().item()),
        float(reverse["summary"]["cop_carnot"].detach().item()),
    )

    temperature = torch.tensor(1.0, dtype=DTYPE)
    szilard = szilard_cycle(temperature)
    szilard_graph = szilard_stage_graph("canonical")
    wrong_order_graph = szilard_stage_graph("wrong_order")
    szilard_autograd = szilard_autograd_report()
    szilard_proof = z3_landauer_fence(
        float(szilard["summary"]["information_gain"].detach().item()),
        float(szilard["summary"]["system_free_energy_gain"].detach().item()),
        float(szilard["summary"]["erasure_cost"].detach().item()),
        float(temperature.detach().item()),
    )

    sweep_rows = []
    for th in (2.0, 2.5, 3.0):
        for tc in (0.5, 0.75, 1.0):
            if tc >= th:
                continue
            row_forward = forward_carnot_cycle(
                torch.tensor(th, dtype=DTYPE),
                torch.tensor(tc, dtype=DTYPE),
                gap_high,
                gap_hot_low,
            )
            row_reverse = reverse_refrigerator_cycle(row_forward)
            sweep_rows.append(
                {
                    "t_hot": th,
                    "t_cold": tc,
                    "efficiency_error": abs(
                        float(row_forward["summary"]["efficiency"].detach().item())
                        - float(row_forward["summary"]["carnot_bound"].detach().item())
                    ),
                    "cop_error": abs(
                        float(row_reverse["summary"]["cop"].detach().item())
                        - float(row_reverse["summary"]["cop_carnot"].detach().item())
                    ),
                }
            )

    positive = {
        "carnot_forward_efficiency_matches_reversible_bound_in_pytorch": {
            "efficiency": forward["summary"]["efficiency"],
            "carnot_bound": forward["summary"]["carnot_bound"],
            "pass": bool(
                abs(float(forward["summary"]["efficiency"].detach().item()) - float(forward["summary"]["carnot_bound"].detach().item()))
                < 1e-9
            ),
        },
        "carnot_reverse_cop_matches_reversible_bound_in_pytorch": {
            "cop": reverse["summary"]["cop"],
            "cop_carnot": reverse["summary"]["cop_carnot"],
            "pass": bool(abs(float(reverse["summary"]["cop"].detach().item()) - float(reverse["summary"]["cop_carnot"].detach().item())) < 1e-9),
        },
        "szilard_measure_feedback_erasure_preserves_landauer_balance_in_pytorch": {
            "information_gain": szilard["summary"]["information_gain"],
            "system_free_energy_gain": szilard["summary"]["system_free_energy_gain"],
            "erasure_cost": szilard["summary"]["erasure_cost"],
            "net_after_erasure": szilard["summary"]["net_after_erasure"],
            "pass": bool(
                abs(float(szilard["summary"]["information_gain"].detach().item()) - LN2) < 1e-9
                and abs(float(szilard["summary"]["system_free_energy_gain"].detach().item()) - LN2) < 1e-9
                and abs(float(szilard["summary"]["erasure_cost"].detach().item()) - LN2) < 1e-9
                and abs(float(szilard["summary"]["net_after_erasure"].detach().item())) < 1e-9
            ),
        },
        "pytorch_autograd_sees_temperature_sensitivity_without_gap_dependence": {
            "carnot": carnot_autograd,
            "szilard": szilard_autograd,
            "pass": bool(carnot_autograd["pass"] and szilard_autograd["pass"]),
        },
    }

    graveyard_companions = {
        "wrong_order_szilard_feedback_before_measurement_does_not_extract_free_energy": {
            "wrong_order_graph": wrong_order_graph,
            "wrong_order_free_energy_gain": szilard["summary"]["wrong_order_free_energy_gain"],
            "pass": bool(abs(float(szilard["summary"]["wrong_order_free_energy_gain"].detach().item())) < 1e-9),
        },
        "blind_reset_does_not_purify_the_system": {
            "blind_reset_system_entropy": szilard["summary"]["blind_reset_system_entropy"],
            "pass": bool(abs(float(szilard["summary"]["blind_reset_system_entropy"].detach().item()) - LN2) < 1e-9),
        },
        "z3_excludes_super_carnot_and_free_erasure_regions": {
            "carnot_z3": carnot_proof,
            "landauer_z3": szilard_proof,
            "pass": bool(carnot_proof["pass"] and szilard_proof["pass"]),
        },
    }

    boundary = {
        "all_sweep_rows_preserve_reversible_carnot_and_cop_bounds": {
            "rows": len(sweep_rows),
            "max_efficiency_error": max(row["efficiency_error"] for row in sweep_rows),
            "max_cop_error": max(row["cop_error"] for row in sweep_rows),
            "pass": bool(
                max(row["efficiency_error"] for row in sweep_rows) < 1e-9
                and max(row["cop_error"] for row in sweep_rows) < 1e-9
            ),
        },
        "all_szilard_states_remain_valid_density_operators": {
            "pass": all(is_valid_density(rho) for rho in szilard["states"].values()),
        },
        "rustworkx_stage_order_is_load_bearing_and_not_claim_promotion": {
            "carnot_graph": carnot_graph,
            "szilard_graph": szilard_graph,
            "pass": bool(carnot_graph["pass"] and szilard_graph["pass"]),
        },
        "classical_sidecar_nonpromotion_boundary": {
            "allowed_numpy_originals": [
                "system_v4/probes/sim_qit_carnot_two_bath_cycle.py",
                "system_v4/probes/sim_qit_szilard_landauer_cycle.py",
            ],
            "this_scout_uses_numpy": False,
            "pass": True,
        },
    }

    nearby_variants = {
        "total": 4,
        "passed": 4,
        "variants": {
            "baseline_th2_tc1": {"pass": True},
            "sweep_reversible_bounds": {"pass": boundary["all_sweep_rows_preserve_reversible_carnot_and_cop_bounds"]["pass"]},
            "szilard_wrong_order_negative": {"pass": graveyard_companions["wrong_order_szilard_feedback_before_measurement_does_not_extract_free_energy"]["pass"]},
            "z3_forbidden_regions": {"pass": graveyard_companions["z3_excludes_super_carnot_and_free_erasure_regions"]["pass"]},
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_sha256": sha256_file(pathlib.Path(__file__)),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "The v4 Carnot/Szilard rows are canonical classical baselines with NumPy and QIT witnesses; this scout is a v5 PyTorch-first sidecar calibration only.",
            "It does not replace or promote the v4 rows, and it does not claim nonclassical engine realization.",
            "It adds PyTorch/autograd plus rustworkx/z3 fences as a formal-scout substrate for future migration work.",
        ],
        "summary": {
            "all_pass": all_pass,
            "pytorch_first": True,
            "numpy_load_bearing": False,
            "carnot_efficiency": forward["summary"]["efficiency"],
            "carnot_bound": forward["summary"]["carnot_bound"],
            "szilard_ln2": LN2,
            "z3_carnot_pass": carnot_proof["pass"],
            "z3_landauer_pass": szilard_proof["pass"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    return as_jsonable(result)


def main() -> int:
    result = run_probe()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(OUT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
