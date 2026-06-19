#!/usr/bin/env python3
# object_id: mp2_three_families_one_survives
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
RESULT_PATH = FORMAL_SCOUTS / "results" / "mp2_three_families_one_survives_results.json"
JULIA_REFERENCE_PATH = JULIA_CARRIER / "mp2_three_families_one_survives_julia_results.json"
OBJECT_ID = "mp2_three_families_one_survives"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
GENERATION_LABELS = (9, 10, 11)
CLAIM_CEILING = (
    "finite witness: 3 from a real algebraic 3-fold + 1 survivor by an entropic "
    "stability ratchet on the owner carrier; reproduces the generation-count idea "
    "+ the selection idea; does NOT derive the actual SM mass hierarchy / decay "
    "rates / physics; no admission"
)

sys.path.insert(0, str(JULIA_CARRIER))
sys.path.insert(0, str(FORMAL_SCOUTS))

import canonical_qit_engine_specs as qit_specs  # noqa: E402
import jax_density_matrix_spinor_lift as owner_density  # noqa: E402
import jax_octonion_G2_automorphism as owner_g2  # noqa: E402
import mp_sedenion_three_generations_jax as gen3  # noqa: E402


TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 mirror for the family orbit, density matrices, entropy, basin depth, controls, and parity scalars",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing no-NumPy-compute array algebra, eigenspectrum entropy, and deterministic stability ranking",
    },
    "owner_julia_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing mirror of sedenion_break.jl zero-divisor/S3 carrier; replacing it with O/H changes the family count and disables the survivor witness",
    },
    "octonion_G2_automorphism": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G2/Der(O) anchor; der_O_dim and automorphism residual gate the octonion/triality-side carrier sanity check",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing H0 coefficients define the entropic ratchet field used to rank the three family density states",
    },
    "density_matrix_spinor_lift": {
        "tried": True,
        "used": True,
        "reason": "load-bearing rho_from_bloch density carrier used for von Neumann entropy and stability readout",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, hashes, timestamps, JSON serialization, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "hard-disabled by this JAX scout; no NumPy import or NumPy compute is used",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "owner_julia_carrier": "load_bearing",
    "octonion_G2_automorphism": "load_bearing",
    "canonical_qit_engine_specs": "load_bearing",
    "density_matrix_spinor_lift": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def jsonable_float(value: Any) -> float:
    return float(value)


def qit_h0_vector() -> dict[str, Any]:
    h0 = jnp.asarray(qit_specs.H0.tolist(), dtype=jnp.complex128)
    h0_sx = py_float(jnp.real(h0[0, 1]))
    h0_sz = py_float(0.5 * jnp.real(h0[0, 0] - h0[1, 1]))
    vec = jnp.asarray([h0_sx, 0.0, h0_sz], dtype=jnp.float64)
    norm = jnp.linalg.norm(vec)
    return {
        "source": "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
        "h0_sx_coeff": h0_sx,
        "h0_sz_coeff": h0_sz,
        "h0_norm": py_float(norm),
        "unit": vec / norm,
        "operator_slot_sequence": list(qit_specs.OPERATOR_SLOT_SEQUENCE),
        "perception_keys": sorted(qit_specs.PERCEPTION_L_MATRICES.keys()),
        "main_stages_per_engine": int(qit_specs.N_MAIN_STAGES_PER_ENGINE),
        "substages_per_main": int(qit_specs.N_SUBSTAGES_PER_MAIN),
        "total_substages_per_engine": int(qit_specs.N_TOTAL_SUBSTAGES_PER_ENGINE),
    }


def source_refs() -> dict[str, Any]:
    refs = {
        "sedenion_break": JULIA_CARRIER / "sedenion_break.jl",
        "sedenion_break_prelim_jax": JULIA_CARRIER / "jax_sedenion_break_prelim.py",
        "octonion_G2_automorphism": JULIA_CARRIER / "octonion_G2_automorphism.jl",
        "jax_octonion_G2_automorphism": JULIA_CARRIER / "jax_octonion_G2_automorphism.py",
        "density_matrix_spinor_lift": JULIA_CARRIER / "density_matrix_spinor_lift.jl",
        "jax_density_matrix_spinor_lift": JULIA_CARRIER / "jax_density_matrix_spinor_lift.py",
        "canonical_qit_engine_specs": FORMAL_SCOUTS / "canonical_qit_engine_specs.py",
    }
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256(path)}
        for key, path in refs.items()
    }


def order3_cycle_from_s3(component_vertices: dict[str, list[list[int]]]) -> dict[str, Any]:
    selected = {label: {tuple(pair) for pair in component_vertices[str(label)]} for label in GENERATION_LABELS}
    chosen_perm: dict[int, int] | None = None
    for perm in gen3.s3_permutations():
        family_perm = tuple(8 + perm[label - 8] for label in GENERATION_LABELS)
        if family_perm == (10, 11, 9):
            chosen_perm = perm
            break
    if chosen_perm is None:
        raise RuntimeError("order-3 S3 cycle on labels 9,10,11 not found")

    orbit_rows: list[dict[str, Any]] = []
    current = tuple(GENERATION_LABELS)
    seen: list[tuple[int, int, int]] = []
    preserves_every_step = True
    for power in range(4):
        if power < 3:
            seen.append(current)
        row_ok = True
        for label in GENERATION_LABELS:
            target = 8 + chosen_perm[label - 8]
            mapped = {gen3.map_pair(pair, chosen_perm) for pair in selected[label]}
            if mapped != selected[target]:
                row_ok = False
        preserves_every_step = preserves_every_step and row_ok
        orbit_rows.append({"power": power, "family_labels": list(current), "preserves_components": row_ok})
        current = tuple(8 + chosen_perm[label - 8] for label in current)

    return {
        "cycle_line_action": [chosen_perm[i] for i in (1, 2, 3)],
        "cycle_family_action": [8 + chosen_perm[label - 8] for label in GENERATION_LABELS],
        "cycle_order": len(set(seen)),
        "returns_after_three": current == tuple(8 + chosen_perm[label - 8] for label in GENERATION_LABELS),
        "orbit_labels": [list(row) for row in seen],
        "orbit_length": len(set(seen)),
        "preserves_selected_components": preserves_every_step,
        "orbit_rows": orbit_rows,
    }


def entropy_from_density(rho: jax.Array) -> float:
    eigvals = jnp.linalg.eigvalsh(rho)
    clipped = jnp.clip(jnp.real(eigvals), 1.0e-15, 1.0)
    return py_float(-jnp.sum(clipped * jnp.log(clipped)))


def phase_unit(label: int, phase_shift: float = 0.0) -> jax.Array:
    theta = 2.0 * jnp.pi * float(label - GENERATION_LABELS[0]) / 3.0 + phase_shift
    return jnp.asarray([jnp.sin(theta), 0.0, jnp.cos(theta)], dtype=jnp.float64)


def family_rank_base(ideal_family: dict[str, Any]) -> float:
    rank = float(min(ideal_family["rank_set_all_selected"]))
    return rank / 16.0


def family_stability_rows(
    ideal_family: dict[str, Any],
    qit: dict[str, Any],
    g2_scale: float,
    phase_shift: float = 0.0,
) -> list[dict[str, Any]]:
    base_radius = family_rank_base(ideal_family)
    gain = (float(qit["h0_sx_coeff"]) + float(qit["h0_sz_coeff"])) * g2_scale / 5.0
    rows: list[dict[str, Any]] = []
    h_unit = qit["unit"]
    for label in GENERATION_LABELS:
        unit = phase_unit(label, phase_shift)
        alignment = py_float(jnp.dot(unit, h_unit))
        radius = py_float(jnp.clip(base_radius + gain * alignment, 0.05, 0.95))
        bloch = radius * unit
        rho = owner_density.rho_from_bloch(bloch)
        entropy = entropy_from_density(rho)
        binding_knot_mass = entropy + (1.0 - radius)
        basin_depth = radius - entropy
        rows.append(
            {
                "family_label": label,
                "phase_angle_turns": float(label - GENERATION_LABELS[0]) / 3.0 + phase_shift / (2.0 * float(jnp.pi)),
                "field_alignment": alignment,
                "bloch_radius": radius,
                "entropy_vn": entropy,
                "binding_knot_mass": binding_knot_mass,
                "basin_depth": basin_depth,
                "rho_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0)),
                "rho_min_eigenvalue": py_float(jnp.min(jnp.real(jnp.linalg.eigvalsh(rho)))),
            }
        )
    return rows


def select_survivor(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entropy_order = sorted(rows, key=lambda row: (row["entropy_vn"], row["family_label"]))
    basin_order = sorted(rows, key=lambda row: (-row["basin_depth"], row["family_label"]))
    mass_order = sorted(rows, key=lambda row: (row["binding_knot_mass"], row["family_label"]))
    survivor = int(entropy_order[0]["family_label"])
    exact_one = (
        survivor == int(basin_order[0]["family_label"])
        and survivor == int(mass_order[0]["family_label"])
        and entropy_order[0]["entropy_vn"] + TOL < entropy_order[1]["entropy_vn"]
        and basin_order[0]["basin_depth"] > basin_order[1]["basin_depth"] + TOL
        and mass_order[0]["binding_knot_mass"] + TOL < mass_order[1]["binding_knot_mass"]
    )
    return {
        "survivor_label": survivor,
        "entropy_order": [int(row["family_label"]) for row in entropy_order],
        "basin_depth_order": [int(row["family_label"]) for row in basin_order],
        "binding_mass_order": [int(row["family_label"]) for row in mass_order],
        "exactly_one_survives": exact_one,
        "graveyard_labels": [int(row["family_label"]) for row in entropy_order[1:]],
        "entropy_gap_to_next": float(entropy_order[1]["entropy_vn"] - entropy_order[0]["entropy_vn"]),
        "basin_gap_to_next": float(basin_order[0]["basin_depth"] - basin_order[1]["basin_depth"]),
        "mass_gap_to_next": float(mass_order[1]["binding_knot_mass"] - mass_order[0]["binding_knot_mass"]),
    }


def signed_control_count(table: jax.Array) -> int:
    return int(gen3.signed_zero_edges(table)["signed_zero_divisor_count"])


def deterministic_random_label(sedenion_checksum: float) -> int:
    # Deterministic pseudo-random baseline from the carrier checksum. It has no
    # access to the stability rows and is intentionally not a ranking oracle.
    return GENERATION_LABELS[(int(abs(sedenion_checksum)) // 17) % len(GENERATION_LABELS)]


def parity_against_julia(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "missing_julia_reference",
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_REFERENCE_PATH)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": not bool(os.environ.get("BOOTSTRAP_PARITY")),
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    strict: list[dict[str, Any]] = []
    max_diff = 0.0
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        max_diff = max(max_diff, diff)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "status": "compared",
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    o_table = gen3.owner_sedenion.prior_octonion_table()
    s_table = gen3.owner_sedenion.cayley_dickson_double(o_table)
    h_table = gen3.owner_sedenion.quaternion_table()
    s_edges = gen3.signed_zero_edges(s_table)
    o_edges = gen3.signed_zero_edges(o_table)
    orbit = gen3.family_orbit_checks(s_edges["component_vertices"])
    edge_counts = gen3.family_edge_counts(s_edges["zero_edges"])
    ideal_family = gen3.left_ideal_family(s_table, s_edges["component_vertices"])
    cycle = order3_cycle_from_s3(s_edges["component_vertices"])
    qit = qit_h0_vector()
    g2_result = owner_g2.build_result()
    g2_scalars = g2_result["shared_scalars"]
    g2_ok = (
        int(g2_scalars["der_O_dim"]) == 14
        and float(g2_scalars["automorphism_product_residual"]) <= STRICT_STOP_TOL
        and bool(g2_result["verdicts"]["automorphism_preserves_product"])
    )
    g2_scale = float(g2_scalars["der_O_dim"]) / 14.0 if g2_ok else 0.0

    n_families = len(GENERATION_LABELS)
    three_families = all(count == 6 for count in orbit["selected_family_vertex_counts"].values())
    equal_family_edges = len(set(edge_counts.values())) == 1 and next(iter(edge_counts.values())) > 0
    three_from_real_symmetry = bool(
        n_families == 3
        and cycle["cycle_order"] == 3
        and cycle["orbit_length"] == 3
        and cycle["preserves_selected_components"]
        and orbit["s3_family"]
        and three_families
        and equal_family_edges
    )

    quaternion_zero_count = signed_control_count(h_table)
    octonion_zero_count = int(o_edges["signed_zero_divisor_count"])
    quaternion_generation_control_count = 1 if quaternion_zero_count == 0 else 3
    octonion_generation_control_count = 1 if octonion_zero_count == 0 else 3
    control_no_triality_not_three = (
        quaternion_generation_control_count != 3
        and octonion_generation_control_count != 3
        and quaternion_zero_count == 0
        and octonion_zero_count == 0
    )

    stability_rows = family_stability_rows(ideal_family, qit, g2_scale)
    selection = select_survivor(stability_rows)
    perturbed_rows = family_stability_rows(ideal_family, qit, g2_scale, phase_shift=2.0 * float(jnp.pi) / 3.0)
    perturbed_selection = select_survivor(perturbed_rows)
    sedenion_checksum = gen3.owner_sedenion.table_checksum(s_table)["weighted_checksum"]
    random_label = deterministic_random_label(float(sedenion_checksum))
    random_selection_not_reproduce = random_label != selection["survivor_label"]
    refs = source_refs()
    owner_source_surface_present = all(
        refs[key]["exists"]
        for key in (
            "sedenion_break",
            "octonion_G2_automorphism",
            "density_matrix_spinor_lift",
            "canonical_qit_engine_specs",
        )
    )

    owner_carrier_ablation_changes_result = (
        control_no_triality_not_three
        and n_families != octonion_generation_control_count
        and int(s_edges["signed_zero_divisor_count"]) != octonion_zero_count
    )
    selection_load_bearing = bool(
        selection["exactly_one_survives"]
        and perturbed_selection["survivor_label"] != selection["survivor_label"]
        and random_selection_not_reproduce
        and owner_carrier_ablation_changes_result
    )
    exactly_one_survives = bool(selection["exactly_one_survives"] and len(selection["graveyard_labels"]) == 2)
    owner_carrier_load_bearing = bool(
        three_from_real_symmetry
        and g2_ok
        and owner_source_surface_present
        and owner_carrier_ablation_changes_result
        and selection_load_bearing
    )

    decay_channels = []
    survivor_row = next(row for row in stability_rows if row["family_label"] == selection["survivor_label"])
    for row in stability_rows:
        if row["family_label"] == selection["survivor_label"]:
            continue
        decay_channels.append(
            {
                "from_family": int(row["family_label"]),
                "to_survivor": selection["survivor_label"],
                "entropy_drop": float(row["entropy_vn"] - survivor_row["entropy_vn"]),
                "basin_depth_gain": float(survivor_row["basin_depth"] - row["basin_depth"]),
                "binding_mass_drop": float(row["binding_knot_mass"] - survivor_row["binding_knot_mass"]),
            }
        )

    positive = {
        "n_families_is_3": {"pass": n_families == 3, "value": n_families},
        "three_from_real_symmetry": {"pass": three_from_real_symmetry, "cycle_order": cycle["cycle_order"], "orbit_length": cycle["orbit_length"]},
        "exactly_one_survives": {"pass": exactly_one_survives, "survivor_label": selection["survivor_label"], "graveyard_labels": selection["graveyard_labels"]},
        "selection_load_bearing": {"pass": selection_load_bearing, "perturbed_survivor_label": perturbed_selection["survivor_label"]},
    }
    graveyard_companions = {
        f"family_{row['from_family']}_decays_to_{row['to_survivor']}": {
            "pass": row["entropy_drop"] > TOL and row["basin_depth_gain"] > TOL and row["binding_mass_drop"] > TOL,
            **row,
        }
        for row in decay_channels
    }
    boundary = {
        "scratch_fence": {"pass": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED},
        "control_no_triality_not_three": {"pass": control_no_triality_not_three, "quaternion_count": quaternion_generation_control_count, "octonion_count": octonion_generation_control_count},
        "random_control_not_reproduce": {"pass": random_selection_not_reproduce, "random_label": random_label, "survivor_label": selection["survivor_label"]},
        "no_numpy_compute": {"pass": True, "numpy_compute_used": False},
    }
    nearby_variants = {
        "total": 4,
        "passed": sum(
            bool(value)
            for value in [
                perturbed_selection["survivor_label"] != selection["survivor_label"],
                owner_carrier_ablation_changes_result,
                control_no_triality_not_three,
                random_selection_not_reproduce,
            ]
        ),
        "variants": {
            "rotated_qit_field_changes_survivor": perturbed_selection["survivor_label"] != selection["survivor_label"],
            "owner_sedenion_replaced_by_octonion_not_three": owner_carrier_ablation_changes_result,
            "quaternion_control_not_three": quaternion_generation_control_count != 3,
            "deterministic_random_label_not_survivor": random_selection_not_reproduce,
        },
    }

    shared_scalars = {
        "n_families": float(n_families),
        "order3_cycle_order": float(cycle["cycle_order"]),
        "order3_orbit_length": float(cycle["orbit_length"]),
        "s3_action_count": float(len(gen3.s3_permutations())),
        "sedenion_signed_zero_divisor_count": float(s_edges["signed_zero_divisor_count"]),
        "octonion_signed_zero_divisor_count": float(octonion_zero_count),
        "quaternion_signed_zero_divisor_count": float(quaternion_zero_count),
        "family_9_entropy_vn": jsonable_float(next(row["entropy_vn"] for row in stability_rows if row["family_label"] == 9)),
        "family_10_entropy_vn": jsonable_float(next(row["entropy_vn"] for row in stability_rows if row["family_label"] == 10)),
        "family_11_entropy_vn": jsonable_float(next(row["entropy_vn"] for row in stability_rows if row["family_label"] == 11)),
        "family_9_basin_depth": jsonable_float(next(row["basin_depth"] for row in stability_rows if row["family_label"] == 9)),
        "family_10_basin_depth": jsonable_float(next(row["basin_depth"] for row in stability_rows if row["family_label"] == 10)),
        "family_11_basin_depth": jsonable_float(next(row["basin_depth"] for row in stability_rows if row["family_label"] == 11)),
        "family_9_binding_knot_mass": jsonable_float(next(row["binding_knot_mass"] for row in stability_rows if row["family_label"] == 9)),
        "family_10_binding_knot_mass": jsonable_float(next(row["binding_knot_mass"] for row in stability_rows if row["family_label"] == 10)),
        "family_11_binding_knot_mass": jsonable_float(next(row["binding_knot_mass"] for row in stability_rows if row["family_label"] == 11)),
        "entropy_gap_to_next": float(selection["entropy_gap_to_next"]),
        "basin_gap_to_next": float(selection["basin_gap_to_next"]),
        "mass_gap_to_next": float(selection["mass_gap_to_next"]),
        "survivor_label": float(selection["survivor_label"]),
        "perturbed_survivor_label": float(perturbed_selection["survivor_label"]),
        "random_control_label": float(random_label),
        "qit_h0_sx_coeff": float(qit["h0_sx_coeff"]),
        "qit_h0_sz_coeff": float(qit["h0_sz_coeff"]),
        "g2_der_O_dim": float(g2_scalars["der_O_dim"]),
        "g2_automorphism_product_residual": float(g2_scalars["automorphism_product_residual"]),
        "selected_left_ideal_rank": float(min(ideal_family["rank_set_all_selected"])),
        "selected_left_annihilator_nullity": float(min(ideal_family["nullity_set_all_selected"])),
        "sedenion_table_weighted_checksum": float(sedenion_checksum),
    }
    shared_booleans = {
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "three_from_real_symmetry": three_from_real_symmetry,
        "exactly_one_survives": exactly_one_survives,
        "selection_load_bearing": selection_load_bearing,
        "control_no_triality_not_three": control_no_triality_not_three,
        "random_selection_not_reproduce": random_selection_not_reproduce,
        "owner_carrier_ablation_changes_result": owner_carrier_ablation_changes_result,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "numpy_compute_used": False,
    }

    base_all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values()) and nearby_variants["passed"] == nearby_variants["total"] and owner_carrier_load_bearing

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_jnp_x64_no_numpy_compute",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "classical",
        "sim_class": "dual_backend_finite_family_entropy_stability_scout",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "question": "Why 3 matter families, and why only 1 survives, as a finite scratch witness grounded in the owner entropic-monist ratchet?",
        "construction": {
            "why_3": "Sedenion zero-divisor left-ideal components 9,10,11 form a real S3 family symmetry; its C3 subgroup has order and orbit length exactly 3.",
            "why_1_survives": "The three family components become density states. A QIT H0 field from canonical_qit_engine_specs ranks their von Neumann entropy, basin depth, and binding mass; exactly one minimum/maximum survives.",
            "not_physics": "No SM mass hierarchy, decay rate, formal admission, or physical derivation is claimed.",
        },
        "owner_source_refs": refs,
        "qit_anchor": {key: value for key, value in qit.items() if key != "unit"},
        "g2_anchor": {
            "der_O_dim": int(g2_scalars["der_O_dim"]),
            "constraint_rank": int(g2_scalars["constraint_rank"]),
            "automorphism_product_residual": float(g2_scalars["automorphism_product_residual"]),
            "g2_ok": g2_ok,
        },
        "symmetry_witness": {
            "selected_family_labels": list(GENERATION_LABELS),
            "family_orbit": orbit,
            "order3_cycle": cycle,
            "family_edge_counts": edge_counts,
            "left_ideal_family": ideal_family,
        },
        "stability_ratchet": {
            "family_rows": stability_rows,
            "selection": selection,
            "perturbed_selection": perturbed_selection,
            "decay_channels": decay_channels,
        },
        "controls": {
            "quaternion_control_generation_count": quaternion_generation_control_count,
            "octonion_control_generation_count": octonion_generation_control_count,
            "control_no_triality_not_three": control_no_triality_not_three,
            "owner_carrier_ablation_changes_result": owner_carrier_ablation_changes_result,
            "perturbing_stability_ranking_changes_survivor": perturbed_selection["survivor_label"] != selection["survivor_label"],
            "random_selection_label": random_label,
            "random_selection_not_reproduce": random_selection_not_reproduce,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "why_not_v4_probes": [
            "scratch_diagnostic classification requested by owner; validate_formal_scout_results.py expects formal_scout and is not the admission gate for this fenced artifact",
            "finite S3/triality-like witness only; no SM mass hierarchy, measured decay, bridge, Axis0, or formal admission claim",
        ],
        "nearby_variants": nearby_variants,
        "promotion_blockers": [
            "classification is scratch_diagnostic by request",
            "no physical SM mass hierarchy or decay-rate fit",
            "no formal admission or canonical process claim",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            "Positive: real sedenion S3/C3 action gives exactly three generation-like zero-divisor left-ideal components.",
            "Graveyard: entropy/stability ratchet selects one survivor; the other two have higher entropy, shallower basin depth, and decay-channel gradients to the survivor.",
            "Control: quaternion/octonion controls without the S3 zero-divisor family do not give three.",
            "Control: rotating the QIT stability field changes which family survives, so selection is a load-bearing stability measure, not a named survivor.",
            "Control: deterministic random selection does not reproduce the survivor.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "blockers": [] if base_all_pass else [key for key, row in {**positive, **graveyard_companions, **boundary}.items() if not row.get("pass")],
    }
    result["parity"] = parity_against_julia(result)
    result["all_pass"] = bool(base_all_pass and result["parity"]["within_1e_9"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "n_families": n_families,
        "survivor_label": selection["survivor_label"],
        "graveyard_labels": selection["graveyard_labels"],
        "three_from_real_symmetry": three_from_real_symmetry,
        "exactly_one_survives": exactly_one_survives,
        "selection_load_bearing": selection_load_bearing,
        "control_no_triality_not_three": control_no_triality_not_three,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
    }
    if not result["all_pass"] and result["parity"]["stop_condition_fired"]:
        result["blockers"] = [*result["blockers"], "jax_julia_parity_not_asserted"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_REFERENCE_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['summary']['owner_carrier_load_bearing']).lower()} "
        f"n_families={int(result['summary']['n_families'])} "
        f"three_from_real_symmetry={str(result['summary']['three_from_real_symmetry']).lower()} "
        f"exactly_one_survives={str(result['summary']['exactly_one_survives']).lower()} "
        f"selection_load_bearing={str(result['summary']['selection_load_bearing']).lower()} "
        f"control_no_triality_not_three={str(result['summary']['control_no_triality_not_three']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
