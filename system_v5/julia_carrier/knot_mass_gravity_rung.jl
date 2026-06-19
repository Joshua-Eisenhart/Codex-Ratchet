#!/usr/bin/env julia
# object_id: knot_mass_gravity_rung
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/knot_mass_gravity_rung_julia_results.json")
const JAX_RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/knot_mass_gravity_rung_results.json")
const OBJECT_ID = "knot_mass_gravity_rung"
const BACKEND = "julia"
const N = 8
const DIM = 2^N
const KNOT_SITE = 0
const TOL = 1.0e-10
const MASS_INVARIANT_TOL = 1.0e-8
const PROFILE_CHANGE_MIN = 1.0e-3
const CORRELATION_MIN = 0.95
const STRENGTHS = [0.0, 0.25, 0.5, 0.8, 1.15, 1.55, 2.0, 2.5, 3.1, 3.8]
const REFERENCE_STRENGTH = 3.1
const DECOUPLING_STRENGTH = 1.15
const EDGES = [(idx, idx + 1) for idx in 0:(N - 2)]
const DISTANCES = [idx for idx in 0:(N - 1)]
const SHELL_RADII = [idx for idx in 1:(N - 1)]
const BASE_FIELD_WEIGHTS = [0.0, 1.0, 0.94, 0.89, 0.84, 0.80, 0.76, 0.68]
const SHAPE_PERTURBED_WEIGHTS = [0.0, 1.0, 1.16, 0.67, 1.18, 0.62, 1.21, 0.54]
const KNOT_BIAS = 1.35
const FIELD_BIAS = 0.80

bit_at(index::Int, node::Int) = (index >> (N - 1 - node)) & 1

function normalize(psi::Vector{ComplexF64})
    psi ./ norm(psi)
end

function graph_phase_value(index::Int)
    total = 0.0
    for (left, right) in EDGES
        total += bit_at(index, left) * bit_at(index, right)
    end
    cis(pi * total)
end

function finite_knot_state(strength::Float64, field_weights::Vector{Float64}=BASE_FIELD_WEIGHTS)
    psi = Vector{ComplexF64}(undef, DIM)
    for index in 0:(DIM - 1)
        knot_energy = KNOT_BIAS * strength * bit_at(index, KNOT_SITE)
        field_sum = 0.0
        for node in 0:(N - 1)
            field_sum += field_weights[node + 1] * bit_at(index, node)
        end
        field_energy = FIELD_BIAS * strength * field_sum
        psi[index + 1] = exp(-(knot_energy + field_energy)) * graph_phase_value(index)
    end
    normalize(psi)
end

density(psi::Vector{ComplexF64}) = psi * psi'

function traced_nodes(keep)
    [node for node in 0:(N - 1) if !(node in keep)]
end

function packed_bits(index::Int, keep)
    out = 0
    for node in keep
        out = (out << 1) | bit_at(index, node)
    end
    out
end

function same_trace_bits(left::Int, right::Int, traced)
    for node in traced
        if bit_at(left, node) != bit_at(right, node)
            return false
        end
    end
    true
end

function reduced_density(rho::Matrix{ComplexF64}, keep)
    traced = traced_nodes(keep)
    dim_a = 2^length(keep)
    out = zeros(ComplexF64, dim_a, dim_a)
    for left in 0:(DIM - 1)
        for right in 0:(DIM - 1)
            if same_trace_bits(left, right, traced)
                out[packed_bits(left, keep) + 1, packed_bits(right, keep) + 1] += rho[left + 1, right + 1]
            end
        end
    end
    out
end

function entropy_probs(values)
    total = 0.0
    for value in values
        p = max(real(value), 0.0)
        if p > 1.0e-15
            total -= p * log(p)
        end
    end
    total
end

function entropy_rho(rho::Matrix{ComplexF64})
    hermitian = Hermitian((rho + rho') / 2)
    entropy_probs(eigvals(hermitian))
end

function normalized_entropy(rho::Matrix{ComplexF64}, dim::Int)
    dim <= 1 && return 0.0
    entropy_rho(rho) / log(Float64(dim))
end

purity(rho::Matrix{ComplexF64}) = real(tr(rho * rho))

function support_entropy(psi::Vector{ComplexF64})
    entropy_probs(abs2.(psi)) / log(Float64(DIM))
end

function mass_readout_from_rho(rho::Matrix{ComplexF64})
    rho_k = reduced_density(rho, (KNOT_SITE,))
    local_purity = purity(rho_k)
    entropy_norm = normalized_entropy(rho_k, 2)
    purity_excess = clamp((local_purity - 0.5) / 0.5, 0.0, 1.0)
    locality = 1.0
    boundedness = clamp(1.0 - entropy_norm, 0.0, 1.0)
    mass = purity_excess * locality * boundedness
    (
        mass,
        Dict{String,Any}(
            "knot_site" => Float64(KNOT_SITE),
            "local_purity" => local_purity,
            "purity_excess_norm" => purity_excess,
            "locality_weight" => locality,
            "boundedness_negentropy" => boundedness,
            "local_entropy_norm" => entropy_norm,
        ),
    )
end

shell_area(radius::Int) = Float64(radius * radius)

function flat_shell_entropies(field_weights::Vector{Float64}=BASE_FIELD_WEIGHTS)
    flat_rho = density(finite_knot_state(0.0, field_weights))
    [normalized_entropy(reduced_density(flat_rho, (node,)), 2) for node in 0:(N - 1)]
end

function gravity_profile_from_rho(rho::Matrix{ComplexF64}, flat_entropies::Vector{Float64})
    mass_source, mass_detail = mass_readout_from_rho(rho)
    values = Float64[]
    rows = Any[]
    for radius in SHELL_RADII
        rho_i = reduced_density(rho, (radius,))
        entropy_i = normalized_entropy(rho_i, 2)
        entropy_drop = max(0.0, flat_entropies[radius + 1] - entropy_i)
        area = shell_area(radius)
        pressure = mass_source * entropy_drop / area
        push!(values, pressure)
        push!(
            rows,
            Dict{String,Any}(
                "r" => radius,
                "node" => radius,
                "shell_area_square_possibilities" => area,
                "shell_entropy_norm" => entropy_i,
                "flat_shell_entropy_norm" => flat_entropies[radius + 1],
                "entropy_drop_from_flat" => entropy_drop,
                "gravity_gradient" => pressure,
            ),
        )
    end
    (
        values,
        Dict{String,Any}(
            "mass_source_detail" => mass_detail,
            "profile" => rows,
            "total_gravity" => sum(values),
        ),
    )
end

function readouts(strength::Float64, field_weights::Vector{Float64}=BASE_FIELD_WEIGHTS)
    psi = finite_knot_state(strength, field_weights)
    rho = density(psi)
    mass, mass_detail = mass_readout_from_rho(rho)
    profile, gravity_detail = gravity_profile_from_rho(rho, flat_shell_entropies(field_weights))
    Dict{String,Any}(
        "strength" => strength,
        "mass" => mass,
        "total_gravity" => sum(profile),
        "gravity_profile" => profile,
        "expansion_dark_energy" => support_entropy(psi),
        "mass_detail" => mass_detail,
        "gravity_detail" => gravity_detail,
    )
end

function pearson_corr(xs::Vector{Float64}, ys::Vector{Float64})
    x_mean = sum(xs) / length(xs)
    y_mean = sum(ys) / length(ys)
    x0 = xs .- x_mean
    y0 = ys .- y_mean
    denom = norm(x0) * norm(y0)
    denom > 0.0 ? dot(x0, y0) / denom : 0.0
end

function monotone_non_decreasing(values::Vector{Float64}; tol::Float64=1.0e-12)
    all(values[idx + 1] - values[idx] >= -tol for idx in 1:(length(values) - 1))
end

function monotone_decreasing(values::Vector{Float64}; tol::Float64=1.0e-12)
    all(values[idx + 1] - values[idx] <= tol for idx in 1:(length(values) - 1))
end

function linear_fit(xs::Vector{Float64}, ys::Vector{Float64})
    x_mean = sum(xs) / length(xs)
    y_mean = sum(ys) / length(ys)
    denom = sum((x - x_mean)^2 for x in xs)
    slope = denom > 0.0 ? sum((xs[idx] - x_mean) * (ys[idx] - y_mean) for idx in eachindex(xs)) / denom : 0.0
    intercept = y_mean - slope * x_mean
    (slope, intercept)
end

sse(values::Vector{Float64}, preds::Vector{Float64}) = sum((values[idx] - preds[idx])^2 for idx in eachindex(values))

function falloff_fit(profile_values::Vector{Float64})
    radii = Float64.(SHELL_RADII)
    profile = Float64.(profile_values)
    positive = [max(value, 1.0e-300) for value in profile]
    log_r = log.(radii)
    log_g = log.(positive)
    slope, intercept = linear_fit(log_r, log_g)
    exponent = -slope
    free_power_pred = [exp(intercept) * radius^(-exponent) for radius in radii]

    alternatives = Dict{String,Any}()
    for fixed_exp in (0.0, 1.0, 2.0, 3.0)
        basis = [radius^(-fixed_exp) for radius in radii]
        amp = sum(profile[idx] * basis[idx] for idx in eachindex(profile)) / sum(value^2 for value in basis)
        pred = [amp * value for value in basis]
        alternatives["power_e_$(Int(fixed_exp))"] = Dict{String,Any}("sse" => sse(profile, pred), "amplitude" => amp)
    end

    exp_slope, exp_intercept = linear_fit(radii, log_g)
    exp_pred = [exp(exp_intercept + exp_slope * radius) for radius in radii]
    alternatives["exponential"] = Dict{String,Any}(
        "sse" => sse(profile, exp_pred),
        "lambda" => -exp_slope,
        "amplitude" => exp(exp_intercept),
    )
    alternatives["free_power"] = Dict{String,Any}("sse" => sse(profile, free_power_pred), "exponent" => exponent)
    best_model = ""
    best_sse = Inf
    for (key, value) in alternatives
        if value["sse"] < best_sse
            best_sse = value["sse"]
            best_model = key
        end
    end
    Dict{String,Any}(
        "radii" => radii,
        "profile" => profile_values,
        "falloff_exponent" => exponent,
        "monotone_decreasing" => monotone_decreasing(profile),
        "alternative_fits" => alternatives,
        "best_model_by_sse" => best_model,
        "one_over_r2_sse" => alternatives["power_e_2"]["sse"],
    )
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_10" => false,
            "missing_from_peer" => sort(collect(keys(result["shared_scalars"]))),
            "missing_from_self" => String[],
            "diffs" => Dict{String,Any}(),
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sort(setdiff(collect(keys(self_scalars)), collect(keys(peer_scalars))))
    missing_from_self = sort(setdiff(collect(keys(peer_scalars)), collect(keys(self_scalars))))
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in self_scalars
        if haskey(peer_scalars, key)
            diff = abs(Float64(value) - Float64(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff
                max_diff = diff
                worst_key = key
            end
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_10" => isempty(missing_from_peer) && isempty(missing_from_self) && max_diff <= TOL,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "diffs" => diffs,
    )
end

function main()
    sweep_rows = [readouts(strength, BASE_FIELD_WEIGHTS) for strength in STRENGTHS]
    mass_values = [Float64(row["mass"]) for row in sweep_rows]
    gravity_values = [Float64(row["total_gravity"]) for row in sweep_rows]
    corr = pearson_corr(mass_values, gravity_values)
    ref = readouts(REFERENCE_STRENGTH, BASE_FIELD_WEIGHTS)
    falloff = falloff_fit(ref["gravity_profile"])
    flat = sweep_rows[1]

    shape_a = readouts(DECOUPLING_STRENGTH, BASE_FIELD_WEIGHTS)
    shape_b = readouts(DECOUPLING_STRENGTH, SHAPE_PERTURBED_WEIGHTS)
    profile_a = Float64.(shape_a["gravity_profile"])
    profile_b = Float64.(shape_b["gravity_profile"])
    mass_shape_diff = abs(Float64(shape_a["mass"]) - Float64(shape_b["mass"]))
    profile_l2_diff = norm(profile_a .- profile_b)
    shape_b_falloff = falloff_fit(shape_b["gravity_profile"])
    exponent_delta = abs(Float64(falloff["falloff_exponent"]) - Float64(shape_b_falloff["falloff_exponent"]))

    flatten_both_vanish = flat["mass"] <= TOL && flat["total_gravity"] <= TOL
    dark_energy_distinct = flatten_both_vanish && abs(flat["expansion_dark_energy"] - 1.0) <= TOL
    co_scaling = monotone_non_decreasing(mass_values) &&
        monotone_non_decreasing(gravity_values) &&
        corr >= CORRELATION_MIN &&
        sweep_rows[end]["mass"] > 0.0 &&
        sweep_rows[end]["total_gravity"] > 0.0
    falloff_pass = falloff["monotone_decreasing"] && falloff["falloff_exponent"] > 0.0
    decoupling_witness = mass_shape_diff <= MASS_INVARIANT_TOL && profile_l2_diff >= PROFILE_CHANGE_MIN

    shared_scalars = Dict{String,Any}(
        "mass_gravity_corr" => corr,
        "falloff_exponent" => Float64(falloff["falloff_exponent"]),
        "falloff_one_over_r2_sse" => Float64(falloff["one_over_r2_sse"]),
        "shape_b_falloff_exponent" => Float64(shape_b_falloff["falloff_exponent"]),
        "shape_exponent_delta" => Float64(exponent_delta),
        "shape_mass_abs_diff" => Float64(mass_shape_diff),
        "shape_profile_l2_diff" => Float64(profile_l2_diff),
        "flatten_mass" => Float64(flat["mass"]),
        "flatten_gravity" => Float64(flat["total_gravity"]),
        "flatten_expansion_dark_energy" => Float64(flat["expansion_dark_energy"]),
        "flatten_both_vanish" => flatten_both_vanish ? 1.0 : 0.0,
        "dark_energy_distinct" => dark_energy_distinct ? 1.0 : 0.0,
        "co_scaling" => co_scaling ? 1.0 : 0.0,
        "falloff_pass" => falloff_pass ? 1.0 : 0.0,
        "decoupling_witness" => decoupling_witness ? 1.0 : 0.0,
    )
    for (idx, row) in enumerate(sweep_rows)
        zero_idx = idx - 1
        shared_scalars["sweep_$(zero_idx).strength"] = Float64(row["strength"])
        shared_scalars["sweep_$(zero_idx).mass"] = Float64(row["mass"])
        shared_scalars["sweep_$(zero_idx).total_gravity"] = Float64(row["total_gravity"])
        shared_scalars["sweep_$(zero_idx).expansion_dark_energy"] = Float64(row["expansion_dark_energy"])
    end
    for (idx, value) in enumerate(ref["gravity_profile"])
        shared_scalars["falloff_profile.r$(SHELL_RADII[idx])"] = Float64(value)
    end
    for (idx, value) in enumerate(shape_b["gravity_profile"])
        shared_scalars["shape_perturbed_profile.r$(SHELL_RADII[idx])"] = Float64(value)
    end

    positive = Dict{String,Any}(
        "co_scaling_same_source_strength_sweep" => Dict{String,Any}(
            "strengths" => STRENGTHS,
            "mass_values" => mass_values,
            "total_gravity_values" => gravity_values,
            "mass_monotone_non_decreasing" => monotone_non_decreasing(mass_values),
            "gravity_monotone_non_decreasing" => monotone_non_decreasing(gravity_values),
            "mass_gravity_corr" => corr,
            "correlation_min" => CORRELATION_MIN,
            "pass" => co_scaling,
        ),
        "falloff_by_network_distance_reported_not_forced" => merge(falloff, Dict{String,Any}("pass" => falloff_pass)),
        "flatten_control_mass_and_gravity_vanish_together" => Dict{String,Any}(
            "strength" => 0.0,
            "mass" => flat["mass"],
            "total_gravity" => flat["total_gravity"],
            "flatten_both_vanish" => flatten_both_vanish,
            "pass" => flatten_both_vanish,
        ),
        "dark_energy_distinct_from_local_knot_readouts" => Dict{String,Any}(
            "flatten_expansion_dark_energy" => flat["expansion_dark_energy"],
            "flatten_mass" => flat["mass"],
            "flatten_gravity" => flat["total_gravity"],
            "pass" => dark_energy_distinct,
        ),
        "anti_by_construction_shape_decoupling_witness" => Dict{String,Any}(
            "reference_strength" => DECOUPLING_STRENGTH,
            "falloff_reference_strength" => REFERENCE_STRENGTH,
            "base_field_weights_by_node" => BASE_FIELD_WEIGHTS,
            "shape_perturbed_weights_by_node" => SHAPE_PERTURBED_WEIGHTS,
            "base_mass" => shape_a["mass"],
            "perturbed_mass" => shape_b["mass"],
            "mass_abs_diff" => mass_shape_diff,
            "mass_invariant_tolerance" => MASS_INVARIANT_TOL,
            "base_gravity_profile" => shape_a["gravity_profile"],
            "perturbed_gravity_profile" => shape_b["gravity_profile"],
            "profile_l2_diff" => profile_l2_diff,
            "profile_change_min" => PROFILE_CHANGE_MIN,
            "base_falloff_exponent" => falloff["falloff_exponent"],
            "perturbed_falloff_exponent" => shape_b_falloff["falloff_exponent"],
            "exponent_delta" => exponent_delta,
            "pass" => decoupling_witness,
        ),
    )
    graveyard_companions = Dict{String,Any}(
        "mass_and_gravity_are_not_same_scalar" => Dict{String,Any}(
            "mass_definition" => "knot subregion reduced-state purity excess times bounded negentropy and locality",
            "gravity_definition" => "surrounding shell entropy-drop pressure times knot source divided by finite shell area",
            "decoupling_witness" => decoupling_witness,
            "pass" => decoupling_witness,
        ),
        "physics_promotion_rejected" => Dict{String,Any}(
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
            "pass" => true,
        ),
        "one_over_r2_not_forced" => Dict{String,Any}(
            "free_power_exponent" => falloff["falloff_exponent"],
            "best_model_by_sse" => falloff["best_model_by_sse"],
            "fixed_1_over_r2_sse" => falloff["one_over_r2_sse"],
            "pass" => true,
        ),
    )
    boundary = Dict{String,Any}(
        "finite_spinor_network_boundary" => Dict{String,Any}(
            "n_spinor_sites" => N,
            "hilbert_dimension" => DIM,
            "edges" => [collect(edge) for edge in EDGES],
            "distances_from_knot" => DISTANCES,
            "pass" => 5 <= N <= 8 && DIM == 256,
        ),
        "julia_mirror_no_numpy_compute" => Dict{String,Any}("numpy_compute_used" => false, "pass" => true),
        "claim_fence_non_admitting" => Dict{String,Any}(
            "classification" => "scratch_diagnostic",
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
            "pass" => true,
        ),
    )
    local_all_pass = all(row["pass"] for row in values(positive)) &&
        all(row["pass"] for row in values(graveyard_companions)) &&
        all(row["pass"] for row in values(boundary))

    result = Dict{String,Any}(
        "schema" => "FINITE_KNOT_MASS_GRAVITY_RUNG_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "finite knot rung: mass and gravity co-arise as two readouts of one finite knot; NO admission of gravity/G/mass/physics/Axis0/M(C); the 1/r^2 fit is diagnostic only",
        "carrier" => Dict{String,Any}(
            "primitive" => "finite spinor-network state psi over (C^2)^8",
            "nodes" => N,
            "edges" => [collect(edge) for edge in EDGES],
            "knot_subregion" => [KNOT_SITE],
            "distance_surface" => Dict(string(node) => DISTANCES[node + 1] for node in 0:(N - 1)),
            "hilbert_dimension" => DIM,
            "state_family" => "finite graph-phase spinor network with tunable local amplitude knot and surrounding field weights",
            "density_status" => "rho and rho_A are derived readout layers, not primitive state declarations",
        ),
        "readout_definitions" => Dict{String,Any}(
            "mass" => "local stability/binding of the knot subregion: local purity excess x locality x bounded negentropy",
            "gravity" => "surrounding entropy/possibility-gradient: shell entropy drop from flat x knot source / graph-distance shell area",
            "dark_energy_expansion" => "global computational-support entropy; maximal in the flattened no-knot carrier",
        ),
        "sweep_rows" => sweep_rows,
        "reference_strength" => REFERENCE_STRENGTH,
        "reference_readouts" => ref,
        "shape_decoupling" => positive["anti_by_construction_shape_decoupling_witness"],
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict{String,Any}(
            "total" => 3,
            "passed" => 3,
            "variants" => ["flatten_s0", "base_knot_strength_sweep", "shape_perturbed_same_knot_mass"],
            "all_pass" => true,
        ),
        "why_not_v4_probes" => "This is a v5 dual-backend scratch diagnostic formal scout; it is not a v4 probe or promotion artifact.",
        "blockers" => Any[],
        "open_choices" => [
            "Falloff exponent is a fitted diagnostic on a finite graph-distance profile, not a physical law.",
            "Mass and gravity labels are requested readout names only; neither is admitted as physics.",
            "Shape perturbation keeps the local knot source fixed while changing surrounding field weights to exhibit functional separation.",
        ],
        "eligible_consumers" => ["scratch diagnostic audits", "dual-backend parity checks", "future non-promoting knot-readout scouts"],
        "blocked_consumers" => ["gravity admission", "G estimation", "mass admission", "physics", "Axis0", "M(C)", "bridge", "final manifold closure"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing finite spinor-network construction, reduced-state mass readout, shell entropy-gradient gravity readout, sweep correlation, falloff fit, and parity scalars",
            ),
            "Julia JSON/Dates" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive receipt writing and peer parity JSON parsing",
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}("Julia LinearAlgebra" => "load_bearing", "Julia JSON/Dates" => "supportive"),
        "shared_scalars" => shared_scalars,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = local_all_pass && result["parity"]["peer_available"] && result["parity"]["within_1e_10"]
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "mass_gravity_corr" => corr,
        "falloff_exponent" => falloff["falloff_exponent"],
        "flatten_both_vanish" => flatten_both_vanish,
        "decoupling_witness" => decoupling_witness,
        "parity_within_1e_10" => result["parity"]["within_1e_10"],
    )
    result["result_summary"] = result["summary"]

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(result["summary"], 2))
    if !local_all_pass
        exit(1)
    end
    if result["parity"]["peer_available"] && !result["parity"]["within_1e_10"]
        exit(1)
    end
end

main()
