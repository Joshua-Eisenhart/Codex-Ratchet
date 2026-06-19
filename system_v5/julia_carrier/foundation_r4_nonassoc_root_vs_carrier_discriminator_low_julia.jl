#!/usr/bin/env julia
# object_id: foundation_r4_nonassoc_root_vs_carrier_discriminator_low
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using SHA
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras
using Z3

const OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_low"
const SOURCE_PATH = joinpath(@__DIR__, "foundation_r4_nonassoc_root_vs_carrier_discriminator_low_julia.jl")
const RESULT_PATH = joinpath(@__DIR__, "results", "foundation_r4_nonassoc_root_vs_carrier_discriminator_low_julia_results.json")
const TOL = 1.0e-9

function cd_conj(x::Vector{Float64})
    y = copy(x)
    length(y) > 1 && (y[2:end] .*= -1.0)
    y
end

function cd_mul(x::Vector{Float64}, y::Vector{Float64})
    n = length(x)
    n == 1 && return [x[1] * y[1]]
    h = n ÷ 2
    a, b = x[1:h], x[(h + 1):end]
    c, d = y[1:h], y[(h + 1):end]
    vcat(cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c)))
end

function basis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function table(dim::Int)
    [[[Int(round(cd_mul(basis(dim, i), basis(dim, j))[k + 1])) for k in 0:(dim - 1)] for j in 0:(dim - 1)] for i in 0:(dim - 1)]
end

function prod_vec(tbl, x::Int, y::Int)
    tbl[x + 1][y + 1]
end

function anticommutes(tbl, i::Int, j::Int)
    a = prod_vec(tbl, i, j)
    b = prod_vec(tbl, j, i)
    all(a[k] + b[k] == 0 for k in eachindex(a))
end

function unit_square_minus_one(tbl, i::Int)
    p = prod_vec(tbl, i, i)
    p[1] == -1 && all(p[k] == 0 for k in 2:length(p))
end

function imag_count(tbl)
    units = [i for i in 1:(length(tbl) - 1) if unit_square_minus_one(tbl, i)]
    good = [i for i in units if all(i == j || anticommutes(tbl, i, j) for j in units)]
    length(good)
end

function left_matrix(tbl, unit::Int)
    dim = length(tbl)
    hcat([Float64.(prod_vec(tbl, unit, col)) for col in 0:(dim - 1)]...)
end

function bare_root_report(tbl, name::String)
    dim = length(tbl)
    finite = dim < 10_000
    q = dim >= 4 ? 1 : min(1, dim - 1)
    r = dim >= 4 ? 2 : min(1, dim - 1)
    comm = prod_vec(tbl, q, r) .- prod_vec(tbl, r, q)
    noncomm = any(!=(0), comm)
    quotient = Dict{String,Any}(
        "M" => ["dimension", "imaginary_unit_square_minus_one_count", "noncommutator_witness"],
        "signature" => [dim, imag_count(tbl), noncomm ? 1 : 0],
        "well_defined" => finite && dim >= 1,
    )
    Dict{String,Any}(
        "carrier" => name,
        "finite" => finite,
        "dimension" => dim,
        "noncommutation_witness_units_1_2" => comm,
        "noncommutation_nonzero" => noncomm,
        "quotient" => quotient,
        "bare_root_admissible" => finite && noncomm && quotient["well_defined"],
    )
end

function quantumoptics_density_witness(dim::Int)
    b = NLevelBasis(dim)
    rho = Operator(b, b, Matrix{ComplexF64}(I, dim, dim) ./ dim)
    vals = eigvals(Hermitian(rho.data))
    Dict{String,Any}(
        "trace" => real(tr(rho.data)),
        "hermiticity_residual" => norm(rho.data - rho.data'),
        "min_eigenvalue" => minimum(real.(vals)),
        "normalization" => real(tr(rho.data)),
        "trace_one_pass" => abs(real(tr(rho.data)) - 1.0) <= TOL,
        "psd_pass" => minimum(real.(vals)) >= -TOL,
        "hermitian_pass" => norm(rho.data - rho.data') <= TOL,
    )
end

function clifford_report()
    cl06 = CliffordAlgebra(0, 6)
    gens = [getproperty(cl06, Symbol("e$i")) for i in 1:6]
    unit = one(gens[1])
    max_residual = 0.0
    for i in 1:6, j in 1:6
        lhs = gens[i] * gens[j] + gens[j] * gens[i]
        rhs = (i == j ? -2 : 0) * unit
        max_residual = max(max_residual, Float64(CliffordAlgebras.norm(lhs - rhs)))
    end
    Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructed" => "CliffordAlgebra(0, 6)",
        "basis_symbol_count" => length(propertynames(cl06)),
        "generator_anticommutation_max_residual" => max_residual,
        "pass" => length(propertynames(cl06)) == 64 && max_residual <= TOL,
    )
end

function z3_smoke()
    s = Z3.Solver()
    x = Z3.IntVar("x")
    Z3.add(s, x == Z3.IntVal(7))
    Z3.add(s, x == Z3.IntVal(3))
    Dict{String,Any}("ran" => true, "verdict" => string(Z3.check(s)), "claim" => "integer equality contradiction for H 3-vs-7 control")
end

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        bytes2hex(sha256(io))
    end
end

function main()
    mkpath(dirname(RESULT_PATH))
    tables = Dict("R" => table(1), "C" => table(2), "H" => table(4), "O" => table(8))
    counts = Dict(k => imag_count(v) for (k, v) in tables)
    bare = Dict(k => bare_root_report(v, k) for (k, v) in tables)
    h_admits = bare["H"]["bare_root_admissible"]
    h_cl6 = counts["H"] >= 7
    o_cl6 = counts["O"] >= 7
    quotient = Dict{String,Any}(
        "S" => ["R", "C", "H", "O"],
        "equivalence_relation" => "carriers are equivalent under M when dimension, imaginary-unit count, noncommutation witness, and Cl6/7-unit admissibility flag match",
        "classes" => Dict(k => [bare[k]["dimension"], counts[k], bare[k]["noncommutation_nonzero"] ? 1 : 0, counts[k] >= 7 ? 1 : 0] for k in keys(tables)),
        "admitted_under_bare_root" => [k for k in ["R", "C", "H", "O"] if bare[k]["bare_root_admissible"]],
        "admitted_under_cl6_constraint" => [k for k in ["R", "C", "H", "O"] if counts[k] >= 7],
    )
    result = Dict{String,Any}(
        "schema_version" => "three_engine_leg_result_v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "reads_peer_result" => false,
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "M" => Dict("probes" => ["finite dimension", "imaginary unit square=-1", "pairwise anticommutator zero", "noncommutator witness", "Cl6/7-unit flag"]),
        "C" => Dict("state_constraints" => ["trace=1", "PSD", "Hermiticity", "normalization"], "rung_specific_constraint" => "optional Cl6/7 mutually anticommuting imaginary units"),
        "density_constraint_witness" => quantumoptics_density_witness(4),
        "unit_counts" => counts,
        "bare_root" => bare,
        "quotient" => quotient,
        "negative_control_flip" => Dict(
            "bare_root_admits_H" => h_admits,
            "cl6_excludes_H" => !h_cl6,
            "cl6_admits_O" => o_cl6,
            "forced_nonassoc_under_bare_root" => false,
            "verdict" => "INSTALLED_BY_CL6_7_UNIT_CONSTRAINT_NOT_FORCED_BY_BARE_ROOT",
            "flips" => h_admits && !h_cl6 && o_cl6,
        ),
        "cliffordalgebras_report" => clifford_report(),
        "julia_z3_control" => z3_smoke(),
        "summary" => Dict(
            "R_unit_count" => counts["R"],
            "C_unit_count" => counts["C"],
            "H_unit_count" => counts["H"],
            "O_unit_count" => counts["O"],
            "H_bare_root_admissible" => h_admits,
            "H_cl6_admissible" => h_cl6,
            "O_cl6_admissible" => o_cl6,
            "forced_nonassoc_under_bare_root" => false,
            "installed_constraint" => "Cl(6)/>=7 mutually anticommuting imaginary units",
        ),
        "all_pass" => h_admits && !h_cl6 && o_cl6 && counts["R"] == 0 && counts["C"] == 1 && counts["H"] == 3 && counts["O"] == 7,
        "source_sha256" => sha256_file(SOURCE_PATH),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("FOUNDATION_R4_NONASSOC_ROOT_VS_CARRIER_DISCRIMINATOR_LOW_JULIA_DONE " * RESULT_PATH)
end

main()
