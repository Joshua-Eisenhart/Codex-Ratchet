#!/usr/bin/env python3
"""PyTorch leg for foundation_nested_hopf_weyl_signed_cut_ratchet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import torch
import torch.func as torch_func


PIN_SPEC = """object_id=foundation_nested_hopf_weyl_signed_cut_ratchet
rung_count=3
eta_shells_rad=[eta_1=1.17,eta_2=0.86,eta_3=0.53] with eta_1 > eta_2 > eta_3 nested Hopf tori in S^3
stacking_order=Stack_r = Phi_r after Phi_{r-1} after ... after Phi_1; adjacent order test compares Phi_r after Phi_{r+1} vs Phi_{r+1} after Phi_r on rho_probe=rho_2
constraint_filters_left_sheet=K_1=[[1,0],[0,-1]], K_2=[[1,1],[1,-1]], K_3=[[1,1],[0,1]], Phi_r(rho)=normalize((K_r kron I_R) rho (K_r kron I_R)^adjoint)
rho_family=rho_r=|psi_r><psi_r|, |psi_r>=cos(theta_r)|L0 R0>+sin(theta_r)|L1 R1>, theta_r=0.70*(r-1)/2 for r=1,2,3
separable_control=rho_sep_r=diag(cos(theta_r)^2,sin(theta_r)^2)_L kron diag(cos(theta_r)^2,sin(theta_r)^2)_R
cut=A|B is Weyl-L sheet vs Weyl-R sheet
entropy_log_base=e
probe_sets=M_1=[Z_L Z_R]; M_2=M_1+[X_L X_R]; M_3=M_2+[Z_L,Z_R,Y_L Y_R]
claim_ceiling=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false; feeds Xi/Axis-0 bridge problem but does not close bridge, Axis0, manifold, or M(C)
"""

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_nested_hopf_weyl_signed_cut_ratchet"
ENGINE = "pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
KAPPA = 0.70
TOL = 1.0e-9

torch.set_default_dtype(torch.float64)

SOURCE_DEPENDENCIES = [
    ROOT / "system_v5/julia_carrier/clifford_torus_nested_hopf_foliation.jl",
    ROOT / "system_v5/julia_carrier/jax_clifford_torus_nested_hopf_foliation.py",
    ROOT / "system_v5/julia_carrier/weyl_sheet_pair_probe.jl",
    ROOT / "system_v5/julia_carrier/jax_weyl_sheet_pair_probe.py",
    ROOT / "system_v5/ops/formal_scouts/foundation_qit_operator_composition_mcp_jax.py",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing torch.linalg.eigvalsh entropy readouts, trace-norm order gaps, and torch.func.jacrev crossing-rung derivative; backed by sim_pytorch_capability",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive import/runtime spelling for PyTorch tensor arithmetic",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "validator-facing aligned PyTorch autograd surface; jacrev computes d S(A|B)/d coupling at the rung-2 crossing",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, timestamp, path, and sha256 receipt logic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "torch": "supportive",
    "torch.func": "supportive",
    "python_stdlib": "supportive",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().real.item())
    return float(value)


I2 = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)
X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)
Y = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=torch.complex128)
Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
K_FILTERS = {
    1: Z,
    2: torch.tensor([[1.0, 1.0], [1.0, -1.0]], dtype=torch.complex128),
    3: torch.tensor([[1.0, 1.0], [0.0, 1.0]], dtype=torch.complex128),
}
COMMUTING_FILTERS = {
    1: torch.tensor([[1.0, 0.0], [0.0, 0.80]], dtype=torch.complex128),
    2: torch.tensor([[1.0, 0.0], [0.0, 0.60]], dtype=torch.complex128),
    3: torch.tensor([[1.0, 0.0], [0.0, 0.40]], dtype=torch.complex128),
}
ETA_SHELLS = {1: 1.17, 2: 0.86, 3: 0.53}


def theta(rung: int, *, kappa: torch.Tensor | None = None) -> torch.Tensor:
    k = torch.tensor(KAPPA, dtype=torch.float64) if kappa is None else kappa
    return k * float(rung - 1) / 2.0


def rho_for_rung(rung: int) -> torch.Tensor:
    th = theta(rung)
    psi = torch.stack(
        [
            torch.cos(th).to(torch.complex128),
            torch.tensor(0.0, dtype=torch.complex128),
            torch.tensor(0.0, dtype=torch.complex128),
            torch.sin(th).to(torch.complex128),
        ]
    )
    return torch.outer(psi, torch.conj(psi))


def separable_rho_for_rung(rung: int) -> torch.Tensor:
    th = theta(rung)
    probs = torch.stack([torch.cos(th) ** 2, torch.sin(th) ** 2]).to(torch.complex128)
    left = torch.diag(probs)
    right = torch.diag(probs)
    return torch.kron(left, right)


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return 0.5 * (rho + torch.conj(rho.T))


def trace_real(rho: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.trace(rho))


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    herm = hermitize(rho)
    return herm / trace_real(herm)


def apply_filter(rho: torch.Tensor, filter_matrix: torch.Tensor) -> torch.Tensor:
    lifted = torch.kron(filter_matrix, I2)
    return normalize_density(lifted @ rho @ torch.conj(lifted.T))


def stack_state(rung: int, rho: torch.Tensor, filters: dict[int, torch.Tensor]) -> torch.Tensor:
    out = rho
    for idx in range(1, rung + 1):
        out = apply_filter(out, filters[idx])
    return out


def partial_trace_left_to_b(rho: torch.Tensor) -> torch.Tensor:
    shaped = rho.reshape(2, 2, 2, 2)
    out = torch.zeros((2, 2), dtype=torch.complex128)
    for left in range(2):
        out = out + shaped[left, :, left, :]
    return out


def entropy_vn(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh(hermitize(rho))
    positive = vals > TOL
    safe = torch.where(positive, vals, torch.ones_like(vals))
    return -torch.sum(torch.where(positive, vals * torch.log(safe), torch.zeros_like(vals)))


def conditional_entropy(rho: torch.Tensor) -> torch.Tensor:
    return entropy_vn(rho) - entropy_vn(partial_trace_left_to_b(rho))


def entropy_components(rho: torch.Tensor) -> dict[str, float]:
    s_ab = entropy_vn(rho)
    s_b = entropy_vn(partial_trace_left_to_b(rho))
    return {"S_AB": py_float(s_ab), "S_B": py_float(s_b)}


def conditional_entropy_crossing_from_kappa(kappa: torch.Tensor) -> torch.Tensor:
    th = kappa / 2.0
    p = torch.sin(th) ** 2
    q = 1.0 - p
    h = -(p * torch.log(p) + q * torch.log(q))
    return -h


def trace_norm_hermitian(matrix: torch.Tensor) -> torch.Tensor:
    return torch.sum(torch.abs(torch.linalg.eigvalsh(hermitize(matrix))))


def order_gap(first: torch.Tensor, second: torch.Tensor, rho_probe: torch.Tensor) -> float:
    left = apply_filter(apply_filter(rho_probe, second), first)
    right = apply_filter(apply_filter(rho_probe, first), second)
    return py_float(trace_norm_hermitian(left - right))


def probe_ops() -> dict[str, torch.Tensor]:
    return {
        "Z_L Z_R": torch.kron(Z, Z),
        "X_L X_R": torch.kron(X, X),
        "Z_L": torch.kron(Z, I2),
        "Z_R": torch.kron(I2, Z),
        "Y_L Y_R": torch.kron(Y, Y),
    }


def probe_family(rung: int) -> list[str]:
    if rung == 1:
        return ["Z_L Z_R"]
    if rung == 2:
        return ["Z_L Z_R", "X_L X_R"]
    return ["Z_L Z_R", "X_L X_R", "Z_L", "Z_R", "Y_L Y_R"]


def expectation(rho: torch.Tensor, op: torch.Tensor) -> float:
    return py_float(torch.real(torch.trace(op @ rho)))


def class_count(vectors: list[list[float]]) -> int:
    classes: list[list[float]] = []
    for vector in vectors:
        if not any(all(abs(a - b) <= 1.0e-8 for a, b in zip(vector, existing)) for existing in classes):
            classes.append(vector)
    return len(classes)


def quotient_report() -> dict[str, Any]:
    ops = probe_ops()
    rhos = [rho_for_rung(r) for r in (1, 2, 3)]
    report: dict[str, Any] = {}
    for rung in (1, 2, 3):
        family = probe_family(rung)
        vectors = [[expectation(rho, ops[name]) for name in family] for rho in rhos]
        report[f"M_{rung}"] = {
            "operators": family,
            "operator_count": len(family),
            "distinguishable_class_count": class_count(vectors),
            "expectation_vectors_by_rung": {str(idx + 1): vectors[idx] for idx in range(3)},
        }
    return report


def density_diagnostics(rho: torch.Tensor) -> dict[str, Any]:
    vals = torch.linalg.eigvalsh(hermitize(rho))
    return {
        "trace": py_float(trace_real(rho)),
        "min_eigenvalue": py_float(torch.min(vals)),
        "hermitian_residual": py_float(torch.max(torch.abs(rho - torch.conj(rho.T)))),
        "psd": py_float(torch.min(vals)) >= -1.0e-9,
    }


def build_result() -> dict[str, Any]:
    quotients = quotient_report()
    rhos = {r: rho_for_rung(r) for r in (1, 2, 3)}
    sep_rhos = {r: separable_rho_for_rung(r) for r in (1, 2, 3)}
    rho_probe = rhos[2]
    conditional = {r: py_float(conditional_entropy(rhos[r])) for r in (1, 2, 3)}
    signed_cut = {r: -conditional[r] for r in (1, 2, 3)}
    sep_conditional = {r: py_float(conditional_entropy(sep_rhos[r])) for r in (1, 2, 3)}
    carrier_components = {r: entropy_components(rhos[r]) for r in (1, 2, 3)}
    sep_components = {r: entropy_components(sep_rhos[r]) for r in (1, 2, 3)}
    gaps = {
        "r1_r2": order_gap(K_FILTERS[1], K_FILTERS[2], rho_probe),
        "r2_r3": order_gap(K_FILTERS[2], K_FILTERS[3], rho_probe),
    }
    commuting_gaps = {
        "r1_r2": order_gap(COMMUTING_FILTERS[1], COMMUTING_FILTERS[2], rho_probe),
        "r2_r3": order_gap(COMMUTING_FILTERS[2], COMMUTING_FILTERS[3], rho_probe),
    }
    crossing_grad = torch_func.jacrev(conditional_entropy_crossing_from_kappa)(torch.tensor(KAPPA, dtype=torch.float64))
    negative_crossings = [r for r, value in conditional.items() if value < -TOL]
    class_counts = [quotients[f"M_{r}"]["distinguishable_class_count"] for r in (1, 2, 3)]
    source_deps = {str(path.relative_to(ROOT)): file_sha256(path) for path in SOURCE_DEPENDENCIES}
    shared_scalars = {
        "conditional_entropy_r1": conditional[1],
        "conditional_entropy_r2": conditional[2],
        "conditional_entropy_r3": conditional[3],
        "signed_cut_Ic_r1": signed_cut[1],
        "signed_cut_Ic_r2": signed_cut[2],
        "signed_cut_Ic_r3": signed_cut[3],
        "separable_conditional_entropy_r1": sep_conditional[1],
        "separable_conditional_entropy_r2": sep_conditional[2],
        "separable_conditional_entropy_r3": sep_conditional[3],
        "carrier_S_AB_r1": carrier_components[1]["S_AB"],
        "carrier_S_AB_r2": carrier_components[2]["S_AB"],
        "carrier_S_AB_r3": carrier_components[3]["S_AB"],
        "carrier_S_B_r1": carrier_components[1]["S_B"],
        "carrier_S_B_r2": carrier_components[2]["S_B"],
        "carrier_S_B_r3": carrier_components[3]["S_B"],
        "separable_control_S_AB_r1": sep_components[1]["S_AB"],
        "separable_control_S_AB_r2": sep_components[2]["S_AB"],
        "separable_control_S_AB_r3": sep_components[3]["S_AB"],
        "separable_control_S_B_r1": sep_components[1]["S_B"],
        "separable_control_S_B_r2": sep_components[2]["S_B"],
        "separable_control_S_B_r3": sep_components[3]["S_B"],
        "order_gap_r1_r2": gaps["r1_r2"],
        "order_gap_r2_r3": gaps["r2_r3"],
        "commuting_order_gap_r1_r2": commuting_gaps["r1_r2"],
        "commuting_order_gap_r2_r3": commuting_gaps["r2_r3"],
        "quotient_class_count_M1": float(class_counts[0]),
        "quotient_class_count_M2": float(class_counts[1]),
        "quotient_class_count_M3": float(class_counts[2]),
        "negative_crossing_rung": float(negative_crossings[0] if negative_crossings else 0),
        "boundary_rung1_conditional_entropy": conditional[1],
    }
    controls = {
        "separable_nonnegative_every_rung": all(value >= -TOL for value in sep_conditional.values()),
        "commuting_control_zero_order_gap": all(value <= TOL for value in commuting_gaps.values()),
        "commuting_control_classification": "not_a_ratchet_zero_order_gap",
        "boundary_rung_count_1_no_signed_cut_crossing": conditional[1] >= -TOL,
        "carrier_conditional_entropy_strictly_decreases": conditional[1] > conditional[2] > conditional[3],
        "carrier_crosses_negative": bool(negative_crossings),
        "order_gap_nonzero_every_adjacent_pair": all(value > TOL for value in gaps.values()),
        "quotient_tightens": class_counts[0] < class_counts[1] and class_counts[1] <= class_counts[2],
        "torch_func_jacrev_crossing_gradient_negative": py_float(crossing_grad) < 0.0,
    }
    rungs = []
    for rung in (1, 2, 3):
        stack = stack_state(rung, rhos[rung], K_FILTERS)
        rungs.append(
            {
                "rung": rung,
                "eta": ETA_SHELLS[rung],
                "theta": py_float(theta(rung)),
                "probe_family": probe_family(rung),
                "density": density_diagnostics(rhos[rung]),
                "stacked_density": density_diagnostics(stack),
                "conditional_entropy_S_A_given_B": conditional[rung],
                "entropy_components": carrier_components[rung],
                "signed_cut_Ic": signed_cut[rung],
                "separable_control_S_A_given_B": sep_conditional[rung],
                "separable_control_entropy_components": sep_components[rung],
                "density_quotient": quotients[f"M_{rung}"],
            }
        )
    all_pass = bool(
        all(value["psd"] for value in (density_diagnostics(rhos[r]) for r in (1, 2, 3)))
        and all(controls[key] for key in controls if isinstance(controls[key], bool))
        and READS_PEER_RESULT is False
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": False},
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_dependencies": source_deps,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["pytorch", "torch", "torch.func", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["pytorch", "torch.func"],
        "control_only_tools": [],
        "rungs": rungs,
        "quotient": quotients,
        "signed_cut": {
            "cut": "Weyl-L sheet | Weyl-R sheet",
            "log_base": "e",
            "conditional_entropy_by_rung": {str(k): v for k, v in conditional.items()},
            "signed_cut_Ic_by_rung": {str(k): v for k, v in signed_cut.items()},
            "headline_claim_under_test": "S(A|B) decreases monotonically and goes negative once nesting forces L/R entanglement",
        },
        "order_gaps": gaps,
        "controls": controls,
        "negative_controls": {
            "separable": {str(k): v for k, v in sep_conditional.items()},
            "commuting": commuting_gaps,
            "boundary": {"rung_count": 1, "conditional_entropy": conditional[1], "crosses_negative": conditional[1] < -TOL},
        },
        "autograd": {
            "function": "torch.func.jacrev d S(A|B)_rung2 / d coupling",
            "coupling": KAPPA,
            "gradient": py_float(crossing_grad),
            "crossing_rung": 2,
            "passes": py_float(crossing_grad) < 0.0,
        },
        "crossover_proofs": {
            "z3": {"ran": False, "load_bearing": False, "verdict": "not_scoped", "reason": "SMT proof is scoped to JAX and Julia legs"},
            "cvc5": {"ran": False, "load_bearing": False, "verdict": "not_scoped", "reason": "SMT proof is scoped to JAX leg"},
        },
        "shared_scalars": shared_scalars,
        "shared_observable_keys": sorted(shared_scalars),
        "all_pass": all_pass,
        "claim_ceiling": "scratch_diagnostic only; promotion_allowed=false; formal_admission_allowed=false; no bridge, Axis0, manifold, or M(C) closure.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_NESTED_HOPF_WEYL_SIGNED_CUT_RATCHET_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"S=[{result['shared_scalars']['conditional_entropy_r1']},"
        f"{result['shared_scalars']['conditional_entropy_r2']},"
        f"{result['shared_scalars']['conditional_entropy_r3']}] "
        f"gaps=[{result['shared_scalars']['order_gap_r1_r2']},"
        f"{result['shared_scalars']['order_gap_r2_r3']}] "
        f"grad={result['autograd']['gradient']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
