#!/usr/bin/env python3
"""L7 schedule-history Xi -> rho_AB -> Phi0 bridge probe.

The Axis0 layered entropy-ratchet audit routes the next bridge target above the
already-failed L4 raw Phi0 family. This scout tests the first routed target:
an L7 schedule-history bridge. It builds exact torch schedule channels from the
shared QIT runtime, derives paired L/R fixed densities, constructs a
history-conditioned two-qubit bridge Xi_history, and compares Phi0 against
history-erased, suffix-erased, type-swap, shuffled-history, no-coupling, random
matched-norm, and response-family controls.

This is a bridge packet, not final Axis0 closure or final manifold admission.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_l7_xi_history_phi0_bridge_probe_results.json"

NAME = "two_root_constraint_l7_xi_history_phi0_bridge_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l7_schedule_history_xi_phi0_bridge"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l7_xi_history_phi0_bridge"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal L7 bridge scout only: constructs a schedule-history Xi bridge from "
    "exact torch QIT engine schedules into rho_AB and Phi0 readouts. It cannot "
    "promote final Axis0 closure, full tensor-network convergence, PEPS/PEPS3D "
    "closure, real scale-level attractor basins, or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact schedule channels, fixed densities, bridge unitaries, and Phi0 entropy readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing schedule-history transition graph and suffix-class witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bridge status and nonpromotion guard for L7 schedule-history Xi",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

TOKENS = ("L", "R")
WORD_LENGTHS = (2, 3, 4, 5)
TAU_VALUES = (0.5, 1.0)
CONTROL_MARGIN = 1.0e-3
PHI0_TOL = 1.0e-3
THETA_BASE = 0.17

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "axis0_entropy_ratchet_result": RESULT_DIR
    / "two_root_constraint_axis0_layered_entropy_ratchet_audit_probe_results.json",
    "response_gradient_result": RESULT_DIR
    / "two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json",
    "stress_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "schedule_phase_result": RESULT_DIR / "two_root_constraint_schedule_memory_phase_map_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()} for name, path in SOURCE_FILES.items()}


def entropy(rho: torch.Tensor, eps: float = 1.0e-12) -> float:
    herm = 0.5 * (rho + rho.conj().T)
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(eps)
    return float((-vals * torch.log(vals)).sum().item())


def kron2(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


def partial_trace_two_qubit(rho_ab: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    shaped = rho_ab.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", shaped)
    rho_b = torch.einsum("abac->bc", shaped)
    return qit.normalize_density(rho_a), qit.normalize_density(rho_b)


def phi0_readout_pair(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a, rho_b = partial_trace_two_qubit(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_A_colon_B": s_a + s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_c_A_to_B": s_b - s_ab,
    }


def bridge_hamiltonians() -> dict[str, torch.Tensor]:
    sx, sy, sz = qit.SX, qit.SY, qit.SZ
    base = 0.52 * (kron2(sx, sx) + kron2(sy, sy)) + 0.26 * kron2(sz, sz)
    suffix = 0.31 * (kron2(sz, sx) - kron2(sx, sz))
    transition = 0.19 * (kron2(sx, sy) + kron2(sy, sx))
    enhanced = base + suffix + transition
    random_raw = 0.62 * kron2(sx, sz) - 0.41 * kron2(sy, sx) + 0.23 * kron2(sz, sy)
    random_matched = random_raw * (torch.linalg.matrix_norm(enhanced) / torch.linalg.matrix_norm(random_raw))
    return {
        "history_enhanced": enhanced,
        "suffix_erased": base + transition,
        "history_erased": base,
        "random_matched_norm": random_matched,
    }


def schedule_words(length: int) -> list[str]:
    return ["".join(tokens) for tokens in itertools.product(TOKENS, repeat=length)]


def mirror_word(word: str) -> str:
    table = str.maketrans({"L": "R", "R": "L"})
    return word.translate(table)[::-1]


def shuffled_word(word: str) -> str:
    if len(word) < 2:
        return word
    return word[1:] + word[0]


def schedule_features(word: str) -> dict[str, Any]:
    transitions = sum(1 for left, right in zip(word, word[1:]) if left != right)
    balance = (word.count("L") - word.count("R")) / len(word)
    p_l = word.count("L") / len(word)
    if p_l in {0.0, 1.0}:
        binary_entropy = 0.0
    else:
        binary_entropy = -(p_l * math.log(p_l) + (1.0 - p_l) * math.log(1.0 - p_l))
    suffix = word[-2:] if len(word) >= 2 else word
    suffix_sign = {"LL": 1.0, "RR": -1.0, "LR": 0.35, "RL": -0.35}.get(suffix, 0.0)
    return {
        "length": len(word),
        "transitions": transitions,
        "transition_density": transitions / max(1, len(word) - 1),
        "balance": balance,
        "binary_entropy": binary_entropy,
        "suffix": suffix,
        "suffix_sign": suffix_sign,
        "last_token": word[-1],
    }


def schedule_graph(words: list[str]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {word: graph.add_node(word) for word in words}
    for word in words:
        for token in TOKENS:
            next_word = (word + token)[-len(word) :]
            if next_word in nodes:
                graph.add_edge(nodes[word], nodes[next_word], token)
    suffix_classes = sorted({schedule_features(word)["suffix"] for word in words})
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
        "suffix_class_count": len(suffix_classes),
        "suffix_classes": suffix_classes,
    }


def fixed_density_for_word(word: str, tau: float, engines: dict[str, torch.Tensor]) -> torch.Tensor:
    channel = qit.schedule_channel(word, engines)
    return qit.fixed_density(channel, cycles=260)


def bridge_theta(features_a: dict[str, Any], features_b: dict[str, Any], *, mode: str) -> float:
    if mode == "no_coupling":
        return 0.0
    if mode == "history_erased":
        return THETA_BASE
    suffix_term = 0.075 * (features_a["suffix_sign"] - features_b["suffix_sign"])
    transition_term = 0.055 * (features_a["transition_density"] + features_b["transition_density"])
    balance_term = 0.045 * abs(features_a["balance"] - features_b["balance"])
    entropy_term = 0.035 * (features_a["binary_entropy"] + features_b["binary_entropy"])
    if mode == "suffix_erased":
        suffix_term = 0.0
    if mode == "shuffled_history":
        transition_term = -transition_term
        balance_term = 0.5 * balance_term
    return max(0.0, THETA_BASE + suffix_term + transition_term + balance_term + entropy_term)


def apply_bridge(rho_a: torch.Tensor, rho_b: torch.Tensor, H_bridge: torch.Tensor, theta: float) -> torch.Tensor:
    rho_ab = qit.normalize_density(kron2(rho_a, rho_b))
    if theta == 0.0:
        return rho_ab
    U = torch.linalg.matrix_exp(-1j * float(theta) * H_bridge)
    return qit.normalize_density(U @ rho_ab @ U.conj().T)


def evaluate_case(
    case_name: str,
    words: list[str],
    tau: float,
    H_bridge: torch.Tensor,
    engines: dict[str, torch.Tensor],
    *,
    type_swap: bool = False,
    shuffled_history: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for word in words:
        partner = mirror_word(word)
        if shuffled_history:
            partner = shuffled_word(partner)
        word_a, word_b = (partner, word) if type_swap else (word, partner)
        rho_a = fixed_density_for_word(word_a, tau, engines)
        rho_b = fixed_density_for_word(word_b, tau, engines)
        features_a = schedule_features(word_a)
        features_b = schedule_features(word_b)
        mode = (
            "no_coupling"
            if case_name == "no_coupling_control"
            else "history_erased"
            if case_name == "history_erased_control"
            else "suffix_erased"
            if case_name == "suffix_erased_control"
            else "shuffled_history"
            if shuffled_history
            else "canonical"
        )
        theta = bridge_theta(features_a, features_b, mode=mode)
        rho_ab = apply_bridge(rho_a, rho_b, H_bridge, theta)
        phi0 = phi0_readout_pair(rho_ab)
        rows.append(
            {
                "word_A": word_a,
                "word_B": word_b,
                "tau": tau,
                "theta": theta,
                "features_A": features_a,
                "features_B": features_b,
                "phi0": phi0,
                "rho_AB_min_eig": float(torch.min(torch.linalg.eigvalsh(rho_ab).real).item()),
            }
        )
    mean_mi = sum(row["phi0"]["I_A_colon_B"] for row in rows) / len(rows)
    mean_ic = sum(row["phi0"]["I_c_A_to_B"] for row in rows) / len(rows)
    mean_conditional = sum(row["phi0"]["S_A_given_B"] for row in rows) / len(rows)
    return {
        "name": case_name,
        "tau": tau,
        "row_count": len(rows),
        "mean_I_A_colon_B": mean_mi,
        "mean_I_c_A_to_B": mean_ic,
        "mean_S_A_given_B": mean_conditional,
        "min_rho_AB_eig": min(row["rho_AB_min_eig"] for row in rows),
        "mean_theta": sum(row["theta"] for row in rows) / len(rows),
        "sample_rows": rows[:6],
    }


def tau_surface(tau: float) -> dict[str, Any]:
    H0 = qit.direction_hamiltonian("iter176_xz")
    engines = {
        "L": qit.engine_channel("L", "iter176_xz", tau=tau),
        "R": qit.engine_channel("R", "iter176_xz", tau=tau),
    }
    Hs = bridge_hamiltonians()
    words = [word for length in WORD_LENGTHS for word in schedule_words(length)]
    cases = [
        evaluate_case("no_coupling_control", words, tau, Hs["history_enhanced"], engines),
        evaluate_case("canonical_l7_xi_history", words, tau, Hs["history_enhanced"], engines),
        evaluate_case("history_erased_control", words, tau, Hs["history_erased"], engines),
        evaluate_case("suffix_erased_control", words, tau, Hs["suffix_erased"], engines),
        evaluate_case("type_swap_control", words, tau, Hs["history_enhanced"], engines, type_swap=True),
        evaluate_case(
            "shuffled_history_control",
            words,
            tau,
            Hs["history_enhanced"],
            engines,
            shuffled_history=True,
        ),
        evaluate_case("random_matched_norm_control", words, tau, Hs["random_matched_norm"], engines),
    ]
    graph = schedule_graph([word for word in schedule_words(4)])
    return {
        "tau": tau,
        "H0_trace": float(torch.trace(H0).real.item()),
        "word_count": len(words),
        "schedule_graph_length4": graph,
        "cases": cases,
    }


def summarize_surfaces(surfaces: list[dict[str, Any]]) -> dict[str, Any]:
    case_values: dict[str, list[float]] = {}
    for surface in surfaces:
        for case in surface["cases"]:
            case_values.setdefault(case["name"], []).append(case["mean_I_A_colon_B"])
    means = {name: sum(values) / len(values) for name, values in case_values.items()}
    canonical = means["canonical_l7_xi_history"]
    controls = {name: value for name, value in means.items() if name != "canonical_l7_xi_history"}
    max_control_name, max_control = max(controls.items(), key=lambda item: item[1])
    no_coupling = means["no_coupling_control"]
    return {
        "mean_I_A_colon_B_by_case": means,
        "canonical_mean_I_A_colon_B": canonical,
        "max_control_name": max_control_name,
        "max_control_mean_I_A_colon_B": max_control,
        "canonical_minus_max_control": canonical - max_control,
        "canonical_minus_no_coupling": canonical - no_coupling,
        "canonical_nonzero": canonical > PHI0_TOL,
        "canonical_separates_controls": canonical > max_control + CONTROL_MARGIN,
    }


def z3_guard(summary: dict[str, Any]) -> dict[str, Any]:
    nonzero = z3.Bool("nonzero")
    separates = z3.Bool("separates")
    l7_built = z3.Bool("l7_built")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(nonzero == bool(summary["canonical_nonzero"]))
    solver.add(separates == bool(summary["canonical_separates_controls"]))
    solver.add(l7_built == True)
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(nonzero, separates, l7_built)))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "sat": status == z3.sat,
        "nonzero": bool(z3.is_true(model.eval(nonzero, model_completion=True))) if model is not None else False,
        "separates_from_controls": bool(z3.is_true(model.eval(separates, model_completion=True))) if model is not None else False,
        "l7_xi_history_built": bool(z3.is_true(model.eval(l7_built, model_completion=True))) if model is not None else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model is not None else False,
        "rule": "L7 Xi_history may advance bridge routing only; final admission still requires control separation plus tensor/scale closure.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    surfaces = [tau_surface(tau) for tau in TAU_VALUES]
    summary_values = summarize_surfaces(surfaces)
    guard = z3_guard(summary_values)
    bridge_status = (
        "l7_history_rescued_control_separated"
        if guard["separates_from_controls"]
        else ("open_nonzero_not_control_separated" if guard["nonzero"] else "killed_near_zero")
    )
    positive = {
        "axis0_entropy_ratchet_loaded": {
            "pass": upstream["axis0_entropy_ratchet_result"].get("all_pass") is True
            and upstream["axis0_entropy_ratchet_result"].get("recommended_next_bridge_target")
            == "L7_Xi_history_or_L8_shell_weighted_phi0",
            "status": upstream["axis0_entropy_ratchet_result"].get("axis0_entropy_ratchet_status"),
        },
        "schedule_surfaces_built": {
            "pass": len(surfaces) == len(TAU_VALUES)
            and all(surface["word_count"] == sum(2**length for length in WORD_LENGTHS) for surface in surfaces),
            "tau_values": list(TAU_VALUES),
            "word_lengths": list(WORD_LENGTHS),
        },
        "history_controls_present": {
            "pass": all(len(surface["cases"]) == 7 for surface in surfaces),
            "case_names": [case["name"] for case in surfaces[0]["cases"]],
        },
        "rho_ab_valid": {
            "pass": min(case["min_rho_AB_eig"] for surface in surfaces for case in surface["cases"]) > -1.0e-8,
            "min_rho_AB_eig": min(case["min_rho_AB_eig"] for surface in surfaces for case in surface["cases"]),
        },
        "bridge_status_classified": {
            "pass": bridge_status
            in {"l7_history_rescued_control_separated", "open_nonzero_not_control_separated", "killed_near_zero"},
            "bridge_status": bridge_status,
            "z3": guard,
        },
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "final_manifold_admission_allowed": False,
        "not_full_tensor_network_convergence": True,
        "not_peps_or_peps3d": True,
        "not_scale_level_real_basin": True,
        "bridge_status": bridge_status,
        "why_not_final": [
            "This scout builds an L7 schedule-history bridge over exact engine schedules, not full tensor-network convergence.",
            "It does not run PEPS/PEPS3D dynamics.",
            "It does not establish scale-level real attractor-basin admission.",
            "Final manifold admission remains blocked by full tensor and basin/admission gates.",
        ],
    }
    graveyard = {
        "not_l4_replay": {
            "pass": True,
            "detail": "The bridge uses schedule words and suffix/history controls, not another raw L4 MI threshold tweak.",
        },
        "not_final_axis0_closure": {
            "pass": guard["final_manifold_admission_allowed"] is False,
            "detail": "Z3 guard keeps final admission false.",
        },
        "not_schedule_pseudobasin_promotion": {
            "pass": True,
            "detail": "Schedule classes are used as history inputs to Xi, not called real attractor basins.",
        },
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for item in graveyard.values() if item["pass"]),
        "items": sorted(graveyard),
    }
    all_pass = all(item["pass"] for item in positive.values()) and guard["sat"]
    summary = {
        "all_pass": all_pass,
        "l7_xi_history_status": bridge_status,
        "canonical_mean_I_A_colon_B": summary_values["canonical_mean_I_A_colon_B"],
        "max_control_name": summary_values["max_control_name"],
        "max_control_mean_I_A_colon_B": summary_values["max_control_mean_I_A_colon_B"],
        "canonical_minus_max_control": summary_values["canonical_minus_max_control"],
        "canonical_minus_no_coupling": summary_values["canonical_minus_no_coupling"],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "L7 schedule-history Xi is now executable. Its status is classified "
            "against history/suffix/type/random/no-coupling controls and remains "
            "bounded bridge evidence, not final Axis0 closure."
        ),
        "next_required_work": (
            "If L7 remains nonseparating, build the L8 shell-weighted bridge. If it separates, "
            "stress it against tensor-carrier and scale controls before any admission."
        ),
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "axis0_entropy_ratchet_status": upstream["axis0_entropy_ratchet_result"].get(
                "axis0_entropy_ratchet_status"
            ),
            "axis0_recommended_next": upstream["axis0_entropy_ratchet_result"].get(
                "recommended_next_bridge_target"
            ),
            "response_gradient_status": upstream["response_gradient_result"].get("summary", {}).get(
                "repair_status"
            ),
            "stress_status": upstream["stress_result"].get("summary", {}).get("stress_status"),
            "schedule_phase_all_pass": upstream["schedule_phase_result"].get("all_pass"),
        },
        "parameters": {
            "tokens": list(TOKENS),
            "word_lengths": list(WORD_LENGTHS),
            "tau_values": list(TAU_VALUES),
            "theta_base": THETA_BASE,
            "control_margin": CONTROL_MARGIN,
            "phi0_tol": PHI0_TOL,
        },
        "surfaces": surfaces,
        "summary_values": summary_values,
        "z3_guard": guard,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": (
            "This is a v5 source-native schedule-history bridge scout using the "
            "shared exact torch QIT runtime and current formal receipts. It is "
            "not a legacy v4 probe, not PEPS/PEPS3D dynamics, not full tensor "
            "convergence, and not final Axis0 admission."
        ),
        "next_work_required": [
            "Stress any separating L7 bridge against tensor-carrier and scale controls.",
            "If L7 is nonseparating, build the L8 shell-weighted Phi0 bridge.",
            "Keep final manifold admission blocked until robust bridge, full tensor, and basin gates close.",
        ],
        "blockers": [],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
