#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "pg32_sedenion_incidence"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(SIM_DIR, "results", "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

const OCTONION_TRIPLES = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function sha256_file(path::String)
    bytes2hex(open(sha256, path))
end

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

function multiply_table(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
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

function octonion_table()
    table = zeros(Int, 8, 8, 8)
    table[1, 1, 1] = 1
    for i in 2:8
        table[i, 1, i] = 1
        table[i, i, 1] = 1
        table[1, i, i] = -1
    end
    for (a0, b0, c0) in OCTONION_TRIPLES
        for (x0, y0, z0, sign) in (
            (a0, b0, c0, 1),
            (b0, c0, a0, 1),
            (c0, a0, b0, 1),
            (b0, a0, c0, -1),
            (c0, b0, a0, -1),
            (a0, c0, b0, -1),
        )
            table[z0 + 1, x0 + 1, y0 + 1] = sign
        end
    end
    table
end

function cd_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2n
    table = zeros(Int, dim, dim, dim)
    for i0 in 0:(dim - 1), j0 in 0:(dim - 1)
        x = basis(dim, i0)
        y = basis(dim, j0)
        a = x[1:n]
        b = x[(n + 1):dim]
        c = y[1:n]
        d = y[(n + 1):dim]
        first = multiply_table(parent, a, c) - multiply_table(parent, cd_conj(d), b)
        second = multiply_table(parent, d, a) + multiply_table(parent, b, cd_conj(c))
        table[:, i0 + 1, j0 + 1] = vcat(first, second)
    end
    table
end

sedenion_table() = cd_double(octonion_table())

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

normsq(v::Vector{Int}) = sum(x * x for x in v)

function product_index_and_sign(table::Array{Int,3}, a::Int, b::Int)
    prod = multiply_table(table, basis(size(table, 1), a), basis(size(table, 1), b))
    terms = vector_terms(prod)
    length(terms) == 1 || error("basis product e$a*e$b has $(length(terms)) terms")
    (terms[1]["basis_index"], terms[1]["coefficient"])
end

function extract_lines(table::Array{Int,3}, points)
    lines = Set{Tuple{Int,Int,Int}}()
    pair_to_line = Dict{Tuple{Int,Int},Tuple{Int,Int,Int}}()
    for a in points, b in points
        a < b || continue
        k, sign = product_index_and_sign(table, a, b)
        if k in points && abs(sign) == 1
            line = Tuple(sort([a, b, k]))
            push!(lines, line)
            pair_to_line[(a, b)] = line
        end
    end
    (sort(collect(lines)), pair_to_line)
end

function pair_axiom(lines, points)
    bad = Vector{Dict{String,Any}}()
    pair_count = 0
    for a in points, b in points
        a < b || continue
        pair_count += 1
        count_lines = count(line -> a in line && b in line, lines)
        if count_lines != 1
            push!(bad, Dict("pair" => [a, b], "line_count" => count_lines))
        end
    end
    Dict("pair_count" => pair_count, "all_pairs_exactly_one_line" => isempty(bad), "violations" => bad)
end

function combinations_k(values::Vector{Int}, k::Int)
    out = Vector{Vector{Int}}()
    current = Int[]
    function rec(start_idx::Int)
        if length(current) == k
            push!(out, copy(current))
            return
        end
        remaining = k - length(current)
        for idx in start_idx:(length(values) - remaining + 1)
            push!(current, values[idx])
            rec(idx + 1)
            pop!(current)
        end
    end
    rec(1)
    out
end

function planes_from_pair_map(pair_to_line, points)
    out = Vector{Vector{Int}}()
    point_vec = collect(points)
    for subset in combinations_k(point_vec, 7)
        subset_set = Set(subset)
        ok = true
        for i in 1:6, j in (i + 1):7
            if !issubset(Set(pair_to_line[(subset[i], subset[j])]), subset_set)
                ok = false
                break
            end
        end
        ok && push!(out, subset)
    end
    out
end

function associator(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int}, z::Vector{Int})
    multiply_table(table, multiply_table(table, x, y), z) - multiply_table(table, x, multiply_table(table, y, z))
end

function alternative_witness(table::Array{Int,3}, plane::Vector{Int})
    labels = vcat([0], plane)
    vecs = [basis(16, label) for label in labels]
    for ix in 1:length(vecs), iy in 1:length(vecs), iz in 1:length(vecs)
        x, y, z = vecs[ix], vecs[iy], vecs[iz]
        left_alt = associator(table, x, y, z) + associator(table, y, x, z)
        right_alt = associator(table, x, y, z) + associator(table, x, z, y)
        if normsq(left_alt) != 0
            return Dict(
                "kind" => "left_linearized_alternativity_failure",
                "x" => labels[ix],
                "y" => labels[iy],
                "z" => labels[iz],
                "associator_xyz" => vector_terms(associator(table, x, y, z)),
                "associator_yxz" => vector_terms(associator(table, y, x, z)),
                "sum_terms" => vector_terms(left_alt),
            )
        end
        if normsq(right_alt) != 0
            return Dict(
                "kind" => "right_linearized_alternativity_failure",
                "x" => labels[ix],
                "y" => labels[iy],
                "z" => labels[iz],
                "associator_xyz" => vector_terms(associator(table, x, y, z)),
                "associator_xzy" => vector_terms(associator(table, x, z, y)),
                "sum_terms" => vector_terms(right_alt),
            )
        end
    end
    nothing
end

function plane_classification(table, lines, pair_to_line)
    planes = planes_from_pair_map(pair_to_line, 1:15)
    records = Vector{Dict{String,Any}}()
    for plane in planes
        plane_set = Set(plane)
        plane_lines = [line for line in lines if issubset(Set(line), plane_set)]
        witness = alternative_witness(table, plane)
        push!(records, Dict(
            "plane" => plane,
            "line_count_inside" => length(plane_lines),
            "closed" => true,
            "alternative" => witness === nothing,
            "classification" => witness === nothing ? "genuine_octonion_subalgebra" : "closed_non_alternative_sedenion_plane",
            "witness" => witness,
        ))
    end
    Dict(
        "plane_count" => length(records),
        "genuine_octonion_count" => count(row -> row["classification"] == "genuine_octonion_subalgebra", records),
        "non_alternative_count" => count(row -> row["classification"] != "genuine_octonion_subalgebra", records),
        "records" => records,
    )
end

function two_term(dim::Int, a::Int, b::Int)
    v = zeros(Int, dim)
    v[a + 1] = 1
    v[b + 1] = 1
    v
end

function support_geometry(ab, cd, pair_to_line, planes)
    support = Set(vcat(collect(ab), collect(cd)))
    containing = [plane for plane in planes if issubset(support, Set(plane))]
    Dict(
        "left_pair" => collect(ab),
        "right_pair" => collect(cd),
        "left_line" => collect(pair_to_line[Tuple(sort(collect(ab)))]),
        "right_line" => collect(pair_to_line[Tuple(sort(collect(cd)))]),
        "support_points" => sort(collect(support)),
        "containing_planes" => containing,
    )
end

function zero_divisors(table, pair_to_line, planes)
    pairs = [(a, b) for a in 1:15 for b in (a + 1):15]
    adjacency = Dict(pair => Set{Tuple{Int,Int}}() for pair in pairs)
    ordered = 0
    examples = Vector{Dict{String,Any}}()
    for ab in pairs, cd in pairs
        prod = multiply_table(table, two_term(16, ab[1], ab[2]), two_term(16, cd[1], cd[2]))
        if normsq(prod) == 0
            ordered += 1
            push!(adjacency[ab], cd)
            push!(adjacency[cd], ab)
            if length(examples) < 12
                geom = support_geometry(ab, cd, pair_to_line, planes)
                geom["product_terms"] = vector_terms(prod)
                push!(examples, geom)
            end
        end
    end
    seen = Set{Tuple{Int,Int}}()
    components = Vector{Vector{Tuple{Int,Int}}}()
    for node in pairs
        node in seen && continue
        stack = [node]
        push!(seen, node)
        comp = Tuple{Int,Int}[]
        while !isempty(stack)
            item = pop!(stack)
            push!(comp, item)
            for nxt in adjacency[item]
                if !(nxt in seen)
                    push!(seen, nxt)
                    push!(stack, nxt)
                end
            end
        end
        length(comp) > 1 && push!(components, sort(comp))
    end
    Dict(
        "ordered_zero_divisor_pair_count" => ordered,
        "undirected_zero_divisor_edge_count" => length(Set(Tuple(sort([ab, cd])) for ab in pairs for cd in adjacency[ab])),
        "component_count" => length(components),
        "component_sizes" => sort([length(comp) for comp in components]),
        "components" => [[collect(pair) for pair in comp] for comp in components],
        "examples" => examples,
    )
end

function octonion_control(table)
    lines, _ = extract_lines(table, 1:7)
    zero_count = 0
    pairs = [(a, b) for a in 1:7 for b in (a + 1):7]
    for ab in pairs, cd in pairs
        zero_count += normsq(multiply_table(table, two_term(8, ab[1], ab[2]), two_term(8, cd[1], cd[2]))) == 0 ? 1 : 0
    end
    axiom = pair_axiom(lines, 1:7)
    Dict(
        "line_count" => length(lines),
        "lines" => [collect(line) for line in lines],
        "pair_axiom" => axiom,
        "ordered_zero_divisor_pair_count" => zero_count,
        "all_pass" => length(lines) == 7 && axiom["all_pairs_exactly_one_line"] && zero_count == 0,
    )
end

function signed_entry_scramble_control(table)
    scrambled = copy(table)
    prod12 = multiply_table(table, basis(16, 1), basis(16, 2))
    prod14 = multiply_table(table, basis(16, 1), basis(16, 4))
    scrambled[:, 2, 3] = prod14
    scrambled[:, 3, 2] = -prod14
    scrambled[:, 2, 5] = prod12
    scrambled[:, 5, 2] = -prod12
    lines, _ = extract_lines(scrambled, 1:15)
    axiom = pair_axiom(lines, 1:15)
    sign_flip = copy(table)
    sign_flip[:, 2, 3] = -prod12
    sign_flip[:, 3, 2] = prod12
    sign_lines, _ = extract_lines(sign_flip, 1:15)
    Dict(
        "control_note" => "Pure in-place sign flips preserve e_i e_j = +/- e_k incidence; the breaking control scrambles signed product entries across pair slots.",
        "pure_sign_flip_line_count" => length(sign_lines),
        "pure_sign_flip_pair_axiom_ok" => pair_axiom(sign_lines, 1:15)["all_pairs_exactly_one_line"],
        "signed_entry_scramble_line_count" => length(lines),
        "signed_entry_scramble_pair_axiom_ok" => axiom["all_pairs_exactly_one_line"],
        "first_pair_violations" => axiom["violations"][1:min(end, 8)],
        "breaks" => length(lines) != 35 || !axiom["all_pairs_exactly_one_line"],
    )
end

function zadd(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function zmul(ctx, args::Vector{Z3.Expr})
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function znot(e::Z3.Expr)
    Z3.Not(e)
end

function z3_line_claim(table, a::Int, b::Int, c::Int; assert_line::Bool)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    coeffs = [Z3.IntVar("C_$(k - 1)_$(a)_$(b)_$(c)_$(assert_line)", ctx) for k in 1:16]
    for k in 1:16
        Z3.add(solver, coeffs[k] == Z3.IntVal(table[k, a + 1, b + 1], ctx))
    end
    pieces = Z3.Expr[zmul(ctx, [coeffs[c + 1], coeffs[c + 1]]) == Z3.IntVal(1, ctx)]
    for k in 0:15
        k == c && continue
        push!(pieces, coeffs[k + 1] == Z3.IntVal(0, ctx))
    end
    line_expr = Z3.And(pieces)
    Z3.add(solver, assert_line ? line_expr : znot(line_expr))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "bound_entry" => "C[*][$a][$b]",
        "target" => c,
        "asserted" => assert_line ? "line_closure" : "not_line_closure",
        "verdict" => string(Z3.check(solver)),
    )
end

function z3_zero_product(table, left_pair, right_pair)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    left = [Z3.IntVar("L_$(i - 1)", ctx) for i in 1:16]
    right = [Z3.IntVar("R_$(i - 1)", ctx) for i in 1:16]
    for idx0 in 0:15
        Z3.add(solver, left[idx0 + 1] == Z3.IntVal(idx0 in left_pair ? 1 : 0, ctx))
        Z3.add(solver, right[idx0 + 1] == Z3.IntVal(idx0 in right_pair ? 1 : 0, ctx))
    end
    for k in 1:16
        terms = Z3.Expr[]
        for i in 1:16, j in 1:16
            coeff = table[k, i, j]
            if coeff != 0
                push!(terms, zmul(ctx, [Z3.IntVal(coeff, ctx), left[i], right[j]]))
            end
        end
        Z3.add(solver, zadd(ctx, terms) == Z3.IntVal(0, ctx))
    end
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "product_derived_in_solver" => true,
        "left_pair" => collect(left_pair),
        "right_pair" => collect(right_pair),
        "verdict" => string(Z3.check(solver)),
    )
end

function smt_suite(table, zero_example)
    claimed_line = (1, 2, product_index_and_sign(table, 1, 2)[1])
    claimed_non_line = (1, 2, 4)
    Dict(
        "claimed_line" => collect(claimed_line),
        "claimed_non_line" => collect(claimed_non_line),
        "julia_z3" => Dict(
            "claimed_line_sat" => z3_line_claim(table, claimed_line...; assert_line=true),
            "claimed_line_negation_unsat" => z3_line_claim(table, claimed_line...; assert_line=false),
            "claimed_non_line_unsat" => z3_line_claim(table, claimed_non_line...; assert_line=true),
            "claimed_non_line_negation_sat" => z3_line_claim(table, claimed_non_line...; assert_line=false),
            "zero_product" => z3_zero_product(table, Tuple(zero_example["left_pair"]), Tuple(zero_example["right_pair"])),
        ),
    )
end

function main()
    mkpath(dirname(RESULT_PATH))
    s_table = sedenion_table()
    o_table = octonion_table()
    lines, pair_to_line = extract_lines(s_table, 1:15)
    axiom = pair_axiom(lines, 1:15)
    planes = planes_from_pair_map(pair_to_line, 1:15)
    plane_summary = plane_classification(s_table, lines, pair_to_line)
    zd = zero_divisors(s_table, pair_to_line, planes)
    controls = Dict(
        "octonion_restriction" => octonion_control(o_table),
        "signed_entry_scramble" => signed_entry_scramble_control(s_table),
    )
    smt = smt_suite(s_table, zd["examples"][1])
    shared_scalars = Dict(
        "line_count" => length(lines),
        "pair_axiom_ok" => axiom["all_pairs_exactly_one_line"] ? 1 : 0,
        "plane_count" => plane_summary["plane_count"],
        "genuine_octonion_plane_count" => plane_summary["genuine_octonion_count"],
        "non_alternative_plane_count" => plane_summary["non_alternative_count"],
        "ordered_zero_divisor_pair_count" => zd["ordered_zero_divisor_pair_count"],
        "zero_divisor_component_count" => zd["component_count"],
        "octonion_line_count" => controls["octonion_restriction"]["line_count"],
        "octonion_zero_divisor_pair_count" => controls["octonion_restriction"]["ordered_zero_divisor_pair_count"],
        "scrambled_breaks_pair_axiom" => controls["signed_entry_scramble"]["breaks"] ? 1 : 0,
    )
    jz3 = smt["julia_z3"]
    all_pass = (
        length(lines) == 35 &&
        axiom["all_pairs_exactly_one_line"] &&
        plane_summary["plane_count"] == 15 &&
        plane_summary["genuine_octonion_count"] == 8 &&
        plane_summary["non_alternative_count"] == 7 &&
        zd["ordered_zero_divisor_pair_count"] == 84 &&
        zd["component_count"] == 7 &&
        controls["octonion_restriction"]["all_pass"] &&
        controls["signed_entry_scramble"]["breaks"] &&
        jz3["claimed_line_sat"]["verdict"] == "sat" &&
        jz3["claimed_line_negation_unsat"]["verdict"] == "unsat" &&
        jz3["claimed_non_line_unsat"]["verdict"] == "unsat" &&
        jz3["claimed_non_line_negation_sat"]["verdict"] == "sat" &&
        jz3["zero_product"]["verdict"] == "sat"
    )
    payload = Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_julia",
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS")) * "Z",
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "packages_used" => ["Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "TOOL_MANIFEST" => Dict(
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT derivation of line/non-line and zero-product facts from bound structure constants"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Z3" => "load_bearing", "JSON" => "supportive"),
        "construction" => Dict(
            "octonion_source" => "canonical oriented octonion table",
            "octonion_triples" => [[a, b, c] for (a, b, c) in OCTONION_TRIPLES],
            "sedenion_rule" => "(a,b)(c,d)=(ac-conj(d)b, da+b conj(c))",
            "line_extraction" => "all triples {i,j,k} with e_i e_j = +/- e_k, derived from table products",
        ),
        "incidence" => Dict("points" => collect(1:15), "line_count" => length(lines), "lines" => [collect(line) for line in lines], "pair_axiom" => axiom),
        "planes" => plane_summary,
        "zero_divisors" => zd,
        "controls" => controls,
        "smt" => smt,
        "shared_scalars" => shared_scalars,
        "all_pass" => all_pass,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        println(io)
    end
    println("wrote: $RESULT_PATH")
    println(
        "SCOUT_DONE all_pass=$(all_pass) lines=$(length(lines)) pair_axiom=$(axiom["all_pairs_exactly_one_line"]) " *
        "planes=$(plane_summary["genuine_octonion_count"])/$(plane_summary["non_alternative_count"]) " *
        "zero_pairs=$(zd["ordered_zero_divisor_pair_count"]) components=$(zd["component_count"]) " *
        "julia_z3_line_flip=$(jz3["claimed_line_negation_unsat"]["verdict"])"
    )
    return all_pass ? 0 : 1
end

exit(main())
