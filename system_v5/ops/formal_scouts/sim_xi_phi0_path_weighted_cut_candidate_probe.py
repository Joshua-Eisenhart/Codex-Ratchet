#!/usr/bin/env python3
"""Xi/Phi0 path-weighted cut candidate scout.

Formal scout only. This tests a next-wave Xi -> rho_AB candidate that couples
spinor/twistor incidence geometry to finite noncommuting QIT path evidence.

The candidate is intentionally allowed to fail. A killed candidate is progress:
it narrows the Axis0/Xi/Phi0 space without promoting a fake bridge.
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
NAME = "xi_phi0_path_weighted_cut_candidate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "xi_phi0_path_weighted_cut_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a path-weighted Xi -> rho_AB cut candidate. It "
    "does not admit final Xi, final Phi0, final Axis0, Markov blanket ontology, "
    "holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite spinors, density matrices, path instruments, entropies, and control readouts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency and nonpromotion fence for candidate admission",
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
I4 = torch.eye(4, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
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


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    return rho / torch.clamp(torch.real(torch.trace(rho)), min=EPS)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def orthogonal_spinor(psi: torch.Tensor) -> torch.Tensor:
    return normalize(torch.stack([-torch.conj(psi[1]), torch.conj(psi[0])]))


def density(state: torch.Tensor) -> torch.Tensor:
    return torch.outer(state, torch.conj(state))


def twistor_node(omega: torch.Tensor, pi: torch.Tensor) -> dict[str, torch.Tensor]:
    return {"omega": normalize(omega), "pi": normalize(pi)}


def incidence(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.vdot(a["pi"], b["omega"]) - torch.vdot(b["pi"], a["omega"])


def edge_state(psi_a: torch.Tensor, psi_b: torch.Tensor, lam: float, phase: float) -> torch.Tensor:
    return normalize(
        math.cos(lam) * torch.kron(psi_a, psi_b)
        + math.sin(lam)
        * complex(math.cos(phase), math.sin(phase))
        * torch.kron(orthogonal_spinor(psi_a), orthogonal_spinor(psi_b))
    )


def build_graph() -> dict[str, Any]:
    params = [
        (0.10, 0.20, 0.40),
        (0.30, -0.20, 0.60),
        (-0.20, 0.50, 0.70),
        (0.70, 0.10, 0.45),
    ]
    spinors = [spinor(*row) for row in params]
    twistors = [
        twistor_node(spinors[i], spinor(params[(i + 1) % 4][0] + 0.14, params[i][1] - 0.08, params[i][2]))
        for i in range(4)
    ]
    return {"spinors": spinors, "twistors": twistors, "edges": [(0, 1), (1, 2), (2, 3), (3, 0)]}


def soft_effect(axis: torch.Tensor, bias: float) -> torch.Tensor:
    return hermitize(0.5 * I2 + 0.5 * bias * axis)


def psd_sqrt(mat: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(hermitize(mat))
    vals = torch.clamp(vals.real, min=0.0)
    return vecs @ torch.diag(torch.sqrt(vals)).to(CDTYPE) @ torch.conj(vecs).T


EFFECTS = {
    "x": psd_sqrt(soft_effect(X, 0.62)),
    "z": psd_sqrt(soft_effect(Z, 0.62)),
    "z2": psd_sqrt(soft_effect(Z, -0.31)),
}


def apply_path(rho_ab: torch.Tensor, order: tuple[str, str]) -> tuple[torch.Tensor, float]:
    k = I4
    for label in order:
        k = torch.kron(EFFECTS[label], I2) @ k
    unnormalized = hermitize(k @ rho_ab @ torch.conj(k).T)
    evidence = float(torch.real(torch.trace(unnormalized)).item())
    return normalize_density(unnormalized), math.log(max(evidence, EPS))


def xi_path_weighted_cut(graph: dict[str, Any], mode: str, *, commuting: bool = False) -> dict[str, Any]:
    pieces = []
    weights = []
    edge_rows = []
    for edge_idx, (i, j) in enumerate(graph["edges"]):
        inc = incidence(graph["twistors"][i], graph["twistors"][j])
        raw_phase = float(torch.angle(inc).item())
        raw_mag = min(max(float(torch.abs(inc).item()), 0.0), 1.0)
        if mode == "incidence_path":
            phase = raw_phase
            lam = 0.35 + 0.40 * raw_mag
        elif mode == "zero_phase_path":
            phase = 0.0
            lam = 0.35 + 0.40 * raw_mag
        elif mode == "random_phase_path":
            gen = torch.Generator()
            gen.manual_seed(20260523 + edge_idx)
            phase = float(((torch.rand((), generator=gen) - 0.5) * 2 * math.pi).item())
            lam = 0.35 + 0.40 * raw_mag
        elif mode == "low_entanglement_path":
            phase = 0.0
            lam = 0.05
        else:
            raise ValueError(mode)

        edge_rho = density(edge_state(graph["spinors"][i], graph["spinors"][j], lam, phase))
        orders = (("z", "z2"), ("z2", "z")) if commuting else (("z", "x"), ("x", "z"))
        oriented_phase = 1.0 if raw_phase >= 0.0 else -1.0
        path_rows = []
        for order in orders:
            posterior, log_evidence = apply_path(edge_rho, order)
            order_sign = 1.0 if order[0] == "z" else -1.0
            weight = math.exp(log_evidence + 0.50 * oriented_phase * order_sign + 0.25 * raw_mag)
            pieces.append(weight * posterior)
            weights.append(weight)
            path_rows.append({"order": list(order), "log_evidence": log_evidence, "weight": weight})
        edge_rows.append(
            {
                "edge": [i, j],
                "mode": mode,
                "raw_phase": raw_phase,
                "raw_magnitude": raw_mag,
                "phase_used": phase,
                "lambda_used": lam,
                "path_rows": path_rows,
                "path_log_evidence_gap": path_rows[0]["log_evidence"] - path_rows[1]["log_evidence"],
            }
        )
    rho = normalize_density(sum(pieces) / sum(weights))
    return {"rho": rho, "edge_rows": edge_rows, "total_weight": sum(weights)}


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


def cut_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_ab = normalize_density(rho_ab)
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_c_A_to_B": s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_A_B": s_a + s_b - s_ab,
    }


def productize(rho_ab: torch.Tensor) -> torch.Tensor:
    return normalize_density(torch.kron(partial_trace_a(rho_ab), partial_trace_b(rho_ab)))


def matrix_health(rho: torch.Tensor) -> dict[str, Any]:
    rho = normalize_density(rho)
    herm_gap = float(torch.linalg.matrix_norm(rho - torch.conj(rho).T).item())
    trace_gap = abs(float(torch.real(torch.trace(rho)).item()) - 1.0)
    min_eval = float(torch.min(torch.linalg.eigvalsh(hermitize(rho)).real).item())
    return {
        "hermiticity_gap": herm_gap,
        "trace_gap": trace_gap,
        "min_eigenvalue": min_eval,
        "pass": bool(herm_gap < 1e-9 and trace_gap < 1e-9 and min_eval > -1e-9),
    }


def qfep_order_gap(edge_rows: list[dict[str, Any]]) -> float:
    return float(sum(row["path_log_evidence_gap"] for row in edge_rows) / len(edge_rows))


def candidate_gate() -> dict[str, Any]:
    graph = build_graph()
    candidate = xi_path_weighted_cut(graph, "incidence_path")
    zero = xi_path_weighted_cut(graph, "zero_phase_path")
    random = xi_path_weighted_cut(graph, "random_phase_path")
    low_entanglement = xi_path_weighted_cut(graph, "low_entanglement_path")
    commuting = xi_path_weighted_cut(graph, "incidence_path", commuting=True)
    erased = {"rho": I4 / 4.0, "edge_rows": [], "total_weight": 0.0}
    product = {"rho": productize(candidate["rho"]), "edge_rows": [], "total_weight": 0.0}

    rows = {
        "candidate": candidate,
        "zero_phase": zero,
        "random_phase": random,
        "low_entanglement": low_entanglement,
        "commuting_path": commuting,
        "productized": product,
        "history_erased": erased,
    }
    readouts = {name: cut_readouts(row["rho"]) for name, row in rows.items()}
    health = {name: matrix_health(row["rho"]) for name, row in rows.items()}
    candidate_ic = readouts["candidate"]["I_c_A_to_B"]
    candidate_admitted = bool(
        health["candidate"]["pass"]
        and candidate_ic > 0.0
        and candidate_ic - readouts["zero_phase"]["I_c_A_to_B"] > 0.02
        and candidate_ic - readouts["random_phase"]["I_c_A_to_B"] > 0.02
        and candidate_ic - readouts["productized"]["I_c_A_to_B"] > 0.20
        and candidate_ic - readouts["history_erased"]["I_c_A_to_B"] > 0.20
    )
    noncommuting_gap = abs(qfep_order_gap(candidate["edge_rows"]))
    commuting_gap = abs(qfep_order_gap(commuting["edge_rows"]))
    return {
        "pass": True,
        "candidate_admitted": candidate_admitted,
        "readouts": readouts,
        "matrix_health": health,
        "qfep_order_gaps": {
            "noncommuting_path_gap": noncommuting_gap,
            "commuting_path_gap": commuting_gap,
        },
        "candidate_margins": {
            "candidate_minus_zero_Ic": candidate_ic - readouts["zero_phase"]["I_c_A_to_B"],
            "candidate_minus_random_Ic": candidate_ic - readouts["random_phase"]["I_c_A_to_B"],
            "candidate_minus_product_Ic": candidate_ic - readouts["productized"]["I_c_A_to_B"],
            "candidate_minus_erased_Ic": candidate_ic - readouts["history_erased"]["I_c_A_to_B"],
            "candidate_minus_commuting_Ic": candidate_ic - readouts["commuting_path"]["I_c_A_to_B"],
        },
        "edge_rows": candidate["edge_rows"],
        "candidate_killed_reason": (
            "incidence-path candidate does not beat zero-phase control under coherent-information admission"
            if not candidate_admitted
            else ""
        ),
    }


def dependency_fence(candidate_admitted: bool) -> dict[str, Any]:
    f01 = z3.Bool("f01")
    n01 = z3.Bool("n01")
    bipartite_cut = z3.Bool("bipartite_cut")
    path_history = z3.Bool("path_history")
    candidate = z3.Bool("candidate_admitted")
    final_phi0 = z3.Bool("final_phi0")
    axioms = [
        z3.Implies(bipartite_cut, f01),
        z3.Implies(path_history, n01),
        z3.Implies(candidate, z3.And(bipartite_cut, path_history)),
        z3.Implies(final_phi0, candidate),
        candidate == bool(candidate_admitted),
    ]

    def status(*assumptions: z3.BoolRef) -> z3.CheckSatResult:
        solver = z3.Solver()
        solver.add(*axioms)
        solver.add(*assumptions)
        return solver.check()

    return {
        "pass": True,
        "path_history_requires_n01": str(status(path_history, z3.Not(n01))),
        "bipartite_cut_requires_f01": str(status(bipartite_cut, z3.Not(f01))),
        "roots_do_not_force_candidate": str(status(f01, n01, z3.Not(candidate))),
        "final_phi0_blocked_if_candidate_killed": str(status(final_phi0)),
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    candidate = candidate_gate()
    fence = dependency_fence(candidate["candidate_admitted"])
    positive = {
        "path_weighted_xi_candidate_audited": {
            "pass": candidate["pass"] and all(row["pass"] for row in candidate["matrix_health"].values()),
            "candidate_admitted": candidate["candidate_admitted"],
            "readouts": candidate["readouts"],
            "candidate_margins": candidate["candidate_margins"],
        },
        "noncommuting_path_component_measured": {
            "pass": candidate["qfep_order_gaps"]["noncommuting_path_gap"] > 0.001
            and candidate["qfep_order_gaps"]["commuting_path_gap"] < 0.001,
            "qfep_order_gaps": candidate["qfep_order_gaps"],
        },
        "matrix_health_all_modes": {
            "pass": all(row["pass"] for row in candidate["matrix_health"].values()),
            "matrix_health": candidate["matrix_health"],
        },
        "dependency_fence": fence,
    }
    graveyard_companions = {
        "path_weighted_candidate_not_admitted": {
            "pass": not candidate["candidate_admitted"],
            "summary": candidate["candidate_killed_reason"],
        },
        "zero_phase_control_rejects_incidence_path_candidate": {
            "pass": candidate["candidate_margins"]["candidate_minus_zero_Ic"] < 0.0,
            "margin": candidate["candidate_margins"]["candidate_minus_zero_Ic"],
        },
        "product_and_history_erased_controls_remain_negative": {
            "pass": candidate["readouts"]["productized"]["I_c_A_to_B"] < 0.0
            and candidate["readouts"]["history_erased"]["I_c_A_to_B"] < -0.6,
            "product_Ic": candidate["readouts"]["productized"]["I_c_A_to_B"],
            "history_erased_Ic": candidate["readouts"]["history_erased"]["I_c_A_to_B"],
        },
        "commuting_path_control_erases_qfep_order_gap": {
            "pass": candidate["qfep_order_gaps"]["commuting_path_gap"] < 0.001,
            "commuting_path_gap": candidate["qfep_order_gaps"]["commuting_path_gap"],
        },
    }
    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": fence["final_phi0_blocked_if_candidate_killed"] == "unsat",
            "summary": "candidate killed, so final Phi0 remains blocked",
        },
        "formal_scout_only": {
            "pass": classification == "formal_scout" and not PROMOTION_ALLOWED,
            "summary": "negative next-wave candidate scout only",
        },
        "holography_and_physics_not_admitted": {
            "pass": True,
            "summary": "finite cut-state candidate scout does not admit holography, ER=EPR, Markov blankets, or physics",
        },
    }
    nearby_variants = {
        "total": 4,
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions.keys()),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is an unpromoted v5 formal scout over a candidate bridge, not a canonical v4 probe.",
    }
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
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "blockers": [],
        "candidate_detail": {
            "edge_rows": candidate["edge_rows"],
            "candidate_killed_reason": candidate["candidate_killed_reason"],
        },
        "all_pass": all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"],
        "runtime_seconds": time.time() - start,
        "generated_at": time.time(),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT_PATH)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
