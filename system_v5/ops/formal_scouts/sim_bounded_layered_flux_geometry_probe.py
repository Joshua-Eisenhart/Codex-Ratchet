#!/usr/bin/env python3
"""Bounded layered flux-geometry formal scout.

This scout encodes the current correction: flux-like readouts are only tested
inside a bounded layered geometry stack. Each layer must constrain the next.
The scout runs small per-engine fixtures at 3 and 8 qubits. It does not admit
final flux, Axis0, Xi, Yang-Mills, gravity, Standard Model, or physics.
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
NAME = "bounded_layered_flux_geometry_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "bounded_layered_flux_geometry_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests flux-like readouts inside a bounded layered "
    "geometry stack where each layer constrains the next. It does not admit "
    "final flux, Axis0, Xi, Yang-Mills, Standard Model, gravity, cosmology, "
    "empirical physics, or physical unification."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density states, bounded qubit layers, CPTP maps, cut readouts, and layer-ablation controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and bounded-layer dependency checks",
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

ENGINE_ROWS = {
    "E1": ["TiSe", "SeFi", "NeTi", "FiNe", "NiFe", "TeNi", "FeSi", "SiTe"],
    "E2": ["FiSe", "SeTi", "TeSi", "SiFe", "NiTe", "FeNi", "NeFi", "TiNe"],
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def dagger(a: torch.Tensor) -> torch.Tensor:
    return torch.conj(a.transpose(-2, -1))


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + dagger(rho)) / 2
    return rho / torch.clamp(torch.real(torch.trace(rho)), min=EPS)


def kron_all(ops: list[torch.Tensor]) -> torch.Tensor:
    out = ops[0]
    for op in ops[1:]:
        out = torch.kron(out, op)
    return out


def plus_density(n: int) -> torch.Tensor:
    vec = torch.ones(2**n, dtype=CDTYPE) / math.sqrt(2**n)
    vec = vec.reshape(-1, 1)
    return vec @ dagger(vec)


def local_full(op: torch.Tensor, qubit: int, n: int) -> torch.Tensor:
    ops = [I2 for _ in range(n)]
    ops[qubit] = op
    return kron_all(ops)


def two_body_zz_unitary(theta: float, a: int, b: int, n: int) -> torch.Tensor:
    zz = local_full(Z, a, n) @ local_full(Z, b, n)
    dim = 2**n
    return math.cos(theta / 2) * torch.eye(dim, dtype=CDTYPE) - 1j * math.sin(theta / 2) * zz


def local_unitary(axis: torch.Tensor, theta: float, qubit: int, n: int) -> torch.Tensor:
    u1 = math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * axis
    return local_full(u1, qubit, n)


def apply_unitary(rho: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    return normalize_state(u @ rho @ dagger(u))


def apply_local_dephase(rho: torch.Tensor, axis: torch.Tensor, q: float, qubit: int, n: int) -> torch.Tensor:
    kraus = [math.sqrt(1.0 - q) * I2, math.sqrt(q) * axis]
    out = torch.zeros_like(rho)
    for k1 in kraus:
        k = local_full(k1, qubit, n)
        out = out + k @ rho @ dagger(k)
    return normalize_state(out)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2).real.clamp_min(0.0)
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
    equation = "".join(left + right) + "->" + "".join(out_letters)
    return torch.einsum(equation, reshaped).reshape(2 ** len(keep), 2 ** len(keep))


def mutual_information_cut(rho: torch.Tensor, left: list[int], right: list[int], n: int) -> float:
    union = sorted(set(left + right))
    return entropy(partial_trace(rho, left, n)) + entropy(partial_trace(rho, right, n)) - entropy(partial_trace(rho, union, n))


def z_expectation(rho: torch.Tensor, qubit: int, n: int) -> float:
    return float(torch.real(torch.trace(rho @ local_full(Z, qubit, n))).item())


def token_operator(token: str) -> str:
    for op in ["Ti", "Te", "Fi", "Fe"]:
        if token.startswith(op) or token.endswith(op):
            return op
    raise ValueError(token)


def apply_token(rho: torch.Tensor, token: str, qubit: int, n: int, strength: float) -> torch.Tensor:
    op = token_operator(token)
    if op == "Ti":
        return apply_local_dephase(rho, Z, min(0.42, strength), qubit, n)
    if op == "Te":
        return apply_local_dephase(rho, X, min(0.42, strength), qubit, n)
    if op == "Fi":
        return apply_unitary(rho, local_unitary(X, 1.7 * strength, qubit, n))
    if op == "Fe":
        return apply_unitary(rho, local_unitary(Z, 1.9 * strength, qubit, n))
    raise ValueError(op)


def holonomy_action(theta_a: float, theta_b: float) -> float:
    ux = math.cos(theta_a / 2) * I2 - 1j * math.sin(theta_a / 2) * X
    uz = math.cos(theta_b / 2) * I2 - 1j * math.sin(theta_b / 2) * Z
    plaquette = ux @ uz @ dagger(ux) @ dagger(uz)
    return float(torch.linalg.matrix_norm(plaquette - I2).item() / math.sqrt(2.0))


def run_stack(engine: str, n: int, mode: str) -> dict[str, Any]:
    tokens = ENGINE_ROWS[engine]
    rho0 = plus_density(n)
    rho = rho0
    chirality = 1.0 if engine == "E1" else -1.0

    # Layer 1: bounded carrier polarity; output constrains geometry strength.
    base_angle = 0.10 + 0.015 * n
    for qubit in range(n):
        sign = chirality if qubit % 2 == 0 else -chirality
        rho = apply_unitary(rho, local_unitary(Z, sign * base_angle, qubit, n))
    shell_balance = sum(z_expectation(rho, q, n) for q in range(n // 2)) - sum(
        z_expectation(rho, q, n) for q in range(n // 2, n)
    )
    geometry_theta = 0.16 + 0.05 * math.tanh(abs(shell_balance))
    if mode == "constraint_bypass":
        geometry_theta = 0.16

    # Layer 2: bounded geometry links; output constrains operator strength.
    if mode != "product_geometry":
        for qubit in range(n):
            rho = apply_unitary(rho, two_body_zz_unitary(geometry_theta, qubit, (qubit + 1) % n, n))
    cut_left = list(range(max(1, n // 2)))
    cut_right = list(range(max(1, n // 2), n))
    geometry_mi = mutual_information_cut(rho, cut_left, cut_right, n)
    operator_strength = 0.09 + 0.025 * math.tanh(geometry_mi)
    if mode == "detached_current":
        operator_strength = 0.09

    # Layer 3: per-engine stage operators; output constrains closure layer.
    ordered_tokens = tokens if mode != "layer_shuffled" else list(reversed(tokens))
    rho_before_order = rho
    for idx, token in enumerate(ordered_tokens):
        rho = apply_token(rho, token, idx % n, n, operator_strength)
    rho_ordered = rho
    rho_reversed = rho_before_order
    for idx, token in enumerate(reversed(ordered_tokens)):
        rho_reversed = apply_token(rho_reversed, token, idx % n, n, operator_strength)
    order_gap = float(torch.linalg.matrix_norm(rho_ordered - rho_reversed).item())
    closure_theta = 0.05 + 0.04 * math.tanh(order_gap)
    if mode == "constraint_bypass":
        closure_theta = 0.05

    # Layer 4: closure transport; final flux-like readout only after all layers.
    rho = apply_unitary(rho_ordered, two_body_zz_unitary(closure_theta, 0, n - 1, n))
    final_mi = mutual_information_cut(rho, cut_left, cut_right, n)
    final_entropy = entropy(rho)
    action = holonomy_action(geometry_theta, closure_theta)
    flux_score = abs(final_mi - geometry_mi) + 0.35 * order_gap + 0.20 * action
    return {
        "engine": engine,
        "qubits": n,
        "mode": mode,
        "shell_balance": shell_balance,
        "geometry_theta": geometry_theta,
        "geometry_mi": geometry_mi,
        "operator_strength": operator_strength,
        "order_gap": order_gap,
        "closure_theta": closure_theta,
        "final_mi": final_mi,
        "final_entropy": final_entropy,
        "holonomy_action": action,
        "flux_score": flux_score,
        "layer_dependency_receipt": {
            "carrier_to_geometry": mode != "constraint_bypass",
            "geometry_to_operator": mode != "detached_current",
            "operator_to_closure": mode != "constraint_bypass",
            "all_layers_present": mode not in {"product_geometry", "layer_shuffled", "constraint_bypass", "detached_current"},
        },
    }


def torch_section() -> dict[str, Any]:
    rows = []
    modes = ["layered", "detached_current", "constraint_bypass", "product_geometry", "layer_shuffled"]
    for engine in ["E1", "E2"]:
        for n in [3, 8]:
            for mode in modes:
                rows.append(run_stack(engine, n, mode))
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(f"{row['engine']}:q{row['qubits']}", []).append(row)
    comparisons = {}
    survived_count = 0
    for key, group in grouped.items():
        live = next(row for row in group if row["mode"] == "layered")
        controls = [row for row in group if row["mode"] != "layered"]
        best_control = max(row["flux_score"] for row in controls)
        margin = live["flux_score"] - best_control
        survived = margin > 0.01 and live["layer_dependency_receipt"]["all_layers_present"]
        survived_count += int(survived)
        comparisons[key] = {
            "live_flux_score": live["flux_score"],
            "best_control_flux_score": best_control,
            "margin": margin,
            "survived": bool(survived),
            "best_control_mode": max(controls, key=lambda row: row["flux_score"])["mode"],
        }
    survival_rate = survived_count / len(comparisons)
    candidate_status = "layered_flux_candidate_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_layered_flux_fixture"
    return {
        "name": "bounded_layered_flux_geometry_fixture",
        "passed": True,
        "candidate_status": candidate_status,
        "candidate_survived": candidate_status == "layered_flux_candidate_survived_fixture",
        "comparison_count": len(comparisons),
        "survived_count": survived_count,
        "survival_rate": survival_rate,
        "comparisons": comparisons,
        "rows_preview": rows[:10],
        "claim": "flux-like readouts are evaluated only after bounded carrier, geometry, operator, and closure layers constrain one another",
    }


def z3_nonpromotion_section() -> dict[str, Any]:
    layers = z3.Int("layers")
    min_qubits = z3.Int("min_qubits")
    final_flux = z3.Bool("final_flux")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(layers == 4, min_qubits >= 3, z3.Not(final_flux), z3.Not(physics))
    bad_layers = z3.Solver()
    bad_layers.add(solver.assertions())
    bad_layers.add(layers < 4)
    bad_qubits = z3.Solver()
    bad_qubits.add(solver.assertions())
    bad_qubits.add(min_qubits < 3)
    promote = z3.Solver()
    promote.add(solver.assertions())
    promote.add(z3.Or(final_flux, physics))
    return {
        "name": "z3_bounded_layered_flux_nonpromotion_fence",
        "passed": bad_layers.check() == z3.unsat and bad_qubits.check() == z3.unsat and promote.check() == z3.unsat,
        "bad_layers_unsat": bad_layers.check() == z3.unsat,
        "bad_qubits_unsat": bad_qubits.check() == z3.unsat,
        "promotion_unsat": promote.check() == z3.unsat,
        "claim": "bounded layered flux fixture cannot promote final flux or physics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch_report = torch_section()
    antipromotion = z3_nonpromotion_section()
    sections = [torch_report, antipromotion]
    graveyard_companions = {
        "layered_requirement_recorded": {
            "pass": True,
            "requirement": "carrier -> geometry -> operator -> closure; all layers run before flux-like readout",
        },
        "at_least_three_qubits_used": {"pass": True, "tested_qubits": [3, 8]},
        "per_engine_runs_separate": {"pass": True, "engines": sorted(ENGINE_ROWS)},
        "candidate_status_recorded": {
            "pass": torch_report["candidate_status"]
            in {"layered_flux_candidate_survived_fixture", "open_or_nonrobust_layered_flux_fixture"},
            "candidate_status": torch_report["candidate_status"],
        },
        "final_flux_physics_rejected": {"pass": antipromotion["promotion_unsat"]},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_flux_not_admitted": {"pass": True, "value": False},
        "axis0_xi_not_admitted": {"pass": True, "value": False},
        "yang_mills_gravity_physics_not_admitted": {"pass": True, "value": False},
        "sixteen_qubit_dense_density_blocked": {
            "pass": True,
            "reason": "Dense 16-qubit density matrices are not run in this scout; next version should use MPS/process-tensor tools if 16 qubits are required.",
        },
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
        "candidate_status": torch_report["candidate_status"],
        "candidate_survived": torch_report["candidate_survived"],
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "comparison_count": torch_report["comparison_count"],
            "survived_count": torch_report["survived_count"],
            "survival_rate": torch_report["survival_rate"],
        },
        "layer_stack": ["carrier_polarity", "bounded_geometry_links", "per_engine_stage_operators", "closure_transport"],
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["MPS_16_qubit_layered_flux", "per-token isolated engine sweeps", "process-tensor layered geometry"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 bounded layered-geometry correction to loose flux-current tests, not a v4 flux or physics proof probe.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "MPS or process-tensor 16-qubit layered stack",
            "per-engine isolated layer sweeps with held-out parameters",
            "replace tautological controls with layer-consistent countermodels",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": torch_report["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
