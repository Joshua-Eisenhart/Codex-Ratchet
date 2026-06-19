#!/usr/bin/env python3
"""First finite M(C) admissibility packet.

Scratch diagnostic only. This builds the finite admissibility object named in
the terrain ledger:

    C = {F01, N01, admissible probe rules, admissible composition rules}
    M(C) = {x : x is admissible under C}

The concrete owner carrier is used as load-bearing evidence for finite
normalization, density reduction, Hopf-sheet readouts, and Pauli order
sensitivity. It is mapped into M(C); it is not equated with M(C).
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "mc_first_admissibility_packet"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_first_admissibility_packet_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/mc_first_admissibility_packet_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

classification = "scratch_diagnostic"
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
CLASSIFICATION = classification

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite carrier construction, density lift, Pauli order gaps, quotient, controls, and parity scalars",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinor, density, projection, and finite reduction operations; no NumPy source path is used",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, paths, timestamps, and peer-result parity loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "hard-disabled for this JAX packet; no NumPy import or NumPy computation is used",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}

CLAIM_CEILING = (
    "first finite M(C) admissibility packet; NOT a physics bridge, NOT Axis0, "
    "NOT a QIT engine, NOT final M(C) admission"
)

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.array([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def finite_round(value: float, digits: int = 12) -> float:
    return round(float(value), digits)


def spinor_from_hopf(eta: float, phi: float, chi: float, phase: float, scale: float) -> jax.Array:
    psi = jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )
    return scale * jnp.exp(1j * phase) * psi


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return jnp.array(
        [
            jnp.real(jnp.trace(rho @ SX)),
            jnp.real(jnp.trace(rho @ SY)),
            jnp.real(jnp.trace(rho @ SZ)),
        ],
        dtype=jnp.float64,
    )


def operators(order_word: str) -> tuple[jax.Array, jax.Array]:
    if order_word == "XY":
        return SX, SY
    if order_word == "YX":
        return SY, SX
    if order_word == "XX":
        return SX, SX
    raise ValueError(f"unknown order_word: {order_word}")


def project_to_unit(psi: jax.Array) -> jax.Array:
    norm = jnp.linalg.norm(psi)
    return jnp.where(norm > TOL, psi / norm, psi)


def candidate_specs() -> list[dict[str, Any]]:
    eta_core = py_float(jnp.pi / 4.0)
    eta_offset = py_float(jnp.pi / 6.0)
    return [
        {
            "id": "L_core_XY",
            "sheet": "L",
            "eta_index": 1,
            "eta": eta_core,
            "phi": 0.0,
            "chi": 0.0,
            "phase": 0.0,
            "scale": 1.0,
            "order_word": "XY",
            "finite_encoding": True,
            "composition_projection_enabled": True,
            "role": "positive_phase_representative",
        },
        {
            "id": "L_core_XY_phase_pi",
            "sheet": "L",
            "eta_index": 1,
            "eta": eta_core,
            "phi": 0.0,
            "chi": 0.0,
            "phase": py_float(jnp.pi),
            "scale": 1.0,
            "order_word": "XY",
            "finite_encoding": True,
            "composition_projection_enabled": True,
            "role": "positive_density_equivalent_phase",
        },
        {
            "id": "R_core_XY",
            "sheet": "R",
            "eta_index": 1,
            "eta": eta_core,
            "phi": 0.0,
            "chi": 0.0,
            "phase": 0.0,
            "scale": 1.0,
            "order_word": "XY",
            "finite_encoding": True,
            "composition_projection_enabled": True,
            "role": "positive_other_sheet",
        },
        {
            "id": "R_core_XY_phase_pi",
            "sheet": "R",
            "eta_index": 1,
            "eta": eta_core,
            "phi": 0.0,
            "chi": 0.0,
            "phase": py_float(jnp.pi),
            "scale": 1.0,
            "order_word": "XY",
            "finite_encoding": True,
            "composition_projection_enabled": True,
            "role": "positive_other_sheet_density_equivalent_phase",
        },
        {
            "id": "L_eta2_YX",
            "sheet": "L",
            "eta_index": 2,
            "eta": eta_offset,
            "phi": 0.0,
            "chi": 0.0,
            "phase": 0.0,
            "scale": 1.0,
            "order_word": "YX",
            "finite_encoding": True,
            "composition_projection_enabled": True,
            "role": "positive_order_orientation_variant",
        },
        {
            "id": "commutative_XX_control",
            "sheet": "L",
            "eta_index": 1,
            "eta": eta_core,
            "phi": 0.0,
            "chi": 0.0,
            "phase": 0.0,
            "scale": 1.0,
            "order_word": "XX",
            "finite_encoding": True,
            "composition_projection_enabled": True,
            "role": "graveyard_N01_commutative",
        },
        {
            "id": "composition_projection_missing_control",
            "sheet": "L",
            "eta_index": 2,
            "eta": eta_offset,
            "phi": 0.0,
            "chi": 0.0,
            "phase": 0.0,
            "scale": 1.0,
            "order_word": "XY",
            "finite_encoding": True,
            "composition_projection_enabled": False,
            "role": "graveyard_composition_rule",
        },
        {
            "id": "nonfinite_global_coordinate_control",
            "sheet": "L",
            "eta_index": 1,
            "eta": eta_core,
            "phi": 0.0,
            "chi": 0.0,
            "phase": 0.0,
            "scale": 1.0,
            "order_word": "XY",
            "finite_encoding": False,
            "composition_projection_enabled": True,
            "role": "graveyard_F01_nonfinite_encoding",
        },
        {
            "id": "unnormalized_spinor_control",
            "sheet": "R",
            "eta_index": 2,
            "eta": eta_offset,
            "phi": 0.0,
            "chi": 0.0,
            "phase": 0.0,
            "scale": 2.0,
            "order_word": "XY",
            "finite_encoding": True,
            "composition_projection_enabled": True,
            "role": "graveyard_F01_probe_norm",
        },
    ]


def analyze_candidate(spec: dict[str, Any]) -> dict[str, Any]:
    psi = spinor_from_hopf(spec["eta"], spec["phi"], spec["chi"], spec["phase"], spec["scale"])
    rho = density(psi)
    bloch = bloch_from_rho(rho)
    a_op, b_op = operators(spec["order_word"])
    left = a_op @ (b_op @ psi)
    right = b_op @ (a_op @ psi)
    projected_left = project_to_unit(left)
    order_delta = left - right
    spinor_norm = py_float(jnp.real(jnp.vdot(psi, psi)))
    trace_rho = py_float(jnp.real(jnp.trace(rho)))
    order_gap = py_float(jnp.linalg.norm(order_delta))
    order_orientation = py_float(jnp.imag(jnp.vdot(psi, order_delta)))
    projected_norm_residual = py_float(jnp.abs(jnp.real(jnp.vdot(projected_left, projected_left)) - 1.0))
    density_phase_blind_key = (
        finite_round(py_float(bloch[0]), 12),
        finite_round(py_float(bloch[1]), 12),
        finite_round(py_float(bloch[2]), 12),
    )
    finite_probe_outputs = {
        "sheet": spec["sheet"],
        "eta_index": int(spec["eta_index"]),
        "rho_bloch": list(density_phase_blind_key),
        "order_word": spec["order_word"],
        "order_gap_bin": int(order_gap > TOL),
        "order_orientation_sign": 1 if order_orientation > TOL else (-1 if order_orientation < -TOL else 0),
        "composition_projected": bool(spec["composition_projection_enabled"]),
    }
    f01_pass = bool(
        spec["finite_encoding"]
        and abs(spinor_norm - 1.0) <= TOL
        and abs(trace_rho - 1.0) <= TOL
        and py_bool(jnp.all(jnp.isfinite(jnp.real(psi))))
        and py_bool(jnp.all(jnp.isfinite(jnp.imag(psi))))
    )
    n01_pass = bool(order_gap > TOL)
    probe_rules_pass = bool(
        abs(spinor_norm - 1.0) <= TOL
        and abs(trace_rho - 1.0) <= TOL
        and all(abs(v) <= 1.0 + TOL for v in density_phase_blind_key)
    )
    composition_rules_pass = bool(spec["composition_projection_enabled"] and projected_norm_residual <= TOL)
    adm = f01_pass and n01_pass and probe_rules_pass and composition_rules_pass
    fail_reasons = []
    if not f01_pass:
        fail_reasons.append("F01_FINITUDE")
    if not n01_pass:
        fail_reasons.append("N01_NONCOMMUTATION")
    if not probe_rules_pass:
        fail_reasons.append("admissible_probe_rules")
    if not composition_rules_pass:
        fail_reasons.append("admissible_composition_rules")
    return {
        "id": spec["id"],
        "role": spec["role"],
        "sheet": spec["sheet"],
        "eta_index": int(spec["eta_index"]),
        "order_word": spec["order_word"],
        "finite_encoding": bool(spec["finite_encoding"]),
        "spinor_components": [
            [finite_round(py_float(jnp.real(psi[0])), 15), finite_round(py_float(jnp.imag(psi[0])), 15)],
            [finite_round(py_float(jnp.real(psi[1])), 15), finite_round(py_float(jnp.imag(psi[1])), 15)],
        ],
        "density_matrix": [
            [
                [finite_round(py_float(jnp.real(rho[0, 0])), 15), finite_round(py_float(jnp.imag(rho[0, 0])), 15)],
                [finite_round(py_float(jnp.real(rho[0, 1])), 15), finite_round(py_float(jnp.imag(rho[0, 1])), 15)],
            ],
            [
                [finite_round(py_float(jnp.real(rho[1, 0])), 15), finite_round(py_float(jnp.imag(rho[1, 0])), 15)],
                [finite_round(py_float(jnp.real(rho[1, 1])), 15), finite_round(py_float(jnp.imag(rho[1, 1])), 15)],
            ],
        ],
        "bloch": [finite_round(py_float(bloch[0]), 15), finite_round(py_float(bloch[1]), 15), finite_round(py_float(bloch[2]), 15)],
        "checks": {
            "spinor_norm": spinor_norm,
            "trace_rho": trace_rho,
            "order_gap": order_gap,
            "order_orientation": order_orientation,
            "projected_norm_residual": projected_norm_residual,
        },
        "finite_probe_outputs": finite_probe_outputs,
        "constraint_checks": {
            "F01_FINITUDE": f01_pass,
            "N01_NONCOMMUTATION": n01_pass,
            "admissible_probe_rules": probe_rules_pass,
            "admissible_composition_rules": composition_rules_pass,
        },
        "Adm_C": adm,
        "fail_reasons": fail_reasons,
    }


def quotient(candidates: list[dict[str, Any]], probe_names: list[str]) -> dict[str, Any]:
    classes: dict[str, list[str]] = {}
    signatures: dict[str, dict[str, Any]] = {}
    for row in candidates:
        probes = row["finite_probe_outputs"]
        signature = {name: probes[name] for name in probe_names}
        key = json.dumps(signature, sort_keys=True, separators=(",", ":"))
        classes.setdefault(key, []).append(row["id"])
        signatures[key] = signature
    ordered = [
        {"class_id": f"q{idx}", "members": sorted(members), "signature": signatures[key]}
        for idx, (key, members) in enumerate(sorted(classes.items()))
    ]
    return {
        "probe_names": probe_names,
        "class_count": len(ordered),
        "classes": ordered,
    }


def adjacency(classes: list[dict[str, Any]]) -> dict[str, Any]:
    edges = []
    for i, left in enumerate(classes):
        for j in range(i + 1, len(classes)):
            right = classes[j]
            differing = [
                key
                for key in left["signature"]
                if left["signature"].get(key) != right["signature"].get(key)
            ]
            if len(differing) == 1:
                edges.append(
                    {
                        "source": left["class_id"],
                        "target": right["class_id"],
                        "reason": f"one_probe_refinement_difference:{differing[0]}",
                    }
                )
    return {
        "rule": "coordinate-free finite compatibility adjacency: one finite probe refinement differs; no metric, time, or global coordinates",
        "edge_count": len(edges),
        "edges": edges,
    }


def admissible_under(row: dict[str, Any], erase: str | None = None) -> bool:
    checks = dict(row["constraint_checks"])
    if erase is not None:
        checks[erase] = True
    return all(bool(value) for value in checks.values())


def na_basin_report() -> dict[str, Any]:
    rows = {
        "R": {"finite": True, "order_sensitive": False, "assoc": True, "na_allowed": False, "norm_ok": True},
        "C": {"finite": True, "order_sensitive": False, "assoc": True, "na_allowed": False, "norm_ok": True},
        "H": {"finite": True, "order_sensitive": True, "assoc": True, "na_allowed": False, "norm_ok": True},
        "M2C": {"finite": True, "order_sensitive": True, "assoc": True, "na_allowed": False, "norm_ok": True},
        "O": {"finite": True, "order_sensitive": True, "assoc": False, "na_allowed": True, "norm_ok": True},
        "J3O": {"finite": True, "order_sensitive": True, "assoc": False, "na_allowed": True, "norm_ok": True},
        "S": {"finite": True, "order_sensitive": True, "assoc": False, "na_allowed": True, "norm_ok": False},
    }

    def basin(allow_na: bool) -> list[str]:
        out = []
        for name, row in rows.items():
            survives = row["finite"] and row["order_sensitive"] and row["norm_ok"] and (row["assoc"] or (allow_na and row["na_allowed"]))
            if survives:
                out.append(name)
        return out

    base = basin(False)
    with_na = basin(True)
    return {
        "status": "candidate_third_constraint_fenced",
        "basis": "finite predicate table mirroring documented B2/B3 repaired basin readout; no M(C+NA) admission",
        "basin_F01_N01": base,
        "basin_F01_N01_NA": with_na,
        "NA_changes_basin": base != with_na,
        "sedenion_excluded_by_norm_not_associativity": "S" not in with_na and rows["S"]["na_allowed"] and not rows["S"]["norm_ok"],
        "predicate_rows": rows,
        "claim_ceiling": "candidate third constraint only; promotion_allowed=false and formal_admission_allowed=false",
    }


def geometry_erased_control(candidates: list[dict[str, Any]], admissible_ids: list[str]) -> dict[str, Any]:
    erased_admissible = [
        row["id"]
        for row in candidates
        if row["finite_encoding"] and row["constraint_checks"]["admissible_composition_rules"]
    ]
    return {
        "rule": "erase psi/rho/Hopf carrier data and keep only finite labels plus composition flag",
        "erased_admissible_ids": erased_admissible,
        "actual_admissible_ids": admissible_ids,
        "reproduces_admissibility_readout": erased_admissible == admissible_ids,
        "pass": erased_admissible != admissible_ids,
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "missing_julia_reference",
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_REFERENCE_PATH)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    rows = []
    max_diff = 0.0
    max_key = None
    strict = []
    missing = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer["shared_scalars"][key]))
        rows.append({"key": key, "jax": float(value), "julia": float(peer["shared_scalars"][key]), "abs_diff": diff})
        if diff > max_diff:
            max_diff = diff
            max_key = key
        if diff > STRICT_STOP_TOL:
            strict.append(rows[-1])
    mismatches = []
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
        "max_diff_key": max_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict or mismatches or missing),
    }


def build_packet() -> dict[str, Any]:
    all_candidates = [analyze_candidate(spec) for spec in candidate_specs()]
    admissible = [row for row in all_candidates if row["Adm_C"]]
    admissible_ids = [row["id"] for row in admissible]
    active_probe_family = ["sheet", "eta_index", "rho_bloch", "order_word", "order_gap_bin", "order_orientation_sign"]
    quotient_active = quotient(admissible, active_probe_family)
    quotient_drop_sheet = quotient(admissible, [name for name in active_probe_family if name != "sheet"])
    quotient_drop_order = quotient(admissible, [name for name in active_probe_family if name != "order_orientation_sign"])

    f01_erased = [row["id"] for row in all_candidates if admissible_under(row, "F01_FINITUDE")]
    n01_erased = [row["id"] for row in all_candidates if admissible_under(row, "N01_NONCOMMUTATION")]
    geom_control = geometry_erased_control(all_candidates, admissible_ids)
    na_report = na_basin_report()

    adm_c_nontrivial = len(quotient_active["classes"]) < len(admissible) and len(admissible) < len(all_candidates)
    f01_load_bearing = f01_erased != admissible_ids
    n01_load_bearing = n01_erased != admissible_ids
    probe_load_bearing = quotient_drop_sheet["class_count"] != quotient_active["class_count"]
    owner_carrier_load_bearing = bool(geom_control["pass"])

    axes = {}
    class_by_member = {
        member: cls["class_id"]
        for cls in quotient_active["classes"]
        for member in cls["members"]
    }
    degree_by_class = {cls["class_id"]: 0 for cls in quotient_active["classes"]}
    adj = adjacency(quotient_active["classes"])
    for edge in adj["edges"]:
        degree_by_class[edge["source"]] += 1
        degree_by_class[edge["target"]] += 1
    for row in admissible:
        class_id = class_by_member[row["id"]]
        rz = row["bloch"][2]
        axes[row["id"]] = {
            "quotient_class": class_id,
            "A0_finite_density_z_sign": "positive" if rz > TOL else ("negative" if rz < -TOL else "zero"),
            "A1_sheet": row["sheet"],
            "A2_eta_bin": row["eta_index"],
            "A3_order_word": row["order_word"],
            "A4_probe_equivalence_class_size": len(next(cls["members"] for cls in quotient_active["classes"] if cls["class_id"] == class_id)),
            "A5_adjacency_degree": degree_by_class[class_id],
            "A6_order_orientation_sign": row["finite_probe_outputs"]["order_orientation_sign"],
        }

    shared_scalars = {
        "S_size": float(len(all_candidates)),
        "admissible_count": float(len(admissible)),
        "excluded_count": float(len(all_candidates) - len(admissible)),
        "quotient_class_count": float(quotient_active["class_count"]),
        "quotient_drop_sheet_class_count": float(quotient_drop_sheet["class_count"]),
        "quotient_drop_order_orientation_class_count": float(quotient_drop_order["class_count"]),
        "f01_erased_admissible_count": float(len(f01_erased)),
        "n01_erased_admissible_count": float(len(n01_erased)),
        "adjacency_edge_count": float(adj["edge_count"]),
        "na_base_basin_count": float(len(na_report["basin_F01_N01"])),
        "na_extended_basin_count": float(len(na_report["basin_F01_N01_NA"])),
    }
    for row in all_candidates:
        prefix = f"candidate.{row['id']}"
        shared_scalars[f"{prefix}.spinor_norm"] = float(row["checks"]["spinor_norm"])
        shared_scalars[f"{prefix}.trace_rho"] = float(row["checks"]["trace_rho"])
        shared_scalars[f"{prefix}.order_gap"] = float(row["checks"]["order_gap"])
        shared_scalars[f"{prefix}.projected_norm_residual"] = float(row["checks"]["projected_norm_residual"])

    shared_booleans = {
        "all_13_elements_present": True,
        "adm_c_nontrivial": adm_c_nontrivial,
        "F01_load_bearing": f01_load_bearing,
        "N01_load_bearing": n01_load_bearing,
        "probe_load_bearing": probe_load_bearing,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "geometry_erased_control_pass": bool(geom_control["pass"]),
        "NA_changes_basin": bool(na_report["NA_changes_basin"]),
        "sedenion_excluded_by_norm_not_associativity": bool(na_report["sedenion_excluded_by_norm_not_associativity"]),
    }
    for row in all_candidates:
        shared_booleans[f"candidate.{row['id']}.Adm_C"] = bool(row["Adm_C"])
        for key, value in row["constraint_checks"].items():
            shared_booleans[f"candidate.{row['id']}.{key}"] = bool(value)

    elements_13 = {
        "1_finite_carrier_S": {
            "description": "finite support set of concrete owner-carrier records plus explicit graveyard controls",
            "size": len(all_candidates),
            "candidate_ids": [row["id"] for row in all_candidates],
        },
        "2_active_constraint_set_C": {
            "C": ["F01_FINITUDE", "N01_NONCOMMUTATION", "admissible_probe_rules", "admissible_composition_rules"],
        },
        "3_admissibility_predicate_Adm_C": {
            "computed": True,
            "admissible_ids": admissible_ids,
            "excluded": {row["id"]: row["fail_reasons"] for row in all_candidates if not row["Adm_C"]},
        },
        "4_finite_probe_family_M": {"probe_names": active_probe_family},
        "5_quotient_S_mod_M": quotient_active,
        "6_order_sensitive_composition_N01": {
            "operator_algebra": "Pauli X/Y noncommuting order on finite spinor carrier",
            "commutative_control": "commutative_XX_control",
        },
        "7_neighborhood_adjacency": adj,
        "8_candidate_carrier_geometry_and_iota": {
            "status": "candidate realization mapped into M(C), not equal to M(C)",
            "carrier": "finite samples from S_s^3 sheets with density rho=psi psi^dagger and Hopf torus eta bins",
            "iota": {row["id"]: class_by_member[row["id"]] for row in admissible},
        },
        "9_readout_map": {
            "preserves": ["sheet", "eta_index", "density/Bloch finite bin", "order word", "order orientation"],
            "loses": ["global spinor phase under density quotient; L_core_XY and L_core_XY_phase_pi are probe-equivalent"],
        },
        "10_axes_A_i": axes,
        "11_negative_controls_graveyards": {
            "F01_erased": f01_erased,
            "N01_erased": n01_erased,
            "probe_drop_sheet": quotient_drop_sheet,
            "geometry_erased_control": geom_control,
            "commutative_control": "commutative_XX_control excluded by N01",
            "composition_control": "composition_projection_missing_control excluded by composition rule",
        },
        "12_evidence_handles": {
            "source_docs": [
                "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/TERRAIN_MATH_LEDGER_v1.md:23-47,265",
                "system_v4/docs/ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md:92-124,348-383",
                "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints.md:114-130",
                "system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:3,21-37,108-127,178-190",
                "user-provided doc-grounded M(C) spec for missing constraint-manifold-architecture.md clauses",
            ],
            "jax_source": str(Path(__file__).resolve()),
            "jax_result": str(RESULT_PATH),
            "julia_result": str(JULIA_REFERENCE_PATH),
        },
        "13_claim_ceiling": CLAIM_CEILING,
    }

    all_13_elements_present = len(elements_13) == 13 and all(elements_13.values())
    shared_booleans["all_13_elements_present"] = all_13_elements_present
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": classification,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "nonclassical",
        "sim_class": "constraint_admissibility_packet",
        "root_constraints_in_force": ["F01_FINITUDE", "N01_NONCOMMUTATION"],
        "carrier_layer": "finite owner-carrier samples from S_s^3 sheets with density lift",
        "geometry_layer": "candidate realization mapped into M(C); coordinate-free adjacency is probe-compatibility only",
        "bridge_layer": "none",
        "cut_layer": "none",
        "allowed_claims": [CLAIM_CEILING],
        "promotion_blockers": [
            "scratch_diagnostic classification",
            "promotion_allowed=false",
            "formal_admission_allowed=false",
            "finite packet only; no final M(C), Axis0, QIT-engine, bridge, or physics admission",
        ],
        "required_tools": ["JAX", "jax.numpy"],
        "actual_tools_used": ["JAX", "jax.numpy", "Python stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_negatives": [
            "F01 erased",
            "N01 erased",
            "probe dropped",
            "geometry erased",
            "commutative control",
            "composition projection missing",
            "NA candidate basin compare",
        ],
        "negatives_run": True,
        "kill_conditions": [
            "Adm_C trivial",
            "F01 or N01 erasure leaves admissible set unchanged",
            "dropping a load-bearing probe leaves quotient unchanged",
            "geometry-erased control reproduces admissibility readout",
            "JAX/Julia parity exceeds 1e-9",
        ],
        "elements_13": elements_13,
        "finite_carrier_rows": all_candidates,
        "M_C": {
            "definition": "M(C) = {x : x is admissible under C}",
            "admissible_ids": admissible_ids,
            "quotient": quotient_active,
        },
        "controls": {
            "F01_erased_admissible_ids": f01_erased,
            "N01_erased_admissible_ids": n01_erased,
            "probe_drop_sheet": quotient_drop_sheet,
            "probe_drop_order_orientation": quotient_drop_order,
            "geometry_erased": geom_control,
        },
        "nonassociativity_candidate": na_report,
        "positive": {
            "all_13_elements_present": {"pass": all_13_elements_present},
            "Adm_C_nontrivial": {"pass": adm_c_nontrivial},
            "owner_carrier_load_bearing": {"pass": owner_carrier_load_bearing},
        },
        "graveyard_companions": {
            "F01_erasure_changes_admissible_set": {"pass": f01_load_bearing, "erased_ids": f01_erased},
            "N01_erasure_changes_admissible_set": {"pass": n01_load_bearing, "erased_ids": n01_erased},
            "probe_drop_changes_quotient": {"pass": probe_load_bearing},
            "geometry_erased_does_not_reproduce": {"pass": bool(geom_control["pass"])},
        },
        "boundary": {
            "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
            "promotion_allowed_false": True,
            "formal_admission_allowed_false": True,
            "NA_changes_basin": bool(na_report["NA_changes_basin"]),
        },
        "nearby_variants": {
            "total": 4,
            "passed": int(f01_load_bearing) + int(n01_load_bearing) + int(probe_load_bearing) + int(owner_carrier_load_bearing),
            "variants": ["F01_erased", "N01_erased", "probe_drop_sheet", "geometry_erased"],
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic finite M(C) packet with dual-backend parity; it intentionally does not use v4 promotion language.",
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
    }
    result["parity"] = parity_against_peer(result)
    result["all_13_elements_present"] = all_13_elements_present
    result["adm_c_nontrivial"] = adm_c_nontrivial
    result["F01_load_bearing"] = f01_load_bearing
    result["N01_load_bearing"] = n01_load_bearing
    result["probe_load_bearing"] = probe_load_bearing
    result["owner_carrier_load_bearing"] = owner_carrier_load_bearing
    result["NA_changes_basin"] = bool(na_report["NA_changes_basin"])
    result["all_pass"] = bool(
        all_13_elements_present
        and adm_c_nontrivial
        and f01_load_bearing
        and n01_load_bearing
        and probe_load_bearing
        and owner_carrier_load_bearing
        and na_report["NA_changes_basin"]
        and result["parity"]["within_1e_9"]
    )
    result["stop_condition_fired"] = not result["all_pass"]
    return result


def print_summary(result: dict[str, Any]) -> None:
    print("mc_first_admissibility_packet - JAX")
    print(
        "all_pass={all_pass} all_13={all_13} adm_c_nontrivial={adm} "
        "F01_load_bearing={f01} N01_load_bearing={n01} probe_load_bearing={probe} "
        "owner_carrier_load_bearing={carrier} NA_changes_basin={na}".format(
            all_pass=str(result["all_pass"]).lower(),
            all_13=str(result["all_13_elements_present"]).lower(),
            adm=str(result["adm_c_nontrivial"]).lower(),
            f01=str(result["F01_load_bearing"]).lower(),
            n01=str(result["N01_load_bearing"]).lower(),
            probe=str(result["probe_load_bearing"]).lower(),
            carrier=str(result["owner_carrier_load_bearing"]).lower(),
            na=str(result["NA_changes_basin"]).lower(),
        )
    )
    print(
        "parity_status={status} parity_max_diff={diff} within_1e-9={within}".format(
            status=result["parity"]["status"],
            diff=result["parity"]["parity_max_diff"],
            within=str(result["parity"]["within_1e_9"]).lower(),
        )
    )
    print(f"wrote: {result['result_path']}")


def main() -> int:
    result = build_packet()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
