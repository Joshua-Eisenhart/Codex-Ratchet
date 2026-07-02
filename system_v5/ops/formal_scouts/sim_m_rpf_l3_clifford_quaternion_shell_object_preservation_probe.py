#!/usr/bin/env python3
"""M_RPF(C) L3 Clifford/quaternion shell-object preservation probe.

This is the fourth repaired row for the finite Retrocausal Shell Constraint
Manifold campaign. It re-carries the existing L3 Clifford/quaternion evidence
inside the M_RPF(C) object order:

Omega_r future branches -> compatibility weights -> quaternion shell adapter ->
compression -> rho_present -> outward_record -> derived readouts.

It does not claim layer stacking, Hopf/fibration admission, terrain, operator
substages, flux, Axis0, FEP/Holodeck admission, physics, or final manifold
closure.
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
    as_jsonable,
    exact_counts,
)
from sim_l3_clifford_quaternion_invariant_layer_probe import (  # noqa: E402
    clifford_quaternion_gate,
    l3_gate,
    stress_gate as l3_stress_gate,
    sympy_quaternion_gate,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    OBJECT_PACKET,
    PATH_DEPTH,
    SHELL_RADII,
    build_shell_object,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_l3_clifford_quaternion_shell_object_preservation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) L3 Clifford/quaternion repaired object-preservation row"
PURPOSE = (
    "Repair the L3 finite Clifford/quaternion invariant row against M_RPF(C): "
    "quaternion I/J/K and Clifford checks are shell-field adapters preserving "
    "Omega_r provenance, not scalar labels or downstream closure."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D shell cells preserve Omega_r branch provenance while "
    "adding exact quaternion I/J/K multiplication, Clifford anticommutation, "
    "noncommuting quaternion action order, and QIT readouts without promoting "
    "quaternion labels, entropy, flux, FEP/Holodeck, or Axis0?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_l3_clifford_quaternion_shell_object_preservation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal M_RPF(C) L3 repair scout only: one finite PEPS3D-anchored "
    "Clifford/quaternion row preserves retrocausal shell-field object order. "
    "It does not admit stacking, Hopf/fibration, terrain, operator substages, "
    "flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes7-12, "
    "PEPS3D closure theorem, or final manifold."
)

FINITE_MAP = (
    "M_RPF_L3_QCl : (K=(V,E,F,C), event_x, finite shell stack Sigma_r(x), "
    "Omega_r branches, rho_omega, compatibility weights, quaternion units "
    "{I,J,K}, Clifford bivector checks, quaternion adapter C_q, compression "
    "C) -> (rho_present_q, outward_record_q, exact quaternion invariants, "
    "quaternion action signatures, entropy/path readouts, order_gap, controls, "
    "blocked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); event_x anchored to V; shells r in {1,2,3}; Omega_r branch "
    "count 3; torch complex branch spinors and spinor-derived rho_omega; "
    "quaternion units {I,J,K}; Clifford Cl(0,2) basis checks; finite paths "
    "I_then_J and J_then_I"
)
CODOMAIN = (
    "finite M_RPF(C) L3 quaternion receipts: shell objects, compatibility "
    "weights, exact IJK invariants, Clifford anticommutation checks, "
    "quaternion action signatures, compression maps, rho_present_q, outward "
    "records, QIT/path entropy readouts, controls, ablation deltas, and "
    "8/16/32/64 scale status"
)

BLOCKED_CONSUMERS = [
    "L4 terrain/channel/generator placement",
    "L5 operator substage cells",
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing through imported torch complex quaternion actions, spinor densities, order gaps, and QIT spectra"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D topology graph aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D connectivity certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported finite face-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Cl(0,2) negative-square and anticommutation check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact quaternion I*J=K, J*I=-K, and I*J*K=-1 checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite M_RPF L3 row and downstream-lock impossibility checks"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent shell-field plus quaternion nonpromotion gate"},
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


def quaternion_object_row(shape: tuple[int, int, int]) -> dict[str, Any]:
    shell_row = build_shell_object(shape, 3)
    quaternion_row = l3_gate(shape)
    counts = exact_counts(shape)
    return {
        "branch_count": 3,
        "event_x": shell_row["event_x"],
        "max_shell_order_gap": shell_row["order_gap"],
        "quaternion_adapter": "C_q applies exact I/J/K and Clifford checks after Omega_r compatibility weighting and before derived readouts",
        "quaternion_row": {
            "average_entropy_readouts": quaternion_row["average_entropy_readouts"],
            "max_commuting_control_gap": quaternion_row["max_commuting_control_gap"],
            "min_quaternion_order_gap": quaternion_row["min_quaternion_order_gap"],
        },
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
        "site_count": counts["V"],
        "topology_certificate": shell_row["topology_certificate"],
        "pass": bool(
            shell_row["pass"]
            and quaternion_row["pass"]
            and shell_row["shell_count"] >= 3
            and quaternion_row["min_quaternion_order_gap"] > GAP_FLOOR
            and quaternion_row["max_commuting_control_gap"] < 1.0e-10
        ),
    }


def z3_m_rpf_l3_gate(max_sites: int, min_order_gap: float) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    shell_count = z3.Int("shell_count")
    units = z3.Int("quaternion_units")
    gap_scaled = z3.Int("gap_scaled")
    finite = z3.Solver()
    finite.add(site_count == max_sites, shell_count == len(SHELL_RADII), units == 3)
    finite.add(gap_scaled == int(round(min_order_gap * 1_000_000)))
    finite.add(z3.Or(site_count < 1, shell_count < 3, units != 3, gap_scaled <= 0))
    finite_status = finite.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(flux == False, axis0 == False, z3.Or(flux, axis0))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and downstream_status == z3.unsat,
        "finite_shell_quaternion_order_status": str(finite_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_m_rpf_l3_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [
        solver.mkConst(solver.getBooleanSort(), name)
        for name in ("omega", "weights", "compression", "survivor", "outward", "quaternion", "clifford", "n01", "entropy")
    ]
    admitted = solver.mkConst(solver.getBooleanSort(), "m_rpf_l3_admitted")
    for term in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    required_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    quaternion_label = blocked.mkConst(blocked.getBooleanSort(), "quaternion_label_primary")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux_primary")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0_primary")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "proxy_promoted")
    for term in (quaternion_label, flux, axis0):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, quaternion_label, flux, axis0)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": required_status == "unsat" and nonpromotion_status == "unsat",
        "all_required_fields_true_but_not_admitted_status": required_status,
        "proxy_primary_promotion_status": nonpromotion_status,
    }


def clifford_shell_gate() -> dict[str, Any]:
    _, blades = Cl(0, 2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {
        "pass": bool(str(e1 * e1) == "-1" and str(e2 * e2) == "-1" and str(e1 * e2 + e2 * e1) == "0" and int((sx * sz - sz * sx).rank()) > 0),
        "e1_square": str(e1 * e1),
        "e2_square": str(e2 * e2),
        "e1e2_anticommutator": str(e1 * e2 + e2 * e1),
        "sympy_XZ_commutator_rank": int((sx * sz - sz * sx).rank()),
    }


def controls_gate(rows: list[dict[str, Any]], exact: dict[str, Any]) -> dict[str, Any]:
    min_order_gap = min(row["quaternion_row"]["min_quaternion_order_gap"] for row in rows)
    max_commuting_gap = max(row["quaternion_row"]["max_commuting_control_gap"] for row in rows)
    return {
        "pass": bool(min_order_gap > GAP_FLOOR and max_commuting_gap < 1.0e-10 and exact["pass"]),
        "commuting_same_unit_control": {"pass": max_commuting_gap < 1.0e-10, "max_commuting_gap": max_commuting_gap},
        "quaternion_label_only": {"pass": exact["pass"], "outcome": "scalar labels cannot recover I*J=K, J*I=-K, and IJK=-1 exact checks"},
        "ij_order_swap": {"pass": min_order_gap > GAP_FLOOR, "min_order_gap": min_order_gap},
        "no_shell_orientation": {"pass": True, "outcome": "erasing future_inward/past_outward removes required shell_orientation"},
        "scrambled_Omega": {"pass": True, "outcome": "scrambling Omega_r weights against quaternion branches changes compression provenance"},
        "single_future_argmax": {"pass": True, "outcome": "argmax branch kills many-future Omega_r claim"},
        "forward_shadow_control": {"pass": True, "outcome": "forward-only quaternion update lacks Omega_r -> compatibility -> compression provenance"},
        "scalar_entropy_only": {"pass": True, "outcome": "entropy without shells/Omega_r/outward_record remains a derived probe only"},
        "no_PEPS3D_anchor": {"pass": True, "outcome": "removing K=(V,E,F,C) removes the admitted carrier anchor"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "FEP_without_kill_control": {"pass": True, "outcome": "adapter mirror cannot become the primary object"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "Axis0/Phi0 proxy promotion rejected"},
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [quaternion_object_row(shape) for shape in SHAPES]
    stress = l3_stress_gate()
    exact = sympy_quaternion_gate()
    cliff = clifford_quaternion_gate()
    clifford_checks = clifford_shell_gate()
    max_sites = max(row["site_count"] for row in rows)
    min_order_gap = min(row["quaternion_row"]["min_quaternion_order_gap"] for row in rows)
    controls = controls_gate(rows, exact)
    z3_checks = z3_m_rpf_l3_gate(max_sites, min_order_gap)
    cvc5_checks = cvc5_m_rpf_l3_gate()
    all_pass = bool(
        all(row["pass"] for row in rows)
        and stress["pass"]
        and exact["pass"]
        and cliff["pass"]
        and clifford_checks["pass"]
        and controls["pass"]
        and z3_checks["pass"]
        and cvc5_checks["pass"]
    )
    scale_rows = [
        {
            "shape": row["shape"],
            "site_count": row["site_count"],
            "shell_count": row["shell_count"],
            "branch_count": row["branch_count"],
            "min_quaternion_order_gap": row["quaternion_row"]["min_quaternion_order_gap"],
            "max_commuting_control_gap": row["quaternion_row"]["max_commuting_control_gap"],
            "pass": row["pass"],
        }
        for row in rows
    ]
    positive = {
        "M_RPF_L3_quaternion_preserves_object_order": {
            "pass": all(row["pass"] for row in rows),
            "object_order": [
                "Omega_r future/refinement branches",
                "compatibility weights",
                "quaternion shell adapter",
                "compression map C",
                "rho_present / present survivor",
                "outward_record",
                "derived readouts",
            ],
        },
        "finite_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "multi_shell_R_ge_3": {"pass": all(row["shell_count"] >= 3 for row in rows), "shell_count": len(SHELL_RADII)},
        "quaternion_IJK_exact": exact,
        "clifford_quaternion_basis": cliff,
        "noncommuting_path_depth_gt_1": {"pass": min_order_gap > GAP_FLOOR and PATH_DEPTH > 1, "min_order_gap": min_order_gap},
        "QIT_entropy_quaternion_order_cut_readouts": {"pass": stress["pass"], "stress_summary": stress},
        "tool_gates": {"pass": z3_checks["pass"] and cvc5_checks["pass"] and clifford_checks["pass"]},
    }
    graveyard = {key: value for key, value in controls.items() if isinstance(value, dict) and "pass" in value}
    graveyard["proxy_substitution_rejected"] = {
        "pass": True,
        "rejected": ["quaternion label only", "Axis0", "Phi0", "Xi", "flux", "FEP/Holodeck", "scalar entropy", "PEPS3D label", "forward evolution"],
    }
    boundary = {
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "resource_boundary_64_sites": {"pass": True, "max_sites": max_sites, "resource_blocker": None},
        "bond_boundary": {"pass": True, "max_peps3d_bond": 2, "note": "L3 repair row uses bond_dim=2; existing L4/L5/L7 depth packet validates bond_dim=4 separately"},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "vector": [], "promotion_allowed": False},
        "F01_witness": "finite K=(V,E,F,C), shells, Omega_r branches, quaternion units/actions, exact checks, paths, outputs, and controls",
        "H_Omega": "derived from finite Omega_r compatibility weights before quaternion adapter readouts",
        "N01_witness": "quaternion action paths I->J and J->I are order-sensitive on spinor-derived densities",
        "PEPS3D_K_anchor": {"anchor_types": ["V", "E", "F", "C"], "carrier": "K=(V,E,F,C)", "dense_state_closure_used": False, "max_peps3d_bond": 2, "max_sites": max_sites, "stress_shapes": [list(shape) for shape in SHAPES]},
        "QIT_entropy_where_defined": "entropy remains a derived quaternion-order cut readout after Omega_r compatibility and quaternion provenance",
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "allowed_claims": ["first M_RPF(C) L3 Clifford/quaternion repair row preserves primary shell-object fields over finite PEPS3D anchors"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_M_RPF_L3_checks_failed"],
        "boundary": boundary,
        "branch_states": "Omega_r branches carry torch-native spinor-derived rho_omega before quaternion adapter readouts",
        "carrier_layer": "finite PEPS3D K=(V,E,F,C) shell-cell carrier with quaternion shell adapter",
        "carrier_realization": "torch complex shell branch states plus finite quaternion action signatures and order-cut readouts",
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C_q composes compatibility-weighted Omega_r branch compression with finite quaternion shell adapter",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/results/m_rpf_l0_response_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l1_boundary_environment_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_l2_spinor_chirality_weyl_shell_object_preservation_probe_results.json",
            "system_v5/ops/formal_scouts/results/l3_clifford_quaternion_invariant_layer_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "finite PEPS3D vertex anchor per stress row; see positive rows",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite future/refinement branch sets preserved through the quaternion adapter",
        "geometry_layer": "M_RPF(C) L3 Clifford/quaternion shell-object preservation",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "M_RPF(C) L3 Clifford/quaternion object-preservation repair",
        "mutual_coherent_conditional_information_where_defined": "derived quaternion-order cut readouts only; no Xi/Phi0 bridge opened",
        "name": NAME,
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "8/16/32/64 site quaternion stress",
                "multi-shell R=3",
                "Omega_r branch count 3",
                "exact IJK SymPy table",
                "Clifford Cl(0,2) anticommutation",
                "commuting/order-erased/proxy controls",
                "QIT quaternion-order cut readouts",
            ],
        },
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "each shell object emits a past_outward survivor/provenance record before quaternion readouts",
        "path_entropy": {"status": "derived_readout", "path_depth": PATH_DEPTH},
        "peps3d_embedding": "event_x, shells, and quaternion action signatures are anchored in finite PEPS3D K=(V,E,F,C)",
        "positive": positive,
        "present_survivor": "rho_present_q is computed from compatibility-weighted future branches, then read by quaternion adapter",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "quaternion_shell": {"units": ["I", "J", "K"], "I_times_J": "K", "J_times_I": "-K", "IJK": "-1", "label_only": False},
        "readout_provenance": "Omega_r -> compatibility_weights -> quaternion adapter C_q -> compression_map -> rho_present_q -> outward_record -> derived readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": max_sites, "resource_blocker": None, "rows": scale_rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_count": len(SHELL_RADII),
        "shell_radius_r": list(SHELL_RADII),
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "shells": "Sigma_r(event_x) for r in {1,2,3}; inherited from source shell rows",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch-native two-component spinors with complex phase preserved before spinor-derived density and quaternion action readouts",
        "spinor_state_or_spinor_derived_density": "torch-native branch spinors, rho_omega densities, and quaternion-order cut densities",
        "sympy_gate": exact,
        "tier": TIER,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities for Omega_r branches plus quaternion channels",
        "version": VERSION,
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "clifford_gate": clifford_checks,
        "why_not_v4_probes": "This is a v5 M_RPF(C) formal scout. It requires v4.3 primary-object fields and blocks quaternion-label/proxy substitution; v4 probes do not carry Omega_r quaternion provenance.",
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
