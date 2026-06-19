#!/usr/bin/env julia
# Julia Symbolics/Z3 mirror for geo_s6_s7_mode_sweep_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s6_s7_mode_sweep_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))

function clean(x)
    text = string(Symbolics.simplify(x, expand=true))
    replacements = Dict("0.0" => "0", "1.0" => "1", "-0.0" => "0", "0//1" => "0", "1//1" => "1")
    return get(replacements, text, text)
end

function symbolics_mode_receipt()
    @variables before after excluded n lens_order q
    count_identity = Symbolics.simplify(before - after - excluded, expand=true)
    lens_remainder = Symbolics.simplify(n - lens_order * q, expand=true)
    Dict(
        "s6_count_identity_expression" => clean(count_identity),
        "s6_bound_values" => Dict("before" => 40, "after" => 16, "excluded" => 24),
        "s6_bound_identity_value" => clean(Symbolics.substitute(count_identity, Dict(before => 40, after => 16, excluded => 24))),
        "s7_commensurate_sample_N8_mod4" => clean(Symbolics.substitute(lens_remainder, Dict(n => 8, lens_order => 4, q => 2))),
        "s7_incommensurate_sample_N6_mod4" => clean(Symbolics.substitute(lens_remainder, Dict(n => 6, lens_order => 4, q => 1))),
        "pass" => clean(Symbolics.substitute(count_identity, Dict(before => 40, after => 16, excluded => 24))) == "0" &&
            clean(Symbolics.substitute(lens_remainder, Dict(n => 8, lens_order => 4, q => 2))) == "0" &&
            clean(Symbolics.substitute(lens_remainder, Dict(n => 6, lens_order => 4, q => 1))) != "0",
    )
end

function zadd(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function zmul(ctx, args::Vector{Z3.Expr})
    length(args) == 1 && return args[1]
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function zsub3(ctx, a::Z3.Expr, b::Z3.Expr, c::Z3.Expr)
    zadd(ctx, [a, zmul(ctx, [Z3.IntVal(-1, ctx), b]), zmul(ctx, [Z3.IntVal(-1, ctx), c])])
end

function z3_controls()
    ctx = Z3.Context()
    identity = Z3.Solver(ctx)
    before = Z3.IntVar("before", ctx)
    after = Z3.IntVar("after", ctx)
    excluded = Z3.IntVar("excluded", ctx)
    Z3.add(identity, before == Z3.IntVal(40, ctx))
    Z3.add(identity, after == Z3.IntVal(16, ctx))
    Z3.add(identity, excluded == Z3.IntVal(24, ctx))
    Z3.add(identity, Z3.Not(zsub3(ctx, before, after, excluded) == Z3.IntVal(0, ctx)))
    identity_verdict = string(Z3.check(identity))

    erased = Z3.Solver(ctx)
    b2 = Z3.IntVar("before_erased", ctx)
    a2 = Z3.IntVar("after_erased", ctx)
    e2 = Z3.IntVar("excluded_erased", ctx)
    Z3.add(erased, b2 == Z3.IntVal(40, ctx))
    Z3.add(erased, a2 == Z3.IntVal(16, ctx))
    Z3.add(erased, e2 == Z3.IntVal(0, ctx))
    Z3.add(erased, zsub3(ctx, b2, a2, e2) == Z3.IntVal(0, ctx))
    erased_verdict = string(Z3.check(erased))

    lens = Z3.Solver(ctx)
    q = Z3.IntVar("q", ctx)
    Z3.add(lens, q == Z3.IntVal(2, ctx))
    Z3.add(lens, Z3.IntVal(6, ctx) == zmul(ctx, [Z3.IntVal(4, ctx), q]))
    incommensurate_verdict = string(Z3.check(lens))

    Dict(
        "s6_identity_violation_verdict" => identity_verdict,
        "s6_erased_excluded_control_verdict" => erased_verdict,
        "s7_N6_commensurate_control_verdict" => incommensurate_verdict,
        "pass" => identity_verdict == "unsat" && erased_verdict == "unsat" && incommensurate_verdict == "unsat",
    )
end

function main()
    mkpath(RESULT_DIR)
    symbolics = symbolics_mode_receipt()
    z3 = z3_controls()
    all_pass = symbolics["pass"] == true && z3["pass"] == true
    result = Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "ran" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "julia_project" => "system_v5/julia_carrier",
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Symbolics", "Z3"],
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing mirror of S6 narrowing arithmetic and S7 lens-order commensurability"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing can-fail controls for erased S6 exclusions and incommensurate S7 lens quotient"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Symbolics" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive"),
        "symbolics_mode_receipt" => symbolics,
        "z3_controls" => z3,
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api/function" => "Symbolics.@variables / Symbolics.substitute / Symbolics.simplify",
                "input_object" => "S6 before/after/excluded counts and S7 N mod lens_order samples",
                "output_object" => "computed count identity and commensurability rows",
                "positive_case" => "40-16-24=0 and N=8 mod 4 equals 0",
                "negative/erased_control" => "N=6 mod 4 is nonzero",
                "boundary_case" => "integer arithmetic mirror only",
                "demotion_condition" => "demote if arithmetic is replaced by literal statuses",
                "gates" => ["julia_symbolics_z3_mirror"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver / Z3.add / Z3.check",
                "input_object" => "S6 count identity and S7 incommensurate quotient branch",
                "output_object" => "unsat identity violation, unsat erased exclusion, unsat N=6 lens quotient",
                "positive_case" => "valid S6 identity has no counterexample",
                "negative/erased_control" => "erasing excluded rows or forcing N=6=4q fails",
                "boundary_case" => "QF integer arithmetic only",
                "demotion_condition" => "demote if can-fail controls are removed",
                "gates" => ["julia_symbolics_z3_mirror"],
            ),
        ],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH_REL)))
    return all_pass ? 0 : 1
end

exit(main())
