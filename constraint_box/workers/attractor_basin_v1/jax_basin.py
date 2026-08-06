#!/usr/bin/env python3
"""Independent JAX/Diffrax receipt for a bounded bistable basin map.

This builder emits raw execution evidence only.  It does not read any peer
engine result and it does not make an admission decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

from jax import config

# This must precede jax.numpy import and every numeric construction.
config.update("jax_enable_x64", True)

import diffrax
import jax
import jax.numpy as jnp
import jaxlib


SIM_ID = "cb_attractor_basin_three_engine_20260801_jax"
H = 0.2
WRONG_H = -0.2
STEPS = 80
DIFFRAX_SEVERANCE_ENV = "CONSTRAINTBOX_TEST_SEVER_DIFFRAX"


def selected_diffeqsolve() -> Any:
    """Return the real API or the controller-selected operation poison."""

    if os.environ.get(DIFFRAX_SEVERANCE_ENV) == "1":
        def severed_diffeqsolve(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("CB_DIFFRAX_OPERATION_SEVERED")

        return severed_diffeqsolve
    return diffrax.diffeqsolve


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def step_map(z: jax.Array, h: jax.Array) -> jax.Array:
    """F_h(x,y) = (x - h*(x^3-x), 0.5*y)."""
    x, y = z[0], z[1]
    return jnp.stack((x - h * (x**3 - x), jnp.float64(0.5) * y))


def potential(x: jax.Array) -> jax.Array:
    """V'(x)=x^3-x, so the x update is one gradient-descent step."""
    return jnp.float64(0.25) * (x**2 - jnp.float64(1.0)) ** 2


potential_grad = jax.grad(potential)


def iterate_one(z0: jax.Array, h: jax.Array) -> jax.Array:
    return jax.lax.fori_loop(
        0,
        STEPS,
        lambda _index, state: step_map(state, h),
        z0,
    )


# Both surfaces are intentional and receipt-bearing.
batched_iterate = jax.jit(jax.vmap(iterate_one, in_axes=(0, None)))
step_jacobian = jax.jacrev(step_map, argnums=0)
batched_jacobian = jax.jit(jax.vmap(step_jacobian, in_axes=(0, None)))


def diffrax_terminal(grid: jax.Array, h: jax.Array) -> jax.Array:
    """Embed the discrete map exactly as 80 fixed Diffrax Euler steps."""

    def vector_field(
        _time: jax.Array, state: jax.Array, parameter: jax.Array
    ) -> jax.Array:
        x = state[..., 0]
        y = state[..., 1]
        return jnp.stack(
            (
                parameter * (x - x**3),
                -jnp.float64(0.5) * y,
            ),
            axis=-1,
        )

    solution = selected_diffeqsolve()(
        diffrax.ODETerm(vector_field),
        diffrax.Euler(),
        t0=jnp.float64(0.0),
        t1=jnp.float64(STEPS),
        dt0=jnp.float64(1.0),
        y0=grid,
        args=h,
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.ConstantStepSize(),
        max_steps=STEPS,
        throw=True,
    )
    return solution.ys[-1]


compiled_diffrax_terminal = jax.jit(diffrax_terminal)


def scalar(value: Any) -> Any:
    """Explicit receipt-only device transfer, after every claim gate is set."""
    return jax.device_get(value).item()


def json_differences(left: Any, right: Any, prefix: str = "") -> list[dict[str, Any]]:
    """Return deterministic field-level differences for two JSON values."""
    if isinstance(left, dict) and isinstance(right, dict):
        differences: list[dict[str, Any]] = []
        for key in sorted(set(left) | set(right)):
            path = f"{prefix}.{key}" if prefix else key
            if key not in left:
                differences.append(
                    {"path": path, "left": "<missing>", "right": right[key]}
                )
            elif key not in right:
                differences.append(
                    {"path": path, "left": left[key], "right": "<missing>"}
                )
            else:
                differences.extend(json_differences(left[key], right[key], path))
        return differences
    if left != right:
        return [{"path": prefix, "left": left, "right": right}]
    return []


def portable_receipt_locator(path: Path) -> str:
    """Identify a replay receipt without embedding a user or host root path."""
    return f"{path.parent.name}/{path.name}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--audit-against",
        type=Path,
        help="Optional same-lane prior receipt for a post-run semantic replay audit.",
    )
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(__file__).resolve()
    runtime_path = Path(sys.executable).resolve()

    # Integer construction makes the requested decimal grid and exact x=0
    # boundary explicit rather than relying on a tolerance classification.
    xs = jnp.arange(-15, 16, dtype=jnp.float64) / jnp.float64(10.0)
    ys = jnp.arange(-5, 6, dtype=jnp.float64) / jnp.float64(10.0)
    mesh_x, mesh_y = jnp.meshgrid(xs, ys, indexing="ij")
    grid = jnp.stack((mesh_x.reshape(-1), mesh_y.reshape(-1)), axis=1)
    initial_x = grid[:, 0]

    h = jnp.float64(H)
    wrong_h = jnp.float64(WRONG_H)

    terminal = batched_iterate(grid, h)
    terminal_replay = batched_iterate(grid, h)
    labels = jnp.sign(terminal[:, 0]).astype(jnp.int32)

    negative_count = jnp.sum(labels == -1)
    boundary_count = jnp.sum(labels == 0)
    positive_count = jnp.sum(labels == 1)
    nonboundary = initial_x != jnp.float64(0.0)
    boundary = initial_x == jnp.float64(0.0)
    left_adjacent = initial_x == jnp.float64(-0.1)
    right_adjacent = initial_x == jnp.float64(0.1)

    endpoint_residual = jnp.max(
        jnp.where(
            nonboundary,
            jnp.abs(jnp.abs(terminal[:, 0]) - jnp.float64(1.0)),
            jnp.float64(0.0),
        )
    )
    y_residual = jnp.max(jnp.abs(terminal[:, 1]))

    fixed_points = jnp.array(
        [[-1.0, 0.0], [0.0, 0.0], [1.0, 0.0]], dtype=jnp.float64
    )
    jacobians = batched_jacobian(fixed_points, h)
    wrong_jacobians = batched_jacobian(fixed_points, wrong_h)
    spectral_radii = jnp.max(jnp.abs(jnp.linalg.eigvals(jacobians)), axis=1)
    wrong_spectral_radii = jnp.max(
        jnp.abs(jnp.linalg.eigvals(wrong_jacobians)), axis=1
    )

    grad_samples = jnp.array([-1.25, -0.4, 0.0, 0.4, 1.25], dtype=jnp.float64)
    gradients = jax.vmap(potential_grad)(grad_samples)
    mapped_x = jax.vmap(
        lambda x: step_map(jnp.stack((x, jnp.float64(0.0))), h)[0]
    )(grad_samples)
    gradient_identity_error = jnp.max(
        jnp.abs(mapped_x - (grad_samples - h * gradients))
    )

    # Diffrax Euler with dt=1 is not an approximate side readout here: its
    # update is exactly the declared discrete map at every one of 80 steps.
    diffrax_result = compiled_diffrax_terminal(grid, h)
    diffrax_replay = compiled_diffrax_terminal(grid, h)
    diffrax_match_error = jnp.max(jnp.abs(diffrax_result - terminal))

    partition_ok = (
        (negative_count == 165)
        & (boundary_count == 11)
        & (positive_count == 165)
        & (endpoint_residual < jnp.float64(1e-9))
        & (y_residual < jnp.float64(1e-20))
    )
    boundary_ok = (
        jnp.all(terminal[boundary, 0] == jnp.float64(0.0))
        & jnp.all(labels[left_adjacent] == -1)
        & jnp.all(labels[right_adjacent] == 1)
        & (boundary_count == 11)
    )
    stability_ok = (
        (spectral_radii[0] < jnp.float64(1.0))
        & (spectral_radii[1] > jnp.float64(1.0))
        & (spectral_radii[2] < jnp.float64(1.0))
    )
    gradient_identity_ok = gradient_identity_error == jnp.float64(0.0)
    replay_ok = jnp.array_equal(terminal, terminal_replay)
    diffrax_ok = (
        (diffrax_match_error < jnp.float64(1e-12))
        & jnp.array_equal(diffrax_result, diffrax_replay)
    )

    # Wrong-sign hostile control: h=-0.2 makes the origin locally stable,
    # makes +/-1 unstable, and destroys most valid terminal-attractor
    # assignments even though terminal signs alone can remain unchanged.
    wrong_terminal = batched_iterate(grid, wrong_h)
    wrong_finite = jnp.all(jnp.isfinite(wrong_terminal), axis=1)
    wrong_valid_assignment = wrong_finite & (
        jnp.abs(jnp.abs(wrong_terminal[:, 0]) - jnp.float64(1.0))
        < jnp.float64(1e-6)
    )
    wrong_valid_assignment_count = jnp.sum(wrong_valid_assignment & nonboundary)
    wrong_sign_caught = (
        (wrong_spectral_radii[0] > jnp.float64(1.0))
        & (wrong_spectral_radii[1] < jnp.float64(1.0))
        & (wrong_spectral_radii[2] > jnp.float64(1.0))
        & (wrong_valid_assignment_count < 330)
    )

    erased_labels = jnp.zeros_like(labels)
    erased_mismatch_count = jnp.sum(erased_labels != labels)
    erased_control_caught = (
        (erased_mismatch_count == 330)
        & ~(
            (jnp.sum(erased_labels == -1) == 165)
            & (jnp.sum(erased_labels == 0) == 11)
            & (jnp.sum(erased_labels == 1) == 165)
        )
    )

    direct_jax_checks = (
        partition_ok
        & boundary_ok
        & stability_ok
        & gradient_identity_ok
        & replay_ok
    )
    all_pass = (
        direct_jax_checks
        & diffrax_ok
        & wrong_sign_caught
        & erased_control_caught
    )

    runtime_manifest = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": runtime_path.name,
        "python_executable_locator_kind": "basename_plus_content_hash",
        "python_executable_sha256": sha256_file(runtime_path),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "jax_backend": jax.default_backend(),
        "jax_devices": [str(device) for device in jax.devices()],
        "jax_enable_x64": bool(jax.config.x64_enabled),
        "environment": {
            "JAX_PLATFORM_NAME": os.environ.get("JAX_PLATFORM_NAME"),
            "NUMBA_CACHE_DIR": os.environ.get("NUMBA_CACHE_DIR"),
        },
    }
    runtime_manifest_sha256 = canonical_sha256(runtime_manifest)

    all_pass_bool = bool(scalar(all_pass))
    receipt = {
        "schema_version": "three_engine_sim_engine_fragment_v1",
        "sim_id": SIM_ID,
        "name": "JAX x64 fixed-grid bistable attractor-basin receipt",
        "version": "1.0.1",
        "role_id": "jax_batched_workhorse_sim_builder",
        "engine": "jax",
        "builder_scope": "raw execution evidence only; no admission or self-audit",
        "source_path": source_path.name,
        "source_locator_kind": "portable_basename_plus_content_hash",
        "source_sha256": sha256_file(source_path),
        "run_command": "${SIM_PY} jax_basin.py --output-dir <OUTPUT_DIR>",
        "run_instance": {"output_locator": output_dir.name},
        "runtime_manifest": runtime_manifest,
        "runtime_manifest_sha256": runtime_manifest_sha256,
        "package_versions": {
            "jax": jax.__version__,
            "jaxlib": jaxlib.__version__,
            "diffrax": diffrax.__version__,
        },
        "packages_used": ["jax", "jax.numpy", "jaxlib", "diffrax"],
        "aligned_packages_load_bearing": ["jax", "diffrax"],
        "reads_peer_result": False,
        "claim_path_host_copy": False,
        "receipt_serialization_device_transfer": "jax.device_get after all gates",
        "claim": {
            "kind": "bounded_finite_grid_basin_partition_and_local_stability",
            "map": "F_h(x,y)=(x-h*(x^3-x),0.5*y)",
            "h": H,
            "steps": STEPS,
            "dtype": "float64",
            "grid": {
                "x": "-1.5:0.1:1.5",
                "y": "-0.5:0.1:0.5",
                "points": int(grid.shape[0]),
            },
            "expected_stable_attractors": [[-1.0, 0.0], [1.0, 0.0]],
            "expected_unstable_boundary": "x=0",
            "classification": "terminal x sign; boundary only exact x=0",
        },
        "result": {
            "partition_counts": {
                "negative": int(scalar(negative_count)),
                "boundary": int(scalar(boundary_count)),
                "positive": int(scalar(positive_count)),
            },
            "terminal_attractor_max_abs_error": float(scalar(endpoint_residual)),
            "terminal_y_max_abs": float(scalar(y_residual)),
            "fixed_point_spectral_radii": [
                float(value) for value in jax.device_get(spectral_radii).tolist()
            ],
            "gradient_identity_max_abs_error": float(
                scalar(gradient_identity_error)
            ),
            "diffrax_direct_max_abs_error": float(scalar(diffrax_match_error)),
            "direct_jax_checks_pass": bool(scalar(direct_jax_checks)),
            "positive_case_pass": bool(scalar(all_pass)),
        },
        "controls": {
            "wrong_sign_h": {
                "h": WRONG_H,
                "fixed_point_spectral_radii": [
                    float(value)
                    for value in jax.device_get(wrong_spectral_radii).tolist()
                ],
                "valid_nonboundary_attractor_assignments": int(
                    scalar(wrong_valid_assignment_count)
                ),
                "nonfinite_terminal_count": int(
                    scalar(jnp.sum(~wrong_finite))
                ),
                "caught": bool(scalar(wrong_sign_caught)),
            },
            "erased_labels": {
                "mismatch_count": int(scalar(erased_mismatch_count)),
                "caught": bool(scalar(erased_control_caught)),
            },
            "boundary": {
                "exact_boundary_seed_count": int(scalar(jnp.sum(boundary))),
                "adjacent_negative_seed_count": int(
                    scalar(jnp.sum(left_adjacent))
                ),
                "adjacent_positive_seed_count": int(
                    scalar(jnp.sum(right_adjacent))
                ),
                "passed": bool(scalar(boundary_ok)),
            },
            "replay": {
                "direct_exact_match": bool(scalar(replay_ok)),
                "diffrax_exact_match": bool(
                    scalar(jnp.array_equal(diffrax_result, diffrax_replay))
                ),
            },
            "diffrax_operation_requirement": {
                "diffrax_value_gate_passed": bool(scalar(diffrax_ok)),
                "requires_controller_operation_poison": True,
                "controller_poison_environment_key": DIFFRAX_SEVERANCE_ENV,
            },
        },
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(iterate_one))",
                "input_object": "341x2 float64 fixed initial grid, h=0.2, 80 steps",
                "output_object": "341x2 terminal grid",
                "positive_case": "165 negative, 11 exact boundary, 165 positive",
                "negative/erased_control": "h=-0.2 stability flip and erased labels",
                "boundary_case": "all 11 exact x=0 seeds stay on boundary",
                "demotion_condition": "missing batched terminal grid or replay drift",
                "gates": ["finite_grid_partition", "all_pass"],
            },
            {
                "tool": "jax",
                "qualified_api/function": "jax.jacrev(step_map)",
                "input_object": "fixed points (-1,0),(0,0),(1,0)",
                "output_object": "three 2x2 Jacobians and spectral radii",
                "positive_case": "+/-1 stable and origin unstable at h=0.2",
                "negative/erased_control": "stability polarity flips at h=-0.2",
                "boundary_case": "origin is the exact separatrix fixed point",
                "demotion_condition": "local stability claim removed",
                "gates": ["stability", "wrong_sign_control", "all_pass"],
            },
            {
                "tool": "jax",
                "qualified_api/function": "jax.grad(potential)",
                "input_object": "five bounded x samples",
                "output_object": "V'(x) and mapped-x identity residual",
                "positive_case": "F_h x-step equals x-h*grad(V)",
                "negative/erased_control": "wrong h is checked separately by jacrev",
                "boundary_case": "grad(V)(0)=0",
                "demotion_condition": "gradient interpretation removed",
                "gates": ["gradient_identity", "all_pass"],
            },
            {
                "tool": "diffrax",
                "qualified_api/function": (
                    "diffrax.diffeqsolve(ODETerm, Euler, ConstantStepSize, "
                    "SaveAt)"
                ),
                "input_object": "341x2 grid as one vector state, dt=1, t=0..80",
                "output_object": "341x2 terminal grid after exactly 80 Euler updates",
                "positive_case": "terminal agrees with declared discrete map",
                "negative/erased_control": "controller reruns this source with the named Diffrax operation poisoned",
                "boundary_case": "exact x=0 states stay zero",
                "demotion_condition": (
                    "remove/bypass Diffrax or mismatch direct map: lane becomes "
                    "bare-JAX and cannot pass rich-tool gate"
                ),
                "gates": ["diffrax_consistency", "all_pass"],
            },
        ],
        "tool_integration_depth": {
            "jax": "claim_load_bearing",
            "jax.numpy": "array_support",
            "jaxlib": "runtime_support",
            "diffrax": "claim_load_bearing",
        },
        "witness_trace": [
            "constructed exact decimal grid from integer indices",
            "ran jitted vmapped 80-step discrete map",
            "classified terminal sign with exact-zero boundary",
            "computed fixed-point Jacobians and potential gradient identity",
            "ran Diffrax Euler embedding of the same 80 discrete updates",
            "ran wrong-sign, erased-label, boundary, and replay controls",
            "declared the controller-owned Diffrax operation-poison requirement",
        ],
        "all_pass": all_pass_bool,
        "exit_code": 0 if all_pass_bool else 1,
        "classification": "tool_lego_fit_probe",
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "continuous_basin_proof": False,
        "continuous_proof_blockers": [
            "no interval enclosure",
            "no reachability certificate",
            "no SOS/Lyapunov certificate",
            "finite grid and local Jacobians do not prove the continuous basin",
        ],
        "admission_decision": None,
    }

    # The semantic projection deliberately excludes run routing and host
    # environment identity. Those remain visible in the receipt and are
    # compared separately by the replay audit, but they cannot make identical
    # mathematics look different merely because a directory or host changed.
    semantic_projection = {
        key: value
        for key, value in receipt.items()
        if key
        not in {
            "run_instance",
            "runtime_manifest",
            "runtime_manifest_sha256",
        }
    }
    receipt["semantic_replay"] = {
        "projection_schema": "jax_basin_semantic_projection_v1",
        "projection_sha256": canonical_sha256(semantic_projection),
        "excluded_nonsemantic_fields": [
            "run_instance",
            "runtime_manifest",
            "runtime_manifest_sha256",
        ],
    }

    receipt_path = output_dir / "jax_basin_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    audit_path: Path | None = None
    audit_pass = True
    if args.audit_against is not None:
        prior_path = args.audit_against.resolve()
        if not prior_path.is_file():
            raise FileNotFoundError(f"prior replay receipt not found: {prior_path}")
        prior_receipt = json.loads(prior_path.read_text(encoding="utf-8"))
        differences = json_differences(prior_receipt, receipt)
        classified_differences = []
        unexpected_differences = []
        for difference in differences:
            path = difference["path"]
            if path.startswith("run_instance."):
                classification = "path_only"
            elif path == "runtime_manifest_sha256" or path.startswith(
                "runtime_manifest."
            ):
                classification = "environment_only"
            else:
                classification = "semantic_or_unexpected"
                unexpected_differences.append(difference)
            classified_differences.append(
                {**difference, "classification": classification}
            )

        semantic_match = (
            prior_receipt.get("semantic_replay", {}).get("projection_sha256")
            == receipt["semantic_replay"]["projection_sha256"]
        )
        runtime_match = (
            prior_receipt.get("runtime_manifest_sha256")
            == receipt["runtime_manifest_sha256"]
        )
        audit_pass = bool(
            semantic_match
            and not unexpected_differences
            and prior_receipt.get("all_pass") is True
            and receipt["all_pass"] is True
            and prior_receipt.get("source_sha256") == receipt["source_sha256"]
            and prior_receipt.get("package_versions") == receipt["package_versions"]
        )
        replay_audit = {
            "schema_version": "jax_basin_semantic_replay_audit_v1",
            "left_receipt": portable_receipt_locator(prior_path),
            "right_receipt": portable_receipt_locator(receipt_path),
            "left_receipt_sha256": sha256_file(prior_path),
            "right_receipt_sha256": sha256_file(receipt_path),
            "exact_receipt_match": sha256_file(prior_path)
            == sha256_file(receipt_path),
            "semantic_projection_match": semantic_match,
            "runtime_environment_match": runtime_match,
            "differences": classified_differences,
            "unexpected_differences": unexpected_differences,
            "path_or_environment_only_differences": bool(
                differences and not unexpected_differences
            ),
            "comparison_explanation": (
                "Output routing and runtime-environment identity are retained "
                "for audit but excluded from the mathematical semantic projection."
            ),
            "source_hash_match": prior_receipt.get("source_sha256")
            == receipt["source_sha256"],
            "package_versions_match": prior_receipt.get("package_versions")
            == receipt["package_versions"],
            "both_runs_all_pass": prior_receipt.get("all_pass") is True
            and receipt["all_pass"] is True,
            "audit_pass": audit_pass,
            "claim_ceiling": "scratch_diagnostic",
            "admission_decision": None,
        }
        audit_path = output_dir / "jax_semantic_replay_audit.json"
        audit_path.write_text(
            json.dumps(replay_audit, indent=2, sort_keys=True, allow_nan=False)
            + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "sim_id": SIM_ID,
                "all_pass": all_pass_bool,
                "audit_pass": audit_pass if args.audit_against else None,
                "receipt": str(receipt_path),
                "replay_audit": str(audit_path) if audit_path else None,
                "semantic_projection_sha256": receipt["semantic_replay"][
                    "projection_sha256"
                ],
                "source_sha256": receipt["source_sha256"],
                "runtime_manifest_sha256": runtime_manifest_sha256,
            },
            sort_keys=True,
        )
    )
    return 0 if all_pass_bool and audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
