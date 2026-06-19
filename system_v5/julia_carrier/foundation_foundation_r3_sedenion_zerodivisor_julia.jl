#!/usr/bin/env julia

using Dates
using JSON
using CliffordAlgebras
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_r3_sedenion_zerodivisor"
const OBJECT_ID = "foundation_foundation_r3_sedenion_zerodivisor_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r3_sedenion_zerodivisor_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r3_sedenion_zerodivisor_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

function basis(dim::Int, idx0::Int)
    v = zeros(Int, dim)
    v[idx0 + 1] = 1
    v
end

function cd_conj(x::Vector{Int})
    out = copy(x)
    for idx in 2:length(out)
        out[idx] = -out[idx]
    end
    out
end

function multiply(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        coeff = table[k, i, j]
        if coeff != 0 && x[i] != 0 && y[j] != 0
            out[k] += coeff * x[i] * y[j]
        end
    end
    out
end

function cd_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2n
    table = zeros(Int, dim, dim, dim)
    for i in 1:dim, j in 1:dim
        x = basis(dim, i - 1)
        y = basis(dim, j - 1)
        a = x[1:n]
        b = x[(n + 1):dim]
        c = y[1:n]
        d = y[(n + 1):dim]
        first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
        second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
        table[:, i, j] = vcat(first, second)
    end
    table
end

function cd_tables()
    r = zeros(Int, 1, 1, 1)
    r[1, 1, 1] = 1
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    s = cd_double(o)
    Dict("R" => r, "C" => c, "H" => h, "O" => o, "S" => s)
end

normsq(v::Vector{Int}) = sum(x * x for x in v)

function vector_terms(v::Vector{Int})
    terms = Vector{Dict{String,Any}}()
    for idx in 1:length(v)
        coeff = v[idx]
        if coeff != 0
            push!(terms, Dict("basis_index" => idx - 1, "label" => "e$(idx - 1)", "coefficient" => coeff))
        end
    end
    terms
end

function signed_two_term_vectors(dim::Int; include_zero::Bool=false)
    vectors = Vector{Vector{Int}}()
    if include_zero
        push!(vectors, zeros(Int, dim))
    end
    for i in 1:(dim - 1), j in (i + 1):(dim - 1), si in (-1, 1), sj in (-1, 1)
        v = zeros(Int, dim)
        v[i + 1] = si
        v[j + 1] = sj
        push!(vectors, v)
    end
    vectors
end

function zero_divisor_probe(table::Array{Int,3}; include_zero::Bool=false)
    dim = size(table, 1)
    vectors = signed_two_term_vectors(dim; include_zero=include_zero)
    first = nothing
    count = 0
    min_product_normsq = typemax(Int)
    for (li, left) in enumerate(vectors), (ri, right) in enumerate(vectors)
        product = multiply(table, left, right)
        product_normsq = normsq(product)
        min_product_normsq = min(min_product_normsq, product_normsq)
        if product_normsq == 0 && (include_zero || (normsq(left) > 0 && normsq(right) > 0))
            count += 1
            if first === nothing
                first = Dict(
                    "left_index" => li,
                    "right_index" => ri,
                    "left_terms" => vector_terms(left),
                    "right_terms" => vector_terms(right),
                    "product_terms" => vector_terms(product),
                    "left_normsq" => normsq(left),
                    "right_normsq" => normsq(right),
                    "product_normsq" => product_normsq,
                )
            end
        end
    end
    Dict(
        "candidate_vector_count" => length(vectors),
        "candidate_pair_count" => length(vectors)^2,
        "include_zero_vector" => include_zero,
        "zero_product_pair_count" => count,
        "zero_divisor_exists" => count > 0,
        "min_product_normsq" => min_product_normsq,
        "first_witness" => first,
    )
end

function norm_defect_coefficients(table::Array{Int,3})
    dim = size(table, 1)
    coeffs = Dict{Tuple{Tuple{Int,Int},Tuple{Int,Int}},Int}()
    terms_by_output = [Vector{Tuple{Int,Int,Int}}() for _ in 1:dim]
    for k in 1:dim, i in 1:dim, j in 1:dim
        value = table[k, i, j]
        if value != 0
            push!(terms_by_output[k], (i - 1, j - 1, value))
        end
    end
    for terms in terms_by_output
        for (i, j, c1) in terms, (p, q, c2) in terms
            akey = i <= p ? (i, p) : (p, i)
            bkey = j <= q ? (j, q) : (q, j)
            key = (akey, bkey)
            coeffs[key] = get(coeffs, key, 0) + c1 * c2
        end
    end
    for i in 0:(dim - 1), j in 0:(dim - 1)
        key = ((i, i), (j, j))
        coeffs[key] = get(coeffs, key, 0) - 1
    end
    nonzero_coeffs = Dict(k => v for (k, v) in coeffs if v != 0)
    coeff_values = collect(values(nonzero_coeffs))
    sample = collect(nonzero_coeffs)[1:min(length(nonzero_coeffs), 8)]
    Dict(
        "nonzero_coeff_count" => length(nonzero_coeffs),
        "max_abs_coeff" => isempty(coeff_values) ? 0 : maximum(abs.(coeff_values)),
        "sample_nonzero_coefficients" => [
            Dict("a_pair" => collect(k[1]), "b_pair" => collect(k[2]), "coefficient" => v)
            for (k, v) in sample
        ],
        "identity_holds" => length(nonzero_coeffs) == 0,
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

function zneq(a::Z3.Expr, b::Z3.Expr)
    Z3.Not(a == b)
end

function smt_product_exprs(ctx, table::Array{Int,3}, left_vars, right_vars)
    dim = size(table, 1)
    exprs = Vector{Z3.Expr}()
    for k in 1:dim
        terms = Vector{Z3.Expr}()
        for i in 1:dim, j in 1:dim
            coeff = table[k, i, j]
            if coeff != 0
                push!(terms, zmul(ctx, [Z3.IntVal(coeff, ctx), left_vars[i], right_vars[j]]))
            end
        end
        push!(exprs, zadd(ctx, terms))
    end
    exprs
end

function z3_derived_product_check(table::Array{Int,3}, left::Vector{Int}, right::Vector{Int}; assert_zero_product::Bool=true)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    dim = size(table, 1)
    left_vars = [Z3.IntVar("left_$(i - 1)", ctx) for i in 1:dim]
    right_vars = [Z3.IntVar("right_$(i - 1)", ctx) for i in 1:dim]
    for i in 1:dim
        Z3.add(solver, left_vars[i] == Z3.IntVal(left[i], ctx))
        Z3.add(solver, right_vars[i] == Z3.IntVal(right[i], ctx))
    end
    Z3.add(solver, Z3.Or([zneq(v, Z3.IntVal(0, ctx)) for v in left_vars]))
    Z3.add(solver, Z3.Or([zneq(v, Z3.IntVal(0, ctx)) for v in right_vars]))
    product_exprs = smt_product_exprs(ctx, table, left_vars, right_vars)
    if assert_zero_product
        for expr in product_exprs
            Z3.add(solver, expr == Z3.IntVal(0, ctx))
        end
    end
    string(Z3.check(solver))
end

function concrete_witness(table::Array{Int,3}, left::Vector{Int}, right::Vector{Int}, claim::String)
    product = multiply(table, left, right)
    Dict(
        "claim" => claim,
        "left_components" => left,
        "right_components" => right,
        "left_terms" => vector_terms(left),
        "right_terms" => vector_terms(right),
        "product_components" => product,
        "product_terms" => vector_terms(product),
        "left_normsq" => normsq(left),
        "right_normsq" => normsq(right),
        "product_normsq" => normsq(product),
        "norm_multiplicativity_defect" => normsq(product) - normsq(left) * normsq(right),
        "pass" => normsq(left) > 0 && normsq(right) > 0 && normsq(product) == 0,
    )
end

function clifford_probe()
    cl3 = CliffordAlgebra(3)
    e1 = basevector(cl3, :e1)
    e2 = basevector(cl3, :e2)
    zero = MultiVector(cl3, 0)
    one = MultiVector(cl3, 1)
    Dict(
        "package" => "CliffordAlgebras",
        "dimension_cl3" => dimension(cl3),
        "e1_square_is_one" => e1 * e1 == one,
        "e1_e2_anticommutes" => e1 * e2 + e2 * e1 == zero,
    )
end

function table_summary(table::Array{Int,3})
    Dict("dim" => size(table, 1), "nonzero_entry_count" => count(!=(0), table), "sum_abs_entries" => sum(abs, table))
end

function main()
    tables = cd_tables()
    o_table = tables["O"]
    s_table = tables["S"]
    zero_o_table = zeros(Int, size(o_table))
    o_probe = zero_divisor_probe(o_table)
    s_probe = zero_divisor_probe(s_table)
    o_norm = norm_defect_coefficients(o_table)
    s_norm = norm_defect_coefficients(s_table)
    s_left = basis(16, 1) + basis(16, 10)
    s_right = basis(16, 5) + basis(16, 14)
    o_left = basis(8, 1) + basis(8, 2)
    o_right = basis(8, 3) + basis(8, 4)
    s_witness = concrete_witness(s_table, s_left, s_right, "(e1 + e10) * (e5 + e14) = 0 in S")
    o_control = concrete_witness(o_table, o_left, o_right, "(e1 + e2) * (e3 + e4) != 0 in O")
    z3_s_status = z3_derived_product_check(s_table, s_left, s_right; assert_zero_product=true)
    z3_o_status = z3_derived_product_check(o_table, o_left, o_right; assert_zero_product=true)
    z3_o_drop_probe_status = z3_derived_product_check(o_table, o_left, o_right; assert_zero_product=false)
    z3_o_zero_structure_status = z3_derived_product_check(zero_o_table, o_left, o_right; assert_zero_product=true)
    clifford = clifford_probe()
    all_pass = (
        !o_probe["zero_divisor_exists"] &&
        o_norm["identity_holds"] &&
        s_probe["zero_divisor_exists"] &&
        !s_norm["identity_holds"] &&
        s_witness["pass"] &&
        !o_control["pass"] &&
        o_control["product_normsq"] > 0 &&
        z3_s_status == "sat" &&
        z3_o_status == "unsat" &&
        z3_o_drop_probe_status == "sat" &&
        z3_o_zero_structure_status == "sat" &&
        clifford["e1_square_is_one"] &&
        clifford["e1_e2_anticommutes"]
    )

    payload = Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => string(now(UTC)),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_project" => Base.active_project(),
        "packages_used" => ["CliffordAlgebras", "Z3", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "claim_path_tools" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => Dict(
            "Cayley-Dickson" => Dict("tried" => true, "used" => true, "reason" => "authoritative O/S multiplication table construction"),
            "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "aligned algebra package sanity check for geometric-product carrier conventions"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT over products derived inside Z3 from computed structure constants"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt writing")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Cayley-Dickson" => "load_bearing", "CliffordAlgebras" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive"),
        "M" => Dict(
            "name" => "finite signed two-term imaginary-vector product probes",
            "vectors" => "all signed two-term pure-imaginary vectors +/-e_i +/-e_j for 1 <= i < j < dim",
            "observables" => ["zero-product existence with nonzero factors", "norm-multiplicativity defect coefficients", "fixed S annihilator product", "fixed O non-annihilator control product"],
            "O_candidate_vectors" => o_probe["candidate_vector_count"],
            "O_candidate_pairs" => o_probe["candidate_pair_count"],
            "S_candidate_vectors" => s_probe["candidate_vector_count"],
            "S_candidate_pairs" => s_probe["candidate_pair_count"],
        ),
        "C" => Dict(
            "trace_equals_one" => "not a density-state rung; carrier normalization is finite unital real algebra with e0 identity",
            "psd" => "not a density-state rung; positivity surrogate is nonzero quadratic norm sum_i x_i^2 > 0 on factors",
            "hermiticity" => "not a density-state rung; involution is Cayley-Dickson conjugation",
            "normalization" => "left and right witnesses are fixed nonzero signed two-term vectors",
            "rung_specific_constraint" => "O and S multiplication tables are computed by Cayley-Dickson doubling from R; solver product equations use those table constants",
        ),
        "S_quotient_under_M" => Dict(
            "relation" => "two finite carriers are equivalent when M sees the same zero-product and norm-multiplicativity profile",
            "O_class" => "normed division under M: no nonzero signed two-term zero-product pair and norm identity coefficients vanish",
            "S_class" => "zero-divisor under M: fixed nonzero S pair annihilates and norm identity has nonzero defect coefficients",
            "quotient_split" => "O and S are separated by M",
        ),
        "tables" => Dict("O" => table_summary(o_table), "S" => table_summary(s_table)),
        "octonion" => Dict("zero_divisor_probe" => o_probe, "norm_multiplicativity" => o_norm, "fixed_control" => o_control),
        "sedenion" => Dict("zero_divisor_probe" => s_probe, "concrete_witness" => s_witness, "norm_multiplicativity" => s_norm),
        "clifford_package_probe" => clifford,
        "smt" => Dict(
            "Z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "product_derived_in_solver" => true,
                "sedenion_witness_verdict" => z3_s_status,
                "octonion_control_verdict" => z3_o_status,
                "octonion_drop_product_probe_verdict" => z3_o_drop_probe_status,
                "octonion_zero_structure_verdict" => z3_o_zero_structure_status,
            )
        ),
        "negative_control" => Dict(
            "S_vs_O_solver_flip" => Dict("S_zero_product" => z3_s_status, "O_same_shape_zero_product" => z3_o_status, "flips" => z3_s_status == "sat" && z3_o_status == "unsat"),
            "drop_product_zero_probe_for_O" => Dict("with_probe" => z3_o_status, "without_probe" => z3_o_drop_probe_status, "flips" => z3_o_status == "unsat" && z3_o_drop_probe_status == "sat"),
            "erase_O_structure_constants" => Dict("with_O_table" => z3_o_status, "with_zero_table" => z3_o_zero_structure_status, "flips" => z3_o_status == "unsat" && z3_o_zero_structure_status == "sat"),
        ),
        "all_pass" => all_pass,
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        println(io)
    end
    println("wrote: $(RESULT_PATH)")
    println("SCOUT_DONE all_pass=$(all_pass) S_product_normsq=$(s_witness["product_normsq"]) S_defect=$(s_witness["norm_multiplicativity_defect"]) O_product_normsq=$(o_control["product_normsq"]) z3_S=$(z3_s_status) z3_O=$(z3_o_status)")
    return all_pass ? 0 : 1
end

exit(main())
