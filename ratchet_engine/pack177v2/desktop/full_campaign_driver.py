#!/usr/bin/env python3
"""Run every locally available fuel-bearing Pack 177 lane without a shell."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "receipts" / "full_campaign_receipt.json"


def execute(name: str, command: list[str], available: bool = True) -> dict[str, object]:
    if not available:
        return {
            "name": name,
            "state": "BLOCKED_DEPENDENCY_UNAVAILABLE",
            "command": command,
            "returncode": None,
        }
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return {
        "name": name,
        "state": "PASS" if completed.returncode == 0 else "FAIL",
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
    }


def main() -> int:
    python = sys.executable
    steps: list[dict[str, object]] = []
    required = [
        ("exact-self-test", [python, "-B", "source/source_balanced_completion_ratchet.py", "--self-test"]),
        ("exact-run", [python, "-B", "source/source_balanced_completion_ratchet.py", "--run"]),
        ("exact-validate", [python, "-B", "source/source_balanced_completion_ratchet.py", "--validate"]),
        ("fuel-self-test", [python, "-B", "source/compile_fuel_obligations.py", "--self-test"]),
        ("fuel-run", [python, "-B", "source/compile_fuel_obligations.py", "--run"]),
        ("fuel-validate", [python, "-B", "source/compile_fuel_obligations.py", "--validate"]),
        ("lev-graph-projection", [python, "-B", "source/build_lev_context_graph.py"]),
        ("cvc5-instance-generation", [python, "-B", "solver/generate_cvc5_instances.py"]),
    ]
    for name, command in required:
        steps.append(execute(name, command))

    jax_available = importlib.util.find_spec("jax") is not None
    torch_available = importlib.util.find_spec("torch") is not None
    julia_path = shutil.which("julia")
    steps.append(execute("jax-census", [python, "-B", "tri-engine/run_jax.py"], jax_available))
    steps.append(execute("pytorch-census", [python, "-B", "tri-engine/run_pytorch.py"], torch_available))
    steps.append(
        execute(
            "julia-census",
            [julia_path or "julia", "--startup-file=no", "tri-engine/run_julia.jl"],
            julia_path is not None,
        )
    )
    engine_states = {str(row["name"]): row["state"] for row in steps}
    all_engines = all(
        engine_states.get(name) == "PASS"
        for name in ("jax-census", "pytorch-census", "julia-census")
    )
    steps.append(
        execute(
            "tri-engine-agreement",
            [python, "-B", "tri-engine/check_agreement.py"],
            all_engines,
        )
    )

    z3_available = importlib.util.find_spec("z3") is not None
    cvc5_path = shutil.which("cvc5")
    steps.append(execute("z3-census", [python, "-B", "solver/run_z3_anf_census.py"], z3_available))
    steps.append(
        execute(
            "cvc5-census",
            [python, "-B", "solver/run_cvc5_instances.py", "--cvc5", cvc5_path or "cvc5"],
            cvc5_path is not None,
        )
    )

    required_pass = all(row["state"] == "PASS" for row in steps[:8])
    optional_fail = any(row["state"] == "FAIL" for row in steps[8:])
    blocked = [row["name"] for row in steps if row["state"] == "BLOCKED_DEPENDENCY_UNAVAILABLE"]
    if not required_pass or optional_fail:
        status = "FAIL"
    elif blocked:
        status = "HOLD_MISSING_ENGINE_OR_SOLVER_DEPENDENCY"
    else:
        status = "PASS_MATHEMATICAL_PORTS__HOLD_NATIVE_LEV_AND_LIVE_INTEGRATION"
    receipt = {
        "schema_version": "ratchet.full-local-campaign/0.2",
        "status": status,
        "steps": steps,
        "blocked_dependencies": blocked,
        "native_lev_invoked": False,
        "live_ratchet_integrated": False,
        "mathematical_authority_assigned_to_orchestrator": False,
        "numpy_on_claim_path": False,
        "fuel_compiler_executed": required_pass,
        "claim_ceiling": "finite completion calibration, residual-to-obligation compilation, and port/solver fidelity; no source science or owner hypothesis admitted",
    }
    OUTPUT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if status.startswith("PASS") else 2 if status.startswith("HOLD") else 1


if __name__ == "__main__":
    raise SystemExit(main())
