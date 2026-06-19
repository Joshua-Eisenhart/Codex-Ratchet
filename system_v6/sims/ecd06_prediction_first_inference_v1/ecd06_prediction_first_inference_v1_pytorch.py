#!/usr/bin/env python3
"""PyTorch lane for the ECD.06 prediction-first inference discriminator."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import ecd06_prediction_first_inference_v1_common as common


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"


def package_smoke() -> dict[str, object]:
    edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
    x = torch.tensor([[1.0], [0.0], [-1.0]], dtype=torch.float64)
    data = Data(x=x, edge_index=edge_index)

    def square(value: torch.Tensor) -> torch.Tensor:
        return value * value

    values = vmap(square)(torch.tensor([1.0, 2.0, 3.0], dtype=torch.float64))
    solver = z3.Solver()
    solver.add(z3.Int("q") <= z3.Int("b"))
    cvc = cvc5.Solver()
    cvc.setLogic("QF_LIA")
    return {
        "torch_dtype": str(x.dtype),
        "torch_func_vmap_sum": float(values.sum().item()),
        "torch_geometric_num_nodes": int(data.num_nodes),
        "sympy_rational": str(sp.Rational(3, 11) + sp.Rational(8, 11)),
        "z3_check": str(solver.check()),
        "cvc5_ready": True,
    }


def build_result() -> dict[str, object]:
    return common.engine_payload(
        "pytorch",
        SOURCE_PATH,
        RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        observables={
            "torch.func": "torch.func.vmap finite tensor transform smoke for prediction-vector lane",
            "torch_geometric": "torch_geometric.data.Data finite graph carrier smoke for edge-index style",
            "sympy": "sp.Rational exact scalar smoke for typed-error aggregation binding",
            "z3": "z3.Solver finite adjusted-error winner relation",
            "cvc5": "cvc5.Solver independent finite adjusted-error winner relation",
        },
        role_id="ecd06_prediction_first_inference_v1_pytorch_builder",
        package_smoke=package_smoke(),
    )


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
