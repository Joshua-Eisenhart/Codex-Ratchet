#!/usr/bin/env python3
"""PyTorch leg for the associativity weakening lattice classifier."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import torch
import torch.func as torch_func


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "assoc_weakening_lattice_classifier"
OBJECT_ID = f"{SIM_ID}_pytorch"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False
TOL = 1.0e-9

IDENTITY_ORDER = [
    "associativity",
    "alternativity",
    "artin_diassociativity_basis_pairs",
    "moufang",
    "flexibility",
    "power_associativity",
    "third_power_associativity",
    "none",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor structure-constant products and identity residual checks",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap basis associator control over the octonion table",
    },
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive receipt serialization and hashing"},
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "python_stdlib": "supportive",
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if torch.is_tensor(value):
        if value.ndim == 0:
            return int(value.item()) if not value.dtype.is_floating_point else float(value.item())
        return value.detach().cpu().tolist()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.cat([torch.ones(1, dtype=x.dtype), -torch.ones(x.shape[0] - 1, dtype=x.dtype)])
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("kij,i,j->k", table.to(dtype=x.dtype), x, y)


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = int(parent.shape[0])
    dim = 2 * n
    table = torch.zeros((dim, dim, dim), dtype=torch.int64)
    eye = torch.eye(dim, dtype=torch.int64)
    for i in range(dim):
        for j in range(dim):
            x, y = eye[i], eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
            table[:, i, j] = torch.cat([first, second]).to(torch.int64)
    return table


def kill_control_table() -> torch.Tensor:
    table = torch.zeros((3, 3, 3), dtype=torch.int64)
    for i in range(3):
        table[i, 0, i] = 1
        table[i, i, 0] = 1
    table[1, 1, 1] = 1
    table[1, 1, 2] = 1
    table[2, 2, 2] = 1
    return table


def cayley_dickson_tables() -> dict[str, torch.Tensor]:
    real = torch.ones((1, 1, 1), dtype=torch.int64)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    sedenion = cd_double(octonion)
    return {"R": real, "C": complex_table, "H": quaternion, "O": octonion, "S": sedenion, "K": kill_control_table()}


def basis(dim: int) -> list[torch.Tensor]:
    eye = torch.eye(dim, dtype=torch.float64)
    return [eye[i] for i in range(dim)]


def generic_samples(dim: int) -> list[torch.Tensor]:
    return [torch.tensor([((seed + 2) * (i + 1) % 7) - 3 for i in range(dim)], dtype=torch.float64) for seed in range(6)]


def elem_label(index: int, dim: int) -> str:
    return f"e{index}" if index < dim else f"g{index - dim}"


def close(x: torch.Tensor, y: torch.Tensor) -> bool:
    return bool(torch.max(torch.abs(x - y)).item() <= TOL)


def residual_support(vec: torch.Tensor) -> dict[str, Any]:
    arr = vec.detach().cpu()
    support = [int(i) for i, value in enumerate(arr.tolist()) if abs(float(value)) > TOL]
    return {"support": support, "values": [float(arr[i].item()) for i in support], "max_abs": float(torch.max(torch.abs(vec)).item())}


def find_associativity(table: torch.Tensor) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            for k, z in enumerate(elems):
                left = multiply(table, multiply(table, x, y), z)
                right = multiply(table, x, multiply(table, y, z))
                if not close(left, right):
                    return False, {"kind": "associator", "x": elem_label(i, dim), "y": elem_label(j, dim), "z": elem_label(k, dim), **residual_support(left - right)}
    return True, None


def find_alternativity(table: torch.Tensor) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            left = multiply(table, multiply(table, x, x), y)
            right = multiply(table, x, multiply(table, x, y))
            if not close(left, right):
                return False, {"kind": "left_alternative", "x": elem_label(i, dim), "y": elem_label(j, dim), **residual_support(left - right)}
            left = multiply(table, multiply(table, y, x), x)
            right = multiply(table, y, multiply(table, x, x))
            if not close(left, right):
                return False, {"kind": "right_alternative", "x": elem_label(i, dim), "y": elem_label(j, dim), **residual_support(left - right)}
    return True, None


def generated_indices(table: torch.Tensor, i: int, j: int) -> list[int]:
    support = {0, i, j}
    changed = True
    while changed:
        changed = False
        for a in list(support):
            for b in list(support):
                for idx, value in enumerate(table[:, a, b].tolist()):
                    if int(value) != 0 and idx not in support:
                        support.add(idx)
                        changed = True
    return sorted(support)


def find_artin_basis_pairs(table: torch.Tensor) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    eye = basis(dim)
    for i in range(dim):
        for j in range(dim):
            generated = generated_indices(table, i, j)
            for a in generated:
                for b in generated:
                    for c in generated:
                        left = multiply(table, multiply(table, eye[a], eye[b]), eye[c])
                        right = multiply(table, eye[a], multiply(table, eye[b], eye[c]))
                        if not close(left, right):
                            return False, {
                                "kind": "basis_pair_generated_subalgebra_associator",
                                "generators": [f"e{i}", f"e{j}"],
                                "basis_triple": [f"e{a}", f"e{b}", f"e{c}"],
                                "generated_indices": generated,
                                **residual_support(left - right),
                            }
    return True, None


def find_moufang(table: torch.Tensor) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            for k, z in enumerate(elems):
                left = multiply(table, multiply(table, x, y), multiply(table, z, x))
                right = multiply(table, x, multiply(table, multiply(table, y, z), x))
                if not close(left, right):
                    return False, {"kind": "moufang", "x": elem_label(i, dim), "y": elem_label(j, dim), "z": elem_label(k, dim), **residual_support(left - right)}
    return True, None


def find_flexibility(table: torch.Tensor) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            left = multiply(table, multiply(table, x, y), x)
            right = multiply(table, x, multiply(table, y, x))
            if not close(left, right):
                return False, {"kind": "flexibility", "x": elem_label(i, dim), "y": elem_label(j, dim), **residual_support(left - right)}
    return True, None


def find_power_associativity(table: torch.Tensor) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        xx = multiply(table, x, x)
        x3_left = multiply(table, xx, x)
        x3_right = multiply(table, x, xx)
        if not close(x3_left, x3_right):
            return False, {"kind": "x3_bracketing", "x": elem_label(i, dim), **residual_support(x3_left - x3_right)}
        x4 = [
            multiply(table, multiply(table, xx, x), x),
            multiply(table, multiply(table, x, xx), x),
            multiply(table, xx, xx),
            multiply(table, x, multiply(table, xx, x)),
            multiply(table, x, multiply(table, x, xx)),
        ]
        for idx, value in enumerate(x4[1:], start=1):
            if not close(x4[0], value):
                return False, {"kind": "x4_bracketing", "x": elem_label(i, dim), "bracketing_index": idx, **residual_support(x4[0] - value)}
    return True, None


def find_third_power(table: torch.Tensor) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        left = multiply(table, x, multiply(table, x, x))
        right = multiply(table, multiply(table, x, x), x)
        if not close(left, right):
            return False, {"kind": "third_power", "x": elem_label(i, dim), **residual_support(left - right)}
    return True, None


def classify_table(table: torch.Tensor) -> dict[str, Any]:
    checks = {
        "associativity": find_associativity(table),
        "alternativity": find_alternativity(table),
        "artin_diassociativity_basis_pairs": find_artin_basis_pairs(table),
        "moufang": find_moufang(table),
        "flexibility": find_flexibility(table),
        "power_associativity": find_power_associativity(table),
        "third_power_associativity": find_third_power(table),
    }
    matrix = {name: passed for name, (passed, _) in checks.items()}
    matrix["none"] = not any(matrix.values())
    witnesses = {name: witness for name, (_, witness) in checks.items() if witness is not None}
    return {"identity_results": matrix, "lattice_position": next(name for name in IDENTITY_ORDER if matrix[name]), "failure_witnesses": witnesses}


def output_permuted_table(table: torch.Tensor) -> torch.Tensor:
    dim = int(table.shape[0])
    perm = list(range(dim))
    if dim > 2:
        perm[1], perm[2] = perm[2], perm[1]
    return table[torch.tensor(perm), :, :]


def table_hash(table: torch.Tensor) -> str:
    flat = [str(int(x)) for x in table.reshape(-1).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def vectorized_basis_control(table: torch.Tensor) -> dict[str, Any]:
    dim = int(table.shape[0])
    triples = torch.tensor([[i, j, k] for i in range(dim) for j in range(dim) for k in range(dim)], dtype=torch.long)
    eye = torch.eye(dim, dtype=torch.float64)

    def assoc_residual(idx: torch.Tensor) -> torch.Tensor:
        x, y, z = eye[idx[0]], eye[idx[1]], eye[idx[2]]
        return torch.max(torch.abs(multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))))

    residuals = torch_func.vmap(assoc_residual)(triples)
    return {
        "used_torch_func_vmap": True,
        "basis_triple_count": int(triples.shape[0]),
        "max_associator_residual": float(torch.max(residuals).item()),
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    tables = cayley_dickson_tables()
    classifications = {name: classify_table(table) for name, table in tables.items()}
    matrix = {name: row["identity_results"] for name, row in classifications.items()}
    positions = {name: row["lattice_position"] for name, row in classifications.items()}
    witnesses = {name: row["failure_witnesses"] for name, row in classifications.items()}
    permuted = classify_table(output_permuted_table(tables["O"]))
    column_has_fail = {identity: any(not matrix[alg][identity] for alg in matrix) for identity in IDENTITY_ORDER}
    expected = {
        "O_expected": matrix["O"]["associativity"] is False
        and all(matrix["O"][key] is True for key in ["alternativity", "artin_diassociativity_basis_pairs", "moufang", "flexibility", "power_associativity", "third_power_associativity"]),
        "S_expected": matrix["S"]["alternativity"] is False
        and matrix["S"]["flexibility"] is True
        and matrix["S"]["power_associativity"] is True
        and matrix["S"]["third_power_associativity"] is True,
        "kill_control_fails_flexibility": matrix["K"]["flexibility"] is False,
        "column_fail_coverage": all(column_has_fail.values()),
        "permuted_table_control_shifts": permuted["lattice_position"] != positions["O"],
    }
    all_pass = bool(
        all(expected.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return to_builtin(
        {
            "schema_version": "engine_leg_result_v1",
            "object_id": OBJECT_ID,
            "engine": "pytorch",
            "classification": classification,
            "promotion_allowed": promotion_allowed,
            "formal_admission_allowed": formal_admission_allowed,
            "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "source_path": str(SOURCE_PATH),
            "source_sha256": source_sha256(),
            "result_path": str(RESULT_PATH),
            "reads_peer_result": reads_peer_result,
            "packages_used": ["torch", "torch.func", "json", "hashlib", "pathlib"],
            "aligned_packages_load_bearing": ["torch.func"],
            "runtime": {"torch_version": torch.__version__, "default_dtype": str(torch.get_default_dtype())},
            "identity_order": IDENTITY_ORDER,
            "algebra_dimensions": {name: int(table.shape[0]) for name, table in tables.items()},
            "table_sha256": {name: table_hash(table) for name, table in tables.items()},
            "classification_matrix": matrix,
            "lattice_positions": positions,
            "failure_witnesses": witnesses,
            "controls": {
                "column_has_at_least_one_fail": column_has_fail,
                "permuted_output_axis_O": {
                    "original_position": positions["O"],
                    "permuted_position": permuted["lattice_position"],
                    "shifted": permuted["lattice_position"] != positions["O"],
                    "permuted_identity_results": permuted["identity_results"],
                },
                "vectorized_basis_control_O": vectorized_basis_control(tables["O"]),
            },
            "expected_checks": expected,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "all_pass": all_pass,
        }
    )


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ASSOC_WEAKENING_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"O={result['lattice_positions']['O']} "
        f"S={result['lattice_positions']['S']} "
        f"K={result['lattice_positions']['K']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
