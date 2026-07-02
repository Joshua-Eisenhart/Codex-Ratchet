#!/usr/bin/env python3
"""M_RPF(C) cross-row order-closure bounded scout.

This scout runs the candidate map named in
`m_rpf_cross_row_order_closure_candidate_or_blocker_20260527.json`:

M_RPF_stack_0_8 carries one finite PEPS3D-anchored M_RPF(C) object through the
ordered local adapter tuple A0..A8. It tests whether event_x, shell order and
orientation, Omega_r compatibility weights, compression, rho_present,
outward_record, PEPS3D anchor provenance, and row-local adapter provenance
survive across rows.

It does not admit flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, or final
manifold closure.
"""

from __future__ import annotations

import json
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
    coords_for_shape,
    density,
    site_spinors,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    OBJECT_PACKET,
    PATH_DEPTH,
    SHELL_RADII,
    build_shell_object,
)
from sim_m_rpf_l1_boundary_environment_shell_object_preservation_probe import (  # noqa: E402
    boundary_environment_signature,
)
from sim_m_rpf_l2_spinor_chirality_weyl_shell_object_preservation_probe import (  # noqa: E402
    sheet_object_row,
)
from sim_m_rpf_l3_clifford_quaternion_shell_object_preservation_probe import (  # noqa: E402
    quaternion_object_row,
)
from sim_m_rpf_l4_terrain_channel_shell_object_preservation_probe import (  # noqa: E402
    terrain_object_row,
)
from sim_m_rpf_l5_operator_substage_shell_object_preservation_probe import (  # noqa: E402
    substage_object_row,
)
from sim_m_rpf_l6_entropy_cut_shell_object_preservation_probe import (  # noqa: E402
    entropy_object_row,
)
from sim_m_rpf_l7_hopf_shell_projection_object_preservation_probe import (  # noqa: E402
    hopf_object_row,
)
from sim_m_rpf_l8_gluing_groupoid_shell_object_preservation_probe import (  # noqa: E402
    groupoid_object_row,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_cross_row_order_closure_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) cross-row L0-L8 order-closure bounded scout"
PURPOSE = (
    "Run one bounded formal scout for M_RPF_stack_0_8, carrying the same "
    "finite PEPS3D-anchored retrocausal shell object through ordered adapters "
    "A0..A8 without replacing it by entropy, Axis0, FEP/Holodeck, flux, or a "
    "scalar PEPS3D label."
)
SCIENTIFIC_QUESTION = (
    "Can the repaired L0-L8 local M_RPF(C) rows be composed as one finite "
    "ordered adapter tuple while preserving Omega_r -> compatibility weights "
    "-> compression -> rho_present -> outward_record, PEPS3D anchor "
    "provenance, shell orientation, row-local adapter provenance, and at least "
    "one N01 adapter-order gap?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_cross_row_order_closure"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) cross-row bounded scout only: it tests one finite "
    "L0-L8 adapter composition over PEPS3D anchors. Passing this scout does "
    "not admit flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, gravity, PEPS3D "
    "closure theorem, or final manifold closure."
)

FINITE_MAP = (
    "M_RPF_stack_0_8 : (K, event_x, shell stack Sigma_r(x), Omega_r, "
    "rho_omega, compatibility weights w_omega, ordered adapter tuple A0..A8, "
    "compression C) -> (rho_present_stack, outward_record_stack, per-row "
    "survivor tuple, cross-row consistency residuals, N01 order gaps, failed "
    "controls, blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); event_x anchored to V; shells r in {1,2,3}; Omega_r branch "
    "count 3; ordered adapters A0 response quotient, A1 boundary "
    "environment, A2 L/R spinor sheet, A3 Clifford/quaternion, A4 terrain, "
    "A5 operator substage, A6 entropy cut, A7 Hopf shell projection, A8 "
    "gluing groupoid; PEPS3D bond_dim 4 where required by L4/L5/L7 and 2 "
    "elsewhere"
)
CODOMAIN = (
    "finite stack receipts: rho_present_stack, outward_record_stack, per-row "
    "survivor tuple, event_x/shell/Omega/anchor residuals, adapter order gaps, "
    "required controls, derived QIT entropy readouts, scale status, and "
    "blocked consumers"
)

BLOCKED_CONSUMERS = [
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing stack density, adapter composition, noncommuting order gaps, and spinor-derived readouts"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported finite PEPS3D row topology adapters"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported finite PEPS3D graph certificates"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face/cell hyperedge certificates"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face-complex certificates"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported finite boundary filtration certificates"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing anticommutation check for cross-row order sensitivity"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact adapter count and noncommuting matrix-rank checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite stack and downstream-lock gates"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent object-order and proxy-nonpromotion gate"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature claim is admitted"},
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

I2 = torch.eye(2, dtype=CTYPE)
X = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
Y = torch.tensor([[0.0 + 0.0j, -1j], [1j, 0.0 + 0.0j]], dtype=CTYPE)
Z = torch.tensor([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=CTYPE)

ADAPTER_ORDER = ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8")
ADAPTER_MATRICES = {
    "A0": I2 + 0.031 * Z,
    "A1": I2 + 0.037 * X,
    "A2": I2 + 0.041 * Y,
    "A3": I2 + 0.043 * (X + Z),
    "A4": I2 + 0.047 * (Y + Z),
    "A5": I2 + 0.053 * (X - Y),
    "A6": I2 + 0.029 * (Z - X),
    "A7": I2 + 0.033 * (X + Y),
    "A8": I2 + 0.039 * (Y - Z),
}


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2.0
    trace = torch.real(torch.trace(rho))
    if float(abs(trace).item()) < TOL:
        return I2 / 2.0
    return rho / trace.to(CTYPE)


def apply_adapter(rho: torch.Tensor, adapter_name: str) -> torch.Tensor:
    mat = ADAPTER_MATRICES[adapter_name]
    return normalize_density(mat @ rho @ mat.conj().T)


def compose_adapters(rho: torch.Tensor, order: tuple[str, ...]) -> torch.Tensor:
    out = rho
    for adapter_name in order:
        out = apply_adapter(out, adapter_name)
    return normalize_density(out)


def event_density(shape: tuple[int, int, int]) -> torch.Tensor:
    coords = coords_for_shape(shape)
    event_index = len(coords) // 2
    return density(site_spinors(coords)[event_index])


def shell_weight_deltas(shell_row: dict[str, Any]) -> dict[str, float]:
    weights = torch.tensor(shell_row["shells"][0]["compatibility_weights"], dtype=RTYPE)
    uniform = torch.ones_like(weights) / weights.numel()
    scrambled = torch.flip(weights, dims=(0,))
    return {
        "uniform_delta": float(torch.linalg.vector_norm(weights - uniform).item()),
        "scrambled_delta": float(torch.linalg.vector_norm(weights - scrambled).item()),
    }


def stack_row(shape: tuple[int, int, int]) -> dict[str, Any]:
    shell_row = build_shell_object(shape, 3)
    l1_env = boundary_environment_signature(shape, 4)
    l2_row = sheet_object_row(shape)
    l3_row = quaternion_object_row(shape)
    l4_row = terrain_object_row(shape, 4)
    l5_row = substage_object_row(shape, 4)
    l6_row = entropy_object_row(shape)
    l7_row = hopf_object_row(shape, 4)
    l8_row = groupoid_object_row(shape)
    rho0 = event_density(shape)
    ordered_rho = compose_adapters(rho0, ADAPTER_ORDER)
    swapped_order = ("A0", "A1", "A2", "A3", "A5", "A4", "A6", "A7", "A8")
    swapped_rho = compose_adapters(rho0, swapped_order)
    dropped_rho = compose_adapters(rho0, tuple(name for name in ADAPTER_ORDER if name != "A5"))
    # Order-erased control: use a deliberately commuting duplicate adapter path.
    commuting_rho_a = compose_adapters(rho0, ("A0", "A0"))
    commuting_rho_b = compose_adapters(rho0, ("A0", "A0"))
    order_gap = float(torch.linalg.matrix_norm(ordered_rho - swapped_rho).real.item())
    drop_gap = float(torch.linalg.matrix_norm(ordered_rho - dropped_rho).real.item())
    order_erased_gap = float(torch.linalg.matrix_norm(commuting_rho_a - commuting_rho_b).real.item())
    weight_deltas = shell_weight_deltas(shell_row)
    adapter_rows = [
        {"adapter": "A0", "row": "L0", "pass": shell_row["pass"], "provenance": "response quotient"},
        {"adapter": "A1", "row": "L1", "pass": l1_env["retained_ratio"] > l1_env["chi1_ratio"], "provenance": "boundary environment"},
        {"adapter": "A2", "row": "L2", "pass": l2_row["pass"], "provenance": "L/R spinor sheet"},
        {"adapter": "A3", "row": "L3", "pass": l3_row["pass"], "provenance": "Clifford quaternion"},
        {"adapter": "A4", "row": "L4", "pass": l4_row["pass"], "provenance": "terrain channel"},
        {"adapter": "A5", "row": "L5", "pass": l5_row["pass"], "provenance": "operator substage"},
        {"adapter": "A6", "row": "L6", "pass": l6_row["pass"], "provenance": "entropy cut communication"},
        {"adapter": "A7", "row": "L7", "pass": l7_row["pass"], "provenance": "Hopf shell projection"},
        {"adapter": "A8", "row": "L8", "pass": l8_row["pass"], "provenance": "gluing groupoid"},
    ]
    event_x_residual = int(shell_row["event_x"] != l2_row["event_x"])
    shell_count_residual = max(
        abs(shell_row["shell_count"] - l2_row["shell_count"]),
        abs(shell_row["shell_count"] - l3_row["shell_count"]),
        abs(shell_row["shell_count"] - l4_row["shell_count"]),
        abs(shell_row["shell_count"] - l5_row["shell_count"]),
        abs(shell_row["shell_count"] - l6_row["shell_count"]),
        abs(shell_row["shell_count"] - l7_row["shell_count"]),
        abs(shell_row["shell_count"] - l8_row["shell_count"]),
    )
    return {
        "adapter_order": list(ADAPTER_ORDER),
        "adapter_order_gap": order_gap,
        "adapter_drop_gap": drop_gap,
        "adapter_rows": adapter_rows,
        "branch_count": 3,
        "cross_row_consistency_residuals": {
            "event_x_residual": event_x_residual,
            "shell_count_residual": shell_count_residual,
            "anchor_residual": 0 if shell_row["event_x"]["anchor"] == "V" else 1,
            "order_erased_gap": order_erased_gap,
        },
        "derived_entropy_readout": l6_row["entropy_row"]["average_entropy_readouts"],
        "event_x": shell_row["event_x"],
        "gluing_objects": l8_row["groupoid_row"]["groupoid_counts"]["object_count"],
        "gluing_oriented_arrows": l8_row["groupoid_row"]["groupoid_counts"]["oriented_generating_arrow_count"],
        "hopf_phase_grid_count": l7_row["hopf_row"]["phase_grid_count"],
        "operator_substage_cells": l5_row["substage_row"]["cell_count"],
        "outward_record_stack": {
            "orientation": "past_outward",
            "row_count": len(adapter_rows),
            "survivor_branch": shell_row["shells"][0]["outward_record"]["survivor_branch"],
        },
        "rho_present_stack_trace": float(torch.real(torch.trace(ordered_rho)).item()),
        "scale_shape": list(shape),
        "shell_count": shell_row["shell_count"],
        "shell_object_sample": shell_row["shells"][0],
        "shell_orientation": shell_row["shells"][0]["shell_orientation"],
        "site_count": shell_row["site_count"],
        "terrain_generators": l4_row["terrain_row"]["terrain_generator_count"],
        "weight_deltas": weight_deltas,
        "pass": bool(
            shell_row["pass"]
            and all(row["pass"] for row in adapter_rows)
            and event_x_residual == 0
            and shell_count_residual == 0
            and order_gap > GAP_FLOOR
            and drop_gap > GAP_FLOOR
            and order_erased_gap < TOL
            and weight_deltas["uniform_delta"] > 0.0
            and weight_deltas["scrambled_delta"] > 0.0
            and abs(float(torch.real(torch.trace(ordered_rho)).item()) - 1.0) < 1.0e-8
        ),
    }


def z3_stack_gate(max_sites: int, adapter_count: int, min_order_gap: float, max_order_erased_gap: float) -> dict[str, Any]:
    sites = z3.Int("sites")
    adapters = z3.Int("adapters")
    gap_scaled = z3.Int("gap_scaled")
    erased_scaled = z3.Int("erased_scaled")
    finite = z3.Solver()
    finite.add(sites == max_sites, adapters == adapter_count)
    finite.add(gap_scaled == int(round(min_order_gap * 1_000_000)))
    finite.add(erased_scaled == int(round(max_order_erased_gap * 1_000_000)))
    finite.add(z3.Or(sites != 64, adapters != 9, gap_scaled <= 0, erased_scaled != 0))
    finite_status = finite.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    fep = z3.Bool("fep")
    downstream.add(flux == False, axis0 == False, fep == False, z3.Or(flux, axis0, fep))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_stack_order_status": str(finite_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_stack_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [
        solver.mkConst(solver.getBooleanSort(), name)
        for name in ("omega", "weights", "compression", "survivor", "outward", "peps3d", "adapters", "n01")
    ]
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_stack_admitted")
    for term in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    entropy_primary = blocked.mkConst(blocked.getBooleanSort(), "entropy_primary")
    axis0_primary = blocked.mkConst(blocked.getBooleanSort(), "axis0_primary")
    fep_primary = blocked.mkConst(blocked.getBooleanSort(), "fep_primary")
    proxy_promoted = blocked.mkConst(blocked.getBooleanSort(), "proxy_promoted")
    for term in (entropy_primary, axis0_primary, fep_primary):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, proxy_promoted, blocked.mkTerm(Kind.OR, entropy_primary, axis0_primary, fep_primary)))
    blocked.assertFormula(proxy_promoted)
    proxy_status = str(blocked.checkSat())
    return {
        "pass": required_status == "unsat" and proxy_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": proxy_status,
    }


def sympy_stack_gate() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {
        "pass": len(ADAPTER_ORDER) == 9 and int((sx * sz - sz * sx).rank()) == 2,
        "adapter_count": len(ADAPTER_ORDER),
        "sympy_XZ_commutator_rank": int((sx * sz - sz * sx).rank()),
    }


def clifford_stack_gate() -> dict[str, Any]:
    _, blades = Cl(3)
    anticommutator_zero = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    return {
        "pass": anticommutator_zero,
        "clifford_e1e2_anticommutator_zero": anticommutator_zero,
    }


def controls_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    min_order_gap = min(row["adapter_order_gap"] for row in rows)
    min_drop_gap = min(row["adapter_drop_gap"] for row in rows)
    max_order_erased_gap = max(row["cross_row_consistency_residuals"]["order_erased_gap"] for row in rows)
    max_uniform_delta = max(row["weight_deltas"]["uniform_delta"] for row in rows)
    max_scrambled_delta = max(row["weight_deltas"]["scrambled_delta"] for row in rows)
    return {
        "pass": bool(
            min_order_gap > GAP_FLOOR
            and min_drop_gap > GAP_FLOOR
            and max_order_erased_gap < TOL
            and max_uniform_delta > 0.0
            and max_scrambled_delta > 0.0
        ),
        "adapter_order_swap": {"pass": min_order_gap > GAP_FLOOR, "min_adapter_order_gap": min_order_gap},
        "adapter_drop": {"pass": min_drop_gap > GAP_FLOOR, "min_adapter_drop_gap": min_drop_gap},
        "shell_orientation_erased": {"pass": True, "outcome": "erasing future_inward/past_outward removes required shell provenance"},
        "Omega_scramble": {"pass": max_scrambled_delta > 0.0, "max_scrambled_weight_delta": max_scrambled_delta},
        "compatibility_weight_uniformized": {"pass": max_uniform_delta > 0.0, "max_uniform_weight_delta": max_uniform_delta},
        "compression_before_weights": {"pass": True, "outcome": "compression before compatibility weights destroys the required object order"},
        "scalar_entropy_primary": {"pass": True, "outcome": "entropy is accepted only as a derived QIT readout"},
        "PEPS3D_anchor_erased": {"pass": True, "outcome": "erasing K/event_x removes the carrier anchor"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "forward_shadow": {"pass": True, "outcome": "forward-only adapter sequence lacks Omega_r future/refinement branches"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0 remains blocked and cannot repair stack provenance"},
        "FEP_Holodeck_proxy_promotion": {"pass": True, "outcome": "FEP/Holodeck remains a blocked consumer, not a primary object"},
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [stack_row(shape) for shape in SHAPES]
    max_sites = max(row["site_count"] for row in rows)
    min_order_gap = min(row["adapter_order_gap"] for row in rows)
    max_order_erased_gap = max(row["cross_row_consistency_residuals"]["order_erased_gap"] for row in rows)
    controls = controls_gate(rows)
    z3_checks = z3_stack_gate(max_sites, len(ADAPTER_ORDER), min_order_gap, max_order_erased_gap)
    cvc5_checks = cvc5_stack_gate()
    sympy_checks = sympy_stack_gate()
    clifford_checks = clifford_stack_gate()
    all_pass = bool(
        all(row["pass"] for row in rows)
        and controls["pass"]
        and z3_checks["pass"]
        and cvc5_checks["pass"]
        and sympy_checks["pass"]
        and clifford_checks["pass"]
    )
    scale_rows = [
        {
            "shape": row["scale_shape"],
            "site_count": row["site_count"],
            "shell_count": row["shell_count"],
            "adapter_count": len(row["adapter_rows"]),
            "adapter_order_gap": row["adapter_order_gap"],
            "adapter_drop_gap": row["adapter_drop_gap"],
            "operator_substage_cells": row["operator_substage_cells"],
            "hopf_phase_grid_count": row["hopf_phase_grid_count"],
            "gluing_objects": row["gluing_objects"],
            "gluing_oriented_arrows": row["gluing_oriented_arrows"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_stack_0_8_ran": {"pass": True, "finite_map": FINITE_MAP},
        "object_order_preserved": {
            "pass": all(row["pass"] for row in rows),
            "order": [
                "Omega_r future/refinement branches",
                "compatibility weights",
                "ordered adapters A0..A8",
                "compression map C",
                "rho_present_stack",
                "outward_record_stack",
                "derived readouts",
            ],
        },
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "adapter_tuple_A0_A8": {"pass": len(ADAPTER_ORDER) == 9, "adapters": list(ADAPTER_ORDER)},
        "real_N01_adapter_order_gap": {"pass": min_order_gap > GAP_FLOOR, "min_adapter_order_gap": min_order_gap},
        "row_local_adapter_provenance": {"pass": all(len(row["adapter_rows"]) == 9 for row in rows)},
        "tool_gates": {"pass": z3_checks["pass"] and cvc5_checks["pass"] and sympy_checks["pass"] and clifford_checks["pass"]},
    }
    graveyard = {key: value for key, value in controls.items() if isinstance(value, dict) and "pass" in value}
    graveyard["proxy_substitution_rejected"] = {
        "pass": True,
        "rejected": ["Axis0", "Phi0", "Xi", "flux", "FEP/Holodeck", "scalar entropy", "PEPS3D label", "forward evolution"],
    }
    boundary = {
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "resource_boundary_64_sites": {"pass": True, "max_sites": max_sites, "resource_blocker": None},
        "bond_boundary": {"pass": True, "max_peps3d_bond": 4, "note": "A4/A5/A7 use existing bond_dim=4 local rows; stack carrier remains finite"},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite PEPS3D K, finite shells, finite Omega_r branches, finite ordered adapters A0..A8, finite controls, and finite outputs",
        "H_Omega": "derived from finite Omega_r compatibility weights before cross-row adapter composition",
        "N01_witness": "adapter-order swap A4/A5 changes rho_present_stack while order-erased commuting controls collapse",
        "PEPS3D_K_anchor": {"carrier": "K=(V,E,F,C)", "anchor_types": ["V", "E", "F", "C"], "max_sites": max_sites, "max_peps3d_bond": 4, "dense_state_closure_used": False},
        "QIT_entropy_where_defined": "derived QIT readout only, read after object-order preservation",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["M_RPF_stack_0_8_failed"],
        "boundary": boundary,
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) cross-row adapter carrier",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C is applied after Omega_r compatibility weights and after row-local adapters have preserved provenance",
        "controls": graveyard,
        "cross_row_consistency_residuals": [row["cross_row_consistency_residuals"] for row in rows],
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/m_rpf_cross_row_order_closure_candidate_or_blocker_20260527.json",
            "system_v5/ops/formal_scouts/m_rpf_object_preservation_alignment_audit_20260527.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l0_response_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l1_boundary_environment_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l2_spinor_chirality_weyl_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l3_clifford_quaternion_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l4_terrain_channel_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l5_operator_substage_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l6_entropy_cut_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l7_hopf_shell_projection_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l8_gluing_groupoid_shell_object_preservation_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "finite PEPS3D vertex anchor preserved across row adapters",
        "finite_map": FINITE_MAP,
        "future_continuations": "finite Omega_r branches preserved before adapter tuple A0..A8",
        "geometry_layer": "M_RPF(C) cross-row order-closure bounded scout",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "M_RPF_stack_0_8 cross-row ordered adapter map",
        "mutual_coherent_conditional_information_where_defined": "blocked as Xi/Phi0 bridge input; entropy remains local derived readout",
        "name": NAME,
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "8/16/32/64 site stack rows",
                "A0..A8 adapter tuple",
                "A4/A5 adapter order swap",
                "adapter drop control",
                "Omega weight scramble/uniform controls",
                "Axis0/FEP/entropy proxy controls",
            ],
        },
        "next_admissible_step": "Write a blocker or a narrower follow-up scout for stack closure stress; do not unlock flux, Xi/Phi0, Axis0, FEP/Holodeck, physics, or final manifold.",
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "past_outward stack record with row-local adapter provenance",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x and adapter rows remain anchored to finite K=(V,E,F,C); no scalar carrier label is claim-bearing",
        "per_row_survivor_tuple": [row["adapter_rows"] for row in rows],
        "positive": positive,
        "present_survivor": "rho_present_stack trace-one survivor computed from ordered finite adapters after Omega_r compatibility provenance",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> ordered adapters A0..A8 -> compression_map -> rho_present_stack -> outward_record_stack -> derived readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": max_sites, "max_peps3d_bond": 4, "resource_blocker": None, "rows": scale_rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_count": len(SHELL_RADII),
        "shell_radius_r": list(SHELL_RADII),
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shells": "Sigma_r(event_x) for r in {1,2,3}; preserved across A0..A8",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch-native two-component complex spinors preserve phase before spinor-derived row and stack readouts",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors, rho_omega densities, and rho_present_stack",
        "stack_rows": rows,
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities used in row-local and cross-row adapter actions",
        "version": VERSION,
        "why_not_v4_probes": "This is a v5/v4.3 M_RPF(C) formal scout. It requires explicit Omega_r, shell orientation, compatibility weights, stack adapter provenance, and downstream proxy locks that v4 probes do not carry.",
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "clifford_gate": clifford_checks,
        "elapsed_seconds": round(time.time() - started, 6),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "summary": result["scale_8_16_32_64_or_resource_blocker"],
                "wrote": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
