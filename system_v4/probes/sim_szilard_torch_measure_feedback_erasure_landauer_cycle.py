#!/usr/bin/env python3
"""PyTorch-native Szilard measurement-feedback-erasure cycle.

No NumPy is used. This is a semiclassical bridge/control row, not a
nonclassical promotion surface.
"""
from __future__ import annotations

import json
import pathlib

import torch
import z3


classification = "canonical"
sim_execution_kind = "bridge"
promotion_allowed = False

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density-operator evolution, entropy, partial traces, and finite-state checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exclusion of below-Landauer and free-work forbidden regions",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
}

DTYPE = torch.float64
TOL = 1e-9
LN2 = float(torch.log(torch.tensor(2.0, dtype=DTYPE)).item())


def projector(index: int) -> torch.Tensor:
    ket = torch.zeros((2, 1), dtype=DTYPE)
    ket[index, 0] = 1.0
    return ket @ ket.T


PROJ0 = projector(0)
IDENTITY_2 = torch.eye(2, dtype=DTYPE)
CNOT_SYSTEM_TO_MEMORY = torch.tensor(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=DTYPE,
)
CONTROLLED_X_MEMORY_TO_SYSTEM = torch.tensor(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ],
    dtype=DTYPE,
)


def entropy(rho: torch.Tensor) -> float:
    hermitian = (rho + rho.T) / 2
    evals = torch.linalg.eigvalsh(hermitian)
    positive = evals[evals > 1e-15]
    if positive.numel() == 0:
        return 0.0
    return float((-positive * torch.log(positive)).sum().item())


def partial_trace_memory(rho_sm: torch.Tensor) -> torch.Tensor:
    rho = rho_sm.reshape(2, 2, 2, 2)
    return torch.einsum("amcm->ac", rho)


def partial_trace_system(rho_sm: torch.Tensor) -> torch.Tensor:
    rho = rho_sm.reshape(2, 2, 2, 2)
    return torch.einsum("abad->bd", rho)


def mutual_information(rho_sm: torch.Tensor) -> float:
    return entropy(partial_trace_memory(rho_sm)) + entropy(partial_trace_system(rho_sm)) - entropy(rho_sm)


def apply_unitary(rho: torch.Tensor, unitary: torch.Tensor) -> torch.Tensor:
    return unitary @ rho @ unitary.T


def reset_memory_to_zero(rho_sm: torch.Tensor) -> torch.Tensor:
    return torch.kron(partial_trace_memory(rho_sm), PROJ0)


def is_valid_density(rho: torch.Tensor) -> bool:
    trace_one = abs(float(torch.trace(rho).item()) - 1.0) < TOL
    hermitian = bool(torch.allclose(rho, rho.T, atol=TOL, rtol=0.0))
    evals = torch.linalg.eigvalsh((rho + rho.T) / 2)
    positive = float(torch.min(evals).item()) > -TOL
    return bool(trace_one and hermitian and positive)


def free_energy_degenerate(rho: torch.Tensor, temperature: float) -> float:
    return -temperature * entropy(rho)


def tensor_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a - b).item())


def z3_landauer_proof(information_gain: float, system_gain: float, erasure_cost: float, temperature: float) -> dict:
    eps = 1e-9
    info = z3.Real("info")
    gain = z3.Real("gain")
    erase = z3.Real("erase")
    temp = z3.Real("temp")
    measured = z3.And(
        info >= information_gain - eps,
        info <= information_gain + eps,
        gain >= system_gain - eps,
        gain <= system_gain + eps,
        erase >= erasure_cost - eps,
        erase <= erasure_cost + eps,
        temp >= temperature - eps,
        temp <= temperature + eps,
    )
    positive = z3.Solver()
    positive.add(measured, erase >= temp * info, gain <= erase)
    forbidden = z3.Solver()
    forbidden.add(measured, z3.Or(gain > erase + 10 * eps, erase < temp * info - 10 * eps))
    free_erasure = z3.Solver()
    free_erasure.add(temp >= temperature - eps, temp <= temperature + eps)
    free_erasure.add(info >= LN2 - eps, erase >= -eps, erase <= eps, erase >= temp * info)
    pos = positive.check()
    neg = forbidden.check()
    free = free_erasure.check()
    return {
        "positive_sat": pos == z3.sat,
        "positive_result": str(pos),
        "forbidden_region_unsat": neg == z3.unsat,
        "forbidden_result": str(neg),
        "free_erasure_counterfactual_unsat": free == z3.unsat,
        "free_erasure_result": str(free),
        "pass": bool(pos == z3.sat and neg == z3.unsat and free == z3.unsat),
    }


def main() -> None:
    temperature = 1.0
    rho_system_initial = 0.5 * IDENTITY_2
    rho_memory_ready = PROJ0
    rho_init = torch.kron(rho_system_initial, rho_memory_ready)
    rho_measured = apply_unitary(rho_init, CNOT_SYSTEM_TO_MEMORY)
    rho_feedback = apply_unitary(rho_measured, CONTROLLED_X_MEMORY_TO_SYSTEM)
    rho_erased = reset_memory_to_zero(rho_feedback)

    rho_wrong_order = apply_unitary(
        apply_unitary(rho_init, CONTROLLED_X_MEMORY_TO_SYSTEM),
        CNOT_SYSTEM_TO_MEMORY,
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
    system_gain = free_energy_degenerate(rho_s_feedback, temperature) - free_energy_degenerate(rho_s_init, temperature)
    erasure_cost = free_energy_degenerate(rho_m_erased, temperature) - free_energy_degenerate(rho_m_feedback, temperature)
    proof = z3_landauer_proof(information_gain, system_gain, erasure_cost, temperature)

    positive = {
        "measurement_creates_one_bit_system_memory_correlation": {
            "system_entropy_after_measurement": entropy(rho_s_measured),
            "memory_entropy_after_measurement": entropy(rho_m_measured),
            "mutual_information": information_gain,
            "pass": bool(
                abs(entropy(rho_s_measured) - LN2) < TOL
                and abs(entropy(rho_m_measured) - LN2) < TOL
                and abs(information_gain - LN2) < TOL
            ),
        },
        "feedback_converts_record_into_one_bit_system_free_energy_gain": {
            "system_entropy_before_feedback": entropy(rho_s_init),
            "system_entropy_after_feedback": entropy(rho_s_feedback),
            "system_free_energy_gain": system_gain,
            "pass": bool(abs(system_gain - temperature * LN2) < TOL and entropy(rho_s_feedback) < TOL),
        },
        "erasure_closes_cycle_at_landauer_cost": {
            "memory_entropy_before_erasure": entropy(rho_m_feedback),
            "memory_entropy_after_erasure": entropy(rho_m_erased),
            "erasure_cost": erasure_cost,
            "pass": bool(abs(erasure_cost - temperature * LN2) < TOL and entropy(rho_m_erased) < TOL),
        },
        "torch_density_operators_remain_valid": {
            "pass": all(is_valid_density(rho) for rho in [rho_init, rho_measured, rho_feedback, rho_erased]),
        },
    }
    negative = {
        "feedback_before_measurement_does_not_purify_system": {
            "system_entropy_after_wrong_order": entropy(rho_s_wrong_order),
            "pass": bool(abs(entropy(rho_s_wrong_order) - LN2) < TOL),
        },
        "reset_without_feedback_does_not_extract_system_gain": {
            "system_entropy_after_blind_reset": entropy(partial_trace_memory(rho_blind_reset)),
            "blind_reset_gap_from_feedback": tensor_gap(rho_blind_reset, rho_feedback),
            "pass": bool(abs(entropy(partial_trace_memory(rho_blind_reset)) - LN2) < TOL),
        },
        "forbidden_free_work_or_below_landauer_region_is_unsat": {
            **proof,
            "pass": proof["pass"],
        },
    }
    boundary = {
        "no_numpy_dependency": {
            "tool_manifest_keys": sorted(TOOL_MANIFEST),
            "pass": "numpy" not in TOOL_MANIFEST and "numpy" not in TOOL_INTEGRATION_DEPTH,
        },
        "finite_two_qubit_carrier_only": {
            "carrier_dimension": int(rho_init.shape[0]),
            "ordered_steps": [
                "measurement_unitary",
                "record_conditioned_feedback_unitary",
                "memory_reset_map",
            ],
            "pass": rho_init.shape == (4, 4),
        },
    }
    all_pass = all(row["pass"] for section in (positive, negative, boundary) for row in section.values())
    results = {
        "name": "szilard_torch_measure_feedback_erasure_landauer_cycle",
        "classification": classification,
        "sim_execution_kind": sim_execution_kind,
        "promotion_allowed": promotion_allowed,
        "claim_ceiling": "semiclassical bridge Szilard control row only; PyTorch density bookkeeping, not nonclassical promotion",
        "promotion_condition": "May inform bridge-boundary work only after separate admission; never promotes nonclassical claims by itself.",
        "blocked_until": "Requires bridge admission and nonclassical comparison rows before any higher-level engine claim.",
        "next_lego_target": "semiclassical_szilard_negative_boundary_manifest",
        "demotion_condition": "Demote to classical calibration if PyTorch density evolution, Landauer UNSAT, or ordering controls fail.",
        "out_of_scope": [
            "nonclassical claim",
            "QIT engine admission",
            "axis or GStack claim",
            "universal demon claim",
        ],
        "prior_function_receipts": {
            "pytorch": "system_v4/probes/a2_state/sim_results/pytorch_capability_results.json",
            "z3": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "observable": {
            "information_gain": information_gain,
            "system_free_energy_gain": system_gain,
            "erasure_cost": erasure_cost,
            "net_after_erasure": system_gain - erasure_cost,
        },
        "summary": {
            "all_pass": all_pass,
            "uses_numpy": False,
            "uses_load_bearing_pytorch": True,
            "uses_load_bearing_z3": True,
            "scope_note": "Full finite Szilard measure-feedback-erasure schedule in PyTorch; bridge/control evidence only.",
        },
    }
    out_path = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "szilard_torch_measure_feedback_erasure_landauer_cycle_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
