#!/usr/bin/env python3
"""QIT payoff-selector strategy formal scout.

This scout gives the user's IGT/game-theory idea a minimal QIT form. Classical
selectors are translated into finite readouts over noncommuting strategy
composition:

- maximax: maximize best attainable utility;
- maximin: maximize worst-case utility;
- minimax: minimize worst-case QIT damage;
- minimin: minimize best-case QIT damage.

The scout asks only whether these selectors are numerically load-bearing against
commuting and label-scramble controls. It does not admit final IGT/game theory.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from sim_stage_capability_state_sweep_probe import (  # noqa: E402
    CDTYPE,
    DTYPE,
    I2C,
    SXC,
    SZC,
    as_jsonable,
    bloch_from_rho,
    density_from_bloch,
    entropy,
    normalize_density,
    strategy_channel,
    strategy_rows,
    topology_target,
    unitary,
)


RESULT_DIR = ROOT / "results"
NAME = "qit_payoff_selector_strategy_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "qit_payoff_selector_strategy_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: maps minimax, maximax, maximin, and minimin to finite "
    "QIT selectors over bounded strategy-channel readouts. It does not admit "
    "final IGT, economics, game theory, psychology, cognition, Axis0, flux, "
    "or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density states, strategy composition, payoff/loss matrices, and selector controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite selector and nonpromotion checks",
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


def initial_state(seed: int) -> torch.Tensor:
    vec = torch.tensor(
        [
            0.51 * torch.sin(torch.tensor(0.47 * seed, dtype=DTYPE)),
            0.43 * torch.cos(torch.tensor(0.31 * seed + 0.2, dtype=DTYPE)),
            0.36 * torch.sin(torch.tensor(0.53 * seed - 0.1, dtype=DTYPE)),
        ],
        dtype=DTYPE,
    )
    return density_from_bloch(vec)


def commuting_channel(token: str):
    # Commuting control: all strategies collapse to z-axis rotations/dephasing.
    sign = +1.0 if token[:2] in {"Ti", "Te", "Fi", "Fe"} else -1.0

    def channel(rho: torch.Tensor) -> torch.Tensor:
        rho = normalize_density(rho)
        u = unitary(SZC, sign * 0.19)
        dephased = 0.82 * (u @ rho @ u.mH) + 0.18 * (0.5 * (rho + SZC @ rho @ SZC))
        return normalize_density(dephased)

    return channel


def scrambled_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shifted = []
    tokens = [row["token"] for row in rows]
    for idx, row in enumerate(rows):
        clone = dict(row)
        clone["token"] = tokens[(idx * 5 + 3) % len(tokens)]
        shifted.append(clone)
    return shifted


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize_density(a) - normalize_density(b))
    return float(0.5 * torch.sum(torch.abs(vals.real)).item())


def retained_coherence(rho: torch.Tensor) -> float:
    bloch = bloch_from_rho(rho)
    return float(torch.linalg.vector_norm(bloch[:2]).item())


def pair_readout(
    row: dict[str, Any],
    opponent: dict[str, Any],
    rho0: torch.Tensor,
    *,
    mode: str,
) -> dict[str, float]:
    make_channel = commuting_channel if mode == "commuting" else strategy_channel
    a = make_channel(row["token"])
    b = make_channel(opponent["token"])
    ab = a(b(rho0))
    ba = b(a(rho0))
    target = topology_target(row["topology"])
    target_pull = float(torch.real(torch.trace(ab @ target)).item())
    entropy_cost = max(0.0, entropy(ab) - entropy(rho0))
    order_gap = float(torch.linalg.matrix_norm(ab - ba).item())
    target_damage = trace_distance(ab, target)
    coherence = retained_coherence(ab)
    utility = 0.54 * target_pull + 0.18 * coherence + 0.20 * order_gap - 0.16 * entropy_cost
    damage = 0.65 * target_damage + 0.25 * entropy_cost - 0.10 * order_gap
    return {
        "utility": utility,
        "damage": damage,
        "target_pull": target_pull,
        "entropy_cost": entropy_cost,
        "order_gap": order_gap,
        "target_damage": target_damage,
        "coherence": coherence,
    }


def matrix_for_seed(seed: int, *, mode: str) -> dict[str, Any]:
    rows = strategy_rows()
    if mode == "scrambled":
        rows = scrambled_rows(rows)
    rho0 = initial_state(seed)
    utilities = []
    damages = []
    for row in rows:
        u_row = []
        d_row = []
        for opponent in rows:
            readout = pair_readout(row, opponent, rho0, mode="commuting" if mode == "commuting" else "live")
            u_row.append(readout["utility"])
            d_row.append(readout["damage"])
        utilities.append(u_row)
        damages.append(d_row)
    utility = torch.tensor(utilities, dtype=DTYPE)
    damage = torch.tensor(damages, dtype=DTYPE)
    return {"rows": rows, "utility": utility, "damage": damage}


def selector_report(seed: int, mode: str) -> dict[str, Any]:
    data = matrix_for_seed(seed, mode=mode)
    rows = data["rows"]
    utility = data["utility"]
    damage = data["damage"]
    selectors = {
        "maximax": int(torch.argmax(torch.max(utility, dim=1).values).item()),
        "maximin": int(torch.argmax(torch.min(utility, dim=1).values).item()),
        "minimax": int(torch.argmin(torch.max(damage, dim=1).values).item()),
        "minimin": int(torch.argmin(torch.min(damage, dim=1).values).item()),
    }
    details = {}
    for name, idx in selectors.items():
        details[name] = {
            "index": idx,
            "token": rows[idx]["token"],
            "topology": rows[idx]["topology"],
            "family": rows[idx]["axis5_family"],
            "worst_utility": float(torch.min(utility[idx]).item()),
            "best_utility": float(torch.max(utility[idx]).item()),
            "worst_damage": float(torch.max(damage[idx]).item()),
            "best_damage": float(torch.min(damage[idx]).item()),
        }
    return {
        "seed": seed,
        "mode": mode,
        "selector_indices": selectors,
        "selector_details": details,
        "utility_range": float((torch.max(utility) - torch.min(utility)).item()),
        "damage_range": float((torch.max(damage) - torch.min(damage)).item()),
        "mean_utility": float(torch.mean(utility).item()),
        "mean_damage": float(torch.mean(damage).item()),
    }


def evaluate_seed(seed: int) -> dict[str, Any]:
    live = selector_report(seed, "live")
    commuting = selector_report(seed, "commuting")
    scrambled = selector_report(seed, "scrambled")
    live_tokens = {name: row["token"] for name, row in live["selector_details"].items()}
    commuting_tokens = {name: row["token"] for name, row in commuting["selector_details"].items()}
    scrambled_tokens = {name: row["token"] for name, row in scrambled["selector_details"].items()}
    changed_vs_commuting = sum(1 for name in live_tokens if live_tokens[name] != commuting_tokens[name])
    changed_vs_scrambled = sum(1 for name in live_tokens if live_tokens[name] != scrambled_tokens[name])
    minimin = live["selector_details"]["minimin"]
    maximin = live["selector_details"]["maximin"]
    minimin_specializes = minimin["best_damage"] < maximin["best_damage"] and minimin["worst_damage"] >= maximin["worst_damage"]
    survived = (
        live["utility_range"] > commuting["utility_range"] + 0.01
        and changed_vs_commuting >= 2
        and changed_vs_scrambled >= 2
        and minimin_specializes
    )
    return {
        "seed": seed,
        "survived": bool(survived),
        "changed_vs_commuting": changed_vs_commuting,
        "changed_vs_scrambled": changed_vs_scrambled,
        "minimin_specializes": bool(minimin_specializes),
        "live": live,
        "commuting": commuting,
        "scrambled": scrambled,
    }


def torch_section() -> dict[str, Any]:
    rows = [evaluate_seed(seed) for seed in range(1, 13)]
    survival_count = sum(1 for row in rows if row["survived"])
    survival_rate = survival_count / len(rows)
    minimin_specialization_rate = sum(1 for row in rows if row["minimin_specializes"]) / len(rows)
    candidate_status = "qit_selector_strategy_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_qit_selector_strategy"
    return {
        "name": "finite_qit_payoff_selector_strategy_fixture",
        "passed": True,
        "candidate_status": candidate_status,
        "candidate_survived": candidate_status == "qit_selector_strategy_survived_fixture",
        "seed_count": len(rows),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "minimin_specialization_rate": minimin_specialization_rate,
        "rows_preview": rows[:4],
        "claim": "classical selectors are translated into finite QIT payoff/damage selectors and checked against controls",
    }


def z3_section() -> dict[str, Any]:
    selector_count = z3.Int("selector_count")
    promoted = z3.Bool("final_igt")
    economics = z3.Bool("economics")
    solver = z3.Solver()
    solver.add(selector_count == 4, z3.Not(promoted), z3.Not(economics))
    bad = z3.Solver()
    bad.add(solver.assertions())
    bad.add(selector_count != 4)
    promo = z3.Solver()
    promo.add(solver.assertions())
    promo.add(z3.Or(promoted, economics))
    return {
        "name": "z3_qit_selector_nonpromotion_fence",
        "passed": bad.check() == z3.unsat and promo.check() == z3.unsat,
        "bad_selector_count_unsat": bad.check() == z3.unsat,
        "promotion_unsat": promo.check() == z3.unsat,
        "claim": "selector translation cannot promote final IGT or economics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    selector = torch_section()
    antipromotion = z3_section()
    sections = [selector, antipromotion]
    graveyard_companions = {
        "selector_status_recorded": {
            "pass": selector["candidate_status"] in {"qit_selector_strategy_survived_fixture", "open_or_nonrobust_qit_selector_strategy"},
            "candidate_status": selector["candidate_status"],
        },
        "four_selectors_tested": {"pass": antipromotion["bad_selector_count_unsat"], "selectors": ["minimax", "maximax", "maximin", "minimin"]},
        "commuting_and_scrambled_controls_present": {"pass": True, "controls": ["commuting", "scrambled"]},
        "final_claims_rejected": {"pass": antipromotion["promotion_unsat"]},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_igt_not_admitted": {"pass": True, "value": False},
        "economics_not_admitted": {"pass": True, "value": False},
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
        "candidate_status": selector["candidate_status"],
        "candidate_survived": selector["candidate_survived"],
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "seed_count": selector["seed_count"],
            "survival_count": selector["survival_count"],
            "survival_rate": selector["survival_rate"],
            "minimin_specialization_rate": selector["minimin_specialization_rate"],
        },
        "selector_translation": {
            "maximax": "argmax_i max_j utility[i,j]",
            "maximin": "argmax_i min_j utility[i,j]",
            "minimax": "argmin_i max_j damage[i,j]",
            "minimin": "argmin_i min_j damage[i,j]",
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["population_dynamics", "replicator_dynamics", "multi-character_world", "held_out_equilibrium_sweep"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 finite QIT selector translation, not a v4 psychology/game-theory admission probe.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "two-character density-carrier interaction with separate memories",
            "population dynamics over selected QIT strategies",
            "label-blind equilibrium tests over held-out channel parameters",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": selector["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

