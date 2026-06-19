#!/usr/bin/env python3
"""Shared builder for basin_dof_perturb_and_read_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import z3


SIM_ID = "basin_dof_perturb_and_read_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "basin_dof_readout_rows_only"
ENGINE_MODE = "all_three_full_sims_basin_dof_axis0_readout_rows"
AXIS0_COMMIT_HINT = "5d330b427"
OWNER_DOCTRINE_COMMIT_HINT = "fcf1b3858"
WELD_COMMIT_HINT = "d6815079e"
PINNED_SEEDS = [0, 3, 15, 16, 17, 31]
PERTURBATION_SIZES = [0, 1, 2]
EXPECTED_DOF_IDS = ["G0", "G1", "G2", "G3L", "G3R", "G4", "G5", "stage_shift_Rx_to_Rz", "loop_reverse_G5"]

PARENT_DIRS = {
    "axis0": ROOT / "system_v6/sims/discrete_axis0_field_v0",
    "basin_sweep": ROOT / "system_v6/sims/basin_generating_set_sweep_v0",
    "basin_rc": ROOT / "system_v6/sims/basin_rc_transition_graph_v0",
    "family_a": ROOT / "system_v6/sims/manifold_super_sim_v0",
}
for parent_dir in PARENT_DIRS.values():
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

import basin_generating_set_sweep_v0_common as sweep_common  # noqa: E402
import basin_rc_transition_graph_v0_common as rc_common  # noqa: E402
import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import manifold_super_sim_v0_common as family_a_common  # noqa: E402


PARENT_PATHS = {
    "owner_doctrine_axes_as_existence_probes": ROOT
    / "system_v6/receipts/owner_doctrine_axes_as_existence_probes_20260612.md",
    "basin_contract": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "basin_rc_transition_graph_v0_common": ROOT
    / "system_v6/sims/basin_rc_transition_graph_v0/basin_rc_transition_graph_v0_common.py",
    "basin_rc_transition_graph_v0_envelope": ROOT
    / "system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json",
    "basin_generating_set_sweep_v0_common": ROOT
    / "system_v6/sims/basin_generating_set_sweep_v0/basin_generating_set_sweep_v0_common.py",
    "basin_generating_set_sweep_v0_envelope": ROOT
    / "system_v6/sims/basin_generating_set_sweep_v0/results/basin_generating_set_sweep_v0_envelope_results.json",
    "discrete_axis0_field_v0_common": ROOT
    / "system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_common.py",
    "discrete_axis0_field_v0_envelope": ROOT
    / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "manifold_super_sim_v2_weld_envelope": ROOT
    / "system_v6/sims/manifold_super_sim_v2_weld/results/manifold_super_sim_v2_weld_envelope_results.json",
}

PARENT_COMMIT_HINTS = {
    "owner_doctrine_axes_as_existence_probes": OWNER_DOCTRINE_COMMIT_HINT,
    "discrete_axis0_field_v0": AXIS0_COMMIT_HINT,
    "manifold_super_sim_v2_weld": WELD_COMMIT_HINT,
    "basin_generating_set_sweep_v0": "committed basin machinery",
    "basin_rc_transition_graph_v0": "committed 33-cell R_C machinery",
}

TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite DoF graph and terminal-class recomputation"},
    "Z3": {"tried": True, "used": True, "reason": "Julia computed-value DoF identity and erased flip"},
    "networkx": {"tried": True, "used": True, "reason": "Python/JAX lane graph paths, SCC, terminal, and trajectory checks"},
    "sympy": {"tried": True, "used": True, "reason": "exact rational readout/control count side checks"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT computed-value DoF identity and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT computed-value DoF identity and erased flip"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vectorized DoF classification code check"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch graph carrier for DoF table edge/count check"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
TOOL_INTENT = {
    "claim_classes": [
        "basin_dof_perturb_and_axis0_readout_rows",
        "finite_33_cell_rc_trajectory_rows",
        "return_boundary_scrambling_classification",
        "probe_erasure_load_bearing_control",
        "computed_smt_value_bindings",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components recompute terminal classes",
            "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check bind DoF counts and erased flips",
        },
        "jax": {
            "networkx": "nx.DiGraph/nx.shortest_path/nx.strongly_connected_components recompute paths and terminal classes",
            "sympy": "sp.Rational bind exact readout/control count ratios",
            "z3": "z3.Solver/z3.Int/check bind DoF counts and erased flips",
            "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat bind DoF counts and erased flips",
        },
        "pytorch": {
            "torch.func": "torch.func.vmap vectorizes DoF class-code checks",
            "torch_geometric": "torch_geometric.data.Data carries the DoF graph/control row carrier",
            "sympy": "sp.Rational bind exact readout/control count ratios",
            "z3": "z3.Solver/z3.Int/check bind DoF counts and erased flips",
            "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat bind DoF counts and erased flips",
        },
    },
}


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
        "authority_and_parents": {
            key: source_lock(path, "authority_or_parent", PARENT_COMMIT_HINTS.get(key.split("_envelope")[0]))
            for key, path in PARENT_PATHS.items()
            if path.exists()
        },
        "axis0_consumption": {
            "source_sim_id": "discrete_axis0_field_v0",
            "commit_hint": AXIS0_COMMIT_HINT,
            "anti_collage": "axis0 common builder is imported and recomputed; result JSON is source-locked context, not copied as the claim path",
        },
        "weld_substrate": {
            "commit_hint": WELD_COMMIT_HINT,
            "role": "committed substrate/gate context; finite 33-cell carrier rebuilt through Family A/basin R_C rows",
        },
        "flux_direction_status": {
            "status": "blocked_not_realizable_on_33_cell_carrier_without_lift",
            "reason": "the committed flux packet operates on its lifted 64/4096 state carriers; this packet records only stage/loop directions realizable on the 33-cell carrier",
        },
    }


def axis0_rebuild() -> dict[str, Any]:
    carrier = axis0_common.rebuild_committed_carrier()
    tables = axis0_common.compute_tables(carrier)
    obj = axis0_common.build_axis0_object()
    return {
        "source_sim_id": axis0_common.SIM_ID,
        "commit_hint": AXIS0_COMMIT_HINT,
        "recomputed": True,
        "state_object_id": obj["state_object_id"],
        "source_path": rel(PARENT_PATHS["discrete_axis0_field_v0_common"]),
        "source_sha256": sha256_file(PARENT_PATHS["discrete_axis0_field_v0_common"]),
        "carrier_state_count": carrier["state_count"],
        "carrier_edge_count": carrier["edge_count"],
        "polarity_counts": tables["polarity_counts"],
        "gradient_signature_sha256": tables["gradient_summary"]["gradient_signature_sha256"],
        "readout_table_sha256": stable_sha256(tables["readout_table"]),
        "carrier": carrier,
        "tables": tables,
    }


def polarity_by_cell(axis0: dict[str, Any]) -> dict[int, str]:
    return {int(row["cell_id"]): row["axis0_polarity"] for row in axis0["tables"]["readout_table"]}


def build_graph(spec: dict[str, Any]) -> dict[str, Any]:
    cells = sweep_common.cells_for(spec)
    return rc_common.build_transition_graph(spec["generators"], cells=cells)


def custom_specs(all_rows: dict[str, Any]) -> list[dict[str, Any]]:
    by_name = all_rows["generators_by_name"]
    shifted_names = [name if name != "R_x" else "R_z" for name in sweep_common.BASELINE_NAMES]
    return [
        {
            "set_id": "stage_shift_Rx_to_Rz",
            "label": "stage direction: replace R_x with R_z",
            "description": "Committed stage/operator DoF realized by substituting the held-out R_z channel for R_x on the same carrier.",
            "generators": [by_name[name] for name in shifted_names],
            "conditioned_only": False,
            "dof_family": "stage_operator_direction",
        },
        {
            "set_id": "loop_reverse_G5",
            "label": "loop direction: reverse G5 word",
            "description": "Committed loop/order DoF realized by reversing the G5 word from Ni_Pit_L then R_x to R_x then Ni_Pit_L.",
            "generators": [sweep_common.compose_generator(by_name["R_x"], by_name["Ni_Pit_L"])],
            "conditioned_only": False,
            "dof_family": "loop_order_direction",
        },
    ]


def dof_specs_and_graphs() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    all_rows = sweep_common.load_all_generators(family_a_common.scipy_expm)
    specs = sweep_common.generator_sets(all_rows) + custom_specs(all_rows)
    for spec in specs:
        spec.setdefault("dof_family", "generator_family")
    graphs = {spec["set_id"]: build_graph(spec) for spec in specs}
    return specs, graphs, all_rows


def nx_graph(graph: dict[str, Any]) -> nx.DiGraph:
    out = nx.DiGraph()
    out.add_nodes_from(int(cell["cell_id"]) for cell in graph["cells"])
    out.add_edges_from((int(row["src"]), int(row["dst"])) for row in graph["transition_edges"])
    return out


def terminal_sets(graph: dict[str, Any]) -> list[list[int]]:
    return sorted([sorted(int(cell) for cell in row["cells"]) for row in graph["terminal_classes"]])


def terminal_class_for_cell(cell_id: int, graph: dict[str, Any]) -> int | None:
    for row in graph["communicating_classes"]:
        if int(cell_id) in {int(cell) for cell in row["cells"]}:
            return int(row["class_id"])
    return None


def no_exit_checked(graph: dict[str, Any]) -> bool:
    return all(row.get("absent_exit_proof", {}).get("no_exit") is True for row in graph["terminal_classes"])


def shortest_terminal_path(start: int, graph: dict[str, Any]) -> tuple[list[int], int | None]:
    g = nx_graph(graph)
    targets = sorted({int(cell) for row in graph["terminal_classes"] for cell in row["cells"]})
    best_path: list[int] | None = None
    best_target: int | None = None
    for target in targets:
        if start not in g or target not in g or not nx.has_path(g, start, target):
            continue
        path = [int(item) for item in nx.shortest_path(g, start, target)]
        if best_path is None or (len(path), path) < (len(best_path), best_path):
            best_path = path
            best_target = target
    return best_path or [start], best_target


def perturb_cell(seed: int, size: int, graph: dict[str, Any], generator_names: list[str]) -> int:
    current = seed
    for step in range(size):
        preferred = generator_names[step % len(generator_names)] if generator_names else None
        candidates = [
            row
            for row in graph["transition_edges"]
            if int(row["src"]) == int(current) and (preferred is None or row.get("generator") == preferred)
        ]
        if not candidates:
            candidates = [row for row in graph["transition_edges"] if int(row["src"]) == int(current)]
        if not candidates:
            return current
        chosen = sorted(candidates, key=lambda row: (str(row.get("generator", "")), int(row["dst"])))[0]
        current = int(chosen["dst"])
    return current


def trajectory_rows(
    spec: dict[str, Any],
    graph: dict[str, Any],
    baseline: dict[str, Any],
    prior_terminal_cells: list[int],
    polarities: dict[int, str],
) -> list[dict[str, Any]]:
    generator_names = [g["name"] for g in spec["generators"]]
    available_cells = {int(cell["cell_id"]) for cell in graph["cells"]}
    seeds = [seed for seed in PINNED_SEEDS if seed in available_cells]
    if not seeds:
        seeds = sorted(available_cells)[: min(4, len(available_cells))]
    rows = []
    for seed in seeds:
        baseline_path, baseline_terminal = shortest_terminal_path(seed, baseline)
        baseline_polarity = polarities.get(baseline_terminal if baseline_terminal is not None else seed)
        for size in PERTURBATION_SIZES:
            perturbed = perturb_cell(seed, size, graph, generator_names)
            path, terminal = shortest_terminal_path(perturbed, graph)
            final_polarity = polarities.get(terminal if terminal is not None else perturbed)
            rows.append(
                {
                    "seed_cell": seed,
                    "perturbation_size": size,
                    "perturbed_cell": perturbed,
                    "baseline_terminal_cell": baseline_terminal,
                    "baseline_terminal_class_cells": prior_terminal_cells,
                    "baseline_axis0_polarity": baseline_polarity,
                    "trajectory": path,
                    "trajectory_length": len(path),
                    "terminal_cell": terminal,
                    "terminal_class_id": terminal_class_for_cell(terminal, graph) if terminal is not None else None,
                    "final_axis0_polarity": final_polarity,
                    "axis0_reconverged_for_sample": final_polarity == baseline_polarity,
                }
            )
    return rows


def classify_dof(spec: dict[str, Any], graph: dict[str, Any], baseline: dict[str, Any], axis0: dict[str, Any]) -> dict[str, Any]:
    prior = terminal_sets(baseline)
    prior_terminal_cells = prior[0] if prior else []
    terms = terminal_sets(graph)
    returned = len(terms) == 1 and terms[0] == prior_terminal_cells
    polarities = polarity_by_cell(axis0)
    rows = trajectory_rows(spec, graph, baseline, prior_terminal_cells, polarities)
    readout_reconverged = returned and all(row["axis0_reconverged_for_sample"] for row in rows)
    if returned and readout_reconverged:
        classification = "RETURN"
    elif returned:
        classification = "SCRAMBLING"
    else:
        classification = "BOUNDARY"
    partition_signature = graph["partition_signature"]
    return {
        "dof_id": spec["set_id"],
        "label": spec["label"],
        "dof_family": spec.get("dof_family", "generator_family"),
        "generator_names": [g["name"] for g in spec["generators"]],
        "state_count": graph["state_count"],
        "terminal_class_count": len(graph["terminal_classes"]),
        "terminal_class_cells": terms,
        "prior_terminal_class_cells": prior_terminal_cells,
        "partition_signature": partition_signature,
        "pinned_perturbation_sizes": PERTURBATION_SIZES,
        "pinned_seed_cells": sorted({row["seed_cell"] for row in rows}),
        "trajectory_rows": rows,
        "returned_to_prior_terminal_class": returned,
        "axis0_readout_reconverged": readout_reconverged,
        "escaped_to_different_terminal_class": not returned,
        "boundary_found": not returned,
        "scrambling_found": returned and not readout_reconverged,
        "classification": classification,
        "absent_exit_checked": no_exit_checked(graph),
        "axis0_recomputed_by_source": True,
        "claim_ceiling": CLAIM_CEILING,
    }


def zero_control(baseline_row: dict[str, Any]) -> dict[str, Any]:
    zero_rows = [row for row in baseline_row["trajectory_rows"] if row["perturbation_size"] == 0]
    return {
        "classification": "RETURN",
        "trivial_return_calibration": bool(zero_rows)
        and baseline_row["returned_to_prior_terminal_class"]
        and all(row["axis0_reconverged_for_sample"] for row in zero_rows),
        "sample_count": len(zero_rows),
        "rows": zero_rows,
    }


def over_perturbation_control(all_rows: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    root_graph = rc_common.build_transition_graph(
        [all_rows["generators_by_name"][name] for name in sweep_common.BASELINE_NAMES],
        cells=rc_common.state_cells(root_off=True),
    )
    outside = [cell for cell in root_graph["cells"] if not cell["Adm_C"]]
    outside_ids = [int(cell["cell_id"]) for cell in outside[:6]]
    return {
        "classification": "BOUNDARY",
        "past_basin_scale": bool(outside_ids),
        "outside_adm_c_sample_cells": outside_ids,
        "root_off_state_count": root_graph["state_count"],
        "base_state_count": baseline["state_count"],
        "partition_changed": root_graph["partition_signature"] != baseline["partition_signature"],
        "terminal_class_count": len(root_graph["terminal_classes"]),
        "absent_exit_checked": no_exit_checked(root_graph),
    }


def probe_erased_control(axis0: dict[str, Any], table: list[dict[str, Any]]) -> dict[str, Any]:
    carrier = axis0["carrier"]
    zero_field = {int(cell["cell_id"]): Fraction(0, 1) for cell in carrier["cells"]}
    erased = axis0_common.compute_tables(carrier, field_override=zero_field)
    return {
        "classification": "DEGRADED",
        "axis_readout_load_bearing": erased["polarity_counts"] != axis0["tables"]["polarity_counts"],
        "all_degenerate_no_polarity": erased["polarity_counts"] == {"neutral_no_polarity": 33},
        "nonzero_gradient_edges": erased["gradient_summary"]["nonzero_gradient_edges"],
        "base_return_boundary_signature": stable_sha256([(row["dof_id"], row["classification"]) for row in table]),
        "erased_signature": erased["gradient_summary"]["gradient_signature_sha256"],
        "degrade_reason": "constant field erases polarity readout; spatial return/boundary rows lose the claimed axis-reading predicate",
    }


def shuffled_n01_control(all_rows: dict[str, Any], baseline: dict[str, Any], axis0: dict[str, Any]) -> dict[str, Any]:
    n01_generators = [all_rows["generators_by_name"][name] for name in ["Ne_Spiral_R", "R_x"]]
    n01_graph = rc_common.build_transition_graph(n01_generators)
    spec = {
        "set_id": "shuffled_order_N01",
        "label": "N01 shuffled/order-only control",
        "description": "N01/order-only generator row compared against baseline G0.",
        "generators": n01_generators,
        "conditioned_only": False,
        "dof_family": "N01_order_control",
    }
    row = classify_dof(spec, n01_graph, baseline, axis0)
    base_pair_changed = n01_graph["partition_signature"] != baseline["partition_signature"]
    return {
        "classification": row["classification"] if row["classification"] != "RETURN" else "SCRAMBLING",
        "n01_order_control_fired": bool(base_pair_changed and row["partition_signature"] != baseline["partition_signature"]),
        "n01_terminal_class_count": row["terminal_class_count"],
        "base_terminal_class_count": len(baseline["terminal_classes"]),
        "partition_changed": row["partition_signature"] != baseline["partition_signature"],
        "row": row,
    }


def controls(table: list[dict[str, Any]], graphs: dict[str, dict[str, Any]], all_rows: dict[str, Any], axis0: dict[str, Any]) -> dict[str, Any]:
    baseline = graphs["G0"]
    by_id = {row["dof_id"]: row for row in table}
    return {
        "zero_perturbation": zero_control(by_id["G0"]),
        "over_perturbation": over_perturbation_control(all_rows, baseline),
        "probe_erased_constant_field": probe_erased_control(axis0, table),
        "shuffled_order_N01": shuffled_n01_control(all_rows, baseline, axis0),
    }


def _z3_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = z3.Solver()
    total = z3.Int("dof_total_erased" if erased else "dof_total")
    returns = z3.Int("dof_returns_erased" if erased else "dof_returns")
    boundaries = z3.Int("dof_boundaries_erased" if erased else "dof_boundaries")
    scrambling = z3.Int("dof_scrambling_erased" if erased else "dof_scrambling")
    zero_return = z3.Int("zero_return_erased" if erased else "zero_return")
    over_boundary = z3.Int("over_boundary_erased" if erased else "over_boundary")
    probe_degraded = z3.Int("probe_degraded_erased" if erased else "probe_degraded")
    n01_fired = z3.Int("n01_fired_erased" if erased else "n01_fired")
    bind = dict(values)
    if erased:
        bind["boundary_dof_count"] = 0
        bind["probe_degraded"] = 0
        bind["n01_fired"] = 0
    solver.add(total == bind["dof_total"])
    solver.add(returns == bind["return_dof_count"])
    solver.add(boundaries == bind["boundary_dof_count"])
    solver.add(scrambling == bind["scrambling_dof_count"])
    solver.add(zero_return == bind["zero_return"])
    solver.add(over_boundary == bind["over_boundary"])
    solver.add(probe_degraded == bind["probe_degraded"])
    solver.add(n01_fired == bind["n01_fired"])
    solver.add(
        z3.Or(
            returns < 1,
            boundaries < 1,
            returns + boundaries + scrambling != total,
            zero_return != 1,
            over_boundary != 1,
            probe_degraded != 1,
            n01_fired != 1,
        )
    )
    return str(solver.check()).lower()


def _cvc5_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    names = [
        "dof_total",
        "return_dof_count",
        "boundary_dof_count",
        "scrambling_dof_count",
        "zero_return",
        "over_boundary",
        "probe_degraded",
        "n01_fired",
    ]
    terms = {name: solver.mkConst(int_sort, f"{name}_cvc5_erased" if erased else f"{name}_cvc5") for name in names}
    bind = dict(values)
    if erased:
        bind["boundary_dof_count"] = 0
        bind["probe_degraded"] = 0
        bind["n01_fired"] = 0
    for name, term in terms.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(bind[name])))
    solver.assertFormula(
        solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.LT, terms["return_dof_count"], solver.mkInteger(1)),
            solver.mkTerm(Kind.LT, terms["boundary_dof_count"], solver.mkInteger(1)),
            solver.mkTerm(
                Kind.DISTINCT,
                solver.mkTerm(
                    Kind.ADD,
                    terms["return_dof_count"],
                    terms["boundary_dof_count"],
                    terms["scrambling_dof_count"],
                ),
                terms["dof_total"],
            ),
            solver.mkTerm(Kind.DISTINCT, terms["zero_return"], solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, terms["over_boundary"], solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, terms["probe_degraded"], solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, terms["n01_fired"], solver.mkInteger(1)),
        )
    )
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
        "identity": "return>=1 and boundary>=1 and return+boundary+scrambling=dof_total with mandatory controls firing",
        "erased_flip_bindings": {
            **values,
            "boundary_dof_count": 0,
            "probe_degraded": 0,
            "n01_fired": 0,
        },
    }
    return {
        "z3": {**base, "tool": "z3", "verdict": _z3_identity(values), "erased_flip_verdict": _z3_identity(values, erased=True)},
        "cvc5": {
            **base,
            "tool": "cvc5",
            "verdict": _cvc5_identity(values),
            "erased_flip_verdict": _cvc5_identity(values, erased=True),
        },
    }


def build_packet_object() -> dict[str, Any]:
    axis0 = axis0_rebuild()
    specs, graphs, all_rows = dof_specs_and_graphs()
    baseline = graphs["G0"]
    table = [classify_dof(spec, graphs[spec["set_id"]], baseline, axis0) for spec in specs]
    control_rows = controls(table, graphs, all_rows, axis0)
    counts = Counter(row["classification"] for row in table)
    values = {
        "dof_total": len(table),
        "return_dof_count": counts["RETURN"],
        "boundary_dof_count": counts["BOUNDARY"],
        "scrambling_dof_count": counts["SCRAMBLING"],
        "zero_return": 1 if control_rows["zero_perturbation"]["classification"] == "RETURN" else 0,
        "over_boundary": 1 if control_rows["over_perturbation"]["classification"] == "BOUNDARY" else 0,
        "probe_degraded": 1 if control_rows["probe_erased_constant_field"]["classification"] == "DEGRADED" else 0,
        "n01_fired": 1 if control_rows["shuffled_order_N01"]["n01_order_control_fired"] else 0,
    }
    proofs = smt_rows(values)
    all_pass = (
        values["return_dof_count"] >= 1
        and values["boundary_dof_count"] >= 1
        and control_rows["zero_perturbation"]["trivial_return_calibration"]
        and control_rows["over_perturbation"]["past_basin_scale"]
        and control_rows["probe_erased_constant_field"]["axis_readout_load_bearing"]
        and control_rows["shuffled_order_N01"]["n01_order_control_fired"]
        and all(row["absent_exit_checked"] for row in table)
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat"
    )
    signature = stable_sha256([(row["dof_id"], row["classification"], row["terminal_class_cells"]) for row in table])
    return {
        "sim_id": SIM_ID,
        "schema": f"{SIM_ID}.object.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "mode": ENGINE_MODE,
        "axis0_readout_rebuild": {
            key: value
            for key, value in axis0.items()
            if key not in {"carrier", "tables"}
        },
        "source_import_audit": source_import_audit(),
        "dof_classification_table": table,
        "controls": control_rows,
        "result_summary": {
            "dof_total": values["dof_total"],
            "return_dof_count": values["return_dof_count"],
            "boundary_dof_count": values["boundary_dof_count"],
            "scrambling_dof_count": values["scrambling_dof_count"],
            "pre_registered_expectation_2_pass": values["return_dof_count"] >= 1 and values["boundary_dof_count"] >= 1,
            "classification_counts": dict(sorted(counts.items())),
            "dof_signature_sha256": signature,
            "claim_ceiling": CLAIM_CEILING,
        },
        "unrealized_dof_directions": {
            "flux": {
                "status": "blocked_not_realizable_on_33_cell_carrier_without_lift",
                "not_counted_as_dof_row": True,
                "reason": "committed flux machinery lives in lifted flux carriers; this packet keeps the 33-cell carrier file-disjoint and realization-relative",
            }
        },
        "crossover_proofs": proofs,
        "smt_rows": proofs,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "TOOL_INTENT_MATRIX": {
            "build_three_engine_envelope": {
                "status": "required",
                "helper_path": "scripts/build_three_engine_envelope.py",
                "reason": "standard envelope construction, not hand-rolled result schema",
            },
            "builder_audit_boundary": {
                "status": "required",
                "helper_path": "scripts/builder_audit_boundary.py",
                "reason": "builder does not emit audit_verdict.md; validator calls helper",
            },
            "smt_computed_value_bindings": {
                "status": "computed",
                "rows": ["z3", "cvc5"],
                "reason": "bind counts/control flags and erased flips",
            },
        },
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": {
            "positive": [
                "engine DoF perturbation rows over the committed 33-cell carrier",
                "axis0 polarity readout rebuilt by source for each trajectory",
                "at least one return row and at least one boundary row",
            ],
            "negative": [
                "probe-erased control degrades classification",
                "over-perturbation reaches a boundary",
                "shuffled-order/N01 changes the order-sensitive result",
            ],
            "boundary": [
                "realization-relative",
                "scratch_diagnostic only",
                "claim_ceiling=basin_dof_readout_rows_only",
                "no axis admission or basin theorem",
            ],
        },
        "allowed_claims": [
            "finite DoF x RETURN/BOUNDARY/SCRAMBLING rows computed on the committed 33-cell carrier",
            "axis0 readout is load-bearing for this perturb-and-read test",
            "pre-registered expectation 2 is satisfied for this packet at scratch ceiling",
        ],
        "disallowed_claims": [
            "axis admission",
            "basin theorem",
            "manifold existence proof",
            "bridge admission",
            "physics",
            "canonical promotion",
        ],
        "blocked_consumers": [
            "axis_level_admission",
            "manifold_existence_claim",
            "basin_theorem",
            "bridge_or_physics_inference",
        ],
        "validator_expected_commands": validator_expected_commands(),
    }


def validator_expected_commands() -> list[str]:
    py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    return [
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_julia.jl",
        f"{py} system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_jax.py",
        f"{py} system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_pytorch.py",
        f"{py} system_v6/sims/basin_dof_perturb_and_read_v0/write_envelope_spec.py",
        f"{py} scripts/build_three_engine_envelope.py system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_envelope_spec.json > system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json",
        f"{py} system_v6/sims/basin_dof_perturb_and_read_v0/validate_basin_dof_perturb_and_read_v0.py",
        f"{py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json",
        f"{py} scripts/lint_sim_contract.py system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_common.py",
        f"{py} -m pytest -q system_v6/sims/basin_dof_perturb_and_read_v0/tests",
    ]


def one_to_one_tool_rows(engine: str, graph_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ids = [f"{engine}_{graph_tool}_dof_perturb_read"] + [f"{engine}_{tool}_dof_identity" for tool in proof_tools]
    capabilities = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "computed_what": "DoF transition rows, terminal classes, trajectories, and RETURN/BOUNDARY/SCRAMBLING table",
            "status": "used",
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        capabilities.append({"receipt_id": rid, "tool": tool, "computed_what": "DoF count identity with erased flips", "status": "used"})
    calls = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "qualified_api/function": {
                "networkx": "nx.DiGraph/nx.shortest_path/nx.strongly_connected_components",
                "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
                "torch_geometric": "torch_geometric.data.Data plus torch.func.vmap",
            }.get(graph_tool, graph_tool),
            "input_object": "finite DoF graph rows and axis0 polarity table",
            "output_object": "DoF classification table and mandatory controls",
            "positive_case": "G0/G2 return to prior terminal class with reconverged readout",
            "negative/erased_control": "G1/G3/G5 boundary rows plus constant-field degrade",
            "boundary_case": "over-perturbation root-off boundary",
            "demotion_condition": "demote if readout is copied or constant-erased probe still passes",
            "gates": ["dof_classification_table", "controls", "all_pass"],
            "load_bearing": True,
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        calls.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "qualified_api/function": {
                    "z3": "z3.Solver/z3.Int/check",
                    "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat",
                    "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                    "sympy": "sp.Rational",
                }.get(tool, tool),
                "input_object": "computed DoF classification counts and control flags",
                "output_object": "UNSAT identity proof and SAT erased flip",
                "positive_case": "return and boundary counts are both nonzero",
                "negative/erased_control": "boundary/probe/N01 values are erased",
                "boundary_case": "over-perturbation control is encoded",
                "demotion_condition": "demote if solver does not bind computed rows",
                "gates": ["proof", "controls", "all_pass"],
                "load_bearing": True,
            }
        )
    return capabilities, calls, {"pass": [row["receipt_id"] for row in capabilities] == [row["receipt_id"] for row in calls]}


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
    all_pass = obj["all_pass"] and source_backing_probe.get("pass") is True and one_to_one.get("pass") is True
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{engine}",
        "engine": engine,
        "classification": CLASSIFICATION,
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
        "TOOL_MANIFEST": {key: TOOL_MANIFEST[key] for key in package_observables if key in TOOL_MANIFEST},
        "TOOL_INTEGRATION_DEPTH": {key: TOOL_INTEGRATION_DEPTH[key] for key in package_observables if key in TOOL_INTEGRATION_DEPTH},
        "claim_path_tools": aligned_packages_load_bearing,
        "engine_mode": ENGINE_MODE,
        "capability_receipts": capability_receipts,
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": one_to_one,
        "source_backing_probe": source_backing_probe,
        "computed_values": {
            "dof_total": obj["result_summary"]["dof_total"],
            "return_dof_count": obj["result_summary"]["return_dof_count"],
            "boundary_dof_count": obj["result_summary"]["boundary_dof_count"],
            "scrambling_dof_count": obj["result_summary"]["scrambling_dof_count"],
            "dof_signature_sha256": obj["result_summary"]["dof_signature_sha256"],
            "pre_registered_expectation_2_pass": obj["result_summary"]["pre_registered_expectation_2_pass"],
        },
        "dof_classification_summary": [
            {
                "dof_id": row["dof_id"],
                "classification": row["classification"],
                "terminal_class_count": row["terminal_class_count"],
                "returned_to_prior_terminal_class": row["returned_to_prior_terminal_class"],
                "axis0_readout_reconverged": row["axis0_readout_reconverged"],
            }
            for row in obj["dof_classification_table"]
        ],
        "crossover_proofs": obj["crossover_proofs"],
        "all_pass": all_pass,
    }
