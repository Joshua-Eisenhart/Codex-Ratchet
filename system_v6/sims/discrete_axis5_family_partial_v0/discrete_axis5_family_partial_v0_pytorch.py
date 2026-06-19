#!/usr/bin/env python3
"""PyTorch lane for discrete_axis5_family_partial_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import torch
from torch.func import vmap
import z3

import discrete_axis5_family_partial_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis5_object: dict) -> dict:
    coords = torch.tensor(
        [row["input_bloch"] for row in axis5_object["axis5_family_table"] if row["operator"] == "Ti"],
        dtype=torch.float64,
    )
    q = torch.tensor(common.Q, dtype=torch.float64)
    dz = torch.diag(torch.tensor([1.0 - q, 1.0 - q, 1.0], dtype=torch.float64))
    dx = torch.diag(torch.tensor([1.0, 1.0 - q, 1.0 - q], dtype=torch.float64))
    rx = torch.tensor(common.operator_matrix("Fi"), dtype=torch.float64)
    rz = torch.tensor(common.operator_matrix("Fe"), dtype=torch.float64)

    def radius_entropy(r: torch.Tensor) -> torch.Tensor:
        radius = torch.clamp(torch.linalg.vector_norm(r), 0.0, 1.0)
        vals = torch.stack(((1.0 + radius) / 2.0, (1.0 - radius) / 2.0))
        return -torch.sum(torch.where(vals > common.EPS, vals * torch.log(vals), torch.zeros_like(vals)))

    def purity(r: torch.Tensor) -> torch.Tensor:
        return (1.0 + torch.dot(r, r)) / 2.0

    ti_post = vmap(lambda r: dz @ r)(coords)
    te_post = vmap(lambda r: dx @ r)(coords)
    fi_post = vmap(lambda r: rx @ r)(coords)
    fe_post = vmap(lambda r: rz @ r)(coords)
    entropy_before = vmap(radius_entropy)(coords)
    dephasing_entropy_nonnegative = bool(
        torch.all(vmap(radius_entropy)(ti_post) - entropy_before >= -common.EPS).item()
        and torch.all(vmap(radius_entropy)(te_post) - entropy_before >= -common.EPS).item()
    )
    unitary_purity_preserved = bool(
        torch.all(torch.abs(vmap(purity)(fi_post) - vmap(purity)(coords)) <= common.EPS).item()
        and torch.all(torch.abs(vmap(purity)(fe_post) - vmap(purity)(coords)) <= common.EPS).item()
    )
    dephasing_contracts = bool(
        torch.all(vmap(torch.linalg.vector_norm)(ti_post) - vmap(torch.linalg.vector_norm)(coords) <= common.EPS).item()
        and torch.all(vmap(torch.linalg.vector_norm)(te_post) - vmap(torch.linalg.vector_norm)(coords) <= common.EPS).item()
    )

    counts = axis5_object["family_counts"]
    z_solver = z3.Solver()
    z_d = z3.Int("pytorch_axis5_dephasing_rows")
    z_u = z3.Int("pytorch_axis5_unitary_rows")
    z_solver.add(z_d == z3.IntVal(counts["dephasing_gradient_side"]))
    z_solver.add(z_u == z3.IntVal(counts["unitary_hamiltonian_side"]))
    z_solver.add(z3.Or(z_d == 0, z_u == 0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_d = c_solver.mkConst(int_sort, "pytorch_axis5_dephasing_rows")
    c_u = c_solver.mkConst(int_sort, "pytorch_axis5_unitary_rows")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_d, c_solver.mkInteger(counts["dephasing_gradient_side"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_u, c_solver.mkInteger(counts["unitary_hamiltonian_side"])))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.OR,
            c_solver.mkTerm(Kind.EQUAL, c_d, c_solver.mkInteger(0)),
            c_solver.mkTerm(Kind.EQUAL, c_u, c_solver.mkInteger(0)),
        )
    )
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "torch_func_vmap_state_count": int(coords.shape[0]),
        "torch_func_vmap_table_rows": int(coords.shape[0] * 4),
        "dephasing_entropy_nonnegative": dephasing_entropy_nonnegative,
        "dephasing_contracts_to_mixed": dephasing_contracts,
        "unitary_purity_preserved": unitary_purity_preserved,
        "z3_family_count_erasure": z3_status,
        "cvc5_family_count_erasure": cvc5_status,
        "pass": (
            int(coords.shape[0]) == common.EXPECTED_STATE_COUNT
            and int(coords.shape[0] * 4) == common.EXPECTED_TABLE_ROWS
            and dephasing_entropy_nonnegative
            and dephasing_contracts
            and unitary_purity_preserved
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis5_object = common.build_axis5_object()
    probe = source_backing_probe(axis5_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "z3", "cvc5"],
        aligned_packages_load_bearing=["torch.func", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap vectorized entropy/purity/contractivity witness recomputation over 33 Bloch vectors",
            "z3": "z3.Solver/z3.Int computed Axis-5 family-count erasure identity",
            "cvc5": "cvc5.Solver/mkConst/mkTerm computed Axis-5 family-count erasure identity",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
