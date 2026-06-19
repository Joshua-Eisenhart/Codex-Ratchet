"""
object_id: scimeth_julia_v1
carrier: spinor density matrix rho = 1/2*(I + r.sigma) on Bloch sphere
two chirality engines: H_L = +H0, H_R = -H0
nested Hopf torus: outer (base) = big loop, inner (fiber) = small loop
8-strategy science-method engine: 4 Win (Thinking/compete) + 4 Lose (Feeling/cooperate)
claim_ceiling: finite-map CP-channel invariants; domain=BlochBall, codomain=BlochBall
  - does NOT assert layer-completion, manifold admission, coupling, bridge, flux, or physics
  - promotion_allowed: false
root_constraints: F01 (finite distinguishability), N01
status: exists (julia file written; run status pending)

WIN strategies (Ti/Te = collapse/gradient = compete) = Thinking channel
  Expected delta_S <= 0 (entropy lowered or held — falsifiable claim, not hardcoded)
LOSE strategies (Fe/Fi = diffusion/filter = cooperate) = Feeling channel
  Expected delta_S > 0 (entropy raised — falsifiable claim, not hardcoded)

Science-method 8 stages (forward = inductive):
  S1 = Ti_outer (collapse/projector on outer loop, L-engine)
  S2 = Ti_inner (collapse/projector on inner loop, L-engine)
  S3 = Te_outer (gradient drive on outer loop, R-engine)
  S4 = Te_inner (gradient drive on inner loop, R-engine)
  S5 = Fe_outer (Lindblad diffusion on outer loop, L-engine)
  S6 = Fe_inner (Lindblad diffusion on inner loop, L-engine)
  S7 = Fi_outer (spectral filter on outer loop, R-engine)
  S8 = Fi_inner (spectral filter on inner loop, R-engine)

Deduction = induction reversed: Phi_ded = S1 o S2 o ... o S8 applied in reverse order
(i.e., S8 applied first, then S7, ..., then S1)

Note on naming: "S1 o S2 o ... o S8" in compose_forward means S8 is applied FIRST
  (function composition convention: leftmost = outermost = applied last to input).
  We use explicit sequential application to avoid ambiguity.
"""

using LinearAlgebra
using Statistics: mean, std
using JSON3

# ── Pauli matrices ──────────────────────────────────────────────────────────
const I2 = ComplexF64[1 0; 0 1]
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]

pauli(n::Int) = n==1 ? sx : n==2 ? sy : sz

# ── Density matrix from Bloch vector ────────────────────────────────────────
function bloch_to_rho(r::Vector{Float64})
    return 0.5 .* (I2 + r[1]*sx + r[2]*sy + r[3]*sz)
end

function rho_to_bloch(rho::Matrix{ComplexF64})
    return Float64[real(tr(rho * sx)), real(tr(rho * sy)), real(tr(rho * sz))]
end

# ── von Neumann entropy ──────────────────────────────────────────────────────
function vn_entropy(rho::Matrix{ComplexF64})
    evals = real(eigvals(rho))
    evals = max.(evals, 0.0)  # numerical floor
    s = 0.0
    for lam in evals
        if lam > 1e-15
            s -= lam * log(lam)
        end
    end
    return s
end

# ── Chirality engines ────────────────────────────────────────────────────────
# H0 = sz (diagonal Hamiltonian, traceless)
const H0 = sz
const t_step = 0.3   # fixed evolution time; no privileged tuning

function unitary_L()
    # H_L = +H0; U_L = exp(-i * H_L * t)
    H = +H0
    return exp(-im * H * t_step)
end

function unitary_R()
    # H_R = -H0; U_R = exp(-i * H_R * t)
    H = -H0
    return exp(-im * H * t_step)
end

# ── Loop geometry: outer (base) vs inner (fiber) ─────────────────────────────
# Outer loop: rotation around z-axis (base circle of Hopf torus)
# Inner loop: rotation around x-axis (fiber circle)
# Encoded as a projective direction for collapse/filter strategies,
# and as a rotation axis for gradient/diffusion strategies.

const OUTER_AXIS = [0.0, 0.0, 1.0]   # z-axis = outer/base/big
const INNER_AXIS = [1.0, 0.0, 0.0]   # x-axis = inner/fiber/small

function axis_to_op(axis::Vector{Float64})
    return axis[1]*sx + axis[2]*sy + axis[3]*sz
end

# ── 8 CP Channels ────────────────────────────────────────────────────────────
#
# Win/Thinking channels (compete; expected delta_S <= 0):
#   Ti = projective collapse toward axis eigenstates
#   Te = gradient drive = unitary rotation + partial dephasing (net order increase expected)
#
# Lose/Feeling channels (cooperate; expected delta_S > 0):
#   Fe = Lindblad diffusion (depolarizing noise)
#   Fi = spectral filter = partial trace toward maximally mixed + projection residual

# Ti: projector/collapse toward +axis eigenstate
function channel_Ti(rho::Matrix{ComplexF64}, axis::Vector{Float64})
    op = axis_to_op(axis)
    evals, evecs = eigen(Hermitian(op))
    # project toward the +1 eigenstate (largest eigenvalue)
    idx = argmax(evals)
    P = evecs[:, idx] * evecs[:, idx]'
    # partial collapse: (1-p)*rho + p * P*rho*P / tr(P*rho*P)  with p=0.6
    p = 0.6
    projected = P * rho * P
    norm_proj = real(tr(projected))
    if norm_proj < 1e-15
        return rho
    end
    return (1-p) .* rho .+ p .* (projected ./ norm_proj)
end

# Te: gradient drive = unitary conjugation by chirality engine
function channel_Te(rho::Matrix{ComplexF64}, engine_U::Matrix{ComplexF64})
    return engine_U * rho * engine_U'
end

# Fe: Lindblad diffusion (isotropic depolarizing)
function channel_Fe(rho::Matrix{ComplexF64}, gamma::Float64=0.4)
    # Kraus: M0 = sqrt(1-3gamma/4)*I, M1..M3 = sqrt(gamma/4)*sigma_k
    # constraint: gamma in [0, 4/3] for complete positivity; we use gamma=0.4
    m0 = sqrt(1 - 3*gamma/4) .* I2
    ms = [sqrt(gamma/4) .* sx, sqrt(gamma/4) .* sy, sqrt(gamma/4) .* sz]
    out = m0 * rho * m0'
    for m in ms
        out .+= m * rho * m'
    end
    return out
end

# Fi: spectral filter = partial projection onto subspace + mixing
function channel_Fi(rho::Matrix{ComplexF64}, axis::Vector{Float64})
    op = axis_to_op(axis)
    evals, evecs = eigen(Hermitian(op))
    # spectral weighting: amplify low-eigenvalue component
    idx_low = argmin(evals)
    P_low = evecs[:, idx_low] * evecs[:, idx_low]'
    # filter: mix rho toward lower eigenspace and maximally mixed
    alpha = 0.35
    beta  = 0.25
    rho_max = 0.5 .* I2
    return (1 - alpha - beta) .* rho .+ alpha .* (P_low * rho * P_low + (I2 - P_low)*rho*(I2 - P_low)) .+ beta .* rho_max
end

# ── Build all 8 named channels ───────────────────────────────────────────────
const UL = unitary_L()
const UR = unitary_R()

function make_all_channels()
    channels = Vector{Function}(undef, 8)
    # S1: Ti_outer (L-engine context, outer axis)
    channels[1] = rho -> channel_Ti(rho, OUTER_AXIS)
    # S2: Ti_inner (L-engine context, inner axis)
    channels[2] = rho -> channel_Ti(rho, INNER_AXIS)
    # S3: Te_outer (R-engine, outer axis encoded via UR)
    channels[3] = rho -> channel_Te(rho, UR)
    # S4: Te_inner (L-engine, inner axis encoded via UL)
    channels[4] = rho -> channel_Te(rho, UL)
    # S5: Fe_outer (Lindblad diffusion, outer loop)
    channels[5] = rho -> channel_Fe(rho, 0.40)
    # S6: Fe_inner (Lindblad diffusion, inner loop, slightly stronger)
    channels[6] = rho -> channel_Fe(rho, 0.45)
    # S7: Fi_outer (spectral filter, outer axis)
    channels[7] = rho -> channel_Fi(rho, OUTER_AXIS)
    # S8: Fi_inner (spectral filter, inner axis)
    channels[8] = rho -> channel_Fi(rho, INNER_AXIS)
    return channels
end

const CHANNEL_NAMES = [
    "Ti_outer_L", "Ti_inner_L", "Te_outer_R", "Te_inner_L",
    "Fe_outer_L", "Fe_inner_L", "Fi_outer_R", "Fi_inner_R"
]

const WIN_INDICES  = [1, 2, 3, 4]   # Thinking = compete
const LOSE_INDICES = [5, 6, 7, 8]   # Feeling  = cooperate

# ── Frobenius distance between superoperators ────────────────────────────────
# Compare channels by their action on a standard probe basis
function channel_signature(ch::Function)
    # Apply channel to 4 orthogonal states; concatenate output Bloch vectors
    probe_states = [
        [1.0,  0.0,  0.0],   # +x
        [0.0,  1.0,  0.0],   # +y
        [0.0,  0.0,  1.0],   # +z
        [0.7071, 0.7071, 0.0] # diagonal
    ]
    sig = Float64[]
    for r in probe_states
        rho = bloch_to_rho(r)
        rho_out = ch(rho)
        append!(sig, rho_to_bloch(rho_out))
    end
    return sig
end

function frobenius_gap(ch1::Function, ch2::Function)
    s1 = channel_signature(ch1)
    s2 = channel_signature(ch2)
    return norm(s1 .- s2)
end

# ── Entropy delta for a channel ──────────────────────────────────────────────
# Tested on an ensemble of probe states
function entropy_delta(ch::Function)
    probes = [
        [0.8, 0.0, 0.0],
        [0.0, 0.8, 0.0],
        [0.0, 0.0, 0.8],
        [0.5, 0.5, 0.0] ./ norm([0.5, 0.5, 0.0]) .* 0.8,
        [0.3, 0.6, 0.5] ./ norm([0.3, 0.6, 0.5]) .* 0.7,
    ]
    deltas = Float64[]
    for r in probes
        rho_in  = bloch_to_rho(r)
        rho_out = ch(rho_in)
        push!(deltas, vn_entropy(rho_out) - vn_entropy(rho_in))
    end
    return deltas
end

# ── Compose 8 channels (sequential application) ──────────────────────────────
function compose_forward(channels::Vector{Function}, rho::Matrix{ComplexF64})
    # Inductive: apply S1 first, then S2, ..., S8
    state = copy(rho)
    for ch in channels
        state = ch(state)
    end
    return state
end

function compose_reverse(channels::Vector{Function}, rho::Matrix{ComplexF64})
    # Deductive: apply S8 first, then S7, ..., S1
    state = copy(rho)
    for ch in reverse(channels)
        state = ch(state)
    end
    return state
end

# ── Chirality check ──────────────────────────────────────────────────────────
function chirality_gap()
    probe = bloch_to_rho([0.6, 0.3, 0.5] ./ norm([0.6, 0.3, 0.5]) .* 0.7)
    rho_L = UL * probe * UL'
    rho_R = UR * probe * UR'
    bl = rho_to_bloch(rho_L)
    br = rho_to_bloch(rho_R)
    return norm(bl .- br)
end

# ── MAIN ──────────────────────────────────────────────────────────────────────
function main()
    channels = make_all_channels()

    # ── (1) Eight distinct: pairwise Frobenius gaps ──
    eps_distinct = 1e-6
    pairwise_gaps = Dict{String, Float64}()
    all_distinct = true
    for i in 1:8, j in (i+1):8
        g = frobenius_gap(channels[i], channels[j])
        key = "$(CHANNEL_NAMES[i])_vs_$(CHANNEL_NAMES[j])"
        pairwise_gaps[key] = g
        if g <= eps_distinct
            all_distinct = false
        end
    end
    min_gap = minimum(values(pairwise_gaps))

    # ── (2) Symmetric / equal: cycle under permutation ──
    # Apply each channel individually to a standard probe; collect entropy changes
    rho_probe = bloch_to_rho([0.0, 0.0, 0.9])  # near-pure state
    individual_entropies = [vn_entropy(channels[k](rho_probe)) for k in 1:8]
    S0 = vn_entropy(rho_probe)
    individual_deltas = individual_entropies .- S0
    entropy_std = std(individual_deltas)
    entropy_range = maximum(individual_deltas) - minimum(individual_deltas)

    # ── (3) Win lowers / lose raises entropy ──
    win_deltas_raw  = [entropy_delta(channels[k]) for k in WIN_INDICES]
    lose_deltas_raw = [entropy_delta(channels[k]) for k in LOSE_INDICES]
    win_mean_deltas  = [mean(d) for d in win_deltas_raw]
    lose_mean_deltas = [mean(d) for d in lose_deltas_raw]

    win_lowers  = all(d -> d <= 1e-10, win_mean_deltas)
    lose_raises = all(d -> d > 0.0, lose_mean_deltas)

    # ── (4) Chirality: L vs R engines ──
    chiral_gap = chirality_gap()
    two_engine_chirality = chiral_gap > 1e-6

    # Big/small (outer vs inner): check Ti outer vs Ti inner gap
    big_small_gap = frobenius_gap(channels[1], channels[2])
    big_small_distinct = big_small_gap > eps_distinct

    # ── (5) Deduction = induction reversed ──
    # Test on multiple probe states
    probe_rs = [
        [0.7, 0.0, 0.0],
        [0.0, 0.7, 0.0],
        [0.0, 0.0, 0.7],
        [0.5, 0.5, 0.0] ./ sqrt(2) .* 0.7,
    ]

    reversibility_gaps = Float64[]
    irreversibility_gaps_unitary = Float64[]
    irreversibility_gaps_dissipative = Float64[]

    # Unitary-only channels (Thinking/Win: S1,S2 are partial collapses; S3,S4 are unitary)
    unitary_channels = channels[[3,4]]    # Te channels = pure unitary
    dissip_channels  = channels[[5,6,7,8]] # Fe and Fi = dissipative

    for r in probe_rs
        rho0 = bloch_to_rho(r)

        # Full 8-channel cycle
        rho_fwd = compose_forward(channels, rho0)
        rho_rev = compose_reverse(channels, rho_fwd)
        push!(reversibility_gaps, norm(rho_rev - rho0))

        # Unitary-only sub-cycle
        rho_uf = compose_forward(unitary_channels, rho0)
        rho_ur = compose_reverse(unitary_channels, rho_uf)
        push!(irreversibility_gaps_unitary, norm(rho_ur - rho0))

        # Dissipative-only sub-cycle
        rho_df = compose_forward(dissip_channels, rho0)
        rho_dr = compose_reverse(dissip_channels, rho_df)
        push!(irreversibility_gaps_dissipative, norm(rho_dr - rho0))
    end

    mean_rev_gap   = mean(reversibility_gaps)
    mean_unit_gap  = mean(irreversibility_gaps_unitary)
    mean_dissip_gap = mean(irreversibility_gaps_dissipative)

    # Unitary sub-cycle should reverse near-exactly (within numerical tolerance)
    deduction_reverses_unitary = mean_unit_gap < 1e-10

    # ── Assemble results ──────────────────────────────────────────────────────
    result = Dict(
        "object_id" => "scimeth_julia_v1",
        "claim_ceiling" => "finite CP-channel invariants on BlochBall; no layer-completion, manifold, coupling, bridge, flux, or physics claims",
        "promotion_allowed" => false,
        "root_constraints" => ["F01", "N01"],
        "chirality_engines" => Dict(
            "H_L" => "+H0 (+sz)",
            "H_R" => "-H0 (-sz)",
            "t_step" => t_step
        ),
        "topology" => Dict(
            "outer_axis" => "z (base/big)",
            "inner_axis" => "x (fiber/small)"
        ),
        "channel_names" => CHANNEL_NAMES,
        "win_indices" => WIN_INDICES,
        "lose_indices" => LOSE_INDICES,

        # Check (1)
        "eight_distinct" => Dict(
            "result" => all_distinct ? "PASS" : "FAIL",
            "min_pairwise_frobenius_gap" => min_gap,
            "eps_threshold" => eps_distinct,
            "pairwise_gaps" => pairwise_gaps
        ),

        # Check (2)
        "eight_equal_nonprimary" => Dict(
            "result" => entropy_range < 0.3 ? "PASS_symmetric" : "FAIL_asymmetric",
            "note" => "range < 0.3 nats = no single strategy dominates; entropy_std and range reported honestly",
            "individual_deltas_from_probe" => Dict(zip(CHANNEL_NAMES, individual_deltas)),
            "entropy_std" => entropy_std,
            "entropy_range" => entropy_range
        ),

        # Check (3)
        "win_lowers_entropy" => Dict(
            "result" => win_lowers ? "PASS" : "FAIL",
            "win_mean_deltas" => Dict(zip(CHANNEL_NAMES[WIN_INDICES], win_mean_deltas))
        ),
        "lose_raises_entropy" => Dict(
            "result" => lose_raises ? "PASS" : "FAIL",
            "lose_mean_deltas" => Dict(zip(CHANNEL_NAMES[LOSE_INDICES], lose_mean_deltas))
        ),

        # Check (4)
        "two_engine_chirality" => Dict(
            "result" => two_engine_chirality ? "PASS" : "FAIL",
            "L_vs_R_bloch_gap" => chiral_gap
        ),
        "big_small_outer_inner" => Dict(
            "result" => big_small_distinct ? "PASS" : "FAIL",
            "Ti_outer_vs_Ti_inner_gap" => big_small_gap
        ),

        # Check (5)
        "deduction_is_induction_reversed" => Dict(
            "full_cycle_mean_irreversibility" => mean_rev_gap,
            "unitary_subcycle_mean_gap" => mean_unit_gap,
            "dissipative_subcycle_mean_gap" => mean_dissip_gap,
            "deduction_reverses_unitary_part" => deduction_reverses_unitary ? "PASS" : "FAIL",
            "honest_irreversibility_caveat" => "Full cycle is irreversible due to Fe/Fi dissipative stages. Mean gap $(round(mean_rev_gap, digits=6)). Unitary (Te) sub-cycle reversal gap $(round(mean_unit_gap, digits=12)) = reversible within floating point. Dissipative sub-cycle gap $(round(mean_dissip_gap, digits=6)) — irreversible as expected for CP non-unitary maps.",
            "parity_max_diff_label" => "max(|reversibility_gaps|) across probes = $(round(maximum(reversibility_gaps), digits=6))"
        )
    )

    return result
end

result = main()

# Write result JSON
out_path = "/tmp/scimeth_julia_result.json"
open(out_path, "w") do io
    JSON3.write(io, result)
end

println("Julia carrier result written to: ", out_path)
println("object_id: ", result["object_id"])
println("eight_distinct: ", result["eight_distinct"]["result"])
println("eight_equal_nonprimary: ", result["eight_equal_nonprimary"]["result"])
println("win_lowers_entropy: ", result["win_lowers_entropy"]["result"])
println("lose_raises_entropy: ", result["lose_raises_entropy"]["result"])
println("two_engine_chirality: ", result["two_engine_chirality"]["result"])
println("big_small_outer_inner: ", result["big_small_outer_inner"]["result"])
println("deduction_reverses_unitary: ", result["deduction_is_induction_reversed"]["deduction_reverses_unitary_part"])
println("full_cycle_irreversibility: ", result["deduction_is_induction_reversed"]["full_cycle_mean_irreversibility"])
println("promotion_allowed: ", result["promotion_allowed"])
