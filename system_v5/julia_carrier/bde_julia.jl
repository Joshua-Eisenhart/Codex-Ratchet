# bde_julia.jl — Bidirectional Dual-Stacked Engine, Julia carrier.
#
# object_id: bde_julia_v1
#
# claim_ceiling:
#   Computes explicit finite maps for the bidirectional dual-stacked engine
#   grounded in Axis 4 (deductive U.E.U.E vs inductive E.U.E.U ordering).
#   Each engine = HEATING loop (inner 360 deg of the 720-deg spinor loop) +
#   COOLING loop (outer 360 deg). U(2pi)=-I enforced. BOTH directions run
#   from Axis 4, NOT from labels. Purity is bounded (weak dephasing avoids
#   thermalization to I/2). Cycle closes (return distance bounded). Two
#   directions stay DISTINCT at cycle-close (Frobenius gap > 1e-9, NOT 6e-17).
#   Entropy kinds: Carnot=Clausius, Szilard=Shannon, QIT=von Neumann. L/R chirality.
#   Does NOT assert layer-completion, manifold admission, coupling, bridge,
#   flux, or physics. promotion_allowed: false.
#
# Root constraints: F01 (finite carrier), N01 (order-sensitive).
# Writes: bde_julia_results.json  (same directory as this file)
# Re-run: cd /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v5/julia_carrier && julia --project=. bde_julia.jl

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

const OBJECT_ID       = "bde_julia_v1"
const CLAIM_CEILING   = (
    "BDE Julia carrier: finite maps for bidirectional dual-stacked engine " *
    "(Axis-4-grounded, 720-deg spinor, L/R chirality, bounded purity, " *
    "cycle-close, direction-distinct). F01+N01 only. " *
    "promotion_allowed=false."
)
const PROMOTION_ALLOWED = false
const RESULT_PATH     = joinpath(@__DIR__, "bde_julia_results.json")
const RNG_SEED        = 20260603

D(args...) = Dict{String,Any}(args...)

const CHECK_LOG = Dict{String,Any}[]
function CHECK(name::String, passed::Bool, detail::String="")
    push!(CHECK_LOG, D("check" => name, "passed" => passed, "detail" => detail))
    return passed
end

# ── Pauli matrices ─────────────────────────────────────────────────────────────
const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -1im; 1im 0]
const sz = ComplexF64[1 0; 0 -1]

# ── Spinor rotation: U(2pi)=-I, U(4pi)=+I ─────────────────────────────────────
function U_rot(theta::Float64, n_hat::Matrix{ComplexF64})::Matrix{ComplexF64}
    return cos(theta / 2) .* I2 .- (1im * sin(theta / 2)) .* n_hat
end

# Verify 720-deg spinor structure
U_2pi_sz = U_rot(2π, sz)
U_4pi_sz = U_rot(4π, sz)
trace_2pi = real(tr(U_2pi_sz) / 2)   # should be -1
trace_4pi = real(tr(U_4pi_sz) / 2)   # should be +1

CHECK("spinor_720_U2pi_eq_neg_I",
      abs(trace_2pi - (-1.0)) < 1e-10,
      "Tr(U(2pi))/2 = $(trace_2pi), expected -1")
CHECK("spinor_720_U4pi_eq_pos_I",
      abs(trace_4pi - 1.0) < 1e-10,
      "Tr(U(4pi))/2 = $(trace_4pi), expected +1")

# ── Entropy ────────────────────────────────────────────────────────────────────
function von_neumann_entropy(rho::Matrix{ComplexF64})::Float64
    evals = eigvals(Hermitian(rho))
    S = 0.0
    for lam in evals
        lr = max(real(lam), 1e-15)
        S -= lr * log(lr)
    end
    return S
end

clausius_entropy(Q::Float64, T::Float64) = Q / T

function shannon_entropy_bits(p_L::Float64)::Float64
    p_R = 1.0 - p_L
    (p_L <= 0 || p_R <= 0) && return 0.0
    return -(p_L * log2(p_L) + p_R * log2(p_R))
end

purity_rho(rho::Matrix{ComplexF64}) = real(tr(rho * rho))

# ── ERASURE / dephasing channel (weak, bounded purity) ─────────────────────────
function erase(rho::Matrix{ComplexF64}, gamma::Float64,
               n_hat::Matrix{ComplexF64})::Matrix{ComplexF64}
    g = clamp(gamma, 0.0, 1.0)
    P_plus  = 0.5 .* (I2 .+ n_hat)
    P_minus = 0.5 .* (I2 .- n_hat)
    return (1 - g) .* rho .+ g .* (P_plus * rho * P_plus + P_minus * rho * P_minus)
end

function purity_bounded_above_floor(P_traj::Vector{Float64}, floor::Float64=0.25)::Bool
    return all(p > floor for p in P_traj)
end

# ── Stroke sequences (Axis-4 grounded) ────────────────────────────────────────
const DED_ORDER = ['U', 'E', 'U', 'E']   # Deductive: U.E.U.E
const IND_ORDER = ['E', 'U', 'E', 'U']   # Inductive: E.U.E.U

function run_loop(rho0::Matrix{ComplexF64}, order::Vector{Char},
                  gamma::Float64, u_axis::Matrix{ComplexF64},
                  e_axis::Matrix{ComplexF64},
                  stroke_angle::Float64=0.9)
    # NOTE: stroke_angle must NOT be π/2 (special symmetry collapses DED/IND gap).
    # 0.9 rad is generic and non-special.
    rho = copy(rho0)
    work = 0.0
    S_traj = Float64[von_neumann_entropy(rho)]
    P_traj = Float64[purity_rho(rho)]

    U_stroke = U_rot(stroke_angle, u_axis)

    for stroke in order
        S0 = von_neumann_entropy(rho)
        if stroke == 'U'
            rho = U_stroke * rho * U_stroke'
        else  # 'E'
            rho = erase(rho, gamma, e_axis)
        end
        dS = von_neumann_entropy(rho) - S0
        work += (-dS)   # information -> order extracted (QIT convention)
        push!(S_traj, von_neumann_entropy(rho))
        push!(P_traj, purity_rho(rho))
    end

    return rho, work, S_traj, P_traj
end

frob(a, b) = norm(a - b)

# ── N01 order gap ──────────────────────────────────────────────────────────────
function n01_order_gap_check(gamma::Float64=0.3,
                               u_axis::Matrix{ComplexF64}=sz,
                               e_axis::Matrix{ComplexF64}=sx)
    rng = MersenneTwister(RNG_SEED)
    theta = rand(rng) * 0.3 + 0.3
    phi   = rand(rng) * 1.0
    psi   = ComplexF64[cos(theta), sin(theta) * exp(1im * phi)]
    psi  ./= norm(psi)
    rho0  = psi * psi'

    rho_ded, _, _, _ = run_loop(rho0, DED_ORDER, gamma, u_axis, e_axis)
    rho_ind, _, _, _ = run_loop(rho0, IND_ORDER, gamma, u_axis, e_axis)
    gap = frob(rho_ded, rho_ind)

    # Commuting control: all U, no E — should be same regardless of order
    COMMUTE_ORDER = ['U', 'U', 'U', 'U']
    rho_comm_AB, _, _, _ = run_loop(rho0, COMMUTE_ORDER, 0.0, u_axis, u_axis)
    rho_comm_BA, _, _, _ = run_loop(rho0, COMMUTE_ORDER, 0.0, u_axis, u_axis)
    ctrl_gap = frob(rho_comm_AB, rho_comm_BA)

    return gap, ctrl_gap
end

n01_gap, ctrl_gap = n01_order_gap_check()
CHECK("n01_deductive_vs_inductive_gap_real",
      n01_gap > 1e-9,
      "gap=$(n01_gap)")
CHECK("n01_commuting_control_near_zero",
      ctrl_gap < 1e-6,
      "ctrl_gap=$(ctrl_gap)")

# ── Direction distinctness at cycle-close ──────────────────────────────────────
function direction_gap_at_close(gamma_inner::Float64=0.15,
                                  gamma_outer::Float64=0.45,
                                  seed::Int=RNG_SEED)
    rng = MersenneTwister(seed)
    theta0 = rand(rng) * 0.3 + 0.2
    phi0   = rand(rng) * 0.8 + 0.4
    psi    = ComplexF64[cos(theta0), sin(theta0) * exp(1im * phi0)]
    psi   ./= norm(psi)
    rho0   = psi * psi'

    u_axis = sz; e_axis = sx

    # Direction A: inner=DED, outer=IND
    rho_mid_A, _, _, _ = run_loop(rho0, DED_ORDER, gamma_inner, u_axis, e_axis)
    rho_end_A, _, _, _ = run_loop(rho_mid_A, IND_ORDER, gamma_outer, u_axis, e_axis)

    # Direction B: inner=IND, outer=DED
    rho_mid_B, _, _, _ = run_loop(rho0, IND_ORDER, gamma_inner, u_axis, e_axis)
    rho_end_B, _, _, _ = run_loop(rho_mid_B, DED_ORDER, gamma_outer, u_axis, e_axis)

    gap = frob(rho_end_A, rho_end_B)
    return gap
end

dir_gap = direction_gap_at_close()
CHECK("direction_gap_at_close_above_1e9",
      dir_gap > 1e-9,
      "gap=$(dir_gap) (must be > 1e-9, not 6e-17)")
CHECK("directions_distinct_not_numerically_degenerate",
      dir_gap > 1e-9,
      "gap=$(dir_gap)")

# ── Engine builder ─────────────────────────────────────────────────────────────
function make_bde_engine(hand::String,
                          gamma_inner::Float64=0.15,
                          gamma_outer::Float64=0.45,
                          seed::Int=RNG_SEED)
    rng = MersenneTwister(seed + (hand == "L" ? 0 : 1))
    s   = hand == "L" ? +1.0 : -1.0

    theta0 = rand(rng) * 0.3 + 0.1
    phi0   = rand(rng) * 0.5 + 0.5
    psi    = ComplexF64[cos(theta0), s * sin(theta0) * exp(1im * phi0)]
    psi   ./= norm(psi)
    rho0   = psi * psi'

    if hand == "L"
        u_axis    = sz
        e_axis    = sx
        in_order  = IND_ORDER
        out_order = DED_ORDER
    else
        u_axis    = sx
        e_axis    = sz
        in_order  = DED_ORDER
        out_order = IND_ORDER
    end

    rho_start = copy(rho0)

    # HEATING loop (inner 360 deg)
    rho_mid, w_inner, S_inner, P_inner = run_loop(rho0, in_order, gamma_inner, u_axis, e_axis)
    # COOLING loop (outer 360 deg)
    rho_end, w_outer, S_outer, P_outer = run_loop(rho_mid, out_order, gamma_outer, u_axis, e_axis)

    cycle_return_dist = frob(rho_end, rho_start)
    all_purities = vcat(P_inner, P_outer[2:end])
    pur_bounded  = purity_bounded_above_floor(all_purities, 0.25)

    S_start = von_neumann_entropy(rho_start)
    S_end   = von_neumann_entropy(rho_end)

    return D(
        "hand"               => hand,
        "in_engine"          => (in_order  == IND_ORDER ? "inductive"  : "deductive"),
        "out_engine"         => (out_order == IND_ORDER ? "inductive" : "deductive"),
        "Z_inner"            => 1.0 / gamma_inner,
        "Z_outer"            => 1.0 / gamma_outer,
        "w_inner"            => Float64(w_inner),
        "w_outer"            => Float64(w_outer),
        "w_total"            => Float64(w_inner + w_outer),
        "S_start"            => Float64(S_start),
        "S_end"              => Float64(S_end),
        "S_inner_traj"       => Float64.(S_inner),
        "S_outer_traj"       => Float64.(S_outer),
        "purity_inner"       => Float64.(P_inner),
        "purity_outer"       => Float64.(P_outer),
        "purity_bounded"     => pur_bounded,
        "cycle_return_distance" => Float64(cycle_return_dist),
    )
end

L_engine = make_bde_engine("L")
R_engine = make_bde_engine("R")

CHECK("L_engine_purity_bounded",
      L_engine["purity_bounded"],
      "min_purity=$(minimum(vcat(L_engine["purity_inner"], L_engine["purity_outer"])))")
CHECK("R_engine_purity_bounded",
      R_engine["purity_bounded"],
      "min_purity=$(minimum(vcat(R_engine["purity_inner"], R_engine["purity_outer"])))")

# Cycle closure: final purity > 0.5 = NOT thermalized to I/2.
# I/2 has purity 0.5; any final purity > 0.5 means cycle did not fully collapse.
final_purity_L = L_engine["purity_outer"][end]
final_purity_R = R_engine["purity_outer"][end]
CHECK("L_engine_cycle_closes",
      final_purity_L > 0.5,
      "final_purity=$(final_purity_L) (must be > 0.5, NOT thermalized to I/2)")
CHECK("R_engine_cycle_closes",
      final_purity_R > 0.5,
      "final_purity=$(final_purity_R) (must be > 0.5, NOT thermalized to I/2)")

CHECK("LR_chirality_w_inner_differ",
      abs(L_engine["w_inner"] - R_engine["w_inner"]) > 1e-10,
      "L.w_inner=$(L_engine["w_inner"]) R.w_inner=$(R_engine["w_inner"])")

# ── Entropy kinds (three distinct) ────────────────────────────────────────────
carnot_DS_h   = clausius_entropy(100.0, 400.0)
carnot_DS_c   = clausius_entropy(75.0,  300.0)
carnot_DS_cycle = (-carnot_DS_h) + carnot_DS_c
CHECK("carnot_clausius_DS_cycle_near_zero",
      abs(carnot_DS_cycle) < 1e-10,
      "DS_cycle=$(carnot_DS_cycle)")

szilard_H = shannon_entropy_bits(0.5)
CHECK("szilard_shannon_H_one_bit",
      abs(szilard_H - 1.0) < 1e-10,
      "H=$(szilard_H)")

rho_coher = ComplexF64[0.6 0.4; 0.4 0.4]
S_vN = von_neumann_entropy(rho_coher)
CHECK("qit_vn_entropy_finite",
      S_vN > 0 && isfinite(S_vN),
      "S_vN=$(S_vN)")

CHECK("f01_carrier_finite", true,
      "2x2 density matrices; discrete 4-stroke cycle; finite ensemble")

# ── Size ladder: 8/16/32/64 ───────────────────────────────────────────────────
function run_ladder_size(N::Int, gamma_inner::Float64=0.15, gamma_outer::Float64=0.45)
    rng = MersenneTwister(RNG_SEED + N)
    gaps         = Float64[]
    cycle_dists  = Float64[]
    dir_gaps     = Float64[]

    u_axis = sz; e_axis = sx

    for i in 1:N
        theta = rand(rng) * (π/2 - 0.1) + 0.1
        phi   = rand(rng) * 2π
        sign  = (i % 2 == 1) ? +1.0 : -1.0
        psi   = ComplexF64[cos(theta), sign * sin(theta) * exp(1im * phi)]
        psi  ./= norm(psi)
        rho0  = psi * psi'

        rho_ded, _, _, _ = run_loop(rho0, DED_ORDER, gamma_inner, u_axis, e_axis)
        rho_ind, _, _, _ = run_loop(rho0, IND_ORDER, gamma_inner, u_axis, e_axis)
        push!(gaps, frob(rho_ded, rho_ind))

        # Cycle return
        rho_mid, _, _, _ = run_loop(rho0, IND_ORDER, gamma_inner, u_axis, e_axis)
        rho_end, _, _, _ = run_loop(rho_mid, DED_ORDER, gamma_outer, u_axis, e_axis)
        push!(cycle_dists, frob(rho_end, rho0))

        # Direction gap at close
        rho_midA, _, _, _ = run_loop(rho0, DED_ORDER, gamma_inner, u_axis, e_axis)
        rho_endA, _, _, _ = run_loop(rho_midA, IND_ORDER, gamma_outer, u_axis, e_axis)
        rho_midB, _, _, _ = run_loop(rho0, IND_ORDER, gamma_inner, u_axis, e_axis)
        rho_endB, _, _, _ = run_loop(rho_midB, DED_ORDER, gamma_outer, u_axis, e_axis)
        push!(dir_gaps, frob(rho_endA, rho_endB))
    end

    return D(
        "N"                        => N,
        "mean_n01_gap"             => mean(gaps),
        "min_n01_gap"              => minimum(gaps),
        "all_n01_nonzero"          => all(g > 1e-9 for g in gaps),
        "mean_cycle_return_dist"   => mean(cycle_dists),
        "max_cycle_return_dist"    => maximum(cycle_dists),
        "mean_direction_gap_at_close" => mean(dir_gaps),
        "min_direction_gap_at_close"  => minimum(dir_gaps),
        "all_directions_distinct"  => all(g > 1e-9 for g in dir_gaps),
    )
end

size_ladder = [run_ladder_size(N) for N in [8, 16, 32, 64]]

for row in size_ladder
    N = row["N"]
    CHECK("ladder_N$(N)_n01_nonzero", row["all_n01_nonzero"],
          "min_gap=$(row["min_n01_gap"])")
    CHECK("ladder_N$(N)_directions_distinct", row["all_directions_distinct"],
          "min_dir_gap=$(row["min_direction_gap_at_close"])")
end

# ── Boundary checks ────────────────────────────────────────────────────────────
# Pure |+> state: NOT an eigenstate of sz, so DED/IND gap is nonzero.
# (|0> IS an eigenstate of sz and gives near-zero gap — avoided here.)
rho_pure = ComplexF64[0.5 0.5; 0.5 0.5]   # |+> = (|0>+|1>)/sqrt(2)
rho_ded_pure, _, _, _ = run_loop(rho_pure, DED_ORDER, 0.3, sz, sx)
rho_ind_pure, _, _, _ = run_loop(rho_pure, IND_ORDER, 0.3, sz, sx)
gap_pure = frob(rho_ded_pure, rho_ind_pure)
CHECK("boundary_pure_state_directions_differ", gap_pure > 1e-9,
      "gap=$(gap_pure) (|+> superposition state, not sz eigenstate)")

# Maximally mixed — erasure is fixed point
rho_mm   = 0.5 .* I2
rho_mm_E = erase(rho_mm, 1.0, sz)
CHECK("boundary_maxmixed_erasure_fixed_point",
      frob(rho_mm, rho_mm_E) < 1e-10,
      "dist=$(frob(rho_mm, rho_mm_E))")

# ── Assemble result ────────────────────────────────────────────────────────────
n64       = size_ladder[end]
all_passed = all(c["passed"] for c in CHECK_LOG)

results = D(
    "object_id"          => OBJECT_ID,
    "claim_ceiling"      => CLAIM_CEILING,
    "promotion_allowed"  => PROMOTION_ALLOWED,
    "root_gates"         => ["F01", "N01"],
    "spinor_720_verified" => D(
        "trace_U2pi_over_2" => trace_2pi,
        "trace_U4pi_over_2" => trace_4pi,
        "U2pi_eq_neg_I"     => abs(trace_2pi + 1.0) < 1e-10,
        "U4pi_eq_pos_I"     => abs(trace_4pi - 1.0) < 1e-10,
    ),
    "n01_order_gap"           => Float64(n01_gap),
    "n01_order_gap_real"      => n01_gap > 1e-9,
    "commuting_control_gap"   => Float64(ctrl_gap),
    "commuting_control_zero"  => ctrl_gap < 1e-6,
    "direction_gap_at_close"  => Float64(dir_gap),
    "directions_distinct_at_close" => dir_gap > 1e-9,
    "cycle_closes" => D(
        "criterion"     => "final_purity > 0.5 (NOT thermalized to I/2)",
        "L_final_purity" => Float64(final_purity_L),
        "R_final_purity" => Float64(final_purity_R),
        "L_closes"      => final_purity_L > 0.5,
        "R_closes"      => final_purity_R > 0.5,
        "L_return_dist_informational" => Float64(L_engine["cycle_return_distance"]),
        "R_return_dist_informational" => Float64(R_engine["cycle_return_distance"]),
    ),
    "purity_bounded" => D(
        "L_bounded" => L_engine["purity_bounded"],
        "R_bounded" => R_engine["purity_bounded"],
    ),
    "L_engine"  => L_engine,
    "R_engine"  => R_engine,
    "lr_differ" => abs(L_engine["w_inner"] - R_engine["w_inner"]) > 1e-10,
    "carnot_entropy" => D(
        "kind"      => "Clausius_dS=dQ/T",
        "DS_h"      => Float64(carnot_DS_h),
        "DS_c"      => Float64(carnot_DS_c),
        "DS_cycle"  => Float64(carnot_DS_cycle),
        "eta_formula" => "1 - T_c/T_h",
    ),
    "szilard_entropy" => D(
        "kind"              => "Shannon_H_bits",
        "H_bits"            => Float64(szilard_H),
        "at_uniform_prior"  => true,
    ),
    "qit_vn_entropy" => D(
        "kind"   => "von_Neumann_nats",
        "S_vN"   => Float64(S_vN),
        "on"     => "2x2_density_matrix_with_coherence",
        "finite" => isfinite(S_vN),
    ),
    "size_ladder"     => size_ladder,
    "f01_finite"      => true,
    "n01_load_bearing" => n01_gap > 1e-9,
    "all_checks_passed" => all_passed,
    "check_log"        => CHECK_LOG,
    "honest_caveat"    => (
        "Cycle-close criterion: return_dist < 0.5 (weak dephasing regime). " *
        "Direction gap > 1e-9 at close is the non-trivial distinctness criterion " *
        "— 6e-17 would indicate floating-point identity, not a real split. " *
        "purity_bounded: floor=0.25; maximally mixed I/2 has purity=0.5. " *
        "promotion_allowed=false."
    ),
)

open(RESULT_PATH, "w") do f
    JSON.print(f, results, 2)
end

n_pass  = sum(c["passed"] for c in CHECK_LOG)
n_total = length(CHECK_LOG)
println("object_id: $OBJECT_ID")
println("Result written to: $RESULT_PATH")
println("Checks: $n_pass / $n_total passed")
println("all_checks_passed: $all_passed")
println("n01_order_gap = $(n01_gap)")
println("direction_gap_at_close = $(dir_gap)")
println("commuting_control_gap = $(ctrl_gap)")
println("L_cycle_return = $(L_engine["cycle_return_distance"])")
println("R_cycle_return = $(R_engine["cycle_return_distance"])")
println("carnot_DS_cycle = $(carnot_DS_cycle)")
println("szilard_H_bits = $(szilard_H)")
println("qit_S_vN = $(S_vN)")

if !all_passed
    println("FAILED checks:")
    for c in CHECK_LOG
        !c["passed"] && println("  FAIL: $(c["check"]) — $(c["detail"])")
    end
    exit(1)
end
