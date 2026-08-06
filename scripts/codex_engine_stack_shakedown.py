#!/usr/bin/env python3
"""Codex-owned runtime capability shakedown for the current sim stack.

This is a diagnostic only. It checks whether the installed Python/JAX,
PyTorch, Julia-carrier, SMT, graph/topology, and skill/agent wiring surfaces
are usable enough for bounded micro-probes. It is not a sim result, proof
promotion, formal scout, or manifold admission packet.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
RESULT_PATH = Path(
    os.environ.get(
        "CODEX_RUNTIME_CAPABILITY_RESULT_PATH",
        str(REPO / "system_v5/ops/tooling/codex_runtime_capability_shakedown_results.json"),
    )
)
CANONICAL_PYTHON = Path(
    os.environ.get(
        "CODEX_RATCHET_PYTHON",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )
)
JULIA = Path(os.environ.get("CODEX_RATCHET_JULIA", "/opt/homebrew/bin/julia"))
JULIA_PROJECT = Path(
    os.environ.get("CODEX_RATCHET_JULIA_PROJECT", str(REPO / "system_v5/julia_carrier"))
)
STRICT_JULIA_LOAD_PATH = "@:@stdlib"

GATE_SKILLS = [
    "lego-sim-classifier",
    "codex-ratchet-tool-status-auditor",
    "codex-ratchet-env-agent-coordination",
]
ENGINE_SKILLS = [
    "jax-sim",
    "julia-sim",
    "pytorch-sim",
    "three-engine-sim",
]
CODEX_EXPECTED_SKILLS = [
    *ENGINE_SKILLS,
    "sim-stack-maintenance",
    *GATE_SKILLS,
]
CLAUDE_EXPECTED_SKILLS = [
    *ENGINE_SKILLS,
    "sim-stack-maintenance",
    *GATE_SKILLS,
]
CODEX_SKILL_ROOTS = [
    REPO / "system_v5/codex_skills",
    Path("/Users/joshuaeisenhart/.codex/skills"),
    Path("/Users/joshuaeisenhart/.codex-second/skills"),
]
CLAUDE_SKILL_ROOT = REPO / ".claude/skills"
CLAUDE_EXPECTED_AGENTS = [
    "fabrication-auditor",
    "fresh-audit-runner",
    "jax-audit-lane-runner",
    "jax-sim-runner",
    "julia-carrier-builder",
    "julia-sim-runner",
    "process-stage-gate-steward",
    "pytorch-sim-runner",
    "repo-doc-archaeologist",
    "sim-contract-gatekeeper",
    "smt-proof-engineer",
]

SUPPORT_IMPORTS = [
    "dynamiqs",
    "netket",
    "ott",
    "blackjax",
    "optimistix",
    "jaxopt",
    "lineax",
    "torchode",
    "xitorch",
    "cvxpylayers",
    "torch_ga",
    "sympy",
]
BLOCKED_IMPORTS = [
    "bayeux",
    "dgl",
    "torch_scatter",
    "torch_sparse",
]

TOOL_MANIFEST = {
    "codex_runtime_env_doctor": {
        "tried": True,
        "used": True,
        "reason": "load-bearing environment authority check for the sim-stack alias, strict Julia carrier, and repo pollution.",
    },
    "runtime_mapping_reference_audit": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stale mapping scan across active docs, skills, agents, and scripts.",
    },
    "julia_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict carrier API probe for Quaternions, Octonions, Z3, and Graphs.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor execution and vmap smoke for the Python/JAX leg.",
    },
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing micro ODE smoke for the JAX dynamics lane.",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor execution, torch.func, and DLPack bridge smoke for the PyTorch lane.",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyG data object smoke for graph-message carrier availability.",
    },
    "torchdiffeq": {
        "tried": True,
        "used": True,
        "reason": "load-bearing micro ODE smoke for PyTorch dynamics support.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT contradiction microcheck in Python and Julia carrier.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT contradiction microcheck in Python.",
    },
    "graph_topology_helpers": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph/topology smoke for rustworkx, XGI, TopoNetX, and GUDHI.",
    },
    "support_imports": {
        "tried": True,
        "used": True,
        "reason": "supportive import reachability checks for optional packages without claiming API depth.",
    },
    "skill_agent_inventory": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Codex/Claude skill and agent wiring check for the sim-stack gate surfaces.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "codex_runtime_env_doctor": "load_bearing",
    "runtime_mapping_reference_audit": "load_bearing",
    "julia_carrier": "load_bearing",
    "jax": "load_bearing",
    "diffrax": "load_bearing",
    "torch": "load_bearing",
    "torch_geometric": "load_bearing",
    "torchdiffeq": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "graph_topology_helpers": "load_bearing",
    "support_imports": "supportive",
    "skill_agent_inventory": "load_bearing",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(
    cmd: list[str],
    *,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }


def compact_run(result: dict[str, Any], *, keep_stdout: int = 4000, keep_stderr: int = 4000) -> dict[str, Any]:
    return {
        "cmd": result.get("cmd"),
        "returncode": result.get("returncode"),
        "timed_out": result.get("timed_out", False),
        "stdout_tail": (result.get("stdout") or "")[-keep_stdout:],
        "stderr_tail": (result.get("stderr") or "")[-keep_stderr:],
    }


def check(
    checks: list[dict[str, Any]],
    name: str,
    status: str,
    detail: dict[str, Any] | None = None,
    *,
    category: str,
    severity: str = "fail",
    note: str | None = None,
) -> None:
    checks.append(
        {
            "name": name,
            "category": category,
            "status": status,
            "severity": severity,
            "note": note,
            "detail": detail or {},
        }
    )


def import_probe(name: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {
            "ok": True,
            "version": getattr(mod, "__version__", None),
            "file": getattr(mod, "__file__", None),
        }
    except Exception as exc:  # import errors are evidence here
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc).splitlines()[0][:300],
        }


def run_doctor(checks: list[dict[str, Any]]) -> dict[str, Any]:
    result = run_cmd([str(CANONICAL_PYTHON), "scripts/codex_runtime_env_doctor.py", "--json"], timeout=360)
    parsed: dict[str, Any] = {"raw": compact_run(result)}
    if result["returncode"] == 0:
        try:
            parsed = json.loads(result["stdout"])
        except json.JSONDecodeError as exc:
            parsed["parse_error"] = str(exc)
    ok = bool(parsed.get("summary", {}).get("ok")) and result["returncode"] == 0
    check(
        checks,
        "codex_runtime_env_doctor",
        "pass" if ok else "fail",
        {
            "summary": parsed.get("summary"),
            "expected": parsed.get("expected"),
            "raw": compact_run(result) if not ok else None,
        },
        category="environment",
    )
    return parsed


def run_mapping_audit(checks: list[dict[str, Any]]) -> dict[str, Any]:
    result = run_cmd(
        [str(CANONICAL_PYTHON), "scripts/audit_runtime_mapping_references.py", "--json"],
        timeout=120,
    )
    parsed: dict[str, Any] = {"raw": compact_run(result)}
    if result["returncode"] == 0:
        try:
            parsed = json.loads(result["stdout"])
        except json.JSONDecodeError as exc:
            parsed["parse_error"] = str(exc)
    summary = parsed.get("summary") or {}
    ok = bool(summary.get("ok")) and result["returncode"] == 0
    check(
        checks,
        "runtime_mapping_reference_audit",
        "pass" if ok else "fail",
        {
            "summary": summary,
            "failure_count": summary.get("failure_count"),
            "warning_count": summary.get("warning_count"),
            "failures": parsed.get("failures", [])[:20],
        },
        category="environment",
    )
    return parsed


def julia_probe(checks: list[dict[str, Any]]) -> dict[str, Any]:
    code = r'''
using JSON3, JSON, Quaternions, Octonions, Z3, Graphs

components(x, props::Vector{Symbol}) = [Int(getproperty(x, prop)) for prop in props]

function table_from_library(basis::Vector, props::Vector{Symbol})
    dim = length(basis)
    table = zeros(Int, dim, dim, dim)
    for i in 1:dim, j in 1:dim
        table[:, i, j] .= components(basis[i] * basis[j], props)
    end
    table
end

function nested_C(table::Array{Int,3})
    dim = size(table, 1)
    [[[table[k, i, j] for j in 1:dim] for i in 1:dim] for k in 1:dim]
end

function concrete_mul(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function basisv(dim::Int, idx::Int)
    v = zeros(Int, dim)
    v[idx] = 1
    v
end

function concrete_assoc(table::Array{Int,3}, a::Int, b::Int, c::Int)
    dim = size(table, 1)
    ea = basisv(dim, a)
    eb = basisv(dim, b)
    ec = basisv(dim, c)
    concrete_mul(table, concrete_mul(table, ea, eb), ec) -
        concrete_mul(table, ea, concrete_mul(table, eb, ec))
end

function first_nonzero_associator(table::Array{Int,3})
    for a in 1:size(table, 1), b in 1:size(table, 1), c in 1:size(table, 1)
        assoc = concrete_assoc(table, a, b, c)
        if any(!=(0), assoc)
            return Dict(
                "indices_one_based" => [a, b, c],
                "indices_zero_based" => [a - 1, b - 1, c - 1],
                "associator_components" => assoc,
            )
        end
    end
    nothing
end

function import_status(name::String)
    try
        @eval using $(Symbol(name))
        return Dict("ok" => true, "error" => "")
    catch e
        return Dict("ok" => false, "error" => first(split(string(e), "\n")))
    end
end

q_basis = [
    Quaternion(1, 0, 0, 0),
    Quaternion(0, 1, 0, 0),
    Quaternion(0, 0, 1, 0),
    Quaternion(0, 0, 0, 1),
]
o_basis = [
    Octonion(1, 0, 0, 0, 0, 0, 0, 0),
    Octonion(0, 1, 0, 0, 0, 0, 0, 0),
    Octonion(0, 0, 1, 0, 0, 0, 0, 0),
    Octonion(0, 0, 0, 1, 0, 0, 0, 0),
    Octonion(0, 0, 0, 0, 1, 0, 0, 0),
    Octonion(0, 0, 0, 0, 0, 1, 0, 0),
    Octonion(0, 0, 0, 0, 0, 0, 1, 0),
    Octonion(0, 0, 0, 0, 0, 0, 0, 1),
]
q_table = table_from_library(q_basis, [:s, :v1, :v2, :v3])
o_table = table_from_library(o_basis, [:s, :v1, :v2, :v3, :v4, :v5, :v6, :v7])

ctx = Context()
solver = Solver(ctx)
x = IntVar("x", ctx)
add(solver, x == IntVal(1, ctx))
add(solver, Not(x == IntVal(1, ctx)))

g = SimpleGraph(3)
add_edge!(g, 1, 2)

blocked = Dict(
    "PythonCall" => import_status("PythonCall"),
    "DLPack" => import_status("DLPack"),
    "CondaPkg" => import_status("CondaPkg"),
    "Zygote" => import_status("Zygote"),
)

payload = Dict(
    "active_project" => string(Base.active_project()),
    "load_path" => join(Base.LOAD_PATH, ":"),
    "quaternion_assoc_i_j_k" => concrete_assoc(q_table, 2, 3, 4),
    "octonion_first_nonzero_associator" => first_nonzero_associator(o_table),
    "octonion_structure_constants" => nested_C(o_table),
    "z3_unsat" => string(check(solver)),
    "graphs_edge_count" => ne(g),
    "strict_blocked_imports" => blocked,
)

println("JSON_BEGIN")
println(JSON3.write(payload))
println("JSON_END")
'''
    env = os.environ.copy()
    env["JULIA_LOAD_PATH"] = STRICT_JULIA_LOAD_PATH
    result = run_cmd(
        [
            str(JULIA),
            "--startup-file=no",
            f"--project={JULIA_PROJECT}",
            "-e",
            code,
        ],
        timeout=240,
        env=env,
    )
    parsed: dict[str, Any] = {"raw": compact_run(result)}
    if result["returncode"] == 0 and "JSON_BEGIN" in result["stdout"]:
        body = result["stdout"].split("JSON_BEGIN", 1)[1].split("JSON_END", 1)[0].strip()
        parsed = json.loads(body)
    expected_project = str(JULIA_PROJECT / "Project.toml")
    ok = (
        result["returncode"] == 0
        and parsed.get("active_project") == expected_project
        and parsed.get("load_path") == STRICT_JULIA_LOAD_PATH
        and parsed.get("quaternion_assoc_i_j_k") == [0, 0, 0, 0]
        and parsed.get("octonion_first_nonzero_associator", {}).get("associator_components")
        == [0, 0, 0, 0, 0, -2, 0, 0]
        and parsed.get("z3_unsat") == "unsat"
        and parsed.get("graphs_edge_count") == 1
    )
    check(
        checks,
        "strict_julia_carrier_api_probe",
        "pass" if ok else "fail",
        {
            "active_project": parsed.get("active_project"),
            "load_path": parsed.get("load_path"),
            "quaternion_assoc_i_j_k": parsed.get("quaternion_assoc_i_j_k"),
            "octonion_first_nonzero_associator": parsed.get("octonion_first_nonzero_associator"),
            "z3_unsat": parsed.get("z3_unsat"),
            "graphs_edge_count": parsed.get("graphs_edge_count"),
            "raw": compact_run(result) if not ok else None,
        },
        category="julia",
    )
    blocked = parsed.get("strict_blocked_imports", {})
    blocked_ok = all(not blocked.get(name, {}).get("ok") for name in ["PythonCall", "DLPack", "CondaPkg"])
    check(
        checks,
        "strict_julia_bridge_quarantine",
        "pass" if blocked_ok else "fail",
        blocked,
        category="julia",
        note="PythonCall/DLPack/CondaPkg should not be available in the strict carrier by default.",
    )
    return parsed


def jax_assoc_from_table(table: list[Any], indices: list[int]) -> list[float]:
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp

    C = jnp.asarray(table, dtype=jnp.float64)
    dim = C.shape[0]

    def basis(idx: int) -> Any:
        return jnp.eye(dim, dtype=jnp.float64)[idx]

    def mul(x: Any, y: Any) -> Any:
        return jnp.einsum("kij,i,j->k", C, x, y)

    a, b, c = [basis(i) for i in indices]
    return [float(x) for x in (mul(mul(a, b), c) - mul(a, mul(b, c))).tolist()]


def torch_assoc_from_table(table: list[Any], indices: list[int]) -> list[float]:
    import torch

    C = torch.tensor(table, dtype=torch.float64)
    dim = C.shape[0]

    def basis(idx: int) -> Any:
        return torch.eye(dim, dtype=torch.float64)[idx]

    def mul(x: Any, y: Any) -> Any:
        return torch.einsum("kij,i,j->k", C, x, y)

    a, b, c = [basis(i) for i in indices]
    return [float(x) for x in (mul(mul(a, b), c) - mul(a, mul(b, c))).tolist()]


def python_api_probes(checks: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

    try:
        import jax

        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp

        values = jax.vmap(lambda x: x * x)(jnp.arange(5.0, dtype=jnp.float64)).tolist()
        out["jax_vmap"] = values
        check(
            checks,
            "jax_vmap_x64",
            "pass" if values == [0.0, 1.0, 4.0, 9.0, 16.0] else "fail",
            {"values": values},
            category="jax",
        )
    except Exception as exc:
        check(checks, "jax_vmap_x64", "fail", {"error": repr(exc)}, category="jax")

    try:
        import diffrax
        import jax.numpy as jnp

        sol = diffrax.diffeqsolve(
            diffrax.ODETerm(lambda _t, y, _args: -y),
            diffrax.Tsit5(),
            t0=0,
            t1=1,
            dt0=0.1,
            y0=jnp.array(1.0),
            saveat=diffrax.SaveAt(t1=True),
        )
        value = float(sol.ys[0])
        out["diffrax_decay"] = value
        check(
            checks,
            "diffrax_decay_micro_ode",
            "pass" if abs(value - math.exp(-1.0)) < 1e-6 else "fail",
            {"value": value, "expected": math.exp(-1.0)},
            category="jax",
        )
    except Exception as exc:
        check(checks, "diffrax_decay_micro_ode", "fail", {"error": repr(exc)}, category="jax")

    try:
        import z3

        x = z3.Int("x")
        solver = z3.Solver()
        solver.add(x == 1, x != 1)
        status = str(solver.check())
        out["z3_unsat"] = status
        check(
            checks,
            "python_z3_unsat_microcheck",
            "pass" if status == "unsat" else "fail",
            {"status": status},
            category="smt",
        )
    except Exception as exc:
        check(checks, "python_z3_unsat_microcheck", "fail", {"error": repr(exc)}, category="smt")

    try:
        import cvc5

        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        x = solver.mkConst(int_sort, "x")
        one = solver.mkInteger(1)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, x, one))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.DISTINCT, x, one))
        status = str(solver.checkSat())
        out["cvc5_unsat"] = status
        check(
            checks,
            "python_cvc5_unsat_microcheck",
            "pass" if status == "unsat" else "fail",
            {"status": status},
            category="smt",
        )
    except Exception as exc:
        check(checks, "python_cvc5_unsat_microcheck", "fail", {"error": repr(exc)}, category="smt")

    try:
        import e3nn_jax as e3j

        dim = e3j.Irreps("1x0e + 1x1o").dim
        out["e3nn_jax_dim"] = dim
        check(
            checks,
            "e3nn_jax_irreps_dim",
            "pass" if dim == 4 else "fail",
            {"dim": dim},
            category="jax",
        )
    except Exception as exc:
        check(checks, "e3nn_jax_irreps_dim", "fail", {"error": repr(exc)}, category="jax")

    try:
        import torch
        from torch.func import jacrev

        jac = jacrev(lambda x: (x * x).sum())(torch.tensor([2.0])).tolist()
        out["torch_jacrev"] = jac
        check(
            checks,
            "torch_func_jacrev",
            "pass" if jac == [4.0] else "fail",
            {"jacobian": jac},
            category="pytorch",
        )
    except Exception as exc:
        check(checks, "torch_func_jacrev", "fail", {"error": repr(exc)}, category="pytorch")

    try:
        import torch
        from torch_geometric.data import Data

        data = Data(
            x=torch.ones((3, 2)),
            edge_index=torch.tensor([[0, 1], [1, 2]], dtype=torch.long),
        )
        edges = int(data.num_edges)
        out["pyg_edges"] = edges
        check(
            checks,
            "torch_geometric_data_edge_count",
            "pass" if edges == 2 else "fail",
            {"edges": edges},
            category="pytorch",
        )
    except Exception as exc:
        check(checks, "torch_geometric_data_edge_count", "fail", {"error": repr(exc)}, category="pytorch")

    try:
        import torch
        from torchdiffeq import odeint

        value = float(odeint(lambda _t, y: -y, torch.tensor([1.0]), torch.tensor([0.0, 1.0]))[-1].item())
        out["torchdiffeq_decay"] = value
        check(
            checks,
            "torchdiffeq_decay_micro_ode",
            "pass" if abs(value - math.exp(-1.0)) < 1e-5 else "fail",
            {"value": value, "expected": math.exp(-1.0)},
            category="pytorch",
        )
    except Exception as exc:
        check(checks, "torchdiffeq_decay_micro_ode", "fail", {"error": repr(exc)}, category="pytorch")

    simple_api = [
        (
            "e3nn_irreps_dim",
            "pytorch",
            lambda: __import__("e3nn.o3", fromlist=["Irreps"]).Irreps("1x0e + 1x1o").dim,
            lambda v: v == 4,
        ),
        (
            "geomstats_hypersphere_dim",
            "pytorch",
            lambda: __import__(
                "geomstats.geometry.hypersphere",
                fromlist=["Hypersphere"],
            ).Hypersphere(dim=2).dim,
            lambda v: v == 2,
        ),
        (
            "qutip_sigmax_shape",
            "quantum",
            lambda: list(__import__("qutip").sigmax().shape),
            lambda v: v == [2, 2],
        ),
        (
            "quimb_pauli_x_square_trace",
            "tensor",
            lambda: float((__import__("quimb").pauli("X") @ __import__("quimb").pauli("X")).trace().real),
            lambda v: abs(v - 2.0) < 1e-12,
        ),
        (
            "rustworkx_edge_count",
            "graph_topology",
            rustworkx_edge_count,
            lambda v: v == 1,
        ),
        (
            "xgi_hyperedge_count",
            "graph_topology",
            xgi_edge_count,
            lambda v: v == 1,
        ),
        (
            "toponetx_simplicial_dim",
            "graph_topology",
            toponetx_dim,
            lambda v: v == 2,
        ),
        (
            "gudhi_simplex_count",
            "graph_topology",
            gudhi_simplex_count,
            lambda v: v == 3,
        ),
        (
            "clifford_e1_square",
            "geometric_algebra",
            clifford_e1_square,
            lambda v: abs(v - 1.0) < 1e-12,
        ),
    ]
    for name, category, fn, predicate in simple_api:
        try:
            value = fn()
            out[name] = value
            check(
                checks,
                name,
                "pass" if predicate(value) else "fail",
                {"value": value},
                category=category,
            )
        except Exception as exc:
            check(checks, name, "fail", {"error": repr(exc)}, category=category)

    support = {name: import_probe(name) for name in SUPPORT_IMPORTS}
    failed_support = [name for name, payload in support.items() if not payload["ok"]]
    check(
        checks,
        "support_package_imports",
        "pass" if not failed_support else "fail",
        {"failed": failed_support, "modules": support},
        category="support_imports",
    )

    blocked = {name: import_probe(name) for name in BLOCKED_IMPORTS}
    unexpectedly_imported = [name for name, payload in blocked.items() if payload["ok"]]
    check(
        checks,
        "known_bad_or_quarantined_imports_do_not_load",
        "pass" if not unexpectedly_imported else "warn",
        {"unexpectedly_imported": unexpectedly_imported, "modules": blocked},
        category="support_imports",
        severity="warn",
        note="These packages are expected absent or import-broken in the current stack.",
    )
    out["support_imports"] = support
    out["blocked_imports"] = blocked
    return out


def rustworkx_edge_count() -> int:
    import rustworkx as rx

    g = rx.PyGraph()
    g.add_nodes_from(range(3))
    g.add_edge(0, 1, "edge")
    return len(g.edge_list())


def xgi_edge_count() -> int:
    import xgi

    graph = xgi.Hypergraph()
    graph.add_edge([1, 2, 3])
    return int(graph.num_edges)


def toponetx_dim() -> int:
    import toponetx as tnx

    complex_ = tnx.SimplicialComplex([[1, 2, 3]])
    return int(complex_.dim)


def gudhi_simplex_count() -> int:
    import gudhi

    tree = gudhi.SimplexTree()
    tree.insert([0, 1])
    return int(tree.num_simplices())


def clifford_e1_square() -> float:
    from clifford import Cl

    _layout, blades = Cl(2)
    e1 = blades["e1"]
    return float((e1 * e1)[()])


def dlpack_probe(checks: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        import jax
        import jax.numpy as jnp
        import torch

        jax_array = jnp.arange(4, dtype=jnp.float32)
        try:
            capsule = jax.dlpack.to_dlpack(jax_array)
            torch_tensor = torch.utils.dlpack.from_dlpack(capsule)
        except AttributeError:
            torch_tensor = torch.utils.dlpack.from_dlpack(jax_array)

        source_torch = torch.arange(4, dtype=torch.float32)
        try:
            capsule = torch.utils.dlpack.to_dlpack(source_torch)
            roundtrip_jax = jax.dlpack.from_dlpack(capsule)
        except Exception:
            roundtrip_jax = jax.dlpack.from_dlpack(source_torch)

        payload = {
            "jax_to_torch": {
                "values": [float(x) for x in torch_tensor.tolist()],
                "dtype": str(torch_tensor.dtype),
                "shape": list(torch_tensor.shape),
            },
            "torch_to_jax": {
                "values": [float(x) for x in list(roundtrip_jax)],
                "dtype": str(roundtrip_jax.dtype),
                "shape": list(roundtrip_jax.shape),
            },
            "claim_ceiling": "DLPack value bridge without numpy conversion; not a Julia bridge claim.",
        }
        ok = (
            payload["jax_to_torch"]["values"] == [0.0, 1.0, 2.0, 3.0]
            and payload["torch_to_jax"]["values"] == [0.0, 1.0, 2.0, 3.0]
        )
        check(
            checks,
            "jax_torch_dlpack_value_bridge",
            "pass" if ok else "fail",
            payload,
            category="cross_runtime",
        )
        check(
            checks,
            "julia_python_dlpack_bridge",
            "skip",
            {
                "reason": "Strict Julia carrier intentionally excludes PythonCall/DLPack/CondaPkg.",
                "claim_ceiling": "No Julia-Python bridge claim.",
            },
            category="cross_runtime",
            severity="skip",
        )
        return payload
    except Exception as exc:
        check(checks, "jax_torch_dlpack_value_bridge", "fail", {"error": repr(exc)}, category="cross_runtime")
        return {"error": repr(exc)}


def tri_engine_table_probe(checks: list[dict[str, Any]], julia_payload: dict[str, Any]) -> dict[str, Any]:
    witness = julia_payload.get("octonion_first_nonzero_associator") or {}
    table = julia_payload.get("octonion_structure_constants")
    expected = witness.get("associator_components")
    indices = witness.get("indices_zero_based")
    payload: dict[str, Any] = {
        "julia_witness": witness,
        "claim_ceiling": "Julia package produced table; JAX and PyTorch execute the finite tensor kernel.",
    }
    if not table or not expected or indices is None:
        check(
            checks,
            "julia_jax_torch_octonion_associator_agreement",
            "fail",
            payload,
            category="cross_runtime",
        )
        return payload
    try:
        jax_assoc = jax_assoc_from_table(table, indices)
        torch_assoc = torch_assoc_from_table(table, indices)
        payload.update(
            {
                "julia_associator": expected,
                "jax_associator": jax_assoc,
                "torch_associator": torch_assoc,
                "max_abs_diff_julia_jax": max(abs(float(a) - float(b)) for a, b in zip(expected, jax_assoc)),
                "max_abs_diff_julia_torch": max(abs(float(a) - float(b)) for a, b in zip(expected, torch_assoc)),
            }
        )
        ok = payload["max_abs_diff_julia_jax"] == 0.0 and payload["max_abs_diff_julia_torch"] == 0.0
        check(
            checks,
            "julia_jax_torch_octonion_associator_agreement",
            "pass" if ok else "fail",
            payload,
            category="cross_runtime",
        )
        return payload
    except Exception as exc:
        payload["error"] = repr(exc)
        check(
            checks,
            "julia_jax_torch_octonion_associator_agreement",
            "fail",
            payload,
            category="cross_runtime",
        )
        return payload


def skill_agent_probe(checks: list[dict[str, Any]]) -> dict[str, Any]:
    codex_roots: dict[str, Any] = {}
    for root in CODEX_SKILL_ROOTS:
        codex_roots[str(root)] = {
            name: (root / name / "SKILL.md").exists() for name in CODEX_EXPECTED_SKILLS
        }
    repo_openai_yaml = {
        name: (REPO / "system_v5/codex_skills" / name / "agents/openai.yaml").exists()
        for name in CODEX_EXPECTED_SKILLS
    }

    claude_skills = {
        name: (CLAUDE_SKILL_ROOT / name / "SKILL.md").exists() for name in CLAUDE_EXPECTED_SKILLS
    }
    claude_agents = {
        name: (REPO / ".claude/agents" / f"{name}.md").exists() for name in CLAUDE_EXPECTED_AGENTS
    }
    payload = {
        "codex_skill_roots": codex_roots,
        "repo_codex_openai_yaml": repo_openai_yaml,
        "claude_skills": claude_skills,
        "claude_agents": claude_agents,
    }
    content_requirements = {
        str(CLAUDE_SKILL_ROOT / "codex-ratchet-env-agent-coordination" / "SKILL.md"): [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "JULIA_LOAD_PATH=@:@stdlib",
            "PythonCall",
            "DLPack",
            "CondaPkg",
            "bayeux",
            "dgl",
            "Import success is not claim integration",
        ],
        str(CLAUDE_SKILL_ROOT / "lego-sim-classifier" / "SKILL.md"): [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "JULIA_LOAD_PATH=@:@stdlib",
            "TOOL_MANIFEST",
            "TOOL_INTEGRATION_DEPTH",
            "No installs are allowed without install-intent",
            "do not modify",
        ],
        str(CLAUDE_SKILL_ROOT / "codex-ratchet-tool-status-auditor" / "SKILL.md"): [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "JULIA_LOAD_PATH=@:@stdlib",
            "TOOL_MANIFEST",
            "TOOL_INTEGRATION_DEPTH",
            "Import success",
            "No installs are allowed without install-intent",
        ],
        str(REPO / "system_v5/codex_skills" / "sim-stack-maintenance" / "SKILL.md"): [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "JULIA_LOAD_PATH=@:@stdlib",
            "dgl",
            "bayeux",
            "promotion_allowed=false",
            "No promotion claim",
        ],
    }
    content_guard: dict[str, Any] = {}
    for path_text, needles in content_requirements.items():
        path = Path(path_text)
        if not path.exists():
            content_guard[path_text] = {"exists": False, "missing": needles}
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        content_guard[path_text] = {
            "exists": True,
            "missing": [needle for needle in needles if needle.lower() not in text.lower()],
        }
    payload["skill_content_guard"] = content_guard
    missing_codex = [
        f"{root}:{name}"
        for root, table in codex_roots.items()
        for name, present in table.items()
        if not present
    ]
    missing_claude_skills = [name for name, present in claude_skills.items() if not present]
    missing_claude_agents = [name for name, present in claude_agents.items() if not present]
    missing_repo_openai_yaml = [name for name, present in repo_openai_yaml.items() if not present]
    content_guard_failures = {
        path: guard
        for path, guard in content_guard.items()
        if (not guard.get("exists")) or guard.get("missing")
    }
    check(
        checks,
        "codex_skill_root_gate_engine_and_maintenance_skills",
        "pass" if not missing_codex else "fail",
        {"missing": missing_codex, "roots": codex_roots},
        category="skill_agent_wiring",
    )
    check(
        checks,
        "repo_codex_skill_openai_agent_adapters",
        "pass" if not missing_repo_openai_yaml else "fail",
        {"missing": missing_repo_openai_yaml, "adapters": repo_openai_yaml},
        category="skill_agent_wiring",
    )
    check(
        checks,
        "claude_skill_gate_and_engine_skills",
        "pass" if not missing_claude_skills else "fail",
        {"missing": missing_claude_skills, "skills": claude_skills},
        category="skill_agent_wiring",
    )
    check(
        checks,
        "claude_sim_agent_role_cards",
        "pass" if not missing_claude_agents else "fail",
        {"missing": missing_claude_agents, "agents": claude_agents},
        category="skill_agent_wiring",
    )
    check(
        checks,
        "skill_runtime_guard_content",
        "pass" if not content_guard_failures else "fail",
        {"failures": content_guard_failures, "guards": content_guard},
        category="skill_agent_wiring",
    )
    return payload


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "pass": 0,
        "fail": 0,
        "warn": 0,
        "skip": 0,
    }
    for item in checks:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "ok": counts.get("fail", 0) == 0,
        "counts": counts,
        "failed_checks": [item["name"] for item in checks if item["status"] == "fail"],
        "warn_checks": [item["name"] for item in checks if item["status"] == "warn"],
        "skip_checks": [item["name"] for item in checks if item["status"] == "skip"],
    }


def main() -> int:
    checks: list[dict[str, Any]] = []
    current_python_ok = Path(sys.executable).resolve() == CANONICAL_PYTHON.resolve()
    check(
        checks,
        "current_python_is_sim_stack_alias",
        "pass" if current_python_ok else "fail",
        {
            "sys_executable": sys.executable,
            "sys_executable_resolved": str(Path(sys.executable).resolve()),
            "canonical_python": str(CANONICAL_PYTHON),
            "canonical_python_resolved": str(CANONICAL_PYTHON.resolve()),
        },
        category="environment",
    )

    doctor = run_doctor(checks)
    mapping = run_mapping_audit(checks)
    julia = julia_probe(checks)
    python_api = python_api_probes(checks)
    dlpack = dlpack_probe(checks)
    tri_engine = tri_engine_table_probe(checks, julia)
    skill_agents = skill_agent_probe(checks)

    summary = summarize(checks)
    result = {
        "schema": "codex_runtime_capability_shakedown.v1",
        "name": "codex_runtime_capability_shakedown",
        "generated_at": utc_now(),
        "repo": str(REPO),
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_file(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "classification": "audit",
        "diagnostic_only": True,
        "ok": summary["ok"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": summary["ok"],
        "claim_ceiling": (
            "Environment/tool/skill capability diagnostic only; no scientific lego, "
            "formal scout, manifold, Axis0, bridge, or physics admission."
        ),
        "demotion_condition": (
            "Always demote to tooling/runtime evidence only. Any lego, formal scout, "
            "bridge, manifold, Axis0, or physics use must be rewritten as a scoped "
            "sim/proof receipt with claim-specific controls and load-bearing tools."
        ),
        "next_lego_target": "none; this audit only identifies runtime and skill wiring readiness",
        "promotion_condition": "none; no promotion path exists for this audit receipt",
        "blocked_until": "permanently blocked from scientific promotion by diagnostic scope",
        "out_of_scope": [
            "science admission",
            "canonical sim promotion",
            "formal scout admission",
            "package installation",
            "model quality evaluation",
            "Julia-Python bridge admission",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "expected_runtime": {
            "python": str(CANONICAL_PYTHON),
            "julia": str(JULIA),
            "julia_project": str(JULIA_PROJECT),
            "julia_load_path": STRICT_JULIA_LOAD_PATH,
        },
        "summary": summary,
        "blockers": [item for item in checks if item["status"] == "fail"],
        "checks": checks,
        "doctor_summary": doctor.get("summary"),
        "mapping_audit_summary": mapping.get("summary"),
        "julia_probe": julia,
        "python_api_probe": python_api,
        "dlpack_probe": dlpack,
        "tri_engine_table_probe": tri_engine,
        "skill_agent_probe": skill_agents,
        "limitations": [
            "Support imports are capability checks, not load-bearing scientific evidence.",
            "Tri-engine agreement uses a Julia-derived octonion table executed by JAX and PyTorch; it is a runtime integration diagnostic.",
            "Julia-Python DLPack is intentionally skipped because strict Julia carrier excludes PythonCall/DLPack/CondaPkg.",
            "This result cannot promote a lego, full layer, G-structure, manifold, Axis0, or physics claim.",
        ],
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": result["summary"]["ok"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if result["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
