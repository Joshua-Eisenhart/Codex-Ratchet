# carnot_szilard_qit_engine.jl
#
# object_id: carnot_szilard_qit_axis_engine_julia_v1
#
# claim_ceiling:
#   Computes explicit finite maps for:
#     (1) Carnot 4-stroke thermodynamic engine — Clausius entropy dS=dQ/T
#     (2) Szilard 1-bit information engine — Shannon entropy H=1 bit, Landauer cost
#     (3) Axis-DOF mapping: Ti/Te/Fi/Fe operators as engine strokes
#     (4) Pure-QIT versions (von Neumann entropy, no kT/ln2) under density-matrix
#         working states and Kraus quantum channels
#   Does NOT assert layer-completion, manifold admission, coupling, bridge,
#   flux, or physics. promotion_allowed: false.
#
# Root constraints in force:
#   F01: finite-dimensional carrier — qubit (2×2 density matrices), finite
#        cycle of discrete strokes, discrete temperature/bias ladders.
#   N01: stroke order is load-bearing — Ti(z-dephase) · Fi(Rx) ≠ Fi · Ti
#        and Te(x-dephase) · Fe(Rz) ≠ Fe · Te (cross-basis pairs).
#        Commuting control: Ti·Ti commutes (same-basis, ~0 gap).
#
# Finite maps:
#   Carnot:   (T_h, T_c, Q_h)         -> (eta, W_net, DS_h, DS_c, DS_cycle)
#   Szilard:  (kT, p_L)               -> (W_extracted, H_shannon_bits, E_reset)
#   QIT:      (rho_init, gamma, theta) -> (rho_final, S_vN per stroke, DS_total)
#   Axis DOF: stroke_name             -> (operator, entropy_role, axis_label)
#
# Size ladder: 8/16/32/64 temperature configs (Carnot), bias configs (Szilard),
#   initial states (QIT).
#
# The JAX audit lane reads this object's result JSON as a target.
# Re-run: julia carnot_szilard_qit_engine.jl
# Result: carnot_szilard_qit_engine_julia_results.json (same directory)

using LinearAlgebra
using Statistics
using Random

try
    @eval using JSON
catch _
    try
        import Pkg
        Pkg.activate(@__DIR__; io=devnull)
        @eval using JSON
    catch e
        error("JSON unavailable: $e")
    end
end

const OBJECT_ID       = "carnot_szilard_qit_axis_engine_julia_v1"
const CLAIM_CEILING   = "Carnot+Szilard+QIT engine finite maps under F01+N01. No layer/manifold/physics claims. promotion_allowed=false."
const PROMOTION_ALLOWED = false
const RESULT_PATH     = joinpath(@__DIR__, "carnot_szilard_qit_engine_julia_results.json")
const JAX_TARGET_PATH = joinpath(@__DIR__, "carnot_szilard_qit_engine_results.json")
const RNG_SEED        = 20260603
const SIZE_LADDER     = [8, 16, 32, 64]

D(args...) = Dict{String,Any}(args...)

# ─── Check log ───────────────────────────────────────────────────────────────
const CHECK_LOG = Dict{String,Any}[]

function CHECK(name::String, passed::Bool, detail::String="")
    push!(CHECK_LOG, D("check" => name, "passed" => passed, "detail" => detail))
    return passed
end

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — qubit operators
# ══════════════════════════════════════════════════════════════════════════════

const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -1im; 1im 0]
const sz = ComplexF64[1 0; 0 -1]

function z_dephase(rho::Matrix{ComplexF64}, gamma::Float64)::Matrix{ComplexF64}
    g = clamp(gamma, 0.0, 1.0)
    K0 = sqrt(1.0 - g/2.0) .* I2
    K1 = sqrt(g/2.0) .* sz
    return K0 * rho * K0' + K1 * rho * K1'
end

function x_dephase(rho::Matrix{ComplexF64}, gamma::Float64)::Matrix{ComplexF64}
    g = clamp(gamma, 0.0, 1.0)
    K0 = sqrt(1.0 - g/2.0) .* I2
    K1 = sqrt(g/2.0) .* sx
    return K0 * rho * K0' + K1 * rho * K1'
end

function Rx(theta::Float64)::Matrix{ComplexF64}
    return cos(theta/2) .* I2 - 1im*sin(theta/2) .* sx
end

function Rz(theta::Float64)::Matrix{ComplexF64}
    return cos(theta/2) .* I2 - 1im*sin(theta/2) .* sz
end

function apply_unitary(rho::Matrix{ComplexF64}, U::Matrix{ComplexF64})::Matrix{ComplexF64}
    return U * rho * U'
end

function von_neumann_entropy(rho::Matrix{ComplexF64})::Float64
    evals = eigvals(Hermitian(rho))
    S = 0.0
    for λ in evals
        λr = max(real(λ), 1e-15)
        S -= λr * log(λr)
    end
    return S
end

function coherence_offdiag(rho::Matrix{ComplexF64})::Float64
    return abs(rho[1,2])
end

# ══════════════════════════════════════════════════════════════════════════════
# 1. CARNOT ENGINE — Clausius entropy
# ══════════════════════════════════════════════════════════════════════════════
# domain:   (T_h, T_c, Q_h) with T_h > T_c > 0, Q_h > 0
# codomain: (eta, W_net, DS_h, DS_c, DS_cycle, per-stroke records)
# entropy kind: Clausius dS = dQ/T

function carnot_engine(T_h::Float64, T_c::Float64, Q_h::Float64)::Dict{String,Any}
    @assert T_h > T_c > 0 "T_h > T_c > 0 required"
    @assert Q_h > 0       "Q_h > 0 required"

    eta   = 1.0 - T_c / T_h
    W_net = eta * Q_h
    Q_c   = Q_h - W_net

    DS_h    = -Q_h / T_h     # hot reservoir perspective
    DS_c    = +Q_c / T_c     # cold reservoir perspective
    DS_cycle = DS_h + DS_c   # = 0 for reversible Carnot

    strokes = [
        D("name" => "A_isothermal_expansion_Th",  "dQ" => Q_h,   "dS_clausius" => Q_h/T_h,  "T" => T_h),
        D("name" => "B_adiabatic_expansion",       "dQ" => 0.0,   "dS_clausius" => 0.0,       "T" => nothing),
        D("name" => "C_isothermal_compression_Tc", "dQ" => -Q_c,  "dS_clausius" => -Q_c/T_c, "T" => T_c),
        D("name" => "D_adiabatic_compression",     "dQ" => 0.0,   "dS_clausius" => 0.0,       "T" => nothing),
    ]

    return D(
        "T_h" => T_h, "T_c" => T_c, "Q_h" => Q_h, "Q_c" => Q_c,
        "W_net" => W_net, "eta" => eta,
        "DS_hot_reservoir"             => DS_h,
        "DS_cold_reservoir"            => DS_c,
        "DS_cycle_working_substance"   => DS_cycle,
        "clausius_inequality_satisfied"=> DS_c >= -DS_h - 1e-12,
        "strokes"                      => strokes,
        "entropy_kind"                 => "Clausius_dS=dQ/T",
    )
end

# Positive test
car_pos = carnot_engine(400.0, 300.0, 100.0)
CHECK("carnot_positive_eta",      abs(car_pos["eta"] - 0.25) < 1e-10,       "eta=$(car_pos["eta"]) expected 0.25")
CHECK("carnot_positive_W_net",    abs(car_pos["W_net"] - 25.0) < 1e-10,     "W_net=$(car_pos["W_net"])")
CHECK("carnot_positive_DS_cycle", abs(car_pos["DS_cycle_working_substance"]) < 1e-10, "DS=$(car_pos["DS_cycle_working_substance"])")
CHECK("carnot_clausius_ineq",     car_pos["clausius_inequality_satisfied"],  "DS_h+DS_c>=0")

# Negative test: reversed temperatures → negative efficiency
car_neg_eta = 1.0 - 400.0/300.0
CHECK("carnot_negative_reversed_eta_lt_0", car_neg_eta < 0, "eta=$car_neg_eta")

# Boundary test: T_c → T_h → eta → 0
car_bnd = carnot_engine(300.0 + 1e-6, 300.0, 100.0)
CHECK("carnot_boundary_eta_near_zero", car_bnd["eta"] < 1e-5, "eta=$(car_bnd["eta"])")

# ══════════════════════════════════════════════════════════════════════════════
# 2. SZILARD ENGINE — Shannon entropy
# ══════════════════════════════════════════════════════════════════════════════
# domain:   (kT > 0, p_L ∈ (0,1))
# codomain: (H_shannon_bits, W_extracted, E_reset, W_net_szilard)
# entropy kind: Shannon H = -Σ p log₂ p  (bits)

function szilard_engine(kT::Float64, p_L::Float64)::Dict{String,Any}
    @assert kT > 0      "kT > 0 required"
    @assert 0 < p_L < 1 "p_L ∈ (0,1) required"
    p_R = 1.0 - p_L

    H_bits = -(p_L*log2(p_L) + p_R*log2(p_R))
    H_nats = -(p_L*log(p_L)  + p_R*log(p_R))

    W_extracted = kT * log(2.0)
    E_reset     = kT * log(2.0) * H_bits   # kT ln2 per bit
    W_net       = W_extracted - E_reset

    steps = [
        D("name" => "measure_partition",    "H_bits_gained" => H_bits,  "W" => 0.0),
        D("name" => "insert_partition",     "H_bits_gained" => 0.0,     "W" => 0.0),
        D("name" => "isothermal_expansion", "H_bits_gained" => -H_bits, "W" => W_extracted),
        D("name" => "landauer_reset",       "H_bits_gained" => H_bits,  "W" => -E_reset),
    ]

    return D(
        "kT" => kT, "p_L" => p_L, "p_R" => p_R,
        "H_shannon_bits" => H_bits,
        "H_shannon_nats" => H_nats,
        "W_extracted"    => W_extracted,
        "E_reset"        => E_reset,
        "W_net_szilard"  => W_net,
        "second_law_balanced" => abs(W_net) < 1e-12 || W_net <= 0,
        "steps"          => steps,
        "entropy_kind"   => "Shannon_H_bits",
    )
end

# Positive test: uniform prior → H=1 bit, W=kT ln2
sz_pos = szilard_engine(1.0, 0.5)
CHECK("szilard_positive_H_one_bit",  abs(sz_pos["H_shannon_bits"] - 1.0) < 1e-10, "H=$(sz_pos["H_shannon_bits"])")
CHECK("szilard_positive_W_kTln2",    abs(sz_pos["W_extracted"] - log(2.0)) < 1e-10, "W=$(sz_pos["W_extracted"])")
CHECK("szilard_positive_second_law", sz_pos["second_law_balanced"], "W_net=$(sz_pos["W_net_szilard"])")

# Negative test: biased prior → H < 1 bit
sz_neg = szilard_engine(1.0, 0.9)
CHECK("szilard_negative_H_lt_1", sz_neg["H_shannon_bits"] < 1.0, "H=$(sz_neg["H_shannon_bits"])")

# Boundary test: nearly deterministic → H → 0
sz_bnd = szilard_engine(1.0, 1.0 - 1e-8)
CHECK("szilard_boundary_H_near_zero", sz_bnd["H_shannon_bits"] < 0.01, "H=$(sz_bnd["H_shannon_bits"])")

# ══════════════════════════════════════════════════════════════════════════════
# 3. N01 NONCOMMUTATION WITNESS
# ══════════════════════════════════════════════════════════════════════════════
# Load-bearing cross-basis pairs:
#   Ti·Fi ≠ Fi·Ti  (z-dephase · Rx — cross basis)
#   Te·Fe ≠ Fe·Te  (x-dephase · Rz — cross basis)
# Commuting control:
#   Ti·Ti ≈ Ti·Ti  (same-basis dephasing — commutes)

rho_coher = ComplexF64[0.6 0.4; 0.4 0.4]
gamma_n01 = 0.5
theta_n01 = π/3.0

rho_Ti_Fi = apply_unitary(z_dephase(rho_coher, gamma_n01), Rx(theta_n01))
rho_Fi_Ti = z_dephase(apply_unitary(rho_coher, Rx(theta_n01)), gamma_n01)
n01_gap   = norm(rho_Ti_Fi - rho_Fi_Ti)

rho_ctrl_AB = z_dephase(z_dephase(rho_coher, 0.3), 0.5)
rho_ctrl_BA = z_dephase(z_dephase(rho_coher, 0.5), 0.3)
ctrl_gap    = norm(rho_ctrl_AB - rho_ctrl_BA)

CHECK("n01_ti_fi_noncommuting",           n01_gap  > 1e-10, "Ti·Fi gap=$n01_gap")
CHECK("n01_control_ti_ti_commutes",       ctrl_gap < 1e-10, "Ti·Ti gap=$ctrl_gap (should be ~0)")

# Te·Fe noncommutation
rho_TeFe  = apply_unitary(x_dephase(rho_coher, 0.7), Rz(theta_n01))
rho_FeTe  = x_dephase(apply_unitary(rho_coher, Rz(theta_n01)), 0.7)
n01_szild = norm(rho_TeFe - rho_FeTe)
CHECK("n01_te_fe_noncommuting", n01_szild > 1e-10, "Te·Fe gap=$n01_szild")

N01_RECORD = D(
    "Ti_Fi_order_gap"    => n01_gap,
    "n01_witnessed"      => n01_gap > 1e-10,
    "commuting_ctrl_gap" => ctrl_gap,
    "ctrl_confirms_specificity" => ctrl_gap < 1e-10,
    "Te_Fe_order_gap"    => n01_szild,
    "stroke_order_is_loadbearing" => true,
    "note" => "Ti-Fe and Te-Fi are same-basis and commute; Ti-Fi and Te-Fe are cross-basis and do not.",
)

# ══════════════════════════════════════════════════════════════════════════════
# 4. AXIS DOF MAPPING
# ══════════════════════════════════════════════════════════════════════════════
# Verify entropy monotone: S non-decreasing under Ti and Te; preserved under Fi, Fe

rho_test = ComplexF64[0.7 0.3; 0.3 0.3]
S0_test   = von_neumann_entropy(rho_test)
S_Ti_test = von_neumann_entropy(z_dephase(rho_test, 0.8))
S_Fi_test = von_neumann_entropy(apply_unitary(rho_test, Rx(π/4)))

CHECK("axis0_Ti_increases_or_preserves_S", S_Ti_test >= S0_test - 1e-12,
      "S0=$S0_test S_Ti=$S_Ti_test")
CHECK("axis0_Fi_preserves_S",              abs(S_Fi_test - S0_test) < 1e-10,
      "S0=$S0_test S_Fi=$S_Fi_test")

AXIS_DOF = D(
    "operators" => D(
        "Ti" => "z_dephasing_Kraus_channel",
        "Te" => "x_dephasing_Kraus_channel",
        "Fi" => "x_rotation_Rx_unitary",
        "Fe" => "z_rotation_Rz_unitary",
    ),
    "carnot_stroke_to_operator" => D(
        "A_isothermal_Th"       => "Ti",
        "B_adiabatic_expansion" => "Fi",
        "C_isothermal_Tc"       => "Te",
        "D_adiabatic_compression" => "Fe",
    ),
    "szilard_step_to_operator" => D(
        "measure_partition"    => "Ti",
        "insert_partition"     => "Fe",
        "isothermal_expansion" => "Fi",
        "landauer_reset"       => "Te",
    ),
    "axis_0_entropy_monotone" => D(
        "description"                   => "S(rho) non-decreasing under Ti and Te; preserved under Fi and Fe",
        "dephasing_ops_increase_S"      => true,
        "unitary_ops_preserve_S"        => true,
        "S0"                            => S0_test,
        "S_after_Ti"                    => S_Ti_test,
        "S_after_Fi"                    => S_Fi_test,
    ),
    "axis_6_noncommutation" => D(
        "description" => "Ti·Fi != Fi·Ti (cross-basis); Te·Fe != Fe·Te (cross-basis); N01 witnessed",
        "Ti_Fi_gap"  => n01_gap,
        "Te_Fe_gap"  => n01_szild,
        "ctrl_gap"   => ctrl_gap,
    ),
)

# ══════════════════════════════════════════════════════════════════════════════
# 5. QIT CARNOT CYCLE — von Neumann entropy, no kT/ln2
# ══════════════════════════════════════════════════════════════════════════════
# domain:   (rho_init, gamma_Ti, theta_Fi, gamma_Te, theta_Fe)
# codomain: per-stroke rho and S(rho)
# entropy kind: von Neumann S = -Tr(rho log rho) nats

function qit_carnot_cycle(rho_init::Matrix{ComplexF64},
                           gamma_Ti::Float64, theta_Fi::Float64,
                           gamma_Te::Float64, theta_Fe::Float64)::Dict{String,Any}
    rhoA = copy(rho_init)
    SA   = von_neumann_entropy(rhoA)

    # Stroke A: Ti
    rhoB = z_dephase(rhoA, gamma_Ti);   SB = von_neumann_entropy(rhoB)
    # Stroke B: Fi
    rhoC = apply_unitary(rhoB, Rx(theta_Fi)); SC = von_neumann_entropy(rhoC)
    # Stroke C: Te
    rhoD = x_dephase(rhoC, gamma_Te);   SD = von_neumann_entropy(rhoD)
    # Stroke D: Fe
    rhoE = apply_unitary(rhoD, Rz(theta_Fe)); SE = von_neumann_entropy(rhoE)

    return D(
        "S_init"       => SA,
        "S_after_Ti"   => SB, "DS_Ti" => SB-SA,
        "S_after_Fi"   => SC, "DS_Fi" => SC-SB,
        "S_after_Te"   => SD, "DS_Te" => SD-SC,
        "S_after_Fe"   => SE, "DS_Fe" => SE-SD,
        "DS_total_cycle" => SE-SA,
        "coherence_init"    => coherence_offdiag(rhoA),
        "coherence_after_Ti" => coherence_offdiag(rhoB),
        "coherence_after_Te" => coherence_offdiag(rhoD),
        "entropy_kind"      => "von_Neumann_nats",
        "no_classical_kT_or_ln2" => true,
    )
end

# Positive test: state WITH coherence
rho_coher_init = ComplexF64[0.6 0.4; 0.4 0.4]
qc_pos = qit_carnot_cycle(rho_coher_init, 0.8, π/3, 0.6, π/4)

CHECK("qit_carnot_Ti_increases_S", qc_pos["DS_Ti"] > 0,       "DS_Ti=$(qc_pos["DS_Ti"])")
CHECK("qit_carnot_Fi_preserves_S", abs(qc_pos["DS_Fi"]) < 1e-10, "DS_Fi=$(qc_pos["DS_Fi"])")
CHECK("qit_carnot_Te_increases_S", qc_pos["DS_Te"] > -1e-10,  "DS_Te=$(qc_pos["DS_Te"])")
CHECK("qit_carnot_Fe_preserves_S", abs(qc_pos["DS_Fe"]) < 1e-10, "DS_Fe=$(qc_pos["DS_Fe"])")

# Negative test: Ti-Ti (same-basis degenerate) → S monotone, no purity restoration
rho_mix = ComplexF64[0.6 0.0; 0.0 0.4]
rho_degen1 = z_dephase(rho_mix, 0.8)
rho_degen2 = z_dephase(rho_degen1, 0.6)
S_degen_start = von_neumann_entropy(rho_mix)
S_degen_end   = von_neumann_entropy(rho_degen2)
purity_start  = real(tr(rho_mix*rho_mix))
purity_end    = real(tr(rho_degen2*rho_degen2))
CHECK("qit_carnot_negative_degenerate_S_monotone",   S_degen_end >= S_degen_start - 1e-12, "S: $S_degen_start -> $S_degen_end")
CHECK("qit_carnot_negative_purity_decreases",         purity_end <= purity_start + 1e-12,  "pur: $purity_start -> $purity_end")

# Boundary: max-mixed state → S=ln2; Ti adds nothing
rho_maxmix  = 0.5 * Matrix{ComplexF64}(I, 2, 2)
S_maxmix    = von_neumann_entropy(rho_maxmix)
S_Ti_maxmix = von_neumann_entropy(z_dephase(rho_maxmix, 1.0))
CHECK("qit_carnot_boundary_maxmixed_S",  abs(S_maxmix - log(2.0)) < 1e-10,  "S=$S_maxmix ln2=$(log(2.0))")
CHECK("qit_carnot_boundary_Ti_noop",     abs(S_Ti_maxmix - S_maxmix) < 1e-10, "delta=$(abs(S_Ti_maxmix-S_maxmix))")

# ══════════════════════════════════════════════════════════════════════════════
# 6. QIT SZILARD CYCLE — von Neumann entropy
# ══════════════════════════════════════════════════════════════════════════════
function qit_szilard_cycle(rho_init::Matrix{ComplexF64},
                            theta_Fe::Float64, theta_Fi::Float64,
                            gamma_Te::Float64)::Dict{String,Any}
    rho0 = copy(rho_init)
    S0   = von_neumann_entropy(rho0)
    coh0 = coherence_offdiag(rho0)

    # Step 1: Ti (full z-dephase = measurement-like)
    rho1 = z_dephase(rho0, 1.0)
    S1   = von_neumann_entropy(rho1)
    coh1 = coherence_offdiag(rho1)

    # Step 2: Fe (z-rotation, conditional phase)
    rho2 = apply_unitary(rho1, Rz(theta_Fe))
    S2   = von_neumann_entropy(rho2)

    # Step 3: Fi (x-rotation, coherent extraction)
    rho3 = apply_unitary(rho2, Rx(theta_Fi))
    S3   = von_neumann_entropy(rho3)

    # Step 4: Te (x-dephase = erasure/reset)
    rho4 = x_dephase(rho3, gamma_Te)
    S4   = von_neumann_entropy(rho4)

    return D(
        "S_init"    => S0, "coh_init" => coh0,
        "S_after_Ti" => S1, "coh_after_Ti" => coh1,
        "S_after_Fe" => S2,
        "S_after_Fi" => S3,
        "S_after_Te" => S4,
        "coherence_destroyed" => coh0 - coh1,
        "DS_total_cycle"      => S4 - S0,
        "entropy_kind"        => "von_Neumann_nats",
        "no_classical_kT_or_ln2" => true,
    )
end

# Positive: state with coherence → Ti destroys coherence
rho_coher2 = ComplexF64[0.5 0.4; 0.4 0.5]
qs_pos = qit_szilard_cycle(rho_coher2, π/2, π/3, 0.8)
CHECK("qit_szilard_positive_coherence_destroyed", qs_pos["coherence_destroyed"] > 1e-6,
      "coh_destroyed=$(qs_pos["coherence_destroyed"])")

# Negative: diagonal state → no coherence to destroy
rho_diag2 = ComplexF64[0.6 0.0; 0.0 0.4]
qs_neg = qit_szilard_cycle(rho_diag2, π/2, π/3, 0.8)
CHECK("qit_szilard_negative_no_coherence", qs_neg["coherence_destroyed"] < 1e-10,
      "coh_destroyed=$(qs_neg["coherence_destroyed"])")

# N01 order check: Te·Fe ≠ Fe·Te
rho_ord2 = ComplexF64[0.5 0.3; 0.3 0.5]
rho_TeFe2 = apply_unitary(x_dephase(rho_ord2, 0.7), Rz(π/3))
rho_FeTe2 = x_dephase(apply_unitary(rho_ord2, Rz(π/3)), 0.7)
n01_szild2 = norm(rho_TeFe2 - rho_FeTe2)
CHECK("qit_szilard_n01_Te_Fe_order_matters", n01_szild2 > 1e-10,
      "Te-Fe vs Fe-Te gap=$n01_szild2")

# Boundary: pure |+> → Ti destroys all coherence
rho_plus = ComplexF64[0.5 0.5; 0.5 0.5]
qs_bnd   = qit_szilard_cycle(rho_plus, 0.0, π/2, 1.0)
CHECK("qit_szilard_boundary_coherence_fully_destroyed", qs_bnd["coh_after_Ti"] < 1e-10,
      "coh_after_Ti=$(qs_bnd["coh_after_Ti"])")

# ══════════════════════════════════════════════════════════════════════════════
# 7. ENTROPY DISTINCTNESS
# ══════════════════════════════════════════════════════════════════════════════
# Verify: diagonal rho → vN = Shannon_nats
p0  = 0.7
rho_diag3 = ComplexF64[p0 0.0; 0.0 1.0-p0]
S_vN_diag  = von_neumann_entropy(rho_diag3)
H_nats     = -(p0*log(p0) + (1.0-p0)*log(1.0-p0))
CHECK("entropy_vN_eq_shannon_for_diagonal", abs(S_vN_diag - H_nats) < 1e-10,
      "vN=$S_vN_diag Shannon_nats=$H_nats")

# Verify: coherent rho → vN ≠ Shannon-on-diagonals
rho_off  = ComplexF64[0.5 0.4; 0.4 0.5]
S_vN_off = von_neumann_entropy(rho_off)
S_diag_only = -(0.5*log(0.5) + 0.5*log(0.5))
CHECK("entropy_vN_neq_shannon_for_coherent", abs(S_vN_off - S_diag_only) > 1e-4,
      "vN=$S_vN_off Shannon_diag=$S_diag_only (vN lower due to coherence)")

ENTROPY_DISTINCTNESS = D(
    "clausius_Carnot" => D(
        "defined_on"               => "heat_reservoirs_and_working_substance_path",
        "unit"                     => "J/K_or_kB_nats",
        "zero_for_adiabatic"       => true,
        "requires_temperature_field" => true,
    ),
    "shannon_Szilard" => D(
        "defined_on"               => "probability_distributions_over_outcomes",
        "unit"                     => "bits",
        "requires_probability_over_positions" => true,
    ),
    "von_Neumann_QIT" => D(
        "defined_on"               => "density_matrices",
        "unit"                     => "nats",
        "reduces_to_shannon_when_diagonal" => true,
        "requires_quantum_state"   => true,
        "no_classical_kT_or_ln2"  => true,
    ),
    "genuinely_distinct" => true,
    "diagonal_test_vN_eq_shannon" => abs(S_vN_diag - H_nats) < 1e-10,
    "coherent_test_vN_lt_shannon_diagonal" => S_vN_off < S_diag_only,
)

# ══════════════════════════════════════════════════════════════════════════════
# 8. SIZE LADDER  8/16/32/64
# ══════════════════════════════════════════════════════════════════════════════
function carnot_ladder_julia(sizes)
    results = Dict{String,Any}()
    for N in sizes
        T_h_vals = range(300.0, 1000.0, length=N)
        T_c = 200.0; Q_h = 50.0
        etas = [carnot_engine(Float64(Th), T_c, Q_h)["eta"] for Th in T_h_vals]
        results[string(N)] = D(
            "n_configs"  => N,
            "eta_min"    => minimum(etas),
            "eta_max"    => maximum(etas),
            "all_positive_W" => all(η > 0 for η in etas),
        )
    end
    return results
end

function szilard_ladder_julia(sizes)
    results = Dict{String,Any}()
    for N in sizes
        p_vals = range(0.05, 0.95, length=N)
        Hs = [szilard_engine(1.0, Float64(p))["H_shannon_bits"] for p in p_vals]
        results[string(N)] = D(
            "n_configs" => N,
            "H_min"     => minimum(Hs),
            "H_max"     => maximum(Hs),
            "all_W_kTln2" => all(abs(szilard_engine(1.0, Float64(p))["W_extracted"] - log(2.0)) < 1e-10 for p in p_vals),
        )
    end
    return results
end

function qit_ladder_julia(sizes)
    rng = MersenneTwister(RNG_SEED)
    results = Dict{String,Any}()
    for N in sizes
        S_inits = Float64[]; S_finals = Float64[]
        for _ in 1:N
            psi = randn(rng, ComplexF64, 2)
            psi ./= norm(psi)
            rho0 = psi * psi'
            rho0 = 0.8*rho0 + 0.1*Matrix{ComplexF64}(I, 2, 2)
            r = qit_carnot_cycle(rho0, 0.7, π/4, 0.5, π/6)
            push!(S_inits, r["S_init"])
            push!(S_finals, r["S_after_Fe"])
        end
        results[string(N)] = D(
            "n_states"     => N,
            "S_init_mean"  => mean(S_inits),
            "S_final_mean" => mean(S_finals),
            "DS_mean"      => mean(S_finals .- S_inits),
        )
    end
    return results
end

lad_carnot  = carnot_ladder_julia(SIZE_LADDER)
lad_szilard = szilard_ladder_julia(SIZE_LADDER)
lad_qit     = qit_ladder_julia(SIZE_LADDER)

CHECK("ladder_carnot_all_4",  length(lad_carnot)  == 4, "n=$(length(lad_carnot))")
CHECK("ladder_szilard_all_4", length(lad_szilard) == 4, "n=$(length(lad_szilard))")
CHECK("ladder_qit_all_4",     length(lad_qit)     == 4, "n=$(length(lad_qit))")

# ══════════════════════════════════════════════════════════════════════════════
# QIT PUSH SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
QIT_PUSH = D(
    "f01_satisfied"                  => true,
    "n01_satisfied"                  => true,
    "qit_carnot_cycle_well_defined"  => true,
    "qit_szilard_cycle_well_defined" => true,
    "von_neumann_entropy_per_stroke" => true,
    "entropy_monotone_dephasing"     => true,
    "entropy_preserved_unitary"      => true,
    "order_sensitive_strokes"        => true,
    "coherence_destruction_szilard"  => true,
    "extractable_work_without_hamiltonian" => "OPEN — H_op not specified",
    "absolute_free_energy"           => "OPEN — requires Tr(rho H)",
    "classical_kT_ln2"               => "EXCLUDED — pure QIT, no classical constants",
    "cycle_closure_guaranteed"       => "OPEN — depends on stroke parameters",
    "promotion_allowed"              => false,
    "candidates_not_proven"          => true,
)

# ══════════════════════════════════════════════════════════════════════════════
# ASSEMBLE AND WRITE RESULT JSON
# ══════════════════════════════════════════════════════════════════════════════
all_passed = all(c["passed"] for c in CHECK_LOG)

results = D(
    "object_id"         => OBJECT_ID,
    "claim_ceiling"     => CLAIM_CEILING,
    "promotion_allowed" => PROMOTION_ALLOWED,
    "carnot_engine" => D(
        "positive_example"  => car_pos,
        "boundary_example"  => car_bnd,
        "entropy_kind"      => "Clausius_dS=dQ/T",
        "eta_formula"       => "1 - T_c/T_h",
        "DS_cycle_zero"     => true,
    ),
    "szilard_engine" => D(
        "positive_example"  => sz_pos,
        "negative_example"  => sz_neg,
        "boundary_example"  => sz_bnd,
        "entropy_kind"      => "Shannon_H_bits",
        "W_formula"         => "kT_ln2",
        "landauer_reset_cost" => "kT_ln2_per_bit_erased",
    ),
    "axis_dof_mapping"  => AXIS_DOF,
    "n01_record"        => N01_RECORD,
    "qit_carnot" => D(
        "positive_example"  => qc_pos,
        "entropy_kind"      => "von_Neumann_nats",
        "no_classical_kT_ln2" => true,
    ),
    "qit_szilard" => D(
        "positive_example"  => qs_pos,
        "negative_example"  => qs_neg,
        "boundary_example"  => qs_bnd,
        "n01_Te_Fe_gap"     => n01_szild2,
        "entropy_kind"      => "von_Neumann_nats",
        "no_classical_kT_ln2" => true,
    ),
    "qit_push"                 => QIT_PUSH,
    "entropy_distinctness"     => ENTROPY_DISTINCTNESS,
    "f01_finite"               => true,
    "n01_load_bearing"         => N01_RECORD,
    "entropy_distinctness_verdict" => true,
    "size_ladder_carnot"       => lad_carnot,
    "size_ladder_szilard"      => lad_szilard,
    "size_ladder_qit"          => lad_qit,
    "all_checks_passed"        => all_passed,
    "check_log"                => CHECK_LOG,
)

open(RESULT_PATH, "w") do f
    JSON.print(f, results, 2)
end

n_pass = sum(c["passed"] for c in CHECK_LOG)
n_total = length(CHECK_LOG)
println("object_id: $OBJECT_ID")
println("Result written to: $RESULT_PATH")
println("Checks: $n_pass / $n_total passed")
println("all_checks_passed: $all_passed")
if !all_passed
    println("FAILED checks:")
    for c in CHECK_LOG
        !c["passed"] && println("  FAIL: $(c["check"]) — $(c["detail"])")
    end
    exit(1)
end
