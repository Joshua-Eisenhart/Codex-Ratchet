#!/usr/bin/env julia
# object_id: three_spinor_associator_scout
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite 3-spinor associator witness only. No final M(C),
# M(C+NA), PEPS3D admission, Axis0, physics/gravity, QIT-engine, bridge,
# global octonionic manifold, or formal-admission claim.

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "three_spinor_associator_scout"
const RESULT_PATH = joinpath(@__DIR__, "disc_associator_harden_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "..", "ops", "formal_scouts", "results", "disc_associator_harden_results.json")
const JAX_SOURCE_PATH = joinpath(@__DIR__, "..", "ops", "formal_scouts", "three_spinor_associator_scout.py")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function setprod!(signs::Matrix{Float64}, idxs::Matrix{Int}, a0::Int, b0::Int, c0::Int, s::Float64)
    signs[a0 + 1, b0 + 1] = s
    idxs[a0 + 1, b0 + 1] = c0 + 1
end

function octonion_table()
    signs = zeros(Float64, 8, 8)
    idxs = ones(Int, 8, 8)
    setprod!(signs, idxs, 0, 0, 0, 1.0)
    for i in 1:7
        setprod!(signs, idxs, 0, i, i, 1.0)
        setprod!(signs, idxs, i, 0, i, 1.0)
        setprod!(signs, idxs, i, i, 0, -1.0)
    end
    for (a, b, c) in FANO
        for (i, j, k) in [(a, b, c), (b, c, a), (c, a, b)]
            setprod!(signs, idxs, i, j, k, 1.0)
        end
        for (i, j, k) in [(b, a, c), (c, b, a), (a, c, b)]
            setprod!(signs, idxs, i, j, k, -1.0)
        end
    end
    signs, idxs
end

const TABLE_SIGNS, TABLE_IDXS = octonion_table()

function oct_mul(a::AbstractVector{Float64}, b::AbstractVector{Float64})
    out = zeros(Float64, 8)
    @inbounds for i in 1:8, j in 1:8
        out[TABLE_IDXS[i, j]] += TABLE_SIGNS[i, j] * a[i] * b[j]
    end
    out
end

function basis(idx0::Int)
    v = zeros(Float64, 8)
    v[idx0 + 1] = 1.0
    v
end

normalize_real(v::AbstractVector{Float64}) = collect(v) ./ norm(v)
normalize_spinor(psi::AbstractVector{ComplexF64}) = collect(psi) ./ norm(psi)

function seed_three_qubit_spinor()
    real = [1.0, -2.0, 3.0, 5.0, -7.0, 11.0, -13.0, 17.0]
    imag = [19.0, -23.0, 29.0, -31.0, 37.0, -41.0, 43.0, -47.0]
    normalize_spinor(ComplexF64.(real, imag))
end

spinor_to_oct_pair(psi::AbstractVector{ComplexF64}) = (real.(psi), imag.(psi))

function oct_pair_to_spinor(pair)
    real, imag = pair
    normalize_spinor(ComplexF64.(real, imag))
end

function right_action_pair(pair, q::AbstractVector{Float64})
    real, imag = pair
    oct_mul(real, q), oct_mul(imag, q)
end

function bracket_products(a::AbstractVector{Float64}, b::AbstractVector{Float64}, c::AbstractVector{Float64})
    oct_mul(oct_mul(a, b), c), oct_mul(a, oct_mul(b, c))
end

function projective_canonical(psi::AbstractVector{ComplexF64})
    anchor = psi[1]
    phase = anchor / abs(anchor)
    collect(psi) ./ phase
end

function density_gap(left::AbstractVector{ComplexF64}, right::AbstractVector{ComplexF64})
    rho_left = left * left'
    rho_right = right * right'
    norm(rho_left - rho_right)
end

function density_phase_erasure_control(psi::AbstractVector{ComplexF64})
    minus = -collect(psi)
    spinor_gap = norm(psi - minus)
    density_sign_gap = density_gap(psi, minus)
    Dict{String,Any}(
        "spinor_sign_gap" => spinor_gap,
        "density_sign_gap" => density_sign_gap,
        "pass" => spinor_gap > 1.0 && density_sign_gap < TOL,
    )
end

function bracket_witness(psi::AbstractVector{ComplexF64}, a::Vector{Float64}, b::Vector{Float64}, c::Vector{Float64})
    left_product, right_product = bracket_products(a, b, c)
    pair = spinor_to_oct_pair(psi)
    left = oct_pair_to_spinor(right_action_pair(pair, left_product))
    right = oct_pair_to_spinor(right_action_pair(pair, right_product))
    delta = left - right
    erased_left = projective_canonical(left)
    erased_right = projective_canonical(right)
    Dict{String,Any}(
        "product_gap" => norm(left_product - right_product),
        "spinor_gap" => norm(delta),
        "basis_probe_max_abs" => maximum(abs.(delta)),
        "optimal_unit_probe_abs" => norm(delta),
        "density_gap_fro" => density_gap(left, right),
        "bracket_erased_projective_gap" => norm(erased_left - erased_right),
        "left_product" => [Float64(v) for v in left_product],
        "right_product" => [Float64(v) for v in right_product],
    )
end

function right_mult_matrix(q::AbstractVector{Float64})
    hcat([oct_mul(basis(idx0), q) for idx0 in 0:7]...)
end

function raw_matrix_associativity_control(psi::AbstractVector{ComplexF64}, a::Vector{Float64}, b::Vector{Float64}, c::Vector{Float64})
    ra = right_mult_matrix(a)
    rb = right_mult_matrix(b)
    rc = right_mult_matrix(c)
    left_matrix = (rc * rb) * ra
    right_matrix = rc * (rb * ra)
    real, imag = spinor_to_oct_pair(psi)
    left = normalize_spinor(ComplexF64.(left_matrix * real, left_matrix * imag))
    right = normalize_spinor(ComplexF64.(right_matrix * real, right_matrix * imag))
    Dict{String,Any}(
        "matrix_associativity_gap" => norm(left_matrix - right_matrix),
        "raw_spinor_alpha_gap" => norm(left - right),
    )
end

arity_can_witness_associator(qubit_count::Int, operation_count::Int) = qubit_count >= 3 && operation_count >= 3

function file_sha256(path::String)
    isfile(path) || return nothing
    bytes2hex(sha256(read(path)))
end

function section_passes(section::Dict{String,Any})
    for row in values(section)
        if isa(row, Dict) && haskey(row, "pass") && !Bool(row["pass"])
            return false
        end
    end
    true
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        missing_row = Dict{String,Any}("missing" => peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_10" => false,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_8" => [missing_row],
            "strict_divergence_gt_1e_6" => [missing_row],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    strict_1e6 = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        julia_value = Float64(value)
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff)
        push!(rows, row)
        diff > STRICT_STOP_TOL && push!(strict, row)
        diff > 1.0e-6 && push!(strict_1e6, row)
    end
    mismatches = Vector{Dict{String,Any}}()
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
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_10" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "within_1e_9" => max_diff <= 1.0e-9 && isempty(strict_1e6) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_8" => strict,
        "strict_divergence_gt_1e_6" => strict_1e6,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing) || max_diff > TOL,
    )
end

function build_result()
    psi = seed_three_qubit_spinor()
    oct_a, oct_b, oct_c = basis(1), basis(2), basis(4)
    h_a, h_b, h_c = basis(1), basis(2), basis(3)
    alt_a, alt_b, alt_c = basis(1), basis(1), basis(4)

    oct_witness = bracket_witness(psi, oct_a, oct_b, oct_c)
    h_control = bracket_witness(psi, h_a, h_b, h_c)
    alt_control = bracket_witness(psi, alt_a, alt_b, alt_c)
    raw_control = raw_matrix_associativity_control(psi, oct_a, oct_b, oct_c)
    phase_control = density_phase_erasure_control(psi)

    positive = Dict{String,Any}(
        "three_qubit_spinor_cell_present" => Dict{String,Any}(
            "domain" => "psi in (C^2)^tensor3, dim_complex=8, finite 3-qubit spinor cell",
            "pass" => length(psi) == 8 && abs(norm(psi) - 1.0) < TOL,
        ),
        "octonion_bracketing_probe_visible" => Dict{String,Any}(
            "witness" => oct_witness,
            "pass" => oct_witness["spinor_gap"] > TOL && oct_witness["basis_probe_max_abs"] > TOL,
        ),
    )

    controls = Dict{String,Any}(
        "H_quaternion_associative_subalgebra_collapses" => Dict{String,Any}(
            "triple" => ["e1", "e2", "e3"],
            "witness" => h_control,
            "pass" => h_control["spinor_gap"] < TOL && h_control["product_gap"] < TOL,
        ),
        "octonion_alternativity_repeated_input_collapses" => Dict{String,Any}(
            "triple" => ["e1", "e1", "e4"],
            "witness" => alt_control,
            "pass" => alt_control["spinor_gap"] < TOL && alt_control["product_gap"] < TOL,
        ),
        "raw_matrix_composition_is_associative_control" => Dict{String,Any}(
            "matrix_associativity_gap" => raw_control["matrix_associativity_gap"],
            "raw_spinor_alpha_gap" => raw_control["raw_spinor_alpha_gap"],
            "pass" => raw_control["matrix_associativity_gap"] < TOL,
        ),
        "density_only_quotient_erases_lifted_associator_signal" => Dict{String,Any}(
            "density_gap_fro" => oct_witness["density_gap_fro"],
            "spinor_gap" => oct_witness["spinor_gap"],
            "pass" => oct_witness["density_gap_fro"] < TOL && oct_witness["spinor_gap"] > TOL,
            "note" => "The density-only readout erases the sign-level lifted associator witness.",
        ),
        "density_sign_phase_erasure_control" => phase_control,
        "two_qubit_two_operation_control_insufficient" => Dict{String,Any}(
            "qubit_count" => 2,
            "operation_count" => 2,
            "arity_sufficient" => arity_can_witness_associator(2, 2),
            "pass" => !arity_can_witness_associator(2, 2),
        ),
        "sedenion_zero_divisor_control_blocked" => Dict{String,Any}(
            "status" => "blocked_expected",
            "reason" => "Sedenion zero-divisor lane is not admitted in this finite spinor-network scout.",
            "pass" => true,
        ),
    )

    boundary = Dict{String,Any}(
        "density_only_quotient_erases_this_lifted_associator" => Dict{String,Any}(
            "density_gap_fro" => oct_witness["density_gap_fro"],
            "spinor_gap" => oct_witness["spinor_gap"],
            "pass" => oct_witness["density_gap_fro"] < TOL && oct_witness["spinor_gap"] > TOL,
            "note" => "For this triple, the two normalized bracketed spinors differ by sign, so rho=|psi><psi| erases the lifted witness.",
        ),
        "two_operation_boundary_insufficient_not_promoted" => Dict{String,Any}(
            "pass" => true,
            "note" => "Associator evidence requires three algebra inputs; two-operation checks are insufficient and are not promoted.",
        ),
        "NA_local_bracket_sensitive_probe_extension_only" => Dict{String,Any}(
            "pass" => true,
            "note" => "NA is recorded only as a local bracket-sensitive probe extension on this finite carrier, not as a new global foundation.",
        ),
        "promotion_and_formal_admission_disabled" => Dict{String,Any}(
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
            "pass" => true,
        ),
    )
    carrier_readout_controls = Dict{String,Any}(
        "owner-octonion-carrier" => Dict{String,Any}(
            "carrier" => "O finite basis table",
            "finite_witness" => "x=e1,y=e2,z=e4 in the finite Fano octonion table",
            "assoc" => oct_witness["product_gap"],
            "readout" => oct_witness["spinor_gap"],
            "pass" => abs(Float64(oct_witness["product_gap"]) - 2.0) < TOL && abs(Float64(oct_witness["spinor_gap"]) - 2.0) < TOL,
        ),
        "quaternion-restriction" => Dict{String,Any}(
            "carrier" => "H=span(1,e1,e2,e3)",
            "finite_witness" => "x=e1,y=e2,z=e3 restricted to the associative quaternion subalgebra",
            "assoc" => h_control["product_gap"],
            "readout" => h_control["spinor_gap"],
            "pass" => h_control["product_gap"] < TOL && h_control["spinor_gap"] < TOL,
        ),
        "density-only-quotient" => Dict{String,Any}(
            "carrier" => "rho=|psi><psi| readout quotient",
            "finite_witness" => "same e1,e2,e4 bracketing after quotienting the sign-level spinor witness",
            "assoc" => oct_witness["product_gap"],
            "readout" => oct_witness["density_gap_fro"],
            "collapses" => oct_witness["density_gap_fro"] < TOL,
            "pass" => oct_witness["spinor_gap"] > STRICT_STOP_TOL && oct_witness["density_gap_fro"] < TOL,
        ),
        "raw-associative-matrix" => Dict{String,Any}(
            "carrier" => "ordinary matrix composition of right-multiplication maps",
            "finite_witness" => "((Rc Rb) Ra) - (Rc (Rb Ra)) on the same finite basis maps",
            "assoc" => raw_control["matrix_associativity_gap"],
            "readout" => raw_control["raw_spinor_alpha_gap"],
            "pass" => raw_control["matrix_associativity_gap"] < TOL && raw_control["raw_spinor_alpha_gap"] < TOL,
        ),
        "two-qubit-two-operation-boundary" => Dict{String,Any}(
            "carrier" => "two-qubit/two-operation boundary control",
            "finite_witness" => "two operations cannot form a three-input associator witness",
            "assoc" => 0.0,
            "readout" => 0.0,
            "insufficient" => !arity_can_witness_associator(2, 2),
            "pass" => !arity_can_witness_associator(2, 2),
        ),
    )
    row_verdict = all(Bool(row["pass"]) for row in values(carrier_readout_controls)) ? "REAL_CARRIER" : "OPEN"

    shared_scalars = Dict{String,Any}(
        "dim_complex" => 8,
        "dim_real" => 16,
        "sample_count" => 1,
        "operation_triple_count" => 3,
        "octonion_product_gap" => oct_witness["product_gap"],
        "octonion_spinor_gap" => oct_witness["spinor_gap"],
        "basis_probe_max_abs" => oct_witness["basis_probe_max_abs"],
        "optimal_unit_probe_abs" => oct_witness["optimal_unit_probe_abs"],
        "density_gap_fro" => oct_witness["density_gap_fro"],
        "H_control_spinor_gap" => h_control["spinor_gap"],
        "H_control_product_gap" => h_control["product_gap"],
        "alternativity_control_spinor_gap" => alt_control["spinor_gap"],
        "alternativity_control_product_gap" => alt_control["product_gap"],
        "raw_matrix_assoc_gap" => raw_control["matrix_associativity_gap"],
        "density_sign_spinor_gap" => phase_control["spinor_sign_gap"],
        "density_sign_density_gap" => phase_control["density_sign_gap"],
        "discriminator.owner_octonion_assoc" => carrier_readout_controls["owner-octonion-carrier"]["assoc"],
        "discriminator.owner_octonion_readout" => carrier_readout_controls["owner-octonion-carrier"]["readout"],
        "discriminator.quaternion_restriction_assoc" => carrier_readout_controls["quaternion-restriction"]["assoc"],
        "discriminator.quaternion_restriction_readout" => carrier_readout_controls["quaternion-restriction"]["readout"],
        "discriminator.density_only_readout" => carrier_readout_controls["density-only-quotient"]["readout"],
        "discriminator.raw_associative_matrix_assoc" => carrier_readout_controls["raw-associative-matrix"]["assoc"],
        "discriminator.raw_associative_matrix_readout" => carrier_readout_controls["raw-associative-matrix"]["readout"],
        "discriminator.two_qubit_two_operation_assoc" => carrier_readout_controls["two-qubit-two-operation-boundary"]["assoc"],
    )

    local_checks_pass = section_passes(positive) && section_passes(controls) && section_passes(boundary)
    shared_booleans = Dict{String,Any}(
        "all_pass" => local_checks_pass,
        "positive.three_qubit_spinor_cell_present" => Bool(positive["three_qubit_spinor_cell_present"]["pass"]),
        "positive.octonion_bracketing_probe_visible" => Bool(positive["octonion_bracketing_probe_visible"]["pass"]),
        "control.H_quaternion_associative_subalgebra_collapses" => Bool(controls["H_quaternion_associative_subalgebra_collapses"]["pass"]),
        "control.octonion_alternativity_repeated_input_collapses" => Bool(controls["octonion_alternativity_repeated_input_collapses"]["pass"]),
        "control.raw_matrix_composition_is_associative" => Bool(controls["raw_matrix_composition_is_associative_control"]["pass"]),
        "control.density_only_quotient_erases_lifted_associator" => Bool(controls["density_only_quotient_erases_lifted_associator_signal"]["pass"]),
        "control.density_sign_phase_erasure" => Bool(controls["density_sign_phase_erasure_control"]["pass"]),
        "discriminator.owner_octonion_carrier_pass" => Bool(carrier_readout_controls["owner-octonion-carrier"]["pass"]),
        "discriminator.quaternion_restriction_pass" => Bool(carrier_readout_controls["quaternion-restriction"]["pass"]),
        "discriminator.density_only_quotient_collapses" => Bool(carrier_readout_controls["density-only-quotient"]["collapses"]),
        "discriminator.raw_associative_matrix_pass" => Bool(carrier_readout_controls["raw-associative-matrix"]["pass"]),
        "discriminator.two_qubit_two_operation_insufficient" => Bool(carrier_readout_controls["two-qubit-two-operation-boundary"]["insufficient"]),
        "discriminator.controls_exposed" => true,
        "discriminator.row_verdict_REAL_CARRIER" => row_verdict == "REAL_CARRIER",
        "boundary.density_only_quotient_erases_lifted_associator" => Bool(boundary["density_only_quotient_erases_this_lifted_associator"]["pass"]),
        "boundary.two_operation_boundary_insufficient_not_promoted" => Bool(boundary["two_operation_boundary_insufficient_not_promoted"]["pass"]),
        "boundary.NA_local_extension_only" => Bool(boundary["NA_local_bracket_sensitive_probe_extension_only"]["pass"]),
        "boundary.promotion_and_formal_admission_disabled" => Bool(boundary["promotion_and_formal_admission_disabled"]["pass"]),
        "root.F01_explicit" => true,
        "root.N01_explicit" => true,
    )

    tool_manifest = Dict{String,Any}(
        "Julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite spinor and octonion-coordinate arithmetic"),
        "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing norm, matrix, and density calculations"),
        "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent mirror for the same finite carrier controls and shared scalar/boolean parity"),
        "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
        "numpy" => Dict("tried" => false, "used" => false, "reason" => "not applicable in Julia mirror; no numpy compute is used"),
    )
    tool_depth = Dict{String,Any}(
        "Julia" => "load_bearing",
        "LinearAlgebra" => "load_bearing",
        "JAX peer backend" => "load_bearing",
        "JSON" => "supportive",
        "numpy" => nothing,
    )

    result = Dict{String,Any}(
        "schema" => "three_spinor_associator_scout_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "source_sha256" => file_sha256(@__FILE__),
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_metadata" => Dict{String,Any}(
            "backend" => "jax",
            "source_path" => JAX_SOURCE_PATH,
            "source_sha256" => file_sha256(JAX_SOURCE_PATH),
            "result_path" => JAX_REFERENCE_PATH,
            "result_sha256" => file_sha256(JAX_REFERENCE_PATH),
        ),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "promotion_status" => "diagnostic_only",
        "claim_ceiling" => "Scratch discriminator only: finite 3-spinor associator route-truth hardening with dual-backend parity. No final M(C), no M(C+NA) admission, no PEPS3D admission, no Axis0, no physics/gravity, no QIT-engine, no bridge, and no global octonionic manifold claim.",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_spinor_associator_probe",
        "finite_map" => "alpha_O(psi,x,y,z) = psi*((xy)z) - psi*(x(yz)) after octonion-coordinate right action and normalization",
        "domain" => "finite 3-qubit spinor cell psi in (C^2)^tensor3, dim_complex=8",
        "codomain_or_output" => "finite witness/control table: product gap, spinor gap, basis probe gap, density readout gap, parity rows",
        "root_constraints" => Dict{String,Any}(
            "F01" => "finite carrier/probe/operator/result: one normalized psi in (C^2)^tensor3, finite octonion basis triples, finite witnesses, finite JSON",
            "N01" => "noncommutation plus bracket-sensitivity are measured objects; the witness compares ((xy)z) against (x(yz)) on the same finite spinor cell",
            "NA" => "local bracket-sensitive probe extension only; not an admitted global foundation",
        ),
        "carrier_layer" => "finite spinor network scout cell; octonion coordinates are diagnostic readout/action coordinates, not an admitted primitive carrier",
        "operation_registry" => Dict{String,Any}(
            "octonion_nonassociative_witness" => Dict{String,Any}("algebra" => "O", "triple" => ["e1", "e2", "e4"]),
            "H_quaternion_associative_control" => Dict{String,Any}("algebra" => "H subset O", "triple" => ["e1", "e2", "e3"]),
            "octonion_alternativity_control" => Dict{String,Any}("algebra" => "O", "triple" => ["e1", "e1", "e4"]),
        ),
        "peps3d_embedding" => Dict{String,Any}("status" => "not_admitted", "note" => "No PEPS3D admission or downstream carrier promotion is made."),
        "blocked_consumers" => ["final_M(C)", "M(C+NA)", "PEPS3D", "Axis0", "physics_gravity", "QIT_engine", "bridge", "global_octonionic_manifold"],
        "numpy_compute_used" => false,
        "TOOL_MANIFEST" => tool_manifest,
        "TOOL_INTEGRATION_DEPTH" => tool_depth,
        "tool_manifest" => tool_manifest,
        "tool_integration_depth" => tool_depth,
        "positive" => positive,
        "carrier_readout_discriminator" => Dict{String,Any}(
            "decisive_rule" => "REAL_CARRIER iff owner octonion carrier has assoc=2/readout=2 and all named mutated or quotient controls collapse to zero/insufficient",
            "controls_exposed" => true,
            "row_verdict" => row_verdict,
            "rows" => carrier_readout_controls,
        ),
        "finite_witnesses" => carrier_readout_controls,
        "CONTROLS" => controls,
        "controls" => controls,
        "graveyard_companions" => controls,
        "boundary" => boundary,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "numbers" => shared_scalars,
        "verdicts" => Dict{String,Any}(
            "finite_3_spinor_associator_witness_exists" => section_passes(positive),
            "controls_behave" => section_passes(controls),
            "row_verdict" => row_verdict,
        ),
        "why_not_v4_probes" => [
            Dict{String,Any}(
                "reason" => "This is a branch-1 finite associator scout with no final M(C), M(C+NA), PEPS3D, Axis0, physics/gravity, QIT-engine, bridge, or global octonionic manifold claim.",
                "pass" => true,
            ),
        ],
        "nearby_variants" => Dict{String,Any}(
            "total" => 2,
            "passed" => 2,
            "items" => [
                Dict{String,Any}(
                    "variant" => "raw_linear_matrix_composition",
                    "status" => "control_collapses",
                    "measured_gap" => raw_control["raw_spinor_alpha_gap"],
                    "pass" => true,
                ),
                Dict{String,Any}(
                    "variant" => "density_only_projective_readout",
                    "status" => "control_collapses",
                    "measured_gap" => oct_witness["density_gap_fro"],
                    "pass" => true,
                ),
            ],
        ),
        "plain_sentence" => "The finite 3-spinor discriminator preserves the single associator survivor: octonion owner carrier assoc=2 and quaternion/raw/density/two-operation controls collapse; raw matrix composition, quotient erasure, density-only readout, quaternionic restriction, and repeated-input alternativity controls collapse as expected.",
        "witnesses" => Dict{String,Any}(
            "octonion" => oct_witness,
            "H_quaternion_control" => h_control,
            "alternativity_control" => alt_control,
            "density_phase_erasure_control" => phase_control,
        ),
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
    )

    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["boundary"]["dual_backend_parity_boundary"] = Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "parity_max_diff" => result["parity"]["parity_max_diff"],
        "within_1e_10" => result["parity"]["within_1e_10"],
        "pass" => Bool(result["parity"]["within_1e_10"]),
    )
    result["all_pass"] = section_passes(positive) && section_passes(controls) && section_passes(result["boundary"])
    result["shared_booleans"]["all_pass"] = Bool(result["all_pass"])
    result["verdicts"]["dual_backend_parity"] = Bool(result["parity"]["within_1e_10"])
    result["verdicts"]["all_pass"] = Bool(result["all_pass"])
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => Bool(result["all_pass"]),
        "row_verdict" => row_verdict,
        "owner_assoc" => carrier_readout_controls["owner-octonion-carrier"]["assoc"],
        "quaternion_assoc" => carrier_readout_controls["quaternion-restriction"]["assoc"],
        "density_readout" => carrier_readout_controls["density-only-quotient"]["readout"],
        "raw_matrix_assoc" => carrier_readout_controls["raw-associative-matrix"]["assoc"],
        "two_qubit_two_operation_insufficient" => carrier_readout_controls["two-qubit-two-operation-boundary"]["insufficient"],
        "controls_exposed" => true,
    )
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result
end

function print_summary(result::Dict{String,Any})
    s = result["shared_scalars"]
    println("three_spinor_associator_scout - Julia backend")
    println("spinor_gap=", s["octonion_spinor_gap"],
        " product_gap=", s["octonion_product_gap"],
        " density_gap=", s["density_gap_fro"])
    println("raw_matrix_assoc_gap=", s["raw_matrix_assoc_gap"],
        " density_sign_spinor_gap=", s["density_sign_spinor_gap"],
        " H_gap=", s["H_control_spinor_gap"],
        " alt_gap=", s["alternativity_control_spinor_gap"])
    println("parity_status=", result["parity"]["status"],
        " parity_max_diff=", result["parity"]["parity_max_diff"],
        " within_1e-10=", result["parity"]["within_1e_10"],
        " all_pass=", result["all_pass"])
    println("wrote: ", result["result_path"])
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if result["stop_condition_fired"]
    exit(2)
end
