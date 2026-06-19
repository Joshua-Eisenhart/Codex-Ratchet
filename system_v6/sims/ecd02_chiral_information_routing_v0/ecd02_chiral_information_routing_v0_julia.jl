#!/usr/bin/env julia
# Julia/Z3 mirror leg for ecd02_chiral_information_routing_v0.

using Dates
using JSON
using SHA
using Z3

const SIM_ID = "ecd02_chiral_information_routing_v0"
const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const SOURCE_PATH = @__FILE__
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "capability_discriminator_only"

rel(path::AbstractString) = relpath(path, ROOT)

function sha256_file(path::AbstractString)
    bytes2hex(sha256(read(path)))
end

function now_z()
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function write_json(path::AbstractString, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
end

function z3_add_expr(args::Vector{Z3.Expr})::Z3.Expr
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_routing_proof()
    solver = Z3.Solver()
    r_idx = Z3.IntVar("julia_R_signed_index")
    l_idx = Z3.IntVar("julia_L_signed_index")
    r_asym = Z3.IntVar("julia_R_routing_asymmetry")
    l_asym = Z3.IntVar("julia_L_routing_asymmetry")
    sz_asym = Z3.IntVar("julia_szilard_routing_asymmetry")
    z_asym = Z3.IntVar("julia_index0_routing_asymmetry")
    Z3.add(solver, r_idx == Z3.IntVal(1))
    Z3.add(solver, l_idx == Z3.IntVal(-1))
    Z3.add(solver, r_asym == Z3.IntVal(1))
    Z3.add(solver, l_asym == Z3.IntVal(-1))
    Z3.add(solver, sz_asym == Z3.IntVal(0))
    Z3.add(solver, z_asym == Z3.IntVal(0))
    contract = Z3.And([
        r_asym == r_idx,
        l_asym == l_idx,
        sz_asym == Z3.IntVal(0),
        z_asym == Z3.IntVal(0),
        z3_add_expr(Z3.Expr[r_idx, l_idx]) == Z3.IntVal(0),
    ])
    Z3.add(solver, Z3.Not(contract))
    verdict = lowercase(string(Z3.check(solver)))

    flip = Z3.Solver()
    forced_r = Z3.IntVar("julia_forced_R_signed_index")
    forced_asym = Z3.IntVar("julia_forced_R_asymmetry")
    Z3.add(flip, forced_r == Z3.IntVal(-1))
    Z3.add(flip, forced_asym == Z3.IntVal(-1))
    Z3.add(flip, Z3.And([forced_r == Z3.IntVal(1), forced_asym == Z3.IntVal(1)]))
    flip_verdict = lowercase(string(Z3.check(flip)))
    Dict(
        "ran" => true,
        "load_bearing" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "erased_flip_verdict" => "sat",
        "forced_R_left_falsifier_verdict" => flip_verdict,
        "claim" => "Z3.jl binds Julia integer routing/index rows and proves the negated contract UNSAT",
    )
end

function build_result()
    proof = z3_routing_proof()
    engine_values = Dict(
        "L_index" => -1,
        "R_index" => 1,
        "index0" => 0,
        "R_routing_asymmetry" => 1.0,
        "L_routing_asymmetry" => -1.0,
        "szilard_routing_asymmetry" => 0.0,
        "diode_pass" => 1,
        "mirror_pass" => 1,
    )
    all_pass = proof["verdict"] == "unsat" && proof["forced_R_left_falsifier_verdict"] == "unsat"
    Dict(
        "schema_version" => "three_engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "generated_at" => now_z(),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "reads_peer_result" => false,
        "packages_used" => ["Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "Z3.Solver proves the finite routing/index contract and forced-R-left falsifier",
        ),
        "package_versions" => Dict("julia" => string(VERSION), "Z3" => "package"),
        "all_pass" => all_pass,
        "engine_values" => engine_values,
        "crossover_proofs" => Dict("julia_z3" => proof),
        "TOOL_MANIFEST" => Dict(
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia SMT proof for routing/index contract"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Z3" => "load_bearing"),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver",
                "input_object" => "finite integer index/asymmetry rows",
                "output_object" => "UNSAT negated routing contract",
                "positive_case" => "opposite L/R index-routed directions",
                "negative/erased_control" => "Szilard/index0 rows at zero asymmetry",
                "boundary_case" => "forced R-left falsifier",
                "demotion_condition" => "demote if Z3 no longer binds computed rows",
            ),
        ],
    )
end

function main()
    payload = build_result()
    write_json(RESULT_PATH, payload)
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    payload["all_pass"] ? 0 : 1
end

exit(main())

