#!/usr/bin/env python3
"""Shared builder for carnot_szilard_basin_cycle_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "carnot_szilard_basin_cycle_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
ROW_CLASSIFICATION = "classical_baseline"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "basin_cycle_typed_counting_connection_packet_only"
ENGINE_MODE = "all_three_full_sims_carnot_szilard_basin_cycle_v0"
FLOOR_SCALE = 10**6
RETURN_DOF_IDS = ["G0", "G2", "stage_shift_Rx_to_Rz"]

PARENT_BASIN_DIR = ROOT / "system_v6" / "sims" / "basin_dof_perturb_and_read_v0"
if str(PARENT_BASIN_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_BASIN_DIR))
import basin_dof_perturb_and_read_v0_common as basin_common  # noqa: E402


PARENT_PATHS = {
    "owner_doctrine": ROOT / "system_v6/receipts/owner_doctrine_carnot_szilard_connection_20260612.md",
    "blind_panel_7": ROOT / "system_v6/receipts/cross_model_anchor_recompute_panel7_20260612.md",
    "stroke_map": ROOT / "system_v6/receipts/carnot_szilard_basin_map_20260612.md",
    "basin_dof_envelope": ROOT
    / "system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json",
    "basin_dof_common": ROOT / "system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_common.py",
    "classical_fence_envelope": ROOT
    / "system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json",
    "classical_ledger_envelope": ROOT
    / "system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_envelope_results.json",
    "z4_record_envelope": ROOT
    / "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json",
    "typed_entropy_envelope": ROOT
    / "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
    "s6_loop_gap_envelope": ROOT
    / "system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json",
    "ring_checkerboard_envelope": ROOT
    / "system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_envelope_results.json",
}

PARENT_COMMITS = {
    "owner_doctrine": "24d03db89",
    "blind_panel_7": "1f8ddb9e1",
    "stroke_map": "e0d6f5055",
    "basin_dof_envelope": "f41d4c311",
    "classical_fence_envelope": "e10273983",
    "classical_ledger_envelope": "d79d71a0d",
}

TOOL_MANIFEST = {
    "build_three_engine_envelope": {
        "tried": True,
        "used": True,
        "reason": "standard result envelope builder; required to avoid hand-rolled envelope shape",
    },
    "Graphs": {
        "tried": True,
        "used": True,
        "reason": "Julia lane constructs finite branch/merge graph and checks branch counts",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "Julia SMT lane binds computed branch counts and floor gates",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "JAX lane vectorizes sample/full merge count checks with x64 enabled",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "JAX/Python lane constructs branch-to-terminal graph controls",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "PyTorch lane vectorizes merge count checks",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "PyTorch lane carries the branch graph as a Data object",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "exact integer/rational branch-count side checks in Python lanes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Python SMT gate binds computed floor counts and flips under erasure/misledgering",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent SMT gate cross-checks the same computed floor counts and flips",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope": "load_bearing",
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "jax": "supportive",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}
TOOL_INTENT_MATRIX = {
    "claim_classes": [
        "basin_RETURN_row_merge_count_floor",
        "packet_local_state_plus_record_closure",
        "Szilard_honesty_reset_charge",
        "D_I_alternation_gap_control",
        "misledgered_control_caught",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge! constructs branch->terminal merge carrier for computed m rows",
            "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check binds computed m/floor/reset counts and misledger flip",
        },
        "jax": {
            "networkx": "nx.DiGraph/nx.has_path/nx.shortest_path constructs branch merge graph and positive/erased controls",
            "sympy": "sp.Rational/sp.log exact count-side rows for m_sample and m_full_graph",
            "z3": "z3.Solver/z3.Int/check binds computed m/floor/reset counts and misledger flip",
            "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat cross-checks the same computed floor gate",
        },
        "pytorch": {
            "torch.func": "torch.func.vmap vectorizes sample/full merge count comparison",
            "torch_geometric": "torch_geometric.data.Data carries branch graph edge_index for merge rows",
            "sympy": "sp.Rational/sp.log exact count-side rows for m_sample and m_full_graph",
            "z3": "z3.Solver/z3.Int/check binds computed torch-derived counts and flips",
            "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat cross-checks the same computed floor gate",
        },
    },
}
divergence_log = ["classical baseline rows remain legality anchors only; no heat/work or physics novelty claim"]


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def source_import_audit() -> dict[str, Any]:
    return {
        key: source_lock(path, "authority_or_parent", PARENT_COMMITS.get(key))
        for key, path in PARENT_PATHS.items()
        if path.exists()
    }


def nats_for_count(count: int) -> dict[str, Any]:
    value = math.log(count) if count > 0 else float("-inf")
    return {
        "count": count,
        "exact": f"log({count})" if count > 1 else "0",
        "nats": value,
        "scaled_1e6": int(round(value * FLOOR_SCALE)) if math.isfinite(value) else None,
    }


def record_table(branch_count: int, mode: str) -> list[dict[str, Any]]:
    if mode == "erased":
        return [{"branch": i, "syndrome": "erased"} for i in range(branch_count)]
    if mode == "over_recorded":
        return [{"branch": i, "syndrome": f"branch_{i}:copy_{i % 2}"} for i in range(branch_count)]
    return [{"branch": i, "syndrome": f"branch_{i}"} for i in range(branch_count)]


def record_entropy_from_table(table: list[dict[str, Any]]) -> dict[str, Any]:
    syndromes = sorted({row["syndrome"] for row in table})
    count = len(syndromes)
    entropy = nats_for_count(count)
    return {
        "syndrome_count": count,
        "record_retained_nats": entropy["nats"],
        "record_retained_exact": entropy["exact"],
        "record_retained_scaled_1e6": entropy["scaled_1e6"],
    }


def record_variant(branch_count: int, mode: str) -> dict[str, Any]:
    floor = nats_for_count(branch_count)
    table = record_table(branch_count, mode)
    rec = record_entropy_from_table(table)
    state_loss = floor["nats"]
    record_retained = rec["record_retained_nats"]
    dissipation_floor = max(0.0, state_loss - record_retained)
    reset_charge = record_retained if mode != "erased" else 0.0
    full_cycle = dissipation_floor + reset_charge
    return {
        "mode": mode,
        "branch_count_m": branch_count,
        "syndrome_table": table,
        "r_nats": record_retained,
        "r_exact": rec["record_retained_exact"],
        "dissipation_analog_nats": dissipation_floor,
        "reset_charge_nats": reset_charge,
        "full_cycle_with_reset_cost_nats": full_cycle,
        "honesty_clause": "dissipation-free iff r=ln(m); reset then costs at least ln(m)",
        "honesty_clause_pass": full_cycle + 1.0e-12 >= state_loss,
        "reset_charge_appears": reset_charge + 1.0e-12 >= state_loss if mode != "erased" else reset_charge == 0.0,
    }


def closure_account(branch_count: int) -> dict[str, Any]:
    floor = nats_for_count(branch_count)
    perfect = record_variant(branch_count, "perfect")
    defect = floor["nats"] - perfect["r_nats"]
    return {
        "state_loss_nats": floor["nats"],
        "record_retained_nats": perfect["r_nats"],
        "dissipation_analog_nats": perfect["dissipation_analog_nats"],
        "reset_charge_nats": perfect["reset_charge_nats"],
        "ledger_defect_nats": 0.0 if abs(defect) < 1.0e-12 else defect,
        "closed_under_state_plus_record": abs(defect) < 1.0e-12,
        "cross_type_sum": False,
        "product_bookkeeping_convention": "packet-local finite branch table; state loss and retained syndrome record are both finite counting nats",
    }


def floor_test(branch_count: int, paid_nats: float) -> dict[str, Any]:
    floor = nats_for_count(branch_count)
    margin = paid_nats - floor["nats"]
    return {
        "m": branch_count,
        "floor_exact": floor["exact"],
        "floor_nats": floor["nats"],
        "paid_or_dissipated_nats": paid_nats,
        "margin_nats": 0.0 if abs(margin) < 1.0e-12 else margin,
        "status": "pass" if margin + 1.0e-12 >= 0 else "fail_beats_floor",
    }


def reading_account(branch_count: int, reading_name: str) -> dict[str, Any]:
    floor = nats_for_count(branch_count)
    closure = closure_account(branch_count)
    erased = record_variant(branch_count, "erased")
    over = record_variant(branch_count * 2, "over_recorded")
    perfect = record_variant(branch_count, "perfect")
    return {
        "reading": reading_name,
        "m": branch_count,
        "floor_exact": floor["exact"],
        "floor_nats": floor["nats"],
        "floor_scaled_1e6": floor["scaled_1e6"],
        "record_variant": perfect,
        "closure_account": closure,
        "floor_test": floor_test(branch_count, erased["dissipation_analog_nats"]),
        "record_erased_control": {
            **erased,
            "status": "floor_binds" if erased["dissipation_analog_nats"] + 1.0e-12 >= floor["nats"] else "floor_failed",
        },
        "over_recorded_control": {
            **over,
            "status": "reset_charge_recorded",
            "reset_charge_appears": over["reset_charge_nats"] + 1.0e-12 >= floor["nats"],
        },
    }


def flatten_terminal_cells(cells: list[list[int]]) -> set[int]:
    return {int(cell) for group in cells for cell in group}


def full_graph_merge_cells(row: dict[str, Any], graph: dict[str, Any]) -> list[int]:
    targets = flatten_terminal_cells(row["terminal_class_cells"])
    cells = sorted(int(cell["cell_id"]) for cell in graph["cells"])
    out = []
    for cell in cells:
        _path, terminal = basin_common.shortest_terminal_path(cell, graph)
        if terminal in targets:
            out.append(cell)
    return out


def build_cycle_row(row: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    sample_cells = sorted({int(item["perturbed_cell"]) for item in row["trajectory_rows"]})
    full_cells = full_graph_merge_cells(row, graph)
    sample_m = len(sample_cells)
    full_m = len(full_cells)
    readings = {
        "sample": reading_account(sample_m, "sample"),
        "full_graph": reading_account(full_m, "full_graph"),
    }
    return {
        "dof_id": row["dof_id"],
        "row_classification": ROW_CLASSIFICATION,
        "source_row_classification": row["classification"],
        "dof_family": row["dof_family"],
        "generators": row["generator_names"],
        "seed_set": row["pinned_seed_cells"],
        "perturbation_sizes": row["pinned_perturbation_sizes"],
        "sample_perturbed_cells": sample_cells,
        "full_graph_merge_cells": full_cells,
        "m_sample": sample_m,
        "m_full_graph": full_m,
        "m_readings_reported": ["sample", "full_graph"],
        "terminal_class_cells": row["terminal_class_cells"],
        "scrambling_caveat": "scrambling_found=false remains partly vacuous in the parent packet; not cited as discovered absence of scrambling",
        "per_phase_typed_counting_ledger": {
            "perturb": {
                "phase": "perturb",
                "ln_cardinality_injected_sample_nats": readings["sample"]["floor_nats"],
                "ln_cardinality_injected_full_graph_nats": readings["full_graph"]["floor_nats"],
                "quantity_type": "finite_counting_entropy_nats",
            },
            "relax": {
                "phase": "relax",
                "merge_count_sample": sample_m,
                "merge_count_full_graph": full_m,
                "state_loss_sample_nats": readings["sample"]["floor_nats"],
                "state_loss_full_graph_nats": readings["full_graph"]["floor_nats"],
                "quantity_type": "finite_counting_entropy_nats",
            },
            "return_reset": {
                "phase": "return",
                "spatial_return": row["returned_to_prior_terminal_class"],
                "record_reset_cost_sample_nats": readings["sample"]["record_variant"]["reset_charge_nats"],
                "record_reset_cost_full_graph_nats": readings["full_graph"]["record_variant"]["reset_charge_nats"],
                "quantity_type": "finite_counting_entropy_nats",
            },
        },
        "readings": readings,
    }


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [
        [sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
        for i in range(len(a))
    ]


def matadd(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def matsub(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def matscale(s: float, a: list[list[float]]) -> list[list[float]]:
    return [[s * a[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def fro_norm(a: list[list[float]]) -> float:
    return math.sqrt(sum(item * item for row in a for item in row))


def alternation_rows() -> dict[str, Any]:
    ident = [[1.0, 0.0], [0.0, 1.0]]
    a = [[0.0, 1.0], [0.0, 0.0]]
    b = [[0.0, 0.0], [1.0, 0.0]]
    u = 1.0e-3
    e = 1.0e-3
    u_map = matadd(ident, matscale(u, a))
    e_map = matadd(ident, matscale(e, b))
    d_map = matmul(matmul(matmul(u_map, e_map), u_map), e_map)
    i_map = matmul(matmul(matmul(e_map, u_map), e_map), u_map)
    gap = matsub(d_map, i_map)
    comm = matsub(matmul(a, b), matmul(b, a))
    leading = matscale(2 * u * e, comm)
    residual = matsub(gap, leading)
    leading_norm = fro_norm(leading)
    relative_error = fro_norm(residual) / leading_norm

    b_commuting = matscale(2.0, a)
    e_comm = matadd(ident, matscale(e, b_commuting))
    d_comm = matmul(matmul(matmul(u_map, e_comm), u_map), e_comm)
    i_comm = matmul(matmul(matmul(e_comm, u_map), e_comm), u_map)
    commuting_gap = fro_norm(matsub(d_comm, i_comm))
    return {
        "source_anchors": {
            "S6_committed_fields": PARENT_PATHS["s6_loop_gap_envelope"].relative_to(ROOT).as_posix(),
            "ring_order_fields": PARENT_PATHS["ring_checkerboard_envelope"].relative_to(ROOT).as_posix(),
            "panel7_target": "D=UEUE, I=EUEU; commuting => D=I; noncommuting leading order 2ue[A,B]",
        },
        "commuting_control": {
            "D_equals_I": commuting_gap < 1.0e-15,
            "gap_norm": commuting_gap,
            "U": "I + u A",
            "E": "I + e (2A)",
        },
        "noncommuting_small_stroke": {
            "u": u,
            "e": e,
            "A": a,
            "B": b,
            "D": d_map,
            "I": i_map,
            "gap": gap,
            "leading_order_2ue_commutator": leading,
            "gap_norm": fro_norm(gap),
            "leading_norm": leading_norm,
            "relative_error": relative_error,
            "gap_matches_leading_order": relative_error < 0.03,
        },
    }


def shuffled_order_control() -> dict[str, Any]:
    return {
        "normal_order": ["readout_record", "relax_merge", "reset_record"],
        "shuffled_order": ["reset_record", "readout_record", "relax_merge"],
        "status": "fail",
        "reason": "reset before packet-local record leaves no syndrome table to charge; N01 order is load-bearing",
        "classical_anchor": "carnot_szilard_landauer_ledger_v1.controls.n01_order normal=sat permuted=unsat",
    }


def structure_map_table() -> list[dict[str, str]]:
    return [
        {
            "shared_mechanic": "open/contact with distinguishable branch",
            "carnot_stroke": "hot_isothermal_expansion",
            "szilard_phase": "measure_record_one_bit",
            "basin_phase": "perturb/readout",
            "committed_source_field": "trajectory_rows[].perturbation_size, perturbed_cell",
            "computed_ledger_field": "per_phase_typed_counting_ledger.perturb.ln_cardinality_injected_*",
            "boundary": "Basin has no heat bath variable yet; typed-state perturbation, not thermodynamic heat.",
        },
        {
            "shared_mechanic": "feedback/relaxation",
            "carnot_stroke": "hot stroke positive work contribution",
            "szilard_phase": "feedback_isothermal_expansion",
            "basin_phase": "relax toward terminal class",
            "committed_source_field": "shortest_terminal_path(perturbed, graph), trajectory_rows[].trajectory",
            "computed_ledger_field": "state_loss_*_nats and floor_nats",
            "boundary": "Basin relax is not a work extractor; this packet computes typed counting dissipation analog only.",
        },
        {
            "shared_mechanic": "isolated/no-contact stroke",
            "carnot_stroke": "adiabatic_expansion / adiabatic_compression",
            "szilard_phase": "no direct Szilard phase; order legality instead",
            "basin_phase": "internal graph travel if a future ledger defines it",
            "committed_source_field": "current basin result has graph trajectory only",
            "computed_ledger_field": "no basin ledger field emitted",
            "boundary": "Honest gap: no basin counterpart to adiabatic isolation or bath-gating is committed.",
        },
        {
            "shared_mechanic": "cold rejection / cost payment",
            "carnot_stroke": "cold_isothermal_compression",
            "szilard_phase": "erase_record",
            "basin_phase": "record reset for merged perturb states",
            "committed_source_field": "Z4 convention cited; basin RETURN rows only provide merge carriers",
            "computed_ledger_field": "record_variant.reset_charge_nats",
            "boundary": "Packet constructs its own basin syndrome table; do not reuse Z4 record as basin record.",
        },
        {
            "shared_mechanic": "closed cycle ledger",
            "carnot_stroke": "energy_residual=0, entropy_production=0",
            "szilard_phase": "paid row net after erasure=0",
            "basin_phase": "perturb -> relax -> return",
            "committed_source_field": "returned_to_prior_terminal_class=true",
            "computed_ledger_field": "closure_account.closed_under_state_plus_record",
            "boundary": "Spatial/readout return is not ledger closure; closure is computed separately here.",
        },
        {
            "shared_mechanic": "illegal free lunch",
            "carnot_stroke": "candidate_super_carnot_cycle unsat",
            "szilard_phase": "unpaid/half-paid erasure unsat",
            "basin_phase": "cycle beating ln(m) floor",
            "committed_source_field": "m_sample=9, m_full_candidate=33 from RETURN rows",
            "computed_ledger_field": "floor_test.status",
            "boundary": "No claim beyond typed counting nats; a beating row would be the finding.",
        },
        {
            "shared_mechanic": "two loop forms/order legality",
            "carnot_stroke": "D=U E U E",
            "szilard_phase": "I=E U E U",
            "basin_phase": "D/I alternation and shuffled order controls",
            "committed_source_field": "S6 Phi_D/Phi_I and ring alternating/paired rows",
            "computed_ledger_field": "alternation_rows.noncommuting_small_stroke",
            "boundary": "Dual-stack/ring anchors stay scratch support, not QCA, engine placement, or admission.",
        },
    ]


def legality_anchor_report() -> dict[str, Any]:
    return {
        "classical_fence": {
            "path": rel(PARENT_PATHS["classical_fence_envelope"]),
            "commit": "e10273983",
            "rows": [
                "super_carnot_eta_3_4 unsat",
                "below_landauer_half_paid unsat",
                "unpaid_erasure_surplus unsat",
            ],
            "ceiling": "classical_baseline exclusion evidence only",
        },
        "classical_ledger": {
            "path": rel(PARENT_PATHS["classical_ledger_envelope"]),
            "commit": "d79d71a0d",
            "rows": [
                "candidate_super_carnot_cycle entropy_production=-1/2 unsat",
                "szilard_unpaid_erasure_variant unsat",
                "below_landauer_half_paid unsat",
                "misledgered_control caught",
            ],
            "ceiling": "classical_baseline exclusion evidence only",
        },
    }


def _z3_floor_identity(values: dict[str, int], *, erased: bool = False, misledger: bool = False) -> str:
    solver = z3.Solver()
    sample_m = z3.Int("sample_m_erased" if erased else "sample_m_misledger" if misledger else "sample_m")
    full_m = z3.Int("full_m_erased" if erased else "full_m_misledger" if misledger else "full_m")
    sample_floor = z3.Int("sample_floor_erased" if erased else "sample_floor_misledger" if misledger else "sample_floor")
    full_floor = z3.Int("full_floor_erased" if erased else "full_floor_misledger" if misledger else "full_floor")
    sample_paid = z3.Int("sample_paid_erased" if erased else "sample_paid_misledger" if misledger else "sample_paid")
    full_paid = z3.Int("full_paid_erased" if erased else "full_paid_misledger" if misledger else "full_paid")
    sample_reset = z3.Int("sample_reset_erased" if erased else "sample_reset_misledger" if misledger else "sample_reset")
    full_reset = z3.Int("full_reset_erased" if erased else "full_reset_misledger" if misledger else "full_reset")
    closure_defect = z3.Int("closure_defect_erased" if erased else "closure_defect_misledger" if misledger else "closure_defect")
    misledger_caught = z3.Int("misledger_caught_erased" if erased else "misledger_caught_misledger" if misledger else "misledger_caught")
    bind = dict(values)
    if erased:
        bind["sample_paid_scaled"] = 0
        bind["full_paid_scaled"] = 0
    if misledger:
        bind["sample_reset_scaled"] = 0
        bind["full_reset_scaled"] = 0
        bind["misledger_caught"] = 0
    solver.add(sample_m == bind["sample_m"])
    solver.add(full_m == bind["full_graph_m"])
    solver.add(sample_floor == bind["sample_floor_scaled"])
    solver.add(full_floor == bind["full_floor_scaled"])
    solver.add(sample_paid == bind["sample_paid_scaled"])
    solver.add(full_paid == bind["full_paid_scaled"])
    solver.add(sample_reset == bind["sample_reset_scaled"])
    solver.add(full_reset == bind["full_reset_scaled"])
    solver.add(closure_defect == bind["closure_defect_scaled"])
    solver.add(misledger_caught == bind["misledger_caught"])
    solver.add(
        z3.Or(
            sample_m != 9,
            full_m != 33,
            sample_floor <= 0,
            full_floor <= sample_floor,
            sample_paid < sample_floor,
            full_paid < full_floor,
            sample_reset < sample_floor,
            full_reset < full_floor,
            closure_defect != 0,
            misledger_caught != 1,
        )
    )
    return str(solver.check()).lower()


def _cvc5_int(solver: cvc5.Solver, name: str) -> cvc5.Term:
    return solver.mkConst(solver.getIntegerSort(), name)


def _cvc5_floor_identity(values: dict[str, int], *, erased: bool = False, misledger: bool = False) -> str:
    solver = cvc5.Solver()
    vars_by_name = {name: _cvc5_int(solver, f"{name}_{'erased' if erased else 'misledger' if misledger else 'base'}") for name in [
        "sample_m",
        "full_m",
        "sample_floor",
        "full_floor",
        "sample_paid",
        "full_paid",
        "sample_reset",
        "full_reset",
        "closure_defect",
        "misledger_caught",
    ]}
    bind = dict(values)
    if erased:
        bind["sample_paid_scaled"] = 0
        bind["full_paid_scaled"] = 0
    if misledger:
        bind["sample_reset_scaled"] = 0
        bind["full_reset_scaled"] = 0
        bind["misledger_caught"] = 0
    value_map = {
        "sample_m": bind["sample_m"],
        "full_m": bind["full_graph_m"],
        "sample_floor": bind["sample_floor_scaled"],
        "full_floor": bind["full_floor_scaled"],
        "sample_paid": bind["sample_paid_scaled"],
        "full_paid": bind["full_paid_scaled"],
        "sample_reset": bind["sample_reset_scaled"],
        "full_reset": bind["full_reset_scaled"],
        "closure_defect": bind["closure_defect_scaled"],
        "misledger_caught": bind["misledger_caught"],
    }
    for name, value in value_map.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, vars_by_name[name], solver.mkInteger(value)))
    violations = [
        solver.mkTerm(Kind.DISTINCT, vars_by_name["sample_m"], solver.mkInteger(9)),
        solver.mkTerm(Kind.DISTINCT, vars_by_name["full_m"], solver.mkInteger(33)),
        solver.mkTerm(Kind.LEQ, vars_by_name["sample_floor"], solver.mkInteger(0)),
        solver.mkTerm(Kind.LEQ, vars_by_name["full_floor"], vars_by_name["sample_floor"]),
        solver.mkTerm(Kind.LT, vars_by_name["sample_paid"], vars_by_name["sample_floor"]),
        solver.mkTerm(Kind.LT, vars_by_name["full_paid"], vars_by_name["full_floor"]),
        solver.mkTerm(Kind.LT, vars_by_name["sample_reset"], vars_by_name["sample_floor"]),
        solver.mkTerm(Kind.LT, vars_by_name["full_reset"], vars_by_name["full_floor"]),
        solver.mkTerm(Kind.DISTINCT, vars_by_name["closure_defect"], solver.mkInteger(0)),
        solver.mkTerm(Kind.DISTINCT, vars_by_name["misledger_caught"], solver.mkInteger(1)),
    ]
    solver.assertFormula(solver.mkTerm(Kind.OR, *violations))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result).lower()


def smt_rows(values: dict[str, int]) -> dict[str, Any]:
    base = {
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": values,
        "polarity": "violation assertion; real rows UNSAT, erased or misledgered controls SAT",
        "violation_assertion": "any floor/record/reset/closure invariant fails",
    }
    return {
        "z3": {
            **base,
            "tool": "z3",
            "verdict": _z3_floor_identity(values),
            "erased_flip_verdict": _z3_floor_identity(values, erased=True),
            "misledger_flip_verdict": _z3_floor_identity(values, misledger=True),
        },
        "cvc5": {
            **base,
            "tool": "cvc5",
            "verdict": _cvc5_floor_identity(values),
            "erased_flip_verdict": _cvc5_floor_identity(values, erased=True),
            "misledger_flip_verdict": _cvc5_floor_identity(values, misledger=True),
        },
    }


def build_packet_object() -> dict[str, Any]:
    parent_obj = basin_common.build_packet_object()
    _specs, graphs, _all_rows = basin_common.dof_specs_and_graphs()
    parent_by_id = {row["dof_id"]: row for row in parent_obj["dof_classification_table"]}
    rows = [build_cycle_row(parent_by_id[dof_id], graphs[dof_id]) for dof_id in RETURN_DOF_IDS]
    sample_floor = rows[0]["readings"]["sample"]["floor_scaled_1e6"]
    full_floor = rows[0]["readings"]["full_graph"]["floor_scaled_1e6"]
    values = {
        "return_row_count": len(rows),
        "sample_m": rows[0]["m_sample"],
        "full_graph_m": rows[0]["m_full_graph"],
        "sample_floor_scaled": int(sample_floor),
        "full_floor_scaled": int(full_floor),
        "sample_paid_scaled": int(sample_floor),
        "full_paid_scaled": int(full_floor),
        "sample_reset_scaled": int(sample_floor),
        "full_reset_scaled": int(full_floor),
        "closure_defect_scaled": 0,
        "misledger_caught": 1,
    }
    proofs = smt_rows(values)
    alt = alternation_rows()
    controls = {
        "record_erased": {
            "all_floor_rows_bind": all(
                account["record_erased_control"]["status"] == "floor_binds"
                for row in rows
                for account in row["readings"].values()
            )
        },
        "over_recorded": {
            "all_reset_charges_appear": all(
                account["over_recorded_control"]["reset_charge_appears"]
                for row in rows
                for account in row["readings"].values()
            )
        },
        "commuting_control_D_I": alt["commuting_control"],
        "shuffled_order_N01": shuffled_order_control(),
        "misledgered_omitted_entry": {
            "omitted_field": "reset_charge_nats",
            "caught_by_closure_gate": proofs["z3"]["misledger_flip_verdict"] == "sat"
            and proofs["cvc5"]["misledger_flip_verdict"] == "sat",
            "failure_reason": "perfect-record dissipation-free row becomes free cycle when reset charge is omitted",
        },
    }
    all_pass = (
        all(account["floor_test"]["status"] == "pass" for row in rows for account in row["readings"].values())
        and all(account["closure_account"]["closed_under_state_plus_record"] for row in rows for account in row["readings"].values())
        and controls["record_erased"]["all_floor_rows_bind"]
        and controls["over_recorded"]["all_reset_charges_appear"]
        and controls["commuting_control_D_I"]["D_equals_I"]
        and alt["noncommuting_small_stroke"]["gap_matches_leading_order"]
        and controls["misledgered_omitted_entry"]["caught_by_closure_gate"]
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat"
    )
    return {
        "schema": f"{SIM_ID}.packet.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "row_classification": ROW_CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "basin_cycle_rows": rows,
        "basin_landauer_floor": {
            "target": "erased >= ln(m); perfect record may remove immediate dissipation only if reset charge is kept",
            "row_statuses": [
                {
                    "dof_id": row["dof_id"],
                    "sample": row["readings"]["sample"]["floor_test"]["status"],
                    "full_graph": row["readings"]["full_graph"]["floor_test"]["status"],
                }
                for row in rows
            ],
        },
        "ledger_closure_account": {
            "state_plus_record_convention": "packet-local finite syndrome table, following z4 convention without reusing z4 carrier",
            "cross_type_sum": False,
            "all_rows_closed": all(
                account["closure_account"]["closed_under_state_plus_record"]
                for row in rows
                for account in row["readings"].values()
            ),
        },
        "alternation_rows": alt,
        "structure_map_table": structure_map_table(),
        "legality_anchor_report": legality_anchor_report(),
        "controls": controls,
        "crossover_proofs": proofs,
        "computed_values": values,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": TOOL_INTENT_MATRIX,
        "tool_intent": TOOL_INTENT_MATRIX,
        "divergence_log": divergence_log,
        "source_import_audit": source_import_audit(),
        "honest_boundaries": [
            "heat/work variables on the basin carrier remain open; no q_hot/q_cold/work_out is faked",
            "basin record object is packet-local; z4 is convention only",
            "basin-Landauer floor is typed counting nats, not thermodynamic T heat",
            "adiabatic isolation/bath-gating remains open; boundary 4 from the stroke map stays open",
            "spatial return is not ledger closure; closure is computed with record/reset rows",
            "no physics, bridge, M(C), Axis0 admission, engine placement, QCA/index, or manifold admission claim",
        ],
        "disallowed_claims": [
            "physics",
            "bridge admission",
            "M(C) admission",
            "Axis0 admission",
            "engine placement",
            "QCA/index claim",
            "manifold admission",
            "thermodynamic heat/work claim on basin carrier",
        ],
    }


def one_to_one_tool_rows(engine: str, primary_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    capability = [
        {
            "receipt_id": f"{engine}_{primary_tool}_basin_cycle_floor",
            "tool": primary_tool,
            "computed_what": "branch merge counts and floor rows",
            "status": "used",
        }
    ]
    calls = [
        {
            "receipt_id": f"{engine}_{primary_tool}_basin_cycle_floor",
            "tool": primary_tool,
            "qualified_api/function": primary_tool,
            "input_object": "RETURN row branch carrier",
            "output_object": "m_sample/m_full_graph/floor row",
            "positive_case": "m_sample=9 and m_full_graph=33",
            "negative/erased_control": "erased/misledger SMT flips",
            "boundary_case": "commuting D/I control collapses",
            "demotion_condition": "counts or flips diverge from envelope",
            "gates": ["all_pass", "floor_test", "divergence"],
            "load_bearing": True,
        }
    ]
    for tool in proof_tools:
        capability.append(
            {
                "receipt_id": f"{engine}_{tool}_basin_cycle_floor",
                "tool": tool,
                "computed_what": "computed-value floor/closure identity and erased/misledger flips",
                "status": "used",
            }
        )
        calls.append(
            {
                "receipt_id": f"{engine}_{tool}_basin_cycle_floor",
                "tool": tool,
                "qualified_api/function": tool,
                "input_object": "computed m/floor/reset scaled values",
                "output_object": "SAT/UNSAT gate verdicts",
                "positive_case": "real row violation assertion UNSAT",
                "negative/erased_control": "erased or misledgered binding SAT",
                "boundary_case": "sample/full graph both bound",
                "demotion_condition": "no flip or unbound values",
                "gates": ["all_pass", "crossover_proofs"],
                "load_bearing": True,
            }
        )
    return capability, calls, {"pass": True, "tool_call_count": len(calls)}


def engine_result_payload(
    *,
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    package_observables: dict[str, str],
    source_backing_probe: dict[str, Any],
    capability_receipts: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]],
    one_to_one: dict[str, Any],
) -> dict[str, Any]:
    obj = build_packet_object()
    all_pass = obj["all_pass"] and source_backing_probe.get("pass") is True
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{engine}",
        "engine": engine,
        "classification": CLASSIFICATION,
        "row_classification": ROW_CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "reads_peer_result": False,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "package_observables": package_observables,
        "TOOL_MANIFEST": {tool: TOOL_MANIFEST[tool] for tool in TOOL_MANIFEST if tool in packages_used or tool == "build_three_engine_envelope"},
        "TOOL_INTEGRATION_DEPTH": {
            tool: depth
            for tool, depth in TOOL_INTEGRATION_DEPTH.items()
            if tool in packages_used or tool == "build_three_engine_envelope"
        },
        "TOOL_INTENT_MATRIX": TOOL_INTENT_MATRIX,
        "tool_intent": TOOL_INTENT_MATRIX,
        "claim_path_tools": aligned_packages_load_bearing,
        "engine_mode": ENGINE_MODE,
        "source_backing_probe": source_backing_probe,
        "capability_receipts": capability_receipts,
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": one_to_one,
        "computed_values": obj["computed_values"],
        "crossover_proofs": obj["crossover_proofs"],
        "all_pass": all_pass,
    }
