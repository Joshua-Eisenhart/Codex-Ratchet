#!/usr/bin/env julia
# object_id: cayley_dickson_tower_64
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "cayley_dickson_tower_64"
const RESULT_PATH = joinpath(@__DIR__, "cayley_dickson_tower_64_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "cayley_dickson_tower_64_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const RUNG_NAMES = ["R", "C", "H", "O", "S", "T32_trigintaduonions", "CD64"]

function basis_vector(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function cd_conj(x::AbstractVector{Float64})
    out = collect(x)
    if length(out) > 1
        out[2:end] .*= -1.0
    end
    out
end

function mul_vec(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for a in 1:dim
        xa = x[a]
        abs(xa) <= 0.0 && continue
        for b in 1:dim
            yb = y[b]
            abs(yb) <= 0.0 && continue
            out .+= table[:, a, b] .* (xa * yb)
        end
    end
    out
end

function cd_pair_mul(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = mul_vec(parent, a, c) - mul_vec(parent, cd_conj(d), b)
    second = mul_vec(parent, d, a) + mul_vec(parent, b, cd_conj(c))
    vcat(first, second)
end

function cd_double(parent::Array{Float64,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    for i0 in 0:(dim - 1), j0 in 0:(dim - 1)
        table[:, i0 + 1, j0 + 1] .= cd_pair_mul(parent, basis_vector(dim, i0), basis_vector(dim, j0))
    end
    table
end

function build_tables()
    tables = Vector{Array{Float64,3}}()
    table = zeros(Float64, 1, 1, 1)
    table[1, 1, 1] = 1.0
    push!(tables, table)
    for _ in 1:6
        table = cd_double(table)
        push!(tables, table)
    end
    tables
end

function assoc_vec(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    mul_vec(table, mul_vec(table, x, y), z) - mul_vec(table, x, mul_vec(table, y, z))
end

function commutator_max(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for a in 1:dim, b in 1:dim
        max_seen = max(max_seen, norm(table[:, a, b] - table[:, b, a]))
    end
    max_seen
end

function associator_max(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for a in 1:dim, b in 1:dim, c in 1:dim
        left = mul_vec(table, table[:, a, b], basis_vector(dim, c - 1))
        right = mul_vec(table, basis_vector(dim, a - 1), table[:, b, c])
        max_seen = max(max_seen, norm(left - right))
    end
    max_seen
end

function normalized(v::Vector{Float64})
    n = norm(v)
    if n <= 0.0
        v[1] = 1.0
        n = 1.0
    end
    v ./ n
end

function deterministic_probe(dim::Int, k::Int)
    normalized([((Float64(mod((k + 17) * (j + 5) * 41 + (j + 1)^2 * 13 + k * 29, 113)) - 56.0) / 39.0) for j in 1:dim])
end

function pair_vector(dim::Int, i0::Int, j0::Int; si::Float64 = 1.0, sj::Float64 = 1.0, normalize_pair::Bool = true)
    v = zeros(Float64, dim)
    v[i0 + 1] = si
    v[j0 + 1] = sj
    normalize_pair ? normalized(v) : v
end

function zero_divisor_vectors(dim::Int)
    if dim < 16
        return nothing
    end
    left = pair_vector(dim, 1, 10; si = -1.0, sj = -1.0, normalize_pair = false)
    right = pair_vector(dim, 4, 15; si = -1.0, sj = 1.0, normalize_pair = false)
    (left, right)
end

function zero_divisor_report(table::Array{Float64,3})
    dim = size(table, 1)
    witness = zero_divisor_vectors(dim)
    if witness === nothing
        return Dict{String,Any}(
            "has_zero_divisors" => false,
            "witness_found" => false,
            "witness_product_norm" => nothing,
            "left_norm" => nothing,
            "right_norm" => nothing,
            "method" => "no targeted witness exists below the sedenion rung",
        )
    end
    left, right = witness
    product = mul_vec(table, left, right)
    product_norm = norm(product)
    Dict{String,Any}(
        "has_zero_divisors" => product_norm <= TOL && norm(left) > TOL && norm(right) > TOL,
        "witness_found" => product_norm <= TOL,
        "witness_product_norm" => product_norm,
        "left_norm" => norm(left),
        "right_norm" => norm(right),
        "left_terms" => ["-e1", "-e10"],
        "right_terms" => ["-e4", "e15"],
        "method" => dim == 16 ? "computed sedenion two-term witness" : "computed inherited sedenion witness embedded in the larger Cayley-Dickson table",
    )
end

function alternator_residual(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    witness = Dict{String,Any}("kind" => "none", "residual" => 0.0)
    xs = Vector{Vector{Float64}}()
    ys = Vector{Vector{Float64}}()
    for i0 in 0:(dim - 1)
        push!(ys, basis_vector(dim, i0))
        if dim <= 8
            push!(xs, basis_vector(dim, i0))
        end
    end
    if dim <= 8
        for i0 in 0:(dim - 1), j0 in (i0 + 1):(dim - 1), si in (-1.0, 1.0), sj in (-1.0, 1.0)
            push!(xs, pair_vector(dim, i0, j0; si = si, sj = sj))
        end
    elseif dim >= 16
        push!(xs, pair_vector(dim, 1, 10; si = -1.0, sj = -1.0))
        ys = [basis_vector(dim, 4)]
    end
    for (ix, x) in enumerate(xs), (iy, y) in enumerate(ys)
        left_alt = norm(assoc_vec(table, x, x, y))
        right_alt = norm(assoc_vec(table, x, y, y))
        if left_alt > max_seen
            max_seen = left_alt
            witness = Dict{String,Any}("kind" => "left_alternative", "x_probe_index" => ix, "y_probe_index" => iy, "residual" => left_alt)
        end
        if right_alt > max_seen
            max_seen = right_alt
            witness = Dict{String,Any}("kind" => "right_alternative", "x_probe_index" => ix, "y_probe_index" => iy, "residual" => right_alt)
        end
    end
    max_seen, witness
end

function power_residual(table::Array{Float64,3})
    dim = size(table, 1)
    probes = [basis_vector(dim, i0) for i0 in 0:(min(dim, 8) - 1)]
    for k in 1:4
        push!(probes, deterministic_probe(dim, k))
    end
    if dim >= 16
        push!(probes, pair_vector(dim, 1, 10; si = -1.0, sj = -1.0))
    end
    max_seen = 0.0
    for x in probes
        x2 = mul_vec(table, x, x)
        refs = [
            mul_vec(table, x2, x2),
            mul_vec(table, mul_vec(table, x2, x), x),
            mul_vec(table, mul_vec(table, x, x2), x),
            mul_vec(table, x, mul_vec(table, x2, x)),
            mul_vec(table, x, mul_vec(table, x, x2)),
        ]
        for candidate in refs[2:end]
            max_seen = max(max_seen, norm(candidate - refs[1]))
        end
    end
    max_seen
end

function flexible_residual(table::Array{Float64,3})
    dim = size(table, 1)
    probes = [basis_vector(dim, i0) for i0 in 0:(min(dim, 6) - 1)]
    for k in 1:3
        push!(probes, deterministic_probe(dim, k))
    end
    if dim >= 16
        push!(probes, pair_vector(dim, 1, 10; si = -1.0, sj = -1.0))
    end
    max_seen = 0.0
    for x in probes, y in probes
        max_seen = max(max_seen, norm(mul_vec(table, mul_vec(table, x, y), x) - mul_vec(table, x, mul_vec(table, y, x))))
    end
    max_seen
end

function norm_mult_residual(table::Array{Float64,3})
    dim = size(table, 1)
    probes = [basis_vector(dim, i0) for i0 in 0:(min(dim, 6) - 1)]
    for k in 1:5
        push!(probes, deterministic_probe(dim, k))
    end
    if dim >= 16
        left, right = zero_divisor_vectors(dim)
        push!(probes, left)
        push!(probes, right)
    end
    max_seen = 0.0
    for x in probes, y in probes
        max_seen = max(max_seen, abs(norm(mul_vec(table, x, y)) - norm(x) * norm(y)))
    end
    max_seen
end

function table_checksum(table::Array{Float64,3})
    dim = size(table, 1)
    nonzero = 0
    abs_sum = 0.0
    weighted = 0.0
    for c in 1:dim, a in 1:dim, b in 1:dim
        v = table[c, a, b]
        if abs(v) > 0.0
            nonzero += 1
            abs_sum += abs(v)
            weighted += v * (1_000_003.0 * c + 1_009.0 * a + b)
        end
    end
    Dict{String,Any}("nonzero_entry_count" => nonzero, "sum_abs_entries" => abs_sum, "weighted_checksum" => weighted)
end

function analyze_rung(table::Array{Float64,3}, level::Int)
    comm = commutator_max(table)
    assoc = associator_max(table)
    alt, alt_witness = alternator_residual(table)
    zero = zero_divisor_report(table)
    norm_resid = norm_mult_residual(table)
    power_resid = power_residual(table)
    flex_resid = flexible_residual(table)
    Dict{String,Any}(
        "level" => level,
        "name" => RUNG_NAMES[level + 1],
        "dim" => size(table, 1),
        "commutator_max" => comm,
        "associator_max" => assoc,
        "alternator_max" => alt,
        "alternator_witness" => alt_witness,
        "has_zero_divisors" => zero["has_zero_divisors"],
        "zero_divisor" => zero,
        "norm_mult_residual" => norm_resid,
        "power_associative_residual" => power_resid,
        "power_associative" => power_resid <= TOL,
        "flexible_residual" => flex_resid,
        "flexible" => flex_resid <= TOL,
        "commutative" => comm <= TOL,
        "associative" => assoc <= TOL,
        "alternative" => alt <= TOL,
        "norm_multiplicative" => norm_resid <= TOL,
        "table_checksum" => table_checksum(table),
    )
end

function first_lost(rungs::Vector{Dict{String,Any}}, key::String)
    for rung in rungs
        if !(rung[key]::Bool)
            return rung["name"]
        end
    end
    "not_lost"
end

function profile(rung::Dict{String,Any})
    Dict{String,Any}(
        "has_zero_divisors" => rung["has_zero_divisors"],
        "alternative" => rung["alternative"],
        "power_associative" => rung["power_associative"],
        "flexible" => rung["flexible"],
        "norm_multiplicative" => rung["norm_multiplicative"],
    )
end

function shared_scalars(rungs::Vector{Dict{String,Any}}, verdicts::Dict{String,Any}, controls::Dict{String,Any})
    scalars = Dict{String,Any}()
    for rung in rungs
        prefix = "rung_$(rung["level"])_"
        for key in ["dim", "commutator_max", "associator_max", "alternator_max", "norm_mult_residual", "power_associative_residual", "flexible_residual"]
            scalars[prefix * key] = Float64(rung[key])
        end
        for key in ["has_zero_divisors", "commutative", "associative", "alternative", "norm_multiplicative", "power_associative", "flexible"]
            scalars[prefix * key] = (rung[key]::Bool) ? 1.0 : 0.0
        end
        checksum = rung["table_checksum"]
        scalars[prefix * "nonzero_entry_count"] = Float64(checksum["nonzero_entry_count"])
        scalars[prefix * "sum_abs_entries"] = Float64(checksum["sum_abs_entries"])
        scalars[prefix * "weighted_checksum"] = Float64(checksum["weighted_checksum"])
    end
    for key in ["dim_ladder_confirmed", "properties_stabilize_after_S", "no_new_named_property_loss_past_S"]
        scalars["verdict_" * key] = (verdicts[key]::Bool) ? 1.0 : 0.0
    end
    scalars["control_dim_doubling_exact"] = (controls["dim_doubling_exact"]::Bool) ? 1.0 : 0.0
    scalars["control_dim_doubling_residual_max"] = Float64(controls["dim_doubling_residual_max"])
    scalars
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => true,
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in result["shared_scalars"]
        if haskey(peer["shared_scalars"], key)
            diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
            diffs[key] = diff
            if diff > max_diff
                max_diff = diff
                worst_key = key
            end
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => max_diff < TOL,
        "strict_divergence_gt_1e_6" => max_diff > STRICT_STOP_TOL,
        "stop_condition_fired" => max_diff > STRICT_STOP_TOL,
        "diffs" => diffs,
    )
end

function main()
    tables = build_tables()
    rungs = [analyze_rung(tables[i + 1], i) for i in 0:6]
    dim_ladder = [r["dim"] for r in rungs]
    expected_dims = [2^i for i in 0:6]
    doubling_residuals = [i == 1 ? 0 : dim_ladder[i] - 2 * dim_ladder[i - 1] for i in 1:length(dim_ladder)]
    controls = Dict{String,Any}(
        "dim_ladder_expected" => expected_dims,
        "dim_doubling_residuals" => doubling_residuals,
        "dim_doubling_residual_max" => maximum(abs.(doubling_residuals)),
        "dim_doubling_exact" => all(x -> x == 0, doubling_residuals),
        "sedenion_zero_divisor_product_norm" => rungs[5]["zero_divisor"]["witness_product_norm"],
        "cd32_embedded_zero_divisor_product_norm" => rungs[6]["zero_divisor"]["witness_product_norm"],
        "cd64_embedded_zero_divisor_product_norm" => rungs[7]["zero_divisor"]["witness_product_norm"],
    )
    s_profile = profile(rungs[5])
    t32_profile = profile(rungs[6])
    cd64_profile = profile(rungs[7])
    verdicts = Dict{String,Any}(
        "dim_ladder_confirmed" => dim_ladder == expected_dims,
        "dim_ladder" => dim_ladder,
        "properties_stabilize_after_S" => s_profile == t32_profile && s_profile == cd64_profile &&
            s_profile["has_zero_divisors"] == true && s_profile["alternative"] == false &&
            s_profile["power_associative"] == true && s_profile["flexible"] == true,
        "no_new_named_property_loss_past_S" => s_profile == t32_profile && s_profile == cd64_profile,
        "algebra_64_equals_engine_64" => "UNTESTED_RESONANCE_ONLY",
        "numeric_resonance_fence" => "algebra-64 and ENGINE-64 both count to 64, but no map is established here",
        "commutativity_lost_at" => first_lost(rungs, "commutative"),
        "associativity_lost_at" => first_lost(rungs, "associative"),
        "alternativity_lost_at" => first_lost(rungs, "alternative"),
        "division_lost_at" => first_lost(rungs, "norm_multiplicative"),
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Cayley-Dickson 2^6 property-profile diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or identity claim.",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "tools" => ["Julia LinearAlgebra"],
        "tool_manifest" => Dict("Julia LinearAlgebra" => "load-bearing for vector norms, residuals, and table checks"),
        "TOOL_MANIFEST" => Dict("Julia LinearAlgebra" => "load-bearing for vector norms, residuals, and table checks"),
        "tool_integration_depth" => Dict("Julia LinearAlgebra" => "load_bearing"),
        "TOOL_INTEGRATION_DEPTH" => Dict("Julia LinearAlgebra" => "load_bearing"),
        "rungs" => rungs,
        "controls" => controls,
        "verdicts" => verdicts,
        "plain_sentence" => "The six Cayley-Dickson doublings reach 64 dimensions exactly, while the post-sedenion result is only a fenced numeric resonance with the owner's ENGINE-64 count.",
    )
    result["shared_scalars"] = shared_scalars(rungs, verdicts, controls)
    result["parity"] = parity_block(result)
    result["stop_condition_fired"] = result["parity"]["stop_condition_fired"] ||
        !(controls["dim_doubling_exact"]::Bool) ||
        !(verdicts["dim_ladder_confirmed"]::Bool) ||
        !(verdicts["properties_stabilize_after_S"]::Bool)
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    if result["stop_condition_fired"]
        println("STOP_CONDITION_FIRED cayley_dickson_tower_64")
        exit(1)
    end
    println("cayley_dickson_tower_64 julia wrote $(RESULT_PATH)")
end

main()
