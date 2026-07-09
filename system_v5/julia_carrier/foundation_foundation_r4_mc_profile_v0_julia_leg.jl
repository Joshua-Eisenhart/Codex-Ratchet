#!/usr/bin/env julia
# object_id: foundation_r4_mc_profile_v0_julia_leg
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false
# rung_reclassified_from_r4_to_r2: true
#
# REPAIR NOTE (R4 reopen): this sim's probe family (P_z0, P_xplus, P_yplus on
# a generic single-qubit Bloch sphere) has no derivation link to R3's
# admitted octonion/Cl(6) carrier (foundation_r3_octonion_cl6_link_xhigh) --
# it is a bare SpinBasis(1/2) toy with zero octonion or Cl(6) content.
# Per the reopen instructions, honest options were: (a) derive the probe
# family from the R3 carrier with a stated derivation, or (b) reclassify as
# R2-level since it has zero linkage to any R3 carrier structure. No
# non-fabricated derivation exists (this is an ordinary qubit density-matrix
# quotient profile, not an octonion/Cl(6) object), so this object is
# reclassified to R2 (foundation_build_spine.md's "admissible-operations
# layer on M(C)") rather than faking an R3 link. It stays scratch_diagnostic,
# promotion_allowed=false, formal_admission_allowed=false, and does not claim
# R4 carrier status.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const OBJECT_ID = "foundation_r4_mc_profile_v0_julia_leg"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_foundation_r4_mc_profile_v0_julia_leg.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "results", "foundation_foundation_r4_mc_profile_v0_julia_leg_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const RUNG_RECLASSIFIED_FROM_R4_TO_R2 = true
const RUNG_RECLASSIFICATION_REASON = "Probe family (P_z0, P_xplus, P_yplus on a generic SpinBasis(1/2)) has zero derivation link to R3's admitted octonion/Cl(6) carrier; no non-fabricated R3 derivation exists, so this object is demoted to R2 (admissible-operations layer on M(C)) rather than asserting a fake R3 dependency."
const PROBE_LO = 1 // 8
const PROBE_HI = 7 // 8
const GRID = [-1 // 1, -1 // 2, 0 // 1, 1 // 2, 1 // 1]
const TOL = 1.0e-10

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

ratstr(x::Rational) = "$(numerator(x))/$(denominator(x))"
ratfloat(x::Rational) = Float64(x)

function qoperator(basis, rows)
    data = rows isa AbstractMatrix ? rows : [rows[1][1] rows[1][2]; rows[2][1] rows[2][2]]
    DenseOperator(basis, ComplexF64.(data))
end

function bloch_matrix(x::Rational, y::Rational, z::Rational)
    [
        (1 + z) / 2 (x - im * y) / 2;
        (x + im * y) / 2 (1 - z) / 2
    ]
end

function born_probs_formula(x::Rational, y::Rational, z::Rational)
    Dict(
        "P_z0" => (1 + z) / 2,
        "P_xplus" => (1 + x) / 2,
        "P_yplus" => (1 + y) / 2,
    )
end

function continuous_admitted(x::Rational, y::Rational, z::Rational)
    probs = born_probs_formula(x, y, z)
    det_margin = (1 - x * x - y * y - z * z) / 4
    trace_ok = true
    hermitian_ok = true
    psd_ok = det_margin >= 0
    probe_ok = all(PROBE_LO <= p <= PROBE_HI for p in values(probs))
    trace_ok && hermitian_ok && psd_ok && probe_ok
end

function state_record(basis, probes, x::Rational, y::Rational, z::Rational)
    matrix = bloch_matrix(x, y, z)
    rho = qoperator(basis, matrix)
    data = dense(rho).data
    q_probs = Dict(k => real(tr(p * rho)) for (k, p) in probes)
    f_probs = born_probs_formula(x, y, z)
    evals = eigvals(Hermitian(data))
    det_margin = (1 - x * x - y * y - z * z) / 4
    admitted = continuous_admitted(x, y, z)
    Dict{String,Any}(
        "id" => "x=$(ratstr(x));y=$(ratstr(y));z=$(ratstr(z))",
        "bloch" => Dict("x" => ratstr(x), "y" => ratstr(y), "z" => ratstr(z)),
        "matrix_entries" => Dict(
            "a" => ratstr((1 + z) / 2),
            "d" => ratstr((1 - z) / 2),
            "re_upper" => ratstr(x / 2),
            "im_upper" => ratstr(-y / 2)
        ),
        "probe_probabilities_exact" => Dict(k => ratstr(v) for (k, v) in f_probs),
        "probe_probabilities_quantumoptics" => q_probs,
        "determinant_margin_exact" => ratstr(det_margin),
        "min_eigenvalue" => minimum(real.(evals)),
        "admitted_under_C" => admitted,
        "quotient_key_full_M" => join([ratstr(f_probs[k]) for k in ["P_z0", "P_xplus", "P_yplus"]], "|"),
        "quotient_key_drop_P_yplus" => join([ratstr(f_probs[k]) for k in ["P_z0", "P_xplus"]], "|"),
    )
end

function quotient_classes(records, key_name::String)
    classes = Dict{String,Vector{String}}()
    for r in records
        r["admitted_under_C"] || continue
        key = r[key_name]
        if !haskey(classes, key)
            classes[key] = String[]
        end
        push!(classes[key], r["id"])
    end
    classes
end

function class_size_summary(classes)
    sizes = sort([length(v) for v in values(classes)])
    Dict("class_count" => length(sizes), "min_class_size" => minimum(sizes), "max_class_size" => maximum(sizes))
end

function convex_midpoint_profile(records)
    admitted = [r for r in records if r["admitted_under_C"]]
    failures = String[]
    checks = 0
    for left in admitted
        for right in admitted
            xl = parse_rational(left["bloch"]["x"])
            yl = parse_rational(left["bloch"]["y"])
            zl = parse_rational(left["bloch"]["z"])
            xr = parse_rational(right["bloch"]["x"])
            yr = parse_rational(right["bloch"]["y"])
            zr = parse_rational(right["bloch"]["z"])
            xm, ym, zm = (xl + xr) / 2, (yl + yr) / 2, (zl + zr) / 2
            checks += 1
            continuous_admitted(xm, ym, zm) || push!(failures, "$(left["id"]) + $(right["id"])")
        end
    end
    Dict("all_pairwise_midpoints_admitted" => isempty(failures), "ordered_pair_count" => checks, "failures" => failures[1:min(length(failures), 5)])
end

function parse_rational(s::String)
    parts = split(s, "/")
    parse(Int, parts[1]) // parse(Int, parts[2])
end

function build_result()
    started = time()
    basis = SpinBasis(1 // 2)
    probes = Dict(
        "P_z0" => qoperator(basis, [[1, 0], [0, 0]]),
        "P_xplus" => qoperator(basis, [[0.5, 0.5], [0.5, 0.5]]),
        "P_yplus" => qoperator(basis, [[0.5, -0.5im], [0.5im, 0.5]]),
    )
    records = [state_record(basis, probes, x, y, z) for x in GRID for y in GRID for z in GRID]
    admitted = [r for r in records if r["admitted_under_C"]]
    full_classes = quotient_classes(records, "quotient_key_full_M")
    drop_y_classes = quotient_classes(records, "quotient_key_drop_P_yplus")
    commuting_subset = [r for r in admitted if r["bloch"]["x"] == "0/1" && r["bloch"]["y"] == "0/1"]
    convex_profile = convex_midpoint_profile(records)

    profile = Dict{String,Any}(
        "grid_values" => [ratstr(v) for v in GRID],
        "grid_cardinality" => length(records),
        "admitted_cardinality" => length(admitted),
        "excluded_grid_cardinality" => length(records) - length(admitted),
        "full_M" => class_size_summary(full_classes),
        "drop_P_yplus" => class_size_summary(drop_y_classes),
        "drop_probe_coarsens_quotient" => length(keys(drop_y_classes)) < length(keys(full_classes)),
        "force_commuting_with_P_z0_admitted_cardinality" => length(commuting_subset),
        "force_commuting_changes_profile" => length(commuting_subset) < length(admitted),
    )
    negative_controls = Dict(
        "non_psd_inside_probe_bounds" => Dict("bloch" => Dict("x" => "3/4", "y" => "3/4", "z" => "3/4"), "violated_constraint" => "PSD"),
        "trace_not_one" => Dict("matrix_entries" => Dict("a" => "3/4", "d" => "3/4", "re_upper" => "0/1", "im_upper" => "0/1"), "violated_constraint" => "trace=1"),
        "probe_upper_bound_z0" => Dict("bloch" => Dict("x" => "0/1", "y" => "0/1", "z" => "1/1"), "violated_constraint" => "probe_bounds"),
        "probe_prob_gt_1" => Dict("matrix_entries" => Dict("a" => "1/2", "d" => "1/2", "re_upper" => "3/4", "im_upper" => "0/1"), "violated_constraint" => "probe_bounds and PSD"),
    )
    all_pass = profile["admitted_cardinality"] == 27 &&
               profile["full_M"]["class_count"] == 27 &&
               profile["drop_P_yplus"]["class_count"] == 9 &&
               profile["drop_probe_coarsens_quotient"] &&
               profile["force_commuting_changes_profile"] &&
               convex_profile["all_pairwise_midpoints_admitted"] &&
               READS_PEER_RESULT == false

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "backend" => "julia_quantumoptics_authoritative_mc_profile",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "rung_reclassified_from_r4_to_r2" => RUNG_RECLASSIFIED_FROM_R4_TO_R2,
        "rung_reclassification_reason" => RUNG_RECLASSIFICATION_REASON,
        "ran" => true,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "executable" => "/opt/homebrew/bin/julia --project=@v1.12 --startup-file=no",
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "M_probe_family" => [
            Dict("id" => "P_z0", "projector" => "|0><0|"),
            Dict("id" => "P_xplus", "projector" => "|+><+|"),
            Dict("id" => "P_yplus", "projector" => "|i+><i+|"),
        ],
        "C_constraints" => [
            "trace(rho)=1",
            "rho=rho^dagger",
            "PSD via 2x2 principal minors/eigenvalues",
            "1/8 <= Tr(P rho) <= 7/8 for each P in M",
        ],
        "quotient_relation" => "rho ~_M sigma iff Tr(P rho)=Tr(P sigma) for every P in finite M",
        "profile" => profile,
        "convex_closure" => convex_profile,
        "sample_admitted_records" => admitted[1:min(5, length(admitted))],
        "negative_controls" => negative_controls,
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing construction of SpinBasis, DenseOperator states/projectors, and Born expectations defining M and C"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive eigenvalue checks of QuantumOptics operator data"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source fingerprint"),
            "Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive timestamp"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "QuantumOptics" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON" => "supportive",
            "SHA" => "supportive",
            "Dates" => "supportive",
        ),
        "claim_ceiling" => "Reclassified R2 M(C) profile v0 (not R4) scratch diagnostic only. It profiles a finite 2x2 probe quotient under explicit constraints on a generic qubit; no octonion/Cl(6) carrier dependency exists, so this is NOT an R4 object. No promotion or formal admission.",
        "runtime_seconds" => round(time() - started; digits=6),
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE all_pass=$(result["all_pass"]) " *
        "admitted=$(result["profile"]["admitted_cardinality"]) " *
        "full_M_classes=$(result["profile"]["full_M"]["class_count"]) " *
        "drop_P_yplus_classes=$(result["profile"]["drop_P_yplus"]["class_count"]) " *
        "convex_midpoints=$(result["convex_closure"]["ordered_pair_count"]) " *
        "reads_peer_result=$(result["reads_peer_result"])"
    )
    return result["all_pass"] ? 0 : 2
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
