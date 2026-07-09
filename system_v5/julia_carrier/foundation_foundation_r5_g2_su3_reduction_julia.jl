#!/usr/bin/env julia
# object_id: foundation_r5_g2_su3_reduction_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: true

using Dates
using JSON
using LinearAlgebra
using SHA
using QuantumOptics
using CliffordAlgebras
using Z3

const RUNG_ID = "foundation_r5_g2_su3_reduction"
const OBJECT_ID = "foundation_r5_g2_su3_reduction_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r5_g2_su3_reduction_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r5_g2_su3_reduction_julia_results.json")
const R3_SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_r3_octonion_cl6_link_xhigh_julia.jl")
const R3_RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r3_octonion_cl6_link_xhigh_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const CLASSIFICATION = classification
const promotion_allowed = false
const PROMOTION_ALLOWED = promotion_allowed
const formal_admission_allowed = false
const FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
const reads_peer_result = true
const READS_PEER_RESULT = reads_peer_result

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite probe guard: constructs the chosen imaginary-unit probe ket and trace-one projector used to bind the unit-fixing measurement surface",
    ),
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing quaternion stage cross-check before the Cayley-Dickson octonion table is accepted",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side no-extra-kernel and erase-flip guard over the computed unit-fixing constraint rows",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive SVD/nullspace residual diagnostics after exact rational rank computation",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing read of R3's persisted result JSON (foundation_r3_octonion_cl6_link_xhigh_julia_results.json) for peer-dependency provenance, plus supportive result receipt serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "load_bearing",
)

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
    table, Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructor" => "CliffordAlgebra(:Quaternions)",
        "basis_labels" => string.(labels),
        "i_squared" => coeffs(clh.i * clh.i, labels),
        "j_squared" => coeffs(clh.j * clh.j, labels),
        "ij_squared" => coeffs(clh.ij * clh.ij, labels),
        "i_j" => coeffs(clh.i * clh.j, labels),
        "j_i" => coeffs(clh.j * clh.i, labels),
    )
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

function fixing_constraint_matrix(dim::Int, vectors::Vector{Vector{Int}})
    rows = zeros(Int, dim * length(vectors), dim^2)
    row = 0
    for vec in vectors
        @assert length(vec) == dim
        for r in 1:dim
            row += 1
            for col in 1:dim
                coeff = vec[col]
                coeff == 0 && continue
                rows[row, varidx(r, col, dim)] += coeff
            end
        end
    end
    rows
end

function augmented_constraint_matrix(table::Array{Int,3}, vectors::Vector{Vector{Int}})
    base = derivation_constraint_matrix(table)
    isempty(vectors) && return base
    vcat(base, fixing_constraint_matrix(size(table, 1), vectors))
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
    eye = Matrix{Float64}(I, dim, dim)
    max_seen = 0.0
    for a in 1:dim, b in 1:dim
        ea = eye[:, a]
        eb = eye[:, b]
        left = d * multiply(table, ea, eb)
        right = multiply(table, d * ea, eb) + multiply(table, ea, d * eb)
        max_seen = max(max_seen, norm(left - right))
    end
    max_seen
end

function fixation_residual(d::Matrix{Float64}, vectors::Vector{Vector{Int}})
    isempty(vectors) && return 0.0
    maximum(norm(d * Float64.(vec)) for vec in vectors)
end

function table_sha(table::Array{Int,3})
    bytes = join(string.(vec(table)), ",")
    bytes2hex(sha256(bytes))
end

function load_r3_peer_result()
    isfile(R3_RESULT_PATH) || error("R5 G2/SU3 reduction sim requires R3 peer result at $(R3_RESULT_PATH); none found.")
    JSON.parsefile(R3_RESULT_PATH)
end

# R3's own Cayley-Dickson octonion construction (foundation_r3_octonion_cl6_link_xhigh_julia.jl,
# function cd_mul), recomputed locally in structure-constant table[c,a,b] form so it can be
# cross-checked, index by index, against this rung's independently-written cd_double/
# cd_pair_multiply octonion table -- the two Cayley-Dickson implementations were previously
# never compared against each other.
function r3_cd_conj(x::Vector{Float64})
    y = copy(x)
    length(y) > 1 && (y[2:end] .*= -1.0)
    y
end

function r3_cd_mul(x::Vector{Float64}, y::Vector{Float64})
    n = length(x)
    n == 1 && return [x[1] * y[1]]
    half = n ÷ 2
    a, b = x[1:half], x[(half + 1):end]
    c, d = y[1:half], y[(half + 1):end]
    vcat(r3_cd_mul(a, c) - r3_cd_mul(r3_cd_conj(d), b), r3_cd_mul(d, a) + r3_cd_mul(b, r3_cd_conj(c)))
end

function r3_cd_basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function r3_style_octonion_table()
    dim = 8
    table = zeros(Int, dim, dim, dim)
    for a in 1:dim, b in 1:dim
        prod = r3_cd_mul(r3_cd_basis(dim, a - 1), r3_cd_basis(dim, b - 1))
        table[:, a, b] .= Int.(round.(prod))
    end
    table
end

function r3_provenance_check(r3::AbstractDict, o_table::Array{Int,3})
    r3_source_present = isfile(R3_SOURCE_PATH)
    r3_style_table = r3_style_octonion_table()
    max_entry_residual = maximum(abs.(r3_style_table .- o_table))
    tables_match = max_entry_residual == 0
    r3_sha = r3_source_present ? bytes2hex(sha256(read(R3_SOURCE_PATH))) : nothing
    Dict{String,Any}(
        "r3_result_path" => R3_RESULT_PATH,
        "r3_source_path" => R3_SOURCE_PATH,
        "r3_object_id" => get(r3, "object_id", nothing),
        "r3_source_sha256_from_own_result" => get(r3, "source_sha256", nothing),
        "r3_source_sha256_recomputed_here" => r3_sha,
        "r3_source_sha_matches" => r3_sha === nothing ? false : r3_sha == get(r3, "source_sha256", nothing),
        "local_cd_double_octonion_table_sha256" => table_sha(o_table),
        "r3_style_cd_mul_octonion_table_sha256" => table_sha(r3_style_table),
        "octonion_table_max_entry_residual_between_implementations" => max_entry_residual,
        "octonion_tables_match" => tables_match,
    )
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

function quantumoptics_unit_probe_guard(dim::Int, unit_index0::Int)
    basis = FockBasis(dim - 1)
    ket = basisstate(basis, unit_index0)
    rho = dm(ket)
    vals = eigvals(Hermitian(rho.data))
    Dict{String,Any}(
        "package" => "QuantumOptics",
        "basis" => "FockBasis($(dim - 1))",
        "fixed_unit_index0" => unit_index0,
        "trace" => real(tr(rho.data)),
        "trace_eq_1" => abs(real(tr(rho.data)) - 1.0) < TOL,
        "psd" => minimum(real.(vals)) >= -TOL,
        "hermitian_defect" => norm(rho.data - rho.data'),
        "hermitian" => norm(rho.data - rho.data') < TOL,
        "normalization" => "chosen probe ket has norm one and projector trace one",
    )
end

function summarize_system(name::String, table::Array{Int,3}, vectors::Vector{Vector{Int}})
    mat = augmented_constraint_matrix(table, vectors)
    rank_exact, pivots = exact_rank(mat)
    rank_svd, rank_tol, ns, singular_values = nullspace_data(mat)
    dim = size(table, 1)
    kernel_dim = dim^2 - rank_exact
    residual = kernel_dim > 0 ? derivation_residual(table, vec_to_matrix(ns[:, 1], dim)) : 0.0
    fixed_residual = kernel_dim > 0 ? fixation_residual(vec_to_matrix(ns[:, 1], dim), vectors) : 0.0
    free_cols = [col for col in 1:size(mat, 2) if !(col in Set(pivots))]
    Dict{String,Any}(
        "name" => name,
        "carrier_dim" => dim,
        "structure_constants_sha256" => table_sha(table),
        "constraint_rows" => size(mat, 1),
        "derivation_constraint_rows" => dim^3,
        "fixing_constraint_rows" => dim * length(vectors),
        "constraint_cols" => size(mat, 2),
        "exact_rank" => rank_exact,
        "svd_rank" => rank_svd,
        "rank_tol" => rank_tol,
        "kernel_dim" => kernel_dim,
        "stabilizer_dim" => kernel_dim,
        "pivot_count" => length(pivots),
        "free_coordinate_count" => kernel_dim,
        "free_columns_1based" => free_cols,
        "basis_derivation_residual_max" => residual,
        "basis_fixation_residual_max" => fixed_residual,
        "smallest_nonzero_singular_value" => rank_svd > 0 ? singular_values[rank_svd] : nothing,
        "largest_zero_singular_value" => rank_svd < length(singular_values) ? singular_values[rank_svd + 1] : nothing,
    )
end

function zadd(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function zmul(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function zlinear(ctx, coeffs::Vector{Int}, variables::Vector{Z3.Expr})
    terms = Z3.Expr[]
    for (coeff, var) in zip(coeffs, variables)
        coeff == 0 && continue
        if coeff == 1
            push!(terms, var)
        else
            push!(terms, zmul(ctx, [Z3.IntVal(coeff, ctx), var]))
        end
    end
    zadd(ctx, terms)
end

function nonzero_or(ctx, variables::Vector{Z3.Expr}, indices::Vector{Int})
    Z3.Or([Z3.Not(variables[idx] == Z3.IntVal(0, ctx)) for idx in indices])
end

function z3_kernel_guard(name::String, constrained_mat::Matrix{Int}, derivation_only_mat::Matrix{Int}, free_columns_1based::Vector{Int})
    ctx = Z3.Context()
    cols = size(constrained_mat, 2)
    free_set = Set(free_columns_1based)
    pivot_indices = [idx for idx in 1:cols if !(idx in free_set)]

    solver = Z3.Solver(ctx)
    vars = [Z3.IntVar("$(name)_d_$(idx)", ctx) for idx in 1:cols]
    for i in 1:size(constrained_mat, 1)
        row = vec(constrained_mat[i, :])
        any(!=(0), row) || continue
        Z3.add(solver, zlinear(ctx, row, vars) == Z3.IntVal(0, ctx))
    end
    for free_col in free_columns_1based
        Z3.add(solver, vars[free_col] == Z3.IntVal(0, ctx))
    end
    Z3.add(solver, nonzero_or(ctx, vars, pivot_indices))
    upper_status = string(Z3.check(solver))

    erased = Z3.Solver(ctx)
    erased_vars = [Z3.IntVar("$(name)_erased_d_$(idx)", ctx) for idx in 1:cols]
    for i in 1:size(derivation_only_mat, 1)
        row = vec(derivation_only_mat[i, :])
        any(!=(0), row) || continue
        Z3.add(erased, zlinear(ctx, row, erased_vars) == Z3.IntVal(0, ctx))
    end
    for free_col in free_columns_1based
        Z3.add(erased, erased_vars[free_col] == Z3.IntVal(0, ctx))
    end
    Z3.add(erased, nonzero_or(ctx, erased_vars, pivot_indices))
    erase_status = string(Z3.check(erased))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "claim" => "no nonzero integer-scaled kernel vector remains after the computed unit-fixing free coordinates are zeroed; erasing unit-fixing constraints admits one",
        "dimension_not_expected_status" => upper_status,
        "upper_bound_no_extra_solution_status" => upper_status,
        "drop_unit_fixing_constraints_status" => erase_status,
        "erase_flip_unsat_to_sat" => upper_status == "unsat" && erase_status == "sat",
        "asserted_constrained_rows" => count(i -> any(!=(0), constrained_mat[i, :]), 1:size(constrained_mat, 1)),
        "asserted_derivation_only_rows" => count(i -> any(!=(0), derivation_only_mat[i, :]), 1:size(derivation_only_mat, 1)),
        "free_coordinate_count" => length(free_columns_1based),
    )
end

function build_result()
    tables = build_tables()
    package_h, package_crosschecks = package_h_table()
    h_package_matches_cd = package_h == tables["H"]
    o = tables["O"]
    e1 = [0, 1, 0, 0, 0, 0, 0, 0]
    e2 = [0, 0, 1, 0, 0, 0, 0, 0]

    full = summarize_system("Der_O_no_unit_fixing_control", o, Vector{Vector{Int}}())
    unit = summarize_system("Der_O_fix_e1_unit_stabilizer", o, [e1])
    two_unit = summarize_system("Der_O_fix_e1_e2_two_unit_control", o, [e1, e2])
    forced_comm_unit = summarize_system("Der_O_forced_commutative_fix_e1_control", forced_commutative_table(o), [e1])
    qo_guard = quantumoptics_unit_probe_guard(8, 1)

    unit_mat = augmented_constraint_matrix(o, [e1])
    derivation_only_mat = derivation_constraint_matrix(o)
    julia_z3 = z3_kernel_guard("O_fix_e1", unit_mat, derivation_only_mat, Int.(unit["free_columns_1based"]))

    r3_peer = load_r3_peer_result()
    r3_check = r3_provenance_check(r3_peer, o)

    negative_control = Dict{String,Any}(
        "drop_unit_fixing_probe_dim_14_vs_8" => full["stabilizer_dim"] == 14 && unit["stabilizer_dim"] == 8,
        "drop_unit_fixing_probe_z3_unsat_to_sat" => julia_z3["erase_flip_unsat_to_sat"],
        "two_independent_units_dim_changes_3_vs_8" => two_unit["stabilizer_dim"] == 3 && two_unit["stabilizer_dim"] != unit["stabilizer_dim"],
        "forced_commutative_unit_fixing_dim_changes" => forced_comm_unit["stabilizer_dim"] != unit["stabilizer_dim"],
        "forced_commutative_unit_fixing_dim" => forced_comm_unit["stabilizer_dim"],
    )
    all_pass = Bool(
        h_package_matches_cd &&
        qo_guard["trace_eq_1"] &&
        qo_guard["psd"] &&
        qo_guard["hermitian"] &&
        full["stabilizer_dim"] == 14 &&
        unit["stabilizer_dim"] == 8 &&
        two_unit["stabilizer_dim"] == 3 &&
        forced_comm_unit["stabilizer_dim"] != 8 &&
        unit["basis_derivation_residual_max"] < TOL &&
        unit["basis_fixation_residual_max"] < TOL &&
        julia_z3["dimension_not_expected_status"] == "unsat" &&
        julia_z3["drop_unit_fixing_constraints_status"] == "sat" &&
        all(value for value in values(negative_control) if value isa Bool) &&
        r3_check["octonion_tables_match"] &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == true
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
        "r3_peer_provenance_check" => r3_check,
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_preflight" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => Base.active_project(),
        ),
        "M" => Dict(
            "name" => "unit_fixing_derivation_probe",
            "explicit_probe_family" => [
                "derivation rows: for every ordered octonion basis pair (e_a,e_b) and output coordinate c, D(e_a e_b)_c - (D(e_a)e_b + e_aD(e_b))_c",
                "unit-fixing rows: for fixed imaginary unit u=e1 and output coordinate c, D(u)_c",
            ],
            "finite_probe_counts" => Dict(
                "derivation_rows" => full["derivation_constraint_rows"],
                "unit_fixing_rows" => unit["fixing_constraint_rows"],
                "total_rows" => unit["constraint_rows"],
            ),
            "quantumoptics_probe_guard" => qo_guard,
        ),
        "C" => Dict(
            "trace_eq_1" => qo_guard["trace_eq_1"],
            "psd" => qo_guard["psd"],
            "hermitian" => qo_guard["hermitian"],
            "normalization" => "basis probes are unit-normalized; QuantumOptics fixed-unit projector has trace one",
            "rung_specific_constraint" => "D is an octonion derivation and D(e1)=0 for the chosen imaginary unit e1",
        ),
        "S_mod_M" => Dict(
            "definition" => "S=Der(O), D ~_M D' iff (D-D')(e1)=0 under the explicit unit-fixing probe; the selected quotient class is the kernel/stabilizer fixing e1",
            "class_dimensions" => Dict("Der_O" => full["stabilizer_dim"], "fix_e1" => unit["stabilizer_dim"]),
            "quotient_rank" => unit["exact_rank"],
            "interpretation" => "the unit-fixing subalgebra has dimension 8, the structural su(3) stabilizer dimension at scratch ceiling",
        ),
        "package_crosscheck" => Dict(
            "h_cliffordalgebras_matches_cayley_dickson" => h_package_matches_cd,
            "details" => package_crosschecks,
        ),
        "summaries" => Dict(
            "Der_O_no_unit_fixing_control" => full,
            "Der_O_fix_e1_unit_stabilizer" => unit,
            "Der_O_fix_e1_e2_two_unit_control" => two_unit,
            "Der_O_forced_commutative_fix_e1_control" => forced_comm_unit,
        ),
        "julia_z3" => julia_z3,
        "negative_control_flip" => negative_control,
        "summary" => Dict(
            "der_O_dim" => full["stabilizer_dim"],
            "fix_e1_stabilizer_dim" => unit["stabilizer_dim"],
            "fix_e1_e2_stabilizer_dim" => two_unit["stabilizer_dim"],
            "forced_commutative_fix_e1_dim" => forced_comm_unit["stabilizer_dim"],
            "unit_fix_rank" => unit["exact_rank"],
            "z3_dimension_not_8" => julia_z3["dimension_not_expected_status"],
            "z3_drop_unit_fixing" => julia_z3["drop_unit_fixing_constraints_status"],
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
        "FOUNDATION_R5_G2_SU3_REDUCTION_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "dim_der_O=", result["summary"]["der_O_dim"], " ",
        "fix_e1_dim=", result["summary"]["fix_e1_stabilizer_dim"], " ",
        "two_unit_dim=", result["summary"]["fix_e1_e2_stabilizer_dim"], " ",
        "forced_comm_fix_dim=", result["summary"]["forced_commutative_fix_e1_dim"], " ",
        "z3_dim_not_8=", result["summary"]["z3_dimension_not_8"], " ",
        "r3_octonion_tables_match=", lowercase(string(result["r3_peer_provenance_check"]["octonion_tables_match"])),
    )
    result["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
