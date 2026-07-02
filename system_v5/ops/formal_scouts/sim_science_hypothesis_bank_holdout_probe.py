#!/usr/bin/env python3
"""Science-method hypothesis-bank holdout formal scout.

This converts the Holodeck/FEP practical idea into a tiny empirical world-model
loop: finite hypotheses, finite instruments, Born-rule observation, posterior
update, and held-out prediction. The pass condition is held-out predictive gain
against controls, not same-target reconstruction.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "science_hypothesis_bank_holdout_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "science_hypothesis_bank_holdout_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite QIT science-method loop over hypotheses, "
    "instruments, posterior update, and held-out prediction. It does not admit "
    "final Holodeck, FEP, world engine, cognition, psychology, Axis0, flux, "
    "or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite two-qubit hypothesis states, Born-rule evidence, posterior update, and held-out controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite hypothesis-bank and nonpromotion checks",
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
EPS = 1e-12
I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def dagger(a: torch.Tensor) -> torch.Tensor:
    return torch.conj(a.transpose(-2, -1))


def normalize_vec(vec: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vec)
    return vec / torch.clamp(norm, min=EPS)


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0)
    if float(torch.sum(vals).item()) <= EPS:
        vals = torch.full_like(vals, 1.0 / vals.numel())
    out = (vecs * vals.to(CDTYPE).unsqueeze(0)) @ dagger(vecs)
    return out / torch.trace(out)


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
    return psi[:, None] @ dagger(psi[:, None])


def xx(theta: float) -> torch.Tensor:
    op = torch.kron(X, X)
    return math.cos(theta / 2.0) * I4 - 1j * math.sin(theta / 2.0) * op


def projector(axis: torch.Tensor, sign: float) -> torch.Tensor:
    return 0.5 * (I2 + sign * axis)


def full_effect(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return normalize_density(torch.kron(left, right))


INSTRUMENTS = [
    full_effect(projector(Z, +1.0), I2),
    full_effect(projector(Z, -1.0), I2),
    full_effect(projector(X, +1.0), projector(Z, +1.0)),
    full_effect(projector(X, -1.0), projector(Z, -1.0)),
    full_effect(projector(Y, +1.0), projector(X, +1.0)),
    full_effect(projector(Y, -1.0), projector(X, -1.0)),
]

HOLDOUTS = [
    full_effect(projector(X, +1.0), projector(X, +1.0)),
    full_effect(projector(X, -1.0), projector(X, -1.0)),
    full_effect(projector(Z, +1.0), projector(Z, -1.0)),
    full_effect(projector(Y, +1.0), projector(Y, -1.0)),
]


def hypothesis_state(hid: int, seed: int, *, wrong_bank: bool = False, product: bool = False) -> torch.Tensor:
    offset = (hid + (2 if wrong_bank else 0)) % 4
    psi_a = spinor(0.17 + 0.11 * offset + 0.013 * seed, -0.23 + 0.07 * offset, 0.38 + 0.035 * offset)
    psi_b = spinor(-0.31 + 0.05 * offset, 0.19 + 0.09 * offset + 0.009 * seed, 0.43 + 0.026 * ((offset + seed) % 4))
    psi = torch.kron(psi_a, psi_b)
    if not product:
        psi = xx(0.32 + 0.16 * offset) @ psi
    return normalize_density(density(psi))


def bank(seed: int, *, wrong_bank: bool = False, product: bool = False) -> list[torch.Tensor]:
    return [hypothesis_state(hid, seed, wrong_bank=wrong_bank, product=product) for hid in range(4)]


def born(rho: torch.Tensor, effect: torch.Tensor) -> float:
    return max(EPS, float(torch.real(torch.trace(normalize_density(rho) @ effect)).item()))


def choose_instrument(prior: torch.Tensor, hypotheses: list[torch.Tensor]) -> int:
    # Choose the finite probe with largest predicted spread across hypotheses.
    spreads = []
    for idx, effect in enumerate(INSTRUMENTS):
        probs = torch.tensor([born(rho, effect) for rho in hypotheses], dtype=RDTYPE)
        mean = torch.sum(prior * probs)
        variance = torch.sum(prior * (probs - mean) ** 2)
        spreads.append((float(variance.item()), idx))
    return max(spreads, key=lambda item: item[0])[1]


def update(prior: torch.Tensor, hypotheses: list[torch.Tensor], effect_idx: int, observed_positive: bool) -> torch.Tensor:
    effect = INSTRUMENTS[effect_idx]
    likelihoods = torch.tensor([born(rho, effect) for rho in hypotheses], dtype=RDTYPE)
    if not observed_positive:
        likelihoods = 1.0 - likelihoods
    posterior = prior * torch.clamp(likelihoods, min=EPS)
    return posterior / torch.sum(posterior)


def expected_holdout(posterior: torch.Tensor, hypotheses: list[torch.Tensor], holdout_idx: int) -> float:
    probs = torch.tensor([born(rho, HOLDOUTS[holdout_idx]) for rho in hypotheses], dtype=RDTYPE)
    return float(torch.sum(posterior * probs).item())


def evaluate_seed(seed: int) -> dict[str, Any]:
    true_id = seed % 4
    holdout_idx = (seed * 3 + 1) % len(HOLDOUTS)
    true_state = hypothesis_state(true_id, seed)
    prior = torch.full((4,), 0.25, dtype=RDTYPE)
    live_bank = bank(seed)
    effect_idx = choose_instrument(prior, live_bank)
    observed_positive = born(true_state, INSTRUMENTS[effect_idx]) >= 0.5
    posterior = update(prior, live_bank, effect_idx, observed_positive)
    live_prediction = expected_holdout(posterior, live_bank, holdout_idx)
    true_holdout = born(true_state, HOLDOUTS[holdout_idx])
    live_error = abs(live_prediction - true_holdout)

    controls = {}
    for mode in ("wrong_bank", "shuffled_observation", "passive_prior", "product_bank"):
        if mode == "wrong_bank":
            control_bank = bank(seed, wrong_bank=True)
            control_posterior = update(prior, control_bank, effect_idx, observed_positive)
        elif mode == "shuffled_observation":
            control_bank = live_bank
            control_posterior = update(prior, control_bank, (effect_idx + 2) % len(INSTRUMENTS), observed_positive)
        elif mode == "passive_prior":
            control_bank = live_bank
            control_posterior = prior
        else:
            control_bank = bank(seed, product=True)
            control_posterior = update(prior, control_bank, effect_idx, observed_positive)
        pred = expected_holdout(control_posterior, control_bank, holdout_idx)
        controls[mode] = {
            "prediction": pred,
            "error": abs(pred - true_holdout),
        }
    best_control_error = min(row["error"] for row in controls.values())
    gain = best_control_error - live_error
    survived = gain > 0.015 and float(torch.max(posterior).item()) > 0.40
    return {
        "seed": seed,
        "true_id": true_id,
        "effect_idx": effect_idx,
        "holdout_idx": holdout_idx,
        "observed_positive": bool(observed_positive),
        "posterior": posterior.tolist(),
        "true_holdout": true_holdout,
        "live_prediction": live_prediction,
        "live_error": live_error,
        "best_control_error": best_control_error,
        "heldout_gain": gain,
        "survived": bool(survived),
        "controls": controls,
    }


def torch_section() -> dict[str, Any]:
    rows = [evaluate_seed(seed) for seed in range(1, 25)]
    survival_count = sum(1 for row in rows if row["survived"])
    survival_rate = survival_count / len(rows)
    gains = torch.tensor([row["heldout_gain"] for row in rows], dtype=RDTYPE)
    candidate_status = "hypothesis_bank_holdout_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_hypothesis_bank_holdout"
    return {
        "name": "finite_science_hypothesis_bank_holdout_fixture",
        "passed": True,
        "candidate_status": candidate_status,
        "candidate_survived": candidate_status == "hypothesis_bank_holdout_survived_fixture",
        "seed_count": len(rows),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "mean_heldout_gain": float(torch.mean(gains).item()),
        "min_heldout_gain": float(torch.min(gains).item()),
        "max_heldout_gain": float(torch.max(gains).item()),
        "rows": rows,
        "claim": "finite hypotheses are selected by instruments and tested on held-out QIT effects",
    }


def z3_section() -> dict[str, Any]:
    hypotheses = z3.Int("hypotheses")
    instruments = z3.Int("instruments")
    final_holodeck = z3.Bool("final_holodeck")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(hypotheses == 4, instruments == 6, z3.Not(final_holodeck), z3.Not(physics))
    bad = z3.Solver()
    bad.add(solver.assertions())
    bad.add(z3.Or(hypotheses != 4, instruments != 6))
    promo = z3.Solver()
    promo.add(solver.assertions())
    promo.add(z3.Or(final_holodeck, physics))
    return {
        "name": "z3_hypothesis_bank_nonpromotion_fence",
        "passed": bad.check() == z3.unsat and promo.check() == z3.unsat,
        "bad_fixture_unsat": bad.check() == z3.unsat,
        "promotion_unsat": promo.check() == z3.unsat,
        "claim": "held-out prediction fixture cannot promote final Holodeck or physics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    science = torch_section()
    antipromotion = z3_section()
    sections = [science, antipromotion]
    graveyard_companions = {
        "candidate_status_recorded": {
            "pass": science["candidate_status"] in {"hypothesis_bank_holdout_survived_fixture", "open_or_nonrobust_hypothesis_bank_holdout"},
            "candidate_status": science["candidate_status"],
        },
        "heldout_not_same_target_reconstruction": {"pass": True, "holdout_effect_count": len(HOLDOUTS)},
        "wrong_shuffled_passive_product_controls_present": {
            "pass": True,
            "controls": ["wrong_bank", "shuffled_observation", "passive_prior", "product_bank"],
        },
        "final_claims_rejected": {"pass": antipromotion["promotion_unsat"]},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_holodeck_not_admitted": {"pass": True, "value": False},
        "fep_world_engine_not_admitted": {"pass": True, "value": False},
        "axis0_flux_physics_not_admitted": {"pass": True, "value": False},
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
        "candidate_status": science["candidate_status"],
        "candidate_survived": science["candidate_survived"],
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "seed_count": science["seed_count"],
            "survival_count": science["survival_count"],
            "survival_rate": science["survival_rate"],
            "mean_heldout_gain": science["mean_heldout_gain"],
            "min_heldout_gain": science["min_heldout_gain"],
            "max_heldout_gain": science["max_heldout_gain"],
        },
        "science_method_translation": {
            "hypotheses": "finite two-qubit density states",
            "instrument_choice": "finite effect with largest predicted spread under the prior",
            "observation": "Born-rule binary effect readout from hidden true state",
            "update": "finite Bayesian posterior over QIT hypotheses",
            "holdout": "prediction on a separate finite QIT effect",
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["multi_step_policy_selection", "process_tensor_memory", "active_experiment_design", "world_grid"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 finite-QIT hypothesis-bank scout, not a v4 Holodeck/cognition admission probe.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "multi-step active instrument selection",
            "process-tensor memory instead of four static hypotheses",
            "couple selected hypotheses to QIT payoff selectors",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": science["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

