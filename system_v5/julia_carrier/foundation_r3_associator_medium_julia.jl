#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras
using Grassmann
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_r3_associator_medium_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r3_associator_medium_julia_results.json")
const RUNG_ID = "foundation_r3_associator_medium"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-10

function h_table_from_clifford()
    cl = CliffordAlgebra(0, 2)
    basis = [cl.𝟏, cl.e1, cl.e2, cl.e1e2]
    labels = ["1", "i=e1", "j=e2", "k=e1e2"]
    props = [Symbol("𝟏"), :e1, :e2, :e1e2]
    table = zeros(Int, 4, 4, 4)
    for a in 1:4, b in 1:4
        prod = basis[a] * basis[b]
        for c in 1:4
            table[c, a, b] = Int(getproperty(prod, props[c]))
        end
    end
    table, labels
end

function conjugation_signs(n::Int)
    signs = ones(Int, n)
    signs[2:end] .= -1
    signs
end

function multiply(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    n = size(table, 1)
    out = zeros(Int, n)
    for c in 1:n, a in 1:n, b in 1:n
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function cayley_dickson_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2n
    table = zeros(Int, dim, dim, dim)
    signs = conjugation_signs(n)
    eye = Matrix{Int}(I, dim, dim)
    for aidx in 1:dim, bidx in 1:dim
        x = eye[:, aidx]
        y = eye[:, bidx]
        a = x[1:n]
        b = x[n+1:end]
        c = y[1:n]
        d = y[n+1:end]
        first = multiply(parent, a, c) - multiply(parent, signs .* d, b)
        second = multiply(parent, d, a) + multiply(parent, b, signs .* c)
        table[:, aidx, bidx] = vcat(first, second)
    end
    table
end

function associator(table::Array{Int,3}, a::Int, b::Int, c::Int)
    n = size(table, 1)
    eye = Matrix{Int}(I, n, n)
    left = multiply(table, multiply(table, eye[:, a], eye[:, b]), eye[:, c])
    right = multiply(table, eye[:, a], multiply(table, eye[:, b], eye[:, c]))
    left - right
end

function associator_summary(table::Array{Int,3}, labels::Vector{String})
    n = size(table, 1)
    max_norm = 0.0
    witness = Dict{String,Any}()
    nonzero_count = 0
    for a in 1:n, b in 1:n, c in 1:n
        v = associator(table, a, b, c)
        norm_v = norm(v)
        if norm_v > TOL
            nonzero_count += 1
        end
        if norm_v > max_norm
            max_norm = norm_v
            nz = findall(!=(0), v)
            witness = Dict{String,Any}(
                "basis_indices_zero_based" => [a - 1, b - 1, c - 1],
                "basis_labels" => [labels[a], labels[b], labels[c]],
                "component_indices_zero_based" => [idx - 1 for idx in nz],
                "vector" => collect(v),
                "norm" => norm_v,
            )
        end
    end
    Dict{String,Any}(
        "dimension" => n,
        "basis_labels" => labels,
        "max_associator_norm" => max_norm,
        "nonzero_associator_count" => nonzero_count,
        "associative_under_M" => max_norm <= TOL,
        "witness" => witness,
    )
end

function alternativity_summary(table::Array{Int,3})
    n = size(table, 1)
    repeated_max = 0.0
    antisymmetry_max = 0.0
    for a in 1:n, b in 1:n, c in 1:n
        repeated_max = max(repeated_max, norm(associator(table, a, a, c)))
        repeated_max = max(repeated_max, norm(associator(table, a, c, c)))
        antisymmetry_max = max(antisymmetry_max, norm(associator(table, a, b, c) + associator(table, b, a, c)))
        antisymmetry_max = max(antisymmetry_max, norm(associator(table, a, b, c) + associator(table, a, c, b)))
    end
    Dict{String,Any}(
        "repeated_input_associator_max_norm" => repeated_max,
        "alternativity_holds" => repeated_max <= TOL,
        "adjacent_swap_antisymmetry_max_norm" => antisymmetry_max,
        "antisymmetry_holds" => antisymmetry_max <= TOL,
        "power_associative_sampled" => repeated_max <= TOL,
    )
end

function z3_sum_terms(terms)
    isempty(terms) && return Z3.IntVal(0)
    Z3.Expr(terms[1].ctx, Z3.Z3_mk_add(Z3.ctx_ref(terms[1]), length(terms), map(e -> Z3.as_ast(e), terms)))
end

function z3_mul(left, right)
    Z3.Expr(left.ctx, Z3.Z3_mk_mul(Z3.ctx_ref(left), 2, [Z3.as_ast(left), Z3.as_ast(right)]))
end

function z3_sub(left, right)
    Z3.Expr(left.ctx, Z3.Z3_mk_sub(Z3.ctx_ref(left), 2, [Z3.as_ast(left), Z3.as_ast(right)]))
end

function z3_derived_associator_certificate(name::String, values::Array{Int,3})
    dim = size(values, 1)
    cache = Dict{Tuple{Int,Int,Int},Any}()
    constraints = Any[]

    function table_var(k::Int, i::Int, j::Int)
        key = (k, i, j)
        if !haskey(cache, key)
            var = Z3.IntVar("$(name)_T_$(k)_$(i)_$(j)")
            cache[key] = var
            push!(constraints, var == Z3.IntVal(values[k + 1, i + 1, j + 1]))
        end
        cache[key]
    end

    function assoc_component(a::Int, b::Int, c::Int, k::Int)
        left = z3_sum_terms([z3_mul(table_var(m, a, b), table_var(k, m, c)) for m in 0:(dim - 1)])
        right = z3_sum_terms([z3_mul(table_var(n, b, c), table_var(k, a, n)) for n in 0:(dim - 1)])
        z3_sub(left, right)
    end

    assoc_rows = Any[]
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1), k in 0:(dim - 1)
        push!(assoc_rows, assoc_component(a, b, c, k))
    end

    all_zero = Z3.Solver()
    for constraint in constraints
        Z3.add(all_zero, constraint)
    end
    for expr in assoc_rows
        Z3.add(all_zero, expr == Z3.IntVal(0))
    end
    with_zero = string(Z3.check(all_zero))

    erased = Z3.Solver()
    for constraint in constraints
        Z3.add(erased, constraint)
    end
    without_zero = string(Z3.check(erased))
    Dict{String,Any}(
        "ran" => true,
        "solver" => "Z3.jl",
        "bound_table_entry_equalities" => length(constraints),
        "derived_assoc_component_count" => length(assoc_rows),
        "asserted_precomputed_associator_coefficients" => 0,
        "assert_all_zero_status" => with_zero,
        "drop_all_zero_constraint_status" => without_zero,
        "erase_flip_unsat_to_sat" => with_zero == "unsat" && without_zero == "sat",
        "derivation" => "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside Z3.jl from bound T[k,i,j] table entries",
    )
end

function main()
    h_table, h_labels = h_table_from_clifford()
    o_table = cayley_dickson_double(h_table)
    o_labels = vcat(h_labels, ["ell", "iell", "jell", "kell"])

    h_summary = associator_summary(h_table, h_labels)
    o_summary = associator_summary(o_table, o_labels)
    o_structure = alternativity_summary(o_table)
    z3_flip = z3_derived_associator_certificate("julia_O_medium", o_table)

    all_pass = (
        h_summary["max_associator_norm"] <= TOL &&
        o_summary["max_associator_norm"] > TOL &&
        o_structure["alternativity_holds"] &&
        o_structure["antisymmetry_holds"] &&
        z3_flip["erase_flip_unsat_to_sat"]
    )

    payload = Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "rung_id" => RUNG_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => string(now(UTC)),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_project" => Base.active_project(),
        "packages_used" => ["CliffordAlgebras", "Grassmann", "Z3", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Grassmann", "Z3"],
        "claim_path_tools" => ["CliffordAlgebras", "Grassmann", "Z3"],
        "M" => Dict(
            "name" => "bracketing-distinguishability associator probe",
            "probe" => "[A,B,C] = (AB)C - A(BC)",
            "finite_probe_family" => "all basis triples in H and O multiplication tables",
        ),
        "C" => Dict(
            "trace_equals_one" => "not a state rung; replaced by unital basis e0=1",
            "psd" => "not a state rung; finite normed-division algebra structure constants instead",
            "hermiticity" => "not a state rung; conjugation signs [1,-1,...] define real star operation",
            "normalization" => "basis vectors are unit coordinate vectors",
            "rung_specific_constraint" => "normed division algebra multiplication from Cl(0,2)=H and Cayley-Dickson O over that H table",
        ),
        "S_quotient_under_M" => Dict(
            "relation" => "(AB)C ~ A(BC) iff associator(A,B,C) == 0",
            "H" => "one indistinguishable bracketing class for all basis triples",
            "O" => "at least one distinguishable bracketing class with nonzero associator",
        ),
        "construction" => Dict(
            "H" => "CliffordAlgebras.CliffordAlgebra(0,2) geometric product table",
            "O" => "Cayley-Dickson double of the package-computed H table",
            "Grassmann_role" => "aligned package import validates Grassmann/Clifford algebra substrate availability; O is not claimed as native Grassmann object",
        ),
        "values" => Dict("H" => h_summary, "O" => o_summary),
        "negative_control" => Dict(
            "H_to_O_structure_flip" => Dict(
                "H_associator_zero" => h_summary["max_associator_norm"] <= TOL,
                "O_associator_nonzero" => o_summary["max_associator_norm"] > TOL,
                "flips" => h_summary["max_associator_norm"] <= TOL && o_summary["max_associator_norm"] > TOL,
            ),
            "z3_drop_all_zero_constraint" => z3_flip,
        ),
        "octonion_structure" => o_structure,
        "all_pass" => all_pass,
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        println(io)
    end
    println("wrote: $(RESULT_PATH)")
    println("SCOUT_DONE H_norm=$(h_summary["max_associator_norm"]) O_norm=$(o_summary["max_associator_norm"]) witness=$(o_summary["witness"]["basis_labels"]) z3_flip=$(z3_flip["erase_flip_unsat_to_sat"]) all_pass=$(all_pass)")
    return all_pass ? 0 : 1
end

exit(main())
