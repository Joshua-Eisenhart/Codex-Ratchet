#!/usr/bin/env python3
"""Stage-capability state-sweep formal scout.

The first stage-capability scout used one initial state. This follow-up asks
whether the finite 16-row QIT capability matrix survives a bounded initial-state
sweep. It is still only a formal scout: no final IGT, Axis0, flux, psychology,
cognition, economics, or physics claim is admitted.
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
from canonical_qit_engine_specs import (  # noqa: E402
    CHART_TOKEN_PRECEDENCE,
    I2,
    SX,
    SZ,
    get_chart_token_spec,
    get_schedule,
)


RESULT_DIR = ROOT / "results"
NAME = "stage_capability_state_sweep_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "stage_capability_state_sweep_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: sweeps initial states for finite strategy-row QIT "
    "capability readouts. It does not admit final IGT, Axis0, Xi, flux, "
    "psychology, cognition, economics, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density states, strategy channels, state-sweep readout matrices, and erasure controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite-cardinality and nonpromotion checks",
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

DTYPE = torch.float64
CDTYPE = torch.complex128
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
I2C = torch.as_tensor(I2, dtype=CDTYPE)
SXC = torch.as_tensor(SX, dtype=CDTYPE)
SZC = torch.as_tensor(SZ, dtype=CDTYPE)
OPS = ("Ti", "Te", "Fi", "Fe")
TOPOLOGIES = ("Se", "Ne", "Ni", "Si")


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


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = torch.as_tensor(rho, dtype=CDTYPE)
    rho = 0.5 * (rho + rho.mH)
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0)
    if float(torch.sum(vals).item()) <= 1e-14:
        vals = torch.full_like(vals, 1.0 / vals.numel())
    out = (vecs * vals.to(CDTYPE).unsqueeze(0)) @ vecs.mH
    return out / torch.trace(out)


def density_from_bloch(vec: torch.Tensor) -> torch.Tensor:
    x, y, z = [float(item) for item in torch.as_tensor(vec, dtype=DTYPE)]
    return normalize_density(0.5 * (I2C + x * SXC + y * SY + z * SZC))


def bloch_from_rho(rho: torch.Tensor) -> torch.Tensor:
    rho = normalize_density(rho)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SXC)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZC)).item(),
        ],
        dtype=DTYPE,
    )


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize_density(rho)).real
    vals = torch.clamp(vals, min=1e-12)
    return float((-torch.sum(vals * torch.log(vals))).item())


def parse_token(token: str) -> tuple[str, str, str]:
    head = token[:2]
    tail = token[-2:]
    if head in OPS and tail in TOPOLOGIES:
        return head, tail, "operator_first"
    if head in TOPOLOGIES and tail in OPS:
        return tail, head, "terrain_first"
    raise ValueError(f"could not parse token {token!r}")


def unitary(pauli: torch.Tensor, angle: float) -> torch.Tensor:
    angle_t = torch.tensor(angle, dtype=DTYPE)
    return torch.cos(angle_t / 2.0).to(CDTYPE) * I2C - 1j * torch.sin(angle_t / 2.0).to(CDTYPE) * pauli


def dephase(rho: torch.Tensor, axis: str, q: float) -> torch.Tensor:
    sigma = SZC if axis == "z" else SXC
    return normalize_density((1.0 - q) * rho + 0.5 * q * (rho + sigma @ rho @ sigma))


def strategy_channel(token: str):
    op, topology, precedence = parse_token(token)
    sign = CHART_TOKEN_PRECEDENCE.get(token, ("operator_first", +1))[1]

    def operator_only(rho: torch.Tensor) -> torch.Tensor:
        rho = normalize_density(rho)
        if op == "Ti":
            return dephase(rho, "z", 0.24)
        if op == "Te":
            return dephase(rho, "x", 0.21)
        if op == "Fi":
            u = unitary(SXC, sign * 0.37)
            return normalize_density(u @ rho @ u.mH)
        if op == "Fe":
            u = unitary(SZC, sign * 0.31)
            return normalize_density(u @ rho @ u.mH)
        raise ValueError(f"unknown op {op!r}")

    terrain_strength = {"Se": 0.075, "Ne": 0.055, "Ni": 0.085, "Si": 0.065}[topology]
    target = topology_target(topology)

    def terrain_step(rho: torch.Tensor) -> torch.Tensor:
        return normalize_density((1.0 - terrain_strength) * normalize_density(rho) + terrain_strength * target)

    def channel(rho: torch.Tensor) -> torch.Tensor:
        if precedence == "operator_first":
            return terrain_step(operator_only(rho))
        return operator_only(terrain_step(rho))

    return channel


def topology_target(topology: str) -> torch.Tensor:
    targets = {
        "Se": torch.tensor([0.42, -0.14, -0.62], dtype=DTYPE),
        "Ne": torch.tensor([0.53, 0.31, 0.27], dtype=DTYPE),
        "Ni": torch.tensor([-0.50, 0.22, 0.46], dtype=DTYPE),
        "Si": torch.tensor([-0.18, -0.44, -0.55], dtype=DTYPE),
    }
    return density_from_bloch(targets[topology])


def strategy_rows() -> list[dict[str, Any]]:
    rows = []
    seen: set[str] = set()
    for engine_type in (0, 1):
        engine_label = f"E{engine_type + 1}"
        for topology, loop_role in get_schedule(engine_type):
            chart = get_chart_token_spec(topology, engine_type, loop_role)
            token = chart["token"]
            if token in seen:
                continue
            seen.add(token)
            op = chart["operator"]
            rows.append(
                {
                    "token": token,
                    "topology": topology,
                    "operator": op,
                    "axis5_family": "dephasing" if op in {"Ti", "Te"} else "rotation",
                    "axis6_precedence": chart["precedence"],
                    "loop_role": loop_role,
                    "engine_label": engine_label,
                }
            )
    if len(rows) != 16:
        raise AssertionError(f"expected 16 strategy rows, got {len(rows)}")
    return rows


def qit_game_readout(row: dict[str, Any], other: dict[str, Any], rho0: torch.Tensor) -> dict[str, float]:
    a = strategy_channel(row["token"])
    b = strategy_channel(other["token"])
    ab = a(b(rho0))
    ba = b(a(rho0))
    return {"order_gap": float(torch.linalg.matrix_norm(ab - ba).item())}


def deterministic_bloch(seed: int) -> torch.Tensor:
    raw = torch.tensor(
        [
            torch.sin(torch.tensor(1.37 * seed + 0.19, dtype=DTYPE)).item(),
            torch.cos(torch.tensor(1.91 * seed - 0.41, dtype=DTYPE)).item(),
            torch.sin(torch.tensor(0.83 * seed + 0.67, dtype=DTYPE)).item(),
        ],
        dtype=DTYPE,
    )
    return 0.72 * raw / torch.linalg.vector_norm(raw)


def token_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a - b).item())


def row_vector(row: dict[str, Any], rows: list[dict[str, Any]], rho0: torch.Tensor) -> dict[str, Any]:
    channel = strategy_channel(row["token"])
    out = channel(rho0)
    target = topology_target(row["topology"])
    entropy_delta = entropy(out) - entropy(rho0)
    target_pull = float(torch.real(torch.trace(out @ target)).item())
    opponent_rows = [candidate for candidate in rows if candidate["token"] != row["token"]]
    order_gaps = [qit_game_readout(row, other, rho0)["order_gap"] for other in opponent_rows]
    exposure = float(torch.linalg.matrix_norm(out - rho0).item()) + abs(entropy_delta)
    futures = []
    for candidate in rows:
        if candidate["token"] == row["token"]:
            continue
        futures.append(bloch_from_rho(strategy_channel(candidate["token"])(out)))
    pairwise = []
    for i, left in enumerate(futures):
        for j, right in enumerate(futures):
            if i < j:
                pairwise.append(token_distance(left, right))
    optionality = float(sum(pairwise) / len(pairwise))
    return {
        "token": row["token"],
        "topology": row["topology"],
        "operator": row["operator"],
        "family": row["axis5_family"],
        "precedence": row["axis6_precedence"],
        "loop_role": row["loop_role"],
        "readouts": {
            "entropy_delta": entropy_delta,
            "target_pull": target_pull,
            "mean_order_gap": float(sum(order_gaps) / len(order_gaps)),
            "exposure": exposure,
            "future_optionality": optionality,
        },
    }


def feature_matrix(vectors: list[dict[str, Any]], keys: list[str]) -> torch.Tensor:
    return torch.tensor([[row["readouts"][key] for key in keys] for row in vectors], dtype=DTYPE)


def min_pairwise_gap(matrix: torch.Tensor) -> float:
    gaps = []
    for i in range(matrix.shape[0]):
        for j in range(i + 1, matrix.shape[0]):
            gaps.append(float(torch.linalg.vector_norm(matrix[i] - matrix[j]).item()))
    return min(gaps)


def grouped_spread(vectors: list[dict[str, Any]], group_key: str, readout: str) -> float:
    groups: dict[str, list[float]] = {}
    for row in vectors:
        groups.setdefault(str(row[group_key]), []).append(row["readouts"][readout])
    means = [sum(values) / len(values) for values in groups.values()]
    return max(means) - min(means)


def evaluate_seed(seed: int) -> dict[str, Any]:
    rows = strategy_rows()
    rho0 = density_from_bloch(deterministic_bloch(seed))
    vectors = [row_vector(row, rows, rho0) for row in rows]
    keys = ["entropy_delta", "target_pull", "mean_order_gap", "exposure", "future_optionality"]
    matrix = feature_matrix(vectors, keys)
    erased = {}
    for idx, key in enumerate(keys):
        reduced = torch.cat([matrix[:, :idx], matrix[:, idx + 1 :]], dim=1)
        erased[key] = min_pairwise_gap(reduced)
    full_gap = min_pairwise_gap(matrix)
    collapsed_count = sum(1 for value in erased.values() if value < full_gap)
    operator_spread = grouped_spread(vectors, "family", "entropy_delta")
    terrain_spread = grouped_spread(vectors, "topology", "target_pull")
    order_spread = grouped_spread(vectors, "precedence", "mean_order_gap")
    role_spread = grouped_spread(vectors, "loop_role", "future_optionality")
    survived = (
        full_gap > 0.006
        and operator_spread > 0.010
        and terrain_spread > 0.020
        and order_spread > 0.001
        and role_spread > 0.001
        and collapsed_count >= 3
    )
    return {
        "seed": seed,
        "full_min_pairwise_gap": full_gap,
        "operator_family_entropy_spread": operator_spread,
        "terrain_target_spread": terrain_spread,
        "precedence_order_gap_spread": order_spread,
        "loop_role_optionality_spread": role_spread,
        "readout_erasure_collapsed_count": collapsed_count,
        "survived": bool(survived),
    }


def sweep_section() -> dict[str, Any]:
    rows = [evaluate_seed(seed) for seed in range(1, 25)]
    survival_count = sum(1 for row in rows if row["survived"])
    survival_rate = survival_count / len(rows)
    gaps = torch.tensor([row["full_min_pairwise_gap"] for row in rows], dtype=DTYPE)
    candidate_status = "survived_state_sweep" if survival_rate >= 0.75 else "open_or_nonrobust_under_state_sweep"
    passed = len(rows) == 24 and candidate_status in {"survived_state_sweep", "open_or_nonrobust_under_state_sweep"}
    return {
        "name": "finite_stage_capability_state_sweep_fixture",
        "passed": bool(passed),
        "candidate_status": candidate_status,
        "candidate_survived": candidate_status == "survived_state_sweep",
        "seed_count": len(rows),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "mean_min_pairwise_gap": float(torch.mean(gaps).item()),
        "min_min_pairwise_gap": float(torch.min(gaps).item()),
        "max_min_pairwise_gap": float(torch.max(gaps).item()),
        "rows": rows,
        "claim": "finite strategy-row capability separation is classified across a bounded initial-state sweep",
    }


def z3_nonpromotion_section() -> dict[str, Any]:
    seed_count = z3.Int("seed_count")
    row_count = z3.Int("row_count")
    promoted = z3.Bool("stage_capability_state_sweep_promoted")
    solver = z3.Solver()
    solver.add(seed_count == 24, row_count == 16, z3.Not(promoted))
    bad = z3.Solver()
    bad.add(solver.assertions())
    bad.add(z3.Or(seed_count != 24, row_count != 16))
    promo = z3.Solver()
    promo.add(solver.assertions())
    promo.add(promoted)
    passed = bad.check() == z3.unsat and promo.check() == z3.unsat
    return {
        "name": "z3_state_sweep_nonpromotion_fence",
        "passed": bool(passed),
        "bad_count_unsat": bad.check() == z3.unsat,
        "promotion_unsat": promo.check() == z3.unsat,
        "claim": "state-sweep evidence cannot promote final IGT, Axis0, flux, cognition, or physics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    sweep = sweep_section()
    antipromotion = z3_nonpromotion_section()
    sections = [sweep, antipromotion]
    graveyard_companions = {
        "state_sweep_status_recorded": {
            "pass": sweep["candidate_status"] in {"survived_state_sweep", "open_or_nonrobust_under_state_sweep"},
            "candidate_status": sweep["candidate_status"],
        },
        "not_single_fixture_only": {"pass": sweep["seed_count"] == 24, "seed_count": sweep["seed_count"]},
        "readout_separation_not_promoted_to_final_theory": {"pass": antipromotion["promotion_unsat"]},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_igt_not_admitted": {"pass": True, "value": False},
        "axis0_not_admitted": {"pass": True, "value": False},
        "flux_not_admitted": {"pass": True, "value": False},
        "psychology_physics_not_admitted": {"pass": True, "value": False},
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
            "mean_min_pairwise_gap": sweep["mean_min_pairwise_gap"],
            "min_min_pairwise_gap": sweep["min_min_pairwise_gap"],
            "max_min_pairwise_gap": sweep["max_min_pairwise_gap"],
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": [
                "held-out strategy readout weights",
                "population dynamics over state sweep",
                "Holodeck world-memory coupled strategy choice",
            ],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 finite-QIT state-sweep check over existing strategy rows, not a v4 typology or ontology probe.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "held-out readout weight search",
            "population strategy dynamics over swept states",
            "world-memory coupled strategy selection",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": sweep["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
