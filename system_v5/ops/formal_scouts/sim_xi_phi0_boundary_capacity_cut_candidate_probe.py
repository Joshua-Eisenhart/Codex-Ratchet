#!/usr/bin/env python3
"""Xi/Phi0 boundary-capacity cut candidate scout.

Formal scout only. This tests a Bekenstein-style finite-boundary candidate for
Xi -> rho_AB: incidence geometry selects and weights a finite set of boundary
edges under an explicit capacity budget, then coherent information reads the
boundary/interior cut.

The candidate is allowed to fail. A clean failure narrows the Axis0/Xi/Phi0
space without promoting a fake finite-information bridge.
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
NAME = "xi_phi0_boundary_capacity_cut_candidate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "xi_phi0_boundary_capacity_cut_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite boundary-capacity Xi -> rho_AB cut "
    "candidate. It does not admit final Xi, final Phi0, final Axis0, "
    "holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite spinors, boundary-capacity edge selection, density matrices, entropy/cut readouts, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite-capacity and nonpromotion dependency fence",
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


def twistor_node(omega: torch.Tensor, pi: torch.Tensor) -> dict[str, torch.Tensor]:
    return {"omega": normalize(omega), "pi": normalize(pi)}


def incidence(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.vdot(a["pi"], b["omega"]) - torch.vdot(b["pi"], a["omega"])


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
    return {
        "spinors": spinors,
        "twistors": twistors,
        "edges": [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)],
        "boundary_cut": {"A": [0, 3], "B": [1, 2]},
    }


def two_qubit_gate(theta: float, phi: float) -> torch.Tensor:
    xx = torch.kron(X, X)
    yy = torch.kron(Y, Y)
    zz = torch.kron(Z, Z)
    generator = theta * (xx + yy) + phi * zz
    return torch.linalg.matrix_exp(-1.0j * generator)


def apply_two_qubit_gate(state: torch.Tensor, gate: torch.Tensor, qa: int, qb: int) -> torch.Tensor:
    state_4d = state.reshape(2, 2, 2, 2)
    gate_4d = gate.reshape(2, 2, 2, 2)
    other = [idx for idx in range(4) if idx not in (qa, qb)]
    perm = [qa, qb, *other]
    state_perm = state_4d.permute(*perm)
    new_perm = torch.einsum("abij,ijcd->abcd", gate_4d, state_perm)
    inv = [0] * 4
    for new_idx, old_idx in enumerate(perm):
        inv[old_idx] = new_idx
    return new_perm.permute(*inv).reshape(16)


def base_state(graph: dict[str, Any]) -> torch.Tensor:
    state = graph["spinors"][0]
    for spin in graph["spinors"][1:]:
        state = torch.kron(state, spin)
    return normalize(state)


def boundary_capacity_state(
    graph: dict[str, Any],
    mode: str,
    *,
    capacity: float,
    enforce_capacity: bool = True,
) -> dict[str, Any]:
    state = base_state(graph)
    incidences = [incidence(graph["twistors"][i], graph["twistors"][j]) for i, j in graph["edges"]]
    magnitudes = [float(torch.abs(row).item()) for row in incidences]
    max_mag = max(magnitudes) + EPS
    total_mag = sum(magnitudes) + EPS

    if mode == "incidence_capacity":
        edge_order = sorted(range(len(graph["edges"])), key=lambda idx: magnitudes[idx], reverse=True)
    elif mode == "uniform_capacity":
        edge_order = list(range(len(graph["edges"])))
    elif mode == "random_capacity":
        gen = torch.Generator()
        gen.manual_seed(20260523)
        edge_order = torch.randperm(len(graph["edges"]), generator=gen).tolist()
    elif mode == "zero_phase_capacity":
        edge_order = sorted(range(len(graph["edges"])), key=lambda idx: magnitudes[idx], reverse=True)
    else:
        raise ValueError(mode)

    used_capacity = 0.0
    selected = []
    for edge_idx in edge_order:
        i, j = graph["edges"][edge_idx]
        inc = incidences[edge_idx]
        mag = magnitudes[edge_idx]
        edge_cost = math.log(2.0) * (0.25 + mag / total_mag)
        if enforce_capacity and used_capacity + edge_cost > capacity:
            continue
        if mode == "uniform_capacity":
            theta = 0.18
            phi = 0.0
        elif mode == "random_capacity":
            theta = 0.08 + 0.30 * mag / max_mag
            gen = torch.Generator()
            gen.manual_seed(4040 + edge_idx)
            phi = float(((torch.rand((), generator=gen) - 0.5) * 2 * math.pi).item()) * 0.08
        elif mode == "zero_phase_capacity":
            theta = 0.08 + 0.30 * mag / max_mag
            phi = 0.0
        else:
            theta = 0.08 + 0.30 * mag / max_mag
            phi = float(torch.angle(inc).item()) * 0.08
        gate = two_qubit_gate(theta, phi)
        state = apply_two_qubit_gate(state, gate, i, j)
        used_capacity += edge_cost
        selected.append(
            {
                "edge": [i, j],
                "edge_cost": edge_cost,
                "magnitude": mag,
                "theta": theta,
                "phi": phi,
            }
        )
    rho = normalize_density(torch.outer(normalize(state), torch.conj(normalize(state))))
    return {
        "rho": rho,
        "capacity": capacity,
        "used_capacity": used_capacity,
        "capacity_slack": capacity - used_capacity,
        "selected_edges": selected,
        "selected_count": len(selected),
        "capacity_respected": used_capacity <= capacity + 1e-9,
    }


def partial_trace_qubits(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    dims = [2, 2, 2, 2]
    trace = [idx for idx in range(4) if idx not in keep]
    reshaped = rho.reshape(*dims, *dims)
    perm = keep + trace + [idx + 4 for idx in keep] + [idx + 4 for idx in trace]
    permuted = reshaped.permute(*perm).reshape(2 ** len(keep), 2 ** len(trace), 2 ** len(keep), 2 ** len(trace))
    return torch.einsum("abcb->ac", permuted)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def cut_readouts(rho: torch.Tensor) -> dict[str, float]:
    rho = normalize_density(rho)
    rho_a = partial_trace_qubits(rho, [0, 3])
    rho_b = partial_trace_qubits(rho, [1, 2])
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_c_A_to_B": s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_A_B": s_a + s_b - s_ab,
    }


def productize(rho: torch.Tensor) -> torch.Tensor:
    return normalize_density(torch.kron(partial_trace_qubits(rho, [0, 3]), partial_trace_qubits(rho, [1, 2])))


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


def candidate_gate() -> dict[str, Any]:
    graph = build_graph()
    capacity = math.log(4.0)
    modes = {
        "candidate": boundary_capacity_state(graph, "incidence_capacity", capacity=capacity),
        "zero_phase": boundary_capacity_state(graph, "zero_phase_capacity", capacity=capacity),
        "uniform": boundary_capacity_state(graph, "uniform_capacity", capacity=capacity),
        "random": boundary_capacity_state(graph, "random_capacity", capacity=capacity),
        "small_capacity": boundary_capacity_state(graph, "incidence_capacity", capacity=0.10),
        "over_capacity": boundary_capacity_state(graph, "incidence_capacity", capacity=capacity, enforce_capacity=False),
    }
    modes["productized"] = {"rho": productize(modes["candidate"]["rho"]), "capacity_respected": True}
    modes["history_erased"] = {"rho": torch.eye(16, dtype=CDTYPE) / 16.0, "capacity_respected": True}

    readouts = {name: cut_readouts(row["rho"]) for name, row in modes.items()}
    health = {name: matrix_health(row["rho"]) for name, row in modes.items()}
    candidate_ic = readouts["candidate"]["I_c_A_to_B"]
    admitted = bool(
        health["candidate"]["pass"]
        and modes["candidate"]["capacity_respected"]
        and candidate_ic > 0.0
        and candidate_ic - readouts["zero_phase"]["I_c_A_to_B"] > 0.02
        and candidate_ic - readouts["uniform"]["I_c_A_to_B"] > 0.02
        and candidate_ic - readouts["random"]["I_c_A_to_B"] > 0.02
        and candidate_ic - readouts["productized"]["I_c_A_to_B"] > 0.20
        and candidate_ic - readouts["history_erased"]["I_c_A_to_B"] > 0.20
    )
    return {
        "pass": True,
        "candidate_admitted": admitted,
        "readouts": readouts,
        "health": health,
        "capacity_rows": {
            name: {k: v for k, v in row.items() if k != "rho"}
            for name, row in modes.items()
            if name not in {"productized", "history_erased"}
        },
        "margins": {
            "candidate_minus_zero_Ic": candidate_ic - readouts["zero_phase"]["I_c_A_to_B"],
            "candidate_minus_uniform_Ic": candidate_ic - readouts["uniform"]["I_c_A_to_B"],
            "candidate_minus_random_Ic": candidate_ic - readouts["random"]["I_c_A_to_B"],
            "candidate_minus_product_Ic": candidate_ic - readouts["productized"]["I_c_A_to_B"],
            "candidate_minus_erased_Ic": candidate_ic - readouts["history_erased"]["I_c_A_to_B"],
            "candidate_minus_small_capacity_Ic": candidate_ic - readouts["small_capacity"]["I_c_A_to_B"],
        },
        "killed_reason": (
            "incidence capacity candidate is beaten by zero/uniform/random capacity controls"
            if not admitted
            else ""
        ),
    }


def dependency_fence(candidate_admitted: bool) -> dict[str, Any]:
    f01 = z3.Bool("f01")
    n01 = z3.Bool("n01")
    capacity = z3.Bool("finite_boundary_capacity")
    incidence = z3.Bool("incidence_noncommuting_geometry")
    candidate = z3.Bool("candidate_admitted")
    final_phi0 = z3.Bool("final_phi0")
    axioms = [
        z3.Implies(capacity, f01),
        z3.Implies(incidence, n01),
        z3.Implies(candidate, z3.And(capacity, incidence)),
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
        "capacity_requires_f01": str(status(capacity, z3.Not(f01))),
        "incidence_requires_n01": str(status(incidence, z3.Not(n01))),
        "roots_do_not_force_candidate": str(status(f01, n01, z3.Not(candidate))),
        "final_phi0_blocked_if_candidate_killed": str(status(final_phi0)),
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    candidate = candidate_gate()
    fence = dependency_fence(candidate["candidate_admitted"])
    positive = {
        "boundary_capacity_candidate_audited": {
            "pass": candidate["pass"] and all(row["pass"] for row in candidate["health"].values()),
            "candidate_admitted": candidate["candidate_admitted"],
            "readouts": candidate["readouts"],
            "margins": candidate["margins"],
        },
        "finite_capacity_budget_is_active": {
            "pass": candidate["capacity_rows"]["candidate"]["capacity_respected"]
            and candidate["capacity_rows"]["small_capacity"]["selected_count"] == 0
            and not candidate["capacity_rows"]["over_capacity"]["capacity_respected"],
            "capacity_rows": candidate["capacity_rows"],
        },
        "matrix_health_all_modes": {
            "pass": all(row["pass"] for row in candidate["health"].values()),
            "health": candidate["health"],
        },
        "dependency_fence": fence,
    }
    graveyard_companions = {
        "boundary_capacity_candidate_not_admitted": {
            "pass": not candidate["candidate_admitted"],
            "summary": candidate["killed_reason"],
        },
        "zero_uniform_random_controls_beat_candidate": {
            "pass": candidate["margins"]["candidate_minus_zero_Ic"] < 0.0
            and candidate["margins"]["candidate_minus_uniform_Ic"] < 0.0
            and candidate["margins"]["candidate_minus_random_Ic"] < 0.0,
            "margins": candidate["margins"],
        },
        "product_and_history_erased_controls_remain_negative": {
            "pass": candidate["readouts"]["productized"]["I_c_A_to_B"] < 0.0
            and candidate["readouts"]["history_erased"]["I_c_A_to_B"] < -1.0,
            "product_Ic": candidate["readouts"]["productized"]["I_c_A_to_B"],
            "history_erased_Ic": candidate["readouts"]["history_erased"]["I_c_A_to_B"],
        },
        "over_capacity_control_rejected": {
            "pass": not candidate["capacity_rows"]["over_capacity"]["capacity_respected"],
            "used_capacity": candidate["capacity_rows"]["over_capacity"]["used_capacity"],
            "capacity": candidate["capacity_rows"]["over_capacity"]["capacity"],
        },
    }
    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": fence["final_phi0_blocked_if_candidate_killed"] == "unsat",
            "summary": "boundary-capacity candidate killed, so final Phi0 remains blocked",
        },
        "formal_scout_only": {
            "pass": classification == "formal_scout" and not PROMOTION_ALLOWED,
            "summary": "negative finite-boundary candidate scout only",
        },
        "holography_and_physics_not_admitted": {
            "pass": True,
            "summary": "finite boundary-capacity cut does not admit holography, ER=EPR, or physics",
        },
    }
    nearby_variants = {
        "total": 4,
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions.keys()),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is an unpromoted v5 formal scout over a finite boundary-capacity bridge candidate, not a canonical v4 probe.",
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
            "killed_reason": candidate["killed_reason"],
            "capacity_rows": candidate["capacity_rows"],
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
