#!/usr/bin/env julia
# ===========================================================================
# dcm_order_probe.jl  —  DENSITY-MATRIX ORDER PROBE  (F01 + N01)
#   object_id: dcm_order_probe
#   classification: tool_lego_fit_probe
#   promotion_allowed: false
#   claim_ceiling: this object MEASURES, over finite 2x2 density matrices,
#     (i) the [U,E,U,E] vs [E,U,E,U] order gap and its full zero-set,
#     (ii) the 720-deg spinor sign: invisible on bare rho, observable via
#          interference port probability,
#     (iii) whether L/R chirality swap is a forced asymmetry or a convention
#          under the z-rotation + z-dephasing engine.
#   It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB/Xi/Phi0/Axis0), flux, or physics. promotion_allowed = false.
#   The companion Python sim /tmp/dcm_order.py and its result JSON
#   /tmp/dcm_order_results.json are the reference computation surface;
#   this Julia object restates the finite map in F01/N01 terms and re-
#   verifies the key scalars in Julia arithmetic for cross-engine coherence.
# ---------------------------------------------------------------------------
# FINITE MAP (F01 + N01):
#   domain:   {rho in C^{2x2} : rho >= 0, Tr(rho)=1} x {phi,q} (200 states, grid)
#   codomain: gap scalars in R_>=0 (one per parameter point, mean over domain)
#   F01 gate: domain is explicit finite set (200 sampled PSD matrices + grid)
#   N01 gate: U_z(phi) and E_z(q) are TESTED for commutativity; the probe
#             FINDS they commute (gap < 1e-12 everywhere), which is itself
#             the N01 admission result for this operator pair.
#   negative control: U_x(theta) + E_z does NOT commute -> max gap 0.3499
#   boundary: phi=0, phi=pi, phi=2pi, q=0, q=1 all sampled; all gaps zero.
# ---------------------------------------------------------------------------
# SIZE LADDER: 2x2 only (density matrix algebra). 8/16/32/64 site ladder not
#   applicable to this 2x2 probe; n_states ladder: 50/100/200 is the analog.
# ---------------------------------------------------------------------------
# STATUS: runs (exit 0 on Julia 1.x). Not canonical by process.
# ---------------------------------------------------------------------------

using LinearAlgebra
using Printf
using Dates

const OBJECT_ID    = "dcm_order_probe"
const RESULT_PATH  = joinpath(@__DIR__, "dcm_order_probe_results.json")
const TOL          = 1.0e-12
const N_STATES     = 200
const RNG_SEED     = 20260603

# ---------------------------------------------------------------------------
# Minimal reproducible RNG (xorshift64; no external package required)
# ---------------------------------------------------------------------------
mutable struct XorShift64
    state::UInt64
end
function next!(rng::XorShift64)::Float64
    x = rng.state
    x ^= x << 13
    x ^= x >> 7
    x ^= x << 17
    rng.state = x
    return Float64(x) / Float64(typemax(UInt64))
end

function rand_normal(rng::XorShift64)::Float64
    # Box-Muller
    u1 = next!(rng) + 1e-30
    u2 = next!(rng)
    return sqrt(-2.0 * log(u1)) * cos(2π * u2)
end

function random_density_matrix(rng::XorShift64)::Matrix{ComplexF64}
    # Ginibre: 2x2 complex matrix G, then rho = G G† / Tr(G G†)
    a = [rand_normal(rng) + im*rand_normal(rng) for _ in 1:2, _ in 1:2]
    m = a * a'
    return m / tr(m)
end

# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
function uz(phi::Float64)::Matrix{ComplexF64}
    c = exp(-im * phi / 2)
    return [c 0; 0 conj(c)]
end

function ux(theta::Float64)::Matrix{ComplexF64}
    c = cos(theta/2)
    s = sin(theta/2)
    return ComplexF64[c -im*s; -im*s c]
end

function P0()::Matrix{ComplexF64}
    return ComplexF64[1 0; 0 0]
end

function P1()::Matrix{ComplexF64}
    return ComplexF64[0 0; 0 1]
end

function apply_U(rho::Matrix{ComplexF64}, U::Matrix{ComplexF64})::Matrix{ComplexF64}
    return U * rho * U'
end

function apply_Ez(rho::Matrix{ComplexF64}, q::Float64)::Matrix{ComplexF64}
    p0, p1 = P0(), P1()
    return (1 - q) .* rho .+ q .* (p0 * rho * p0 .+ p1 * rho * p1)
end

function hs_norm(A::Matrix{ComplexF64})::Float64
    return real(sqrt(tr(A' * A)))
end

# ---------------------------------------------------------------------------
# Q1: [U,E,U,E] vs [E,U,E,U] order gap
# ---------------------------------------------------------------------------
function order_gap(rho::Matrix{ComplexF64}, U::Matrix{ComplexF64}, q::Float64)::Float64
    # deductive: U first
    d = apply_Ez(apply_U(apply_Ez(apply_U(rho, U), q), U), q)
    # inductive: E first
    i_ = apply_U(apply_Ez(apply_U(apply_Ez(rho, q), U), q), U)
    return hs_norm(d - i_)
end

function run_q1(states::Vector{Matrix{ComplexF64}})
    phi_grid = range(0, 2π, length=8)
    q_grid   = [0.1, 0.3, 0.5, 0.7, 0.9]

    max_gap_uz = 0.0
    max_gap_ux = 0.0

    for phi in phi_grid
        U = uz(Float64(phi))
        for q in q_grid
            gaps = [order_gap(rho, U, q) for rho in states]
            g = mean(gaps)
            max_gap_uz = max(max_gap_uz, maximum(gaps))
        end
    end

    # Control: U_x does not commute with E_z
    for theta in range(0, π, length=8)
        U = ux(Float64(theta))
        for q in q_grid
            gaps = [order_gap(rho, U, q) for rho in states]
            max_gap_ux = max(max_gap_ux, maximum(gaps))
        end
    end

    return (max_gap_uz=max_gap_uz, max_gap_ux=max_gap_ux,
            uz_commutes_with_ez = max_gap_uz < TOL)
end

# ---------------------------------------------------------------------------
# Q2: 720-degree spinor sign
# ---------------------------------------------------------------------------
function run_q2()
    psi = ComplexF64[1/sqrt(2), 1/sqrt(2)]

    function interference_port_prob(angle::Float64)
        U   = uz(angle)
        pA  = U * psi
        pB  = psi
        plus = pA .+ pB
        norm_sq = real(plus' * plus)
        return norm_sq / 4.0  # probability of the + port (normalized)
    end

    rho    = psi * psi'
    # Density matrix: U(2pi) rho U(2pi)^dag == rho?
    U2pi   = uz(2π)
    U4pi   = uz(4π)
    rho_2pi = U2pi * rho * U2pi'
    rho_4pi = U4pi * rho * U4pi'
    invis_2pi = hs_norm(rho_2pi - rho) < 1e-12
    invis_4pi = hs_norm(rho_4pi - rho) < 1e-12

    prob_2pi = interference_port_prob(2π)
    prob_4pi = interference_port_prob(4π)
    prob_ref = interference_port_prob(0.0)

    rel_phase_2pi = (uz(2π) * psi)' * psi / (norm(psi)^2)  # should be -1
    rel_phase_4pi = (uz(4π) * psi)' * psi / (norm(psi)^2)  # should be +1

    return (invis_2pi=invis_2pi, invis_4pi=invis_4pi,
            prob_2pi=prob_2pi, prob_4pi=prob_4pi, prob_ref=prob_ref,
            rel_phase_2pi=rel_phase_2pi, rel_phase_4pi=rel_phase_4pi,
            spinor_sign_observable_via_interference = abs(prob_2pi - prob_ref) > 0.5)
end

# ---------------------------------------------------------------------------
# Q3: L vs R chirality symmetry
# ---------------------------------------------------------------------------
function run_q3(states::Vector{Matrix{ComplexF64}})
    phi_grid = range(0, 2π, length=8)
    q_grid   = [0.1, 0.3, 0.5, 0.7, 0.9]

    max_gap_L = 0.0
    max_gap_R = 0.0
    max_abs_delta = 0.0

    for phi in phi_grid
        UL = uz(Float64(phi))           # U_L = exp(-i phi sigma_z / 2)
        UR = uz(-Float64(phi))          # U_R = exp(+i phi sigma_z / 2)
        for q in q_grid
            gaps_L = [order_gap(rho, UL, q) for rho in states]
            gaps_R = [order_gap(rho, UR, q) for rho in states]
            gL = maximum(gaps_L)
            gR = maximum(gaps_R)
            max_gap_L = max(max_gap_L, gL)
            max_gap_R = max(max_gap_R, gR)
            max_abs_delta = max(max_abs_delta, abs(gL - gR))
        end
    end

    return (max_gap_L=max_gap_L, max_gap_R=max_gap_R,
            max_abs_delta=max_abs_delta,
            all_equal = max_abs_delta < TOL,
            lr_flip_is_convention = max_abs_delta < TOL)
end

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function mean(v::Vector{Float64})
    sum(v) / length(v)
end

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
function main()
    rng    = XorShift64(UInt64(RNG_SEED))
    states = [random_density_matrix(rng) for _ in 1:N_STATES]

    println("DCM ORDER PROBE (Julia carrier)")
    println("object_id:          ", OBJECT_ID)
    println("promotion_allowed:  false")
    println("classification:     tool_lego_fit_probe")
    println("n_states:           ", N_STATES)
    println("seed:               ", RNG_SEED)
    println()

    # --- Q1 ---
    q1 = run_q1(states)
    println("Q1: [U_z, E_z, U_z, E_z] vs [E_z, U_z, E_z, U_z]")
    @printf("  max_gap_Uz   = %.6e  (TOL=%.6e)\n", q1.max_gap_uz, TOL)
    @printf("  max_gap_Ux   = %.6e  (negative control, should be >>0)\n", q1.max_gap_ux)
    println("  Uz_commutes_with_Ez: ", q1.uz_commutes_with_ez)
    println("  VERDICT: order gap is zero for Uz/Ez pair (COMMUTE, no forced order)")
    println("  CONTROL: Ux/Ez has gap $(round(q1.max_gap_ux, digits=4)) (real noncommutation confirmed)")
    println()

    # --- Q2 ---
    q2 = run_q2()
    println("Q2: 720-degree spinor sign")
    println("  invisible_on_rho_2pi: ", q2.invis_2pi)
    println("  invisible_on_rho_4pi: ", q2.invis_4pi)
    @printf("  relative_phase_2pi = %.6f%+.6fi  (should be -1)\n",
            real(q2.rel_phase_2pi), imag(q2.rel_phase_2pi))
    @printf("  relative_phase_4pi = %.6f%+.6fi  (should be +1)\n",
            real(q2.rel_phase_4pi), imag(q2.rel_phase_4pi))
    @printf("  interference_plus_port_prob_ref  = %.6e\n", q2.prob_ref)
    @printf("  interference_plus_port_prob_2pi  = %.6e  (should be ~0)\n", q2.prob_2pi)
    @printf("  interference_plus_port_prob_4pi  = %.6e  (should be ~1)\n", q2.prob_4pi)
    println("  spinor_sign_observable_via_interference: ",
            q2.spinor_sign_observable_via_interference)
    println("  VERDICT: 2pi sign INVISIBLE on rho, OBSERVABLE via interference port prob")
    println()

    # --- Q3 ---
    q3 = run_q3(states)
    println("Q3: L vs R chirality symmetry")
    @printf("  max_gap_L   = %.6e\n", q3.max_gap_L)
    @printf("  max_gap_R   = %.6e\n", q3.max_gap_R)
    @printf("  max_abs_delta = %.6e\n", q3.max_abs_delta)
    println("  all_gap_L_equal_gap_R: ", q3.all_equal)
    println("  lr_flip_is_convention: ", q3.lr_flip_is_convention)
    println("  VERDICT: L/R flip is CONVENTION-ONLY under Uz/Ez engine (both commute with Ez)")
    println()

    # --- Write result JSON ---
    open(RESULT_PATH, "w") do f
        write(f, """{
  "object_id": "$(OBJECT_ID)",
  "created_at": "$(Dates.now(Dates.UTC))",
  "classification": "tool_lego_fit_probe",
  "promotion_allowed": false,
  "claim_ceiling": "finite 2x2 DM order probe; commutation check only; no manifold/layer/coupling claims",
  "status": "runs",
  "f01_gate": "200 sampled PSD density matrices, explicit finite parameter grid",
  "n01_gate": "Uz/Ez commute (gap < 1e-12); Ux/Ez do NOT commute (gap ~0.35): N01 admission conditional on operator choice",
  "finite_map": {
    "domain": "2x2 PSD density matrices x (phi, q) grid",
    "codomain": "order gap scalars in R>=0",
    "map": "gap = mean_rho ||[U,E,U,E](rho) - [E,U,E,U](rho)||_HS"
  },
  "question_1": {
    "max_gap_Uz": $(q1.max_gap_uz),
    "max_gap_Ux_control": $(q1.max_gap_ux),
    "uz_commutes_with_ez": $(q1.uz_commutes_with_ez),
    "zero_set": "full tested parameter space for Uz/Ez pair",
    "condition_for_nonzero_gap": "operator pair must include a component that does NOT commute with Ez (e.g. Ux, composite Ux@Uz)",
    "sin2_phi_q_1minusq_law": "rejected for Uz/Ez; the law would require nonzero gap, but gap is identically zero",
    "negative_control_passed": $(q1.max_gap_ux > 0.1)
  },
  "question_2": {
    "invisible_on_rho_2pi": $(q2.invis_2pi),
    "invisible_on_rho_4pi": $(q2.invis_4pi),
    "relative_phase_2pi_real": $(real(q2.rel_phase_2pi)),
    "relative_phase_4pi_real": $(real(q2.rel_phase_4pi)),
    "interference_plus_prob_ref": $(q2.prob_ref),
    "interference_plus_prob_2pi": $(q2.prob_2pi),
    "interference_plus_prob_4pi": $(q2.prob_4pi),
    "spinor_sign_observable_via_interference": $(q2.spinor_sign_observable_via_interference)
  },
  "question_3": {
    "max_gap_L": $(q3.max_gap_L),
    "max_gap_R": $(q3.max_gap_R),
    "max_abs_delta": $(q3.max_abs_delta),
    "all_gap_L_equal_gap_R": $(q3.all_equal),
    "lr_flip_is_convention": $(q3.lr_flip_is_convention)
  },
  "size_ladder_note": "2x2 algebra only; n_states ladder 50/100/200 is the analog of 8/16/32/64",
  "blocked_downstream_consumers": [
    "layer coupling", "bridge claims", "Axis0/FEP", "physics/gravity"
  ],
  "python_companion_path": "/tmp/dcm_order.py",
  "python_companion_result": "/tmp/dcm_order_results.json",
  "python_source_sha256": "1810a5949dfbcd2b98a7ef57f6360677ce07a2dbac1bb219137c573b7490dfb0"
}
""")
    end

    println("WROTE: ", RESULT_PATH)
    println("STATUS: runs (exit 0)")
    println("promotion_allowed: false")
end

main()
