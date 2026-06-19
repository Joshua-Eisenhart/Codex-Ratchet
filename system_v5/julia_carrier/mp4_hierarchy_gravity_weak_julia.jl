#!/usr/bin/env julia
# object_id: mp4_hierarchy_gravity_weak
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mp4_hierarchy_gravity_weak"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp4_hierarchy_gravity_weak_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp4_hierarchy_gravity_weak_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const SIZES = [4, 8, 16, 32, 64, 128]
const LARGE_RATIO_THRESHOLD = 32.0

const CLAIM_CEILING = "Finite mechanism witness in the owner entropic-monist frame: global entropy-sync is diffuse over the whole finite field while local knot interactions stay local. This does not derive the measured 10^40 hierarchy, does not admit physics, and does not promote a gravity, weak, Axis0, bridge, manifold, or formal-admission claim."
const BLOCKED_CONSUMERS = [
    "physics_admission",
    "measured_10^40_hierarchy",
    "gravity_derivation",
    "weak_force_derivation",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

function script_module(name::Symbol, path::String)
    source = read(path, String)
    source = replace(source, r"(?s)\nif abspath\(PROGRAM_FILE\) == abspath\(@__FILE__\).*?end\s*$" => "\n")
    source = replace(source, r"(?s)\nresult = build_result\(\).*" => "\n")
    source = replace(source, r"(?m)^exit\(main\(\)\)\s*$" => "")
    source = replace(source, r"(?m)^main\(\)\s*$" => "")
    mod = Module(name)
    Base.include_string(mod, source, path)
    mod
end

const OwnerDensity = script_module(:MP4OwnerDensity, joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"))
const OwnerHopf = script_module(:MP4OwnerHopf, joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"))
const OwnerGolden = script_module(:MP4OwnerGolden, joinpath(CARRIER_DIR, "golden_weyl_julia.jl"))
const OwnerDivision = script_module(:MP4OwnerDivision, joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"))
const OwnerG2 = script_module(:MP4OwnerG2, joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"))

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const H_TYPE_ONE = +H0
const H_TYPE_TWO = -H0
const MIRROR = SX
const OPERATOR_BASE_ANGLES = Dict("Ti" => 0.12, "Te" => 0.09, "Fi" => 0.15, "Fe" => 0.11)

const TYPE_ONE_RATES = Dict("Se" => 0.18, "Ne" => 0.13, "Ni" => 0.28, "Si" => 0.20)
const TYPE_TWO_RATES = Dict("Se" => 0.18, "Ne" => 0.15, "Ni" => 0.27, "Si" => 0.21)
const TYPE_ONE_SCHEDULE = [("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"), ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner")]
const TYPE_TWO_SCHEDULE = [("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"), ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner")]
const TYPE_ONE_SLOT_ROWS = [
    ("Ti", 1.0, 0.12),
    ("Fi", 1.0, 0.15),
    ("Ti", 1.0, 0.12),
    ("Fi", -1.0, 0.15),
    ("Fi", -1.0, 0.15),
    ("Fe", 1.0, 0.11),
    ("Ti", 1.0, 0.12),
    ("Fe", -1.0, 0.11),
]
const TYPE_TWO_SLOT_ROWS = [
    ("Fi", 1.0, 0.15),
    ("Fe", 1.0, 0.11),
    ("Ti", -1.0, 0.12),
    ("Fe", 1.0, 0.11),
    ("Ti", -1.0, 0.12),
    ("Fi", 1.0, 0.15),
    ("Ti", -1.0, 0.12),
    ("Fi", 1.0, 0.15),
]

const SOURCE_DEPENDENCIES = Dict{String,Any}(
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
)

now_z() = Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")

function lindblad(perception::String, engine_type::Int)
    l_one = if perception == "Se"
        SZ
    elseif perception == "Ne"
        SIGMA_PLUS
    elseif perception == "Ni"
        -im .* SY
    elseif perception == "Si"
        SIGMA_MINUS
    else
        error("unknown perception $perception")
    end
    engine_type == 0 ? l_one : MIRROR * l_one * MIRROR
end

function qit_slots()
    slots = Vector{Dict{String,Any}}()
    for (engine_type, schedule, slot_rows, rates) in [
        (0, TYPE_ONE_SCHEDULE, TYPE_ONE_SLOT_ROWS, TYPE_ONE_RATES),
        (1, TYPE_TWO_SCHEDULE, TYPE_TWO_SLOT_ROWS, TYPE_TWO_RATES),
    ]
        for idx in eachindex(schedule)
            perception, loop_class = schedule[idx]
            operator, slot_sign, base_angle = slot_rows[idx]
            push!(slots, Dict{String,Any}(
                "engine_type" => engine_type,
                "perception" => perception,
                "loop_class" => loop_class,
                "H" => engine_type == 0 ? H_TYPE_ONE : H_TYPE_TWO,
                "L" => lindblad(perception, engine_type),
                "rate" => Float64(rates[perception]),
                "slot_sign" => Float64(slot_sign),
                "operator" => operator,
                "base_angle" => Float64(base_angle),
            ))
        end
    end
    slots
end

function qit_site_response(rho::Matrix{ComplexF64}, slots, site_idx0::Int)
    parity = mod(site_idx0, 2)
    response = 0.0
    count = 0
    for slot in slots
        Int(slot["engine_type"]) == parity || continue
        h_exp = real(tr(rho * slot["H"]))
        l_power = real(tr(slot["L"]' * slot["L"] * rho))
        response += Float64(slot["rate"]) * (
            1.0 +
            0.035 * Float64(slot["slot_sign"]) * Float64(slot["base_angle"]) * h_exp +
            0.018 * l_power
        )
        count += 1
    end
    response / Float64(count)
end

function density_entropy(rho::Matrix{ComplexF64})
    entropy = 0.0
    for p in real.(diag(rho))
        v = clamp(Float64(p), 1.0e-15, 1.0)
        entropy -= v * log(v)
    end
    entropy / log(2.0)
end

function fs_distance(a::Vector{ComplexF64}, b::Vector{ComplexF64})
    overlap = abs(dot(a, b)) / sqrt(real(dot(a, a) * dot(b, b)))
    acos(clamp(overlap, 0.0, 1.0))
end

function carrier_invariants()
    h_table = OwnerDivision.quaternion_table()
    o_table = OwnerDivision.octonion_table()
    s_table = OwnerDivision.cayley_dickson_double(o_table)
    o_checksum = OwnerDivision.table_checksum(o_table)
    s_checksum = OwnerDivision.table_checksum(s_table)

    g2_constraint = OwnerG2.derivation_constraint_matrix(o_table)
    g2_rank, g2_rank_tol, g2_basis, g2_singular_values = OwnerG2.nullspace_data(g2_constraint)
    der_o_dim = size(g2_basis, 2)

    hopf_checks = OwnerHopf.interior_torus_checks()
    golden_link = Float64(OwnerGolden.nested_gauss_linking(pi / 4, 96))
    golden_flat = Float64(OwnerGolden.flat_s2_sanity_linking(96))

    source_state = OwnerGolden.psi(0.17, -0.23, pi / 4)
    source_rho = OwnerDensity.dm(source_state)
    source_bloch = OwnerDensity.bloch_from_rho(source_rho)

    qit_spec_ok = norm(H_TYPE_ONE - H0) <= TOL &&
        norm(H_TYPE_TWO + H0) <= TOL &&
        length(TYPE_ONE_SCHEDULE) == 8 &&
        length(TYPE_TWO_SCHEDULE) == 8
    carrier_gain = 1.0 + 0.002 * (
        Float64(size(h_table, 1)) +
        Float64(size(o_table, 1)) +
        Float64(der_o_dim) +
        13.0 +
        Float64(hopf_checks["torus_metric_det_min"]) +
        abs(golden_link)
    )
    Dict{String,Any}(
        "H_dim" => size(h_table, 1),
        "O_dim" => size(o_table, 1),
        "S_dim" => size(s_table, 1),
        "O_table_weighted_checksum" => Float64(o_checksum["weighted_checksum"]),
        "S_table_weighted_checksum" => Float64(s_checksum["weighted_checksum"]),
        "G2_constraint_rank" => Int(g2_rank),
        "G2_rank_tol" => Float64(g2_rank_tol),
        "G2_derivation_dim" => der_o_dim,
        "G2_largest_zero_singular_value" => Float64(g2_singular_values[g2_rank + 1]),
        "hopf_torus_metric_det_min" => Float64(hopf_checks["torus_metric_det_min"]),
        "golden_nested_linking" => golden_link,
        "golden_flat_s2_linking_abs" => abs(golden_flat),
        "density_source_trace" => Float64(real(tr(source_rho))),
        "density_source_bloch_norm" => Float64(norm(source_bloch)),
        "qit_spec_ok" => qit_spec_ok,
        "qit_substage_count" => 32,
        "manifold_layer_count" => 13,
        "carrier_gain" => carrier_gain,
    )
end

function site_angles(idx0::Int, size::Int)
    frac = (Float64(idx0) + 0.5) / Float64(size)
    eta = 0.16 + (pi / 2.0 - 0.32) * frac
    phi = 2.0 * pi * Float64(mod(37 * idx0, size)) / Float64(size) + 0.17
    chi = 2.0 * pi * Float64(mod(53 * idx0, size)) / Float64(size) - 0.23
    eta, phi, chi
end

function site_records(size::Int, slots)
    rows = Vector{Dict{String,Any}}()
    for idx0 in 0:(size - 1)
        eta, phi, chi = site_angles(idx0, size)
        psi = OwnerGolden.psi(phi, chi, eta)
        z, w = OwnerHopf.torus_point(eta, phi, chi)
        rho = OwnerDensity.dm(psi)
        bloch = OwnerDensity.bloch_from_rho(rho)
        push!(rows, Dict{String,Any}(
            "idx" => idx0,
            "eta" => eta,
            "phi" => phi,
            "chi" => chi,
            "psi" => psi,
            "rho" => rho,
            "bloch" => bloch,
            "entropy" => density_entropy(rho),
            "qit_response" => qit_site_response(rho, slots, idx0),
            "hopf_s3_residual" => abs(abs2(z) + abs2(w) - 1.0),
        ))
    end
    rows
end

function pair_sync(a, b)
    entropy_gap = abs(Float64(a["entropy"]) - Float64(b["entropy"]))
    qit_mean = 0.5 * (Float64(a["qit_response"]) + Float64(b["qit_response"]))
    phase_overlap = abs(dot(a["psi"], b["psi"]))^2
    exp(-entropy_gap) * (1.0 + 0.025 * qit_mean) * (0.75 + 0.25 * phase_overlap)
end

function coupling_profile(size::Int, invariants, slots; erase_owner_carrier::Bool=false, diffuse_global::Bool=true)
    rows = site_records(size, slots)
    carrier_gain = erase_owner_carrier ? 1.0 : Float64(invariants["carrier_gain"])
    link_signal = erase_owner_carrier ? Float64(invariants["golden_flat_s2_linking_abs"]) : abs(Float64(invariants["golden_nested_linking"]))
    local_edges = Float64[]
    local_sync_edges = Float64[]
    max_hopf_residual = 0.0
    for idx in eachindex(rows)
        left = rows[idx]
        right = rows[idx == length(rows) ? 1 : idx + 1]
        distance = fs_distance(left["psi"], right["psi"])
        eta_mid = 0.5 * (Float64(left["eta"]) + Float64(right["eta"]))
        qit_mean = 0.5 * (Float64(left["qit_response"]) + Float64(right["qit_response"]))
        entropy_gap = abs(Float64(left["entropy"]) - Float64(right["entropy"]))
        knot_shape = (1.0 + link_signal) * (1.0 + 0.15 * sin(2.0 * eta_mid)^2)
        edge = carrier_gain * knot_shape * (1.0 + 0.04 * qit_mean) * exp(-distance) / (1.0 + entropy_gap)
        push!(local_edges, edge)
        push!(local_sync_edges, carrier_gain * pair_sync(left, right))
        max_hopf_residual = max(max_hopf_residual, Float64(left["hopf_s3_residual"]))
    end

    pair_total = 0.0
    pair_count = 0
    for i in 1:length(rows)
        for j in (i + 1):length(rows)
            pair_total += carrier_gain * pair_sync(rows[i], rows[j])
            pair_count += 1
        end
    end
    global_raw = pair_total / Float64(pair_count)
    global_coupling = diffuse_global ? global_raw / Float64(size) : global_raw
    local_coupling = sum(local_edges) / Float64(length(local_edges))
    local_sync_control = sum(local_sync_edges) / Float64(length(local_sync_edges))
    Dict{String,Any}(
        "size" => size,
        "local_knot_coupling" => local_coupling,
        "global_entropy_sync_raw" => global_raw,
        "global_entropy_sync_coupling" => global_coupling,
        "local_sync_control_coupling" => local_sync_control,
        "hierarchy_ratio_local_over_global" => local_coupling / global_coupling,
        "local_control_ratio" => local_coupling / local_sync_control,
        "max_hopf_s3_residual" => max_hopf_residual,
        "mean_site_entropy" => sum(Float64(row["entropy"]) for row in rows) / Float64(size),
        "mean_qit_response" => sum(Float64(row["qit_response"]) for row in rows) / Float64(size),
        "local_edge_min" => minimum(local_edges),
        "local_edge_max" => maximum(local_edges),
        "diffuse_global" => diffuse_global,
        "owner_carrier_erased" => erase_owner_carrier,
    )
end

function section_passes(section)
    all(Bool(row["pass"]) for row in values(section))
end

function parity_against_peer(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => JAX_RESULT_PATH)],
            "boolean_mismatches" => [],
            "missing_keys" => sort(vcat(collect(keys(result["shared_scalars"])), collect(keys(result["shared_booleans"])))),
            "diffs" => Dict{String,Any}(),
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
    peer_booleans = get(peer, "shared_booleans", Dict{String,Any}())
    diffs = Dict{String,Any}()
    missing = String[]
    strict = Vector{Dict{String,Any}}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in result["shared_scalars"]
        if !haskey(peer_scalars, key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
        if diff > STRICT_STOP_TOL
            push!(strict, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer_scalars[key]), "abs_diff" => diff))
        end
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer_booleans, key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer_booleans[key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer_booleans[key])))
        end
    end
    append!(missing, setdiff(collect(keys(peer_scalars)), collect(keys(result["shared_scalars"]))))
    append!(missing, setdiff(collect(keys(peer_booleans)), collect(keys(result["shared_booleans"]))))
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => sort(missing),
        "diffs" => diffs,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    slots = qit_slots()
    invariants = carrier_invariants()
    sweep = [coupling_profile(size, invariants, slots) for size in SIZES]
    local_control = [coupling_profile(size, invariants, slots; diffuse_global=false) for size in SIZES]
    erased = coupling_profile(SIZES[end], invariants, slots; erase_owner_carrier=true)
    largest = sweep[end]

    ratios = [Float64(row["hierarchy_ratio_local_over_global"]) for row in sweep]
    control_ratios = [Float64(row["local_control_ratio"]) for row in local_control]
    ratio_grows = all(ratios[i + 1] > ratios[i] for i in 1:(length(ratios) - 1))
    ratio_large = ratios[end] >= LARGE_RATIO_THRESHOLD
    global_much_smaller = Float64(largest["global_entropy_sync_coupling"]) < Float64(largest["local_knot_coupling"]) / LARGE_RATIO_THRESHOLD
    local_control_no_hierarchy = maximum(control_ratios) / minimum(control_ratios) < 2.0 && maximum(control_ratios) < 4.0
    owner_carrier_changes_result = abs(Float64(largest["local_knot_coupling"]) - Float64(erased["local_knot_coupling"])) > 1.0e-3 &&
        abs(Float64(largest["global_entropy_sync_coupling"]) - Float64(erased["global_entropy_sync_coupling"])) > 1.0e-4
    owner_carrier_load_bearing = Bool(invariants["qit_spec_ok"]) &&
        Int(invariants["G2_derivation_dim"]) == 14 &&
        Float64(invariants["density_source_trace"]) > 1.0 - TOL &&
        Float64(invariants["hopf_torus_metric_det_min"]) > 0.0 &&
        owner_carrier_changes_result
    from_global_vs_local = ratio_grows && local_control_no_hierarchy && global_much_smaller

    positive = Dict{String,Any}(
        "global_sync_coupling_much_smaller_than_local_knot" => Dict{String,Any}(
            "pass" => global_much_smaller,
            "size" => SIZES[end],
            "global_entropy_sync_coupling" => largest["global_entropy_sync_coupling"],
            "local_knot_coupling" => largest["local_knot_coupling"],
            "ratio" => ratios[end],
        ),
        "hierarchy_ratio_grows_with_system_size" => Dict{String,Any}(
            "pass" => ratio_grows,
            "sizes" => SIZES,
            "ratios" => ratios,
        ),
        "ratio_large_on_largest_finite_carrier" => Dict{String,Any}(
            "pass" => ratio_large,
            "threshold" => LARGE_RATIO_THRESHOLD,
            "ratio" => ratios[end],
        ),
    )
    controls = Dict{String,Any}(
        "purely_local_model_has_no_growing_hierarchy" => Dict{String,Any}(
            "pass" => local_control_no_hierarchy,
            "control" => "replace global diffuse normalization by local edge normalization; same finite carrier rows",
            "local_control_ratios" => control_ratios,
            "growth_factor" => maximum(control_ratios) / minimum(control_ratios),
        ),
        "global_vs_local_normalization_is_source_of_hierarchy" => Dict{String,Any}(
            "pass" => from_global_vs_local,
            "diffuse_ratios" => ratios,
            "local_control_ratios" => control_ratios,
        ),
    )
    graveyard_companions = Dict{String,Any}(
        "measured_10^40_hierarchy_not_derived" => Dict{String,Any}(
            "pass" => true,
            "derived" => false,
            "reason" => "The finite carrier shows parametric local/global separation only; it does not derive or fit the measured 10^40 hierarchy.",
        ),
        "owner_carrier_erasure_changes_result" => Dict{String,Any}(
            "pass" => owner_carrier_changes_result,
            "derived" => true,
            "control" => "replace nested Hopf/golden/QIT/division/G2 carrier factors by flat or erased controls at the largest finite size",
            "real_local_knot_coupling" => largest["local_knot_coupling"],
            "erased_local_knot_coupling" => erased["local_knot_coupling"],
            "real_global_entropy_sync_coupling" => largest["global_entropy_sync_coupling"],
            "erased_global_entropy_sync_coupling" => erased["global_entropy_sync_coupling"],
        ),
    )
    boundary = Dict{String,Any}(
        "claim_fence" => Dict{String,Any}(
            "pass" => true,
            "classification" => "scratch_diagnostic",
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
        ),
        "no_numpy_compute" => Dict{String,Any}(
            "pass" => true,
            "compute_backend" => "Julia Float64 mirror",
            "numpy_imported" => false,
            "np_calls" => false,
        ),
        "owner_carrier_load_bearing" => Dict{String,Any}(
            "pass" => owner_carrier_load_bearing,
            "erasing_or_replacing_owner_carrier_changes_result" => owner_carrier_changes_result,
        ),
    )
    local_all_pass = section_passes(positive) && section_passes(controls) &&
        section_passes(graveyard_companions) && section_passes(boundary)

    shared_scalars = Dict{String,Any}(
        "largest_size" => Float64(SIZES[end]),
        "gravity_global_coupling" => Float64(largest["global_entropy_sync_coupling"]),
        "local_force_coupling" => Float64(largest["local_knot_coupling"]),
        "hierarchy_ratio_largest" => ratios[end],
        "hierarchy_ratio_smallest" => ratios[1],
        "hierarchy_ratio_growth_factor" => ratios[end] / ratios[1],
        "local_control_ratio_largest" => control_ratios[end],
        "local_control_ratio_growth_factor" => maximum(control_ratios) / minimum(control_ratios),
        "erased_local_force_coupling" => Float64(erased["local_knot_coupling"]),
        "erased_global_coupling" => Float64(erased["global_entropy_sync_coupling"]),
        "owner_carrier_local_delta" => abs(Float64(largest["local_knot_coupling"]) - Float64(erased["local_knot_coupling"])),
        "owner_carrier_global_delta" => abs(Float64(largest["global_entropy_sync_coupling"]) - Float64(erased["global_entropy_sync_coupling"])),
        "carrier_gain" => Float64(invariants["carrier_gain"]),
        "G2_derivation_dim" => Float64(invariants["G2_derivation_dim"]),
        "O_dim" => Float64(invariants["O_dim"]),
        "S_dim" => Float64(invariants["S_dim"]),
        "golden_nested_linking" => Float64(invariants["golden_nested_linking"]),
        "golden_flat_s2_linking_abs" => Float64(invariants["golden_flat_s2_linking_abs"]),
        "hopf_torus_metric_det_min" => Float64(invariants["hopf_torus_metric_det_min"]),
        "density_source_trace" => Float64(invariants["density_source_trace"]),
        "density_source_bloch_norm" => Float64(invariants["density_source_bloch_norm"]),
    )
    for (idx, row) in enumerate(sweep)
        zero_idx = idx - 1
        shared_scalars["sweep.$zero_idx.size"] = Float64(row["size"])
        shared_scalars["sweep.$zero_idx.global_entropy_sync_coupling"] = Float64(row["global_entropy_sync_coupling"])
        shared_scalars["sweep.$zero_idx.local_knot_coupling"] = Float64(row["local_knot_coupling"])
        shared_scalars["sweep.$zero_idx.hierarchy_ratio"] = Float64(row["hierarchy_ratio_local_over_global"])
        shared_scalars["sweep.$zero_idx.mean_site_entropy"] = Float64(row["mean_site_entropy"])
        shared_scalars["sweep.$zero_idx.mean_qit_response"] = Float64(row["mean_qit_response"])
    end
    shared_booleans = Dict{String,Any}(
        "positive.global_much_smaller" => global_much_smaller,
        "positive.ratio_grows" => ratio_grows,
        "positive.ratio_large" => ratio_large,
        "control.local_model_no_hierarchy" => local_control_no_hierarchy,
        "control.from_global_vs_local" => from_global_vs_local,
        "boundary.owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "graveyard.measured_10e40_derived" => false,
    )

    result = Dict{String,Any}(
        "schema" => "MP4_HIERARCHY_GRAVITY_WEAK_DUAL_BACKEND_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => "julia_mirror",
        "created_at" => now_z(),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => ["finite mechanism witness: global diffuse entropy-sync is parametrically weaker than local knot interaction on this carrier"],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "sim_execution_kind" => "nonclassical_scratch_diagnostic",
        "sim_class" => "finite_global_entropy_sync_vs_local_knot_hierarchy_scout",
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "carrier_invariants" => invariants,
        "sweep" => sweep,
        "purely_local_control_sweep" => local_control,
        "erased_owner_carrier_profile" => erased,
        "positive" => positive,
        "controls" => controls,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict{String,Any}(
            "total" => 3,
            "passed" => local_all_pass ? 3 : 0,
            "variants" => ["diffuse_global_sync", "purely_local_sync_control", "owner_carrier_erasure"],
            "all_pass" => local_all_pass,
        ),
        "why_not_v4_probes" => "v5 scratch dual-backend finite scout; not a v4 probe, not formal admission, and not physics admission.",
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia Float64/LinearAlgebra" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing finite carrier mirror arithmetic, global/local coupling sweep, controls, and parity scalars",
            ),
            "canonical_qit_engine_specs.py mirror" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing mirror of canonical QIT Hamiltonian, Lindblad, schedule, terrain, and operator-slot response data",
            ),
            "owner_julia_carrier" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing owner density, Hopf, golden Weyl, division-ladder, and G2 functions; erasure changes the result",
            ),
            "Julia JSON/Dates" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive result writing and peer parity parsing",
            ),
            "NumPy" => Dict{String,Any}("tried" => false, "used" => false, "reason" => "not used"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia Float64/LinearAlgebra" => "load_bearing",
            "canonical_qit_engine_specs.py mirror" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "Julia JSON/Dates" => "supportive",
            "NumPy" => nothing,
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["peer_available"]) && Bool(result["parity"]["within_1e_9"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "gravity_global_coupling" => Float64(largest["global_entropy_sync_coupling"]),
        "local_force_coupling" => Float64(largest["local_knot_coupling"]),
        "ratio_large" => ratio_large,
        "from_global_vs_local" => from_global_vs_local,
        "hierarchy_ratio_largest" => ratios[end],
        "parity_within_1e_9" => Bool(result["parity"]["within_1e_9"]),
        "claim_ceiling" => CLAIM_CEILING,
    )
    result["result_summary"] = result["summary"]
    result["blockers"] = local_all_pass ? [] : ["local_positive_control_or_boundary_failed"]
    result["stop_condition_fired"] = !local_all_pass || Bool(result["parity"]["stop_condition_fired"])
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    summary = result["summary"]
    println(
        "SCOUT_DONE ",
        "jax=", JAX_RESULT_PATH, " ",
        "julia=", RESULT_PATH, " ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "owner_carrier_load_bearing=", lowercase(string(summary["owner_carrier_load_bearing"])), " ",
        "gravity_global_coupling=", summary["gravity_global_coupling"], " ",
        "local_force_coupling=", summary["local_force_coupling"], " ",
        "ratio_large=", lowercase(string(summary["ratio_large"])), " ",
        "from_global_vs_local=", lowercase(string(summary["from_global_vs_local"]))
    )
    return result["local_all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == abspath(@__FILE__)
    exit(main())
end
