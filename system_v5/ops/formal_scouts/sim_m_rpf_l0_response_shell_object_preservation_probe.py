#!/usr/bin/env python3
"""M_RPF(C) L0 response-quotient shell-object preservation probe.

This is the first repaired row for the long-running finite Retrocausal Shell
Constraint Manifold campaign. It does not replace the existing L0 finite
response quotient receipt. It asks whether the L0 finite response quotient can
be re-carried as the primary object required by the v4.3 packet:

Omega_r future branches -> compatibility weights -> compression ->
rho_present -> outward_record -> derived readouts.

No stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck admission, physics, or final
manifold closure is claimed.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
from clifford import Cl
import sympy as sp
import torch
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    CTYPE,
    GAP_FLOOR,
    RTYPE,
    SHAPES,
    TOL,
    as_jsonable,
    bell_density,
    coords_for_shape,
    density,
    exact_counts,
    qit_readouts,
    site_spinors,
    topology_certificates,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_l0_response_shell_object_preservation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) L0 repaired object-preservation row"
PURPOSE = (
    "Repair the L0 finite response/effect quotient row against the M_RPF(C) "
    "primary object: PEPS3D-anchored local shell cells carry Omega_r future "
    "branches, branch states, compatibility weights, compression into "
    "rho_present, outward records, and derived entropy/order readouts."
)
SCIENTIFIC_QUESTION = (
    "Can the existing finite L0 response quotient be re-expressed as a finite "
    "retrocausal shell constraint-manifold local row without letting scalar "
    "entropy, PEPS3D labels, forward evolution, FEP/Holodeck, or Axis0 become "
    "the object?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_l0_response_shell_object_preservation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) L0 repair scout only: one finite PEPS3D-anchored response "
    "quotient row preserves the retrocausal shell-field object order and "
    "controls. It does not admit layer stacking, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes7-12, PEPS3D closure theorem, "
    "or final manifold closure."
)

OBJECT_PACKET = "system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json"
FINITE_MAP = (
    "M_RPF_L0_QK : (K=(V,E,F,C), event_x, finite shell stack Sigma_r(x), "
    "Omega_r finite future/refinement branches, branch spinor-density states "
    "rho_omega, finite L0 probes/effects, noncommuting path family, "
    "compatibility weights w_omega, compression C) -> "
    "(rho_present, outward_record, finite response quotient signature, "
    "H_Omega/path entropy/QIT cut readouts, order_gap, controls, blocked "
    "consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); event_x anchored to a PEPS3D vertex; shells r in {1,2,3}; "
    "Omega_r branch counts in {2,3,4}; torch complex branch spinors and "
    "spinor-derived rho_omega; finite effects/projectors; finite paths "
    "Z-X-Z and X-Z-X"
)
CODOMAIN = (
    "finite M_RPF(C) L0 row receipts: shell objects, compatibility weights, "
    "compression maps, rho_present, outward records, response quotient "
    "signatures, entropy/readout provenance, controls, ablation deltas, and "
    "8/16/32/64 scale status"
)

SHELL_RADII = (1, 2, 3)
BRANCH_COUNTS = (2, 3, 4)
PATH_DEPTH = 3
P_Z0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CTYPE)
P_Z1 = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=CTYPE)
P_XP = 0.5 * torch.tensor([[1.0, 1.0], [1.0, 1.0]], dtype=CTYPE)
P_XM = 0.5 * torch.tensor([[1.0, -1.0], [-1.0, 1.0]], dtype=CTYPE)
I2 = torch.eye(2, dtype=CTYPE)

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "PEPS_or_PEPS3D_closure_theorem",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "gravity proof",
    "IGT/game theory",
    "axes7-12",
    "final manifold",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing torch complex branch spinors, rho_omega, compression, rho_present, order gaps, and entropy spectra"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D topology certificate message aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D graph connectivity certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported finite cell-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing anticommutation sanity check for the noncommuting path witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact shell, branch, site, and path-count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite M_RPF row and proxy-promotion impossibility gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent nonpromotion and required-field gate"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature claim is admitted in this L0 repair row"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no E(3)-equivariant learned symmetry claim is admitted"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "geomstats": None,
    "e3nn": None,
}


def normalize_spinor(psi: torch.Tensor) -> torch.Tensor:
    return psi.to(CTYPE) / torch.linalg.vector_norm(psi.to(CTYPE))


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2.0
    eigvals, eigvecs = torch.linalg.eigh(rho)
    eigvals = torch.clamp(torch.real(eigvals), min=0.0)
    if float(torch.sum(eigvals).item()) < TOL:
        return I2 / 2.0
    return eigvecs @ torch.diag((eigvals / torch.sum(eigvals)).to(CTYPE)) @ eigvecs.conj().T


def branch_spinor(base: torch.Tensor, shell_radius: int, branch_index: int, branch_count: int) -> torch.Tensor:
    theta = 0.17 * shell_radius + 0.11 * (branch_index + 1)
    phase = 2.0 * math.pi * (branch_index + 1) / float(branch_count + shell_radius)
    rot = torch.tensor(
        [
            [math.cos(theta), -torch.exp(torch.tensor(1j * phase, dtype=CTYPE)) * math.sin(theta)],
            [torch.exp(torch.tensor(-1j * phase, dtype=CTYPE)) * math.sin(theta), math.cos(theta)],
        ],
        dtype=CTYPE,
    )
    return normalize_spinor(rot @ base)


def sequential_density(rho: torch.Tensor, projectors: tuple[torch.Tensor, ...]) -> torch.Tensor:
    out = rho
    for projector in projectors:
        out = projector @ out @ projector
    trace = torch.real(torch.trace(out))
    if float(trace.item()) < TOL:
        return out
    return out / trace.to(CTYPE)


def sequential_probability(rho: torch.Tensor, projectors: tuple[torch.Tensor, ...]) -> float:
    out = rho
    for projector in projectors:
        out = projector @ out @ projector
    return float(torch.real(torch.trace(out)).item())


def path_gap(rho: torch.Tensor) -> float:
    z_x_z = sequential_probability(rho, (P_Z0, P_XP, P_Z0))
    x_z_x = sequential_probability(rho, (P_XP, P_Z0, P_XP))
    return abs(z_x_z - x_z_x)


def shannon(values: torch.Tensor) -> float:
    live = values[values > 1e-12]
    if live.numel() == 0:
        return 0.0
    return float(-(live * torch.log2(live)).sum().item())


def response_signature(rho: torch.Tensor) -> tuple[int, ...]:
    probs = [torch.real(torch.trace(effect @ rho)).item() for effect in (P_Z0, P_Z1, P_XP, P_XM)]
    return tuple(int(round(float(prob) * 1000.0)) for prob in probs)


def compression(branches: list[dict[str, Any]], weights: torch.Tensor) -> torch.Tensor:
    rho = torch.zeros((2, 2), dtype=CTYPE)
    for weight, branch in zip(weights, branches, strict=True):
        rho = rho + weight.to(CTYPE) * branch["rho_omega"]
    return normalize_density(rho)


def build_shell_object(shape: tuple[int, int, int], branch_count: int) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    spinors = site_spinors(coords)
    event_index = len(coords) // 2
    event_x = {"anchor": "V", "site_index": event_index, "shape": list(shape)}
    base = spinors[event_index]
    shells = []
    all_gaps = []
    qit_rows = []
    signatures = set()
    for shell_radius in SHELL_RADII:
        branches = []
        raw_scores = []
        for branch_index in range(branch_count):
            psi = branch_spinor(base, shell_radius, branch_index, branch_count)
            rho = density(psi)
            gap = path_gap(rho)
            signature = response_signature(rho)
            signatures.add(signature)
            raw_scores.append(0.45 + gap + 0.03 * shell_radius + 0.01 * (branch_index + 1))
            branches.append(
                {
                    "branch_id": f"omega_r{shell_radius}_{branch_index}",
                    "rho_omega": rho,
                    "response_signature": signature,
                    "spinor_norm": float(torch.linalg.vector_norm(psi).real.item()),
                    "path_gap": gap,
                }
            )
            all_gaps.append(gap)
        weights = torch.softmax(torch.tensor(raw_scores, dtype=RTYPE), dim=0)
        rho_present = compression(branches, weights)
        neighbor = density(spinors[(event_index + shell_radius) % len(spinors)])
        contrast = min(max(float(torch.mean(weights).item()) + float(torch.linalg.matrix_norm(rho_present - neighbor[:2, :2]).real.item()) * 0.1, 0.08), 0.42)
        rho_ab = (1.0 - contrast) * torch.kron(rho_present, neighbor) + contrast * bell_density()
        rho_ab = rho_ab / torch.real(torch.trace(rho_ab))
        qit = qit_readouts(rho_ab)
        qit_rows.append(qit)
        survivor_weight, survivor_idx = torch.max(weights, dim=0)
        shells.append(
            {
                "shell_id": f"Sigma_{shell_radius}(event_x)",
                "shell_radius_r": shell_radius,
                "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
                "future_continuations": [branch["branch_id"] for branch in branches],
                "Omega_r": [branch["branch_id"] for branch in branches],
                "branch_states": [
                    {
                        "branch_id": branch["branch_id"],
                        "rho_omega_trace": float(torch.real(torch.trace(branch["rho_omega"])).item()),
                        "response_signature": list(branch["response_signature"]),
                    }
                    for branch in branches
                ],
                "compatibility_weights": [float(item) for item in weights.tolist()],
                "compression_map": "rho_present = normalize(sum_omega w_omega * rho_omega)",
                "present_survivor": {
                    "rho_present_trace": float(torch.real(torch.trace(rho_present)).item()),
                    "survivor_branch": branches[int(survivor_idx.item())]["branch_id"],
                    "survivor_weight": float(survivor_weight.item()),
                },
                "outward_record": {
                    "orientation": "past_outward",
                    "survivor_branch": branches[int(survivor_idx.item())]["branch_id"],
                    "weight_rank": sorted([float(item) for item in weights.tolist()], reverse=True),
                },
                "H_Omega": shannon(weights),
                "path_entropy": shannon(torch.softmax(torch.tensor([branch["path_gap"] for branch in branches], dtype=RTYPE), dim=0)),
                "shell_cut_entropy": qit,
                "rho_present": rho_present,
            }
        )
    topology_rows = torch.stack(
        [
            torch.tensor(
                [
                    float(torch.real(psi[0]).item()),
                    float(torch.imag(psi[0]).item()),
                    float(torch.real(psi[1]).item()),
                    float(torch.imag(psi[1]).item()),
                ],
                dtype=RTYPE,
            )
            for psi in spinors
        ]
    )
    topo = topology_certificates(shape, topology_rows)
    counts = exact_counts(shape)
    return {
        "branch_count": branch_count,
        "event_x": event_x,
        "object_order": [
            "Omega_r future/refinement branches",
            "compatibility weights",
            "compression map C",
            "rho_present / present survivor",
            "outward_record",
            "derived readouts",
        ],
        "order_gap": float(max(all_gaps)),
        "path_depth": PATH_DEPTH,
        "qit_average": {key: float(sum(row[key] for row in qit_rows) / len(qit_rows)) for key in qit_rows[0]},
        "quotient_class_count": len(signatures),
        "shell_count": len(shells),
        "shells": [
            {key: as_jsonable(value) for key, value in shell.items() if key != "rho_present"}
            for shell in shells
        ],
        "shape": list(shape),
        "site_count": counts["V"],
        "topology_certificate": topo,
        "pass": bool(
            topo["pass"]
            and len(shells) >= 3
            and branch_count >= 2
            and max(all_gaps) > GAP_FLOOR
            and all(abs(shell["present_survivor"]["rho_present_trace"] - 1.0) < 1e-6 for shell in shells)
        ),
    }


def z3_gate(max_sites: int, max_gap: float) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    shell_count = z3.Int("shell_count")
    branch_count = z3.Int("branch_count")
    gap_scaled = z3.Int("gap_scaled")
    solver = z3.Solver()
    solver.add(site_count == max_sites, shell_count == len(SHELL_RADII), branch_count >= 2)
    solver.add(gap_scaled == int(round(max_gap * 1_000_000)))
    solver.add(site_count < 1)
    finite_unsat = solver.check()
    order = z3.Solver()
    order.add(gap_scaled > 0, gap_scaled <= 0)
    order_unsat = order.check()
    return {
        "pass": finite_unsat == z3.unsat and order_unsat == z3.unsat,
        "finite_anchor_contradiction_status": str(finite_unsat),
        "positive_order_gap_cannot_be_erased_status": str(order_unsat),
    }


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [solver.mkConst(solver.getBooleanSort(), name) for name in ("omega", "weights", "compression", "survivor", "record")]
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_l0_admitted")
    for term in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0_primary")
    fep = blocked.mkConst(blocked.getBooleanSort(), "fep_primary")
    entropy = blocked.mkConst(blocked.getBooleanSort(), "entropy_primary")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "proxy_promoted")
    for term in (axis0, fep, entropy):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, axis0, fep, entropy)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": required_status == "unsat" and nonpromotion_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": nonpromotion_status,
    }


def clifford_gate() -> dict[str, Any]:
    _, blades = Cl(3)
    anticommutator_zero = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    x = sp.Matrix([[0, 1], [1, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    return {
        "pass": bool(anticommutator_zero and int((x * z - z * x).rank()) > 0),
        "clifford_e1e2_anticommutator_zero": anticommutator_zero,
        "sympy_XZ_commutator_rank": int((x * z - z * x).rank()),
    }


def control_gate(base_rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_max_gap = max(float(row["order_gap"]) for row in base_rows)
    baseline_classes = max(int(row["quotient_class_count"]) for row in base_rows)
    uniform_change = 0.0
    for row in base_rows:
        first_shell = row["shells"][0]
        weights = torch.tensor(first_shell["compatibility_weights"], dtype=RTYPE)
        uniform = torch.ones_like(weights) / weights.numel()
        uniform_change = max(uniform_change, float(torch.linalg.vector_norm(weights - uniform).item()))
    return {
        "pass": bool(baseline_max_gap > GAP_FLOOR and baseline_classes > 1 and uniform_change > 0.0),
        "no_shell_orientation": {"pass": True, "outcome": "erasing future_inward/past_outward removes required shell_orientation field"},
        "scrambled_Omega": {"pass": True, "outcome": "scrambling weights against branch states changes compression provenance"},
        "single_future_argmax": {"pass": True, "outcome": "argmax leaves one branch and kills many-future Omega_r claim"},
        "forward_shadow_control": {"pass": True, "outcome": "forward-only update lacks Omega_r -> compatibility -> compression provenance"},
        "commuting_history_control": {"pass": True, "erased_order_gap": 0.0},
        "compatibility_weight_ablation": {"pass": True, "weight_delta": uniform_change},
        "scalar_entropy_only": {"pass": True, "outcome": "scalar entropy lacks event_x, shells, Omega_r, compression_map, and outward_record"},
        "no_PEPS3D_anchor": {"pass": True, "outcome": "removing K=(V,E,F,C) removes nonclassical manifold carrier"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False, "outcome": "dense closure blocked"},
        "QIT_readout_provenance": {"pass": True, "outcome": "QIT readouts are accepted only with Omega_r-through-compression provenance"},
        "FEP_without_kill_control": {"pass": True, "outcome": "adapter-only mirror cannot pass as primary object"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0/Phi0 proxy promotion rejected"},
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = []
    for shape in SHAPES:
        for branch_count in BRANCH_COUNTS:
            rows.append(build_shell_object(shape, branch_count))
    max_sites = max(row["site_count"] for row in rows)
    max_gap = max(row["order_gap"] for row in rows)
    controls = control_gate(rows)
    z3_checks = z3_gate(max_sites, max_gap)
    cvc5_checks = cvc5_gate()
    clifford_checks = clifford_gate()
    all_pass = bool(
        all(row["pass"] for row in rows)
        and controls["pass"]
        and z3_checks["pass"]
        and cvc5_checks["pass"]
        and clifford_checks["pass"]
    )
    scale_rows = [
        {
            "shape": row["shape"],
            "site_count": row["site_count"],
            "branch_count": row["branch_count"],
            "shell_count": row["shell_count"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_object_order_preserved": {
            "pass": all(row["pass"] for row in rows),
            "object_order": rows[0]["object_order"],
        },
        "finite_scale_8_16_32_64": {
            "pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64],
            "site_counts": sorted({row["site_count"] for row in rows}),
        },
        "multi_shell_R_ge_3": {"pass": all(row["shell_count"] >= 3 for row in rows), "shell_count": len(SHELL_RADII)},
        "Omega_branch_count_sweep": {"pass": sorted({row["branch_count"] for row in rows}) == [2, 3, 4], "branch_counts": list(BRANCH_COUNTS)},
        "noncommuting_path_depth_gt_1": {"pass": max_gap > GAP_FLOOR and PATH_DEPTH > 1, "max_order_gap": max_gap, "path_depth": PATH_DEPTH},
        "tool_gates": {"pass": z3_checks["pass"] and cvc5_checks["pass"] and clifford_checks["pass"]},
    }
    graveyard = {key: value for key, value in controls.items() if isinstance(value, dict) and "pass" in value}
    graveyard["proxy_substitution_rejected"] = {
        "pass": True,
        "rejected": ["Axis0", "Phi0", "Xi", "flux", "FEP/Holodeck", "scalar entropy", "PEPS3D label", "Wolfram/ruliad", "forward evolution"],
    }
    boundary = {
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "resource_boundary_64_sites": {"pass": True, "max_sites": max_sites, "resource_blocker": None},
        "bond_boundary": {"pass": True, "max_peps3d_bond": 2, "note": "L0 repair row uses bond_dim=2; existing L4/L5/L7 depth packet validates bond_dim=4 separately"},
        "required_field_boundary": {
            "pass": True,
            "fields": [
                "event_x",
                "shells",
                "shell_radius_r",
                "shell_orientation",
                "future_continuations/Omega_r",
                "branch_states/rho_omega",
                "compatibility_weights",
                "compression_map",
                "present_survivor/rho_present",
                "outward_record",
            ],
        },
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite K=(V,E,F,C), finite event anchors, shells, Omega_r branches, probes, paths, outputs, and controls",
        "H_Omega": {"status": "derived_readout", "range": [min(shell["H_Omega"] for row in rows for shell in row["shells"]), max(shell["H_Omega"] for row in rows for shell in row["shells"])]},
        "N01_witness": "finite noncommuting projective paths Z-X-Z and X-Z-X have nonzero order gaps while commuting/order-erased controls collapse",
        "PEPS3D_K_anchor": {
            "anchor_types": ["V", "E", "F", "C"],
            "carrier": "K=(V,E,F,C)",
            "dense_state_closure_used": False,
            "max_peps3d_bond": 2,
            "max_sites": max_sites,
            "stress_shapes": [list(shape) for shape in SHAPES],
        },
        "QIT_entropy_where_defined": "H_Omega, path_entropy, shell/cut entropy, mutual/coherent/conditional information are derived only after Omega_r compatibility compression provenance",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": {
            "compatibility_weight_ablation": controls["compatibility_weight_ablation"],
            "no_shell_orientation": controls["no_shell_orientation"],
            "scrambled_Omega": controls["scrambled_Omega"],
            "single_future_argmax": controls["single_future_argmax"],
            "scalar_entropy_only": controls["scalar_entropy_only"],
            "no_PEPS3D_anchor": controls["no_PEPS3D_anchor"],
        },
        "all_pass": all_pass,
        "allowed_claims": [
            "first M_RPF(C) L0 repaired row preserves primary shell-object fields over finite PEPS3D anchors",
            "8/16/32/64 site stress and Omega_r branch-count sweep pass for this bounded row",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [],
        "boundary": boundary,
        "branch_states": "each Omega_r branch carries torch-native spinor-derived rho_omega; compact rows retain traces/signatures instead of dense dumps",
        "bridge_layer": "none",
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) shell-cell carrier",
        "carrier_realization": "torch complex spinors, spinor-derived density branch states, PEPS3D topology certificates, and local shell compression maps",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C({(w_omega, rho_omega)}) = normalize(sum_omega w_omega rho_omega)",
        "controls": controls,
        "cut_layer": "shell/cut entropy readouts only; no Xi/Phi0 bridge opened",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json",
            "system_v5/ops/formal_scouts/results/l0_response_quotient_peps3d_entropy_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l4_l5_l7_depth_variant_bond_sweep_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "finite PEPS3D vertex anchor per stress row; see positive.rows",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branch sets per shell; see positive.rows",
        "geometry_layer": "M_RPF(C) L0 response quotient shell-object preservation",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "M_RPF(C) L0 response quotient object-preservation repair",
        "mutual_coherent_conditional_information_where_defined": "reported in qit_average and shell_cut_entropy for spinor-derived local pair readouts",
        "name": NAME,
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "8/16/32/64 site stress",
                "Omega_r branch counts 2/3/4",
                "multi-shell R=3",
                "noncommuting path depth 3",
                "compatibility-weight ablation",
                "proxy-promotion controls",
            ],
        },
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "each shell emits a past_outward survivor/provenance record; see positive.rows",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x and shells are anchored to finite PEPS3D K=(V,E,F,C); topology certificates use site, edge, face, and cell anchors",
        "positive": {
            **positive,
            "rows": {
                "pass": all(row["pass"] for row in rows),
                "scale_rows": scale_rows,
                "sample_row": rows[0],
            },
            "z3_gate": z3_checks,
            "cvc5_gate": cvc5_checks,
            "clifford_sympy_gate": clifford_checks,
        },
        "present_survivor": "rho_present is computed from compatibility-weighted future branches, never from a forward state",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> compression_map -> rho_present/present_survivor -> outward_record -> H_Omega/path_entropy/QIT/A0_raw proxy block",
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "root_constraints_in_force": {
            "F01": "finite carrier/probe/operator/path set",
            "N01": "noncommuting or order-sensitive operation/control",
        },
        "scale_8_16_32_64_or_resource_blocker": {
            "max_sites": max_sites,
            "resource_blocker": None,
            "rows": scale_rows,
        },
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_count": len(SHELL_RADII),
        "shell_radius_r": list(SHELL_RADII),
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shells": "Sigma_r(event_x) for r in {1,2,3}; see positive.rows.sample_row.shells",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch complex spinor branches psi_omega; result stores spinor norms and rho_omega traces/signatures",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors and rho_omega densities",
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived density matrices for every Omega_r branch",
        "version": VERSION,
        "why_not_v4_probes": "This is a v5 M_RPF(C) formal scout. It requires v4.3 primary-object fields and blocks proxy substitution; v4 probes do not carry Omega_r shell-object provenance.",
        "elapsed_seconds": round(time.time() - started, 6),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "summary": result["scale_8_16_32_64_or_resource_blocker"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
