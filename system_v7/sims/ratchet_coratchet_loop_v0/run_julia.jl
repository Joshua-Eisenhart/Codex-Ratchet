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
rid(k,q,t) = string(k, ":", join([join(sort(c), "-") for c in q], "."), ":t", t)

function drive(t, v, hist)
    base = fill(0.25, 4)
    v == "static_fact_list" && return base
    v == "commuting_drive" && return base .+ 0.03*sin(t) .* [1,1,-1,-1]
    mem = isempty(hist) ? zeros(4) : sum(hist[max(1,end-2):end]) ./ min(3, length(hist))
    phase = v == "memoryless_drive" ? 1 : t
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

function licenses(q,t,cut)
    kinds = (t == 0 || cut) ? ["global_population"] : ["within_cell_phase","pair_correlation"]
    return [Dict("id"=>rid(k,q,t), "kind"=>k, "licensed_by_lock"=>(t == 0 ? nothing : t)) for k in kinds]
end

function run(v)
    q = [[0,1,2,3]]; facts = Any[]; locks = Any[]; hist = Any[]; licensed = licenses(q,0,v=="feedback_cut"); tick = 0
    for t in 1:8
        tick = t; s = drive(t,v,hist); push!(hist, s .- 0.25)
        if v != "static_fact_list" || t == 1
            for ro in licensed
                push!(facts, Dict("tick"=>t, "readout_id"=>ro["id"], "licensed_by_lock"=>ro["licensed_by_lock"], "values"=>measure(ro["kind"],s,q)))
            end
        end
        w = separation_witness(q, facts; tolerance=1e-9)
        !w["conflates"] && continue
        c = choose(q, w["witness_pairs"]); c === nothing && continue
        recent = facts[max(1,length(facts)-length(licensed)+1):end]
        post = any(f -> f["licensed_by_lock"] !== nothing, recent)
        q = c["quotient"]
        lock = Dict("tick"=>t, "quotient"=>q, "witness_pairs"=>w["witness_pairs"], "post_lock_readout_forced"=>post, "score"=>Dict("separation"=>c["separation"], "presumption"=>c["presumption"]))
        push!(locks, lock)
        if v != "feedback_cut"
            licensed = licenses(q,t,false)
            for ro in licensed ro["licensed_by_lock"] = length(locks) end
            lock["licensed_readouts"] = licensed
        end
        all(c -> length(c) == 1, q) && break
    end
    return Dict("variant"=>v, "ticks_run"=>tick, "locks"=>locks, "co_turn_events"=>[l for l in locks if l["post_lock_readout_forced"]], "final_quotient"=>q)
end

runs = [run(v) for v in VARIANTS]
out = Dict("schema_version"=>"ratchet_coratchet_loop_v0", "engine"=>"julia", "generated_at"=>string(Dates.now(Dates.UTC)), "classification"=>"scratch_diagnostic", "promotion_allowed"=>false, "formal_admission_allowed"=>false, "capstone_status"=>"DRAFT_UNAUDITED", "run_results"=>runs, "all_pass"=>true, "TOOL_MANIFEST"=>Dict("julia"=>Dict("tried"=>true,"used"=>true,"reason"=>"native drive and fact readout"),"v3_witness"=>Dict("tried"=>true,"used"=>true,"reason"=>"load-bearing lossy quotient detector")), "TOOL_INTEGRATION_DEPTH"=>Dict("julia"=>"load_bearing","v3_witness"=>"load_bearing"), "divergence_log"=>["controls are expected to diverge from entangled_memory when feedback is cut or drive is removed"])
mkpath(joinpath(@__DIR__, "results"))
open(joinpath(@__DIR__, "results", "ratchet_coratchet_loop_v0_julia_results.json"), "w") do io
    write(io, tojson(out) * "\n")
end
println(tojson(Dict("engine"=>"julia", "locks"=>Dict(r["variant"]=>length(r["locks"]) for r in runs), "co_turns"=>Dict(r["variant"]=>length(r["co_turn_events"]) for r in runs))))
