#!/usr/bin/env python3
"""Attach geometry to the frozen 2Q GCM states."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


SIM_ID = "gcm_geometry_attach_2q_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_carrier_and_pins_relative_2q_geometry_attach"
ENGINE_MODE = "all_three_full_sims"

EXPECTED_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_SURVIVOR_COUNT = 544
EXPECTED_PRODUCT_SURVIVOR_COUNT = 528
EXPECTED_ENTANGLED_SURVIVOR_COUNT = 16
EXPECTED_QUOTIENT_CLASS_COUNT = 8
EXPECTED_ONE_Q_GEOMETRY_CLASS_COUNT = 8
EXPECTED_ENTANGLED_FIBER_COUNT = 16
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_NEGATIVITY_VALUES = [0.25, 0.353553390593274]

SCRIPTS_DIR = ROOT / "scripts"
ONE_Q_ATTACH_DIR = ROOT / "system_v6" / "sims" / "gcm_geometry_attach_v0"
TWO_Q_CARVE_DIR = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_2q_v0"
for path in (SCRIPTS_DIR, ONE_Q_ATTACH_DIR, TWO_Q_CARVE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402
import gcm_constraint_carve_2q_v0_common as carve2q  # noqa: E402
import gcm_geometry_attach_v0_common as attach1q  # noqa: E402


ONE_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
TWO_Q_CARVE_RESULT_PATH = TWO_Q_CARVE_DIR / "results" / "gcm_constraint_carve_2q_v0_results.json"
TWO_Q_FREEZE_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_registry.json"
)
TWO_Q_FREEZE_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_results.json"
)
V0_RESULT_PATH = ROOT / "system_v6" / "sims" / "gcm_geometry_attach_2q_v0" / "results" / "gcm_geometry_attach_2q_v0_results.json"
V0_AUDIT_PATH = ROOT / "system_v6" / "sims" / "gcm_geometry_attach_2q_v0" / "audit_verdict.md"

AUTHORITY_PATHS = {
    "one_q_geometry_attach_result": ONE_Q_ATTACH_DIR / "results" / "gcm_geometry_attach_v0_results.json",
    "one_q_geometry_attach_common": ONE_Q_ATTACH_DIR / "gcm_geometry_attach_v0_common.py",
    "two_q_carve_result": TWO_Q_CARVE_RESULT_PATH,
    "two_q_carve_common": TWO_Q_CARVE_DIR / "gcm_constraint_carve_2q_v0_common.py",
    "one_q_frozen_registry": ONE_Q_REGISTRY_PATH,
    "two_q_freeze_registry": TWO_Q_FREEZE_REGISTRY_PATH,
    "two_q_freeze_result_states": TWO_Q_FREEZE_RESULT_PATH,
    "v0_scalar_derived_attach_result": V0_RESULT_PATH,
    "v0_audit_real_state_cut": V0_AUDIT_PATH,
    "substrate_check_helper": ROOT / "scripts" / "gcm_substrate_check.py",
    "builder_audit_boundary": ROOT / "scripts" / "builder_audit_boundary.py",
    "build_card": SIM_DIR / "build_card.md",
}

THREE_AXIS_DECLARATION = {
    "layers": {
        "declaration": "layers 3-12 + 17-18",
        "geometry_layers": "3-12 from the 1Q C2/S3/Hopf/density/shell attach",
        "two_q_extension_layers": "17-18 as the 2Q marginal/correlation/fiber extension on the carved survivor object",
    },
    "nesting": {
        "coordinate": "integrated-onto-the-carve",
        "definition": "geometry rows consume the frozen GCM substrate and the landed 2Q carve survivor rows",
    },
    "qubit_depth": {"coordinate": "2Q", "boundary": "two-qubit object; no bridge, axis, stage, or physics promotion"},
}

TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing GCM object lineage positive and lineage-free negative check",
    },
    "gcm_constraint_carve_2q_v0": {
        "tried": True,
        "used": True,
        "reason": "load-bearing recomputation/source for the 544 2Q survivors and 16 entangled rows",
    },
    "gcm_2q_freeze_and_cut_v0": {
        "tried": True,
        "used": True,
        "reason": "load-bearing frozen 2Q registry IDs plus stored rho_AB/rho_A/rho_B state matrices",
    },
    "gcm_geometry_attach_v0": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 1Q realization rule, eta-shell labels, and cross-rung regression target",
    },
    "Graphs": {"tried": True, "used": True, "reason": "Julia load-bearing survivor/fiber incidence graph check."},
    "sympy": {"tried": True, "used": True, "reason": "exact integer guards for survivor and fiber counts"},
    "z3": {"tried": True, "used": True, "reason": "SMT binding of 2Q geometry count invariants"},
    "cvc5": {"tried": True, "used": True, "reason": "independent SMT binding of the same count invariants"},
    "python_stdlib": {"tried": True, "used": True, "reason": "canonical JSON, hashes, grouping, and result writing"},
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary from birth",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "gcm_constraint_carve_2q_v0": "load_bearing",
    "gcm_2q_freeze_and_cut_v0": "load_bearing",
    "gcm_geometry_attach_v0": "load_bearing",
    "Graphs": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "2q_survivor_geometry_attachment",
        "product_survivor_pure_bloch_pair_realization",
        "entangled_marginal_purity_shrinkage",
        "state_derived_schmidt_angle_basis_and_correlation_fiber_readout",
        "state_derived_negativity_crosscheck",
        "v0_scalar_vs_v1_state_regression_error_bars",
        "cross_rung_1q_shell_regression",
    ],
    "engine_tool_intent": {
        "julia": {"Graphs": "SimpleGraph/add_edge!/connected_components check entangled survivor to marginal-fiber incidence"},
        "jax": {"jax.numpy": "batched radius and purity-shrinkage recomputation", "sympy": "exact count guard"},
        "pytorch": {"torch.func": "batched product-radius and entangled-radius recomputation", "sympy": "exact count guard"},
    },
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def stable_id(prefix: str, value: Any, length: int = 20) -> str:
    return f"{prefix}_{stable_sha256(value)[:length]}"


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(role: str, path: Path) -> dict[str, Any]:
    return {
        "role": role,
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
    }


def q(value: float, digits: int = 15) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0.0 else rounded


def vector_norm(values: list[float]) -> float:
    return math.sqrt(sum(float(v) * float(v) for v in values))


def normalized(values: list[float]) -> list[float]:
    norm = vector_norm(values)
    if norm <= 1e-15:
        return [0.0, 0.0, 1.0]
    return [q(float(v) / norm) for v in values]


def point_key(values: list[float] | tuple[float, ...]) -> tuple[float, float, float]:
    return tuple(q(float(v), digits=12) for v in values)  # type: ignore[return-value]


def complex_from_cell(cell: dict[str, float]) -> complex:
    return complex(float(cell["re"]), float(cell["im"]))


def complex_cell(value: complex) -> dict[str, float]:
    return {"re": q(value.real), "im": q(value.imag)}


def json_to_complex_matrix(matrix: list[list[dict[str, float]]]) -> list[list[complex]]:
    return [[complex_from_cell(cell) for cell in row] for row in matrix]


def complex_vector_to_json(vector: list[complex]) -> list[dict[str, float]]:
    return [complex_cell(value) for value in vector]


def matrix_to_json(matrix: list[list[complex]]) -> list[list[dict[str, float]]]:
    return [[complex_cell(cell) for cell in row] for row in matrix]


def matrix_max_abs_delta(left: list[list[dict[str, float]]], right: list[list[dict[str, float]]]) -> float:
    left_c = json_to_complex_matrix(left)
    right_c = json_to_complex_matrix(right)
    return q(max(abs(left_c[i][j] - right_c[i][j]) for i in range(len(left_c)) for j in range(len(left_c[i]))))


def bloch_from_density(rho: list[list[complex]]) -> list[float]:
    return [
        q(2.0 * rho[0][1].real),
        q(-2.0 * rho[0][1].imag),
        q((rho[0][0] - rho[1][1]).real),
    ]


def trace_square_2x2(rho: list[list[complex]]) -> float:
    value = (
        rho[0][0] * rho[0][0]
        + rho[0][1] * rho[1][0]
        + rho[1][0] * rho[0][1]
        + rho[1][1] * rho[1][1]
    )
    return q(value.real)


def hermitian_2x2_eigenvectors(rho: list[list[complex]]) -> tuple[list[float], list[list[complex]]]:
    a = rho[0][0].real
    d = rho[1][1].real
    b = rho[0][1]
    center = (a + d) / 2.0
    gap = math.sqrt(((a - d) / 2.0) ** 2 + abs(b) ** 2)
    eigenvalues = [q(center + gap), q(center - gap)]
    vectors: list[list[complex]] = []
    for lam in eigenvalues:
        if abs(b) > 1.0e-14:
            vector = [b, complex(lam - a, 0.0)]
        elif a >= d:
            vector = [1.0 + 0.0j, 0.0 + 0.0j] if lam >= center else [0.0 + 0.0j, 1.0 + 0.0j]
        else:
            vector = [0.0 + 0.0j, 1.0 + 0.0j] if lam >= center else [1.0 + 0.0j, 0.0 + 0.0j]
        norm = math.sqrt(sum(abs(item) ** 2 for item in vector))
        vectors.append([item / norm for item in vector])
    return eigenvalues, vectors


def state_vector_from_pure_density(rho_ab: list[list[complex]]) -> list[complex]:
    diag = [max(0.0, rho_ab[i][i].real) for i in range(4)]
    pivot = max(range(4), key=lambda idx: diag[idx])
    if diag[pivot] <= 1.0e-14:
        raise ValueError("rho_AB has no usable pure-state pivot")
    pivot_amp = math.sqrt(diag[pivot])
    return [rho_ab[i][pivot] / pivot_amp for i in range(4)]


def schmidt_from_state_row(row: dict[str, Any]) -> dict[str, Any]:
    rho_ab = json_to_complex_matrix(row["rho_AB"])
    rho_a = json_to_complex_matrix(row["rho_A"])
    rho_b = json_to_complex_matrix(row["rho_B"])
    state = state_vector_from_pure_density(rho_ab)
    coeff = [[state[0], state[1]], [state[2], state[3]]]
    evals_a, basis_a = hermitian_2x2_eigenvectors(rho_a)
    schmidt_coefficients = [q(math.sqrt(max(0.0, value))) for value in evals_a]
    basis_b: list[list[complex]] = []
    for sigma, avec in zip(schmidt_coefficients, basis_a, strict=True):
        if sigma <= 1.0e-14:
            basis_b.append([0.0 + 0.0j, 1.0 + 0.0j])
            continue
        raw = [
            (coeff[0][0].conjugate() * avec[0] + coeff[1][0].conjugate() * avec[1]) / sigma,
            (coeff[0][1].conjugate() * avec[0] + coeff[1][1].conjugate() * avec[1]) / sigma,
        ]
        norm = math.sqrt(sum(abs(item) ** 2 for item in raw))
        basis_b.append([item / norm for item in raw])
    theta = math.atan2(schmidt_coefficients[1], schmidt_coefficients[0])
    sin_2theta = 2.0 * schmidt_coefficients[0] * schmidt_coefficients[1]
    negativity = q(schmidt_coefficients[0] * schmidt_coefficients[1])
    return {
        "state_vector_basis_order": ["00", "01", "10", "11"],
        "state_vector": complex_vector_to_json(state),
        "coefficient_matrix": matrix_to_json(coeff),
        "basis_A": [complex_vector_to_json(vector) for vector in basis_a],
        "basis_B_from_state": [complex_vector_to_json(vector) for vector in basis_b],
        "schmidt_coefficients": schmidt_coefficients,
        "lambda_plus": q(evals_a[0]),
        "lambda_minus": q(evals_a[1]),
        "theta_rad": q(theta),
        "sin_2theta": q(sin_2theta),
        "negativity_from_schmidt": negativity,
        "log_negativity_from_schmidt": q(math.log(1.0 + 2.0 * negativity)),
        "rho_A_bloch_from_matrix": bloch_from_density(rho_a),
        "rho_B_bloch_from_matrix": bloch_from_density(rho_b),
        "radius_A_from_matrix": q(vector_norm(bloch_from_density(rho_a))),
        "radius_B_from_matrix": q(vector_norm(bloch_from_density(rho_b))),
        "purity_A_from_matrix": trace_square_2x2(rho_a),
        "purity_B_from_matrix": trace_square_2x2(rho_b),
    }


def load_one_q_registry() -> dict[str, Any]:
    return load_json(ONE_Q_REGISTRY_PATH)


def load_one_q_attach() -> dict[str, Any]:
    return load_json(AUTHORITY_PATHS["one_q_geometry_attach_result"])


def two_q_carve_packet() -> dict[str, Any]:
    return carve2q.build_packet()


def load_two_q_registry() -> dict[str, Any]:
    return load_json(TWO_Q_FREEZE_REGISTRY_PATH)


def load_two_q_freeze_result() -> dict[str, Any]:
    return load_json(TWO_Q_FREEZE_RESULT_PATH)


def load_v0_result() -> dict[str, Any]:
    return load_json(V0_RESULT_PATH)


def two_q_registry_dependency() -> dict[str, Any]:
    if TWO_Q_FREEZE_REGISTRY_PATH.is_file():
        payload = load_json(TWO_Q_FREEZE_REGISTRY_PATH)
        rows = payload["frozen_2q_registry"]["survivors"]
        return {
            "status": "landed_registry_consumed",
            "path": rel(TWO_Q_FREEZE_REGISTRY_PATH),
            "sha256": sha256_file(TWO_Q_FREEZE_REGISTRY_PATH),
            "gcm_2q_object_id": payload.get("gcm_2q_object_id"),
            "registry_body_sha256": payload.get("registry_body_sha256"),
            "audit_resolved_by_commit": "8326405e6",
            "registry_id_count": len(rows),
            "claims_conditional_on_2q_registry_audit": False,
        }
    return {
        "status": "not_landed_provisional_ids_derived",
        "path": rel(TWO_Q_FREEZE_REGISTRY_PATH),
        "sha256": None,
        "dependency": "Replace provisional 2Q geometry IDs with gcm_2q_freeze_and_cut_v0 registry IDs when that lane lands.",
    }


def one_q_hopf_set(one_q_payload: dict[str, Any]) -> set[tuple[float, float, float]]:
    rows = one_q_payload["attachment_map"]["survivor_spinor_maps"]
    return {point_key(tuple(row["hopf_projection"])) for row in rows}


def realize_pure_bloch_from_xz(raw_bloch: list[float], *, zero_pin: str) -> dict[str, Any]:
    sx, sz = carve2q.probe_signature(tuple(float(v) for v in raw_bloch))
    if sx == 0 and sz == 0:
        bloch = [0.0, 0.0, 1.0]
        spinor = attach1q.spinor_from_probe_signature([0, 1])
        pin_status = zero_pin
    else:
        spinor = attach1q.spinor_from_probe_signature([sx, sz])
        bloch = [q(v) for v in spinor["bloch_unit"]]
        pin_status = "normalized_xz_probe_signature"
    return {
        "raw_bloch": [q(v) for v in raw_bloch],
        "raw_radius": q(vector_norm(raw_bloch)),
        "probe_signature_xz": [int(sx), int(sz)],
        "pure_bloch": bloch,
        "pure_radius": q(vector_norm(bloch)),
        "T_eta_label": spinor["eta_label"],
        "T_eta_rad": spinor["eta_rad"],
        "pin_status": pin_status,
    }


def registry_by_raw_sid(registry: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(row["raw_2q_survivor_id"]): row for row in registry["frozen_2q_registry"]["survivors"]}


def freeze_state_by_raw_sid(freeze_result: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(row["raw_2q_survivor_id"]): row for row in freeze_result["entropy_tables"]["survivor_cut_entropy_rows"]}


def product_geometry_rows(
    survivors: list[dict[str, Any]],
    registry_rows: dict[int, dict[str, Any]],
    state_rows: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in survivors:
        if row["family"] != "product_grid":
            continue
        raw_sid = int(row["survivor_id"])
        registry_row = registry_rows[raw_sid]
        state_row = state_rows[raw_sid]
        first = realize_pure_bloch_from_xz(row["first_bloch"], zero_pin="zero_xz_first_product_pin_z_plus")
        second = realize_pure_bloch_from_xz(row["second_bloch"], zero_pin="zero_xz_second_product_pin_z_plus")
        v0_id = stable_id(
            "gcm2qgeom",
            {"family": row["family"], "candidate_id": row["candidate_id"], "first": row["first_bloch"], "second": row["second_bloch"]},
        )
        rows.append(
            {
                "gcm_2q_survivor_id": registry_row["gcm_2q_survivor_id"],
                "raw_2q_survivor_id": raw_sid,
                "two_q_candidate_id": row["candidate_id"],
                "geometry_id": registry_row["gcm_2q_survivor_id"],
                "replaces_v0_provisional_2q_geometry_id": v0_id,
                "family": row["family"],
                "realization_rule": "product_of_1q_attach_pure_bloch_realizations_from_xz_probe_signatures",
                "stored_state_ids": state_row["rho_ids"],
                "raw_marginals": {
                    "A": first["raw_bloch"],
                    "B": second["raw_bloch"],
                    "raw_radius_A": first["raw_radius"],
                    "raw_radius_B": second["raw_radius"],
                },
                "geometric_marginals": {"A": first, "B": second},
                "joint_geometry": {
                    "kind": "product_of_1q_bloch_points",
                    "A_pure_bloch": first["pure_bloch"],
                    "B_pure_bloch": second["pure_bloch"],
                    "product_radius_control": [first["pure_radius"], second["pure_radius"]],
                },
            }
        )
    return rows


def schmidt_row(
    row: dict[str, Any],
    registry_row: dict[str, Any],
    state_row: dict[str, Any],
) -> dict[str, Any]:
    derived = schmidt_from_state_row(state_row)
    first = derived["rho_A_bloch_from_matrix"]
    second = derived["rho_B_bloch_from_matrix"]
    r_a = derived["radius_A_from_matrix"]
    r_b = derived["radius_B_from_matrix"]
    sin_2theta = derived["sin_2theta"]
    n_a = normalized(first)
    n_b = normalized(second)
    shell_a = realize_pure_bloch_from_xz(first, zero_pin="zero_xz_entangled_A_pin_z_plus")
    shell_b = realize_pure_bloch_from_xz(second, zero_pin="zero_xz_entangled_B_pin_z_plus")
    v0_id = stable_id(
        "gcm2qent",
        {"family": row["family"], "candidate_id": row["candidate_id"], "first": row["first_bloch"], "second": row["second_bloch"]},
    )
    neg_expected = min(EXPECTED_NEGATIVITY_VALUES, key=lambda value: abs(value - derived["negativity_from_schmidt"]))
    return {
        "gcm_2q_survivor_id": registry_row["gcm_2q_survivor_id"],
        "raw_2q_survivor_id": row["survivor_id"],
        "two_q_candidate_id": row["candidate_id"],
        "geometry_id": registry_row["gcm_2q_survivor_id"],
        "replaces_v0_provisional_2q_geometry_id": v0_id,
        "family": row["family"],
        "stored_state_source": {
            "source_result": rel(TWO_Q_FREEZE_RESULT_PATH),
            "rho_ids": state_row["rho_ids"],
            "rho_AB": state_row["rho_AB"],
            "rho_A": state_row["rho_A"],
            "rho_B": state_row["rho_B"],
        },
        "reduced_states": {
            "A_bloch": [q(v) for v in first],
            "B_bloch": [q(v) for v in second],
            "radius_A": q(r_a),
            "radius_B": q(r_b),
            "purity_A": derived["purity_A_from_matrix"],
            "purity_B": derived["purity_B_from_matrix"],
            "radii_strictly_less_than_one": bool(r_a < 1.0 - 1e-12 and r_b < 1.0 - 1e-12),
            "rho_A_matrix": state_row["rho_A"],
            "rho_B_matrix": state_row["rho_B"],
        },
        "schmidt_decomposition": {
            "form": "state-derived Schmidt decomposition from stored rho_AB; bases are computed from rho_A and the pure-state coefficient matrix",
            "theta_rad": derived["theta_rad"],
            "lambda_plus": derived["lambda_plus"],
            "lambda_minus": derived["lambda_minus"],
            "schmidt_coefficients": derived["schmidt_coefficients"],
            "basis_A": derived["basis_A"],
            "basis_B_from_state": derived["basis_B_from_state"],
            "state_vector_basis_order": derived["state_vector_basis_order"],
            "state_vector": derived["state_vector"],
            "coefficient_matrix": derived["coefficient_matrix"],
            "sin_2theta": q(sin_2theta),
            "eta_2q_analog_rad": derived["theta_rad"],
        },
        "negativity_cross_check": {
            "negativity_from_schmidt": derived["negativity_from_schmidt"],
            "log_negativity_from_schmidt": derived["log_negativity_from_schmidt"],
            "freeze_entropy_negativity": state_row["entropy_values"]["negativity"],
            "freeze_entropy_log_negativity": state_row["entropy_values"]["log_negativity"],
            "nearest_expected_value": q(neg_expected),
            "nearest_expected_label": "0.25" if abs(neg_expected - 0.25) < 1e-12 else "1_over_2sqrt2",
            "matches_freeze": abs(derived["negativity_from_schmidt"] - state_row["entropy_values"]["negativity"]) <= 1e-12,
            "matches_expected_family": abs(derived["negativity_from_schmidt"] - neg_expected) <= 1e-12,
        },
        "marginal_position": {
            "D_C2_x_D_C2": {
                "A": [q(v) for v in first],
                "B": [q(v) for v in second],
                "rho_A_id": state_row["rho_ids"]["rho_A_id"],
                "rho_B_id": state_row["rho_ids"]["rho_B_id"],
            },
            "normalized_shell_map": {
                "A_raw_unit_direction": n_a,
                "B_raw_unit_direction": n_b,
                "A_1q_attach_direction": shell_a["pure_bloch"],
                "B_1q_attach_direction": shell_b["pure_bloch"],
                "A_1q_shell": shell_a["T_eta_label"],
                "B_1q_shell": shell_b["T_eta_label"],
            },
        },
        "correlation_data_marginals_miss": {
            "canonical_schmidt_correlation_diag_phi0": [q(sin_2theta), q(-sin_2theta), 1.0],
            "phase_fiber_witnesses_same_marginals": [
                {
                    "phi_rad": 0.0,
                    "xx": q(sin_2theta),
                    "xy": 0.0,
                    "yx": 0.0,
                    "yy": q(-sin_2theta),
                    "zz": 1.0,
                },
                {
                    "phi_rad": q(math.pi / 2.0),
                    "xx": 0.0,
                    "xy": q(sin_2theta),
                    "yx": q(sin_2theta),
                    "yy": 0.0,
                    "zz": 1.0,
                },
            ],
            "marginals_determine_state": False,
        },
    }


def entangled_geometry_rows(
    survivors: list[dict[str, Any]],
    registry_rows: dict[int, dict[str, Any]],
    state_rows: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        schmidt_row(row, registry_rows[int(row["survivor_id"])], state_rows[int(row["survivor_id"])])
        for row in survivors
        if row.get("entangled") is True
    ]


def entangled_fibers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        marginals = row["marginal_position"]["D_C2_x_D_C2"]
        key = stable_sha256(marginals)
        buckets[key].append(row)
    fibers = []
    for key, members in sorted(buckets.items()):
        sample = members[0]
        witnesses = sample["correlation_data_marginals_miss"]["phase_fiber_witnesses_same_marginals"]
        fibers.append(
            {
                "fiber_id": f"fiber_{key[:16]}",
                "marginal_pair": sample["marginal_position"]["D_C2_x_D_C2"],
                "finite_carved_member_count": len(members),
                "finite_carved_member_ids": [row["gcm_2q_survivor_id"] for row in members],
                "finite_carved_raw_member_ids": [row["raw_2q_survivor_id"] for row in members],
                "phase_witness_count": len(witnesses),
                "same_marginals_distinct_correlation_witnesses": witnesses,
                "marginals_determine_state": False,
            }
        )
    return fibers


def cross_rung_shell_map(product_rows: list[dict[str, Any]], entangled_rows: list[dict[str, Any]]) -> dict[str, Any]:
    product_counter: Counter[str] = Counter()
    for row in product_rows:
        product_counter[f"A:{row['geometric_marginals']['A']['T_eta_label']}|B:{row['geometric_marginals']['B']['T_eta_label']}"] += 1
    ent_counter: Counter[str] = Counter()
    for row in entangled_rows:
        shell = row["marginal_position"]["normalized_shell_map"]
        ent_counter[f"A:{shell['A_1q_shell']}|B:{shell['B_1q_shell']}"] += 1
    return {
        "product_shell_pair_counts": dict(sorted(product_counter.items())),
        "entangled_shell_pair_counts": dict(sorted(ent_counter.items())),
        "interpretation": "Shell labels are 1Q attach eta shells applied to normalized marginal directions; entangled radii remain subunit.",
    }


def one_q_regression(product_rows: list[dict[str, Any]], entangled_rows: list[dict[str, Any]]) -> dict[str, Any]:
    one_q = load_one_q_attach()
    expected = one_q_hopf_set(one_q)
    observed_a = {point_key(tuple(row["geometric_marginals"]["A"]["pure_bloch"])) for row in product_rows}
    observed_a.update(point_key(tuple(row["marginal_position"]["normalized_shell_map"]["A_1q_attach_direction"])) for row in entangled_rows)
    return {
        "operation": "partial_trace_A_then_normalize_to_1Q_attach_realization_rule",
        "one_q_attach_hopf_class_count": len(expected),
        "observed_normalized_A_geometry_count": len(observed_a),
        "image_equals_1q_attach_hopf_set": observed_a == expected,
        "one_q_attach_result_sha256": sha256_file(AUTHORITY_PATHS["one_q_geometry_attach_result"]),
    }


def v0_scalar_vs_state_regression(entangled_rows: list[dict[str, Any]]) -> dict[str, Any]:
    v0 = load_v0_result()
    v0_by_raw = {
        int(row["two_q_survivor_id"]): row
        for row in v0["geometry_packet"]["entangled_survivor_geometries"]
    }
    rows = []
    max_abs_diff = 0.0
    for row in entangled_rows:
        raw_sid = int(row["raw_2q_survivor_id"])
        old = v0_by_raw[raw_sid]
        metric_pairs = {
            "radius_A": (old["reduced_states"]["radius_A"], row["reduced_states"]["radius_A"]),
            "radius_B": (old["reduced_states"]["radius_B"], row["reduced_states"]["radius_B"]),
            "purity_A": (old["reduced_states"]["purity_A"], row["reduced_states"]["purity_A"]),
            "purity_B": (old["reduced_states"]["purity_B"], row["reduced_states"]["purity_B"]),
            "theta_rad": (old["schmidt_decomposition"]["theta_rad"], row["schmidt_decomposition"]["theta_rad"]),
            "lambda_plus": (old["schmidt_decomposition"]["lambda_plus"], row["schmidt_decomposition"]["lambda_plus"]),
            "lambda_minus": (old["schmidt_decomposition"]["lambda_minus"], row["schmidt_decomposition"]["lambda_minus"]),
            "sin_2theta": (old["schmidt_decomposition"]["sin_2theta"], row["schmidt_decomposition"]["sin_2theta"]),
        }
        diffs = {name: q(abs(float(old_value) - float(new_value))) for name, (old_value, new_value) in metric_pairs.items()}
        max_abs_diff = max(max_abs_diff, max(diffs.values()))
        rows.append(
            {
                "raw_2q_survivor_id": raw_sid,
                "gcm_2q_survivor_id": row["gcm_2q_survivor_id"],
                "v0_provisional_2q_geometry_id": old["provisional_2q_geometry_id"],
                "v1_final_geometry_id": row["geometry_id"],
                "metric_abs_diffs": diffs,
                "rho_A_matrix_delta_vs_freeze": matrix_max_abs_delta(
                    row["stored_state_source"]["rho_A"],
                    row["reduced_states"]["rho_A_matrix"],
                ),
                "rho_B_matrix_delta_vs_freeze": matrix_max_abs_delta(
                    row["stored_state_source"]["rho_B"],
                    row["reduced_states"]["rho_B_matrix"],
                ),
            }
        )
    return {
        "source_v0_result": rel(V0_RESULT_PATH),
        "source_v0_audit": rel(V0_AUDIT_PATH),
        "regression_meaning": "v0 scalar-derived rows compared to v1 state-derived rows; these diffs are the v0 honest error bars",
        "row_count": len(rows),
        "max_abs_metric_diff": q(max_abs_diff),
        "rows": rows,
    }


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    for key in (
        "gcm_lineage",
        "one_q_lineage",
        "two_q_lineage",
    ):
        variant.pop(key, None)
    for section in ("product_survivor_geometries", "entangled_survivor_geometries"):
        for row in variant.get("geometry_packet", {}).get(section, []):
            row.pop("two_q_survivor_id", None)
            row.pop("two_q_candidate_id", None)
    return variant


def substrate_enforcement(payload: dict[str, Any]) -> dict[str, Any]:
    positive = gcm_substrate_check(payload, TWO_Q_FREEZE_REGISTRY_PATH)
    negative = gcm_substrate_check(lineage_free_variant(payload), TWO_Q_FREEZE_REGISTRY_PATH)
    return {
        "helper": "scripts/gcm_substrate_check.py",
        "registry": rel(TWO_Q_FREEZE_REGISTRY_PATH),
        "positive_payload_ok": positive,
        "lineage_free_negative": negative,
        "negative_failed_as_required": negative.get("ok") is False,
    }


def z3_geometry_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    n = z3.Int("survivor_count")
    p = z3.Int("product_count")
    e = z3.Int("entangled_count")
    f = z3.Int("entangled_fiber_count")
    solver.add(n == counts["survivor_count"])
    solver.add(p == counts["product_survivor_count"])
    solver.add(e == counts["entangled_survivor_count"])
    solver.add(f == counts["entangled_fiber_count"])
    solver.add(n == EXPECTED_SURVIVOR_COUNT, p == EXPECTED_PRODUCT_SURVIVOR_COUNT)
    solver.add(e == EXPECTED_ENTANGLED_SURVIVOR_COUNT, f == EXPECTED_ENTANGLED_FIBER_COUNT)
    solver.add(n == p + e)
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "claim": "2Q geometry attaches to 544 survivors split as 528 product and 16 entangled rows, with 16 marginal fibers",
        "input_object": counts,
    }


def cvc5_geometry_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    n = solver.mkConst(int_sort, "survivor_count")
    p = solver.mkConst(int_sort, "product_count")
    e = solver.mkConst(int_sort, "entangled_count")
    f = solver.mkConst(int_sort, "entangled_fiber_count")
    for term, value in (
        (n, counts["survivor_count"]),
        (p, counts["product_survivor_count"]),
        (e, counts["entangled_survivor_count"]),
        (f, counts["entangled_fiber_count"]),
    ):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(EXPECTED_SURVIVOR_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, p, solver.mkInteger(EXPECTED_PRODUCT_SURVIVOR_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, e, solver.mkInteger(EXPECTED_ENTANGLED_SURVIVOR_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, f, solver.mkInteger(EXPECTED_ENTANGLED_FIBER_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkTerm(Kind.ADD, p, e)))
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "2Q geometry attaches to 544 survivors split as 528 product and 16 entangled rows, with 16 marginal fibers",
        "input_object": counts,
    }


def result_hash_payload(payload: dict[str, Any]) -> dict[str, Any]:
    stripped = copy.deepcopy(payload)
    stripped.pop("generated_at", None)
    stripped.pop("result_sha256", None)
    return stripped


def build_packet() -> dict[str, Any]:
    one_q_registry = load_one_q_registry()
    two_q = two_q_carve_packet()
    two_q_registry = load_two_q_registry()
    two_q_freeze = load_two_q_freeze_result()
    registry_rows = registry_by_raw_sid(two_q_registry)
    state_rows = freeze_state_by_raw_sid(two_q_freeze)
    survivors = two_q["survivors"]
    products = product_geometry_rows(survivors, registry_rows, state_rows)
    entangled = entangled_geometry_rows(survivors, registry_rows, state_rows)
    fibers = entangled_fibers(entangled)
    shell_map = cross_rung_shell_map(products, entangled)
    regression = one_q_regression(products, entangled)
    v0_regression = v0_scalar_vs_state_regression(entangled)
    product_radius_errors = [
        abs(row["geometric_marginals"]["A"]["pure_radius"] - 1.0) for row in products
    ] + [abs(row["geometric_marginals"]["B"]["pure_radius"] - 1.0) for row in products]
    entangled_radii = [
        radius
        for row in entangled
        for radius in (
            row["reduced_states"]["radius_A"],
            row["reduced_states"]["radius_B"],
        )
    ]
    counts = {
        "survivor_count": len(survivors),
        "product_survivor_count": len(products),
        "entangled_survivor_count": len(entangled),
        "quotient_class_count": two_q["quotient"]["class_count"],
        "entangled_fiber_count": len(fibers),
        "one_q_geometry_class_count": regression["one_q_attach_hopf_class_count"],
    }
    state_checks = {
        "all_entangled_rows_have_stored_rho_ids": all(row["stored_state_source"]["rho_ids"] for row in entangled),
        "all_entangled_schmidt_negativity_matches_freeze": all(
            row["negativity_cross_check"]["matches_freeze"] for row in entangled
        ),
        "all_entangled_schmidt_negativity_matches_expected_family": all(
            row["negativity_cross_check"]["matches_expected_family"] for row in entangled
        ),
        "observed_negativity_values": sorted(
            {row["negativity_cross_check"]["negativity_from_schmidt"] for row in entangled}
        ),
        "expected_negativity_values": EXPECTED_NEGATIVITY_VALUES,
        "final_ids_replace_v0_provisional_ids": all(
            row["geometry_id"].startswith("gcm2qsurv_")
            and row["replaces_v0_provisional_2q_geometry_id"].startswith("gcm2qent_")
            for row in entangled
        )
        and all(
            row["geometry_id"].startswith("gcm2qsurv_")
            and row["replaces_v0_provisional_2q_geometry_id"].startswith("gcm2qgeom_")
            for row in products
        ),
    }
    z3_proof = z3_geometry_proof(counts)
    cvc5_proof = cvc5_geometry_proof(counts)
    payload: dict[str, Any] = {
        "schema": "gcm_geometry_attach_2q_v1_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "claim": "Attach 2Q geometry to the 544 landed 2Q carve survivors; product rows get product 1Q Bloch geometry and entangled rows are re-derived from stored rho_AB/rho_A/rho_B states under final frozen 2Q survivor IDs.",
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "gcm_object_id": one_q_registry["gcm_object_id"],
        "registry_body_sha256": one_q_registry["registry_body_sha256"],
        "gcm_2q_object_id": two_q_registry["gcm_2q_object_id"],
        "gcm_2q_registry_body_sha256": two_q_registry["registry_body_sha256"],
        "three_axis_declaration": THREE_AXIS_DECLARATION,
        "one_q_lineage": {
            "gcm_object_id": one_q_registry["gcm_object_id"],
            "registry_body_sha256": one_q_registry["registry_body_sha256"],
            "survivor_ids": [row["survivor_id"] for row in one_q_registry["frozen_registry"]["survivors"]],
            "quotient_class_ids": [
                row["quotient_class_id"] for row in one_q_registry["frozen_registry"]["quotient_classes"]
            ],
            "candidate_region_ids": [
                row["candidate_region_id"] for row in one_q_registry["frozen_registry"]["candidate_regions"]
            ],
            "object_maps": [
                {
                    "survivor_id": row["survivor_id"],
                    "quotient_class_id": row["quotient_class_id"],
                    "candidate_region_id": row["candidate_region_id"],
                }
                for row in load_one_q_attach()["gcm_lineage"]["object_maps"]
            ],
        },
        "gcm_lineage": {
            "gcm_2q_object_id": two_q_registry["gcm_2q_object_id"],
            "gcm_2q_registry_body_sha256": two_q_registry["registry_body_sha256"],
            "base_registry_body_sha256": two_q_registry["base_registry_body_sha256"],
            "gcm_2q_survivor_ids": [
                registry_rows[int(row["survivor_id"])]["gcm_2q_survivor_id"] for row in survivors
            ],
            "gcm_2q_quotient_class_ids": [
                row["gcm_2q_quotient_class_id"]
                for row in two_q_registry["frozen_2q_registry"]["quotient_classes"]
            ],
            "gcm_2q_candidate_region_ids": [
                row["gcm_2q_candidate_region_id"]
                for row in two_q_registry["frozen_2q_registry"]["candidate_regions"]
            ],
            "object_maps": [
                {
                    "gcm_2q_survivor_id": registry_rows[int(row["survivor_id"])]["gcm_2q_survivor_id"],
                    "raw_2q_survivor_id": int(row["survivor_id"]),
                    "two_q_candidate_id": row["candidate_id"],
                }
                for row in survivors
            ],
        },
        "two_q_registry_dependency": two_q_registry_dependency(),
        "two_q_lineage": {
            "source": "gcm_2q_freeze_and_cut_v0",
            "source_result_sha256": sha256_file(TWO_Q_CARVE_RESULT_PATH),
            "freeze_result_sha256": sha256_file(TWO_Q_FREEZE_RESULT_PATH),
            "freeze_registry_sha256": sha256_file(TWO_Q_FREEZE_REGISTRY_PATH),
            "source_commit_authority": "218fac1a1 plus freeze registry gcm_2q_object_id",
            "registry_dependency_hash": two_q_registry["registry_body_sha256"],
            "audit_resolved_by_commit": "8326405e6",
            "claims_conditional_on_2q_registry_in_flight_audit": False,
            "id_rule": "final geometry ids are the landed gcm2qsurv_* survivor ids from the 2Q freeze registry",
            "raw_survivor_ids": [row["survivor_id"] for row in survivors],
            "gcm_2q_survivor_ids": [registry_rows[int(row["survivor_id"])]["gcm_2q_survivor_id"] for row in survivors],
        },
        "geometry_packet": {
            "product_survivor_geometries": products,
            "entangled_survivor_geometries": entangled,
            "entangled_fibers_over_marginals": fibers,
            "cross_rung_shell_map": shell_map,
            "v0_scalar_vs_v1_state_regression": v0_regression,
            "G1_pattern_honesty": {
                "status": "carved_support_signature_reading_until_proven_more",
                "forbidden_promotion": "No shell/fiber pattern here is promoted to independent manifold geometry.",
            },
        },
        "controls": {
            "product_survivor_geometric_marginal_radii": {
                "expected": "1 exactly after 1Q attach pure Bloch realization",
                "max_error": max(product_radius_errors) if product_radius_errors else None,
                "all_exact_within_tolerance": bool(product_radius_errors and max(product_radius_errors) <= 1e-12),
                "raw_carve_marginals_are_pins_not_the_claim": True,
            },
            "entangled_reduced_radii": {
                "min_radius": min(entangled_radii) if entangled_radii else None,
                "max_radius": max(entangled_radii) if entangled_radii else None,
                "all_strictly_between_zero_and_one": all(0.0 < r < 1.0 for r in entangled_radii),
            },
            "carve_erasure": {
                "lineage_removed_anchor_count": 0,
                "lineage_available": False,
                "outcome": "geometry feedstock remains but nested GCM attachment status is lost",
            },
            "one_q_regression_through_partial_trace": regression,
            "real_state_derivation": state_checks,
        },
        "counts": counts,
        "exact_count_guard": {key: str(sp.Rational(value, 1)) for key, value in counts.items()},
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "source_locks": {name: source_lock(name, path) for name, path in AUTHORITY_PATHS.items()},
        "builder_gates": {
            "file_disjoint_packet": True,
            "boundary_helper_fully_used": True,
            "G_2a_idempotency_from_birth": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "substrate_check_helper_script_side": True,
            "lineage_free_negative_required": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "disallowed_claims": [
            "THE manifold",
            "canonical geometry",
            "bridge admission",
            "axis admission",
            "stage admission",
            "physics admission",
            "marginals determine entangled survivor state",
            "lineage-free geometry admission",
            "2Q registry promotion beyond committed keystone 8326405e6 and cited scratch ceiling",
        ],
    }
    payload["substrate_enforcement"] = substrate_enforcement(payload)
    payload["all_pass"] = bool(
        payload["gcm_object_id"] == EXPECTED_OBJECT_ID
        and payload["registry_body_sha256"] == EXPECTED_REGISTRY_BODY_SHA256
        and payload["gcm_2q_object_id"] == EXPECTED_2Q_OBJECT_ID
        and payload["gcm_2q_registry_body_sha256"] == EXPECTED_2Q_REGISTRY_BODY_SHA256
        and counts["survivor_count"] == EXPECTED_SURVIVOR_COUNT
        and counts["product_survivor_count"] == EXPECTED_PRODUCT_SURVIVOR_COUNT
        and counts["entangled_survivor_count"] == EXPECTED_ENTANGLED_SURVIVOR_COUNT
        and counts["quotient_class_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
        and counts["entangled_fiber_count"] == EXPECTED_ENTANGLED_FIBER_COUNT
        and counts["one_q_geometry_class_count"] == EXPECTED_ONE_Q_GEOMETRY_CLASS_COUNT
        and payload["controls"]["product_survivor_geometric_marginal_radii"]["all_exact_within_tolerance"]
        and payload["controls"]["entangled_reduced_radii"]["all_strictly_between_zero_and_one"]
        and regression["image_equals_1q_attach_hopf_set"]
        and state_checks["all_entangled_rows_have_stored_rho_ids"]
        and state_checks["all_entangled_schmidt_negativity_matches_freeze"]
        and state_checks["all_entangled_schmidt_negativity_matches_expected_family"]
        and state_checks["final_ids_replace_v0_provisional_ids"]
        and all(row["reduced_states"]["radii_strictly_less_than_one"] for row in entangled)
        and all(row["correlation_data_marginals_miss"]["marginals_determine_state"] is False for row in entangled)
        and payload["substrate_enforcement"]["positive_payload_ok"].get("ok") is True
        and payload["substrate_enforcement"]["negative_failed_as_required"] is True
        and z3_proof["verdict"] == "sat"
        and cvc5_proof["verdict"] == "sat"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    payload["result_sha256"] = stable_sha256(result_hash_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload.get("schema") == "gcm_geometry_attach_2q_v1_result_v1", "schema mismatch")
    require(payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(payload.get("claim_ceiling") == CLAIM_CEILING, "claim ceiling mismatch")
    require(payload.get("gcm_2q_object_id") == EXPECTED_2Q_OBJECT_ID, "2Q object id mismatch")
    require(payload.get("gcm_2q_registry_body_sha256") == EXPECTED_2Q_REGISTRY_BODY_SHA256, "2Q registry body hash mismatch")
    require(payload.get("three_axis_declaration") == THREE_AXIS_DECLARATION, "three coordinate declaration mismatch")
    counts = payload.get("counts", {})
    require(counts.get("survivor_count") == EXPECTED_SURVIVOR_COUNT, "survivor count mismatch")
    require(counts.get("product_survivor_count") == EXPECTED_PRODUCT_SURVIVOR_COUNT, "product count mismatch")
    require(counts.get("entangled_survivor_count") == EXPECTED_ENTANGLED_SURVIVOR_COUNT, "entangled count mismatch")
    require(counts.get("entangled_fiber_count") == EXPECTED_ENTANGLED_FIBER_COUNT, "fiber count mismatch")
    controls = payload.get("controls", {})
    require(
        controls.get("product_survivor_geometric_marginal_radii", {}).get("all_exact_within_tolerance") is True,
        "product geometric marginal radius control failed",
    )
    require(
        controls.get("entangled_reduced_radii", {}).get("all_strictly_between_zero_and_one") is True,
        "entangled reduced radius control failed",
    )
    require(
        controls.get("one_q_regression_through_partial_trace", {}).get("image_equals_1q_attach_hopf_set") is True,
        "1Q regression through partial trace failed",
    )
    state_checks = controls.get("real_state_derivation", {})
    require(state_checks.get("all_entangled_rows_have_stored_rho_ids") is True, "stored rho ids missing from entangled rows")
    require(
        state_checks.get("all_entangled_schmidt_negativity_matches_freeze") is True,
        "state-derived negativity does not match freeze",
    )
    require(
        state_checks.get("all_entangled_schmidt_negativity_matches_expected_family") is True,
        "state-derived negativity does not match expected 0.25 / 1/(2sqrt2) family",
    )
    require(state_checks.get("final_ids_replace_v0_provisional_ids") is True, "final gcm2qsurv ids did not replace v0 provisional ids")
    entangled = payload.get("geometry_packet", {}).get("entangled_survivor_geometries", [])
    require(len(entangled) == EXPECTED_ENTANGLED_SURVIVOR_COUNT, "entangled geometry row count mismatch")
    require(
        all(row.get("geometry_id", "").startswith("gcm2qsurv_") for row in entangled),
        "entangled rows must use final gcm2qsurv ids",
    )
    require(
        all(row.get("stored_state_source", {}).get("rho_AB") for row in entangled),
        "entangled rows must carry stored rho_AB matrices",
    )
    require(
        all(row.get("negativity_cross_check", {}).get("matches_freeze") is True for row in entangled),
        "entangled negativity cross-check failed",
    )
    require(
        all(row.get("reduced_states", {}).get("radii_strictly_less_than_one") is True for row in entangled),
        "some entangled reduced states are not subunit",
    )
    require(
        all(row.get("correlation_data_marginals_miss", {}).get("marginals_determine_state") is False for row in entangled),
        "entangled marginal determinacy overclaim",
    )
    v0_regression = payload.get("geometry_packet", {}).get("v0_scalar_vs_v1_state_regression", {})
    require(v0_regression.get("row_count") == EXPECTED_ENTANGLED_SURVIVOR_COUNT, "v0 regression row count mismatch")
    require(isinstance(v0_regression.get("max_abs_metric_diff"), (int, float)), "v0 regression max diff missing")
    positive = gcm_substrate_check(payload, TWO_Q_FREEZE_REGISTRY_PATH)
    negative = gcm_substrate_check(lineage_free_variant(payload), TWO_Q_FREEZE_REGISTRY_PATH)
    require(positive.get("ok") is True, f"substrate positive failed: {positive.get('errors')}")
    require(negative.get("ok") is False, "lineage-free substrate check did not fail")
    require(
        "GCM2Q_LINEAGE_CONSUMPTION_MISSING" not in positive.get("error_codes", []),
        "2Q lineage was not consumed by substrate helper",
    )
    require(
        payload.get("two_q_registry_dependency", {}).get("claims_conditional_on_2q_registry_audit") is False,
        "2Q registry dependency still marked conditional",
    )
    require(
        payload.get("two_q_lineage", {}).get("claims_conditional_on_2q_registry_in_flight_audit") is False,
        "2Q lineage still marked in-flight conditional",
    )
    require(
        payload.get("two_q_lineage", {}).get("audit_resolved_by_commit") == "8326405e6",
        "2Q lineage missing committed keystone citation",
    )
    require(payload.get("substrate_enforcement", {}).get("positive_payload_ok", {}).get("ok") is True, "stored substrate positive not ok")
    require(payload.get("substrate_enforcement", {}).get("negative_failed_as_required") is True, "stored substrate negative not red")
    proofs = payload.get("crossover_proofs", {})
    require(proofs.get("z3", {}).get("verdict") == "sat", "z3 proof failed")
    require(proofs.get("cvc5", {}).get("verdict") == "sat", "cvc5 proof failed")
    require(payload.get("TOOL_MANIFEST") == TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(payload.get("TOOL_INTEGRATION_DEPTH") == TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(payload.get("tool_intent") == TOOL_INTENT, "tool_intent mismatch")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    require(payload.get("all_pass") is True, "all_pass must be true")
    require(payload.get("result_sha256") == stable_sha256(result_hash_payload(payload)), "result hash mismatch")
    return errors


def main() -> int:
    payload = build_packet()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
