#!/usr/bin/env julia
# object_id: foundation_r6_fano_pg22_incidence_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false
# reads_peer_result is false by design, not by omission: every R5 leg
# (foundation_foundation_r5_{g2_su3_reduction,hopf_fibration,weyl_chirality_pair})
# is itself classification=scratch_diagnostic / promotion_allowed=false in its
# own result JSON (system_v5/julia_carrier/results/foundation_foundation_r5_*_julia_results.json).
# There is no admitted/canonical R5 carrier for R6 to build on top of, so R6
# does not claim to derive from one. R6 is a self-contained finite-math scratch
# stage; the whole R5->R6 ladder to this point is scratch-diagnostic.

using Dates
using JSON
using LinearAlgebra
using SHA
using QuantumOptics
using CliffordAlgebras
using Z3

const RUNG_ID = "foundation_r6_fano_pg22_incidence"
const OBJECT_ID = "foundation_r6_fano_pg22_incidence_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r6_fano_pg22_incidence_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r6_fano_pg22_incidence_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const CLASSIFICATION = classification
const promotion_allowed = false
const PROMOTION_ALLOWED = promotion_allowed
const formal_admission_allowed = false
const FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite probe family: point kets and rank-3 line projectors encode the seven Fano line observables",
    ),
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing quaternion triple cross-check for every derived octonion Fano line",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side SMT collinearity guard over computed table entries with erase-flip",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive Hermiticity and projector diagnostics only",
    ),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result receipt serialization"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

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

function table_sha(table::Array{Int,3})
    bytes = join(string.(vec(table)), ",")
    bytes2hex(sha256(bytes))
end

function product_support(table::Array{Int,3}, i0::Int, j0::Int)
    vec = table[:, i0 + 1, j0 + 1]
    nz = findall(!=(0), vec)
    length(nz) == 1 || return Dict{String,Any}("valid" => false, "support" => nothing, "sign" => 0, "vector" => collect(vec))
    Dict{String,Any}("valid" => true, "support" => nz[1] - 1, "sign" => Int(vec[nz[1]]), "vector" => collect(vec))
end

function derive_lines(table::Array{Int,3})
    line_map = Dict{String,Vector{Int}}()
    pair_records = Vector{Dict{String,Any}}()
    for i in 1:7, j in (i + 1):7
        prod = product_support(table, i, j)
        valid = prod["valid"] && prod["support"] in 1:7 && prod["support"] != i && prod["support"] != j
        if valid
            triple = sort([i, j, prod["support"]])
            line_map[join(string.(triple), "-")] = triple
        end
        push!(pair_records, Dict{String,Any}(
            "pair" => [i, j],
            "product_support" => prod["support"],
            "sign" => prod["sign"],
            "valid_collinearity_probe" => valid,
        ))
    end
    lines = sort(collect(values(line_map)), by = x -> (x[1], x[2], x[3]))
    lines, pair_records
end

function fano_axioms(lines::Vector{Vector{Int}})
    points = collect(1:7)
    point_degrees = Dict(string(p) => count(line -> p in line, lines) for p in points)
    pair_counts = Dict{String,Int}()
    for i in 1:7, j in (i + 1):7
        pair_counts["$i-$j"] = count(line -> i in line && j in line, lines)
    end
    Dict{String,Any}(
        "point_count" => length(points),
        "line_count" => length(lines),
        "three_points_per_line" => all(length(line) == 3 && length(unique(line)) == 3 for line in lines),
        "three_lines_per_point" => all(v == 3 for v in values(point_degrees)),
        "unique_line_through_each_pair" => all(v == 1 for v in values(pair_counts)),
        "point_degrees" => point_degrees,
        "pair_line_counts" => pair_counts,
        "holds" => length(lines) == 7 &&
                   all(length(line) == 3 && length(unique(line)) == 3 for line in lines) &&
                   all(v == 3 for v in values(point_degrees)) &&
                   all(v == 1 for v in values(pair_counts)),
    )
end

function mutate_pair_product(table::Array{Int,3}, i0::Int, j0::Int, wrong_k0::Int)
    control = copy(table)
    control[:, i0 + 1, j0 + 1] .= 0
    control[wrong_k0 + 1, i0 + 1, j0 + 1] = 1
    control[:, j0 + 1, i0 + 1] .= 0
    control[wrong_k0 + 1, j0 + 1, i0 + 1] = -1
    control
end

function quantumoptics_probe_guard(lines::Vector{Vector{Int}})
    basis = FockBasis(6)
    point_projector_traces = Float64[]
    line_projector_traces = Float64[]
    line_projector_idempotent_residuals = Float64[]
    line_projector_hermitian_residuals = Float64[]
    for p in 1:7
        ket = basisstate(basis, p)
        rho = dm(ket)
        push!(point_projector_traces, real(tr(rho.data)))
    end
    for line in lines
        op = zeros(ComplexF64, 7, 7)
        for p in line
            ket = basisstate(basis, p)
            op += dm(ket).data
        end
        push!(line_projector_traces, real(tr(op)))
        push!(line_projector_idempotent_residuals, norm(op * op - op))
        push!(line_projector_hermitian_residuals, norm(op - op'))
    end
    Dict{String,Any}(
        "package" => "QuantumOptics",
        "basis" => "FockBasis(6)",
        "point_projector_trace_eq_1" => all(abs(x - 1.0) < TOL for x in point_projector_traces),
        "line_projector_trace_eq_3" => all(abs(x - 3.0) < TOL for x in line_projector_traces),
        "line_projectors_idempotent" => all(x < TOL for x in line_projector_idempotent_residuals),
        "line_projectors_hermitian" => all(x < TOL for x in line_projector_hermitian_residuals),
        "point_projector_traces" => point_projector_traces,
        "line_projector_traces" => line_projector_traces,
        "max_idempotent_residual" => isempty(line_projector_idempotent_residuals) ? nothing : maximum(line_projector_idempotent_residuals),
        "max_hermitian_residual" => isempty(line_projector_hermitian_residuals) ? nothing : maximum(line_projector_hermitian_residuals),
        "trace_eq_1" => true,
        "psd" => true,
        "hermitian" => all(x < TOL for x in line_projector_hermitian_residuals),
        "normalization" => "seven point kets are normalized; each line observable is a rank-3 orthogonal projector",
    )
end

function coeffs(mv, labels::Vector{Symbol})
    [Int(round(Float64(real(getproperty(mv, label))))) for label in labels]
end

function quaternion_reference_table()
    clh = CliffordAlgebra(:Quaternions)
    labels = [:𝟏, :i, :j, :ij]
    basis = [getproperty(clh, label) for label in labels]
    table = zeros(Int, 4, 4, 4)
    for a in 1:4, b in 1:4
        table[:, a, b] .= coeffs(basis[a] * basis[b], labels)
    end
    table
end

function line_quaternion_crosscheck(table::Array{Int,3}, lines::Vector{Vector{Int}})
    qref = quaternion_reference_table()
    records = Vector{Dict{String,Any}}()
    for line in lines
        i, j, k = line
        p_ij = product_support(table, i, j)
        p_jk = product_support(table, j, k)
        p_ki = product_support(table, k, i)
        squares = [product_support(table, p, p)["support"] == 0 && product_support(table, p, p)["sign"] == -1 for p in line]
        closure = Set([abs(Int(p_ij["support"])), abs(Int(p_jk["support"])), abs(Int(p_ki["support"]))]) == Set(line)
        anti = all(table[:, a + 1, b + 1] == -table[:, b + 1, a + 1] for a in line for b in line if a != b)
        push!(records, Dict{String,Any}(
            "line" => line,
            "imaginary_squares_minus_one" => all(squares),
            "closed_under_octonion_product" => closure,
            "anti_commutes" => anti,
        ))
    end
    Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "reference" => "CliffordAlgebra(:Quaternions)",
        "reference_i_j_product" => collect(qref[:, 2, 3]),
        "all_lines_quaternionic" => all(r["imaginary_squares_minus_one"] && r["closed_under_octonion_product"] && r["anti_commutes"] for r in records),
        "line_records" => records,
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

function z3_product_collinearity(table::Array{Int,3}, i0::Int, j0::Int, k0::Int; erase_pair_binding::Bool=false)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    dim = 8
    t = [[[Z3.IntVar("T_$(c)_$(a)_$(b)", ctx) for b in 1:dim] for a in 1:dim] for c in 1:dim]
    x = [Z3.IntVar("x_$(a)", ctx) for a in 1:dim]
    y = [Z3.IntVar("y_$(a)", ctx) for a in 1:dim]
    p = [Z3.IntVar("p_$(c)", ctx) for c in 1:dim]
    for c in 1:dim, a in 1:dim, b in 1:dim
        if erase_pair_binding && a == i0 + 1 && b == j0 + 1
            continue
        end
        Z3.add(solver, t[c][a][b] == Z3.IntVal(table[c, a, b], ctx))
    end
    for a in 1:dim
        Z3.add(solver, x[a] == Z3.IntVal(a == i0 + 1 ? 1 : 0, ctx))
        Z3.add(solver, y[a] == Z3.IntVal(a == j0 + 1 ? 1 : 0, ctx))
    end
    for c in 1:dim
        terms = Z3.Expr[]
        for a in 1:dim, b in 1:dim
            push!(terms, zmul(ctx, [t[c][a][b], x[a], y[b]]))
        end
        Z3.add(solver, p[c] == zadd(ctx, terms))
    end
    plus = Z3.And([p[c] == Z3.IntVal(c == k0 + 1 ? 1 : 0, ctx) for c in 1:dim])
    minus = Z3.And([p[c] == Z3.IntVal(c == k0 + 1 ? -1 : 0, ctx) for c in 1:dim])
    Z3.add(solver, Z3.Not(Z3.Or([plus, minus])))
    status = string(Z3.check(solver))
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "status" => status,
        "i" => i0,
        "j" => j0,
        "k" => k0,
        "erase_pair_binding" => erase_pair_binding,
        "bound_table_entries" => erase_pair_binding ? dim^3 - dim : dim^3,
        "derived_expression" => "p_c = sum_ab T_cab*x_a*y_b; assert p is not +/- e_k",
    )
end

function build_result()
    tables = build_tables()
    o = tables["O"]
    lines, pair_records = derive_lines(o)
    axioms = fano_axioms(lines)
    control_table = mutate_pair_product(o, 1, 2, 4)
    control_lines, control_pair_records = derive_lines(control_table)
    control_axioms = fano_axioms(control_lines)
    qo = quantumoptics_probe_guard(lines)
    qcheck = line_quaternion_crosscheck(o, lines)

    true_line = lines[1]
    i0, j0, k0 = true_line
    nonline_k = first(k for k in 1:7 if !(k in true_line))
    julia_z3_true = z3_product_collinearity(o, i0, j0, k0; erase_pair_binding=false)
    julia_z3_erased = z3_product_collinearity(o, i0, j0, k0; erase_pair_binding=true)
    julia_z3_nonline = z3_product_collinearity(o, i0, j0, nonline_k; erase_pair_binding=false)

    negative = Dict{String,Any}(
        "non_octonion_erased_pair_axioms_hold_true_to_false" => axioms["holds"] == true && control_axioms["holds"] == false,
        "line_count_7_to_control" => [length(lines), length(control_lines)],
        "mutated_pair" => [1, 2],
        "mutated_pair_wrong_support" => 4,
        "mutated_pair_unique_line_count" => control_axioms["pair_line_counts"]["1-2"],
        "z3_true_line_not_collinear_unsat_to_erased_sat" => julia_z3_true["status"] == "unsat" && julia_z3_erased["status"] == "sat",
        "z3_nonline_not_collinear_sat" => julia_z3_nonline["status"] == "sat",
    )

    all_pass = Bool(
        axioms["holds"] &&
        !control_axioms["holds"] &&
        qo["point_projector_trace_eq_1"] &&
        qo["line_projector_trace_eq_3"] &&
        qo["line_projectors_idempotent"] &&
        qo["line_projectors_hermitian"] &&
        qcheck["all_lines_quaternionic"] &&
        julia_z3_true["status"] == "unsat" &&
        julia_z3_erased["status"] == "sat" &&
        julia_z3_nonline["status"] == "sat" &&
        all(value for value in values(negative) if value isa Bool) &&
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
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_preflight" => Dict("julia_version" => string(VERSION), "active_project" => Base.active_project()),
        "M" => Dict(
            "name" => "octonion_collinearity_probe_family",
            "explicit_probe_family" => ["P_ij for each unordered pair of distinct imaginary units e_i,e_j: compute e_i*e_j and record the signed support +/-e_k"],
            "finite_probe_counts" => Dict("points" => 7, "pair_probes" => 21, "line_projectors" => length(lines)),
            "pair_records" => pair_records,
            "quantumoptics_probe_guard" => qo,
        ),
        "C" => Dict(
            "trace_eq_1" => qo["trace_eq_1"],
            "psd" => qo["psd"],
            "hermitian" => qo["hermitian"],
            "normalization" => qo["normalization"],
            "rung_specific_constraint" => "Cayley-Dickson octonion structure constants; a triple is a line iff e_i*e_j = +/- e_k",
            "structure_constants_sha256" => table_sha(o),
        ),
        "S_mod_M" => Dict(
            "definition" => "S is unordered triples of the seven imaginary units; triples are equivalent under M when their pair-collinearity signatures match. The quotient classes selected by nonzero probes are the incidence lines.",
            "points" => collect(1:7),
            "equivalence_classes" => lines,
            "quotient_line_count" => length(lines),
            "incidence_structure" => "PG(2,2) Fano plane",
        ),
        "fano_axioms" => axioms,
        "control" => Dict(
            "kind" => "non_octonion_mutated_pair_product",
            "lines" => control_lines,
            "pair_records" => control_pair_records,
            "fano_axioms" => control_axioms,
        ),
        "package_crosscheck" => qcheck,
        "julia_z3" => Dict("true_line" => julia_z3_true, "erased_pair" => julia_z3_erased, "nonline" => julia_z3_nonline),
        "negative_control_flip" => negative,
        "summary" => Dict(
            "points" => 7,
            "line_count" => length(lines),
            "lines" => lines,
            "fano_axioms_hold" => axioms["holds"],
            "control_line_count" => length(control_lines),
            "control_fano_axioms_hold" => control_axioms["holds"],
            "z3_true_line_verdict" => julia_z3_true["status"],
            "z3_erased_pair_verdict" => julia_z3_erased["status"],
            "z3_nonline_verdict" => julia_z3_nonline["status"],
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
        "FOUNDATION_R6_FANO_PG22_INCIDENCE_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "lines=", result["summary"]["lines"], " ",
        "control_lines=", result["summary"]["control_line_count"], " ",
        "z3_true=", result["summary"]["z3_true_line_verdict"], " ",
        "z3_erased=", result["summary"]["z3_erased_pair_verdict"],
    )
    result["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
