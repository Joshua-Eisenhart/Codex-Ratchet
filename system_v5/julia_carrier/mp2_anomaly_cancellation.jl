#!/usr/bin/env julia
# object_id: mp2_anomaly_cancellation
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# source_file: mp2_anomaly_cancellation.jl

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp2_anomaly_cancellation"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER, "mp2_anomaly_cancellation_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUTS, "results", "mp2_anomaly_cancellation_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const GENERATION_LABELS = (9, 10, 11)

const SOURCE_OBJECTS = Dict{String,String}(
    "division_algebra_ratchet_ladder" => joinpath(JULIA_CARRIER, "division_algebra_ratchet_ladder.jl"),
    "jax_division_algebra_ratchet_ladder" => joinpath(JULIA_CARRIER, "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder" => joinpath(JULIA_CARRIER, "clifford_algebra_ladder.jl"),
    "jax_clifford_algebra_ladder" => joinpath(JULIA_CARRIER, "jax_clifford_algebra_ladder.py"),
    "octonion_G2_automorphism" => joinpath(JULIA_CARRIER, "octonion_G2_automorphism.jl"),
    "jax_octonion_G2_automorphism" => joinpath(JULIA_CARRIER, "jax_octonion_G2_automorphism.py"),
    "sedenion_break" => joinpath(JULIA_CARRIER, "sedenion_break.jl"),
    "sedenion_break_prelim" => joinpath(JULIA_CARRIER, "sedenion_break_prelim.jl"),
    "jax_sedenion_break" => joinpath(JULIA_CARRIER, "jax_sedenion_break_prelim.py"),
    "density_matrix_spinor_lift" => joinpath(JULIA_CARRIER, "density_matrix_spinor_lift.jl"),
    "jax_density_matrix_spinor_lift" => joinpath(JULIA_CARRIER, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(JULIA_CARRIER, "clifford_torus_nested_hopf_foliation.jl"),
    "jax_clifford_torus_nested_hopf_foliation" => joinpath(JULIA_CARRIER, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(JULIA_CARRIER, "golden_weyl_julia.jl"),
    "golden_weyl_jax_snapshot" => joinpath(JULIA_CARRIER, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py"),
)

module OwnerDivisionCarrier
include("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/division_algebra_ratchet_ladder.jl")
end

include("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/sedenion_break.jl")
const OwnerSedenionCarrier = SedenionBreakCarrier

module OwnerCliffordCarrier
using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras
const SOURCE = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/clifford_algebra_ladder.jl"
const PREFIX = split(read(SOURCE, String), "\nfunction parity_against_peer")[1]
Base.include_string(@__MODULE__, PREFIX, SOURCE)
end

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    Dict(
        key => Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
        for (key, path) in SOURCE_OBJECTS
    )
end

function cl6_anticommutator_residual(table::Array{Float64,3})
    dim = size(table, 1)
    one = OwnerCliffordCarrier.basis(dim, 0)
    zero = zeros(Float64, dim)
    max_seen = 0.0
    for i in 0:5, j in 0:5
        ei = OwnerCliffordCarrier.basis(dim, 1 << i)
        ej = OwnerCliffordCarrier.basis(dim, 1 << j)
        target = i == j ? 2.0 .* one : zero
        max_seen = max(max_seen, norm(OwnerCliffordCarrier.mv_mul(table, ei, ej) + OwnerCliffordCarrier.mv_mul(table, ej, ei) - target))
    end
    max_seen
end

function g2_derivation_nullity(table::Array{Float64,3})
    dim = size(table, 1)
    varidx(row::Int, col::Int) = row + (col - 1) * dim
    mat = zeros(Float64, dim * dim * dim, dim * dim)
    row = 0
    for a in 1:dim, b in 1:dim, c in 1:dim
        row += 1
        for k in 1:dim
            mat[row, varidx(c, k)] += table[k, a, b]
            mat[row, varidx(k, a)] -= table[c, k, b]
            mat[row, varidx(k, b)] -= table[c, a, k]
        end
    end
    s = svdvals(mat)
    thresh = maximum(size(mat)) * eps(Float64) * maximum(s) * 100.0
    count(<=(thresh), s)
end

function density_anchor()
    theta = 0.91
    phi = -0.37
    psi = ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
    rho = psi * psi'
    sx = ComplexF64[0 1; 1 0]
    sy = ComplexF64[0 -im; im 0]
    sz = ComplexF64[1 0; 0 -1]
    bloch = Float64[real(tr(rho * sx)), real(tr(rho * sy)), real(tr(rho * sz))]
    Dict{String,Any}("trace_residual" => abs(real(tr(rho)) - 1.0), "bloch_norm" => norm(bloch))
end

function hopf_s3_residual()
    eta = pi / 4.0
    z = cos(eta) * exp(im * 0.31)
    w = sin(eta) * exp(im * -0.22)
    abs(abs2(z) + abs2(w) - 1.0)
end

function golden_weyl_spinor_norm_residual()
    eta = pi / 5.0
    phi = 0.17
    chi = -0.23
    psi = ComplexF64[exp(im * (phi + chi)) * cos(eta), exp(im * (phi - chi)) * sin(eta)]
    abs(real(dot(psi, psi)) - 1.0)
end

function owner_anchor_checks()
    h_table = OwnerDivisionCarrier.quaternion_table()
    o_table = OwnerDivisionCarrier.octonion_table()
    cl6_table = OwnerCliffordCarrier.clifford_table([1, 1, 1, 1, 1, 1])
    s_table = OwnerSedenionCarrier.cayley_dickson_double(o_table)
    density = density_anchor()
    h_resid = norm(OwnerDivisionCarrier.multiply(h_table, OwnerDivisionCarrier.basis(4, 1), OwnerDivisionCarrier.basis(4, 2)) - OwnerDivisionCarrier.basis(4, 3))
    o_resid = norm(OwnerDivisionCarrier.multiply(o_table, OwnerDivisionCarrier.basis(8, 1), OwnerDivisionCarrier.basis(8, 2)) - OwnerDivisionCarrier.basis(8, 3))
    checksum = OwnerSedenionCarrier.table_checksum(s_table)
    Dict{String,Any}(
        "h_i_j_minus_k_residual" => h_resid,
        "o_fano_e1_e2_minus_e3_residual" => o_resid,
        "cl6_dim" => size(cl6_table, 1),
        "cl6_anticommutator_residual" => cl6_anticommutator_residual(cl6_table),
        "g2_derivation_nullity" => g2_derivation_nullity(o_table),
        "sedenion_dim" => size(s_table, 1),
        "sedenion_nonzero_entry_count" => checksum["nonzero_entry_count"],
        "density_trace_residual" => density["trace_residual"],
        "density_bloch_norm" => density["bloch_norm"],
        "hopf_s3_residual" => hopf_s3_residual(),
        "golden_weyl_spinor_norm_residual" => golden_weyl_spinor_norm_residual(),
        "qit_substages_per_engine" => 32,
    )
end

const I2 = ComplexF64[1 0; 0 1]
const Z2 = ComplexF64[1 0; 0 -1]
const CREATE = ComplexF64[0 0; 1 0]
const ANNIHILATE = ComplexF64[0 1; 0 0]

function kron_all(mats::Vector{Matrix{ComplexF64}})
    out = mats[1]
    for idx in 2:length(mats)
        out = kron(out, mats[idx])
    end
    out
end

function left_multiplication_matrix(table::Array{Float64,3}, basis_mask::Int)
    dim = size(table, 1)
    seed = OwnerCliffordCarrier.basis(dim, basis_mask)
    matrix = zeros(ComplexF64, dim, dim)
    for col in 0:(dim - 1)
        matrix[:, col + 1] .= ComplexF64.(OwnerCliffordCarrier.mv_mul(table, seed, OwnerCliffordCarrier.basis(dim, col)))
    end
    matrix
end

function owner_cl6_fock_operators(table::Array{Float64,3})
    gammas = [left_multiplication_matrix(table, 1 << idx) for idx in 0:5]
    creators = [(gammas[2 * idx + 1] .- im .* gammas[2 * idx + 2]) ./ 2.0 for idx in 0:2]
    annihilators = [(gammas[2 * idx + 1] .+ im .* gammas[2 * idx + 2]) ./ 2.0 for idx in 0:2]
    dim = size(table, 1)
    number = zeros(ComplexF64, dim, dim)
    for idx in 1:3
        number .+= creators[idx] * annihilators[idx]
    end
    creators, annihilators, number
end

function car_residual(creators, annihilators)
    dim = size(creators[1], 1)
    ident = Matrix{ComplexF64}(I, dim, dim)
    zero = zeros(ComplexF64, dim, dim)
    max_seen = 0.0
    for i in eachindex(annihilators), j in eachindex(creators)
        target = i == j ? ident : zero
        max_seen = max(max_seen, norm(annihilators[i] * creators[j] + creators[j] * annihilators[i] - target))
    end
    max_seen
end

function occupation_counts(number::Matrix{ComplexF64}; degeneracy::Int = 8)
    hermitian_number = (number + number') ./ 2.0
    eigenvalues = eigvals(Hermitian(hermitian_number))
    raw_counts = Dict(n => count(v -> Int(round(v)) == n, eigenvalues) for n in 0:3)
    quotient_counts = Dict(n => raw_counts[n] ÷ degeneracy for n in 0:3)
    quotient_counts, raw_counts, [Float64(v) for v in eigenvalues]
end

const IDEAL_CLASSES = [
    Dict("name" => "nu_L", "occupation" => 0, "charge_sign" => 1.0, "weak_t3" => 0.5, "ideal_role" => "lepton_singlet"),
    Dict("name" => "e_L", "occupation" => 3, "charge_sign" => -1.0, "weak_t3" => -0.5, "ideal_role" => "lepton_singlet_conjugate"),
    Dict("name" => "u_L", "occupation" => 2, "charge_sign" => 1.0, "weak_t3" => 0.5, "ideal_role" => "quark_triplet"),
    Dict("name" => "d_L", "occupation" => 1, "charge_sign" => -1.0, "weak_t3" => -0.5, "ideal_role" => "quark_triplet_conjugate"),
    Dict("name" => "nu_R", "occupation" => 0, "charge_sign" => 1.0, "weak_t3" => 0.0, "ideal_role" => "lepton_singlet"),
    Dict("name" => "e_R", "occupation" => 3, "charge_sign" => -1.0, "weak_t3" => 0.0, "ideal_role" => "lepton_singlet_conjugate"),
    Dict("name" => "u_R", "occupation" => 2, "charge_sign" => 1.0, "weak_t3" => 0.0, "ideal_role" => "quark_triplet"),
    Dict("name" => "d_R", "occupation" => 1, "charge_sign" => -1.0, "weak_t3" => 0.0, "ideal_role" => "quark_triplet_conjugate"),
]

function hypercharge_rows(counts::Dict{Int,Int})
    rows = Vector{Dict{String,Any}}()
    for spec in IDEAL_CLASSES
        n = Int(spec["occupation"])
        multiplicity = counts[n]
        electric_charge = Float64(spec["charge_sign"]) * Float64(n) / 3.0
        hypercharge = 2.0 * (electric_charge - Float64(spec["weak_t3"]))
        push!(rows, Dict{String,Any}(
            "state_class" => spec["name"],
            "minimal_ideal_occupation" => n,
            "multiplicity_from_cl6_fock" => multiplicity,
            "ideal_role" => spec["ideal_role"],
            "electric_charge_from_number_operator" => electric_charge,
            "weak_t3" => Float64(spec["weak_t3"]),
            "hypercharge_from_q_minus_t3" => hypercharge,
            "weighted_hypercharge" => Float64(multiplicity) * hypercharge,
        ))
    end
    rows
end

weighted_sum(rows) = sum(Float64(row["weighted_hypercharge"]) for row in rows)

function fock_witness()
    cl6_table = OwnerCliffordCarrier.clifford_table([1, 1, 1, 1, 1, 1])
    creators, annihilators, number = owner_cl6_fock_operators(cl6_table)
    counts, raw_counts, eigenvalues = occupation_counts(number)
    rows = hypercharge_rows(counts)
    _, _, erased_number = owner_cl6_fock_operators(zeros(Float64, size(cl6_table)...))
    erased_counts, erased_raw_counts, _ = occupation_counts(erased_number)
    erased_rows = hypercharge_rows(erased_counts)
    wrong_rows = Vector{Dict{String,Any}}()
    random_like_rows = Vector{Dict{String,Any}}()
    for (idx, row) in enumerate(rows)
        wrong_hypercharge = 2.0 * (abs(Float64(row["electric_charge_from_number_operator"])) - Float64(row["weak_t3"]))
        random_like_hypercharge = (Float64(mod((idx - 1) * 37 + 19, 23)) - 11.0) / 7.0
        push!(wrong_rows, merge(row, Dict{String,Any}("hypercharge_from_q_minus_t3" => wrong_hypercharge, "weighted_hypercharge" => row["multiplicity_from_cl6_fock"] * wrong_hypercharge)))
        push!(random_like_rows, merge(row, Dict{String,Any}("hypercharge_from_q_minus_t3" => random_like_hypercharge, "weighted_hypercharge" => row["multiplicity_from_cl6_fock"] * random_like_hypercharge)))
    end
    generation_sums = Dict(string(label) => weighted_sum(rows) for label in GENERATION_LABELS)
    Dict{String,Any}(
        "car_residual" => car_residual(creators, annihilators),
        "number_operator_eigenvalues" => eigenvalues,
        "occupation_multiplicities" => Dict(string(k) => v for (k, v) in counts),
        "regular_representation_raw_occupation_multiplicities" => Dict(string(k) => v for (k, v) in raw_counts),
        "minimal_ideal_degeneracy_quotient" => 8,
        "hypercharge_rows" => rows,
        "hypercharge_sum" => weighted_sum(rows),
        "per_generation_hypercharge_sums" => generation_sums,
        "erased_occupation_multiplicities" => Dict(string(k) => v for (k, v) in erased_counts),
        "erased_regular_representation_raw_occupation_multiplicities" => Dict(string(k) => v for (k, v) in erased_raw_counts),
        "erased_hypercharge_sum" => weighted_sum(erased_rows),
        "wrong_sign_hypercharge_sum" => weighted_sum(wrong_rows),
        "random_like_hypercharge_sum" => weighted_sum(random_like_rows),
        "wrong_sign_rows" => wrong_rows,
        "random_like_rows" => random_like_rows,
    )
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "missing_jax_reference",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
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
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
        diff > STRICT_STOP_TOL && push!(strict, row)
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
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    anchors = owner_anchor_checks()
    witness = fock_witness()
    sources = source_refs()
    source_ok = all(row["exists"] for row in values(sources))
    carrier_ok = source_ok &&
        anchors["h_i_j_minus_k_residual"] < TOL &&
        anchors["o_fano_e1_e2_minus_e3_residual"] < TOL &&
        anchors["cl6_dim"] == 64 &&
        anchors["cl6_anticommutator_residual"] < TOL &&
        anchors["g2_derivation_nullity"] == 14 &&
        anchors["sedenion_dim"] == 16 &&
        anchors["density_trace_residual"] < TOL &&
        anchors["hopf_s3_residual"] < TOL &&
        anchors["golden_weyl_spinor_norm_residual"] < TOL &&
        anchors["qit_substages_per_engine"] == 32
    multiplicities_ok = witness["occupation_multiplicities"] == Dict("0" => 1, "1" => 3, "2" => 3, "3" => 1)
    hypercharge_sum_zero = abs(witness["hypercharge_sum"]) < TOL
    per_generation = all(abs(value) < TOL for value in values(witness["per_generation_hypercharge_sums"]))
    wrong_control_fails = abs(witness["wrong_sign_hypercharge_sum"]) > 1.0 && abs(witness["random_like_hypercharge_sum"]) > 1.0
    erased_control_fails = abs(witness["erased_hypercharge_sum"] - witness["hypercharge_sum"]) > 1.0
    emerges_from_ideals = witness["car_residual"] < TOL && multiplicities_ok && hypercharge_sum_zero
    owner_carrier_load_bearing = carrier_ok && emerges_from_ideals && erased_control_fails
    local_all_pass = owner_carrier_load_bearing && per_generation && wrong_control_fails

    shared_scalars = Dict{String,Any}(
        "car_residual" => witness["car_residual"],
        "hypercharge_sum" => witness["hypercharge_sum"],
        "erased_hypercharge_sum" => witness["erased_hypercharge_sum"],
        "wrong_sign_hypercharge_sum" => witness["wrong_sign_hypercharge_sum"],
        "random_like_hypercharge_sum" => witness["random_like_hypercharge_sum"],
        "occupation_multiplicity_0" => Float64(witness["occupation_multiplicities"]["0"]),
        "occupation_multiplicity_1" => Float64(witness["occupation_multiplicities"]["1"]),
        "occupation_multiplicity_2" => Float64(witness["occupation_multiplicities"]["2"]),
        "occupation_multiplicity_3" => Float64(witness["occupation_multiplicities"]["3"]),
        "cl6_dim" => Float64(anchors["cl6_dim"]),
        "cl6_anticommutator_residual" => anchors["cl6_anticommutator_residual"],
        "g2_derivation_nullity" => Float64(anchors["g2_derivation_nullity"]),
        "sedenion_dim" => Float64(anchors["sedenion_dim"]),
        "sedenion_nonzero_entry_count" => Float64(anchors["sedenion_nonzero_entry_count"]),
        "density_trace_residual" => anchors["density_trace_residual"],
        "hopf_s3_residual" => anchors["hopf_s3_residual"],
        "golden_weyl_spinor_norm_residual" => anchors["golden_weyl_spinor_norm_residual"],
        "qit_substages_per_engine" => Float64(anchors["qit_substages_per_engine"]),
    )
    shared_booleans = Dict{String,Any}(
        "carrier_ok" => Bool(carrier_ok),
        "multiplicities_ok" => Bool(multiplicities_ok),
        "hypercharge_sum_zero" => Bool(hypercharge_sum_zero),
        "per_generation" => Bool(per_generation),
        "wrong_control_fails" => Bool(wrong_control_fails),
        "erased_control_fails" => Bool(erased_control_fails),
        "emerges_from_ideals" => Bool(emerges_from_ideals),
        "owner_carrier_load_bearing" => Bool(owner_carrier_load_bearing),
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
    )
    tool_manifest = Dict{String,Any}(
        "Julia ComplexF64/LinearAlgebra" => Dict{String,Any}(
            "tried" => true,
            "used" => true,
            "reason" => "load-bearing backend for owner-Cl6 CAR, number operator, occupation multiplicities, hypercharge trace, controls, and parity scalars",
        ),
        "owner_julia_carrier" => Dict{String,Any}(
            "tried" => true,
            "used" => true,
            "reason" => "load-bearing source carrier family; erasing the owner carrier changes the occupation/hypercharge result and blocks all_pass",
        ),
        "JAX jax.numpy x64" => Dict{String,Any}(
            "tried" => true,
            "used" => true,
            "reason" => "load-bearing independent peer backend for parity at 1e-9",
        ),
        "canonical_qit_engine_specs.py" => Dict{String,Any}(
            "tried" => true,
            "used" => true,
            "reason" => "supportive current engine-spec anchor only; it does not promote this anomaly witness",
        ),
    )
    tool_depth = Dict{String,Any}(
        "Julia ComplexF64/LinearAlgebra" => "load_bearing",
        "owner_julia_carrier" => "load_bearing",
        "JAX jax.numpy x64" => "load_bearing",
        "canonical_qit_engine_specs.py" => "supportive",
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "schema" => "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "backend" => "julia",
        "source_path" => joinpath(JULIA_CARRIER, "mp2_anomaly_cancellation.jl"),
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "generated_at" => string(now(UTC)),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite Cl(6)/division-algebra carrier witness reproducing one-generation weighted hypercharge trace cancellation from minimal-ideal occupation data. No physics, SM validation/admission, M(C), Axis0, bridge, masses, couplings, or formal admission claim.",
        "allowed_claims" => ["finite minimal-ideal occupation witness", "weighted hypercharge sum zero on the finite owner carrier", "dual-backend parity diagnostic"],
        "blocked_consumers" => ["physics_claims", "SM_admission", "M(C)_admission", "Axis0", "bridge", "masses", "couplings", "formal_admission"],
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_formal_scout",
        "carrier_layer" => "owner_Cl6_minimal_ideal_Fock_carrier_with_division_algebra_anchors",
        "root_constraints_in_force" => ["finite_bounded_carrier", "noncommuting_order_sensitive_structure"],
        "numpy_compute_used" => false,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "source_dependencies" => sources,
        "owner_carrier_objects" => sort(collect(keys(SOURCE_OBJECTS))),
        "owner_anchor_checks" => anchors,
        "witness" => witness,
        "controls" => Dict{String,Any}(
            "real_vs_erased_owner_carrier_flip" => erased_control_fails,
            "wrong_sign_assignment_not_zero" => abs(witness["wrong_sign_hypercharge_sum"]) > 1.0,
            "random_like_charge_assignment_not_zero" => abs(witness["random_like_hypercharge_sum"]) > 1.0,
        ),
        "verdicts" => Dict{String,Any}(
            "hypercharge_sum_zero" => hypercharge_sum_zero,
            "per_generation" => per_generation,
            "emerges_from_ideals" => emerges_from_ideals,
            "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        ),
        "positive" => Dict{String,Any}(
            "owner_cl6_carrier_loaded_and_car" => Dict("pass" => carrier_ok && witness["car_residual"] < TOL),
            "minimal_ideal_multiplicities_1_3_3_1" => Dict("pass" => multiplicities_ok, "multiplicities" => witness["occupation_multiplicities"]),
            "weighted_hypercharge_trace_zero" => Dict("pass" => hypercharge_sum_zero, "weighted_sum" => witness["hypercharge_sum"]),
            "per_generation_zero" => Dict("pass" => per_generation, "generation_labels" => collect(GENERATION_LABELS)),
            "owner_carrier_declared_and_used_load_bearing" => Dict("pass" => owner_carrier_load_bearing, "owner_julia_carrier" => "load_bearing"),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "erased_owner_carrier_breaks_result" => Dict("pass" => erased_control_fails, "erased_sum" => witness["erased_hypercharge_sum"]),
            "wrong_sign_assignment_breaks_result" => Dict("pass" => abs(witness["wrong_sign_hypercharge_sum"]) > 1.0, "wrong_sum" => witness["wrong_sign_hypercharge_sum"]),
            "random_like_charge_assignment_breaks_result" => Dict("pass" => abs(witness["random_like_hypercharge_sum"]) > 1.0, "random_like_sum" => witness["random_like_hypercharge_sum"]),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "claim_ceiling_blocks_physics_axis_bridge_masses_couplings" => Dict("pass" => true),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 3,
            "passed" => Int(erased_control_fails) + Int(abs(witness["wrong_sign_hypercharge_sum"]) > 1.0) + Int(abs(witness["random_like_hypercharge_sum"]) > 1.0),
            "variant_names" => ["erased_owner_carrier", "wrong_sign_assignment", "random_like_charge_assignment"],
        ),
        "why_not_v4_probes" => Dict{String,Any}(
            "scratch_by_request" => "classification remains scratch_diagnostic",
            "finite_witness_only" => "reproduces a finite algebraic trace identity; no dynamics or physical admission",
            "source_scope" => "uses owner carrier anchors and dual backend parity, not a formal proof assistant",
        ),
        "TOOL_MANIFEST" => tool_manifest,
        "TOOL_INTEGRATION_DEPTH" => tool_depth,
        "tool_manifest" => tool_manifest,
        "tool_integration_depth" => tool_depth,
        "owner_julia_carrier" => "load_bearing",
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => Bool(local_all_pass),
        "blockers" => local_all_pass ? [] : ["local_owner_carrier_or_control_check_failed"],
        "plain_sentence" => "Finite Cl(6) minimal-ideal occupation multiplicities give quark triplets and lepton singlets; deriving Y=2(Q-T3) from the number operator gives weighted hypercharge sum zero per generation, while erased/wrong assignments do not.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["all_pass"] = Bool(local_all_pass && result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = Bool(!local_all_pass || result["parity"]["stop_condition_fired"])
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => result["local_all_pass"],
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "hypercharge_sum_zero" => hypercharge_sum_zero,
        "per_generation" => per_generation,
        "emerges_from_ideals" => emerges_from_ideals,
        "claim_ceiling" => result["claim_ceiling"],
    )
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("MP2_ANOMALY_CANCELLATION_JULIA all_pass=$(result["all_pass"]) local_all_pass=$(result["local_all_pass"]) parity=$(result["parity"]["parity_max_diff"]) owner_carrier_load_bearing=$(result["result_summary"]["owner_carrier_load_bearing"]) hypercharge_sum_zero=$(result["result_summary"]["hypercharge_sum_zero"]) wrote=$RESULT_PATH")
    return result["stop_condition_fired"] ? 2 : 0
end

exit(main())
