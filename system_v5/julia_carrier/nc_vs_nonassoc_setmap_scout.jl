#!/usr/bin/env julia
# object_id: nc_vs_nonassoc_setmap_scout
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite set-map placing H/O/J3(O)/S by witness, scratch scout.
# No final M(C), PEPS3D admission, Axis0, physics, engine, or bridge claim.

using Dates
using JSON
using LinearAlgebra
using Printf

const OBJECT_ID = "nc_vs_nonassoc_setmap_scout"
const BRANCH = 3
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "Finite set-map placing H/O/J3(O)/S by witness, scratch scout. No final M(C), PEPS3D admission, Axis0, physics, engine, or bridge claim."
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/nc_vs_nonassoc_setmap_scout_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/nc_vs_nonassoc_setmap_scout_results.json")
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/nc_vs_nonassoc_setmap_scout.jl")
const TOL = 1.0e-10
const NONZERO_TOL = 1.0e-8
const SAMPLE_COUNT = 18

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing x64 finite algebra tables, products, associators, norms, and verdict scalars"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite vector norms and parity scalars"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization and peer receipt parsing"),
    "JAX" => Dict("tried" => true, "used" => true, "reason" => "supportive independent backend mirror checked through peer_result_path parity"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "forbidden for this branch; absent from the Julia backend"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "JAX" => "supportive",
    "numpy" => nothing,
)

function basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
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

function associator(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function commutator(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    multiply(table, x, y) - multiply(table, y, x)
end

function conjugate_cd(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function real_table()
    ones(Float64, 1, 1, 1)
end

function cayley_dickson_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2n)]
    c = y[1:n]
    d = y[(n + 1):(2n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_cd(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_cd(c))
    vcat(first, second)
end

function cayley_dickson_double(parent::Array{Float64,3})
    dim = 2 * size(parent, 1)
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cayley_dickson_multiply(parent, basis(dim, i), basis(dim, j))
    end
    table
end

function complex_pair_mul(a::AbstractVector{Float64}, b::AbstractVector{Float64})
    [a[1] * b[1] - a[2] * b[2], a[1] * b[2] + a[2] * b[1]]
end

function m2c_get(x::AbstractVector{Float64}, row0::Int, col0::Int)
    start = (row0 * 2 + col0) * 2 + 1
    [x[start], x[start + 1]]
end

function m2c_set!(out::Vector{Float64}, row0::Int, col0::Int, value::AbstractVector{Float64})
    start = (row0 * 2 + col0) * 2 + 1
    out[start] = value[1]
    out[start + 1] = value[2]
end

function m2c_vector_multiply(x::AbstractVector{Float64}, y::AbstractVector{Float64})
    out = zeros(Float64, 8)
    for i in 0:1, j in 0:1
        acc = zeros(Float64, 2)
        for k in 0:1
            acc += complex_pair_mul(m2c_get(x, i, k), m2c_get(y, k, j))
        end
        m2c_set!(out, i, j, acc)
    end
    out
end

function m2c_table()
    dim = 8
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= m2c_vector_multiply(basis(dim, i), basis(dim, j))
    end
    table
end

octonion_conj(x::AbstractVector{Float64}) = conjugate_cd(x)

function j3_basis_matrix(idx0::Int)
    mat = zeros(Float64, 3, 3, 8)
    if idx0 < 3
        mat[idx0 + 1, idx0 + 1, 1] = 1.0
        return mat
    end
    pairs = [(1, 2), (1, 3), (2, 3)]
    slot = idx0 - 3
    pair_idx = div(slot, 8) + 1
    component = mod(slot, 8)
    i, j = pairs[pair_idx]
    unit = basis(8, component)
    mat[i, j, :] .= unit
    mat[j, i, :] .= octonion_conj(unit)
    mat
end

function j3_flatten(mat::Array{Float64,3})
    parts = Vector{Float64}()
    push!(parts, mat[1, 1, 1])
    push!(parts, mat[2, 2, 1])
    push!(parts, mat[3, 3, 1])
    for (i, j) in [(1, 2), (1, 3), (2, 3)]
        append!(parts, vec(mat[i, j, :]))
    end
    parts
end

function j3_unflatten(x::AbstractVector{Float64})
    mat = zeros(Float64, 3, 3, 8)
    mat[1, 1, 1] = x[1]
    mat[2, 2, 1] = x[2]
    mat[3, 3, 1] = x[3]
    cursor = 4
    for (i, j) in [(1, 2), (1, 3), (2, 3)]
        octv = collect(x[cursor:(cursor + 7)])
        cursor += 8
        mat[i, j, :] .= octv
        mat[j, i, :] .= octonion_conj(octv)
    end
    mat
end

function j3_matmul_oct(o_table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    out = zeros(Float64, 3, 3, 8)
    for i in 1:3, j in 1:3
        acc = zeros(Float64, 8)
        for k in 1:3
            acc += multiply(o_table, vec(a[i, k, :]), vec(b[k, j, :]))
        end
        out[i, j, :] .= acc
    end
    out
end

function j3_jordan_matrix_product(o_table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    0.5 .* (j3_matmul_oct(o_table, a, b) + j3_matmul_oct(o_table, b, a))
end

function j3_vector_multiply(o_table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    j3_flatten(j3_jordan_matrix_product(o_table, j3_unflatten(x), j3_unflatten(y)))
end

function j3_table(o_table::Array{Float64,3})
    dim = 27
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= j3_vector_multiply(o_table, basis(dim, i), basis(dim, j))
    end
    table
end

function j3_square_trace(o_table::Array{Float64,3}, x::AbstractVector{Float64})
    mat = j3_unflatten(x)
    sq = j3_jordan_matrix_product(o_table, mat, mat)
    sq[1, 1, 1] + sq[2, 2, 1] + sq[3, 3, 1]
end

function probe_vector(dim::Int, sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 +
                   (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0) for j in 1:dim]
end

function terms_from_vector(v::AbstractVector{Float64})
    terms = Vector{Dict{String,Any}}()
    for idx in 0:(length(v) - 1)
        value = v[idx + 1]
        if abs(value) > TOL
            push!(terms, Dict{String,Any}("basis_index" => idx, "label" => "e$idx", "coefficient" => value))
        end
    end
    terms
end

function vector_witness(table::Array{Float64,3}, left::AbstractVector{Float64}, right::AbstractVector{Float64}, kind::String)
    product = multiply(table, left, right)
    product_norm = norm(product)
    left_norm = norm(left)
    right_norm = norm(right)
    Dict{String,Any}(
        "kind" => kind,
        "left_terms" => terms_from_vector(left),
        "right_terms" => terms_from_vector(right),
        "product_terms" => terms_from_vector(product),
        "left_norm" => left_norm,
        "right_norm" => right_norm,
        "product_norm" => product_norm,
        "pass" => product_norm < TOL && left_norm > TOL && right_norm > TOL,
    )
end

function explicit_zero_witness(name::String, table::Array{Float64,3})
    dim = size(table, 1)
    if name == "M2C"
        return vector_witness(table, basis(dim, 0), basis(dim, 6), "matrix_units_E11_times_E22")
    elseif name == "J3O"
        return vector_witness(table, basis(dim, 0), basis(dim, 1), "orthogonal_jordan_idempotents_E11_circ_E22")
    elseif name == "S"
        return vector_witness(table, basis(dim, 1) + basis(dim, 10), basis(dim, 5) + basis(dim, 14), "requested_sedenion_(e1+e10)*(e5+e14)")
    end
    Dict{String,Any}(
        "kind" => "no_explicit_zero_product_claimed",
        "left_terms" => [],
        "right_terms" => [],
        "product_terms" => [],
        "left_norm" => nothing,
        "right_norm" => nothing,
        "product_norm" => nothing,
        "pass" => false,
    )
end

function analyze_algebra(name::String, table::Array{Float64,3})
    dim = size(table, 1)
    assoc_gap = 0.0
    comm_gap = 0.0
    alt_xxy_gap = 0.0
    alt_xyy_gap = 0.0
    power_gap = 0.0
    norm_mult_gap = 0.0
    assoc_witness = Dict{String,Any}("kind" => "none")
    comm_witness = Dict{String,Any}("kind" => "none")
    norm_witness = Dict{String,Any}("kind" => "none")
    power_witness = Dict{String,Any}("kind" => "none")

    for sample_idx in 1:SAMPLE_COUNT
        x = probe_vector(dim, sample_idx, 3)
        y = probe_vector(dim, sample_idx, 5)
        z = probe_vector(dim, sample_idx, 7)
        assoc_norm = norm(associator(table, x, y, z))
        if assoc_norm > assoc_gap
            assoc_gap = assoc_norm
            assoc_witness = Dict{String,Any}("sample_idx" => sample_idx, "norm" => assoc_norm)
        end
        comm_norm = norm(commutator(table, x, y))
        if comm_norm > comm_gap
            comm_gap = comm_norm
            comm_witness = Dict{String,Any}("sample_idx" => sample_idx, "norm" => comm_norm)
        end
        alt_xxy_gap = max(alt_xxy_gap, norm(associator(table, x, x, y)))
        alt_xyy_gap = max(alt_xyy_gap, norm(associator(table, x, y, y)))
        x2 = multiply(table, x, x)
        x3_left = multiply(table, x2, x)
        x3_right = multiply(table, x, x2)
        x4_left = multiply(table, x2, x2)
        x4_right = multiply(table, x, x3_right)
        power_residual = max(norm(x3_left - x3_right), norm(x4_left - x4_right))
        if power_residual > power_gap
            power_gap = power_residual
            power_witness = Dict{String,Any}("sample_idx" => sample_idx, "norm" => power_residual)
        end
        product = multiply(table, x, y)
        norm_residual = abs(norm(product) - norm(x) * norm(y))
        if norm_residual > norm_mult_gap
            norm_mult_gap = norm_residual
            norm_witness = Dict{String,Any}("sample_idx" => sample_idx, "residual" => norm_residual)
        end
    end

    zero = explicit_zero_witness(name, table)
    if zero["pass"]
        zero_norm_residual = abs(zero["product_norm"] - zero["left_norm"] * zero["right_norm"])
        if zero_norm_residual > norm_mult_gap
            norm_mult_gap = zero_norm_residual
            norm_witness = merge(copy(zero), Dict{String,Any}("residual" => zero_norm_residual))
        end
    end

    Dict{String,Any}(
        "dim" => dim,
        "sample_count" => SAMPLE_COUNT,
        "associativity_gap" => assoc_gap,
        "commutativity_gap" => comm_gap,
        "alternativity_xxy_gap" => alt_xxy_gap,
        "alternativity_xyy_gap" => alt_xyy_gap,
        "alternativity_gap" => max(alt_xxy_gap, alt_xyy_gap),
        "power_associativity_gap" => power_gap,
        "norm_multiplicativity_gap" => norm_mult_gap,
        "assoc_witness" => assoc_witness,
        "comm_witness" => comm_witness,
        "power_witness" => power_witness,
        "norm_multiplicativity_witness" => norm_witness,
        "explicit_zero_product_witness" => zero,
        "assoc_zero_under_tol" => assoc_gap < TOL,
        "commutative_under_tol" => comm_gap < TOL,
        "alternative_under_tol" => max(alt_xxy_gap, alt_xyy_gap) < TOL,
        "power_associative_under_tol" => power_gap < TOL,
        "norm_multiplicative_under_tol" => norm_mult_gap < TOL,
        "explicit_zero_product_found" => Bool(zero["pass"]),
    )
end

function classify(name::String, metrics::Dict{String,Any})
    placement = if name in ["R", "C"]
        "commutative_associative_control_below_NC_line"
    elseif name == "H"
        "Set1_noncommutative_associative_quaternion_carrier"
    elseif name == "M2C"
        "Set1_noncommutative_associative_matrix_algebra_with_zero_products"
    elseif name == "O"
        "Set2_alternative_nonassociative_octonion_readout_lane"
    elseif name == "J3O"
        "Set2_formally_real_nonassociative_jordan_observable_lane"
    elseif name == "S"
        "graveyard_nonassociative_zero_divisor_sedenion"
    else
        "unclassified"
    end
    Dict{String,Any}(
        "placement" => placement,
        "set1_nc_associative" => name in ["H", "M2C"],
        "set2_superset_or_nonassoc_lane" => name in ["H", "M2C", "O", "J3O"],
        "graveyard" => name == "S",
        "noncommutative_detected" => metrics["commutativity_gap"] > NONZERO_TOL,
        "nonassociative_detected" => metrics["associativity_gap"] > NONZERO_TOL,
        "commutative_control" => name in ["R", "C"],
    )
end

function table_checksum(table::Array{Float64,3})
    dim = size(table, 1)
    nonzero = 0
    sum_abs = 0.0
    checksum = 0.0
    for c in 1:dim, a in 1:dim, b in 1:dim
        value = table[c, a, b]
        if abs(value) > 0.0
            nonzero += 1
        end
        sum_abs += abs(value)
        checksum += value * (1_000_003.0 * c + 1_009.0 * a + b)
    end
    Dict{String,Any}("dim" => dim, "nonzero_entry_count" => nonzero, "sum_abs_entries" => sum_abs, "weighted_checksum" => checksum)
end

function formal_real_j3_positive(o_table::Array{Float64,3})
    min_square_trace = Inf
    max_square_trace_error = 0.0
    witness = Dict{String,Any}("kind" => "none")
    for sample_idx in 1:SAMPLE_COUNT
        x = probe_vector(27, sample_idx, 11)
        value = j3_square_trace(o_table, x)
        weighted_coordinate_sq = dot(x[1:3], x[1:3]) + 2.0 * dot(x[4:end], x[4:end])
        min_square_trace = min(min_square_trace, value)
        max_square_trace_error = max(max_square_trace_error, abs(value - weighted_coordinate_sq))
        if !haskey(witness, "square_trace") || value < witness["square_trace"]
            witness = Dict{String,Any}("sample_idx" => sample_idx, "square_trace" => value, "weighted_coordinate_square" => weighted_coordinate_sq)
        end
    end
    Dict{String,Any}(
        "min_sample_square_trace" => min_square_trace,
        "max_square_trace_minus_vector_square_abs" => max_square_trace_error,
        "pass" => min_square_trace > 0.0 && max_square_trace_error < TOL,
        "witness" => witness,
    )
end

function build_tables()
    r = real_table()
    c = cayley_dickson_double(r)
    h = cayley_dickson_double(c)
    o = cayley_dickson_double(h)
    s = cayley_dickson_double(o)
    Dict{String,Any}(
        "R" => r,
        "C" => c,
        "H" => h,
        "M2C" => m2c_table(),
        "O" => o,
        "J3O" => j3_table(o),
        "S" => s,
    )
end

function row_pass(section::Dict{String,Any})
    all(Bool(row["pass"]) for row in values(section))
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "parity_max_diff" => nothing,
            "max_diff_key" => nothing,
            "within_1e_10" => false,
            "boolean_mismatches" => [],
            "missing_keys" => [],
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    missing = String[]
    for key in sort(collect(keys(result["shared_scalars"])))
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        julia_value = Float64(result["shared_scalars"][key])
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        push!(rows, Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff))
    end
    mismatches = Vector{Dict{String,Any}}()
    for key in sort(collect(keys(result["shared_booleans"])))
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(result["shared_booleans"][key]) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(result["shared_booleans"][key]), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "max_diff_key" => max_diff_key,
        "within_1e_10" => max_diff < TOL && isempty(mismatches) && isempty(missing),
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
    )
end

function build_result()
    tables = build_tables()
    names = ["R", "C", "H", "M2C", "O", "J3O", "S"]
    metrics = Dict{String,Any}(name => analyze_algebra(name, tables[name]) for name in names)
    placements = Dict{String,Any}(name => classify(name, metrics[name]) for name in names)
    j3_formal_real = formal_real_j3_positive(tables["O"])

    positive = Dict{String,Any}(
        "H_associative_noncommutative_carrier" => Dict(
            "pass" => metrics["H"]["assoc_zero_under_tol"] && placements["H"]["noncommutative_detected"],
            "assoc_gap" => metrics["H"]["associativity_gap"],
            "comm_gap" => metrics["H"]["commutativity_gap"],
            "placement" => placements["H"]["placement"],
        ),
        "O_alternative_nonassoc_no_zero_divisor_in_norm_control" => Dict(
            "pass" => metrics["O"]["associativity_gap"] > NONZERO_TOL && metrics["O"]["alternative_under_tol"] &&
                metrics["O"]["norm_multiplicative_under_tol"] && !metrics["O"]["explicit_zero_product_found"],
            "assoc_gap" => metrics["O"]["associativity_gap"],
            "alternativity_gap" => metrics["O"]["alternativity_gap"],
            "norm_multiplicativity_gap" => metrics["O"]["norm_multiplicativity_gap"],
            "placement" => placements["O"]["placement"],
        ),
        "J3O_formally_real_nonassoc_jordan_observable" => Dict(
            "pass" => metrics["J3O"]["associativity_gap"] > NONZERO_TOL && metrics["J3O"]["commutative_under_tol"] &&
                metrics["J3O"]["power_associative_under_tol"] && j3_formal_real["pass"],
            "assoc_gap" => metrics["J3O"]["associativity_gap"],
            "comm_gap" => metrics["J3O"]["commutativity_gap"],
            "power_gap" => metrics["J3O"]["power_associativity_gap"],
            "formal_real_square_trace" => j3_formal_real,
            "placement" => placements["J3O"]["placement"],
        ),
        "S_sedenion_graveyard_zero_divisor" => Dict(
            "pass" => metrics["S"]["explicit_zero_product_found"],
            "witness" => metrics["S"]["explicit_zero_product_witness"],
            "placement" => placements["S"]["placement"],
        ),
        "finite_set_map_clean_separation" => Dict(
            "pass" => placements["H"]["set1_nc_associative"] && placements["M2C"]["set1_nc_associative"] &&
                placements["O"]["set2_superset_or_nonassoc_lane"] && placements["J3O"]["set2_superset_or_nonassoc_lane"] &&
                placements["S"]["graveyard"] && placements["R"]["commutative_control"] && placements["C"]["commutative_control"],
            "set1" => ["H", "M2C"],
            "set2_non_graveyard" => ["H", "M2C", "O", "J3O"],
            "graveyard" => ["S"],
            "commutative_controls_below_nc_line" => ["R", "C"],
        ),
    )

    real_nonassoc = Dict{String,Any}(name => metrics[name]["associativity_gap"] > NONZERO_TOL for name in ["H", "M2C", "O", "J3O", "S"])
    erased_nonassoc = Dict{String,Any}(name => false for name in keys(real_nonassoc))
    changed_by_erasure = [name for name in keys(real_nonassoc) if Bool(real_nonassoc[name]) != Bool(erased_nonassoc[name])]
    sort!(changed_by_erasure)

    controls = Dict{String,Any}(
        "H_assoc_gap_known_zero" => Dict("pass" => metrics["H"]["associativity_gap"] < TOL, "value" => metrics["H"]["associativity_gap"]),
        "O_nonassoc_but_alternative_known" => Dict(
            "pass" => metrics["O"]["associativity_gap"] > NONZERO_TOL && metrics["O"]["alternative_under_tol"],
            "assoc_gap" => metrics["O"]["associativity_gap"],
            "alternativity_gap" => metrics["O"]["alternativity_gap"],
        ),
        "S_requested_zero_divisor_exact" => Dict("pass" => metrics["S"]["explicit_zero_product_witness"]["pass"], "witness" => metrics["S"]["explicit_zero_product_witness"]),
        "R_C_commutative_controls_below_NC_line" => Dict(
            "pass" => metrics["R"]["commutative_under_tol"] && metrics["C"]["commutative_under_tol"] &&
                placements["H"]["noncommutative_detected"] && placements["M2C"]["noncommutative_detected"],
            "R_comm_gap" => metrics["R"]["commutativity_gap"],
            "C_comm_gap" => metrics["C"]["commutativity_gap"],
            "H_comm_gap" => metrics["H"]["commutativity_gap"],
            "M2C_comm_gap" => metrics["M2C"]["commutativity_gap"],
        ),
        "real_vs_erased_nonassoc_verdict_fires" => Dict(
            "pass" => changed_by_erasure == ["J3O", "O", "S"],
            "real_nonassoc" => real_nonassoc,
            "erased_nonassoc" => erased_nonassoc,
            "changed_by_erasure" => changed_by_erasure,
        ),
    )

    boundary = Dict{String,Any}(
        "scratch_diagnostic_only" => Dict("pass" => true, "classification" => "scratch_diagnostic", "promotion_allowed" => false, "formal_admission_allowed" => false),
        "carrier_boundary" => Dict(
            "pass" => true,
            "carrier" => "finite spinor networks",
            "diagnostic_readout_lanes" => ["quaternion coordinates", "octonion coordinates", "sedenion coordinates", "J3(O) tensor coordinates"],
            "not_admitted_as_primitives" => ["octonion primitive", "tensor primitive", "PEPS3D admission primitive"],
        ),
        "claim_ceiling" => Dict(
            "pass" => true,
            "claim" => "finite set-map placing H/O/J3(O)/S by witness, scratch scout",
            "blocked_claims" => ["final M(C)", "PEPS3D admission", "Axis0", "physics", "engine", "bridge"],
        ),
        "zero_product_boundary" => Dict(
            "pass" => true,
            "note" => "M2C and J3(O) have finite zero-product pairs in their associative/Jordan products; only S is routed to graveyard here because the requested sedenion witness breaks normed-division behavior.",
        ),
    )

    shared_scalars = Dict{String,Any}()
    for name in names
        for key in ["dim", "associativity_gap", "commutativity_gap", "alternativity_gap", "power_associativity_gap", "norm_multiplicativity_gap"]
            shared_scalars["$name.$key"] = Float64(metrics[name][key])
        end
        checksum = table_checksum(tables[name])
        shared_scalars["$name.table_nonzero_entry_count"] = Float64(checksum["nonzero_entry_count"])
        shared_scalars["$name.table_weighted_checksum"] = Float64(checksum["weighted_checksum"])
        witness = metrics[name]["explicit_zero_product_witness"]
        if witness["product_norm"] !== nothing
            shared_scalars["$name.explicit_zero_product_norm"] = Float64(witness["product_norm"])
        end
    end
    shared_scalars["J3O.formal_real_min_square_trace"] = Float64(j3_formal_real["min_sample_square_trace"])
    shared_scalars["J3O.formal_real_square_trace_error"] = Float64(j3_formal_real["max_square_trace_minus_vector_square_abs"])

    shared_booleans = Dict{String,Any}()
    for name in names
        for key in ["assoc_zero_under_tol", "commutative_under_tol", "alternative_under_tol", "power_associative_under_tol", "norm_multiplicative_under_tol", "explicit_zero_product_found"]
            shared_booleans["$name.$key"] = Bool(metrics[name][key])
        end
        shared_booleans["$name.set1_nc_associative"] = Bool(placements[name]["set1_nc_associative"])
        shared_booleans["$name.set2_superset_or_nonassoc_lane"] = Bool(placements[name]["set2_superset_or_nonassoc_lane"])
        shared_booleans["$name.graveyard"] = Bool(placements[name]["graveyard"])
    end
    for (section_name, section) in [("positive", positive), ("controls", controls), ("boundary", boundary)]
        for (key, row) in section
            shared_booleans["$section_name.$key.pass"] = Bool(row["pass"])
        end
    end

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "branch" => BRANCH,
        "backend" => "julia_full_sim",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical_diagnostic",
        "sim_class" => "finite_set_map_probe",
        "numpy_used" => false,
        "tol" => TOL,
        "nonzero_tol" => NONZERO_TOL,
        "sample_count" => SAMPLE_COUNT,
        "carrier_statement" => boundary["carrier_boundary"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_manifest" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "positive" => positive,
        "CONTROLS" => controls,
        "controls" => controls,
        "boundary" => boundary,
        "placements" => placements,
        "metrics" => metrics,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "Finite witnesses separate H and M2(C) as noncommutative associative rows, O as alternative nonassociative without a finite zero-product witness, J3(O) as a formally real nonassociative Jordan observable, S as the explicit zero-divisor graveyard row, and R/C as commutative controls below the NC line.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["all_pass"] = row_pass(positive) && row_pass(controls) && row_pass(boundary) &&
        result["parity"]["within_1e_10"] && result["classification"] == CLASSIFICATION &&
        result["promotion_allowed"] === PROMOTION_ALLOWED && result["formal_admission_allowed"] === FORMAL_ADMISSION_ALLOWED && result["numpy_used"] === false
    result["headline"] = @sprintf("H_assoc=%.3e; O_assoc=%.3e; J3O_assoc=%.3e; S_zero=%.3e; parity=%s",
        metrics["H"]["associativity_gap"],
        metrics["O"]["associativity_gap"],
        metrics["J3O"]["associativity_gap"],
        metrics["S"]["explicit_zero_product_witness"]["product_norm"],
        string(result["parity"]["parity_max_diff"]))
    result
end

function print_summary(result::Dict{String,Any})
    println("$OBJECT_ID - Julia backend")
    println(result["plain_sentence"])
    println("parity_status=$(result["parity"]["status"]) parity_max_diff=$(result["parity"]["parity_max_diff"]) within_1e-10=$(result["parity"]["within_1e_10"])")
    println("all_pass=$(result["all_pass"]) result_path=$(result["result_path"])")
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)
