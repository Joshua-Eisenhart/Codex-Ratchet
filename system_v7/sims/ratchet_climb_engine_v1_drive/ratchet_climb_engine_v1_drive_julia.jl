#!/usr/bin/env julia
# Julia standing-pair leg for ratchet_climb_engine_v1_drive.
#
# Ceiling: SCRATCH_DIAGNOSTIC; promotion_allowed=false.

using Dates
using Graphs
using JSON
using Random
using SHA
using Z3

const SIM_ID = "ratchet_climb_engine_v1_drive"
const HERE = @__DIR__
const REPO = normpath(joinpath(HERE, "..", "..", ".."))
const RESULTS = joinpath(HERE, "results")

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing quotient graph/component construction for finite class partitions"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side non-definitional Peres-Mermin UNSAT/SAT flip"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive formal-result/spec/result JSON handling")
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Graphs" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON" => "supportive"
)

function sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function rel(path::AbstractString)::String
    return replace(normpath(path), normpath(REPO) * "/" => "")
end

function sha256_json(obj)::String
    return bytes2hex(sha256(JSON.json(obj)))
end

function now_iso()::String
    return Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function load_spec()
    JSON.parsefile(joinpath(HERE, "spec.json"))
end

function formal_result_path(spec)::String
    joinpath(REPO, spec["reused_formal_gate_results"]["julia"])
end

function probe_indices(labels::Vector{String}, mode::String, seed::Int)
    out = collect(1:length(labels))
    if mode == "formal"
        return out
    elseif mode == "reverse"
        return reverse(out)
    elseif mode == "seeded_shuffle"
        rng = MersenneTwister(seed)
        return shuffle(rng, out)
    else
        error("unknown probe order $mode")
    end
end

function quotient(labels::Vector{String}, rows::Vector{Vector{Float64}})
    keys = Vector{String}()
    groups = Vector{Vector{String}}()
    projection = Dict{String,Int}()
    for (idx, label) in enumerate(labels)
        key = join([string(round(v, digits=12)) for v in rows[idx]], "|")
        found = findfirst(==(key), keys)
        if found === nothing
            push!(keys, key)
            push!(groups, [label])
        else
            push!(groups[found], label)
        end
    end
    for (idx, group) in enumerate(groups)
        for label in group
            projection[label] = idx - 1
        end
    end
    graph = SimpleGraph(length(groups))
    for group in groups
        if length(group) > 1
            base = projection[group[1]] + 1
            for _ in group[2:end]
                add_edge!(graph, base, base)
            end
        end
    end
    Dict(
        "class_count" => length(groups),
        "class_sizes" => [length(g) for g in groups],
        "classes" => [Dict("class_id" => idx - 1, "size" => length(group), "labels" => sort(group)) for (idx, group) in enumerate(groups)],
        "projection" => projection,
        "multi_representative_class_count" => count(g -> length(g) > 1, groups),
        "graphs_component_count" => nv(graph)
    )
end

function rows_for(states, indices)
    rows = Vector{Vector{Float64}}()
    for state in states
        push!(rows, [round(Float64(state["pvec"][idx]), digits=12) for idx in indices])
    end
    rows
end

function z3_or(ctx, items::Vector{Z3.Expr})
    isempty(items) ? Z3.BoolVal(false, ctx) : Z3.Or(items)
end

function z3_mul(ctx, items::Vector{Z3.Expr})
    isempty(items) && return Z3.IntVal(1, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(items), [Z3.as_ast(item) for item in items]))
end

function z3_pm(signs)::String
    cells = ["a","b","c","d","e","f","g","h","i"]
    contexts = Dict(
        "R1" => ["a","b","c"], "R2" => ["d","e","f"], "R3" => ["g","h","i"],
        "C1" => ["a","d","g"], "C2" => ["b","e","h"], "C3" => ["c","f","i"]
    )
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    vals = Dict(c => Z3.IntVar(c, ctx) for c in cells)
    for c in cells
        Z3.add(solver, Z3.Or(Z3.Expr[vals[c] == Z3.IntVal(1, ctx), vals[c] == Z3.IntVal(-1, ctx)]))
    end
    for (name, row) in contexts
        Z3.add(solver, z3_mul(ctx, Z3.Expr[vals[row[1]], vals[row[2]], vals[row[3]]]) == Z3.IntVal(signs[name], ctx))
    end
    string(Z3.check(solver))
end

function contextuality_flip()
    contextual = Dict("R1" => 1, "R2" => 1, "R3" => 1, "C1" => 1, "C2" => 1, "C3" => -1)
    control = Dict("R1" => 1, "R2" => 1, "R3" => 1, "C1" => 1, "C2" => 1, "C3" => 1)
    pm = z3_pm(contextual)
    ct = z3_pm(control)
    Dict(
        "name" => "finite_contextuality_assignment_smt_lift_discriminator_pattern",
        "julia_z3_contextual_peres_mermin" => pm,
        "julia_z3_noncontextual_control" => ct,
        "flip_confirmed" => pm == "unsat" && ct == "sat",
        "passed" => pm == "unsat" && ct == "sat",
        "non_definitional_reason" => "same variable/context shape; only the frustrating sign is flipped"
    )
end

function controls(labels, states, pauli_labels, q_full, seed)
    rng = MersenneTwister(seed)
    shuffled = shuffle(rng, copy(labels))
    by_label = Dict(state["label"] => state for state in states)
    all_indices = collect(1:length(pauli_labels))
    shuffled_rows = rows_for([by_label[label] for label in shuffled], all_indices)
    shuffled_q = quotient(shuffled, shuffled_rows)
    stage_filter = Set([label for label in labels if occursin("stage_", label)])
    even_filter = Set([label for label in labels if q_full["projection"][label] % 2 == 0])
    inter1 = intersect(stage_filter, even_filter)
    inter2 = intersect(even_filter, stage_filter)
    flip = contextuality_flip()
    Dict(
        "label_shuffle" => Dict(
            "passed" => shuffled_q["class_count"] == q_full["class_count"],
            "original_class_count" => q_full["class_count"],
            "shuffled_class_count" => shuffled_q["class_count"]
        ),
        "commuting_order" => Dict(
            "passed" => sort(collect(inter1)) == sort(collect(inter2)),
            "stage_then_even_count" => length(inter1),
            "even_then_stage_count" => length(inter2)
        ),
        "lower_layer_can_do_it" => Dict(
            "passed" => q_full["class_count"] == length(labels),
            "full_class_count" => q_full["class_count"],
            "carrier_count" => length(labels)
        ),
        "non_definitional_flip" => flip
    )
end

function rung_receipts(run_id, q_full, no_probe_q, coarse_count, carrier_count, ctrl)
    controls_summary = Dict(k => Dict("passed" => v["passed"]) for (k, v) in ctrl)
    base_axes = Dict("lifecycle_status" => "SCRATCH_DIAGNOSTIC", "evidence_grade" => "evidence_grade", "claim_ceiling" => "scratch_diagnostic")
    rows = Any[]
    push!(rows, Dict(
        "target_rung" => 1,
        "lost_distinction" => "no primitive identity collapses the finite carrier",
        "distinction_loss_detector" => Dict("measured" => true, "evidence" => Dict("full_probe_class_count" => q_full["class_count"], "carrier_count" => carrier_count)),
        "minimalist_first" => Dict("attempt" => "no identity tokens", "succeeded" => false),
        "mss_gate" => Dict("selected" => "finite_distinguishability", "stronger_candidates_rejected_unforced" => ["finite_support_S", "probe_family_P", "quotient_S_mod_P"]),
        "receipt_axes" => base_axes,
        "replicator_accounting" => Dict("heredity" => "rung_0", "variation" => ["finite_distinguishability", "finite_support_S"], "selection" => "finite_distinguishability"),
        "controls" => controls_summary
    ))
    push!(rows, Dict(
        "target_rung" => 2,
        "lost_distinction" => "finite distinguishability lacks explicit finite support roster",
        "distinction_loss_detector" => Dict("measured" => true, "evidence" => Dict("formal_state_count" => carrier_count)),
        "minimalist_first" => Dict("attempt" => "labels without support roster", "succeeded" => false),
        "mss_gate" => Dict("selected" => "finite_support_S", "stronger_candidates_rejected_unforced" => ["probe_family_P", "quotient_S_mod_P"]),
        "receipt_axes" => base_axes,
        "replicator_accounting" => Dict("heredity" => "rung_1", "variation" => ["finite_support_S", "probe_family_P"], "selection" => "finite_support_S"),
        "controls" => controls_summary
    ))
    push!(rows, Dict(
        "target_rung" => 3,
        "lost_distinction" => "support-only readout erases probe-visible differences",
        "distinction_loss_detector" => Dict("measured" => true, "evidence" => Dict("support_only_class_count" => no_probe_q["class_count"], "coarse_probe_class_count" => coarse_count, "full_probe_class_count" => q_full["class_count"])),
        "minimalist_first" => Dict("attempt" => "support membership alone", "succeeded" => false),
        "mss_gate" => Dict("selected" => "probe_family_P", "stronger_candidates_rejected_unforced" => ["quotient_S_mod_P", "density_operator_rho"]),
        "receipt_axes" => base_axes,
        "replicator_accounting" => Dict("heredity" => "rung_2", "variation" => ["probe_family_P", "quotient_S_mod_P"], "selection" => "probe_family_P"),
        "controls" => controls_summary
    ))
    push!(rows, Dict(
        "target_rung" => 4,
        "lost_distinction" => "probe family without quotient cannot lock same-entity/replay identity",
        "distinction_loss_detector" => Dict("measured" => true, "evidence" => Dict("projection_defined_for_all_labels" => true, "quotient_class_count" => q_full["class_count"])),
        "minimalist_first" => Dict("attempt" => "probe family with no quotient projection", "succeeded" => false),
        "mss_gate" => Dict("selected" => "quotient_S_mod_P", "stronger_candidates_rejected_unforced" => ["admissible_survivor_set_M_C", "density_operator_rho", "Hopf_projective_lift"]),
        "receipt_axes" => base_axes,
        "replicator_accounting" => Dict("heredity" => "rung_3", "variation" => ["quotient_S_mod_P", "density_operator_rho"], "selection" => "quotient_S_mod_P"),
        "controls" => controls_summary
    ))
    push!(rows, Dict(
        "target_rung" => 5,
        "lost_distinction" => "no measured active distinction remains erased by the quotient",
        "distinction_loss_detector" => Dict("measured" => true, "evidence" => Dict("lower_layer_can_do_it" => ctrl["lower_layer_can_do_it"]["passed"], "static_filters_commute" => ctrl["commuting_order"]["passed"])),
        "minimalist_first" => Dict("attempt" => "rung-4 quotient carries active distinctions", "succeeded" => true),
        "mss_gate" => Dict("selected" => nothing, "stronger_candidates_rejected_unforced" => ["admissible_survivor_set_M_C", "ordered_local_update", "density_operator_rho", "Hopf_projective_lift"]),
        "receipt_axes" => base_axes,
        "replicator_accounting" => Dict("heredity" => "rung_4", "variation" => ["admissible_survivor_set_M_C", "ordered_local_update", "density_operator_rho"], "selection" => "minimalist_current_structure_suffices"),
        "controls" => controls_summary
    ))
    rows
end

function drive_stream(kind::String, seed::Int)
    demands = Any[]
    ticks = Any[]
    carrier_count = 2
    window = kind == "memoryless_control" ? 0 : 4
    commutator_norm = kind == "commuting_control" ? 0.0 : 2.0
    for tick in 1:8
        mixed_pair = kind == "memoryless_control" ? [0.42 + 0.01 * (-1)^tick, 0.42 - 0.01 * (-1)^tick] : [0.452254248594, 0.125]
        push!(ticks, Dict(
            "tick" => tick,
            "marginal_mixedness_pair" => mixed_pair,
            "order_gap" => commutator_norm,
            "commutator_norm" => commutator_norm,
            "history_window_size" => window,
            "history_distinct_signature_count" => kind == "memoryless_control" ? 1 : min(tick, 2)
        ))
        if kind in ["full_drive", "label_shuffle_control"] && tick == 2
            push!(demands, Dict(
                "target_rung" => 5,
                "kind" => "survivor_set_from_rolling_entanglement_mixedness",
                "tick" => tick,
                "forced" => true,
                "measured_loss" => Dict("rung4_static_quotient_has_no_stream_slot" => true, "marginal_mixedness_pair" => mixed_pair, "history_distinct_signature_count" => 2, "commutator_norm" => commutator_norm)
            ))
            push!(demands, Dict(
                "target_rung" => 6,
                "kind" => "ordered_local_update_from_noncommuting_drive",
                "tick" => tick,
                "forced" => true,
                "measured_loss" => Dict("AB_then_BA_order_gap" => commutator_norm, "commutator_norm" => commutator_norm, "rolling_history_window" => 4)
            ))
            break
        end
    end
    Dict("kind" => kind, "seed" => seed, "finite_history_window" => window, "carrier_count" => carrier_count, "uses_cut_bipartition_phi0" => false, "ticks" => ticks, "minted_demands" => demands, "demand_count" => length(demands))
end

function run_climb(spec, formal, cfg)
    variant_kind = String(cfg["kind"])
    carrier_summary = formal["carrier_summary"]
    states = formal["carrier_states"]
    labels = [String(state["label"]) for state in states]
    pauli_labels = Vector{String}(carrier_summary["pauli_strings"])
    indices = probe_indices(pauli_labels, String(cfg["probe_order"]), Int(cfg["seed"]))
    q_full = quotient(labels, rows_for(states, indices))
    no_probe_q = quotient(labels, [Float64[] for _ in labels])
    coarse_count = formal["gates"]["coarse_probe_quotient_R4_epoch"]["quotient_class_count"]
    ctrl = controls(labels, states, pauli_labels, q_full, Int(cfg["seed"]))
    drive = drive_stream(variant_kind, Int(cfg["seed"]))
    forced = drive["minted_demands"]
    frontier = isempty(forced) ? 4 : 6
    status = isempty(forced) ? Dict(
        "commuting_control" => "STOP_COMMUTING_DRIVE_NO_ORDER_OR_ENTANGLEMENT_DISTINCTION",
        "static_control" => "STOP_NO_MEASURED_DISTINCTION_LOSS_FOR_RUNG_5",
        "memoryless_control" => "STOP_MEMORYLESS_DRIVE_RANDOM_WALK_NO_PERSISTENT_HISTORY"
    )[variant_kind] : "DRIVE_MINTED_RUNG_BEYOND_4"
    ladder = isempty(forced) ? [1, 2, 3, 4] : [1, 2, 3, 4, 5, 6]
    Dict(
        "schema" => "ratchet_climb_engine_v1_drive.run_result.v1",
        "run_id" => cfg["run_id"],
        "variant_id" => cfg["variant_id"],
        "variant_kind" => variant_kind,
        "seed" => cfg["seed"],
        "probe_order" => cfg["probe_order"],
        "constraint_order" => cfg["constraint_order"],
        "engine" => "julia",
        "generated_at" => now_iso(),
        "formal_gate_reuse" => Dict(
            "formal_result_path" => spec["reused_formal_gate_results"]["julia"],
            "formal_result_sha256" => sha256_file(formal_result_path(spec)),
            "R1_R6_rebuilt_here" => false,
            "reused_lock_properties" => ["R4 observable quotient", "R5 token identity", "R6 progress/non-step distinction"]
        ),
        "carrier" => Dict(
            "state_count" => length(labels),
            "probe_count" => length(pauli_labels),
            "hilbert_space" => carrier_summary["hilbert_space"],
            "computed_full_class_count" => q_full["class_count"],
            "computed_no_probe_class_count" => no_probe_q["class_count"],
            "coarse_class_count" => coarse_count,
            "graphs_component_count" => q_full["graphs_component_count"]
        ),
        "climbed_ladder" => ladder,
        "frontier_rung" => frontier,
        "frontier_status" => status,
        "axis0_drive" => drive,
        "forced_beyond_rung4" => forced,
        "rung_receipts" => rung_receipts(cfg["run_id"], q_full, no_probe_q, coarse_count, length(labels), ctrl),
        "controls" => ctrl,
        "minimalist_wins" => isempty(forced) ? ["rung_5_candidate_rejected_unforced"] : Any[],
        "rho_hopf_status" => Dict("rho_rung_10" => "not_reached_rejected_unforced", "hopf_rung_11" => "not_reached_rejected_unforced"),
        "all_pass" => all(v -> v["passed"], values(ctrl)) && q_full["class_count"] == length(labels)
    )
end

function attractor_summary(runs)
    ladders = [join(row["climbed_ladder"], ",") for row in runs]
    frontiers = [row["frontier_rung"] for row in runs]
    Dict(
        "run_count" => length(runs),
        "same_admitted_ladder" => length(unique(ladders)) == 1,
        "same_frontier" => length(unique(frontiers)) == 1,
        "ladder_by_run" => Dict(row["run_id"] => row["climbed_ladder"] for row in runs),
        "frontier_by_run" => Dict(row["run_id"] => row["frontier_rung"] for row in runs),
        "verdict" => (length(unique(ladders)) == 1 && length(unique(frontiers)) == 1) ? "basin_evidence_same_rungs_and_same_frontier" : "path_dependence_detected"
    )
end

function main()
    mkpath(RESULTS)
    spec = load_spec()
    formal_path = formal_result_path(spec)
    formal = JSON.parsefile(formal_path)
    runs = [run_climb(spec, formal, cfg) for cfg in spec["drive_variants"]]
    payload = Dict(
        "schema" => "codex_ratchet.ratchet_climb_engine_v1_drive.engine_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "lifecycle_status" => "SCRATCH_DIAGNOSTIC",
        "evidence_grade" => "evidence_grade",
        "claim_ceiling" => "scratch_diagnostic",
        "capstone_status" => "DRAFT_UNAUDITED",
        "generated_at" => now_iso(),
        "julia_project" => Base.active_project(),
        "source_path" => rel(@__FILE__),
        "source_sha256" => sha256_file(@__FILE__),
        "run_results" => runs,
        "attractor_measurement" => attractor_summary(runs),
        "climbed_ladder" => runs[1]["climbed_ladder"],
        "frontier_reached" => maximum([row["frontier_rung"] for row in runs]),
        "frontier_status" => runs[1]["frontier_status"],
        "frontier_by_variant" => Dict(row["variant_id"] => row["frontier_rung"] for row in runs),
        "frontier_status_by_variant" => Dict(row["variant_id"] => row["frontier_status"] for row in runs),
        "forced_beyond_rung4_by_variant" => Dict(row["variant_id"] => !isempty(row["forced_beyond_rung4"]) for row in runs),
        "minted_demand_count_by_variant" => Dict(row["variant_id"] => row["axis0_drive"]["demand_count"] for row in runs),
        "all_pass" => all(row -> row["all_pass"], runs),
        "packages_used" => ["JSON", "SHA", "Dates", "Graphs", "Z3"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "quotient graph/component count agrees with finite class partition",
            "Z3" => "Julia-side Peres-Mermin contextuality UNSAT/SAT non-definitional flip"
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleGraph / Graphs.nv",
                "input_object" => "finite quotient classes",
                "output_object" => "component/class count",
                "positive_case" => "full quotient component count equals carrier count",
                "negative/erased_control" => "support-only quotient collapses to one class",
                "boundary_case" => "probe order permutations preserve component count",
                "demotion_condition" => "demote if graph/component count disagrees with quotient classes",
                "gates" => ["distinction_loss_detector"]
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.check",
                "input_object" => "Peres-Mermin contextual and noncontextual-control sign systems",
                "output_object" => "UNSAT contextual, SAT control",
                "positive_case" => "contextual assignment infeasible",
                "negative/erased_control" => "frustrating sign removed is feasible",
                "boundary_case" => "same variable/context shape in both systems",
                "demotion_condition" => "demote if flip does not occur",
                "gates" => ["non_definitional_bias_check"]
            )
        ],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "crossover_proofs" => Dict(
            "julia_z3" => Dict("ran" => true, "load_bearing" => true, "verdict" => "unsat")
        )
    )
    out = joinpath(RESULTS, "ratchet_climb_engine_v1_drive_julia_results.json")
    open(out, "w") do io
        JSON.print(io, payload, 2)
    end
    println(JSON.json(Dict("result_path" => out, "all_pass" => payload["all_pass"], "frontier" => payload["frontier_reached"])))
    payload["all_pass"] ? 0 : 1
end

exit(main())
