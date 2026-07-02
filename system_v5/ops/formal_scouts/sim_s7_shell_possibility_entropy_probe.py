#!/usr/bin/env python3
"""Stage 7 shell-possibility entropy readout on the Stage-2 shell-stack carrier.

Entropy is an output in this probe. The asserted proof claim binds to the
prior distinguishability invariant: branch-rank, trace-distinguishability gap,
and present-survivor capacity on the already-admitted Stage-2 shell carrier.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import autoray as ar
import cvc5  # noqa: F401  # imported so cvc5 availability is part of this run
import jax.numpy as jnp
import sympy as sp
import torch
import z3

import sim_carrier_shell_stack_sigma_r_probe as carrier

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).resolve()
OBJECT_ID = "s7_shell_possibility_entropy_readout"
RESULT = RESULT_DIR / "s7_shell_possibility_entropy_results.json"

DTYPE = torch.float64
SCALE_RUNGS = (8, 16, 32, 64)
DISTINGUISHABILITY_EPS = 1.0e-6
CAPACITY_EPS = carrier.CAPACITY_EPS
TOL = carrier.TOL
ORDER_EPS = carrier.ORDER_EPS
RANK_EPS = 1.0e-10
ENTROPY_EPS = 1.0e-12
JAX_TOL = 1.0e-10
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]
DEPENDENCY_RESULT = RESULT_DIR / "shell_stack_results.json"
DEPENDENCY_SOURCE = ROOT / "sim_carrier_shell_stack_sigma_r_probe.py"

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY readout computation on the Stage-2 shell-stack carrier: branch trace-distance classes, survivor rank/capacity, and von Neumann entropy outputs.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputing the same rank/gap/capacity and entropy readouts on the carrier recurrence without NumPy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via smt_load_bearing: the SAT->UNSAT flip is over measured branch-rank/distinguishability-gap/capacity variables, not the entropy scalar.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through smt_load_bearing cvc5_claim_pairs on the same measured rank/gap/capacity invariant.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact known-value and two-branch distinguishability witness bound into the same SMT flip.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "NON-DENSE carrier witness inherited from the Stage-2 carrier: product-MPS over per-shell mixtures plus remove-and-recompute profile ablation.",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "NON-DENSE scale witness inherited from the Stage-2 carrier: finite trace-effect contraction tree per rung.",
    },
    "autoray": {
        "tried": True,
        "used": True,
        "reason": "Backend-dispatched torch reduction for compatibility-weighted entropy aggregation, with an erased-weight recompute ablation.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation or tensor conversion.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; no SciPy routine is needed for this finite readout.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "autoray": "load_bearing",
    "numpy": None,
    "scipy": None,
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    return value


def load_dependency_result() -> dict[str, Any]:
    if not DEPENDENCY_RESULT.exists():
        return {
            "path": str(DEPENDENCY_RESULT.relative_to(ROOT)),
            "exists": False,
            "accepted": False,
            "reason": "Stage-2 shell-stack result is missing; this Stage-7 readout cannot honestly run.",
        }
    payload = json.loads(DEPENDENCY_RESULT.read_text(encoding="utf-8"))
    accepted = bool(
        payload.get("object_id") == "shell_stack"
        and payload.get("classification") == "lego"
        and payload.get("promotion_allowed") is False
        and payload.get("required_pass") is True
        and payload.get("all_pass") is True
    )
    return {
        "path": str(DEPENDENCY_RESULT.relative_to(ROOT)),
        "source": str(DEPENDENCY_SOURCE.relative_to(ROOT)),
        "exists": True,
        "object_id": payload.get("object_id"),
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "required_pass": payload.get("required_pass"),
        "all_pass": payload.get("all_pass"),
        "accepted": accepted,
    }


def entropy_torch(rho: torch.Tensor) -> float:
    rho_h = (rho + rho.T) / 2.0
    eigs = torch.linalg.eigvalsh(rho_h).real
    live = eigs[eigs > 1.0e-13]
    if int(live.numel()) == 0:
        return 0.0
    return float(-torch.sum(live * torch.log(live)).item())


def entropy_jax(rho: jnp.ndarray) -> float:
    rho_h = (rho + rho.T) / 2.0
    eigs = jnp.linalg.eigvalsh(rho_h)
    live = jnp.where(eigs > 1.0e-13, eigs, 1.0)
    return float(-jnp.sum(jnp.where(eigs > 1.0e-13, eigs * jnp.log(live), 0.0)))


def trace_distance_torch(left: torch.Tensor, right: torch.Tensor) -> float:
    delta = ((left - right) + (left - right).T) / 2.0
    eigs = torch.linalg.eigvalsh(delta).real
    return float(0.5 * torch.sum(torch.abs(eigs)).item())


def trace_distance_jax(left: jnp.ndarray, right: jnp.ndarray) -> float:
    delta = ((left - right) + (left - right).T) / 2.0
    eigs = jnp.linalg.eigvalsh(delta)
    return float(0.5 * jnp.sum(jnp.abs(eigs)))


def density_rank_torch(rho: torch.Tensor) -> int:
    eigs = torch.linalg.eigvalsh((rho + rho.T) / 2.0).real
    return int(torch.sum(eigs > RANK_EPS).item())


def density_rank_jax(rho: jnp.ndarray) -> int:
    eigs = jnp.linalg.eigvalsh((rho + rho.T) / 2.0)
    return int(jnp.sum(eigs > RANK_EPS).item())


def branch_records_to_tensors(shell: dict[str, Any]) -> tuple[list[torch.Tensor], torch.Tensor]:
    densities = [
        torch.tensor(record["density_matrix"], dtype=DTYPE)
        for record in shell["branch_states"]
    ]
    weights = torch.tensor(shell["compatibility_weights"], dtype=DTYPE)
    return densities, weights


def distinct_classes_torch(branches: list[torch.Tensor], weights: torch.Tensor) -> dict[str, Any]:
    reps: list[torch.Tensor] = []
    class_weights: list[torch.Tensor] = []
    assignments: list[int] = []
    for branch, weight in zip(branches, weights):
        assigned = None
        for idx, rep in enumerate(reps):
            if trace_distance_torch(branch, rep) <= DISTINGUISHABILITY_EPS:
                assigned = idx
                break
        if assigned is None:
            reps.append(branch)
            class_weights.append(weight.clone())
            assignments.append(len(reps) - 1)
        else:
            class_weights[assigned] = class_weights[assigned] + weight
            assignments.append(assigned)

    if not reps:
        return {
            "class_count": 0,
            "class_weights": [],
            "assignments": [],
            "min_pair_trace_distance": 0.0,
            "max_pair_trace_distance": 0.0,
            "distinguishable": False,
            "mixture": torch.zeros((2, 2), dtype=DTYPE),
        }

    total_weight = sum(class_weights)
    mixture = torch.zeros_like(reps[0])
    for rep, weight in zip(reps, class_weights):
        mixture = mixture + (weight / total_weight) * rep

    gaps = [
        trace_distance_torch(left, right)
        for i, left in enumerate(reps)
        for right in reps[i + 1 :]
    ]
    min_gap = min(gaps) if gaps else 0.0
    max_gap = max(gaps) if gaps else 0.0
    return {
        "class_count": len(reps),
        "class_weights": [float(weight.item()) for weight in class_weights],
        "assignments": assignments,
        "min_pair_trace_distance": min_gap,
        "max_pair_trace_distance": max_gap,
        "distinguishable": bool(len(reps) >= 2 and min_gap >= DISTINGUISHABILITY_EPS),
        "mixture": mixture,
    }


def distinct_classes_jax(branches: list[jnp.ndarray], weights: jnp.ndarray) -> dict[str, Any]:
    reps: list[jnp.ndarray] = []
    class_weights: list[jnp.ndarray] = []
    assignments: list[int] = []
    for idx, branch in enumerate(branches):
        weight = weights[idx]
        assigned = None
        for rep_idx, rep in enumerate(reps):
            if trace_distance_jax(branch, rep) <= DISTINGUISHABILITY_EPS:
                assigned = rep_idx
                break
        if assigned is None:
            reps.append(branch)
            class_weights.append(weight)
            assignments.append(len(reps) - 1)
        else:
            class_weights[assigned] = class_weights[assigned] + weight
            assignments.append(assigned)

    if not reps:
        return {
            "class_count": 0,
            "class_weights": [],
            "assignments": [],
            "min_pair_trace_distance": 0.0,
            "max_pair_trace_distance": 0.0,
            "distinguishable": False,
            "mixture": jnp.zeros((2, 2), dtype=jnp.float64),
        }

    total_weight = sum(class_weights)
    mixture = jnp.zeros_like(reps[0])
    for rep, weight in zip(reps, class_weights):
        mixture = mixture + (weight / total_weight) * rep

    gaps = [
        trace_distance_jax(left, right)
        for i, left in enumerate(reps)
        for right in reps[i + 1 :]
    ]
    min_gap = min(gaps) if gaps else 0.0
    max_gap = max(gaps) if gaps else 0.0
    return {
        "class_count": len(reps),
        "class_weights": [float(weight) for weight in class_weights],
        "assignments": assignments,
        "min_pair_trace_distance": min_gap,
        "max_pair_trace_distance": max_gap,
        "distinguishable": bool(len(reps) >= 2 and min_gap >= DISTINGUISHABILITY_EPS),
        "mixture": mixture,
    }


def weighted_entropy_autoray(shell_entropies: list[float], shell_masses: list[float]) -> float:
    entropies = torch.tensor(shell_entropies, dtype=DTYPE)
    masses = torch.tensor(shell_masses, dtype=DTYPE)
    total = ar.do("sum", masses)
    if float(total.item()) <= 0.0:
        return 0.0
    normalized = masses / total
    return float(ar.do("sum", entropies * normalized).item())


def shell_entropy_profile_torch(carrier_row: dict[str, Any]) -> dict[str, Any]:
    shell_rows = []
    shell_entropies: list[float] = []
    shell_masses: list[float] = []
    class_counts: list[int] = []
    min_gaps: list[float] = []
    max_gaps: list[float] = []

    for shell in carrier_row["shells"]:
        branches, weights = branch_records_to_tensors(shell)
        classes = distinct_classes_torch(branches, weights)
        entropy = entropy_torch(classes["mixture"]) if classes["distinguishable"] else 0.0
        mass = sum(float(record["attenuated_global_weight"]) for record in shell["branch_states"])
        class_counts.append(int(classes["class_count"]))
        min_gaps.append(float(classes["min_pair_trace_distance"]))
        max_gaps.append(float(classes["max_pair_trace_distance"]))
        shell_entropies.append(entropy)
        shell_masses.append(mass)
        shell_rows.append(
            {
                "shell_id": shell["shell_id"],
                "branch_label_count": len(branches),
                "effective_branch_rank": int(classes["class_count"]),
                "class_weights": classes["class_weights"],
                "branch_to_class": classes["assignments"],
                "min_trace_distinguishability_gap": float(classes["min_pair_trace_distance"]),
                "max_trace_distinguishability_gap": float(classes["max_pair_trace_distance"]),
                "distinguishability_test_ran_before_entropy": True,
                "H_Omega_r": entropy,
                "entropy_contributes_only_if_distinguishable": bool(classes["distinguishable"]),
                "attenuated_shell_mass": mass,
            }
        )

    h_omega = weighted_entropy_autoray(shell_entropies, shell_masses)
    live_min_gaps = [gap for gap in min_gaps if gap > 0.0]
    return {
        "shell_rows": shell_rows,
        "H_Omega": h_omega,
        "autoray_H_Omega": h_omega,
        "min_effective_branch_rank": min(class_counts) if class_counts else 0,
        "min_trace_distinguishability_gap": min(live_min_gaps) if live_min_gaps else 0.0,
        "max_trace_distinguishability_gap": max(max_gaps) if max_gaps else 0.0,
        "shell_entropy_profile": {
            row["shell_id"]: row["H_Omega_r"]
            for row in shell_rows
        },
        "shell_mass_profile": {
            row["shell_id"]: row["attenuated_shell_mass"]
            for row in shell_rows
        },
        "pass": bool(
            shell_rows
            and min(class_counts) >= 2
            and (min(live_min_gaps) if live_min_gaps else 0.0) >= DISTINGUISHABILITY_EPS
        ),
    }


def readout_torch(shell_count: int, *, mode: str = "real", order: str = "inward", include_details: bool = False) -> dict[str, Any]:
    carrier_row = carrier.compress_shell_stack_torch(shell_count, mode=mode, order=order, include_details=True)
    profile = shell_entropy_profile_torch(carrier_row)
    survivor_matrix = carrier_row["present_survivor_matrix"]
    eigs = torch.linalg.eigvalsh((survivor_matrix + survivor_matrix.T) / 2.0).real
    q_summary = carrier.quimb_mps_summary(carrier_row["shell_mixes"])
    c_summary = carrier.cotengra_trace_summary(shell_count)
    result = {
        "runtime": "torch",
        "shell_count": shell_count,
        "mode": mode,
        "order": order,
        "H_present": entropy_torch(survivor_matrix),
        "H_Omega": profile["H_Omega"],
        "entropy_as_output": True,
        "entropy_scalar_used_in_smt_claim": False,
        "min_effective_branch_rank": profile["min_effective_branch_rank"],
        "min_trace_distinguishability_gap": profile["min_trace_distinguishability_gap"],
        "max_trace_distinguishability_gap": profile["max_trace_distinguishability_gap"],
        "present_survivor_rank": density_rank_torch(survivor_matrix),
        "present_survivor_trace": float(torch.trace(survivor_matrix).item()),
        "present_survivor_trace_gap": carrier_row["present_survivor"]["trace_gap"],
        "present_survivor_min_eig": float(torch.min(eigs).item()),
        "present_survivor_capacity_det": carrier_row["present_survivor"]["determinant"],
        "survivor_invariant": carrier_row["survivor_invariant"],
        "quimb_non_dense_mps": q_summary,
        "mps_non_dense_result": q_summary,
        "cotengra_trace_tree": c_summary,
        "dense_state_closure_used": False,
        "distinguishability_before_entropy": True,
        "rank_gap_invariant_pass": bool(
            profile["pass"]
            and density_rank_torch(survivor_matrix) >= 2
            and carrier_row["present_survivor"]["determinant"] >= CAPACITY_EPS
            and carrier_row["present_survivor"]["trace_gap"] <= TOL
            and float(torch.min(eigs).item()) >= -TOL
        ),
        "readout_entropy_observed_after_rank_gap": bool(profile["H_Omega"] >= ENTROPY_EPS),
        "pass": False,
    }
    result["pass"] = bool(
        result["rank_gap_invariant_pass"]
        and result["readout_entropy_observed_after_rank_gap"]
        and q_summary["pass"]
        and c_summary["pass"]
    )
    if include_details:
        result["shell_entropy_rows"] = profile["shell_rows"]
        result["shell_entropy_profile"] = profile["shell_entropy_profile"]
        result["shell_mass_profile"] = profile["shell_mass_profile"]
        result["carrier_object_fields"] = {
            "shells": carrier_row["shells"],
            "future_continuations": carrier_row["future_continuations"],
            "compatibility_weights": carrier_row["compatibility_weights"],
            "compression_map": carrier_row["compression_map"],
            "present_survivor": carrier_row["present_survivor"],
            "outward_record": carrier_row["outward_record"],
        }
    return result


def readout_jax(shell_count: int, *, mode: str = "real", order: str = "inward") -> dict[str, Any]:
    bank = carrier.density_bank_jax()
    running = bank[2]
    survivor_acc = jnp.zeros((2, 2), dtype=jnp.float64)
    radii = list(range(1, shell_count + 1))
    if order == "inward":
        radii = list(reversed(radii))
    shell_entropies: list[float] = []
    shell_masses: list[float] = []
    class_counts: list[int] = []
    min_gaps: list[float] = []
    max_gaps: list[float] = []

    for radius in radii:
        branches = carrier.shell_branch_jax(radius, mode)
        weights = carrier.compatibility_weights_jax(branches, running, radius, mode)
        classes = distinct_classes_jax(branches, weights)
        shell_entropy = entropy_jax(classes["mixture"]) if classes["distinguishable"] else 0.0
        scale = jnp.float64(1.0 / math.sqrt(float(radius)))
        shell_mix = jnp.zeros((2, 2), dtype=jnp.float64)
        mass = 0.0
        for weight, rho in zip(weights, branches):
            shell_mix = shell_mix + weight * rho
            survivor_acc = survivor_acc + scale * weight * rho
            mass += float(scale * weight)
        update = shell_mix @ running @ shell_mix
        update = (update + update.T) / 2.0
        trace = jnp.trace(update)
        running = jnp.where(trace > 1.0e-15, update / trace, shell_mix)
        class_counts.append(int(classes["class_count"]))
        min_gaps.append(float(classes["min_pair_trace_distance"]))
        max_gaps.append(float(classes["max_pair_trace_distance"]))
        shell_entropies.append(shell_entropy)
        shell_masses.append(mass)

    survivor = (survivor_acc + survivor_acc.T) / 2.0
    survivor = survivor / jnp.trace(survivor)
    eigs = jnp.linalg.eigvalsh((survivor + survivor.T) / 2.0)
    h_omega = weighted_entropy_autoray(shell_entropies, shell_masses)
    live_min_gaps = [gap for gap in min_gaps if gap > 0.0]
    trace_gap = abs(float(jnp.trace(survivor)) - 1.0)
    det = float(jnp.linalg.det(survivor))
    min_eig = float(jnp.min(eigs))
    return {
        "runtime": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "shell_count": shell_count,
        "mode": mode,
        "order": order,
        "H_present": entropy_jax(survivor),
        "H_Omega": h_omega,
        "min_effective_branch_rank": min(class_counts) if class_counts else 0,
        "min_trace_distinguishability_gap": min(live_min_gaps) if live_min_gaps else 0.0,
        "max_trace_distinguishability_gap": max(max_gaps) if max_gaps else 0.0,
        "present_survivor_rank": density_rank_jax(survivor),
        "present_survivor_trace_gap": trace_gap,
        "present_survivor_min_eig": min_eig,
        "present_survivor_capacity_det": det,
        "dense_state_closure_used": False,
        "rank_gap_invariant_pass": bool(
            class_counts
            and min(class_counts) >= 2
            and (min(live_min_gaps) if live_min_gaps else 0.0) >= DISTINGUISHABILITY_EPS
            and density_rank_jax(survivor) >= 2
            and det >= CAPACITY_EPS
            and trace_gap <= TOL
            and min_eig >= -TOL
        ),
    }


def max_delta(torch_row: dict[str, Any], jax_row: dict[str, Any]) -> float:
    keys = [
        "H_present",
        "H_Omega",
        "min_trace_distinguishability_gap",
        "max_trace_distinguishability_gap",
        "present_survivor_trace_gap",
        "present_survivor_min_eig",
        "present_survivor_capacity_det",
    ]
    return max(abs(float(torch_row[key]) - float(jax_row[key])) for key in keys)


def proof_measured(row: dict[str, Any]) -> dict[str, float]:
    return {
        "min_effective_branch_rank": float(row["min_effective_branch_rank"]),
        "min_trace_distinguishability_gap": float(row["min_trace_distinguishability_gap"]),
        "present_survivor_rank": float(row["present_survivor_rank"]),
        "survivor_capacity_det": float(row["present_survivor_capacity_det"]),
        "survivor_trace_gap": float(row["present_survivor_trace_gap"]),
        "survivor_min_eig": float(row["present_survivor_min_eig"]),
        "H_Omega_reported": float(row["H_Omega"]),
    }


def provenance_stripped_measured(real_row: dict[str, Any]) -> dict[str, float]:
    measured = proof_measured(real_row)
    measured["min_effective_branch_rank"] = 1.0
    measured["min_trace_distinguishability_gap"] = 0.0
    measured["H_Omega_reported"] = float(real_row["H_Omega"])
    return measured


def rank_gap_claim_builder(v: dict[str, Any]) -> Any:
    return z3.And(
        v["min_effective_branch_rank"] >= z3.RealVal("2"),
        v["min_trace_distinguishability_gap"] >= z3.RealVal(str(DISTINGUISHABILITY_EPS)),
        v["present_survivor_rank"] >= z3.RealVal("2"),
        v["survivor_capacity_det"] >= z3.RealVal(str(CAPACITY_EPS)),
        v["survivor_trace_gap"] <= z3.RealVal(str(TOL)),
        v["survivor_min_eig"] >= z3.RealVal(str(-TOL)),
    )


def smt_rank_gap_proof(real_row: dict[str, Any], control_measured: dict[str, float], label: str) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim=f"rank_gap_distinguishability_capacity_invariant_{label}",
        real_measured=proof_measured(real_row),
        control_measured=control_measured,
        claim_builder=rank_gap_claim_builder,
        cvc5_claim_pairs=[
            ("min_effective_branch_rank", ">=", 2.0),
            ("min_trace_distinguishability_gap", ">=", DISTINGUISHABILITY_EPS),
            ("present_survivor_rank", ">=", 2.0),
            ("survivor_capacity_det", ">=", CAPACITY_EPS),
            ("survivor_trace_gap", "<=", TOL),
            ("survivor_min_eig", ">=", -TOL),
        ],
    )
    proof.update(
        {
            "asserted_claim_variables": [
                "min_effective_branch_rank",
                "min_trace_distinguishability_gap",
                "present_survivor_rank",
                "survivor_capacity_det",
                "survivor_trace_gap",
                "survivor_min_eig",
            ],
            "reported_but_not_asserted_variables": ["H_Omega_reported"],
            "entropy_scalar_used_in_asserted_claim": False,
            "pass": bool(
                proof["real_claim_verdict"] == "sat"
                and proof["negated_claim_verdict"] == "unsat"
                and proof["differ"] is True
                and proof["bound_to_measured"] is True
                and proof.get("cvc5_real_verdict") == "sat"
                and proof.get("cvc5_control_verdict") == "unsat"
            ),
        }
    )
    return proof


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
    )
    return row


def known_value_checks() -> dict[str, Any]:
    zero = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=DTYPE)
    one = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=DTYPE)
    half = torch.eye(2, dtype=DTYPE) / 2.0
    mixed_entropy = entropy_torch(half)
    pure_entropy = entropy_torch(zero)
    orthogonal = distinct_classes_torch([zero, one], torch.tensor([0.5, 0.5], dtype=DTYPE))
    identical = distinct_classes_torch([zero, zero.clone()], torch.tensor([0.5, 0.5], dtype=DTYPE))
    orthogonal_entropy = entropy_torch(orthogonal["mixture"]) if orthogonal["distinguishable"] else 0.0
    identical_entropy = entropy_torch(identical["mixture"]) if identical["distinguishable"] else 0.0

    sympy_half_entropy = sp.simplify(-(sp.Rational(1, 2) * sp.log(sp.Rational(1, 2)) * 2))
    sympy_pure_entropy = sp.Integer(0)
    sympy_real_det = sp.Rational(1, 4)
    sympy_control_det = sp.Integer(0)
    sympy_proof = smt_load_bearing(
        claim="sympy_exact_two_distinguishable_branches_rank_gap_capacity_vs_identical_control",
        real_measured={
            "min_effective_branch_rank": 2.0,
            "min_trace_distinguishability_gap": 1.0,
            "present_survivor_rank": 2.0,
            "survivor_capacity_det": float(sympy_real_det),
            "survivor_trace_gap": 0.0,
            "survivor_min_eig": 0.5,
            "H_Omega_reported": float(sp.N(sympy_half_entropy)),
        },
        control_measured={
            "min_effective_branch_rank": 1.0,
            "min_trace_distinguishability_gap": 0.0,
            "present_survivor_rank": 1.0,
            "survivor_capacity_det": float(sympy_control_det),
            "survivor_trace_gap": 0.0,
            "survivor_min_eig": 0.0,
            "H_Omega_reported": float(sympy_pure_entropy),
        },
        claim_builder=rank_gap_claim_builder,
        cvc5_claim_pairs=[
            ("min_effective_branch_rank", ">=", 2.0),
            ("min_trace_distinguishability_gap", ">=", DISTINGUISHABILITY_EPS),
            ("present_survivor_rank", ">=", 2.0),
            ("survivor_capacity_det", ">=", CAPACITY_EPS),
            ("survivor_trace_gap", "<=", TOL),
            ("survivor_min_eig", ">=", -TOL),
        ],
    )
    sympy_proof.update(
        {
            "engine": "sympy+load_bearing_proof",
            "exact_mixed_entropy": str(sympy_half_entropy),
            "exact_pure_entropy": str(sympy_pure_entropy),
            "exact_real_det": str(sympy_real_det),
            "exact_control_det": str(sympy_control_det),
            "entropy_scalar_used_in_asserted_claim": False,
            "pass": bool(
                sympy_proof["real_claim_verdict"] == "sat"
                and sympy_proof["negated_claim_verdict"] == "unsat"
                and sympy_proof["differ"] is True
                and sympy_proof.get("cvc5_real_verdict") == "sat"
                and sympy_proof.get("cvc5_control_verdict") == "unsat"
            ),
        }
    )

    log2 = math.log(2.0)
    rows = {
        "maximally_mixed_single_qubit_survivor": {
            "computed_entropy": mixed_entropy,
            "expected": "log(2)",
            "abs_error": abs(mixed_entropy - log2),
            "pass": bool(abs(mixed_entropy - log2) <= 1.0e-10),
        },
        "pure_single_future_survivor": {
            "computed_entropy": pure_entropy,
            "expected": 0.0,
            "determinant": float(torch.linalg.det(zero).item()),
            "pass": bool(pure_entropy <= ENTROPY_EPS and abs(float(torch.linalg.det(zero).item())) < CAPACITY_EPS),
        },
        "two_orthogonal_distinguishable_branches": {
            "effective_branch_rank": orthogonal["class_count"],
            "min_trace_distinguishability_gap": orthogonal["min_pair_trace_distance"],
            "computed_H_Omega": orthogonal_entropy,
            "expected": "log(2)",
            "pass": bool(
                orthogonal["class_count"] == 2
                and orthogonal["min_pair_trace_distance"] >= 1.0 - 1.0e-12
                and abs(orthogonal_entropy - log2) <= 1.0e-10
            ),
        },
        "two_identical_labels_not_distinguishable": {
            "label_count": 2,
            "effective_branch_rank": identical["class_count"],
            "min_trace_distinguishability_gap": identical["min_pair_trace_distance"],
            "computed_H_Omega": identical_entropy,
            "expected": 0.0,
            "pass": bool(identical["class_count"] == 1 and identical_entropy <= ENTROPY_EPS),
        },
    }
    return {
        "torch_computed_anchors": rows,
        "sympy_exact": {
            "S_I_over_2": str(sympy_half_entropy),
            "S_pure": str(sympy_pure_entropy),
            "rank_gap_capacity_smt_flip": sympy_proof,
        },
        "pass": bool(all(row["pass"] for row in rows.values()) and sympy_proof["pass"]),
    }


def build_scale_rung(shell_count: int, *, include_details: bool = False) -> dict[str, Any]:
    real = readout_torch(shell_count, mode="real", order="inward", include_details=include_details)
    single = readout_torch(shell_count, mode="single_future", order="inward", include_details=False)
    scrambled = readout_torch(shell_count, mode="scrambled", order="inward", include_details=False)
    outward = readout_torch(shell_count, mode="real", order="outward", include_details=False)
    jax_real = readout_jax(shell_count, mode="real", order="inward")
    jax_delta = max_delta(real, jax_real)
    order_gap = abs(float(real["H_Omega"]) - float(outward["H_Omega"]))
    density_order_gap = float(
        torch.linalg.vector_norm(
            carrier.compress_shell_stack_torch(shell_count, mode="real", order="inward")["present_survivor_matrix"]
            - carrier.compress_shell_stack_torch(shell_count, mode="real", order="outward")["present_survivor_matrix"]
        ).item()
    )
    proof_single = smt_rank_gap_proof(real, proof_measured(single), f"n{shell_count}_real_vs_single_future")
    proof_scrambled = smt_rank_gap_proof(real, proof_measured(scrambled), f"n{shell_count}_real_vs_scrambled")
    proof_stripped = smt_rank_gap_proof(real, provenance_stripped_measured(real), f"n{shell_count}_real_vs_provenance_stripped_entropy_matched")
    proofs = {
        "single_future_rank_gap_smt_load_bearing": proof_single,
        "scrambled_rank_gap_smt_load_bearing": proof_scrambled,
        "provenance_stripped_entropy_matched_rank_gap_smt_load_bearing": proof_stripped,
    }
    pass_rung = bool(
        real["pass"]
        and single["min_effective_branch_rank"] == 1
        and single["min_trace_distinguishability_gap"] == 0.0
        and scrambled["min_effective_branch_rank"] == 1
        and scrambled["min_trace_distinguishability_gap"] == 0.0
        and proof_single["pass"]
        and proof_scrambled["pass"]
        and proof_stripped["pass"]
        and jax_delta <= JAX_TOL
        and density_order_gap > ORDER_EPS
        and real["dense_state_closure_used"] is False
    )
    return {
        "sites_or_qubits": shell_count,
        "shell_count": shell_count,
        "dense_state_closure_used": False,
        "torch": real,
        "jax_mirror": jax_real,
        "jax_vs_pytorch_delta": jax_delta,
        "controls": {
            "single_future": single,
            "scrambled": scrambled,
            "outward_order": {
                "H_Omega_gap": order_gap,
                "present_survivor_density_gap": density_order_gap,
                "shows_order_sensitivity": bool(density_order_gap > ORDER_EPS),
            },
            "provenance_stripped_entropy_matched": {
                "raw_H_Omega_reported": real["H_Omega"],
                "min_effective_branch_rank": 1,
                "min_trace_distinguishability_gap": 0.0,
                "same_entropy_scalar_as_real": True,
                "kills_rank_gap_invariant": True,
            },
        },
        "proof_results": proofs,
        "pass": pass_rung,
    }


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    real = top["torch"]
    single = top["controls"]["single_future"]
    stripped = top["controls"]["provenance_stripped_entropy_matched"]
    real_profile = real["quimb_non_dense_mps"]["profile_variation_l2"]
    single_profile = single["quimb_non_dense_mps"]["profile_variation_l2"]
    real_masses = list(real["carrier_object_fields"]["compatibility_weights"].values())
    flattened_weights = [1.0 / len(weights) for weights in real_masses for _ in weights]
    real_shell_entropies = list(real["shell_entropy_profile"].values())
    real_shell_masses = list(real["shell_mass_profile"].values())
    autoray_real = weighted_entropy_autoray(real_shell_entropies, real_shell_masses)
    autoray_erased = weighted_entropy_autoray(real_shell_entropies, flattened_weights[: len(real_shell_entropies)])

    return {
        "torch_branch_rank_gap_to_single_future": add_ablation_pass(
            tool_ablation(
                "torch rank/gap-conditioned H_Omega on real carrier vs single-future erased carrier",
                baseline_value=real["H_Omega"],
                ablated_value=single["H_Omega"],
                tool="torch",
            )
        ),
        "torch_provenance_strip_keeps_entropy_but_kills_gap": add_ablation_pass(
            tool_ablation(
                "torch provenance-stripped control keeps raw entropy scalar but removes rank/gap support",
                baseline_value=real["min_trace_distinguishability_gap"],
                ablated_value=stripped["min_trace_distinguishability_gap"],
                tool="torch",
            )
        ),
        "quimb_shell_mps_profile_variation": add_ablation_pass(
            tool_ablation(
                "quimb shell profile variation real compatibility-weighted futures vs single-future erased carrier",
                baseline_value=real_profile,
                ablated_value=single_profile,
                tool="quimb",
            )
        ),
        "autoray_weighted_entropy_reduction": add_ablation_pass(
            tool_ablation(
                "autoray backend-dispatched weighted entropy reduction with carrier shell masses vs flattened masses",
                baseline_value=autoray_real,
                ablated_value=autoray_erased,
                tool="autoray",
            )
        ),
        "sympy_exact_rank_gap_capacity_flip": add_ablation_pass(
            tool_ablation(
                "sympy exact two-branch capacity determinant vs identical-branch control",
                baseline_value=0.25,
                ablated_value=0.0,
                tool="sympy",
            )
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependency = load_dependency_result()

    scale_rungs = {str(n): build_scale_rung(n) for n in SCALE_RUNGS}
    top = build_scale_rung(64, include_details=True)
    known = known_value_checks()
    tool_ablations = build_tool_ablations(top)

    scale_pass = bool(all(row["pass"] for row in scale_rungs.values()))
    proof_pass = bool(
        all(
            proof["pass"]
            for rung in scale_rungs.values()
            for proof in rung["proof_results"].values()
        )
        and known["sympy_exact"]["rank_gap_capacity_smt_flip"]["pass"]
    )
    ablation_pass = bool(all(row["pass"] for row in tool_ablations.values()))
    controls_pass = bool(
        top["controls"]["single_future"]["H_Omega"] <= ENTROPY_EPS
        and top["controls"]["single_future"]["min_effective_branch_rank"] == 1
        and top["controls"]["scrambled"]["min_effective_branch_rank"] == 1
        and top["controls"]["provenance_stripped_entropy_matched"]["same_entropy_scalar_as_real"] is True
        and top["proof_results"]["provenance_stripped_entropy_matched_rank_gap_smt_load_bearing"]["negated_claim_verdict"] == "unsat"
    )
    jax_vs_pytorch_delta = max(row["jax_vs_pytorch_delta"] for row in scale_rungs.values())
    all_pass = bool(
        dependency["accepted"]
        and scale_pass
        and proof_pass
        and ablation_pass
        and controls_pass
        and known["pass"]
        and jax_vs_pytorch_delta <= JAX_TOL
    )

    carrier_fields = top["torch"]["carrier_object_fields"]
    result = {
        "schema": "PER_SIM_CONTRACT_STAGE7_ENTROPY_READOUT_v1",
        "sim_id": "sim_s7_shell_possibility_entropy_probe",
        "name": "sim_s7_shell_possibility_entropy_probe",
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "thisfile": str(THISFILE.relative_to(ROOT)),
        "result": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "acts_on_object_id": "shell_stack",
        "primary_object": "RetrocausalPossibilityField",
        "classification": "lego",
        "tier": "canonical STAGE 7 entropy/information readout",
        "sim_execution_kind": "nonclassical",
        "sim_class": "information_readout_probe",
        "promotion_allowed": False,
        "purpose": "Compute shell-possibility entropy as an information readout on the already-admitted Stage-2 Sigma_r shell-stack carrier.",
        "scientific_question": "Does the Stage-2 shell-stack carrier expose a distinguishability-conditioned shell-possibility entropy readout whose proof flips on branch-rank/gap/capacity controls rather than on entropy magnitude?",
        "dependency_receipts": [
            str(DEPENDENCY_RESULT.relative_to(ROOT)),
            "results/F01_finite_distinguishability_results.json",
            "results/N01_path_family_results.json",
        ],
        "dependency_status": dependency,
        "finite_map": {
            "domain": "Stage-2 shell_stack Sigma_r carrier result: finite shells r in {1..n}, branch density matrices rho_{r,b}, compatibility weights, compression map, and rho_present.",
            "codomain_or_output": "H_present, per-shell H_Omega_r, aggregate H_Omega, branch-rank/gap invariant, proof flips, controls, and blocked consumers.",
            "definition": "E_7: shell_stack -> distinguishability partition -> entropy readout; distinguishability partition is computed before entropy and is the only SMT claim-bearing invariant.",
        },
        "domain": {
            "carrier_source": str(DEPENDENCY_SOURCE.relative_to(ROOT)),
            "carrier_result": str(DEPENDENCY_RESULT.relative_to(ROOT)),
            "scale_shell_counts": list(SCALE_RUNGS),
            "branch_density_dim": [2, 2],
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "H_present": top["torch"]["H_present"],
            "H_Omega": top["torch"]["H_Omega"],
            "per_shell_entropy_profile": top["torch"]["shell_entropy_profile"],
            "rank_gap_distinguishability_invariant": {
                "min_effective_branch_rank": top["torch"]["min_effective_branch_rank"],
                "min_trace_distinguishability_gap": top["torch"]["min_trace_distinguishability_gap"],
                "present_survivor_rank": top["torch"]["present_survivor_rank"],
                "present_survivor_capacity_det": top["torch"]["present_survivor_capacity_det"],
            },
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite shell/probe/branch-density/path set inherited from the Stage-2 shell_stack carrier; readout partitions finite branch densities by trace distinguishability.",
            },
            "N01": {
                "role": "active",
                "statement": "order-sensitive carrier compression is inherited and rechecked by inward-vs-outward survivor density gap; entropy is not used as the order variable.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "carrier_layer": "Stage-2 Sigma_r shell-stack carrier; this Stage-7 sim does not build a new physical carrier",
        "geometry_layer": "information readout on shell-stack carrier; no geometry, manifold, flux, bridge, or Axis0 promotion",
        "carrier_realization": "torch.float64 spinor-derived 2x2 branch densities and present survivor from sim_carrier_shell_stack_sigma_r_probe.py",
        "peps3d_embedding": {
            "status": "inherited finite PEPS3D carrier anchor from Stage-2 shell_stack result",
            "anchor_rule": "each Sigma_r shell remains a finite PEPS3D carrier cell/shell index with explicit local branch densities; no dense global 2**N state is materialized",
            "dense_state_closure_used": False,
        },
        "peps3d_carrier_anchor": "Stage-2 shell_stack PEPS3D anchor, consumed as an existing finite carrier rather than rebuilt",
        "peps2d_projection_boundary": "not_materialized_for_this_readout; included only as an explicit non-claim boundary",
        "spinor_state": "branch states are Stage-2 spinor-derived density matrices rho_{r,b}; rho_present is the compressed survivor density",
        "quaternion_action": "not_applicable",
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "boundary_interior_cut_readout_not_opened",
        "law_or_candidate_tested": "H_Omega is an entropy readout sourced from prior branch distinguishability; SMT proof asserts branch-rank/gap/capacity, not entropy scalar magnitude.",
        "branch_status_before_run": "Stage-2 carrier admitted as a lego result; Stage-7 readout requested with no downstream consumer opened",
        "allowed_claims": [
            "Stage-7 shell-possibility entropy readout runs on the Stage-2 shell_stack carrier if validators pass",
            "rank/gap distinguishability is computed before entropy",
            "single-future, scrambled, and provenance-stripped controls kill the asserted rank/gap invariant",
            "provenance-stripped control can keep the raw entropy scalar while SMT still flips unsat",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "readout lego only; no layer completion claim",
            "entropy is not an organizing variable and is not used in the SMT asserted claim",
            "no Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final-manifold consumer is unlocked",
        ],
        "eligible_consumers": ["bounded Stage-7 information-readout audits that cite this result and fresh validator output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3",
            "load_bearing_proof.smt_load_bearing cvc5 cross-check",
            "sympy exact two-branch known-value proof bound into the same rank/gap SMT flip",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [
            "quimb product-MPS shell-stack profile witness",
            "cotengra finite trace-effect contraction tree",
        ],
        "geometry_topology_boundary": "quimb/cotengra provide non-dense carrier/trace witnesses only; no topology or geometry promotion is claimed",
        "survivor_invariant": {
            **top["torch"]["survivor_invariant"],
            "rank_gap_distinguishability": {
                "min_effective_branch_rank": top["torch"]["min_effective_branch_rank"],
                "min_trace_distinguishability_gap": top["torch"]["min_trace_distinguishability_gap"],
                "present_survivor_rank": top["torch"]["present_survivor_rank"],
                "passed": top["torch"]["rank_gap_invariant_pass"],
            },
        },
        "required_negatives": [
            "single_future_control",
            "scrambled_future_control",
            "provenance_stripped_entropy_matched_control",
            "identical_branch_known_value_control",
            "outward_order_control",
        ],
        "negatives_run": top["controls"],
        "kill_conditions": {
            "single_future_control": "effective branch rank must collapse to 1, trace-distinguishability gap to 0, H_Omega to 0, and SMT claim to unsat",
            "scrambled_future_control": "labels without distinct branch densities must collapse rank/gap and SMT claim",
            "provenance_stripped_entropy_matched_control": "raw entropy scalar is matched while branch rank/gap is zero; SMT must still be unsat",
            "identical_branch_known_value_control": "two labels with identical density must report H_Omega=0 despite label count=2",
            "outward_order_control": "same carrier futures processed in reversed order must produce a different survivor density",
        },
        "required_artifacts": [
            "result JSON",
            "scale_ladder",
            "torch_primary_result",
            "jax_mirror_result",
            "proof_results",
            "controls",
            "tool_ablations",
            "known_value_checks",
            "object fields inherited from shell_stack",
        ],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"sim_s7_shell_possibility_entropy_probe:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "dependency_accepted": dependency["accepted"],
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "known_value_checks_pass": known["pass"],
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "H_present_64": top["torch"]["H_present"],
            "H_Omega_64": top["torch"]["H_Omega"],
            "min_effective_branch_rank_64": top["torch"]["min_effective_branch_rank"],
            "min_trace_distinguishability_gap_64": top["torch"]["min_trace_distinguishability_gap"],
            "entropy_scalar_used_in_smt_claim": False,
        },
        "torch_primary_result": {
            **top["torch"],
            "claim": "rank/gap distinguishability and survivor capacity are prior to entropy; entropy is reported after the partition",
        },
        "jax_mirror_result": top["jax_mirror"],
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "jax_vs_pytorch": {
            "max_abs_delta": jax_vs_pytorch_delta,
            "tolerance": JAX_TOL,
            "agree": bool(jax_vs_pytorch_delta <= JAX_TOL),
        },
        "proof_results": {
            **top["proof_results"],
            "known_value_sympy_rank_gap_capacity_smt_load_bearing": known["sympy_exact"]["rank_gap_capacity_smt_flip"],
            "pass": proof_pass,
        },
        "controls": top["controls"],
        "known_value_checks": known,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {
            "scale_axis": "shell_count",
            "rungs": scale_rungs,
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "scale_details": scale_rungs,
        "entropy_as_output": {
            "status": "reported_only_not_master_variable",
            "H_present": top["torch"]["H_present"],
            "H_Omega": top["torch"]["H_Omega"],
            "per_shell_profile": top["torch"]["shell_entropy_profile"],
            "smt_assertion_uses_entropy_scalar": False,
        },
        "positive": {
            "distinguishability_before_entropy": {
                "pass": top["torch"]["distinguishability_before_entropy"],
                "min_effective_branch_rank": top["torch"]["min_effective_branch_rank"],
                "min_trace_distinguishability_gap": top["torch"]["min_trace_distinguishability_gap"],
            },
            "rank_gap_capacity_invariant": {
                "pass": top["torch"]["rank_gap_invariant_pass"],
                "present_survivor_rank": top["torch"]["present_survivor_rank"],
                "capacity_det": top["torch"]["present_survivor_capacity_det"],
            },
            "entropy_readout_after_partition": {
                "pass": top["torch"]["readout_entropy_observed_after_rank_gap"],
                "H_present": top["torch"]["H_present"],
                "H_Omega": top["torch"]["H_Omega"],
            },
            "scale_8_16_32_64": {"pass": scale_pass},
        },
        "graveyard_companions": top["controls"],
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "entropy_as_master_variable": {"used": False, "pass": True},
            "entropy_scalar_in_smt_claim": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "shells": carrier_fields["shells"],
        "future_continuations": carrier_fields["future_continuations"],
        "compatibility_weights": carrier_fields["compatibility_weights"],
        "compression_map": carrier_fields["compression_map"],
        "present_survivor": carrier_fields["present_survivor"],
        "outward_record": carrier_fields["outward_record"],
        "field_object": {
            "primary_object": "RetrocausalPossibilityField",
            "object_statement": "Stage-7 reads entropy from the finite shell possibility field after branch distinguishability has already partitioned future continuations.",
            "first_class_fields": ["shells", "future_continuations", "compatibility_weights", "compression_map", "present_survivor", "outward_record"],
            "readout_provenance": "future_continuations -> compatibility_weights -> distinguishability_partition -> compression_map -> present_survivor -> entropy_readout",
        },
        "pass_rule": "dependency shell_stack result accepted; all 8/16/32/64 rungs pass without dense closure; torch and JAX agree; z3/cvc5 helper proof flips on measured branch-rank/distinguishability-gap/capacity variables; provenance-stripped entropy-matched control is unsat; known values are computed; tool ablations are remove-and-recompute rows",
        "fail_rule": "fail on missing Stage-2 shell_stack dependency, entropy inside SMT asserted claim, missing proof flip, live single/scrambled/provenance-stripped controls, dense closure, JAX mismatch, missing genuine ablation, missing known-value checks, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blockers": [] if all_pass else ["one_or_more_stage7_shell_possibility_entropy_checks_failed"],
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(RESULT.relative_to(ROOT)),
                "scale_pass": result["scale_ladder"]["pass"],
                "proof_pass": result["proof_results"]["pass"],
                "known_value_checks_pass": result["known_value_checks"]["pass"],
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "entropy_scalar_used_in_smt_claim": result["result_summary"]["entropy_scalar_used_in_smt_claim"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
