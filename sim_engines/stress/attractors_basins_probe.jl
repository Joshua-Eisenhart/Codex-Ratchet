# UNOFFICIAL STRESS PROBE (julia leg) — Newton-fractal basins of attraction.
#
# classification: unofficial_stress_probe · promotion_allowed: false
# (the receipt with these labels is written by attractors_basins_probe.py)
#
# DynamicalSystems.jl + Attractors.jl are the LOAD-BEARING engines here:
# AttractorsViaRecurrences DISCOVERS the attractors of the Newton map for
# z^p - 1 on its own (no root list supplied) and labels a 101x101 grid of
# initial conditions — classical basin-mapping capability that jnp /
# QuantumOptics cannot provide. Emits one JSON line on stdout.
using DynamicalSystems
using JSON

function newton_rule_factory(p::Int)
    return function (u, params, n)
        z = complex(u[1], u[2])
        if p == 1
            return SVector(1.0, 0.0)          # Newton for z - 1 is the constant map z -> 1
        end
        if abs(z) < 1e-6
            z = complex(1e-6, 0.0)            # guard the z = 0 pole of the Newton update
        end
        znew = z - (z^p - 1) / (p * z^(p - 1))
        return SVector(real(znew), imag(znew))
    end
end

function basin_case(p::Int, n_ics::Int)
    rule = newton_rule_factory(p)
    ds = DeterministicIteratedMap(rule, SVector(0.4, 0.4))
    grid = (range(-1.5, 1.5; length = 301), range(-1.5, 1.5; length = 301))
    mapper = AttractorsViaRecurrences(ds, grid; horizon_limit = 1e13)
    ics = range(-1.5, 1.5; length = n_ics)
    counts = Dict{Int,Int}()
    total = 0
    for x in ics, y in ics
        lab = mapper(SVector(x, y))
        counts[lab] = get(counts, lab, 0) + 1
        total += 1
    end
    attractors = extract_attractors(mapper)
    att_points = Dict{String,Vector{Float64}}()
    for (k, set) in attractors
        pts = collect(set)
        m = sum(pts) / length(pts)
        u = m
        for _ in 1:200                        # refine by iterating the map itself
            u = rule(u, nothing, 0)
        end
        att_points[string(k)] = [u[1], u[2]]
    end
    fractions = Dict(string(k) => v / total for (k, v) in counts if k > 0)
    unlabeled = get(counts, -1, 0) / total
    return Dict(
        "power" => p,
        "n_ics_total" => total,
        "n_attractors" => length(attractors),
        "attractor_points" => att_points,
        "basin_fractions" => fractions,
        "unlabeled_fraction" => unlabeled,
    )
end

result = Dict(
    "engine" => "DynamicalSystems.jl DeterministicIteratedMap + Attractors.jl AttractorsViaRecurrences",
    "cases" => Dict("p3" => basin_case(3, 101), "p1" => basin_case(1, 101)),
)
println(JSON.json(result))
