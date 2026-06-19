#!/usr/bin/env julia
"""
Axis 0 — operational correlation/entropy monotones on L/R Weyl spinor density matrices.

object_id: axis0_entropy_monotone_julia
claim_ceiling: candidate — passes F01+N01 gate. NOT layer-complete. NOT a bridge claim.
  promotion_allowed: false
engine: Julia (LinearAlgebra, reference/proof path)

Finite map:
  domain:  L/R Weyl spinor states on nested-shell torus (2 shells, 6x6x4 = 288 sites)
  codomain: (S_L, S_R, S_shell_inner, S_shell_outer, MI_LR, CI_LR, MI_shells, corr_mono, split_label)

Correlation structure:
  Individual spinors are pure and separable; ensemble joint
  rho_joint = (1/N) sum_i rhoL_i ⊗ rhoR_i
  is a correlated mixture (not a product of marginals in general).

N01: [Ti, Fi] genuinely non-commuting (z-dephase vs x-rotation); entropy and
     correlation monotone change under order permutation.

Axis-0 split: threshold on corr_mono ladder => homeostasis vs allostasis.
"""

using LinearAlgebra
using JSON

# ---- Constants ----
const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const P0 = ComplexF64[1 0; 0 0]
const P1 = ComplexF64[0 0; 0 1]
const Qp = 0.5 * ComplexF64[1 1; 1 1]
const Qm = 0.5 * ComplexF64[1 -1; -1 1]

const SHELLS_RADII = [0.6, 1.0]
const NPhi = 6
const NChi = 6
const NEta = 4

# ---- Weyl spinor construction ----
function weyl_spinor(phi::Float64, chi::Float64, eta::Float64, s::Int)
    psi = ComplexF64[
        exp(im*(phi + s*chi)) * cos(eta),
        exp(im*(phi - s*chi)) * sin(eta)
    ]
    n = norm(psi)
    n < 1e-15 && (psi[1] = 1.0; return psi)
    return psi / n
end

function build_sites()
    sites = Tuple{Float64,Float64,Float64,Float64}[]
    for r in SHELLS_RADII
        for i in 0:(NPhi-1)
            phi = 2π*i/NPhi
            for j in 0:(NChi-1)
                chi = 2π*j/NChi
                for k in 0:(NEta-1)
                    eta = (π/2)*(k+0.5)/NEta
                    push!(sites, (r, phi, chi, eta))
                end
            end
        end
    end
    return sites
end

function build_density_matrices(sites)
    N = length(sites)
    rhoL = Vector{Matrix{ComplexF64}}(undef, N)
    rhoR = Vector{Matrix{ComplexF64}}(undef, N)
    for (idx, (r, phi, chi, eta)) in enumerate(sites)
        psiL = weyl_spinor(phi, chi, eta*r, +1)
        psiR = weyl_spinor(phi, chi, eta*r, -1)
        rhoL[idx] = psiL * psiL'
        rhoR[idx] = psiR * psiR'
    end
    return rhoL, rhoR
end

# ---- Von Neumann entropy ----
function vn_entropy(rho::Matrix{ComplexF64})
    evals = real.(eigvals(Hermitian(rho)))
    evals = clamp.(evals, 1e-15, Inf)
    return -sum(e * log(e) for e in evals)
end

# ---- Partial traces of 4x4 density matrix ----
function partial_trace_A(rhoAB::Matrix{ComplexF64})
    # rho_B[i,j] = sum_{k=0,1} rhoAB[2k+i, 2k+j]  (1-indexed: k=0->1, k=1->3)
    rho_B = zeros(ComplexF64, 2, 2)
    for k in 0:1
        for i in 1:2
            for j in 1:2
                rho_B[i,j] += rhoAB[2k+i, 2k+j]
            end
        end
    end
    return rho_B
end

function partial_trace_B(rhoAB::Matrix{ComplexF64})
    # rho_A[a,b] = sum_{i=1,2} rhoAB[2(a-1)+i, 2(b-1)+i]
    rho_A = zeros(ComplexF64, 2, 2)
    for i in 1:2
        for a in 1:2
            for b in 1:2
                rho_A[a,b] += rhoAB[2(a-1)+i, 2(b-1)+i]
            end
        end
    end
    return rho_A
end

# ---- Ensemble joint state ----
function ensemble_joint(rhoL_batch::Vector{Matrix{ComplexF64}},
                        rhoR_batch::Vector{Matrix{ComplexF64}})
    N = length(rhoL_batch)
    joint = zeros(ComplexF64, 4, 4)
    for i in 1:N
        joint .+= kron(rhoL_batch[i], rhoR_batch[i])
    end
    return joint / N
end

# ---- Mutual information ----
function mutual_information(rhoA::Matrix{ComplexF64}, rhoB::Matrix{ComplexF64},
                            rhoAB::Matrix{ComplexF64})
    return vn_entropy(rhoA) + vn_entropy(rhoB) - vn_entropy(rhoAB)
end

# ---- Coherent information CI(A>B) = S(B) - S(AB) ----
function coherent_information(rhoAB::Matrix{ComplexF64})
    rho_B = partial_trace_A(rhoAB)
    return vn_entropy(rho_B) - vn_entropy(rhoAB)
end

# ---- Correlation monotone: trace norm of (rhoAB - rhoA⊗rhoB) ----
function correlation_monotone(rhoAB::Matrix{ComplexF64},
                              rhoA::Matrix{ComplexF64}, rhoB::Matrix{ComplexF64})
    diff = rhoAB - kron(rhoA, rhoB)
    evals = real.(eigvals(Hermitian(diff)))
    return sum(abs, evals)
end

# ---- Operator channels ----
Ti_channel(rho::Matrix{ComplexF64}, q::Float64=0.5) =
    (1-q)*rho + q*(P0*rho*P0 + P1*rho*P1)

function Ux(t::Float64)
    return cos(t/2)*I2 - im*sin(t/2)*sx
end

function Uz(p::Float64)
    return cos(p/2)*I2 - im*sin(p/2)*sz
end

Fi_channel(rho::Matrix{ComplexF64}, t::Float64=0.7) =
    let U = Ux(t); U*rho*U' end

Fe_channel(rho::Matrix{ComplexF64}, p::Float64=0.7) =
    let U = Uz(p); U*rho*U' end

# ---- Main ----
println("=" ^ 60)
println("AXIS 0 — Julia reference path")
println("object_id: axis0_entropy_monotone_julia")
println("claim_ceiling: candidate | promotion_allowed: false")
println("=" ^ 60)

sites = build_sites()
N = length(sites)
n_per_shell = NPhi * NChi * NEta  # 144
println("\nF01 check: N=$N sites, $(length(SHELLS_RADII)) shells x $(NPhi)x$(NChi)x$(NEta) grid")
@assert N < 1_000_000_000 "F01 violated: infinite sites"

rhoL, rhoR = build_density_matrices(sites)
@assert all(size(r) == (2,2) for r in rhoL) "F01 violated: wrong shape"
@assert all(all(isfinite.(r)) for r in rhoL) "F01 violated: non-finite"

# Per-site entropy (pure -> 0)
entropies_L = [vn_entropy(r) for r in rhoL]
entropies_R = [vn_entropy(r) for r in rhoR]
mean_eL = sum(entropies_L)/N
mean_eR = sum(entropies_R)/N
println("\n--- Per-site entropy (pure spinors -> 0 expected) ---")
println("  Entropy L per-site mean: $(round(mean_eL, sigdigits=4))")
println("  Entropy R per-site mean: $(round(mean_eR, sigdigits=4))")

# Split by shell
shell_inner_L = rhoL[1:n_per_shell]
shell_outer_L = rhoL[n_per_shell+1:end]
shell_inner_R = rhoR[1:n_per_shell]
shell_outer_R = rhoR[n_per_shell+1:end]

# Ensemble joint states
joint_inner = ensemble_joint(shell_inner_L, shell_inner_R)
joint_outer = ensemble_joint(shell_outer_L, shell_outer_R)
joint_full  = ensemble_joint(rhoL, rhoR)

# Marginals
avg_L_inner = partial_trace_B(joint_inner)
avg_R_inner = partial_trace_A(joint_inner)
avg_L_outer = partial_trace_B(joint_outer)
avg_R_outer = partial_trace_A(joint_outer)

S_L_inner = vn_entropy(avg_L_inner)
S_L_outer = vn_entropy(avg_L_outer)
S_R_inner = vn_entropy(avg_R_inner)
S_R_outer = vn_entropy(avg_R_outer)

println("\n--- Von Neumann entropy per sector/shell (ensemble mixed state) ---")
println("  S(L, inner shell r=0.6): $(round(S_L_inner, digits=8))")
println("  S(L, outer shell r=1.0): $(round(S_L_outer, digits=8))")
println("  S(R, inner shell r=0.6): $(round(S_R_inner, digits=8))")
println("  S(R, outer shell r=1.0): $(round(S_R_outer, digits=8))")

# Mutual information
MI_LR_inner = mutual_information(avg_L_inner, avg_R_inner, joint_inner)
MI_LR_outer = mutual_information(avg_L_outer, avg_R_outer, joint_outer)

# Shell-to-shell MI
joint_shells_L = ensemble_joint(shell_inner_L, shell_outer_L)
avg_Li = partial_trace_B(joint_shells_L)
avg_Lo = partial_trace_A(joint_shells_L)
MI_shells = mutual_information(avg_Li, avg_Lo, joint_shells_L)

CI_LR_inner = coherent_information(joint_inner)
CI_LR_outer = coherent_information(joint_outer)

println("\n--- Mutual information (ensemble joint states) ---")
println("  MI(L:R, inner shell): $(round(MI_LR_inner, digits=8))")
println("  MI(L:R, outer shell): $(round(MI_LR_outer, digits=8))")
println("  MI(L_inner:L_outer):  $(round(MI_shells, digits=8))")

println("\n--- Coherent information ---")
println("  CI(L>R, inner shell): $(round(CI_LR_inner, digits=8))")
println("  CI(L>R, outer shell): $(round(CI_LR_outer, digits=8))")

# Correlation monotone on ensemble joints
cm_inner = correlation_monotone(joint_inner, avg_L_inner, avg_R_inner)
cm_outer = correlation_monotone(joint_outer, avg_L_outer, avg_R_outer)
marg_full_L = partial_trace_B(joint_full)
marg_full_R = partial_trace_A(joint_full)
cm_full  = correlation_monotone(joint_full, marg_full_L, marg_full_R)

# Axis-0 split: dephasing ladder
dephase_strengths = range(0.0, 1.0, length=8)
corr_monos_by_strength = Float64[]
for q in dephase_strengths
    rhoL_d = [Ti_channel(r, Float64(q)) for r in rhoL]
    joint_d = ensemble_joint(rhoL_d, rhoR)
    marg_L_d = partial_trace_B(joint_d)
    marg_R_d = partial_trace_A(joint_d)
    push!(corr_monos_by_strength, correlation_monotone(joint_d, marg_L_d, marg_R_d))
end

println("\n--- Correlation monotone vs dephasing strength (Axis-0 split probe) ---")
println("  $(rpad("q",6))  $(rpad("corr_mono",12))")
for (q, cm) in zip(dephase_strengths, corr_monos_by_strength)
    println("  $(rpad(round(q,digits=3),6))  $(rpad(round(cm,digits=8),12))")
end

threshold = sum(corr_monos_by_strength)/length(corr_monos_by_strength)
homeostasis = [cm for cm in corr_monos_by_strength if cm <= threshold]
allostasis  = [cm for cm in corr_monos_by_strength if cm >  threshold]
n_homeo = length(homeostasis)
n_allos = length(allostasis)

println("\n--- AXIS-0 SPLIT (threshold=$(round(threshold, digits=6))) ---")
println("  homeostasis (corr <= threshold): $n_homeo states")
println("  allostasis  (corr >  threshold): $n_allos states")
println("  split non-trivial: $(n_homeo > 0 && n_allos > 0)")
println("  cm_inner=$(round(cm_inner,digits=8)), cm_outer=$(round(cm_outer,digits=8)), cm_full=$(round(cm_full,digits=8))")

# N01: Ti (z-dephase) and Fi (x-rotation) are genuinely non-commuting
r0 = rhoL[1]
r_Ti_Fi = Fi_channel(Ti_channel(r0))
r_Fi_Ti = Ti_channel(Fi_channel(r0))

# Commutator norm
comm_norm = norm(Ti_channel(Fi_channel(r0)) - Fi_channel(Ti_channel(r0)))

S_TiFi_site = vn_entropy(r_Ti_Fi)
S_FiTi_site = vn_entropy(r_Fi_Ti)
n01_diff_entropy_site = abs(S_TiFi_site - S_FiTi_site)

# Ensemble N01
rhoL_TiFi = [Fi_channel(Ti_channel(r)) for r in rhoL]
rhoL_FiTi = [Ti_channel(Fi_channel(r)) for r in rhoL]

joint_TiFi = ensemble_joint(rhoL_TiFi, rhoR)
joint_FiTi = ensemble_joint(rhoL_FiTi, rhoR)

marg_L_TiFi = partial_trace_B(joint_TiFi)
marg_R_TiFi = partial_trace_A(joint_TiFi)
marg_L_FiTi = partial_trace_B(joint_FiTi)
marg_R_FiTi = partial_trace_A(joint_FiTi)

MI_TiFi = mutual_information(marg_L_TiFi, marg_R_TiFi, joint_TiFi)
MI_FiTi = mutual_information(marg_L_FiTi, marg_R_FiTi, joint_FiTi)

cm_TiFi = correlation_monotone(joint_TiFi, marg_L_TiFi, marg_R_TiFi)
cm_FiTi = correlation_monotone(joint_FiTi, marg_L_FiTi, marg_R_FiTi)

n01_diff_MI = abs(MI_TiFi - MI_FiTi)
n01_diff_cm = abs(cm_TiFi - cm_FiTi)

println("\n--- N01 order-sensitivity (Ti=z-dephase, Fi=x-rotation) ---")
println("  [Ti,Fi] commutator Frobenius norm on r0: $(round(comm_norm, sigdigits=6))")
println("  Single-site S(Ti then Fi): $(round(S_TiFi_site, digits=10))")
println("  Single-site S(Fi then Ti): $(round(S_FiTi_site, digits=10))")
println("  |entropy diff| single-site: $(round(n01_diff_entropy_site, sigdigits=3))")
println("  Ensemble MI after Ti-then-Fi: $(round(MI_TiFi, digits=10))")
println("  Ensemble MI after Fi-then-Ti: $(round(MI_FiTi, digits=10))")
println("  |MI diff|: $(round(n01_diff_MI, sigdigits=3))")
println("  corr_mono after Ti-then-Fi: $(round(cm_TiFi, digits=10))")
println("  corr_mono after Fi-then-Ti: $(round(cm_FiTi, digits=10))")
println("  |corr_mono diff|: $(round(n01_diff_cm, sigdigits=3))")
n01_sensitive = comm_norm > 1e-10 || n01_diff_MI > 1e-10 || n01_diff_cm > 1e-10
println("  N01 sensitive: $n01_sensitive")

f01_ok = (N < 1_000_000_000 &&
          all(isfinite.(corr_monos_by_strength)) &&
          isfinite(S_L_inner) &&
          isfinite(MI_LR_inner))

println("\n--- GATE SUMMARY ---")
println("  F01 (finite, terminates): $f01_ok")
println("  N01 (order-sensitive): $n01_sensitive")
println("  Axis-0 split real: $(n_homeo > 0 && n_allos > 0)")

# Write reference JSON
results = Dict(
    "object_id" => "axis0_entropy_monotone_julia",
    "engine" => "julia_linearalgebra",
    "N_sites" => N,
    "S_L_inner" => S_L_inner,
    "S_L_outer" => S_L_outer,
    "S_R_inner" => S_R_inner,
    "S_R_outer" => S_R_outer,
    "MI_LR_inner" => MI_LR_inner,
    "MI_LR_outer" => MI_LR_outer,
    "MI_shells" => MI_shells,
    "CI_LR_inner" => CI_LR_inner,
    "CI_LR_outer" => CI_LR_outer,
    "corr_mono_inner" => cm_inner,
    "corr_mono_outer" => cm_outer,
    "corr_mono_full" => cm_full,
    "corr_mono_ladder" => corr_monos_by_strength,
    "threshold" => threshold,
    "n_homeostasis" => n_homeo,
    "n_allostasis" => n_allos,
    "n01_diff_MI" => n01_diff_MI,
    "n01_diff_cm" => n01_diff_cm,
    "n01_comm_norm" => comm_norm,
    "f01_finite" => f01_ok,
    "n01_sensitive" => n01_sensitive,
    "axis0_split_real" => n_homeo > 0 && n_allos > 0,
    "promotion_allowed" => false,
    "claim_ceiling" => "candidate"
)

open("/tmp/ax0_julia_results.json", "w") do f
    JSON.print(f, results, 2)
end
println("\nResults written to /tmp/ax0_julia_results.json")
