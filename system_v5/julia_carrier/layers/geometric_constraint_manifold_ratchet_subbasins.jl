# geometric_constraint_manifold_ratchet_subbasins.jl
#
# Finite proof/mapping scout for the idea that F01/N01-driven constraints
# ratchet a finite geometric-constraint fixture into a parent attractor basin
# with four sub-basins. Diagnostic only: no PEPS/layer/manifold admission.

using Attractors
using Dates
using DynamicalSystems
using JSON
using SHA
using StaticArrays
import Z3

const RESULT_PATH = joinpath(@__DIR__, "geometric_constraint_manifold_ratchet_subbasins_results.json")

const WORDS = [
    "NeTi", "FeSi", "TiSe", "NiFe",
    "SeFi", "SiTe", "FiNe", "TeNi",
    "NeFi", "TeSi", "FiSe", "NiTe",
    "TiNe", "SiFe", "SeTi", "FeNi",
]
const SUBSTAGES = ["Ti", "Te", "Fi", "Fe"]
const TARGET_WORD = 1

const TOOL_MANIFEST = Dict(
    "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "builds finite ratchet maps, controls, scale rungs, and result receipt"),
    "Z3" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "proves bounded parent-basin reachability and order/control counterexample status"),
    "Attractors" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "maps the finite ratchet table and measures parent/sub-basin fractions"),
    "DynamicalSystems" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "supplies DeterministicIteratedMap for the finite ratchet table"),
    "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "writes the result artifact"),
    "SHA" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "embeds source and table hashes for stale-receipt and bit-identical-control checks"),
    "StaticArrays" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "represents one-dimensional discrete map states for DynamicalSystems"),
    "Dates" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "timestamps the result artifact"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Julia" => "load_bearing",
    "Z3" => "load_bearing",
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
parent_basin_states() = [state_id(TARGET_WORD, sub_i) for sub_i in 1:length(SUBSTAGES)]

function source_sha256()
    bytes2hex(sha256(read(@__FILE__)))
end

function table_hash(table::Dict{Int,Int}, nwords::Int)
    payload = join(["$(x)->$(table[x])" for x in states(nwords)], ";")
    bytes2hex(sha256(payload))
end

function parent_ratchet(state::Int)
    w = word_of(state)
    s = substage_of(state)
    state_id(max(TARGET_WORD, w - 1), s)
end

function substage_shift(word_i::Int)
    if word_i == TARGET_WORD
        return 0
    end
    return mod(word_i, length(SUBSTAGES))
end

function order_sensitive_refiner(state::Int)
    w = word_of(state)
    s = substage_of(state)
    shifted = 1 + mod(s - 1 + substage_shift(w), length(SUBSTAGES))
    state_id(w, shifted)
end

function identity_refiner(state::Int)
    state
end

function collapse_subbasin(state::Int)
    state_id(word_of(state), 1)
end

function compose_table(left, right, nwords::Int)
    Dict(x => left(right(x)) for x in states(nwords))
end

function transition_tables(nwords::Int)
    a = Dict(x => parent_ratchet(x) for x in states(nwords))
    b = Dict(x => order_sensitive_refiner(x) for x in states(nwords))
    idb = Dict(x => identity_refiner(x) for x in states(nwords))
    collapse = Dict(x => collapse_subbasin(x) for x in states(nwords))
    Dict(
        "parent_ratchet" => a,
        "order_refiner" => b,
        "genuine" => Dict(x => a[b[x]] for x in states(nwords)),
        "reverse_order" => Dict(x => b[a[x]] for x in states(nwords)),
        "parent_erased" => b,
        "order_erased_genuine" => Dict(x => a[idb[x]] for x in states(nwords)),
        "order_erased_reverse" => Dict(x => idb[a[x]] for x in states(nwords)),
        "subbasin_collapsed" => Dict(x => a[collapse[x]] for x in states(nwords)),
    )
end

function iter_table(table::Dict{Int,Int}, x::Int, k::Int)
    y = x
    for _ in 1:k
        y = table[y]
    end
    y
end

function final_states(table::Dict{Int,Int}, nwords::Int, k::Int)
    Dict(x => iter_table(table, x, k) for x in states(nwords))
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

function z3_parent_reach_counterexample(table::Dict{Int,Int}, nwords::Int, k::Int)
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
    Z3.add(solver, Z3.Not(Z3.Or([vars[end] == Z3.IntVal(p, ctx) for p in parent_basin_states()])))
    status = string(Z3.check(solver))
    Dict(
        "query" => "exists state not reaching the parent basin within k",
        "status" => status,
        "counterexample_exists" => status == "sat",
        "proves_all_reach_parent_basin" => status == "unsat",
        "k" => k,
    )
end

function z3_external_fixed_counterexample(table::Dict{Int,Int}, nwords::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    nstates = nwords * length(SUBSTAGES)
    x0 = Z3.IntVar("x0", ctx)
    x1 = Z3.IntVar("x1", ctx)
    Z3.add(solver, z3_domain(ctx, x0, nstates))
    Z3.add(solver, z3_domain(ctx, x1, nstates))
    z3_link_table!(solver, ctx, x0, x1, table, nstates)
    Z3.add(solver, x1 == x0)
    Z3.add(solver, Z3.Not(Z3.Or([x0 == Z3.IntVal(p, ctx) for p in parent_basin_states()])))
    status = string(Z3.check(solver))
    Dict(
        "query" => "exists fixed point outside parent basin",
        "status" => status,
        "counterexample_exists" => status == "sat",
        "proves_no_external_fixed_point" => status == "unsat",
    )
end

function z3_order_witness(table_a::Dict{Int,Int}, table_b::Dict{Int,Int}, nwords::Int)
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

function z3_subbasin_nonempty(table::Dict{Int,Int}, nwords::Int, k::Int, sub_i::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    nstates = nwords * length(SUBSTAGES)
    target = state_id(TARGET_WORD, sub_i)
    vars = [Z3.IntVar("x$(i)", ctx) for i in 0:k]
    for x in vars
        Z3.add(solver, z3_domain(ctx, x, nstates))
    end
    for i in 1:k
        z3_link_table!(solver, ctx, vars[i], vars[i + 1], table, nstates)
    end
    Z3.add(solver, vars[end] == Z3.IntVal(target, ctx))
    status = string(Z3.check(solver))
    Dict(
        "target_subbasin" => SUBSTAGES[sub_i],
        "target_state" => target,
        "target_label" => state_label(target),
        "status" => status,
        "nonempty_witness_exists" => status == "sat",
    )
end

function entropy_report(basins)
    box_side = max(2, min(8, fld(length(basins), 4)))
    basin_ent, boundary_ent = basin_entropy(basins, box_side)
    Dict(
        "method" => "Attractors.basin_entropy over one-dimensional finite ratchet basin labels",
        "box_side" => box_side,
        "basin_entropy" => isfinite(Float64(basin_ent)) ? Float64(basin_ent) : nothing,
        "boundary_basin_entropy" => isfinite(Float64(boundary_ent)) ? Float64(boundary_ent) : nothing,
        "claim_boundary" => "finite-map entropy diagnostic only; no Wada/fractal/infinite-time theorem",
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
    sub_fractions = Dict(sub => 0.0 for sub in SUBSTAGES)
    parent_fraction = 0.0
    rows = Vector{Dict{String,Any}}()
    for raw_label in sort(collect(keys(fractions)); by = x -> Int(x))
        label = Int(raw_label)
        frac = Float64(fractions[raw_label])
        pts = collect(attractors[label])
        attractor_state = round(Int, sum(Float64(first(p)) for p in pts) / length(pts))
        w = word_of(attractor_state)
        sub = substage_of(attractor_state)
        if w == TARGET_WORD
            parent_fraction += frac
            sub_fractions[SUBSTAGES[sub]] = sub_fractions[SUBSTAGES[sub]] + frac
        end
        push!(rows, Dict(
            "label" => label,
            "fraction" => frac,
            "attractor_state" => attractor_state,
            "attractor_label" => state_label(attractor_state),
            "in_parent_basin" => w == TARGET_WORD,
            "subbasin" => SUBSTAGES[sub],
        ))
    end
    Dict(
        "attractor_count" => length(attractors),
        "parent_basin_fraction" => parent_fraction,
        "subbasin_fractions" => sub_fractions,
        "nonempty_subbasin_count" => count(v -> v > 0, values(sub_fractions)),
        "raw_basin_labels" => [Int(x) for x in basins],
        "attractor_rows" => rows,
        "basin_entropy" => entropy_report(basins),
    )
end

function direct_ratchet_metrics(table::Dict{Int,Int}, nwords::Int, k::Int)
    finals = final_states(table, nwords, k)
    parent_bad = [x for x in states(nwords) if word_of(finals[x]) != TARGET_WORD]
    sub_counts = Dict(sub => 0 for sub in SUBSTAGES)
    for y in values(finals)
        if word_of(y) == TARGET_WORD
            sub_counts[SUBSTAGES[substage_of(y)]] += 1
        end
    end
    energy_deltas = [
        (word_of(table[x]) - TARGET_WORD) - (word_of(x) - TARGET_WORD)
        for x in states(nwords)
    ]
    Dict(
        "parent_bad_reach_count" => length(parent_bad),
        "subbasin_final_counts" => sub_counts,
        "nonempty_subbasin_count" => count(v -> v > 0, values(sub_counts)),
        "max_parent_energy_delta_one_step" => maximum(energy_deltas),
        "strict_parent_energy_decrease_count" => count(d -> d < 0, energy_deltas),
        "fixed_parent_state_count" => count(x -> table[x] == x && word_of(x) == TARGET_WORD, states(nwords)),
    )
end

function rung_report(nwords::Int)
    tabs = transition_tables(nwords)
    nstates = nwords * length(SUBSTAGES)
    k = nwords - 1

    z3_reach = z3_parent_reach_counterexample(tabs["genuine"], nwords, k)
    z3_external_fixed = z3_external_fixed_counterexample(tabs["genuine"], nwords)
    z3_parent_erased = z3_parent_reach_counterexample(tabs["parent_erased"], nwords, k)
    z3_order = z3_order_witness(tabs["parent_ratchet"], tabs["order_refiner"], nwords)
    z3_order_erased = z3_order_witness(tabs["parent_ratchet"], Dict(x => x for x in states(nwords)), nwords)
    z3_subbasins = Dict(SUBSTAGES[sub_i] => z3_subbasin_nonempty(tabs["genuine"], nwords, k, sub_i) for sub_i in 1:length(SUBSTAGES))

    attractors_genuine = map_with_attractors(tabs["genuine"], nwords)
    attractors_parent_erased = map_with_attractors(tabs["parent_erased"], nwords)
    attractors_subbasin_collapsed = map_with_attractors(tabs["subbasin_collapsed"], nwords)
    direct_genuine = direct_ratchet_metrics(tabs["genuine"], nwords, k)
    direct_collapsed = direct_ratchet_metrics(tabs["subbasin_collapsed"], nwords, k)

    order_gap_count = hamming_table(tabs["genuine"], tabs["reverse_order"], nwords)
    order_erased_gap_count = hamming_table(tabs["order_erased_genuine"], tabs["order_erased_reverse"], nwords)

    table_hashes = Dict(name => table_hash(table, nwords) for (name, table) in tabs)
    controls_pass =
        z3_parent_erased["counterexample_exists"] &&
        z3_order["order_sensitive_witness_exists"] &&
        z3_order_erased["commutation_proven"] &&
        attractors_parent_erased["parent_basin_fraction"] < 1.0 &&
        attractors_subbasin_collapsed["nonempty_subbasin_count"] == 1 &&
        length(unique(values(table_hashes))) > 1

    proof_pass =
        z3_reach["proves_all_reach_parent_basin"] &&
        z3_external_fixed["proves_no_external_fixed_point"] &&
        all(row["nonempty_witness_exists"] for row in values(z3_subbasins)) &&
        attractors_genuine["parent_basin_fraction"] == 1.0 &&
        attractors_genuine["nonempty_subbasin_count"] == length(SUBSTAGES) &&
        direct_genuine["parent_bad_reach_count"] == 0 &&
        direct_genuine["max_parent_energy_delta_one_step"] <= 0 &&
        order_gap_count > 0 &&
        order_erased_gap_count == 0 &&
        controls_pass

    Dict(
        "state_count" => nstates,
        "word_count" => nwords,
        "horizon_k" => k,
        "parent_basin_labels" => [state_label(x) for x in parent_basin_states()],
        "z3_parent_reachability" => z3_reach,
        "z3_no_external_fixed_point" => z3_external_fixed,
        "z3_parent_erased_control" => z3_parent_erased,
        "z3_order_sensitive_witness" => z3_order,
        "z3_order_erased_control" => z3_order_erased,
        "z3_subbasin_nonempty" => z3_subbasins,
        "attractors_genuine" => attractors_genuine,
        "attractors_parent_erased_control" => attractors_parent_erased,
        "attractors_subbasin_collapsed_control" => attractors_subbasin_collapsed,
        "direct_ratchet_metrics" => direct_genuine,
        "direct_collapsed_metrics" => direct_collapsed,
        "order_gap_count" => order_gap_count,
        "order_erased_gap_count" => order_erased_gap_count,
        "table_hashes" => table_hashes,
        "controls_pass" => controls_pass,
        "proof_pass" => proof_pass,
    )
end

function main()
    source_hash = source_sha256()
    rungs = Dict{String,Any}()
    for nwords in (2, 4, 8, 16)
        row = rung_report(nwords)
        rungs[string(row["state_count"])] = row
    end
    r64 = rungs["64"]
    all_rungs_pass = all(row["proof_pass"] for row in values(rungs))
    all_pass = all_rungs_pass

    tool_ablations = Dict(
        "parent_ratchet_erased" => Dict(
            "what_changed" => "remove parent word-ratchet A, leaving only the order-sensitive substage refiner B",
            "baseline_parent_bad_reach_count" => r64["direct_ratchet_metrics"]["parent_bad_reach_count"],
            "control_parent_bad_reach_count" => r64["state_count"] - round(Int, r64["attractors_parent_erased_control"]["parent_basin_fraction"] * r64["state_count"]),
            "outcome_delta" => (r64["state_count"] - round(Int, r64["attractors_parent_erased_control"]["parent_basin_fraction"] * r64["state_count"])) - r64["direct_ratchet_metrics"]["parent_bad_reach_count"],
        ),
        "subbasin_selector_collapsed" => Dict(
            "what_changed" => "force every state into the Ti sub-basin before parent ratchet",
            "baseline_nonempty_subbasins" => r64["attractors_genuine"]["nonempty_subbasin_count"],
            "control_nonempty_subbasins" => r64["attractors_subbasin_collapsed_control"]["nonempty_subbasin_count"],
            "outcome_delta" => r64["attractors_genuine"]["nonempty_subbasin_count"] - r64["attractors_subbasin_collapsed_control"]["nonempty_subbasin_count"],
        ),
        "order_erased_refiner" => Dict(
            "what_changed" => "replace order-sensitive refiner B with identity so A and B commute",
            "baseline_order_gap_count" => r64["order_gap_count"],
            "control_order_gap_count" => r64["order_erased_gap_count"],
            "outcome_delta" => r64["order_gap_count"] - r64["order_erased_gap_count"],
        ),
    )

    result = Dict{String,Any}(
        "object_id" => "geometric_constraint_manifold_ratchet_subbasins",
        "sim_id" => "geometric_constraint_manifold_ratchet_subbasins",
        "name" => "Finite geometric-constraint ratchet into parent attractor basin with sub-basins",
        "version" => "0.1.0",
        "generated_at" => string(now(UTC)),
        "source_receipt_coherence" => Dict(
            "source_path" => @__FILE__,
            "source_sha256" => source_hash,
            "coherence_rule" => "Result is stale if source_sha256 does not match the current source file hash.",
        ),
        "tier" => "tool-stage finite proof and attractor-mapping scout",
        "classification" => "formal_scout",
        "sim_execution_kind" => "bridge",
        "sim_class" => "constraint_basin_ratchet_probe",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "one_layer_done_right_candidate" => false,
        "all_pass" => all_pass,

        "purpose" => "Show a finite F01/N01 constraint map that monotonically ratchets every finite state into one parent attractor basin while preserving four nonempty sub-basins.",
        "scientific_question" => "Can a geometric constraint manifold fixture converge under the two root constraints into an attractor basin with sub-basins, and do erased/order/collapse controls break the claim?",
        "claim_ceiling" => "Diagnostic finite proof/mapping scout only. It proves a ratchet/sub-basin pattern on the terrain/operator schedule fixture. It does not admit a PEPS carrier, layer, manifold basin, Axis0, flux, FEP, physics, or final manifold status.",
        "demotion_condition" => "Demote to broken if parent-basin Z3 reachability stops proving UNSAT, if any sub-basin becomes empty, if parent-erased/order-erased/subbasin-collapsed controls stop flipping, if source hash mismatches, or if downstream wording treats this as PEPS/layer/manifold admission.",
        "out_of_scope" => [
            "PEPS2D or PEPS3D carrier construction",
            "spinor-network carrier admission",
            "continuous or infinite-time attractor theorem",
            "Basins.jl Wada/fractal boundary proof",
            "per-layer completion",
            "manifold basin admission",
            "flux/Xi/Phi0/Axis0/FEP/physics claims",
        ],
        "next_lego_target" => "Replace the schedule fixture with one exported terrain/channel carrier map whose states carry real density/channel data, then rerun the same parent/sub-basin proof.",
        "promotion_condition" => "Promotion requires a real target-layer carrier map, PEPS3D or explicit blocked carrier boundary where required, spinor/density carrier evidence, fresh controls, and a passing layer-completion claim gate for completion-like wording.",
        "blocked_until" => "A target layer exports a real carrier transition map with finite states and sub-basin readouts, replacing this schedule fixture.",

        "root_constraints" => [
            "F01 finite carrier/probe/operator/path set: finite (terrain/operator word, substage) states at 8/16/32/64 state rungs",
            "N01 noncommuting/order-sensitive operation/control: parent ratchet A and substage refiner B have A_after_B != B_after_A, while order-erased B=id commutes",
        ],
        "root_constraints_in_force" => [
            "F01 finite distinguishable terrain/operator schedule states",
            "N01 order-sensitive parent/substage composition with Z3 SAT witness and order-erased UNSAT control",
        ],
        "finite_map" => Dict(
            "domain" => "finite states (native_word, substage) over prefixes of 16 terrain/operator words x 4 substages",
            "codomain_or_output" => "next finite state, Z3 parent reachability proof, Attractors parent/sub-basin fractions, and negative-control deltas",
            "map" => "F = A_after_B. A ratchets word index toward target parent word NeTi; B refines substage by a word-dependent order-sensitive shift and becomes identity inside the parent basin.",
        ),
        "domain" => "8/16/32/64 finite terrain/operator schedule states; no continuous, PEPS, spinor, or manifold carrier is claimed",
        "codomain_or_output" => "bounded parent-basin convergence certificate, four sub-basin coverage readout, and controls",

        "carrier_layer" => "finite schedule fixture",
        "geometry_layer" => "terrain/operator order grammar fixture, not a geometric manifold carrier admission",
        "carrier_realization" => "Julia finite transition tables, Z3 SMT queries, DynamicalSystems deterministic maps, and Attractors basin mapping",
        "peps3d_embedding" => "absent; this absence blocks manifold, PEPS3D, flux, Axis0, FEP, physics, and basin-admission consumers",
        "spinor_state" => "not_applicable_to_this_finite_ratchet_scout",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [
            "system_v5/julia_carrier/layers/constraint_basin_synthesis_terrain64_results.json",
            "system_v5/julia_carrier/layers/attractors_constraint_basin_same_map_bridge_results.json",
            "system_v5/julia_carrier/layers/attractors_constraint_basin_empirical_scout_results.json",
        ],
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
            "proof-pattern design for exported carrier maps",
            "bounded comparison against terrain/operator and Attractors basin scouts",
        ],

        "law_or_candidate_tested" => "F01/N01 constraints ratchet all finite states into one parent attractor basin with four nonempty sub-basins",
        "branch_status_before_run" => "ratchet_subbasin_scout_not_admission",
        "allowed_claims" => [
            "The finite schedule fixture has Z3-certified bounded convergence into a parent basin.",
            "Attractors maps the genuine 64-state ratchet to a parent basin fraction of 1.0 with four nonempty sub-basins.",
            "Parent-erased, order-erased, and sub-basin-collapsed controls flip distinct parts of the claim.",
            "promotion_allowed=false; no layer, manifold, PEPS, flux, Axis0, FEP, bridge admission, or physics claim is made.",
        ],
        "promotion_blockers" => [
            "finite schedule fixture only",
            "no PEPS2D or PEPS3D carrier",
            "no spinor-network or spinor-derived density carrier",
            "no exported per-layer carrier map",
            "no layer-completion claim gate",
        ],

        "required_tools" => collect(keys(TOOL_MANIFEST)),
        "actual_tools_used" => collect(keys(TOOL_MANIFEST)),
        "proof_surfaces_used" => ["Z3 parent reachability", "Z3 no external fixed point", "Z3 order witness", "Z3 sub-basin nonempty witnesses"],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "backend_primary_result" => Dict(
            "backend" => "Julia + Z3 + Attractors.jl + DynamicalSystems.jl",
            "claim_bearing" => true,
            "claim_scope" => "finite ratchet/sub-basin proof-pattern scout only; not proof promotion or admission",
            "all_pass" => all_pass,
            "summary" => "Z3 proves bounded finite parent-basin reachability and controls; Attractors maps the finite table into parent/sub-basin fractions.",
        ),

        "required_inputs" => ["16 native words", "4 substages", "parent ratchet A", "word-dependent substage refiner B", "8/16/32/64 state rungs"],
        "data_or_artifact_dependencies" => [],
        "required_negatives" => ["parent_ratchet_erased", "order_erased_refiner", "subbasin_selector_collapsed", "bit_identical_control_check"],
        "negatives_run" => ["parent_ratchet_erased", "order_erased_refiner", "subbasin_selector_collapsed", "bit_identical_control_check"],
        "kill_conditions" => [
            "genuine parent-basin reachability query becomes SAT",
            "external fixed-point query becomes SAT",
            "any parent sub-basin has no witness",
            "Attractors maps genuine table to parent fraction below 1.0",
            "order-erased control remains order-sensitive",
            "sub-basin-collapsed control still has four nonempty sub-basins",
            "control table hashes are bit-identical",
        ],

        "scale_ladder" => Dict("rungs" => rungs),
        "controls" => Dict(
            "parent_erased_control_64" => r64["z3_parent_erased_control"],
            "order_erased_control_64" => r64["z3_order_erased_control"],
            "subbasin_collapsed_control_64" => r64["attractors_subbasin_collapsed_control"],
            "bit_identical_control_check_64" => r64["table_hashes"],
        ),
        "tool_ablations" => tool_ablations,
        "z3_proof" => Dict(
            "ratchet64" => Dict(
                "parent_reachability" => r64["z3_parent_reachability"],
                "no_external_fixed_point" => r64["z3_no_external_fixed_point"],
                "order_sensitive_witness" => r64["z3_order_sensitive_witness"],
                "order_erased_control" => r64["z3_order_erased_control"],
                "subbasin_nonempty" => r64["z3_subbasin_nonempty"],
            ),
            "load_bearing" => all_pass,
        ),
        "entropy_as_output" => Dict(
            "genuine_64" => r64["attractors_genuine"]["basin_entropy"],
            "subbasin_collapsed_64" => r64["attractors_subbasin_collapsed_control"]["basin_entropy"],
            "boundary" => "Attractors.basin_entropy diagnostic only; no Wada/fractal claim",
        ),
        "decorative_tool_name_overclaim_guard" => Dict(
            "Z3" => "load_bearing for finite bounded proof only; not continuous/manifold admission",
            "Attractors" => "load_bearing for finite table basin labels/fractions/entropy only; not a proof engine",
            "DynamicalSystems" => "load_bearing for deterministic map execution only; not a carrier admission",
            "shared_premise_tested" => "Removing parent ratchet prevents full parent-basin convergence; collapsing sub-basin selector removes sub-basin coverage; order-erased selector removes N01 gap.",
            "bit_identical_controls_checked" => "64-state table hashes differ across genuine, parent-erased, order-erased, and sub-basin-collapsed tables.",
        ),

        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "geometric_constraint_manifold_ratchet_subbasins:F01_N01_parent_basin_subbasins",
        "result_summary" => Dict(
            "all_rungs_pass" => all_rungs_pass,
            "state_rungs" => sort(collect(keys(rungs)); by = x -> parse(Int, x)),
            "parent_basin_fraction_64" => r64["attractors_genuine"]["parent_basin_fraction"],
            "nonempty_subbasin_count_64" => r64["attractors_genuine"]["nonempty_subbasin_count"],
            "subbasin_fractions_64" => r64["attractors_genuine"]["subbasin_fractions"],
            "parent_erased_parent_fraction_64" => r64["attractors_parent_erased_control"]["parent_basin_fraction"],
            "collapsed_nonempty_subbasin_count_64" => r64["attractors_subbasin_collapsed_control"]["nonempty_subbasin_count"],
            "order_gap_count_64" => r64["order_gap_count"],
            "order_erased_gap_count_64" => r64["order_erased_gap_count"],
            "source_sha256" => source_hash,
        ),
        "summary" => Dict(
            "all_pass" => all_pass,
            "sim_execution_kind" => "bridge",
            "tests_passed" => all_pass ? 1 : 0,
            "tests_total" => 1,
        ),
        "pass_rule" => "All 8/16/32/64 rungs must prove parent-basin reachability, no external fixed points, four nonempty sub-basins, Attractors parent fraction 1.0, nonzero N01 order gap, zero order-erased gap, and flipping controls.",
        "fail_rule" => "Any missing proof, empty sub-basin, failed Attractors parent fraction, bit-identical control, missing source hash match, or promotion-like downstream claim fails the scout.",
        "promotion_status" => "diagnostic_only",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("geometric_constraint_manifold_ratchet_subbasins")
    println("  result: ", RESULT_PATH)
    println("  all_pass: ", all_pass)
    println("  parent basin fraction 64: ", r64["attractors_genuine"]["parent_basin_fraction"])
    println("  nonempty subbasins 64: ", r64["attractors_genuine"]["nonempty_subbasin_count"])
    println("  parent-erased parent fraction 64: ", r64["attractors_parent_erased_control"]["parent_basin_fraction"])
    println("  collapsed subbasins 64: ", r64["attractors_subbasin_collapsed_control"]["nonempty_subbasin_count"])
    println("  order gap 64: ", r64["order_gap_count"])
    exit(all_pass ? 0 : 1)
end

main()
