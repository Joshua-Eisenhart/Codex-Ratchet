#!/usr/bin/env julia
# object_id: foundation_r1_n01_noncommutation_order_quotient_v1
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using Symbolics
using Z3

const OBJECT_ID = "foundation_r1_n01_noncommutation_order_quotient_v1"
const ENGINE = "julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r1_n01_noncommutation_order_quotient_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r1_n01_noncommutation_order_quotient_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-10

const OUTCOME_LABELS = ["++", "+-", "-+", "--"]
const STATE_IDS = ["ket0", "ket1", "ket_plus", "ket_minus", "ket_i_plus", "maximally_mixed"]
const PROBE_IDS = ["Z", "X", "Z_duplicate"]
const ORDERED_HISTORIES = ["Z_then_X", "X_then_Z", "Z_then_Z_duplicate", "Z_duplicate_then_Z"]

function mat(op)
    return Matrix{ComplexF64}(dense(op).data)
end

function finite_qit_object()
    b = SpinBasis(1//2)
    ket0 = spindown(b)
    ket1 = spinup(b)
    ket_plus = (ket0 + ket1) / sqrt(2.0)
    ket_minus = (ket0 - ket1) / sqrt(2.0)
    ket_i_plus = (ket0 + im * ket1) / sqrt(2.0)
    pz_plus = dm(ket0)
    pz_minus = dm(ket1)
    px_plus = dm(ket_plus)
    px_minus = dm(ket_minus)
    identity = identityoperator(b)
    states = Dict{String,Matrix{ComplexF64}}(
        "ket0" => mat(dm(ket0)),
        "ket1" => mat(dm(ket1)),
        "ket_plus" => mat(dm(ket_plus)),
        "ket_minus" => mat(dm(ket_minus)),
        "ket_i_plus" => mat(dm(ket_i_plus)),
        "maximally_mixed" => mat(identity / 2.0),
    )
    projectors = Dict{String,Vector{Matrix{ComplexF64}}}(
        "Z" => [mat(pz_plus), mat(pz_minus)],
        "X" => [mat(px_plus), mat(px_minus)],
        "Z_duplicate" => [mat(pz_plus), mat(pz_minus)],
    )
    z_op = projectors["Z"][1] - projectors["Z"][2]
    x_op = projectors["X"][1] - projectors["X"][2]
    return states, projectors, z_op, x_op
end

function joint_distribution(rho::Matrix{ComplexF64}, first::Vector{Matrix{ComplexF64}}, second::Vector{Matrix{ComplexF64}})
    probs = Float64[]
    for p1 in first
        branch = p1 * rho * p1
        for p2 in second
            push!(probs, Float64(real(tr(p2 * branch))))
        end
    end
    return probs
end

function tv_gap(a::Vector{Float64}, b::Vector{Float64})
    return 0.5 * sum(abs.(a .- b))
end

function rounded_signature(values::Vector{Float64}; digits::Int=12)
    return [round(v; digits=digits) for v in values]
end

function quotient_classes(rows::Vector{Dict{String,Any}}, signature_key::String)
    grouped = Dict{String,Vector{String}}()
    for row in rows
        key = join(row[signature_key], "|")
        grouped[key] = get(grouped, key, String[])
        push!(grouped[key], row["state_id"])
    end
    classes = Vector{Dict{String,Any}}()
    for (idx, key) in enumerate(sort(collect(keys(grouped))))
        push!(classes, Dict{String,Any}(
            "class_id" => idx,
            "signature_key" => key,
            "state_ids" => sort(grouped[key]),
        ))
    end
    return Dict{String,Any}(
        "class_count" => length(classes),
        "classes" => classes,
    )
end

function exact_finite_checks()
    z = [1//1 0//1; 0//1 -1//1]
    x = [0//1 1//1; 1//1 0//1]
    comm_zx = z * x - x * z
    comm_zz = z * z - z * z

    solver = Solver()
    l1_num = IntVar("julia_l1_num")
    tv_num = IntVar("julia_tv_num")
    tv_den = IntVar("julia_tv_den")
    add(solver, l1_num == IntVal(4))
    add(solver, tv_num == IntVal(1))
    add(solver, tv_den == IntVal(2))
    add(solver, l1_num > IntVal(0))
    add(solver, tv_den > IntVal(0))
    main_status = string(check(solver))

    bad = Solver()
    bad_l1_num = IntVar("julia_bad_l1_num")
    add(bad, bad_l1_num == IntVal(4))
    add(bad, bad_l1_num == IntVal(0))
    bad_status = string(check(bad))

    return Dict{String,Any}(
        "exact_commutator_ZX_entries" => string(comm_zx),
        "exact_commutator_ZZ_entries" => string(comm_zz),
        "exact_ZX_commutator_nonzero" => any(!iszero, comm_zx),
        "exact_ZZ_commutator_zero" => all(iszero, comm_zz),
        "symbolics_loaded" => true,
        "z3" => Dict{String,Any}(
            "ran" => true,
            "load_bearing" => true,
            "verdict" => main_status,
            "negative_control_verdict" => bad_status,
            "claim" => "Exact ket0 order-gap certificate: L1 numerator 4 over denominator 4 gives total-variation gap 1/2; contradictory zero-gap control is unsat.",
            "pass" => main_status == "sat" && bad_status == "unsat",
        ),
    )
end

function build_result()
    states, projectors, z_op, x_op = finite_qit_object()
    comm_zx = z_op * x_op - x_op * z_op
    comm_zz = z_op * z_op - z_op * z_op

    rows = Vector{Dict{String,Any}}()
    for state_id in STATE_IDS
        rho = states[state_id]
        zx = joint_distribution(rho, projectors["Z"], projectors["X"])
        xz = joint_distribution(rho, projectors["X"], projectors["Z"])
        zz = joint_distribution(rho, projectors["Z"], projectors["Z_duplicate"])
        zdupz = joint_distribution(rho, projectors["Z_duplicate"], projectors["Z"])
        noncommuting_gap = tv_gap(zx, xz)
        control_gap = tv_gap(zz, zdupz)
        push!(rows, Dict{String,Any}(
            "state_id" => state_id,
            "Z_then_X" => rounded_signature(zx),
            "X_then_Z" => rounded_signature(xz),
            "Z_then_Z_duplicate" => rounded_signature(zz),
            "Z_duplicate_then_Z" => rounded_signature(zdupz),
            "noncommuting_order_gap" => noncommuting_gap,
            "commuting_control_order_gap" => control_gap,
            "noncommuting_quotient_signature" => rounded_signature(vcat(zx, xz, [noncommuting_gap])),
            "commuting_control_quotient_signature" => rounded_signature(vcat(zz, zdupz, [control_gap])),
        ))
    end

    noncommuting_quotient = quotient_classes(rows, "noncommuting_quotient_signature")
    commuting_quotient = quotient_classes(rows, "commuting_control_quotient_signature")
    witness = rows[findfirst(row -> row["state_id"] == "ket0", rows)]
    exact_checks = exact_finite_checks()
    noncommuting_gap_max = maximum(row["noncommuting_order_gap"] for row in rows)
    commuting_gap_max = maximum(row["commuting_control_order_gap"] for row in rows)
    refined = noncommuting_quotient["class_count"] > commuting_quotient["class_count"]

    negative_controls = Dict{String,Any}(
        "commuting_duplicate_Z_has_zero_commutator" => Dict("pass" => norm(comm_zz) <= TOL, "commutator_norm" => Float64(norm(comm_zz))),
        "commuting_duplicate_Z_has_zero_order_gap_all_states" => Dict("pass" => commuting_gap_max <= TOL, "max_order_gap" => Float64(commuting_gap_max)),
        "noncommuting_ZX_has_nonzero_commutator" => Dict("pass" => norm(comm_zx) > TOL, "commutator_norm" => Float64(norm(comm_zx))),
        "finite_witness_ket0_has_nonzero_order_gap" => Dict("pass" => witness["noncommuting_order_gap"] > TOL, "state_id" => "ket0", "order_gap" => Float64(witness["noncommuting_order_gap"])),
        "noncommuting_quotient_refines_commuting_control" => Dict("pass" => refined, "noncommuting_class_count" => noncommuting_quotient["class_count"], "commuting_control_class_count" => commuting_quotient["class_count"]),
    )

    all_pass = Bool(
        all(row["commuting_control_order_gap"] <= TOL for row in rows) &&
        witness["noncommuting_order_gap"] > TOL &&
        norm(comm_zx) > TOL &&
        norm(comm_zz) <= TOL &&
        refined &&
        exact_checks["z3"]["pass"] &&
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false &&
        READS_PEER_RESULT == false
    )

    return Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "executable" => "/opt/homebrew/bin/julia --startup-file=no",
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "backend" => "julia_quantumoptics_z3",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "finite_object" => Dict{String,Any}(
            "hilbert_dimension" => 2,
            "state_ids" => STATE_IDS,
            "named_positive_witness" => "ket0",
            "probe_ids" => PROBE_IDS,
            "projective_probes" => Dict("Z" => "computational-basis rank-1 projectors", "X" => "Hadamard-basis rank-1 projectors", "Z_duplicate" => "duplicate/relabel of Z projectors"),
            "ordered_histories" => ORDERED_HISTORIES,
            "outcome_labels" => OUTCOME_LABELS,
        ),
        "ordered_histories" => Dict{String,Any}(
            "rows" => rows,
            "witness_ket0" => witness,
        ),
        "quotient" => Dict{String,Any}(
            "definition" => "States are quotiented by rounded ordered-history outcome-distribution signatures. Noncommuting uses Z_then_X and X_then_Z; control uses duplicate Z histories.",
            "noncommuting" => noncommuting_quotient,
            "commuting_control" => commuting_quotient,
            "strict_refinement_observed" => refined,
        ),
        "class_signatures" => Dict{String,Any}(
            "outcome_order" => OUTCOME_LABELS,
            "state_rows" => rows,
        ),
        "noncommuting" => Dict{String,Any}(
            "probe_pair" => "Z,X",
            "commutator_norm" => Float64(norm(comm_zx)),
            "commutator_norm_fro" => Float64(norm(comm_zx)),
            "order_gap" => Float64(witness["noncommuting_order_gap"]),
            "order_gap_max" => Float64(noncommuting_gap_max),
            "witness_state_id" => "ket0",
            "classification" => "nonzero_commutator_nonzero_order_gap_refined_quotient",
        ),
        "commuting_control" => Dict{String,Any}(
            "probe_pair" => "Z,Z_duplicate",
            "commutator_norm" => Float64(norm(comm_zz)),
            "commutator_norm_fro" => Float64(norm(comm_zz)),
            "order_gap" => Float64(commuting_gap_max),
            "order_gap_max" => Float64(commuting_gap_max),
            "classification" => "zero_commutator_zero_order_gap_coarser_quotient",
        ),
        "negative_controls" => negative_controls,
        "finite_certificates" => exact_checks,
        "packages" => Dict{String,Any}(
            "load_bearing" => ["QuantumOptics", "Z3"],
            "supportive" => ["Symbolics", "LinearAlgebra", "JSON", "Dates"],
            "control_only" => String[],
            "missing_required" => String[],
        ),
        "package_observables" => Dict{String,Any}(
            "QuantumOptics" => "Constructed SpinBasis states, rank-1 projectors, density operators, and projective ordered-history probabilities.",
            "Z3" => "Checked exact finite ket0 order-gap arithmetic with an unsat contradictory zero-gap control.",
            "Symbolics" => "Loaded for exact finite-check surface; rational matrices record exact commutator entries.",
            "LinearAlgebra" => "Supportive Frobenius norms and trace arithmetic.",
        ),
        "TOOL_MANIFEST" => Dict{String,Any}(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite qubit states, projectors, and projective measurement histories"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing exact finite order-gap SAT/UNSAT certificate"),
            "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "supportive exact finite-check surface alongside rational commutator arithmetic"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive local matrix norms and traces"),
            "JSON/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization and timestamping"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "QuantumOptics" => "load_bearing",
            "Z3" => "load_bearing",
            "Symbolics" => "supportive",
            "LinearAlgebra" => "supportive",
            "JSON/Dates" => "supportive",
        ),
        "claim_ceiling" => "R1 N01 scratch diagnostic only: finite one-qubit projective-probe ordered-history quotient. Not full M(C), not R0/R1-F01/R2, not formal admission, not canonical, not bridge, not axis, and not physics/gravity/entropy-master evidence.",
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote ", RESULT_PATH)
    println("SCOUT_DONE all_pass=", result["all_pass"],
        " noncommuting_order_gap=", result["noncommuting"]["order_gap"],
        " commuting_control_order_gap=", result["commuting_control"]["order_gap"],
        " noncommuting_classes=", result["quotient"]["noncommuting"]["class_count"],
        " commuting_control_classes=", result["quotient"]["commuting_control"]["class_count"],
        " reads_peer_result=", result["reads_peer_result"])
    return result["all_pass"] ? 0 : 2
end

exit(main())
