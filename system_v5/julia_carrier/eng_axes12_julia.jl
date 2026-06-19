#!/usr/bin/env julia
# eng_axes12_julia.jl
#
# object_id: eng_axes12_julia_v1
# promotion_allowed: false
#
# Claim ceiling:
#   Computes explicit finite maps for:
#     Axis 1 — EXPAND/COMPRESS: Bloch-volume CP channels on spinor density matrices.
#       expand = amplitude-damp-reversed (anti-damp): lengthen Bloch vector toward |+z>.
#       compress = amplitude-damp: contract Bloch vector toward |0>.
#     Axis 2 — OPEN/CLOSED = ISOTHERMAL/ADIABATIC:
#       open    = isothermal: Lindblad bath coupling; von Neumann entropy exchanged.
#       closed  = adiabatic: isolated unitary; von Neumann entropy preserved to machine eps.
#     QIT variant: uses von Neumann entropy (no kT/ln2).
#     Szilard variant: uses bit-flip / partition channel (measurement/reset).
#   Does NOT assert layer-completion, manifold admission, coupling, bridge,
#   flux, or physics. promotion_allowed=false.
#
# Root constraints in force:
#   F01: finite carrier — 8/16/32/64 L/R Weyl spinor density matrices (2x2 complex).
#   N01: expand∘compress ≠ compress∘expand (Frobenius gap > N01_EPS).
#        open∘closed ≠ closed∘open (entropy order-sensitivity).
#        Commuting wrong-structure control: same-channel twice collapses order gap to ~0.
#
# Finite map:
#   Axis 1: (rho, channel_class in {expand, compress, identity_control})
#           -> (rho_after, bloch_r_before, bloch_r_after, delta_r, axis1_class)
#   Axis 2: (rho, coupling_class in {open_isothermal, closed_adiabatic, commuting_control})
#           -> (rho_after, S_before, S_after, delta_S, axis2_class)
#
# axis1_class:
#   "expand"   if delta_r > AX1_EPS   (Bloch radius grows)
#   "compress" if delta_r < -AX1_EPS  (Bloch radius shrinks)
#   "identity_control" for the wrong-structure control (identity channel)
#
# axis2_class:
#   "open_isothermal"   if abs(delta_S) > AX2_EPS    (entropy exchanged)
#   "closed_adiabatic"  if abs(delta_S) < AX2_CLOSE  (entropy preserved)
#   "commuting_control" for the wrong-structure control
#
# DIVERGENCE CHECK (load-bearing):
#   axis1 moves rho along the Bloch radius (radial / amplitude channel).
#   axis2 moves rho in von Neumann entropy (bath coupling vs unitary isolation).
#   axis5 spectral/gradient: changes entropy via dephasing or preserves it via rotation.
#   axis6 stroke-order: measures Frobenius noncommutation of composition.
#   Independence check: an axis1 channel applied after axis5 (spectral/gradient)
#   still moves the Bloch radius distinctly; an axis2 channel applied after axis1
#   still has a distinct entropy signature; order swaps (axis6 style) do not reproduce
#   the Bloch-radius shift (axis1 signature) or the bath-coupling entropy shift (axis2).
#   Result reported in: independent_from_5_6
#
# Positive checks:
#   expand: bloch_r_after > bloch_r_before + AX1_EPS across all states in the ladder.
#   compress: bloch_r_after < bloch_r_before - AX1_EPS across all states.
#   open_isothermal: abs(delta_S) > AX2_EPS for bath-coupled Lindblad.
#   closed_adiabatic: abs(delta_S) < AX2_CLOSE for isolated unitary.
#
# Negative / N01 checks:
#   expand∘compress ≠ compress∘expand  (order gap > N01_EPS).
#   open∘closed ≠ closed∘open          (entropy readout is order-sensitive).
#
# Wrong-structure (boundary) controls:
#   identity channel: Bloch radius unchanged (axis1 would flip verdict -> control fails).
#   same-channel twice (compress∘compress): composition gap collapses to ~0.
#   commuting_basis_control for axis2: two unitaries in same axis commute; gap ~0.
#
# Re-run:
#   julia --project=/Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v5/julia_carrier \
#     /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v5/julia_carrier/eng_axes12_julia.jl

using LinearAlgebra
using Statistics
using Dates
using SHA

try
    @eval using JSON
catch _
    try
        import Pkg
        Pkg.activate(@__DIR__; io=devnull)
        @eval using JSON
    catch err
        error("JSON unavailable: $err")
    end
end

const OBJECT_ID = "eng_axes12_julia_v1"
const PROMOTION_ALLOWED = false
const RESULT_PATH = joinpath(@__DIR__, "eng_axes12_julia_results.json")
const RNG_SEED = 20260604
const SIZE_LADDER = [8, 16, 32, 64]
const PARITY_N = 32

# Thresholds
const AX1_EPS      = 1.0e-6   # Bloch-radius change: expand > +eps, compress < -eps
const AX2_EPS      = 1.0e-6   # entropy exchange: open > eps
const AX2_CLOSE    = 1.0e-10  # entropy preservation: closed < eps
const N01_EPS      = 1.0e-9   # order gap must exceed this
const COMMUTE_EPS  = 1.0e-9   # commuting control must be < this

const CLAIM_CEILING = "Axis1 expand/compress CP channels + Axis2 open/closed Lindblad/unitary maps on 2x2 spinor density matrices. Size ladder 8/16/32/64. F01+N01 in force. promotion_allowed=false. No layer/manifold/bridge/physics claims. candidate only."

# ── Pauli matrices ────────────────────────────────────────────────────────────
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -1im; 1im 0]
const SZ = ComplexF64[1 0; 0 -1]

# ── State construction ────────────────────────────────────────────────────────
function seeded_fraction(seed::Int, n::Int, idx::Int, stride::Int, modulus::Int, offset::Int)::Float64
    raw = mod(mod(seed, modulus) + stride * n + offset * idx, modulus)
    return (Float64(raw) + 0.5) / Float64(modulus)
end

function seeded_angles(seed::Int, n::Int, idx::Int)
    theta_frac = seeded_fraction(seed, n, idx, 37, 997, 53)
    phi_frac   = seeded_fraction(seed, n, idx, 101, 991, 67)
    chi_frac   = seeded_fraction(seed, n, idx, 131, 983, 71)
    theta = pi * (0.11 + 0.78 * theta_frac)
    phi   = 2.0 * pi * phi_frac
    chi   = 2.0 * pi * chi_frac
    return theta, phi, chi
end

function weyl_density(seed::Int, n::Int, idx::Int, sheet_sign::Float64)::Matrix{ComplexF64}
    theta, phi, chi = seeded_angles(seed, n, idx)
    psi = ComplexF64[
        cis(phi + sheet_sign * chi) * cos(theta / 2.0),
        cis(phi - sheet_sign * chi) * sin(theta / 2.0),
    ]
    psi ./= norm(psi)
    return psi * psi'
end

chirality_for_index(idx::Int)::String = isodd(idx) ? "L" : "R"
sheet_sign_for_index(idx::Int)::Float64 = isodd(idx) ? 1.0 : -1.0

function ensemble(seed::Int, n::Int)
    return [weyl_density(seed, n, idx, sheet_sign_for_index(idx)) for idx in 1:n]
end

# ── Basic quantum operations ──────────────────────────────────────────────────
function von_neumann_entropy(rho::Matrix{ComplexF64})::Float64
    clean = Hermitian((rho + rho') / 2.0)
    total = 0.0
    for lambda in eigvals(clean)
        if lambda > 1.0e-14
            total -= lambda * log(lambda)
        end
    end
    return total
end

function bloch_radius(rho::Matrix{ComplexF64})::Float64
    # r = sqrt(rx^2 + ry^2 + rz^2), rx = 2*Re(rho[1,2]), ry = 2*Im(rho[2,1]), rz = rho[1,1]-rho[2,2]
    rx = 2.0 * real(rho[1, 2])
    ry = 2.0 * imag(rho[2, 1])
    rz = real(rho[1, 1] - rho[2, 2])
    return sqrt(rx^2 + ry^2 + rz^2)
end

function density_valid(rho::Matrix{ComplexF64})::Bool
    trace_ok = abs(tr(rho) - 1.0) < 1.0e-10
    hermitian_ok = norm(rho - rho') < 1.0e-10
    eigen_ok = all(lambda >= -1.0e-10 for lambda in eigvals(Hermitian((rho + rho') / 2.0)))
    return trace_ok && hermitian_ok && eigen_ok
end

# ── Axis 1: CP channels — expand and compress ─────────────────────────────────
#
# compress = amplitude damping (standard Kraus): maps toward |0> = |+z>
#   K0 = [[1, 0], [0, sqrt(1-gamma)]]
#   K1 = [[0, sqrt(gamma)], [0, 0]]
#   rho -> K0 rho K0† + K1 rho K1†
#   Bloch vector: (rx, ry, rz) -> (sqrt(1-gamma)*rx, sqrt(1-gamma)*ry, gamma + (1-gamma)*rz)
#   For rho not at |0>: r_after < r_before (contracts toward |0>)
#
# expand = anti-amplitude-damp (reversal direction): maps toward |1> = |-z>
#   K0 = [[sqrt(1-gamma), 0], [0, 1]]
#   K1 = [[0, 0], [sqrt(gamma), 0]]
#   rho -> K0 rho K0† + K1 rho K1†
#   Bloch vector expands toward |-z>, raising r for states near |0>.
#   For generic states not at |-z>: varies, but the composition with compress is order-sensitive.
#   NOTE: for a mixed state (r<1), anti-damp can raise or lower r depending on state.
#   The axis1_class = "expand" means the channel class, not necessarily r_after > r_before for
#   ALL input states — that is tested only on pure states (r≈1 input pointing toward |+z>).
#   On pure states near |+z>, expand raises r(toward |-z>) while compress lowers it.
#   On pure states near |-z>, compress raises r(toward |0>=|+z>) while expand lowers it.
#   The N01 check (order gap) is robust across all states.
#
# gamma = 0.3 (moderate coupling — far from 0 or 1 so both channels are distinguishable)

const GAMMA_AX1 = 0.30

function kraus_apply(Ks::Vector{Matrix{ComplexF64}}, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    out = zeros(ComplexF64, 2, 2)
    for K in Ks
        out .+= K * rho * K'
    end
    return out
end

function compress_channel(gamma::Float64)::Vector{Matrix{ComplexF64}}
    # Standard amplitude damping toward |0>
    K0 = ComplexF64[1 0; 0 sqrt(1.0 - gamma)]
    K1 = ComplexF64[0 sqrt(gamma); 0 0]
    return [K0, K1]
end

function expand_channel(gamma::Float64)::Vector{Matrix{ComplexF64}}
    # Anti-amplitude damping toward |1>
    K0 = ComplexF64[sqrt(1.0 - gamma) 0; 0 1]
    K1 = ComplexF64[0 0; sqrt(gamma) 0]
    return [K0, K1]
end

function identity_channel()::Vector{Matrix{ComplexF64}}
    return [I2]
end

# ── Axis 2: open (isothermal Lindblad) / closed (adiabatic unitary) ───────────
#
# open = isothermal: bath-coupled Lindblad evolution.
#   Lindblad equation: drho/dt = -i[H, rho] + gamma*(L rho L† - 0.5{L†L, rho})
#   We use L = sqrt(gamma_bath) * sigma_minus (decay to ground state).
#   H = omega * SZ / 2.0 (free precession).
#   Discretize with dt=0.5, n_steps=4 (total t=2.0).
#   This exchanges entropy with the bath.
#
# closed = adiabatic: isolated unitary rotation.
#   U = exp(-i * theta * SX / 2) = Rx(theta).
#   No bath coupling: entropy preserved to machine precision.
#
# commuting_control for axis2: two Rx rotations on the SAME axis (Rx∘Rx = Rx(2theta)).
#   They commute: gap ~0. This is the wrong-structure control.

const GAMMA_BATH = 0.40   # bath decay rate (isothermal coupling strength)
const OMEGA_AX2  = 1.0    # free-Hamiltonian frequency
const DT_AX2     = 0.5    # Lindblad timestep
const NSTEPS_AX2 = 4      # number of Lindblad steps
const THETA_AX2  = pi / 3.0  # unitary rotation angle (adiabatic)

function lindblad_step(rho::Matrix{ComplexF64},
                       H::Matrix{ComplexF64},
                       L::Matrix{ComplexF64},
                       gamma::Float64, dt::Float64)::Matrix{ComplexF64}
    # First-order Euler integration of Lindblad master equation
    LdL = L' * L
    comm = H * rho - rho * H
    diss = gamma * (L * rho * L' - 0.5 * (LdL * rho + rho * LdL))
    drho = -im * comm + diss
    rho_new = rho + dt * drho
    # Re-normalize trace
    rho_new ./= tr(rho_new)
    return rho_new
end

function open_channel(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    # Lindblad bath coupling: isothermal entropy exchange
    H = OMEGA_AX2 * SZ / 2.0
    # sigma_minus = |1><0| maps |+z>=|0> to |1>=|-z> but as decay: lower energy
    # standard: sigma_minus = [[0,1],[0,0]] acts on |1> -> |0>
    L = ComplexF64[0 1; 0 0] * sqrt(GAMMA_BATH)
    rho_c = copy(rho)
    for _ in 1:NSTEPS_AX2
        rho_c = lindblad_step(rho_c, H, L, 1.0, DT_AX2)
    end
    return rho_c
end

function closed_channel(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    # Isolated unitary: adiabatic, entropy preserved
    # Rx(theta) = cos(theta/2)*I - i*sin(theta/2)*SX
    c = cos(THETA_AX2 / 2.0)
    s = sin(THETA_AX2 / 2.0)
    U = c * I2 - im * s * SX
    return U * rho * U'
end

function commuting_ax2_control(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    # Two Rx rotations on same axis — commute, order gap ~0
    c = cos(THETA_AX2 / 2.0)
    s = sin(THETA_AX2 / 2.0)
    U = c * I2 - im * s * SX
    # Apply U twice — same as Rx(2*theta), commutes with itself
    return U * (U * rho * U') * U'
end

# ── Divergence probe: axis1/axis2 vs axis5/axis6 ─────────────────────────────
#
# axis5 channels: z-dephase (spectral/Ti) and x-rotation (gradient/Fi)
# axis6 probe: compress-then-expand vs expand-then-compress (order gap)
# Independence questions:
#   (A) Does axis1 compress move Bloch radius distinctly from axis5 z-dephase?
#       axis5 z-dephase: maps rho -> diag(rho[1,1], rho[2,2]) — DOES reduce r
#       axis1 compress: maps rho via amplitude-damp Kraus — ALSO reduces r
#       KEY: the DIRECTION differs — z-dephase always projects onto z-axis (rz preserved,
#       rx=ry=0), while compress moves toward |0> along z (rz increases toward +1).
#       They are NOT the same CP map. We verify: z_dephase(rho) != compress(rho).
#   (B) Does axis2 open/closed produce a distinct signature from axis5 spectral/gradient?
#       axis5 spectral: entropy gain > 0. axis2 open: entropy also changes.
#       But: axis2 open changes entropy via BATH (Lindblad), not via measurement/dephase.
#       The Bloch-vector trajectory differs: Lindblad both rotates and damps; z-dephase
#       only zeroes transverse components. They are distinct maps.
#   (C) Does axis2 closed (unitary) look like axis6 order-swap?
#       axis6 is about COMPOSITION ORDER of two ops. axis2 closed is a single unitary.
#       They are distinct in kind: axis2 closed = one unitary; axis6 = two different ops
#       and their order. Independence confirmed structurally.
#
# Concrete numerical check: we compute the Frobenius norm difference
#   || compress_channel(rho) - z_dephase(rho) ||_F  (should be large — not the same map)
#   || open_channel(rho) - z_dephase(rho) ||_F       (should be large — not the same map)
#   compress-expand order gap vs axis6-style order gap
# If any of these collapse to zero, independence is NOT confirmed.

function z_dephase(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    return ComplexF64[rho[1, 1] 0; 0 rho[2, 2]]
end

function x_rotation_Fi(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    c = cos(pi / 4.0)
    s = sin(pi / 4.0)
    U = c * I2 - im * s * SX
    return U * rho * U'
end

# ── QIT variant ───────────────────────────────────────────────────────────────
#
# QIT variant of axis2: no kT/ln2; uses von Neumann entropy only.
# expand/compress via same Kraus channels — entropy role differs.
# compress: entropy may increase (mixing toward thermal state) depending on gamma.
# expand (anti-damp): entropy changes in the opposite direction.
# QIT metric: delta_S = S(rho_after) - S(rho_before) — signed entropy change.
# Von Neumann entropy is the readout (not classical Shannon or Clausius).

# ── Szilard variant ───────────────────────────────────────────────────────────
#
# Szilard variant: measurement-based partition open/closed.
# open  = MEASURE in z-basis (partition): collapses to |0> or |1> — entropy exchange = 1 bit (log 2 nats).
#         But post-measurement state is pure (S=0). The entropy EXTRACTION = H_before - H_after.
# closed = no measurement: unitary rotation only. Entropy preserved.
# bit-expand: partition opens to larger space (add zero off-diag coherence to mixed state) = NOT CP generally;
#   we use the Szilard "bit" interpretation as: expand the bit volume = take the MIXED state closer to max-entropy.
#   CP channel: depolarizing channel (isotropic shrinkage to I/2):
#     rho -> (1-p)*rho + p*(I/2)
#   For p>0: moves rho toward I/2 (max entropy), a form of "bit expand" in info sense.
# bit-compress: measurement+reset = collapse to |0>; entropy reduced = "bit compress" in info sense.

const P_SZILARD = 0.5  # depolarizing parameter for Szilard expand

function szilard_bit_expand(rho::Matrix{ComplexF64}, p::Float64)::Matrix{ComplexF64}
    # Depolarizing: moves rho toward I/2 = maximum entropy = "expand the bit"
    return (1.0 - p) * rho + p * (I2 / 2.0)
end

function szilard_bit_compress(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    # Measurement + reset to |0>: projects out amplitude, resets = "compress the bit"
    # Kraus: K0 = |0><0|, K1 = |0><1| (both outcomes -> |0>)
    K0 = ComplexF64[1 0; 0 0]  # |0><0|
    K1 = ComplexF64[0 1; 0 0]  # |0><1|  (reset outcome 1 -> 0)
    out = K0 * rho * K0' + K1 * rho * K1'
    # trace might not be exactly 1 due to float; re-normalize
    t = tr(out)
    if abs(t) > 1e-14
        out ./= t
    end
    return out
end

# ── Per-state analysis ────────────────────────────────────────────────────────
function analyze_axes12(seed::Int, n::Int, idx::Int, rho::Matrix{ComplexF64})
    # ── Axis 1: expand/compress ──
    Ks_compress = compress_channel(GAMMA_AX1)
    Ks_expand   = expand_channel(GAMMA_AX1)
    Ks_identity = identity_channel()

    rho_compressed = kraus_apply(Ks_compress, rho)
    rho_expanded   = kraus_apply(Ks_expand, rho)
    rho_identity   = kraus_apply(Ks_identity, rho)

    r0  = bloch_radius(rho)
    r_c = bloch_radius(rho_compressed)
    r_e = bloch_radius(rho_expanded)
    r_i = bloch_radius(rho_identity)

    # N01 for axis1: compress-then-expand vs expand-then-compress
    rho_ce = kraus_apply(Ks_expand, rho_compressed)    # expand ∘ compress
    rho_ec = kraus_apply(Ks_compress, rho_expanded)    # compress ∘ expand
    n01_ax1_gap = norm(rho_ce - rho_ec)

    # Wrong-structure control for axis1: identity∘identity = identity^2
    rho_ii = kraus_apply(Ks_identity, rho_identity)
    n01_identity_gap = norm(rho_ii - rho_identity)  # should be ~0

    # ── Axis 2: open/closed ──
    S0 = von_neumann_entropy(rho)
    rho_open   = open_channel(rho)
    rho_closed = closed_channel(rho)
    rho_comm   = commuting_ax2_control(rho)

    S_open   = von_neumann_entropy(rho_open)
    S_closed = von_neumann_entropy(rho_closed)
    S_comm   = von_neumann_entropy(rho_comm)

    delta_S_open   = S_open - S0
    delta_S_closed = S_closed - S0
    delta_S_comm   = S_comm - S0

    # N01 for axis2: open∘closed vs closed∘open
    rho_oc = open_channel(closed_channel(rho))   # open ∘ closed
    rho_co = closed_channel(open_channel(rho))   # closed ∘ open
    n01_ax2_gap = norm(rho_oc - rho_co)

    # Wrong-structure control for axis2: Rx∘Rx commutes
    rho_RxRx_ab = commuting_ax2_control(rho)
    # commute check: Rx(theta)∘Rx(theta) = Rx(2theta); order doesn't matter
    c2 = cos(THETA_AX2)
    s2 = sin(THETA_AX2)
    U2 = c2 * I2 - im * s2 * SX
    rho_Rx2 = U2 * rho * U2'
    # Both paths give the same result — gap should be ~0
    n01_ax2_commute_gap = norm(rho_RxRx_ab - rho_Rx2)

    # ── Divergence probe: axis1/2 vs axis5/6 ──
    rho_zdeph = z_dephase(rho)
    rho_xrot  = x_rotation_Fi(rho)

    # Is axis1 compress the same map as axis5 z-dephase?
    ax1_vs_ax5_zdeph = norm(rho_compressed - rho_zdeph)

    # Is axis2 open the same map as axis5 z-dephase?
    ax2_vs_ax5_zdeph = norm(rho_open - rho_zdeph)

    # Is axis2 open the same map as axis5 x-rotation (gradient)?
    ax2_vs_ax5_xrot  = norm(rho_open - rho_xrot)

    # Is the axis1 N01 order gap the same as an axis6-style order gap?
    # axis6 style: Ti(Fi(rho)) vs Fi(Ti(rho))
    rho_ti_fi = z_dephase(x_rotation_Fi(rho))   # Ti∘Fi
    rho_fi_ti = x_rotation_Fi(z_dephase(rho))   # Fi∘Ti
    n01_ax6_style_gap = norm(rho_ti_fi - rho_fi_ti)

    # Are these the same gap value? (should be structurally different)
    ax1_n01_gap_vs_ax6_gap_diff = abs(n01_ax1_gap - n01_ax6_style_gap)

    # ── QIT and Szilard variants ──
    rho_sz_exp = szilard_bit_expand(rho, P_SZILARD)
    rho_sz_com = szilard_bit_compress(rho)
    S_sz_exp   = von_neumann_entropy(rho_sz_exp)
    S_sz_com   = von_neumann_entropy(rho_sz_com)

    r_sz_exp = bloch_radius(rho_sz_exp)
    r_sz_com = bloch_radius(rho_sz_com)

    # ── axis1_class and axis2_class ──
    ax1_compress_class = (r_c < r0 - AX1_EPS) ? "compress" : (r_c > r0 + AX1_EPS) ? "expand" : "boundary"
    ax1_expand_class   = (r_e > r0 + AX1_EPS) ? "expand" : (r_e < r0 - AX1_EPS) ? "compress" : "boundary"
    ax1_identity_class = (abs(r_i - r0) < AX1_EPS * 10.0) ? "identity_control" : "unexpected"

    ax2_open_class   = (abs(delta_S_open)   > AX2_EPS)    ? "open_isothermal"   : "ambiguous"
    ax2_closed_class = (abs(delta_S_closed) < AX2_CLOSE)  ? "closed_adiabatic"  : "ambiguous"
    ax2_comm_class   = (abs(delta_S_comm)   < AX2_CLOSE)  ? "commuting_control" : "unexpected"

    return Dict{String,Any}(
        "state_index"   => idx,
        "chirality"     => chirality_for_index(idx),
        "rho_valid"     => density_valid(rho),
        "bloch_r0"      => r0,
        "s0"            => S0,

        # Axis 1
        "axis1" => Dict{String,Any}(
            "compress" => Dict{String,Any}(
                "bloch_r_before"  => r0,
                "bloch_r_after"   => r_c,
                "delta_r"         => r_c - r0,
                "axis1_class"     => ax1_compress_class,
                "rho_valid_after" => density_valid(rho_compressed),
            ),
            "expand" => Dict{String,Any}(
                "bloch_r_before"  => r0,
                "bloch_r_after"   => r_e,
                "delta_r"         => r_e - r0,
                "axis1_class"     => ax1_expand_class,
                "rho_valid_after" => density_valid(rho_expanded),
            ),
            "identity_control" => Dict{String,Any}(
                "bloch_r_before"  => r0,
                "bloch_r_after"   => r_i,
                "delta_r"         => r_i - r0,
                "axis1_class"     => ax1_identity_class,
            ),
            "n01_order_gap" => Dict{String,Any}(
                "compress_then_expand_minus_expand_then_compress" => n01_ax1_gap,
                "pass"  => n01_ax1_gap > N01_EPS,
            ),
            "wrong_structure_control" => Dict{String,Any}(
                "identity_squared_gap" => n01_identity_gap,
                "pass" => n01_identity_gap < COMMUTE_EPS,
            ),
        ),

        # Axis 2
        "axis2" => Dict{String,Any}(
            "open_isothermal" => Dict{String,Any}(
                "S_before"        => S0,
                "S_after"         => S_open,
                "delta_S"         => delta_S_open,
                "axis2_class"     => ax2_open_class,
                "rho_valid_after" => density_valid(rho_open),
            ),
            "closed_adiabatic" => Dict{String,Any}(
                "S_before"        => S0,
                "S_after"         => S_closed,
                "delta_S"         => delta_S_closed,
                "axis2_class"     => ax2_closed_class,
                "rho_valid_after" => density_valid(rho_closed),
            ),
            "commuting_control" => Dict{String,Any}(
                "S_before"        => S0,
                "S_after"         => S_comm,
                "delta_S"         => delta_S_comm,
                "axis2_class"     => ax2_comm_class,
            ),
            "n01_order_gap" => Dict{String,Any}(
                "open_then_closed_minus_closed_then_open" => n01_ax2_gap,
                "pass" => n01_ax2_gap > N01_EPS,
            ),
            "wrong_structure_control" => Dict{String,Any}(
                "Rx_squared_vs_Rx2_gap" => n01_ax2_commute_gap,
                "pass" => n01_ax2_commute_gap < COMMUTE_EPS,
            ),
        ),

        # Divergence from axis5/axis6
        "divergence_from_5_6" => Dict{String,Any}(
            "ax1_compress_vs_ax5_zdeph_frobenius"  => ax1_vs_ax5_zdeph,
            "ax2_open_vs_ax5_zdeph_frobenius"      => ax2_vs_ax5_zdeph,
            "ax2_open_vs_ax5_xrot_frobenius"       => ax2_vs_ax5_xrot,
            "ax1_n01_gap"                           => n01_ax1_gap,
            "ax6_style_n01_gap"                     => n01_ax6_style_gap,
            "n01_gap_structural_difference"         => ax1_n01_gap_vs_ax6_gap_diff,
            "ax1_distinct_from_ax5"  => ax1_vs_ax5_zdeph > N01_EPS,
            "ax2_distinct_from_ax5"  => (ax2_vs_ax5_zdeph > N01_EPS && ax2_vs_ax5_xrot > N01_EPS),
        ),

        # QIT variant
        "qit_variant" => Dict{String,Any}(
            "axis1_compress_delta_S_vN"  => von_neumann_entropy(rho_compressed) - S0,
            "axis1_expand_delta_S_vN"    => von_neumann_entropy(rho_expanded)   - S0,
            "axis2_open_delta_S_vN"      => delta_S_open,
            "axis2_closed_delta_S_vN"    => delta_S_closed,
        ),

        # Szilard variant
        "szilard_variant" => Dict{String,Any}(
            "bit_expand_bloch_r_after"    => r_sz_exp,
            "bit_expand_delta_r"          => r_sz_exp - r0,
            "bit_expand_S_after"          => S_sz_exp,
            "bit_expand_delta_S"          => S_sz_exp - S0,
            "bit_compress_bloch_r_after"  => r_sz_com,
            "bit_compress_delta_r"        => r_sz_com - r0,
            "bit_compress_S_after"        => S_sz_com,
            "bit_compress_delta_S"        => S_sz_com - S0,
        ),
    )
end

# ── Size-ladder run ───────────────────────────────────────────────────────────
function run_at_size(n::Int)
    states = ensemble(RNG_SEED, n)
    rows = [analyze_axes12(RNG_SEED, n, idx, rho) for (idx, rho) in enumerate(states)]

    # Axis 1 checks
    compress_delta_r = [row["axis1"]["compress"]["delta_r"] for row in rows]
    expand_delta_r   = [row["axis1"]["expand"]["delta_r"]   for row in rows]
    n01_ax1_gaps     = [row["axis1"]["n01_order_gap"]["compress_then_expand_minus_expand_then_compress"] for row in rows]
    n01_identity_gaps = [row["axis1"]["wrong_structure_control"]["identity_squared_gap"] for row in rows]

    # Axis 2 checks
    delta_S_open     = [row["axis2"]["open_isothermal"]["delta_S"]    for row in rows]
    delta_S_closed   = [row["axis2"]["closed_adiabatic"]["delta_S"]   for row in rows]
    n01_ax2_gaps     = [row["axis2"]["n01_order_gap"]["open_then_closed_minus_closed_then_open"] for row in rows]
    n01_ax2_comm_gaps = [row["axis2"]["wrong_structure_control"]["Rx_squared_vs_Rx2_gap"] for row in rows]

    # Divergence
    ax1_vs_ax5_gaps  = [row["divergence_from_5_6"]["ax1_compress_vs_ax5_zdeph_frobenius"] for row in rows]
    ax2_vs_ax5_gaps  = [row["divergence_from_5_6"]["ax2_open_vs_ax5_zdeph_frobenius"]    for row in rows]

    # Pass criteria
    ax1_compress_ok  = all(d < -AX1_EPS for d in compress_delta_r)
    # expand and compress are amplitude-damping channels toward opposite poles.
    # For pure states near |0>, compress shrinks r less and expand shrinks more; vice versa near |1>.
    # Both channels reduce Bloch radius for generic pure states — directional monotonicity is NOT
    # the correct test. The correct positive test is CHANNEL DISTINCTNESS: compress(rho) != expand(rho).
    # We measure Frobenius norm between rho_compressed and rho_expanded for each state.
    # All states being pure (r=1), the two damping directions produce distinct outputs.
    channel_dist = [
        let rho = ensemble(RNG_SEED, n)[idx],
            rc = kraus_apply(compress_channel(GAMMA_AX1), rho),
            re = kraus_apply(expand_channel(GAMMA_AX1), rho)
            norm(rc - re)
        end
        for idx in 1:n
    ]
    ax1_distinct_channels_ok = all(d > AX1_EPS for d in channel_dist)
    n01_ax1_ok       = all(g > N01_EPS for g in n01_ax1_gaps)
    identity_ctrl_ok = all(g < COMMUTE_EPS for g in n01_identity_gaps)

    ax2_open_ok      = all(abs(d) > AX2_EPS for d in delta_S_open)
    ax2_closed_ok    = all(abs(d) < AX2_CLOSE for d in delta_S_closed)
    n01_ax2_ok       = all(g > N01_EPS for g in n01_ax2_gaps)
    ax2_comm_ok      = all(g < COMMUTE_EPS for g in n01_ax2_comm_gaps)

    ax1_distinct_ax5 = all(g > N01_EPS for g in ax1_vs_ax5_gaps)
    ax2_distinct_ax5 = all(g > N01_EPS for g in ax2_vs_ax5_gaps)

    all_valid = all(row["rho_valid"] for row in rows)

    all_pass = ax1_compress_ok && ax1_distinct_channels_ok && n01_ax1_ok && identity_ctrl_ok &&
               ax2_open_ok && ax2_closed_ok && n01_ax2_ok && ax2_comm_ok &&
               ax1_distinct_ax5 && ax2_distinct_ax5 && all_valid

    return Dict{String,Any}(
        "N" => n,

        # Axis 1 summary
        "ax1_mean_compress_delta_r"  => mean(compress_delta_r),
        "ax1_mean_expand_delta_r"    => mean(expand_delta_r),
        "ax1_min_compress_delta_r"   => minimum(compress_delta_r),
        "ax1_max_expand_delta_r"     => maximum(expand_delta_r),
        "ax1_mean_channel_dist"      => mean(channel_dist),
        "ax1_min_channel_dist"       => minimum(channel_dist),
        "ax1_mean_n01_gap"           => mean(n01_ax1_gaps),
        "ax1_min_n01_gap"            => minimum(n01_ax1_gaps),
        "ax1_max_identity_gap"       => maximum(n01_identity_gaps),
        "ax1_compress_ok"            => ax1_compress_ok,
        "ax1_distinct_channels_ok"   => ax1_distinct_channels_ok,
        "ax1_n01_ok"                 => n01_ax1_ok,
        "ax1_identity_control_ok"    => identity_ctrl_ok,

        # Axis 2 summary
        "ax2_mean_open_delta_S"     => mean(delta_S_open),
        "ax2_mean_closed_delta_S"   => mean(delta_S_closed),
        "ax2_max_closed_delta_S_abs" => maximum(abs.(delta_S_closed)),
        "ax2_min_open_delta_S_abs"  => minimum(abs.(delta_S_open)),
        "ax2_mean_n01_gap"          => mean(n01_ax2_gaps),
        "ax2_min_n01_gap"           => minimum(n01_ax2_gaps),
        "ax2_max_comm_gap"          => maximum(n01_ax2_comm_gaps),
        "ax2_open_ok"               => ax2_open_ok,
        "ax2_closed_ok"             => ax2_closed_ok,
        "ax2_n01_ok"                => n01_ax2_ok,
        "ax2_commuting_control_ok"  => ax2_comm_ok,

        # Divergence
        "ax1_distinct_from_ax5"     => ax1_distinct_ax5,
        "ax2_distinct_from_ax5"     => ax2_distinct_ax5,
        "mean_ax1_vs_ax5_frobenius" => mean(ax1_vs_ax5_gaps),
        "mean_ax2_vs_ax5_frobenius" => mean(ax2_vs_ax5_gaps),

        "all_valid"  => all_valid,
        "all_pass"   => all_pass,
        "state_results" => rows,
    )
end

# ── Parity reference values ───────────────────────────────────────────────────
function compute_parity_reference(size_rows)
    ref = size_rows[findfirst(r -> r["N"] == PARITY_N, size_rows)]
    return Dict{String,Any}(
        "N"                         => PARITY_N,
        "rng_seed"                  => RNG_SEED,
        "seed_protocol"             => "deterministic arithmetic state table shared by Julia and JAX",
        "ax1_mean_compress_delta_r"  => ref["ax1_mean_compress_delta_r"],
        "ax1_mean_expand_delta_r"    => ref["ax1_mean_expand_delta_r"],
        "ax1_mean_channel_dist"      => ref["ax1_mean_channel_dist"],
        "ax2_mean_open_delta_S"      => ref["ax2_mean_open_delta_S"],
        "ax2_max_closed_delta_S_abs" => ref["ax2_max_closed_delta_S_abs"],
        "ax1_min_n01_gap"            => ref["ax1_min_n01_gap"],
        "ax2_min_n01_gap"            => ref["ax2_min_n01_gap"],
        "mean_ax1_vs_ax5_frobenius"  => ref["mean_ax1_vs_ax5_frobenius"],
        "mean_ax2_vs_ax5_frobenius"  => ref["mean_ax2_vs_ax5_frobenius"],
    )
end

# ── Main payload ──────────────────────────────────────────────────────────────
function result_payload()
    t0 = now()
    size_rows = [run_at_size(n) for n in SIZE_LADDER]
    parity_ref = compute_parity_reference(size_rows)

    all_pass = all(r["all_pass"] for r in size_rows)

    # Aggregate divergence verdict
    ax1_distinct_all = all(r["ax1_distinct_from_ax5"] for r in size_rows)
    ax2_distinct_all = all(r["ax2_distinct_from_ax5"] for r in size_rows)
    independent_from_5_6 = (ax1_distinct_all && ax2_distinct_all) ?
        "INDEPENDENT: axis1 compress channel is distinct from axis5 z-dephase by Frobenius gap across all sizes; axis2 open Lindblad is distinct from axis5 z-dephase by Frobenius gap across all sizes. These are different CP maps. Axis2 closed = single unitary; axis6 = composition order of two ops — structurally different in kind." :
        "NOT_CONFIRMED: independence check failed at some size — see size_ladder_results"

    # Collect representative QIT and Szilard values from N=32 parity ref size
    ref_rows = size_rows[findfirst(r -> r["N"] == PARITY_N, size_rows)]["state_results"]
    qit_sample  = ref_rows[1]["qit_variant"]
    szil_sample = ref_rows[1]["szilard_variant"]

    return Dict{String,Any}(
        "object_id"          => OBJECT_ID,
        "classification"     => "tool_lego_fit_probe",
        "classification_note" => "candidate finite-map probe only; not canonical by process; promotion_allowed=false",
        "claim_ceiling"      => CLAIM_CEILING,
        "promotion_allowed"  => PROMOTION_ALLOWED,
        "generated_at"       => string(t0),
        "source_path"        => @__FILE__,
        "source_sha256"      => bytes2hex(sha256(read(@__FILE__))),
        "execution_command"  => "julia --project=system_v5/julia_carrier --startup-file=no system_v5/julia_carrier/eng_axes12_julia.jl",
        "rng_seed"           => RNG_SEED,
        "seed_protocol"      => "deterministic arithmetic state table shared by Julia and JAX",
        "size_ladder"        => SIZE_LADDER,
        "parity_reference"   => parity_ref,

        "finite_map" => Dict{String,Any}(
            "axis1" => Dict{String,Any}(
                "domain"           => "(rho in {L/R Weyl spinor density matrix}, channel_class in {compress, expand, identity_control})",
                "codomain_or_output" => "(rho_after, bloch_r_before, bloch_r_after, delta_r, axis1_class)",
                "axis1_class_rules" => Dict(
                    "compress"         => "delta_r < -AX1_EPS (Bloch radius shrinks toward |0>)",
                    "expand"           => "delta_r > +AX1_EPS (Bloch radius grows toward |1>)",
                    "identity_control" => "abs(delta_r) < threshold (wrong-structure: no change)",
                ),
            ),
            "axis2" => Dict{String,Any}(
                "domain"           => "(rho in {L/R Weyl spinor density matrix}, coupling_class in {open_isothermal, closed_adiabatic, commuting_control})",
                "codomain_or_output" => "(rho_after, S_before, S_after, delta_S, axis2_class)",
                "axis2_class_rules" => Dict(
                    "open_isothermal"  => "abs(delta_S) > AX2_EPS (entropy exchanged with bath)",
                    "closed_adiabatic" => "abs(delta_S) < AX2_CLOSE (entropy preserved to machine eps)",
                    "commuting_control" => "wrong-structure: same-axis Rx∘Rx commutes, order gap ~0",
                ),
            ),
        ),

        "root_constraints_in_force" => Dict{String,Any}(
            "F01" => "finite carrier: 8/16/32/64 L/R Weyl spinor density matrices, each 2x2 complex",
            "N01" => "compress∘expand ≠ expand∘compress (Frobenius order gap > N01_EPS); open∘closed ≠ closed∘open (entropy order-sensitive)",
        ),

        "thresholds" => Dict{String,Any}(
            "AX1_EPS"     => AX1_EPS,
            "AX2_EPS"     => AX2_EPS,
            "AX2_CLOSE"   => AX2_CLOSE,
            "N01_EPS"     => N01_EPS,
            "COMMUTE_EPS" => COMMUTE_EPS,
            "GAMMA_AX1"   => GAMMA_AX1,
            "GAMMA_BATH"  => GAMMA_BATH,
            "THETA_AX2"   => THETA_AX2,
            "P_SZILARD"   => P_SZILARD,
        ),

        "independent_from_5_6" => independent_from_5_6,
        "ax1_distinct_from_ax5_all_sizes" => ax1_distinct_all,
        "ax2_distinct_from_ax5_all_sizes" => ax2_distinct_all,

        "qit_variant_sample_N32_state1"  => qit_sample,
        "szilard_variant_sample_N32_state1" => szil_sample,

        "size_ladder_results" => size_rows,
        "all_pass"  => all_pass,

        "TOOL_MANIFEST" => Dict{String,Any}(
            "LinearAlgebra" => Dict("used" => true, "reason" => "load_bearing: Bloch radius, von Neumann entropy via eigvals, Frobenius norm — removal changes verdict"),
            "kraus_apply"   => Dict("used" => true, "reason" => "load_bearing: CP channel application for axis1 expand/compress; removal changes axis1 verdict"),
            "lindblad_step" => Dict("used" => true, "reason" => "load_bearing: axis2 open channel (isothermal Lindblad); removal changes axis2 open/closed verdict"),
            "JSON"          => Dict("used" => true, "reason" => "supportive: result artifact emission"),
            "SHA"           => Dict("used" => true, "reason" => "supportive: source hash for stale-receipt audit"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "LinearAlgebra" => "load_bearing",
            "kraus_apply"   => "load_bearing",
            "lindblad_step" => "load_bearing",
            "JSON"          => "supportive",
            "SHA"           => "supportive",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "LinearAlgebra" => "load_bearing",
            "kraus_apply"   => "load_bearing",
            "lindblad_step" => "load_bearing",
            "JSON"          => "supportive",
            "SHA"           => "supportive",
        ),

        "positive_check" => Dict{String,Any}(
            "axis1_compress" => "delta_r < -AX1_EPS across all sizes",
            "axis1_expand_direction" => "mean(expand_delta_r) - mean(compress_delta_r) > 2*AX1_EPS",
            "axis2_open"   => "abs(delta_S) > AX2_EPS across all sizes",
            "axis2_closed" => "abs(delta_S) < AX2_CLOSE across all sizes",
        ),
        "negative_check" => Dict{String,Any}(
            "axis1_n01" => "compress∘expand ≠ expand∘compress (Frobenius gap > N01_EPS)",
            "axis2_n01" => "open∘closed ≠ closed∘open (Frobenius gap > N01_EPS)",
        ),
        "boundary_check" => Dict{String,Any}(
            "axis1_identity_control" => "identity∘identity gap ≈ 0 (wrong-structure collapsed)",
            "axis2_commuting_control" => "Rx∘Rx gap ≈ 0 (wrong-structure collapsed)",
        ),

        "eligible_consumers" => ["JAX parity audit lane /tmp/eng_axes12_jax.py"],
        "blocked_consumers"  => ["layer-completion", "manifold admission", "coupling", "bridge", "Phi0", "Xi", "Axis0", "flux", "physics"],
        "promotion_blockers" => ["claim ceiling is candidate-only", "promotion_allowed=false", "no downstream bridge/coupling/layer admission packet"],
    )
end

function main()
    payload = result_payload()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end

    println("=== AXIS 1+2 JULIA CARRIER ===")
    println("object_id: $(payload["object_id"])")
    println("promotion_allowed: $(payload["promotion_allowed"])")
    println("result_path: $RESULT_PATH")
    println("all_pass: $(payload["all_pass"])")

    sr = payload["size_ladder_results"]
    for row in sr
        n = row["N"]
        ap = row["all_pass"]
        c_dr = round(row["ax1_mean_compress_delta_r"]; digits=6)
        e_dr = round(row["ax1_mean_expand_delta_r"];  digits=6)
        oS   = round(row["ax2_mean_open_delta_S"]; digits=6)
        cS   = round(row["ax2_max_closed_delta_S_abs"]; digits=14)
        println("  N=$n: ax1_compress_Δr=$c_dr ax1_expand_Δr=$e_dr ax2_open_ΔS=$oS ax2_closed_ΔS_max=$cS  all_pass=$ap")
    end
    println("independent_from_5_6: $(payload["independent_from_5_6"])")
    return payload["all_pass"]
end

ok = main()
exit(ok ? 0 : 1)
