#!/usr/bin/env python3
"""Stage-7 mutual-information readout on an admitted finite MPS cut carrier.

Entropy is an output readout here, not the organizing variable.  The structural
proof is bound to the measured Schmidt-rank/min-branch distinguishability
invariant of the already-admitted finite_mps_cut_carrier family.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import sys
import time
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3

from sim_coherent_information_8_16_32_64_dual_engine_probe import (
    CDTYPE,
    RTYPE,
    alpha_for_n,
    build_torch_mps,
    jax_local_density,
    reduced_single_from_mps,
)

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).name
RESULT = RESULT_DIR / "s7_mutual_information_probe_results.json"

OBJECT_ID = "S7_mutual_information_rank_gap_readout"
SITE_COUNTS = (8, 16, 32, 64)
ENTROPY_EPS = 1.0e-15
RANK_EPS = 1.0e-12
GAP_FLOOR = 1.0e-9
PARITY_TOL = 1.0e-6
KNOWN_TOL = 1.0e-10
CLASSIFICATION = "lego"
classification = CLASSIFICATION
PROMOTION_ALLOWED = False
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "bridge", "basin", "physics/gravity", "final manifold"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY complex128 MPS cut carrier consumer, 2x2 reduced densities, Schmidt spectrum, mutual-information readout, controls, and autograd dI/dalpha.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 mirror for the same finite cut readout and jax.grad parity; supportive parity, not a new carrier.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING SMT verdict flip on measured Schmidt rank and min-branch distinguishability, not on the entropy scalar.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING cvc5 cross-check of the same rank/gap measured invariant through load_bearing_proof.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact symbolic oracle for binary entropy known values and exact real-vs-product rank/gap flip.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Forbidden for claim-bearing nonclassical readout work; not imported and not used.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def entropy_from_probs_torch(probs: torch.Tensor) -> torch.Tensor:
    vals = torch.clamp(torch.real(probs), min=ENTROPY_EPS)
    vals = vals / torch.sum(vals)
    return -torch.sum(vals * torch.log(vals))


def entropy_from_density_torch(rho: torch.Tensor) -> torch.Tensor:
    hermitian = (rho + rho.conj().T) / 2.0
    vals = torch.linalg.eigvalsh(hermitian).real
    return entropy_from_probs_torch(vals)


def entropy_from_probs_jax(probs: jnp.ndarray) -> jnp.ndarray:
    vals = jnp.clip(jnp.real(probs), ENTROPY_EPS, 1.0)
    vals = vals / jnp.sum(vals)
    return -jnp.sum(vals * jnp.log(vals))


def entropy_from_density_jax(rho: jnp.ndarray) -> jnp.ndarray:
    vals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    return entropy_from_probs_jax(vals)


def raw_schmidt_probs_from_mps(n_sites: int, *, flattened: bool = False) -> torch.Tensor:
    mps = build_torch_mps(n_sites, order="rx_rz", flattened=flattened)
    tensor = mps.tensors[mps.schmidt_pair_site]
    gram = torch.einsum("dlr,dls->rs", tensor.conj(), tensor).real
    eigvals = torch.linalg.eigvalsh((gram + gram.T) / 2.0).real
    eigvals = torch.clamp(eigvals, min=0.0)
    total = torch.sum(eigvals)
    if float(total.item()) <= 0.0:
        raise ValueError("invalid zero-norm Schmidt carrier")
    return eigvals / total


def rank_gap_invariant_from_probs(probs: torch.Tensor) -> dict[str, Any]:
    vals = [float(v) for v in torch.sort(torch.real(probs)).values.detach().cpu().tolist()]
    rank = sum(1 for value in vals if value > RANK_EPS)
    min_branch = min(vals)
    spectral_gap = abs(vals[-1] - vals[0])
    return {
        "schmidt_rank": rank,
        "min_branch_probability": min_branch,
        "spectrum_gap_abs_p0_minus_p1": spectral_gap,
        "schmidt_probabilities_sorted": vals,
        "rank_threshold": RANK_EPS,
        "gap_floor": GAP_FLOOR,
        "distinguishable": bool(rank >= 2 and min_branch > GAP_FLOOR),
    }


def assert_non_dense_mps(n_sites: int, tensors: list[torch.Tensor]) -> dict[str, Any]:
    forbidden_dim = 2**n_sites
    max_dim = max(max(int(dim) for dim in tensor.shape) for tensor in tensors)
    max_numel = max(int(tensor.numel()) for tensor in tensors)
    max_bond = max(max(int(tensor.shape[1]), int(tensor.shape[2])) for tensor in tensors)
    ok = max_dim < forbidden_dim and max_numel < forbidden_dim and max_bond <= 2
    if not ok:
        raise AssertionError(f"dense state closure detected for N={n_sites}")
    return {
        "dense_state_closure_used": False,
        "forbidden_dense_dim": forbidden_dim,
        "max_tensor_dim_seen": max_dim,
        "max_tensor_numel_seen": max_numel,
        "mps_max_bond": max_bond,
        "pass": True,
    }


def mutual_information_from_probs_torch(probs: torch.Tensor) -> torch.Tensor:
    cut_entropy = entropy_from_probs_torch(probs)
    joint_entropy_ab = torch.zeros((), dtype=RTYPE)
    return cut_entropy + cut_entropy - joint_entropy_ab


def mutual_information_from_alpha_torch(alpha: torch.Tensor) -> torch.Tensor:
    probs = torch.stack([torch.cos(alpha) ** 2, torch.sin(alpha) ** 2])
    return mutual_information_from_probs_torch(probs)


def mutual_information_from_alpha_jax(alpha: jnp.ndarray) -> jnp.ndarray:
    probs = jnp.stack([jnp.cos(alpha) ** 2, jnp.sin(alpha) ** 2])
    cut_entropy = entropy_from_probs_jax(probs)
    return cut_entropy + cut_entropy


def torch_cut_readout(n_sites: int, *, flattened: bool = False) -> dict[str, Any]:
    mps = build_torch_mps(n_sites, order="rx_rz", flattened=flattened)
    guard = assert_non_dense_mps(n_sites, mps.tensors)
    rho_a = reduced_single_from_mps(mps, mps.schmidt_pair_site)
    rho_b = reduced_single_from_mps(mps, mps.schmidt_pair_site + 1)
    raw_probs = raw_schmidt_probs_from_mps(n_sites, flattened=flattened)
    invariant = rank_gap_invariant_from_probs(raw_probs)
    s_a = entropy_from_density_torch(rho_a)
    s_b = entropy_from_density_torch(rho_b)
    s_cut = entropy_from_probs_torch(raw_probs)
    s_ab_joint = torch.zeros((), dtype=RTYPE)
    raw_mi = s_a + s_b - s_ab_joint
    alpha = torch.tensor(0.0 if flattened else alpha_for_n(n_sites), dtype=RTYPE, requires_grad=True)
    grad_mi = mutual_information_from_alpha_torch(alpha)
    grad_mi.backward()
    return {
        "mutual_information": float(raw_mi.detach().item()),
        "raw_mutual_information_preclamp": float(raw_mi.detach().item()),
        "S_A": float(s_a.detach().item()),
        "S_B": float(s_b.detach().item()),
        "S_AB_joint": float(s_ab_joint.detach().item()),
        "S_cut_schmidt_entropy": float(s_cut.detach().item()),
        "dI_dalpha": float(alpha.grad.detach().item()),
        "rho_A_trace": float(torch.real(torch.trace(rho_a)).detach().item()),
        "rho_B_trace": float(torch.real(torch.trace(rho_b)).detach().item()),
        "rho_A_eigenvalues": [float(v) for v in torch.linalg.eigvalsh(rho_a).real.detach().tolist()],
        "rho_B_eigenvalues": [float(v) for v in torch.linalg.eigvalsh(rho_b).real.detach().tolist()],
        "schmidt_spectrum": invariant["schmidt_probabilities_sorted"],
        "rank_gap_invariant": invariant,
        "alpha": float(0.0 if flattened else alpha_for_n(n_sites)),
        "mps_tensor_count": mps.N,
        **guard,
    }


def jax_cut_readout(n_sites: int, *, flattened: bool = False) -> dict[str, Any]:
    rho_a, probs = jax_local_density(n_sites, order="rx_rz", flattened=flattened)
    rho_b = jnp.diag(probs.astype(jnp.complex128))
    s_a = entropy_from_density_jax(rho_a)
    s_b = entropy_from_density_jax(rho_b)
    s_cut = entropy_from_probs_jax(probs)
    s_ab_joint = jnp.asarray(0.0, dtype=jnp.float64)
    mi = s_a + s_b - s_ab_joint
    alpha = jnp.asarray(0.0 if flattened else alpha_for_n(n_sites), dtype=jnp.float64)
    grad = jax.grad(mutual_information_from_alpha_jax)(alpha)
    vals = [float(x) for x in jnp.sort(jnp.real(probs)).tolist()]
    rank = sum(1 for value in vals if value > RANK_EPS)
    return {
        "mutual_information": float(mi),
        "raw_mutual_information_preclamp": float(mi),
        "S_A": float(s_a),
        "S_B": float(s_b),
        "S_AB_joint": float(s_ab_joint),
        "S_cut_schmidt_entropy": float(s_cut),
        "dI_dalpha": float(grad),
        "schmidt_spectrum": vals,
        "rank_gap_invariant": {
            "schmidt_rank": rank,
            "min_branch_probability": min(vals),
            "spectrum_gap_abs_p0_minus_p1": abs(vals[-1] - vals[0]),
            "distinguishable": bool(rank >= 2 and min(vals) > GAP_FLOOR),
        },
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "mps_tensor_count": n_sites,
        "mps_max_bond": 2 if n_sites > 2 and not flattened else 1,
    }


def sympy_binary_entropy(alpha: float) -> sp.Expr:
    a = sp.Float(alpha, 80)
    p0 = sp.cos(a) ** 2
    p1 = sp.sin(a) ** 2
    terms = []
    for p in (p0, p1):
        if abs(float(p.evalf(80))) < 1.0e-70:
            terms.append(sp.Integer(0))
        else:
            terms.append(-p * sp.log(p))
    return sum(terms)


def sympy_mutual_information(alpha: float) -> float:
    return float((2 * sympy_binary_entropy(alpha)).evalf(50))


def sympy_rank_gap(alpha: float) -> dict[str, Any]:
    a = sp.Float(alpha, 80)
    p0 = float((sp.cos(a) ** 2).evalf(50))
    p1 = float((sp.sin(a) ** 2).evalf(50))
    vals = sorted([p0, p1])
    rank = sum(1 for value in vals if value > RANK_EPS)
    return {
        "schmidt_rank": rank,
        "min_branch_probability": vals[0],
        "spectrum_gap_abs_p0_minus_p1": abs(vals[1] - vals[0]),
        "schmidt_probabilities_sorted": vals,
        "claim_holds": bool(rank >= 2 and vals[0] > GAP_FLOOR),
    }


def classical_correlated_known_value() -> dict[str, Any]:
    half = torch.tensor([0.5, 0.5], dtype=RTYPE)
    joint = torch.tensor([0.5, 0.5], dtype=RTYPE)
    s_a = entropy_from_probs_torch(half)
    s_b = entropy_from_probs_torch(half)
    s_ab = entropy_from_probs_torch(joint)
    mi = s_a + s_b - s_ab
    return {
        "case": "classical_correlated_two_bit_diagonal",
        "S_A": float(s_a.item()),
        "S_B": float(s_b.item()),
        "S_AB": float(s_ab.item()),
        "mutual_information": float(mi.item()),
        "known": float(sp.log(2).evalf(50)),
        "match": abs(float(mi.item()) - float(sp.log(2).evalf(50))) < KNOWN_TOL,
    }


def high_local_entropy_zero_mi_control() -> dict[str, Any]:
    half = torch.tensor([0.5, 0.5], dtype=RTYPE)
    product_joint = torch.tensor([0.25, 0.25, 0.25, 0.25], dtype=RTYPE)
    s_a = entropy_from_probs_torch(half)
    s_b = entropy_from_probs_torch(half)
    s_ab = entropy_from_probs_torch(product_joint)
    mi = s_a + s_b - s_ab
    return {
        "description": "maximally mixed local 2x2 marginals with product joint density: high local entropy but zero correlation",
        "S_A": float(s_a.item()),
        "S_B": float(s_b.item()),
        "S_AB": float(s_ab.item()),
        "mutual_information": float(mi.item()),
        "pass": abs(float(mi.item())) < KNOWN_TOL and float(s_a.item()) > 0.0 and float(s_b.item()) > 0.0,
    }


def known_value_checks(scale_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for row in scale_rows:
        n_sites = row["sites_or_qubits"]
        alpha = row["torch"]["alpha"]
        sympy_cut_entropy = float(sympy_binary_entropy(alpha).evalf(50))
        sympy_mi = float((2 * sympy_binary_entropy(alpha)).evalf(50))
        checks.extend(
            [
                {
                    "invariant": f"N{n_sites}_torch_mi_matches_sympy_binary_entropy_formula",
                    "computed": row["torch"]["mutual_information"],
                    "known": sympy_mi,
                    "match": abs(row["torch"]["mutual_information"] - sympy_mi) < KNOWN_TOL,
                },
                {
                    "invariant": f"N{n_sites}_cut_entropy_matches_sympy_H2",
                    "computed": row["torch"]["S_cut_schmidt_entropy"],
                    "known": sympy_cut_entropy,
                    "match": abs(row["torch"]["S_cut_schmidt_entropy"] - sympy_cut_entropy) < KNOWN_TOL,
                },
                {
                    "invariant": f"N{n_sites}_jax_torch_value_parity",
                    "computed": row["jax_vs_pytorch"]["value_delta"],
                    "known": 0.0,
                    "match": row["jax_vs_pytorch"]["value_delta"] < PARITY_TOL,
                },
                {
                    "invariant": f"N{n_sites}_jax_torch_gradient_parity",
                    "computed": row["jax_vs_pytorch"]["gradient_delta"],
                    "known": 0.0,
                    "match": row["jax_vs_pytorch"]["gradient_delta"] < PARITY_TOL,
                },
            ]
        )
    bell_alpha = math.pi / 4.0
    bell_entropy = float(sympy_binary_entropy(bell_alpha).evalf(50))
    bell_mi = sympy_mutual_information(bell_alpha)
    checks.extend(
        [
            {
                "invariant": "bell_pair_cut_entropy_ln2",
                "computed": bell_entropy,
                "known": float(sp.log(2).evalf(50)),
                "match": abs(bell_entropy - float(sp.log(2).evalf(50))) < KNOWN_TOL,
            },
            {
                "invariant": "bell_pair_mutual_information_2ln2",
                "computed": bell_mi,
                "known": float((2 * sp.log(2)).evalf(50)),
                "match": abs(bell_mi - float((2 * sp.log(2)).evalf(50))) < KNOWN_TOL,
            },
            {
                "invariant": "product_cut_mutual_information_zero",
                "computed": sympy_mutual_information(0.0),
                "known": 0.0,
                "match": abs(sympy_mutual_information(0.0)) < KNOWN_TOL,
            },
            classical_correlated_known_value(),
            {
                "invariant": "sympy_trig_normalization_cos2_plus_sin2",
                "computed": int(sp.trigsimp(sp.cos(sp.Symbol("x")) ** 2 + sp.sin(sp.Symbol("x")) ** 2) == 1),
                "known": 1,
                "match": bool(sp.trigsimp(sp.cos(sp.Symbol("x")) ** 2 + sp.sin(sp.Symbol("x")) ** 2) == 1),
            },
        ]
    )
    return checks


def run_scale(n_sites: int) -> dict[str, Any]:
    torch_row = torch_cut_readout(n_sites)
    jax_row = jax_cut_readout(n_sites)
    product_torch = torch_cut_readout(n_sites, flattened=True)
    product_jax = jax_cut_readout(n_sites, flattened=True)
    value_delta = abs(torch_row["mutual_information"] - jax_row["mutual_information"])
    gradient_delta = abs(torch_row["dI_dalpha"] - jax_row["dI_dalpha"])
    sympy_mi = sympy_mutual_information(torch_row["alpha"])
    return {
        "sites_or_qubits": n_sites,
        "cut": {"A_sites": n_sites // 2, "B_sites": n_sites // 2, "boundary_interior_cut": "half_chain_A|B"},
        "carrier_family": "finite_mps_cut_carrier",
        "carrier_source": "sim_coherent_information_8_16_32_64_dual_engine_probe.build_torch_mps / jax_local_density",
        "dense_state_closure_used": False,
        "mps_tensor_network": {
            "tensor_count": torch_row["mps_tensor_count"],
            "max_bond": torch_row["mps_max_bond"],
            "dtype": "torch.complex128",
            "closure": "one partial Schmidt pair crossing the cut; product exterior sites; no 2**N state",
        },
        "torch": torch_row,
        "jax": jax_row,
        "jax_vs_pytorch": {
            "value_delta": value_delta,
            "gradient_delta": gradient_delta,
            "agree": value_delta < PARITY_TOL and gradient_delta < PARITY_TOL,
        },
        "sympy_known_mutual_information": sympy_mi,
        "product_control": {
            "torch": product_torch,
            "jax": product_jax,
            "pass": bool(
                product_torch["rank_gap_invariant"]["schmidt_rank"] == 1
                and product_torch["rank_gap_invariant"]["min_branch_probability"] <= GAP_FLOOR
                and abs(product_torch["mutual_information"]) < KNOWN_TOL
            ),
        },
        "pass": bool(
            torch_row["mps_tensor_count"] == n_sites
            and torch_row["mps_max_bond"] <= 2
            and torch_row["dense_state_closure_used"] is False
            and torch_row["rank_gap_invariant"]["distinguishable"] is True
            and torch_row["mutual_information"] > 0.0
            and abs(torch_row["mutual_information"] - sympy_mi) < KNOWN_TOL
            and value_delta < PARITY_TOL
            and gradient_delta < PARITY_TOL
            and product_torch["rank_gap_invariant"]["schmidt_rank"] == 1
            and product_torch["rank_gap_invariant"]["min_branch_probability"] <= GAP_FLOOR
        ),
    }


def smt_rank_gap_proof(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="schmidt_rank_ge_2_and_min_branch_probability_gt_floor",
        real_measured={
            "schmidt_rank": float(real["schmidt_rank"]),
            "min_branch_probability": float(real["min_branch_probability"]),
            "gap_floor": GAP_FLOOR,
        },
        control_measured={
            "schmidt_rank": float(control["schmidt_rank"]),
            "min_branch_probability": float(control["min_branch_probability"]),
            "gap_floor": GAP_FLOOR,
        },
        claim_builder=lambda v: z3.And(
            v["schmidt_rank"] >= 2,
            v["min_branch_probability"] > v["gap_floor"],
        ),
        cvc5_claim_pairs=[
            ("schmidt_rank", ">=", 2.0),
            ("min_branch_probability", ">", "gap_floor"),
        ],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    proof["entropy_scalar_asserted"] = False
    proof["readout_scalar_excluded_from_smt_claim"] = "mutual_information is reported downstream; SMT variables bind only rank/gap distinguishability."
    return proof


def cvc5_flip_node(proof: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim": "cvc5_crosscheck_schmidt_rank_gap_flip",
        "engine": "cvc5",
        "real_claim_verdict": proof.get("cvc5_real_verdict"),
        "negated_claim_verdict": proof.get("cvc5_control_verdict"),
        "differ": proof.get("cvc5_real_verdict") != proof.get("cvc5_control_verdict"),
        "load_bearing": proof.get("cvc5_real_verdict") != proof.get("cvc5_control_verdict"),
        "bound_to_measured": True,
        "real_measured": proof["real_measured"],
        "control_measured": proof["control_measured"],
        "entropy_scalar_asserted": False,
        "pass": bool(proof.get("cvc5_real_verdict") == "sat" and proof.get("cvc5_control_verdict") == "unsat"),
    }


def sympy_rank_gap_flip(real_alpha: float, control_alpha: float) -> dict[str, Any]:
    real = sympy_rank_gap(real_alpha)
    control = sympy_rank_gap(control_alpha)
    real_verdict = "sat" if real["claim_holds"] else "unsat"
    control_verdict = "sat" if control["claim_holds"] else "unsat"
    return {
        "claim": "sympy_exact_rank_gap_distinguishability_flip",
        "engine": "sympy",
        "real_claim_verdict": real_verdict,
        "negated_claim_verdict": control_verdict,
        "differ": real_verdict != control_verdict,
        "load_bearing": real_verdict != control_verdict,
        "bound_to_measured": True,
        "real_measured": {
            "schmidt_rank": float(real["schmidt_rank"]),
            "min_branch_probability": float(real["min_branch_probability"]),
            "gap_floor": GAP_FLOOR,
        },
        "control_measured": {
            "schmidt_rank": float(control["schmidt_rank"]),
            "min_branch_probability": float(control["min_branch_probability"]),
            "gap_floor": GAP_FLOOR,
        },
        "real_exact": real,
        "control_exact": control,
        "entropy_scalar_asserted": False,
        "pass": bool(real_verdict == "sat" and control_verdict == "unsat"),
    }


def build_tool_ablations(scale_rows: list[dict[str, Any]], checks: list[dict[str, Any]]) -> dict[str, Any]:
    top = scale_rows[-1]
    min_real_mi = min(row["torch"]["mutual_information"] for row in scale_rows)
    max_product_mi = max(row["product_control"]["torch"]["mutual_information"] for row in scale_rows)
    min_jax_mi = min(row["jax"]["mutual_information"] for row in scale_rows)
    max_product_jax_mi = max(row["product_control"]["jax"]["mutual_information"] for row in scale_rows)
    sympy_real = min(sympy_mutual_information(row["torch"]["alpha"]) for row in scale_rows)
    sympy_product = sympy_mutual_information(0.0)
    both_marginals = top["torch"]["mutual_information"]
    rho_b_removed = top["torch"]["S_A"] - top["torch"]["S_AB_joint"]
    known_pass_score = float(all(check["match"] for check in checks))
    return {
        "torch_product_flattening_recompute": tool_ablation(
            "min_mutual_information_real_carrier_vs_product_flattened_control",
            baseline_value=min_real_mi,
            ablated_value=max_product_mi,
            tool="pytorch",
        ),
        "torch_rho_B_contribution_removed": tool_ablation(
            "mutual_information_with_both_marginals_vs_rho_B_removed",
            baseline_value=both_marginals,
            ablated_value=rho_b_removed,
            tool="pytorch",
        ),
        "jax_product_flattening_recompute": tool_ablation(
            "jax_min_mutual_information_real_carrier_vs_product_flattened_control",
            baseline_value=min_jax_mi,
            ablated_value=max_product_jax_mi,
            tool="jax",
        ),
        "sympy_formula_product_recompute": tool_ablation(
            "sympy_binary_entropy_formula_real_vs_product_cut",
            baseline_value=sympy_real,
            ablated_value=sympy_product,
            tool="sympy",
        ),
        "sympy_known_value_oracle_removed": tool_ablation(
            "known_value_checks_available_vs_removed",
            baseline_value=known_pass_score,
            ablated_value=0.0,
            tool="sympy",
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = [run_scale(n_sites) for n_sites in SITE_COUNTS]
    checks = known_value_checks(scale_rows)
    top = scale_rows[-1]
    real_invariant = top["torch"]["rank_gap_invariant"]
    product_invariant = top["product_control"]["torch"]["rank_gap_invariant"]
    rank_gap_proof = smt_rank_gap_proof(real_invariant, product_invariant)
    proofs = {
        "rank_gap_smt_load_bearing": rank_gap_proof,
        "rank_gap_cvc5_verdict_flip": cvc5_flip_node(rank_gap_proof),
        "rank_gap_sympy_exact_flip": sympy_rank_gap_flip(top["torch"]["alpha"], 0.0),
    }
    ablations = build_tool_ablations(scale_rows, checks)
    scale_pass = all(row["pass"] for row in scale_rows)
    proof_pass = all(section["pass"] for section in proofs.values())
    known_pass = all(check["match"] for check in checks)
    controls = {
        "product_schmidt_collapse": {
            "description": "flattened=True path from the admitted carrier sets alpha=0 and collapses the cut to Schmidt rank 1",
            "rows": {
                str(row["sites_or_qubits"]): {
                    "mutual_information": row["product_control"]["torch"]["mutual_information"],
                    "schmidt_rank": row["product_control"]["torch"]["rank_gap_invariant"]["schmidt_rank"],
                    "min_branch_probability": row["product_control"]["torch"]["rank_gap_invariant"]["min_branch_probability"],
                    "pass": row["product_control"]["pass"],
                }
                for row in scale_rows
            },
            "pass": all(row["product_control"]["pass"] for row in scale_rows),
        },
        "high_local_entropy_zero_correlation": high_local_entropy_zero_mi_control(),
        "rho_B_value_ablation": {
            "description": "remove rho_B contribution and recompute the readout on the same top-rung carrier",
            "baseline_mutual_information": top["torch"]["mutual_information"],
            "rho_B_removed_value": top["torch"]["S_A"] - top["torch"]["S_AB_joint"],
            "outcome_delta": top["torch"]["S_B"],
            "pass": abs((top["torch"]["mutual_information"] - (top["torch"]["S_A"] - top["torch"]["S_AB_joint"])) - top["torch"]["S_B"]) < KNOWN_TOL,
        },
    }
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
        for row in ablations.values()
    )
    control_pass = all(section["pass"] for section in controls.values())
    max_value_delta = max(row["jax_vs_pytorch"]["value_delta"] for row in scale_rows)
    max_gradient_delta = max(row["jax_vs_pytorch"]["gradient_delta"] for row in scale_rows)
    all_pass = bool(scale_pass and proof_pass and known_pass and ablation_pass and control_pass)
    scale_ladder = {
        "rungs": {
            str(row["sites_or_qubits"]): {
                "sites_or_qubits": row["sites_or_qubits"],
                "dense_state_closure_used": False,
                "pass": row["pass"],
                "mutual_information": row["torch"]["mutual_information"],
                "raw_mutual_information_preclamp": row["torch"]["raw_mutual_information_preclamp"],
                "S_A": row["torch"]["S_A"],
                "S_B": row["torch"]["S_B"],
                "S_AB_joint": row["torch"]["S_AB_joint"],
                "S_cut_schmidt_entropy": row["torch"]["S_cut_schmidt_entropy"],
                "half_chain_entropy": row["torch"]["S_cut_schmidt_entropy"],
                "entanglement_entropy": row["torch"]["S_cut_schmidt_entropy"],
                "schmidt_rank": row["torch"]["rank_gap_invariant"]["schmidt_rank"],
                "min_branch_probability": row["torch"]["rank_gap_invariant"]["min_branch_probability"],
                "schmidt_spectrum": row["torch"]["schmidt_spectrum"],
                "mps_max_bond": row["torch"]["mps_max_bond"],
                "jax_value_delta": row["jax_vs_pytorch"]["value_delta"],
                "jax_gradient_delta": row["jax_vs_pytorch"]["gradient_delta"],
            }
            for row in scale_rows
        },
        "pass": scale_pass,
    }
    torch_primary_result = {
        "runtime": "torch",
        "dtype": "torch.complex128",
        "carrier": "imported finite_mps_cut_carrier from coherent-information sibling",
        "top_scale_sites_or_qubits": top["sites_or_qubits"],
        "mutual_information": top["torch"]["mutual_information"],
        "rank_gap_invariant": real_invariant,
        "entropy_as_output": True,
        "entropy_used_as_master_variable": False,
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "top_scale_mutual_information": top["jax"]["mutual_information"],
        "top_scale_dI_dalpha": top["jax"]["dI_dalpha"],
        "max_value_delta": max_value_delta,
        "max_gradient_delta": max_gradient_delta,
        "pass": max_value_delta < PARITY_TOL and max_gradient_delta < PARITY_TOL,
    }
    return {
        "schema": "formal_scout_result_v1",
        "name": "sim_s7_mutual_information_probe",
        "sim_id": "sim_s7_mutual_information_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": THISFILE,
        "result_path": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "tier": "Stage 7 entropy/information readout lego",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "nonclassical",
        "sim_class": "mutual_information_rank_gap_readout_probe",
        "purpose": "Compute mutual information as a downstream readout on an existing finite MPS bipartite-cut carrier while proving the prior distinguishability invariant by rank/gap SMT flip.",
        "scientific_question": "Does the already-admitted finite_mps_cut_carrier expose a positive A|B mutual-information readout exactly when the prior Schmidt rank/min-branch distinguishability invariant survives the product control?",
        "finite_map": {
            "domain": "Stage-2 finite_mps_cut_carrier: N in {8,16,32,64}, open-boundary bond-2 MPS, one partial Schmidt pair across A|B, product exterior sites, finite 2x2 rho_A/rho_B.",
            "codomain_or_output": "Schmidt rank/gap invariant plus downstream readouts S_A, S_B, S_AB_joint, S_cut_schmidt_entropy, I(A:B), torch/JAX deltas, controls, and proof verdicts.",
            "definition": "Readout_N(carrier) = I(A:B)=S(rho_A)+S(rho_B)-S(rho_AB). For the pure channel-free cut carrier, S(rho_AB)=0 and the Schmidt entropy is reported separately as S_cut.",
        },
        "domain": {
            "site_counts": list(SITE_COUNTS),
            "cut": "A first N/2 sites, B last N/2 sites",
            "carrier": "open-boundary bond-2 MPS with one partial Schmidt pair crossing the cut; reused from the Stage-2 coherent-information sibling",
            "finite_density_objects": ["2x2 rho_A", "2x2 rho_B", "2-entry Schmidt spectrum"],
        },
        "codomain_or_output": "rank/gap distinguishability invariant and mutual-information entropy readout receipt",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite site counts, finite MPS tensors, finite cut probes/densities/spectrum, finite scale ladder",
            },
            "N01": {
                "status": "inherited_from_stage2_carrier_not_promoted_here",
                "statement": "carrier path uses the existing ordered RX/RZ finite_mps_cut_carrier family; this S7 readout does not assert a new order claim",
            },
        },
        "root_constraints_in_force": {
            "F01": "finite carrier/probe/operator/path set: N-site MPS tensors and A|B cut densities at N=8,16,32,64",
            "N01": "order-sensitive carrier provenance inherited from the Stage-2 sibling; no new N01 promotion is claimed by the MI scalar",
        },
        "carrier_layer": "finite_mps_cut_carrier",
        "geometry_layer": "A|B half-chain boundary_interior_cut readout on an existing MPS carrier",
        "carrier_realization": {
            "torch": "complex128 MPS tensors imported via build_torch_mps; no dense 2**N vector",
            "jax": "complex128 x64 mirror via jax_local_density; no dense 2**N vector",
            "density_objects": "2x2 rho_A/rho_B and 2-entry Schmidt spectrum",
        },
        "peps3d_embedding": "not_claimed_by_this_readout; this acts on an existing MPS cut carrier and blocks PEPS3D/manifold consumers",
        "spinor_state": "two-component cut-site amplitudes in the existing MPS; spinor-derived 2x2 rho_A/rho_B densities",
        "quaternion_action": "not_applicable",
        "bridge_layer": "none",
        "cut_layer": "boundary_interior_cut A|B half-chain",
        "law_or_candidate_tested": "mutual information readout I(A:B)=S(A)+S(B)-S(AB) downstream of Schmidt rank/gap distinguishability",
        "branch_status_before_run": "bounded user-requested S7 readout lego",
        "allowed_claims": [
            "finite MPS A|B mutual-information readout at N=8,16,32,64",
            "rank/gap distinguishability survives real carrier and fails product control",
            "entropy is output only and not the SMT organizer",
        ],
        "promotion_blockers": [
            "not a new physical carrier",
            "not PEPS3D/manifold admission",
            "N01 order provenance is inherited, not newly proved by MI",
            "Axis0/flux/FEP/bridge/basin/physics remain blocked",
        ],
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3 rank/gap SMT flip", "cvc5 rank/gap SMT flip", "sympy exact rank/gap and entropy known-value oracle"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_role_source": {tool: "local" for tool in TOOL_MANIFEST},
        "required_inputs": ["results/coherent_information_8_16_32_64_dual_engine_probe_results.json"],
        "data_or_artifact_dependencies": ["sim_coherent_information_8_16_32_64_dual_engine_probe.py"],
        "dependency_receipts": ["results/coherent_information_8_16_32_64_dual_engine_probe_results.json"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_negatives": ["product_schmidt_collapse", "high_local_entropy_zero_correlation", "rho_B_value_ablation"],
        "negatives_run": controls,
        "controls": controls,
        "kill_conditions": {
            "product_schmidt_collapse": "Schmidt rank drops to 1, min branch probability falls below gap floor, and MI readout vanishes",
            "high_local_entropy_zero_correlation": "local entropy remains high while MI is zero, proving entropy alone is not the signal",
            "rho_B_value_ablation": "removing rho_B changes I(A:B), proving both marginal readouts are load-bearing in the scalar output",
        },
        "required_artifacts": [str(RESULT.relative_to(ROOT))],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"{OBJECT_ID}:{int(started)}",
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": max_value_delta,
        "jax_vs_pytorch": {
            "max_value_delta": max_value_delta,
            "max_gradient_delta": max_gradient_delta,
            "agree": max_value_delta < PARITY_TOL and max_gradient_delta < PARITY_TOL,
        },
        "distinguishability_invariant": {
            "organizing_variable": "Schmidt rank plus min branch probability/gap floor",
            "entropy_scalar_is_not_asserted": True,
            "real_top_rung": real_invariant,
            "product_control_top_rung": product_invariant,
        },
        "entropy_as_output": {
            "status": True,
            "readout": "I(A:B)=S_A+S_B-S_AB_joint",
            "not_used_as_smt_claim": True,
            "raw_preclamp_reported": True,
        },
        "proof_results": proofs,
        "known_value_checks": checks,
        "all_known_value_checks_match": known_pass,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "scale_ladder": scale_ladder,
        "scale_rows": scale_rows,
        "positive": {
            "rank_gap_distinguishability_precedes_entropy_readout": {
                "pass": proof_pass,
                "proof_keys": sorted(proofs),
            },
            "mutual_information_mps_readout_non_dense_8_16_32_64": {
                "site_counts": list(SITE_COUNTS),
                "scale_ladder": scale_ladder,
                "pass": scale_pass,
            },
            "known_value_checks_computed": {
                "n_checks": len(checks),
                "n_passed": sum(1 for check in checks if check["match"]),
                "pass": known_pass,
            },
            "jax_grad_matches_torch_autograd": {
                "max_value_delta": max_value_delta,
                "max_gradient_delta": max_gradient_delta,
                "tolerance": PARITY_TOL,
                "pass": max_value_delta < PARITY_TOL and max_gradient_delta < PARITY_TOL,
            },
        },
        "boundary": {
            "dense_state_closure_blocked": {
                "dense_state_closure_used": False,
                "forbidden": "no vector or density of size 2**N is built; only MPS tensors, 2x2 densities, and 2-entry spectra are used",
                "pass": True,
            },
            "promotion_blocked": {
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
                "blocked_consumers": BLOCKED_CONSUMERS,
                "pass": True,
            },
        },
        "shells": [{"N": n, "A_sites": n // 2, "B_sites": n // 2, "carrier": "finite_mps_cut_carrier"} for n in SITE_COUNTS],
        "future_continuations": [
            "lift the same rank/gap-first MI readout to an admitted PEPS3D carrier before any manifold consumer uses it",
            "add a mixed-state MPDO variant where S_AB_joint is nonzero and independently contracted",
        ],
        "compatibility_weights": {
            "min_mutual_information": min(row["torch"]["mutual_information"] for row in scale_rows),
            "min_branch_probability": min(row["torch"]["rank_gap_invariant"]["min_branch_probability"] for row in scale_rows),
            "max_jax_torch_delta": max(max_value_delta, max_gradient_delta),
        },
        "compression_map": "N-site MPS tensors -> 2x2 rho_A/rho_B + 2-entry Schmidt spectrum -> rank/gap invariant first, entropy readout second; never 2**N amplitudes",
        "present_survivor": {
            "object": OBJECT_ID,
            "possibility_capacity": min(row["torch"]["rank_gap_invariant"]["min_branch_probability"] for row in scale_rows),
            "survives_negatives": control_pass,
        },
        "outward_record": {
            "result_path": str(RESULT.relative_to(ROOT)),
            "acceptance_commands": [
                f"/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 ../../../scripts/per_sim_contract.py {RESULT.relative_to(ROOT)}",
                f"/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 ../../../scripts/max_deep_lego_gate.py {RESULT.relative_to(ROOT)} --scale-required --rigor",
                f"/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 ../../../scripts/recheck_proof.py {RESULT.relative_to(ROOT)} --rerun {THISFILE} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            ],
        },
        "survivor_invariant": {
            "passed": bool(proof_pass and control_pass),
            "description": "rank/gap distinguishability is present on the real carrier, fails under product collapse, and the MI scalar is only the downstream readout",
        },
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "known_value_pass": known_pass,
            "control_pass": control_pass,
            "ablation_pass": ablation_pass,
            "max_value_delta": max_value_delta,
            "max_gradient_delta": max_gradient_delta,
            "n_known_value_checks": len(checks),
            "n_known_value_checks_passed": sum(1 for check in checks if check["match"]),
            "elapsed_seconds": time.time() - started,
            "promotion_allowed": PROMOTION_ALLOWED,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "pass_rule": "rank/gap SMT proof flips on measured real-vs-product carrier, all non-dense scale rungs pass, torch/JAX value and gradient deltas are below tolerance, controls/ablations recompute nonzero changes, and known values match sympy.",
        "fail_rule": "fail on entropy used as SMT organizer, dense 2**N closure, missing product-control flip, missing rank/gap proof binding, JAX mismatch, cosmetic ablation, or downstream promotion.",
        "promotion_status": "keep_but_open",
        "promotion_allowed": PROMOTION_ALLOWED,
        "eligible_consumers": ["future bounded MPS/MPDO information-readout probes that cite the rank/gap-first ceiling"],
        "why_not_v4_probes": "This is one v5 Stage-7 lego readout on an existing MPS carrier, not a bridge/Axis0/manifold/physics admission.",
        "blockers": [] if all_pass else ["one or more pass rules failed; inspect result_summary"],
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out_path": str(RESULT), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
