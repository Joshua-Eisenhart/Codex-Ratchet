#!/usr/bin/env python3
"""Hardened Gap F replay: archive-pinned state selection plus structured OT.

The packet endpoint is selected by its named context and shipped endpoint
identity. The value 137/160 is checked only after selection. OTT is checked
against an independent SciPy LP under a circular ground metric where OT is not
identically total variation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

os.environ.setdefault("JAX_ENABLE_X64", "1")

import jax
import jax.numpy as jnp
import numpy as np
import ott
import scipy
from ott.geometry import geometry
from ott.problems.linear import linear_problem
from ott.solvers.linear import sinkhorn
from scipy.optimize import linprog


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "results" / "gap_f_ott_structured_v2_results.json"
JULIA_SOURCE = HERE / "gap_f_endpoint_check_v2.jl"
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/var/folders/59/jd7hbp413gn509q_fz_k6wgr0000gn/T/codex-ratchet-representative-grdkqpeb/repo/system_v5/julia_carrier"
SIM_MEMBER = "sims_and_scripts/ontological_finitude_cosmogenesis_ratchet_sim.py"
RECEIPT_MEMBER = "sims_and_scripts/ontological_finitude_cosmogenesis_ratchet_sim_results.json"
EXPECTED_ARCHIVE_SHA256 = "42fc2629e076b4cd5b8015514fb1c9027aa7c751702ebc7a719a6b808141b9da"
EXPECTED_SIM_SHA256 = "2c9c4ebea4fac081ed4ef0485a121dca1d69a618c2b77a3137cda21500f94762"
EXPECTED_RECEIPT_SHA256 = "ae71a5b6633d9c464de8934eb73d4d20fc00c9a0c14455ea005019d2a501d2a9"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_packet(archive: Path) -> tuple[Any, dict[str, Any], dict[str, str]]:
    archive_bytes = archive.read_bytes()
    archive_sha = sha256_bytes(archive_bytes)
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"unexpected packet archive sha256: {archive_sha}")
    with zipfile.ZipFile(archive) as bundle:
        sim_bytes = bundle.read(SIM_MEMBER)
        receipt_bytes = bundle.read(RECEIPT_MEMBER)
    sim_sha = sha256_bytes(sim_bytes)
    receipt_sha = sha256_bytes(receipt_bytes)
    if sim_sha != EXPECTED_SIM_SHA256 or receipt_sha != EXPECTED_RECEIPT_SHA256:
        raise ValueError("packet member hash mismatch")
    temporary = tempfile.TemporaryDirectory(prefix="ratchet-gap-f-v2-")
    source_path = Path(temporary.name) / "ontological_finitude_cosmogenesis_ratchet_sim.py"
    source_path.write_bytes(sim_bytes)
    spec = importlib.util.spec_from_file_location("packet166_gap_f_source", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to construct packet sim module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._temporary_source = temporary
    return module, json.loads(receipt_bytes), {
        "archive_sha256": archive_sha,
        "sim_member_sha256": sim_sha,
        "receipt_member_sha256": receipt_sha,
    }


def circular_cost(size: int) -> np.ndarray:
    indices = np.arange(size)
    distance = np.abs(indices[:, None] - indices[None, :])
    return np.minimum(distance, size - distance).astype(np.float64) / (size / 2.0)


def normalize(counts: tuple[int, ...] | list[int]) -> np.ndarray:
    values = np.asarray(counts, dtype=np.float64)
    return values / values.sum()


def lp_ot(a: np.ndarray, b: np.ndarray, cost: np.ndarray) -> dict[str, Any]:
    n = len(a)
    equality = np.zeros((2 * n, n * n), dtype=np.float64)
    for i in range(n):
        equality[i, i * n : (i + 1) * n] = 1.0
    for j in range(n):
        equality[n + j, j::n] = 1.0
    result = linprog(
        cost.reshape(-1),
        A_eq=equality,
        b_eq=np.concatenate([a, b]),
        bounds=(0.0, None),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"SciPy OT oracle failed: {result.message}")
    plan = result.x.reshape(n, n)
    return {
        "cost": float(np.sum(plan * cost)),
        "row_residual": float(np.max(np.abs(plan.sum(axis=1) - a))),
        "column_residual": float(np.max(np.abs(plan.sum(axis=0) - b))),
        "status": int(result.status),
        "message": result.message,
    }


def ott_ot(a: np.ndarray, b: np.ndarray, cost: np.ndarray, epsilon: float) -> dict[str, Any]:
    jcost = jnp.asarray(cost, dtype=jnp.float64)
    problem = linear_problem.LinearProblem(
        geometry.Geometry(cost_matrix=jcost, epsilon=epsilon),
        a=jnp.asarray(a, dtype=jnp.float64),
        b=jnp.asarray(b, dtype=jnp.float64),
    )
    solver = sinkhorn.Sinkhorn(threshold=1e-10, max_iterations=300_000, lse_mode=True)
    answer = solver(problem)
    plan = np.asarray(answer.matrix, dtype=np.float64)
    return {
        "epsilon": epsilon,
        "converged": bool(answer.converged),
        "transport_cost": float(np.sum(plan * cost)),
        "row_residual": float(np.max(np.abs(plan.sum(axis=1) - a))),
        "column_residual": float(np.max(np.abs(plan.sum(axis=0) - b))),
        "reg_ot_cost": float(answer.reg_ot_cost),
    }


def run_julia() -> dict[str, Any]:
    command = [
        JULIA,
        "--startup-file=no",
        f"--project={JULIA_PROJECT}",
        str(JULIA_SOURCE),
    ]
    environment = dict(os.environ)
    environment["JULIA_LOAD_PATH"] = "@:@stdlib"
    completed = subprocess.run(
        command,
        env=environment,
        cwd=HERE,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    report: dict[str, Any] = {}
    if completed.returncode == 0:
        report = json.loads(completed.stdout.strip().splitlines()[-1])
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.splitlines(),
        "stderr": completed.stderr.splitlines(),
        "report": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if Path(sys.executable).resolve() != Path(PYTHON).resolve():
        raise RuntimeError(f"wrong Python runtime: {sys.executable}")
    if not bool(jax.config.read("jax_enable_x64")):
        raise RuntimeError("JAX x64 must be enabled")

    sim, shipped, hashes = load_packet(args.archive.resolve())
    orbits = {
        context: sim.orbit(sim.INITIAL, context)
        for context in ("flat", "order_sensitive", "bracket_sensitive", "joint_order_bracket")
    }
    endpoint = tuple(orbits["joint_order_bracket"]["endpoint"])
    shipped_endpoint = tuple(shipped["constraint_orbits"]["joint_order_bracket"]["endpoint"])
    rotated = endpoint[1:] + endpoint[:1]
    tv = sim.total_variation(endpoint, rotated)
    target_tv = Fraction(137, 160)
    fixed_point = sim.update(endpoint, "joint_order_bracket") == endpoint

    cost = circular_cost(len(endpoint))
    p = normalize(endpoint)
    q = normalize(rotated)
    lp_primary = lp_ot(p, q, cost)
    ott_sweep = [ott_ot(p, q, cost, epsilon) for epsilon in (0.03, 0.01, 0.003, 0.001)]
    converged_primary = [row for row in ott_sweep if row["converged"]]
    if not converged_primary:
        raise RuntimeError("OTT did not converge at any preregistered epsilon")
    ott_primary = converged_primary[-1]
    self_lp = lp_ot(p, p, cost)
    self_ott = ott_ot(p, p, cost, 0.001)

    independent_left = tuple(orbits["order_sensitive"]["endpoint"])
    independent_right = tuple(orbits["bracket_sensitive"]["endpoint"])
    independent_a = normalize(independent_left)
    independent_b = normalize(independent_right)
    lp_independent = lp_ot(independent_a, independent_b, cost)
    ott_independent = ott_ot(independent_a, independent_b, cost, 0.001)

    perturbed = list(rotated)
    perturbed[9] -= 1
    perturbed[10] += 1
    perturbed_lp = lp_ot(p, normalize(perturbed), cost)
    zero_cost = np.zeros_like(cost)
    zero_cost_lp = lp_ot(p, q, zero_cost)
    discrete_cost_lp = lp_ot(p, q, 1.0 - np.eye(len(endpoint), dtype=np.float64))
    julia = run_julia()
    julia_report = julia["report"]

    oracle_tolerance = 5e-5
    checks = {
        "archive_and_members_match_pinned_hashes": hashes == {
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "sim_member_sha256": EXPECTED_SIM_SHA256,
            "receipt_member_sha256": EXPECTED_RECEIPT_SHA256,
        },
        "endpoint_selected_by_named_context_matches_shipped_identity": endpoint == shipped_endpoint,
        "endpoint_is_fixed_point": fixed_point,
        "postselection_tv_matches_shipped_137_160": tv == target_tv,
        "structured_metric_is_not_discrete_0_1_metric": not np.array_equal(cost, 1.0 - np.eye(len(endpoint))),
        "structured_ot_not_identically_tv": abs(lp_primary["cost"] - float(tv)) > 1e-3,
        "ott_primary_converged": ott_primary["converged"],
        "ott_primary_matches_independent_lp": abs(ott_primary["transport_cost"] - lp_primary["cost"]) < oracle_tolerance,
        "ott_primary_marginals_match": max(ott_primary["row_residual"], ott_primary["column_residual"]) < oracle_tolerance,
        "self_transport_is_zero": self_lp["cost"] < 1e-12 and self_ott["transport_cost"] < oracle_tolerance,
        "independent_named_pair_ott_matches_lp": ott_independent["converged"] and abs(ott_independent["transport_cost"] - lp_independent["cost"]) < oracle_tolerance,
        "independent_pair_is_not_target_selected": (independent_left, independent_right) != (endpoint, rotated),
        "perturbed_pair_changes_structured_cost": abs(perturbed_lp["cost"] - lp_primary["cost"]) > 1e-4,
        "zero_metric_erasure_collapses_transport": zero_cost_lp["cost"] == 0.0 and lp_primary["cost"] > 0.0,
        "discrete_metric_reproduces_tv_only_as_ablation": abs(discrete_cost_lp["cost"] - float(tv)) < 1e-12,
        "julia_completed_in_canonical_carrier": julia["exit_code"] == 0 and julia_report.get("active_project") == f"{JULIA_PROJECT}/Project.toml",
        "julia_endpoint_matches_python": tuple(julia_report.get("endpoint", ())) == endpoint,
        "julia_tv_and_fixed_point_match": julia_report.get("tv_fraction") == "137/160" and julia_report.get("fixed_point") is True,
    }
    all_pass = all(checks.values())
    command = [PYTHON, str(Path(__file__).resolve()), "--archive", str(args.archive.resolve()), "--output", str(args.output.resolve())]
    result = {
        "schema": "codex-ratchet.gap-f-structured-ot-result.v2",
        "sim_id": "gap_f_packet166_structured_ot",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "runner_identity": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "jax_version": jax.__version__,
            "jax_x64": bool(jax.config.read("jax_enable_x64")),
            "ott_version": ott.__version__,
            "scipy_version": scipy.__version__,
            "julia_project": JULIA_PROJECT,
        },
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source": {
            "archive_path": str(args.archive.resolve()),
            "archive_sha256": hashes["archive_sha256"],
            "sim_member": SIM_MEMBER,
            "sim_member_sha256": hashes["sim_member_sha256"],
            "shipped_receipt_member": RECEIPT_MEMBER,
            "shipped_receipt_member_sha256": hashes["receipt_member_sha256"],
            "probe_path": str(Path(__file__).resolve()),
            "probe_sha256": sha256_file(Path(__file__).resolve()),
            "julia_source_path": str(JULIA_SOURCE),
            "julia_source_sha256": sha256_file(JULIA_SOURCE),
        },
        "selection_contract": {
            "selector": "named joint_order_bracket orbit endpoint",
            "target_value_used_for_selection": False,
            "endpoint": list(endpoint),
            "rotated_endpoint": list(rotated),
            "postselection_tv_fraction": f"{tv.numerator}/{tv.denominator}",
            "fixed_point": fixed_point,
        },
        "primary_structured_ot": {
            "ground_metric": "normalized circular geodesic distance over the 16 fixed law indices",
            "scipy_lp_oracle": lp_primary,
            "ott_sinkhorn_epsilon_sweep": ott_sweep,
            "selected_ott_result": ott_primary,
            "discrete_0_1_metric_ablation_cost": discrete_cost_lp["cost"],
            "total_variation": float(tv),
        },
        "independent_named_pair": {
            "selector": "order_sensitive endpoint versus bracket_sensitive endpoint",
            "left": list(independent_left),
            "right": list(independent_right),
            "scipy_lp_oracle": lp_independent,
            "ott_result": ott_independent,
        },
        "controls": {
            "self": {"scipy_lp": self_lp, "ott": self_ott},
            "perturbed_pair_scipy_lp": perturbed_lp,
            "zero_metric_erasure_scipy_lp": zero_cost_lp,
            "discrete_metric_ablation_scipy_lp": discrete_cost_lp,
        },
        "julia_cross_engine": julia,
        "checks": checks,
        "all_pass": all_pass,
        "tool_manifest": {
            "ott": "claim_load_bearing for entropic transport under the structured metric",
            "scipy.optimize.linprog": "independent numerical LP oracle for the same finite transport problem",
            "julia": "exact independent endpoint, fixed-point, and TV replay; not an OT oracle",
        },
        "tool_calls": [
            {
                "tool": "ott",
                "api": "Geometry + LinearProblem + Sinkhorn",
                "input": "archive-pinned endpoint distributions and circular cost matrix",
                "output": "transport plan and structured transport cost",
                "negative_control": "zero-cost erasure collapses separation",
                "gates": ["all_pass"],
            },
            {
                "tool": "scipy",
                "api": "scipy.optimize.linprog(method=highs)",
                "input": "same finite marginal constraints and cost matrix",
                "output": "unregularized LP optimum",
                "negative_control": "discrete-metric ablation exposes the original TV coupling",
                "gates": ["all_pass"],
            },
        ],
        "claim_ceiling": (
            "Archive-pinned function-level evidence that OTT agrees with a finite SciPy LP oracle "
            "under one nontrivial structured ground metric on two named packet profile pairs. "
            "This does not admit the packet, a scientific transport law, QIT, a manifold, or a Ratchet rung."
        ),
        "blocked_consumers": ["scientific canon", "Ratchet rung promotion", "QIT or manifold admission", "Lev graph mutation"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "receipt": str(args.output.resolve()), "failed": [name for name, value in checks.items() if not value]}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
