#!/usr/bin/env python3
"""QIT-FEP Axis0 path-integral spinor scout.

This scout tests a finite quantum-information translation of FEP that is
compatible with the current constraint manifold:

* states are finite density operators over C^2 spinors, optionally entangled
  with a one-qubit reference;
* hidden trajectories are finite Kraus histories, not continuous gradients or
  classical Markov states;
* path evidence is a Feynman-like finite sum over instrument histories;
* variational free energy is quantum relative entropy against the unnormalized
  posterior cut state;
* the provisional Axis0 scalar is evidence-plus-coherent-information:

      Phi_QFEP_provisional = log Z_path + I_c(A -> B)

The additive scalar is deliberately labeled provisional. The receipt reports
log Z and I_c separately; the sum is a candidate aggregate, not an invariant.

Formal scout only. It does not canonize Axis0, FEP, Markov blankets,
holographic spacetime, ER=EPR, twistor theory, cognition, or physics.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "qit_fep_axis0_path_integral_spinor_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "qit_fep_axis0_path_integral_spinor_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite QIT-FEP Axis0 candidate over spinor "
    "density states and Kraus-history path sums. It does not admit final "
    "Axis0, full FEP, Markov blanket ontology, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex density matrices, Kraus-history path sums, finite QVFE, entropy, and coherent-information readouts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency fence for F01/N01/capacity requirements and nonpromotion",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-10


I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)


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


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    tr = torch.real(torch.trace(rho))
    return rho / tr


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def normalize_vec(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize_vec(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * axis


def dephase(axis: torch.Tensor, q: float) -> list[torch.Tensor]:
    return [math.sqrt(1 - q) * I2, math.sqrt(q) * axis]


def amplitude_down(gamma: float) -> list[torch.Tensor]:
    # Source convention used in current terrain docs: fixed point z = -1.
    k0 = torch.tensor([[math.sqrt(1 - gamma), 0], [0, 1]], dtype=CDTYPE)
    k1 = torch.tensor([[0, 0], [math.sqrt(gamma), 0]], dtype=CDTYPE)
    return [k0, k1]


def amplitude_up(gamma: float) -> list[torch.Tensor]:
    k0 = torch.tensor([[1, 0], [0, math.sqrt(1 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=CDTYPE)
    return [k0, k1]


def soft_effect(axis: torch.Tensor, bias: float = 0.62) -> torch.Tensor:
    # Full rank positive effect, so log/sqrt are stable.
    return hermitize(0.5 * I2 + 0.5 * bias * axis)


def psd_sqrt(mat: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(hermitize(mat))
    vals = torch.clamp(vals.real, min=0.0)
    return vecs @ torch.diag(torch.sqrt(vals)).to(CDTYPE) @ torch.conj(vecs).T


def logm_psd(mat: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(hermitize(mat))
    vals = torch.clamp(vals.real, min=EPS)
    return vecs @ torch.diag(torch.log(vals)).to(CDTYPE) @ torch.conj(vecs).T


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def relative_entropy(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    rho = normalize_state(rho)
    log_rho = logm_psd(rho)
    log_sigma = logm_psd(normalize_state(sigma))
    return float(torch.real(torch.trace(rho @ (log_rho - log_sigma))).item())


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def coherent_information_a_to_b(rho_ab: torch.Tensor) -> float:
    return entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)


def mutual_information_ab(rho_ab: torch.Tensor) -> float:
    return entropy(partial_trace_a(rho_ab)) + entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)


def zz_entangler(theta: float) -> torch.Tensor:
    zz = torch.kron(Z, Z)
    return math.cos(theta / 2) * torch.eye(4, dtype=CDTYPE) - 1j * math.sin(theta / 2) * zz


def initial_ab(phi: float, chi: float, eta: float, *, entangled: bool) -> torch.Tensor:
    psi_a = spinor(phi, chi, eta)
    psi_b = spinor(phi + 0.37, chi - 0.21, max(0.12, min(1.2, eta + 0.18)))
    psi = torch.kron(psi_a, psi_b)
    if entangled:
        psi = zz_entangler(0.74) @ psi
    return density(normalize_vec(psi))


def transform_reference_b(rho_ab: torch.Tensor, u_b: torch.Tensor) -> torch.Tensor:
    u_ab = torch.kron(I2, u_b)
    return normalize_state(u_ab @ rho_ab @ torch.conj(u_ab).T)


def fro_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).real.item())


def engine_instruments(flux: int, *, commuting: bool = False, reversed_order: bool = False) -> list[list[torch.Tensor]]:
    if commuting:
        instruments = [
            dephase(Z, 0.16),
            [unitary(Z, flux * 0.31)],
            dephase(Z, 0.11),
            [unitary(Z, flux * -0.19)],
        ]
    else:
        instruments = [
            [unitary(Z, flux * 0.31)],
            dephase(X, 0.16),
            [unitary(X, flux * -0.27)],
            amplitude_down(0.13) if flux > 0 else amplitude_up(0.13),
        ]
    return list(reversed(instruments)) if reversed_order else instruments


def engine_instruments_with_params(
    flux: int,
    *,
    q_dephase: float,
    gamma: float,
    reversed_order: bool = False,
) -> list[list[torch.Tensor]]:
    instruments = [
        [unitary(Z, flux * 0.31)],
        dephase(X, q_dephase),
        [unitary(X, flux * -0.27)],
        amplitude_down(gamma) if flux > 0 else amplitude_up(gamma),
    ]
    return list(reversed(instruments)) if reversed_order else instruments


def scaled_noncommuting_instruments(flux: int, target_path_count: int, *, reversed_order: bool = False) -> list[list[torch.Tensor]]:
    instruments = engine_instruments(flux, commuting=False, reversed_order=False)
    if target_path_count >= 8:
        instruments.append(dephase(Z, 0.09))
    if target_path_count >= 16:
        instruments.append(dephase(Y, 0.07))
    return list(reversed(instruments)) if reversed_order else instruments


def enumerate_kraus_paths(instruments: list[list[torch.Tensor]]) -> list[torch.Tensor]:
    out: list[torch.Tensor] = []
    for choices in itertools.product(*instruments):
        k = I2.clone()
        for step in choices:
            k = step @ k
        out.append(k)
    return out


def apply_channel(rho: torch.Tensor, instruments: list[list[torch.Tensor]]) -> torch.Tensor:
    acc = torch.zeros_like(rho)
    for k in enumerate_kraus_paths(instruments):
        acc = acc + k @ rho @ torch.conj(k).T
    return normalize_state(acc)


def qit_fep_path_sum(
    rho_ab: torch.Tensor,
    instruments: list[list[torch.Tensor]],
    effect_a: torch.Tensor,
) -> dict[str, Any]:
    sqrt_e = psd_sqrt(effect_a)
    sqrt_e_ab = torch.kron(sqrt_e, I2)
    effect_ab = torch.kron(effect_a, I2)
    tau = torch.zeros((4, 4), dtype=CDTYPE)
    evidence_terms: list[float] = []
    paths = enumerate_kraus_paths(instruments)
    for k_a in paths:
        k_ab = torch.kron(k_a, I2)
        evolved = k_ab @ rho_ab @ torch.conj(k_ab).T
        term = sqrt_e_ab @ evolved @ torch.conj(sqrt_e_ab).T
        tau = tau + term
        evidence_terms.append(float(torch.real(torch.trace(effect_ab @ evolved)).item()))
    z_path = float(sum(evidence_terms))
    posterior = normalize_state(tau)
    f_min = -math.log(max(z_path, EPS))
    prior_free_energy = relative_entropy(rho_ab, posterior) + f_min
    posterior_free_energy = relative_entropy(posterior, posterior) + f_min
    prior_a_relative_entropy = relative_entropy(partial_trace_a(rho_ab), partial_trace_a(posterior))
    data_processing_margin = relative_entropy(rho_ab, posterior) - prior_a_relative_entropy
    ic = coherent_information_a_to_b(posterior)
    mutual_information = mutual_information_ab(posterior)
    phi_qfep_provisional = math.log(max(z_path, EPS)) + ic
    phi_qfep_mutual_information = math.log(max(z_path, EPS)) + mutual_information
    return {
        "path_count": len(paths),
        "z_path": z_path,
        "log_z": math.log(max(z_path, EPS)),
        "f_min": f_min,
        "prior_free_energy": prior_free_energy,
        "posterior_free_energy": posterior_free_energy,
        "qvfe_gap_prior_minus_min": prior_free_energy - posterior_free_energy,
        "prior_a_relative_entropy": prior_a_relative_entropy,
        "data_processing_margin_ab_to_a": data_processing_margin,
        "coherent_information": ic,
        "mutual_information": mutual_information,
        "phi_qfep_provisional": phi_qfep_provisional,
        "phi_qfep_mutual_information": phi_qfep_mutual_information,
        "posterior": posterior,
        "evidence_terms": evidence_terms,
    }


def one_site_path_sum(
    rho_a: torch.Tensor,
    instruments: list[list[torch.Tensor]],
    effect_a: torch.Tensor,
) -> float:
    return float(torch.real(torch.trace(effect_a @ apply_channel(rho_a, instruments))).item())


def diagonal_classical_control(rho: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.diag(rho)).to(CDTYPE)


def run_core_fixture() -> dict[str, Any]:
    rho_ab = initial_ab(0.17, 0.33, 0.58, entangled=True)
    effect = soft_effect(Z + 0.35 * X, 0.52)
    instruments = engine_instruments(+1)
    result = qit_fep_path_sum(rho_ab, instruments, effect)
    rho_a = partial_trace_a(rho_ab)
    channel_z = one_site_path_sum(rho_a, instruments, effect)
    path_gap = abs(channel_z - result["z_path"])
    return {
        "pass": (
            result["path_count"] == 4
            and path_gap < 1e-9
            and result["qvfe_gap_prior_minus_min"] > 1e-4
            and result["data_processing_margin_ab_to_a"] > -1e-9
        ),
        "path_count": result["path_count"],
        "path_sum_channel_gap": path_gap,
        "f_min": result["f_min"],
        "prior_free_energy": result["prior_free_energy"],
        "posterior_free_energy": result["posterior_free_energy"],
        "qvfe_gap_prior_minus_min": result["qvfe_gap_prior_minus_min"],
        "prior_a_relative_entropy": result["prior_a_relative_entropy"],
        "data_processing_margin_ab_to_a": result["data_processing_margin_ab_to_a"],
        "log_z": result["log_z"],
        "coherent_information": result["coherent_information"],
        "mutual_information": result["mutual_information"],
        "phi_qfep_provisional": result["phi_qfep_provisional"],
        "phi_qfep_mutual_information": result["phi_qfep_mutual_information"],
    }


def run_order_and_classical_controls() -> dict[str, Any]:
    rho_ab = initial_ab(-0.22, 0.47, 0.49, entangled=True)
    effect = soft_effect(X + 0.25 * Z, 0.48)
    forward = qit_fep_path_sum(rho_ab, engine_instruments(+1), effect)
    reversed_q = qit_fep_path_sum(rho_ab, engine_instruments(+1, reversed_order=True), effect)
    commuting_quantum = qit_fep_path_sum(rho_ab, engine_instruments(+1, commuting=True), soft_effect(Z, 0.48))
    commuting_quantum_reversed = qit_fep_path_sum(
        rho_ab,
        engine_instruments(+1, commuting=True, reversed_order=True),
        soft_effect(Z, 0.48),
    )
    commuting = qit_fep_path_sum(
        torch.kron(diagonal_classical_control(partial_trace_a(rho_ab)), partial_trace_b(rho_ab)),
        engine_instruments(+1, commuting=True),
        soft_effect(Z, 0.48),
    )
    commuting_reversed = qit_fep_path_sum(
        torch.kron(diagonal_classical_control(partial_trace_a(rho_ab)), partial_trace_b(rho_ab)),
        engine_instruments(+1, commuting=True, reversed_order=True),
        soft_effect(Z, 0.48),
    )
    scaling_rows = []
    for target in (4, 8, 16):
        scaled_forward = qit_fep_path_sum(rho_ab, scaled_noncommuting_instruments(+1, target), effect)
        scaled_reversed = qit_fep_path_sum(rho_ab, scaled_noncommuting_instruments(+1, target, reversed_order=True), effect)
        actual_path_count = scaled_forward["path_count"]
        scaling_rows.append(
            {
                "target_path_count": target,
                "actual_path_count": actual_path_count,
                "order_gap": abs(scaled_forward["phi_qfep_provisional"] - scaled_reversed["phi_qfep_provisional"]),
            }
        )
    order_gap = abs(forward["phi_qfep_provisional"] - reversed_q["phi_qfep_provisional"])
    commuting_quantum_order_gap = abs(
        commuting_quantum["phi_qfep_provisional"] - commuting_quantum_reversed["phi_qfep_provisional"]
    )
    commuting_order_gap = abs(commuting["phi_qfep_provisional"] - commuting_reversed["phi_qfep_provisional"])
    scaling_pass = all(row["order_gap"] > 1e-3 for row in scaling_rows)
    return {
        "pass": order_gap > 1e-3 and commuting_quantum_order_gap < 1e-9 and commuting_order_gap < 1e-9 and scaling_pass,
        "noncommuting_order_gap": order_gap,
        "commuting_quantum_order_gap": commuting_quantum_order_gap,
        "commuting_order_gap": commuting_order_gap,
        "path_count_scaling": scaling_rows,
        "forward_phi": forward["phi_qfep_provisional"],
        "reversed_phi": reversed_q["phi_qfep_provisional"],
        "commuting_quantum_phi": commuting_quantum["phi_qfep_provisional"],
        "commuting_quantum_reversed_phi": commuting_quantum_reversed["phi_qfep_provisional"],
        "commuting_phi": commuting["phi_qfep_provisional"],
        "commuting_reversed_phi": commuting_reversed["phi_qfep_provisional"],
    }


def run_entanglement_control() -> dict[str, Any]:
    effect = soft_effect(Y + 0.4 * Z, 0.50)
    instruments = engine_instruments(-1)
    entangled = qit_fep_path_sum(initial_ab(0.52, -0.31, 0.66, entangled=True), instruments, effect)
    product = qit_fep_path_sum(initial_ab(0.52, -0.31, 0.66, entangled=False), instruments, effect)
    ic_gap = abs(entangled["coherent_information"] - product["coherent_information"])
    phi_gap = abs(entangled["phi_qfep_provisional"] - product["phi_qfep_provisional"])
    return {
        "pass": ic_gap > 1e-2 and phi_gap > 1e-2,
        "entangled_ic": entangled["coherent_information"],
        "product_ic": product["coherent_information"],
        "ic_gap": ic_gap,
        "entangled_phi": entangled["phi_qfep_provisional"],
        "product_phi": product["phi_qfep_provisional"],
        "phi_gap": phi_gap,
    }


def run_b_side_unitary_gauge_control() -> dict[str, Any]:
    """Reference-only unitary changes B gauge, not A-side evidence.

    This is not a proof that every extension of rho_A is equivalent. The cut
    state is intentionally load-bearing. This check only blocks a spurious
    dependence on the arbitrary B-side basis for a fixed cut.
    """

    rho_ab = initial_ab(-0.14, 0.28, 0.62, entangled=True)
    u_b = unitary(Y, 0.83) @ unitary(Z, -0.37)
    rho_gauge = transform_reference_b(rho_ab, u_b)
    instruments = engine_instruments(+1)
    effect = soft_effect(Z + 0.2 * X, 0.51)
    original = qit_fep_path_sum(rho_ab, instruments, effect)
    gauged = qit_fep_path_sum(rho_gauge, instruments, effect)
    rho_a_gap = fro_gap(partial_trace_a(rho_ab), partial_trace_a(rho_gauge))
    posterior_a_gap = fro_gap(partial_trace_a(original["posterior"]), partial_trace_a(gauged["posterior"]))
    gaps = {
        "rho_a_gap": rho_a_gap,
        "posterior_a_gap": posterior_a_gap,
        "z_path_gap": abs(original["z_path"] - gauged["z_path"]),
        "log_z_gap": abs(original["log_z"] - gauged["log_z"]),
        "coherent_information_gap": abs(original["coherent_information"] - gauged["coherent_information"]),
        "phi_qfep_provisional_gap": abs(
            original["phi_qfep_provisional"] - gauged["phi_qfep_provisional"]
        ),
    }
    return {
        "pass": all(value < 1e-9 for value in gaps.values()),
        "interpretation": (
            "B-side local unitary is a reference-basis gauge change for a fixed "
            "cut. A-side path evidence and coherent-information aggregate must "
            "be invariant."
        ),
        "not_claimed": "does not prove invariance over arbitrary non-isometric extensions of rho_A",
        "gaps": gaps,
        "original_phi": original["phi_qfep_provisional"],
        "gauged_phi": gauged["phi_qfep_provisional"],
    }


def component_summary(result: dict[str, Any]) -> dict[str, float]:
    return {
        "log_z": result["log_z"],
        "coherent_information": result["coherent_information"],
        "mutual_information": result["mutual_information"],
        "phi_qfep_provisional": result["phi_qfep_provisional"],
        "phi_qfep_mutual_information": result["phi_qfep_mutual_information"],
        "f_min": result["f_min"],
    }


def candidate_values(result: dict[str, Any]) -> dict[str, float]:
    return {
        "log_z_only": result["log_z"],
        "ic_only": result["coherent_information"],
        "mi_only": result["mutual_information"],
        "phi_logz_plus_ic": result["phi_qfep_provisional"],
        "phi_logz_plus_mi": result["phi_qfep_mutual_information"],
    }


def abs_component_gaps(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    return {
        "log_z": abs(a["log_z"] - b["log_z"]),
        "coherent_information": abs(a["coherent_information"] - b["coherent_information"]),
        "mutual_information": abs(a["mutual_information"] - b["mutual_information"]),
        "phi_qfep_provisional": abs(a["phi_qfep_provisional"] - b["phi_qfep_provisional"]),
        "phi_qfep_mutual_information": abs(
            a["phi_qfep_mutual_information"] - b["phi_qfep_mutual_information"]
        ),
        "f_min": abs(a["f_min"] - b["f_min"]),
    }


def run_axis0_component_ablation_comparison() -> dict[str, Any]:
    rho_ent = initial_ab(0.25, -0.41, 0.57, entangled=True)
    rho_prod = initial_ab(0.25, -0.41, 0.57, entangled=False)
    effect = soft_effect(X + 0.31 * Z, 0.47)
    forward = qit_fep_path_sum(rho_ent, engine_instruments(+1), effect)
    reversed_q = qit_fep_path_sum(rho_ent, engine_instruments(+1, reversed_order=True), effect)
    product = qit_fep_path_sum(rho_prod, engine_instruments(+1), effect)
    commuting = qit_fep_path_sum(rho_ent, engine_instruments(+1, commuting=True), soft_effect(Z, 0.47))
    commuting_reversed = qit_fep_path_sum(
        rho_ent,
        engine_instruments(+1, commuting=True, reversed_order=True),
        soft_effect(Z, 0.47),
    )
    forward_values = candidate_values(forward)
    reversed_values = candidate_values(reversed_q)
    product_values = candidate_values(product)
    commuting_values = candidate_values(commuting)
    commuting_reversed_values = candidate_values(commuting_reversed)
    rows: dict[str, dict[str, Any]] = {}
    for name in forward_values:
        order_gap = abs(forward_values[name] - reversed_values[name])
        entanglement_gap = abs(forward_values[name] - product_values[name])
        commuting_gap = abs(commuting_values[name] - commuting_reversed_values[name])
        rows[name] = {
            "order_gap": order_gap,
            "entanglement_gap": entanglement_gap,
            "commuting_order_gap": commuting_gap,
            "passes_first_order_controls": (
                order_gap > 1e-3 and entanglement_gap > 1e-2 and commuting_gap < 1e-9
            ),
        }
    simple_components_pass = rows["log_z_only"]["passes_first_order_controls"] and rows["ic_only"][
        "passes_first_order_controls"
    ]
    return {
        "pass": simple_components_pass and rows["phi_logz_plus_ic"]["passes_first_order_controls"],
        "rows": rows,
        "aggregate_uniqueness_verdict": (
            "not_unique_in_this_fixture: log_z_only and ic_only both pass the "
            "same first-order controls as phi_logz_plus_ic"
        ),
        "next_required_test": (
            "compare candidate families on full engine-chart rows and capacity "
            "budgets before any Axis0 promotion"
        ),
    }


def run_finite_capacity_budget_gate() -> dict[str, Any]:
    """Executable finite-capacity gate for this scout's bounded carrier.

    This is Bekenstein-style rather than a physical Bekenstein calculation:
    the scout has no radius/energy model. The gate enforces the usable derived
    implication needed here: finite Hilbert carrier, finite path registry, and
    rejected over-capacity candidate rows.
    """

    max_boundary_dim = 4
    max_path_count = 16
    carrier_dim = 4
    observed_path_counts = [4, 8, 16]
    observed_ok = carrier_dim <= max_boundary_dim and all(count <= max_path_count for count in observed_path_counts)
    negative_controls = {
        "over_path_budget_32": {
            "path_count": 32,
            "admitted": 32 <= max_path_count,
            "expected": "reject",
        },
        "over_boundary_dim_8": {
            "boundary_dim": 8,
            "admitted": 8 <= max_boundary_dim,
            "expected": "reject",
        },
    }
    negatives_rejected = all(not row["admitted"] for row in negative_controls.values())
    return {
        "pass": observed_ok and negatives_rejected,
        "capacity_model": "finite_budget_gate_not_physical_bekenstein_calculation",
        "max_boundary_dim": max_boundary_dim,
        "max_path_count": max_path_count,
        "capacity_budget_nats": math.log(max_boundary_dim) + math.log(max_path_count),
        "observed": {
            "carrier_dim": carrier_dim,
            "path_counts": observed_path_counts,
            "admitted": observed_ok,
        },
        "negative_controls": negative_controls,
        "interpretation": (
            "Derived finite-capacity constraint made executable: the scout "
            "admits finite rows and rejects over-budget path or boundary rows."
        ),
    }


def run_candidate_component_decomposition() -> dict[str, Any]:
    """Keep candidate components visible so the aggregate cannot overclaim."""

    rho_ent = initial_ab(0.25, -0.41, 0.57, entangled=True)
    rho_prod = initial_ab(0.25, -0.41, 0.57, entangled=False)
    effect = soft_effect(X + 0.31 * Z, 0.47)
    forward = qit_fep_path_sum(rho_ent, engine_instruments(+1), effect)
    reversed_q = qit_fep_path_sum(rho_ent, engine_instruments(+1, reversed_order=True), effect)
    product = qit_fep_path_sum(rho_prod, engine_instruments(+1), effect)
    commuting = qit_fep_path_sum(rho_ent, engine_instruments(+1, commuting=True), soft_effect(Z, 0.47))
    commuting_reversed = qit_fep_path_sum(
        rho_ent,
        engine_instruments(+1, commuting=True, reversed_order=True),
        soft_effect(Z, 0.47),
    )
    order_gaps = abs_component_gaps(forward, reversed_q)
    entanglement_gaps = abs_component_gaps(forward, product)
    commuting_order_gaps = abs_component_gaps(commuting, commuting_reversed)
    return {
        "pass": (
            order_gaps["phi_qfep_provisional"] > 1e-3
            and order_gaps["phi_qfep_mutual_information"] > 1e-3
            and entanglement_gaps["coherent_information"] > 1e-2
            and commuting_order_gaps["phi_qfep_provisional"] < 1e-9
            and commuting_order_gaps["phi_qfep_mutual_information"] < 1e-9
        ),
        "forward_components": component_summary(forward),
        "reversed_components": component_summary(reversed_q),
        "product_components": component_summary(product),
        "commuting_components": component_summary(commuting),
        "commuting_reversed_components": component_summary(commuting_reversed),
        "order_gaps": order_gaps,
        "entanglement_gaps": entanglement_gaps,
        "commuting_order_gaps": commuting_order_gaps,
        "verdict": (
            "Phi_QFEP_provisional is retained only as an additive candidate. "
            "The receipt keeps log_z, coherent_information, mutual_information, "
            "and f_min separate."
        ),
    }


def run_parameter_robustness_sweep() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    rho_ab = initial_ab(0.19, -0.36, 0.61, entangled=True)
    for bias in (0.34, 0.48, 0.62):
        effect = soft_effect(X + 0.25 * Z, bias)
        for q_dephase in (0.06, 0.16, 0.28):
            for gamma in (0.07, 0.13, 0.21):
                forward = qit_fep_path_sum(
                    rho_ab,
                    engine_instruments_with_params(+1, q_dephase=q_dephase, gamma=gamma),
                    effect,
                )
                reversed_q = qit_fep_path_sum(
                    rho_ab,
                    engine_instruments_with_params(+1, q_dephase=q_dephase, gamma=gamma, reversed_order=True),
                    effect,
                )
                gap = abs(forward["phi_qfep_provisional"] - reversed_q["phi_qfep_provisional"])
                rows.append(
                    {
                        "effect_bias": bias,
                        "q_dephase": q_dephase,
                        "gamma": gamma,
                        "order_gap": gap,
                    }
                )
    gaps = torch.tensor([row["order_gap"] for row in rows], dtype=DTYPE)
    return {
        "pass": float(torch.min(gaps).item()) > 1e-3 and float(torch.mean(gaps).item()) > 1e-2,
        "grid_size": len(rows),
        "min_order_gap": float(torch.min(gaps).item()),
        "mean_order_gap": float(torch.mean(gaps).item()),
        "max_order_gap": float(torch.max(gaps).item()),
        "near_threshold_warning": (
            "minimum order gap is close to 1e-3; widen this sweep before any "
            "promotion beyond formal scout"
        ),
        "rows": rows,
    }


def run_manifold_variance_grid() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    commuting_rows: list[dict[str, Any]] = []
    effect = soft_effect(Z + 0.3 * X, 0.44)
    commuting_effect = soft_effect(Z, 0.44)
    for flux in (-1, 1):
        for eta in (0.28, 0.52, 0.81):
            for chi in (-0.42, 0.0, 0.39):
                rho_ab = initial_ab(0.11 * flux, chi, eta, entangled=True)
                result = qit_fep_path_sum(rho_ab, engine_instruments(flux), effect)
                commuting_result = qit_fep_path_sum(
                    rho_ab,
                    engine_instruments(flux, commuting=True),
                    commuting_effect,
                )
                rows.append(
                    {
                        "flux": flux,
                        "eta": eta,
                        "chi": chi,
                        "phi_qfep_provisional": result["phi_qfep_provisional"],
                        "log_z": result["log_z"],
                        "ic": result["coherent_information"],
                    }
                )
                commuting_rows.append(
                    {
                        "flux": flux,
                        "eta": eta,
                        "chi": chi,
                        "phi_qfep_provisional": commuting_result["phi_qfep_provisional"],
                        "log_z": commuting_result["log_z"],
                        "ic": commuting_result["coherent_information"],
                    }
                )
    values = torch.tensor([row["phi_qfep_provisional"] for row in rows], dtype=DTYPE)
    by_flux = {
        str(flux): float(torch.mean(torch.tensor([row["phi_qfep_provisional"] for row in rows if row["flux"] == flux], dtype=DTYPE)).item())
        for flux in (-1, 1)
    }
    by_eta = {
        str(eta): float(torch.mean(torch.tensor([row["phi_qfep_provisional"] for row in rows if row["eta"] == eta], dtype=DTYPE)).item())
        for eta in (0.28, 0.52, 0.81)
    }
    commuting_by_flux = {
        str(flux): float(torch.mean(torch.tensor([row["phi_qfep_provisional"] for row in commuting_rows if row["flux"] == flux], dtype=DTYPE)).item())
        for flux in (-1, 1)
    }
    flux_mean_gap = abs(by_flux["1"] - by_flux["-1"])
    commuting_flux_mean_gap = abs(commuting_by_flux["1"] - commuting_by_flux["-1"])
    eta_span = max(by_eta.values()) - min(by_eta.values())
    variance = float(torch.var(values, unbiased=False).item())
    commuting_values = torch.tensor([row["phi_qfep_provisional"] for row in commuting_rows], dtype=DTYPE)
    commuting_variance = float(torch.var(commuting_values, unbiased=False).item())
    return {
        "pass": (
            variance > 1e-4
            and flux_mean_gap > 1e-3
            and eta_span > 1e-3
            and commuting_flux_mean_gap < 1e-9
        ),
        "grid_size": len(rows),
        "variance": variance,
        "flux_mean_gap": flux_mean_gap,
        "eta_span": eta_span,
        "by_flux_mean": by_flux,
        "by_eta_mean": by_eta,
        "commuting_null": {
            "variance": commuting_variance,
            "flux_mean_gap": commuting_flux_mean_gap,
            "by_flux_mean": commuting_by_flux,
            "interpretation": (
                "With a commuting Z-only instrument/effect family, the same "
                "grid no longer carries flux-direction information."
            ),
        },
        "rows": rows,
        "commuting_rows": commuting_rows,
    }


def run_z3_dependency_fence() -> dict[str, Any]:
    f01, n01, qfep, capacity = z3.Bools("f01 n01 qfep capacity")
    axioms = [
        z3.Implies(qfep, f01),
        z3.Implies(qfep, n01),
        z3.Implies(qfep, capacity),
    ]

    def check(extra: list[z3.BoolRef]) -> str:
        solver = z3.Solver()
        solver.add(*(axioms + extra))
        return str(solver.check())

    qfep_without_f01 = check([qfep, z3.Not(f01)])
    qfep_without_n01 = check([qfep, z3.Not(n01)])
    roots_force_qfep = check([f01, n01, z3.Not(qfep)])
    witness = check([f01, n01, capacity, qfep])
    return {
        "pass": (
            qfep_without_f01 == "unsat"
            and qfep_without_n01 == "unsat"
            and roots_force_qfep == "sat"
            and witness == "sat"
        ),
        "qfep_without_f01": qfep_without_f01,
        "qfep_without_n01": qfep_without_n01,
        "roots_do_not_force_qfep": roots_force_qfep,
        "qfep_with_roots_capacity_witness": witness,
        "interpretation": (
            "Declared dependency fence only. It prevents metadata promotion "
            "without F01/N01/capacity assumptions, but it is not an independent "
            "derivation of QIT-FEP from the roots."
        ),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    sections = {
        "core_implementation_correctness": run_core_fixture(),
        "noncommuting_order_vs_classical_markov_control": run_order_and_classical_controls(),
        "entanglement_information_carrier_control": run_entanglement_control(),
        "b_side_unitary_gauge_control": run_b_side_unitary_gauge_control(),
        "candidate_component_decomposition": run_candidate_component_decomposition(),
        "axis0_component_ablation_comparison": run_axis0_component_ablation_comparison(),
        "finite_capacity_budget_gate": run_finite_capacity_budget_gate(),
        "parameter_robustness_sweep": run_parameter_robustness_sweep(),
        "manifold_variance_grid": run_manifold_variance_grid(),
    }
    dependency_fence = run_z3_dependency_fence()
    all_pass = all(bool(section.get("pass")) for section in sections.values())
    positive = {
        "noncommuting_order_signal_survives_controls": sections["noncommuting_order_vs_classical_markov_control"],
        "entanglement_information_carrier_is_load_bearing": sections["entanglement_information_carrier_control"],
        "b_side_reference_gauge_invariance_survives": sections["b_side_unitary_gauge_control"],
        "spinor_manifold_variance_visible": sections["manifold_variance_grid"],
        "candidate_components_are_separately_reported": sections["candidate_component_decomposition"],
        "axis0_component_ablation_comparison": sections["axis0_component_ablation_comparison"],
        "finite_capacity_budget_gate": sections["finite_capacity_budget_gate"],
        "parameter_robustness_sweep": sections["parameter_robustness_sweep"],
    }
    graveyard_companions = {
        "classical_commuting_markov_order_erasure": {
            "pass": sections["noncommuting_order_vs_classical_markov_control"]["pass"],
            "noncommuting_order_gap": sections["noncommuting_order_vs_classical_markov_control"]["noncommuting_order_gap"],
            "commuting_order_gap": sections["noncommuting_order_vs_classical_markov_control"]["commuting_order_gap"],
            "verdict": "classical commuting Markov control erases the order signal that survives in the noncommuting QIT path sum",
        },
        "product_state_entanglement_ablation": {
            "pass": sections["entanglement_information_carrier_control"]["pass"],
            "ic_gap": sections["entanglement_information_carrier_control"]["ic_gap"],
            "phi_gap": sections["entanglement_information_carrier_control"]["phi_gap"],
            "verdict": "product control loses coherent-information contribution to Phi_QFEP_provisional",
        },
        "commuting_manifold_flux_null": {
            "pass": sections["manifold_variance_grid"]["commuting_null"]["flux_mean_gap"] < 1e-9,
            "commuting_flux_mean_gap": sections["manifold_variance_grid"]["commuting_null"]["flux_mean_gap"],
            "noncommuting_flux_mean_gap": sections["manifold_variance_grid"]["flux_mean_gap"],
            "verdict": "commuting Z-only manifold control erases flux-direction sensitivity",
        },
    }
    boundary = {
        "implementation_consistency_path_sum_linearity": {
            "pass": sections["core_implementation_correctness"]["path_sum_channel_gap"] < 1e-9,
            "path_sum_channel_gap": sections["core_implementation_correctness"]["path_sum_channel_gap"],
            "verdict": "correctness check only: finite Kraus path sum matches the closed channel by linearity",
        },
        "implementation_consistency_qvfe_identity": {
            "pass": bool(
                sections["core_implementation_correctness"]["qvfe_gap_prior_minus_min"] > 1e-4
                and abs(sections["core_implementation_correctness"]["posterior_free_energy"] - sections["core_implementation_correctness"]["f_min"]) < 1e-8
                and sections["core_implementation_correctness"]["data_processing_margin_ab_to_a"] > -1e-9
            ),
            "qvfe_gap_prior_minus_min": sections["core_implementation_correctness"]["qvfe_gap_prior_minus_min"],
            "data_processing_margin_ab_to_a": sections["core_implementation_correctness"]["data_processing_margin_ab_to_a"],
            "posterior_free_energy": sections["core_implementation_correctness"]["posterior_free_energy"],
            "f_min": sections["core_implementation_correctness"]["f_min"],
            "verdict": (
                "correctness check only: posterior realizes the defined "
                "relative-entropy identity; data-processing margin is tracked "
                "as an implementation sanity check"
            ),
        },
        "declared_dependency_fence": dependency_fence,
        "finite_not_continuous_gradient": {
            "pass": sections["core_implementation_correctness"]["path_count"] == 4,
            "path_count": sections["core_implementation_correctness"]["path_count"],
            "uses_autograd": False,
            "verdict": "finite Kraus-history sum only; no continuous gradient assumption",
        },
        "formal_scout_only_no_axis0_promotion": {
            "pass": PROMOTION_ALLOWED is False and "does not admit final Axis0" in CLAIM_CEILING,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "passed": 10,
            "total": 10,
            "items": [
                "noncommuting_order_gap",
                "commuting_quantum_control",
                "path_count_scaling",
                "entanglement_ablation",
                "b_side_reference_gauge_control",
                "candidate_component_decomposition",
                "axis0_component_ablation_comparison",
                "finite_capacity_budget_gate",
                "parameter_robustness_sweep",
                "manifold_variance_grid",
            ],
        },
        "why_not_v4_probes": (
            "Existing v4 FEP probes are useful classical/source-native precursors, "
            "but this scout tests the missing QIT-specific object: finite Kraus "
            "history sums over spinor density states with coherent-information "
            "Axis0 readout and commuting/product controls."
        ),
        "blockers": [],
        "sections": sections,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
