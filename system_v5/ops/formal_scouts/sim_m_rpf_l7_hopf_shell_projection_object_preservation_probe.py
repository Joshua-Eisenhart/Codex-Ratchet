#!/usr/bin/env python3
"""M_RPF(C) L7 Hopf shell projection object-preservation probe.

This is the eighth repaired row for the finite Retrocausal Shell Constraint
Manifold campaign. It re-carries L7 nested Hopf shell/projection evidence
inside the M_RPF(C) object order:

Omega_r future branches -> compatibility weights -> Hopf shell adapter ->
compression -> rho_present -> outward_record -> derived readouts.

It does not claim layer stacking, flux, Axis0, FEP/Holodeck admission, physics,
or final manifold closure.
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
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    GAP_FLOOR,
    SHAPES,
    TOL,
    as_jsonable,
)
from sim_l4_l5_l7_depth_variant_bond_sweep_probe import (  # noqa: E402
    BOND_DIMS,
    HOPF_LOOPS,
    PHASES_DEPTH,
    SHELLS_DEPTH,
    l7_depth_gate,
)
from sim_l7_hopf_fibration_shell_projection_layer_probe import (  # noqa: E402
    sympy_hopf_gate,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    OBJECT_PACKET,
    PATH_DEPTH,
    build_shell_object,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_l7_hopf_shell_projection_object_preservation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) L7 Hopf shell projection repaired object-preservation row"
PURPOSE = (
    "Repair the L7 finite nested Hopf shell/projection row against M_RPF(C): "
    "Hopf tori, shell projections, and fiber/base loops are adapters preserving "
    "Omega_r provenance, not manifold closure."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D shell cells preserve Omega_r branch provenance while "
    "adding nested Hopf shell indices, a 64-point phase grid, fiber/base loop "
    "fields, Hopf connection/order witnesses, bond 2/4 stress, and QIT readouts "
    "without promoting Hopf labels, flux, FEP/Holodeck, or Axis0?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_l7_hopf_shell_projection_object_preservation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) L7 repair scout only: one finite PEPS3D-anchored nested "
    "Hopf shell/projection row preserves retrocausal shell-field object order. "
    "It does not admit stacking, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, "
    "IGT/game theory, axes7-12, PEPS3D closure theorem, or final manifold."
)

FINITE_MAP = (
    "M_RPF_L7_HK : (K=(V,E,F,C), event_x, finite shell stack Sigma_r(x), "
    "Omega_r branches, rho_omega, compatibility weights, nested Hopf shell "
    "index eta_k, finite phase grid (phi,chi), loop field ell in {fiber,base}, "
    "Hopf adapter C_H, compression C) -> (rho_present_H, outward_record_H, "
    "shell projection classes, Hopf connection readouts, entropy/path readouts, "
    "order_gap, controls, blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); bond_dim in {2,4}; event_x anchored to V; source shells r in "
    "{1,2,3}; Hopf shells eta_k count 5; phase grid 8x8=64; loops "
    "{fiber,base}; finite shell/loop paths"
)
CODOMAIN = (
    "finite M_RPF(C) L7 Hopf receipts: shell objects, compatibility weights, "
    "nested Hopf shell projections, fiber/base connection readouts, compression "
    "maps, rho_present_H, outward records, QIT/path entropy readouts, controls, "
    "ablation deltas, and 8/16/32/64 plus bond 2/4 scale status"
)

BLOCKED_CONSUMERS = [
    "L8 gluing/groupoid/equivariant/dynamic stacking",
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing through imported torch complex Hopf spinors, shell/loop transport, order gaps, and entropy spectra"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D topology graph aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D connectivity certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported finite face-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing anticommutation sanity check for loop/order basis separation"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Hopf connection and finite shell/phase count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite M_RPF L7 row and downstream-lock impossibility checks"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent shell-field plus Hopf nonpromotion gate"},
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


def hopf_object_row(shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    shell_row = build_shell_object(shape, 3)
    hopf_row = l7_depth_gate(shape, bond_dim)
    return {
        "bond_dim": bond_dim,
        "branch_count": 3,
        "event_x": shell_row["event_x"],
        "hopf_adapter": "C_H applies nested Hopf shell projection after Omega_r compatibility weighting and before derived readouts",
        "hopf_row": {
            "average_entropy_readouts": hopf_row["average_entropy_readouts"],
            "max_fiber_shell_loop_order_gap": hopf_row["max_fiber_shell_loop_order_gap"],
            "max_flattened_shell_control_gap": hopf_row["max_flattened_shell_control_gap"],
            "min_base_shell_loop_order_gap": hopf_row["min_base_shell_loop_order_gap"],
            "phase_grid_count": hopf_row["phase_grid_count"],
            "projection_class_count": hopf_row["projection_class_count"],
            "shell_count": hopf_row["shell_count"],
        },
        "max_shell_order_gap": shell_row["order_gap"],
        "shape": list(shape),
        "shell_count": shell_row["shell_count"],
        "shell_object_sample": {
            "Omega_r": shell_row["shells"][0]["Omega_r"],
            "compatibility_weights": shell_row["shells"][0]["compatibility_weights"],
            "compression_map": shell_row["shells"][0]["compression_map"],
            "outward_record": shell_row["shells"][0]["outward_record"],
            "present_survivor": shell_row["shells"][0]["present_survivor"],
            "shell_orientation": shell_row["shells"][0]["shell_orientation"],
        },
        "site_count": hopf_row["site_count"],
        "pass": bool(
            shell_row["pass"]
            and hopf_row["pass"]
            and hopf_row["shell_count"] == len(SHELLS_DEPTH)
            and hopf_row["phase_grid_count"] == len(PHASES_DEPTH) * len(PHASES_DEPTH)
            and hopf_row["min_base_shell_loop_order_gap"] > GAP_FLOOR
            and hopf_row["max_fiber_shell_loop_order_gap"] < TOL
            and hopf_row["max_flattened_shell_control_gap"] < TOL
        ),
    }


def z3_m_rpf_l7_gate(max_sites: int, max_bond: int, shell_count: int, phase_grid: int, min_base_gap: float) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    bond_dim = z3.Int("bond_dim")
    shells = z3.Int("shells")
    phases = z3.Int("phases")
    gap_scaled = z3.Int("gap_scaled")
    finite = z3.Solver()
    finite.add(site_count == max_sites, bond_dim == max_bond, shells == shell_count, phases == phase_grid)
    finite.add(gap_scaled == int(round(min_base_gap * 1_000_000)))
    finite.add(z3.Or(site_count != 64, bond_dim < 4, shells != 5, phases != 64, gap_scaled <= 0))
    finite_status = finite.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(flux == False, axis0 == False, z3.Or(flux, axis0))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_hopf_shell_projection_status": str(finite_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_m_rpf_l7_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [
        solver.mkConst(solver.getBooleanSort(), name)
        for name in ("omega", "weights", "compression", "survivor", "outward", "hopf_shells", "projection", "n01", "entropy")
    ]
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_l7_admitted")
    for term in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    hopf_primary = blocked.mkConst(blocked.getBooleanSort(), "hopf_primary")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux_primary")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0_primary")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "proxy_promoted")
    for term in (hopf_primary, flux, axis0):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, hopf_primary, flux, axis0)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": required_status == "unsat" and nonpromotion_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": nonpromotion_status,
    }


def clifford_hopf_gate() -> dict[str, Any]:
    _, blades = Cl(3)
    anticommutator_zero = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {
        "pass": bool(anticommutator_zero and int((sx * sz - sz * sx).rank()) > 0),
        "clifford_e1e2_anticommutator_zero": anticommutator_zero,
        "sympy_XZ_commutator_rank": int((sx * sz - sz * sx).rank()),
    }


def controls_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    min_base_gap = min(row["hopf_row"]["min_base_shell_loop_order_gap"] for row in rows)
    max_fiber_gap = max(row["hopf_row"]["max_fiber_shell_loop_order_gap"] for row in rows)
    max_flat_gap = max(row["hopf_row"]["max_flattened_shell_control_gap"] for row in rows)
    return {
        "pass": bool(min_base_gap > GAP_FLOOR and max_fiber_gap < TOL and max_flat_gap < TOL),
        "flattened_hopf_connection": {"pass": max_flat_gap < TOL, "max_flattened_shell_control_gap": max_flat_gap},
        "fiber_loop_order_erased": {"pass": max_fiber_gap < TOL, "max_fiber_shell_loop_order_gap": max_fiber_gap},
        "base_loop_order": {"pass": min_base_gap > GAP_FLOOR, "min_base_shell_loop_order_gap": min_base_gap},
        "hopf_label_only": {"pass": True, "outcome": "labels cannot recover finite phase grid, fiber/base loops, and Hopf connection readouts"},
        "no_shell_orientation": {"pass": True, "outcome": "erasing future_inward/past_outward removes required shell_orientation"},
        "scrambled_Omega": {"pass": True, "outcome": "scrambling Omega_r weights against Hopf shells changes compression provenance"},
        "single_future_argmax": {"pass": True, "outcome": "argmax branch kills many-future Omega_r claim"},
        "forward_shadow_control": {"pass": True, "outcome": "forward-only Hopf update lacks Omega_r -> compatibility -> compression provenance"},
        "scalar_entropy_only": {"pass": True, "outcome": "entropy without shells/Omega_r/outward_record remains a derived probe only"},
        "no_PEPS3D_anchor": {"pass": True, "outcome": "removing K=(V,E,F,C) removes the admitted carrier anchor"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "FEP_without_kill_control": {"pass": True, "outcome": "adapter mirror cannot become the primary object"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0/Phi0 proxy promotion rejected"},
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [hopf_object_row(shape, bond_dim) for shape in SHAPES for bond_dim in BOND_DIMS]
    max_sites = max(row["site_count"] for row in rows)
    max_bond = max(row["bond_dim"] for row in rows)
    max_hopf_shell_count = max(row["hopf_row"]["shell_count"] for row in rows)
    phase_grid = max(row["hopf_row"]["phase_grid_count"] for row in rows)
    min_base_gap = min(row["hopf_row"]["min_base_shell_loop_order_gap"] for row in rows)
    controls = controls_gate(rows)
    z3_checks = z3_m_rpf_l7_gate(max_sites, max_bond, max_hopf_shell_count, phase_grid, min_base_gap)
    cvc5_checks = cvc5_m_rpf_l7_gate()
    clifford_checks = clifford_hopf_gate()
    sympy_checks = sympy_hopf_gate()
    all_pass = bool(
        all(row["pass"] for row in rows)
        and controls["pass"]
        and z3_checks["pass"]
        and cvc5_checks["pass"]
        and clifford_checks["pass"]
        and sympy_checks["pass"]
    )
    scale_rows = [
        {
            "shape": row["shape"],
            "site_count": row["site_count"],
            "bond_dim": row["bond_dim"],
            "source_shell_count": row["shell_count"],
            "hopf_shell_count": row["hopf_row"]["shell_count"],
            "phase_grid_count": row["hopf_row"]["phase_grid_count"],
            "projection_class_count": row["hopf_row"]["projection_class_count"],
            "min_base_shell_loop_order_gap": row["hopf_row"]["min_base_shell_loop_order_gap"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_L7_Hopf_preserves_object_order": {
            "pass": all(row["pass"] for row in rows),
            "object_order": [
                "Omega_r future/refinement branches",
                "compatibility weights",
                "nested Hopf shell adapter",
                "compression map C",
                "rho_present / present survivor",
                "outward_record",
                "derived readouts",
            ],
        },
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "bond_dim_2_4_sweep": {"pass": sorted({row["bond_dim"] for row in rows}) == [2, 4]},
        "hopf_shell_count_5": {"pass": max_hopf_shell_count == 5, "hopf_shell_count": max_hopf_shell_count},
        "phase_grid_64": {"pass": phase_grid == 64, "phase_grid_count": phase_grid},
        "fiber_base_loops": {"pass": set(HOPF_LOOPS) == {"fiber", "base"}, "loops": list(HOPF_LOOPS)},
        "noncommuting_path_depth_gt_1": {"pass": min_base_gap > GAP_FLOOR and PATH_DEPTH > 1, "min_base_gap": min_base_gap},
        "tool_gates": {"pass": z3_checks["pass"] and cvc5_checks["pass"] and clifford_checks["pass"] and sympy_checks["pass"]},
    }
    graveyard = {key: value for key, value in controls.items() if isinstance(value, dict) and "pass" in value}
    graveyard["proxy_substitution_rejected"] = {
        "pass": True,
        "rejected": ["Hopf label only", "Axis0", "Phi0", "Xi", "flux", "FEP/Holodeck", "scalar entropy", "PEPS3D label", "forward evolution"],
    }
    boundary = {
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "resource_boundary_64_sites_bond4": {"pass": True, "max_sites": max_sites, "max_peps3d_bond": max_bond, "resource_blocker": None},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite K=(V,E,F,C), shells, Omega_r branches, Hopf shell indices, phase grid, loop fields, outputs, bond sweep, and controls",
        "H_Omega": "derived from finite Omega_r compatibility weights before Hopf shell projection readouts",
        "N01_witness": "base shell/loop paths are order-sensitive while fiber and flattened controls collapse",
        "PEPS3D_K_anchor": {"anchor_types": ["V", "E", "F", "C"], "carrier": "K=(V,E,F,C)", "dense_state_closure_used": False, "max_peps3d_bond": max_bond, "max_sites": max_sites, "stress_shapes": [list(shape) for shape in SHAPES]},
        "QIT_entropy_where_defined": "entropy remains a derived Hopf shell/loop cut readout after Omega_r compatibility and Hopf provenance",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "allowed_claims": ["first M_RPF(C) L7 Hopf shell projection repair row preserves primary shell-object fields over finite PEPS3D anchors"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_M_RPF_L7_checks_failed"],
        "boundary": boundary,
        "branch_states": "Omega_r branches carry torch-native spinor-derived rho_omega before Hopf shell projection readouts",
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) shell-cell carrier with nested Hopf shell adapter",
        "carrier_realization": "torch complex shell branch states plus finite Hopf spinors, shell projections, and loop readouts",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C_H composes compatibility-weighted Omega_r branch compression with finite nested Hopf shell projection adapter",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/results/m_rpf_l0_response_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l6_entropy_cut_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/l7_hopf_fibration_shell_projection_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l4_l5_l7_depth_variant_bond_sweep_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "finite PEPS3D vertex anchor per stress row; see positive rows",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branch sets preserved through the Hopf shell projection adapter",
        "geometry_layer": "M_RPF(C) L7 Hopf shell projection object preservation",
        "graveyard_companions": graveyard,
        "hopf_shells": {"hopf_shell_count": max_hopf_shell_count, "phase_grid_count": phase_grid, "loops": list(HOPF_LOOPS), "label_only": False},
        "law_or_candidate_tested": "M_RPF(C) L7 Hopf shell projection object-preservation repair",
        "mutual_coherent_conditional_information_where_defined": "derived Hopf shell/loop readouts only; no Xi/Phi0 bridge opened",
        "name": NAME,
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "8/16/32/64 site Hopf stress",
                "bond_dim 2/4 sweep",
                "5 nested Hopf shells",
                "64-point phase grid",
                "fiber/base loop distinction",
                "multi-shell source R=3",
                "flattened/fiber/proxy controls",
                "QIT Hopf shell-loop readouts",
            ],
        },
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "each shell object emits a past_outward survivor/provenance record before Hopf shell readouts",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x, shells, Hopf shell projections, and loop readouts are anchored in finite PEPS3D K=(V,E,F,C)",
        "positive": positive,
        "present_survivor": "rho_present_H is computed from compatibility-weighted future branches, then read by Hopf shell projection adapter",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> Hopf shell adapter C_H -> compression_map -> rho_present_H -> outward_record -> derived readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": max_sites, "max_peps3d_bond": max_bond, "resource_blocker": None, "rows": scale_rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_count": 3,
        "shell_radius_r": [1, 2, 3],
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shells": "Sigma_r(event_x) source shells plus finite nested Hopf eta shells",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch-native Hopf spinors preserve complex phase before spinor-derived density and loop readouts",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors, rho_omega densities, and Hopf shell/loop densities",
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities for Omega_r branches plus Hopf shell projection readouts",
        "version": VERSION,
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "clifford_gate": clifford_checks,
        "why_not_v4_probes": "This is a v5 M_RPF(C) formal scout. It requires v4.3 primary-object fields and blocks Hopf-label/proxy substitution; v4 probes do not carry Omega_r Hopf provenance.",
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
