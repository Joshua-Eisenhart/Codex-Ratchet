#!/usr/bin/env julia

"""
Deep operational probe for the strict Julia carrier.

This is an integration diagnostic, not a scientific proof.  Every direct
non-stdlib dependency in `system_v5/julia_carrier/Project.toml` receives a
positive case, a negative control, a boundary case, a bounded stress case, and
an adjacent-package integration edge.  A red package row is evidence and does
not prevent the receipt from being written.

Usage:
    julia --project=system_v5/julia_carrier julia_core_deep_stress.jl --output PATH
    julia --project=system_v5/julia_carrier julia_core_deep_stress.jl PATH
"""

import Dates
import LinearAlgebra
import SHA
import TOML

const DIRECT_NON_STDLIB = [
    "Attractors",
    "ChaosTools",
    "CliffordAlgebras",
    "DifferentialEquations",
    "DynamicalSystems",
    "Graphs",
    "Grassmann",
    "ITensorMPS",
    "ITensors",
    "JSON",
    "JSON3",
    "Manifolds",
    "Octonions",
    "QuantumClifford",
    "QuantumOptics",
    "QuantumToolbox",
    "Quaternions",
    "StaticArrays",
    "Symbolics",
    "Yao",
    "Z3",
]

const DIRECT_STDLIB_SUPPORT = ["Dates", "LinearAlgebra", "SHA"]
const IMPORT_STATUS = Dict{String,Any}()

function error_text(err, bt = nothing)
    if bt === nothing
        return sprint(showerror, err)
    end
    sprint(showerror, err, bt)
end

function require_package(name::String)
    started = time_ns()
    try
        # Base.require performs Julia's actual package load while the explicit
        # const binding below avoids Julia 1.12 dynamic-global world-age warnings.
        mod = Base.require(Main, Symbol(name))
        IMPORT_STATUS[name] = (
            pass = true,
            version = string(something(Base.pkgversion(mod), "unknown")),
            module_path = something(Base.pathof(mod), "unknown"),
            error = nothing,
            duration_ms = round((time_ns() - started) / 1.0e6; digits = 3),
        )
        return mod
    catch err
        IMPORT_STATUS[name] = (
            pass = false,
            version = nothing,
            module_path = nothing,
            error = error_text(err, catch_backtrace()),
            duration_ms = round((time_ns() - started) / 1.0e6; digits = 3),
        )
        return nothing
    end
end

const Attractors = require_package("Attractors")
const ChaosTools = require_package("ChaosTools")
const CliffordAlgebras = require_package("CliffordAlgebras")
const DifferentialEquations = require_package("DifferentialEquations")
const DynamicalSystems = require_package("DynamicalSystems")
const Graphs = require_package("Graphs")
const Grassmann = require_package("Grassmann")
const ITensorMPS = require_package("ITensorMPS")
const ITensors = require_package("ITensors")
const JSON = require_package("JSON")
const JSON3 = require_package("JSON3")
const Manifolds = require_package("Manifolds")
const Octonions = require_package("Octonions")
const QuantumClifford = require_package("QuantumClifford")
const QuantumOptics = require_package("QuantumOptics")
const QuantumToolbox = require_package("QuantumToolbox")
const Quaternions = require_package("Quaternions")
const StaticArrays = require_package("StaticArrays")
const Symbolics = require_package("Symbolics")
const Yao = require_package("Yao")
const Z3 = require_package("Z3")

function output_path(args::Vector{String})
    isempty(args) && error("missing output path; use --output PATH or a first positional argument")
    if args[1] == "--output"
        length(args) == 2 || error("--output requires exactly one path")
        return abspath(args[2])
    elseif startswith(args[1], "--output=")
        length(args) == 1 || error("--output=PATH cannot be combined with extra arguments")
        value = split(args[1], "="; limit = 2)[2]
        isempty(value) && error("--output= requires a nonempty path")
        return abspath(value)
    elseif length(args) == 1
        return abspath(args[1])
    end
    error("unexpected arguments; use --output PATH or a first positional argument")
end

sha256_file(path::String) = bytes2hex(SHA.sha256(read(path)))

function observed(pass::Bool, value)
    (pass = pass, observed = value)
end

function run_case(label::String, expected::String, f::Function)
    started = time_ns()
    try
        result = f()
        result isa NamedTuple || error("case must return a NamedTuple")
        hasproperty(result, :pass) || error("case result lacks pass")
        hasproperty(result, :observed) || error("case result lacks observed")
        return (
            label = label,
            pass = Bool(result.pass),
            expected = expected,
            observed = result.observed,
            error = nothing,
            duration_ms = round((time_ns() - started) / 1.0e6; digits = 3),
        )
    catch err
        return (
            label = label,
            pass = false,
            expected = expected,
            observed = nothing,
            error = error_text(err, catch_backtrace()),
            duration_ms = round((time_ns() - started) / 1.0e6; digits = 3),
        )
    end
end

# `do` blocks are passed as the first positional argument in Julia.
run_case(f::Function, label::String, expected::String) = run_case(label, expected, f)

function expected_error(f::Function, expected_type::Type)
    try
        f()
        return observed(false, (threw = false, error_type = nothing))
    catch err
        return observed(
            err isa expected_type,
            (threw = true, error_type = string(typeof(err)), message = sprint(showerror, err)),
        )
    end
end

function package_row(
    package::String,
    kind::String,
    qualified_api::Vector{String},
    demotion_condition::String,
    positive,
    negative,
    boundary,
    stress,
    adjacent,
)
    import_status = IMPORT_STATUS[package]
    demotion = (
        passed = negative.pass && !isempty(demotion_condition),
        method = "executed negative/failure control bound to the declared demotion condition",
        condition = demotion_condition,
        qualified_api = join(qualified_api, "; "),
        observed = negative.observed,
        error = negative.error,
    )
    tool_calls = [(
        tool = package,
        qualified_api = join(qualified_api, "; "),
        probe_function = "make_rows/$(package)",
        executed = true,
        load_bearing = true,
        raw_probe_recorded = true,
        input_object = (
            positive = positive.expected,
            negative = negative.expected,
            boundary = boundary.expected,
            stress = stress.expected,
        ),
        output_object = (
            positive = positive.observed,
            negative = negative.observed,
            boundary = boundary.observed,
            stress = stress.observed,
        ),
        case_bindings = (
            positive = (passed = positive.pass, duration_ms = positive.duration_ms),
            negative = (passed = negative.pass, duration_ms = negative.duration_ms),
            boundary = (passed = boundary.pass, duration_ms = boundary.duration_ms),
            stress = (passed = stress.pass, duration_ms = stress.duration_ms),
        ),
        gates = ["positive", "negative", "boundary", "stress", "demotion", "adjacent_integration_edge"],
    )]
    operational_pass =
        import_status.pass &&
        positive.pass && negative.pass && boundary.pass && stress.pass && adjacent.pass && demotion.passed
    (
        package = package,
        role = "current_carrier_member",
        independent_engine = kind == "engine",
        kind = kind,
        qualified_api = qualified_api,
        version = import_status.version,
        import_status = import_status,
        positive = positive,
        negative = negative,
        boundary = boundary,
        stress = stress,
        adjacent_integration_edge = adjacent,
        demotion_condition = demotion_condition,
        demotion = demotion,
        tool_calls = tool_calls,
        operational_pass = operational_pass,
    )
end

function logistic_system(r::Float64 = 4.0)
    f(u, p, n) = StaticArrays.SA[p[1] * u[1] * (1.0 - u[1])]
    DynamicalSystems.DiscreteDynamicalSystem(f, StaticArrays.SA[0.2], [r])
end

function basin_metrics(points::Int)
    ds = DynamicalSystems.CoupledODEs(
        (u, p, t) -> StaticArrays.SA[u[1] - u[1]^3],
        StaticArrays.SA[0.2],
    )
    attractor_sets = Dict(
        1 => DynamicalSystems.StateSpaceSet([StaticArrays.SA[-1.0]]),
        2 => DynamicalSystems.StateSpaceSet([StaticArrays.SA[1.0]]),
    )
    mapper = Attractors.AttractorsViaProximity(ds, attractor_sets; Ttr = 5)
    grid = (range(-1.5, 1.5; length = points),)
    basins, returned = Attractors.basins_of_attraction(mapper, grid; show_progress = false)
    labels = sort!(unique(Int.(vec(basins))))
    (labels = labels, attractor_count = length(returned), sample_count = length(basins))
end

function clifford_generators(n::Int)
    algebra = CliffordAlgebras.CliffordAlgebra(n, 0)
    generators = [getproperty(algebra, Symbol("e$(i)")) for i in 1:n]
    algebra, generators
end

grassmann_basis(n::Int) = Grassmann.Λ(n)

function qbasis(index0::Int)
    Quaternions.Quaternion(ntuple(k -> k == index0 + 1 ? 1.0 : 0.0, 4)...)
end

function obasis(index0::Int)
    Octonions.Octonion(ntuple(k -> k == index0 + 1 ? 1.0 : 0.0, 8)...)
end

quat_coeffs(q) = [Float64(getfield(q, i)) for i in 1:4]
oct_coeffs(o) = [Float64(getfield(o, i)) for i in 1:8]

function tensor_basis_pair()
    i = ITensors.Index(2, "deep-stress-i")
    left = ITensors.ITensor(i)
    right = ITensors.ITensor(i)
    left[i => 1] = 1.0
    right[i => 2] = 1.0
    i, left, right
end

function z3_int_bounds!(solver, x, lo::Int, hi::Int, ctx)
    Z3.add(solver, Z3.Not(x < Z3.IntVal(lo, ctx)))
    Z3.add(solver, x < Z3.IntVal(hi + 1, ctx))
end

function z3_graph_coloring(g, colors::Int)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    vars = [Z3.IntVar("color_$(colors)_$(i)", ctx) for i in 1:Graphs.nv(g)]
    for x in vars
        z3_int_bounds!(solver, x, 0, colors - 1, ctx)
    end
    for edge in Graphs.edges(g)
        Z3.add(solver, Z3.Not(vars[Graphs.src(edge)] == vars[Graphs.dst(edge)]))
    end
    string(Z3.check(solver))
end

function make_rows()
    rows = Any[]

    push!(rows, package_row(
        "Attractors",
        "engine",
        ["Attractors.AttractorsViaProximity", "Attractors.basins_of_attraction"],
        "demote if both known fixed points are not recovered, the invalid one-attractor control is accepted silently, or bounded grid scaling fails",
        run_case("two fixed-point basins", "both -1 and +1 attractors are mapped") do
            metrics = basin_metrics(31)
            observed(metrics.attractor_count == 2 && all(x -> x in metrics.labels, [1, 2]), metrics)
        end,
        run_case("degenerate automatic epsilon", "a one-point one-attractor mapper rejects automatic epsilon=0") do
            expected_error(ArgumentError) do
                ds = DynamicalSystems.CoupledODEs(
                    (u, p, t) -> StaticArrays.SA[u[1] - u[1]^3],
                    StaticArrays.SA[0.2],
                )
                only = Dict(1 => DynamicalSystems.StateSpaceSet([StaticArrays.SA[-1.0]]))
                Attractors.AttractorsViaProximity(ds, only; Ttr = 5)
            end
        end,
        run_case("separatrix boundary", "the unstable zero seed is reported as unmapped (-1)") do
            metrics = basin_metrics(31)
            observed(-1 in metrics.labels, metrics)
        end,
        run_case("dense bounded grid", "81 initial conditions complete with both attractors") do
            metrics = basin_metrics(81)
            observed(metrics.sample_count == 81 && metrics.attractor_count == 2, metrics)
        end,
        run_case("DynamicalSystems + StaticArrays edge", "the mapper consumes a CoupledODEs/SVector system and returns 21 labels") do
            metrics = basin_metrics(21)
            observed(metrics.sample_count == 21 && all(x -> x in metrics.labels, [1, 2]), metrics)
        end,
    ))

    push!(rows, package_row(
        "ChaosTools",
        "engine",
        ["ChaosTools.lyapunov"],
        "demote if the chaotic and stable logistic controls do not separate in exponent sign or the long-run estimate is non-finite",
        run_case("chaotic logistic exponent", "r=4 has a positive exponent near log(2)") do
            value = ChaosTools.lyapunov(logistic_system(4.0), 1_000; Ttr = 200)
            observed(isfinite(value) && value > 0.5, value)
        end,
        run_case("stable logistic control", "r=2 has a strictly negative exponent") do
            value = ChaosTools.lyapunov(logistic_system(2.0), 500; Ttr = 100)
            observed(isfinite(value) && value < 0.0, value)
        end,
        run_case("neutral logistic boundary", "r=1 approaches a near-zero exponent") do
            value = ChaosTools.lyapunov(logistic_system(1.0), 1_000; Ttr = 200)
            observed(isfinite(value) && abs(value) < 0.02, value)
        end,
        run_case("long exponent estimate", "10,000 iterates remain finite and positive") do
            value = ChaosTools.lyapunov(logistic_system(4.0), 10_000; Ttr = 500)
            observed(isfinite(value) && value > 0.5, value)
        end,
        run_case("DynamicalSystems tangent edge", "ChaosTools consumes the live DynamicalSystems object") do
            ds = logistic_system(4.0)
            points, times = DynamicalSystems.trajectory(ds, 20)
            value = ChaosTools.lyapunov(ds, 500; Ttr = 100)
            observed(length(points) == length(times) == 21 && value > 0.5, (samples = length(points), lyapunov = value))
        end,
    ))

    push!(rows, package_row(
        "CliffordAlgebras",
        "library",
        ["CliffordAlgebras.CliffordAlgebra", "CliffordAlgebras.dimension"],
        "demote if Cl(n,0) generators fail their square/anticommutation relations or disagree with the Grassmann carrier",
        run_case("Cl(3,0) anticommutation", "e1^2=1 and e1e2+e2e1=0") do
            algebra, generators = clifford_generators(3)
            e1, e2 = generators[1], generators[2]
            observed(e1 * e1 == one(e1) && iszero(e1 * e2 + e2 * e1), (dimension = CliffordAlgebras.dimension(algebra), product = string(e1 * e2)))
        end,
        run_case("reversed-order control", "e1e2 differs from e2e1") do
            _, generators = clifford_generators(3)
            observed(generators[1] * generators[2] != generators[2] * generators[1], string(generators[1] * generators[2] - generators[2] * generators[1]))
        end,
        run_case("scalar identity boundary", "the scalar unit is multiplicatively neutral") do
            _, generators = clifford_generators(1)
            e1 = only(generators)
            observed(one(e1) * e1 == e1 && CliffordAlgebras.dimension(CliffordAlgebras.CliffordAlgebra(1, 0)) == 2, string(one(e1)))
        end,
        run_case("Cl(6,0) relation table", "all 36 generator pairs satisfy the Clifford relation") do
            _, generators = clifford_generators(6)
            unit = one(first(generators))
            failures = 0
            for i in eachindex(generators), j in eachindex(generators)
                lhs = generators[i] * generators[j] + generators[j] * generators[i]
                rhs = (i == j ? 2 : 0) * unit
                failures += lhs == rhs ? 0 : 1
            end
            observed(failures == 0, (pairs = 36, failures = failures))
        end,
        run_case("Grassmann relation edge", "both packages produce zero e1/e2 anticommutators") do
            _, generators = clifford_generators(3)
            basis = grassmann_basis(3)
            cliff_zero = iszero(generators[1] * generators[2] + generators[2] * generators[1])
            grass_zero = iszero(basis.v1 * basis.v2 + basis.v2 * basis.v1)
            observed(cliff_zero && grass_zero, (clifford_zero = cliff_zero, grassmann_zero = grass_zero))
        end,
    ))

    push!(rows, package_row(
        "DifferentialEquations",
        "engine",
        ["DifferentialEquations.ODEProblem", "DifferentialEquations.solve", "DifferentialEquations.EnsembleProblem"],
        "demote if decay/growth controls do not separate, zero-span behavior drifts, or the ensemble runner loses trajectories",
        run_case("exponential decay", "u(1) agrees with exp(-1)") do
            problem = DifferentialEquations.ODEProblem((u, p, t) -> -u, StaticArrays.SA[1.0], (0.0, 1.0))
            solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(); abstol = 1e-10, reltol = 1e-10)
            value = solution.u[end][1]
            observed(isapprox(value, exp(-1); atol = 1e-7), value)
        end,
        run_case("sign-flipped growth control", "du=+u grows instead of matching decay") do
            problem = DifferentialEquations.ODEProblem((u, p, t) -> u, StaticArrays.SA[1.0], (0.0, 1.0))
            solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5())
            value = solution.u[end][1]
            observed(value > 2.5 && !isapprox(value, exp(-1); atol = 1e-2), value)
        end,
        run_case("zero timespan boundary", "a zero-duration solve preserves the initial state") do
            problem = DifferentialEquations.ODEProblem((u, p, t) -> -u, StaticArrays.SA[1.0], (0.0, 0.0))
            solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5())
            observed(solution.u[end] == StaticArrays.SA[1.0], (saved = length(solution.u), final = collect(solution.u[end])))
        end,
        run_case("threaded ensemble", "32 trajectories complete") do
            problem = DifferentialEquations.ODEProblem((u, p, t) -> -u, [1.0], (0.0, 0.2))
            ensemble = DifferentialEquations.EnsembleProblem(problem)
            solution = DifferentialEquations.solve(ensemble, DifferentialEquations.Tsit5(), DifferentialEquations.EnsembleThreads(); trajectories = 32)
            observed(length(solution.u) == 32, (trajectories = length(solution.u), flattened_length = length(solution)))
        end,
        run_case("StaticArrays state edge", "the solver preserves a two-component SVector state and invariant sum") do
            problem = DifferentialEquations.ODEProblem((u, p, t) -> StaticArrays.SA[-u[1], u[1]], StaticArrays.SA[1.0, 0.0], (0.0, 1.0))
            solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(); abstol = 1e-10, reltol = 1e-10)
            final = solution.u[end]
            observed(final isa StaticArrays.SVector && isapprox(sum(final), 1.0; atol = 1e-8), collect(final))
        end,
    ))

    push!(rows, package_row(
        "DynamicalSystems",
        "engine",
        ["DynamicalSystems.DiscreteDynamicalSystem", "DynamicalSystems.trajectory"],
        "demote if discrete trajectories escape their declared map semantics, invalid lengths stop failing, or ChaosTools cannot consume the system",
        run_case("logistic trajectory", "r=4 trajectory has n+1 bounded samples") do
            points, times = DynamicalSystems.trajectory(logistic_system(4.0), 100)
            values = [point[1] for point in points]
            observed(length(points) == length(times) == 101 && all(x -> 0.0 <= x <= 1.0, values), (samples = length(points), extrema = [minimum(values), maximum(values)]))
        end,
        run_case("negative length control", "trajectory rejects a negative iteration count") do
            expected_error(BoundsError) do
                DynamicalSystems.trajectory(logistic_system(4.0), -1)
            end
        end,
        run_case("zero-length boundary", "zero steps returns only the initial state at time zero") do
            points, times = DynamicalSystems.trajectory(logistic_system(4.0), 0)
            observed(length(points) == 1 && only(times) == 0 && only(points)[1] == 0.2, (points = length(points), time = only(times)))
        end,
        run_case("long discrete trajectory", "100,001 samples remain finite and bounded") do
            points, _ = DynamicalSystems.trajectory(logistic_system(4.0), 100_000)
            values = [point[1] for point in points]
            observed(length(values) == 100_001 && all(isfinite, values) && all(x -> 0.0 <= x <= 1.0, values), (samples = length(values), final = last(values)))
        end,
        run_case("ChaosTools exponent edge", "the same discrete system produces a positive Lyapunov exponent") do
            ds = logistic_system(4.0)
            exponent = ChaosTools.lyapunov(ds, 1_000; Ttr = 200)
            observed(exponent > 0.5, exponent)
        end,
    ))

    push!(rows, package_row(
        "Graphs",
        "library",
        ["Graphs.SimpleGraph", "Graphs.add_edge!", "Graphs.dijkstra_shortest_paths"],
        "demote if graph invariants, empty-graph boundaries, scale behavior, or graph-derived solver constraints fail",
        run_case("cycle graph invariants", "a five-cycle has five vertices, five edges, and one component") do
            graph = Graphs.cycle_graph(5)
            observed(Graphs.nv(graph) == 5 && Graphs.ne(graph) == 5 && length(Graphs.connected_components(graph)) == 1, (vertices = Graphs.nv(graph), edges = Graphs.ne(graph)))
        end,
        run_case("disconnected control", "removing a bridge makes two connected components") do
            graph = Graphs.SimpleGraph(4)
            Graphs.add_edge!(graph, 1, 2)
            Graphs.add_edge!(graph, 3, 4)
            observed(length(Graphs.connected_components(graph)) == 2 && !Graphs.has_path(graph, 1, 4), Graphs.connected_components(graph))
        end,
        run_case("empty graph boundary", "a zero-vertex graph has no vertices or edges") do
            graph = Graphs.SimpleGraph(0)
            observed(Graphs.nv(graph) == 0 && Graphs.ne(graph) == 0, (vertices = Graphs.nv(graph), edges = Graphs.ne(graph)))
        end,
        run_case("large path graph", "a 5,000-node path remains connected with distance 4,999") do
            graph = Graphs.path_graph(5_000)
            state = Graphs.dijkstra_shortest_paths(graph, 1)
            observed(Graphs.ne(graph) == 4_999 && state.dists[end] == 4_999, (edges = Graphs.ne(graph), terminal_distance = state.dists[end]))
        end,
        run_case("Z3 coloring edge", "the graph-derived triangle is 3-colorable but not 2-colorable") do
            graph = Graphs.complete_graph(3)
            sat3 = z3_graph_coloring(graph, 3)
            sat2 = z3_graph_coloring(graph, 2)
            observed(sat3 == "sat" && sat2 == "unsat", (three_colors = sat3, two_colors = sat2))
        end,
    ))

    push!(rows, package_row(
        "Grassmann",
        "library",
        ["Grassmann.Λ", "Grassmann.wedge"],
        "demote if Euclidean basis products lose square/wedge/anticommutation laws or disagree with CliffordAlgebras",
        run_case("geometric bivector", "v1*v2 is nonzero and anticommutes") do
            basis = grassmann_basis(3)
            product = basis.v1 * basis.v2
            observed(!iszero(product) && basis.v2 * basis.v1 == -product, string(product))
        end,
        run_case("self-wedge control", "v1 wedge v1 is zero while v1*v1 is the scalar unit") do
            basis = grassmann_basis(3)
            wedge = Grassmann.wedge(basis.v1, basis.v1)
            observed(iszero(wedge) && !iszero(basis.v1 * basis.v1), (wedge = string(wedge), geometric = string(basis.v1 * basis.v1)))
        end,
        run_case("one-dimensional boundary", "the sole Euclidean generator squares to one") do
            basis = grassmann_basis(1)
            observed(string(basis.v1 * basis.v1) == "1v", string(basis.v1 * basis.v1))
        end,
        run_case("six-generator anticommutation", "all 15 distinct generator pairs anticommute") do
            basis = grassmann_basis(6)
            generators = [getproperty(basis, Symbol("v$(i)")) for i in 1:6]
            failures = sum(!iszero(generators[i] * generators[j] + generators[j] * generators[i]) for i in 1:6 for j in (i + 1):6)
            observed(failures == 0, (pairs = 15, failures = failures))
        end,
        run_case("CliffordAlgebras relation edge", "both packages agree that distinct Euclidean generators anticommute") do
            basis = grassmann_basis(3)
            _, generators = clifford_generators(3)
            grass = iszero(basis.v1 * basis.v2 + basis.v2 * basis.v1)
            cliff = iszero(generators[1] * generators[2] + generators[2] * generators[1])
            observed(grass && cliff, (grassmann = grass, clifford = cliff))
        end,
    ))

    push!(rows, package_row(
        "ITensorMPS",
        "library",
        ["ITensorMPS.MPS", "ITensorMPS.apply", "ITensorMPS.expect", "ITensorMPS.inner"],
        "demote if MPS norms/expectations fail, the X control does not flip Z, or ITensors operators cannot drive the MPS",
        run_case("Hadamard product-state MPS", "H on site 1 yields Z≈0 while untouched sites remain +1") do
            sites = ITensors.siteinds("Qubit", 4)
            psi = ITensorMPS.MPS(sites, "0")
            psi = ITensorMPS.apply(ITensors.op("H", sites, 1), psi)
            z = real.(ITensorMPS.expect(psi, "Z"))
            norm = real(ITensorMPS.inner(psi, psi))
            observed(abs(z[1]) < 1e-12 && all(x -> isapprox(x, 1.0; atol = 1e-12), z[2:end]) && isapprox(norm, 1.0; atol = 1e-12), (z = z, norm = norm))
        end,
        run_case("X-flip control", "X on |0> flips Z from +1 to -1") do
            sites = ITensors.siteinds("Qubit", 2)
            psi = ITensorMPS.MPS(sites, "0")
            flipped = ITensorMPS.apply(ITensors.op("X", sites, 1), psi)
            z = real.(ITensorMPS.expect(flipped, "Z"))
            observed(isapprox(z[1], -1.0; atol = 1e-12) && isapprox(z[2], 1.0; atol = 1e-12), z)
        end,
        run_case("single-site boundary", "a one-site |0> MPS has norm and Z expectation one") do
            sites = ITensors.siteinds("Qubit", 1)
            psi = ITensorMPS.MPS(sites, "0")
            z = only(real.(ITensorMPS.expect(psi, "Z")))
            observed(isapprox(real(ITensorMPS.inner(psi, psi)), 1.0; atol = 1e-12) && isapprox(z, 1.0; atol = 1e-12), z)
        end,
        run_case("24-site local-gate chain", "24 Hadamards preserve unit norm and yield 24 near-zero Z values") do
            sites = ITensors.siteinds("Qubit", 24)
            psi = ITensorMPS.MPS(sites, "0")
            for site in 1:24
                psi = ITensorMPS.apply(ITensors.op("H", sites, site), psi)
            end
            z = real.(ITensorMPS.expect(psi, "Z"))
            norm = real(ITensorMPS.inner(psi, psi))
            observed(length(z) == 24 && maximum(abs.(z)) < 1e-12 && isapprox(norm, 1.0; atol = 1e-10), (max_abs_z = maximum(abs.(z)), norm = norm))
        end,
        run_case("ITensors operator edge", "an ITensors op is accepted by ITensorMPS.apply and changes a package expectation") do
            sites = ITensors.siteinds("Qubit", 2)
            psi = ITensorMPS.MPS(sites, "0")
            before = first(real.(ITensorMPS.expect(psi, "Z")))
            after_psi = ITensorMPS.apply(ITensors.op("X", sites, 1), psi)
            after = first(real.(ITensorMPS.expect(after_psi, "Z")))
            observed(isapprox(before, 1.0; atol = 1e-12) && isapprox(after, -1.0; atol = 1e-12), (before = before, after = after))
        end,
    ))

    push!(rows, package_row(
        "ITensors",
        "library",
        ["ITensors.Index", "ITensors.ITensor", "ITensors.dag", "ITensors.scalar", "ITensors.op"],
        "demote if contraction orthogonality/norm controls fail, rank scaling breaks, or the MPS layer cannot consume ITensors objects",
        run_case("basis tensor norm", "a basis tensor contracts with itself to one") do
            _, left, _ = tensor_basis_pair()
            value = real(ITensors.scalar(ITensors.dag(left) * left))
            observed(value == 1.0, value)
        end,
        run_case("orthogonal contraction control", "orthogonal basis tensors contract to zero") do
            _, left, right = tensor_basis_pair()
            value = real(ITensors.scalar(ITensors.dag(left) * right))
            observed(value == 0.0, value)
        end,
        run_case("dimension-one boundary", "a dimension-one index contracts exactly") do
            index = ITensors.Index(1, "deep-stress-unit")
            tensor = ITensors.ITensor(index)
            tensor[index => 1] = 2.0
            value = real(ITensors.scalar(ITensors.dag(tensor) * tensor))
            observed(value == 4.0, value)
        end,
        run_case("rank-12 product tensor", "a deterministic rank-12 product contracts to unit norm") do
            indices = [ITensors.Index(2, "deep-stress-$(i)") for i in 1:12]
            tensors = Any[]
            for index in indices
                tensor = ITensors.ITensor(index)
                tensor[index => 1] = 1.0
                tensor[index => 2] = 0.0
                push!(tensors, tensor)
            end
            product = reduce(*, tensors)
            value = real(ITensors.scalar(ITensors.dag(product) * product))
            observed(value == 1.0 && length(ITensors.inds(product)) == 12, (norm = value, rank = length(ITensors.inds(product))))
        end,
        run_case("ITensorMPS state edge", "ITensors sites and operators produce a normalized MPS through ITensorMPS") do
            sites = ITensors.siteinds("Qubit", 3)
            psi = ITensorMPS.MPS(sites, "0")
            psi = ITensorMPS.apply(ITensors.op("H", sites, 2), psi)
            observed(isapprox(real(ITensorMPS.inner(psi, psi)), 1.0; atol = 1e-12), real.(ITensorMPS.expect(psi, "Z")))
        end,
    ))

    push!(rows, package_row(
        "JSON",
        "serialization_library",
        ["JSON.json", "JSON.parse"],
        "demote if typed round trips, malformed-input rejection, empty boundaries, scale behavior, or JSON3 interchange fails",
        run_case("typed object round trip", "nested booleans, integers, strings, and arrays survive") do
            value = Dict("name" => "ratchet", "ok" => true, "n" => 3, "items" => Any[1, "two"])
            decoded = JSON.parse(JSON.json(value))
            observed(decoded["name"] == "ratchet" && decoded["ok"] == true && decoded["n"] == 3 && decoded["items"][2] == "two", decoded)
        end,
        run_case("malformed JSON control", "a truncated object raises a parser error") do
            expected_error(Exception) do
                JSON.parse("{\"broken\":")
            end
        end,
        run_case("empty object boundary", "an empty object round trips with no keys") do
            decoded = JSON.parse(JSON.json(Dict{String,Any}()))
            observed(isempty(decoded), decoded)
        end,
        run_case("2,000-record round trip", "record count and terminal id survive") do
            value = [Dict("id" => i, "parity" => isodd(i)) for i in 1:2_000]
            decoded = JSON.parse(JSON.json(value))
            observed(length(decoded) == 2_000 && decoded[end]["id"] == 2_000, (count = length(decoded), terminal = decoded[end]["id"]))
        end,
        run_case("JSON3 interchange edge", "JSON output is read by JSON3 with the same fields") do
            encoded = JSON.json(Dict("edge" => "JSON->JSON3", "value" => 137))
            decoded = JSON3.read(encoded)
            observed(decoded.edge == "JSON->JSON3" && decoded.value == 137, (edge = String(decoded.edge), value = Int(decoded.value)))
        end,
    ))

    push!(rows, package_row(
        "JSON3",
        "serialization_library",
        ["JSON3.write", "JSON3.read", "JSON3.pretty"],
        "demote if structured round trips, malformed-input rejection, null boundary, scale behavior, or JSON interchange fails",
        run_case("named-tuple round trip", "ordered named fields and nested arrays survive") do
            value = (schema = "deep_stack_v1", pass = true, values = [1, 2, 3])
            decoded = JSON3.read(JSON3.write(value))
            observed(decoded.schema == "deep_stack_v1" && decoded.pass == true && collect(decoded.values) == [1, 2, 3], (schema = String(decoded.schema), values = Int.(decoded.values)))
        end,
        run_case("malformed JSON3 control", "a truncated array raises a parser error") do
            expected_error(Exception) do
                JSON3.read("[1, 2")
            end
        end,
        run_case("null boundary", "JSON null decodes to nothing") do
            value = JSON3.read("null")
            observed(value === nothing, string(value))
        end,
        run_case("2,000-record round trip", "record count and terminal id survive") do
            value = [(id = i, even = iseven(i)) for i in 1:2_000]
            decoded = JSON3.read(JSON3.write(value))
            observed(length(decoded) == 2_000 && decoded[end].id == 2_000, (count = length(decoded), terminal = Int(decoded[end].id)))
        end,
        run_case("JSON interchange edge", "JSON3 output is read by JSON with the same fields") do
            encoded = JSON3.write((edge = "JSON3->JSON", value = 160))
            decoded = JSON.parse(encoded)
            observed(decoded["edge"] == "JSON3->JSON" && decoded["value"] == 160, decoded)
        end,
    ))

    push!(rows, package_row(
        "Manifolds",
        "library",
        ["Manifolds.Sphere", "Manifolds.distance", "Manifolds.log", "Manifolds.exp", "Manifolds.is_point"],
        "demote if sphere membership, geodesic round trips, invalid-point controls, or StaticArrays interoperability fails",
        run_case("orthogonal sphere distance", "orthogonal S2 points are pi/2 apart") do
            manifold = Manifolds.Sphere(2)
            p = StaticArrays.SA[1.0, 0.0, 0.0]
            q = StaticArrays.SA[0.0, 1.0, 0.0]
            value = Manifolds.distance(manifold, p, q)
            observed(isapprox(value, pi / 2; atol = 1e-12), value)
        end,
        run_case("off-manifold control", "a norm-two point is rejected") do
            manifold = Manifolds.Sphere(2)
            invalid = StaticArrays.SA[2.0, 0.0, 0.0]
            observed(!Manifolds.is_point(manifold, invalid), collect(invalid))
        end,
        run_case("coincident-point boundary", "distance(p,p) is zero") do
            manifold = Manifolds.Sphere(2)
            p = StaticArrays.SA[1.0, 0.0, 0.0]
            value = Manifolds.distance(manifold, p, p)
            observed(value == 0.0, value)
        end,
        run_case("128 log-exp round trips", "bounded great-circle samples reconstruct with small error") do
            manifold = Manifolds.Sphere(2)
            p = StaticArrays.SA[1.0, 0.0, 0.0]
            errors = Float64[]
            for theta in range(0.0, pi / 2; length = 128)
                q = StaticArrays.SA[cos(theta), sin(theta), 0.0]
                tangent = Manifolds.log(manifold, p, q)
                reconstructed = Manifolds.exp(manifold, p, tangent)
                push!(errors, Manifolds.distance(manifold, q, reconstructed))
            end
            observed(maximum(errors) < 1e-10, (samples = length(errors), max_error = maximum(errors)))
        end,
        run_case("StaticArrays point edge", "SVector inputs are accepted and reconstruct through log/exp") do
            manifold = Manifolds.Sphere(2)
            p = StaticArrays.SA[1.0, 0.0, 0.0]
            q = StaticArrays.SA[0.0, 1.0, 0.0]
            reconstructed = Manifolds.exp(manifold, p, Manifolds.log(manifold, p, q))
            observed(Manifolds.distance(manifold, q, reconstructed) < 1e-12, (input_type = string(typeof(q)), output_type = string(typeof(reconstructed)), reconstructed = collect(reconstructed)))
        end,
    ))

    push!(rows, package_row(
        "Octonions",
        "library",
        ["Octonions.Octonion", "Base.:*"],
        "demote if the package loses its nonassociative witness, unit/basis norms, multiplication table, or quaternion embedding control",
        run_case("nonzero associator", "(e1e2)e4 - e1(e2e4) has norm two") do
            e1, e2, e4 = obasis(1), obasis(2), obasis(4)
            coeffs = oct_coeffs((e1 * e2) * e4 - e1 * (e2 * e4))
            observed(isapprox(LinearAlgebra.norm(coeffs), 2.0; atol = 1e-12), coeffs)
        end,
        run_case("quaternionic-subalgebra control", "the e1,e2,e3 associator vanishes") do
            e1, e2, e3 = obasis(1), obasis(2), obasis(3)
            coeffs = oct_coeffs((e1 * e2) * e3 - e1 * (e2 * e3))
            observed(iszero(LinearAlgebra.norm(coeffs)), coeffs)
        end,
        run_case("unit boundary", "e0 is a two-sided identity") do
            unit, e7 = obasis(0), obasis(7)
            observed(unit * e7 == e7 && e7 * unit == e7, oct_coeffs(unit * e7))
        end,
        run_case("full basis table", "all 64 basis products remain signed unit basis elements") do
            bad = 0
            for i in 0:7, j in 0:7
                coeffs = oct_coeffs(obasis(i) * obasis(j))
                bad += isapprox(LinearAlgebra.norm(coeffs), 1.0; atol = 1e-12) ? 0 : 1
            end
            observed(bad == 0, (products = 64, bad = bad))
        end,
        run_case("Quaternions associativity edge", "the octonion witness is nonzero while the quaternion associator is zero") do
            oct = oct_coeffs((obasis(1) * obasis(2)) * obasis(4) - obasis(1) * (obasis(2) * obasis(4)))
            quat = quat_coeffs((qbasis(1) * qbasis(2)) * qbasis(3) - qbasis(1) * (qbasis(2) * qbasis(3)))
            observed(LinearAlgebra.norm(oct) > 0.0 && LinearAlgebra.norm(quat) == 0.0, (octonion_norm = LinearAlgebra.norm(oct), quaternion_norm = LinearAlgebra.norm(quat)))
        end,
    ))

    push!(rows, package_row(
        "QuantumClifford",
        "engine",
        ["QuantumClifford.ghz", "QuantumClifford.stabilizerview", "QuantumClifford.stab_to_gf2"],
        "demote if GHZ stabilizers lose their GF(2) structure, product controls are indistinguishable, or graph extraction fails",
        run_case("three-qubit GHZ stabilizer", "GF(2) view is 3x6 with an all-X generator") do
            gf2 = QuantumClifford.stab_to_gf2(QuantumClifford.stabilizerview(QuantumClifford.ghz(3)))
            observed(size(gf2) == (3, 6) && all(gf2[1, 1:3]), (shape = collect(size(gf2)), true_count = sum(gf2)))
        end,
        run_case("product-state control", "the canonical product stabilizer has no X support") do
            state = one(QuantumClifford.Stabilizer, 3)
            gf2 = QuantumClifford.stab_to_gf2(QuantumClifford.stabilizerview(state))
            observed(!any(gf2[:, 1:3]) && sum(gf2[:, 4:6]) == 3, (x_true = sum(gf2[:, 1:3]), z_true = sum(gf2[:, 4:6])))
        end,
        run_case("Bell boundary", "the two-qubit GHZ/Bell state has a 2x4 stabilizer view") do
            gf2 = QuantumClifford.stab_to_gf2(QuantumClifford.stabilizerview(QuantumClifford.bell()))
            observed(size(gf2) == (2, 4), collect(size(gf2)))
        end,
        run_case("64-qubit GHZ tableau", "the stabilizer conversion scales to 64 generators") do
            gf2 = QuantumClifford.stab_to_gf2(QuantumClifford.stabilizerview(QuantumClifford.ghz(64)))
            observed(size(gf2) == (64, 128) && all(gf2[1, 1:64]), (shape = collect(size(gf2)), true_count = sum(gf2)))
        end,
        run_case("Graphs stabilizer edge", "Z-pair GHZ generators induce a connected three-node graph") do
            n = 3
            gf2 = QuantumClifford.stab_to_gf2(QuantumClifford.stabilizerview(QuantumClifford.ghz(n)))
            graph = Graphs.SimpleGraph(n)
            for row in 1:size(gf2, 1)
                support = findall(identity, gf2[row, (n + 1):(2n)])
                length(support) == 2 && Graphs.add_edge!(graph, support[1], support[2])
            end
            observed(Graphs.is_connected(graph) && Graphs.ne(graph) == 2, (edges = Graphs.ne(graph), components = length(Graphs.connected_components(graph))))
        end,
    ))

    push!(rows, package_row(
        "QuantumOptics",
        "engine",
        ["QuantumOptics.SpinBasis", "QuantumOptics.dm", "QuantumOptics.entropy_vn", "QuantumOptics.tensor", "QuantumOptics.sigmax"],
        "demote if state entropy/trace controls fail, tensor scaling breaks, or the Pauli carrier disagrees with QuantumToolbox",
        run_case("pure spin superposition", "a normalized pure-state density operator has entropy zero") do
            basis = QuantumOptics.SpinBasis(1 // 2)
            psi = (QuantumOptics.spinup(basis) + QuantumOptics.spindown(basis)) / sqrt(2)
            rho = QuantumOptics.dm(psi)
            entropy = real(QuantumOptics.entropy_vn(rho))
            observed(abs(entropy) < 1e-12 && isapprox(real(LinearAlgebra.tr(rho.data)), 1.0; atol = 1e-12), (entropy = entropy, trace = real(LinearAlgebra.tr(rho.data))))
        end,
        run_case("maximally mixed control", "I/2 has entropy log(2), unlike the pure state") do
            basis = QuantumOptics.SpinBasis(1 // 2)
            mixed = QuantumOptics.Operator(basis, basis, Matrix{ComplexF64}(LinearAlgebra.I, 2, 2) / 2)
            entropy = real(QuantumOptics.entropy_vn(mixed))
            observed(isapprox(entropy, log(2); atol = 1e-12), entropy)
        end,
        run_case("spin-basis boundary", "the spin-1/2 basis is two dimensional and sigma-X is 2x2") do
            basis = QuantumOptics.SpinBasis(1 // 2)
            sigma = QuantumOptics.sigmax(basis)
            observed(length(basis) == 2 && size(sigma.data) == (2, 2), (basis_dim = length(basis), operator_shape = collect(size(sigma.data))))
        end,
        run_case("eight-spin tensor state", "an eight-spin product density operator remains normalized and pure") do
            basis = QuantumOptics.SpinBasis(1 // 2)
            states = [QuantumOptics.spinup(basis) for _ in 1:8]
            psi = reduce(QuantumOptics.tensor, states)
            rho = QuantumOptics.dm(psi)
            entropy = real(QuantumOptics.entropy_vn(rho))
            observed(length(psi.data) == 256 && isapprox(real(LinearAlgebra.tr(rho.data)), 1.0; atol = 1e-12) && abs(entropy) < 1e-10, (dimension = length(psi.data), entropy = entropy))
        end,
        run_case("QuantumToolbox Pauli edge", "both quantum packages expose the same sigma-X matrix") do
            basis = QuantumOptics.SpinBasis(1 // 2)
            optics = Matrix(QuantumOptics.sigmax(basis).data)
            toolbox = Matrix(QuantumToolbox.sigmax().data)
            observed(isapprox(optics, toolbox; atol = 0.0), (optics = string(optics), toolbox = string(toolbox)))
        end,
    ))

    push!(rows, package_row(
        "QuantumToolbox",
        "engine",
        ["QuantumToolbox.destroy", "QuantumToolbox.fock", "QuantumToolbox.mesolve", "QuantumToolbox.sigmax"],
        "demote if dissipative and closed controls do not separate, vacuum behavior fails, scale integration breaks, or Pauli carriers disagree",
        run_case("damped oscillator", "collapse dynamics reduce the occupation from n=2") do
            a = QuantumToolbox.destroy(5)
            number = a' * a
            psi = QuantumToolbox.fock(5, 2)
            solution = QuantumToolbox.mesolve(number, psi, range(0.0, 2.0; length = 41), [sqrt(0.4) * a]; e_ops = [number], progress_bar = Val(false))
            values = real.(solution.expect[1, :])
            observed(first(values) > 1.9 && last(values) < first(values) - 0.5, (initial = first(values), final = last(values)))
        end,
        run_case("closed-system control", "without collapse operators the number expectation stays at two") do
            a = QuantumToolbox.destroy(5)
            number = a' * a
            psi = QuantumToolbox.fock(5, 2)
            solution = QuantumToolbox.mesolve(number, psi, range(0.0, 2.0; length = 21), []; e_ops = [number], progress_bar = Val(false))
            values = real.(solution.expect[1, :])
            observed(maximum(abs.(values .- 2.0)) < 1e-10, (minimum = minimum(values), maximum = maximum(values)))
        end,
        run_case("vacuum boundary", "the vacuum number expectation is zero") do
            a = QuantumToolbox.destroy(2)
            number = a' * a
            vacuum = QuantumToolbox.fock(2, 0)
            value = real(QuantumToolbox.expect(number, vacuum))
            observed(value == 0.0, value)
        end,
        run_case("ten-level dissipative solve", "101 time points remain finite and occupation decreases") do
            a = QuantumToolbox.destroy(10)
            number = a' * a
            psi = QuantumToolbox.fock(10, 7)
            solution = QuantumToolbox.mesolve(number, psi, range(0.0, 3.0; length = 101), [sqrt(0.2) * a]; e_ops = [number], progress_bar = Val(false))
            values = real.(solution.expect[1, :])
            observed(length(values) == 101 && all(isfinite, values) && last(values) < first(values), (count = length(values), initial = first(values), final = last(values)))
        end,
        run_case("QuantumOptics Pauli edge", "both quantum packages expose the same sigma-X matrix") do
            basis = QuantumOptics.SpinBasis(1 // 2)
            toolbox = Matrix(QuantumToolbox.sigmax().data)
            optics = Matrix(QuantumOptics.sigmax(basis).data)
            observed(isapprox(toolbox, optics; atol = 0.0), (toolbox = string(toolbox), optics = string(optics)))
        end,
    ))

    push!(rows, package_row(
        "Quaternions",
        "library",
        ["Quaternions.Quaternion", "Base.:*"],
        "demote if quaternion noncommutation, associativity, identity, basis-table norms, or the octonion comparison fails",
        run_case("quaternion order gap", "ij=-ji with norm-two difference") do
            i, j = qbasis(1), qbasis(2)
            gap = quat_coeffs(i * j - j * i)
            observed(isapprox(LinearAlgebra.norm(gap), 2.0; atol = 1e-12), gap)
        end,
        run_case("associativity control", "(ij)k-i(jk) is zero") do
            i, j, k = qbasis(1), qbasis(2), qbasis(3)
            assoc = quat_coeffs((i * j) * k - i * (j * k))
            observed(LinearAlgebra.norm(assoc) == 0.0, assoc)
        end,
        run_case("unit boundary", "q0 is a two-sided identity") do
            unit, k = qbasis(0), qbasis(3)
            observed(unit * k == k && k * unit == k, quat_coeffs(unit * k))
        end,
        run_case("full basis table", "all 16 basis products remain signed unit basis elements") do
            bad = 0
            for i in 0:3, j in 0:3
                coeffs = quat_coeffs(qbasis(i) * qbasis(j))
                bad += isapprox(LinearAlgebra.norm(coeffs), 1.0; atol = 1e-12) ? 0 : 1
            end
            observed(bad == 0, (products = 16, bad = bad))
        end,
        run_case("Octonions associator edge", "quaternion associativity contrasts with a nonzero octonion witness") do
            quat = quat_coeffs((qbasis(1) * qbasis(2)) * qbasis(3) - qbasis(1) * (qbasis(2) * qbasis(3)))
            oct = oct_coeffs((obasis(1) * obasis(2)) * obasis(4) - obasis(1) * (obasis(2) * obasis(4)))
            observed(LinearAlgebra.norm(quat) == 0.0 && LinearAlgebra.norm(oct) > 0.0, (quaternion_norm = LinearAlgebra.norm(quat), octonion_norm = LinearAlgebra.norm(oct)))
        end,
    ))

    push!(rows, package_row(
        "StaticArrays",
        "library",
        ["StaticArrays.SVector", "StaticArrays.SMatrix"],
        "demote if fixed-size arithmetic, dimension errors, singleton boundaries, repeated multiplication, or solver interoperability fails",
        run_case("fixed-size matrix-vector product", "a 2x2 SMatrix maps [1,2] to [5,11]") do
            matrix = StaticArrays.SMatrix{2,2}(1.0, 3.0, 2.0, 4.0)
            vector = StaticArrays.SA[1.0, 2.0]
            value = matrix * vector
            observed(value == StaticArrays.SA[5.0, 11.0], collect(value))
        end,
        run_case("dimension mismatch control", "adding unequal SVector dimensions raises DimensionMismatch") do
            expected_error(DimensionMismatch) do
                StaticArrays.SA[1.0, 2.0] + StaticArrays.SA[1.0, 2.0, 3.0]
            end
        end,
        run_case("singleton boundary", "a one-element SVector preserves value and norm") do
            vector = StaticArrays.SA[3.0]
            observed(length(vector) == 1 && LinearAlgebra.norm(vector) == 3.0, collect(vector))
        end,
        run_case("100,000 fixed-size updates", "repeated bounded rotations remain finite") do
            rotation = StaticArrays.SMatrix{2,2}(cos(0.001), sin(0.001), -sin(0.001), cos(0.001))
            vector = StaticArrays.SA[1.0, 0.0]
            for _ in 1:100_000
                vector = rotation * vector
            end
            observed(all(isfinite, vector) && isapprox(LinearAlgebra.norm(vector), 1.0; atol = 1e-10), (vector = collect(vector), norm = LinearAlgebra.norm(vector)))
        end,
        run_case("DifferentialEquations state edge", "an SVector survives a solver round trip with the invariant sum") do
            problem = DifferentialEquations.ODEProblem((u, p, t) -> StaticArrays.SA[-u[1], u[1]], StaticArrays.SA[1.0, 0.0], (0.0, 1.0))
            solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(); abstol = 1e-10, reltol = 1e-10)
            final = solution.u[end]
            observed(final isa StaticArrays.SVector && isapprox(sum(final), 1.0; atol = 1e-8), collect(final))
        end,
    ))

    push!(rows, package_row(
        "Symbolics",
        "engine",
        ["Symbolics.variable", "Symbolics.expand", "Symbolics.derivative", "Symbolics.simplify", "Symbolics.substitute", "Symbolics.build_function"],
        "demote if symbolic differentiation/substitution controls, zero boundaries, polynomial scale, or graph-derived expressions fail",
        run_case("compiled polynomial derivative", "d(x+1)^5/dx at x=2 equals 405") do
            x = Symbolics.variable(:deep_x)
            derivative = Symbolics.simplify(Symbolics.derivative(Symbolics.expand((x + 1)^5), x))
            function_value = Symbolics.build_function(derivative, x; expression = Val(false))(2.0)
            observed(isapprox(function_value, 405.0; atol = 1e-12), (derivative = string(derivative), value = function_value))
        end,
        run_case("wrong-derivative control", "the degree-four impostor differs from the real derivative at x=2") do
            x = Symbolics.variable(:deep_x_negative)
            expression = (x + 1)^5
            actual = Symbolics.derivative(expression, x)
            impostor = 4 * (x + 1)^3
            actual_value = Symbolics.value(Symbolics.substitute(actual, Dict(x => 2); fold = Val(true)))
            impostor_value = Symbolics.value(Symbolics.substitute(impostor, Dict(x => 2); fold = Val(true)))
            observed(actual_value != impostor_value, (actual = actual_value, impostor = impostor_value))
        end,
        run_case("zero-expression boundary", "simplify(x-x) is zero") do
            x = Symbolics.variable(:deep_x_boundary)
            value = Symbolics.simplify(x - x)
            observed(Symbolics.value(value) == 0, string(value))
        end,
        run_case("degree-15 expansion", "the derivative at x=1 equals 15*2^14") do
            x = Symbolics.variable(:deep_x_stress)
            expanded = Symbolics.expand((x + 1)^15)
            derivative = Symbolics.derivative(expanded, x)
            value = Symbolics.value(Symbolics.substitute(derivative, Dict(x => 1); fold = Val(true)))
            observed(value == 15 * 2^14, (value = value, expected = 15 * 2^14, expression_length = length(string(expanded))))
        end,
        run_case("Graphs degree-polynomial edge", "graph degrees become coefficients in a symbolic polynomial") do
            graph = Graphs.path_graph(5)
            degrees = Graphs.degree(graph)
            x = Symbolics.variable(:deep_graph_x)
            expression = sum(degrees[i] * x^(i - 1) for i in eachindex(degrees))
            symbolic_value = Symbolics.value(Symbolics.substitute(expression, Dict(x => 2); fold = Val(true)))
            direct_value = sum(degrees[i] * 2^(i - 1) for i in eachindex(degrees))
            observed(symbolic_value == direct_value, (degrees = degrees, symbolic = symbolic_value, direct = direct_value))
        end,
    ))

    push!(rows, package_row(
        "Yao",
        "engine",
        ["Yao.zero_state", "Yao.chain", "Yao.put", "Yao.control", "Yao.apply!", "Yao.state", "Yao.mat"],
        "demote if Bell preparation, identity controls, one-qubit boundaries, state-vector scaling, or Pauli interoperability fails",
        run_case("Bell circuit", "H+CNOT prepares equal |00> and |11> amplitudes") do
            register = Yao.zero_state(2)
            circuit = Yao.chain(2, Yao.put(1 => Yao.H), Yao.control(1, 2 => Yao.X))
            Yao.apply!(register, circuit)
            state = vec(Yao.state(register))
            expected_amp = inv(sqrt(2))
            pass = isapprox(abs(state[1]), expected_amp; atol = 1e-12) && isapprox(abs(state[4]), expected_amp; atol = 1e-12) && abs(state[2]) < 1e-12 && abs(state[3]) < 1e-12
            observed(pass, string(state))
        end,
        run_case("identity-state control", "without the circuit, |11> amplitude is zero") do
            state = vec(Yao.state(Yao.zero_state(2)))
            observed(isapprox(abs(state[1]), 1.0; atol = 1e-12) && abs(state[4]) == 0.0, string(state))
        end,
        run_case("single-qubit X boundary", "X maps |0> exactly to |1>") do
            register = Yao.zero_state(1)
            Yao.apply!(register, Yao.X)
            state = vec(Yao.state(register))
            observed(abs(state[1]) == 0.0 && isapprox(abs(state[2]), 1.0; atol = 1e-12), string(state))
        end,
        run_case("12-qubit Hadamard layer", "4,096 amplitudes remain normalized") do
            register = Yao.zero_state(12)
            circuit = Yao.chain(12, [Yao.put(i => Yao.H) for i in 1:12]...)
            Yao.apply!(register, circuit)
            state = vec(Yao.state(register))
            observed(length(state) == 4_096 && isapprox(sum(abs2, state), 1.0; atol = 1e-10), (amplitudes = length(state), norm2 = sum(abs2, state)))
        end,
        run_case("QuantumOptics Pauli edge", "Yao.X and QuantumOptics.sigmax have identical matrices") do
            basis = QuantumOptics.SpinBasis(1 // 2)
            yao = Matrix(Yao.mat(Yao.X))
            optics = Matrix(QuantumOptics.sigmax(basis).data)
            observed(isapprox(yao, optics; atol = 0.0), (yao = string(yao), optics = string(optics)))
        end,
    ))

    push!(rows, package_row(
        "Z3",
        "proof_solver",
        ["Z3.Context", "Z3.IntVar", "Z3.Solver", "Z3.add", "Z3.check"],
        "demote if SAT/UNSAT controls collapse, empty-solver semantics drift, bounded constraint scale fails, or graph coloring is not solver-derived",
        run_case("bounded SAT model", "1 < x < 3 is satisfiable over integers") do
            ctx = Z3.Context()
            x = Z3.IntVar("deep_sat_x", ctx)
            solver = Z3.Solver(ctx)
            Z3.add(solver, Z3.IntVal(1, ctx) < x)
            Z3.add(solver, x < Z3.IntVal(3, ctx))
            status = string(Z3.check(solver))
            observed(status == "sat", status)
        end,
        run_case("contradictory UNSAT control", "x>1 and x<0 is unsatisfiable") do
            ctx = Z3.Context()
            x = Z3.IntVar("deep_unsat_x", ctx)
            solver = Z3.Solver(ctx)
            Z3.add(solver, Z3.IntVal(1, ctx) < x)
            Z3.add(solver, x < Z3.IntVal(0, ctx))
            status = string(Z3.check(solver))
            observed(status == "unsat", status)
        end,
        run_case("empty solver boundary", "an unconstrained solver is satisfiable") do
            status = string(Z3.check(Z3.Solver(Z3.Context())))
            observed(status == "sat", status)
        end,
        run_case("100 fixed integer bindings", "a 100-variable exact assignment is satisfiable") do
            ctx = Z3.Context()
            solver = Z3.Solver(ctx)
            for i in 1:100
                x = Z3.IntVar("deep_stress_$(i)", ctx)
                Z3.add(solver, x == Z3.IntVal(i, ctx))
            end
            status = string(Z3.check(solver))
            observed(status == "sat", (variables = 100, status = status))
        end,
        run_case("Graphs coloring edge", "triangle edge constraints are SAT for 3 colors and UNSAT for 2") do
            graph = Graphs.complete_graph(3)
            sat3 = z3_graph_coloring(graph, 3)
            sat2 = z3_graph_coloring(graph, 2)
            observed(sat3 == "sat" && sat2 == "unsat", (three_colors = sat3, two_colors = sat2, graph_edges = Graphs.ne(graph)))
        end,
    ))

    rows
end

function support_row(
    package::String,
    module_value::Module,
    qualified_api::Vector{String},
    usage::String,
    demotion_condition::String,
    positive,
    negative,
    boundary,
    stress,
    adjacent,
)
    demotion = (
        passed = negative.pass && !isempty(demotion_condition),
        method = "executed negative/failure control bound to the declared demotion condition",
        condition = demotion_condition,
        qualified_api = join(qualified_api, "; "),
        observed = negative.observed,
        error = negative.error,
    )
    tool_calls = [(
        tool = package,
        qualified_api = join(qualified_api, "; "),
        probe_function = "support_rows/$(package)",
        executed = true,
        load_bearing = true,
        raw_probe_recorded = true,
        input_object = (
            positive = positive.expected,
            negative = negative.expected,
            boundary = boundary.expected,
            stress = stress.expected,
        ),
        output_object = (
            positive = positive.observed,
            negative = negative.observed,
            boundary = boundary.observed,
            stress = stress.observed,
        ),
        case_bindings = (
            positive = (passed = positive.pass, duration_ms = positive.duration_ms),
            negative = (passed = negative.pass, duration_ms = negative.duration_ms),
            boundary = (passed = boundary.pass, duration_ms = boundary.duration_ms),
            stress = (passed = stress.pass, duration_ms = stress.duration_ms),
        ),
        gates = ["positive", "negative", "boundary", "stress", "demotion", "adjacent_integration_edge"],
    )]
    operational_pass = positive.pass && negative.pass && boundary.pass && stress.pass && adjacent.pass && demotion.passed
    (
        package = package,
        role = "support",
        independent_engine = false,
        kind = "stdlib_support",
        qualified_api = qualified_api,
        version = string(something(Base.pkgversion(module_value), VERSION)),
        import_status = (
            pass = true,
            version = string(something(Base.pkgversion(module_value), VERSION)),
            module_path = something(Base.pathof(module_value), "builtin"),
            error = nothing,
            duration_ms = 0.0,
        ),
        usage = usage,
        positive = positive,
        negative = negative,
        boundary = boundary,
        stress = stress,
        adjacent_integration_edge = adjacent,
        demotion_condition = demotion_condition,
        demotion = demotion,
        tool_calls = tool_calls,
        operational_pass = operational_pass,
    )
end

function support_rows()
    dates_row = support_row(
        "Dates",
        Dates,
        ["Dates.Date", "Dates.DateTime", "Dates.Day", "Dates.datetime2unix", "Dates.unix2datetime"],
        "receipt time and temporal test fixtures; support only, never an independent engine or scientific claimant",
        "demote support if calendar arithmetic, invalid-date rejection, epoch boundaries, bounded date scaling, or JSON3 timestamp interchange fails",
        run_case("calendar arithmetic", "adding 1 hour and 26 minutes reaches 14:00 exactly") do
            start = Dates.DateTime(2026, 7, 14, 12, 34, 0)
            final = start + Dates.Hour(1) + Dates.Minute(26)
            observed(final == Dates.DateTime(2026, 7, 14, 14, 0, 0), string(final))
        end,
        run_case("invalid calendar control", "February 30 is rejected") do
            expected_error(ArgumentError) do
                Dates.Date(2026, 2, 30)
            end
        end,
        run_case("Unix epoch boundary", "DateTime(1970-01-01) maps exactly to Unix time zero and back") do
            epoch = Dates.DateTime(1970, 1, 1)
            unix = Dates.datetime2unix(epoch)
            roundtrip = Dates.unix2datetime(unix)
            observed(unix == 0.0 && roundtrip == epoch, (unix = unix, roundtrip = string(roundtrip)))
        end,
        run_case("10,000-day sequence", "a 10,000-element date sequence remains sorted with the exact endpoint delta") do
            origin = Dates.Date(2000, 1, 1)
            values = [origin + Dates.Day(i) for i in 0:9_999]
            observed(issorted(values) && length(values) == 10_000 && last(values) - first(values) == Dates.Day(9_999), (count = length(values), first = string(first(values)), last = string(last(values))))
        end,
        run_case("JSON3 timestamp edge", "an ISO DateTime string survives JSON3 serialization and reparsing") do
            timestamp = Dates.DateTime(2026, 7, 14, 21, 9, 53)
            encoded = JSON3.write((timestamp = string(timestamp),))
            decoded = JSON3.read(encoded)
            reparsed = Dates.DateTime(String(decoded.timestamp))
            observed(reparsed == timestamp, (encoded = encoded, reparsed = string(reparsed)))
        end,
    )

    linear_algebra_row = support_row(
        "LinearAlgebra",
        LinearAlgebra,
        ["LinearAlgebra.norm", "LinearAlgebra.cholesky", "LinearAlgebra.SymTridiagonal", "LinearAlgebra.eigvals"],
        "numeric invariants and controls for package probes; support only, never counted as an independent engine",
        "demote support if solve residuals, definiteness rejection, zero boundaries, spectral scale, or StaticArrays interoperability fails",
        run_case("dense linear solve", "a well-conditioned 2x2 solve recovers [2,3] with negligible residual") do
            matrix = [3.0 1.0; 1.0 2.0]
            rhs = [9.0, 8.0]
            solution = matrix \ rhs
            residual = LinearAlgebra.norm(matrix * solution - rhs)
            observed(isapprox(solution, [2.0, 3.0]; atol = 1e-12) && residual < 1e-12, (solution = solution, residual = residual))
        end,
        run_case("indefinite Cholesky control", "an indefinite symmetric matrix raises PosDefException") do
            expected_error(LinearAlgebra.PosDefException) do
                LinearAlgebra.cholesky(LinearAlgebra.Symmetric([1.0 2.0; 2.0 1.0]))
            end
        end,
        run_case("zero-vector boundary", "the norm of an empty vector is exactly zero") do
            vector = Float64[]
            observed(LinearAlgebra.norm(vector) == 0.0, (length = length(vector), norm = LinearAlgebra.norm(vector)))
        end,
        run_case("1,024-value tridiagonal spectrum", "the discrete Laplacian spectrum is finite and lies strictly between zero and four") do
            matrix = LinearAlgebra.SymTridiagonal(fill(2.0, 1_024), fill(-1.0, 1_023))
            values = LinearAlgebra.eigvals(matrix)
            observed(length(values) == 1_024 && all(isfinite, values) && minimum(values) > 0.0 && maximum(values) < 4.0, (count = length(values), minimum = minimum(values), maximum = maximum(values)))
        end,
        run_case("StaticArrays solve edge", "LinearAlgebra solves an SMatrix/SVector system with negligible residual") do
            matrix = StaticArrays.SMatrix{2,2}(3.0, 1.0, 1.0, 2.0)
            rhs = StaticArrays.SA[9.0, 8.0]
            solution = matrix \ rhs
            residual = LinearAlgebra.norm(matrix * solution - rhs)
            observed(solution isa StaticArrays.SVector && isapprox(solution, StaticArrays.SA[2.0, 3.0]; atol = 1e-12) && residual < 1e-12, (solution = collect(solution), residual = residual))
        end,
    )

    sha_row = support_row(
        "SHA",
        SHA,
        ["SHA.sha256", "Base.bytes2hex"],
        "source, Project.toml, Manifest.toml, and receipt identity; support only, never an independent engine",
        "demote support if known vectors, tamper separation, empty-input boundary, bounded large payloads, or JSON3 canonical payload hashing fails",
        run_case("SHA-256 known vector", "sha256(\"abc\") matches the published digest") do
            digest = bytes2hex(SHA.sha256(codeunits("abc")))
            expected_digest = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
            observed(digest == expected_digest, digest)
        end,
        run_case("tampered-input control", "a one-byte mutation changes the digest") do
            original = bytes2hex(SHA.sha256(codeunits("ratchet-payload")))
            tampered = bytes2hex(SHA.sha256(codeunits("ratchet-payloae")))
            observed(original != tampered, (original = original, tampered = tampered))
        end,
        run_case("empty-input boundary", "sha256(empty) matches the standard empty digest") do
            digest = bytes2hex(SHA.sha256(UInt8[]))
            expected_digest = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            observed(digest == expected_digest, digest)
        end,
        run_case("four-megabyte payload", "a deterministic 4 MiB payload hashes reproducibly to 32 bytes") do
            payload = fill(UInt8(0xa5), 4 * 1_024 * 1_024)
            first_digest = SHA.sha256(payload)
            second_digest = SHA.sha256(payload)
            observed(length(first_digest) == 32 && first_digest == second_digest, (payload_bytes = length(payload), digest = bytes2hex(first_digest)))
        end,
        run_case("JSON3 canonical payload edge", "decode/rebuild through JSON3 preserves the exact serialized digest") do
            payload = (id = 137, label = "deep-stack")
            encoded = JSON3.write(payload)
            decoded = JSON3.read(encoded)
            rebuilt = JSON3.write((id = Int(decoded.id), label = String(decoded.label)))
            first_digest = bytes2hex(SHA.sha256(codeunits(encoded)))
            second_digest = bytes2hex(SHA.sha256(codeunits(rebuilt)))
            observed(encoded == rebuilt && first_digest == second_digest, (encoded = encoded, digest = first_digest))
        end,
    )

    [dates_row, linear_algebra_row, sha_row]
end

function direct_roster(project_path::String)
    deps = collect(keys(TOML.parsefile(project_path)["deps"]))
    sort!(setdiff(deps, DIRECT_STDLIB_SUPPORT))
end

function main(args::Vector{String})
    destination = output_path(args)
    source_path = abspath(@__FILE__)
    project_path = Base.active_project()
    project_path === nothing && error("no active Julia project")
    manifest_path = joinpath(dirname(project_path), "Manifest.toml")
    isfile(manifest_path) || error("active project lacks Manifest.toml: $(manifest_path)")

    declared = direct_roster(project_path)
    expected = sort(copy(DIRECT_NON_STDLIB))
    roster_match = declared == expected
    rows = make_rows()
    supports = support_rows()
    row_names = sort([row.package for row in rows])
    row_roster_match = row_names == expected
    support_names = sort([row.package for row in supports])
    support_roster_match = support_names == sort(copy(DIRECT_STDLIB_SUPPORT))
    operational_rows = vcat(rows, supports)
    operational_pass_count = count(row -> row.operational_pass, operational_rows)
    operational_red_count = length(operational_rows) - operational_pass_count

    receipt = (
        schema = "codex_ratchet_julia_core_deep_stress_v1",
        created_at = string(Dates.now(Dates.UTC)) * "Z",
        classification = "integration_diagnostic",
        promotion_allowed = false,
        scientific_claim_proven = false,
        receipt_semantics = "operational package diagnostics only; red rows are preserved; no Ratchet/QIT or downstream science claim is promoted",
        active_project = project_path,
        julia_version = string(VERSION),
        load_path = copy(Base.LOAD_PATH),
        julia_load_path_env = get(ENV, "JULIA_LOAD_PATH", nothing),
        project_sha256 = sha256_file(project_path),
        manifest_sha256 = sha256_file(manifest_path),
        source_path = source_path,
        source_sha256 = sha256_file(source_path),
        roster = (
            declared_direct_nonstdlib = declared,
            expected_direct_nonstdlib = expected,
            declared_matches_expected = roster_match,
            row_names = row_names,
            rows_match_expected = row_roster_match,
            required_stdlib_support = sort(copy(DIRECT_STDLIB_SUPPORT)),
            support_row_names = support_names,
            support_rows_match_expected = support_roster_match,
        ),
        summary = (
            row_count = length(operational_rows),
            direct_nonstdlib_row_count = length(rows),
            support_row_count = length(supports),
            operational_pass_count = operational_pass_count,
            operational_red_count = operational_red_count,
            all_operational_pass = operational_red_count == 0,
            trustworthy_receipt_written_even_if_red = true,
        ),
        rows = rows,
        support_rows = supports,
    )

    mkpath(dirname(destination))
    open(destination, "w") do io
        JSON3.pretty(io, receipt)
        write(io, '\n')
    end

    # Independent read-back catches unsupported values or truncated output.
    decoded = JSON3.read(read(destination, String))
    valid =
        decoded.schema == "codex_ratchet_julia_core_deep_stress_v1" &&
        decoded.classification == "integration_diagnostic" &&
        decoded.promotion_allowed == false &&
        decoded.scientific_claim_proven == false &&
        length(decoded.rows) == length(DIRECT_NON_STDLIB) &&
        length(decoded.support_rows) == length(DIRECT_STDLIB_SUPPORT) &&
        decoded.summary.row_count == length(DIRECT_NON_STDLIB) + length(DIRECT_STDLIB_SUPPORT) &&
        decoded.roster.declared_matches_expected == true &&
        decoded.roster.rows_match_expected == true &&
        decoded.roster.support_rows_match_expected == true

    println("receipt=$(destination)")
    println("rows=$(length(operational_rows)) direct=$(length(rows)) support=$(length(supports)) operational_pass=$(operational_pass_count) operational_red=$(operational_red_count)")
    println("roster_match=$(roster_match && row_roster_match && support_roster_match) readback_valid=$(valid)")
    return valid ? 0 : 2
end

exit_code = try
    main(ARGS)
catch err
    println(stderr, "HARNESS FAILURE: ", error_text(err, catch_backtrace()))
    2
end
exit(exit_code)
