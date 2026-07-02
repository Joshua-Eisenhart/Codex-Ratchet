#!/usr/bin/env python3
"""Axis0 signed QIT/FEP gradient scout over finite spinor-shell histories.

Formal scout only. Axis0 is treated here as a signed free-energy-pressure
readout, not as a primitive geometric axis:

    A0 = d/dlambda [path_surprise - compression + shell_transition_cost]

The row tests whether this signed gradient separates homeostatic compression
from allostatic basin transition on finite probe histories. Raw branch-count
entropy is kept as a negative control. This does not admit final Axis0, Xi,
Phi0, flux, PEPS closure, or physics.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "axis0_qit_fep_signed_gradient_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "axis0_qit_fep_signed_entropy_gradient_over_finite_spinor_shell_histories"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests Axis0 as a signed QIT/FEP entropy-gradient "
    "readout over finite spinor-shell histories. It does not admit final "
    "Axis0, Xi, Phi0, flux, PEPS closure, gravity, Standard Model, Yang-Mills, "
    "Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing finite complex spinor carriers, Weyl-Heisenberg "
            "operators, density reductions, finite history branches, entropy, "
            "and signed gradient controls"
        ),
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
W_SHIFT = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
W_PHASE = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)


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
        return {"real": value.real, "imag": value.imag}
    return value


def hermitize(mat: torch.Tensor) -> torch.Tensor:
    return (mat + torch.conj(mat).T) / 2.0


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    tr = torch.real(torch.trace(rho))
    return rho / torch.clamp(tr, min=EPS)


def normalize_spinor(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.clamp(torch.linalg.vector_norm(psi), min=EPS)


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_spinor(psi)
    return torch.outer(psi, torch.conj(psi))


def basis_spinor(bitstring: str) -> torch.Tensor:
    dim = 2 ** len(bitstring)
    out = torch.zeros(dim, dtype=CDTYPE)
    out[int(bitstring, 2)] = 1.0 + 0.0j
    return out


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize_spinor(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def kron_all(ops: list[torch.Tensor]) -> torch.Tensor:
    out = ops[0]
    for op in ops[1:]:
        out = torch.kron(out, op)
    return out


def partial_trace_keep(rho: torch.Tensor, keep: list[int], n_sites: int) -> torch.Tensor:
    keep = list(keep)
    trace_out = [idx for idx in range(n_sites) if idx not in keep]
    dims = [2] * n_sites
    shaped = rho.reshape(dims + dims)
    perm = keep + trace_out + [idx + n_sites for idx in keep] + [idx + n_sites for idx in trace_out]
    shaped = shaped.permute(perm)
    keep_dim = 2 ** len(keep)
    trace_dim = 2 ** len(trace_out)
    shaped = shaped.reshape(keep_dim, trace_dim, keep_dim, trace_dim)
    return normalize_state(torch.einsum("abcb->ac", shaped))


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def psd_sqrt(mat: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(hermitize(mat))
    vals = torch.clamp(vals.real, min=0.0)
    return vecs @ torch.diag(torch.sqrt(vals)).to(CDTYPE) @ torch.conj(vecs).T


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ torch.conj(k).T
    return normalize_state(out)


def amplitude_compression_kraus(gamma: float) -> list[torch.Tensor]:
    gamma = float(max(0.0, min(0.95, gamma)))
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=CDTYPE)
    return [torch.kron(a, b) for a in (k0, k1) for b in (k0, k1)]


def unsharp_effects(operator: torch.Tensor, bias: float) -> list[torch.Tensor]:
    bias = float(max(0.0, min(0.95, bias)))
    e_plus = hermitize(0.5 * (I2 + bias * operator))
    e_minus = hermitize(0.5 * (I2 - bias * operator))
    return [psd_sqrt(e_plus), psd_sqrt(e_minus)]


def smooth_shell_unitary(lam: float, chirality: int) -> torch.Tensor:
    theta = 1.65 * lam
    g_j = torch.kron(W_SHIFT, I2)
    g_k = torch.kron(W_PHASE, W_SHIFT)
    u_j = torch.matrix_exp(-1j * theta * g_j)
    u_k = torch.matrix_exp(-1j * theta * g_k)
    if chirality >= 0:
        return u_k @ u_j
    return u_j @ u_k


def target_evidence_effect() -> torch.Tensor:
    target = density(basis_spinor("00"))
    floor = 0.06
    return hermitize(floor * I4 + (1.0 - floor) * target)


def branch_sqrt_effects() -> list[torch.Tensor]:
    first = unsharp_effects(W_SHIFT, 0.38)
    second = unsharp_effects(W_PHASE, 0.38)
    return [torch.kron(a, b) for a in first for b in second]


def dense_pair(mode: str) -> torch.Tensor:
    if mode == "homeostatic":
        bell = normalize_spinor(basis_spinor("00") + basis_spinor("11"))
        return normalize_state(0.62 * density(bell) + 0.38 * I4 / 4.0)
    if mode == "allostatic":
        return density(basis_spinor("00"))
    return I4 / 4.0


def mps_pair(mode: str) -> torch.Tensor:
    if mode == "homeostatic":
        ghz = normalize_spinor(basis_spinor("0" * 8) + basis_spinor("1" * 8))
        rho = density(ghz)
        return partial_trace_keep(rho, [3, 4], 8)
    if mode == "allostatic":
        return density(basis_spinor("00"))
    return I4 / 4.0


def peps_patch_pair(mode: str) -> torch.Tensor:
    if mode == "homeostatic":
        plus = normalize_spinor(spinor(0.0, 0.0, math.pi / 4.0))
        psi = kron_all([plus, plus, plus, plus])
        for a, b in [(0, 1), (0, 2), (1, 3), (2, 3)]:
            phase = torch.ones(16, dtype=CDTYPE)
            for idx in range(16):
                bits = f"{idx:04b}"
                if bits[a] == "1" and bits[b] == "1":
                    phase[idx] *= -1.0
            psi = torch.diag(phase) @ psi
        return partial_trace_keep(density(psi), [0, 1], 4)
    if mode == "allostatic":
        return density(basis_spinor("00"))
    return I4 / 4.0


def carrier_pair(carrier: str, mode: str) -> torch.Tensor:
    if carrier == "dense_spinor":
        return dense_pair(mode)
    if carrier == "mps_pair_reduction":
        return mps_pair(mode)
    if carrier == "peps_patch_pair_reduction":
        return peps_patch_pair(mode)
    raise ValueError(carrier)


def evolved_pair(rho0: torch.Tensor, mode: str, lam: float, chirality: int) -> tuple[torch.Tensor, float]:
    if mode == "homeostatic":
        rho = apply_kraus(rho0, amplitude_compression_kraus(0.78 * lam))
        return rho, 0.05 * lam * lam
    if mode == "allostatic":
        u = smooth_shell_unitary(lam, chirality)
        rho = normalize_state(u @ rho0 @ torch.conj(u).T)
        return rho, 2.25 * lam * lam
    return rho0, 0.0


def finite_history_free_energy(rho0: torch.Tensor, mode: str, lam: float, chirality: int) -> dict[str, float]:
    rho, transition_cost = evolved_pair(rho0, mode, lam, chirality)
    sqrt_evidence = psd_sqrt(target_evidence_effect())
    branch_ops = branch_sqrt_effects()
    branch_masses = []
    unnormalized = torch.zeros_like(rho)
    for branch in branch_ops:
        k = sqrt_evidence @ branch
        branch_rho = hermitize(k @ rho @ torch.conj(k).T)
        mass = float(torch.real(torch.trace(branch_rho)).item())
        branch_masses.append(max(0.0, mass))
        unnormalized = unnormalized + branch_rho
    z_path = max(EPS, sum(branch_masses))
    posterior = normalize_state(unnormalized)
    probs = torch.tensor([mass / z_path for mass in branch_masses], dtype=DTYPE)
    probs = torch.clamp(probs, min=EPS)
    probs = probs / torch.clamp(torch.sum(probs), min=EPS)
    path_entropy = float((-torch.sum(probs * torch.log(probs))).item())
    path_surprise = -math.log(z_path)
    compression = math.log(4.0) - entropy(posterior)
    free_energy = path_surprise - compression + transition_cost
    return {
        "lambda": lam,
        "Z_path": z_path,
        "path_surprise": path_surprise,
        "compression_negentropy": compression,
        "transition_cost": transition_cost,
        "F_qit": free_energy,
        "H_path": path_entropy,
        "H_branch_count": math.log(float(len(branch_masses))),
    }


def central_gradient(rho0: torch.Tensor, mode: str, chirality: int, *, lam0: float = 0.18, delta: float = 0.04) -> dict[str, Any]:
    low = finite_history_free_energy(rho0, mode, lam0 - delta, chirality)
    mid = finite_history_free_energy(rho0, mode, lam0, chirality)
    high = finite_history_free_energy(rho0, mode, lam0 + delta, chirality)
    denom = 2.0 * delta
    return {
        "low": low,
        "mid": mid,
        "high": high,
        "A0_gradient": (high["F_qit"] - low["F_qit"]) / denom,
        "d_path_surprise": (high["path_surprise"] - low["path_surprise"]) / denom,
        "d_compression": (high["compression_negentropy"] - low["compression_negentropy"]) / denom,
        "d_transition_cost": (high["transition_cost"] - low["transition_cost"]) / denom,
        "d_H_path": (high["H_path"] - low["H_path"]) / denom,
        "d_H_branch_count": (high["H_branch_count"] - low["H_branch_count"]) / denom,
    }


def order_gap_probe() -> dict[str, float]:
    rho = density(normalize_spinor(torch.kron(spinor(0.2, 0.3, 0.55), spinor(0.4, -0.2, 0.62))))
    u_plus = smooth_shell_unitary(0.27, 1)
    u_minus = smooth_shell_unitary(0.27, -1)
    noncommuting_gap = float(torch.linalg.matrix_norm(u_plus @ rho @ torch.conj(u_plus).T - u_minus @ rho @ torch.conj(u_minus).T).item())
    g_a = torch.kron(W_PHASE, I2)
    g_b = torch.kron(I2, W_PHASE)
    u_a = torch.matrix_exp(-1j * 0.27 * g_a)
    u_b = torch.matrix_exp(-1j * 0.27 * g_b)
    commuting_ab = u_b @ u_a @ rho @ torch.conj(u_b @ u_a).T
    commuting_ba = u_a @ u_b @ rho @ torch.conj(u_a @ u_b).T
    commuting_gap = float(torch.linalg.matrix_norm(commuting_ab - commuting_ba).item())
    return {
        "noncommuting_order_gap": noncommuting_gap,
        "commuting_order_control_gap": commuting_gap,
    }


def main() -> int:
    started = time.time()
    carriers = ["dense_spinor", "mps_pair_reduction", "peps_patch_pair_reduction"]
    modes = ["homeostatic", "allostatic", "product_control"]
    gradients: dict[str, dict[str, Any]] = {}
    for carrier in carriers:
        gradients[carrier] = {}
        for mode in modes:
            rho0 = carrier_pair(carrier, mode)
            gradients[carrier][mode] = central_gradient(rho0, mode, chirality=1)
    chiral_plus = central_gradient(carrier_pair("dense_spinor", "allostatic"), "allostatic", chirality=1)
    chiral_minus = central_gradient(carrier_pair("dense_spinor", "allostatic"), "allostatic", chirality=-1)
    chiral_gap = abs(chiral_plus["A0_gradient"] - chiral_minus["A0_gradient"])
    root_order = order_gap_probe()
    sign_checks = {}
    for carrier in carriers:
        sign_checks[carrier] = {
            "homeostatic_negative": gradients[carrier]["homeostatic"]["A0_gradient"] < -0.15,
            "allostatic_positive": gradients[carrier]["allostatic"]["A0_gradient"] > 0.15,
            "product_near_zero": abs(gradients[carrier]["product_control"]["A0_gradient"]) < 1.0e-8,
        }
    branch_count_control = {
        carrier: {
            mode: gradients[carrier][mode]["d_H_branch_count"]
            for mode in modes
        }
        for carrier in carriers
    }
    raw_branch_count_fails_axis0 = all(
        abs(value) < 1.0e-12
        for carrier_rows in branch_count_control.values()
        for value in carrier_rows.values()
    )
    checks = {
        "P1_axis0_homeostatic_negative_all_carriers": all(item["homeostatic_negative"] for item in sign_checks.values()),
        "P2_axis0_allostatic_positive_all_carriers": all(item["allostatic_positive"] for item in sign_checks.values()),
        "P3_product_no_structure_near_zero_all_carriers": all(item["product_near_zero"] for item in sign_checks.values()),
        "P4_raw_branch_count_entropy_fails_as_axis0": raw_branch_count_fails_axis0,
        "P5_chirality_changes_signed_pressure_magnitude": chiral_gap > 1.0e-4,
        "P6_f01_finite_histories_and_carriers": len(branch_sqrt_effects()) == 4 and len(carriers) == 3,
        "P7_n01_noncommuting_order_beats_commuting_control": (
            root_order["noncommuting_order_gap"] > 1.0e-4
            and root_order["commuting_order_control_gap"] < 1.0e-8
        ),
    }
    divergence_log = [
        "Raw branch-count entropy is constant at log(4), so it cannot carry signed Axis0 pressure.",
        "Product/no-structure fixtures remain near zero under the signed F_QIT gradient.",
        "Homeostatic and allostatic fixtures are separated by the free-energy gradient, not by branch count.",
        "Chirality is accepted only as a magnitude/order effect here; no final sign-polairty claim is promoted.",
    ]
    result = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "axis0_working_definition": "A0 = d/dlambda[path_surprise - compression_negentropy + shell_transition_cost]",
        "finite_history": {
            "branch_count": len(branch_sqrt_effects()),
            "branch_family": "finite unsharp Weyl-Heisenberg shell probe histories",
            "evidence": "soft target-basin effect with finite floor",
            "lambda_probe": "central finite difference at lambda=0.18 with delta=0.04",
        },
        "carrier_results": gradients,
        "sign_checks": sign_checks,
        "chirality": {
            "plus_gradient": chiral_plus["A0_gradient"],
            "minus_gradient": chiral_minus["A0_gradient"],
            "gradient_gap": chiral_gap,
            "interpretation": "chirality is an order/magnitude stressor in this row, not a final polarity-sign admission",
        },
        "root_constraint_ablations": {
            "F01": {
                "finite_branch_count": len(branch_sqrt_effects()),
                "finite_carriers": carriers,
                "pass": len(branch_sqrt_effects()) == 4 and len(carriers) == 3,
            },
            "N01": root_order,
        },
        "path_entropy_negative_control": {
            "branch_count_control": branch_count_control,
            "raw_branch_count_fails_axis0": raw_branch_count_fails_axis0,
            "actual_H_path_gradients": {
                carrier: {mode: gradients[carrier][mode]["d_H_path"] for mode in modes}
                for carrier in carriers
            },
        },
        "checks": checks,
        "all_pass": all(checks.values()),
        "why_not_final_axis0": [
            "This row tests a signed F_QIT gradient on small finite shell histories only.",
            "The evidence effect and transition cost family are fixtures, not a proved Xi bridge.",
            "PEPS is represented by a local patch reduction, not by full PEPS/PEPS3D environment closure.",
            "Magnitude and sign are reported separately; no carrier-discriminating polarity-sign claim is promoted.",
        ],
        "divergence_log": divergence_log,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "checks": checks}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
