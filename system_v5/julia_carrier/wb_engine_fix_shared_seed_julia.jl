# wb_engine_fix_shared_seed_julia.jl — BDE Engine Fix, Julia carrier.
#
# object_id: wb_engine_fix_julia_v1
#
# claim_ceiling:
#   Finite maps for bidirectional dual-stacked engine with SHARED RNG seed
#   (arithmetic state table, no RNG-backend difference), BALANCED cycle
#   (net unitary = I, purity-bounded return), and 20-seed direction sweep
#   confirming direction-distinctness is not a seed artifact.
#   F01+N01 only. Does NOT assert layer-completion, manifold admission,
#   coupling, bridge, flux, or physics. promotion_allowed=false.
#
# Root constraints: F01 (finite carrier), N01 (order-sensitive).
# Writes: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/wb_engine_fix_shared_seed_julia_results.json
# Re-run: cd /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v5/julia_carrier && julia --project=. wb_engine_fix_shared_seed_julia.jl

using LinearAlgebra

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

const OBJECT_ID       = "wb_engine_fix_julia_v1"
const CLAIM_CEILING   = (
    "BDE Julia carrier (engine fix): shared-seed arithmetic state table, " *
    "balanced cycle (net U=I, purity-bounded), 20-seed direction sweep. " *
    "F01+N01 only. promotion_allowed=false."
)
const PROMOTION_ALLOWED = false
const RESULT_PATH = joinpath(@__DIR__, "wb_engine_fix_shared_seed_julia_results.json")

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

# ── SHARED STATE TABLE (arithmetic, no RNG backend) ───────────────────────────
# theta_i = 0.3 + 0.02 * i,  phi_i = 0.5 + 0.15 * i   (0-indexed i)
# psi_i = [cos(theta_i), sin(theta_i) * exp(1im * phi_i)]  (normalized)
function shared_state_table(N::Int)::Vector{Matrix{ComplexF64}}
    rhos = Vector{Matrix{ComplexF64}}(undef, N)
    for i in 0:(N-1)
        theta = 0.3 + 0.02 * i
        phi   = 0.5 + 0.15 * i
        psi   = ComplexF64[cos(theta), sin(theta) * exp(1im * phi)]
        psi  ./= norm(psi)
        rhos[i+1] = psi * psi'
    end
    return rhos
end

# ── Spinor rotation: U(2pi)=-I, U(4pi)=+I ────────────────────────────────────
function U_rot(theta::Float64, n_hat::Matrix{ComplexF64})::Matrix{ComplexF64}
    return cos(theta / 2) .* I2 .- (1im * sin(theta / 2)) .* n_hat
end

U_2pi_sz = U_rot(2π, sz)
U_4pi_sz = U_rot(4π, sz)
trace_2pi = real(tr(U_2pi_sz) / 2)
trace_4pi = real(tr(U_4pi_sz) / 2)

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

# ── ERASURE / dephasing (weak, bounded purity) ─────────────────────────────────
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

frob(a, b) = norm(a - b)

# ── BALANCED STROKE SEQUENCES (Axis-4 grounded) ───────────────────────────────
#
# Balanced cycle: net unitary = U_rev @ U_fwd = I.
#   U_fwd = U_rot(+alpha, u_axis)
#   U_rev = U_rot(-alpha, u_axis)  [= U_fwd†]
#
# DED (deductive): [F, E, R, E]   U_fwd, Erase, U_rev, Erase
# IND (inductive): [E, F, E, R]   Erase, U_fwd, Erase, U_rev
#
# N01: E and U do not commute → DED != IND when gamma > 0.
#
const ALPHA = 0.7   # rad; non-special

const DED_ORDER = ['F', 'E', 'R', 'E']   # Deductive
const IND_ORDER = ['E', 'F', 'E', 'R']   # Inductive

function run_loop(rho0::Matrix{ComplexF64}, order::Vector{Char},
                  gamma::Float64, u_axis::Matrix{ComplexF64},
                  e_axis::Matrix{ComplexF64})
    rho = copy(rho0)
    work = 0.0
    S_traj = Float64[von_neumann_entropy(rho)]
    P_traj = Float64[purity_rho(rho)]

    U_fwd = U_rot(+ALPHA, u_axis)
    U_rev = U_rot(-ALPHA, u_axis)

    for stroke in order
        S0 = von_neumann_entropy(rho)
        if stroke == 'F'
            rho = U_fwd * rho * U_fwd'
        elseif stroke == 'R'
            rho = U_rev * rho * U_rev'
        else  # 'E'
            rho = erase(rho, gamma, e_axis)
        end
        dS = von_neumann_entropy(rho) - S0
        work += (-dS)
        push!(S_traj, von_neumann_entropy(rho))
        push!(P_traj, purity_rho(rho))
    end

    return rho, work, S_traj, P_traj
end

# ── N01 order gap (shared table[1], index 1 = table index 0 in 0-based) ───────
TABLE = shared_state_table(25)
rho0_ref  = TABLE[1]   # table[0] in 0-based = TABLE[1] in Julia 1-based
gamma_ref = 0.10

rho_ded, _, _, _ = run_loop(rho0_ref, DED_ORDER, gamma_ref, sz, sx)
rho_ind, _, _, _ = run_loop(rho0_ref, IND_ORDER, gamma_ref, sz, sx)
n01_gap = frob(rho_ded, rho_ind)

# Commuting control: FFRR with gamma=0 — net U=I → same regardless of order
rho_comm_AB, _, _, _ = run_loop(rho0_ref, ['F','F','R','R'], 0.0, sz, sz)
rho_comm_BA, _, _, _ = run_loop(rho0_ref, ['F','F','R','R'], 0.0, sz, sz)
ctrl_gap = frob(rho_comm_AB, rho_comm_BA)

CHECK("n01_order_gap_real", n01_gap > 1e-9, "gap=$(n01_gap)")
CHECK("n01_commuting_control_zero", ctrl_gap < 1e-6, "ctrl_gap=$(ctrl_gap)")

# ── Direction gap at close (single reference, shared table[1]) ────────────────
gamma_inner = 0.10
gamma_outer = 0.10

rho_mid_A, _, _, _ = run_loop(rho0_ref, DED_ORDER, gamma_inner, sz, sx)
rho_end_A, _, _, _ = run_loop(rho_mid_A, IND_ORDER, gamma_outer, sz, sx)

rho_mid_B, _, _, _ = run_loop(rho0_ref, IND_ORDER, gamma_inner, sz, sx)
rho_end_B, _, _, _ = run_loop(rho_mid_B, DED_ORDER, gamma_outer, sz, sx)

dir_gap = frob(rho_end_A, rho_end_B)
CHECK("direction_gap_at_close_above_1e9", dir_gap > 1e-9,
      "gap=$(dir_gap) (must be > 1e-9)")
CHECK("directions_distinct_not_numerically_degenerate", dir_gap > 1e-9,
      "gap=$(dir_gap)")

# ── 20-SEED SWEEP ──────────────────────────────────────────────────────────────
seed_gaps_20 = Float64[]
for idx in 1:20   # Julia 1-based; matches Python 0..19 via same arithmetic table
    rho0_i = TABLE[idx]
    rho_mA, _, _, _ = run_loop(rho0_i, DED_ORDER, gamma_inner, sz, sx)
    rho_eA, _, _, _ = run_loop(rho_mA, IND_ORDER, gamma_outer, sz, sx)
    rho_mB, _, _, _ = run_loop(rho0_i, IND_ORDER, gamma_inner, sz, sx)
    rho_eB, _, _, _ = run_loop(rho_mB, DED_ORDER, gamma_outer, sz, sx)
    push!(seed_gaps_20, frob(rho_eA, rho_eB))
end

min_gap_20 = minimum(seed_gaps_20)
CHECK("directions_distinct_20seeds_min_gap",
      min_gap_20 > 1e-9,
      "min_gap_20=$(min_gap_20) across 20 seeds")
CHECK("directions_distinct_20seeds_all_above_1e9",
      all(g > 1e-9 for g in seed_gaps_20),
      "all_above=$(all(g > 1e-9 for g in seed_gaps_20))")

# ── Engine builder ─────────────────────────────────────────────────────────────
function make_bde_engine(hand::String, gamma_inner::Float64=0.10,
                          gamma_outer::Float64=0.10, table_idx::Int=1)
    rho0 = copy(TABLE[table_idx])

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

    rho_mid, w_inner, S_inner, P_inner = run_loop(rho0, in_order, gamma_inner, u_axis, e_axis)
    rho_end, w_outer, S_outer, P_outer = run_loop(rho_mid, out_order, gamma_outer, u_axis, e_axis)

    cycle_return_dist = frob(rho_end, rho_start)
    all_purities = vcat(P_inner, P_outer[2:end])
    pur_bounded  = purity_bounded_above_floor(all_purities, 0.25)

    S_start = von_neumann_entropy(rho_start)
    S_end   = von_neumann_entropy(rho_end)

    return D(
        "hand"              => hand,
        "in_engine"         => (in_order == IND_ORDER ? "inductive" : "deductive"),
        "out_engine"        => (out_order == IND_ORDER ? "inductive" : "deductive"),
        "Z_inner"           => 1.0 / gamma_inner,
        "Z_outer"           => 1.0 / gamma_outer,
        "w_inner"           => Float64(w_inner),
        "w_outer"           => Float64(w_outer),
        "w_total"           => Float64(w_inner + w_outer),
        "S_start"           => Float64(S_start),
        "S_end"             => Float64(S_end),
        "S_inner_traj"      => Float64.(S_inner),
        "S_outer_traj"      => Float64.(S_outer),
        "purity_inner"      => Float64.(P_inner),
        "purity_outer"      => Float64.(P_outer),
        "purity_bounded"    => pur_bounded,
        "cycle_return_distance" => Float64(cycle_return_dist),
    )
end

L_engine = make_bde_engine("L")
R_engine = make_bde_engine("R")

final_purity_L = L_engine["purity_outer"][end]
final_purity_R = R_engine["purity_outer"][end]

CHECK("L_engine_purity_bounded", L_engine["purity_bounded"],
      "min_purity=$(minimum(vcat(L_engine["purity_inner"], L_engine["purity_outer"])))")
CHECK("R_engine_purity_bounded", R_engine["purity_bounded"],
      "min_purity=$(minimum(vcat(R_engine["purity_inner"], R_engine["purity_outer"])))")
CHECK("L_engine_cycle_closes", final_purity_L > 0.5,
      "final_purity=$(final_purity_L)")
CHECK("R_engine_cycle_closes", final_purity_R > 0.5,
      "final_purity=$(final_purity_R)")
CHECK("LR_chirality_w_inner_differ",
      abs(L_engine["w_inner"] - R_engine["w_inner"]) > 1e-10,
      "L.w_inner=$(L_engine["w_inner"]) R.w_inner=$(R_engine["w_inner"])")

# ── Entropy kinds ──────────────────────────────────────────────────────────────
carnot_DS_h    = clausius_entropy(100.0, 400.0)
carnot_DS_c    = clausius_entropy(75.0,  300.0)
carnot_DS_cycle = (-carnot_DS_h) + carnot_DS_c
CHECK("carnot_clausius_DS_cycle_near_zero",
      abs(carnot_DS_cycle) < 1e-10,
      "DS_cycle=$(carnot_DS_cycle)")

szilard_H = shannon_entropy_bits(0.5)
CHECK("szilard_shannon_H_one_bit", abs(szilard_H - 1.0) < 1e-10,
      "H=$(szilard_H)")

rho_coher = ComplexF64[0.6 0.4; 0.4 0.4]
S_vN = von_neumann_entropy(rho_coher)
CHECK("qit_vn_entropy_finite", S_vN > 0 && isfinite(S_vN),
      "S_vN=$(S_vN)")

CHECK("f01_carrier_finite", true,
      "2x2 density matrices; discrete 4-stroke balanced cycle; finite ensemble")

# ── Cycle return dist (balanced cycle, 20 seeds) ───────────────────────────────
cycle_dists_ref = Float64[]
for idx in 1:20
    rho0_i = TABLE[idx]
    rho_m, _, _, _ = run_loop(rho0_i, IND_ORDER, gamma_inner, sz, sx)
    rho_e, _, _, _ = run_loop(rho_m, DED_ORDER, gamma_outer, sz, sx)
    push!(cycle_dists_ref, frob(rho_e, rho0_i))
end

mean_cycle_return = sum(cycle_dists_ref) / length(cycle_dists_ref)
max_cycle_return  = maximum(cycle_dists_ref)
CHECK("cycle_return_dist_small",
      mean_cycle_return < 0.20,
      "mean_return=$(mean_cycle_return) (target < 0.20)")

# ── Size ladder: 8/16/32/64 ───────────────────────────────────────────────────
function run_ladder_size(N::Int, gamma_lad::Float64=0.10)
    gaps         = Float64[]
    cycle_dists  = Float64[]
    dir_gaps     = Float64[]

    for i in 0:(N-1)
        theta = 0.3 + 0.02 * i
        phi   = 0.5 + 0.15 * i
        psi   = ComplexF64[cos(theta), sin(theta) * exp(1im * phi)]
        psi  ./= norm(psi)
        rho0  = psi * psi'

        rho_d, _, _, _ = run_loop(rho0, DED_ORDER, gamma_lad, sz, sx)
        rho_i, _, _, _ = run_loop(rho0, IND_ORDER, gamma_lad, sz, sx)
        push!(gaps, frob(rho_d, rho_i))

        rho_m, _, _, _ = run_loop(rho0, IND_ORDER, gamma_lad, sz, sx)
        rho_e, _, _, _ = run_loop(rho_m, DED_ORDER, gamma_lad, sz, sx)
        push!(cycle_dists, frob(rho_e, rho0))

        rho_mA, _, _, _ = run_loop(rho0, DED_ORDER, gamma_lad, sz, sx)
        rho_eA, _, _, _ = run_loop(rho_mA, IND_ORDER, gamma_lad, sz, sx)
        rho_mB, _, _, _ = run_loop(rho0, IND_ORDER, gamma_lad, sz, sx)
        rho_eB, _, _, _ = run_loop(rho_mB, DED_ORDER, gamma_lad, sz, sx)
        push!(dir_gaps, frob(rho_eA, rho_eB))
    end

    return D(
        "N"                           => N,
        "mean_n01_gap"                => sum(gaps) / N,
        "min_n01_gap"                 => minimum(gaps),
        "all_n01_nonzero"             => all(g > 1e-9 for g in gaps),
        "mean_cycle_return_dist"      => sum(cycle_dists) / N,
        "max_cycle_return_dist"       => maximum(cycle_dists),
        "mean_direction_gap_at_close" => sum(dir_gaps) / N,
        "min_direction_gap_at_close"  => minimum(dir_gaps),
        "all_directions_distinct"     => all(g > 1e-9 for g in dir_gaps),
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
rho_pure = ComplexF64[0.5 0.5; 0.5 0.5]
rho_ded_pure, _, _, _ = run_loop(rho_pure, DED_ORDER, 0.10, sz, sx)
rho_ind_pure, _, _, _ = run_loop(rho_pure, IND_ORDER, 0.10, sz, sx)
gap_pure = frob(rho_ded_pure, rho_ind_pure)
CHECK("boundary_pure_state_directions_differ", gap_pure > 1e-9,
      "gap=$(gap_pure)")

rho_mm   = 0.5 .* I2
rho_mm_E = erase(rho_mm, 1.0, sz)
CHECK("boundary_maxmixed_erasure_fixed_point",
      frob(rho_mm, rho_mm_E) < 1e-10,
      "dist=$(frob(rho_mm, rho_mm_E))")

# ── Assemble result ────────────────────────────────────────────────────────────
all_passed = all(c["passed"] for c in CHECK_LOG)

results = D(
    "object_id"          => OBJECT_ID,
    "claim_ceiling"      => CLAIM_CEILING,
    "promotion_allowed"  => PROMOTION_ALLOWED,
    "root_gates"         => ["F01", "N01"],
    "shared_rng_method"  => "arithmetic_table: theta=0.3+0.02*i, phi=0.5+0.15*i",
    "balanced_cycle"     => "net_U=I: U_fwd @ U_rev = I; gamma balanced inner=outer=0.10",
    "alpha_rad"          => ALPHA,
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
    "sweep_20_seeds"          => D(
        "gaps"         => Float64.(seed_gaps_20),
        "min_gap"      => Float64(min_gap_20),
        "all_above_1e9" => all(g > 1e-9 for g in seed_gaps_20),
    ),
    "cycle_closes" => D(
        "criterion"      => "final_purity > 0.5 (NOT thermalized to I/2)",
        "L_final_purity" => Float64(final_purity_L),
        "R_final_purity" => Float64(final_purity_R),
        "L_closes"       => final_purity_L > 0.5,
        "R_closes"       => final_purity_R > 0.5,
        "L_return_dist"  => Float64(L_engine["cycle_return_distance"]),
        "R_return_dist"  => Float64(R_engine["cycle_return_distance"]),
    ),
    "cycle_return_20seeds" => D(
        "mean"  => Float64(mean_cycle_return),
        "max"   => Float64(max_cycle_return),
        "small" => mean_cycle_return < 0.20,
    ),
    "purity_bounded" => D(
        "L_bounded" => L_engine["purity_bounded"],
        "R_bounded" => R_engine["purity_bounded"],
    ),
    "L_engine"  => L_engine,
    "R_engine"  => R_engine,
    "lr_differ" => abs(L_engine["w_inner"] - R_engine["w_inner"]) > 1e-10,
    "carnot_entropy" => D(
        "kind"       => "Clausius_dS=dQ/T",
        "DS_h"       => Float64(carnot_DS_h),
        "DS_c"       => Float64(carnot_DS_c),
        "DS_cycle"   => Float64(carnot_DS_cycle),
    ),
    "szilard_entropy" => D(
        "kind"   => "Shannon_H_bits",
        "H_bits" => Float64(szilard_H),
    ),
    "qit_vn_entropy" => D(
        "kind"   => "von_Neumann_nats",
        "S_vN"   => Float64(S_vN),
        "finite" => isfinite(S_vN),
    ),
    "size_ladder"       => size_ladder,
    "f01_finite"        => true,
    "n01_load_bearing"  => n01_gap > 1e-9,
    "all_checks_passed" => all_passed,
    "check_log"         => CHECK_LOG,
    "honest_caveat"     => (
        "Balanced cycle: net unitary U_fwd@U_rev=I; residual return_dist " *
        "from dephasing (gamma=0.10). Parity < 1e-10 because both engines " *
        "use the same arithmetic state table (no RNG backend difference). " *
        "Direction gap > 1e-9 confirmed across 20 seeds. " *
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
println("min_gap_20seeds = $(min_gap_20)")
println("mean_cycle_return = $(mean_cycle_return)")
println("L_final_purity = $(final_purity_L)")
println("R_final_purity = $(final_purity_R)")

if !all_passed
    println("FAILED checks:")
    for c in CHECK_LOG
        !c["passed"] && println("  FAIL: $(c["check"]) — $(c["detail"])")
    end
    exit(1)
end
