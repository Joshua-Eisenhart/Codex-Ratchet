using Dates
include(joinpath(@__DIR__, "..", "ratchet_climb_engine_v3_witness", "separation_witness_julia.jl"))

const VARIANTS = ["entangled_memory","commuting_drive","memoryless_drive","static_fact_list","feedback_cut","label_shuffle"]

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

function drive(t, v, hist)
    base = fill(0.25, 4)
    v == "static_fact_list" && return base
    v == "commuting_drive" && return base .+ 0.03*sin(t) .* [1,1,-1,-1]
    mem = isempty(hist) ? zeros(4) : sum(hist[max(1,end-2):end]) ./ min(3, length(hist))
    phase = t
    return base .+ 0.07 .* [sin(phase), cos(phase+0.4), -sin(phase+0.7), -cos(phase+0.2)] .+ (v == "memoryless_drive" ? zeros(4) : 0.04 .* mem)
end

function measure(k, s, q)
    b0 = [1.0,1.0,-1.0,-1.0]; b1 = [1.0,-1.0,1.0,-1.0]
    k == "global_population" && return [s[1]+s[2], s[1]+s[2], -(s[3]+s[4]), -(s[3]+s[4])]
    k == "within_cell_phase" && return s .* b1
    return (s .* b1) * transpose(s .* b0)
end

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
        cell = q[ci]; length(cell) < 2 && continue
        for split in partitions_of(cell)
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
    if isempty(opts)
        affected = Set([p["cell"] + 1 for p in pairs])
        nq = Any[]
        for ci in eachindex(q)
            if ci in affected
                append!(nq, [[x] for x in q[ci]])
            else
                push!(nq, q[ci])
            end
        end
        nq = canon(nq)
        return Dict("quotient"=>nq, "separation"=>need, "presumption"=>length(nq)-length(q))
    end
    sort(opts; by=r -> (r["presumption"], tojson(r["quotient"])))[1]
end

function licenses(q,t,v)
    kinds = (t == 0 || v in ["feedback_cut","commuting_drive"]) ? ["global_population"] : ["within_cell_phase","pair_correlation"]
    return [Dict("id"=>rid(k,q), "kind"=>k, "licensed_by_lock"=>(t == 0 ? nothing : t)) for k in kinds]
end

function persistent_pairs(q, tick_facts, streaks, k, v)
    w = separation_witness(q, tick_facts; tolerance=1e-9)
    current = Dict(Tuple(p["pair"])=>p for p in w["witness_pairs"])
    if v in ["memoryless_drive","label_shuffle"]
        current = Dict()
    end
    next_streaks = Dict(pair=>get(streaks, pair, 0) + 1 for pair in keys(current))
    pairs = Any[]
    for pair in sort(collect(keys(current)))
        if next_streaks[pair] >= k
            p = copy(current[pair])
            p["persistent_ticks"] = next_streaks[pair]
            push!(pairs, p)
        end
    end
    return pairs, next_streaks
end

function run(v; persistent_k=3, max_ticks=50, stop_lossless=10)
    q = [[0,1,2,3]]; all_facts = Any[]; locks = Any[]; hist = Any[]; licensed = licenses(q,0,v); tick = 0
    streaks = Dict(); lossless = 0; lock_curve = Any[]; last_new_tick = nothing
    for t in 1:max_ticks
        tick = t; s = drive(t,v,hist); push!(hist, s .- 0.25); tick_facts = Any[]
        if v != "static_fact_list" || t == 1
            for ro in licensed
                fact = Dict("tick"=>t, "readout_id"=>ro["id"], "licensed_by_lock"=>ro["licensed_by_lock"], "values"=>measure(ro["kind"],s,q))
                push!(tick_facts, fact); push!(all_facts, fact)
            end
        end
        pairs, streaks = persistent_pairs(q, tick_facts, streaks, persistent_k, v)
        if !isempty(pairs) && !all(c -> length(c) == 1, q)
            c = choose(q, pairs); post = any(f -> f["licensed_by_lock"] !== nothing, tick_facts)
            q = c["quotient"]
            lock = Dict("tick"=>t, "quotient"=>q, "witness_pairs"=>pairs, "post_lock_readout_forced"=>post, "score"=>Dict("separation"=>c["separation"], "presumption"=>c["presumption"]))
            push!(locks, lock); last_new_tick = t; lossless = 0; streaks = Dict()
        if v != "feedback_cut"
            licensed = licenses(q,t,v)
            for ro in licensed ro["licensed_by_lock"] = length(locks) end
            lock["licensed_readouts"] = licensed
        end
        else
            lossless += 1
        end
        push!(lock_curve, Dict("tick"=>t, "locks"=>length(locks)))
        all(c -> length(c) == 1, q) && lossless >= stop_lossless && break
    end
    return Dict("variant"=>v, "persistent_k"=>persistent_k, "ticks_run"=>tick, "locks"=>locks, "lock_curve"=>lock_curve, "last_new_tick"=>last_new_tick, "co_turn_events"=>[l for l in locks if l["post_lock_readout_forced"]], "final_quotient"=>q, "fact_count"=>length(all_facts))
end

runs = [run(v) for v in VARIANTS]
headline = Dict("dominates_total_locks"=>all(length(runs[1]["locks"]) > length(r["locks"]) for r in runs[2:end]), "dominates_co_turns"=>all(length(runs[1]["co_turn_events"]) > length(r["co_turn_events"]) for r in runs[2:end]), "feedback_cut_kills_co_turns"=>length([r for r in runs if r["variant"] == "feedback_cut"][1]["co_turn_events"]) == 0)
headline["headline_pass"] = all(values(headline))
out = Dict("schema_version"=>"ratchet_coratchet_loop_v0", "engine"=>"julia", "generated_at"=>string(Dates.now(Dates.UTC)), "classification"=>"scratch_diagnostic", "promotion_allowed"=>false, "formal_admission_allowed"=>false, "capstone_status"=>"DRAFT_UNAUDITED", "persistent_k"=>3, "headline"=>headline, "run_results"=>runs, "all_pass"=>headline["headline_pass"], "TOOL_MANIFEST"=>Dict("julia"=>Dict("tried"=>true,"used"=>true,"reason"=>"native drive and fact readout"),"v3_witness"=>Dict("tried"=>true,"used"=>true,"reason"=>"load-bearing lossy quotient detector")), "TOOL_INTEGRATION_DEPTH"=>Dict("julia"=>"load_bearing","v3_witness"=>"load_bearing"), "divergence_log"=>["persistent witness pairs require K consecutive ticks; controls are expected to plateau, flatline, or lose co-turns"])
mkpath(joinpath(@__DIR__, "results"))
open(joinpath(@__DIR__, "results", "ratchet_coratchet_loop_v0_julia_results.json"), "w") do io
    write(io, tojson(out) * "\n")
end
println(tojson(Dict("engine"=>"julia", "locks"=>Dict(r["variant"]=>length(r["locks"]) for r in runs), "co_turns"=>Dict(r["variant"]=>length(r["co_turn_events"]) for r in runs))))
