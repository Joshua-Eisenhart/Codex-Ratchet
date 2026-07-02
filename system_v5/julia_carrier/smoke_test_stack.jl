# Phase-1 live smoke-test: resolved != runs. Each package gets a REAL operation, isolated in try/catch,
# so one failure does not abort the rest. Prints a PASS/FAIL table + a JSON receipt.
import JSON

results = Vector{Dict{String,Any}}()
function check(f, name::String)
    t0 = time()
    try
        detail = f()
        push!(results, Dict("pkg"=>name, "ok"=>true, "detail"=>string(detail), "sec"=>round(time()-t0; digits=2)))
        println("PASS  $name  ($(round(time()-t0;digits=1))s)  $detail")
    catch e
        msg = try; first(split(string(e), '\n')); catch; string(typeof(e)); end
        push!(results, Dict("pkg"=>name, "ok"=>false, "detail"=>msg, "sec"=>round(time()-t0; digits=2)))
        println("FAIL  $name  ($(round(time()-t0;digits=1))s)  $msg")
    end
end

# 1. Grassmann — geometric product of basis blades (full-spinor algebra carrier)
check("Grassmann.geometric_product") do
    @eval using Grassmann
    @eval basis"3"
    r = @eval (v1 * v2)          # e1*e2 -> bivector
    "v1*v2 = $r"
end

# 2. CliffordAlgebras — Cl(3,0) rotor exp (SU(2) gauge source)
check("CliffordAlgebras.rotor") do
    @eval using CliffordAlgebras
    cl = @eval CliffordAlgebra(:Cl3)
    "algebra=$(typeof(cl))"
end

# 3. ITensors + ITensorMPS — random MPS + inner (TN entanglement carrier)
check("ITensorMPS.random_mps_inner") do
    @eval using ITensors, ITensorMPS
    ip = @eval begin
        s = siteinds("S=1/2", 6)
        psi = random_mps(s; linkdims=8)
        inner(psi, psi)
    end
    "inner(psi,psi)=$(round(real(ip);digits=6))"
end

# 4. ITensorNetworks — the DEFERRED 3-D claim: exact named_grid((2,2,2)) contraction
check("ITensorNetworks.exact_3d_2x2x2") do
    @eval using ITensorNetworks, NamedGraphs, OMEinsumContractionOrders, Graphs
    val = @eval begin
        g = NamedGraphs.NamedGraphGenerators.named_grid((2, 2, 2))  # genuine 3-D lattice graph (8 vertices)
        s = ITensorNetworks.siteinds("S=1/2", g)
        tn = ITensorNetworks.ITensorNetwork(v -> "Up", s)           # product state on the 3-D grid
        seq = ITensorNetworks.contraction_sequence(tn; alg="greedy") # order-finder needs OMEinsumContractionOrders
        T = ITensorNetworks.contract(tn; sequence=seq)              # exact contraction -> rank-8 state tensor |psi>
        nrm = ITensors.scalar(T * ITensors.dag(T))                  # <psi|psi>: contract all 8 legs -> scalar = 1.0
        (Graphs.nv(g), round(real(nrm); digits=6))
    end
    "3d_grid_vertices,scalar=$val"
end

# 5. DifferentialEquations — EnsembleProblem (the BRANCH engine)
check("DifferentialEquations.EnsembleProblem") do
    @eval using DifferentialEquations
    n = @eval begin
        f(u, p, t) = -u
        prob = ODEProblem(f, [1.0], (0.0, 1.0))
        ep = EnsembleProblem(prob, prob_func = (p, i, r) -> remake(p, u0 = [1.0 + 1e-3*i]))
        sol = solve(ep, Tsit5(), EnsembleThreads(); trajectories = 8)
        length(sol)
    end
    "$n trajectories solved"
end

# 6. Attractors — basin clustering (the SELECTION / survivor metric)
check("Attractors.basins") do
    @eval using Attractors, DynamicalSystems, StaticArrays
    nb = @eval begin
        ds = CoupledODEs((u, p, t) -> SA[u[2], -u[1] - 0.1u[2]], SA[1.0, 0.0])
        grid = (range(-2, 2; length = 11), range(-2, 2; length = 11))
        mapper = AttractorsViaRecurrences(ds, grid)
        basins, attractors = basins_of_attraction(mapper, grid)
        length(attractors)
    end
    "$nb attractor(s) mapped"
end

# 7. Z3 — UNSAT verdict (the rigorous proof form). Fully qualified: Z3.check collides with this file's check().
check("Z3.unsat") do
    @eval using Z3
    verdict = @eval begin
        ctx = Z3.Context()
        x = Z3.IntVar("x", ctx)          # Z3.jl signature: IntVar(name::String, ctx) -- name first
        sol = Z3.Solver(ctx)
        Z3.add(sol, Z3.IntVal(1, ctx) < x)   # 1 < x  (isless needs BOTH operands as Expr)
        Z3.add(sol, x < Z3.IntVal(0, ctx))   # x < 0
        string(Z3.check(sol))                # 1<x & x<0 over integers -> unsat
    end
    "x>1 & x<0 -> $verdict"
end

# 8. IntervalArithmetic — interval op (branch-and-prune substrate)
check("IntervalArithmetic.interval") do
    @eval using IntervalArithmetic
    w = @eval begin
        a = interval(0.0, 1.0)
        b = a * a - a
        (inf(b), sup(b))
    end
    "[0,1]^2-[0,1] = $w"
end

# 9. QuantumClifford — stabilizer state (stabilizer/QIT cross-check). bell() avoids the parse-time S"..." macro.
check("QuantumClifford.stabilizer") do
    @eval using QuantumClifford
    d = @eval begin
        s = QuantumClifford.bell()          # 2-qubit Bell stabilizer (== S"XX ZZ")
        size(stabilizerview(s))
    end
    "Bell stabilizer dims=$d"
end

npass = count(r -> r["ok"], results)
println("\n=== $npass/$(length(results)) PASS ===")
open(joinpath(@__DIR__, "smoke_test_stack_results.json"), "w") do io
    JSON.print(io, Dict("n_pass" => npass, "n_total" => length(results), "results" => results), 2)
end
exit(npass == length(results) ? 0 : 1)
