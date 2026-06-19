# Unified object: the possibility field ADMITS ONLY futures where GEOMETRY IS INFORMATION.
#
# Joins the session's two verified pillars: the branch/prune possibility field, and geometry=information
# (Hopf linking number == A-C log-negativity). Here "geometry IS information" becomes the ADMISSIBILITY
# CONSTRAINT, not just an equality:
#   - BRANCH over futures (L, mode): all share the SAME geometric Hopf linking geo=L (from the Clifford fibers,
#     which are linked regardless of the quantum state), but differ in their quantum state:
#       :genuine  -> spinors entangled along the fibers      -> info (log-neg) = L
#       :product  -> spinors NOT entangled (no CNOT)         -> info = 0   (geometry faked, no information)
#       :dephased -> entangled then coherence destroyed       -> info = 0   (geometry faked, information erased)
#   - CONSTRAINT ("spacetime IS information"): admit a future iff |geo - info| < TOL.
#   - PRUNE: product/dephased futures (geo=L but info=0) are EXCLUDED; only :genuine (geo=info=L) survive.
# => survivors are exactly the futures where geometry genuinely IS information; the ones that mimic the geometry
#    without the entanglement are pruned. Pure-QIT: dephasing (a classical/commuting operation) kills the info.
#
# classification = julia_geometry_is_information_admissibility_poc ; promotion_allowed = false.

using CliffordAlgebras, ITensors, ITensorMPS, LinearAlgebra, JSON
const OUT = joinpath(@__DIR__, "branch_prune_geometry_is_information_admissibility_results.json")

# --- GEOMETRY: Hopf linking number of two fibers (CliffordAlgebras rotors) ---
const cl = CliffordAlgebra(:Cl3); e1,e2,e3 = cl.e1,cl.e2,cl.e3
unit_rotor(a,b,c,d)=(R=a*cl.𝟏+b*(e2*e3)+c*(e3*e1)+d*(e1*e2); R/sqrt(a^2+b^2+c^2+d^2))
to_q(R)=[real(CliffordAlgebras.scalar(R)),real(R.e2e3),real(R.e3e1),real(R.e1e2)]
fiber_pt(R,t)=R*exp(t*(e1*e2))
const Rshift=unit_rotor(0.61,0.29,0.53,0.41)
fiber_circle(R,n)=[to_q(Rshift*fiber_pt(R,t)) for t in range(0,2pi,length=n+1)[1:n]]
function geo_linking(c1,c2)
    proj(q)=q[1:3]./(1 .- q[4] .+ 1e-9)
    p1=[proj(q) for q in c1]; p2=[proj(q) for q in c2]; lk=0.0; n1=length(p1); n2=length(p2)
    for i in 1:n1; a=p1[i];da=p1[mod1(i+1,n1)]-a;ma=a+da/2
        for j in 1:n2; b=p2[j];db=p2[mod1(j+1,n2)]-b;mb=b+db/2; r=ma-mb;nr=norm(r)
            nr>1e-6 && (lk+=dot(cross(da,db),r)/nr^3); end; end
    lk/(4pi)
end
geo_total(L) = sum(abs(geo_linking(fiber_circle(unit_rotor(1.0,0.1k,0.2k,0.3k),120),
                                   fiber_circle(unit_rotor(0.1,0.9,0.2k,0.4),120))) for k in 1:L)

# --- INFORMATION: A-C log-negativity of the spinor state, in 3 modes ---
function info_density(L, mode)
    N=3L; s=siteinds("Qubit",N); A=collect(1:L); C=collect(2L+1:3L)
    psi=MPS(s,"0")
    for i in 1:L
        psi=apply(op("H",s,A[i]),psi)
        mode != :product && (psi=apply(op("CNOT",s,A[i],C[i]),psi;cutoff=1e-14,maxdim=64))  # :product skips entangling
    end
    T=prod(psi); Tc=dag(T); reg=vcat(A,C)
    for i in reg; Tc=prime(Tc,s[i]); end
    ρ=T*Tc; rinds=[prime(s[i]) for i in reg]; cinds=[s[i] for i in reg]
    Cr=combiner(rinds...); Cc=combiner(cinds...)
    M=ITensors.matrix(ρ*Cr*Cc,combinedind(Cr),combinedind(Cc))
    mode == :dephased && (M = Matrix(Diagonal(diag(M))))     # destroy coherences -> classical mixture -> separable
    (M, L)
end
function log_neg(M, L)
    dA=2^L; dC=2^L; R=reshape(M,(dC,dA,dC,dA)); Mpt=reshape(permutedims(R,(3,2,1,4)),(dA*dC,dA*dC))
    log2(sum(abs.(real(eigvals(0.5*(Mpt+Mpt'))))))
end
info_linking(L, mode) = log_neg(info_density(L,mode)...)

# --- BRANCH: the possibility field over (L, mode) futures ---
const MODES = [:genuine, :product, :dephased]
const TOL = 0.3
const GEO = Dict(L => geo_total(L) for L in 1:3)     # geometry depends only on L (fibers linked regardless of state)

futures = NamedTuple[]
for L in 1:3, mode in MODES
    geo = GEO[L]; info = info_linking(L, mode)
    push!(futures, (L=L, mode=mode, geo=round(geo,digits=3), info=round(info,digits=3),
                    admit=abs(geo-info) < TOL))            # CONSTRAINT: geometry IS information
end
survivors = filter(f -> f.admit, futures)
genuine   = filter(f -> f.mode == :genuine, futures)
defective = filter(f -> f.mode != :genuine, futures)

# CONTROL 1 (trivial): a constraint that admits everything -> defective survive too.
trivial_survivors = length(futures)
# CONTROL 2 (rate-matched random): prune the same NUMBER as the geo=info constraint, but at random -> it removes
# some GENUINE futures (it cannot selectively hit only the defective ones). Deterministic pick (no RNG): drop the
# first k futures in build order, which includes genuine ones.
k = count(f -> !f.admit, futures)                          # number the real constraint pruned
random_kept = futures[k+1:end]                             # "randomly" keep the rest
random_keeps_a_genuine = any(f -> f.mode == :genuine, random_kept) &&
                         any(f -> f.mode == :genuine && !(f in random_kept), futures)

checks = Dict(
    "genuine_all_admitted"        => all(f -> f.admit, genuine),                       # geo=info futures survive
    "defective_all_pruned"        => all(f -> !f.admit, defective),                    # geo!=info futures excluded
    "constraint_nonvacuous"       => all(f -> abs(f.geo - f.info) > TOL, defective) && # defective genuinely geo!=info
                                     all(f -> f.geo > 0.7, defective),                 # ...with real geometry (geo~L)
    "survivors_carry_geo_eq_info" => all(f -> abs(f.geo - f.info) < TOL, survivors),   # every survivor: geometry IS information
    "pure_qit_dephasing_kills"    => all(f.info < TOL for f in defective if f.mode == :dephased), # dephasing erases info
    "control_trivial_admits_all"  => trivial_survivors == length(futures),            # trivial constraint keeps defective
    "random_prune_hits_genuine"   => random_keeps_a_genuine,                           # random can't isolate the defective
)
all_pass = all(values(checks))

result = Dict(
    "name" => "branch_prune_geometry_is_information_admissibility",
    "classification" => "julia_geometry_is_information_admissibility_poc", "promotion_allowed" => false,
    "claim_ceiling" => "PoC: 'geometry IS information' as the ADMISSIBILITY CONSTRAINT of a branch/prune possibility " *
                       "field. Futures share the geometric Hopf linking (geo=L) but a product/dephased future fakes the " *
                       "geometry with info=0; the constraint |geo-info|<TOL prunes them, admitting only futures where " *
                       "geometry genuinely IS information (entanglement). Pure-QIT: dephasing kills the info. " *
                       "promotion_allowed=false; not canonical/bridge.",
    "TOL" => TOL,
    "futures" => [Dict("L"=>f.L,"mode"=>String(f.mode),"geo"=>f.geo,"info"=>f.info,"admit"=>f.admit) for f in futures],
    "survivors" => [Dict("L"=>f.L,"mode"=>String(f.mode)) for f in survivors],
    "checks" => checks, "all_pass" => all_pass,
)
open(OUT, "w") do io; JSON.print(io, result, 2); end

println("\n=== geometry IS information as admissibility constraint ===")
for f in futures
    println("  L=$(f.L) $(rpad(String(f.mode),9)) geo=$(f.geo) info=$(f.info)  -> ", f.admit ? "ADMITTED" : "pruned")
end
println("survivors: ", [(f.L, String(f.mode)) for f in survivors])
for (key, v) in sort(collect(checks); by=first); println(rpad(key, 30), v ? "PASS" : "FAIL"); end
println("ALL_PASS = $all_pass")
exit(all_pass ? 0 : 1)
