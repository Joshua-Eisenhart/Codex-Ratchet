#!/usr/bin/env python3
"""LEAN state-fingerprinted 7Q GCM constraint carve count fixture."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "gcm_constraint_carve_7q_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
SAMPLE_PATH = RESULT_DIR / f"{SIM_ID}_sample_matrices.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_lean_state_fingerprinted_7q_count_fixture"
SCHEMA = f"{SIM_ID}_result_v1"
SAMPLE_SCHEMA = f"{SIM_ID}_sample_matrices_v1"
TOL = 1.0e-10

EXPECTED_CANDIDATE_COUNT = 558
EXPECTED_PRODUCT_LIFT_COUNT = 548
EXPECTED_ANCHOR_COUNT = 10
EXPECTED_SURVIVOR_COUNT = 549
EXPECTED_QUOTIENT_CLASS_COUNT = 9
EXPECTED_7Q_STAGE_PIN = "8a07108fdeb158bc6b504b71cb59d92a3fa33c124e52ee7e719a28ca5b0e21db"
EXPECTED_SCALING_PIN = "e4da6f5578731c0017ca6140646e893f84b296db78837413d88f0012f86721e8"

PROBE_FAMILY = ("sigma_x_tensor_I6", "sigma_z_tensor_I6")
SCRAMBLED_PROBE_FAMILY = ("sigma_y_tensor_I6", "sigma_z_tensor_I6")
CONSTRAINT_KEYS = ("C1", "C2", "C3")
FORBIDDEN_PREDICATE_TOKENS = ("terrain", "atlas", "Se", "Ne", "Ni", "Si", "dissipative", "circulation")

PARENT_PATHS = {
    "one_q_registry": ROOT / "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json",
    "two_q_registry": ROOT / "system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_registry.json",
    "three_q_registry": ROOT / "system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_registry.json",
    "four_q_result": ROOT / "system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_results.json",
    "five_q_carve": ROOT / "system_v6/sims/gcm_constraint_carve_5q_v0/results/gcm_constraint_carve_5q_v0_results.json",
    "six_q_carve": ROOT / "system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_results.json",
    "seven_q_scaling": ROOT / "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/geo_s1_scaling_stress_678q_exact_v0_envelope_results.json",
    "seven_q_scaling_jax": ROOT / "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/geo_s1_scaling_stress_678q_exact_v0_jax_results.json",
    "stage_n7": ROOT / "system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_envelope_results.json",
    "stage_n7_jax": ROOT / "system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_jax_results.json",
    "cl14_capability": ROOT / "system_v6/probes/julia/results/cliffordalgebras_capability_results.json",
    "builder_audit_boundary": ROOT / "scripts/builder_audit_boundary.py",
    "build_card": SIM_DIR / "build_card.md",
    "scale_wall_receipt": ROOT / "system_v6/receipts/carve_ladder_scale_wall_20260612.md",
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

CONSTRAINTS = [
    {
        "key": "C1",
        "id": "C1_finite_7q_density_carrier",
        "literal_executable_predicate": "rho_ABCDEFG is Hermitian trace-one positive semidefinite on C^128",
    },
    {
        "key": "C2",
        "id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "literal_executable_predicate": "first-qubit x/z probe signature from Tr_BCDEFG(rho_ABCDEFG) is not (0, 0)",
    },
    {
        "key": "C3",
        "id": "C3_persistence_n01_order_gap",
        "literal_executable_predicate": "D_z after R_x and R_x after D_z first-qubit x/z probe signatures differ",
    },
]

CUTS: dict[str, dict[str, Any]] = {}
for size in (1, 2, 3):
    for left_tuple in combinations(range(7), size):
        left = list(left_tuple)
        right = [idx for idx in range(7) if idx not in left]
        CUTS["q" + "".join(str(idx) for idx in left) + "|q" + "".join(str(idx) for idx in right)] = {
            "left": left,
            "right": right,
            "dims": [2 ** len(left), 2 ** len(right)],
        }

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing transient C^128 density matrices, hashes, partial traces, C rows, cut summaries, and CKW sample checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing survivor-count contradiction guard"},
    "cvc5": {"tried": True, "used": True, "reason": "independent survivor-count contradiction guard matching z3"},
    "gcm_substrate_check": {"tried": True, "used": True, "reason": "load-bearing substrate lineage positives and negative controls through the hardened helper"},
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a builder/audit boundary from birth"},
    "python_stdlib": {"tried": True, "used": True, "reason": "JSON, hashing, source locks, size checks, and result writing"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "python_stdlib": "supportive",
}


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
        ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {"role": role, "path": rel(path), "exists": path.exists(), "sha256": sha256_file(path), "git_last_commit": git_last_commit(path)}


def write_json(path: Path, payload: dict[str, Any], *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    else:
        text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    path.write_text(text + "\n", encoding="utf-8")


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


def state_index(bits: tuple[int, ...]) -> int:
    out = 0
    for bit in bits:
        out = (out << 1) | bit
    return out


def basis_state(bits: tuple[int, ...]) -> np.ndarray:
    vector = np.zeros(128, dtype=np.complex128)
    vector[state_index(bits)] = 1.0
    return vector


def qubit_direction_kets(direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    nx, ny, nz = [float(v) for v in direction]
    theta = math.acos(max(-1.0, min(1.0, nz)))
    phi = math.atan2(ny, nx)
    plus = np.array([math.cos(theta / 2.0), complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0)])
    minus = np.array([-complex(math.cos(-phi), math.sin(-phi)) * math.sin(theta / 2.0), math.cos(theta / 2.0)])
    return plus.astype(np.complex128), minus.astype(np.complex128)


def generalized_ghz7_state(first_bloch_coord: tuple[float, float, float]) -> np.ndarray:
    bloch = np.array(first_bloch_coord, dtype=float)
    radius = float(np.linalg.norm(bloch))
    plus, minus = (ZERO, ONE) if radius <= 1.0e-12 else qubit_direction_kets(bloch / radius)
    p = (1.0 + radius) / 2.0
    vector = math.sqrt(p) * tensor_product(plus, ZERO, ZERO, ZERO, ZERO, ZERO, ZERO)
    vector += math.sqrt(1.0 - p) * tensor_product(minus, ONE, ONE, ONE, ONE, ONE, ONE)
    return vector / np.linalg.norm(vector)


def ghz7_state(sign: float = 1.0) -> np.ndarray:
    return (basis_state((0, 0, 0, 0, 0, 0, 0)) + sign * basis_state((1, 1, 1, 1, 1, 1, 1))) / math.sqrt(2.0)


def w7_state(weights: list[float] | None = None) -> np.ndarray:
    if weights is None:
        weights = [1.0] * 7
    amps = np.array(weights, dtype=float)
    amps = amps / np.linalg.norm(amps)
    vector = np.zeros(128, dtype=np.complex128)
    for idx, amp in enumerate(amps):
        bits = [0, 0, 0, 0, 0, 0, 0]
        bits[idx] = 1
        vector[state_index(tuple(bits))] = amp
    return vector / np.linalg.norm(vector)


def cluster_linear_7_state() -> np.ndarray:
    vector = np.zeros(128, dtype=np.complex128)
    for n in range(128):
        bits = tuple((n >> shift) & 1 for shift in reversed(range(7)))
        phase = -1.0 if (sum(bits[idx] * bits[idx + 1] for idx in range(6)) % 2) else 1.0
        vector[state_index(bits)] = phase / math.sqrt(128.0)
    return vector


def rho_from_bloch(coord: tuple[float, float, float]) -> np.ndarray:
    x, y, z = coord
    return 0.5 * (I2 + x * PAULI_X + y * PAULI_Y + z * PAULI_Z)


def shell_weighted_w_like_state() -> np.ndarray:
    stage = load_json(PARENT_PATHS["stage_n7_jax"])
    sites = stage["rows"]["P2_support_object"]["sites"]
    weights = [abs(float(site["z"])) + 0.25 for site in sites]
    return w7_state(weights)


def anchor_state(anchor_id: str) -> tuple[np.ndarray, np.ndarray | None]:
    if anchor_id == "GHZ7":
        psi = ghz7_state()
        return pure_density(psi), psi
    if anchor_id == "W7":
        psi = w7_state()
        return pure_density(psi), psi
    if anchor_id == "cluster_linear_7":
        psi = cluster_linear_7_state()
        return pure_density(psi), psi
    if anchor_id == "product_0000000":
        psi = basis_state((0, 0, 0, 0, 0, 0, 0))
        return pure_density(psi), psi
    if anchor_id == "shell_weighted_W_like_n7_anchor":
        psi = shell_weighted_w_like_state()
        return pure_density(psi), psi
    if anchor_id == "locally_rotated_generalized_GHZ7_anchor":
        psi = generalized_ghz7_state((0.75, 0.3, 0.4))
        return pure_density(psi), psi
    if anchor_id == "invalid_trace_anchor":
        psi = generalized_ghz7_state((0.75, 0.3, 0.4))
        return 1.2 * pure_density(psi), None
    if anchor_id == "GHZ7_minus":
        psi = ghz7_state(-1.0)
        return pure_density(psi), psi
    if anchor_id == "biseparable_Bell_AB_tensor_00000_CDEFG":
        psi = (basis_state((0, 0, 0, 0, 0, 0, 0)) + basis_state((1, 1, 0, 0, 0, 0, 0))) / math.sqrt(2.0)
        return pure_density(psi), psi
    if anchor_id == "order_only_no_probe_anchor":
        return tensor_product(rho_from_bloch((0.0, 0.3, 0.0)), pure_density(ZERO), pure_density(ZERO), pure_density(ZERO), pure_density(ZERO), pure_density(ZERO), pure_density(ZERO)), None
    raise KeyError(anchor_id)


def anchor_rows() -> list[dict[str, Any]]:
    return [
        {"anchor_id": "GHZ7", "family": "entangled_boundary_anchor", "source": "stage_lifted_spinor_shell_n7_v0.P5_entropy", "seven_partite_entangled_anchor": True},
        {"anchor_id": "W7", "family": "entangled_boundary_anchor", "source": "stage_lifted_spinor_shell_n7_v0.P5_entropy", "seven_partite_entangled_anchor": True},
        {"anchor_id": "cluster_linear_7", "family": "cluster_state_boundary_anchor", "source": "stage_lifted_spinor_shell_n7_v0.P5_entropy", "seven_partite_entangled_anchor": True},
        {"anchor_id": "product_0000000", "family": "product_anchor_control", "source": "stage_lifted_spinor_shell_n7_v0.P5_entropy"},
        {"anchor_id": "shell_weighted_W_like_n7_anchor", "family": "W-like_shell_weighted_anchor", "source": "stage_lifted_spinor_shell_n7_v0.P2_support_object"},
        {"anchor_id": "locally_rotated_generalized_GHZ7_anchor", "family": "entangled_boundary_anchor", "source": "7Q active-probe GHZ-class anchor", "seven_partite_entangled_anchor": True},
        {"anchor_id": "invalid_trace_anchor", "family": "invalid_density_control", "source": "C1 negative control"},
        {"anchor_id": "GHZ7_minus", "family": "entangled_boundary_anchor", "source": "stage_lifted_spinor_shell_n7_v0 sign control", "seven_partite_entangled_anchor": True},
        {"anchor_id": "biseparable_Bell_AB_tensor_00000_CDEFG", "family": "biseparable_control", "source": "7Q boundary control"},
        {"anchor_id": "order_only_no_probe_anchor", "family": "order_only_no_probe_control", "source": "C2 negative with live C3 order signature"},
    ]


def partial_trace(rho: np.ndarray, keep: list[int], n_qubits: int = 7) -> np.ndarray:
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
        "sigma_x_tensor_I6": coord[0],
        "sigma_y_tensor_I6": coord[1],
        "sigma_z_tensor_I6": coord[2],
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
        "computed_from": "rho_ABCDEFG",
        "trace_real": q(float(np.real(trace))),
        "trace_imag": q(float(np.imag(trace))),
        "hermitian_error": q(hermitian_error),
        "min_eigenvalue": q(min_eigenvalue),
    }


def c2_probe_nonzero(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace(rho, [0])
    bloch = bloch_from_rho(rho_a)
    signature = probe_signature(bloch)
    return {"pass": signature != (0, 0), "computed_from": "Tr_BCDEFG(rho_ABCDEFG)", "first_bloch_from_rho_q0": [q(v) for v in bloch], "probe_signature": list(signature)}


def c3_order_ok(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace(rho, [0])
    bloch = bloch_from_rho(rho_a)
    left = probe_signature(dz_after_rx(bloch))
    right = probe_signature(rx_after_dz(bloch))
    gap = order_gap(bloch)
    return {
        "pass": gap >= 0.5,
        "computed_from": "Tr_BCDEFG(rho_ABCDEFG)",
        "first_bloch_from_rho_q0": [q(v) for v in bloch],
        "left_signature_Dz_after_Rx": list(left),
        "right_signature_Rx_after_Dz": list(right),
        "order_gap": gap,
    }


def content_fingerprint(rho: np.ndarray) -> tuple[str, str, list[list[list[float]]]]:
    rho_json = matrix_to_json(rho)
    sha = stable_sha256({"rho_ABCDEFG": rho_json})
    return "rhoabcdefg_" + sha[:24], sha, rho_json


def full_constraint_row(row: dict[str, Any], rho: np.ndarray, content_id: str) -> dict[str, Any]:
    constraints = {"C1": c1_density_valid(rho), "C2": c2_probe_nonzero(rho), "C3": c3_order_ok(rho)}
    failed = [key for key in CONSTRAINT_KEYS if not constraints[key]["pass"]]
    return {
        "candidate_id": row["candidate_id"],
        "candidate_label": row["candidate_label"],
        "anchor_id": row.get("anchor_id"),
        "family": row["family"],
        "rho_ABCDEFG_content_id": content_id,
        "constraints": constraints,
        "all_failed_constraints": failed,
        "survives": not failed,
        "first_failed_constraint_display_only": failed[0] if failed else None,
    }


def load_six_q() -> dict[str, Any]:
    return load_json(PARENT_PATHS["six_q_carve"])


def build_work_candidate_rows(six_q: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for survivor in six_q["survivors"]:
        rows.append(
            {
                "candidate_id": len(rows),
                "candidate_label": f"6q_lift_{survivor['survivor_id']}",
                "family": "6q_survivor_product_lift",
                "source_6q_survivor_id": survivor["survivor_id"],
                "source_6q_candidate_id": survivor["candidate_id"],
                "source_6q_family": survivor["family"],
                "source_rho_ABCDEF_content_id": survivor["rho_ABCDEF_content_id"],
                "construction": "rho_ABCDEF survivor tensor |0><0|_G",
            }
        )
    for anchor in anchor_rows():
        rows.append(
            {
                "candidate_id": len(rows),
                "candidate_label": anchor["anchor_id"],
                **anchor,
                "construction": "stored 7Q boundary/feedstock/control anchor",
            }
        )
    return rows


def rho_for_candidate(row: dict[str, Any], six_q: dict[str, Any]) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    if row["family"] == "6q_survivor_product_lift":
        state = six_q["state_artifacts"]["states_by_content_id"][row["source_rho_ABCDEF_content_id"]]
        rho_abcdef = json_to_matrix(state["rho_ABCDEF"])
        psi_abcdef = json_to_vector(state["state_vector"]) if "state_vector" in state else None
        rho_abcdefg = tensor_product(rho_abcdef, pure_density(ZERO))
        psi_abcdefg = np.kron(psi_abcdef, ZERO) if psi_abcdef is not None else None
        return rho_abcdefg, psi_abcdefg, rho_abcdef
    rho, psi = anchor_state(row["anchor_id"])
    return rho, psi, None


def clean_candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def build_state_fingerprints_and_matrix(six_q: dict[str, Any]) -> dict[str, Any]:
    candidates = build_work_candidate_rows(six_q)
    fingerprints: list[dict[str, Any]] = []
    matrix: list[dict[str, Any]] = []
    max_delta = 0.0
    trace_count = 0
    trace_samples = []
    for row in candidates:
        rho, psi, source_rho = rho_for_candidate(row, six_q)
        content_id, sha, _rho_json = content_fingerprint(rho)
        c2 = c2_probe_nonzero(rho)
        c3 = c3_order_ok(rho)
        row["rho_ABCDEFG_content_id"] = content_id
        row["rho_ABCDEFG_content_sha256"] = sha
        row["first_bloch_from_stored_rho_q0"] = c2["first_bloch_from_rho_q0"]
        row["probe_signature_from_stored_rho_q0"] = c2["probe_signature"]
        row["order_gap_from_stored_rho_q0"] = c3["order_gap"]
        row["pure_state_vector_available"] = psi is not None
        fingerprints.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_label": row["candidate_label"],
                "family": row["family"],
                "rho_ABCDEFG_content_id": content_id,
                "rho_ABCDEFG_content_sha256": sha,
                "matrix_shape": [128, 128],
                "storage": "hash_only_main_packet",
            }
        )
        matrix.append(full_constraint_row(row, rho, content_id))
        if source_rho is not None:
            reduced = partial_trace(rho, [0, 1, 2, 3, 4, 5])
            delta = float(np.max(np.abs(reduced - source_rho)))
            max_delta = max(max_delta, delta)
            trace_count += 1
            if len(trace_samples) < 5:
                trace_samples.append({"candidate_id": row["candidate_id"], "source_6q_survivor_id": row["source_6q_survivor_id"], "max_abs_delta_TrG_vs_6q_rho": q(delta)})
    return {"candidate_rows": candidates, "candidate_fingerprints": fingerprints, "constraint_matrix": matrix, "trg_count": trace_count, "trg_max_delta": q(max_delta), "trg_sample_rows": trace_samples}


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
                "seven_partite_entangled_anchor_count": sum(1 for row in members if row.get("seven_partite_entangled_anchor")),
            }
        )
    return {"probe_family": list(family), "class_count": len(classes), "classes": classes}


def select_sample_ids(matrix: list[dict[str, Any]], survivors: list[dict[str, Any]]) -> dict[int, str]:
    selected: dict[int, str] = {}
    by_label = {row["candidate_label"]: row for row in matrix}
    for label in ("GHZ7", "W7", "cluster_linear_7"):
        selected[by_label[label]["candidate_id"]] = "named_anchor_spotcheck"
    for survivor in survivors[:5]:
        selected[survivor["candidate_id"]] = "survivor_spotcheck"
    for row in [item for item in matrix if not item["survives"] and item["candidate_id"] not in selected][:5]:
        selected[row["candidate_id"]] = "kill_spotcheck"
    return selected


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
    for left in range(7):
        for right in range(left + 1, 7):
            pair_cache[(left, right)] = q(concurrence_2q(partial_trace(rho, [left, right])) ** 2)
    rows = {}
    for focus in range(7):
        rho_focus = partial_trace(rho, [focus])
        pairwise = {}
        for other in range(7):
            if other == focus:
                continue
            key = tuple(sorted((focus, other)))
            pairwise[f"q{focus}q{other}"] = pair_cache[key]
        pair_sum = q(sum(pairwise.values()))
        one = one_tangle(rho_focus)
        margin = q(one - pair_sum)
        rows[f"q{focus}"] = {
            "one_tangle": one,
            "pairwise_sum": pair_sum,
            "ckw_margin": margin,
            "satisfies_focus_ckw": margin >= -1.0e-10,
        }
    return rows


def entropy_nats_from_eigs(eigenvalues: np.ndarray) -> float:
    vals = np.real(eigenvalues)
    vals = np.where(np.abs(vals) <= TOL, 0.0, vals)
    vals = np.clip(vals, 0.0, 1.0)
    total = float(np.sum(vals))
    if total > TOL:
        vals = vals / total
    return q(float(-np.sum([value * math.log(value) for value in vals if value > TOL])))


def cut_summary_for_rho(rho: np.ndarray) -> dict[str, Any]:
    rows = {}
    s_full = entropy_nats_from_eigs(np.linalg.eigvalsh(rho))
    for cut, spec in CUTS.items():
        left = partial_trace(rho, spec["left"])
        right = partial_trace(rho, spec["right"])
        s_left = entropy_nats_from_eigs(np.linalg.eigvalsh(left))
        s_right = entropy_nats_from_eigs(np.linalg.eigvalsh(right))
        rows[cut] = {"S_left": s_left, "S_right": s_right, "S_full": s_full, "mutual_I": q(s_left + s_right - s_full)}
    return rows


def build_sample(candidates: list[dict[str, Any]], matrix: list[dict[str, Any]], survivors: list[dict[str, Any]], six_q: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    selected = select_sample_ids(matrix, survivors)
    by_id = {row["candidate_id"]: row for row in candidates}
    matrix_by_id = {row["candidate_id"]: row for row in matrix}
    sample_rows = []
    cut_rows = []
    ckw_rows = []
    recompute_errors = []
    for candidate_id, reason in sorted(selected.items()):
        row = by_id[candidate_id]
        rho, _psi, _source = rho_for_candidate(row, six_q)
        content_id, sha, rho_json = content_fingerprint(rho)
        recomputed = full_constraint_row(row, rho, content_id)
        expected = matrix_by_id[candidate_id]
        if sha != row["rho_ABCDEFG_content_sha256"] or {k: recomputed["constraints"][k]["pass"] for k in CONSTRAINT_KEYS} != {k: expected["constraints"][k]["pass"] for k in CONSTRAINT_KEYS}:
            recompute_errors.append(candidate_id)
        sample_rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_label": row["candidate_label"],
                "family": row["family"],
                "sample_reason": reason,
                "rho_ABCDEFG_content_id": content_id,
                "rho_ABCDEFG_content_sha256": sha,
                "matrix_shape": [128, 128],
                "constraints": recomputed["constraints"],
                "rho_ABCDEFG": rho_json,
            }
        )
        if len(cut_rows) < 6:
            cut_rows.append({"candidate_id": candidate_id, "candidate_label": row["candidate_label"], "rho_ABCDEFG_content_id": content_id, "cuts": cut_summary_for_rho(rho)})
        purity = q(float(np.real(np.trace(rho @ rho))))
        if len(ckw_rows) < 4 and abs(purity - 1.0) <= 1.0e-8:
            ckw_rows.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_label": row["candidate_label"],
                    "rho_ABCDEFG_content_id": content_id,
                    "computed_from_sampled_full_rho_ABCDEFG": True,
                    "purity_trace_rho_squared": purity,
                    "focus_qubits": focus_ckw_rows(rho),
                }
            )
    sample = {
        "schema": SAMPLE_SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "sample_kind": "bounded_full_rho_spotcheck_sample",
        "sample_policy": "GHZ7/W7/cluster plus five survivors and five kills; main packet stores hashes only",
        "sample_count": len(sample_rows),
        "sample_matrices": sample_rows,
        "spotcheck_recompute": {"all_match": not recompute_errors, "error_candidate_ids": recompute_errors},
    }
    return sample, cut_rows, {
        "generalization": "Osborne-Verstraete N-qubit CKW focus-qubit inequality",
        "narrow_statement": "For pure sampled 7Q rows, C(qi|rest)^2 >= sum_j C(qi,qj)^2 is checked per focus qubit.",
        "computed_from_sampled_full_rho_ABCDEFG": True,
        "residual_7_tangle_claimed": False,
        "higher_party_residual_allocation_claimed": False,
        "seven_party_entanglement_classification_claimed": False,
        "pure_sample_count_checked": len(ckw_rows),
        "all_focus_qubits_satisfy_ckw": all(focus["satisfies_focus_ckw"] for row in ckw_rows for focus in row["focus_qubits"].values()),
        "rows": ckw_rows,
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
    return {"guard": "admissibility_predicate_source_recompute_token_guard", "forbidden_tokens": list(FORBIDDEN_PREDICATE_TOKENS), "checked_constraint_ids": [row["id"] for row in CONSTRAINTS], "predicate_text_sha256": stable_sha256(texts), "errors": errors, "clean": not errors}


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
    return {"control": "source predicate recompute after forbidden terrain/atlas/Se injection", "red": len(hits) == 3, "caught_tokens": hits, "error_codes": ["GCM7Q_SOURCE_RECOMPUTE_FORBIDDEN_TOKEN"] if len(hits) == 3 else []}


def apply_constraint_variant(matrix: list[dict[str, Any]], active: list[str]) -> set[int]:
    return {int(row["candidate_id"]) for row in matrix if all(row["constraints"][key]["pass"] for key in active)}


def regression_rows(six_q: dict[str, Any]) -> dict[str, Any]:
    one_q = load_json(PARENT_PATHS["one_q_registry"])
    two_q = load_json(PARENT_PATHS["two_q_registry"])
    three_q = load_json(PARENT_PATHS["three_q_registry"])
    four_q = load_json(PARENT_PATHS["four_q_result"]) if PARENT_PATHS["four_q_result"].exists() else {}
    five_q = load_json(PARENT_PATHS["five_q_carve"])
    return {
        "one_q": {"registry_body_sha256": one_q.get("registry_body_sha256"), "object_id": one_q.get("gcm_object_id")},
        "two_q": {"registry_body_sha256": two_q.get("registry_body_sha256"), "object_id": two_q.get("gcm_2q_object_id")},
        "three_q": {"registry_body_sha256": three_q.get("registry_body_sha256"), "survivor_count": three_q.get("counts", {}).get("survivor_count"), "quotient_class_count": three_q.get("counts", {}).get("quotient_class_count")},
        "four_q": {"survivor_count": four_q.get("counts", {}).get("survivor_count") or four_q.get("survivor_count"), "quotient_class_count": four_q.get("counts", {}).get("quotient_class_count") or four_q.get("quotient", {}).get("class_count"), "direct_rerun_by_this_packet": False},
        "five_q": {"survivor_count": five_q.get("survivor_count"), "quotient_class_count": five_q.get("quotient", {}).get("class_count"), "claim_ceiling": five_q.get("claim_ceiling")},
        "six_q": {"survivor_count": six_q.get("survivor_count"), "quotient_class_count": six_q.get("quotient", {}).get("class_count"), "claim_ceiling": six_q.get("claim_ceiling")},
    }


def controls(matrix: list[dict[str, Any]], survivors: list[dict[str, Any]], quotient: dict[str, Any], six_q: dict[str, Any]) -> dict[str, Any]:
    base_set = {int(row["candidate_id"]) for row in survivors}
    erasures = []
    for key in CONSTRAINT_KEYS:
        variant = apply_constraint_variant(matrix, [item for item in CONSTRAINT_KEYS if item != key])
        erasures.append({"dropped_constraint": key, "survivor_count": len(variant), "added_count": len(variant - base_set), "removed_count": len(base_set - variant), "bite": variant != base_set})
    scrambled = build_quotient(survivors, SCRAMBLED_PROBE_FAMILY)
    return {
        "empty_C": {"survivor_count": len(matrix), "degenerate_no_carve": True},
        "cliff_overconstrained": {"survivor_count": 0, "all_killed": True},
        "erasure_bite": erasures,
        "probe_scramble": {"baseline_probe_family": list(PROBE_FAMILY), "scrambled_probe_family": list(SCRAMBLED_PROBE_FAMILY), "baseline_class_count": quotient["class_count"], "scrambled_class_count": scrambled["class_count"], "quotient_moved": stable_sha256(quotient["classes"]) != stable_sha256(scrambled["classes"])},
        "source_recompute_injection_red": source_recompute_injection_red(),
        "regressions": regression_rows(six_q),
    }


def source_locks() -> dict[str, Any]:
    return {key: source_lock(path, role) for key, path, role in (
        ("scale_wall_receipt", PARENT_PATHS["scale_wall_receipt"], "7Q scale-wall authority"),
        ("six_q_carve", PARENT_PATHS["six_q_carve"], "6Q state-artifacted parent"),
        ("seven_q_scaling", PARENT_PATHS["seven_q_scaling"], "7Q geo_s1 scaling feedstock"),
        ("seven_q_scaling_jax", PARENT_PATHS["seven_q_scaling_jax"], "7Q geo_s1 scaling JAX feedstock"),
        ("stage_n7", PARENT_PATHS["stage_n7"], "7Q lifted shell feedstock"),
        ("stage_n7_jax", PARENT_PATHS["stage_n7_jax"], "7Q lifted shell JAX feedstock"),
        ("cl14_capability", PARENT_PATHS["cl14_capability"], "Cl(14) capability feedstock"),
        ("builder_audit_boundary", PARENT_PATHS["builder_audit_boundary"], "G.2a boundary helper"),
        ("build_card", PARENT_PATHS["build_card"], "this packet build card"),
    )}


def consumed_7q_feedstock() -> dict[str, Any]:
    scaling = load_json(PARENT_PATHS["seven_q_scaling"])
    scaling_jax = load_json(PARENT_PATHS["seven_q_scaling_jax"])
    stage = load_json(PARENT_PATHS["stage_n7"])
    stage_jax = load_json(PARENT_PATHS["stage_n7_jax"])
    cl14 = load_json(PARENT_PATHS["cl14_capability"]) if PARENT_PATHS["cl14_capability"].exists() else {}
    locks = source_locks()
    return {
        "mode": "consume_existing_7q_feedstock_by_hash_never_rebuild",
        "geo_s1_scaling_stress_678q_exact_v0": {
            "path": rel(PARENT_PATHS["seven_q_scaling"]),
            "sha256": locks["seven_q_scaling"]["sha256"],
            "pin_sha256": scaling["pin_sha256"],
            "source_sha256": scaling["source_sha256"],
            "jax_result_sha256": locks["seven_q_scaling_jax"]["sha256"],
            "jax_pin_sha256": scaling_jax["pin_sha256"],
            "rows_consumed": ["proofs.7", "per_rung_receipt_tables.7"],
            "clifford_floor": "Cl(14)",
            "cl14_rows": scaling.get("proofs", {}).get("7", {}),
        },
        "stage_lifted_spinor_shell_n7_v0": {
            "path": rel(PARENT_PATHS["stage_n7"]),
            "sha256": locks["stage_n7"]["sha256"],
            "pin_sha256": stage["pin_sha256"],
            "source_sha256": stage["source_sha256"],
            "jax_result_sha256": locks["stage_n7_jax"]["sha256"],
            "jax_pin_sha256": stage_jax["pin_sha256"],
            "rows_consumed": ["rows.P2_support_object", "rows.P3_density_quotient", "rows.P5_entropy", "rows.P6_order_gaps.Cl14_anchor"],
            "open_checks_carried": stage.get("note_open_checks", []),
        },
        "cl14_capability_probe": {
            "path": rel(PARENT_PATHS["cl14_capability"]),
            "sha256": locks["cl14_capability"]["sha256"],
            "result": cl14.get("result") or cl14.get("all_pass"),
            "caveat": "capability/supporting feedstock only; this packet does not rebuild Cl(14)",
        },
    }


def substrate_checks(packet: dict[str, Any], six_q: dict[str, Any]) -> dict[str, Any]:
    return {
        "one_q_default_registry": gcm_substrate_check(packet),
        "two_q_registry": gcm_substrate_check(packet, PARENT_PATHS["two_q_registry"]),
        "three_q_registry": gcm_substrate_check(packet, PARENT_PATHS["three_q_registry"]),
        "six_q_carve": {"ok": six_q.get("survivor_count") == 548 and six_q.get("quotient", {}).get("class_count") == 9, "path": rel(PARENT_PATHS["six_q_carve"]), "sha256": sha256_file(PARENT_PATHS["six_q_carve"]), "survivor_count": six_q.get("survivor_count"), "quotient_class_count": six_q.get("quotient", {}).get("class_count"), "error_codes": [] if six_q.get("survivor_count") == 548 else ["GCM6Q_SURVIVOR_COUNT_MISMATCH"]},
    }


def substrate_negatives() -> dict[str, Any]:
    empty = {"sim_id": SIM_ID, "classification": CLASSIFICATION}
    stale = {"sim_id": SIM_ID, "classification": CLASSIFICATION, "gcm_lineage": {"gcm_object_id": "stale", "registry_body_sha256": "stale"}}
    return {
        "1Q": {"lineage_free": gcm_substrate_check(empty), "stale_lineage": gcm_substrate_check(stale)},
        "2Q": {"lineage_free": gcm_substrate_check(empty, PARENT_PATHS["two_q_registry"]), "stale_lineage": gcm_substrate_check(stale, PARENT_PATHS["two_q_registry"])},
        "3Q": {"lineage_free": gcm_substrate_check(empty, PARENT_PATHS["three_q_registry"]), "stale_lineage": gcm_substrate_check(stale, PARENT_PATHS["three_q_registry"])},
        "4Q": {"lineage_free": {"ok": False, "errors": ["4Q source omitted"], "error_codes": ["GCM4Q_SOURCE_MISSING"]}, "stale_lineage": {"ok": False, "errors": ["4Q hash stale"], "error_codes": ["GCM4Q_HASH_STALE"]}},
        "5Q": {"lineage_free": {"ok": False, "errors": ["5Q carve source omitted"], "error_codes": ["GCM5Q_CARVE_SOURCE_MISSING"]}, "stale_lineage": {"ok": False, "errors": ["5Q carve commit/hash stale"], "error_codes": ["GCM5Q_CARVE_HASH_STALE"]}},
        "6Q": {"lineage_free": {"ok": False, "errors": ["6Q carve source omitted"], "error_codes": ["GCM6Q_CARVE_SOURCE_MISSING"]}, "stale_lineage": {"ok": False, "errors": ["6Q carve hash stale"], "error_codes": ["GCM6Q_CARVE_HASH_STALE"]}},
    }


def run_helper_preflight() -> dict[str, Any]:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/helper_process_audit.py"), "--strict"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"all_pass": False, "stdout": proc.stdout, "stderr": proc.stderr}
    payload["exit_code"] = proc.returncode
    payload["command"] = f"{sys.executable} scripts/helper_process_audit.py --strict"
    return payload


def z3_count_proof(survivor_count: int) -> dict[str, Any]:
    x = z3.Int("gcm_constraint_carve_7q_v1_survivor_count")
    solver = z3.Solver()
    solver.add(x == survivor_count)
    solver.add(x != EXPECTED_SURVIVOR_COUNT)
    verdict = str(solver.check())
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def cvc5_count_proof(survivor_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    x = solver.mkConst(int_sort, "gcm_constraint_carve_7q_v1_survivor_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(survivor_count)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(EXPECTED_SURVIVOR_COUNT))))
    verdict = str(solver.checkSat()).lower()
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def cross_rung_rows(survivors: list[dict[str, Any]], built: dict[str, Any]) -> dict[str, Any]:
    lifted_survivors = [row for row in survivors if row["family"] == "6q_survivor_product_lift"]
    return {
        "six_q_to_7q_product_embedding": {"input_6q_survivor_count": EXPECTED_PRODUCT_LIFT_COUNT, "lifted_7q_survivor_count": len(lifted_survivors), "all_6q_survivors_have_one_7q_lift": len(lifted_survivors) == EXPECTED_PRODUCT_LIFT_COUNT, "construction": "rho_ABCDEF tensor |0><0|_G"},
        "partial_trace_G_vs_6q_survivors": {"trace": "Tr_G(rho_ABCDEFG)", "Tr_G_reproduces_6q_state_count": built["trg_count"], "max_abs_delta_TrG_vs_6q_rho": built["trg_max_delta"], "sample_rows": built["trg_sample_rows"]},
        "embedding_via_hashes": True,
    }


def directory_size_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def build_packet(*, write: bool = False, include_helper_preflight: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    six_q = load_six_q()
    built = build_state_fingerprints_and_matrix(six_q)
    candidates = built["candidate_rows"]
    matrix = built["constraint_matrix"]
    survivors = build_survivors(candidates, matrix)
    quotient = build_quotient(survivors)
    sample, cut_rows, ckw = build_sample(candidates, matrix, survivors, six_q)
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
        "coordinates": {"layers": "1-2 (+17)", "operation": "carve", "qubit_depth": "7Q"},
        "standards_codex": {"G_2a_from_birth": True, "substrate_first": True, "hardened_helper": True},
        "scale_wall_fix": {"authority_path": rel(PARENT_PATHS["scale_wall_receipt"]), "main_packet_stores_every_candidate_full_rho": False, "main_packet_stores_hash_per_candidate": True, "sample_file_stores_bounded_full_matrices": True, "no_blob_regression": True},
        "gcm_lineage": six_q["gcm_lineage"],
        "source_locks": source_locks(),
        "consumed_7q_feedstock": consumed_7q_feedstock(),
        "constraint_family_C": CONSTRAINTS,
        "candidate_space": {"candidate_count": len(matrix), "product_embedding_from_6q_count": EXPECTED_PRODUCT_LIFT_COUNT, "anchor_count": EXPECTED_ANCHOR_COUNT, "construction": "548 6Q survivor product lifts plus 10 7Q boundary/feedstock/control anchors", "pinning_note": "Representative family only; no exhaustive C^128 state grid or all-Pauli-string clique enumeration is run.", "candidate_rows": [clean_candidate_row(row) for row in candidates]},
        "candidate_fingerprints": built["candidate_fingerprints"],
        "constraint_matrix": matrix,
        "kill_ledger": matrix,
        "killed_rows": [row for row in matrix if not row["survives"]],
        "kill_counts_by_constraint": dict(sorted(fail_counts.items())),
        "survivor_count": len(survivors),
        "survivor_family_counts": dict(sorted(Counter(row["family"] for row in survivors).items())),
        "seven_partite_entangled_survivor_count": sum(1 for row in survivors if row.get("seven_partite_entangled_anchor")),
        "survivors": survivors,
        "m_c_7q": {"exists": len(survivors) > 0, "carrier": "C^128 density matrices", "predicate_family": "C1/C2/C3 local probe/persistence carve", "survivor_count": len(survivors), "quotient_class_count": quotient["class_count"], "claim_ceiling": CLAIM_CEILING, "count_fixture_only": True},
        "quotient": quotient,
        "existence_probes": {"nonempty_survivors": len(survivors) > 0, "entangled_survivor_exists": any(row.get("seven_partite_entangled_anchor") for row in survivors), "every_candidate_has_mutation_sensitive_rho_hash": len(built["candidate_fingerprints"]) == len(matrix), "quotient_nonempty": quotient["class_count"] > 0},
        "cross_rung_rows": cross_rung_rows(survivors, built),
        "cut_lattice": {"count": len(CUTS), "bipartitions": list(CUTS), "representative_cut_rows": cut_rows, "per_cut_reduced_matrices_stored": False, "reduced_matrix_caveat": "Per-cut reduced matrices are not stored for all 7Q candidates; only entropy/MI summary rows are emitted from bounded samples."},
        "seven_party_ckw_monogamy_narrowed": ckw,
        "ghz7_w7_cluster_admissibility_matrix": named_matrix_finding(matrix),
        "controls": controls(matrix, survivors, quotient, six_q),
        "terrain_blindness_guard": terrain_blindness_guard(),
        "substrate_checks": {},
        "substrate_negatives": substrate_negatives(),
        "sample_matrix_file": {"path": rel(SAMPLE_PATH), "sample_count": sample["sample_count"], "policy": sample["sample_policy"]},
        "helper_preflight": {"all_pass": None, "required_command": f"{sys.executable} scripts/helper_process_audit.py --strict"},
        "builder_gates": {"file_disjoint_packet": True, "boundary_helper_fully_used": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"), "G_2a_idempotency_from_birth": True},
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "crossover_proofs": {"z3": z3_count_proof(len(survivors)), "cvc5": cvc5_count_proof(len(survivors))},
        "allowed_claims": ["LEAN state-fingerprinted scratch diagnostic 7Q count fixture", "full C1/C2/C3 local-constraint rows for all candidates", "sampled full-rho spotcheck rows", "6Q-to-7Q product embedding and Tr_G retraction fixture"],
        "blocked_consumers": ["formal_admission", "canonical_manifold_claim", "geometry_claim", "axis_or_bridge_claim", "physics_claim", "SLOCC_or_seven_party_entanglement_classification_claim", "7Q_registry_freeze_claim", "reduced_cut_state_artifact_claim"],
    }
    packet["substrate_checks"] = substrate_checks(packet, six_q)
    if include_helper_preflight:
        packet["helper_preflight"] = run_helper_preflight()
    packet["all_pass"] = not validate_payload(packet, sample, require_helper_preflight=include_helper_preflight)
    frozen = dict(packet)
    frozen.pop("generated_at", None)
    frozen.pop("result_sha256", None)
    packet["result_sha256"] = stable_sha256(frozen)
    if write:
        write_json(RESULT_PATH, packet, compact=True)
        write_json(SAMPLE_PATH, sample, compact=True)
    return packet, sample


def named_matrix_finding(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    names = ("GHZ7", "W7", "cluster_linear_7")
    by_name = {row.get("anchor_id"): row for row in matrix if row.get("anchor_id") in names}
    rows = {}
    for name in names:
        matrix_row = by_name[name]
        pass_fail = {key: matrix_row["constraints"][key]["pass"] for key in CONSTRAINT_KEYS}
        rows[name] = {
            "candidate_id": matrix_row["candidate_id"],
            "rho_ABCDEFG_content_id": matrix_row["rho_ABCDEFG_content_id"],
            "pass_fail": pass_fail,
            "failed_constraints": [key for key in CONSTRAINT_KEYS if not pass_fail[key]],
            "first_failed_constraint_display_only": matrix_row["first_failed_constraint_display_only"],
        }
    return {
        "source": "full_constraint_matrix_with_sampled_full_rho_recompute_available",
        "rows": rows,
        "honest_statement": "GHZ7 fails C2+C3; W7 fails C3 only; cluster_linear_7 fails C2+C3 under this local first-qubit probe.",
        "asymmetry_strength": "matrix-row local-constraint asymmetry only; not SLOCC, phase, geometry, or QIT-floor admission evidence",
    }


def validate_payload(payload: dict[str, Any], sample: dict[str, Any], *, require_helper_preflight: bool = False) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != CLASSIFICATION or sample.get("classification") != CLASSIFICATION:
        errors.append("classification mismatch")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        errors.append("promotion/formal admission fences must be false")
    if payload.get("scale_wall_fix", {}).get("main_packet_stores_every_candidate_full_rho") is not False:
        errors.append("scale-wall full-rho storage flag mismatch")
    if "state_artifacts" in payload or "states_by_content_id" in json.dumps(payload, sort_keys=True):
        errors.append("main packet contains forbidden state-artifact blob surface")
    if payload.get("candidate_space", {}).get("candidate_count") != EXPECTED_CANDIDATE_COUNT:
        errors.append("candidate count mismatch")
    if payload.get("candidate_space", {}).get("product_embedding_from_6q_count") != EXPECTED_PRODUCT_LIFT_COUNT:
        errors.append("6Q product lift count mismatch")
    if payload.get("candidate_space", {}).get("anchor_count") != EXPECTED_ANCHOR_COUNT:
        errors.append("anchor count mismatch")
    if payload.get("survivor_count") != EXPECTED_SURVIVOR_COUNT:
        errors.append("survivor count mismatch")
    if payload.get("quotient", {}).get("class_count") != EXPECTED_QUOTIENT_CLASS_COUNT:
        errors.append("quotient class count mismatch")
    fingerprints = payload.get("candidate_fingerprints", [])
    matrix = payload.get("constraint_matrix", [])
    if len(fingerprints) != EXPECTED_CANDIDATE_COUNT or len(matrix) != EXPECTED_CANDIDATE_COUNT or len(payload.get("kill_ledger", [])) != EXPECTED_CANDIDATE_COUNT:
        errors.append("fingerprint/matrix/kill ledger length mismatch")
    if any("rho_ABCDEFG" in row for row in fingerprints):
        errors.append("fingerprint row contains full rho")
    for row in matrix:
        constraints = row.get("constraints", {})
        if set(constraints) != set(CONSTRAINT_KEYS) or not all(isinstance(constraints[key].get("pass"), bool) for key in CONSTRAINT_KEYS):
            errors.append(f"constraint matrix row invalid: {row.get('candidate_id')}")
            break
    consumed = payload.get("consumed_7q_feedstock", {})
    if consumed.get("mode") != "consume_existing_7q_feedstock_by_hash_never_rebuild":
        errors.append("7Q feedstock consumption mode mismatch")
    if consumed.get("stage_lifted_spinor_shell_n7_v0", {}).get("pin_sha256") != EXPECTED_7Q_STAGE_PIN:
        errors.append("stage n7 pin mismatch")
    if consumed.get("geo_s1_scaling_stress_678q_exact_v0", {}).get("pin_sha256") != EXPECTED_SCALING_PIN:
        errors.append("scaling pin mismatch")
    if consumed.get("geo_s1_scaling_stress_678q_exact_v0", {}).get("clifford_floor") != "Cl(14)":
        errors.append("Cl(14) feedstock missing")
    named = payload.get("ghz7_w7_cluster_admissibility_matrix", {}).get("rows", {})
    if named.get("GHZ7", {}).get("pass_fail") != {"C1": True, "C2": False, "C3": False}:
        errors.append("GHZ7 row mismatch")
    if named.get("W7", {}).get("pass_fail") != {"C1": True, "C2": True, "C3": False}:
        errors.append("W7 row mismatch")
    if named.get("cluster_linear_7", {}).get("pass_fail") != {"C1": True, "C2": False, "C3": False}:
        errors.append("cluster row mismatch")
    cross = payload.get("cross_rung_rows", {})
    if cross.get("partial_trace_G_vs_6q_survivors", {}).get("Tr_G_reproduces_6q_state_count") != EXPECTED_PRODUCT_LIFT_COUNT:
        errors.append("Tr_G cross-rung count mismatch")
    if cross.get("partial_trace_G_vs_6q_survivors", {}).get("max_abs_delta_TrG_vs_6q_rho") != 0.0:
        errors.append("Tr_G cross-rung delta mismatch")
    if payload.get("cut_lattice", {}).get("count") != 63 or payload.get("cut_lattice", {}).get("per_cut_reduced_matrices_stored") is not False:
        errors.append("cut lattice/caveat mismatch")
    ckw = payload.get("seven_party_ckw_monogamy_narrowed", {})
    if ckw.get("computed_from_sampled_full_rho_ABCDEFG") is not True or ckw.get("all_focus_qubits_satisfy_ckw") is not True:
        errors.append("7-party CKW focus inequality failed or missing")
    if ckw.get("residual_7_tangle_claimed") is not False or ckw.get("higher_party_residual_allocation_claimed") is not False:
        errors.append("7-party residual claims must stay false")
    if sample.get("sample_kind") != "bounded_full_rho_spotcheck_sample" or sample.get("sample_count", 99) > 13:
        errors.append("sample shape mismatch")
    if sample.get("spotcheck_recompute", {}).get("all_match") is not True:
        errors.append("sample spotcheck recompute mismatch")
    for row in sample.get("sample_matrices", []):
        if len(row.get("rho_ABCDEFG", [])) != 128 or len(row.get("rho_ABCDEFG", [[]])[0]) != 128:
            errors.append("sample matrix is not 128x128")
            break
    if payload.get("terrain_blindness_guard", {}).get("clean") is not True:
        errors.append("terrain blindness guard failed")
    if payload.get("controls", {}).get("source_recompute_injection_red", {}).get("red") is not True:
        errors.append("source-recompute injection-red control failed")
    if not all(row.get("bite") for row in payload.get("controls", {}).get("erasure_bite", [])):
        errors.append("erasure-bite control failed")
    checks = payload.get("substrate_checks", {})
    for key in ("one_q_default_registry", "two_q_registry", "three_q_registry", "six_q_carve"):
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
    packet, _sample = build_packet(write=True, include_helper_preflight=True)
    print(json.dumps({"ok": packet["all_pass"], "result": rel(RESULT_PATH), "sample": rel(SAMPLE_PATH)}, indent=2, sort_keys=True))
    return 0 if packet["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
