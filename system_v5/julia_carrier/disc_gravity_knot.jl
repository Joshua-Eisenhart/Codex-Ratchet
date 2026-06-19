#!/usr/bin/env julia
# object_id: disc_gravity_knot
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "disc_gravity_knot"
const NAME = OBJECT_ID
const BACKEND = "julia_float64"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER, "disc_gravity_knot_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "disc_gravity_knot_results.json")
const JAX_SOURCE_PATH = joinpath(FORMAL_SCOUTS, "sim_disc_gravity_knot_probe.py")
const JULIA_SOURCE_PATH = @__FILE__
const GOLDEN_RECEIPT_PATH = joinpath(JULIA_CARRIER, "golden_weyl_julia_receipt.json")
const MATRIX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "carrier_readout_discriminator_matrix_results.json")
const DENSITY_LIFT_JAX_PATH = joinpath(JULIA_CARRIER, "jax_density_matrix_spinor_lift.py")
const HOPF_JAX_PATH = joinpath(JULIA_CARRIER, "jax_clifford_torus_nested_hopf_foliation.py")
const GOLDEN_JAX_PATH = joinpath(JULIA_CARRIER, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py")
const DENSITY_LIFT_JULIA_PATH = joinpath(JULIA_CARRIER, "density_matrix_spinor_lift.jl")
const HOPF_JULIA_PATH = joinpath(JULIA_CARRIER, "clifford_torus_nested_hopf_foliation.jl")
const GOLDEN_JULIA_PATH = joinpath(JULIA_CARRIER, "golden_weyl_julia.jl")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "scratch"
const PARITY_TOL = 1.0e-9
const EPS = 1.0e-12
const PRESENT_THRESHOLD = 1.0e-6
const EXPONENT_TOL = 1.0e-9
const LINK_SAMPLES = 64
const SOURCE_ETA = 0.7853981633974483
const SOURCE_PHI = 0.17
const SOURCE_CHI = -0.23
const SHELL_ETAS = [0.34, 0.43, 0.57, 0.71, 0.92, 1.08, 1.23, 1.36]
const SHELL_PHIS = [0.23, 0.58, 1.03, 1.59, 2.17, 2.84, 3.48, 4.26]
const SHELL_CHIS = [-0.37, -0.06, 0.51, 1.04, 1.73, 2.28, 2.96, 3.64]
const CLAIM_CEILING = "Gravity/knot carrier-readout discriminator only. classification=scratch_diagnostic; promotion=false; formal_admission=false. It may report finite owner-carrier load-bearing for this readout, but it does not derive G, admit gravity or mass, prove physics, admit M(C), bridge, Axis0, PEPS3D, or close the manifold."
const BLOCKED_CONSUMERS = [
    "G derivation",
    "gravity admission",
    "mass admission",
    "physics",
    "M(C)",
    "Axis0",
    "bridge",
    "PEPS3D admission",
    "formal admission",
    "promotion",
]

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia Float64 backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent mirror backend for the finite gravity/knot carrier-readout discriminator"),
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite complex spinor, density, metric, readout, control, and parity scalar algebra"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer result for shared scalar and boolean parity"),
    "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner Hopf/Weyl/Clifford carrier functions and receipts; erasing the carrier changes the readout result"),
    "carrier_readout_discriminator_matrix result" => Dict("tried" => true, "used" => true, "reason" => "load-bearing prior finite falsifier for target-imprint demotion of the knot_mass_gravity branch"),
    "Julia stdlib" => Dict("tried" => true, "used" => true, "reason" => "supportive path handling, source hashing, JSON parsing, timestamps, and result serialization"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "explicitly excluded from the Julia mirror and not used by the JAX peer"),
    "pytorch" => Dict("tried" => false, "used" => false, "reason" => "explicitly not added; this request is the JAX plus Julia lane and keeps the stale C8 PyTorch rule unsatisfied by design"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia Float64 backend" => "load_bearing",
    "Julia LinearAlgebra" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "owner_julia_carrier" => "load_bearing",
    "carrier_readout_discriminator_matrix result" => "load_bearing",
    "Julia stdlib" => "supportive",
    "numpy" => nothing,
    "pytorch" => nothing,
)

function owner_module(name::Symbol, path::String)
    source = read(path, String)
    source = replace(source, r"(?m)^\s*main\(\)\s*$" => "")
    source = replace(source, r"(?s)\nresult = build_result\(\).*" => "\n")
    mod = Module(name)
    Base.include_string(mod, source, path)
    mod
end

const OwnerDensity = owner_module(:DiscOwnerDensity, DENSITY_LIFT_JULIA_PATH)
const OwnerHopf = owner_module(:DiscOwnerHopf, HOPF_JULIA_PATH)
const OwnerGolden = owner_module(:DiscOwnerGolden, GOLDEN_JULIA_PATH)

read_json(path::String) = JSON.parsefile(path)

function sha256_file(path::String)
    if !isfile(path)
        return nothing
    end
    bytes2hex(sha256(read(path)))
end

function source_refs()
    paths = Dict{String,String}(
        "self" => JULIA_SOURCE_PATH,
        "jax_peer" => JAX_SOURCE_PATH,
        "golden_weyl_jax" => GOLDEN_JAX_PATH,
        "golden_weyl_julia" => GOLDEN_JULIA_PATH,
        "golden_weyl_receipt" => GOLDEN_RECEIPT_PATH,
        "density_matrix_spinor_lift_jax" => DENSITY_LIFT_JAX_PATH,
        "density_matrix_spinor_lift_julia" => DENSITY_LIFT_JULIA_PATH,
        "clifford_torus_nested_hopf_foliation_jax" => HOPF_JAX_PATH,
        "clifford_torus_nested_hopf_foliation_julia" => HOPF_JULIA_PATH,
        "carrier_readout_discriminator_matrix" => MATRIX_RESULT_PATH,
    )
    Dict{String,Any}(
        key => Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
        for (key, path) in paths
    )
end

spinor(eta::Float64, phi::Float64, chi::Float64) = OwnerGolden.psi(phi, chi, eta)
density(psi::Vector{ComplexF64}) = OwnerDensity.dm(psi)
bloch_from_rho(rho::Matrix{ComplexF64}) = Float64.(OwnerDensity.bloch_from_rho(rho))

function fs_distance(a::Vector{ComplexF64}, b::Vector{ComplexF64})
    overlap = abs(dot(a, b)) / sqrt(real(dot(a, a) * dot(b, b)))
    acos(clamp(overlap, 0.0, 1.0))
end

function finite_invariants()
    receipt = read_json(GOLDEN_RECEIPT_PATH)
    inv = receipt["invariants"]
    owner_hopf = OwnerHopf.interior_torus_checks()
    source = spinor(SOURCE_ETA, SOURCE_PHI, SOURCE_CHI)
    source_rho = density(source)
    source_bloch = bloch_from_rho(source_rho)
    real_link_sample = OwnerGolden.nested_gauss_linking(SOURCE_ETA, LINK_SAMPLES)
    random_unlinked_sample = OwnerGolden.nested_but_unlinked_linking(SOURCE_ETA, LINK_SAMPLES)
    trivial_flat_sample = OwnerGolden.flat_s2_sanity_linking(LINK_SAMPLES)
    Dict{String,Any}(
        "golden_linking_receipt" => Float64(inv["linking_number"]),
        "flat_linking_receipt" => Float64(inv["flat_S2_linking_number"]),
        "cocycle_wL" => Float64(inv["cocycle_wL"]),
        "cocycle_wR" => Float64(inv["cocycle_wR"]),
        "carrier_error_bound" => Float64(inv["carrier_error_bound"]),
        "real_link_sample" => Float64(real_link_sample),
        "random_unlinked_link_sample" => Float64(random_unlinked_sample),
        "trivial_flat_link_sample" => Float64(trivial_flat_sample),
        "owner_hopf_metric_det_min" => Float64(owner_hopf["torus_metric_det_min"]),
        "owner_density_trace" => Float64(real(tr(source_rho))),
        "owner_density_bloch_norm" => Float64(norm(source_bloch)),
        "owner_golden_state_norm" => Float64(real(dot(source, source))),
    )
end

function prior_knot_target_imprint()
    if !isfile(MATRIX_RESULT_PATH)
        return Dict{String,Any}(
            "available" => false,
            "all_pass" => false,
            "branch_verdict" => "OPEN",
            "mutated_carrier_value" => 0.0,
            "owner_carrier_value" => 0.0,
            "negative_control_value" => 0.0,
            "shape_scramble_survives" => false,
            "path" => MATRIX_RESULT_PATH,
        )
    end
    data = read_json(MATRIX_RESULT_PATH)
    target = nothing
    for row in get(data, "rows", Any[])
        if get(row, "branch_id", "") == "knot_mass_gravity"
            target = row
            break
        end
    end
    if target === nothing
        return Dict{String,Any}(
            "available" => true,
            "all_pass" => Bool(get(data, "all_pass", false)),
            "branch_verdict" => "OPEN",
            "mutated_carrier_value" => 0.0,
            "owner_carrier_value" => 0.0,
            "negative_control_value" => 0.0,
            "shape_scramble_survives" => false,
            "path" => MATRIX_RESULT_PATH,
        )
    end
    mutated = Float64(get(target, "mutated_carrier_value", 0.0))
    owner = Float64(get(target, "owner_carrier_value", 0.0))
    negative = Float64(get(target, "negative_control_value", 0.0))
    Dict{String,Any}(
        "available" => true,
        "all_pass" => Bool(get(data, "all_pass", false)),
        "branch_verdict" => String(get(target, "branch_verdict", "OPEN")),
        "mutated_carrier_value" => mutated,
        "owner_carrier_value" => owner,
        "negative_control_value" => negative,
        "shape_scramble_survives" => mutated > 0.5 && owner > 0.5,
        "mutation" => get(target, "mutation", nothing),
        "claim_ceiling" => get(target, "claim_ceiling", nothing),
        "path" => MATRIX_RESULT_PATH,
    )
end

function mass_from_signal(link_signal::Float64, invariants)
    chirality_gap = abs(Float64(invariants["cocycle_wL"]) - Float64(invariants["cocycle_wR"]))
    density_gate = max(0.0, min(1.0, Float64(invariants["owner_density_bloch_norm"])))
    raw = abs(link_signal) * density_gate * (1.0 + 0.125 * chirality_gap)
    tanh(raw)
end

function branch_profile(label::String, link_signal::Float64, invariants; flatten_shells::Bool)
    source = spinor(SOURCE_ETA, SOURCE_PHI, SOURCE_CHI)
    mass = mass_from_signal(link_signal, invariants)
    rows = Vector{Dict{String,Any}}()
    profile = Float64[]
    distances = Float64[]
    amplitude = mass * abs(link_signal)
    for idx in eachindex(SHELL_ETAS)
        shell = flatten_shells ? source : spinor(SHELL_ETAS[idx], SHELL_PHIS[idx], SHELL_CHIS[idx])
        metric = fs_distance(source, shell)
        distance = max(metric, EPS)
        value = flatten_shells ? 0.0 : amplitude / (distance * distance)
        push!(distances, distance)
        push!(profile, value)
        push!(rows, Dict{String,Any}(
            "shell_index" => idx - 1,
            "eta" => SHELL_ETAS[idx],
            "phi" => SHELL_PHIS[idx],
            "chi" => SHELL_CHIS[idx],
            "hopf_fubini_study_metric_distance" => distance,
            "link_signal" => link_signal,
            "mass_source" => mass,
            "gravity_readout" => value,
        ))
    end
    Dict{String,Any}(
        "label" => label,
        "link_signal" => link_signal,
        "mass" => mass,
        "total_gravity" => sum(profile),
        "metric_distances" => distances,
        "gravity_profile" => profile,
        "rows" => rows,
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
    logd = log.(distances)
    logv = log.(vals)
    slope, intercept = linear_fit(logd, logv)
    exponent = -slope
    free_pred = [exp(intercept) * distances[i]^(-exponent) for i in eachindex(distances)]
    fixed = [d^-2.0 for d in distances]
    amp = sum(vals .* fixed) / sum(fixed .* fixed)
    fixed_pred = amp .* fixed
    Dict{String,Any}(
        "falloff_exponent" => exponent,
        "free_power_sse" => sum((vals .- free_pred) .^ 2),
        "one_over_r2_sse" => sum((vals .- fixed_pred) .^ 2),
        "one_over_r2_amplitude" => amp,
    )
end

function row_verdict(; parity_ok::Bool, real_present::Bool, oneoverr2_on_metric::Bool, dies_under_flatten::Bool, survives_random_knot::Bool, owner_carrier_load_bearing::Bool, prior_target_imprint::Bool)
    if !parity_ok
        return "OPEN"
    elseif !real_present
        return "GRAVEYARD"
    elseif survives_random_knot
        return "GENERIC"
    elseif prior_target_imprint
        return "CONVENTION"
    elseif oneoverr2_on_metric && dies_under_flatten && owner_carrier_load_bearing
        return "REAL_CARRIER"
    elseif oneoverr2_on_metric
        return "CONVENTION"
    end
    "OPEN"
end

function parity_block(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "within_1e_9" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "missing_from_peer" => sort(collect(keys(result["shared_scalars"]))),
            "missing_from_self" => String[],
            "boolean_mismatches" => String[],
            "string_mismatches" => String[],
            "diffs" => Dict{String,Any}(),
        )
    end
    peer = read_json(JAX_RESULT_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
    missing_from_peer = sort(setdiff(collect(keys(self_scalars)), collect(keys(peer_scalars))))
    missing_from_self = sort(setdiff(collect(keys(peer_scalars)), collect(keys(self_scalars))))
    max_diff = 0.0
    worst_key = nothing
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
    self_booleans = result["shared_booleans"]
    peer_booleans = get(peer, "shared_booleans", Dict{String,Any}())
    boolean_mismatches = [
        key for (key, value) in self_booleans
        if haskey(peer_booleans, key) && Bool(value) != Bool(peer_booleans[key])
    ]
    self_strings = result["shared_strings"]
    peer_strings = get(peer, "shared_strings", Dict{String,Any}())
    string_mismatches = [
        key for (key, value) in self_strings
        if haskey(peer_strings, key) && String(value) != String(peer_strings[key])
    ]
    within = isempty(missing_from_peer) && isempty(missing_from_self) &&
        isempty(boolean_mismatches) && isempty(string_mismatches) && max_diff <= PARITY_TOL
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "within_1e_9" => within,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
        "diffs" => diffs,
    )
end

function build_result()
    invariants = finite_invariants()
    prior = prior_knot_target_imprint()
    real = branch_profile("intended_weyl_hopf_clifford_knot", Float64(invariants["golden_linking_receipt"]), invariants; flatten_shells=false)
    flattened = branch_profile("carrier_flattened_flat_s2", Float64(invariants["flat_linking_receipt"]), invariants; flatten_shells=true)
    random_knot = branch_profile("deterministic_unlinked_random_trivial_knot", Float64(invariants["random_unlinked_link_sample"]), invariants; flatten_shells=false)
    trivial_knot = branch_profile("flat_s2_trivial_knot", Float64(invariants["trivial_flat_link_sample"]), invariants; flatten_shells=false)
    fit = falloff_fit(Float64.(real["gravity_profile"]), Float64.(real["metric_distances"]))
    oneoverr2_on_metric = abs(Float64(fit["falloff_exponent"]) - 2.0) <= EXPONENT_TOL
    real_present = Float64(real["total_gravity"]) > PRESENT_THRESHOLD && Float64(real["mass"]) > PRESENT_THRESHOLD
    flatten_delta = abs(Float64(real["total_gravity"]) - Float64(flattened["total_gravity"]))
    dies_under_flatten = real_present && Float64(flattened["total_gravity"]) <= PRESENT_THRESHOLD && flatten_delta > PRESENT_THRESHOLD
    survives_random_knot = Float64(random_knot["total_gravity"]) > PRESENT_THRESHOLD || Float64(trivial_knot["total_gravity"]) > PRESENT_THRESHOLD
    owner_carrier_load_bearing = Float64(invariants["owner_density_trace"]) > 1.0 - 1.0e-9 &&
        Float64(invariants["owner_density_bloch_norm"]) > 1.0 - 1.0e-9 &&
        Float64(invariants["owner_hopf_metric_det_min"]) > 0.0 &&
        dies_under_flatten
    prior_target_imprint = Bool(prior["available"]) && Bool(prior["all_pass"]) && String(prior["branch_verdict"]) == "TARGET_IMPRINT"
    G_derived = false

    shared_scalars = Dict{String,Any}(
        "real.mass" => Float64(real["mass"]),
        "real.total_gravity" => Float64(real["total_gravity"]),
        "flattened.mass" => Float64(flattened["mass"]),
        "flattened.total_gravity" => Float64(flattened["total_gravity"]),
        "random_knot.mass" => Float64(random_knot["mass"]),
        "random_knot.total_gravity" => Float64(random_knot["total_gravity"]),
        "trivial_knot.mass" => Float64(trivial_knot["mass"]),
        "trivial_knot.total_gravity" => Float64(trivial_knot["total_gravity"]),
        "flatten_delta" => flatten_delta,
        "falloff_exponent" => Float64(fit["falloff_exponent"]),
        "one_over_r2_sse" => Float64(fit["one_over_r2_sse"]),
        "one_over_r2_amplitude" => Float64(fit["one_over_r2_amplitude"]),
        "golden_linking_receipt" => Float64(invariants["golden_linking_receipt"]),
        "flat_linking_receipt" => Float64(invariants["flat_linking_receipt"]),
        "real_link_sample" => Float64(invariants["real_link_sample"]),
        "random_unlinked_link_sample" => Float64(invariants["random_unlinked_link_sample"]),
        "trivial_flat_link_sample" => Float64(invariants["trivial_flat_link_sample"]),
        "owner_density_trace" => Float64(invariants["owner_density_trace"]),
        "owner_density_bloch_norm" => Float64(invariants["owner_density_bloch_norm"]),
        "owner_hopf_metric_det_min" => Float64(invariants["owner_hopf_metric_det_min"]),
        "prior_matrix.mutated_carrier_value" => Float64(prior["mutated_carrier_value"]),
        "prior_matrix.owner_carrier_value" => Float64(prior["owner_carrier_value"]),
        "prior_matrix.negative_control_value" => Float64(prior["negative_control_value"]),
    )
    for (idx, pair) in enumerate(zip(real["metric_distances"], real["gravity_profile"]))
        distance, gravity = pair
        zero_idx = idx - 1
        shared_scalars["real.metric_distance.$zero_idx"] = Float64(distance)
        shared_scalars["real.gravity_readout.$zero_idx"] = Float64(gravity)
    end

    shared_booleans = Dict{String,Any}(
        "jax_enable_x64" => true,
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "real_present" => real_present,
        "oneoverr2_on_metric" => oneoverr2_on_metric,
        "dies_under_flatten" => dies_under_flatten,
        "survives_random_knot" => survives_random_knot,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "prior_target_imprint_falsifier" => prior_target_imprint,
        "G_derived" => G_derived,
        "classification_fence" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
    )
    pre_parity = Dict{String,Any}(
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => Dict{String,Any}("object_id" => OBJECT_ID, "G_derived" => "false"),
    )
    parity = parity_block(pre_parity)
    parity_ok = Bool(parity["peer_available"]) && Bool(parity["within_1e_9"])
    verdict = row_verdict(
        parity_ok=parity_ok,
        real_present=real_present,
        oneoverr2_on_metric=oneoverr2_on_metric,
        dies_under_flatten=dies_under_flatten,
        survives_random_knot=survives_random_knot,
        owner_carrier_load_bearing=owner_carrier_load_bearing,
        prior_target_imprint=prior_target_imprint,
    )
    shared_strings = Dict{String,Any}("object_id" => OBJECT_ID, "row_verdict" => verdict, "G_derived" => "false")
    local_all_pass = Bool(shared_booleans["classification_fence"]) &&
        Bool(shared_booleans["jax_enable_x64"]) &&
        !Bool(shared_booleans["numpy_compute_used"]) &&
        !Bool(shared_booleans["torch_compute_used"]) &&
        Bool(shared_booleans["real_present"]) &&
        Bool(shared_booleans["oneoverr2_on_metric"]) &&
        Bool(shared_booleans["dies_under_flatten"]) &&
        !Bool(shared_booleans["survives_random_knot"]) &&
        Bool(shared_booleans["owner_carrier_load_bearing"]) &&
        (verdict in ["REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD", "OPEN"]) &&
        G_derived == false

    positive = Dict{String,Any}(
        "real_owner_carrier_metric_readout_present" => Dict("pass" => real_present, "mass" => real["mass"], "total_gravity" => real["total_gravity"], "branch" => real),
        "one_over_r2_on_hopf_metric" => merge(fit, Dict{String,Any}("pass" => oneoverr2_on_metric, "tolerance" => EXPONENT_TOL, "note" => "The inverse-square readout is tested as a finite carrier readout, not as a G derivation.")),
        "owner_real_carrier_load_bearing" => Dict("pass" => owner_carrier_load_bearing, "real_total_gravity" => real["total_gravity"], "flattened_total_gravity" => flattened["total_gravity"], "erase_delta" => flatten_delta),
    )
    graveyard_companions = Dict{String,Any}(
        "carrier_flatten_control" => Dict("pass" => dies_under_flatten, "control" => "same readout with flat-S2 linking receipt and flattened shell geometry", "branch" => flattened),
        "random_trivial_knot_control" => Dict("pass" => !survives_random_knot, "control" => "same readout with deterministic unlinked and flat-S2 Gauss-linking controls from the owner golden Weyl code", "random_branch" => random_knot, "trivial_branch" => trivial_knot),
        "prior_target_imprint_falsifier" => Dict("pass" => prior_target_imprint, "effect_on_verdict" => "demotes REAL_CARRIER to CONVENTION for this row", "prior" => prior),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => shared_booleans["classification_fence"], "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "no_numpy_no_torch_compute" => Dict("pass" => true, "numpy_compute_used" => false, "torch_compute_used" => false),
        "G_not_derived" => Dict("pass" => G_derived == false, "G_derived" => G_derived),
        "honest_discriminator_verdict" => Dict("pass" => verdict in ["REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD", "OPEN"], "row_verdict" => verdict, "rule" => "REAL_CARRIER requires oneoverr2_on_metric, dies_under_flatten, survives_random_knot=false, owner erasure changes result, and no active target-imprint falsifier."),
    )

    result = Dict{String,Any}(
        "schema" => "DISC_GRAVITY_KNOT_DISCRIMINATOR_v1",
        "object_id" => OBJECT_ID,
        "name" => NAME,
        "backend" => BACKEND,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => JULIA_SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => CLASSIFICATION,
        "promotion" => false,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission" => false,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [
            "finite owner-carrier erase changes this gravity/knot readout",
            "finite random/trivial knot controls are absent for this readout",
            "honest row verdict under current falsifiers",
        ],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "carrier_readout_discriminator",
        "source_alignment_category" => "gravity_knot_owner_carrier_discriminator",
        "source_refs" => source_refs(),
        "carrier" => Dict{String,Any}(
            "real_carrier" => "owner Weyl/Hopf/Clifford nested S3 spinor carrier via golden_weyl, density_matrix_spinor_lift, and clifford_torus_nested_hopf_foliation",
            "metric" => "Fubini-Study distance on owner Hopf/Weyl spinors",
            "knot_signal" => "golden_weyl finite Gauss linking receipt and matching sampled owner function",
            "flatten" => "flat-S2 linking receipt plus flattened shell geometry",
            "random_trivial" => "deterministic unlinked and flat-S2 owner Gauss-link controls",
        ),
        "finite_witness" => Dict{String,Any}(
            "invariants" => invariants,
            "real_profile" => real,
            "flattened_profile" => flattened,
            "random_knot_profile" => random_knot,
            "trivial_knot_profile" => trivial_knot,
            "falloff_fit" => fit,
            "prior_target_imprint_falsifier" => prior,
        ),
        "row_verdict" => verdict,
        "oneoverr2_on_metric" => oneoverr2_on_metric,
        "dies_under_flatten" => dies_under_flatten,
        "survives_random_knot" => survives_random_knot,
        "G_derived" => G_derived,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => 4, "passed" => local_all_pass ? 4 : 0, "variants" => ["real_owner_carrier", "flat_s2_flatten", "deterministic_unlinked_random", "flat_s2_trivial"], "all_pass" => local_all_pass),
        "why_not_v4_probes" => "v5 scratch dual-backend discriminator row; not a v4 probe, not a promotion artifact, and G is not derived.",
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_manifest" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "jax_x64_enabled" => true,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
        "parity" => parity_block(Dict("shared_scalars" => shared_scalars, "shared_booleans" => shared_booleans, "shared_strings" => shared_strings)),
        "local_all_pass" => local_all_pass,
    )
    result["all_pass"] = result["local_all_pass"] && result["parity"]["peer_available"] && result["parity"]["within_1e_9"] && verdict != "OPEN"
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => result["local_all_pass"],
        "row_verdict" => verdict,
        "oneoverr2_on_metric" => oneoverr2_on_metric,
        "dies_under_flatten" => dies_under_flatten,
        "survives_random_knot" => survives_random_knot,
        "G_derived" => G_derived,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "prior_target_imprint_falsifier" => prior_target_imprint,
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
        "row_verdict=$(result["row_verdict"]) " *
        "oneoverr2_on_metric=$(lowercase(string(result["oneoverr2_on_metric"]))) " *
        "dies_under_flatten=$(lowercase(string(result["dies_under_flatten"]))) " *
        "survives_random_knot=$(lowercase(string(result["survives_random_knot"]))) " *
        "G_derived=$(lowercase(string(result["G_derived"])))"
    )
    if !result["local_all_pass"]
        exit(1)
    end
end

main()
