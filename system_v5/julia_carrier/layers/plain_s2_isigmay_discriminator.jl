# =============================================================================
# plain_s2_isigmay_discriminator.jl
# -----------------------------------------------------------------------------
# object_id         = plain_s2_isigmay_discriminator
# classification    = discriminator_probe
# promotion_allowed = false
#
# PRE-REGISTERED SETTLEMENT TEST (controller-set bar):
#   The contested thread: is w_L=-w_R with collapsing controls nesting-specific
#   (genuine layer discriminator) or by-construction (iσ_y charge-conjugation
#   forces w_L=-w_R for ANY section, nested or not)?
#
#   Test: build a PLAIN-S^2 section pair (L and R) that carries the SAME
#   iσ_y·conj(psi_L) charge-conjugation the reauthor uses, on the PLAIN base
#   n(eta,t) = (sin(eta)cos(t), sin(eta)sin(t), cos(eta)) — NO Hopf, NO nesting.
#   Run the SAME two controls the nested cocycle uses on this plain-S^2 pair,
#   over the reauthor's exact per-rung eta-extents.
#
# DECISION RULE (pre-registered):
#   SIGN-BY-CONSTRUCTION if the plain-S^2 iσ_y pair ALSO shows w_L=-w_R AND
#   its glued/decoupled controls ALSO collapse to ~0.
#   SIGN-NESTING-SPECIFIC if the plain-S^2 iσ_y pair does NOT reproduce the
#   opposite-sign + control-collapse pattern (nested version has something the
#   plain sphere lacks).
#
# RATIONALE:
#   The reauthor's iσ_y charge-conjugation maps u -> (iσ_y) conj(u). On a plain
#   sphere section u(n) the eigen-spinor satisfies n.σ u = -|n| u. The charge-
#   conjugated partner satisfies n.σ (iσ_y conj(u)) = +|n| (iσ_y conj(u)) — it
#   is the OPPOSITE-eigenvalue eigen-spinor. So (L,R) are the two branches of
#   n.σ. Their Berry curvatures are equal in magnitude and opposite in sign by
#   the C-symmetry of the Bloch Hamiltonian — for ANY section on ANY sphere where
#   iσ_y conj maps one band to the other.
#
#   That means: if the sign-opposition is purely forced by iσ_y conj, then a
#   PLAIN sphere section + the SAME iσ_y conj lift should ALSO give w_L=-w_R.
#   And if the Wilson plaquette flux formula is symmetric under the same
#   conjugation, both controls should collapse to ~0 for the same reason as on
#   the nested section (the glued section has no curvature regardless; the
#   decoupled section's overlap phases cancel by the same gauge argument).
#
# ROOT CONSTRAINTS: F01 (finite domain/codomain) + N01 (order-sensitive control).
# Tools: LinearAlgebra (load-bearing: eigen/Wilson phases), JSON (supportive).
# =============================================================================

using LinearAlgebra
import JSON

const OBJECT_ID      = "plain_s2_isigmay_discriminator"
const CLASSIFICATION = "discriminator_probe"
const OUT = "/tmp/plain_s2_isigmay_discriminator_results.json"

# ---------------------------------------------------------------------------
# Pauli matrices (plain notation; no gamma5 / Weyl basis needed for S^2)
# ---------------------------------------------------------------------------
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

# PLAIN S^2 base point — geographic parametrization (same as the pre-registered
# test: n(eta,t) = (sin eta cos t, sin eta sin t, cos eta)).
# eta in (0,pi) is the polar angle from the north pole; t in [0,2pi) is azimuth.
plain_n(eta, t) = [sin(eta)*cos(t), sin(eta)*sin(t), cos(eta)]

# Lower eigen-spinor of n.sigma (the -|n| branch = psi_L carrier).
# This is the Berry-phase-carrying section of the Hopf bundle over S^2.
function lower_eigspinor(n::Vector{Float64})
    H = n[1]*SX + n[2]*SY + n[3]*SZ
    e = eigen(Hermitian(H))
    return ComplexF64.(e.vectors[:, 1])   # lower eigenvalue column
end

# iσ_y charge conjugation (SAME as the reauthor): C(u) = (iSY) * conj(u).
# Maps lower band -> upper band on the plain sphere (by C-symmetry of n.sigma).
charge_conj(u::Vector{ComplexF64}) = (im * SY) * conj(u)

# Plain-S^2 section: L = lower eigen-spinor, R = iσ_y conj(L).
# Both normalized to 1 (they already are, by construction of eigen).
function plain_section(eta, t, chi::Symbol)
    n = plain_n(eta, t)
    u = lower_eigspinor(n)
    return chi == :L ? u : charge_conj(u)
end

# ---------------------------------------------------------------------------
# CONTROL (C1): GLUED / PRODUCT section — exact tensor product of an eta-only
# qubit and a t-only qubit. No mixed curvature by construction.
# Same spirit as the reauthor's glued control.
# ---------------------------------------------------------------------------
qeta_glued(eta) = ComplexF64[cos(eta/2), sin(eta/2)]
qt_glued(t)     = ComplexF64[cos(t/2), sin(t/2)*cis(t)]

function plain_glued(eta, t, chi::Symbol)
    u = kron(qeta_glued(eta), qt_glued(t))   # C^4; we take the 2-component slice
    idx = chi == :L ? [1,2] : [3,4]
    v = u[idx]
    n = norm(v)
    return n < 1e-14 ? ComplexF64[1.0, 0.0] : v / n
end

# ---------------------------------------------------------------------------
# CONTROL (C2): ETA-DECOUPLED — freeze eta inside the spinor at eta0=pi/4.
# The spinor ignores eta entirely; the plaquette's eta-leg overlaps are trivial.
# ---------------------------------------------------------------------------
function plain_decoupled(eta, t, chi::Symbol; eta0=pi/4)
    return plain_section(eta0, t, chi)
end

# ---------------------------------------------------------------------------
# FHS Wilson-plaquette mixed winding (same algorithm as the reauthor).
# For chirality chi, sum plaquette flux over (eta-step x t-step) rectangles
# closed in t. Returns (1/2pi) * total_flux.
# ---------------------------------------------------------------------------
function link(psi_a::Vector{ComplexF64}, psi_b::Vector{ComplexF64})
    z = dot(psi_a, psi_b)
    az = abs(z)
    return az < 1e-14 ? ComplexF64(1.0) : z / az
end

function mixed_winding(section_fn, eta_lo, eta_hi, chi::Symbol; nt::Int=240)
    total = 0.0
    for j in 0:nt-1
        t0 = 2pi * j / nt
        t1 = 2pi * (j + 1) / nt
        p11 = section_fn(eta_lo, t0, chi)
        p12 = section_fn(eta_lo, t1, chi)
        p22 = section_fn(eta_hi, t1, chi)
        p21 = section_fn(eta_hi, t0, chi)
        U1 = link(p11, p12)
        U2 = link(p12, p22)
        U3 = link(p22, p21)
        U4 = link(p21, p11)
        total += angle(U1 * U2 * U3 * U4)
    end
    return total / (2pi)
end

function ladder_winding(section_fn, etas::Vector{Float64}, chi::Symbol; nt=240)
    [mixed_winding(section_fn, etas[k], etas[k+1], chi; nt=nt) for k in 1:length(etas)-1]
end

# ---------------------------------------------------------------------------
# ETA BANDS — reauthor's exact per-rung extents
#   Band A: eta in [pi/8, 3pi/8], 8-shell ladder
#   Band B: eta in [0.05, 1.5],   8-shell ladder
# NOTE: plain-S^2 parametrization has n(0,t) = north pole for ALL t, so the
# eta=0 boundary is a coordinate singularity. Band B starts at 0.05 (finite),
# which avoids the degenerate north-pole locus. Band A is entirely interior.
# ---------------------------------------------------------------------------
band_A = collect(range(pi/8, 3pi/8, length=8))
band_B = collect(range(0.05, 1.5, length=8))

println("="^72)
println("plain_s2_isigmay_discriminator")
println("Pre-registered settlement: SIGN-BY-CONSTRUCTION vs SIGN-NESTING-SPECIFIC")
println("="^72)

# Plain S^2 iσ_y pair
wL_A_plain = ladder_winding(plain_section, band_A, :L)
wR_A_plain = ladder_winding(plain_section, band_A, :R)
wL_B_plain = ladder_winding(plain_section, band_B, :L)
wR_B_plain = ladder_winding(plain_section, band_B, :R)

# Glued control (plain sphere)
wL_A_glued = ladder_winding(plain_glued, band_A, :L)
wR_A_glued = ladder_winding(plain_glued, band_A, :R)
wL_B_glued = ladder_winding(plain_glued, band_B, :L)
wR_B_glued = ladder_winding(plain_glued, band_B, :R)

# Decoupled control (plain sphere)
wL_A_decpl = ladder_winding(plain_decoupled, band_A, :L)
wR_A_decpl = ladder_winding(plain_decoupled, band_A, :R)
wL_B_decpl = ladder_winding(plain_decoupled, band_B, :L)
wR_B_decpl = ladder_winding(plain_decoupled, band_B, :R)

# Report per rung
println("\n[Band A  eta in [pi/8, 3pi/8], 8 shells]")
println("  PLAIN S^2 iσ_y pair:")
for k in 1:length(wL_A_plain)
    println("    rung $k: w_L=", round(wL_A_plain[k], digits=6),
            "  w_R=", round(wR_A_plain[k], digits=6),
            "  w_L+w_R=", round(wL_A_plain[k]+wR_A_plain[k], sigdigits=3))
end
println("  GLUED control:")
for k in 1:length(wL_A_glued)
    println("    rung $k: w_L=", round(wL_A_glued[k], sigdigits=3),
            "  w_R=", round(wR_A_glued[k], sigdigits=3))
end
println("  DECOUPLED control:")
for k in 1:length(wL_A_decpl)
    println("    rung $k: w_L=", round(wL_A_decpl[k], sigdigits=3),
            "  w_R=", round(wR_A_decpl[k], sigdigits=3))
end

println("\n[Band B  eta in [0.05, 1.5], 8 shells]")
println("  PLAIN S^2 iσ_y pair:")
for k in 1:length(wL_B_plain)
    println("    rung $k: w_L=", round(wL_B_plain[k], digits=6),
            "  w_R=", round(wR_B_plain[k], digits=6),
            "  w_L+w_R=", round(wL_B_plain[k]+wR_B_plain[k], sigdigits=3))
end
println("  GLUED control:")
for k in 1:length(wL_B_glued)
    println("    rung $k: w_L=", round(wL_B_glued[k], sigdigits=3),
            "  w_R=", round(wR_B_glued[k], sigdigits=3))
end
println("  DECOUPLED control:")
for k in 1:length(wL_B_decpl)
    println("    rung $k: w_L=", round(wL_B_decpl[k], sigdigits=3),
            "  w_R=", round(wR_B_decpl[k], sigdigits=3))
end

# ---------------------------------------------------------------------------
# Verdict booleans (pre-registered decision rule)
# ---------------------------------------------------------------------------
ctrl_tol = 1e-6

# Plain S^2 iσ_y: do w_L and w_R oppose on EVERY rung?
plain_A_opp = all(sign(wL_A_plain[k]) != sign(wR_A_plain[k]) && abs(wL_A_plain[k]) > ctrl_tol
                  for k in 1:length(wL_A_plain))
plain_B_opp = all(sign(wL_B_plain[k]) != sign(wR_B_plain[k]) && abs(wL_B_plain[k]) > ctrl_tol
                  for k in 1:length(wL_B_plain))

# Antisymmetry: max |w_L + w_R| over all rungs
antisym_A = maximum(abs(wL_A_plain[k] + wR_A_plain[k]) for k in 1:length(wL_A_plain))
antisym_B = maximum(abs(wL_B_plain[k] + wR_B_plain[k]) for k in 1:length(wL_B_plain))

# Glued control collapses?
glued_A_collapses = all(abs(wL_A_glued[k]) < ctrl_tol && abs(wR_A_glued[k]) < ctrl_tol
                        for k in 1:length(wL_A_glued))
glued_B_collapses = all(abs(wL_B_glued[k]) < ctrl_tol && abs(wR_B_glued[k]) < ctrl_tol
                        for k in 1:length(wL_B_glued))

# Decoupled control collapses?
decpl_A_collapses = all(abs(wL_A_decpl[k]) < ctrl_tol && abs(wR_A_decpl[k]) < ctrl_tol
                        for k in 1:length(wL_A_decpl))
decpl_B_collapses = all(abs(wL_B_decpl[k]) < ctrl_tol && abs(wR_B_decpl[k]) < ctrl_tol
                        for k in 1:length(wL_B_decpl))

# SIGN-BY-CONSTRUCTION: plain sphere reproduces BOTH opposite-sign AND control-collapse
sign_by_construction = (plain_A_opp && plain_B_opp &&
                        glued_A_collapses && glued_B_collapses &&
                        decpl_A_collapses && decpl_B_collapses)

# SIGN-NESTING-SPECIFIC: plain sphere does NOT reproduce the full pattern
sign_nesting_specific = !sign_by_construction

# Representative scalar values for the top-level summary
w_L_rep = wL_A_plain[4]    # median rung of band A
w_R_rep = wR_A_plain[4]
glued_max_A = maximum(max(abs(wL_A_glued[k]), abs(wR_A_glued[k])) for k in 1:length(wL_A_glued))
decpl_max_A = maximum(max(abs(wL_A_decpl[k]), abs(wR_A_decpl[k])) for k in 1:length(wL_A_decpl))

println("\n" * "="^72)
println("VERDICT BOOLEANS:")
println("  plain-S^2 w_L opposes w_R (band A, all rungs):  ", plain_A_opp)
println("  plain-S^2 w_L opposes w_R (band B, all rungs):  ", plain_B_opp)
println("  max |w_L+w_R| band A: ", round(antisym_A, sigdigits=3),
        "  band B: ", round(antisym_B, sigdigits=3))
println("  glued control collapses (band A): ", glued_A_collapses)
println("  glued control collapses (band B): ", glued_B_collapses)
println("  decoupled control collapses (band A): ", decpl_A_collapses)
println("  decoupled control collapses (band B): ", decpl_B_collapses)
println()
println("  SIGN-BY-CONSTRUCTION : ", sign_by_construction)
println("  SIGN-NESTING-SPECIFIC: ", sign_nesting_specific)
println()
if sign_by_construction
    println("  -> Plain sphere + iσ_y conj reproduces w_L=-w_R AND control-collapse.")
    println("     The 'nested-not-glued' cocycle signature is BY-CONSTRUCTION from")
    println("     the charge-conjugation alone; NO genuine nesting discriminator survives.")
else
    println("  -> Plain sphere + iσ_y conj does NOT reproduce the full pattern.")
    println("     Something about nesting (Hopf fiber phase, eta<->torus mixing) is")
    println("     required; the sign-opposition is not purely forced by iσ_y.")
end
println("="^72)

# ---------------------------------------------------------------------------
# Write result JSON
# ---------------------------------------------------------------------------
results = Dict{String,Any}(
    "object_id"         => OBJECT_ID,
    "classification"    => CLASSIFICATION,
    "promotion_allowed" => false,
    "domain" => "finite shell set {eta_1<...<eta_8} on bands A=[pi/8,3pi/8] and B=[0.05,1.5]; plain-S^2 base n(eta,t)=(sin(eta)cos(t),sin(eta)sin(t),cos(eta)); 240-step torus grid; 2-component spinor (NOT Hopf; NOT nested).",
    "codomain" => "signed mixed Wilson-plaquette winding w_L, w_R per rung per band; glued-control max |w|; decoupled-control max |w|; verdict: SIGN-BY-CONSTRUCTION vs SIGN-NESTING-SPECIFIC.",
    "finite_map" => "(plain-S^2 eta-shell ladder, lower-eigen-spinor section + iσ_y charge-conj) |-> (w_L, w_R) per rung + (glued-control, decoupled-control) |w| per rung; decision: does iσ_y alone force the nested-cocycle signature?",
    "root_constraints" => [
        "F01: finite shell ladder (8 rungs per band); finite torus grid (240 steps); 2-component spinor section.",
        "N01: the pre-registered question is whether [eta-transport, torus-transport] commute on a PLAIN sphere. The discriminator measures whether nonzero mixed curvature is nesting-specific."
    ],
    "section_description" => "PLAIN S^2 only. No Hopf fibration, no nested tori, no S^3 embedding. Base n(eta,t)=(sin(eta)cos(t), sin(eta)sin(t), cos(eta)). L = lower eigen-spinor of n.sigma. R = iσ_y conj(L) = upper eigen-spinor (charge-conjugate partner). SAME iσ_y conj as the reauthor. SAME two controls as the reauthor.",
    "band_A" => Dict(
        "eta_range" => [pi/8, 3pi/8],
        "n_shells" => 8,
        "plain_wL_per_rung" => wL_A_plain,
        "plain_wR_per_rung" => wR_A_plain,
        "glued_max_abs_w" => glued_max_A,
        "decpl_max_abs_w" => decpl_max_A,
        "glued_wL_per_rung" => wL_A_glued,
        "glued_wR_per_rung" => wR_A_glued,
        "decpl_wL_per_rung" => wL_A_decpl,
        "decpl_wR_per_rung" => wR_A_decpl,
        "opposite_sign_all_rungs" => plain_A_opp,
        "max_antisym_wL_plus_wR" => antisym_A,
        "glued_collapses" => glued_A_collapses,
        "decpl_collapses" => decpl_A_collapses,
    ),
    "band_B" => Dict(
        "eta_range" => [0.05, 1.5],
        "n_shells" => 8,
        "plain_wL_per_rung" => wL_B_plain,
        "plain_wR_per_rung" => wR_B_plain,
        "glued_wL_per_rung" => wL_B_glued,
        "glued_wR_per_rung" => wR_B_glued,
        "decpl_wL_per_rung" => wL_B_decpl,
        "decpl_wR_per_rung" => wR_B_decpl,
        "opposite_sign_all_rungs" => plain_B_opp,
        "max_antisym_wL_plus_wR" => antisym_B,
        "glued_collapses" => glued_B_collapses,
        "decpl_collapses" => decpl_B_collapses,
    ),
    "representative_scalar" => Dict(
        "w_L" => w_L_rep,
        "w_R" => w_R_rep,
        "glued_max_abs_A" => glued_max_A,
        "decpl_max_abs_A" => decpl_max_A,
    ),
    "verdict_booleans" => Dict(
        "plain_opp_sign_band_A" => plain_A_opp,
        "plain_opp_sign_band_B" => plain_B_opp,
        "glued_collapses_band_A" => glued_A_collapses,
        "glued_collapses_band_B" => glued_B_collapses,
        "decpl_collapses_band_A" => decpl_A_collapses,
        "decpl_collapses_band_B" => decpl_B_collapses,
        "SIGN_BY_CONSTRUCTION" => sign_by_construction,
        "SIGN_NESTING_SPECIFIC" => sign_nesting_specific,
    ),
    "plain_verdict_phrase" => sign_by_construction ? "SIGN-BY-CONSTRUCTION" : "SIGN-NESTING-SPECIFIC",
    "discriminator_sentence" => (
        sign_by_construction ?
        "A plain S^2 section with iσ_y charge conjugation reproduces w_L=-w_R AND both controls collapse to ~0: the entire cocycle signature — opposite-sign plus control-collapse — is FORCED by the iσ_y charge-conjugation for any section, and NO part of the nested cocycle survives as a genuine nesting discriminator a plain sphere cannot reproduce." :
        "The plain S^2 iσ_y pair does NOT reproduce the full nested-cocycle pattern (opposite-sign + control-collapse on both controls); at least one structural feature of the nesting (Hopf fiber phase, mixed eta<->torus curvature) is required and the cocycle carries genuine nesting information a plain sphere lacks."
    ),
    "tool_manifest" => Dict(
        "LinearAlgebra" => "load_bearing: eigen-spinor computation and FHS Wilson plaquette phases; the entire mixed winding.",
        "JSON" => "supportive: receipt emission only.",
    ),
    "tool_integration_depth" => Dict(
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive",
    ),
    "claim_ceiling" => "Settles the pre-registered sign-structure question for the Weyl-on-nested-Hopf layer. Does NOT assert layer-completion, manifold admission, coupling, bridge, flux, or physics. promotion_allowed=false.",
    "blocked_consumers" => ["layer-completion", "manifold-admission", "coupling", "bridge/Xi/Phi0/Axis0", "flux/FEP", "physics"],
    "status_ladder" => "exists < runs < passes local rerun < canonical by process",
)

open(OUT, "w") do io
    JSON.print(io, results, 2)
end
println("\nwrote: ", OUT)
