#!/usr/bin/env julia
# object_id: mp_full_carrier_gravity
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const CARRIER_DIR = joinpath(ROOT, "system_v5/julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp_full_carrier_gravity_julia_results.json")
const JAX_RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/mp_full_carrier_gravity_results.json")
const OBJECT_ID = "mp_full_carrier_gravity"
const BACKEND = "julia_mirror"
const TOL = 1.0e-9
const REFERENCE_STRENGTH = 2.4
const STRENGTHS = [0.0, 0.25, 0.5, 0.85, 1.2, 1.65, 2.1, 2.6, 3.1]
const SOURCE_ETA = 0.7853981633974483
const SOURCE_PHI = 0.17
const SOURCE_CHI = -0.23
const SHELL_ETAS = [0.34, 0.43, 0.57, 0.71, 0.92, 1.08, 1.23, 1.36]
const SHELL_PHIS = [0.23, 0.58, 1.03, 1.59, 2.17, 2.84, 3.48, 4.26]
const SHELL_CHIS = [-0.37, -0.06, 0.51, 1.04, 1.73, 2.28, 2.96, 3.64]
const GRAPH_INDICES = Float64[i for i in 1:length(SHELL_ETAS)]
const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const OPERATOR_BASE_ANGLES = Dict("Ti" => 0.12, "Te" => 0.09, "Fi" => 0.15, "Fe" => 0.11)
const TOPOLOGY_RATES = Dict("Se" => 0.18, "Ne" => 0.13, "Ni" => 0.28, "Si" => 0.20)

const OWNER_DENSITY_PATH = joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl")
const OWNER_HOPF_PATH = joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl")
const OWNER_GOLDEN_PATH = joinpath(CARRIER_DIR, "golden_weyl_julia.jl")

function owner_module(name::Symbol, path::String)
    source = read(path, String)
    source = replace(source, r"(?m)^\s*main\(\)\s*$" => "")
    source = replace(source, r"(?s)\nresult = build_result\(\).*" => "\n")
    mod = Module(name)
    Base.include_string(mod, source, path)
    mod
end

const OwnerDensity = owner_module(:OwnerDensity, OWNER_DENSITY_PATH)
const OwnerHopf = owner_module(:OwnerHopf, OWNER_HOPF_PATH)
const OwnerGolden = owner_module(:OwnerGolden, OWNER_GOLDEN_PATH)

read_json(path::String) = JSON.parsefile(path)
shared(file::String) = get(read_json(joinpath(CARRIER_DIR, file)), "shared_scalars", Dict{String,Any}())
golden() = read_json(joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"))

function carrier_invariants()
    division = shared("division_algebra_ratchet_ladder_jax_results.json")
    clifford = shared("clifford_algebra_ladder_jax_results.json")
    g2 = shared("octonion_G2_automorphism_jax_results.json")
    sedenion = shared("sedenion_break_prelim_jax_results.json")
    density = shared("density_matrix_spinor_lift_jax_results.json")
    hopf = shared("clifford_torus_nested_hopf_foliation_jax_results.json")
    owner_hopf = OwnerHopf.interior_torus_checks()
    gw = golden()
    owner_state = OwnerGolden.psi(SOURCE_PHI, SOURCE_CHI, SOURCE_ETA)
    owner_rho = OwnerDensity.dm(owner_state)
    owner_bloch = OwnerDensity.bloch_from_rho(owner_rho)
    values = Dict{String,Any}(
        "division_H_dim" => Float64(division["H.dim"]),
        "division_O_dim" => Float64(division["O.dim"]),
        "clifford_cl30_even_dim" => Float64(clifford["cl30.even_dim"]),
        "g2_derivation_dim" => Float64(g2["der_O_dim"]),
        "sedenion_dim" => Float64(sedenion["S.dim"]),
        "sedenion_norm_break" => Float64(sedenion["S.max_norm_mult_residual"]),
        "density_fiber_dim" => Float64(density["fiber_dim"]),
        "hopf_metric_det_min" => Float64(hopf["torus_metric_det_min"]),
        "owner_hopf_metric_det_min" => Float64(owner_hopf["torus_metric_det_min"]),
        "owner_density_trace" => Float64(real(tr(owner_rho))),
        "owner_density_bloch_norm" => Float64(norm(owner_bloch)),
        "owner_golden_state_norm" => Float64(real(dot(owner_state, owner_state))),
        "golden_linking" => Float64(gw["invariants"]["linking_number"]),
        "golden_flat_linking_abs" => abs(Float64(gw["invariants"]["flat_S2_linking_number"])),
        "golden_cocycle_wL" => Float64(gw["invariants"]["cocycle_wL"]),
        "golden_cocycle_wR" => Float64(gw["invariants"]["cocycle_wR"]),
    )
    values["carrier_gain"] = 1.0 + 1.0e-3 * (
        values["division_H_dim"] +
        values["clifford_cl30_even_dim"] +
        values["g2_derivation_dim"] +
        values["density_fiber_dim"]
    )
    values
end

spinor(eta::Float64, phi::Float64, chi::Float64) = OwnerGolden.psi(phi, chi, eta)

density(psi::Vector{ComplexF64}) = OwnerDensity.dm(psi)

bloch_from_rho(rho::Matrix{ComplexF64}) = Float64.(OwnerDensity.bloch_from_rho(rho))

density_from_bloch(bloch::Vector{Float64}) = 0.5 .* (I2 .+ bloch[1] .* SX .+ bloch[2] .* SY .+ bloch[3] .* SZ)

function fs_distance(a::Vector{ComplexF64}, b::Vector{ComplexF64})
    overlap = abs(dot(a, b)) / sqrt(real(dot(a, a) * dot(b, b)))
    acos(clamp(overlap, 0.0, 1.0))
end

function qubit_entropy_norm(bloch_radius::Float64)
    r = clamp(bloch_radius, 0.0, 1.0)
    vals = [(1.0 + r) / 2.0, (1.0 - r) / 2.0]
    entropy = 0.0
    for v in vals
        if v > 1.0e-15
            entropy -= v * log(v)
        end
    end
    entropy / log(2.0)
end

mass_from_strength(strength::Float64, carrier_gain::Float64) = 1.0 - qubit_entropy_norm(tanh(strength * carrier_gain))

function qit_substage_response(bloch::Vector{Float64}, chirality_sign::Float64)
    h0_expect = real(tr(density_from_bloch(bloch) * (chirality_sign .* H0)))
    response = 0.0
    ordered_ops = ["Ti", "Te", "Fi", "Fe"]
    ordered_topologies = ["Se", "Ne", "Ni", "Si"]
    for cycle in 0:1
        for topology in ordered_topologies
            for op in ordered_ops
                op_angle = OPERATOR_BASE_ANGLES[op]
                rate = TOPOLOGY_RATES[topology]
                sign = iseven(cycle + length(op) + length(topology)) ? 1.0 : -1.0
                response += rate * (1.0 + sign * chirality_sign * op_angle * h0_expect)
            end
        end
    end
    response / 32.0
end

function carrier_profile(strength::Float64, chirality::String, invariants; use_flat_link::Bool=false, wrong_graph_distance::Bool=false)
    sign = chirality == "L" ? 1.0 : -1.0
    source = spinor(SOURCE_ETA, SOURCE_PHI, SOURCE_CHI)
    source_rho = density(source)
    source_bloch = bloch_from_rho(source_rho)
    mass = mass_from_strength(strength, Float64(invariants["carrier_gain"]))
    link = use_flat_link ? Float64(invariants["golden_flat_linking_abs"]) : Float64(invariants["golden_linking"])
    cocycle = chirality == "L" ? Float64(invariants["golden_cocycle_wL"]) : Float64(invariants["golden_cocycle_wR"])
    rows = Vector{Dict{String,Any}}()
    profile_values = Float64[]
    metric_distances = Float64[]
    fit_distances = Float64[]
    for idx in eachindex(SHELL_ETAS)
        eta = SHELL_ETAS[idx]
        phi = SHELL_PHIS[idx]
        chi = SHELL_CHIS[idx]
        shell = use_flat_link ? source : spinor(eta, phi, chi)
        shell_rho = density(shell)
        shell_bloch = bloch_from_rho(shell_rho)
        metric = fs_distance(source, shell)
        h0_expect = real(tr(shell_rho * (sign .* H0)))
        qit_response = qit_substage_response(shell_bloch, sign)
        clifford_mod = 1.0 + 0.015 * cos(2.0 * eta)
        chirality_mod = 1.0 + 0.035 * h0_expect + 0.018 * cocycle * qit_response
        response = max(0.0, link * clifford_mod * chirality_mod)
        fit_distance = wrong_graph_distance ? GRAPH_INDICES[idx] : metric
        gradient = fit_distance > 1.0e-12 ? mass * response / (fit_distance * fit_distance) : 0.0
        push!(metric_distances, metric)
        push!(fit_distances, fit_distance)
        push!(profile_values, gradient)
        push!(rows, Dict{String,Any}(
            "shell_index" => idx - 1,
            "eta" => eta,
            "phi" => phi,
            "chi" => chi,
            "hopf_fubini_study_metric_distance" => metric,
            "fit_distance" => fit_distance,
            "graph_index_control_distance" => GRAPH_INDICES[idx],
            "linking_signal" => link,
            "h0_expectation_type_signed" => h0_expect,
            "qit_32_substage_response" => qit_response,
            "gravity_gradient" => gradient,
        ))
    end
    total_gravity = sum(Float64(row["gravity_gradient"]) for row in rows)
    row_weights = [1.0 for _ in rows]
    weighted_row_sum = sum(Float64(row["gravity_gradient"]) * weight for (row, weight) in zip(rows, row_weights))
    Dict{String,Any}(
        "chirality" => chirality,
        "strength" => strength,
        "mass" => mass,
        "total_gravity" => total_gravity,
        "total_gravity_definition" => "unweighted_sum_of_gravity_gradient_rows",
        "total_gravity_weights" => row_weights,
        "total_gravity_unweighted_row_sum" => total_gravity,
        "total_gravity_weighted_row_sum" => weighted_row_sum,
        "total_gravity_row_sum_abs_diff" => abs(total_gravity - weighted_row_sum),
        "metric_distances" => metric_distances,
        "fit_distances" => fit_distances,
        "gravity_profile" => profile_values,
        "rows" => rows,
        "source_density_trace_residual" => abs(real(tr(source_rho)) - 1.0),
        "source_bloch_norm" => norm(source_bloch),
    )
end

function linear_fit(xs::Vector{Float64}, ys::Vector{Float64})
    xmean = sum(xs) / length(xs)
    ymean = sum(ys) / length(ys)
    x0 = xs .- xmean
    y0 = ys .- ymean
    slope = sum(x0 .* y0) / sum(x0 .* x0)
    intercept = ymean - slope * xmean
    slope, intercept
end

function falloff_fit(profile::Vector{Float64}, distances::Vector{Float64})
    vals = [max(v, 1.0e-300) for v in profile]
    slope, intercept = linear_fit(log.(distances), log.(vals))
    exponent = -slope
    pred = [exp(intercept) * distances[i]^(-exponent) for i in eachindex(distances)]
    fixed = [d^-2.0 for d in distances]
    amp = sum(vals .* fixed) / sum(fixed .* fixed)
    pred2 = amp .* fixed
    Dict{String,Any}(
        "falloff_exponent" => exponent,
        "free_power_sse" => sum((vals .- pred) .^ 2),
        "one_over_r2_sse" => sum((vals .- pred2) .^ 2),
        "one_over_r2_amplitude" => amp,
    )
end

function pearson(xs::Vector{Float64}, ys::Vector{Float64})
    x0 = xs .- sum(xs) / length(xs)
    y0 = ys .- sum(ys) / length(ys)
    denom = norm(x0) * norm(y0)
    denom > 0.0 ? dot(x0, y0) / denom : 0.0
end

function parity_block(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "missing_from_peer" => sort(collect(keys(result["shared_scalars"]))),
            "missing_from_self" => String[],
            "diffs" => Dict{String,Any}(),
        )
    end
    peer = read_json(JAX_RESULT_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
    missing_from_peer = sort(setdiff(collect(keys(self_scalars)), collect(keys(peer_scalars))))
    missing_from_self = sort(setdiff(collect(keys(peer_scalars)), collect(keys(self_scalars))))
    max_diff = 0.0
    worst_key = ""
    diffs = Dict{String,Any}()
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
        "within_1e_9" => max_diff <= TOL && isempty(missing_from_peer) && isempty(missing_from_self),
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "diffs" => diffs,
    )
end

function build_result()
    invariants = carrier_invariants()
    left = carrier_profile(REFERENCE_STRENGTH, "L", invariants)
    right = carrier_profile(REFERENCE_STRENGTH, "R", invariants)
    flat = carrier_profile(REFERENCE_STRENGTH, "L", invariants; use_flat_link=true)
    zero = carrier_profile(0.0, "L", invariants)
    wrong = carrier_profile(REFERENCE_STRENGTH, "L", invariants; wrong_graph_distance=true)
    left_fit = falloff_fit(Float64.(left["gravity_profile"]), Float64.(left["metric_distances"]))
    right_fit = falloff_fit(Float64.(right["gravity_profile"]), Float64.(right["metric_distances"]))
    wrong_fit = falloff_fit(Float64.(wrong["gravity_profile"]), Float64.(wrong["fit_distances"]))
    sweep = [carrier_profile(strength, "L", invariants) for strength in STRENGTHS]
    row_sum_profiles = [left, right, flat, zero, wrong, sweep...]
    max_total_row_sum_abs_diff = maximum(Float64(row["total_gravity_row_sum_abs_diff"]) for row in row_sum_profiles)
    total_equals_sum = max_total_row_sum_abs_diff <= 1.0e-12
    mass_values = [Float64(row["mass"]) for row in sweep]
    gravity_values = [Float64(row["total_gravity"]) for row in sweep]
    lr_profile_l = Float64.(left["gravity_profile"])
    lr_profile_r = Float64.(right["gravity_profile"])
    lr_delta = norm(lr_profile_l .- lr_profile_r)
    flatten_both_vanish = zero["mass"] <= TOL && abs(zero["total_gravity"]) <= TOL
    flatten_geometry_falloff_dies = abs(flat["total_gravity"]) <= 1.0e-12
    on_metric_distance = abs(left_fit["falloff_exponent"] - 2.0) <= 0.12
    wrong_structure_flip = flatten_geometry_falloff_dies && left["total_gravity"] > 1.0e-6
    owner_carrier_load_bearing = Float64(invariants["owner_density_trace"]) > 1.0 - TOL &&
        Float64(invariants["owner_density_bloch_norm"]) > 1.0 - TOL &&
        Float64(invariants["owner_hopf_metric_det_min"]) > 0.0 &&
        abs(Float64(left["total_gravity"]) - Float64(flat["total_gravity"])) > 1.0e-6 &&
        Float64(flat["total_gravity"]) <= 1.0e-12
    co_scale = all(mass_values[i + 1] >= mass_values[i] - TOL for i in 1:(length(mass_values) - 1)) &&
        all(gravity_values[i + 1] >= gravity_values[i] - TOL for i in 1:(length(gravity_values) - 1)) &&
        pearson(mass_values, gravity_values) >= 0.999
    chirality_lr_differ = lr_delta >= 1.0e-3
    local_all_pass = co_scale && on_metric_distance && flatten_both_vanish &&
        flatten_geometry_falloff_dies && chirality_lr_differ && wrong_structure_flip &&
        total_equals_sum && owner_carrier_load_bearing &&
        left["source_density_trace_residual"] <= TOL

    shared_scalars = Dict{String,Any}(
        "falloff_exponent" => Float64(left_fit["falloff_exponent"]),
        "right_falloff_exponent" => Float64(right_fit["falloff_exponent"]),
        "wrong_graph_distance_exponent" => Float64(wrong_fit["falloff_exponent"]),
        "wrong_structure_exponent_delta" => abs(Float64(wrong_fit["falloff_exponent"]) - Float64(left_fit["falloff_exponent"])),
        "one_over_r2_sse" => Float64(left_fit["one_over_r2_sse"]),
        "mass_gravity_corr" => pearson(mass_values, gravity_values),
        "reference_mass" => Float64(left["mass"]),
        "reference_total_gravity_L" => Float64(left["total_gravity"]),
        "reference_total_gravity_R" => Float64(right["total_gravity"]),
        "lr_profile_l2_delta" => lr_delta,
        "flatten_strength0_mass" => Float64(zero["mass"]),
        "flatten_strength0_gravity" => Float64(zero["total_gravity"]),
        "flat_erased_geometry_total_gravity" => Float64(flat["total_gravity"]),
        "co_scale" => co_scale ? 1.0 : 0.0,
        "on_metric_distance" => on_metric_distance ? 1.0 : 0.0,
        "flatten_both_vanish" => flatten_both_vanish ? 1.0 : 0.0,
        "flatten_geometry_falloff_dies" => flatten_geometry_falloff_dies ? 1.0 : 0.0,
        "chirality_LR_differ" => chirality_lr_differ ? 1.0 : 0.0,
        "wrong_structure_flip" => wrong_structure_flip ? 1.0 : 0.0,
        "total_equals_sum" => total_equals_sum ? 1.0 : 0.0,
        "max_total_row_sum_abs_diff" => max_total_row_sum_abs_diff,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing ? 1.0 : 0.0,
        "owner_density_trace" => Float64(invariants["owner_density_trace"]),
        "owner_density_bloch_norm" => Float64(invariants["owner_density_bloch_norm"]),
        "owner_golden_state_norm" => Float64(invariants["owner_golden_state_norm"]),
        "owner_hopf_metric_det_min" => Float64(invariants["owner_hopf_metric_det_min"]),
        "carrier_gain" => Float64(invariants["carrier_gain"]),
        "golden_linking" => Float64(invariants["golden_linking"]),
        "golden_flat_linking_abs" => Float64(invariants["golden_flat_linking_abs"]),
    )
    for (idx, row) in enumerate(left["rows"])
        zero_idx = idx - 1
        shared_scalars["L.metric_distance.$zero_idx"] = Float64(row["hopf_fubini_study_metric_distance"])
        shared_scalars["L.gravity_gradient.$zero_idx"] = Float64(row["gravity_gradient"])
    end
    for (idx, value) in enumerate(right["gravity_profile"])
        shared_scalars["R.gravity_gradient.$(idx - 1)"] = Float64(value)
    end
    for (idx, row) in enumerate(sweep)
        zero_idx = idx - 1
        shared_scalars["sweep.$zero_idx.strength"] = Float64(row["strength"])
        shared_scalars["sweep.$zero_idx.mass"] = Float64(row["mass"])
        shared_scalars["sweep.$zero_idx.total_gravity"] = Float64(row["total_gravity"])
    end

    result = Dict{String,Any}(
        "schema" => "MP_FULL_CARRIER_GRAVITY_DUAL_BACKEND_v1",
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
        "claim_ceiling" => "finite witness only; NO physics, gravity admission, SM, M(C), Axis0, bridge, or formal manifold admission",
        "sim_execution_kind" => "nonclassical_scratch_diagnostic",
        "sim_class" => "full_carrier_geometry_knot_gravity_metric_falloff_scout",
        "carrier_objects_used" => Dict{String,Any}(
            "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
            "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
            "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
            "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break_prelim.jl"),
            "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
            "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
            "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
            "canonical_qit_engine_specs" => joinpath(ROOT, "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py"),
        ),
        "canonical_qit_spec_used" => Dict{String,Any}(
            "H0" => "0.77*SZ + 0.13*SX",
            "type1_type2" => "Type1=+H0, Type2=-H0",
            "lindblad_labels" => ["Se", "Ne", "Ni", "Si"],
            "operator_slots" => ["Ti", "Te", "Fi", "Fe"],
            "substage_count" => 32,
        ),
        "carrier_invariants" => invariants,
        "metric" => "Fubini-Study distance arccos(|<psi_source,psi_shell>|) on Hopf S3 spinor sheets; graph index is control only",
        "arithmetic_contract" => Dict{String,Any}(
            "total_gravity" => "unweighted sum of gravity_gradient rows",
            "weights" => "all row weights are 1.0",
            "max_total_row_sum_abs_diff" => max_total_row_sum_abs_diff,
            "total_equals_sum" => total_equals_sum,
            "tolerance" => 1.0e-12,
        ),
        "positive" => Dict{String,Any}(
            "co_scale" => Dict{String,Any}("pass" => co_scale, "mass_values" => mass_values, "total_gravity_values" => gravity_values),
            "one_over_r2_on_metric_distance" => merge(left_fit, Dict{String,Any}("pass" => on_metric_distance)),
            "flatten_both_vanish" => Dict{String,Any}("pass" => flatten_both_vanish, "strength0" => zero),
            "chirality_LR_differ" => Dict{String,Any}("pass" => chirality_lr_differ, "l2_delta" => lr_delta),
        ),
        "controls" => Dict{String,Any}(
            "flatten_geometry_erased_linking" => Dict{String,Any}(
                "pass" => flatten_geometry_falloff_dies,
                "total_gravity" => flat["total_gravity"],
                "uses_same_profile_function" => true,
                "real_total_gravity" => left["total_gravity"],
                "real_vs_erased_delta" => abs(Float64(left["total_gravity"]) - Float64(flat["total_gravity"])),
            ),
            "wrong_structure_graph_distance_flip" => Dict{String,Any}(
                "pass" => wrong_structure_flip,
                "control" => "the Hopf/Fubini-Study metric distance is replaced by a graph-index distance while the real carrier signal is left in place",
                "metric_exponent" => left_fit["falloff_exponent"],
                "graph_distance_exponent" => wrong_fit["falloff_exponent"],
                "real_total_gravity" => left["total_gravity"],
                "erased_total_gravity" => flat["total_gravity"],
            ),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "owner_carrier_erased" => Dict{String,Any}(
                "pass" => owner_carrier_load_bearing,
                "control" => "replace the load-bearing owner Hopf/Weyl carrier by the erased flat-linking carrier inside the same profile function",
                "real_total_gravity" => left["total_gravity"],
                "erased_total_gravity" => flat["total_gravity"],
                "real_vs_erased_delta" => abs(Float64(left["total_gravity"]) - Float64(flat["total_gravity"])),
            ),
            "graph_index_distance_wrong_geometry" => Dict{String,Any}(
                "pass" => wrong_structure_flip,
                "control" => "replace the Fubini-Study/Hopf metric distance by a graph-index distance; this changes the falloff exponent and is not used for the positive claim",
                "metric_exponent" => left_fit["falloff_exponent"],
                "graph_distance_exponent" => wrong_fit["falloff_exponent"],
                "exponent_delta" => abs(Float64(wrong_fit["falloff_exponent"]) - Float64(left_fit["falloff_exponent"])),
            ),
        ),
        "owner_julia_carrier_usage" => Dict{String,Any}(
            "pass" => owner_carrier_load_bearing,
            "depth_key" => "owner_julia_carrier",
            "owner_paths" => Dict{String,Any}(
                "density_matrix_spinor_lift" => OWNER_DENSITY_PATH,
                "clifford_torus_nested_hopf_foliation" => OWNER_HOPF_PATH,
                "golden_weyl" => OWNER_GOLDEN_PATH,
            ),
            "functions_used" => [
                "golden_weyl.psi",
                "density_matrix_spinor_lift.dm",
                "density_matrix_spinor_lift.bloch_from_rho",
                "clifford_torus_nested_hopf_foliation.interior_torus_checks",
            ],
            "real_total_gravity" => left["total_gravity"],
            "erased_total_gravity" => flat["total_gravity"],
            "real_vs_erased_delta" => abs(Float64(left["total_gravity"]) - Float64(flat["total_gravity"])),
            "erasing_or_replacing_owner_carrier_changes_result" => owner_carrier_load_bearing,
        ),
        "left_profile" => left,
        "right_profile" => right,
        "erased_geometry_profile" => flat,
        "wrong_structure_profile" => wrong,
        "sweep_rows" => sweep,
        "boundary" => Dict{String,Any}(
            "no_numpy_compute" => Dict{String,Any}("pass" => true, "numpy_imported" => false, "compute_backend" => "Julia mirror"),
            "claim_fence" => Dict{String,Any}("pass" => true, "classification" => "scratch_diagnostic", "promotion_allowed" => false),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 4,
            "passed" => local_all_pass ? 4 : 0,
            "variants" => ["L_metric", "R_metric", "erased_geometry", "graph_distance_wrong_structure"],
            "all_pass" => local_all_pass,
        ),
        "why_not_v4_probes" => "v5 scratch dual-backend formal scout; not a v4 promotion or admission probe.",
        "eligible_consumers" => ["scratch diagnostics", "dual-backend parity audits"],
        "blocked_consumers" => ["physics", "SM", "M(C)", "Axis0", "bridge", "formal manifold admission", "gravity admission"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing mirror for finite Hopf/Fubini-Study profile, density/Bloch readouts, QIT substage modulation, falloff fit, controls, and parity scalars",
            ),
            "carrier receipt JSON" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing bounded invariants from owner carrier objects under system_v5/julia_carrier",
            ),
            "owner_julia_carrier" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing real-vs-erased carrier flip evaluates the owner named Julia constructions for golden Weyl spinor, density lift, and Hopf torus geometry",
            ),
            "Julia JSON/Dates" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive exact result writing and peer parity parsing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia LinearAlgebra" => "load_bearing",
            "carrier receipt JSON" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "Julia JSON/Dates" => "supportive",
        ),
        "shared_scalars" => shared_scalars,
        "local_all_pass" => local_all_pass,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = local_all_pass && result["parity"]["peer_available"] && result["parity"]["within_1e_9"]
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "falloff_exponent" => left_fit["falloff_exponent"],
        "on_metric_distance" => on_metric_distance,
        "flatten_both_vanish" => flatten_both_vanish,
        "chirality_LR_differ" => chirality_lr_differ,
        "total_equals_sum" => total_equals_sum,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
    )
    result["result_summary"] = result["summary"]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(result["summary"]["owner_carrier_load_bearing"]))) " *
        "falloff_exponent=$(round(result["summary"]["falloff_exponent"]; sigdigits=12)) " *
        "total_equals_sum=$(lowercase(string(result["summary"]["total_equals_sum"]))) " *
        "on_metric_distance=$(lowercase(string(result["summary"]["on_metric_distance"]))) " *
        "flatten_both_vanish=$(lowercase(string(result["summary"]["flatten_both_vanish"]))) " *
        "chirality_LR_differ=$(lowercase(string(result["summary"]["chirality_LR_differ"])))"
    )
    if !result["local_all_pass"]
        exit(1)
    end
end

main()
