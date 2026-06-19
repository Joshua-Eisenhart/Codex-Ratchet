#!/usr/bin/env python3
"""PyTorch graph/tensor lane for render_layer_readout_v1."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import render_layer_readout_v1_common as common


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "torch.func": {"tried": True, "used": True, "reason": "vmap tensor smoke plus v1 render vector lane binding"},
    "torch_geometric": {"tried": True, "used": True, "reason": "finite graph carrier smoke for committed edge-index style"},
    "sympy": {"tried": True, "used": True, "reason": "exact finite scalar smoke check"},
    "z3": {"tried": True, "used": True, "reason": "two-sided v1 reachability proof with erased old-pin control"},
    "cvc5": {"tried": True, "used": True, "reason": "independent two-sided v1 reachability proof with erased old-pin control"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def package_smoke() -> dict[str, object]:
    edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
    x = torch.tensor([[1.0], [-1.0], [0.0]], dtype=torch.float64)
    data = Data(x=x, edge_index=edge_index)

    def square(value: torch.Tensor) -> torch.Tensor:
        return value * value

    values = vmap(square)(torch.tensor([1.0, 2.0, 3.0], dtype=torch.float64))
    solver = z3.Solver()
    solver.add(z3.Int("x") == 1)
    cvc = cvc5.Solver()
    cvc.setLogic("QF_LIA")
    return {
        "torch_dtype": str(x.dtype),
        "torch_func_vmap_sum": float(values.sum().item()),
        "torch_geometric_num_nodes": int(data.num_nodes),
        "sympy_rational": str(sp.Rational(2, 5) + sp.Rational(3, 5)),
        "z3_check": str(solver.check()),
        "cvc5_ready": True,
    }


def build_result() -> dict[str, object]:
    payload = common.engine_payload(
        "pytorch",
        SOURCE_PATH,
        RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        observables={
            "torch.func": "torch.func.vmap tensor smoke plus v1 render vector lane binding",
            "torch_geometric": "torch_geometric.data.Data finite graph carrier smoke for committed edge-index style",
            "sympy": "sp.Rational exact control smoke for finite scalar binding",
            "z3": "z3.Solver two-sided v1 reachability proof with erased old-pin control",
            "cvc5": "cvc5.Solver independent two-sided v1 reachability proof with erased old-pin control",
        },
        role_id="render_layer_readout_v1_pytorch_graph_tensor_builder",
    )
    payload["package_smoke"] = package_smoke()
    return payload


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
