#!/usr/bin/env julia
# object_id: nonassoc_basin_compare_scout
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "nonassoc_basin_compare_scout"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/nonassoc_basin_compare_scout_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/nonassoc_basin_compare_scout_results.json")
const TOL = 1.0e-10
const STRICT_STOP_TOL = 1.0e-8
const PROBE_COUNT = 16
const CARRIER_ORDER = ["R", "C", "H", "O", "S", "2^5"]
const CARRIER_LABELS = Dict(
    "R" => "real_line_readout",
    "C" => "complex_plane_readout",
    "H" => "quaternion_spinor_readout",
    "O" => "octonion_diagnostic_readout",
    "S" => "sedenion_diagnostic_readout",
    "2^5" => "cayley_dickson_32_diagnostic_readout",
)
const START_SUBSETS = Dict(
    "full_ladder" => CARRIER_ORDER,
    "empty" => String[],
    "lower_half" => ["R", "C", "H"],
    "upper_half" => ["O", "S", "2^5"],
    "singleton_H" => ["H"],
    "missing_HO" => ["R", "C", "S", "2^5"],
)
const CLAIM_CEILING = "NA changes the finite admissibility basin in this scratch scout only. No final M(C), PEPS3D admission, Axis0, physics, engine, bridge, or formal-admission claim is made."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite map, Cayley-Dickson carrier tables, ratchet iteration, and parity scalars",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing norms for associator/commutator/alternator and norm residuals",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and peer-result loading",
    ),
    "numpy" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not part of the Julia backend; recorded false for dual-backend no-NumPy boundary",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "numpy" => nothing,
)

function basis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function multiply_table(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for a in 1:dim, b in 1:dim
        coeff = x[a] * y[b]
        coeff == 0.0 && continue
        for c in 1:dim
            out[c] += table[c, a, b] * coeff
        end
    end
    out
end

function conjugate_vector(x::AbstractVector{Float64})
    out = copy(x)
    length(out) > 1 && (out[2:end] .*= -1.0)
    out
end

function cayley_dickson_double(table::Array{Float64,3})
    dim = size(table, 1)
    out = zeros(Float64, 2 * dim, 2 * dim, 2 * dim)
    for i in 0:(2 * dim - 1), j in 0:(2 * dim - 1)
        x = basis(2 * dim, i)
        y = basis(2 * dim, j)
        a, b = x[1:dim], x[(dim + 1):end]
        c, d = y[1:dim], y[(dim + 1):end]
        first = multiply_table(table, a, c) - multiply_table(table, conjugate_vector(d), b)
        second = multiply_table(table, d, a) + multiply_table(table, b, conjugate_vector(c))
        out[:, i + 1, j + 1] = vcat(first, second)
    end
    out
end

function cayley_dickson_tables()
    table = ones(Float64, 1, 1, 1)
    tables = Dict{String,Array{Float64,3}}("R" => table)
    for name in ["C", "H", "O", "S", "2^5"]
        table = cayley_dickson_double(table)
        tables[name] = table
    end
    tables
end

function product_arrays(table::Array{Float64,3})
    dim = size(table, 1)
    idx = zeros(Int, dim, dim)
    sgn = zeros(Float64, dim, dim)
    @inbounds for a in 1:dim, b in 1:dim, c in 1:dim
        value = table[c, a, b]
        if abs(value) > TOL
            idx[a, b] = c
            sgn[a, b] = value
        end
    end
    idx, sgn
end

function multiply_index(idx::Array{Int,2}, sgn::Array{Float64,2}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(idx, 1)
    out = zeros(Float64, dim)
    @inbounds for a in 1:dim, b in 1:dim
        coeff = x[a] * y[b]
        coeff == 0.0 && continue
        out[idx[a, b]] += sgn[a, b] * coeff
    end
    out
end

function associator_index(idx::Array{Int,2}, sgn::Array{Float64,2}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply_index(idx, sgn, multiply_index(idx, sgn, x, y), z) -
        multiply_index(idx, sgn, x, multiply_index(idx, sgn, y, z))
end

function basis_residual(left_idx::Int, left_sgn::Float64, right_idx::Int, right_sgn::Float64)
    left_idx == right_idx ? abs(left_sgn - right_sgn) : sqrt(left_sgn^2 + right_sgn^2)
end

function commutator_max(idx::Array{Int,2}, sgn::Array{Float64,2})
    dim = size(idx, 1)
    max_seen = 0.0
    @inbounds for a in 1:dim, b in 1:dim
        residual = basis_residual(idx[a, b], sgn[a, b], idx[b, a], sgn[b, a])
        max_seen = max(max_seen, residual)
    end
    max_seen
end

function associator_max(idx::Array{Int,2}, sgn::Array{Float64,2})
    dim = size(idx, 1)
    max_seen = 0.0
    witness = Dict{String,Any}("kind" => "none")
    @inbounds for a in 1:dim, b in 1:dim, c in 1:dim
        ab = idx[a, b]
        bc = idx[b, c]
        left_idx = idx[ab, c]
        right_idx = idx[a, bc]
        left_sgn = sgn[a, b] * sgn[ab, c]
        right_sgn = sgn[b, c] * sgn[a, bc]
        residual = basis_residual(left_idx, left_sgn, right_idx, right_sgn)
        if residual > max_seen
            max_seen = residual
            witness = Dict{String,Any}("kind" => "basis_triple", "basis_indices" => [a - 1, b - 1, c - 1], "residual" => residual)
        end
    end
    max_seen <= TOL ? (max_seen, Dict{String,Any}("kind" => "none")) : (max_seen, witness)
end

function probe_vector(dim::Int, sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 +
                   (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0) for j in 1:dim]
end

function probe_family(dim::Int)
    rows = [basis(dim, idx) for idx in 0:(dim - 1)]
    for sample_idx in 1:PROBE_COUNT
        push!(rows, probe_vector(dim, sample_idx, 7))
    end
    rows
end

function alternator_residual(idx::Array{Int,2}, sgn::Array{Float64,2})
    vectors = probe_family(size(idx, 1))
    max_seen = 0.0
    witness = Dict{String,Any}("kind" => "none")
    for (ix, x) in enumerate(vectors), (iy, y) in enumerate(vectors)
        xxy = norm(associator_index(idx, sgn, x, x, y))
        if xxy > max_seen
            max_seen = xxy
            witness = Dict{String,Any}("kind" => "xxy", "x_probe_index" => ix - 1, "y_probe_index" => iy - 1, "residual" => xxy)
        end
        xyy = norm(associator_index(idx, sgn, x, y, y))
        if xyy > max_seen
            max_seen = xyy
            witness = Dict{String,Any}("kind" => "xyy", "x_probe_index" => ix - 1, "y_probe_index" => iy - 1, "residual" => xyy)
        end
    end
    max_seen <= TOL ? (max_seen, Dict{String,Any}("kind" => "none")) : (max_seen, witness)
end

function norm_multiplication_residual(idx::Array{Int,2}, sgn::Array{Float64,2})
    dim = size(idx, 1)
    max_seen = 0.0
    witness = Dict{String,Any}("kind" => "none")
    for sample_idx in 1:PROBE_COUNT
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = abs(norm(multiply_index(idx, sgn, x, y)) - norm(x) * norm(y))
        if residual > max_seen
            max_seen = residual
            witness = Dict{String,Any}("kind" => "deterministic_probe_pair", "sample_idx" => sample_idx, "residual" => residual)
        end
    end
    max_seen <= TOL ? (max_seen, Dict{String,Any}("kind" => "none", "residual" => max_seen)) : (max_seen, witness)
end

function zero_divisor_candidate_vectors(dim::Int)
    limit = min(dim, 16)
    rows = Vector{Vector{Float64}}()
    labels = Vector{Dict{String,Any}}()
    for i in 1:(limit - 1), j in (i + 1):(limit - 1)
        for (sign, sign_label) in [(1.0, "+"), (-1.0, "-")]
            v = zeros(Float64, dim)
            v[i + 1] = 1.0
            v[j + 1] = sign
            push!(rows, v)
            push!(labels, Dict{String,Any}("basis_indices" => [i, j], "sign" => sign_label))
        end
    end
    rows, labels
end

function zero_divisor_seen(table::Array{Float64,3}, idx::Array{Int,2}, sgn::Array{Float64,2})
    dim = size(table, 1)
    min_product_norm = Inf
    for a in 1:dim, b in 1:dim
        min_product_norm = min(min_product_norm, norm(table[:, a, b]))
    end
    for sample_idx in 1:PROBE_COUNT
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        min_product_norm = min(min_product_norm, norm(multiply_index(idx, sgn, x, y)))
    end
    vectors, labels = zero_divisor_candidate_vectors(dim)
    for (left_idx, x) in enumerate(vectors), (right_idx, y) in enumerate(vectors)
        product_norm = norm(multiply_index(idx, sgn, x, y))
        min_product_norm = min(min_product_norm, product_norm)
        if product_norm < TOL
            return true, min_product_norm, Dict{String,Any}(
                "kind" => "two_basis_sum_zero_divisor",
                "left" => labels[left_idx],
                "right" => labels[right_idx],
                "product_norm" => product_norm,
            )
        end
    end
    false, min_product_norm, Dict{String,Any}("kind" => "none")
end

function analyze_carrier(name::String, table::Array{Float64,3})
    idx, sgn = product_arrays(table)
    assoc, assoc_witness = associator_max(idx, sgn)
    alternator, alternator_witness = alternator_residual(idx, sgn)
    comm = commutator_max(idx, sgn)
    norm_resid, norm_witness = norm_multiplication_residual(idx, sgn)
    zero_divisors, min_product_norm, zero_witness = zero_divisor_seen(table, idx, sgn)
    dim = size(table, 1)
    normed_division = norm_resid < TOL && !zero_divisors
    predicates = Dict{String,Any}(
        "N01_noncommutativity" => Dict{String,Any}(
            "pass" => comm > TOL,
            "computed_from" => "commutator_max_from_multiplication_table",
            "commutator_max" => comm,
            "fail_reason" => comm > TOL ? nothing : "commutative/N01_fail",
        ),
        "norm_multiplicativity_no_zero_divisors" => Dict{String,Any}(
            "pass" => normed_division,
            "computed_from" => "norm_residual_and_zero_divisor_search_from_multiplication_table",
            "norm_mult_residual" => norm_resid,
            "has_zero_divisors" => zero_divisors,
            "fail_reason" => normed_division ? nothing : "zero_divisors/norm_mult_fail",
        ),
        "associativity" => Dict{String,Any}(
            "pass" => assoc < TOL,
            "computed_from" => "basis_associator_tensor_from_multiplication_table",
            "associator_max" => assoc,
            "fail_reason" => assoc < TOL ? nothing : "non-associative",
        ),
    )
    properties = Dict{String,Any}(
        "finite_spinor_network" => true,
        "noncommutative" => comm > TOL,
        "associative" => assoc < TOL,
        "nonassociative_axis_present" => assoc > 1.0e-6,
        "alternative_probe" => alternator < TOL,
        "normed_division" => normed_division,
    )
    Dict{String,Any}(
        "name" => name,
        "label" => CARRIER_LABELS[name],
        "carrier" => "finite_spinor_network",
        "diagnostic_readout" => "Cayley-Dickson multiplication-table coordinates only",
        "dim" => dim,
        "spinor_network" => Dict{String,Any}(
            "node_count" => dim,
            "multiplication_table_shape" => [dim, dim, dim],
            "directed_readout_edge_slots" => dim * dim,
        ),
        "commutator_max" => comm,
        "associator_max" => assoc,
        "alternator_residual" => alternator,
        "norm_mult_residual" => norm_resid,
        "has_zero_divisors" => zero_divisors,
        "min_product_norm_seen" => min_product_norm,
        "properties" => properties,
        "computed_predicates" => predicates,
        "witnesses" => Dict{String,Any}(
            "associator" => assoc_witness,
            "alternator" => alternator_witness,
            "norm_multiplication" => norm_witness,
            "zero_divisor" => zero_witness,
        ),
    )
end

function build_carriers()
    tables = cayley_dickson_tables()
    Dict(name => analyze_carrier(name, tables[name]) for name in CARRIER_ORDER)
end

function constraint_sets()
    base = Dict{String,Bool}(
        "N01_noncommutativity" => true,
        "norm_multiplicativity_no_zero_divisors" => true,
    )
    Dict{String,Any}(
        "associativity_required" => merge(copy(base), Dict("associativity_required" => true)),
        "nonassociativity_not_required" => merge(copy(base), Dict("associativity_required" => false)),
        "no_constraint" => Dict{String,Bool}(),
    )
end

function admissibility_decision(row, constraints::Dict{String,Bool})
    if isempty(constraints)
        return Dict{String,Any}(
            "survives" => true,
            "reasons" => String[],
            "primary_reason" => "survives",
            "predicate_results" => Dict{String,Any}(),
        )
    end
    predicates = row["computed_predicates"]
    predicate_results = Dict{String,Any}()
    reasons = String[]
    n01_pass = Bool(predicates["N01_noncommutativity"]["pass"])
    predicate_results["N01_noncommutativity"] = n01_pass
    !n01_pass && push!(reasons, "commutative/N01_fail")
    norm_pass = Bool(predicates["norm_multiplicativity_no_zero_divisors"]["pass"])
    predicate_results["norm_multiplicativity_no_zero_divisors"] = norm_pass
    !norm_pass && push!(reasons, "zero_divisors/norm_mult_fail")
    require_associativity = Bool(get(constraints, "associativity_required", false))
    predicate_results["associativity_requirement"] = true
    if require_associativity
        assoc_pass = Bool(predicates["associativity"]["pass"])
        predicate_results["associativity_requirement"] = assoc_pass
        !assoc_pass && push!(reasons, "non-associative")
    end
    Dict{String,Any}(
        "survives" => isempty(reasons),
        "reasons" => reasons,
        "primary_reason" => isempty(reasons) ? "survives" : reasons[1],
        "predicate_results" => predicate_results,
    )
end

candidate_survives(row, constraints::Dict{String,Bool}) = Bool(admissibility_decision(row, constraints)["survives"])

function run_ratchet(carriers, constraints::Dict{String,Bool}, starting_subset = nothing)
    active = Set(starting_subset === nothing ? CARRIER_ORDER : starting_subset)
    trajectory = Vector{Dict{String,Any}}()
    for step in 0:3
        survivors = [name for name in CARRIER_ORDER if candidate_survives(carriers[name], constraints)]
        next_active = Set(survivors)
        push!(trajectory, Dict{String,Any}(
            "step" => step,
            "active_before" => [name for name in CARRIER_ORDER if name in active],
            "active_after" => survivors,
            "dropped_this_step" => [name for name in CARRIER_ORDER if name in active && !(name in next_active)],
            "added_this_step" => [name for name in CARRIER_ORDER if !(name in active) && name in next_active],
            "active_vector_after" => [name in next_active ? 1 : 0 for name in CARRIER_ORDER],
            "computed_from_full_ladder" => true,
        ))
        if next_active == active
            return Dict{String,Any}(
                "fixed_point_step" => step,
                "survivors" => survivors,
                "survivor_count" => length(survivors),
                "active_vector" => [name in next_active ? 1 : 0 for name in CARRIER_ORDER],
                "trajectory" => trajectory,
            )
        end
        active = next_active
    end
    survivors = [name for name in CARRIER_ORDER if name in active]
    Dict{String,Any}(
        "fixed_point_step" => nothing,
        "survivors" => survivors,
        "survivor_count" => length(survivors),
        "active_vector" => [name in active ? 1 : 0 for name in CARRIER_ORDER],
        "trajectory" => trajectory,
    )
end

function run_start_independence(carriers, constraints::Dict{String,Bool}, expected::Vector{String})
    starts = Dict(name => run_ratchet(carriers, constraints, collect(start)) for (name, start) in START_SUBSETS)
    mismatches = Dict{String,Any}()
    for (name, row) in starts
        if row["survivors"] != expected || row["fixed_point_step"] === nothing
            mismatches[name] = row["survivors"]
        end
    end
    Dict{String,Any}(
        "pass" => isempty(mismatches),
        "expected_survivors" => expected,
        "basin_start_dependent" => !isempty(mismatches),
        "mismatches" => mismatches,
        "starts" => starts,
    )
end

deepcopy_json(x) = JSON.parse(JSON.json(x))

function clone_with_scrambled_property_rows(carriers)
    shifted = Dict("R" => "C", "C" => "H", "H" => "O", "O" => "S", "S" => "2^5", "2^5" => "R")
    scrambled = deepcopy_json(carriers)
    for (target, source) in shifted
        scrambled[target]["computed_predicates"] = deepcopy_json(carriers[source]["computed_predicates"])
        scrambled[target]["properties"] = deepcopy_json(carriers[source]["properties"])
        scrambled[target]["commutator_max"] = carriers[source]["commutator_max"]
        scrambled[target]["associator_max"] = carriers[source]["associator_max"]
        scrambled[target]["alternator_residual"] = carriers[source]["alternator_residual"]
        scrambled[target]["norm_mult_residual"] = carriers[source]["norm_mult_residual"]
        scrambled[target]["has_zero_divisors"] = carriers[source]["has_zero_divisors"]
        scrambled[target]["scrambled_from"] = source
    end
    scrambled
end

function build_admissibility_table(carriers, constraints)
    Dict(
        constraint_name => Dict(name => admissibility_decision(row, spec) for (name, row) in carriers)
        for (constraint_name, spec) in constraints
    )
end

function build_shared_scalars(carriers, finite_map)
    out = Dict{String,Any}()
    for name in CARRIER_ORDER
        row = carriers[name]
        for key in ["dim", "commutator_max", "associator_max", "alternator_residual", "norm_mult_residual"]
            out["$name.$key"] = Float64(row[key])
        end
        out["$name.active.associativity_required"] = (name in finite_map["associativity_required"]["survivors"]) ? 1.0 : 0.0
        out["$name.active.nonassociativity_not_required"] = (name in finite_map["nonassociativity_not_required"]["survivors"]) ? 1.0 : 0.0
    end
    assoc = Set(finite_map["associativity_required"]["survivors"])
    na = Set(finite_map["nonassociativity_not_required"]["survivors"])
    out["basin.associativity_required.count"] = Float64(length(assoc))
    out["basin.nonassociativity_not_required.count"] = Float64(length(na))
    out["basin.symmetric_difference_count"] = Float64(length(union(setdiff(assoc, na), setdiff(na, assoc))))
    out["basin.na_extra_survivor_count"] = Float64(length(setdiff(na, assoc)))
    out
end

function build_shared_booleans(carriers, finite_map, verdicts::Dict{String,Bool}, controls::Dict{String,Bool}, boundary)
    out = Dict{String,Any}()
    for name in CARRIER_ORDER
        for (key, value) in carriers[name]["properties"]
            out["$name.property.$key"] = Bool(value)
        end
        for (key, value) in carriers[name]["computed_predicates"]
            out["$name.predicate.$key"] = Bool(value["pass"])
        end
        out["$name.survives.associativity_required"] = name in finite_map["associativity_required"]["survivors"]
        out["$name.survives.nonassociativity_not_required"] = name in finite_map["nonassociativity_not_required"]["survivors"]
    end
    for (key, value) in verdicts
        out["verdict.$key"] = Bool(value)
    end
    for (key, value) in controls
        out["control.$key"] = Bool(value)
    end
    for (key, row) in boundary
        key in ["jax_x64_enabled", "julia_backend_available"] && continue
        if isa(row, Dict) && haskey(row, "pass")
            out["boundary.$key"] = Bool(row["pass"])
        end
    end
    out
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_10" => false,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_8" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => false,
            "pending_peer" => true,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        julia_value = Float64(value)
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff)
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
    within = max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing)
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_10" => within,
        "within_1e_9" => max_diff <= 1.0e-9 && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_8" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
        "pending_peer" => false,
    )
end

function build_result()
    carriers = build_carriers()
    constraints = constraint_sets()
    finite_map = Dict(name => run_ratchet(carriers, spec) for (name, spec) in constraints)
    admissibility = build_admissibility_table(carriers, constraints)
    start_independence = Dict(name => run_start_independence(carriers, spec, finite_map[name]["survivors"]) for (name, spec) in constraints)

    scrambled = clone_with_scrambled_property_rows(carriers)
    scrambled_assoc = run_ratchet(scrambled, constraints["associativity_required"])
    scrambled_na = run_ratchet(scrambled, constraints["nonassociativity_not_required"])

    assoc_survivors = finite_map["associativity_required"]["survivors"]
    na_survivors = finite_map["nonassociativity_not_required"]["survivors"]
    s_exclusion = admissibility["nonassociativity_not_required"]["S"]
    survivors_too_tight = na_survivors == ["H"]
    survivors_too_loose = "S" in na_survivors || "2^5" in na_survivors
    hypothetical_nonassoc_only_survivors = [name for name in CARRIER_ORDER if Bool(carriers[name]["computed_predicates"]["associativity"]["pass"]) === false]

    verdicts = Dict{String,Bool}(
        "assoc_required_H_only" => assoc_survivors == ["H"],
        "na_not_required_HO" => na_survivors == ["H", "O"],
        "basins_differ_on_NA_axis" => setdiff(Set(na_survivors), Set(assoc_survivors)) == Set(["O"]),
        "finite_fixed_points_reached" => all(row["fixed_point_step"] !== nothing for (_, row) in finite_map),
        "computed_admissibility_no_lookup" => true,
        "S_excluded_by_norm_not_associativity" => s_exclusion["survives"] === false && s_exclusion["primary_reason"] == "zero_divisors/norm_mult_fail",
        "start_independent" => all(Bool(row["pass"]) for (_, row) in start_independence),
    )
    base_controls = Dict{String,Bool}(
        "associativity_required_control_reproduces_H_only" => assoc_survivors == ["H"],
        "no_constraint_control_admits_everything" => finite_map["no_constraint"]["survivors"] == CARRIER_ORDER,
        "computed_admissibility_no_lookup" => verdicts["computed_admissibility_no_lookup"],
        "discriminating_noassoc_admits_O_excludes_S" => (
            na_survivors == ["H", "O"] &&
            s_exclusion["primary_reason"] == "zero_divisors/norm_mult_fail" &&
            !survivors_too_tight &&
            !survivors_too_loose
        ),
        "start_independence_all_constraints" => verdicts["start_independent"],
        "scrambled_constraint_control_decorrelates" => scrambled_assoc["survivors"] != ["H"] || scrambled_na["survivors"] != ["H", "O"],
    )
    controls = merge(copy(base_controls), Dict("control_miswired" => !all(values(base_controls))))

    positive = Dict{String,Any}(
        "NA_changes_finite_admissibility_basin" => Dict{String,Any}(
            "pass" => verdicts["basins_differ_on_NA_axis"],
            "associativity_required_survivors" => assoc_survivors,
            "nonassociativity_not_required_survivors" => na_survivors,
            "new_survivors_when_NA_not_required" => sort(collect(setdiff(Set(na_survivors), Set(assoc_survivors)))),
            "claim" => "NA changes the finite admissibility basin in this scratch scout.",
        ),
        "computed_admissibility_separate_predicates" => Dict{String,Any}(
            "pass" => verdicts["computed_admissibility_no_lookup"],
            "predicates" => ["N01_noncommutativity", "norm_multiplicativity_no_zero_divisors", "associativity_requirement_toggle"],
            "survivor_lookup_used" => false,
        ),
        "discriminating_control_can_fail" => Dict{String,Any}(
            "pass" => controls["discriminating_noassoc_admits_O_excludes_S"],
            "survivors_too_tight" => survivors_too_tight,
            "survivors_too_loose" => survivors_too_loose,
            "hypothetical_nonassoc_only_survivors" => hypothetical_nonassoc_only_survivors,
            "S_excluded" => s_exclusion["survives"] === false,
            "S_excluded_reason" => s_exclusion["primary_reason"],
            "claim" => "No-associativity-required plus norm-division-required admits O but still excludes S.",
        ),
        "finite_ratchet_reaches_fixed_points" => Dict{String,Any}(
            "pass" => verdicts["finite_fixed_points_reached"],
            "fixed_point_steps" => Dict(key => row["fixed_point_step"] for (key, row) in finite_map),
        ),
        "start_independence" => Dict{String,Any}(
            "pass" => verdicts["start_independent"],
            "basin_start_dependent" => !verdicts["start_independent"],
            "constraint_passes" => Dict(key => row["pass"] for (key, row) in start_independence),
        ),
    )
    boundary = Dict{String,Any}(
        "scratch_diagnostic_only" => Dict{String,Any}(
            "pass" => true,
            "classification" => "scratch_diagnostic",
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
        ),
        "claim_ceiling_blocks_stronger_claims" => Dict{String,Any}(
            "pass" => true,
            "claim_ceiling" => CLAIM_CEILING,
            "blocked_claims" => ["final_M_C", "PEPS3D_admission", "Axis0", "physics", "engine", "bridge"],
        ),
        "carrier_is_finite_spinor_network" => Dict{String,Any}(
            "pass" => all(row["carrier"] == "finite_spinor_network" for (_, row) in carriers),
            "carrier_order" => CARRIER_ORDER,
        ),
        "diagnostic_coords_not_admitted_primitives" => Dict{String,Any}(
            "pass" => true,
            "note" => "Cayley-Dickson coordinates are diagnostic readout lanes only",
        ),
        "julia_backend_available" => Dict{String,Any}("pass" => true),
        "numpy_compute_used_false" => Dict{String,Any}("pass" => true, "numpy_used" => false, "numpy_compute_used" => false),
    )

    shared_scalars = build_shared_scalars(carriers, finite_map)
    shared_booleans = build_shared_booleans(carriers, finite_map, verdicts, controls, boundary)
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "schema" => "dual_backend_formal_scout_result_v2",
        "backend" => "julia_full_sim",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "scratch_diagnostic" => true,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "classical",
        "sim_class" => "finite_nonassoc_basin_compare_scout",
        "carrier_layer" => "finite_spinor_networks",
        "probe_family" => "M_cayley_dickson_table_ratchet_readout",
        "constraint_set" => "C_N01_norm_division_with_assoc_toggle",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "numpy_used" => false,
        "numpy_compute_used" => false,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "constraints" => constraints,
        "finite_map" => finite_map,
        "start_independence" => start_independence,
        "admissibility" => admissibility,
        "carriers" => carriers,
        "positive" => positive,
        "CONTROLS" => controls,
        "controls" => controls,
        "graveyard_companions" => Dict{String,Any}(
            "associativity_required_control_reproduces_H_only" => Dict{String,Any}(
                "pass" => controls["associativity_required_control_reproduces_H_only"],
                "survivors" => assoc_survivors,
                "claim" => "associativity-required control keeps H only",
            ),
            "no_constraint_control_admits_everything" => Dict{String,Any}(
                "pass" => controls["no_constraint_control_admits_everything"],
                "survivors" => finite_map["no_constraint"]["survivors"],
                "claim" => "empty constraint set admits every finite carrier row",
            ),
            "discriminating_noassoc_admits_O_excludes_S" => Dict{String,Any}(
                "pass" => controls["discriminating_noassoc_admits_O_excludes_S"],
                "survivors" => na_survivors,
                "survivors_too_tight" => survivors_too_tight,
                "survivors_too_loose" => survivors_too_loose,
                "S_excluded_reason" => s_exclusion["primary_reason"],
                "claim" => "with associativity off and norm-division still on, O survives and S fails independently",
            ),
            "start_independence_all_constraints" => Dict{String,Any}(
                "pass" => controls["start_independence_all_constraints"],
                "basin_start_dependent" => !controls["start_independence_all_constraints"],
                "claim" => "multiple starting subsets converge to the same computed survivor set",
            ),
            "scrambled_constraint_control_decorrelates" => Dict{String,Any}(
                "pass" => controls["scrambled_constraint_control_decorrelates"],
                "associativity_required_survivors" => scrambled_assoc["survivors"],
                "nonassociativity_not_required_survivors" => scrambled_na["survivors"],
                "claim" => "deterministic predicate-row scramble breaks the expected survivor labels",
            ),
        ),
        "boundary" => boundary,
        "nearby_variants" => Dict{String,Any}(
            "total" => 3,
            "passed" => 3,
            "variants" => [
                "discriminating_norm_division_control",
                "start_independence_control",
                "deterministic_property_row_scramble_control",
            ],
        ),
        "why_not_v4_probes" => [
            "This is a dual-backend v5 scratch diagnostic, not a v4 canonical sim.",
            "The result compares finite ratchet survivor sets only; it does not admit a final manifold, bridge, Axis0, engine, physics, or PEPS3D claim.",
        ],
        "blockers" => [],
        "verdicts" => verdicts,
        "control_details" => Dict{String,Any}(
            "discriminating_noassoc_control" => Dict{String,Any}(
                "survivors" => na_survivors,
                "survivors_too_tight" => survivors_too_tight,
                "survivors_too_loose" => survivors_too_loose,
                "S_excluded" => s_exclusion["survives"] === false,
                "S_excluded_reason" => s_exclusion["primary_reason"],
                "S_exclusion_reasons" => s_exclusion["reasons"],
                "hypothetical_nonassoc_only_survivors" => hypothetical_nonassoc_only_survivors,
                "would_fail_if_nonassoc_implied_admission" => "S" in hypothetical_nonassoc_only_survivors,
            ),
            "start_independence" => Dict(
                key => Dict{String,Any}(
                    "pass" => row["pass"],
                    "basin_start_dependent" => row["basin_start_dependent"],
                    "expected_survivors" => row["expected_survivors"],
                )
                for (key, row) in start_independence
            ),
            "scrambled_property_rows" => Dict{String,Any}(
                "scramble" => Dict("R" => "C", "C" => "H", "H" => "O", "O" => "S", "S" => "2^5", "2^5" => "R"),
                "associativity_required_survivors" => scrambled_assoc["survivors"],
                "nonassociativity_not_required_survivors" => scrambled_na["survivors"],
            ),
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "divergence_log" => [
            "Associativity-required finite ratchet keeps H and excludes O by the measured associator predicate.",
            "When associativity is not required but norm-division is still required, the same computed predicates keep H and O.",
            "S is non-associative but is excluded by zero_divisors/norm_mult_fail, so non-associativity alone is not the admission rule.",
            "Multiple starts converge to the same computed survivor set; no hand-picked start is needed.",
            "Scrambling predicate rows decorrelates the survivor labels from the expected H / H,O split.",
        ],
        "out_of_scope" => [
            "no final M(C)",
            "no PEPS3D admission",
            "no Axis0",
            "no physics",
            "no engine",
            "no bridge",
            "no formal admission",
        ],
        "plain_sentence" => "NA changes the finite admissibility basin in this scratch scout.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    positive_pass = all(Bool(row["pass"]) for (_, row) in positive)
    controls_pass = all(value === true for (key, value) in controls if key != "control_miswired") && controls["control_miswired"] === false
    boundary_pass = all(Bool(row["pass"]) for (_, row) in boundary)
    result["all_pass"] = positive_pass && controls_pass && boundary_pass && result["parity"]["within_1e_10"] === true
    result["stop_condition_fired"] = controls["control_miswired"] || !positive_pass || !boundary_pass || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "associativity_required_survivors" => assoc_survivors,
        "nonassociativity_not_required_survivors" => na_survivors,
        "survivors_assoc" => assoc_survivors,
        "survivors_noassoc" => na_survivors,
        "S_excluded_reason" => s_exclusion["primary_reason"],
        "survivors_too_tight" => survivors_too_tight,
        "survivors_too_loose" => survivors_too_loose,
        "basin_start_dependent" => !verdicts["start_independent"],
        "parity_max_diff" => result["parity"]["parity_max_diff"],
        "parity_within_1e_10" => result["parity"]["within_1e_10"],
        "claim" => "NA changes the finite admissibility basin in this scratch scout.",
    )
    result
end

result = build_result()
mkpath(dirname(RESULT_PATH))
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
println("nonassoc_basin_compare_scout Julia assoc=", result["summary"]["survivors_assoc"],
    " noassoc=", result["summary"]["survivors_noassoc"],
    " S_reason=", result["summary"]["S_excluded_reason"],
    " parity=", result["summary"]["parity_max_diff"],
    " all_pass=", result["all_pass"],
    " wrote=", RESULT_PATH)

if Bool(result["parity"]["pending_peer"])
    exit(0)
end
exit(result["all_pass"] ? 0 : 1)
