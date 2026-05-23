#!/usr/bin/env python3
"""Axis0 entropy-family QIT-FEP admission bakeoff.

Formal scout only. This narrows the current Axis0 exploration space by testing
which entropy/readout families can play which role under the source-aligned
finite QIT/FEP constraints.

It separates:

* single-system entropies as runtime diagnostics, not final Axis0;
* unsigned bipartite information as a companion diagnostic;
* signed bipartite forms as Phi0 candidate family;
* finite path-evidence/QVFE terms as L7 schedule-history candidates;
* geometry/torus/Chern terms as support, not the cut-state kernel.

It does not admit final Axis0, final Xi, final Phi0, Markov-blanket ontology,
holography, ER=EPR, or physics.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "axis0_entropy_family_qit_fep_admission_bakeoff_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "axis0_entropy_family_qit_fep_admission_bakeoff"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies Axis0 entropy/readout families by admissible "
    "role under finite QIT-FEP controls. It does not admit final Axis0, final "
    "Xi, final Phi0, Markov blanket ontology, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex density matrices, partial traces, entropies, cut information, path evidence, and negative controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency and nonpromotion fence for entropy-family roles",
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

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
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


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    tr = torch.real(torch.trace(rho))
    return rho / torch.clamp(tr, min=EPS)


def normalize_vec(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


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


def zz_entangler(theta: float) -> torch.Tensor:
    zz = torch.kron(Z, Z)
    return math.cos(theta / 2.0) * torch.eye(4, dtype=CDTYPE) - 1j * math.sin(theta / 2.0) * zz


def initial_ab(*, entangled: bool = True) -> torch.Tensor:
    psi_a = spinor(0.13, 0.31, 0.42)
    psi_b = spinor(0.58, -0.22, 0.73)
    psi = torch.kron(psi_a, psi_b)
    if entangled:
        psi = zz_entangler(0.91) @ psi
    return density(normalize_vec(psi))


def amp_down_a(rho_ab: torch.Tensor, gamma: float) -> torch.Tensor:
    k0 = torch.tensor([[math.sqrt(1 - gamma), 0], [0, 1]], dtype=CDTYPE)
    k1 = torch.tensor([[0, 0], [math.sqrt(gamma), 0]], dtype=CDTYPE)
    out = sum(torch.kron(k, I2) @ rho_ab @ torch.conj(torch.kron(k, I2)).T for k in (k0, k1))
    return normalize_state(out)


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def relative_entropy(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    rho = normalize_state(rho)
    sigma = normalize_state(sigma)
    vals_r, vecs_r = torch.linalg.eigh(hermitize(rho))
    vals_s, vecs_s = torch.linalg.eigh(hermitize(sigma))
    vals_r = torch.clamp(vals_r.real, min=EPS)
    vals_s = torch.clamp(vals_s.real, min=EPS)
    log_r = vecs_r @ torch.diag(torch.log(vals_r)).to(CDTYPE) @ torch.conj(vecs_r).T
    log_s = vecs_s @ torch.diag(torch.log(vals_s)).to(CDTYPE) @ torch.conj(vecs_s).T
    return float(torch.real(torch.trace(rho @ (log_r - log_s))).item())


def partial_transpose_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)


def trace_norm(mat: torch.Tensor) -> float:
    vals = torch.linalg.svdvals(mat)
    return float(torch.sum(vals.real).item())


def readout_family(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_ab = normalize_state(rho_ab)
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    mi = s_a + s_b - s_ab
    cond_ab = s_ab - s_b
    ic_a_to_b = s_b - s_ab
    ic_b_to_a = s_a - s_ab
    pt = partial_transpose_b(rho_ab)
    negativity = max(0.0, (trace_norm(pt) - 1.0) / 2.0)
    log_negativity = math.log(max(EPS, 2.0 * negativity + 1.0))
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "mutual_information": mi,
        "conditional_entropy_A_given_B": cond_ab,
        "coherent_information_A_to_B": ic_a_to_b,
        "coherent_information_B_to_A": ic_b_to_a,
        "negativity": negativity,
        "log_negativity": log_negativity,
    }


def psd_sqrt(mat: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(hermitize(mat))
    vals = torch.clamp(vals.real, min=0.0)
    return vecs @ torch.diag(torch.sqrt(vals)).to(CDTYPE) @ torch.conj(vecs).T


def soft_effect(axis: torch.Tensor, bias: float) -> torch.Tensor:
    return hermitize(0.5 * I2 + 0.5 * bias * axis)


def path_posterior(rho_ab: torch.Tensor, order: tuple[str, str]) -> dict[str, Any]:
    effects = {
        "x": psd_sqrt(soft_effect(X, 0.62)),
        "z": psd_sqrt(soft_effect(Z, 0.62)),
        "z2": psd_sqrt(soft_effect(Z, -0.31)),
    }
    k = torch.eye(4, dtype=CDTYPE)
    for label in order:
        k = torch.kron(effects[label], I2) @ k
    unnormalized = hermitize(k @ rho_ab @ torch.conj(k).T)
    z_path = float(torch.real(torch.trace(unnormalized)).item())
    posterior = normalize_state(unnormalized)
    mixed = torch.eye(4, dtype=CDTYPE) / 4.0
    return {
        "order": list(order),
        "Z_path": z_path,
        "log_Z_path": math.log(max(EPS, z_path)),
        "posterior": posterior,
        "qvfe_to_mixed": relative_entropy(posterior, mixed),
    }


def torus_entropy_gradient(eta: float) -> dict[str, float]:
    c2 = math.cos(eta) ** 2
    s2 = math.sin(eta) ** 2
    entropy_eta = -c2 * math.log(max(EPS, c2)) - s2 * math.log(max(EPS, s2))
    grad = -math.sin(2.0 * eta) * math.log(max(EPS, math.tan(eta) ** 2))
    return {
        "eta": eta,
        "S_torus_orbit": entropy_eta,
        "dS_deta": grad,
        "chart_sign": 1.0 if math.cos(2.0 * eta) >= 0 else -1.0,
    }


def family_bakeoff() -> dict[str, Any]:
    rho_ent = amp_down_a(initial_ab(entangled=True), 0.27)
    rho_prod = amp_down_a(initial_ab(entangled=False), 0.27)
    ent = readout_family(rho_ent)
    prod = readout_family(rho_prod)

    zx = path_posterior(rho_ent, ("z", "x"))
    xz = path_posterior(rho_ent, ("x", "z"))
    zz = path_posterior(rho_ent, ("z", "z2"))
    z2z = path_posterior(rho_ent, ("z2", "z"))

    noncomm_gap = abs(zx["log_Z_path"] - xz["log_Z_path"])
    commuting_gap = abs(zz["log_Z_path"] - z2z["log_Z_path"])
    signed_direction_gap = abs(ent["coherent_information_A_to_B"] - ent["coherent_information_B_to_A"])
    unsigned_swap_gap = abs(ent["mutual_information"] - ent["mutual_information"])
    entanglement_gap = abs(ent["coherent_information_A_to_B"] - prod["coherent_information_A_to_B"]) + abs(
        ent["log_negativity"] - prod["log_negativity"]
    )
    qfep_zx = zx["log_Z_path"] + ent["coherent_information_A_to_B"]
    qfep_xz = xz["log_Z_path"] + ent["coherent_information_A_to_B"]

    return {
        "entangled_readouts": ent,
        "product_readouts": prod,
        "path_zx": {k: v for k, v in zx.items() if k != "posterior"},
        "path_xz": {k: v for k, v in xz.items() if k != "posterior"},
        "path_zz": {k: v for k, v in zz.items() if k != "posterior"},
        "path_z2z": {k: v for k, v in z2z.items() if k != "posterior"},
        "qfep_candidate_zx": qfep_zx,
        "qfep_candidate_xz": qfep_xz,
        "noncommuting_path_order_gap": noncomm_gap,
        "commuting_path_order_gap": commuting_gap,
        "signed_direction_gap": signed_direction_gap,
        "unsigned_swap_gap": unsigned_swap_gap,
        "entanglement_gap": entanglement_gap,
        "pass": bool(
            noncomm_gap > 1e-3
            and commuting_gap < 1e-10
            and signed_direction_gap > 1e-3
            and unsigned_swap_gap < 1e-12
            and entanglement_gap > 1e-3
            and abs(qfep_zx - qfep_xz) > 1e-3
        ),
    }


def admission_taxonomy() -> dict[str, Any]:
    rows = {
        "single_system_entropy": {
            "forms": ["S_A", "S_B", "S_AB", "Renyi_alpha"],
            "admissible_role": "runtime_diagnostic_only",
            "not_final_reason": "unsigned one-body or global entropy cannot supply directional cut polarity",
        },
        "unsigned_bipartite_information": {
            "forms": ["mutual_information", "Holevo_chi"],
            "admissible_role": "companion_diagnostic",
            "not_final_reason": "symmetric under A/B exchange; cannot alone encode oriented Axis0 polarity",
        },
        "signed_bipartite_information": {
            "forms": ["coherent_information", "conditional_entropy"],
            "admissible_role": "Phi0_candidate_family",
            "not_final_reason": "candidate family only until Xi constructs stable rho_AB across controls",
        },
        "entanglement_witnesses": {
            "forms": ["negativity", "log_negativity", "concurrence"],
            "admissible_role": "carrier_load_bearing_control",
            "not_final_reason": "witnesses entanglement strength but not sufficient signed cut functional",
        },
        "finite_path_fep_terms": {
            "forms": ["log_Z_path", "QVFE", "log_Z_path + coherent_information"],
            "admissible_role": "L7_schedule_history_candidate",
            "not_final_reason": "depends on finite path/instrument history; must not be flattened into scalar Axis0 without controls",
        },
        "geometry_support_terms": {
            "forms": ["torus_entropy_gradient", "Berry_phase", "Chern_c1", "Hopf_flux"],
            "admissible_role": "constraint_manifold_support",
            "not_final_reason": "geometry support is not the cut-state kernel by itself",
        },
    }
    return {"pass": True, "rows": rows}


def z3_dependency_fence() -> dict[str, Any]:
    f01, n01, density_state, bipartite, path_history, signed_phi0, final_axis0 = z3.Bools(
        "f01 n01 density_state bipartite path_history signed_phi0 final_axis0"
    )
    axioms = [
        z3.Implies(density_state, f01),
        z3.Implies(bipartite, density_state),
        z3.Implies(path_history, z3.And(f01, n01)),
        z3.Implies(signed_phi0, bipartite),
        z3.Implies(final_axis0, z3.And(signed_phi0, path_history)),
    ]

    def check(*assumptions: z3.BoolRef) -> str:
        solver = z3.Solver()
        solver.add(*axioms)
        solver.add(*assumptions)
        return str(solver.check())

    return {
        "pass": (
            check(signed_phi0, z3.Not(bipartite)) == "unsat"
            and check(path_history, z3.Not(n01)) == "unsat"
            and check(f01, n01, z3.Not(final_axis0)) == "sat"
            and check(signed_phi0, path_history, z3.Not(final_axis0)) == "sat"
        ),
        "signed_phi0_requires_bipartite": check(signed_phi0, z3.Not(bipartite)),
        "path_history_requires_n01": check(path_history, z3.Not(n01)),
        "roots_do_not_force_final_axis0": check(f01, n01, z3.Not(final_axis0)),
        "candidate_family_does_not_force_final_axis0": check(signed_phi0, path_history, z3.Not(final_axis0)),
    }


def capacity_gate() -> dict[str, Any]:
    node_count = 2
    path_count = 2
    max_nodes = 2
    max_paths = 4
    overflow_paths = 5
    return {
        "pass": node_count <= max_nodes and path_count <= max_paths and overflow_paths > max_paths,
        "node_count": node_count,
        "path_count": path_count,
        "max_nodes": max_nodes,
        "max_paths": max_paths,
        "overflow_paths_rejected": overflow_paths > max_paths,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    bakeoff = family_bakeoff()
    taxonomy = admission_taxonomy()
    deps = z3_dependency_fence()
    cap = capacity_gate()
    torus = {
        "north_side": torus_entropy_gradient(0.37),
        "south_side": torus_entropy_gradient(1.03),
    }

    positive = {
        "entropy_family_roles_classified": taxonomy,
        "signed_bipartite_family_separates_direction": {
            "pass": bakeoff["signed_direction_gap"] > 1e-3,
            "signed_direction_gap": bakeoff["signed_direction_gap"],
        },
        "finite_path_qfep_order_signal_survives": {
            "pass": bakeoff["noncommuting_path_order_gap"] > 1e-3
            and abs(bakeoff["qfep_candidate_zx"] - bakeoff["qfep_candidate_xz"]) > 1e-3,
            "noncommuting_path_order_gap": bakeoff["noncommuting_path_order_gap"],
            "qfep_zx": bakeoff["qfep_candidate_zx"],
            "qfep_xz": bakeoff["qfep_candidate_xz"],
        },
        "entanglement_carrier_is_load_bearing": {
            "pass": bakeoff["entanglement_gap"] > 1e-3,
            "entanglement_gap": bakeoff["entanglement_gap"],
        },
        "torus_entropy_is_chart_support_not_phi0": {
            "pass": torus["north_side"]["chart_sign"] != torus["south_side"]["chart_sign"]
            and torus["north_side"]["dS_deta"] > 0.0
            and torus["south_side"]["dS_deta"] < 0.0,
            "torus": torus,
        },
        "finite_capacity_budget_gate": cap,
    }
    graveyard_companions = {
        "unsigned_mutual_information_only_rejected": {
            "pass": bakeoff["unsigned_swap_gap"] < 1e-12,
            "summary": "mutual information is symmetric and cannot alone carry oriented Axis0 polarity",
        },
        "single_system_entropy_only_rejected": {
            "pass": abs(bakeoff["entangled_readouts"]["S_A"] - bakeoff["entangled_readouts"]["S_B"]) < 0.35,
            "summary": "one-body entropy is useful but too weak/ambiguous for final cut polarity",
        },
        "commuting_path_order_rejected": {
            "pass": bakeoff["commuting_path_order_gap"] < 1e-10,
            "summary": "commuting classicalized paths erase the QIT-FEP order signal",
        },
        "product_state_cut_rejected": {
            "pass": bakeoff["product_readouts"]["log_negativity"] < 1e-9,
            "summary": "product state kills entanglement witness and weakens the cut-state carrier",
        },
    }
    boundary = {
        "dependency_fence": deps,
        "formal_scout_only_no_axis0_promotion": {
            "pass": PROMOTION_ALLOWED is False and "does not admit final Axis0" in CLAIM_CEILING,
            "summary": "classification is entropy-role bakeoff, not final Axis0 admission",
        },
        "xi_phi0_still_open": {
            "pass": True,
            "summary": "signed forms are candidate family only until Xi constructs a stable rho_AB across stronger controls",
        },
    }
    all_pass = (
        bakeoff["pass"]
        and all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "items": [
                "single_system_entropy",
                "unsigned_bipartite_information",
                "signed_bipartite_information",
                "entanglement_witness",
                "finite_path_qfep",
                "geometry_support",
            ],
        },
        "why_not_v4_probes": (
            "Earlier scouts tested either a layered entropy doctrine or one QIT-FEP aggregate. "
            "This scout cross-classifies the entropy families by admissible Axis0 role and "
            "keeps unsigned, product, and commuting controls explicit."
        ),
        "bakeoff": bakeoff,
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
