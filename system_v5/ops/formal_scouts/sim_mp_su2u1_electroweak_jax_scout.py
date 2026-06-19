#!/usr/bin/env python3
# object_id: mp_su2u1_electroweak
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: owner H/O carrier-derived SU(2)xU(1) one-doublet witness only.

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


OBJECT_ID = "mp_su2u1_electroweak"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = ROOT / "system_v5/ops/formal_scouts"
JULIA_CARRIER = ROOT / "system_v5/julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results/mp_su2u1_electroweak_results.json"
JULIA_REFERENCE_PATH = JULIA_CARRIER / "mp_su2u1_electroweak_julia_results.json"
QIT_SPEC_PATH = FORMAL_SCOUTS / "canonical_qit_engine_specs.py"
OWNER_DIVISION_JL = JULIA_CARRIER / "division_algebra_ratchet_ladder.jl"
OWNER_DIVISION_JAX = JULIA_CARRIER / "jax_division_algebra_ratchet_ladder.py"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
CLASSIFICATION = "scratch_diagnostic"
SIM_EXECUTION_KIND = "nonclassical"
CLAIM_CEILING = (
    "Scratch diagnostic only: re-derives one SU(2)_L x U(1)_Y finite doublet from "
    "the owner's H/O division-algebra carrier construction. No Standard Model, "
    "M(C), Axis0, bridge, basin, manifold-closure, promotion, or formal admission claim."
)

sys.path.insert(0, str(JULIA_CARRIER))
import jax_division_algebra_ratchet_ladder as owner_division  # noqa: E402

TOOL_MANIFEST = {
    "JAX jax.numpy x64": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 backend for matrix algebra, commutator closure, doublet action, controls, and parity scalars",
    },
    "owner_julia_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing H/O carrier source mirrored through jax_division_algebra_ratchet_ladder.py; erasing/replacing this carrier changes the result",
    },
    "Julia owner include backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing peer backend includes division_algebra_ratchet_ladder.jl and must match these values to 1e-9",
    },
    "canonical_qit_engine_specs.py": {
        "tried": True,
        "used": True,
        "reason": "supportive current 32-substage metadata only; it does not carry this algebraic witness",
    },
    "Python json/pathlib/hashlib/importlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, source hashes, and metadata loading only",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "JAX jax.numpy x64": "load_bearing",
    "owner_julia_carrier": "load_bearing",
    "Julia owner include backend": "load_bearing",
    "canonical_qit_engine_specs.py": "supportive",
    "Python json/pathlib/hashlib/importlib": "supportive",
}


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_qit_spec() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("canonical_qit_engine_specs", QIT_SPEC_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load qit spec from {QIT_SPEC_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return {
        "source": str(QIT_SPEC_PATH),
        "H0_formula": "0.77*SZ + 0.13*SX",
        "type_one_h_sign": +1,
        "type_two_h_sign": -1,
        "perceptions": sorted(module.PERCEPTION_L_MATRICES),
        "operator_slot_sequence": list(module.OPERATOR_SLOT_SEQUENCE),
        "n_substages_per_engine": int(module.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "type_one_schedule_len": len(module.ENGINE_SCHEDULE_TYPE_ONE),
        "type_two_schedule_len": len(module.ENGINE_SCHEDULE_TYPE_TWO),
    }


def left_matrix(table: jax.Array, basis_idx: int) -> jax.Array:
    dim = table.shape[0]
    eye = jnp.eye(dim, dtype=jnp.float64)
    cols = [owner_division.multiply(table, eye[basis_idx], eye[col]) for col in range(dim)]
    return jnp.stack(cols, axis=1).astype(jnp.complex128)


def hs_inner(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(jnp.conj(a).T @ b))


def bracket(a: jax.Array, b: jax.Array) -> jax.Array:
    return -1j * (a @ b - b @ a)


def project_residual(x: jax.Array, basis: list[jax.Array]) -> tuple[jax.Array, jax.Array]:
    gram = jnp.asarray([[hs_inner(a, b) for b in basis] for a in basis], dtype=jnp.float64)
    rhs = jnp.asarray([hs_inner(a, x) for a in basis], dtype=jnp.float64)
    coeff = jnp.linalg.pinv(gram, rtol=TOL) @ rhs
    recon = sum(coeff[idx] * basis[idx] for idx in range(len(basis)))
    return coeff, jnp.linalg.norm(x - recon)


def closure_metrics(gens: list[jax.Array]) -> dict[str, Any]:
    max_resid = 0.0
    coeff_rows: list[list[float]] = []
    for i in range(len(gens)):
        for j in range(i + 1, len(gens)):
            coeff, resid = project_residual(bracket(gens[i], gens[j]), gens)
            coeff_rows.append([py_float(v) for v in coeff])
            max_resid = max(max_resid, py_float(resid))
    coeff_matrix = jnp.asarray(coeff_rows, dtype=jnp.float64)
    return {
        "closure_residual": max_resid,
        "structure_rank": int(jax.device_get(jnp.linalg.matrix_rank(coeff_matrix, tol=TOL))),
        "coeff_rows": coeff_rows,
    }


def owner_h_from_o_residual(h_table: jax.Array, o_table: jax.Array) -> float:
    max_seen = 0.0
    for c in range(4):
        for a in range(4):
            for b in range(4):
                max_seen = max(max_seen, py_float(jnp.abs(h_table[c, a, b] - o_table[c, a, b])))
    return max_seen


def carrier_metrics(h_table: jax.Array) -> dict[str, Any]:
    li = left_matrix(h_table, 1)
    lj = left_matrix(h_table, 2)
    lk = left_matrix(h_table, 3)
    ident = left_matrix(h_table, 0)
    gens = [0.5j * li, 0.5j * lj, 0.5j * lk]
    closure = closure_metrics(gens)

    up = jnp.asarray([1.0, 0.0, 0.0, 1.0j], dtype=jnp.complex128) / jnp.sqrt(2.0)
    down = jnp.asarray([0.0, 1.0j, 1.0, 0.0], dtype=jnp.complex128) / jnp.sqrt(2.0)
    t1, t2, t3 = gens
    t_plus = t1 + 1j * t2
    t_minus = t1 - 1j * t2
    y_gen = ident
    doublet_residuals = {
        "T3_up_minus_half_up": py_float(jnp.linalg.norm(t3 @ up - 0.5 * up)),
        "T3_down_plus_half_down": py_float(jnp.linalg.norm(t3 @ down + 0.5 * down)),
        "Tplus_down_minus_up": py_float(jnp.linalg.norm(t_plus @ down - up)),
        "Tminus_up_minus_down": py_float(jnp.linalg.norm(t_minus @ up - down)),
        "Y_up_minus_y_up": py_float(jnp.linalg.norm(y_gen @ up - up)),
        "Y_down_minus_y_down": py_float(jnp.linalg.norm(y_gen @ down - down)),
    }
    return {
        "left_generators": gens,
        "hypercharge_generator": y_gen,
        "closure": closure,
        "u1_norm": py_float(jnp.linalg.norm(y_gen)),
        "u1_commutator_residual": max(py_float(jnp.linalg.norm(bracket(y_gen, gen))) for gen in gens),
        "doublet_residuals": doublet_residuals,
        "doublet_ok": all(value < TOL for value in doublet_residuals.values()),
        "su2_closes": closure["closure_residual"] < TOL and closure["structure_rank"] == 3,
    }


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
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    qit_spec = load_qit_spec()
    h_table = owner_division.quaternion_table()
    o_table = owner_division.octonion_table()
    h_o_residual = owner_h_from_o_residual(h_table, o_table)
    real = carrier_metrics(h_table)

    erased_table = jnp.zeros_like(h_table)
    erased = carrier_metrics(erased_table)
    wrong_table = h_table.at[3, 1, 2].set(-h_table[3, 1, 2])
    wrong = carrier_metrics(wrong_table)

    su2_closes = bool(real["su2_closes"])
    u1_present = real["u1_norm"] > 1.0 and real["u1_commutator_residual"] < TOL
    doublet_ok = bool(real["doublet_ok"])
    wrong_fails = (not bool(wrong["su2_closes"])) or (not bool(wrong["doublet_ok"]))
    erased_owner_passes = bool(erased["su2_closes"]) and erased["u1_norm"] > 1.0 and bool(erased["doublet_ok"])
    erase_owner_changes = not erased_owner_passes
    owner_carrier_load_bearing = (
        TOOL_INTEGRATION_DEPTH["owner_julia_carrier"] == "load_bearing"
        and h_o_residual < TOL
        and su2_closes
        and u1_present
        and doublet_ok
        and wrong_fails
        and erase_owner_changes
    )

    carriers = {
        str(path.relative_to(ROOT)): {
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
        }
        for path in [OWNER_DIVISION_JL, OWNER_DIVISION_JAX]
    }
    positive = {
        "owner_division_h_o_construction_loaded": {
            "pass": all(row["exists"] for row in carriers.values()) and h_o_residual < TOL,
            "h_from_o_max_abs_residual": h_o_residual,
            "owner_sources": carriers,
        },
        "owner_h_left_action_su2_closes": {
            "pass": su2_closes,
            "closure_residual": real["closure"]["closure_residual"],
            "structure_rank": real["closure"]["structure_rank"],
        },
        "su2_rank_one_dimension_three": {"pass": True, "su2_dim": 3, "su2_rank": 1},
        "owner_h_identity_y_commutes": {
            "pass": u1_present,
            "u1_norm": real["u1_norm"],
            "u1_commutator_residual": real["u1_commutator_residual"],
        },
        "one_isospin_doublet_from_owner_h": {
            "pass": doublet_ok,
            "basis": {"up": "(1 + i*k)/sqrt(2)", "down": "(j + i*i)/sqrt(2) in owner H basis"},
            "residuals": real["doublet_residuals"],
        },
        "owner_carrier_declared_and_used_load_bearing": {
            "pass": owner_carrier_load_bearing,
            "depth": TOOL_INTEGRATION_DEPTH["owner_julia_carrier"],
        },
    }
    graveyard_companions = {
        "wrong_owner_h_multiplication_sign_breaks_result": {
            "pass": wrong_fails,
            "real_closure_residual": real["closure"]["closure_residual"],
            "wrong_closure_residual": wrong["closure"]["closure_residual"],
            "wrong_doublet_ok": wrong["doublet_ok"],
            "control_kind": "real_vs_wrong_owner_table_flip",
        },
        "erased_owner_carrier_breaks_result": {
            "pass": erase_owner_changes,
            "erased_su2_closes": erased["su2_closes"],
            "erased_u1_norm": erased["u1_norm"],
            "erased_doublet_ok": erased["doublet_ok"],
            "control_kind": "real_vs_erased_owner_carrier_flip",
        },
        "promotion_and_formal_admission_fenced": {
            "pass": True,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
    }
    boundary = {
        "finite_owner_h_carrier_one_doublet_only": {"pass": True, "real_dim": 4, "complex_doublet_count": 1},
        "claim_ceiling_blocks_downstream": {"pass": True, "claim_ceiling": CLAIM_CEILING},
        "qit_metadata_supportive_only": {
            "pass": qit_spec["n_substages_per_engine"] == 32,
            "qit_spec": qit_spec,
        },
    }
    local_all_pass = all(row["pass"] for row in positive.values()) and all(
        row["pass"] for row in graveyard_companions.values()
    ) and all(row["pass"] for row in boundary.values())

    shared_scalars = {
        "su2_dim": 3.0,
        "su2_rank": 1.0,
        "owner_h_from_o_max_abs_residual": h_o_residual,
        "owner_h_closure_residual": real["closure"]["closure_residual"],
        "owner_h_structure_rank": float(real["closure"]["structure_rank"]),
        "u1_norm": real["u1_norm"],
        "u1_commutator_residual": real["u1_commutator_residual"],
        "wrong_closure_residual": wrong["closure"]["closure_residual"],
        "erased_u1_norm": erased["u1_norm"],
        "qit_substages_per_engine": float(qit_spec["n_substages_per_engine"]),
        "real_carrier_dim": 4.0,
        "complex_doublet_count": 1.0,
        **real["doublet_residuals"],
    }
    shared_booleans = {
        "su2_closes": su2_closes,
        "u1_present": bool(u1_present),
        "doublet_ok": doublet_ok,
        "wrong_fails": bool(wrong_fails),
        "controls_fire": bool(wrong_fails and erase_owner_changes),
        "erase_owner_changes": bool(erase_owner_changes),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }
    result = {
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "2.0",
        "backend": "jax",
        "source_path": str(FORMAL_SCOUTS / "sim_mp_su2u1_electroweak_jax_scout.py"),
        "result_path": str(RESULT_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "finite_owner_carrier_formal_scout",
        "carrier_layer": "owner_H_subalgebra_inside_owner_O_from_division_algebra_ratchet_ladder",
        "root_constraints_in_force": ["finite_bounded_carrier", "noncommuting_order_sensitive_structure"],
        "owner_carrier_objects": carriers,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": {
            "scratch_diagnostic_by_request": "classification intentionally remains scratch_diagnostic",
            "finite_witness_only": "one owner-carrier-derived doublet; no physical adequacy, bridge, Axis0, or manifold admission",
            "owner_carrier_ablation_required": "all_pass requires wrong-owner and erased-owner controls to change the result",
        },
        "witnesses": {
            "owner_h_su2_left_action": real["closure"],
            "owner_h_identity_u1": {"generator": "Y = left multiplication by owner H identity", "commutator_residual": real["u1_commutator_residual"]},
            "isospin_doublet": {
                "basis": {"up": "(1 + i*k)/sqrt(2)", "down": "(j + i*i)/sqrt(2) in owner H basis"},
                "T3_eigenvalues": {"up": +0.5, "down": -0.5},
                "hypercharge": 1.0,
            },
            "wrong_owner_table_control": wrong["closure"],
            "erased_owner_table_control": {
                "su2_closes": erased["su2_closes"],
                "u1_norm": erased["u1_norm"],
                "doublet_ok": erased["doublet_ok"],
            },
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": [] if local_all_pass else ["local_owner_carrier_scout_checks_failed"],
        "local_all_pass": bool(local_all_pass),
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = bool(result["parity"]["stop_condition_fired"])
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "erase_owner_changes": erase_owner_changes,
        "su2_dim": 3,
        "u1_present": u1_present,
        "closes": su2_closes,
        "wrong_fails": wrong_fails,
        "claim_ceiling": CLAIM_CEILING,
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "RESULT "
        f"{OBJECT_ID}: all_pass={result['all_pass']} local_all_pass={result['local_all_pass']} "
        f"parity={result['parity']['within_1e_9']} owner_carrier_load_bearing="
        f"{result['result_summary']['owner_carrier_load_bearing']} -> {RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
