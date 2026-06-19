#!/usr/bin/env julia
# object_id: foundation_r0_probe_quotient_refinement_v1
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics

const OBJECT_ID = "foundation_r0_probe_quotient_refinement_v1"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r0_probe_quotient_refinement_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r0_probe_quotient_refinement_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1e-10

function rounded(x; digits=12)
    round(Float64(real(x)); digits=digits)
end

function qubit_objects()
    basis = SpinBasis(1 // 2)
    z0 = spindown(basis)
    z1 = spinup(basis)
    x_plus = (z0 + z1) / sqrt(2.0)
    x_minus = (z0 - z1) / sqrt(2.0)
    states = Dict{String,Any}(
        "rho_z0" => dm(z0),
        "rho_z1" => dm(z1),
        "rho_plus" => dm(x_plus),
        "rho_minus" => dm(x_minus),
    )
    probes = Dict{String,Any}(
        "Z" => Dict("name" => "Z", "outcome_labels" => ["z0", "z1"], "effects" => [dm(z0), dm(z1)]),
        "X" => Dict("name" => "X", "outcome_labels" => ["x_plus", "x_minus"], "effects" => [dm(x_plus), dm(x_minus)]),
        "Z_duplicate" => Dict("name" => "Z_duplicate", "outcome_labels" => ["z0_dup", "z1_dup"], "effects" => [dm(z0), dm(z1)]),
        "Z_relabel" => Dict("name" => "Z_relabel", "outcome_labels" => ["z1_relabel", "z0_relabel"], "effects" => [dm(z1), dm(z0)]),
    )
    return states, probes
end

function matrix_from_operator(rho)
    dense(rho).data
end

function density_admissibility(state_id::String, rho)
    mat = matrix_from_operator(rho)
    eigs = eigvals(Hermitian(mat))
    trace_value = tr(rho)
    Dict{String,Any}(
        "state_id" => state_id,
        "finite_object" => size(mat) == (2, 2),
        "shape" => [size(mat, 1), size(mat, 2)],
        "hermitian_residual_fro" => Float64(norm(mat - mat')),
        "trace_real" => Float64(real(trace_value)),
        "trace_imag_abs" => Float64(abs(imag(trace_value))),
        "trace_one" => abs(real(trace_value) - 1.0) <= TOL && abs(imag(trace_value)) <= TOL,
        "min_eigenvalue" => Float64(minimum(real.(eigs))),
        "psd" => minimum(real.(eigs)) >= -TOL,
    )
end

function distribution(rho, probe::Dict{String,Any})
    [rounded(tr(effect * rho)) for effect in probe["effects"]]
end

function signature(rho, probe_family)
    [distribution(rho, probe) for probe in probe_family]
end

function quotient(states::Dict{String,Any}, probe_family, name::String)
    classes = Dict{String,Dict{String,Any}}()
    for state_id in sort(collect(keys(states)))
        sig = signature(states[state_id], probe_family)
        key = JSON.json(sig)
        if !haskey(classes, key)
            classes[key] = Dict{String,Any}("members" => String[], "signature" => sig)
        end
        push!(classes[key]["members"], state_id)
    end
    rows = Vector{Dict{String,Any}}()
    for (idx, key) in enumerate(sort(collect(keys(classes))))
        push!(rows, Dict{String,Any}(
            "class_id" => "$(name)_q$(idx - 1)",
            "members" => sort(classes[key]["members"]),
            "signature" => classes[key]["signature"],
        ))
    end
    Dict{String,Any}(
        "name" => name,
        "probe_names" => [probe["name"] for probe in probe_family],
        "class_count" => length(rows),
        "classes" => rows,
        "partition_member_ids" => sort(collect(keys(states))),
    )
end

function class_containing(q, state_id::String)
    for cls in q["classes"]
        if state_id in cls["members"]
            return cls["class_id"]
        end
    end
    return nothing
end

function invalid_density_controls()
    trace_bad = [1.0 + 0.0im 0.0 + 0.0im; 0.0 + 0.0im 1.0 + 0.0im]
    psd_bad = [1.2 + 0.0im 0.0 + 0.0im; 0.0 + 0.0im -0.2 + 0.0im]
    nonhermitian_bad = [1.0 + 0.0im 1.0 + 0.0im; 0.0 + 0.0im 0.0 + 0.0im]
    controls = Dict{String,Any}()
    for (name, mat) in [
        ("invalid_trace_two_identity", trace_bad),
        ("invalid_psd_trace_one_diagonal", psd_bad),
        ("invalid_nonhermitian_trace_one", nonhermitian_bad),
    ]
        eig_min = ishermitian(mat) ? Float64(minimum(eigvals(Hermitian(mat)))) : nothing
        trace_value = tr(mat)
        controls[name] = Dict{String,Any}(
            "finite_object" => size(mat) == (2, 2),
            "hermitian_residual_fro" => Float64(norm(mat - mat')),
            "trace_real" => Float64(real(trace_value)),
            "trace_imag_abs" => Float64(abs(imag(trace_value))),
            "trace_one" => abs(real(trace_value) - 1.0) <= TOL && abs(imag(trace_value)) <= TOL,
            "min_eigenvalue" => eig_min,
            "psd" => eig_min === nothing ? false : eig_min >= -TOL,
            "accepted_as_density" => false,
        )
    end
    return controls
end

function build_result()
    states, probes = qubit_objects()
    q_empty = quotient(states, Any[], "empty_probe")
    q_z = quotient(states, [probes["Z"]], "M_Z")
    q_zx = quotient(states, [probes["Z"], probes["X"]], "M_ZX")
    q_duplicate_z = quotient(states, [probes["Z"], probes["Z_duplicate"]], "M_Z_duplicate")
    q_relabel_z = quotient(states, [probes["Z"], probes["Z_relabel"]], "M_Z_relabel")

    witness = Dict{String,Any}(
        "pair" => ["rho_plus", "rho_minus"],
        "Z_distributions" => Dict(
            "rho_plus" => distribution(states["rho_plus"], probes["Z"]),
            "rho_minus" => distribution(states["rho_minus"], probes["Z"]),
        ),
        "X_distributions" => Dict(
            "rho_plus" => distribution(states["rho_plus"], probes["X"]),
            "rho_minus" => distribution(states["rho_minus"], probes["X"]),
        ),
        "same_under_Z" => distribution(states["rho_plus"], probes["Z"]) == distribution(states["rho_minus"], probes["Z"]),
        "distinct_under_X" => distribution(states["rho_plus"], probes["X"]) != distribution(states["rho_minus"], probes["X"]),
        "same_Z_class" => class_containing(q_z, "rho_plus") == class_containing(q_z, "rho_minus"),
        "split_ZX_class" => class_containing(q_zx, "rho_plus") != class_containing(q_zx, "rho_minus"),
    )

    admissibility = Dict{String,Any}(
        state_id => density_admissibility(state_id, rho)
        for (state_id, rho) in states
    )
    all_admissible = all(
        row["finite_object"] && row["trace_one"] && row["psd"] && row["hermitian_residual_fro"] <= TOL
        for row in values(admissibility)
    )
    invalid_controls = invalid_density_controls()
    invalid_controls_rejected = all(!row["accepted_as_density"] && !(row["trace_one"] && row["psd"] && row["hermitian_residual_fro"] <= TOL) for row in values(invalid_controls))

    negative_controls = Dict{String,Any}(
        "empty_probe_collapses_identity" => Dict(
            "pass" => q_empty["class_count"] == 1,
            "class_count" => q_empty["class_count"],
        ),
        "duplicate_Z_does_not_refine" => Dict(
            "pass" => q_duplicate_z["class_count"] == q_z["class_count"],
            "Z_class_count" => q_z["class_count"],
            "duplicate_Z_class_count" => q_duplicate_z["class_count"],
        ),
        "relabel_Z_does_not_refine" => Dict(
            "pass" => q_relabel_z["class_count"] == q_z["class_count"],
            "Z_class_count" => q_z["class_count"],
            "relabel_Z_class_count" => q_relabel_z["class_count"],
        ),
        "invalid_density_candidates_rejected" => Dict(
            "pass" => invalid_controls_rejected,
            "candidates" => invalid_controls,
        ),
        "cross_engine_agreement_is_plumbing_not_proof" => Dict(
            "pass" => true,
            "note" => "This standalone Julia lane does not read peer JSON; any later agreement is envelope plumbing, not proof promotion.",
        ),
    )

    strict_refinement = (
        q_zx["class_count"] > q_z["class_count"] &&
        witness["same_under_Z"] &&
        witness["distinct_under_X"] &&
        witness["same_Z_class"] &&
        witness["split_ZX_class"]
    )
    all_pass = all_admissible && invalid_controls_rejected && strict_refinement &&
        all(row["pass"] for row in values(negative_controls))

    Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "engine" => "julia",
        "executable" => "/opt/homebrew/bin/julia --startup-file=no",
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "reads_peer_result" => READS_PEER_RESULT,
        "packages" => Dict(
            "load_bearing" => ["QuantumOptics"],
            "supportive" => ["LinearAlgebra", "JSON", "Dates"],
            "control_only" => String[],
            "missing_required" => String[],
        ),
        "package_observables" => Dict(
            "QuantumOptics" => "constructed qubit kets, density operators, projectors, Born-rule distributions, and trace observables",
            "LinearAlgebra" => "supportive Hermitian residual and PSD eigenvalue checks",
        ),
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing qubit states, density operators, projectors, and Born-rule probe distributions"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive Hermitian norm and eigenvalue checks for density admissibility"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
            "Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive timestamp"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "QuantumOptics" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON" => "supportive",
            "Dates" => "supportive",
        ),
        "finite_support" => Dict(
            "S" => ["rho_z0", "rho_z1", "rho_plus", "rho_minus"],
            "dimension" => 2,
            "state_kind" => "finite support qubit density matrices",
        ),
        "probe_families" => Dict(
            "M_empty" => String[],
            "M_Z" => ["Z"],
            "M_ZX" => ["Z", "X"],
            "M_Z_duplicate" => ["Z", "Z_duplicate"],
            "M_Z_relabel" => ["Z", "Z_relabel"],
        ),
        "quotient" => Dict(
            "empty_probe" => q_empty,
            "M_Z" => q_z,
            "M_ZX" => q_zx,
            "duplicate_Z_control" => q_duplicate_z,
            "relabel_Z_control" => q_relabel_z,
        ),
        "witness_pair" => witness,
        "density_admissibility" => admissibility,
        "negative_controls" => negative_controls,
        "core_checks" => Dict(
            "all_admissible_density_matrices" => all_admissible,
            "strict_quotient_refinement" => strict_refinement,
            "z_to_zx_class_count_increase" => q_zx["class_count"] - q_z["class_count"],
            "all_pass" => all_pass,
        ),
        "all_pass" => all_pass,
        "claim_ceiling" => "R0 scratch_diagnostic probe-relative quotient refinement only: finite support qubit states under M_Z versus M_ZX. Not M(C), not R1/R2, not formal, not canonical, not bridge, not axis evidence.",
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: ", RESULT_PATH)
    println(
        "SCOUT_DONE all_pass=", result["all_pass"],
        " z_classes=", result["quotient"]["M_Z"]["class_count"],
        " zx_classes=", result["quotient"]["M_ZX"]["class_count"],
        " witness_same_Z=", result["witness_pair"]["same_under_Z"],
        " witness_distinct_X=", result["witness_pair"]["distinct_under_X"],
        " reads_peer_result=", READS_PEER_RESULT,
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
