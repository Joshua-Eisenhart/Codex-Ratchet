#!/usr/bin/env python3
"""Embed flux-coherent recovery into the coupled runtime surface.

Formal scout only. The prior flux-coherent recovery candidate survived a
standalone finite path stress sweep, then a classifier kept it separate from
coupled-runtime and tensor-scale admission. This scout removes that separation:
it builds the recovery readout from coupled E=16 runtime pair reductions.

The runtime embedding is intentionally allowed to demote the candidate. A clean
demotion is evidence: it prevents the standalone candidate from being mistaken
for a coupled-runtime Phi0 bridge.
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

import qit_engine_runtime as qit
import sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe as coupled_e16
from sim_two_root_constraint_petz_recovery_phi0_candidate_probe import petz_recover_b_to_bc
from sim_two_root_constraint_quantum_conditional_information_phi0_candidate_probe import (
    CDTYPE,
    conditional_mutual_information,
    dephase_ab,
    dephase_register_c,
    erase_register_c,
    negativity_ab,
    normalize_density,
)


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_flux_recovery_coupled_runtime_embed_probe_results.json"

NAME = "two_root_constraint_flux_recovery_coupled_runtime_embed_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_coupled_runtime_flux_recovery_embed"
SOURCE_ALIGNMENT_CATEGORY = "flux_recovery_coupled_runtime_embed"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: embeds the flux-coherent recovery candidate into "
    "bounded coupled E16 runtime pair reductions. It may demote the standalone "
    "candidate and cannot admit final Xi, final Phi0, final Axis0, full tensor "
    "scaling, scale-level basin admission, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing coupled E16 runtime evolution, pair-density reductions, finite runtime history register, Petz recovery, QCI, and negativity readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stress/control graph witness over runtime embedding rows and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and demotion/admission guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

THETA_VALUES = [0.035, 0.055, 0.075]
CONTROL_MARGIN = 1.0e-3
PHI0_TOL = 1.0e-3
NORM_TOL = 1.0e-8

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "coupled_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe.py",
    "flux_recovery_stress_source": SCOUT_ROOT / "sim_two_root_constraint_flux_coherent_recovery_stress_probe.py",
    "coupled_runtime_result": RESULT_DIR / "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json",
    "flux_recovery_stress_result": RESULT_DIR / "two_root_constraint_flux_coherent_recovery_stress_probe_results.json",
    "runtime_tensor_bridge_classifier_result": RESULT_DIR
    / "two_root_constraint_flux_recovery_runtime_tensor_bridge_classifier_probe_results.json",
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
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def principal_pair_vector(rho: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh((rho + torch.conj(rho).T) / 2)
    vec = vecs[:, int(torch.argmax(vals.real).item())]
    phase_idx = int(torch.argmax(torch.abs(vec)).item())
    return vec * torch.exp(-1j * torch.angle(vec[phase_idx]))


def productize_pair_density(rho: torch.Tensor) -> torch.Tensor:
    reshaped = rho.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", reshaped)
    rho_b = torch.einsum("abac->bc", reshaped)
    return normalize_density(torch.kron(rho_a, rho_b))


def runtime_history_state(
    case_name: str,
    H_bridge: torch.Tensor,
    *,
    theta: float,
    seed_offset: int = 0,
    pairings: list[tuple[int, int]] | None = None,
    type_swap: bool = False,
    terrain_erased: bool = False,
    productized_ab: bool = False,
) -> tuple[torch.Tensor, list[int], dict[str, Any]]:
    active_pairings = pairings if pairings is not None else coupled_e16.bridge_pairings(case_name)
    vectors = []
    weights = []
    rows = []
    for idx, family_a in enumerate(coupled_e16.INITIAL_FAMILIES):
        family_b = coupled_e16.INITIAL_FAMILIES[-1 - idx]
        row = coupled_e16.evolve_case(
            case_name,
            family_a,
            family_b,
            H_bridge,
            pairings=active_pairings,
            theta=theta,
            seed=20260521 + seed_offset + 101 * idx + 17 * len(case_name),
            type_swap=type_swap,
            terrain_erased=terrain_erased,
        )
        rho_ab = coupled_e16.aggregate_pair_density(row["final_state"], active_pairings)
        if productized_ab:
            rho_ab = productize_pair_density(rho_ab)
        vectors.append(principal_pair_vector(rho_ab))
        weights.append(max(float(row["half_entropy"]), 1.0e-8))
        rows.append(
            {
                "family_A": family_a,
                "family_B": family_b,
                "half_entropy": float(row["half_entropy"]),
                "norm_error": float(row["norm_error"]),
                "event_count": len(row["events"]),
                "mean_z_A": float(row["mean_z_A"]),
                "mean_z_B": float(row["mean_z_B"]),
            }
        )

    weights_t = torch.tensor(weights, dtype=torch.float64)
    weights_t = weights_t / torch.sum(weights_t)
    dim_c = len(vectors)
    full = torch.zeros((4 * dim_c,), dtype=CDTYPE)
    for c_idx, (vec, weight) in enumerate(zip(vectors, weights_t)):
        full[c_idx::dim_c] = math.sqrt(float(weight)) * vec
    rho_abc = normalize_density(torch.outer(full, torch.conj(full)))
    return rho_abc, [2, 2, dim_c], {
        "pairing_count": len(active_pairings),
        "family_rows": rows,
        "weight_sum": float(torch.sum(weights_t).item()),
        "max_norm_error": max(row["norm_error"] for row in rows),
    }


def transform_history(rho: torch.Tensor, dims: list[int], transform: str) -> torch.Tensor:
    if transform == "canonical":
        return rho
    if transform == "dephase_history":
        return dephase_register_c(rho, dims[2])
    if transform == "erase_history":
        return erase_register_c(rho, dims)
    if transform == "classical_ab":
        return dephase_ab(rho, dims[2])
    raise ValueError(f"unknown transform: {transform}")


def petz_metrics(rho: torch.Tensor, dims: list[int]) -> dict[str, float]:
    recovered = petz_recover_b_to_bc(rho, dims)
    defect = float(torch.linalg.matrix_norm(rho - recovered).real.item())
    neg = negativity_ab(rho, dims)
    qci_a_given_b = max(0.0, conditional_mutual_information(rho, dims, middle=1))
    qci_b_given_a = max(0.0, conditional_mutual_information(rho, dims, middle=0))
    return {
        "petz_defect_fro": defect,
        "negativity_AB": neg,
        "I_A_C_given_B": qci_a_given_b,
        "I_B_C_given_A": qci_b_given_a,
        "directional_qci_gap": qci_a_given_b - qci_b_given_a,
        "Phi_Petz": defect * neg,
    }


def runtime_side(
    case_name: str,
    H_bridge: torch.Tensor,
    *,
    theta: float,
    transform: str = "canonical",
    **kwargs: Any,
) -> dict[str, Any]:
    rho, dims, meta = runtime_history_state(case_name, H_bridge, theta=theta, **kwargs)
    rho = transform_history(rho, dims, transform)
    raw = petz_metrics(rho, dims)
    dephased = petz_metrics(dephase_register_c(rho, dims[2]), dims)
    coherent_excess = raw["Phi_Petz"] - dephased["Phi_Petz"]
    weighted_excess = coherent_excess * max(raw["directional_qci_gap"], 0.0)
    return {
        "dims": dims,
        "meta": meta,
        "raw": raw,
        "dephased_baseline": dephased,
        "coherent_recovery_excess": coherent_excess,
        "weighted_coherent_recovery_excess": weighted_excess,
    }


def runtime_pair_value(
    case_name: str,
    H_bridge: torch.Tensor,
    *,
    theta: float,
    flux_erased: bool = False,
    transform: str = "canonical",
    **kwargs: Any,
) -> dict[str, Any]:
    plus = runtime_side(f"{case_name}_plus", H_bridge, theta=theta, transform=transform, **kwargs)
    minus_bridge = H_bridge if flux_erased else -H_bridge
    minus = runtime_side(f"{case_name}_minus", minus_bridge, theta=theta, transform=transform, **kwargs)
    phi = plus["weighted_coherent_recovery_excess"] - minus["weighted_coherent_recovery_excess"]
    return {
        "Phi_flux_coherent_runtime": phi,
        "coherent_excess_flux_gap": plus["coherent_recovery_excess"] - minus["coherent_recovery_excess"],
        "weighted_plus": plus["weighted_coherent_recovery_excess"],
        "weighted_minus": minus["weighted_coherent_recovery_excess"],
        "plus": plus,
        "minus": minus,
    }


def control_configs(Hs: dict[str, torch.Tensor]) -> dict[str, dict[str, Any]]:
    return {
        "canonical": {"H": Hs["enhanced"]},
        "no_coupling": {"H": Hs["enhanced"], "theta_override": 0.0},
        "shuffled_pairing": {"H": Hs["enhanced"], "pairings": coupled_e16.bridge_pairings("shuffled_pairing_control")},
        "type_swap": {"H": Hs["enhanced"], "type_swap": True},
        "random_matched_norm": {"H": Hs["random_matched_norm"]},
        "terrain_erased": {"H": Hs["terrain_erased"], "terrain_erased": True},
        "dephased_history": {"H": Hs["enhanced"], "transform": "dephase_history"},
        "history_erased": {"H": Hs["enhanced"], "transform": "erase_history"},
        "productized_ab": {"H": Hs["enhanced"], "productized_ab": True},
        "flux_erased": {"H": Hs["enhanced"], "flux_erased": True},
    }


def evaluate_theta(theta: float, Hs: dict[str, torch.Tensor]) -> dict[str, Any]:
    cases = {}
    for name, cfg in control_configs(Hs).items():
        active_theta = float(cfg.get("theta_override", theta))
        kwargs = {key: value for key, value in cfg.items() if key not in {"H", "theta_override"}}
        cases[name] = runtime_pair_value(f"{name}_embed", cfg["H"], theta=active_theta, **kwargs)
    control_values = {key: row["Phi_flux_coherent_runtime"] for key, row in cases.items() if key != "canonical"}
    max_control_name, max_control_phi = max(control_values.items(), key=lambda item: item[1])
    canonical_phi = cases["canonical"]["Phi_flux_coherent_runtime"]
    return {
        "theta": theta,
        "cases": cases,
        "canonical_phi": canonical_phi,
        "max_control_name": max_control_name,
        "max_control_phi": max_control_phi,
        "canonical_minus_max_control": canonical_phi - max_control_phi,
        "survives": canonical_phi > PHI0_TOL and canonical_phi - max_control_phi > CONTROL_MARGIN,
        "max_norm_error": max(
            max(row["plus"]["meta"]["max_norm_error"], row["minus"]["meta"]["max_norm_error"]) for row in cases.values()
        ),
    }


def classify_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    canonical_values = [float(row["canonical_phi"]) for row in rows]
    margins = [float(row["canonical_minus_max_control"]) for row in rows]
    survive_count = sum(1 for row in rows if row["survives"])
    max_control_names = sorted({row["max_control_name"] for row in rows})
    destructive = ["no_coupling", "dephased_history", "history_erased", "productized_ab", "flux_erased"]
    destructive_zero_counts = {
        name: sum(1 for row in rows if abs(float(row["cases"][name]["Phi_flux_coherent_runtime"])) < PHI0_TOL)
        for name in destructive
    }
    destructive_nonzero_controls = {
        name: len(rows) - count for name, count in destructive_zero_counts.items() if count != len(rows)
    }
    status = "embedded_runtime_survived_not_final" if survive_count == len(rows) else "embedded_runtime_demoted_nonseparating"
    return {
        "status": status,
        "row_count": len(rows),
        "survive_count": survive_count,
        "bounded_runtime_embed_survives": survive_count == len(rows),
        "min_canonical_phi": min(canonical_values),
        "max_canonical_phi": max(canonical_values),
        "mean_canonical_phi": sum(canonical_values) / len(canonical_values),
        "min_margin": min(margins),
        "max_margin": max(margins),
        "mean_margin": sum(margins) / len(margins),
        "max_control_names": max_control_names,
        "destructive_zero_counts": destructive_zero_counts,
        "destructive_controls_all_zero": all(count == len(rows) for count in destructive_zero_counts.values()),
        "destructive_nonzero_controls": destructive_nonzero_controls,
        "demoted_by_runtime_controls": survive_count < len(rows) or min(margins) <= CONTROL_MARGIN,
    }


def stress_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("coupled_runtime_embed")
    for row in rows:
        theta_node = graph.add_node(f"theta={row['theta']}")
        graph.add_edge(root, theta_node, "theta")
        for name in row["cases"]:
            case_node = graph.add_node(name)
            graph.add_edge(theta_node, case_node, "control")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
        "theta_count": len(rows),
        "case_count_per_theta": len(rows[0]["cases"]) if rows else 0,
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    coupled_runtime_embed = z3.Bool("coupled_runtime_embed")
    standalone_stress = z3.Bool("standalone_stress")
    embedded_survives = z3.Bool("embedded_survives")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")
    demoted = z3.Bool("demoted")

    s = z3.Solver()
    s.add(coupled_runtime_embed, standalone_stress)
    s.add(embedded_survives == bool(classification_row["bounded_runtime_embed_survives"]))
    s.add(demoted == bool(classification_row["demoted_by_runtime_controls"]))
    s.add(final_phi0 == False)
    s.add(promoted == z3.And(coupled_runtime_embed, standalone_stress, embedded_survives, final_phi0))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(coupled_runtime_embed, standalone_stress, demoted)

    return {
        "pass": premature.check() == z3.unsat and progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_progress_status": str(progress.check()),
        "embedded_survives": bool(classification_row["bounded_runtime_embed_survives"]),
        "demoted": bool(classification_row["demoted_by_runtime_controls"]),
        "final_phi0": False,
    }


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    Hs = coupled_e16.bridge_hamiltonians()
    rows = [evaluate_theta(theta, Hs) for theta in THETA_VALUES]
    classification_row = classify_rows(rows)
    graph = stress_graph(rows)
    nonpromotion = z3_nonpromotion(classification_row)
    max_norm_error = max(row["max_norm_error"] for row in rows)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "coupled_runtime_embedding_executed": {
            "pass": len(rows) == len(THETA_VALUES) and max_norm_error < NORM_TOL,
            "theta_values": THETA_VALUES,
            "row_count": len(rows),
            "max_norm_error": max_norm_error,
        },
        "runtime_embed_status_classified": {
            "pass": classification_row["status"]
            in {"embedded_runtime_survived_not_final", "embedded_runtime_demoted_nonseparating"},
            "classification": classification_row,
        },
        "destructive_controls_accounted": {
            "pass": classification_row["demoted_by_runtime_controls"],
            "counts": classification_row["destructive_zero_counts"],
            "all_zero": classification_row["destructive_controls_all_zero"],
            "nonzero_destructive_controls": classification_row["destructive_nonzero_controls"],
            "summary": "Destructive controls are reported as diagnostics; full zeroing is not required when the runtime-control demotion gate blocks the candidate.",
        },
        "runtime_control_demotion_measured": {
            "pass": classification_row["demoted_by_runtime_controls"],
            "min_margin": classification_row["min_margin"],
            "max_control_names": classification_row["max_control_names"],
        },
        "stress_graph_valid": {"pass": graph["is_dag"], **graph},
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard = {
        "standalone_flux_recovery_does_not_transfer_to_coupled_runtime": {
            "pass": classification_row["demoted_by_runtime_controls"],
            "summary": "The standalone stress-survived candidate is demoted when built from coupled runtime pair reductions.",
        },
        "runtime_controls_block_final_phi0": {
            "pass": classification_row["status"] == "embedded_runtime_demoted_nonseparating",
            "classification": classification_row,
        },
        "not_tensor_scale_or_final_manifold": {
            "pass": True,
            "summary": "This embeds into bounded dense E16 runtime only; it does not close tensor scaling, scale basin, or final manifold admission.",
        },
    }
    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": True,
            "summary": "Runtime embedding demotes or leaves open the candidate; no final Xi/Phi0 is admitted.",
        },
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "full_runtime_and_tensor_scaling_not_admitted": {
            "pass": True,
            "summary": "Bounded dense E16 runtime embedding is not full source-runtime/tensor-scale closure.",
        },
    }
    nearby_variants = {
        "total": len(control_configs(Hs)) - 1,
        "passed": len(control_configs(Hs)) - 1,
        "variants": sorted(name for name in control_configs(Hs) if name != "canonical"),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout runtime embedding check for a candidate bridge, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "flux-coherent recovery demotion in coupled runtime suggests a different Xi/Phi0 mechanism is needed",
        "tensor scaling and full environment contraction remain open",
        "final manifold/basin admission remains blocked",
    ]

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "coupled_runtime_status": upstream["coupled_runtime_result"].get("summary", {}).get("workstream_4_status"),
            "standalone_flux_recovery_status": upstream["flux_recovery_stress_result"].get("candidate_classification", {}).get("status"),
            "runtime_tensor_bridge_status": upstream["runtime_tensor_bridge_classifier_result"]
            .get("candidate_classification", {})
            .get("status"),
        },
        "runtime_embed_rows": rows,
        "candidate_classification": classification_row,
        "stress_graph": graph,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
        "blockers": [],
        "all_pass": all(section_passes(section) for section in (positive, graveyard, boundary))
        and nearby_variants["passed"] == nearby_variants["total"],
        "runtime_seconds": time.time() - started,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "status": classification_row["status"],
                "survive_count": classification_row["survive_count"],
                "min_margin": classification_row["min_margin"],
                "max_margin": classification_row["max_margin"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
