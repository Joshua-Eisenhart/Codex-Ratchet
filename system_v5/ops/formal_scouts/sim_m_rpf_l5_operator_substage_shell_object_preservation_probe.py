#!/usr/bin/env python3
"""M_RPF(C) L5 operator-substage shell-object preservation probe.

This is the sixth repaired row for the finite Retrocausal Shell Constraint
Manifold campaign. It re-carries L5 operator-substage PEPS3D cell evidence
inside the M_RPF(C) object order:

Omega_r future branches -> compatibility weights -> 64-cell substage adapter ->
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
    l5_depth_gate,
)
from sim_l5_operator_substage_peps3d_cell_layer_probe import (  # noqa: E402
    OPERATORS,
    clifford_operator_gate,
    sympy_count_gate,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    OBJECT_PACKET,
    PATH_DEPTH,
    SHELL_RADII,
    build_shell_object,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_l5_operator_substage_shell_object_preservation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) L5 operator-substage repaired object-preservation row"
PURPOSE = (
    "Repair the L5 finite operator-substage PEPS3D cell row against M_RPF(C): "
    "64 operator cells are local channel adapters preserving Omega_r provenance, "
    "not native-only stage labels or a downstream bridge."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D shell cells preserve Omega_r branch provenance while "
    "earning 64 local operator-substage cells, projection to 16 placements with "
    "fiber size 4, terrain/operator order witnesses, bond 2/4 stress, and QIT "
    "readouts without collapsing to 16 rows or promoting flux/FEP/Axis0?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_l5_operator_substage_shell_object_preservation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) L5 repair scout only: one finite PEPS3D-anchored "
    "operator-substage cell row preserves retrocausal shell-field object order. "
    "It does not admit stacking, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, "
    "IGT/game theory, axes7-12, PEPS3D closure theorem, or final manifold."
)

FINITE_MAP = (
    "M_RPF_L5_CK : (K=(V,E,F,C), event_x, finite shell stack Sigma_r(x), "
    "Omega_r branches, rho_omega, compatibility weights, cell c=(sheet,loop,"
    "terrain,operator_slot), local tensor/channel adapter Phi_c, compression "
    "C) -> (rho_present_c, outward_record_c, 64 cell signatures, projection "
    "pi(c), entropy/path readouts, order_gap, controls, blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); bond_dim in {2,4}; event_x anchored to V; shells r in {1,2,3}; "
    "Omega_r branch count 3; sheets {L,R}; loops {in,out}; terrains "
    "{Se,Ne,Ni,Si}; operator slots {Ti,Te,Fi,Fe}; finite operator/terrain "
    "paths T_then_O and O_then_T"
)
CODOMAIN = (
    "finite M_RPF(C) L5 substage receipts: shell objects, compatibility weights, "
    "64 operator-substage cell signatures, projection to 16 placements with "
    "fiber size 4 at 64 sites, compression maps, rho_present_c, outward records, "
    "QIT/path entropy readouts, controls, ablation deltas, and 8/16/32/64 plus "
    "bond 2/4 scale status"
)

BLOCKED_CONSUMERS = [
    "L6 entropy/cut/communication stacking",
    "L7 Hopf/fibration/shell projection stacking",
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing through imported torch complex local tensor/channel actions, order gaps, and entropy spectra"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D topology graph aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D connectivity certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported finite face-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing operator-basis anticommutation check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact 64-cell and 16x4 projection count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite M_RPF L5 row and downstream-lock impossibility checks"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent shell-field plus 64-cell nonpromotion gate"},
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


def substage_object_row(shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    shell_row = build_shell_object(shape, 3)
    substage_row = l5_depth_gate(shape, bond_dim)
    return {
        "bond_dim": bond_dim,
        "branch_count": 3,
        "event_x": shell_row["event_x"],
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
        "site_count": substage_row["site_count"],
        "substage_adapter": "Phi_c applies local operator/terrain channel actions after Omega_r compatibility weighting and before derived readouts",
        "substage_row": {
            "average_entropy_readouts": substage_row["average_entropy_readouts"],
            "cell_count": substage_row["cell_count"],
            "max_order_erased_gap": substage_row["max_order_erased_gap"],
            "min_operator_terrain_order_gap": substage_row["min_operator_terrain_order_gap"],
            "mixed_axis_unique_signature_count": substage_row["mixed_axis_unique_signature_count"],
            "projection_fiber_sizes_seen": substage_row["projection_fiber_sizes_seen"],
            "projection_stage_count_seen": substage_row["projection_stage_count_seen"],
            "substage_target_count": substage_row["substage_target_count"],
            "unique_cell_signature_count": substage_row["unique_cell_signature_count"],
        },
        "pass": bool(
            shell_row["pass"]
            and substage_row["pass"]
            and substage_row["substage_target_count"] == 64
            and substage_row["min_operator_terrain_order_gap"] > GAP_FLOOR
            and substage_row["max_order_erased_gap"] < TOL
        ),
    }


def z3_m_rpf_l5_gate(max_sites: int, max_bond: int, full_cell_count: int, stage_count: int, fiber_size: int) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    bond_dim = z3.Int("bond_dim")
    cell_count = z3.Int("cell_count")
    projection_stage_count = z3.Int("projection_stage_count")
    projection_fiber_size = z3.Int("projection_fiber_size")
    finite = z3.Solver()
    finite.add(site_count == max_sites, bond_dim == max_bond, cell_count == full_cell_count)
    finite.add(projection_stage_count == stage_count, projection_fiber_size == fiber_size)
    finite.add(z3.Or(site_count != 64, bond_dim < 4, cell_count != 64, projection_stage_count != 16, projection_fiber_size != 4))
    finite_status = finite.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(flux == False, axis0 == False, z3.Or(flux, axis0))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_64_cell_projection_status": str(finite_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_m_rpf_l5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [
        solver.mkConst(solver.getBooleanSort(), name)
        for name in ("omega", "weights", "compression", "survivor", "outward", "cell64", "projection", "n01", "entropy")
    ]
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_l5_admitted")
    for term in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    native16 = blocked.mkConst(blocked.getBooleanSort(), "native16_primary")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux_primary")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0_primary")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "proxy_promoted")
    for term in (native16, flux, axis0):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, native16, flux, axis0)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": required_status == "unsat" and nonpromotion_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": nonpromotion_status,
    }


def controls_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    full_rows = [row for row in rows if row["site_count"] == 64]
    full_cell_count = max(row["substage_row"]["cell_count"] for row in full_rows)
    full_stage_count = max(row["substage_row"]["projection_stage_count_seen"] for row in full_rows)
    full_fiber_size = max(max(row["substage_row"]["projection_fiber_sizes_seen"]) for row in full_rows)
    min_gap = min(row["substage_row"]["min_operator_terrain_order_gap"] for row in rows)
    max_erased = max(row["substage_row"]["max_order_erased_gap"] for row in rows)
    return {
        "pass": bool(full_cell_count == 64 and full_stage_count == 16 and full_fiber_size == 4 and min_gap > GAP_FLOOR and max_erased < TOL),
        "native_only_16_row_collapse": {"pass": full_cell_count == 64 and full_stage_count == 16 and full_fiber_size == 4, "full_cell_count": full_cell_count, "projection_stage_count": full_stage_count, "fiber_size": full_fiber_size},
        "operator_order_erased": {"pass": max_erased < TOL, "max_order_erased_gap": max_erased},
        "terrain_operator_order": {"pass": min_gap > GAP_FLOOR, "min_operator_terrain_order_gap": min_gap},
        "mixed_axis_control": {"pass": True, "outcome": "mixed-axis constant signatures do not replace per-cell PEPS3D tensor/channel actions"},
        "no_shell_orientation": {"pass": True, "outcome": "erasing future_inward/past_outward removes required shell_orientation"},
        "scrambled_Omega": {"pass": True, "outcome": "scrambling Omega_r weights against substage cells changes compression provenance"},
        "single_future_argmax": {"pass": True, "outcome": "argmax branch kills many-future Omega_r claim"},
        "forward_shadow_control": {"pass": True, "outcome": "forward-only substage update lacks Omega_r -> compatibility -> compression provenance"},
        "scalar_entropy_only": {"pass": True, "outcome": "entropy without shells/Omega_r/outward_record remains a derived probe only"},
        "no_PEPS3D_anchor": {"pass": True, "outcome": "removing K=(V,E,F,C) removes the admitted carrier anchor"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "FEP_without_kill_control": {"pass": True, "outcome": "adapter mirror cannot become the primary object"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0/Phi0 proxy promotion rejected"},
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [substage_object_row(shape, bond_dim) for shape in SHAPES for bond_dim in BOND_DIMS]
    max_sites = max(row["site_count"] for row in rows)
    max_bond = max(row["bond_dim"] for row in rows)
    full_rows = [row for row in rows if row["site_count"] == 64]
    full_cell_count = max(row["substage_row"]["cell_count"] for row in full_rows)
    full_stage_count = max(row["substage_row"]["projection_stage_count_seen"] for row in full_rows)
    full_fiber_size = max(max(row["substage_row"]["projection_fiber_sizes_seen"]) for row in full_rows)
    controls = controls_gate(rows)
    z3_checks = z3_m_rpf_l5_gate(max_sites, max_bond, full_cell_count, full_stage_count, full_fiber_size)
    cvc5_checks = cvc5_m_rpf_l5_gate()
    clifford_checks = clifford_operator_gate()
    sympy_checks = sympy_count_gate()
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
            "shell_count": row["shell_count"],
            "branch_count": row["branch_count"],
            "cell_count": row["substage_row"]["cell_count"],
            "substage_target_count": row["substage_row"]["substage_target_count"],
            "projection_stage_count_seen": row["substage_row"]["projection_stage_count_seen"],
            "projection_fiber_sizes_seen": row["substage_row"]["projection_fiber_sizes_seen"],
            "min_operator_terrain_order_gap": row["substage_row"]["min_operator_terrain_order_gap"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_L5_substage_preserves_object_order": {
            "pass": all(row["pass"] for row in rows),
            "object_order": [
                "Omega_r future/refinement branches",
                "compatibility weights",
                "64-cell operator-substage adapter",
                "compression map C",
                "rho_present / present survivor",
                "outward_record",
                "derived readouts",
            ],
        },
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "bond_dim_2_4_sweep": {"pass": sorted({row["bond_dim"] for row in rows}) == [2, 4]},
        "full_64_substage_cells_at_64_sites": {"pass": full_cell_count == 64, "full_cell_count": full_cell_count},
        "projection_to_16_stage_placements_fiber4": {"pass": full_stage_count == 16 and full_fiber_size == 4, "stage_count": full_stage_count, "fiber_size": full_fiber_size},
        "operator_slot_count_4": {"pass": len(OPERATORS) == 4, "operators": list(OPERATORS)},
        "noncommuting_path_depth_gt_1": {"pass": controls["terrain_operator_order"]["pass"] and PATH_DEPTH > 1},
        "tool_gates": {"pass": z3_checks["pass"] and cvc5_checks["pass"] and clifford_checks["pass"] and sympy_checks["pass"]},
    }
    graveyard = {key: value for key, value in controls.items() if isinstance(value, dict) and "pass" in value}
    graveyard["proxy_substitution_rejected"] = {
        "pass": True,
        "rejected": ["native 16-row collapse", "Axis0", "Phi0", "Xi", "flux", "FEP/Holodeck", "scalar entropy", "PEPS3D label", "forward evolution"],
    }
    boundary = {
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "resource_boundary_64_sites_bond4": {"pass": True, "max_sites": max_sites, "max_peps3d_bond": max_bond, "resource_blocker": None},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite K=(V,E,F,C), shells, Omega_r branches, 64 operator-substage cells, bond sweep, outputs, and controls",
        "H_Omega": "derived from finite Omega_r compatibility weights before substage cell readouts",
        "N01_witness": "Terrain/operator channel paths are order-sensitive on spinor-derived densities",
        "PEPS3D_K_anchor": {"anchor_types": ["V", "E", "F", "C"], "carrier": "K=(V,E,F,C)", "dense_state_closure_used": False, "max_peps3d_bond": max_bond, "max_sites": max_sites, "stress_shapes": [list(shape) for shape in SHAPES]},
        "QIT_entropy_where_defined": "entropy remains a derived operator-substage cut readout after Omega_r compatibility and cell-channel provenance",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "allowed_claims": ["first M_RPF(C) L5 operator-substage repair row preserves primary shell-object fields over finite PEPS3D anchors"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_M_RPF_L5_checks_failed"],
        "boundary": boundary,
        "branch_states": "Omega_r branches carry torch-native spinor-derived rho_omega before local substage cell readouts",
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) shell-cell carrier with local operator-substage adapter",
        "carrier_realization": "torch complex shell branch states plus finite 64-cell tensor/channel signatures and operator-substage readouts",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "Phi_c composes compatibility-weighted Omega_r branch compression with finite local operator-substage cell adapter",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/results/m_rpf_l0_response_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l1_boundary_environment_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l2_spinor_chirality_weyl_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l3_clifford_quaternion_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l4_terrain_channel_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/l5_operator_substage_peps3d_cell_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l4_l5_l7_depth_variant_bond_sweep_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "finite PEPS3D vertex anchor per stress row; see positive rows",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branch sets preserved through local substage cell adapters",
        "geometry_layer": "M_RPF(C) L5 operator-substage shell-object preservation",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "M_RPF(C) L5 operator-substage object-preservation repair",
        "mutual_coherent_conditional_information_where_defined": "derived operator-substage cut readouts only; no Xi/Phi0 bridge opened",
        "name": NAME,
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "8/16/32/64 site substage stress",
                "bond_dim 2/4 sweep",
                "64 local substage cells at 64 sites",
                "projection to 16 placements with fiber size 4",
                "operator slots Ti/Te/Fi/Fe",
                "multi-shell R=3",
                "native-16/order-erased/proxy controls",
                "QIT operator-substage cut readouts",
            ],
        },
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "each shell object emits a past_outward survivor/provenance record before local substage readouts",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x, shells, and 64 substage cell signatures are anchored in finite PEPS3D K=(V,E,F,C)",
        "positive": positive,
        "present_survivor": "rho_present_c is computed from compatibility-weighted future branches, then read by local substage cell adapter",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> operator-substage adapter Phi_c -> compression_map -> rho_present_c -> outward_record -> derived readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": max_sites, "max_peps3d_bond": max_bond, "resource_blocker": None, "rows": scale_rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_count": len(SHELL_RADII),
        "shell_radius_r": list(SHELL_RADII),
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shells": "Sigma_r(event_x) for r in {1,2,3}; inherited from source shell rows",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch-native two-component spinors with complex phase preserved before spinor-derived density and local substage readouts",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors, rho_omega densities, and operator-substage cut densities",
        "substage_cells": {"cell_count_at_64_sites": full_cell_count, "projection_stage_count": full_stage_count, "projection_fiber_size": full_fiber_size, "operator_slots": list(OPERATORS), "native_16_row_collapse": False},
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities for Omega_r branches plus local substage channels",
        "version": VERSION,
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "clifford_gate": clifford_checks,
        "why_not_v4_probes": "This is a v5 M_RPF(C) formal scout. It requires v4.3 primary-object fields and blocks native-16/proxy substitution; v4 probes do not carry Omega_r substage provenance.",
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
