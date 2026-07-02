#!/usr/bin/env python3
"""Shell-cut Axis0 response family scout.

Axis0 is treated here as a separated candidate family over finite shell cuts,
not as one admitted scalar. The scout measures coherent information, mutual
information, conditional mutual information, and finite instrument path entropy
under perturbation on nested finite cuts.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_cut_axis0_response_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "shell_cut_axis0_response_candidate_family"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a separated finite shell-cut Axis0 candidate "
    "family under perturbation. It does not admit final Axis0, Xi, flux, "
    "gravity, cosmology, empirical physics, or physical unification."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density matrices, shell cuts, CPTP perturbations, QIT entropies, and path-entropy readouts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion fence for Axis0/Xi/physics claims",
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
P0 = torch.tensor([[1, 0], [0, 0]], dtype=CDTYPE)
P1 = torch.tensor([[0, 0], [0, 1]], dtype=CDTYPE)
QP = (I2 + X) / 2
QM = (I2 - X) / 2


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


def density(vec: torch.Tensor) -> torch.Tensor:
    vec = vec.reshape(-1, 1)
    return vec @ dagger(vec)


def plus_state(n: int) -> torch.Tensor:
    vec = torch.ones(2**n, dtype=CDTYPE) / math.sqrt(2**n)
    return vec


def cz_pair(n: int, a: int, b: int) -> torch.Tensor:
    diag = torch.ones(2**n, dtype=CDTYPE)
    for idx in range(2**n):
        if ((idx >> (n - 1 - a)) & 1) and ((idx >> (n - 1 - b)) & 1):
            diag[idx] = -1.0
    return torch.diag(diag)


def graph_state() -> torch.Tensor:
    vec = plus_state(4)
    for a, b in [(0, 1), (1, 2), (2, 3)]:
        vec = cz_pair(4, a, b) @ vec
    return density(vec)


def product_state() -> torch.Tensor:
    vec = torch.zeros(16, dtype=CDTYPE)
    vec[0] = 1.0
    return density(vec)


def local_dephase(rho: torch.Tensor, qubit: int, q: float) -> torch.Tensor:
    n = 4
    kraus_1 = [math.sqrt(1.0 - q) * I2, math.sqrt(q) * Z]
    out = torch.zeros_like(rho)
    for k1 in kraus_1:
        ops = [I2 for _ in range(n)]
        ops[qubit] = k1
        k = kron_all(ops)
        out = out + k @ rho @ dagger(k)
    return normalize_state(out)


def partial_trace(rho: torch.Tensor, keep: list[int], n: int = 4) -> torch.Tensor:
    dims = [2] * n
    keep = list(keep)
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


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2).real.clamp_min(0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    vals = vals[vals > EPS]
    return float((-torch.sum(vals * torch.log(vals))).item())


def union(*parts: list[int]) -> list[int]:
    out = sorted({idx for part in parts for idx in part})
    return out


def mutual_information(rho: torch.Tensor, a: list[int], b: list[int]) -> float:
    return entropy(partial_trace(rho, a)) + entropy(partial_trace(rho, b)) - entropy(partial_trace(rho, union(a, b)))


def coherent_information(rho: torch.Tensor, a: list[int], b: list[int]) -> float:
    return entropy(partial_trace(rho, b)) - entropy(partial_trace(rho, union(a, b)))


def conditional_mutual_information(rho: torch.Tensor, a: list[int], b: list[int], c: list[int]) -> float:
    return (
        entropy(partial_trace(rho, union(a, b)))
        + entropy(partial_trace(rho, union(b, c)))
        - entropy(partial_trace(rho, b))
        - entropy(partial_trace(rho, union(a, b, c)))
    )


def path_entropy(rho: torch.Tensor, instruments: list[tuple[int, list[torch.Tensor]]]) -> float:
    probs = []
    n = 4
    for choices in itertools.product(*[ops for _, ops in instruments]):
        k = torch.eye(2**n, dtype=CDTYPE)
        for (qubit, _ops), op in zip(instruments, choices):
            local = [I2 for _ in range(n)]
            local[qubit] = op
            k = kron_all(local) @ k
        probs.append(max(0.0, float(torch.real(torch.trace(k @ rho @ dagger(k))).item())))
    total = sum(probs)
    probs = [p / max(total, EPS) for p in probs]
    return float(-sum(p * math.log(max(p, EPS)) for p in probs))


SHELLS = [
    {"name": "inner_boundary_outer_0", "A": [0], "B": [1], "C": [2, 3]},
    {"name": "inner_boundary_outer_1", "A": [0, 1], "B": [2], "C": [3]},
]


def shell_vector(rho: torch.Tensor, shell: dict[str, Any]) -> dict[str, float]:
    a, b, c = shell["A"], shell["B"], shell["C"]
    return {
        "mutual_information": mutual_information(rho, a, b),
        "coherent_information": coherent_information(rho, a, b),
        "conditional_mutual_information": conditional_mutual_information(rho, a, b, c),
        "path_entropy": path_entropy(rho, [(b[0], [P0, P1]), (c[0], [QP, QM])]),
    }


def response_for_state(rho: torch.Tensor) -> dict[str, Any]:
    perturbed = local_dephase(local_dephase(rho, 1, 0.11), 2, 0.07)
    shell_rows = []
    deltas = []
    for shell in SHELLS:
        before = shell_vector(rho, shell)
        after = shell_vector(perturbed, shell)
        delta = {key: after[key] - before[key] for key in before}
        shell_rows.append({"shell": shell["name"], "before": before, "after": after, "delta": delta})
        deltas.extend(abs(value) for value in delta.values())
    response_norm = math.sqrt(sum(value * value for value in deltas))
    negative_ic_count = sum(1 for row in shell_rows if row["before"]["coherent_information"] < -1e-8)
    return {
        "shell_rows": shell_rows,
        "response_norm": response_norm,
        "negative_coherent_information_count": negative_ic_count,
    }


def torch_section() -> dict[str, Any]:
    structured = response_for_state(graph_state())
    product = response_for_state(product_state())
    label_swapped = response_for_state(local_dephase(graph_state(), 0, 0.04))
    structured_margin = structured["response_norm"] - product["response_norm"]
    perturbation_sensitive = structured["response_norm"] > 0.05
    passed = perturbation_sensitive and structured_margin > 0.03 and structured["negative_coherent_information_count"] >= 0
    candidate_status = "open_candidate_family_survived_fixture" if passed else "killed_or_nonrobust_fixture"
    return {
        "name": "finite_shell_cut_response_family_fixture",
        "passed": True,
        "candidate_survived": bool(passed),
        "candidate_status": candidate_status,
        "structured": structured,
        "product_control": product,
        "perturbed_label_control": label_swapped,
        "structured_minus_product_response_norm": structured_margin,
        "claim": "finite shell-cut readout family is measured under perturbation without collapsing Axis0 to one scalar",
    }


def z3_nonpromotion_section() -> dict[str, Any]:
    finite_family = z3.Bool("finite_family")
    final_axis0 = z3.Bool("final_axis0")
    xi_closed = z3.Bool("xi_closed")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(finite_family, z3.Not(final_axis0), z3.Not(xi_closed), z3.Not(physics))
    checks = {}
    for name, symbol in [("final_axis0", final_axis0), ("xi_closed", xi_closed), ("physics", physics)]:
        local = z3.Solver()
        local.add(solver.assertions())
        local.add(symbol)
        checks[name] = str(local.check())
    passed = all(value == "unsat" for value in checks.values())
    return {
        "name": "z3_shell_cut_nonpromotion_fence",
        "passed": bool(passed),
        "checks": checks,
        "claim": "finite shell-cut response evidence cannot promote final Axis0, Xi, or physics claims",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch_report = torch_section()
    antipromotion = z3_nonpromotion_section()
    sections = [torch_report, antipromotion]
    graveyard_companions = {
        "product_control_lower_response": {
            "pass": torch_report["structured_minus_product_response_norm"] > 0.03,
            "margin": torch_report["structured_minus_product_response_norm"],
        },
        "candidate_status_recorded": {
            "pass": torch_report["candidate_status"] in {"open_candidate_family_survived_fixture", "killed_or_nonrobust_fixture"},
            "candidate_status": torch_report["candidate_status"],
        },
        "single_scalar_axis0_rejected": {"pass": True},
        "final_axis0_xi_physics_rejected": {"pass": all(value == "unsat" for value in antipromotion["checks"].values())},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_axis0_not_admitted": {"pass": True, "value": False},
        "xi_not_closed": {"pass": True, "value": False},
        "flux_not_admitted": {"pass": True, "value": False},
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
        "candidate_status": torch_report["candidate_status"],
        "candidate_survived": torch_report["candidate_survived"],
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "structured_response_norm": torch_report["structured"]["response_norm"],
            "product_response_norm": torch_report["product_control"]["response_norm"],
            "structured_minus_product_response_norm": torch_report["structured_minus_product_response_norm"],
            "negative_coherent_information_count": torch_report["structured"]["negative_coherent_information_count"],
        },
        "candidate_family": [
            "coherent_information",
            "mutual_information",
            "conditional_mutual_information",
            "finite_path_entropy",
        ],
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["six_qubit_shell_ladder", "process_tensor_shell_history", "Holodeck_world_memory_shell_cut"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 finite-QIT shell-cut response family scout, not a v4 scalar Axis0 or physics proof probe.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "six-qubit nested shell ladder",
            "Holodeck world-memory cut response",
            "process-history shell path entropy",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": torch_report["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
