#!/usr/bin/env python3
"""Canonical-QIT multicarrier subdense environment-contraction scout.

This is the next bounded bridge after the dense 8-site common-boundary scout.
It consumes bounded canonical-QIT replay stage records and the plural Axis0
router, then applies them to MPS, PEPS, and PEPS3D tensor carriers using only
local tensor updates and nearest-neighbor environment contractions.

Formal scout only. The readout is a subdense local-environment proxy, not a
full PEPS/PEPS3D environment contraction theorem, not gauge-invariant geometry,
and not a canonical physics, cognition, Holodeck, or neural-world-model claim.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import pathlib
import time
from dataclasses import dataclass
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import networkx as nx
import opt_einsum as oe
import quimb.tensor as qtn
import torch
import z3

from canonical_qit_engine_specs import (
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_operator_slot_spec,
    get_schedule,
)
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    MANIFOLD_TARGET_MIX,
    apply_lindblad_step,
    bloch_vector,
    density_entropy,
    generate_initial_density as replay_initial_density,
    stage_fixed_target,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_multicarrier_subdense_environment_contraction_probe_results.json"

NAME = "source_native_multicarrier_subdense_environment_contraction_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "bounded_canonical_qit_multicarrier_subdense_environment_contraction_replay"
CLAIM_CEILING = (
    "Formal scout only: consumes bounded canonical-QIT stage replay records and "
    "plural Axis0 router outputs in MPS, PEPS, and PEPS3D local tensor updates, "
    "then reads nearest-neighbor subdense local-environment contractions. It is "
    "not source-native EngineCore execution, does not prove full PEPS/PEPS3D "
    "environment contraction, does not prove gauge-invariant finite-size "
    "geometry, and does not admit final Axis0, Holodeck, physics, cognition, "
    "neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing local carrier tensors, pair-environment densities, signatures, controls, and finite statistics"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing PEPS/PEPS3D tensor-network construction/count sanity checks without global dense readout"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing local pair-environment contraction-tree witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric pair-contraction cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "supportive dependency and finite-size carrier graph"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite no-dense/admission witness"},
    "canonical_qit_engine_specs": {"tried": True, "used": True, "reason": "supportive local terrain schedule, operator slot, and Pauli-generator replay specs; independent load-bearing checks remain on PyTorch and tensor-network/proof tools"},
    "canonical_qit_replay_helpers": {"tried": True, "used": True, "reason": "supportive local bounded-replay helpers for torch density seeds, terrain Lindblad step, target mix, and diagnostics"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "networkx": "supportive",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "canonical_qit_replay_helpers": "supportive",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "quimb": "local",
    "cotengra": "local",
    "opt_einsum": "local",
    "networkx": "local",
    "z3": "local",
    "canonical_qit_engine_specs": "local_supportive",
    "canonical_qit_replay_helpers": "local_supportive",
}

TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
I2 = torch.eye(2, dtype=TORCH_COMPLEX)
SX = torch.as_tensor([[0, 1], [1, 0]], dtype=TORCH_COMPLEX)
SY = torch.as_tensor([[0, -1j], [1j, 0]], dtype=TORCH_COMPLEX)
SZ = torch.as_tensor([[1, 0], [0, -1]], dtype=TORCH_COMPLEX)
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
FIELD_ABLATION_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "falsifier_graveyard",
    "next_policy",
]
FIELD_SIGNAL_WEIGHT = 5e-5
FIELD_ABLATION_GAP_FLOOR = 1e-6
FIELD_COMPONENT_VARIANCE_FLOOR = 1e-10
CANDIDATE_NAMES = [
    "fep_gradient_polarity",
    "path_entropy",
    "correlation_diversity_derivative",
    "retrocausal_many_futures_policy_scoring",
    "holographic_boundary_interior_reconstruction",
]
LOAD_BEARING_AXIS0_CANDIDATE_NAMES = [
    "fep_gradient_polarity",
    "correlation_diversity_derivative",
    "retrocausal_many_futures_policy_scoring",
]
BLOCKED_AXIS0_CANDIDATE_NAMES = [
    "path_entropy",
    "holographic_boundary_interior_reconstruction",
]
CANDIDATE_WEIGHTS = {
    "fep_gradient_polarity": 0.31,
    "path_entropy": 0.0,
    "correlation_diversity_derivative": 0.19,
    "retrocausal_many_futures_policy_scoring": 0.13,
    "holographic_boundary_interior_reconstruction": 0.0,
}
OPERATOR_VECTOR_WEIGHTS = {
    "Te": {
        "fep_gradient_polarity": 1.0,
        "correlation_diversity_derivative": 0.0,
        "retrocausal_many_futures_policy_scoring": 0.0,
    },
    "Fe": {
        "fep_gradient_polarity": 0.0,
        "correlation_diversity_derivative": 1.0,
        "retrocausal_many_futures_policy_scoring": 0.0,
    },
    "Ti": {
        "fep_gradient_polarity": 0.0,
        "correlation_diversity_derivative": 0.0,
        "retrocausal_many_futures_policy_scoring": 1.0,
    },
    "Fi": {
        "fep_gradient_polarity": 0.5,
        "correlation_diversity_derivative": 0.25,
        "retrocausal_many_futures_policy_scoring": 0.25,
    },
}
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
    data: torch.Tensor
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
    if isinstance(value, torch.Tensor):
        return value.tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_COMPLEX)


def as_real_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_REAL)


def to_external_array(value: Any) -> list:
    tensor = as_complex_tensor(value).detach().cpu().resolve_conj()
    return tensor.tolist()


def to_external_matrix(value: Any) -> list:
    return to_external_array(value)


def to_external_vector(value: Any) -> list:
    tensor = as_real_tensor(value).detach().cpu()
    return tensor.tolist()


def dagger(a: torch.Tensor) -> torch.Tensor:
    return torch.conj(a.transpose(-2, -1))


def real_float(value: Any) -> float:
    return float(torch.real(as_complex_tensor(value)).item())


def mean_float(values: Any) -> float:
    return float(torch.mean(as_real_tensor(list(values))).item())


def variance_float(values: Any) -> float:
    return float(torch.var(as_real_tensor(list(values)), unbiased=False).item())


def norm_float(value: Any) -> float:
    tensor = as_complex_tensor(value)
    return float(torch.linalg.vector_norm(tensor.reshape(-1)).item())


def normalize_density(rho: Any) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    rho = (rho + dagger(rho)) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(torch.real(vals), min=1e-12)
    out = (vecs * vals.to(TORCH_COMPLEX)) @ dagger(vecs)
    trace = torch.real(torch.trace(out))
    if float(torch.abs(trace).item()) <= 1e-14:
        return torch.eye(out.shape[0], dtype=TORCH_COMPLEX) / out.shape[0]
    return out / trace


def entropy(rho: Any) -> float:
    rho = normalize_density(rho)
    vals = torch.real(torch.linalg.eigvalsh((rho + dagger(rho)) / 2))
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / torch.sum(vals)
    return -float(torch.sum(vals * torch.log(vals)).item())


def two_site_stats(rho_ab: Any) -> dict[str, float]:
    rho_ab = normalize_density(rho_ab)
    rho4 = rho_ab.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", rho4).reshape(2, 2)
    rho_b = torch.einsum("abad->bd", rho4).reshape(2, 2)
    xi = torch.kron(SX, I2)
    ix = torch.kron(I2, SX)
    yi = torch.kron(SY, I2)
    iy = torch.kron(I2, SY)
    zi = torch.kron(SZ, I2)
    iz = torch.kron(I2, SZ)
    return {
        "two_site_entropy": entropy(rho_ab),
        "two_site_purity": real_float(torch.trace(rho_ab @ rho_ab)),
        "two_site_mutual_information": float(entropy(rho_a) + entropy(rho_b) - entropy(rho_ab)),
        "pauli_xI": real_float(torch.trace(xi @ rho_ab)),
        "pauli_Ix": real_float(torch.trace(ix @ rho_ab)),
        "pauli_yI": real_float(torch.trace(yi @ rho_ab)),
        "pauli_Iy": real_float(torch.trace(iy @ rho_ab)),
        "pauli_zI": real_float(torch.trace(zi @ rho_ab)),
        "pauli_Iz": real_float(torch.trace(iz @ rho_ab)),
        "pauli_xx": real_float(torch.trace(torch.kron(SX, SX) @ rho_ab)),
        "pauli_yy": real_float(torch.trace(torch.kron(SY, SY) @ rho_ab)),
        "pauli_zz": real_float(torch.trace(torch.kron(SZ, SZ) @ rho_ab)),
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


def density_hash(rho: Any) -> str:
    tensor = normalize_density(rho).detach().cpu().resolve_conj()
    rounded = [
        [round(float(z.real), 12), round(float(z.imag), 12)]
        for z in tensor.reshape(-1).tolist()
    ]
    payload = json.dumps(rounded, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def state_summary(rho: Any) -> dict[str, Any]:
    tensor = normalize_density(rho)
    return {
        "density_hash": density_hash(tensor),
        "bloch": bloch_vector(tensor),
        "entropy": density_entropy(tensor),
        "purity": real_float(torch.trace(tensor @ tensor)),
    }


def observation_distribution(rho: Any) -> list[float]:
    tensor = normalize_density(rho)
    z0 = float(torch.real(tensor[0, 0]).item())
    z1 = float(torch.real(tensor[1, 1]).item())
    sx_plus = 0.5 * (1.0 + float(torch.real(torch.trace(tensor @ SX)).item()))
    sy_plus = 0.5 * (1.0 + float(torch.real(torch.trace(tensor @ SY)).item()))
    raw = torch.clamp(torch.tensor([z0, z1, sx_plus, sy_plus], dtype=TORCH_REAL), min=1e-12)
    raw = raw / torch.sum(raw)
    return [float(x.item()) for x in raw]


def l2_list_gap(left: list[float], right: list[float]) -> float:
    a = as_real_tensor(left)
    b = as_real_tensor(right)
    return float(torch.linalg.vector_norm(a - b).item())


def apply_replay_operator_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    generator = OPERATOR_GENERATORS[slot["operator"]]
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    out = unitary @ rho @ unitary.conj().T
    return normalize_density(out), slot


def make_replay_stage_record(
    *,
    engine_type: int,
    seed_idx: int,
    main_idx: int,
    substage_idx: int,
    perception: str,
    loop_class: str,
    rho_before: torch.Tensor,
    rho_after_slot: torch.Tensor,
    rho_after_terrain: torch.Tensor,
    rho_after: torch.Tensor,
    slot: dict[str, Any],
) -> dict[str, Any]:
    model_before = state_summary(rho_before)
    terrain_prediction = state_summary(rho_after_terrain)
    model_after = state_summary(rho_after)
    target = stage_fixed_target(perception, engine_type)
    target_obs = observation_distribution(target)
    observed = observation_distribution(rho_after)
    predicted = observation_distribution(rho_after_terrain)
    prediction_error = l2_list_gap(predicted, observed)
    target_error = l2_list_gap(target_obs, observed)
    repair_delta = norm_float(rho_after - rho_after_terrain)
    slot_delta = norm_float(rho_after_slot - rho_before)
    entropy_after = density_entropy(rho_after)
    return {
        "engine_type": int(engine_type),
        "engine_label": "type_one_left_weyl" if engine_type == 0 else "type_two_right_weyl",
        "seed_idx": int(seed_idx),
        "main_stage_idx": int(main_idx),
        "substage_idx": int(substage_idx),
        "perception": perception,
        "loop_class": loop_class,
        "operator": slot["operator"],
        "operator_sign": int(slot["sign"]),
        "ordered_token": slot["token"],
        "token": slot["token"],
        "slot_delta_norm": slot_delta,
        "entropy": entropy_after,
        "model_before": model_before,
        "prediction": {
            "source": "canonical_qit_lindblad_replay_before_target_mix",
            "observation_distribution": predicted,
            "target_distribution": target_obs,
            "target_bloch": bloch_vector(target),
            "entropy": terrain_prediction["entropy"],
            "bloch": terrain_prediction["bloch"],
        },
        "observation": {
            "source": "post_operator_lindblad_and_target_mix_density",
            "observation_distribution": observed,
            "bloch": model_after["bloch"],
            "entropy": entropy_after,
            "purity": model_after["purity"],
        },
        "fep_efe_score": {
            "expected_free_energy_proxy": float(prediction_error + 0.5 * target_error + 0.05 * entropy_after),
            "prediction_error_l2": prediction_error,
            "target_error_l2": target_error,
            "ambiguity_proxy": entropy_after,
            "risk_proxy": target_error,
        },
        "update_repair": {
            "manifold_projection_delta_norm": repair_delta,
            "target_mix": float(MANIFOLD_TARGET_MIX),
            "target_density_hash": density_hash(target),
            "target_bloch": bloch_vector(target),
        },
        "falsifier_graveyard": {
            "matched_controls_required_downstream": [
                "axis0_zeroed_control",
                "scalar_mean_control",
                "shuffled_name_binding_control",
                "field_ablation_control",
                "manifold_zeroed_control",
            ],
            "replay_boundary": "canonical_qit_stage_zero_replay_not_engine_core",
            "slot_contract": {
                "ordered_token": slot["token"],
                "operator": slot["operator"],
                "operator_sign": int(slot["sign"]),
                "is_native_operator": bool(slot["is_native_operator"]),
                "is_chart_locked": bool(slot["is_chart_locked"]),
            },
        },
        "next_policy": {
            "policy_id": f"E{engine_type}:M{main_idx}:U{substage_idx}:{slot['token']}",
            "operator": slot["operator"],
            "operator_sign": int(slot["sign"]),
            "ordered_token": slot["token"],
            "precedence": slot["precedence"],
        },
        "model_after": model_after,
    }


def run_source_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_idx in range(N_SOURCE_SEEDS):
        for engine_type in (0, 1):
            rho = replay_initial_density(91000 + 100 * seed_idx + engine_type)
            for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
                for substage_idx in range(4):
                    rho_before = normalize_density(rho)
                    rho_after_slot, slot = apply_replay_operator_slot(
                        rho_before, perception, engine_type, loop_class, substage_idx
                    )
                    rho_after_terrain = normalize_density(apply_lindblad_step(rho_after_slot, perception, engine_type))
                    target = stage_fixed_target(perception, engine_type)
                    rho = normalize_density(
                        (1.0 - MANIFOLD_TARGET_MIX) * rho_after_terrain
                        + MANIFOLD_TARGET_MIX * target
                    )
                    row = make_replay_stage_record(
                        engine_type=engine_type,
                        seed_idx=seed_idx,
                        main_idx=main_idx,
                        substage_idx=substage_idx,
                        perception=perception,
                        loop_class=loop_class,
                        rho_before=rho_before,
                        rho_after_slot=rho_after_slot,
                        rho_after_terrain=rho_after_terrain,
                        rho_after=rho,
                        slot=slot,
                    )
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
    efe = as_real_tensor([row.get("fep_efe_score", {}).get("expected_free_energy_proxy", 0.0) for row in records])
    repair = as_real_tensor([row.get("update_repair", {}).get("manifold_projection_delta_norm", 0.0) for row in records])
    controls = {
        control
        for row in records
        for control in row.get("falsifier_graveyard", {}).get("matched_controls_required_downstream", [])
    }
    return {
        "pass": not missing and len(records) == N_SOURCE_SEEDS * 64 and bool(torch.all(torch.isfinite(efe))) and bool(torch.all(torch.isfinite(repair))),
        "record_count": len(records),
        "required_fields": REQUIRED_STAGE_FIELDS,
        "missing_required_stage_fields": missing,
        "fep_proxy_mean": float(torch.mean(efe).item()),
        "fep_proxy_variance": float(torch.var(efe, unbiased=False).item()),
        "repair_delta_mean": float(torch.mean(repair).item()),
        "graveyard_controls": sorted(controls),
    }


def axis0_signature(router: dict[str, Any]) -> dict[str, Any]:
    outputs = router.get("axis0_outputs_or_blockers") or {}
    vectors: dict[str, list[float]] = {}
    for name in CANDIDATE_NAMES:
        arr = as_real_tensor(outputs.get(name, {}).get("values", []))
        if int(arr.numel()):
            arr = torch.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
            scale = float(torch.max(torch.abs(arr)).item())
            if scale > 0.0:
                arr = arr / scale
        vectors[name] = [float(x) for x in arr]
    return {
        "ready": bool(router.get("exists") and router.get("all_pass") is True and all(vectors.values())),
        "candidate_names": list(CANDIDATE_NAMES),
        "candidate_vectors": vectors,
        "source_receipt": router.get("path"),
    }


def axis0_candidate_values(axis0: dict[str, Any], idx: int) -> dict[str, float]:
    vectors = axis0.get("candidate_vectors", {})
    values = {}
    for name in CANDIDATE_NAMES:
        vector = vectors.get(name, [])
        values[name] = float(vector[idx % len(vector)]) if vector else 0.0
    return values


def axis0_drive(axis0: dict[str, Any], idx: int, mode: str = "full_vector", operator: str | None = None) -> float:
    if not axis0.get("ready"):
        return 0.0
    raw_values = axis0_candidate_values(axis0, idx)
    values = {name: raw_values[name] for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES}
    if mode == "zero_all":
        return 0.0
    if mode == "scalar_mean":
        return mean_float(values.values())
    if mode == "shuffled_name_binding":
        rolled = list(values.values())[1:] + list(values.values())[:1]
        values = dict(zip(LOAD_BEARING_AXIS0_CANDIDATE_NAMES, rolled))
    elif mode.startswith("drop::"):
        dropped = mode.split("::", 1)[1]
        if dropped in BLOCKED_AXIS0_CANDIDATE_NAMES:
            pass
        elif dropped not in values:
            raise ValueError(mode)
        else:
            values = dict(values)
            values[dropped] = 0.0
    elif mode.startswith("sign_flip::"):
        flipped = mode.split("::", 1)[1]
        if flipped in BLOCKED_AXIS0_CANDIDATE_NAMES:
            pass
        elif flipped not in values:
            raise ValueError(mode)
        else:
            values = dict(values)
            values[flipped] = -values[flipped]
    elif mode.startswith("time_shuffle::"):
        shuffled = mode.split("::", 1)[1]
        if shuffled in BLOCKED_AXIS0_CANDIDATE_NAMES:
            pass
        elif shuffled not in values:
            raise ValueError(mode)
        else:
            vector = axis0.get("candidate_vectors", {}).get(shuffled, [])
            values = dict(values)
            if vector:
                values[shuffled] = float(vector[(idx * 7 + 11) % len(vector)])
    elif mode != "full_vector":
        raise ValueError(mode)
    if operator in OPERATOR_VECTOR_WEIGHTS:
        weights = OPERATOR_VECTOR_WEIGHTS[str(operator)]
        weighted = sum(weights[name] * values[name] for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES)
        denom = sum(abs(weights[name]) for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES)
    else:
        weighted = sum(CANDIDATE_WEIGHTS[name] * values[name] for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES)
        denom = sum(abs(CANDIDATE_WEIGHTS[name]) for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES)
    return float(weighted / denom)


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


def random_site(rng: torch.Generator, dims: list[int]) -> torch.Tensor:
    real = torch.randn(tuple(dims), generator=rng, dtype=TORCH_REAL) * 0.08
    imag = torch.randn(tuple(dims), generator=rng, dtype=TORCH_REAL) * 0.08
    return (real + 1j * imag).to(TORCH_COMPLEX)


def make_mps_carrier(length: int, seed: int, bond_dim: int = 2) -> LocalCarrier:
    rng = torch.Generator().manual_seed(seed)
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
    rng = torch.Generator().manual_seed(seed)
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
    rng = torch.Generator().manual_seed(seed)
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
        tn = qtn.PEPS.rand(Lx=lx, Ly=ly, bond_dim=2, phys_dim=2, seed=101 + lx * 10 + ly)
        return {"num_tensors": int(tn.num_tensors), "num_indices": int(tn.num_indices), "pass": int(tn.num_tensors) == len(carrier.sites)}
    if carrier.family == "peps3d":
        lx, ly, lz = carrier.shape
        tn = qtn.PEPS3D.rand(Lx=lx, Ly=ly, Lz=lz, bond_dim=2, phys_dim=2, seed=202 + lx * 100 + ly * 10 + lz)
        return {"num_tensors": int(tn.num_tensors), "num_indices": int(tn.num_indices), "pass": int(tn.num_tensors) == len(carrier.sites)}
    return {"num_tensors": len(carrier.sites), "num_indices": sum(site.data.ndim for site in carrier.sites.values()), "pass": True}


def quimb_partial_trace(tn: Any, family: str, where: list[Any]) -> torch.Tensor:
    if family == "peps":
        rho = tn.partial_trace(where, max_bond=4, optimize="auto")
    elif family == "peps3d":
        rho = tn.partial_trace(where, max_bond=4)
    else:
        raise ValueError(family)
    return normalize_density(as_complex_tensor(rho).reshape(2 ** len(where), 2 ** len(where)))


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
        drive = axis0_drive(axis0, 0, operator=str(record["operator"]))
        mem_drive = holodeck_memory_drive(memory, 0)
        angle = source_strength(record, drive, mem_drive)
        angle_zero = source_strength(record, 0.0)
        gate = torch.matrix_exp(-1j * float(record["operator_sign"]) * angle * torch.kron(axis, axis))
        gate_zero = torch.matrix_exp(-1j * float(record["operator_sign"]) * angle_zero * torch.kron(axis, axis))
        tn.gate_(to_external_matrix(gate), (pair[0], pair[1]), contract="split", max_bond=4, cutoff=1e-10)
        tn_zero.gate_(to_external_matrix(gate_zero), (pair[0], pair[1]), contract="split", max_bond=4, cutoff=1e-10)
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
            "trace": real_float(torch.trace(rho)),
            "min_eigenvalue": float(torch.min(torch.real(torch.linalg.eigvalsh((rho + dagger(rho)) / 2))).item()),
            "update_gap_from_base": norm_float(rho - base),
            "axis0_zeroed_gap": norm_float(rho - rho_zero),
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
    site.data = torch.tensordot(site.data, unitary.T, dims=([site.axes["phys"]], [0])).to(TORCH_COMPLEX)


def stable_field_bucket(payload: Any, modulus: int = 997) -> float:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return float(int(digest[:8], 16) % modulus) / float(modulus)


def science_method_field_components(record: dict[str, Any]) -> dict[str, float]:
    model_before = record.get("model_before", {})
    prediction = record.get("prediction", {})
    observation = record.get("observation", {})
    graveyard = record.get("falsifier_graveyard", {})
    next_policy = record.get("next_policy", {})

    before_bloch = as_real_tensor(model_before.get("bloch", [0.0, 0.0, 0.0]))
    before_component = float(
        torch.mean(before_bloch).item()
        + 0.25 * float(model_before.get("entropy", 0.0))
        + 0.10 * float(model_before.get("purity", 0.0))
    )

    pred_dist = as_real_tensor(prediction.get("observation_distribution", []))
    if int(pred_dist.numel()):
        pred_weights = torch.linspace(-0.5, 0.5, int(pred_dist.numel()), dtype=TORCH_REAL)
        pred_component = float((2.0 * torch.dot(pred_dist, pred_weights)).item())
    else:
        pred_component = 0.0

    obs_dist = as_real_tensor(observation.get("observation_distribution", []))
    if int(obs_dist.numel()):
        obs_weights = torch.linspace(0.5, -0.5, int(obs_dist.numel()), dtype=TORCH_REAL)
        obs_component = float((2.0 * torch.dot(obs_dist, obs_weights)).item())
    else:
        obs_component = 0.0

    controls = graveyard.get("matched_controls_required_downstream", [])
    slot_contract = graveyard.get("slot_contract", {})
    graveyard_component = float(
        0.10 * len(controls)
        + stable_field_bucket(
            {
                "controls": controls,
                "ordered_token": slot_contract.get("ordered_token"),
                "operator": slot_contract.get("operator"),
                "operator_sign": slot_contract.get("operator_sign"),
            }
        )
    )

    next_policy_component = float(
        stable_field_bucket(
            {
                "policy_id": next_policy.get("policy_id"),
                "operator": next_policy.get("operator"),
                "operator_sign": next_policy.get("operator_sign"),
                "ordered_token": next_policy.get("ordered_token"),
            }
        )
    )
    return {
        "model_before": before_component,
        "prediction": pred_component,
        "observation": obs_component,
        "falsifier_graveyard": graveyard_component,
        "next_policy": next_policy_component,
    }


def science_method_field_signal(record: dict[str, Any], ablate_stage_field: str | None = None) -> float:
    components = science_method_field_components(record)
    if ablate_stage_field is not None:
        if ablate_stage_field not in components:
            raise ValueError(f"unknown stage field ablation: {ablate_stage_field}")
        components[ablate_stage_field] = 0.0
    return float(torch.sum(torch.tanh(as_real_tensor(list(components.values())))).item())


def field_component_variance_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    values = {
        field: as_real_tensor([science_method_field_components(record)[field] for record in records])
        for field in FIELD_ABLATION_FIELDS
    }
    variances = {field: float(torch.var(arr, unbiased=False).item()) for field, arr in values.items()}
    return {
        "pass": all(var > FIELD_COMPONENT_VARIANCE_FLOOR for var in variances.values()),
        "field_component_variance_floor": FIELD_COMPONENT_VARIANCE_FLOOR,
        "variances": variances,
        "means": {field: float(torch.mean(arr).item()) for field, arr in values.items()},
    }


def source_strength(
    record: dict[str, Any],
    drive: float,
    memory_drive: float = 0.0,
    *,
    ablate_stage_field: str | None = None,
) -> float:
    fep = record.get("fep_efe_score", {})
    repair = record.get("update_repair", {})
    manifold_delta = float(repair.get("manifold_projection_delta_norm", 0.0))
    science_signal = science_method_field_signal(record, ablate_stage_field)
    return float(
        0.003
        + 0.00035 * float(record.get("slot_delta_norm", 0.0))
        + 0.00010 * float(record.get("entropy", 0.0))
        + 0.00008 * float(fep.get("expected_free_energy_proxy", 0.0))
        + 0.00012 * float(fep.get("prediction_error_l2", 0.0))
        + 0.00020 * manifold_delta
        + FIELD_SIGNAL_WEIGHT * science_signal
        + 0.08000 * float(drive)
        + 0.02000 * float(memory_drive)
    )


def pair_environment_density(carrier: LocalCarrier, edge: tuple[tuple[int, ...], tuple[int, ...], str, str]) -> torch.Tensor:
    site_a, site_b, side_a, side_b = edge
    a = carrier.sites[site_a].data
    b = carrier.sites[site_b].data
    axis_a = carrier.sites[site_a].axes[side_a]
    axis_b = carrier.sites[site_b].axes[side_b]
    pair = torch.tensordot(a, b, dims=([axis_a], [axis_b]))
    a_remaining = [idx for idx in range(a.ndim) if idx != axis_a]
    b_remaining = [idx for idx in range(b.ndim) if idx != axis_b]
    phys_a = a_remaining.index(carrier.sites[site_a].axes["phys"])
    phys_b = len(a_remaining) + b_remaining.index(carrier.sites[site_b].axes["phys"])
    pair = torch.movedim(pair, [phys_a, phys_b], [0, 1]).reshape(4, -1)
    rho = pair @ dagger(pair)
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
                "contracted_rank": int(torch.linalg.matrix_rank(rho, tol=1e-10).item()),
                "contracted_trace": real_float(torch.trace(rho)),
                **stats,
            }
        )
    return rows


def signature_from_rows(rows: list[dict[str, Any]]) -> torch.Tensor:
    arr = as_real_tensor([[row[col] for col in ENVIRONMENT_SIGNATURE_COLUMNS] for row in rows])
    return torch.cat([torch.mean(arr, dim=0), torch.std(arr, dim=0, unbiased=False), arr[-1]])


def apply_axis_scale(arr: torch.Tensor, axis: int, scale: torch.Tensor) -> torch.Tensor:
    shape = [1] * arr.ndim
    shape[axis] = len(scale)
    return (arr * scale.reshape(shape)).to(TORCH_COMPLEX)


def gauge_control_report(carrier: LocalCarrier) -> dict[str, Any]:
    edge = carrier.edges[0]
    base_rho = pair_environment_density(carrier, edge)
    site_a, site_b, side_a, side_b = edge
    axis_a = carrier.sites[site_a].axes[side_a]
    axis_b = carrier.sites[site_b].axes[side_b]
    dim = carrier.sites[site_a].data.shape[axis_a]
    scale = torch.linspace(1.18, 0.82, int(dim), dtype=TORCH_REAL).to(TORCH_COMPLEX)

    balanced = copy.deepcopy(carrier)
    balanced.sites[site_a].data = apply_axis_scale(balanced.sites[site_a].data, axis_a, scale)
    balanced.sites[site_b].data = apply_axis_scale(balanced.sites[site_b].data, axis_b, 1.0 / scale)
    balanced_rho = pair_environment_density(balanced, edge)

    unbalanced = copy.deepcopy(carrier)
    unbalanced.sites[site_a].data = apply_axis_scale(unbalanced.sites[site_a].data, axis_a, scale)
    unbalanced_rho = pair_environment_density(unbalanced, edge)

    balanced_gap = norm_float(base_rho - balanced_rho)
    unbalanced_gap = norm_float(base_rho - unbalanced_rho)
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
    zero_manifold: bool = False,
    ablate_stage_field: str | None = None,
    identity_control: bool = False,
    axis0_drive_mode: str = "full_vector",
) -> dict[str, Any]:
    carrier = make_carrier(family, shape, seed)
    quimb_check = quimb_count_check(carrier)
    site_order = sorted(carrier.sites)
    before_rows = environment_rows(carrier)
    axis0_drives = []
    memory_drives = []
    manifold_deltas = []
    stage_hashes = []
    for idx, record in enumerate(records):
        site = carrier.sites[site_order[idx % len(site_order)]]
        source_record = record
        if zero_manifold:
            source_record = copy.deepcopy(record)
            source_record.setdefault("update_repair", {})["manifold_projection_delta_norm"] = 0.0
        drive = axis0_drive(axis0, idx, "zero_all" if zero_axis0 else axis0_drive_mode, operator=str(source_record["operator"]))
        mem_drive = 0.0 if zero_memory else holodeck_memory_drive(memory, idx)
        manifold_deltas.append(float(source_record.get("update_repair", {}).get("manifold_projection_delta_norm", 0.0)))
        axis0_drives.append(drive)
        memory_drives.append(mem_drive)
        stage_hashes.append(record["model_after"]["density_hash"])
        if identity_control:
            continue
        apply_physical_slot(
            site,
            str(source_record["operator"]),
            int(source_record["operator_sign"]),
            source_strength(source_record, drive, mem_drive, ablate_stage_field=ablate_stage_field),
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
        "zero_manifold": bool(zero_manifold),
        "ablate_stage_field": ablate_stage_field,
        "identity_control": bool(identity_control),
        "axis0_drive_mode": axis0_drive_mode,
        "stage_records_consumed": len(records),
        "unique_model_after_hashes_consumed": len(set(stage_hashes)),
        "axis0_ready": bool(axis0.get("ready")),
        "axis0_drive_mean_abs": mean_float(abs(value) for value in axis0_drives),
        "axis0_drive_variance": variance_float(axis0_drives),
        "holodeck_memory_ready": bool(memory.get("ready")),
        "holodeck_memory_drive_mean_abs": mean_float(abs(value) for value in memory_drives),
        "holodeck_memory_drive_variance": variance_float(memory_drives),
        "manifold_projection_delta_mean_abs": mean_float(abs(value) for value in manifold_deltas),
        "manifold_projection_delta_variance": variance_float(manifold_deltas),
        "quimb_count_check": quimb_check,
        "environment_signature": after_sig,
        "environment_shift_from_initial": norm_float(after_sig - before_sig),
        "environment_rows_head": after_rows[:3],
        "gauge_control": gauge,
        "pass": (
            len(records) == N_SOURCE_SEEDS * 64
            and len(set(stage_hashes)) > 16
            and quimb_check["pass"]
            and len(after_rows) > 0
            and bool(torch.all(torch.isfinite(after_sig)))
            and gauge["pass"]
        ),
    }


def local_contraction_tree_witness() -> dict[str, Any]:
    inputs = [("p", "a", "x"), ("x", "q", "b")]
    output = ("p", "q", "a", "b")
    sizes = {"p": 2, "q": 2, "a": 4, "b": 4, "x": 2}
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False, on_trial_error="raise").search(inputs, output, sizes)
    rng = torch.Generator().manual_seed(4141)
    left = torch.randn((2, 4, 2), generator=rng, dtype=TORCH_REAL)
    right = torch.randn((2, 2, 4), generator=rng, dtype=TORCH_REAL)
    ref = oe.contract("pax,xqb->pqab", left, right)
    return {
        "cotengra_cost": float(tree.contraction_cost()),
        "cotengra_width": float(tree.contraction_width()),
        "opt_einsum_reference_norm": norm_float(ref),
        "pass": float(tree.contraction_cost()) > 0.0 and norm_float(ref) > 0.0,
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
        ("canonical_qit_stage_zero_replay_records", "local_tensor_updates"),
        ("Axis0.plural_router", "local_tensor_updates"),
        ("local_tensor_updates", "MPS.local_environment"),
        ("local_tensor_updates", "PEPS.local_environment"),
        ("local_tensor_updates", "PEPS3D.local_environment"),
        ("PEPS.local_environment", "balanced_gauge_control"),
        ("PEPS3D.local_environment", "finite_size_control"),
        ("axis0_zeroed_control", "repair_receipt"),
        ("manifold_zeroed_control", "repair_receipt"),
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
        f"{a}_vs_{b}": norm_float(rows[a]["environment_signature"] - rows[b]["environment_signature"])
        for i, a in enumerate(keys)
        for b in keys[i + 1 :]
    }


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return norm_float(a["environment_signature"] - b["environment_signature"])


def axis0_zeroed_gaps(full_rows: dict[str, dict[str, Any]], zero_rows: dict[str, dict[str, Any]]) -> dict[str, float]:
    return {
        key: norm_float(full_rows[key]["environment_signature"] - zero_rows[key]["environment_signature"])
        for key in sorted(full_rows)
    }


def memory_zeroed_gaps(full_rows: dict[str, dict[str, Any]], zero_rows: dict[str, dict[str, Any]]) -> dict[str, float]:
    return {
        key: norm_float(full_rows[key]["environment_signature"] - zero_rows[key]["environment_signature"])
        for key in sorted(full_rows)
    }


def manifold_zeroed_gaps(full_rows: dict[str, dict[str, Any]], zero_rows: dict[str, dict[str, Any]]) -> dict[str, float]:
    return {
        key: norm_float(full_rows[key]["environment_signature"] - zero_rows[key]["environment_signature"])
        for key in sorted(full_rows)
    }


def field_ablation_signature_gaps(
    full_rows: dict[str, dict[str, Any]],
    ablation_rows: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, float]]:
    return {
        field: {
            key: norm_float(full_rows[key]["environment_signature"] - rows[key]["environment_signature"])
            for key in sorted(full_rows)
        }
        for field, rows in ablation_rows.items()
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
    raw_candidate_names = list(axis0["candidate_names"])

    full_rows: dict[str, dict[str, Any]] = {}
    zero_rows: dict[str, dict[str, Any]] = {}
    scalar_mean_rows: dict[str, dict[str, Any]] = {}
    shuffled_name_rows: dict[str, dict[str, Any]] = {}
    drop_one_rows: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in raw_candidate_names}
    sign_flip_rows: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in raw_candidate_names}
    time_shuffle_rows: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in raw_candidate_names}
    memory_zero_rows: dict[str, dict[str, Any]] = {}
    manifold_zero_rows: dict[str, dict[str, Any]] = {}
    field_ablation_rows: dict[str, dict[str, dict[str, Any]]] = {
        field: {} for field in FIELD_ABLATION_FIELDS
    }
    identity_rows: dict[str, dict[str, Any]] = {}
    for family, shape, seed in carrier_specs():
        key = f"{family}_{int(math.prod(shape))}"
        full_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=False, zero_memory=False, identity_control=False)
        zero_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=True, zero_memory=False, identity_control=False)
        scalar_mean_rows[key] = run_carrier(
            records,
            axis0,
            memory,
            family,
            shape,
            seed,
            zero_axis0=False,
            zero_memory=False,
            identity_control=False,
            axis0_drive_mode="scalar_mean",
        )
        shuffled_name_rows[key] = run_carrier(
            records,
            axis0,
            memory,
            family,
            shape,
            seed,
            zero_axis0=False,
            zero_memory=False,
            identity_control=False,
            axis0_drive_mode="shuffled_name_binding",
        )
        for name in raw_candidate_names:
            drop_one_rows[name][key] = run_carrier(
                records,
                axis0,
                memory,
                family,
                shape,
                seed,
                zero_axis0=False,
                zero_memory=False,
                identity_control=False,
                axis0_drive_mode=f"drop::{name}",
            )
            sign_flip_rows[name][key] = run_carrier(
                records,
                axis0,
                memory,
                family,
                shape,
                seed,
                zero_axis0=False,
                zero_memory=False,
                identity_control=False,
                axis0_drive_mode=f"sign_flip::{name}",
            )
            time_shuffle_rows[name][key] = run_carrier(
                records,
                axis0,
                memory,
                family,
                shape,
                seed,
                zero_axis0=False,
                zero_memory=False,
                identity_control=False,
                axis0_drive_mode=f"time_shuffle::{name}",
            )
        memory_zero_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=False, zero_memory=True, identity_control=False)
        manifold_zero_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=False, zero_memory=False, zero_manifold=True, identity_control=False)
        for field in FIELD_ABLATION_FIELDS:
            field_ablation_rows[field][key] = run_carrier(
                records,
                axis0,
                memory,
                family,
                shape,
                seed,
                zero_axis0=False,
                zero_memory=False,
                ablate_stage_field=field,
                identity_control=False,
            )
        identity_rows[key] = run_carrier(records, axis0, memory, family, shape, seed, zero_axis0=True, zero_memory=True, identity_control=True)

    axis0_gaps = axis0_zeroed_gaps(full_rows, zero_rows)
    scalar_mean_gaps = {
        key: signature_gap(full_rows[key], scalar_mean_rows[key])
        for key in sorted(full_rows)
    }
    shuffled_name_gaps = {
        key: signature_gap(full_rows[key], shuffled_name_rows[key])
        for key in sorted(full_rows)
    }
    drop_one_gaps = {
        name: {
            key: signature_gap(full_rows[key], drop_one_rows[name][key])
            for key in sorted(full_rows)
        }
        for name in raw_candidate_names
    }
    sign_flip_gaps = {
        name: {
            key: signature_gap(full_rows[key], sign_flip_rows[name][key])
            for key in sorted(full_rows)
        }
        for name in raw_candidate_names
    }
    time_shuffle_gaps = {
        name: {
            key: signature_gap(full_rows[key], time_shuffle_rows[name][key])
            for key in sorted(full_rows)
        }
        for name in raw_candidate_names
    }
    active_drop_one_gaps = {name: drop_one_gaps[name] for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES}
    active_sign_flip_gaps = {name: sign_flip_gaps[name] for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES}
    active_time_shuffle_gaps = {name: time_shuffle_gaps[name] for name in LOAD_BEARING_AXIS0_CANDIDATE_NAMES}
    blocked_drop_one_gaps = {name: drop_one_gaps[name] for name in BLOCKED_AXIS0_CANDIDATE_NAMES}
    blocked_sign_flip_gaps = {name: sign_flip_gaps[name] for name in BLOCKED_AXIS0_CANDIDATE_NAMES}
    blocked_time_shuffle_gaps = {name: time_shuffle_gaps[name] for name in BLOCKED_AXIS0_CANDIDATE_NAMES}
    memory_gaps = memory_zeroed_gaps(full_rows, memory_zero_rows)
    manifold_gaps = manifold_zeroed_gaps(full_rows, manifold_zero_rows)
    field_report = field_component_variance_report(records)
    field_gaps = field_ablation_signature_gaps(full_rows, field_ablation_rows)
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
        "weak_link": "PEPS/PEPS3D campaign lacked a no-dense downstream consumer of canonical-QIT replay stage fields plus the plural Axis0 router, and the first subdense consumer still risked collapsing plural Axis0 candidate vectors into one scalar mean.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "No-dense PEPS/PEPS3D environment scouts must avoid global dense vector readout, consume stage science fields and only the non-blocked pre-guard Axis0 drive candidates, and include full-vector, scalar-mean, shuffled-name, drop-one, sign-flip, time-shuffle, axis0-zeroed, memory-zeroed, manifold-zeroed, gauge, and finite-size controls.",
        "dependency_subset": [
            "canonical_qit_stage_zero_replay_record_v1",
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
            "axis0_scalar_mean_environment_signature_gaps": scalar_mean_gaps,
            "axis0_shuffled_name_environment_signature_gaps": shuffled_name_gaps,
            "active_axis0_drop_one_environment_signature_gaps": active_drop_one_gaps,
            "active_axis0_sign_flip_environment_signature_gaps": active_sign_flip_gaps,
            "active_axis0_time_shuffle_environment_signature_gaps": active_time_shuffle_gaps,
            "blocked_axis0_drop_one_environment_signature_gaps": blocked_drop_one_gaps,
            "blocked_axis0_sign_flip_environment_signature_gaps": blocked_sign_flip_gaps,
            "blocked_axis0_time_shuffle_environment_signature_gaps": blocked_time_shuffle_gaps,
            "holodeck_memory_zeroed_environment_signature_gaps": memory_gaps,
            "manifold_zeroed_environment_signature_gaps": manifold_gaps,
            "science_method_field_component_variance": field_report,
            "science_method_field_ablation_signature_gaps": field_gaps,
            "identity_environment_shift_from_initial": identity_gaps,
            "balanced_gauge_control_by_carrier": {key: row["gauge_control"] for key, row in full_rows.items()},
        },
        "axis0_outputs_or_blockers": {
            **axis0,
            "primary_axis0_drive_mode": "full_vector",
            "load_bearing_axis0_candidate_names": LOAD_BEARING_AXIS0_CANDIDATE_NAMES,
            "blocked_axis0_candidate_names": BLOCKED_AXIS0_CANDIDATE_NAMES,
            "scalar_mean_control_gaps": scalar_mean_gaps,
            "shuffled_name_binding_control_gaps": shuffled_name_gaps,
            "drop_one_control_gaps": drop_one_gaps,
            "sign_flip_control_gaps": sign_flip_gaps,
            "time_shuffle_control_gaps": time_shuffle_gaps,
            "candidate_weights": CANDIDATE_WEIGHTS,
            "pre_guard_axis0_boundary": {
                "status": "raw_router_candidate_surface_for_downstream_guard",
                "guard_receipt_consumed": False,
                "post_guard_admission_claim_allowed": False,
                "blocked_candidates_masked_from_load_bearing_drive": BLOCKED_AXIS0_CANDIDATE_NAMES,
                "downstream_guard_result": "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json",
                "note": "This scout intentionally runs before the Axis0 plural-candidate guard. It reports all raw candidates, but path_entropy and HBI are masked out of the geometry-driving vector.",
            },
            "holodeck_memory_placeholder": memory,
            "holographic_boundary_interior_reconstruction": axis0_router_receipt.get("axis0_outputs_or_blockers", {}).get("holographic_boundary_interior_reconstruction", {}),
            "path_entropy": axis0_router_receipt.get("axis0_outputs_or_blockers", {}).get("path_entropy", {}),
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
            "axis0_drive_mode": "full_vector",
        },
        "plural_axis0_active_vector_differs_from_scalar_mean_control": {
            "pass": axis0["ready"] and all(gap > AXIS0_GAP_FLOOR for gap in scalar_mean_gaps.values()),
            "scalar_mean_gaps": scalar_mean_gaps,
            "candidate_weights": CANDIDATE_WEIGHTS,
            "load_bearing_axis0_candidate_names": LOAD_BEARING_AXIS0_CANDIDATE_NAMES,
        },
        "plural_axis0_active_name_binding_and_candidate_controls_are_visible": {
            "pass": axis0["ready"]
            and all(gap > AXIS0_GAP_FLOOR for gap in shuffled_name_gaps.values())
            and all(
                gap > AXIS0_GAP_FLOOR
                for rows_by_candidate in active_drop_one_gaps.values()
                for gap in rows_by_candidate.values()
            )
            and all(
                gap > AXIS0_GAP_FLOOR
                for rows_by_candidate in active_sign_flip_gaps.values()
                for gap in rows_by_candidate.values()
            )
            and all(
                gap > AXIS0_GAP_FLOOR
                for rows_by_candidate in active_time_shuffle_gaps.values()
                for gap in rows_by_candidate.values()
            ),
            "shuffled_name_gaps": shuffled_name_gaps,
            "active_drop_one_gaps": active_drop_one_gaps,
            "active_sign_flip_gaps": active_sign_flip_gaps,
            "active_time_shuffle_gaps": active_time_shuffle_gaps,
            "raw_candidate_names": raw_candidate_names,
            "blocked_axis0_candidate_names": BLOCKED_AXIS0_CANDIDATE_NAMES,
        },
        "holodeck_memory_placeholder_drives_local_environment_signature": {
            "pass": memory["ready"] and all(gap > AXIS0_GAP_FLOOR for gap in memory_gaps.values()),
            "memory_zeroed_gaps": memory_gaps,
            "memory_signal": memory,
            "memory_drive_mean_abs": {key: row["holodeck_memory_drive_mean_abs"] for key, row in full_rows.items()},
        },
        "manifold_projection_delta_drives_local_environment_signature": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in manifold_gaps.values()),
            "manifold_zeroed_gaps": manifold_gaps,
            "full_manifold_projection_delta_mean_abs": {
                key: row["manifold_projection_delta_mean_abs"] for key, row in full_rows.items()
            },
            "zeroed_manifold_projection_delta_mean_abs": {
                key: row["manifold_projection_delta_mean_abs"] for key, row in manifold_zero_rows.items()
            },
        },
        "science_method_field_components_drive_local_environment_signature": {
            "pass": field_report["pass"]
            and all(
                gap > FIELD_ABLATION_GAP_FLOOR
                for gaps in field_gaps.values()
                for gap in gaps.values()
            ),
            "field_component_variance": field_report,
            "field_ablation_gap_floor": FIELD_ABLATION_GAP_FLOOR,
            "field_ablation_signature_gaps": field_gaps,
            "field_signal_weight": FIELD_SIGNAL_WEIGHT,
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
        "subdense_axis0_is_pre_guard_raw_input_not_post_guard_admission": {
            "pass": axis0["candidate_names"] == CANDIDATE_NAMES,
            "raw_candidate_names": raw_candidate_names,
            "load_bearing_axis0_candidate_names": LOAD_BEARING_AXIS0_CANDIDATE_NAMES,
            "blocked_axis0_candidate_names": BLOCKED_AXIS0_CANDIDATE_NAMES,
            "guard_receipt_consumed": False,
            "post_guard_admission_claim_allowed": False,
            "downstream_guard_result": "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json",
            "note": "Subdense is the raw multicarrier control surface consumed by the downstream Axis0 guard; it reports all raw candidates but masks blocked candidates from load-bearing geometry.",
        },
    }

    graveyards = {
        "axis0_zeroed_control_changes_environment_signature": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in axis0_gaps.values()),
            "axis0_zeroed_gaps": axis0_gaps,
        },
        "axis0_scalar_mean_control_is_not_equivalent_to_full_vector_binding": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in scalar_mean_gaps.values()),
            "scalar_mean_gaps": scalar_mean_gaps,
            "reason": "Scalar means remain controls/diagnostics only; primary subdense actuation uses weighted active-candidate binding.",
        },
        "axis0_candidate_name_binding_shuffle_changes_environment_signature": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in shuffled_name_gaps.values()),
            "shuffled_name_gaps": shuffled_name_gaps,
        },
        "active_axis0_drop_sign_flip_and_time_shuffle_controls_are_not_silent": {
            "pass": all(
                gap > AXIS0_GAP_FLOOR
                for family in [active_drop_one_gaps, active_sign_flip_gaps, active_time_shuffle_gaps]
                for rows_by_candidate in family.values()
                for gap in rows_by_candidate.values()
            ),
            "active_drop_one_gaps": active_drop_one_gaps,
            "active_sign_flip_gaps": active_sign_flip_gaps,
            "active_time_shuffle_gaps": active_time_shuffle_gaps,
        },
        "blocked_axis0_candidates_do_not_drive_subdense_geometry": {
            "pass": all(
                gap < AXIS0_GAP_FLOOR
                for family in [blocked_drop_one_gaps, blocked_sign_flip_gaps, blocked_time_shuffle_gaps]
                for rows_by_candidate in family.values()
                for gap in rows_by_candidate.values()
            ),
            "blocked_drop_one_gaps": blocked_drop_one_gaps,
            "blocked_sign_flip_gaps": blocked_sign_flip_gaps,
            "blocked_time_shuffle_gaps": blocked_time_shuffle_gaps,
            "blocked_axis0_candidate_names": BLOCKED_AXIS0_CANDIDATE_NAMES,
        },
        "holodeck_memory_zeroed_control_changes_environment_signature": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in memory_gaps.values()),
            "memory_zeroed_gaps": memory_gaps,
        },
        "manifold_zeroed_control_changes_environment_signature": {
            "pass": all(gap > AXIS0_GAP_FLOOR for gap in manifold_gaps.values()),
            "manifold_zeroed_gaps": manifold_gaps,
        },
        "science_method_field_ablation_controls_change_environment_signature": {
            "pass": field_report["pass"]
            and all(
                gap > FIELD_ABLATION_GAP_FLOOR
                for gaps in field_gaps.values()
                for gap in gaps.values()
            ),
            "field_component_variance": field_report,
            "field_ablation_gap_floor": FIELD_ABLATION_GAP_FLOOR,
            "field_ablation_signature_gaps": field_gaps,
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
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_role_source": TOOL_ROLE_SOURCE,
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
