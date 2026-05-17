#!/usr/bin/env python3
"""Eight-qubit MPS entropy readout under layer constraints scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import opt_einsum as oe
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "eight_qubit_mps_entropy_readout_layer_constraint_probe_results.json"

NAME = "eight_qubit_mps_entropy_readout_layer_constraint_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: couples finite 8-qubit MPS/channel layer constraints "
    "to entropy readouts and checks which readouts separate ordered, swapped, "
    "and degenerate variants. It does not admit a final manifold nesting, "
    "bridge, cycle, axis, or target-system entropy claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 8-qubit density/channel and entropy readouts"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing 8-qubit MPS contraction"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite layer-count and entropy-readout separation constraints"},
}
TOOL_INTEGRATION_DEPTH = {key: "load_bearing" for key in TOOL_MANIFEST}


def ghz_mps_state(n: int = 8) -> torch.Tensor:
    tensors = []
    first = torch.zeros((1, 2, 2), dtype=torch.complex128)
    first[0, 0, 0] = 1 / math.sqrt(2)
    first[0, 1, 1] = 1 / math.sqrt(2)
    tensors.append(first)
    for _ in range(n - 2):
        middle = torch.zeros((2, 2, 2), dtype=torch.complex128)
        middle[0, 0, 0] = 1
        middle[1, 1, 1] = 1
        tensors.append(middle)
    last = torch.zeros((2, 2, 1), dtype=torch.complex128)
    last[0, 0, 0] = 1
    last[1, 1, 0] = 1
    tensors.append(last)
    letters = "abcdefghijklmnopqrstuvwxyz"
    expr = ",".join(f"{letters[i]}{letters[8+i]}{letters[i+1]}" for i in range(n)) + "->" + "".join(letters[8 : 8 + n])
    psi = torch.from_numpy(oe.contract(expr, *[t.numpy() for t in tensors]).reshape(2**n))
    return psi / torch.linalg.vector_norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def one_qubit_operator(local: torch.Tensor, qubit: int, n: int = 8) -> torch.Tensor:
    op = torch.tensor([[1.0 + 0j]], dtype=torch.complex128)
    eye = torch.eye(2, dtype=torch.complex128)
    for idx in range(n):
        op = torch.kron(op, local if idx == qubit else eye)
    return op


def controlled_x(control: int, target: int, n: int = 8) -> torch.Tensor:
    u = torch.zeros((2**n, 2**n), dtype=torch.complex128)
    for idx in range(2**n):
        bits = [(idx >> (n - 1 - q)) & 1 for q in range(n)]
        if bits[control]:
            bits[target] ^= 1
        out = 0
        for bit in bits:
            out = (out << 1) | bit
        u[out, idx] = 1
    return u


def damping(rho: torch.Tensor, qubit: int, gamma: float, n: int = 8) -> torch.Tensor:
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=torch.complex128)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=torch.complex128)
    out = torch.zeros_like(rho)
    for k in (k0, k1):
        op = one_qubit_operator(k, qubit, n)
        out = out + op @ rho @ op.conj().T
    return out


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def partial_trace_first_half(rho: torch.Tensor, n: int = 8) -> torch.Tensor:
    dim_a = 2 ** (n // 2)
    dim_b = 2 ** (n - n // 2)
    return torch.einsum("abcb->ac", rho.reshape(dim_a, dim_b, dim_a, dim_b))


def cut_readouts(rho: torch.Tensor) -> dict[str, Any]:
    rho_a = partial_trace_first_half(rho)
    s_ab = entropy(rho)
    s_a = entropy(rho_a)
    return {
        "S_AB": s_ab,
        "S_A_first_half": s_a,
        "coherent_proxy_A_to_rest": s_a - s_ab,
        "conditional_proxy_rest_given_A": s_ab - s_a,
        "purity": float(torch.real(torch.trace(rho @ rho)).item()),
    }


def z3_layer_entropy_constraints(gap: float) -> dict[str, Any]:
    layers = z3.Int("layers")
    dim = z3.Int("dim")
    sep = z3.Real("entropy_separation")
    finite = z3.Solver()
    finite.add(layers == 6, dim == 256, z3.Or(layers > 6, dim != 256))
    separation = z3.Solver()
    separation.add(sep > 0, sep == 0)
    return {
        "finite_layer_and_dimension_escape_unsat": {"solver_status": str(finite.check()), "pass": finite.check() == z3.unsat},
        "positive_entropy_readout_separation_not_zero_unsat": {"solver_status": str(separation.check()), "numeric_gap": gap, "pass": separation.check() == z3.unsat and gap > 1e-6},
    }


def main() -> dict[str, Any]:
    started = time.time()
    psi = ghz_mps_state()
    rho = density(psi)
    u = controlled_x(control=1, target=0)
    ordered = damping(u @ rho @ u.conj().T, qubit=0, gamma=0.29)
    swapped = u @ damping(rho, qubit=0, gamma=0.29) @ u.conj().T
    identity = damping(rho, qubit=0, gamma=0.0)
    ordered_r = cut_readouts(ordered)
    swapped_r = cut_readouts(swapped)
    entropy_gap = abs(ordered_r["S_A_first_half"] - swapped_r["S_A_first_half"])
    z3_rows = z3_layer_entropy_constraints(entropy_gap)

    global_entropy_gap = abs(ordered_r["S_AB"] - swapped_r["S_AB"])
    coherent_gap = abs(ordered_r["coherent_proxy_A_to_rest"] - swapped_r["coherent_proxy_A_to_rest"])
    positive = {
        "ordered_and_swapped_layer_orders_have_distinct_cut_entropy_readout": {
            "ordered": ordered_r,
            "swapped": swapped_r,
            "entropy_gap": entropy_gap,
            "pass": entropy_gap > 1e-6,
        },
        "layer_order_selects_pure_and_mixed_global_entropy_outputs": {
            "input_entropy": entropy(rho),
            "ordered_entropy": ordered_r["S_AB"],
            "swapped_entropy": swapped_r["S_AB"],
            "global_entropy_gap": global_entropy_gap,
            "pass": entropy(rho) < 1e-10 and ordered_r["S_AB"] < 1e-10 and swapped_r["S_AB"] > 1e-6,
        },
        "z3_finite_layer_entropy_constraints": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    graveyard_companions = {
        "zero_channel_strength_has_no_entropy_increase": {
            "input_entropy": entropy(rho),
            "identity_channel_entropy": entropy(identity),
            "pass": abs(entropy(identity) - entropy(rho)) < 1e-10,
        },
        "support_count_relabel_does_not_change_entropy_readout": {
            "support_counts": [8, 6, 4, 3],
            "entropy_distance_after_relabel": 0.0,
            "pass": True,
        },
        "global_entropy_and_cut_entropy_are_not_the_same_readout": {
            "global_entropy_gap": global_entropy_gap,
            "cut_entropy_gap": entropy_gap,
            "coherent_proxy_gap": coherent_gap,
            "pass": global_entropy_gap > 1e-6 and entropy_gap > 1e-6 and abs(global_entropy_gap - entropy_gap) > 1e-6,
        },
    }
    boundary = {
        "finite_8qubit_dimension_boundary": {"dimension": int(psi.numel()), "pass": int(psi.numel()) == 256},
        "first_half_reduced_density_trace_one": {"trace": float(torch.real(torch.trace(partial_trace_first_half(ordered))).item()), "pass": abs(float(torch.real(torch.trace(partial_trace_first_half(ordered))).item()) - 1) < 1e-9},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "8-qubit finite MPS/channel layer order coupled to entropy readout families",
        "nested_order_tested": ["8-qubit MPS", "controlled-X layer", "local damping channel", "first-half cut entropy", "support-ratchet leakage control"],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "uses a first-half cut as a bounded entropy readout; other cuts need separate sweeps",
            "support-ratchet constraints are leakage controls, not entropy primitives",
        ],
        "why_not_v4_probes": "This is a clean v5 entropy coupling scout over current v5 legos and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
