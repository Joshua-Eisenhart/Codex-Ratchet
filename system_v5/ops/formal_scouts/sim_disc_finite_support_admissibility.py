#!/usr/bin/env python3
"""Finite-support / state-on-algebra manifold-layer discriminator.

Scratch diagnostic only. This row reloads the owner
``mc_first_admissibility_packet`` carrier and recomputes a finite
state-on-algebra admissibility predicate from the carrier rows. It asks whether
the admissible set and quotient really depend on F01 finitude, N01
noncommutation, and the finite probe family.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "disc_finite_support_admissibility"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_CARRIER_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_first_admissibility_packet_results.json"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/disc_finite_support_admissibility_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/disc_finite_support_admissibility_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "nonclassical"
SIM_EXECUTION_KIND = sim_execution_kind

CLAIM_CEILING = (
    "finite-support/state-on-algebra base-layer discriminator only; "
    "promotion=false, formal_admission=false; no final M(C), manifold closure, "
    "Axis0, bridge, engine, or physics claim"
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 recomputation of owner carrier density, F01, N01, quotient, controls, and parity scalars",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex state-on-algebra operations over finite carrier rows; no NumPy source path is used",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, paths, timestamps, and peer-result parity loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "hard-disabled for this JAX lane; no NumPy import or NumPy computation is used",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}

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


def complex_from_pair(pair: list[float]) -> complex:
    return complex(float(pair[0]), float(pair[1]))


def operators(order_word: str) -> tuple[jax.Array, jax.Array]:
    if order_word == "XY":
        return SX, SY
    if order_word == "YX":
        return SY, SX
    if order_word == "XX":
        return SX, SX
    raise ValueError(f"unknown order_word: {order_word}")


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return jnp.array(
        [
            jnp.real(jnp.trace(rho @ SX)),
            jnp.real(jnp.trace(rho @ SY)),
            jnp.real(jnp.trace(rho @ SZ)),
        ],
        dtype=jnp.float64,
    )


def load_owner_carrier() -> dict[str, Any]:
    data = json.loads(SOURCE_CARRIER_PATH.read_text(encoding="utf-8"))
    rows = data.get("finite_carrier_rows") or []
    if not rows:
        raise RuntimeError(f"missing finite_carrier_rows in {SOURCE_CARRIER_PATH}")
    return data


def recompute_row(row: dict[str, Any]) -> dict[str, Any]:
    psi = jnp.asarray([complex_from_pair(pair) for pair in row["spinor_components"]], dtype=jnp.complex128)
    rho = jnp.outer(psi, jnp.conj(psi))
    bloch = bloch_from_rho(rho)
    a_op, b_op = operators(str(row["order_word"]))
    left = a_op @ (b_op @ psi)
    right = b_op @ (a_op @ psi)
    delta = left - right
    spinor_norm = py_float(jnp.real(jnp.vdot(psi, psi)))
    trace_rho = py_float(jnp.real(jnp.trace(rho)))
    order_gap = py_float(jnp.linalg.norm(delta))
    order_orientation = py_float(jnp.imag(jnp.vdot(psi, delta)))
    all_finite = py_bool(jnp.all(jnp.isfinite(jnp.real(psi)))) and py_bool(jnp.all(jnp.isfinite(jnp.imag(psi))))
    bloch_tuple = (
        finite_round(py_float(bloch[0]), 12),
        finite_round(py_float(bloch[1]), 12),
        finite_round(py_float(bloch[2]), 12),
    )
    probes = dict(row["finite_probe_outputs"])
    order_sign = 1 if order_orientation > TOL else (-1 if order_orientation < -TOL else 0)
    computed_probe_outputs = {
        "sheet": str(row["sheet"]),
        "eta_index": int(row["eta_index"]),
        "rho_bloch": list(bloch_tuple),
        "order_word": str(row["order_word"]),
        "order_gap_bin": int(order_gap > TOL),
        "order_orientation_sign": order_sign,
        "composition_projected": bool(probes["composition_projected"]),
        "support_kind": "finite_support" if bool(row["finite_encoding"]) else "continuous_or_nonfinite_proxy",
    }
    f01_pass = bool(row["finite_encoding"]) and abs(spinor_norm - 1.0) <= TOL and abs(trace_rho - 1.0) <= TOL and all_finite
    n01_pass = order_gap > TOL
    probe_rules_pass = (
        abs(spinor_norm - 1.0) <= TOL
        and abs(trace_rho - 1.0) <= TOL
        and all(abs(value) <= 1.0 + TOL for value in bloch_tuple)
        and computed_probe_outputs["sheet"] in {"L", "R"}
        and computed_probe_outputs["eta_index"] in {1, 2}
        and computed_probe_outputs["order_word"] in {"XY", "YX", "XX"}
    )
    composition_rules_pass = bool(probes["composition_projected"])
    adm_c = f01_pass and n01_pass and probe_rules_pass and composition_rules_pass
    fail_reasons = []
    if not f01_pass:
        fail_reasons.append("F01_FINITUDE")
    if not n01_pass:
        fail_reasons.append("N01_NONCOMMUTATION")
    if not probe_rules_pass:
        fail_reasons.append("state_on_algebra_probe_rules")
    if not composition_rules_pass:
        fail_reasons.append("composition_rules")
    return {
        "id": str(row["id"]),
        "role": str(row["role"]),
        "support_kind": computed_probe_outputs["support_kind"],
        "finite_probe_outputs": computed_probe_outputs,
        "checks": {
            "spinor_norm": spinor_norm,
            "trace_rho": trace_rho,
            "order_gap": order_gap,
            "order_orientation": order_orientation,
            "bloch": list(bloch_tuple),
        },
        "constraint_checks": {
            "F01_FINITUDE": f01_pass,
            "N01_NONCOMMUTATION": n01_pass,
            "state_on_algebra_probe_rules": probe_rules_pass,
            "composition_rules": composition_rules_pass,
        },
        "Adm_C": adm_c,
        "fail_reasons": fail_reasons,
    }


def admissible_under(row: dict[str, Any], erase: str | None = None) -> bool:
    checks = dict(row["constraint_checks"])
    if erase == "F01":
        checks["F01_FINITUDE"] = True
    if erase == "N01":
        checks["N01_NONCOMMUTATION"] = True
    return all(bool(value) for value in checks.values())


def signature_values(row: dict[str, Any], probe_names: list[str]) -> list[Any]:
    probes = row["finite_probe_outputs"]
    return [probes[name] for name in probe_names]


def quotient(rows: list[dict[str, Any]], probe_names: list[str]) -> dict[str, Any]:
    classes: dict[str, list[str]] = {}
    signatures: dict[str, list[Any]] = {}
    for row in rows:
        values = signature_values(row, probe_names)
        key = json.dumps(values, sort_keys=True, separators=(",", ":"))
        classes.setdefault(key, []).append(row["id"])
        signatures[key] = values
    ordered = [
        {
            "class_id": f"q{idx}",
            "members": sorted(members),
            "signature": signatures[key],
        }
        for idx, (key, members) in enumerate(sorted(classes.items()))
    ]
    assigned = sorted(member for cls in ordered for member in cls["members"])
    return {
        "probe_names": probe_names,
        "class_count": len(ordered),
        "classes": ordered,
        "partition_member_ids": assigned,
    }


def quotient_well_defined(rows: list[dict[str, Any]], q: dict[str, Any]) -> bool:
    source_ids = sorted(row["id"] for row in rows)
    class_ids = [cls["class_id"] for cls in q["classes"]]
    return (
        bool(rows)
        and q["partition_member_ids"] == source_ids
        and len(class_ids) == len(set(class_ids))
        and q["class_count"] == len(q["classes"])
    )


def layer_verdict(
    f01_changes: bool,
    n01_changes: bool,
    quotient_ok: bool,
    trivial_collapses: bool,
    owner_load_bearing: bool,
) -> str:
    if f01_changes and n01_changes and quotient_ok and trivial_collapses and owner_load_bearing:
        return "REAL_LAYER"
    if not f01_changes and not n01_changes:
        return "CONVENTION"
    if quotient_ok and not trivial_collapses:
        return "GENERIC"
    if f01_changes or n01_changes or owner_load_bearing:
        return "PARTIAL"
    return "OPEN"


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "missing_julia_reference",
            "within_1e_9": False,
            "parity_max_diff": None,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_REFERENCE_PATH)}],
            "boolean_mismatches": [],
            "string_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    max_diff = 0.0
    max_key = None
    rows = []
    strict = []
    missing = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer["shared_scalars"][key]))
        row = {"key": key, "jax": float(value), "julia": float(peer["shared_scalars"][key]), "abs_diff": diff}
        rows.append(row)
        if diff > max_diff:
            max_diff = diff
            max_key = key
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    string_mismatches = []
    for key, value in result["shared_strings"].items():
        if key not in peer.get("shared_strings", {}):
            missing.append(key)
            continue
        if str(value) != str(peer["shared_strings"][key]):
            string_mismatches.append({"key": key, "jax": str(value), "julia": str(peer["shared_strings"][key])})
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not boolean_mismatches and not string_mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict or boolean_mismatches or string_mismatches or missing),
    }


def build_result() -> dict[str, Any]:
    carrier = load_owner_carrier()
    rows = [recompute_row(row) for row in carrier["finite_carrier_rows"]]
    admissible = [row for row in rows if row["Adm_C"]]
    admissible_ids = [row["id"] for row in admissible]
    f01_erased_ids = [row["id"] for row in rows if admissible_under(row, "F01")]
    n01_erased_ids = [row["id"] for row in rows if admissible_under(row, "N01")]
    active_probe_family = ["sheet", "eta_index", "rho_bloch", "order_word", "order_gap_bin", "order_orientation_sign"]
    q_s = quotient(rows, active_probe_family)
    q_adm = quotient(admissible, active_probe_family)
    q_trivial = quotient(admissible, [])
    q_layer_erased = quotient(admissible, ["support_kind"])
    q_ok = quotient_well_defined(rows, q_s) and quotient_well_defined(admissible, q_adm)
    adm_depends_on_finitude = f01_erased_ids != admissible_ids
    erase_finitude_changes_adm = adm_depends_on_finitude
    erase_n01_changes_adm = n01_erased_ids != admissible_ids
    trivial_probe_family_collapses = q_trivial["class_count"] == 1 and q_adm["class_count"] > 1
    owner_real_carrier_load_bearing = q_layer_erased["class_count"] != q_adm["class_count"]
    n01_load_bearing = erase_n01_changes_adm
    verdict = layer_verdict(
        adm_depends_on_finitude,
        n01_load_bearing,
        q_ok,
        trivial_probe_family_collapses,
        owner_real_carrier_load_bearing,
    )
    shared_scalars = {
        "S_size": float(len(rows)),
        "admissible_count": float(len(admissible)),
        "f01_erased_admissible_count": float(len(f01_erased_ids)),
        "n01_erased_admissible_count": float(len(n01_erased_ids)),
        "S_quotient_class_count": float(q_s["class_count"]),
        "Adm_quotient_class_count": float(q_adm["class_count"]),
        "trivial_probe_class_count": float(q_trivial["class_count"]),
        "layer_erased_quotient_class_count": float(q_layer_erased["class_count"]),
    }
    for row in rows:
        prefix = f"candidate.{row['id']}"
        shared_scalars[f"{prefix}.spinor_norm"] = float(row["checks"]["spinor_norm"])
        shared_scalars[f"{prefix}.trace_rho"] = float(row["checks"]["trace_rho"])
        shared_scalars[f"{prefix}.order_gap"] = float(row["checks"]["order_gap"])
    shared_booleans = {
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "source_carrier_all_pass": bool(carrier.get("all_pass")),
        "quotient_well_defined": q_ok,
        "adm_depends_on_finitude": adm_depends_on_finitude,
        "erase_finitude_changes_adm": erase_finitude_changes_adm,
        "erase_n01_changes_adm": erase_n01_changes_adm,
        "n01_load_bearing": n01_load_bearing,
        "trivial_probe_family_collapses": trivial_probe_family_collapses,
        "owner_real_carrier_load_bearing": owner_real_carrier_load_bearing,
        "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
        "promotion_false": promotion_allowed is False,
        "formal_admission_false": formal_admission_allowed is False,
    }
    for row in rows:
        shared_booleans[f"candidate.{row['id']}.Adm_C"] = bool(row["Adm_C"])
        for key, value in row["constraint_checks"].items():
            shared_booleans[f"candidate.{row['id']}.{key}"] = bool(value)
    shared_strings = {
        "layer_verdict": verdict,
        "admissible_ids": ",".join(admissible_ids),
        "f01_erased_ids": ",".join(f01_erased_ids),
        "n01_erased_ids": ",".join(n01_erased_ids),
    }
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "source_carrier_path": str(SOURCE_CARRIER_PATH),
        "source_carrier_object_id": carrier.get("object_id"),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "manifold_layer_discriminator",
        "root_constraints_in_force": ["F01_FINITUDE", "N01_NONCOMMUTATION"],
        "carrier_layer": "finite support / state-on-algebra base layer over owner mc_first_admissibility_packet rows",
        "geometry_layer": "none; quotient is finite probe equivalence only",
        "bridge_layer": "none",
        "cut_layer": "none",
        "allowed_claims": [CLAIM_CEILING],
        "promotion_blockers": [
            "scratch_diagnostic classification",
            "promotion_allowed=false",
            "formal_admission_allowed=false",
            "single finite discriminator row only",
            "does not admit final M(C), a full manifold, a bridge, Axis0, engine, or physics claim",
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
        "S": {
            "definition": "finite admissibility space loaded from the real mc_first_admissibility_packet owner carrier",
            "size": len(rows),
            "candidate_ids": [row["id"] for row in rows],
        },
        "C": {
            "constraints": ["F01_FINITUDE", "N01_NONCOMMUTATION", "state_on_algebra_probe_rules", "composition_rules"],
            "F01": "finite support row, normalized finite state, finite result witness",
            "N01": "nonzero order gap in the finite Pauli probe algebra",
            "probe_rules": "state-on-algebra trace/positivity proxy via finite Bloch probes plus explicit sheet/eta/order labels",
            "composition_rules": "owner carrier composition projection remains enabled",
        },
        "Adm_C": {
            "predicate": "F01 and N01 and state_on_algebra_probe_rules and composition_rules",
            "admissible_ids": admissible_ids,
            "excluded": {row["id"]: row["fail_reasons"] for row in rows if not row["Adm_C"]},
        },
        "quotient_S_mod_M": q_s,
        "quotient_Adm_mod_M": q_adm,
        "controls": {
            "erase_F01_support_to_continuous": {
                "admissible_ids": f01_erased_ids,
                "changes_admissible_set": erase_finitude_changes_adm,
            },
            "erase_N01_commutative_probe_algebra": {
                "admissible_ids": n01_erased_ids,
                "changes_admissible_set": erase_n01_changes_adm,
            },
            "trivial_probe_family": {
                "quotient": q_trivial,
                "collapses": trivial_probe_family_collapses,
            },
            "erase_owner_layer_structure": {
                "quotient": q_layer_erased,
                "changes_result": owner_real_carrier_load_bearing,
            },
        },
        "positive": {
            "adm_depends_on_finitude": {"pass": adm_depends_on_finitude},
            "n01_load_bearing": {"pass": n01_load_bearing},
            "quotient_well_defined": {"pass": q_ok},
            "owner_real_carrier_load_bearing": {"pass": owner_real_carrier_load_bearing},
        },
        "graveyard_companions": {
            "continuous_support_proxy_admitted_only_when_F01_erased": "nonfinite_global_coordinate_control" in f01_erased_ids,
            "commutative_control_admitted_only_when_N01_erased": "commutative_XX_control" in n01_erased_ids,
            "trivial_probe_family_collapses_quotient": trivial_probe_family_collapses,
        },
        "boundary": {
            "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
            "promotion_allowed_false": promotion_allowed is False,
            "formal_admission_allowed_false": formal_admission_allowed is False,
            "claim_ceiling": CLAIM_CEILING,
        },
        "nearby_variants": {
            "total": 4,
            "passed": int(adm_depends_on_finitude)
            + int(n01_load_bearing)
            + int(trivial_probe_family_collapses)
            + int(owner_real_carrier_load_bearing),
            "variants": ["F01_erased", "N01_erased", "trivial_probe_family", "owner_layer_structure_erased"],
        },
        "why_not_v4_probes": "v5 scratch diagnostic dual-backend discriminator row; no v4 promotion language is claimed.",
        "finite_carrier_rows": rows,
        "layer_verdict": verdict,
        "adm_depends_on_finitude": adm_depends_on_finitude,
        "erase_finitude_changes_adm": erase_finitude_changes_adm,
        "erase_n01_changes_adm": erase_n01_changes_adm,
        "quotient_well_defined": q_ok,
        "n01_load_bearing": n01_load_bearing,
        "owner_real_carrier_load_bearing": owner_real_carrier_load_bearing,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(
        carrier.get("all_pass")
        and result["jax_enable_x64"]
        and q_ok
        and adm_depends_on_finitude
        and n01_load_bearing
        and trivial_probe_family_collapses
        and owner_real_carrier_load_bearing
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and result["parity"]["within_1e_9"]
    )
    result["stop_condition_fired"] = not result["all_pass"]
    return result


def print_summary(result: dict[str, Any]) -> None:
    print("disc_finite_support_admissibility - JAX")
    print(
        "all_pass={all_pass} layer_verdict={verdict} adm_depends_on_finitude={f01} "
        "erase_finitude_changes_adm={erase_f01} erase_n01_changes_adm={erase_n01} "
        "quotient_well_defined={quotient} n01_load_bearing={n01} owner_real_carrier_load_bearing={owner}".format(
            all_pass=str(result["all_pass"]).lower(),
            verdict=result["layer_verdict"],
            f01=str(result["adm_depends_on_finitude"]).lower(),
            erase_f01=str(result["erase_finitude_changes_adm"]).lower(),
            erase_n01=str(result["erase_n01_changes_adm"]).lower(),
            quotient=str(result["quotient_well_defined"]).lower(),
            n01=str(result["n01_load_bearing"]).lower(),
            owner=str(result["owner_real_carrier_load_bearing"]).lower(),
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
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
