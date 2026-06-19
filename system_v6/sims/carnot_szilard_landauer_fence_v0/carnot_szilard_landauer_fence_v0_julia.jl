#!/usr/bin/env julia
# Julia exact Rational reference for carnot_szilard_landauer_fence_v0.

using Dates
using Graphs
using JSON3
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "carnot_szilard_landauer_fence_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false

rel(path::AbstractString) = relpath(path, ROOT)

function sha256_file(path::AbstractString)::String
    return bytes2hex(SHA.sha256(read(path)))
end

function frac_json(x::Rational{Int})
    return Dict("num" => numerator(x), "den" => denominator(x), "string" => "$(numerator(x))/$(denominator(x))")
end

function z3_bound_status(value::Rational{Int}, bound::Rational{Int}, relation::Symbol; include_constraint::Bool=true)::String
    solver = Z3.Solver()
    x_num = Z3.IntVar("julia_value_num")
    x_den = Z3.IntVar("julia_value_den")
    b_num = Z3.IntVar("julia_bound_num")
    b_den = Z3.IntVar("julia_bound_den")
    Z3.add(solver, x_num == Z3.IntVal(numerator(value)))
    Z3.add(solver, x_den == Z3.IntVal(denominator(value)))
    Z3.add(solver, b_num == Z3.IntVal(numerator(bound)))
    Z3.add(solver, b_den == Z3.IntVal(denominator(bound)))
    Z3.add(solver, x_den > Z3.IntVal(0))
    Z3.add(solver, b_den > Z3.IntVal(0))
    if include_constraint
        lhs = Z3.IntVar("julia_cross_lhs")
        rhs = Z3.IntVar("julia_cross_rhs")
        Z3.add(solver, lhs == Z3.IntVal(numerator(value) * denominator(bound)))
        Z3.add(solver, rhs == Z3.IntVal(numerator(bound) * denominator(value)))
        if relation == :le
            Z3.add(solver, Z3.Not(lhs > rhs))
        elseif relation == :ge
            Z3.add(solver, Z3.Not(lhs < rhs))
        elseif relation == :eq
            Z3.add(solver, lhs == rhs)
        else
            error("unsupported relation")
        end
    end
    return string(Z3.check(solver))
end

function z3_forbidden_status(value::Rational{Int}, bound::Rational{Int}, legal_relation::Symbol, forbidden_relation::Symbol)::String
    solver = Z3.Solver()
    x_num = Z3.IntVar("julia_value_num")
    x_den = Z3.IntVar("julia_value_den")
    b_num = Z3.IntVar("julia_bound_num")
    b_den = Z3.IntVar("julia_bound_den")
    Z3.add(solver, x_num == Z3.IntVal(numerator(value)))
    Z3.add(solver, x_den == Z3.IntVal(denominator(value)))
    Z3.add(solver, b_num == Z3.IntVal(numerator(bound)))
    Z3.add(solver, b_den == Z3.IntVal(denominator(bound)))
    Z3.add(solver, x_den > Z3.IntVal(0))
    Z3.add(solver, b_den > Z3.IntVal(0))
    lhs = Z3.IntVar("julia_cross_lhs")
    rhs = Z3.IntVar("julia_cross_rhs")
    Z3.add(solver, lhs == Z3.IntVal(numerator(value) * denominator(bound)))
    Z3.add(solver, rhs == Z3.IntVal(numerator(bound) * denominator(value)))
    if legal_relation == :le
        Z3.add(solver, Z3.Not(lhs > rhs))
    elseif legal_relation == :ge
        Z3.add(solver, Z3.Not(lhs < rhs))
    else
        error("unsupported legal relation")
    end
    if forbidden_relation == :gt
        Z3.add(solver, lhs > rhs)
    elseif forbidden_relation == :lt
        Z3.add(solver, lhs < rhs)
    else
        error("unsupported forbidden relation")
    end
    return string(Z3.check(solver))
end

function order_verdict(order::Vector{String})::Dict{String,Any}
    index = Dict(step => i for (i, step) in enumerate(order))
    graph = Graphs.SimpleDiGraph(3)
    for i in 1:(length(order)-1)
        Graphs.add_edge!(graph, i, i + 1)
    end
    measure_before_feedback = index["measure"] < index["feedback"]
    feedback_before_erase = index["feedback"] < index["erase"]
    path_measure_to_erase = Graphs.has_path(graph, index["measure"], index["erase"])
    legal = measure_before_feedback && feedback_before_erase && path_measure_to_erase
    return Dict(
        "order" => order,
        "measure_before_feedback" => measure_before_feedback,
        "feedback_before_erase" => feedback_before_erase,
        "path_measure_to_erase" => path_measure_to_erase,
        "verdict" => legal ? "sat" : "unsat",
    )
end

function build_result()
    mkpath(RESULT_DIR)
    t_h = 2//1
    t_c = 1//1
    eta_c = 1//1 - t_c // t_h
    admitted = Dict(
        "sub_carnot_eta_1_4" => Dict("eta" => 1//4, "bound" => eta_c, "status" => "sat"),
        "carnot_equality_boundary" => Dict("eta" => eta_c, "bound" => eta_c, "status" => "sat"),
        "paid_erasure_one_bit" => Dict("paid_ln2_coeff" => 1//1, "required_ln2_coeff" => 1//1, "status" => "sat"),
        "trivial_zero_work" => Dict("eta" => 0//1, "bound" => eta_c, "status" => "sat"),
    )
    excluded = Dict(
        "super_carnot_eta_3_4" => Dict("eta" => 3//4, "bound" => eta_c, "status" => "unsat"),
        "single_bath_positive_work" => Dict("eta" => 1//2, "bound" => 0//1, "status" => "unsat"),
        "below_landauer_half_paid" => Dict("paid_ln2_coeff" => 1//2, "required_ln2_coeff" => 1//1, "status" => "unsat"),
        "unpaid_erasure_surplus" => Dict("paid_ln2_coeff" => 0//1, "required_ln2_coeff" => 1//1, "status" => "unsat"),
    )
    proofs = Dict{String,Any}()
    for (name, row) in admitted
        if haskey(row, "eta")
            proofs[name] = Dict("julia_z3" => z3_bound_status(row["eta"], row["bound"], :le))
        else
            proofs[name] = Dict("julia_z3" => z3_bound_status(row["paid_ln2_coeff"], row["required_ln2_coeff"], :ge))
        end
    end
    proofs["super_carnot_eta_3_4"] = Dict("julia_z3" => z3_forbidden_status(3//4, eta_c, :le, :gt))
    proofs["single_bath_positive_work"] = Dict("julia_z3" => z3_forbidden_status(1//2, 0//1, :le, :gt))
    proofs["below_landauer_half_paid"] = Dict("julia_z3" => z3_forbidden_status(1//2, 1//1, :ge, :lt))
    proofs["unpaid_erasure_surplus"] = Dict("julia_z3" => z3_forbidden_status(0//1, 1//1, :ge, :lt))
    controls = Dict(
        "broken_fence_drop_carnot_constraint_super_carnot" => Dict(
            "julia_z3" => z3_bound_status(3//4, eta_c, :le, include_constraint=false),
            "expected" => "sat",
        ),
        "shuffled_ledger_order" => Dict(
            "normal" => order_verdict(["measure", "feedback", "erase"]),
            "shuffled" => order_verdict(["feedback", "measure", "erase"]),
            "n01_order_gap" => 1,
        ),
    )
    expected = Dict(
        "sub_carnot_eta_1_4" => "sat",
        "carnot_equality_boundary" => "sat",
        "paid_erasure_one_bit" => "sat",
        "trivial_zero_work" => "sat",
        "super_carnot_eta_3_4" => "unsat",
        "single_bath_positive_work" => "unsat",
        "below_landauer_half_paid" => "unsat",
        "unpaid_erasure_surplus" => "unsat",
    )
    proof_ok = all(proofs[name]["julia_z3"] == status for (name, status) in expected)
    control_ok = controls["broken_fence_drop_carnot_constraint_super_carnot"]["julia_z3"] == "sat" &&
        controls["shuffled_ledger_order"]["normal"]["verdict"] == "sat" &&
        controls["shuffled_ledger_order"]["shuffled"]["verdict"] == "unsat"
    exact_rows = Dict(
        "pinned_units" => Dict("k_B" => "1", "T_h" => frac_json(t_h), "T_c" => frac_json(t_c)),
        "computed" => Dict(
            "eta_C" => frac_json(eta_c),
            "szilard_single_bit_work" => Dict("unit" => "nats", "exact" => "ln(2)", "ln2_coeff" => frac_json(1//1)),
            "landauer_min_erasure_cost" => Dict("unit" => "nats", "exact" => "ln(2)", "ln2_coeff" => frac_json(1//1)),
            "typed_entropy_conversion" => Dict("bits" => frac_json(1//1), "nats_exact" => "ln(2)", "conversion" => "1 bit * ln(2) = ln(2) nats"),
        ),
        "rows" => Dict(
            "admitted" => Dict(name => merge(Dict(k => v isa Rational ? frac_json(v) : v for (k, v) in row), Dict("classification" => "classical_baseline")) for (name, row) in admitted),
            "excluded" => Dict(name => merge(Dict(k => v isa Rational ? frac_json(v) : v for (k, v) in row), Dict("classification" => "classical_baseline")) for (name, row) in excluded),
        ),
    )
    payload = Dict(
        "schema_version" => "three_engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "packages_used" => ["JSON3", "SHA", "Z3", "Graphs"],
        "aligned_packages_load_bearing" => ["Z3", "Graphs"],
        "package_versions" => Dict("julia" => string(VERSION), "project" => Base.active_project()),
        "all_pass" => proof_ok && control_ok,
        "exact_rows" => exact_rows,
        "proofs" => Dict("details" => proofs, "controls" => controls),
        "boundary_convention" => "closed reversible Carnot boundary admitted: eta <= eta_C, so eta = eta_C is SAT; only eta > eta_C is excluded",
        "typed_entropy_violations" => [],
        "TOOL_MANIFEST" => Dict(
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load_bearing Julia-side SMT check over computed exact Rational coefficients"),
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load_bearing order graph for shuffled-ledger N01 control"),
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Z3" => "load_bearing", "Graphs" => "load_bearing", "JSON3" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.IntVal/Z3.add/Z3.check",
                "input_object" => "computed exact Rational Carnot/Landauer coefficients",
                "output_object" => "SAT admitted rows, UNSAT forbidden rows, SAT broken-fence control",
                "positive_case" => "sub-Carnot/equality/paid/zero rows",
                "negative/erased_control" => "super-Carnot, single-bath positive work, below-Landauer, unpaid erasure",
                "boundary_case" => "eta = eta_C admitted",
                "demotion_condition" => "demote if Z3 rows are not bound to computed Rational values",
                "gates" => ["all_pass", "julia_reference"],
            ),
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.has_path",
                "input_object" => "finite measurement-feedback-erasure step order",
                "output_object" => "normal order SAT, shuffled order UNSAT",
                "positive_case" => "measure -> feedback -> erase",
                "negative/erased_control" => "feedback -> measure -> erase",
                "boundary_case" => "three finite steps",
                "demotion_condition" => "demote if order verdict is label-only",
                "gates" => ["N01_order_control"],
            ),
        ],
    )
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, payload)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    return payload
end

payload = build_result()
exit(payload["all_pass"] ? 0 : 1)
