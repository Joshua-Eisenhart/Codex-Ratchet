# constraint_basin_synthesis_terrain64.jl
#
# Bounded finite proof packet for the "constraints create a survivor basin" move.
# This is a proof-pattern scout over the 16 terrain/operator words x 4 substages,
# not a layer-completion or manifold-admission receipt.

using Dates
using JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "constraint_basin_synthesis_terrain64_results.json")

const WORDS = [
    "NeTi", "FeSi", "TiSe", "NiFe",
    "SeFi", "SiTe", "FiNe", "TeNi",
    "NeFi", "TeSi", "FiSe", "NiTe",
    "TiNe", "SiFe", "SeTi", "FeNi",
]

const SUBSTAGES = ["Ti", "Te", "Fi", "Fe"]
const TARGET_WORD = 1
const TARGET_SUBSTAGE = 1

state_id(word_i::Int, sub_i::Int) = (word_i - 1) * length(SUBSTAGES) + sub_i
word_of(state::Int) = fld(state - 1, length(SUBSTAGES)) + 1
substage_of(state::Int) = mod(state - 1, length(SUBSTAGES)) + 1
state_label(state::Int) = "$(WORDS[word_of(state)])::$(SUBSTAGES[substage_of(state)])"

function states(nwords::Int)
    collect(1:(nwords * length(SUBSTAGES)))
end

function project_substage(state::Int)
    state_id(word_of(state), TARGET_SUBSTAGE)
end

function contract_word(state::Int, nwords::Int; gated_by_substage::Bool)
    w = word_of(state)
    s = substage_of(state)
    if w == TARGET_WORD
        return state
    end
    if (!gated_by_substage) || s == TARGET_SUBSTAGE
        return state_id(w - 1, s)
    end
    return state
end

function transition_tables(nwords::Int)
    xs = states(nwords)
    project = Dict(x => project_substage(x) for x in xs)
    contract_gated = Dict(x => contract_word(x, nwords; gated_by_substage=true) for x in xs)
    contract_order_erased = Dict(x => contract_word(x, nwords; gated_by_substage=false) for x in xs)

    genuine = Dict(x => contract_gated[project[x]] for x in xs)
    reverse_order = Dict(x => project[contract_gated[x]] for x in xs)
    order_erased = Dict(x => contract_order_erased[project[x]] for x in xs)
    constraint_erased = project
    identity = Dict(x => x for x in xs)

    Dict(
        "project_substage" => project,
        "contract_gated" => contract_gated,
        "contract_order_erased" => contract_order_erased,
        "genuine" => genuine,
        "reverse_order" => reverse_order,
        "order_erased" => order_erased,
        "constraint_erased" => constraint_erased,
        "identity" => identity,
    )
end

function iter_table(table::Dict{Int,Int}, x::Int, k::Int)
    y = x
    for _ in 1:k
        y = table[y]
    end
    y
end

function bad_reach_states(table::Dict{Int,Int}, nwords::Int, target::Int, k::Int)
    [x for x in states(nwords) if iter_table(table, x, k) != target]
end

function non_target_fixed_states(table::Dict{Int,Int}, nwords::Int, target::Int)
    [x for x in states(nwords) if x != target && table[x] == x]
end

function hamming_table(a::Dict{Int,Int}, b::Dict{Int,Int}, nwords::Int)
    count(x -> a[x] != b[x], states(nwords))
end

function z3_domain(ctx, x, nstates::Int)
    Z3.Or([x == Z3.IntVal(i, ctx) for i in 1:nstates])
end

function z3_link_table!(solver, ctx, xin, xout, table::Dict{Int,Int}, nstates::Int)
    for i in 1:nstates
        Z3.add(
            solver,
            Z3.Or([
                Z3.Not(xin == Z3.IntVal(i, ctx)),
                xout == Z3.IntVal(table[i], ctx),
            ]),
        )
    end
end

function z3_reachability_counterexample(table::Dict{Int,Int}, nwords::Int, target::Int, k::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    nstates = nwords * length(SUBSTAGES)
    vars = [Z3.IntVar("x$(i)", ctx) for i in 0:k]
    for x in vars
        Z3.add(solver, z3_domain(ctx, x, nstates))
    end
    for i in 1:k
        z3_link_table!(solver, ctx, vars[i], vars[i + 1], table, nstates)
    end
    Z3.add(solver, Z3.Not(vars[end] == Z3.IntVal(target, ctx)))
    status = string(Z3.check(solver))
    Dict(
        "query" => "exists state not reaching target within k",
        "status" => status,
        "counterexample_exists" => status == "sat",
        "proves_all_reach" => status == "unsat",
        "k" => k,
    )
end

function z3_non_target_fixed_counterexample(table::Dict{Int,Int}, nwords::Int, target::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    nstates = nwords * length(SUBSTAGES)
    x0 = Z3.IntVar("x0", ctx)
    x1 = Z3.IntVar("x1", ctx)
    Z3.add(solver, z3_domain(ctx, x0, nstates))
    Z3.add(solver, z3_domain(ctx, x1, nstates))
    z3_link_table!(solver, ctx, x0, x1, table, nstates)
    Z3.add(solver, Z3.Not(x0 == Z3.IntVal(target, ctx)))
    Z3.add(solver, x1 == x0)
    status = string(Z3.check(solver))
    Dict(
        "query" => "exists non-target fixed point",
        "status" => status,
        "counterexample_exists" => status == "sat",
        "proves_no_other_fixed_point" => status == "unsat",
    )
end

function z3_commutation_witness(table_a::Dict{Int,Int}, table_b::Dict{Int,Int}, nwords::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    nstates = nwords * length(SUBSTAGES)
    x0 = Z3.IntVar("x0", ctx)
    ax = Z3.IntVar("ax", ctx)
    ab = Z3.IntVar("ab", ctx)
    bx = Z3.IntVar("bx", ctx)
    ba = Z3.IntVar("ba", ctx)
    for x in (x0, ax, ab, bx, ba)
        Z3.add(solver, z3_domain(ctx, x, nstates))
    end
    z3_link_table!(solver, ctx, x0, ax, table_a, nstates)
    z3_link_table!(solver, ctx, ax, ab, table_b, nstates)
    z3_link_table!(solver, ctx, x0, bx, table_b, nstates)
    z3_link_table!(solver, ctx, bx, ba, table_a, nstates)
    Z3.add(solver, Z3.Not(ab == ba))
    status = string(Z3.check(solver))
    Dict(
        "query" => "exists x where A_then_B differs from B_then_A",
        "status" => status,
        "order_sensitive_witness_exists" => status == "sat",
        "commutation_proven" => status == "unsat",
    )
end

function rung_report(nwords::Int)
    tabs = transition_tables(nwords)
    nstates = nwords * length(SUBSTAGES)
    target = state_id(TARGET_WORD, TARGET_SUBSTAGE)
    k = nwords - 1

    genuine_bad = bad_reach_states(tabs["genuine"], nwords, target, k)
    erased_bad = bad_reach_states(tabs["constraint_erased"], nwords, target, k)
    wrong_target = state_id(min(2, nwords), TARGET_SUBSTAGE)
    wrong_target_bad = bad_reach_states(tabs["genuine"], nwords, wrong_target, k)

    order_gap_count = hamming_table(tabs["genuine"], tabs["reverse_order"], nwords)
    erased_order_gap_count = hamming_table(
        tabs["order_erased"],
        Dict(x => tabs["project_substage"][tabs["contract_order_erased"][x]] for x in states(nwords)),
        nwords,
    )

    z3_reach = z3_reachability_counterexample(tabs["genuine"], nwords, target, k)
    z3_no_other = z3_non_target_fixed_counterexample(tabs["genuine"], nwords, target)
    z3_order = z3_commutation_witness(tabs["contract_gated"], tabs["project_substage"], nwords)
    z3_order_erased = z3_commutation_witness(tabs["contract_order_erased"], tabs["project_substage"], nwords)
    z3_constraint_erased = z3_reachability_counterexample(tabs["constraint_erased"], nwords, target, k)
    z3_wrong_target = z3_reachability_counterexample(tabs["genuine"], nwords, wrong_target, k)

    controls_pass =
        z3_order["order_sensitive_witness_exists"] &&
        z3_order_erased["commutation_proven"] &&
        z3_constraint_erased["counterexample_exists"] &&
        z3_wrong_target["counterexample_exists"]

    table_hamming = Dict(
        "genuine_vs_constraint_erased" => hamming_table(tabs["genuine"], tabs["constraint_erased"], nwords),
        "order_erased_vs_constraint_erased" => hamming_table(tabs["order_erased"], tabs["constraint_erased"], nwords),
        "genuine_vs_identity" => hamming_table(tabs["genuine"], tabs["identity"], nwords),
    )

    proof_pass =
        z3_reach["proves_all_reach"] &&
        z3_no_other["proves_no_other_fixed_point"] &&
        controls_pass &&
        order_gap_count > 0 &&
        erased_order_gap_count == 0 &&
        all(v > 0 for v in values(table_hamming))

    Dict(
        "state_count" => nstates,
        "word_count" => nwords,
        "horizon_k" => k,
        "target_state" => target,
        "target_label" => state_label(target),
        "z3_reachability" => z3_reach,
        "z3_no_other_fixed_point" => z3_no_other,
        "z3_order_sensitive_genuine" => z3_order,
        "z3_order_erased_control" => z3_order_erased,
        "z3_constraint_erased_control" => z3_constraint_erased,
        "z3_wrong_target_control" => z3_wrong_target,
        "genuine_bad_reach_count" => length(genuine_bad),
        "constraint_erased_bad_reach_count" => length(erased_bad),
        "wrong_target_bad_reach_count" => length(wrong_target_bad),
        "order_gap_count" => order_gap_count,
        "order_erased_gap_count" => erased_order_gap_count,
        "control_table_hamming" => table_hamming,
        "sample_transitions" => [
            Dict(
                "from" => state_label(x),
                "genuine_next" => state_label(tabs["genuine"][x]),
                "reverse_order_next" => state_label(tabs["reverse_order"][x]),
                "constraint_erased_next" => state_label(tabs["constraint_erased"][x]),
            )
            for x in first(states(nwords), min(8, nstates))
        ],
        "controls_pass" => controls_pass,
        "proof_pass" => proof_pass,
    )
end

function main()
    rungs = Dict{String,Any}()
    for nwords in (2, 4, 8, 16)
        row = rung_report(nwords)
        rungs[string(row["state_count"])] = row
    end

    r64 = rungs["64"]
    all_rungs_pass = all(row["proof_pass"] for row in values(rungs))
    all_pass = all_rungs_pass

    tool_ablations = Dict(
        "constraint_erased_transition" => Dict(
            "what_changed" => "remove the word-contraction constraint, leaving only substage projection",
            "baseline_bad_reach_count" => r64["genuine_bad_reach_count"],
            "control_bad_reach_count" => r64["constraint_erased_bad_reach_count"],
            "outcome_delta" => r64["constraint_erased_bad_reach_count"] - r64["genuine_bad_reach_count"],
        ),
        "order_gate_erased" => Dict(
            "what_changed" => "remove substage gating from word contraction",
            "baseline_order_gap_count" => r64["order_gap_count"],
            "control_order_gap_count" => r64["order_erased_gap_count"],
            "outcome_delta" => r64["order_gap_count"] - r64["order_erased_gap_count"],
        ),
        "wrong_target_claim" => Dict(
            "what_changed" => "keep the genuine map but claim the FeSi::Ti state is the basin target",
            "baseline_bad_reach_count" => r64["genuine_bad_reach_count"],
            "wrong_target_bad_reach_count" => r64["wrong_target_bad_reach_count"],
            "outcome_delta" => r64["wrong_target_bad_reach_count"] - r64["genuine_bad_reach_count"],
        ),
    )

    result = Dict{String,Any}(
        "object_id" => "constraint_basin_synthesis_terrain64",
        "sim_id" => "constraint_basin_synthesis_terrain64",
        "name" => "Finite constraint-basin synthesis proof over 16 terrain/operator words x 4 substages",
        "version" => "0.1.0",
        "generated_at" => string(now(UTC)),
        "tier" => "tool-stage finite proof scout",
        "classification" => "formal_scout",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "constraint_probe",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "one_layer_done_right_candidate" => false,
        "all_pass" => all_pass,

        "purpose" => "Prove, on a finite 64-state fixture, that a named constraint set creates a bounded survivor basin and that erased/wrong controls flip the proof.",
        "scientific_question" => "Can finite F01/N01 constraints force all allowed terrain/operator microstates into a target survivor basin within a bounded horizon?",
        "claim_ceiling" => "Diagnostic proof-pattern scout only. This proves a finite SMT basin certificate shape over the terrain/operator schedule fixture. It does not admit a layer, a PEPS carrier, a manifold basin, Axis0, flux, FEP, physics, or final manifold status.",
        "demotion_condition" => "Demote to broken if any genuine Z3 proof flips from UNSAT/SAT as expected, if erased controls stop producing counterexamples, or if a downstream report cites this as PEPS/manifold/layer admission.",
        "out_of_scope" => [
            "continuous or infinite-time attractor proof",
            "PEPS2D or PEPS3D carrier construction",
            "spinor-network carrier admission",
            "per-layer completion",
            "manifold basin admission",
            "flux/Xi/Phi0/Axis0/FEP/physics claims",
        ],
        "next_lego_target" => "Port this proof shape onto one exported per-layer finite map with a real carrier, starting with a terrain/channel map that already has controls.",
        "promotion_condition" => "Promotion requires a real JAX or Julia carrier map exported by the target layer, PEPS3D or explicit blocked carrier boundary as required by the manifold gate, fresh controls, and a passing layer-completion claim gate for any completion-like wording.",
        "blocked_until" => "A target layer exports an admitted finite map/carrier and the proof is rerun against that map instead of this finite schedule fixture.",

        "root_constraints" => [
            "F01 finite carrier/probe/operator/path set: 16 words x 4 substages, checked at 8/16/32/64 state rungs",
            "N01 noncommuting/order-sensitive operation/control: gated word contraction and substage projection have A∘B != B∘A, while order-erased control commutes",
        ],
        "root_constraints_in_force" => [
            "F01 finite distinguishable terrain/operator schedule states",
            "N01 order-sensitive composition, witnessed by a Z3 SAT noncommutation query",
        ],

        "finite_map" => Dict(
            "domain" => "finite states (native_word, substage) in 16 terrain/operator words x {Ti,Te,Fi,Fe}; scale rungs use prefixes with 8/16/32/64 states",
            "codomain_or_output" => "next finite state plus Z3 reachability/no-extra-fixed/order-control proof statuses",
            "map" => "F_C = contract_word_gated_after_project_substage. project_substage sets substage Ti; contract_word_gated moves one word toward NeTi only after the Ti projection. The target NeTi::Ti is fixed.",
        ),
        "domain" => "64 finite terrain/operator microstates; no continuous, PEPS, or infinite-time state space is claimed",
        "codomain_or_output" => "bounded survivor-basin certificate, negative-control counterexamples, and diagnostic result JSON",

        "carrier_layer" => "finite schedule fixture",
        "geometry_layer" => "terrain/operator order grammar fixture, not a geometric manifold carrier",
        "carrier_realization" => "Julia-native finite integer transition tables plus Z3 SMT proof queries",
        "peps3d_embedding" => "absent; this absence blocks manifold, PEPS3D, flux, Axis0, FEP, physics, and basin-admission consumers",
        "spinor_state" => "not_applicable_to_this_finite_proof_scout",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [
            "system_v5/julia_carrier/layers/sixteen_terrain_placement_lattice_results.json",
            "system_v5/julia_carrier/layers/jax_weyl_terrain_64_microstep_diagnostic_results.json",
            "system_v5/julia_carrier/layers/jax_terrain_choi_holonomy_ladder_probe_results.json",
        ],
        "downstream_blocks" => [
            "layer completion", "parent-complete layer status", "G-structure selection",
            "PEPS2D", "PEPS3D", "stacking readiness", "flux", "Xi", "Phi0",
            "Axis0", "FEP", "bridge", "gravity", "physics", "final manifold admission",
            "manifold basin admission",
        ],
        "blocked_consumers" => [
            "layer completion", "parent-complete layer status", "G-structure selection",
            "PEPS2D", "PEPS3D", "stacking readiness", "flux", "Xi", "Phi0",
            "Axis0", "FEP", "bridge", "gravity", "physics", "final manifold admission",
            "manifold basin admission",
        ],
        "eligible_consumers" => [
            "proof-pattern design for later per-layer constraint-basin packets",
            "bounded scout comparison against JAX terrain/operator stress probes",
        ],

        "law_or_candidate_tested" => "bounded reachability to a target survivor basin under F_C, exclusion of non-target fixed points, and N01 order sensitivity with erased/wrong controls",
        "branch_status_before_run" => "proof_scout_not_admission",
        "allowed_claims" => [
            "The finite 64-state fixture has a Z3-certified bounded basin under the named constraints.",
            "The constraint-erased and wrong-target controls produce Z3 SAT counterexamples.",
            "The order-erased control collapses the N01 order witness.",
            "promotion_allowed=false; no layer, manifold, PEPS, flux, Axis0, FEP, bridge, or physics claim is made.",
        ],
        "promotion_blockers" => [
            "no PEPS3D carrier",
            "no spinor-network carrier",
            "finite schedule fixture only",
            "no continuous terrain/Lindblad basin boundary proof",
            "no per-layer rebuilt carrier map",
            "no layer-completion claim gate",
        ],

        "required_tools" => ["Julia", "Z3", "JSON"],
        "actual_tools_used" => ["Julia", "Z3", "JSON", "Dates"],
        "proof_surfaces_used" => ["Z3 finite bounded reachability", "Z3 fixed-point exclusion", "Z3 order-sensitivity witness"],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "tool_manifest" => Dict(
            "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "builds the finite transition fixture, controls, scale rungs, and result receipt"),
            "Z3" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "proves no bounded-reachability counterexample, proves no non-target fixed point, and flips to SAT on erased/wrong controls"),
            "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "writes the result artifact"),
            "Dates" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "timestamps the result artifact"),
        ),
        "tool_integration_depth" => Dict(
            "Julia" => "load_bearing",
            "Z3" => "load_bearing",
            "JSON" => "supportive",
            "Dates" => "supportive",
        ),
        "backend_primary_result" => Dict(
            "backend" => "Julia + Z3",
            "claim_bearing" => true,
            "all_pass" => all_pass,
            "summary" => "Z3 is the proof backend; Julia supplies the finite map and controls.",
        ),

        "required_inputs" => ["16 native words", "4 substages", "target NeTi::Ti", "constraint flags project_substage then gated word contraction"],
        "data_or_artifact_dependencies" => [],
        "required_negatives" => ["order_erased_control", "constraint_erased_control", "wrong_target_control", "bit_identical_control_check"],
        "negatives_run" => ["order_erased_control", "constraint_erased_control", "wrong_target_control", "bit_identical_control_check"],
        "kill_conditions" => [
            "genuine reachability query becomes SAT",
            "non-target fixed-point query becomes SAT",
            "order-erased control remains order-sensitive",
            "constraint-erased or wrong-target control becomes UNSAT",
            "control transition tables are bit-identical",
        ],

        "scale_ladder" => Dict("rungs" => rungs),
        "controls" => Dict(
            "order_erased_control" => r64["z3_order_erased_control"],
            "constraint_erased_control" => r64["z3_constraint_erased_control"],
            "wrong_target_control" => r64["z3_wrong_target_control"],
            "bit_identical_control_check" => r64["control_table_hamming"],
        ),
        "tool_ablations" => tool_ablations,
        "z3_proof" => Dict(
            "terrain64" => Dict(
                "reachability" => r64["z3_reachability"],
                "no_other_fixed_point" => r64["z3_no_other_fixed_point"],
                "order_sensitive_genuine" => r64["z3_order_sensitive_genuine"],
                "order_erased_control" => r64["z3_order_erased_control"],
                "constraint_erased_control" => r64["z3_constraint_erased_control"],
                "wrong_target_control" => r64["z3_wrong_target_control"],
            ),
            "load_bearing" => all_pass,
        ),

        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "constraint_basin_synthesis_terrain64:NeTi::Ti",
        "result_summary" => Dict(
            "all_rungs_pass" => all_rungs_pass,
            "state_rungs" => sort(collect(keys(rungs)); by=x->parse(Int, x)),
            "terrain64_order_gap_count" => r64["order_gap_count"],
            "terrain64_constraint_erased_bad_reach_count" => r64["constraint_erased_bad_reach_count"],
            "terrain64_wrong_target_bad_reach_count" => r64["wrong_target_bad_reach_count"],
        ),
        "pass_rule" => "All 8/16/32/64 rungs must prove bounded reachability UNSAT, prove no other fixed point UNSAT, show genuine order SAT, show order-erased commutation UNSAT, and show erased/wrong controls SAT.",
        "fail_rule" => "Any missing proof flip, bit-identical control, failed scale rung, or promotion-like downstream claim fails the scout.",
        "promotion_status" => "diagnostic_only",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("constraint_basin_synthesis_terrain64")
    println("  result: ", RESULT_PATH)
    println("  all_pass: ", all_pass)
    println("  terrain64 reachability: ", r64["z3_reachability"]["status"])
    println("  terrain64 no-other-fixed: ", r64["z3_no_other_fixed_point"]["status"])
    println("  terrain64 order witness: ", r64["z3_order_sensitive_genuine"]["status"])
    println("  terrain64 order-erased control: ", r64["z3_order_erased_control"]["status"])
    println("  terrain64 constraint-erased control: ", r64["z3_constraint_erased_control"]["status"])
    exit(all_pass ? 0 : 1)
end

main()
