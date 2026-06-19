#!/usr/bin/env julia
# object_id: sedenion_break_prelim
# classification: scratch_diagnostic
# promotion_allowed: false
# claim_ceiling: PRELIM finite Cayley-Dickson S diagnostic only. This
# reproduces known Hurwitz math as a finite witness and makes no forcing,
# basin, admission, engine, bridge, Axis0, or manifold claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "sedenion_break_prelim"
const RESULT_PATH = joinpath(@__DIR__, "sedenion_break_prelim_julia_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const NORM_PROBE_COUNT = 64
const STRUCTURE_PROBE_COUNT = 16
const ZERO_WITNESS_LIMIT = 8

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function quaternion_table()
    table = zeros(Float64, 4, 4, 4)
    add_identity!(table, 4)
    for a in 1:3
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in [(1, 2, 3)]
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function prior_octonion_table()
    table = zeros(Float64, 8, 8, 8)
    add_identity!(table, 8)
    for a in 1:7
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function basis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function conjugate(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function cayley_dickson_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2n)]
    c = y[1:n]
    d = y[(n + 1):(2n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate(c))
    vcat(first, second)
end

function cayley_dickson_double(parent::Array{Float64,3})
    n = size(parent, 1)
    table = zeros(Float64, 2n, 2n, 2n)
    for i in 1:(2n), j in 1:(2n)
        x = zeros(Float64, 2n)
        y = zeros(Float64, 2n)
        x[i] = 1.0
        y[j] = 1.0
        table[:, i, j] .= cayley_dickson_multiply(parent, x, y)
    end
    table
end

function associator(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function probe_vector(dim::Int, sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 +
                   (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0) for j in 1:dim]
end

function probe_family(dim::Int)
    vectors = [basis(dim, a) for a in 0:(dim - 1)]
    for sample_idx in 1:STRUCTURE_PROBE_COUNT
        push!(vectors, probe_vector(dim, sample_idx, 7))
    end
    vectors
end

function table_checksum(table::Array{Float64,3})
    dim = size(table, 1)
    checksum = 0.0
    nonzero = 0
    abs_sum = 0.0
    for c in 1:dim, a in 1:dim, b in 1:dim
        value = table[c, a, b]
        if abs(value) > 0.0
            nonzero += 1
            abs_sum += abs(value)
            checksum += value * (1_000_003.0 * c + 1_009.0 * a + b)
        end
    end
    Dict{String,Any}(
        "dim" => dim,
        "nonzero_entry_count" => nonzero,
        "sum_abs_entries" => abs_sum,
        "weighted_checksum" => checksum,
    )
end

function terms_from_vector(v::AbstractVector{Float64})
    terms = Vector{Dict{String,Any}}()
    for idx in 0:(length(v) - 1)
        value = v[idx + 1]
        if abs(value) > TOL
            push!(terms, Dict{String,Any}("basis_index" => idx, "coefficient" => value, "label" => "e$idx"))
        end
    end
    terms
end

function pair_vector(dim::Int, i::Int, j::Int; si::Float64 = 1.0, sj::Float64 = 1.0)
    v = zeros(Float64, dim)
    v[i + 1] = si
    v[j + 1] = sj
    v
end

function pure_imaginary_pairs(dim::Int)
    [(i, j) for i in 1:(dim - 1) for j in (i + 1):(dim - 1)]
end

function zero_witness_dict(kind::String, left::AbstractVector{Float64}, right::AbstractVector{Float64}, product::AbstractVector{Float64})
    Dict{String,Any}(
        "kind" => kind,
        "left_terms" => terms_from_vector(left),
        "right_terms" => terms_from_vector(right),
        "product_terms" => terms_from_vector(product),
        "left_norm" => norm(left),
        "right_norm" => norm(right),
        "product_norm" => norm(product),
    )
end

function zero_divisor_search(table::Array{Float64,3})
    dim = size(table, 1)
    pairs = pure_imaginary_pairs(dim)
    plus_count = 0
    signed_count = 0
    plus_first = nothing
    signed_first = nothing
    plus_examples = Vector{Dict{String,Any}}()
    signed_examples = Vector{Dict{String,Any}}()
    min_plus_product_norm = Inf
    min_signed_product_norm = Inf

    for (i, j) in pairs, (k, l) in pairs
        left = pair_vector(dim, i, j)
        right = pair_vector(dim, k, l)
        product = multiply(table, left, right)
        product_norm = norm(product)
        min_plus_product_norm = min(min_plus_product_norm, product_norm)
        if product_norm < TOL && norm(left) > TOL && norm(right) > TOL
            plus_count += 1
            witness = zero_witness_dict("plus_two_term_pure_imaginary_pair", left, right, product)
            witness["pair_indices"] = Dict("left" => [i, j], "right" => [k, l])
            if plus_first === nothing
                plus_first = witness
            end
            if length(plus_examples) < ZERO_WITNESS_LIMIT
                push!(plus_examples, witness)
            end
        end

        for si in (-1.0, 1.0), sj in (-1.0, 1.0), sk in (-1.0, 1.0), sl in (-1.0, 1.0)
            left_signed = pair_vector(dim, i, j; si = si, sj = sj)
            right_signed = pair_vector(dim, k, l; si = sk, sj = sl)
            signed_product = multiply(table, left_signed, right_signed)
            signed_product_norm = norm(signed_product)
            min_signed_product_norm = min(min_signed_product_norm, signed_product_norm)
            if signed_product_norm < TOL && norm(left_signed) > TOL && norm(right_signed) > TOL
                signed_count += 1
                witness = zero_witness_dict("signed_two_term_pure_imaginary_pair", left_signed, right_signed, signed_product)
                witness["pair_indices"] = Dict("left" => [i, j], "right" => [k, l])
                if signed_first === nothing
                    signed_first = witness
                end
                if length(signed_examples) < ZERO_WITNESS_LIMIT
                    push!(signed_examples, witness)
                end
            end
        end
    end

    Dict{String,Any}(
        "search_kind" => "pure_imaginary_two_basis_term_pairs",
        "basis_index_range" => [1, dim - 1],
        "ordered_plus_pair_search_size" => length(pairs)^2,
        "ordered_signed_pair_search_size" => length(pairs)^2 * 16,
        "plus_zero_divisor_count" => plus_count,
        "signed_zero_divisor_count" => signed_count,
        "min_plus_product_norm_seen" => min_plus_product_norm,
        "min_signed_product_norm_seen" => min_signed_product_norm,
        "plus_first_witness" => plus_first,
        "signed_first_witness" => signed_first,
        "plus_examples" => plus_examples,
        "signed_examples" => signed_examples,
        "zero_divisors_exist" => plus_first !== nothing || signed_first !== nothing,
    )
end

function structure_checks(table::Array{Float64,3}, zero_search::Dict{String,Any})
    dim = size(table, 1)
    vectors = probe_family(dim)
    max_alternative = 0.0
    max_alternative_witness = Dict{String,Any}("kind" => "none")
    max_power = 0.0
    max_power_witness = Dict{String,Any}("kind" => "none")
    max_flexible = 0.0
    max_flexible_witness = Dict{String,Any}("kind" => "none")
    max_norm_residual = 0.0
    max_norm_witness = Dict{String,Any}("kind" => "none")

    for sample_idx in 1:NORM_PROBE_COUNT
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = abs(norm(multiply(table, x, y)) - norm(x) * norm(y))
        if residual > max_norm_residual
            max_norm_residual = residual
            max_norm_witness = Dict{String,Any}("kind" => "deterministic_pseudorandom_pair", "sample_idx" => sample_idx, "residual" => residual)
        end
    end

    if zero_search["plus_first_witness"] !== nothing
        witness = zero_search["plus_first_witness"]
        residual = abs(witness["product_norm"] - witness["left_norm"] * witness["right_norm"])
        if residual > max_norm_residual
            max_norm_residual = residual
            max_norm_witness = merge(copy(witness), Dict{String,Any}("norm_multiplicative_residual" => residual))
        end
    end

    for (ix, x) in enumerate(vectors)
        x2 = multiply(table, x, x)
        power_residual = norm(multiply(table, x, multiply(table, x, x2)) - multiply(table, x2, x2))
        if power_residual > max_power
            max_power = power_residual
            max_power_witness = Dict{String,Any}("probe_index" => ix, "residual" => power_residual)
        end
        for (iy, y) in enumerate(vectors)
            alternative_residual = norm(associator(table, x, x, y))
            if alternative_residual > max_alternative
                max_alternative = alternative_residual
                max_alternative_witness = Dict{String,Any}("x_probe_index" => ix, "y_probe_index" => iy, "residual" => alternative_residual)
            end
            flexible_residual = norm(multiply(table, x, multiply(table, y, x)) - multiply(table, multiply(table, x, y), x))
            if flexible_residual > max_flexible
                max_flexible = flexible_residual
                max_flexible_witness = Dict{String,Any}("a_probe_index" => ix, "b_probe_index" => iy, "residual" => flexible_residual)
            end
        end
    end

    Dict{String,Any}(
        "probe_count" => length(vectors),
        "probe_kind" => "basis_vectors_plus_deterministic_pseudorandom_vectors",
        "max_norm_mult_residual" => max_norm_residual,
        "norm_multiplicative_holds_in_probe" => max_norm_residual < TOL,
        "norm_multiplicative_fail_witness" => max_norm_witness,
        "max_associator_xxy" => max_alternative,
        "alternative_holds" => max_alternative < TOL,
        "alternative_witness" => max_alternative_witness,
        "max_power_four_residual" => max_power,
        "power_associative_holds" => max_power < TOL,
        "power_associative_witness" => max_power_witness,
        "max_flexible_residual" => max_flexible,
        "flexible_holds" => max_flexible < TOL,
        "flexible_witness" => max_flexible_witness,
    )
end

function build_shared_scalars(table_checks::Dict{String,Any}, o_checks::Dict{String,Any}, s_checks::Dict{String,Any}, o_zero::Dict{String,Any}, s_zero::Dict{String,Any})
    Dict{String,Any}(
        "tables.O_cd_vs_prior_max_abs_diff" => table_checks["octonion_cd_vs_prior_max_abs_diff"],
        "tables.O_cd.weighted_checksum" => table_checks["O_cd"]["weighted_checksum"],
        "tables.O_cd.nonzero_entry_count" => table_checks["O_cd"]["nonzero_entry_count"],
        "tables.S.weighted_checksum" => table_checks["S"]["weighted_checksum"],
        "tables.S.nonzero_entry_count" => table_checks["S"]["nonzero_entry_count"],
        "O.dim" => 8,
        "S.dim" => 16,
        "O.zero.plus_zero_divisor_count" => o_zero["plus_zero_divisor_count"],
        "S.zero.plus_zero_divisor_count" => s_zero["plus_zero_divisor_count"],
        "S.zero.signed_zero_divisor_count" => s_zero["signed_zero_divisor_count"],
        "O.max_norm_mult_residual" => o_checks["max_norm_mult_residual"],
        "S.max_norm_mult_residual" => s_checks["max_norm_mult_residual"],
        "O.max_associator_xxy" => o_checks["max_associator_xxy"],
        "S.max_associator_xxy" => s_checks["max_associator_xxy"],
        "S.max_power_four_residual" => s_checks["max_power_four_residual"],
        "S.max_flexible_residual" => s_checks["max_flexible_residual"],
    )
end

function build_shared_booleans(o_checks::Dict{String,Any}, s_checks::Dict{String,Any}, o_zero::Dict{String,Any}, s_zero::Dict{String,Any}, verdicts::Dict{String,Any})
    Dict{String,Any}(
        "O.zero_divisors_in_search" => o_zero["zero_divisors_exist"],
        "S.zero_divisors_in_search" => s_zero["zero_divisors_exist"],
        "O.norm_multiplicative_holds_in_probe" => o_checks["norm_multiplicative_holds_in_probe"],
        "S.norm_multiplicative_holds_in_probe" => s_checks["norm_multiplicative_holds_in_probe"],
        "O.alternative_holds" => o_checks["alternative_holds"],
        "S.alternative_holds" => s_checks["alternative_holds"],
        "S.power_associative_holds" => s_checks["power_associative_holds"],
        "S.flexible_holds" => s_checks["flexible_holds"],
        "sedenion_is_normed_division" => verdicts["sedenion_is_normed_division"],
        "sedenion_zero_divisors" => verdicts["sedenion_zero_divisors"],
        "ladder_stops_at_O" => verdicts["ladder_stops_at_O"],
    )
end

function build_result()
    h_table = quaternion_table()
    o_cd = cayley_dickson_double(h_table)
    o_prior = prior_octonion_table()
    s_table = cayley_dickson_double(o_cd)
    octonion_cd_diff = maximum(abs.(o_cd .- o_prior))

    o_zero = zero_divisor_search(o_cd)
    s_zero = zero_divisor_search(s_table)
    o_checks = structure_checks(o_cd, o_zero)
    s_checks = structure_checks(s_table, s_zero)

    o_normed_division_alt = !o_zero["zero_divisors_exist"] &&
                            o_checks["norm_multiplicative_holds_in_probe"] &&
                            o_checks["alternative_holds"]
    s_normed_division = !s_zero["zero_divisors_exist"] &&
                        s_checks["norm_multiplicative_holds_in_probe"]
    verdicts = Dict{String,Any}(
        "sedenion_is_normed_division" => s_normed_division,
        "sedenion_zero_divisors" => s_zero["zero_divisors_exist"],
        "ladder_stops_at_O" => o_normed_division_alt && !s_normed_division && s_zero["zero_divisors_exist"] && !s_checks["alternative_holds"],
    )

    table_checks = Dict{String,Any}(
        "H" => table_checksum(h_table),
        "O_cd" => table_checksum(o_cd),
        "S" => table_checksum(s_table),
        "octonion_cd_vs_prior_max_abs_diff" => octonion_cd_diff,
        "octonion_cd_matches_prior_table" => octonion_cd_diff < TOL,
    )
    shared_scalars = build_shared_scalars(table_checks, o_checks, s_checks, o_zero, s_zero)
    shared_booleans = build_shared_booleans(o_checks, s_checks, o_zero, s_zero, verdicts)

    stop_reasons = String[]
    if octonion_cd_diff > STRICT_STOP_TOL
        push!(stop_reasons, "O-level Cayley-Dickson construction disagrees with prior octonion table.")
    end
    if o_zero["zero_divisors_exist"]
        push!(stop_reasons, "O-level control found zero divisors; multiplication is miswired.")
    end
    if !s_zero["zero_divisors_exist"]
        push!(stop_reasons, "No concrete S zero divisor found in the bounded search set.")
    end

    contrast = [
        Dict{String,Any}(
            "algebra" => "O",
            "dim" => 8,
            "zero_divisors_in_search" => o_zero["zero_divisors_exist"],
            "max_norm_mult_residual" => o_checks["max_norm_mult_residual"],
            "alternative_holds" => o_checks["alternative_holds"],
            "max_associator_xxy" => o_checks["max_associator_xxy"],
            "normed_division_control" => o_normed_division_alt,
        ),
        Dict{String,Any}(
            "algebra" => "S",
            "dim" => 16,
            "zero_divisors_in_search" => s_zero["zero_divisors_exist"],
            "max_norm_mult_residual" => s_checks["max_norm_mult_residual"],
            "alternative_holds" => s_checks["alternative_holds"],
            "max_associator_xxy" => s_checks["max_associator_xxy"],
            "normed_division_control" => s_normed_division,
        ),
    ]

    plain = verdicts["ladder_stops_at_O"] ?
        "At scratch_diagnostic ceiling, the normed-division ladder stops at O; S is a non-division Cayley-Dickson algebra with zero divisors, non-multiplicative norm, failed alternativity, and finite-probe power-associative/flexible behavior." :
        "At scratch_diagnostic ceiling, the O/S break did not pass all controls; inspect stop reasons and bounded search coverage."

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_reference",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "question" => "Where does the Cayley-Dickson normed-division carrier ladder break one rung past octonions?",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "PRELIM finite Cayley-Dickson S diagnostic only; no forcing proof, basin, admission, engine, bridge, Axis0, or manifold closure claim",
        "sim_execution_kind" => "classical",
        "sim_class" => "carrier_break_control",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "norm_probe_count" => NORM_PROBE_COUNT,
        "structure_probe_count" => STRUCTURE_PROBE_COUNT,
        "construction" => Dict{String,Any}(
            "formula" => "(a,b)(c,d) = (ac - conj(d)b, da + b conj(c))",
            "basis_order" => "Cayley-Dickson doubling appends the new component after the parent component; indices are zero-based e0..e15.",
            "octonion_control" => table_checks,
        ),
        "tool_manifest" => Dict{String,Any}(
            "julia" => "load_bearing finite table construction and scalar probes",
            "LinearAlgebra" => "supportive norms for residuals and witnesses",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "julia" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON" => "supportive",
        ),
        "divergence_log" => [
            "O control: no zero divisors in bounded two-term search, norm multiplicativity residual near machine epsilon, alternative residual near machine epsilon.",
            "S break: concrete zero divisors found, norm multiplicativity fails, alternativity fails.",
        ],
        "fences" => [
            "This reproduces Hurwitz known math as a finite witness, not a new claim.",
            "S is excluded as a normed-division carrier: no conserved norm means no probability readout, and zero divisors mean no clean inverse.",
            "The zero-divisor structure of S is a candidate separate object for annihilation/interference-style diagnostics, not promoted here.",
            "scratch_diagnostic only, promotion_allowed=false, no engine, Axis0, bridge, basin, forcing, admission, or manifold claim.",
            "The 64=2^6 Cayley-Dickson-vs-engine resonance is not asserted as identity.",
        ],
        "zero_divisor_search" => Dict{String,Any}("O" => o_zero, "S" => s_zero),
        "checks" => Dict{String,Any}("O" => o_checks, "S" => s_checks),
        "contrast" => contrast,
        "verdicts" => verdicts,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "control_status" => Dict{String,Any}(
            "octonion_cd_matches_prior_table" => octonion_cd_diff < TOL,
            "O_zero_divisor_control_ok" => !o_zero["zero_divisors_exist"],
            "S_zero_divisor_witness_found" => s_zero["zero_divisors_exist"],
            "control_miswired" => octonion_cd_diff > STRICT_STOP_TOL || o_zero["zero_divisors_exist"],
        ),
        "stop_condition_fired" => !isempty(stop_reasons),
        "stop_reasons" => stop_reasons,
        "plain_sentence" => plain,
    )
end

function print_summary(result::Dict{String,Any})
    println("Sedenion break prelim - Julia reference")
    println("classification: ", result["classification"], " | promotion_allowed: ", result["promotion_allowed"])
    z = result["zero_divisor_search"]["S"]
    println("S zero_divisors_exist=", z["zero_divisors_exist"],
        " plus_count=", z["plus_zero_divisor_count"],
        " signed_count=", z["signed_zero_divisor_count"],
        " first_plus_product_norm=", z["plus_first_witness"] === nothing ? "none" : z["plus_first_witness"]["product_norm"])
    for row in result["contrast"]
        println(row["algebra"],
            ": dim=", row["dim"],
            " zero_divisors_in_search=", row["zero_divisors_in_search"],
            " max_norm_mult_residual=", row["max_norm_mult_residual"],
            " alternative_holds=", row["alternative_holds"],
            " max_associator_xxy=", row["max_associator_xxy"],
            " normed_division_control=", row["normed_division_control"])
    end
    s_checks = result["checks"]["S"]
    println("S power_associative_holds=", s_checks["power_associative_holds"],
        " max_power_four_residual=", s_checks["max_power_four_residual"],
        " flexible_holds=", s_checks["flexible_holds"],
        " max_flexible_residual=", s_checks["max_flexible_residual"])
    println("verdicts=", JSON.json(result["verdicts"]))
    println(result["plain_sentence"])
    println("wrote: ", result["result_path"])
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if result["stop_condition_fired"]
    println("STOP: ", join(result["stop_reasons"], " | "))
    exit(2)
end
