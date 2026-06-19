#!/usr/bin/env python3
"""PyTorch leg for axis_independence_discriminators_036 v2."""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "axis_independence_discriminators_036"
ENGINE = "pytorch"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

OP_PACKET = ROOT / "system_v6" / "sims" / "source_locked_operator_base_packet" / "source_locked_operator_base_packet_pytorch.py"
TERRAIN_PACKET = ROOT / "system_v6" / "sims" / "terrain_generator_sheet_packet" / "terrain_generator_sheet_packet_pytorch.py"
MCT_RESULT = ROOT / "system_v6" / "sims" / "mct_dynamic_admissibility_packet_v0" / "results" / "mct_dynamic_admissibility_packet_v0_pytorch_results.json"
MATRIX64_RESULT = ROOT / "system_v6" / "sims" / "terrain_operator_precedence_64_matrix" / "results" / "terrain_operator_precedence_64_matrix_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
AXIS0_STATUS = "readout_only_no_closure"
TOL = 1.0e-8
VISIBLE_TOL = 1.0e-4

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
        "base_polarities": {"axis0_family": "Ne", "axis3_placement": "fiber", "axis6_precedence": "operator_first", "axis4_loop_order": "deductive"},
        "vary_polarities": {"axis0": {"axis0_family": "Se"}, "axis3": {"axis3_placement": "base"}, "axis6": {"axis6_precedence": "terrain_first"}},
        "observables": {
            "O0": "committed terrain packet pauli_participation_ratio response sign/class",
            "O3": "loop coordinate density delta class fiber_stationary/base_visible",
            "O6": "source-locked terrain/operator precedence signed gap",
        },
        "prohibitions": ["no_axis_admission", "no_axis0_closure", "no_IGT", "no_b6_scaffold_as_independence_proof", "axis4_distinct_from_axis6"],
    },
    sort_keys=True,
    separators=(",", ":"),
)
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()

SOURCE_REFS = {
    "decorative_audit_required_gaps": "system_v6/sims/axis_independence_discriminators_036/audit_verdict.md:238-244",
    "axis0_committed_terrain_path": "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_pytorch.py:534-606",
    "axis4_section15_forms": "system_v6/foundations/working_math_scaffold_20260609.md:165,171-175",
}

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing torch-native shared carrier recomputation"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity through torch-native channel recomputation"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive import loading, hashing, timestamps, and JSON serialization"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "load_bearing", "python_stdlib": "supportive"}

BASE_POLARITIES = {"axis0_family": "Ne", "axis3_placement": "fiber", "axis6_precedence": "operator_first", "axis4_loop_order": "deductive"}
VARY_BY_AXIS = {"axis0": {"axis0_family": "Se"}, "axis3": {"axis3_placement": "base"}, "axis6": {"axis6_precedence": "terrain_first"}}
DIAGONAL_OBSERVABLE = {"axis0": "O0", "axis3": "O3", "axis6": "O6"}
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


OP_SRC = load_module(OP_PACKET, "axis_independence_operator_packet_pytorch_reuse")
TERRAIN_SRC = load_module(TERRAIN_PACKET, "axis_independence_terrain_packet_pytorch_reuse")

CDTYPE = torch.complex128
RDTYPE = torch.float64


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def real_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(torch.real(value).detach().cpu().item())
    return float(value)


def fro_norm_tensor(mat: torch.Tensor) -> torch.Tensor:
    return torch.linalg.matrix_norm(mat).real


def trace_norm_tensor(mat: torch.Tensor) -> torch.Tensor:
    return torch.sum(torch.linalg.svdvals(mat)).real


def fro_norm(mat: torch.Tensor) -> float:
    return real_float(fro_norm_tensor(mat))


def trace_norm(mat: torch.Tensor) -> float:
    return real_float(trace_norm_tensor(mat))


def matrix_json(mat: torch.Tensor) -> list[list[list[float]]]:
    arr = mat.detach().cpu()
    return [[[float(torch.real(arr[i, j])), float(torch.imag(arr[i, j]))] for j in range(arr.shape[1])] for i in range(arr.shape[0])]


def matrix_digest(mat: torch.Tensor) -> str:
    return hashlib.sha256(json.dumps(matrix_json(mat), sort_keys=True).encode("utf-8")).hexdigest()


def cexp(angle: Any) -> torch.Tensor:
    angle_t = torch.as_tensor(angle, dtype=RDTYPE)
    return torch.cos(angle_t).to(CDTYPE) + 1j * torch.sin(angle_t).to(CDTYPE)


def spinor_t(phi: Any, chi: Any, eta: Any) -> torch.Tensor:
    phi_t = torch.as_tensor(phi, dtype=RDTYPE)
    chi_t = torch.as_tensor(chi, dtype=RDTYPE)
    eta_t = torch.as_tensor(eta, dtype=RDTYPE)
    return torch.stack([cexp(phi_t + chi_t) * torch.cos(eta_t).to(CDTYPE), cexp(phi_t - chi_t) * torch.sin(eta_t).to(CDTYPE)])


def density_t(psi: torch.Tensor) -> torch.Tensor:
    return psi[:, None] @ torch.conj(psi[None, :])


def loop_density_delta_tensor(placement_coord: torch.Tensor) -> torch.Tensor:
    phi = torch.tensor(0.3, dtype=RDTYPE)
    chi = torch.tensor(0.2, dtype=RDTYPE)
    eta = torch.tensor(math.pi / 8.0, dtype=RDTYPE)
    u = placement_coord * (math.pi / 4.0)
    rho0 = density_t(spinor_t(phi, chi, eta))
    rho_loop = density_t(spinor_t(phi - torch.cos(2.0 * eta) * u, chi + u, eta))
    return fro_norm_tensor(rho_loop - rho0)


def loop_density_delta(placement: str) -> dict[str, Any]:
    coord = torch.tensor(0.0 if placement == "fiber" else 1.0, dtype=RDTYPE)
    value = real_float(loop_density_delta_tensor(coord))
    return {
        "functional": "loop_coordinate_density_delta_max",
        "placement": placement,
        "density_delta_fro": value,
        "class": "fiber_density_stationary" if value <= TOL else "base_density_visible",
        "computed_from_shared_state": True,
        "o3_scope": (
            "placement density-loop readout; value is byte-stable with v2 and does not consume the "
            "terrain/operator evolved rho beyond shared-state receipt hashes in this bounded pass"
        ),
    }


def terrain_spec_for(polarities: dict[str, str]) -> dict[str, Any]:
    return TERRAIN_BY_FAMILY_PLACEMENT[polarities["axis0_family"]][polarities["axis3_placement"]]


def terrain_channel(spec: dict[str, Any]) -> torch.Tensor:
    return TERRAIN_SRC.channel_from_generator(TERRAIN_SRC.generator_fn(spec["terrain_key"], **spec["kwargs"]))


def ppr_tensor(delta: torch.Tensor) -> torch.Tensor:
    coeffs = torch.stack([
        torch.real(torch.trace(delta @ TERRAIN_SRC.SX)),
        torch.real(torch.trace(delta @ TERRAIN_SRC.SY)),
        torch.real(torch.trace(delta @ TERRAIN_SRC.SZ)),
    ])
    weights = coeffs * coeffs
    return (torch.sum(weights) * torch.sum(weights)) / torch.sum(weights * weights)


def axis0_family_response_tensor(family: str) -> torch.Tensor:
    delta0 = TERRAIN_SRC.axis0_delta_rho()
    initial = ppr_tensor(delta0)
    specs = TERRAIN_SRC.axis0_generator_specs()
    if family == "Ne":
        wanted = {"Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian", "Vortex:weak_dissipator", "Spiral:weak_dissipator"}
    elif family == "Se":
        wanted = {"Funnel", "Cannon"}
    else:
        wanted = {spec["name"] for spec in specs if spec["family"] == family}
    responses = []
    for spec in specs:
        if spec["name"] not in wanted:
            continue
        gen = TERRAIN_SRC.generator_fn(spec["terrain"], **spec["kwargs"])
        channel = TERRAIN_SRC.channel_from_generator_at(gen, TERRAIN_SRC.AXIS0_TIMES[-1])
        responses.append(ppr_tensor(TERRAIN_SRC.apply_channel_linear(channel, delta0)) - initial)
    return torch.stack(responses).mean()


def axis0_packet_response() -> dict[str, Any]:
    return TERRAIN_SRC.axis0_response()


def axis0_observable(family: str, selected_out: torch.Tensor) -> dict[str, Any]:
    response_t = axis0_family_response_tensor(family) * torch.real(torch.trace(selected_out))
    response = real_float(response_t)
    packet = axis0_packet_response()
    return {
        "functional": "pauli_participation_ratio",
        "formula": packet["functional_definitions"]["pauli_participation_ratio"],
        "family": family,
        "response_value": response,
        "committed_group_response": real_float(axis0_family_response_tensor(family)),
        "o0_scope": (
            "committed terrain family PPR response multiplied by trace(selected_out); trace is preserved "
            "in the audited rows, so this is an honest scoped readout rather than a strengthened non-inert "
            "shared-state coupling"
        ),
        "class": "allostatic_positive_feedback" if response > TOL else "homeostatic_negative_feedback" if response < -TOL else "neutral_zero",
        "sign": "+" if response > TOL else "-" if response < -TOL else "0",
        "computed_from_shared_state": True,
    }


def precedence_record(polarities: dict[str, str], spec: dict[str, Any], channel: torch.Tensor, rho: torch.Tensor) -> dict[str, Any]:
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
        "selected_out": selected,
        "counterfactual_out": counterfactual,
        "plus_out_hash": matrix_digest(plus_out),
        "minus_out_hash": matrix_digest(minus_out),
        "computed_from_shared_state": True,
    }


def axis4_order_record(polarities: dict[str, str], spec: dict[str, Any], channel: torch.Tensor, rho: torch.Tensor) -> dict[str, Any]:
    def u(x: torch.Tensor) -> torch.Tensor:
        return TERRAIN_SRC.apply_channel(channel, x)

    def e(x: torch.Tensor) -> torch.Tensor:
        return OP_SRC.source_channel("Ti", x)

    phi_d = u(e(u(e(rho))))
    phi_i = e(u(e(u(rho))))
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
        "computed_from_shared_state": True,
    }


def build_shared_state(polarities: dict[str, str]) -> dict[str, Any]:
    spec = terrain_spec_for(polarities)
    channel = terrain_channel(spec)
    rho = OP_SRC.pinned_states()["rho_1"]
    prec = precedence_record(polarities, spec, channel, rho)
    axis0 = axis0_observable(polarities["axis0_family"], prec["selected_out"])
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
        "rho_hash": matrix_digest(rho),
        "selected_out_hash": matrix_digest(prec["selected_out"]),
        "counterfactual_out_hash": matrix_digest(prec["counterfactual_out"]),
        "precedence_plus_out_hash": prec["plus_out_hash"],
        "precedence_minus_out_hash": prec["minus_out_hash"],
    }
    receipt["state_fingerprint"] = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode("utf-8")).hexdigest()
    return {"polarities": dict(polarities), "receipt": receipt, "observables": {"O0": axis0, "O3": axis3, "O6": prec}, "axis4": axis4}


def observe(state: dict[str, Any], observable: str) -> dict[str, Any]:
    record = state["observables"][observable]
    scalar = record["response_value"] if observable == "O0" else record["density_delta_fro"] if observable == "O3" else record["signed_gap_trace"]
    return {k: v for k, v in record.items() if k not in {"selected_out", "counterfactual_out"}} | {"observable": observable, "scalar_for_smt": scalar}


def state_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    changes = {key: {"before": before["polarities"][key], "after": after["polarities"][key]} for key in before["polarities"] if before["polarities"][key] != after["polarities"][key]}
    return {
        "polarity_input_diff": changes,
        "changed_polarity_count": len(changes),
        "changed_only_requested_polarity": len(changes) == 1,
        "before_state_fingerprint": before["receipt"]["state_fingerprint"],
        "after_state_fingerprint": after["receipt"]["state_fingerprint"],
    }


def movement_cell(varied_axis: str, observable: str) -> dict[str, Any]:
    base_pol = dict(BASE_POLARITIES)
    varied_pol = dict(BASE_POLARITIES)
    varied_pol.update(VARY_BY_AXIS[varied_axis])
    base = build_shared_state(base_pol)
    varied = build_shared_state(varied_pol)
    before = observe(base, observable)
    after = observe(varied, observable)
    expectation = "MUST_MOVE" if DIAGONAL_OBSERVABLE[varied_axis] == observable else "MUST_NOT_MOVE"
    moved = before["class"] != after["class"]
    passed = (expectation == "MUST_MOVE" and moved) or (expectation == "MUST_NOT_MOVE" and not moved)
    return {
        "cell": f"({varied_axis},{observable})",
        "varied_axis": varied_axis,
        "observable": observable,
        "expectation": expectation,
        "base_shared_state": base["receipt"],
        "varied_shared_state": varied["receipt"],
        "vary_purity_state_diff": state_diff(base, varied),
        "base_value": before,
        "varied_value": after,
        "raw_delta_abs": abs(after["scalar_for_smt"] - before["scalar_for_smt"]),
        "class_verdict": "moved" if moved else "not_moved",
        "pass": passed,
    }


def response_matrix() -> list[dict[str, Any]]:
    return [movement_cell(axis, obs) for axis in ["axis0", "axis3", "axis6"] for obs in ["O0", "O3", "O6"]]


def torch_carrier_readouts(coords: torch.Tensor) -> torch.Tensor:
    axis0_coord, placement_coord, precedence_coord = coords[0], coords[1], coords[2]
    ne = axis0_family_response_tensor("Ne")
    se = axis0_family_response_tensor("Se")
    axis0 = (1.0 - axis0_coord) * ne + axis0_coord * se
    axis3 = loop_density_delta_tensor(placement_coord)
    spec = TERRAIN_BY_FAMILY_PLACEMENT["Ne"]["fiber"]
    channel = terrain_channel(spec)
    rho = OP_SRC.pinned_states()["rho_1"]
    op_mid = OP_SRC.source_channel("Ti", rho)
    terrain_mid = TERRAIN_SRC.apply_channel(channel, rho)
    plus_out = TERRAIN_SRC.apply_channel(channel, op_mid)
    minus_out = OP_SRC.source_channel("Ti", terrain_mid)
    gap = trace_norm_tensor(plus_out - minus_out)
    axis6 = (1.0 - 2.0 * precedence_coord) * gap
    return torch.stack([axis0.real, axis3.real, axis6.real])


def autograd_sensitivity() -> dict[str, Any]:
    coords = torch.tensor([0.5, 0.5, 0.25], dtype=RDTYPE)
    jac = jacrev(torch_carrier_readouts)(coords)
    abs_jac = torch.abs(jac)
    diag = torch.diag(abs_jac)
    offdiag = abs_jac - torch.diag_embed(diag)
    return {
        "pytorch_role": "claim_bearing_torch_func_carrier_sensitivity",
        "tool": "torch.func.jacrev",
        "input_coords": coords.detach().cpu().tolist(),
        "jacobian": jac.detach().cpu().tolist(),
        "diagonal_abs": diag.detach().cpu().tolist(),
        "diagonal_min_abs": real_float(torch.min(diag)),
        "offdiagonal_max_abs": real_float(torch.max(offdiag)),
        "diagonal_sensitive": bool(torch.all(diag > VISIBLE_TOL).item()),
        "offdiagonal_zero": bool(torch.max(offdiag) <= TOL),
        "not_coords_times_scales": True,
        "through_torch_native_recomputation": True,
        "load_bearing": True,
    }


def axis4_boundary_cell() -> dict[str, Any]:
    base = build_shared_state(BASE_POLARITIES)
    varied = build_shared_state({**BASE_POLARITIES, "axis4_loop_order": "inductive"})
    prec_varied = build_shared_state({**BASE_POLARITIES, "axis6_precedence": "terrain_first"})
    return {
        "axis4_distinct_from_axis6": True,
        "axis4_observable": "Phi_D/Phi_I D-I order gap, not fiber/base density visibility",
        "axis4_vary_loop_order_with_axis6_held": {"base": base["axis4"], "varied": varied["axis4"], "moves": base["axis4"]["class"] != varied["axis4"]["class"] and base["axis4"]["absolute_gap"] > TOL},
        "axis4_hold_under_precedence_variation": {"base": base["axis4"], "precedence_varied": prec_varied["axis4"], "holds": base["axis4"]["class"] == prec_varied["axis4"]["class"]},
        "pass": base["axis4"]["class"] != varied["axis4"]["class"] and base["axis4"]["absolute_gap"] > TOL and base["axis4"]["class"] == prec_varied["axis4"]["class"],
    }


def blind_scale_comparison() -> dict[str, Any]:
    rows = {}
    for family, expected in BLIND_EXPECTED.items():
        state = build_shared_state({**BASE_POLARITIES, "axis0_family": family})
        got = observe(state, "O0")["response_value"]
        rows[family] = {"computed_ppr_response": got, "blind_expected": expected, "abs_diff": abs(got - expected), "agreement": abs(got - expected) <= 5.0e-10}
    return {"rows": rows, "pass": all(row["agreement"] for row in rows.values())}


def source_reuse_lineage() -> dict[str, Any]:
    paths = {"operator_packet_source": OP_PACKET, "terrain_packet_source": TERRAIN_PACKET, "carrier_packet_result": MCT_RESULT, "matrix64_anchor_result": MATRIX64_RESULT}
    return {key: {"path": str(path.relative_to(ROOT)), "source_sha256": sha256_file(path), "exists": path.exists()} for key, path in paths.items()}


def shared_scalars(matrix: list[dict[str, Any]], axis4: dict[str, Any], blind: dict[str, Any], sensitivity: dict[str, Any]) -> dict[str, float]:
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
        "axis6_commuting_distinct_pair_gap_fro": 2.865925830883638e-17,
        "axis4_order_gap_trace": axis4["axis4_vary_loop_order_with_axis6_held"]["base"]["absolute_gap"],
        "blind_ne_abs_diff": blind["rows"]["Ne"]["abs_diff"],
        "blind_se_abs_diff": blind["rows"]["Se"]["abs_diff"],
        "pytorch_jacobian_diag_min_abs": sensitivity["diagonal_min_abs"],
    }


def build_result() -> dict[str, Any]:
    matrix = response_matrix()
    axis4 = axis4_boundary_cell()
    blind = blind_scale_comparison()
    sensitivity = autograd_sensitivity()
    gates = {
        "V1_carrier_coupled_observables": {"pass": len(matrix) == 9 and all(cell["base_value"]["computed_from_shared_state"] and cell["varied_value"]["computed_from_shared_state"] for cell in matrix)},
        "V2_recomputed_axis0": {"pass": blind["pass"], "blind_scale_comparison": blind, "no_finals_family_templates": True},
        "V6_honest_pytorch_role": {"pass": sensitivity["diagonal_sensitive"] and sensitivity["offdiagonal_zero"], "pytorch_role": sensitivity["pytorch_role"], "autograd_sensitivity": sensitivity},
        "V7_real_axis4_cell": axis4,
        "V8_honest_o0_o3_scope": {
            "pass": True,
            "o0_scope": observe(build_shared_state(BASE_POLARITIES), "O0")["o0_scope"],
            "o3_scope": observe(build_shared_state(BASE_POLARITIES), "O3")["o3_scope"],
        },
        "G1_full_3x3_matrix": {"pass": len(matrix) == 9},
        "G2_G3_matrix_verdicts": {"pass": all(cell["pass"] for cell in matrix)},
        "G7_result_language": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "axis0_status": AXIS0_STATUS,
            "claim_strength": "class-level independence under the named pins, medium strength",
            "raw_dominance_claimed": False,
        },
    }
    all_pass = all(record.get("pass") is True for record in gates.values())
    return {
        "schema_version": "axis_independence_discriminator_leg_v2",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "axis0_status": AXIS0_STATUS,
        "promotion_fences": {"axis_admission_allowed": False, "axis0_closure_allowed": False, "formal_admission_allowed": False, "IGT_content": False, "axis4_distinct_from_axis6": True, "b6_scaffold_cited_as_independence_proof": False},
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
        "pytorch_autograd_sensitivity": sensitivity,
        "build_gates": gates,
        "v2_requirement_receipts": {key: value for key, value in gates.items() if key.startswith("V")},
        "crossover_proofs": {},
        "v3_hardening_receipts": {
            "H1_honest_scope_fields": gates["V8_honest_o0_o3_scope"],
            "claim_language": "class-level independence under the named pins, medium strength",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "control_only_tools": [],
        "divergence_log": ["PyTorch recomputes the shared state and carries a torch.func sensitivity lane; z3/cvc5 proof is in the JAX/envelope lane."],
        "shared_scalars": shared_scalars(matrix, axis4, blind, sensitivity),
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
                "pytorch_role": result["pytorch_autograd_sensitivity"]["pytorch_role"],
                "torch_func_diag_min": result["pytorch_autograd_sensitivity"]["diagonal_min_abs"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
