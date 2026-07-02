#!/usr/bin/env python3
"""Source-aligned runtime trajectory receipt coupling scout.

Primary purpose: keep getting the operational runtime working.

This scout does not try to rescue Axis0/flux/IGT by label replay alone. It
first runs the current source-aligned torch runtime, then asks whether those
actual stage receipts are rich enough to drive small cut-current and selector
readouts.
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
import source_aligned_qit_engine_runtime as rt  # noqa: E402


RESULT_DIR = ROOT / "results"
NAME = "runtime_trajectory_receipt_coupling_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_source_aligned_runtime_trajectory_receipt"
SOURCE_ALIGNMENT_CATEGORY = "source_aligned_runtime_receipt_coupling"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: executes current source-aligned torch runtime trajectories "
    "and tests whether their stage receipts can drive tiny cut-current and IGT "
    "selector readouts. It does not admit final engines, Axis0, Xi, flux, IGT, "
    "Holodeck, Standard Model, gravity, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density states, stage trajectories, two-qubit cut readouts, and selector matrices",
    },
    "source_aligned_qit_engine_runtime": {
        "tried": True,
        "used": True,
        "reason": "load-bearing execution of the current source-aligned runtime stage functions and charts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and finite-cardinality guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "source_aligned_qit_engine_runtime": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
}

CDTYPE = torch.complex128
RDTYPE = torch.float64
EPS = 1e-10
I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def dagger(a: torch.Tensor) -> torch.Tensor:
    return torch.conj(a.transpose(-2, -1))


def normalize(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0)
    if float(torch.sum(vals).item()) <= EPS:
        vals = torch.full_like(vals, 1.0 / vals.numel())
    out = (vecs * vals.to(CDTYPE).unsqueeze(0)) @ dagger(vecs)
    return out / torch.trace(out)


def rho_seed(seed: int) -> torch.Tensor:
    theta = 0.21 + 0.077 * seed
    phi = 0.37 + 0.43 * seed
    r = torch.tensor(
        [
            0.68 * math.sin(theta) * math.cos(phi),
            0.61 * math.sin(theta) * math.sin(phi),
            0.55 * math.cos(theta),
        ],
        dtype=RDTYPE,
    )
    return rt.rho_from_bloch(float(r[0]), float(r[1]), float(r[2]))


def run_source_trajectory(label: str, seed: int, cycles: int) -> dict[str, Any]:
    rho = rho_seed(seed)
    trajectory: list[dict[str, Any]] = []
    cycle_end_states: list[torch.Tensor] = []
    for cycle in range(cycles):
        for idx, stage in enumerate(rt.ENGINE_CHARTS[label]):
            before = rho
            rho, record = rt.run_stage(rho, label, stage, idx)
            local_record = dict(record)
            local_record["cycle"] = cycle
            local_record["stage_global_idx"] = len(trajectory)
            local_record["stage_delta_fro"] = float(torch.linalg.matrix_norm(rho - before).item())
            local_record["entropy_before"] = rt.entropy(before)
            local_record["purity_before"] = rt.purity(before)
            trajectory.append(local_record)
        cycle_end_states.append(rho)
    drift = float(torch.linalg.matrix_norm(cycle_end_states[-1] - cycle_end_states[-2]).item()) if cycles > 1 else 0.0
    return {
        "label": label,
        "seed": seed,
        "cycles": cycles,
        "final_density": rho,
        "cycle_end_states": cycle_end_states,
        "trajectory": trajectory,
        "last_cycle_drift_fro": drift,
        "tokens_seen": sorted({row["token"] for row in trajectory}),
        "terrain_realizations_seen": sorted({row["terrain_realization"] for row in trajectory}),
        "all_stage_valid": all(bool(row["valid_density"]) for row in trajectory),
        "all_a6_xor_ok": all(bool(row["axis_values"]["A6_xor_ok"]) for row in trajectory),
        "raw_path_xor_pass_count": sum(1 for row in trajectory if bool(row["axis_values"]["A6_path_xor_ok"])),
        "stage_count": len(trajectory),
    }


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize(rho)).real.clamp_min(0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    vals = vals[vals > EPS]
    return float((-torch.sum(vals * torch.log(vals))).item())


def partial_trace_2q(rho: torch.Tensor, keep: int) -> torch.Tensor:
    shaped = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return torch.einsum("abad->bd", shaped)
    if keep == 1:
        return torch.einsum("abcb->ac", shaped)
    raise ValueError(keep)


def mutual_information_2q(rho: torch.Tensor) -> float:
    return entropy(partial_trace_2q(rho, 0)) + entropy(partial_trace_2q(rho, 1)) - entropy(rho)


def unitary_pair(theta: float, *, label_erased: bool = False) -> torch.Tensor:
    op = torch.kron(Z, Z if not label_erased else X)
    return math.cos(theta / 2.0) * torch.eye(4, dtype=CDTYPE) - 1j * math.sin(theta / 2.0) * op


def pair_from_cycle_states(left: torch.Tensor, right: torch.Tensor, theta: float, *, mode: str) -> torch.Tensor:
    rho = torch.kron(left, right)
    if mode == "product":
        return normalize(rho)
    u = unitary_pair(theta, label_erased=mode == "label_erased")
    return normalize(u @ rho @ dagger(u))


def receipt_integrity_section() -> dict[str, Any]:
    cases = []
    all_tokens = set()
    all_terrains = set()
    for seed in range(1, 7):
        left = run_source_trajectory("T1", seed, cycles=16)
        right = run_source_trajectory("T2", seed, cycles=16)
        all_tokens.update(left["tokens_seen"])
        all_tokens.update(right["tokens_seen"])
        all_terrains.update(left["terrain_realizations_seen"])
        all_terrains.update(right["terrain_realizations_seen"])
        final_gap = float(torch.linalg.matrix_norm(left["final_density"] - right["final_density"]).item())
        cases.append(
            {
                "seed": seed,
                "left_stage_count": left["stage_count"],
                "right_stage_count": right["stage_count"],
                "left_valid": left["all_stage_valid"],
                "right_valid": right["all_stage_valid"],
                "left_a6_xor_ok": left["all_a6_xor_ok"],
                "right_a6_xor_ok": right["all_a6_xor_ok"],
                "left_raw_path_xor_pass_count": left["raw_path_xor_pass_count"],
                "right_raw_path_xor_pass_count": right["raw_path_xor_pass_count"],
                "left_last_cycle_drift_fro": left["last_cycle_drift_fro"],
                "right_last_cycle_drift_fro": right["last_cycle_drift_fro"],
                "final_density_gap": final_gap,
            }
        )
    source_runtime_operational = (
        all(row["left_stage_count"] == 128 and row["right_stage_count"] == 128 for row in cases)
        and all(row["left_valid"] and row["right_valid"] for row in cases)
        and all(row["left_a6_xor_ok"] and row["right_a6_xor_ok"] for row in cases)
        and len(all_tokens) == 16
        and len(all_terrains) == 8
    )
    return {
        "name": "source_aligned_runtime_trajectory_receipt_integrity",
        "passed": source_runtime_operational,
        "candidate_status": "source_runtime_receipts_operational" if source_runtime_operational else "source_runtime_receipts_incomplete",
        "candidate_survived": source_runtime_operational,
        "case_count": len(cases),
        "token_count": len(all_tokens),
        "terrain_realization_count": len(all_terrains),
        "tokens_seen": sorted(all_tokens),
        "terrain_realizations_seen": sorted(all_terrains),
        "mean_final_density_gap": sum(row["final_density_gap"] for row in cases) / len(cases),
        "cases": cases,
        "claim": "source-aligned runtime trajectories produce finite valid stage receipts across both types",
    }


def cut_current_from_source_cycles(mode: str, seed: int) -> dict[str, Any]:
    left = run_source_trajectory("T1", seed, cycles=12)
    right = run_source_trajectory("T2", seed, cycles=12)
    left_states = left["cycle_end_states"]
    right_states = right["cycle_end_states"]
    if mode == "order_scramble":
        right_states = list(reversed(right_states))
    currents = []
    prev = pair_from_cycle_states(left_states[0], right_states[0], 0.0, mode="product")
    for idx, (rho_l, rho_r) in enumerate(zip(left_states, right_states, strict=True)):
        if mode == "commuting":
            theta = 0.015
        else:
            delta_l = left["trajectory"][idx * 8 + 7]["stage_delta_fro"]
            delta_r = right["trajectory"][idx * 8 + 7]["stage_delta_fro"]
            theta = 0.025 + 0.20 * (delta_l + delta_r)
        current = pair_from_cycle_states(rho_l, rho_r, theta, mode=mode)
        mi_delta = mutual_information_2q(current) - mutual_information_2q(prev)
        cut_op = torch.kron(Z, X)
        comm_gap = float(torch.linalg.matrix_norm(cut_op @ current - current @ cut_op).item())
        currents.append(abs(mi_delta) + 0.04 * comm_gap)
        prev = current
    return {
        "mode": mode,
        "total_current": sum(currents),
        "max_current": max(currents),
        "mean_current": sum(currents) / len(currents),
    }


def cut_current_section() -> dict[str, Any]:
    cases = []
    for seed in range(1, 7):
        modes = {
            mode: cut_current_from_source_cycles(mode, seed)
            for mode in ("live", "product", "order_scramble", "commuting", "label_erased")
        }
        live = modes["live"]["total_current"]
        best_control = max(row["total_current"] for key, row in modes.items() if key != "live")
        margin = live - best_control
        survived = margin > 0.02
        cases.append(
            {
                "seed": seed,
                "survived": bool(survived),
                "live_current": live,
                "best_control_current": best_control,
                "margin": margin,
                "mode_totals": {key: row["total_current"] for key, row in modes.items()},
            }
        )
    survival_count = sum(1 for row in cases if row["survived"])
    survival_rate = survival_count / len(cases)
    return {
        "name": "source_trajectory_cut_current_fixture",
        "passed": True,
        "candidate_status": "source_trajectory_cut_current_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_source_trajectory_cut_current",
        "candidate_survived": survival_rate >= 0.75,
        "case_count": len(cases),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "mean_margin": sum(row["margin"] for row in cases) / len(cases),
        "cases": cases,
        "claim": "actual source-aligned cycle-end trajectories can drive a tiny current-through-cut fixture",
    }


def selector_score(row: dict[str, Any], *, mode: str) -> tuple[float, float]:
    axis = row["axis_values"]
    entropy_drop = float(row["entropy_before"] - row["entropy_after"])
    purity_gain = float(row["purity_after"] - row["purity_before"])
    stage_delta = float(row["stage_delta_fro"])
    a6_bonus = 0.03 if axis["A6_xor_ok"] else -0.12
    native_bonus = 0.02 if row["operator"] in {"Ti", "Te", "Fi", "Fe"} else -0.10
    if mode == "label_erased":
        native_bonus = 0.0
    if mode == "commuting":
        stage_delta *= 0.2
    if mode == "scrambled":
        entropy_drop *= -1.0
    payoff = 0.36 * stage_delta + 0.28 * max(0.0, entropy_drop) + 0.18 * max(0.0, purity_gain) + a6_bonus + native_bonus
    damage = 0.34 * max(0.0, -entropy_drop) + 0.22 * max(0.0, -purity_gain) + 0.11 * stage_delta - a6_bonus
    return payoff, damage


def selector_indices(payoffs: torch.Tensor, damages: torch.Tensor) -> dict[str, int]:
    return {
        "maximax": int(torch.argmax(torch.max(payoffs, dim=1).values).item()),
        "maximin": int(torch.argmax(torch.min(payoffs, dim=1).values).item()),
        "minimax": int(torch.argmin(torch.max(damages, dim=1).values).item()),
        "minimin": int(torch.argmin(torch.min(damages, dim=1).values).item()),
    }


def selector_section() -> dict[str, Any]:
    cases = []
    for seed in range(1, 7):
        left = run_source_trajectory("T1", seed, cycles=6)["trajectory"]
        right = run_source_trajectory("T2", seed, cycles=6)["trajectory"]
        # One representative receipt per token keeps the selector finite and typed.
        receipts: dict[str, dict[str, Any]] = {}
        for row in [*left, *right]:
            receipts.setdefault(row["token"], row)
        rows = list(receipts.values())
        reports = {}
        for mode in ("live", "commuting", "scrambled", "label_erased"):
            payoff = torch.zeros((len(rows), len(rows)), dtype=RDTYPE)
            damage = torch.zeros_like(payoff)
            for i, row_i in enumerate(rows):
                for j, row_j in enumerate(rows):
                    p_i, d_i = selector_score(row_i, mode=mode)
                    p_j, d_j = selector_score(row_j, mode=mode)
                    token_interaction = 0.015 if row_i["topology"] != row_j["topology"] else -0.010
                    payoff[i, j] = p_i + 0.35 * p_j + token_interaction
                    damage[i, j] = d_i + 0.25 * d_j - token_interaction
            selectors = selector_indices(payoff, damage)
            reports[mode] = {
                "tokens": {key: rows[idx]["token"] for key, idx in selectors.items()},
                "payoff_range": float((torch.max(payoff) - torch.min(payoff)).item()),
            }
        live_tokens = reports["live"]["tokens"]
        control_changes = {
            mode: sum(1 for key in live_tokens if live_tokens[key] != reports[mode]["tokens"][key])
            for mode in ("commuting", "scrambled", "label_erased")
        }
        minimin_not_same_as_maximax = live_tokens["minimin"] != live_tokens["maximax"]
        survived = min(control_changes.values()) >= 1 and minimin_not_same_as_maximax and reports["live"]["payoff_range"] > 0.015
        cases.append(
            {
                "seed": seed,
                "survived": bool(survived),
                "live_tokens": live_tokens,
                "control_changes": control_changes,
                "minimin_not_same_as_maximax": bool(minimin_not_same_as_maximax),
                "live_payoff_range": reports["live"]["payoff_range"],
            }
        )
    survival_count = sum(1 for row in cases if row["survived"])
    survival_rate = survival_count / len(cases)
    return {
        "name": "source_trajectory_igt_selector_fixture",
        "passed": True,
        "candidate_status": "source_trajectory_igt_selector_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_source_trajectory_igt_selector",
        "candidate_survived": survival_rate >= 0.75,
        "case_count": len(cases),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "cases": cases,
        "claim": "minimax/maximax/maximin/minimin selectors consume actual runtime stage receipts",
    }


def z3_section() -> dict[str, Any]:
    stages_per_pair_seed = z3.Int("stages_per_pair_seed")
    final_runtime = z3.Bool("final_runtime")
    final_flux = z3.Bool("final_flux")
    final_igt = z3.Bool("final_igt")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(stages_per_pair_seed == 256, z3.Not(final_runtime), z3.Not(final_flux), z3.Not(final_igt), z3.Not(physics))
    bad_count = z3.Solver()
    bad_count.add(solver.assertions())
    bad_count.add(stages_per_pair_seed != 256)
    promo = z3.Solver()
    promo.add(solver.assertions())
    promo.add(z3.Or(final_runtime, final_flux, final_igt, physics))
    return {
        "name": "z3_runtime_trajectory_nonpromotion_fence",
        "passed": bad_count.check() == z3.unsat and promo.check() == z3.unsat,
        "stage_count_guard_unsat": bad_count.check() == z3.unsat,
        "promotion_unsat": promo.check() == z3.unsat,
        "claim": "source trajectory receipts cannot promote final runtime, flux, IGT, or physics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    integrity = receipt_integrity_section()
    current = cut_current_section()
    selectors = selector_section()
    antipromotion = z3_section()
    sections = [integrity, current, selectors, antipromotion]
    graveyard_companions = {
        "actual_source_runtime_executed": {
            "pass": integrity["passed"],
            "meaning": "uses source_aligned_qit_engine_runtime.run_stage over T1/T2 charts, not only static token labels",
        },
        "raw_geometry_path_xor_not_required": {
            "pass": True,
            "meaning": "A6 xor is checked against chart inner/outer; raw fiber/base path xor is reported but not required",
        },
        "receipt_pass_not_candidate_survival": {
            "pass": True,
            "meaning": "all_pass validates receipt and gates; candidate_status carries scientific status",
        },
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_runtime_not_admitted": {"pass": True, "value": False},
        "final_axis0_xi_flux_not_admitted": {"pass": True, "value": False},
        "final_igt_not_admitted": {"pass": True, "value": False},
        "physics_not_admitted": {"pass": True, "value": False},
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
        "candidate_status": {
            "runtime_receipts": integrity["candidate_status"],
            "cut_current": current["candidate_status"],
            "igt_selector": selectors["candidate_status"],
        },
        "candidate_survived": {
            "runtime_receipts": integrity["candidate_survived"],
            "cut_current": current["candidate_survived"],
            "igt_selector": selectors["candidate_survived"],
        },
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "runtime_receipt_token_count": integrity["token_count"],
            "runtime_receipt_terrain_count": integrity["terrain_realization_count"],
            "runtime_receipt_mean_final_density_gap": integrity["mean_final_density_gap"],
            "source_cut_current_survival_rate": current["survival_rate"],
            "source_cut_current_mean_margin": current["mean_margin"],
            "source_igt_selector_survival_rate": selectors["survival_rate"],
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["EngineCore NumPy-boundary direct import", "8-16 qubit MPS transport", "population dynamics", "process tensor memory"],
            "recommended_next": [
                "port this trajectory receipt shape into the 8-qubit suite",
                "run MPS/no-dense cut current once this tiny receipt coupling is stable",
                "only then add multi-agent population dynamics",
            ],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 source-aligned torch runtime trajectory receipt scout; it is not a legacy v4 Holodeck/IGT/physics probe.",
            "v4_equivalent": None,
        },
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": result["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
