#!/usr/bin/env python3
"""Summarize available rich sim libraries versus current envelope usage."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PYTHON_MODULES = [
    "jax", "diffrax", "dynamiqs", "netket", "qutip", "quimb", "cotengra", "jaxopt", "lineax", "jraph", "ott", "e3nn_jax", "optax", "equinox", "flax",
    "z3", "cvc5", "sympy", "toponetx", "gudhi", "rustworkx", "networkx", "xgi",
    "torch", "torch_ga", "torch_geometric", "clifford", "geomstats", "e3nn", "functorch", "numpy", "scipy", "mpmath",
]

JULIA_MODULES = [
    "QuantumOptics", "QuantumToolbox", "Yao", "QXTools", "QXZoo", "QXGraphDecompositions",
    "Attractors", "DynamicalSystems", "Basins", "Z3", "CVC5",
    "CliffordAlgebras", "Grassmann", "Octonions", "Quaternions", "StaticArrays", "Manifolds", "CombinatorialSpaces",
    "DifferentialEquations", "ITensors", "ITensorMPS", "ITensorNetworks", "TensorOperations", "Symbolics", "Graphs",
    "PythonCall", "DLPack", "CUDA", "Reactant", "Enzyme", "Flux", "Lux", "GraphNeuralNetworks", "GraphNeuralNets",
]

FAMILY = {
    "julia_qit": ["QuantumOptics", "QuantumToolbox", "Yao", "QXTools", "QXZoo", "QXGraphDecompositions", "ITensors", "ITensorMPS", "ITensorNetworks"],
    "julia_dynamics_attractors": ["Attractors", "DynamicalSystems", "Basins", "DifferentialEquations"],
    "julia_proof_symbolic": ["Z3", "CVC5", "Symbolics"],
    "julia_spinor_nonassoc_geometry": ["CliffordAlgebras", "Grassmann", "Octonions", "Quaternions", "StaticArrays", "Manifolds", "CombinatorialSpaces", "TensorOperations", "Graphs"],
    "julia_jax_interop_ad": ["PythonCall", "DLPack", "CUDA", "Reactant", "Enzyme"],
    "julia_nn_graph": ["Flux", "Lux", "GraphNeuralNetworks", "GraphNeuralNets"],
    "jax_qit": ["dynamiqs", "netket", "qutip", "quimb", "cotengra"],
    "jax_dynamics_attractors": ["diffrax", "dynamax", "blackjax"],
    "jax_solve_optimization": ["jaxopt", "lineax", "optax", "optimistix", "equinox", "flax"],
    "jax_graph_topology_geometry": ["jraph", "ott", "e3nn_jax", "toponetx", "gudhi", "rustworkx", "networkx", "xgi"],
    "jax_proof_symbolic": ["z3", "cvc5", "sympy"],
    "pytorch_support_geometry": ["torch", "torch_ga", "torch_geometric", "clifford", "geomstats", "e3nn", "functorch"],
}


def py_inventory() -> list[dict[str, Any]]:
    rows = []
    for mod_name in PYTHON_MODULES:
        try:
            mod = importlib.import_module(mod_name)
            rows.append({"module": mod_name, "ok": True, "version": getattr(mod, "__version__", None), "file": getattr(mod, "__file__", None)})
        except Exception as exc:
            rows.append({"module": mod_name, "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:180]}"})
    return rows


def julia_inventory(repo: Path) -> dict[str, Any]:
    julia = Path("/opt/homebrew/bin/julia")
    if not julia.exists():
        return {"ok": False, "error": "/opt/homebrew/bin/julia missing", "modules": []}
    script = repo / "system_v5/ops/old_sim_processing/tmp_julia_library_inventory.jl"
    out = repo / "system_v5/evidence/sim_tool_library_coverage_julia_tmp.json"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        """
using JSON
mods = %s
rows = Any[]
for m in mods
    ok = false; err = nothing
    try
        @eval using $(Symbol(m))
        ok = true
    catch e
        err = string(typeof(e), ": ", e)
    end
    push!(rows, Dict("module"=>m, "ok"=>ok, "error"=> ok ? nothing : first(err, min(lastindex(err), 220))))
end
open("%s", "w") do io
    JSON.print(io, Dict("julia"=>Sys.BINDIR*"/julia", "active_project"=>Base.active_project(), "modules"=>rows))
end
""" % (json.dumps(JULIA_MODULES), str(out)),
        encoding="utf-8",
    )
    proc = subprocess.run([str(julia), "--startup-file=no", "--project=@v1.12", str(script)], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    if proc.returncode != 0:
        return {"ok": False, "returncode": proc.returncode, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:], "modules": []}
    data = json.loads(out.read_text(encoding="utf-8"))
    data["ok"] = True
    return data


def current_usage(repo: Path) -> dict[str, Any]:
    p = repo / "system_v5/evidence/three_engine_source_claim_audit_20260608.json"
    if not p.exists():
        return {"ok": False, "error": "source claim audit missing"}
    d = json.loads(p.read_text(encoding="utf-8"))
    declared = Counter()
    backed = Counter()
    for env in d.get("envelopes", []):
        for engine, audit in env.get("engines", {}).items():
            for pkg in audit.get("declared_load_bearing", []):
                declared[f"{engine}:{pkg}"] += 1
            for pkg in audit.get("rich_backed_packages", []):
                backed[f"{engine}:{pkg}"] += 1
    return {"ok": True, "envelope_count": d["summary"]["envelope_count"], "declared_load_bearing_counts": dict(declared.most_common()), "source_backed_counts": dict(backed.most_common())}


def family_status(mod_rows: dict[str, bool]) -> dict[str, Any]:
    out = {}
    for fam, mods in FAMILY.items():
        out[fam] = {"available": [m for m in mods if mod_rows.get(m) is True], "missing_or_unchecked": [m for m in mods if mod_rows.get(m) is not True]}
    return out


def render_md(report: dict[str, Any], json_rel: str) -> str:
    py_rows = report["python_inventory"]["modules"]
    jul_rows = report["julia_inventory"]["modules"]
    lines = [
        "# Sim Tool Library Coverage — 2026-06-08",
        "",
        "Status: environment/tool inventory plus current-envelope coverage. Not an install plan by itself.",
        "",
        "## Bottom line",
        "",
        "The machine has many useful libraries already. The current three-engine envelope estate uses only a narrow slice of them: Julia mostly `QuantumOptics`/`CliffordAlgebras`/`Z3`; JAX almost always `z3`/`cvc5` plus baseline `jax.numpy`; PyTorch almost always `torch.func`. That supports bounded scratch/proof pressure, but it is not the full sim-library stack the model wants.",
        "",
        f"Full JSON: `{json_rel}`",
        "",
        "## Current envelope usage",
        "",
    ]
    usage = report["current_envelope_usage"]
    lines.append(f"- envelopes in source-claim audit: `{usage.get('envelope_count')}`")
    lines.append("")
    lines.append("### Source-backed package counts")
    for key, val in usage.get("source_backed_counts", {}).items():
        lines.append(f"- `{key}`: `{val}`")
    lines.append("")
    lines.append("## Julia default-project inventory (not strict-carrier truth)")
    lines.append("")
    lines.append(
        "> **Strict-carrier caveat:** this section inventories the global/default Julia project. "
        "It is useful future fuel, but it is not evidence that a package is available under "
        "the strict carrier command `JULIA_LOAD_PATH=@:@stdlib --project=system_v5/julia_carrier`. "
        "`ITensorNetworks` and `TensorOperations` require install intent, isolated-project evidence, "
        "or deliberate admission before a carrier claim may cite them."
    )
    lines.append("")
    lines.append(f"- active project: `{report['julia_inventory'].get('active_project')}`")
    for row in jul_rows:
        mark = "✅" if row.get("ok") else "—"
        lines.append(f"- {mark} `{row['module']}`")
    lines.append("")
    lines.append("## Python/JAX/PyTorch inventory")
    lines.append("")
    lines.append(f"- Python: `{report['python_executable']}`")
    for row in py_rows:
        mark = "✅" if row.get("ok") else "—"
        version = f" `{row.get('version')}`" if row.get("version") else ""
        lines.append(f"- {mark} `{row['module']}`{version}")
    lines.append("")
    lines.append("## Use as future sim fuel")
    lines.append("")
    lines.append("- QIT/open-systems: Julia `QuantumOptics`, `ITensors`; JAX `dynamiqs`, `qutip`, `quimb`, `netket`.")
    lines.append("- Attractors/dynamics: Julia `Attractors`, `DynamicalSystems`, `DifferentialEquations`; JAX `diffrax` with `vmap`/`jit` for basin maps.")
    lines.append("- Proof pressure: Julia `Z3`; Python `z3`, `cvc5`, `sympy`; keep solver variables bound to computed finite objects.")
    lines.append("- Spinor/noncomm/nonassoc: use Julia `CliffordAlgebras`, `Grassmann`, `Octonions`, `Quaternions`, and `Manifolds` when present; `StaticArrays` and `CombinatorialSpaces` are useful candidates but must be import-verified before use.")
    lines.append("- Cross-engine bridge: PythonCall/DLPack/CUDA/Reactant/Enzyme are not in the default Julia project right now; treat interop as future setup, not current evidence.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path, default=Path("system_v5/evidence/sim_tool_library_coverage_20260608.json"))
    parser.add_argument("--md-out", type=Path, default=Path("system_v5/docs/maintenance/sim_tool_library_coverage_20260608.md"))
    args = parser.parse_args()
    repo = args.repo.resolve()
    py_rows = py_inventory()
    julia = julia_inventory(repo)
    module_status = {row["module"]: row.get("ok") is True for row in py_rows}
    module_status.update({row["module"]: row.get("ok") is True for row in julia.get("modules", [])})
    report = {
        "schema": "sim_tool_library_coverage.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": str(repo),
        "claim_ceiling": "Import inventory + usage coverage only; not evidence of a sim claim.",
        "python_executable": sys.executable,
        "python_inventory": {"modules": py_rows},
        "julia_inventory": julia,
        "family_status": family_status(module_status),
        "current_envelope_usage": current_usage(repo),
    }
    json_out = args.json_out if args.json_out.is_absolute() else repo / args.json_out
    md_out = args.md_out if args.md_out.is_absolute() else repo / args.md_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_out.write_text(render_md(report, json_out.relative_to(repo).as_posix()), encoding="utf-8")
    print(json.dumps({"status": "ok", "json_out": json_out.relative_to(repo).as_posix(), "md_out": md_out.relative_to(repo).as_posix(), "julia_ok": julia.get("ok"), "python_module_count": len(py_rows)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
