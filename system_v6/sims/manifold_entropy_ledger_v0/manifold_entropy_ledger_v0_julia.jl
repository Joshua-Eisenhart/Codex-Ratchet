#!/usr/bin/env julia

using JSON
using Manifolds
using SHA
using Z3

const SIM_ID = "manifold_entropy_ledger_v0"
const ROOT = normpath(joinpath(abspath(@__DIR__), "..", "..", ".."))
const RESULT = joinpath(ROOT, "system_v6", "sims", SIM_ID, "results", "$(SIM_ID)_julia_results.json")
const SOURCE = joinpath(ROOT, "system_v6", "sims", SIM_ID, "$(SIM_ID)_julia.jl")

function rel(path::AbstractString)
    normalized = normpath(abspath(path))
    prefix = endswith(ROOT, "/") ? ROOT : ROOT * "/"
    return startswith(normalized, prefix) ? normalized[length(prefix)+1:end] : normalized
end

function sha256_file(path::AbstractString)
    return bytes2hex(SHA.sha256(read(path)))
end

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_chain()
    coeffs = Dict(
        "h_s3" => [0, 1, 2],
        "h_eta" => [1, -1, 0],
        "expected_conditional" => [-1, 2, 2],
    )
    solver = Z3.Solver()
    violations = Z3.Expr[]
    for idx in 1:3
        j = Z3.IntVar("j_$idx")
        m = Z3.IntVar("m_$idx")
        c = Z3.IntVar("c_$idx")
        Z3.add(solver, j == Z3.IntVal(coeffs["h_s3"][idx]))
        Z3.add(solver, m == Z3.IntVal(coeffs["h_eta"][idx]))
        Z3.add(solver, c == Z3.IntVal(coeffs["expected_conditional"][idx]))
        push!(violations, Z3.Not(j == z3_add(Z3.Expr[m, c])))
    end
    Z3.add(solver, Z3.Or(violations))
    positive = string(Z3.check(solver))

    erased = Z3.Solver()
    erased_terms = Z3.Expr[]
    for idx in 1:3
        j = Z3.IntVar("ej_$idx")
        m = Z3.IntVar("em_$idx")
        Z3.add(erased, j == Z3.IntVal(coeffs["h_s3"][idx]))
        Z3.add(erased, m == Z3.IntVal(coeffs["h_eta"][idx]))
        push!(erased_terms, j == m)
    end
    Z3.add(erased, Z3.And(erased_terms))
    erased_status = string(Z3.check(erased))
    return Dict(
        "ran" => true,
        "load_bearing" => true,
        "verdict" => positive,
        "erased_conditional_control_verdict" => erased_status,
        "erased_flip_control_can_fail" => erased_status == "unsat",
    )
end

function main()
    pi = Base.MathConstants.pi
    s3 = Manifolds.Sphere(3)
    s3_volume = Manifolds.manifold_volume(s3)
    h_s3 = log(s3_volume)
    h_eta = 1 - log(2)
    expected_conditional = log(4 * pi^2) - 1
    chain_defect = h_s3 - h_eta - expected_conditional
    leaf_pi6 = log(sqrt(3) * pi^2)
    z3_row = z3_chain()

    payload = Dict(
        "schema_version" => "$(SIM_ID)_julia_leg_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "source_path" => rel(SOURCE),
        "source_sha256" => sha256_file(SOURCE),
        "result_path" => rel(RESULT),
        "julia_project" => Base.active_project(),
        "reads_peer_result" => false,
        "packages_used" => ["JSON", "Manifolds", "Z3"],
        "aligned_packages_load_bearing" => ["Manifolds", "Z3"],
        "log_base" => "e",
        "seed" => Dict("stochastic" => false, "deterministic_symbolic_seed" => "$(SIM_ID):julia:manifolds:z3:v1"),
        "ledger" => Dict(
            "round_s3" => Dict(
                "api" => "Manifolds.manifold_volume(Sphere(3))",
                "volume" => s3_volume,
                "entropy_exact" => "log(2*pi^2)",
                "entropy_float" => h_s3,
            ),
            "eta_marginal" => Dict(
                "density" => "sin(2*eta)",
                "entropy_exact" => "1 - log(2)",
                "entropy_float" => h_eta,
            ),
            "conditional_expectation" => Dict(
                "value_exact" => "-1 + log(4*pi^2)",
                "value_float" => expected_conditional,
            ),
            "chain_rule_check" => Dict(
                "identity" => "h(S^3)=h(eta)+E[h(T_eta)]",
                "defect_float" => chain_defect,
                "pass" => abs(chain_defect) < 1e-12,
            ),
            "cross_layer_meeting_point" => Dict(
                "leaf" => "T_pi/6",
                "measure_entropy_exact" => "log(sqrt(3)*pi^2)",
                "measure_entropy_float" => leaf_pi6,
                "carrier_vn_anchor" => "cited by envelope from lifted ladder parents; not recomputed in Julia leg",
            ),
        ),
        "crossover_proofs" => Dict("julia_z3" => z3_row),
        "capability_receipts" => Dict(
            "active_project" => Base.active_project(),
            "Manifolds.Sphere" => string(s3),
            "Z3.Solver" => "imported_and_checked",
        ),
        "TOOL_MANIFEST" => Dict(
            "Manifolds" => Dict("used" => true, "reason" => "load-bearing S3 volume through manifold_volume"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing coefficient identity control"),
            "JSON" => Dict("used" => true, "reason" => "structured result write"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Manifolds" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive"),
        "claim_path_tools" => ["Manifolds", "Z3", "JSON"],
        "tool_calls" => [
            Dict(
                "tool" => "Manifolds",
                "qualified_api/function" => "Manifolds.Sphere / Manifolds.manifold_volume",
                "input_object" => "round Sphere(3)",
                "output_object" => "S3 volume and h(S3)",
                "positive_case" => "volume matches 2*pi^2",
                "negative/erased_control" => "not used as a solver control",
                "boundary_case" => "round unit S3 only",
                "demotion_condition" => "demote if replaced by a literal without API call",
                "gates" => ["round_s3_entropy"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver / Z3.add / Z3.check",
                "input_object" => "coefficient vectors over [1, log(2), log(pi)]",
                "output_object" => "unsat chain identity counterexample",
                "positive_case" => "chain identity has no coefficient mismatch",
                "negative/erased_control" => "erased conditional term is unsat",
                "boundary_case" => "linear integer coefficients",
                "demotion_condition" => "demote if controls do not fail",
                "gates" => ["julia_z3_chain_identity"],
            ),
            Dict(
                "tool" => "JSON",
                "qualified_api/function" => "JSON.print",
                "input_object" => "Julia result payload",
                "output_object" => "packet-local JSON",
                "positive_case" => "structured rows emitted",
                "negative/erased_control" => "not a proof engine",
                "boundary_case" => "result serialization",
                "demotion_condition" => "demote if result is not structured",
                "gates" => ["structured_payload"],
            ),
        ],
        "all_pass" => abs(chain_defect) < 1e-12 && z3_row["verdict"] == "unsat" && z3_row["erased_flip_control_can_fail"],
    )
    mkpath(dirname(RESULT))
    open(RESULT, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT))))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
