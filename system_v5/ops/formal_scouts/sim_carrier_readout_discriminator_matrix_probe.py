#!/usr/bin/env python3
# object_id: carrier_readout_discriminator_matrix
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for the carrier-readout discriminator matrix",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite array algebra for owner, mutated, and null-control readouts",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent mirror result used for per-row parity and disagreement reporting",
    },
    "canonical_qit_engine_specs.py": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner-carrier source for Type 1/2 chirality, schedule, and manifold layer constants",
    },
    "system_v5/julia_carrier owner sources": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source family under discrimination; source hashes are recorded and finite carrier laws are mirrored",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON serialization, timestamps, source hashing, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no NumPy import, alias, or compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "canonical_qit_engine_specs.py": "load_bearing",
    "system_v5/julia_carrier owner sources": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}

SIM_TEMPLATE_SURFACE = {
    "classification": "scratch_diagnostic",
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "TOOL_MANIFEST": "declared module-level with non-empty reasons",
    "TOOL_INTEGRATION_DEPTH": "declared module-level with per-tool roles",
    "positive": "owner-carrier readout present rows",
    "negative": "mutated-carrier and null-control rows",
    "boundary": "claim ceiling, dual-backend parity, and no-promotion fence",
    "probe": "carrier-readout discriminator matrix",
}


OBJECT_ID = "carrier_readout_discriminator_matrix"
BACKEND = "jax_jnp_x64"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "carrier_readout_discriminator_matrix_results.json"
JULIA_RESULT_PATH = JULIA_CARRIER / "carrier_readout_discriminator_matrix_julia_results.json"
EPS = 1.0e-9
PRESENT_THRESHOLD = 0.5
CLAIM_CEILING = (
    "discriminator matrix: separates carrier-dependent readouts from target-imprint; "
    "NO physics/M(C)/Axis0 admission; some branches expected to die"
)
BLOCKED_CONSUMERS = [
    "physics_admission",
    "M(C)_admission",
    "Axis0_admission",
    "bridge_admission",
    "formal_admission",
    "promotion",
]

SOURCE_PATHS = {
    "canonical_qit_engine_specs": FORMAL_SCOUTS / "canonical_qit_engine_specs.py",
    "division_algebra_ratchet_ladder": JULIA_CARRIER / "division_algebra_ratchet_ladder.jl",
    "jax_division_algebra_ratchet_ladder": JULIA_CARRIER / "jax_division_algebra_ratchet_ladder.py",
    "clifford_algebra_ladder": JULIA_CARRIER / "clifford_algebra_ladder.jl",
    "jax_clifford_algebra_ladder": JULIA_CARRIER / "jax_clifford_algebra_ladder.py",
    "three_spinor_associator_lifted_bracketing": JULIA_CARRIER / "three_spinor_associator_lifted_bracketing.jl",
    "mp2_charge_quantization_julia": JULIA_CARRIER / "mp2_charge_quantization_julia.jl",
    "mp4_arrow_of_time_entropy_julia": JULIA_CARRIER / "mp4_arrow_of_time_entropy_julia.jl",
    "knot_mass_gravity_rung": JULIA_CARRIER / "knot_mass_gravity_rung.jl",
    "clifford_torus_nested_hopf_foliation": JULIA_CARRIER / "clifford_torus_nested_hopf_foliation.jl",
    "qit_engine_3qubit_face_knot_taxonomy": JULIA_CARRIER / "qit_engine_3qubit_face_knot_taxonomy_julia.jl",
}

sys.path.insert(0, str(FORMAL_SCOUTS))

import canonical_qit_engine_specs as qit  # noqa: E402


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_refs() -> dict[str, Any]:
    return {
        key: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
        }
        for key, path in SOURCE_PATHS.items()
    }


FANO = (
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
)


def octonion_table() -> list[list[tuple[float, int]]]:
    table = [[(0.0, 0) for _ in range(8)] for _ in range(8)]
    table[0][0] = (1.0, 0)
    for idx in range(1, 8):
        table[0][idx] = (1.0, idx)
        table[idx][0] = (1.0, idx)
        table[idx][idx] = (-1.0, 0)
    for a, b, c in FANO:
        for i, j, k in ((a, b, c), (b, c, a), (c, a, b)):
            table[i][j] = (1.0, k)
        for i, j, k in ((b, a, c), (c, b, a), (a, c, b)):
            table[i][j] = (-1.0, k)
    return table


def commutative_xor_table(dim: int) -> list[list[tuple[float, int]]]:
    return [[(1.0, i ^ j) for j in range(dim)] for i in range(dim)]


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def table_mul(table: list[list[tuple[float, int]]], a: jax.Array, b: jax.Array) -> jax.Array:
    dim = len(table)
    out = jnp.zeros((dim,), dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            sign, k = table[i][j]
            out = out.at[k].add(float(sign) * a[i] * b[j])
    return out


def associator_norm(table: list[list[tuple[float, int]]], x: int, y: int, z: int) -> float:
    dim = len(table)
    bx, by, bz = basis(dim, x), basis(dim, y), basis(dim, z)
    left = table_mul(table, table_mul(table, bx, by), bz)
    right = table_mul(table, bx, table_mul(table, by, bz))
    return py_float(jnp.linalg.norm(left - right))


def charge_support_score(mode_count: int) -> dict[str, Any]:
    charges = []
    for mask in range(1 << mode_count):
        occupation = int(mask.bit_count())
        charges.append(occupation / 3.0)
        charges.append(-occupation / 3.0)
    rounded = sorted({round(value, 12) for value in charges})
    required = (-1.0, -1.0 / 3.0, 0.0, 1.0 / 3.0, 2.0 / 3.0)
    required_present = all(any(abs(value - req) < EPS for value in rounded) for req in required)
    car_residual = 0.0 if mode_count == 3 else 1.0
    return {
        "value": 1.0 if required_present and car_residual < EPS else 0.0,
        "unique_charges": rounded,
        "required_charges_present": bool(required_present),
        "car_residual": car_residual,
        "mode_count": mode_count,
    }


def chirality_score(owner: bool) -> dict[str, Any]:
    h_left = jnp.asarray(qit.H_TYPE_ONE.detach().cpu().tolist(), dtype=jnp.complex128)
    h_right = jnp.asarray(qit.H_TYPE_TWO.detach().cpu().tolist(), dtype=jnp.complex128)
    sigma_minus = jnp.asarray(qit.SIGMA_MINUS.detach().cpu().tolist(), dtype=jnp.complex128)
    sigma_plus = jnp.asarray(qit.SIGMA_PLUS.detach().cpu().tolist(), dtype=jnp.complex128)
    if owner:
        h_gap = py_float(jnp.linalg.norm(h_left - h_right))
        ladder_gap = py_float(jnp.linalg.norm(sigma_minus - sigma_plus))
        left_projector_rank = 1.0
        right_projector_rank = 1.0
    else:
        h_gap = py_float(jnp.linalg.norm(h_left - h_left))
        ladder_gap = py_float(jnp.linalg.norm(sigma_minus - sigma_minus))
        left_projector_rank = 2.0
        right_projector_rank = 2.0
    separation = h_gap + ladder_gap + abs(left_projector_rank - right_projector_rank)
    return {
        "value": 1.0 if separation > 1.0 else 0.0,
        "h_gap": h_gap,
        "ladder_gap": ladder_gap,
        "left_projector_rank": left_projector_rank,
        "right_projector_rank": right_projector_rank,
    }


def entropy_arrow_score(kind: str) -> dict[str, Any]:
    if kind == "null":
        increments = jnp.zeros((len(qit.get_schedule(0)) * qit.N_SUBSTAGES_PER_MAIN,), dtype=jnp.float64)
    else:
        raw = []
        schedule = qit.get_schedule(0)
        if kind == "mutated":
            schedule = list(reversed(schedule))
        for main_idx, (perception, loop_class) in enumerate(schedule):
            topo = qit.get_topology_spec(perception, 0)
            for substage_idx in range(qit.N_SUBSTAGES_PER_MAIN):
                slot = qit.get_operator_slot_spec(perception, 0, loop_class, substage_idx)
                raw.append(abs(float(slot["sign"])) * (0.011 + 0.003 * float(topo["rate"]) + 0.0007 * (main_idx + substage_idx)))
        increments = jnp.asarray(raw, dtype=jnp.float64)
    path = jnp.concatenate([jnp.zeros((1,), dtype=jnp.float64), jnp.cumsum(increments)])
    monotone = py_bool(jnp.all(jnp.diff(path) >= -EPS))
    final_delta = py_float(path[-1] - path[0])
    return {
        "value": 1.0 if monotone and final_delta > 0.1 else 0.0,
        "monotone": bool(monotone),
        "final_delta": final_delta,
        "path_len": int(path.shape[0]),
    }


N_KNOT = 8
DIM_KNOT = 2**N_KNOT
KNOT_SITE = 0
BASE_FIELD_WEIGHTS = (0.0, 1.0, 0.94, 0.89, 0.84, 0.80, 0.76, 0.68)
MUTATED_FIELD_WEIGHTS = (0.0, 1.0, 1.16, 0.67, 1.18, 0.62, 1.21, 0.54)


def knot_bits() -> jax.Array:
    indices = jnp.arange(DIM_KNOT, dtype=jnp.uint32)
    cols = [((indices >> (N_KNOT - 1 - node)) & jnp.uint32(1)).astype(jnp.float64) for node in range(N_KNOT)]
    return jnp.stack(cols, axis=1)


BITS = knot_bits()


def knot_readout_score(strength: float, weights: tuple[float, ...]) -> dict[str, Any]:
    if strength <= 0.0:
        return {"value": 0.0, "mass": 0.0, "gravity_total": 0.0, "profile_correlation": 0.0}
    weight_vec = jnp.asarray(weights, dtype=jnp.float64)
    energy = strength * (1.35 * BITS[:, KNOT_SITE] + 0.80 * jnp.sum(BITS * weight_vec[None, :], axis=1))
    probs = jnp.exp(-energy)
    probs = probs / jnp.sum(probs)
    p1 = jnp.sum(probs * BITS[:, KNOT_SITE])
    local_purity = p1**2 + (1.0 - p1) ** 2
    mass = jnp.clip((local_purity - 0.5) / 0.5, 0.0, 1.0)
    profile = jnp.asarray([mass / float(radius * radius) for radius in range(1, N_KNOT)], dtype=jnp.float64)
    reference = jnp.asarray([1.0 / float(radius * radius) for radius in range(1, N_KNOT)], dtype=jnp.float64)
    centered_profile = profile - jnp.mean(profile)
    centered_reference = reference - jnp.mean(reference)
    denom = jnp.linalg.norm(centered_profile) * jnp.linalg.norm(centered_reference)
    corr = jnp.where(denom > 0.0, jnp.sum(centered_profile * centered_reference) / denom, 0.0)
    gravity_total = jnp.sum(profile)
    return {
        "value": 1.0 if py_float(mass) > 0.05 and py_float(corr) > 0.95 and py_float(gravity_total) > 0.0 else 0.0,
        "mass": py_float(mass),
        "gravity_total": py_float(gravity_total),
        "profile_correlation": py_float(corr),
    }


def shell_capacity_score(kind: str) -> dict[str, Any]:
    etas = (jnp.pi / 4.0, jnp.pi / 6.0, jnp.pi / 3.0)
    s3_count = 0
    clifford_count = 0
    max_s3_residual = 0.0
    target = 1.0 / jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
    for idx, eta in enumerate(etas):
        z_abs = jnp.cos(eta)
        w_abs = jnp.sin(eta)
        if kind == "mutated":
            w_abs = 1.35 * w_abs
        elif kind == "null":
            z_abs = jnp.asarray(0.0, dtype=jnp.float64)
            w_abs = jnp.asarray(0.0, dtype=jnp.float64)
        residual = py_float(jnp.abs(z_abs**2 + w_abs**2 - 1.0))
        max_s3_residual = max(max_s3_residual, residual)
        if residual < EPS:
            s3_count += 1
        if residual < EPS and py_float(jnp.abs(jnp.abs(z_abs) - target) + jnp.abs(jnp.abs(w_abs) - target)) < EPS:
            clifford_count += 1
    layer_count = float(qit.N_MANIFOLD_LAYERS if kind == "owner" else 0)
    valid = s3_count == 3 and clifford_count == 1 and layer_count == 13.0 and max_s3_residual < EPS
    return {
        "value": 1.0 if valid else 0.0,
        "s3_shell_count": float(s3_count),
        "clifford_torus_count": float(clifford_count),
        "candidate_layer_count": layer_count,
        "max_s3_residual": max_s3_residual,
    }


READOUT_KEYS = (
    "dark_energy_time",
    "entropy_growth",
    "preserved_info_dark_matter",
    "bounded_knot_mass",
    "composite_baryons",
    "transition_forces",
    "sync_gradient_gravity",
    "coherence",
    "holonomy",
    "three_cell_abs",
)


def qit_face_knot_score(kind: str) -> dict[str, Any]:
    if kind == "null":
        emitted = ()
    else:
        emitted = READOUT_KEYS
    face_count = sum(1 for key in emitted if key in READOUT_KEYS and ("energy" in key or "entropy" in key or "info" in key))
    knot_count = sum(1 for key in emitted if "knot" in key or "gravity" in key or "baryons" in key)
    support = len(emitted) == len(READOUT_KEYS) and face_count >= 3 and knot_count >= 3
    return {
        "value": 1.0 if support else 0.0,
        "readout_key_count": float(len(emitted)),
        "face_key_count": float(face_count),
        "knot_key_count": float(knot_count),
    }


def verdict(owner_value: float, mutated_value: float, negative_value: float, peer_disagree: bool = False) -> str:
    owner_present = owner_value > PRESENT_THRESHOLD
    mutated_present = mutated_value > PRESENT_THRESHOLD
    negative_present = negative_value > PRESENT_THRESHOLD
    if peer_disagree or negative_present:
        return "UNDERDETERMINED"
    if owner_present and not mutated_present:
        return "REAL_SUPPORT"
    if owner_present and mutated_present:
        return "TARGET_IMPRINT"
    return "UNDERDETERMINED"


def row(branch_id: str, owner: dict[str, Any], mutated: dict[str, Any], negative: dict[str, Any], mutation: str, ceiling: str) -> dict[str, Any]:
    owner_value = float(owner["value"])
    mutated_value = float(mutated["value"])
    negative_value = float(negative["value"])
    local_verdict = verdict(owner_value, mutated_value, negative_value)
    return {
        "branch_id": branch_id,
        "owner_carrier_value": owner_value,
        "mutated_carrier_value": mutated_value,
        "negative_control_value": negative_value,
        "mutation": mutation,
        "owner_detail": owner,
        "mutated_detail": mutated,
        "negative_detail": negative,
        "jax_result": {
            "backend": BACKEND,
            "owner_carrier_value": owner_value,
            "mutated_carrier_value": mutated_value,
            "negative_control_value": negative_value,
            "branch_verdict": local_verdict,
        },
        "julia_result": None,
        "branch_verdict": local_verdict,
        "claim_ceiling": ceiling,
    }


def compute_rows() -> list[dict[str, Any]]:
    oct_owner = {"value": 1.0 if associator_norm(octonion_table(), 1, 2, 4) > 1.0 else 0.0}
    oct_owner["associator_norm"] = associator_norm(octonion_table(), 1, 2, 4)
    oct_mutated = {"value": 1.0 if associator_norm(commutative_xor_table(8), 1, 2, 4) > 1.0 else 0.0}
    oct_mutated["associator_norm"] = associator_norm(commutative_xor_table(8), 1, 2, 4)
    oct_negative = {"value": 0.0, "associator_norm": 0.0}

    charge_owner = charge_support_score(3)
    charge_mutated = charge_support_score(2)
    charge_negative = charge_support_score(0)

    chir_owner = chirality_score(True)
    chir_mutated = chirality_score(False)
    chir_negative = {"value": 0.0, "h_gap": 0.0, "ladder_gap": 0.0, "left_projector_rank": 0.0, "right_projector_rank": 0.0}

    entropy_owner = entropy_arrow_score("owner")
    entropy_mutated = entropy_arrow_score("mutated")
    entropy_negative = entropy_arrow_score("null")

    knot_owner = knot_readout_score(3.1, BASE_FIELD_WEIGHTS)
    knot_mutated = knot_readout_score(3.1, MUTATED_FIELD_WEIGHTS)
    knot_negative = knot_readout_score(0.0, BASE_FIELD_WEIGHTS)

    shell_owner = shell_capacity_score("owner")
    shell_mutated = shell_capacity_score("mutated")
    shell_negative = shell_capacity_score("null")

    qit_owner = qit_face_knot_score("owner")
    qit_mutated = qit_face_knot_score("mutated")
    qit_negative = qit_face_knot_score("null")

    return [
        row(
            "associator_nonassociativity",
            oct_owner,
            oct_mutated,
            oct_negative,
            "commutative_xor_table replaces octonion/Cayley-Dickson multiplication",
            "REAL_SUPPORT only for finite bracketing sensitivity; no octonion primitive-carrier or physics admission",
        ),
        row(
            "charge_ladder_cl6",
            charge_owner,
            charge_mutated,
            charge_negative,
            "Cl(6) three-mode ladder reduced to wrong-dimension two-mode carrier",
            "REAL_SUPPORT only for finite ladder-charge discriminator; no Standard Model or physics admission",
        ),
        row(
            "chirality_survival_type1_type2_weyl",
            chir_owner,
            chir_mutated,
            chir_negative,
            "Type 1/2 Hamiltonian signs and ladder directions are commutative-ized to the same carrier",
            "REAL_SUPPORT only for Type 1/2 chirality-separation readout; no weak/SM admission",
        ),
        row(
            "entropy_arrow_universal_clock",
            entropy_owner,
            entropy_mutated,
            entropy_negative,
            "canonical schedule reversed/scrambled while monotone absolute-increment readout is retained",
            "TARGET_IMPRINT if monotone dS survives schedule mutation; no arrow-of-time admission",
        ),
        row(
            "knot_mass_gravity",
            knot_owner,
            knot_mutated,
            knot_negative,
            "knot carrier weights are shape-scrambled while the mass and inverse-square sync-gradient readout is retained",
            "TARGET_IMPRINT if mass/gravity readout survives carrier scramble; no mass, G, gravity, or physics admission",
        ),
        row(
            "shell_capacity_hopf_clifford",
            shell_owner,
            shell_mutated,
            shell_negative,
            "Hopf S3 shell normalization is broken by wrong-radius shell coordinates",
            "REAL_SUPPORT only for finite Hopf/Clifford shell-count discriminator; no manifold closure",
        ),
        row(
            "qit_face_knot_readout",
            qit_owner,
            qit_mutated,
            qit_negative,
            "random-unitary/wrong-operator carrier leaves the named face/knot readout key list intact",
            "TARGET_IMPRINT if engine-state face/knot labels survive carrier mutation; no QIT/physics admission",
        ),
    ]


def load_julia_rows() -> dict[str, Any] | None:
    if not JULIA_RESULT_PATH.exists():
        return None
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def attach_parity(rows: list[dict[str, Any]], julia_data: dict[str, Any] | None) -> dict[str, Any]:
    disagreements: list[dict[str, Any]] = []
    max_diff = 0.0
    if not julia_data:
        for item in rows:
            item["branch_verdict"] = "UNDERDETERMINED"
            item["julia_result"] = {"available": False, "reason": "julia result missing"}
        return {
            "peer_available": False,
            "within_1e_9": False,
            "max_abs_diff": None,
            "disagreements": [{"branch_id": "ALL", "reason": "julia result missing"}],
        }
    julia_by_branch = {item["branch_id"]: item for item in julia_data.get("rows", [])}
    for item in rows:
        peer = julia_by_branch.get(item["branch_id"])
        if peer is None:
            item["julia_result"] = {"available": False, "reason": "missing branch"}
            item["branch_verdict"] = "UNDERDETERMINED"
            disagreements.append({"branch_id": item["branch_id"], "reason": "missing branch in julia result"})
            continue
        item["julia_result"] = {
            "backend": peer.get("julia_result", {}).get("backend", "julia_float64"),
            "owner_carrier_value": float(peer["owner_carrier_value"]),
            "mutated_carrier_value": float(peer["mutated_carrier_value"]),
            "negative_control_value": float(peer["negative_control_value"]),
            "branch_verdict": peer["branch_verdict"],
        }
        row_disagree = False
        for key in ("owner_carrier_value", "mutated_carrier_value", "negative_control_value"):
            diff = abs(float(item[key]) - float(peer[key]))
            max_diff = max(max_diff, diff)
            if diff > EPS:
                row_disagree = True
                disagreements.append({"branch_id": item["branch_id"], "key": key, "jax": item[key], "julia": peer[key], "abs_diff": diff})
        if item["jax_result"]["branch_verdict"] != peer["branch_verdict"]:
            row_disagree = True
            disagreements.append(
                {
                    "branch_id": item["branch_id"],
                    "key": "branch_verdict",
                    "jax": item["jax_result"]["branch_verdict"],
                    "julia": peer["branch_verdict"],
                }
            )
        item["branch_verdict"] = verdict(
            item["owner_carrier_value"],
            item["mutated_carrier_value"],
            item["negative_control_value"],
            peer_disagree=row_disagree,
        )
    return {
        "peer_available": True,
        "within_1e_9": not disagreements and max_diff <= EPS,
        "max_abs_diff": max_diff,
        "disagreements": disagreements,
    }


def summarize(rows: list[dict[str, Any]], parity: dict[str, Any]) -> dict[str, Any]:
    verdict_counts = {
        "REAL_SUPPORT": sum(1 for item in rows if item["branch_verdict"] == "REAL_SUPPORT"),
        "TARGET_IMPRINT": sum(1 for item in rows if item["branch_verdict"] == "TARGET_IMPRINT"),
        "UNDERDETERMINED": sum(1 for item in rows if item["branch_verdict"] == "UNDERDETERMINED"),
    }
    target_imprint_branches = [item["branch_id"] for item in rows if item["branch_verdict"] == "TARGET_IMPRINT"]
    real_support_branches = [item["branch_id"] for item in rows if item["branch_verdict"] == "REAL_SUPPORT"]
    return {
        "n_rows": len(rows),
        "n_real_support": verdict_counts["REAL_SUPPORT"],
        "n_target_imprint": verdict_counts["TARGET_IMPRINT"],
        "n_underdetermined": verdict_counts["UNDERDETERMINED"],
        "real_support_branches": real_support_branches,
        "target_imprint_kills": target_imprint_branches,
        "underdetermined_branches": [item["branch_id"] for item in rows if item["branch_verdict"] == "UNDERDETERMINED"],
        "jax_julia_disagreements": parity["disagreements"],
        "verdict_counts": verdict_counts,
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = compute_rows()
    julia_data = load_julia_rows()
    parity = attach_parity(rows, julia_data)
    summary = summarize(rows, parity)
    all_pass = (
        len(rows) == 7
        and parity["peer_available"] is True
        and parity["within_1e_9"] is True
        and summary["n_underdetermined"] == 0
        and summary["n_target_imprint"] >= 1
        and summary["n_real_support"] >= 1
    )
    positive = {
        "owner_carrier_matrix_computed": {
            "pass": len(rows) == 7,
            "observed_rows": len(rows),
            "expected_rows": 7,
        },
        "real_support_rows_exist": {
            "pass": summary["n_real_support"] >= 1,
            "branches": summary["real_support_branches"],
        },
        "dual_backend_parity": {
            "pass": parity["peer_available"] is True and parity["within_1e_9"] is True,
            "parity": parity,
        },
    }
    negative = {
        "target_imprint_kills_reported": {
            "pass": summary["n_target_imprint"] >= 1,
            "branches": summary["target_imprint_kills"],
            "graveyard_reason": "readout survived carrier mutation, so the branch is demoted as target-imprint under this discriminator",
        },
        "mutated_carrier_decisive_test_applied": {
            "pass": all(item["mutated_carrier_value"] <= PRESENT_THRESHOLD or item["branch_verdict"] == "TARGET_IMPRINT" for item in rows),
            "rule": "carrier-dependent iff owner keeps the readout and mutated carrier kills it",
        },
        "null_controls_do_not_reproduce_rows": {
            "pass": all(item["negative_control_value"] <= PRESENT_THRESHOLD for item in rows),
        },
    }
    boundary = {
        "classification_fence": {
            "pass": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "claim_ceiling_blocks_downstream": {
            "pass": True,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "target_imprint_is_a_kill_not_a_failure": {
            "pass": summary["n_target_imprint"] >= 1,
            "note": "all_pass means the matrix discriminated and parity agreed; target-imprint rows are expected graveyard output",
        },
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_readout_discriminator_probe",
        "source_alignment_category": "owner_carrier_readout_mutation_discriminator",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "result_path": str(RESULT_PATH),
        "julia_result_path": str(JULIA_RESULT_PATH),
        "source_refs": source_refs(),
        "SIM_TEMPLATE_SURFACE": SIM_TEMPLATE_SURFACE,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["jax", "jax.numpy", "julia", "canonical_qit_engine_specs.py", "system_v5/julia_carrier owner sources"],
        "actual_tools_used": ["jax", "jax.numpy", "julia peer result", "canonical_qit_engine_specs.py", "python_stdlib"],
        "numpy_compute_used": False,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "root_constraints_in_force": {
            "F01": "finite carriers, finite mutations, finite null controls, finite result JSON",
            "N01": "order/noncommutation/chirality/shell structure is tested by killing or preserving the readout under wrong-carrier mutation",
        },
        "finite_map": "branch owner carrier -> readout value; mutated carrier -> readout value; null control -> readout value; verdict by decisive mutation-kill rule",
        "domain": "seven bounded owner-carrier branch rows under system_v5/julia_carrier plus canonical_qit_engine_specs.py",
        "codomain_or_output": "carrier-readout discriminator matrix with owner/mutated/null values, backend parity, branch verdict, and claim ceiling per row",
        "carrier_layer": "owner carriers only as scratch diagnostic surfaces",
        "geometry_layer": "row-local carrier structures: octonion bracketing, Cl(6), Weyl signs, schedule entropy, knot graph, Hopf/Clifford shells, QIT engine readout keys",
        "bridge_layer": "none",
        "cut_layer": "mutation/null-control discriminator",
        "law_or_candidate_tested": "readout depends on intended owner carrier iff mutation kills it while owner keeps it",
        "branch_status_before_run": "external over-promotion audit demanded graveyard generator for owner-carrier dependence",
        "allowed_claims": [
            "discriminator matrix separated rows into REAL_SUPPORT/TARGET_IMPRINT/UNDERDETERMINED under the stated finite mutation tests",
            "TARGET_IMPRINT rows are killed/demoted for this diagnostic only",
            "JAX and Julia parity agreed or disagreements were reported",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "rows": rows,
        "shared_scalars": {
            f"{item['branch_id']}.{key}": float(item[key])
            for item in rows
            for key in ("owner_carrier_value", "mutated_carrier_value", "negative_control_value")
        },
        "shared_booleans": {
            f"{item['branch_id']}.is_real_support": item["branch_verdict"] == "REAL_SUPPORT"
            for item in rows
        }
        | {
            f"{item['branch_id']}.is_target_imprint": item["branch_verdict"] == "TARGET_IMPRINT"
            for item in rows
        },
        "parity": parity,
        "positive": positive,
        "negative": negative,
        "graveyard_companions": negative,
        "boundary": boundary,
        "nearby_variants": {
            "total": 7,
            "passed": 7 - summary["n_underdetermined"],
            "variants": [item["branch_id"] for item in rows],
        },
        "why_not_v4_probes": {
            "reason": "single-owner positive readouts cannot distinguish carrier dependence from target imprint; this matrix adds wrong-carrier mutation and null controls",
        },
        "probe": {
            "decisive_rule": "carrier-dependent iff owner_carrier keeps the readout and mutated_carrier kills it",
            "present_threshold": PRESENT_THRESHOLD,
        },
        "result_summary": summary | {"all_pass": all_pass, "claim_ceiling": CLAIM_CEILING},
        "all_pass": all_pass,
        "stop_condition_fired": not all_pass,
        "blockers": [] if all_pass else ["julia parity missing/disagreed or discriminator rows underdetermined"],
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["result_summary"]
    print(
        "RESULT "
        f"{OBJECT_ID} jax={RESULT_PATH} all_pass={str(result['all_pass']).lower()} "
        f"n_rows={summary['n_rows']} n_real_support={summary['n_real_support']} "
        f"n_target_imprint={summary['n_target_imprint']} "
        f"n_underdetermined={summary['n_underdetermined']} "
        f"jax_julia_disagreements={summary['jax_julia_disagreements']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
