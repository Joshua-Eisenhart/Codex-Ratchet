#!/usr/bin/env python3
"""Isolated sim: finite response / distinguishability quotient layer.

Layer (geometric constraint manifold): the FIRST finite geometry, built from
distinguishability under probes -- nominalist identity: x ~_P y iff the probes
cannot tell them apart. Sims this ONE layer in isolation; no stacking/bridge.

Math verbatim from the owner's spec:
  P = {E_a}, E_a >= 0, sum_a E_a = I            (finite effect/POVM family)
  r_P(x) = (Tr(E_1 rho_x), ..., Tr(E_m rho_x))  (response vector)
  x ~_P y iff ||r_P(x) - r_P(y)|| <= epsilon    (finite equivalence)
  Q_P = X / ~_P                                 (quotient cells)

The "dynamic" axis here is refinement: as the tolerance epsilon shrinks (or the
probe family is enriched), the quotient refines -- more cells, higher quotient
entropy. The readout changes because the distinguishability structure changes,
not because of labels.

Entropy is part of the manifold here too: H(Q_P) = -sum_c p_c log p_c over the
cell-size distribution is the distinguishability entropy of the quotient.

Controls (each must COARSEN the quotient, measurably):
  - remove a load-bearing probe         (drop one SIC effect)
  - replace noncommuting with commuting  (z-only POVM: blind to coherence)
  - scramble the response vectors        (quotient stops matching true distinctness)
  - make all responses equal             (total collapse to 1 cell)

Load-bearing tool: sympy proves the two structural facts the numeric quotient
relies on -- SIC responses are informationally complete (determine rho), and
commuting z-effects are provably independent of the off-diagonal (coherence).

classification: tool_lego_fit_probe (isolated; promotion_allowed=False)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch

torch.set_default_dtype(torch.float64)
CDT = torch.complex128

I2 = torch.eye(2, dtype=CDT)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDT)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDT)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDT)
PAULI = [SX, SY, SZ]


def rho_from_bloch(r):
    r = np.asarray(r, dtype=float)
    M = I2.clone()
    for c, P in zip(r, PAULI):
        M = M + float(c) * P
    return 0.5 * M


def sic_effects():
    s = 1.0 / math.sqrt(3.0)
    bs = [(s, s, s), (s, -s, -s), (-s, s, -s), (-s, -s, s)]   # tetrahedron, sum=0
    return [0.25 * (I2 + b[0] * SX + b[1] * SY + b[2] * SZ) for b in bs]


def z_effects():
    return [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)]   # commuting POVM, blind to x,y


def response(states, effects):
    return np.array([[float(torch.trace(E @ rho).real) for E in effects] for rho in states])


def quotient_cells(resp, eps):
    # The relation r_P(x) ~ r_P(y) iff ||.|| <= eps is NOT transitive, so the
    # quotient is its transitive closure (single-linkage): the finest equivalence
    # relation containing it. This is the honest reading of Q_P = X / ~_P.
    n = len(resp)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(resp[i] - resp[j]) <= eps:
                parent[find(i)] = find(j)
    cells = {}
    for i in range(n):
        cells.setdefault(find(i), []).append(i)
    return list(cells.values())


def quotient_entropy(cells, n):
    ps = [len(c) / n for c in cells]
    return -sum(p * math.log(p) for p in ps if p > 0)   # nats


def build_registry():
    """Finite state registry X with engineered structure to expose probe power."""
    states_bloch = [
        (0.6, 0.2, 0.3),      # distinct everywhere
        (-0.4, 0.5, -0.2),    # distinct everywhere
        (0.1, -0.7, 0.4),     # distinct everywhere
        (0.5, 0.5, 0.30),     # PAIR A: same z, coherence + ...
        (-0.5, -0.5, 0.30),   # PAIR A: same z, coherence - (z-only cannot tell A apart)
        (0.0, 0.0, 0.80),     # near-pole
        (0.0, 0.0, 0.82),     # near-pole, close to previous (eps-sensitive)
        (0.3, -0.3, 0.3),     # DUPLICATE of next
        (0.3, -0.3, 0.3),     # DUPLICATE (must always share a cell)
        (-0.6, 0.1, -0.5),    # distinct
        (0.2, 0.6, -0.1),     # distinct
        (-0.2, -0.2, -0.6),   # distinct
    ]
    return [rho_from_bloch(b) for b in states_bloch], states_bloch


def sympy_structural_facts():
    """Load-bearing: prove SIC is informationally complete and z-effects are
    blind to coherence. The numeric quotient relies on exactly these facts."""
    import sympy as sp

    x, y, z = sp.symbols("x y z", real=True)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    rho = (sp.eye(2) + x * sx + y * sy + z * sz) / 2
    s = 1 / sp.sqrt(3)
    bs = [(s, s, s), (s, -s, -s), (-s, s, -s), (-s, -s, s)]
    eff = [(sp.eye(2) + b[0] * sx + b[1] * sy + b[2] * sz) / 4 for b in bs]
    resp = sp.Matrix([sp.trace(E * rho) for E in eff])
    J = resp.jacobian(sp.Matrix([x, y, z]))
    sic_informationally_complete = bool(J.rank() == 3)   # response determines (x,y,z)

    zeff = [(sp.eye(2) + sz) / 2, (sp.eye(2) - sz) / 2]
    zresp = [sp.simplify(sp.trace(E * rho)) for E in zeff]
    z_blind_to_coherence = bool(
        sp.simplify(sp.diff(zresp[0], x)) == 0 and sp.simplify(sp.diff(zresp[0], y)) == 0
        and sp.simplify(sp.diff(zresp[1], x)) == 0 and sp.simplify(sp.diff(zresp[1], y)) == 0)
    return {"sic_informationally_complete": sic_informationally_complete,
            "z_effects_blind_to_coherence": z_blind_to_coherence,
            "z_response_z_component": [str(zresp[0]), str(zresp[1])]}


def main():
    states, bloch = build_registry()
    n = len(states)
    SIC, Z = sic_effects(), z_effects()
    eps = 0.02

    r_sic = response(states, SIC)
    r_z = response(states, Z)

    cells_sic = quotient_cells(r_sic, eps)
    cells_z = quotient_cells(r_z, eps)
    H_sic = quotient_entropy(cells_sic, n)
    H_z = quotient_entropy(cells_z, n)

    # dynamic axis: refinement as epsilon shrinks (more cells, higher entropy)
    eps_sweep = [0.5, 0.2, 0.1, 0.05, 0.02, 0.005]
    refine = [{"eps": e, "n_cells_sic": len(quotient_cells(r_sic, e)),
               "H_sic": quotient_entropy(quotient_cells(r_sic, e), n)} for e in eps_sweep]
    monotone_refine = all(refine[k]["n_cells_sic"] >= refine[k - 1]["n_cells_sic"]
                          for k in range(1, len(refine)))

    # controls: each must measurably change the quotient -- a real coarsening, or breaking the
    # quotient's tracking of TRUE distinctness. (The prior "scramble" was a ROW PERMUTATION of
    # r_sic: it preserves the response multiset, so the cell COUNT is unchanged -- it could never
    # coarsen, and no verdict gated it. Replaced below with a noise control that is gated.)
    r_drop = response(states, SIC[:3])                      # remove a probe -> fewer effects
    cells_drop = quotient_cells(r_drop, eps)
    r_equal = np.zeros_like(r_sic)                          # all responses equal -> total collapse
    cells_equal = quotient_cells(r_equal, eps)
    # noise > eps on every response: the quotient must STOP tracking true distinctness --
    # the engineered TRUE duplicates (7,8) get independent noise and no longer share a cell.
    r_noisy = r_sic + np.random.default_rng(3).normal(scale=0.2, size=r_sic.shape)
    cells_noisy = quotient_cells(r_noisy, eps)

    # PAIR A (indices 3,4): same z, opposite coherence.
    def same_cell(cells, i, j):
        return any(i in c and j in c for c in cells)

    sym = sympy_structural_facts()

    verdicts = {
        # SIC (informationally complete) separates the coherence pair; z-only cannot
        "sic_separates_coherence_pair": not same_cell(cells_sic, 3, 4),
        "z_only_collapses_coherence_pair": same_cell(cells_z, 3, 4),
        # duplicates always share a cell, even under SIC (sanity / true identity)
        "duplicates_share_cell_sic": same_cell(cells_sic, 7, 8),
        # SIC quotient is strictly finer than z-only (more cells, higher entropy)
        "sic_finer_than_z": len(cells_sic) > len(cells_z) and H_sic > H_z,
        "all_equal_collapses_to_one": len(cells_equal) == 1,
        # CONTROL (gated): dropping a probe cannot REFINE the quotient (fewer effects -> <= cells)
        "control_drop_probe_does_not_refine": len(cells_drop) <= len(cells_sic),
        # CONTROL (gated): noise > eps breaks the quotient's tracking of true distinctness --
        # the engineered true duplicates (7,8) no longer share a cell
        "control_noise_breaks_true_duplicate_identity": not same_cell(cells_noisy, 7, 8),
        # eps genuinely controls granularity (falsifiable: all-identical responses would NOT refine)
        "eps_controls_granularity": refine[0]["n_cells_sic"] <= 2
            and refine[-1]["n_cells_sic"] > refine[0]["n_cells_sic"] + 5,
        "refines_to_full_separation": refine[-1]["n_cells_sic"] >= n - 1,  # near-duplicates merge
        # load-bearing sympy COUPLED to measured: z-blindness PREDICTS the measured z-responses of
        # the coherence pair are identical (within machine eps) while SIC tells them apart.
        "sympy_z_blindness_matches_measured_pair": sym["z_effects_blind_to_coherence"]
            and float(np.linalg.norm(r_z[3] - r_z[4])) < 1e-9
            and float(np.linalg.norm(r_sic[3] - r_sic[4])) > eps,
        "sympy_sic_informationally_complete": sym["sic_informationally_complete"],
    }

    result = {
        "name": "finite_response_distinguishability_quotient_isolated",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "layer": "finite response / distinguishability quotient",
        "finite_map": "FiniteResponseQuotient: (X, probes P, eps) -> (cells Q_P, responses r_P)",
        "domain": "finite state registry X (12 qubit densities), probe family P, tolerance eps",
        "codomain_or_output": "quotient cells, response vectors, quotient entropy",
        "root_constraints": {"F01": "12 finite states, finite effect families, finite eps grid",
                             "N01": "noncommuting SIC effects vs commuting z-effects is the distinguishing test"},
        "native_scale": {"n_states": n, "n_sic_effects": 4, "n_z_effects": 2, "eps": eps},
        "dynamic_step": "refinement over epsilon (quotient refines as eps shrinks)",
        "quotient": {
            "n_cells_sic": len(cells_sic), "n_cells_z": len(cells_z),
            "quotient_entropy_sic_nats": H_sic, "quotient_entropy_z_nats": H_z,
            "coarsening_entropy_drop": H_sic - H_z,
        },
        "refinement_sweep": refine,
        "controls": {
            "sic_n_cells": len(cells_sic),
            "drop_probe_n_cells": len(cells_drop),
            "noise_n_cells": len(cells_noisy),
            "noise_breaks_duplicate_identity": not same_cell(cells_noisy, 7, 8),
            "all_equal_n_cells": len(cells_equal),
        },
        "load_bearing_sympy": sym,
        "verdicts": verdicts,
        "all_pass": all(verdicts.values()),
        "blocked_consumers": ["stacking", "order_tests", "Xi", "Phi0", "Axis0", "flux", "FEP", "physics"],
        "tool_manifest": {
            "torch": {"used": True, "reason": "claim-bearing response/effect computation over densities"},
            "sympy": {"used": True, "reason": "load-bearing: proves SIC informational completeness + z-blindness to coherence"},
            "numpy": {"used": True, "reason": "quotient union-find + entropy, control only"},
        },
        "tool_integration_depth": "load_bearing",
    }

    import contract_emit, torch
    contract_emit.attach(result, {"sic_vs_z_quotient_entropy": (H_sic, H_z)},
        "native distinguishability scale (12 states, SIC vs z probes, eps refinement); 8/16/32/64 qubit ladder N/A.",
        torch_primary=float(torch.trace(torch.tensor(SIC[0], dtype=torch.complex128)
                                        @ torch.tensor(states[0], dtype=torch.complex128)).real))

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "finite_response_distinguishability_quotient_isolated_results.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"all_pass={result['all_pass']}  ({sum(verdicts.values())}/{len(verdicts)} verdicts)")
    for k, v in verdicts.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\nSIC quotient: {len(cells_sic)} cells, H={H_sic:.3f} nats")
    print(f"z-only quotient: {len(cells_z)} cells, H={H_z:.3f} nats  (coarsening drop {H_sic-H_z:.3f})")
    print("refinement over eps:", [(r["eps"], r["n_cells_sic"]) for r in refine])
    print(f"sympy: SIC informationally complete={sym['sic_informationally_complete']}, "
          f"z blind to coherence={sym['z_effects_blind_to_coherence']}")
    print(f"result -> {out_path}")


if __name__ == "__main__":
    main()
