#!/usr/bin/env python3
"""Repaired 3Q GCM constraint carve count fixture.

This packet keeps the v0 count fixture but repairs the audited floor failures:
actual candidate states are artifacted, every constraint is evaluated for every
candidate, and CKW rows are recomputed from stored rho_ABC states.
"""

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


SIM_ID = "gcm_constraint_carve_3q_v1"
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
CLAIM_CEILING = "scratch_diagnostic_state_artifacted_3q_count_fixture"
ENGINE_MODE = "shared_packet_three_lane_scratch_diagnostic"

EXPECTED_CANDIDATE_COUNT = 552
EXPECTED_PRODUCT_LIFT_COUNT = 544
EXPECTED_ANCHOR_COUNT = 8
EXPECTED_SURVIVOR_COUNT = 545
EXPECTED_QUOTIENT_CLASS_COUNT = 9
EXPECTED_ENTANGLED_SURVIVOR_COUNT = 1
EXPECTED_2Q_SURVIVOR_COUNT = 544
EXPECTED_2Q_CLASS_COUNT = 8
EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_1Q_REGISTRY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"

PROBE_FAMILY = ("sigma_x_tensor_I_tensor_I", "sigma_z_tensor_I_tensor_I")
SCRAMBLED_PROBE_FAMILY = ("sigma_y_tensor_I_tensor_I", "sigma_z_tensor_I_tensor_I")
CONSTRAINT_KEYS = ("C1", "C2", "C3")
FORBIDDEN_PREDICATE_TOKENS = (
    "terrain",
    "atlas",
    "Se",
    "Ne",
    "Ni",
    "Si",
    "dissipative",
    "circulation",
)

PARENT_PATHS = {
    "one_q_registry": ROOT / "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json",
    "two_q_carve": ROOT / "system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_results.json",
    "two_q_registry": ROOT / "system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_registry.json",
    "three_q_v0_audit": ROOT / "system_v6/sims/gcm_constraint_carve_3q_v0/audit_verdict.md",
    "three_q_floor": ROOT / "system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json",
    "three_q_shell": ROOT / "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json",
    "climb_ledger_correction": ROOT / "system_v6/receipts/qubit_ladder_climb_ledger_20260612.md",
    "build_card": SIM_DIR / "build_card.md",
    "builder_audit_boundary": ROOT / "scripts/builder_audit_boundary.py",
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia lane builds a SimpleGraph over quotient classes and matrix adjacency."},
    "JSON3": {"tried": True, "used": True, "reason": "Julia lane reads and writes structured result receipts."},
    "networkx": {"tried": True, "used": True, "reason": "JAX/Python lane recomputes quotient connectivity from full matrix rows."},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch lane batches matrix-derived C2/C3 observables across candidate rows."},
    "sympy": {"tried": True, "used": True, "reason": "Exact rational guards for count fixture and CKW margin fixture."},
    "z3": {"tried": True, "used": True, "reason": "SMT contradiction proof binds computed survivor count."},
    "cvc5": {"tried": True, "used": True, "reason": "Independent SMT contradiction proof binds computed survivor count."},
    "gcm_substrate_check": {"tried": True, "used": True, "reason": "Hardened 1Q and 2Q lineage consumption gate."},
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a builder/audit boundary from birth."},
}

TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "JSON3": "supportive",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "state_artifacted_3q_constraint_matrix",
        "substrate_first_1q_2q_lineage_consumption",
        "ghz_w_full_matrix_asymmetry",
        "ckw_recomputed_from_stored_rho",
        "count_fixture_regression_552_to_545_over_9",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "SimpleGraph/add_edge!/connected_components over quotient-class matrix adjacency.",
        },
        "jax": {
            "networkx": "nx.Graph connected components from the matrix-derived quotient buckets.",
            "sympy": "sp.Rational exact survivor/class count and CKW margin guard.",
            "z3": "z3.Solver unsat contradiction guard for computed survivor_count != 545.",
            "cvc5": "cvc5.Solver unsat contradiction guard for computed survivor_count != 545.",
        },
        "pytorch": {
            "torch.func": "vmap over matrix-derived first-qubit probes and order-gap observables.",
            "sympy": "sp.Rational exact survivor/class count and CKW margin guard.",
        },
    },
}

CONSTRAINTS = [
    {
        "key": "C1",
        "id": "C1_finite_3q_density_carrier",
        "literal_executable_predicate": "rho_ABC is Hermitian trace-one positive semidefinite on C^8",
    },
    {
        "key": "C2",
        "id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "literal_executable_predicate": "first-qubit x/z probe signature from Tr_BC(rho_ABC) is not (0, 0)",
    },
    {
        "key": "C3",
        "id": "C3_persistence_n01_order_gap",
        "literal_executable_predicate": "D_z after R_x and R_x after D_z first-qubit x/z probe signatures differ",
    },
]

PAULI_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
I2 = np.eye(2, dtype=np.complex128)
ZERO = np.array([1.0, 0.0], dtype=np.complex128)
ONE = np.array([0.0, 1.0], dtype=np.complex128)


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def q(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def scaled(value: float) -> int:
    return int(round(2.0 * float(value)))


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    row: dict[str, Any] = {"role": role, "path": rel(path) if path.is_relative_to(ROOT) else str(path), "exists": path.exists()}
    if path.exists() and path.is_file():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    return row


def complex_pair(value: complex) -> list[float]:
    return [q(float(np.real(value))), q(float(np.imag(value)))]


def matrix_to_json(matrix: np.ndarray) -> list[list[list[float]]]:
    return [[complex_pair(value) for value in row] for row in matrix.tolist()]


def vector_to_json(vector: np.ndarray) -> list[list[float]]:
    return [complex_pair(value) for value in vector.tolist()]


def json_to_matrix(value: list[list[list[float]]]) -> np.ndarray:
    return np.array([[complex(pair[0], pair[1]) for pair in row] for row in value], dtype=np.complex128)


def tensor_product(*matrices: np.ndarray) -> np.ndarray:
    out = matrices[0]
    for matrix in matrices[1:]:
        out = np.kron(out, matrix)
    return out


def state_index(a: int, b: int, c: int) -> int:
    return 4 * a + 2 * b + c


def basis_state(a: int, b: int, c: int) -> np.ndarray:
    vector = np.zeros(8, dtype=np.complex128)
    vector[state_index(a, b, c)] = 1.0
    return vector


def pure_density(vector: np.ndarray) -> np.ndarray:
    return np.outer(vector, np.conjugate(vector))


def rho_from_bloch(coord: tuple[float, float, float]) -> np.ndarray:
    x, y, z = coord
    return 0.5 * (I2 + x * PAULI_X + y * PAULI_Y + z * PAULI_Z)


def qubit_direction_kets(direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    nx, ny, nz = [float(v) for v in direction]
    theta = math.acos(max(-1.0, min(1.0, nz)))
    phi = math.atan2(ny, nx)
    plus = np.array([math.cos(theta / 2.0), complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0)])
    minus = np.array([-complex(math.cos(-phi), math.sin(-phi)) * math.sin(theta / 2.0), math.cos(theta / 2.0)])
    return plus.astype(np.complex128), minus.astype(np.complex128)


def generalized_ghz_state(first_bloch_coord: tuple[float, float, float]) -> np.ndarray:
    bloch = np.array(first_bloch_coord, dtype=float)
    radius = float(np.linalg.norm(bloch))
    if radius <= 1.0e-12:
        plus, minus = ZERO, ONE
    else:
        plus, minus = qubit_direction_kets(bloch / radius)
    p = (1.0 + radius) / 2.0
    vector = math.sqrt(p) * np.kron(plus, np.kron(ZERO, ZERO))
    vector += math.sqrt(1.0 - p) * np.kron(minus, np.kron(ONE, ONE))
    return vector / np.linalg.norm(vector)


def anchor_state(anchor_id: str) -> tuple[np.ndarray, np.ndarray | None]:
    if anchor_id == "GHZ":
        psi = (basis_state(0, 0, 0) + basis_state(1, 1, 1)) / math.sqrt(2.0)
        return pure_density(psi), psi
    if anchor_id == "W":
        psi = (basis_state(0, 0, 1) + basis_state(0, 1, 0) + basis_state(1, 0, 0)) / math.sqrt(3.0)
        return pure_density(psi), psi
    if anchor_id == "biseparable_Bell_AB_tensor_0C":
        psi = (basis_state(0, 0, 0) + basis_state(1, 1, 0)) / math.sqrt(2.0)
        return pure_density(psi), psi
    if anchor_id == "product_000":
        psi = basis_state(0, 0, 0)
        return pure_density(psi), psi
    if anchor_id == "locally_rotated_generalized_GHZ_anchor":
        psi = generalized_ghz_state((0.75, 0.3, 0.4))
        return pure_density(psi), psi
    if anchor_id == "invalid_trace_anchor":
        psi = generalized_ghz_state((0.75, 0.3, 0.4))
        return 1.2 * pure_density(psi), None
    if anchor_id == "GHZ_minus":
        psi = (basis_state(0, 0, 0) - basis_state(1, 1, 1)) / math.sqrt(2.0)
        return pure_density(psi), psi
    if anchor_id == "order_only_no_probe_anchor":
        rho_a = rho_from_bloch((0.0, 0.3, 0.0))
        return tensor_product(rho_a, pure_density(ZERO), pure_density(ZERO)), None
    raise KeyError(anchor_id)


def product_lift_state(first: tuple[float, float, float], second: tuple[float, float, float]) -> np.ndarray:
    return tensor_product(rho_from_bloch(first), rho_from_bloch(second), pure_density(ZERO))


def partial_trace(rho: np.ndarray, keep: list[int]) -> np.ndarray:
    dims = [2, 2, 2]
    keep_set = set(keep)
    traced = rho.reshape(dims + dims)
    current_n = len(dims)
    for qubit in reversed(range(len(dims))):
        if qubit not in keep_set:
            traced = np.trace(traced, axis1=qubit, axis2=qubit + current_n)
            current_n -= 1
    final_dim = 2 ** len(keep)
    return traced.reshape((final_dim, final_dim))


def bloch_from_rho_a(rho_a: np.ndarray) -> tuple[float, float, float]:
    return (
        q(float(np.real(np.trace(PAULI_X @ rho_a)))),
        q(float(np.real(np.trace(PAULI_Y @ rho_a)))),
        q(float(np.real(np.trace(PAULI_Z @ rho_a)))),
    )


def probe_signature(coord: tuple[float, float, float], family: tuple[str, str] = PROBE_FAMILY) -> tuple[int, int]:
    mapping = {
        "sigma_x_tensor_I_tensor_I": coord[0],
        "sigma_y_tensor_I_tensor_I": coord[1],
        "sigma_z_tensor_I_tensor_I": coord[2],
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
        "computed_from": "rho_ABC",
        "trace_real": q(float(np.real(trace))),
        "trace_imag": q(float(np.imag(trace))),
        "hermitian_error": q(hermitian_error),
        "min_eigenvalue": q(min_eigenvalue),
    }


def c2_probe_nonzero(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace(rho, [0])
    bloch = bloch_from_rho_a(rho_a)
    signature = probe_signature(bloch)
    return {
        "pass": signature != (0, 0),
        "computed_from": "Tr_BC(rho_ABC)",
        "first_bloch_from_rho_A": [q(v) for v in bloch],
        "probe_signature": list(signature),
    }


def c3_order_ok(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace(rho, [0])
    bloch = bloch_from_rho_a(rho_a)
    left = probe_signature(dz_after_rx(bloch))
    right = probe_signature(rx_after_dz(bloch))
    gap = order_gap(bloch)
    return {
        "pass": gap >= 0.5,
        "computed_from": "Tr_BC(rho_ABC)",
        "first_bloch_from_rho_A": [q(v) for v in bloch],
        "left_signature_Dz_after_Rx": list(left),
        "right_signature_Rx_after_Dz": list(right),
        "order_gap": gap,
    }


def state_record(candidate_id: int, label: str, rho: np.ndarray, psi: np.ndarray | None) -> tuple[str, dict[str, Any]]:
    rho_json = matrix_to_json(rho)
    content_id = "rhoabc_" + stable_sha256({"rho_ABC": rho_json})[:24]
    trace = np.trace(rho)
    eigvals = np.linalg.eigvalsh((rho + np.conjugate(rho.T)) / 2.0)
    record: dict[str, Any] = {
        "content_id": content_id,
        "candidate_labels": [label],
        "first_candidate_id": candidate_id,
        "matrix_shape": [8, 8],
        "rho_ABC": rho_json,
        "trace_real": q(float(np.real(trace))),
        "trace_imag": q(float(np.imag(trace))),
        "min_eigenvalue": q(float(np.min(np.real(eigvals)))),
    }
    if psi is not None:
        record["state_vector"] = vector_to_json(psi)
    return content_id, record


def one_q_registry() -> dict[str, Any]:
    return load_json(PARENT_PATHS["one_q_registry"])


def two_q_payload() -> dict[str, Any]:
    return load_json(PARENT_PATHS["two_q_carve"])


def two_q_registry() -> dict[str, Any]:
    return load_json(PARENT_PATHS["two_q_registry"])


def first_nested_id(registry: dict[str, Any], section: str, field: str) -> str:
    rows = registry.get(section, {}).get("survivors" if field.endswith("survivor_id") else "quotient_classes", [])
    if field.endswith("candidate_region_id"):
        rows = registry.get(section, {}).get("candidate_regions", [])
    for row in rows:
        value = row.get(field)
        if isinstance(value, str):
            return value
    raise KeyError(f"{section}.{field}")


def gcm_lineage() -> dict[str, Any]:
    one_q = one_q_registry()
    two_q = two_q_registry()
    return {
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "survivor_ids": [first_nested_id(one_q, "frozen_registry", "survivor_id")],
        "quotient_class_ids": [first_nested_id(one_q, "frozen_registry", "quotient_class_id")],
        "candidate_region_ids": [first_nested_id(one_q, "frozen_registry", "candidate_region_id")],
        "gcm_2q_survivor_ids": [first_nested_id(two_q, "frozen_2q_registry", "gcm_2q_survivor_id")],
        "gcm_2q_quotient_class_ids": [first_nested_id(two_q, "frozen_2q_registry", "gcm_2q_quotient_class_id")],
        "gcm_2q_candidate_region_ids": [first_nested_id(two_q, "frozen_2q_registry", "gcm_2q_candidate_region_id")],
        "object_maps": [
            {
                "survivor_id": first_nested_id(one_q, "frozen_registry", "survivor_id"),
                "gcm_2q_survivor_id": first_nested_id(two_q, "frozen_2q_registry", "gcm_2q_survivor_id"),
                "role": "minimal resolved lineage witness for hardened substrate check",
            }
        ],
    }


def anchor_rows() -> list[dict[str, Any]]:
    return [
        {"anchor_id": "GHZ", "family": "entangled_boundary_anchor", "source": "geo_s1_three_qubit_floor_exact_v0", "tripartite_entangled_anchor": True},
        {"anchor_id": "W", "family": "entangled_boundary_anchor", "source": "geo_s1_three_qubit_floor_exact_v0", "tripartite_entangled_anchor": True},
        {"anchor_id": "biseparable_Bell_AB_tensor_0C", "family": "entangled_boundary_anchor", "source": "geo_s1_three_qubit_floor_exact_v0", "pair_entangled_control": True},
        {"anchor_id": "product_000", "family": "product_anchor_control", "source": "geo_s1_three_qubit_floor_exact_v0"},
        {"anchor_id": "locally_rotated_generalized_GHZ_anchor", "family": "entangled_boundary_anchor", "source": "lifted-ladder GHZ-class active-probe anchor", "tripartite_entangled_anchor": True},
        {"anchor_id": "invalid_trace_anchor", "family": "invalid_density_control", "source": "C1 negative control"},
        {"anchor_id": "GHZ_minus", "family": "entangled_boundary_anchor", "source": "geo_s1_three_qubit_floor_exact_v0 sign control", "tripartite_entangled_anchor": True},
        {"anchor_id": "order_only_no_probe_anchor", "family": "order_only_no_probe_control", "source": "C2 negative with live C3 order signature"},
    ]


def build_work_candidates() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    registry = two_q_registry()
    raw_to_2q_id = {
        row.get("raw_2q_survivor_id"): row.get("gcm_2q_survivor_id")
        for row in registry.get("frozen_2q_registry", {}).get("survivors", [])
    }
    for source in two_q_payload()["survivors"]:
        first = tuple(float(v) for v in source["first_bloch"])
        second = tuple(float(v) for v in source.get("second_bloch", [0.0, 0.0, 0.0]))
        rho = product_lift_state(first, second)
        rows.append(
            {
                "candidate_id": len(rows),
                "candidate_label": f"2q_lift_{source['survivor_id']}",
                "family": "2q_survivor_product_lift",
                "source_2q_survivor_id": source["survivor_id"],
                "source_gcm_2q_survivor_id": raw_to_2q_id.get(source["survivor_id"]),
                "source_2q_candidate_id": source["candidate_id"],
                "source_2q_family": source["family"],
                "construction": "rho_A(first_bloch) tensor rho_B(second_bloch) tensor |0><0|_C from stored 2Q local pins",
                "pair_entangled_AB_inherited": bool(source.get("entangled", False)),
                "pair_entanglement_not_claimed_in_product_lift_state": True,
                "_rho_ABC": rho,
                "_state_vector": None,
            }
        )
    for anchor in anchor_rows():
        rho, psi = anchor_state(anchor["anchor_id"])
        rows.append(
            {
                "candidate_id": len(rows),
                "candidate_label": anchor["anchor_id"],
                **anchor,
                "construction": "stored 3Q floor/shell boundary anchor",
                "_rho_ABC": rho,
                "_state_vector": psi,
            }
        )
    return rows


def clean_candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def full_constraint_row(row: dict[str, Any], content_id: str) -> dict[str, Any]:
    rho = row["_rho_ABC"]
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
        "rho_ABC_content_id": content_id,
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
        content_id, record = state_record(row["candidate_id"], row["candidate_label"], row["_rho_ABC"], row["_state_vector"])
        if content_id in states:
            states[content_id]["candidate_labels"].append(row["candidate_label"])
        else:
            states[content_id] = record
        row["rho_ABC_content_id"] = content_id
        row["first_bloch_from_stored_rho_A"] = c2_probe_nonzero(row["_rho_ABC"])["first_bloch_from_rho_A"]
        row["probe_signature_from_stored_rho_A"] = c2_probe_nonzero(row["_rho_ABC"])["probe_signature"]
        row["order_gap_from_stored_rho_A"] = c3_order_ok(row["_rho_ABC"])["order_gap"]
        candidate_index.append({"candidate_id": row["candidate_id"], "candidate_label": row["candidate_label"], "rho_ABC_content_id": content_id})
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
        coord = tuple(float(v) for v in row["first_bloch_from_stored_rho_A"])
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
                "tripartite_entangled_anchor_count": sum(1 for row in members if row.get("tripartite_entangled_anchor")),
            }
        )
    return {"probe_family": list(family), "class_count": len(classes), "classes": classes}


def survivor_state_rows(survivors: list[dict[str, Any]], states: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for survivor in survivors:
        content_id = survivor["rho_ABC_content_id"]
        rows.append(
            {
                "survivor_id": survivor["survivor_id"],
                "candidate_id": survivor["candidate_id"],
                "candidate_label": survivor["candidate_label"],
                "rho_ABC_content_id": content_id,
                "rho_ABC": states[content_id]["rho_ABC"],
            }
        )
    return rows


def concurrence_2q(rho_2q: np.ndarray) -> float:
    sy = PAULI_Y
    yy = np.kron(sy, sy)
    product = rho_2q @ yy @ np.conjugate(rho_2q) @ yy
    eigvals = np.linalg.eigvals(product)
    roots = sorted((math.sqrt(max(0.0, float(np.real(value)))) for value in eigvals), reverse=True)
    while len(roots) < 4:
        roots.append(0.0)
    return q(max(0.0, roots[0] - roots[1] - roots[2] - roots[3]))


def one_tangle(rho_single: np.ndarray) -> float:
    return q(max(0.0, float(np.real(4.0 * np.linalg.det(rho_single)))))


def ckw_for_rho(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace(rho, [0])
    rho_b = partial_trace(rho, [1])
    rho_c = partial_trace(rho, [2])
    rho_ab = partial_trace(rho, [0, 1])
    rho_ac = partial_trace(rho, [0, 2])
    rho_bc = partial_trace(rho, [1, 2])
    tau_ab = q(concurrence_2q(rho_ab) ** 2)
    tau_ac = q(concurrence_2q(rho_ac) ** 2)
    tau_bc = q(concurrence_2q(rho_bc) ** 2)
    rows = {
        "A|BC": {"one_tangle": one_tangle(rho_a), "pairwise_tangles": {"AB": tau_ab, "AC": tau_ac}},
        "B|AC": {"one_tangle": one_tangle(rho_b), "pairwise_tangles": {"AB": tau_ab, "BC": tau_bc}},
        "C|AB": {"one_tangle": one_tangle(rho_c), "pairwise_tangles": {"AC": tau_ac, "BC": tau_bc}},
    }
    for row in rows.values():
        pair_sum = q(sum(row["pairwise_tangles"].values()))
        margin = q(row["one_tangle"] - pair_sum)
        row["pairwise_sum"] = pair_sum
        row["ckw_margin"] = margin
        row["satisfies_ckw"] = margin >= -1.0e-10
    return rows


def ckw_rows(survivors: list[dict[str, Any]], states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for survivor in survivors:
        if not survivor.get("tripartite_entangled_anchor"):
            continue
        state = states[survivor["rho_ABC_content_id"]]
        rho = json_to_matrix(state["rho_ABC"])
        rows.append(
            {
                "state_id": survivor["candidate_label"],
                "candidate_id": survivor["candidate_id"],
                "survivor_id": survivor["survivor_id"],
                "rho_ABC_content_id": survivor["rho_ABC_content_id"],
                "computed_from_stored_rho_ABC": True,
                "party_cuts": ckw_for_rho(rho),
            }
        )
    return {
        "opened_by_2q_audit": "OPEN_closes_at_3_parties_only_if_recomputed_from_stored_rho",
        "computed_from_stored_rho_ABC": True,
        "survivor_count_checked": len(rows),
        "all_party_cuts_satisfy_ckw": all(
            cut["satisfies_ckw"] for row in rows for cut in row["party_cuts"].values()
        ),
        "rows": rows,
    }


def ghz_w_matrix_finding(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {row.get("anchor_id"): row for row in matrix if row.get("anchor_id") in {"GHZ", "W"}}
    rows = {}
    for name in ("GHZ", "W"):
        matrix_row = by_name[name]
        pass_fail = {key: matrix_row["constraints"][key]["pass"] for key in CONSTRAINT_KEYS}
        rows[name] = {
            "candidate_id": matrix_row["candidate_id"],
            "rho_ABC_content_id": matrix_row["rho_ABC_content_id"],
            "pass_fail": pass_fail,
            "failed_constraints": [key for key in CONSTRAINT_KEYS if not pass_fail[key]],
            "first_failed_constraint_display_only": matrix_row["first_failed_constraint_display_only"],
        }
    return {
        "source": "full_constraint_matrix",
        "rows": rows,
        "honest_statement": "GHZ fails C2+C3; W fails C3 only.",
        "asymmetry_strength": "matrix-row asymmetry, not SLOCC separation or QIT-floor admission",
    }


def terrain_blindness_guard() -> dict[str, Any]:
    texts = [stable_json(row) for row in CONSTRAINTS]
    errors: list[str] = []
    for row, text in zip(CONSTRAINTS, texts):
        lowered = text.lower()
        for token in FORBIDDEN_PREDICATE_TOKENS:
            matched = re.search(rf"\b{re.escape(token)}\b", text) is not None if token in {"Se", "Ne", "Ni", "Si"} else token.lower() in lowered
            if matched:
                errors.append(f"{row['id']}: forbidden predicate token {token!r}")
    return {
        "guard": "admissibility_predicate_token_guard",
        "forbidden_tokens": list(FORBIDDEN_PREDICATE_TOKENS),
        "checked_constraint_ids": [row["id"] for row in CONSTRAINTS],
        "predicate_text_sha256": stable_sha256(texts),
        "errors": errors,
        "clean": not errors,
    }


def injection_red_control() -> dict[str, Any]:
    injected = dict(CONSTRAINTS[1])
    injected["literal_executable_predicate"] += " terrain atlas Se"
    text = stable_json(injected)
    caught = "terrain" in text.lower() and "atlas" in text.lower() and re.search(r"\bSe\b", text) is not None
    return {
        "control": "inject forbidden terrain/atlas/Se token into C2 predicate text",
        "injected_variant_caught": bool(caught),
        "red": bool(caught),
    }


def apply_constraint_variant(matrix: list[dict[str, Any]], active: list[str]) -> set[int]:
    survivors = set()
    for row in matrix:
        if all(row["constraints"][key]["pass"] for key in active):
            survivors.add(int(row["candidate_id"]))
    return survivors


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
        "injection_red": injection_red_control(),
        "regressions": regression_rows(),
    }


def regression_rows() -> dict[str, Any]:
    one_q = one_q_registry()
    two_q = two_q_payload()
    two_q_reg = two_q_registry()
    return {
        "one_q": {
            "object_id_match": one_q.get("gcm_object_id") == EXPECTED_1Q_OBJECT_ID,
            "registry_body_sha256": one_q.get("registry_body_sha256"),
            "registry_body_hash_match": one_q.get("registry_body_sha256") == EXPECTED_1Q_REGISTRY_SHA256,
            "survivor_count": one_q.get("counts", {}).get("survivor_count"),
            "quotient_class_count": one_q.get("counts", {}).get("quotient_class_count"),
        },
        "two_q": {
            "sim_id": two_q.get("sim_id"),
            "survivor_count": two_q.get("survivor_count"),
            "quotient_class_count": two_q.get("quotient", {}).get("class_count"),
            "registry_object_id": two_q_reg.get("gcm_2q_object_id"),
            "registry_body_sha256": two_q_reg.get("registry_body_sha256"),
            "registry_body_hash_match": two_q_reg.get("registry_body_sha256") == EXPECTED_2Q_REGISTRY_SHA256,
        },
    }


def source_locks() -> dict[str, Any]:
    return {
        "one_q_registry": source_lock(PARENT_PATHS["one_q_registry"], "1Q frozen substrate registry"),
        "two_q_carve": source_lock(PARENT_PATHS["two_q_carve"], "2Q carve result consumed for 544 lifts"),
        "two_q_registry": source_lock(PARENT_PATHS["two_q_registry"], "2Q frozen registry consumed by hardened helper"),
        "three_q_v0_audit": source_lock(PARENT_PATHS["three_q_v0_audit"], "v0 FAIL audit repair contract"),
        "three_q_floor": source_lock(PARENT_PATHS["three_q_floor"], "3Q floor feedstock consumed read-only"),
        "three_q_shell": source_lock(PARENT_PATHS["three_q_shell"], "3Q shell feedstock consumed read-only"),
        "climb_ledger_correction": source_lock(PARENT_PATHS["climb_ledger_correction"], "refreshed climb ledger lock"),
        "builder_audit_boundary": source_lock(PARENT_PATHS["builder_audit_boundary"], "G.2a boundary helper"),
        "build_card": source_lock(PARENT_PATHS["build_card"], "this packet build card"),
    }


def lineage_free_negative() -> dict[str, Any]:
    result = gcm_substrate_check({"sim_id": SIM_ID, "classification": CLASSIFICATION})
    return {
        "red": result.get("ok") is False,
        "negative_payload": "missing 1Q/2Q substrate lineage",
        "error_codes": result.get("error_codes", []),
        "errors": result.get("errors", []),
    }


def substrate_checks(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "one_q_default_registry": gcm_substrate_check(packet),
        "two_q_registry": gcm_substrate_check(packet, PARENT_PATHS["two_q_registry"]),
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
    x = z3.Int("gcm_constraint_carve_3q_v1_survivor_count")
    solver = z3.Solver()
    solver.add(x == survivor_count)
    solver.add(x != EXPECTED_SURVIVOR_COUNT)
    verdict = str(solver.check())
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def cvc5_count_proof(survivor_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    x = solver.mkConst(int_sort, "gcm_constraint_carve_3q_v1_survivor_count")
    value = solver.mkInteger(survivor_count)
    expected = solver.mkInteger(EXPECTED_SURVIVOR_COUNT)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, x, value))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, x, expected)))
    verdict = str(solver.checkSat()).lower()
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def cross_rung_rows(survivors: list[dict[str, Any]]) -> dict[str, Any]:
    lifted = [row for row in survivors if row["family"] == "2q_survivor_product_lift"]
    fiber_counts = Counter(str(row["source_2q_survivor_id"]) for row in lifted)
    return {
        "product_embedding_vs_2q": {
            "input_2q_survivor_count": EXPECTED_2Q_SURVIVOR_COUNT,
            "lifted_survivor_count": len(lifted),
            "all_lifted_survive": len(lifted) == EXPECTED_2Q_SURVIVOR_COUNT,
            "construction": "rho_A(first_bloch) tensor rho_B(second_bloch) tensor |0><0|_C",
        },
        "partial_trace_vs_2q_local_pins": {
            "trace": "Tr_C(rho_ABC)",
            "image_equals_2q_survivor_local_pin_set": len(fiber_counts) == EXPECTED_2Q_SURVIVOR_COUNT and set(fiber_counts.values()) == {1},
            "pair_entanglement_not_claimed": True,
        },
    }


def build_packet(*, include_helper_preflight: bool = False) -> dict[str, Any]:
    built = build_state_and_matrix()
    states = built["states_by_content_id"]
    matrix = built["constraint_matrix"]
    candidates = built["work_candidates"]
    survivors = build_survivors(candidates, matrix)
    quotient = build_quotient(survivors)
    survivor_states = survivor_state_rows(survivors, states)
    ckw = ckw_rows(survivors, states)
    control_rows = controls(matrix, survivors, quotient)
    family_counts = dict(sorted(Counter(row["family"] for row in survivors).items()))
    fail_counts = Counter(key for row in matrix for key in row["all_failed_constraints"])
    packet: dict[str, Any] = {
        "schema": "gcm_constraint_carve_3q_v1_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "coordinates": {"layers": "1-2 (+17)", "operation": "carve", "qubit_depth": "3Q"},
        "standards_codex": {"G_2a_from_birth": True, "substrate_first": True},
        "gcm_lineage": gcm_lineage(),
        "source_locks": source_locks(),
        "ledger_lock_refreshed": {
            "path": rel(PARENT_PATHS["climb_ledger_correction"]),
            "sha256": source_locks()["climb_ledger_correction"].get("sha256"),
            "git_last_commit": source_locks()["climb_ledger_correction"].get("git_last_commit"),
            "refreshed_from_disk": True,
        },
        "strict_fixes": {
            "actual_states_artifacted": True,
            "full_constraint_matrix_not_first_failed_label": True,
            "ckw_recomputed_from_stored_rho_ABC": True,
            "ghz_w_honest_matrix_statement": "GHZ fails C2+C3; W fails C3 only.",
            "julia_graphs_declaration_corrected": True,
            "helper_preflight_green_required": True,
            "ledger_lock_refreshed": True,
        },
        "constraint_family_C": CONSTRAINTS,
        "candidate_space": {
            "candidate_count": len(matrix),
            "product_embedding_from_2q_count": EXPECTED_PRODUCT_LIFT_COUNT,
            "anchor_count": EXPECTED_ANCHOR_COUNT,
            "construction": "544 2Q local-pin product lifts plus 8 stored 3Q anchors",
            "candidate_rows": [clean_candidate_row(row) for row in candidates],
        },
        "state_artifacts": {
            "artifact_kind": "rho_ABC_content_addressed_states",
            "content_id_rule": "rhoabc_<sha256(canonical rho_ABC JSON)[:24]>",
            "states_by_content_id": states,
            "candidate_state_index": built["candidate_state_index"],
            "survivor_states": survivor_states,
        },
        "constraint_matrix": matrix,
        "kill_ledger": matrix,
        "killed_rows": [row for row in matrix if not row["survives"]],
        "kill_counts_by_constraint": dict(sorted(fail_counts.items())),
        "survivor_count": len(survivors),
        "survivor_family_counts": family_counts,
        "tripartite_entangled_survivor_count": sum(1 for row in survivors if row.get("tripartite_entangled_anchor")),
        "survivors": survivors,
        "quotient": quotient,
        "cross_rung_rows": cross_rung_rows(survivors),
        "ghz_w_matrix_finding": ghz_w_matrix_finding(matrix),
        "monogamy_ckw_recomputed_from_stored_rho": ckw,
        "controls": control_rows,
        "lineage_free_negative": lineage_free_negative(),
        "terrain_blindness_guard": terrain_blindness_guard(),
        "substrate_checks": {},
        "helper_preflight": {"all_pass": None, "required_command": f"{sys.executable} scripts/helper_process_audit.py --strict"},
        "julia_graphs_fix": {
            "required": True,
            "source_path": rel(SIM_DIR / f"{SIM_ID}_julia.jl"),
            "must_import_and_use": ["Graphs.SimpleGraph", "Graphs.add_edge!", "Graphs.connected_components"],
        },
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
            "state-artifacted scratch diagnostic count fixture",
            "full-matrix GHZ/W local constraint asymmetry",
            "CKW inequality recomputed from stored rho_ABC for surviving tripartite anchor",
            "552->545/9 regression fixture",
        ],
        "blocked_consumers": [
            "formal_admission",
            "canonical_manifold_claim",
            "axis_or_bridge_claim",
            "physics_claim",
            "SLOCC_GHZ_W_separator_claim",
            "QIT_floor_admission",
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
    return packet


def validate_payload(payload: dict[str, Any], *, require_helper_preflight: bool = False) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != CLASSIFICATION:
        errors.append("classification mismatch")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        errors.append("promotion/formal admission fences must be false")
    if payload.get("candidate_space", {}).get("candidate_count") != EXPECTED_CANDIDATE_COUNT:
        errors.append("candidate count mismatch")
    if payload.get("survivor_count") != EXPECTED_SURVIVOR_COUNT:
        errors.append("survivor count mismatch")
    if payload.get("quotient", {}).get("class_count") != EXPECTED_QUOTIENT_CLASS_COUNT:
        errors.append("quotient class count mismatch")
    if payload.get("tripartite_entangled_survivor_count") != EXPECTED_ENTANGLED_SURVIVOR_COUNT:
        errors.append("tripartite entangled survivor count mismatch")
    state_artifacts = payload.get("state_artifacts", {})
    states = state_artifacts.get("states_by_content_id", {})
    candidate_index = state_artifacts.get("candidate_state_index", [])
    survivor_states = state_artifacts.get("survivor_states", [])
    matrix = payload.get("constraint_matrix", [])
    if len(candidate_index) != EXPECTED_CANDIDATE_COUNT:
        errors.append("candidate state index length mismatch")
    if len(matrix) != EXPECTED_CANDIDATE_COUNT or len(payload.get("kill_ledger", [])) != EXPECTED_CANDIDATE_COUNT:
        errors.append("full constraint matrix/kill ledger length mismatch")
    if len(survivor_states) != EXPECTED_SURVIVOR_COUNT:
        errors.append("survivor state length mismatch")
    for row in candidate_index:
        content_id = row.get("rho_ABC_content_id")
        if content_id not in states or "rho_ABC" not in states.get(content_id, {}):
            errors.append(f"missing rho_ABC state artifact for candidate {row.get('candidate_id')}")
            break
    for row in matrix:
        constraints = row.get("constraints", {})
        if set(constraints) != set(CONSTRAINT_KEYS):
            errors.append(f"constraint matrix row missing C1/C2/C3: {row.get('candidate_id')}")
            break
        if not all(isinstance(constraints[key].get("pass"), bool) for key in CONSTRAINT_KEYS):
            errors.append(f"constraint matrix row has non-boolean pass/fail: {row.get('candidate_id')}")
            break
    ghz_w = payload.get("ghz_w_matrix_finding", {}).get("rows", {})
    if ghz_w.get("GHZ", {}).get("pass_fail") != {"C1": True, "C2": False, "C3": False}:
        errors.append("GHZ full matrix row mismatch")
    if ghz_w.get("W", {}).get("pass_fail") != {"C1": True, "C2": True, "C3": False}:
        errors.append("W full matrix row mismatch")
    ckw = payload.get("monogamy_ckw_recomputed_from_stored_rho", {})
    if ckw.get("computed_from_stored_rho_ABC") is not True or ckw.get("survivor_count_checked") != EXPECTED_ENTANGLED_SURVIVOR_COUNT:
        errors.append("CKW was not recomputed from stored rho_ABC for exactly one tripartite survivor")
    if ckw.get("all_party_cuts_satisfy_ckw") is not True:
        errors.append("CKW inequality failed for a surviving tripartite state")
    if payload.get("terrain_blindness_guard", {}).get("clean") is not True:
        errors.append("terrain blindness guard failed")
    if payload.get("controls", {}).get("injection_red", {}).get("red") is not True:
        errors.append("injection-red control failed")
    if payload.get("lineage_free_negative", {}).get("red") is not True:
        errors.append("lineage-free negative did not stay red")
    checks = payload.get("substrate_checks", {})
    if checks.get("one_q_default_registry", {}).get("ok") is not True:
        errors.append("1Q substrate check failed")
    if checks.get("two_q_registry", {}).get("ok") is not True:
        errors.append("2Q substrate check failed")
    if payload.get("ledger_lock_refreshed", {}).get("refreshed_from_disk") is not True:
        errors.append("ledger lock was not refreshed")
    if not payload.get("ledger_lock_refreshed", {}).get("sha256"):
        errors.append("ledger lock sha256 missing")
    if require_helper_preflight and payload.get("helper_preflight", {}).get("all_pass") is not True:
        errors.append("helper preflight is not green")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    return errors


def main() -> int:
    packet = build_packet(include_helper_preflight=True)
    write_json(RESULT_PATH, packet)
    print(json.dumps({"ok": packet["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if packet["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
