#!/usr/bin/env julia

using Attractors
using LinearAlgebra
using Printf
using Random: Xoshiro
using SHA
using StaticArrays

const SIM_ID = "attractors_basin_native_schedule_v0"
const CLASSIFICATION = "tool_lego_fit_probe"
const TOOL_INTEGRATION_DEPTH = "split__instrument_checks_load_bearing__schedule_battery_confirmatory"  # audit 2026-07-11: schedule verdicts algebraically foregone (spectral radii <1); package discriminates only in the instrument pair
const SEED = 0
const G = 0.35
const KAP = 1.0
const Q = 1.0 - exp(-1.0)
const TH = pi / 4
const T_FLOW = 1.0
const N_STEPS = 400
const WELD_TOL = 1.0e-6
const SOURCE_DIR = joinpath(@__DIR__, "source_copies")

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SP = 0.5 .* (SX .+ im .* SY)
const SM = 0.5 .* (SX .- im .* SY)
const P0 = 0.5 .* (I2 .+ SZ)
const P1 = 0.5 .* (I2 .- SZ)
const QP = 0.5 .* (I2 .+ SX)
const QM = 0.5 .* (I2 .- SX)
const UX = cos(TH / 2) .* I2 .- im * sin(TH / 2) .* SX
const UZ = cos(TH / 2) .* I2 .- im * sin(TH / 2) .* SZ
const PAULIS = (SX, SY, SZ)

const TERRAIN = [
    (+1, :damp, +1), (+1, :depol, 0), (+1, :damp, -1), (+1, :proj, 0),
    (-1, :damp, -1), (-1, :depol, 0), (-1, :damp, +1), (-1, :proj, 0),
]
const NATIVE_STAGES = [
    (0, "Ti"), (0, "Fi"), (1, "Ti"), (1, "Fi"),
    (2, "Te"), (2, "Fe"), (3, "Te"), (3, "Fe"),
    (4, "Ti"), (4, "Fi"), (5, "Ti"), (5, "Fi"),
    (6, "Te"), (6, "Fe"), (7, "Te"), (7, "Fe"),
]
const EXPECTED_SOURCE_SHA256 = Dict(
    "targets.json" => "1d74d038881b528e67e7ac21d9feef09e26c942ebc0e8f3bbcbca1e78ebbe69e",
    "oracle_targets.py" => "e97247034d7da3a2ebbd27bda01d348e76da6c7cd605144219a3f297524dcdfb",
)

const TOOL_MANIFEST = Dict(
    "Attractors" => Dict(
        "used" => true,
        "reason" => "AttractorsViaRecurrences and basins_fractions gate every reported basin result and both instrument checks.",
    ),
    "StaticArrays" => Dict(
        "used" => true,
        "reason" => "SVector is the concrete three-coordinate state type of each DeterministicIteratedMap.",
    ),
)

function dissipator(L, rho)
    return L * rho * L' - 0.5 .* (L' * L * rho + rho * L' * L)
end

function generator(t::Int)
    eps, kind, pole = TERRAIN[t + 1]
    H = eps .* (SX .+ SY .+ SZ) ./ sqrt(3.0)
    return function (rho)
        out = -im * G .* (H * rho - rho * H)
        if kind == :damp
            out .+= KAP .* dissipator(pole > 0 ? SP : SM, rho)
        elseif kind == :depol
            out .+= 0.5 * KAP .* (dissipator(SX, rho) + dissipator(SY, rho))
        else
            out .+= KAP .* dissipator(SZ, rho)
        end
        return out
    end
end

function flow(X, rho; time = T_FLOW, steps = N_STEPS)
    dt = time / steps
    state = copy(rho)
    for _ in 1:steps
        k1 = X(state)
        k2 = X(state + 0.5 * dt * k1)
        k3 = X(state + 0.5 * dt * k2)
        k4 = X(state + dt * k3)
        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        state = 0.5 .* (state + state')
        state ./= real(tr(state))
    end
    return state
end

function apply_operator(name::String, rho)
    if name == "Ti"
        return (1.0 - Q) .* rho .+ Q .* (P0 * rho * P0 + P1 * rho * P1)
    elseif name == "Te"
        return (1.0 - Q) .* rho .+ Q .* (QP * rho * QP + QM * rho * QM)
    elseif name == "Fi"
        return UX * rho * UX'
    elseif name == "Fe"
        return UZ * rho * UZ'
    end
    error("unknown operator: $name")
end

bloch_to_density(u) = 0.5 .* (I2 .+ u[1] .* SX .+ u[2] .* SY .+ u[3] .* SZ)

function density_to_bloch(rho)
    return SVector{3, Float64}(ntuple(i -> real(tr(rho * PAULIS[i])), 3))
end

function stage_map(u, t::Int, opname::String)
    rho = flow(generator(t), bloch_to_density(u))
    return density_to_bloch(apply_operator(opname, rho))
end

function source_hashes!()
    actual = Dict{String, String}()
    for (name, expected) in EXPECTED_SOURCE_SHA256
        path = joinpath(SOURCE_DIR, name)
        isfile(path) || error("CONTRACT WELD ABORT: missing source copy $path")
        digest = bytes2hex(sha256(read(path)))
        digest == expected || error("CONTRACT WELD ABORT: SHA-256 mismatch for $name: $digest != $expected")
        actual[name] = digest
    end
    return actual
end

function copied_bloch_down_targets()
    text = read(joinpath(SOURCE_DIR, "targets.json"), String)
    pattern = Regex("\\\"bloch_down\\\"\\s*:\\s*\\[([^\\]]+)\\]")
    targets = Vector{SVector{3, Float64}}()
    for match in eachmatch(pattern, text)
        numbers = parse.(Float64, strip.(split(match.captures[1], ',')))
        length(numbers) == 3 || error("CONTRACT WELD ABORT: malformed bloch_down target")
        push!(targets, SVector{3, Float64}(numbers))
    end
    length(targets) == 16 || error("CONTRACT WELD ABORT: expected 16 bloch_down targets, found $(length(targets))")
    return targets
end

function contract_weld!()
    hashes = source_hashes!()
    targets = copied_bloch_down_targets()
    probe = SVector(0.55, 0.35, 0.25)
    deviations = Float64[]
    rows = Vector{Dict{String, Any}}()
    for (index, ((t, opname), target)) in enumerate(zip(NATIVE_STAGES, targets))
        observed = stage_map(probe, t, opname)
        deviation = maximum(abs.(observed .- target))
        push!(deviations, deviation)
        push!(rows, Dict(
            "index" => index,
            "terrain" => t,
            "operator" => opname,
            "observed" => collect(observed),
            "target" => collect(target),
            "max_abs_deviation" => deviation,
        ))
    end
    max_deviation = maximum(deviations)
    @printf("contract_weld_max_abs_deviation=%.12e\n", max_deviation)
    max_deviation <= WELD_TOL || error(
        "CONTRACT WELD ABORT: max bloch_down deviation $(max_deviation) exceeds $(WELD_TOL); no basin API was called"
    )
    return Dict(
        "passed" => true,
        "tolerance" => WELD_TOL,
        "max_abs_deviation" => max_deviation,
        "source_sha256" => hashes,
        "stages" => rows,
    )
end

function affine_from_function(f)
    z = SVector(0.0, 0.0, 0.0)
    b = f(z)
    A = zeros(Float64, 3, 3)
    for j in 1:3
        e = SVector{3, Float64}(ntuple(i -> i == j ? 1.0 : 0.0, 3))
        A[:, j] .= f(e) .- b
    end
    return (A = A, b = b)
end

function compose_affines(parts)
    A = Matrix{Float64}(I, 3, 3)
    b = zeros(Float64, 3)
    for part in parts
        b = part.A * b + part.b
        A = part.A * A
    end
    return (A = A, b = SVector{3, Float64}(b))
end

apply_affine(affine, u) = SVector{3, Float64}(affine.A * u + affine.b)

operator_basis(name) = name in ("Ti", "Fe") ? "Z" : "X"

function build_schedule_affines()
    stage_affines = Dict{Tuple{Int, String}, Any}()
    for stage in NATIVE_STAGES
        t, opname = stage
        stage_affines[stage] = affine_from_function(u -> stage_map(u, t, opname))
    end
    grouped = vcat(
        [stage for stage in NATIVE_STAGES if operator_basis(stage[2]) == "Z"],
        [stage for stage in NATIVE_STAGES if operator_basis(stage[2]) == "X"],
    )
    schedules = Dict{String, Any}(
        "native" => compose_affines([stage_affines[s] for s in NATIVE_STAGES]),
        "reversed" => compose_affines([stage_affines[s] for s in reverse(NATIVE_STAGES)]),
        "grouped_same_basis" => compose_affines([stage_affines[s] for s in grouped]),
        "one_axis" => stage_affines[(0, "Fi")],
    )
    commuting_forward = affine_from_function() do u
        rho = flow(generator(0), bloch_to_density(u))
        density_to_bloch(apply_operator("Fe", apply_operator("Ti", rho)))
    end
    commuting_reverse = affine_from_function() do u
        rho = flow(generator(0), bloch_to_density(u))
        density_to_bloch(apply_operator("Ti", apply_operator("Fe", rho)))
    end
    commuting_gap = max(
        maximum(abs.(commuting_forward.A .- commuting_reverse.A)),
        maximum(abs.(commuting_forward.b .- commuting_reverse.b)),
    )
    commuting_gap <= 1.0e-12 || error("commuting control construction failed: order gap $commuting_gap")
    schedules["commuting_pair"] = commuting_forward
    conventions = Dict(
        "native" => ["t$(t):$op" for (t, op) in NATIVE_STAGES],
        "reversed" => ["t$(t):$op" for (t, op) in reverse(NATIVE_STAGES)],
        "grouped_same_basis" => ["t$(t):$op" for (t, op) in grouped],
        "grouped_rule" => "stable Z-basis block (Ti/Fe) followed by stable X-basis block (Te/Fi)",
        "commuting_pair" => "t0 terrain flow, then Z-dephasing Ti and Z-rotation Fe; reverse operator order is numerically identical",
        "commuting_pair_order_gap" => commuting_gap,
        "one_axis" => "t0 terrain flow followed by its native X-rotation Fi",
    )
    return schedules, conventions
end

function bloch_initial_conditions(rng, n::Int)
    points = SVector{3, Float64}[]
    while length(points) < n
        u = SVector(2rand(rng) - 1, 2rand(rng) - 1, 2rand(rng) - 1)
        norm(u) <= 1.0 && push!(points, u)
    end
    return points
end

function package_locations(mapper)
    locations = Dict{String, Any}()
    for (label, attractor) in extract_attractors(mapper)
        total = zeros(Float64, 3)
        count = 0
        for point in attractor
            total .+= point
            count += 1
        end
        count > 0 && (locations[string(label)] = collect(total ./ count))
    end
    return locations
end

function measure_rule(rule, initial_conditions, grid; parameters = nothing)
    u0 = SVector(0.0, 0.0, 0.0)
    ds = DeterministicIteratedMap(rule, u0, parameters)
    mapper = AttractorsViaRecurrences(
        ds,
        grid;
        sparse = true,
        consecutive_recurrences = 16,
        attractor_locate_steps = 32,
        consecutive_attractor_steps = 8,
        consecutive_basin_steps = 8,
        consecutive_lost_steps = 100,
        maximum_iterations = 1000,
    )
    fractions, labels = basins_fractions(mapper, initial_conditions; show_progress = false)
    converted = Dict(string(label) => Float64(fraction) for (label, fraction) in fractions)
    positive = sort([label for (label, fraction) in fractions if label > 0 && fraction > 0])
    lost_fraction = Float64(get(fractions, -1, 0.0))
    return Dict(
        "basin_fractions" => converted,
        "labels" => collect(labels),
        "positive_attractor_labels" => collect(positive),
        "attractor_count" => length(positive),
        "lost_fraction" => lost_fraction,
        "package_attractor_locations" => package_locations(mapper),
        "package_gate_valid" => lost_fraction == 0.0,
    )
end

function perturbation_convergence(affine)
    fixed_point = SVector{3, Float64}((Matrix{Float64}(I, 3, 3) - affine.A) \ affine.b)
    base = (0.95 / sqrt(3.0)) .* SVector(1.0, 1.0, 1.0)
    eps = 1.0e-7
    starts = [base]
    for j in 1:3, sign in (-1.0, 1.0)
        delta = SVector{3, Float64}(ntuple(i -> i == j ? sign * eps : 0.0, 3))
        push!(starts, base + delta)
    end
    finals = SVector{3, Float64}[]
    for start in starts
        u = start
        for _ in 1:64
            u = apply_affine(affine, u)
        end
        push!(finals, u)
    end
    spread = maximum(norm(finals[i] - finals[j]) for i in eachindex(finals) for j in eachindex(finals))
    fixed_error = maximum(norm(u - fixed_point) for u in finals)
    return Dict(
        "kind" => "single_basin_perturbation_convergence",
        "initial_radius" => norm(base),
        "perturbation" => eps,
        "iterations" => 64,
        "affine_fixed_point" => collect(fixed_point),
        "max_final_pairwise_spread" => spread,
        "max_distance_to_fixed_point" => fixed_error,
        "passed" => spread < 1.0e-9 && fixed_error < 1.0e-9,
    )
end

function schedule_measurements(schedules, initial_conditions, grid)
    results = Dict{String, Any}()
    for name in sort(collect(keys(schedules)))
        affine = schedules[name]
        rule(u, p, n) = apply_affine(p, u)
        measured = measure_rule(rule, initial_conditions, grid; parameters = affine)
        measured["perturbation_check"] = perturbation_convergence(affine)
        measured["trivial_single_basin"] = measured["attractor_count"] == 1 &&
            measured["lost_fraction"] == 0.0 &&
            length(measured["basin_fractions"]) == 1 &&
            abs(only(values(measured["basin_fractions"])) - 1.0) <= 1.0e-12
        results[name] = measured
        println("schedule=", name, " basin_fractions=", measured["basin_fractions"])
    end
    return results
end

function instrument_checks(initial_conditions, grid)
    center = SVector(0.10, -0.05, 0.15)
    negative_rule(u, p, n) = SVector{3, Float64}(0.5 .* u .+ center)
    positive_rule(u, p, n) = SVector(
        0.5 * u[1] + (u[1] >= 0 ? 0.3 : -0.3),
        0.5 * u[2],
        0.5 * u[3],
    )
    negative = measure_rule(negative_rule, initial_conditions, grid)
    negative["passed"] = negative["attractor_count"] == 1 &&
        negative["lost_fraction"] == 0.0 &&
        length(negative["basin_fractions"]) == 1 &&
        abs(only(values(negative["basin_fractions"])) - 1.0) <= 1.0e-12
    positive = measure_rule(positive_rule, initial_conditions, grid)
    positive_fractions = [
        fraction for (label, fraction) in positive["basin_fractions"]
        if parse(Int, label) > 0 && fraction > 0.0
    ]
    positive["passed"] = positive["attractor_count"] >= 2 &&
        positive["lost_fraction"] == 0.0 &&
        length(positive_fractions) >= 2 &&
        all(0.0 < fraction < 1.0 for fraction in positive_fractions)
    println("instrument_negative_single_global=", negative["passed"], " basin_fractions=", negative["basin_fractions"])
    println("instrument_positive_multistable=", positive["passed"], " basin_fractions=", positive["basin_fractions"])
    negative["passed"] || error("INSTRUMENT ABORT: single-global-attractor negative control was not exactly one basin of fraction 1")
    positive["passed"] || error("INSTRUMENT ABORT: multistable positive control did not resolve at least two nontrivial basins")
    return Dict("negative_single_global" => negative, "positive_multistable" => positive)
end

function json_escape(text::AbstractString)
    io = IOBuffer()
    for c in text
        if c == '"'
            print(io, "\\\"")
        elseif c == '\\'
            print(io, "\\\\")
        elseif c == '\n'
            print(io, "\\n")
        elseif c == '\r'
            print(io, "\\r")
        elseif c == '\t'
            print(io, "\\t")
        elseif Int(c) < 0x20
            @printf(io, "\\u%04x", Int(c))
        else
            print(io, c)
        end
    end
    return String(take!(io))
end

function write_json(io, value)
    if value === nothing
        print(io, "null")
    elseif value isa Bool
        print(io, value ? "true" : "false")
    elseif value isa Integer
        print(io, value)
    elseif value isa AbstractFloat
        isfinite(value) || error("cannot serialize non-finite float")
        print(io, repr(Float64(value)))
    elseif value isa AbstractString || value isa Symbol
        print(io, '"', json_escape(string(value)), '"')
    elseif value isa AbstractDict
        print(io, '{')
        keys_sorted = sort(collect(keys(value)); by = string)
        for (index, key) in enumerate(keys_sorted)
            index > 1 && print(io, ',')
            write_json(io, string(key))
            print(io, ':')
            write_json(io, value[key])
        end
        print(io, '}')
    elseif value isa Tuple || value isa AbstractArray
        print(io, '[')
        for (index, item) in enumerate(value)
            index > 1 && print(io, ',')
            write_json(io, item)
        end
        print(io, ']')
    else
        error("unsupported JSON value type $(typeof(value))")
    end
end

function next_result_path()
    version = 1
    while true
        path = joinpath(@__DIR__, "results_v$(version).json")
        !isfile(path) && return path
        version += 1
    end
end

function main()
    # Fail-first contract weld. No recurrence mapper, RNG, grid, or basin API exists before this returns.
    weld = contract_weld!()

    schedules, conventions = build_schedule_affines()
    rng = Xoshiro(SEED)
    initial_conditions = bloch_initial_conditions(rng, 384)
    axis = range(-1.05, 1.05; length = 49)
    grid = (axis, axis, axis)

    instruments = instrument_checks(initial_conditions, grid)
    schedule_results = schedule_measurements(schedules, initial_conditions, grid)
    package_valid = all(result["package_gate_valid"] for result in values(schedule_results))
    perturbations_valid = all(result["perturbation_check"]["passed"] for result in values(schedule_results))
    all_trivial = all(result["trivial_single_basin"] for result in values(schedule_results))
    honesty_conclusion = all_trivial ?
        "All five schedules have one attractor with basin fraction 1. Schedule-specificity at basin level is excluded within scope; differing fixed-point locations are reported only as geometry." :
        "At least one schedule has nontrivial package-reported basin structure; report the measured fractions without promotion beyond this scratch diagnostic."

    tool_calls = [Dict(
        "tool" => "Attractors.jl",
        "qualified_api/function" => "Attractors.AttractorsViaRecurrences + Attractors.basins_fractions",
        "input_object" => "DeterministicIteratedMap and shared seeded Bloch-ball initial conditions",
        "output_object" => "basin fractions, labels, and package-extracted attractors",
        "positive_case" => "piecewise contraction with two attracting fixed points must yield more than one nontrivial basin",
        "negative/erased_control" => "single global contraction must yield exactly one basin with fraction 1",
        "boundary_case" => "single-basin schedules use near-boundary perturbation convergence to the affine fixed point",
        "demotion_condition" => "any lost schedule fraction or either failed instrument check demotes/rejects the basin result",
        "gates" => ["all_pass", "basin_result"],
    )]

    all_pass = Bool(weld["passed"]) &&
        Bool(instruments["negative_single_global"]["passed"]) &&
        Bool(instruments["positive_multistable"]["passed"]) &&
        package_valid && perturbations_valid

    payload = Dict{String, Any}(
        "schema" => "attractors_basin_native_schedule_result_v1",
        "sim_id" => SIM_ID,
        "name" => "Attractors.jl native GKSL schedule basin diagnostic",
        "version" => 1,
        "classification" => CLASSIFICATION,
        "claim_ceiling" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "all_pass" => all_pass,
        "root_constraints_in_force" => ["finite carrier/probe/path set", "order-sensitive native stage composition"],
        "allowed_claims" => ["bounded package-gated basin fractions", "fixed-point location geometry only"],
        "blocked_consumers" => ["formal admission", "canonical scientific basin claim", "axis", "bridge", "physics", "manifold completion"],
        "seed" => SEED,
        "deterministic" => true,
        "reads_peer_result" => false,
        "command" => "/opt/homebrew/bin/julia --project=/Users/joshuaeisenhart/.julia/environments/codex-ratchet-attractors-v1.12 attractors_native_schedule.jl",
        "runner_identity" => Dict("engine" => "Julia", "julia_version" => string(VERSION), "binary" => joinpath(Sys.BINDIR, "julia")),
        "julia" => Dict(
            "ran" => true,
            "source_path" => joinpath(@__DIR__, "attractors_native_schedule.jl"),
            "active_project" => Base.active_project(),
            "packages_used" => ["Attractors", "StaticArrays"],
            "package_versions" => Dict("Attractors" => string(pkgversion(Attractors)), "StaticArrays" => string(pkgversion(StaticArrays))),
            "aligned_packages_load_bearing" => ["Attractors"],
            "reads_peer_result" => false,
        ),
        "contract_weld" => weld,
        "controls_and_schedule_conventions" => conventions,
        "instrument" => Dict(
            "grid" => Dict("lower" => -1.05, "upper" => 1.05, "length_per_axis" => 49),
            "initial_condition_count" => length(initial_conditions),
            "initial_conditions_inside_bloch_ball" => all(norm(u) <= 1.0 for u in initial_conditions),
            "recurrence" => Dict(
                "mapper" => "AttractorsViaRecurrences",
                "fractions_api" => "basins_fractions",
                "sparse" => true,
                "consecutive_recurrences" => 16,
                "attractor_locate_steps" => 32,
                "maximum_iterations" => 1000,
            ),
        ),
        "schedule_results" => schedule_results,
        "instrument_checks" => instruments,
        "all_schedules_trivial_single_basin" => all_trivial,
        "honesty_conclusion" => honesty_conclusion,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => tool_calls,
        "divergence_log" => [
            all_trivial ? "No schedule differs in basin count or basin fraction within scope." : "At least one package-reported basin structure differs; see schedule_results.",
            "Attractor locations are retained separately and are not promoted into basin-structure specificity.",
        ],
    )

    all_pass || error("RESULT ABORT: a computational or package gate failed")
    output_path = next_result_path()
    isfile(output_path) && error("APPEND-ONLY ABORT: refusing to overwrite $output_path")
    open(output_path, "w") do io
        write_json(io, payload)
        println(io)
    end
    isfile(output_path) || error("ARTIFACT PERSISTENCE ABORT: $output_path was not created")
    println(honesty_conclusion)
    println("result_path=", output_path)
    return payload
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
