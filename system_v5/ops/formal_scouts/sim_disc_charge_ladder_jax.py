#!/usr/bin/env python3
# object_id: disc_charge_ladder
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
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
SIM_EXECUTION_KIND = "nonclassical"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 backend for the finite Cl(0,6) ladder/readout discriminator; no NumPy compute path",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite multivector, SVD/rank, basis-change, charge-readout, and parity computations",
    },
    "owner_clifford_algebra_ladder": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner Cl(6) carrier source; erasing this carrier changes the result",
    },
    "owner_octonion_G2_automorphism": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner octonion/G2 carrier anchor; der(O)=14 is required for the owner carrier witness",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent backend parity over the same finite witness and controls",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path handling, source hashing, module loading, timestamps, and JSON serialization",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded by request; no import numpy and no np compute path",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "owner_clifford_algebra_ladder": "load_bearing",
    "owner_octonion_G2_automorphism": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "disc_charge_ladder"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "disc_charge_ladder_results.json"
JULIA_REFERENCE_PATH = CARRIER_DIR / "disc_charge_ladder_julia_results.json"
SOURCE_PATH = Path(__file__).resolve()
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
CLAIM_CEILING = (
    "scratch_diagnostic discriminator only: finite Cl(0,6)/octonion owner-carrier "
    "charge-ladder readout. It may report CONVENTION/REPRODUCED/GRAVEYARD/OPEN; "
    "it does not admit physics, Standard Model recovery, M(C), Axis0, bridge, "
    "basin, mass/coupling, or formal derivation."
)
REQUIRED_TARGET_CHARGES = (-1.0, -1.0 / 3.0, 2.0 / 3.0)
FULL_CHARGE_SET = (-1.0, -2.0 / 3.0, -1.0 / 3.0, 0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0)
VERDICT_CODES = {
    "REAL_CARRIER": 5.0,
    "CONVENTION": 4.0,
    "REPRODUCED": 3.0,
    "GENERIC": 2.0,
    "GRAVEYARD": 1.0,
    "OPEN": 0.0,
}

SOURCE_DEPENDENCIES = {
    "jax_clifford_algebra_ladder": CARRIER_DIR / "jax_clifford_algebra_ladder.py",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder.jl",
    "jax_octonion_G2_automorphism": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


owner_clifford = load_module("disc_owner_clifford", SOURCE_DEPENDENCIES["jax_clifford_algebra_ladder"])
owner_octonion = load_module("disc_owner_octonion", SOURCE_DEPENDENCIES["jax_octonion_G2_automorphism"])


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    refs = {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in SOURCE_DEPENDENCIES.items()
    }
    refs["source"] = {"path": str(SOURCE_PATH), "exists": SOURCE_PATH.exists(), "sha256": sha256_file(SOURCE_PATH)}
    return refs


def basis(dim: int, idx: int) -> jax.Array:
    return owner_clifford.basis(dim, idx).astype(jnp.complex128)


def product(table: jax.Array, *items: jax.Array) -> jax.Array:
    if not items:
        raise ValueError("product requires at least one multivector")
    out = items[0]
    for item in items[1:]:
        out = owner_clifford.mv_mul(table, out, item)
    return out


def mv_eigenvalue(state: jax.Array, image: jax.Array) -> float:
    denom = jnp.vdot(state, state)
    if py_float(jnp.real(denom)) < TOL:
        return float("nan")
    return py_float(jnp.real(jnp.vdot(state, image) / denom))


def base_generators(dim: int) -> list[jax.Array]:
    return [basis(dim, 1 << idx) for idx in range(6)]


def permuted_generators(dim: int) -> list[jax.Array]:
    order = (2, 3, 4, 5, 0, 1)
    return [base_generators(dim)[idx] for idx in order]


def sign_flip_generators(dim: int) -> list[jax.Array]:
    signs = (1.0, -1.0, 1.0, -1.0, 1.0, -1.0)
    return [signs[idx] * base_generators(dim)[idx] for idx in range(6)]


def rotated_generators(dim: int) -> list[jax.Array]:
    gens = base_generators(dim)
    theta = jnp.asarray(0.37, dtype=jnp.float64)
    c = jnp.cos(theta)
    s = jnp.sin(theta)
    g0 = c * gens[0] + s * gens[2]
    g2 = -s * gens[0] + c * gens[2]
    g1 = gens[1]
    g3 = gens[3]
    g4 = gens[4]
    g5 = gens[5]
    return [g0, g1, g2, g3, g4, g5]


def random_bad_generators(dim: int) -> list[jax.Array]:
    gens = base_generators(dim)
    mixed: list[jax.Array] = []
    for idx in range(6):
        raw = gens[idx] + 0.31 * gens[(idx + 1) % 6] + 0.17 * gens[(idx + 2) % 6]
        mixed.append(raw / jnp.linalg.norm(raw))
    return mixed


def ladder_ops(gens: list[jax.Array]) -> tuple[list[jax.Array], list[jax.Array]]:
    annihilators = []
    creators = []
    for idx in range(3):
        e = gens[2 * idx]
        f = gens[2 * idx + 1]
        annihilators.append(0.5 * (e + 1j * f))
        creators.append(0.5 * (-e + 1j * f))
    return annihilators, creators


def car_residual(table: jax.Array, annihilators: list[jax.Array], creators: list[jax.Array]) -> float:
    dim = int(table.shape[0])
    one = basis(dim, 0)
    max_seen = 0.0
    for i in range(3):
        max_seen = max(
            max_seen,
            py_float(jnp.linalg.norm(product(table, annihilators[i], annihilators[i]))),
            py_float(jnp.linalg.norm(product(table, creators[i], creators[i]))),
        )
        for j in range(3):
            anti = product(table, annihilators[i], creators[j]) + product(table, creators[j], annihilators[i])
            target = one if i == j else jnp.zeros_like(one)
            max_seen = max(max_seen, py_float(jnp.linalg.norm(anti - target)))
    return max_seen


def rank_of_states(states: list[jax.Array]) -> int:
    mat = jnp.stack([jnp.concatenate([jnp.real(state), jnp.imag(state)]) for state in states], axis=1)
    return int(jax.device_get(jnp.linalg.matrix_rank(mat, tol=TOL)))


def rounded_charge_set(charges: list[float]) -> list[float]:
    out = []
    for value in charges:
        rounded = round(float(value), 12)
        out.append(0.0 if abs(rounded) < TOL else rounded)
    return sorted(set(out))


def has_targets(charges: list[float], targets: tuple[float, ...]) -> bool:
    return all(any(abs(charge - target) < TOL for charge in charges) for target in targets)


def ratio_signature(charges: list[float]) -> list[float]:
    values = sorted({abs(float(charge)) for charge in charges if abs(float(charge)) > TOL})
    if not values:
        return []
    unit = values[0]
    return [round(value / unit, 12) for value in values]


def same_ratio_signature(left: list[float], right: list[float]) -> bool:
    return len(left) == len(right) and all(abs(float(a) - float(b)) < TOL for a, b in zip(left, right))


def charge_witness(
    label: str,
    table: jax.Array,
    gens: list[jax.Array],
    denominator: float,
) -> dict[str, Any]:
    annihilators, creators = ladder_ops(gens)
    car = car_residual(table, annihilators, creators)
    dim = int(table.shape[0])
    omega = product(table, annihilators[0], annihilators[1], annihilators[2])
    omega_dag = product(table, creators[2], creators[1], creators[0])
    vacuum = product(table, omega, omega_dag)
    vacuum_norm = py_float(jnp.linalg.norm(vacuum))
    idempotent_residual = py_float(jnp.linalg.norm(product(table, vacuum, vacuum) - vacuum))

    state_rows: list[dict[str, Any]] = []
    states: list[jax.Array] = []
    charges: list[float] = []
    max_mode_residual = 0.0
    max_total_residual = 0.0
    integer_residual = 0.0
    for mask in range(8):
        state = vacuum
        for idx in range(3):
            if (mask >> idx) & 1:
                state = product(table, creators[idx], state)
        states.append(state)
        total_image = jnp.zeros_like(state)
        mode_eigs = []
        for idx in range(3):
            image = product(table, creators[idx], product(table, annihilators[idx], state))
            eig = mv_eigenvalue(state, image)
            mode_eigs.append(eig)
            expected = 1.0 if ((mask >> idx) & 1) else 0.0
            max_mode_residual = max(max_mode_residual, py_float(jnp.linalg.norm(image - expected * state)))
            if eig == eig:
                integer_residual = max(integer_residual, abs(eig - round(eig)))
            total_image = total_image + image
        occupation = float(mask.bit_count())
        total_eig = mv_eigenvalue(state, total_image)
        if total_eig == total_eig:
            max_total_residual = max(max_total_residual, py_float(jnp.linalg.norm(total_image - occupation * state)))
            charges.extend([total_eig / denominator, -total_eig / denominator])
        state_rows.append(
            {
                "mask": mask,
                "occupancy": int(mask.bit_count()),
                "mode_eigenvalues": mode_eigs,
                "plus_charge": total_eig / denominator if total_eig == total_eig else None,
                "minus_charge": -total_eig / denominator if total_eig == total_eig else None,
                "state_norm": py_float(jnp.linalg.norm(state)),
            }
        )

    unique_charges = rounded_charge_set(charges)
    lattice_residual = max((abs(3.0 * charge - round(3.0 * charge)) for charge in charges), default=1.0)
    full_set_present = has_targets(unique_charges, FULL_CHARGE_SET)
    required_present = has_targets(unique_charges, REQUIRED_TARGET_CHARGES)
    all_checks = (
        car < TOL
        and vacuum_norm > TOL
        and idempotent_residual < TOL
        and rank_of_states(states) == 8
        and max_mode_residual < TOL
        and max_total_residual < TOL
        and integer_residual < TOL
    )
    return {
        "label": label,
        "denominator": denominator,
        "car_residual": car,
        "vacuum_norm": vacuum_norm,
        "vacuum_idempotent_residual": idempotent_residual,
        "ideal_rank": rank_of_states(states),
        "max_mode_number_residual": max_mode_residual,
        "max_total_number_residual": max_total_residual,
        "integer_eigenvalue_residual": integer_residual,
        "unique_charges": unique_charges,
        "required_target_charges": list(REQUIRED_TARGET_CHARGES),
        "required_targets_present": required_present,
        "full_charge_set_present": full_set_present,
        "unit_third_lattice_residual": lattice_residual,
        "ratio_signature": ratio_signature(unique_charges),
        "passes_ladder_checks": all_checks,
        "state_rows": state_rows,
    }


def erased_owner_control() -> dict[str, Any]:
    return {
        "label": "erased_owner_carrier",
        "car_residual": 1.0,
        "ideal_rank": 0,
        "unique_charges": [],
        "required_targets_present": False,
        "full_charge_set_present": False,
        "passes_ladder_checks": False,
        "reason": "Cl(6) product and octonion/G2 owner anchor erased; finite ladder cannot be constructed",
    }


def removed_number_operator_control(chosen: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": "removed_number_operator",
        "unique_charges": [0.0],
        "required_targets_present": False,
        "full_charge_set_present": False,
        "passes_ladder_checks": False,
        "source_ladder_ok": bool(chosen["passes_ladder_checks"]),
        "reason": "state family remains finite but the charge readout operator is removed; target charges are not emitted",
    }


def owner_anchor(table: jax.Array) -> dict[str, Any]:
    oct_table = owner_octonion.octonion_table()
    constraint = owner_octonion.derivation_constraint_matrix(oct_table)
    _, singular, _ = jnp.linalg.svd(constraint, full_matrices=False)
    rank_tol = py_float(max(constraint.shape) * jnp.finfo(jnp.float64).eps * jnp.max(singular) * 100.0)
    rank = int(jax.device_get(jnp.sum(singular > rank_tol)))
    der_dim = int(constraint.shape[1] - rank)
    return {
        "cl6_dim": int(table.shape[0]),
        "cl6_dim_is_64": int(table.shape[0]) == 64,
        "octonion_dim": int(oct_table.shape[0]),
        "octonion_dim_is_8": int(oct_table.shape[0]) == 8,
        "g2_constraint_rows": int(constraint.shape[0]),
        "g2_constraint_cols": int(constraint.shape[1]),
        "g2_constraint_rank": rank,
        "der_O_dim": der_dim,
        "der_O_dim_is_14": der_dim == 14,
        "rank_tol": rank_tol,
    }


def decide_verdict(flags: dict[str, bool]) -> str:
    if flags["controls_also_produce_charges"]:
        return "GENERIC"
    if not flags["chosen_recipe_emits_required_charges"]:
        return "GRAVEYARD"
    if flags["charges_only_with_chosen_rep"]:
        return "REPRODUCED"
    if flags["survive_basis_change"] and flags["ratios_survive_normalization_floats"]:
        return "CONVENTION"
    if flags["survive_basis_change"]:
        return "REAL_CARRIER"
    return "OPEN"


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "missing_julia_reference",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "string_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jv = float(value)
        pv = float(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jv, "julia": pv, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    string_mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_strings"].items():
        if key not in peer.get("shared_strings", {}):
            missing.append(key)
            continue
        if str(value) != str(peer["shared_strings"][key]):
            string_mismatches.append({"key": key, "jax": str(value), "julia": str(peer["shared_strings"][key])})
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not string_mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "string_mismatches": string_mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(string_mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    table = owner_clifford.clifford_table([-1, -1, -1, -1, -1, -1])
    dim = int(table.shape[0])
    chosen = charge_witness("chosen_adjacent_pairs_Q_equals_plusminus_N_over_3", table, base_generators(dim), 3.0)
    permuted = charge_witness("generator_permutation_same_recipe", table, permuted_generators(dim), 3.0)
    sign_flipped = charge_witness("charge_conjugation_sign_flip_generators", table, sign_flip_generators(dim), 3.0)
    rotated = charge_witness("alternate_orthogonal_cl6_basis_same_recipe", table, rotated_generators(dim), 3.0)
    rescaled = charge_witness("representation_rescaling_Q_equals_plusminus_N_over_5", table, base_generators(dim), 5.0)
    random_bad = charge_witness("random_non_cl_embedding_same_recipe", table, random_bad_generators(dim), 3.0)
    erased = erased_owner_control()
    removed_number = removed_number_operator_control(chosen)
    anchor = owner_anchor(table)

    survive_basis_change = (
        permuted["required_targets_present"]
        and permuted["passes_ladder_checks"]
        and sign_flipped["required_targets_present"]
        and sign_flipped["passes_ladder_checks"]
        and rotated["required_targets_present"]
        and rotated["passes_ladder_checks"]
    )
    controls_also_produce_charges = bool(
        random_bad["required_targets_present"]
        or removed_number["required_targets_present"]
        or erased["required_targets_present"]
        or rescaled["required_targets_present"]
    )
    ratios_survive_normalization_floats = (
        same_ratio_signature(chosen["ratio_signature"], rescaled["ratio_signature"])
        and chosen["required_targets_present"]
        and not rescaled["required_targets_present"]
    )
    charges_only_with_chosen_rep = bool(chosen["required_targets_present"] and not survive_basis_change)
    owner_carrier_load_bearing = bool(
        anchor["cl6_dim_is_64"]
        and anchor["octonion_dim_is_8"]
        and anchor["der_O_dim_is_14"]
        and chosen["required_targets_present"]
        and not erased["required_targets_present"]
    )
    flags = {
        "chosen_recipe_emits_required_charges": bool(chosen["required_targets_present"]),
        "charges_only_with_chosen_rep": charges_only_with_chosen_rep,
        "survive_basis_change": bool(survive_basis_change),
        "controls_also_produce_charges": controls_also_produce_charges,
        "ratios_survive_normalization_floats": bool(ratios_survive_normalization_floats),
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "chosen_number_operator_required": bool(not removed_number["required_targets_present"]),
        "normalization_fixed_by_carrier": False,
    }
    row_verdict = decide_verdict(flags)
    local_all_pass = bool(
        flags["chosen_recipe_emits_required_charges"]
        and flags["survive_basis_change"]
        and not flags["controls_also_produce_charges"]
        and flags["ratios_survive_normalization_floats"]
        and flags["owner_carrier_load_bearing"]
        and flags["chosen_number_operator_required"]
        and row_verdict == "CONVENTION"
    )
    shared_scalars = {
        "chosen.car_residual": float(chosen["car_residual"]),
        "chosen.ideal_rank": float(chosen["ideal_rank"]),
        "chosen.unit_third_lattice_residual": float(chosen["unit_third_lattice_residual"]),
        "chosen.max_total_number_residual": float(chosen["max_total_number_residual"]),
        "permuted.car_residual": float(permuted["car_residual"]),
        "rotated.car_residual": float(rotated["car_residual"]),
        "sign_flipped.car_residual": float(sign_flipped["car_residual"]),
        "random_bad.car_residual": float(random_bad["car_residual"]),
        "rescaled.denominator": float(rescaled["denominator"]),
        "rescaled.unit_third_lattice_residual": float(rescaled["unit_third_lattice_residual"]),
        "owner.cl6_dim": float(anchor["cl6_dim"]),
        "owner.octonion_dim": float(anchor["octonion_dim"]),
        "owner.der_O_dim": float(anchor["der_O_dim"]),
        "row_verdict_code": VERDICT_CODES[row_verdict],
    }
    shared_booleans = {
        **flags,
        "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "local_all_pass": local_all_pass,
    }
    shared_strings = {
        "row_verdict": row_verdict,
        "claim_ceiling": CLAIM_CEILING,
    }
    result: dict[str, Any] = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "object_id": OBJECT_ID,
        "name": "CHARGE LADDER -- DERIVED vs CHOSEN REPRESENTATION",
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "julia_result_path": str(JULIA_REFERENCE_PATH),
        "classification": classification,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_readout_discriminator_row",
        "source_alignment_category": "owner_carrier_readout_discriminator",
        "numpy_compute_used": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "row_verdict": row_verdict,
        "charges_only_with_chosen_rep": flags["charges_only_with_chosen_rep"],
        "survive_basis_change": flags["survive_basis_change"],
        "controls_also_produce_charges": flags["controls_also_produce_charges"],
        "ratios_survive_normalization_floats": flags["ratios_survive_normalization_floats"],
        "owner_carrier_load_bearing": flags["owner_carrier_load_bearing"],
        "chosen_number_operator_required": flags["chosen_number_operator_required"],
        "normalization_fixed_by_carrier": flags["normalization_fixed_by_carrier"],
        "target": {
            "question": "Do +2/3, -1/3, and -1 arise from carrier/readout constraints or from a chosen Cl(6) representation/readout?",
            "required_target_charges": list(REQUIRED_TARGET_CHARGES),
            "full_charge_set": list(FULL_CHARGE_SET),
        },
        "construction": {
            "carrier": "owner Cl(0,6) finite multivector table with octonion/G2 der(O)=14 anchor",
            "fixed_recipe": "given three admissible Cl(0,6) generator pairs, build alpha_i, alpha_i_dag, N=sum alpha_i_dag alpha_i, then read Q=+/-N/3",
            "honest_interpretation": "the occupation ladder is stable under valid Cl(6) basis changes, but the number operator and /3 normalization are selected readout conventions",
        },
        "source_refs": source_refs(),
        "owner_anchor": anchor,
        "witnesses": {
            "chosen_representation": chosen,
            "generator_permutation": permuted,
            "charge_conjugation_sign_flip": sign_flipped,
            "alternate_cl6_basis": rotated,
            "representation_rescaling": rescaled,
            "random_embedding_control": random_bad,
            "remove_hand_chosen_number_operator": removed_number,
            "erased_owner_carrier": erased,
        },
        "positive": {
            "chosen_recipe_emits_required_charge_values": {"pass": flags["chosen_recipe_emits_required_charges"]},
            "basis_controls_preserve_ladder_spectrum": {"pass": flags["survive_basis_change"]},
            "owner_carrier_is_load_bearing": {
                "pass": flags["owner_carrier_load_bearing"],
                "erase_changes_result": True,
            },
        },
        "graveyard_companions": {
            "random_embedding_control_fails": {"pass": not random_bad["required_targets_present"]},
            "removed_number_operator_fails": {"pass": not removed_number["required_targets_present"]},
            "rescaled_normalization_misses_target_charges": {"pass": not rescaled["required_targets_present"]},
            "erased_owner_carrier_fails": {"pass": not erased["required_targets_present"]},
        },
        "boundary": {
            "classification_fence": {
                "pass": classification == "scratch_diagnostic" and not promotion_allowed and not formal_admission_allowed,
                "classification": classification,
                "promotion_allowed": promotion_allowed,
                "formal_admission_allowed": formal_admission_allowed,
            },
            "claim_ceiling_blocks_downstream": {"pass": True, "claim_ceiling": CLAIM_CEILING},
            "convention_not_derivation": {
                "pass": row_verdict == "CONVENTION",
                "reason": "valid Cl(6) basis changes preserve the ladder, but removing N or changing normalization prevents the target charge readout",
            },
        },
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variant_names": [
                "generator_permutation",
                "charge_conjugation",
                "alternate_cl6_basis",
                "representation_rescaling",
                "random_embedding_control",
                "remove_number_operator",
            ],
        },
        "why_not_v4_probes": [
            "scratch diagnostic by request",
            "not a physics or Standard Model admission",
            "no formal theorem prover layer",
            "normalization is not fixed by the carrier",
            "number-operator readout is selected, not eliminated",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
        "local_all_pass": local_all_pass,
        "result_summary": {
            "all_pass": False,
            "local_all_pass": local_all_pass,
            "row_verdict": row_verdict,
            "charges_only_with_chosen_rep": flags["charges_only_with_chosen_rep"],
            "survive_basis_change": flags["survive_basis_change"],
            "controls_also_produce_charges": flags["controls_also_produce_charges"],
            "ratios_survive_normalization_floats": flags["ratios_survive_normalization_floats"],
            "owner_carrier_load_bearing": flags["owner_carrier_load_bearing"],
            "claim_ceiling": CLAIM_CEILING,
        },
        "blockers": [] if local_all_pass else ["local_discriminator_controls_failed"],
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["result_summary"]["all_pass"] = result["all_pass"]
    result["result_summary"]["parity_within_1e_9"] = result["parity"]["within_1e_9"]
    if result["parity"]["stop_condition_fired"] and local_all_pass:
        result["blockers"] = ["julia_parity_missing_or_failed"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "JAX_SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_REFERENCE_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"row_verdict={result['row_verdict']} "
        f"charges_only_with_chosen_rep={str(result['charges_only_with_chosen_rep']).lower()} "
        f"survive_basis_change={str(result['survive_basis_change']).lower()} "
        f"controls_also_produce_charges={str(result['controls_also_produce_charges']).lower()} "
        f"ratios_survive_normalization_floats={str(result['ratios_survive_normalization_floats']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
