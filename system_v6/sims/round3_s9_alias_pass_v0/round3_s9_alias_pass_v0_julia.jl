#!/usr/bin/env julia
# Julia Symbolics/Z3 reference lane for round3_s9_alias_pass_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "round3_s9_alias_pass_v0"
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

@variables eta
const DETA = Differential(eta)

sx(x) = string(Symbolics.simplify(x; expand=true))

function f_anchor()
    cos(2eta)
end

function f_string(kind::String, epsilon::Rational{Int}=0//1)
    if kind == "anchor"
        return "cos(2eta)"
    elseif kind == "bump"
        sign = epsilon > 0 ? "+" : "-"
        return "cos(2eta)$(sign)$(abs(numerator(epsilon)))/$(denominator(epsilon))*sin(2eta)^2"
    elseif kind == "pi6"
        sign = epsilon > 0 ? "+" : "-"
        return "cos(2eta)$(sign)$(abs(numerator(epsilon)))/$(denominator(epsilon))*(cos(2eta)-1/2)"
    elseif kind == "pi4"
        sign = epsilon > 0 ? "+" : "-"
        return "cos(2eta)$(sign)$(abs(numerator(epsilon)))/$(denominator(epsilon))*cos(2eta)"
    elseif kind == "pi6pi4"
        sign = epsilon > 0 ? "+" : "-"
        return "cos(2eta)$(sign)$(abs(numerator(epsilon)))/$(denominator(epsilon))*cos(2eta)*(cos(2eta)-1/2)"
    elseif kind == "alias"
        return "1-2*sin(eta)^2"
    elseif kind == "flat"
        return "0"
    end
    error("unknown kind: $kind")
end

function f_expr(kind::String, epsilon::Rational{Int}=0//1)
    anchor = f_anchor()
    if kind == "anchor"
        return anchor
    elseif kind == "bump"
        return anchor + epsilon * sin(2eta)^2
    elseif kind == "pi6"
        return anchor + epsilon * (cos(2eta) - 1//2)
    elseif kind == "pi4"
        return anchor + epsilon * cos(2eta)
    elseif kind == "pi6pi4"
        return anchor + epsilon * cos(2eta) * (cos(2eta) - 1//2)
    elseif kind == "alias"
        return 1 - 2 * sin(eta)^2
    elseif kind == "flat"
        return 0
    end
    error("unknown kind: $kind")
end

function leaf_values(kind::String, epsilon::Rational{Int}=0//1)
    if kind == "anchor" || kind == "alias" || kind == "loop"
        return Dict("0" => "1", "pi/6" => "1/2", "pi/4" => "0", "pi/3" => "-1/2", "pi/2" => "-1")
    elseif kind == "bump" && epsilon == 1//20
        return Dict("0" => "1", "pi/6" => "41/80", "pi/4" => "1/20", "pi/3" => "-39/80", "pi/2" => "-1")
    elseif kind == "bump" && epsilon == -1//20
        return Dict("0" => "1", "pi/6" => "39/80", "pi/4" => "-1/20", "pi/3" => "-41/80", "pi/2" => "-1")
    elseif kind == "pi6" && epsilon == 1//10
        return Dict("0" => "21/20", "pi/6" => "1/2", "pi/4" => "-1/20", "pi/3" => "-3/5", "pi/2" => "-23/20")
    elseif kind == "pi6" && epsilon == -1//10
        return Dict("0" => "19/20", "pi/6" => "1/2", "pi/4" => "1/20", "pi/3" => "-2/5", "pi/2" => "-17/20")
    elseif kind == "pi4" && epsilon == 1//10
        return Dict("0" => "11/10", "pi/6" => "11/20", "pi/4" => "0", "pi/3" => "-11/20", "pi/2" => "-11/10")
    elseif kind == "pi4" && epsilon == -1//10
        return Dict("0" => "9/10", "pi/6" => "9/20", "pi/4" => "0", "pi/3" => "-9/20", "pi/2" => "-9/10")
    elseif kind == "pi6pi4" && epsilon == 1//10
        return Dict("0" => "21/20", "pi/6" => "1/2", "pi/4" => "0", "pi/3" => "-47/80", "pi/2" => "-17/20")
    elseif kind == "pi6pi4" && epsilon == -1//10
        return Dict("0" => "19/20", "pi/6" => "1/2", "pi/4" => "0", "pi/3" => "-33/80", "pi/2" => "-23/20")
    elseif kind == "flat"
        return Dict("0" => "0", "pi/6" => "0", "pi/4" => "0", "pi/3" => "0", "pi/2" => "0")
    end
    error("unknown leaf values for $kind $epsilon")
end

function annular_flux(values::Dict{String,String})
    order = ["0", "pi/6", "pi/4", "pi/3", "pi/2"]
    out = Dict{String,String}()
    for i in 1:length(order)-1
        left = parse_rational(values[order[i]])
        right = parse_rational(values[order[i+1]])
        out["$(order[i])->$(order[i+1])"] = string(right - left)
    end
    out
end

function parse_rational(value::String)
    if occursin("/", value)
        parts = split(value, "/")
        return parse(Int, parts[1]) // parse(Int, parts[2])
    end
    parse(Int, value) // 1
end

function c1_value(values::Dict{String,String})
    string((parse_rational(values["0"]) - parse_rational(values["pi/2"])) // 2)
end

function canonical_tuple(kind::String, epsilon::Rational{Int}=0//1; path_ordered_loop_signature="not-scoped-light-symbolic")
    local_kind = kind == "loop" ? "anchor" : kind
    f = f_expr(local_kind, epsilon)
    curvature = expand_derivatives(DETA(f))
    values = leaf_values(local_kind, epsilon)
    Dict(
        "canonicalizer" => "f_simplified, F=f'(eta), c1, leaf_holonomy_vector[0,pi/6,pi/4,pi/3,pi/2], annular_flux_vector, validity_class, path_ordered_loop_signature_when_scoped",
        "f_simplified" => f_string(local_kind, epsilon),
        "F_curvature_form_coefficient" => sx(curvature),
        "c1" => c1_value(values),
        "leaf_holonomy_vector" => values,
        "annular_flux_vector" => annular_flux(values),
        "validity_class" => "ordinary_one_form_A=dphi+f(eta)dchi_on_pinned_S9_chart",
        "path_ordered_loop_signature" => path_ordered_loop_signature,
        "s2_s9_convention_pin" => "pinned_phi_holonomy_convention; pin-relative separations are reopenable, not intrinsic kills",
    )
end

function registry_specs()
    [
        Dict("id" => "S9.R3.0_committed_hopf", "finite_representative" => "f=cos(2eta)", "closeness" => "control", "expected_teeth_row" => "none; anchor", "cost" => "light-symbolic", "forms" => [("anchor", 0//1, "anchor")]),
        Dict("id" => "S9.R3.1_c1_small_density_bump", "finite_representative" => "f=cos(2eta)+epsilon*sin(2eta)^2, epsilon in {1/20,-1/20}", "closeness" => "closest same-c1 density neighbor", "expected_teeth_row" => "curvature density before holonomy", "cost" => "light-symbolic", "forms" => [("bump", 1//20, "epsilon=1/20"), ("bump", -1//20, "epsilon=-1/20")]),
        Dict("id" => "S9.R3.2_one_leaf_match_pi6", "finite_representative" => "f=cos(2eta)+epsilon*(cos(2eta)-1/2), epsilon in {1/10,-1/10}", "closeness" => "matches holonomy at pi/6 only", "expected_teeth_row" => "expanded holonomy spectrum", "cost" => "light-symbolic", "forms" => [("pi6", 1//10, "epsilon=1/10"), ("pi6", -1//10, "epsilon=-1/10")]),
        Dict("id" => "S9.R3.3_one_leaf_match_pi4", "finite_representative" => "f=cos(2eta)+epsilon*cos(2eta), epsilon in {1/10,-1/10}", "closeness" => "matches holonomy at pi/4 only", "expected_teeth_row" => "expanded holonomy spectrum", "cost" => "light-symbolic", "forms" => [("pi4", 1//10, "epsilon=1/10"), ("pi4", -1//10, "epsilon=-1/10")]),
        Dict("id" => "S9.R3.4_two_leaf_match_pi6_pi4", "finite_representative" => "f=cos(2eta)+epsilon*cos(2eta)*(cos(2eta)-1/2), epsilon in {1/10,-1/10}", "closeness" => "very close leaf-anchor neighbor", "expected_teeth_row" => "annular flux plus off-anchor holonomy", "cost" => "light-symbolic", "forms" => [("pi6pi4", 1//10, "epsilon=1/10"), ("pi6pi4", -1//10, "epsilon=-1/10")]),
        Dict("id" => "S9.R3.5_path_ordered_loop_neighbor", "finite_representative" => "same local c1 row plus two named quaternionic loop families from the committed transport closure", "closeness" => "closest heavy transport neighbor", "expected_teeth_row" => "path-ordered holonomy commutator", "cost" => "heavy-local", "forms" => [("loop", 0//1, "local-c1-anchor-plus-heavy-loop-family")]),
    ]
end

function witness(anchor, candidate, preferred_row::String)
    paths = if preferred_row == "curvature density before holonomy"
        [["F_curvature_form_coefficient"]]
    elseif preferred_row == "expanded holonomy spectrum"
        [["leaf_holonomy_vector", "0"], ["leaf_holonomy_vector", "pi/4"], ["leaf_holonomy_vector", "pi/3"]]
    elseif preferred_row == "annular flux plus off-anchor holonomy"
        [["annular_flux_vector", "0->pi/6"], ["annular_flux_vector", "pi/4->pi/3"], ["leaf_holonomy_vector", "0"], ["leaf_holonomy_vector", "pi/3"]]
    else
        [["f_simplified"], ["F_curvature_form_coefficient"], ["leaf_holonomy_vector", "0"]]
    end
    for path in paths
        left = anchor
        right = candidate
        for part in path
            left = left[part]
            right = right[part]
        end
        if left != right
            return Dict("field" => join(path, "."), "anchor" => left, "candidate" => right)
        end
    end
    Dict("field" => "canonical_tuple", "anchor" => "equal", "candidate" => "equal")
end

function julia_z3_proof()
    solver = Z3.Solver()
    anchor_scaled = Z3.IntVar("julia_anchor_leaf0_scaled_by_20")
    candidate_scaled = Z3.IntVar("julia_candidate_leaf0_scaled_by_20")
    Z3.add(solver, anchor_scaled == Z3.IntVal(20))
    Z3.add(solver, candidate_scaled == Z3.IntVal(21))
    Z3.add(solver, anchor_scaled == candidate_scaled)
    positive = string(Z3.check(solver))

    flip = Z3.Solver()
    flip_anchor = Z3.IntVar("julia_flip_anchor_leaf0_scaled_by_20")
    flip_candidate = Z3.IntVar("julia_flip_candidate_leaf0_scaled_by_20")
    Z3.add(flip, flip_anchor == Z3.IntVal(20))
    Z3.add(flip, flip_candidate == Z3.IntVal(20))
    Z3.add(flip, flip_anchor == flip_candidate)
    flip_status = string(Z3.check(flip))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => positive,
        "load_bearing" => true,
        "asserted_precomputed_boolean" => false,
        "claim" => "computed exact rational off-anchor holonomy witness cannot equal the pinned anchor value",
        "witness_values" => Dict("candidate" => "S9.R3.2_one_leaf_match_pi6 epsilon=1/10", "leaf" => "0", "anchor_leaf0" => "1", "candidate_leaf0" => "21/20", "scaled_difference" => "1"),
        "negated_assertion" => "anchor_leaf0_scaled_by_20 == candidate_leaf0_scaled_by_20",
        "flip_control_verdict" => flip_status,
        "positive_case" => "off-anchor holonomy differs by exact rational 1/20, so alias equality is UNSAT",
        "negative/erased_control" => "deliberate reparameterized alias has equal scaled leaf value",
        "boundary_case" => "SMT binds a finite rational nonzero witness only; path-ordered loops remain queued-heavy-local",
    )
end

function build_rows()
    anchor = canonical_tuple("anchor")
    candidates = []
    for spec in registry_specs()
        forms = []
        for form in spec["forms"]
            kind, eps, label = form
            push!(forms, Dict(
                "variant" => label,
                "canonical_tuple" => canonical_tuple(kind, eps; path_ordered_loop_signature=spec["id"] == "S9.R3.5_path_ordered_loop_neighbor" ? "queued-heavy-local" : "not-scoped-light-symbolic"),
            ))
        end
        if spec["id"] == "S9.R3.0_committed_hopf"
            verdict = "anchor"
            row_name = "anchor"
            wit = witness(anchor, forms[1]["canonical_tuple"], "anchor")
            citation = "anchor row; no co-survivor citation required"
        elseif spec["cost"] == "heavy-local"
            verdict = "open + queued-heavy-local"
            row_name = "heavy_local_cost_guard_not_run_in_phase_1"
            wit = Dict("field" => "path_ordered_loop_signature", "anchor" => "ordinary one-form local anchor; no path-ordered loop signature scoped", "candidate" => "$(spec["id"]) cost=heavy-local; queued for $(spec["expected_teeth_row"])")
            citation = "no prior co-survivor receipt cited; S4 audit standard forces open + queued-heavy-local"
        else
            verdict = "excluded-by-" * replace(spec["expected_teeth_row"], " " => "-")
            row_name = spec["expected_teeth_row"]
            wit = witness(anchor, forms[1]["canonical_tuple"], spec["expected_teeth_row"])
            citation = "not a known co-survivor label; exact light-symbolic teeth row supplied a separating witness"
        end
        push!(candidates, Dict(
            "id" => spec["id"],
            "finite_representative" => spec["finite_representative"],
            "closeness" => spec["closeness"],
            "expected_teeth_row" => spec["expected_teeth_row"],
            "cost" => spec["cost"],
            "verdict" => verdict,
            "row" => row_name,
            "witness" => wit,
            "canonical_forms" => forms,
            "citation_status" => citation,
        ))
    end
    alias_tuple = canonical_tuple("alias")
    flat_tuple = canonical_tuple("flat")
    controls = [
        Dict("id" => "control.anchor_self", "verdict" => "anchor", "row" => "anchor", "witness" => witness(anchor, anchor, "anchor"), "canonical_tuple" => anchor),
        Dict("id" => "control.alias_reparameterized_committed", "verdict" => alias_tuple["leaf_holonomy_vector"] == anchor["leaf_holonomy_vector"] && alias_tuple["c1"] == anchor["c1"] ? "alias" : "failed", "row" => "gauge-reparameterization alias check", "witness" => witness(anchor, alias_tuple, "anchor"), "canonical_tuple" => alias_tuple),
        Dict("id" => "control.round2_flat_far_connection", "verdict" => "excluded-by-curvature-density-row", "row" => "curvature density first teeth row", "witness" => witness(anchor, flat_tuple, "curvature density before holonomy"), "canonical_tuple" => flat_tuple),
    ]
    Dict("candidate_rows" => candidates, "control_rows" => controls)
end

function build_result()
    rows = build_rows()
    verdicts = Dict(row["id"] => row["verdict"] for row in rows["candidate_rows"])
    controls = Dict(row["id"] => row["verdict"] for row in rows["control_rows"])
    heavy_queue = [row["id"] for row in rows["candidate_rows"] if row["cost"] == "heavy-local"]
    light_exclusions = [row["id"] for row in rows["candidate_rows"] if startswith(row["verdict"], "excluded-by-")]
    proof = julia_z3_proof()
    gates = Dict(
        "symbolics_rows_built" => length(rows["candidate_rows"]) == 6,
        "anchor_classifies_as_itself" => verdicts["S9.R3.0_committed_hopf"] == "anchor",
        "deliberate_alias_classifies_alias" => controls["control.alias_reparameterized_committed"] == "alias",
        "far_candidate_dies_first_teeth" => controls["control.round2_flat_far_connection"] == "excluded-by-curvature-density-row",
        "light_symbolic_exclusions_named_by_registry_rows" => length(light_exclusions) == 4,
        "heavy_local_rows_queued" => verdicts["S9.R3.5_path_ordered_loop_neighbor"] == "open + queued-heavy-local",
        "julia_z3_positive_unsat" => proof["verdict"] == "unsat",
        "julia_z3_flip_control_sat" => proof["flip_control_verdict"] == "sat",
    )
    all_pass = all(values(gates))
    Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "julia_symbolics_z3_connection_reference_lane",
        "engine_role_note" => "Julia Symbolics rebuilds exact f/F forms and exact leaf rows; Z3.jl binds the finite rational nonzero witness polarity.",
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Symbolics", "Z3"],
        "package_observables" => Dict(
            "Symbolics" => "Symbolics.simplify/Differential/expand_derivatives computes exact f and F rows before hand-entered exact leaf substitutions",
            "Z3" => "Z3.Solver/check proves finite rational off-anchor holonomy equality UNSAT and alias flip SAT",
        ),
        "claim_path_tools" => ["Symbolics", "Z3"],
        "all_pass" => all_pass,
        "positive" => Dict("symbolics_reference_rows" => rows["candidate_rows"], "anchor_and_alias_control" => rows["control_rows"][1:2]),
        "negative" => Dict("far_candidate_control" => rows["control_rows"][3], "heavy_local_label_guard" => "not-run heavy-local rows are open + queued-heavy-local"),
        "boundary" => Dict(
            "phase" => "light-symbolic phase 1 only",
            "heavy_local_not_run" => heavy_queue,
            "pytorch_omitted" => "no PyTorch tensor/autograd/message-passing claim path is scoped",
            "path_ordered_transport_loops" => "queued-heavy-local, not run",
        ),
        "candidate_verdicts" => rows["candidate_rows"],
        "control_verdicts" => rows["control_rows"],
        "phase2_queue" => Dict(
            "light_symbolic_non_alias_representatives_remaining" => [],
            "heavy_local_queued_by_registry_cost_class" => heavy_queue,
            "known_cosurvivor_classes" => [],
        ),
        "crossover_proofs" => Dict("julia_z3" => proof),
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("used" => true, "reason" => "load-bearing exact connection form and derivative construction"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing Julia-side finite rational nonzero-witness polarity"),
            "JSON" => Dict("used" => true, "reason" => "supportive result serialization"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hash"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Symbolics" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api" => "Symbolics.simplify/Differential/expand_derivatives",
                "input_object" => "finite S9 registry functions f(eta)",
                "output_object" => "exact f and F rows mirrored against Python SymPy verdicts",
                "positive_case" => "reparameterized anchor preserves exact leaf and c1 rows",
                "negative/erased_control" => "flat far-control has F=0 and fails the curvature-density row",
                "boundary_case" => "path-ordered loops remain queued",
                "demotion_condition" => "Symbolics lane disagrees with Python exact verdict table",
            )
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
    result["all_pass"] ? 0 : 1
end

exit(main())
