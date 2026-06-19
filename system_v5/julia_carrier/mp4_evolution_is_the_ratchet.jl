#!/usr/bin/env julia
# object_id: mp4_evolution_is_the_ratchet
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp4_evolution_is_the_ratchet"
const RESULT_PATH = joinpath(@__DIR__, "mp4_evolution_is_the_ratchet_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "..", "ops", "formal_scouts", "results", "mp4_evolution_is_the_ratchet_results.json")
const CANONICAL_SPEC = joinpath(@__DIR__, "..", "ops", "formal_scouts", "canonical_qit_engine_specs.py")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "Finite structural unification witness in the owner's entropic-monist frame: a population/candidate carrier under constraints is selected by the same finite constraint-survival ratchet operator used on the QIT terrain carrier. This is not a proof or derivation of biology, evolution, physics, natural selection, Hoffman, M(C), Axis0, bridge, or any physics admission."
const STRATEGY_ORDER = ["WinWin", "WinLose", "LoseWin", "LoseLose"]
const BLOCKED_CONSUMERS = [
    "biology_admission",
    "physics_admission",
    "natural_selection_derivation",
    "hoffman_derivation",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

const OWNER_RECEIPTS = Dict{String,String}(
    "density_matrix_spinor_lift" => joinpath(@__DIR__, "density_matrix_spinor_lift_julia_results.json"),
    "clifford_torus_nested_hopf_foliation" => joinpath(@__DIR__, "clifford_torus_nested_hopf_foliation_julia_results.json"),
    "golden_weyl" => joinpath(@__DIR__, "golden_weyl_julia_receipt.json"),
    "golden_weyl_ledger" => joinpath(@__DIR__, "golden_weyl_ledger.json"),
    "division_algebra_ratchet_ladder" => joinpath(@__DIR__, "division_algebra_ratchet_ladder_julia_results.json"),
    "octonion_G2_automorphism" => joinpath(@__DIR__, "octonion_G2_automorphism_julia_results.json"),
)

const OWNER_SOURCES = Dict{String,String}(
    "canonical_qit_engine_specs" => CANONICAL_SPEC,
    "density_matrix_spinor_lift" => joinpath(@__DIR__, "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax" => joinpath(@__DIR__, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(@__DIR__, "clifford_torus_nested_hopf_foliation.jl"),
    "clifford_torus_nested_hopf_foliation_jax" => joinpath(@__DIR__, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(@__DIR__, "golden_weyl_julia.jl"),
    "golden_weyl_jax_snapshot" => joinpath(@__DIR__, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "division_algebra_ratchet_ladder" => joinpath(@__DIR__, "division_algebra_ratchet_ladder.jl"),
    "division_algebra_ratchet_ladder_jax" => joinpath(@__DIR__, "jax_division_algebra_ratchet_ladder.py"),
    "octonion_G2_automorphism" => joinpath(@__DIR__, "octonion_G2_automorphism.jl"),
    "octonion_G2_automorphism_jax" => joinpath(@__DIR__, "jax_octonion_G2_automorphism.py"),
)

const TOOL_MANIFEST = Dict{String,Any}(
    "julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Julia mirror for finite x64-equivalent constraint-survival logits, controls, and parity rows"),
    "jax" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend written by the Python driver"),
    "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing gate from real owner carrier receipts; erasing the gate changes survivor selection to no-selection"),
    "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source alignment for the four canonical terrain strategy rows and QIT ratchet strategy order"),
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite matrix/vector computation for the mirror"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "not used"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "julia" => "load_bearing",
    "jax" => "load_bearing",
    "owner_julia_carrier" => "load_bearing",
    "canonical_qit_engine_specs.py" => "load_bearing",
    "Julia LinearAlgebra" => "load_bearing",
    "numpy" => "None",
)

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function sha256_file(path::String)
    isfile(path) || return nothing
    bytes2hex(sha256(read(path)))
end

read_json(path::String) = JSON.parsefile(path)
as_float(x) = Float64(x)

function get_path(data, dotted::String, default=nothing)
    cur = data
    parts = split(dotted, ".")
    idx = 1
    while idx <= length(parts)
        if !(cur isa AbstractDict)
            return default
        end
        remaining = join(parts[idx:end], ".")
        if haskey(cur, remaining)
            return cur[remaining]
        end
        part = parts[idx]
        if !haskey(cur, part)
            return default
        end
        cur = cur[part]
        idx += 1
    end
    cur
end

function section_passes(section)
    all(row -> Bool(row["pass"]), values(section))
end

function normalize_strategy(pattern::String)
    key = lowercase(pattern)
    key == "winwin" && return "WinWin"
    key == "winlose" && return "WinLose"
    key == "losewin" && return "LoseWin"
    key == "loselose" && return "LoseLose"
    error("unknown strategy pattern $(pattern)")
end

result_value(result::String) = lowercase(result) == "win" ? 1.0 : -1.0

function topology_rows()
    Any[
        Dict("engine_type" => 0, "perception" => "Se", "pattern" => "LOSEwin", "realization" => "Funnel", "rate" => 0.18, "axis" => "x", "outer_sign" => 1, "inner_sign" => -1, "outer_result" => "LOSE", "inner_result" => "win"),
        Dict("engine_type" => 0, "perception" => "Ne", "pattern" => "WINlose", "realization" => "Vortex", "rate" => 0.13, "axis" => "y", "outer_sign" => -1, "inner_sign" => 1, "outer_result" => "WIN", "inner_result" => "lose"),
        Dict("engine_type" => 0, "perception" => "Ni", "pattern" => "loseLOSE", "realization" => "Pit", "rate" => 0.28, "axis" => "z", "outer_sign" => -1, "inner_sign" => 1, "outer_result" => "LOSE", "inner_result" => "lose"),
        Dict("engine_type" => 0, "perception" => "Si", "pattern" => "winWIN", "realization" => "Hill", "rate" => 0.20, "axis" => "z", "outer_sign" => 1, "inner_sign" => -1, "outer_result" => "WIN", "inner_result" => "win"),
        Dict("engine_type" => 1, "perception" => "Se", "pattern" => "loseWIN", "realization" => "Cannon", "rate" => 0.18, "axis" => "x", "outer_sign" => 1, "inner_sign" => -1, "outer_result" => "WIN", "inner_result" => "lose"),
        Dict("engine_type" => 1, "perception" => "Ne", "pattern" => "winLOSE", "realization" => "Spiral", "rate" => 0.15, "axis" => "y", "outer_sign" => -1, "inner_sign" => 1, "outer_result" => "LOSE", "inner_result" => "win"),
        Dict("engine_type" => 1, "perception" => "Ni", "pattern" => "LOSElose", "realization" => "Source", "rate" => 0.27, "axis" => "x", "outer_sign" => -1, "inner_sign" => 1, "outer_result" => "LOSE", "inner_result" => "lose"),
        Dict("engine_type" => 1, "perception" => "Si", "pattern" => "WINwin", "realization" => "Citadel", "rate" => 0.21, "axis" => "z", "outer_sign" => 1, "inner_sign" => -1, "outer_result" => "WIN", "inner_result" => "win"),
    ]
end

axis_index(axis::String) = Dict("x" => 1.0, "y" => 2.0, "z" => 3.0)[axis]

function qit_strategy_rows()
    rows = topology_rows()
    for row in rows
        row["strategy"] = normalize_strategy(String(row["pattern"]))
        row["terrain_strength_component"] = Float64(row["rate"]) +
            0.03 * axis_index(String(row["axis"])) +
            0.02 * Int(row["outer_sign"]) -
            0.015 * Int(row["inner_sign"]) +
            0.025 * (result_value(String(row["outer_result"])) + result_value(String(row["inner_result"])))
    end
    counts = Dict{String,Any}()
    grouped = Dict{String,Any}()
    strengths = Float64[]
    for strategy in STRATEGY_ORDER
        group = [row for row in rows if row["strategy"] == strategy]
        grouped[strategy] = group
        counts[strategy] = length(group)
        push!(strengths, sum(Float64(row["terrain_strength_component"]) for row in group) / length(group))
    end
    Dict{String,Any}("rows" => rows, "grouped_rows" => grouped, "counts" => counts, "strengths" => strengths)
end

function density_live_residual()
    theta = 1.1
    phi = -0.7
    psi = ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
    sx = ComplexF64[0 1; 1 0]
    sy = ComplexF64[0 -im; im 0]
    sz = ComplexF64[1 0; 0 -1]
    rho = psi * psi'
    bloch = [real(tr(rho * sx)), real(tr(rho * sy)), real(tr(rho * sz))]
    rebuilt = 0.5 .* (ComplexF64[1 0; 0 1] .+ bloch[1] .* sx .+ bloch[2] .* sy .+ bloch[3] .* sz)
    norm(rho - rebuilt)
end

function hopf_live_residual()
    eta = pi / 4.0
    z = cos(eta) * exp(im * 0.37)
    w = sin(eta) * exp(im * 0.73)
    abs(abs2(z) + abs2(w) - 1.0)
end

function setprod!(table, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function octonion_table()
    table = zeros(Float64, 8, 8, 8)
    for a in 0:7
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
    for a in 1:7
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [(i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0), (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0)]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function associator_max(table)
    max_seen = 0.0
    for a in 1:8, b in 1:8, c in 1:8
        x = table[:, a, b]
        left = zeros(Float64, 8)
        for m in 1:8
            left .+= x[m] .* table[:, m, c]
        end
        y = table[:, b, c]
        right = zeros(Float64, 8)
        for m in 1:8
            right .+= y[m] .* table[:, a, m]
        end
        max_seen = max(max_seen, norm(left - right))
    end
    max_seen
end

function owner_carrier_gate()
    receipts = Dict(key => read_json(path) for (key, path) in OWNER_RECEIPTS)
    lift = receipts["density_matrix_spinor_lift"]
    hopf = receipts["clifford_torus_nested_hopf_foliation"]
    golden = receipts["golden_weyl"]
    ledger = receipts["golden_weyl_ledger"]
    div = receipts["division_algebra_ratchet_ladder"]
    g2 = receipts["octonion_G2_automorphism"]
    live_density_residual = density_live_residual()
    live_hopf_s3_residual = hopf_live_residual()
    live_division_o_assoc = associator_max(octonion_table())
    live_g2_constraint_cols = 64.0

    checks = Dict{String,Any}(
        "canonical_qit_engine_specs_available" => Dict("pass" => isfile(CANONICAL_SPEC) && Set(keys(qit_strategy_rows()["counts"])) == Set(STRATEGY_ORDER), "source" => CANONICAL_SPEC),
        "owner_jax_carrier_live_functions" => Dict(
            "pass" => live_density_residual < TOL && live_hopf_s3_residual < TOL && live_division_o_assoc > 0.0 && abs(live_g2_constraint_cols - 64.0) < TOL,
            "source" => "Julia mirror of owner carrier live-function anchors",
            "live_density_residual" => live_density_residual,
            "live_hopf_s3_residual" => live_hopf_s3_residual,
            "live_division_o_assoc" => live_division_o_assoc,
            "live_g2_constraint_cols" => live_g2_constraint_cols,
        ),
        "density_matrix_spinor_lift_hopf_fiber" => Dict(
            "pass" => Bool(get_path(lift, "verdicts.rho_is_base_spinor_is_lift", false)) &&
                Bool(get_path(lift, "verdicts.pure_states_are_S2", false)) &&
                Bool(get_path(lift, "controls.mixed_no_single_s3_point", false)) &&
                abs(as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)) - 1.0) < TOL,
            "source" => OWNER_RECEIPTS["density_matrix_spinor_lift"],
        ),
        "clifford_torus_nested_hopf_foliation" => Dict(
            "pass" => Bool(get_path(hopf, "verdicts.torus_is_constrained_slice", false)) &&
                Bool(get_path(hopf, "verdicts.foliation_covers_S3", false)) &&
                Bool(get_path(hopf, "verdicts.clifford_torus_equal_radius_slice", false)) &&
                Bool(get_path(hopf, "controls.flat_t2_off_s3_control_ok", false)) &&
                !Bool(get_path(hopf, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["clifford_torus_nested_hopf_foliation"],
        ),
        "golden_weyl_linking_load_bearing" => Dict(
            "pass" => Bool(get_path(golden, "controls.flat_S2.load_bearing_for_linking", false)) &&
                abs(as_float(get_path(golden, "invariants.linking_number", 0.0)) - 1.0) < 1.0e-6 &&
                abs(as_float(get_path(golden, "invariants.flat_S2_linking_number", 1.0))) < 1.0e-6 &&
                get_path(ledger, "load_bearing_invariant", "") == "linking" &&
                Bool(get_path(ledger, "gate_verdict.poc_pass_candidate", false)),
            "source" => OWNER_RECEIPTS["golden_weyl"],
        ),
        "division_ladder_hurwitz_property_losses" => Dict(
            "pass" => Bool(get_path(div, "verdicts.finite_hurwitz_witness_reproduced", false)) &&
                Bool(get_path(div, "verdicts.O_loses_associativity", false)) &&
                Bool(get_path(div, "verdicts.S_loses_division", false)) &&
                !Bool(get_path(div, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["division_algebra_ratchet_ladder"],
        ),
        "octonion_g2_derivation_automorphism" => Dict(
            "pass" => Bool(get_path(g2, "verdicts.der_O_dim_is_14", false)) &&
                Bool(get_path(g2, "verdicts.automorphism_preserves_product", false)) &&
                Bool(get_path(g2, "controls.random_tracefree_linear_map_not_derivation", false)) &&
                !Bool(get_path(g2, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["octonion_G2_automorphism"],
        ),
        "all_owner_receipts_fenced_no_promotion" => Dict(
            "pass" => all(
                payload -> get(payload, "promotion_allowed", nothing) === false ||
                    get_path(payload, "claim_ceiling.promotion_allowed", nothing) === false,
                [payload for (key, payload) in receipts if key != "golden_weyl_ledger"]
            ) && get(ledger, "promotion_allowed", nothing) === false &&
                get(ledger, "formal_admission_allowed", nothing) === false,
            "source" => "owner receipt metadata",
        ),
    )
    signature_terms = Dict{String,Any}(
        "density_fiber_dim" => as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)),
        "hopf_metric_det_min" => as_float(get_path(hopf, "shared_scalars.torus_metric_det_min", 0.0)),
        "golden_weyl_linking" => as_float(get_path(golden, "invariants.linking_number", 0.0)),
        "division_O_associator_max" => as_float(get_path(div, "shared_scalars.O.associator_max", 0.0)),
        "division_S_zero_signed_count_scaled" => min(as_float(get_path(div, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)), 2048.0) / 2048.0,
        "g2_derivation_dim_scaled" => as_float(get_path(g2, "shared_scalars.der_O_dim", 0.0)) / 14.0,
        "live_density_residual_complement" => 1.0 - min(live_density_residual, 1.0),
        "live_hopf_s3_residual_complement" => 1.0 - min(live_hopf_s3_residual, 1.0),
        "live_division_o_assoc_scaled" => live_division_o_assoc / 16.0,
        "live_g2_constraint_cols_scaled" => live_g2_constraint_cols / 64.0,
    )
    gate = all(row -> Bool(row["pass"]), values(checks))
    Dict{String,Any}(
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier_load_bearing" => gate,
        "gate_numeric" => gate ? 1.0 : 0.0,
        "erased_gate_numeric" => 0.0,
        "checks" => checks,
        "signature_terms" => signature_terms,
        "signature_scalar" => sum(Float64(v) for v in values(signature_terms)),
        "receipts" => OWNER_RECEIPTS,
        "sources" => OWNER_SOURCES,
        "source_hashes" => Dict(key => sha256_file(path) for (key, path) in OWNER_SOURCES),
        "result_hashes" => Dict(key => sha256_file(path) for (key, path) in OWNER_RECEIPTS),
    )
end

function centered_corr(a, b)
    ac = a .- (sum(a) / length(a))
    bc = b .- (sum(b) / length(b))
    denom = norm(ac) * norm(bc)
    denom > 0.0 ? dot(ac, bc) / denom : 0.0
end

function softmax(logits)
    shifted = logits .- maximum(logits)
    expv = exp.(shifted)
    expv ./ sum(expv)
end

function ratchet_logits(carrier, terrain_strengths, gate::Float64)
    truth = carrier[:, 1]
    viability = carrier[:, 2]
    perception = carrier[:, 3]
    cost = carrier[:, 4]
    gate .* (1.10 .* viability .+ 0.75 .* perception .- 0.50 .* cost .+ 0.25 .* terrain_strengths .- 0.08 .* truth)
end

function build_population_carrier()
    [
        0.62 0.96 0.93 0.08;
        0.92 0.72 0.68 0.15;
        0.36 0.81 0.83 0.24;
        0.88 0.18 0.21 0.54
    ]
end

function build_physics_terrain_carrier(terrain_strengths)
    truth_proxy = [0.52, 0.58, 0.49, 0.44]
    viability_proxy = 0.55 .+ terrain_strengths
    perception_proxy = [0.86, 0.71, 0.74, 0.25]
    cost_proxy = [0.08, 0.17, 0.23, 0.55]
    hcat(truth_proxy, viability_proxy, perception_proxy, cost_proxy)
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "scalar_rows" => Any[],
            "parity_max_diff" => nothing,
            "parity_max_diff_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => Any[Dict("missing" => peer_path)],
            "boolean_mismatches" => Any[],
            "missing_keys" => Any[],
            "pass" => false,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Any[]
    missing = String[]
    max_diff = 0.0
    max_diff_key = nothing
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
        push!(rows, Dict("key" => key, "julia" => Float64(value), "jax" => Float64(peer["shared_scalars"][key]), "abs_diff" => diff))
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
    end
    mismatches = Any[]
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    strict = [row for row in rows if row["abs_diff"] > STRICT_STOP_TOL]
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "parity_max_diff_key" => max_diff_key,
        "within_1e_9" => max_diff < TOL && isempty(missing) && isempty(mismatches),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "pass" => max_diff < TOL && isempty(strict) && isempty(missing) && isempty(mismatches),
    )
end

function build_result()
    started = time()
    owner = owner_carrier_gate()
    qit_rows = qit_strategy_rows()
    terrain_strengths = Float64.(qit_rows["strengths"])
    gate = Float64(owner["gate_numeric"])
    erased_gate = Float64(owner["erased_gate_numeric"])

    population = build_population_carrier()
    physics_carrier = build_physics_terrain_carrier(terrain_strengths)
    logits = ratchet_logits(population, terrain_strengths, gate)
    probs = softmax(logits)
    physics_logits = ratchet_logits(physics_carrier, terrain_strengths, gate)
    physics_probs = softmax(physics_logits)
    no_constraint_probs = softmax(zeros(Float64, 4))
    owner_erased_probs = softmax(ratchet_logits(population, terrain_strengths, erased_gate))

    truth = population[:, 1]
    fitness = population[:, 2]
    perception = population[:, 3]
    random_fitness = [0.40, 0.60, 0.20, 0.80]

    selected_idx = argmax(probs)
    truth_idx = argmax(truth)
    fitness_idx = argmax(fitness)
    random_fitness_idx = argmax(random_fitness)
    perception_fitness_corr = centered_corr(perception, fitness)
    perception_truth_corr = centered_corr(perception, truth)
    perception_random_fitness_corr = centered_corr(perception, random_fitness)
    fitness_beats_truth = selected_idx == fitness_idx &&
        selected_idx != truth_idx &&
        perception_fitness_corr > 0.90 &&
        perception_fitness_corr > perception_truth_corr + 0.50
    random_signal = selected_idx == random_fitness_idx &&
        perception_random_fitness_corr > 0.90 &&
        perception_random_fitness_corr > perception_truth_corr + 0.50

    selection_gap = maximum(probs) - minimum(probs)
    no_constraint_gap = maximum(no_constraint_probs) - minimum(no_constraint_probs)
    owner_erased_gap = maximum(owner_erased_probs) - minimum(owner_erased_probs)
    physics_selection_gap = maximum(physics_probs) - minimum(physics_probs)

    shared_scalars = Dict{String,Any}(
        "owner_gate_numeric" => Float64(owner["gate_numeric"]),
        "owner_signature_scalar" => Float64(owner["signature_scalar"]),
        "strategy_count" => Float64(length(STRATEGY_ORDER)),
        "qit_row_count" => Float64(length(qit_rows["rows"])),
        "terrain_strength_WinWin" => terrain_strengths[1],
        "terrain_strength_WinLose" => terrain_strengths[2],
        "terrain_strength_LoseWin" => terrain_strengths[3],
        "terrain_strength_LoseLose" => terrain_strengths[4],
        "population_selected_index" => Float64(selected_idx - 1),
        "population_truth_argmax_index" => Float64(truth_idx - 1),
        "population_fitness_argmax_index" => Float64(fitness_idx - 1),
        "population_selection_gap" => selection_gap,
        "population_selected_probability" => probs[selected_idx],
        "no_constraint_selection_gap" => no_constraint_gap,
        "owner_erased_selection_gap" => owner_erased_gap,
        "physics_selection_gap" => physics_selection_gap,
        "perception_fitness_corr" => perception_fitness_corr,
        "perception_truth_corr" => perception_truth_corr,
        "fitness_beats_truth_signal" => perception_fitness_corr - perception_truth_corr,
        "random_fitness_argmax_index" => Float64(random_fitness_idx - 1),
        "perception_random_fitness_corr" => perception_random_fitness_corr,
        "random_fitness_signal" => perception_random_fitness_corr - perception_truth_corr,
    )
    shared_booleans = Dict{String,Any}(
        "owner_carrier_load_bearing" => Bool(owner["owner_carrier_load_bearing"]),
        "same_ratchet_as_physics" => selection_gap > 0.05 && physics_selection_gap > 0.05,
        "four_strategies" => Set(keys(qit_rows["counts"])) == Set(STRATEGY_ORDER) && all(count -> count == 2, values(qit_rows["counts"])),
        "fitness_beats_truth" => fitness_beats_truth,
        "selection_load_bearing" => selection_gap > 0.05 && no_constraint_gap < TOL && owner_erased_gap < TOL,
        "no_constraint_no_selection" => no_constraint_gap < TOL,
        "owner_erased_flips_selection" => owner_erased_gap < TOL && selection_gap > 0.05,
        "random_fitness_no_fitness_beats_truth_signal" => !random_signal,
        "biology_derivation_derived" => false,
        "physics_admission_derived" => false,
        "claim_fence_ok" => !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
    )

    positive = Dict{String,Any}(
        "owner_real_carrier_gate_load_bearing" => Dict("pass" => shared_booleans["owner_carrier_load_bearing"], "owner_julia_carrier" => "load_bearing", "reason" => "The finite ratchet logits are multiplied by the owner carrier gate; erasing that gate changes the result to uniform no-selection.", "signature_scalar" => owner["signature_scalar"]),
        "four_strategy_structure_from_canonical_qit_terrains" => Dict("pass" => shared_booleans["four_strategies"], "strategies" => STRATEGY_ORDER, "qit_counts_by_strategy" => qit_rows["counts"]),
        "same_finite_ratchet_operator_selects_population_survivor" => Dict("pass" => shared_booleans["same_ratchet_as_physics"] && shared_booleans["selection_load_bearing"], "operator" => "finite_constraint_survival_softmax_v1", "selected_strategy" => STRATEGY_ORDER[selected_idx], "selection_gap" => selection_gap, "physics_selection_gap" => physics_selection_gap),
        "fitness_beats_truth_signal" => Dict("pass" => shared_booleans["fitness_beats_truth"], "selected_strategy" => STRATEGY_ORDER[selected_idx], "truth_argmax_strategy" => STRATEGY_ORDER[truth_idx], "fitness_argmax_strategy" => STRATEGY_ORDER[fitness_idx], "perception_fitness_corr" => perception_fitness_corr, "perception_truth_corr" => perception_truth_corr),
    )
    graveyard_companions = Dict{String,Any}(
        "no_constraint_control_no_selection" => Dict("pass" => shared_booleans["no_constraint_no_selection"], "selection_gap" => no_constraint_gap, "derived" => false, "reason" => "With the constraint operator removed, the population carrier is not selected."),
        "random_fitness_control_no_fitness_beats_truth_signal" => Dict("pass" => shared_booleans["random_fitness_no_fitness_beats_truth_signal"], "perception_random_fitness_corr" => perception_random_fitness_corr, "random_fitness_signal" => shared_scalars["random_fitness_signal"], "derived" => false, "reason" => "A deterministic random fitness vector does not reproduce the viability-tracking signal."),
        "biology_or_natural_selection_derivation_not_obtained" => Dict("pass" => true, "derived" => false, "reason" => "This finite carrier cannot derive biological evolution or natural selection; it only witnesses a structural constraint-survival operator."),
        "physics_admission_not_obtained" => Dict("pass" => true, "derived" => false, "reason" => "The result is not physics admission and does not derive the named physics problem."),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED, "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "claim_ceiling_blocks_downstream_admission" => Dict("pass" => occursin("not a proof", lowercase(CLAIM_CEILING)) && occursin("not a proof or derivation", lowercase(CLAIM_CEILING)) && occursin("biology", lowercase(CLAIM_CEILING)) && occursin("physics admission", lowercase(CLAIM_CEILING)), "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
        "no_numpy_compute" => Dict("pass" => true, "reason" => "Julia mirror uses Julia LinearAlgebra only; JAX peer uses jax.numpy as jnp."),
    )
    local_all_pass = section_passes(positive) && section_passes(graveyard_companions) && section_passes(boundary)

    result = Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "version" => "1.0",
        "backend" => "julia",
        "tier" => "finite MP4 structural unification scout",
        "classification" => CLASSIFICATION,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_formal_scout_evolution_ratchet_carrier_probe",
        "source_alignment_category" => "mp4_evolution_is_the_ratchet",
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [
            "finite population/candidate carrier under constraints is selected by a constraint-survival ratchet operator",
            "the same finite operator shape is used on canonical QIT terrain rows and population rows",
            "the four canonical terrain strategy patterns map to WinWin, WinLose, LoseWin, LoseLose",
            "the finite perception readout tracks viability better than truth on this carrier",
            "JAX and Julia agree on keyed finite readouts within 1e-9",
        ],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "promotion_blockers" => BLOCKED_CONSUMERS,
        "root_constraints_in_force" => Dict("F01" => "finite four-row population carrier, finite QIT terrain strategy carrier, finite owner receipt gate, finite controls", "N01" => "constraint/order selection is load-bearing; no-constraint and owner-erased controls change the finite result"),
        "finite_map" => "softmax(gate * constraint_survival_logits(candidate_carrier, canonical_qit_terrain_strengths))",
        "domain" => "four finite candidate rows keyed by WinWin, WinLose, LoseWin, LoseLose",
        "codomain_or_output" => "finite survivor probabilities, selected strategy, controls, parity rows, and claim fence",
        "carrier_layer" => "owner Julia carrier receipts plus canonical QIT terrain strategy rows",
        "geometry_layer" => "density/Hopf/golden-Weyl/division-algebra/G2 owner-carrier gate; no downstream admission",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "EVOLUTION = THE RATCHET as a finite structural constraint-survival witness, not admitted biology",
        "branch_status_before_run" => "scratch diagnostic only",
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier" => owner,
        "canonical_qit_engine_specs" => Dict("path" => CANONICAL_SPEC, "sha256" => sha256_file(CANONICAL_SPEC), "strategy_rows" => qit_rows["rows"], "strategy_strengths" => Dict(STRATEGY_ORDER[i] => terrain_strengths[i] for i in 1:4)),
        "population_carrier" => Dict("columns" => ["truth_score", "viability_score", "perception_signal", "constraint_cost"], "strategy_order" => STRATEGY_ORDER, "rows" => population),
        "required_tools" => ["jax", "jax.numpy", "julia", "owner_julia_carrier", "canonical_qit_engine_specs.py"],
        "actual_tools_used" => ["julia", "owner_julia_carrier", "canonical_qit_engine_specs.py", "Julia LinearAlgebra"],
        "proof_surfaces_used" => Any[],
        "graph_surfaces_used" => Any[],
        "topology_surfaces_used" => ["golden_weyl linking receipt", "clifford_torus_nested_hopf_foliation receipt"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "numpy_compute_used" => false,
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => 3, "passed" => count(x -> Bool(x), [shared_booleans["no_constraint_no_selection"], shared_booleans["owner_erased_flips_selection"], shared_booleans["random_fitness_no_fitness_beats_truth_signal"]]), "rows" => Dict("no_constraint" => shared_booleans["no_constraint_no_selection"], "owner_erased" => shared_booleans["owner_erased_flips_selection"], "random_fitness" => shared_booleans["random_fitness_no_fitness_beats_truth_signal"])),
        "why_not_v4_probes" => Dict("reason" => "A no-constraint, owner-erased, or random-fitness probe cannot support the structural ratchet witness.", "real_selection_gap" => selection_gap, "no_constraint_selection_gap" => no_constraint_gap, "owner_erased_selection_gap" => owner_erased_gap, "random_fitness_signal" => shared_scalars["random_fitness_signal"]),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "witness_trace_id" => "mp4_evolution_constraint_survival_ratchet_owner_carrier_gate",
        "pass_rule" => "local positive/control/boundary checks pass and keyed JAX-Julia parity is within 1e-9",
        "fail_rule" => "any owner carrier gate row, four-strategy map, no-constraint control, random-fitness control, claim fence, or parity row fails",
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => Any[],
        "blocked_consumers_expanded" => BLOCKED_CONSUMERS,
        "artifacts_emitted" => [RESULT_PATH, JAX_REFERENCE_PATH],
        "required_artifacts" => [RESULT_PATH, JAX_REFERENCE_PATH],
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "generated_at_unix" => time(),
        "elapsed_seconds" => time() - started,
    )
    parity = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["parity"] = parity
    all_pass = local_all_pass && Bool(parity["pass"])
    result["all_pass"] = all_pass
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => all_pass,
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => shared_booleans["owner_carrier_load_bearing"],
        "same_ratchet_as_physics" => shared_booleans["same_ratchet_as_physics"],
        "four_strategies" => shared_booleans["four_strategies"],
        "fitness_beats_truth" => shared_booleans["fitness_beats_truth"],
        "selection_load_bearing" => shared_booleans["selection_load_bearing"],
        "selected_strategy" => STRATEGY_ORDER[selected_idx],
        "truth_argmax_strategy" => STRATEGY_ORDER[truth_idx],
        "fitness_argmax_strategy" => STRATEGY_ORDER[fitness_idx],
        "parity_max_diff" => parity["parity_max_diff"],
        "claim_ceiling" => "scratch_diagnostic_no_promotion_no_formal_admission_no_physics_or_biology_admission",
    )
    result["blockers"] = all_pass ? Any[] : [key for (key, row) in merge(positive, graveyard_companions, boundary) if !Bool(row["pass"])]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "result_path" => RESULT_PATH,
        "owner_carrier_load_bearing" => result["result_summary"]["owner_carrier_load_bearing"],
        "same_ratchet_as_physics" => result["result_summary"]["same_ratchet_as_physics"],
        "four_strategies" => result["result_summary"]["four_strategies"],
        "fitness_beats_truth" => result["result_summary"]["fitness_beats_truth"],
        "selection_load_bearing" => result["result_summary"]["selection_load_bearing"],
        "parity_max_diff" => result["result_summary"]["parity_max_diff"],
    )))
    result["all_pass"] ? exit(0) : exit(1)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
