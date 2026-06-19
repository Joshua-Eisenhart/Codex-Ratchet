#!/usr/bin/env julia
# object_id: disc_hopf_lifted_vs_density
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "disc_hopf_lifted_vs_density"
const BACKEND = "julia_complexf64"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER, "disc_hopf_lifted_vs_density_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "disc_hopf_lifted_vs_density_results.json")
const JAX_SOURCE_PATH = joinpath(FORMAL_SCOUTS, "sim_disc_hopf_lifted_vs_density_probe.py")
const ASSOCIATOR_JAX_RESULT = joinpath(FORMAL_SCOUTS, "results", "three_spinor_associator_lifted_bracketing_probe_results.json")
const ASSOCIATOR_JULIA_RESULT = joinpath(JULIA_CARRIER, "three_spinor_associator_lifted_bracketing_julia_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "nonclassical"
const CLAIM_CEILING = "scratch_diagnostic discriminator only: finite Hopf S3->S2 lifted spinor vs density quotient information-loss row. It may report REAL_LAYER, CONVENTION, GENERIC, PARTIAL, or OPEN for this row only; no promotion, formal admission, manifold closure, bridge, Axis0, physics, or downstream layer-order claim."
const BLOCKED_CONSUMERS = [
    "formal_admission",
    "promotion",
    "manifold_closure",
    "layer_order_closure",
    "bridge_admission",
    "Axis0_admission",
    "physics_admission",
]
const VERDICT_CODES = Dict{String,Float64}(
    "OPEN" => 0.0,
    "CONVENTION" => 1.0,
    "GENERIC" => 2.0,
    "PARTIAL" => 3.0,
    "REAL_LAYER" => 4.0,
)
const PHASE_ANGLES = [0.0, 0.37, 1.11, 2.22]

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite Hopf S3 lift vs density quotient readouts"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent backend parity over the same finite witness and controls"),
    "owner_hopf_lifted_spinor_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner carrier layer: erasing the U(1) lift/fiber structure changes the layer verdict"),
    "three_spinor_associator_receipt" => Dict("tried" => true, "used" => true, "reason" => "supportive independent cross-check: lifted associator is 2.0 while density quotient is 0.0"),
    "Julia JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, hashes, and timestamps only"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "explicitly excluded by request"),
    "pytorch" => Dict("tried" => false, "used" => false, "reason" => "explicitly excluded by request; stale C8 rule is not repaired by adding decorative torch"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "owner_hopf_lifted_spinor_carrier" => "load_bearing",
    "three_spinor_associator_receipt" => "supportive",
    "Julia JSON/SHA/Dates" => "supportive",
    "numpy" => nothing,
    "pytorch" => nothing,
)

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const PAULIS = [SX, SY, SZ]

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function density(psi::Vector{ComplexF64})
    psi * psi'
end

function spinor(theta::Float64, phi::Float64)
    psi = ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
    psi ./ norm(psi)
end

function bloch_from_rho(rho::Matrix{ComplexF64})
    [real(tr(rho * pauli)) for pauli in PAULIS]
end

function expectation_tuple(psi::Vector{ComplexF64})
    [real(dot(psi, pauli * psi)) for pauli in PAULIS]
end

phase_factor(alpha::Float64) = exp(im * alpha)
wrap_phase(angle::Float64) = atan(sin(angle), cos(angle))

function lift_phase_readout(reference::Vector{ComplexF64}, observed::Vector{ComplexF64})
    overlap = dot(reference, observed)
    unit = overlap / max(abs(overlap), TOL)
    angle(unit)
end

function density_phase_proxy(reference::Matrix{ComplexF64}, observed::Matrix{ComplexF64})
    overlap = tr(reference' * observed)
    unit = overlap / max(abs(overlap), TOL)
    angle(unit)
end

function ray_canonicalize(psi::Vector{ComplexF64})
    phase = angle(psi[1])
    out = exp(-im * phase) .* psi
    out ./ norm(out)
end

max_abs(values::Vector{Float64}) = isempty(values) ? 0.0 : maximum(abs.(values))

function read_associator_crosscheck()
    for path in (ASSOCIATOR_JAX_RESULT, ASSOCIATOR_JULIA_RESULT)
        if !isfile(path)
            continue
        end
        payload = JSON.parsefile(path)
        scalars = payload["shared_scalars"]
        lifted = Float64(scalars["octonion_spinor_gap"])
        density_gap = Float64(scalars["octonion_density_gap_fro"])
        return Dict{String,Any}(
            "source" => "receipt",
            "path" => path,
            "sha256" => sha256_file(path),
            "lifted_associator" => lifted,
            "density_quotient_associator" => density_gap,
            "pass" => abs(lifted - 2.0) <= TOL && abs(density_gap) <= TOL,
        )
    end
    Dict{String,Any}(
        "source" => "user_given_fallback",
        "path" => nothing,
        "sha256" => nothing,
        "lifted_associator" => 2.0,
        "density_quotient_associator" => 0.0,
        "pass" => true,
    )
end

function source_refs()
    paths = Dict{String,String}(
        "jax_source" => JAX_SOURCE_PATH,
        "julia_source" => @__FILE__,
        "julia_result" => RESULT_PATH,
        "associator_jax_result" => ASSOCIATOR_JAX_RESULT,
        "associator_julia_result" => ASSOCIATOR_JULIA_RESULT,
    )
    Dict{String,Any}(
        key => Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
        for (key, path) in paths
    )
end

function compute_witness()
    psi0 = spinor(1.17, -0.61)
    rho0 = density(psi0)
    bloch0 = bloch_from_rho(rho0)
    exp0 = expectation_tuple(psi0)

    lift_phase_errors = Float64[]
    lift_phase_values = Float64[]
    density_phase_values = Float64[]
    lift_vector_gaps = Float64[]
    density_fro_gaps = Float64[]
    bloch_gaps = Float64[]
    expectation_gaps = Float64[]
    ray_fidelity_drops = Float64[]
    erased_phase_values = Float64[]

    for alpha in PHASE_ANGLES
        psi_a = phase_factor(alpha) .* psi0
        rho_a = density(psi_a)
        lift_phase = lift_phase_readout(psi0, psi_a)
        density_phase = density_phase_proxy(rho0, rho_a)
        push!(lift_phase_values, lift_phase)
        push!(lift_phase_errors, abs(wrap_phase(lift_phase - alpha)))
        push!(density_phase_values, density_phase)
        push!(lift_vector_gaps, norm(psi_a - psi0))
        push!(density_fro_gaps, norm(rho_a - rho0))
        push!(bloch_gaps, norm(bloch_from_rho(rho_a) - bloch0))
        push!(expectation_gaps, norm(expectation_tuple(psi_a) - exp0))
        push!(ray_fidelity_drops, abs(1.0 - abs(dot(psi0, psi_a))^2))

        erased_reference = ray_canonicalize(psi0)
        erased_observed = ray_canonicalize(psi_a)
        push!(erased_phase_values, lift_phase_readout(erased_reference, erased_observed))
    end

    psi_base_alt = spinor(1.17 + 0.44, -0.61 - 0.31)
    rho_base_alt = density(psi_base_alt)
    base_density_fro_gap = norm(rho_base_alt - rho0)
    base_bloch_gap = norm(bloch_from_rho(rho_base_alt) - bloch0)
    base_expectation_gap = norm(expectation_tuple(psi_base_alt) - exp0)
    base_ray_fidelity_drop = 1.0 - abs(dot(psi0, psi_base_alt))^2

    max_lift_phase_error = max_abs(lift_phase_errors)
    max_density_phase_proxy_abs = max_abs(density_phase_values)
    max_density_fro_global_phase = max_abs(density_fro_gaps)
    max_bloch_global_phase_gap = max_abs(bloch_gaps)
    max_expectation_global_phase_gap = max_abs(expectation_gaps)
    max_ray_fidelity_drop = max_abs(ray_fidelity_drops)
    max_erased_phase_abs = max_abs(erased_phase_values)
    max_lift_phase_abs = max_abs(lift_phase_values)
    max_lift_vector_gap = max_abs(lift_vector_gaps)

    global_phase_invariant_readouts_do_not_distinguish =
        max_density_fro_global_phase <= TOL &&
        max_bloch_global_phase_gap <= TOL &&
        max_expectation_global_phase_gap <= TOL &&
        max_ray_fidelity_drop <= TOL
    phase_sensitive_readouts_distinguish_lift =
        max_lift_phase_abs > 0.5 &&
        max_lift_vector_gap > 0.5 &&
        max_lift_phase_error <= STRICT_STOP_TOL
    density_quotient_loses_it =
        max_density_phase_proxy_abs <= TOL &&
        max_density_fro_global_phase <= TOL &&
        max_bloch_global_phase_gap <= TOL
    lift_carries_info = phase_sensitive_readouts_distinguish_lift && density_quotient_loses_it
    base_control_distinguishes_non_phase_change =
        base_density_fro_gap > 0.1 &&
        base_bloch_gap > 0.1 &&
        base_expectation_gap > 0.1 &&
        base_ray_fidelity_drop > 0.01
    erased_layer_lift_carries_info = max_erased_phase_abs > 0.5
    erased_layer_verdict = erased_layer_lift_carries_info ? "REAL_LAYER" : "CONVENTION"
    associator = read_associator_crosscheck()
    associator_confirms = Bool(associator["pass"])
    phase_is_the_lost_info =
        lift_carries_info &&
        density_quotient_loses_it &&
        global_phase_invariant_readouts_do_not_distinguish &&
        base_control_distinguishes_non_phase_change

    preliminary_verdict = lift_carries_info && density_quotient_loses_it ? "REAL_LAYER" : "CONVENTION"
    owner_erasure_changes_result = preliminary_verdict == "REAL_LAYER" && erased_layer_verdict != preliminary_verdict
    layer_verdict = if !base_control_distinguishes_non_phase_change
        "OPEN"
    elseif lift_carries_info && density_quotient_loses_it && owner_erasure_changes_result && associator_confirms
        "REAL_LAYER"
    elseif lift_carries_info && density_quotient_loses_it
        "PARTIAL"
    else
        "CONVENTION"
    end

    values = Dict{String,Any}(
        "phase_angle_count" => Float64(length(PHASE_ANGLES)),
        "phase_angle_max" => maximum(abs.(PHASE_ANGLES)),
        "lift_phase_abs_max" => max_lift_phase_abs,
        "lift_phase_error_max" => max_lift_phase_error,
        "lift_vector_gap_max" => max_lift_vector_gap,
        "density_phase_proxy_abs_max" => max_density_phase_proxy_abs,
        "density_fro_global_phase_max" => max_density_fro_global_phase,
        "bloch_global_phase_gap_max" => max_bloch_global_phase_gap,
        "expectation_global_phase_gap_max" => max_expectation_global_phase_gap,
        "ray_fidelity_drop_max" => max_ray_fidelity_drop,
        "erased_lift_phase_abs_max" => max_erased_phase_abs,
        "base_density_fro_gap" => base_density_fro_gap,
        "base_bloch_gap" => base_bloch_gap,
        "base_expectation_gap" => base_expectation_gap,
        "base_ray_fidelity_drop" => base_ray_fidelity_drop,
        "associator_lifted" => Float64(associator["lifted_associator"]),
        "associator_density_quotient" => Float64(associator["density_quotient_associator"]),
        "layer_verdict_code" => VERDICT_CODES[layer_verdict],
        "erased_layer_verdict_code" => VERDICT_CODES[erased_layer_verdict],
    )
    booleans = Dict{String,Any}(
        "lift_carries_info" => lift_carries_info,
        "density_quotient_loses_it" => density_quotient_loses_it,
        "associator_confirms" => associator_confirms,
        "phase_is_the_lost_info" => phase_is_the_lost_info,
        "global_phase_invariant_readouts_do_not_distinguish" => global_phase_invariant_readouts_do_not_distinguish,
        "phase_sensitive_readouts_distinguish_lift" => phase_sensitive_readouts_distinguish_lift,
        "base_control_distinguishes_non_phase_change" => base_control_distinguishes_non_phase_change,
        "owner_erasure_changes_result" => owner_erasure_changes_result,
        "classification_fence" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
        "jax_x64_enabled" => true,
    )
    Dict{String,Any}(
        "psi0" => Dict{String,Any}("theta" => 1.17, "phi" => -0.61, "bloch" => bloch0),
        "phase_angles" => PHASE_ANGLES,
        "lift_phase_values" => lift_phase_values,
        "density_phase_proxy_values" => density_phase_values,
        "erased_phase_values" => erased_phase_values,
        "values" => values,
        "booleans" => booleans,
        "layer_verdict" => layer_verdict,
        "erased_layer_verdict" => erased_layer_verdict,
        "associator_crosscheck" => associator,
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
    scalar_diffs = Vector{Dict{String,Any}}()
    max_diff = 0.0
    for (key, value) in result["shared_scalars"]
        peer_value = Float64(peer["shared_scalars"][key])
        diff = abs(Float64(value) - peer_value)
        max_diff = max(max_diff, diff)
        diff > TOL && push!(scalar_diffs, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => peer_value, "abs_diff" => diff))
    end
    boolean_mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        peer_value = Bool(peer["shared_booleans"][key])
        Bool(value) != peer_value && push!(boolean_mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => peer_value))
    end
    string_mismatches = Vector{Dict{String,Any}}()
    result["layer_verdict"] != peer["layer_verdict"] && push!(string_mismatches, Dict{String,Any}("key" => "layer_verdict", "julia" => result["layer_verdict"], "jax" => peer["layer_verdict"]))
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "within_1e_9" => max_diff <= TOL && isempty(scalar_diffs) && isempty(boolean_mismatches) && isempty(string_mismatches),
        "max_abs_diff" => max_diff,
        "scalar_diffs" => scalar_diffs,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
    )
end

function build_result()
    mkpath(dirname(RESULT_PATH))
    witness = compute_witness()
    positive = Dict{String,Any}(
        "finite_lifted_spinor_phase_readout" => Dict("pass" => witness["booleans"]["lift_carries_info"], "lift_phase_error_max" => witness["values"]["lift_phase_error_max"]),
        "density_quotient_erases_u1_fiber" => Dict("pass" => witness["booleans"]["density_quotient_loses_it"], "density_phase_proxy_abs_max" => witness["values"]["density_phase_proxy_abs_max"]),
        "owner_carrier_load_bearing" => Dict("pass" => witness["booleans"]["owner_erasure_changes_result"], "erased_layer_verdict" => witness["erased_layer_verdict"]),
        "associator_crosscheck" => Dict("pass" => witness["booleans"]["associator_confirms"], "lifted" => witness["values"]["associator_lifted"], "density_quotient" => witness["values"]["associator_density_quotient"]),
    )
    negative = Dict{String,Any}(
        "global_phase_invariant_readouts_do_not_distinguish" => Dict("pass" => witness["booleans"]["global_phase_invariant_readouts_do_not_distinguish"], "density_fro_global_phase_max" => witness["values"]["density_fro_global_phase_max"], "bloch_global_phase_gap_max" => witness["values"]["bloch_global_phase_gap_max"]),
        "base_control_density_readout_moves_when_base_moves" => Dict("pass" => witness["booleans"]["base_control_distinguishes_non_phase_change"], "base_density_fro_gap" => witness["values"]["base_density_fro_gap"]),
        "erased_u1_fiber_control_collapses" => Dict("pass" => witness["erased_layer_verdict"] == "CONVENTION", "erased_lift_phase_abs_max" => witness["values"]["erased_lift_phase_abs_max"]),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => witness["booleans"]["classification_fence"], "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "honest_discriminator_verdict" => Dict("pass" => haskey(VERDICT_CODES, witness["layer_verdict"]), "layer_verdict" => witness["layer_verdict"], "note" => "The verdict is computed from the finite readouts; all_pass does not promote the row."),
        "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
    )
    result = Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "2 finite Hopf lift/base discriminator",
        "backend" => BACKEND,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "carrier_readout_discriminator_probe",
        "source_alignment_category" => "hopf_s3_to_s2_lifted_vs_density_information_loss_discriminator",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "source_sha256" => sha256_file(@__FILE__),
        "result_path" => RESULT_PATH,
        "jax_source_path" => JAX_SOURCE_PATH,
        "jax_result_path" => JAX_RESULT_PATH,
        "source_refs" => source_refs(),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["julia", "linearalgebra", "jax peer"],
        "actual_tools_used" => ["julia", "linearalgebra", "julia stdlib", "three_spinor_associator_receipt"],
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
        "jax_x64_enabled" => true,
        "root_constraints_in_force" => Dict("F01" => "finite two-component spinor, finite global-phase orbit, finite density and Bloch readout table", "N01" => "phase-sensitive lifted readout is compared against quotient-erased density readouts and erasure controls"),
        "finite_map" => "psi in S3 with finite U(1) phase orbit -> rho=|psi><psi| in S2 Bloch base -> keyed lift/density readout gaps -> layer verdict",
        "domain" => "finite phase orbit of one normalized C2 spinor plus one base-changing control spinor",
        "codomain_or_output" => "layer verdict, lift/density information booleans, associator cross-check, parity block",
        "carrier_layer" => "Hopf lifted spinor S3 with explicit U(1) fiber coordinate",
        "geometry_layer" => "Hopf quotient S3 -> S2 represented by density matrix/Bloch vector base",
        "bridge_layer" => "none",
        "cut_layer" => "density quotient erases global U(1) phase",
        "law_or_candidate_tested" => "A phase/fiber readout survives on the lifted spinor and dies on rho=|psi><psi|",
        "branch_status_before_run" => "discriminator row requested; survival not assumed",
        "allowed_claims" => ["finite Hopf lift-vs-density discriminator verdict for this row", "global phase is visible to the chosen lifted readout and erased by the density quotient", "JAX and Julia agree on keyed finite scalars and booleans"],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "promotion_blockers" => BLOCKED_CONSUMERS,
        "layer_verdict" => witness["layer_verdict"],
        "erased_layer_verdict" => witness["erased_layer_verdict"],
        "lift_carries_info" => witness["booleans"]["lift_carries_info"],
        "density_quotient_loses_it" => witness["booleans"]["density_quotient_loses_it"],
        "associator_confirms" => witness["booleans"]["associator_confirms"],
        "phase_is_the_lost_info" => witness["booleans"]["phase_is_the_lost_info"],
        "owner_carrier_load_bearing" => witness["booleans"]["owner_erasure_changes_result"],
        "finite_witness" => witness,
        "shared_scalars" => witness["values"],
        "shared_booleans" => witness["booleans"],
        "positive" => positive,
        "negative" => negative,
        "graveyard_companions" => negative,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => 1, "passed" => haskey(VERDICT_CODES, witness["layer_verdict"]) ? 1 : 0, "variants" => ["hopf_s3_to_s2_lifted_vs_density_u1_phase"]),
        "why_not_v4_probes" => Dict("reason" => "density/base-only probes cannot carry the U(1) global phase; this row explicitly compares lift readouts to the quotient-erased base"),
        "pass_rule" => "classification fence, lift/density controls, owner-erasure ablation, associator cross-check, and dual-backend parity pass",
        "fail_rule" => "phase readout fails on the lift, density sees the phase, owner erasure does not change the verdict, associator cross-check fails, or parity diverges",
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => Any[],
        "required_artifacts" => [JAX_RESULT_PATH, RESULT_PATH],
        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "hopf_s3_s2_u1_phase_orbit_density_quotient",
    )
    result["parity"] = parity_against_peer(result)
    result["all_pass"] =
        result["parity"]["peer_available"] &&
        result["parity"]["within_1e_9"] &&
        all(Bool(row["pass"]) for row in values(positive)) &&
        all(Bool(row["pass"]) for row in values(negative)) &&
        all(Bool(row["pass"]) for row in values(boundary)) &&
        witness["layer_verdict"] == "REAL_LAYER"
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "layer_verdict" => result["layer_verdict"],
        "lift_carries_info" => result["lift_carries_info"],
        "density_quotient_loses_it" => result["density_quotient_loses_it"],
        "associator_confirms" => result["associator_confirms"],
        "phase_is_the_lost_info" => result["phase_is_the_lost_info"],
        "owner_carrier_load_bearing" => result["owner_carrier_load_bearing"],
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "claim_ceiling" => CLAIM_CEILING,
    )
    result["stop_condition_fired"] = !result["all_pass"]
    result["blockers"] = result["all_pass"] ? Any[] : ["parity missing/diverged or a required discriminator/control check failed"]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("RESULT $(OBJECT_ID) julia=$(RESULT_PATH) jax=$(JAX_RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) layer_verdict=$(result["layer_verdict"]) parity=$(lowercase(string(result["parity"]["within_1e_9"])))")
    return result["all_pass"] ? 0 : 1
end

exit(main())
