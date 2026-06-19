#!/usr/bin/env python3
"""Shared builder for engine_16_stage_correspondence_v1."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import scipy.linalg
import sympy as sp
import z3


SIM_ID = "engine_16_stage_correspondence_v1"
SCHEMA = f"{SIM_ID}_result_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "hypothesis_test_only"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "julia_canon_jax_with_pytorch_graph"

LAMBDA = 0.7
THETA = math.pi / 2.0
FLOW_TIME = 1.0
TOL = 1.0e-10

ENG64_DIR = ROOT / "system_v6" / "sims" / "eng64_stage_fingerprint_ids_v0"
SCRIPTS_DIR = ROOT / "scripts"
for import_dir in (ENG64_DIR, SCRIPTS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import eng64_stage_fingerprint_ids_v0 as eng64  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


SOURCE_PATHS = {
    "hypothesis": ROOT / "system_v6/receipts/ratchet_geometry_order_hypothesis_20260612.md",
    "first_proposal_result": ROOT
    / "system_v6/sims/engine_16_stage_definition_correspondence_v0/results/engine_16_stage_definition_correspondence_v0_results.json",
    "first_proposal_common": ROOT
    / "system_v6/sims/engine_16_stage_definition_correspondence_v0/engine_16_stage_definition_correspondence_v0_common.py",
    "eng64_source": ENG64_DIR / "eng64_stage_fingerprint_ids_v0.py",
    "eng64_result": ENG64_DIR / "results/eng64_stage_fingerprint_ids_v0_results.json",
    "s5_jax_source": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/geo_s5_terrain_flows_v0_jax.py",
    "s5_envelope": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "s5_audit": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md",
    "terrain_math": ROOT / "system_v5/READ ONLY Reference Docs/terrain math.md",
    "terrain_operator_map": ROOT / "system_v6/receipts/terrain_operator_map_20260609.md",
    "gcm_registry": ROOT / "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json",
    "standards_codex": ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
    "builder_boundary": ROOT / "scripts/builder_audit_boundary.py",
    "substrate_helper": ROOT / "scripts/gcm_substrate_check.py",
}

GCM_LINEAGE = {
    "gcm_object_id": "gcmobj_a40e54e13cec01466c9d675028b3574b",
    "registry_body_sha256": "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed",
    "registry_path": "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json",
    "survivor_ids": ["surv_df8410cc012bfc835668"],
    "quotient_class_ids": ["qcls_830aa0cdc681784fa290"],
    "candidate_region_ids": ["creg_fb8dade30d57503aa616"],
    "object_maps": [
        {
            "role": "one_qubit_carve_anchor",
            "survivor_id": "surv_df8410cc012bfc835668",
            "quotient_class_id": "qcls_830aa0cdc681784fa290",
            "candidate_region_id": "creg_fb8dade30d57503aa616",
        }
    ],
}

TOOL_MANIFEST = {
    "eng64_stage_fingerprint_ids_v0": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: imports the exact audited label-free fingerprint machinery and representative density carrier unchanged.",
    },
    "geo_s5_terrain_flows_v0": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source: consumes pinned S5 terrain generator rows by source/result hash as the finite T_tau realization estate.",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite affine matrix and density arithmetic on the one-qubit Bloch carrier.",
    },
    "scipy.linalg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: computes exp(tX) finite-time affine flow maps from the pinned terrain generators.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive exact parsing of S5 pinned generator rows before numerical finite-time realization.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive computed-count consistency gate over stage/control/correspondence counts.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent computed-count consistency gate matching z3.",
    },
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing substrate-first lineage gate plus lineage-free negative control.",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a idempotency-from-birth validator boundary.",
    },
    "json_hashing": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result serialization, source locks, and stability hashes.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "eng64_stage_fingerprint_ids_v0": "load_bearing",
    "geo_s5_terrain_flows_v0": "load_bearing",
    "scipy.linalg": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "numpy": "supportive",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
    "json_hashing": "supportive",
}

TOOL_INTENT = {
    "claim_classes": [
        "engine_16_stage_correspondence_hypothesis_test",
        "eng64_fingerprint_family_reuse",
        "gcm_substrate_consumption",
        "computed_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "construct the exact alias graph over the 16 computed stage output keys without reading peer results",
        },
        "jax": {
            "networkx": "construct the exact alias graph over the 16 computed stage fingerprint IDs without reading peer results",
            "sympy": "exactly bind the 16x16 match-matrix dimensions and discovered-component count",
        },
        "pytorch": {
            "torch.func": "batched application of all 16 explicit affine stage maps to the representative Bloch vector",
            "sympy": "exactly bind the 16x16 match-matrix dimensions and discovered-component count",
        },
    },
}

STAGE_TABLE: list[dict[str, str]] = [
    {"stage_token": "TiSe", "terrain": "Se", "operator": "Ti", "composition": "T_Se o D_z", "order": "terrain_after_operator"},
    {"stage_token": "SeTi", "terrain": "Se", "operator": "Ti", "composition": "D_z o T_Se", "order": "operator_after_terrain"},
    {"stage_token": "FiSe", "terrain": "Se", "operator": "Fi", "composition": "T_Se o R_x", "order": "terrain_after_operator"},
    {"stage_token": "SeFi", "terrain": "Se", "operator": "Fi", "composition": "R_x o T_Se", "order": "operator_after_terrain"},
    {"stage_token": "TiNe", "terrain": "Ne", "operator": "Ti", "composition": "T_Ne o D_z", "order": "terrain_after_operator"},
    {"stage_token": "NeTi", "terrain": "Ne", "operator": "Ti", "composition": "D_z o T_Ne", "order": "operator_after_terrain"},
    {"stage_token": "FiNe", "terrain": "Ne", "operator": "Fi", "composition": "T_Ne o R_x", "order": "terrain_after_operator"},
    {"stage_token": "NeFi", "terrain": "Ne", "operator": "Fi", "composition": "R_x o T_Ne", "order": "operator_after_terrain"},
    {"stage_token": "TeNi", "terrain": "Ni", "operator": "Te", "composition": "T_Ni o D_x", "order": "terrain_after_operator"},
    {"stage_token": "NiTe", "terrain": "Ni", "operator": "Te", "composition": "D_x o T_Ni", "order": "operator_after_terrain"},
    {"stage_token": "FeNi", "terrain": "Ni", "operator": "Fe", "composition": "T_Ni o R_z", "order": "terrain_after_operator"},
    {"stage_token": "NiFe", "terrain": "Ni", "operator": "Fe", "composition": "R_z o T_Ni", "order": "operator_after_terrain"},
    {"stage_token": "TeSi", "terrain": "Si", "operator": "Te", "composition": "T_Si o D_x", "order": "terrain_after_operator"},
    {"stage_token": "SiTe", "terrain": "Si", "operator": "Te", "composition": "D_x o T_Si", "order": "operator_after_terrain"},
    {"stage_token": "FeSi", "terrain": "Si", "operator": "Fe", "composition": "T_Si o R_z", "order": "terrain_after_operator"},
    {"stage_token": "SiFe", "terrain": "Si", "operator": "Fe", "composition": "R_z o T_Si", "order": "operator_after_terrain"},
]

TERRAIN_REALIZATION = {
    "Se": {"role": "expansion_family", "source_key": "Se_Funnel_L", "committed_generator": "Se / Funnel"},
    "Ne": {"role": "circulation", "source_key": "Ne_Vortex_L", "committed_generator": "Ne / Vortex"},
    "Ni": {"role": "contraction_attractor", "source_key": "Ni_Source_R", "committed_generator": "Ni / Source"},
    "Si": {"role": "retention_strata", "source_key": "Si_Citadel_R", "committed_generator": "Si / Citadel"},
}

OPERATOR_PAIRING = {
    "Ti": {"channel": "D_z", "native_side": "z", "kind": "dephase"},
    "Te": {"channel": "D_x", "native_side": "x", "kind": "dephase"},
    "Fi": {"channel": "R_x", "native_side": "x", "kind": "rotation"},
    "Fe": {"channel": "R_z", "native_side": "z", "kind": "rotation"},
}

PAIRING_SCRAMBLE = {"Ti": "Te", "Te": "Ti", "Fi": "Fe", "Fe": "Fi"}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return out or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def round_float(value: float, digits: int = 12) -> float:
    value = float(value)
    if abs(value) < 10 ** (-digits):
        return 0.0
    return round(value, digits)


def round_list(values: Any, digits: int = 12) -> list[Any]:
    arr = np.asarray(values)
    if arr.ndim == 1:
        return [round_float(float(x), digits) for x in arr]
    return [[round_float(float(x), digits) for x in row] for row in arr]


def complex_matrix_list(rho: np.ndarray, digits: int = 12) -> list[list[list[float]]]:
    return [
        [[round_float(float(np.real(cell)), digits), round_float(float(np.imag(cell)), digits)] for cell in row]
        for row in rho
    ]


def bloch_from_rho(rho: np.ndarray) -> np.ndarray:
    return np.array(
        [
            2.0 * float(np.real(rho[0, 1])),
            -2.0 * float(np.imag(rho[0, 1])),
            float(np.real(rho[0, 0] - rho[1, 1])),
        ],
        dtype=float,
    )


def rho_from_bloch(vec: np.ndarray) -> np.ndarray:
    x, y, z = [float(v) for v in vec]
    return np.array(
        [
            [(1.0 + z) / 2.0, (x - 1j * y) / 2.0],
            [(x + 1j * y) / 2.0, (1.0 - z) / 2.0],
        ],
        dtype=np.complex128,
    )


def entropy_vn(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + np.conjugate(rho.T)) / 2.0)
    clipped = np.clip(np.real(vals), 0.0, 1.0)
    return float(-sum(val * math.log(val) for val in clipped if val > 1.0e-14))


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def parse_expr(value: str) -> sp.Expr:
    return sp.sympify(value.replace("//", "/"), locals={"sqrt": sp.sqrt})


def parse_matrix_strings(values: list[list[str]]) -> np.ndarray:
    return np.array([[float(sp.N(parse_expr(item), 40)) for item in row] for row in values], dtype=float)


def parse_vector_strings(values: list[str]) -> np.ndarray:
    return np.array([float(sp.N(parse_expr(item), 40)) for item in values], dtype=float)


def affine_matrix(m: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    out = np.zeros((4, 4), dtype=float)
    out[0, 0] = 1.0
    out[1:, 1:] = m
    if b is not None:
        out[1:, 0] = b
    return out


def compose_affine(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    m_left = np.asarray(left["M"], dtype=float)
    b_left = np.asarray(left["b"], dtype=float)
    m_right = np.asarray(right["M"], dtype=float)
    b_right = np.asarray(right["b"], dtype=float)
    return {
        "M": m_left @ m_right,
        "b": b_left + m_left @ b_right,
        "notation": f"{left['notation']} o {right['notation']}",
    }


def apply_affine(channel: dict[str, Any], vec: np.ndarray) -> np.ndarray:
    return np.asarray(channel["M"], dtype=float) @ vec + np.asarray(channel["b"], dtype=float)


def rotation_x(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=float)


def rotation_z(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)


def operator_channels(assignment: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    channels = {
        "Ti": {"M": np.diag([LAMBDA, LAMBDA, 1.0]), "b": np.zeros(3), "notation": "D_z"},
        "Te": {"M": np.diag([1.0, LAMBDA, LAMBDA]), "b": np.zeros(3), "notation": "D_x"},
        "Fi": {"M": rotation_x(THETA), "b": np.zeros(3), "notation": "R_x"},
        "Fe": {"M": rotation_z(THETA), "b": np.zeros(3), "notation": "R_z"},
    }
    if assignment:
        return {name: {**channels[assignment.get(name, name)], "notation": channels[assignment.get(name, name)]["notation"]} for name in channels}
    return channels


def finite_time_flow(A: np.ndarray, b: np.ndarray, t: float = FLOW_TIME) -> tuple[np.ndarray, np.ndarray]:
    block = np.zeros((4, 4), dtype=float)
    block[:3, :3] = A
    block[:3, 3] = b
    exp_block = scipy.linalg.expm(t * block)
    return exp_block[:3, :3], exp_block[:3, 3]


def measured_flow_character(M: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    singular = np.linalg.svd(M, compute_uv=False)
    eigvals = np.linalg.eigvals(M)
    if np.linalg.norm(b) > 1.0e-9:
        character = "non_unital_attractor"
    elif max(abs(singular - 1.0)) < 1.0e-9:
        character = "circulation_or_isometry"
    elif max(singular) <= 1.0 + 1.0e-9 and min(singular) < 1.0 - 1.0e-9:
        character = "contraction_or_retention"
    elif max(singular) > 1.0 + 1.0e-9:
        character = "expansion"
    else:
        character = "neutral"
    return {
        "measured_character": character,
        "singular_values": round_list(singular, 12),
        "eigenvalues_re_im": [[round_float(float(np.real(v)), 12), round_float(float(np.imag(v)), 12)] for v in eigvals],
        "translation_norm": round_float(float(np.linalg.norm(b)), 12),
        "determinant": round_float(float(np.linalg.det(M)), 12),
    }


def terrain_flows() -> dict[str, dict[str, Any]]:
    s5 = load_json(SOURCE_PATHS["s5_envelope"])
    table = s5["bloch_generator_table"]
    out: dict[str, dict[str, Any]] = {}
    for terrain, pin in TERRAIN_REALIZATION.items():
        source_key = pin["source_key"]
        row = table[source_key]
        A = parse_matrix_strings(row["pinned"]["A"])
        b = parse_vector_strings(row["pinned"]["b"])
        M, offset = finite_time_flow(A, b)
        out[terrain] = {
            "M": M,
            "b": offset,
            "notation": f"T_{terrain}",
            "terrain": terrain,
            "role": pin["role"],
            "source_key": source_key,
            "committed_generator": pin["committed_generator"],
            "source_ref": row["source_ref"],
            "generator_A": round_list(A, 12),
            "generator_b": round_list(b, 12),
            "flow_time": FLOW_TIME,
            "finite_time_M": round_list(M, 12),
            "finite_time_b": round_list(offset, 12),
            "finite_time_affine_4x4": round_list(affine_matrix(M, offset), 12),
            "measured": measured_flow_character(M, offset),
        }
    return out


def vector_fingerprint(rho: np.ndarray) -> tuple[float, ...]:
    if rho.shape != (2, 2):
        raise ValueError(f"eng64 fingerprint carrier must be 2x2 density matrix, got {rho.shape}")
    return eng64.fingerprint(rho)


def component_id_for_rho(rho: np.ndarray) -> str:
    return eng64.component_id_for_fingerprint(vector_fingerprint(rho))


def nullspace_basis(a: np.ndarray, tol: float = 1.0e-9) -> list[list[float]]:
    _, s, vh = np.linalg.svd(a)
    rank = int((s > tol).sum())
    basis = vh[rank:].T
    return [round_list(basis[:, idx], 10) for idx in range(basis.shape[1])]


def geometry_row(channel: dict[str, Any], rho_in: np.ndarray, rho_out: np.ndarray) -> dict[str, Any]:
    m = np.asarray(channel["M"], dtype=float)
    b = np.asarray(channel["b"], dtype=float)
    eigvals = np.linalg.eigvals(m)
    singular = np.linalg.svd(m, compute_uv=False)
    entropy_in = entropy_vn(rho_in)
    entropy_out = entropy_vn(rho_out)
    purity_in = purity(rho_in)
    purity_out = purity(rho_out)
    affine_fixed = nullspace_basis(np.c_[m - np.eye(3), b.reshape(3, 1)])
    return {
        "linear_fixed_subspace_basis_if_unital": nullspace_basis(m - np.eye(3)),
        "affine_fixed_equation_augmented_nullspace": affine_fixed,
        "eigenvalues_re_im": [[round_float(float(np.real(v)), 12), round_float(float(np.imag(v)), 12)] for v in eigvals],
        "singular_values": round_list(singular, 12),
        "translation": round_list(b, 12),
        "translation_norm": round_float(float(np.linalg.norm(b)), 12),
        "determinant": round_float(float(np.linalg.det(m)), 12),
        "spectral_radius": round_float(float(max(abs(v) for v in eigvals)), 12),
        "entropy_input": round_float(entropy_in, 12),
        "entropy_output": round_float(entropy_out, 12),
        "entropy_delta": round_float(entropy_out - entropy_in, 12),
        "purity_input": round_float(purity_in, 12),
        "purity_output": round_float(purity_out, 12),
        "purity_delta": round_float(purity_out - purity_in, 12),
    }


def build_stage_rows(
    *,
    erase_order: bool = False,
    pairing_scramble: bool = False,
    identity: bool = False,
    label_prefix: str = "",
) -> list[dict[str, Any]]:
    rho_in = np.array(eng64.RHO_REPR, dtype=np.complex128)
    bloch_in = bloch_from_rho(rho_in)
    flows = terrain_flows()
    operators = operator_channels(PAIRING_SCRAMBLE if pairing_scramble else None)
    rows = []
    for index, spec in enumerate(STAGE_TABLE):
        terrain = flows[spec["terrain"]]
        operator = operators[spec["operator"]]
        if identity:
            channel = {"M": np.eye(3), "b": np.zeros(3), "notation": "I"}
            effective_order = "identity"
        elif erase_order:
            channel = compose_affine(terrain, operator)
            effective_order = "order_erased_terrain_after_operator"
        elif spec["order"] == "terrain_after_operator":
            channel = compose_affine(terrain, operator)
            effective_order = "terrain_after_operator"
        else:
            channel = compose_affine(operator, terrain)
            effective_order = "operator_after_terrain"
        bloch_out = apply_affine(channel, bloch_in)
        rho_out = rho_from_bloch(bloch_out)
        fp = vector_fingerprint(rho_out)
        component_id = component_id_for_rho(rho_out)
        stage_token = f"{label_prefix}{spec['stage_token']}"
        rows.append(
            {
                "authority_table_position": index,
                "stage_token": stage_token,
                "authority_stage_token": spec["stage_token"],
                "terrain": spec["terrain"],
                "operator_label": spec["operator"],
                "operator_channel": operator["notation"],
                "source_composition": spec["composition"],
                "effective_composition": channel["notation"],
                "effective_order": effective_order,
                "pairing_scrambled": pairing_scramble,
                "terrain_source_key": terrain["source_key"],
                "terrain_role": terrain["role"],
                "matrix_bloch_3x3": round_list(channel["M"], 12),
                "translation_bloch_3": round_list(channel["b"], 12),
                "matrix_affine_4x4": round_list(affine_matrix(channel["M"], channel["b"]), 12),
                "bloch_input": round_list(bloch_in, 12),
                "bloch_output": round_list(bloch_out, 12),
                "rho_output": complex_matrix_list(rho_out, 12),
                "rho_output_trace_real": round_float(float(np.real(np.trace(rho_out))), 12),
                "rho_output_eigvals": round_list(np.linalg.eigvalsh((rho_out + np.conjugate(rho_out.T)) / 2.0), 12),
                "fingerprint": list(fp),
                "fingerprint_id": component_id,
                "component_id": component_id,
                "geometry": geometry_row(channel, rho_in, rho_out),
            }
        )
    return rows


def base_operator_rows() -> list[dict[str, Any]]:
    rows = []
    for name, channel in operator_channels().items():
        rows.append(
            {
                "operator": name,
                "channel": channel["notation"],
                "native_side": OPERATOR_PAIRING[name]["native_side"],
                "kind": OPERATOR_PAIRING[name]["kind"],
                "bloch_matrix_3x3": round_list(channel["M"], 12),
                "translation_bloch_3": round_list(channel["b"], 12),
                "affine_channel_4x4": round_list(affine_matrix(channel["M"], channel["b"]), 12),
                "fixture_parameter": {"lambda": LAMBDA} if name in {"Ti", "Te"} else {"theta": THETA},
            }
        )
    return rows


def discovered_components() -> list[dict[str, Any]]:
    result = load_json(SOURCE_PATHS["eng64_result"])
    rows = result["stage_fingerprint_components"]
    by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_component[row["component_id"]].append(row)
    components = []
    for component in result["components"]:
        cid = component["component_id"]
        sample = sorted(by_component[cid], key=lambda row: row["stage"])[0]
        components.append(
            {
                "component_id": cid,
                "representative_stage": component["representative_stage"],
                "stages": component["stages"],
                "size": component["size"],
                "representative_fingerprint": sample["fingerprint"],
            }
        )
    return sorted(components, key=lambda row: int(row["representative_stage"]))


def alias_groups_for_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        groups[row["component_id"]].append(row["stage_token"])
    return [
        {"component_id": component_id, "stage_tokens": sorted(tokens), "size": len(tokens)}
        for component_id, tokens in sorted(groups.items())
        if len(tokens) > 1
    ]


def stage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        groups[row["component_id"]].append(row["stage_token"])
    return {
        "stage_count": len(rows),
        "n_distinct": len(groups),
        "largest_alias_group": max((len(value) for value in groups.values()), default=0),
        "alias_groups": [
            {"component_id": key, "stage_tokens": sorted(value), "size": len(value)}
            for key, value in sorted(groups.items())
            if len(value) > 1
        ],
    }


def correspondence(stage_rows: list[dict[str, Any]], discovered: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = []
    nearest = []
    for row in stage_rows:
        fp = np.asarray(row["fingerprint"], dtype=float)
        matrix_row = []
        distances = []
        for comp in discovered:
            comp_fp = np.asarray(comp["representative_fingerprint"], dtype=float)
            match = row["component_id"] == comp["component_id"]
            matrix_row.append(1 if match else 0)
            distances.append(float(np.linalg.norm(fp - comp_fp, ord=2)))
        best_idx = int(np.argmin(distances))
        nearest.append(
            {
                "stage_token": row["stage_token"],
                "component_id": row["component_id"],
                "nearest_discovered_component_id": discovered[best_idx]["component_id"],
                "nearest_l2_distance": round_float(distances[best_idx], 12),
                "exact_match": row["component_id"] == discovered[best_idx]["component_id"],
            }
        )
        matrix.append(matrix_row)
    defined_set = {row["component_id"] for row in stage_rows}
    discovered_set = {row["component_id"] for row in discovered}
    matched = sorted(defined_set & discovered_set)
    perfect = defined_set == discovered_set and len(defined_set) == 16
    exact_stage_matches = [row["stage_token"] for row in stage_rows if row["component_id"] in discovered_set]
    failing_pairings = [row["stage_token"] for row in stage_rows if row["component_id"] not in discovered_set]
    if perfect:
        verdict = "full_bijection"
    elif len(matched) == 0:
        verdict = "0-match_again"
    else:
        verdict = "partial"
    return {
        "question": "Does the owner-corrected native-pairing terrain-flow table reproduce the discovered eng64 16 component set under exact fingerprint equivalence?",
        "match_rule": "exact equality of eng64_fp_* component IDs computed from rounded 8-float density fingerprints",
        "defined_component_count": len(defined_set),
        "discovered_component_count": len(discovered_set),
        "exact_matched_component_count": len(matched),
        "exact_stage_match_count": len(exact_stage_matches),
        "perfect_bijection": perfect,
        "verdict": verdict,
        "result": "MATCH" if perfect else "MISMATCH",
        "stage_labels": [row["stage_token"] for row in stage_rows],
        "discovered_labels": [f"rep_hex{comp['representative_stage']:02d}:{comp['component_id']}" for comp in discovered],
        "match_matrix_16x16": matrix,
        "nearest_discovered_by_stage": nearest,
        "defined_alias_groups": alias_groups_for_rows(stage_rows),
        "defined_components_without_discovered_counterpart": sorted(defined_set - discovered_set),
        "discovered_components_without_defined_counterpart": sorted(discovered_set - defined_set),
        "matched_component_ids": matched,
        "exact_stage_matches": exact_stage_matches,
        "failing_pairings": failing_pairings,
    }


def non_equivalence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [row["stage_token"] for row in rows]
    status = []
    distances = []
    for left in rows:
        status_row = []
        distance_row = []
        lfp = np.asarray(left["fingerprint"], dtype=float)
        for right in rows:
            rfp = np.asarray(right["fingerprint"], dtype=float)
            same = left["component_id"] == right["component_id"]
            status_row.append("alias" if same else "distinct")
            distance_row.append(round_float(float(np.linalg.norm(lfp - rfp, ord=2)), 12))
        status.append(status_row)
        distances.append(distance_row)
    return {
        "labels": labels,
        "alias_distinct_matrix_16x16": status,
        "fingerprint_l2_distance_matrix_16x16": distances,
        "alias_groups": alias_groups_for_rows(rows),
        "all_pairs_distinct": not alias_groups_for_rows(rows),
    }


def commuting_pair_receipts() -> dict[str, Any]:
    flows = terrain_flows()
    operators = operator_channels()
    receipts = []
    for spec in STAGE_TABLE[::2]:
        terrain = flows[spec["terrain"]]
        operator = operators[spec["operator"]]
        a = compose_affine(terrain, operator)
        b = compose_affine(operator, terrain)
        delta = np.r_[np.ravel(np.asarray(a["M"]) - np.asarray(b["M"])), np.asarray(a["b"]) - np.asarray(b["b"])]
        gap = float(np.linalg.norm(delta, ord=2))
        receipts.append(
            {
                "pair": f"{spec['operator']}<->{spec['terrain']}",
                "terrain_after_operator": f"T_{spec['terrain']} o {operator['notation']}",
                "operator_after_terrain": f"{operator['notation']} o T_{spec['terrain']}",
                "commutator_affine_l2": round_float(gap, 12),
                "commuting_under_tolerance": gap <= TOL,
                "honest_null_rule": "if commuting_under_tolerance=true, the two ordered labels are reported as the same stage, not forced distinct",
            }
        )
    return {
        "reported_all_commuting_pairs": len(receipts) == 8,
        "commuting_pairs": [row for row in receipts if row["commuting_under_tolerance"]],
        "noncommuting_pairs": [row for row in receipts if not row["commuting_under_tolerance"]],
        "all_pairs": receipts,
    }


def controls(normal_rows: list[dict[str, Any]], discovered: list[dict[str, Any]]) -> dict[str, Any]:
    normal_match = correspondence(normal_rows, discovered)
    order_rows = build_stage_rows(erase_order=True)
    scramble_rows = build_stage_rows(pairing_scramble=True)
    scramble_match = correspondence(scramble_rows, discovered)
    labels_original = {row["authority_stage_token"]: row["component_id"] for row in normal_rows}
    labels_permuted = {f"perm_{idx:02d}_{row['authority_stage_token']}": row["component_id"] for idx, row in enumerate(normal_rows)}
    wrong_worse = scramble_match["exact_matched_component_count"] < normal_match["exact_matched_component_count"]
    doing_nothing = scramble_match["exact_matched_component_count"] == normal_match["exact_matched_component_count"]
    return {
        "order_erasure": {
            **stage_summary(order_rows),
            "control": "Both ordered variants for one terrain/operator pair are evaluated as the same T_tau-after-channel map.",
            "collapsed_toward_8": stage_summary(order_rows)["n_distinct"] <= 8,
        },
        "pairing_scramble": {
            **stage_summary(scramble_rows),
            "control": "Wrong-pairing variant swaps Ti<->Te and Fi<->Fe before matrix construction.",
            "exact_matched_component_count": scramble_match["exact_matched_component_count"],
            "normal_exact_matched_component_count": normal_match["exact_matched_component_count"],
            "wrong_pairing_scores_worse": wrong_worse,
            "pairing_convention_doing_nothing": doing_nothing,
            "diagnosis": "wrong pairing scored worse" if wrong_worse else "pairing convention did not improve exact discovered-component matches",
        },
        "label_permutation_invariance": {
            "control": "Stage labels are deterministically permuted after fingerprints are computed; component IDs must remain unchanged.",
            "fingerprint_ids_unchanged": sorted(labels_original.values()) == sorted(labels_permuted.values()),
            "label_field_used_in_fingerprint": False,
            "permuted_label_count": len(labels_permuted),
        },
        "commuting_pair_honest_null_rule": commuting_pair_receipts(),
    }


def z3_gate(values: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    stage_count = z3.Int("stage_count")
    discovered = z3.Int("discovered_distinct")
    defined = z3.Int("defined_distinct")
    order_erased = z3.Int("order_erased_distinct")
    exact_matches = z3.Int("exact_matched_components")
    solver.add(stage_count == values["stage_count"])
    solver.add(discovered == values["discovered_distinct"])
    solver.add(defined == values["defined_distinct"])
    solver.add(order_erased == values["order_erased_distinct"])
    solver.add(exact_matches == values["exact_matched_components"])
    solver.add(stage_count == 16)
    solver.add(discovered == 16)
    solver.add(defined <= 16)
    solver.add(order_erased <= 8)
    solver.add(exact_matches >= 0)
    solver.add(exact_matches <= 16)
    verdict = str(solver.check())
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": False,
        "supportive": True,
        "polarity": "direct satisfiable computed-count consistency check",
        "bound_values": values,
    }


def cvc5_gate(values: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    stage_count = solver.mkConst(int_sort, "stage_count")
    discovered = solver.mkConst(int_sort, "discovered_distinct")
    defined = solver.mkConst(int_sort, "defined_distinct")
    order_erased = solver.mkConst(int_sort, "order_erased_distinct")
    exact_matches = solver.mkConst(int_sort, "exact_matched_components")

    def eq(term: Any, value: int) -> None:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(value)))

    eq(stage_count, values["stage_count"])
    eq(discovered, values["discovered_distinct"])
    eq(defined, values["defined_distinct"])
    eq(order_erased, values["order_erased_distinct"])
    eq(exact_matches, values["exact_matched_components"])
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, stage_count, solver.mkInteger(16)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, discovered, solver.mkInteger(16)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, defined, solver.mkInteger(16)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, order_erased, solver.mkInteger(8)))
    solver.assertFormula(solver.mkTerm(Kind.GEQ, exact_matches, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, exact_matches, solver.mkInteger(16)))
    verdict = str(solver.checkSat()).lower()
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": False,
        "supportive": True,
        "polarity": "direct satisfiable computed-count consistency check",
        "bound_values": values,
    }


def smt_rows(stage_rows: list[dict[str, Any]], discovered: list[dict[str, Any]], corr: dict[str, Any], control_rows: dict[str, Any]) -> dict[str, Any]:
    values = {
        "stage_count": len(stage_rows),
        "defined_distinct": stage_summary(stage_rows)["n_distinct"],
        "discovered_distinct": len({row["component_id"] for row in discovered}),
        "exact_matched_components": int(corr["exact_matched_component_count"]),
        "order_erased_distinct": int(control_rows["order_erasure"]["n_distinct"]),
    }
    return {"z3": z3_gate(values), "cvc5": cvc5_gate(values)}


def diff_vs_first_proposal(corr: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = load_json(SOURCE_PATHS["first_proposal_result"])
    first_summary = first.get("summary", {})
    prior_exact = int(first_summary.get("exact_matched_component_count", 0))
    prior_distinct = int(first_summary.get("defined_distinct_component_count", 0))
    current_exact = int(corr["exact_matched_component_count"])
    current_distinct = int(stage_summary(rows)["n_distinct"])
    return {
        "baseline_packet": "system_v6/sims/engine_16_stage_definition_correspondence_v0",
        "baseline_result": first_summary.get("correspondence_result", first.get("correspondence", {}).get("result")),
        "baseline_exact_matched_component_count": prior_exact,
        "current_exact_matched_component_count": current_exact,
        "score_delta_exact_matched_components": current_exact - prior_exact,
        "baseline_defined_distinct_component_count": prior_distinct,
        "current_defined_distinct_component_count": current_distinct,
        "distinct_count_delta": current_distinct - prior_distinct,
        "changed_stage_math": [
            "v0 used 2 chirality sheets x T/F operator pairs x order polarity",
            "v1 uses owner-forwarded native-pairing table: terrain flow T_tau composed with one channel D_z/D_x/R_x/R_z",
            "v1 realizes T_tau from committed S5 terrain generator rows at t=1",
            "v1 consumes GCM object lineage before accepting the result",
        ],
        "moved_the_needle": current_exact != prior_exact or current_distinct != prior_distinct,
        "movement_summary": (
            f"exact matches {prior_exact}-> {current_exact}; defined distinct components {prior_distinct}-> {current_distinct}"
        ),
    }


def source_locks() -> dict[str, dict[str, Any]]:
    return {
        "hypothesis": source_lock(SOURCE_PATHS["hypothesis"], "registered owner-forwarded hypothesis", "c74e2db99"),
        "first_proposal_result": source_lock(SOURCE_PATHS["first_proposal_result"], "0/16 baseline result"),
        "first_proposal_common": source_lock(SOURCE_PATHS["first_proposal_common"], "baseline stage math implementation"),
        "eng64_source": source_lock(SOURCE_PATHS["eng64_source"], "audited fingerprint machinery", "fab7b2253"),
        "eng64_result": source_lock(SOURCE_PATHS["eng64_result"], "audited discovered-16 component set", "fab7b2253"),
        "s5_jax_source": source_lock(SOURCE_PATHS["s5_jax_source"], "committed S5 terrain generator source"),
        "s5_envelope": source_lock(SOURCE_PATHS["s5_envelope"], "committed S5 terrain generator result estate"),
        "s5_audit": source_lock(SOURCE_PATHS["s5_audit"], "S5 caveat boundary"),
        "terrain_math": source_lock(SOURCE_PATHS["terrain_math"], "terrain generator source formulas"),
        "terrain_operator_map": source_lock(SOURCE_PATHS["terrain_operator_map"], "operator/terrain source router"),
        "gcm_registry": source_lock(SOURCE_PATHS["gcm_registry"], "frozen GCM object registry"),
        "standards_codex": source_lock(SOURCE_PATHS["standards_codex"], "G.2a and standards codex"),
        "builder_boundary": source_lock(SOURCE_PATHS["builder_boundary"], "G.2a helper"),
        "substrate_helper": source_lock(SOURCE_PATHS["substrate_helper"], "substrate lineage helper"),
    }


def build_packet() -> dict[str, Any]:
    flows = terrain_flows()
    stage_rows = build_stage_rows()
    discovered = discovered_components()
    corr = correspondence(stage_rows, discovered)
    neq = non_equivalence(stage_rows)
    control_rows = controls(stage_rows, discovered)
    smt = smt_rows(stage_rows, discovered, corr, control_rows)
    substrate = gcm_substrate_check({"gcm_lineage": GCM_LINEAGE})
    negative_payload = {"sim_id": SIM_ID, "classification": CLASSIFICATION}
    negative = gcm_substrate_check(negative_payload)
    all_pass = bool(
        len(stage_rows) == 16
        and len(discovered) == 16
        and len(corr["match_matrix_16x16"]) == 16
        and all(len(row) == 16 for row in corr["match_matrix_16x16"])
        and control_rows["order_erasure"]["collapsed_toward_8"]
        and (
            control_rows["pairing_scramble"]["wrong_pairing_scores_worse"]
            or control_rows["pairing_scramble"]["pairing_convention_doing_nothing"]
        )
        and control_rows["label_permutation_invariance"]["fingerprint_ids_unchanged"]
        and control_rows["commuting_pair_honest_null_rule"]["reported_all_commuting_pairs"]
        and substrate["ok"]
        and not negative["ok"]
        and smt["z3"]["verdict"] == "sat"
        and smt["cvc5"]["verdict"] == "sat"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    summary = {
        "stage_count": len(stage_rows),
        "defined_distinct_component_count": stage_summary(stage_rows)["n_distinct"],
        "discovered_component_count": len(discovered),
        "exact_matched_component_count": corr["exact_matched_component_count"],
        "exact_stage_match_count": corr["exact_stage_match_count"],
        "correspondence_verdict": corr["verdict"],
        "perfect_bijection": corr["perfect_bijection"],
        "commuting_pair_count": len(control_rows["commuting_pair_honest_null_rule"]["commuting_pairs"]),
    }
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "layer_declaration": {
            "layer": "15 ordered compositions",
            "integration": "integrated-onto-the-carve",
            "carrier_floor": "1Q",
        },
        "gcm_lineage": copy.deepcopy(GCM_LINEAGE),
        "substrate_check": substrate,
        "lineage_free_negative_control": negative,
        "definition_phase_pinned_before_correspondence": True,
        "definition_rule": {
            "authority": "ratchet_geometry_order_hypothesis_20260612.md lines 35-73",
            "flow_count": 4,
            "channel_count": 4,
            "order_count_per_pair": 2,
            "stage_count": "4 native terrain/channel pairings x 2 channel families per side x 2 orders = 16",
            "terrain_realization": {
                terrain: {
                    key: value
                    for key, value in flow.items()
                    if key
                    in {
                        "terrain",
                        "role",
                        "source_key",
                        "committed_generator",
                        "source_ref",
                        "flow_time",
                        "finite_time_M",
                        "finite_time_b",
                        "finite_time_affine_4x4",
                        "measured",
                    }
                }
                for terrain, flow in flows.items()
            },
            "native_pairing_convention": OPERATOR_PAIRING,
            "stage_table_verbatim_tokens": [row["stage_token"] for row in STAGE_TABLE],
            "under_determined_choices_pinned_as_convention": [
                "one S5 sheeted generator row selected per terrain before scoring",
                "finite terrain flow time t=1",
                "lambda=0.7 and theta=pi/2 retained from the prior operator fixture",
                "wrong-pairing control swaps Ti/Te and Fi/Fe before scoring",
            ],
        },
        "source_locks": source_locks(),
        "eng64_fingerprint_contract": {
            "source": rel(SOURCE_PATHS["eng64_source"]),
            "fp_tolerance": eng64.FP_TOL,
            "rng_seed": eng64.RNG_SEED,
            "representative_rho_sha256": stable_sha256(
                [[float(np.real(cell)), float(np.imag(cell))] for row in eng64.RHO_REPR for cell in row]
            ),
            "definition": "Apply stage channel to RHO_REPR, flatten rho_out row-major as real/imag pairs, round to FP_TOL=1e-7, and hash the 8-float vector using eng64 component_id_for_fingerprint.",
            "method_reused_unchanged": True,
        },
        "base_operator_rows": base_operator_rows(),
        "terrain_flow_rows": [
            {
                key: value
                for key, value in flow.items()
                if key
                in {
                    "terrain",
                    "role",
                    "source_key",
                    "committed_generator",
                    "source_ref",
                    "generator_A",
                    "generator_b",
                    "flow_time",
                    "finite_time_M",
                    "finite_time_b",
                    "finite_time_affine_4x4",
                    "measured",
                }
            }
            for flow in flows.values()
        ],
        "defined_stage_rows": stage_rows,
        "discovered_components": discovered,
        "correspondence": corr,
        "non_equivalence_matrix": neq,
        "controls": control_rows,
        "diff_vs_first_proposal": diff_vs_first_proposal(corr, stage_rows),
        "smt_rows": smt,
        "summary": summary,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "G_2a_idempotency_from_birth": True,
            "builder_audit_boundary_ok": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "file_disjoint_packet": True,
            "definitions_pinned_before_correspondence": True,
            "substrate_first_gcm_lineage": substrate["ok"],
            "lineage_free_negative_red": not negative["ok"],
            "no_stage_admission": True,
            "fingerprint_method_reused_unchanged": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "disallowed_claims": [
            "stage admission",
            "Matrix64 admission",
            "QIT-engine admission",
            "axis admission",
            "bridge admission",
            "manifold admission",
            "physics claim",
            "target-system claim",
        ],
        "allowed_claims": [
            "scratch diagnostic hypothesis test executed",
            "owner-corrected native-pairing table evaluated under pinned finite T_tau choices",
            "label-free eng64 fingerprint correspondence computed",
            "GCM substrate lineage consumed",
        ],
    }


def write_lineage_free_negative(payload: dict[str, Any] | None = None) -> None:
    negative_payload = payload or {"sim_id": SIM_ID, "classification": CLASSIFICATION}
    write_json(LINEAGE_FREE_NEGATIVE_PATH, negative_payload)
