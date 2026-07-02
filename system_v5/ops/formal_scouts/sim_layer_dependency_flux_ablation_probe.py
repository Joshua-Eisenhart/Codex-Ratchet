#!/usr/bin/env python3
"""Layer-dependency flux ablation formal scout.

This follow-up tightens the bounded-layer flux fixture. A flux-like readout is
not considered meaningful unless each layer changes the next numeric control:
carrier -> geometry, geometry -> operator strength, operator order -> closure,
and closure -> final cut current. This is still a formal scout only.
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
NAME = "layer_dependency_flux_ablation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "layer_dependency_flux_ablation_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether flux-like readouts require numeric "
    "carrier-to-geometry-to-operator-to-closure dependencies. It does not "
    "admit final flux, Axis0, Xi, Yang-Mills, Standard Model, gravity, "
    "cosmology, or physical unification."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density states, bounded layer stack, cut readouts, and dependency ablations",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and finite-layer dependency checks",
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
EPS = 1e-10
I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)

ROWS = {
    "E1": ["TiSe", "SeFi", "NeTi", "FiNe", "NiFe", "TeNi", "FeSi", "SiTe"],
    "E2": ["FiSe", "SeTi", "TeSi", "SiFe", "NiTe", "FeNi", "NeFi", "TiNe"],
}


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


def normalize(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0)
    if float(torch.sum(vals).item()) <= EPS:
        vals = torch.full_like(vals, 1.0 / vals.numel())
    out = (vecs * vals.to(CDTYPE).unsqueeze(0)) @ dagger(vecs)
    return out / torch.trace(out)


def kron_all(ops: list[torch.Tensor]) -> torch.Tensor:
    out = ops[0]
    for op in ops[1:]:
        out = torch.kron(out, op)
    return out


def local_full(op: torch.Tensor, q: int, n: int) -> torch.Tensor:
    ops = [I2 for _ in range(n)]
    ops[q] = op
    return kron_all(ops)


def product_carrier(engine: str, n: int, seed: int) -> torch.Tensor:
    chirality = 1.0 if engine == "E1" else -1.0
    states = []
    for q in range(n):
        z = chirality * (0.28 + 0.04 * ((seed + q) % 3)) * (1.0 if q < max(1, n // 2) else -0.55)
        x = 0.18 * math.sin(0.37 * seed + 0.51 * q)
        length = min(0.82, math.sqrt(x * x + z * z))
        if length <= EPS:
            rho = 0.5 * I2
        else:
            rho = 0.5 * (I2 + x * X + z * Z)
        states.append(normalize(rho))
    return normalize(kron_all(states))


def plus_carrier(n: int) -> torch.Tensor:
    vec = torch.ones(2**n, dtype=CDTYPE) / math.sqrt(2**n)
    return vec[:, None] @ dagger(vec[:, None])


def unitary(axis: torch.Tensor, theta: float, q: int, n: int) -> torch.Tensor:
    u1 = math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * axis
    return local_full(u1, q, n)


def zz_unitary(theta: float, a: int, b: int, n: int) -> torch.Tensor:
    zz = local_full(Z, a, n) @ local_full(Z, b, n)
    dim = 2**n
    return math.cos(theta / 2.0) * torch.eye(dim, dtype=CDTYPE) - 1j * math.sin(theta / 2.0) * zz


def apply_unitary(rho: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    return normalize(u @ rho @ dagger(u))


def apply_dephase(rho: torch.Tensor, axis: torch.Tensor, q: int, n: int, strength: float) -> torch.Tensor:
    full = local_full(axis, q, n)
    return normalize((1.0 - strength) * rho + strength * full @ rho @ full)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize(rho)).real.clamp_min(0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    vals = vals[vals > EPS]
    return float((-torch.sum(vals * torch.log(vals))).item())


def partial_trace(rho: torch.Tensor, keep: list[int], n: int) -> torch.Tensor:
    dims = [2] * n
    keep_set = set(keep)
    reshaped = rho.reshape(*dims, *dims)
    letters = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    left = letters[:n]
    right = letters[n : 2 * n]
    for idx in range(n):
        if idx not in keep_set:
            right[idx] = left[idx]
    out_letters = [left[idx] for idx in keep] + [right[idx] for idx in keep]
    return torch.einsum("".join(left + right) + "->" + "".join(out_letters), reshaped).reshape(2 ** len(keep), 2 ** len(keep))


def mutual_information(rho: torch.Tensor, left: list[int], right: list[int], n: int) -> float:
    union = sorted(set(left + right))
    return entropy(partial_trace(rho, left, n)) + entropy(partial_trace(rho, right, n)) - entropy(partial_trace(rho, union, n))


def z_expectation(rho: torch.Tensor, q: int, n: int) -> float:
    return float(torch.real(torch.trace(rho @ local_full(Z, q, n))).item())


def token_op(token: str) -> str:
    for op in ("Ti", "Te", "Fi", "Fe"):
        if token.startswith(op) or token.endswith(op):
            return op
    raise ValueError(token)


def apply_token(rho: torch.Tensor, token: str, q: int, n: int, strength: float) -> torch.Tensor:
    op = token_op(token)
    if op == "Ti":
        return apply_dephase(rho, Z, q, n, min(0.48, strength))
    if op == "Te":
        return apply_dephase(rho, X, q, n, min(0.48, strength))
    if op == "Fi":
        return apply_unitary(rho, unitary(X, 1.6 * strength, q, n))
    if op == "Fe":
        return apply_unitary(rho, unitary(Z, 1.8 * strength, q, n))
    raise ValueError(op)


def holonomy(theta_a: float, theta_b: float) -> float:
    ux = math.cos(theta_a / 2.0) * I2 - 1j * math.sin(theta_a / 2.0) * X
    uz = math.cos(theta_b / 2.0) * I2 - 1j * math.sin(theta_b / 2.0) * Z
    return float(torch.linalg.matrix_norm(ux @ uz @ dagger(ux) @ dagger(uz) - I2).item() / math.sqrt(2.0))


def run_variant(engine: str, n: int, seed: int, mode: str) -> dict[str, Any]:
    rho = plus_carrier(n) if mode == "carrier_erased" else product_carrier(engine, n, seed)
    left = list(range(max(1, n // 2)))
    right = list(range(max(1, n // 2), n))
    shell_balance = sum(z_expectation(rho, q, n) for q in left) - sum(z_expectation(rho, q, n) for q in right)
    geometry_theta = 0.09 + 0.09 * math.tanh(abs(shell_balance))

    rho_geom = rho
    if mode != "product_geometry":
        for q in range(n):
            rho_geom = apply_unitary(rho_geom, zz_unitary(geometry_theta, q, (q + 1) % n, n))
    geometry_mi = mutual_information(rho_geom, left, right, n)
    operator_strength = 0.055 + 0.055 * math.tanh(geometry_mi + abs(shell_balance) / max(1, n))
    if mode == "detached_operator":
        operator_strength = 0.055

    tokens = ROWS[engine]
    ordered = list(tokens)
    if mode == "order_erased":
        ordered = sorted(tokens)
    rho_ordered = rho_geom
    for idx, token in enumerate(ordered):
        rho_ordered = apply_token(rho_ordered, token, idx % n, n, operator_strength)
    rho_reversed = rho_geom
    for idx, token in enumerate(reversed(ordered)):
        rho_reversed = apply_token(rho_reversed, token, idx % n, n, operator_strength)
    order_gap = float(torch.linalg.matrix_norm(rho_ordered - rho_reversed).item())
    closure_theta = 0.035 + 0.085 * math.tanh(order_gap)
    if mode == "closure_bypass":
        closure_theta = 0.035

    rho_final = apply_unitary(rho_ordered, zz_unitary(closure_theta, 0, n - 1, n))
    final_mi = mutual_information(rho_final, left, right, n)
    final_current = abs(final_mi - geometry_mi) + 0.30 * order_gap + 0.25 * holonomy(geometry_theta, closure_theta)
    return {
        "engine": engine,
        "qubits": n,
        "seed": seed,
        "mode": mode,
        "shell_balance": shell_balance,
        "geometry_theta": geometry_theta,
        "geometry_mi": geometry_mi,
        "operator_strength": operator_strength,
        "order_gap": order_gap,
        "closure_theta": closure_theta,
        "final_mi": final_mi,
        "final_current": final_current,
    }


def evaluate_case(engine: str, n: int, seed: int) -> dict[str, Any]:
    modes = ["live", "carrier_erased", "product_geometry", "detached_operator", "order_erased", "closure_bypass"]
    rows = {mode: run_variant(engine, n, seed, mode) for mode in modes}
    live = rows["live"]
    best_control = max((row for key, row in rows.items() if key != "live"), key=lambda row: row["final_current"])
    deltas = {
        "carrier_to_geometry_delta": abs(live["geometry_theta"] - rows["carrier_erased"]["geometry_theta"]),
        "geometry_to_operator_delta": abs(live["operator_strength"] - rows["product_geometry"]["operator_strength"]),
        "operator_to_closure_delta": abs(live["closure_theta"] - rows["order_erased"]["closure_theta"]),
        "closure_to_current_delta": abs(live["final_current"] - rows["closure_bypass"]["final_current"]),
        "live_minus_best_control": live["final_current"] - best_control["final_current"],
    }
    dependency_pass = (
        deltas["carrier_to_geometry_delta"] > 0.015
        and deltas["geometry_to_operator_delta"] > 0.002
        and deltas["operator_to_closure_delta"] > 0.0005
        and deltas["closure_to_current_delta"] > 0.0005
    )
    candidate_survived = dependency_pass and deltas["live_minus_best_control"] > 0.002
    return {
        "engine": engine,
        "qubits": n,
        "seed": seed,
        "dependency_pass": bool(dependency_pass),
        "candidate_survived": bool(candidate_survived),
        "best_control_mode": best_control["mode"],
        "deltas": deltas,
        "live": live,
        "controls": {key: value for key, value in rows.items() if key != "live"},
    }


def torch_section() -> dict[str, Any]:
    cases = [evaluate_case(engine, n, seed) for engine in ("E1", "E2") for n in (3, 8) for seed in range(1, 7)]
    dependency_count = sum(1 for row in cases if row["dependency_pass"])
    survival_count = sum(1 for row in cases if row["candidate_survived"])
    dependency_rate = dependency_count / len(cases)
    survival_rate = survival_count / len(cases)
    candidate_status = "layer_dependency_flux_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_layer_dependency_flux"
    return {
        "name": "finite_layer_dependency_flux_ablation_fixture",
        "passed": True,
        "candidate_status": candidate_status,
        "candidate_survived": candidate_status == "layer_dependency_flux_survived_fixture",
        "case_count": len(cases),
        "dependency_count": dependency_count,
        "dependency_rate": dependency_rate,
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "cases_preview": cases[:8],
        "summary": {
            "min_live_minus_best_control": min(row["deltas"]["live_minus_best_control"] for row in cases),
            "max_live_minus_best_control": max(row["deltas"]["live_minus_best_control"] for row in cases),
            "mean_live_minus_best_control": sum(row["deltas"]["live_minus_best_control"] for row in cases) / len(cases),
        },
        "claim": "every layer dependency is ablated before any flux-like candidate can be considered load-bearing",
    }


def z3_section() -> dict[str, Any]:
    dependencies = z3.Int("dependencies")
    promoted = z3.Bool("promoted")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(dependencies == 4, z3.Not(promoted), z3.Not(physics))
    missing = z3.Solver()
    missing.add(solver.assertions())
    missing.add(dependencies < 4)
    promo = z3.Solver()
    promo.add(solver.assertions())
    promo.add(z3.Or(promoted, physics))
    return {
        "name": "z3_dependency_nonpromotion_fence",
        "passed": missing.check() == z3.unsat and promo.check() == z3.unsat,
        "missing_dependency_unsat": missing.check() == z3.unsat,
        "promotion_unsat": promo.check() == z3.unsat,
        "claim": "four numeric dependency checks still cannot promote flux or physics",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependency = torch_section()
    antipromotion = z3_section()
    sections = [dependency, antipromotion]
    graveyard_companions = {
        "candidate_status_recorded": {
            "pass": dependency["candidate_status"] in {"layer_dependency_flux_survived_fixture", "open_or_nonrobust_layer_dependency_flux"},
            "candidate_status": dependency["candidate_status"],
        },
        "dependency_ablations_present": {"pass": dependency["case_count"] == 24, "case_count": dependency["case_count"]},
        "receipt_pass_not_scientific_success": {
            "pass": True,
            "meaning": "all_pass validates receipt contract; candidate_survived carries scientific status",
        },
        "final_claims_rejected": {"pass": antipromotion["promotion_unsat"]},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_flux_not_admitted": {"pass": True, "value": False},
        "axis0_xi_not_admitted": {"pass": True, "value": False},
        "physics_unification_not_admitted": {"pass": True, "value": False},
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
        "candidate_status": dependency["candidate_status"],
        "candidate_survived": dependency["candidate_survived"],
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "case_count": dependency["case_count"],
            "dependency_count": dependency["dependency_count"],
            "dependency_rate": dependency["dependency_rate"],
            "survival_count": dependency["survival_count"],
            "survival_rate": dependency["survival_rate"],
            **dependency["summary"],
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["MPS_process_tensor_scaling", "gauge_invariant_current_through_cut", "16_qubit_sparse_stack"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 layer-dependency ablation of a bounded flux fixture, not a v4 flux proof.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "replace dense final current with a gauge-invariant current-through-cut observable",
            "run process-tensor or MPS version at 16 qubits",
            "require held-out parameter survival before any flux promotion",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": dependency["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

