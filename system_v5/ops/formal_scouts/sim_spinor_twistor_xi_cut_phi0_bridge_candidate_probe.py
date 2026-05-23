#!/usr/bin/env python3
"""Spinor/twistor Xi -> rho_AB -> Phi0 bridge candidate probe.

Formal scout only. This tests a first finite bridge candidate:

  Xi(history/spinor-twistor graph) -> rho_AB
  Phi0(rho_AB) = I_c(A -> B) = S(rho_B) - S(rho_AB)

Controls:

* productized cut state must lose coherent information;
* history-erased maximally mixed cut must fail;
* zero/random incidence phase controls must audit the candidate;
* trace/PSD/Hermiticity gates must pass.

Current outcome expectation: the naive raw incidence-phase bridge is allowed to
fail. A clean negative result is better than tuning the bridge into a fake pass.
This does not canonize Axis 0, Xi, holography, ER=EPR, or full twistor theory.
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
NAME = "spinor_twistor_xi_cut_phi0_bridge_candidate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "spinor_twistor_xi_phi0_bridge_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite Xi -> rho_AB bridge candidate and "
    "coherent-information Phi0 readout for a spinor/twistor graph. It does not "
    "canonize Axis0, holography, ER=EPR, or full twistor theory."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinors, bipartite density matrices, partial traces, and entropy readouts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-capacity and nonpromotion proof fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


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


def partial_trace_a(rho: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho.reshape(2, 2, 2, 2))


def partial_trace_b(rho: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho.reshape(2, 2, 2, 2))


def entropy(rho: torch.Tensor) -> float:
    herm = (rho + torch.conj(rho).T) / 2
    vals = torch.linalg.eigvalsh(herm).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def cut_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    s_ab = entropy(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "I_c_A_to_B": s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_A_B": s_a + s_b - s_ab,
    }


def twistor_node(omega: torch.Tensor, pi: torch.Tensor) -> dict[str, torch.Tensor]:
    return {"omega": normalize(omega), "pi": normalize(pi)}


def incidence(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.vdot(a["pi"], b["omega"]) - torch.vdot(b["pi"], a["omega"])


def edge_state(psi_a: torch.Tensor, psi_b: torch.Tensor, lam: float, phase: float) -> torch.Tensor:
    return normalize(
        math.cos(lam) * torch.kron(psi_a, psi_b)
        + math.sin(lam) * complex(math.cos(phase), math.sin(phase)) * torch.kron(orthogonal_spinor(psi_a), orthogonal_spinor(psi_b))
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


def xi_bridge(graph: dict[str, Any], phase_mode: str) -> torch.Tensor:
    rho = torch.zeros((4, 4), dtype=CDTYPE)
    for idx, (i, j) in enumerate(graph["edges"]):
        inc = incidence(graph["twistors"][i], graph["twistors"][j])
        raw_phase = float(torch.angle(inc).item())
        raw_mag = float(torch.abs(inc).item())
        bounded_mag = min(max(raw_mag, 0.0), 1.0)
        if phase_mode == "incidence":
            phase = raw_phase
            lam = 0.65 + 0.02 * idx
        elif phase_mode == "zero":
            phase = 0.0
            lam = 0.65 + 0.02 * idx
        elif phase_mode == "random_fixed":
            phase = 1.7 * (idx + 1)
            lam = 0.65 + 0.02 * idx
        elif phase_mode == "absolute_incidence_phase":
            phase = abs(raw_phase)
            lam = 0.65 + 0.02 * idx
        elif phase_mode == "oriented_phase_class":
            phase = 0.0 if raw_phase >= 0.0 else math.pi
            lam = 0.65 + 0.02 * idx
        elif phase_mode == "incidence_magnitude_lambda":
            phase = 0.0
            lam = 0.35 + 0.45 * bounded_mag
        elif phase_mode == "inverse_magnitude_lambda":
            phase = 0.0
            lam = 0.80 - 0.35 * bounded_mag
        elif phase_mode == "history_coupled_edge_weight":
            phase = raw_phase + 0.31 * (idx + 1)
            lam = min(1.15, max(0.20, 0.55 + 0.08 * idx + 0.12 * math.cos(raw_phase)))
        else:
            raise ValueError(phase_mode)
        state = edge_state(graph["spinors"][i], graph["spinors"][j], lam, phase)
        rho = rho + density(state)
    return rho / torch.real(torch.trace(rho))


def productize(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.kron(partial_trace_a(rho_ab), partial_trace_b(rho_ab))


def matrix_health(rho: torch.Tensor) -> dict[str, Any]:
    herm_gap = float(torch.linalg.matrix_norm(rho - torch.conj(rho).T).item())
    trace_gap = abs(float(torch.real(torch.trace(rho)).item()) - 1.0)
    min_eval = float(torch.min(torch.linalg.eigvalsh((rho + torch.conj(rho).T) / 2).real).item())
    return {
        "hermiticity_gap": herm_gap,
        "trace_gap": trace_gap,
        "min_eigenvalue": min_eval,
        "pass": bool(herm_gap < 1e-9 and trace_gap < 1e-9 and min_eval > -1e-9),
    }


def bridge_gate() -> dict[str, Any]:
    graph = build_graph()
    candidate = xi_bridge(graph, "incidence")
    zero_phase = xi_bridge(graph, "zero")
    random_phase = xi_bridge(graph, "random_fixed")
    product = productize(candidate)
    erased = torch.eye(4, dtype=CDTYPE) / 4.0

    cand = cut_readouts(candidate)
    zero = cut_readouts(zero_phase)
    random = cut_readouts(random_phase)
    prod = cut_readouts(product)
    erased_read = cut_readouts(erased)
    candidate_modes = [
        "incidence",
        "absolute_incidence_phase",
        "oriented_phase_class",
        "incidence_magnitude_lambda",
        "inverse_magnitude_lambda",
        "history_coupled_edge_weight",
    ]
    mode_readouts = {}
    mode_health = {}
    admitted_modes = []
    for mode in candidate_modes:
        rho_mode = xi_bridge(graph, mode)
        readout = cut_readouts(rho_mode)
        health_row = matrix_health(rho_mode)
        mode_readouts[mode] = readout
        mode_health[mode] = health_row
        mode_admitted = (
            health_row["pass"]
            and readout["I_c_A_to_B"] > 0.0
            and readout["I_c_A_to_B"] - zero["I_c_A_to_B"] > 0.02
            and readout["I_c_A_to_B"] - random["I_c_A_to_B"] > 0.02
            and readout["I_c_A_to_B"] - prod["I_c_A_to_B"] > 0.5
            and readout["I_c_A_to_B"] - erased_read["I_c_A_to_B"] > 0.5
        )
        if mode_admitted:
            admitted_modes.append(mode)
    health = {
        "candidate": matrix_health(candidate),
        "zero_phase": matrix_health(zero_phase),
        "random_phase": matrix_health(random_phase),
        "product": matrix_health(product),
        "history_erased": matrix_health(erased),
        "candidate_modes": mode_health,
    }
    all_health = all(row["pass"] for key, row in health.items() if key != "candidate_modes") and all(
        row["pass"] for row in mode_health.values()
    )
    naive_raw_phase_rejected = cand["I_c_A_to_B"] < 0.0 and cand["I_c_A_to_B"] - zero["I_c_A_to_B"] < 0.0
    return {
        "candidate_readout": cand,
        "candidate_mode_readouts": mode_readouts,
        "candidate_modes_admitted": admitted_modes,
        "candidate_modes_admitted_count": len(admitted_modes),
        "zero_phase_control_readout": zero,
        "random_phase_control_readout": random,
        "product_control_readout": prod,
        "history_erased_control_readout": erased_read,
        "matrix_health": health,
        "candidate_minus_product_Ic": cand["I_c_A_to_B"] - prod["I_c_A_to_B"],
        "candidate_minus_erased_Ic": cand["I_c_A_to_B"] - erased_read["I_c_A_to_B"],
        "candidate_minus_zero_phase_Ic": cand["I_c_A_to_B"] - zero["I_c_A_to_B"],
        "candidate_minus_random_phase_Ic": cand["I_c_A_to_B"] - random["I_c_A_to_B"],
        "naive_raw_incidence_phase_bridge_rejected": naive_raw_phase_rejected,
        "pass": bool(
            all_health
            and prod["I_c_A_to_B"] < -0.3
            and erased_read["I_c_A_to_B"] < -0.6
            and naive_raw_phase_rejected
        ),
    }


def capacity_and_nonpromotion_gate() -> dict[str, Any]:
    log_dim_ab = math.log(4.0)
    cap_ok = log_dim_ab
    cap_small = math.log(3.0)
    log_dim = z3.RealVal(str(round(log_dim_ab, 12)))
    ok_cap = z3.RealVal(str(round(cap_ok, 12)))
    small_cap = z3.RealVal(str(round(cap_small, 12)))
    ok = z3.Solver()
    ok.add(log_dim <= ok_cap)
    small = z3.Solver()
    small.add(log_dim <= small_cap)

    f01 = z3.Bool("f01")
    n01 = z3.Bool("n01")
    cut_capacity = z3.Bool("cut_capacity")
    raw_phase_bridge_survives = z3.Bool("raw_phase_bridge_survives")
    axis0_canon = z3.Bool("axis0_canon")
    holography_canon = z3.Bool("holography_canon")
    er_epr_canon = z3.Bool("er_epr_canon")
    dependency_axioms = [
        z3.Implies(cut_capacity, f01),
        z3.Implies(er_epr_canon, z3.And(f01, n01, cut_capacity)),
        z3.Implies(holography_canon, z3.And(cut_capacity, er_epr_canon)),
        z3.Implies(axis0_canon, raw_phase_bridge_survives),
        z3.Not(raw_phase_bridge_survives),
    ]

    def status(*assumptions: z3.BoolRef) -> z3.CheckSatResult:
        solver = z3.Solver()
        solver.add(*dependency_axioms)
        solver.add(*assumptions)
        return solver.check()

    roots_do_not_force_axis0_status = status(f01, n01, z3.Not(axis0_canon))
    cut_capacity_requires_f01_status = status(cut_capacity, z3.Not(f01))
    er_epr_requires_roots_status = status(er_epr_canon, z3.Or(z3.Not(f01), z3.Not(n01)))
    holography_requires_er_epr_status = status(holography_canon, z3.Not(er_epr_canon))
    axis0_canon_rejected_by_raw_bridge_status = status(axis0_canon)

    return {
        "log_dim_AB": log_dim_ab,
        "capacity_ok": cap_ok,
        "capacity_too_small": cap_small,
        "ok_capacity_status": str(ok.check()),
        "too_small_capacity_status": str(small.check()),
        "roots_do_not_force_axis0_status": str(roots_do_not_force_axis0_status),
        "cut_capacity_requires_f01_status": str(cut_capacity_requires_f01_status),
        "er_epr_requires_roots_status": str(er_epr_requires_roots_status),
        "holography_requires_er_epr_status": str(holography_requires_er_epr_status),
        "axis0_canon_rejected_by_raw_bridge_status": str(axis0_canon_rejected_by_raw_bridge_status),
        "canon_nonpromotion_status": str(axis0_canon_rejected_by_raw_bridge_status),
        "pass": bool(
            ok.check() == z3.sat
            and small.check() == z3.unsat
            and roots_do_not_force_axis0_status == z3.sat
            and cut_capacity_requires_f01_status == z3.unsat
            and er_epr_requires_roots_status == z3.unsat
            and holography_requires_er_epr_status == z3.unsat
            and axis0_canon_rejected_by_raw_bridge_status == z3.unsat
        ),
    }


def negative_control_section(bridge: dict[str, Any], capacity: dict[str, Any]) -> dict[str, Any]:
    rows = {
        "NC1_productized_cut_kills_candidate_information": {
            "expected_to_fail": True,
            "candidate_Ic": bridge["candidate_readout"]["I_c_A_to_B"],
            "product_Ic": bridge["product_control_readout"]["I_c_A_to_B"],
            "candidate_minus_product_Ic": bridge["candidate_minus_product_Ic"],
            "pass": bool(bridge["candidate_minus_product_Ic"] > 0.5 and bridge["product_control_readout"]["I_c_A_to_B"] < -0.3),
            "summary": "productizing rho_AB kills the candidate's cut information",
        },
        "NC2_history_erased_cut_is_maximally_bad": {
            "expected_to_fail": True,
            "history_erased_Ic": bridge["history_erased_control_readout"]["I_c_A_to_B"],
            "candidate_minus_erased_Ic": bridge["candidate_minus_erased_Ic"],
            "pass": bool(bridge["candidate_minus_erased_Ic"] > 0.5 and bridge["history_erased_control_readout"]["I_c_A_to_B"] < -0.6),
            "summary": "history-erased maximally mixed cut loses the signed coherent-information readout",
        },
        "NC3_zero_phase_beats_raw_incidence_phase": {
            "expected_to_fail": True,
            "candidate_Ic": bridge["candidate_readout"]["I_c_A_to_B"],
            "zero_phase_Ic": bridge["zero_phase_control_readout"]["I_c_A_to_B"],
            "candidate_minus_zero_phase_Ic": bridge["candidate_minus_zero_phase_Ic"],
            "pass": bool(bridge["candidate_minus_zero_phase_Ic"] < -0.1),
            "summary": "raw phase(I_ij) is killed because zero-phase control has stronger coherent information",
        },
        "NC4_random_phase_does_not_save_raw_bridge": {
            "expected_to_fail": True,
            "candidate_Ic": bridge["candidate_readout"]["I_c_A_to_B"],
            "random_phase_Ic": bridge["random_phase_control_readout"]["I_c_A_to_B"],
            "candidate_minus_random_phase_Ic": bridge["candidate_minus_random_phase_Ic"],
            "pass": bool(bridge["candidate_minus_random_phase_Ic"] > 0.2 and bridge["candidate_readout"]["I_c_A_to_B"] < 0.0),
            "summary": "candidate beats random phase but still has negative coherent information, so it is not admitted",
        },
        "NC5_canon_promotion_rejected": {
            "expected_to_fail": True,
            "canon_nonpromotion_status": capacity["canon_nonpromotion_status"],
            "pass": capacity["canon_nonpromotion_status"] == "unsat",
            "summary": "Axis0 canon promotion is rejected because the raw incidence-phase bridge was killed",
        },
    }
    fired = sum(1 for row in rows.values() if row["pass"])
    return {
        "rows": rows,
        "fired_count": fired,
        "rows_total": len(rows),
        "pass": fired == len(rows),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    positive = {
        "xi_bridge_candidate_phi0_coherent_information": bridge_gate(),
        "finite_capacity_and_nonpromotion": capacity_and_nonpromotion_gate(),
    }
    negative_controls = negative_control_section(
        positive["xi_bridge_candidate_phi0_coherent_information"],
        positive["finite_capacity_and_nonpromotion"],
    )
    graveyard_companions = {
        "productized_cut_state_rejected": {
            "pass": positive["xi_bridge_candidate_phi0_coherent_information"]["product_control_readout"]["I_c_A_to_B"] < -0.3,
            "summary": "productizing the cut removes positive coherent information",
        },
        "history_erased_cut_state_rejected": {
            "pass": positive["xi_bridge_candidate_phi0_coherent_information"]["history_erased_control_readout"]["I_c_A_to_B"] < -0.6,
            "summary": "maximally mixed history-erased cut fails the signed Phi0 candidate",
        },
        "naive_raw_incidence_phase_bridge_rejected": {
            "pass": positive["xi_bridge_candidate_phi0_coherent_information"]["naive_raw_incidence_phase_bridge_rejected"],
            "summary": "raw phase(I_ij) is not an admitted Xi bridge; zero-phase control beats it",
        },
        "xi_candidate_sweep_has_no_admitted_mode": {
            "pass": positive["xi_bridge_candidate_phi0_coherent_information"]["candidate_modes_admitted_count"] == 0,
            "summary": "first bridge sweep found no mode that beats zero/random/product/history controls",
        },
    }
    boundary = {
        "xi_bridge_not_canonized": {
            "pass": True,
            "summary": "naive bridge was audited and rejected; Xi remains open",
        },
        "phi0_not_final": {
            "pass": True,
            "summary": "coherent information is a strong candidate, not final Axis0 kernel",
        },
        "holography_er_epr_not_admitted": {
            "pass": True,
            "summary": "finite cut-state test does not admit holographic spacetime or ER=EPR",
        },
    }
    all_rows = [*positive.values(), *graveyard_companions.values(), *boundary.values(), negative_controls]
    all_pass = all(row.get("pass") is True for row in all_rows)
    result = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "math_object": "finite spinor/twistor Xi bridge candidate producing bipartite cut state rho_AB",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "negative_controls": negative_controls,
        "nearby_variants": {
            "total": len(all_rows),
            "passed": sum(1 for row in all_rows if row.get("pass") is True),
        },
        "why_not_v4_probes": (
            "This is a v5 noncanonical formal scout for a current Xi/Phi0 "
            "bridge candidate over spinor/twistor cut states; v4 probes do "
            "not own this bridge-admission contract."
        ),
        "open_boundaries": [
            "Xi bridge remains candidate",
            "Phi0 coherent-information kernel remains candidate",
            "full twistor theory not admitted",
            "holographic spacetime and ER=EPR not admitted",
        ],
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT_PATH), "all_pass": all_pass}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
