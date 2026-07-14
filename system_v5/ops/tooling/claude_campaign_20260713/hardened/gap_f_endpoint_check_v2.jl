#!/usr/bin/env julia

# Exact Julia sidecar for the packet-166 endpoint used by Gap F v2.
# It independently reimplements the finite integer update. It does not read a
# Python result and it does not claim that optimal transport equals TV.

const BUDGET = 160

function omega()
    return NTuple{4,Int}[(a, b, c, d) for a in 0:1 for b in 0:1 for c in 0:1 for d in 0:1]
end

operate(table::NTuple{4,Int}, a::Int, b::Int) = table[2 * a + b + 1]

function features(table::NTuple{4,Int})
    assoc = sum(
        operate(table, operate(table, a, b), c) != operate(table, a, operate(table, b, c))
        for a in 0:1 for b in 0:1 for c in 0:1
    )
    order = sum(operate(table, a, b) != operate(table, b, a) for a in 0:1 for b in 0:1)
    return assoc, order
end

const OMEGA = omega()
const FEATURES = features.(OMEGA)

likelihood(index::Int) = 1 + FEATURES[index][1] + FEATURES[index][2]

function normalize_full_support(raw::Vector{BigInt})
    n = length(raw)
    remainder = BigInt(BUDGET - n)
    total = sum(raw)
    quotas = [Rational{BigInt}(remainder * value, total) for value in raw]
    allocations = [fld(numerator(q), denominator(q)) for q in quotas]
    leftover = remainder - sum(allocations)
    order = sort(collect(1:n), by=i -> (Rational{BigInt}(allocations[i]) - quotas[i], i))
    for index in order[1:Int(leftover)]
        allocations[index] += 1
    end
    result = BigInt[1 + value for value in allocations]
    @assert sum(result) == BUDGET && minimum(result) >= 1
    return result
end

update(profile::Vector{BigInt}) = normalize_full_support(
    BigInt[profile[index] * likelihood(index) for index in eachindex(profile)]
)

total_variation(p::Vector{BigInt}, q::Vector{BigInt}) =
    Rational{BigInt}(sum(abs.(p .- q)), 2 * sum(p))

function main()
    current = fill(BigInt(10), 16)
    seen = Dict{Tuple{Vararg{BigInt}},Int}(Tuple(current) => 0)
    round = 0
    period = 0
    for step in 1:128
        current = update(current)
        key = Tuple(current)
        if haskey(seen, key)
            round = step
            period = step - seen[key]
            break
        end
        seen[key] = step
    end
    rotated = vcat(current[2:end], current[1:1])
    tv = total_variation(current, rotated)
    fixed = update(current) == current
    endpoint = join(string.(current), ",")
    active_project = string(Base.active_project())
    println("{" *
        "\"schema\":\"codex-ratchet.gap-f-julia-endpoint.v2\"," *
        "\"julia_version\":\"$(VERSION)\"," *
        "\"active_project\":\"$(active_project)\"," *
        "\"endpoint\":[" * endpoint * "]," *
        "\"repeat_round\":$(round)," *
        "\"period\":$(period)," *
        "\"fixed_point\":$(fixed)," *
        "\"tv_fraction\":\"$(numerator(tv))/$(denominator(tv))\"" *
        "}")
end

main()
