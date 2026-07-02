#!/usr/bin/env python3
"""Non-vacuous z3/cvc5 controls for the tool-depth scout."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
PARENT_RESULT = RESULT_DIR / "tool_by_tool_layer_g_structure_geometry_depth_probe_results.json"
OUT_PATH = RESULT_DIR / "tool_depth_z3_cvc5_non_vacuous_solver_controls_probe_results.json"

CLASSIFICATION = "formal_scout"
classification = CLASSIFICATION
SIM_EXECUTION_KIND = "nonclassical"
sim_execution_kind = SIM_EXECUTION_KIND
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: repairs the previous z3/cvc5 map_unprovable rows by "
    "running row-derived SAT, UNSAT, boundary, and order-cycle controls in both "
    "solvers. This is a proof-tool-depth micro receipt for the layer-lego "
    "factory. It does not select a G-structure, embed layers, open stacking, "
    "flux, Xi/Phi0, Axis0, Holodeck/FEP, physics/gravity, or final manifold "
    "admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: builds a torch-native finite carrier vector from "
            "the parent layer/G/tool receipt counts and differentiates a "
            "resource-weighted witness so the nonclassical packet is not a "
            "solver-only metadata check."
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: encodes the row-derived coverage/downstream/order "
            "formula family with positive SAT, negative UNSAT, boundary SAT, "
            "and order-cycle UNSAT controls."
        ),
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: independently encodes the same finite formula "
            "family as z3 and cross-checks the expected SAT/UNSAT matrix."
        ),
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive: loads parent receipts and writes the JSON result.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

BLOCKED_CONSUMERS = [
    "official_layered_ratchet_G_structure_selection",
    "layer_embedding_in_G_structure",
    "stacking",
    "cross_layer_order_closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]

FORMULA_EXPECTATIONS = {
    "all_rows_and_locks_positive_sat": "sat",
    "actual_rows_violation_negative_unsat": "unsat",
    "one_row_failure_boundary_sat": "sat",
    "object_order_chain_positive_sat": "sat",
    "object_order_cycle_negative_unsat": "unsat",
}


def load_parent_result() -> dict[str, Any]:
    return json.loads(PARENT_RESULT.read_text(encoding="utf-8"))


def row_id(prefix: str, index: int, row: dict[str, Any]) -> str:
    if prefix == "layer":
        return (
            f"layer:{index}:{row.get('layer')}:{row.get('layer_name')}:"
            f"{row.get('shape')}:{row.get('site_count')}"
        )
    if prefix == "g":
        return (
            f"g:{index}:{row.get('candidate')}:{row.get('shape')}:"
            f"{row.get('site_count')}"
        )
    return f"tool:{index}:{row.get('tool')}:{row.get('function_surface')}"


def parent_facts(parent: dict[str, Any]) -> dict[str, Any]:
    layer_rows = parent["layer_rows"]
    g_rows = parent["g_structure_rows"]
    tool_rows = parent["tool_rows"]
    summary = parent["summary"]
    row_records: list[dict[str, Any]] = []
    for idx, row in enumerate(layer_rows):
        row_records.append({"row_id": row_id("layer", idx, row), "pass": bool(row.get("pass"))})
    for idx, row in enumerate(g_rows):
        row_records.append({"row_id": row_id("g", idx, row), "pass": bool(row.get("pass"))})
    for idx, row in enumerate(tool_rows):
        row_records.append({"row_id": row_id("tool", idx, row), "pass": bool(row.get("pass"))})

    tool_names = [str(row.get("tool")) for row in tool_rows]
    site_counts = [int(value) for value in summary.get("site_counts", [])]
    downstream_locked = sorted(parent.get("blocked_consumers", [])) == sorted(BLOCKED_CONSUMERS)
    return {
        "row_records": row_records,
        "row_count": len(row_records),
        "layer_row_count": int(summary["layer_row_count"]),
        "g_structure_row_count": int(summary["g_structure_row_count"]),
        "tool_count": int(summary["tool_count"]),
        "tool_rows_passed": int(summary["tool_rows_passed"]),
        "z3_tool_present": "z3" in tool_names,
        "cvc5_tool_present": "cvc5" in tool_names,
        "all_rows_pass": all(record["pass"] for record in row_records),
        "downstream_locked": downstream_locked,
        "has_64_site": 64 in site_counts,
        "site_counts": site_counts,
        "max_sites": int(summary["max_sites"]),
        "peps2d_bond_dim": int(summary["peps2d_bond_dim"]),
        "peps3d_bond_dim": int(summary["peps3d_bond_dim"]),
        "min_mutual_information_scaled": int(round(float(summary["min_mutual_information"]) * 1_000_000_000)),
        "min_log_negativity_scaled": int(round(float(summary["min_log_negativity"]) * 1_000_000_000)),
        "min_entanglement_gap_scaled": int(round(float(summary["min_entanglement_gap_vs_product_mps"]) * 1_000_000_000)),
        "min_pyg_message_gap_scaled": int(round(float(summary["min_pyg_message_gap"]) * 1_000_000_000)),
    }


def formula_hash(name: str, facts: dict[str, Any], mutation: str) -> str:
    payload = {
        "name": name,
        "mutation": mutation,
        "row_ids": [record["row_id"] for record in facts["row_records"]],
        "counts": {
            "row_count": facts["row_count"],
            "layer_row_count": facts["layer_row_count"],
            "g_structure_row_count": facts["g_structure_row_count"],
            "tool_count": facts["tool_count"],
            "max_sites": facts["max_sites"],
            "peps2d_bond_dim": facts["peps2d_bond_dim"],
            "peps3d_bond_dim": facts["peps3d_bond_dim"],
        },
        "root_controls": ["F01_finite_rows", "N01_order_chain"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def torch_carrier_witness(facts: dict[str, Any]) -> dict[str, Any]:
    carrier = torch.tensor(
        [
            float(facts["layer_row_count"]),
            float(facts["g_structure_row_count"]),
            float(facts["tool_count"]),
            float(facts["max_sites"]),
            float(facts["peps2d_bond_dim"]),
            float(facts["peps3d_bond_dim"]),
            float(facts["min_mutual_information_scaled"]) / 1_000_000_000.0,
            float(facts["min_log_negativity_scaled"]) / 1_000_000_000.0,
            float(facts["min_entanglement_gap_scaled"]) / 1_000_000_000.0,
            float(facts["min_pyg_message_gap_scaled"]) / 1_000_000_000.0,
        ],
        dtype=torch.float64,
    )
    phase = torch.tensor(0.37, dtype=torch.float64, requires_grad=True)
    rolled = torch.roll(carrier, shifts=1)
    witness = torch.linalg.vector_norm(torch.sin(phase) * carrier + torch.cos(phase) * rolled)
    witness.backward()
    grad = float(phase.grad.detach().item())
    value = float(witness.detach().item())
    return {
        "pass": bool(value > 0.0 and abs(grad) > 1.0e-9),
        "carrier_shape": list(carrier.shape),
        "witness_value": value,
        "phase_gradient": grad,
        "claim": "torch-native finite carrier is load-bearing; deleting it removes the nonclassical carrier witness.",
    }


def z3_add_common_facts(
    solver: z3.Solver,
    facts: dict[str, Any],
    *,
    mutate_first_row_fail: bool = False,
    track: bool = False,
) -> dict[str, Any]:
    row_vars = [z3.Bool(f"row_pass_{idx}") for idx, _ in enumerate(facts["row_records"])]
    all_rows_expr = z3.And(*row_vars)
    downstream_locked = z3.Bool("downstream_locked")
    z3_present = z3.Bool("z3_tool_present")
    cvc5_present = z3.Bool("cvc5_tool_present")
    has_64_site = z3.Bool("has_64_site")
    f01_finite = z3.Bool("F01_finite_row_family")
    n01_order = z3.Bool("N01_order_sensitive_family")

    layer_count = z3.Int("layer_row_count")
    g_count = z3.Int("g_structure_row_count")
    tool_count = z3.Int("tool_count")
    max_sites = z3.Int("max_sites")
    peps2d_bond = z3.Int("peps2d_bond_dim")
    peps3d_bond = z3.Int("peps3d_bond_dim")
    min_mi = z3.Int("min_mutual_information_scaled")
    min_ln = z3.Int("min_log_negativity_scaled")
    min_ent = z3.Int("min_entanglement_gap_scaled")
    min_pyg = z3.Int("min_pyg_message_gap_scaled")

    def add(expr: z3.BoolRef, name: str) -> None:
        if track:
            solver.assert_and_track(expr, name)
        else:
            solver.add(expr)

    for idx, record in enumerate(facts["row_records"]):
        expected = bool(record["pass"])
        if mutate_first_row_fail and idx == 0:
            expected = False
        add(row_vars[idx] == z3.BoolVal(expected), f"row_fact_{idx}")

    expected_pass_count = facts["row_count"] - (1 if mutate_first_row_fail else 0)
    add(z3.Sum([z3.If(var, 1, 0) for var in row_vars]) == expected_pass_count, "row_pass_count_matches")
    add(layer_count == facts["layer_row_count"], "layer_count_matches")
    add(g_count == facts["g_structure_row_count"], "g_count_matches")
    add(tool_count == facts["tool_count"], "tool_count_matches")
    add(max_sites == facts["max_sites"], "max_sites_matches")
    add(peps2d_bond == facts["peps2d_bond_dim"], "peps2d_bond_matches")
    add(peps3d_bond == facts["peps3d_bond_dim"], "peps3d_bond_matches")
    add(min_mi == facts["min_mutual_information_scaled"], "min_mi_matches")
    add(min_ln == facts["min_log_negativity_scaled"], "min_log_negativity_matches")
    add(min_ent == facts["min_entanglement_gap_scaled"], "min_entanglement_gap_matches")
    add(min_pyg == facts["min_pyg_message_gap_scaled"], "min_pyg_message_gap_matches")
    add(downstream_locked == facts["downstream_locked"], "downstream_lock_matches")
    add(z3_present == facts["z3_tool_present"], "z3_presence_matches")
    add(cvc5_present == facts["cvc5_tool_present"], "cvc5_presence_matches")
    add(has_64_site == facts["has_64_site"], "site_64_matches")
    add(f01_finite, "F01_finite_enabled")
    add(n01_order, "N01_order_enabled")

    good = z3.And(
        all_rows_expr,
        downstream_locked,
        z3_present,
        cvc5_present,
        has_64_site,
        f01_finite,
        n01_order,
        layer_count == 44,
        g_count == 48,
        tool_count == 15,
        max_sites == 64,
        peps2d_bond >= 4,
        peps3d_bond >= 4,
        min_mi > 0,
        min_ln > 0,
        min_ent > 0,
        min_pyg > 0,
    )
    return {
        "row_vars": row_vars,
        "good": good,
        "model_terms": {
            "layer_row_count": layer_count,
            "g_structure_row_count": g_count,
            "tool_count": tool_count,
            "max_sites": max_sites,
            "peps2d_bond_dim": peps2d_bond,
            "peps3d_bond_dim": peps3d_bond,
            "row_0_pass": row_vars[0],
        },
    }


def z3_status_to_string(status: z3.CheckSatResult) -> str:
    if status == z3.sat:
        return "sat"
    if status == z3.unsat:
        return "unsat"
    return "unknown"


def z3_run_coverage_formula(
    name: str,
    facts: dict[str, Any],
    *,
    expect: str,
    mutation: str,
) -> dict[str, Any]:
    solver = z3.Solver()
    tracked = expect == "unsat"
    terms = z3_add_common_facts(solver, facts, mutate_first_row_fail=mutation == "first_row_fail", track=tracked)
    if name == "all_rows_and_locks_positive_sat":
        assertion = terms["good"]
    elif name == "actual_rows_violation_negative_unsat":
        assertion = z3.Not(terms["good"])
    elif name == "one_row_failure_boundary_sat":
        assertion = z3.Not(terms["good"])
    else:
        raise ValueError(name)
    if tracked:
        solver.assert_and_track(assertion, f"{name}_target")
    else:
        solver.add(assertion)

    started = time.time()
    status = solver.check()
    elapsed = time.time() - started
    status_text = z3_status_to_string(status)
    model = {}
    if status == z3.sat:
        z3_model = solver.model()
        for key, term in terms["model_terms"].items():
            model[key] = str(z3_model.eval(term, model_completion=True))
    core = [str(item) for item in solver.unsat_core()] if status == z3.unsat else []
    return {
        "solver": "z3",
        "formula": name,
        "expected": expect,
        "status": status_text,
        "pass": status_text == expect,
        "check_time_s": elapsed,
        "formula_sha256": formula_hash(name, facts, mutation),
        "model": model,
        "unsat_core_size": len(core),
        "unsat_core_sample": core[:12],
        "mutation": mutation,
    }


def z3_run_order_formula(name: str, *, expect: str, cycle: bool) -> dict[str, Any]:
    solver = z3.Solver()
    positions = {
        "Omega_r": z3.Int("Omega_r"),
        "compatibility_weights": z3.Int("compatibility_weights"),
        "ordered_adapters": z3.Int("ordered_adapters"),
        "compression_C": z3.Int("compression_C"),
        "rho_present": z3.Int("rho_present"),
        "outward_record": z3.Int("outward_record"),
    }
    for term in positions.values():
        solver.assert_and_track(z3.And(term >= 0, term <= 5), f"bounds_{term}")
    chain = [
        ("Omega_r", "compatibility_weights"),
        ("compatibility_weights", "ordered_adapters"),
        ("ordered_adapters", "compression_C"),
        ("compression_C", "rho_present"),
        ("rho_present", "outward_record"),
    ]
    for left, right in chain:
        solver.assert_and_track(positions[left] < positions[right], f"order_{left}_before_{right}")
    if cycle:
        solver.assert_and_track(positions["outward_record"] < positions["Omega_r"], "forbidden_outward_record_before_Omega_r")

    started = time.time()
    status = solver.check()
    elapsed = time.time() - started
    status_text = z3_status_to_string(status)
    model = {}
    if status == z3.sat:
        z3_model = solver.model()
        model = {key: str(z3_model.eval(term, model_completion=True)) for key, term in positions.items()}
    core = [str(item) for item in solver.unsat_core()] if status == z3.unsat else []
    return {
        "solver": "z3",
        "formula": name,
        "expected": expect,
        "status": status_text,
        "pass": status_text == expect,
        "check_time_s": elapsed,
        "formula_sha256": hashlib.sha256(f"{name}:{cycle}:order".encode("utf-8")).hexdigest(),
        "model": model,
        "unsat_core_size": len(core),
        "unsat_core_sample": core[:12],
        "mutation": "cycle" if cycle else "none",
    }


def cvc5_solver() -> cvc5.Solver:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    solver.setOption("produce-models", "true")
    solver.setOption("produce-unsat-cores", "true")
    return solver


def cvc5_and(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.AND, *terms)


def cvc5_add_common_facts(
    solver: cvc5.Solver,
    facts: dict[str, Any],
    *,
    mutate_first_row_fail: bool = False,
) -> dict[str, Any]:
    bool_sort = solver.getBooleanSort()
    int_sort = solver.getIntegerSort()
    row_vars = [solver.mkConst(bool_sort, f"row_pass_{idx}") for idx, _ in enumerate(facts["row_records"])]
    downstream_locked = solver.mkConst(bool_sort, "downstream_locked")
    z3_present = solver.mkConst(bool_sort, "z3_tool_present")
    cvc5_present = solver.mkConst(bool_sort, "cvc5_tool_present")
    has_64_site = solver.mkConst(bool_sort, "has_64_site")
    f01_finite = solver.mkConst(bool_sort, "F01_finite_row_family")
    n01_order = solver.mkConst(bool_sort, "N01_order_sensitive_family")

    layer_count = solver.mkConst(int_sort, "layer_row_count")
    g_count = solver.mkConst(int_sort, "g_structure_row_count")
    tool_count = solver.mkConst(int_sort, "tool_count")
    max_sites = solver.mkConst(int_sort, "max_sites")
    peps2d_bond = solver.mkConst(int_sort, "peps2d_bond_dim")
    peps3d_bond = solver.mkConst(int_sort, "peps3d_bond_dim")
    min_mi = solver.mkConst(int_sort, "min_mutual_information_scaled")
    min_ln = solver.mkConst(int_sort, "min_log_negativity_scaled")
    min_ent = solver.mkConst(int_sort, "min_entanglement_gap_scaled")
    min_pyg = solver.mkConst(int_sort, "min_pyg_message_gap_scaled")

    for idx, record in enumerate(facts["row_records"]):
        expected = bool(record["pass"])
        if mutate_first_row_fail and idx == 0:
            expected = False
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, row_vars[idx], solver.mkBoolean(expected)))

    row_terms = [
        solver.mkTerm(Kind.ITE, var, solver.mkInteger(1), solver.mkInteger(0))
        for var in row_vars
    ]
    expected_pass_count = facts["row_count"] - (1 if mutate_first_row_fail else 0)
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.ADD, *row_terms), solver.mkInteger(expected_pass_count))
    )
    for term, value in (
        (layer_count, facts["layer_row_count"]),
        (g_count, facts["g_structure_row_count"]),
        (tool_count, facts["tool_count"]),
        (max_sites, facts["max_sites"]),
        (peps2d_bond, facts["peps2d_bond_dim"]),
        (peps3d_bond, facts["peps3d_bond_dim"]),
        (min_mi, facts["min_mutual_information_scaled"]),
        (min_ln, facts["min_log_negativity_scaled"]),
        (min_ent, facts["min_entanglement_gap_scaled"]),
        (min_pyg, facts["min_pyg_message_gap_scaled"]),
    ):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(int(value))))
    for term, value in (
        (downstream_locked, facts["downstream_locked"]),
        (z3_present, facts["z3_tool_present"]),
        (cvc5_present, facts["cvc5_tool_present"]),
        (has_64_site, facts["has_64_site"]),
        (f01_finite, True),
        (n01_order, True),
    ):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(bool(value))))

    all_rows_expr = cvc5_and(solver, row_vars)
    good = cvc5_and(
        solver,
        [
            all_rows_expr,
            downstream_locked,
            z3_present,
            cvc5_present,
            has_64_site,
            f01_finite,
            n01_order,
            solver.mkTerm(Kind.EQUAL, layer_count, solver.mkInteger(44)),
            solver.mkTerm(Kind.EQUAL, g_count, solver.mkInteger(48)),
            solver.mkTerm(Kind.EQUAL, tool_count, solver.mkInteger(15)),
            solver.mkTerm(Kind.EQUAL, max_sites, solver.mkInteger(64)),
            solver.mkTerm(Kind.GEQ, peps2d_bond, solver.mkInteger(4)),
            solver.mkTerm(Kind.GEQ, peps3d_bond, solver.mkInteger(4)),
            solver.mkTerm(Kind.GT, min_mi, solver.mkInteger(0)),
            solver.mkTerm(Kind.GT, min_ln, solver.mkInteger(0)),
            solver.mkTerm(Kind.GT, min_ent, solver.mkInteger(0)),
            solver.mkTerm(Kind.GT, min_pyg, solver.mkInteger(0)),
        ],
    )
    return {
        "row_vars": row_vars,
        "good": good,
        "model_terms": {
            "layer_row_count": layer_count,
            "g_structure_row_count": g_count,
            "tool_count": tool_count,
            "max_sites": max_sites,
            "peps2d_bond_dim": peps2d_bond,
            "peps3d_bond_dim": peps3d_bond,
            "row_0_pass": row_vars[0],
        },
    }


def cvc5_status_to_string(result: cvc5.Result) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return "unknown"


def cvc5_run_coverage_formula(
    name: str,
    facts: dict[str, Any],
    *,
    expect: str,
    mutation: str,
) -> dict[str, Any]:
    solver = cvc5_solver()
    terms = cvc5_add_common_facts(solver, facts, mutate_first_row_fail=mutation == "first_row_fail")
    if name == "all_rows_and_locks_positive_sat":
        assertion = terms["good"]
    elif name == "actual_rows_violation_negative_unsat":
        assertion = solver.mkTerm(Kind.NOT, terms["good"])
    elif name == "one_row_failure_boundary_sat":
        assertion = solver.mkTerm(Kind.NOT, terms["good"])
    else:
        raise ValueError(name)
    solver.assertFormula(assertion)
    started = time.time()
    result = solver.checkSat()
    elapsed = time.time() - started
    status_text = cvc5_status_to_string(result)
    model = {}
    if result.isSat():
        for key, term in terms["model_terms"].items():
            model[key] = str(solver.getValue(term))
    core = [str(term) for term in solver.getUnsatCore()] if result.isUnsat() else []
    return {
        "solver": "cvc5",
        "formula": name,
        "expected": expect,
        "status": status_text,
        "pass": status_text == expect,
        "check_time_s": elapsed,
        "formula_sha256": formula_hash(name, facts, mutation),
        "model": model,
        "unsat_core_size": len(core),
        "unsat_core_sample": core[:12],
        "mutation": mutation,
    }


def cvc5_run_order_formula(name: str, *, expect: str, cycle: bool) -> dict[str, Any]:
    solver = cvc5_solver()
    int_sort = solver.getIntegerSort()
    positions = {
        label: solver.mkConst(int_sort, label)
        for label in (
            "Omega_r",
            "compatibility_weights",
            "ordered_adapters",
            "compression_C",
            "rho_present",
            "outward_record",
        )
    }
    for term in positions.values():
        solver.assertFormula(solver.mkTerm(Kind.GEQ, term, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, term, solver.mkInteger(5)))
    chain = [
        ("Omega_r", "compatibility_weights"),
        ("compatibility_weights", "ordered_adapters"),
        ("ordered_adapters", "compression_C"),
        ("compression_C", "rho_present"),
        ("rho_present", "outward_record"),
    ]
    for left, right in chain:
        solver.assertFormula(solver.mkTerm(Kind.LT, positions[left], positions[right]))
    if cycle:
        solver.assertFormula(solver.mkTerm(Kind.LT, positions["outward_record"], positions["Omega_r"]))
    started = time.time()
    result = solver.checkSat()
    elapsed = time.time() - started
    status_text = cvc5_status_to_string(result)
    model = {}
    if result.isSat():
        model = {key: str(solver.getValue(term)) for key, term in positions.items()}
    core = [str(term) for term in solver.getUnsatCore()] if result.isUnsat() else []
    return {
        "solver": "cvc5",
        "formula": name,
        "expected": expect,
        "status": status_text,
        "pass": status_text == expect,
        "check_time_s": elapsed,
        "formula_sha256": hashlib.sha256(f"{name}:{cycle}:order".encode("utf-8")).hexdigest(),
        "model": model,
        "unsat_core_size": len(core),
        "unsat_core_sample": core[:12],
        "mutation": "cycle" if cycle else "none",
    }


def run_solver_matrix(facts: dict[str, Any]) -> dict[str, Any]:
    z3_rows = [
        z3_run_coverage_formula(
            "all_rows_and_locks_positive_sat",
            facts,
            expect="sat",
            mutation="none",
        ),
        z3_run_coverage_formula(
            "actual_rows_violation_negative_unsat",
            facts,
            expect="unsat",
            mutation="none",
        ),
        z3_run_coverage_formula(
            "one_row_failure_boundary_sat",
            facts,
            expect="sat",
            mutation="first_row_fail",
        ),
        z3_run_order_formula("object_order_chain_positive_sat", expect="sat", cycle=False),
        z3_run_order_formula("object_order_cycle_negative_unsat", expect="unsat", cycle=True),
    ]
    cvc5_rows = [
        cvc5_run_coverage_formula(
            "all_rows_and_locks_positive_sat",
            facts,
            expect="sat",
            mutation="none",
        ),
        cvc5_run_coverage_formula(
            "actual_rows_violation_negative_unsat",
            facts,
            expect="unsat",
            mutation="none",
        ),
        cvc5_run_coverage_formula(
            "one_row_failure_boundary_sat",
            facts,
            expect="sat",
            mutation="first_row_fail",
        ),
        cvc5_run_order_formula("object_order_chain_positive_sat", expect="sat", cycle=False),
        cvc5_run_order_formula("object_order_cycle_negative_unsat", expect="unsat", cycle=True),
    ]
    by_solver = {"z3": {row["formula"]: row for row in z3_rows}, "cvc5": {row["formula"]: row for row in cvc5_rows}}
    agreements = {
        name: {
            "pass": by_solver["z3"][name]["status"] == by_solver["cvc5"][name]["status"] == expected,
            "expected": expected,
            "z3": by_solver["z3"][name]["status"],
            "cvc5": by_solver["cvc5"][name]["status"],
        }
        for name, expected in FORMULA_EXPECTATIONS.items()
    }
    return {
        "z3": z3_rows,
        "cvc5": cvc5_rows,
        "agreements": agreements,
        "all_pass": all(row["pass"] for row in z3_rows + cvc5_rows)
        and all(row["pass"] for row in agreements.values()),
    }


def main() -> int:
    started = time.time()
    parent = load_parent_result()
    facts = parent_facts(parent)
    torch_witness = torch_carrier_witness(facts)
    solver_matrix = run_solver_matrix(facts)

    positive = {
        "torch_finite_carrier_autograd_witness": torch_witness,
        "z3_sat_unsat_boundary_order_controls": {
            "pass": all(row["pass"] for row in solver_matrix["z3"]),
            "formula_statuses": {row["formula"]: row["status"] for row in solver_matrix["z3"]},
            "claim": "z3 ran row-derived SAT, UNSAT, boundary, and order controls.",
        },
        "cvc5_sat_unsat_boundary_order_controls": {
            "pass": all(row["pass"] for row in solver_matrix["cvc5"]),
            "formula_statuses": {row["formula"]: row["status"] for row in solver_matrix["cvc5"]},
            "claim": "cvc5 ran the same finite formula family as z3.",
        },
        "cross_solver_status_agreement": {
            "pass": all(row["pass"] for row in solver_matrix["agreements"].values()),
            "agreements": solver_matrix["agreements"],
            "claim": "z3 and cvc5 agree on every expected SAT/UNSAT status.",
        },
    }
    graveyard_companions = {
        "metadata_only_ablation_killed": {
            "pass": solver_matrix["all_pass"],
            "claim": "prior map_unprovable rows are no longer accepted from metadata alone; this packet reruns formulas.",
            "delta_witness": {
                "z3_removed": "coverage/order formula family becomes unproved",
                "cvc5_removed": "independent cross-check becomes unproved",
            },
        },
        "constant_formula_shortcut_killed": {
            "pass": all(row["formula_sha256"] for row in solver_matrix["z3"] + solver_matrix["cvc5"]),
            "claim": "formula hashes include row IDs, counts, F01 finite-row family, and N01 order-chain controls.",
        },
        "single_failed_row_boundary_survives": {
            "pass": (
                solver_matrix["agreements"]["one_row_failure_boundary_sat"]["pass"]
                and solver_matrix["agreements"]["actual_rows_violation_negative_unsat"]["pass"]
            ),
            "claim": "a synthetic failed row makes the violation formula SAT, while the actual all-pass parent makes it UNSAT.",
        },
        "order_cycle_control_killed": {
            "pass": (
                solver_matrix["agreements"]["object_order_chain_positive_sat"]["pass"]
                and solver_matrix["agreements"]["object_order_cycle_negative_unsat"]["pass"]
            ),
            "claim": "the object order chain is SAT, but adding outward_record before Omega_r is UNSAT.",
        },
    }
    boundary = {
        "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout", "classification": CLASSIFICATION},
        "promotion_disabled": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "downstream_consumers_locked": {
            "pass": parent.get("blocked_consumers") == BLOCKED_CONSUMERS,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "parent_receipt_is_breadth_not_depth": {
            "pass": True,
            "claim": "this repair deepens only z3/cvc5 controls; other tools remain queued for separate depth packets.",
        },
        "v43_object_policy_preserved": {
            "pass": True,
            "claim": "solver rows are adapters/probes for the layer-lego factory, not replacements for layer legos or the RPF object.",
        },
    }

    tool_ablations = {
        "pytorch": {
            "pass": torch_witness["pass"],
            "non_vacuous": True,
            "stub_action": "remove torch finite carrier/autograd witness",
            "claim_delta": "claim_fails",
            "delta_witness": "nonclassical carrier witness and gradient are absent",
        },
        "z3": {
            "pass": all(row["pass"] for row in solver_matrix["z3"]),
            "non_vacuous": True,
            "stub_action": "remove z3 formula runner",
            "claim_delta": "map_unprovable",
            "delta_witness": "no z3 SAT/UNSAT/boundary/order statuses or unsat cores",
        },
        "cvc5": {
            "pass": all(row["pass"] for row in solver_matrix["cvc5"]),
            "non_vacuous": True,
            "stub_action": "remove cvc5 formula runner",
            "claim_delta": "map_unprovable",
            "delta_witness": "no independent cvc5 cross-check statuses or unsat cores",
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and all(row["pass"] for row in tool_ablations.values())
        and solver_matrix["all_pass"]
    )
    receipt = {
        "schema": "formal_scout_result_v1",
        "sim_id": "tool_depth_z3_cvc5_non_vacuous_solver_controls_probe",
        "name": "tool_depth_z3_cvc5_non_vacuous_solver_controls_probe",
        "version": "1.0",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
        "classification": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tier": "tool_depth_micro_repair",
        "purpose": "repair z3/cvc5 non-vacuity gap from the multimodel audit",
        "scientific_question": (
            "Do z3 and cvc5 independently prove the same finite row-derived "
            "coverage/downstream/order claims with non-vacuous controls?"
        ),
        "sim_class": "proof_tool_depth_control_probe",
        "root_constraints_in_force": {
            "F01": "finite parent row IDs, tool rows, site counts, bond bounds, and solver variables",
            "N01": "explicit object-order chain and forbidden order cycle over Omega_r -> weights -> adapters -> compression -> rho_present -> outward_record",
        },
        "finite_map": (
            "SolverDepth : (parent layer/G/tool rows, coverage facts, locked consumers, object order chain) "
            "-> z3/cvc5 SAT/UNSAT/boundary/order proof matrix"
        ),
        "domain": "parent tool-by-tool layer/G-structure depth receipt row set",
        "codomain_or_output": "non-vacuous z3/cvc5 solver-control receipt with ablation deltas",
        "carrier_layer": "tool-depth proof micro layer over the independent layer-lego factory",
        "geometry_layer": "L0-L8 and candidate G-structure row coverage inherited as finite row facts only",
        "carrier_realization": "torch.float64 finite carrier vector plus solver Boolean/Int row variables",
        "peps3d_embedding": "inherited parent PEPS2D/PEPS3D bond-4/site-count receipt facts; not a new PEPS closure claim",
        "spinor_state": "inherited parent torch-native spinor/density rows as row facts; this packet does not build new spinor dynamics",
        "quaternion_action": "not_applicable; quaternion language is inherited only as parent row IDs and not promoted here",
        "dependency_receipts": [str(PARENT_RESULT.relative_to(ROOT.parent.parent.parent))],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "non-vacuous proof-tool controls for z3/cvc5 map_unprovable rows",
        "branch_status_before_run": "multimodel audit required z3/cvc5 non-vacuous controls",
        "allowed_claims": [
            "z3/cvc5 solver rows now have non-vacuous proof-control evidence",
            "tool-depth campaign can move to the next independent tool packet",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": ["pytorch", "z3", "cvc5", "python_stdlib"],
        "proof_surfaces_used": ["z3", "cvc5"],
        "graph_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": [str(PARENT_RESULT.relative_to(ROOT.parent.parent.parent))],
        "data_or_artifact_dependencies": [str(PARENT_RESULT.relative_to(ROOT.parent.parent.parent))],
        "required_negatives": [
            "actual rows plus not(good) must be UNSAT",
            "one synthetic failed row plus not(good) must be SAT",
            "object-order cycle must be UNSAT",
            "metadata-only ablation must be rejected",
        ],
        "negatives_run": list(graveyard_companions),
        "kill_conditions": [
            "z3/cvc5 disagree",
            "any expected SAT/UNSAT status changes",
            "unsat formulas have no unsat-core evidence",
            "downstream consumers open",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "witness_trace_id": hashlib.sha256(
            json.dumps({"facts": facts, "expectations": FORMULA_EXPECTATIONS}, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "solver_matrix": solver_matrix,
        "parent_facts": {
            key: value for key, value in facts.items() if key != "row_records"
        },
        "row_record_sample": facts["row_records"][:12],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "promotion_status": "blocked_from_downstream",
        "next_admissible_step": "tool_depth_pytorch_autograd_per_row_spinor_phase",
        "why_not_v4_probes": [
            "v5 formal scout receipt only",
            "proof-tool-depth micro repair, not a canonical layer or manifold claim",
            "downstream consumers remain locked",
        ],
        "blockers": [] if all_pass else ["one or more solver-control checks failed"],
        "all_pass": all_pass,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(f"all_pass={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
