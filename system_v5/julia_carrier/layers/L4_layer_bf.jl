# L4_layer_bf.jl
# ==============================================================================
# GEOMETRY-MANIFOLD LAYER L4 (BF rebuild) -- Hopf fibration S^3 -> S^2, U(1) fiber.
#
#   classification = "L4_layer_bf_poc" ;  promotion_allowed = false.
#
# WHY THIS REBUILD EXISTS (fab-audit finding it answers):
#   The prior L4_layer.jl reported "dependency-forcing HOLDS" because ALL FOUR of its
#   below-geometry erasures (E1 trivialize, E2 cos2eta->0, E3 single-slice, E4 lock fiber)
#   collapse c1 to 0. But it has NO anti-tautology control: there is no operation of
#   comparable magnitude that PERTURBS the section yet LEAVES c1 intact. When every
#   operation you try collapses the signature, "the real erasure collapses it" carries no
#   information -- you cannot tell a measured structural collapse from "any perturbation
#   kills it." The old negative_controls block (L4_layer.jl lines 555-565) only checks more
#   ways to get c1=0 (no_winding, trivial, flat); it never exhibits a survivor. That is the
#   exact cosmetic trap: the collapse is presented as decisive but is not contrasted against
#   a non-collapsing perturbation, so it could be a tautology of "perturb -> die."
#
#   The codex sibling (L4_layer_codex.jl) is the model FOR THE FHS CHERN PART: it measures
#   c1 by the gauge-invariant Fukui-Hatsugai-Suzuki plaquette winding on a real spinor
#   section, and it contrasts m=1 against genuinely different sections (m=0, constant,
#   phase-erased). That part is honest. But its N01/holonomy/fiber pieces are hardcoded
#   analytic closed forms whose "erased" value is literally written `0.0`
#   (horizontal_commutator_gap: trivialized_vertical_phi_gap=0.0; holonomy_readout:
#   trivial_delta_phi=0.0) -- those are NOT measured collapses, they are constants.
#
# WHAT THIS REBUILD DOES:
#   Keep the genuinely measured, gauge-invariant FHS first-Chern signature on a Julia-native
#   spinor section. Add the missing ANTI-TAUTOLOGY NEGATIVE CONTROL: large-amplitude
#   perturbations of the SAME section, of magnitude comparable to (or larger than) the
#   winding's own 2pi phase, that do NOT remove the topological winding. These MUST leave
#   c1=1 intact. The real erasure (winding m: 1 -> 0, which removes the U(1) chi-winding that
#   the cos(2eta) d chi connection content carries) MUST collapse c1 to 0. The signature is
#   load-bearing iff BOTH hold: real erasure collapses AND the anti-tautology controls survive.
#
# THE FOUR GENUINE-DEPENDENCY-FORCING REQUIREMENTS, AND HOW THIS FILE MEETS THEM:
#   (1) POSITIVE: erasing the real below-geometry (the U(1) winding) collapses c1 (measured).
#   (2) ANTI-TAUTOLOGY NEGATIVE: a DIFFERENT operation of comparable magnitude that is NOT
#       the below-geometry erasure (a smooth gauge transform with multi-radian amplitude; a
#       smooth same-class polar deformation) LEAVES c1 intact. Numbers reported.
#   (3) STRUCTURAL: the FHS estimator is a gauge-INVARIANT link product. There is no
#       built-in algebraic zero: the gauge transform mangles every per-plaquette phase by
#       several radians, yet the gauge-invariant global winding is preserved. No operator is
#       a scalar multiple of, nor co-diagonal with, another such that a zero is guaranteed.
#   (4) INPUT-DEPENDENCE: the surviving c1 is NOT a fixed constant -- it equals the winding
#       integer m (m=0->0, 1->1, 2->2, 3->3, -1->-1), measured and reported.
#
# BLOCH DISCIPLINE:
#   Density-operator / spinor-section only. rho = psi psi' (2x2, PSD, trace 1). FHS reads the
#   gauge-invariant overlap dot(v_i, v_j) of normalized spinors. NO r=(rx,ry,rz) Bloch vector,
#   NO dot-r ODE, NO sigma-triple state evolution. (The Hopf projection pi(psi)=psi' sigma psi
#   is used ONLY as a geometric base coordinate for the fiber/base witness, never as a state.)
#
# LOAD-BEARING Z3:
#   c1 measured two independent ways (FHS plaquette winding; symmetric finite-difference Berry
#   curvature surface integral). Z3 derives free ints C_hopf,C_triv open-bracketed by the raw
#   measured reals and must satisfy C_hopf > C_triv. The verdict FLIPS when fed the collapsed
#   (erased) measurements -> the SMT result is coupled to the measured data, not a tautology.
# ==============================================================================

using LinearAlgebra
using Z3
using JSON

const TWO_PI = 2pi
const RESULTS_PATH = joinpath(@__DIR__, "L4_layer_bf_results.json")
const RUN_COMMAND = "julia --project=\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier\" \"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/L4_layer_bf.jl\""

# ------------------------------------------------------------------------------
# 1. CARRIER -- Julia-native C^2 spinor, Hopf chart, spinor-derived density (NO numpy, NO Bloch)
# ------------------------------------------------------------------------------
unit(v::Vector{ComplexF64}) = v / norm(v)

# Hopf chart psi(phi,chi;eta) on S^3 subset C^2.
hopf_chart(phi, chi, eta) = unit(ComplexF64[cis(phi + chi) * cos(eta), cis(phi - chi) * sin(eta)])

# spinor-derived density rho = psi psi' (2x2, PSD, trace 1). Julia-native.
density(psi::Vector{ComplexF64}) = psi * psi'

# Pauli matrices used ONLY for the geometric base coordinate of the fiber/base witness.
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
# Geometric base coordinate (NOT a state vector; never evolved). Real expectation triple.
base_coord(psi) = real.([psi' * SX * psi, psi' * SY * psi, psi' * SZ * psi])

# ------------------------------------------------------------------------------
# 2. SECTIONS over the S^2 base (theta, alpha) -- the carrier's induced line-bundle section
# ------------------------------------------------------------------------------
# Gauge-fixed section of the Hopf line bundle, winding m. m=1 is the genuine Hopf generator.
# theta = polar (from eta), alpha = base azimuth (from the chart's chi-winding). The U(1)
# winding e^{i m alpha} on the lower component is the cos(2 eta) d chi connection content
# made into a section -- removing it (m=0) erases the below-geometry.
hopf_section(theta, alpha; m::Int=1) = unit(ComplexF64[cos(theta / 2), cis(m * alpha) * sin(theta / 2)])

# ------------------------------------------------------------------------------
# 3. FIRST CHERN -- two INDEPENDENT gauge-invariant estimators on the SAME section
# ------------------------------------------------------------------------------
# Estimator A: Fukui-Hatsugai-Suzuki plaquette Chern (gauge-invariant link product).
# Gauge invariance is the structural point: the per-plaquette phase angle(z) is invariant
# under psi -> e^{i g} psi, so there is NO built-in algebraic zero a perturbation can exploit.
function fhs_chern(secfn; ntheta=80, nalpha=80)
    total = 0.0; maxF = 0.0; sumF = 0.0
    for i in 0:ntheta-1
        th0 = pi * i / ntheta; th1 = pi * (i + 1) / ntheta
        for j in 0:nalpha-1
            a0 = TWO_PI * j / nalpha; a1 = TWO_PI * (j + 1) / nalpha
            v1 = secfn(th0, a0); v2 = secfn(th1, a0); v3 = secfn(th1, a1); v4 = secfn(th0, a1)
            z = dot(v1, v2) * dot(v2, v3) * dot(v3, v4) * dot(v4, v1)
            F = angle(z)
            total += F; maxF = max(maxF, abs(F)); sumF += abs(F)
        end
    end
    (c1 = total / TWO_PI, maxF = maxF, sumF = sumF)
end

# Estimator B: symmetric finite-difference Berry curvature surface integral (independent of A).
# F_{theta,alpha} = 2 Im <d_theta psi | d_alpha psi>; c1 = (1/2pi) int_{S^2} F. Both
# derivatives centered. This is a continuous-curvature reading, NOT a link product, so it is
# a genuinely independent estimator of the same integer.
function curvature_point(secfn, th, a; h=1e-5)
    dth = (secfn(th + h, a) - secfn(th - h, a)) / (2h)
    da  = (secfn(th, a + h) - secfn(th, a - h)) / (2h)
    2 * imag(dth' * da)
end
function curvature_chern(secfn; ntheta=200, nalpha=200)
    ths = range(1e-3, pi - 1e-3; length=ntheta)
    as  = range(0, TWO_PI; length=nalpha)
    dth = step(ths); da = step(as)
    tot = 0.0
    for th in ths, a in as
        tot += curvature_point(secfn, th, a) * dth * da
    end
    tot / TWO_PI
end

# ------------------------------------------------------------------------------
# 4. FIBER / BASE SPLIT -- geometric witness on the carrier (density / base-coord only)
# ------------------------------------------------------------------------------
# Fiber = global U(1) phase orbit psi -> e^{it} psi: base coordinate INVARIANT along it.
# In the chart convention psi=(e^{i(phi+chi)}cos eta, e^{i(phi-chi)}sin eta), the GLOBAL
# phase phi is the fiber (both components share it -> base-invariant); the RELATIVE phase
# chi and the amplitude eta are BASE moves (they rotate/raise the point on S^2). So the base
# witness varies chi (not phi). Uses the geometric base coordinate only -- no Bloch state, no r-ODE.
function fiber_base_split(eta)
    psi0 = hopf_chart(0.3, 0.7, eta)
    b0 = base_coord(psi0)
    fiber_moves = [norm(base_coord(cis(t) .* psi0) .- b0) for t in range(0, TWO_PI, length=33)]
    base_moves  = [norm(base_coord(hopf_chart(0.3, 0.7 + dc, eta)) .- b0) for dc in range(0.0, 1.0, length=33)]
    (fiber_invariance = maximum(fiber_moves), base_responsiveness = maximum(base_moves))
end

# ------------------------------------------------------------------------------
# 5. DERIVED QIT readout (never primary): von Neumann entropy of fiber- vs base-averaged rho
# ------------------------------------------------------------------------------
function vn_entropy(rho)
    ev = real.(eigvals(Hermitian((rho + rho') / 2)))
    -sum(e * log(e) for e in ev if e > 1e-12; init = 0.0)
end
function fiber_vs_base_entropy(eta; n=64)
    psi0 = hopf_chart(0.3, 0.7, eta)
    # fiber average (global phase) stays PURE -> S=0; base average (vary relative phase chi) MIXES -> S>0.
    rho_fiber = sum(density(cis(t) .* psi0) for t in range(0, TWO_PI, length=n)) / n
    rho_base  = sum(density(hopf_chart(0.3, 0.7 + TWO_PI*k/n, eta)) for k in 0:n-1) / n
    (S_fiber = vn_entropy(rho_fiber), S_base = vn_entropy(rho_base))
end

# ------------------------------------------------------------------------------
# 6. PEPS3D K=(V,E,F,C) finite anchor (combinatorial only)
# ------------------------------------------------------------------------------
function peps3d_anchor(nphi, nchi, nshell)
    V = nphi * nchi * nshell
    E = nshell * (2 * nphi * nchi)
    F = nshell * (nphi * nchi)
    C = (nshell - 1) * (nphi * nchi)
    (V = V, E = E, F = F, C = C, euler = V - E + F - C)
end

# ------------------------------------------------------------------------------
# 7. LOAD-BEARING Z3 -- c1 gap derived from the two independent estimators, verdict flips
# ------------------------------------------------------------------------------
function meas_bracket(m1::Float64, m2::Float64)
    r1 = round(Int, m1); r2 = round(Int, m2)
    (min(r1, r2) - 1, max(r1, r2) + 1)
end
function gap_forced(hbr::Tuple{Int,Int}, tbr::Tuple{Int,Int})
    ctx = Context()
    Ch = Const("Chopf", IntSort(ctx)); Ct = Const("Ctriv", IntSort(ctx))
    s = Solver(ctx)
    add(s, Ch > IntVal(hbr[1], ctx)); add(s, Ch < IntVal(hbr[2], ctx))
    add(s, Ct > IntVal(tbr[1], ctx)); add(s, Ct < IntVal(tbr[2], ctx))
    add(s, Not(Ch > Ct))
    string(check(s))
end

# ==============================================================================
#                                   RUN
# ==============================================================================
results = Dict{String,Any}()
results["layer"] = "L4"
results["object"] = "hopf_fibration_S3_to_S2_U1_fiber"
results["classification"] = "L4_layer_bf_poc"
results["promotion_allowed"] = false
results["run_command"] = RUN_COMMAND
results["bloch_free"] = "density/spinor-section only: rho=psi*psi', FHS uses gauge-invariant overlaps; base_coord is a geometric coordinate, never an evolved state; no r-vector, no dot-r ODE"
results["finite_map"] = Dict(
    "domain"   => "S^3={psi in C^2:||psi||=1}, Hopf chart psi(phi,chi;eta)",
    "codomain" => "S^2 base (theta,alpha); U(1) line bundle, first Chern c1 via gauge-invariant FHS + curvature integral",
)

# ----- carrier sanity (Julia-native spinor, density PSD/trace1/pure) ----------
psi_t = hopf_chart(0.3, 0.7, pi/5)
rho_t = density(psi_t)
ev    = real.(eigvals(Hermitian((rho_t + rho_t')/2)))
results["carrier"] = Dict(
    "on_S3_norm_dev" => abs(norm(psi_t) - 1),
    "rho_trace"      => real(tr(rho_t)),
    "rho_is_psd"     => minimum(ev) > -1e-12,
    "rho_is_pure"    => abs(real(tr(rho_t*rho_t)) - 1) < 1e-10,
    "julia_native"   => true,
    "uses_numpy"     => false,
)

# ======================================================================
# 8. POSITIVE: genuine Hopf bundle signature (winding m=1) -- MEASURED c1
# ======================================================================
fh_hopf  = fhs_chern((th,a)->hopf_section(th,a; m=1))
cv_hopf  = curvature_chern((th,a)->hopf_section(th,a; m=1))
fb_hopf  = fiber_base_split(pi/5)
ent_hopf = fiber_vs_base_entropy(pi/5)
c1_hopf  = round(Int, fh_hopf.c1)

results["positive_hopf_signature"] = Dict(
    "c1_fhs_plaquette"     => round(fh_hopf.c1, digits=6),
    "c1_curvature_integral"=> round(cv_hopf, digits=6),
    "c1_integer"           => c1_hopf,
    "two_estimators_agree" => round(Int, fh_hopf.c1) == round(Int, cv_hopf),
    "sumF_total_flux"      => round(fh_hopf.sumF, digits=4),
    "maxF_plaquette"       => round(fh_hopf.maxF, digits=6),
    "curvature_nonzero"    => fh_hopf.sumF > 1e-2,
    "fiber_invariance"     => round(fb_hopf.fiber_invariance, digits=9),
    "base_responsiveness"  => round(fb_hopf.base_responsiveness, digits=6),
    "S_fiber_pure"         => round(ent_hopf.S_fiber, digits=9),
    "S_base_mixed"         => round(ent_hopf.S_base, digits=6),
)

# ======================================================================
# 9. INPUT-DEPENDENCE (req 4): the surviving signature is NOT a fixed constant.
#     c1 tracks the winding integer m. If c1 were a hardcoded 1 this would fail.
# ======================================================================
input_dep = Dict{String,Any}()
m_grid = (-1, 0, 1, 2, 3)
input_dep_pass = true
for m in m_grid
    r = fhs_chern((th,a)->hopf_section(th,a; m=m))
    input_dep["m_$(m)"] = round(r.c1, digits=6)
    (abs(r.c1 - m) < 0.05) || (global input_dep_pass = false)
end
results["input_dependence"] = Dict(
    "c1_vs_winding_m" => input_dep,
    "c1_equals_m"     => input_dep_pass,
    "note"            => "c1 = winding m for every m tested; the surviving signature varies with input, it is not a fixed constant.",
)

# ======================================================================
# 10. POSITIVE ERASURE (req 1): remove the REAL below-geometry (the U(1) winding).
#      winding m: 1 -> 0 removes the chi-winding that the cos(2 eta) d chi connection
#      content carries. c1 MUST collapse 1 -> 0. Measured on the SAME FHS estimator.
# ======================================================================
fh_erased = fhs_chern((th,a)->hopf_section(th,a; m=0))
cv_erased = curvature_chern((th,a)->hopf_section(th,a; m=0))
erasure_collapsed = abs(fh_erased.c1) < 0.05 && abs(cv_erased) < 0.05
results["positive_erasure_real_below_geometry"] = Dict(
    "operation"        => "winding m: 1 -> 0 (remove the U(1) winding = the cos(2eta) d chi connection content)",
    "c1_fhs_after"     => round(fh_erased.c1, digits=6),
    "c1_curvature_after"=> round(cv_erased, digits=6),
    "c1_before"        => round(fh_hopf.c1, digits=6),
    "delta_c1"         => round(abs(fh_hopf.c1) - abs(fh_erased.c1), digits=6),
    "signature_collapsed" => erasure_collapsed,
    "note" => "erasing the actual below-geometry (the winding) collapses c1 1->0 on BOTH estimators. This is the measured POSITIVE collapse.",
)

# ======================================================================
# 11. ANTI-TAUTOLOGY NEGATIVE CONTROL (req 2 + 3): operations of COMPARABLE MAGNITUDE
#      that are NOT the below-geometry erasure must LEAVE c1 intact.
#      If they collapsed it too, the collapse in (10) would be a tautology of "perturb->die".
# ======================================================================

# CONTROL A: large-amplitude smooth GAUGE transform psi -> e^{i g(theta,alpha)} psi.
# c1 is gauge-invariant => MUST stay 1. The gauge phase amplitude is multi-radian
# (comparable to / larger than the winding's own 2pi phase budget), so this is NOT a
# small perturbation -- it mangles every per-plaquette local phase yet preserves the
# gauge-invariant global winding. STRUCTURAL: this is exactly why the FHS estimator has
# no built-in algebraic zero a perturbation could trip.
gauge_fn(th, a) = 3.7*sin(2a) + 2.9*cos(th) + 1.3*sin(th + a)
gauged_section(th, a) = cis(gauge_fn(th, a)) * hopf_section(th, a; m=1)
gauge_amp = maximum(abs(gauge_fn(th, a)) for th in range(0, pi, length=40) for a in range(0, TWO_PI, length=40))
fh_gauge = fhs_chern(gauged_section)
cv_gauge = curvature_chern(gauged_section)
ctrlA_survives = abs(fh_gauge.c1 - 1) < 0.05 && abs(cv_gauge - 1) < 0.2

# CONTROL B: smooth same-class POLAR deformation (bend the theta profile, keep winding m=1).
# Comparable magnitude (theta is shifted by up to ~0.4 rad across the sphere), same bundle
# class => c1 MUST stay 1.
deform_section(th, a) = let s = 0.5*(th + 0.4*sin(th)); unit(ComplexF64[cos(s), cis(1*a)*sin(s)]) end
deform_amp = maximum(abs(0.4*sin(th)) for th in range(0, pi, length=40))
fh_deform = fhs_chern(deform_section)
cv_deform = curvature_chern(deform_section)
ctrlB_survives = abs(fh_deform.c1 - 1) < 0.05 && abs(cv_deform - 1) < 0.2

anti_taut_pass = ctrlA_survives && ctrlB_survives
results["anti_tautology_negative_control"] = Dict(
    "control_A_gauge_transform" => Dict(
        "operation"        => "psi -> e^{i g(theta,alpha)} psi, g large-amplitude smooth periodic",
        "gauge_phase_amplitude_rad" => round(gauge_amp, digits=4),
        "comparable_to_winding_2pi" => gauge_amp > TWO_PI*0.8,
        "c1_fhs_after"     => round(fh_gauge.c1, digits=6),
        "c1_curvature_after"=> round(cv_gauge, digits=6),
        "signature_survives"=> ctrlA_survives,
    ),
    "control_B_polar_deformation" => Dict(
        "operation"        => "theta -> theta + 0.4 sin(theta) (smooth same-class bend), keep winding m=1",
        "deformation_amplitude_rad" => round(deform_amp, digits=4),
        "c1_fhs_after"     => round(fh_deform.c1, digits=6),
        "c1_curvature_after"=> round(cv_deform, digits=6),
        "signature_survives"=> ctrlB_survives,
    ),
    "both_controls_leave_signature_intact" => anti_taut_pass,
    "verdict" => anti_taut_pass ?
        "ANTI-TAUTOLOGY HOLDS: two comparable-magnitude operations that are NOT the below-geometry erasure leave c1=1 intact, while the real erasure (winding->0) collapses it to 0. The collapse is SPECIFIC, not a tautology of 'any perturbation dies'." :
        "ANTI-TAUTOLOGY FAILS: a non-below-geometry perturbation also collapsed c1 -- the collapse in section 10 may be a tautology.",
)

# Decisive comparison: real erasure collapses AND anti-taut controls survive.
results["dependency_forcing_decisive"] = Dict(
    "real_erasure_collapses_c1"        => erasure_collapsed,
    "anti_taut_controls_keep_c1"       => anti_taut_pass,
    "c1_real_erasure"                  => round(fh_erased.c1, digits=4),
    "c1_anti_taut_gauge"               => round(fh_gauge.c1, digits=4),
    "c1_anti_taut_deform"              => round(fh_deform.c1, digits=4),
    "dependency_forcing_genuine"       => erasure_collapsed && anti_taut_pass,
    "note" => "GENUINE iff the real below-geometry erasure collapses the signature WHILE a comparable-magnitude non-erasure leaves it intact. Both measured numbers reported.",
)

# ======================================================================
# 12. LOAD-BEARING Z3 -- gap derived from two independent estimators; verdict flips on collapse
# ======================================================================
hbr = meas_bracket(fh_hopf.c1, cv_hopf)        # genuine ~ (0,2) -> C_hopf=1
tbr = meas_bracket(fh_erased.c1, cv_erased)    # erased  ~ (-1,1) -> C_triv=0
z3_genuine = gap_forced(hbr, tbr)                                       # expect unsat
z3_brokenH = gap_forced(meas_bracket(fh_erased.c1, cv_erased), tbr)    # genuine slot fed erased -> sat
z3_brokenT = gap_forced(hbr, meas_bracket(fh_hopf.c1, cv_hopf))        # erased slot fed genuine -> sat
z3_load_bearing = (z3_genuine == "unsat" && z3_brokenH == "sat" && z3_brokenT == "sat")
results["z3_load_bearing"] = Dict(
    "claim"          => "free ints C_hopf,C_triv DERIVED from 2 independent c1 estimators satisfy C_hopf>C_triv",
    "hopf_bracket"   => [hbr[1], hbr[2]],
    "triv_bracket"   => [tbr[1], tbr[2]],
    "genuine_unsat"  => z3_genuine,
    "broken_hopf_to_triv_sat" => z3_brokenH,
    "broken_triv_to_hopf_sat" => z3_brokenT,
    "verdict_flips"  => z3_load_bearing,
    "is_load_bearing"=> z3_load_bearing,
)

# ======================================================================
# 13. SCALE LADDER 8/16/32/64 -- c1 quantized; per-grid info (sumF, peps3d) changes
# ======================================================================
scale_rows = Dict{String,Any}()
for n in (8, 16, 32, 64)
    fh = fhs_chern((th,a)->hopf_section(th,a; m=1); ntheta=n, nalpha=2n)
    pa = peps3d_anchor(n, n, 4)
    scale_rows["grid_$(n)"] = Dict(
        "ntheta" => n, "nalpha" => 2n,
        "c1" => round(fh.c1, digits=4),
        "c1_quantized" => abs(round(fh.c1) - 1) < 0.05,
        "sumF" => round(fh.sumF, digits=4),
        "maxF" => round(fh.maxF, digits=6),
        "peps3d_V" => pa.V, "peps3d_E" => pa.E, "peps3d_F" => pa.F, "peps3d_C" => pa.C,
    )
end
results["scale_8_16_32_64"] = scale_rows
scale_ok = all(scale_rows["grid_$n"]["c1_quantized"] for n in (8,16,32,64))

# ----- tool manifest -----------------------------------------------------------
results["tool_manifest"] = Dict(
    "LinearAlgebra" => Dict("role" => "load_bearing", "use" => "norms/overlaps/eigvals for FHS link products, curvature integral, density spectra"),
    "Z3"            => Dict("role" => "load_bearing", "use" => "free-int c1 gap C_hopf>C_triv from 2 independent estimators; verdict flips on collapsed input"),
    "JSON"          => Dict("role" => "io", "use" => "receipt emission"),
    "numpy"         => Dict("role" => "ABSENT", "use" => "Julia-native; no numpy"),
)
results["tool_integration_depth"] = Dict("LinearAlgebra" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive")

results["blocked_consumers"] = [
    "layer completion", "parent-complete L4", "stacking readiness",
    "L5 nested Hopf tori", "L6 connection/holonomy admission",
    "Xi", "Phi0", "Axis0", "flux", "FEP", "physics/gravity bridge",
]
results["promotion_note"] = "promotion_allowed=false; L4_layer_bf_poc; bounded Julia PoC; not canonical; order/stacking gated behind parent-complete + realness gate."

# ======================================================================
# 14. HONEST PASS LADDER
# ======================================================================
carrier_ok = results["carrier"]["on_S3_norm_dev"] < 1e-10 &&
             abs(results["carrier"]["rho_trace"] - 1) < 1e-10 &&
             results["carrier"]["rho_is_psd"] && results["carrier"]["rho_is_pure"]
positive_ok = abs(fh_hopf.c1 - 1) < 0.05 && fh_hopf.sumF > 1e-2 &&
              (round(Int, fh_hopf.c1) == round(Int, cv_hopf))
input_ok = input_dep_pass
erasure_ok = erasure_collapsed
anti_taut_ok = anti_taut_pass
split_ok = fb_hopf.fiber_invariance < 1e-9 && fb_hopf.base_responsiveness > 1e-3
entropy_ok = ent_hopf.S_fiber < 1e-6 && ent_hopf.S_base > 1e-3
z3_ok = z3_load_bearing
# THE decisive genuine-dependency-forcing gate: collapse AND survive.
dependency_forcing_genuine = erasure_ok && anti_taut_ok

all_pass = carrier_ok && positive_ok && input_ok && erasure_ok && anti_taut_ok &&
           split_ok && entropy_ok && z3_ok && scale_ok && dependency_forcing_genuine

results["controls_summary"] = Dict(
    "carrier_ok"                 => carrier_ok,
    "positive_c1_ok"             => positive_ok,
    "input_dependence_ok"        => input_ok,
    "real_erasure_collapses_ok"  => erasure_ok,
    "anti_tautology_survives_ok" => anti_taut_ok,
    "fiber_base_split_ok"        => split_ok,
    "derived_entropy_ok"         => entropy_ok,
    "z3_load_bearing_ok"         => z3_ok,
    "scale_8_16_32_64_ok"        => scale_ok,
    "dependency_forcing_genuine" => dependency_forcing_genuine,
)
results["all_pass"] = all_pass
results["honest_status"] = all_pass ?
    "genuine_now : L4 Hopf c1=1 (two independent estimators) MEASURED on a Julia-native spinor section; real below-geometry erasure (winding->0) collapses c1 to 0 WHILE two comparable-magnitude non-erasure controls (multi-radian gauge transform, smooth polar deformation) leave c1=1 intact; c1 tracks winding m (input-dependent, not constant); z3 verdict flips on collapsed input. Anti-tautology control present with numbers. Bloch-free." :
    "still_partial : see controls_summary -- in particular dependency_forcing_genuine names whether the real erasure collapsed AND the anti-tautology controls survived."

# ======================================================================
# PRINT
# ======================================================================
println("================ L4 LAYER (BF rebuild) : Hopf S^3 -> S^2 U(1) ================")
println("carrier        : on_S3=", round(results["carrier"]["on_S3_norm_dev"],sigdigits=3),
        "  pure=", results["carrier"]["rho_is_pure"], "  PSD=", results["carrier"]["rho_is_psd"])
println("POSITIVE c1    : FHS=", round(fh_hopf.c1,digits=5), "  curvature=", round(cv_hopf,digits=5),
        "  sumF=", round(fh_hopf.sumF,digits=4), "  (two estimators agree=", positive_ok, ")")
println("INPUT-DEP c1=m : ", join(["m=$m->$(input_dep["m_$m"])" for m in m_grid], "  "), "   (c1 varies with input=", input_ok, ")")
println("------ DEPENDENCY-FORCING : collapse the real below-geometry ------")
println("  REAL ERASURE (winding 1->0)        : c1 ", round(fh_hopf.c1,digits=3), " -> ", round(fh_erased.c1,digits=3),
        "   collapsed=", erasure_collapsed)
println("------ ANTI-TAUTOLOGY : comparable-magnitude NON-erasure must SURVIVE ------")
println("  CTRL A gauge xform (amp=", round(gauge_amp,digits=2), " rad) : c1 -> ", round(fh_gauge.c1,digits=4),
        "   survives=", ctrlA_survives)
println("  CTRL B polar deform (amp=", round(deform_amp,digits=2), " rad): c1 -> ", round(fh_deform.c1,digits=4),
        "   survives=", ctrlB_survives)
println("  ==> dependency_forcing_genuine = ", dependency_forcing_genuine,
        "  (real erasure collapses AND non-erasure survives)")
println("------ fiber/base split + derived entropy ------")
println("  fiber_inv=", round(fb_hopf.fiber_invariance,sigdigits=3), "  base_resp=", round(fb_hopf.base_responsiveness,digits=4),
        "   S_fiber=", round(ent_hopf.S_fiber,sigdigits=3), "  S_base=", round(ent_hopf.S_base,digits=4))
println("------ z3 load-bearing ------")
println("  genuine=", z3_genuine, "  brokenH=", z3_brokenH, "  brokenT=", z3_brokenT,
        "  => load_bearing=", z3_load_bearing)
println("------ scale 8/16/32/64 ------")
for n in (8,16,32,64)
    r = scale_rows["grid_$n"]
    println("  grid=", rpad(n,3), " c1=", rpad(r["c1"],8), " quantized=", r["c1_quantized"],
            "  sumF=", rpad(r["sumF"],9), " peps3d(V,E,F,C)=(", r["peps3d_V"],",",r["peps3d_E"],",",r["peps3d_F"],",",r["peps3d_C"],")")
end
println("===========================================================================")
for (k,v) in sort(collect(results["controls_summary"]); by=first)
    println("  ", rpad(k,30), v ? "PASS" : "FAIL")
end
println("ALL_PASS = ", all_pass)
println("STATUS   : ", results["honest_status"])

open(RESULTS_PATH, "w") do io
    JSON.print(io, results, 2)
end
println("wrote ", RESULTS_PATH)
exit(all_pass ? 0 : 1)
