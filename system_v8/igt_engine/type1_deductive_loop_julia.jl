# Type-1 DEDUCTIVE outer loop — Julia leg (AUTHORITATIVE, QuantumOptics master equation).
# Mirrors type1_deductive_loop_jax.py exactly: Type-1 s=+1, H_L=+H0, FeTi/z-family
# operators, terrain order Se->Ne->Ni->Si, Axis-6 up/down composition.
# Terrain flows integrated by QuantumOptics.timeevolution.master (genuine package use).
# STATUS: candidate engine-cycle probe; promotion_allowed=false; tool_lego_fit_probe.

using QuantumOptics
using JSON
using LinearAlgebra

b = GenericBasis(2)
mI = ComplexF64[1 0; 0 1]
mx = ComplexF64[0 1; 1 0]
my = ComplexF64[0 -im; im 0]
mz = ComplexF64[1 0; 0 -1]
msm = ComplexF64[0 0; 1 0]     # sigma_-  (matches jax sm)
mP0 = ComplexF64[1 0; 0 0]
mP1 = ComplexF64[0 0; 0 1]

op(M) = Operator(b, M)

# frozen parameters (identical to jax leg)
nvec = [0.6, 0.0, 0.8]
H0m = nvec[1]*mx + nvec[2]*my + nvec[3]*mz
s_sign = 1.0
gF=0.6; gV=0.6; gP=0.6; gSi=0.6
eF=0.9; eV=1.0; eP=0.9
wSi=0.8; tau=0.5; qTi=0.5; phiFe=0.7

# terrain (H_eff, jump ops), signs folded (Type-1 s=+1)
terr_Se() = (op(s_sign*eF*H0m), [op(sqrt(gF)*mz)])
terr_Ne() = (op(s_sign*H0m),    [op(sqrt(eV*gV)*mx)])
terr_Ni() = (op(s_sign*eP*H0m), [op(sqrt(gP)*msm)])
terr_Si() = (op(s_sign*wSi*mz), [op(sqrt(gSi)*mP0), op(sqrt(gSi)*mP1)])

function flow_terr(terr, rho::Operator)
    H, J = terr()
    tout, rhot = timeevolution.master([0.0, tau], rho, H, J; abstol=1e-11, reltol=1e-11)
    r = rhot[end]
    M = (r.data + r.data')/2
    return op(M / real(tr(M)))
end

# discrete operator channels (identical math to jax)
function O_Ti(rho::Operator)
    M = rho.data
    Md = (1-qTi)*M + qTi*(mP0*M*mP0 + mP1*M*mP1)
    return op(Md)
end
function O_Fe(rho::Operator)
    Uz = exp(-im*phiFe*mz/2)
    return op(Uz * rho.data * Uz')
end

# Axis-6 composed stages
stage1(rho) = flow_terr(terr_Se, O_Ti(rho))   # Se, Ti^  operator-first
stage2(rho) = O_Ti(flow_terr(terr_Ne, rho))   # Ne, Ti_  terrain-first
stage3(rho) = O_Fe(flow_terr(terr_Ni, rho))   # Ni, Fe_  terrain-first
stage4(rho) = flow_terr(terr_Si, O_Fe(rho))   # Si, Fe^  operator-first

function vN(rho::Operator)
    w = real.(eigvals(Hermitian(rho.data)))
    w = clamp.(w, 1e-12, 1.0)
    return -sum(w .* log.(w))
end

rho0 = op(0.5*(mI + 0.5*mx + 0.3*mz))
s1 = stage1(rho0); s2 = stage2(s1); s3 = stage3(s2); s4 = stage4(s3)
traj = [rho0, s1, s2, s3, s4]
ent = [vN(r) for r in traj]
rho_out = s4

dS_loop = ent[end] - ent[1]
purity_out = real(tr(rho_out.data * rho_out.data))
rev = stage1(stage2(stage3(stage4(rho0))))
loop_noncomm = norm(rho_out.data - rev.data)
c1 = O_Fe(O_Ti(rho0)); c2 = O_Ti(O_Fe(rho0))
ctrl_noncomm = norm(c1.data - c2.data)

out = Dict(
    "engine" => "julia:QuantumOptics",
    "loop" => "type1_deductive_outer",
    "terrain_order" => "Se->Ne->Ni->Si",
    "vN_entropy_trajectory" => ent,
    "dS_loop" => dS_loop,
    "purity_out" => purity_out,
    "loop_noncomm_fwd_vs_rev" => loop_noncomm,
    "commuting_control_noncomm" => ctrl_noncomm,
    "ran" => true,
)
println(JSON.json(out))
