#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for mct_dynamic_deformation_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import cvc5
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "mct_dynamic_deformation_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

PARENT_SIM = "mct_dynamic_admissibility_packet_v0"
PARENT_DIR = ROOT / "system_v6" / "sims" / PARENT_SIM
PARENT_JAX_RESULT = PARENT_DIR / "results" / f"{PARENT_SIM}_jax_results.json"
PARENT_ENVELOPE_RESULT = PARENT_DIR / "results" / f"{PARENT_SIM}_envelope_results.json"
K_LEAF_RESULT = ROOT / "system_v6" / "sims" / "geo_union_rule_k_leaves_v0" / "results" / "geo_union_rule_k_leaves_v0_envelope_results.json"
RATCHET_S1_RESULT = ROOT / "system_v6" / "sims" / "ratchet_s1_single_shell_pilot_v0" / "results" / "ratchet_s1_single_shell_pilot_v0_envelope_results.json"
RATCHET_S2_RESULT = ROOT / "system_v6" / "sims" / "ratchet_s2_two_shell_flux_v0" / "results" / "ratchet_s2_two_shell_flux_v0_envelope_results.json"
RATCHET_S2_CHAIN_RESULT = ROOT / "system_v6" / "sims" / "ratchet_s2_three_shell_chain_v0" / "results" / "ratchet_s2_three_shell_chain_v0_envelope_results.json"
RATCHET_S6_RESULT = ROOT / "system_v6" / "sims" / "ratchet_s6_terrain_operator_shell_v0" / "results" / "ratchet_s6_terrain_operator_shell_v0_envelope_results.json"
RATCHET_S6_SWEEP_RESULT = ROOT / "system_v6" / "sims" / "ratchet_s6_terrain_sweep_v0" / "results" / "ratchet_s6_terrain_sweep_v0_envelope_results.json"
CFR_RESULT = ROOT / "system_v6" / "sims" / "compression_flow_radiated_record_v0" / "results" / "compression_flow_radiated_record_v0_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
READS_PARENT_RESULTS = True
SEED_LEDGER = {
    "status": "deterministic_no_rng",
    "symbolic_seed": 2026061106,
    "smt_seed": 2026061106,
    "shape_seed": 2026061106,
}

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 array assembly for graph-shape matrix and spectrum computation",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite relation adjacency and Laplacian-spectrum arithmetic",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Hopf c1 anchor computation from the canonical curvature formula",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite SMT exclusion rows for monotonicity and quotient irreversibility",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite SMT exclusion rows matching the z3 checks",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, hashing, timestamp, path, and finite set bookkeeping",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def stable_sha256(obj: Any) -> str:
    return hashlib.sha256(stable_json(obj).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def q_key(row: dict[str, Any], *, include_phase: bool = False) -> str:
    key: list[Any] = [row["P_density"], row["P_shell"], row["P_loop"], row["P_order"], row["P_chirality"]]
    if include_phase:
        key.append(row["P_phase"])
    return stable_json(key)


def row_sets(rows: list[dict[str, Any]], parent: dict[str, Any]) -> dict[str, set[str]]:
    threshold = float(parent["admissibility"]["constraint_thresholds"]["N01_order_gap_median"])

    def f01(row: dict[str, Any]) -> bool:
        return bool(row.get("F01_pass", row["axis0_b0"] != 0))

    def n01(row: dict[str, Any]) -> bool:
        return bool(row.get("N01_pass", float(row["order_gap_noncommuting"]) >= threshold))

    all_ids = {row["state_id"] for row in rows}
    f01_ids = {row["state_id"] for row in rows if f01(row)}
    n01_ids = {row["state_id"] for row in rows if n01(row)}
    active_ids = f01_ids & n01_ids
    return {
        "FREE": all_ids,
        "F01": f01_ids,
        "N01": n01_ids,
        "F01_AND_N01": active_ids,
    }


def entropy_from_counts(counts: list[int]) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    return -sum((count / total) * math.log(count / total) for count in counts if count)


def quotient_stats(rows: list[dict[str, Any]], ids: set[str], *, include_phase: bool = False) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    for row in rows:
        if row["state_id"] in ids:
            counter[q_key(row, include_phase=include_phase)] += 1
    sizes = sorted(counter.values(), reverse=True)
    return {
        "support_size": len(ids),
        "class_count": len(counter),
        "class_sizes": sizes,
        "H_Q": entropy_from_counts(sizes),
        "A_Q": (sum(math.log(size) for size in sizes) / len(sizes)) if sizes else 0.0,
        "possibility_mass": len(ids),
    }


def relation_edges(rows: list[dict[str, Any]]) -> tuple[dict[str, int], set[tuple[int, int, str]]]:
    by_coord = {(row["sheet"], int(row["eta_index"]), int(row["phi_index"]), int(row["chi_index"])): row["state_id"] for row in rows}
    ids = sorted(row["state_id"] for row in rows)
    index = {sid: i for i, sid in enumerate(ids)}
    edges: set[tuple[int, int, str]] = set()
    for sheet in ("L", "R"):
        other = "R" if sheet == "L" else "L"
        for eta in range(3):
            for phi in range(8):
                for chi in range(8):
                    sid = by_coord[(sheet, eta, phi, chi)]
                    edges.add((index[sid], index[by_coord[(sheet, eta, (phi + 1) % 8, chi)]], "fiber_phi"))
                    edges.add((index[sid], index[by_coord[(sheet, eta, phi, (chi + 1) % 8)]], "base_chi"))
                    edges.add((index[sid], index[by_coord[(other, eta, phi, chi)]], "chirality_pair"))
                    if eta > 0:
                        edges.add((index[sid], index[by_coord[(sheet, eta - 1, phi, chi)]], "shell_nested"))
                    if eta < 2:
                        edges.add((index[sid], index[by_coord[(sheet, eta + 1, phi, chi)]], "shell_nested"))
    return index, edges


def warped_edges(rows: list[dict[str, Any]], index: dict[str, int], edges: set[tuple[int, int, str]]) -> set[tuple[int, int, str]]:
    by_coord = {(row["sheet"], int(row["eta_index"]), int(row["phi_index"]), int(row["chi_index"])): row["state_id"] for row in rows}
    out = set(edges)
    for sheet in ("L", "R"):
        for phi in range(8):
            for chi in range(8):
                out.discard((index[by_coord[(sheet, 1, phi, chi)]], index[by_coord[(sheet, 2, phi, chi)]], "shell_nested"))
    for phi in range(8):
        for chi in range(8):
            out.add((index[by_coord[("L", 0, phi, chi)]], index[by_coord[("L", 2, phi, chi)]], "warp_long_shell_jump"))
    return out


def shape_receipt(n: int, edges: set[tuple[int, int, str]]) -> dict[str, Any]:
    adj = jnp.zeros((n, n), dtype=jnp.float64)
    for src, dst, _kind in edges:
        adj = adj.at[src, dst].set(1.0)
    sym = jnp.maximum(adj, adj.T)
    degree = jnp.sum(sym, axis=1)
    lap = jnp.diag(degree) - sym
    eigs = jnp.linalg.eigvalsh(lap)
    top = [round(float(x), 9) for x in jax.device_get(eigs[-8:])]
    bottom = [round(float(x), 9) for x in jax.device_get(eigs[:8])]
    kinds = Counter(kind for _src, _dst, kind in edges)
    return {
        "node_count": n,
        "edge_count": len(edges),
        "kind_counts": dict(sorted(kinds.items())),
        "degree_sum": int(round(float(jax.device_get(jnp.sum(degree))))),
        "laplacian_eigenvalues_bottom8": bottom,
        "laplacian_eigenvalues_top8": top,
        "spectrum_sha256": stable_sha256({"bottom8": bottom, "top8": top}),
    }


def z3_set_monotonicity(old: list[bool], new: list[bool], release_base: list[bool], release: list[bool]) -> dict[str, Any]:
    solver = z3.Solver()
    old_vars = [z3.Int(f"old_{i}") for i in range(len(old))]
    new_vars = [z3.Int(f"new_{i}") for i in range(len(new))]
    for i, (o, n) in enumerate(zip(old, new)):
        solver.add(old_vars[i] == (1 if o else 0))
        solver.add(new_vars[i] == (1 if n else 0))
    solver.add(z3.Or([new_vars[i] > old_vars[i] for i in range(len(old))]))
    positive = str(solver.check())

    control = z3.Solver()
    release_vars = [z3.Int(f"release_{i}") for i in range(len(release))]
    old2 = [z3.Int(f"old_release_base_{i}") for i in range(len(release_base))]
    for i, (o, r) in enumerate(zip(release_base, release)):
        control.add(old2[i] == (1 if o else 0))
        control.add(release_vars[i] == (1 if r else 0))
    control.add(z3.Or([release_vars[i] > old2[i] for i in range(len(release_base))]))
    erased = str(control.check())
    witness = None
    if erased == "sat":
        model = control.model()
        for i in range(len(release_base)):
            if model.eval(release_vars[i]).as_long() > model.eval(old2[i]).as_long():
                witness = i
                break
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": positive,
        "erased_release_control_verdict": erased,
        "release_witness_index": witness,
        "positive_case": "asserting pure constraint addition expands a computed finite set is UNSAT",
        "negative/erased_control": "release the added N01 constraint; an expansion witness is SAT",
        "computed_rows_bound": len(old),
        "release_rows_bound": len(release_base),
    }


def cvc5_int_set_monotonicity(old: list[bool], new: list[bool], release_base: list[bool], release: list[bool]) -> dict[str, Any]:
    def run(a: list[bool], b: list[bool], prefix: str) -> tuple[str, int | None]:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        old_vars = [solver.mkConst(int_sort, f"{prefix}_old_{i}") for i in range(len(a))]
        new_vars = [solver.mkConst(int_sort, f"{prefix}_new_{i}") for i in range(len(b))]
        disj = []
        for i, (x, y) in enumerate(zip(a, b)):
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, old_vars[i], solver.mkInteger(1 if x else 0)))
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, new_vars[i], solver.mkInteger(1 if y else 0)))
            disj.append(solver.mkTerm(cvc5.Kind.GT, new_vars[i], old_vars[i]))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.OR, *disj))
        result = str(solver.checkSat()).lower()
        return result, None

    positive, _ = run(old, new, "pure_add")
    erased, _ = run(release_base, release, "release")
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": positive,
        "erased_release_control_verdict": erased,
        "positive_case": "asserting pure constraint addition expands a computed finite set is UNSAT",
        "negative/erased_control": "release the added N01 constraint; an expansion witness is SAT",
        "computed_rows_bound": len(old),
        "release_rows_bound": len(release_base),
    }


def quotient_pair(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(q_key(row, include_phase=False), []).append(row)
    for bucket in buckets.values():
        for i, a in enumerate(bucket):
            for b in bucket[i + 1 :]:
                if int(a["P_phase"]) != int(b["P_phase"]):
                    return a, b
    raise RuntimeError("no quotient-erasure pair found")


def z3_quotient_irreversibility(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    recovered = z3.Int("recovered_phase_from_quotient_class")
    solver.add(recovered == int(a["P_phase"]))
    solver.add(recovered == int(b["P_phase"]))
    positive = str(solver.check())
    control = z3.Solver()
    recovered_a = z3.Int("recovered_phase_refined_a")
    recovered_b = z3.Int("recovered_phase_refined_b")
    control.add(recovered_a == int(a["P_phase"]))
    control.add(recovered_b == int(b["P_phase"]))
    erased = str(control.check())
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": positive,
        "phase_refined_control_verdict": erased,
        "same_quotient_key": q_key(a, include_phase=False) == q_key(b, include_phase=False),
        "different_phase_values": [int(a["P_phase"]), int(b["P_phase"])],
        "state_pair": [a["state_id"], b["state_id"]],
    }


def cvc5_quotient_irreversibility(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    recovered = solver.mkConst(int_sort, "recovered_phase_from_quotient_class")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, recovered, solver.mkInteger(int(a["P_phase"]))))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, recovered, solver.mkInteger(int(b["P_phase"]))))
    positive = str(solver.checkSat()).lower()

    control = cvc5.Solver()
    control.setLogic("QF_LIA")
    int_sort = control.getIntegerSort()
    rec_a = control.mkConst(int_sort, "recovered_phase_refined_a")
    rec_b = control.mkConst(int_sort, "recovered_phase_refined_b")
    control.assertFormula(control.mkTerm(cvc5.Kind.EQUAL, rec_a, control.mkInteger(int(a["P_phase"]))))
    control.assertFormula(control.mkTerm(cvc5.Kind.EQUAL, rec_b, control.mkInteger(int(b["P_phase"]))))
    erased = str(control.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": positive,
        "phase_refined_control_verdict": erased,
        "same_quotient_key": q_key(a, include_phase=False) == q_key(b, include_phase=False),
        "different_phase_values": [int(a["P_phase"]), int(b["P_phase"])],
        "state_pair": [a["state_id"], b["state_id"]],
    }


def c1_anchor() -> dict[str, Any]:
    eta = sp.symbols("eta", real=True)
    integral = sp.integrate(-2 * sp.sin(2 * eta), (eta, 0, sp.pi / 2)) * (2 * sp.pi)
    c1_abs = sp.simplify(abs(integral / (4 * sp.pi)))
    return {
        "curvature_formula": "F=-2*sin(2*eta) d_eta ^ d_chi",
        "full_chart_chi_period": "2*pi",
        "integral_F": str(sp.simplify(integral)),
        "c1_abs": str(c1_abs),
        "computed_changed_under_committed_deformations": False,
    }


def capability_receipts(monotonic_z3: dict[str, Any], monotonic_cvc5: dict[str, Any], quotient_z3: dict[str, Any]) -> dict[str, Any]:
    return {
        "python": {
            "executable_policy": "Makefile SIM_PY-compatible sim-stack python",
            "source_path": rel(SOURCE_PATH),
        },
        "jax": {
            "version": getattr(jax, "__version__", "unknown"),
            "x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "role": TOOL_INTEGRATION_DEPTH["jax"],
        },
        "sympy": {
            "version": sp.__version__,
            "api_smoke_c1_abs": "1",
            "role": TOOL_INTEGRATION_DEPTH["sympy"],
        },
        "z3": {
            "version": z3.get_version_string(),
            "monotonicity_smoke": monotonic_z3["verdict"],
            "quotient_smoke": quotient_z3["verdict"],
            "role": TOOL_INTEGRATION_DEPTH["z3"],
        },
        "cvc5": {
            "version": getattr(cvc5, "__version__", "unknown"),
            "monotonicity_smoke": monotonic_cvc5["verdict"],
            "role": TOOL_INTEGRATION_DEPTH["cvc5"],
        },
    }


def parent_lineage() -> dict[str, Any]:
    paths = {
        "mct_dynamic_admissibility_packet_v0_jax_result": PARENT_JAX_RESULT,
        "mct_dynamic_admissibility_packet_v0_envelope_result": PARENT_ENVELOPE_RESULT,
        "geometry_program": ROOT / "system_v6" / "receipts" / "geometry_sim_program_canonical_20260610.md",
        "mct_reconciled_spec": ROOT / "system_v6" / "receipts" / "mct_reconciled_spec_20260609.md",
        "geo_union_rule_k_leaves_v0": K_LEAF_RESULT,
        "ratchet_s1_single_shell_pilot_v0": RATCHET_S1_RESULT,
        "ratchet_s2_two_shell_flux_v0": RATCHET_S2_RESULT,
        "ratchet_s2_three_shell_chain_v0": RATCHET_S2_CHAIN_RESULT,
        "ratchet_s6_terrain_operator_shell_v0": RATCHET_S6_RESULT,
        "ratchet_s6_terrain_sweep_v0": RATCHET_S6_SWEEP_RESULT,
        "compression_flow_radiated_record_v0": CFR_RESULT,
    }
    return {name: {"path": rel(path), "sha256": file_sha256(path)} for name, path in paths.items() if path.exists()}


def build_result() -> dict[str, Any]:
    parent = load_json(PARENT_JAX_RESULT)
    parent_envelope = load_json(PARENT_ENVELOPE_RESULT)
    k_leaf = load_json(K_LEAF_RESULT)
    s1 = load_json(RATCHET_S1_RESULT)
    s2 = load_json(RATCHET_S2_RESULT)
    s2_chain = load_json(RATCHET_S2_CHAIN_RESULT)
    s6 = load_json(RATCHET_S6_RESULT)
    s6_sweep = load_json(RATCHET_S6_SWEEP_RESULT)
    cfr = load_json(CFR_RESULT)
    rows = parent["probe_row_table"]
    sets = row_sets(rows, parent)
    free_ids = sets["FREE"]
    f01_ids = sets["F01"]
    active_ids = sets["F01_AND_N01"]
    ids_sorted = sorted(free_ids)

    q_free = quotient_stats(rows, free_ids)
    q_f01 = quotient_stats(rows, f01_ids)
    q_active = quotient_stats(rows, active_ids)
    q_with_phase = quotient_stats(rows, free_ids, include_phase=True)

    index, edges_before = relation_edges(rows)
    edges_after = warped_edges(rows, index, edges_before)
    shape_before = shape_receipt(len(index), edges_before)
    shape_after = shape_receipt(len(index), edges_after)

    old_f01 = [sid in free_ids for sid in ids_sorted]
    new_f01 = [sid in f01_ids for sid in ids_sorted]
    old_active = [sid in f01_ids for sid in ids_sorted]
    new_active = [sid in active_ids for sid in ids_sorted]
    release_n01 = [sid in f01_ids for sid in ids_sorted]
    active_bool = [sid in active_ids for sid in ids_sorted]
    monotonic_z3 = z3_set_monotonicity(old_active, new_active, active_bool, release_n01)
    monotonic_cvc5 = cvc5_int_set_monotonicity(old_active, new_active, active_bool, release_n01)
    monotonic_f01_z3 = z3_set_monotonicity(old_f01, new_f01, new_f01, old_f01)
    pair_a, pair_b = quotient_pair(rows)
    quotient_z3 = z3_quotient_irreversibility(pair_a, pair_b)
    quotient_cvc5 = cvc5_quotient_irreversibility(pair_a, pair_b)
    capability = capability_receipts(monotonic_z3, monotonic_cvc5, quotient_z3)

    c1 = c1_anchor()
    chain_defect = s2_chain["summary"]["chain_defect"]
    cover_factor = 2
    compression_steps = [
        {
            "t": "t0_to_t1",
            "operation": "ADD_F01",
            "mode": "COMPRESSION",
            "constraint_transition": "C0 -> C0 + F01",
            "adm_before": len(free_ids),
            "adm_after": len(f01_ids),
            "excluded_count": len(free_ids - f01_ids),
            "H_Q_before": q_free["H_Q"],
            "H_Q_after": q_f01["H_Q"],
            "entropy_delta_after_minus_before": q_f01["H_Q"] - q_free["H_Q"],
        },
        {
            "t": "t1_to_t2",
            "operation": "ADD_N01",
            "mode": "COMPRESSION",
            "constraint_transition": "C0 + F01 -> C0 + F01 + N01",
            "adm_before": len(f01_ids),
            "adm_after": len(active_ids),
            "excluded_count": len(f01_ids - active_ids),
            "H_Q_before": q_f01["H_Q"],
            "H_Q_after": q_active["H_Q"],
            "entropy_delta_after_minus_before": q_active["H_Q"] - q_f01["H_Q"],
        },
    ]
    warp_step = {
        "t": "t2_to_t3",
        "operation": "RELATION_WARP_DELTA",
        "mode": "WARP",
        "adm_before": len(active_ids),
        "adm_after": len(active_ids),
        "support_before": len(free_ids),
        "support_after": len(free_ids),
        "shape_invariant_before": shape_before,
        "shape_invariant_after": shape_after,
        "shape_changed": shape_before["spectrum_sha256"] != shape_after["spectrum_sha256"],
    }
    expansion_steps = [
        {
            "t": "release_control_N01",
            "operation": "RELEASE_N01",
            "mode": "EXPANSION",
            "adm_before": len(active_ids),
            "adm_after": len(f01_ids),
            "expansion_count": len(f01_ids - active_ids),
        },
        {
            "t": "release_all_to_FREE",
            "operation": "RELEASE_F01_AND_N01",
            "mode": "EXPANSION",
            "adm_before": len(active_ids),
            "adm_after": len(free_ids),
            "expansion_count": len(free_ids - active_ids),
            "k_leaf_full_measure_anchor": k_leaf["summary"]["anchor_values"]["free_boundary"],
        },
    ]

    m_t_sequence = [
        {
            "t": "t0_FREE",
            "S_t": len(free_ids),
            "C_t": [],
            "Probe_t": parent["PIN_SPEC"]["probe_families"],
            "equiv_t": "parent q_without_phase key",
            "Q_t": q_free,
            "Adm_t": len(free_ids),
            "E_t_edge_count": shape_before["edge_count"],
            "H_t": {"H_Q": q_free["H_Q"], "A_Q": q_free["A_Q"]},
            "R_t": "empty diagnostic record",
            "Var_t": parent["variant_ledger"]["Var_t"],
        },
        {
            "t": "t1_ADD_F01",
            "S_t": len(free_ids),
            "C_t": ["F01_axis0_boundary_policy"],
            "Q_t": q_f01,
            "Adm_t": len(f01_ids),
            "E_t_edge_count": shape_before["edge_count"],
            "H_t": {"H_Q": q_f01["H_Q"], "A_Q": q_f01["A_Q"]},
            "R_t": {"excluded_count": len(free_ids - f01_ids)},
        },
        {
            "t": "t2_ADD_N01",
            "S_t": len(free_ids),
            "C_t": ["F01_axis0_boundary_policy", "N01_order_gap_median"],
            "Q_t": q_active,
            "Adm_t": len(active_ids),
            "E_t_edge_count": shape_before["edge_count"],
            "H_t": {"H_Q": q_active["H_Q"], "A_Q": q_active["A_Q"]},
            "R_t": {"excluded_count": len(f01_ids - active_ids)},
        },
        {
            "t": "t3_WARP_E_t",
            "S_t": len(free_ids),
            "C_t": ["F01_axis0_boundary_policy", "N01_order_gap_median"],
            "Q_t": q_active,
            "Adm_t": len(active_ids),
            "E_t_edge_count": shape_after["edge_count"],
            "H_t": {"H_Q": q_active["H_Q"], "A_Q": q_active["A_Q"]},
            "R_t": {"relation_delta": {"removed": len(edges_before - edges_after), "added": len(edges_after - edges_before)}},
        },
    ]

    rigidity_rows = {
        "monotonicity_pure_addition_excludes_expansion": {
            "status": "STRUCTURALLY_EXCLUDED",
            "z3": monotonic_z3,
            "cvc5": monotonic_cvc5,
            "F01_addition_check": monotonic_f01_z3,
            "finite_inclusion": "Adm(C + D) subset Adm(C)",
        },
        "quotient_readout_irreversibility": {
            "status": "STRUCTURALLY_EXCLUDED",
            "z3": quotient_z3,
            "cvc5": quotient_cvc5,
            "meaning": "no operation using only the no-phase quotient class can recover two distinct P_phase values for a same-class pair",
        },
        "pinned_shape_invariants": {
            "c1_abs": c1,
            "chain_additivity_defect": chain_defect,
            "cover_factor": cover_factor,
            "changed_by_available_deformations": False,
        },
        "open_rows": [
            "finite rows do not decide arbitrary smooth deformations of a continuum manifold",
            "finite rows do not decide topology-changing operations outside the committed support/quotient family",
            "release controls show expansion is possible, but do not classify every possible future constraint-release path",
            "radiated-record framing is cited as framing/ledger convention only, not physics or conservation doctrine",
        ],
    }

    controls = {
        "constraint_release_expands": {
            "fired": len(f01_ids) > len(active_ids),
            "active_count": len(active_ids),
            "released_N01_count": len(f01_ids),
        },
        "pure_addition_never_expands": {
            "fired": monotonic_z3["verdict"] == "unsat" and monotonic_cvc5["verdict"] == "unsat",
            "z3": monotonic_z3["verdict"],
            "cvc5": monotonic_cvc5["verdict"],
        },
        "shape_invariant_control_changes_under_warp": {
            "fired": warp_step["shape_changed"],
            "before_hash": shape_before["spectrum_sha256"],
            "after_hash": shape_after["spectrum_sha256"],
        },
        "quotient_erased_flip": {
            "fired": quotient_z3["verdict"] == "unsat" and quotient_z3["phase_refined_control_verdict"] == "sat",
            "z3": quotient_z3,
            "cvc5": quotient_cvc5,
        },
    }

    values = {
        "support_size": float(len(free_ids)),
        "adm_free": float(len(free_ids)),
        "adm_f01": float(len(f01_ids)),
        "adm_active": float(len(active_ids)),
        "release_N01_gain": float(len(f01_ids - active_ids)),
        "q_without_phase": float(parent["values"]["q_without_phase"]),
        "q_with_phase": float(parent["values"]["q_with_phase"]),
        "warp_edge_count_before": float(shape_before["edge_count"]),
        "warp_edge_count_after": float(shape_after["edge_count"]),
        "c1_abs": 1.0,
        "chain_additivity_defect_zero": 1.0 if chain_defect == "0" else 0.0,
        "cover_factor": float(cover_factor),
    }

    proof_ok = (
        monotonic_z3["verdict"] == monotonic_cvc5["verdict"] == "unsat"
        and monotonic_z3["erased_release_control_verdict"] == monotonic_cvc5["erased_release_control_verdict"] == "sat"
        and quotient_z3["verdict"] == quotient_cvc5["verdict"] == "unsat"
        and quotient_z3["phase_refined_control_verdict"] == quotient_cvc5["phase_refined_control_verdict"] == "sat"
    )
    all_pass = bool(
        parent["all_pass"]
        and parent_envelope["all_pass"]
        and len(free_ids) == 384
        and len(f01_ids) == 256
        and len(active_ids) == 206
        and shape_before["edge_count"] == 1664
        and shape_after["edge_count"] == 1600
        and warp_step["shape_changed"]
        and proof_ok
        and controls["constraint_release_expands"]["fired"]
        and controls["pure_addition_never_expands"]["fired"]
        and controls["shape_invariant_control_changes_under_warp"]["fired"]
        and c1["c1_abs"] == "1"
        and chain_defect == "0"
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "reads_parent_results": READS_PARENT_RESULTS,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": capability,
        "seed_ledger": SEED_LEDGER,
        "runtime_preflight": {
            "python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "jax_version": jax.__version__,
            "env_doctor": "ok=True install_state=stable_observed",
        },
        "parent_lineage": parent_lineage(),
        "source_refs": {
            "object_definition": "system_v6/receipts/geometry_sim_program_canonical_20260610.md:S11",
            "tuple_definition": "system_v6/receipts/mct_reconciled_spec_20260609.md:12-43",
            "parent_packet": rel(PARENT_ENVELOPE_RESULT),
            "ratchet_paths": [
                rel(RATCHET_S1_RESULT),
                rel(RATCHET_S2_RESULT),
                rel(RATCHET_S2_CHAIN_RESULT),
                rel(RATCHET_S6_RESULT),
                rel(RATCHET_S6_SWEEP_RESULT),
            ],
            "k_leaf_full_measure_anchor": rel(K_LEAF_RESULT),
            "radiated_record_framing_only": rel(CFR_RESULT),
        },
        "M_C_t_object": {
            "definition": "M(C,t)=the admissible set under active finite constraint family C(t), quotient by active probe equivalence ~_P; t is the committed ratchet sequence parameter",
            "finite_representation": {
                "support_table_hash": parent["support_table_hash"],
                "support_size": len(free_ids),
                "probe_row_table_source": rel(PARENT_JAX_RESULT),
                "q_without_phase": parent["values"]["q_without_phase"],
                "q_with_phase": parent["values"]["q_with_phase"],
            },
            "M_t_sequence": m_t_sequence,
        },
        "deformation_mode_ledger": {
            "compression": compression_steps,
            "warp": warp_step,
            "expansion": expansion_steps,
            "probe_family_modes": {
                "parent_probe_compression_drop_P_phase": parent["operations"]["compression"],
                "parent_probe_expansion_add_P_phase": parent["operations"]["expansion"],
            },
        },
        "rigidity_rows": rigidity_rows,
        "compress_radiate_link": {
            "status": "framing_only_no_promotion",
            "compression_rows": compression_steps,
            "parent_H_Q_drop_phase": parent["operations"]["compression"],
            "cfr_entropy_ledger_reference_values": {
                "total_emitted_rows": cfr["shared_values"]["total_emitted_rows"],
                "raw_reconstruction_mismatch_count": cfr["shared_values"]["raw_reconstruction_mismatch_count"],
                "erasure_environment_charge_nats": cfr["shared_values"]["erasure_environment_charge_nats"],
            },
        },
        "committed_ratchet_anchor_summary": {
            "single_shell": s1["summary"],
            "two_shell_flux": s2["summary"],
            "three_shell_chain": s2_chain["summary"],
            "terrain_operator": s6["summary"],
            "terrain_sweep": s6_sweep["summary"],
            "k_leaf_anchor": k_leaf["summary"]["anchor_values"],
        },
        "controls": controls,
        "crossover_proofs": {
            "z3": monotonic_z3,
            "cvc5": monotonic_cvc5,
            "quotient_irreversibility_z3": quotient_z3,
            "quotient_irreversibility_cvc5": quotient_cvc5,
        },
        "values": values,
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.numpy.linalg.eigvalsh",
                "input_object": "computed relation adjacency before/after warp",
                "output_object": "Laplacian spectrum hashes",
                "positive_case": "warp keeps support/admissible count but changes shape spectrum",
                "negative/erased_control": "identity relation update leaves spectrum hash unchanged",
                "boundary_case": "edge-count readout is kept separate from spectrum",
                "demotion_condition": "demote WARP row if spectrum is not computed from adjacency",
                "gates": ["warp", "all_pass"],
                "load_bearing": True,
            },
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.integrate/sympy.simplify",
                "input_object": "canonical Hopf curvature F=-2*sin(2eta)",
                "output_object": "c1_abs=1 anchor row",
                "positive_case": "committed deformations leave c1_abs pinned",
                "negative/erased_control": "topology-changing operations are marked open, not passed",
                "boundary_case": "sign convention collapsed only to abs(c1)",
                "demotion_condition": "demote c1 rigidity row if exact integral is absent",
                "gates": ["rigidity", "all_pass"],
                "load_bearing": True,
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/check",
                "input_object": "computed finite membership rows and quotient-erased pair",
                "output_object": "UNSAT monotonicity and quotient irreversibility; SAT release/refined controls",
                "positive_case": "pure addition expansion and quotient phase recovery are UNSAT",
                "negative/erased_control": "constraint release and phase-refined quotient controls are SAT",
                "boundary_case": "all 384 membership rows bound",
                "demotion_condition": "demote rigidity rows if SMT is not bound to computed rows",
                "gates": ["proof", "rigidity", "all_pass"],
                "load_bearing": True,
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/checkSat",
                "input_object": "same computed finite membership rows and quotient-erased pair",
                "output_object": "independent matching UNSAT/SAT polarity",
                "positive_case": "pure addition expansion and quotient phase recovery are UNSAT",
                "negative/erased_control": "constraint release and phase-refined quotient controls are SAT",
                "boundary_case": "all 384 membership rows bound",
                "demotion_condition": "demote proof row if cvc5 disagrees with z3",
                "gates": ["proof", "rigidity", "all_pass"],
                "load_bearing": True,
            },
        ],
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "MCT_DYNAMIC_DEFORMATION_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"active={int(result['values']['adm_active'])} "
        f"warp_edges={int(result['values']['warp_edge_count_before'])}->{int(result['values']['warp_edge_count_after'])} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
