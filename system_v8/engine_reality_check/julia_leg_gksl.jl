#!/usr/bin/env julia
# =====================================================================
# ENGINE REALITY CHECK -- JULIA LEG (authoritative substrate)
#
# Shared task: single qubit, density-operator formalism only.
#   rho0  = [[0.75, 0.25], [0.25, 0.25]]
#   H     = 0.5 * sigma_z          sigma_z = diag(1, -1)
#   gamma = 0.3
#   L     = sqrt(gamma) * sigma_minus   sigma_minus = [[0,0],[1,0]]
#
#   drho/dt = -i[H, rho] + L rho L^dag - 0.5 {L^dag L, rho}
#
# Integrated to t = 1.0 by EXACT matrix exponential of the vectorised
# Liouvillian, column-stacking convention vec(A X B) = (B^T kron A) vec(X).
# Julia's `vec` is column-major, so this convention is native here.
#
# ALIGNED PACKAGE: QuantumOptics.jl supplies the GKSL generator
# (`liouvillian`) and the operators (`sigmaz`, `sigmam`). It is
# load-bearing: the reported numbers come from exp(t * L_QO) where L_QO
# is QuantumOptics' superoperator matrix. LinearAlgebra supplies only
# `exp`, `eigen`, `norm`.
#
# A hand-built column-stacking Liouvillian and QuantumOptics'
# `timeevolution.master` ODE integrator are run as INDEPENDENT
# CROSS-CHECKS. They do not supply the reported values.
# =====================================================================

using Pkg
using QuantumOptics
using LinearAlgebra
using JSON
using Printf

const OUT_JSON = joinpath(@__DIR__, "julia_leg_gksl.json")

# --- provenance: which packages actually resolved, and from where -----
pkgversions = Dict{String,String}()
for (_uuid, dep) in Pkg.dependencies()
    if dep.name in ("QuantumOptics", "QuantumOpticsBase", "JSON")
        pkgversions[dep.name] = string(dep.version)
    end
end

println("=== JULIA LEG :: GKSL single qubit ===")
println("julia_version    = ", string(VERSION))
println("active_project   = ", Base.active_project())
for k in sort(collect(keys(pkgversions)))
    println(@sprintf("pkg %-18s = v%s", k, pkgversions[k]))
end

# --- problem specification -------------------------------------------
const GAMMA = 0.3
const TFINAL = 1.0

b = SpinBasis(1//2)                       # 2-dimensional, ordering (up, down)
sz = sigmaz(b)
sm = sigmam(b)

# Assert the package operators are literally the matrices the task names.
SZ_REF = ComplexF64[1 0; 0 -1]
SM_REF = ComplexF64[0 0; 1 0]
op_sz_ok = norm(Matrix(sz.data) - SZ_REF) < 1e-15
op_sm_ok = norm(Matrix(sm.data) - SM_REF) < 1e-15
println("sigma_z matches diag(1,-1)      : ", op_sz_ok)
println("sigma_minus matches [[0,0],[1,0]]: ", op_sm_ok)

H = 0.5 * sz
Jop = sqrt(GAMMA) * sm

rho0m = ComplexF64[0.75 0.25; 0.25 0.25]
rho0 = DenseOperator(b, copy(rho0m))

Hm = Matrix(H.data)
Jm = Matrix(Jop.data)

# --- GKSL generator from the ALIGNED package -------------------------
Lsuper = liouvillian(H, [Jop])
Lqo = Matrix(dense(Lsuper).data)          # 4x4 superoperator matrix

# --- convention check, measured not assumed --------------------------
# Compare L * vec(rho0) against the GKSL right-hand side written out
# directly, under column-stacking and under row-stacking.
drho_direct = -im * (Hm * rho0m - rho0m * Hm) +
              Jm * rho0m * Jm' -
              0.5 * (Jm' * Jm * rho0m + rho0m * Jm' * Jm)
v_apply = Lqo * vec(rho0m)
res_col = norm(reshape(v_apply, 2, 2) - drho_direct)
res_row = norm(permutedims(reshape(v_apply, 2, 2)) - drho_direct)
col_stacking_confirmed = res_col < 1e-13 && res_row > 1e-6
println(@sprintf("convention: col-stack residual %.3e | row-stack residual %.3e -> col_stacking_confirmed=%s",
                 res_col, res_row, col_stacking_confirmed))

# --- INDEPENDENT hand-built Liouvillian (cross-check only) -----------
# vec(A X B) = (B^T kron A) vec(X), column stacking.
I2 = Matrix{ComplexF64}(I, 2, 2)
JdJ = Jm' * Jm
L_hand = -im * (kron(I2, Hm) - kron(transpose(Hm), I2)) +
         kron(conj(Jm), Jm) -
         0.5 * (kron(I2, JdJ) + kron(transpose(JdJ), I2))
liouvillian_agreement = norm(L_hand - Lqo)
println(@sprintf("hand-built vs QuantumOptics Liouvillian: ||dL|| = %.3e", liouvillian_agreement))

# --- EXACT propagation: matrix exponential of the vectorised generator
Pt = exp(Lqo * TFINAL)                    # 4x4 exact matrix exponential
vec_rt = Pt * vec(rho0m)
rho_t = reshape(vec_rt, 2, 2)

# --- reported observables --------------------------------------------
t1_pop = real(rho_t[1, 1])
t2_coh_re = real(rho_t[1, 2])
t3_purity = real(tr(rho_t * rho_t))
t5_trace = real(tr(rho_t))

# von Neumann entropy in bits, from the spectrum; 0*log(0) := 0.
function vn_entropy_log2(rho::AbstractMatrix)
    herm = 0.5 * (rho + rho')
    ev = eigvals(Hermitian(herm))
    s = 0.0
    for lam in ev
        p = real(lam)
        if p > 1e-15
            s -= p * log2(p)
        end
    end
    return s
end

t4_vn_entropy_log2 = vn_entropy_log2(rho_t)
s_t0 = vn_entropy_log2(rho0m)

# --- mandatory self-checks -------------------------------------------
# C1 trace preserved to 1e-12
c1_trace_dev = abs(t5_trace - 1.0)
c1_imag_trace = abs(imag(tr(rho_t)))
c1 = c1_trace_dev < 1e-12 && c1_imag_trace < 1e-12

# C2 Hermitian to 1e-12
c2_herm_dev = norm(rho_t - rho_t')
c2 = c2_herm_dev < 1e-12

# C3 eigenvalues >= -1e-12
eigs_t = real.(eigvals(Hermitian(0.5 * (rho_t + rho_t'))))
c3_min_eig = minimum(eigs_t)
c3 = c3_min_eig >= -1e-12

# C4 S at t=0 recomputed from rho0, reported beside S(rho_t).
# Boolean form: both entropies finite, in the qubit range [0, 1] bits,
# and S(rho0) reproduced independently from the closed-form eigenvalues
# of rho0 (analytic, no eigensolver).
eigs_0 = real.(eigvals(Hermitian(0.5 * (rho0m + rho0m'))))
tr0 = real(tr(rho0m))
det0 = real(det(rho0m))
disc = sqrt(max(tr0^2 - 4 * det0, 0.0))
lam_p = 0.5 * (tr0 + disc)
lam_m = 0.5 * (tr0 - disc)
s_t0_closedform = -(lam_p > 1e-15 ? lam_p * log2(lam_p) : 0.0) -
                  (lam_m > 1e-15 ? lam_m * log2(lam_m) : 0.0)
c4_s0_agreement = abs(s_t0 - s_t0_closedform)
c4 = isfinite(s_t0) && isfinite(t4_vn_entropy_log2) &&
     0.0 <= s_t0 <= 1.0 + 1e-12 && 0.0 <= t4_vn_entropy_log2 <= 1.0 + 1e-12 &&
     c4_s0_agreement < 1e-12

# --- cross-check: QuantumOptics ODE master equation (NOT reported) ----
# `global` is required: a bare assignment inside try/catch at top level is
# soft scope and would silently create a local, leaving ode_dev = NaN.
ode_ok = false
ode_dev = NaN
ode_err = ""
try
    _tout, rhout = timeevolution.master([0.0, TFINAL], rho0, H, [Jop];
                                        abstol = 1e-12, reltol = 1e-12)
    rho_ode = Matrix(rhout[end].data)
    global ode_dev = norm(rho_ode - rho_t)
    global ode_ok = ode_dev < 1e-8
catch err
    global ode_err = string(err)
    println("timeevolution.master cross-check FAILED: ", ode_err)
end

# --- cross-check: analytic closed form (NOT reported) -----------------
# This Liouvillian is exactly solvable: H is diagonal so populations and
# coherences decouple. rho11(t) = rho11(0) e^{-gamma t};
# rho12(t) = rho12(0) e^{-(gamma/2) t} e^{-i t} (omega = 1 from H = 0.5 sigma_z).
rho11_analytic = 0.75 * exp(-GAMMA * TFINAL)
rho12_analytic = 0.25 * exp(-0.5 * GAMMA * TFINAL) * exp(-im * TFINAL)
rho_analytic = ComplexF64[rho11_analytic rho12_analytic;
                          conj(rho12_analytic) 1.0-rho11_analytic]
analytic_dev = norm(rho_analytic - rho_t)
analytic_ok = analytic_dev < 1e-13

# --- human-readable block, 12 significant figures --------------------
sf(x) = @sprintf("%.12g", x)          # %g strips trailing zeros
se(x) = @sprintf("%.11e", x)          # always exactly 12 significant digits
println()
println("--- reported values (12 significant figures) ---")
println("T1 rho_t[0,0]  population      = ", sf(t1_pop), "   [", se(t1_pop), "]")
println("T2 Re(rho_t[0,1]) coherence    = ", sf(t2_coh_re), "   [", se(t2_coh_re), "]")
println("T3 purity Tr(rho^2)            = ", sf(t3_purity), "   [", se(t3_purity), "]")
println("T4 von Neumann S (log2)        = ", sf(t4_vn_entropy_log2), "   [", se(t4_vn_entropy_log2), "]")
println("T5 trace Tr(rho)               = ", sf(t5_trace), "   [", se(t5_trace), "]")
println()
println("--- self-checks ---")
println(@sprintf("C1 trace preserved   : %s   |Tr-1| = %.3e , |Im Tr| = %.3e", c1, c1_trace_dev, c1_imag_trace))
println(@sprintf("C2 Hermitian         : %s   ||rho - rho^dag|| = %.3e", c2, c2_herm_dev))
println(@sprintf("C3 positivity        : %s   min eig = %.12g", c3, c3_min_eig))
println(@sprintf("C4 entropies         : %s   S(rho0) = %s bits , S(rho_t) = %s bits", c4, sf(s_t0), sf(t4_vn_entropy_log2)))
println(@sprintf("   eig(rho0) = [%.12g, %.12g] ; eig(rho_t) = [%.12g, %.12g]", eigs_0[1], eigs_0[2], eigs_t[1], eigs_t[2]))
println()
println("--- cross-checks (not the reported path) ---")
println(@sprintf("hand-built Liouvillian ||dL||          = %.3e", liouvillian_agreement))
println(@sprintf("QuantumOptics master ODE ||drho||      = %.3e  ok=%s", ode_dev, ode_ok))
println(@sprintf("analytic closed form  ||drho||         = %.3e  ok=%s", analytic_dev, analytic_ok))

result = Dict(
    "t1_pop" => t1_pop,
    "t2_coh_re" => t2_coh_re,
    "t3_purity" => t3_purity,
    "t4_vn_entropy_log2" => t4_vn_entropy_log2,
    "t5_trace" => t5_trace,
    "c1" => c1,
    "c2" => c2,
    "c3" => c3,
    "c4" => c4,
    "engine" => "julia",
    "julia_version" => string(VERSION),
    "active_project" => string(Base.active_project()),
    "packages_used" => ["QuantumOptics", "QuantumOpticsBase", "LinearAlgebra", "JSON", "Printf", "Pkg"],
    "gksl_generator_source" => "QuantumOptics.liouvillian",
    "propagator" => "LinearAlgebra.exp of 4x4 vectorised Liouvillian, column stacking",
    "sigfig12" => Dict(
        "t1_pop" => sf(t1_pop),
        "t2_coh_re" => sf(t2_coh_re),
        "t3_purity" => sf(t3_purity),
        "t4_vn_entropy_log2" => sf(t4_vn_entropy_log2),
        "t5_trace" => sf(t5_trace),
        "s_rho0_vn_log2" => sf(s_t0),
    ),
    "sigfig12_sci" => Dict(
        "t1_pop" => se(t1_pop),
        "t2_coh_re" => se(t2_coh_re),
        "t3_purity" => se(t3_purity),
        "t4_vn_entropy_log2" => se(t4_vn_entropy_log2),
        "t5_trace" => se(t5_trace),
        "s_rho0_vn_log2" => se(s_t0),
    ),
    "detail" => Dict(
        "s_rho0_vn_log2" => s_t0,
        "s_rho0_closedform_log2" => s_t0_closedform,
        "c1_trace_dev" => c1_trace_dev,
        "c1_imag_trace" => c1_imag_trace,
        "c2_herm_dev" => c2_herm_dev,
        "c3_min_eig" => c3_min_eig,
        "c4_s0_agreement" => c4_s0_agreement,
        "eig_rho0" => eigs_0,
        "eig_rho_t" => eigs_t,
        # NOTE: JSON.jl serialises a Julia Matrix COLUMN-major (each inner
        # array is a column). rho_t_im is antisymmetric, so a column-major
        # dump reads as the transpose. Emit explicit row-major nesting and
        # named entries so no reader has to guess.
        "rho_t_re_rowmajor" => [[real(rho_t[i, j]) for j in 1:2] for i in 1:2],
        "rho_t_im_rowmajor" => [[imag(rho_t[i, j]) for j in 1:2] for i in 1:2],
        "rho_t_entries" => Dict(
            "r00_re" => real(rho_t[1, 1]), "r00_im" => imag(rho_t[1, 1]),
            "r01_re" => real(rho_t[1, 2]), "r01_im" => imag(rho_t[1, 2]),
            "r10_re" => real(rho_t[2, 1]), "r10_im" => imag(rho_t[2, 1]),
            "r11_re" => real(rho_t[2, 2]), "r11_im" => imag(rho_t[2, 2]),
        ),
        "op_sigma_z_matches_spec" => op_sz_ok,
        "op_sigma_minus_matches_spec" => op_sm_ok,
        "col_stacking_confirmed" => col_stacking_confirmed,
        "conv_res_col" => res_col,
        "conv_res_row" => res_row,
        "handbuilt_liouvillian_dev" => liouvillian_agreement,
        "qo_master_ode_dev" => ode_dev,
        "qo_master_ode_ok" => ode_ok,
        "qo_master_ode_err" => ode_err,
        "analytic_closedform_dev" => analytic_dev,
        "analytic_closedform_ok" => analytic_ok,
        "pkg_versions" => pkgversions,
        "gamma" => GAMMA,
        "t_final" => TFINAL,
    ),
)

open(OUT_JSON, "w") do io
    JSON.print(io, result)
end
println()
println("json written: ", OUT_JSON)
println(JSON.json(result))
