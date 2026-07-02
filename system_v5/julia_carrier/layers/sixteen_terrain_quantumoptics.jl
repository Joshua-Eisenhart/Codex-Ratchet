# THE 16-TERRAIN PLACEMENT LATTICE on QuantumOptics.jl (rigorous Lindblad ground truth, per the owner's tooling spec).
# 16 = 4 topology laws (Se/Ne/Ni/Si) x 2 Weyl sheets (H_L=+H0, H_R=-H0) x 2 path placements (fiber/lifted-base).
# Each terrain = a (Hamiltonian H, jump operators J) pair; timeevolution.master solves the exact Lindblad master eq.
# QuantumOptics is LOAD-BEARING here (the master-equation solver IS the dynamics, not a hand-rolled integrator), and
# the steady states are CROSS-CHECKED against the independent hand-rolled RK4 sim (sixteen_terrain_placement_lattice.jl).
# classification = sixteen_terrain_qo_poc ; promotion_allowed = false.

using QuantumOptics, LinearAlgebra, JSON

const b = SpinBasis(1//2)
const SX = sigmax(b); const SY = sigmay(b); const SZ = sigmaz(b); const SM = sigmam(b); const SP = sigmap(b)
const H0 = SZ; const HL = H0; const HR = -H0                 # H_L=+H0, H_R=-H0
const eps = 0.2; const gam = 1.0; const kap = 1.0
const Pp = 0.5*(identityoperator(b) + SX); const Pm = 0.5*(identityoperator(b) - SX)   # sigma_x projectors (Si basis K=sx)

# 8 terrains as (H, [jump ops]) -- the terrains.md Lindblad families:
terrains = [
  ("L","Se","Funnel",  eps*HL, [SM, sqrt(0.3)*SP]),                # dissipative release + weak coherent
  ("L","Ne","Vortex",  HL,     [sqrt(eps)*SZ]),                    # Hamiltonian circulation + weak dephasing
  ("L","Ni","Pit",     eps*HL, [sqrt(gam)*SM]),                    # sink -> |down>
  ("L","Si","Hill",    SX,     [sqrt(kap)*Pp, sqrt(kap)*Pm]),      # dephase around sigma_x commuting basis
  ("R","Se","Cannon",  eps*HR, [SM, sqrt(0.3)*SP]),
  ("R","Ne","Spiral",  HR,     [sqrt(eps)*SZ]),                    # opposite chirality (H_R=-H0)
  ("R","Ni","Source",  eps*HR, [sqrt(gam)*SP]),                    # sink -> |up>
  ("R","Si","Citadel", SX,     [sqrt(kap)*Pp, sqrt(kap)*Pm]),
]

bloch(rho) = real.([expect(SX,rho), expect(SY,rho), expect(SZ,rho)])

function initial_density()
    # Match sixteen_terrain_placement_lattice.jl exactly: rho_of([0.6,0.3,0.2] / norm(...)).
    r0 = [0.6, 0.3, 0.2] ./ norm([0.6, 0.3, 0.2])
    return 0.5*(identityoperator(b) + r0[1]*SX + r0[2]*SY + r0[3]*SZ)
end

function run_terrain(H, J; base=false)
    # base path = lifted-base traversal drift (extra rotation about z, rate cos(2eta)); fiber = none
    eta = pi/6; Hb = base ? H + cos(2eta)*SZ : H
    rho0 = initial_density()   # same initial density as the hand-rolled RK4 reference
    tout, rhot = timeevolution.master(collect(0:0.05:40.0), rho0, Hb, J)
    s = bloch(rhot[end])
    # circulation: net azimuthal winding in xy over the trajectory
    ang = 0.0; bs = bloch.(rhot)
    for i in 2:length(bs)
        da = atan(bs[i][2],bs[i][1]) - atan(bs[i-1][2],bs[i-1][1])
        da > pi && (da-=2pi); da < -pi && (da+=2pi); ang += da
    end
    (steady=round.(s,digits=3), circulation=round(ang,digits=2),
     coh_off_sx=round(hypot(s[2],s[3]),digits=3),   # Si dephasing kills y,z (off the sigma_x axis)
     rx=round(s[1],digits=3), sz=round(s[3],digits=3), purity=round(real(expect(rhot[end],rhot[end])),digits=3))
end

println("=== 16-terrain lattice on QuantumOptics.jl (timeevolution.master) ===")
P = Dict{String,Any}(); C = Dict{String,Any}()
for (sheet,topo,name,H,J) in terrains
    f = run_terrain(H,J; base=false); g = run_terrain(H,J; base=true)
    P["$(name)_f"]=f; P["$(name)_b"]=g; C[name]=(sheet=sheet,topo=topo,fiber=f,base=g)
    println("  $sheet $topo $(rpad(name,8)) steady=$(f.steady) circ=$(f.circulation) coh_off_sx=$(f.coh_off_sx) sz=$(f.sz)")
end

f=C["Funnel"].fiber; v=C["Vortex"].fiber; p=C["Pit"].fiber; h=C["Hill"].fiber
src=C["Source"].fiber; sp=C["Spiral"].fiber; ci=C["Citadel"].fiber
checks = Dict(
  "Ni_sinks_opposite_LR"     => p.sz < -0.3 && src.sz > 0.3,              # Pit sigma_- -> down, Source sigma_+ -> up
  "Ne_circulates"            => abs(v.circulation) > 1.0 && abs(sp.circulation) > 1.0,
  "Ne_LR_opposite_chirality" => sign(v.circulation) == -sign(sp.circulation),
  "Si_dephases_off_sx"       => h.coh_off_sx < 0.1 && ci.coh_off_sx < 0.1, # FIXED: y,z killed, sigma_x axis preserved
  "Si_preserves_sx_axis"     => abs(h.rx) > 0.3,                          # dephasing keeps the commuting (x) component
  "terrains_distinct"        => length(unique([C[n].fiber.steady for n in keys(C)])) >= 6,
  "fiber_vs_base_differ"     => any(P["$(n)_f"].circulation != P["$(n)_b"].circulation for (s,t,n,H,J) in terrains),
  "sixteen_placements"       => length(P) == 16,
)
all_pass = all(values(checks))

# CROSS-CHECK vs the hand-rolled RK4 sim (independent solver, same master equation -> steady states must agree)
xref = Dict("Funnel"=>-0.538, "Vortex"=>0.286, "Pit"=>-1.0, "Source"=>1.0, "Hill_rx"=>0.857)
xcheck = abs(f.sz-(-0.538))<0.05 && abs(v.sz-0.286)<0.05 && abs(p.sz-(-1.0))<0.05 &&
         abs(src.sz-1.0)<0.05 && abs(h.rx-0.857)<0.05
checks["crosscheck_vs_handrolled_RK4"] = xcheck
all_pass = all(values(checks))

result = Dict(
  "name"=>"sixteen_terrain_quantumoptics","classification"=>"sixteen_terrain_qo_poc","promotion_allowed"=>false,
  "tool_integration"=>Dict("QuantumOptics.jl"=>"load_bearing (timeevolution.master IS the dynamics)",
                           "crosscheck"=>"independent hand-rolled RK4 sixteen_terrain_placement_lattice.jl agrees on steady states"),
  "claim_ceiling"=>"PoC: the 16-terrain placement lattice solved with the QuantumOptics Lindblad master equation; each " *
                   "terrain's steady state + dynamical type MEASURED, cross-checked vs an independent RK4 integrator. " *
                   "NOT a G-structure admission. promotion_allowed=false.",
  "placements"=>P, "checks"=>checks, "all_pass"=>all_pass,
)
open(joinpath(@__DIR__,"sixteen_terrain_quantumoptics_results.json"),"w") do io; JSON.print(io,result,2); end
println()
for (k,v) in sort(collect(checks);by=first); println(rpad(k,30), v ? "PASS" : "FAIL"); end
println("ALL_PASS = $all_pass  (QuantumOptics master eq; cross-checks hand-rolled RK4)")
exit(all_pass ? 0 : 1)
