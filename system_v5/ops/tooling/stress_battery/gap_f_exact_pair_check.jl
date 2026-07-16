# Gap F cross-engine check: recompute the ontological_finitude_cosmogenesis_ratchet_sim
# joint_order_bracket orbit with exact Rational{BigInt} arithmetic and confirm the
# permutation-control pair has total variation exactly 137//160.
# Independent re-implementation of the sim's update()/normalize_full_support().
# stdlib only; prints one JSON object to stdout.

const QALPH = 2
const ARITY = 2
const BUDGET = 160

# Same order as Python itertools.product(range(2), repeat=4): last slot fastest.
function build_omega()
    omega = NTuple{4,Int}[]
    for a in 0:1, b in 0:1, c in 0:1, d in 0:1
        push!(omega, (a, b, c, d))
    end
    return omega
end

const OMEGA = build_omega()

operate(table::NTuple{4,Int}, a::Int, b::Int) = table[QALPH * a + b + 1]

function features(table::NTuple{4,Int})
    assoc_viol = 0
    for a in 0:1, b in 0:1, c in 0:1
        if operate(table, operate(table, a, b), c) != operate(table, a, operate(table, b, c))
            assoc_viol += 1
        end
    end
    order_viol = 0
    for a in 0:1, b in 0:1
        if operate(table, a, b) != operate(table, b, a)
            order_viol += 1
        end
    end
    return (assoc_viol, order_viol)
end

const FEATS = [features(t) for t in OMEGA]

# joint_order_bracket likelihood: 1 + order_violations + associator_violations
likelihood(i::Int) = 1 + FEATS[i][2] + FEATS[i][1]

function normalize_full_support(raw::Vector{BigInt})
    @assert all(v -> v > 0, raw)
    n = length(raw)
    remainder_budget = BigInt(BUDGET - n)
    total = sum(raw)
    quotas = [Rational{BigInt}(remainder_budget * v, total) for v in raw]
    allocations = [fld(numerator(q), denominator(q)) for q in quotas]
    leftover = remainder_budget - sum(allocations)
    # Python key: (-(quota - alloc), index) ascending == (alloc - quota, index) ascending
    order = sort(collect(1:n), by = i -> (Rational{BigInt}(allocations[i]) - quotas[i], i))
    for i in order[1:Int(leftover)]
        allocations[i] += 1
    end
    result = [BigInt(1) + a for a in allocations]
    @assert sum(result) == BUDGET && minimum(result) >= 1
    return result
end

update(profile::Vector{BigInt}) =
    normalize_full_support([profile[i] * likelihood(i) for i in 1:length(profile)])

total_variation(p::Vector{BigInt}, q::Vector{BigInt}) =
    Rational{BigInt}(sum(abs.(p .- q)), 2 * sum(p))

function main()
    initial = fill(BigInt(10), 16)
    seen = Dict{Vector{BigInt},Int}(initial => 0)
    history = [initial]
    current = initial
    transient = -1
    period = -1
    for _ in 1:128
        current = update(current)
        push!(history, current)
        if haskey(seen, current)
            transient = seen[current]
            period = length(history) - 1 - transient
            break
        end
        seen[current] = length(history) - 1
    end
    endpoint = history[end]
    rotated = vcat(endpoint[2:end], endpoint[1:1])
    tv = total_variation(endpoint, rotated)
    target = 137 // 160
    # negative control: wrong pair must NOT hit the target
    tv_wrong = total_variation(endpoint, initial)
    fixed_point = update(endpoint) == endpoint

    ep_str = join(string.(endpoint), ",")
    println("{" *
        "\"engine\":\"julia\"," *
        "\"julia_version\":\"$(VERSION)\"," *
        "\"endpoint\":[" * ep_str * "]," *
        "\"transient_length\":$(transient)," *
        "\"period\":$(period)," *
        "\"fixed_point\":$(fixed_point)," *
        "\"tv_exact\":\"$(numerator(tv))/$(denominator(tv))\"," *
        "\"tv_equals_137_160\":$(tv == target)," *
        "\"control_wrong_pair_tv\":\"$(numerator(tv_wrong))/$(denominator(tv_wrong))\"," *
        "\"control_wrong_pair_differs\":$(tv_wrong != target)" *
        "}")
end

main()
