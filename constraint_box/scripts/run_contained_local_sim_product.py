#!/usr/bin/env python3
"""Run the contained CB source against explicitly supplied local resources.

This is deliberately a composition runner, not a package installer.  The ZIP
contains CB, ClaimGate, Mini-LevOS, workers, and this controller; CPython,
JAX/Diffrax, PyTorch/PyG, Julia/Attractors, and a local Lev result remain
explicit external resources.  A successful run is bounded integration evidence
only and never authorizes release or promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "constraintbox.contained-local-sim-product-receipt.v1"


class ProductRunError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _object(stdout: str, name: str) -> dict[str, Any]:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ProductRunError(f"{name} did not emit JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ProductRunError(f"{name} JSON root must be an object")
    return value


def _run(
    name: str,
    command: list[str],
    *,
    environment: dict[str, str],
    expected_exit_codes: frozenset[int] = frozenset({0}),
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=1800,
    )
    if completed.returncode not in expected_exit_codes:
        raise ProductRunError(
            f"{name} exited {completed.returncode}: {completed.stderr[-1000:]}"
        )
    value = _object(completed.stdout, name)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "result": value,
    }


def _resolve_file(path: Path, label: str) -> Path:
    # Keep the supplied launcher path. Resolving a virtual-environment Python
    # symlink before execution silently discards its site-packages and defeats
    # the explicit local-resource selection made by the operator.
    invocation = path.expanduser().absolute()
    result = invocation.resolve(strict=True)
    if not result.is_file():
        raise ProductRunError(f"{label} is not a file: {result}")
    return invocation


def _resolve_dir(path: Path, label: str) -> Path:
    result = path.expanduser().resolve(strict=True)
    if not result.is_dir():
        raise ProductRunError(f"{label} is not a directory: {result}")
    return result


def run_product(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output_dir.expanduser().resolve()
    if output.exists():
        raise ProductRunError(f"output directory must be new: {output}")
    worker_python = _resolve_file(args.worker_python, "worker Python")
    julia = _resolve_file(args.julia, "Julia")
    julia_project = _resolve_dir(args.julia_project, "Julia project")
    external_sim_estate = _resolve_dir(args.external_sim_estate, "external sim estate")
    if not (julia_project / "Project.toml").is_file() or not (julia_project / "Manifest.toml").is_file():
        raise ProductRunError("Julia project must contain Project.toml and Manifest.toml")
    if (args.lev_source_run is None) != (args.lev_execution_id is None) or (args.lev_source_run is None) != (args.lev_suite_id is None):
        raise ProductRunError("Lev observation requires --lev-source-run, --lev-execution-id, and --lev-suite-id together")

    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["CONSTRAINTBOX_JULIA_BIN"] = str(julia)
    environment["CONSTRAINTBOX_JULIA_PROJECT"] = str(julia_project)
    environment["CONSTRAINTBOX_WORKER_PYTHON"] = str(worker_python)
    # The package stays source-contained while the larger engine estate is an
    # explicit local binding. This permits a fresh extraction to run the same
    # fixed workers without copying the entire surrounding checkout into ZIP.
    environment["CONSTRAINTBOX_EXTERNAL_SIM_ESTATE"] = str(external_sim_estate)
    run_id = "contained-local-sim-product-v1"

    suite = _run(
        "capability_suite",
        [str(worker_python), "-B", "-m", "constraintbox", "capability-suite", "--request-id", run_id, "--run-dir", str(output / "capability-suite")],
        environment=environment,
    )
    suite_receipt = output / "capability-suite" / "capability_suite_receipt.json"
    if suite["result"].get("disposition") != "ELIGIBLE" or not suite_receipt.is_file():
        raise ProductRunError("capability suite did not produce an ELIGIBLE retained receipt")

    basin = _run(
        "attractor_basin",
        [
            str(worker_python), "-B", str(ROOT / "workers" / "attractor_basin_v1" / "basin_controller.py"),
            "--constraintbox-root", str(ROOT), "--worker-python-runtime", str(worker_python),
            "--julia-runtime", str(julia), "--julia-project", str(julia_project),
            "--worker-root", str(ROOT / "workers" / "attractor_basin_v1"), "--output-dir", str(output / "attractor-basin"),
        ],
        environment=environment,
    )
    basin_envelope = output / "attractor-basin" / "controller_envelope.json"
    if basin["result"].get("bounded_run_status") != "PASS" or not basin_envelope.is_file():
        raise ProductRunError("attractor-basin controller did not retain a PASS envelope")

    admission = _run(
        "sim_admission",
        [
            str(worker_python), "-B", "-m", "constraintbox", "admit-sim-evidence",
            "--capability-suite", str(suite_receipt), "--attractor-basin-envelope", str(basin_envelope),
            "--run-dir", str(output / "sim-admission"),
        ],
        environment=environment,
    )
    if admission["result"].get("disposition") != "ELIGIBLE":
        raise ProductRunError("ClaimGate did not admit the fixed bounded sim evidence")

    parity = _run(
        "shared_affine_parity",
        [str(worker_python), "-B", "-m", "constraintbox", "shared-affine-parity", "--run-dir", str(output / "shared-affine-parity")],
        environment=environment,
    )
    if parity["result"].get("state") != "CONSISTENT":
        raise ProductRunError("four-runtime shared affine parity was not CONSISTENT")

    lev: dict[str, Any] | None = None
    if args.lev_source_run is not None:
        lev_source = _resolve_dir(args.lev_source_run, "Lev source run")
        lev = _run(
            "lev_observation",
            [
                str(worker_python), "-B", "-m", "constraintbox", "observe-lev-eval",
                "--request-id", run_id, "--source-run-dir", str(lev_source),
                "--expected-execution-id", args.lev_execution_id, "--expected-suite-id", args.lev_suite_id,
                "--run-dir", str(output / "lev-observation"),
            ],
            environment=environment,
            expected_exit_codes=frozenset({4}),
        )
        if (
            lev["result"].get("terminal") != "PARKED"
            or lev["result"].get("capture_state") != "retained"
            or lev["result"].get("replay_state") != "retained_snapshot_rechecked"
        ):
            raise ProductRunError("Lev result was not retained and replay-checked by the CB observer")

    receipt = {
        "schema": SCHEMA,
        "state": "VERIFIED",
        "source_root": str(ROOT),
        "source_product": "contained ConstraintBox source plus local resource bindings",
        "local_resources": {
            "worker_python": str(worker_python), "worker_python_sha256": _sha256(worker_python),
            "julia": str(julia), "julia_sha256": _sha256(julia),
            "julia_project": str(julia_project), "julia_project_sha256": _sha256(julia_project / "Project.toml"),
            "julia_manifest_sha256": _sha256(julia_project / "Manifest.toml"),
            "external_sim_estate": str(external_sim_estate),
        },
        "runs": {
            "capability_suite": suite,
            "attractor_basin": basin,
            "sim_admission": admission,
            "shared_affine_parity": parity,
            "lev_observation": lev,
        },
        "external_estate_included": False,
        "java_tlc_apalache_used": False,
        "release_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": "one fresh local execution of the contained CB source against explicitly supplied Python/Julia resources, plus optional retained Lev observation; bounded integration only, not whole-estate readiness, scientific proof, release, or promotion",
    }
    (output / "contained_local_sim_product_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--worker-python", type=Path, required=True)
    parser.add_argument("--julia", type=Path, required=True)
    parser.add_argument("--julia-project", type=Path, required=True)
    parser.add_argument("--external-sim-estate", type=Path, required=True)
    parser.add_argument("--lev-source-run", type=Path)
    parser.add_argument("--lev-execution-id")
    parser.add_argument("--lev-suite-id")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = run_product(args)
    except (OSError, ProductRunError, subprocess.TimeoutExpired, ValueError) as exc:
        print(json.dumps({"schema": SCHEMA, "state": "FAILED", "error": str(exc), "promotion_allowed": False}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
