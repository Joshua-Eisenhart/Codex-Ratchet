#!/usr/bin/env julia
# object_id: foundation_r0_distinguishability_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using QuantumOptics

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_r0_distinguishability_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r0_distinguishability_julia_results.json")
const OBJECT_ID = "foundation_r0_distinguishability_julia"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const TOL = 1.0e-12

rounded(x::Real; digits::Int = 12) = round(Float64(x); digits = digits)

function ket_vec(basis::NLevelBasis, values::Vector{ComplexF64})
    ket = Ket(basis, values)
    return ket / sqrt(real(dagger(ket) * ket))
end

function projector(ket::Ket)
    return dm(ket)
end

function named_states()
    b = NLevelBasis(2)
    z0 = basisstate(b, 1)
    z1 = basisstate(b, 2)
    x_plus = ket_vec(b, ComplexF64[1.0 + 0im, 1.0 + 0im])
    x_minus = ket_vec(b, ComplexF64[1.0 + 0im, -1.0 + 0im])
    mixed = 0.5 * dm(z0) + 0.5 * dm(z1)
    Dict{String,Any}(
        "pure_z0" => dm(z0),
        "pure_z1" => dm(z1),
        "rho_a_x_plus" => dm(x_plus),
        "rho_b_x_minus" => dm(x_minus),
        "maximally_mixed" => mixed,
    )
end

function probe_families()
    b = NLevelBasis(2)
    z0 = basisstate(b, 1)
    z1 = basisstate(b, 2)
    x_plus = ket_vec(b, ComplexF64[1.0 + 0im, 1.0 + 0im])
    x_minus = ket_vec(b, ComplexF64[1.0 + 0im, -1.0 + 0im])
    Dict{String,Any}(
        "M1_Z" => Dict{String,Any}(
            "probe_names" => ["Z"],
            "effects" => Dict{String,Any}("Z" => [projector(z0), projector(z1)]),
        ),
        "M2_ZX" => Dict{String,Any}(
            "probe_names" => ["Z", "X"],
            "effects" => Dict{String,Any}(
                "Z" => [projector(z0), projector(z1)],
                "X" => [projector(x_plus), projector(x_minus)],
            ),
        ),
    )
end

function born_vector(rho::Operator, effects::AbstractVector)
    [rounded(real(expect(effect, rho))) for effect in effects]
end

function family_signature(rho::Operator, family::Dict{String,Any})
    [born_vector(rho, family["effects"][probe_name]) for probe_name in family["probe_names"]]
end

function quotient(states::Dict{String,Any}, family::Dict{String,Any}, name::String)
    classes = Dict{String,Any}()
    for state_id in sort(collect(keys(states)))
        sig = family_signature(states[state_id], family)
        key = JSON.json(sig)
        if !haskey(classes, key)
            classes[key] = Dict{String,Any}("members" => String[], "signature" => sig)
        end
        push!(classes[key]["members"], state_id)
    end
    rows = Any[]
    for (idx, key) in enumerate(sort(collect(keys(classes))))
        push!(rows, Dict{String,Any}(
            "class_id" => "$(name)_class_$(idx - 1)",
            "members" => sort(classes[key]["members"]),
            "signature" => classes[key]["signature"],
        ))
    end
    Dict{String,Any}(
        "name" => name,
        "probe_names" => family["probe_names"],
        "class_count" => length(rows),
        "classes" => rows,
    )
end

function matrix_rows(rho::Operator)
    data = dense(rho).data
    [[rounded(real(data[i, j])) for j in 1:size(data, 2)] for i in 1:size(data, 1)]
end

function hermitian_max_gap(rho::Operator)
    data = dense(rho).data
    maximum(abs(data[i, j] - conj(data[j, i])) for i in 1:size(data, 1), j in 1:size(data, 2))
end

function diagonal_psd_floor(rho::Operator)
    data = dense(rho).data
    if abs(data[1, 2]) <= TOL && abs(data[2, 1]) <= TOL
        return minimum([real(data[1, 1]), real(data[2, 2])])
    end
    trace = real(data[1, 1] + data[2, 2])
    determinant = real(data[1, 1] * data[2, 2] - data[1, 2] * data[2, 1])
    discriminant = max(trace * trace - 4.0 * determinant, 0.0)
    return (trace - sqrt(discriminant)) / 2.0
end

function constraint_report(states::Dict{String,Any}, families::Dict{String,Any})
    per_state = Dict{String,Any}()
    for state_id in sort(collect(keys(states)))
        rho = states[state_id]
        probe_norms = Dict{String,Any}()
        for (family_name, family) in families
            for probe_name in family["probe_names"]
                probe_norms["$(family_name):$(probe_name)"] = rounded(sum(born_vector(rho, family["effects"][probe_name])))
            end
        end
        per_state[state_id] = Dict{String,Any}(
            "trace" => rounded(real(tr(rho))),
            "trace_is_one" => abs(real(tr(rho)) - 1.0) <= TOL,
            "hermitian_max_gap" => rounded(hermitian_max_gap(rho); digits = 15),
            "psd_min_eigenvalue_floor" => rounded(diagonal_psd_floor(rho); digits = 15),
            "probability_normalizations" => probe_norms,
        )
    end
    per_state
end

function main()
    states = named_states()
    families = probe_families()
    q_z = quotient(states, families["M1_Z"], "M1_Z")
    q_zx = quotient(states, families["M2_ZX"], "M2_ZX")

    rho_a = states["rho_a_x_plus"]
    rho_b = states["rho_b_x_minus"]
    z_stats_a = born_vector(rho_a, families["M1_Z"]["effects"]["Z"])
    z_stats_b = born_vector(rho_b, families["M1_Z"]["effects"]["Z"])
    x_stats_a = born_vector(rho_a, families["M2_ZX"]["effects"]["X"])
    x_stats_b = born_vector(rho_b, families["M2_ZX"]["effects"]["X"])
    z_equal = all(abs(a - b) <= TOL for (a, b) in zip(z_stats_a, z_stats_b))
    x_different = any(abs(a - b) > TOL for (a, b) in zip(x_stats_a, x_stats_b))
    quotient_refines = q_z["class_count"] < q_zx["class_count"]

    constraints = constraint_report(states, families)
    all_constraints_ok = all(
        row["trace_is_one"] &&
        Float64(row["hermitian_max_gap"]) <= TOL &&
        Float64(row["psd_min_eigenvalue_floor"]) >= -TOL &&
        all(abs(Float64(v) - 1.0) <= TOL for v in values(row["probability_normalizations"]))
        for row in values(constraints)
    )
    all_pass = z_equal && x_different && quotient_refines && all_constraints_ok

    result = Dict{String,Any}(
        "schema" => "foundation_r0_distinguishability_engine_leg_v2",
        "object_id" => OBJECT_ID,
        "rung_id" => "foundation_r0_distinguishability",
        "classification" => CLASSIFICATION,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sZ"),
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => false,
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_project" => Base.active_project(),
        "packages_used" => ["QuantumOptics", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics"],
        "claim_path_tools" => ["QuantumOptics"],
        "M" => Dict{String,Any}(
            "M1" => ["Z"],
            "M2" => ["Z", "X"],
            "probe_effects" => Dict{String,Any}(
                "Z" => ["|0><0|", "|1><1|"],
                "X" => ["|+><+|", "|-><-|"],
            ),
        ),
        "C" => Dict{String,Any}(
            "trace_one" => true,
            "psd" => true,
            "hermitian" => true,
            "probability_normalization" => true,
            "rung_specific_constraint" => "rho_a and rho_b are distinct states with equal Z Born statistics and different X Born statistics",
            "per_state" => constraints,
        ),
        "S" => Dict{String,Any}(
            "definition" => "finite one-qubit density-matrix probe set used for quotient counting",
            "state_ids" => sort(collect(keys(states))),
            "state_matrices_real" => Dict{String,Any}(id => matrix_rows(rho) for (id, rho) in states),
        ),
        "S_mod_M" => Dict{String,Any}(
            "M1_Z" => q_z,
            "M2_ZX" => q_zx,
        ),
        "witness_pair" => Dict{String,Any}(
            "rho_a" => "rho_a_x_plus",
            "rho_b" => "rho_b_x_minus",
            "Z_stats_a" => z_stats_a,
            "Z_stats_b" => z_stats_b,
            "X_stats_a" => x_stats_a,
            "X_stats_b" => x_stats_b,
            "Z_equal" => z_equal,
            "X_different" => x_different,
        ),
        "negative_control_flip" => Dict{String,Any}(
            "control" => "drop_X_from_M2_ZX",
            "n_classes_Z" => q_z["class_count"],
            "n_classes_ZX" => q_zx["class_count"],
            "classes_refine_when_X_added" => quotient_refines,
        ),
        "summary" => Dict{String,Any}(
            "n_classes_Z" => q_z["class_count"],
            "n_classes_ZX" => q_zx["class_count"],
            "Z_equal" => z_equal,
            "X_different" => x_different,
            "all_pass" => all_pass,
        ),
        "all_pass" => all_pass,
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: $(RESULT_PATH)")
    println("JULIA_FOUNDATION_R0_DONE all_pass=$(all_pass) n_classes_Z=$(q_z["class_count"]) n_classes_ZX=$(q_zx["class_count"])")
    return all_pass ? 0 : 2
end

exit(main())
