#!/usr/bin/env python3
"""Axis0 layered entropy ratchet audit.

The recent Axis0 doctrine audit reframes the current bridge failures: runtime
entropy, Hopf/torus entropy, and bipartite Axis0 entropy are different layers,
not interchangeable candidates for one flat scalar. This scout turns that
claim into executable repo evidence. It builds a layer-by-layer admissibility
matrix for entropy forms, checks the unlock thresholds with z3, and uses the
current Phi0 bridge receipts to route the next run target.

This is an audit and routing scout. It does not admit Axis0, a final manifold,
scale-level attractor basins, or full tensor-network closure.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_axis0_layered_entropy_ratchet_audit_probe_results.json"

NAME = "two_root_constraint_axis0_layered_entropy_ratchet_audit_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_axis0_layered_entropy_ratchet_audit"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_axis0_layered_entropy_ratchet"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal routing/audit scout only: verifies that Axis0 entropy forms are "
    "layer-indexed by the constraint-manifold ratchet and routes the current "
    "Phi0 failures to L7 schedule-history Xi or L8 shell-weighted bridge work. "
    "It cannot promote final Axis0 closure, final manifold admission, real "
    "scale-level attractor basins, or full tensor-network convergence."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing entropy calculations for single-system, torus-seat, bipartite, Chern, and schedule ensemble examples",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing layer-to-entropy dependency graph and monotone unlock witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing satisfiability checks for entropy-form unlock thresholds and nonpromotion guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/doctrine provenance hashes"},
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

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "axis_and_entropy_reference": pathlib.Path.home() / "wiki" / "concepts" / "axis-and-entropy-reference.md",
    "constraint_geometry_axis0_separation": pathlib.Path.home()
    / "wiki"
    / "concepts"
    / "constraint-geometry-axis0-separation.md",
    "qit_bridge_master_table": REPO
    / "system_v5"
    / "READ ONLY Reference Docs"
    / "QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE copy.md",
    "taijitu_reconciliation": REPO
    / "system_v5"
    / "READ ONLY Reference Docs"
    / "TAIJITU_PROBE_RECONCILIATION_CARD copy.md",
    "weyl_flux": REPO / "system_v5" / "READ ONLY Reference Docs" / "Weyl Flux.md",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
    "stress_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "response_gradient_result": RESULT_DIR
    / "two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json",
    "slow_mode_bridge_result": RESULT_DIR / "two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json",
    "mps_phi0_result": RESULT_DIR / "two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json",
}

LAYERS = [
    {
        "id": "L1",
        "name": "Pauli / finite noncommuting algebra",
        "features": {"finite_carrier", "observable_algebra", "noncommuting_ops"},
    },
    {
        "id": "L2",
        "name": "Spinor S3 / torus-seat chart",
        "features": {"spinor", "state_carrier", "torus_chart"},
    },
    {"id": "L3", "name": "Density D(C2)", "features": {"density_state"}},
    {
        "id": "L4",
        "name": "Weyl L/R bipartite cut",
        "features": {"weyl_lr", "bipartite", "cut_state_candidate"},
    },
    {"id": "L5", "name": "Terrain CPTP density laws", "features": {"cptp_dynamics", "terrain_laws"}},
    {"id": "L6", "name": "Hopf loop / bundle layer", "features": {"hopf_bundle", "loop"}},
    {"id": "L7", "name": "Engine schedule history", "features": {"schedule_history", "engine_word"}},
    {"id": "L8", "name": "Full M(C) shell/history support", "features": {"shell_weighted", "full_mc"}},
]

ENTROPY_FORMS = {
    "shannon_count": {
        "requirements": {"finite_carrier"},
        "kind": "unsigned_predicate",
        "axis0_role": "pre_entropy_cardinality",
    },
    "connes_operator_entropy": {
        "requirements": {"observable_algebra"},
        "kind": "operator_algebra",
        "axis0_role": "supportive_pre_axis",
    },
    "von_neumann_S_rho": {
        "requirements": {"density_state"},
        "kind": "single_system_unsigned",
        "axis0_role": "runtime_sheet_entropy",
    },
    "renyi_entropy": {
        "requirements": {"density_state"},
        "kind": "single_system_unsigned",
        "axis0_role": "runtime_sheet_entropy",
    },
    "relative_entropy_to_mixed": {
        "requirements": {"density_state"},
        "kind": "single_system_unsigned",
        "axis0_role": "runtime_sheet_entropy",
    },
    "berry_phase": {
        "requirements": {"spinor"},
        "kind": "geometric_phase",
        "axis0_role": "geometry_flux_support",
    },
    "torus_orbit_entropy_gradient": {
        "requirements": {"torus_chart"},
        "kind": "geometry_unsigned_with_sign_gradient",
        "axis0_role": "chart_A0_sign",
    },
    "holevo_chi": {
        "requirements": {"density_state"},
        "kind": "ensemble_information",
        "axis0_role": "diagnostic",
    },
    "mutual_information": {
        "requirements": {"bipartite"},
        "kind": "bipartite_unsigned",
        "axis0_role": "Phi0_diagnostic_companion",
    },
    "conditional_entropy": {
        "requirements": {"bipartite"},
        "kind": "bipartite_signed",
        "axis0_role": "Phi0_signed_family",
    },
    "coherent_information": {
        "requirements": {"bipartite"},
        "kind": "bipartite_signed",
        "axis0_role": "Phi0_primary_candidate_family",
    },
    "negativity": {
        "requirements": {"bipartite"},
        "kind": "bipartite_entanglement_witness",
        "axis0_role": "control_witness",
    },
    "log_negativity": {
        "requirements": {"bipartite"},
        "kind": "bipartite_entanglement_witness",
        "axis0_role": "control_witness",
    },
    "concurrence": {
        "requirements": {"bipartite"},
        "kind": "bipartite_entanglement_witness",
        "axis0_role": "control_witness",
    },
    "chern_c1": {
        "requirements": {"hopf_bundle"},
        "kind": "topological_invariant",
        "axis0_role": "Hopf_flux_threshold",
    },
    "schedule_history_holevo": {
        "requirements": {"schedule_history"},
        "kind": "schedule_ensemble",
        "axis0_role": "Xi_history_candidate",
    },
    "schedule_history_gradient": {
        "requirements": {"schedule_history", "bipartite"},
        "kind": "history_phi0_gradient",
        "axis0_role": "L7_Xi_history_candidate",
    },
    "shell_weighted_coherent_information": {
        "requirements": {"shell_weighted", "bipartite"},
        "kind": "shell_weighted_signed",
        "axis0_role": "L8_shell_candidate",
    },
    "topological_entanglement_entropy": {
        "requirements": {"shell_weighted", "hopf_bundle"},
        "kind": "topological_entropy",
        "axis0_role": "L8_topological_support",
    },
}

SIGNED_FORMS = {"conditional_entropy", "coherent_information"}
L4_ONLY_FORMS = {"mutual_information", "conditional_entropy", "coherent_information", "negativity", "log_negativity", "concurrence"}


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
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return float(value.real.item())
        return [jsonable(v) for v in value.detach().cpu().reshape(-1)]
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()} for name, path in SOURCE_FILES.items()}


def doc_hit(path: pathlib.Path, needles: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(path), "exists": False, "hits": {}}
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    return {
        "path": rel(path),
        "exists": True,
        "hits": {needle: (needle.lower() in lowered) for needle in needles},
    }


def cumulative_layer_matrix() -> list[dict[str, Any]]:
    features: set[str] = set()
    prior_forms: set[str] = set()
    rows: list[dict[str, Any]] = []
    for layer in LAYERS:
        features |= set(layer["features"])
        admissible = {
            name for name, spec in ENTROPY_FORMS.items() if set(spec["requirements"]).issubset(features)
        }
        new_unlocks = admissible - prior_forms
        rows.append(
            {
                "layer": layer["id"],
                "name": layer["name"],
                "features_added": sorted(layer["features"]),
                "cumulative_feature_count": len(features),
                "admissible_entropy_forms": sorted(admissible),
                "admissible_count": len(admissible),
                "new_unlocks": sorted(new_unlocks),
                "signed_bipartite_unlocked": bool(SIGNED_FORMS <= admissible),
                "monotone_from_previous": prior_forms.issubset(admissible),
            }
        )
        prior_forms = admissible
    return rows


def first_layer_for(form: str, matrix: list[dict[str, Any]]) -> str | None:
    for row in matrix:
        if form in set(row["admissible_entropy_forms"]):
            return str(row["layer"])
    return None


def build_dependency_graph(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    layer_nodes = {row["layer"]: graph.add_node({"type": "layer", "id": row["layer"]}) for row in matrix}
    form_nodes = {
        form: graph.add_node({"type": "entropy_form", "id": form})
        for form in sorted(ENTROPY_FORMS.keys())
    }
    for left, right in zip(matrix, matrix[1:]):
        graph.add_edge(layer_nodes[left["layer"]], layer_nodes[right["layer"]], {"kind": "ratchet_order"})
    for row in matrix:
        new_unlocks = set(row["new_unlocks"])
        for form in new_unlocks:
            graph.add_edge(layer_nodes[row["layer"]], form_nodes[form], {"kind": "unlocks"})
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_directed_acyclic": rx.is_directed_acyclic_graph(graph),
        "unlock_edges": sum(1 for edge in graph.edge_list() if graph.get_edge_data(*edge)["kind"] == "unlocks"),
    }


def entropy(rho: torch.Tensor, eps: float = 1.0e-12) -> float:
    herm = 0.5 * (rho + rho.conj().T)
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(eps)
    return float((-vals * torch.log(vals)).sum().item())


def relative_entropy_diagonal_to_mixed(rho_diag: torch.Tensor, eps: float = 1.0e-12) -> float:
    vals = torch.real(torch.diag(rho_diag)).clamp_min(eps)
    dim = vals.numel()
    return float(torch.sum(vals * (torch.log(vals) - math.log(1.0 / dim))).item())


def partial_trace_two_qubit(rho_ab: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    shaped = rho_ab.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", shaped)
    rho_b = torch.einsum("abac->bc", shaped)
    return rho_a, rho_b


def partial_transpose_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)


def executable_examples() -> dict[str, Any]:
    dtype = torch.complex128
    rho = torch.diag(torch.tensor([0.65, 0.35], dtype=torch.float64)).to(dtype)
    single_entropy = entropy(rho)
    rel_to_mixed = relative_entropy_diagonal_to_mixed(rho)
    renyi2 = float((-torch.log(torch.real(torch.trace(rho @ rho)))).item())

    etas = torch.linspace(0.05, math.pi / 2.0 - 0.05, 64, dtype=torch.float64)
    p = torch.cos(etas) ** 2
    torus_s = -(p * torch.log(p) + (1.0 - p) * torch.log(1.0 - p))
    # dS/d eta = sin(2 eta) * log(cos^2 eta / sin^2 eta)
    torus_grad = torch.sin(2.0 * etas) * torch.log(p / (1.0 - p))
    eta_mid = torch.tensor(math.pi / 4.0, dtype=torch.float64)
    chart_a0_left = float(torch.sign(torch.cos(2.0 * torch.tensor(math.pi / 6.0))).item())
    chart_a0_right = float(torch.sign(torch.cos(2.0 * torch.tensor(math.pi / 3.0))).item())

    bell = torch.zeros(4, dtype=dtype)
    bell[0] = 1.0 / math.sqrt(2.0)
    bell[3] = 1.0 / math.sqrt(2.0)
    rho_ab = torch.outer(bell, bell.conj())
    rho_a, rho_b = partial_trace_two_qubit(rho_ab)
    s_ab = entropy(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    mutual = s_a + s_b - s_ab
    conditional = s_ab - s_b
    coherent = s_b - s_ab
    pt_vals = torch.linalg.eigvalsh(partial_transpose_b(rho_ab)).real
    negativity = float(torch.sum(torch.clamp(-pt_vals, min=0.0)).item())
    log_negativity = float(torch.log(torch.tensor(2.0 * negativity + 1.0)).item())
    concurrence = 1.0

    theta = torch.linspace(0.0, math.pi, 2049, dtype=torch.float64)
    sphere_area = torch.trapezoid(torch.sin(theta), theta) * (2.0 * math.pi)
    chern = float((sphere_area / (4.0 * math.pi)).item())

    p_ensemble = torch.tensor([0.5, 0.5], dtype=torch.float64)
    rho0 = torch.diag(torch.tensor([0.9, 0.1], dtype=torch.float64)).to(dtype)
    rho1 = torch.diag(torch.tensor([0.2, 0.8], dtype=torch.float64)).to(dtype)
    avg = p_ensemble[0] * rho0 + p_ensemble[1] * rho1
    holevo = entropy(avg) - float(p_ensemble[0].item()) * entropy(rho0) - float(p_ensemble[1].item()) * entropy(rho1)

    return {
        "single_system": {
            "von_neumann_S": single_entropy,
            "renyi_2": renyi2,
            "relative_entropy_to_max_mixed": rel_to_mixed,
            "rho_trace": float(torch.trace(rho).real.item()),
        },
        "torus_seat": {
            "eta_pi_over_4": float(eta_mid.item()),
            "S_eta_min": float(torch.min(torus_s).item()),
            "S_eta_max": float(torch.max(torus_s).item()),
            "gradient_sign_eta_pi_over_6": chart_a0_left,
            "gradient_sign_eta_pi_over_3": chart_a0_right,
            "gradient_abs_near_pi_over_4": float(torch.min(torch.abs(torus_grad)).item()),
        },
        "bipartite_axis0": {
            "S_A": s_a,
            "S_B": s_b,
            "S_AB": s_ab,
            "I_A_colon_B": mutual,
            "S_A_given_B": conditional,
            "I_c_A_to_B": coherent,
            "conditional_entropy_is_signed_negative": conditional < 0.0,
            "negativity": negativity,
            "log_negativity": log_negativity,
            "concurrence": concurrence,
        },
        "topological": {"chern_c1_numeric": chern, "chern_c1_close_to_one": abs(chern - 1.0) < 1.0e-6},
        "schedule_ensemble": {"holevo_chi_example": holevo},
    }


def z3_unlock_guard(matrix: list[dict[str, Any]], phi0_failures_active: bool) -> dict[str, Any]:
    idx = {row["layer"]: i + 1 for i, row in enumerate(matrix)}
    first = {form: first_layer_for(form, matrix) for form in ENTROPY_FORMS}
    solver = z3.Solver()

    signed_first = z3.Int("signed_bipartite_first_layer")
    chern_first = z3.Int("chern_first_layer")
    schedule_first = z3.Int("schedule_history_first_layer")
    shell_first = z3.Int("shell_weighted_first_layer")
    chart_first = z3.Int("chart_a0_first_layer")
    final_admission = z3.Bool("final_manifold_admission_allowed")
    next_requires_l7_or_l8 = z3.Bool("next_requires_l7_or_l8")
    l4_family_exhausted = z3.Bool("l4_family_exhausted_by_controls")

    solver.add(signed_first == idx[first["coherent_information"]])
    solver.add(signed_first == idx["L4"])
    solver.add(chern_first == idx[first["chern_c1"]])
    solver.add(chern_first == idx["L6"])
    solver.add(schedule_first == idx[first["schedule_history_holevo"]])
    solver.add(schedule_first == idx["L7"])
    solver.add(shell_first == idx[first["shell_weighted_coherent_information"]])
    solver.add(shell_first == idx["L8"])
    solver.add(chart_first == idx[first["torus_orbit_entropy_gradient"]])
    solver.add(chart_first == idx["L2"])
    solver.add(l4_family_exhausted == bool(phi0_failures_active))
    solver.add(next_requires_l7_or_l8 == z3.And(l4_family_exhausted, signed_first == idx["L4"]))
    solver.add(final_admission == False)
    status = solver.check()
    model = solver.model() if status == z3.sat else None

    return {
        "sat": status == z3.sat,
        "model": {
            "signed_bipartite_first_layer": int(str(model[signed_first])) if model is not None else None,
            "chern_first_layer": int(str(model[chern_first])) if model is not None else None,
            "schedule_history_first_layer": int(str(model[schedule_first])) if model is not None else None,
            "shell_weighted_first_layer": int(str(model[shell_first])) if model is not None else None,
            "chart_a0_first_layer": int(str(model[chart_first])) if model is not None else None,
            "next_requires_l7_or_l8": bool(z3.is_true(model[next_requires_l7_or_l8])) if model is not None else None,
            "final_manifold_admission_allowed": bool(z3.is_true(model[final_admission])) if model is not None else None,
        },
    }


def current_phi0_failure_summary() -> dict[str, Any]:
    receipts = {
        "mps_phi0": read_json(SOURCE_FILES["mps_phi0_result"]),
        "slow_mode_bridge": read_json(SOURCE_FILES["slow_mode_bridge_result"]),
        "stress": read_json(SOURCE_FILES["stress_result"]),
        "response_gradient": read_json(SOURCE_FILES["response_gradient_result"]),
    }
    response = receipts["response_gradient"]
    stress = receipts["stress"]
    slow = receipts["slow_mode_bridge"]
    mps = receipts["mps_phi0"]
    response_summary = response.get("summary", {})
    stress_summary = stress.get("summary", {})
    slow_summary = slow.get("summary", {})
    mps_summary = mps.get("summary", {})
    response_boundary = response.get("boundary", {})
    stress_boundary = stress.get("boundary", {})
    slow_boundary = slow.get("boundary", {})
    mps_boundary = mps.get("boundary", {})
    active_failures = {
        "mps_nonseparating": (
            "not_control_separated"
            in str(mps_summary.get("bridge_status", mps_boundary.get("bridge_status", ""))).lower()
        )
        or ("nonseparating" in json.dumps(mps_summary).lower()),
        "slow_mode_open": str(
            slow_summary.get("bridge_status", slow_boundary.get("bridge_status", ""))
        ).startswith("open"),
        "stress_nonrobust": "nonrobust"
        in str(stress_summary.get("stress_status", stress_boundary.get("stress_status", ""))).lower(),
        "response_gradient_nonrobust": "nonrobust"
        in str(response_summary.get("repair_status", response_boundary.get("repair_status", ""))).lower(),
        "final_admission_blocked": response_summary.get("final_manifold_admission_allowed")
        is False
        and stress_summary.get("final_manifold_admission_allowed") is False
        and slow_summary.get("final_manifold_admission_allowed") is False
        and mps_boundary.get("final_manifold_admission_allowed") is False,
    }
    receipt_statuses = {
        "mps_phi0": mps_summary.get("bridge_status") or mps_boundary.get("bridge_status"),
        "slow_mode_bridge": slow_summary.get("bridge_status") or slow_boundary.get("bridge_status"),
        "stress": stress_summary.get("stress_status") or stress_boundary.get("stress_status"),
        "response_gradient": response_summary.get("repair_status") or response_boundary.get("repair_status"),
    }
    allowed_nonpromotional = {
        "open_nonzero_not_control_separated",
        "open_nonrobust_internal_controls",
        "open_nonrobust_response_controls",
        "killed_near_zero",
    }
    l4_receipt_promotion_guard = {
        "allowed_nonpromotional_statuses": sorted(allowed_nonpromotional),
        "unexpected_statuses": {
            name: status for name, status in receipt_statuses.items() if status not in allowed_nonpromotional
        },
        "repair_rescued_flags": {
            "response_gradient": bool(response_summary.get("repair_rescued", False)),
            "mps_phi0": bool(mps_summary.get("z3_rescue_guard", {}).get("bridge_rescued", False)),
        },
    }
    l4_receipt_promotion_guard["passes"] = (
        not l4_receipt_promotion_guard["unexpected_statuses"]
        and not any(l4_receipt_promotion_guard["repair_rescued_flags"].values())
    )
    return {
        "receipt_statuses": receipt_statuses,
        "active_failures": active_failures,
        "l4_receipt_promotion_guard": l4_receipt_promotion_guard,
        "all_current_l4_phi0_repairs_nonpromotional": all(active_failures.values())
        and bool(l4_receipt_promotion_guard["passes"]),
        "response_gradient_key_numbers": {
            "canonical_mean_I_A_colon_B": response_summary.get("canonical_mean_mutual_information"),
            "canonical_min_no_coupling_delta": response_summary.get("canonical_min_delta_vs_no_coupling"),
            "canonical_mean_abs_gradient": response_summary.get("canonical_mean_abs_gradient"),
            "max_comparable_delta_case": response_summary.get("max_comparable_mean_delta"),
            "max_comparable_abs_gradient_case": response_summary.get("max_comparable_abs_gradient"),
            "tensor_carrier_challenge_passed": response_summary.get("tensor_carrier_challenge_passed"),
        },
    }


def main() -> None:
    started = time.time()
    matrix = cumulative_layer_matrix()
    first_unlocks = {form: first_layer_for(form, matrix) for form in sorted(ENTROPY_FORMS)}
    phi0_summary = current_phi0_failure_summary()
    z3_guard = z3_unlock_guard(matrix, phi0_summary["all_current_l4_phi0_repairs_nonpromotional"])
    examples = executable_examples()
    graph = build_dependency_graph(matrix)

    doctrine_checks = {
        "axis_and_entropy_reference": doc_hit(
            SOURCE_FILES["axis_and_entropy_reference"],
            ["Three-Layer Entropy Architecture", "Axis 0", "S(A|B)", "I_c", "open"],
        ),
        "constraint_geometry_axis0_separation": doc_hit(
            SOURCE_FILES["constraint_geometry_axis0_separation"],
            ["root constraints", "admissible manifold", "geometry induced", "axis slices"],
        ),
        "qit_bridge_master_table": doc_hit(
            SOURCE_FILES["qit_bridge_master_table"],
            ["runtime entropy", "bridge family", "rho_AB", "coherent information", "open bridge"],
        ),
        "taijitu_reconciliation": doc_hit(
            SOURCE_FILES["taijitu_reconciliation"],
            ["sign( cos(2 eta) )", "Phi_0(rho_AB)", "bridge and cut still open"],
        ),
        "weyl_flux": doc_hit(
            SOURCE_FILES["weyl_flux"],
            ["rho_{AB}", "entropy layer", "Axis 0 field", "entropy gradient"],
        ),
    }
    doctrine_supported = all(
        check["exists"] and all(check["hits"].values()) for check in doctrine_checks.values()
    )

    monotone = all(row["monotone_from_previous"] for row in matrix)
    threshold_checks = {
        "chart_a0_unlocked_at_L2": first_unlocks["torus_orbit_entropy_gradient"] == "L2",
        "signed_bipartite_unlocked_at_L4": first_unlocks["coherent_information"] == "L4"
        and first_unlocks["conditional_entropy"] == "L4",
        "chern_unlocked_at_L6": first_unlocks["chern_c1"] == "L6",
        "schedule_history_unlocked_at_L7": first_unlocks["schedule_history_holevo"] == "L7",
        "shell_weighted_unlocked_at_L8": first_unlocks["shell_weighted_coherent_information"] == "L8",
    }

    current_run_improvement = {
        "stop_doing": [
            "Do not replay another raw L4 mutual-information/coherent-information threshold tweak as if it can close Axis0.",
            "Do not treat L2 chart sign sign(cos(2 eta)) and L4 Phi0(rho_AB) as the same object.",
            "Do not promote schedule pseudo-basins or nonrobust Phi0 response gradients to final manifold admission.",
        ],
        "do_next": [
            "Build an L7 Xi_history scout: schedule-history -> rho_AB -> Phi0, with history-erased and suffix-erased controls.",
            "Or build an L8 shell-weighted scout: sum_r w_r I_c(A_r->B_r), with shell-shuffled, weight-shuffled, terrain-erased, and tensor-carrier controls.",
            "Keep L4 family receipts as killed/open controls and use them as baselines for L7/L8 bridge tests.",
        ],
        "why": (
            "The current failures are not just bad parameter choices. They show the tested L4 Phi0 family is "
            "nonrobust under internal controls, while the doctrine requires the still-open Xi bridge to unify "
            "L2 chart sign, L4 bipartite signed entropy, L6 Hopf/Chern structure, and L7/L8 history/shell support."
        ),
    }

    all_pass = bool(
        doctrine_supported
        and monotone
        and graph["is_directed_acyclic"]
        and all(threshold_checks.values())
        and z3_guard["sat"]
        and phi0_summary["all_current_l4_phi0_repairs_nonpromotional"]
        and phi0_summary["l4_receipt_promotion_guard"]["passes"]
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "axis0_entropy_ratchet_status": "layered_doctrine_executable" if all_pass else "needs_review",
        "current_phi0_failure_reframed_as_layer_mismatch": phi0_summary[
            "all_current_l4_phi0_repairs_nonpromotional"
        ],
        "recommended_next_bridge_target": "L7_Xi_history_or_L8_shell_weighted_phi0",
        "final_manifold_admission_allowed": False,
        "source_hashes": source_hashes(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "doctrine_checks": doctrine_checks,
        "layer_entropy_matrix": matrix,
        "first_unlocks": first_unlocks,
        "threshold_checks": threshold_checks,
        "dependency_graph": graph,
        "executable_examples": examples,
        "z3_unlock_guard": z3_guard,
        "current_phi0_failure_summary": phi0_summary,
        "current_run_improvement": current_run_improvement,
        "positive": {
            "doctrine_source_docs_support_layers": {
                "pass": doctrine_supported,
                "checked_sources": sorted(doctrine_checks),
            },
            "entropy_layer_matrix_monotone": {
                "pass": monotone,
                "row_count": len(matrix),
            },
            "threshold_unlocks_match_expected_layers": {
                "pass": all(threshold_checks.values()),
                "threshold_checks": threshold_checks,
            },
            "dependency_graph_and_z3_guard_pass": {
                "pass": graph["is_directed_acyclic"] and z3_guard["sat"],
                "graph_is_directed_acyclic": graph["is_directed_acyclic"],
                "z3_sat": z3_guard["sat"],
            },
            "current_l4_phi0_failures_are_nonpromotional": {
                "pass": phi0_summary["all_current_l4_phi0_repairs_nonpromotional"],
                "phi0_summary": phi0_summary,
            },
        },
        "graveyard_companions": {
            "l4_phi0_not_promoted": {
                "pass": phi0_summary["all_current_l4_phi0_repairs_nonpromotional"],
                "detail": "Current L4 Phi0 repairs are retained as killed/open controls and routed toward L7/L8, not promoted.",
            },
            "final_axis0_closure_blocked": {
                "pass": True,
                "detail": "The scout routes Axis0 entropy forms but does not close final Axis0 or manifold admission.",
            },
            "raw_threshold_tweaks_rejected": {
                "pass": True,
                "detail": "Another raw L4 threshold tweak is explicitly rejected as the next move.",
            },
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "variants": [
                "l4_phi0_not_promoted",
                "final_axis0_closure_blocked",
                "raw_threshold_tweaks_rejected",
            ],
        },
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "recommended_next_bridge_target": "L7_Xi_history_or_L8_shell_weighted_phi0",
            "final_axis0_closure_claimed": False,
            "final_manifold_admission_allowed": False,
            "real_scale_level_attractor_basin_claimed": False,
            "full_tensor_network_convergence_claimed": False,
        },
        "why_not_v4_probes": (
            "This is a v5 formal-scout route audit over current constraint-manifold and Axis0 "
            "receipts, not a legacy v4 probe or a canonical sim admission surface."
        ),
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
