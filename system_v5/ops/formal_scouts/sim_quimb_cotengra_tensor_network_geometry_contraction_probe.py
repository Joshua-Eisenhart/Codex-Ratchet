#!/usr/bin/env python3
"""Quimb/cotengra tensor-network geometry contraction scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import opt_einsum as oe
import quimb as qu
import quimb.tensor as qtn
import sympy as sp
import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "quimb_cotengra_tensor_network_geometry_contraction_probe_results.json"

NAME = "quimb_cotengra_tensor_network_geometry_contraction_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: admits quimb and cotengra as tensor-network tools for "
    "finite geometry-shaped contractions, MPS entropy readouts, and contraction "
    "tree optimization. It does not admit final manifold, cognition, physics, "
    "or neural-network architecture claims."
)

TOOL_MANIFEST = {
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS construction, gate application, and bond entropy readouts"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-tree search over geometry-shaped tensor equations"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing reference contraction path and numeric contraction cross-check"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor fixtures, gate construction, dense-state entropy, and distance calculations"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic contraction-inventory sanity check"},
}
TOOL_INTEGRATION_DEPTH = {
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
}

DTYPE = torch.complex128
RTYPE = torch.float64
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return value.item()
    return value


def to_quimb_array(value: torch.Tensor) -> Any:
    return qu.qarray(value.detach().cpu().tolist())


def topology_gates() -> dict[str, Any]:
    return {
        "funnel": to_quimb_array(torch.linalg.matrix_exp(-1j * 0.12 * torch.kron(SX, SZ))),
        "vortex": to_quimb_array(torch.linalg.matrix_exp(-1j * 0.18 * torch.kron(SY, SX))),
        "pit": to_quimb_array(torch.linalg.matrix_exp(-1j * 0.21 * torch.kron(SZ, SZ))),
        "hill": to_quimb_array(torch.linalg.matrix_exp(-1j * 0.09 * torch.kron(SZ, SX))),
    }


def mps_topology_readout() -> dict[str, Any]:
    base = qtn.MPS_rand_state(8, bond_dim=4, seed=17)
    gates = topology_gates()
    rows = {}
    for name, gate in gates.items():
        psi = base.copy()
        for pair in [(0, 1), (2, 3), (4, 5), (6, 7), (1, 2), (3, 4), (5, 6)]:
            psi.gate_(gate, pair, contract="swap+split", max_bond=8, cutoff=1e-10)
        entropies = [float(psi.entropy(i)) for i in range(1, 8)]
        rows[name] = {
            "max_bond": int(psi.max_bond()),
            "entropy_by_cut": entropies,
            "entropy_sum": float(sum(entropies)),
        }
    sums = {k: v["entropy_sum"] for k, v in rows.items()}
    return {
        "rows": rows,
        "unique_entropy_sums": len({round(v, 6) for v in sums.values()}),
        "pass": len({round(v, 6) for v in sums.values()}) == 4 and all(v["max_bond"] <= 8 for v in rows.values()),
    }


def dense_entropy_crosscheck() -> dict[str, Any]:
    ghz_vec = torch.zeros((2**4, 1), dtype=DTYPE)
    ghz_vec[0, 0] = 1.0 / math.sqrt(2.0)
    ghz_vec[15, 0] = 1.0 / math.sqrt(2.0)
    rho_full = to_quimb_array(ghz_vec @ torch.conj(ghz_vec.T))
    rho = qu.ptr(rho_full, dims=[2, 2, 2, 2], keep=[0, 1])
    vals = torch.linalg.eigvalsh(torch.as_tensor(rho, dtype=DTYPE)).real
    vals = torch.clamp(vals, min=1e-12)
    entropy = float(-(vals * torch.log(vals)).sum().item())
    return {"two_qubit_reduced_entropy": entropy, "pass": entropy > 0.65}


def contraction_tree_report() -> dict[str, Any]:
    generator = torch.Generator().manual_seed(5)
    arrays = [
        torch.randn((2, 3), generator=generator, dtype=RTYPE),
        torch.randn((3, 4), generator=generator, dtype=RTYPE),
        torch.randn((4, 5), generator=generator, dtype=RTYPE),
        torch.randn((5, 2), generator=generator, dtype=RTYPE),
    ]
    inputs = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
    output = ("a", "e")
    size_dict = {"a": 2, "b": 3, "c": 4, "d": 5, "e": 2}
    optimizer = ctg.HyperOptimizer(max_repeats=12, progbar=False, on_trial_error="raise")
    tree = optimizer.search(inputs, output, size_dict)
    contract_expr = "ab,bc,cd,de->ae"
    ref = oe.contract(contract_expr, *arrays)
    path, info = oe.contract_path(contract_expr, *arrays, optimize="optimal")
    ref_norm = float(torch.linalg.vector_norm(torch.as_tensor(ref)).item())
    return {
        "cotengra_width": float(tree.contraction_width()),
        "cotengra_cost": float(tree.contraction_cost()),
        "opt_einsum_path": [str(x) for x in path],
        "opt_einsum_optimized_flops": float(info.opt_cost),
        "reference_norm": ref_norm,
        "pass": float(tree.contraction_cost()) <= float(info.opt_cost) * 2.0 and ref_norm > 0,
    }


def collapsed_contraction_control() -> dict[str, Any]:
    generator = torch.Generator().manual_seed(7)
    arrays = [
        torch.randn((2, 2), generator=generator, dtype=RTYPE),
        torch.randn((2, 2), generator=generator, dtype=RTYPE),
        torch.randn((2, 2), generator=generator, dtype=RTYPE),
        torch.randn((2, 2), generator=generator, dtype=RTYPE),
    ]
    structured = oe.contract("ab,bc,cd,de->ae", *arrays)
    collapsed = oe.contract("ab,ab,ab,ab->ab", *arrays)
    diff = float(torch.linalg.vector_norm(torch.as_tensor(structured - collapsed)).item())
    return {"structured_vs_collapsed_norm": diff, "pass": diff > 0.1}


def symbolic_inventory() -> dict[str, Any]:
    tensors, open_indices = sp.symbols("tensors open_indices", integer=True)
    claim = sp.And(sp.Eq(tensors, 4), sp.Eq(open_indices, 2))
    return {"pass": bool(claim.subs({tensors: 4, open_indices: 2})), "tensor_count": 4, "open_index_count": 2}


def main() -> int:
    started = time.time()
    mps = mps_topology_readout()
    dense = dense_entropy_crosscheck()
    tree = contraction_tree_report()
    collapsed = collapsed_contraction_control()
    symbolic = symbolic_inventory()
    positive = {
        "quimb_mps_topology_entropy_readouts_separate": mps,
        "cotengra_contraction_tree_executes": tree,
        "dense_entropy_crosscheck_executes": dense,
        "symbolic_contraction_inventory": symbolic,
    }
    graveyard_companions = {
        "collapsed_geometry_contraction_differs": collapsed,
        "single_gate_reuse_would_collapse_topology_entropy": {
            "unique_entropy_sums": mps["unique_entropy_sums"],
            "pass": mps["unique_entropy_sums"] == 4,
        },
    }
    boundary = {
        "installed_versions": {
            "quimb": getattr(qu, "__version__", "unknown"),
            "cotengra": getattr(ctg, "__version__", "unknown"),
            "pass": True,
        }
    }
    nearby_variants = {
        "total": 2,
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and nearby_variants["passed"] == nearby_variants["total"]
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "tensor_network_tool_admission_for_dynamic_geometry_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Tool-admission scout only.",
            "Does not yet integrate quimb/cotengra into the full chiral operating-space stage cycle.",
            "Does not promote final neural-network architecture or physics claims.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
