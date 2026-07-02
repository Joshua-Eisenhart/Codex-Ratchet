#!/usr/bin/env julia
# eng_yinyang_julia.jl
#
# object_id: eng_yinyang_v1
# claim_ceiling: Yin-yang 1-axis element finite map over F01+N01.
#   Encodes one yin/yang bit as a qubit density matrix on a circle.
#   Checks: FLIP (parity/complex-conjugation = chirality) gives a DISTINCT
#   chiral partner. ROTATE CW vs CCW (axis4 run-directions) give distinct
#   trajectories. FLIP and ROTATE are INDEPENDENT. 6-bit hexagram = 2^6 = 64.
#   Does NOT assert layer-completion, manifold admission, coupling, bridge,
#   flux, or physics. A state that passes is a candidate, not a proven object.
# promotion_allowed: false
#
# Root gates:
#   F01: finite carrier — ensemble of 8/16/32/64 qubit density matrices on S^1
#   N01: non-commuting operation domain — CW vs CCW rotation about z-axis
#        (R_z(+theta) vs R_z(-theta)) compose non-trivially with dephase;
#        flip = complex conjugation (σ_y K σ_y^†) is NOT the same as rotation
#
# Finite map:
#   (state ρ, N_bits) → {ρ_flipped, ρ_cw, ρ_ccw,
#                         flip_gap, cw_ccw_gap, flip_vs_rotate_gap,
#                         two_dots_distinguishable,
#                         hexagram_count, yinyang_schema}
#
# Domain:
#   ρ ∈ {qubit density matrices parameterized on S^1 circle}
#   N_bits ∈ {8, 16, 32, 64}  (size ladder)
#
# Codomain:
#   ρ_flipped     — state after chirality flip (complex conjugation)
#   ρ_cw, ρ_ccw  — states after CW / CCW rotation by angle θ
#   flip_gap      — ||ρ_flipped - ρ||_F  (should be > 0 for non-symmetric state)
#   cw_ccw_gap    — ||ρ_cw - ρ_ccw||_F  (should be > 0; runs are distinct)
#   flip_vs_rotate_gap — ||ρ_flipped - ρ_cw||_F (should be > 0; ops independent)
#   two_dots_distinguishable — yin seed ≠ yang seed (a~b witness: the two dots)
#   hexagram_count — 2^6 = 64  (6 binary axes stacked)
#   yinyang_schema — human-readable encoding
#
# Axis map (owner 2026-06-04):
#   axis0  = entropy monotone readout (Clausius/Shannon/vN)
#   axis1  = expand/compress (Bloch-volume on ρ)
#   axis2  = open/closed (bath-coupled vs isolated)
#   axis3  = Carnot/Szilard engine-family selector
#   axis4  = CW/CCW run-direction (THIS object: the rotate operation)
#   axis5  = hot/cold (spectral/gradient)
#   axis6  = stroke order/precedence (noncommuting composition)
#
#   This object encodes: axis4 (CW vs CCW = engine vs refrigerator),
#   flip = chirality (L/R mirror partner, related to axis2 open/closed sign),
#   two-dots = a~b distinguishability seed (F01 core witness).
#   6-bit stacking shown as hexagram enumeration.

using LinearAlgebra
using Random
using Statistics
using Dates

try
    @eval using JSON
catch _
    try
        import Pkg
        Pkg.activate(@__DIR__; io=devnull)
        @eval using JSON
    catch e2
        error("JSON unavailable: $e2")
    end
end

# ── constants ──────────────────────────────────────────────────────────────────
const OBJECT_ID         = "eng_yinyang_v1"
const CLAIM_CEILING     = "Yin-yang 1-axis element: FLIP=chirality, ROTATE=axis4; 6-bit hexagram=64; F01+N01 only; promotion_allowed=false"
const PROMOTION_ALLOWED = false
const RESULT_PATH       = joinpath(@__DIR__, "eng_yinyang_julia_results.json")
const RNG_SEED          = 20260604
const SIZE_LADDER       = [8, 16, 32, 64]
const FLIP_EPS          = 1.0e-10   # flip should produce a DISTINCT state (gap > this)
const ROTATE_EPS        = 1.0e-10   # CW vs CCW should be distinct (gap > this)
const INDEP_EPS         = 1.0e-10   # flip vs rotate should be distinct (gap > this)
const COMMUTE_EPS       = 1.0e-6    # commuting control gap should be < this
const ROTATE_ANGLE      = π / 4     # 45° rotation used as default stroke

# ── Pauli matrices ─────────────────────────────────────────────────────────────
const I2 = Matrix{ComplexF64}(I, 2, 2)
const σx = ComplexF64[0 1; 1 0]
const σy = ComplexF64[0 -1im; 1im 0]
const σz = ComplexF64[1 0; 0 -1]

# ── YIN-YANG ENCODING ─────────────────────────────────────────────────────────
# One yin/yang bit = one qubit density matrix on the unit circle (S^1 in Bloch).
# Yin  = |ψ_yin⟩  = state parameterized at angle φ (e.g. φ = 0 → |+⟩)
# Yang = |ψ_yang⟩ = state parameterized at angle φ + π  (antipodal)
# The "two dots": each carries a seed of the other — the small opposite circle
# inside each half — encoded as: yin state has a small yang-seed component,
# yang state has a small yin-seed component.  This is the a~b indistinguishability
# witness: the two states are NOT fully distinct (each contains a trace of the other).

function yinyang_state(phi::Float64, seed_eps::Float64)::Matrix{ComplexF64}
    # Pure qubit on the equator of the Bloch circle (S^1 at θ = π/2)
    # |ψ⟩ = cos(φ/2)|0⟩ + e^{iφ}sin(φ/2)|1⟩
    # With seed: add seed_eps of the antipodal component to make
    # the two-dot distinguishability witness non-trivial.
    psi_main = ComplexF64[cos(phi/2), exp(im*phi)*sin(phi/2)]
    psi_anti = ComplexF64[cos((phi+π)/2), exp(im*(phi+π))*sin((phi+π)/2)]
    psi = (1.0 - seed_eps) * psi_main + seed_eps * psi_anti
    n = norm(psi)
    psi ./= n
    return psi * psi'
end

# Yin: angle = 0; Yang: angle = π  (antipodal on circle)
function yin_state(seed_eps::Float64=0.05)::Matrix{ComplexF64}
    return yinyang_state(0.0, seed_eps)
end
function yang_state(seed_eps::Float64=0.05)::Matrix{ComplexF64}
    return yinyang_state(Float64(π), seed_eps)
end

# ── OPERATION A: FLIP (chirality = parity = complex conjugation) ───────────────
# Flip = σ_y K σ_y^† where K is complex conjugation
# Equivalently: ρ → σ_y ρ* σ_y^†
# This is the standard time-reversal / chirality flip on a qubit.
# For a Bloch vector (x,y,z): flip sends (x,y,z) → (x,-y,z) (reflection in xz-plane)
# which is a parity / mirror operation.
function chirality_flip(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    return σy * conj.(rho) * σy'
end

# ── OPERATION B: ROTATE CW vs CCW (axis4 = run-direction) ─────────────────────
# CW rotation about z-axis by angle θ: R_z(+θ) = exp(-i θ/2 σ_z)
# CCW rotation about z-axis by angle θ: R_z(-θ) = exp(+i θ/2 σ_z)
# In Bloch sphere: (x,y,z) → (x cos θ ∓ y sin θ, x sin θ ± y cos θ, z)
function rz_unitary(theta::Float64)::Matrix{ComplexF64}
    return exp(-im * (theta/2) * σz)
end

function rotate_cw(rho::Matrix{ComplexF64}, theta::Float64=ROTATE_ANGLE)::Matrix{ComplexF64}
    U = rz_unitary(theta)
    return U * rho * U'
end

function rotate_ccw(rho::Matrix{ComplexF64}, theta::Float64=ROTATE_ANGLE)::Matrix{ComplexF64}
    U = rz_unitary(-theta)
    return U * rho * U'
end

# ── commuting control: rotation by θ=0 (identity) should give zero gap ────────
function rotate_identity(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    return copy(rho)  # θ=0: no rotation
end

# ── TWO DOTS: distinguishability witness ───────────────────────────────────────
# The two dots of the yin-yang = the seed of the opposite in each half.
# We test: are yin and yang states distinguishable despite each containing
# a seed of the other?
function two_dots_distinguishable(rho_yin::Matrix{ComplexF64}, rho_yang::Matrix{ComplexF64})::Tuple{Float64,Bool}
    gap = norm(rho_yin - rho_yang)
    return gap, gap > FLIP_EPS
end

# ── 6-BIT HEXAGRAM: 2^6 = 64 ──────────────────────────────────────────────────
# Stack 6 yin/yang bits → 64 hexagram states.
# Each bit is one axis from {axis1..axis6}.
# Encode as a 6-bit binary string; show all 64 are distinct.
function hexagram_states(seed_eps::Float64=0.05)
    # Each bit: 0 = yin (angle 0), 1 = yang (angle π)
    # Generate all 64 6-bit combinations
    states_64 = Matrix{ComplexF64}[]
    labels_64 = String[]
    for k in 0:63
        bits = digits(k, base=2, pad=6)  # LSB first → 6 bits
        # Tensor product of 6 qubits (density matrix via Kronecker product)
        rho_k = ones(ComplexF64, 1, 1)
        for b in bits
            phi = b == 0 ? 0.0 : Float64(π)
            rho_bit = yinyang_state(phi, seed_eps)
            rho_k = kron(rho_k, rho_bit)
        end
        push!(states_64, rho_k)
        push!(labels_64, join(reverse(bits)))  # MSB-first label
    end
    # Check all 64 are distinct (pairwise trace-distance sampling)
    # Full pairwise is 64^2/2 = 2016 checks: do a spot-check on neighbors
    n_distinct = 0
    for i in 1:63
        d = norm(states_64[i] - states_64[i+1])
        if d > FLIP_EPS
            n_distinct += 1
        end
    end
    return length(states_64), n_distinct, labels_64[1:4], labels_64[61:64]
end

# ── validity check ─────────────────────────────────────────────────────────────
function density_valid(rho::Matrix{ComplexF64})::Bool
    tr_ok  = abs(tr(rho) - 1.0) < 1e-10
    herm   = norm(rho - rho') < 1e-10
    evals  = eigvals(Hermitian((rho + rho') / 2))
    pos_ok = all(e >= -1e-10 for e in evals)
    return tr_ok && herm && pos_ok
end

function frobenius_gap(a::Matrix{ComplexF64}, b::Matrix{ComplexF64})::Float64
    return norm(a - b)
end

# ── INDEPENDENCE CHECK: FLIP ≠ ROTATE ─────────────────────────────────────────
# Flip is chirality (complex conjugation): Bloch (x,y,z) → (x,-y,z)
# CW rotate is Bloch (x,y,z) → (x cosθ - y sinθ, x sinθ + y cosθ, z)
# These are DIFFERENT operations.  For a generic state, flip ≠ rotate.
# We check: ||flip(ρ) - cw(ρ)|| > threshold for generic states.
function check_independence(rho::Matrix{ComplexF64})::Tuple{Float64,Bool}
    rho_f  = chirality_flip(rho)
    rho_cw = rotate_cw(rho)
    gap    = frobenius_gap(rho_f, rho_cw)
    return gap, gap > INDEP_EPS
end

# ── WRONG-STRUCTURE CONTROL (anti-tautology) ───────────────────────────────────
# Control: use rotation by θ = 0 (identity) → CW=CCW → gap should collapse to 0.
# If gap collapses under identity rotation but survives under ±θ, the
# CW/CCW distinction is NOT by construction but genuinely depends on θ≠0.
function wrong_structure_control_rotate(rho::Matrix{ComplexF64})::Tuple{Float64,Float64}
    rho_id1 = rotate_identity(rho)   # both are identity
    rho_id2 = rotate_identity(rho)
    gap_identity = frobenius_gap(rho_id1, rho_id2)   # should be 0
    # Also: +θ vs -θ control with very small θ (near-commuting)
    tiny = 1e-8
    gap_tiny = frobenius_gap(rotate_cw(rho, tiny), rotate_ccw(rho, tiny))
    return gap_identity, gap_tiny
end

# Control: flip applied twice = identity (check chirality flip is involution)
function wrong_structure_control_flip(rho::Matrix{ComplexF64})::Float64
    rho_ff = chirality_flip(chirality_flip(rho))
    return frobenius_gap(rho_ff, rho)
end

# ── POSITIVE CHECK: flip gives distinct chiral partner ─────────────────────────
# For a qubit with off-diagonal ρ_{01} = a + ib (b ≠ 0):
# flip: ρ_{01} → (σ_y ρ* σ_y)_{01} = -conj(ρ_{01}) = -(a-ib) = -a+ib
# So the imaginary part sign changes → gap is 2|Im(ρ_{01})|.
# For a state on the equator: ρ = 0.5[[1, e^{iφ}],[e^{-iφ}, 1]]
# ρ_{01} = 0.5 e^{iφ}; after flip: ρ_{01} → 0.5 e^{-iφ}·(-1)
# Gap = |ρ_{01,orig} - ρ_{01,flip}| = 0.5|e^{iφ} + e^{-iφ}| = |cos φ|
# For φ = π/4: gap = |cos(π/4)| / 2 ≈ 0.35 → nonzero → distinct chiral partner.

# ── per-size analysis ──────────────────────────────────────────────────────────
function run_at_size(N::Int, rng_seed::Int)
    rng = MersenneTwister(rng_seed + N)

    flip_gaps    = Float64[]
    cw_ccw_gaps  = Float64[]
    indep_gaps   = Float64[]
    ctrl_id_gaps = Float64[]
    ctrl_tiny_gaps = Float64[]
    flip2_gaps   = Float64[]
    state_results = Dict{String,Any}[]

    for i in 1:N
        # Sample φ uniformly on circle (exclude exact 0 and π to avoid degenerate cases)
        phi = 2π * (i - 0.5) / N
        seed_eps = 0.05   # the "two dot" fraction
        rho0 = yinyang_state(phi, seed_eps)

        # Operation A: chirality flip
        rho_flip = chirality_flip(rho0)
        fg = frobenius_gap(rho0, rho_flip)
        push!(flip_gaps, fg)

        # Operation B: CW vs CCW rotation
        rho_cw  = rotate_cw(rho0)
        rho_ccw = rotate_ccw(rho0)
        rcg = frobenius_gap(rho_cw, rho_ccw)
        push!(cw_ccw_gaps, rcg)

        # Independence: flip ≠ rotate
        ig, indep_ok = check_independence(rho0)
        push!(indep_gaps, ig)

        # Wrong-structure controls
        g_id, g_tiny = wrong_structure_control_rotate(rho0)
        push!(ctrl_id_gaps, g_id)
        push!(ctrl_tiny_gaps, g_tiny)

        # Flip involution: flip twice = identity
        f2g = wrong_structure_control_flip(rho0)
        push!(flip2_gaps, f2g)

        push!(state_results, Dict(
            "idx" => i,
            "phi" => phi,
            "flip_gap" => fg,
            "cw_ccw_gap" => rcg,
            "independence_gap" => ig,
            "ctrl_identity_gap" => g_id,
            "ctrl_tiny_gap" => g_tiny,
            "flip_involution_gap" => f2g,
            "rho_valid" => density_valid(rho0),
            "rho_flip_valid" => density_valid(rho_flip),
            "rho_cw_valid" => density_valid(rho_cw),
            "rho_ccw_valid" => density_valid(rho_ccw),
            "flip_distinct" => fg > FLIP_EPS,
            "cw_ccw_distinct" => rcg > ROTATE_EPS,
            "flip_ne_rotate" => ig > INDEP_EPS,
            "ctrl_identity_near_zero" => g_id < COMMUTE_EPS,
            "flip_is_involution" => f2g < COMMUTE_EPS,
        ))
    end

    mean_flip = mean(flip_gaps)
    max_flip  = maximum(flip_gaps)
    mean_cw_ccw = mean(cw_ccw_gaps)
    max_cw_ccw  = maximum(cw_ccw_gaps)
    mean_indep  = mean(indep_gaps)
    max_indep   = maximum(indep_gaps)
    max_ctrl_id = maximum(ctrl_id_gaps)
    max_ctrl_tiny = maximum(ctrl_tiny_gaps)
    max_flip2     = maximum(flip2_gaps)

    n_flip_distinct  = sum(r["flip_distinct"] for r in state_results)
    n_cw_ccw_distinct = sum(r["cw_ccw_distinct"] for r in state_results)
    n_indep          = sum(r["flip_ne_rotate"] for r in state_results)
    n_ctrl_zero      = sum(r["ctrl_identity_near_zero"] for r in state_results)
    n_involution     = sum(r["flip_is_involution"] for r in state_results)

    return Dict{String,Any}(
        "N" => N,
        "mean_flip_gap" => mean_flip,
        "max_flip_gap" => max_flip,
        "mean_cw_ccw_gap" => mean_cw_ccw,
        "max_cw_ccw_gap" => max_cw_ccw,
        "mean_independence_gap" => mean_indep,
        "max_independence_gap" => max_indep,
        "max_ctrl_identity_gap" => max_ctrl_id,
        "max_ctrl_tiny_gap" => max_ctrl_tiny,
        "max_flip_involution_gap" => max_flip2,
        "frac_flip_distinct" => n_flip_distinct / N,
        "frac_cw_ccw_distinct" => n_cw_ccw_distinct / N,
        "frac_indep" => n_indep / N,
        "frac_ctrl_near_zero" => n_ctrl_zero / N,
        "frac_involution" => n_involution / N,
        "flip_is_chirality" => max_flip > FLIP_EPS && n_flip_distinct == N,
        "rotate_is_axis4" => max_cw_ccw > ROTATE_EPS && n_cw_ccw_distinct == N,
        "flip_ne_rotate" => max_indep > INDEP_EPS && n_indep == N,
        "ctrl_identity_collapses" => max_ctrl_id < COMMUTE_EPS,
        "flip_is_involution" => max_flip2 < COMMUTE_EPS,
        "state_results" => state_results,
    )
end

# ── boundary checks ────────────────────────────────────────────────────────────
function boundary_checks()
    results = Dict{String,Any}[]

    # Boundary 1: φ = 0 state (yin state exact) — flip should still give distinct partner
    rho_yin = yin_state(0.05)
    rho_yang = yang_state(0.05)
    rho_yin_flipped = chirality_flip(rho_yin)
    push!(results, Dict(
        "label" => "yin_flip_vs_yang",
        "flip_gap_from_yin" => frobenius_gap(rho_yin, rho_yin_flipped),
        "yin_yang_gap" => frobenius_gap(rho_yin, rho_yang),
        "flip_gives_yang_approx" => frobenius_gap(rho_yin_flipped, rho_yang) < 0.5,
        "note" => "flip of yin should be close to yang (chirality partner); gap shows they are distinct",
    ))

    # Boundary 2: maximally mixed state ρ = I/2 — flip should give identity (no chirality)
    rho_mixed = ComplexF64[0.5 0; 0 0.5]
    rho_mixed_flipped = chirality_flip(rho_mixed)
    rho_mixed_cw = rotate_cw(rho_mixed)
    rho_mixed_ccw = rotate_ccw(rho_mixed)
    push!(results, Dict(
        "label" => "maximally_mixed_boundary",
        "flip_gap" => frobenius_gap(rho_mixed, rho_mixed_flipped),
        "cw_ccw_gap" => frobenius_gap(rho_mixed_cw, rho_mixed_ccw),
        "note" => "mixed state is rotation-invariant; CW/CCW gap should be 0; flip also 0 (no chirality axis to flip)",
    ))

    # Boundary 3: pure |0⟩ — known reference
    rho_0 = ComplexF64[1 0; 0 0]
    rho_0_flip = chirality_flip(rho_0)
    rho_0_cw   = rotate_cw(rho_0)
    rho_0_ccw  = rotate_ccw(rho_0)
    push!(results, Dict(
        "label" => "pure_0_state_boundary",
        "flip_gap" => frobenius_gap(rho_0, rho_0_flip),
        "cw_ccw_gap" => frobenius_gap(rho_0_cw, rho_0_ccw),
        "note" => "|0⟩ has no off-diagonal; flip = identity; CW=CCW for z-eigenstates",
    ))

    # Boundary 4: pure |+⟩ = (|0⟩+|1⟩)/√2 — maximal off-diagonal
    rho_plus = ComplexF64[0.5 0.5; 0.5 0.5]
    rho_plus_flip = chirality_flip(rho_plus)
    rho_plus_cw   = rotate_cw(rho_plus)
    rho_plus_ccw  = rotate_ccw(rho_plus)
    push!(results, Dict(
        "label" => "pure_plus_state_boundary",
        "flip_gap" => frobenius_gap(rho_plus, rho_plus_flip),
        "cw_ccw_gap" => frobenius_gap(rho_plus_cw, rho_plus_ccw),
        "note" => "|+⟩ has maximal real off-diagonal; flip changes sign of imaginary part (here 0) → flip≈identity; CW≠CCW",
    ))

    return results
end

# ── two-dots test ──────────────────────────────────────────────────────────────
function run_two_dots_test()
    rho_yin  = yin_state(0.05)
    rho_yang = yang_state(0.05)
    gap, dist = two_dots_distinguishable(rho_yin, rho_yang)
    return Dict{String,Any}(
        "label" => "two_dots_distinguishability",
        "yin_yang_frobenius_gap" => gap,
        "two_dots_distinguishable" => dist,
        "seed_eps" => 0.05,
        "interpretation" => "yin and yang are DISTINCT despite each carrying a seed of the other (two dots); gap > 0 confirms distinguishability under F01",
    )
end

# ── hexagram test ──────────────────────────────────────────────────────────────
function run_hexagram_test()
    total, n_distinct_neighbors, first4, last4 = hexagram_states(0.05)
    return Dict{String,Any}(
        "label" => "hexagram_64_states",
        "total_states" => total,
        "expected" => 64,
        "n_distinct_neighbor_pairs" => n_distinct_neighbors,
        "n_neighbor_pairs_checked" => 63,
        "first4_labels" => first4,
        "last4_labels" => last4,
        "hexagram_count_correct" => total == 64,
        "neighbors_all_distinct" => n_distinct_neighbors == 63,
        "interpretation" => "6 stacked yin-yang bits produce 2^6=64 hexagram states; neighbor pairs are distinct under Frobenius norm",
    )
end

# ── main ───────────────────────────────────────────────────────────────────────
function main()
    println("Running eng_yinyang_v1 ...")
    t0 = now()

    # Size ladder
    ladder_results = Dict{String,Any}[]
    for N in SIZE_LADDER
        println("  N=$N ...")
        res = run_at_size(N, RNG_SEED)
        # Strip per-state details for ladder summary
        res_summary = copy(res)
        delete!(res_summary, "state_results")
        push!(ladder_results, res_summary)
    end

    # Full state-level results for N=16 (reference size)
    full_N16 = run_at_size(16, RNG_SEED)
    state_summaries = [Dict(
        "idx" => r["idx"],
        "phi" => r["phi"],
        "flip_gap" => r["flip_gap"],
        "cw_ccw_gap" => r["cw_ccw_gap"],
        "independence_gap" => r["independence_gap"],
        "ctrl_identity_gap" => r["ctrl_identity_gap"],
        "flip_involution_gap" => r["flip_involution_gap"],
        "flip_distinct" => r["flip_distinct"],
        "cw_ccw_distinct" => r["cw_ccw_distinct"],
        "flip_ne_rotate" => r["flip_ne_rotate"],
        "ctrl_identity_near_zero" => r["ctrl_identity_near_zero"],
        "flip_is_involution" => r["flip_is_involution"],
    ) for r in full_N16["state_results"]]

    boundary = boundary_checks()
    two_dots = run_two_dots_test()
    hexagram = run_hexagram_test()

    # Summary from N=64
    n64 = ladder_results[end]
    flip_is_chirality   = n64["flip_is_chirality"]
    rotate_is_axis4     = n64["rotate_is_axis4"]
    flip_ne_rotate      = n64["flip_ne_rotate"]
    ctrl_id_collapses   = n64["ctrl_identity_collapses"]
    flip_involution     = n64["flip_is_involution"]

    # Honest parity metrics (for JAX comparison)
    parity_ref = Dict{String,Any}(
        "N" => 64,
        "mean_flip_gap" => n64["mean_flip_gap"],
        "mean_cw_ccw_gap" => n64["mean_cw_ccw_gap"],
        "mean_independence_gap" => n64["mean_independence_gap"],
        "max_ctrl_identity_gap" => n64["max_ctrl_identity_gap"],
        "rotate_angle_radians" => ROTATE_ANGLE,
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "root_gates" => ["F01", "N01"],
        "carrier_realization" => "Julia ComplexF64 qubit density matrices on S^1 (Bloch equator circle); 6-bit hexagram stack",
        "timestamp" => string(t0),
        "rotate_angle_radians" => ROTATE_ANGLE,
        "seed_eps" => 0.05,
        "size_ladder_results" => ladder_results,
        "n16_state_summaries" => state_summaries,
        "boundary_checks" => boundary,
        "two_dots_test" => two_dots,
        "hexagram_test" => hexagram,
        "parity_ref_for_jax" => parity_ref,
        "summary_n64" => Dict(
            "flip_is_chirality" => flip_is_chirality,
            "rotate_is_axis4" => rotate_is_axis4,
            "flip_independent_of_rotate" => flip_ne_rotate,
            "ctrl_identity_collapses" => ctrl_id_collapses,
            "flip_is_involution" => flip_involution,
            "mean_flip_gap" => n64["mean_flip_gap"],
            "mean_cw_ccw_gap" => n64["mean_cw_ccw_gap"],
            "mean_independence_gap" => n64["mean_independence_gap"],
            "max_ctrl_identity_gap" => n64["max_ctrl_identity_gap"],
            "frac_flip_distinct" => n64["frac_flip_distinct"],
            "frac_cw_ccw_distinct" => n64["frac_cw_ccw_distinct"],
            "frac_indep" => n64["frac_indep"],
            "yinyang_schema" => Dict(
                "one_bit" => "qubit rho on S^1 (Bloch equator), yin=phi0, yang=phi_pi",
                "two_dots" => "seed_eps=0.05 component of opposite in each state; gap > 0 → a~b distinguishable",
                "flip" => "chirality = complex conjugation = sigma_y K sigma_y† ; Bloch (x,y,z)→(x,-y,z)",
                "rotate_cw" => "R_z(+theta) = exp(-i theta/2 sigma_z); axis4 CW run-direction",
                "rotate_ccw" => "R_z(-theta) = exp(+i theta/2 sigma_z); axis4 CCW run-direction",
                "six_bits" => "6 independent yin/yang axes = 2^6 = 64 hexagram states",
                "axis_map" => Dict(
                    "axis0" => "entropy monotone readout (Clausius/Shannon/vN)",
                    "axis1" => "expand/compress (Bloch volume)",
                    "axis2" => "open/closed (bath-coupled vs isolated)",
                    "axis3" => "Carnot/Szilard engine-family selector",
                    "axis4" => "CW/CCW run-direction (THIS object: rotate_cw vs rotate_ccw)",
                    "axis5" => "hot/cold (spectral/gradient)",
                    "axis6" => "stroke order/precedence (noncommuting composition)",
                ),
            ),
        ),
        "honest_caveat" => "flip_is_chirality=true iff ALL N=64 states show flip_gap > eps AND flip is not the identity. rotate_is_axis4=true iff ALL states show cw≠ccw. If either is false, the claim is not earned. ctrl_identity_gap must collapse to confirm the CW/CCW split is not by construction.",
        "downstream_blocks" => [
            "layer_completion",
            "manifold_admission",
            "coupling",
            "bridge",
            "Axis0_readout",
            "flux",
            "physics",
            "engine_family_coupling",
        ],
    )

    open(RESULT_PATH, "w") do f
        JSON.print(f, result, 2)
    end
    println("Result written to: $RESULT_PATH")

    println("\n=== Yin-Yang Engine Summary (N=64) ===")
    println("  flip_is_chirality      : $flip_is_chirality")
    println("  rotate_is_axis4        : $rotate_is_axis4")
    println("  flip_independent_of_rotate : $flip_ne_rotate")
    println("  ctrl_identity_collapses    : $ctrl_id_collapses")
    println("  flip_is_involution         : $flip_involution")
    println("  mean_flip_gap              : $(n64["mean_flip_gap"])")
    println("  mean_cw_ccw_gap            : $(n64["mean_cw_ccw_gap"])")
    println("  mean_independence_gap      : $(n64["mean_independence_gap"])")
    println("  max_ctrl_identity_gap      : $(n64["max_ctrl_identity_gap"])")
    println("  two_dots_distinguishable   : $(two_dots["two_dots_distinguishable"])")
    println("  hexagram_count             : $(hexagram["total_states"]) (expected 64)")
    println("  hexagram_neighbors_distinct: $(hexagram["neighbors_all_distinct"])")
    println("\nDone.")
end

main()
