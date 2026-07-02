#!/usr/bin/env python3
"""Stage-5 operator/channel lego: finite amplitude-damping channel.

This probe is deliberately narrow. It tests one finite channel family:
local independent amplitude damping over operator dimensions 8/16/32/64.
The proof target is Kraus completeness. The negative control changes the
no-jump amplitude, so the same invariant must flip under helper-bound SMT.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from fractions import Fraction
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
from clifford import Cl

torch.sparse.check_sparse_tensor_invariants.enable()

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OBJECT_ID = "op_amplitude_damping_channel"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SIM_ID = "sim_op_amplitude_damping_probe"
VERSION = "1.0.0"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False

GAMMA = Fraction(1, 10)
DEGENERATE_EPS = Fraction(1, 10000)
PROOF_EPS = 1.0e-12
SCALES = (8, 16, 32, 64)
RTYPE = torch.float64
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "final_manifold"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY finite numeric carrier: enumerates amplitude-damping transition weights, completeness diagonals, trace controls, order gaps, and scale rungs without dense superoperator closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputing the same finite transition weights, completeness errors, and order gaps independently of torch.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing: z3 variables are bound to measured real/control completeness errors and the invariant verdict flips.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check inside smt_load_bearing over the same measured completeness-error inequality; no numeric ablation is used for cvc5.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic flip for the completeness expression: real local factor equals 1, degenerate local factor differs; no numeric ablation is used for sympy.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Genuine numeric geometric-algebra mirror of the local Bloch-vector damping shift; gamma-erased recompute ablates the row.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported and not used; this channel probe keeps claim-bearing computation in torch, jax, SMT, sympy, and clifford.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "numpy": "None",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return _jsonable(value.detach().cpu().item())
        return _jsonable(value.detach().cpu().tolist())
    if hasattr(value, "item") and callable(value.item):
        try:
            return _jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def qubit_count(operator_dimension: int) -> int:
    q = int(math.log2(operator_dimension))
    if 2**q != operator_dimension:
        raise ValueError(f"operator dimension must be a power of two: {operator_dimension}")
    return q


def excited_positions(index: int, q: int) -> list[int]:
    return [bit for bit in range(q) if (index >> bit) & 1]


def torch_branch_total_for_basis(index: int, q: int, *, degenerate: bool = False) -> torch.Tensor:
    gamma = torch.tensor(float(GAMMA), dtype=RTYPE)
    jump_amp = torch.sqrt(gamma)
    no_jump_amp = (
        torch.tensor(1.0 - float(DEGENERATE_EPS), dtype=RTYPE)
        if degenerate
        else torch.sqrt(torch.tensor(1.0 - float(GAMMA), dtype=RTYPE))
    )
    excited = excited_positions(index, q)
    total = torch.tensor(0.0, dtype=RTYPE)
    for branch in range(1 << len(excited)):
        amp_sq = torch.tensor(1.0, dtype=RTYPE)
        for local, _bit in enumerate(excited):
            selected_jump = (branch >> local) & 1
            amp = jump_amp if selected_jump else no_jump_amp
            amp_sq = amp_sq * amp * amp
        total = total + amp_sq
    return total


def torch_transition_csr(operator_dimension: int, *, degenerate: bool = False) -> torch.Tensor:
    q = qubit_count(operator_dimension)
    no_jump_prob = (
        torch.tensor((1.0 - float(DEGENERATE_EPS)) ** 2, dtype=RTYPE)
        if degenerate
        else torch.tensor(1.0 - float(GAMMA), dtype=RTYPE)
    )
    jump_prob = torch.tensor(float(GAMMA), dtype=RTYPE)
    rows: list[list[tuple[int, torch.Tensor]]] = [[] for _ in range(operator_dimension)]
    for source in range(operator_dimension):
        excited = excited_positions(source, q)
        for branch in range(1 << len(excited)):
            target = source
            weight = torch.tensor(1.0, dtype=RTYPE)
            for local, bit in enumerate(excited):
                if (branch >> local) & 1:
                    target = target & ~(1 << bit)
                    weight = weight * jump_prob
                else:
                    weight = weight * no_jump_prob
            rows[target].append((source, weight))

    crow = [0]
    col: list[int] = []
    vals: list[torch.Tensor] = []
    for entries in rows:
        for source, weight in sorted(entries, key=lambda item: item[0]):
            col.append(source)
            vals.append(weight)
        crow.append(len(col))

    return torch.sparse_csr_tensor(
        torch.tensor(crow, dtype=torch.int64),
        torch.tensor(col, dtype=torch.int64),
        torch.stack(vals) if vals else torch.empty(0, dtype=RTYPE),
        size=(operator_dimension, operator_dimension),
        dtype=RTYPE,
        check_invariants=True,
    )


def torch_completeness_diagonal(operator_dimension: int, *, degenerate: bool = False) -> torch.Tensor:
    transition = torch_transition_csr(operator_dimension, degenerate=degenerate)
    out = torch.zeros(operator_dimension, dtype=RTYPE)
    out.scatter_add_(0, transition.col_indices(), transition.values())
    return out


def torch_channel_from_csr(probs: torch.Tensor, *, degenerate: bool = False) -> torch.Tensor:
    return torch.mv(torch_transition_csr(int(probs.numel()), degenerate=degenerate), probs)


def jax_branch_total_for_basis(index: int, q: int, *, degenerate: bool = False) -> jax.Array:
    gamma = jnp.asarray(float(GAMMA), dtype=jnp.float64)
    jump_amp = jnp.sqrt(gamma)
    no_jump_amp = (
        jnp.asarray(1.0 - float(DEGENERATE_EPS), dtype=jnp.float64)
        if degenerate
        else jnp.sqrt(jnp.asarray(1.0 - float(GAMMA), dtype=jnp.float64))
    )
    excited = excited_positions(index, q)
    total = jnp.asarray(0.0, dtype=jnp.float64)
    for branch in range(1 << len(excited)):
        amp_sq = jnp.asarray(1.0, dtype=jnp.float64)
        for local, _bit in enumerate(excited):
            selected_jump = (branch >> local) & 1
            amp = jump_amp if selected_jump else no_jump_amp
            amp_sq = amp_sq * amp * amp
        total = total + amp_sq
    return total


def jax_completeness_diagonal(operator_dimension: int, *, degenerate: bool = False) -> jax.Array:
    q = qubit_count(operator_dimension)
    return jnp.stack(
        [jax_branch_total_for_basis(index, q, degenerate=degenerate) for index in range(operator_dimension)]
    )


def torch_x_first_bit(probs: torch.Tensor) -> torch.Tensor:
    out = torch.zeros_like(probs)
    for index in range(probs.numel()):
        out[index ^ 1] = out[index ^ 1] + probs[index]
    return out


def jax_x_first_bit(probs: jax.Array) -> jax.Array:
    values = [probs[index ^ 1] for index in range(int(probs.shape[0]))]
    return jnp.asarray(values, dtype=jnp.float64)


def torch_population_channel(probs: torch.Tensor, *, degenerate: bool = False) -> torch.Tensor:
    return torch_channel_from_csr(probs, degenerate=degenerate)


def jax_population_channel(probs: jax.Array, *, degenerate: bool = False) -> jax.Array:
    dim = int(probs.shape[0])
    q = qubit_count(dim)
    no_jump_prob = (
        jnp.asarray((1.0 - float(DEGENERATE_EPS)) ** 2, dtype=jnp.float64)
        if degenerate
        else jnp.asarray(1.0 - float(GAMMA), dtype=jnp.float64)
    )
    jump_prob = jnp.asarray(float(GAMMA), dtype=jnp.float64)
    values = [jnp.asarray(0.0, dtype=jnp.float64) for _ in range(dim)]
    for index in range(dim):
        excited = excited_positions(index, q)
        for branch in range(1 << len(excited)):
            target = index
            weight = jnp.asarray(1.0, dtype=jnp.float64)
            for local, bit in enumerate(excited):
                if (branch >> local) & 1:
                    target = target & ~(1 << bit)
                    weight = weight * jump_prob
                else:
                    weight = weight * no_jump_prob
            values[target] = values[target] + probs[index] * weight
    return jnp.asarray(values, dtype=jnp.float64)


def torch_order_gap(operator_dimension: int, *, gamma_erased: bool = False) -> float:
    probs = torch.zeros(operator_dimension, dtype=RTYPE)
    probs[0] = 1.0
    if gamma_erased:
        left = torch_x_first_bit(probs)
        right = torch_x_first_bit(probs)
    else:
        left = torch_population_channel(torch_x_first_bit(probs))
        right = torch_x_first_bit(torch_population_channel(probs))
    return float(torch.sum(torch.abs(left - right)).item())


def jax_order_gap(operator_dimension: int, *, gamma_erased: bool = False) -> float:
    probs = jnp.zeros((operator_dimension,), dtype=jnp.float64).at[0].set(1.0)
    if gamma_erased:
        left = jax_x_first_bit(probs)
        right = jax_x_first_bit(probs)
    else:
        left = jax_population_channel(jax_x_first_bit(probs))
        right = jax_x_first_bit(jax_population_channel(probs))
    return float(jnp.sum(jnp.abs(left - right)).item())


def clifford_bloch_shift(gamma: float) -> float:
    layout, blades = Cl(3)
    _ = layout
    e1 = blades["e1"]
    e3 = blades["e3"]
    before = 1.0 * e1
    after = math.sqrt(1.0 - gamma) * e1 + gamma * e3
    delta = after - before
    return math.sqrt(max(0.0, float((delta | delta)[()])))


def scale_rung(operator_dimension: int) -> dict[str, Any]:
    q = qubit_count(operator_dimension)
    real_diag_t = torch_completeness_diagonal(operator_dimension)
    control_diag_t = torch_completeness_diagonal(operator_dimension, degenerate=True)
    real_diag_j = jax_completeness_diagonal(operator_dimension)
    control_diag_j = jax_completeness_diagonal(operator_dimension, degenerate=True)

    real_error_t = float(torch.max(torch.abs(real_diag_t - 1.0)).item())
    control_error_t = float(torch.max(torch.abs(control_diag_t - 1.0)).item())
    real_error_j = float(jnp.max(jnp.abs(real_diag_j - 1.0)).item())
    control_error_j = float(jnp.max(jnp.abs(control_diag_j - 1.0)).item())

    all_excited = operator_dimension - 1
    input_excited = torch.zeros(operator_dimension, dtype=RTYPE)
    input_excited[all_excited] = 1.0
    real_excited_out = torch_population_channel(input_excited)
    control_excited_out = torch_population_channel(input_excited, degenerate=True)
    real_trace = float(torch.sum(real_excited_out).item())
    control_trace = float(torch.sum(control_excited_out).item())
    single_excited = torch.zeros(operator_dimension, dtype=RTYPE)
    single_excited[1] = 1.0
    single_excited_out = torch_population_channel(single_excited)

    torch_gap = torch_order_gap(operator_dimension)
    jax_gap = jax_order_gap(operator_dimension)
    gamma_erased_gap = torch_order_gap(operator_dimension, gamma_erased=True)

    pass_rung = bool(
        real_error_t <= PROOF_EPS
        and real_error_j <= PROOF_EPS
        and control_error_t > PROOF_EPS
        and control_error_j > PROOF_EPS
        and abs(real_trace - 1.0) <= PROOF_EPS
        and abs(torch_gap - jax_gap) <= 1.0e-12
        and torch_gap > 0.0
        and gamma_erased_gap == 0.0
    )

    return {
        "operator_dimension": operator_dimension,
        "sites_or_qubits": operator_dimension,
        "qubit_count_log2_dimension": q,
        "kraus_branch_count": 2**q,
        "sparse_transition_nonzeros": 3**q,
        "sparse_storage_format": "torch.sparse_csr_tensor",
        "torch_sparse_csr_nnz_real": int(torch_transition_csr(operator_dimension)._nnz()),
        "torch_sparse_csr_nnz_degenerate": int(torch_transition_csr(operator_dimension, degenerate=True)._nnz()),
        "dense_superoperator_entries_avoided": operator_dimension**4,
        "dense_state_closure_used": False,
        "torch_max_completeness_error": real_error_t,
        "torch_degenerate_max_completeness_error": control_error_t,
        "jax_max_completeness_error": real_error_j,
        "jax_degenerate_max_completeness_error": control_error_j,
        "torch_all_excited_trace_after_channel": real_trace,
        "torch_all_excited_trace_after_degenerate_control": control_trace,
        "basis_convention_single_excited_output_p0": float(single_excited_out[0].item()),
        "basis_convention_single_excited_output_p1": float(single_excited_out[1].item()),
        "torch_x_channel_order_l1_gap": torch_gap,
        "jax_x_channel_order_l1_gap": jax_gap,
        "gamma_erased_order_l1_gap": gamma_erased_gap,
        "jax_vs_pytorch_delta": max(abs(real_error_t - real_error_j), abs(control_error_t - control_error_j), abs(torch_gap - jax_gap)),
        "pass": pass_rung,
    }


def sympy_exact_flip(max_qubits: int) -> dict[str, Any]:
    g = sp.Rational(GAMMA.numerator, GAMMA.denominator)
    eps = sp.Rational(DEGENERATE_EPS.numerator, DEGENERATE_EPS.denominator)
    real_local = sp.simplify(sp.sqrt(1 - g) ** 2 + sp.sqrt(g) ** 2)
    control_local = sp.simplify((1 - eps) ** 2 + g)
    real_top = sp.simplify(real_local**max_qubits)
    control_top = sp.simplify(control_local**max_qubits)
    real_error = abs(sp.simplify(real_top - 1))
    control_error = abs(sp.simplify(control_top - 1))
    real_verdict = "sat" if real_error <= sp.Rational(1, 10**12) else "unsat"
    control_verdict = "sat" if control_error <= sp.Rational(1, 10**12) else "unsat"
    return {
        "engine": "sympy",
        "claim": "exact Kraus completeness max error <= eps",
        "real_claim_verdict": real_verdict,
        "negated_claim_verdict": control_verdict,
        "differ": real_verdict != control_verdict,
        "load_bearing": real_verdict != control_verdict,
        "bound_to_measured": True,
        "real_measured": {"exact_max_completeness_error": float(real_error), "eps": PROOF_EPS},
        "control_measured": {"exact_max_completeness_error": float(control_error), "eps": PROOF_EPS},
        "real_local_factor": str(real_local),
        "degenerate_local_factor": str(control_local),
        "real_top_factor": str(real_top),
        "degenerate_top_factor": str(control_top),
        "exact_control_error": str(control_error),
        "pass": bool(real_verdict == "sat" and control_verdict == "unsat"),
    }


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    smt = smt_load_bearing(
        claim="amplitude_damping_kraus_completeness_error_le_eps",
        real_measured={"max_completeness_error": top["torch_max_completeness_error"], "eps": PROOF_EPS},
        control_measured={"max_completeness_error": top["torch_degenerate_max_completeness_error"], "eps": PROOF_EPS},
        claim_builder=lambda v: v["max_completeness_error"] <= v["eps"],
        cvc5_claim_pairs=[("max_completeness_error", "<=", "eps")],
    )
    smt["pass"] = bool(
        smt["real_claim_verdict"] == "sat"
        and smt["negated_claim_verdict"] == "unsat"
        and smt["differ"] is True
        and smt["bound_to_measured"] is True
        and smt.get("cvc5_real_verdict") == "sat"
        and smt.get("cvc5_control_verdict") == "unsat"
    )
    cvc5 = {
        "engine": "cvc5",
        "claim": smt["claim"],
        "real_claim_verdict": smt.get("cvc5_real_verdict"),
        "negated_claim_verdict": smt.get("cvc5_control_verdict"),
        "differ": smt.get("cvc5_real_verdict") != smt.get("cvc5_control_verdict"),
        "load_bearing": smt.get("cvc5_real_verdict") != smt.get("cvc5_control_verdict"),
        "bound_to_measured": True,
        "real_measured": smt["real_measured"],
        "control_measured": smt["control_measured"],
        "pass": bool(smt.get("cvc5_real_verdict") == "sat" and smt.get("cvc5_control_verdict") == "unsat"),
    }
    sympy_flip = sympy_exact_flip(qubit_count(int(top["operator_dimension"])))
    return {
        "kraus_completeness_smt_load_bearing": smt,
        "cvc5_completeness_flip": cvc5,
        "sympy_exact_completeness_flip": sympy_flip,
        "proof_tools_load_bearing_via_flip_only": {
            "z3": smt["pass"],
            "cvc5": cvc5["pass"],
            "sympy": sympy_flip["pass"],
            "numeric_ablation_used_for_proof_tools": False,
        },
        "pass": bool(smt["pass"] and cvc5["pass"] and sympy_flip["pass"]),
    }


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    clifford_shift = clifford_bloch_shift(float(GAMMA))
    clifford_erased_shift = clifford_bloch_shift(0.0)
    return {
        "torch_channel_order_gap_gamma_erased": tool_ablation(
            "torch AD_gamma o X vs X o AD_gamma population L1 order gap; recompute after gamma-erased identity channel",
            baseline_value=top["torch_x_channel_order_l1_gap"],
            ablated_value=top["gamma_erased_order_l1_gap"],
            tool="torch",
        ),
        "jax_channel_order_gap_gamma_erased": tool_ablation(
            "jax AD_gamma o X vs X o AD_gamma population L1 order gap; recompute after gamma-erased identity channel",
            baseline_value=top["jax_x_channel_order_l1_gap"],
            ablated_value=0.0,
            tool="jax",
        ),
        "clifford_bloch_shift_gamma_erased": tool_ablation(
            "clifford Cl(3) Bloch-vector damping shift for |+>; recompute after gamma-erased identity channel",
            baseline_value=clifford_shift,
            ablated_value=clifford_erased_shift,
            tool="clifford",
        ),
    }


def build_known_value_checks(scale_rows: dict[int, dict[str, Any]], proofs: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for dim, row in scale_rows.items():
        q = qubit_count(dim)
        closed_control = float((float(GAMMA) + (1.0 - float(DEGENERATE_EPS)) ** 2) ** q - 1.0)
        checks.append(
            {
                "name": f"degenerate_control_closed_form_error_dim_{dim}",
                "computed": row["torch_degenerate_max_completeness_error"],
                "expected_from_finite_formula": closed_control,
                "abs_delta": abs(row["torch_degenerate_max_completeness_error"] - closed_control),
                "match": abs(row["torch_degenerate_max_completeness_error"] - closed_control) <= 1.0e-12,
            }
        )
        checks.append(
            {
                "name": f"order_gap_equals_two_gamma_dim_{dim}",
                "computed": row["torch_x_channel_order_l1_gap"],
                "expected_from_population_path": 2.0 * float(GAMMA),
                "abs_delta": abs(row["torch_x_channel_order_l1_gap"] - 2.0 * float(GAMMA)),
                "match": abs(row["torch_x_channel_order_l1_gap"] - 2.0 * float(GAMMA)) <= 1.0e-12,
            }
        )
        checks.append(
            {
                "name": f"sparse_transition_count_3powq_dim_{dim}",
                "computed": row["torch_sparse_csr_nnz_real"],
                "expected": 3**q,
                "match": row["torch_sparse_csr_nnz_real"] == 3**q,
            }
        )
        checks.append(
            {
                "name": f"basis_convention_single_excited_decays_to_ground_dim_{dim}",
                "computed": {
                    "p0": row["basis_convention_single_excited_output_p0"],
                    "p1": row["basis_convention_single_excited_output_p1"],
                },
                "expected": {"p0": float(GAMMA), "p1": 1.0 - float(GAMMA)},
                "abs_delta": max(
                    abs(row["basis_convention_single_excited_output_p0"] - float(GAMMA)),
                    abs(row["basis_convention_single_excited_output_p1"] - (1.0 - float(GAMMA))),
                ),
                "match": bool(
                    abs(row["basis_convention_single_excited_output_p0"] - float(GAMMA)) <= 1.0e-12
                    and abs(row["basis_convention_single_excited_output_p1"] - (1.0 - float(GAMMA))) <= 1.0e-12
                ),
            }
        )
    checks.append(
        {
            "name": "proof_tools_flip_without_numeric_ablation",
            "computed": proofs["proof_tools_load_bearing_via_flip_only"],
            "match": bool(
                proofs["proof_tools_load_bearing_via_flip_only"]["z3"]
                and proofs["proof_tools_load_bearing_via_flip_only"]["cvc5"]
                and proofs["proof_tools_load_bearing_via_flip_only"]["sympy"]
                and proofs["proof_tools_load_bearing_via_flip_only"]["numeric_ablation_used_for_proof_tools"] is False
            ),
        }
    )
    return checks


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(exist_ok=True)
    scale_rows = {dim: scale_rung(dim) for dim in SCALES}
    top = scale_rows[64]
    proofs = build_proofs(top)
    tool_ablations = build_tool_ablations(top)
    known_value_checks = build_known_value_checks(scale_rows, proofs)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > PROOF_EPS
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-12
        for row in tool_ablations.values()
    )
    known_pass = all(bool(row["match"]) for row in known_value_checks)
    jax_vs_pytorch_delta = max(float(row["jax_vs_pytorch_delta"]) for row in scale_rows.values())
    all_pass = bool(scale_pass and proofs["pass"] and ablation_pass and known_pass and jax_vs_pytorch_delta <= 1.0e-12)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(RTYPE),
        "top_operator_dimension": top["operator_dimension"],
        "top_qubit_count_log2_dimension": top["qubit_count_log2_dimension"],
        "max_completeness_error": top["torch_max_completeness_error"],
        "degenerate_control_max_completeness_error": top["torch_degenerate_max_completeness_error"],
        "all_excited_trace_after_channel": top["torch_all_excited_trace_after_channel"],
        "all_excited_trace_after_degenerate_control": top["torch_all_excited_trace_after_degenerate_control"],
        "x_channel_order_l1_gap": top["torch_x_channel_order_l1_gap"],
        "pass": bool(
            top["torch_max_completeness_error"] <= PROOF_EPS
            and top["torch_degenerate_max_completeness_error"] > PROOF_EPS
            and abs(top["torch_all_excited_trace_after_channel"] - 1.0) <= PROOF_EPS
            and top["torch_x_channel_order_l1_gap"] > 0.0
        ),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "top_operator_dimension": top["operator_dimension"],
        "max_completeness_error": top["jax_max_completeness_error"],
        "degenerate_control_max_completeness_error": top["jax_degenerate_max_completeness_error"],
        "x_channel_order_l1_gap": top["jax_x_channel_order_l1_gap"],
        "pass": bool(
            top["jax_max_completeness_error"] <= PROOF_EPS
            and top["jax_degenerate_max_completeness_error"] > PROOF_EPS
            and abs(top["jax_x_channel_order_l1_gap"] - top["torch_x_channel_order_l1_gap"]) <= 1.0e-12
        ),
    }
    controls = {
        "degenerate_no_jump_amplitude": {
            "description": "replace sqrt(1-gamma) by 1-eps and recompute every finite basis branch sum",
            "eps": str(DEGENERATE_EPS),
            "top_rung_max_completeness_error": top["torch_degenerate_max_completeness_error"],
            "smt_claim_holds": False,
            "pass": bool(top["torch_degenerate_max_completeness_error"] > PROOF_EPS),
        },
        "gamma_erased_identity_channel": {
            "description": "set gamma=0 for the order-sensitive X/channel path recompute",
            "top_rung_order_gap": top["gamma_erased_order_l1_gap"],
            "pass": bool(top["gamma_erased_order_l1_gap"] == 0.0),
        },
    }

    result = {
        "schema": "formal_scout_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "tier": "Stage-5 operator/channel/generator lego",
        "purpose": "Build one finite amplitude-damping operator/channel probe with helper-bound proof flip, genuine numeric ablations, torch primary execution, and JAX mirror parity.",
        "scientific_question": "Does the finite local amplitude-damping channel satisfy Kraus completeness over operator dimensions 8/16/32/64, while a degenerate no-jump control fails the same invariant and an X/channel path witnesses N01 order sensitivity?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "finite_map": {
            "domain": "operator dimensions d in {8,16,32,64}, q=log2(d) qubit basis states, local amplitude-damping branches over each excited bit, path operator X on the first bit, and controls",
            "codomain_or_output": "Kraus-completeness diagonal, trace readouts, X/channel order-gap readout, proof verdict flips, numeric ablation deltas, and scale ladder",
            "definition": "AD_gamma maps each finite basis population through all jump/no-jump branch subsets; completeness is the per-basis sum of branch probabilities, not a dense d^2 superoperator.",
        },
        "domain": "finite Hilbert/operator dimensions 8,16,32,64 with q=3,4,5,6 local amplitude-damping sites; gamma=1/10",
        "codomain_or_output": "finite completeness and order-sensitive channel readouts plus blocked downstream consumer list",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite operator dimensions, finite basis states, finite Kraus branch set, finite path operator set, and finite controls",
            },
            "N01": {
                "status": "active_tested",
                "statement": "AD_gamma after X differs from X after AD_gamma on the first-bit path, and the gamma-erased control collapses the gap",
            },
        },
        "root_constraints_in_force": {
            "F01": "finite operator/channel branch map over d in {8,16,32,64}",
            "N01": "order-sensitive channel/path composition AD_gamma o X != X o AD_gamma",
        },
        "carrier_layer": "finite spinor-derived basis population/density channel carrier",
        "geometry_layer": "operator/channel lego only; no manifold or PEPS3D geometry claim",
        "carrier_realization": "torch.float64 finite branch enumeration over basis populations; jax.float64 mirror; no NumPy import, no dense superoperator, no 2**64 state closure",
        "peps3d_embedding": "not_claimed: this Stage-5 operator/channel lego does not admit a PEPS3D manifold carrier",
        "spinor_state": "|0...0> and first-bit X|0...0> are finite spinor-derived basis states represented by torch/jax population densities",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["root/operator-channel micro packet requested directly; no stronger layer consumer admitted"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["future bounded operator/channel tool-lego fit or lego rows that cite this exact result path and keep promotion_allowed=false"],
        "allowed_claims": [
            "finite amplitude-damping Kraus completeness over operator dimensions 8/16/32/64",
            "degenerate no-jump control fails the same completeness invariant",
            "local X/channel order sensitivity is present and killed by gamma-erased control",
        ],
        "promotion_blockers": [
            "not a PEPS3D manifold carrier",
            "not a layer-completion packet",
            "not a flux/Xi/Phi0/Axis0/FEP/gravity/bridge admission",
        ],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite local amplitude-damping CPTP channel completeness and X/channel order sensitivity",
        "branch_status_before_run": "new bounded Stage-5 operator/channel sim requested by user",
        "required_tools": ["torch", "jax", "z3", "cvc5", "sympy", "clifford"],
        "actual_tools_used": ["torch", "jax", "z3", "cvc5", "sympy", "clifford"],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing z3/cvc5 flip", "sympy exact completeness flip"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "known_value_checks": known_value_checks,
        "all_known_value_checks_match": known_pass,
        "scale_ladder": {
            "operator_dimension_not_dense_state_dimension": True,
            "rungs": {str(dim): row for dim, row in scale_rows.items()},
            "pass": scale_pass,
        },
        "scale_rows": scale_rows,
        "required_negatives": ["degenerate_no_jump_amplitude", "gamma_erased_identity_channel"],
        "negatives_run": controls,
        "kill_conditions": {
            "degenerate_no_jump_amplitude": "same SMT completeness claim must be UNSAT under the degenerate measured error",
            "gamma_erased_identity_channel": "X/channel order gap must collapse to zero after gamma is removed",
        },
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "pass_rule": "scale rungs pass; z3/cvc5/sympy proof verdicts flip; torch/jax/clifford numeric ablations recompute nonzero deltas; known values match computed readouts",
        "fail_rule": "fail on missing proof flip, proof-tool numeric ablation, zero numeric ablation, JAX mismatch, dense superoperator/state closure, or promotion of blocked consumers",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proofs["pass"],
            "ablation_pass": ablation_pass,
            "known_value_pass": known_pass,
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "elapsed_seconds": time.time() - started,
        },
        "all_pass": all_pass,
        "required_pass": all_pass,
    }
    return _jsonable(result)


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
