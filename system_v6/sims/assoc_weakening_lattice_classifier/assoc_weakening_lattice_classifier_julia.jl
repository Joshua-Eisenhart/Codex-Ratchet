#!/usr/bin/env julia
# Julia leg for the associativity weakening lattice classifier.

using Dates
using JSON
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "assoc_weakening_lattice_classifier"
const OBJECT_ID = "$(SIM_ID)_julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(SIM_DIR, "results", "$(SIM_ID)_julia_results.json")

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false
const TOL = 1.0e-9

const IDENTITY_ORDER = [
    "associativity",
    "alternativity",
    "artin_diassociativity_basis_pairs",
    "moufang",
    "flexibility",
    "power_associativity",
    "third_power_associativity",
    "none",
]

const TOOL_MANIFEST = Dict(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing in-solver associator violation/control from bound structure constants"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and table hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Z3" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

source_sha256() = bytes2hex(open(sha256, SOURCE_PATH))

function multiply(table::Array{Int,3}, x::Vector{<:Real}, y::Vector{<:Real})::Vector{Float64}
    dim = size(table, 1)
    out = zeros(Float64, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function multiply_int(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})::Vector{Int}
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function cd_conj(x::Vector{Int})::Vector{Int}
    y = copy(x)
    for i in 2:length(y)
        y[i] = -y[i]
    end
    y
end

function cd_double(parent::Array{Int,3})::Array{Int,3}
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Int, dim, dim, dim)
    for i in 1:dim, j in 1:dim
        x = zeros(Int, dim)
        y = zeros(Int, dim)
        x[i] = 1
        y[j] = 1
        a, b = x[1:n], x[n + 1:end]
        c, d = y[1:n], y[n + 1:end]
        first = multiply_int(parent, a, c) - multiply_int(parent, cd_conj(d), b)
        second = multiply_int(parent, d, a) + multiply_int(parent, b, cd_conj(c))
        table[:, i, j] = vcat(first, second)
    end
    table
end

function kill_control_table()::Array{Int,3}
    table = zeros(Int, 3, 3, 3)
    for i in 1:3
        table[i, 1, i] = 1
        table[i, i, 1] = 1
    end
    table[2, 2, 2] = 1
    table[2, 2, 3] = 1
    table[3, 3, 3] = 1
    table
end

function cayley_dickson_tables()
    real = ones(Int, 1, 1, 1)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    sedenion = cd_double(octonion)
    Dict("R" => real, "C" => complex_table, "H" => quaternion, "O" => octonion, "S" => sedenion, "K" => kill_control_table())
end

function basis(dim::Int)
    rows = Vector{Vector{Float64}}()
    for i in 1:dim
        row = zeros(Float64, dim)
        row[i] = 1.0
        push!(rows, row)
    end
    rows
end

function generic_samples(dim::Int)
    [Float64[((seed + 2) * i % 7) - 3 for i in 1:dim] for seed in 0:5]
end

elem_label(index::Int, dim::Int) = index <= dim ? "e$(index - 1)" : "g$(index - dim - 1)"
close_vec(x::Vector{Float64}, y::Vector{Float64}) = maximum(abs.(x - y)) <= TOL

function residual_support(vec::Vector{Float64})
    support = [i - 1 for i in 1:length(vec) if abs(vec[i]) > TOL]
    Dict("support" => support, "values" => [vec[i + 1] for i in support], "max_abs" => maximum(abs.(vec)))
end

function find_associativity(table::Array{Int,3})
    dim = size(table, 1)
    elems = vcat(basis(dim), generic_samples(dim))
    for i in 1:length(elems), j in 1:length(elems), k in 1:length(elems)
        left = multiply(table, multiply(table, elems[i], elems[j]), elems[k])
        right = multiply(table, elems[i], multiply(table, elems[j], elems[k]))
        if !close_vec(left, right)
            return false, merge(Dict("kind" => "associator", "x" => elem_label(i, dim), "y" => elem_label(j, dim), "z" => elem_label(k, dim)), residual_support(left - right))
        end
    end
    true, nothing
end

function find_alternativity(table::Array{Int,3})
    dim = size(table, 1)
    elems = vcat(basis(dim), generic_samples(dim))
    for i in 1:length(elems), j in 1:length(elems)
        left = multiply(table, multiply(table, elems[i], elems[i]), elems[j])
        right = multiply(table, elems[i], multiply(table, elems[i], elems[j]))
        if !close_vec(left, right)
            return false, merge(Dict("kind" => "left_alternative", "x" => elem_label(i, dim), "y" => elem_label(j, dim)), residual_support(left - right))
        end
        left = multiply(table, multiply(table, elems[j], elems[i]), elems[i])
        right = multiply(table, elems[j], multiply(table, elems[i], elems[i]))
        if !close_vec(left, right)
            return false, merge(Dict("kind" => "right_alternative", "x" => elem_label(i, dim), "y" => elem_label(j, dim)), residual_support(left - right))
        end
    end
    true, nothing
end

function generated_indices(table::Array{Int,3}, i0::Int, j0::Int)
    support = Set([1, i0, j0])
    changed = true
    while changed
        changed = false
        for a in collect(support), b in collect(support), k in 1:size(table, 1)
            if table[k, a, b] != 0 && !(k in support)
                push!(support, k)
                changed = true
            end
        end
    end
    sort(collect(support))
end

function find_artin_basis_pairs(table::Array{Int,3})
    dim = size(table, 1)
    eye = basis(dim)
    for i in 1:dim, j in 1:dim
        generated = generated_indices(table, i, j)
        for a in generated, b in generated, c in generated
            left = multiply(table, multiply(table, eye[a], eye[b]), eye[c])
            right = multiply(table, eye[a], multiply(table, eye[b], eye[c]))
            if !close_vec(left, right)
                return false, merge(
                    Dict(
                        "kind" => "basis_pair_generated_subalgebra_associator",
                        "generators" => ["e$(i - 1)", "e$(j - 1)"],
                        "basis_triple" => ["e$(a - 1)", "e$(b - 1)", "e$(c - 1)"],
                        "generated_indices" => [x - 1 for x in generated],
                    ),
                    residual_support(left - right),
                )
            end
        end
    end
    true, nothing
end

function find_moufang(table::Array{Int,3})
    dim = size(table, 1)
    elems = vcat(basis(dim), generic_samples(dim))
    for i in 1:length(elems), j in 1:length(elems), k in 1:length(elems)
        left = multiply(table, multiply(table, elems[i], elems[j]), multiply(table, elems[k], elems[i]))
        right = multiply(table, elems[i], multiply(table, multiply(table, elems[j], elems[k]), elems[i]))
        if !close_vec(left, right)
            return false, merge(Dict("kind" => "moufang", "x" => elem_label(i, dim), "y" => elem_label(j, dim), "z" => elem_label(k, dim)), residual_support(left - right))
        end
    end
    true, nothing
end

function find_flexibility(table::Array{Int,3})
    dim = size(table, 1)
    elems = vcat(basis(dim), generic_samples(dim))
    for i in 1:length(elems), j in 1:length(elems)
        left = multiply(table, multiply(table, elems[i], elems[j]), elems[i])
        right = multiply(table, elems[i], multiply(table, elems[j], elems[i]))
        if !close_vec(left, right)
            return false, merge(Dict("kind" => "flexibility", "x" => elem_label(i, dim), "y" => elem_label(j, dim)), residual_support(left - right))
        end
    end
    true, nothing
end

function find_power_associativity(table::Array{Int,3})
    dim = size(table, 1)
    elems = vcat(basis(dim), generic_samples(dim))
    for i in 1:length(elems)
        x = elems[i]
        xx = multiply(table, x, x)
        x3_left = multiply(table, xx, x)
        x3_right = multiply(table, x, xx)
        if !close_vec(x3_left, x3_right)
            return false, merge(Dict("kind" => "x3_bracketing", "x" => elem_label(i, dim)), residual_support(x3_left - x3_right))
        end
        x4 = [
            multiply(table, multiply(table, xx, x), x),
            multiply(table, multiply(table, x, xx), x),
            multiply(table, xx, xx),
            multiply(table, x, multiply(table, xx, x)),
            multiply(table, x, multiply(table, x, xx)),
        ]
        for idx in 2:length(x4)
            if !close_vec(x4[1], x4[idx])
                return false, merge(Dict("kind" => "x4_bracketing", "x" => elem_label(i, dim), "bracketing_index" => idx - 1), residual_support(x4[1] - x4[idx]))
            end
        end
    end
    true, nothing
end

function find_third_power(table::Array{Int,3})
    dim = size(table, 1)
    elems = vcat(basis(dim), generic_samples(dim))
    for i in 1:length(elems)
        left = multiply(table, elems[i], multiply(table, elems[i], elems[i]))
        right = multiply(table, multiply(table, elems[i], elems[i]), elems[i])
        if !close_vec(left, right)
            return false, merge(Dict("kind" => "third_power", "x" => elem_label(i, dim)), residual_support(left - right))
        end
    end
    true, nothing
end

function classify_table(table::Array{Int,3})
    checks = Dict(
        "associativity" => find_associativity(table),
        "alternativity" => find_alternativity(table),
        "artin_diassociativity_basis_pairs" => find_artin_basis_pairs(table),
        "moufang" => find_moufang(table),
        "flexibility" => find_flexibility(table),
        "power_associativity" => find_power_associativity(table),
        "third_power_associativity" => find_third_power(table),
    )
    matrix = Dict(name => checks[name][1] for name in keys(checks))
    matrix["none"] = !any(values(matrix))
    witnesses = Dict(name => checks[name][2] for name in keys(checks) if checks[name][2] !== nothing)
    position = first(name for name in IDENTITY_ORDER if matrix[name])
    Dict("identity_results" => matrix, "lattice_position" => position, "failure_witnesses" => witnesses)
end

function output_permuted_table(table::Array{Int,3})
    dim = size(table, 1)
    perm = collect(1:dim)
    if dim > 2
        perm[2], perm[3] = perm[3], perm[2]
    end
    table[perm, :, :]
end

table_sha256(table::Array{Int,3}) = bytes2hex(sha256(join(string.(vec(table)), ",")))

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_bind_table(table::Array{Int,3}, label::String)
    dim = size(table, 1)
    solver = Z3.Solver()
    c = Array{Z3.Expr,3}(undef, dim, dim, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        c[k, i, j] = Z3.IntVar("$(label)_C_$(k)_$(i)_$(j)")
        Z3.add(solver, c[k, i, j] == Z3.IntVal(table[k, i, j]))
    end
    solver, c
end

z3_coeff(value) = value isa Integer ? Z3.IntVal(value) : value

function z3_product(c::Array{Z3.Expr,3}, x::Vector, y::Vector)
    dim = size(c, 1)
    out = Vector{Z3.Expr}()
    for k in 1:dim
        terms = Z3.Expr[]
        for i in 1:dim, j in 1:dim
            if (x[i] isa Integer && x[i] == 0) || (y[j] isa Integer && y[j] == 0)
                continue
            end
            push!(terms, z3_mul(Z3.Expr[z3_coeff(x[i]), z3_coeff(y[j]), c[k, i, j]]))
        end
        push!(out, z3_add(terms))
    end
    out
end

function z3_assoc_violation(table::Array{Int,3}, label::String; witness=nothing)
    dim = size(table, 1)
    solver, c = z3_bind_table(table, "$(label)_assoc")
    eye = [Int[a == b ? 1 : 0 for a in 1:dim] for b in 1:dim]
    triples = witness === nothing ? [(i, j, k) for i in 1:dim, j in 1:dim, k in 1:dim] : [witness]
    diffs = Z3.Expr[]
    for (i, j, k) in triples
        left = z3_product(c, z3_product(c, eye[i], eye[j]), eye[k])
        right = z3_product(c, eye[i], z3_product(c, eye[j], eye[k]))
        for m in 1:dim
            push!(diffs, Z3.Not(left[m] == right[m]))
        end
    end
    Z3.add(solver, Z3.Or(diffs))
    Dict(
        "solver" => "julia_z3",
        "verdict" => string(Z3.check(solver)),
        "algebra" => label,
        "witness_scope" => witness === nothing ? "all_basis_triples" : "fixed_basis",
        "witness" => witness === nothing ? nothing : [witness[1] - 1, witness[2] - 1, witness[3] - 1],
    )
end

function build_result()
    tables = cayley_dickson_tables()
    classifications = Dict(name => classify_table(table) for (name, table) in tables)
    matrix = Dict(name => row["identity_results"] for (name, row) in classifications)
    positions = Dict(name => row["lattice_position"] for (name, row) in classifications)
    witnesses = Dict(name => row["failure_witnesses"] for (name, row) in classifications)
    permuted = classify_table(output_permuted_table(tables["O"]))
    column_has_fail = Dict(identity => any(!matrix[alg][identity] for alg in keys(matrix)) for identity in IDENTITY_ORDER)
    julia_z3 = Dict(
        "O_associativity_violation" => z3_assoc_violation(tables["O"], "O"; witness=(2, 3, 5)),
        "H_associativity_violation_control" => z3_assoc_violation(tables["H"], "H"),
    )
    expected = Dict(
        "O_expected" => matrix["O"]["associativity"] == false && all(matrix["O"][key] == true for key in ["alternativity", "artin_diassociativity_basis_pairs", "moufang", "flexibility", "power_associativity", "third_power_associativity"]),
        "S_expected" => matrix["S"]["alternativity"] == false && matrix["S"]["flexibility"] == true && matrix["S"]["power_associativity"] == true && matrix["S"]["third_power_associativity"] == true,
        "kill_control_fails_flexibility" => matrix["K"]["flexibility"] == false,
        "column_fail_coverage" => all(values(column_has_fail)),
        "permuted_table_control_shifts" => permuted["lattice_position"] != positions["O"],
    )
    smt_ok = julia_z3["O_associativity_violation"]["verdict"] == "sat" && julia_z3["H_associativity_violation_control"]["verdict"] == "unsat"
    all_pass = (
        all(values(expected)) &&
        smt_ok &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )
    Dict(
        "schema_version" => "engine_leg_result_v1",
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH,
        "source_sha256" => source_sha256(),
        "result_path" => RESULT_PATH,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "runtime" => Dict("julia_version" => string(VERSION), "active_project" => Base.active_project()),
        "identity_order" => IDENTITY_ORDER,
        "algebra_dimensions" => Dict(name => size(table, 1) for (name, table) in tables),
        "table_sha256" => Dict(name => table_sha256(table) for (name, table) in tables),
        "classification_matrix" => matrix,
        "lattice_positions" => positions,
        "failure_witnesses" => witnesses,
        "controls" => Dict(
            "column_has_at_least_one_fail" => column_has_fail,
            "permuted_output_axis_O" => Dict(
                "original_position" => positions["O"],
                "permuted_position" => permuted["lattice_position"],
                "shifted" => permuted["lattice_position"] != positions["O"],
                "permuted_identity_results" => permuted["identity_results"],
            ),
        ),
        "smt" => Dict("julia_z3" => julia_z3),
        "expected_checks" => expected,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "all_pass" => all_pass,
    )
end

function main()::Int
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: ", RESULT_PATH)
    println(
        "ASSOC_WEAKENING_JULIA_DONE all_pass=$(result["all_pass"]) " *
        "O=$(result["lattice_positions"]["O"]) " *
        "S=$(result["lattice_positions"]["S"]) " *
        "K=$(result["lattice_positions"]["K"]) " *
        "julia_z3_O=$(result["smt"]["julia_z3"]["O_associativity_violation"]["verdict"])"
    )
    result["all_pass"] ? 0 : 2
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
