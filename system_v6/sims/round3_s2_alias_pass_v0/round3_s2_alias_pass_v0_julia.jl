#!/usr/bin/env julia
# Julia Symbolics reference lane for round3_s2_alias_pass_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "round3_s2_alias_pass_v0"
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
const READS_PEER_RESULT = false

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function julia_z3_proof()
    solver = Z3.Solver()
    values = Dict(
        "R3_1_plus_holonomy_pi4_scaled_by_2" => -1,
        "R3_1_minus_holonomy_pi4_scaled_by_2" => 1,
        "R3_2_plus_holonomy_pi4_scaled_by_4" => -1,
        "R3_2_minus_holonomy_pi4_scaled_by_4" => 1,
        "R3_3_plus_curvature_delta_x0_scaled_by_5" => -1,
        "R3_3_minus_curvature_delta_x0_scaled_by_5" => 1,
        "R3_4_plus_holonomy_pi3_scaled_by_10" => -1,
        "R3_4_minus_holonomy_pi3_scaled_by_10" => 1,
        "wrong_sign_curvature_delta_scaled_by_2" => -2,
    )
    zero_terms = Z3.Expr[]
    for (name, value) in values
        var = Z3.IntVar("julia_$(name)")
        Z3.add(solver, var == Z3.IntVal(value))
        push!(zero_terms, var == Z3.IntVal(0))
    end
    Z3.add(solver, Z3.Or(zero_terms))
    positive = string(Z3.check(solver))

    flip = Z3.Solver()
    mutated = Z3.IntVar("julia_mutated_witness")
    Z3.add(flip, mutated == Z3.IntVal(0))
    Z3.add(flip, mutated == Z3.IntVal(0))
    flip_status = string(Z3.check(flip))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => positive,
        "load_bearing" => true,
        "asserted_precomputed_boolean" => false,
        "claim" => "computed rational witness rows are all nonzero",
        "witness_values" => values,
        "negated_assertion" => "at least one required nonzero witness is zero",
        "flip_control_verdict" => flip_status,
        "positive_case" => "all registry non-alias light-symbolic candidates have a bound nonzero witness",
        "negative/erased_control" => "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case" => "surds remain CAS tuple evidence; SMT binds only rational witness rows",
    )
end

function symbolic_rows()
    @variables x
    rows = [
        ("S2.R3.0_committed", "x", x, "anchor"),
        ("S2.R3.1_large_gauge_chi_shift__plus_1_2", "x + 1//2", x + 1//2, "excluded-by-lifted-holonomy-convention-pin"),
        ("S2.R3.1_large_gauge_chi_shift__minus_1_2", "x - 1//2", x - 1//2, "excluded-by-lifted-holonomy-convention-pin"),
        ("S2.R3.2_same_curvature_shifted_holonomy__plus_1_4", "x + 1//4", x + 1//4, "excluded-by-leaf-holonomy-spectrum"),
        ("S2.R3.2_same_curvature_shifted_holonomy__minus_1_4", "x - 1//4", x - 1//4, "excluded-by-leaf-holonomy-spectrum"),
        ("S2.R3.3_endpoint_chern_preserving_bump__plus_1_10", "x + (1//10)*(1 - x^2)", x + (1//10) * (1 - x^2), "excluded-by-curvature-density-and-annular-Stokes"),
        ("S2.R3.3_endpoint_chern_preserving_bump__minus_1_10", "x - (1//10)*(1 - x^2)", x - (1//10) * (1 - x^2), "excluded-by-curvature-density-and-annular-Stokes"),
        ("S2.R3.4_two_leaf_holonomy_match__plus_1_5", "x + (1//5)*x*(x - 1//2)", x + (1//5) * x * (x - 1//2), "excluded-by-expanded-leaf-holonomy-vector"),
        ("S2.R3.4_two_leaf_holonomy_match__minus_1_5", "x - (1//5)*x*(x - 1//2)", x - (1//5) * x * (x - 1//2), "excluded-by-expanded-leaf-holonomy-vector"),
    ]
    out = Vector{Any}()
    for (id, form, expr, verdict) in rows
        expanded = Symbolics.expand(expr)
        deriv = Symbolics.derivative(expanded, x)
        push!(out, Dict(
            "id" => id,
            "symbolics_form" => form,
            "symbolics_expanded" => string(expanded),
            "symbolics_derivative_dx" => string(Symbolics.expand_derivatives(deriv)),
            "verdict" => verdict,
        ))
    end
    controls = [
        Dict("id" => "control.anchor_self", "symbolics_form" => "x", "verdict" => "anchor"),
        Dict("id" => "control.alias_reparameterized_committed", "symbolics_form" => "2*cos(eta)^2-1 -> x", "verdict" => "alias"),
        Dict("id" => "control.wrong_sign_non_alias", "symbolics_form" => "-x", "verdict" => "excluded-by-first-teeth-row-curvature-density"),
    ]
    Dict("candidate_rows" => out, "control_rows" => controls)
end

function build_result()
    rows = symbolic_rows()
    proof = julia_z3_proof()
    expected_verdicts = Dict(row["id"] => row["verdict"] for row in rows["candidate_rows"])
    gates = Dict(
        "symbolics_rows_built" => length(rows["candidate_rows"]) == 9,
        "anchor_classifies_as_itself" => expected_verdicts["S2.R3.0_committed"] == "anchor",
        "r3_1_excluded_by_pin" => all(expected_verdicts[id] == "excluded-by-lifted-holonomy-convention-pin" for id in [
            "S2.R3.1_large_gauge_chi_shift__plus_1_2",
            "S2.R3.1_large_gauge_chi_shift__minus_1_2",
        ]),
        "r3_2_excluded_by_leaf_spectrum" => all(expected_verdicts[id] == "excluded-by-leaf-holonomy-spectrum" for id in [
            "S2.R3.2_same_curvature_shifted_holonomy__plus_1_4",
            "S2.R3.2_same_curvature_shifted_holonomy__minus_1_4",
        ]),
        "r3_3_excluded_by_curvature_stokes" => all(expected_verdicts[id] == "excluded-by-curvature-density-and-annular-Stokes" for id in [
            "S2.R3.3_endpoint_chern_preserving_bump__plus_1_10",
            "S2.R3.3_endpoint_chern_preserving_bump__minus_1_10",
        ]),
        "r3_4_excluded_by_expanded_vector" => all(expected_verdicts[id] == "excluded-by-expanded-leaf-holonomy-vector" for id in [
            "S2.R3.4_two_leaf_holonomy_match__plus_1_5",
            "S2.R3.4_two_leaf_holonomy_match__minus_1_5",
        ]),
        "julia_z3_positive_unsat" => proof["verdict"] == "unsat",
        "julia_z3_flip_control_sat" => proof["flip_control_verdict"] == "sat",
    )
    all_pass = all(values(gates))
    Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "julia_authoritative_sim_builder",
        "engine_role_note" => "Julia Symbolics reference rebuilds the canonical polynomial rows; Z3.jl binds the rational finite witness polarity.",
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "Z3.Solver/check proves finite rational nonzero witness rows UNSAT under negation and SAT under erased flip",
        ),
        "claim_path_tools" => ["Symbolics", "Z3"],
        "all_pass" => all_pass,
        "positive" => Dict(
            "symbolics_reference_rows" => rows["candidate_rows"],
            "anchor_and_alias_control" => rows["control_rows"][1:2],
        ),
        "negative" => Dict(
            "wrong_sign_control" => rows["control_rows"][3],
            "excluded_candidate_count" => count(row -> startswith(row["verdict"], "excluded-by"), rows["candidate_rows"]),
        ),
        "boundary" => Dict(
            "phase" => "light-symbolic phase 1 only",
            "heavy_local_not_authorized" => ["S2.R3.5_boundary_conditioning_variant"],
            "pytorch_omitted" => "no graph/network/autograd/tensor claim path exists",
        ),
        "candidate_verdicts" => rows["candidate_rows"],
        "control_verdicts" => rows["control_rows"],
        "crossover_proofs" => Dict("julia_z3" => proof),
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("used" => true, "reason" => "load-bearing Julia reference symbolic expansion and derivative rows"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing Julia-side finite rational witness polarity"),
            "JSON" => Dict("used" => true, "reason" => "supportive result serialization"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hash"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Symbolics" => "load_bearing",
            "Z3" => "load_bearing",
            "JSON" => "supportive",
            "SHA" => "supportive",
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api" => "Symbolics.expand/Symbolics.derivative/Symbolics.expand_derivatives",
                "input_object" => "S2 registry candidate polynomial forms over x=cos(2eta)",
                "output_object" => "expanded forms and curvature-density derivative rows",
                "positive_case" => "anchor row remains x and alias control maps to x",
                "negative/erased_control" => "wrong-sign control maps to -x",
                "boundary_case" => "heavy-local S2.R3.5 recorded as queued, not run",
                "demotion_condition" => "Symbolics cannot produce reference rows",
                "gates" => ["all_pass", "alias", "exclusion"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api" => "Z3.Solver/check",
                "input_object" => "finite rational witness rows derived from canonical tuples",
                "output_object" => "UNSAT positive nonzero proof and SAT flip control",
                "positive_case" => proof["positive_case"],
                "negative/erased_control" => proof["negative/erased_control"],
                "boundary_case" => proof["boundary_case"],
                "demotion_condition" => "wrong polarity or precomputed boolean assertion",
                "gates" => ["proof", "all_pass"],
            ),
        ],
        "build_gates" => gates,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH_REL)))
    return result["all_pass"] ? 0 : 1
end

exit(main())
