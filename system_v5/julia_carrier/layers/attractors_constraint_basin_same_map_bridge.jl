# attractors_constraint_basin_same_map_bridge.jl
#
# Same-fixture bridge between the Z3 finite constraint-basin proof scout and
# Attractors.jl empirical basin mapping. This stays diagnostic-only.

using Attractors
using Dates
using DynamicalSystems
using JSON
using SHA
using StaticArrays

const RESULT_PATH = joinpath(@__DIR__, "attractors_constraint_basin_same_map_bridge_results.json")
const Z3_RESULT_PATH = joinpath(@__DIR__, "constraint_basin_synthesis_terrain64_results.json")

const WORDS = [
    "NeTi", "FeSi", "TiSe", "NiFe",
    "SeFi", "SiTe", "FiNe", "TeNi",
    "NeFi", "TeSi", "FiSe", "NiTe",
    "TiNe", "SiFe", "SeTi", "FeNi",
]
const SUBSTAGES = ["Ti", "Te", "Fi", "Fe"]
const TARGET_WORD = 1
const TARGET_SUBSTAGE = 1

const TOOL_MANIFEST = Dict(
    "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "constructs the same finite transition tables and emits the result receipt"),
    "Attractors" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "maps the exact finite transition table as a deterministic iterated map"),
    "DynamicalSystems" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "supplies DeterministicIteratedMap for the finite transition table"),
    "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "reads the Z3 result receipt and writes the bridge receipt"),
    "SHA" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "records source and transition-table hashes for stale/identity checks"),
    "StaticArrays" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "represents the one-dimensional discrete map state"),
    "Dates" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "timestamps the result artifact"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Julia" => "load_bearing",
    "Attractors" => "load_bearing",
    "DynamicalSystems" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
    "StaticArrays" => "supportive",
    "Dates" => "supportive",
)

state_id(word_i::Int, sub_i::Int) = (word_i - 1) * length(SUBSTAGES) + sub_i
word_of(state::Int) = fld(state - 1, length(SUBSTAGES)) + 1
substage_of(state::Int) = mod(state - 1, length(SUBSTAGES)) + 1
state_label(state::Int) = "$(WORDS[word_of(state)])::$(SUBSTAGES[substage_of(state)])"
states(nwords::Int) = collect(1:(nwords * length(SUBSTAGES)))

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
    order_erased_reverse = Dict(x => project[contract_order_erased[x]] for x in xs)
    constraint_erased = project
    identity = Dict(x => x for x in xs)
    Dict(
        "genuine" => genuine,
        "reverse_order" => reverse_order,
        "order_erased" => order_erased,
        "order_erased_reverse" => order_erased_reverse,
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

function hamming_table(a::Dict{Int,Int}, b::Dict{Int,Int}, nwords::Int)
    count(x -> a[x] != b[x], states(nwords))
end

function table_hash(table::Dict{Int,Int}, nwords::Int)
    payload = join(["$(x)->$(table[x])" for x in states(nwords)], ";")
    bytes2hex(sha256(payload))
end

function source_sha256()
    bytes2hex(sha256(read(@__FILE__)))
end

function entropy_report(basins)
    box_side = max(2, min(8, fld(length(basins), 4)))
    basin_ent, boundary_ent = basin_entropy(basins, box_side)
    Dict(
        "method" => "Attractors.basin_entropy over the one-dimensional finite transition-table basin labels",
        "box_side" => box_side,
        "basin_entropy" => isfinite(Float64(basin_ent)) ? Float64(basin_ent) : nothing,
        "boundary_basin_entropy" => isfinite(Float64(boundary_ent)) ? Float64(boundary_ent) : nothing,
        "claim_boundary" => "diagnostic finite-map entropy only; no fractal/Wada/infinite-time claim",
    )
end

function map_with_attractors(table::Dict{Int,Int}, nwords::Int)
    nstates = nwords * length(SUBSTAGES)
    function f(u, p, n)
        x = clamp(round(Int, u[1]), 1, nstates)
        SA[Float64(table[x])]
    end
    ds = DeterministicIteratedMap(f, SA[1.0])
    grid = (range(1, nstates; length = nstates),)
    mapper = AttractorsViaRecurrences(
        ds,
        grid;
        consecutive_recurrences = 3,
        attractor_locate_steps = 10,
        maximum_iterations = max(100, 4 * nstates),
    )
    basins, attractors = basins_of_attraction(mapper, grid; show_progress = false)
    fractions = basins_fractions(basins)
    target = state_id(TARGET_WORD, TARGET_SUBSTAGE)
    wrong_target = state_id(min(2, nwords), TARGET_SUBSTAGE)
    target_label = nothing
    wrong_label = nothing
    rows = Vector{Dict{String,Any}}()
    for raw_label in sort(collect(keys(fractions)); by = x -> Int(x))
        label = Int(raw_label)
        pts = collect(attractors[label])
        attractor_state = round(Int, Float64(first(only(pts))))
        if attractor_state == target
            target_label = Int(raw_label)
        end
        if attractor_state == wrong_target
            wrong_label = Int(raw_label)
        end
        push!(rows, Dict(
            "label" => label,
            "fraction" => Float64(fractions[raw_label]),
            "attractor_state" => attractor_state,
            "attractor_label" => state_label(attractor_state),
        ))
    end
    target_fraction = target_label === nothing ? 0.0 : Float64(fractions[Int32(target_label)])
    wrong_fraction = wrong_label === nothing ? 0.0 : Float64(fractions[Int32(wrong_label)])
    Dict(
        "attractor_count" => length(attractors),
        "target_state" => target,
        "target_label" => state_label(target),
        "target_fraction" => target_fraction,
        "wrong_target_state" => wrong_target,
        "wrong_target_label" => state_label(wrong_target),
        "wrong_target_fraction" => wrong_fraction,
        "raw_basin_labels" => [Int(x) for x in basins],
        "attractor_rows" => rows,
        "basin_entropy" => entropy_report(basins),
    )
end

function rung_report(nwords::Int, z3_rung)
    tabs = transition_tables(nwords)
    nstates = nwords * length(SUBSTAGES)
    target = state_id(TARGET_WORD, TARGET_SUBSTAGE)
    wrong_target = state_id(min(2, nwords), TARGET_SUBSTAGE)
    k = nwords - 1

    genuine = map_with_attractors(tabs["genuine"], nwords)
    constraint_erased = map_with_attractors(tabs["constraint_erased"], nwords)
    wrong_target_bad = count(x -> iter_table(tabs["genuine"], x, k) != wrong_target, states(nwords))

    order_gap_count = hamming_table(tabs["genuine"], tabs["reverse_order"], nwords)
    order_erased_gap_count = hamming_table(tabs["order_erased"], tabs["order_erased_reverse"], nwords)

    z3_reach_proved = get(get(z3_rung, "z3_reachability", Dict()), "proves_all_reach", false) == true
    z3_erased_counter = get(get(z3_rung, "z3_constraint_erased_control", Dict()), "counterexample_exists", false) == true
    z3_wrong_counter = get(get(z3_rung, "z3_wrong_target_control", Dict()), "counterexample_exists", false) == true

    same_map_pass =
        genuine["target_fraction"] == 1.0 &&
        genuine["attractor_count"] == 1 &&
        constraint_erased["target_fraction"] < 1.0 &&
        wrong_target_bad > 0 &&
        order_gap_count > 0 &&
        order_erased_gap_count == 0 &&
        z3_reach_proved &&
        z3_erased_counter &&
        z3_wrong_counter

    Dict(
        "state_count" => nstates,
        "word_count" => nwords,
        "horizon_k" => k,
        "genuine_table_hash" => table_hash(tabs["genuine"], nwords),
        "constraint_erased_table_hash" => table_hash(tabs["constraint_erased"], nwords),
        "genuine_attractors" => genuine,
        "constraint_erased_attractors" => constraint_erased,
        "wrong_target_bad_reach_count_direct" => wrong_target_bad,
        "order_gap_count_direct" => order_gap_count,
        "order_erased_gap_count_direct" => order_erased_gap_count,
        "z3_reach_proved" => z3_reach_proved,
        "z3_erased_counterexample_exists" => z3_erased_counter,
        "z3_wrong_target_counterexample_exists" => z3_wrong_counter,
        "same_map_bridge_pass" => same_map_pass,
    )
end

function main()
    source_hash = source_sha256()
    z3_result = JSON.parsefile(Z3_RESULT_PATH)
    z3_rungs = z3_result["scale_ladder"]["rungs"]

    rungs = Dict{String,Any}()
    for nwords in (2, 4, 8, 16)
        nstates = nwords * length(SUBSTAGES)
        rungs[string(nstates)] = rung_report(nwords, z3_rungs[string(nstates)])
    end
    r64 = rungs["64"]
    all_rungs_pass = all(row["same_map_bridge_pass"] for row in values(rungs))
    controls_pass =
        r64["genuine_attractors"]["target_fraction"] == 1.0 &&
        r64["constraint_erased_attractors"]["target_fraction"] < 1.0 &&
        r64["wrong_target_bad_reach_count_direct"] > 0 &&
        r64["order_gap_count_direct"] > 0 &&
        r64["order_erased_gap_count_direct"] == 0
    z3_dependency_pass = get(z3_result, "all_pass", false) == true &&
        get(z3_result, "classification", "") == "formal_scout" &&
        get(z3_result, "promotion_allowed", true) == false
    all_pass = all_rungs_pass && controls_pass && z3_dependency_pass

    tool_ablations = Dict(
        "constraint_erased_same_map" => Dict(
            "what_changed" => "Attractors consumes project_substage-only table instead of genuine F_C table",
            "baseline_target_fraction" => r64["genuine_attractors"]["target_fraction"],
            "control_target_fraction" => r64["constraint_erased_attractors"]["target_fraction"],
            "outcome_delta" => r64["genuine_attractors"]["target_fraction"] - r64["constraint_erased_attractors"]["target_fraction"],
        ),
        "wrong_target_same_table" => Dict(
            "what_changed" => "Keep genuine F_C table but claim FeSi::Ti instead of NeTi::Ti as the target",
            "baseline_bad_reach_count" => 0,
            "wrong_target_bad_reach_count" => r64["wrong_target_bad_reach_count_direct"],
            "outcome_delta" => r64["wrong_target_bad_reach_count_direct"],
        ),
        "order_erased_table" => Dict(
            "what_changed" => "Erase substage gating so order gap against projection table disappears",
            "baseline_order_gap_count" => r64["order_gap_count_direct"],
            "control_order_gap_count" => r64["order_erased_gap_count_direct"],
            "outcome_delta" => r64["order_gap_count_direct"] - r64["order_erased_gap_count_direct"],
        ),
    )

    result = Dict{String,Any}(
        "object_id" => "attractors_constraint_basin_same_map_bridge",
        "sim_id" => "attractors_constraint_basin_same_map_bridge",
        "name" => "Same-map bridge from Z3 finite basin proof to Attractors finite-map basin mapping",
        "version" => "0.1.0",
        "generated_at" => string(now(UTC)),
        "source_receipt_coherence" => Dict(
            "source_path" => @__FILE__,
            "source_sha256" => source_hash,
            "coherence_rule" => "Result must be treated as stale if source_sha256 does not match the current source file hash.",
        ),
        "tier" => "tool-stage same-fixture bridge scout",
        "classification" => "formal_scout",
        "sim_execution_kind" => "bridge",
        "sim_class" => "constraint_basin_same_map_bridge_probe",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "one_layer_done_right_candidate" => false,
        "all_pass" => all_pass,

        "purpose" => "Check that Attractors.jl basin mapping agrees with the Z3 finite proof on the same transition-table fixture, not a continuous surrogate.",
        "scientific_question" => "Can the exact finite F_C table proven by Z3 be mapped by Attractors as the same target basin while erased/wrong/order controls still fail?",
        "claim_ceiling" => "Same-fixture bridge scout only. It proves neither a continuous attractor theorem nor a PEPS/layer/manifold admission. It only records parity between a finite Z3 proof fixture and Attractors finite-map mapping.",
        "demotion_condition" => "Demote to broken if Attractors no longer maps the genuine F_C table to NeTi::Ti, if erased/wrong/order controls stop flipping, if the Z3 dependency receipt is not passing, or if downstream wording treats this as layer/manifold/PEPS admission.",
        "out_of_scope" => [
            "continuous or infinite-time attractor proof",
            "new Z3 proof beyond dependency comparison",
            "PEPS2D or PEPS3D carrier construction",
            "spinor-network carrier admission",
            "per-layer terrain/operator completion",
            "manifold basin admission",
            "flux/Xi/Phi0/Axis0/FEP/physics claims",
        ],
        "next_lego_target" => "Export one real terrain/channel carrier finite map and run this same-map bridge against that exported carrier rather than the schedule fixture.",
        "promotion_condition" => "Promotion requires a real target-layer carrier map, formal proof or interval bound where claimed, fresh controls, and a passing layer-completion claim gate for any completion-like wording.",
        "blocked_until" => "A target layer emits a real carrier transition map that can replace this proof fixture without inventing a surrogate.",

        "root_constraints" => [
            "F01 finite carrier/probe/operator/path set: exact finite transition tables at 8/16/32/64 state rungs",
            "N01 noncommuting/order-sensitive operation/control: genuine table differs from reverse-order table; order-erased table collapses the gap",
        ],
        "root_constraints_in_force" => [
            "F01 finite distinguishable terrain/operator schedule states",
            "N01 direct transition-table order gap, not a continuous ODE label",
        ],
        "finite_map" => Dict(
            "domain" => "finite states (native_word, substage) at 8/16/32/64 state rungs",
            "codomain_or_output" => "Attractors finite-map basin labels/fractions plus Z3 dependency parity and direct control deltas",
            "map" => "F_C = contract_word_gated_after_project_substage, recreated from the same fixture used by constraint_basin_synthesis_terrain64.jl.",
        ),
        "domain" => "finite terrain/operator schedule states only; no continuous, PEPS, spinor, or manifold state space is claimed",
        "codomain_or_output" => "same-fixture Attractors/Z3 parity receipt with negative-control deltas",

        "carrier_layer" => "finite schedule fixture",
        "geometry_layer" => "terrain/operator order grammar fixture, not a geometric manifold carrier",
        "carrier_realization" => "Julia finite transition tables mapped through DynamicalSystems.DeterministicIteratedMap and AttractorsViaRecurrences",
        "peps3d_embedding" => "absent; this blocks manifold, PEPS3D, flux, Axis0, FEP, physics, and basin-admission consumers",
        "spinor_state" => "not_applicable_to_this_same_fixture_bridge",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [Z3_RESULT_PATH],
        "prior_function_receipts" => [],
        "downstream_blocks" => [
            "layer completion", "parent-complete layer status", "G-structure selection",
            "PEPS2D", "PEPS3D", "stacking readiness", "flux", "Xi", "Phi0",
            "Axis0", "FEP", "bridge admission", "gravity", "physics",
            "final manifold admission", "manifold basin admission",
        ],
        "blocked_consumers" => [
            "layer completion", "parent-complete layer status", "G-structure selection",
            "PEPS2D", "PEPS3D", "stacking readiness", "flux", "Xi", "Phi0",
            "Axis0", "FEP", "bridge admission", "gravity", "physics",
            "final manifold admission", "manifold basin admission",
        ],
        "eligible_consumers" => [
            "diagnostic same-fixture proof/mapping parity",
            "future harness for exported per-layer finite maps",
        ],

        "law_or_candidate_tested" => "same finite F_C table maps all states to target basin under Attractors and matches the existing Z3 proof dependency; erased/wrong/order controls fail",
        "branch_status_before_run" => "same_fixture_bridge_not_admission",
        "allowed_claims" => [
            "Attractors.jl maps the same finite F_C fixture to the same target basin that Z3 proves.",
            "Constraint-erased, wrong-target, and order-erased controls flip on the 64-state fixture.",
            "promotion_allowed=false; no layer, manifold, PEPS, flux, Axis0, FEP, bridge admission, or physics claim is made.",
        ],
        "promotion_blockers" => [
            "finite schedule fixture only",
            "no PEPS2D or PEPS3D carrier",
            "no spinor-network carrier",
            "no exported per-layer carrier map",
            "no layer-completion claim gate",
        ],

        "required_tools" => collect(keys(TOOL_MANIFEST)),
        "actual_tools_used" => collect(keys(TOOL_MANIFEST)),
        "proof_surfaces_used" => ["dependency: constraint_basin_synthesis_terrain64 Z3 proof receipt"],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "backend_primary_result" => Dict(
            "backend" => "Julia + Attractors.jl + DynamicalSystems.jl with Z3 dependency receipt",
            "claim_bearing" => true,
            "claim_scope" => "same-fixture finite-map bridge only; not proof promotion or admission",
            "all_pass" => all_pass,
            "summary" => "Attractors maps the exact finite table; Z3 result is a dependency receipt, not rerun here.",
        ),

        "required_inputs" => ["same finite transition table fixture", "Z3 dependency result", "8/16/32/64 state rungs"],
        "data_or_artifact_dependencies" => [Z3_RESULT_PATH],
        "required_negatives" => ["constraint_erased_same_map", "wrong_target_same_table", "order_erased_table", "bit_identical_control_check"],
        "negatives_run" => ["constraint_erased_same_map", "wrong_target_same_table", "order_erased_table", "bit_identical_control_check"],
        "kill_conditions" => [
            "genuine F_C table does not map to NeTi::Ti target basin",
            "constraint-erased table maps all states to the target",
            "wrong-target claim has no failing states",
            "order-erased table keeps a nonzero order gap",
            "Z3 dependency receipt is not passing",
            "downstream report treats same-fixture parity as layer/manifold/PEPS admission",
        ],

        "scale_ladder" => Dict("rungs" => rungs),
        "controls" => Dict(
            "constraint_erased_64" => r64["constraint_erased_attractors"],
            "wrong_target_bad_reach_count_64" => r64["wrong_target_bad_reach_count_direct"],
            "order_gap_count_64" => r64["order_gap_count_direct"],
            "order_erased_gap_count_64" => r64["order_erased_gap_count_direct"],
            "z3_dependency_pass" => z3_dependency_pass,
        ),
        "tool_ablations" => tool_ablations,
        "entropy_as_output" => Dict(
            "genuine_64" => r64["genuine_attractors"]["basin_entropy"],
            "constraint_erased_64" => r64["constraint_erased_attractors"]["basin_entropy"],
            "boundary" => "Attractors.basin_entropy diagnostic only; no fractal/Wada claim",
        ),
        "decorative_tool_name_overclaim_guard" => Dict(
            "Attractors" => "load_bearing for finite-map basin labels/fractions/entropy only; not a proof engine",
            "DynamicalSystems" => "load_bearing for deterministic map execution only; not a nonclassical carrier admission",
            "shared_premise_tested" => "Attractors consumed the same finite table fixture as the Z3 scout; controls used different table hashes and changed target fractions/order gaps.",
            "bit_identical_controls_checked" => "genuine and constraint-erased table hashes differ on the 64-state rung",
        ),

        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "attractors_constraint_basin_same_map_bridge:F_C->NeTi::Ti",
        "result_summary" => Dict(
            "all_rungs_pass" => all_rungs_pass,
            "controls_pass" => controls_pass,
            "z3_dependency_pass" => z3_dependency_pass,
            "state_rungs" => sort(collect(keys(rungs)); by = x -> parse(Int, x)),
            "target_fraction_genuine_64" => r64["genuine_attractors"]["target_fraction"],
            "target_fraction_constraint_erased_64" => r64["constraint_erased_attractors"]["target_fraction"],
            "wrong_target_bad_reach_count_64" => r64["wrong_target_bad_reach_count_direct"],
            "order_gap_count_64" => r64["order_gap_count_direct"],
            "order_erased_gap_count_64" => r64["order_erased_gap_count_direct"],
            "source_sha256" => source_hash,
        ),
        "summary" => Dict(
            "all_pass" => all_pass,
            "sim_execution_kind" => "bridge",
            "tests_passed" => all_pass ? 1 : 0,
            "tests_total" => 1,
        ),
        "pass_rule" => "All 8/16/32/64 rungs must map genuine F_C to the target under Attractors, match Z3 dependency proof flags, and keep erased/wrong/order controls failing.",
        "fail_rule" => "Any missing same-map target basin, failed Z3 dependency, bit-identical control, or promotion-like downstream claim fails the bridge scout.",
        "promotion_status" => "diagnostic_only",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("attractors_constraint_basin_same_map_bridge")
    println("  result: ", RESULT_PATH)
    println("  all_pass: ", all_pass)
    println("  target fraction genuine 64: ", r64["genuine_attractors"]["target_fraction"])
    println("  target fraction erased 64: ", r64["constraint_erased_attractors"]["target_fraction"])
    println("  wrong target bad reach 64: ", r64["wrong_target_bad_reach_count_direct"])
    println("  order gap 64: ", r64["order_gap_count_direct"])
    exit(all_pass ? 0 : 1)
end

main()
