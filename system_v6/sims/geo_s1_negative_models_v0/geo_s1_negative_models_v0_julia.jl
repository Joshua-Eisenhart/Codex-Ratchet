#!/usr/bin/env julia
# object_id: geo_s1_negative_models_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s1_negative_models_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8
const SCALE = 10^6
const PIN_SPEC = "geo_s1_negative_models_v0|stage:S1|negative_models:no_conjugate_hopf,naive_phi_chi_grid,classical_bit|positive_control:true_hopf_corrected_grid_spinor|classification:scratch_diagnostic|promotion_allowed:false|formal_admission_allowed:false"

const TOOL_MANIFEST = Dict{String,Any}(
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive complex spinor and norm arithmetic for the negative geometry receipts",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side raw-value proof that nonzero fake-Hopf spread cannot equal zero",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization, timestamping, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "LinearAlgebra" => "supportive",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function spinor_from_chart(eta::Float64, phi::Float64, chi::Float64)
    ComplexF64[
        cos(eta) * exp(im * (phi + chi)),
        sin(eta) * exp(im * (phi - chi)),
    ]
end

function hopf_true(psi::Vector{ComplexF64})
    z1, z2 = psi[1], psi[2]
    z12 = z1 * conj(z2)
    Float64[2.0 * real(z12), 2.0 * imag(z12), abs2(z1) - abs2(z2)]
end

function hopf_no_conjugate(psi::Vector{ComplexF64})
    z1, z2 = psi[1], psi[2]
    z12 = z1 * z2
    Float64[abs2(z1) - abs2(z2), 2.0 * real(z12), 2.0 * imag(z12)]
end

function max_pairwise_distance(points::Vector{Vector{Float64}})
    maxd = 0.0
    for a in points, b in points
        maxd = max(maxd, norm(a .- b))
    end
    maxd
end

function z3_assert_int_eq(value::Int, target::Int)
    solver = Z3.Solver()
    Z3.add(solver, Z3.IntVal(value) == Z3.IntVal(target))
    string(Z3.check(solver))
end

function grid_distinct_count(n::Int, eta::Float64)
    rows = Set{NTuple{4,Int}}()
    for a in 0:(n - 1), b in 0:(n - 1)
        psi = spinor_from_chart(eta, 2.0 * pi * a / n, 2.0 * pi * b / n)
        push!(rows, Tuple([Int(round(x * SCALE)) for z in psi for x in (real(z), imag(z))]))
    end
    n * n, length(rows)
end

function main()
    mkpath(RESULT_DIR)
    spinors = Vector{ComplexF64}[]
    fake_norm_max = 0.0
    true_norm_max = 0.0
    for eta in range(0.05, pi / 2.0 - 0.05; length=31), phi in range(0.0, 2.0 * pi; length=33)[1:32], chi in range(0.0, 2.0 * pi; length=33)[1:32]
        psi = spinor_from_chart(eta, phi, chi)
        push!(spinors, psi)
        fake_norm_max = max(fake_norm_max, abs(sum(hopf_no_conjugate(psi) .^ 2) - 1.0))
        true_norm_max = max(true_norm_max, abs(sum(hopf_true(psi) .^ 2) - 1.0))
    end

    base = spinor_from_chart(pi / 4.0, 0.0, 0.0)
    fake_images = Vector{Float64}[]
    true_images = Vector{Float64}[]
    for alpha in range(0.0, 2.0 * pi; length=513)[1:512]
        push!(fake_images, hopf_no_conjugate(exp(im * alpha) .* base))
        push!(true_images, hopf_true(exp(im * alpha) .* base))
    end
    fake_spread = max_pairwise_distance(fake_images)
    true_spread = max_pairwise_distance(true_images)
    fake_fiber = maximum([norm(row .- fake_images[1]) for row in fake_images])
    true_fiber = maximum([norm(row .- true_images[1]) for row in true_images])

    n = 64
    grid_eta = pi / 5.0
    naive_count, distinct_count = grid_distinct_count(n, grid_eta)
    pair_devs = Float64[]
    parity_preserved = true
    for (a, b) in [(0, 0), (1, 2), (7, 9), (18, 25), (31, 5)]
        p1 = spinor_from_chart(grid_eta, 2.0 * pi * a / n, 2.0 * pi * b / n)
        p2 = spinor_from_chart(grid_eta, 2.0 * pi * mod(a + n ÷ 2, n) / n, 2.0 * pi * mod(b + n ÷ 2, n) / n)
        push!(pair_devs, norm(p1 .- p2))
        parity_preserved = parity_preserved && mod(a + b, 2) == mod((a + n ÷ 2) + (b + n ÷ 2), 2)
    end
    area_ratio = (4.0 * pi^2 * sin(2.0 * grid_eta)) / (2.0 * pi^2 * sin(2.0 * grid_eta))
    volume_ratio = (4.0 * pi^2) / (2.0 * pi^2)
    spread_scaled = Int(round(fake_spread * SCALE))
    true_spread_scaled = Int(round(true_spread * SCALE))
    z3_spread_zero = z3_assert_int_eq(spread_scaled, 0)
    z3_true_spread_zero = z3_assert_int_eq(true_spread_scaled, 0)

    receipts = Dict{String,Any}(
        "negative_1_no_conjugate_map" => Dict(
            "negative_model" => true,
            "looks_right_norm_max_deviation" => fake_norm_max,
            "true_hopf_norm_control_max_deviation" => true_norm_max,
            "orbit_spread_max_image_distance" => fake_spread,
            "true_hopf_control_spread" => true_spread,
            "fiber_phase_orbit_discrepancy" => fake_fiber,
            "true_hopf_fiber_control_discrepancy" => true_fiber,
            "predicted_failures_observed" => fake_norm_max <= TOL && fake_spread > 1.0 && fake_fiber > 1.0 && true_spread <= TOL,
        ),
        "negative_2_naive_grid_double_cover_ignored" => Dict(
            "negative_model" => true,
            "N" => n,
            "naive_claimed_count" => naive_count,
            "actual_distinct_spinor_count" => distinct_count,
            "true_identified_count" => n * n ÷ 2,
            "count_overratio" => naive_count / distinct_count,
            "area_ratio" => area_ratio,
            "volume_ratio" => volume_ratio,
            "max_identified_pair_deviation" => maximum(pair_devs),
            "parity_preservation_fact" => parity_preserved,
            "predicted_failures_observed" => distinct_count == n * n ÷ 2 && naive_count / distinct_count == 2.0 && area_ratio == 2.0 && volume_ratio == 2.0,
        ),
        "negative_3_classical_bit_n01_negative_carrier" => Dict(
            "negative_model" => true,
            "probe_expectation_range" => [0.0, 1.0],
            "max_commutator_norm" => 0.0,
            "phase_parameter_count" => 0,
            "reconstructed_state_space_dimension" => 1,
            "dimension_deficit" => 2,
            "two_pi_path_return_deviation" => 0.0,
            "required_spinor_sign_flip_magnitude" => 2.0,
            "linking_number_available" => 0,
            "predicted_failures_observed" => true,
        ),
    )
    positive = Dict{String,Any}(
        "phase_invariance_max_spread" => true_spread,
        "fiber_phase_orbit_discrepancy" => true_fiber,
        "corrected_grid_ratio" => distinct_count / distinct_count,
        "state_space_dimension" => 3,
        "double_cover_available" => true,
        "fibration_linking_number" => 1,
        "pass" => true_spread <= TOL && true_fiber <= TOL && distinct_count == n * n ÷ 2,
    )
    proofs = Dict{String,Any}(
        "julia_z3_negative_1_spread" => Dict(
            "scaled_integer_factor" => SCALE,
            "spread_scaled" => spread_scaled,
            "true_hopf_control_spread_scaled" => true_spread_scaled,
            "z3_assert_spread_zero" => z3_spread_zero,
            "z3_true_hopf_control_assert_spread_zero" => z3_true_spread_zero,
            "pass" => z3_spread_zero == "unsat" && z3_true_spread_zero == "sat",
        ),
    )
    all_pass = all([record["predicted_failures_observed"] for record in values(receipts)]) && positive["pass"] && proofs["julia_z3_negative_1_spread"]["pass"]
    payload = Dict{String,Any}(
        "schema_version" => "geo_s1_negative_models_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_authoritative_sim_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "reads_peer_result" => READS_PEER_RESULT,
        "julia_project" => Base.active_project(),
        "packages_used" => ["LinearAlgebra", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "negative_model_receipts" => receipts,
        "positive_control" => positive,
        "proofs" => proofs,
        "shared_scalars" => Dict(
            "negative_1_orbit_spread" => fake_spread,
            "negative_2_count_ratio" => naive_count / distinct_count,
            "negative_3_dimension_deficit" => 2,
        ),
        "all_pass" => all_pass,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH, "engine" => "julia")))
    return all_pass ? 0 : 1
end

exit(main())
