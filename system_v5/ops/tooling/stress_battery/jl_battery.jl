# Deep stress battery — Julia side. Julia 1.12: all package loads at TOP LEVEL (world-age rules).
using JSON
using QuantumOptics
using QuantumClifford
using CliffordAlgebras
using Octonions
using Quaternions
using DifferentialEquations
using ITensors, ITensorMPS
using Manifolds
using Symbolics
using Graphs

# canon module at top level
const CANON_OK = try
    include(ENV["CANON_PATH"]); true
catch e
    println("CANON LOAD FAIL: ", e); false
end

results = Dict{String,Any}()
macro probe(name, blk)
    quote
        local t0 = time()
        try
            local detail = $(esc(blk))
            results[$name] = Dict("status"=>"PASS", "sec"=>round(time()-t0, digits=2), "detail"=>detail)
            println("PASS ", $name, " (", round(time()-t0, digits=1), "s) ", detail)
        catch e
            results[$name] = Dict("status"=>"FAIL", "sec"=>round(time()-t0, digits=2),
                                  "error"=>first(sprint(showerror, e), 200))
            println("FAIL ", $name, ": ", first(sprint(showerror, e), 140))
        end
        flush(stdout)
    end
end

@probe "canon_module_octonion_associator" begin
    CANON_OK || error("canon module failed to load")
    M = ExceptionalAlgebraCanon
    assoc = Base.invokelatest(M.associator, Base.invokelatest(M.basis_octonion, 1),
                              Base.invokelatest(M.basis_octonion, 2), Base.invokelatest(M.basis_octonion, 4))
    expected = ntuple(i -> i == 8 ? 2.0 : 0.0, 8)
    assoc.c == expected || error("associator != 2e7: $(assoc.c)")
    "associator(e1,e2,e4) = 2e7 EXACT"
end

@probe "canon_albert_jordan_identity" begin
    CANON_OK || error("canon module failed to load")
    M = ExceptionalAlgebraCanon
    x = Base.invokelatest(M.primitive_idempotent, 1)
    r = Base.invokelatest(M.jordan_identity_residual, x, Base.invokelatest(M.primitive_idempotent, 2))
    # The canon returns an Albert element, not a scalar.  Gate every
    # coordinate explicitly so this remains a real identity check.
    err = max(maximum(abs, r.diag), maximum(M.norm2, r.off))
    err < 1e-10 || error("Jordan identity residual norm $err")
    "Albert algebra Jordan identity residual norm < 1e-10 on idempotents"
end

@probe "quantumoptics_lindblad_trace" begin
    b = SpinBasis(1//2)
    H = sigmaz(b); psi0 = normalize(spinup(b) + spindown(b))
    ts, rhos = timeevolution.master(range(0, 1, length=5), psi0, H, [0.5*sigmam(b)])
    tr_last = real(tr(rhos[end]))
    abs(tr_last - 1.0) < 1e-9 || error("trace drift: $tr_last")
    "Lindblad trace preserved: $tr_last"
end

@probe "quantumclifford_stabilizer" begin
    s = S"XX ZZ"
    canonicalize!(s)
    "Bell stabilizer canonicalized: $(string(s))"
end

@probe "cliffordalgebras_rotor" begin
    cl = CliffordAlgebra(3)
    gp = cl.e1 * cl.e2
    CliffordAlgebras.scalar(gp * gp) == -1 || error("(e1e2)^2 scalar != -1")
    "Cl(3): (e1*e2)^2 = -1 verified"
end

@probe "octonions_nonassociativity" begin
    a = Octonion(0,1,0,0,0,0,0,0); b = Octonion(0,0,1,0,0,0,0,0); c = Octonion(0,0,0,0,1,0,0,0)
    assoc = (a*b)*c - a*(b*c)
    abs(assoc) > 1e-12 || error("associator vanished")
    "octonion associator nonzero: |assoc|=$(abs(assoc))"
end

@probe "quaternions_unit_rotation" begin
    q = Quaternion(cos(pi/4), sin(pi/4), 0, 0)
    abs(abs(q) - 1.0) < 1e-12 || error("not unit")
    "unit quaternion verified"
end

@probe "differentialequations_ode" begin
    prob = ODEProblem((u, p, t) -> -u, 1.0, (0.0, 1.0))
    sol = solve(prob, Tsit5(), abstol=1e-10, reltol=1e-10)
    err = abs(sol.u[end] - exp(-1))
    err < 1e-8 || error("ODE error $err")
    "dy/dt=-y: |err|=$(round(err, sigdigits=2))"
end

@probe "itensors_mps_norm" begin
    sites = siteinds("S=1/2", 6)
    psi = random_mps(sites; linkdims=4)
    n = norm(psi)
    abs(n - 1.0) < 1e-10 || error("norm $n")
    "6-site MPS norm = 1"
end

@probe "manifolds_sphere_geodesic" begin
    S = Sphere(2)
    d = distance(S, [1.0, 0, 0], [0, 1.0, 0])
    abs(d - pi/2) < 1e-12 || error("distance $d")
    "S2 great-circle distance = pi/2"
end

@probe "symbolics_identity" begin
    @variables x
    expr = simplify(sin(x)^2 + cos(x)^2)
    string(expr) == "1" || error("not simplified: $expr")
    "sin^2+cos^2 -> 1"
end

@probe "graphs_toposort" begin
    g = SimpleDiGraph(4)
    add_edge!(g, 1, 2); add_edge!(g, 2, 3); add_edge!(g, 1, 4); add_edge!(g, 4, 3)
    order = topological_sort_by_dfs(g)
    order[1] == 1 || error("bad toposort")
    "DAG toposort ok"
end

# isolated envs via subprocess (own projects, clean worlds)
@probe "attractors_basin_fractions_isolated" begin
    code = """
    using Pkg; Pkg.activate(joinpath(homedir(), ".julia/environments/codex-ratchet-attractors-v1.12"), io=devnull)
    using Attractors, StaticArrays
    henon_rule(x, p, n) = SVector{2}(1.0 - p[1]*x[1]^2 + x[2], p[2]*x[1])
    ds = DeterministicIteratedMap(henon_rule, [0.0, 0.0], [1.4, 0.3])
    grid = (range(-2, 2; length=50), range(-2, 2; length=50))
    mapper = AttractorsViaRecurrences(ds, grid; sparse=false)
    basins, atts = basins_of_attraction(mapper, grid; show_progress=false)
    println("ATTRACTORS_FOUND=", length(atts))
    """
    out = read(pipeline(`julia --startup-file=no -e $code`, stderr=devnull), String)
    m = match(r"ATTRACTORS_FOUND=(\d+)", out)
    m !== nothing || error("no output: $(first(out, 150))")
    "Henon basins in isolated env: $(m[1]) attractor(s)"
end

@probe "tensorkit_symmetric_tensor_isolated" begin
    code = """
    using Pkg; Pkg.activate(joinpath(homedir(), ".julia/environments/codex-ratchet-tensorkit-v1.12"), io=devnull)
    using TensorKit
    V = ComplexSpace(2)
    t = randn(V ⊗ V, V)
    println("TK_NORM=", norm(t) > 0)
    """
    out = read(pipeline(`julia --startup-file=no -e $code`, stderr=devnull), String)
    occursin("TK_NORM=true", out) || error("failed: $(first(out, 150))")
    "TensorKit tensor built in isolated env"
end

@probe "enzyme_autodiff_isolated" begin
    # Enzyme loaded in subprocess to avoid polluting this session's world
    code = """
    using Enzyme
    x = [0.2, -0.1, 0.4]; target = [0.1, 0.2, 0.3]
    f(z) = sum((z .- target).^2)
    dx = zero(x)
    autodiff(Reverse, Const(f), Active, Duplicated(x, dx))
    println("GRAD_ERR=", maximum(abs.(dx .- 2 .* (x .- target))))
    """
    out = read(pipeline(`julia --startup-file=no -e $code`, stderr=devnull), String)
    m = match(r"GRAD_ERR=([\d.e-]+)", out)
    (m !== nothing && parse(Float64, m[1]) < 1e-12) || error("grad: $(first(out, 150))")
    "Enzyme reverse-mode grad exact"
end

npass = count(r -> r["status"] == "PASS", values(results))
const BATTERY_OUT = get(ENV, "CODEX_JL_BATTERY_RESULT_PATH", joinpath(@__DIR__, "jl_battery_results.json"))
mkpath(dirname(BATTERY_OUT))
open(BATTERY_OUT, "w") do io
    JSON.print(io, Dict("battery"=>"julia", "pass"=>npass, "fail"=>length(results)-npass, "results"=>results), 1)
end
println("=== $npass/$(length(results)) PASS")
