#!/usr/bin/env python3
"""Build the current tool -> function/API -> receipt matrix.

This is a receipt index, not an admission or promotion surface. It records the
fresh bounded tool-function wave and its exact claim ceiling.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "system_v5" / "evidence" / "tool_function_receipt_matrix.json"
OUT_MD = ROOT / "system_v5" / "docs" / "TOOL_FUNCTION_RECEIPT_MATRIX.md"


TARGETS: list[dict[str, Any]] = [
    {
        "tool": "pytorch",
        "function_api": "torch.autograd.grad/backward, torch.nn.Module, torch.matmul/tensor shape ops",
        "receipt": "system_v4/probes/a2_state/sim_results/pytorch_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["density_matrix_representability", "operator_family_admission"],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.nn.GCNConv MessagePassing over Hopf-fiber edge_index",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_pyg_hopf_graph_deep_capability_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_shell_geometry", "werner_local_structure"],
    },
    {
        "tool": "pyg",
        "function_api": "torch_geometric.nn.MessagePassing.propagate directed additive aggregation",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_e3nn_pyg_equivariance_under_mp_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_cell_complex_geometry", "operator_family_admission"],
    },
    {
        "tool": "qutip",
        "function_api": "qutip.basis, ket2dm, sigmax/sigmaz expectation",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_capability_results.json",
        "role": "bridge_useful",
        "depth": "load_bearing",
        "candidate_lego_targets": ["channel_cptp_map", "lindbladian_evolution"],
    },
    {
        "tool": "qutip",
        "function_api": "qutip.mesolve Lindblad open-system evolution",
        "receipt": "system_v4/probes/a2_state/sim_results/qutip_open_system_bridge_results.json",
        "role": "classical_baseline",
        "depth": "load_bearing",
        "candidate_lego_targets": ["lindbladian_evolution", "channel_cptp_map"],
    },
    {
        "tool": "qiskit",
        "function_api": "QuantumCircuit, Statevector, DensityMatrix, Operator expectation_value",
        "receipt": "system_v4/probes/a2_state/sim_results/qiskit_capability_results.json",
        "role": "bridge_useful",
        "depth": "load_bearing",
        "candidate_lego_targets": ["unitary_channel_map", "density_matrix_object"],
    },
    {
        "tool": "clifford",
        "function_api": "Cl(3)/Cl(6) layout blades, rotor products, grade/scalar extraction",
        "receipt": "system_v4/probes/a2_state/sim_results/clifford_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["clifford_generator_basis", "clifford_geometry"],
    },
    {
        "tool": "gudhi",
        "function_api": "SimplexTree, Rips/filtration persistence and Betti summaries",
        "receipt": "system_v4/probes/a2_state/sim_results/gudhi_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["persistence_geometry", "concurrence_measure"],
    },
    {
        "tool": "toponetx",
        "function_api": "CellComplex/SimplicialComplex rank cells and incidence_matrix",
        "receipt": "system_v4/probes/a2_state/sim_results/toponetx_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["state_class_binding_geometry", "cell_complex_geometry"],
    },
    {
        "tool": "toponetx",
        "function_api": "CellComplex rank-2 cell incidence_matrix(2)",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_xgi_toponetx_higher_order_incidence_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["cell_complex_geometry", "hypergraph_shell_geometry"],
    },
    {
        "tool": "xgi",
        "function_api": "xgi.Hypergraph hyperedge membership and shared incidence intersection",
        "receipt": "system_v4/probes/a2_state/sim_results/xgi_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hypergraph_shell_geometry", "dual_hypergraph_geometry"],
    },
    {
        "tool": "xgi",
        "function_api": "XGI hyperedge incidence matched to TopoNetX rank-2 cells",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_xgi_toponetx_higher_order_incidence_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["hypergraph_shell_geometry", "cell_complex_geometry"],
    },
    {
        "tool": "rustworkx",
        "function_api": "rustworkx PyDiGraph DAG construction, topological_sort, transitive_reduction, dijkstra_shortest_paths, cycle detection",
        "receipt": "system_v4/probes/a2_state/sim_results/rustworkx_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["graph_shell_geometry", "dependency_dag_and_collapse"],
    },
    {
        "tool": "z3",
        "function_api": "z3 Solver/SolverFor QF_LIA add/check/model and UNSAT witness",
        "receipt": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "distinguishability_relation"],
    },
    {
        "tool": "z3",
        "function_api": "z3 SolverFor('QF_LIA') shared SAT/UNSAT agreement fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_cvc5_z3_unsat_agreement_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "probe_object"],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 Solver.assertFormula/checkSat/getValue QF_LIA fixture",
        "receipt": "system_v4/probes/a2_state/sim_results/cvc5_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "carrier_admission_density_matrix"],
    },
    {
        "tool": "cvc5",
        "function_api": "cvc5 shared QF_LIA SAT/UNSAT agreement with z3",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_cvc5_z3_unsat_agreement_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["constraint_probe_admissibility", "probe_object"],
    },
    {
        "tool": "sympy",
        "function_api": "sympy symbolic expression/matrix simplification and exact algebra",
        "receipt": "system_v4/probes/a2_state/sim_results/sympy_capability_results.json",
        "role": "classical_bridge",
        "depth": "load_bearing",
        "candidate_lego_targets": ["entropy_family_crosschecks", "operator_family_admission"],
    },
    {
        "tool": "geomstats",
        "function_api": "geomstats metric.geodesic, exp/log, SPD distance, Frechet mean",
        "receipt": "system_v4/probes/a2_state/sim_results/geomstats_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["geometry_crosschecks_same_carrier", "quantum_metric_nonuniqueness"],
    },
    {
        "tool": "e3nn",
        "function_api": "e3nn.o3.Irreps and D_from_matrix vector representation",
        "receipt": "system_v4/probes/a2_state/sim_results/e3nn_capability_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["operator_family_admission", "graph_cell_complex_geometry"],
    },
    {
        "tool": "e3nn",
        "function_api": "e3nn vector irrep action commuting with PyG MessagePassing.propagate",
        "receipt": "system_v4/probes/a2_state/sim_results/sim_integration_e3nn_pyg_equivariance_under_mp_micro_results.json",
        "role": "nonclassical_adjacent",
        "depth": "load_bearing",
        "candidate_lego_targets": ["operator_family_admission", "graph_cell_complex_geometry"],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - report path is the point
        return {"_load_error": str(exc)}
    return data if isinstance(data, dict) else {"_non_object": True}


def all_pass(payload: dict[str, Any]) -> bool:
    if payload.get("all_pass") is True or payload.get("overall_pass") is True:
        return True
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return bool(summary.get("all_pass") or summary.get("passed") == summary.get("total"))
    return False


def result_classification(payload: dict[str, Any]) -> str | None:
    value = payload.get("classification")
    return str(value) if value is not None else None


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in TARGETS:
        path = ROOT / target["receipt"]
        payload = load_json(path)
        manifest = payload.get("tool_manifest") if isinstance(payload.get("tool_manifest"), dict) else {}
        depth = payload.get("tool_integration_depth") if isinstance(payload.get("tool_integration_depth"), dict) else {}
        tool = target["tool"]
        rows.append(
            {
                **target,
                "receipt_exists": path.exists(),
                "receipt_all_pass": all_pass(payload),
                "receipt_classification": result_classification(payload),
                "receipt_schema": payload.get("schema"),
                "manifest_reason": (manifest.get(tool) or {}).get("reason") if isinstance(manifest.get(tool), dict) else None,
                "observed_depth": depth.get(tool),
                "boundary_source": "receipt" if payload.get("claim_ceiling") or payload.get("out_of_scope") else "matrix_default",
                "boundary_gap": not (payload.get("claim_ceiling") and payload.get("out_of_scope")),
                "claim_ceiling": payload.get("claim_ceiling") or "tool_function_receipt_only_not_admission_or_promotion",
                "out_of_scope": payload.get("out_of_scope") or [
                    "no QIT admission",
                    "no GStack admission",
                    "no axis admission",
                    "no bridge or engine claim",
                    "no scientific lego coupling promotion",
                ],
            }
        )
    return rows


def write_markdown(rows: list[dict[str, Any]], generated_at: str) -> None:
    lines = [
        "# Tool Function Receipt Matrix",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Boundary: receipt index only. This does not admit, promote, or validate a lego, coupling, bridge, axis, GStack, QIT, or engine claim.",
        "",
        "## Summary",
        "",
        f"- Rows: `{len(rows)}`",
        f"- Passing rows: `{sum(1 for row in rows if row['receipt_all_pass'])}`",
        f"- Missing receipts: `{sum(1 for row in rows if not row['receipt_exists'])}`",
        "",
        "## Matrix",
        "",
        "| tool | exact function/API surface | receipt | classification | role | depth | pass | candidate lego targets |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        targets = ", ".join(f"`{item}`" for item in row["candidate_lego_targets"])
        lines.append(
            f"| `{row['tool']}` | {row['function_api']} | `{row['receipt']}` | "
            f"`{row['receipt_classification']}` | `{row['role']}` | `{row['observed_depth'] or row['depth']}` | "
            f"`{row['receipt_all_pass']}` | {targets} |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows()
    payload = {
        "schema": "tool_function_receipt_matrix.v1",
        "generated_at": generated_at,
        "boundary": "receipt_index_only_not_admission_or_promotion",
        "summary": {
            "row_count": len(rows),
            "passing_count": sum(1 for row in rows if row["receipt_all_pass"]),
            "missing_receipt_count": sum(1 for row in rows if not row["receipt_exists"]),
            "receipt_boundary_gap_count": sum(1 for row in rows if row["boundary_gap"]),
            "receipt_schema_missing_count": sum(1 for row in rows if row["receipt_schema"] is None),
            "tools": sorted({row["tool"] for row in rows}),
        },
        "rows": rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(rows, generated_at)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["missing_receipt_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
