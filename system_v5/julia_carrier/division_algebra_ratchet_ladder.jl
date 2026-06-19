#!/usr/bin/env julia
# object_id: division_algebra_ratchet_ladder
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite division-algebra/Hopf-ladder witness only. No basin,
# admission, engine, Axis0, bridge, gravity, or manifold-closure claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "division_algebra_ratchet_ladder"
const RESULT_PATH = joinpath(@__DIR__, "division_algebra_ratchet_ladder_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "division_algebra_ratchet_ladder_jax_results.json")
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

function real_table()
    table = zeros(Float64, 1, 1, 1)
    setprod!(table, 0, 0, 0, 1.0)
    table
end

function complex_table()
    table = zeros(Float64, 2, 2, 2)
    add_identity!(table, 2)
    setprod!(table, 1, 1, 0, -1.0)
    table
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

function octonion_table()
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

function conjugate_cd(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function cayley_dickson_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_cd(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_cd(c))
    vcat(first, second)
end

function cayley_dickson_double(parent::Array{Float64,3})
    n = size(parent, 1)
    table = zeros(Float64, 2 * n, 2 * n, 2 * n)
    for i in 1:(2 * n), j in 1:(2 * n)
        x = zeros(Float64, 2 * n)
        y = zeros(Float64, 2 * n)
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

function commutator_max(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1)
        max_seen = max(max_seen, norm(multiply(table, basis(dim, a), basis(dim, b)) -
                                      multiply(table, basis(dim, b), basis(dim, a))))
    end
    max_seen
end

function associator_max(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        max_seen = max(max_seen, norm(associator(table, basis(dim, a), basis(dim, b), basis(dim, c))))
    end
    max_seen
end

function alternator_residual(table::Array{Float64,3})
    vectors = probe_family(size(table, 1))
    max_xxy = 0.0
    max_xyy = 0.0
    xxy_witness = Dict{String,Any}("kind" => "none")
    xyy_witness = Dict{String,Any}("kind" => "none")
    for (ix, x) in enumerate(vectors), (iy, y) in enumerate(vectors)
        xxy = norm(associator(table, x, x, y))
        if xxy > max_xxy
            max_xxy = xxy
            xxy_witness = Dict{String,Any}("x_probe_index" => ix, "y_probe_index" => iy, "residual" => xxy)
        end
        xyy = norm(associator(table, x, y, y))
        if xyy > max_xyy
            max_xyy = xyy
            xyy_witness = Dict{String,Any}("x_probe_index" => ix, "y_probe_index" => iy, "residual" => xyy)
        end
    end
    max(max_xxy, max_xyy), max_xxy, max_xyy, xxy_witness, xyy_witness, length(vectors)
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

function pair_vector(dim::Int, i::Int, j::Int; si::Float64 = 1.0, sj::Float64 = 1.0)
    v = zeros(Float64, dim)
    v[i + 1] = si
    v[j + 1] = sj
    v
end

function pure_imaginary_pairs(dim::Int)
    [(i, j) for i in 1:(dim - 1) for j in (i + 1):(dim - 1)]
end

function zero_divisor_search(table::Array{Float64,3})
    dim = size(table, 1)
    min_product_norm = Inf
    first_witness = nothing
    basis_zero_count = 0
    probe_zero_count = 0
    signed_zero_count = 0
    examples = Vector{Dict{String,Any}}()

    for a in 0:(dim - 1), b in 0:(dim - 1)
        left = basis(dim, a)
        right = basis(dim, b)
        product = multiply(table, left, right)
        product_norm = norm(product)
        min_product_norm = min(min_product_norm, product_norm)
        if product_norm < TOL && norm(left) > TOL && norm(right) > TOL
            basis_zero_count += 1
            witness = zero_witness_dict("basis_pair", left, right, product)
            witness["pair_indices"] = Dict("left" => [a], "right" => [b])
            first_witness === nothing && (first_witness = witness)
            length(examples) < ZERO_WITNESS_LIMIT && push!(examples, witness)
        end
    end

    for sample_idx in 1:NORM_PROBE_COUNT
        left = probe_vector(dim, sample_idx, 1)
        right = probe_vector(dim, sample_idx, 2)
        product = multiply(table, left, right)
        product_norm = norm(product)
        min_product_norm = min(min_product_norm, product_norm)
        if product_norm < TOL && norm(left) > TOL && norm(right) > TOL
            probe_zero_count += 1
            witness = zero_witness_dict("deterministic_probe_pair", left, right, product)
            witness["sample_idx"] = sample_idx
            first_witness === nothing && (first_witness = witness)
            length(examples) < ZERO_WITNESS_LIMIT && push!(examples, witness)
        end
    end

    pairs = pure_imaginary_pairs(dim)
    for (i, j) in pairs, (k, l) in pairs
        for si in (-1.0, 1.0), sj in (-1.0, 1.0), sk in (-1.0, 1.0), sl in (-1.0, 1.0)
            left = pair_vector(dim, i, j; si = si, sj = sj)
            right = pair_vector(dim, k, l; si = sk, sj = sl)
            product = multiply(table, left, right)
            product_norm = norm(product)
            min_product_norm = min(min_product_norm, product_norm)
            if product_norm < TOL && norm(left) > TOL && norm(right) > TOL
                signed_zero_count += 1
                witness = zero_witness_dict("signed_two_term_pure_imaginary_pair", left, right, product)
                witness["pair_indices"] = Dict("left" => [i, j], "right" => [k, l])
                first_witness === nothing && (first_witness = witness)
                length(examples) < ZERO_WITNESS_LIMIT && push!(examples, witness)
            end
        end
    end

    Dict{String,Any}(
        "search_kind" => "basis_pairs_plus_probe_pairs_plus_signed_two_term_pure_imaginary_pairs",
        "basis_pair_search_size" => dim * dim,
        "probe_pair_search_size" => NORM_PROBE_COUNT,
        "signed_pair_search_size" => length(pairs)^2 * 16,
        "basis_zero_divisor_count" => basis_zero_count,
        "probe_zero_divisor_count" => probe_zero_count,
        "signed_zero_divisor_count" => signed_zero_count,
        "min_product_norm_seen" => min_product_norm,
        "zero_divisors_exist" => first_witness !== nothing,
        "first_witness" => first_witness,
        "examples" => examples,
    )
end

function norm_mult_residual(table::Array{Float64,3}, zero_search::Dict{String,Any})
    dim = size(table, 1)
    max_seen = 0.0
    witness = Dict{String,Any}("kind" => "none")
    for sample_idx in 1:NORM_PROBE_COUNT
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = abs(norm(multiply(table, x, y)) - norm(x) * norm(y))
        if residual > max_seen
            max_seen = residual
            witness = Dict{String,Any}("kind" => "deterministic_probe_pair", "sample_idx" => sample_idx, "residual" => residual)
        end
    end
    if zero_search["first_witness"] !== nothing
        zw = zero_search["first_witness"]
        residual = abs(zw["product_norm"] - zw["left_norm"] * zw["right_norm"])
        if residual > max_seen
            max_seen = residual
            witness = merge(copy(zw), Dict{String,Any}("norm_multiplicative_residual" => residual))
        end
    end
    max_seen, witness
end

function analyze_algebra(symbol::String, label::String, table::Array{Float64,3})
    zero_search = zero_divisor_search(table)
    norm_resid, norm_witness = norm_mult_residual(table, zero_search)
    alt_resid, alt_xxy, alt_xyy, alt_xxy_witness, alt_xyy_witness, alt_probe_count = alternator_residual(table)
    comm = commutator_max(table)
    assoc = associator_max(table)
    commutative = comm < TOL
    associative = assoc < TOL
    alternative = alt_resid < TOL
    normed_division = norm_resid < TOL && !zero_search["zero_divisors_exist"]
    Dict{String,Any}(
        "name" => symbol,
        "label" => label,
        "dim" => size(table, 1),
        "commutator_max" => comm,
        "associator_max" => assoc,
        "alternator_residual" => alt_resid,
        "alternator_xxy_max" => alt_xxy,
        "alternator_xyy_max" => alt_xyy,
        "norm_mult_residual" => norm_resid,
        "has_zero_divisors" => zero_search["zero_divisors_exist"],
        "zero_divisor_check" => zero_search,
        "alternator_check" => Dict{String,Any}(
            "probe_kind" => "basis_vectors_plus_deterministic_pseudorandom_vectors",
            "probe_count" => alt_probe_count,
            "xxy_witness" => alt_xxy_witness,
            "xyy_witness" => alt_xyy_witness,
        ),
        "norm_multiplicative_check" => Dict{String,Any}("witness" => norm_witness),
        "properties" => Dict{String,Any}(
            "commutative" => commutative,
            "associative" => associative,
            "alternative" => alternative,
            "normed_division" => normed_division,
        ),
    )
end

function hopf_fibration_rows()
    rows = Vector{Dict{String,Any}}()
    for (name, dim) in [("R", 1), ("C", 2), ("H", 4), ("O", 8)]
        push!(rows, Dict{String,Any}(
            "algebra" => name,
            "algebra_dim" => dim,
            "total_unit_sphere_dim" => 2 * dim - 1,
            "base_sphere_dim" => dim,
            "fiber_sphere_dim" => dim - 1,
            "correspondence" => "S^$(2 * dim - 1) total, S^$(dim) base, S^$(dim - 1) fiber",
        ))
    end
    rows
end

function property_loss_verdicts(algebras::Dict{String,Any})
    normed = [name for name in ["R", "C", "H", "O", "S"] if algebras[name]["properties"]["normed_division"]]
    Dict{String,Any}(
        "R_C_commutative_no_loss" => algebras["R"]["properties"]["commutative"] && algebras["C"]["properties"]["commutative"],
        "H_loses_commutativity" => algebras["C"]["properties"]["commutative"] && !algebras["H"]["properties"]["commutative"],
        "O_loses_associativity" => algebras["H"]["properties"]["associative"] && !algebras["O"]["properties"]["associative"],
        "S_loses_alternativity" => algebras["O"]["properties"]["alternative"] && !algebras["S"]["properties"]["alternative"],
        "S_loses_division" => algebras["O"]["properties"]["normed_division"] && !algebras["S"]["properties"]["normed_division"] && algebras["S"]["has_zero_divisors"],
        "normed_division_exactly_R_C_H_O" => normed == ["R", "C", "H", "O"],
        "finite_hurwitz_witness_reproduced" => normed == ["R", "C", "H", "O"] &&
            algebras["R"]["properties"]["commutative"] &&
            algebras["C"]["properties"]["commutative"] &&
            !algebras["H"]["properties"]["commutative"] &&
            !algebras["O"]["properties"]["associative"] &&
            !algebras["S"]["properties"]["alternative"] &&
            algebras["S"]["has_zero_divisors"],
        "normed_division_algebras_seen" => normed,
    )
end

function build_shared_scalars(algebras::Dict{String,Any}, verdicts::Dict{String,Any})
    out = Dict{String,Any}()
    for name in ["R", "C", "H", "O", "S"]
        for key in ["dim", "commutator_max", "associator_max", "alternator_residual", "alternator_xxy_max", "alternator_xyy_max", "norm_mult_residual"]
            out["$name.$key"] = algebras[name][key]
        end
        out["$name.zero.signed_zero_divisor_count"] = algebras[name]["zero_divisor_check"]["signed_zero_divisor_count"]
    end
    out["verdict.normed_division_count"] = length(verdicts["normed_division_algebras_seen"])
    out
end

function build_shared_booleans(algebras::Dict{String,Any}, verdicts::Dict{String,Any}, controls::Dict{String,Any})
    out = Dict{String,Any}()
    for name in ["R", "C", "H", "O", "S"]
        for key in ["commutative", "associative", "alternative", "normed_division"]
            out["$name.property.$key"] = algebras[name]["properties"][key]
        end
        out["$name.has_zero_divisors"] = algebras[name]["has_zero_divisors"]
    end
    for (key, value) in verdicts
        isa(value, Bool) && (out["verdict.$key"] = value)
    end
    for (key, value) in controls
        isa(value, Bool) && (out["control.$key"] = value)
    end
    out
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        max_diff = max(max_diff, diff)
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    h_table = quaternion_table()
    o_prior = octonion_table()
    o_cd = cayley_dickson_double(h_table)
    o_cd_vs_prior_max_abs_diff = maximum(abs.(o_cd .- o_prior))
    s_table = cayley_dickson_double(o_cd)
    algebras = Dict{String,Any}(
        "R" => analyze_algebra("R", "real_numbers", real_table()),
        "C" => analyze_algebra("C", "complex_numbers", complex_table()),
        "H" => analyze_algebra("H", "quaternions", h_table),
        "O" => analyze_algebra("O", "octonions_cayley_dickson_checked_against_fano", o_cd),
        "S" => analyze_algebra("S", "sedenions_cayley_dickson_from_O", s_table),
    )
    verdicts = property_loss_verdicts(algebras)
    controls = Dict{String,Any}(
        "R_commutative_control_ok" => algebras["R"]["properties"]["commutative"],
        "C_commutative_control_ok" => algebras["C"]["properties"]["commutative"],
        "S_zero_divisor_control_ok" => algebras["S"]["has_zero_divisors"],
        "O_cd_matches_prior_table" => o_cd_vs_prior_max_abs_diff < TOL,
    )
    controls["control_miswired"] = !(controls["R_commutative_control_ok"] &&
                                     controls["C_commutative_control_ok"] &&
                                     controls["S_zero_divisor_control_ok"] &&
                                     controls["O_cd_matches_prior_table"])
    shared_scalars = build_shared_scalars(algebras, verdicts)
    shared_scalars["O_cd_vs_prior_max_abs_diff"] = o_cd_vs_prior_max_abs_diff
    shared_scalars["S.table.weighted_checksum"] = table_checksum(s_table)["weighted_checksum"]
    shared_scalars["S.table.nonzero_entry_count"] = table_checksum(s_table)["nonzero_entry_count"]
    shared_booleans = build_shared_booleans(algebras, verdicts, controls)
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_full_sim",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite R,C,H,O,S division-algebra ratchet witness only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind" => "classical",
        "sim_class" => "finite_division_algebra_geometry_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "probe_source" => "basis vectors plus deterministic pseudorandom vectors; same formulas mirrored in JAX x64",
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load_bearing finite table construction, Cayley-Dickson doubling, and exhaustive/probe scalar checks",
            "LinearAlgebra" => "load_bearing norms for commutator, associator, alternator, norm-multiplication, and zero-divisor witnesses",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
        ),
        "controls" => controls,
        "construction_checks" => Dict{String,Any}(
            "O_cd_vs_prior_max_abs_diff" => o_cd_vs_prior_max_abs_diff,
            "O_cd_matches_prior_table" => o_cd_vs_prior_max_abs_diff < TOL,
            "S_table_checksum" => table_checksum(s_table),
        ),
        "algebras" => algebras,
        "property_loss_table" => Dict(name => algebras[name]["properties"] for name in ["R", "C", "H", "O", "S"]),
        "hopf_fibration_correspondence" => hopf_fibration_rows(),
        "verdicts" => verdicts,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "divergence_log" => [
            "R and C remain commutative under the finite table check.",
            "H is the first rung with nonzero commutator residual.",
            "O keeps alternativity/normed-division in these probes but has nonzero basis associator residual.",
            "S has explicit signed two-term zero divisors and nonzero alternator residual.",
        ],
        "plain_sentence" => verdicts["finite_hurwitz_witness_reproduced"] ?
            "The finite ladder reproduces the R,C,H,O normed-division rungs and shows S as the first sampled Cayley-Dickson non-division rung." :
            "The finite ladder did not reproduce the expected R,C,H,O/S property-loss pattern; inspect controls and witnesses.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] ||
        !verdicts["finite_hurwitz_witness_reproduced"] ||
        result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    println("division_algebra_ratchet_ladder - Julia full sim")
    for name in ["R", "C", "H", "O", "S"]
        a = result["algebras"][name]
        p = a["properties"]
        println(name,
            ": dim=", a["dim"],
            " commutator_max=", a["commutator_max"],
            " associator_max=", a["associator_max"],
            " alternator_residual=", a["alternator_residual"],
            " norm_mult_residual=", a["norm_mult_residual"],
            " has_zero_divisors=", a["has_zero_divisors"],
            " commutative=", p["commutative"],
            " associative=", p["associative"],
            " alternative=", p["alternative"],
            " normed_division=", p["normed_division"])
    end
    println("verdicts=", JSON.json(result["verdicts"]))
    println("controls=", JSON.json(result["controls"]))
    println("parity_status=", result["parity"]["status"],
        " parity_max_diff=", result["parity"]["parity_max_diff"],
        " within_1e-9=", result["parity"]["within_1e_9"])
    println(result["plain_sentence"])
    println("wrote: ", result["result_path"])
end

if abspath(PROGRAM_FILE) == abspath(@__FILE__)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    print_summary(result)

    if result["stop_condition_fired"]
        println("STOP: division_algebra_ratchet_ladder control/verdict/parity condition failed.")
        exit(2)
    end
end
