#!/usr/bin/env julia

# basin_hierarchy_discovery_codex.jl
#
# Purpose:
#   Given an ordered ratchet flow, drive many finite seeds to fixed points and
#   discover whether there is (a) state-space convergence for each schedule and
#   (b) schedule-separated attractor structure with macro, sub, and sub-sub
#   hierarchy.
#
# Honest boundary:
#   The default flow is a stubbed affine contraction family. It is here to make
#   the scaffold executable and to test the metrics. It is not a Codex Ratchet
#   nonclassical basin receipt. A real run must provide the project ratchet order
#   and concrete maps via JSON input.
#
# Optional input:
#   julia --project=. layers/basin_hierarchy_discovery_codex.jl --input=flow.json
#
# Input schema:
# {
#   "kind": "ordered_ratchet_flow",
#   "input_status": "real",
#   "state_dimension": 3,
#   "steps": [
#     {"name": "T1", "affine_A": [[...]], "affine_b": [...]},
#     {"name": "T2", "affine_A": [[...]], "affine_b": [...]}
#   ],
#   "canonical_order": ["T1", "T2"],
#   "schedule_family": [["T1", "T1", "T2"], ["T2", "T1", "T2"]]
# }

using Dates
using JSON
using LinearAlgebra
using Random
using Statistics

const DEFAULT_RESULT_PATH = joinpath(@__DIR__, "basin_hierarchy_discovery_codex_results.json")
const DEFAULT_SEED_COUNT = 2048
const DEFAULT_CYCLES = 80
const DEFAULT_MACRO_EPS = 0.85
const DEFAULT_SUB_EPS = 0.28
const DEFAULT_SUBSUB_EPS = 0.09
const CONVERGENCE_TOL = 1.0e-7
const RESIDUAL_TOL = 1.0e-7
const DIFFEQ_LOADED = Ref(false)
const ATTRACTORS_LOADED = Ref(false)
const DIFFEQ_LOAD_ERROR = Ref{Union{Nothing,String}}(nothing)
const ATTRACTORS_LOAD_ERROR = Ref{Union{Nothing,String}}(nothing)

try
    @eval using Attractors
    ATTRACTORS_LOADED[] = true
catch err
    ATTRACTORS_LOAD_ERROR[] = sprint(showerror, err)
end

try
    @eval using DifferentialEquations
    DIFFEQ_LOADED[] = true
catch err
    DIFFEQ_LOAD_ERROR[] = sprint(showerror, err)
end

struct FlowStep
    name::String
    A::Matrix{Float64}
    b::Vector{Float64}
    input_status::String
end

function parse_args(args)
    opts = Dict{String,String}()
    for arg in args
        if startswith(arg, "--") && occursin("=", arg)
            key, value = split(arg[3:end], "=", limit=2)
            opts[key] = value
        end
    end
    return opts
end

function optional_tool_status()
    status = Dict{String,Any}()
    for pkg in ("Attractors", "DifferentialEquations")
        loaded = pkg == "Attractors" ? ATTRACTORS_LOADED[] : DIFFEQ_LOADED[]
        load_error = pkg == "Attractors" ? ATTRACTORS_LOAD_ERROR[] : DIFFEQ_LOAD_ERROR[]
        if Base.find_package(pkg) === nothing
            status[pkg] = Dict("available" => false, "loaded" => false, "role" => "not installed in active Julia environment")
            continue
        end
        if loaded
            status[pkg] = Dict(
                "available" => true,
                "loaded" => true,
                "role" => pkg == "DifferentialEquations" ?
                    "loaded; used for DiscreteProblem/FunctionMap cross-checks of the ordered map" :
                    "loaded; used to materialize the schedule-attractor cloud as a StateSpaceSet before custom hierarchy clustering"
            )
        else
            status[pkg] = Dict(
                "available" => true,
                "loaded" => false,
                "role" => "available but failed to load; direct discrete ordered-flow iteration used",
                "error" => load_error
            )
        end
    end
    return status
end

function to_matrix(x, dim::Int)
    A = Matrix{Float64}(undef, dim, dim)
    for i in 1:dim, j in 1:dim
        A[i, j] = Float64(x[i][j])
    end
    return A
end

function to_vector(x, dim::Int)
    length(x) == dim || error("vector length $(length(x)) does not match state_dimension $dim")
    return [Float64(v) for v in x]
end

function all_binary_schedules(names::Vector{String}, depth::Int)
    schedules = Vector{Vector{String}}()
    function rec(prefix, k)
        if k == depth
            push!(schedules, copy(prefix))
            return
        end
        for name in names
            push!(prefix, name)
            rec(prefix, k + 1)
            pop!(prefix)
        end
    end
    rec(String[], 0)
    return schedules
end

function stub_flow()
    dim = 3
    lambda = 0.35
    A1 = lambda .* Matrix{Float64}(I, dim, dim)
    A2 = lambda .* Matrix{Float64}(I, dim, dim)
    # Translation-only affine contractions are enough to make order matter:
    # F2(F1(x)) != F1(F2(x)) when b1 != b2 and lambda != 1.
    b1 = (1.0 - lambda) .* [-1.0, -0.18, 0.06]
    b2 = (1.0 - lambda) .* [1.0, 0.18, -0.06]
    steps = Dict(
        "T1" => FlowStep("T1", A1, b1, "stubbed_affine_contraction"),
        "T2" => FlowStep("T2", A2, b2, "stubbed_affine_contraction"),
    )
    schedules = all_binary_schedules(["T1", "T2"], 4)
    return (
        source = "stub",
        input_status = "stubbed",
        state_dimension = dim,
        steps = steps,
        schedules = schedules,
        notes = [
            "Stub creates 16 length-4 schedule words over two noncommuting affine contractions.",
            "It exercises convergence, fixed-point residual, spectral gap, schedule separation, and hierarchy criteria.",
            "It is not a nonclassical, CPTP, PEPS, PEPS3D, or formal_scout basin run.",
        ],
    )
end

function load_flow(path::String)
    raw = JSON.parsefile(path)
    dim = Int(raw["state_dimension"])
    status = get(raw, "input_status", "real_unverified_by_scaffold")
    steps = Dict{String,FlowStep}()
    for row in raw["steps"]
        name = String(row["name"])
        A_key = haskey(row, "affine_A") ? "affine_A" : "A"
        b_key = haskey(row, "affine_b") ? "affine_b" : "b"
        steps[name] = FlowStep(name, to_matrix(row[A_key], dim), to_vector(row[b_key], dim), status)
    end

    schedules = Vector{Vector{String}}()
    if haskey(raw, "schedule_family")
        for sched in raw["schedule_family"]
            push!(schedules, [String(s) for s in sched])
        end
    elseif haskey(raw, "canonical_order")
        push!(schedules, [String(s) for s in raw["canonical_order"]])
    else
        error("input must provide schedule_family or canonical_order")
    end
    return (
        source = path,
        input_status = status,
        state_dimension = dim,
        steps = steps,
        schedules = schedules,
        notes = [String(x) for x in get(raw, "notes", Any[])],
    )
end

function apply_step(step::FlowStep, x::Vector{Float64})
    return step.A * x + step.b
end

function compose_schedule(steps::Dict{String,FlowStep}, schedule::Vector{String})
    dim = length(first(values(steps)).b)
    A = Matrix{Float64}(I, dim, dim)
    b = zeros(Float64, dim)
    for name in schedule
        haskey(steps, name) || error("schedule references missing step $name")
        st = steps[name]
        A = st.A * A
        b = st.A * b + st.b
    end
    return A, b
end

function iterate_schedule(steps, schedule, x0::Vector{Float64}, cycles::Int)
    x = copy(x0)
    for _ in 1:cycles
        for name in schedule
            x = apply_step(steps[name], x)
        end
    end
    return x
end

function schedule_cycle(steps, schedule, x::Vector{Float64})
    y = copy(x)
    for name in schedule
        y = apply_step(steps[name], y)
    end
    return y
end

function diffeq_discrete_crosscheck(steps, schedule, x0::Vector{Float64}, cycles::Int)
    if !DIFFEQ_LOADED[]
        return Dict(
            "used" => false,
            "reason" => "DifferentialEquations did not load",
            "error" => nothing,
        )
    end
    try
        f(u, p, t) = schedule_cycle(steps, schedule, Vector{Float64}(u))
        prob = DiscreteProblem(f, copy(x0), (0, cycles))
        sol = solve(prob, FunctionMap(); save_everystep=false)
        direct = iterate_schedule(steps, schedule, x0, cycles)
        err = norm(Vector{Float64}(sol.u[end]) .- direct)
        return Dict(
            "used" => true,
            "method" => "DifferentialEquations.DiscreteProblem + FunctionMap",
            "error_vs_direct_iteration" => err,
            "pass" => err <= 1.0e-10,
        )
    catch err
        return Dict(
            "used" => false,
            "reason" => "DifferentialEquations discrete cross-check failed",
            "error" => sprint(showerror, err),
        )
    end
end

function seed_states(dim::Int, n::Int)
    rng = MersenneTwister(20260601)
    seeds = Vector{Vector{Float64}}()
    while length(seeds) < n
        x = rand(rng, dim) .* 2.0 .- 1.0
        norm(x) <= sqrt(dim) || continue
        push!(seeds, x)
    end
    return seeds
end

dist(a, b) = norm(a .- b)

function max_pairwise_distance(points)
    length(points) <= 1 && return 0.0
    m = 0.0
    for i in 1:(length(points) - 1), j in (i + 1):length(points)
        m = max(m, dist(points[i], points[j]))
    end
    return m
end

function greedy_cluster(points, labels, eps::Float64)
    centroids = Vector{Vector{Float64}}()
    members = Vector{Vector{Int}}()
    for (i, p) in enumerate(points)
        if isempty(centroids)
            push!(centroids, copy(p))
            push!(members, [i])
            continue
        end
        ds = [dist(p, c) for c in centroids]
        k = argmin(ds)
        if ds[k] <= eps
            push!(members[k], i)
            centroids[k] = vec(mean(reduce(hcat, points[members[k]]), dims=2))
        else
            push!(centroids, copy(p))
            push!(members, [i])
        end
    end

    order = sortperm(1:length(centroids); by=i -> (centroids[i][1], length(members[i])))
    out = Vector{Dict{String,Any}}()
    for (new_idx, old_idx) in enumerate(order)
        inds = members[old_idx]
        pts = points[inds]
        push!(out, Dict(
            "cluster_id" => new_idx,
            "count" => length(inds),
            "labels" => labels[inds],
            "centroid" => round.(centroids[old_idx], digits=8),
            "diameter" => round(max_pairwise_distance(pts), digits=10),
        ))
    end
    return out
end

function cluster_indices(points, eps::Float64, indices::Vector{Int})
    centroids = Vector{Vector{Float64}}()
    members = Vector{Vector{Int}}()
    for idx in indices
        p = points[idx]
        if isempty(centroids)
            push!(centroids, copy(p))
            push!(members, [idx])
            continue
        end
        ds = [dist(p, c) for c in centroids]
        k = argmin(ds)
        if ds[k] <= eps
            push!(members[k], idx)
            centroids[k] = vec(mean(reduce(hcat, points[members[k]]), dims=2))
        else
            push!(centroids, copy(p))
            push!(members, [idx])
        end
    end
    return members
end

function nested_hierarchy(points, labels, thresholds)
    all_indices = collect(eachindex(points))
    macro_groups = cluster_indices(points, thresholds[1], all_indices)
    hierarchy = Vector{Dict{String,Any}}()
    for (i, macro_inds) in enumerate(macro_groups)
        sub = cluster_indices(points, thresholds[2], macro_inds)
        subnodes = Vector{Dict{String,Any}}()
        for (j, sub_inds) in enumerate(sub)
            subsub = cluster_indices(points, thresholds[3], sub_inds)
            subsubnodes = [Dict(
                "id" => "M$(i).S$(j).SS$(k)",
                "count" => length(ss),
                "labels" => labels[ss],
                "diameter" => round(max_pairwise_distance(points[ss]), digits=10),
            ) for (k, ss) in enumerate(subsub)]
            push!(subnodes, Dict(
                "id" => "M$(i).S$(j)",
                "count" => length(sub_inds),
                "labels" => labels[sub_inds],
                "diameter" => round(max_pairwise_distance(points[sub_inds]), digits=10),
                "children" => subsubnodes,
            ))
        end
        push!(hierarchy, Dict(
            "id" => "M$(i)",
            "count" => length(macro_inds),
            "labels" => labels[macro_inds],
            "diameter" => round(max_pairwise_distance(points[macro_inds]), digits=10),
            "children" => subnodes,
        ))
    end
    return hierarchy
end

function minimum_inter_schedule_distance(points)
    length(points) <= 1 && return 0.0
    m = Inf
    for i in 1:(length(points) - 1), j in (i + 1):length(points)
        m = min(m, dist(points[i], points[j]))
    end
    return isfinite(m) ? m : 0.0
end

function spectral_gap(A::Matrix{Float64})
    vals = eigvals(A)
    radius = maximum(abs.(vals))
    return max(0.0, 1.0 - radius), radius
end

function schedule_label(schedule)
    return join(schedule, "∘")
end

function evaluate_flow(flow; nseeds::Int, cycles::Int, macro_eps::Float64, sub_eps::Float64, subsub_eps::Float64)
    seeds = seed_states(flow.state_dimension, nseeds)
    schedule_results = Vector{Dict{String,Any}}()
    attractors = Vector{Vector{Float64}}()
    labels = String[]
    diffeq_crosschecks = Vector{Dict{String,Any}}()

    for schedule in flow.schedules
        finals = [iterate_schedule(flow.steps, schedule, seed, cycles) for seed in seeds]
        centroid = vec(mean(reduce(hcat, finals), dims=2))
        A, b = compose_schedule(flow.steps, schedule)
        residual = norm(A * centroid + b - centroid)
        gap, radius = spectral_gap(A)
        width = max_pairwise_distance(finals[1:min(length(finals), 128)])
        convergence_metric = maximum([dist(f, centroid) for f in finals])
        crosscheck = diffeq_discrete_crosscheck(flow.steps, schedule, seeds[1], cycles)
        push!(diffeq_crosschecks, merge(Dict("schedule" => schedule_label(schedule)), crosscheck))
        push!(attractors, centroid)
        push!(labels, schedule_label(schedule))
        push!(schedule_results, Dict(
            "schedule" => schedule,
            "label" => schedule_label(schedule),
            "seed_count" => nseeds,
            "cycles" => cycles,
            "state_space_convergence_metric_max_distance_to_centroid" => convergence_metric,
            "state_space_width_sampled_max_pairwise_128" => width,
            "fixed_point_residual" => residual,
            "spectral_radius" => radius,
            "spectral_gap_1_minus_radius" => gap,
            "differential_equations_crosscheck" => crosscheck,
            "centroid" => round.(centroid, digits=10),
            "state_space_converged" => convergence_metric <= CONVERGENCE_TOL,
            "fixed_point_residual_pass" => residual <= RESIDUAL_TOL,
        ))
    end

    attractors_receipt = if ATTRACTORS_LOADED[]
        try
            cloud = StateSpaceSet(attractors)
            Dict(
                "used" => true,
                "method" => "Attractors.StateSpaceSet over schedule attractor centroids",
                "point_count" => length(cloud),
                "dimension" => flow.state_dimension,
            )
        catch err
            Dict(
                "used" => false,
                "method" => "Attractors.StateSpaceSet over schedule attractor centroids",
                "error" => sprint(showerror, err),
            )
        end
    else
        Dict(
            "used" => false,
            "reason" => "Attractors did not load",
        )
    end

    macro_clusters = greedy_cluster(attractors, labels, macro_eps)
    sub_clusters = greedy_cluster(attractors, labels, sub_eps)
    subsub_clusters = greedy_cluster(attractors, labels, subsub_eps)
    hierarchy = nested_hierarchy(attractors, labels, [macro_eps, sub_eps, subsub_eps])

    max_state_convergence = maximum([r["state_space_convergence_metric_max_distance_to_centroid"] for r in schedule_results])
    max_residual = maximum([r["fixed_point_residual"] for r in schedule_results])
    min_schedule_sep = minimum_inter_schedule_distance(attractors)
    sep_ratio = min_schedule_sep / max(max_state_convergence, eps(Float64))

    sub_split_parents = count(node -> length(node["children"]) >= 2, hierarchy)
    subsub_split_parents = 0
    for node in hierarchy
        for child in node["children"]
            subsub_split_parents += length(child["children"]) >= 2 ? 1 : 0
        end
    end
    hierarchy_depth_pass =
        length(macro_clusters) >= 2 &&
        sub_split_parents >= 1 &&
        subsub_split_parents >= 1

    state_space_vs_schedule_separation_pass =
        max_state_convergence <= CONVERGENCE_TOL &&
        min_schedule_sep > 10.0 * max(max_state_convergence, RESIDUAL_TOL)

    hierarchy_criterion = Dict(
        "definition" => "macro/sub/sub-sub clusters must split schedule attractors at nested thresholds while each schedule is monostable over many seeds",
        "macro_eps" => macro_eps,
        "sub_eps" => sub_eps,
        "subsub_eps" => subsub_eps,
        "macro_cluster_count" => length(macro_clusters),
        "sub_cluster_count" => length(sub_clusters),
        "subsub_cluster_count" => length(subsub_clusters),
        "macro_parents_with_sub_split" => sub_split_parents,
        "sub_parents_with_subsub_split" => subsub_split_parents,
        "pass" => hierarchy_depth_pass && state_space_vs_schedule_separation_pass,
        "status" => flow.input_status == "stubbed" ? "stub_metric_pass_only" : "real_input_metric_pass_not_admission",
    )

    return Dict(
        "schedule_results" => schedule_results,
        "macro_clusters" => macro_clusters,
        "sub_clusters" => sub_clusters,
        "subsub_clusters" => subsub_clusters,
        "hierarchy" => hierarchy,
        "convergence_metric" => Dict(
            "max_state_space_distance_to_centroid_across_schedules" => max_state_convergence,
            "max_fixed_point_residual" => max_residual,
            "all_schedules_converged" => max_state_convergence <= CONVERGENCE_TOL,
        ),
        "fixed_point_residual" => Dict(
            "max" => max_residual,
            "tolerance" => RESIDUAL_TOL,
            "pass" => max_residual <= RESIDUAL_TOL,
        ),
        "spectral_gap" => Dict(
            "min_gap" => minimum([r["spectral_gap_1_minus_radius"] for r in schedule_results]),
            "max_spectral_radius" => maximum([r["spectral_radius"] for r in schedule_results]),
            "meaning" => "For affine input maps only: 1 - spectral radius of the composed schedule map.",
        ),
        "tool_use_receipts" => Dict(
            "DifferentialEquations" => Dict(
                "crosscheck_count" => length(diffeq_crosschecks),
                "all_crosschecks_pass" => all(get(x, "pass", false) for x in diffeq_crosschecks),
                "crosschecks" => diffeq_crosschecks,
            ),
            "Attractors" => attractors_receipt,
        ),
        "state_space_vs_schedule_separation" => Dict(
            "max_state_space_convergence" => max_state_convergence,
            "min_schedule_attractor_separation" => min_schedule_sep,
            "separation_ratio" => sep_ratio,
            "pass" => state_space_vs_schedule_separation_pass,
            "reading" => "state-space basin if many seeds collapse per schedule; schedule basin if different ordered schedules have separated fixed points",
        ),
        "hierarchy_criterion" => hierarchy_criterion,
    )
end

function source_quotes()
    return [
        Dict(
            "file" => "system_v5/grok_sim/MANIFOLD_DEEP_BASIN_STRATEGY.md",
            "section" => "Phase 1 — Probe-Side Strengthening / Change 1e",
            "quote" => "Run the 5-chart × 3-phase probe under 5+ random seeds for the underlying ratchet state initialization. Record `min_basin_gap_across_seeds`, `min_holonomy_gap_across_seeds`.",
            "line_cite" => "lines 152-156",
        ),
        Dict(
            "file" => "system_v5/grok_sim/HANDOFF_NESTED_BASIN_ARCHITECTURE_AND_TOOLING_BLOCK_20260520.md",
            "section" => "0b. W7 ALIGNMENT NOTE",
            "quote" => "No basin claim until fixed-state / fixed-observable / generated-channel evidence exists on the named E=8/E=16 substrate.",
            "line_cite" => "line 47",
        ),
        Dict(
            "file" => "system_v5/grok_sim/HANDOFF_NESTED_BASIN_ARCHITECTURE_AND_TOOLING_BLOCK_20260520.md",
            "section" => "1. Executive summary",
            "quote" => "The architectural reframe: layers are NOT basins; they are ratcheting mechanisms that drive a constraint basin downstream; axes 0-6 are DOFs within that basin.",
            "line_cite" => "line 534",
        ),
        Dict(
            "file" => "system_v5/grok_sim/HANDOFF_NESTED_BASIN_ARCHITECTURE_AND_TOOLING_BLOCK_20260520.md",
            "section" => "30. iter_176-179 — full Φ_engine cycle runs",
            "quote" => "Multi-basin structure only appears when **multiple engines are composed sequentially**.",
            "line_cite" => "line 1873",
        ),
    ]
end

function source_gaps(flow)
    gaps = String[]
    if flow.input_status == "stubbed"
        push!(gaps, "No real ordered ratchet flow was provided; default affine contractions are stub inputs.")
    end
    push!(gaps, "The named docs do not provide a complete Julia-ready ratchet-order map schema.")
    push!(gaps, "The named docs do not provide PEPS3D Lindblad dynamics or an admitted E=8/E=16 fixed-state/fixed-observable/generated-channel receipt.")
    push!(gaps, "The hierarchy thresholds in this scaffold are explicit diagnostics, not source-cited formal admission thresholds.")
    return gaps
end

function main()
    opts = parse_args(ARGS)
    flow = haskey(opts, "input") ? load_flow(opts["input"]) : stub_flow()
    nseeds = parse(Int, get(opts, "seeds", string(DEFAULT_SEED_COUNT)))
    cycles = parse(Int, get(opts, "cycles", string(DEFAULT_CYCLES)))
    macro_eps = parse(Float64, get(opts, "macro-eps", string(DEFAULT_MACRO_EPS)))
    sub_eps = parse(Float64, get(opts, "sub-eps", string(DEFAULT_SUB_EPS)))
    subsub_eps = parse(Float64, get(opts, "subsub-eps", string(DEFAULT_SUBSUB_EPS)))
    outpath = get(opts, "output", DEFAULT_RESULT_PATH)

    tool_status = optional_tool_status()
    evaluation = evaluate_flow(flow; nseeds=nseeds, cycles=cycles, macro_eps=macro_eps, sub_eps=sub_eps, subsub_eps=subsub_eps)

    all_metrics_pass =
        evaluation["convergence_metric"]["all_schedules_converged"] &&
        evaluation["fixed_point_residual"]["pass"] &&
        evaluation["state_space_vs_schedule_separation"]["pass"] &&
        evaluation["hierarchy_criterion"]["pass"]

    receipt = Dict(
        "kind" => "basin_hierarchy_discovery_codex",
        "script" => "layers/basin_hierarchy_discovery_codex.jl",
        "generated_at" => string(now(UTC)),
        "classification" => "scaffold_diagnostic",
        "promotion_allowed" => false,
        "input_source" => flow.source,
        "input_status" => flow.input_status,
        "real_vs_stubbed_inputs" => Dict(
            "flow_maps" => flow.input_status == "stubbed" ? "stubbed" : "provided_by_input",
            "schedule_family" => flow.input_status == "stubbed" ? "stubbed" : "provided_by_input",
            "metrics" => "real computations over the active flow object",
            "nonclassical_admission" => "not claimed",
        ),
        "flow_notes" => flow.notes,
        "state_dimension" => flow.state_dimension,
        "step_names" => collect(keys(flow.steps)),
        "schedule_count" => length(flow.schedules),
        "seed_count" => nseeds,
        "cycles" => cycles,
        "tool_status" => tool_status,
        "source_quotes" => source_quotes(),
        "anti_hallucination_gaps" => source_gaps(flow),
        "evaluation" => evaluation,
        "all_metrics_pass" => all_metrics_pass,
        "status_label" => "runs",
        "claim_boundary" => "This scaffold discovers attractor-like hierarchy for the supplied finite ordered-flow maps. It does not admit a Codex Ratchet nonclassical basin, PEPS3D layer, W7 result, or formal_scout claim.",
        "what_must_exist_before_real_run" => [
            "A concrete ordered ratchet flow: finite state dimension, named step maps, and exact schedule order/family.",
            "For project evidence, the maps must be the real ratchet maps, not affine stubs.",
            "For nonclassical promotion, the lower finite-map gate must provide carrier, domain/codomain, controls, PEPS3D anchor, spinor/quaternion realization where applicable, and receipt paths.",
            "For W7-style basin claims, fixed-state / fixed-observable / generated-channel evidence on E=8/E=16 must exist before calling the output a basin claim.",
        ],
    )

    open(outpath, "w") do io
        JSON.print(io, receipt, 2)
        write(io, "\n")
    end

    println("BASIN HIERARCHY DISCOVERY CODEX")
    println("input_source: $(receipt["input_source"])")
    println("input_status: $(receipt["input_status"])")
    println("seed_count: $nseeds")
    println("schedule_count: $(length(flow.schedules))")
    println("convergence_max: $(evaluation["convergence_metric"]["max_state_space_distance_to_centroid_across_schedules"])")
    println("fixed_point_residual_max: $(evaluation["fixed_point_residual"]["max"])")
    println("spectral_gap_min: $(evaluation["spectral_gap"]["min_gap"])")
    println("schedule_min_separation: $(evaluation["state_space_vs_schedule_separation"]["min_schedule_attractor_separation"])")
    println("macro/sub/subsub clusters: $(evaluation["hierarchy_criterion"]["macro_cluster_count"])/$(evaluation["hierarchy_criterion"]["sub_cluster_count"])/$(evaluation["hierarchy_criterion"]["subsub_cluster_count"])")
    println("hierarchy_pass: $(evaluation["hierarchy_criterion"]["pass"])")
    println("all_metrics_pass: $all_metrics_pass")
    println("wrote: $outpath")
end

main()
