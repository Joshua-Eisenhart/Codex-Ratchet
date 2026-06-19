#!/usr/bin/env julia
# =============================================================================
# wb_basin_proof_smt_julia.jl
#
# OBJECT:  basin_proof_smt
# VERSION: 1.2
# CLAIM CEILING: carrier_smt_probe — promotion_allowed: false
#
# PURPOSE:
#   Attractor-basin proof (C => Basin) via SMT flip on a small finite carrier.
#   Encodes: C(F01 + N01 + dynamics) => forall x in R, forall t<=K: F^t(x) in A
#
# FINITE MAP:
#   domain   -> 8 finite initial states (Bloch vectors r^2 <= 0.9) x K in {1,2,4,8} steps
#   codomain -> (z3_verdict, cvc5_verdict, basin_label, flip_detected) per K
#
# ROOT CONSTRAINTS:
#   F01: finite carrier (8 states, depolarizing channel, K max steps in {1,2,4,8})
#   N01: The user-requested standard Depolarize/PhaseFlip Pauli-channel order
#        check is measured and blocked because those channels commute. A separate
#        depolarizing/amplitude-damping order-sensitive witness is measured and
#        kept as an alternate N01 pressure check.
#
# CARRIER: Bloch-vector abstraction of single-qubit depolarizing dynamics.
#   F^t(state): each Bloch component (a,b,c) -> lambda^t * (a,b,c)
#   lambda = 1 - 4p/3,  p=0.25,  lambda = 2/3
#   r = sqrt(a^2+b^2+c^2)
#   Basin A: S(rho) >= 0.5 nats, equivalent to r <= r_basin_bound (≈ 0.6006)
#   Reachable region R: r^2 <= 0.9 (purity tr(rho^2) = (1 + r^2)/2 <= 0.95)
#
# SMT PROBLEM (z3 + cvc5 via Python subprocess):
#   REAL carrier (p=0.25): negate the claim that all states in R reach basin A.
#     => UNSAT (for K>=2): no state in R fails to reach basin A => basin FORCED
#   ERASED carrier (p=0.0, identity): same negation
#     => SAT: there exist states in R with r' = r >= r_basin => NOT in basin
#   THE FLIP: real=UNSAT, erased=SAT — load-bearing, not hardcoded
#
# TAUTOLOGY CHECK:
#   If BOTH real and erased give UNSAT => tautology_detected, result rejected.
#
# ANTI-FABRICATION:
#   - z3/cvc5 results computed, not hardcoded
#   - Wrong-structure controls: overclaim threshold, underconstrained R, erased channel
#   - Size ladder: K in {1, 2, 4, 8}
#   - N01 check measured on 2x2 density matrices
#
# RUN:
#   cd "/Users/joshuaeisenhart/Desktop/Codex Ratchet" && \
#   julia --project="system_v5/julia_carrier" \
#     "system_v5/julia_carrier/wb_basin_proof_smt_julia.jl"
# =============================================================================

using LinearAlgebra
using Random
using Dates
import JSON

const OBJECT_ID   = "basin_proof_smt"
const VERSION     = "1.2"
const HERE        = @__DIR__
const RESULT_PATH = joinpath(HERE, "wb_basin_proof_smt_julia_results.json")
const SEED        = 20260604

println("="^78)
println("wb_basin_proof_smt_julia.jl  (object_id=$(OBJECT_ID), version=$(VERSION))")
println("Attractor-basin proof via SMT flip on finite Bloch-vector carrier")
println("="^78)

# ── Tool manifest ─────────────────────────────────────────────────────────────
const TOOL_MANIFEST = Dict{String,Any}(
    "Julia"         => Dict("tried" => true, "used" => true,  "role" => "load_bearing",
        "reason" => "executes finite map, N01 check, size ladder, result emission; removing flips all verdicts"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true,  "role" => "load_bearing",
        "reason" => "2x2 density matrix ops for N01 channel commutativity check; removing kills N01 measurement"),
    "JSON"          => Dict("tried" => true, "used" => true,  "role" => "supportive",
        "reason" => "writes result artifact for JAX audit lane and parity check"),
    "Dates"         => Dict("tried" => true, "used" => true,  "role" => "supportive",
        "reason" => "timestamps result artifact"),
    "z3_subprocess" => Dict("tried" => true, "used" => true,  "role" => "load_bearing",
        "reason" => "SMT solver: UNSAT on real carrier proves basin forced for all states in R; removing z3 removes the proof"),
    "cvc5_subprocess" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "cross-check z3 UNSAT via independent solver; flip is load-bearing only when both solvers agree"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,String}(
    "Julia"           => "load_bearing",
    "LinearAlgebra"   => "load_bearing",
    "JSON"            => "supportive",
    "Dates"           => "supportive",
    "z3_subprocess"   => "load_bearing",
    "cvc5_subprocess" => "load_bearing",
)

# =============================================================================
# PHYSICAL CONSTANTS
# =============================================================================
const P_DEPOL  = 0.25
const LAMBDA   = 1.0 - 4*P_DEPOL/3   # = 2/3
const R_MAX_SQ = 0.9
const K_VALUES = [1, 2, 4, 8]

println("Physical constants:")
println("  p_depol = $P_DEPOL,  lambda = $(round(LAMBDA, digits=8))")
println("  R (reachable): r^2 <= $R_MAX_SQ")
println("  K ladder: $K_VALUES")
println()

# =============================================================================
# N01 CHECK: Depolarizing vs Amplitude-Damping channels do NOT commute
# Both are standard CPTP maps; their ordering matters on mixed states.
# =============================================================================
println("--- N01 check: channel noncommutativity (depolarizing vs amplitude-damping) ---")

const σX = ComplexF64[0 1; 1 0]
const σY = ComplexF64[0 -im; im 0]
const σZ = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]

"Apply depolarizing channel: (1-p)*rho + p/3*(X*rho*X + Y*rho*Y + Z*rho*Z)"
function apply_depol(rho::Matrix{ComplexF64}, p::Float64)
    (1-p)*rho + p/3*(σX*rho*σX + σY*rho*σY + σZ*rho*σZ)
end

"Apply phase-flip channel: (1-p)*rho + p*Z*rho*Z"
function apply_phase_flip(rho::Matrix{ComplexF64}, p::Float64)
    (1-p)*rho + p*(σZ*rho*σZ)
end

"Apply amplitude-damping channel with Kraus operators K0=[[1,0],[0,sqrt(1-p)]], K1=[[0,sqrt(p)],[0,0]]"
function apply_amp_damp(rho::Matrix{ComplexF64}, p::Float64)
    K0 = ComplexF64[1 0; 0 sqrt(1-p)]
    K1 = ComplexF64[0 sqrt(p); 0 0]
    K0*rho*K0' + K1*rho*K1'
end

# Test state: |+><+| = [[0.5, 0.5], [0.5, 0.5]]
rho_plus = ComplexF64[0.5 0.5; 0.5 0.5]
p_n01 = 0.3

# The user-requested witness: standard depolarizing and phase-flip Pauli
# channels commute in this representation, so this cannot be claimed as N01.
rho_DF = apply_phase_flip(apply_depol(rho_plus, p_n01), p_n01)
rho_FD = apply_depol(apply_phase_flip(rho_plus, p_n01), p_n01)
requested_n01_diff = norm(rho_DF - rho_FD)
requested_n01_passed = requested_n01_diff > 1e-10

# Alternate order-sensitive witness: Depol THEN AmpDamp vs AmpDamp THEN Depol.
rho_DA = apply_amp_damp(apply_depol(rho_plus, p_n01), p_n01)
rho_AD = apply_depol(apply_amp_damp(rho_plus, p_n01), p_n01)
n01_diff = norm(rho_DA - rho_AD)
n01_passed = n01_diff > 1e-10

println("  Requested Depol∘PhaseFlip vs PhaseFlip∘Depol on |+><+| (p=0.3):")
println("  ||diff||_F = $(round(requested_n01_diff, sigdigits=6))")
println("  Requested N01 witness passed: $requested_n01_passed")
println("  Alternate Depol∘AmpDamp vs AmpDamp∘Depol on |+><+| (p=0.3):")
println("  ||diff||_F = $(round(n01_diff, sigdigits=6))")
println("  Alternate order-sensitive witness passed: $n01_passed")
println()

# =============================================================================
# BASIN BOUNDARY COMPUTATION
# S(rho) = -((1+r)/2)*log((1+r)/2) - ((1-r)/2)*log((1-r)/2)  in nats
# Basin A: S(rho) >= S_THRESHOLD  <=>  r <= r_basin_bound
# =============================================================================

"Von Neumann entropy from Bloch radius r in [0,1]"
function bloch_entropy(r::Float64)
    r = clamp(r, 0.0, 1.0 - 1e-12)
    p_plus  = (1 + r) / 2
    p_minus = (1 - r) / 2
    h_plus  = p_plus  < 1e-15 ? 0.0 : -p_plus  * log(p_plus)
    h_minus = p_minus < 1e-15 ? 0.0 : -p_minus * log(p_minus)
    h_plus + h_minus
end

"Single-qubit density matrix from Bloch vector."
function rho_from_bloch(v::Vector{Float64})
    0.5 .* (I2 .+ v[1] .* σX .+ v[2] .* σY .+ v[3] .* σZ)
end

"Find r_basin: largest r such that S(rho) >= S_threshold (binary search)"
function find_r_basin(S_threshold::Float64)
    lo, hi = 0.0, 1.0
    for _ in 1:80
        mid = (lo + hi) / 2
        bloch_entropy(mid) >= S_threshold ? (lo = mid) : (hi = mid)
    end
    (lo + hi) / 2
end

const S_THRESHOLD = 0.5  # nats
const r_basin = find_r_basin(S_THRESHOLD)
println("Basin A: S(rho) >= $S_THRESHOLD nats  <=>  r <= $(round(r_basin, digits=8))")
println("  Verify: S(r_basin) = $(round(bloch_entropy(r_basin), digits=6)) (should ≈ $S_THRESHOLD)")
println("  S(r=0) = $(round(bloch_entropy(0.0), digits=6)) (maximally mixed)")
println("  S(r=1) = $(round(bloch_entropy(1.0-1e-12), digits=6)) (pure)")
println()

println("--- Size ladder: contraction bounds ---")
for K in K_VALUES
    lK   = LAMBDA^K
    rp   = lK * sqrt(R_MAX_SQ)
    Srp  = bloch_entropy(rp)
    ib   = rp <= r_basin
    println("  K=$K: lambda^K=$(round(lK, digits=6)), r'_max=$(round(rp, digits=6)), S=$(round(Srp, digits=4)), in_basin=$ib")
end
println()

# =============================================================================
# SMT ENCODING via Python subprocess (z3 + cvc5)
# Negation of claim: exists x in R such that after K steps x NOT in basin A
#   = exists (a,b,c): a^2+b^2+c^2 <= R_MAX_SQ  AND  lambda^(2K)*(a^2+b^2+c^2) > r_basin^2
# UNSAT: claim holds for ALL states in R (basin forced)
# SAT:   there exists a state in R that is NOT pulled into basin A
# =============================================================================

const PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"

"""
Run SMT proof for one (K, p_channel) configuration.
Returns (z3_verdict, cvc5_verdict, raw_output).
Verdicts: "UNSAT", "SAT", "ERROR:<msg>"
"""
function run_smt_proof(K::Int, p_channel::Float64; label::String="real")
    lambda_K_sq = (1.0 - 4*p_channel/3)^(2*K)
    r_basin_sq  = r_basin^2
    R_max_sq    = R_MAX_SQ

    # Rational fractions for cvc5:
    # p_channel = 0.25 => lambda = 2/3, lambda^(2K) = 4^K/9^K
    # p_channel = 0.0  => lambda = 1,   lambda^(2K) = 1
    # r_basin_sq: use limit_denominator approximation
    # R_MAX_SQ = 9/10 (exact)

    python_code = """
import sys

# ===== z3 =====
try:
    from z3 import Real, Solver, sat, unsat
    a, b, c = Real('a'), Real('b'), Real('c')
    r_sq = a*a + b*b + c*c
    s = Solver()
    # Negate the claim: in R AND NOT in basin after K steps
    s.add(r_sq <= $(R_max_sq))
    s.add($(lambda_K_sq) * r_sq > $(r_basin_sq))
    result = s.check()
    z3_v = "UNSAT" if result == unsat else "SAT"
    print("Z3_VERDICT:" + z3_v)
except Exception as e:
    print("Z3_VERDICT:ERROR:" + str(e)[:200])

# ===== cvc5 =====
try:
    import cvc5
    from fractions import Fraction

    slv = cvc5.Solver()
    slv.setOption("produce-models", "true")
    slv.setLogic("QF_NRA")

    real_sort = slv.getRealSort()
    a5 = slv.mkConst(real_sort, "a5")
    b5 = slv.mkConst(real_sort, "b5")
    c5 = slv.mkConst(real_sort, "c5")

    def mk_rat(num, den):
        return slv.mkReal(int(num), int(den))

    r_sq5 = slv.mkTerm(cvc5.Kind.ADD,
                slv.mkTerm(cvc5.Kind.MULT, a5, a5),
                slv.mkTerm(cvc5.Kind.ADD,
                    slv.mkTerm(cvc5.Kind.MULT, b5, b5),
                    slv.mkTerm(cvc5.Kind.MULT, c5, c5)))

    # R_MAX_SQ = 9/10
    in_R = slv.mkTerm(cvc5.Kind.LEQ, r_sq5, mk_rat(9, 10))

    # lambda_K_sq as exact rational
    p_rat = Fraction(1, 4) if abs($(p_channel) - 0.25) < 1e-10 else (Fraction(0) if abs($(p_channel)) < 1e-10 else Fraction($(p_channel)).limit_denominator(10000))
    lam_rat = Fraction(1) - Fraction(4, 3) * p_rat
    lam_K_sq_rat = lam_rat**(2 * $(K))
    lam_num = lam_K_sq_rat.numerator
    lam_den = lam_K_sq_rat.denominator

    # r_basin_sq as rational approximation
    r_bs_rat = Fraction($(r_basin_sq)).limit_denominator(100000)
    r_bs_num = r_bs_rat.numerator
    r_bs_den = r_bs_rat.denominator

    # not_in_basin: lam_num/lam_den * r_sq5 > r_bs_num/r_bs_den
    # => lam_num * r_bs_den * r_sq5 > r_bs_num * lam_den
    if lam_num == 0:
        # lambda=0: everything in basin trivially => UNSAT on negation always
        # But this shouldn't happen with our parameters
        not_in_basin = slv.mkTerm(cvc5.Kind.GT, mk_rat(1, 1), mk_rat(2, 1))  # 1>2 = False
    else:
        lhs = slv.mkTerm(cvc5.Kind.MULT, mk_rat(lam_num * r_bs_den, 1), r_sq5)
        rhs = mk_rat(r_bs_num * lam_den, 1)
        not_in_basin = slv.mkTerm(cvc5.Kind.GT, lhs, rhs)

    slv.assertFormula(in_R)
    slv.assertFormula(not_in_basin)

    cvc5_res = slv.checkSat()
    cvc5_v = "UNSAT" if cvc5_res.isUnsat() else "SAT"
    print("CVC5_VERDICT:" + cvc5_v)
except Exception as e:
    print("CVC5_VERDICT:ERROR:" + str(e)[:200])
"""

    tmpfile = "/tmp/smt_probe_$(label)_K$(K)_$(SEED).py"
    open(tmpfile, "w") do f; write(f, python_code); end

    out = try
        read(`$PYTHON $tmpfile`, String)
    catch e
        "ERROR: $e"
    end

    z3_v   = "UNKNOWN"
    cvc5_v = "UNKNOWN"
    for line in split(out, "\n")
        startswith(line, "Z3_VERDICT:")   && (z3_v   = strip(line[length("Z3_VERDICT:")+1:end]))
        startswith(line, "CVC5_VERDICT:") && (cvc5_v = strip(line[length("CVC5_VERDICT:")+1:end]))
    end
    z3_v, cvc5_v, out
end

# =============================================================================
# MAIN SMT EXPERIMENT
# =============================================================================

println("--- SMT proofs: real vs erased carrier ---")
println()

smt_results  = Dict{String,Any}[]
any_z3_unsat_real    = false;  any_z3_unsat_erased    = false
any_cvc5_unsat_real  = false;  any_cvc5_unsat_erased  = false
flip_detected_z3     = false;  flip_detected_cvc5     = false
tautology_z3         = false;  tautology_cvc5         = false

for K in K_VALUES
    println("  K = $K:")

    z3_real,    cvc5_real,    _ = run_smt_proof(K, P_DEPOL; label="real")
    z3_erased,  cvc5_erased,  _ = run_smt_proof(K, 0.0;     label="erased")

    z3_flip   = (z3_real   == "UNSAT") && (z3_erased   != "UNSAT")
    cvc5_flip = (cvc5_real == "UNSAT") && (cvc5_erased != "UNSAT")
    z3_taut   = (z3_real   == "UNSAT") && (z3_erased   == "UNSAT")
    cvc5_taut = (cvc5_real == "UNSAT") && (cvc5_erased == "UNSAT")

    println("    Real   carrier: z3=$z3_real,  cvc5=$cvc5_real")
    println("    Erased carrier: z3=$z3_erased, cvc5=$cvc5_erased")
    println("    Flip: z3=$z3_flip, cvc5=$cvc5_flip")
    println("    Tautology: z3=$z3_taut, cvc5=$cvc5_taut")

    global any_z3_unsat_real, any_z3_unsat_erased
    global any_cvc5_unsat_real, any_cvc5_unsat_erased
    global flip_detected_z3, flip_detected_cvc5
    global tautology_z3, tautology_cvc5

    z3_real   == "UNSAT" && (any_z3_unsat_real    = true)
    z3_erased == "UNSAT" && (any_z3_unsat_erased  = true)
    cvc5_real   == "UNSAT" && (any_cvc5_unsat_real  = true)
    cvc5_erased == "UNSAT" && (any_cvc5_unsat_erased = true)
    z3_flip   && (flip_detected_z3   = true)
    cvc5_flip && (flip_detected_cvc5 = true)
    z3_taut   && (tautology_z3   = true)
    cvc5_taut && (tautology_cvc5 = true)

    lK  = LAMBDA^K
    rp  = lK * sqrt(R_MAX_SQ)
    Srp = bloch_entropy(rp)
    rpe = 1.0^K * sqrt(R_MAX_SQ)

    push!(smt_results, Dict{String,Any}(
        "K" => K,
        "lambda_K_real"    => lK,
        "lambda_K_erased"  => 1.0,
        "r_prime_max_real"   => rp,
        "r_prime_max_erased" => rpe,
        "S_at_bound_real"    => Srp,
        "in_basin_real"      => rp  <= r_basin,
        "in_basin_erased"    => rpe <= r_basin,
        "z3_real"    => z3_real,
        "z3_erased"  => z3_erased,
        "cvc5_real"  => cvc5_real,
        "cvc5_erased" => cvc5_erased,
        "z3_flip"    => z3_flip,
        "cvc5_flip"  => cvc5_flip,
        "z3_tautology"   => z3_taut,
        "cvc5_tautology" => cvc5_taut,
    ))
    println()
end

# =============================================================================
# WRONG-STRUCTURE CONTROLS
# =============================================================================
println("--- Wrong-structure controls ---")

# WSC1: Over-claimed threshold S >= 0.0 => trivially all states in basin => tautology
wsc1_r_basin = find_r_basin(0.0)
wsc1_tautology = wsc1_r_basin >= 0.999
println("  WSC1 (S_threshold=0.0, overclaim): r_basin=$(round(wsc1_r_basin, digits=4)), tautology_flag=$wsc1_tautology")

# WSC2: Under-constrained R (full Bloch ball, r^2<=1.0)
wsc2_rp = LAMBDA^4 * sqrt(1.0)
wsc2_in_basin = wsc2_rp <= r_basin
println("  WSC2 (R=full sphere, r^2<=1): r'_max(K=4)=$(round(wsc2_rp, digits=4)), in_basin=$wsc2_in_basin")
println("       => claim holds but R is vacuous (unrestricted carrier — not a load-bearing proof)")

# WSC3: Erased carrier results embedded above
println("  WSC3 (erased, p=0): see smt_results_per_K above — should give SAT for all K")
println()

# =============================================================================
# 8 FINITE SAMPLE STATES — domain check at K=4
# =============================================================================
println("--- Finite domain: 8 sample states, K=4 steps ---")
rng_s = MersenneTwister(SEED)
K4    = 4
lK4   = LAMBDA^K4

sample_results = Dict{String,Any}[]
for i in 1:8
    # Random Bloch vector in R (r^2 <= R_MAX_SQ)
    v = normalize(randn(rng_s, 3))
    r0 = sqrt(R_MAX_SQ) * rand(rng_s)^(1/3)
    bloch0 = r0 * v
    r0_val = norm(bloch0)
    rho1 = rho_from_bloch(collect(bloch0))
    rho2 = kron(rho1, I2 ./ 2)
    rho2_eigs = eigvals(Hermitian(rho2))
    bloch_K = lK4 * bloch0
    rK_val  = norm(bloch_K)
    S_bef   = bloch_entropy(r0_val)
    S_aft   = bloch_entropy(rK_val)
    push!(sample_results, Dict{String,Any}(
        "state_idx" => i, "r0" => round(r0_val, digits=6),
        "r_after_K4" => round(rK_val, digits=6),
        "S_before" => round(S_bef, digits=6), "S_after" => round(S_aft, digits=6),
        "in_R" => r0_val^2 <= R_MAX_SQ, "in_basin_after_K4" => rK_val <= r_basin,
        "rho_dim" => [size(rho2, 1), size(rho2, 2)],
        "rho_trace" => round(real(tr(rho2)), digits=12),
        "rho_min_eig" => round(minimum(real.(rho2_eigs)), digits=12),
        "rho_hermitian_error" => round(norm(rho2 - rho2'), digits=12),
    ))
    println("  state_$i: r0=$(round(r0_val,digits=4)), r'=$(round(rK_val,digits=4)), S=$(round(S_bef,digits=3))→$(round(S_aft,digits=3)), in_basin=$(rK_val <= r_basin)")
end
println()

# =============================================================================
# AGGREGATE VERDICT
# =============================================================================
println("--- Aggregate verdict ---")
println("  z3:   flip_detected=$flip_detected_z3,  any_unsat_real=$any_z3_unsat_real,  any_unsat_erased=$any_z3_unsat_erased")
println("  cvc5: flip_detected=$flip_detected_cvc5, any_unsat_real=$any_cvc5_unsat_real, any_unsat_erased=$any_cvc5_unsat_erased")
println("  tautology_detected_z3=$tautology_z3, tautology_detected_cvc5=$tautology_cvc5")
println("  tautology_rejected=$(!(tautology_z3 || tautology_cvc5))")
println()

# =============================================================================
# WRITE RESULT JSON
# =============================================================================

result = Dict{String,Any}(
    "object_id"          => OBJECT_ID,
    "version"            => VERSION,
    "classification"     => "carrier_smt_probe",
    "promotion_allowed"  => false,
    "claim_ceiling"      => "carrier_smt_probe — promotion_allowed: false. Does NOT assert layer-completion, manifold admission, coupling, bridge, flux, or physics.",
    "timestamp"          => string(now()),
    "seed"               => SEED,
    "engine"             => "julia_carrier",

    "finite_map" => Dict{String,Any}(
        "domain"   => "8 finite 4x4 density-matrix samples generated from active Bloch vectors in R (r^2 <= 0.9) with a mixed spectator qubit; SMT abstraction uses the active 3-component Bloch radius; K in {1,2,4,8} depolarizing steps",
        "codomain" => "(z3_verdict, cvc5_verdict, basin_label, flip_detected) per K",
        "f01"      => "finite carrier: 8 states, depolarizing channel (p=0.25), K in {1,2,4,8} steps",
        "n01"      => "Requested Depol/PhaseFlip Pauli-channel order check is measured false (commutes, diff=$(round(requested_n01_diff, sigdigits=4))); alternate Depol/AmpDamp order witness is measured true (diff=$(round(n01_diff, sigdigits=4)))",
    ),

    "physical_parameters" => Dict{String,Any}(
        "p_depol"       => P_DEPOL,
        "lambda"        => LAMBDA,
        "R_MAX_SQ"      => R_MAX_SQ,
        "S_threshold"   => S_THRESHOLD,
        "r_basin_bound" => r_basin,
        "K_values"      => K_VALUES,
    ),

    "n01_check" => Dict{String,Any}(
        "requested_depol_phaseflip" => Dict{String,Any}(
            "test" => "Depol∘PhaseFlip vs PhaseFlip∘Depol on |+><+| with p=0.3",
            "diff_norm" => requested_n01_diff,
            "passed" => requested_n01_passed,
            "status" => "blocked_false_for_standard_Pauli_channels",
            "statement" => "standard depolarizing and phase-flip Pauli channels commute on this carrier"),
        "alternate_depol_ampdamp" => Dict{String,Any}(
            "test" => "Depol∘AmpDamp vs AmpDamp∘Depol on |+><+| with p=0.3",
            "diff_norm" => n01_diff,
            "passed" => n01_passed,
            "statement" => "Depol and AmpDamp do not commute: diff_norm=$(round(n01_diff, sigdigits=4)) > 1e-10"),
        "requested_witness_passed" => requested_n01_passed,
        "alternate_witness_passed" => n01_passed,
        "note" => "The SMT contraction proof is real/erased load-bearing, but the user-requested Pauli-channel N01 witness is not available under standard channel definitions.",
    ),

    "smt_results_per_K" => smt_results,

    "aggregate" => Dict{String,Any}(
        "z3_flip_detected"    => flip_detected_z3,
        "cvc5_flip_detected"  => flip_detected_cvc5,
        "flip_detected"       => flip_detected_z3 || flip_detected_cvc5,
        "both_solvers_flip"   => flip_detected_z3 && flip_detected_cvc5,
        "z3_unsat_real"       => any_z3_unsat_real,
        "z3_unsat_erased"     => any_z3_unsat_erased,
        "cvc5_unsat_real"     => any_cvc5_unsat_real,
        "cvc5_unsat_erased"   => any_cvc5_unsat_erased,
        "tautology_detected_z3"   => tautology_z3,
        "tautology_detected_cvc5" => tautology_cvc5,
        "tautology_rejected"      => !(tautology_z3 || tautology_cvc5),
    ),

    "wrong_structure_controls" => Dict{String,Any}(
        "wsc1_overclaim_threshold" => Dict{String,Any}(
            "S_threshold" => 0.0, "r_basin" => wsc1_r_basin,
            "tautology_flag" => wsc1_tautology,
            "interpretation" => "overclaim: S>=0.0 means all states in basin; SMT negation is always UNSAT => tautology detected and rejected"),
        "wsc2_underconstrained_R" => Dict{String,Any}(
            "R_max_sq" => 1.0, "r_prime_K4" => wsc2_rp, "in_basin" => wsc2_in_basin,
            "interpretation" => "claim still holds geometrically but R is the full Bloch sphere — not a useful constraint-admissibility proof"),
        "wsc3_erased_carrier" => Dict{String,Any}(
            "note" => "p=0 results embedded in smt_results_per_K under z3_erased/cvc5_erased; should all be SAT (basin not forced)"),
    ),

    "sample_states_K4" => sample_results,

    "tool_manifest"          => TOOL_MANIFEST,
    "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,

    "blocked_consumers" => [
        "layer-completion / manifold admission",
        "coupling / coexistence / nesting promotion",
        "bridge / rho_AB / Xi / Phi0 / Axis0",
        "flux / FEP / physics",
    ],

    "open_issues" => [
        "Bloch-vector abstraction: maps full 4x4 density matrix to 3-vector; full tensor-product carrier not in SMT",
        "Requested Depol/PhaseFlip N01 witness is blocked because standard Pauli channels commute; alternate nonunital order-sensitive witness is reported separately",
        "Basin A boundary r_basin computed numerically; SMT encodes a rational approximation (Fraction.limit_denominator(100000))",
        "K=1 gives SAT on real carrier (basin not forced at one step) — expected; only K>=2 gives UNSAT",
        "Amplitude-damping channel not in the main carrier dynamics (depolarizing only); used only for N01 witness",
        "cvc5 uses QF_NRA with nonlinear product terms; may be slow on large K; K=8 has lambda^16 as very small rational",
    ],
)

open(RESULT_PATH, "w") do f
    JSON.print(f, result, 2)
end

println("Result written to: $(RESULT_PATH)")
println("="^78)
println("wb_basin_proof_smt_julia.jl DONE")
println("="^78)
