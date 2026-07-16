#!/usr/bin/env julia

"""
Julia/Attractors leg for the bounded gap-D basin-chain probe.

The shared discrete map is

    F(x; α, f) = x - α * max(x - f, 0)

with active α=0.5 and floor f=3.0.  The tested start grid is strictly above
the floor.  This matters: every x <= f is also a fixed point, so the receipt
may claim only the unique active-domain boundary attractor, never a globally
unique fixed point.
"""

using Attractors
using StaticArrays

const FLOOR = 3.0
const DRIVE = 0.5
const ERASED_DRIVE = 0.0
const START_GRID = range(3.5, 12.0; length = 18)
const PROXIMITY_EPSILON = 1.0e-10

shared_map(u, p, n) = SVector(u[1] - p[1] * max(u[1] - p[2], 0.0))

function iterate_endpoint(start::Float64, drive::Float64; steps::Int = 128)
    state = SVector(start)
    parameters = SVector(drive, FLOOR)
    for n in 1:steps
        state = shared_map(state, parameters, n)
    end
    return state[1]
end

function basin_labels(drive::Float64; horizon_limit::Float64)
    parameters = SVector(drive, FLOOR)
    system = DeterministicIteratedMap(shared_map, SVector(FLOOR), parameters)
    attractors = Dict(1 => StateSpaceSet([SVector(FLOOR)]))
    mapper = AttractorsViaProximity(
        system,
        attractors;
        ε = PROXIMITY_EPSILON,
        Ttr = 0,
        Δt = 1,
        consecutive_lost_steps = 100,
        horizon_limit = horizon_limit,
    )
    basins, _ = basins_of_attraction(mapper, (START_GRID,); show_progress = false)
    labels = Int.(basins)
    positive_labels = sort(unique(filter(>(0), labels)))
    active_fraction = count(>(0), labels) / length(labels)
    lost_fraction = count(==(-1), labels) / length(labels)
    return labels, positive_labels, active_fraction, lost_fraction
end

function main()
    active_labels, active_positive, active_fraction, active_lost = basin_labels(
        DRIVE; horizon_limit = 256.0
    )
    erased_labels, erased_positive, erased_fraction, erased_lost = basin_labels(
        ERASED_DRIVE; horizon_limit = 128.0
    )

    active_endpoints = [iterate_endpoint(Float64(start), DRIVE) for start in START_GRID]
    erased_endpoints = [iterate_endpoint(Float64(start), ERASED_DRIVE) for start in START_GRID]
    attractor_location = sum(active_endpoints) / length(active_endpoints)
    max_endpoint_error = maximum(abs.(active_endpoints .- FLOOR))
    erased_max_motion = maximum(
        abs(erased_endpoints[index] - Float64(start))
        for (index, start) in enumerate(START_GRID)
    )
    boundary_fixed = shared_map(SVector(FLOOR), SVector(DRIVE, FLOOR), 0)[1] == FLOOR
    below_floor_fixed = shared_map(SVector(2.5), SVector(DRIVE, FLOOR), 0)[1] == 2.5

    active_basin_count = length(active_positive)
    erased_basin_count = length(erased_positive)
    all_pass = (
        active_basin_count == 1 &&
        active_positive == [1] &&
        active_fraction == 1.0 &&
        active_lost == 0.0 &&
        max_endpoint_error <= 1.0e-12 &&
        erased_basin_count == 0 &&
        erased_fraction == 0.0 &&
        erased_lost == 1.0 &&
        erased_max_motion == 0.0 &&
        boundary_fixed &&
        below_floor_fixed
    )

    println("JULIA_ACTIVE_PROJECT=", Base.active_project())
    println("JULIA_VERSION=", VERSION)
    println("JULIA_ATTRACTORS_VERSION=", pkgversion(Attractors))
    println("JULIA_STATICARRAYS_VERSION=", pkgversion(StaticArrays))
    println("JULIA_START_COUNT=", length(START_GRID))
    println("JULIA_ACTIVE_BASIN_COUNT=", active_basin_count)
    println("JULIA_ACTIVE_BASIN_FRACTION=", active_fraction)
    println("JULIA_ACTIVE_LOST_FRACTION=", active_lost)
    println("JULIA_ACTIVE_LABELS=", join(active_labels, ","))
    println("JULIA_ATTRACTOR_LOCATION=", repr(attractor_location))
    println("JULIA_MAX_ENDPOINT_ERROR=", repr(max_endpoint_error))
    println("JULIA_ERASED_BASIN_COUNT=", erased_basin_count)
    println("JULIA_ERASED_BASIN_FRACTION=", erased_fraction)
    println("JULIA_ERASED_LOST_FRACTION=", erased_lost)
    println("JULIA_ERASED_LABELS=", join(erased_labels, ","))
    println("JULIA_ERASED_MAX_MOTION=", repr(erased_max_motion))
    println("JULIA_BOUNDARY_FIXED=", lowercase(string(boundary_fixed)))
    println("JULIA_GLOBAL_BELOW_FLOOR_FIXED=", lowercase(string(below_floor_fixed)))
    println(all_pass ? "PASS basin_chain_d_julia" : "FAIL basin_chain_d_julia")
    return all_pass ? 0 : 1
end

exit(main())
