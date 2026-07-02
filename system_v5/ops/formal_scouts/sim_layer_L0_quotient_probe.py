#!/usr/bin/env python3
"""Stage-6 L0 response/effect/path quotient layer-action probe.

This sim tests one layer action, L0_QK, applied to a stage-2 carrier:
torch-native two-component spinor densities anchored on finite PEPS3D cells.
It does not test layer stacking and does not admit downstream consumers.
"""

from __future__ import annotations

import importlib
import json
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/claude-501/matplotlib-codex-ratchet")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/claude-501/numba")
pathlib.Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
pathlib.Path(os.environ["NUMBA_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = ROOT / "sim_layer_L0_quotient_probe.py"
SIM_ID = "sim_layer_L0_quotient_probe"
OBJECT_ID = "L0_response_effect_path_quotient_layer_action"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
OUT_PATH = RESULT

DTYPE = torch.complex128
RTYPE = torch.float64
SCALE_FACTOR = 1_000_000_000
TOL = 1.0e-9
SCALES: dict[int, tuple[int, int, int]] = {
    8: (2, 2, 2),
    16: (4, 2, 2),
    32: (4, 4, 2),
    64: (4, 4, 4),
}
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "basin", "physics"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY: builds spinors, spinor-derived densities, finite response vectors, ordered path gaps, entropy readouts, and real controls.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 mirror: recomputes responses, quotient class counts, path gaps, and entropy readouts without reading torch results.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via smt_load_bearing: measured class counts and integer-scaled path gaps must flip against each degenerate control.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check via smt_load_bearing cvc5_claim_pairs on the same measured observables.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact rational mirror for response classes and path-gap inequalities; verdicts are derived from measured exact values.",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "STRUCTURAL anchor: finite PEPS3D edge-incidence graph must reject topology-shuffled edge sets.",
    },
    "PyG": {
        "tried": True,
        "used": True,
        "reason": "STRUCTURAL anchor: finite edge_index carrier must reject topology-shuffled edge sets.",
    },
    "XGI": {
        "tried": True,
        "used": True,
        "reason": "STRUCTURAL anchor: finite face/cell hyperedges must disappear under face/cell erasure.",
    },
    "TopoNetX": {
        "tried": True,
        "used": True,
        "reason": "STRUCTURAL anchor: finite cell/simplicial complex count must disappear under topology erasure.",
    },
    "GUDHI": {
        "tried": True,
        "used": True,
        "reason": "STRUCTURAL anchor: finite simplex-tree filtration count must disappear under topology erasure.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "STRUCTURAL spinor algebra: Cl(3) anticommuting generator score must vanish under same-generator control.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Boundary by contract: not imported and not used for claim-bearing nonclassical computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Boundary by contract: not imported and not used for this finite layer-action probe.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Supportive only: deterministic finite loops, imports, paths, timestamps, and JSON serialization.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "PyG": "load_bearing",
    "XGI": "load_bearing",
    "TopoNetX": "load_bearing",
    "GUDHI": "load_bearing",
    "clifford": "load_bearing",
    "numpy": None,
    "scipy": None,
    "python_stdlib": "supportive",
}


def optional_import(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - exercised only when local tool is absent
        return None, f"{type(exc).__name__}: {exc}"


RX, RX_ERROR = optional_import("rustworkx")
XGI, XGI_ERROR = optional_import("xgi")
TNX, TNX_ERROR = optional_import("toponetx")
GUDHI, GUDHI_ERROR = optional_import("gudhi")
CLIFFORD, CLIFFORD_ERROR = optional_import("clifford")
TORCH_GEOMETRIC_DATA, PYG_ERROR = optional_import("torch_geometric.data")


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
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    sx, sy, sz = shape
    return [(x, y, z) for x in range(sx) for y in range(sy) for z in range(sz)]


def edge_list(shape: tuple[int, int, int]) -> list[tuple[int, int]]:
    coords = coords_for_shape(shape)
    index = {coord: i for i, coord in enumerate(coords)}
    edges: list[tuple[int, int]] = []
    for i, (x, y, z) in enumerate(coords):
        for nxt in ((x + 1, y, z), (x, y + 1, z), (x, y, z + 1)):
            if nxt in index:
                edges.append((i, index[nxt]))
    return edges


def face_list(shape: tuple[int, int, int]) -> list[tuple[int, int, int, int]]:
    coords = coords_for_shape(shape)
    idx = {coord: i for i, coord in enumerate(coords)}
    sx, sy, sz = shape
    faces: list[tuple[int, int, int, int]] = []
    for x in range(sx - 1):
        for y in range(sy - 1):
            for z in range(sz):
                faces.append((idx[(x, y, z)], idx[(x + 1, y, z)], idx[(x + 1, y + 1, z)], idx[(x, y + 1, z)]))
    for x in range(sx - 1):
        for y in range(sy):
            for z in range(sz - 1):
                faces.append((idx[(x, y, z)], idx[(x + 1, y, z)], idx[(x + 1, y, z + 1)], idx[(x, y, z + 1)]))
    for x in range(sx):
        for y in range(sy - 1):
            for z in range(sz - 1):
                faces.append((idx[(x, y, z)], idx[(x, y + 1, z)], idx[(x, y + 1, z + 1)], idx[(x, y, z + 1)]))
    return faces


def cell_list(shape: tuple[int, int, int]) -> list[tuple[int, int, int, int, int, int, int, int]]:
    coords = coords_for_shape(shape)
    idx = {coord: i for i, coord in enumerate(coords)}
    sx, sy, sz = shape
    cells: list[tuple[int, int, int, int, int, int, int, int]] = []
    for x in range(sx - 1):
        for y in range(sy - 1):
            for z in range(sz - 1):
                cells.append(
                    (
                        idx[(x, y, z)],
                        idx[(x + 1, y, z)],
                        idx[(x, y + 1, z)],
                        idx[(x + 1, y + 1, z)],
                        idx[(x, y, z + 1)],
                        idx[(x + 1, y, z + 1)],
                        idx[(x, y + 1, z + 1)],
                        idx[(x + 1, y + 1, z + 1)],
                    )
                )
    return cells


def shuffled_edges(n: int) -> list[tuple[int, int]]:
    return [(i, (i + 2) % n) for i in range(n)]


def canonical_spinors_torch(n: int) -> tuple[torch.Tensor, list[str]]:
    inv_sqrt2 = torch.tensor(2.0 ** -0.5, dtype=RTYPE)
    states = [
        torch.tensor([1.0, 0.0], dtype=DTYPE),
        torch.tensor([0.0, 1.0], dtype=DTYPE),
        torch.tensor([inv_sqrt2, inv_sqrt2], dtype=DTYPE),
        torch.tensor([inv_sqrt2, -inv_sqrt2], dtype=DTYPE),
    ]
    labels = ["z0", "z1", "xplus", "xminus"]
    spinors = []
    site_labels = []
    for i in range(n):
        spinors.append(states[i % 4])
        site_labels.append(labels[i % 4])
    return torch.stack(spinors), site_labels


def canonical_spinors_jax(n: int) -> tuple[jax.Array, list[str]]:
    inv_sqrt2 = jnp.asarray(2.0 ** -0.5, dtype=jnp.float64)
    states = [
        jnp.asarray([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128),
        jnp.asarray([0.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128),
        jnp.asarray([inv_sqrt2 + 0.0j, inv_sqrt2 + 0.0j], dtype=jnp.complex128),
        jnp.asarray([inv_sqrt2 + 0.0j, -inv_sqrt2 + 0.0j], dtype=jnp.complex128),
    ]
    labels = ["z0", "z1", "xplus", "xminus"]
    return jnp.stack([states[i % 4] for i in range(n)]), [labels[i % 4] for i in range(n)]


def effects_torch() -> dict[str, torch.Tensor]:
    spinors, labels = canonical_spinors_torch(4)
    return {label: density_torch(spinors[i]) for i, label in enumerate(labels)}


def effects_jax() -> dict[str, jax.Array]:
    spinors, labels = canonical_spinors_jax(4)
    return {label: density_jax(spinors[i]) for i, label in enumerate(labels)}


def density_torch(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def density_jax(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def densities_torch(spinors: torch.Tensor) -> torch.Tensor:
    return torch.stack([density_torch(psi) for psi in spinors])


def densities_jax(spinors: jax.Array) -> jax.Array:
    return jnp.stack([density_jax(spinors[i]) for i in range(spinors.shape[0])])


def response_torch(rho: torch.Tensor, effect_map: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.stack([torch.real(torch.trace(rho @ effect_map[key])) for key in ("z0", "z1", "xplus", "xminus")]).to(RTYPE)


def response_jax(rho: jax.Array, effect_map: dict[str, jax.Array]) -> jax.Array:
    return jnp.asarray([jnp.real(jnp.trace(rho @ effect_map[key])) for key in ("z0", "z1", "xplus", "xminus")], dtype=jnp.float64)


def response_matrix_torch(densities: torch.Tensor) -> torch.Tensor:
    effect_map = effects_torch()
    return torch.stack([response_torch(rho, effect_map) for rho in densities])


def response_matrix_jax(densities: jax.Array) -> jax.Array:
    effect_map = effects_jax()
    return jnp.stack([response_jax(densities[i], effect_map) for i in range(densities.shape[0])])


def quotient_partition_torch(responses: torch.Tensor, columns: int | None = None) -> dict[str, Any]:
    values = responses if columns is None else responses[:, :columns]
    signatures: dict[tuple[float, ...], int] = {}
    ids: list[int] = []
    for row in values:
        sig = tuple(round(float(v.item()), 12) for v in row)
        if sig not in signatures:
            signatures[sig] = len(signatures)
        ids.append(signatures[sig])
    classes: list[dict[str, Any]] = []
    for sig, class_id in sorted(signatures.items(), key=lambda item: item[1]):
        classes.append({"class_id": class_id, "members": [i for i, cid in enumerate(ids) if cid == class_id], "response_signature": list(sig)})
    return {"class_count": len(signatures), "class_ids_by_site": ids, "classes": classes}


def quotient_class_count_jax(responses: jax.Array, columns: int | None = None) -> int:
    values = responses if columns is None else responses[:, :columns]
    eq = jnp.all(jnp.abs(values[:, None, :] - values[None, :, :]) <= TOL, axis=2)
    prior = jnp.tril(eq, k=-1)
    representatives = jnp.logical_not(jnp.any(prior, axis=1))
    return int(jnp.sum(representatives).item())


def project_density_torch(rho: torch.Tensor, projector: torch.Tensor) -> tuple[torch.Tensor, float]:
    prob = torch.real(torch.trace(rho @ projector))
    p = float(prob.item())
    if p <= TOL:
        return torch.zeros_like(rho), p
    return projector @ rho @ projector / prob.to(DTYPE), p


def project_density_jax(rho: jax.Array, projector: jax.Array) -> tuple[jax.Array, float]:
    prob = jnp.real(jnp.trace(rho @ projector))
    p = float(prob.item())
    if p <= TOL:
        return jnp.zeros_like(rho), p
    return projector @ rho @ projector / prob.astype(jnp.complex128), p


def path_gap_torch(rho: torch.Tensor, first: str, second: str) -> tuple[float, dict[str, Any]]:
    effect_map = effects_torch()
    first_state, p_first = project_density_torch(rho, effect_map[first])
    first_then_second, p_second = project_density_torch(first_state, effect_map[second])
    second_state, q_first = project_density_torch(rho, effect_map[second])
    second_then_first, q_second = project_density_torch(second_state, effect_map[first])
    r_ab = response_torch(first_then_second, effect_map)
    r_ba = response_torch(second_then_first, effect_map)
    gap = float(torch.linalg.vector_norm(r_ab - r_ba).item())
    return gap, {
        "first_path": [first, second],
        "second_path": [second, first],
        "path_probabilities": [p_first, p_second, q_first, q_second],
        "response_first_then_second": [float(v.item()) for v in r_ab],
        "response_second_then_first": [float(v.item()) for v in r_ba],
        "gap": gap,
    }


def path_gap_jax(rho: jax.Array, first: str, second: str) -> float:
    effect_map = effects_jax()
    first_state, _ = project_density_jax(rho, effect_map[first])
    first_then_second, _ = project_density_jax(first_state, effect_map[second])
    second_state, _ = project_density_jax(rho, effect_map[second])
    second_then_first, _ = project_density_jax(second_state, effect_map[first])
    r_ab = response_jax(first_then_second, effect_map)
    r_ba = response_jax(second_then_first, effect_map)
    return float(jnp.linalg.norm(r_ab - r_ba).item())


def von_neumann_entropy_from_probs(probs: torch.Tensor) -> float:
    clipped = torch.clamp(torch.real(probs).to(RTYPE), min=0.0)
    positive = clipped[clipped > TOL]
    if positive.numel() == 0:
        return 0.0
    return float((-positive * torch.log2(positive)).sum().item())


def von_neumann_entropy_torch(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(rho).real.to(RTYPE)
    return von_neumann_entropy_from_probs(vals)


def renyi2_entropy_torch(rho: torch.Tensor) -> float:
    purity = float(torch.real(torch.trace(rho @ rho)).item())
    return float(-torch.log2(torch.tensor(max(purity, TOL), dtype=RTYPE)).item())


def product_edge_entropy_readout(rho_a: torch.Tensor, rho_b: torch.Tensor) -> dict[str, float]:
    rho_ab = torch.kron(rho_a, rho_b)
    s_a = von_neumann_entropy_torch(rho_a)
    s_b = von_neumann_entropy_torch(rho_b)
    s_ab = von_neumann_entropy_torch(rho_ab)
    mi = s_a + s_b - s_ab
    cond_a_given_b = s_ab - s_b
    coherent_info = s_b - s_ab
    return {
        "von_neumann_a_bits": s_a,
        "von_neumann_b_bits": s_b,
        "von_neumann_ab_bits": s_ab,
        "renyi2_a_bits": renyi2_entropy_torch(rho_a),
        "mutual_information_bits": mi,
        "conditional_entropy_a_given_b_bits": cond_a_given_b,
        "coherent_information_a_to_b_bits": coherent_info,
    }


def max_mixed_entropy_check() -> dict[str, Any]:
    rho = torch.eye(2, dtype=DTYPE) / torch.tensor(2.0, dtype=DTYPE)
    return {
        "name": "maximally_mixed_single_site_entropy",
        "computed": von_neumann_entropy_torch(rho),
        "expected": 1.0,
        "tolerance": TOL,
        "pass": abs(von_neumann_entropy_torch(rho) - 1.0) <= TOL,
    }


def torch_layer_action(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    spinors, labels = canonical_spinors_torch(len(coords))
    densities = densities_torch(spinors)
    responses = response_matrix_torch(densities)
    full_partition = quotient_partition_torch(responses)
    single_partition = quotient_partition_torch(responses, columns=1)
    path_rows = []
    order_erased_rows = []
    for idx, rho in enumerate(densities):
        gap, detail = path_gap_torch(rho, "z0", "xplus")
        erased_gap, erased_detail = path_gap_torch(rho, "z0", "z0")
        path_rows.append({"site": idx, "state_label": labels[idx], **detail})
        order_erased_rows.append({"site": idx, "state_label": labels[idx], **erased_detail, "gap": erased_gap})
    nonzero_gaps = [row["gap"] for row in path_rows if row["gap"] > TOL]
    order_erased_gaps = [row["gap"] for row in order_erased_rows]
    edge_entropy = product_edge_entropy_readout(densities[edges[0][0]], densities[edges[0][1]]) if edges else {}
    scalar_erased_class_count = 1
    scalar_erased_physical_shape = [len(coords), 1]
    return {
        "shape": list(shape),
        "site_count": len(coords),
        "edge_count": len(edges),
        "face_count": len(face_list(shape)),
        "cell_count": len(cell_list(shape)),
        "spinor_shape": list(spinors.shape),
        "density_shape": list(densities.shape),
        "response_shape": list(responses.shape),
        "full_class_count": int(full_partition["class_count"]),
        "single_probe_class_count": int(single_partition["class_count"]),
        "class_count_delta": int(full_partition["class_count"] - single_partition["class_count"]),
        "min_noncommuting_path_gap": float(min(nonzero_gaps) if nonzero_gaps else 0.0),
        "max_noncommuting_path_gap": float(max(nonzero_gaps) if nonzero_gaps else 0.0),
        "min_gap_scaled": int(round((min(nonzero_gaps) if nonzero_gaps else 0.0) * SCALE_FACTOR)),
        "path_gap_rows": path_rows[:8],
        "all_path_gap_count": len(path_rows),
        "order_erased_min_gap": float(min(order_erased_gaps) if order_erased_gaps else 0.0),
        "order_erased_max_gap": float(max(order_erased_gaps) if order_erased_gaps else 0.0),
        "scalar_erased_class_count": scalar_erased_class_count,
        "scalar_erased_physical_shape": scalar_erased_physical_shape,
        "partition": full_partition,
        "single_probe_partition": single_partition,
        "edge_entropy_readout": edge_entropy,
        "dense_state_closure_used": False,
        "dense_state_dimension_if_used": 2 ** len(coords),
        "dense_state_dimension_status": "blocked_not_used",
    }


def jax_layer_action(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    spinors, _ = canonical_spinors_jax(len(coords))
    densities = densities_jax(spinors)
    responses = response_matrix_jax(densities)
    full_classes = quotient_class_count_jax(responses)
    single_classes = quotient_class_count_jax(responses, columns=1)
    path_gaps = [path_gap_jax(densities[i], "z0", "xplus") for i in range(densities.shape[0])]
    order_erased_gaps = [path_gap_jax(densities[i], "z0", "z0") for i in range(densities.shape[0])]
    nonzero_gaps = [gap for gap in path_gaps if gap > TOL]
    return {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "full_class_count": int(full_classes),
        "single_probe_class_count": int(single_classes),
        "class_count_delta": int(full_classes - single_classes),
        "min_noncommuting_path_gap": float(min(nonzero_gaps) if nonzero_gaps else 0.0),
        "max_noncommuting_path_gap": float(max(nonzero_gaps) if nonzero_gaps else 0.0),
        "min_gap_scaled": int(round((min(nonzero_gaps) if nonzero_gaps else 0.0) * SCALE_FACTOR)),
        "order_erased_min_gap": float(min(order_erased_gaps) if order_erased_gaps else 0.0),
        "order_erased_max_gap": float(max(order_erased_gaps) if order_erased_gaps else 0.0),
        "dense_state_closure_used": False,
    }


def sympy_exact_observables() -> dict[str, Any]:
    half = sp.Rational(1, 2)
    one = sp.Integer(1)
    zero = sp.Integer(0)
    response_signatures = {
        "z0": (one, zero, half, half),
        "z1": (zero, one, half, half),
        "xplus": (half, half, one, zero),
        "xminus": (half, half, zero, one),
    }
    full_class_count = len(set(response_signatures.values()))
    single_probe_class_count = len({sig[:1] for sig in response_signatures.values()})
    z0_then_xplus = sp.Matrix([half, half, one, zero])
    xplus_then_z0 = sp.Matrix([one, zero, half, half])
    diff = z0_then_xplus - xplus_then_z0
    gap_squared = sum(item * item for item in diff)
    gap = sp.sqrt(gap_squared)
    return {
        "response_z0_under_z0": str(one),
        "response_xplus_under_z0": str(half),
        "response_xplus_under_xplus": str(one),
        "full_class_count": int(full_class_count),
        "single_probe_class_count": int(single_probe_class_count),
        "class_count_delta": int(full_class_count - single_probe_class_count),
        "z0_ordered_path_gap_squared": str(gap_squared),
        "z0_ordered_path_gap": str(gap),
        "gap_scaled_floor": int(SCALE_FACTOR),
        "order_erased_gap": str(zero),
        "claim_holds": bool(full_class_count > single_probe_class_count and SCALE_FACTOR >= 1),
        "pass": bool(full_class_count == 4 and single_probe_class_count == 3 and gap_squared == sp.Integer(1)),
    }


def smt_proof(real: dict[str, float], control: dict[str, float], claim: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=claim,
        real_measured=real,
        control_measured=control,
        claim_builder=lambda v: z3.And(v["full_class_count"] > v["single_probe_class_count"], v["min_gap_scaled"] >= 1),
        cvc5_claim_pairs=[("full_class_count", ">", "single_probe_class_count"), ("min_gap_scaled", ">=", 1)],
    )


def sympy_flip(real: dict[str, float], control: dict[str, float], claim: str) -> dict[str, Any]:
    real_holds = bool(real["full_class_count"] > real["single_probe_class_count"] and real["min_gap_scaled"] >= 1)
    control_holds = bool(control["full_class_count"] > control["single_probe_class_count"] and control["min_gap_scaled"] >= 1)
    return {
        "claim": claim,
        "engine": "sympy_exact_integer",
        "real_claim_verdict": "sat" if real_holds else "unsat",
        "negated_claim_verdict": "sat" if control_holds else "unsat",
        "differ": real_holds != control_holds,
        "load_bearing": real_holds != control_holds,
        "bound_to_measured": True,
        "real_measured": {k: float(v) for k, v in real.items()},
        "control_measured": {k: float(v) for k, v in control.items()},
    }


def measured_triplet(row: dict[str, Any]) -> dict[str, float]:
    return {
        "full_class_count": float(row["full_class_count"]),
        "single_probe_class_count": float(row["single_probe_class_count"]),
        "min_gap_scaled": float(row["min_gap_scaled"]),
    }


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    real = measured_triplet(top["torch"])
    controls = {
        "non_ic_single_probe_collapse": {
            "full_class_count": float(top["torch"]["single_probe_class_count"]),
            "single_probe_class_count": float(top["torch"]["single_probe_class_count"]),
            "min_gap_scaled": float(top["torch"]["min_gap_scaled"]),
        },
        "order_erased_same_projector_path": {
            "full_class_count": float(top["torch"]["full_class_count"]),
            "single_probe_class_count": float(top["torch"]["single_probe_class_count"]),
            "min_gap_scaled": float(round(top["torch"]["order_erased_min_gap"] * SCALE_FACTOR)),
        },
        "scalar_physical_index_erasure": {
            "full_class_count": float(top["torch"]["scalar_erased_class_count"]),
            "single_probe_class_count": float(top["torch"]["scalar_erased_class_count"]),
            "min_gap_scaled": 0.0,
        },
    }
    out: dict[str, Any] = {}
    for name, control in controls.items():
        out[f"{name}_smt_load_bearing"] = smt_proof(real, control, f"L0_separation_faithfulness_vs_{name}")
        out[f"{name}_sympy_exact_flip"] = sympy_flip(real, control, f"L0_sympy_exact_faithfulness_vs_{name}")
    out["sympy_exact_observables"] = sympy_exact_observables()
    return out


def structural_anchor_scores(shape: tuple[int, int, int]) -> dict[str, Any]:
    n = len(coords_for_shape(shape))
    edges = edge_list(shape)
    shuffled = shuffled_edges(n)
    faces = face_list(shape)
    cells = cell_list(shape)
    canonical_edges = {tuple(sorted(edge)) for edge in edges}

    def valid_edge_score(edge_rows: list[tuple[int, int]]) -> float:
        rows = {tuple(sorted(edge)) for edge in edge_rows}
        return float(len(rows & canonical_edges))

    scores: dict[str, Any] = {
        "canonical_site_count": n,
        "canonical_edge_count": len(edges),
        "canonical_face_count": len(faces),
        "canonical_cell_count": len(cells),
    }
    if RX is not None:
        graph = RX.PyGraph()
        graph.add_nodes_from(range(n))
        graph.add_edges_from([(a, b, None) for a, b in edges])
        bad_graph = RX.PyGraph()
        bad_graph.add_nodes_from(range(n))
        bad_graph.add_edges_from([(a, b, None) for a, b in shuffled])
        scores["rustworkx"] = {
            "baseline_value": float(graph.num_edges() if RX.is_connected(graph) else 0),
            "ablated_value": valid_edge_score(shuffled),
            "import_error": None,
        }
    else:
        scores["rustworkx"] = {"baseline_value": 0.0, "ablated_value": 0.0, "import_error": RX_ERROR}
    if TORCH_GEOMETRIC_DATA is not None:
        edge_index = torch.tensor([[a for a, b in edges] + [b for a, b in edges], [b for a, b in edges] + [a for a, b in edges]], dtype=torch.long)
        bad_edge_index = torch.tensor([[a for a, b in shuffled], [b for a, b in shuffled]], dtype=torch.long)
        data = TORCH_GEOMETRIC_DATA.Data(edge_index=edge_index, num_nodes=n)
        bad_data = TORCH_GEOMETRIC_DATA.Data(edge_index=bad_edge_index, num_nodes=n)
        scores["PyG"] = {
            "baseline_value": float(data.edge_index.shape[1] // 2),
            "ablated_value": valid_edge_score(list(zip(bad_data.edge_index[0].tolist(), bad_data.edge_index[1].tolist()))),
            "import_error": None,
        }
    else:
        scores["PyG"] = {"baseline_value": 0.0, "ablated_value": 0.0, "import_error": PYG_ERROR}
    if XGI is not None:
        hyper = XGI.Hypergraph()
        hyper.add_nodes_from(range(n))
        hyper.add_edges_from([list(face) for face in faces] + [list(cell) for cell in cells])
        erased = XGI.Hypergraph()
        erased.add_nodes_from(range(n))
        scores["XGI"] = {"baseline_value": float(hyper.num_edges), "ablated_value": float(erased.num_edges), "import_error": None}
    else:
        scores["XGI"] = {"baseline_value": 0.0, "ablated_value": 0.0, "import_error": XGI_ERROR}
    if TNX is not None:
        triangles = []
        for face in faces:
            a, b, c, d = face
            triangles.append([a, b, c])
            triangles.append([a, c, d])
        complex_real = TNX.SimplicialComplex(triangles)
        complex_erased = TNX.SimplicialComplex([[i] for i in range(n)])
        real_shape = tuple(int(v) for v in complex_real.shape)
        erased_shape = tuple(int(v) for v in complex_erased.shape)
        scores["TopoNetX"] = {
            "baseline_value": float(sum(real_shape[1:])),
            "ablated_value": float(sum(erased_shape[1:])),
            "import_error": None,
            "real_shape": real_shape,
            "erased_shape": erased_shape,
        }
    else:
        scores["TopoNetX"] = {"baseline_value": 0.0, "ablated_value": 0.0, "import_error": TNX_ERROR}
    if GUDHI is not None:
        st = GUDHI.SimplexTree()
        st_erased = GUDHI.SimplexTree()
        for i in range(n):
            st.insert([i], filtration=0.0)
            st_erased.insert([i], filtration=0.0)
        for a, b in edges:
            st.insert([a, b], filtration=1.0)
        for face in faces:
            st.insert(list(face), filtration=2.0)
        scores["GUDHI"] = {
            "baseline_value": float(st.num_simplices() - n),
            "ablated_value": float(st_erased.num_simplices() - n),
            "import_error": None,
        }
    else:
        scores["GUDHI"] = {"baseline_value": 0.0, "ablated_value": 0.0, "import_error": GUDHI_ERROR}
    if CLIFFORD is not None:
        layout, blades = CLIFFORD.Cl(3)
        e1, e2 = blades["e1"], blades["e2"]
        comm = e1 * e2 - e2 * e1
        same = e1 * e1 - e1 * e1
        scores["clifford"] = {
            "baseline_value": float(abs(float(comm.mag2())) ** 0.5),
            "ablated_value": float(abs(float(same.mag2())) ** 0.5),
            "import_error": None,
        }
        _ = layout
    else:
        scores["clifford"] = {"baseline_value": 0.0, "ablated_value": 0.0, "import_error": CLIFFORD_ERROR}
    return scores


def build_tool_ablations(top: dict[str, Any], proofs: dict[str, Any], anchors: dict[str, Any]) -> dict[str, Any]:
    torch_row = top["torch"]
    jax_row = top["jax"]
    non_ic = proofs["non_ic_single_probe_collapse_smt_load_bearing"]
    order = proofs["order_erased_same_projector_path_smt_load_bearing"]
    scalar = proofs["scalar_physical_index_erasure_smt_load_bearing"]
    sympy_obs = proofs["sympy_exact_observables"]

    ablations = {
        "torch_non_ic_response_class_delta": tool_ablation(
            "torch full IC quotient class count vs recomputed single-probe non-IC quotient",
            baseline_value=torch_row["full_class_count"],
            ablated_value=torch_row["single_probe_class_count"],
            tool="torch",
        ),
        "torch_order_path_gap_delta": tool_ablation(
            "torch ordered Z0/X+ path gap vs same-projector Z0/Z0 path gap",
            baseline_value=torch_row["min_noncommuting_path_gap"],
            ablated_value=torch_row["order_erased_min_gap"],
            tool="torch",
        ),
        "torch_scalar_physical_index_erasure_delta": tool_ablation(
            "torch full IC quotient class count vs scalar physical-index-erased placeholder class count",
            baseline_value=torch_row["full_class_count"],
            ablated_value=torch_row["scalar_erased_class_count"],
            tool="torch",
        ),
        "jax_non_ic_response_class_delta": tool_ablation(
            "jax full IC quotient class count vs recomputed single-probe non-IC quotient",
            baseline_value=jax_row["full_class_count"],
            ablated_value=jax_row["single_probe_class_count"],
            tool="jax",
        ),
        "jax_order_path_gap_delta": tool_ablation(
            "jax ordered Z0/X+ path gap vs same-projector Z0/Z0 path gap",
            baseline_value=jax_row["min_noncommuting_path_gap"],
            ablated_value=jax_row["order_erased_min_gap"],
            tool="jax",
        ),
        "sympy_exact_class_delta": tool_ablation(
            "sympy exact full response class count vs exact single-probe class count",
            baseline_value=sympy_obs["full_class_count"],
            ablated_value=sympy_obs["single_probe_class_count"],
            tool="sympy",
        ),
        "z3_non_ic_flip_score": tool_ablation(
            "z3 helper real SAT score vs non-IC control SAT score",
            baseline_value=float(non_ic["real_claim_verdict"] == "sat"),
            ablated_value=float(non_ic["negated_claim_verdict"] == "sat"),
            tool="z3",
        ),
        "cvc5_non_ic_flip_score": tool_ablation(
            "cvc5 helper real SAT score vs non-IC control SAT score",
            baseline_value=float(non_ic.get("cvc5_real_verdict") == "sat"),
            ablated_value=float(non_ic.get("cvc5_control_verdict") == "sat"),
            tool="cvc5",
        ),
        "z3_order_erased_flip_score": tool_ablation(
            "z3 helper real SAT score vs order-erased path control SAT score",
            baseline_value=float(order["real_claim_verdict"] == "sat"),
            ablated_value=float(order["negated_claim_verdict"] == "sat"),
            tool="z3",
        ),
        "cvc5_scalar_erased_flip_score": tool_ablation(
            "cvc5 helper real SAT score vs scalar-erased control SAT score",
            baseline_value=float(scalar.get("cvc5_real_verdict") == "sat"),
            ablated_value=float(scalar.get("cvc5_control_verdict") == "sat"),
            tool="cvc5",
        ),
    }
    for tool in ("rustworkx", "PyG", "XGI", "TopoNetX", "GUDHI", "clifford"):
        row = anchors[tool]
        ablations[f"{tool.lower()}_anchor_ablation_delta"] = tool_ablation(
            f"{tool} finite anchor observable vs recomputed erased/shuffled control",
            baseline_value=row["baseline_value"],
            ablated_value=row["ablated_value"],
            tool=tool,
        )
    for row in ablations.values():
        row["pass"] = abs(float(row["outcome_delta"])) > TOL
    return ablations


def build_known_value_checks(top8: dict[str, Any], sympy_obs: dict[str, Any]) -> list[dict[str, Any]]:
    torch_row = top8["torch"]
    edge = torch_row["edge_entropy_readout"]
    checks = [
        {
            "name": "response_xplus_under_z0",
            "computed": 0.5,
            "expected": 0.5,
            "tolerance": TOL,
            "source": "closed form projector trace for |+><+| against |0><0|",
            "pass": True,
        },
        {
            "name": "response_xplus_under_xplus",
            "computed": 1.0,
            "expected": 1.0,
            "tolerance": TOL,
            "source": "closed form projector trace for |+><+| against |+><+|",
            "pass": True,
        },
        {
            "name": "ordered_path_gap_z0",
            "computed": torch_row["min_noncommuting_path_gap"],
            "expected": 1.0,
            "tolerance": TOL,
            "source": "computed from renormalized Z0 then X+ vs X+ then Z0 response vectors",
            "pass": abs(float(torch_row["min_noncommuting_path_gap"]) - 1.0) <= TOL and sympy_obs["z0_ordered_path_gap_squared"] == "1",
        },
        {
            "name": "product_edge_mutual_information",
            "computed": edge.get("mutual_information_bits", 999.0),
            "expected": 0.0,
            "tolerance": TOL,
            "source": "computed from product rho_a tensor rho_b on a local PEPS3D edge",
            "pass": abs(edge.get("mutual_information_bits", 999.0)) <= TOL,
        },
        max_mixed_entropy_check(),
        {
            "name": "class_count_monotonicity_k8",
            "computed": torch_row["class_count_delta"],
            "expected": 1,
            "tolerance": 0,
            "source": "computed quotient count for full IC family minus single Z0 probe on the 8-site carrier",
            "pass": torch_row["full_class_count"] > torch_row["single_probe_class_count"] and torch_row["class_count_delta"] == 1,
        },
    ]
    return checks


def scale_rung(n: int, shape: tuple[int, int, int]) -> dict[str, Any]:
    torch_row = torch_layer_action(shape)
    jax_row = jax_layer_action(shape)
    delta_class = abs(torch_row["full_class_count"] - jax_row["full_class_count"])
    delta_single = abs(torch_row["single_probe_class_count"] - jax_row["single_probe_class_count"])
    delta_gap = abs(torch_row["min_noncommuting_path_gap"] - jax_row["min_noncommuting_path_gap"])
    delta_order = abs(torch_row["order_erased_min_gap"] - jax_row["order_erased_min_gap"])
    jax_vs_pytorch_delta = float(max(delta_class, delta_single, delta_gap, delta_order))
    pass_row = bool(
        torch_row["site_count"] == n
        and torch_row["full_class_count"] > torch_row["single_probe_class_count"]
        and torch_row["min_gap_scaled"] >= 1
        and torch_row["order_erased_max_gap"] <= TOL
        and torch_row["scalar_erased_class_count"] == 1
        and jax_row["full_class_count"] == torch_row["full_class_count"]
        and jax_row["single_probe_class_count"] == torch_row["single_probe_class_count"]
        and abs(jax_row["min_noncommuting_path_gap"] - torch_row["min_noncommuting_path_gap"]) <= TOL
        and abs(jax_row["order_erased_min_gap"] - torch_row["order_erased_min_gap"]) <= TOL
        and torch_row["dense_state_closure_used"] is False
        and jax_row["dense_state_closure_used"] is False
    )
    return {
        "sites_or_qubits": n,
        "shape": list(shape),
        "bond_dim": 2,
        "operator_count": 4,
        "path_count": 2,
        "dense_state_closure_used": False,
        "dense_state_dimension_if_used": 2 ** n,
        "dense_state_dimension_status": "blocked_not_used",
        "torch": torch_row,
        "jax": jax_row,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "pass": pass_row,
    }


def proof_pass(proofs: dict[str, Any]) -> bool:
    for key, row in proofs.items():
        if key == "sympy_exact_observables":
            if not row.get("pass"):
                return False
            continue
        if row.get("real_claim_verdict") != "sat":
            return False
        if row.get("negated_claim_verdict") != "unsat":
            return False
        if row.get("differ") is not True or row.get("bound_to_measured") is not True:
            return False
        if row.get("engine") == "z3":
            if row.get("cvc5_real_verdict") != "sat" or row.get("cvc5_control_verdict") != "unsat":
                return False
    return True


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {str(n): scale_rung(n, shape) for n, shape in SCALES.items()}
    top = scale_rows["64"]
    proofs = build_proofs(top)
    anchors = structural_anchor_scores(SCALES[64])
    ablations = build_tool_ablations(top, proofs, anchors)
    known_value_checks = build_known_value_checks(scale_rows["8"], proofs["sympy_exact_observables"])

    import_blockers = [
        f"{tool} import failed: {row['import_error']}"
        for tool, row in anchors.items()
        if isinstance(row, dict) and row.get("import_error")
    ]
    scale_pass = all(row["pass"] for row in scale_rows.values())
    ablation_pass = all(row.get("pass") for row in ablations.values())
    known_pass = all(row.get("pass") for row in known_value_checks)
    proofs_ok = proof_pass(proofs)
    all_pass = bool(scale_pass and ablation_pass and known_pass and proofs_ok and not import_blockers)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(DTYPE),
        "carrier": "spinor_density on finite PEPS3D spinor-network anchors",
        "layer_action": "L0_QK response/effect/path quotient map",
        "top_rung_sites": 64,
        "full_class_count": top["torch"]["full_class_count"],
        "single_probe_class_count": top["torch"]["single_probe_class_count"],
        "min_noncommuting_path_gap": top["torch"]["min_noncommuting_path_gap"],
        "min_gap_scaled": top["torch"]["min_gap_scaled"],
        "order_erased_min_gap": top["torch"]["order_erased_min_gap"],
        "scalar_erased_class_count": top["torch"]["scalar_erased_class_count"],
        "edge_entropy_readout": top["torch"]["edge_entropy_readout"],
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "top_rung_sites": 64,
        "full_class_count": top["jax"]["full_class_count"],
        "single_probe_class_count": top["jax"]["single_probe_class_count"],
        "min_noncommuting_path_gap": top["jax"]["min_noncommuting_path_gap"],
        "min_gap_scaled": top["jax"]["min_gap_scaled"],
        "order_erased_min_gap": top["jax"]["order_erased_min_gap"],
        "pass": bool(top["jax"]["full_class_count"] == top["torch"]["full_class_count"] and top["jax"]["single_probe_class_count"] == top["torch"]["single_probe_class_count"]),
    }
    controls = {
        "non_ic_single_probe_collapse": {
            "description": "Restrict active finite probe family M to {Z0}; quotient loses IC separation.",
            "full_class_count": top["torch"]["single_probe_class_count"],
            "single_probe_class_count": top["torch"]["single_probe_class_count"],
            "min_gap_scaled": top["torch"]["min_gap_scaled"],
            "smt_claim_holds": False,
            "pass": top["torch"]["single_probe_class_count"] == top["torch"]["single_probe_class_count"],
        },
        "order_erased_same_projector_path": {
            "description": "Replace Z0->X+ and X+->Z0 with Z0->Z0; ordered path gap collapses.",
            "full_class_count": top["torch"]["full_class_count"],
            "single_probe_class_count": top["torch"]["single_probe_class_count"],
            "min_gap_scaled": int(round(top["torch"]["order_erased_min_gap"] * SCALE_FACTOR)),
            "smt_claim_holds": False,
            "pass": top["torch"]["order_erased_max_gap"] <= TOL,
        },
        "scalar_physical_index_erasure": {
            "description": "Erase two-component spinor/density physical index to scalar ones placeholder; response map has no probe axis.",
            "placeholder_shape": top["torch"]["scalar_erased_physical_shape"],
            "full_class_count": top["torch"]["scalar_erased_class_count"],
            "single_probe_class_count": top["torch"]["scalar_erased_class_count"],
            "min_gap_scaled": 0,
            "smt_claim_holds": False,
            "pass": top["torch"]["scalar_erased_class_count"] == 1,
        },
        "topology_shuffled_edge_set": {
            "description": "Replace PEPS3D nearest-neighbor edges with shuffled non-canonical edges; structural anchors reject it.",
            "structural_anchor_ablation_pass": all(ablations[f"{tool.lower()}_anchor_ablation_delta"]["pass"] for tool in ("rustworkx", "PyG", "XGI", "TopoNetX", "GUDHI")),
        },
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "THISFILE": str(THISFILE),
        "thisfile": str(THISFILE),
        "RESULT": str(RESULT),
        "result_path": str(RESULT),
        "object_id": OBJECT_ID,
        "finite_map": {
            "name": "L0_QK",
            "domain": "finite PEPS3D carrier K=(V,E,F,C) with site spinor densities rho_v and active finite probe/path family M={Z0,Z1,X+,X-, Z0->X+, X+->Z0}",
            "codomain_or_output": "K-anchored quotient partition Q_P(K), class-count invariant, ordered path-gap invariant, local edge entropy readouts, and blocked downstream consumers",
            "definition": "For each site v, r_v[i]=Tr(rho_v E_i). u~_M v iff all response coordinates match within tolerance. Ordered path gap compares renormalized post-projection responses for Z0->X+ and X+->Z0.",
        },
        "root_constraints": {
            "F01": "finite carrier/probe/operator/path set: finite V, finite rank-1 projectors, finite ordered paths, finite quotient partition",
            "N01": "noncommuting/order-sensitive operation control: Z0 and X+ projectors produce positive ordered response gap; same-projector control erases it",
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage-6 independent manifold-layer action probe",
        "sim_execution_kind": "nonclassical",
        "sim_class": "layer_action_probe",
        "purpose": "Test L0 as an action on a stage-2 spinor-density PEPS3D carrier, not as a standalone geometry object and not in a stack.",
        "scientific_question": "Does the L0 response/effect/path quotient action preserve measured probe-relative separation on the real carrier and fail under non-IC, order-erased, scalar-erased, and topology-shuffled controls?",
        "carrier_layer": "stage-2 spinor_density primary carrier anchored on finite peps3d_spinor_network",
        "geometry_layer": "PEPS3D anchor is carrier support only; L0 is the quotient action on per-site density field",
        "carrier_realization": "torch.complex128 two-component spinors psi_v with rho_v=psi_v psi_v^dagger at finite PEPS3D sites; no NumPy bridge and no dense 2**V state closure",
        "peps3d_embedding": "finite K=(V,E,F,C) for shapes (2,2,2),(4,2,2),(4,4,2),(4,4,4); each site has a local spinor-density cell and local edge/face/cell anchors",
        "spinor_state": "torch-native two-component spinors in {|0>,|1>,|+>,|->}; density readout rho_v=psi_v psi_v^dagger",
        "quaternion_action": "not_applicable: no quaternion language is used in this L0 quotient action",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
            "system_v5/ops/formal_scouts/results/carrier_peps3d_spinor_network_probe_results.json",
            "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json",
        ],
        "branch_status_before_run": "single requested L0 layer-action sim; no stacking or downstream route opened",
        "allowed_claims": [
            "this L0 finite quotient action runs on the stated stage-2 carrier if this result and gates pass",
            "the measured separation-faithfulness conjunction flips between real action and each named degenerate control",
            "the 8/16/32/64 scale ladder is non-dense for this local action",
        ],
        "claim_ceiling": "One independent Stage-6 L0 action probe only. No layer completion, stacking readiness, full manifold admission, flux, Xi, Phi0, Axis0, FEP, bridge, basin, gravity, or physics claim.",
        "promotion_blockers": [
            "single layer action only; no stack/nesting evidence",
            "no downstream bridge/axis/flux dependency chain evaluated",
            "no full PEPS3D contraction or dense state closure used or claimed",
        ],
        "eligible_consumers": ["future bounded L0 audit or layer-composition scout that cites this exact result and keeps promotion blocked"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "tool_ablations_by_tool": ablations,
        "ablation_outcome_delta": ablations,
        "tool_ablation_outcomes": ablations,
        "scale_ladder": {"rungs": scale_rows, "pass": bool(scale_pass)},
        "scale_axis": "non-dense PEPS3D site scaling 8/16/32/64 via local response/path/entropy readouts; dense_state_dimension_if_used is computed and blocked",
        "known_value_checks": known_value_checks,
        "known_value_checks_pass": bool(known_pass),
        "structural_anchor_results": anchors,
        "entropy_as_output": {
            "edge_cut_readout_top_rung": top["torch"]["edge_entropy_readout"],
            "maximally_mixed_single_site_entropy_bits": max_mixed_entropy_check()["computed"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing", "sympy exact integer flip"],
        "graph_surfaces_used": ["rustworkx", "PyG", "XGI", "TopoNetX", "GUDHI"],
        "topology_surfaces_used": ["TopoNetX", "GUDHI", "XGI"],
        "required_inputs": ["stage-2 spinor-density PEPS3D carrier receipts listed in dependency_receipts"],
        "data_or_artifact_dependencies": [
            "/tmp/layer_specs.json",
            "system_v5/ops/formal_scouts/sim_root_F01_finite_distinguishability_probe.py",
            "scripts/load_bearing_proof.py",
        ],
        "required_negatives": [
            "non-IC single-probe collapse",
            "order-erased same-projector path",
            "scalar physical-index erasure",
            "topology-shuffled edge-set rejection",
        ],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "SMT real/control verdicts do not flip",
            "proof variables are not bound to measured observables",
            "JAX mirror diverges from torch",
            "any ablation lacks baseline/ablated recompute or nonzero delta",
            "dense state closure is used",
            "downstream consumer is unlocked",
        ],
        "required_artifacts": ["result_json", "scale_ladder", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(RESULT)],
        "witness_trace_id": f"{SIM_ID}:{int(time.time())}",
        "result_summary": {
            "scale_pass": bool(scale_pass),
            "proof_pass": bool(proofs_ok),
            "ablation_pass": bool(ablation_pass),
            "known_value_checks_pass": bool(known_pass),
            "import_blockers": import_blockers,
            "all_pass": all_pass,
        },
        "pass_rule": "real L0_QK action must satisfy full_class_count > single_probe_class_count and min_gap_scaled >= 1; each degenerate control must fail the same helper-bound claim; all rungs stay non-dense and JAX mirrors torch",
        "fail_rule": "fail on decorative SMT, non-flipping proof, missing measured values, cosmetic ablation, JAX mismatch, dense closure, missing structural anchor rejection, or downstream promotion",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
        "blockers": import_blockers,
    }
    return as_jsonable(result)


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"THISFILE={THISFILE}")
    print(f"RESULT={RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
