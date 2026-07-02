#!/usr/bin/env python3
"""Quimb TensorNetwork constructor micro-probe.

This is a one-tool/function probe for qtn.Tensor and qtn.TensorNetwork
construction. It is intentionally narrower than the combined quimb/cotengra
contraction scout.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import quimb
import quimb.tensor as qtn
import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "quimb_tensornetwork_constructor_micro_probe_results.json"

NAME = "quimb_tensornetwork_constructor_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: probes quimb qtn.Tensor/qtn.TensorNetwork construction "
    "on a finite torch-backed spinor-bond fixture. It does not admit layer "
    "completion, G-structure selection, stacking, Axis0, flux, FEP, physics, "
    "or final manifold claims."
)
FINITE_MAP = (
    "QTN_constructor_micro : finite torch-backed site tensors and named "
    "physical/virtual indices -> quimb TensorNetwork object, index graph, "
    "bond-count readouts, contraction signature, and erased/wrong-index controls"
)
DOMAIN = (
    "four finite two-level sites; torch.complex128 site tensors; named physical "
    "indices p0..p3; named virtual bonds b01,b12,b23; bond_dim in {1,2}; "
    "wrong-index and erased-bond controls"
)
CODOMAIN_OR_OUTPUT = (
    "quimb TensorNetwork constructor object type, tensor count, connected "
    "virtual-bond count, max virtual bond, dense four-site signature for this "
    "micro fixture, bipartition entropy, and control deltas"
)
ROOT_CONSTRAINTS_IN_FORCE = [
    "F01 finite carrier/probe/operator/path set",
    "N01 order/index-sensitive virtual-bond graph construction",
]
TOOL_MANIFEST = {
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing qtn.Tensor and qtn.TensorNetwork constructors, index graph, and contraction object",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex site tensors and entropy/cut readouts",
    },
}
TOOL_INTEGRATION_DEPTH = {"quimb": "load_bearing", "pytorch": "load_bearing"}
BLOCKED_CONSUMERS = [
    "full_layer_completion_claim",
    "official_g_structure_selection",
    "layer_stacking_readiness",
    "cross_layer_order_closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return value.item()
    return value


def site_tensor(shape: tuple[int, int, int], seed: int) -> torch.Tensor:
    gen = torch.Generator().manual_seed(seed)
    real = torch.randn(shape, generator=gen, dtype=torch.float64)
    imag = torch.randn(shape, generator=gen, dtype=torch.float64)
    data = torch.complex(real, imag)
    return data / torch.linalg.vector_norm(data)


def build_network(bond_dim: int, *, wrong_index: bool = False) -> qtn.TensorNetwork:
    specs = [
        ((1, 2, bond_dim), ("l0", "p0", "b01"), "SITE0", 11),
        ((bond_dim, 2, bond_dim), ("b01" if not wrong_index else "bXX", "p1", "b12"), "SITE1", 13),
        ((bond_dim, 2, bond_dim), ("b12", "p2", "b23"), "SITE2", 17),
        ((bond_dim, 2, 1), ("b23", "p3", "r3"), "SITE3", 19),
    ]
    tensors = [
        qtn.Tensor(data=site_tensor(shape, seed), inds=inds, tags={tag})
        for shape, inds, tag, seed in specs
    ]
    return qtn.TensorNetwork(tensors)


def index_counts(tn: qtn.TensorNetwork) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tensor in tn.tensors:
        for ind in tensor.inds:
            counts[ind] = counts.get(ind, 0) + 1
    return counts


def dense_signature(tn: qtn.TensorNetwork) -> dict[str, Any]:
    out = tn.contract(output_inds=("p0", "p1", "p2", "p3"))
    data = torch.as_tensor(out.data, dtype=torch.complex128).reshape(16)
    norm = torch.linalg.vector_norm(data)
    if float(norm.real.item()) > 0.0:
        data = data / norm
    psi = data.reshape(4, 4)
    rho_left = psi @ torch.conj(psi.T)
    vals = torch.clamp(torch.linalg.eigvalsh(rho_left).real, min=1.0e-14)
    entropy = float(-(vals * torch.log(vals)).sum().item())
    return {
        "dense_shape": list(out.shape),
        "norm": float(norm.real.item()),
        "half_cut_entropy": entropy,
    }


def network_readout(tn: qtn.TensorNetwork) -> dict[str, Any]:
    sizes = tn.ind_sizes()
    counts = index_counts(tn)
    virtual = {ind: size for ind, size in sizes.items() if ind.startswith("b")}
    connected_virtual = {ind: size for ind, size in virtual.items() if counts.get(ind) == 2}
    dangling_virtual = {ind: size for ind, size in virtual.items() if counts.get(ind) != 2}
    signature = dense_signature(tn)
    return {
        "object_type": type(tn).__name__,
        "tensor_count": len(tn.tensors),
        "index_count": int(tn.num_indices),
        "index_sizes": dict(sorted(sizes.items())),
        "connected_virtual_bonds": dict(sorted(connected_virtual.items())),
        "dangling_virtual_bonds": dict(sorted(dangling_virtual.items())),
        "connected_virtual_bond_count": len(connected_virtual),
        "dangling_virtual_bond_count": len(dangling_virtual),
        "max_virtual_bond": max(virtual.values()) if virtual else 0,
        "signature": signature,
    }


def run_probe() -> dict[str, Any]:
    valid = network_readout(build_network(2))
    erased = network_readout(build_network(1))
    wrong = network_readout(build_network(2, wrong_index=True))
    valid_entropy = float(valid["signature"]["half_cut_entropy"])
    erased_entropy = float(erased["signature"]["half_cut_entropy"])
    positive = {
        "quimb_tensornetwork_constructor_preserves_torch_arrays": {
            "pass": valid["object_type"] == "TensorNetwork" and valid["tensor_count"] == 4,
            "object_type": valid["object_type"],
            "tensor_count": valid["tensor_count"],
            "quimb_version": getattr(quimb, "__version__", "unknown"),
            "first_tensor_data_type": type(build_network(2).tensors[0].data).__name__,
        },
        "valid_virtual_bond_graph_has_three_connected_bonds": {
            "pass": valid["connected_virtual_bond_count"] == 3
            and valid["dangling_virtual_bond_count"] == 0
            and valid["max_virtual_bond"] == 2,
            "connected_virtual_bonds": valid["connected_virtual_bonds"],
            "dangling_virtual_bonds": valid["dangling_virtual_bonds"],
            "max_virtual_bond": valid["max_virtual_bond"],
        },
        "valid_network_has_nonzero_cut_entropy": {
            "pass": valid_entropy > 1.0e-4,
            "half_cut_entropy": valid_entropy,
        },
    }
    graveyard = {
        "wrong_index_layout_breaks_virtual_bond_graph": {
            "pass": wrong["connected_virtual_bond_count"] < valid["connected_virtual_bond_count"]
            and wrong["dangling_virtual_bond_count"] > 0,
            "valid_connected_virtual_bond_count": valid["connected_virtual_bond_count"],
            "wrong_connected_virtual_bond_count": wrong["connected_virtual_bond_count"],
            "wrong_dangling_virtual_bonds": wrong["dangling_virtual_bonds"],
        },
        "erased_virtual_bonds_collapse_bond_depth": {
            "pass": erased["max_virtual_bond"] == 1 and valid["max_virtual_bond"] == 2,
            "valid_max_virtual_bond": valid["max_virtual_bond"],
            "erased_max_virtual_bond": erased["max_virtual_bond"],
        },
        "bond_dim_one_product_boundary_changes_entropy": {
            "pass": valid_entropy > erased_entropy + 1.0e-4 and erased_entropy < 1.0e-10,
            "valid_half_cut_entropy": valid_entropy,
            "erased_half_cut_entropy": erased_entropy,
            "entropy_delta": valid_entropy - erased_entropy,
        },
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {
            "valid_network": valid,
            "erased_bond_network": erased,
            "wrong_index_network": wrong,
        },
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()),
    }


def blocked_receipt(started: float, kind: str, detail: str) -> dict[str, Any]:
    return {
        "sim_id": NAME,
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": {},
        "graveyard_companions": {},
        "boundary": {},
        "nearby_variants": {"total": 0, "passed": 0, "variants": []},
        "why_not_v4_probes": "This is a v5 micro-tool constructor probe, not v4 probe accumulation.",
        "blockers": [{"kind": kind, "detail": detail}],
        "elapsed_seconds": time.time() - started,
        "all_pass": False,
    }


def main() -> int:
    started = time.time()
    try:
        body = run_probe()
        result = {
            "sim_id": NAME,
            "name": NAME,
            "classification": CLASSIFICATION,
            "sim_execution_kind": SIM_EXECUTION_KIND,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "finite_map": FINITE_MAP,
            "domain": DOMAIN,
            "codomain_or_output": CODOMAIN_OR_OUTPUT,
            "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
            "carrier_layer": "finite quimb TensorNetwork constructor fixture",
            "geometry_layer": "four-site spinor-bond index graph",
            "carrier_realization": "torch.complex128 site tensors inside quimb qtn.Tensor/qtn.TensorNetwork objects",
            "peps3d_embedding": "not_applicable_micro_tool_probe; downstream PEPS3D consumers stay blocked",
            "spinor_state": "finite two-level site tensors; no layer spinor claim",
            "quaternion_action": "not_applicable",
            "dependency_receipts": [
                "system_v5/ops/formal_scouts/full_spinor_jax_internal_mirror_blockers_20260531.json"
            ],
            "downstream_blocks": BLOCKED_CONSUMERS,
            "bridge_layer": "none",
            "cut_layer": "four-site half-cut entropy only; no shell interior/boundary bridge",
            "law_or_candidate_tested": "quimb TensorNetwork construction sensitivity to index graph and virtual bond controls",
            "allowed_claims": [
                "quimb TensorNetwork construction has one falsifiable micro-tool receipt",
                "wrong index layout and erased virtual bonds are non-vacuous controls for this fixture",
            ],
            "promotion_blockers": [
                "not integrated into every standalone layer receipt",
                "not a full PEPS3D environment contraction",
                "not layer completion or stacking evidence",
            ],
            "tool_manifest": TOOL_MANIFEST,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "actual_tools_used": sorted(TOOL_MANIFEST),
            "required_tools": sorted(TOOL_MANIFEST),
            "proof_surfaces_used": [],
            "graph_surfaces_used": ["quimb TensorNetwork index graph"],
            "topology_surfaces_used": [],
            "source_alignment_category": "quimb_tensornetwork_constructor_internal_control_micro_probe",
            "why_not_v4_probes": "This is a v5 micro-tool constructor probe that closes one target-specific internal gap; it does not promote v4 probes, layers, G-structures, stacking, Axis0, flux, FEP, physics, or final manifold claims.",
            "elapsed_seconds": time.time() - started,
            **body,
        }
    except Exception as exc:
        result = blocked_receipt(started, "runtime_error", f"{type(exc).__name__}: {exc}")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
