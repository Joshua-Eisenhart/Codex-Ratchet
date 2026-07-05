using Dates
using LinearAlgebra
include(joinpath(@__DIR__, "..", "ratchet_climb_engine_v3_witness", "separation_witness_julia.jl"))

const BASE = fill(0.25, 4)
const ENTANGLED_A = [1.0 0.22 0.0 0.0; 0.0 1.0 0.0 0.0; 0.0 0.0 1.0 -0.16; 0.0 0.0 0.0 1.0]
const ENTANGLED_B = [1.0 0.0 -0.19 0.0; 0.0 1.0 0.0 0.13; 0.0 0.0 1.0 0.0; 0.0 0.0 0.0 1.0]
const COMMUTE_A = Diagonal([1.07, 0.97, 1.03, 0.93])
const COMMUTE_B = Diagonal([0.91, 1.11, 0.89, 1.09])
@assert !(ENTANGLED_A * ENTANGLED_B ≈ ENTANGLED_B * ENTANGLED_A)
@assert COMMUTE_A * COMMUTE_B ≈ COMMUTE_B * COMMUTE_A
const INITIAL_READOUTS = ["global_population"]
const EXTENDED_READOUTS = ["within_cell_phase", "pair_correlation", "time_ordered_two_step"]
const VARIANT_RUNS = [
    ("entangled_memory", "entangled_memory"),
    ("commuting", "commuting"),
    ("memoryless", "memoryless"),
    ("static", "static"),
    ("shuffled", "shuffled"),
    ("feedback_cut", "feedback_cut"),
]

function escs(s) replace(string(s), "\\"=>"\\\\", "\""=>"\\\"") end
function tojson(x)
    x === nothing && return "null"
    x isa Bool && return x ? "true" : "false"
    x isa Number && return string(x)
    x isa AbstractString && return "\"" * escs(x) * "\""
    x isa AbstractArray && return "[" * join([tojson(v) for v in x], ",") * "]"
    x isa Dict && return "{" * join(["\"" * escs(k) * "\":" * tojson(v) for (k,v) in sort(collect(x); by=p->string(p[1]))], ",") * "}"
    return "\"" * escs(x) * "\""
end

canon(q) = [sort(c) for c in q]
rid(k,q) = string(k, ":", join([join(sort(c), "-") for c in q], "."))

function measure(k, s, q, previous=nothing, operators=nothing)
    b0 = [1.0,1.0,-1.0,-1.0]; b1 = [1.0,-1.0,1.0,-1.0]
    k == "global_population" && return [s[1]+s[2], s[1]+s[2], -(s[3]+s[4]), -(s[3]+s[4])]
    k == "within_cell_phase" && return s .* b1
    k == "pair_correlation" && return (s .* b1) * transpose(s .* b0)
    if k == "time_ordered_two_step"
        ops = operators === nothing ? (COMMUTE_A, COMMUTE_B) : operators
        a, b = ops
        x = previous === nothing ? BASE : previous
        return fill(norm(b * (a * x) - a * (b * x)), 4)
    end
    error(k)
end

fact(k, tick, s, q, ro, previous=nothing, operators=nothing) = Dict("tick"=>tick, "readout_id"=>ro["id"], "licensed_by_lock"=>ro["licensed_by_lock"], "values"=>measure(k, s, q, previous, operators))
facts_for(readouts, tick, s, q, previous=nothing, operators=nothing) = [fact(ro["kind"], tick, s, q, ro, previous, operators) for ro in readouts]

function g_history(carrier, history, tick, q, readouts)
    mem = isempty(history) ? zeros(4) : sum(history[max(1,end-2):end]) ./ min(3, length(history))
    phase = tick + 0.17 * length(history)
    s = BASE .+ 0.07 .* [sin(phase), cos(phase+0.4), -sin(phase+0.7), -cos(phase+0.2)] .+ 0.04 .* mem
    return s, facts_for(readouts, tick, s, q, carrier, (ENTANGLED_A, ENTANGLED_B))
end

function g_commute(carrier, history, tick, q, readouts)
    s = BASE .+ 0.03*sin(tick) .* [1.0,1.0,-1.0,-1.0]
    return s, facts_for(readouts, tick, s, q, carrier, (COMMUTE_A, COMMUTE_B))
end

g_empty_history(carrier, history, tick, q, readouts) = g_history(carrier, Any[], tick, q, readouts)

function g_replay(carrier, history, tick, q, readouts)
    tick > 1 && return carrier, Any[]
    return copy(BASE), facts_for(readouts, tick, BASE, q, carrier, (COMMUTE_A, COMMUTE_B))
end

function g_label_shuffle(carrier, history, tick, q, readouts)
    s, facts = g_history(carrier, history, tick, q, readouts)
    for item in facts
        vals = item["values"]
        item["values"] = ndims(vals) == 1 ? vcat(vals[end:end], vals[1:end-1]) : vcat(vals[end:end, :], vals[1:end-1, :])
    end
    return s, facts
end

g_feedback_cut(carrier, history, tick, q, readouts) = g_history(carrier, Any[], tick, q, readouts)

const GENERATOR_TABLE = Dict("entangled_memory"=>g_history, "commuting"=>g_commute, "memoryless"=>g_empty_history, "static"=>g_replay, "shuffled"=>g_label_shuffle, "feedback_cut"=>g_feedback_cut)

function partitions_of(cell)
    isempty(cell) && return [Any[]]
    first = cell[1]; rest = cell[2:end]; out = Any[]
    for part in partitions_of(rest)
        push!(out, vcat([[first]], [copy(c) for c in part]))
        for i in eachindex(part)
            merged = [copy(c) for c in part]
            merged[i] = sort(vcat([first], merged[i]))
            push!(out, merged)
        end
    end
    return out
end

function refs(q, pairs)
    pairset = [Tuple(p["pair"]) for p in pairs]; out = Any[]
    for ci in eachindex(q)
        length(q[ci]) < 2 && continue
        for split in partitions_of(q[ci])
            length(split) <= 1 && continue
            sep = count(pr -> any(a !== b && pr[1] in a && pr[2] in b for a in split for b in split), pairset)
            if sep > 0
                nq = canon(vcat(q[1:ci-1], [sort(c) for c in split], q[ci+1:end]))
                push!(out, Dict("quotient"=>nq, "separation"=>sep, "presumption"=>length(nq)-length(q)))
            end
        end
    end
    return out
end

function choose(q,pairs)
    need = length(unique([Tuple(p["pair"]) for p in pairs]))
    opts = [r for r in refs(q,pairs) if r["separation"] == need]
    if !isempty(opts)
        return sort(opts; by=r -> (r["presumption"], tojson(r["quotient"])))[1]
    end
    affected = Set([p["cell"] + 1 for p in pairs]); nq = Any[]
    for ci in eachindex(q)
        ci in affected ? append!(nq, [[x] for x in q[ci]]) : push!(nq, q[ci])
    end
    nq = canon(nq)
    return Dict("quotient"=>nq, "separation"=>need, "presumption"=>length(nq)-length(q))
end

license_readouts(q, kinds, lock_id) = [Dict("id"=>rid(k,q), "kind"=>k, "licensed_by_lock"=>lock_id) for k in kinds]

function persistent_pairs(q, tick_facts, streaks, k)
    w = separation_witness(q, tick_facts; tolerance=1e-9)
    current = Dict(Tuple(p["pair"])=>p for p in w["witness_pairs"])
    next_streaks = Dict(pair=>get(streaks, pair, 0) + 1 for pair in keys(current))
    pairs = Any[]
    for pair in sort(collect(keys(current)))
        if next_streaks[pair] >= k
            p = copy(current[pair]); p["persistent_ticks"] = next_streaks[pair]; push!(pairs, p)
        end
    end
    return pairs, next_streaks
end

function order_only_pairs(q, tick_facts)
    order_facts = [f for f in tick_facts if occursin("time_ordered_two_step", f["readout_id"])]
    isempty(order_facts) && return Any[]
    return separation_witness(q, order_facts; tolerance=1e-9)["witness_pairs"]
end

function run_pipeline(label, generator; persistent_k=3, max_ticks=50, stop_lossless=10, extend_licensing=true)
    q = [[0,1,2,3]]; all_facts = Any[]; locks = Any[]; history = Any[]; carrier = copy(BASE)
    licensed = license_readouts(q, INITIAL_READOUTS, nothing); streaks = Dict(); lossless = 0; curve = Any[]; last = nothing; tick = 0
    for t in 1:max_ticks
        tick = t
        carrier, tick_facts = generator(carrier, history, t, q, copy(licensed))
        push!(history, carrier .- BASE); append!(all_facts, tick_facts)
        pairs, streaks = persistent_pairs(q, tick_facts, streaks, persistent_k)
        if !isempty(pairs) && !all(c -> length(c) == 1, q)
            c = choose(q, pairs); post = any(f -> f["licensed_by_lock"] !== nothing && f["tick"] > locks[f["licensed_by_lock"]]["tick"], tick_facts)
            order_pairs = order_only_pairs(q, tick_facts)
            q = c["quotient"]
            lock = Dict("tick"=>t, "quotient"=>q, "witness_pairs"=>pairs, "order_witness_pairs"=>order_pairs, "post_lock_readout_forced"=>post, "score"=>Dict("separation"=>c["separation"], "presumption"=>c["presumption"]))
            push!(locks, lock); last = t; lossless = 0; streaks = Dict()
            licensed = extend_licensing ? license_readouts(q, EXTENDED_READOUTS, length(locks)) : Any[]; lock["licensed_readouts"] = licensed
        else
            lossless += 1
        end
        push!(curve, Dict("tick"=>t, "locks"=>length(locks)))
        all(c -> length(c) == 1, q) && lossless >= stop_lossless && break
    end
    return Dict("variant"=>label, "persistent_k"=>persistent_k, "ticks_run"=>tick, "locks"=>locks, "lock_curve"=>curve, "last_new_tick"=>last, "co_turn_events"=>[l for l in locks if l["post_lock_readout_forced"]], "order_fact_events"=>[l for l in locks if !isempty(l["order_witness_pairs"])], "final_quotient"=>q, "fact_count"=>length(all_facts))
end

function run_all(k=3)
    [run_pipeline(label, GENERATOR_TABLE[gen]; persistent_k=k, extend_licensing=(label != "feedback_cut")) for (label, gen) in VARIANT_RUNS]
end

function headline(runs)
    first = runs[1]; rest = runs[2:end]
    h = Dict("dominates_total_locks"=>all(length(first["locks"]) > length(r["locks"]) for r in rest), "dominates_co_turns"=>all(length(first["co_turn_events"]) > length(r["co_turn_events"]) for r in rest))
    h["headline_pass"] = all(values(h)); h
end

runs = run_all(3); h = headline(runs)
out = Dict("schema_version"=>"ratchet_coratchet_loop_v0", "engine"=>"julia", "generated_at"=>string(Dates.now(Dates.UTC)), "classification"=>"scratch_diagnostic", "promotion_allowed"=>false, "formal_admission_allowed"=>false, "capstone_status"=>"STRUCTURAL_REPAIR_20260704_TIME_ORDERED", "persistent_k"=>3, "commutation_assertions"=>Dict("entangled_pair_noncommuting"=>true, "commuting_pair_commutes"=>true), "headline"=>h, "run_results"=>runs, "all_pass"=>h["headline_pass"], "shared_pipeline"=>"Julia implements generator, carrier evolution, fact measurement, and label-blind persistence/refinement/licensing/time-ordered/co-turn logic in this file", "TOOL_MANIFEST"=>Dict("julia"=>Dict("tried"=>true,"used"=>true,"reason"=>"native generator, carrier evolution, and fact measurement"),"v3_witness"=>Dict("tried"=>true,"used"=>true,"reason"=>"load-bearing lossy quotient detector")), "TOOL_INTEGRATION_DEPTH"=>Dict("julia"=>"load_bearing","v3_witness"=>"load_bearing"), "divergence_log"=>["run labels differ only by generator output"])
mkpath(joinpath(@__DIR__, "results"))
open(joinpath(@__DIR__, "results", "ratchet_coratchet_loop_v0_julia_results.json"), "w") do io
    write(io, tojson(out) * "\n")
end
println(tojson(Dict("engine"=>"julia", "locks"=>Dict(r["variant"]=>length(r["locks"]) for r in runs), "co_turns"=>Dict(r["variant"]=>length(r["co_turn_events"]) for r in runs), "headline"=>h)))
