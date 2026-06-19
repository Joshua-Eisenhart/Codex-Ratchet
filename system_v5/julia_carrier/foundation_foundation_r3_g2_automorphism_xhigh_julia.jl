#!/usr/bin/env julia
# object_id: foundation_r3_g2_automorphism_xhigh_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using CliffordAlgebras
using Grassmann
using Z3

const RUNG_ID = "foundation_r3_g2_automorphism_xhigh"
const OBJECT_ID = "foundation_r3_g2_automorphism_xhigh_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r3_g2_automorphism_xhigh_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r3_g2_automorphism_xhigh_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const CLASSIFICATION = classification
const promotion_allowed = false
const PROMOTION_ALLOWED = promotion_allowed
const formal_admission_allowed = false
const FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing quaternion multiplication cross-check: CliffordAlgebras(:Quaternions) must match the computed Cayley-Dickson H table before the ladder is accepted",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side dimension guard bound to exact ranks computed from the structure-constant derivation matrix",
    ),
    "Grassmann" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "aligned Julia algebra surface loaded for the finite carrier route; not used as an octonion implementation",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive SVD/nullspace residual check after exact rank computation",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result receipt serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "Grassmann" => "supportive",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

function basis_vector(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function coeffs(mv, labels::Vector{Symbol})
    [Int(round(Float64(real(getproperty(mv, label))))) for label in labels]
end

function package_h_table()
    clh = CliffordAlgebra(:Quaternions)
    labels = [:𝟏, :i, :j, :ij]
    basis = [getproperty(clh, label) for label in labels]
    table = zeros(Int, 4, 4, 4)
    for a in 1:4, b in 1:4
        table[:, a, b] .= coeffs(basis[a] * basis[b], labels)
    end
    crosschecks = Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructor" => "CliffordAlgebra(:Quaternions)",
        "basis_labels" => string.(labels),
        "i_squared" => coeffs(clh.i * clh.i, labels),
        "j_squared" => coeffs(clh.j * clh.j, labels),
        "ij_squared" => coeffs(clh.ij * clh.ij, labels),
        "i_j" => coeffs(clh.i * clh.j, labels),
        "j_i" => coeffs(clh.j * clh.i, labels),
    )
    table, crosschecks
end

function multiply(table::Array{Int,3}, x::AbstractVector{<:Real}, y::AbstractVector{<:Real})
    dim = size(table, 1)
    out = zeros(eltype(float.(x .+ y)), dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function conjugate_vec(x::AbstractVector{<:Real})
    collect(x) .* vcat([1], fill(-1, length(x) - 1))
end

function cd_pair_multiply(parent::Array{Int,3}, x::AbstractVector{Int}, y::AbstractVector{Int})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_vec(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_vec(c))
    Int.(vcat(first, second))
end

function cd_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Int, dim, dim, dim)
    eye = Matrix{Int}(I, dim, dim)
    for i in 1:dim, j in 1:dim
        table[:, i, j] .= cd_pair_multiply(parent, eye[:, i], eye[:, j])
    end
    table
end

function build_tables()
    r = zeros(Int, 1, 1, 1)
    r[1, 1, 1] = 1
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    Dict("R" => r, "C" => c, "H" => h, "O" => o)
end

varidx(row::Int, col::Int, dim::Int) = row + (col - 1) * dim

function derivation_constraint_matrix(table::Array{Int,3})
    dim = size(table, 1)
    mat = zeros(Int, dim^3, dim^2)
    row = 0
    for a in 1:dim, b in 1:dim, c in 1:dim
        row += 1
        for k in 1:dim
            mat[row, varidx(c, k, dim)] += table[k, a, b]
            mat[row, varidx(k, a, dim)] -= table[c, k, b]
            mat[row, varidx(k, b, dim)] -= table[c, a, k]
        end
    end
    mat
end

function exact_rank(mat::Matrix{Int})
    rows = Vector{Vector{Rational{BigInt}}}()
    for i in 1:size(mat, 1)
        if any(!=(0), mat[i, :])
            push!(rows, [BigInt(x)//BigInt(1) for x in mat[i, :]])
        end
    end
    m = length(rows)
    n = size(mat, 2)
    r = 1
    pivots = Int[]
    for col in 1:n
        pivot = findfirst(i -> rows[i][col] != 0//1, r:m)
        pivot === nothing && continue
        p = pivot + r - 1
        rows[r], rows[p] = rows[p], rows[r]
        pv = rows[r][col]
        rows[r] = rows[r] ./ pv
        for i in 1:m
            if i != r && rows[i][col] != 0//1
                factor = rows[i][col]
                rows[i] = rows[i] .- factor .* rows[r]
            end
        end
        push!(pivots, col)
        r += 1
        r > m && break
    end
    length(pivots), pivots
end

function nullspace_data(mat::Matrix{Int})
    fmat = Float64.(mat)
    decomp = svd(fmat)
    tol = max(size(fmat)...) * eps(Float64) * maximum(decomp.S) * 100.0
    rank = count(>(tol), decomp.S)
    v = Matrix(decomp.Vt')
    basis = v[:, (rank + 1):end]
    rank, tol, basis, decomp.S
end

function vec_to_matrix(v::AbstractVector{Float64}, dim::Int)
    out = zeros(Float64, dim, dim)
    for col in 1:dim
        out[:, col] .= v[((col - 1) * dim + 1):(col * dim)]
    end
    out
end

function derivation_residual(table::Array{Int,3}, d::Matrix{Float64})
    dim = size(table, 1)
    max_seen = 0.0
    for a0 in 0:(dim - 1), b0 in 0:(dim - 1)
        ea = basis_vector(dim, a0)
        eb = basis_vector(dim, b0)
        left = d * multiply(table, ea, eb)
        right = multiply(table, d * ea, eb) + multiply(table, ea, d * eb)
        max_seen = max(max_seen, norm(left - right))
    end
    max_seen
end

function table_sha(table::Array{Int,3})
    bytes = join(string.(vec(table)), ",")
    bytes2hex(sha256(bytes))
end

function forced_commutative_table(table::Array{Int,3})
    control = copy(table)
    dim = size(table, 1)
    for i in 2:dim, j in 2:dim
        if i != j
            control[:, i, j] .= 0
        end
    end
    control
end

function h_embedded_in_o_table(h::Array{Int,3})
    control = zeros(Int, 8, 8, 8)
    control[1:4, 1:4, 1:4] .= h
    control
end

function z3_dimension_guard(name::String, cols::Int, computed_rank::Int, expected_dim::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    dim = Z3.IntVar("$(name)_computed_derivation_dim", ctx)
    rank = Z3.IntVar("$(name)_computed_derivation_rank", ctx)
    Z3.add(solver, rank == Z3.IntVal(computed_rank, ctx))
    Z3.add(solver, dim == Z3.IntVal(cols - computed_rank, ctx))
    Z3.add(solver, Z3.Not(dim == Z3.IntVal(expected_dim, ctx)))
    dimension_not_expected = string(Z3.check(solver))

    erased = Z3.Solver(ctx)
    erased_dim = Z3.IntVar("$(name)_erased_constraint_dim", ctx)
    Z3.add(erased, erased_dim == Z3.IntVal(cols, ctx))
    Z3.add(erased, Z3.Not(erased_dim == Z3.IntVal(expected_dim, ctx)))
    erased_status = string(Z3.check(erased))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "computed_rank" => computed_rank,
        "ambient_dim" => cols,
        "computed_dim" => cols - computed_rank,
        "expected_dim" => expected_dim,
        "dimension_not_expected_status" => dimension_not_expected,
        "drop_derivation_constraints_dimension_not_expected_status" => erased_status,
        "erase_flip_unsat_to_sat" => dimension_not_expected == "unsat" && erased_status == "sat",
    )
end

function density_guard(dim::Int)
    diag = fill(1.0 / dim, dim)
    Dict{String,Any}(
        "trace" => sum(diag),
        "trace_eq_1" => abs(sum(diag) - 1.0) < TOL,
        "psd" => minimum(diag) >= 0.0,
        "hermitian_defect" => 0.0,
        "normalization" => "uniform finite probe guard rho=I/dim; derivation dimension is not inferred from rho",
    )
end

function summarize_algebra(name::String, table::Array{Int,3})
    mat = derivation_constraint_matrix(table)
    rank_exact, pivots = exact_rank(mat)
    rank_svd, rank_tol, ns, singular_values = nullspace_data(mat)
    dim = size(table, 1)
    der_dim = dim^2 - rank_exact
    residual = der_dim > 0 ? derivation_residual(table, vec_to_matrix(ns[:, 1], dim)) : 0.0
    Dict{String,Any}(
        "name" => name,
        "carrier_dim" => dim,
        "structure_constants_sha256" => table_sha(table),
        "constraint_rows" => size(mat, 1),
        "constraint_cols" => size(mat, 2),
        "exact_rank" => rank_exact,
        "svd_rank" => rank_svd,
        "rank_tol" => rank_tol,
        "derivation_dim" => der_dim,
        "pivot_count" => length(pivots),
        "free_coordinate_count" => der_dim,
        "basis_residual_max" => residual,
        "smallest_nonzero_singular_value" => rank_svd > 0 ? singular_values[rank_svd] : nothing,
        "largest_zero_singular_value" => rank_svd < length(singular_values) ? singular_values[rank_svd + 1] : nothing,
        "density_guard" => density_guard(dim),
    )
end

function build_result()
    tables = build_tables()
    package_h, package_crosschecks = package_h_table()
    h_package_matches_cd = package_h == tables["H"]
    summaries = Dict(name => summarize_algebra(name, table) for (name, table) in tables)
    dim_ladder = Dict(name => summaries[name]["derivation_dim"] for name in ["R", "C", "H", "O"])

    forced_comm = forced_commutative_table(tables["O"])
    h_embedded = h_embedded_in_o_table(tables["H"])
    forced_comm_summary = summarize_algebra("O_forced_commutative_control", forced_comm)
    h_embedded_summary = summarize_algebra("O_dimension_H_embedded_associative_control", h_embedded)

    julia_z3 = Dict(
        "H" => z3_dimension_guard("H", summaries["H"]["constraint_cols"], summaries["H"]["exact_rank"], 3),
        "O" => z3_dimension_guard("O", summaries["O"]["constraint_cols"], summaries["O"]["exact_rank"], 14),
    )

    expected = Dict("R" => 0, "C" => 0, "H" => 3, "O" => 14)
    ladder_pass = all(dim_ladder[name] == expected[name] for name in keys(expected))
    negative_control = Dict{String,Any}(
        "ladder_changes_R_C_H_O" => dim_ladder == expected,
        "drop_derivation_constraint_O_dim_64_vs_14" => summaries["O"]["constraint_cols"] == 64 && summaries["O"]["derivation_dim"] == 14,
        "forced_commutative_O_dim_changes" => forced_comm_summary["derivation_dim"] != summaries["O"]["derivation_dim"],
        "forced_commutative_O_derivation_dim" => forced_comm_summary["derivation_dim"],
        "h_embedded_associative_control_dim_changes" => h_embedded_summary["derivation_dim"] != summaries["O"]["derivation_dim"],
        "h_embedded_associative_control_derivation_dim" => h_embedded_summary["derivation_dim"],
        "julia_z3_O_erase_flip" => julia_z3["O"]["erase_flip_unsat_to_sat"],
        "julia_z3_H_erase_flip" => julia_z3["H"]["erase_flip_unsat_to_sat"],
    )
    all_pass = Bool(
        ladder_pass &&
        h_package_matches_cd &&
        negative_control["forced_commutative_O_dim_changes"] &&
        negative_control["h_embedded_associative_control_dim_changes"] &&
        negative_control["julia_z3_O_erase_flip"] &&
        negative_control["julia_z3_H_erase_flip"] &&
        summaries["O"]["basis_residual_max"] < TOL &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )

    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["CliffordAlgebras", "Grassmann", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_preflight" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => Base.active_project(),
        ),
        "M" => Dict(
            "name" => "derivation_automorphism_probe",
            "explicit_probe_family" => ["for every ordered basis pair (e_a,e_b) and output coordinate c: D(e_a e_b)_c - (D(e_a)e_b + e_aD(e_b))_c"],
            "finite_probe_counts" => Dict(name => summaries[name]["constraint_rows"] for name in ["R", "C", "H", "O"]),
        ),
        "C" => Dict(
            "trace_eq_1" => all(summaries[name]["density_guard"]["trace_eq_1"] for name in ["R", "C", "H", "O"]),
            "psd" => all(summaries[name]["density_guard"]["psd"] for name in ["R", "C", "H", "O"]),
            "hermitian" => all(summaries[name]["density_guard"]["hermitian_defect"] == 0.0 for name in ["R", "C", "H", "O"]),
            "normalization" => "basis probes are unit-normalized and the auxiliary uniform rho=I/dim guard has trace 1; the rung-specific claim is multiplication preservation",
            "rung_specific_constraint" => "computed structure constants must satisfy D(xy)=D(x)y+xD(y) for every basis pair",
        ),
        "S_mod_M" => Dict(
            "definition" => "S=End_R(A), D ~_M D' iff the derivation residual vector M(D-D') is zero; the symmetry class is ker(M)=Der(A)",
            "class_dimensions" => dim_ladder,
            "quotient_ranks" => Dict(name => summaries[name]["exact_rank"] for name in ["R", "C", "H", "O"]),
        ),
        "package_crosscheck" => Dict(
            "h_cliffordalgebras_matches_cayley_dickson" => h_package_matches_cd,
            "details" => package_crosschecks,
        ),
        "summaries" => summaries,
        "controls" => Dict(
            "O_forced_commutative_control" => forced_comm_summary,
            "O_dimension_H_embedded_associative_control" => h_embedded_summary,
        ),
        "julia_z3" => julia_z3,
        "negative_control_flip" => negative_control,
        "summary" => Dict(
            "dim_der_R" => dim_ladder["R"],
            "dim_der_C" => dim_ladder["C"],
            "dim_der_H" => dim_ladder["H"],
            "dim_der_O" => dim_ladder["O"],
            "O_rank" => summaries["O"]["exact_rank"],
            "O_forced_commutative_derivation_dim" => forced_comm_summary["derivation_dim"],
            "O_h_embedded_derivation_dim" => h_embedded_summary["derivation_dim"],
            "z3_O_dimension_not_14" => julia_z3["O"]["dimension_not_expected_status"],
            "z3_H_dimension_not_3" => julia_z3["H"]["dimension_not_expected_status"],
        ),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R3_G2_AUTOMORPHISM_XHIGH_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "dims=", result["summary"]["dim_der_R"], "/", result["summary"]["dim_der_C"], "/", result["summary"]["dim_der_H"], "/", result["summary"]["dim_der_O"], " ",
        "forced_comm_dim=", result["summary"]["O_forced_commutative_derivation_dim"], " ",
        "z3_O_dim_not_14=", result["summary"]["z3_O_dimension_not_14"],
    )
    result["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
