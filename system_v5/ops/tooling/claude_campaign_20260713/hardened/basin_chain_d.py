#!/usr/bin/env python3
"""Run the bounded gap-D basin chain across Julia, JAX, Optimistix, and Z3.

Shared map:

    F(x; alpha) = x - alpha * max(x - 3, 0)

The start grid is strictly above 3.  Julia Attractors assigns that grid to the
supplied boundary attractor; JAX/Diffrax integrates the residual flow F(x)-x;
Optimistix iterates F directly; and Z3 certifies the active affine branch.

Important ceiling: the full piecewise map fixes every x <= 3.  The tool probe
therefore certifies 3 only as the active-domain boundary/unique active-branch
fixed point, not as a globally minimal or globally unique fixed point.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("JAX_ENABLE_X64", "1")

from jax import config

config.update("jax_enable_x64", True)

import diffrax
import jax
import jax.numpy as jnp
import optimistix as optx
import z3


HERE = Path(__file__).resolve().parent
JULIA_SOURCE = HERE / "basin_chain_d.jl"
RESULT_PATH = HERE / "results" / "basin_chain_d_results.json"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier"

FLOOR = 3.0
DRIVE = 0.5
ERASED_DRIVE = 0.0
STARTS = jnp.linspace(3.5, 12.0, 18, dtype=jnp.float64)
TOLERANCE = 1.0e-8
SOLVER_TOLERANCE = 1.0e-12

CLASSIFICATION = "tool_lego_fit_probe"
PROMOTION_ALLOWED = False

TOOL_MANIFEST = {
    "Attractors": {
        "tried": True,
        "used": True,
        "reason": "AttractorsViaProximity and basins_of_attraction gate active and erased basin labels.",
    },
    "StaticArrays": {
        "tried": True,
        "used": True,
        "reason": "SVector is the one-dimensional state carrier for DeterministicIteratedMap.",
    },
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "ODETerm and diffeqsolve gate relaxation endpoints and erased-drive freezing.",
    },
    "optimistix": {
        "tried": True,
        "used": True,
        "reason": "fixed_point directly iterates the shared map for active and erased drives.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Exact Real solvers gate active-branch UNSAT, global anti-overclaim SAT, and erased-control SAT.",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "Not relevant to the one-dimensional fixed-point/basin claim; used only by the separate Item 1 probe.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "Attractors": "load_bearing",
    "StaticArrays": "supportive",
    "diffrax": "load_bearing",
    "optimistix": "load_bearing",
    "z3": "load_bearing",
    "rustworkx": None,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shared_map(x: jax.Array, drive: jax.Array | float) -> jax.Array:
    return x - drive * jnp.maximum(x - FLOOR, 0.0)


def parse_julia_stdout(stdout: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if "=" in line and line.startswith("JULIA_"):
            key, value = line.split("=", 1)
            parsed[key] = value
    return parsed


def run_julia_leg() -> dict[str, Any]:
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
        cwd=HERE,
        env=environment,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    fields = parse_julia_stdout(completed.stdout)

    required = {
        "JULIA_ACTIVE_PROJECT",
        "JULIA_VERSION",
        "JULIA_ATTRACTORS_VERSION",
        "JULIA_STATICARRAYS_VERSION",
        "JULIA_START_COUNT",
        "JULIA_ACTIVE_BASIN_COUNT",
        "JULIA_ACTIVE_BASIN_FRACTION",
        "JULIA_ACTIVE_LOST_FRACTION",
        "JULIA_ATTRACTOR_LOCATION",
        "JULIA_MAX_ENDPOINT_ERROR",
        "JULIA_ERASED_BASIN_COUNT",
        "JULIA_ERASED_BASIN_FRACTION",
        "JULIA_ERASED_LOST_FRACTION",
        "JULIA_ERASED_MAX_MOTION",
        "JULIA_BOUNDARY_FIXED",
        "JULIA_GLOBAL_BELOW_FLOOR_FIXED",
    }
    missing = sorted(required - fields.keys())
    passed = (
        completed.returncode == 0
        and not missing
        and "PASS basin_chain_d_julia" in completed.stdout
        and int(fields["JULIA_START_COUNT"]) == len(STARTS)
        and int(fields["JULIA_ACTIVE_BASIN_COUNT"]) == 1
        and float(fields["JULIA_ACTIVE_BASIN_FRACTION"]) == 1.0
        and float(fields["JULIA_ACTIVE_LOST_FRACTION"]) == 0.0
        and abs(float(fields["JULIA_ATTRACTOR_LOCATION"]) - FLOOR) <= TOLERANCE
        and float(fields["JULIA_MAX_ENDPOINT_ERROR"]) <= SOLVER_TOLERANCE
        and int(fields["JULIA_ERASED_BASIN_COUNT"]) == 0
        and float(fields["JULIA_ERASED_BASIN_FRACTION"]) == 0.0
        and float(fields["JULIA_ERASED_LOST_FRACTION"]) == 1.0
        and float(fields["JULIA_ERASED_MAX_MOTION"]) == 0.0
        and fields["JULIA_BOUNDARY_FIXED"] == "true"
        and fields["JULIA_GLOBAL_BELOW_FLOOR_FIXED"] == "true"
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "ran": True,
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.splitlines(),
        "stderr": completed.stderr.splitlines(),
        "missing_fields": missing,
        "active_project": fields.get("JULIA_ACTIVE_PROJECT"),
        "julia_version": fields.get("JULIA_VERSION"),
        "package_versions": {
            "Attractors": fields.get("JULIA_ATTRACTORS_VERSION"),
            "StaticArrays": fields.get("JULIA_STATICARRAYS_VERSION"),
        },
        "packages_used": ["Attractors", "StaticArrays"],
        "aligned_packages_load_bearing": ["Attractors"],
        "source_path": str(JULIA_SOURCE),
        "source_sha256": sha256_file(JULIA_SOURCE),
        "reads_peer_result": False,
        "start_count": int(fields["JULIA_START_COUNT"]) if not missing else None,
        "active_basin_count": int(fields["JULIA_ACTIVE_BASIN_COUNT"]) if not missing else None,
        "active_basin_fraction": float(fields["JULIA_ACTIVE_BASIN_FRACTION"]) if not missing else None,
        "active_lost_fraction": float(fields["JULIA_ACTIVE_LOST_FRACTION"]) if not missing else None,
        "attractor_location": float(fields["JULIA_ATTRACTOR_LOCATION"]) if not missing else None,
        "max_endpoint_error": float(fields["JULIA_MAX_ENDPOINT_ERROR"]) if not missing else None,
        "erased_basin_count": int(fields["JULIA_ERASED_BASIN_COUNT"]) if not missing else None,
        "erased_basin_fraction": float(fields["JULIA_ERASED_BASIN_FRACTION"]) if not missing else None,
        "erased_lost_fraction": float(fields["JULIA_ERASED_LOST_FRACTION"]) if not missing else None,
        "erased_max_motion": float(fields["JULIA_ERASED_MAX_MOTION"]) if not missing else None,
        "boundary_fixed": fields.get("JULIA_BOUNDARY_FIXED") == "true",
        "global_below_floor_fixed_witness": fields.get("JULIA_GLOBAL_BELOW_FLOOR_FIXED") == "true",
    }


def run_diffrax_leg() -> dict[str, Any]:
    def residual_flow(t: jax.Array, state: jax.Array, drive: jax.Array) -> jax.Array:
        del t
        return shared_map(state, drive) - state

    saveat = diffrax.SaveAt(t1=True)
    controller = diffrax.PIDController(rtol=1.0e-12, atol=1.0e-12)
    active = diffrax.diffeqsolve(
        diffrax.ODETerm(residual_flow),
        diffrax.Tsit5(),
        t0=0.0,
        t1=80.0,
        dt0=0.1,
        y0=STARTS,
        args=jnp.array(DRIVE, dtype=jnp.float64),
        saveat=saveat,
        stepsize_controller=controller,
        max_steps=100_000,
        throw=False,
    )
    erased = diffrax.diffeqsolve(
        diffrax.ODETerm(residual_flow),
        diffrax.Tsit5(),
        t0=0.0,
        t1=80.0,
        dt0=0.1,
        y0=STARTS,
        args=jnp.array(ERASED_DRIVE, dtype=jnp.float64),
        saveat=saveat,
        stepsize_controller=controller,
        max_steps=100_000,
        throw=False,
    )
    active_endpoints = active.ys[0]
    erased_endpoints = erased.ys[0]
    analytic_endpoints = FLOOR + (STARTS - FLOOR) * jnp.exp(-DRIVE * 80.0)
    active_error = float(jnp.max(jnp.abs(active_endpoints - FLOOR)))
    analytic_error = float(jnp.max(jnp.abs(active_endpoints - analytic_endpoints)))
    erased_motion = float(jnp.max(jnp.abs(erased_endpoints - STARTS)))
    active_success = bool(diffrax.is_successful(active.result))
    erased_success = bool(diffrax.is_successful(erased.result))
    passed = (
        active_success
        and erased_success
        and active_error <= TOLERANCE
        and analytic_error <= TOLERANCE
        and erased_motion <= SOLVER_TOLERANCE
        and float(jnp.max(jnp.abs(erased_endpoints - FLOOR))) > TOLERANCE
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "solver": "diffrax.Tsit5",
        "api": "diffrax.ODETerm + diffrax.diffeqsolve",
        "residual_flow": "dx/dt = F(x; alpha) - x",
        "t1": 80.0,
        "active_result": str(active.result),
        "erased_result": str(erased.result),
        "active_endpoints": [float(value) for value in active_endpoints],
        "analytic_endpoints": [float(value) for value in analytic_endpoints],
        "max_endpoint_error_to_floor": active_error,
        "max_error_to_analytic_flow": analytic_error,
        "erased_endpoints": [float(value) for value in erased_endpoints],
        "erased_max_motion": erased_motion,
        "reads_peer_result": False,
    }


def run_optimistix_leg() -> dict[str, Any]:
    solver = optx.FixedPointIteration(rtol=1.0e-13, atol=1.0e-13)
    active = optx.fixed_point(
        shared_map,
        solver,
        jnp.array(12.0, dtype=jnp.float64),
        args=jnp.array(DRIVE, dtype=jnp.float64),
        max_steps=1_000,
        throw=False,
    )
    erased = optx.fixed_point(
        shared_map,
        solver,
        jnp.array(12.0, dtype=jnp.float64),
        args=jnp.array(ERASED_DRIVE, dtype=jnp.float64),
        max_steps=1_000,
        throw=False,
    )
    active_value = float(active.value)
    erased_value = float(erased.value)
    active_residual = abs(float(shared_map(active.value, DRIVE) - active.value))
    erased_residual = abs(float(shared_map(erased.value, ERASED_DRIVE) - erased.value))
    active_success = bool(active.result == optx.RESULTS.successful)
    erased_success = bool(erased.result == optx.RESULTS.successful)
    passed = (
        active_success
        and erased_success
        and abs(active_value - FLOOR) <= TOLERANCE
        and active_residual <= SOLVER_TOLERANCE
        and abs(erased_value - 12.0) <= SOLVER_TOLERANCE
        and erased_residual <= SOLVER_TOLERANCE
        and abs(erased_value - FLOOR) > TOLERANCE
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "api": "optimistix.fixed_point + optimistix.FixedPointIteration",
        "active_value": active_value,
        "active_residual": active_residual,
        "active_result": str(active.result),
        "active_num_steps": int(active.stats["num_steps"]),
        "erased_value": erased_value,
        "erased_residual": erased_residual,
        "erased_result": str(erased.result),
        "erased_num_steps": int(erased.stats["num_steps"]),
        "reads_peer_result": False,
    }


def z3_verdict(solver: z3.Solver) -> str:
    return str(solver.check())


def z3_model_value(solver: z3.Solver, variable: z3.ArithRef) -> str | None:
    if solver.check() != z3.sat:
        return None
    return str(solver.model().eval(variable, model_completion=True))


def run_z3_leg(measured_julia_floor: float) -> dict[str, Any]:
    floor = z3.Real("julia_measured_floor")
    floor_exact = z3.RealVal(format(measured_julia_floor, ".17g"))
    drive = z3.RealVal(1) / z3.RealVal(2)
    measurement_bindings = (floor == floor_exact,)

    boundary = z3.Real("boundary")
    boundary_solver = z3.Solver()
    boundary_solver.add(*measurement_bindings)
    boundary_solver.add(boundary == floor)
    boundary_solver.add(boundary == boundary - drive * (boundary - floor))

    below = z3.Real("active_affine_below")
    below_solver = z3.Solver()
    below_solver.add(*measurement_bindings)
    below_solver.add(below < floor)
    below_solver.add(below == below - drive * (below - floor))

    strict_above = z3.Real("strict_active_fixed")
    strict_above_solver = z3.Solver()
    strict_above_solver.add(*measurement_bindings)
    strict_above_solver.add(strict_above > floor)
    strict_above_solver.add(strict_above == strict_above - drive * (strict_above - floor))

    global_below = z3.Real("global_piecewise_below")
    piecewise = z3.If(
        global_below > floor,
        global_below - drive * (global_below - floor),
        global_below,
    )
    global_below_solver = z3.Solver()
    global_below_solver.add(*measurement_bindings)
    global_below_solver.add(global_below < floor)
    global_below_solver.add(global_below == piecewise)

    erased = z3.Real("erased_strict_active_fixed")
    erased_solver = z3.Solver()
    erased_solver.add(*measurement_bindings)
    erased_solver.add(erased > floor)
    erased_solver.add(erased == erased - z3.RealVal(0) * (erased - floor))

    verdicts = {
        "boundary_exact": z3_verdict(boundary_solver),
        "active_affine_below_floor": z3_verdict(below_solver),
        "strict_active_interior_fixed_point": z3_verdict(strict_above_solver),
        "global_piecewise_below_floor_fixed_point": z3_verdict(global_below_solver),
        "erased_strict_active_fixed_point": z3_verdict(erased_solver),
    }
    passed = verdicts == {
        "boundary_exact": "sat",
        "active_affine_below_floor": "unsat",
        "strict_active_interior_fixed_point": "unsat",
        "global_piecewise_below_floor_fixed_point": "sat",
        "erased_strict_active_fixed_point": "sat",
    }
    return {
        "status": "PASS" if passed else "FAIL",
        "api": "z3.Solver.check over exact Real arithmetic and a piecewise If",
        "polarity": {
            "active_branch": "UNSAT below the active affine floor and UNSAT strictly above the boundary",
            "full_piecewise_anti_overclaim": "SAT below the floor because every x <= 3 is globally fixed",
            "erased_control": "SAT strictly above the floor when drive is zero",
        },
        "verdicts": verdicts,
        "witnesses": {
            "boundary": z3_model_value(boundary_solver, boundary),
            "global_below_floor": z3_model_value(global_below_solver, global_below),
            "erased_strict_active": z3_model_value(erased_solver, erased),
            "measured_julia_floor_decimal": format(measured_julia_floor, ".17g"),
        },
        "measurement_bindings": {
            "floor_symbol": "julia_measured_floor",
            "floor_exact_decimal": format(measured_julia_floor, ".17g"),
            "applied_to_every_query": True,
            "load_bearing_to_unsat": True,
            "optimistix_role": "independent numerical candidate checked by cross-engine agreement, not a Z3 premise",
        },
        "claim": (
            "3 is the unique active-affine fixed point and boundary approached by starts above 3; "
            "global fixed-point uniqueness/minimality is explicitly false"
        ),
    }


def main() -> int:
    if sys.prefix != "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main":
        raise RuntimeError(f"wrong Python environment: {sys.prefix}")
    if not bool(jax.config.read("jax_enable_x64")):
        raise RuntimeError("JAX x64 is not enabled")

    julia_leg = run_julia_leg()
    diffrax_leg = run_diffrax_leg()
    optimistix_leg = run_optimistix_leg()

    julia_location = julia_leg.get("attractor_location")
    if julia_location is None:
        raise RuntimeError("Julia did not return an attractor location for the Z3 measurement binding")
    z3_leg = run_z3_leg(float(julia_location))
    optimistix_location = optimistix_leg["active_value"]
    diffrax_max_error = diffrax_leg["max_endpoint_error_to_floor"]
    julia_optimistix_delta = (
        abs(float(julia_location) - optimistix_location)
        if julia_location is not None
        else float("inf")
    )
    cross_engine_pass = (
        julia_leg["status"] == "PASS"
        and diffrax_leg["status"] == "PASS"
        and optimistix_leg["status"] == "PASS"
        and julia_optimistix_delta <= TOLERANCE
        and diffrax_max_error <= TOLERANCE
    )
    erased_flip_pass = (
        julia_leg.get("erased_basin_count") == 0
        and julia_leg.get("erased_lost_fraction") == 1.0
        and diffrax_leg["erased_max_motion"] <= SOLVER_TOLERANCE
        and abs(optimistix_leg["erased_value"] - FLOOR) > TOLERANCE
        and z3_leg["verdicts"]["erased_strict_active_fixed_point"] == "sat"
        and z3_leg["verdicts"]["strict_active_interior_fixed_point"] == "unsat"
    )
    all_pass = cross_engine_pass and erased_flip_pass and z3_leg["status"] == "PASS"

    result = {
        "schema": "codex-ratchet.basin-chain-d-result.v2",
        "sim_id": "gap_d_basin_chain_cross_engine",
        "name": "Gap-D active-boundary basin chain",
        "version": 2,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": [
            "env",
            "JAX_ENABLE_X64=1",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            str(Path(__file__).resolve()),
        ],
        "runner_identity": {
            "controller_engine": "python",
            "executable": sys.executable,
            "python_version": sys.version,
            "jax_version": jax.__version__,
            "jax_x64": bool(jax.config.read("jax_enable_x64")),
            "diffrax_version": diffrax.__version__,
            "optimistix_version": optx.__version__,
            "z3_version": z3.get_version_string(),
        },
        "engine_contract": {
            "mode": "julia_canon_jax_workhorse",
            "lanes": ["julia_attractors", "jax_diffrax", "jax_optimistix", "z3"],
            "julia_semantic_owner": "shared discrete map and active-domain basin labels",
            "jax_workhorse": "residual-flow endpoints and direct fixed-point iteration",
            "proof_surface": "Z3 exact active-branch certificate with full-piecewise anti-overclaim witness",
            "reads_peer_result": False,
        },
        "shared_object": {
            "map": "F(x; alpha) = x - alpha*max(x-3, 0)",
            "active_drive": DRIVE,
            "erased_drive": ERASED_DRIVE,
            "floor": FLOOR,
            "start_grid": [float(value) for value in STARTS],
            "start_domain": "strictly above the floor",
            "cross_engine_tolerance": TOLERANCE,
            "global_fixed_set": "all real x <= 3",
            "allowed_fixed_point_claim": "unique active-affine boundary fixed point at 3",
        },
        "source": {
            "python_path": str(Path(__file__).resolve()),
            "python_sha256": sha256_file(Path(__file__).resolve()),
            "julia_path": str(JULIA_SOURCE),
            "julia_sha256": sha256_file(JULIA_SOURCE),
            "claude_live_source_sha256_before_runtime_path_hardening": {
                "python": "2a4011cec35632ac37acf49e90c858bc80362629ad2c126bd199797df52c7d9d",
                "julia": "65841ae37615d335e87dc77bf34206e4952e411bad747b4d722b207a1b659b92",
            },
        },
        "legs": {
            "julia_attractors": julia_leg,
            "jax_diffrax": diffrax_leg,
            "jax_optimistix": optimistix_leg,
            "z3_active_floor": z3_leg,
            "cross_engine_agreement": {
                "status": "PASS" if cross_engine_pass else "FAIL",
                "julia_location": julia_location,
                "optimistix_location": optimistix_location,
                "julia_optimistix_abs_delta": julia_optimistix_delta,
                "diffrax_max_endpoint_error_to_julia_floor": diffrax_max_error,
                "tolerance": TOLERANCE,
            },
            "erased_drive_control": {
                "status": "PASS" if erased_flip_pass else "FAIL",
                "julia_active_basin_removed": julia_leg.get("erased_basin_count") == 0,
                "diffrax_starts_frozen": diffrax_leg["erased_max_motion"] <= SOLVER_TOLERANCE,
                "optimistix_nonminimal_start_survives": abs(optimistix_leg["erased_value"] - 12.0) <= SOLVER_TOLERANCE,
                "z3_polarity_flips_unsat_to_sat": (
                    z3_leg["verdicts"]["strict_active_interior_fixed_point"] == "unsat"
                    and z3_leg["verdicts"]["erased_strict_active_fixed_point"] == "sat"
                ),
            },
        },
        "per_leg": {
            "julia_attractors": julia_leg["status"],
            "jax_diffrax": diffrax_leg["status"],
            "jax_optimistix": optimistix_leg["status"],
            "z3_active_floor": z3_leg["status"],
            "cross_engine_agreement": "PASS" if cross_engine_pass else "FAIL",
            "erased_drive_control": "PASS" if erased_flip_pass else "FAIL",
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "Attractors.jl",
                "qualified_api/function": "Attractors.AttractorsViaProximity + Attractors.basins_of_attraction",
                "input_object": "DeterministicIteratedMap of F over the shared above-floor start grid",
                "output_object": "active and erased basin labels/counts",
                "positive_case": "all active-drive starts receive the one positive boundary-attractor label",
                "negative/erased_control": "zero drive leaves every above-floor start unassigned/lost",
                "boundary_case": "F(3)=3 while F(2.5)=2.5 records the global fixed-set ceiling",
                "demotion_condition": "any lost active start, any positive erased basin, or wrong Julia project",
                "gates": ["julia_attractors", "erased_drive_control", "all_pass"],
            },
            {
                "tool": "diffrax",
                "qualified_api/function": "diffrax.ODETerm + diffrax.diffeqsolve + diffrax.Tsit5",
                "input_object": "residual flow dx/dt=F(x)-x over the shared start grid",
                "output_object": "active and erased relaxation endpoints",
                "positive_case": "all active endpoints approach 3 within 1e-8",
                "negative/erased_control": "zero-drive endpoints remain at their starts",
                "boundary_case": "residual flow vanishes at x=3",
                "demotion_condition": "solver failure, endpoint disagreement, or erased motion",
                "gates": ["jax_diffrax", "cross_engine_agreement", "erased_drive_control", "all_pass"],
            },
            {
                "tool": "optimistix",
                "qualified_api/function": "optimistix.fixed_point + optimistix.FixedPointIteration",
                "input_object": "direct iteration of F from x0=12",
                "output_object": "active and erased fixed-point candidates",
                "positive_case": "active candidate approaches 3 within 1e-8 with small residual",
                "negative/erased_control": "identity map returns the nonminimal start 12",
                "boundary_case": (
                    "measured candidate is checked against the Julia location to 1e-8 in the independent "
                    "cross-engine agreement leg and is not used as a formal Z3 premise"
                ),
                "demotion_condition": "solver failure, residual failure, or erased candidate approaching 3",
                "gates": ["jax_optimistix", "cross_engine_agreement", "erased_drive_control", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check over RealVal, If, and exact affine constraints",
                "input_object": (
                    "the measured Julia attractor decimal as the exact symbolic floor plus the exact drive; "
                    "the Optimistix candidate remains an independent cross-engine check"
                ),
                "output_object": "active-branch UNSAT, global-below-floor SAT, erased-drive SAT",
                "positive_case": "no strict active-interior fixed point and exact boundary is SAT",
                "negative/erased_control": "zero drive admits a strict-above fixed point",
                "boundary_case": "full piecewise map explicitly admits below-floor fixed points",
                "demotion_condition": "missing polarity flip, missing measured-value binding, or false global-minimality claim",
                "gates": ["z3_active_floor", "erased_drive_control", "all_pass"],
            },
        ],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_location,
                "jax_diffrax_max_endpoint": max(diffrax_leg["active_endpoints"]),
                "jax_optimistix": optimistix_location,
            },
            "max_abs_deviation_from_floor": max(
                abs(float(julia_location) - FLOOR) if julia_location is not None else float("inf"),
                diffrax_max_error,
                abs(optimistix_location - FLOOR),
            ),
            "tolerance": TOLERANCE,
        },
        "claim_ceiling": (
            "tool-lego fit evidence for one supplied active-boundary basin and its controls; "
            "cross-engine agreement is diagnostic, Z3 is active-branch-only, and no lego, "
            "scientific basin, manifold, bridge, axis, or formal admission is promoted"
        ),
        "blocked_consumers": [
            "lego promotion",
            "global fixed-point minimality or uniqueness",
            "scientific basin or manifold admission",
            "bridge or axis claims",
            "formal admission",
        ],
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for name, status in result["per_leg"].items():
        print(f"{status} {name}")
    print("PASS basin_chain_d" if all_pass else "FAIL basin_chain_d")
    print(f"RECEIPT {RESULT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
