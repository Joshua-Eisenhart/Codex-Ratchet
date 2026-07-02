#!/usr/bin/env python3
"""Runtime-priority QIT work suite formal scout.

This keeps getting the operational engines working as the primary task while
running the next three requested probes:

1. 8-qubit shell-cut response with finite process-history path entropy.
2. runtime-row current-through-cut flux rescue/falsifier.
3. two-agent QIT selector game over minimax/maximax/maximin/minimin.

The script is a formal scout only. Receipt success is not candidate survival.
"""

from __future__ import annotations

import itertools
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
from canonical_qit_engine_specs import get_chart_token_spec, get_schedule  # noqa: E402


RESULT_DIR = ROOT / "results"
NAME = "runtime_priority_work_suite_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "runtime_priority_qit_work_suite"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: consumes current runtime row schedules for shell-cut, "
    "flux-current, and two-agent selector probes. It does not admit final "
    "engines, Axis0, Xi, flux, IGT/game theory, Holodeck, cognition, "
    "psychology, gravity, Standard Model, Yang-Mills, cosmology, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density states, runtime row channels, shell cuts, current-through-cut readouts, and selector controls",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive current runtime schedule and chart-token source for both engine rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and finite-cardinality checks",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
}

CDTYPE = torch.complex128
RDTYPE = torch.float64
EPS = 1e-10
I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
P0 = torch.tensor([[1, 0], [0, 0]], dtype=CDTYPE)
P1 = torch.tensor([[0, 0], [0, 1]], dtype=CDTYPE)
QP = 0.5 * (I2 + X)
QM = 0.5 * (I2 - X)


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


def kron_all(ops: list[torch.Tensor]) -> torch.Tensor:
    out = ops[0]
    for op in ops[1:]:
        out = torch.kron(out, op)
    return out


LOCAL_CACHE: dict[tuple[int, int, str], torch.Tensor] = {}


def op_key(op: torch.Tensor) -> str | None:
    if torch.allclose(op, I2):
        return "I"
    if torch.allclose(op, X):
        return "X"
    if torch.allclose(op, Y):
        return "Y"
    if torch.allclose(op, Z):
        return "Z"
    if torch.allclose(op, P0):
        return "P0"
    if torch.allclose(op, P1):
        return "P1"
    if torch.allclose(op, QP):
        return "QP"
    if torch.allclose(op, QM):
        return "QM"
    return None


def local_full(op: torch.Tensor, qubit: int, n: int) -> torch.Tensor:
    label = op_key(op)
    key = (n, qubit, label) if label is not None else None
    if key is not None:
        cached = LOCAL_CACHE.get(key)
        if cached is not None:
            return cached
    ops = [I2 for _ in range(n)]
    ops[qubit] = op
    out = kron_all(ops)
    if key is not None:
        LOCAL_CACHE[key] = out
    return out


def plus_state(n: int) -> torch.Tensor:
    vec = torch.ones(2**n, dtype=CDTYPE) / math.sqrt(2**n)
    return vec[:, None] @ dagger(vec[:, None])


def zero_state(n: int) -> torch.Tensor:
    vec = torch.zeros(2**n, dtype=CDTYPE)
    vec[0] = 1.0
    return vec[:, None] @ dagger(vec[:, None])


def cz_pair(n: int, a: int, b: int) -> torch.Tensor:
    diag = torch.ones(2**n, dtype=CDTYPE)
    for idx in range(2**n):
        if ((idx >> (n - 1 - a)) & 1) and ((idx >> (n - 1 - b)) & 1):
            diag[idx] = -1.0
    return torch.diag(diag)


def graph_state(n: int, seed: int) -> torch.Tensor:
    rho = plus_state(n)
    if seed % 3 == 0:
        edges = [(i, i + 1) for i in range(n - 1)]
    elif seed % 3 == 1:
        edges = [(i, (i + 1) % n) for i in range(n)]
    else:
        edges = [(0, i) for i in range(1, n)] + [(2, 5), (3, 7)] if n >= 8 else [(0, i) for i in range(1, n)]
    u = torch.eye(2**n, dtype=CDTYPE)
    for a, b in edges:
        u = cz_pair(n, a, b) @ u
    return normalize(u @ rho @ dagger(u))


def unitary_1q(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * axis


def apply_local_unitary(rho: torch.Tensor, axis: torch.Tensor, theta: float, qubit: int, n: int) -> torch.Tensor:
    u = local_full(unitary_1q(axis, theta), qubit, n)
    return normalize(u @ rho @ dagger(u))


def apply_local_dephase(rho: torch.Tensor, axis: torch.Tensor, q: float, qubit: int, n: int) -> torch.Tensor:
    full = local_full(axis, qubit, n)
    return normalize((1.0 - q) * rho + q * full @ rho @ full)


def token_operator(token: str) -> str:
    for op in ("Ti", "Te", "Fi", "Fe"):
        if token.startswith(op) or token.endswith(op):
            return op
    raise ValueError(token)


def apply_token_local(rho: torch.Tensor, token: str, qubit: int, n: int, *, strength: float = 1.0, commuting: bool = False) -> torch.Tensor:
    op = token_operator(token)
    if commuting:
        axis = Z
        if op in {"Ti", "Te"}:
            return apply_local_dephase(rho, axis, 0.18 * strength, qubit, n)
        return apply_local_unitary(rho, axis, 0.23 * strength, qubit, n)
    if op == "Ti":
        return apply_local_dephase(rho, Z, 0.22 * strength, qubit, n)
    if op == "Te":
        return apply_local_dephase(rho, X, 0.20 * strength, qubit, n)
    if op == "Fi":
        return apply_local_unitary(rho, X, 0.31 * strength, qubit, n)
    if op == "Fe":
        return apply_local_unitary(rho, Z, 0.29 * strength, qubit, n)
    raise ValueError(op)


def token_kraus_local(token: str, qubit: int, n: int, *, strength: float = 1.0) -> list[torch.Tensor]:
    op = token_operator(token)
    if op == "Ti":
        q = min(0.42, 0.22 * strength)
        return [math.sqrt(1.0 - q) * torch.eye(2**n, dtype=CDTYPE), math.sqrt(q) * local_full(Z, qubit, n)]
    if op == "Te":
        q = min(0.42, 0.20 * strength)
        return [math.sqrt(1.0 - q) * torch.eye(2**n, dtype=CDTYPE), math.sqrt(q) * local_full(X, qubit, n)]
    axis = X if op == "Fi" else Z
    angle = (0.31 if op == "Fi" else 0.29) * strength
    return [local_full(unitary_1q(axis, angle), qubit, n)]


def runtime_rows(engine_type: int) -> list[dict[str, Any]]:
    rows = []
    for idx, (topology, loop) in enumerate(get_schedule(engine_type)):
        chart = get_chart_token_spec(topology, engine_type, loop)
        rows.append(
            {
                "idx": idx,
                "engine_type": engine_type,
                "engine_label": f"E{engine_type + 1}",
                "topology": topology,
                "loop": loop,
                "token": chart["token"],
                "operator": chart["operator"],
                "precedence": chart["precedence"],
            }
        )
    return rows


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


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize(rho)).real.clamp_min(0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    vals = vals[vals > EPS]
    return float((-torch.sum(vals * torch.log(vals))).item())


def union(*parts: list[int]) -> list[int]:
    return sorted({idx for part in parts for idx in part})


def mutual_information(rho: torch.Tensor, a: list[int], b: list[int], n: int) -> float:
    return entropy(partial_trace(rho, a, n)) + entropy(partial_trace(rho, b, n)) - entropy(partial_trace(rho, union(a, b), n))


def conditional_mutual_information(rho: torch.Tensor, a: list[int], b: list[int], c: list[int], n: int) -> float:
    return (
        entropy(partial_trace(rho, union(a, b), n))
        + entropy(partial_trace(rho, union(b, c), n))
        - entropy(partial_trace(rho, b, n))
        - entropy(partial_trace(rho, union(a, b, c), n))
    )


def path_entropy_for_rows(rho: torch.Tensor, rows: list[dict[str, Any]], n: int) -> float:
    branches = [(1.0, normalize(rho))]
    for row in rows:
        qubit = row["idx"] % n
        new_branches = []
        for weight, state in branches:
            for k in token_kraus_local(row["token"], qubit, n):
                out = k @ state @ dagger(k)
                prob = max(0.0, float(torch.real(torch.trace(out)).item()))
                if prob > EPS:
                    new_branches.append((weight * prob, normalize(out)))
        branches = new_branches
    total = sum(weight for weight, _ in branches)
    probs = [weight / max(total, EPS) for weight, _ in branches]
    return float(-sum(p * math.log(max(p, EPS)) for p in probs))


def run_runtime_density(rho: torch.Tensor, engine_type: int, n: int, *, mode: str = "live") -> torch.Tensor:
    rows = runtime_rows(engine_type)
    if mode == "order_scramble":
        rows = list(reversed(rows))
    for row in rows:
        token = row["token"]
        if mode == "label_erased":
            token = "TiSe" if row["idx"] % 2 == 0 else "FiSe"
        rho = apply_token_local(rho, token, row["idx"] % n, n, strength=1.0, commuting=mode == "commuting")
        if mode != "product_links":
            # A small geometry link after each row; this keeps runtime rows tied
            # to bounded shell structure without claiming a final manifold law.
            a = row["idx"] % n
            b = (a + 1) % n
            zz = local_full(Z, a, n) @ local_full(Z, b, n)
            theta = 0.025 + 0.006 * (row["idx"] + 1)
            u = math.cos(theta / 2.0) * torch.eye(2**n, dtype=CDTYPE) - 1j * math.sin(theta / 2.0) * zz
            rho = normalize(u @ rho @ dagger(u))
    return rho


def shell_process_section() -> dict[str, Any]:
    n = 8
    cases = []
    for engine_type in (0, 1):
        rows = runtime_rows(engine_type)
        for seed in range(1, 7):
            rho0 = graph_state(n, seed)
            live = run_runtime_density(rho0, engine_type, n, mode="live")
            product = run_runtime_density(zero_state(n), engine_type, n, mode="live")
            scrambled = run_runtime_density(rho0, engine_type, n, mode="order_scramble")
            left, boundary, right = [0, 1, 2], [3], [4, 5, 6, 7]
            live_cmi = conditional_mutual_information(live, left, boundary, right, n)
            product_cmi = conditional_mutual_information(product, left, boundary, right, n)
            scrambled_cmi = conditional_mutual_information(scrambled, left, boundary, right, n)
            path_h = path_entropy_for_rows(rho0, rows, n)
            margin = live_cmi - max(product_cmi, scrambled_cmi)
            survived = margin > 0.015 and path_h > 0.1
            cases.append(
                {
                    "engine_label": f"E{engine_type + 1}",
                    "seed": seed,
                    "live_cmi": live_cmi,
                    "product_cmi": product_cmi,
                    "scrambled_cmi": scrambled_cmi,
                    "path_entropy": path_h,
                    "margin": margin,
                    "survived": bool(survived),
                }
            )
    survival_count = sum(1 for row in cases if row["survived"])
    survival_rate = survival_count / len(cases)
    return {
        "name": "runtime_shell_cut_process_entropy_fixture",
        "passed": True,
        "candidate_status": "runtime_shell_process_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_runtime_shell_process",
        "candidate_survived": survival_rate >= 0.75,
        "case_count": len(cases),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "mean_margin": sum(row["margin"] for row in cases) / len(cases),
        "mean_path_entropy": sum(row["path_entropy"] for row in cases) / len(cases),
        "cases": cases,
        "claim": "current runtime rows drive an 8-qubit finite shell-cut process-history readout",
    }


def current_through_cut(rho_before: torch.Tensor, rho_after: torch.Tensor, n: int) -> float:
    left = list(range(n // 2))
    right = list(range(n // 2, n))
    delta_mi = mutual_information(rho_after, left, right, n) - mutual_information(rho_before, left, right, n)
    boundary_op = local_full(Z, n // 2 - 1, n) @ local_full(X, n // 2, n)
    comm_gap = float(torch.linalg.matrix_norm(boundary_op @ rho_after - rho_after @ boundary_op).item())
    return abs(delta_mi) + 0.05 * comm_gap


def flux_current_section() -> dict[str, Any]:
    n = 8
    cases = []
    for engine_type in (0, 1):
        for seed in range(1, 7):
            rho0 = graph_state(n, seed)
            rows = runtime_rows(engine_type)
            histories: dict[str, list[float]] = {}
            for mode in ("live", "product_links", "order_scramble", "commuting", "label_erased"):
                rho = rho0
                currents = []
                active_rows = rows if mode != "order_scramble" else list(reversed(rows))
                for row in active_rows:
                    before = rho
                    token = row["token"] if mode != "label_erased" else "TiSe"
                    rho = apply_token_local(rho, token, row["idx"] % n, n, commuting=mode == "commuting")
                    if mode != "product_links":
                        a = row["idx"] % n
                        b = (a + 1) % n
                        zz = local_full(Z, a, n) @ local_full(Z, b, n)
                        theta = 0.03 + 0.005 * row["idx"]
                        u = math.cos(theta / 2.0) * torch.eye(2**n, dtype=CDTYPE) - 1j * math.sin(theta / 2.0) * zz
                        rho = normalize(u @ rho @ dagger(u))
                    currents.append(current_through_cut(before, rho, n))
                histories[mode] = currents
            live_score = sum(histories["live"])
            best_control = max(sum(values) for key, values in histories.items() if key != "live")
            margin = live_score - best_control
            dependency_spread = min(
                abs(live_score - sum(histories["product_links"])),
                abs(live_score - sum(histories["commuting"])),
                abs(live_score - sum(histories["label_erased"])),
            )
            survived = margin > 0.01 and dependency_spread > 0.01
            cases.append(
                {
                    "engine_label": f"E{engine_type + 1}",
                    "seed": seed,
                    "live_current": live_score,
                    "best_control_current": best_control,
                    "margin": margin,
                    "dependency_spread": dependency_spread,
                    "survived": bool(survived),
                    "control_totals": {key: sum(values) for key, values in histories.items()},
                }
            )
    survival_count = sum(1 for row in cases if row["survived"])
    survival_rate = survival_count / len(cases)
    return {
        "name": "runtime_current_through_cut_flux_fixture",
        "passed": True,
        "candidate_status": "runtime_cut_current_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_runtime_cut_current",
        "candidate_survived": survival_rate >= 0.75,
        "case_count": len(cases),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "mean_margin": sum(row["margin"] for row in cases) / len(cases),
        "mean_dependency_spread": sum(row["dependency_spread"] for row in cases) / len(cases),
        "cases": cases,
        "claim": "flux is tested as a current-through-cut readout over current runtime row histories",
    }


def two_agent_initial(seed: int) -> torch.Tensor:
    n = 4
    rho = graph_state(n, seed)
    # Separate memories slightly by local chirality-like rotations.
    rho = apply_local_unitary(rho, X, 0.08 * seed, 0, n)
    rho = apply_local_unitary(rho, Z, -0.06 * seed, 2, n)
    return rho


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize(a) - normalize(b))
    return float(0.5 * torch.sum(torch.abs(vals.real)).item())


def two_agent_payoff(row_a: dict[str, Any], row_b: dict[str, Any], rho0: torch.Tensor, *, mode: str) -> tuple[float, float]:
    n = 4
    token_a = row_a["token"]
    token_b = row_b["token"]
    if mode == "scrambled":
        token_a, token_b = token_b, token_a
    if mode == "label_erased":
        token_a = token_b = "TiSe"
    rho = rho0 if mode != "product_memory" else zero_state(n)
    before = rho
    rho = apply_token_local(rho, token_a, 0, n, commuting=mode == "commuting")
    rho = apply_token_local(rho, token_b, 2, n, commuting=mode == "commuting")
    # Interaction/coupling channel between two characters.
    zz = local_full(Z, 1, n) @ local_full(X, 2, n)
    u = math.cos(0.055) * torch.eye(2**n, dtype=CDTYPE) - 1j * math.sin(0.055) * zz
    rho = normalize(u @ rho @ dagger(u))
    info = mutual_information(rho, [0, 1], [2, 3], n)
    order_gap = float(torch.linalg.matrix_norm(rho - before).item())
    entropy_cost = max(0.0, entropy(rho) - entropy(rho0))
    a_local = partial_trace(rho, [0], n)
    b_local = partial_trace(rho, [2], n)
    a_target = 0.5 * (I2 + (0.35 if row_a["topology"] in {"Ne", "Ni"} else -0.35) * Z)
    b_target = 0.5 * (I2 + (0.35 if row_b["topology"] in {"Ne", "Ni"} else -0.35) * Z)
    utility_a = 0.45 * float(torch.real(torch.trace(a_local @ a_target)).item()) + 0.24 * info + 0.18 * order_gap - 0.13 * entropy_cost
    damage_a = trace_distance(a_local, a_target) + 0.20 * entropy_cost - 0.08 * info
    utility_b = 0.45 * float(torch.real(torch.trace(b_local @ b_target)).item()) + 0.24 * info + 0.18 * order_gap - 0.13 * entropy_cost
    damage_b = trace_distance(b_local, b_target) + 0.20 * entropy_cost - 0.08 * info
    return utility_a - 0.25 * damage_a, utility_b - 0.25 * damage_b


def selector_indices(payoffs: torch.Tensor, damages: torch.Tensor) -> dict[str, int]:
    return {
        "maximax": int(torch.argmax(torch.max(payoffs, dim=1).values).item()),
        "maximin": int(torch.argmax(torch.min(payoffs, dim=1).values).item()),
        "minimax": int(torch.argmin(torch.max(damages, dim=1).values).item()),
        "minimin": int(torch.argmin(torch.min(damages, dim=1).values).item()),
    }


def two_agent_selector_section() -> dict[str, Any]:
    rows = [*runtime_rows(0), *runtime_rows(1)]
    # Keep one row per token while preserving current runtime metadata.
    uniq: dict[str, dict[str, Any]] = {}
    for row in rows:
        uniq.setdefault(row["token"], row)
    rows = list(uniq.values())
    cases = []
    for seed in range(1, 9):
        rho0 = two_agent_initial(seed)
        reports = {}
        for mode in ("live", "commuting", "scrambled", "product_memory", "label_erased"):
            payoff = torch.zeros((len(rows), len(rows)), dtype=RDTYPE)
            damage = torch.zeros_like(payoff)
            for i, row_a in enumerate(rows):
                for j, row_b in enumerate(rows):
                    ua, ub = two_agent_payoff(row_a, row_b, rho0, mode=mode)
                    payoff[i, j] = ua
                    damage[i, j] = -0.5 * (ua + ub)
            selectors = selector_indices(payoff, damage)
            reports[mode] = {
                "selectors": selectors,
                "tokens": {key: rows[idx]["token"] for key, idx in selectors.items()},
                "payoff_range": float((torch.max(payoff) - torch.min(payoff)).item()),
            }
        live_tokens = reports["live"]["tokens"]
        control_changes = {
            mode: sum(1 for key in live_tokens if live_tokens[key] != reports[mode]["tokens"][key])
            for mode in ("commuting", "scrambled", "product_memory", "label_erased")
        }
        minimin_distinct = len({live_tokens["minimin"], live_tokens["minimax"], live_tokens["maximin"], live_tokens["maximax"]}) >= 3
        survived = min(control_changes.values()) >= 2 and minimin_distinct and reports["live"]["payoff_range"] > 0.02
        cases.append(
            {
                "seed": seed,
                "survived": bool(survived),
                "live_tokens": live_tokens,
                "control_changes": control_changes,
                "minimin_distinct": bool(minimin_distinct),
                "live_payoff_range": reports["live"]["payoff_range"],
            }
        )
    survival_count = sum(1 for row in cases if row["survived"])
    survival_rate = survival_count / len(cases)
    return {
        "name": "runtime_two_agent_qit_selector_fixture",
        "passed": True,
        "candidate_status": "runtime_two_agent_selector_survived_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_runtime_two_agent_selector",
        "candidate_survived": survival_rate >= 0.75,
        "case_count": len(cases),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "cases": cases,
        "claim": "two-agent QIT selectors consume current runtime tokens and separate local states/memories",
    }


def z3_section() -> dict[str, Any]:
    probes = z3.Int("probes")
    final_runtime = z3.Bool("final_runtime")
    final_flux = z3.Bool("final_flux")
    final_igt = z3.Bool("final_igt")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(probes == 3, z3.Not(final_runtime), z3.Not(final_flux), z3.Not(final_igt), z3.Not(physics))
    bad = z3.Solver()
    bad.add(solver.assertions())
    bad.add(probes != 3)
    promo = z3.Solver()
    promo.add(solver.assertions())
    promo.add(z3.Or(final_runtime, final_flux, final_igt, physics))
    return {
        "name": "z3_runtime_suite_nonpromotion_fence",
        "passed": bad.check() == z3.unsat and promo.check() == z3.unsat,
        "bad_probe_count_unsat": bad.check() == z3.unsat,
        "promotion_unsat": promo.check() == z3.unsat,
        "claim": "three runtime-priority probes cannot promote final runtime, flux, IGT, or physics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    shell = shell_process_section()
    flux = flux_current_section()
    selectors = two_agent_selector_section()
    antipromotion = z3_section()
    sections = [shell, flux, selectors, antipromotion]
    graveyard_companions = {
        "current_runtime_rows_consumed": {
            "pass": True,
            "row_counts": {"E1": len(runtime_rows(0)), "E2": len(runtime_rows(1))},
        },
        "receipt_pass_not_candidate_survival": {
            "pass": True,
            "meaning": "all_pass validates receipt contract; section candidate_status carries scientific status",
        },
        "three_requested_probes_present": {
            "pass": True,
            "probes": [shell["name"], flux["name"], selectors["name"]],
        },
        "final_claims_rejected": {"pass": antipromotion["promotion_unsat"]},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_runtime_not_admitted": {"pass": True, "value": False},
        "final_axis0_xi_flux_not_admitted": {"pass": True, "value": False},
        "final_igt_holodeck_not_admitted": {"pass": True, "value": False},
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
            "shell_process": shell["candidate_status"],
            "cut_current": flux["candidate_status"],
            "two_agent_selector": selectors["candidate_status"],
        },
        "candidate_survived": {
            "shell_process": shell["candidate_survived"],
            "cut_current": flux["candidate_survived"],
            "two_agent_selector": selectors["candidate_survived"],
        },
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "shell_process_survival_rate": shell["survival_rate"],
            "shell_process_mean_margin": shell["mean_margin"],
            "shell_process_mean_path_entropy": shell["mean_path_entropy"],
            "cut_current_survival_rate": flux["survival_rate"],
            "cut_current_mean_margin": flux["mean_margin"],
            "cut_current_mean_dependency_spread": flux["mean_dependency_spread"],
            "two_agent_selector_survival_rate": selectors["survival_rate"],
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["full EngineCore dense import", "16_qubit_MPS", "population_dynamics", "process_tensor_memory"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 runtime-priority QIT suite; it does not promote legacy v4 Holodeck/IGT/physics probes.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "wire these three sections to EngineCore trajectory receipts",
            "upgrade 8-qubit dense shell/flux sections to MPS before 16 qubits",
            "add two-agent population dynamics only after selector survival improves",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": result["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
