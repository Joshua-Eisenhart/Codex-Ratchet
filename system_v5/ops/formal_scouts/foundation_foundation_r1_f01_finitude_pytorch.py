#!/usr/bin/env python3
"""PyTorch torch.func finite-support sensitivity leg for F01."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import torch
from torch.func import jacrev


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "foundation_foundation_r1_f01_finitude_pytorch_results.json"
)

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DTYPE = torch.float64
TOL = 1.0e-10

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "constructs concrete active and padded density matrices and computes torch.linalg.eigvalsh ranks",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "jacrev probes finite-support/probe sensitivity for the active carrier parameterization",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "writes the engine receipt",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "binds source and result paths",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch.func": "load_bearing",
    "json": "supportive",
    "pathlib": "supportive",
}


def finite_probe_family(dim: int) -> tuple[list[str], torch.Tensor]:
    eye = torch.eye(dim, dtype=DTYPE)
    projectors = [torch.outer(eye[i], eye[i]) for i in range(dim)]
    x01 = torch.zeros((dim, dim), dtype=DTYPE)
    x01[0, 1] = 0.5
    x01[1, 0] = 0.5
    return ["P0", "P1", "P2", "X01_half"], torch.stack([*projectors, x01])


def rank_from_spectrum(matrix: torch.Tensor) -> tuple[int, list[float]]:
    eigs = torch.linalg.eigvalsh(matrix)
    return int(torch.sum(eigs > TOL).item()), [float(x) for x in eigs.tolist()]


def density_from_theta(theta: torch.Tensor) -> torch.Tensor:
    weights = torch.softmax(theta[:3], dim=0)
    coherence_scale = 0.05 * torch.tanh(theta[3])
    coherence = coherence_scale * torch.sqrt(weights[0] * weights[1])
    rho = torch.diag(weights)
    rho = rho.clone()
    rho[0, 1] = coherence
    rho[1, 0] = coherence
    return rho


def probe_readout(theta: torch.Tensor) -> torch.Tensor:
    rho = density_from_theta(theta)
    _, probes = finite_probe_family(3)
    return torch.einsum("pij,ji->p", probes, rho)


def class_count(rows: list[list[float]]) -> int:
    return len({tuple(round(x, 12) for x in row) for row in rows})


def main() -> int:
    rho_a = torch.tensor(
        [[0.5, 0.0, 0.0], [0.0, 0.3, 0.0], [0.0, 0.0, 0.2]], dtype=DTYPE
    )
    rho_b = torch.tensor(
        [[0.5, 0.05, 0.0], [0.05, 0.3, 0.0], [0.0, 0.0, 0.2]], dtype=DTYPE
    )
    rho_c = torch.tensor(
        [[0.5, 0.0, 0.0], [0.0, 0.2, 0.0], [0.0, 0.0, 0.3]], dtype=DTYPE
    )
    admitted = [rho_a, rho_b, rho_c]
    admitted_names = ["rho_a_diag_503020", "rho_b_coherent_503020_x01_005", "rho_c_diag_502030"]
    rho_over = torch.eye(4, dtype=DTYPE) / 4.0

    dim = int(rho_a.shape[0])
    padded_dim = int(rho_over.shape[0])
    probe_names, probes = finite_probe_family(dim)
    identity_residual = float(torch.max(torch.abs(torch.sum(probes[:3], dim=0) - torch.eye(dim, dtype=DTYPE))).item())
    probe_vectors = torch.stack([torch.einsum("pij,ji->p", probes, rho) for rho in admitted])
    vectors = [[float(x) for x in row] for row in probe_vectors.tolist()]
    dropped_vectors = [row[:3] for row in vectors]
    full_class_count = class_count(vectors)
    dropped_class_count = class_count(dropped_vectors)
    ranks_and_eigs = [rank_from_spectrum(rho) for rho in admitted]
    ranks = [item[0] for item in ranks_and_eigs]
    eigs = [item[1] for item in ranks_and_eigs]
    admitted_rank, admitted_eigs = ranks_and_eigs[0]
    over_rank, over_eigs = rank_from_spectrum(rho_over)
    traces = [float(torch.trace(rho).item()) for rho in admitted]
    hermitian_residuals = [float(torch.max(torch.abs(rho - rho.T.conj())).item()) for rho in admitted]
    min_eigs = [min(row) for row in eigs]

    theta = torch.tensor([0.2, -0.3, -0.7, 1.1], dtype=DTYPE)
    probe_vector_at_theta = probe_readout(theta)
    jacobian = jacrev(probe_readout)(theta)
    singular_values = torch.linalg.svdvals(jacobian)
    sum_gradient = jacrev(lambda x: torch.sum(probe_readout(x)[:3]))(theta)
    density_jacobian = jacrev(lambda x: torch.linalg.eigvalsh(density_from_theta(x)))(theta)
    finite_bounds_hold = bool(
        torch.all(probe_vector_at_theta[:3] >= -TOL)
        and torch.all(probe_vector_at_theta[:3] <= 1.0 + TOL)
        and abs(float(torch.sum(probe_vector_at_theta[:3]).item()) - 1.0) <= TOL
        and torch.all(torch.isfinite(jacobian))
        and torch.all(torch.isfinite(density_jacobian))
    )
    jacobian_rank = int(torch.sum(singular_values > TOL).item())
    all_pass = (
        identity_residual <= TOL
        and all(abs(trace - 1.0) <= TOL for trace in traces)
        and all(floor >= -TOL for floor in min_eigs)
        and all(residual <= TOL for residual in hermitian_residuals)
        and all(rank <= dim for rank in ranks)
        and admitted_rank == dim
        and over_rank == dim + 1
        and padded_dim == dim + 1
        and dropped_class_count < full_class_count
        and finite_bounds_hold
        and jacobian_rank == dim
        and float(torch.max(torch.abs(sum_gradient)).item()) <= TOL
    )

    payload = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": "foundation_r1_f01_finitude",
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "dtype": str(DTYPE),
        "packages_used": ["torch", "torch.func", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "M": {
            "description": "finite PyTorch probe family on a d=3 carrier",
            "probe_names": probe_names,
            "probe_count": int(probes.shape[0]),
            "carrier_dimension": dim,
            "identity_residual_projectors_only": identity_residual,
            "identity_residual": identity_residual,
            "resolves_identity": identity_residual <= TOL,
            "probe_vectors": vectors,
            "computed_dimension_source": "rho_a.shape[0]",
        },
        "C": {
            "trace_equals_one": all(abs(trace - 1.0) <= TOL for trace in traces),
            "psd": all(floor >= -TOL for floor in min_eigs),
            "hermitian": all(residual <= TOL for residual in hermitian_residuals),
            "normalization": identity_residual <= TOL,
            "rung_specific_constraint": "F01 finite support appears as computed spectral rank r <= reference carrier dimension d",
            "f01_support_bound": "r <= d",
            "computed_admitted_ranks": ranks,
            "computed_rank_source": "torch.linalg.eigvalsh(matrix), count(eigenvalue > tol)",
            "active_finite_carrier_support_embedding": True,
        },
        "quotient": {
            "relation": "rho ~_M sigma iff all finite probe expectations in M match",
            "candidate_family": admitted_names,
            "admitted_cardinality": len(admitted),
            "class_count": full_class_count,
            "classes": {
                f"class_{idx + 1}": {
                    "representative": admitted_names[idx],
                    "probe_vector": row,
                    "members": [admitted_names[idx]],
                }
                for idx, row in enumerate(vectors)
            },
            "drop_probe": "X01_half",
            "drop_probe_class_count": dropped_class_count,
        },
        "computed_candidates": {
            "admitted_reference": {
                "name": admitted_names[0],
                "carrier_dimension": dim,
                "computed_rank": admitted_rank,
                "eigenvalues": admitted_eigs,
                "f01_admitted": admitted_rank <= dim,
            },
            "excluded_over_support": {
                "name": "rho_over_padded_maximally_mixed_rank_4",
                "candidate_carrier_dimension": padded_dim,
                "reference_f01_dimension": dim,
                "computed_rank": over_rank,
                "eigenvalues": over_eigs,
                "f01_admitted": over_rank <= dim,
            },
        },
        "torch_func_check": {
            "ran": True,
            "load_bearing": True,
            "genuine_independent_check": True,
            "description": "jacrev checks sensitivity of finite probe readouts and density eigenvalues to a constrained parameterization; it is not an SMT mirror",
            "theta": theta.tolist(),
            "probe_vector": probe_vector_at_theta.tolist(),
            "jacobian": jacobian.tolist(),
            "singular_values": singular_values.tolist(),
            "jacobian_rank": jacobian_rank,
            "sum_gradient": sum_gradient.tolist(),
            "density_eigval_jacobian": density_jacobian.tolist(),
            "finite_bounds_hold": finite_bounds_hold,
        },
        "negative_control": {
            "erase": "drop X01_half probe",
            "flipped": dropped_class_count < full_class_count,
            "computed_rank_values": {"d": dim, "over_support_r": over_rank},
            "drop_probe_control": {
                "drop_probe": "X01_half",
                "full_probe_class_count": full_class_count,
                "drop_probe_class_count": dropped_class_count,
                "coarsened": dropped_class_count < full_class_count,
            },
            "note": "The SAT/UNSAT F01 erase flip is load-bearing in the JAX and envelope crossover proof; PyTorch supplies independent differentiable sensitivity plus spectral ranks.",
        },
        "summary": {
            "all_pass": all_pass,
            "finite_cardinality": dim,
            "computed_dim": dim,
            "computed_rank_admit": admitted_rank,
            "computed_rank_over": over_rank,
            "computed_padded_dim": padded_dim,
            "all_admitted_have_finite_support": all(rank <= dim for rank in ranks),
            "claim_ceiling": "F01 finite differentiable support check at micro scale; no promotion, no later-rung claim",
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "PYTORCH_F01_DONE "
        f"all_pass={str(all_pass).lower()} d={dim} admitted_r={admitted_rank} over_r={over_rank} "
        f"jacobian_rank={jacobian_rank}"
    )
    print(f"wrote: {RESULT_PATH}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
