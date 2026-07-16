#!/usr/bin/env python3
"""Execute the supplied manifold L1--L8 instruments and retain raw receipts.

This runner records what actually executed.  A local PASS is not converted to
Ratchet admission; every source instrument declares itself scratch diagnostic.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = HERE / "layer_execution_receipts.json"
LOCAL_DEPS = ROOT / ".ratchet_deps"

SCRIPTS = {
    f"L{index}": ROOT / "sims_and_scripts" / name
    for index, name in enumerate(
        [
            "manifold_L1_probe_quotient_sim.py",
            "manifold_L2_rank_strata_marginals_sim.py",
            "manifold_L3_spinor_hopf_sim.py",
            "manifold_L4_local_weyl_factors_sim.py",
            "manifold_L5_nested_shells_schmidt_strata_sim.py",
            "manifold_L6_shell_metric_bkm_connection_sim.py",
            "manifold_L7_shell_connection_holonomy_sim.py",
            "manifold_L8_global_bundle_chern_quantization_sim.py",
        ],
        start=1,
    )
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        if LOCAL_DEPS.exists():
            sys.path.insert(0, str(LOCAL_DEPS))
            try:
                return importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:
                return None
        return None


def main() -> int:
    env = os.environ.copy()
    if LOCAL_DEPS.exists():
        env["PYTHONPATH"] = str(LOCAL_DEPS) + os.pathsep + env.get("PYTHONPATH", "")
    rows = []
    failures = []
    for layer, script in SCRIPTS.items():
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        stdout = completed.stdout
        local_pass = completed.returncode == 0 and f"PASS manifold_{layer}" in stdout
        # L5--L8 use a slightly longer PASS name; all include a generic PASS manifold_Ln prefix.
        local_pass = completed.returncode == 0 and f"PASS manifold_{layer}" in stdout
        result_path = script.with_name(script.stem + "_results.json")
        result = None
        if result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
        row = {
            "layer": layer,
            "script": str(script.relative_to(ROOT)),
            "source_sha256": sha256(script),
            "returncode": completed.returncode,
            "local_pass": local_pass,
            "stdout": stdout,
            "stderr": completed.stderr,
            "result_file": str(result_path.relative_to(ROOT)) if result_path.exists() else None,
            "result_sha256": sha256(result_path) if result_path.exists() else None,
            "declared_classification": result.get("classification") if isinstance(result, dict) else "scratch_diagnostic_in_source_docstring",
            "declared_promotion_allowed": result.get("promotion_allowed") if isinstance(result, dict) else False,
            "ratchet_admitted": False,
        }
        rows.append(row)
        if not local_pass:
            failures.append(layer)

    receipt = {
        "schema_version": "manifold-layer-execution-receipt/1.0",
        "python": sys.version,
        "dependencies": {
            "numpy": version("numpy"),
            "scipy": version("scipy"),
            "z3-solver": version("z3-solver"),
            "cvc5": version("cvc5"),
        },
        "layers": rows,
        "local_pass_count": sum(bool(row["local_pass"]) for row in rows),
        "local_fail_count": len(failures),
        "ratchet_admitted_layer_count": 0,
        "status": "LOCAL_EXECUTION_COMPLETE__NOT_ADMISSION" if not failures else "LOCAL_EXECUTION_HAS_FAILURES",
    }
    OUTPUT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"local execution: {receipt['local_pass_count']}/8 pass")
    print("Ratchet-admitted manifold layers: 0")
    print(f"receipt: {OUTPUT}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
