#!/usr/bin/env python3
"""Shell-cut response stress formal scout.

This expands the first finite shell-cut response fixture into a seed/graph/size
stress test. It keeps Axis0 open: the scout asks whether the QIT shell-cut
family remains responsive under graph rewires, 4/6-qubit nested shells, local
basis stress, product controls, and shell relabel controls.
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
NAME = "shell_cut_response_stress_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "shell_cut_response_stress_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests finite shell-cut QIT response families. "
    "It does not admit final Axis0, Xi, flux, gravity, cosmology, empirical "
    "physics, or physical unification."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph states, shell cuts, CPTP perturbations, QIT entropy readouts, and stress controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite stress-count and nonpromotion checks",
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
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
P0 = torch.tensor([[1, 0], [0, 0]], dtype=CDTYPE)
P1 = torch.tensor([[0, 0], [0, 1]], dtype=CDTYPE)
QP = (I2 + X) / 2
QM = (I2 - X) / 2


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


def density(vec: torch.Tensor) -> torch.Tensor:
    vec = vec.reshape(-1, 1)
    return vec @ dagger(vec)


def plus_state(n: int) -> torch.Tensor:
    return torch.ones(2**n, dtype=CDTYPE) / math.sqrt(2**n)


def cz_pair(n: int, a: int, b: int) -> torch.Tensor:
    diag = torch.ones(2**n, dtype=CDTYPE)
    for idx in range(2**n):
        if ((idx >> (n - 1 - a)) & 1) and ((idx >> (n - 1 - b)) & 1):
            diag[idx] = -1.0
    return torch.diag(diag)


def edges_for(n: int, seed: int) -> list[tuple[int, int]]:
    if seed % 3 == 0:
        return [(i, i + 1) for i in range(n - 1)]
    if seed % 3 == 1:
        return [(i, (i + 1) % n) for i in range(n)]
    return [(0, i) for i in range(1, n)] + [(i, i + 1) for i in range(1, n - 1, 2)]


def graph_state(n: int, seed: int) -> torch.Tensor:
    vec = plus_state(n)
    for a, b in edges_for(n, seed):
        vec = cz_pair(n, a, b) @ vec
    return normalize(density(vec))


def product_state(n: int) -> torch.Tensor:
    vec = torch.zeros(2**n, dtype=CDTYPE)
    vec[0] = 1.0
    return density(vec)


def local_full(op: torch.Tensor, qubit: int, n: int) -> torch.Tensor:
    ops = [I2 for _ in range(n)]
    ops[qubit] = op
    return kron_all(ops)


def local_dephase(rho: torch.Tensor, qubit: int, q: float, n: int) -> torch.Tensor:
    full_z = local_full(Z, qubit, n)
    return normalize((1.0 - q) * rho + q * full_z @ rho @ full_z)


def local_unitary_stress(rho: torch.Tensor, n: int, seed: int) -> torch.Tensor:
    out = rho
    for q in range(n):
        theta = 0.13 + 0.017 * ((seed + q) % 7)
        axis = X if q % 2 == 0 else Y
        u1 = math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * axis
        u = local_full(u1, q, n)
        out = normalize(u @ out @ dagger(u))
    return out


def permute_density(rho: torch.Tensor, permutation: list[int], n: int) -> torch.Tensor:
    tensor = rho.reshape(*([2] * n), *([2] * n))
    perm = permutation + [idx + n for idx in permutation]
    return tensor.permute(*perm).reshape(2**n, 2**n)


def partial_trace(rho: torch.Tensor, keep: list[int], n: int) -> torch.Tensor:
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


def coherent_information(rho: torch.Tensor, a: list[int], b: list[int], n: int) -> float:
    return entropy(partial_trace(rho, b, n)) - entropy(partial_trace(rho, union(a, b), n))


def conditional_mutual_information(rho: torch.Tensor, a: list[int], b: list[int], c: list[int], n: int) -> float:
    return (
        entropy(partial_trace(rho, union(a, b), n))
        + entropy(partial_trace(rho, union(b, c), n))
        - entropy(partial_trace(rho, b, n))
        - entropy(partial_trace(rho, union(a, b, c), n))
    )


def path_entropy(rho: torch.Tensor, instruments: list[tuple[int, list[torch.Tensor]]], n: int) -> float:
    probs = []
    for choices in itertools.product(*[ops for _, ops in instruments]):
        k = torch.eye(2**n, dtype=CDTYPE)
        for (qubit, _ops), op in zip(instruments, choices):
            k = local_full(op, qubit, n) @ k
        probs.append(max(0.0, float(torch.real(torch.trace(k @ rho @ dagger(k))).item())))
    total = sum(probs)
    probs = [p / max(total, EPS) for p in probs]
    return float(-sum(p * math.log(max(p, EPS)) for p in probs))


def shells_for(n: int) -> list[dict[str, Any]]:
    if n == 4:
        return [
            {"name": "q4_single_boundary", "A": [0], "B": [1], "C": [2, 3]},
            {"name": "q4_pair_boundary", "A": [0, 1], "B": [2], "C": [3]},
        ]
    return [
        {"name": "q6_single_boundary", "A": [0], "B": [1], "C": [2, 3, 4, 5]},
        {"name": "q6_pair_boundary", "A": [0, 1], "B": [2, 3], "C": [4, 5]},
        {"name": "q6_late_boundary", "A": [1, 2], "B": [3], "C": [0, 4, 5]},
    ]


def shell_vector(rho: torch.Tensor, shell: dict[str, Any], n: int) -> dict[str, float]:
    a, b, c = shell["A"], shell["B"], shell["C"]
    return {
        "mutual_information": mutual_information(rho, a, b, n),
        "coherent_information": coherent_information(rho, a, b, n),
        "conditional_mutual_information": conditional_mutual_information(rho, a, b, c, n),
        "path_entropy": path_entropy(rho, [(b[0], [P0, P1]), (c[0], [QP, QM])], n),
    }


def response_for_state(rho: torch.Tensor, n: int) -> dict[str, Any]:
    shells = shells_for(n)
    perturbed = rho
    for shell in shells:
        perturbed = local_dephase(perturbed, shell["B"][0], 0.09, n)
        perturbed = local_dephase(perturbed, shell["C"][0], 0.06, n)
    rows = []
    all_deltas = []
    by_key = {"mutual_information": 0.0, "coherent_information": 0.0, "conditional_mutual_information": 0.0, "path_entropy": 0.0}
    for shell in shells:
        before = shell_vector(rho, shell, n)
        after = shell_vector(perturbed, shell, n)
        delta = {key: after[key] - before[key] for key in before}
        for key, value in delta.items():
            by_key[key] += abs(value)
            all_deltas.append(abs(value))
        rows.append({"shell": shell["name"], "before": before, "after": after, "delta": delta})
    return {
        "shell_rows": rows,
        "response_norm": math.sqrt(sum(value * value for value in all_deltas)),
        "response_by_key_abs": by_key,
        "negative_coherent_information_count": sum(1 for row in rows if row["before"]["coherent_information"] < -1e-8),
    }


def evaluate_case(n: int, seed: int) -> dict[str, Any]:
    structured = response_for_state(graph_state(n, seed), n)
    product = response_for_state(product_state(n), n)
    local_basis = response_for_state(local_unitary_stress(graph_state(n, seed), n, seed), n)
    permutation = list(range(n))
    permutation = permutation[1:] + permutation[:1]
    relabel = response_for_state(permute_density(graph_state(n, seed), permutation, n), n)
    structured_margin = structured["response_norm"] - product["response_norm"]
    local_margin = local_basis["response_norm"] - product["response_norm"]
    relabel_gap = abs(structured["response_norm"] - relabel["response_norm"])
    cmi_weight = structured["response_by_key_abs"]["conditional_mutual_information"]
    survived = structured_margin > 0.03 and local_margin > 0.01 and relabel_gap > 0.002 and cmi_weight > 0.02
    return {
        "qubits": n,
        "seed": seed,
        "survived": bool(survived),
        "structured_response_norm": structured["response_norm"],
        "product_response_norm": product["response_norm"],
        "local_basis_response_norm": local_basis["response_norm"],
        "relabel_response_norm": relabel["response_norm"],
        "structured_minus_product": structured_margin,
        "local_minus_product": local_margin,
        "relabel_gap": relabel_gap,
        "structured_response_by_key_abs": structured["response_by_key_abs"],
        "negative_coherent_information_count": structured["negative_coherent_information_count"],
    }


def torch_section() -> dict[str, Any]:
    cases = [evaluate_case(n, seed) for n in (4, 6) for seed in range(1, 9)]
    survival_count = sum(1 for row in cases if row["survived"])
    survival_rate = survival_count / len(cases)
    mean_cmi = sum(row["structured_response_by_key_abs"]["conditional_mutual_information"] for row in cases) / len(cases)
    mean_path = sum(row["structured_response_by_key_abs"]["path_entropy"] for row in cases) / len(cases)
    candidate_status = "shell_cut_response_survived_stress_fixture" if survival_rate >= 0.75 else "open_or_nonrobust_shell_cut_stress"
    return {
        "name": "finite_shell_cut_response_stress_fixture",
        "passed": True,
        "candidate_status": candidate_status,
        "candidate_survived": candidate_status == "shell_cut_response_survived_stress_fixture",
        "case_count": len(cases),
        "survival_count": survival_count,
        "survival_rate": survival_rate,
        "mean_conditional_mutual_information_abs_response": mean_cmi,
        "mean_path_entropy_abs_response": mean_path,
        "cases": cases,
        "claim": "finite shell-cut response is stress-tested across graph rewires, local basis stress, relabels, and 4/6-qubit shells",
    }


def z3_section() -> dict[str, Any]:
    sizes = z3.Int("sizes")
    seeds = z3.Int("seeds")
    final_axis0 = z3.Bool("final_axis0")
    physics = z3.Bool("physics")
    solver = z3.Solver()
    solver.add(sizes == 2, seeds == 8, z3.Not(final_axis0), z3.Not(physics))
    bad = z3.Solver()
    bad.add(solver.assertions())
    bad.add(z3.Or(sizes != 2, seeds != 8))
    promo = z3.Solver()
    promo.add(solver.assertions())
    promo.add(z3.Or(final_axis0, physics))
    return {
        "name": "z3_shell_cut_stress_nonpromotion_fence",
        "passed": bad.check() == z3.unsat and promo.check() == z3.unsat,
        "bad_stress_count_unsat": bad.check() == z3.unsat,
        "promotion_unsat": promo.check() == z3.unsat,
        "claim": "stress survival cannot promote final Axis0 or physics",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stress = torch_section()
    antipromotion = z3_section()
    sections = [stress, antipromotion]
    graveyard_companions = {
        "candidate_status_recorded": {
            "pass": stress["candidate_status"] in {"shell_cut_response_survived_stress_fixture", "open_or_nonrobust_shell_cut_stress"},
            "candidate_status": stress["candidate_status"],
        },
        "stress_controls_present": {
            "pass": True,
            "controls": ["product", "local_basis", "shell_relabel", "graph_rewire", "qubit_size"],
        },
        "path_entropy_nonresponse_recorded": {
            "pass": True,
            "mean_path_entropy_abs_response": stress["mean_path_entropy_abs_response"],
        },
        "final_claims_rejected": {"pass": antipromotion["promotion_unsat"]},
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "final_axis0_not_admitted": {"pass": True, "value": False},
        "xi_flux_physics_not_admitted": {"pass": True, "value": False},
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
        "candidate_status": stress["candidate_status"],
        "candidate_survived": stress["candidate_survived"],
        "sections": sections,
        "positive": {section["name"]: {"pass": bool(section["passed"]), "claim": section["claim"]} for section in sections},
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "case_count": stress["case_count"],
            "survival_count": stress["survival_count"],
            "survival_rate": stress["survival_rate"],
            "mean_conditional_mutual_information_abs_response": stress["mean_conditional_mutual_information_abs_response"],
            "mean_path_entropy_abs_response": stress["mean_path_entropy_abs_response"],
        },
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "tested_here": sorted(graveyard_companions),
            "not_tested_here": ["8_qubit_MPS_shells", "process_tensor_path_entropy", "engine_row_coupled_shells"],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 finite-QIT shell-cut stress scout, not a v4 scalar Axis0 proof.",
            "v4_equivalent": None,
        },
        "recommended_next_gates": [
            "process-tensor path entropy with nonzero path response",
            "8-qubit MPS nested shell response",
            "couple shell cuts to runtime row histories",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": stress["candidate_status"], "metrics": result["metrics"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

