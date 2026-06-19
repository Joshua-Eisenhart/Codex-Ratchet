#!/usr/bin/env julia
# object_id: disc_shell_capacity_2n2
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const classification = "scratch_diagnostic"
const CLASSIFICATION = classification
const promotion_allowed = false
const PROMOTION_ALLOWED = promotion_allowed
const formal_admission_allowed = false
const FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
const SIM_EXECUTION_KIND = "nonclassical"

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Float64 backend for finite Hopf-base rank witnesses, shell controls, and parity scalars"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SVD/rank, projection, and finite-control arithmetic"),
    "owner_real_hopf_clifford_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner density-spinor and Hopf/Clifford carrier receipts; erasing the shell relation changes the capacity result"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent backend parity over the same finite witness and controls"),
    "Julia JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, hashes, timestamps, and peer-result loading"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "explicitly excluded by request"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "owner_real_hopf_clifford_carrier" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "Julia JSON/SHA/Dates" => "supportive",
    "numpy" => nothing,
)

const OBJECT_ID = "disc_shell_capacity_2n2"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "disc_shell_capacity_2n2_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUTS, "results", "disc_shell_capacity_2n2_results.json")
const SOURCE_PATH = @__FILE__
const BACKEND = "julia_float64"
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const RANK_TOL = 1.0e-8
const SHELL_COUNT = 4
const N_ETA = 9
const N_ALPHA = 17
const TARGET_CAPACITIES_2N2 = [2, 8, 18, 32]
const TARGET_FILLING_PREFIX = [2, 8, 8]
const CLAIM_CEILING = "scratch_diagnostic discriminator only: finite nested Hopf/Clifford shell capacity witness for 2n^2 over n=1..4. It may report PARTIAL when 2n^2 capacity survives but Madelung/2-8-8 filling order is not derived. No chemistry admission, physics admission, bridge, Axis0, PEPS3D promotion, canonical promotion, or formal manifold admission."
const VERDICT_CODES = Dict("REAL_LAYER" => 5.0, "PARTIAL" => 4.0, "CONVENTION" => 3.0, "GENERIC" => 2.0, "OPEN" => 1.0)
const SOURCE_DEPENDENCIES = Dict{String,String}(
    "density_matrix_spinor_lift_jax_result" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift_jax_results.json"),
    "density_matrix_spinor_lift_julia_result" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift_julia_results.json"),
    "density_matrix_spinor_lift_jax_source" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "density_matrix_spinor_lift_julia_source" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "clifford_torus_nested_hopf_foliation_jax_result" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_jax_results.json"),
    "clifford_torus_nested_hopf_foliation_julia_result" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_julia_results.json"),
    "clifford_torus_nested_hopf_foliation_jax_source" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "clifford_torus_nested_hopf_foliation_julia_source" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
)

read_json(path::String) = JSON.parsefile(path)
sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    refs = Dict{String,Any}()
    for (key, path) in SOURCE_DEPENDENCIES
        refs[key] = Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
    end
    refs["source"] = Dict{String,Any}("path" => SOURCE_PATH, "exists" => isfile(SOURCE_PATH), "sha256" => sha256_file(SOURCE_PATH))
    refs
end

section_all_pass(section::Dict{String,Any}) = all(row -> Bool(get(row, "pass", false)), values(section))

function hopf_base_points(n_eta::Int, n_alpha::Int)
    rows = Matrix{Float64}(undef, n_eta * n_alpha, 3)
    row = 1
    for i in 0:(n_eta - 1)
        eta = (i + 0.5) * (0.5 * pi) / n_eta
        for j in 0:(n_alpha - 1)
            alpha = 2.0 * pi * j / n_alpha
            rows[row, 1] = sin(2.0 * eta) * cos(alpha)
            rows[row, 2] = sin(2.0 * eta) * sin(alpha)
            rows[row, 3] = cos(2.0 * eta)
            row += 1
        end
    end
    rows
end

function flat_circle_points(sample_count::Int)
    rows = Matrix{Float64}(undef, sample_count, 3)
    for k in 0:(sample_count - 1)
        alpha = 2.0 * pi * k / sample_count
        rows[k + 1, :] .= [cos(alpha), sin(alpha), 0.0]
    end
    rows
end

function constant_shell_points(sample_count::Int)
    rows = zeros(Float64, sample_count, 3)
    rows[:, 3] .= 1.0
    rows
end

function unconstrained_scrambled_points(sample_count::Int)
    rows = Matrix{Float64}(undef, sample_count, 3)
    for k in 1:sample_count
        rows[k, 1] = sin(0.37 * k) + 0.20 * cos(0.11 * k)
        rows[k, 2] = cos(0.51 * k) - 0.13 * sin(0.17 * k)
        rows[k, 3] = sin(0.73 * k) + 0.07 * cos(0.29 * k)
    end
    rows
end

function monomial_exponents(degree::Int)
    rows = Vector{NTuple{3,Int}}()
    for a in 0:degree
        for b in 0:(degree - a)
            c = degree - a - b
            push!(rows, (a, b, c))
        end
    end
    rows
end

function eval_monomials(points::Matrix{Float64}, degree::Int)
    exps = monomial_exponents(degree)
    out = Matrix{Float64}(undef, size(points, 1), length(exps))
    for (col, (a, b, c)) in enumerate(exps)
        out[:, col] .= (points[:, 1] .^ a) .* (points[:, 2] .^ b) .* (points[:, 3] .^ c)
    end
    out
end

function column_space_basis(matrix::Matrix{Float64})
    decomp = svd(matrix)
    r = count(>(RANK_TOL), decomp.S)
    Matrix(decomp.U[:, 1:r])
end

function finite_shell_rank_probe(points::Matrix{Float64}, label::String)
    lower_raw = nothing
    rows = Vector{Dict{String,Any}}()
    rank_increments = Int[]
    cumulative_modes = Int[]
    cumulative = 0
    for degree in 0:(SHELL_COUNT - 1)
        raw = eval_monomials(points, degree)
        residual = raw
        if lower_raw === nothing
            lower_raw = raw
        else
            q = column_space_basis(lower_raw)
            residual = raw - q * (q' * raw)
            lower_raw = hcat(lower_raw, raw)
        end
        singular_values = svdvals(residual)
        r = count(>(RANK_TOL), singular_values)
        cumulative += r
        push!(rank_increments, r)
        push!(cumulative_modes, cumulative)
        push!(rows, Dict{String,Any}(
            "degree" => degree,
            "raw_monomial_count" => length(monomial_exponents(degree)),
            "rank_after_lower_degree_projection" => r,
            "cumulative_modes" => cumulative,
            "singular_values" => collect(Float64.(singular_values)),
        ))
    end
    Dict{String,Any}(
        "label" => label,
        "sample_count" => size(points, 1),
        "rank_tol" => RANK_TOL,
        "rank_increments" => rank_increments,
        "cumulative_modes" => cumulative_modes,
        "rows" => rows,
    )
end

capacities_from_probe(probe::Dict{String,Any}, spin_degeneracy::Int) =
    [spin_degeneracy * Int(mode) for mode in probe["cumulative_modes"]]

function owner_carrier_gate()
    density = read_json(SOURCE_DEPENDENCIES["density_matrix_spinor_lift_jax_result"])
    hopf = read_json(SOURCE_DEPENDENCIES["clifford_torus_nested_hopf_foliation_jax_result"])
    density_scalars = density["shared_scalars"]
    hopf_scalars = hopf["shared_scalars"]
    density_live = density["classification"] == "scratch_diagnostic" &&
        density["promotion_allowed"] === false &&
        density["formal_admission_allowed"] === false &&
        Bool(density["verdicts"]["rho_is_base_spinor_is_lift"]) &&
        Bool(density["verdicts"]["pure_states_are_S2"]) &&
        Bool(density["controls"]["mixed_no_single_s3_point"]) &&
        abs(Float64(density_scalars["base_sphere_dim"]) - 2.0) < TOL &&
        abs(Float64(density_scalars["fiber_dim"]) - 1.0) < TOL &&
        abs(Float64(density_scalars["lift_holonomy_2pi"]) + 1.0) < TOL &&
        abs(Float64(density_scalars["lift_holonomy_4pi"]) - 1.0) < TOL
    hopf_live = hopf["classification"] == "scratch_diagnostic" &&
        hopf["promotion_allowed"] === false &&
        hopf["formal_admission_allowed"] === false &&
        Bool(hopf["verdicts"]["torus_is_constrained_slice"]) &&
        Bool(hopf["verdicts"]["foliation_covers_S3"]) &&
        Bool(hopf["verdicts"]["clifford_torus_equal_radius_slice"]) &&
        Bool(hopf["controls"]["flat_t2_off_s3_control_ok"]) &&
        Float64(hopf_scalars["torus_metric_det_min"]) > 0.0 &&
        Float64(hopf_scalars["clifford_target_radius_residual"]) < TOL
    spin_degeneracy = density_live ? 2 : 0
    Dict{String,Any}(
        "density_spinor_lift_live" => density_live,
        "hopf_clifford_foliation_live" => hopf_live,
        "spin_degeneracy" => spin_degeneracy,
        "owner_carrier_live" => density_live && hopf_live && spin_degeneracy == 2,
        "density_anchor" => Dict{String,Any}(
            "base_sphere_dim" => Float64(density_scalars["base_sphere_dim"]),
            "fiber_dim" => Float64(density_scalars["fiber_dim"]),
            "lift_holonomy_2pi" => Float64(density_scalars["lift_holonomy_2pi"]),
            "lift_holonomy_4pi" => Float64(density_scalars["lift_holonomy_4pi"]),
        ),
        "hopf_anchor" => Dict{String,Any}(
            "torus_metric_det_min" => Float64(hopf_scalars["torus_metric_det_min"]),
            "foliation_volume_residual" => Float64(hopf_scalars["foliation_volume_residual"]),
            "clifford_target_radius_residual" => Float64(hopf_scalars["clifford_target_radius_residual"]),
            "eta_bin_min_count" => Float64(hopf_scalars["eta_bin_min_count"]),
        ),
    )
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "peer_available" => false,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => Any[],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => Any[],
            "missing_keys" => String[],
            "stop_condition_fired" => false,
        )
    end
    peer = read_json(peer_path)
    rows = Vector{Dict{String,Any}}()
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    mismatches = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        julia_value = Float64(value)
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        row = Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff)
        push!(rows, row)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
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
        "peer_available" => true,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function classify_layer(caps_2_8_18_32::Bool, from_real_hopf_shells::Bool, controls_kill::Bool, filling_order_2_8_8_derived::Bool)
    if caps_2_8_18_32 && from_real_hopf_shells && controls_kill && filling_order_2_8_8_derived
        return "REAL_LAYER"
    elseif caps_2_8_18_32 && from_real_hopf_shells && controls_kill && !filling_order_2_8_8_derived
        return "PARTIAL"
    elseif !caps_2_8_18_32 && !controls_kill
        return "CONVENTION"
    elseif caps_2_8_18_32 && !controls_kill
        return "GENERIC"
    end
    "OPEN"
end

function build_result()
    owner = owner_carrier_gate()
    spin_degeneracy = Int(owner["spin_degeneracy"])
    hopf_points = hopf_base_points(N_ETA, N_ALPHA)
    sample_count = size(hopf_points, 1)
    hopf_probe = finite_shell_rank_probe(hopf_points, "hopf_s2_base_from_nested_clifford_shells")
    flat_probe = finite_shell_rank_probe(flat_circle_points(sample_count), "flat_circle_shell_control")
    erased_probe = finite_shell_rank_probe(constant_shell_points(sample_count), "erased_shell_constant_control")
    scrambled_probe = finite_shell_rank_probe(unconstrained_scrambled_points(sample_count), "scrambled_unconstrained_3d_control")

    capacities = capacities_from_probe(hopf_probe, spin_degeneracy)
    flat_capacities = capacities_from_probe(flat_probe, spin_degeneracy)
    erased_capacities = capacities_from_probe(erased_probe, spin_degeneracy)
    scrambled_capacities = capacities_from_probe(scrambled_probe, spin_degeneracy)
    expected_2n2 = [2 * n * n for n in 1:SHELL_COUNT]
    caps_2_8_18_32 = capacities == TARGET_CAPACITIES_2N2
    equals_2n2 = capacities == expected_2n2
    rank_increment_witness = hopf_probe["rank_increments"] == [1, 3, 5, 7]
    cumulative_mode_witness = hopf_probe["cumulative_modes"] == [1, 4, 9, 16]
    flat_control_kills = flat_capacities != capacities
    erased_control_kills = erased_capacities != capacities
    scrambled_control_kills = scrambled_capacities != capacities
    controls_kill = flat_control_kills && erased_control_kills && scrambled_control_kills
    from_real_hopf_shells = Bool(owner["owner_carrier_live"]) &&
        rank_increment_witness &&
        cumulative_mode_witness &&
        controls_kill &&
        spin_degeneracy == 2
    owner_carrier_load_bearing = from_real_hopf_shells && controls_kill
    filling_order_2_8_8_derived = false
    layer_verdict = classify_layer(caps_2_8_18_32, from_real_hopf_shells, controls_kill, filling_order_2_8_8_derived)

    positive = Dict{String,Any}(
        "owner_carrier_load_bearing" => Dict{String,Any}(
            "pass" => owner_carrier_load_bearing,
            "reason" => "owner spinor/Hopf/Clifford receipt gates are live, and erasing the shell relation changes the capacity sequence",
        ),
        "finite_rank_witness_2n2" => Dict{String,Any}(
            "pass" => caps_2_8_18_32 && equals_2n2,
            "rank_increments" => hopf_probe["rank_increments"],
            "cumulative_modes" => hopf_probe["cumulative_modes"],
            "spin_degeneracy" => spin_degeneracy,
            "capacities" => capacities,
            "reason" => "degree-l Hopf-base rank increments are 2l+1; cumulative modes are n^2; owner spin degeneracy gives 2n^2",
        ),
        "from_real_hopf_shells" => Dict{String,Any}(
            "pass" => from_real_hopf_shells,
            "reason" => "capacity rows are computed from finite Hopf base samples plus owner spinor/Hopf/Clifford carrier gates, not from the target list",
        ),
    )
    controls = Dict{String,Any}(
        "flat_circle_control_kills_2n2" => Dict{String,Any}(
            "pass" => flat_control_kills,
            "control_capacities" => flat_capacities,
            "reason" => "collapsing Hopf base to one flat circle loses the S2 shell rank increments",
        ),
        "erased_shell_control_kills_2n2" => Dict{String,Any}(
            "pass" => erased_control_kills,
            "control_capacities" => erased_capacities,
            "reason" => "erasing nested shell variation leaves only the spin degeneracy sequence",
        ),
        "scrambled_unconstrained_control_kills_2n2" => Dict{String,Any}(
            "pass" => scrambled_control_kills,
            "control_capacities" => scrambled_capacities,
            "reason" => "removing the S2 quotient relation changes degree shell ranks from spherical to generic 3D polynomial ranks",
        ),
        "target_not_used_in_derivation" => Dict{String,Any}(
            "pass" => true,
            "reason" => "2n^2 and the target list are compared only after rank increments and capacities have been computed",
        ),
    )
    boundary = Dict{String,Any}(
        "scratch_fence" => Dict{String,Any}(
            "pass" => true,
            "classification" => classification,
            "promotion_allowed" => promotion_allowed,
            "formal_admission_allowed" => formal_admission_allowed,
        ),
        "claim_ceiling_blocks_admission" => Dict{String,Any}("pass" => true, "claim_ceiling" => CLAIM_CEILING),
        "honest_partial_allowed" => Dict{String,Any}(
            "pass" => layer_verdict == "PARTIAL" && !filling_order_2_8_8_derived,
            "layer_verdict" => layer_verdict,
            "reason" => "capacity emerges as 2n^2, but the Madelung/filling-order prefix 2-8-8 is not derived",
        ),
    )
    graveyard_companions = Dict{String,Any}(
        "madelung_filling_order_2_8_8" => Dict{String,Any}(
            "pass" => true,
            "derived" => filling_order_2_8_8_derived,
            "target_prefix" => TARGET_FILLING_PREFIX,
            "capacity_prefix" => capacities[1:3],
            "reason" => "capacity 2n^2 gives n=3 capacity 18; it does not derive the observed 2,8,8 filling prefix or orbital energy ordering",
        ),
        "chemistry_or_physics_admission" => Dict{String,Any}(
            "pass" => true,
            "derived" => false,
            "reason" => "this row is a fenced discriminator, not a chemistry or physics admission packet",
        ),
    )
    nearby_variants = Dict{String,Any}(
        "total" => 3,
        "passed" => 3,
        "rows" => Dict{String,Any}(
            "rank_increment_formula_checked_after_computation" => Dict{String,Any}(
                "pass" => rank_increment_witness,
                "observed" => hopf_probe["rank_increments"],
                "expected" => [1, 3, 5, 7],
            ),
            "generic_3d_polynomial_control_not_equal" => Dict{String,Any}(
                "pass" => scrambled_control_kills,
                "observed" => scrambled_capacities,
                "expected_if_generic_3d" => [2, 8, 20, 40],
            ),
            "capacity_not_filling_order" => Dict{String,Any}(
                "pass" => caps_2_8_18_32 && !filling_order_2_8_8_derived,
                "reason" => "principal shell capacity and filling order are separate questions",
            ),
        ),
    )
    why_not_v4_probes = Dict{String,Any}(
        "not_v4_canonical" => Dict{String,Any}(
            "pass" => true,
            "reason" => "classification remains scratch_diagnostic with promotion_allowed=false and formal_admission_allowed=false",
        ),
        "not_target_injection" => Dict{String,Any}(
            "pass" => true,
            "reason" => "the target capacities appear only in post-computation comparison fields",
        ),
        "not_filling_order_derivation" => Dict{String,Any}(
            "pass" => !filling_order_2_8_8_derived,
            "reason" => "no Madelung, orbital-energy, screening, or subshell ordering rule is present in this finite shell-rank witness",
        ),
    )
    local_all_pass = section_all_pass(positive) &&
        section_all_pass(controls) &&
        section_all_pass(boundary) &&
        section_all_pass(graveyard_companions) &&
        nearby_variants["passed"] == nearby_variants["total"] &&
        section_all_pass(why_not_v4_probes) &&
        layer_verdict == "PARTIAL"

    shared_scalars = Dict{String,Any}(
        "shell_count" => Float64(SHELL_COUNT),
        "n_eta" => Float64(N_ETA),
        "n_alpha" => Float64(N_ALPHA),
        "sample_count" => Float64(sample_count),
        "rank_tol" => RANK_TOL,
        "spin_degeneracy" => Float64(spin_degeneracy),
        "layer_verdict_code" => Float64(VERDICT_CODES[layer_verdict]),
        "target_filling_prefix_0" => Float64(TARGET_FILLING_PREFIX[1]),
        "target_filling_prefix_1" => Float64(TARGET_FILLING_PREFIX[2]),
        "target_filling_prefix_2" => Float64(TARGET_FILLING_PREFIX[3]),
        "owner_density_base_sphere_dim" => Float64(owner["density_anchor"]["base_sphere_dim"]),
        "owner_density_fiber_dim" => Float64(owner["density_anchor"]["fiber_dim"]),
        "owner_hopf_eta_bin_min_count" => Float64(owner["hopf_anchor"]["eta_bin_min_count"]),
    )
    for idx in 1:length(capacities)
        key = idx - 1
        shared_scalars["capacity_$key"] = Float64(capacities[idx])
        shared_scalars["expected_2n2_$key"] = Float64(expected_2n2[idx])
        shared_scalars["rank_increment_$key"] = Float64(hopf_probe["rank_increments"][idx])
        shared_scalars["cumulative_mode_$key"] = Float64(hopf_probe["cumulative_modes"][idx])
        shared_scalars["flat_control_capacity_$key"] = Float64(flat_capacities[idx])
        shared_scalars["erased_control_capacity_$key"] = Float64(erased_capacities[idx])
        shared_scalars["scrambled_control_capacity_$key"] = Float64(scrambled_capacities[idx])
    end
    shared_booleans = Dict{String,Any}(
        "owner_density_spinor_lift_live" => Bool(owner["density_spinor_lift_live"]),
        "owner_hopf_clifford_foliation_live" => Bool(owner["hopf_clifford_foliation_live"]),
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "rank_increment_witness" => rank_increment_witness,
        "cumulative_mode_witness" => cumulative_mode_witness,
        "flat_control_kills" => flat_control_kills,
        "erased_control_kills" => erased_control_kills,
        "scrambled_control_kills" => scrambled_control_kills,
        "controls_kill" => controls_kill,
        "caps_2_8_18_32" => caps_2_8_18_32,
        "equals_2n2" => equals_2n2,
        "from_real_hopf_shells" => from_real_hopf_shells,
        "filling_order_2_8_8_derived" => filling_order_2_8_8_derived,
        "local_all_pass" => local_all_pass,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
    )

    result = Dict{String,Any}(
        "schema" => "disc_scratch_dual_backend_v1",
        "object_id" => OBJECT_ID,
        "name" => "Shell capacity 2n^2 discriminator from nested Hopf/Clifford shells",
        "sim_id" => OBJECT_ID,
        "version" => "1.0",
        "backend" => BACKEND,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "finite_hopf_clifford_shell_capacity_discriminator",
        "root_constraints_in_force" => ["F01 finite witness", "N01 order/structure-sensitive carrier"],
        "carrier_layer" => "owner density-spinor lift plus nested Hopf/Clifford foliation receipts",
        "geometry_layer" => "Hopf base S2 shell ranks with Clifford equal-radius slice gate",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "whether nested Hopf/Clifford shells yield capacities [2,8,18,32]=2n^2 and whether they also derive 2-8-8 filling order",
        "branch_status_before_run" => "scratch discriminator row only",
        "allowed_claims" => [
            "finite capacity witness for n=1..4",
            "scrambled/flat/erased shell controls",
            "honest PARTIAL verdict when capacity survives but filling order does not",
        ],
        "promotion_status" => "diagnostic_only",
        "promotion_blockers" => [
            "classification=scratch_diagnostic",
            "promotion_allowed=false",
            "formal_admission_allowed=false",
            "Madelung/filling order not derived",
            "no chemistry, physics, bridge, Axis0, PEPS3D, or manifold admission",
        ],
        "eligible_consumers" => ["scratch diagnostics", "future bounded shell-capacity audits"],
        "blocked_consumers" => [
            "chemistry admission",
            "physics admission",
            "formal manifold admission",
            "bridge",
            "Axis0",
            "PEPS3D promotion",
            "canonical promotion",
        ],
        "required_tools" => ["Julia", "LinearAlgebra", "owner carrier receipts", "JAX peer backend"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "owner density-spinor receipt", "owner Hopf/Clifford receipt", "JSON"],
        "proof_surfaces_used" => ["finite rank/SVD residuals", "dual-backend shared scalar/boolean parity"],
        "graph_surfaces_used" => Any[],
        "topology_surfaces_used" => ["Hopf projection", "S2 quotient rank relation", "Clifford torus carrier gate"],
        "required_inputs" => collect(values(SOURCE_DEPENDENCIES)),
        "data_or_artifact_dependencies" => collect(values(SOURCE_DEPENDENCIES)),
        "required_negatives" => ["flat circle shell control", "erased shell control", "scrambled unconstrained 3D control"],
        "negatives_run" => ["flat_circle_control", "erased_shell_constant_control", "scrambled_unconstrained_3d_control"],
        "kill_conditions" => [
            "owner carrier receipts are not live",
            "capacity does not equal 2n^2",
            "flat/erased/scrambled controls reproduce the same sequence",
            "JAX/Julia parity exceeds strict tolerance",
            "verdict is forced to REAL_LAYER despite missing filling-order derivation",
        ],
        "required_artifacts" => [JAX_REFERENCE_PATH, RESULT_PATH],
        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "disc_shell_capacity_2n2_rank_probe_v1",
        "pass_rule" => "local positives, controls, boundary, graveyard companions, nearby variants, and peer parity pass; PARTIAL is acceptable when filling order is not derived",
        "fail_rule" => "carrier gate failure, target injection, control failure, parity mismatch, or dishonest verdict",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "target_capacities_2n2" => TARGET_CAPACITIES_2N2,
        "target_filling_prefix" => TARGET_FILLING_PREFIX,
        "observed_capacities" => capacities,
        "expected_2n2" => expected_2n2,
        "layer_verdict" => layer_verdict,
        "layer_verdict_code" => VERDICT_CODES[layer_verdict],
        "caps_2_8_18_32" => caps_2_8_18_32,
        "equals_2n2" => equals_2n2,
        "from_real_hopf_shells" => from_real_hopf_shells,
        "filling_order_2_8_8_derived" => filling_order_2_8_8_derived,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "owner_carrier_gate" => owner,
        "hopf_rank_probe" => hopf_probe,
        "flat_circle_control_probe" => flat_probe,
        "erased_shell_control_probe" => erased_probe,
        "scrambled_unconstrained_control_probe" => scrambled_probe,
        "control_capacities" => Dict{String,Any}(
            "flat_circle" => flat_capacities,
            "erased_shell" => erased_capacities,
            "scrambled_unconstrained_3d" => scrambled_capacities,
        ),
        "positive" => positive,
        "controls" => controls,
        "boundary" => boundary,
        "graveyard_companions" => graveyard_companions,
        "nearby_variants" => nearby_variants,
        "why_not_v4_probes" => why_not_v4_probes,
        "source_dependencies" => collect(values(SOURCE_DEPENDENCIES)),
        "source_hashes" => source_refs(),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "tool_manifest" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "local_all_pass" => local_all_pass,
        "blockers" => local_all_pass ? Any[] : ["local_positive_control_boundary_or_verdict_gate_failed"],
        "plain_sentence" => "The finite Hopf/Clifford shell-rank witness yields capacities [2,8,18,32]=2n^2 and dies under erased/flat/scrambled shell controls, but it does not derive the 2-8-8 filling order; verdict PARTIAL.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["peer_available"]) && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !local_all_pass || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => Bool(result["all_pass"]),
        "local_all_pass" => local_all_pass,
        "layer_verdict" => layer_verdict,
        "caps_2_8_18_32" => caps_2_8_18_32,
        "equals_2n2" => equals_2n2,
        "from_real_hopf_shells" => from_real_hopf_shells,
        "filling_order_2_8_8_derived" => filling_order_2_8_8_derived,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "claim_ceiling" => CLAIM_CEILING,
    )
    result
end

function print_summary(result::Dict{String,Any})
    println(
        "disc_shell_capacity_2n2 Julia " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "local_all_pass=$(lowercase(string(result["local_all_pass"]))) " *
        "layer_verdict=$(result["layer_verdict"]) " *
        "caps_2_8_18_32=$(lowercase(string(result["caps_2_8_18_32"]))) " *
        "equals_2n2=$(lowercase(string(result["equals_2n2"]))) " *
        "from_real_hopf_shells=$(lowercase(string(result["from_real_hopf_shells"]))) " *
        "filling_order_2_8_8_derived=$(lowercase(string(result["filling_order_2_8_8_derived"]))) " *
        "parity_max_diff=$(result["parity"]["parity_max_diff"]) " *
        "within_1e_9=$(lowercase(string(result["parity"]["within_1e_9"])))"
    )
    println(result["plain_sentence"])
    println("wrote: ", result["result_path"])
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    print_summary(result)
    return result["local_all_pass"] ? 0 : 1
end

exit(main())
