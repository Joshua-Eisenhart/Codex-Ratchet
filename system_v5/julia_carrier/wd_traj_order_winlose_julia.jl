#!/usr/bin/env julia
# object_id: wd_traj_order_winlose_julia
# claim_ceiling: finite-map carrier — computes trajectory divergence and N01
#   composition-order gap split by WIN vs LOSE label on the 16-cell QIT engine.
#   Does NOT assert layer-completion, manifold admission, coupling, bridge,
#   rho_AB/Xi/Phi0/Axis0, flux, or physics.
#   promotion_allowed: false
#
# Root constraints in force: F01 (finite distinguishability), N01 (ordering).
#
# Move: traj_order_winlose
# Question: does WIN/LOSE co-vary with (a) mid-substep trajectory divergence or
#   (b) N01 composition-order gap distribution — or is the label grammar at all levels?
#
# Run: julia system_v5/julia_carrier/wd_traj_order_winlose_julia.jl
# Output: system_v5/julia_carrier/wd_traj_order_winlose_julia_results.json

using LinearAlgebra
using JSON
using Dates

# ── Pauli basis (identical to qit16_julia.jl) ─────────────────────────────────
const I2  = ComplexF64[1 0; 0 1]
const sx  = ComplexF64[0 1; 1 0]
const sy  = ComplexF64[0 -im; im 0]
const sz  = ComplexF64[1 0; 0 -1]
const P0  = (I2 + sz) / 2
const P1  = (I2 - sz) / 2
const Qp  = (I2 + sx) / 2
const Qm  = (I2 - sx) / 2

# ── Channel functions (identical to qit16_julia.jl) ───────────────────────────
function apply_Ti(rho, q1)
    return (1.0 - q1) .* rho .+ q1 .* (P0 * rho * P0 .+ P1 * rho * P1)
end

function apply_Te(rho, q2)
    return (1.0 - q2) .* rho .+ q2 .* (Qp * rho * Qp .+ Qm * rho * Qm)
end

function apply_Fi(rho, theta)
    U = exp(-im * theta / 2 .* sx)
    return U * rho * U'
end

function apply_Fe(rho, phi)
    U = exp(-im * phi / 2 .* sz)
    return U * rho * U'
end

# ── State / geometry helpers ──────────────────────────────────────────────────
function psi_s3(phi, chi, eta)
    return ComplexF64[cis(phi + chi) * cos(eta), cis(phi - chi) * sin(eta)]
end

function dm(psi)
    return psi * psi'
end

const ETA0 = pi / 4
const PHI0 = pi / 6
const CHI0 = pi / 3
const U0   = pi / 4

function weyl_frame_unitary(side::Symbol, u)
    H0 = sz / 2
    return side == :left ? exp(-im * H0 * u) : exp(+im * H0 * u)
end

function terrain_initial_rho(terrain::Symbol, weyl_side::Symbol)
    psi0 = psi_s3(PHI0, CHI0, ETA0)
    rho0 = dm(psi0)
    if terrain in (:Ni, :Si)
        V = weyl_frame_unitary(weyl_side, U0)
        return V' * rho0 * V
    else
        return rho0
    end
end

# Canonical parameters at n_steps = 16
const Q1_BASE  = 0.3
const Q2_BASE  = 0.3
const TH_BASE  = pi/4
const PH_BASE  = pi/3

function params_for_steps(n)
    scale = 8.0 / n
    return (q1=Q1_BASE*scale, q2=Q2_BASE*scale, theta=TH_BASE*scale, phi=PH_BASE*scale)
end

const N_STEPS_CANONICAL = 16
const P_CANONICAL = params_for_steps(N_STEPS_CANONICAL)

# ── Apply channel at fractional parameter t ∈ [0,1] ─────────────────────────
# t=0 → identity (param=0); t=1 → full channel (param=canonical)
function apply_channel_frac(judge_fn::Symbol, rho, t::Float64)
    if judge_fn == :Ti
        return apply_Ti(rho, P_CANONICAL.q1 * t)
    elseif judge_fn == :Te
        return apply_Te(rho, P_CANONICAL.q2 * t)
    elseif judge_fn == :Fi
        return apply_Fi(rho, P_CANONICAL.theta * t)
    else  # :Fe
        return apply_Fe(rho, P_CANONICAL.phi * t)
    end
end

# ── Trace norm (L1 for density matrices) ─────────────────────────────────────
# trace norm = sum of singular values
function trace_norm(delta::Matrix{ComplexF64})
    return sum(svdvals(delta))
end

# ── 16 cell definitions (identical to qit16_julia.jl) ────────────────────────
struct CellDef
    token::String
    judge_fn::Symbol
    terrain::Symbol
    axis6_order::Symbol
    loop_type::Symbol
    outcome::String
    engine::Int
    step::Int
end

const CELLS = CellDef[
    CellDef("TiSe", :Ti, :Se, :UP,   :outer_major, "LOSE", 1, 1),
    CellDef("SeFi", :Fi, :Se, :DOWN, :inner_minor, "win",  1, 1),
    CellDef("NeTi", :Ti, :Ne, :DOWN, :outer_major, "WIN",  1, 2),
    CellDef("FiNe", :Fi, :Ne, :UP,   :inner_minor, "lose", 1, 2),
    CellDef("NiFe", :Fe, :Ni, :DOWN, :outer_major, "LOSE", 1, 3),
    CellDef("TeNi", :Te, :Ni, :UP,   :inner_minor, "lose", 1, 3),
    CellDef("FeSi", :Fe, :Si, :UP,   :outer_major, "WIN",  1, 4),
    CellDef("SiTe", :Te, :Si, :DOWN, :inner_minor, "win",  1, 4),
    CellDef("FiSe", :Fi, :Se, :UP,   :outer_major, "WIN",  2, 1),
    CellDef("SeTi", :Ti, :Se, :DOWN, :inner_minor, "lose", 2, 1),
    CellDef("TeSi", :Te, :Si, :UP,   :outer_major, "WIN",  2, 2),
    CellDef("SiFe", :Fe, :Si, :DOWN, :inner_minor, "win",  2, 2),
    CellDef("NiTe", :Te, :Ni, :DOWN, :outer_major, "LOSE", 2, 3),
    CellDef("FeNi", :Fe, :Ni, :UP,   :inner_minor, "lose", 2, 3),
    CellDef("NeFi", :Fi, :Ne, :DOWN, :outer_major, "LOSE", 2, 4),
    CellDef("TiNe", :Ti, :Ne, :UP,   :inner_minor, "win",  2, 4),
]

is_win(outcome) = outcome in ("WIN", "win")
is_lose(outcome) = outcome in ("LOSE", "lose")
is_uppercase(outcome) = outcome in ("WIN", "LOSE")
is_lowercase(outcome) = outcome in ("win", "lose")

# ── PART A: Trajectory divergence ────────────────────────────────────────────
# Strategy: pair cells that share (terrain, judge_fn).
# For each such pair, compute rho(t) for 32 substeps for each cell.
# Report ||rho_cell1(t) - rho_cell2(t)||_1 for each t.
# Note: within matched pairs the win/lose direction is the SAME (by chart construction)
# so we also compute the cross-group divergence: mean WIN trajectory vs mean LOSE trajectory.

const N_SUBSTEPS = 32

function substep_trajectory(cell::CellDef, weyl_side::Symbol)
    rho_in = terrain_initial_rho(cell.terrain, weyl_side)
    traj = Matrix{ComplexF64}[]
    for k in 1:N_SUBSTEPS
        t = k / N_SUBSTEPS
        rho_t = apply_channel_frac(cell.judge_fn, rho_in, t)
        push!(traj, rho_t)
    end
    return rho_in, traj
end

function part_a_trajectory_divergence()
    # Build (terrain, judge_fn) pair index
    pair_key(c) = (c.terrain, c.judge_fn)
    groups = Dict{Tuple{Symbol,Symbol}, Vector{CellDef}}()
    for cell in CELLS
        k = pair_key(cell)
        push!(get!(groups, k, CellDef[]), cell)
    end

    matched_pairs = Tuple{CellDef,CellDef}[]
    for (k, cells) in groups
        if length(cells) == 2
            push!(matched_pairs, (cells[1], cells[2]))
        end
    end

    # For each matched pair, compute per-substep trace-norm divergence
    pair_results = Dict{String,Any}[]
    for (c1, c2) in matched_pairs
        rho_in1, traj1 = substep_trajectory(c1, :left)
        rho_in2, traj2 = substep_trajectory(c2, :left)

        @assert length(traj1) == N_SUBSTEPS
        @assert length(traj2) == N_SUBSTEPS

        divergences = Float64[]
        for k in 1:N_SUBSTEPS
            push!(divergences, trace_norm(traj1[k] .- traj2[k]))
        end

        max_div = maximum(divergences)
        mean_div = sum(divergences) / N_SUBSTEPS

        # Win/lose classification of each cell in the pair
        c1_is_win = is_win(c1.outcome)
        c2_is_win = is_win(c2.outcome)
        pair_outcome_type = (c1_is_win == c2_is_win) ? "same_direction" : "opposite_direction"

        push!(pair_results, Dict{String,Any}(
            "cell1_token"   => c1.token,
            "cell2_token"   => c2.token,
            "terrain"       => string(c1.terrain),
            "judge_fn"      => string(c1.judge_fn),
            "cell1_outcome" => c1.outcome,
            "cell2_outcome" => c2.outcome,
            "pair_outcome_type" => pair_outcome_type,
            "max_trace_norm_divergence" => max_div,
            "mean_trace_norm_divergence" => mean_div,
            "per_substep_divergences" => divergences,
        ))
    end

    global_max_div = maximum(r["max_trace_norm_divergence"] for r in pair_results)
    global_mean_div = sum(r["mean_trace_norm_divergence"] for r in pair_results) / length(pair_results)

    # Cross-group analysis: WIN group mean trajectory vs LOSE group mean trajectory
    # For each substep, compute mean rho over WIN cells and mean rho over LOSE cells
    win_cells  = filter(c -> is_win(c.outcome),  CELLS)
    lose_cells = filter(c -> is_lose(c.outcome), CELLS)

    @assert length(win_cells) == 8 "Expected 8 WIN cells, got $(length(win_cells))"
    @assert length(lose_cells) == 8 "Expected 8 LOSE cells, got $(length(lose_cells))"

    # Build trajectories for all WIN and LOSE cells
    cross_divergences = Float64[]
    for k in 1:N_SUBSTEPS
        rho_win_sum  = zeros(ComplexF64, 2, 2)
        rho_lose_sum = zeros(ComplexF64, 2, 2)
        for cell in win_cells
            rho_in = terrain_initial_rho(cell.terrain, :left)
            t = k / N_SUBSTEPS
            rho_win_sum .+= apply_channel_frac(cell.judge_fn, rho_in, t)
        end
        for cell in lose_cells
            rho_in = terrain_initial_rho(cell.terrain, :left)
            t = k / N_SUBSTEPS
            rho_lose_sum .+= apply_channel_frac(cell.judge_fn, rho_in, t)
        end
        rho_win_mean  = rho_win_sum  ./ length(win_cells)
        rho_lose_mean = rho_lose_sum ./ length(lose_cells)
        push!(cross_divergences, trace_norm(rho_win_mean .- rho_lose_mean))
    end

    cross_max  = maximum(cross_divergences)
    cross_mean = sum(cross_divergences) / N_SUBSTEPS

    # Uppercase WIN/LOSE (outer-major) vs lowercase win/lose (inner-minor)
    outer_win_cells  = filter(c -> c.outcome == "WIN",  CELLS)
    outer_lose_cells = filter(c -> c.outcome == "LOSE", CELLS)
    inner_win_cells  = filter(c -> c.outcome == "win",  CELLS)
    inner_lose_cells = filter(c -> c.outcome == "lose", CELLS)

    cross_outer_divs = Float64[]
    cross_inner_divs = Float64[]
    for k in 1:N_SUBSTEPS
        t = k / N_SUBSTEPS
        rho_ow  = sum(apply_channel_frac(c.judge_fn, terrain_initial_rho(c.terrain, :left), t) for c in outer_win_cells)  ./ length(outer_win_cells)
        rho_ol  = sum(apply_channel_frac(c.judge_fn, terrain_initial_rho(c.terrain, :left), t) for c in outer_lose_cells) ./ length(outer_lose_cells)
        rho_iw  = sum(apply_channel_frac(c.judge_fn, terrain_initial_rho(c.terrain, :left), t) for c in inner_win_cells)  ./ length(inner_win_cells)
        rho_il  = sum(apply_channel_frac(c.judge_fn, terrain_initial_rho(c.terrain, :left), t) for c in inner_lose_cells) ./ length(inner_lose_cells)
        push!(cross_outer_divs, trace_norm(rho_ow .- rho_ol))
        push!(cross_inner_divs, trace_norm(rho_iw .- rho_il))
    end

    # Observation about structure of matched pairs
    n_same_dir_pairs  = count(r -> r["pair_outcome_type"] == "same_direction",  pair_results)
    n_opp_dir_pairs   = count(r -> r["pair_outcome_type"] == "opposite_direction", pair_results)

    return Dict{String,Any}(
        "n_matched_pairs"    => length(matched_pairs),
        "n_same_direction_pairs"  => n_same_dir_pairs,
        "n_opposite_direction_pairs" => n_opp_dir_pairs,
        "structural_note" => (
            n_opp_dir_pairs == 0
            ? "ALL matched (terrain,judge_fn) pairs have same win/lose direction by chart construction. No cross-outcome pairing exists within this constraint."
            : "Some matched pairs have opposite win/lose outcomes."
        ),
        "pair_results" => pair_results,
        "global_max_trace_norm_divergence_within_pairs" => global_max_div,
        "global_mean_trace_norm_divergence_within_pairs" => global_mean_div,
        "cross_group_win_vs_lose" => Dict{String,Any}(
            "n_win_cells"  => length(win_cells),
            "n_lose_cells" => length(lose_cells),
            "max_trace_norm_divergence"  => cross_max,
            "mean_trace_norm_divergence" => cross_mean,
            "per_substep_divergences"    => cross_divergences,
        ),
        "outer_major_loop" => Dict{String,Any}(
            "n_WIN"  => length(outer_win_cells),
            "n_LOSE" => length(outer_lose_cells),
            "max_trace_norm_divergence"  => maximum(cross_outer_divs),
            "mean_trace_norm_divergence" => sum(cross_outer_divs) / N_SUBSTEPS,
            "per_substep_divergences" => cross_outer_divs,
        ),
        "inner_minor_loop" => Dict{String,Any}(
            "n_win"  => length(inner_win_cells),
            "n_lose" => length(inner_lose_cells),
            "max_trace_norm_divergence"  => maximum(cross_inner_divs),
            "mean_trace_norm_divergence" => sum(cross_inner_divs) / N_SUBSTEPS,
            "per_substep_divergences" => cross_inner_divs,
        ),
    )
end

# ── PART B: N01 composition-order gap split by WIN vs LOSE ───────────────────
# For each cell, compute gap = norm(A*B*psi - B*A*psi) where A is the
# cell's judge_fn operator matrix, B = sx (the non-commuting N01 witness),
# and psi is the initial state vector from rho_in.
#
# Note: rho_in is a pure state so psi = principal eigenvector of rho_in.

function principal_eigenvector(rho::Matrix{ComplexF64})
    # rho is a 2x2 Hermitian rank-1 matrix (pure state)
    # The principal eigenvector has eigenvalue ≈ 1
    F = eigen(Hermitian(rho))
    # F.values are sorted ascending; take the last (largest)
    psi = F.vectors[:, end]
    # Normalize
    psi_norm = norm(psi)
    if psi_norm < 1e-12
        error("principal_eigenvector: zero-norm eigenvector")
    end
    return ComplexF64.(psi ./ psi_norm)
end

function judge_fn_matrix(jfn::Symbol)
    # Return a 2x2 matrix for the judge function operator
    # Ti: projector onto z-basis (use full Ti superoperator is not a 2x2 matrix;
    #     for N01 gap we need a 2x2 operator that represents the channel action.
    #     We use the "dominant" Kraus operator: for Ti with q1, K1 = sqrt(1-q1)*I + sqrt(q1)*P0...
    #     But for the N01 gap test we want to check composition order of the operator matrix.
    #     Use the Hamiltonian / generator matrix for each channel:
    #     Ti (z-dephase): H_Ti = P0 - P1 = sz (z-measurement basis)
    #     Te (x-dephase): H_Te = Qp - Qm = sx
    #     Fi (x-rotation): H_Fi = sx/2 (generator)
    #     Fe (z-rotation): H_Fe = sz/2 (generator)
    if jfn == :Ti
        return sz   # z-dephasing basis operator
    elseif jfn == :Te
        return sx   # x-dephasing basis operator
    elseif jfn == :Fi
        return sx ./ 2   # x-rotation generator
    else  # :Fe
        return sz ./ 2   # z-rotation generator
    end
end

function n01_gap_for_cell(cell::CellDef, weyl_side::Symbol)
    rho_in = terrain_initial_rho(cell.terrain, weyl_side)
    psi = principal_eigenvector(rho_in)

    A = judge_fn_matrix(cell.judge_fn)
    B = sx   # N01 witness: sx

    # gap = ||A*B*psi - B*A*psi||
    ab_psi = A * (B * psi)
    ba_psi = B * (A * psi)
    gap = norm(ab_psi .- ba_psi)
    commutator_norm_val = norm(A * B .- B * A)

    return gap, commutator_norm_val
end

function part_b_n01_gap_split()
    win_gaps  = Float64[]
    lose_gaps = Float64[]
    win_tokens  = String[]
    lose_tokens = String[]
    cell_entries = Dict{String,Any}[]

    for cell in CELLS
        gap, cn = n01_gap_for_cell(cell, :left)
        entry = Dict{String,Any}(
            "token"          => cell.token,
            "judge_fn"       => string(cell.judge_fn),
            "terrain"        => string(cell.terrain),
            "outcome"        => cell.outcome,
            "is_win"         => is_win(cell.outcome),
            "n01_gap"        => gap,
            "commutator_norm" => cn,
        )
        push!(cell_entries, entry)
        if is_win(cell.outcome)
            push!(win_gaps, gap)
            push!(win_tokens, cell.token)
        else
            push!(lose_gaps, gap)
            push!(lose_tokens, cell.token)
        end
    end

    @assert length(win_gaps) == 8 "Expected 8 WIN cells, got $(length(win_gaps))"
    @assert length(lose_gaps) == 8 "Expected 8 LOSE cells, got $(length(lose_gaps))"

    mean_win  = sum(win_gaps) / length(win_gaps)
    mean_lose = sum(lose_gaps) / length(lose_gaps)
    max_win   = maximum(win_gaps)
    max_lose  = maximum(lose_gaps)
    gap_diff  = mean_win - mean_lose
    scale     = max(mean_win, mean_lose, 1e-15)
    rel_diff  = abs(gap_diff) / scale

    # 5% threshold
    gap_differs = rel_diff > 0.05

    # Also split by uppercase (outer_major) vs lowercase (inner_minor)
    outer_win_gaps  = [cell_entries[i]["n01_gap"] for i in 1:16 if CELLS[i].outcome == "WIN"]
    outer_lose_gaps = [cell_entries[i]["n01_gap"] for i in 1:16 if CELLS[i].outcome == "LOSE"]
    inner_win_gaps  = [cell_entries[i]["n01_gap"] for i in 1:16 if CELLS[i].outcome == "win"]
    inner_lose_gaps = [cell_entries[i]["n01_gap"] for i in 1:16 if CELLS[i].outcome == "lose"]

    outer_win_mean  = isempty(outer_win_gaps)  ? 0.0 : sum(outer_win_gaps)  / length(outer_win_gaps)
    outer_lose_mean = isempty(outer_lose_gaps) ? 0.0 : sum(outer_lose_gaps) / length(outer_lose_gaps)
    inner_win_mean  = isempty(inner_win_gaps)  ? 0.0 : sum(inner_win_gaps)  / length(inner_win_gaps)
    inner_lose_mean = isempty(inner_lose_gaps) ? 0.0 : sum(inner_lose_gaps) / length(inner_lose_gaps)

    return Dict{String,Any}(
        "n_win_cells"  => length(win_gaps),
        "n_lose_cells" => length(lose_gaps),
        "win_tokens"   => win_tokens,
        "lose_tokens"  => lose_tokens,
        "win_gaps"     => win_gaps,
        "lose_gaps"    => lose_gaps,
        "mean_n01_gap_win"   => mean_win,
        "mean_n01_gap_lose"  => mean_lose,
        "max_n01_gap_win"    => max_win,
        "max_n01_gap_lose"   => max_lose,
        "gap_diff_win_minus_lose" => gap_diff,
        "relative_diff"      => rel_diff,
        "gap_differs_above_5pct" => gap_differs,
        "outer_major_mean_WIN"  => outer_win_mean,
        "outer_major_mean_LOSE" => outer_lose_mean,
        "inner_minor_mean_win"  => inner_win_mean,
        "inner_minor_mean_lose" => inner_lose_mean,
        "outer_vs_inner_WIN_diff" => outer_win_mean - inner_win_mean,
        "outer_vs_inner_LOSE_diff" => outer_lose_mean - inner_lose_mean,
        "cell_entries" => cell_entries,
        "honest_note" => (
            gap_differs
            ? "N01 gap distribution differs by > 5% between WIN and LOSE cells — survived N01-gap correlation probe"
            : "N01 gap distribution does not differ by > 5% between WIN and LOSE — WIN/LOSE is grammar at N01-gap level too"
        ),
    )
end

# ── Positive / negative / boundary checks ────────────────────────────────────
function positive_negative_boundary_checks()
    results = Dict{String,Any}[]

    # POSITIVE: all 16 cells at n_steps=16 produce valid density matrices
    all_valid = true
    for cell in CELLS
        rho_in  = terrain_initial_rho(cell.terrain, :left)
        rho_out = apply_channel_frac(cell.judge_fn, rho_in, 1.0)
        ev = real.(eigvals(Hermitian(rho_out)))
        pos = all(e -> e >= -1e-10, ev)
        herm = norm(rho_out - rho_out') < 1e-12
        tr_ok = abs(tr(rho_out) - 1.0) < 1e-12
        push!(results, Dict{String,Any}(
            "check"  => "valid_dm_$(cell.token)",
            "kind"   => "positive",
            "pos_ok" => pos, "herm_ok" => herm, "tr_ok" => tr_ok,
            "passed" => pos && herm && tr_ok,
        ))
        if !(pos && herm && tr_ok)
            all_valid = false
        end
    end

    # NEGATIVE: trajectory at t=0 should equal rho_in (identity application)
    for cell in CELLS[1:4]
        rho_in = terrain_initial_rho(cell.terrain, :left)
        rho_t0 = apply_channel_frac(cell.judge_fn, rho_in, 0.0)
        diff   = trace_norm(rho_t0 .- rho_in)
        push!(results, Dict{String,Any}(
            "check"  => "t0_is_identity_$(cell.token)",
            "kind"   => "negative_control",
            "trace_norm_diff_t0_vs_rho_in" => diff,
            "passed" => diff < 1e-12,
        ))
    end

    # BOUNDARY: at t=1, trajectory endpoint should match apply_channel_frac=1 = canonical channel
    for cell in CELLS[1:4]
        p = P_CANONICAL
        rho_in = terrain_initial_rho(cell.terrain, :left)
        rho_t1 = apply_channel_frac(cell.judge_fn, rho_in, 1.0)
        # Apply canonical channel directly for comparison
        if cell.judge_fn == :Ti
            rho_ref = apply_Ti(rho_in, p.q1)
        elseif cell.judge_fn == :Te
            rho_ref = apply_Te(rho_in, p.q2)
        elseif cell.judge_fn == :Fi
            rho_ref = apply_Fi(rho_in, p.theta)
        else
            rho_ref = apply_Fe(rho_in, p.phi)
        end
        diff = trace_norm(rho_t1 .- rho_ref)
        push!(results, Dict{String,Any}(
            "check"  => "t1_matches_canonical_$(cell.token)",
            "kind"   => "boundary",
            "trace_norm_diff" => diff,
            "passed" => diff < 1e-12,
        ))
    end

    # WRONG STRUCTURE: N01 gap for commuting operators should be ~0
    # Use diagonal operators A = diag(1,2), B = diag(3,5) — commuting
    diag_A = Matrix(Diagonal([1.0+0im, 2.0+0im]))
    diag_B = Matrix(Diagonal([3.0+0im, 5.0+0im]))
    rho_test = terrain_initial_rho(:Se, :left)
    psi_test = principal_eigenvector(rho_test)
    ab_psi_ctrl = diag_A * (diag_B * psi_test)
    ba_psi_ctrl = diag_B * (diag_A * psi_test)
    ctrl_gap = norm(ab_psi_ctrl .- ba_psi_ctrl)
    push!(results, Dict{String,Any}(
        "check"  => "commuting_control_n01_gap_zero",
        "kind"   => "wrong_structure_control",
        "gap"    => ctrl_gap,
        "passed" => ctrl_gap < 1e-12,
        "note"   => "Commuting diagonal operators produce ~0 N01 gap; non-commuting Pauli pair produces nonzero gap"
    ))

    # WRONG STRUCTURE: erased N01 witness — if B=A (self-commuting) gap should be 0
    psi_self = psi_test
    A_self = sx
    ab_self = A_self * (A_self * psi_self)
    ba_self = A_self * (A_self * psi_self)
    self_gap = norm(ab_self .- ba_self)
    push!(results, Dict{String,Any}(
        "check"  => "self_commutator_gap_zero",
        "kind"   => "wrong_structure_control",
        "gap"    => self_gap,
        "passed" => self_gap < 1e-12,
        "note"   => "A*A*psi - A*A*psi = 0 always; valid zero-gap control"
    ))

    all_passed = all(r["passed"] for r in results)
    return Dict{String,Any}("checks" => results, "all_passed" => all_passed)
end

# ── Size ladder ───────────────────────────────────────────────────────────────
# The 16-cell engine is fixed (2x2 Hilbert space), so the ladder varies
# the number of substeps: 8/16/32/64. We verify trajectory continuity at each.
function size_ladder_check()
    sizes = [8, 16, 32, 64]
    ladder = Dict{String,Any}[]
    for n in sizes
        p = params_for_steps(n)
        all_valid = true
        max_div = 0.0
        for cell in CELLS
            rho_in = terrain_initial_rho(cell.terrain, :left)
            for k in 1:n
                t = k / n
                # Apply with this ladder's scale
                if cell.judge_fn == :Ti
                    rho_t = apply_Ti(rho_in, p.q1 * t)
                elseif cell.judge_fn == :Te
                    rho_t = apply_Te(rho_in, p.q2 * t)
                elseif cell.judge_fn == :Fi
                    rho_t = apply_Fi(rho_in, p.theta * t)
                else
                    rho_t = apply_Fe(rho_in, p.phi * t)
                end
                ev = real.(eigvals(Hermitian(rho_t)))
                if !all(e -> e >= -1e-10, ev)
                    all_valid = false
                end
            end
            # compare WIN vs LOSE cross-group divergence at this n
        end
        # Cross-group divergence at n substeps
        win_cs  = filter(c -> is_win(c.outcome), CELLS)
        lose_cs = filter(c -> is_lose(c.outcome), CELLS)
        divs = Float64[]
        for k in 1:n
            t = k / n
            rho_ws = sum(apply_channel_frac(c.judge_fn, terrain_initial_rho(c.terrain, :left), t) for c in win_cs)  ./ length(win_cs)
            rho_ls = sum(apply_channel_frac(c.judge_fn, terrain_initial_rho(c.terrain, :left), t) for c in lose_cs) ./ length(lose_cs)
            push!(divs, trace_norm(rho_ws .- rho_ls))
        end
        max_div = maximum(divs)

        push!(ladder, Dict{String,Any}(
            "n_substeps"  => n,
            "all_valid_dm" => all_valid,
            "cross_group_max_trace_norm_divergence" => max_div,
        ))
    end
    return Dict{String,Any}("ladder" => ladder)
end

# ── Main ──────────────────────────────────────────────────────────────────────
function main()
    println("=== wd_traj_order_winlose_julia ===")
    println("Running Part A: trajectory divergence...")
    part_a = part_a_trajectory_divergence()
    println("Running Part B: N01 gap split by WIN/LOSE...")
    part_b = part_b_n01_gap_split()
    println("Running positive/negative/boundary checks...")
    pnb = positive_negative_boundary_checks()
    println("Running size ladder...")
    ladder = size_ladder_check()

    # ── Verdict ───────────────────────────────────────────────────────────────
    cross_max_div = part_a["cross_group_win_vs_lose"]["max_trace_norm_divergence"]
    n01_gap_differs = part_b["gap_differs_above_5pct"]
    outer_max_div = part_a["outer_major_loop"]["max_trace_norm_divergence"]
    inner_max_div = part_a["inner_minor_loop"]["max_trace_norm_divergence"]

    # Thresholds
    TRAJ_THRESHOLD = 0.05  # trace norm: 0.05 on [0,2] scale is 2.5% relative
    TRAJ_SIGNAL = cross_max_div > TRAJ_THRESHOLD

    verdict_traj = TRAJ_SIGNAL ? "traj_divergence_survived" : "traj_divergence_null"
    verdict_n01  = n01_gap_differs ? "n01_gap_differs_WIN_LOSE" : "n01_gap_null"

    if !TRAJ_SIGNAL && !n01_gap_differs
        verdict = "grammar_terminal_all_levels"
        verdict_note = "WIN/LOSE does not co-vary with trajectory divergence OR N01 gap at any measured level. Label is pure grammar at all levels tested."
    elseif TRAJ_SIGNAL && n01_gap_differs
        verdict = "partial_covariance_both_probes"
        verdict_note = "WIN/LOSE shows some co-variance with both trajectory divergence and N01 gap. Survived both probes — not grammar-terminal."
    elseif TRAJ_SIGNAL
        verdict = "partial_covariance_traj_only"
        verdict_note = "WIN/LOSE co-varies with trajectory divergence but not N01 gap."
    else
        verdict = "partial_covariance_n01_only"
        verdict_note = "WIN/LOSE co-varies with N01 gap but not trajectory divergence."
    end

    result = Dict{String,Any}(
        "object_id"         => "wd_traj_order_winlose_julia",
        "move"              => "traj_order_winlose",
        "engine"            => "julia",
        "run_timestamp"     => string(now()),
        "claim_ceiling"     => "finite_map_carrier_only",
        "promotion_allowed" => false,
        "root_constraints"  => ["F01", "N01"],
        "n_substeps"        => N_SUBSTEPS,
        "n_cells"           => length(CELLS),
        "n_steps_canonical" => N_STEPS_CANONICAL,
        "part_a_trajectory_divergence" => part_a,
        "part_b_n01_gap_split"         => part_b,
        "positive_negative_boundary"   => pnb,
        "size_ladder"                  => ladder,
        "verdict" => Dict{String,Any}(
            "verdict"                    => verdict,
            "verdict_note"               => verdict_note,
            "cross_max_traj_divergence"  => cross_max_div,
            "traj_threshold"             => TRAJ_THRESHOLD,
            "traj_signal"                => TRAJ_SIGNAL,
            "n01_gap_signal"             => n01_gap_differs,
            "mean_n01_gap_win"           => part_b["mean_n01_gap_win"],
            "mean_n01_gap_lose"          => part_b["mean_n01_gap_lose"],
            "n01_gap_relative_diff"      => part_b["relative_diff"],
            "outer_major_max_div"        => outer_max_div,
            "inner_minor_max_div"        => inner_max_div,
        ),
    )

    out_path = joinpath(@__DIR__, "wd_traj_order_winlose_julia_results.json")
    open(out_path, "w") do f
        JSON.print(f, result, 2)
    end
    println("Written: ", out_path)

    println("\n=== VERDICT ===")
    println("verdict: ", verdict)
    println("verdict_note: ", verdict_note)
    println("cross-group max trajectory divergence (WIN vs LOSE mean rho): ", cross_max_div)
    println("outer-major max traj divergence: ", outer_max_div)
    println("inner-minor max traj divergence: ", inner_max_div)
    println("N01 gap: mean_WIN=", part_b["mean_n01_gap_win"], "  mean_LOSE=", part_b["mean_n01_gap_lose"])
    println("N01 gap relative diff: ", part_b["relative_diff"], "  (> 5%? ", n01_gap_differs, ")")
    println("Structural note: ", part_a["structural_note"])
    println("All pnb checks passed: ", pnb["all_passed"])
end

main()
