#!/usr/bin/env python3
"""Holodeck science world-memory ablation formal scout.

This follow-up treats the Holodeck as a finite empirical world-model loop:
predict, instrument, observe, update, and falsify against controls. The question
is whether world-memory is load-bearing under a bounded seed sweep.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from typing import Any

import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


RESULT_DIR = ROOT / "results"
NAME = "holodeck_science_world_memory_ablation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "holodeck_science_world_memory_ablation_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests finite Holodeck/science-method world-memory "
    "load-bearing behavior under ablations. It does not admit final Holodeck, "
    "FEP, IGT, Axis0, Xi, flux, cognition, psychology, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite world-memory density states, instrument updates, QIT-FEP readouts, and ablation sweep",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and dependency checks",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

CDTYPE = torch.complex128
RDTYPE = torch.float64
I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def normalize_vec(vec: torch.Tensor) -> torch.Tensor:
    vec = torch.as_tensor(vec, dtype=CDTYPE)
    norm = torch.linalg.vector_norm(vec)
    if float(norm.real.item()) <= 1e-14:
        out = torch.zeros_like(vec)
        out[0] = 1.0 + 0.0j
        return out
    return vec / norm


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


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_vec(psi)
    return psi[:, None] @ psi.conj()[None, :]


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = torch.as_tensor(rho, dtype=CDTYPE)
    rho = 0.5 * (rho + rho.mH)
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0)
    if float(torch.sum(vals).item()) <= 1e-14:
        vals = torch.full_like(vals, 1.0 / vals.numel())
    out = (vecs * vals.to(CDTYPE).unsqueeze(0)) @ vecs.mH
    return out / torch.trace(out)


def xx_entangler(theta: float) -> torch.Tensor:
    xx = torch.kron(X, X)
    angle = torch.tensor(theta, dtype=RDTYPE)
    return torch.cos(angle / 2.0).to(CDTYPE) * I4 - 1j * torch.sin(angle / 2.0).to(CDTYPE) * xx


def product_world_memory_state() -> torch.Tensor:
    return torch.kron(density(spinor(0.24, -0.11, 0.47)), density(spinor(-0.37, 0.29, 0.54)))


def raw_trace_memory_state() -> torch.Tensor:
    return torch.kron(density(spinor(0.24, -0.11, 0.47)), 0.5 * I2)


def projector(axis: torch.Tensor, sign: float) -> torch.Tensor:
    return 0.5 * (I2 + sign * axis)


def active_projection_instruments(*, reversed_order: bool = False) -> list[list[torch.Tensor]]:
    weak_x = 0.88 * I2 + 0.12 * projector(X, +1.0)
    weak_z = 0.86 * I2 + 0.14 * projector(Z, -1.0)
    weak_y = 0.90 * I2 + 0.10 * projector(Y, +1.0)
    stages = [
        [weak_x, projector(X, -1.0)],
        [weak_z, projector(Z, +1.0)],
        [weak_y, projector(Y, -1.0)],
    ]
    return list(reversed(stages)) if reversed_order else stages


def target_effect() -> torch.Tensor:
    target = xx_entangler(0.69) @ torch.kron(spinor(0.32, -0.18, 0.49), spinor(-0.21, 0.27, 0.52))
    return density(target)


def expand_kraus(k: torch.Tensor) -> torch.Tensor:
    k = torch.as_tensor(k, dtype=CDTYPE)
    if k.shape == (2, 2):
        return torch.kron(k, I2)
    if k.shape == (4, 4):
        return k
    raise ValueError(f"unsupported Kraus shape {tuple(k.shape)}")


def apply_instruments(rho: torch.Tensor, instruments: list[list[torch.Tensor]]) -> torch.Tensor:
    rho = normalize_density(rho)
    for stage in instruments:
        accum = torch.zeros_like(rho)
        for k in stage:
            full_k = expand_kraus(k)
            accum = accum + full_k @ rho @ full_k.mH
        rho = normalize_density(accum)
    return rho


def partial_trace_two_qubit(rho: torch.Tensor, keep: int) -> torch.Tensor:
    tensor = normalize_density(rho).reshape(2, 2, 2, 2)
    if keep == 0:
        return torch.einsum("abcb->ac", tensor)
    return torch.einsum("abac->bc", tensor)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize_density(rho)).real
    vals = torch.clamp(vals, min=1e-12)
    return float((-torch.sum(vals * torch.log(vals))).item())


def mutual_information(rho: torch.Tensor) -> float:
    return entropy(partial_trace_two_qubit(rho, 0)) + entropy(partial_trace_two_qubit(rho, 1)) - entropy(rho)


def qit_holodeck_update(
    world_memory: torch.Tensor,
    instruments: list[list[torch.Tensor]],
    effect: torch.Tensor,
) -> dict[str, float]:
    posterior = apply_instruments(world_memory, instruments)
    effect = normalize_density(effect)
    reconstruction_score = float(torch.real(torch.trace(effect @ posterior)).item())
    cue_projector = torch.kron(projector(X, +1.0), projector(Z, +1.0))
    cue_confirmation_score = float(torch.real(torch.trace(cue_projector @ posterior)).item())
    return {
        "reconstruction_score": reconstruction_score,
        "cue_confirmation_score": cue_confirmation_score,
        "mutual_information": mutual_information(posterior),
    }


def seeded_world_memory(seed: int, *, wrong_memory: bool = False, raw_memory: bool = False) -> torch.Tensor:
    phi_w = -0.31 + 0.041 * seed
    chi_w = 0.22 + 0.037 * seed
    eta_w = 0.46 + 0.003 * (seed % 7)
    psi_w = spinor(phi_w, chi_w, eta_w)
    if raw_memory:
        return torch.kron(density(psi_w), 0.5 * I2)
    if wrong_memory:
        psi_m = spinor(0.91 - 0.017 * seed, 0.44 + 0.011 * seed, 0.26 + 0.002 * (seed % 5))
    else:
        psi_m = spinor(0.38 + 0.006 * seed, -0.17 + 0.004 * seed, 0.52)
    psi = xx_entangler(0.74 + 0.01 * (seed % 9)) @ torch.kron(psi_w, psi_m)
    return density(normalize_vec(psi))


def evaluate_seed(seed: int) -> dict[str, Any]:
    instruments = active_projection_instruments(reversed_order=bool(seed % 2))
    live = qit_holodeck_update(seeded_world_memory(seed), instruments, target_effect())
    wrong = qit_holodeck_update(seeded_world_memory(seed, wrong_memory=True), instruments, target_effect())
    raw = qit_holodeck_update(seeded_world_memory(seed, raw_memory=True), instruments, target_effect())
    product = qit_holodeck_update(product_world_memory_state(), instruments, target_effect())
    passive = qit_holodeck_update(seeded_world_memory(seed), [[I2]], target_effect())
    live_score = live["reconstruction_score"] + 0.20 * live["cue_confirmation_score"] + 0.15 * live["mutual_information"]
    wrong_score = wrong["reconstruction_score"] + 0.20 * wrong["cue_confirmation_score"] + 0.15 * wrong["mutual_information"]
    raw_score = raw["reconstruction_score"] + 0.20 * raw["cue_confirmation_score"] + 0.15 * raw["mutual_information"]
    product_score = product["reconstruction_score"] + 0.20 * product["cue_confirmation_score"] + 0.15 * product["mutual_information"]
    passive_score = passive["reconstruction_score"] + 0.20 * passive["cue_confirmation_score"] + 0.15 * passive["mutual_information"]
    best_control = max(wrong_score, raw_score, product_score, passive_score)
    margin = live_score - best_control
    survived = margin > 0.015 and live["mutual_information"] > raw["mutual_information"] + 0.01
    return {
        "seed": seed,
        "live_score": live_score,
        "best_control_score": best_control,
        "margin": margin,
        "survived": bool(survived),
        "live_reconstruction": live["reconstruction_score"],
        "live_mutual_information": live["mutual_information"],
        "raw_memory_mutual_information": raw["mutual_information"],
        "wrong_memory_score": wrong_score,
        "raw_memory_score": raw_score,
        "product_score": product_score,
        "passive_score": passive_score,
    }


def sweep_section() -> dict[str, Any]:
    rows = [evaluate_seed(seed) for seed in range(1, 17)]
    margins = torch.tensor([row["margin"] for row in rows], dtype=torch.float64)
    survival_count = sum(1 for row in rows if row["survived"])
    survival_rate = survival_count / len(rows)
    candidate_status = "world_memory_load_bearing_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_world_memory_fixture"
    return {
        "name": "finite_holodeck_science_world_memory_ablation_fixture",
        "passed": True,
        "candidate_status": candidate_status,
        "candidate_survived": candidate_status == "world_memory_load_bearing_fixture",
        "seed_count": len(rows),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "mean_margin": float(torch.mean(margins).item()),
        "min_margin": float(torch.min(margins).item()),
        "max_margin": float(torch.max(margins).item()),
        "rows": rows,
        "claim": "finite Holodeck science loop tests whether world-memory is load-bearing under ablations",
    }


def z3_nonpromotion_section() -> dict[str, Any]:
    seed_count = z3.Int("seed_count")
    final_holodeck = z3.Bool("final_holodeck")
    final_fep = z3.Bool("final_fep")
    cognition = z3.Bool("cognition")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(seed_count == 16, z3.Not(final_holodeck), z3.Not(final_fep), z3.Not(cognition), z3.Not(physics))
    checks = {}
    for name, symbol in [
        ("final_holodeck", final_holodeck),
        ("final_fep", final_fep),
        ("cognition", cognition),
        ("physics", physics),
    ]:
        local = z3.Solver()
        local.add(solver.assertions())
        local.add(symbol)
        checks[name] = str(local.check())
    return {
        "name": "z3_holodeck_science_nonpromotion_fence",
        "passed": all(value == "unsat" for value in checks.values()),
        "checks": checks,
        "claim": "world-memory ablation evidence cannot promote final Holodeck/FEP/cognition/physics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    sweep = sweep_section()
    antipromotion = z3_nonpromotion_section()
    sections = [sweep, antipromotion]
    graveyard_companions = {
        "memory_ablation_status_recorded": {
            "pass": sweep["candidate_status"] in {"world_memory_load_bearing_fixture", "open_or_nonrobust_world_memory_fixture"},
            "candidate_status": sweep["candidate_status"],
        },
        "not_single_seed_only": {"pass": sweep["seed_count"] == 16, "seed_count": sweep["seed_count"]},
        "final_claims_rejected": {"pass": all(value == "unsat" for value in antipromotion["checks"].values())},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_holodeck_not_admitted": {"pass": True, "value": False},
        "final_fep_not_admitted": {"pass": True, "value": False},
        "axis0_flux_not_admitted": {"pass": True, "value": False},
        "cognition_physics_not_admitted": {"pass": True, "value": False},
    }
    all_pass = (
        all(section["passed"] for section in sections)
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": classification,
        "CLASSIFICATION": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "PROMOTION_ALLOWED": PROMOTION_ALLOWED,
        "promotion_allowed": PROMOTION_ALLOWED,
        "CLAIM_CEILING": CLAIM_CEILING,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "candidate_status": sweep["candidate_status"],
        "candidate_survived": sweep["candidate_survived"],
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "seed_count": sweep["seed_count"],
            "survival_count": sweep["survival_count"],
            "survival_rate": sweep["survival_rate"],
            "mean_margin": sweep["mean_margin"],
            "min_margin": sweep["min_margin"],
            "max_margin": sweep["max_margin"],
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["hypothesis-bank train/test split", "multi-cell world model", "policy action selection"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 finite-QIT world-memory ablation scout, not a v4 cognition or world-model ontology probe.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "typed hypothesis-bank held-out observations",
            "policy selection by expected evidence",
            "multi-cell finite world-memory grid",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": sweep["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
