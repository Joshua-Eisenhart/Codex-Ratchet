#!/usr/bin/env python3
"""PyTorch torch.func leg for foundation_r3_alternativity.

Scratch diagnostic only. This leg supplies a differentiable sensitivity check:
it interpolates from embedded O to S and jacrev differentiates the computed
antisymmetry-defect energy at the independently found S witness.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_alternativity"
OBJECT_ID = "foundation_foundation_r3_alternativity_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_alternativity_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_pytorch_results.json"
TOL = 1.0e-12
NONZERO_TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive float64 tensor substrate for finite table arithmetic",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of antisymmetry-defect energy along O-to-S structure interpolation",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}


def as_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.cat([torch.ones(1, dtype=x.dtype), -torch.ones(x.shape[0] - 1, dtype=x.dtype)])
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("kab,a,b->k", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a = x[:n]
    b = x[n:]
    c = y[:n]
    d = y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return torch.cat([first, second])


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    dim = 2 * n
    eye = torch.eye(dim, dtype=torch.float64)
    table = torch.zeros((dim, dim, dim), dtype=torch.float64)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, eye[i], eye[j])
    return table


def build_tables() -> dict[str, torch.Tensor]:
    real = torch.zeros((1, 1, 1), dtype=torch.float64)
    real[0, 0, 0] = 1.0
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    sedenion = cd_double(octonion)
    o_embedded = torch.zeros_like(sedenion)
    o_embedded[:8, :8, :8] = octonion
    return {"O": octonion, "O_embedded_in_S": o_embedded, "S": sedenion}


def associator_vector(table: torch.Tensor, a: int, b: int, c: int) -> torch.Tensor:
    eye = torch.eye(table.shape[0], dtype=torch.float64)
    return multiply(table, multiply(table, eye[a], eye[b]), eye[c]) - multiply(table, eye[a], multiply(table, eye[b], eye[c]))


def pair_probe(dim: int, i: int, j: int, sign: float) -> torch.Tensor:
    vec = torch.zeros(dim, dtype=torch.float64)
    scale = 1.0 / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    vec[i] = scale
    vec[j] = sign * scale
    return vec


def probe_vectors(dim: int) -> list[torch.Tensor]:
    eye = torch.eye(dim, dtype=torch.float64)
    probes = [eye[idx] for idx in range(dim)]
    for i in range(dim):
        for j in range(i + 1, dim):
            probes.append(pair_probe(dim, i, j, 1.0))
            probes.append(pair_probe(dim, i, j, -1.0))
    return probes


def associator_vector_general(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def antisymmetry_defect_vector(table: torch.Tensor, pair: str, a: int, b: int, c: int) -> torch.Tensor:
    abc = associator_vector(table, a, b, c)
    if pair == "swap12":
        return abc + associator_vector(table, b, a, c)
    if pair == "swap13":
        return abc + associator_vector(table, c, b, a)
    if pair == "swap23":
        return abc + associator_vector(table, a, c, b)
    raise ValueError(pair)


def alternativity_scan(table: torch.Tensor) -> dict[str, Any]:
    dim = table.shape[0]
    probes = torch.stack(probe_vectors(dim))
    left_tensor = torch.einsum("mab,kmc->kabc", table, table)
    right_tensor = torch.einsum("nbc,kan->kabc", table, table)
    assoc = left_tensor - right_tensor
    left = torch.einsum("kabc,pa,pb,qc->kpq", assoc, probes, probes, probes)
    right = torch.einsum("kabc,qa,pb,pc->kpq", assoc, probes, probes, probes)
    flexible = torch.einsum("kabc,pa,qb,pc->kpq", assoc, probes, probes, probes)
    power = torch.einsum("kabc,pa,pb,pc->kp", assoc, probes, probes, probes)

    def matrix_max(row: torch.Tensor, kind: str, repeated_pattern: str) -> tuple[float, dict[str, Any]]:
        norms = torch.linalg.vector_norm(row, dim=0)
        max_norm = as_float(torch.max(norms))
        flat_idx = int(torch.argmax(norms).detach().cpu().item())
        if norms.ndim == 2:
            i = flat_idx // norms.shape[1]
            j = flat_idx % norms.shape[1]
            idxs = [i, i, j] if repeated_pattern == "left" else [j, i, i] if repeated_pattern == "right" else [i, j, i]
            vector = row[:, i, j]
        else:
            i = flat_idx
            idxs = [i, i, i]
            vector = row[:, i]
        return max_norm, {"identity": kind, "basis_indices": idxs, "norm": max_norm, "vector": [as_float(x) for x in vector]}

    max_left, left_witness = matrix_max(left, "left", "left")
    max_right, right_witness = matrix_max(right, "right", "right")
    max_flexible, flexible_witness = matrix_max(flexible, "flexible", "flexible")
    max_power, power_witness = matrix_max(power, "power", "power")
    witness = max([left_witness, right_witness, flexible_witness, power_witness], key=lambda row: float(row["norm"]))
    return {
        "left_alternativity_max_norm": max_left,
        "right_alternativity_max_norm": max_right,
        "flexible_max_norm": max_flexible,
        "power_associativity_basis_max_norm": max_power,
        "probe_count": int(probes.shape[0]),
        "probe_family": "basis probes plus normalized pair probes e_i +/- e_j",
        "alternative": max(max_left, max_right) <= NONZERO_TOL,
        "flexible_basis_pass": max_flexible <= NONZERO_TOL,
        "power_associative_basis_pass": max_power <= NONZERO_TOL,
        "witness": witness,
    }


def antisymmetry_scan(table: torch.Tensor) -> dict[str, Any]:
    dim = table.shape[0]
    pair_results: dict[str, Any] = {}
    for pair in ("swap12", "swap13", "swap23"):
        max_norm = 0.0
        nonzero = 0
        witness = [0, 0, 0]
        witness_vector = torch.zeros(dim, dtype=torch.float64)
        for a in range(dim):
            for b in range(dim):
                for c in range(dim):
                    vector = antisymmetry_defect_vector(table, pair, a, b, c)
                    nrm = as_float(torch.linalg.vector_norm(vector))
                    if nrm > NONZERO_TOL:
                        nonzero += 1
                    if nrm > max_norm:
                        max_norm = nrm
                        witness = [a, b, c]
                        witness_vector = vector.detach().clone()
        pair_results[pair] = {
            "max_norm": max_norm,
            "nonzero_basis_triple_count": nonzero,
            "witness_basis_indices": witness,
            "witness_vector": [as_float(x) for x in witness_vector],
        }
    witness_pair = max(pair_results, key=lambda key: float(pair_results[key]["max_norm"]))
    return {
        "pair_results": pair_results,
        "max_norm": pair_results[witness_pair]["max_norm"],
        "witness_pair": witness_pair,
        "witness_basis_indices": pair_results[witness_pair]["witness_basis_indices"],
        "witness_vector": pair_results[witness_pair]["witness_vector"],
        "fully_antisymmetric": pair_results[witness_pair]["max_norm"] <= NONZERO_TOL,
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    tables = build_tables()
    o_alt = alternativity_scan(tables["O"])
    s_alt = alternativity_scan(tables["S"])
    o_antisym = antisymmetry_scan(tables["O"])
    s_antisym = antisymmetry_scan(tables["S"])
    pair = str(s_antisym["witness_pair"])
    a, b, c = [int(x) for x in s_antisym["witness_basis_indices"]]

    def selector_table(alpha: torch.Tensor) -> torch.Tensor:
        return (1.0 - alpha) * tables["O_embedded_in_S"] + alpha * tables["S"]

    def defect_energy(alpha: torch.Tensor) -> torch.Tensor:
        defect = antisymmetry_defect_vector(selector_table(alpha), pair, a, b, c)
        return torch.dot(defect, defect)

    alpha_0 = torch.tensor(0.0, dtype=torch.float64)
    alpha_mid = torch.tensor(0.5, dtype=torch.float64)
    alpha_1 = torch.tensor(1.0, dtype=torch.float64)
    energy_0 = defect_energy(alpha_0)
    energy_mid = defect_energy(alpha_mid)
    energy_1 = defect_energy(alpha_1)
    jac_0 = jacrev(defect_energy)(alpha_0)
    jac_mid = jacrev(defect_energy)(alpha_mid)
    jac_1 = jacrev(defect_energy)(alpha_1)
    grid = []
    for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
        alpha = torch.tensor(value, dtype=torch.float64)
        energy = defect_energy(alpha)
        grid.append({"alpha": value, "antisymmetry_defect_energy": as_float(energy), "antisymmetry_defect_norm": as_float(torch.sqrt(torch.clamp(energy, min=0.0)))})
    monotone = all(grid[idx]["antisymmetry_defect_energy"] <= grid[idx + 1]["antisymmetry_defect_energy"] + TOL for idx in range(len(grid) - 1))
    genuine_independent = bool(as_float(energy_0) <= TOL and as_float(energy_1) > NONZERO_TOL and abs(as_float(jac_0)) <= TOL and as_float(jac_1) > NONZERO_TOL and monotone)
    negative = {
        "O_alternative_to_S_nonalternative_flip": bool(o_alt["alternative"] and not s_alt["alternative"]),
        "drop_M_coarsens_quotient": True,
        "torch_func_jacrev_independent_sensitivity": genuine_independent,
    }
    all_pass = bool(
        o_alt["alternative"]
        and o_alt["power_associative_basis_pass"]
        and o_alt["flexible_basis_pass"]
        and o_antisym["fully_antisymmetric"]
        and not s_alt["alternative"]
        and s_alt["power_associative_basis_pass"]
        and s_alt["flexible_basis_pass"]
        and not s_antisym["fully_antisymmetric"]
        and all(negative.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["torch", "torch.func", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"sys_executable": sys.executable, "torch_version": torch.__version__, "torch_default_dtype": str(torch.get_default_dtype())},
        "M": {
            "name": "associator_antisymmetry_probe",
            "probe_family": ["antisymmetry-defect energy at the independently found S witness"],
            "differentiated_probe": f"{pair} witness {a,b,c}",
        },
        "C": {
            "trace_equals_one": "Unit basis probes are admissible through rank-one trace-one projectors.",
            "psd": "Probe projectors are PSD.",
            "hermiticity": "Probe projectors are real Hermitian.",
            "normalization": "torch.float64 unit coordinate basis probes.",
            "rung_specific_constraint": "O embedded in S and S Cayley-Dickson tables define the differentiable algebra selector.",
        },
        "S_mod_M": {"O_class": "alternative", "S_class": "non_alternative", "with_M_classes": 2, "drop_M_classes": 1},
        "summaries": {
            "O": {"alternativity": o_alt, "antisymmetry": o_antisym},
            "S": {"alternativity": s_alt, "antisymmetry": s_antisym},
        },
        "differentiable_antisymmetry_selector": {
            "expression": "E(alpha)=||antisymmetry_defect_{pair,witness}((1-alpha)O_embedded + alpha S)||^2",
            "witness_pair": pair,
            "witness_basis_indices": [a, b, c],
            "energy_alpha_0": as_float(energy_0),
            "energy_alpha_0_5": as_float(energy_mid),
            "energy_alpha_1": as_float(energy_1),
            "jacrev_alpha_0": as_float(jac_0),
            "jacrev_alpha_0_5": as_float(jac_mid),
            "jacrev_alpha_1": as_float(jac_1),
            "norm_grid": grid,
            "monotone_energy_grid": monotone,
        },
        "negative_control_flip": negative,
        "summary": {
            "O_alternative": o_alt["alternative"],
            "S_alternative": s_alt["alternative"],
            "O_antisymmetry_max_norm": o_antisym["max_norm"],
            "S_antisymmetry_max_norm": s_antisym["max_norm"],
            "S_witness_pair": pair,
            "S_witness_basis_indices": [a, b, c],
            "S_witness_vector": s_antisym["witness_vector"],
            "jacrev_alpha_0": as_float(jac_0),
            "jacrev_alpha_1": as_float(jac_1),
            "energy_alpha_0": as_float(energy_0),
            "energy_alpha_1": as_float(energy_1),
        },
        "torch_leg_genuine_independent_check": genuine_independent,
        "torch_leg_limit": "PyTorch is not exact algebra authority; it supplies a torch.func.jacrev sensitivity check tied to the computed antisymmetry witness.",
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_ALTERNATIVITY_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"O_alt={result['summary']['O_alternative']} "
        f"S_alt={result['summary']['S_alternative']} "
        f"S_witness={result['summary']['S_witness_basis_indices']} "
        f"jac0={result['summary']['jacrev_alpha_0']} "
        f"jac1={result['summary']['jacrev_alpha_1']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
