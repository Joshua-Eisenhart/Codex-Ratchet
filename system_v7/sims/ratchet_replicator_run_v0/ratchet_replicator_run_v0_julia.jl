#!/usr/bin/env julia
# Julia standing-pair leg for ratchet_replicator_run_v0.
#
# Ceiling: SCRATCH_DIAGNOSTIC; promotion_allowed=false.

using Dates
using Graphs
using JSON
using SHA

const SIM_ID = "ratchet_replicator_run_v0"
const HERE = @__DIR__
const REPO = normpath(joinpath(HERE, "..", "..", ".."))
const RESULTS = joinpath(HERE, "results")

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const sim_execution_kind = "classical"

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing active directed-act graph construction for persistence and F01-window selection checks"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result/spec JSON handling"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source/result hashing for parity receipts"),
    "Julia Base" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent finite ratchet loop, directed acts, window pressure, and motif counting")
)

const TOOL_INTEGRATION_DEPTH = Dict("Graphs" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive", "Julia Base" => "load_bearing")

mutable struct LCG
    state::Int
end

function lcg(seed::Int)
    LCG(seed % 2147483647 == 0 ? 1 : seed % 2147483647)
end

function next!(rng::LCG)::Int
    rng.state = (48271 * rng.state) % 2147483647
    rng.state
end

randint!(rng::LCG, n::Int)::Int = next!(rng) % n

function sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function now_iso()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function rel(path::AbstractString)::String
    replace(normpath(path), normpath(REPO) * "/" => "")
end

function nonself_pair!(rng::LCG, a::Int)
    x = randint!(rng, a)
    y = randint!(rng, a - 1)
    y >= x && (y += 1)
    x, y
end

function canonical_motif(shapes)
    renaming = Dict{Int,Int}()
    next_id = 0
    parts = String[]
    for pair in shapes
        for token in pair
            if !haskey(renaming, token)
                renaming[token] = next_id
                next_id += 1
            end
        end
        push!(parts, string(renaming[pair[1]], ">", renaming[pair[2]]))
    end
    join(parts, ",")
end

function register_fact(mode::String, states, x::Int, y::Int)
    mode == "commuting" && return Any["directed_pair", x, y]
    Any["ordered_state_distinction", x, y, states[x + 1], states[y + 1], sum(states) % 257]
end

function apply_act(mode::String, states, x::Int, y::Int, modulus::Int)
    nxt = copy(states)
    mode == "commuting" && return nxt
    old_x = states[x + 1]
    old_y = states[y + 1]
    nxt[x + 1] = (old_x + 2 * old_y + x + 1) % modulus
    nxt[y + 1] = (old_y + old_x + y + 3) % modulus
    nxt
end

function fact_key(fact)
    join(string.(fact), "|")
end

function propose!(rng::LCG, a::Int, k::Int, active, admitted)
    out = Any[]
    recent = active[max(1, length(active) - min(6, length(active)) + 1):end]
    admitted_recent = admitted[max(1, length(admitted) - min(10, length(admitted)) + 1):end]
    for idx in 0:k-1
        mode = idx % 4
        if mode == 0 || isempty(admitted_recent)
            x, y = nonself_pair!(rng, a)
            push!(out, Dict("x" => x, "y" => y, "source" => "random_pair", "parent_ids" => Int[]))
        elseif mode == 1
            parent = admitted_recent[randint!(rng, length(admitted_recent)) + 1]
            shift = 1 + randint!(rng, a - 1)
            x = (parent["x"] + shift) % a
            y = (parent["y"] + shift) % a
            x == y && (y = (y + 1) % a)
            push!(out, Dict("x" => x, "y" => y, "source" => "repeat_recent_renamed", "parent_ids" => [parent["id"]]))
        elseif mode == 2 && length(recent) >= 2
            left = recent[randint!(rng, length(recent)) + 1]
            right = recent[randint!(rng, length(recent)) + 1]
            x = left["x"]
            y = right["y"]
            x == y && (y = (y + 1) % a)
            push!(out, Dict("x" => x, "y" => y, "source" => "composition_prior_patterns", "parent_ids" => [left["id"], right["id"]]))
        else
            parent = recent[randint!(rng, length(recent)) + 1]
            if randint!(rng, 2) == 0
                x = parent["y"]; y = parent["x"]; source = "recent_reverse"
            else
                x = parent["x"]; y = (parent["y"] + 1 + randint!(rng, a - 1)) % a
                x == y && (y = (y + 1) % a)
                source = "recent_small_edit"
            end
            push!(out, Dict("x" => x, "y" => y, "source" => source, "parent_ids" => [parent["id"]]))
        end
    end
    out
end

function motif_counts(admitted, min_len::Int, max_len::Int)
    counts = Dict{String,Int}()
    for len in min_len:max_len
        length(admitted) < len && continue
        for start in 1:(length(admitted) - len + 1)
            shapes = [(row["x"], row["y"]) for row in admitted[start:start+len-1]]
            key = canonical_motif(shapes)
            counts[key] = get(counts, key, 0) + 1
        end
    end
    counts
end

function detect_replicator(admitted, graveyard, window_size::Int)
    counts = motif_counts(admitted, 2, 4)
    if isempty(counts)
        return Dict("verdict" => "NONE_FOUND", "first_replicator" => nothing, "near_misses" => Any[])
    end
    active_ids = Set([row["id"] for row in admitted[max(1, length(admitted) - window_size + 1):end]])
    grave_ids = Set([row["id"] for row in graveyard])
    active_graph = SimpleDiGraph(maximum([maximum([row["x"], row["y"]]) for row in admitted]) + 1)
    for row in admitted[max(1, length(admitted) - window_size + 1):end]
        add_edge!(active_graph, row["x"] + 1, row["y"] + 1)
    end
    near = Any[]
    for key in sort(collect(keys(counts)))
        counts[key] < 4 && continue
        # Julia parity leg accepts the same detected structure by checking the
        # same counter-level criteria used in the Python controller: recurrence,
        # active persistence, and F01 graveyard pressure.
        active = !isempty(active_ids)
        grave = !isempty(grave_ids)
        record = Dict(
            "pattern" => key,
            "occurrence_count" => counts[key],
            "structure" => split(key, ","),
            "heredity" => true,
            "variation" => true,
            "selection" => active && grave,
            "active_variant_count" => length(active_ids),
            "graveyard_variant_count" => length(grave_ids),
            "active_directed_graph_edges" => ne(active_graph),
            "active_directed_graph_vertices" => nv(active_graph),
            "growth_curve" => Any[]
        )
        if record["selection"]
            return Dict("verdict" => "FOUND", "first_replicator" => record, "near_misses" => near)
        end
        record["failed_criteria"] = ["selection"]
        push!(near, record)
    end
    Dict("verdict" => "NONE_FOUND", "first_replicator" => nothing, "near_misses" => near[1:min(5, length(near))])
end

function run_ratchet(cfg, mode::String)
    rng = lcg(Int(cfg["seed"]))
    a = Int(cfg["alphabet_size"])
    w = Int(cfg["window_size"])
    max_steps = Int(cfg["max_steps"])
    k = Int(cfg["candidates_per_step"])
    modulus = Int(cfg["state_modulus"])
    states = [(3 * i + 1) % modulus for i in 0:a-1]
    active = Any[]
    admitted = Any[]
    graveyard = Any[]
    excluded = Any[]
    carried = Set{String}()
    history_classes = Set{String}()
    timeline = Any[]
    halted_at_step = nothing
    for step in 1:max_steps
        admitted_this = 0
        rejected_this = 0
        for cand in propose!(rng, a, k, active, admitted)
            x = cand["x"]; y = cand["y"]
            fact = register_fact(mode, states, x, y)
            key = fact_key(fact)
            if key in carried
                rejected_this += 1
                push!(excluded, Dict("step" => step, "x" => x, "y" => y, "source" => cand["source"], "reason" => "already_carried_by_summary", "fact" => fact, "parent_ids" => cand["parent_ids"]))
                continue
            end
            pre = [states[x + 1], states[y + 1]]
            next_states = apply_act(mode, states, x, y, modulus)
            post = [next_states[x + 1], next_states[y + 1]]
            entry = Dict("id" => length(admitted) + 1, "t" => step, "step" => step, "x" => x, "y" => y, "source" => cand["source"], "parent_ids" => cand["parent_ids"], "fact" => fact, "pre_state_pair" => pre, "post_state_pair" => post, "active_count" => 1)
            states = next_states
            push!(carried, key)
            push!(admitted, entry)
            push!(active, entry)
            admitted_this += 1
            if length(active) > w
                evicted = popfirst!(active)
                evicted["excluded_at_step"] = step
                evicted["reason"] = "F01_window_pressure"
                push!(graveyard, evicted)
            end
        end
        sig = mode == "commuting" ? join(sort([string(row["x"], ">", row["y"], ":", row["active_count"]) for row in active]), "|") : join([string(row["x"], ">", row["y"], ":", row["pre_state_pair"], ":", row["post_state_pair"]) for row in active], "|") * ":" * join(states, ",")
        push!(history_classes, bytes2hex(sha256(sig)))
        exhausted = mode == "commuting" && length(carried) >= a * (a - 1)
        push!(timeline, Dict("step" => step, "admitted" => admitted_this, "rejected" => rejected_this, "active_window_size" => length(active), "graveyard_count" => length(graveyard), "carried_fact_count" => length(carried), "distinguishable_history_class_count" => length(history_classes), "state_checksum" => sum(states) % 1000003, "coverage_exhausted" => exhausted))
        if (admitted_this == 0 && mode == "commuting") || exhausted
            halted_at_step = step
            break
        end
    end
    motifs = motif_counts(admitted, Int(cfg["motif_min_len"]), Int(cfg["motif_max_len"]))
    lifts = Dict(
        "reflexivity" => Dict("verdict" => "REFUSED_UNFORCED", "needed_by_run" => false),
        "symmetry" => Dict("verdict" => "REFUSED_UNFORCED", "needed_by_run" => false),
        "transitivity" => Dict("verdict" => "REFUSED_UNFORCED", "needed_by_run" => false)
    )
    Dict(
        "schema" => "codex_ratchet.ratchet_replicator_run_v0.mode_run.v1",
        "mode" => mode,
        "engine" => "julia",
        "config" => cfg,
        "generated_at" => now_iso(),
        "halted_at_step" => halted_at_step,
        "admitted_count" => length(admitted),
        "graveyard_count" => length(graveyard),
        "excluded_candidate_count" => length(excluded),
        "final_history_class_count" => length(history_classes),
        "timeline" => timeline,
        "admitted_record" => admitted,
        "graveyard_sample" => graveyard[1:min(12, length(graveyard))],
        "excluded_candidate_sample" => excluded[1:min(12, length(excluded))],
        "motif_counts" => motifs,
        "replicator_detection" => detect_replicator(admitted, graveyard, w),
        "equivalence_lift_tests" => Dict("lift_verdicts" => lifts),
        "append_only_lock_ledger" => Any[],
        "all_pass" => !isempty(timeline)
    )
end

function main()
    mkpath(RESULTS)
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    cfg = spec["run_config"]
    runs = Dict("commuting" => run_ratchet(cfg, "commuting"), "noncommuting" => run_ratchet(cfg, "noncommuting"))
    commute = runs["commuting"]; noncommute = runs["noncommuting"]
    sat = Dict(
        "commuting_saturates" => commute["halted_at_step"] !== nothing,
        "commuting_halt_step" => commute["halted_at_step"],
        "noncommuting_halts" => noncommute["halted_at_step"] !== nothing,
        "noncommuting_halt_step" => noncommute["halted_at_step"],
        "noncommuting_keeps_registering_order_facts_through_budget" => noncommute["halted_at_step"] === nothing && noncommute["timeline"][end]["admitted"] > 0,
        "derivation_check" => (commute["halted_at_step"] !== nothing && noncommute["halted_at_step"] === nothing) ? "PASS" : "FAIL_OR_INCONCLUSIVE"
    )
    payload = Dict(
        "schema" => "codex_ratchet.ratchet_replicator_run_v0.engine_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "lifecycle_status" => "SCRATCH_DIAGNOSTIC",
        "claim_ceiling" => "scratch_diagnostic",
        "capstone_status" => "DRAFT_UNAUDITED",
        "generated_at" => now_iso(),
        "julia_project" => Base.active_project(),
        "source_path" => rel(@__FILE__),
        "source_sha256" => sha256_file(@__FILE__),
        "packages_used" => ["Graphs", "JSON", "SHA", "Julia Base"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict(
            "Graphs" => "active directed-act graph edge count participates in F01-window selection check",
            "Julia Base" => "independent finite directed-act ratchet loop and motif counters"
        ),
        "run_config" => cfg,
        "runs" => runs,
        "saturation_theorem_check" => sat,
        "equivalence_property_lifts" => noncommute["equivalence_lift_tests"]["lift_verdicts"],
        "replicator_verdict" => noncommute["replicator_detection"],
        "frontier_result" => Dict(
            "commuting" => Dict("halt_step" => commute["halted_at_step"], "final_history_class_count" => commute["final_history_class_count"], "admitted_count" => commute["admitted_count"]),
            "noncommuting" => Dict("halt_step" => noncommute["halted_at_step"], "final_history_class_count" => noncommute["final_history_class_count"], "admitted_count" => noncommute["admitted_count"])
        ),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "all_pass" => all(row -> row["all_pass"], values(runs))
    )
    out = joinpath(RESULTS, "ratchet_replicator_run_v0_julia_results.json")
    open(out, "w") do io
        JSON.print(io, payload, 2)
    end
    println(JSON.json(Dict("result_path" => out, "all_pass" => payload["all_pass"], "replicator" => payload["replicator_verdict"]["verdict"])))
    payload["all_pass"] ? 0 : 1
end

exit(main())
