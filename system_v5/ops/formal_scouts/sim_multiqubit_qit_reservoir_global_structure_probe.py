#!/usr/bin/env python3
"""Multi-qubit QIT reservoir global-structure classification scout."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import engine_v6_proper_multiqubit_reference as v6
from reservoir_torch_readout import classifier_accuracy as torch_classifier_accuracy


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_qit_reservoir_global_structure_probe_results.json"

NAME = "multiqubit_qit_reservoir_global_structure_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether a frozen multi-qubit QIT reservoir built "
    "from the v6 reference engine separates global correlation classes whose "
    "single-qubit marginals are intentionally uninformative. It does not prove "
    "learned dynamics and does not admit intelligence, neural capability, canonical "
    "manifold status, physics, cognition, or 64-site PEPS3D behavior."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing frozen multi-qubit engine feature extraction"},
    "sklearn": {"tried": False, "used": False, "reason": "not used; torch ridge readout replaces sklearn classifier plumbing"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite pass-predicate witness"},
    "engine_v6_reference": {"tried": True, "used": True, "reason": "supportive repo-grounded copy of the external v6 candidate"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'sklearn': None,
    'z3': 'load_bearing',
    'engine_v6_reference': 'supportive',
}

DTYPE = torch.complex64
REAL_DTYPE = torch.float32
CLASS_NAMES = ["ghz_coherent", "ghz_dephased", "bell_pair_product", "even_parity_mixture"]
N_PER_CLASS = {4: 28, 8: 20}
MIN_NONCLASSICAL_WIDTH = 8


def width_role(n_qubits: int) -> dict[str, Any]:
    if n_qubits < MIN_NONCLASSICAL_WIDTH:
        return {
            "minimum_width_qubits": n_qubits,
            "minimum_width_role": "calibration_only",
            "minimum_width_reason": "sub-8 row is retained only as a calibration/control boundary, not maturity evidence",
        }
    return {
        "minimum_width_qubits": n_qubits,
        "minimum_width_role": "maturity_gate",
        "minimum_width_reason": "row meets the current minimum nonclassical width floor",
    }


def _rand_angle(generator: torch.Generator) -> torch.Tensor:
    return torch.rand((), generator=generator, dtype=REAL_DTYPE) * (2 * math.pi)


def _complex_phase(angle: torch.Tensor) -> torch.Tensor:
    return torch.complex(torch.cos(angle), torch.sin(angle)).to(DTYPE)


def random_unitary_2(generator: torch.Generator) -> torch.Tensor:
    z = torch.complex(
        torch.randn((2, 2), generator=generator, dtype=REAL_DTYPE),
        torch.randn((2, 2), generator=generator, dtype=REAL_DTYPE),
    )
    q, r = torch.linalg.qr(z.to(DTYPE))
    diag = torch.diagonal(r)
    phase = diag / diag.abs().clamp_min(1e-12)
    return (q * phase).to(DTYPE)


def kron_all(mats: list[torch.Tensor]) -> torch.Tensor:
    out = mats[0]
    for mat in mats[1:]:
        out = torch.kron(out, mat)
    return out.to(DTYPE)


def ghz_density(n_qubits: int, phase: torch.Tensor) -> torch.Tensor:
    d = 2**n_qubits
    psi = torch.zeros(d, dtype=DTYPE)
    psi[0] = 1.0 / math.sqrt(2)
    psi[-1] = _complex_phase(phase) / math.sqrt(2)
    return torch.outer(psi, psi.conj()).to(DTYPE)


def ghz_dephased_density(n_qubits: int) -> torch.Tensor:
    d = 2**n_qubits
    rho = torch.zeros((d, d), dtype=DTYPE)
    rho[0, 0] = 0.5
    rho[-1, -1] = 0.5
    return rho


def bell_pair_product_density(n_qubits: int, generator: torch.Generator) -> torch.Tensor:
    assert n_qubits % 2 == 0
    pair = torch.zeros(4, dtype=DTYPE)
    phase = _complex_phase(_rand_angle(generator))
    pair[0] = 1.0 / math.sqrt(2)
    pair[3] = phase / math.sqrt(2)
    psi = pair
    for _ in range(n_qubits // 2 - 1):
        phase = _complex_phase(_rand_angle(generator))
        pair = torch.zeros(4, dtype=DTYPE)
        pair[0] = 1.0 / math.sqrt(2)
        pair[3] = phase / math.sqrt(2)
        psi = torch.kron(psi, pair)
    return torch.outer(psi, psi.conj()).to(DTYPE)


def even_parity_mixture_density(n_qubits: int) -> torch.Tensor:
    d = 2**n_qubits
    rho = torch.zeros((d, d), dtype=DTYPE)
    states = [idx for idx in range(d) if bin(idx).count("1") % 2 == 0]
    for idx in states:
        rho[idx, idx] = 1.0 / len(states)
    return rho


def base_density(label: int, n_qubits: int, generator: torch.Generator) -> torch.Tensor:
    if label == 0:
        return ghz_density(n_qubits, _rand_angle(generator))
    if label == 1:
        return ghz_dephased_density(n_qubits)
    if label == 2:
        return bell_pair_product_density(n_qubits, generator)
    if label == 3:
        return even_parity_mixture_density(n_qubits)
    raise ValueError(label)


def sample_density(label: int, n_qubits: int, generator: torch.Generator) -> torch.Tensor:
    rho = base_density(label, n_qubits, generator)
    local_u = kron_all([random_unitary_2(generator) for _ in range(n_qubits)])
    rho = local_u @ rho @ local_u.conj().T
    rho = (rho + rho.conj().T) / 2
    rho = rho / torch.trace(rho).real
    return rho.to(DTYPE)


def partial_trace_torch(rho: torch.Tensor, n_qubits: int, keep: list[int]) -> torch.Tensor:
    keep = sorted(keep)
    trace_out = [idx for idx in range(n_qubits) if idx not in keep]
    reshaped = rho.reshape([2] * (2 * n_qubits))
    for q in sorted(trace_out, reverse=True):
        n_now = reshaped.ndim // 2
        reshaped = reshaped.diagonal(dim1=q, dim2=n_now + q).sum(dim=-1)
    d = 2 ** len(keep)
    return reshaped.reshape(d, d)


def entropy_torch(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = vals.clamp_min(1e-9)
    vals = vals / vals.sum()
    return float(-(vals * vals.log()).sum().item())


def local_bloch_features(rhos: torch.Tensor, n_qubits: int) -> torch.Tensor:
    x = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    y = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    rows = []
    for rho in rhos:
        feat = []
        for q in range(n_qubits):
            red = partial_trace_torch(rho, n_qubits, [q])
            feat.extend([torch.trace(x @ red).real, torch.trace(y @ red).real, torch.trace(z @ red).real])
        rows.append(feat)
    return torch.tensor(rows, dtype=REAL_DTYPE)


def structural_static_features(rhos: torch.Tensor, n_qubits: int) -> torch.Tensor:
    rows = []
    half = list(range(n_qubits // 2))
    other = list(range(n_qubits // 2, n_qubits))
    for rho in rhos:
        rho_a = partial_trace_torch(rho, n_qubits, half)
        rho_b = partial_trace_torch(rho, n_qubits, other)
        s_ab = entropy_torch(rho)
        mi = entropy_torch(rho_a) + entropy_torch(rho_b) - s_ab
        purity = float(torch.trace(rho @ rho).real.item())
        spectrum = torch.sort(torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real).values[-8:]
        rows.append([s_ab, mi, purity, *spectrum.tolist()])
    return torch.tensor(rows, dtype=REAL_DTYPE)


def full_static_projection_features(rhos: torch.Tensor, seed: int, dim: int = 512) -> torch.Tensor:
    flat = torch.cat([rhos.real.reshape(len(rhos), -1), rhos.imag.reshape(len(rhos), -1)], dim=1)
    generator = torch.Generator().manual_seed(seed)
    proj = torch.randn((flat.shape[1], dim), generator=generator, dtype=REAL_DTYPE) * (1.0 / math.sqrt(dim))
    return flat @ proj


def reservoir_features(rhos: torch.Tensor, n_qubits: int) -> torch.Tensor:
    torch.manual_seed(1234 + n_qubits)
    engine = v6.TrainablePairedEngineV6(n_classes=len(CLASS_NAMES), n_qubits=n_qubits, hidden_dim=64)
    engine.eval()
    with torch.no_grad():
        rho_t = rhos.to(dtype=v6.DTYPE)
        feats_l = engine.engine_L(rho_t)
        feats_r = engine.engine_R(rho_t)
        feats = torch.cat([feats_l, feats_r], dim=-1).detach().cpu()
    return feats.to(dtype=REAL_DTYPE)


def _label_tensor(value: Any) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().to(dtype=torch.long).clone()
    return torch.tensor(value, dtype=torch.long)


def classifier_accuracy(x: Any, y: Any, seed: int, shuffle_labels: bool = False) -> float:
    return torch_classifier_accuracy(
        x,
        _label_tensor(y),
        seed=seed,
        shuffle_labels=shuffle_labels,
        test_size=0.35,
        ridge=1e-3,
    )


def run_for_n(n_qubits: int) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(120000 + n_qubits)
    rhos = []
    labels = []
    for label in range(len(CLASS_NAMES)):
        for _ in range(N_PER_CLASS[n_qubits]):
            rhos.append(sample_density(label, n_qubits, generator))
            labels.append(label)
    rhos_arr = torch.stack(rhos)
    y = torch.tensor(labels, dtype=torch.long)
    local = local_bloch_features(rhos_arr, n_qubits)
    static = structural_static_features(rhos_arr, n_qubits)
    projected = full_static_projection_features(rhos_arr, seed=130000 + n_qubits)
    reservoir = reservoir_features(rhos_arr, n_qubits)
    metrics = {
        "local_only_accuracy": classifier_accuracy(local, y, seed=1 + n_qubits),
        "structural_static_accuracy": classifier_accuracy(static, y, seed=2 + n_qubits),
        "full_static_random_projection_accuracy": classifier_accuracy(projected, y, seed=3 + n_qubits),
        "frozen_reservoir_accuracy": classifier_accuracy(reservoir, y, seed=4 + n_qubits),
        "frozen_reservoir_shuffled_label_accuracy": classifier_accuracy(reservoir, y, seed=5 + n_qubits, shuffle_labels=True),
    }
    local_norm = float(local.abs().max().item())
    return {
        **width_role(n_qubits),
        "n_qubits": n_qubits,
        "samples": int(len(y)),
        "chance": 1.0 / len(CLASS_NAMES),
        "feature_dims": {
            "local_only": int(local.shape[1]),
            "structural_static": int(static.shape[1]),
            "full_static_random_projection": int(projected.shape[1]),
            "frozen_reservoir": int(reservoir.shape[1]),
        },
        "max_abs_local_bloch_feature": local_norm,
        "metrics": metrics,
        "pass": local_norm < 1e-4
        and metrics["frozen_reservoir_accuracy"] >= 0.70
        and metrics["frozen_reservoir_accuracy"] > metrics["local_only_accuracy"] + 0.25
        and metrics["frozen_reservoir_shuffled_label_accuracy"] <= 0.45,
    }


def z3_scaling_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row8 = next(row for row in rows if row["n_qubits"] == 8)
    solver = z3.Solver()
    n8 = z3.Int("n8")
    res8 = z3.Real("res8")
    local8 = z3.Real("local8")
    shuffled8 = z3.Real("shuffled8")
    solver.add(n8 == 8)
    solver.add(res8 == str(round(row8["metrics"]["frozen_reservoir_accuracy"], 6)))
    solver.add(local8 == str(round(row8["metrics"]["local_only_accuracy"], 6)))
    solver.add(shuffled8 == str(round(row8["metrics"]["frozen_reservoir_shuffled_label_accuracy"], 6)))
    solver.add(z3.Not(z3.And(n8 >= 8, res8 > local8, shuffled8 < res8)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite N=8 reservoir/local/shuffle ordering.",
    }


def main() -> int:
    started = time.time()
    rows = [run_for_n(4), run_for_n(8)]
    row8 = next(row for row in rows if row["n_qubits"] == 8)
    positive = {
        "frozen_multiqubit_reservoir_separates_global_structure_at_8q": {
            "rows": rows,
            "minimum_width_qubits": MIN_NONCLASSICAL_WIDTH,
            "minimum_width_role": "maturity_gate",
            "minimum_width_reason": "only the 8q row is used for the positive pass predicate; the 4q row is calibration-only",
            "pass": row8["pass"],
        },
        "z3_rejects_local_or_shuffle_only_explanation_at_8q": z3_scaling_witness(rows),
    }
    graveyards = {
        "local_single_qubit_marginals_are_uninformative": {
            "max_abs_local_bloch_by_n": {str(row["n_qubits"]): row["max_abs_local_bloch_feature"] for row in rows},
            "pass": all(row["max_abs_local_bloch_feature"] < 1e-4 for row in rows),
        },
        "shuffled_labels_do_not_count_as_work": {
            "shuffled_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["frozen_reservoir_shuffled_label_accuracy"] for row in rows},
            "pass": row8["metrics"]["frozen_reservoir_shuffled_label_accuracy"] <= 0.45,
        },
        "full_static_baseline_is_reported_not_hidden": {
            "full_static_random_projection_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["full_static_random_projection_accuracy"] for row in rows},
            "pass": all("full_static_random_projection_accuracy" in row["metrics"] for row in rows),
        },
    }
    boundary = {
        "eight_qubit_is_the_evidence_floor": {"min_evidence_qubits": 8, "pass": row8["n_qubits"] == 8},
        "four_qubit_row_is_calibration_only": {
            "pass": all(
                row.get("minimum_width_role") == "calibration_only"
                for row in rows
                if row["n_qubits"] < MIN_NONCLASSICAL_WIDTH
            ),
            "subminimum_rows": [
                {
                    "n_qubits": row["n_qubits"],
                    "minimum_width_role": row.get("minimum_width_role"),
                    "minimum_width_reason": row.get("minimum_width_reason"),
                }
                for row in rows
                if row["n_qubits"] < MIN_NONCLASSICAL_WIDTH
            ],
        },
        "structural_static_baseline_does_not_dominate_reservoir": {
            "pass": row8["metrics"]["structural_static_accuracy"] < row8["metrics"]["frozen_reservoir_accuracy"],
            "structural_static_accuracy": row8["metrics"]["structural_static_accuracy"],
            "frozen_reservoir_accuracy": row8["metrics"]["frozen_reservoir_accuracy"],
            "reason": (
                "A static global-feature baseline solving the task blocks any claim "
                "that the frozen reservoir is the load-bearing source of global-structure separation."
            ),
        },
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    checks = {**positive, **graveyards, **boundary}
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_qit_reservoir_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Frozen-reservoir readout scout only.",
            "Does not prove learned engine dynamics.",
            "Includes full-static baseline as overclaim guard.",
        ],
        "blockers": [key for key, row in checks.items() if row.get("pass") is not True],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
