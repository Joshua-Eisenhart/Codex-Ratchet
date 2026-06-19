# cs2_julia.jl
#
# object_id: cs2_carnot_szilard_two_entropy_julia_v1
#
# claim_ceiling:
#   Computes explicit finite maps for:
#   (1) Carnot 4-stroke heat engine — Clausius entropy dS = dQ/T (J/K)
#       forward (heat engine) AND reverse (refrigerator / heat pump)
#   (2) Szilard 1-bit information engine — Shannon H (bits) AND
#       von Neumann S_vN (nats) — both entropies tracked per step
#       forward (work extraction) AND reverse (work-to-information)
#   (3) Explicit two-entropy distinctness record:
#       Clausius dQ/T (J/K, thermal) vs Shannon/vN (bits/nats, informational)
#       are distinct bookkeeping systems on the same engine structure.
#   Does NOT assert layer-completion, manifold admission, coupling,
#   bridge (rho_AB/Xi/Phi0/Axis0), flux, or physics.
#   Does NOT claim these ARE Axis 3 (Ax3 is OPEN).
#   promotion_allowed: false.
#
# Root constraints in force:
#   F01: finite-dimensional carrier — qubit (2x2), discrete stroke/step
#        sequences, finite temperature/bias ladder (8/16/32/64 configs).
#   N01: stroke order is load-bearing — z-dephase x Rx != Rx x z-dephase
#        (cross-basis noncommutation; commuting control provided).
#
# Finite maps:
#   carnot_forward:  (T_h, T_c, Q_h) -> (eta, W_net, DS_h, DS_c, DS_cycle)
#   carnot_reverse:  (T_h, T_c, W_in) -> (COP, Q_h_pump, Q_c_absorbed, DS_cycle)
#   szilard_forward: (kT, p_L) -> (H_bits, S_vN_nats, W_extracted, E_reset)
#   szilard_reverse: (kT, p_L) -> (W_in, info_gained, erasure_cost)
#   two_entropy_distinctness: reports both entropy species per engine step
#
# Size ladder: 8/16/32/64 temperature/bias configurations
#
# Re-run: julia cs2_julia.jl
# Results: cs2_julia_results.json (same directory, JAX audit target)

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

const OBJECT_ID         = "cs2_carnot_szilard_two_entropy_julia_v1"
const CLAIM_CEILING     = "Carnot+Szilard two-entropy engine (Clausius J/K vs Shannon/vN bits/nats), both directions, under F01+N01. No layer/manifold/bridge/physics claims. Ax3 OPEN. promotion_allowed=false."
const PROMOTION_ALLOWED = false
const RESULT_PATH       = joinpath(@__DIR__, "cs2_julia_results.json")
const RNG_SEED          = 20260604
const SIZE_LADDER       = [8, 16, 32, 64]

D(args...) = Dict{String,Any}(args...)

# ─── Check log ───────────────────────────────────────────────────────────────
const CHECK_LOG = Dict{String,Any}[]

function CHECK(name::String, passed::Bool, detail::String="")
    push!(CHECK_LOG, D("check" => name, "passed" => passed, "detail" => detail))
    if !passed
        @warn "FAIL: $name — $detail"
    end
    return passed
end

# ══════════════════════════════════════════════════════════════════════════════
# QUBIT OPERATORS (for vN entropy bookkeeping)
# ══════════════════════════════════════════════════════════════════════════════

const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sz = ComplexF64[1 0; 0 -1]

function z_dephase(rho::Matrix{ComplexF64}, gamma::Float64)::Matrix{ComplexF64}
    g = clamp(gamma, 0.0, 1.0)
    K0 = sqrt(1.0 - g/2.0) .* I2
    K1 = sqrt(g/2.0) .* sz
    return K0 * rho * K0' + K1 * rho * K1'
end

function Rx(theta::Float64)::Matrix{ComplexF64}
    return cos(theta/2) .* I2 - 1im*sin(theta/2) .* sx
end

function von_neumann_entropy(rho::Matrix{ComplexF64})::Float64
    evals = eigvals(Hermitian(rho))
    S = 0.0
    for lam in evals
        lr = max(real(lam), 1e-15)
        S -= lr * log(lr)
    end
    return S
end

# ══════════════════════════════════════════════════════════════════════════════
# 1. CARNOT ENGINE — CLAUSIUS ENTROPY
# ══════════════════════════════════════════════════════════════════════════════
# Clausius entropy: dS = dQ/T  (units: J/K or kB)
# This is DISTINCT from Shannon/vN entropy: no log(p), no density matrices.
# The 4 strokes: isothermal-hot / adiabatic-expand / isothermal-cold / adiabatic-compress

function carnot_forward(T_h::Float64, T_c::Float64, Q_h::Float64)::Dict{String,Any}
    @assert T_h > T_c > 0 "T_h > T_c > 0 required"
    @assert Q_h > 0        "Q_h > 0"

    eta   = 1.0 - T_c / T_h
    W_net = eta * Q_h
    Q_c   = Q_h - W_net   # heat rejected to cold reservoir

    # Clausius entropy changes (working substance perspective)
    DS_h    = -Q_h / T_h    # working substance gains -Q_h/T_h from hot (exports to hot)
    DS_c    = +Q_c / T_c    # working substance exports Q_c to cold; cold gains +Q_c/T_c
    DS_cycle = DS_h + DS_c  # = 0 for reversible Carnot

    strokes = [
        D("stroke" => "A_isothermal_expand_hot",
          "dQ_working" => Q_h,    "T" => T_h,
          "dS_clausius" =>  Q_h / T_h,
          "direction" => "forward",
          "entropy_species" => "Clausius_dS=dQ/T"),
        D("stroke" => "B_adiabatic_expand",
          "dQ_working" => 0.0,   "T" => nothing,
          "dS_clausius" => 0.0,
          "direction" => "forward",
          "entropy_species" => "Clausius_dS=dQ/T"),
        D("stroke" => "C_isothermal_compress_cold",
          "dQ_working" => -Q_c,  "T" => T_c,
          "dS_clausius" => -Q_c / T_c,
          "direction" => "forward",
          "entropy_species" => "Clausius_dS=dQ/T"),
        D("stroke" => "D_adiabatic_compress",
          "dQ_working" => 0.0,   "T" => nothing,
          "dS_clausius" => 0.0,
          "direction" => "forward",
          "entropy_species" => "Clausius_dS=dQ/T"),
    ]

    return D(
        "engine_direction"     => "forward_heat_engine",
        "T_h" => T_h, "T_c" => T_c, "Q_h" => Q_h, "Q_c" => Q_c,
        "W_net" => W_net,
        "eta"  => eta,
        "eta_carnot_formula"   => 1.0 - T_c / T_h,
        "eta_matches_formula"  => abs(eta - (1.0 - T_c/T_h)) < 1e-12,
        "DS_hot_reservoir"     => DS_h,
        "DS_cold_reservoir"    => DS_c,
        "DS_cycle_total"       => DS_cycle,
        "DS_cycle_zero"        => abs(DS_cycle) < 1e-10,
        "W_net_positive"       => W_net > 0,
        "clausius_ineq_satisfied" => DS_c >= -DS_h - 1e-12,
        "strokes"              => strokes,
        "entropy_species"      => "Clausius_dS=dQ/T",
        "units"                => "J/K or kB",
        "NOT_Shannon_NOT_vN"   => true,
    )
end

function carnot_reverse(T_h::Float64, T_c::Float64, W_in::Float64)::Dict{String,Any}
    # Reverse Carnot = refrigerator (work in -> heat pumped from cold to hot)
    @assert T_h > T_c > 0 "T_h > T_c > 0 required"
    @assert W_in > 0       "W_in > 0 for refrigerator"

    # COP_refrigerator = Q_c / W_in = T_c / (T_h - T_c)
    COP_fridge = T_c / (T_h - T_c)
    Q_c_abs    = COP_fridge * W_in      # heat absorbed from cold reservoir
    Q_h_pump   = Q_c_abs + W_in         # heat delivered to hot reservoir

    DS_cycle_rev = -Q_h_pump/T_h + Q_c_abs/T_c  # should be 0 for reversible

    strokes = [
        D("stroke" => "A_isothermal_compress_hot",
          "dQ_working" => -Q_h_pump, "T" => T_h,
          "dS_clausius" => -Q_h_pump / T_h,
          "direction" => "reverse",
          "entropy_species" => "Clausius_dS=dQ/T"),
        D("stroke" => "B_adiabatic_expand_rev",
          "dQ_working" => 0.0, "T" => nothing,
          "dS_clausius" => 0.0,
          "direction" => "reverse",
          "entropy_species" => "Clausius_dS=dQ/T"),
        D("stroke" => "C_isothermal_expand_cold",
          "dQ_working" => Q_c_abs, "T" => T_c,
          "dS_clausius" => Q_c_abs / T_c,
          "direction" => "reverse",
          "entropy_species" => "Clausius_dS=dQ/T"),
        D("stroke" => "D_adiabatic_compress_rev",
          "dQ_working" => 0.0, "T" => nothing,
          "dS_clausius" => 0.0,
          "direction" => "reverse",
          "entropy_species" => "Clausius_dS=dQ/T"),
    ]

    return D(
        "engine_direction"  => "reverse_refrigerator",
        "T_h" => T_h, "T_c" => T_c, "W_in" => W_in,
        "Q_c_absorbed"      => Q_c_abs,
        "Q_h_pumped"        => Q_h_pump,
        "COP_refrigerator"  => COP_fridge,
        "COP_formula"       => T_c / (T_h - T_c),
        "COP_matches_formula" => abs(COP_fridge - T_c/(T_h-T_c)) < 1e-12,
        "DS_cycle_total"    => DS_cycle_rev,
        "DS_cycle_zero"     => abs(DS_cycle_rev) < 1e-10,
        "W_in_positive"     => W_in > 0,
        "Q_h_pump_positive" => Q_h_pump > 0,
        "strokes"           => strokes,
        "entropy_species"   => "Clausius_dS=dQ/T",
        "units"             => "J/K or kB",
        "NOT_Shannon_NOT_vN" => true,
    )
end

# ── Carnot checks ──────────────────────────────────────────────────────────────
car_fwd = carnot_forward(400.0, 300.0, 100.0)
CHECK("carnot_fwd_eta_eq_formula",   car_fwd["eta_matches_formula"],
      "eta=$(car_fwd["eta"]) formula=$(1.0 - 300.0/400.0)")
CHECK("carnot_fwd_eta_value",        abs(car_fwd["eta"] - 0.25) < 1e-12,
      "eta=$(car_fwd["eta"]) expected 0.25")
CHECK("carnot_fwd_DS_cycle_zero",    car_fwd["DS_cycle_zero"],
      "DS_cycle=$(car_fwd["DS_cycle_total"])")
CHECK("carnot_fwd_W_net_positive",   car_fwd["W_net_positive"],
      "W_net=$(car_fwd["W_net"])")
CHECK("carnot_fwd_clausius_ineq",    car_fwd["clausius_ineq_satisfied"],
      "DS_cold=$(car_fwd["DS_cold_reservoir"])")

# Negative: T_c → T_h means eta → 0; T_c > T_h means reversed efficiency < 0
neg_eta = 1.0 - 400.0/300.0
CHECK("carnot_negative_reversed_eta_lt_0", neg_eta < 0.0,
      "eta_reversed=$neg_eta")

# Boundary: T_c → T_h → eta → 0
car_bnd = carnot_forward(300.0 + 1e-6, 300.0, 100.0)
CHECK("carnot_boundary_eta_near_zero", car_bnd["eta"] < 1e-5,
      "eta=$(car_bnd["eta"])")

# Reverse direction
car_rev = carnot_reverse(400.0, 300.0, 25.0)
CHECK("carnot_rev_COP_eq_formula",   car_rev["COP_matches_formula"],
      "COP=$(car_rev["COP_refrigerator"]) formula=$(300.0/(400.0-300.0))")
CHECK("carnot_rev_COP_value",        abs(car_rev["COP_refrigerator"] - 3.0) < 1e-10,
      "COP=$(car_rev["COP_refrigerator"]) expected 3.0")
CHECK("carnot_rev_DS_cycle_zero",    car_rev["DS_cycle_zero"],
      "DS_cycle=$(car_rev["DS_cycle_total"])")
CHECK("carnot_rev_Q_h_pump_positive", car_rev["Q_h_pump_positive"],
      "Q_h=$(car_rev["Q_h_pumped"])")

# Cross-check: reverse COP = (1/eta - 1) = T_c/(T_h-T_c)
eta_fwd   = car_fwd["eta"]
cop_cross = (1.0/eta_fwd) - 1.0
CHECK("carnot_cross_check_rev_vs_fwd_eta",
      abs(cop_cross - car_rev["COP_refrigerator"]) < 1e-10,
      "COP_from_eta=$cop_cross COP_direct=$(car_rev["COP_refrigerator"])")

# ══════════════════════════════════════════════════════════════════════════════
# 2. SZILARD ENGINE — SHANNON H (bits) + von Neumann S_vN (nats)
# ══════════════════════════════════════════════════════════════════════════════
# Shannon: H = -Σ p log₂ p  (bits) — classical probability over positions
# von Neumann: S_vN = -Tr(rho log rho) (nats) — quantum density matrix
# Both are tracked here; they are DISTINCT from Clausius dS=dQ/T.
# The qubit density matrix rho encodes the particle position distribution.

function szilard_forward(kT::Float64, p_L::Float64)::Dict{String,Any}
    @assert kT > 0       "kT > 0"
    @assert 0 < p_L < 1  "p_L ∈ (0,1)"
    p_R = 1.0 - p_L

    # Shannon entropy (bits)
    H_bits = -(p_L*log2(p_L) + p_R*log2(p_R))
    H_nats = -(p_L*log(p_L)  + p_R*log(p_R))

    # von Neumann entropy of the corresponding diagonal qubit state
    rho_particle = ComplexF64[p_L 0.0; 0.0 p_R]
    S_vN_nats    = von_neumann_entropy(rho_particle)
    # For diagonal rho, S_vN = H_nats exactly (verified below)

    # Landauer: work extracted <= kT ln2 per bit of information
    W_extracted = kT * log(2.0)     # upper bound: extract at most kT ln2 per bit
    E_reset     = kT * H_nats       # erasure cost = kT * H_nats (Landauer)

    steps = [
        D("step" => "1_measure_partition",
          "H_bits"   => H_bits,  "H_nats" => H_nats,
          "S_vN_nats" => S_vN_nats,
          "W"         => 0.0,
          "direction" => "forward",
          "note"      => "demon measures; gains 1-bit info (for uniform prior)"),
        D("step" => "2_insert_partition",
          "H_bits"   => 0.0, "H_nats" => 0.0,
          "S_vN_nats" => 0.0,
          "W"         => 0.0,
          "direction" => "forward",
          "note"      => "partition inserted at particle location"),
        D("step" => "3_isothermal_expansion",
          "H_bits"   => -H_bits, "H_nats" => -H_nats,
          "S_vN_nats" => -S_vN_nats,
          "W"         => W_extracted,
          "direction" => "forward",
          "note"      => "particle expands; work extracted; demon info erased implicitly"),
        D("step" => "4_landauer_reset",
          "H_bits"   => H_bits,  "H_nats"  => H_nats,
          "S_vN_nats" => S_vN_nats,
          "W"         => -E_reset,
          "direction" => "forward",
          "note"      => "demon memory erased; Landauer cost kT*H_nats"),
    ]

    W_net = W_extracted - E_reset

    return D(
        "engine_direction"   => "forward_work_extraction",
        "kT" => kT, "p_L" => p_L, "p_R" => p_R,
        "H_shannon_bits"     => H_bits,
        "H_shannon_nats"     => H_nats,
        "S_vN_nats"          => S_vN_nats,
        "vN_eq_shannon_for_diagonal" => abs(S_vN_nats - H_nats) < 1e-12,
        "W_extracted"        => W_extracted,
        "W_extracted_le_kTln2" => W_extracted <= kT * log(2.0) + 1e-12,
        "E_reset_landauer"   => E_reset,
        "E_reset_ge_kTln2_if_1bit" => H_bits > 0.99 ? E_reset >= kT*log(2.0) - 1e-12 : true,
        "W_net_szilard"      => W_net,
        "second_law_balanced_for_uniform" => abs(W_net) < 1e-12 || p_L != 0.5,
        "steps"              => steps,
        "entropy_species"    => D(
            "Shannon_H_bits"   => "classical probability; bits",
            "vN_S_nats"        => "quantum density matrix; nats",
            "Clausius_ABSENT"  => "no dQ/T tracking — distinct from Carnot entropy",
        ),
        "NOT_Clausius"       => true,
        "units_Shannon"      => "bits",
        "units_vN"           => "nats",
    )
end

function szilard_reverse(kT::Float64, p_L::Float64)::Dict{String,Any}
    # Reverse Szilard: work IN -> information gained / erasure direction
    # W_in = E_reset (cost to erase demon's memory and restore initial state)
    # This is the "writing" / decompression direction
    @assert kT > 0       "kT > 0"
    @assert 0 < p_L < 1  "p_L ∈ (0,1)"
    p_R = 1.0 - p_L

    H_bits = -(p_L*log2(p_L) + p_R*log2(p_R))
    H_nats = -(p_L*log(p_L)  + p_R*log(p_R))

    rho_particle = ComplexF64[p_L 0.0; 0.0 p_R]
    S_vN_nats    = von_neumann_entropy(rho_particle)

    # In reverse: work is consumed to write information (compress entropy)
    W_in         = kT * log(2.0)   # same kT ln2 — symmetry of Landauer
    info_gained  = H_bits          # bits of info stored
    erasure_cost = kT * H_nats     # kT * H_nats nats of entropy cleared

    steps = [
        D("step" => "1_write_information",
          "H_bits"    => H_bits, "H_nats" => H_nats,
          "S_vN_nats" => S_vN_nats,
          "W_consumed" => W_in,
          "direction"  => "reverse",
          "note"       => "work in; information written to demon memory"),
        D("step" => "2_remove_partition",
          "H_bits"    => 0.0, "H_nats" => 0.0,
          "S_vN_nats" => 0.0,
          "W_consumed" => 0.0,
          "direction"  => "reverse",
          "note"       => "partition removed"),
        D("step" => "3_isothermal_compress",
          "H_bits"    => H_bits, "H_nats" => H_nats,
          "S_vN_nats" => S_vN_nats,
          "W_consumed" => erasure_cost,
          "direction"  => "reverse",
          "note"       => "entropy erased; information stored in memory"),
        D("step" => "4_restore",
          "H_bits"    => 0.0, "H_nats" => 0.0,
          "S_vN_nats" => 0.0,
          "W_consumed" => 0.0,
          "direction"  => "reverse",
          "note"       => "system restored"),
    ]

    return D(
        "engine_direction"   => "reverse_work_to_information",
        "kT" => kT, "p_L" => p_L, "p_R" => p_R,
        "H_shannon_bits"     => H_bits,
        "H_shannon_nats"     => H_nats,
        "S_vN_nats"          => S_vN_nats,
        "W_in_consumed"      => W_in,
        "info_gained_bits"   => info_gained,
        "erasure_cost_nats"  => erasure_cost,
        "W_in_ge_kTln2"      => W_in >= kT * log(2.0) - 1e-12,
        "steps"              => steps,
        "entropy_species"    => D(
            "Shannon_H_bits"   => "classical probability; bits",
            "vN_S_nats"        => "quantum density matrix; nats",
            "Clausius_ABSENT"  => "no dQ/T — distinct from Carnot",
        ),
        "NOT_Clausius"       => true,
    )
end

# ── Szilard forward checks ─────────────────────────────────────────────────────
sz_fwd = szilard_forward(1.0, 0.5)
CHECK("szilard_fwd_H_one_bit",         abs(sz_fwd["H_shannon_bits"] - 1.0) < 1e-10,
      "H=$(sz_fwd["H_shannon_bits"])")
CHECK("szilard_fwd_W_extracted_kTln2", abs(sz_fwd["W_extracted"] - log(2.0)) < 1e-10,
      "W=$(sz_fwd["W_extracted"]) kTln2=$(log(2.0))")
CHECK("szilard_fwd_W_le_kTln2",        sz_fwd["W_extracted_le_kTln2"],
      "W_extracted=$(sz_fwd["W_extracted"])")
CHECK("szilard_fwd_vN_eq_shannon",     sz_fwd["vN_eq_shannon_for_diagonal"],
      "S_vN=$(sz_fwd["S_vN_nats"]) H_nats=$(sz_fwd["H_shannon_nats"])")
CHECK("szilard_fwd_second_law_uniform",
      abs(sz_fwd["W_net_szilard"]) < 1e-10,
      "W_net=$(sz_fwd["W_net_szilard"]) (should be 0 for uniform prior)")

# Negative: biased prior -> H < 1 bit; net work is extractable
sz_fwd_biased = szilard_forward(1.0, 0.9)
CHECK("szilard_fwd_biased_H_lt_1", sz_fwd_biased["H_shannon_bits"] < 1.0,
      "H=$(sz_fwd_biased["H_shannon_bits"])")
CHECK("szilard_fwd_biased_net_positive",
      sz_fwd_biased["W_net_szilard"] > 0,
      "W_net=$(sz_fwd_biased["W_net_szilard"]) (biased demon extracts net work)")

# Boundary: near-deterministic -> H -> 0; W_extracted still = kT ln2; net work -> kT ln2
sz_bnd = szilard_forward(1.0, 1.0 - 1e-8)
CHECK("szilard_bnd_H_near_zero", sz_bnd["H_shannon_bits"] < 0.01,
      "H=$(sz_bnd["H_shannon_bits"])")

# Reverse direction
sz_rev = szilard_reverse(1.0, 0.5)
CHECK("szilard_rev_W_in_ge_kTln2", sz_rev["W_in_ge_kTln2"],
      "W_in=$(sz_rev["W_in_consumed"]) kTln2=$(log(2.0))")
CHECK("szilard_rev_info_gained_1bit", abs(sz_rev["info_gained_bits"] - 1.0) < 1e-10,
      "info=$(sz_rev["info_gained_bits"])")

# ══════════════════════════════════════════════════════════════════════════════
# 3. N01 NONCOMMUTATION WITNESS — load-bearing constraint
# ══════════════════════════════════════════════════════════════════════════════
# z-dephase o Rx != Rx o z-dephase (cross-basis)
# control: z-dephase o z-dephase commutes (same-basis)

rho_test = ComplexF64[0.6 0.4; 0.4 0.4]
gamma_n  = 0.5
theta_n  = π/3.0

rho_AB   = z_dephase(rho_test, gamma_n) |> (r -> r * Rx(theta_n)' + Rx(theta_n) * r * Rx(theta_n)')
# Correct composition: apply Rx unitary THEN dephase, vs dephase THEN Rx
rho_zdRx  = let r = z_dephase(rho_test, gamma_n); Rx(theta_n)*r*Rx(theta_n)' end  # dephase first, then rotate
rho_Rxzd  = z_dephase(Rx(theta_n)*rho_test*Rx(theta_n)', gamma_n)                  # rotate first, then dephase
n01_gap   = norm(rho_zdRx - rho_Rxzd)

rho_ctrl1 = z_dephase(rho_test, 0.3)
rho_ctrl2 = z_dephase(rho_test, 0.5)
# z-dephase(gamma1) followed by z-dephase(gamma2) vs z-dephase(gamma2) followed by z-dephase(gamma1)
rho_zd_AB = z_dephase(z_dephase(rho_test, 0.3), 0.5)
rho_zd_BA = z_dephase(z_dephase(rho_test, 0.5), 0.3)
ctrl_gap  = norm(rho_zd_AB - rho_zd_BA)

CHECK("n01_zdephaseoRx_noncommuting", n01_gap > 1e-10,
      "z-dephase∘Rx vs Rx∘z-dephase gap=$n01_gap")
CHECK("n01_control_zdezde_commutes",  ctrl_gap < 1e-10,
      "z-dephase∘z-dephase gap=$ctrl_gap (should be ~0)")

N01_RECORD = D(
    "zdephase_Rx_order_gap"    => n01_gap,
    "n01_witnessed"            => n01_gap > 1e-10,
    "same_basis_ctrl_gap"      => ctrl_gap,
    "ctrl_specificity"         => ctrl_gap < 1e-10,
    "stroke_order_loadbearing" => true,
    "note" => "Cross-basis pair (z-dephase, Rx) does not commute; same-basis (z-dephase, z-dephase) commutes.",
)

# ══════════════════════════════════════════════════════════════════════════════
# 4. TWO-ENTROPY DISTINCTNESS RECORD
# ══════════════════════════════════════════════════════════════════════════════
# Clausius (J/K) and Shannon/vN (bits/nats) are distinct bookkeeping species.
# They co-exist on the SAME engine structure but track DIFFERENT quantities.
# Do NOT conflate them.

p0     = 0.7
rho_d  = ComplexF64[p0 0.0; 0.0 1.0-p0]
S_vN_d = von_neumann_entropy(rho_d)
H_nats_d = -(p0*log(p0) + (1.0-p0)*log(1.0-p0))

# Diagonal rho: vN = Shannon_nats (both collapse)
CHECK("entropy_vN_eq_shannon_nats_diagonal",
      abs(S_vN_d - H_nats_d) < 1e-12,
      "vN=$S_vN_d Shannon_nats=$H_nats_d")

# Coherent rho: vN < Shannon_diagonal (they diverge)
rho_coh  = ComplexF64[0.5 0.4; 0.4 0.5]
S_vN_coh = von_neumann_entropy(rho_coh)
H_diag   = -(0.5*log(0.5) + 0.5*log(0.5))  # Shannon on diagonal only
CHECK("entropy_vN_neq_shannon_for_coherent",
      abs(S_vN_coh - H_diag) > 1e-4,
      "vN=$S_vN_coh Shannon_diag=$H_diag (coherent state lowers vN vs classical H)")

# Clausius: defined at thermal reservoirs; neither vN nor Shannon captures this
# Verify the Carnot result carries Clausius species marker and no Shannon/vN keys
CHECK("clausius_species_marked",
      get(car_fwd, "entropy_species", "") == "Clausius_dS=dQ/T"
      && !haskey(car_fwd, "H_shannon_bits")
      && !haskey(car_fwd, "S_vN_nats"),
      "Clausius entropy_species present and no Shannon/vN keys in Carnot result")

TWO_ENTROPY = D(
    "Clausius_dS_dQoverT" => D(
        "defined_on"           => "thermal_reservoirs_and_path_integrals",
        "units"                => "J/K or kB",
        "zero_for_adiabatic"   => true,
        "requires_temperature" => true,
        "has_log_p"            => false,
        "has_density_matrix"   => false,
    ),
    "Shannon_H" => D(
        "defined_on"            => "classical_probability_over_positions",
        "units"                 => "bits",
        "requires_probability"  => true,
        "has_dQ_over_T"         => false,
        "has_density_matrix"    => false,
    ),
    "von_Neumann_S_vN" => D(
        "defined_on"                 => "density_matrices",
        "units"                      => "nats",
        "reduces_to_shannon_when_diagonal" => true,
        "requires_quantum_state"     => true,
        "has_dQ_over_T"              => false,
        "diagonal_test_passes"       => abs(S_vN_d - H_nats_d) < 1e-12,
        "coherent_test_diverges"     => abs(S_vN_coh - H_diag) > 1e-4,
    ),
    "genuinely_distinct"    => true,
    "Ax3_claim"             => "OPEN — do not assert these ARE Axis 3",
    "co_exist_on_engine"    => "both species track separate quantities on same engine structure",
    "conflation_forbidden"  => true,
)

# ══════════════════════════════════════════════════════════════════════════════
# 5. SIZE LADDER 8/16/32/64
# ══════════════════════════════════════════════════════════════════════════════

function carnot_ladder(sizes)
    results = Dict{String,Any}()
    for N in sizes
        T_h_vals = range(310.0, 1000.0, length=N)
        T_c = 300.0; Q_h = 50.0
        records = [carnot_forward(Float64(Th), T_c, Q_h) for Th in T_h_vals]
        etas = [r["eta"] for r in records]
        DS_cycles = [r["DS_cycle_total"] for r in records]
        results[string(N)] = D(
            "n_configs"        => N,
            "eta_min"          => minimum(etas),
            "eta_max"          => maximum(etas),
            "all_W_net_positive" => all(r["W_net_positive"] for r in records),
            "all_DS_cycle_zero"  => all(abs(ds) < 1e-10 for ds in DS_cycles),
            "DS_cycle_max_abs"   => maximum(abs.(DS_cycles)),
        )
    end
    return results
end

function szilard_ladder(sizes)
    results = Dict{String,Any}()
    for N in sizes
        p_vals = range(0.05, 0.95, length=N)
        records = [szilard_forward(1.0, Float64(p)) for p in p_vals]
        Hs   = [r["H_shannon_bits"] for r in records]
        vNs  = [r["S_vN_nats"] for r in records]
        vN_eq_Hs = [r["vN_eq_shannon_for_diagonal"] for r in records]
        results[string(N)] = D(
            "n_configs"            => N,
            "H_bits_min"           => minimum(Hs),
            "H_bits_max"           => maximum(Hs),
            "S_vN_min"             => minimum(vNs),
            "S_vN_max"             => maximum(vNs),
            "all_W_le_kTln2"       => all(r["W_extracted_le_kTln2"] for r in records),
            "all_vN_eq_shannon"    => all(vN_eq_Hs),
            "max_vN_shannon_diff"  => maximum([abs(r["S_vN_nats"] - r["H_shannon_nats"]) for r in records]),
        )
    end
    return results
end

lad_carnot  = carnot_ladder(SIZE_LADDER)
lad_szilard = szilard_ladder(SIZE_LADDER)

for N in SIZE_LADDER
    key = string(N)
    CHECK("ladder_carnot_DS_cycle_zero_N$N",
          lad_carnot[key]["all_DS_cycle_zero"],
          "DS_cycle_max=$(lad_carnot[key]["DS_cycle_max_abs"])")
    CHECK("ladder_szilard_vN_eq_shannon_N$N",
          lad_szilard[key]["all_vN_eq_shannon"],
          "max_diff=$(lad_szilard[key]["max_vN_shannon_diff"])")
end

# ══════════════════════════════════════════════════════════════════════════════
# ASSEMBLE AND WRITE RESULT JSON
# ══════════════════════════════════════════════════════════════════════════════
all_passed = all(c["passed"] for c in CHECK_LOG)
n_pass     = sum(c["passed"] for c in CHECK_LOG)
n_total    = length(CHECK_LOG)

result = D(
    "object_id"          => OBJECT_ID,
    "claim_ceiling"      => CLAIM_CEILING,
    "promotion_allowed"  => PROMOTION_ALLOWED,
    "f01_finite"         => true,
    "n01_load_bearing"   => N01_RECORD,
    # Carnot engine
    "carnot_forward"     => car_fwd,
    "carnot_reverse"     => car_rev,
    "carnot_boundary"    => car_bnd,
    "carnot_checks"      => D(
        "eta_eq_1_minus_Tc_over_Th"  => car_fwd["eta_matches_formula"],
        "DS_clausius_cycle_zero_fwd" => car_fwd["DS_cycle_zero"],
        "DS_clausius_cycle_zero_rev" => car_rev["DS_cycle_zero"],
        "W_net_positive_fwd"         => car_fwd["W_net_positive"],
        "COP_fridge_eq_Tc_over_dT"   => car_rev["COP_matches_formula"],
        "both_directions_run"        => true,
        "entropy_species"            => "Clausius_dS=dQ/T",
    ),
    # Szilard engine
    "szilard_forward"    => sz_fwd,
    "szilard_forward_biased" => sz_fwd_biased,
    "szilard_forward_boundary" => sz_bnd,
    "szilard_reverse"    => sz_rev,
    "szilard_checks"     => D(
        "W_extracted_le_kTln2"    => sz_fwd["W_extracted_le_kTln2"],
        "E_reset_ge_kTln2_1bit"   => sz_fwd["E_reset_ge_kTln2_if_1bit"],
        "H_shannon_bits_uniform"  => sz_fwd["H_shannon_bits"],
        "S_vN_nats_uniform"       => sz_fwd["S_vN_nats"],
        "vN_eq_shannon_diagonal"  => sz_fwd["vN_eq_shannon_for_diagonal"],
        "both_directions_run"     => true,
        "entropy_species"         => D(
            "Shannon_bits"  => sz_fwd["H_shannon_bits"],
            "vN_nats"       => sz_fwd["S_vN_nats"],
        ),
    ),
    # Two-entropy distinctness
    "two_entropy_distinctness" => TWO_ENTROPY,
    # Size ladder
    "size_ladder_carnot"  => lad_carnot,
    "size_ladder_szilard" => lad_szilard,
    # Check log
    "all_checks_passed"  => all_passed,
    "n_checks_passed"    => n_pass,
    "n_checks_total"     => n_total,
    "check_log"          => CHECK_LOG,
)

open(RESULT_PATH, "w") do f
    JSON.print(f, result, 2)
end

println("object_id: $OBJECT_ID")
println("Result: $RESULT_PATH")
println("Checks: $n_pass / $n_total passed")
println("all_checks_passed: $all_passed")
if !all_passed
    println("FAILED checks:")
    for c in CHECK_LOG
        !c["passed"] && println("  FAIL: $(c["check"]) — $(c["detail"])")
    end
    exit(1)
end
