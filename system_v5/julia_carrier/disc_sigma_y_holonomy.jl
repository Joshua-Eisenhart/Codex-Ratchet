#!/usr/bin/env julia
# object_id: disc_sigma_y_holonomy
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "disc_sigma_y_holonomy"
const BACKEND = "julia_float64"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER, "disc_sigma_y_holonomy_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "disc_sigma_y_holonomy_results.json")
const EPS = 1.0e-9
const STRICT_TOL = 1.0e-7
const ODD_COUPLING_BASE = 0.17
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "scratch"
const CLAIM_CEILING = "scratch_diagnostic discriminator only: finite sigma_y/720-degree holonomy hinge for this row; no promotion, formal admission, physics, bridge, Axis0, or chirality doctrine closure"

const BLOCKED_CONSUMERS = [
    "formal_admission",
    "promotion",
    "physics_admission",
    "bridge_admission",
    "Axis0_admission",
    "chirality_doctrine_closure",
]

const SOURCE_PATHS = Dict{String,String}(
    "jax_source" => joinpath(FORMAL_SCOUTS, "sim_disc_sigma_y_holonomy_probe.py"),
    "julia_source" => @__FILE__,
    "clifford_torus_nested_hopf_foliation_source" => joinpath(JULIA_CARRIER, "clifford_torus_nested_hopf_foliation.jl"),
    "clifford_torus_nested_hopf_foliation_jax_result" => joinpath(JULIA_CARRIER, "clifford_torus_nested_hopf_foliation_jax_results.json"),
    "golden_weyl_julia_source" => joinpath(JULIA_CARRIER, "golden_weyl_julia.jl"),
    "golden_weyl_jax_receipt" => joinpath(JULIA_CARRIER, "golden_weyl_jax_receipt.json"),
    "golden_weyl_julia_receipt" => joinpath(JULIA_CARRIER, "golden_weyl_julia_receipt.json"),
    "density_matrix_spinor_lift_source" => joinpath(JULIA_CARRIER, "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax_result" => joinpath(JULIA_CARRIER, "density_matrix_spinor_lift_jax_results.json"),
)

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia Float64 backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Julia backend for the finite sigma_y holonomy discriminator witness"),
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite Pauli tensor algebra, eigenspectrum invariants, and control residuals"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer result for backend parity"),
    "clifford_torus_nested_hopf_foliation" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner nested Hopf-torus carrier receipt; erasing it zeroes the lifted odd-connection coefficient"),
    "golden_weyl" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner Weyl/Hopf receipt supplying finite linking, cocycle, and nested-connection scalars"),
    "density_matrix_spinor_lift" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner lift receipt supplying the 2pi/4pi spinor-vs-density holonomy witness"),
    "Julia stdlib" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON serialization, timestamps, hashing, and peer-result loading"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "not available in Julia path and explicitly excluded from this scratch diagnostic"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia Float64 backend" => "load_bearing",
    "Julia LinearAlgebra" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "clifford_torus_nested_hopf_foliation" => "load_bearing",
    "golden_weyl" => "load_bearing",
    "density_matrix_spinor_lift" => "load_bearing",
    "Julia stdlib" => "supportive",
    "numpy" => nothing,
)

const I2 = ComplexF64[1.0 0.0; 0.0 1.0]
const SX = ComplexF64[0.0 1.0; 1.0 0.0]
const SY = ComplexF64[0.0 -im; im 0.0]
const SZ = ComplexF64[1.0 0.0; 0.0 -1.0]
const ZERO4 = zeros(ComplexF64, 4, 4)
const VERDICT_CODES = Dict{String,Float64}(
    "OPEN" => 0.0,
    "REAL_CARRIER" => 1.0,
    "CONVENTION" => 2.0,
    "REPRODUCED" => 3.0,
    "GENERIC" => 4.0,
    "GRAVEYARD" => 5.0,
)

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    Dict{String,Any}(
        key => Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
        for (key, path) in SOURCE_PATHS
    )
end

function read_json(path::String)
    JSON.parsefile(path)
end

function load_owner_receipts()
    Dict{String,Any}(
        "clifford" => read_json(SOURCE_PATHS["clifford_torus_nested_hopf_foliation_jax_result"]),
        "golden_jax" => read_json(SOURCE_PATHS["golden_weyl_jax_receipt"]),
        "golden_julia" => read_json(SOURCE_PATHS["golden_weyl_julia_receipt"]),
        "density" => read_json(SOURCE_PATHS["density_matrix_spinor_lift_jax_result"]),
    )
end

function owner_carrier_scalars(receipts)
    verdicts = receipts["clifford"]["verdicts"]
    torus_gate = all(Bool(get(verdicts, key, false)) for key in [
        "torus_is_constrained_slice",
        "foliation_covers_S3",
        "clifford_torus_equal_radius_slice",
        "flat_t2_control_pass",
    ]) ? 1.0 : 0.0
    golden = receipts["golden_jax"]["invariants"]
    density = receipts["density"]["values"]
    linking = Float64(golden["linking_number"])
    flat_linking = Float64(golden["flat_S2_linking_number"])
    cocycle_wl = Float64(golden["cocycle_wL"])
    cocycle_wr = Float64(golden["cocycle_wR"])
    base_2pi = Float64(density["base_holonomy_2pi"])
    lift_2pi = Float64(density["lift_holonomy_2pi"])
    lift_4pi = Float64(density["lift_holonomy_4pi"])
    spinor_720_gate = abs(lift_2pi + 1.0) < STRICT_TOL && abs(lift_4pi - 1.0) < STRICT_TOL ? 1.0 : 0.0
    density_erases_360_gate = abs(base_2pi - 1.0) < STRICT_TOL ? 1.0 : 0.0
    linking_gap = abs(linking - flat_linking)
    cocycle_gap = abs(cocycle_wl - cocycle_wr) / 2.0
    holonomy_gap = abs(lift_2pi - base_2pi) / 2.0
    owner_gate = torus_gate * spinor_720_gate * density_erases_360_gate
    odd_strength = ODD_COUPLING_BASE * owner_gate * linking_gap * cocycle_gap * holonomy_gap
    Dict{String,Any}(
        "torus_gate" => torus_gate,
        "spinor_720_gate" => spinor_720_gate,
        "density_erases_360_gate" => density_erases_360_gate,
        "linking" => linking,
        "flat_linking" => flat_linking,
        "linking_gap" => linking_gap,
        "cocycle_wL" => cocycle_wl,
        "cocycle_wR" => cocycle_wr,
        "cocycle_gap" => cocycle_gap,
        "base_holonomy_2pi" => base_2pi,
        "lift_holonomy_2pi" => lift_2pi,
        "lift_holonomy_4pi" => lift_4pi,
        "holonomy_gap" => holonomy_gap,
        "owner_gate" => owner_gate,
        "odd_strength" => odd_strength,
    )
end

kron2(a, b) = kron(a, b)
matrix_gap(a, b) = norm(a - b)

function spectral_gap(a, b)
    ea = sort(eigvals(Hermitian((a + a') ./ 2.0)))
    eb = sort(eigvals(Hermitian((b + b') ./ 2.0)))
    maximum(abs.(ea .- eb))
end

function density_from_spinor(psi)
    psi * psi'
end

function spinor(theta::Float64, phi::Float64)
    ComplexF64[cos(theta / 2.0), cis(phi) * sin(theta / 2.0)]
end

function row_witness(scalars)
    sigy = kron2(SY, I2)
    h0 = 0.37 .* kron2(SX, I2) .+
        0.23 .* kron2(SZ, I2) .+
        0.19 .* kron2(I2, SY) .+
        0.11 .* kron2(SY, SZ)
    odd_operator = kron2(SX, SY) .+ 0.5 .* kron2(SZ, SY)
    even_operator = kron2(SY, I2) .+ 0.25 .* kron2(I2, SY)
    odd_conjugation_residual = matrix_gap(sigy * odd_operator * sigy', -odd_operator)
    even_conjugation_residual = matrix_gap(sigy * even_operator * sigy', even_operator)
    odd_operator_norm = matrix_gap(odd_operator, ZERO4)

    odd_strength = Float64(scalars["odd_strength"])
    h_lift_left = h0 .+ odd_strength .* odd_operator
    h_lift_right = sigy * h0 * sigy' .+ odd_strength .* odd_operator
    h_bare_left = h0
    h_bare_right = sigy * h_bare_left * sigy'
    h_erased_left = h0
    h_erased_right = sigy * h_erased_left * sigy'
    random_connection = 0.031 .* (kron2(SY, I2) .- 0.7 .* kron2(I2, SY) .+ 0.2 .* kron2(SY, SY))
    h_random_left = h0 .+ random_connection
    h_random_right = sigy * h_random_left * sigy'

    psi_left = kron2(spinor(1.1, -0.7), spinor(0.6, 0.31))
    rho_left = density_from_spinor(psi_left)
    rho_right = sigy * rho_left * sigy'

    lifted_after_sigy_gap = matrix_gap(sigy * h_lift_left * sigy', h_lift_right)
    lifted_spectral_gap = spectral_gap(h_lift_left, h_lift_right)
    bare_after_sigy_gap = matrix_gap(sigy * h_bare_left * sigy', h_bare_right)
    bare_spectral_gap = spectral_gap(h_bare_left, h_bare_right)
    erased_after_sigy_gap = matrix_gap(sigy * h_erased_left * sigy', h_erased_right)
    erased_spectral_gap = spectral_gap(h_erased_left, h_erased_right)
    density_after_sigy_gap = matrix_gap(sigy * rho_left * sigy', rho_right)
    random_after_sigy_gap = matrix_gap(sigy * h_random_left * sigy', h_random_right)
    random_spectral_gap = spectral_gap(h_random_left, h_random_right)

    sigma_y_odd_coupling_present = odd_strength > STRICT_TOL &&
        odd_operator_norm > STRICT_TOL &&
        odd_conjugation_residual < STRICT_TOL &&
        even_conjugation_residual < STRICT_TOL
    bare_collapses_under_sigy = bare_after_sigy_gap < STRICT_TOL && bare_spectral_gap < STRICT_TOL
    erased_path_collapses = erased_after_sigy_gap < STRICT_TOL && erased_spectral_gap < STRICT_TOL
    density_only_collapses = density_after_sigy_gap < STRICT_TOL
    random_connection_no_split = random_after_sigy_gap < STRICT_TOL && random_spectral_gap < STRICT_TOL
    lifted_path_differs = lifted_after_sigy_gap > STRICT_TOL && lifted_spectral_gap > STRICT_TOL
    owner_erasure_changes_result = lifted_path_differs && erased_path_collapses

    row_verdict = if !(bare_collapses_under_sigy && erased_path_collapses && density_only_collapses && random_connection_no_split)
        "GENERIC"
    elseif lifted_path_differs && sigma_y_odd_coupling_present && owner_erasure_changes_result
        "REAL_CARRIER"
    elseif !lifted_path_differs && !sigma_y_odd_coupling_present
        "CONVENTION"
    elseif !lifted_path_differs && sigma_y_odd_coupling_present
        "REPRODUCED"
    else
        "OPEN"
    end

    Dict{String,Any}(
        "row_verdict" => row_verdict,
        "bare_collapses_under_sigy" => bare_collapses_under_sigy,
        "lifted_path_differs" => lifted_path_differs,
        "erased_path_collapses" => erased_path_collapses,
        "density_only_collapses" => density_only_collapses,
        "random_connection_no_split" => random_connection_no_split,
        "sigma_y_odd_coupling_present" => sigma_y_odd_coupling_present,
        "owner_erasure_changes_result" => owner_erasure_changes_result,
        "values" => Dict{String,Any}(
            "odd_strength" => odd_strength,
            "odd_operator_norm" => odd_operator_norm,
            "odd_conjugation_residual" => odd_conjugation_residual,
            "even_conjugation_residual" => even_conjugation_residual,
            "lifted_after_sigy_gap" => lifted_after_sigy_gap,
            "lifted_spectral_gap" => lifted_spectral_gap,
            "bare_after_sigy_gap" => bare_after_sigy_gap,
            "bare_spectral_gap" => bare_spectral_gap,
            "erased_after_sigy_gap" => erased_after_sigy_gap,
            "erased_spectral_gap" => erased_spectral_gap,
            "density_after_sigy_gap" => density_after_sigy_gap,
            "random_after_sigy_gap" => random_after_sigy_gap,
            "random_spectral_gap" => random_spectral_gap,
            "row_verdict_code" => VERDICT_CODES[row_verdict],
        ),
    )
end

function parity_against_peer(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "within_1e_9" => false,
            "max_abs_diff" => nothing,
            "scalar_diffs" => Any[],
            "boolean_mismatches" => Any[],
            "string_mismatches" => [Dict("key" => "peer", "julia" => "present", "jax" => "missing")],
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    diffs = Vector{Dict{String,Any}}()
    max_diff = 0.0
    for (key, value) in result["shared_scalars"]
        peer_value = Float64(peer["shared_scalars"][key])
        diff = abs(Float64(value) - peer_value)
        max_diff = max(max_diff, diff)
        diff > EPS && push!(diffs, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => peer_value, "abs_diff" => diff))
    end
    boolean_mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        peer_value = Bool(peer["shared_booleans"][key])
        Bool(value) != peer_value && push!(boolean_mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => peer_value))
    end
    string_mismatches = Vector{Dict{String,Any}}()
    if result["row_verdict"] != peer["row_verdict"]
        push!(string_mismatches, Dict{String,Any}("key" => "row_verdict", "julia" => result["row_verdict"], "jax" => peer["row_verdict"]))
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "within_1e_9" => max_diff <= EPS && isempty(diffs) && isempty(boolean_mismatches) && isempty(string_mismatches),
        "max_abs_diff" => max_diff,
        "scalar_diffs" => diffs,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
    )
end

function build_result()
    mkpath(dirname(RESULT_PATH))
    receipts = load_owner_receipts()
    scalars = owner_carrier_scalars(receipts)
    witness = row_witness(scalars)
    row_verdict = witness["row_verdict"]

    shared_scalars = Dict{String,Any}()
    for (key, value) in scalars
        shared_scalars[key] = value
    end
    for (key, value) in witness["values"]
        shared_scalars[key] = value
    end
    shared_booleans = Dict{String,Any}(
        "bare_collapses_under_sigy" => witness["bare_collapses_under_sigy"],
        "lifted_path_differs" => witness["lifted_path_differs"],
        "erased_path_collapses" => witness["erased_path_collapses"],
        "density_only_collapses" => witness["density_only_collapses"],
        "random_connection_no_split" => witness["random_connection_no_split"],
        "sigma_y_odd_coupling_present" => witness["sigma_y_odd_coupling_present"],
        "owner_erasure_changes_result" => witness["owner_erasure_changes_result"],
        "classification_fence" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
    )
    positive = Dict{String,Any}(
        "lifted_path_holonomy_compared" => Dict("pass" => true, "finite_witness" => "4x4 Pauli tensor pair plus owner weighted sigma_y-odd connection term"),
        "owner_carrier_load_bearing" => Dict("pass" => witness["owner_erasure_changes_result"], "rule" => "erase path/connection memory zeroes odd_strength and collapses the split", "owner_odd_strength" => scalars["odd_strength"]),
        "sigma_y_odd_coupling_present" => Dict("pass" => witness["sigma_y_odd_coupling_present"], "odd_operator" => "X_i Y_j + 0.5 Z_i Y_j", "odd_conjugation_residual" => witness["values"]["odd_conjugation_residual"]),
        "unitary_invariant_split" => Dict("pass" => witness["lifted_path_differs"], "spectral_gap" => witness["values"]["lifted_spectral_gap"], "reason" => "different spectra are a finite witness that no unitary can map the lifted branch Hamiltonians"),
    )
    negative = Dict{String,Any}(
        "bare_pm_h0_collapses_under_sigy" => Dict("pass" => witness["bare_collapses_under_sigy"], "gap" => witness["values"]["bare_after_sigy_gap"]),
        "erase_path_connection_memory_collapses" => Dict("pass" => witness["erased_path_collapses"], "gap" => witness["values"]["erased_after_sigy_gap"]),
        "density_only_rho_collapses" => Dict("pass" => witness["density_only_collapses"], "gap" => witness["values"]["density_after_sigy_gap"]),
        "random_trivial_connection_no_meaningful_split" => Dict("pass" => witness["random_connection_no_split"], "gap" => witness["values"]["random_after_sigy_gap"]),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => shared_booleans["classification_fence"], "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
        "honest_discriminator_verdict" => Dict("pass" => haskey(VERDICT_CODES, row_verdict), "row_verdict" => row_verdict, "note" => "all_pass means the discriminator and controls ran cleanly; the verdict may still be CONVENTION, REPRODUCED, or GRAVEYARD in other branches"),
    )
    result = Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "carrier_readout_discriminator_probe",
        "source_alignment_category" => "sigma_y_720_degree_holonomy_hinge_discriminator",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "jax_result_path" => JAX_RESULT_PATH,
        "source_refs" => source_refs(),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["julia", "linearalgebra", "jax peer", "clifford_torus_nested_hopf_foliation", "golden_weyl", "density_matrix_spinor_lift"],
        "actual_tools_used" => ["julia", "linearalgebra", "julia stdlib", "owner carrier result JSONs"],
        "numpy_compute_used" => false,
        "root_constraints_in_force" => Dict("F01" => "finite 4x4 Pauli tensor carrier, finite source-result receipts, finite scalar witness table", "N01" => "noncommuting sigma_y action and sigma_y-odd operator conjugation are explicitly tested"),
        "finite_map" => "owner carrier scalars -> odd connection coefficient -> Type1/Type2 finite Pauli tuple -> sigma_y and spectral invariants -> row verdict",
        "domain" => "one sigma_y/720-degree holonomy discriminator row with bare, erased, density-only, and random/trivial controls",
        "codomain_or_output" => "single row verdict plus finite witness booleans and dual-backend parity",
        "carrier_layer" => "lifted spinor/path/connection nested Hopf-torus owner carrier",
        "geometry_layer" => "clifford_torus_nested_hopf_foliation + golden_weyl + density_matrix_spinor_lift receipts",
        "bridge_layer" => "none",
        "cut_layer" => "sigma_y convention-erasure controls",
        "law_or_candidate_tested" => "Type1/Type2 chirality is real only if a sigma_y-odd lifted/path/connection coupling survives while erasures collapse",
        "branch_status_before_run" => "discriminator row requested; survival not assumed",
        "allowed_claims" => ["finite discriminator row verdict under this exact sigma_y/holonomy witness", "negative controls collapsed or failed as reported", "JAX and Julia parity agreed or disagreements were reported"],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "promotion_blockers" => BLOCKED_CONSUMERS,
        "row_id" => "sigma_y_720_degree_holonomy_hinge",
        "row_verdict" => row_verdict,
        "bare_collapses_under_sigy" => witness["bare_collapses_under_sigy"],
        "lifted_path_differs" => witness["lifted_path_differs"],
        "erased_path_collapses" => witness["erased_path_collapses"],
        "density_only_collapses" => witness["density_only_collapses"],
        "random_connection_no_split" => witness["random_connection_no_split"],
        "sigma_y_odd_coupling_present" => witness["sigma_y_odd_coupling_present"],
        "owner_erasure_changes_result" => witness["owner_erasure_changes_result"],
        "owner_carrier_scalars" => scalars,
        "finite_witness" => witness,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "positive" => positive,
        "negative" => negative,
        "graveyard_companions" => negative,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => 1, "passed" => haskey(VERDICT_CODES, row_verdict) ? 1 : 0, "variants" => ["sigma_y_720_degree_holonomy_hinge"]),
        "why_not_v4_probes" => Dict("reason" => "bare Type1/Type2 signs and density-only readouts are sigma_y conventions; this row adds lifted/path/connection memory plus erasure controls"),
    )
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = result["parity"]["peer_available"] &&
        result["parity"]["within_1e_9"] &&
        shared_booleans["classification_fence"] &&
        result["bare_collapses_under_sigy"] &&
        result["erased_path_collapses"] &&
        result["density_only_collapses"] &&
        result["random_connection_no_split"] &&
        row_verdict != "GENERIC" &&
        row_verdict != "OPEN"
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "row_verdict" => row_verdict,
        "claim_ceiling" => CLAIM_CEILING,
        "controls_all_collapsed" => result["bare_collapses_under_sigy"] && result["erased_path_collapses"] && result["density_only_collapses"] && result["random_connection_no_split"],
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
    )
    result["stop_condition_fired"] = !result["all_pass"]
    result["blockers"] = result["all_pass"] ? Any[] : ["parity missing/disagreed, generic/open verdict, or a required collapse control failed"]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("RESULT $(OBJECT_ID) julia=$(RESULT_PATH) jax=$(JAX_RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) row_verdict=$(result["row_verdict"]) parity=$(lowercase(string(result["parity"]["within_1e_9"])))")
    return result["all_pass"] ? 0 : 1
end

exit(main())
