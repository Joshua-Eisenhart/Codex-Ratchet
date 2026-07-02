#!/usr/bin/env julia
# Julia leg for survivor_set_running_mean_threshold_noncommutation_v0.
#
# Independent recomputation of the finite survivor-set restriction object. This
# leg uses native Julia integer bitmasks for configurations and set/symdiff
# comparisons for survivor sets. It does not read exact/JAX/previous results.

using JSON3
using SHA
using Dates

const SIM_ID = "survivor_set_running_mean_threshold_noncommutation_v0"
const HERE = @__DIR__
const OFFSETS = [-2, -1, 1, 2]

sha256_self() = bytes2hex(sha256(read(@__FILE__)))

bit_at(x::Int, i::Int) = (x >> i) & 1

function lexless(a::Vector{Int}, b::Vector{Int})::Bool
    m = min(length(a), length(b))
    for i in 1:m
        a[i] < b[i] && return true
        a[i] > b[i] && return false
    end
    return length(a) < length(b)
end

function windows_for(n::Int)
    seen = Vector{Vector{Int}}()
    function visit(start::Int, k::Int, chosen::Vector{Int})
        if length(chosen) == k
            comp = sort(unique([mod(OFFSETS[i], n) for i in chosen]))
            any(x -> x == comp, seen) || push!(seen, comp)
            return
        end
        remaining = k - length(chosen)
        for i in start:(length(OFFSETS) - remaining + 1)
            push!(chosen, i)
            visit(i + 1, k, chosen)
            pop!(chosen)
        end
    end
    for k in 1:length(OFFSETS)
        visit(1, k, Int[])
    end
    return seen
end

enumerate_configs(n::Int) = collect(0:(2^n - 1))

function count1(x::Int, comp::Vector{Int})::Int
    total = 0
    for i in comp
        total += bit_at(x, i)
    end
    return total
end

function mean_count(comp::Vector{Int}, X::Vector{Int})::Float64
    isempty(X) && return 0.0
    return sum(count1(y, comp) for y in X) / length(X)
end

function step_density_running(comp::Vector{Int}, X::Vector{Int})
    m = mean_count(comp, X)
    return [x for x in X if count1(x, comp) >= m]
end

function step_density_fixed(comp::Vector{Int}, X::Vector{Int}, REF::Vector{Int})
    m = mean_count(comp, REF)
    return [x for x in X if count1(x, comp) >= m]
end

function step_density_floor_running(comp::Vector{Int}, X::Vector{Int})
    thr = floor(Int, mean_count(comp, X))
    return [x for x in X if count1(x, comp) >= thr]
end

function cond_value(c::Int, x::Int, comp::Vector{Int}, X::Vector{Int}, n::Int; anti::Bool=false)
    w = [mod(c + o, n) for o in comp]
    ones = 0
    zeros = 0
    for y in X
        if all(bit_at(y, j) == bit_at(x, j) for j in w)
            if bit_at(y, c) == 1
                ones += 1
            else
                zeros += 1
            end
        end
    end
    ones == zeros && return nothing
    maj = ones > zeros ? 1 : 0
    return anti ? 1 - maj : maj
end

function step_consistency(comp::Vector{Int}, X::Vector{Int}, n::Int)
    out = Int[]
    for x in X
        ok = true
        for c in 0:(n - 1)
            m = cond_value(c, x, comp, X, n; anti=false)
            if m !== nothing && bit_at(x, c) != m
                ok = false
                break
            end
        end
        ok && push!(out, x)
    end
    return out
end

function step_minority(comp::Vector{Int}, X::Vector{Int}, n::Int)
    out = Int[]
    for x in X
        ok = true
        for c in 0:(n - 1)
            m = cond_value(c, x, comp, X, n; anti=true)
            if m !== nothing && bit_at(x, c) != m
                ok = false
                break
            end
        end
        ok && push!(out, x)
    end
    return out
end

function agrees_outside(x::Int, y::Int, outside::Vector{Int})::Bool
    return all(bit_at(x, i) == bit_at(y, i) for i in outside)
end

function step_competitive(comp::Vector{Int}, X::Vector{Int}, n::Int)
    compset = Set(comp)
    outside = [i for i in 0:(n - 1) if !(i in compset)]
    out = Int[]
    for x in X
        dominated = false
        for y in X
            y == x && continue
            if agrees_outside(x, y, outside) && count1(y, comp) > count1(x, comp)
                dominated = true
                break
            end
        end
        dominated || push!(out, x)
    end
    return out
end

symdiff_len(a::Vector{Int}, b::Vector{Int}) = length(symdiff(Set(a), Set(b)))

function noncommute_count(step, windows, ALL)
    nc = 0
    examples = Vector{Any}()
    for a in windows, b in windows
        lexless(a, b) || continue
        AB = step(b, step(a, ALL))
        BA = step(a, step(b, ALL))
        d = symdiff_len(AB, BA)
        if d > 0
            nc += 1
            if length(examples) < 2 && !isempty(AB) && !isempty(BA)
                push!(examples, Dict("a" => a, "b" => b, "len_AB" => length(AB),
                                     "len_BA" => length(BA), "symdiff" => d))
            end
        end
    end
    return nc, examples
end

function fixed_ref_count(windows, ALL)
    nc = 0
    for a in windows, b in windows
        lexless(a, b) || continue
        A2 = step_density_fixed(b, step_density_fixed(a, ALL, ALL), ALL)
        B2 = step_density_fixed(a, step_density_fixed(b, ALL, ALL), ALL)
        symdiff_len(A2, B2) > 0 && (nc += 1)
    end
    return nc
end

function run_for_n(n::Int)
    ALL = enumerate_configs(n)
    windows = windows_for(n)
    npairs = (length(windows) * (length(windows) - 1)) ÷ 2
    dens_run, dens_ex = noncommute_count((comp, X) -> step_density_running(comp, X), windows, ALL)
    dens_fix = fixed_ref_count(windows, ALL)
    dens_floor, _ = noncommute_count((comp, X) -> step_density_floor_running(comp, X), windows, ALL)
    cons, _ = noncommute_count((comp, X) -> step_consistency(comp, X, n), windows, ALL)
    comp_ctl, _ = noncommute_count((comp, X) -> step_competitive(comp, X, n), windows, ALL)
    mino, _ = noncommute_count((comp, X) -> step_minority(comp, X, n), windows, ALL)
    return Dict(
        "N" => n,
        "config_count" => length(ALL),
        "window_count" => length(windows),
        "pair_count" => npairs,
        "running_mean_threshold_running_X_noncommute" => dens_run,
        "running_mean_threshold_fixed_reference_noncommute" => dens_fix,
        "floor_mean_threshold_running_X_noncommute" => dens_floor,
        "ensemble_consistency_noncommute" => cons,
        "competitive_exclusion_noncommute" => comp_ctl,
        "minority_frustration_noncommute" => mino,
        "examples" => dens_ex,
    )
end

function main()
    per_n = Dict(string(n) => run_for_n(n) for n in (5, 6, 7))
    order_dependence = all(per_n[string(n)]["running_mean_threshold_running_X_noncommute"] > 0 for n in (5, 6, 7))
    isolator_holds = all(per_n[string(n)]["running_mean_threshold_fixed_reference_noncommute"] == 0 for n in (5, 6, 7))
    necessary_not_sufficient = all(
        per_n[string(n)]["floor_mean_threshold_running_X_noncommute"] == 0 &&
        per_n[string(n)]["ensemble_consistency_noncommute"] == 0 &&
        per_n[string(n)]["competitive_exclusion_noncommute"] == 0 &&
        per_n[string(n)]["minority_frustration_noncommute"] == 0
        for n in (5, 6, 7)
    )

    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "computation_style" => "native_julia_integer_bitmask_survivor_sets",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), "yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => sha256_self(),
        "result_path" => "system_v7/sims/$SIM_ID/results/$(SIM_ID)_julia_results.json",
        "julia_project" => something(Base.active_project(), "none"),
        "per_N" => per_n,
        "claims" => Dict(
            "running_X_admits_order_dependence" => order_dependence,
            "isolator_fixed_reference_commutes" => isolator_holds,
            "state_dependence_necessary_not_sufficient" => necessary_not_sufficient,
            "rule" => "convention-free: survive iff count1(x,comp) >= real-valued mean over the running survivor set (no rounding)",
            "emergence_label" => "REJECTED as overclaim by the full-fleet audit; this is order-dependent survivor-set filtering, not strong emergence",
        ),
        "honest_scope" => Dict(
            "earns" => "a narrow, fleet-survived fact: a natural state-reactive cut admits generic restriction-noncommutation, convention-free, with the necessary-not-sufficient sharpening",
            "does_not_earn" => "the emergence label; a full ratchet; a local-only rule; a causal engine; any GNVW/bridge/manifold/axis claim",
        ),
        "packages_used" => ["JSON3", "SHA", "Dates"],
        "aligned_packages_load_bearing" => String[],
        "TOOL_MANIFEST" => Dict(
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "result serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "source self-hash"),
            "julia_integer_bit_operations" => Dict("tried" => true, "used" => true, "reason" => "independent finite configuration carrier and survivor-set predicates"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "JSON3" => "supportive",
            "SHA" => "supportive",
            "julia_integer_bit_operations" => "load_bearing",
        ),
    )

    out = joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
    mkpath(dirname(out))
    open(out, "w") do f
        JSON3.pretty(f, result)
    end
    println("julia leg wrote ", out)
    for n in (5, 6, 7)
        r = per_n[string(n)]
        println("  N=$n: density(>=mean) running-X $(r["running_mean_threshold_running_X_noncommute"])/$(r["pair_count"]) | fixed-ref $(r["running_mean_threshold_fixed_reference_noncommute"]) | floor(mean) $(r["floor_mean_threshold_running_X_noncommute"]) | consistency $(r["ensemble_consistency_noncommute"]) competitive $(r["competitive_exclusion_noncommute"]) minority $(r["minority_frustration_noncommute"])")
    end
    println("  order_dependence=$order_dependence isolator_holds=$isolator_holds necessary_not_sufficient=$necessary_not_sufficient")
end

main()
