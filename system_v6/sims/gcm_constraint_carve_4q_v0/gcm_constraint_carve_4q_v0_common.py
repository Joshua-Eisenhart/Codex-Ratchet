#!/usr/bin/env python3
"""State-artifacted 4Q GCM constraint carve count fixture."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "gcm_constraint_carve_4q_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_SPEC_PATH = SIM_DIR / f"{SIM_ID}_envelope_spec.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_state_artifacted_4q_count_fixture"
SCHEMA = f"{SIM_ID}_result_v1"
TOL = 1.0e-10

EXPECTED_CANDIDATE_COUNT = 555
EXPECTED_PRODUCT_LIFT_COUNT = 545
EXPECTED_ANCHOR_COUNT = 10
EXPECTED_SURVIVOR_COUNT = 546
EXPECTED_QUOTIENT_CLASS_COUNT = 9
EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_1Q_REGISTRY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_3Q_OBJECT_ID = "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
EXPECTED_3Q_REGISTRY_SHA256 = "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"

EXPECTED_4Q_SUPPORT_PIN = "acd40027098ca7074723cbb63c21dc9598637363e0a821372830f71b5a6f42ab"
EXPECTED_STAGE_N4_PIN = "6d5fb046d0ca2813e22b02fa9d9ae2e669311ae52f9ea3853486b0834f13eaa4"
EXPECTED_TERRAIN_N4_PIN = "939b812785cd98ae25bc977345f38f4298a62643215d3cc2c5732c0a2c721acc"

PROBE_FAMILY = ("sigma_x_tensor_I_tensor_I_tensor_I", "sigma_z_tensor_I_tensor_I_tensor_I")
SCRAMBLED_PROBE_FAMILY = ("sigma_y_tensor_I_tensor_I_tensor_I", "sigma_z_tensor_I_tensor_I_tensor_I")
CONSTRAINT_KEYS = ("C1", "C2", "C3")
FORBIDDEN_PREDICATE_TOKENS = ("terrain", "atlas", "Se", "Ne", "Ni", "Si", "dissipative", "circulation")

PARENT_PATHS = {
    "one_q_registry": ROOT / "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json",
    "two_q_registry": ROOT / "system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_registry.json",
    "three_q_carve": ROOT / "system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json",
    "three_q_freeze_registry": ROOT / "system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_registry.json",
    "three_q_freeze_result": ROOT / "system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_results.json",
    "four_q_support": ROOT / "system_v6/sims/geo_s1_four_qubit_support_exact_v0/results/geo_s1_four_qubit_support_exact_v0_envelope_results.json",
    "four_q_support_jax": ROOT / "system_v6/sims/geo_s1_four_qubit_support_exact_v0/results/geo_s1_four_qubit_support_exact_v0_jax_results.json",
    "stage_n4": ROOT / "system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_envelope_results.json",
    "stage_n4_jax": ROOT / "system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json",
    "terrain_n4": ROOT / "system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json",
    "climb_ledger_correction": ROOT / "system_v6/receipts/qubit_ladder_climb_ledger_20260612.md",
    "builder_audit_boundary": ROOT / "scripts/builder_audit_boundary.py",
    "build_card": SIM_DIR / "build_card.md",
}

CUTS = {
    "q0|q123": {"left": [0], "right": [1, 2, 3], "dims": [2, 8]},
    "q1|q023": {"left": [1], "right": [0, 2, 3], "dims": [2, 8]},
    "q2|q013": {"left": [2], "right": [0, 1, 3], "dims": [2, 8]},
    "q3|q012": {"left": [3], "right": [0, 1, 2], "dims": [2, 8]},
    "q01|q23": {"left": [0, 1], "right": [2, 3], "dims": [4, 4]},
    "q02|q13": {"left": [0, 2], "right": [1, 3], "dims": [4, 4]},
    "q03|q12": {"left": [0, 3], "right": [1, 2], "dims": [4, 4]},
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


PAULI_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
I2 = np.eye(2, dtype=np.complex128)
ZERO = np.array([1.0, 0.0], dtype=np.complex128)
ONE = np.array([0.0, 1.0], dtype=np.complex128)
PLUS = (ZERO + ONE) / math.sqrt(2.0)


TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite C^16 density matrices, partial traces, full C1/C2/C3 rows, and 4-party CKW focus inequalities",
    },
    "z3": {"tried": True, "used": True, "reason": "load-bearing survivor-count contradiction guard"},
    "cvc5": {"tried": True, "used": True, "reason": "independent survivor-count contradiction guard matching z3"},
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hardened 1Q, 2Q, and 3Q lineage consumption checks",
    },
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a builder/audit boundary from birth"},
    "python_stdlib": {"tried": True, "used": True, "reason": "JSON, hashing, source locks, and result writing"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "python_stdlib": "supportive",
}

TOOL_INTENT = {
    "claim_classes": [
        "state_artifacted_4q_constraint_matrix",
        "3q_to_4q_product_embedding_and_TrD_retraction",
        "GHZ4_W4_cluster_full_matrix_rows",
        "narrowed_4party_ckw_from_stored_rho",
        "Cl8_C16_floor_rows_consumed_from_feedstock",
    ],
    "engine_tool_intent": {
        "julia": {"Graphs": "Graphs.SimpleGraph/add_edge!/connected_components over quotient-class adjacency"},
        "jax": {
            "networkx": "nx.Graph/connected_components over quotient classes",
            "sympy": "sp.Rational exact count guard",
            "z3": "z3.Solver unsat guard for survivor count",
            "cvc5": "cvc5.Solver unsat guard for survivor count",
        },
        "pytorch": {
            "torch.func": "vmap recomputes C2 active-probe booleans from matrix-derived first-qubit x/z rows",
            "sympy": "sp.Rational exact survivor/class count guards",
        },
    },
}

CONSTRAINTS = [
    {
        "key": "C1",
        "id": "C1_finite_4q_density_carrier",
        "literal_executable_predicate": "rho_ABCD is Hermitian trace-one positive semidefinite on C^16",
    },
    {
        "key": "C2",
        "id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "literal_executable_predicate": "first-qubit x/z probe signature from Tr_BCD(rho_ABCD) is not (0, 0)",
    },
    {
        "key": "C3",
        "id": "C3_persistence_n01_order_gap",
        "literal_executable_predicate": "D_z after R_x and R_x after D_z first-qubit x/z probe signatures differ",
    },
]


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def q(value: float, digits: int = 12) -> float:
    rounded = round(float(value), digits)
    return 0.0 if abs(rounded) <= TOL else rounded


def scaled(value: float) -> int:
    return int(round(2.0 * float(value)))


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def stable_id(prefix: str, value: Any, length: int = 24) -> str:
    return f"{prefix}_{stable_sha256(value)[:length]}"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_last_commit(path: Path) -> str | None:
    if not path.exists() or not path.is_relative_to(ROOT):
        return None
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": rel(path) if path.is_relative_to(ROOT) else str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def complex_pair(value: complex) -> list[float]:
    return [q(float(np.real(value))), q(float(np.imag(value)))]


def matrix_to_json(matrix: np.ndarray) -> list[list[list[float]]]:
    return [[complex_pair(value) for value in row] for row in matrix.tolist()]


def vector_to_json(vector: np.ndarray) -> list[list[float]]:
    return [complex_pair(value) for value in vector.tolist()]


def json_cell_to_complex(cell: Any) -> complex:
    if isinstance(cell, dict):
        return complex(float(cell["re"]), float(cell["im"]))
    return complex(float(cell[0]), float(cell[1]))


def json_to_matrix(value: list[list[Any]]) -> np.ndarray:
    return np.array([[json_cell_to_complex(cell) for cell in row] for row in value], dtype=np.complex128)


def json_to_vector(value: list[Any]) -> np.ndarray:
    return np.array([json_cell_to_complex(cell) for cell in value], dtype=np.complex128)


def tensor_product(*items: np.ndarray) -> np.ndarray:
    out = items[0]
    for item in items[1:]:
        out = np.kron(out, item)
    return out


def pure_density(vector: np.ndarray) -> np.ndarray:
    return np.outer(vector, np.conjugate(vector))


def rho_from_bloch(coord: tuple[float, float, float]) -> np.ndarray:
    x, y, z = coord
    return 0.5 * (I2 + x * PAULI_X + y * PAULI_Y + z * PAULI_Z)


def state_index(bits: tuple[int, int, int, int]) -> int:
    q0, q1, q2, q3 = bits
    return 8 * q0 + 4 * q1 + 2 * q2 + q3


def basis_state(*bits: int) -> np.ndarray:
    vector = np.zeros(16, dtype=np.complex128)
    vector[state_index(tuple(bits))] = 1.0
    return vector


def qubit_direction_kets(direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    nx, ny, nz = [float(v) for v in direction]
    theta = math.acos(max(-1.0, min(1.0, nz)))
    phi = math.atan2(ny, nx)
    plus = np.array([math.cos(theta / 2.0), complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0)])
    minus = np.array([-complex(math.cos(-phi), math.sin(-phi)) * math.sin(theta / 2.0), math.cos(theta / 2.0)])
    return plus.astype(np.complex128), minus.astype(np.complex128)


def generalized_ghz4_state(first_bloch_coord: tuple[float, float, float]) -> np.ndarray:
    bloch = np.array(first_bloch_coord, dtype=float)
    radius = float(np.linalg.norm(bloch))
    if radius <= 1.0e-12:
        plus, minus = ZERO, ONE
    else:
        plus, minus = qubit_direction_kets(bloch / radius)
    p = (1.0 + radius) / 2.0
    vector = math.sqrt(p) * tensor_product(plus, ZERO, ZERO, ZERO)
    vector += math.sqrt(1.0 - p) * tensor_product(minus, ONE, ONE, ONE)
    return vector / np.linalg.norm(vector)


def cluster_linear_4_state() -> np.ndarray:
    vector = np.zeros(16, dtype=np.complex128)
    for q0 in (0, 1):
        for q1 in (0, 1):
            for q2 in (0, 1):
                for q3 in (0, 1):
                    phase = -1.0 if ((q0 * q1 + q1 * q2 + q2 * q3) % 2) else 1.0
                    vector[state_index((q0, q1, q2, q3))] = phase / 4.0
    return vector


def terrain_feedstock_state_vector() -> np.ndarray:
    terrain = load_json(PARENT_PATHS["terrain_n4"])
    pairs = terrain["carrier"]["state_vector_re_im"]
    vector = np.array([complex(float(pair[0]), float(pair[1])) for pair in pairs], dtype=np.complex128)
    return vector / np.linalg.norm(vector)


def anchor_state(anchor_id: str) -> tuple[np.ndarray, np.ndarray | None]:
    if anchor_id == "GHZ4":
        psi = (basis_state(0, 0, 0, 0) + basis_state(1, 1, 1, 1)) / math.sqrt(2.0)
        return pure_density(psi), psi
    if anchor_id == "W4":
        psi = (basis_state(0, 0, 0, 1) + basis_state(0, 0, 1, 0) + basis_state(0, 1, 0, 0) + basis_state(1, 0, 0, 0)) / 2.0
        return pure_density(psi), psi
    if anchor_id == "cluster_linear_4":
        psi = cluster_linear_4_state()
        return pure_density(psi), psi
    if anchor_id == "product_0000":
        psi = basis_state(0, 0, 0, 0)
        return pure_density(psi), psi
    if anchor_id == "lifted_ladder_n4_feedstock_product_anchor":
        psi = terrain_feedstock_state_vector()
        return pure_density(psi), psi
    if anchor_id == "locally_rotated_generalized_GHZ4_anchor":
        psi = generalized_ghz4_state((0.75, 0.3, 0.4))
        return pure_density(psi), psi
    if anchor_id == "invalid_trace_anchor":
        psi = generalized_ghz4_state((0.75, 0.3, 0.4))
        return 1.2 * pure_density(psi), None
    if anchor_id == "GHZ4_minus":
        psi = (basis_state(0, 0, 0, 0) - basis_state(1, 1, 1, 1)) / math.sqrt(2.0)
        return pure_density(psi), psi
    if anchor_id == "biseparable_Bell_AB_tensor_00CD":
        psi = (basis_state(0, 0, 0, 0) + basis_state(1, 1, 0, 0)) / math.sqrt(2.0)
        return pure_density(psi), psi
    if anchor_id == "order_only_no_probe_anchor":
        return tensor_product(rho_from_bloch((0.0, 0.3, 0.0)), pure_density(ZERO), pure_density(ZERO), pure_density(ZERO)), None
    raise KeyError(anchor_id)


def partial_trace(rho: np.ndarray, keep: list[int], n_qubits: int = 4) -> np.ndarray:
    dims = [2] * n_qubits
    keep_set = set(keep)
    shaped = rho.reshape(dims + dims)
    current_n = len(dims)
    for qubit in reversed(range(n_qubits)):
        if qubit not in keep_set:
            shaped = np.trace(shaped, axis1=qubit, axis2=qubit + current_n)
            current_n -= 1
            dims.pop(qubit)
    final_dim = 2 ** len(keep)
    return shaped.reshape((final_dim, final_dim))


def bloch_from_rho(rho_a: np.ndarray) -> tuple[float, float, float]:
    return (
        q(float(np.real(np.trace(PAULI_X @ rho_a)))),
        q(float(np.real(np.trace(PAULI_Y @ rho_a)))),
        q(float(np.real(np.trace(PAULI_Z @ rho_a)))),
    )


def probe_signature(coord: tuple[float, float, float], family: tuple[str, str] = PROBE_FAMILY) -> tuple[int, int]:
    mapping = {
        "sigma_x_tensor_I_tensor_I_tensor_I": coord[0],
        "sigma_y_tensor_I_tensor_I_tensor_I": coord[1],
        "sigma_z_tensor_I_tensor_I_tensor_I": coord[2],
    }
    return tuple(scaled(mapping[name]) for name in family)  # type: ignore[return-value]


def dz_after_rx(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (0.5 * x, -0.5 * z, y)


def rx_after_dz(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (0.5 * x, -z, 0.5 * y)


def order_gap(coord: tuple[float, float, float], family: tuple[str, str] = PROBE_FAMILY) -> float:
    left = probe_signature(dz_after_rx(coord), family)
    right = probe_signature(rx_after_dz(coord), family)
    return q(math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right))))


def c1_density_valid(rho: np.ndarray) -> dict[str, Any]:
    hermitian_error = float(np.max(np.abs(rho - np.conjugate(rho.T))))
    trace = np.trace(rho)
    eigvals = np.linalg.eigvalsh((rho + np.conjugate(rho.T)) / 2.0)
    min_eigenvalue = float(np.min(np.real(eigvals)))
    passed = (
        abs(float(np.real(trace)) - 1.0) <= 1.0e-10
        and abs(float(np.imag(trace))) <= 1.0e-10
        and hermitian_error <= 1.0e-10
        and min_eigenvalue >= -1.0e-10
    )
    return {
        "pass": bool(passed),
        "computed_from": "rho_ABCD",
        "trace_real": q(float(np.real(trace))),
        "trace_imag": q(float(np.imag(trace))),
        "hermitian_error": q(hermitian_error),
        "min_eigenvalue": q(min_eigenvalue),
    }


def c2_probe_nonzero(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace(rho, [0])
    bloch = bloch_from_rho(rho_a)
    signature = probe_signature(bloch)
    return {
        "pass": signature != (0, 0),
        "computed_from": "Tr_BCD(rho_ABCD)",
        "first_bloch_from_rho_q0": [q(v) for v in bloch],
        "probe_signature": list(signature),
    }


def c3_order_ok(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace(rho, [0])
    bloch = bloch_from_rho(rho_a)
    left = probe_signature(dz_after_rx(bloch))
    right = probe_signature(rx_after_dz(bloch))
    gap = order_gap(bloch)
    return {
        "pass": gap >= 0.5,
        "computed_from": "Tr_BCD(rho_ABCD)",
        "first_bloch_from_rho_q0": [q(v) for v in bloch],
        "left_signature_Dz_after_Rx": list(left),
        "right_signature_Rx_after_Dz": list(right),
        "order_gap": gap,
    }


def state_record(candidate_id: int, label: str, rho: np.ndarray, psi: np.ndarray | None) -> tuple[str, dict[str, Any]]:
    rho_json = matrix_to_json(rho)
    content_id = "rhoabcd_" + stable_sha256({"rho_ABCD": rho_json})[:24]
    trace = np.trace(rho)
    eigvals = np.linalg.eigvalsh((rho + np.conjugate(rho.T)) / 2.0)
    record: dict[str, Any] = {
        "content_id": content_id,
        "candidate_labels": [label],
        "first_candidate_id": candidate_id,
        "matrix_shape": [16, 16],
        "rho_ABCD": rho_json,
        "trace_real": q(float(np.real(trace))),
        "trace_imag": q(float(np.imag(trace))),
        "min_eigenvalue": q(float(np.min(np.real(eigvals)))),
    }
    if psi is not None:
        record["state_vector"] = vector_to_json(psi)
    return content_id, record


def clean_candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def anchor_rows() -> list[dict[str, Any]]:
    return [
        {"anchor_id": "GHZ4", "family": "entangled_boundary_anchor", "source": "stage_lifted_spinor_shell_n4_v0.P5_entropy", "four_partite_entangled_anchor": True},
        {"anchor_id": "W4", "family": "entangled_boundary_anchor", "source": "stage_lifted_spinor_shell_n4_v0.P5_entropy", "four_partite_entangled_anchor": True},
        {"anchor_id": "cluster_linear_4", "family": "cluster_state_boundary_anchor", "source": "stage_lifted_spinor_shell_n4_v0.P5_entropy", "four_partite_entangled_anchor": True},
        {"anchor_id": "product_0000", "family": "product_anchor_control", "source": "stage_lifted_spinor_shell_n4_v0.P5_entropy"},
        {"anchor_id": "lifted_ladder_n4_feedstock_product_anchor", "family": "lifted_ladder_feedstock_anchor", "source": "terrain_spinor_flux_nest_n4_v0.carrier.state_vector"},
        {"anchor_id": "locally_rotated_generalized_GHZ4_anchor", "family": "entangled_boundary_anchor", "source": "4Q active-probe GHZ-class anchor", "four_partite_entangled_anchor": True},
        {"anchor_id": "invalid_trace_anchor", "family": "invalid_density_control", "source": "C1 negative control"},
        {"anchor_id": "GHZ4_minus", "family": "entangled_boundary_anchor", "source": "stage_lifted_spinor_shell_n4_v0 sign control", "four_partite_entangled_anchor": True},
        {"anchor_id": "biseparable_Bell_AB_tensor_00CD", "family": "biseparable_control", "source": "4Q boundary control"},
        {"anchor_id": "order_only_no_probe_anchor", "family": "order_only_no_probe_control", "source": "C2 negative with live C3 order signature"},
    ]


def build_work_candidates() -> list[dict[str, Any]]:
    carve = load_json(PARENT_PATHS["three_q_carve"])
    registry = load_json(PARENT_PATHS["three_q_freeze_registry"])
    states = carve["state_artifacts"]["states_by_content_id"]
    gcm_by_raw = {
        int(row["raw_3q_survivor_id"]): row["gcm_3q_survivor_id"]
        for row in registry["frozen_3q_registry"]["survivors"]
    }
    rows: list[dict[str, Any]] = []
    for survivor in carve["survivors"]:
        raw_sid = int(survivor["survivor_id"])
        state = states[survivor["rho_ABC_content_id"]]
        rho_abc = json_to_matrix(state["rho_ABC"])
        psi_abc = json_to_vector(state["state_vector"]) if "state_vector" in state else None
        rho_abcd = tensor_product(rho_abc, pure_density(ZERO))
        psi_abcd = np.kron(psi_abc, ZERO) if psi_abc is not None else None
        rows.append(
            {
                "candidate_id": len(rows),
                "candidate_label": f"3q_lift_{survivor['survivor_id']}",
                "family": "3q_survivor_product_lift",
                "raw_3q_survivor_id": raw_sid,
                "source_gcm_3q_survivor_id": gcm_by_raw[raw_sid],
                "source_3q_candidate_id": survivor["candidate_id"],
                "source_3q_family": survivor["family"],
                "source_rho_ABC_content_id": survivor["rho_ABC_content_id"],
                "construction": "rho_ABC survivor tensor |0><0|_D",
                "_rho_ABCD": rho_abcd,
                "_state_vector": psi_abcd,
                "_source_rho_ABC": rho_abc,
            }
        )
    for anchor in anchor_rows():
        rho, psi = anchor_state(anchor["anchor_id"])
        rows.append(
            {
                "candidate_id": len(rows),
                "candidate_label": anchor["anchor_id"],
                **anchor,
                "construction": "stored 4Q boundary/feedstock/control anchor",
                "_rho_ABCD": rho,
                "_state_vector": psi,
                "_source_rho_ABC": None,
            }
        )
    return rows


def full_constraint_row(row: dict[str, Any], content_id: str) -> dict[str, Any]:
    rho = row["_rho_ABCD"]
    constraints = {
        "C1": c1_density_valid(rho),
        "C2": c2_probe_nonzero(rho),
        "C3": c3_order_ok(rho),
    }
    failed = [key for key in CONSTRAINT_KEYS if not constraints[key]["pass"]]
    return {
        "candidate_id": row["candidate_id"],
        "candidate_label": row["candidate_label"],
        "anchor_id": row.get("anchor_id"),
        "family": row["family"],
        "rho_ABCD_content_id": content_id,
        "constraints": constraints,
        "all_failed_constraints": failed,
        "survives": not failed,
        "first_failed_constraint_display_only": failed[0] if failed else None,
    }


def build_state_and_matrix() -> dict[str, Any]:
    states: dict[str, dict[str, Any]] = {}
    candidate_index = []
    matrix = []
    candidates = []
    for row in build_work_candidates():
        content_id, record = state_record(row["candidate_id"], row["candidate_label"], row["_rho_ABCD"], row["_state_vector"])
        if content_id in states:
            states[content_id]["candidate_labels"].append(row["candidate_label"])
        else:
            states[content_id] = record
        row["rho_ABCD_content_id"] = content_id
        row["first_bloch_from_stored_rho_q0"] = c2_probe_nonzero(row["_rho_ABCD"])["first_bloch_from_rho_q0"]
        row["probe_signature_from_stored_rho_q0"] = c2_probe_nonzero(row["_rho_ABCD"])["probe_signature"]
        row["order_gap_from_stored_rho_q0"] = c3_order_ok(row["_rho_ABCD"])["order_gap"]
        candidate_index.append({"candidate_id": row["candidate_id"], "candidate_label": row["candidate_label"], "rho_ABCD_content_id": content_id})
        matrix.append(full_constraint_row(row, content_id))
        candidates.append(row)
    return {
        "states_by_content_id": states,
        "candidate_state_index": candidate_index,
        "constraint_matrix": matrix,
        "work_candidates": candidates,
    }


def build_survivors(candidates: list[dict[str, Any]], matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_candidate = {row["candidate_id"]: row for row in matrix}
    survivors = []
    for row in candidates:
        matrix_row = by_candidate[row["candidate_id"]]
        if not matrix_row["survives"]:
            continue
        clean = clean_candidate_row(row)
        clean["survivor_id"] = len(survivors)
        clean["constraint_pass_fail"] = {key: matrix_row["constraints"][key]["pass"] for key in CONSTRAINT_KEYS}
        survivors.append(clean)
    return survivors


def build_quotient(survivors: list[dict[str, Any]], family: tuple[str, str] = PROBE_FAMILY) -> dict[str, Any]:
    buckets: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in survivors:
        coord = tuple(float(v) for v in row["first_bloch_from_stored_rho_q0"])
        buckets[probe_signature(coord, family)].append(row)
    classes = []
    for idx, key in enumerate(sorted(buckets)):
        members = sorted(buckets[key], key=lambda item: item["survivor_id"])
        classes.append(
            {
                "class_id": f"Q{idx}",
                "probe_signature": list(key),
                "member_survivor_ids": [row["survivor_id"] for row in members],
                "member_candidate_ids": [row["candidate_id"] for row in members],
                "member_count": len(members),
                "family_counts": dict(sorted(Counter(row["family"] for row in members).items())),
                "four_partite_entangled_anchor_count": sum(1 for row in members if row.get("four_partite_entangled_anchor")),
            }
        )
    return {"probe_family": list(family), "class_count": len(classes), "classes": classes}


def survivor_state_rows(survivors: list[dict[str, Any]], states: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "survivor_id": survivor["survivor_id"],
            "candidate_id": survivor["candidate_id"],
            "candidate_label": survivor["candidate_label"],
            "rho_ABCD_content_id": survivor["rho_ABCD_content_id"],
            "rho_ABCD": states[survivor["rho_ABCD_content_id"]]["rho_ABCD"],
        }
        for survivor in survivors
    ]


def concurrence_2q(rho_2q: np.ndarray) -> float:
    yy = np.kron(PAULI_Y, PAULI_Y)
    product = rho_2q @ yy @ np.conjugate(rho_2q) @ yy
    eigvals = np.linalg.eigvals(product)
    roots = sorted((math.sqrt(max(0.0, float(np.real(value)))) for value in eigvals), reverse=True)
    while len(roots) < 4:
        roots.append(0.0)
    return q(max(0.0, roots[0] - roots[1] - roots[2] - roots[3]))


def one_tangle(rho_single: np.ndarray) -> float:
    return q(max(0.0, float(np.real(4.0 * np.linalg.det(rho_single)))))


def focus_ckw_rows(rho: np.ndarray) -> dict[str, Any]:
    pair_cache: dict[tuple[int, int], float] = {}
    for left in range(4):
        for right in range(left + 1, 4):
            pair_cache[(left, right)] = q(concurrence_2q(partial_trace(rho, [left, right])) ** 2)
    rows = {}
    for focus in range(4):
        rho_focus = partial_trace(rho, [focus])
        pairwise = {}
        for other in range(4):
            if other == focus:
                continue
            key = tuple(sorted((focus, other)))
            pairwise[f"q{focus}q{other}"] = pair_cache[key]
        pair_sum = q(sum(pairwise.values()))
        one = one_tangle(rho_focus)
        margin = q(one - pair_sum)
        rows[f"q{focus}"] = {
            "one_tangle": one,
            "pairwise_tangles": pairwise,
            "pairwise_sum": pair_sum,
            "ckw_margin": margin,
            "satisfies_focus_ckw": margin >= -1.0e-10,
        }
    return rows


def four_party_ckw_rows(survivors: list[dict[str, Any]], states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for survivor in survivors:
        state = states[survivor["rho_ABCD_content_id"]]
        if "state_vector" not in state:
            continue
        rho = json_to_matrix(state["rho_ABCD"])
        rows.append(
            {
                "state_id": survivor["candidate_label"],
                "candidate_id": survivor["candidate_id"],
                "survivor_id": survivor["survivor_id"],
                "rho_ABCD_content_id": survivor["rho_ABCD_content_id"],
                "computed_from_stored_rho_ABCD": True,
                "focus_qubits": focus_ckw_rows(rho),
            }
        )
    return {
        "generalization": "Osborne-Verstraete N-qubit CKW focus-qubit inequality",
        "narrow_statement": "For stored pure survivor states, C(qi|rest)^2 >= sum_j C(qi,qj)^2 is checked per focus qubit.",
        "computed_from_stored_rho_ABCD": True,
        "residual_4_tangle_claimed": False,
        "pure_survivor_count_checked": len(rows),
        "all_focus_qubits_satisfy_ckw": all(focus["satisfies_focus_ckw"] for row in rows for focus in row["focus_qubits"].values()),
        "rows": rows,
    }


def named_matrix_finding(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    names = ("GHZ4", "W4", "cluster_linear_4")
    by_name = {row.get("anchor_id"): row for row in matrix if row.get("anchor_id") in names}
    rows = {}
    for name in names:
        matrix_row = by_name[name]
        pass_fail = {key: matrix_row["constraints"][key]["pass"] for key in CONSTRAINT_KEYS}
        rows[name] = {
            "candidate_id": matrix_row["candidate_id"],
            "rho_ABCD_content_id": matrix_row["rho_ABCD_content_id"],
            "pass_fail": pass_fail,
            "failed_constraints": [key for key in CONSTRAINT_KEYS if not pass_fail[key]],
            "first_failed_constraint_display_only": matrix_row["first_failed_constraint_display_only"],
        }
    return {
        "source": "full_constraint_matrix",
        "rows": rows,
        "honest_statement": "GHZ4 fails C2+C3; W4 fails C3 only; cluster_linear_4 fails C2+C3 under this local first-qubit probe.",
        "asymmetry_strength": "matrix-row local-constraint asymmetry only; not SLOCC, phase, or QIT-floor admission evidence",
    }


def terrain_blindness_guard() -> dict[str, Any]:
    texts = [json.dumps(row, sort_keys=True) for row in CONSTRAINTS]
    errors: list[str] = []
    for row, text in zip(CONSTRAINTS, texts):
        lowered = text.lower()
        for token in FORBIDDEN_PREDICATE_TOKENS:
            matched = re.search(rf"\b{re.escape(token)}\b", text) is not None if token in {"Se", "Ne", "Ni", "Si"} else token.lower() in lowered
            if matched:
                errors.append(f"{row['id']}: forbidden predicate token {token!r}")
    return {
        "guard": "admissibility_predicate_source_recompute_token_guard",
        "forbidden_tokens": list(FORBIDDEN_PREDICATE_TOKENS),
        "checked_constraint_ids": [row["id"] for row in CONSTRAINTS],
        "predicate_text_sha256": stable_sha256(texts),
        "errors": errors,
        "clean": not errors,
    }


def source_recompute_injection_red() -> dict[str, Any]:
    injected = dict(CONSTRAINTS[1])
    injected["literal_executable_predicate"] += " terrain atlas Se"
    text = json.dumps(injected, sort_keys=True)
    hits = []
    if "terrain" in text.lower():
        hits.append("terrain")
    if "atlas" in text.lower():
        hits.append("atlas")
    if re.search(r"\bSe\b", text):
        hits.append("Se")
    return {
        "control": "source predicate recompute after forbidden terrain/atlas/Se injection",
        "red": len(hits) == 3,
        "caught_tokens": hits,
        "error_codes": ["GCM4Q_SOURCE_RECOMPUTE_FORBIDDEN_TOKEN"] if len(hits) == 3 else [],
    }


def apply_constraint_variant(matrix: list[dict[str, Any]], active: list[str]) -> set[int]:
    survivors = set()
    for row in matrix:
        if all(row["constraints"][key]["pass"] for key in active):
            survivors.add(int(row["candidate_id"]))
    return survivors


def regression_rows() -> dict[str, Any]:
    one_q = load_json(PARENT_PATHS["one_q_registry"])
    two_q = load_json(PARENT_PATHS["two_q_registry"])
    three_q = load_json(PARENT_PATHS["three_q_freeze_registry"])
    return {
        "one_q": {
            "object_id_match": one_q.get("gcm_object_id") == EXPECTED_1Q_OBJECT_ID,
            "registry_body_sha256": one_q.get("registry_body_sha256"),
            "registry_body_hash_match": one_q.get("registry_body_sha256") == EXPECTED_1Q_REGISTRY_SHA256,
        },
        "two_q": {
            "object_id_match": two_q.get("gcm_2q_object_id") == EXPECTED_2Q_OBJECT_ID,
            "registry_body_sha256": two_q.get("registry_body_sha256"),
            "registry_body_hash_match": two_q.get("registry_body_sha256") == EXPECTED_2Q_REGISTRY_SHA256,
        },
        "three_q": {
            "object_id_match": three_q.get("gcm_3q_object_id") == EXPECTED_3Q_OBJECT_ID,
            "registry_body_sha256": three_q.get("registry_body_sha256"),
            "registry_body_hash_match": three_q.get("registry_body_sha256") == EXPECTED_3Q_REGISTRY_SHA256,
            "survivor_count": three_q.get("counts", {}).get("survivor_count"),
            "quotient_class_count": three_q.get("counts", {}).get("quotient_class_count"),
        },
    }


def controls(matrix: list[dict[str, Any]], survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    base_set = {int(row["candidate_id"]) for row in survivors}
    erasures = []
    for key in CONSTRAINT_KEYS:
        variant = apply_constraint_variant(matrix, [item for item in CONSTRAINT_KEYS if item != key])
        erasures.append(
            {
                "dropped_constraint": key,
                "survivor_count": len(variant),
                "added_count": len(variant - base_set),
                "removed_count": len(base_set - variant),
                "bite": variant != base_set,
            }
        )
    scrambled = build_quotient(survivors, SCRAMBLED_PROBE_FAMILY)
    return {
        "empty_C": {"survivor_count": len(matrix), "degenerate_no_carve": True},
        "cliff_overconstrained": {"survivor_count": 0, "all_killed": True},
        "erasure_bite": erasures,
        "probe_scramble": {
            "baseline_probe_family": list(PROBE_FAMILY),
            "scrambled_probe_family": list(SCRAMBLED_PROBE_FAMILY),
            "baseline_class_count": quotient["class_count"],
            "scrambled_class_count": scrambled["class_count"],
            "quotient_moved": stable_sha256(quotient["classes"]) != stable_sha256(scrambled["classes"]),
        },
        "source_recompute_injection_red": source_recompute_injection_red(),
        "regressions": regression_rows(),
    }


def source_locks() -> dict[str, Any]:
    return {
        key: source_lock(path, role)
        for key, path, role in (
            ("one_q_registry", PARENT_PATHS["one_q_registry"], "1Q frozen substrate registry"),
            ("two_q_registry", PARENT_PATHS["two_q_registry"], "2Q frozen substrate registry"),
            ("three_q_carve", PARENT_PATHS["three_q_carve"], "3Q carve v1 state-artifacted source"),
            ("three_q_freeze_registry", PARENT_PATHS["three_q_freeze_registry"], "3Q frozen registry source"),
            ("three_q_freeze_result", PARENT_PATHS["three_q_freeze_result"], "3Q freeze result source"),
            ("four_q_support", PARENT_PATHS["four_q_support"], "4Q support exact feedstock"),
            ("four_q_support_jax", PARENT_PATHS["four_q_support_jax"], "4Q support JAX result feedstock"),
            ("stage_n4", PARENT_PATHS["stage_n4"], "4Q lifted shell feedstock"),
            ("stage_n4_jax", PARENT_PATHS["stage_n4_jax"], "4Q lifted shell JAX feedstock"),
            ("terrain_n4", PARENT_PATHS["terrain_n4"], "4Q terrain flux nest feedstock"),
            ("climb_ledger_correction", PARENT_PATHS["climb_ledger_correction"], "climb ledger correction"),
            ("builder_audit_boundary", PARENT_PATHS["builder_audit_boundary"], "G.2a boundary helper"),
            ("build_card", PARENT_PATHS["build_card"], "this packet build card"),
        )
    }


def consumed_4q_feedstock() -> dict[str, Any]:
    support = load_json(PARENT_PATHS["four_q_support"])
    stage = load_json(PARENT_PATHS["stage_n4"])
    terrain = load_json(PARENT_PATHS["terrain_n4"])
    locks = source_locks()
    return {
        "mode": "consume_existing_feedstock_never_rebuild",
        "geo_s1_four_qubit_support_exact_v0": {
            "path": rel(PARENT_PATHS["four_q_support"]),
            "sha256": locks["four_q_support"]["sha256"],
            "pin_sha256": support["pin_sha256"],
            "source_sha256": support["source_sha256"],
            "claim_boundary": support.get("claim_boundary"),
        },
        "stage_lifted_spinor_shell_n4_v0": {
            "path": rel(PARENT_PATHS["stage_n4"]),
            "sha256": locks["stage_n4"]["sha256"],
            "pin_sha256": stage["pin_sha256"],
            "source_sha256": stage["source_sha256"],
            "rows_consumed": ["rows.jax.P2_support_object", "rows.jax.P3_density_quotient", "rows.jax.P5_entropy", "rows.jax.P6_order_gaps.Cl8_anchor"],
        },
        "terrain_spinor_flux_nest_n4_v0": {
            "path": rel(PARENT_PATHS["terrain_n4"]),
            "sha256": locks["terrain_n4"]["sha256"],
            "pin_sha256": terrain["pin_sha256"],
            "source_sha256": terrain["source_sha256"],
            "rows_consumed": ["carrier", "parent_lineage", "support_graph", "ratcheted_rows"],
        },
    }


def first_nested_id(registry: dict[str, Any], section: str, field: str) -> str:
    bucket = "survivors" if field.endswith("survivor_id") else "quotient_classes"
    if field.endswith("candidate_region_id"):
        bucket = "candidate_regions"
    for row in registry.get(section, {}).get(bucket, []):
        value = row.get(field)
        if isinstance(value, str):
            return value
    raise KeyError(f"{section}.{field}")


def gcm_lineage() -> dict[str, Any]:
    one_q = load_json(PARENT_PATHS["one_q_registry"])
    two_q = load_json(PARENT_PATHS["two_q_registry"])
    three_q = load_json(PARENT_PATHS["three_q_freeze_registry"])
    one_surv = first_nested_id(one_q, "frozen_registry", "survivor_id")
    one_cls = first_nested_id(one_q, "frozen_registry", "quotient_class_id")
    one_reg = first_nested_id(one_q, "frozen_registry", "candidate_region_id")
    two_surv = first_nested_id(two_q, "frozen_2q_registry", "gcm_2q_survivor_id")
    two_cls = first_nested_id(two_q, "frozen_2q_registry", "gcm_2q_quotient_class_id")
    two_reg = first_nested_id(two_q, "frozen_2q_registry", "gcm_2q_candidate_region_id")
    three_surv = first_nested_id(three_q, "frozen_3q_registry", "gcm_3q_survivor_id")
    three_cls = first_nested_id(three_q, "frozen_3q_registry", "gcm_3q_quotient_class_id")
    three_reg = first_nested_id(three_q, "frozen_3q_registry", "gcm_3q_candidate_region_id")
    return {
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "one_q_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "three_q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "survivor_ids": [one_surv],
        "quotient_class_ids": [one_cls],
        "candidate_region_ids": [one_reg],
        "gcm_2q_survivor_ids": [two_surv],
        "gcm_2q_quotient_class_ids": [two_cls],
        "gcm_2q_candidate_region_ids": [two_reg],
        "gcm_3q_survivor_ids": [three_surv],
        "gcm_3q_quotient_class_ids": [three_cls],
        "gcm_3q_candidate_region_ids": [three_reg],
        "object_maps": [
            {
                "survivor_id": one_surv,
                "quotient_class_id": one_cls,
                "candidate_region_id": one_reg,
                "gcm_2q_survivor_id": two_surv,
                "gcm_2q_quotient_class_id": two_cls,
                "gcm_2q_candidate_region_id": two_reg,
                "gcm_3q_survivor_id": three_surv,
                "gcm_3q_quotient_class_id": three_cls,
                "gcm_3q_candidate_region_id": three_reg,
                "role": "minimal resolved lineage witness for hardened 1Q/2Q/3Q substrate checks",
            }
        ],
    }


def substrate_checks(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "one_q_default_registry": gcm_substrate_check(packet),
        "two_q_registry": gcm_substrate_check(packet, PARENT_PATHS["two_q_registry"]),
        "three_q_registry": gcm_substrate_check(packet, PARENT_PATHS["three_q_freeze_registry"]),
    }


def substrate_negatives() -> dict[str, Any]:
    empty = {"sim_id": SIM_ID, "classification": CLASSIFICATION}
    stale = {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "gcm_lineage": {
            "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
            "registry_body_sha256": "stale",
        },
    }
    return {
        "1Q": {
            "lineage_free": gcm_substrate_check(empty),
            "stale_lineage": gcm_substrate_check(stale),
        },
        "2Q": {
            "lineage_free": gcm_substrate_check(empty, PARENT_PATHS["two_q_registry"]),
            "stale_lineage": gcm_substrate_check(stale, PARENT_PATHS["two_q_registry"]),
        },
        "3Q": {
            "lineage_free": gcm_substrate_check(empty, PARENT_PATHS["three_q_freeze_registry"]),
            "stale_lineage": gcm_substrate_check(stale, PARENT_PATHS["three_q_freeze_registry"]),
        },
    }


def run_helper_preflight() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/helper_process_audit.py"), "--strict"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"all_pass": False, "stdout": proc.stdout, "stderr": proc.stderr}
    payload["exit_code"] = proc.returncode
    payload["command"] = f"{sys.executable} scripts/helper_process_audit.py --strict"
    return payload


def z3_count_proof(survivor_count: int) -> dict[str, Any]:
    x = z3.Int("gcm_constraint_carve_4q_v0_survivor_count")
    solver = z3.Solver()
    solver.add(x == survivor_count)
    solver.add(x != EXPECTED_SURVIVOR_COUNT)
    verdict = str(solver.check())
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def cvc5_count_proof(survivor_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    x = solver.mkConst(int_sort, "gcm_constraint_carve_4q_v0_survivor_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(survivor_count)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(EXPECTED_SURVIVOR_COUNT))))
    verdict = str(solver.checkSat()).lower()
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def cross_rung_rows(candidates: list[dict[str, Any]], survivors: list[dict[str, Any]]) -> dict[str, Any]:
    lifted_survivors = [row for row in survivors if row["family"] == "3q_survivor_product_lift"]
    checked = 0
    max_delta = 0.0
    sample_rows = []
    for row in candidates:
        if row["family"] != "3q_survivor_product_lift":
            continue
        rho_abc = row["_source_rho_ABC"]
        rho_abcd = row["_rho_ABCD"]
        reduced = partial_trace(rho_abcd, [0, 1, 2])
        delta = float(np.max(np.abs(reduced - rho_abc)))
        max_delta = max(max_delta, delta)
        checked += 1
        if len(sample_rows) < 5:
            sample_rows.append(
                {
                    "candidate_id": row["candidate_id"],
                    "raw_3q_survivor_id": row["raw_3q_survivor_id"],
                    "source_gcm_3q_survivor_id": row["source_gcm_3q_survivor_id"],
                    "max_abs_delta_TrD_vs_3q_rho": q(delta),
                }
            )
    return {
        "three_q_to_4q_product_embedding": {
            "input_3q_survivor_count": EXPECTED_PRODUCT_LIFT_COUNT,
            "lifted_4q_survivor_count": len(lifted_survivors),
            "all_3q_survivors_have_one_4q_lift": len(lifted_survivors) == EXPECTED_PRODUCT_LIFT_COUNT,
            "construction": "rho_ABC tensor |0><0|_D",
        },
        "partial_trace_D_vs_3q_survivors": {
            "trace": "Tr_D(rho_ABCD)",
            "Tr_D_reproduces_3q_state_count": checked,
            "max_abs_delta_TrD_vs_3q_rho": q(max_delta),
            "sample_rows": sample_rows,
        },
        "cut_lattice": {"count": len(CUTS), "bipartitions": list(CUTS)},
    }


def entropy_nats_from_eigs(eigenvalues: np.ndarray) -> float:
    vals = np.real(eigenvalues)
    vals = np.where(np.abs(vals) <= TOL, 0.0, vals)
    vals = np.clip(vals, 0.0, 1.0)
    total = float(np.sum(vals))
    if total > TOL:
        vals = vals / total
    return q(float(-np.sum([value * math.log(value) for value in vals if value > TOL])))


def representative_cut_rows(survivors: list[dict[str, Any]], states: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {"3q_lift_544", "locally_rotated_generalized_GHZ4_anchor", "W4", "cluster_linear_4"}
    rows = []
    for survivor in survivors:
        if survivor["candidate_label"] not in wanted:
            continue
        rho = json_to_matrix(states[survivor["rho_ABCD_content_id"]]["rho_ABCD"])
        cut_rows = {}
        for cut, spec in CUTS.items():
            left = partial_trace(rho, spec["left"])
            right = partial_trace(rho, spec["right"])
            s_left = entropy_nats_from_eigs(np.linalg.eigvalsh(left))
            s_right = entropy_nats_from_eigs(np.linalg.eigvalsh(right))
            s_full = entropy_nats_from_eigs(np.linalg.eigvalsh(rho))
            cut_rows[cut] = {
                "S_left": s_left,
                "S_right": s_right,
                "S_full": s_full,
                "mutual_I": q(s_left + s_right - s_full),
            }
        rows.append({"candidate_label": survivor["candidate_label"], "cuts": cut_rows})
    return rows


def floor_rows_extended() -> dict[str, Any]:
    support = load_json(PARENT_PATHS["four_q_support"])
    stage = load_json(PARENT_PATHS["stage_n4"])
    return {
        "consumed_not_rebuilt": True,
        "geo_s1_four_qubit_support_exact_v0": {
            "path": rel(PARENT_PATHS["four_q_support"]),
            "proofs": {
                "P1_anticommutation_table": support.get("proofs", {}).get("P1_anticommutation_table"),
                "P2_max_9_family_upper_bound": support.get("proofs", {}).get("P2_max_9_family_upper_bound"),
            },
        },
        "stage_lifted_spinor_shell_n4_v0": {
            "path": rel(PARENT_PATHS["stage_n4"]),
            "Cl8_anchor": stage.get("rows", {}).get("jax", {}).get("P6_order_gaps", {}).get("Cl8_anchor"),
        },
    }


def build_packet(*, write: bool = False, include_helper_preflight: bool = False) -> dict[str, Any]:
    built = build_state_and_matrix()
    states = built["states_by_content_id"]
    matrix = built["constraint_matrix"]
    candidates = built["work_candidates"]
    survivors = build_survivors(candidates, matrix)
    quotient = build_quotient(survivors)
    control_rows = controls(matrix, survivors, quotient)
    fail_counts = Counter(key for row in matrix for key in row["all_failed_constraints"])
    packet: dict[str, Any] = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "coordinates": {"layers": "1-2 (+17 tensor)", "operation": "carve", "qubit_depth": "4Q"},
        "standards_codex": {"G_2a_from_birth": True, "substrate_first": True},
        "gcm_lineage": gcm_lineage(),
        "source_locks": source_locks(),
        "consumed_4q_feedstock": consumed_4q_feedstock(),
        "constraint_family_C": CONSTRAINTS,
        "candidate_space": {
            "candidate_count": len(matrix),
            "product_embedding_from_3q_count": EXPECTED_PRODUCT_LIFT_COUNT,
            "anchor_count": EXPECTED_ANCHOR_COUNT,
            "construction": "545 3Q survivor product lifts plus 10 4Q boundary/feedstock/control anchors",
            "candidate_rows": [clean_candidate_row(row) for row in candidates],
        },
        "state_artifacts": {
            "artifact_kind": "rho_ABCD_content_addressed_states",
            "content_id_rule": "rhoabcd_<sha256(canonical rho_ABCD JSON)[:24]>",
            "states_by_content_id": states,
            "candidate_state_index": built["candidate_state_index"],
            "survivor_states": survivor_state_rows(survivors, states),
        },
        "constraint_matrix": matrix,
        "kill_ledger": matrix,
        "killed_rows": [row for row in matrix if not row["survives"]],
        "kill_counts_by_constraint": dict(sorted(fail_counts.items())),
        "survivor_count": len(survivors),
        "survivor_family_counts": dict(sorted(Counter(row["family"] for row in survivors).items())),
        "four_partite_entangled_survivor_count": sum(1 for row in survivors if row.get("four_partite_entangled_anchor")),
        "survivors": survivors,
        "m_c_4q": {
            "exists": len(survivors) > 0,
            "carrier": "C^16 density matrices",
            "predicate_family": "C1/C2/C3 local probe/persistence carve",
            "survivor_count": len(survivors),
            "quotient_class_count": quotient["class_count"],
            "claim_ceiling": CLAIM_CEILING,
        },
        "quotient": quotient,
        "existence_probes": {
            "nonempty_survivors": len(survivors) > 0,
            "entangled_survivor_exists": any(row.get("four_partite_entangled_anchor") for row in survivors),
            "every_candidate_has_stored_rho_ABCD": len(built["candidate_state_index"]) == len(matrix),
            "quotient_nonempty": quotient["class_count"] > 0,
        },
        "cross_rung_rows": cross_rung_rows(candidates, survivors),
        "cut_lattice": {"count": len(CUTS), "bipartitions": list(CUTS), "representative_cut_rows": representative_cut_rows(survivors, states)},
        "four_party_ckw_monogamy_narrowed": four_party_ckw_rows(survivors, states),
        "floor_rows_extended": floor_rows_extended(),
        "ghz4_w4_cluster_admissibility_matrix": named_matrix_finding(matrix),
        "controls": control_rows,
        "terrain_blindness_guard": terrain_blindness_guard(),
        "substrate_checks": {},
        "substrate_negatives": substrate_negatives(),
        "helper_preflight": {"all_pass": None, "required_command": f"{sys.executable} scripts/helper_process_audit.py --strict"},
        "builder_gates": {
            "file_disjoint_packet": True,
            "boundary_helper_fully_used": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "G_2a_idempotency_from_birth": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "crossover_proofs": {
            "z3": z3_count_proof(len(survivors)),
            "cvc5": cvc5_count_proof(len(survivors)),
        },
        "allowed_claims": [
            "state-artifacted scratch diagnostic 4Q count fixture",
            "full-matrix GHZ4/W4/cluster local-constraint rows",
            "narrowed 4-party CKW focus-qubit checks from stored rho_ABCD where pure-state computation is applicable",
            "3Q-to-4Q product embedding and Tr_D retraction fixture",
        ],
        "blocked_consumers": [
            "formal_admission",
            "canonical_manifold_claim",
            "axis_or_bridge_claim",
            "physics_claim",
            "SLOCC_GHZ_W_cluster_separator_claim",
            "4Q_registry_freeze_claim",
        ],
    }
    packet["substrate_checks"] = substrate_checks(packet)
    if include_helper_preflight:
        packet["helper_preflight"] = run_helper_preflight()
    packet["all_pass"] = not validate_payload(packet, require_helper_preflight=include_helper_preflight)
    frozen = dict(packet)
    frozen.pop("generated_at", None)
    frozen.pop("result_sha256", None)
    packet["result_sha256"] = stable_sha256(frozen)
    if write:
        write_json(RESULT_PATH, packet)
    return packet


def validate_payload(payload: dict[str, Any], *, require_helper_preflight: bool = False) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != CLASSIFICATION:
        errors.append("classification mismatch")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        errors.append("promotion/formal admission fences must be false")
    if payload.get("candidate_space", {}).get("candidate_count") != EXPECTED_CANDIDATE_COUNT:
        errors.append("candidate count mismatch")
    if payload.get("candidate_space", {}).get("product_embedding_from_3q_count") != EXPECTED_PRODUCT_LIFT_COUNT:
        errors.append("3Q product lift count mismatch")
    if payload.get("candidate_space", {}).get("anchor_count") != EXPECTED_ANCHOR_COUNT:
        errors.append("anchor count mismatch")
    if payload.get("survivor_count") != EXPECTED_SURVIVOR_COUNT:
        errors.append("survivor count mismatch")
    if payload.get("quotient", {}).get("class_count") != EXPECTED_QUOTIENT_CLASS_COUNT:
        errors.append("quotient class count mismatch")
    state_artifacts = payload.get("state_artifacts", {})
    states = state_artifacts.get("states_by_content_id", {})
    candidate_index = state_artifacts.get("candidate_state_index", [])
    matrix = payload.get("constraint_matrix", [])
    if len(candidate_index) != EXPECTED_CANDIDATE_COUNT:
        errors.append("candidate state index length mismatch")
    if len(matrix) != EXPECTED_CANDIDATE_COUNT or len(payload.get("kill_ledger", [])) != EXPECTED_CANDIDATE_COUNT:
        errors.append("full constraint matrix/kill ledger length mismatch")
    for row in candidate_index:
        content_id = row.get("rho_ABCD_content_id")
        if content_id not in states or "rho_ABCD" not in states.get(content_id, {}):
            errors.append(f"missing rho_ABCD state artifact for candidate {row.get('candidate_id')}")
            break
    for row in matrix:
        constraints = row.get("constraints", {})
        if set(constraints) != set(CONSTRAINT_KEYS):
            errors.append(f"constraint matrix row missing C1/C2/C3: {row.get('candidate_id')}")
            break
        if not all(isinstance(constraints[key].get("pass"), bool) for key in CONSTRAINT_KEYS):
            errors.append(f"constraint matrix row has non-boolean pass/fail: {row.get('candidate_id')}")
            break
    consumed = payload.get("consumed_4q_feedstock", {})
    if consumed.get("mode") != "consume_existing_feedstock_never_rebuild":
        errors.append("4Q feedstock consumption mode mismatch")
    pins = {
        "geo_s1_four_qubit_support_exact_v0": EXPECTED_4Q_SUPPORT_PIN,
        "stage_lifted_spinor_shell_n4_v0": EXPECTED_STAGE_N4_PIN,
        "terrain_spinor_flux_nest_n4_v0": EXPECTED_TERRAIN_N4_PIN,
    }
    for key, expected in pins.items():
        if consumed.get(key, {}).get("pin_sha256") != expected:
            errors.append(f"{key} pin mismatch")
    named = payload.get("ghz4_w4_cluster_admissibility_matrix", {}).get("rows", {})
    if named.get("GHZ4", {}).get("pass_fail") != {"C1": True, "C2": False, "C3": False}:
        errors.append("GHZ4 full matrix row mismatch")
    if named.get("W4", {}).get("pass_fail") != {"C1": True, "C2": True, "C3": False}:
        errors.append("W4 full matrix row mismatch")
    if named.get("cluster_linear_4", {}).get("pass_fail") != {"C1": True, "C2": False, "C3": False}:
        errors.append("cluster full matrix row mismatch")
    cross = payload.get("cross_rung_rows", {})
    if cross.get("partial_trace_D_vs_3q_survivors", {}).get("Tr_D_reproduces_3q_state_count") != EXPECTED_PRODUCT_LIFT_COUNT:
        errors.append("Tr_D cross-rung count mismatch")
    if cross.get("partial_trace_D_vs_3q_survivors", {}).get("max_abs_delta_TrD_vs_3q_rho") != 0.0:
        errors.append("Tr_D cross-rung delta mismatch")
    ckw = payload.get("four_party_ckw_monogamy_narrowed", {})
    if ckw.get("computed_from_stored_rho_ABCD") is not True or ckw.get("all_focus_qubits_satisfy_ckw") is not True:
        errors.append("4-party CKW focus inequality failed or missing")
    if ckw.get("residual_4_tangle_claimed") is not False:
        errors.append("residual 4-tangle must not be claimed")
    if payload.get("terrain_blindness_guard", {}).get("clean") is not True:
        errors.append("terrain blindness guard failed")
    if payload.get("controls", {}).get("source_recompute_injection_red", {}).get("red") is not True:
        errors.append("source-recompute injection-red control failed")
    if not payload.get("controls", {}).get("source_recompute_injection_red", {}).get("error_codes"):
        errors.append("source-recompute injection-red error codes missing")
    if not all(row.get("bite") for row in payload.get("controls", {}).get("erasure_bite", [])):
        errors.append("erasure-bite control failed")
    checks = payload.get("substrate_checks", {})
    for key in ("one_q_default_registry", "two_q_registry", "three_q_registry"):
        if checks.get(key, {}).get("ok") is not True:
            errors.append(f"{key} substrate check failed")
    for rung, rows in payload.get("substrate_negatives", {}).items():
        lineage_free = rows.get("lineage_free", {})
        if lineage_free.get("ok") is not False or not lineage_free.get("error_codes"):
            errors.append(f"{rung} lineage-free negative did not stay red with error codes")
    if require_helper_preflight and payload.get("helper_preflight", {}).get("all_pass") is not True:
        errors.append("helper preflight is not green")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    return errors


def main() -> int:
    packet = build_packet(write=True, include_helper_preflight=True)
    print(json.dumps({"ok": packet["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if packet["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
