#!/usr/bin/env python3
"""
sim_julia_carrier_algebra_capability -- strict Julia carrier algebra probe.

This is a bounded capability receipt for the Julia Canon carrier project.  It
subprocess-runs the strict carrier with JULIA_LOAD_PATH=@:@stdlib and checks
package-native quaternion, octonion, Clifford, and Julia Z3 algebra surfaces.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"

REPO = Path(__file__).resolve().parents[2]
PROBE_PATH = Path(__file__).resolve()
RESULT_PATH = (
    PROBE_PATH.parent
    / "a2_state"
    / "sim_results"
    / "julia_carrier_algebra_capability_results.json"
)
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = REPO / "system_v5" / "julia_carrier"
STRICT_LOAD_PATH = "@:@stdlib"

_NOT_USED_REASON = (
    "not used: this bounded Julia carrier algebra capability receipt isolates "
    "Quaternions.jl, Octonions.jl, CliffordAlgebras.jl, and Julia Z3.jl APIs; "
    "other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "julia_carrier_algebra": {
        "tried": False,
        "used": False,
        "reason": "tool under capability test -- overwritten after strict Julia subprocess run",
    },
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "julia_carrier_algebra": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

JULIA_SCRIPT = r'''
using Dates
using JSON
using Pkg
import CliffordAlgebras
import Octonions
import Quaternions
import Z3

const TOL = 1.0e-9

qcomp(q) = [Int(getfield(q, idx)) for idx in 1:4]
ocomp(o) = [Int(getfield(o, idx)) for idx in 1:8]
normsq(v::Vector{Int}) = sum(x -> x * x, v)

function qbasis(idx0::Int)
    Quaternions.Quaternion(ntuple(k -> k == idx0 + 1 ? 1 : 0, 4)...)
end

function obasis(idx0::Int)
    Octonions.Octonion(ntuple(k -> k == idx0 + 1 ? 1 : 0, 8)...)
end

function quaternion_table()
    table = zeros(Int, 4, 4, 4)
    for i in 0:3, j in 0:3
        vals = qcomp(qbasis(i) * qbasis(j))
        for k in 0:3
            table[k + 1, i + 1, j + 1] = vals[k + 1]
        end
    end
    table
end

function octonion_table()
    table = zeros(Int, 8, 8, 8)
    for i in 0:7, j in 0:7
        vals = ocomp(obasis(i) * obasis(j))
        for k in 0:7
            table[k + 1, i + 1, j + 1] = vals[k + 1]
        end
    end
    table
end

function nested_C(table::Array{Int,3})
    dim = size(table, 1)
    [[[table[k, i, j] for j in 1:dim] for i in 1:dim] for k in 1:dim]
end

function concrete_basis(dim::Int, idx::Int)
    v = zeros(Int, dim)
    v[idx] = 1
    v
end

function concrete_mul(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function concrete_assoc(table::Array{Int,3}, a::Int, b::Int, c::Int)
    dim = size(table, 1)
    ea = concrete_basis(dim, a)
    eb = concrete_basis(dim, b)
    ec = concrete_basis(dim, c)
    concrete_mul(table, concrete_mul(table, ea, eb), ec) -
        concrete_mul(table, ea, concrete_mul(table, eb, ec))
end

function zadd(args::Vector{Z3.Expr}, ctx::Z3.Context)
    isempty(args) && return Z3.IntVal(0, ctx)
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), Cuint(length(args)), map(Z3.as_ast, args)))
end

function zmul(args::Vector{Z3.Expr}, ctx::Z3.Context)
    isempty(args) && return Z3.IntVal(1, ctx)
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), Cuint(length(args)), map(Z3.as_ast, args)))
end

function zsub(a::Z3.Expr, b::Z3.Expr, ctx::Z3.Context)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_sub(Z3.ref(ctx), Cuint(2), map(Z3.as_ast, [a, b])))
end

function neq_zero(e::Z3.Expr, ctx::Z3.Context)
    Z3.Not(e == Z3.IntVal(0, ctx))
end

function nonzero_vector(v::Vector{Z3.Expr}, ctx::Z3.Context)
    Z3.Or([neq_zero(e, ctx) for e in v])
end

function solver_with_bound_C(table::Array{Int,3}, prefix::String)
    dim = size(table, 1)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    C = Array{Z3.Expr,3}(undef, dim, dim, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        C[k, i, j] = Z3.IntVar("$(prefix)_C_$(k - 1)_$(i - 1)_$(j - 1)", ctx)
        Z3.add(solver, C[k, i, j] == Z3.IntVal(table[k, i, j], ctx))
    end
    ctx, solver, C
end

function basis_product(C::Array{Z3.Expr,3}, i::Int, j::Int)
    [C[k, i, j] for k in 1:size(C, 1)]
end

function product_right_basis(C::Array{Z3.Expr,3}, x::Vector{Z3.Expr}, j::Int, ctx::Z3.Context)
    dim = size(C, 1)
    [zadd([zmul([C[k, i, j], x[i]], ctx) for i in 1:dim], ctx) for k in 1:dim]
end

function product_left_basis(C::Array{Z3.Expr,3}, i::Int, y::Vector{Z3.Expr}, ctx::Z3.Context)
    dim = size(C, 1)
    [zadd([zmul([C[k, i, j], y[j]], ctx) for j in 1:dim], ctx) for k in 1:dim]
end

function associator_basis(C::Array{Z3.Expr,3}, a::Int, b::Int, c::Int, ctx::Z3.Context)
    ab = basis_product(C, a, b)
    bc = basis_product(C, b, c)
    left = product_right_basis(C, ab, c, ctx)
    right = product_left_basis(C, a, bc, ctx)
    [zsub(left[k], right[k], ctx) for k in 1:size(C, 1)]
end

function z3_nonzero_associator_status(table::Array{Int,3}, prefix::String, a::Int, b::Int, c::Int)
    ctx, solver, C = solver_with_bound_C(table, prefix)
    Z3.add(solver, nonzero_vector(associator_basis(C, a, b, c, ctx), ctx))
    string(Z3.check(solver))
end

function z3_forced_zero_status(table::Array{Int,3}, prefix::String, a::Int, b::Int, c::Int)
    ctx, solver, C = solver_with_bound_C(table, prefix)
    for expr in associator_basis(C, a, b, c, ctx)
        Z3.add(solver, expr == Z3.IntVal(0, ctx))
    end
    string(Z3.check(solver))
end

function direct_dep_versions()
    deps = Pkg.dependencies()
    by_name = Dict{String,Any}()
    for (_uuid, info) in deps
        if getproperty(info, :is_direct_dep)
            version = getproperty(info, :version)
            by_name[getproperty(info, :name)] = isnothing(version) ? "stdlib" : string(version)
        end
    end
    by_name
end

function main()
    q_table = quaternion_table()
    o_table = octonion_table()

    one_q = qbasis(0)
    qi = qbasis(1)
    qj = qbasis(2)
    qk = qbasis(3)
    qij = qi * qj
    qji = qj * qi
    q_gap = qcomp(qij - qji)
    q_assoc = qcomp((qi * qj) * qk - qi * (qj * qk))
    q_commuting_gap = qcomp(qi * qi - qi * qi)
    q_norm_lhs = normsq(qcomp(qi * qj))
    q_norm_rhs = normsq(qcomp(qi)) * normsq(qcomp(qj))

    one_o = obasis(0)
    oe1 = obasis(1)
    oe2 = obasis(2)
    oe4 = obasis(4)
    o_pair_e1e2 = ocomp(oe1 * oe2)
    o_pair_e2e4 = ocomp(oe2 * oe4)
    o_assoc = ocomp((oe1 * oe2) * oe4 - oe1 * (oe2 * oe4))
    o_norm_lhs = normsq(ocomp((one_o + oe1) * (one_o - oe2)))
    o_norm_rhs = normsq(ocomp(one_o + oe1)) * normsq(ocomp(one_o - oe2))

    cl3 = CliffordAlgebras.CliffordAlgebra(3, 0)
    ce1 = getproperty(cl3, :e1)
    ce2 = getproperty(cl3, :e2)
    cl_zero = CliffordAlgebras.MultiVector(cl3, 0)
    cl_unit = one(ce1)
    cl_product = ce1 * ce2
    cl_anticommutator = ce1 * ce2 + ce2 * ce1
    cl_e1_square_residual = Float64(CliffordAlgebras.norm(ce1 * ce1 - cl_unit))
    cl_anticommutator_residual = Float64(CliffordAlgebras.norm(cl_anticommutator - cl_zero))

    z3_quaternion_assoc_nonzero = z3_nonzero_associator_status(q_table, "q_assoc_ijk", 2, 3, 4)
    z3_octonion_assoc_nonzero = z3_nonzero_associator_status(o_table, "o_assoc_e1_e2_e4", 2, 3, 5)
    z3_octonion_forced_zero = z3_forced_zero_status(o_table, "o_assoc_e1_e2_e4_forced_zero", 2, 3, 5)

    positive = Dict{String,Any}(
        "quaternion_i_times_j_is_k" => Dict(
            "api_surface" => "Quaternions.Quaternion multiplication",
            "ij_components" => qcomp(qij),
            "expected_k_components" => qcomp(qk),
            "pass" => qij == qk,
        ),
        "quaternion_noncommutation_gap_nonzero" => Dict(
            "api_surface" => "Quaternions.Quaternion multiplication",
            "ij_minus_ji_components" => q_gap,
            "gap_normsq" => normsq(q_gap),
            "pass" => normsq(q_gap) > 0,
        ),
        "octonion_structure_constants_named_pairs" => Dict(
            "api_surface" => "Octonions.Octonion multiplication",
            "table_shape" => collect(size(o_table)),
            "basis_labels" => ["1", "e1", "e2", "e3", "e4", "e5", "e6", "e7"],
            "C_layout" => "C[k][i][j], one-based Julia table exported as nested JSON",
            "pairs" => Dict(
                "e1_times_e2" => o_pair_e1e2,
                "e2_times_e4" => o_pair_e2e4,
            ),
            "C" => nested_C(o_table),
            "pass" => normsq(o_pair_e1e2) == 1 && normsq(o_pair_e2e4) == 1,
        ),
        "octonion_e1_e2_e4_associator_nonzero" => Dict(
            "api_surface" => "Octonions.Octonion multiplication",
            "basis_triple" => ["e1", "e2", "e4"],
            "left_minus_right_components" => o_assoc,
            "associator_normsq" => normsq(o_assoc),
            "pass" => normsq(o_assoc) > 0,
        ),
        "clifford_cl3_blade_product_and_anticommutation" => Dict(
            "api_surface" => "CliffordAlgebras.CliffordAlgebra(3,0) generator product",
            "dimension" => CliffordAlgebras.dimension(cl3),
            "e1e2_product" => string(cl_product),
            "e1_square_residual" => cl_e1_square_residual,
            "anticommutator_residual" => cl_anticommutator_residual,
            "pass" => CliffordAlgebras.dimension(cl3) == 8 &&
                cl_e1_square_residual <= TOL &&
                cl_anticommutator_residual <= TOL,
        ),
        "julia_z3_bound_quaternion_associator_nonzero_unsat" => Dict(
            "api_surface" => "Z3.add/check over Quaternions-derived C[k,i,j]",
            "claim" => "with bound quaternion table entries, associator(i,j,k) has a nonzero component",
            "status" => z3_quaternion_assoc_nonzero,
            "expected_status" => "unsat",
            "pass" => z3_quaternion_assoc_nonzero == "unsat",
        ),
        "julia_z3_bound_octonion_associator_nonzero_sat" => Dict(
            "api_surface" => "Z3.add/check over Octonions-derived C[k,i,j]",
            "claim" => "with bound octonion table entries, associator(e1,e2,e4) has a nonzero component",
            "status" => z3_octonion_assoc_nonzero,
            "expected_status" => "sat",
            "pass" => z3_octonion_assoc_nonzero == "sat",
        ),
    )

    negative = Dict{String,Any}(
        "commuting_pair_zero_gap_control" => Dict(
            "api_surface" => "Quaternions.Quaternion multiplication",
            "ii_minus_ii_components" => q_commuting_gap,
            "gap_normsq" => normsq(q_commuting_gap),
            "must_fail_if_nonzero" => true,
            "pass" => normsq(q_commuting_gap) == 0,
        ),
        "quaternion_associative_zero_associator_control" => Dict(
            "api_surface" => "Quaternions.Quaternion multiplication",
            "basis_triple" => ["i", "j", "k"],
            "left_minus_right_components" => q_assoc,
            "associator_normsq" => normsq(q_assoc),
            "must_fail_if_nonzero" => true,
            "pass" => normsq(q_assoc) == 0,
        ),
        "julia_z3_forced_octonion_associator_zero_unsat_control" => Dict(
            "api_surface" => "Z3.add/check over Octonions-derived C[k,i,j]",
            "claim" => "force every component of associator(e1,e2,e4) to zero after binding package-derived C",
            "status" => z3_octonion_forced_zero,
            "expected_status" => "unsat",
            "must_fail_if_sat" => true,
            "pass" => z3_octonion_forced_zero == "unsat",
        ),
    )

    boundary = Dict{String,Any}(
        "quaternion_identity_elements" => Dict(
            "api_surface" => "Quaternions.Quaternion multiplication",
            "left_identity_components" => qcomp(one_q * qi),
            "right_identity_components" => qcomp(qi * one_q),
            "target_components" => qcomp(qi),
            "pass" => one_q * qi == qi && qi * one_q == qi,
        ),
        "octonion_identity_elements" => Dict(
            "api_surface" => "Octonions.Octonion multiplication",
            "left_identity_components" => ocomp(one_o * oe4),
            "right_identity_components" => ocomp(oe4 * one_o),
            "target_components" => ocomp(oe4),
            "pass" => one_o * oe4 == oe4 && oe4 * one_o == oe4,
        ),
        "quaternion_norm_preservation" => Dict(
            "api_surface" => "Quaternions.Quaternion multiplication",
            "normsq_i_times_j" => q_norm_lhs,
            "normsq_i_times_normsq_j" => q_norm_rhs,
            "pass" => q_norm_lhs == q_norm_rhs,
        ),
        "octonion_norm_preservation" => Dict(
            "api_surface" => "Octonions.Octonion multiplication",
            "left" => "normsq((1+e1)*(1-e2))",
            "right" => "normsq(1+e1)*normsq(1-e2)",
            "normsq_product" => o_norm_lhs,
            "normsq_factor_product" => o_norm_rhs,
            "pass" => o_norm_lhs == o_norm_rhs,
        ),
        "clifford_identity_element" => Dict(
            "api_surface" => "CliffordAlgebras one(generator) multiplication",
            "left_identity" => string(cl_unit * ce1),
            "right_identity" => string(ce1 * cl_unit),
            "target" => string(ce1),
            "pass" => cl_unit * ce1 == ce1 && ce1 * cl_unit == ce1,
        ),
    )

    all_flags = Bool[]
    for section in (positive, negative, boundary)
        for (_name, row) in section
            push!(all_flags, Bool(row["pass"]))
        end
    end

    result = Dict{String,Any}(
        "julia" => Dict(
            "ran" => true,
            "source_path" => abspath(PROGRAM_FILE),
            "packages_used" => ["Quaternions", "Octonions", "CliffordAlgebras", "Z3", "JSON", "Pkg", "Dates"],
            "aligned_packages_load_bearing" => ["Quaternions", "Octonions", "CliffordAlgebras", "Z3"],
            "reads_peer_result" => false,
        ),
        "active_project" => Base.active_project(),
        "load_path" => join(Base.LOAD_PATH, ":"),
        "julia_version" => string(VERSION),
        "generated_at" => Dates.format(now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "dep_versions" => direct_dep_versions(),
        "positive" => positive,
        "negative" => negative,
        "boundary" => boundary,
        "summary" => Dict(
            "all_pass" => !isempty(all_flags) && all(all_flags),
            "pass_count" => count(identity, all_flags),
            "total_count" => length(all_flags),
        ),
    )

    println("JSON_BEGIN")
    JSON.print(stdout, result, 2)
    println()
    println("JSON_END")
end

main()
'''


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_pass_flags(section: dict) -> list[bool]:
    flags: list[bool] = []
    for value in section.values():
        if isinstance(value, dict) and "pass" in value:
            flags.append(bool(value["pass"]))
    return flags


def _run_julia() -> tuple[dict, dict]:
    env = os.environ.copy()
    env["JULIA_LOAD_PATH"] = STRICT_LOAD_PATH
    with tempfile.TemporaryDirectory(prefix="julia_carrier_algebra_capability_") as tmp:
        script_path = Path(tmp) / "sim_julia_carrier_algebra_capability.jl"
        script_path.write_text(JULIA_SCRIPT, encoding="utf-8")
        cmd = [
            str(JULIA),
            "--startup-file=no",
            f"--project={JULIA_PROJECT}",
            str(script_path),
        ]
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=240,
            check=False,
        )

    run_meta = {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stderr": proc.stderr[-4000:],
        "stdout_tail": proc.stdout[-4000:],
        "julia_script_sha256": _sha256_text(JULIA_SCRIPT),
        "julia_script_mode": "embedded_tempfile",
    }
    if proc.returncode != 0:
        raise RuntimeError(f"julia subprocess failed: {run_meta}")
    if "JSON_BEGIN" not in proc.stdout or "JSON_END" not in proc.stdout:
        raise RuntimeError(f"julia subprocess did not emit JSON sentinels: {run_meta}")
    payload = proc.stdout.split("JSON_BEGIN", 1)[1].split("JSON_END", 1)[0].strip()
    return json.loads(payload), run_meta


def build_results() -> dict:
    julia_payload, run_meta = _run_julia()
    TOOL_MANIFEST["julia_carrier_algebra"]["tried"] = True
    TOOL_MANIFEST["julia_carrier_algebra"]["used"] = True
    TOOL_MANIFEST["julia_carrier_algebra"]["reason"] = (
        "load-bearing capability under test: strict Julia carrier subprocess "
        "uses Quaternions.jl, Octonions.jl, CliffordAlgebras.jl, and Julia Z3.jl "
        "to decide all positive, negative, and boundary verdicts."
    )

    pos = julia_payload["positive"]
    neg = julia_payload["negative"]
    bnd = julia_payload["boundary"]
    flags = _collect_pass_flags(pos) + _collect_pass_flags(neg) + _collect_pass_flags(bnd)
    all_pass = bool(flags) and all(flags) and julia_payload["summary"]["all_pass"]

    package_tool_manifest = {
        "Quaternions": {
            "tried": True,
            "used": True,
            "reason": "load-bearing quaternion product, noncommutation, associativity control, identity, and norm-preservation checks.",
        },
        "Octonions": {
            "tried": True,
            "used": True,
            "reason": "load-bearing octonion structure constants, named pair products, nonzero associator, identity, and norm-preservation checks.",
        },
        "CliffordAlgebras": {
            "tried": True,
            "used": True,
            "reason": "load-bearing Cl(3,0) basis blade product, identity, dimension, and anticommutation checks.",
        },
        "Z3": {
            "tried": True,
            "used": True,
            "reason": "load-bearing Julia Z3.jl checks over bound package-derived structure constants.",
        },
    }
    package_tool_depth = {
        "Quaternions": "load_bearing",
        "Octonions": "load_bearing",
        "CliffordAlgebras": "load_bearing",
        "Z3": "load_bearing",
    }
    tool_calls = [
        {
            "tool": "Quaternions",
            "qualified_api/function": "Quaternions.Quaternion multiplication",
            "input_object": "basis units i,j,k",
            "output_object": {
                "ij_components": pos["quaternion_i_times_j_is_k"]["ij_components"],
                "ij_minus_ji_components": pos["quaternion_noncommutation_gap_nonzero"]["ij_minus_ji_components"],
            },
            "positive_case": "i*j equals k and i*j-j*i is nonzero",
            "negative/erased_control": "i*i-i*i gap is zero; associator(i,j,k) is zero",
            "boundary_case": "identity and norm preservation",
            "demotion_condition": "demote if product, control, identity, or norm-preservation verdict fails",
            "gates": ["summary.all_pass", "positive", "negative", "boundary"],
        },
        {
            "tool": "Octonions",
            "qualified_api/function": "Octonions.Octonion multiplication",
            "input_object": "basis units e1,e2,e4",
            "output_object": {
                "e1e2": pos["octonion_structure_constants_named_pairs"]["pairs"]["e1_times_e2"],
                "e2e4": pos["octonion_structure_constants_named_pairs"]["pairs"]["e2_times_e4"],
                "associator": pos["octonion_e1_e2_e4_associator_nonzero"]["left_minus_right_components"],
            },
            "positive_case": "two named basis-pair products and a nonzero associator",
            "negative/erased_control": "Julia Z3 forced-zero associator is UNSAT",
            "boundary_case": "identity and norm preservation",
            "demotion_condition": "demote if structure constants, associator, Z3 control, identity, or norm verdict fails",
            "gates": ["summary.all_pass", "positive", "negative", "boundary"],
        },
        {
            "tool": "CliffordAlgebras",
            "qualified_api/function": "CliffordAlgebras.CliffordAlgebra(3,0) generator product",
            "input_object": "Cl(3,0) e1,e2",
            "output_object": pos["clifford_cl3_blade_product_and_anticommutation"],
            "positive_case": "Cl(3) dimension 8, e1*e2 blade product, and anticommutator residual zero",
            "negative/erased_control": "zero multivector anticommutator gates the residual check",
            "boundary_case": "Clifford identity element",
            "demotion_condition": "demote if Cl(3) product, dimension, anticommutation, or identity verdict fails",
            "gates": ["summary.all_pass", "positive", "boundary"],
        },
        {
            "tool": "Z3",
            "qualified_api/function": "Z3.add/check",
            "input_object": "bound Quaternions/Octonions C[k,i,j] structure constants",
            "output_object": {
                "quaternion_assoc_nonzero": pos["julia_z3_bound_quaternion_associator_nonzero_unsat"]["status"],
                "octonion_assoc_nonzero": pos["julia_z3_bound_octonion_associator_nonzero_sat"]["status"],
                "octonion_forced_zero": neg["julia_z3_forced_octonion_associator_zero_unsat_control"]["status"],
            },
            "positive_case": "quaternion nonzero-associator claim UNSAT; octonion nonzero-associator claim SAT",
            "negative/erased_control": "forcing the nonzero octonion associator to zero is UNSAT",
            "boundary_case": "all solver constants are bound from package-derived finite tables",
            "demotion_condition": "demote if any expected SAT/UNSAT polarity flips",
            "gates": ["summary.all_pass", "positive", "negative"],
        },
    ]

    results = {
        "name": "sim_julia_carrier_algebra_capability",
        "purpose": (
            "bounded isolation probe of strict Julia carrier algebra APIs: "
            "Quaternions.jl products/controls, Octonions.jl structure constants "
            "and associator, CliffordAlgebras.jl Cl(3) product/anticommutation, "
            "and Julia Z3.jl bound-table facts"
        ),
        "witness_loadbearing_use": "capability matrix v0: first Julia Canon strict-carrier ALGEBRA probe",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "package_tool_manifest": package_tool_manifest,
        "package_tool_integration_depth": package_tool_depth,
        "tool_calls": tool_calls,
        "julia": julia_payload["julia"],
        "strict_julia_command": {
            "executable": str(JULIA),
            "project": str(JULIA_PROJECT),
            "load_path": STRICT_LOAD_PATH,
            "startup_file": "no",
        },
        "julia_run": run_meta,
        "active_project": julia_payload["active_project"],
        "load_path": julia_payload["load_path"],
        "julia_version": julia_payload["julia_version"],
        "dep_versions": julia_payload["dep_versions"],
        "source_path": str(PROBE_PATH),
        "source_sha256": _source_sha256(PROBE_PATH),
        "julia_script_sha256": run_meta["julia_script_sha256"],
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": classification,
        "all_pass": all_pass,
        "pass_count": int(sum(flags)),
        "total_count": int(len(flags)),
        "summary": {"all_pass": all_pass},
        "surviving_alternatives": [
            "This receipt covers only bounded strict Julia carrier algebra capability; it does not promote a scientific lego, bridge, axis, GStack, or nonclassical admission."
        ],
        "demotion_condition": (
            "Demote this Julia carrier algebra capability receipt if any "
            "quaternion, octonion, CliffordAlgebras, Julia Z3, identity, norm, "
            "or negative-control verdict fails on rerun."
        ),
        "out_of_scope": [
            "no scientific lego promotion",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no nonclassical admission",
            "no JAX or PyTorch parity claim",
            "no foundation_nested_hopf_weyl_signed_cut_ratchet interaction",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_julia_carrier_algebra_capability",
        target=(
            "Use as bounded strict Julia carrier algebra capability evidence "
            "before exact tool-lego fit or coupling packets."
        ),
    )
    results["claim_ceiling"] = (
        "finite sim_julia_carrier_algebra_capability receipt only; "
        "no bridge, GStack, axis, or promoted admission"
    )
    return results


def main() -> int:
    try:
        results = build_results()
    except Exception as exc:
        results = {
            "name": "sim_julia_carrier_algebra_capability",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "classification": classification,
            "error": str(exc),
            "all_pass": False,
            "summary": {"all_pass": False},
            "out_of_scope": [
                "no scientific lego promotion",
                "no bridge claim",
                "no axis claim",
                "no GStack claim",
                "no nonclassical admission",
            ],
        }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Results written to {RESULT_PATH}")
    print(
        f"all_pass={results.get('all_pass')} "
        f"pass={results.get('pass_count')}/{results.get('total_count')}"
    )
    return 0 if results.get("summary", {}).get("all_pass") is True else 1


if __name__ == "__main__":
    sys.exit(main())
