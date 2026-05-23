#!/usr/bin/env python3
"""Petz-recovery Phi0 bridge candidate.

Formal scout only. This tests a finite quantum-Markov/recovery-error candidate
after additive free-energy and tripartite conditional-information candidates
failed to separate from controls.

Candidate surface:

    rho_ABC = coherent finite Kraus-history dilation over a path register C
    R_Petz(B -> BC)(rho_AB) = rho_BC^(1/2)
        (rho_B^(-1/2) rho_AB rho_B^(-1/2) tensor I_C)
        rho_BC^(1/2)
    Delta_Petz = ||rho_ABC - R_Petz(rho_AB)||_F
    Phi_Petz = Delta_Petz * negativity(AB)

The candidate is allowed to fail. A clean failure still narrows the Axis0/Phi0
search space without promoting final Xi, final Phi0, full FEP, or physics.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

from sim_two_root_constraint_quantum_conditional_information_phi0_candidate_probe import (
    CDTYPE,
    I4,
    as_jsonable,
    coherent_history_state,
    coherent_information_ab,
    conditional_mutual_information,
    dephase_ab,
    dephase_register_c,
    entropy,
    erase_register_c,
    hermitize,
    negativity_ab,
    normalize_density,
    partial_trace,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_petz_recovery_phi0_candidate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "petz_recovery_phi0_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite Petz-recovery/quantum-Markov Phi0 "
    "candidate. It does not admit final Xi, final Phi0, final Axis0, full FEP, "
    "Markov blanket ontology, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex density matrices, PSD matrix powers, Petz "
            "recovery, entropy, negativity, and finite cut readouts"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency and nonpromotion fence for bridge classification",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

EPS = 1e-9


def psd_power(mat: torch.Tensor, power: float) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(hermitize(mat))
    vals = torch.clamp(vals.real, min=EPS)
    return vecs @ torch.diag((vals**power).to(CDTYPE)) @ torch.conj(vecs).T


def petz_recover_b_to_bc(rho_abc: torch.Tensor, dims: list[int]) -> torch.Tensor:
    dim_a, dim_b, dim_c = dims
    if dim_c == 1:
        return normalize_density(rho_abc.clone())

    rho_ab = partial_trace(rho_abc, dims, [0, 1])
    rho_bc = partial_trace(rho_abc, dims, [1, 2])
    rho_b = partial_trace(rho_abc, dims, [1])

    rho_b_inv_sqrt = psd_power(rho_b, -0.5)
    rho_bc_sqrt = psd_power(rho_bc, 0.5)
    eye_a = torch.eye(dim_a, dtype=CDTYPE)
    eye_c = torch.eye(dim_c, dtype=CDTYPE)

    b_lift = torch.kron(eye_a, rho_b_inv_sqrt)
    inner_ab = b_lift @ rho_ab @ b_lift
    inner_abc = torch.kron(inner_ab, eye_c)
    bc_lift = torch.kron(eye_a, rho_bc_sqrt)
    recovered = bc_lift @ inner_abc @ bc_lift
    return normalize_density(recovered)


def evaluate_case(name: str, transform: str = "canonical", **kwargs: Any) -> dict[str, Any]:
    rho, dims, meta = coherent_history_state(**kwargs)
    if transform == "dephase_history":
        rho = dephase_register_c(rho, dims[2])
    elif transform == "erase_history":
        rho = erase_register_c(rho, dims)
    elif transform == "classical_ab":
        rho = dephase_ab(rho, dims[2])
    elif transform != "canonical":
        raise ValueError(f"unknown transform: {transform}")

    recovered = petz_recover_b_to_bc(rho, dims)
    defect = float(torch.linalg.matrix_norm(rho - recovered).real.item())
    qci = max(0.0, conditional_mutual_information(rho, dims, middle=1))
    reverse_qci = max(0.0, conditional_mutual_information(rho, dims, middle=0))
    neg = negativity_ab(rho, dims)
    ic = coherent_information_ab(rho, dims)
    phi = defect * neg
    return {
        "name": name,
        "dims": dims,
        "transform": transform,
        "branch_count": meta["branch_count"],
        "branch_probability_total": sum(meta["branch_probs"]),
        "S_ABC": entropy(rho),
        "S_recovered": entropy(recovered),
        "petz_defect_fro": defect,
        "I_A_C_given_B": qci,
        "I_B_C_given_A": reverse_qci,
        "I_c_A_to_B": ic,
        "negativity_AB": neg,
        "Phi_Petz": phi,
    }


def classify_cases(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    canonical = cases["canonical"]["Phi_Petz"]
    controls = {key: row["Phi_Petz"] for key, row in cases.items() if key != "canonical"}
    max_control_name, max_control_phi = max(controls.items(), key=lambda item: item[1])
    min_control_name, min_control_phi = min(controls.items(), key=lambda item: item[1])

    canonical_minus_history_erased = canonical - cases["history_erased"]["Phi_Petz"]
    canonical_minus_dephased_history = canonical - cases["dephased_history"]["Phi_Petz"]
    canonical_minus_product = canonical - cases["product"]["Phi_Petz"]
    canonical_minus_commuting = canonical - cases["commuting"]["Phi_Petz"]
    canonical_minus_reversed = canonical - cases["reversed_order"]["Phi_Petz"]
    canonical_minus_collapsed = canonical - cases["collapsed_register"]["Phi_Petz"]
    canonical_minus_max = canonical - max_control_phi
    raw_defect_minus_commuting = cases["canonical"]["petz_defect_fro"] - cases["commuting"]["petz_defect_fro"]
    raw_defect_minus_reversed = cases["canonical"]["petz_defect_fro"] - cases["reversed_order"]["petz_defect_fro"]

    petz_defect_load_bearing = cases["canonical"]["petz_defect_fro"] > 0.02
    history_register_load_bearing = abs(canonical_minus_history_erased) > 0.02
    entanglement_condition_load_bearing = abs(canonical_minus_product) > 0.02
    noncommuting_path_sensitive = abs(raw_defect_minus_commuting) > 0.02
    order_sensitive = abs(raw_defect_minus_reversed) > 0.005
    collapsed_register_rejected = abs(canonical_minus_collapsed) > 0.02
    control_separated = canonical_minus_max > 0.02
    first_rung_survives = (
        control_separated
        and petz_defect_load_bearing
        and history_register_load_bearing
        and entanglement_condition_load_bearing
        and noncommuting_path_sensitive
    )
    status = "first_rung_control_separated_not_final" if first_rung_survives else "open_or_killed_nonseparating"
    return {
        "status": status,
        "first_rung_survives": first_rung_survives,
        "control_separated": control_separated,
        "petz_defect_load_bearing": petz_defect_load_bearing,
        "history_register_load_bearing": history_register_load_bearing,
        "entanglement_condition_load_bearing": entanglement_condition_load_bearing,
        "noncommuting_path_sensitive": noncommuting_path_sensitive,
        "order_sensitive": order_sensitive,
        "collapsed_register_rejected": collapsed_register_rejected,
        "canonical_phi": canonical,
        "max_control_name": max_control_name,
        "max_control_phi": max_control_phi,
        "min_control_name": min_control_name,
        "min_control_phi": min_control_phi,
        "canonical_minus_max_control": canonical_minus_max,
        "canonical_minus_history_erased": canonical_minus_history_erased,
        "canonical_minus_dephased_history": canonical_minus_dephased_history,
        "canonical_minus_product": canonical_minus_product,
        "canonical_minus_commuting": canonical_minus_commuting,
        "canonical_minus_reversed": canonical_minus_reversed,
        "raw_defect_minus_commuting": raw_defect_minus_commuting,
        "raw_defect_minus_reversed": raw_defect_minus_reversed,
        "canonical_minus_classical_ab": canonical - cases["classical_ab"]["Phi_Petz"],
        "canonical_minus_collapsed_register": canonical_minus_collapsed,
        "canonical_minus_opposite_flux": canonical - cases["opposite_flux"]["Phi_Petz"],
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite_tripartite_cut")
    noncommuting = z3.Bool("noncommuting_paths")
    recovery = z3.Bool("petz_recovery")
    entanglement = z3.Bool("entanglement_condition")
    first_rung = z3.Bool("first_rung")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    s = z3.Solver()
    s.add(finite, noncommuting, recovery, entanglement)
    s.add(first_rung == bool(classification_row["first_rung_survives"]))
    s.add(final_phi0 == False)
    s.add(promoted == z3.And(finite, noncommuting, recovery, entanglement, first_rung, final_phi0))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(finite, noncommuting, recovery, entanglement)

    return {
        "pass": premature.check() == z3.unsat and progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_progress_status": str(progress.check()),
        "final_phi0": False,
    }


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    cases = {
        "canonical": evaluate_case("canonical"),
        "history_erased": evaluate_case("history_erased", transform="erase_history"),
        "dephased_history": evaluate_case("dephased_history", transform="dephase_history"),
        "product": evaluate_case("product", entangled=False),
        "commuting": evaluate_case("commuting", commuting=True),
        "reversed_order": evaluate_case("reversed_order", reversed_order=True),
        "classical_ab": evaluate_case("classical_ab", transform="classical_ab"),
        "collapsed_register": evaluate_case("collapsed_register", collapse_register=True),
        "opposite_flux": evaluate_case("opposite_flux", flux=-1),
    }
    classification_row = classify_cases(cases)
    nonpromotion = z3_nonpromotion(classification_row)

    positive = {
        "petz_recovery_surface_built": {
            "pass": all(math.isfinite(row["Phi_Petz"]) for row in cases.values()),
            "case_names": sorted(cases),
            "canonical_components": {
                key: cases["canonical"][key]
                for key in [
                    "petz_defect_fro",
                    "I_A_C_given_B",
                    "I_c_A_to_B",
                    "negativity_AB",
                    "Phi_Petz",
                    "branch_count",
                ]
            },
        },
        "petz_defect_signal_measured": {
            "pass": classification_row["petz_defect_load_bearing"],
            "canonical_petz_defect": cases["canonical"]["petz_defect_fro"],
        },
        "history_register_signal_measured": {
            "pass": classification_row["history_register_load_bearing"],
            "canonical_minus_history_erased": classification_row["canonical_minus_history_erased"],
            "canonical_minus_collapsed_register": classification_row["canonical_minus_collapsed_register"],
        },
        "entanglement_condition_measured": {
            "pass": classification_row["entanglement_condition_load_bearing"],
            "canonical_minus_product": classification_row["canonical_minus_product"],
        },
        "noncommuting_path_difference_measured": {
            "pass": classification_row["noncommuting_path_sensitive"],
            "canonical_minus_commuting": classification_row["canonical_minus_commuting"],
            "raw_defect_minus_commuting": classification_row["raw_defect_minus_commuting"],
        },
        "candidate_status_classified": {
            "pass": True,
            "classification": classification_row,
        },
        "z3_nonpromotion_guard": nonpromotion,
    }

    if classification_row["first_rung_survives"]:
        graveyard_companions = {
            "first_rung_is_not_final_phi0": {
                "pass": True,
                "summary": "The Petz-recovery candidate separates in this bounded fixture but still has no final Xi/Phi0 admission.",
            },
            "full_stress_not_run": {
                "pass": True,
                "summary": "This scout does not provide scale, tensor-carrier, broad seed, or full source-runtime stress.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "No physical, holographic, or ER=EPR claim follows from a finite Petz-recovery defect.",
            },
            "markov_blanket_ontology_not_admitted": {
                "pass": True,
                "summary": "The recovery map is a finite quantum Markov diagnostic, not a classical Markov blanket ontology.",
            },
        }
    else:
        graveyard_companions = {
            "candidate_not_control_separated": {
                "pass": not classification_row["control_separated"],
                "summary": "The canonical Petz-recovery candidate does not beat all controls by the admission margin.",
            },
            "recovery_signal_not_sufficient_for_admission": {
                "pass": True,
                "summary": "Petz-recovery defect structure alone is not enough to admit Phi0 without control separation.",
            },
            "near_reversed_order_control_blocks_admission": {
                "pass": abs(classification_row["canonical_minus_reversed"]) <= 0.02,
                "summary": "The reversed-order control remains too close to the canonical Petz readout for admission.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "No physical, holographic, or ER=EPR claim follows from a killed/open finite Petz-recovery defect.",
            },
        }

    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": nonpromotion["premature_promotion_status"] == "unsat",
            "summary": "The candidate is either killed/open or first-rung only; final Phi0 remains false in the dependency fence.",
        },
        "formal_scout_only": {
            "pass": True,
            "summary": "The receipt is nonpromotional and remains under the formal-scout claim ceiling.",
        },
        "full_fep_not_admitted": {
            "pass": True,
            "summary": "This is a finite QIT/FEP-adjacent recovery diagnostic, not full FEP or a classical Markov-chain replacement.",
        },
    }
    nearby_variants = {
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "total": len(graveyard_companions),
        "variants": sorted(graveyard_companions),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout candidate classifier over a finite Petz-recovery bridge, not a canonical v4 physics probe.",
    }
    open_gaps = [
        "final Xi/Phi0 remains open",
        "scale, seed, tensor-carrier, and stress controls are not closed by this candidate",
        "full FEP, Markov blanket ontology, holography, ER=EPR, and physics remain unadmitted",
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
        "cases": cases,
        "candidate_classification": classification_row,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
        "blockers": [],
        "all_pass": all(section_passes(section) for section in (positive, graveyard_companions, boundary))
        and nearby_variants["passed"] == nearby_variants["total"],
        "runtime_seconds": time.time() - start,
        "generated_at": time.time(),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "status": classification_row["status"],
                "canonical_minus_max_control": classification_row["canonical_minus_max_control"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
