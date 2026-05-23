#!/usr/bin/env python3
"""Quantum-conditional-information Phi0 bridge candidate.

Formal scout only. This tests a non-additive Xi -> rho_ABC -> Phi0 candidate
after additive raw-incidence, path-weighted, boundary-capacity, and
free-energy candidates failed to separate from controls.

Candidate surface:

    rho_ABC = coherent finite Kraus-history dilation over a path register C
    QCI_AB_C = I(A:C|B) = S(AB) + S(BC) - S(B) - S(ABC)
    Phi_QCI = QCI_AB_C * negativity(AB) + I_c(A -> B)

The candidate is allowed to fail. A clean failure still narrows the Axis0/Phi0
search space without promoting final Xi, final Phi0, full FEP, or physics.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_quantum_conditional_information_phi0_candidate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "quantum_conditional_information_phi0_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite tripartite quantum-conditional-"
    "information Phi0 candidate. It does not admit final Xi, final Phi0, final "
    "Axis0, full FEP, Markov blanket ontology, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex density matrices, coherent Kraus-history "
            "registers, partial traces, entropy, negativity, and conditional "
            "information readouts"
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

CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def normalize_vec(vec: torch.Tensor) -> torch.Tensor:
    return vec / torch.linalg.vector_norm(vec)


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    return rho / torch.clamp(torch.real(torch.trace(rho)), min=EPS)


def density(vec: torch.Tensor) -> torch.Tensor:
    return torch.outer(vec, torch.conj(vec))


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize_vec(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * axis


def dephase(axis: torch.Tensor, q: float) -> list[torch.Tensor]:
    return [math.sqrt(1.0 - q) * I2, math.sqrt(q) * axis]


def amplitude_down(gamma: float) -> list[torch.Tensor]:
    k0 = torch.tensor([[math.sqrt(1 - gamma), 0], [0, 1]], dtype=CDTYPE)
    k1 = torch.tensor([[0, 0], [math.sqrt(gamma), 0]], dtype=CDTYPE)
    return [k0, k1]


def amplitude_up(gamma: float) -> list[torch.Tensor]:
    k0 = torch.tensor([[1, 0], [0, math.sqrt(1 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=CDTYPE)
    return [k0, k1]


def zz_entangler(theta: float) -> torch.Tensor:
    return math.cos(theta / 2.0) * I4 - 1j * math.sin(theta / 2.0) * torch.kron(Z, Z)


def initial_cut_vector(*, entangled: bool) -> torch.Tensor:
    psi_a = spinor(0.18, -0.31, 0.53)
    psi_b = spinor(-0.22, 0.47, 0.71)
    psi = torch.kron(psi_a, psi_b)
    if entangled:
        psi = zz_entangler(0.88) @ psi
    return normalize_vec(psi)


def instruments(flux: int, *, commuting: bool, reversed_order: bool) -> list[list[torch.Tensor]]:
    if commuting:
        rows = [
            [unitary(Z, flux * 0.29)],
            dephase(Z, 0.18),
            [unitary(Z, flux * -0.21)],
            dephase(Z, 0.12),
        ]
    else:
        rows = [
            [unitary(Z, flux * 0.29)],
            dephase(X, 0.18),
            [unitary(X, flux * -0.23)],
            amplitude_down(0.17) if flux > 0 else amplitude_up(0.17),
        ]
    return list(reversed(rows)) if reversed_order else rows


def partial_trace(rho: torch.Tensor, dims: list[int], keep: list[int]) -> torch.Tensor:
    n = len(dims)
    keep = list(keep)
    trace = [idx for idx in range(n) if idx not in keep]
    perm = keep + trace + [idx + n for idx in keep] + [idx + n for idx in trace]
    reshaped = rho.reshape(*(dims + dims)).permute(perm)
    dim_keep = math.prod(dims[idx] for idx in keep)
    dim_trace = math.prod(dims[idx] for idx in trace)
    reshaped = reshaped.reshape(dim_keep, dim_trace, dim_keep, dim_trace)
    return torch.einsum("abcb->ac", reshaped)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def coherent_information_ab(rho_abc: torch.Tensor, dims: list[int]) -> float:
    rho_ab = partial_trace(rho_abc, dims, [0, 1])
    rho_b = partial_trace(rho_abc, dims, [1])
    return entropy(rho_b) - entropy(rho_ab)


def conditional_mutual_information(rho_abc: torch.Tensor, dims: list[int], middle: int) -> float:
    if middle == 1:
        rho_ab = partial_trace(rho_abc, dims, [0, 1])
        rho_bc = partial_trace(rho_abc, dims, [1, 2])
        rho_b = partial_trace(rho_abc, dims, [1])
        return entropy(rho_ab) + entropy(rho_bc) - entropy(rho_b) - entropy(rho_abc)
    if middle == 0:
        rho_ab = partial_trace(rho_abc, dims, [0, 1])
        rho_ac = partial_trace(rho_abc, dims, [0, 2])
        rho_a = partial_trace(rho_abc, dims, [0])
        return entropy(rho_ab) + entropy(rho_ac) - entropy(rho_a) - entropy(rho_abc)
    raise ValueError("middle must be 0 or 1 for this scout")


def negativity_ab(rho_abc: torch.Tensor, dims: list[int]) -> float:
    rho_ab = partial_trace(rho_abc, dims, [0, 1])
    reshaped = rho_ab.reshape(2, 2, 2, 2)
    pt_b = reshaped.permute(0, 3, 2, 1).reshape(4, 4)
    vals = torch.linalg.eigvalsh(hermitize(pt_b)).real
    return float(torch.sum(torch.clamp(-vals, min=0.0)).item())


def dephase_register_c(rho_abc: torch.Tensor, dim_c: int) -> torch.Tensor:
    out = torch.zeros_like(rho_abc)
    for idx in range(dim_c):
        proj_c = torch.zeros((dim_c, dim_c), dtype=CDTYPE)
        proj_c[idx, idx] = 1
        proj = torch.kron(I4, proj_c)
        out = out + proj @ rho_abc @ proj
    return normalize_density(out)


def erase_register_c(rho_abc: torch.Tensor, dims: list[int]) -> torch.Tensor:
    rho_ab = partial_trace(rho_abc, dims, [0, 1])
    rho_c = partial_trace(rho_abc, dims, [2])
    return normalize_density(torch.kron(rho_ab, rho_c))


def dephase_ab(rho_abc: torch.Tensor, dim_c: int) -> torch.Tensor:
    out = torch.zeros_like(rho_abc)
    for idx in range(4):
        proj_ab = torch.zeros((4, 4), dtype=CDTYPE)
        proj_ab[idx, idx] = 1
        proj = torch.kron(proj_ab, torch.eye(dim_c, dtype=CDTYPE))
        out = out + proj @ rho_abc @ proj
    return normalize_density(out)


def coherent_history_state(
    *,
    entangled: bool = True,
    commuting: bool = False,
    reversed_order: bool = False,
    flux: int = 1,
    collapse_register: bool = False,
) -> tuple[torch.Tensor, list[int], dict[str, Any]]:
    psi0 = initial_cut_vector(entangled=entangled)
    rows = instruments(flux, commuting=commuting, reversed_order=reversed_order)
    branch_vectors = []
    branch_probs = []
    for outcomes in itertools.product(*[range(len(row)) for row in rows]):
        k = I2
        for stage, outcome in zip(rows, outcomes):
            k = stage[outcome] @ k
        vec_ab = torch.kron(k, I2) @ psi0
        branch_vectors.append(vec_ab)
        branch_probs.append(float(torch.linalg.vector_norm(vec_ab).square().real.item()))

    if collapse_register:
        vec = normalize_vec(sum(branch_vectors))
        rho = density(vec).reshape(4, 1, 4, 1).reshape(4, 4)
        return rho, [2, 2, 1], {"branch_count": len(branch_vectors), "branch_probs": branch_probs}

    dim_c = len(branch_vectors)
    full = torch.zeros((4 * dim_c,), dtype=CDTYPE)
    for c_idx, vec_ab in enumerate(branch_vectors):
        for ab_idx in range(4):
            full[ab_idx * dim_c + c_idx] = vec_ab[ab_idx]
    full = normalize_vec(full)
    rho = density(full)
    return rho, [2, 2, dim_c], {"branch_count": dim_c, "branch_probs": branch_probs}


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

    qci_ac_given_b = max(0.0, conditional_mutual_information(rho, dims, middle=1))
    qci_bc_given_a = max(0.0, conditional_mutual_information(rho, dims, middle=0))
    neg = negativity_ab(rho, dims)
    ic = coherent_information_ab(rho, dims)
    phi = qci_ac_given_b * neg + ic
    return {
        "name": name,
        "dims": dims,
        "transform": transform,
        "branch_count": meta["branch_count"],
        "branch_probability_total": sum(meta["branch_probs"]),
        "branch_probability_span": max(meta["branch_probs"]) - min(meta["branch_probs"]),
        "S_ABC": entropy(rho),
        "I_c_A_to_B": ic,
        "I_A_C_given_B": qci_ac_given_b,
        "I_B_C_given_A": qci_bc_given_a,
        "directional_qci_gap": qci_ac_given_b - qci_bc_given_a,
        "negativity_AB": neg,
        "Phi_QCI": phi,
    }


def classify_cases(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    canonical = cases["canonical"]["Phi_QCI"]
    controls = {key: row["Phi_QCI"] for key, row in cases.items() if key != "canonical"}
    max_control_name, max_control_phi = max(controls.items(), key=lambda item: item[1])
    min_control_name, min_control_phi = min(controls.items(), key=lambda item: item[1])
    canonical_minus_max = canonical - max_control_phi
    canonical_minus_history_erased = canonical - cases["history_erased"]["Phi_QCI"]
    canonical_minus_dephased_history = canonical - cases["dephased_history"]["Phi_QCI"]
    canonical_minus_product = canonical - cases["product"]["Phi_QCI"]
    canonical_minus_commuting = canonical - cases["commuting"]["Phi_QCI"]
    canonical_minus_reversed = canonical - cases["reversed_order"]["Phi_QCI"]
    canonical_minus_collapsed_register = canonical - cases["collapsed_register"]["Phi_QCI"]

    history_register_load_bearing = abs(canonical_minus_history_erased) > 0.02
    coherent_history_load_bearing = abs(canonical_minus_dephased_history) > 0.02
    entanglement_condition_load_bearing = abs(canonical_minus_product) > 0.02
    noncommuting_path_sensitive = abs(canonical_minus_commuting) > 0.02
    order_sensitive = abs(canonical_minus_reversed) > 0.005
    control_separated = canonical_minus_max > 0.02
    first_rung_survives = (
        control_separated
        and history_register_load_bearing
        and entanglement_condition_load_bearing
        and noncommuting_path_sensitive
    )
    status = "first_rung_control_separated_not_final" if first_rung_survives else "open_or_killed_nonseparating"
    return {
        "status": status,
        "first_rung_survives": first_rung_survives,
        "control_separated": control_separated,
        "history_register_load_bearing": history_register_load_bearing,
        "coherent_history_load_bearing": coherent_history_load_bearing,
        "entanglement_condition_load_bearing": entanglement_condition_load_bearing,
        "noncommuting_path_sensitive": noncommuting_path_sensitive,
        "order_sensitive": order_sensitive,
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
        "canonical_minus_classical_ab": canonical - cases["classical_ab"]["Phi_QCI"],
        "canonical_minus_collapsed_register": canonical_minus_collapsed_register,
        "canonical_minus_opposite_flux": canonical - cases["opposite_flux"]["Phi_QCI"],
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite_tripartite_cut")
    noncommuting = z3.Bool("noncommuting_paths")
    history_register = z3.Bool("history_register")
    entanglement = z3.Bool("entanglement_condition")
    first_rung = z3.Bool("first_rung")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    s = z3.Solver()
    s.add(finite, noncommuting, history_register, entanglement)
    s.add(first_rung == bool(classification_row["first_rung_survives"]))
    s.add(final_phi0 == False)
    s.add(promoted == z3.And(finite, noncommuting, history_register, entanglement, first_rung, final_phi0))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(finite, noncommuting, history_register, entanglement)

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
        "tripartite_cut_surface_built": {
            "pass": all(math.isfinite(row["Phi_QCI"]) for row in cases.values()),
            "case_names": sorted(cases),
            "canonical_components": {
                key: cases["canonical"][key]
                for key in [
                    "I_c_A_to_B",
                    "I_A_C_given_B",
                    "I_B_C_given_A",
                    "directional_qci_gap",
                    "negativity_AB",
                    "Phi_QCI",
                    "branch_count",
                ]
            },
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
                "summary": "The tripartite QCI candidate separates in this bounded fixture but still has no final Xi/Phi0 admission.",
            },
            "full_stress_not_run": {
                "pass": True,
                "summary": "This scout does not provide scale, tensor-carrier, broad seed, or full source-runtime stress.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "No physical, holographic, or ER=EPR claim follows from a finite tripartite cut functional.",
            },
            "markov_blanket_ontology_not_admitted": {
                "pass": True,
                "summary": "The path register is a finite quantum history register, not a classical Markov blanket ontology.",
            },
        }
    else:
        graveyard_companions = {
            "candidate_not_control_separated": {
                "pass": not classification_row["control_separated"],
                "summary": "The canonical tripartite QCI candidate does not beat all controls by the admission margin.",
            },
            "qci_signal_not_sufficient_for_admission": {
                "pass": True,
                "summary": "Tripartite conditional-information structure alone is not enough to admit Phi0 without control separation.",
            },
            "history_register_not_sufficient_for_admission": {
                "pass": True,
                "summary": "A finite coherent history register is useful evidence, not a final bridge by itself.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "No physical, holographic, or ER=EPR claim follows from a killed/open finite tripartite cut functional.",
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
            "summary": "This is a finite QIT/FEP-adjacent tripartite cut candidate, not full FEP or a classical Markov-chain replacement.",
        },
    }
    nearby_variants = {
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "total": len(graveyard_companions),
        "variants": sorted(graveyard_companions),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout candidate classifier over a finite tripartite QIT bridge, not a canonical v4 physics probe.",
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
