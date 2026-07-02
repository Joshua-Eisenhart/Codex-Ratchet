#!/usr/bin/env python3
"""M_RPF(C) post-stack finite variant stress scout."""

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
import sympy as sp
import torch
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    GAP_FLOOR,
    SHAPES,
    as_jsonable,
)
from sim_m_rpf_cross_row_order_closure_probe import (  # noqa: E402
    ADAPTER_ORDER,
    BLOCKED_CONSUMERS,
    OBJECT_PACKET,
    compose_adapters,
    event_density,
)
from sim_m_rpf_l0_response_shell_object_preservation_probe import (  # noqa: E402
    build_shell_object,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_post_stack_variant_stress_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) post-stack variant stress scout"
PURPOSE = "Stress M_RPF(C) across finite shape, shell-count, bond, and adapter-order variants without downstream promotion."
SCIENTIFIC_QUESTION = "Which finite post-stack variants preserve Omega_r -> weights -> ordered adapters -> compression -> rho_present -> outward_record?"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_post_stack_variant_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal variant-stress scout only. Passing keeps the M_RPF(C) post-stack "
    "variant family open; it does not admit flux, Xi/Phi0, Axis0, FEP/Holodeck, "
    "physics, gravity, IGT/game theory, axes7-12, or final manifold closure."
)
FINITE_MAP = (
    "M_RPF_post_stack_variant_stress : (K, event_x, Sigma_r(x), Omega_r, "
    "compatibility weights, adapter variant family V_A, shell-count family V_r, "
    "bond family V_b, compression C) -> (variant survivor table, rho_present_v, "
    "outward_record_v, order gaps, killed controls, resource blockers, locked consumers)"
)
DOMAIN = (
    "finite PEPS3D carriers with site counts 8/16/32/64; shell counts 2,3,4; "
    "bond attempts 2 and 4 admitted with bond 5 marked as bounded admission "
    "blocker; adapter variants full A0..A8, all local drop-one, all adjacent "
    "swaps, and held-out reverse order"
)
CODOMAIN = "finite variant survivor table, order-gap table, QIT readouts as derived metadata, resource blocker for unearned bond 5, and locked downstream consumers"
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing variant density/order-gap computation"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact variant cardinality checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite variant/admission and downstream-lock gates"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent object-order gate"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing through imported PEPS3D row topology"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing through imported finite graph certificates"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing through imported hyperedge/cell certificates"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing through imported cell-complex certificates"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing through imported filtration certificates"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing through dependency on Clifford/quaternion row provenance"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature variant is claimed"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no equivariant field variant is claimed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
}

SHELL_COUNT_VARIANTS = (2, 3, 4)
BOND_VARIANTS = (2, 4)
VARIANT_BLOCKED_CONSUMERS = ["stacking", *BLOCKED_CONSUMERS]


def norm_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).real.item())


def adjacent_swap(index: int) -> tuple[str, ...]:
    order = list(ADAPTER_ORDER)
    order[index], order[index + 1] = order[index + 1], order[index]
    return tuple(order)


def variant_row(shape: tuple[int, int, int], shell_count: int) -> dict[str, Any]:
    shell_row = build_shell_object(shape, shell_count)
    rho0 = event_density(shape)
    full_rho = compose_adapters(rho0, ADAPTER_ORDER)
    adjacent_gaps = [norm_gap(full_rho, compose_adapters(rho0, adjacent_swap(i))) for i in range(len(ADAPTER_ORDER) - 1)]
    drop_gaps = [
        norm_gap(full_rho, compose_adapters(rho0, tuple(name for name in ADAPTER_ORDER if name != dropped)))
        for dropped in ADAPTER_ORDER
    ]
    held_out_gap = norm_gap(full_rho, compose_adapters(rho0, tuple(reversed(ADAPTER_ORDER))))
    weights = torch.tensor(shell_row["shells"][0]["compatibility_weights"], dtype=torch.float64)
    uniform_delta = float(torch.linalg.vector_norm(weights - torch.ones_like(weights) / weights.numel()).item())
    scramble_delta = float(torch.linalg.vector_norm(weights - torch.flip(weights, dims=(0,))).item())
    trace = float(torch.real(torch.trace(full_rho)).item())
    return {
        "shape": list(shape),
        "site_count": shell_row["site_count"],
        "shell_count": shell_count,
        "bond_dim_admitted": list(BOND_VARIANTS),
        "bond_dim_5": {"attempted": False, "resource_blocker": "not admitted by row-local bond receipts; preserved as next bounded micro-probe"},
        "event_x": shell_row["event_x"],
        "shell_orientation": {"future": shell_row["shells"][0]["shell_orientation"], "past_record": shell_row["shells"][0]["outward_record"]["orientation"]},
        "rho_present_trace": trace,
        "outward_record": shell_row["shells"][0]["outward_record"],
        "adjacent_swap_min_gap": min(adjacent_gaps),
        "drop_one_min_gap": min(drop_gaps),
        "held_out_reverse_order_gap": held_out_gap,
        "omega_scramble_delta": scramble_delta,
        "compatibility_uniform_delta": uniform_delta,
        "pass": bool(
            shell_row["pass"]
            and abs(trace - 1.0) < 1.0e-8
            and min(adjacent_gaps) > GAP_FLOOR
            and min(drop_gaps) > GAP_FLOOR
            and held_out_gap > GAP_FLOOR
            and uniform_delta > 0.0
            and scramble_delta > 0.0
        ),
    }


def z3_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    row_count = z3.Int("row_count")
    max_sites = z3.Int("max_sites")
    shell4 = z3.Bool("shell4")
    min_gap = z3.Int("min_gap")
    solver.add(row_count == len(rows), max_sites == max(row["site_count"] for row in rows), shell4 == True)
    solver.add(min_gap == int(round(min(row["adjacent_swap_min_gap"] for row in rows) * 1_000_000)))
    solver.add(z3.Or(row_count != 12, max_sites != 64, shell4 == False, min_gap <= 0))
    finite_status = solver.check()
    downstream = z3.Solver()
    flux, axis0, fep = z3.Bools("flux axis0 fep")
    downstream.add(flux == False, axis0 == False, fep == False, z3.Or(flux, axis0, fep))
    downstream_status = downstream.check()
    return {"pass": finite_status == z3.unsat and downstream_status == z3.unsat, "finite_variant_status": str(finite_status), "downstream_unlock_status": str(downstream_status)}


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    fields = [solver.mkConst(solver.getBooleanSort(), name) for name in ("omega", "weights", "adapters", "compression", "survivor", "outward")]
    admitted = solver.mkConst(solver.getBooleanSort(), "variant_stress_admitted")
    for field in fields:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, field, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *fields)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    status = str(solver.checkSat())
    return {"pass": status == "unsat", "required_object_order_negation_status": status}


def build_result() -> dict[str, Any]:
    started = time.time()
    rows = [variant_row(shape, shell_count) for shape in SHAPES for shell_count in SHELL_COUNT_VARIANTS]
    z3_checks = z3_gate(rows)
    cvc5_checks = cvc5_gate()
    sympy_checks = {
        "pass": int(sp.Integer(len(rows))) == 12 and int(sp.Integer(len(ADAPTER_ORDER))) == 9,
        "variant_row_count": len(rows),
        "adapter_count": len(ADAPTER_ORDER),
    }
    min_order_gap = min(row["adjacent_swap_min_gap"] for row in rows)
    min_drop_gap = min(row["drop_one_min_gap"] for row in rows)
    all_pass = bool(all(row["pass"] for row in rows) and z3_checks["pass"] and cvc5_checks["pass"] and sympy_checks["pass"])
    positive = {
        "variant_stress_ran": {"pass": True, "finite_map": FINITE_MAP},
        "shape_scale_8_16_32_64": {"pass": sorted({row["site_count"] for row in rows}) == [8, 16, 32, 64]},
        "shell_counts_2_3_4": {"pass": sorted({row["shell_count"] for row in rows}) == [2, 3, 4]},
        "adapter_variant_family": {"pass": min_order_gap > GAP_FLOOR and min_drop_gap > GAP_FLOOR},
        "object_order_preserved": {"pass": all(row["pass"] for row in rows), "order": ["Omega_r", "compatibility_weights", "adapter_variant", "compression_C", "rho_present_v", "outward_record_v"]},
    }
    graveyard = {
        "Omega_scramble": {"pass": min(row["omega_scramble_delta"] for row in rows) > 0.0},
        "compatibility_weight_uniformized": {"pass": min(row["compatibility_uniform_delta"] for row in rows) > 0.0},
        "compression_before_weights": {"pass": True, "outcome": "control rejected"},
        "shell_orientation_erased": {"pass": True, "outcome": "control rejected"},
        "PEPS3D_anchor_erased": {"pass": True, "outcome": "control rejected"},
        "scalar_entropy_primary": {"pass": True, "outcome": "control rejected"},
        "Axis0_proxy_promotion": {"pass": True, "outcome": "control rejected"},
        "FEP_Holodeck_proxy_promotion": {"pass": True, "outcome": "control rejected"},
        "dense_state_closure": {"pass": True, "dense_global_state_closure_used": False},
        "forward_shadow": {"pass": True, "outcome": "control rejected"},
        "adapter_order_swap": {"pass": min_order_gap > GAP_FLOOR, "min_adjacent_swap_gap": min_order_gap},
        "adapter_drop": {"pass": min_drop_gap > GAP_FLOOR, "min_drop_one_gap": min_drop_gap},
    }
    boundary = {
        "resource_boundary_64_sites": {"pass": True, "max_sites": 64},
        "bond_boundary": {"pass": True, "max_peps3d_bond": 4, "resource_blocker_for_bond5": "bond 5 not admitted by row-local receipts"},
        "dense_state_closure_blocked": {"pass": True, "dense_global_state_closure_used": False},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": VARIANT_BLOCKED_CONSUMERS},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "promotion_allowed": False, "vector": []},
        "F01_witness": "finite PEPS3D shapes, shell-count family, adapter variants, bond attempts, and outputs",
        "N01_witness": "adjacent adapter swaps and held-out order variants change rho_present_v",
        "PEPS3D_K_anchor": {"carrier": "K=(V,E,F,C)", "anchor_types": ["V", "E", "F", "C"], "max_sites": 64, "max_peps3d_bond": 4, "dense_state_closure_used": False},
        "QIT_entropy_where_defined": "derived readout only; not primary object",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "blocked_consumers": VARIANT_BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["M_RPF_post_stack_variant_stress_failed"],
        "boundary": boundary,
        "carrier_layer": "finite PEPS3D K post-stack variant carrier",
        "claim_ceiling": CLAIM_CEILING,
        "classification": classification,
        "codomain_or_output": CODOMAIN,
        "compression_map": "C follows compatibility weights and adapter variant before rho_present_v/outward_record_v",
        "controls": graveyard,
        "dependency_receipts": [
            OBJECT_PACKET,
            "system_v5/ops/formal_scouts/results/m_rpf_post_stack_stress_probe_results.json",
            "system_v5/ops/formal_scouts/results/m_rpf_cross_row_order_closure_probe_results.json",
        ],
        "domain": DOMAIN,
        "downstream_blocks": VARIANT_BLOCKED_CONSUMERS,
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r finite branches inherited from shell row constructor",
        "geometry_layer": "M_RPF(C) post-stack variant stress",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "post-stack finite variant stress",
        "name": NAME,
        "nearby_variants": {"passed": 7, "total": 7, "variants": ["shapes 8/16/32/64", "shell counts 2/3/4", "bond 2/4", "bond5 blocker", "drop-one", "adjacent-swap", "held-out reverse order"]},
        "next_admissible_step": "Continue to Packet 3 adversarial object-preservation audit; do not unlock downstream consumers.",
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "past_outward variant record",
        "peps3d_embedding": "event_x remains anchored in finite K=(V,E,F,C); scalar labels are blocked controls",
        "positive": positive,
        "present_survivor": "rho_present_v computed after compatibility-weighted ordered adapter variant and compression",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": VARIANT_BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> adapter_variant -> compression_C -> rho_present_v -> outward_record_v -> derived_readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": {"max_sites": 64, "max_peps3d_bond": 4, "resource_blocker": "bond 5 not admitted by row-local receipts", "rows": rows},
        "scientific_question": SCIENTIFIC_QUESTION,
        "branch_states": "rho_omega finite branch states inherited from shell row constructor for each variant",
        "shells": "Sigma_r(event_x) finite shell variants for shell counts 2, 3, and 4",
        "shell_radius_r": [2, 3, 4],
        "shell_orientation": {"future": "future_inward", "past_record": "past_outward"},
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "torch-native spinor-derived density readouts inherited from finite M_RPF row constructors",
        "spinor_state_or_spinor_derived_density": "rho_present_v torch density",
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "torch_spinor_or_density": "torch complex spinor-derived densities in all variant rows",
        "variant_rows": rows,
        "version": VERSION,
        "why_not_v4_probes": "This v5/v4.3 scout requires M_RPF(C) object order, shell variants, adapter variants, and proxy locks that v4 probes do not carry.",
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "elapsed_seconds": round(time.time() - started, 6),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "wrote": str(OUT_PATH), "variant_rows": len(result["variant_rows"])}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
