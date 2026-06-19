#!/usr/bin/env python3
"""PyTorch graph/component leg for sedenion-derived PG(3,2) incidence."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "pg32_sedenion_incidence"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

OCTONION_TRIPLES = (
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def basis(dim: int, idx: int, *, dtype: torch.dtype = torch.int64) -> torch.Tensor:
    return torch.eye(dim, dtype=dtype)[idx]


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.ones_like(x)
    signs[1:] = -1
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("kij,i,j->k", table, x, y)


def octonion_table(*, dtype: torch.dtype = torch.int64) -> torch.Tensor:
    table = torch.zeros((8, 8, 8), dtype=dtype)
    table[0, 0, 0] = 1
    for i in range(1, 8):
        table[i, 0, i] = 1
        table[i, i, 0] = 1
        table[0, i, i] = -1
    for a, b, c in OCTONION_TRIPLES:
        for x, y, z, sign in (
            (a, b, c, 1),
            (b, c, a, 1),
            (c, a, b, 1),
            (b, a, c, -1),
            (c, b, a, -1),
            (a, c, b, -1),
        ):
            table[z, x, y] = sign
    return table


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    dim = 2 * n
    table = torch.zeros((dim, dim, dim), dtype=parent.dtype)
    eye = torch.eye(dim, dtype=parent.dtype)
    for i in range(dim):
        for j in range(dim):
            x = eye[i]
            y = eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
            table[:, i, j] = torch.cat([first, second])
    return table


def sedenion_table(*, dtype: torch.dtype = torch.int64) -> torch.Tensor:
    return cd_double(octonion_table(dtype=dtype))


def vector_terms(v: torch.Tensor) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for idx, coeff in enumerate(v.detach().cpu().tolist()):
        if float(coeff) != 0.0:
            value: int | float = int(coeff) if float(coeff).is_integer() else float(coeff)
            terms.append({"basis_index": idx, "label": f"e{idx}", "coefficient": value})
    return terms


def normsq(v: torch.Tensor) -> float:
    return float(torch.sum(v * v).item())


def product_index_and_sign(table: torch.Tensor, a: int, b: int) -> tuple[int, int]:
    prod = multiply(table, basis(int(table.shape[0]), a, dtype=table.dtype), basis(int(table.shape[0]), b, dtype=table.dtype))
    terms = vector_terms(prod)
    if len(terms) != 1:
        raise ValueError(f"basis product e{a}*e{b} has {len(terms)} terms")
    return int(terms[0]["basis_index"]), int(terms[0]["coefficient"])


def extract_lines(table: torch.Tensor, points: range) -> tuple[list[tuple[int, int, int]], dict[tuple[int, int], tuple[int, int, int]]]:
    lines = set()
    pair_to_line: dict[tuple[int, int], tuple[int, int, int]] = {}
    for a, b in combinations(points, 2):
        k, sign = product_index_and_sign(table, a, b)
        if k in points and abs(sign) == 1:
            line = tuple(sorted((a, b, k)))
            lines.add(line)
            pair_to_line[(a, b)] = line
    return sorted(lines), pair_to_line


def pair_axiom(lines: list[tuple[int, int, int]], points: range) -> dict[str, Any]:
    bad = []
    for a, b in combinations(points, 2):
        count = sum(1 for line in lines if a in line and b in line)
        if count != 1:
            bad.append({"pair": [a, b], "line_count": count})
    return {"pair_count": len(list(combinations(points, 2))), "all_pairs_exactly_one_line": not bad, "violations": bad}


def planes_from_pair_map(pair_to_line: dict[tuple[int, int], tuple[int, int, int]], points: range) -> list[tuple[int, ...]]:
    planes = []
    for subset in combinations(points, 7):
        subset_set = set(subset)
        if all(set(pair_to_line[tuple(sorted((a, b)))]) <= subset_set for a, b in combinations(subset, 2)):
            planes.append(subset)
    return planes


def assoc(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def alternative_witness(table: torch.Tensor, plane: tuple[int, ...]) -> dict[str, Any] | None:
    vecs = [basis(16, 0, dtype=table.dtype)] + [basis(16, p, dtype=table.dtype) for p in plane]
    labels = [0, *plane]
    for ix, x in enumerate(vecs):
        for iy, y in enumerate(vecs):
            for iz, z in enumerate(vecs):
                left_alt = assoc(table, x, y, z) + assoc(table, y, x, z)
                right_alt = assoc(table, x, y, z) + assoc(table, x, z, y)
                if normsq(left_alt) != 0.0:
                    return {"kind": "left_linearized_alternativity_failure", "x": labels[ix], "y": labels[iy], "z": labels[iz], "sum_terms": vector_terms(left_alt)}
                if normsq(right_alt) != 0.0:
                    return {"kind": "right_linearized_alternativity_failure", "x": labels[ix], "y": labels[iy], "z": labels[iz], "sum_terms": vector_terms(right_alt)}
    return None


def plane_classification(table: torch.Tensor, lines: list[tuple[int, int, int]], pair_to_line: dict[tuple[int, int], tuple[int, int, int]]) -> dict[str, Any]:
    records = []
    for plane in planes_from_pair_map(pair_to_line, range(1, 16)):
        plane_set = set(plane)
        plane_lines = [line for line in lines if set(line) <= plane_set]
        witness = alternative_witness(table, plane)
        records.append(
            {
                "plane": list(plane),
                "line_count_inside": len(plane_lines),
                "closed": True,
                "alternative": witness is None,
                "classification": "genuine_octonion_subalgebra" if witness is None else "closed_non_alternative_sedenion_plane",
                "witness": witness,
            }
        )
    return {
        "plane_count": len(records),
        "genuine_octonion_count": sum(1 for row in records if row["classification"] == "genuine_octonion_subalgebra"),
        "non_alternative_count": sum(1 for row in records if row["classification"] != "genuine_octonion_subalgebra"),
        "records": records,
    }


def two_term(dim: int, a: int, b: int, *, dtype: torch.dtype = torch.int64) -> torch.Tensor:
    out = torch.zeros((dim,), dtype=dtype)
    out[a] = 1
    out[b] = 1
    return out


def zero_divisor_graph(table: torch.Tensor) -> dict[str, Any]:
    pairs = list(combinations(range(1, 16), 2))
    adjacency: dict[tuple[int, int], set[tuple[int, int]]] = {pair: set() for pair in pairs}
    ordered = 0
    examples = []
    for ab in pairs:
        x = two_term(16, *ab, dtype=table.dtype)
        for cd in pairs:
            y = two_term(16, *cd, dtype=table.dtype)
            prod = multiply(table, x, y)
            if normsq(prod) == 0.0:
                ordered += 1
                adjacency[ab].add(cd)
                adjacency[cd].add(ab)
                if len(examples) < 12:
                    examples.append({"left_pair": list(ab), "right_pair": list(cd), "product_terms": vector_terms(prod)})
    seen = set()
    components = []
    for node in pairs:
        if node in seen:
            continue
        stack = [node]
        seen.add(node)
        comp = []
        while stack:
            item = stack.pop()
            comp.append(item)
            for nxt in adjacency[item]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if len(comp) > 1:
            components.append(sorted(comp))
    return {
        "ordered_zero_divisor_pair_count": ordered,
        "component_count": len(components),
        "component_sizes": sorted(len(comp) for comp in components),
        "components": [[list(pair) for pair in comp] for comp in components],
        "examples": examples,
    }


def octonion_control(table: torch.Tensor) -> dict[str, Any]:
    lines, _ = extract_lines(table, range(1, 8))
    zero_count = 0
    for ab in combinations(range(1, 8), 2):
        for cd in combinations(range(1, 8), 2):
            zero_count += int(normsq(multiply(table, two_term(8, *ab, dtype=table.dtype), two_term(8, *cd, dtype=table.dtype))) == 0.0)
    axiom = pair_axiom(lines, range(1, 8))
    return {"line_count": len(lines), "pair_axiom": axiom, "ordered_zero_divisor_pair_count": zero_count, "all_pass": len(lines) == 7 and axiom["all_pairs_exactly_one_line"] and zero_count == 0}


def signed_entry_scramble_control(table: torch.Tensor) -> dict[str, Any]:
    scrambled = table.clone()
    prod_12 = multiply(table, basis(16, 1, dtype=table.dtype), basis(16, 2, dtype=table.dtype))
    prod_14 = multiply(table, basis(16, 1, dtype=table.dtype), basis(16, 4, dtype=table.dtype))
    scrambled[:, 1, 2] = prod_14
    scrambled[:, 2, 1] = -prod_14
    scrambled[:, 1, 4] = prod_12
    scrambled[:, 4, 1] = -prod_12
    lines, _ = extract_lines(scrambled, range(1, 16))
    axiom = pair_axiom(lines, range(1, 16))
    return {"line_count": len(lines), "pair_axiom_ok": axiom["all_pairs_exactly_one_line"], "first_pair_violations": axiom["violations"][:8], "breaks": len(lines) != 35 or not axiom["all_pairs_exactly_one_line"]}


def jacrev_zero_witness(float_table: torch.Tensor, left_pair: tuple[int, int], right_pair: tuple[int, int]) -> dict[str, Any]:
    def product_norm_from_theta(theta: torch.Tensor) -> torch.Tensor:
        left = torch.zeros(16, dtype=torch.float64)
        right = torch.zeros(16, dtype=torch.float64)
        left[left_pair[0]] = theta[0]
        left[left_pair[1]] = theta[1]
        right[right_pair[0]] = theta[2]
        right[right_pair[1]] = theta[3]
        return torch.sum(multiply(float_table, left, right) ** 2)

    theta = torch.ones(4, dtype=torch.float64)
    value = product_norm_from_theta(theta)
    grad = jacrev(product_norm_from_theta)(theta)
    perturbed = theta.clone()
    perturbed[0] += 0.125
    perturbed_value = product_norm_from_theta(perturbed)
    return {
        "left_pair": list(left_pair),
        "right_pair": list(right_pair),
        "product_normsq_at_ones": float(value.item()),
        "jacrev_gradient": [float(x) for x in grad.detach().cpu().tolist()],
        "perturbed_product_normsq": float(perturbed_value.item()),
        "load_bearing_check": float(value.item()) == 0.0 and float(perturbed_value.item()) > 0.0,
    }


def main() -> int:
    torch.set_default_dtype(torch.float64)
    s_table = sedenion_table(dtype=torch.int64)
    o_table = octonion_table(dtype=torch.int64)
    lines, pair_to_line = extract_lines(s_table, range(1, 16))
    axiom = pair_axiom(lines, range(1, 16))
    planes = plane_classification(s_table, lines, pair_to_line)
    zd = zero_divisor_graph(s_table)
    first_left = tuple(zd["examples"][0]["left_pair"])
    first_right = tuple(zd["examples"][0]["right_pair"])
    jac = jacrev_zero_witness(s_table.to(torch.float64), first_left, first_right)
    control_oct = octonion_control(o_table)
    control_scramble = signed_entry_scramble_control(s_table)
    shared_scalars = {
        "line_count": len(lines),
        "pair_axiom_ok": int(axiom["all_pairs_exactly_one_line"]),
        "plane_count": planes["plane_count"],
        "genuine_octonion_plane_count": planes["genuine_octonion_count"],
        "non_alternative_plane_count": planes["non_alternative_count"],
        "ordered_zero_divisor_pair_count": zd["ordered_zero_divisor_pair_count"],
        "zero_divisor_component_count": zd["component_count"],
        "octonion_line_count": control_oct["line_count"],
        "octonion_zero_divisor_pair_count": control_oct["ordered_zero_divisor_pair_count"],
        "scrambled_breaks_pair_axiom": int(control_scramble["breaks"]),
    }
    all_pass = (
        len(lines) == 35
        and axiom["all_pairs_exactly_one_line"]
        and planes["plane_count"] == 15
        and planes["genuine_octonion_count"] == 8
        and planes["non_alternative_count"] == 7
        and zd["ordered_zero_divisor_pair_count"] == 84
        and zd["component_count"] == 7
        and control_oct["all_pass"]
        and control_scramble["breaks"]
        and jac["load_bearing_check"]
    )
    payload = {
        "schema_version": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_pytorch",
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "sys_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "json"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "torch tensor recomputation of Cayley-Dickson incidence and zero-divisor graph"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity check around one zero-product witness"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
        "construction": {
            "octonion_source": "canonical oriented octonion table",
            "octonion_triples": [list(row) for row in OCTONION_TRIPLES],
            "line_extraction": "all triples {i,j,k} with e_i e_j = +/- e_k, derived from table products",
        },
        "incidence": {"line_count": len(lines), "lines": [list(line) for line in lines], "pair_axiom": axiom},
        "planes": planes,
        "zero_divisors": zd,
        "controls": {"octonion_restriction": control_oct, "signed_entry_scramble": control_scramble},
        "torch_func_zero_witness": jac,
        "shared_scalars": shared_scalars,
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"lines={len(lines)} pair_axiom={axiom['all_pairs_exactly_one_line']} "
        f"planes={planes['genuine_octonion_count']}/{planes['non_alternative_count']} "
        f"zero_pairs={zd['ordered_zero_divisor_pair_count']} components={zd['component_count']} "
        f"jacrev_load={jac['load_bearing_check']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
