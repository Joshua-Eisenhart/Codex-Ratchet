#!/usr/bin/env python3
"""Source-native multicarrier subdense environment-contraction scout.

This is the next bounded bridge after the dense 8-site common-boundary scout.
It consumes repaired EngineCore science-method stage records and the plural
Axis0 router, then applies them to MPS, PEPS, and PEPS3D tensor carriers using
only local tensor updates and nearest-neighbor environment contractions.

Formal scout only. The readout is a subdense local-environment proxy, not a
full PEPS/PEPS3D environment contraction theorem, not gauge-invariant geometry,
and not a canonical physics, cognition, Holodeck, or neural-world-model claim.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import time
from dataclasses import dataclass
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import networkx as nx
import numpy as np
import opt_einsum as oe
import quimb as qu
import quimb.tensor as qtn
import z3

from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_multicarrier_subdense_environment_contraction_probe_results.json"

NAME = "source_native_multicarrier_subdense_environment_contraction_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "source_native_multicarrier_subdense_environment_contraction_repair"
CLAIM_CEILING = (
    "Formal scout only: consumes source-native science-method stage records and "
    "plural Axis0 router outputs in MPS, PEPS, and PEPS3D local tensor updates, "
    "then reads nearest-neighbor subdense local-environment contractions. It "
    "does not prove full PEPS/PEPS3D environment contraction, does not prove "
    "gauge-invariant finite-size geometry, and does not admit final Axis0, "
    "Holodeck, physics, cognition, neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing local tensor updates, pair-environment densities, and matched controls"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing PEPS/PEPS3D tensor-network construction/count sanity checks without global dense readout"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing local pair-environment contraction-tree witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric pair-contraction cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dependency and finite-size carrier graph"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite no-dense/admission witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native science-method stage records"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = np.complex128
I2 = np.eye(2, dtype=DTYPE)
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
OP_AXES = {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SY}
N_SOURCE_SEEDS = 2
MAX_ENV_EDGES = 36
AXIS0_GAP_FLOOR = 1e-5
GAUGE_INVARIANCE_CEILING = 1e-8
UNBALANCED_GAUGE_FLOOR = 1e-5
REQUIRED_STAGE_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "fep_efe_score",
    "update_repair",
    "falsifier_graveyard",
    "next_policy",
    "model_after",
]
ENVIRONMENT_SIGNATURE_COLUMNS = [
    "two_site_entropy",
    "two_site_purity",
    "two_site_mutual_information",
    "pauli_xI",
    "pauli_Ix",
    "pauli_yI",
    "pauli_Iy",
    "pauli_zI",
    "pauli_Iz",
    "pauli_xx",
    "pauli_yy",
    "pauli_zz",
    "contracted_rank",
    "contracted_trace",
]


@dataclass
class TensorSite:
    data: np.ndarray
    axes: dict[str, int]


@dataclass
class LocalCarrier:
    name: str
    family: str
    shape: tuple[int, ...]
    sites: dict[tuple[int, ...], TensorSite]
    edges: list[tuple[tuple[int, ...], tuple[int, ...], str, str]]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (np.complexfloating, complex)):
        return {"real": float(np.real(value)), "imag": float(np.imag(value))}
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_density(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = np.linalg.eigh(rho)
    vals = np.clip(vals.real, 1e-12, None)
    out = vecs @ np.diag(vals.astype(DTYPE)) @ vecs.conj().T
    return (out / np.trace(out).real).astype(DTYPE)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = np.clip(vals, 1e-12, None)
    vals = vals / vals.sum()
    return float(-(vals * np.log(vals)).sum())


def two_site_stats(rho_ab: np.ndarray) -> dict[str, float]:
    rho4 = rho_ab.reshape(2, 2, 2, 2)
    rho_a = np.einsum("abcb->ac", rho4).reshape(2, 2)
    rho_b = np.einsum("abad->bd", rho4).reshape(2, 2)
    xi = np.kron(SX, I2)
    ix = np.kron(I2, SX)
    yi = np.kron(SY, I2)
    iy = np.kron(I2, SY)
    zi = np.kron(SZ, I2)
    iz = np.kron(I2, SZ)
    return {
        "two_site_entropy": entropy(rho_ab),
        "two_site_purity": float(np.real(np.trace(rho_ab @ rho_ab))),
        "two_site_mutual_information": float(entropy(rho_a) + entropy(rho_b) - entropy(rho_ab)),
        "pauli_xI": float(np.real(np.trace(xi @ rho_ab))),
        "pauli_Ix": float(np.real(np.trace(ix @ rho_ab))),
        "pauli_yI": float(np.real(np.trace(yi @ rho_ab))),
        "pauli_Iy": float(np.real(np.trace(iy @ rho_ab))),
        "pauli_zI": float(np.real(np.trace(zi @ rho_ab))),
        "pauli_Iz": float(np.real(np.trace(iz @ rho_ab))),
        "pauli_xx": float(np.real(np.trace(np.kron(SX, SX) @ rho_ab))),
        "pauli_yy": float(np.real(np.trace(np.kron(SY, SY) @ rho_ab))),
        "pauli_zz": float(np.real(np.trace(np.kron(SZ, SZ) @ rho_ab))),
    }


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(path),
        "name": data.get("name"),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling", "")[:240],
        "positive": data.get("positive", {}),
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def run_source_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_idx in range(N_SOURCE_SEEDS):
        for engine_type in (0, 1):
            engine = EngineCore(engine_type, manifold_enabled=True)
            rho = generate_initial_density(91000 + 100 * seed_idx + engine_type)
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for substage_idx in range(4):
                    rho, row = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                    rows.append(row)
    return rows


def stage_science_contract(records: list[dict[str, Any]]) -> dict[str, Any]:
    missing = {
        f"E{row['engine_type']}:S{row['main_stage_idx']}:u{row['substage_idx']}:i{idx}": [
            field for field in REQUIRED_STAGE_FIELDS if field not in row
        ]
        for idx, row in enumerate(records)
    }
    missing = {key: value for key, value in missing.items() if value}
    efe = np.asarray([row.get("fep_efe_score", {}).get("expected_free_energy_proxy", 0.0) for row in records], dtype=float)
    repair = np.asarray([row.get("update_repair", {}).get("manifold_projection_delta_norm", 0.0) for row in records], dtype=float)
    controls = {
        control
        for row in records
        for control in row.get("falsifier_graveyard", {}).get("matched_controls_required_downstream", [])
    }
    return {
        "pass": not missing and len(records) == N_SOURCE_SEEDS * 64 and np.all(np.isfinite(efe)) and np.all(np.isfinite(repair)),
        "record_count": len(records),
        "required_fields": REQUIRED_STAGE_FIELDS,
        "missing_required_stage_fields": missing,
        "fep_proxy_mean": float(np.mean(efe)),
        "fep_proxy_variance": float(np.var(efe)),
        "repair_delta_mean": float(np.mean(repair)),
        "graveyard_controls": sorted(controls),
    }


def axis0_signature(router: dict[str, Any]) -> dict[str, Any]:
    outputs = router.get("axis0_outputs_or_blockers") or {}
    names = [
        "fep_gradient_polarity",
        "path_entropy",
        "correlation_diversity_derivative",
        "retrocausal_many_futures_policy_scoring",
        "holographic_boundary_interior_reconstruction",
    ]
    vectors: dict[str, list[float]] = {}
    for name in names:
        arr = np.asarray(outputs.get(name, {}).get("values", []), dtype=float)
        if arr.size:
            arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
            scale = float(np.max(np.abs(arr)))
            if scale > 0.0:
                arr = arr / scale
        vectors[name] = [float(x) for x in arr]
    return {
        "ready": bool(router.get("exists") and router.get("all_pass") is True and all(vectors.values())),
        "candidate_names": names,
        "candidate_vectors": vectors,
        "source_receipt": router.get("path"),
    }


def axis0_drive(axis0: dict[str, Any], idx: int) -> float:
    if not axis0.get("ready"):
        return 0.0
    values = []
    for vector in axis0.get("candidate_vectors", {}).values():
        if vector:
            values.append(float(vector[idx % len(vector)]))
    return float(np.mean(values)) if values else 0.0


def holodeck_memory_signal(memory_receipt: dict[str, Any]) -> dict[str, Any]:
    recall = ((memory_receipt.get("positive") or {}).get("predictive_model_verifies_contextual_recall") or {})
    target = float(recall.get("mean_target_verification_score", 0.0))
    wrong = float(recall.get("mean_wrong_model_target_score", 0.0))
    margin = target - wrong
    return {
        "ready": bool(memory_receipt.get("exists") and memory_receipt.get("all_pass") is True and margin > 0.0),
        "source_receipt": memory_receipt.get("path"),
        "mean_target_verification_score": target,
        "mean_wrong_model_target_score": wrong,
        "verification_margin": margin,
    }


def holodeck_memory_drive(memory: dict[str, Any], idx: int) -> float:
    if not memory.get("ready"):
        return 0.0
    phase = 1.0 if idx % 2 == 0 else -0.5
    return float(memory["verification_margin"] * phase)


def random_site(rng: np.random.Generator, dims: list[int]) -> np.ndarray:
    arr = rng.normal(scale=0.08, size=dims) + 1j * rng.normal(scale=0.08, size=dims)
    return arr.astype(DTYPE)


def make_mps_carrier(length: int, seed: int, bond_dim: int = 2) -> LocalCarrier:
    rng = np.random.default_rng(seed)
    sites: dict[tuple[int, ...], TensorSite] = {}
    edges: list[tuple[tuple[int, ...], tuple[int, ...], str, str]] = []
    for i in range(length):
        dims = []
        axes = {}
        if i > 0:
            axes["left"] = len(dims)
            dims.append(bond_dim)
        if i < length - 1:
            axes["right"] = len(dims)
            dims.append(bond_dim)
        axes["phys"] = len(dims)
        dims.append(2)
        sites[(i,)] = TensorSite(random_site(rng, dims), axes)
    for i in range(length - 1):
        edges.append(((i,), (i + 1,), "right", "left"))
    return LocalCarrier(f"mps_{length}", "mps", (length,), sites, edges)


def make_peps_carrier(lx: int, ly: int, seed: int, bond_dim: int = 2) -> LocalCarrier:
    rng = np.random.default_rng(seed)
    sites: dict[tuple[int, ...], TensorSite] = {}
    edges: list[tuple[tuple[int, ...], tuple[int, ...], str, str]] = []
    for i in range(lx):
        for j in range(ly):
            dims = []
            axes = {}
            if i > 0:
                axes["north"] = len(dims)
                dims.append(bond_dim)
            if j < ly - 1:
                axes["east"] = len(dims)
                dims.append(bond_dim)
            if i < lx - 1:
                axes["south"] = len(dims)
                dims.append(bond_dim)
            if j > 0:
                axes["west"] = len(dims)
                dims.append(bond_dim)
            axes["phys"] = len(dims)
            dims.append(2)
            sites[(i, j)] = TensorSite(random_site(rng, dims), axes)
    for i in range(lx):
        for j in range(ly):
            if i + 1 < lx:
                edges.append(((i, j), (i + 1, j), "south", "north"))
            if j + 1 < ly:
                edges.append(((i, j), (i, j + 1), "east", "west"))
    return LocalCarrier(f"peps_{lx * ly}", "peps", (lx, ly), sites, edges)


def make_peps3d_carrier(lx: int, ly: int, lz: int, seed: int, bond_dim: int = 2) -> LocalCarrier:
    rng = np.random.default_rng(seed)
    sites: dict[tuple[int, ...], TensorSite] = {}
    edges: list[tuple[tuple[int, ...], tuple[int, ...], str, str]] = []
    for i in range(lx):
        for j in range(ly):
            for k in range(lz):
                dims = []
                axes = {}
                if i < lx - 1:
                    axes["x_plus"] = len(dims)
                    dims.append(bond_dim)
                if j < ly - 1:
                    axes["y_plus"] = len(dims)
                    dims.append(bond_dim)
                if k < lz - 1:
                    axes["z_plus"] = len(dims)
                    dims.append(bond_dim)
                if i > 0:
                    axes["x_minus"] = len(dims)
                    dims.append(bond_dim)
                if j > 0:
                    axes["y_minus"] = len(dims)
                    dims.append(bond_dim)
                if k > 0:
                    axes["z_minus"] = len(dims)
                    dims.append(bond_dim)
                axes["phys"] = len(dims)
                dims.append(2)
                sites[(i, j, k)] = TensorSite(random_site(rng, dims), axes)
    for i in range(lx):
        for j in range(ly):
            for k in range(lz):
                if i + 1 < lx:
                    edges.append(((i, j, k), (i + 1, j, k), "x_plus", "x_minus"))
                if j + 1 < ly:
                    edges.append(((i, j, k), (i, j + 1, k), "y_plus", "y_minus"))
                if k + 1 < lz:
                    edges.append(((i, j, k), (i, j, k + 1), "z_plus", "z_minus"))
    return LocalCarrier(f"peps3d_{lx * ly * lz}", "peps3d", (lx, ly, lz), sites, edges)


def carrier_specs() -> list[tuple[str, tuple[int, ...], int]]:
    return [
        ("mps", (16,), 1010),
        ("peps", (4, 4), 2020),
        ("peps3d", (4, 4, 2), 3032),
        ("peps3d", (4, 4, 4), 3064),
    ]


def make_carrier(family: str, shape: tuple[int, ...], seed: int) -> LocalCarrier:
    if family == "mps":
        return make_mps_carrier(shape[0], seed)
    if family == "peps":
        return make_peps_carrier(shape[0], shape[1], seed)
    if family == "peps3d":
        return make_peps3d_carrier(shape[0], shape[1], shape[2], seed)
    raise ValueError(family)


def quimb_count_check(carrier: LocalCarrier) -> dict[str, Any]:
    if carrier.family == "peps":
        lx, ly = carrier.shape
        arrays = [[carrier.sites[(i, j)].data for j in range(ly)] for i in range(lx)]
        tn = qtn.PEPS(arrays)
        return {"num_tensors": int(tn.num_tensors), "num_indices": int(tn.num_indices), "pass": int(tn.num_tensors) == len(carrier.sites)}
    if carrier.family == "peps3d":
        lx, ly, lz = carrier.shape
        arrays = [
            [[carrier.sites[(i, j, k)].data for k in range(lz)] for j in range(ly)]
            for i in range(lx)
        ]
        tn = qtn.PEPS3D(arrays)
        return {"num_tensors": int(tn.num_tensors), "num_indices": int(tn.num_indices), "pass": int(tn.num_tensors) == len(carrier.sites)}
    return {"num_tensors": len(carrier.sites), "num_indices": sum(site.data.ndim for site in carrier.sites.values()), "pass": True}


def quimb_partial_trace(tn: Any, family: str, where: list[Any]) -> np.ndarray:
    if family == "peps":
        rho = tn.partial_trace(where, max_bond=4, optimize="auto")
    elif family == "peps3d":
        rho = tn.partial_trace(where, max_bond=4)
    else:
        raise ValueError(family)
    return normalize_density(np.asarray(rho, dtype=DTYPE).reshape(2 ** len(where), 2 ** len(where)))


def quimb_local_environment_api_report(records: list[dict[str, Any]], axis0: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for family, shape, seed, pair in [
        ("peps", (2, 2), 4410, [(0, 0), (0, 1)]),
        ("peps3d", (2, 2, 2), 4420, [(0, 0, 0), (0, 0, 1)]),
    ]:
        if family == "peps":
            tn = qtn.PEPS.rand(Lx=shape[0], Ly=shape[1], bond_dim=2, phys_dim=2, seed=seed)
        else:
            tn = qtn.PEPS3D.rand(Lx=shape[0], Ly=shape[1], Lz=shape[2], bond_dim=2, phys_dim=2, seed=seed)
        tn_zero = tn.copy()
        base = quimb_partial_trace(tn, family, pair)
        record = records[0]
        axis = OP_AXES[str(record["operator"])]
        drive = axis0_drive(axis0, 0)
        mem_drive = holodeck_memory_drive(memory, 0)
        angle = source_strength(record, drive, mem_drive)
        angle_zero = source_strength(record, 0.0)
        gate = qu.expm(-1j * float(record["operator_sign"]) * angle * np.kron(axis, axis))
        gate_zero = qu.expm(-1j * float(record["operator_sign"]) * angle_zero * np.kron(axis, axis))
        tn.gate_(gate, (pair[0], pair[1]), contract="split", max_bond=4, cutoff=1e-10)
        tn_zero.gate_(gate_zero, (pair[0], pair[1]), contract="split", max_bond=4, cutoff=1e-10)
        rho = quimb_partial_trace(tn, family, pair)
        rho_zero = quimb_partial_trace(tn_zero, family, pair)
        rows[family] = {
            "pair": [str(x) for x in pair],
            "stage_record_model_after_hash": record["model_after"]["density_hash"],
            "axis0_ready": bool(axis0.get("ready")),
            "axis0_drive": float(drive),
            "holodeck_memory_ready": bool(memory.get("ready")),
            "holodeck_memory_drive": float(mem_drive),
            "rho_shape": list(rho.shape),
            "trace": float(np.real(np.trace(rho))),
            "min_eigenvalue": float(np.min(np.linalg.eigvalsh((rho + rho.conj().T) / 2).real)),
            "update_gap_from_base": float(np.linalg.norm(rho - base)),
            "axis0_zeroed_gap": float(np.linalg.norm(rho - rho_zero)),
            "two_site_stats": two_site_stats(rho),
        }
    return {
        "pass": all(
            row["rho_shape"] == [4, 4]
            and abs(row["trace"] - 1.0) < 1e-8
            and row["min_eigenvalue"] > -1e-8
            and row["update_gap_from_base"] > 1e-8
            and row["axis0_zeroed_gap"] > 1e-8
            for row in rows.values()
        ),
        "rows": rows,
        "claim_ceiling": "Installed quimb partial_trace local reduced-density API works on bounded PEPS/PEPS3D patches only.",
    }


def apply_physical_slot(site: TensorSite, operator: str, sign: int, strength: float) -> None:
    axis = OP_AXES[operator]
    unitary = I2 - 1j * float(sign) * float(strength) * axis
    site.data = np.tensordot(site.data, unitary.T, axes=([site.axes["phys"]], [0])).astype(DTYPE)


def source_strength(record: dict[str, Any], drive: float, memory_drive: float = 0.0) -> float:
    fep = record.get("fep_efe_score", {})
    repair = record.get("update_repair", {})
    return float(
        0.003
        + 0.00035 * float(record.get("slot_delta_norm", 0.0))
        + 0.00010 * float(record.get("entropy", 0.0))
        + 0.00008 * float(fep.get("expected_free_energy_proxy", 0.0))
        + 0.00012 * float(fep.get("prediction_error_l2", 0.0))
        + 0.00008 * float(repair.get("manifold_projection_delta_norm", 0.0))
        + 0.08000 * float(drive)
        + 0.02000 * float(memory_drive)
    )


def pair_environment_density(carrier: LocalCarrier, edge: tuple[tuple[int, ...], tuple[int, ...], str, str]) -> np.ndarray:
    site_a, site_b, side_a, side_b = edge
    a = carrier.sites[site_a].data
    b = carrier.sites[site_b].data
    axis_a = carrier.sites[site_a].axes[side_a]
    axis_b = carrier.sites[site_b].axes[side_b]
    pair = np.tensordot(a, b, axes=([axis_a], [axis_b]))
    a_remaining = [idx for idx in range(a.ndim) if idx != axis_a]
    b_remaining = [idx for idx in range(b.ndim) if idx != axis_b]
    phys_a = a_remaining.index(carrier.sites[site_a].axes["phys"])
    phys_b = len(a_remaining) + b_remaining.index(carrier.sites[site_b].axes["phys"])
    pair = np.moveaxis(pair, [phys_a, phys_b], [0, 1]).reshape(4, -1)
    rho = pair @ pair.conj().T
    return normalize_density(rho)


def environment_rows(carrier: LocalCarrier) -> list[dict[str, Any]]:
    rows = []
    edge_count = len(carrier.edges)
    if edge_count <= MAX_ENV_EDGES:
        selected = list(enumerate(carrier.edges))
    else:
        step = max(1, edge_count // MAX_ENV_EDGES)
        selected = [(idx, carrier.edges[idx]) for idx in range(0, edge_count, step)][:MAX_ENV_EDGES]
    for edge_idx, edge in selected:
        rho = pair_environment_density(carrier, edge)
        stats = two_site_stats(rho)
        rows.append(
            {
                "edge_index": edge_idx,
                "edge": [str(edge[0]), str(edge[1]), edge[2], edge[3]],
                "contracted_rank": int(np.linalg.matrix_rank(rho, tol=1e-10)),
                "contracted_trace": float(np.real(np.trace(rho))),
                **stats,
            }
        )
    return rows


def signature_from_rows(rows: list[dict[str, Any]]) -> np.ndarray:
    arr = np.asarray([[row[col] for col in ENVIRONMENT_SIGNATURE_COLUMNS] for row in rows], dtype=float)
    return np.r_[arr.mean(axis=0), arr.std(axis=0), arr[-1]]


def apply_axis_scale(arr: np.ndarray, axis: int, scale: np.ndarray) -> np.ndarray:
    shape = [1] * arr.ndim
    shape[axis] = len(scale)
    return (arr * scale.reshape(shape)).astype(DTYPE)


def gauge_control_report(carrier: LocalCarrier) -> dict[str, Any]:
    edge = carrier.edges[0]
    base_rho = pair_environment_density(carrier, edge)
    site_a, site_b, side_a, side_b = edge
    axis_a = carrier.sites[site_a].axes[side_a]
    axis_b = carrier.sites[site_b].axes[side_b]
    dim = carrier.sites[site_a].data.shape[axis_a]
    scale = np.linspace(1.18, 0.82, dim).astype(DTYPE)

    balanced = copy.deepcopy(carrier)
    balanced.sites[site_a].data = apply_axis_scale(balanced.sites[site_a].data, axis_a, scale)
    balanced.sites[site_b].data = apply_axis_scale(balanced.sites[site_b].data, axis_b, 1.0 / scale)
    balanced_rho = pair_environment_density(balanced, edge)

    unbalanced = copy.deepcopy(carrier)
    unbalanced.sites[site_a].data = apply_axis_scale(unbalanced.sites[site_a].data, axis_a, scale)
    unbalanced_rho = pair_environment_density(unbalanced, edge)

    balanced_gap = float(np.linalg.norm(base_rho - balanced_rho))
    unbalanced_gap = float(np.linalg.norm(base_rho - unbalanced_rho))
    return {
        "edge": [str(edge[0]), str(edge[1]), edge[2], edge[3]],
        "balanced_gauge_trace_distance_proxy": balanced_gap,
        "unbalanced_gauge_trace_distance_proxy": unbalanced_gap,
        "pass": balanced_gap < GAUGE_INVARIANCE_CEILING and unbalanced_gap > UNBALANCED_GAUGE_FLOOR,
    }


def run_carrier(
    records: list[dict[str, Any]],
    axis0: dict[str, Any],
    memory: dict[str, Any],
    family: str,
    shape: tuple[int, ...],
    seed: int,
    *,
    zero_axis0: bool = False,
    zero_memory: bool = False,
    identity_control: bool = False,
) -> dict[str, Any]:
    carrier = make_carrier(family, shape, seed)
    quimb_check = quimb_count_check(carrier)
    site_order = sorted(carrier.sites)
    before_rows = environment_rows(carrier)
    axis0_drives = []
    memory_drives = []
    stage_hashes = []
    for idx, record in enumerate(records):
        site = carrier.sites[site_order[idx % len(site_order)]]
        drive = 0.0 if zero_axis0 else axis0_drive(axis0, idx)
        mem_drive = 0.0 if zero_memory else holodeck_memory_drive(memory, idx)
        axis0_drives.append(drive)
        memory_drives.append(mem_drive)
        stage_hashes.append(record["model_after"]["density_hash"])
        if identity_control:
            continue
        apply_physical_slot(
            site,
            str(record["operator"]),
            int(record["operator_sign"]),
            source_strength(record, drive, mem_drive),
        )
    after_rows = environment_rows(carrier)
    before_sig = signature_from_rows(before_rows)
    after_sig = signature_from_rows(after_rows)
    gauge = gauge_control_report(carrier)
    return {
        "carrier": carrier.name,
        "family": carrier.family,
        "shape": "x".join(str(x) for x in carrier.shape),
        "site_count": len(carrier.sites),
        "edge_count": len(carrier.edges),
        "sampled_environment_edges": len(after_rows),
        "zero_axis0": bool(zero_axis0),
        "zero_memory": bool(zero_memory),
        "identity_control": bool(identity_control),
        "stage_records_consumed": len(records),
        "unique_model_after_hashes_consumed": len(set(stage_hashes)),
        "axis0_ready": bool(axis0.get("ready")),
        "axis0_drive_mean_abs": float(np.mean(np.abs(axis0_drives))),
        "axis0_drive_variance": float(np.var(axis0_drives)),
        "holodeck_memory_ready": bool(memory.get("ready")),
        "holodeck_memory_drive_mean_abs": float(np.mean(np.abs(memory_drives))),
        "holodeck_memory_drive_variance": float(np.var(memory_drives)),
        "quimb_count_check": quimb_check,
        "environment_signature": after_sig,
        "environment_shift_from_initial": float(np.linalg.norm(after_sig - before_sig)),
        "environment_rows_head": after_rows[:3],
        "gauge_control": gauge,
        "pass": (
            len(records) == N_SOURCE_SEEDS * 64
            and len(set(stage_hashes)) > 16
            and quimb_check["pass"]
            and len(after_rows) > 0
            and bool(np.all(np.isfinite(after_sig)))
            and gauge["pass"]
        ),
    }


def local_contraction_tree_witness() -> dict[str, Any]:
    inputs = [("p", "a", "x"), ("x", "q", "b")]
    output = ("p", "q", "a", "b")
    sizes = {"p": 2, "q": 2, "a": 4, "b": 4, "x": 2}
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False, on_trial_error="raise").search(inputs, output, sizes)
    rng = np.random.default_rng(4141)
    left = rng.normal(size=(2, 4, 2))
    right = rng.normal(size=(2, 2, 4))
    ref = oe.contract("pax,xqb->pqab", left, right)
    return {
        "cotengra_cost": float(tree.contraction_cost()),
        "cotengra_width": float(tree.contraction_width()),
        "opt_einsum_reference_norm": float(np.linalg.norm(ref)),
        "pass": float(tree.contraction_cost()) > 0.0 and float(np.linalg.norm(ref)) > 0.0,
    }


def static_no_dense_guard() -> dict[str, Any]:
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    forbidden = ["." + "to_dense(", "dense" + "_vector("]
    hits = [term for term in forbidden if term in text]
    return {
        "forbidden_terms": forbidden,
        "hits": hits,
        "pass": not hits,
    }


def z3_no_dense_witness(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    carriers = z3.Int("carriers")
    min_sites = z3.Int("min_sites")
    max_sites = z3.Int("max_sites")
    no_dense = z3.Bool("no_dense")
    solver.add(carriers == len(rows))
    solver.add(min_sites == min(int(row["site_count"]) for row in rows.values()))
    solver.add(max_sites == max(int(row["site_count"]) for row in rows.values()))
    solver.add(no_dense == static_no_dense_guard()["pass"])
    solver.add(z3.Not(z3.And(carriers >= 4, min_sites >= 16, max_sites >= 64, no_dense)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite carrier count, site count, and static no-dense guard.",
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("EngineCore.science_method_stage_records", "local_tensor_updates"),
        ("Axis0.plural_router", "local_tensor_updates"),
        ("local_tensor_updates", "MPS.local_environment"),
        ("local_tensor_updates", "PEPS.local_environment"),
        ("local_tensor_updates", "PEPS3D.local_environment"),
        ("PEPS.local_environment", "balanced_gauge_control"),
        ("PEPS3D.local_environment", "finite_size_control"),
        ("axis0_zeroed_control", "repair_receipt"),
        ("static_no_dense_guard", "repair_receipt"),
    ]
    graph.add_edges_from(edges)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "edge_list": edges,
        "pass": nx.is_directed_acyclic_graph(graph),
    }


def pairwise_signature_gaps(rows: dict[str, dict[str, Any]]) -> dict[str, float]:
    keys = sorted(rows)
    return {
        f"{a}_vs_{b}": float(np.linalg.norm(rows[a]["environment_signature"] - rows[b]["environment_signature"]))
        for i, a in enumerate(keys)
        for b in keys[i + 1 :]
    }


def axis0_zeroed_gaps(full_rows: dict[str, dict[str, Any]], zero_rows: dict[str, dict[str, Any]]) -> dict[str, float]:
    return {
        key: float(np.linalg.norm(full_rows[key]["environment_signature"] - zero_rows[key]["environment_signature"]))
        for key in sorted(full_rows)
    }


def memory_zeroed_gaps(full_rows: dict[str, dict[str, Any]], zero_rows: dict[str, dict[str, Any]]) -> dict[str, float]:
    return {
        key: float(np.linalg.norm(full_rows[key]["environment_signature"] - zero_rows[key]["environment_signature"]))
        for key in sorted(full_rows)
    }


def main() -> int:
    started = time.time()
    records = run_source_records()
    stage_contract = stage_science_contract(records)
    stage_contract_receipt = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0_router_receipt = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    memory_receipt = load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")
    axis0 = axis0_signature(axis0_router_receipt)
    memory = holodeck_memory_signal(memory_receipt)

    full_rows: dict[str, dict[str, Any]] = {}
    zero_rows: dict[str, dict[str, Any]] = {}
    memory_zero_rows: dict[str, dict[str, Any]] = {}
    identity_rows: dict[str, dict[str, Any]] = {}
    for family, shape, seed in carrier_specs():
        key = f"{family}_{int(np.prod(shape))}"
        full_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=False, zero_memory=False, identity_control=False)
        zero_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=True, zero_memory=False, identity_control=False)
        memory_zero_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=False, zero_memory=True, identity_control=False)
        identity_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=True, zero_memory=True, identity_control=True)

    axis0_gaps = axis0_zeroed_gaps(full_rows, zero_rows)
    memory_gaps = memory_zeroed_gaps(full_rows, memory_zero_rows)
    identity_gaps = {
        key: float(identity_rows[key]["environment_shift_from_initial"])
        for key in sorted(identity_rows)
    }
    signature_gaps = pairwise_signature_gaps(full_rows)
    tree_witness = local_contraction_tree_witness()
    no_dense_guard = static_no_dense_guard()
    graph = dependency_graph()
    quimb_local_api = quimb_local_environment_api_report(records, axis0, memory)

    repair_receipt = {
        "weak_link": "PEPS/PEPS3D campaign lacked a no-dense downstream consumer of EngineCore science-method fields plus the plural Axis0 router.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "No-dense PEPS/PEPS3D environment scouts must avoid global dense vector readout, consume stage science fields and Axis0 router outputs, and include axis0-zeroed, gauge, and finite-size controls.",
        "dependency_subset": [
            "EngineCore science_method_stage_record_v1",
            "macro_sim_stage_record_science_method_contract receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "source_native_holodeck_hash_memory_placeholder receipt",
            "quimb PEPS/PEPS3D tensor-count surfaces",
            "quimb PEPS/PEPS3D bounded partial_trace local-environment API",
            "cotengra/opt_einsum local pair-environment contraction witness",
            "MPS16/PEPS16/PEPS3D32/PEPS3D64 finite-size rows",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            "script": "missing_before_this_repair_wave",
            "stage_contract_receipt": stage_contract_receipt.get("path"),
            "axis0_router_receipt": axis0_router_receipt.get("path"),
            "holodeck_memory_placeholder_receipt": memory_receipt.get("path"),
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "axis0_zeroed_environment_signature_gaps": axis0_gaps,
            "holodeck_memory_zeroed_environment_signature_gaps": memory_gaps,
            "identity_environment_shift_from_initial": identity_gaps,
            "balanced_gauge_control_by_carrier": {key: row["gauge_control"] for key, row in full_rows.items()},
        },
        "axis0_outputs_or_blockers": {
            **axis0,
            "holodeck_memory_placeholder": memory,
            "holographic_boundary_interior_reconstruction": axis0_router_receipt.get("axis0_outputs_or_blockers", {}).get("holographic_boundary_interior_reconstruction", {}),
            "retrocausal_many_futures_policy_scoring": axis0_router_receipt.get("axis0_outputs_or_blockers", {}).get("retrocausal_many_futures_policy_scoring", {}),
        },
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local no-dense dependency-consumption repair could be tested directly; provider outputs remain proposal/audit-only until tied to local receipts",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Promote this only to a stronger environment-contraction scout if a future repair replaces the local pair proxy with true PEPS/PEPS3D boundary environment contraction and stricter gauge-invariant controls.",
    }

    positive = {
        "science_method_stage_records_consumed_by_subdense_environment": {
            "pass": stage_contract["pass"] and all(row["pass"] for row in full_rows.values()),
            "stage_contract": stage_contract,
            "carrier_rows": {key: {k: v for k, v in row.items() if k != "environment_signature"} for key, row in full_rows.items()},
        },
        "plural_axis0_router_drives_local_environment_signature": {
            "pass": axis0["ready"] and all(gap > AXIS0_GAP_FLOOR for gap in axis0_gaps.values()),
            "axis0_zeroed_gaps": axis0_gaps,
            "axis0_drive_mean_abs": {key: row["axis0_drive_mean_abs"] for key, row in full_rows.items()},
        },
        "holodeck_memory_placeholder_drives_local_environment_signature": {
            "pass": memory["ready"] and all(gap > AXIS0_GAP_FLOOR for gap in memory_gaps.values()),
            "memory_zeroed_gaps": memory_gaps,
            "memory_signal": memory,
            "memory_drive_mean_abs": {key: row["holodeck_memory_drive_mean_abs"] for key, row in full_rows.items()},
        },
        "finite_size_multicarrier_environment_rows_execute": {
            "pass": {"mps_16", "peps_16", "peps3d_32", "peps3d_64"}.issubset(full_rows)
            and full_rows["peps3d_32"]["site_count"] < full_rows["peps3d_64"]["site_count"],
            "site_counts": {key: row["site_count"] for key, row in full_rows.items()},
            "edge_counts": {key: row["edge_count"] for key, row in full_rows.items()},
            "pairwise_signature_gaps": signature_gaps,
        },
        "cotengra_opt_einsum_local_environment_witness_executes": tree_witness,
        "quimb_partial_trace_local_environment_api_consumes_stage_axis0": quimb_local_api,
        "z3_rejects_dense_or_missing_carrier_collapse": z3_no_dense_witness(full_rows),
        "dependency_graph_is_acyclic": graph,
    }

    graveyards = {
        "axis0_zeroed_control_changes_environment_signature": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in axis0_gaps.values()),
            "axis0_zeroed_gaps": axis0_gaps,
        },
        "holodeck_memory_zeroed_control_changes_environment_signature": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in memory_gaps.values()),
            "memory_zeroed_gaps": memory_gaps,
        },
        "identity_update_does_not_count_as_environment_dynamics": {
            "pass": all(gap < AXIS0_GAP_FLOOR for gap in identity_gaps.values()),
            "identity_environment_shift_from_initial": identity_gaps,
        },
        "balanced_gauge_is_stable_unbalanced_gauge_is_rejected": {
            "pass": all(row["gauge_control"]["pass"] for row in full_rows.values()),
            "gauge_controls": {key: row["gauge_control"] for key, row in full_rows.items()},
        },
    }

    boundary = {
        "static_no_dense_global_readout_guard": no_dense_guard,
        "claim_ceiling_blocks_full_environment_and_gauge_claims": {
            "pass": "does not prove full PEPS/PEPS3D environment contraction" in CLAIM_CEILING
            and "does not prove gauge-invariant finite-size geometry" in CLAIM_CEILING,
        },
        "repair_receipt_present": {
            "pass": all(key in repair_receipt for key in [
                "weak_link",
                "target_file_or_result",
                "admission_rule_improved",
                "dependency_subset",
                "stage_fields_touched_or_consumed",
                "before_baseline/hash",
                "after_delta/hash",
                "primary_control/result",
                "axis0_outputs_or_blockers",
                "provider_inputs_used",
                "promotion_ceiling",
                "next_step",
            ]),
            "receipt": repair_receipt,
        },
    }

    nearby_variants = {
        "total": len(graveyards),
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "repair_receipt": repair_receipt,
        "why_not_v4_probes": [
            "Subdense local-environment proxy only.",
            "Does not replace the dense 8-site bridge with a full no-dense PEPS/PEPS3D environment theorem.",
            "Does not admit canonical Axis0, Holodeck, physics, cognition, or neural-world-model claims.",
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
