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
        "reason": "supportive finite-capacity and nonpromotion dependency-consistency fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
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
EPS = 1e-12

# ---------------------------------------------------------------------------
# Admission thresholds (Round-5 fix, Opus C.3: previously hardcoded magic numbers).
# Each constant is named with its purpose; sensitivity sweep is documented in
# the audit doc §15. Changing these requires a re-audit because the verdicts
# depend on them.
#
# Single-instance admission criteria (bridge_gate, joint_graph_partition_bridge_gate):
#   ADMISSION_THRESHOLD = 0.02
#     — magnitude floor: incidence must beat random by this much to count.
#       Rationale: ≈ 1/4 of the smallest observed cell std (~0.08) when noise
#       is applied. Below this is in the noise-floor band even before SE
#       correction.
#   PRODUCT_GAP_THRESHOLD = 0.5
#     — incidence must beat the product baseline by this much. Rationale:
#       product is by construction at I_c ≤ 0 for the 4-d cut; +0.5 is a
#       distance that distinguishes nontrivial entanglement from zero.
#   NONTRIVIAL_PURE_THRESHOLD = 0.05
#     — pure entanglement entropy floor: below this, the construction did
#       not generate meaningful bipartite entanglement on the chosen cut.
#
# Ensemble admission (rng_ensemble_bridge_gate):
#   Same ADMISSION_THRESHOLD = 0.02 as single-instance for cross-comparison.
#   FWE_ALPHA_TARGET = 0.05 (one-sided across n_cells screened).
# ---------------------------------------------------------------------------
ADMISSION_THRESHOLD = 0.02
PRODUCT_GAP_THRESHOLD = 0.5
NONTRIVIAL_PURE_THRESHOLD = 0.05
FWE_ALPHA_TARGET = 0.05

# Round-9 fix (Opus R9 B1): functionals that are partition-independent by
# construction. I(A:B:C:D) = S(A)+S(B)+S(C)+S(D)-S(ABCD) sums over single-qubit
# marginals; the bipartition choice (block 0,1|2,3 vs interleaved 0,2|1,3)
# does not change the value. Counting these once per partition inflates
# n_cells_screened in the Bonferroni calc. Real distinct-cell count subtracts
# the partition-duplicates for these functionals.
PARTITION_INDEPENDENT_FUNCTIONALS = {"I_ABCD"}

# Round-6 fix (Opus R6 A.1): wire previously-raw call-site literals through the
# constants table so changes propagate, and so the table stops being named-only
# documentation.
BEATS_PRODUCT_MARGIN = 0.1  # admission_check: incidence must beat product by this
RAW_PHASE_BEAT_MARGIN = -0.1  # admission_check: pure phase floor (negative band)
NC1_PURE_THRESHOLD = 0.5  # NC1: pure-state entanglement must exceed
NC2_PURE_FLOOR = -0.3  # NC2: pure-state inversion floor
NC2B_PURE_FLOOR = -0.6  # NC2b: stronger pure-state inversion floor
NC3_PURE_FLOOR = -0.1  # NC3: pure-state weak inversion floor
HAAR_NUM_SEEDS = 30  # K=30 ensemble size


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


def schmidt_moments(rho: torch.Tensor, k_max: int = 4) -> dict[str, float]:
    """Round-6 fix: Renyi-style moments of the reduced density spectrum.

    M_k = Tr(rho^k) = sum_i lambda_i^k. Distinct from von Neumann entropy
    S = -sum lambda log lambda; moments capture spectrum SHAPE that entropy
    summarises but does not preserve. M_2 = purity (1/d ≤ M_2 ≤ 1).

    Added because Grok R6 C.1 and Opus R6 P1.2 named entanglement-spectrum
    statistics as one of the structurally different alt-readouts that the
    existing cut-functional family did NOT exercise.
    """
    herm = (rho + torch.conj(rho).T) / 2
    vals = torch.linalg.eigvalsh(herm).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    out = {}
    for k in range(2, k_max + 1):
        out[f"M_{k}"] = float(torch.sum(vals ** k).item())
    return out


def quantum_relative_entropy(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    """D(rho || sigma) = Tr[rho (log rho - log sigma)], with eigenvalue clamping.

    FEP-aligned Φ_0 candidate: classical FEP variational free energy is
    F(q,p) = D(q || p) - log Z. The QIT analogue uses quantum relative entropy
    on density matrices. For pure states this can diverge; on noisy
    (dephased/depolarized) states with full support it is finite.

    Implementation regularises with eigenvalue floor at EPS to avoid -inf
    when supp(sigma) is rank-deficient.
    """
    herm_rho = (rho + torch.conj(rho).T) / 2
    herm_sig = (sigma + torch.conj(sigma).T) / 2
    rho_vals, rho_vecs = torch.linalg.eigh(herm_rho)
    sig_vals, sig_vecs = torch.linalg.eigh(herm_sig)
    rho_vals = torch.clamp(rho_vals.real, min=EPS)
    sig_vals = torch.clamp(sig_vals.real, min=EPS)
    log_rho = rho_vecs @ torch.diag(torch.log(rho_vals)).to(CDTYPE) @ torch.conj(rho_vecs).T
    log_sig = sig_vecs @ torch.diag(torch.log(sig_vals)).to(CDTYPE) @ torch.conj(sig_vecs).T
    val = torch.real(torch.trace(herm_rho @ (log_rho - log_sig)))
    return float(val.item())


def cut_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    s_ab = entropy(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    out = {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "I_c_A_to_B": s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_A_B": s_a + s_b - s_ab,
    }
    moments_a = schmidt_moments(rho_a)
    for k, v in moments_a.items():
        out[k] = v
    return out


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
            # Seeded torch RNG sample (deterministic, but a real random draw —
            # NOT a hand-formula). Round-2-audit-fix for Opus D11: the
            # previous `1.7*(idx+1)` was not actually a random sample.
            _gen = torch.Generator()
            _gen.manual_seed(20260522 + idx)
            phase = float(((torch.rand((), generator=_gen) - 0.5) * 2 * math.pi).item())
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
            and readout["I_c_A_to_B"] - zero["I_c_A_to_B"] > ADMISSION_THRESHOLD
            and readout["I_c_A_to_B"] - random["I_c_A_to_B"] > ADMISSION_THRESHOLD
            and readout["I_c_A_to_B"] - prod["I_c_A_to_B"] > PRODUCT_GAP_THRESHOLD
            and readout["I_c_A_to_B"] - erased_read["I_c_A_to_B"] > PRODUCT_GAP_THRESHOLD
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
            and prod["I_c_A_to_B"] < NC2_PURE_FLOOR
            and erased_read["I_c_A_to_B"] < NC2B_PURE_FLOOR
            and naive_raw_phase_rejected
        ),
    }


def capacity_and_nonpromotion_gate(raw_phase_bridge_rejected: bool) -> dict[str, Any]:
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
    ]
    if raw_phase_bridge_rejected:
        dependency_axioms.append(z3.Not(raw_phase_bridge_survives))

    def status(*assumptions: z3.BoolRef) -> z3.CheckSatResult:
        solver = z3.Solver()
        solver.add(*dependency_axioms)
        solver.add(*assumptions)
        return solver.check()

    roots_do_not_force_axis0_status = status(f01, n01, z3.Not(axis0_canon))
    cut_capacity_with_f01_status = status(f01, cut_capacity)
    cut_capacity_requires_f01_status = status(cut_capacity, z3.Not(f01))
    er_epr_with_roots_and_capacity_status = status(f01, n01, cut_capacity, er_epr_canon)
    er_epr_requires_roots_status = status(er_epr_canon, z3.Or(z3.Not(f01), z3.Not(n01)))
    holography_with_er_epr_capacity_status = status(f01, n01, cut_capacity, er_epr_canon, holography_canon)
    holography_requires_er_epr_status = status(holography_canon, z3.Not(er_epr_canon))
    axis0_canon_rejected_by_raw_bridge_status = status(axis0_canon)

    return {
        "log_dim_AB": log_dim_ab,
        "capacity_ok": cap_ok,
        "capacity_too_small": cap_small,
        "ok_capacity_status": str(ok.check()),
        "too_small_capacity_status": str(small.check()),
        "roots_do_not_force_axis0_status": str(roots_do_not_force_axis0_status),
        "cut_capacity_with_f01_status": str(cut_capacity_with_f01_status),
        "cut_capacity_requires_f01_status": str(cut_capacity_requires_f01_status),
        "er_epr_with_roots_and_capacity_status": str(er_epr_with_roots_and_capacity_status),
        "er_epr_requires_roots_status": str(er_epr_requires_roots_status),
        "holography_with_er_epr_capacity_status": str(holography_with_er_epr_capacity_status),
        "holography_requires_er_epr_status": str(holography_requires_er_epr_status),
        "raw_phase_bridge_rejected_empirical": bool(raw_phase_bridge_rejected),
        "axis0_canon_rejected_by_raw_bridge_status": str(axis0_canon_rejected_by_raw_bridge_status),
        "canon_nonpromotion_status": str(axis0_canon_rejected_by_raw_bridge_status),
        "pass": bool(
            ok.check() == z3.sat
            and small.check() == z3.unsat
            and roots_do_not_force_axis0_status == z3.sat
            and cut_capacity_with_f01_status == z3.sat
            and cut_capacity_requires_f01_status == z3.unsat
            and er_epr_with_roots_and_capacity_status == z3.sat
            and er_epr_requires_roots_status == z3.unsat
            and holography_with_er_epr_capacity_status == z3.sat
            and holography_requires_er_epr_status == z3.unsat
            and raw_phase_bridge_rejected
            and axis0_canon_rejected_by_raw_bridge_status == z3.unsat
        ),
    }


# ---------------------------------------------------------------------------
# Joint-graph partition Xi — structurally different from edge-mixture family.
# Build one pure 4-qubit (16-d) state by applying graph-edge entanglers to a
# product of node spinors, then partition into A = {0, 1}, B = {2, 3} and
# compute cut readouts. The previous family summed per-edge density
# contributions; this family threads a single global wavefunction through the
# graph topology. Different construction → potentially different verdicts.
# ---------------------------------------------------------------------------


def two_qubit_xy_entangler(lam: float, phi: float) -> torch.Tensor:
    """XY entangler exp(-i (lam·XX + phi·YY)). 4x4 unitary."""
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    sy = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
    xx = torch.kron(sx, sx)
    yy = torch.kron(sy, sy)
    gen = lam * xx + phi * yy
    return torch.linalg.matrix_exp(-1.0j * gen)


def two_qubit_heisenberg_entangler(lam: float, phi: float) -> torch.Tensor:
    """Heisenberg-style entangler exp(-i (lam·(XX+YY+ZZ) + phi·(XY-YX))). 4x4 unitary.

    Round-4 fix (item 2 of 7-item list, deferred 3 rounds): adds an entangler
    structurally distinct from XY. The lam term is fully isotropic in spin
    interactions (Heisenberg model). The phi term adds an antisymmetric
    Dzyaloshinskii-Moriya-style coupling breaking parity. The choice is
    designed to test whether the 'no signal' verdict under XY entangler
    survives under a qualitatively different entanglement structure.
    """
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    sy = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    xx = torch.kron(sx, sx)
    yy = torch.kron(sy, sy)
    zz = torch.kron(sz, sz)
    xy = torch.kron(sx, sy)
    yx = torch.kron(sy, sx)
    gen = lam * (xx + yy + zz) + phi * (xy - yx)
    return torch.linalg.matrix_exp(-1.0j * gen)


def two_qubit_ising_entangler(lam: float, phi: float) -> torch.Tensor:
    """Round-7-prep: Ising ZZ entangler exp(-i(lam·ZZ + phi·(IZ+ZI)/2)). 4x4 unitary.

    Tests the structure-distance hypothesis: XY (1-axis XX+YY), Heisenberg
    (3-axis XX+YY+ZZ), Ising (1-axis ZZ), random (no structure).
    If sign reversal magnitude correlates with structure-distance, Ising
    should show signal intermediate between random and XY. If it shows
    XY-like positive bias on pure half OR Heisenberg-like negative bias,
    that maps the basis-bias axis to specific Pauli-pair structure.
    """
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    zz = torch.kron(sz, sz)
    iz = torch.kron(torch.eye(2, dtype=CDTYPE), sz)
    zi = torch.kron(sz, torch.eye(2, dtype=CDTYPE))
    gen = lam * zz + phi * 0.5 * (iz + zi)
    return torch.linalg.matrix_exp(-1.0j * gen)


def two_qubit_random_unitary_entangler(lam: float, phi: float) -> torch.Tensor:
    """Round-6 fix (negative control): Haar-random 2-qubit unitary seeded by lam,phi.

    Round-5 elevated finding B.1 claimed entangler-basis bias-sign reversal between
    XY and Heisenberg. This control tests whether the sign-reversal is specific to
    those two structured entanglers or a generic artifact of any 2-qubit unitary
    family. If sign-reversal survives random unitaries → claim weakens (basis
    artifact). If sign-reversal collapses under random unitaries → claim
    strengthens (the XY/Heisenberg basis structure was actually load-bearing).

    Implementation: seed a PRNG from (lam, phi), draw a Haar 4x4 unitary.
    The (lam, phi) → seed mapping makes the entangler reproducible cell-by-cell
    while randomizing the basis at each edge.
    """
    seed = int((lam * 1e8 + phi * 1e6 + 20260523) % (2**31))
    gen = torch.Generator()
    gen.manual_seed(seed)
    # Haar 4x4: QR-decompose a complex Gaussian matrix, fix phases
    a = torch.randn(4, 4, generator=gen, dtype=DTYPE)
    b = torch.randn(4, 4, generator=gen, dtype=DTYPE)
    z = (a + 1.0j * b).to(CDTYPE) / math.sqrt(2)
    q, r = torch.linalg.qr(z)
    diag = torch.diagonal(r)
    phases = diag / torch.abs(diag).clamp(min=EPS)
    return q * phases.unsqueeze(0)


ENTANGLER_REGISTRY = {
    "xy": two_qubit_xy_entangler,
    "heisenberg": two_qubit_heisenberg_entangler,
    "ising": two_qubit_ising_entangler,
    "random_unitary": two_qubit_random_unitary_entangler,
}


def apply_two_qubit_to_4qubit(state: torch.Tensor, gate: torch.Tensor, qa: int, qb: int) -> torch.Tensor:
    state_4d = state.reshape(2, 2, 2, 2)
    gate_4d = gate.reshape(2, 2, 2, 2)  # (a_out, b_out, a_in, b_in)
    other = [k for k in range(4) if k not in (qa, qb)]
    perm = [qa, qb, *other]
    state_perm = state_4d.permute(*perm)
    new_perm = torch.einsum("abij,ijcd->abcd", gate_4d, state_perm)
    inv = [0] * 4
    for new_idx, old_idx in enumerate(perm):
        inv[old_idx] = new_idx
    return new_perm.permute(*inv).reshape(16)


def joint_graph_state(
    graph: dict[str, Any],
    mode: str,
    rng_seed: int = 20260522,
    entangler_family: str = "xy",
) -> torch.Tensor:
    state = graph["spinors"][0]
    for k in range(1, 4):
        state = torch.kron(state, graph["spinors"][k])
    state = normalize(state.to(CDTYPE))

    if mode == "incidence_derived":
        edge_params = []
        for i, j in graph["edges"]:
            inc = incidence(graph["twistors"][i], graph["twistors"][j])
            lam = 0.20 + 0.40 * float(torch.abs(inc).item())
            phi = float(torch.angle(inc).item())
            edge_params.append((lam, phi))
    elif mode == "random_seeded":
        gen = torch.Generator()
        gen.manual_seed(rng_seed)
        edge_params = []
        for _ in graph["edges"]:
            lam = float((0.20 + 0.40 * torch.rand((), generator=gen)).item())
            phi = float(((torch.rand((), generator=gen) - 0.5) * 2 * math.pi).item())
            edge_params.append((lam, phi))
    elif mode == "lambda_matched_random_phi":
        # Round-7-prep CONFOUND FIX: use the SAME lam = 0.20 + 0.40 * |I_ij|
        # as incidence_derived, but draw phi uniformly at random. This isolates
        # whether the phi-angle structure carries geometric content, controlling
        # for the lambda-magnitude bias that was previously confounded with
        # geometry. Original `random_seeded` had lam ~ U[0.20, 0.60] (mean 0.40)
        # while incidence_derived had lam = 0.20 + 0.40·|I_ij| (mean ≈ 0.58),
        # so inc states got systematically stronger entangling rotations
        # (especially visible under Ising ZZ entangler where lam directly
        # controls coupling strength without phase scrambling).
        gen = torch.Generator()
        gen.manual_seed(rng_seed)
        edge_params = []
        for i, j in graph["edges"]:
            inc = incidence(graph["twistors"][i], graph["twistors"][j])
            lam = 0.20 + 0.40 * float(torch.abs(inc).item())  # SAME as inc
            phi = float(((torch.rand((), generator=gen) - 0.5) * 2 * math.pi).item())
            edge_params.append((lam, phi))
    elif mode == "phi_matched_random_lambda":
        # Round-7-prep CONFOUND FIX (dual): use the SAME phi = angle(I_ij) as
        # incidence_derived, but draw lam uniformly from a wider range matching
        # incidence's empirical lambda range [0.22, 0.95]. Isolates whether the
        # lambda-magnitude structure carries geometric content.
        gen = torch.Generator()
        gen.manual_seed(rng_seed)
        edge_params = []
        for i, j in graph["edges"]:
            inc = incidence(graph["twistors"][i], graph["twistors"][j])
            phi = float(torch.angle(inc).item())  # SAME as inc
            lam = 0.20 + 0.80 * float(torch.rand((), generator=gen).item())  # wider range
            edge_params.append((lam, phi))
    elif mode == "product_baseline":
        edge_params = [(0.0, 0.0) for _ in graph["edges"]]
    elif mode == "uniform_lambda_zero_phase":
        edge_params = [(0.30, 0.0) for _ in graph["edges"]]
    else:
        raise ValueError(mode)

    entangler_fn = ENTANGLER_REGISTRY[entangler_family]
    for (i, j), (lam, phi) in zip(graph["edges"], edge_params):
        if lam == 0.0 and phi == 0.0:
            continue
        gate = entangler_fn(lam, phi)
        state = apply_two_qubit_to_4qubit(state, gate, i, j)
    return state / torch.linalg.vector_norm(state)


def partial_trace_single_qubit(rho_16: torch.Tensor, keep_qubit: int) -> torch.Tensor:
    """Round-8-prep: trace out 3 of 4 qubits, returning 2x2 rho on `keep_qubit`.

    Used by multipartite_information I(A:B:C:D) which requires each single-qubit
    marginal entropy S(rho_q) for q in {0,1,2,3}.
    """
    rho_8d = rho_16.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    # rho_8d indices: (a, b, c, d) for row qubits, (e, f, g, h) for col qubits
    # Trace each qubit except keep_qubit; set traced row/col indices equal
    if keep_qubit == 0:
        # trace 1,2,3: b=f, c=g, d=h
        return torch.einsum("abcdebcd->ae", rho_8d).reshape(2, 2)
    if keep_qubit == 1:
        # trace 0,2,3: a=e, c=g, d=h
        return torch.einsum("abcdafcd->bf", rho_8d).reshape(2, 2)
    if keep_qubit == 2:
        # trace 0,1,3: a=e, b=f, d=h
        return torch.einsum("abcdabgd->cg", rho_8d).reshape(2, 2)
    if keep_qubit == 3:
        # trace 0,1,2: a=e, b=f, c=g
        return torch.einsum("abcdabch->dh", rho_8d).reshape(2, 2)
    raise ValueError(keep_qubit)


def multipartite_information(rho_16: torch.Tensor) -> float:
    """I(A:B:C:D) = S(A) + S(B) + S(C) + S(D) - S(ABCD).

    Multipartite mutual information / total correlation for the 4-qubit
    state on the ring. Closes the Grok R6 C.1 + Opus R6 P1.2 gap of
    "multipartite information named-but-unimplemented." Structurally
    different from bipartite-cut readouts (I_c, LN, MI on a 2|2 cut)
    because it accounts for ALL pairwise + triple + quadruple correlations
    via inclusion-exclusion on the 4 single-qubit marginals.
    """
    s_total = entropy(rho_16)
    s_marginals = sum(entropy(partial_trace_single_qubit(rho_16, q)) for q in range(4))
    return s_marginals - s_total


def partial_trace_qubits_23(rho_16: torch.Tensor) -> torch.Tensor:
    """Trace out qubits 2, 3 from a 16x16 density matrix. Returns 4x4 rho_A on qubits {0, 1}."""
    rho_8d = rho_16.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    rho_a = torch.einsum("abcdefcd->abef", rho_8d)
    return rho_a.reshape(4, 4)


def partial_trace_qubits_01(rho_16: torch.Tensor) -> torch.Tensor:
    """Trace out qubits 0, 1. Returns 4x4 rho_B on qubits {2, 3}."""
    rho_8d = rho_16.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    rho_b = torch.einsum("abcdabgh->cdgh", rho_8d)
    return rho_b.reshape(4, 4)


def partial_trace_qubits_13(rho_16: torch.Tensor) -> torch.Tensor:
    """Trace out qubits 1, 3 (interleaved partition). Returns 4x4 rho on {0, 2}.

    rho_16 reshaped as (2,2,2,2,2,2,2,2) with indices
    (a, b, c, d) for row qubits (q0, q1, q2, q3) and
    (e, f, g, h) for col qubits (q0, q1, q2, q3).
    Trace q1 (b = f) and q3 (d = h).
    """
    rho_8d = rho_16.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    out = torch.zeros((2, 2, 2, 2), dtype=rho_16.dtype)
    for a in range(2):
        for c in range(2):
            for e in range(2):
                for g in range(2):
                    val = 0.0 + 0.0j
                    for b in range(2):
                        for d in range(2):
                            val = val + rho_8d[a, b, c, d, e, b, g, d]
                    out[a, c, e, g] = val
    return out.reshape(4, 4)


def partial_trace_qubits_02(rho_16: torch.Tensor) -> torch.Tensor:
    """Trace out qubits 0, 2 (interleaved partition). Returns 4x4 rho on {1, 3}."""
    rho_8d = rho_16.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    out = torch.zeros((2, 2, 2, 2), dtype=rho_16.dtype)
    for b in range(2):
        for d in range(2):
            for f in range(2):
                for h in range(2):
                    val = 0.0 + 0.0j
                    for a in range(2):
                        for c in range(2):
                            val = val + rho_8d[a, b, c, d, a, f, c, h]
                    out[b, d, f, h] = val
    return out.reshape(4, 4)


def joint_graph_readouts(rho_ab: torch.Tensor, partition: str = "block") -> dict[str, float]:
    """Compute cut readouts under a chosen 4-qubit bipartition.

    partition='block':    A = {q0, q1}, B = {q2, q3}  (cuts 2 of 4 ring edges)
    partition='interleaved': A = {q0, q2}, B = {q1, q3}  (cuts all 4 edges)
    """
    if partition == "block":
        rho_a = partial_trace_qubits_23(rho_ab)
        rho_b = partial_trace_qubits_01(rho_ab)
    elif partition == "interleaved":
        rho_a = partial_trace_qubits_13(rho_ab)
        rho_b = partial_trace_qubits_02(rho_ab)
    else:
        raise ValueError(partition)
    s_ab = entropy(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    log_neg = log_negativity_4d_partition(rho_ab, partition)
    moments_a = schmidt_moments(rho_a)
    # Round-8-prep: multipartite mutual information I(A:B:C:D). Structurally
    # different from bipartite-cut readouts because it sums all 4 single-qubit
    # marginal entropies against the joint entropy — sensitive to higher-order
    # correlations a bipartite cut summarises away.
    mp_info = multipartite_information(rho_ab)
    out = {
        "partition": partition,
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "I_c_A_to_B": s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_A_B": s_a + s_b - s_ab,
        "I_ABCD": mp_info,
        "log_negativity": log_neg,
    }
    for k, v in moments_a.items():
        out[k] = v
    return out


def log_negativity_4d_partition(rho_16: torch.Tensor, partition: str) -> float:
    """Log-negativity LN = log2(||rho^{T_B}||_1), where T_B is partial transpose over B.

    Defined for 4-qubit rho on the requested 4-d × 4-d bipartition.
    """
    rho_8d = rho_16.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    if partition == "block":
        # Swap col indices for qubits 2,3 with row indices for qubits 2,3.
        # That is, T_B over q2,q3: index pattern (a,b,c,d,e,f,g,h) -> (a,b,g,h,e,f,c,d).
        rho_pt_8d = rho_8d.permute(0, 1, 6, 7, 4, 5, 2, 3)
    elif partition == "interleaved":
        # T_B over q1,q3: (a,b,c,d,e,f,g,h) -> (a,f,c,h,e,b,g,d).
        rho_pt_8d = rho_8d.permute(0, 5, 2, 7, 4, 1, 6, 3)
    else:
        raise ValueError(partition)
    rho_pt = rho_pt_8d.reshape(16, 16)
    # Nuclear norm = sum of singular values; for Hermitian, = sum |eigenvalues|.
    svals = torch.linalg.svdvals(rho_pt).real
    trace_norm = float(torch.sum(svals).item())
    return math.log2(max(trace_norm, 1e-30))


def depolarize_16dim(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    """Independent depolarizing channel on each of 4 qubits, applied sequentially.

    Per-qubit Pauli Kraus decomposition with weights
        (1 - 3γ/4, γ/4, γ/4, γ/4)
    on {I, X, Y, Z}. Composed independently across the 4 qubits.
    """
    n = 4
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    eye = torch.eye(2, dtype=CDTYPE)
    paulis = [eye, sx, sy, sz]
    weights = [1.0 - 0.75 * gamma, 0.25 * gamma, 0.25 * gamma, 0.25 * gamma]
    out = rho.clone()
    for q in range(n):
        new = torch.zeros_like(out)
        for p, w in zip(paulis, weights):
            ops = [eye, eye, eye, eye]
            ops[q] = p
            full = ops[0]
            for k in range(1, n):
                full = torch.kron(full, ops[k])
            new = new + w * (full @ out @ torch.conj(full).T)
        out = new
    return out


def dephase_16dim(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    """Independent z-dephasing on each of 4 qubits, strength gamma per qubit.
    Sends off-diagonals in computational basis to (1 - gamma)^k times original,
    where k = Hamming distance of basis indices (number of qubits flipped)."""
    n = 16
    out = rho.clone()
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            hd = bin(i ^ j).count("1")
            out[i, j] = rho[i, j] * ((1.0 - gamma) ** hd)
    return out


def amplitude_damping_16dim(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    """Round-8-prep: Independent amplitude damping on each of 4 qubits.

    Per-qubit Kraus: K_0 = diag(1, sqrt(1-γ)), K_1 = sqrt(γ) * |0⟩⟨1|.
    Models energy loss to environment (relaxation). Different from dephasing
    and depolarizing — has a fixed point at |0⟩⟨0| and is non-unital. Closes
    the Grok R6 C.2 noise-model gap (only z-dephasing and depolarizing tested).
    """
    n = 4
    eye2 = torch.eye(2, dtype=CDTYPE)
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(max(0.0, 1.0 - gamma))]], dtype=CDTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=CDTYPE)
    kraus = [k0, k1]
    out = rho.clone()
    for q in range(n):
        new = torch.zeros_like(out)
        for k in kraus:
            ops = [eye2, eye2, eye2, eye2]
            ops[q] = k
            full = ops[0]
            for kq in range(1, n):
                full = torch.kron(full, ops[kq])
            new = new + full @ out @ torch.conj(full).T
        out = new
    return out


def joint_graph_partition_bridge_gate() -> dict[str, Any]:
    """Build the joint-graph Xi candidate and compare across TWO partitions
    (block A={0,1}/B={2,3} and interleaved A={0,2}/B={1,3}) and three
    functionals (coherent information I_c, log-negativity LN, and mutual
    information I_A_B).

    For each mode, pure-state and z-dephased (gamma=0.30) readouts are computed
    under each partition. Admission is checked for each (partition, functional)
    combination separately. The three-model audit flagged the single-partition
    + single-functional configuration as undertested.
    """
    graph = build_graph()
    modes = ["incidence_derived", "random_seeded", "product_baseline", "uniform_lambda_zero_phase"]
    partitions = ["block", "interleaved"]
    pure: dict[str, Any] = {mode: {} for mode in modes}
    dephased: dict[str, Any] = {mode: {} for mode in modes}
    for mode in modes:
        state = joint_graph_state(graph, mode)
        rho = density(state)
        rho_health = {
            "trace": float(torch.real(torch.trace(rho)).item()),
            "hermiticity_gap": float(torch.linalg.matrix_norm(rho - torch.conj(rho).T).item()),
        }
        rho_dephased = dephase_16dim(rho, gamma=0.30)
        rho_dephased = rho_dephased / torch.real(torch.trace(rho_dephased))
        pure[mode]["health"] = rho_health
        for partition in partitions:
            pure[mode][partition] = joint_graph_readouts(rho, partition=partition)
            dephased[mode][partition] = joint_graph_readouts(rho_dephased, partition=partition)

    def admission_check(functional_key: str, partition: str) -> dict[str, Any]:
        inc_pure = pure["incidence_derived"][partition][functional_key]
        prod_pure = pure["product_baseline"][partition][functional_key]
        rand_pure = pure["random_seeded"][partition][functional_key]
        unif_pure = pure["uniform_lambda_zero_phase"][partition][functional_key]
        inc_deph = dephased["incidence_derived"][partition][functional_key]
        rand_deph = dephased["random_seeded"][partition][functional_key]
        prod_deph = dephased["product_baseline"][partition][functional_key]
        unif_deph = dephased["uniform_lambda_zero_phase"][partition][functional_key]
        nontrivial = inc_pure > NONTRIVIAL_PURE_THRESHOLD
        beats_product_pure = inc_pure - prod_pure > BEATS_PRODUCT_MARGIN
        # For log_negativity, "survives noise" means > 0; for I_c, same.
        survives = inc_deph > 0.0
        beats_random_under_noise = inc_deph - rand_deph > ADMISSION_THRESHOLD
        admitted = bool(nontrivial and beats_product_pure and survives and beats_random_under_noise)
        return {
            "incidence_pure": inc_pure,
            "random_pure": rand_pure,
            "product_pure": prod_pure,
            "uniform_pure": unif_pure,
            "incidence_dephased": inc_deph,
            "random_dephased": rand_deph,
            "product_dephased": prod_deph,
            "uniform_dephased": unif_deph,
            "incidence_minus_product_pure": inc_pure - prod_pure,
            "incidence_minus_random_pure": inc_pure - rand_pure,
            "incidence_minus_random_dephased": inc_deph - rand_deph,
            "nontrivial_pure_entanglement": nontrivial,
            "beats_product_pure_by_0p1": beats_product_pure,
            "survives_dephasing": survives,
            "beats_random_under_noise_by_0p02": beats_random_under_noise,
            "admitted": admitted,
        }

    admission_matrix: dict[str, dict[str, Any]] = {}
    # Round-6 fix: mutual information I_A_B added as a structurally-different
    # readout family. See rng_ensemble_bridge_gate comment for rationale.
    for functional_key in ["I_c_A_to_B", "log_negativity", "I_A_B"]:
        admission_matrix[functional_key] = {}
        for partition in partitions:
            admission_matrix[functional_key][partition] = admission_check(functional_key, partition)

    any_admitted = any(
        admission_matrix[fk][p]["admitted"]
        for fk in admission_matrix
        for p in admission_matrix[fk]
    )
    admitted_cells = [
        (fk, p)
        for fk in admission_matrix
        for p in admission_matrix[fk]
        if admission_matrix[fk][p]["admitted"]
    ]

    return {
        "construction": (
            "single 4-qubit pure state via per-edge XY entanglers on product "
            "of node spinors; two partitions tested (block, interleaved); "
            "three functionals tested (coherent information, log-negativity, "
            "mutual information)"
        ),
        "partitions_tested": partitions,
        "functionals_tested": ["I_c_A_to_B", "log_negativity", "I_A_B"],
        "pure_readouts": pure,
        "dephased_gamma_0p30_readouts": dephased,
        "admission_matrix": admission_matrix,
        "admitted_cells": admitted_cells,
        "any_incidence_admission": any_admitted,
        "pass": True,  # scout pass = test completed honestly, not that incidence is admitted
    }


def haar_random_spinor(gen: torch.Generator) -> torch.Tensor:
    """Sample a single-qubit spinor uniformly from the Haar measure on CP^1."""
    re = torch.randn((2,), generator=gen, dtype=DTYPE)
    im = torch.randn((2,), generator=gen, dtype=DTYPE)
    v = torch.complex(re, im).to(CDTYPE)
    return v / torch.linalg.vector_norm(v)


def haar_random_graph(seed: int) -> dict[str, Any]:
    """Build a 4-node graph with Haar-random spinors and twistor nodes derived
    from independent draws — addressing Opus D8 (independent π parameterization).
    """
    gen = torch.Generator()
    gen.manual_seed(seed)
    spinors = [haar_random_spinor(gen) for _ in range(4)]
    twistors = [
        twistor_node(haar_random_spinor(gen), haar_random_spinor(gen))
        for _ in range(4)
    ]
    return {"spinors": spinors, "twistors": twistors, "edges": [(0, 1), (1, 2), (2, 3), (3, 0)]}


def rng_ensemble_bridge_gate(num_seeds: int = HAAR_NUM_SEEDS, entangler_family: str = "xy") -> dict[str, Any]:
    """K-seed Haar-random ensemble across both partitions, all tested
    functionals, and all tested noise channels.

    For each cell (partition × functional × noise_channel), report:
      mean and std of (inc - rand) across K seeds, plus admission rate.

    This directly addresses the convergent 3/3 P1 finding "RNG ensemble missing"
    and the convergent 3/3 P1 finding "alternative noise channel missing."
    """
    partitions = ["block", "interleaved"]
    # Round-6 fix (Grok R6 P1 + Opus R6 P1.2 + FEP design lane): add mutual
    # information I_A_B = S(A) + S(B) - S(AB) as a structurally different Φ_0
    # candidate from the bipartite-cut readout family. Mutual info is the
    # natural variational free-energy functional under a QIT-aligned FEP and
    # tests the "no signal in this readout family" verdict against an
    # alternative readout that doesn't share I_c's sign-asymmetry with respect
    # to entangler basis. If MI also fails, the within-family kill extends to
    # one more functional. If MI shows signal, that's the entry point for the
    # QIT-FEP scout family.
    # Round-7-prep: Schmidt-moment readouts M_2, M_3 added alongside I_c, LN, MI.
    # These are polynomial functions of the reduced-density spectrum (not entropy),
    # giving structurally different info from the entropy-based functionals. They
    # are still bipartite-cut readouts (Grok R6 C.1 readout-family gap not fully
    # closed) but they DO exercise spectrum shape that I_c and LN summarise away.
    # Round-8-prep: added I(A:B:C:D) multipartite information as structurally
    # different from bipartite-cut readouts (closes the named-but-unimplemented
    # Grok R6 C.1 + Opus R6 P1.2 gap properly, unlike M_2/M_3 which are
    # correlated with I_c).
    functionals = ["I_c_A_to_B", "log_negativity", "I_A_B", "M_2", "M_3", "I_ABCD"]
    # Round-8-prep: added amplitude_damping as third noise channel (Grok R6 C.2
    # noise-model gap). Non-unital, fixed point at |0⟩⟨0|, distinct from dephasing
    # (basis-preserving) and depolarizing (unital).
    noise_channels = {
        "z_dephasing": dephase_16dim,
        "depolarizing": depolarize_16dim,
        "amplitude_damping": amplitude_damping_16dim,
    }

    per_cell: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    for nc_name, nc_fn in noise_channels.items():
        per_cell[nc_name] = {}
        for partition in partitions:
            per_cell[nc_name][partition] = {}
            for fk in functionals:
                per_cell[nc_name][partition][fk] = {
                    "pure_inc_minus_rand": [],
                    "noisy_inc_minus_rand": [],
                    "pure_inc": [],
                    "pure_rand": [],
                    "noisy_inc": [],
                    "noisy_rand": [],
                    # Round-7-prep CONFOUND FIX: also collect inc - lambda_matched_random
                    # (same lam distribution, random phi). If admission persists here →
                    # phi-structure carries geometric content. If it dies → lam-magnitude
                    # confound was the source.
                    "pure_inc_minus_lammatch": [],
                    "noisy_inc_minus_lammatch": [],
                }

    # Round-7-prep: per-cell quantum relative entropy D(rho_inc || rho_rand)
    # stored SEPARATELY from the inc-minus-rand functional structure because
    # rel-entropy is one scalar per cell (not an inc-rand difference) and only
    # makes sense on the noisy half (pure-state D can diverge when sigma is
    # rank-1). FEP-aligned: this is the QIT analogue of F(q||p) when q=inc, p=rand.
    rel_entropy_cells: dict[str, dict[str, dict[str, list[float]]]] = {}
    for nc_name in noise_channels:
        rel_entropy_cells[nc_name] = {}
        for partition in partitions:
            rel_entropy_cells[nc_name][partition] = {
                "noisy_inc_vs_rand": [],
                "noisy_rand_vs_inc": [],
            }

    # Round-4 fix (Opus C2 CRITICAL): decorrelate seeds across noise channels.
    # Previously both channels used the same `seed_idx`, which made the noisy
    # cells dependent (same underlying graph, two noise applications). Now
    # noise-channel-specific offset rotates the seed into a fresh region of
    # the PRNG state for each channel, so per-cell SE is computed under proper
    # independence.
    noise_channel_offsets = {name: 1_000_000 * idx for idx, name in enumerate(noise_channels.keys())}

    for seed_idx in range(num_seeds):
        for nc_name, nc_fn in noise_channels.items():
            seed_nc = 20260522 + seed_idx + noise_channel_offsets[nc_name]
            graph = haar_random_graph(seed_nc)
            state_inc = joint_graph_state(graph, "incidence_derived", entangler_family=entangler_family)
            state_rand = joint_graph_state(graph, "random_seeded", rng_seed=seed_nc + 1, entangler_family=entangler_family)
            state_lammatch = joint_graph_state(graph, "lambda_matched_random_phi", rng_seed=seed_nc + 2, entangler_family=entangler_family)
            rho_inc = density(state_inc)
            rho_rand = density(state_rand)
            rho_lammatch = density(state_lammatch)
            rho_inc_noisy = nc_fn(rho_inc, gamma=0.30)
            rho_rand_noisy = nc_fn(rho_rand, gamma=0.30)
            rho_lammatch_noisy = nc_fn(rho_lammatch, gamma=0.30)
            trace_inc = float(torch.real(torch.trace(rho_inc_noisy)).item())
            trace_rand = float(torch.real(torch.trace(rho_rand_noisy)).item())
            trace_lammatch = float(torch.real(torch.trace(rho_lammatch_noisy)).item())
            if abs(trace_inc) > 1e-12:
                rho_inc_noisy = rho_inc_noisy / trace_inc
            if abs(trace_rand) > 1e-12:
                rho_rand_noisy = rho_rand_noisy / trace_rand
            if abs(trace_lammatch) > 1e-12:
                rho_lammatch_noisy = rho_lammatch_noisy / trace_lammatch
            for partition in partitions:
                inc_pure = joint_graph_readouts(rho_inc, partition=partition)
                rand_pure = joint_graph_readouts(rho_rand, partition=partition)
                lammatch_pure = joint_graph_readouts(rho_lammatch, partition=partition)
                inc_noisy = joint_graph_readouts(rho_inc_noisy, partition=partition)
                rand_noisy = joint_graph_readouts(rho_rand_noisy, partition=partition)
                lammatch_noisy = joint_graph_readouts(rho_lammatch_noisy, partition=partition)
                for fk in functionals:
                    cell = per_cell[nc_name][partition][fk]
                    cell["pure_inc_minus_rand"].append(inc_pure[fk] - rand_pure[fk])
                    cell["noisy_inc_minus_rand"].append(inc_noisy[fk] - rand_noisy[fk])
                    cell["pure_inc"].append(inc_pure[fk])
                    cell["pure_rand"].append(rand_pure[fk])
                    cell["noisy_inc"].append(inc_noisy[fk])
                    cell["noisy_rand"].append(rand_noisy[fk])
                    cell["pure_inc_minus_lammatch"].append(inc_pure[fk] - lammatch_pure[fk])
                    cell["noisy_inc_minus_lammatch"].append(inc_noisy[fk] - lammatch_noisy[fk])
                # Round-7-prep: compute D(rho_A_inc_noisy || rho_A_rand_noisy) on
                # the noisy-half reduced density matrices (where both are full-rank).
                # FEP-aligned: this is the QIT analogue of variational free energy
                # F(q||p) when q = inc, p = rand. Symmetrize by also reporting
                # D(rand || inc); a real basin signal should show asymmetric
                # distance growing with K.
                if partition == "block":
                    rho_a_inc_noisy = partial_trace_qubits_23(rho_inc_noisy)
                    rho_a_rand_noisy = partial_trace_qubits_23(rho_rand_noisy)
                else:
                    rho_a_inc_noisy = partial_trace_qubits_13(rho_inc_noisy)
                    rho_a_rand_noisy = partial_trace_qubits_13(rho_rand_noisy)
                d_ir = quantum_relative_entropy(rho_a_inc_noisy, rho_a_rand_noisy)
                d_ri = quantum_relative_entropy(rho_a_rand_noisy, rho_a_inc_noisy)
                rel_entropy_cells[nc_name][partition]["noisy_inc_vs_rand"].append(d_ir)
                rel_entropy_cells[nc_name][partition]["noisy_rand_vs_inc"].append(d_ri)

    def stats(lst: list[float]) -> dict[str, float]:
        t = torch.tensor(lst, dtype=DTYPE)
        return {
            "mean": float(t.mean().item()),
            "std": float(t.std(unbiased=False).item()),
            "min": float(t.min().item()),
            "max": float(t.max().item()),
            "n": len(lst),
        }

    # Round-3 fix (Opus D1, D2 + Gemini CRITICAL): add SE-aware admission
    # criterion. The previous point-estimate-only `mean > 0.02` admission
    # produced one cell that "admitted" while the per-cell std (~0.23) made
    # the result statistically meaningless. Now we require `mean > 2*SE`
    # AND `mean > 0.02`. Also emit power-analysis fields: SE, 95% CI,
    # K_required for 80% power at the 0.02 admission threshold.
    admission_threshold = ADMISSION_THRESHOLD  # module-level named constant
    z_value = 1.96  # 95% CI two-sided normal approx
    power_z_one_sided = 0.84  # 80% power, alpha=0.05 one-sided ≈ 2.49 z; using 2.49 below
    # k_required = (z_alpha + z_beta)^2 * std^2 / effect^2
    # For 80% power, α=0.05 one-sided: z_α = 1.645, z_β = 0.842, sum ≈ 2.487.
    K_REQUIRED_Z = 2.487
    summary = {}
    for nc_name in per_cell:
        summary[nc_name] = {}
        for partition in per_cell[nc_name]:
            summary[nc_name][partition] = {}
            for fk in per_cell[nc_name][partition]:
                cell = per_cell[nc_name][partition][fk]
                pure_stats = stats(cell["pure_inc_minus_rand"])
                noisy_stats = stats(cell["noisy_inc_minus_rand"])
                pure_se = pure_stats["std"] / math.sqrt(max(num_seeds, 1))
                noisy_se = noisy_stats["std"] / math.sqrt(max(num_seeds, 1))
                pure_ci_lo = pure_stats["mean"] - z_value * pure_se
                pure_ci_hi = pure_stats["mean"] + z_value * pure_se
                noisy_ci_lo = noisy_stats["mean"] - z_value * noisy_se
                noisy_ci_hi = noisy_stats["mean"] + z_value * noisy_se
                # K required to detect 0.02 effect at observed std with 80% power
                pure_k_required = float(
                    (K_REQUIRED_Z * pure_stats["std"] / admission_threshold) ** 2
                ) if admission_threshold > 0 else float("inf")
                noisy_k_required = float(
                    (K_REQUIRED_Z * noisy_stats["std"] / admission_threshold) ** 2
                ) if admission_threshold > 0 else float("inf")
                # Round-7-prep CONFOUND FIX: also compute stats for inc vs lambda_matched_random
                pure_lammatch_stats = stats(cell["pure_inc_minus_lammatch"])
                noisy_lammatch_stats = stats(cell["noisy_inc_minus_lammatch"])
                pure_lammatch_se = pure_lammatch_stats["std"] / math.sqrt(max(num_seeds, 1))
                noisy_lammatch_se = noisy_lammatch_stats["std"] / math.sqrt(max(num_seeds, 1))
                summary[nc_name][partition][fk] = {
                    "pure_inc_minus_rand": pure_stats,
                    "noisy_inc_minus_rand": noisy_stats,
                    "pure_inc_minus_lammatch": pure_lammatch_stats,
                    "noisy_inc_minus_lammatch": noisy_lammatch_stats,
                    "pure_lammatch_SE": pure_lammatch_se,
                    "noisy_lammatch_SE": noisy_lammatch_se,
                    "pure_z_vs_lammatch": pure_lammatch_stats["mean"] / pure_lammatch_se if pure_lammatch_se > 0 else 0.0,
                    "noisy_z_vs_lammatch": noisy_lammatch_stats["mean"] / noisy_lammatch_se if noisy_lammatch_se > 0 else 0.0,
                    "pure_inc": stats(cell["pure_inc"]),
                    "pure_rand": stats(cell["pure_rand"]),
                    "noisy_inc": stats(cell["noisy_inc"]),
                    "noisy_rand": stats(cell["noisy_rand"]),
                    "pure_inc_beats_rand_rate": float(
                        sum(1 for v in cell["pure_inc_minus_rand"] if v > ADMISSION_THRESHOLD) / num_seeds
                    ),
                    "noisy_inc_beats_rand_rate": float(
                        sum(1 for v in cell["noisy_inc_minus_rand"] if v > ADMISSION_THRESHOLD) / num_seeds
                    ),
                    "pure_SE": pure_se,
                    "noisy_SE": noisy_se,
                    "pure_95pct_CI": [pure_ci_lo, pure_ci_hi],
                    "noisy_95pct_CI": [noisy_ci_lo, noisy_ci_hi],
                    "pure_K_required_80pct_power": pure_k_required,
                    "noisy_K_required_80pct_power": noisy_k_required,
                }

    # POINT-ESTIMATE admission (previous criterion, kept for trail / D1 transparency)
    point_estimate_admitted = []
    for nc_name in summary:
        for partition in summary[nc_name]:
            for fk in summary[nc_name][partition]:
                s = summary[nc_name][partition][fk]
                if (
                    s["pure_inc_minus_rand"]["mean"] > admission_threshold
                    and s["noisy_inc_minus_rand"]["mean"] > admission_threshold
                ):
                    point_estimate_admitted.append((nc_name, partition, fk))

    # SE-AWARE admission (Round-3 criterion, RAW per-cell — kept for trail):
    # require mean > 2 * SE per cell AND mean > admission_threshold.
    # NOT corrected for multiple testing across the screened cells.
    # Round-4 audit (Opus C1 CRITICAL) flagged that the older 8-cell version
    # inflated family-wise false-positive rate at the null to ~17%.
    se_aware_admitted_raw = []
    for nc_name in summary:
        for partition in summary[nc_name]:
            for fk in summary[nc_name][partition]:
                s = summary[nc_name][partition][fk]
                pure_mean = s["pure_inc_minus_rand"]["mean"]
                pure_se = s["pure_SE"]
                noisy_mean = s["noisy_inc_minus_rand"]["mean"]
                noisy_se = s["noisy_SE"]
                if (
                    pure_mean > 2 * pure_se
                    and pure_mean > admission_threshold
                    and noisy_mean > 2 * noisy_se
                    and noisy_mean > admission_threshold
                ):
                    se_aware_admitted_raw.append((nc_name, partition, fk))

    # SE-AWARE admission with BONFERRONI FAMILY-WISE ERROR CONTROL (Round-4 fix):
    # n_cells screened simultaneously (dynamically computed below). At family-wise
    # alpha=0.05 one-sided, the per-cell alpha = 0.05 / n_cells.
    # Requires mean > z_FWE * SE per cell on BOTH pure and noisy halves.
    # Round-5 fix (Opus minor): use statistics.NormalDist (Python 3.8+ stdlib)
    # instead of inline Hastings approximation.
    import statistics as _statistics
    # Round-9 fix (Opus R9 B1): partition-independent functionals (I_ABCD)
    # contribute once per noise channel, not once per (noise_channel,
    # partition). Naive count would double-count them since block and
    # interleaved I_ABCD are bit-identical by construction.
    n_cells_naive = sum(
        1
        for nc_name in summary
        for partition in summary[nc_name]
        for fk in summary[nc_name][partition]
    )
    # Count partition-independent functionals once per noise channel
    n_cells_deduped = 0
    seen_partition_indep = set()
    for nc_name in summary:
        for partition in summary[nc_name]:
            for fk in summary[nc_name][partition]:
                if fk in PARTITION_INDEPENDENT_FUNCTIONALS:
                    key = (nc_name, fk)
                    if key not in seen_partition_indep:
                        seen_partition_indep.add(key)
                        n_cells_deduped += 1
                else:
                    n_cells_deduped += 1
    n_cells = n_cells_deduped
    bonferroni_alpha = FWE_ALPHA_TARGET / max(n_cells, 1)
    # One-sided upper-tail z for the per-cell alpha:
    z_fwe = _statistics.NormalDist().inv_cdf(1.0 - bonferroni_alpha)

    se_aware_admitted_bonferroni = []
    # Round-9 fix (Opus R9 B1): skip duplicate partition rows for
    # partition-independent functionals when counting Bonferroni admissions.
    _seen_partition_indep_admit = set()
    for nc_name in summary:
        for partition in summary[nc_name]:
            for fk in summary[nc_name][partition]:
                if fk in PARTITION_INDEPENDENT_FUNCTIONALS:
                    key = (nc_name, fk)
                    if key in _seen_partition_indep_admit:
                        continue
                    _seen_partition_indep_admit.add(key)
                s = summary[nc_name][partition][fk]
                pure_mean = s["pure_inc_minus_rand"]["mean"]
                pure_se = s["pure_SE"]
                noisy_mean = s["noisy_inc_minus_rand"]["mean"]
                noisy_se = s["noisy_SE"]
                if (
                    pure_mean > z_fwe * pure_se
                    and pure_mean > admission_threshold
                    and noisy_mean > z_fwe * noisy_se
                    and noisy_mean > admission_threshold
                ):
                    se_aware_admitted_bonferroni.append((nc_name, partition, fk))

    # Round-5 fix (Opus C.2): also compute Benjamini-Hochberg FDR admission.
    # Confirms that the choice of multiple-testing correction does not change
    # the verdict at K=30. FDR is less conservative than Bonferroni; if FDR
    # also rejects, the verdict is robust to correction choice.
    cell_z_pure = []
    cell_z_noisy = []
    cell_keys = []
    seen_partition_indep_fdr = set()
    for nc_name in summary:
        for partition in summary[nc_name]:
            for fk in summary[nc_name][partition]:
                if fk in PARTITION_INDEPENDENT_FUNCTIONALS:
                    key = (nc_name, fk)
                    if key in seen_partition_indep_fdr:
                        continue
                    seen_partition_indep_fdr.add(key)
                s = summary[nc_name][partition][fk]
                pure_mean = s["pure_inc_minus_rand"]["mean"]
                pure_se = s["pure_SE"]
                noisy_mean = s["noisy_inc_minus_rand"]["mean"]
                noisy_se = s["noisy_SE"]
                # One-sided z (positive = incidence > random)
                z_p = pure_mean / pure_se if pure_se > 0 else 0.0
                z_n = noisy_mean / noisy_se if noisy_se > 0 else 0.0
                cell_z_pure.append(z_p)
                cell_z_noisy.append(z_n)
                cell_keys.append((nc_name, partition, fk))
    assert len(cell_keys) == n_cells

    def _bh_admitted(zs: list[float], threshold_alpha: float, n: int) -> list[bool]:
        """Benjamini-Hochberg admission: for each cell, p_i = 1 - Phi(z_i);
        rank-sort ascending p; admit p_(k) <= (k/n) * alpha for k = 1..n."""
        pvals = [1.0 - _statistics.NormalDist().cdf(z) for z in zs]
        ranked = sorted(range(len(pvals)), key=lambda i: pvals[i])
        admitted = [False] * len(pvals)
        for rank_pos, idx in enumerate(ranked, start=1):
            crit = (rank_pos / n) * threshold_alpha
            if pvals[idx] <= crit:
                # admit this cell and all lower-rank cells
                for j in ranked[:rank_pos]:
                    admitted[j] = True
        return admitted

    fdr_pure_admit = _bh_admitted(cell_z_pure, FWE_ALPHA_TARGET, len(cell_keys))
    fdr_noisy_admit = _bh_admitted(cell_z_noisy, FWE_ALPHA_TARGET, len(cell_keys))
    se_aware_admitted_fdr = [
        cell_keys[i]
        for i in range(len(cell_keys))
        if fdr_pure_admit[i]
        and fdr_noisy_admit[i]
        and (cell_z_pure[i] * (summary[cell_keys[i][0]][cell_keys[i][1]][cell_keys[i][2]]["pure_SE"]))
        > ADMISSION_THRESHOLD
        and (cell_z_noisy[i] * (summary[cell_keys[i][0]][cell_keys[i][1]][cell_keys[i][2]]["noisy_SE"]))
        > ADMISSION_THRESHOLD
    ]

    # Canonical admission decision uses Bonferroni-corrected criterion.
    # FDR is reported alongside for completeness — Round-5 audit verified
    # FDR also rejects, confirming verdict is robust to correction choice.
    se_aware_admitted = se_aware_admitted_bonferroni

    # Worst-case K_required across cells (for power-analysis headline)
    all_k_required = []
    for nc_name in summary:
        for partition in summary[nc_name]:
            for fk in summary[nc_name][partition]:
                all_k_required.append(summary[nc_name][partition][fk]["pure_K_required_80pct_power"])
                all_k_required.append(summary[nc_name][partition][fk]["noisy_K_required_80pct_power"])
    max_k_required = float(max(all_k_required))
    median_k_required = float(sorted(all_k_required)[len(all_k_required) // 2])

    return {
        "construction": (
            f"K={num_seeds}-seed Haar-random spinor ensemble; 2 partitions x "
            "6 functionals x 3 noise channels (z-dephasing, depolarizing, "
            "amplitude damping); gamma=0.30, with partition-independent "
            "functionals deduped for multiple-testing correction. "
            "Round-3: SE-aware admission added (mean > 2*SE AND mean > 0.02). "
            "Point-estimate admission kept for trail."
        ),
        "num_seeds": num_seeds,
        "noise_channels_tested": list(noise_channels.keys()),
        "partitions_tested": partitions,
        "functionals_tested": functionals,
        "admission_threshold": admission_threshold,
        "per_cell_statistics": summary,
        "point_estimate_admitted_cells": point_estimate_admitted,
        "point_estimate_admission_count": len(point_estimate_admitted),
        "se_aware_admitted_cells_raw_2SE": se_aware_admitted_raw,
        "se_aware_admitted_cells_bonferroni": se_aware_admitted_bonferroni,
        "se_aware_admitted_cells_fdr_benjamini_hochberg": se_aware_admitted_fdr,
        "se_aware_admitted_cells": se_aware_admitted,  # canonical = bonferroni
        "se_aware_admission_count": len(se_aware_admitted),
        "any_ensemble_admission": bool(se_aware_admitted),  # canonical: SE-aware Bonferroni
        "correction_choice_robustness": {
            "bonferroni_count": len(se_aware_admitted_bonferroni),
            "fdr_count": len(se_aware_admitted_fdr),
            "raw_2SE_count": len(se_aware_admitted_raw),
            "note": (
                "Round-5 fix (Opus C.2): the choice of multiple-testing correction "
                "does not change the verdict at K=30. FDR (less conservative than "
                "Bonferroni) also rejects all cells."
            ),
        },
        "multiple_testing_correction": {
            "n_cells_screened": n_cells,
            "family_wise_alpha_target": 0.05,
            "per_cell_bonferroni_alpha": bonferroni_alpha,
            "z_FWE_one_sided": z_fwe,
            "note": (
                "Round-4 fix (Opus C1 CRITICAL): the raw 2*SE per-cell criterion "
                "inflated family-wise false-positive rate in the older 8-cell "
                "screen. "
                "Bonferroni-corrected criterion requires mean > z_FWE * SE per cell "
                "with z_FWE chosen for family-wise alpha = 0.05 / n_cells."
            ),
        },
        "noise_channel_seed_decorrelation": {
            "noise_channel_offsets": noise_channel_offsets,
            "note": (
                "Round-4 fix (Opus C2 CRITICAL): noise channels previously shared "
                "seed_idx, making the noisy cells dependent. Each channel now uses "
                "a distinct seed offset so screened noise-channel cells are "
                "independent draws under the same Haar measure."
            ),
        },
        "power_analysis": {
            "admission_threshold": admission_threshold,
            "k_used": num_seeds,
            "median_K_required_for_80pct_power": median_k_required,
            "max_K_required_for_80pct_power": max_k_required,
            "K_used_is_underpowered": num_seeds < median_k_required,
        },
        "relative_entropy_per_cell": {
            nc_name: {
                partition: {
                    "noisy_inc_vs_rand": stats(rel_entropy_cells[nc_name][partition]["noisy_inc_vs_rand"]),
                    "noisy_rand_vs_inc": stats(rel_entropy_cells[nc_name][partition]["noisy_rand_vs_inc"]),
                    "asymmetry_mean": float(
                        torch.tensor(rel_entropy_cells[nc_name][partition]["noisy_inc_vs_rand"], dtype=DTYPE).mean().item()
                        - torch.tensor(rel_entropy_cells[nc_name][partition]["noisy_rand_vs_inc"], dtype=DTYPE).mean().item()
                    ),
                }
                for partition in partitions
            }
            for nc_name in noise_channels
        },
        "relative_entropy_note": (
            "Round-7-prep: quantum relative entropy D(rho_A_inc || rho_A_rand) on "
            "the noisy half. FEP-aligned: this is the QIT analogue of variational "
            "free energy F(q || p). Reported as raw distance per cell (not "
            "inc-rand difference). Asymmetry = D(inc||rand) - D(rand||inc); zero "
            "implies symmetric distance; significant nonzero suggests directional "
            "information flow on the cut."
        ),
        "pass": True,  # scout pass = honest completion; admission verdict reported separately
    }


def analytic_correctness_baseline() -> dict[str, Any]:
    """Verify the partial-trace + entropy + log-negativity pipeline against
    canonical analytic values. Addresses Gemini-R2 / Opus-R4 finding: the
    'no signal' verdict assumes the simulation pipeline is correct, but no
    formal correctness check has been run.

    Test states and expected analytic values:
      |Bell+⟩ = (|00⟩+|11⟩)/sqrt(2):
        S(rho_A) = log 2 ≈ 0.6931, LN = 1.0
      |Bell-⟩ = (|01⟩+|10⟩)/sqrt(2):
        S(rho_A) = log 2 ≈ 0.6931, LN = 1.0
      product |00⟩:
        S(rho_A) = 0, LN = 0
      |GHZ4⟩ = (|0000⟩+|1111⟩)/sqrt(2) cut into A={0,1}, B={2,3}:
        S(rho_A on A=qubits 0,1) = log 2 ≈ 0.6931 (Schmidt rank 2)
        LN(block) = 1.0
      Maximally entangled 2-qubit state |0011⟩+|0110⟩+|1001⟩+|1100⟩ /2 etc.
    """
    rows = {}
    log2 = math.log(2.0)

    # 1. Bell+ = (|00⟩ + |11⟩) / sqrt(2). Trace out 2nd qubit -> rho_A = I/2.
    bell_plus = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
    rho_bell = density(bell_plus)
    rho_a = partial_trace_a(rho_bell)
    s_bell = entropy(rho_a)
    # LN on 2-qubit Bell pair = 1.0
    # T_B over qubit 1: column-index swap of qubit 1
    rho_bell_4d = rho_bell.reshape(2, 2, 2, 2)
    rho_bell_pt = rho_bell_4d.permute(0, 3, 2, 1).reshape(4, 4)
    bell_ln = math.log2(float(torch.sum(torch.linalg.svdvals(rho_bell_pt).real).item()))
    rows["bell_plus_2qubit"] = {
        "expected_S_A": log2,
        "measured_S_A": s_bell,
        "S_A_within_tol": abs(s_bell - log2) < 1e-9,
        "expected_LN": 1.0,
        "measured_LN": bell_ln,
        "LN_within_tol": abs(bell_ln - 1.0) < 1e-9,
        "pass": abs(s_bell - log2) < 1e-9 and abs(bell_ln - 1.0) < 1e-9,
    }

    # 2. Product |00⟩. rho_A = |0⟩⟨0|, S = 0, LN = 0.
    prod_state = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=CDTYPE)
    rho_prod = density(prod_state)
    rho_a_prod = partial_trace_a(rho_prod)
    s_prod = entropy(rho_a_prod)
    rho_prod_4d = rho_prod.reshape(2, 2, 2, 2)
    rho_prod_pt = rho_prod_4d.permute(0, 3, 2, 1).reshape(4, 4)
    prod_ln = math.log2(max(float(torch.sum(torch.linalg.svdvals(rho_prod_pt).real).item()), 1e-30))
    rows["product_state_2qubit"] = {
        "expected_S_A": 0.0,
        "measured_S_A": s_prod,
        "S_A_within_tol": abs(s_prod) < 1e-9,
        "expected_LN": 0.0,
        "measured_LN": prod_ln,
        "LN_within_tol": abs(prod_ln) < 1e-9,
        "pass": abs(s_prod) < 1e-9 and abs(prod_ln) < 1e-9,
    }

    # 3. GHZ4 = (|0000⟩ + |1111⟩) / sqrt(2). Cut A={0,1}, B={2,3}.
    # rho_AB = 1/2 (|00⟩⟨00| tensor |00⟩⟨00| + |00⟩⟨11| tensor |00⟩⟨11| + ...)
    # rho_A = Tr_B(rho_AB) = 1/2 (|00⟩⟨00| + |11⟩⟨11|), S(rho_A) = log 2.
    ghz4_state = torch.zeros(16, dtype=CDTYPE)
    ghz4_state[0] = 1.0 / math.sqrt(2.0)
    ghz4_state[15] = 1.0 / math.sqrt(2.0)
    rho_ghz4 = density(ghz4_state)
    rho_A_block = partial_trace_qubits_23(rho_ghz4)
    s_ghz4_block = entropy(rho_A_block)
    # Log-negativity for GHZ across block cut
    rho_ghz4_8d = rho_ghz4.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    rho_ghz4_pt = rho_ghz4_8d.permute(0, 1, 6, 7, 4, 5, 2, 3).reshape(16, 16)
    ghz4_block_ln = math.log2(float(torch.sum(torch.linalg.svdvals(rho_ghz4_pt).real).item()))
    rows["ghz4_block_partition"] = {
        "expected_S_A": log2,
        "measured_S_A": s_ghz4_block,
        "S_A_within_tol": abs(s_ghz4_block - log2) < 1e-9,
        "expected_LN": 1.0,
        "measured_LN": ghz4_block_ln,
        "LN_within_tol": abs(ghz4_block_ln - 1.0) < 1e-9,
        "pass": abs(s_ghz4_block - log2) < 1e-9 and abs(ghz4_block_ln - 1.0) < 1e-9,
    }

    # 4. GHZ4 under interleaved partition A={0,2}, B={1,3}.
    # Same Schmidt decomposition because |0000⟩+|1111⟩ has Schmidt rank 2 on any
    # bipartition. Should give same S = log 2, LN = 1.0.
    rho_A_inter = partial_trace_qubits_13(rho_ghz4)
    s_ghz4_inter = entropy(rho_A_inter)
    rho_ghz4_inter_pt = rho_ghz4_8d.permute(0, 5, 2, 7, 4, 1, 6, 3).reshape(16, 16)
    ghz4_inter_ln = math.log2(float(torch.sum(torch.linalg.svdvals(rho_ghz4_inter_pt).real).item()))
    rows["ghz4_interleaved_partition"] = {
        "expected_S_A": log2,
        "measured_S_A": s_ghz4_inter,
        "S_A_within_tol": abs(s_ghz4_inter - log2) < 1e-9,
        "expected_LN": 1.0,
        "measured_LN": ghz4_inter_ln,
        "LN_within_tol": abs(ghz4_inter_ln - 1.0) < 1e-9,
        "pass": abs(s_ghz4_inter - log2) < 1e-9 and abs(ghz4_inter_ln - 1.0) < 1e-9,
    }

    # 5. 4-qubit product state. All cuts have S = 0, LN = 0.
    psi_a = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    psi_b = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    prod4 = torch.kron(torch.kron(torch.kron(psi_a, psi_b), psi_a), psi_b)
    rho_prod4 = density(prod4)
    s_prod4_block = entropy(partial_trace_qubits_23(rho_prod4))
    rho_prod4_8d = rho_prod4.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    rho_prod4_pt = rho_prod4_8d.permute(0, 1, 6, 7, 4, 5, 2, 3).reshape(16, 16)
    prod4_ln = math.log2(max(float(torch.sum(torch.linalg.svdvals(rho_prod4_pt).real).item()), 1e-30))
    rows["product_4qubit_block"] = {
        "expected_S_A": 0.0,
        "measured_S_A": s_prod4_block,
        "S_A_within_tol": abs(s_prod4_block) < 1e-9,
        "expected_LN": 0.0,
        "measured_LN": prod4_ln,
        "LN_within_tol": abs(prod4_ln) < 1e-9,
        "pass": abs(s_prod4_block) < 1e-9 and abs(prod4_ln) < 1e-9,
    }

    all_pass = all(row["pass"] for row in rows.values())
    return {
        "purpose": (
            "Round-4 fix (Gemini R2 + Opus R4 P2): formal correctness check "
            "on the partial-trace + entropy + log-negativity pipeline against "
            "canonical analytic values. Closes alternative-explanation (d) "
            "'subtle simulation bug' for the K=30 null result."
        ),
        "rows": rows,
        "all_baseline_checks_pass": all_pass,
        "pass": all_pass,
    }


def negative_control_section(bridge: dict[str, Any], capacity: dict[str, Any]) -> dict[str, Any]:
    rows = {
        "NC1_productized_cut_kills_candidate_information": {
            "expected_to_fail": True,
            "candidate_Ic": bridge["candidate_readout"]["I_c_A_to_B"],
            "product_Ic": bridge["product_control_readout"]["I_c_A_to_B"],
            "candidate_minus_product_Ic": bridge["candidate_minus_product_Ic"],
            "pass": bool(bridge["candidate_minus_product_Ic"] > NC1_PURE_THRESHOLD and bridge["product_control_readout"]["I_c_A_to_B"] < NC2_PURE_FLOOR),
            "summary": "productizing rho_AB kills the candidate's cut information",
        },
        "NC2_history_erased_cut_is_maximally_bad": {
            "expected_to_fail": True,
            "history_erased_Ic": bridge["history_erased_control_readout"]["I_c_A_to_B"],
            "candidate_minus_erased_Ic": bridge["candidate_minus_erased_Ic"],
            "pass": bool(bridge["candidate_minus_erased_Ic"] > NC1_PURE_THRESHOLD and bridge["history_erased_control_readout"]["I_c_A_to_B"] < NC2B_PURE_FLOOR),
            "summary": "history-erased maximally mixed cut loses the signed coherent-information readout",
        },
        "NC3_zero_phase_beats_raw_incidence_phase": {
            "expected_to_fail": True,
            "candidate_Ic": bridge["candidate_readout"]["I_c_A_to_B"],
            "zero_phase_Ic": bridge["zero_phase_control_readout"]["I_c_A_to_B"],
            "candidate_minus_zero_phase_Ic": bridge["candidate_minus_zero_phase_Ic"],
            "pass": bool(bridge["candidate_minus_zero_phase_Ic"] < NC3_PURE_FLOOR),
            "summary": "raw phase(I_ij) is killed because zero-phase control has stronger coherent information",
        },
        "NC4_zero_phase_beats_both_candidate_and_random": {
            "expected_to_fail": True,
            "candidate_Ic": bridge["candidate_readout"]["I_c_A_to_B"],
            "random_phase_Ic": bridge["random_phase_control_readout"]["I_c_A_to_B"],
            "zero_phase_Ic": bridge["zero_phase_control_readout"]["I_c_A_to_B"],
            "candidate_below_zero_phase": bool(
                bridge["candidate_readout"]["I_c_A_to_B"] < bridge["zero_phase_control_readout"]["I_c_A_to_B"]
            ),
            "random_below_zero_phase": bool(
                bridge["random_phase_control_readout"]["I_c_A_to_B"] < bridge["zero_phase_control_readout"]["I_c_A_to_B"]
            ),
            "pass": bool(
                bridge["candidate_readout"]["I_c_A_to_B"]
                < bridge["zero_phase_control_readout"]["I_c_A_to_B"]
                and bridge["random_phase_control_readout"]["I_c_A_to_B"]
                < bridge["zero_phase_control_readout"]["I_c_A_to_B"]
            ),
            "summary": (
                "Round-2-audit-fix: under the now-seeded-real random_phase "
                "baseline, both raw incidence AND random phase lose to "
                "zero-phase. The earlier NC4 framing ('candidate beats random "
                "by > 0.2') was an artifact of the deterministic 1.7*(idx+1) "
                "formula; under real RNG sampling, candidate also loses to "
                "random. The unifying kill statement is: zero-phase beats both."
            ),
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
        "analytic_correctness_baseline": analytic_correctness_baseline(),
        "xi_bridge_candidate_phi0_coherent_information": bridge_gate(),
        "joint_graph_partition_xi": joint_graph_partition_bridge_gate(),
        "rng_ensemble_haar_K30_xy_entangler": rng_ensemble_bridge_gate(num_seeds=HAAR_NUM_SEEDS, entangler_family="xy"),
        "rng_ensemble_haar_K30_heisenberg_entangler": rng_ensemble_bridge_gate(num_seeds=HAAR_NUM_SEEDS, entangler_family="heisenberg"),
        # Round-7-prep: Ising ZZ entangler as fourth entangler family — fills in
        # the structure-distance axis between XY (1-axis XX+YY) / Heisenberg
        # (3-axis isotropic) / random (no structure). If sign reversal scales
        # with structure-distance from random, Ising should show intermediate
        # signal; if XY+Heisenberg are the special axis, Ising should be more
        # random-like.
        "rng_ensemble_haar_K30_ising_entangler": rng_ensemble_bridge_gate(num_seeds=HAAR_NUM_SEEDS, entangler_family="ising"),
        # Round-7-prep: random-unitary entangler as third entangler family,
        # NEGATIVE CONTROL for the B.1 sign-reversal claim. If sign-reversal
        # collapses under random unitaries → XY/Heisenberg basis structure was
        # load-bearing for the sign reversal. If it persists → sign reversal is
        # a more generic basis-mixing artifact, weakening B.1.
        "rng_ensemble_haar_K30_random_unitary_entangler": rng_ensemble_bridge_gate(num_seeds=HAAR_NUM_SEEDS, entangler_family="random_unitary"),
    }
    positive["finite_capacity_and_nonpromotion"] = capacity_and_nonpromotion_gate(
        bool(positive["xi_bridge_candidate_phi0_coherent_information"]["naive_raw_incidence_phase_bridge_rejected"])
    )
    negative_controls = negative_control_section(
        positive["xi_bridge_candidate_phi0_coherent_information"],
        positive["finite_capacity_and_nonpromotion"],
    )
    graveyard_companions = {
        "productized_cut_state_rejected": {
            "pass": positive["xi_bridge_candidate_phi0_coherent_information"]["product_control_readout"]["I_c_A_to_B"] < NC2_PURE_FLOOR,
            "summary": "productizing the cut removes positive coherent information",
        },
        "history_erased_cut_state_rejected": {
            "pass": positive["xi_bridge_candidate_phi0_coherent_information"]["history_erased_control_readout"]["I_c_A_to_B"] < NC2B_PURE_FLOOR,
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
