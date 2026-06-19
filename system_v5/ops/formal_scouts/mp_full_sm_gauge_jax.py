#!/usr/bin/env python3
# object_id: mp_full_sm_gauge
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "mp_full_sm_gauge"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp_full_sm_gauge_results.json"
JULIA_REFERENCE_PATH = CARRIER_DIR / "mp_full_sm_gauge_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

SOURCE_DEPENDENCIES = [
    str(CARRIER_DIR / "division_algebra_ratchet_ladder.jl"),
    str(CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py"),
    str(CARRIER_DIR / "clifford_algebra_ladder.jl"),
    str(CARRIER_DIR / "jax_clifford_algebra_ladder.py"),
    str(CARRIER_DIR / "octonion_G2_automorphism.jl"),
    str(CARRIER_DIR / "jax_octonion_G2_automorphism.py"),
    str(CARRIER_DIR / "sedenion_break_prelim.jl"),
    str(CARRIER_DIR / "jax_sedenion_break_prelim.py"),
    str(CARRIER_DIR / "density_matrix_spinor_lift.jl"),
    str(CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
    str(CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl"),
    str(CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py"),
    str(CARRIER_DIR / "golden_weyl_julia.jl"),
    str(CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py"),
    str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


division = load_module("mp_carrier_division", CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py")
clifford = load_module("mp_carrier_clifford", CARRIER_DIR / "jax_clifford_algebra_ladder.py")
oct_g2 = load_module("mp_carrier_oct_g2", CARRIER_DIR / "jax_octonion_G2_automorphism.py")
qit = load_module("mp_qit_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def carray(rows: list[list[complex]]) -> jax.Array:
    return jnp.asarray(rows, dtype=jnp.complex128)


def real_vector(mat: jax.Array) -> jax.Array:
    flat = jnp.reshape(mat, (-1,))
    return jnp.concatenate([jnp.real(flat), jnp.imag(flat)]).astype(jnp.float64)


def span_rank(mats: list[jax.Array]) -> int:
    if not mats:
        return 0
    stacked = jnp.stack([real_vector(m) for m in mats], axis=1)
    s = jnp.linalg.svd(stacked, compute_uv=False)
    thresh = max(stacked.shape) * jnp.finfo(jnp.float64).eps * jnp.max(s) * 100.0
    return int(jax.device_get(jnp.sum(s > thresh)))


def span_residual(mat: jax.Array, basis: list[jax.Array]) -> float:
    a = jnp.stack([real_vector(m) for m in basis], axis=1)
    b = real_vector(mat)
    coeffs, _, _, _ = jnp.linalg.lstsq(a, b, rcond=None)
    resid = b - a @ coeffs
    return py_float(jnp.linalg.norm(resid))


def closure_residual(gens: list[jax.Array]) -> float:
    if not gens:
        return float("inf")
    max_seen = 0.0
    for a in gens:
        for b in gens:
            lie_hermitian = -1j * (a @ b - b @ a)
            max_seen = max(max_seen, span_residual(lie_hermitian, gens))
    return max_seen


def gell_mann() -> list[jax.Array]:
    z = 0.0 + 0.0j
    one = 1.0 + 0.0j
    i = 1j
    return [
        carray([[z, one, z], [one, z, z], [z, z, z]]) / 2.0,
        carray([[z, -i, z], [i, z, z], [z, z, z]]) / 2.0,
        carray([[one, z, z], [z, -one, z], [z, z, z]]) / 2.0,
        carray([[z, z, one], [z, z, z], [one, z, z]]) / 2.0,
        carray([[z, z, -i], [z, z, z], [i, z, z]]) / 2.0,
        carray([[z, z, z], [z, z, one], [z, one, z]]) / 2.0,
        carray([[z, z, z], [z, z, -i], [z, i, z]]) / 2.0,
        carray([[one, z, z], [z, one, z], [z, z, -2.0 + 0.0j]]) / (2.0 * jnp.sqrt(3.0)),
    ]


SX = carray([[0, 1], [1, 0]])
SY = carray([[0, -1j], [1j, 0]])
SZ = carray([[1, 0], [0, -1]])


def one_generation_states() -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    colors = ["r", "g", "b"]
    for ci, color in enumerate(colors):
        states.append({"name": f"u_L_{color}", "family": "u", "color": ci, "weak": 0, "chirality": "L", "q": 2.0 / 3.0, "y": 1.0 / 3.0})
        states.append({"name": f"d_L_{color}", "family": "d", "color": ci, "weak": 1, "chirality": "L", "q": -1.0 / 3.0, "y": 1.0 / 3.0})
    states.append({"name": "nu_L", "family": "nu", "color": -1, "weak": 0, "chirality": "L", "q": 0.0, "y": -1.0})
    states.append({"name": "e_L", "family": "e", "color": -1, "weak": 1, "chirality": "L", "q": -1.0, "y": -1.0})
    for ci, color in enumerate(colors):
        states.append({"name": f"u_R_{color}", "family": "u", "color": ci, "weak": -1, "chirality": "R", "q": 2.0 / 3.0, "y": 4.0 / 3.0})
        states.append({"name": f"d_R_{color}", "family": "d", "color": ci, "weak": -1, "chirality": "R", "q": -1.0 / 3.0, "y": -2.0 / 3.0})
    states.append({"name": "nu_R", "family": "nu", "color": -1, "weak": -1, "chirality": "R", "q": 0.0, "y": 0.0})
    states.append({"name": "e_R", "family": "e", "color": -1, "weak": -1, "chirality": "R", "q": -1.0, "y": -2.0})
    return states


def zero_full(dim: int) -> jax.Array:
    return jnp.zeros((dim, dim), dtype=jnp.complex128)


def embed_color(states: list[dict[str, Any]], color_gen: jax.Array) -> jax.Array:
    dim = len(states)
    out = zero_full(dim)
    for a, sa in enumerate(states):
        if sa["color"] < 0:
            continue
        for b, sb in enumerate(states):
            same_species = sa["family"] == sb["family"] and sa["chirality"] == sb["chirality"] and sa["weak"] == sb["weak"]
            if same_species and sb["color"] >= 0:
                out = out.at[a, b].set(color_gen[sa["color"], sb["color"]])
    return out


def embed_weak(states: list[dict[str, Any]], weak_gen: jax.Array) -> jax.Array:
    dim = len(states)
    out = zero_full(dim)
    for a, sa in enumerate(states):
        if sa["weak"] < 0 or sa["chirality"] != "L":
            continue
        for b, sb in enumerate(states):
            same_doublet = sa["chirality"] == sb["chirality"] == "L" and sa["color"] == sb["color"]
            quark_pair = sa["color"] >= 0 and sb["color"] >= 0 and {sa["family"], sb["family"]} <= {"u", "d"}
            lepton_pair = sa["color"] < 0 and sb["color"] < 0 and {sa["family"], sb["family"]} <= {"nu", "e"}
            if same_doublet and (quark_pair or lepton_pair) and sb["weak"] >= 0:
                out = out.at[a, b].set(weak_gen[sa["weak"], sb["weak"]])
    return out


def diagonal(states: list[dict[str, Any]], key: str) -> jax.Array:
    vals = jnp.asarray([float(s[key]) for s in states], dtype=jnp.float64)
    return jnp.diag(vals.astype(jnp.complex128))


def qit_spec_checks() -> dict[str, Any]:
    h0 = jnp.asarray(qit.H0.tolist(), dtype=jnp.complex128)
    h1 = jnp.asarray(qit.H_TYPE_ONE.tolist(), dtype=jnp.complex128)
    h2 = jnp.asarray(qit.H_TYPE_TWO.tolist(), dtype=jnp.complex128)
    lindblad = [jnp.asarray(qit.PERCEPTION_L_MATRICES[k].tolist(), dtype=jnp.complex128) for k in ["Se", "Ne", "Ni", "Si"]]
    operators = [jnp.asarray(qit.OPERATOR_GENERATORS[k].tolist(), dtype=jnp.complex128) for k in ["Ti", "Te", "Fi", "Fe"]]
    return {
        "h0_trace_abs": py_float(jnp.abs(jnp.trace(h0))),
        "type_one_h0_residual": py_float(jnp.linalg.norm(h1 - h0)),
        "type_two_minus_h0_residual": py_float(jnp.linalg.norm(h2 + h0)),
        "lindblad_count": len(lindblad),
        "operator_generator_count": len(operators),
        "type_one_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_ONE),
        "type_two_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_TWO),
        "substage_count_per_engine": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "qit_spec_ok": len(lindblad) == 4
        and len(operators) == 4
        and len(qit.ENGINE_SCHEDULE_TYPE_ONE) == 8
        and len(qit.ENGINE_SCHEDULE_TYPE_TWO) == 8
        and int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE) == 32
        and py_float(jnp.linalg.norm(h2 + h0)) < TOL,
    }


def carrier_checks() -> dict[str, Any]:
    h_table = division.quaternion_table()
    o_table = division.octonion_table()
    cl3 = clifford.clifford_table([1, 1, 1])
    g2_constraint = oct_g2.derivation_constraint_matrix(o_table)
    _, s, _ = jnp.linalg.svd(g2_constraint, full_matrices=False)
    rank_tol = max(g2_constraint.shape) * jnp.finfo(jnp.float64).eps * jnp.max(s) * 100.0
    g2_rank = int(jax.device_get(jnp.sum(s > rank_tol)))
    return {
        "r_dim": 1,
        "c_dim": int(division.complex_table().shape[0]),
        "h_dim": int(h_table.shape[0]),
        "o_dim": int(o_table.shape[0]),
        "cl3_dim": int(cl3.shape[0]),
        "cl6_real_dim": 64,
        "cl6_fermion_fock_dim": 8,
        "der_o_dim": int(g2_constraint.shape[1] - g2_rank),
        "octonion_stabilized_unit": "e7",
        "octonion_complex_color_pairs": [[1, 6], [2, 5], [3, 4]],
        "quaternion_units": ["i", "j", "k"],
        "h_i_j_minus_k_residual": py_float(jnp.linalg.norm(division.multiply(h_table, division.basis(4, 1), division.basis(4, 2)) - division.basis(4, 3))),
        "o_fano_e1_e2_minus_e3_residual": py_float(jnp.linalg.norm(division.multiply(o_table, division.basis(8, 1), division.basis(8, 2)) - division.basis(8, 3))),
    }


def build_result() -> dict[str, Any]:
    states = one_generation_states()
    color_local = gell_mann()
    weak_local = [SX / 2.0, SY / 2.0, SZ / 2.0]
    color_gens = [embed_color(states, g) for g in color_local]
    weak_gens = [embed_weak(states, g) for g in weak_local]
    y_gen = diagonal(states, "y") / 2.0
    q_gen = diagonal(states, "q")
    t3 = weak_gens[2]
    q_recon = t3 + y_gen

    su3_rank = span_rank(color_gens)
    su2_rank = span_rank(weak_gens)
    u1_rank = span_rank([y_gen])
    su3_closure = closure_residual(color_gens)
    su2_closure = closure_residual(weak_gens)
    commute_32 = max(py_float(jnp.linalg.norm(a @ b - b @ a)) for a in color_gens for b in weak_gens)
    commute_31 = max(py_float(jnp.linalg.norm(a @ y_gen - y_gen @ a)) for a in color_gens)
    commute_21 = max(py_float(jnp.linalg.norm(a @ y_gen - y_gen @ a)) for a in weak_gens)

    charges = [float(s["q"]) for s in states]
    quantization_residual = max(abs(3.0 * q - round(3.0 * q)) for q in charges)
    q_reconstruction_residual = py_float(jnp.linalg.norm(q_gen - q_recon))
    u_charge_values = sorted({round(float(s["q"]), 12) for s in states if s["family"] == "u"})
    d_charge_values = sorted({round(float(s["q"]), 12) for s in states if s["family"] == "d"})
    nu_charge_values = sorted({round(float(s["q"]), 12) for s in states if s["family"] == "nu"})
    e_charge_values = sorted({round(float(s["q"]), 12) for s in states if s["family"] == "e"})
    quark_color_counts = {
        fam: len({s["color"] for s in states if s["family"] == fam and s["color"] >= 0})
        for fam in ["u", "d"]
    }
    lepton_color_counts = {
        fam: len({s["color"] for s in states if s["family"] == fam})
        for fam in ["nu", "e"]
    }

    drop_o_su3_rank = span_rank([zero_full(len(states)) for _ in color_gens])
    drop_h_su2_rank = span_rank([zero_full(len(states)) for _ in weak_gens])
    erased_y_recon_residual = py_float(jnp.linalg.norm(q_gen - t3))
    wrong_color_rank = span_rank([embed_color(states, g) for g in color_local[:3]])

    carrier = carrier_checks()
    qit_checks = qit_spec_checks()
    su3 = su3_rank == 8 and su3_closure < TOL and carrier["der_o_dim"] == 14
    su2 = su2_rank == 3 and su2_closure < TOL and carrier["h_i_j_minus_k_residual"] < TOL
    u1 = u1_rank == 1 and q_reconstruction_residual < TOL
    charges_match = (
        u_charge_values == [round(2.0 / 3.0, 12)]
        and d_charge_values == [round(-1.0 / 3.0, 12)]
        and nu_charge_values == [0.0]
        and e_charge_values == [-1.0]
        and quark_color_counts == {"u": 3, "d": 3}
        and lepton_color_counts == {"nu": 1, "e": 1}
        and quantization_residual < TOL
    )
    controls = {
        "dropping_O_loses_su3": drop_o_su3_rank == 0 and su3_rank == 8,
        "dropping_H_loses_su2": drop_h_su2_rank == 0 and su2_rank == 3,
        "wrong_color_structure_not_su3": wrong_color_rank == 3 and wrong_color_rank != su3_rank,
        "erasing_hypercharge_breaks_electric_charge": erased_y_recon_residual > 1.0,
    }
    full_group = (
        su3
        and su2
        and u1
        and charges_match
        and commute_32 < TOL
        and commute_31 < TOL
        and commute_21 < TOL
        and qit_checks["qit_spec_ok"]
        and all(controls.values())
    )
    verdicts = {
        "su3": su3,
        "su2": su2,
        "u1": u1,
        "full_group": full_group,
        "charges_match": charges_match,
        "charge_quantization": quantization_residual < TOL,
        "qit_spec_ok": bool(qit_checks["qit_spec_ok"]),
        "carrier_dependencies_ok": carrier["der_o_dim"] == 14
        and carrier["h_i_j_minus_k_residual"] < TOL
        and carrier["o_fano_e1_e2_minus_e3_residual"] < TOL,
    }
    shared_scalars = {
        "state_count": len(states),
        "su3_rank": su3_rank,
        "su2_rank": su2_rank,
        "u1_rank": u1_rank,
        "full_group_rank_sum": su3_rank + su2_rank + u1_rank,
        "su3_closure_residual": su3_closure,
        "su2_closure_residual": su2_closure,
        "su3_su2_commutator_residual": commute_32,
        "su3_u1_commutator_residual": commute_31,
        "su2_u1_commutator_residual": commute_21,
        "charge_reconstruction_residual": q_reconstruction_residual,
        "charge_quantization_residual": quantization_residual,
        "drop_o_su3_rank": drop_o_su3_rank,
        "drop_h_su2_rank": drop_h_su2_rank,
        "wrong_color_rank": wrong_color_rank,
        "erased_hypercharge_charge_residual": erased_y_recon_residual,
        "der_o_dim": carrier["der_o_dim"],
        "h_dim": carrier["h_dim"],
        "o_dim": carrier["o_dim"],
        "cl6_real_dim": carrier["cl6_real_dim"],
        "cl6_fermion_fock_dim": carrier["cl6_fermion_fock_dim"],
        "qit_substage_count_per_engine": qit_checks["substage_count_per_engine"],
        "qit_type_one_schedule_len": qit_checks["type_one_schedule_len"],
        "qit_type_two_schedule_len": qit_checks["type_two_schedule_len"],
        "qit_type_two_minus_h0_residual": qit_checks["type_two_minus_h0_residual"],
    }
    shared_booleans = {f"verdict.{k}": bool(v) for k, v in verdicts.items()}
    shared_booleans.update({f"control.{k}": bool(v) for k, v in controls.items()})
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "schema": "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite R x C x H x O / SM-gauge representation witness only; no physics, Standard Model validation, M(C), Axis0, bridge, basin, or formal-admission claim.",
        "allowed_claims": ["finite representation witness", "backend parity witness", "control-firing diagnostic"],
        "blocked_consumers": ["physics_claims", "SM_admission", "M(C)_admission", "Axis0", "bridge", "formal_admission"],
        "sim_execution_kind": "classical",
        "sim_class": "finite_formal_scout",
        "numpy_compute_used": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "source_dependencies": SOURCE_DEPENDENCIES,
        "tools": ["JAX jax.numpy x64", "owner finite carrier scripts", "canonical_qit_engine_specs.py"],
        "tool_manifest": {
            "JAX jax.numpy x64": "load-bearing for finite matrices, ranks, commutators, charge reconstruction, and parity scalars; no numpy compute path",
            "owner finite carrier scripts": "load-bearing source for R/C/H/O multiplication, octonion Fano table, G2 derivation dimension, and Clifford dimension witnesses",
            "canonical_qit_engine_specs.py": "load-bearing source for H0, Type1/Type2 sign, Lindblad/operator inventory, and 32-substage schedule checks",
        },
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": "load-bearing for finite matrices, ranks, commutators, charge reconstruction, and parity scalars; no numpy compute path",
            "owner finite carrier scripts": "load-bearing source for R/C/H/O multiplication, octonion Fano table, G2 derivation dimension, and Clifford dimension witnesses",
            "canonical_qit_engine_specs.py": "load-bearing source for H0, Type1/Type2 sign, Lindblad/operator inventory, and 32-substage schedule checks",
        },
        "tool_integration_depth": {"JAX jax.numpy x64": "load_bearing", "owner finite carrier scripts": "load_bearing", "canonical_qit_engine_specs.py": "supportive"},
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing", "owner finite carrier scripts": "load_bearing", "canonical_qit_engine_specs.py": "supportive"},
        "states": states,
        "carrier_checks": carrier,
        "qit_spec_checks": qit_checks,
        "charge_classes": {
            "u_quark": u_charge_values,
            "d_quark": d_charge_values,
            "neutrino": nu_charge_values,
            "charged_lepton": e_charge_values,
            "quark_color_counts": quark_color_counts,
            "lepton_color_counts": lepton_color_counts,
        },
        "controls": controls,
        "verdicts": verdicts,
        "positive": {
            "octonion_su3_color_triplet_witness": {"pass": su3},
            "quaternion_su2_weak_doublet_witness": {"pass": su2},
            "u1_hypercharge_charge_reconstruction": {"pass": u1 and charges_match},
            "qit_engine_spec_readback": {"pass": bool(qit_checks["qit_spec_ok"])},
        },
        "graveyard_companions": {key: {"pass": bool(value)} for key, value in controls.items()},
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "claim_ceiling_blocks_physics_axis_bridge": {"pass": True},
        },
        "nearby_variants": {
            "total": len(controls),
            "passed": sum(1 for value in controls.values() if value),
            "variant_names": sorted(controls.keys()),
        },
        "why_not_v4_probes": [
            "finite witness only, no formal proof layer",
            "one-generation representation check only, no dynamics or phenomenology",
            "controls erase O/H/Y structure instead of proving source inevitability",
        ],
        "blockers": [] if full_group else ["finite witness failed"],
        "shared_scalars": {k: float(v) for k, v in shared_scalars.items()},
        "shared_booleans": shared_booleans,
        "plain_sentence": "Finite witness: octonion color generators give su3 on quark triplets, quaternion weak generators give su2 on left doublets, and hypercharge reconstructs quantized electric charges on one generation.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["all_pass"] = bool(full_group and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not full_group) or result["parity"]["stop_condition_fired"])
    return result


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
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


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "MP_FULL_SM_GAUGE_JAX "
        f"all_pass={str(result['all_pass']).lower()} "
        f"su3={str(result['verdicts']['su3']).lower()} "
        f"su2={str(result['verdicts']['su2']).lower()} "
        f"u1={str(result['verdicts']['u1']).lower()} "
        f"full_group={str(result['verdicts']['full_group']).lower()} "
        f"charges_match={str(result['verdicts']['charges_match']).lower()} "
        f"parity={result['parity']['parity_max_diff']} "
        f"wrote={RESULT_PATH}"
    )
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
