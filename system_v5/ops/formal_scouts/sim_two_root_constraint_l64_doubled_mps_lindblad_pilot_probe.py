#!/usr/bin/env python3
"""L64 doubled-MPS deterministic Lindblad pilot.

The L64 trajectory route is bounded and cap-sensitive: adaptive D=2/4 fails at
two cycles, and fixed D=6 is mixed rather than a clean convergence route. This
scout tries the next named tensor algorithm from the active plan: represent the
density operator as a Liouville-space MPS with physical dimension 4 and apply
exact local Lindblad channels plus two-site unitary superoperators.

This is a deterministic doubled-MPS first rung. It is not full MPDO
convergence, not PEPS/PEPS3D, not robust Phi0, not scale-level basin admission,
and not final constraint-manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import statistics
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json"

NAME = "two_root_constraint_l64_doubled_mps_lindblad_pilot_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l64_doubled_mps_deterministic_lindblad_pilot"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l64_doubled_mps_lindblad"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tensor-runtime pilot only: runs deterministic Liouville-space "
    "doubled-MPS Lindblad dynamics at L32/L64 with exact local terrain "
    "channels and two-site unitary superoperators. It cannot promote full "
    "L64 convergence, PEPS/PEPS3D closure, robust Phi0, real scale-level "
    "attractor basins, or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Liouville-space MPS tensors, local Liouvillian matrix exponentials, two-site superoperators, SVD truncation, reduced-density readouts, and entropy/Phi0 diagnostics",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing trajectory graph over length, family, variant, cycle, and terrain-stage rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and doubled-MPS first-rung guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "statistics": {"tried": True, "used": True, "reason": "supportive timing and readout summaries"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "statistics": "supportive",
}

DTYPE = qit.DTYPE
DTYPE_REAL = torch.float64
TRACE_VEC = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 1.0 + 0.0j], dtype=DTYPE)

LENGTHS = (32, 64)
FAMILIES = ("plus_x", "alternating_z")
VARIANTS = ("dynamic", "no_entangler")
TARGET_CYCLES = 2
MAX_BOND = 4
STAGES_PER_TRAJECTORY = len(mps_runtime.TERRAIN_ORDER_BY_TOKEN["1"]) * TARGET_CYCLES
TIME_BUDGET_SECONDS = 420.0
TRACE_TOL = 1.0e-8
HERMITIAN_TOL = 1.0e-8
POSITIVITY_TOL = -1.0e-6

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "qit_runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "fixed_high_cap_result": RESULT_DIR / "two_root_constraint_l64_fixed_high_cap_pilot_probe_results.json",
    "two_cycle_result": RESULT_DIR / "two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
    "handoff": REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, Any]:
    return {
        name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()}
        for name, path in SOURCE_FILES.items()
    }


def density_vector_for_site(family: str, site: int) -> torch.Tensor:
    ket = mps_runtime.site_vector(family, site).to(DTYPE)
    rho = torch.outer(ket, ket.conj())
    return rho.reshape(4).clone()


def two_site_superoperator_from_gate(gate: torch.Tensor) -> torch.Tensor:
    unitary = gate.reshape(4, 4).to(DTYPE)
    return torch.kron(unitary, unitary.conj()).reshape(4, 4, 4, 4)


def local_lindblad_channel(token: str, terrain: str) -> torch.Tensor:
    H = mps_runtime.local_hamiltonian(token)
    collapses = mps_runtime.collapse_ops(token, terrain)
    return qit.stage_channel(H, collapses, tau=mps_runtime.DT)


def vec_to_density_single(vector: torch.Tensor) -> torch.Tensor:
    return mps_runtime.normalize_density(vector.reshape(2, 2))


def two_site_vector_to_density(vector: torch.Tensor) -> torch.Tensor:
    tensor = vector.reshape(2, 2, 2, 2)
    rho = tensor.permute(0, 2, 1, 3).reshape(4, 4)
    return mps_runtime.normalize_density(rho)


class LiouvilleMPS:
    """Open-boundary MPS for vectorized density operators with local d=4."""

    def __init__(self, tensors: list[torch.Tensor]):
        self.tensors = tensors

    @property
    def L(self) -> int:
        return len(self.tensors)

    @classmethod
    def product(cls, family: str, length: int) -> "LiouvilleMPS":
        return cls([density_vector_for_site(family, idx).reshape(4, 1, 1) for idx in range(length)])

    def bond_dims(self) -> list[int]:
        return [int(tensor.shape[2]) for tensor in self.tensors[:-1]]

    def max_bond(self) -> int:
        return max(self.bond_dims(), default=1)

    def trace_value(self) -> torch.Tensor:
        env = torch.ones((1,), dtype=DTYPE)
        for tensor in self.tensors:
            env = torch.einsum("l,plr,p->r", env, tensor, TRACE_VEC)
        return env.squeeze()

    def normalize_trace_(self) -> complex:
        trace = self.trace_value()
        if abs(complex(trace.item())) < 1.0e-30:
            raise ValueError("zero trace in LiouvilleMPS")
        self.tensors[0] = self.tensors[0] / trace
        return complex(trace.item())

    def apply_single(self, op: torch.Tensor, site: int) -> None:
        self.tensors[site] = torch.einsum("ab,bij->aij", op.to(DTYPE), self.tensors[site])

    def apply_two(self, op: torch.Tensor, site: int, max_bond: int) -> float:
        if op.ndim == 2:
            op = op.reshape(4, 4, 4, 4)
        left = self.tensors[site]
        right = self.tensors[site + 1]
        theta = torch.einsum("air,brj->abij", left, right)
        theta = torch.einsum("ABab,abij->ABij", op.to(DTYPE), theta).contiguous()
        d_left, d_right, chi_left, chi_right = theta.shape
        matrix = theta.permute(0, 2, 1, 3).reshape(d_left * chi_left, d_right * chi_right)
        u_mat, singulars, vh_mat = torch.linalg.svd(matrix, full_matrices=False)
        chi_new = min(max_bond, int(singulars.numel()))
        discarded = singulars[chi_new:]
        discarded_weight = float(torch.sum(discarded.real * discarded.real).item()) if discarded.numel() else 0.0
        u_mat = u_mat[:, :chi_new]
        singulars = singulars[:chi_new]
        vh_mat = vh_mat[:chi_new, :]
        self.tensors[site] = (u_mat * singulars.unsqueeze(0)).reshape(d_left, chi_left, chi_new)
        self.tensors[site + 1] = vh_mat.reshape(chi_new, d_right, chi_right).permute(1, 0, 2).contiguous()
        return discarded_weight

    def left_trace_env(self, stop: int) -> torch.Tensor:
        env = torch.ones((1,), dtype=DTYPE)
        for idx in range(stop):
            env = torch.einsum("l,plr,p->r", env, self.tensors[idx], TRACE_VEC)
        return env

    def right_trace_env(self, start: int) -> torch.Tensor:
        env = torch.ones((1,), dtype=DTYPE)
        for idx in range(self.L - 1, start - 1, -1):
            env = torch.einsum("r,plr,p->l", env, self.tensors[idx], TRACE_VEC)
        return env

    def reduced_single(self, site: int) -> torch.Tensor:
        left_env = self.left_trace_env(site)
        right_env = self.right_trace_env(site + 1)
        vector = torch.einsum("l,plr,r->p", left_env, self.tensors[site], right_env)
        return vec_to_density_single(vector)

    def reduced_two_adjacent(self, site: int) -> torch.Tensor:
        left_env = self.left_trace_env(site)
        right_env = self.right_trace_env(site + 2)
        vector = torch.einsum("l,plr,qrs,s->pq", left_env, self.tensors[site], self.tensors[site + 1], right_env)
        return two_site_vector_to_density(vector.reshape(16))


def mean_z(lmps: LiouvilleMPS) -> float:
    values = [qit.bloch(lmps.reduced_single(site))[2] for site in range(lmps.L)]
    return float(sum(values) / len(values))


def pair_diagnostics(rho_ab: torch.Tensor) -> dict[str, float]:
    hermitian = 0.5 * (rho_ab + rho_ab.conj().T)
    evals = torch.linalg.eigvalsh(hermitian).real
    phi0 = mps_runtime.phi0_readout_pair(hermitian)
    return {
        **phi0,
        "trace_real": float(torch.trace(rho_ab).real.item()),
        "trace_imag_abs": abs(float(torch.trace(rho_ab).imag.item())),
        "hermitian_error": float(torch.linalg.matrix_norm(rho_ab - rho_ab.conj().T).real.item()),
        "min_eigenvalue": float(torch.min(evals).item()),
        "max_eigenvalue": float(torch.max(evals).item()),
    }


def run_lmps_surface(length: int, family: str, variant: str, started: float) -> dict[str, Any]:
    lmps = LiouvilleMPS.product(family, length)
    token_prev: str | None = "1"
    total_truncation = 0.0
    stage_rows: list[dict[str, Any]] = []
    two_site_super = two_site_superoperator_from_gate(mps_runtime.two_site_gate())
    stop_reason = "target_complete"
    for cycle in range(TARGET_CYCLES):
        token = mps_runtime.choose_hysteresis(mean_z(lmps), token_prev)
        token_prev = token
        for terrain_idx, terrain in enumerate(mps_runtime.TERRAIN_ORDER_BY_TOKEN[token]):
            stage_started = time.time()
            local_channel = local_lindblad_channel(token, terrain)
            for site in range(length):
                lmps.apply_single(local_channel, site)
            trace_before = lmps.normalize_trace_()
            stage_truncation = 0.0
            if variant == "dynamic":
                for site in range(terrain_idx % 2, length - 1, 2):
                    stage_truncation += lmps.apply_two(two_site_super, site, max_bond=MAX_BOND)
                lmps.normalize_trace_()
            elif variant != "no_entangler":
                raise ValueError(f"unknown variant {variant}")
            total_truncation += stage_truncation
            pair = lmps.reduced_two_adjacent(length // 2 - 1)
            pair_diag = pair_diagnostics(pair)
            stage_rows.append(
                {
                    "length": length,
                    "family": family,
                    "variant": variant,
                    "cycle": cycle,
                    "stage_index": terrain_idx,
                    "token": token,
                    "terrain": terrain,
                    "trace_before_normalize_real": float(trace_before.real),
                    "trace_before_normalize_imag": float(trace_before.imag),
                    "global_trace_error": abs(complex(lmps.trace_value().item()) - 1.0),
                    "stage_truncation_error": stage_truncation,
                    "total_truncation_error": total_truncation,
                    "max_bond": lmps.max_bond(),
                    "pair_min_eigenvalue": pair_diag["min_eigenvalue"],
                    "pair_hermitian_error": pair_diag["hermitian_error"],
                    "pair_I_A_colon_B": pair_diag["I_A_colon_B"],
                    "stage_seconds": time.time() - stage_started,
                    "elapsed_seconds": time.time() - started,
                }
            )
            if time.time() - started > TIME_BUDGET_SECONDS:
                stop_reason = "time_budget_after_completed_stage"
                break
        if stop_reason != "target_complete":
            break
    final_pair = lmps.reduced_two_adjacent(length // 2 - 1)
    final_diag = pair_diagnostics(final_pair)
    return {
        "length": length,
        "family": family,
        "variant": variant,
        "cycles": TARGET_CYCLES,
        "stages_completed": len(stage_rows),
        "target_stages": STAGES_PER_TRAJECTORY,
        "completed_target": len(stage_rows) == STAGES_PER_TRAJECTORY,
        "stop_reason": stop_reason,
        "max_bond": lmps.max_bond(),
        "bond_dims": lmps.bond_dims(),
        "global_trace_error": abs(complex(lmps.trace_value().item()) - 1.0),
        "total_truncation_error": total_truncation,
        "mean_stage_seconds": float(statistics.fmean(row["stage_seconds"] for row in stage_rows)) if stage_rows else 0.0,
        "max_stage_seconds": max((row["stage_seconds"] for row in stage_rows), default=0.0),
        "center_pair": final_diag,
        "stage_rows": stage_rows,
    }


def mean(values: list[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def trajectory_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("l64_doubled_mps_lindblad")
    for row in rows:
        route = graph.add_node(f"L{row['length']}:{row['family']}:{row['variant']}")
        graph.add_edge(root, route, "trajectory")
        for stage in row["stage_rows"]:
            stage_node = graph.add_node(
                f"L{stage['length']}:{stage['family']}:{stage['variant']}:{stage['cycle']}:{stage['stage_index']}"
            )
            graph.add_edge(route, stage_node, stage["terrain"])
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
        "weakly_connected_components": len(rx.weakly_connected_components(graph)),
    }


def aggregate(rows: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    by_length_variant: dict[str, list[dict[str, Any]]] = {}
    by_key: dict[tuple[int, str], dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_length_variant.setdefault(f"L{row['length']}:{row['variant']}", []).append(row)
        by_key.setdefault((row["length"], row["family"]), {})[row["variant"]] = row
    comparisons: list[dict[str, Any]] = []
    for (length, family), variants in sorted(by_key.items()):
        if set(VARIANTS).issubset(variants):
            dynamic = variants["dynamic"]
            control = variants["no_entangler"]
            dyn_mi = dynamic["center_pair"]["I_A_colon_B"]
            ctrl_mi = control["center_pair"]["I_A_colon_B"]
            comparisons.append(
                {
                    "length": length,
                    "family": family,
                    "dynamic_I_A_colon_B": dyn_mi,
                    "no_entangler_I_A_colon_B": ctrl_mi,
                    "dynamic_minus_no_entangler_I_A_colon_B": dyn_mi - ctrl_mi,
                    "dynamic_truncation_error": dynamic["total_truncation_error"],
                    "no_entangler_truncation_error": control["total_truncation_error"],
                    "dynamic_min_eigenvalue": dynamic["center_pair"]["min_eigenvalue"],
                    "no_entangler_min_eigenvalue": control["center_pair"]["min_eigenvalue"],
                }
            )
    route_summary: dict[str, Any] = {}
    for key, key_rows in by_length_variant.items():
        mi_values = [row["center_pair"]["I_A_colon_B"] for row in key_rows]
        min_eigs = [row["center_pair"]["min_eigenvalue"] for row in key_rows]
        route_summary[key] = {
            "trajectory_count": len(key_rows),
            "completed_trajectories": sum(1 for row in key_rows if row["completed_target"]),
            "stages_completed": sum(row["stages_completed"] for row in key_rows),
            "mean_I_A_colon_B": mean(mi_values),
            "max_I_A_colon_B": max(mi_values) if mi_values else 0.0,
            "min_I_A_colon_B": min(mi_values) if mi_values else 0.0,
            "min_pair_eigenvalue": min(min_eigs) if min_eigs else 0.0,
            "max_pair_hermitian_error": max((row["center_pair"]["hermitian_error"] for row in key_rows), default=0.0),
            "max_global_trace_error": max((row["global_trace_error"] for row in key_rows), default=float("inf")),
            "total_truncation_error": sum(row["total_truncation_error"] for row in key_rows),
            "max_bond": max((row["max_bond"] for row in key_rows), default=0),
            "mean_stage_seconds": mean([row["mean_stage_seconds"] for row in key_rows]),
            "max_stage_seconds": max((row["max_stage_seconds"] for row in key_rows), default=0.0),
        }
    dynamic_control_deltas = [row["dynamic_minus_no_entangler_I_A_colon_B"] for row in comparisons]
    min_eigs = [row["center_pair"]["min_eigenvalue"] for row in rows]
    hermitian_errors = [row["center_pair"]["hermitian_error"] for row in rows]
    trace_errors = [row["global_trace_error"] for row in rows]
    return {
        "route": "l64_doubled_mps_lindblad_pilot",
        "lengths": list(LENGTHS),
        "families": list(FAMILIES),
        "variants": list(VARIANTS),
        "target_cycles": TARGET_CYCLES,
        "max_bond": MAX_BOND,
        "elapsed_seconds": elapsed,
        "trajectory_count": len(rows),
        "completed_trajectories": sum(1 for row in rows if row["completed_target"]),
        "target_trajectory_count": len(LENGTHS) * len(FAMILIES) * len(VARIANTS),
        "stages_completed": sum(row["stages_completed"] for row in rows),
        "target_stages_total": len(LENGTHS) * len(FAMILIES) * len(VARIANTS) * STAGES_PER_TRAJECTORY,
        "route_summary": route_summary,
        "comparisons": comparisons,
        "matched_comparison_count": len(comparisons),
        "mean_dynamic_minus_no_entangler_I_A_colon_B": mean(dynamic_control_deltas),
        "max_dynamic_minus_no_entangler_I_A_colon_B": max(dynamic_control_deltas, default=0.0),
        "min_dynamic_minus_no_entangler_I_A_colon_B": min(dynamic_control_deltas, default=0.0),
        "min_pair_eigenvalue": min(min_eigs) if min_eigs else 0.0,
        "max_pair_hermitian_error": max(hermitian_errors, default=0.0),
        "max_global_trace_error": max(trace_errors, default=float("inf")),
        "trajectory_graph": trajectory_graph(rows),
        "trajectory_rows": [
            {key: value for key, value in row.items() if key != "stage_rows"} | {"stage_count": len(row["stage_rows"])}
            for row in rows
        ],
        "stage_rows_sample": [stage for row in rows for stage in row["stage_rows"]][:24],
    }


def run_surface() -> dict[str, Any]:
    started = time.time()
    rows: list[dict[str, Any]] = []
    for length in LENGTHS:
        for family in FAMILIES:
            for variant in VARIANTS:
                rows.append(run_lmps_surface(length, family, variant, started))
                if time.time() - started > TIME_BUDGET_SECONDS:
                    return aggregate(rows, time.time() - started)
    return aggregate(rows, time.time() - started)


def z3_guard(surface: dict[str, Any]) -> dict[str, Any]:
    complete = z3.Bool("complete")
    doubled_mps = z3.Bool("doubled_mps")
    trace_ok = z3.Bool("trace_ok")
    local_pair_physical = z3.Bool("local_pair_physical")
    dynamic_control_measured = z3.Bool("dynamic_control_measured")
    full_l64_convergence = z3.Bool("full_l64_convergence")
    robust_phi0 = z3.Bool("robust_phi0")
    peps3d = z3.Bool("peps3d")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(complete == (surface["completed_trajectories"] == surface["target_trajectory_count"]))
    solver.add(doubled_mps == True)
    solver.add(trace_ok == (surface["max_global_trace_error"] < TRACE_TOL))
    solver.add(
        local_pair_physical
        == (surface["min_pair_eigenvalue"] >= POSITIVITY_TOL and surface["max_pair_hermitian_error"] < HERMITIAN_TOL)
    )
    solver.add(dynamic_control_measured == (surface["matched_comparison_count"] == len(LENGTHS) * len(FAMILIES)))
    solver.add(full_l64_convergence == False)
    solver.add(robust_phi0 == False)
    solver.add(peps3d == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == z3.And(full_l64_convergence, robust_phi0, peps3d, scale_basin))
    check = solver.check()
    model = solver.model() if check == z3.sat else None
    return {
        "sat": check == z3.sat,
        "pilot_complete": bool(z3.is_true(model.eval(complete, model_completion=True))) if model else False,
        "doubled_mps_route_present": bool(z3.is_true(model.eval(doubled_mps, model_completion=True))) if model else False,
        "trace_ok": bool(z3.is_true(model.eval(trace_ok, model_completion=True))) if model else False,
        "local_pair_physical": bool(z3.is_true(model.eval(local_pair_physical, model_completion=True))) if model else False,
        "dynamic_control_measured": bool(z3.is_true(model.eval(dynamic_control_measured, model_completion=True))) if model else False,
        "full_l64_convergence_claimed": bool(z3.is_true(model.eval(full_l64_convergence, model_completion=True))) if model else False,
        "robust_phi0_claimed": bool(z3.is_true(model.eval(robust_phi0, model_completion=True))) if model else False,
        "peps3d_claimed": bool(z3.is_true(model.eval(peps3d, model_completion=True))) if model else False,
        "scale_basin_claimed": bool(z3.is_true(model.eval(scale_basin, model_completion=True))) if model else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model else False,
        "rule": "A doubled-MPS deterministic Lindblad pilot can advance the tensor route but cannot imply full L64 convergence, robust Phi0, PEPS3D, scale-basin, or final admission.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    surface = run_surface()
    guard = z3_guard(surface)
    status = (
        "bounded_l64_doubled_mps_lindblad_pilot_complete"
        if surface["completed_trajectories"] == surface["target_trajectory_count"]
        else "bounded_l64_doubled_mps_lindblad_pilot_partial"
    )
    positive = {
        "upstream_fixed_high_cap_loaded": {
            "pass": upstream["fixed_high_cap_result"].get("all_pass") is True
            and upstream["fixed_high_cap_result"].get("summary", {}).get("l64_fixed_high_cap_status")
            == "bounded_l64_fixed_high_cap_pilot_complete",
            "upstream_status": upstream["fixed_high_cap_result"].get("summary", {}).get("l64_fixed_high_cap_status"),
        },
        "all_doubled_mps_rows_completed": {
            "pass": guard["pilot_complete"],
            "completed_trajectories": surface["completed_trajectories"],
            "target_trajectory_count": surface["target_trajectory_count"],
            "stages_completed": surface["stages_completed"],
            "target_stages_total": surface["target_stages_total"],
        },
        "trace_and_local_pair_physicality": {
            "pass": guard["trace_ok"] and guard["local_pair_physical"],
            "max_global_trace_error": surface["max_global_trace_error"],
            "min_pair_eigenvalue": surface["min_pair_eigenvalue"],
            "max_pair_hermitian_error": surface["max_pair_hermitian_error"],
        },
        "dynamic_vs_no_entangler_control_measured": {
            "pass": guard["dynamic_control_measured"],
            "matched_comparison_count": surface["matched_comparison_count"],
            "mean_dynamic_minus_no_entangler_I_A_colon_B": surface["mean_dynamic_minus_no_entangler_I_A_colon_B"],
            "max_dynamic_minus_no_entangler_I_A_colon_B": surface["max_dynamic_minus_no_entangler_I_A_colon_B"],
            "min_dynamic_minus_no_entangler_I_A_colon_B": surface["min_dynamic_minus_no_entangler_I_A_colon_B"],
        },
        "z3_nonpromotion_guard": {
            "pass": guard["sat"] and not guard["final_manifold_admission_allowed"],
            "guard": guard,
        },
    }
    graveyard = {
        "full_l64_convergence_not_claimed": {
            "pass": not guard["full_l64_convergence_claimed"],
            "detail": "This is a bounded doubled-MPS first rung, not bond/horizon convergence.",
        },
        "robust_phi0_not_claimed": {
            "pass": not guard["robust_phi0_claimed"],
            "detail": "Center-pair Phi0 diagnostics are not a robust bridge theorem.",
        },
        "peps3d_not_claimed": {
            "pass": not guard["peps3d_claimed"],
            "detail": "This scout is 1D doubled MPS, not PEPS3D.",
        },
        "scale_basin_not_claimed": {
            "pass": not guard["scale_basin_claimed"],
            "detail": "No real scale-level attractor-basin admission is made.",
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    summary = {
        "all_pass": all_pass,
        "l64_doubled_mps_status": status,
        "trajectory_count": surface["trajectory_count"],
        "completed_trajectories": surface["completed_trajectories"],
        "stages_completed": surface["stages_completed"],
        "elapsed_seconds": surface["elapsed_seconds"],
        "route_mean_I_A_colon_B": {
            key: row["mean_I_A_colon_B"] for key, row in surface["route_summary"].items()
        },
        "route_total_truncation_error": {
            key: row["total_truncation_error"] for key, row in surface["route_summary"].items()
        },
        "mean_dynamic_minus_no_entangler_I_A_colon_B": surface["mean_dynamic_minus_no_entangler_I_A_colon_B"],
        "max_dynamic_minus_no_entangler_I_A_colon_B": surface["max_dynamic_minus_no_entangler_I_A_colon_B"],
        "min_dynamic_minus_no_entangler_I_A_colon_B": surface["min_dynamic_minus_no_entangler_I_A_colon_B"],
        "max_global_trace_error": surface["max_global_trace_error"],
        "min_pair_eigenvalue": surface["min_pair_eigenvalue"],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "A deterministic Liouville-space doubled-MPS route now runs at L32/L64 with exact local Lindblad channels. "
            "It is a tensor-algorithm advance beyond stochastic trajectory/cap probes, but remains first-rung evidence."
        ),
        "next_required_work": (
            "Stress the doubled-MPS route with more cycles, larger bond caps, and comparison against trajectory ensembles; "
            "do not promote Phi0 or basin admission until it survives bridge controls and scale-level basin criteria."
        ),
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "fixed_high_cap_status": upstream["fixed_high_cap_result"].get("summary", {}).get("l64_fixed_high_cap_status"),
            "two_cycle_status": upstream["two_cycle_result"].get("summary", {}).get("l64_two_cycle_status"),
        },
        "parameters": {
            "lengths": list(LENGTHS),
            "families": list(FAMILIES),
            "variants": list(VARIANTS),
            "target_cycles": TARGET_CYCLES,
            "max_bond": MAX_BOND,
            "time_budget_seconds": TIME_BUDGET_SECONDS,
            "trace_tolerance": TRACE_TOL,
            "positivity_tolerance": POSITIVITY_TOL,
        },
        "surface": surface,
        "z3_guard": guard,
        "positive": positive,
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "l64_doubled_mps_status": status,
            "full_l64_convergence_claimed": False,
            "robust_phi0_claimed": False,
            "peps_peps3d_full_claimed": False,
            "scale_basin_claimed": False,
            "final_manifold_admission_allowed": False,
        },
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "items": sorted(graveyard),
        },
        "why_not_v4_probes": (
            "This is a v5 source-native PyTorch formal scout extending the current QIT engine tensor runtime. "
            "It is not a wiki route, not a legacy v4 probe, not PEPS/PEPS3D, and not final manifold admission."
        ),
        "next_work_required": [
            "Extend doubled-MPS to longer horizons and higher bond caps if this first rung remains physical.",
            "Compare deterministic doubled-MPS readouts against stochastic trajectory ensemble averages.",
            "Keep robust Phi0, PEPS/PEPS3D convergence, scale-level basin admission, and final admission blocked.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
