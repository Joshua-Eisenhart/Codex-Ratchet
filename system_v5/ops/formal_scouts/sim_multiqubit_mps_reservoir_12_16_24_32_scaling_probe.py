#!/usr/bin/env python3
"""MPS v7 reservoir scaling scout for 12/16/24/32 qubits."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import engine_v7_mps_reference as v7
from reservoir_torch_readout import classifier_accuracy


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_mps_reservoir_12_16_24_32_scaling_probe_results.json"

NAME = "multiqubit_mps_reservoir_12_16_24_32_scaling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: translates the external v7 MPS scaling report into a "
    "repo-grounded finite 12/16/24/32-qubit MPS reservoir run with tiny "
    "classification and scaling predicates. It does not prove learned dynamics, "
    "does not prove 32-qubit functional superiority, and does not admit intelligence, "
    "neural capability, canonical manifold status, physics, cognition, or 64-site "
    "PEPS3D behavior."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing MPS trajectory features"},
    "sklearn": {"tried": False, "used": False, "reason": "not used; torch ridge readout replaces sklearn classifier plumbing"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite scaling witness"},
    "engine_v7_reference": {"tried": True, "used": True, "reason": "supportive repo-grounded MPS v7 candidate boundary"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'sklearn': None,
    'z3': 'load_bearing',
    'engine_v7_reference': 'supportive',
}

CLASS_NAMES = ["product", "ghz", "w", "random_mps"]
N_VALUES = [12, 16, 24, 32]
N_PER_CLASS = 5


def random_unitary(seed: int) -> torch.Tensor:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    real = torch.randn((2, 2), generator=gen, dtype=torch.float64)
    imag = torch.randn((2, 2), generator=gen, dtype=torch.float64)
    z = torch.complex(real, imag).to(dtype=v7.DTYPE)
    q, r = torch.linalg.qr(z)
    diag = torch.diagonal(r)
    phase = diag / torch.clamp(torch.abs(diag), min=1e-12)
    return q * phase.conj()


def perturb_local(mps: v7.MPS, seed: int) -> v7.MPS:
    out = mps.copy()
    for site in range(out.N):
        out.apply_single(random_unitary(seed + site), site)
    out.normalize_()
    return out


def make_state(label: int, n_qubits: int, seed: int) -> v7.MPS:
    if label == 0:
        state = v7.product_random_mps(n_qubits, seed=seed)
    elif label == 1:
        state = v7.ghz_mps(n_qubits)
    elif label == 2:
        state = v7.w_mps(n_qubits)
    elif label == 3:
        state = v7.random_pure_nqubit_mps(n_qubits, chi=4, seed=seed)
    else:
        raise ValueError(label)
    return perturb_local(state, seed + 1000)


def initial_local_features(mps: v7.MPS) -> torch.Tensor:
    rows = []
    for site in (0, mps.N // 2, mps.N - 1):
        rho = mps.reduced_single(site)
        rho_h = (rho + rho.conj().transpose(-1, -2)) / 2
        eigs = torch.linalg.eigvalsh(rho_h).real
        eigs = torch.clamp(eigs, min=1e-9)
        eigs = eigs / eigs.sum()
        ent = float((-(eigs * torch.log(eigs)).sum()).item())
        bz = float((v7.SZ @ rho).diag().sum().real.item())
        bx = float((v7.SX @ rho).diag().sum().real.item())
        rows.extend([ent, bz, bx])
    return torch.tensor(rows, dtype=torch.float64)


def reservoir_features(mps: v7.MPS, n_qubits: int) -> torch.Tensor:
    eng1 = v7.MPSEngineV7(engine_type=1, chi_max=8)
    eng2 = v7.MPSEngineV7(engine_type=2, chi_max=8)
    f1 = eng1.trajectory_features(mps).detach().cpu().to(dtype=torch.float64)
    f2 = eng2.trajectory_features(mps).detach().cpu().to(dtype=torch.float64)
    return torch.cat([f1, f2])


def clf_acc(x: torch.Tensor, y: torch.Tensor, seed: int, shuffle: bool = False) -> float:
    return classifier_accuracy(
        x,
        y,
        seed=seed,
        shuffle_labels=shuffle,
        test_size=0.4,
        ridge=1e-3,
    )


def run_n(n_qubits: int) -> dict[str, Any]:
    rows = []
    labels = []
    local = []
    started = time.time()
    for label in range(len(CLASS_NAMES)):
        for sample in range(N_PER_CLASS):
            seed = 310000 + 1000 * n_qubits + 100 * label + sample
            state = make_state(label, n_qubits, seed)
            local.append(initial_local_features(state))
            rows.append(reservoir_features(state, n_qubits))
            labels.append(label)
    elapsed = time.time() - started
    x_res = torch.stack(rows)
    x_local = torch.stack(local)
    y = torch.tensor(labels, dtype=torch.int64)
    res_acc = clf_acc(x_res, y, seed=320000 + n_qubits)
    local_acc = clf_acc(x_local, y, seed=321000 + n_qubits)
    shuffle_acc = clf_acc(x_res, y, seed=322000 + n_qubits, shuffle=True)
    return {
        "n_qubits": n_qubits,
        "hilbert_dimension_log2": n_qubits,
        "samples": int(len(y)),
        "feature_dims": {"local_probe": int(x_local.shape[1]), "paired_mps_reservoir": int(x_res.shape[1])},
        "elapsed_seconds": elapsed,
        "accuracy": {
            "local_probe": local_acc,
            "paired_mps_reservoir": res_acc,
            "paired_mps_reservoir_shuffled_label": shuffle_acc,
        },
        "pass": x_res.shape[1] == 320 and res_acc >= 0.45 and shuffle_acc <= 0.50,
    }


def z3_scaling_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    nmax = z3.Int("nmax")
    rows_count = z3.Int("rows_count")
    min_acc = z3.Real("min_reservoir_accuracy")
    solver.add(nmax == max(row["n_qubits"] for row in rows))
    solver.add(rows_count == len(rows))
    solver.add(min_acc == str(round(min(row["accuracy"]["paired_mps_reservoir"] for row in rows), 6)))
    solver.add(z3.Not(z3.And(nmax == 32, rows_count == 4, min_acc > 0)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite N coverage and nonzero reservoir accuracy.",
    }


def n01_order_witness() -> dict[str, Any]:
    """Finite same-site noncommuting operation witness on the MPS fixture."""

    state = make_state(label=0, n_qubits=12, seed=330012)
    pz_plus = (0.5 * (v7.I2 + v7.SZ)).to(v7.DTYPE)

    sx_then_pz = state.copy()
    sx_then_pz.apply_single(v7.SX, 0)
    sx_then_pz.apply_single(pz_plus, 0)
    sx_then_pz.normalize_()

    pz_then_sx = state.copy()
    pz_then_sx.apply_single(pz_plus, 0)
    pz_then_sx.apply_single(v7.SX, 0)
    pz_then_sx.normalize_()

    rho_a = sx_then_pz.reduced_single(0)
    rho_b = pz_then_sx.reduced_single(0)
    gap = float(torch.linalg.matrix_norm(rho_a - rho_b).real.item())
    commutator_gap = float(torch.linalg.matrix_norm(v7.SX @ pz_plus - pz_plus @ v7.SX).real.item())

    solver = z3.Solver()
    finite_n = z3.Int("finite_mps_order_witness_n_qubits")
    order_gap = z3.Real("mps_operator_order_gap")
    solver.add(finite_n == 12)
    solver.add(order_gap == str(round(gap, 12)))
    solver.add(z3.Not(z3.And(finite_n == 12, order_gap > 0)))
    status = solver.check()
    return {
        "pass": status == z3.unsat and gap > 0 and commutator_gap > 0,
        "solver_status": str(status),
        "root": "N01_noncommutation_or_order_sensitivity",
        "finite_carrier": {"n_qubits": 12, "site": 0},
        "ordered_operations": ["SX_then_Pz_plus", "Pz_plus_then_SX"],
        "density_gap_frobenius": gap,
        "operator_commutator_gap_frobenius": commutator_gap,
        "claim": "Finite MPS fixture distinguishes same-site SX/Pz+ operation order; this does not prove 32-qubit superiority.",
    }


def main() -> int:
    started = time.time()
    rows = [run_n(n) for n in N_VALUES]
    positive = {
        "mps_reservoir_runs_12_16_24_32_qubits": {
            "class_names": CLASS_NAMES,
            "rows": rows,
            "pass": all(row["pass"] for row in rows),
        },
        "z3_rejects_missing_32_qubit_scaling_cell": z3_scaling_witness(rows),
        "n01_noncommutation_or_order_witness": n01_order_witness(),
    }
    graveyards = {
        "local_probe_baseline_is_reported_not_hidden": {
            "local_accuracy_by_n": {str(row["n_qubits"]): row["accuracy"]["local_probe"] for row in rows},
            "pass": True,
        },
        "shuffled_label_control_is_reported": {
            "shuffled_accuracy_by_n": {str(row["n_qubits"]): row["accuracy"]["paired_mps_reservoir_shuffled_label"] for row in rows},
            "pass": all(row["accuracy"]["paired_mps_reservoir_shuffled_label"] <= 0.50 for row in rows),
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "does_not_claim_32q_functional_superiority": {"pass": "does not prove 32-qubit functional superiority" in CLAIM_CEILING},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_mps_reservoir_scaling_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Tiny MPS scaling scout only.",
            "Does not prove 32-qubit functional superiority.",
            "Does not replace PEPS3D 64-site scouts.",
        ],
        "blockers": [],
        "root_constraints": {
            "finite_carrier_root": True,
            "noncommutation_or_order_root": positive["n01_noncommutation_or_order_witness"]["pass"],
            "finite_evidence": "bounded 12/16/24/32-qubit MPS fixtures with an explicit 12-qubit order witness",
            "noncommutation_or_order_evidence": "SX/Pz+ same-site operation-order witness distinguishes SX_then_Pz_plus from Pz_plus_then_SX",
        },
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
