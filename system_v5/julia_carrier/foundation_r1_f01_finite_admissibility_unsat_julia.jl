#!/usr/bin/env julia
# object_id: foundation_r1_f01_finite_admissibility_unsat_v1
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using Z3

const OBJECT_ID = "foundation_r1_f01_finite_admissibility_unsat_v1"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r1_f01_finite_admissibility_unsat_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r1_f01_finite_admissibility_unsat_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const N = 4
const SUPPORT = collect(0:(N - 1))
const POSITIVE_K = 4
const NEGATIVE_K = 5
const RAISED_N = 5

function add_injection_constraints!(solver, vars, n::Int; finite_bound::Bool)
    for x in vars
        if finite_bound
            add(solver, Not(x < IntVal(0)))
            add(solver, x < IntVal(n))
        end
    end
    for i in eachindex(vars)
        for j in (i + 1):length(vars)
            add(solver, Not(vars[i] == vars[j]))
        end
    end
end

function z3_status(k::Int, n::Int; finite_bound::Bool, label::String)
    solver = Solver()
    vars = [IntVar("$(label)_x$(i)") for i in 1:k]
    add_injection_constraints!(solver, vars, n; finite_bound=finite_bound)
    string(check(solver))
end

function permutation_count(k::Int, n::Int)
    if k > n
        return big(0)
    end
    out = big(1)
    for value in (n - k + 1):n
        out *= value
    end
    out
end

function local_support_observables()
    positive_mask = [atom < POSITIVE_K for atom in SUPPORT]
    negative_slots_available = length(SUPPORT)
    Dict{String,Any}(
        "support_vector" => SUPPORT,
        "positive_mask" => positive_mask,
        "positive_mask_l1" => Float64(norm(Float64.(positive_mask), 1)),
        "positive_candidate_size" => POSITIVE_K,
        "negative_candidate_size" => NEGATIVE_K,
        "negative_excess_atoms" => max(NEGATIVE_K - negative_slots_available, 0),
        "positive_embedding_count" => string(permutation_count(POSITIVE_K, N)),
        "negative_embedding_count" => string(permutation_count(NEGATIVE_K, N)),
        "raised_bound_embedding_count" => string(permutation_count(NEGATIVE_K, RAISED_N))
    )
end

function build_result()
    positive_status = z3_status(POSITIVE_K, N; finite_bound=true, label="positive")
    negative_status = z3_status(NEGATIVE_K, N; finite_bound=true, label="negative")
    no_finitude_status = z3_status(NEGATIVE_K, N; finite_bound=false, label="nofinitude")
    raised_bound_status = z3_status(NEGATIVE_K, RAISED_N; finite_bound=true, label="raised")
    solver_results = Dict{String,Any}(
        "positive_K4_into_N4" => Dict("solver" => "Z3.jl", "status" => positive_status, "expected" => "sat", "pass" => positive_status == "sat"),
        "negative_K5_into_N4" => Dict("solver" => "Z3.jl", "status" => negative_status, "expected" => "unsat", "pass" => negative_status == "unsat"),
        "no_finitude_K5_distinct_unbounded" => Dict("solver" => "Z3.jl", "status" => no_finitude_status, "expected" => "sat", "pass" => no_finitude_status == "sat"),
        "raised_bound_K5_into_N5" => Dict("solver" => "Z3.jl", "status" => raised_bound_status, "expected" => "sat", "pass" => raised_bound_status == "sat")
    )
    negative_controls = Dict{String,Any}(
        "K5_cannot_inject_into_N4" => Dict("pass" => negative_status == "unsat", "observed" => negative_status),
        "removing_finite_support_bound_makes_K5_sat" => Dict("pass" => no_finitude_status == "sat", "observed" => no_finitude_status),
        "raising_bound_to_N5_makes_K5_sat" => Dict("pass" => raised_bound_status == "sat", "observed" => raised_bound_status)
    )
    all_pass = all(Bool(v["pass"]) for v in values(solver_results)) && READS_PEER_RESULT == false
    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "backend" => "julia_z3_finite_injection",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "executable" => "/opt/homebrew/bin/julia --startup-file=no",
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "finite_support" => Dict("S" => SUPPORT, "N" => N, "predicate" => "admit(candidate) iff occupied support atoms inject into finite S"),
        "candidates" => Dict("positive" => Dict("K" => POSITIVE_K, "expected" => "sat_admitted"), "negative" => Dict("K" => NEGATIVE_K, "expected" => "unsat_excluded")),
        "solver_results" => solver_results,
        "negative_controls" => negative_controls,
        "support_observables" => local_support_observables(),
        "packages" => Dict(
            "load_bearing" => ["Z3"],
            "supportive" => ["JSON", "LinearAlgebra", "Dates"],
            "control_only" => String[],
            "missing_required" => String[]
        ),
        "package_observables" => Dict(
            "Z3" => "encoded finite injective map into S and produced SAT/UNSAT controls",
            "LinearAlgebra" => "supportive L1 support-mask size readout only",
            "JSON" => "supportive result serialization only"
        ),
        "TOOL_MANIFEST" => Dict(
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite injection SAT/UNSAT proof for F01 support predicate"),
            "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive finite support-mask observable"),
            "Julia JSON/Dates stdlib path support" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization and timestamp logic")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Z3" => "load_bearing", "Julia LinearAlgebra" => "supportive", "Julia JSON/Dates stdlib path support" => "supportive"),
        "all_pass" => all_pass,
        "claim_ceiling" => "R1 F01 scratch finite-object certificate only: tests one encoded finite support/admissibility predicate. Not full M(C), R2, formal, canonical, bridge, axis, physics, gravity, or entropy-master evidence."
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("SCOUT_DONE all_pass=", result["all_pass"], " positive=", result["solver_results"]["positive_K4_into_N4"]["status"], " negative=", result["solver_results"]["negative_K5_into_N4"]["status"], " no_finitude=", result["solver_results"]["no_finitude_K5_distinct_unbounded"]["status"], " raised_bound=", result["solver_results"]["raised_bound_K5_into_N5"]["status"], " reads_peer_result=", result["reads_peer_result"])
    return result["all_pass"] ? 0 : 2
end

exit(main())
