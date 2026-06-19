#!/usr/bin/env julia
# Julia leg for manifold_unified_run_v0.

using Dates
using JSON3
using Pkg
using QuantumOptics
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_ID = "manifold_unified_run_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const TRAJECTORY_ARTIFACT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_step_trajectory_artifact.json")
const TRAJECTORY_ARTIFACT_SHA_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_step_trajectory_artifact.sha256")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SCALE = 10^12
const TOL = 1.0e-8
const PACKAGES_USED = ["JSON3", "QuantumOptics", "Z3", "Dates", "SHA"]
const ALIGNED_PACKAGES_LOAD_BEARING = ["QuantumOptics", "Z3"]
const TOOL_MANIFEST = Dict(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing NLevelBasis/Ket/tensor/dm density trace on the same n=3 spinor sites"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-Z3 continuity identity with erased flip"),
    "JSON3/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization and hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict("QuantumOptics" => "load_bearing", "Z3" => "load_bearing", "JSON3/Dates/SHA" => "supportive")

rel(path::AbstractString)::String = replace(relpath(path, ROOT), "\\" => "/")
sha256_file(path::AbstractString)::String = bytes2hex(sha256(read(path)))
sha256_text(text::String)::String = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))
r12(x) = round(Float64(real(x)); digits=12)

function package_version(name::String)::String
    for (_, dep) in Pkg.dependencies()
        dep.name == name && return dep.version === nothing ? "unknown" : string(dep.version)
    end
    return "unknown"
end

function load_json(path::AbstractString)
    return JSON3.read(read(path, String), Dict{String,Any})
end

function load_verified_trajectory_artifact()
    isfile(TRAJECTORY_ARTIFACT_PATH) || error("missing trajectory artifact: $(TRAJECTORY_ARTIFACT_PATH)")
    isfile(TRAJECTORY_ARTIFACT_SHA_PATH) || error("missing trajectory artifact sha sidecar: $(TRAJECTORY_ARTIFACT_SHA_PATH)")
    expected = strip(read(TRAJECTORY_ARTIFACT_SHA_PATH, String))
    actual = sha256_file(TRAJECTORY_ARTIFACT_PATH)
    expected == actual || error("trajectory artifact hash mismatch: expected $(expected), got $(actual)")
    return load_json(TRAJECTORY_ARTIFACT_PATH), expected
end

function z3_add_terms(terms::Vector{Z3.Expr})
    isempty(terms) && return Z3.IntVal(0)
    length(terms) == 1 && return terms[1]
    return Z3.Expr(terms[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(terms[1]), length(terms), map(Z3.as_ast, terms)))
end

function z3_sub_terms(terms::Vector{Z3.Expr})
    length(terms) == 1 && return terms[1]
    return Z3.Expr(terms[1].ctx, Z3.Libz3.Z3_mk_sub(Z3.ctx_ref(terms[1]), length(terms), map(Z3.as_ast, terms)))
end

function z3_mul_terms(terms::Vector{Z3.Expr})
    length(terms) == 1 && return terms[1]
    return Z3.Expr(terms[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(terms[1]), length(terms), map(Z3.as_ast, terms)))
end

function z3_continuity(proof_row; erased::Bool=false)
    solver = Z3.Solver()
    current_terms = Dict{String,Z3.Expr}()
    for edge in proof_row["edge_formula_rows"]
        edge_id = String(edge["edge_id"])
        current = Z3.IntVar("j_current_$(edge_id)_scaled")
        coupling = Z3.IntVar("j_coupling_$(edge_id)_scaled")
        population_delta = Z3.IntVar("j_population_delta_$(edge_id)_scaled")
        residual = Z3.IntVar("j_rounding_residual_$(edge_id)_scaled2")
        Z3.add(solver, current == Z3.IntVal(Int(edge["current_src_to_dst_scaled"])))
        Z3.add(solver, coupling == Z3.IntVal(Int(edge["coupling_strength_scaled"])))
        Z3.add(solver, population_delta == Z3.IntVal(Int(edge["population_src_minus_dst_scaled"])))
        Z3.add(solver, residual == Z3.IntVal(Int(edge["rounding_residual_scaled2"])))
        lhs = z3_mul_terms(Z3.Expr[current, Z3.IntVal(SCALE)])
        rhs = z3_add_terms(Z3.Expr[z3_mul_terms(Z3.Expr[coupling, population_delta]), residual])
        Z3.add(solver, lhs == rhs)
        current_terms[edge_id] = current
    end
    site_id = String(proof_row["site_id"])
    balance = first(row for row in proof_row["site_balance_rows"] if String(row["site_id"]) == site_id)
    network = Z3.IntVar("j_network_$(site_id)_scaled")
    local_flow = Z3.IntVar("j_local_$(site_id)_scaled")
    divergence = Z3.IntVar("j_divergence_$(site_id)_scaled")
    outgoing = [current_terms[String(edge_id)] for edge_id in balance["outgoing_edge_ids"]]
    incoming = [current_terms[String(edge_id)] for edge_id in balance["incoming_edge_ids"]]
    derived = z3_sub_terms(Z3.Expr[z3_add_terms(outgoing), z3_add_terms(incoming)])
    Z3.add(solver, network == Z3.IntVal(Int(balance["network_population_flow_scaled"])))
    Z3.add(solver, local_flow == Z3.IntVal(Int(balance["local_population_flow_scaled"])))
    Z3.add(solver, divergence == Z3.IntVal(Int(balance["edge_divergence_scaled"])))
    Z3.add(solver, divergence == derived)
    rhs = z3_sub_terms(Z3.Expr[local_flow, divergence])
    erased && (rhs = z3_sub_terms(Z3.Expr[rhs, Z3.IntVal(1)]))
    Z3.add(solver, Z3.Not(network == rhs))
    return string(Z3.check(solver))
end

function site_ket(site, basis)
    left = complex(Float64(site["psi_L"][1]), Float64(site["psi_L"][2]))
    right = complex(Float64(site["psi_R"][1]), Float64(site["psi_R"][2]))
    return Ket(basis, ComplexF64[left, right])
end

function quantumoptics_receipt(sites)
    basis = NLevelBasis(2)
    ket = tensor(site_ket(sites[1], basis), site_ket(sites[2], basis), site_ket(sites[3], basis))
    rho = dm(ket)
    trace_value = tr(rho)
    return Dict(
        "tool" => "QuantumOptics.NLevelBasis/Ket/tensor/dm",
        "site_count" => length(sites),
        "density_trace" => r12(trace_value),
        "pass" => abs(real(trace_value) - 1.0) <= TOL,
    )
end

function main()
    mkpath(RESULT_DIR)
    artifact, artifact_sha = load_verified_trajectory_artifact()
    step3 = artifact["trajectory"]["steps"][4]
    proof_row = step3["flux_continuity"]["proof_row"]
    q_receipt = quantumoptics_receipt(artifact["engine_inputs"]["julia_quantum_sites"])
    z3_verdict = z3_continuity(proof_row)
    erased = z3_continuity(proof_row; erased=true)
    payload = Dict(
        "schema_version" => "$(SIM_ID)_$(ENGINE)_leg_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "classification" => CLASSIFICATION,
        "ceiling" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "mode" => "RATCHETED",
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "trajectory_artifact" => Dict(
            "artifact_path" => rel(TRAJECTORY_ARTIFACT_PATH),
            "artifact_sha_path" => rel(TRAJECTORY_ARTIFACT_SHA_PATH),
            "artifact_file_sha256" => sha256_file(TRAJECTORY_ARTIFACT_PATH),
            "verified_file_sha256" => artifact_sha,
            "content_sha256" => artifact["content_sha256"],
            "verified" => true,
        ),
        "packages_used" => PACKAGES_USED,
        "aligned_packages_load_bearing" => ALIGNED_PACKAGES_LOAD_BEARING,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "package_versions" => Dict(
            "QuantumOptics" => package_version("QuantumOptics"),
            "Z3" => package_version("Z3"),
            "JSON3" => package_version("JSON3"),
        ),
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "engine_values" => Dict("conditioned_total_abs_current" => step3["s5_s6_terrain_flow"]["observables"]["total_abs_current"]),
        "quantumoptics_receipt" => q_receipt,
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => lowercase(z3_verdict),
                "erased_flip_verdict" => lowercase(erased),
                "formula_terms_bound" => true,
                "edge_current_terms_in_solver" => true,
                "divergence_derived_in_solver" => true,
                "proof_row" => proof_row,
            ),
        ),
        "tool_calls" => [
            Dict(
                "tool" => "QuantumOptics",
                "qualified_api/function" => "QuantumOptics.NLevelBasis/Ket/tensor/dm",
                "input_object" => "same n=3 committed site spinors",
                "output_object" => "density trace",
                "positive_case" => "trace equals 1",
                "negative/erased_control" => "not a proof engine",
                "boundary_case" => "three two-level sites",
                "demotion_condition" => "demote if source omits QuantumOptics API calls",
                "gates" => ["julia_density_trace"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "step3 edge-current rows and site-balance rows",
                "output_object" => "continuity UNSAT and erased SAT",
                "positive_case" => "negated continuity identity is UNSAT",
                "negative/erased_control" => "erased target flips SAT",
                "boundary_case" => "integer-scaled rows",
                "demotion_condition" => "demote if solver is fed a precomputed boolean",
                "gates" => ["julia_z3_cross_layer_identity"],
            ),
        ],
        "all_pass" => q_receipt["pass"] && lowercase(z3_verdict) == "unsat" && lowercase(erased) == "sat",
    )
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, payload)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
