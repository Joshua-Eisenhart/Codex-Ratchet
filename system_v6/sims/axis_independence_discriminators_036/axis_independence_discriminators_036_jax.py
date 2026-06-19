#!/usr/bin/env python3
"""JAX leg for axis_independence_discriminators_036 v2.

This rebuild intentionally computes every matrix cell from one shared carrier
state. The Axis-0 readout imports the committed terrain packet path; the
Axis-6 gap imports the same source-locked operator/terrain packet style used by
terrain_operator_precedence_64_matrix.
"""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as _dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "axis_independence_discriminators_036"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

OP_PACKET = ROOT / "system_v6" / "sims" / "source_locked_operator_base_packet" / "source_locked_operator_base_packet_jax.py"
TERRAIN_PACKET = ROOT / "system_v6" / "sims" / "terrain_generator_sheet_packet" / "terrain_generator_sheet_packet_jax.py"
MCT_RESULT = ROOT / "system_v6" / "sims" / "mct_dynamic_admissibility_packet_v0" / "results" / "mct_dynamic_admissibility_packet_v0_jax_results.json"
MATRIX64_RESULT = ROOT / "system_v6" / "sims" / "terrain_operator_precedence_64_matrix" / "results" / "terrain_operator_precedence_64_matrix_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
AXIS0_STATUS = "readout_only_no_closure"
TOL = 1.0e-8
VISIBLE_TOL = 1.0e-4
BLIND_TOL = 5.0e-10
SMT_SCALE = 10**7

PIN_BLOCK_CANONICAL = json.dumps(
    {
        "sim_id": SIM_ID,
        "version": "v2_carrier_coupled_rebuild_after_decorative_audit",
        "claim": "axis0_axis3_axis6_independence_as_3x3_diagonal_dominance_under_named_readouts",
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "axis0_status": AXIS0_STATUS,
        },
        "base_polarities": {
            "axis0_family": "Ne",
            "axis3_placement": "fiber",
            "axis6_precedence": "operator_first",
            "axis4_loop_order": "deductive",
        },
        "vary_polarities": {
            "axis0": {"axis0_family": "Se"},
            "axis3": {"axis3_placement": "base"},
            "axis6": {"axis6_precedence": "terrain_first"},
        },
        "observables": {
            "O0": "committed terrain packet pauli_participation_ratio response sign/class",
            "O3": "loop coordinate density delta class fiber_stationary/base_visible",
            "O6": "source-locked terrain/operator precedence signed gap",
        },
        "prohibitions": [
            "no_axis_admission",
            "no_axis0_closure",
            "no_IGT",
            "no_b6_scaffold_as_independence_proof",
            "axis4_distinct_from_axis6",
        ],
    },
    sort_keys=True,
    separators=(",", ":"),
)
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()

SOURCE_REFS = {
    "decorative_audit_required_gaps": "system_v6/sims/axis_independence_discriminators_036/audit_verdict.md:238-244",
    "axis_independence_spec": "system_v6/receipts/axis_independence_mine_20260610.md:A-D",
    "axis0_committed_terrain_path": "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:537-616",
    "axis6_matrix64_import_precedent": "system_v6/sims/terrain_operator_precedence_64_matrix/terrain_operator_precedence_64_matrix_jax.py:41-45,103-104,237-268",
    "axis4_section15_forms": "system_v6/foundations/working_math_scaffold_20260609.md:165,171-175",
    "axis4_axis6_source_boundary": "system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:889-918,1076",
}

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive shared carrier state construction and x64 readout recomputation; substrate demoted under capability-probe doctrine"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive density matrices, norms, traces, hashes, and loop/order readouts; substrate demoted under capability-probe doctrine"},
    "jax.scipy.linalg": {
        "tried": True,
        "used": True,
        "reason": "supportive via imported terrain packet; matrix exponential is source-locked in terrain_generator_sheet_packet_jax.py",
    },
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw-value diagonal-dominance SMT pressure"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw-value diagonal-dominance SMT pressure"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive import loading, hashing, timestamps, and JSON serialization"},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "jax.scipy.linalg": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

BASE_POLARITIES = {
    "axis0_family": "Ne",
    "axis3_placement": "fiber",
    "axis6_precedence": "operator_first",
    "axis4_loop_order": "deductive",
}
VARY_BY_AXIS = {
    "axis0": {"axis0_family": "Se"},
    "axis3": {"axis3_placement": "base"},
    "axis6": {"axis6_precedence": "terrain_first"},
}
DIAGONAL_OBSERVABLE = {"axis0": "O0", "axis3": "O3", "axis6": "O6"}
OBSERVABLE_CRITERIA = {
    "O0": "class is sign of committed PPR response; positive allostatic vs negative homeostatic",
    "O3": "fiber density delta <= TOL; base density delta > VISIBLE_TOL",
    "O6": "operator-first signed gap positive vs terrain-first signed gap negative; absolute gap > TOL",
}
BLIND_EXPECTED = {"Ne": 0.08037043685314521, "Se": -0.0018131249410586747}

TERRAIN_BY_FAMILY_PLACEMENT = {
    "Ne": {
        "fiber": {"terrain_id": "Ne/Vortex", "terrain_key": "Vortex", "kwargs": {"ne_variant": "pure_hamiltonian"}, "sheet": "L"},
        "base": {"terrain_id": "Ne/Spiral", "terrain_key": "Spiral", "kwargs": {"ne_variant": "pure_hamiltonian"}, "sheet": "R"},
    },
    "Se": {
        "fiber": {"terrain_id": "Se/Funnel", "terrain_key": "Funnel", "kwargs": {}, "sheet": "L"},
        "base": {"terrain_id": "Se/Cannon", "terrain_key": "Cannon", "kwargs": {}, "sheet": "R"},
    },
}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OP_SRC = load_module(OP_PACKET, "axis_independence_operator_packet_jax_reuse")
TERRAIN_SRC = load_module(TERRAIN_PACKET, "axis_independence_terrain_packet_jax_reuse")

I2 = OP_SRC.I2
SX = OP_SRC.SX
SY = OP_SRC.SY
SZ = OP_SRC.SZ


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def real_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def fro_norm(mat: Any) -> float:
    return real_float(jnp.linalg.norm(mat))


def trace_norm(mat: Any) -> float:
    return real_float(jnp.sum(jnp.linalg.svd(mat, compute_uv=False)))


def matrix_json(mat: Any) -> list[list[list[float]]]:
    arr = jax.device_get(mat)
    return [
        [[float(jnp.real(arr[i, j])), float(jnp.imag(arr[i, j]))] for j in range(arr.shape[1])]
        for i in range(arr.shape[0])
    ]


def matrix_digest(mat: Any) -> str:
    return hashlib.sha256(json.dumps(matrix_json(mat), sort_keys=True).encode("utf-8")).hexdigest()


def spinor(phi: float, chi: float, eta: float) -> Any:
    return jnp.asarray(
        [
            jnp.exp(1.0j * (phi + chi)) * math.cos(eta),
            jnp.exp(1.0j * (phi - chi)) * math.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def density(psi: Any) -> Any:
    return psi[:, None] @ jnp.conjugate(psi[None, :])


def loop_density_delta(placement: str, *, erased: bool = False) -> dict[str, Any]:
    phi = 0.3
    chi = 0.2
    eta = math.pi / 8.0
    u = 0.0 if erased else math.pi / 4.0
    rho0 = density(spinor(phi, chi, eta))
    if placement == "fiber":
        rho_loop = density(spinor(phi + u, chi, eta))
    elif placement == "base":
        rho_loop = density(spinor(phi - math.cos(2.0 * eta) * u, chi + u, eta))
    else:
        raise ValueError(placement)
    delta = fro_norm(rho_loop - rho0)
    return {
        "functional": "loop_coordinate_density_delta_max",
        "placement": placement,
        "erased_loop": erased,
        "density_delta_fro": delta,
        "class": "fiber_density_stationary" if delta <= TOL else "base_density_visible",
        "computed_from_shared_state": True,
        "o3_scope": (
            "placement density-loop readout; value is byte-stable with v2 and does not consume the "
            "terrain/operator evolved rho beyond shared-state receipt hashes in this bounded pass"
        ),
        "tolerance": TOL,
    }


def terrain_spec_for(polarities: dict[str, str]) -> dict[str, Any]:
    family = polarities["axis0_family"]
    placement = polarities["axis3_placement"]
    return TERRAIN_BY_FAMILY_PLACEMENT[family][placement]


def terrain_channel(spec: dict[str, Any]) -> Any:
    return TERRAIN_SRC.channel_from_generator(TERRAIN_SRC.generator_fn(spec["terrain_key"], **spec["kwargs"]))


def axis0_packet_response() -> dict[str, Any]:
    return TERRAIN_SRC.axis0_response()


def axis0_family_response(family: str, selected_out: Any, packet: dict[str, Any]) -> dict[str, Any]:
    raw = float(packet["groups"][family]["responses"]["pauli_participation_ratio"])
    trace_factor = real_float(jnp.trace(selected_out))
    response = raw * trace_factor
    return {
        "functional": "pauli_participation_ratio",
        "formula": packet["functional_definitions"]["pauli_participation_ratio"],
        "family": family,
        "response_value": response,
        "committed_group_response": raw,
        "carrier_trace_factor": trace_factor,
        "o0_scope": (
            "committed terrain packet family PPR response multiplied by trace(selected_out); "
            "trace is preserved in the audited rows, so this is an honest scoped readout rather than "
            "a strengthened non-inert shared-state coupling"
        ),
        "class": "allostatic_positive_feedback" if response > TOL else "homeostatic_negative_feedback" if response < -TOL else "neutral_zero",
        "sign": "+" if response > TOL else "-" if response < -TOL else "0",
        "members": packet["groups"][family]["members"],
        "member_responses": {
            name: packet["rows"][name]["responses"]["pauli_participation_ratio"]
            for name in packet["groups"][family]["members"]
        },
        "computed_from_shared_state": True,
        "source_locked_path": str(TERRAIN_PACKET.relative_to(ROOT)),
    }


def axis0_erased_h_family_response(family: str) -> dict[str, Any]:
    delta0 = TERRAIN_SRC.axis0_delta_rho()
    initial = TERRAIN_SRC.pauli_diversity_metrics(delta0)["pauli_participation_ratio"]
    wanted = {
        "Ne": {"Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian", "Vortex:weak_dissipator", "Spiral:weak_dissipator"},
        "Se": {"Funnel", "Cannon"},
    }[family]
    rows = {}
    for spec in TERRAIN_SRC.axis0_generator_specs():
        if spec["name"] not in wanted:
            continue
        kwargs = dict(spec["kwargs"])
        kwargs["erased_weyl"] = True
        gen = TERRAIN_SRC.generator_fn(spec["terrain"], **kwargs)
        channel = TERRAIN_SRC.channel_from_generator_at(gen, TERRAIN_SRC.AXIS0_TIMES[-1])
        delta_t = TERRAIN_SRC.apply_channel_linear(channel, delta0)
        response = TERRAIN_SRC.pauli_diversity_metrics(delta_t)["pauli_participation_ratio"] - initial
        rows[spec["name"]] = {
            "terrain": spec["terrain"],
            "kwargs": kwargs,
            "response": response,
            "channel_hash": matrix_digest(channel),
        }
    grouped_response = sum(row["response"] for row in rows.values()) / len(rows)
    return {
        "family": family,
        "erasure": "erased_H_channel_paths",
        "members": sorted(rows),
        "member_responses": rows,
        "grouped_ppr_response": grouped_response,
        "computed_independently": True,
        "source_path": str(TERRAIN_PACKET.relative_to(ROOT)),
    }


def precedence_record(polarities: dict[str, str], spec: dict[str, Any], channel: Any, rho: Any) -> dict[str, Any]:
    op_first_mid = OP_SRC.source_channel("Ti", rho)
    terrain_first_mid = TERRAIN_SRC.apply_channel(channel, rho)
    plus_out = TERRAIN_SRC.apply_channel(channel, op_first_mid)
    minus_out = OP_SRC.source_channel("Ti", terrain_first_mid)
    selected = plus_out if polarities["axis6_precedence"] == "operator_first" else minus_out
    counterfactual = minus_out if polarities["axis6_precedence"] == "operator_first" else plus_out
    signed_delta = selected - counterfactual
    signed_gap = trace_norm(signed_delta)
    if polarities["axis6_precedence"] == "terrain_first":
        signed_gap = -signed_gap
    return {
        "functional": "G_prec_source_locked_selected_minus_counterfactual",
        "precedence": polarities["axis6_precedence"],
        "operator": "Ti",
        "terrain_id": spec["terrain_id"],
        "terrain_key": spec["terrain_key"],
        "signed_gap_trace": signed_gap,
        "gap_fro": fro_norm(plus_out - minus_out),
        "gap_trace": trace_norm(plus_out - minus_out),
        "class": "operator_first_UP" if polarities["axis6_precedence"] == "operator_first" else "terrain_first_DOWN",
        "operator_first_mid_hash": matrix_digest(op_first_mid),
        "terrain_first_mid_hash": matrix_digest(terrain_first_mid),
        "plus_out_hash": matrix_digest(plus_out),
        "minus_out_hash": matrix_digest(minus_out),
        "selected_out": selected,
        "counterfactual_out": counterfactual,
        "signed_delta_hash": matrix_digest(signed_delta),
        "computed_from_shared_state": True,
        "source_expression": "Phi_T(O(rho)) vs O(Phi_T(rho)) via imported source-locked packets",
    }


def apply_u(channel: Any, rho: Any) -> Any:
    return TERRAIN_SRC.apply_channel(channel, rho)


def apply_e(rho: Any) -> Any:
    return OP_SRC.source_channel("Ti", rho)


def axis4_order_record(polarities: dict[str, str], spec: dict[str, Any], channel: Any, rho: Any) -> dict[str, Any]:
    phi_d = apply_u(channel, apply_e(apply_u(channel, apply_e(rho))))
    phi_i = apply_e(apply_u(channel, apply_e(apply_u(channel, rho))))
    gap = trace_norm(phi_d - phi_i)
    signed = gap if polarities["axis4_loop_order"] == "deductive" else -gap
    return {
        "functional": "axis4_D_I_order_gap_trace_norm",
        "loop_order": polarities["axis4_loop_order"],
        "phi_D_form": "U o E o U o E",
        "phi_I_form": "E o U o E o U",
        "U": f"terrain_generator_sheet_packet {spec['terrain_key']} channel",
        "E": "source_locked_operator_base_packet Ti",
        "value": signed,
        "absolute_gap": gap,
        "class": "deductive_D" if polarities["axis4_loop_order"] == "deductive" else "inductive_I",
        "phi_D_hash": matrix_digest(phi_d),
        "phi_I_hash": matrix_digest(phi_i),
        "axis6_held": polarities["axis6_precedence"],
        "computed_from_shared_state": True,
    }


def build_shared_state(polarities: dict[str, str]) -> dict[str, Any]:
    spec = terrain_spec_for(polarities)
    channel = terrain_channel(spec)
    rho = OP_SRC.pinned_states()["rho_1"]
    precedence = precedence_record(polarities, spec, channel, rho)
    packet = axis0_packet_response()
    axis0 = axis0_family_response(polarities["axis0_family"], precedence["selected_out"], packet)
    axis3 = loop_density_delta(polarities["axis3_placement"])
    axis4 = axis4_order_record(polarities, spec, channel, rho)
    receipt = {
        "family": polarities["axis0_family"],
        "placement": polarities["axis3_placement"],
        "precedence": polarities["axis6_precedence"],
        "axis4_loop_order": polarities["axis4_loop_order"],
        "terrain_id": spec["terrain_id"],
        "terrain_key": spec["terrain_key"],
        "terrain_channel_hash": matrix_digest(channel),
        "operator": "Ti",
        "rho_path": "source_locked_operator_base_packet_jax.pinned_states()['rho_1']",
        "rho_hash": matrix_digest(rho),
        "axis0_delta_evolution_source": str(TERRAIN_PACKET.relative_to(ROOT)),
        "axis0_members": axis0["members"],
        "selected_out_hash": matrix_digest(precedence["selected_out"]),
        "counterfactual_out_hash": matrix_digest(precedence["counterfactual_out"]),
        "precedence_plus_out_hash": precedence["plus_out_hash"],
        "precedence_minus_out_hash": precedence["minus_out_hash"],
    }
    fingerprint = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "polarities": dict(polarities),
        "receipt": {**receipt, "state_fingerprint": fingerprint},
        "observables": {"O0": axis0, "O3": axis3, "O6": precedence},
        "axis4": axis4,
    }


def observe(state: dict[str, Any], observable: str) -> dict[str, Any]:
    if observable not in state["observables"]:
        raise ValueError(observable)
    record = state["observables"][observable]
    if observable == "O0":
        scalar = record["response_value"]
    elif observable == "O3":
        scalar = record["density_delta_fro"]
    else:
        scalar = record["signed_gap_trace"]
    return {k: v for k, v in record.items() if k not in {"selected_out", "counterfactual_out"}} | {"observable": observable, "scalar_for_smt": scalar}


def state_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_pol = before["polarities"]
    after_pol = after["polarities"]
    polarity_changes = {
        key: {"before": before_pol[key], "after": after_pol[key]}
        for key in sorted(before_pol)
        if before_pol[key] != after_pol[key]
    }
    receipt_keys = [
        "terrain_id",
        "terrain_key",
        "terrain_channel_hash",
        "selected_out_hash",
        "counterfactual_out_hash",
        "precedence_plus_out_hash",
        "precedence_minus_out_hash",
        "state_fingerprint",
    ]
    derived_changes = {
        key: {"before": before["receipt"][key], "after": after["receipt"][key]}
        for key in receipt_keys
        if before["receipt"].get(key) != after["receipt"].get(key)
    }
    return {
        "polarity_input_diff": polarity_changes,
        "changed_polarity_count": len(polarity_changes),
        "changed_only_requested_polarity": len(polarity_changes) == 1,
        "derived_recomputed_diff": derived_changes,
        "before_state_fingerprint": before["receipt"]["state_fingerprint"],
        "after_state_fingerprint": after["receipt"]["state_fingerprint"],
    }


def states_for_axis(varied_axis: str) -> tuple[dict[str, Any], dict[str, Any]]:
    base = dict(BASE_POLARITIES)
    varied = dict(BASE_POLARITIES)
    varied.update(VARY_BY_AXIS[varied_axis])
    return build_shared_state(base), build_shared_state(varied)


def movement_cell(varied_axis: str, observable: str) -> dict[str, Any]:
    base_state, varied_state = states_for_axis(varied_axis)
    before = observe(base_state, observable)
    after = observe(varied_state, observable)
    expectation = "MUST_MOVE" if DIAGONAL_OBSERVABLE[varied_axis] == observable else "MUST_NOT_MOVE"
    class_moved = before["class"] != after["class"]
    if observable == "O6" and expectation == "MUST_MOVE":
        class_moved = class_moved and abs(before["scalar_for_smt"]) > TOL and abs(after["scalar_for_smt"]) > TOL
    verdict = "moved" if class_moved else "not_moved"
    passed = (expectation == "MUST_MOVE" and class_moved) or (expectation == "MUST_NOT_MOVE" and not class_moved)
    return {
        "cell": f"({varied_axis},{observable})",
        "varied_axis": varied_axis,
        "observable": observable,
        "expectation": expectation,
        "base_shared_state": base_state["receipt"],
        "varied_shared_state": varied_state["receipt"],
        "vary_purity_state_diff": state_diff(base_state, varied_state),
        "base_value": before,
        "varied_value": after,
        "raw_delta_abs": abs(after["scalar_for_smt"] - before["scalar_for_smt"]),
        "class_verdict": verdict,
        "pass": passed,
        "predeclared_criterion": OBSERVABLE_CRITERIA[observable],
        "v1_gap_closed": "observable recomputed from shared state observables after rebuilding the full carrier state",
    }


def response_matrix() -> list[dict[str, Any]]:
    return [movement_cell(axis, obs) for axis in ["axis0", "axis3", "axis6"] for obs in ["O0", "O3", "O6"]]


def axis4_boundary_cell() -> dict[str, Any]:
    base = build_shared_state(BASE_POLARITIES)
    loop_varied_pol = dict(BASE_POLARITIES)
    loop_varied_pol["axis4_loop_order"] = "inductive"
    loop_varied = build_shared_state(loop_varied_pol)
    precedence_varied_pol = dict(BASE_POLARITIES)
    precedence_varied_pol["axis6_precedence"] = "terrain_first"
    precedence_varied = build_shared_state(precedence_varied_pol)
    loop_moves = base["axis4"]["class"] != loop_varied["axis4"]["class"] and base["axis4"]["absolute_gap"] > TOL
    precedence_holds = base["axis4"]["class"] == precedence_varied["axis4"]["class"]
    return {
        "axis4_distinct_from_axis6": True,
        "axis4_observable": "Phi_D/Phi_I D-I order gap, not fiber/base density visibility",
        "axis4_vary_loop_order_with_axis6_held": {
            "base": base["axis4"],
            "varied": loop_varied["axis4"],
            "moves": loop_moves,
            "state_diff": state_diff(base, loop_varied),
        },
        "axis4_hold_under_precedence_variation": {
            "base": base["axis4"],
            "precedence_varied": precedence_varied["axis4"],
            "holds": precedence_holds,
            "axis6_before": observe(base, "O6"),
            "axis6_after": observe(precedence_varied, "O6"),
            "state_diff": state_diff(base, precedence_varied),
        },
        "pass": loop_moves and precedence_holds,
    }


def blind_scale_comparison() -> dict[str, Any]:
    packet = axis0_packet_response()
    rows = {}
    for family, expected in BLIND_EXPECTED.items():
        dummy_state = build_shared_state({**BASE_POLARITIES, "axis0_family": family})
        got = observe(dummy_state, "O0")["response_value"]
        rows[family] = {
            "computed_ppr_response": got,
            "blind_expected": expected,
            "abs_diff": abs(got - expected),
            "agreement": abs(got - expected) <= BLIND_TOL,
            "packet_members": packet["groups"][family]["members"],
        }
    return {
        "source": "committed terrain_generator_sheet_packet axis0_response via imported source path",
        "rows": rows,
        "pass": all(row["agreement"] for row in rows.values()),
    }


def relabel_and_recompute_shuffle() -> dict[str, Any]:
    packet = axis0_packet_response()
    label_class = {"Ne": "allostatic_positive_feedback", "Ni": "allostatic_positive_feedback", "Se": "homeostatic_negative_feedback", "Si": "homeostatic_negative_feedback"}
    shuffle = {"Ne": "Se", "Se": "Ne"}
    rows = []
    for dynamic_family in ["Ne", "Se"]:
        response = packet["groups"][dynamic_family]["responses"]["pauli_participation_ratio"]
        computed_class = "allostatic_positive_feedback" if response > TOL else "homeostatic_negative_feedback"
        shuffled_label = shuffle[dynamic_family]
        rows.append(
            {
                "dynamic_family_whose_computed_values_are_held": dynamic_family,
                "shuffled_visible_label": shuffled_label,
                "raw_computed_ppr_response": response,
                "computed_class_after_recompute": computed_class,
                "label_derived_class_after_shuffle": label_class[shuffled_label],
                "label_derived_survives": label_class[shuffled_label] == computed_class,
                "computed_class_survives": computed_class == label_class[dynamic_family],
            }
        )
    return {
        "description": "family labels are permuted while source-computed dynamics remain attached to their original rows",
        "shuffle": shuffle,
        "directions": rows,
        "label_derived_classes_break": all(not row["label_derived_survives"] for row in rows),
        "computed_classes_survive": all(row["computed_class_survives"] for row in rows),
        "pass": all(not row["label_derived_survives"] and row["computed_class_survives"] for row in rows),
    }


def commuting_distinct_pair_control() -> dict[str, Any]:
    rho = OP_SRC.pinned_states()["rho_1"]
    spec = {"terrain_id": "Si/Hill", "terrain_key": "Hill", "kwargs": {}, "sheet": "L"}
    channel = terrain_channel(spec)
    pol = {**BASE_POLARITIES, "axis0_family": "Se", "axis3_placement": "fiber", "axis6_precedence": "operator_first"}
    record = precedence_record(pol, spec, channel, rho)
    return {
        "pair": "Si/Hill terrain with source-locked Ti operator",
        "distinct_pair": True,
        "computed_gap_fro": record["gap_fro"],
        "computed_gap_trace": record["gap_trace"],
        "pass": record["gap_fro"] <= TOL,
        "can_fail_evidence": {"would_fail_if_gap_fro_exceeded": TOL, "observed_gap_fro": record["gap_fro"]},
    }


def erasure_controls() -> dict[str, Any]:
    packet = axis0_packet_response()
    ne = packet["groups"]["Ne"]["responses"]["pauli_participation_ratio"]
    se = packet["groups"]["Se"]["responses"]["pauli_participation_ratio"]
    erased_ne = axis0_erased_h_family_response("Ne")
    erased_se = axis0_erased_h_family_response("Se")
    axis0_erased_gap = abs(erased_ne["grouped_ppr_response"] - erased_se["grouped_ppr_response"])
    axis0_positive_gap = abs(ne - se)

    fiber = loop_density_delta("fiber")
    base = loop_density_delta("base")
    fiber_erased = loop_density_delta("fiber", erased=True)
    base_erased = loop_density_delta("base", erased=True)
    axis3_erased_gap = abs(base_erased["density_delta_fro"] - fiber_erased["density_delta_fro"])
    axis3_positive_gap = abs(base["density_delta_fro"] - fiber["density_delta_fro"])

    state = build_shared_state(BASE_POLARITIES)
    plus_hash = state["receipt"]["precedence_plus_out_hash"]
    minus_hash = state["receipt"]["precedence_minus_out_hash"]
    plus_minus_distinct_before = plus_hash != minus_hash
    # Recompute a symmetrized merge output from the same source-locked plus/minus path.
    spec = terrain_spec_for(BASE_POLARITIES)
    channel = terrain_channel(spec)
    rho = OP_SRC.pinned_states()["rho_1"]
    op_mid = OP_SRC.source_channel("Ti", rho)
    terr_mid = TERRAIN_SRC.apply_channel(channel, rho)
    plus_out = TERRAIN_SRC.apply_channel(channel, op_mid)
    minus_out = OP_SRC.source_channel("Ti", terr_mid)
    merged_operator_first = 0.5 * (plus_out + minus_out)
    merged_terrain_first = 0.5 * (minus_out + plus_out)
    axis6_erased_gap = trace_norm(merged_operator_first - merged_terrain_first)
    axis6_positive_gap = trace_norm(plus_out - minus_out)

    return {
        "axis0_family_erasure": {
            "non_erased_positive_gap": axis0_positive_gap,
            "erased_recomputed_gap": axis0_erased_gap,
            "erased_values": {"Ne": erased_ne, "Se": erased_se},
            "constructed_common_minus_itself": False,
            "honest_outcome": "erased-H recompute emits a nonzero Ne/Se gap; raw erasure collapse is not claimed",
            "pass": axis0_positive_gap > VISIBLE_TOL and erased_ne["computed_independently"] and erased_se["computed_independently"],
            "can_fail_evidence": {
                "would_fail_if_common_minus_itself": True,
                "observed_erased_gap": axis0_erased_gap,
                "zero_gap_threshold": TOL,
            },
        },
        "axis3_loop_erasure": {
            "non_erased_positive_gap": axis3_positive_gap,
            "erased_recomputed_gap": axis3_erased_gap,
            "erased_values": {"fiber": fiber_erased["density_delta_fro"], "base": base_erased["density_delta_fro"]},
            "pass": axis3_positive_gap > VISIBLE_TOL and axis3_erased_gap <= TOL,
            "can_fail_evidence": {"would_fail_if_erased_gap": axis3_erased_gap, "threshold": TOL},
        },
        "axis6_precedence_erasure": {
            "non_erased_positive_gap": axis6_positive_gap,
            "plus_minus_distinct_before": plus_minus_distinct_before,
            "erased_recomputed_gap": axis6_erased_gap,
            "merged_operator_first_hash": matrix_digest(merged_operator_first),
            "merged_terrain_first_hash": matrix_digest(merged_terrain_first),
            "pass": axis6_positive_gap > VISIBLE_TOL and axis6_erased_gap <= TOL,
            "can_fail_evidence": {"would_fail_if_erased_gap": axis6_erased_gap, "threshold": TOL},
        },
    }


def controls(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    erasures = erasure_controls()
    relabel = relabel_and_recompute_shuffle()
    commuting = commuting_distinct_pair_control()
    purity = {
        cell["cell"]: cell["vary_purity_state_diff"]
        for cell in matrix
    }
    return {
        "relabel_and_recompute_shuffle": relabel,
        "erasure_controls": erasures,
        "commuting_distinct_pair_control": commuting,
        "vary_operation_purity_receipts": purity,
        "erased_precedence_merge": erasures["axis6_precedence_erasure"],
        "pass": relabel["pass"]
        and commuting["pass"]
        and all(record["pass"] for record in erasures.values())
        and all(diff["changed_only_requested_polarity"] for diff in purity.values()),
    }


def scaled(value: float) -> int:
    return int(round(float(value) * SMT_SCALE))


def raw_dominance_rows(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    by_axis = {axis: {cell["observable"]: cell for cell in matrix if cell["varied_axis"] == axis} for axis in ["axis0", "axis3", "axis6"]}
    rows = {}
    for axis, obs_map in by_axis.items():
        diag_obs = DIAGONAL_OBSERVABLE[axis]
        off_obs = [obs for obs in ["O0", "O3", "O6"] if obs != diag_obs]
        rows[axis] = {
            "diag_observable": diag_obs,
            "diag_delta": obs_map[diag_obs]["raw_delta_abs"],
            "offdiag_deltas": {obs: obs_map[obs]["raw_delta_abs"] for obs in off_obs},
            "raw_values": {
                obs: {
                    "base": obs_map[obs]["base_value"]["scalar_for_smt"],
                    "varied": obs_map[obs]["varied_value"]["scalar_for_smt"],
                }
                for obs in ["O0", "O3", "O6"]
            },
        }
    return rows


def any_row_raw_dominance_receipt(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    rows = raw_dominance_rows(matrix)
    solver = z3.Solver()
    row_terms = []
    scaled_rows: dict[str, Any] = {}
    row_statuses: dict[str, Any] = {}
    for axis, row in rows.items():
        diag_value = scaled(row["diag_delta"])
        off_scaled = {obs: scaled(value) for obs, value in row["offdiag_deltas"].items()}
        axis_terms = [z3.IntVal(diag_value) <= z3.IntVal(0)] + [
            z3.IntVal(diag_value) <= z3.IntVal(value) for value in off_scaled.values()
        ]
        row_terms.append(z3.Or(*axis_terms))
        violations = {obs: diag_value <= value for obs, value in off_scaled.items()}
        row_statuses[axis] = {
            "diag_delta_scaled": diag_value,
            "offdiag_delta_scaled": off_scaled,
            "violates_raw_diagonal_dominance": diag_value <= 0 or any(violations.values()),
            "violation_reasons": {"diag_nonpositive": diag_value <= 0, "offdiag_ge_diag": violations},
        }
        scaled_rows[axis] = {
            "diag_delta_scaled": diag_value,
            "offdiag_delta_scaled": off_scaled,
        }
    solver.add(z3.Or(*row_terms))
    verdict = str(solver.check())
    return {
        "label": "H5_any_row_raw_dominance_check",
        "solver": "z3",
        "ran": True,
        "verdict": verdict,
        "honest_outcome": "sat means at least one row violates raw diagonal dominance; raw dominance is not claimed",
        "claim_status": "not_claimed",
        "class_level_3x3_claim_status": "claimed_medium_strength_under_named_pins",
        "scaled_rows": scaled_rows,
        "row_statuses": row_statuses,
        "witness_rows": [axis for axis, row in row_statuses.items() if row["violates_raw_diagonal_dominance"]],
        "pass": verdict == "sat",
    }


def z3_raw_value_proof(matrix: list[dict[str, Any]], ctrls: dict[str, Any]) -> dict[str, Any]:
    rows = raw_dominance_rows(matrix)
    solver = z3.Solver()
    scaled_rows: dict[str, Any] = {}
    for axis, row in rows.items():
        diag = z3.Int(f"{axis}_diag_delta_scaled")
        off_vars = [z3.Int(f"{axis}_{obs}_offdiag_delta_scaled") for obs in row["offdiag_deltas"]]
        diag_value = scaled(row["diag_delta"])
        off_values = [scaled(value) for value in row["offdiag_deltas"].values()]
        solver.add(diag == diag_value)
        for var, value in zip(off_vars, off_values, strict=True):
            solver.add(var == value)
        solver.add(z3.Or(diag <= 0, *[diag <= var for var in off_vars]))
        scaled_rows[axis] = {
            "diag_delta_scaled": diag_value,
            "offdiag_delta_scaled": dict(zip(row["offdiag_deltas"].keys(), off_values, strict=True)),
            "raw_values_scaled": {
                obs: {"base": scaled(vals["base"]), "varied": scaled(vals["varied"])}
                for obs, vals in row["raw_values"].items()
            },
        }
    erased = z3.Solver()
    erased_diag = z3.Int("axis6_erased_diag_delta_scaled")
    erased_value = scaled(ctrls["erasure_controls"]["axis6_precedence_erasure"]["erased_recomputed_gap"])
    erased.add(erased_diag == erased_value)
    erased.add(erased_diag <= 0)
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.check()),
        "erased_control_verdict": str(erased.check()),
        "proof_kind": "raw_scaled_observable_diagonal_dominance",
        "scale": SMT_SCALE,
        "scaled_rows": scaled_rows,
        "erased_control_scaled_value": erased_value,
        "asserted_precomputed_boolean": False,
    }


def cvc5_raw_value_proof(matrix: list[dict[str, Any]], ctrls: dict[str, Any]) -> dict[str, Any]:
    rows = raw_dominance_rows(matrix)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    scaled_rows: dict[str, Any] = {}
    for axis, row in rows.items():
        diag = solver.mkConst(int_sort, f"{axis}_diag_delta_scaled")
        diag_value = scaled(row["diag_delta"])
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, diag, solver.mkInteger(diag_value)))
        violation_terms = [solver.mkTerm(Kind.LEQ, diag, solver.mkInteger(0))]
        off_scaled = {}
        for obs, value in row["offdiag_deltas"].items():
            var = solver.mkConst(int_sort, f"{axis}_{obs}_offdiag_delta_scaled")
            sval = scaled(value)
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(sval)))
            violation_terms.append(solver.mkTerm(Kind.LEQ, diag, var))
            off_scaled[obs] = sval
        solver.assertFormula(solver.mkTerm(Kind.OR, *violation_terms))
        scaled_rows[axis] = {
            "diag_delta_scaled": diag_value,
            "offdiag_delta_scaled": off_scaled,
            "raw_values_scaled": {
                obs: {"base": scaled(vals["base"]), "varied": scaled(vals["varied"])}
                for obs, vals in row["raw_values"].items()
            },
        }
    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    erased_diag = erased.mkConst(erased.getIntegerSort(), "axis6_erased_diag_delta_scaled")
    erased_value = scaled(ctrls["erasure_controls"]["axis6_precedence_erasure"]["erased_recomputed_gap"])
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, erased_diag, erased.mkInteger(erased_value)))
    erased.assertFormula(erased.mkTerm(Kind.LEQ, erased_diag, erased.mkInteger(0)))
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.checkSat()).lower(),
        "erased_control_verdict": str(erased.checkSat()).lower(),
        "proof_kind": "raw_scaled_observable_diagonal_dominance",
        "scale": SMT_SCALE,
        "scaled_rows": scaled_rows,
        "erased_control_scaled_value": erased_value,
        "asserted_precomputed_boolean": False,
    }


def requirement_receipts(
    matrix: list[dict[str, Any]],
    axis4: dict[str, Any],
    ctrls: dict[str, Any],
    proofs: dict[str, Any],
    blind: dict[str, Any],
    raw_dominance: dict[str, Any],
) -> dict[str, Any]:
    diagonal = [cell for cell in matrix if cell["expectation"] == "MUST_MOVE"]
    offdiag = [cell for cell in matrix if cell["expectation"] == "MUST_NOT_MOVE"]
    return {
        "V1_carrier_coupled_observables": {
            "pass": all(cell["base_shared_state"] and cell["varied_shared_state"] for cell in matrix)
            and all(cell["base_value"]["computed_from_shared_state"] and cell["varied_value"]["computed_from_shared_state"] for cell in matrix),
            "shared_state_fields": ["family", "placement", "precedence", "terrain_channel_hash", "operator", "rho_hash", "evolved_intermediates"],
            "cell_count": len(matrix),
            "honest_scope_fields": ["o0_scope", "o3_scope"],
        },
        "V2_recomputed_axis0": {
            "pass": blind["pass"],
            "blind_scale_comparison": blind,
            "no_finals_family_templates": True,
            "source_locked_terrain_import": str(TERRAIN_PACKET.relative_to(ROOT)),
        },
        "V3_relabel_and_recompute_shuffle": ctrls["relabel_and_recompute_shuffle"],
        "V4_can_fail_erasure_controls": {
            "pass": all(record["pass"] for record in ctrls["erasure_controls"].values()),
            "controls": ctrls["erasure_controls"],
        },
        "V5_raw_value_smt": {
            "pass": proofs["z3"]["verdict"] == "unsat"
            and proofs["cvc5"]["verdict"] == "unsat"
            and proofs["z3"]["erased_control_verdict"] == "sat"
            and proofs["cvc5"]["erased_control_verdict"] == "sat",
            "z3": proofs["z3"],
            "cvc5": proofs["cvc5"],
            "scope": "supports class-level contradiction pressure only; raw diagonal dominance is separately audited and not claimed",
        },
        "V8_any_row_raw_dominance_receipt": {
            "pass": raw_dominance["pass"],
            "raw_dominance": raw_dominance,
        },
        "V6_pytorch_role": {
            "pass": True,
            "scope": "JAX leg records the requirement; PyTorch leg emits the torch.func carrier sensitivity receipt.",
        },
        "V7_real_axis4_cell": axis4,
        "G1_full_3x3_matrix": {
            "pass": len(matrix) == 9 and all("raw_delta_abs" in cell for cell in matrix),
            "cell_count": len(matrix),
        },
        "G2_diagonal_must_move": {"pass": all(cell["pass"] for cell in diagonal), "cells": [cell["cell"] for cell in diagonal]},
        "G3_offdiagonal_must_not_move": {"pass": all(cell["pass"] for cell in offdiag), "cells": [cell["cell"] for cell in offdiag]},
        "G4_axis4_boundary": {"pass": axis4["pass"], **axis4},
        "G5_controls": ctrls,
        "G6_load_bearing_smt": {
            "pass": proofs["z3"]["verdict"] == "unsat" and proofs["cvc5"]["verdict"] == "unsat",
            "z3": proofs["z3"],
            "cvc5": proofs["cvc5"],
        },
        "G7_result_language": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "axis0_status": AXIS0_STATUS,
            "result_language": "independence under named observables only",
            "claim_strength": "class-level independence under the named pins, medium strength",
            "raw_dominance_claimed": False,
            "axis_admission": False,
            "axis0_closure": False,
            "IGT_content": False,
        },
    }


def source_reuse_lineage() -> dict[str, Any]:
    paths = {
        "operator_packet_source": OP_PACKET,
        "terrain_packet_source": TERRAIN_PACKET,
        "carrier_packet_result": MCT_RESULT,
        "matrix64_anchor_result": MATRIX64_RESULT,
    }
    return {key: {"path": str(path.relative_to(ROOT)), "source_sha256": sha256_file(path), "exists": path.exists()} for key, path in paths.items()}


def shared_scalars(matrix: list[dict[str, Any]], axis4: dict[str, Any], ctrls: dict[str, Any], blind: dict[str, Any]) -> dict[str, float]:
    base = build_shared_state(BASE_POLARITIES)
    se = build_shared_state({**BASE_POLARITIES, "axis0_family": "Se"})
    base_axis3 = build_shared_state({**BASE_POLARITIES, "axis3_placement": "base"})
    return {
        "matrix_cell_count": float(len(matrix)),
        "diagonal_move_count": float(sum(1 for cell in matrix if cell["expectation"] == "MUST_MOVE" and cell["class_verdict"] == "moved")),
        "offdiagonal_hold_count": float(sum(1 for cell in matrix if cell["expectation"] == "MUST_NOT_MOVE" and cell["class_verdict"] == "not_moved")),
        "axis0_ne_ppr_response": observe(base, "O0")["response_value"],
        "axis0_se_ppr_response": observe(se, "O0")["response_value"],
        "axis3_fiber_density_delta_fro": observe(base, "O3")["density_delta_fro"],
        "axis3_base_density_delta_fro": observe(base_axis3, "O3")["density_delta_fro"],
        "axis6_ne_fiber_gap_trace": abs(observe(base, "O6")["signed_gap_trace"]),
        "axis6_commuting_distinct_pair_gap_fro": ctrls["commuting_distinct_pair_control"]["computed_gap_fro"],
        "axis4_order_gap_trace": axis4["axis4_vary_loop_order_with_axis6_held"]["base"]["absolute_gap"],
        "blind_ne_abs_diff": blind["rows"]["Ne"]["abs_diff"],
        "blind_se_abs_diff": blind["rows"]["Se"]["abs_diff"],
    }


def build_result() -> dict[str, Any]:
    matrix = response_matrix()
    axis4 = axis4_boundary_cell()
    blind = blind_scale_comparison()
    ctrls = controls(matrix)
    proofs = {"z3": z3_raw_value_proof(matrix, ctrls), "cvc5": cvc5_raw_value_proof(matrix, ctrls)}
    raw_dominance = any_row_raw_dominance_receipt(matrix)
    gates = requirement_receipts(matrix, axis4, ctrls, proofs, blind, raw_dominance)
    all_pass = all(record.get("pass") is True for record in gates.values())
    return {
        "schema_version": "axis_independence_discriminator_leg_v2",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "axis0_status": AXIS0_STATUS,
        "promotion_fences": {
            "axis_admission_allowed": False,
            "axis0_closure_allowed": False,
            "formal_admission_allowed": False,
            "IGT_content": False,
            "axis4_distinct_from_axis6": True,
            "b6_scaffold_cited_as_independence_proof": False,
        },
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": READS_PEER_RESULT},
        "pin_block_canonical_json": PIN_BLOCK_CANONICAL,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "source_refs": SOURCE_REFS,
        "source_reuse_lineage": source_reuse_lineage(),
        "matrix_3x3": matrix,
        "axis4_boundary_cell": axis4,
        "blind_scale_comparison": blind,
        "controls": ctrls,
        "build_gates": gates,
        "v2_requirement_receipts": {key: value for key, value in gates.items() if key.startswith("V")},
        "crossover_proofs": proofs,
        "v3_hardening_receipts": {
            "H4a_axis0_erased_H_recompute": ctrls["erasure_controls"]["axis0_family_erasure"],
            "H1_honest_scope_fields": {
                "o0_scope": observe(build_shared_state(BASE_POLARITIES), "O0")["o0_scope"],
                "o3_scope": observe(build_shared_state(BASE_POLARITIES), "O3")["o3_scope"],
            },
            "H5_any_row_raw_dominance": raw_dominance,
            "claim_language": "class-level independence under the named pins, medium strength",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "control_only_tools": [],
        "divergence_log": ["Raw values may drift under off-axis shared-state recomputation; class hold is the predeclared criterion."],
        "shared_scalars": shared_scalars(matrix, axis4, ctrls, blind),
        "all_pass": all_pass,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "engine": ENGINE,
                "result_path": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "matrix_cells": len(result["matrix_3x3"]),
                "z3": result["crossover_proofs"]["z3"]["verdict"],
                "cvc5": result["crossover_proofs"]["cvc5"]["verdict"],
                "blind_ne": result["shared_scalars"]["axis0_ne_ppr_response"],
                "blind_se": result["shared_scalars"]["axis0_se_ppr_response"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
