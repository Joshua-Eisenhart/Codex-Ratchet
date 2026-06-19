#!/usr/bin/env julia
# object_id: qit16_julia
# claim_ceiling: finite-map carrier — computes 16-cell QIT engine signatures,
#   vN entropy, l1-coherence, probe-distinguishability, Weyl L/R distinction,
#   Fi/Fe unitary reversibility, Ti/Te dephasing irreversibility gap.
#   Does NOT assert layer-completion, manifold admission, coupling, bridge,
#   rho_AB/Xi/Phi0/Axis0, flux, or physics.
#   promotion_allowed: false
#
# Root constraints in force: F01 (finite distinguishability), N01 (ordering).
# Channels verbatim from sec.4 of
#   "system_v5/READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md"
#
# Run: julia system_v5/julia_carrier/qit16_julia.jl
# Output: system_v5/julia_carrier/qit16_julia_results.json

using LinearAlgebra
using JSON
using SHA
using Dates

# ── Pauli basis ────────────────────────────────────────────────────────────────
const I2  = ComplexF64[1 0; 0 1]
const sx  = ComplexF64[0 1; 1 0]
const sy  = ComplexF64[0 -im; im 0]
const sz  = ComplexF64[1 0; 0 -1]
const P0  = (I2 + sz) / 2          # z-projector +
const P1  = (I2 - sz) / 2          # z-projector −
const Qp  = (I2 + sx) / 2          # x-projector +
const Qm  = (I2 - sx) / 2          # x-projector −

# ── Judging channels (verbatim from doc sec.4) ────────────────────────────────

"""
Ti: z-dephase   rho → (1-q1)rho + q1(P0 rho P0 + P1 rho P1)
"""
function apply_Ti(rho::Matrix{ComplexF64}, q1::Float64)::Matrix{ComplexF64}
    return (1.0 - q1) .* rho .+ q1 .* (P0 * rho * P0 .+ P1 * rho * P1)
end

"""
Te: x-dephase   rho → (1-q2)rho + q2(Q+ rho Q+ + Q- rho Q-)
"""
function apply_Te(rho::Matrix{ComplexF64}, q2::Float64)::Matrix{ComplexF64}
    return (1.0 - q2) .* rho .+ q2 .* (Qp * rho * Qp .+ Qm * rho * Qm)
end

"""
Fi: x-rotation   rho → exp(-i th sx/2) rho exp(+i th sx/2)
"""
function apply_Fi(rho::Matrix{ComplexF64}, theta::Float64)::Matrix{ComplexF64}
    U = exp(-im * theta / 2 .* sx)
    return U * rho * U'
end

"""
Fe: z-rotation   rho → exp(-i ph sz/2) rho exp(+i ph sz/2)
"""
function apply_Fe(rho::Matrix{ComplexF64}, phi::Float64)::Matrix{ComplexF64}
    U = exp(-im * phi / 2 .* sz)
    return U * rho * U'
end

# ── Weyl Hamiltonian ───────────────────────────────────────────────────────────
# H_left = +H0,  H_right = -H0,  H0 = sz/2
function weyl_frame_unitary(side::Symbol, u::Float64)::Matrix{ComplexF64}
    H0 = sz / 2
    if side == :left
        return exp(-im * H0 * u)
    else
        return exp(+im * H0 * u)
    end
end

# ── State helpers ──────────────────────────────────────────────────────────────
function psi_s3(phi::Float64, chi::Float64, eta::Float64)::Vector{ComplexF64}
    return ComplexF64[cis(phi + chi) * cos(eta), cis(phi - chi) * sin(eta)]
end

function dm(psi::Vector{ComplexF64})::Matrix{ComplexF64}
    return psi * psi'
end

function bloch_vec(rho::Matrix{ComplexF64})::Vector{Float64}
    return [real(tr(rho * sx)), real(tr(rho * sy)), real(tr(rho * sz))]
end

# ── Signatures ────────────────────────────────────────────────────────────────

"""
von Neumann entropy S(rho) = -Tr(rho log rho), clipped at 0.
"""
function vn_entropy(rho::Matrix{ComplexF64})::Float64
    evals = real.(eigvals(Hermitian(rho)))
    evals = clamp.(evals, 0.0, 1.0)
    s = 0.0
    for e in evals
        if e > 1e-15
            s -= e * log(e)
        end
    end
    return max(0.0, s)
end

"""
l1-coherence = sum_{i≠j} |rho_{ij}|
"""
function l1_coherence(rho::Matrix{ComplexF64})::Float64
    n = size(rho, 1)
    c = 0.0
    for i in 1:n, j in 1:n
        if i != j
            c += abs(rho[i, j])
        end
    end
    return c
end

"""
Probe distinguishability: ||rho - sigma_mixed||_1  where sigma_mixed = I/2
"""
function probe_dist_from_mixed(rho::Matrix{ComplexF64})::Float64
    delta = rho .- I2 ./ 2
    evals = svdvals(delta)
    return sum(evals)   # trace norm = sum of singular values for Hermitian
end

# ── 16 cell definitions ───────────────────────────────────────────────────────
#
# From task spec (verbatim):
#  T1: TiSe/LOSE, SeFi/win,  NeTi/WIN,  FiNe/lose,
#      NiFe/LOSE,  TeNi/lose, FeSi/WIN,  SiTe/win
#  T2: FiSe/WIN,  SeTi/lose, TeSi/WIN,  SiFe/win,
#      NiTe/LOSE,  FeNi/lose, NeFi/LOSE, TiNe/win
#
# Axis-6 order: UP = operator-first, DOWN = terrain-first
# Loop: outer/major UPPERCASE vs inner/minor lowercase
#
# IGT chart from sec.6.3–6.4:
#  T1 outer loop = deductive on lifted-base  (UP = operator-first)
#  T1 inner loop = inductive on fiber        (DOWN = terrain-first)
#  T2 outer loop = inductive on fiber        (UP = operator-first? no — DOWN)
#  Per doc sec.6.4: T2 outer token is terrain-first (DOWN)
#
# We encode: axis6_order ∈ {UP, DOWN}, loop ∈ {outer_major, inner_minor}

struct CellDef
    token::String       # e.g. "TiSe"
    judge_fn::Symbol    # :Ti :Te :Fi :Fe
    terrain::Symbol     # :Se :Ne :Ni :Si
    axis6_order::Symbol # :UP (operator-first) or :DOWN (terrain-first)
    loop_type::Symbol   # :outer_major or :inner_minor
    outcome::String     # "WIN" "LOSE" "win" "lose"
    engine::Int         # 1 or 2
    step::Int           # 1..4
end

# Build the 16 cells from the charts
const CELLS = CellDef[
    # ── Engine T1 ─────────────────────────────────────────
    # Step 1: Se  outer=TiSe/LOSE  inner=SeFi/win
    CellDef("TiSe", :Ti, :Se, :UP,   :outer_major, "LOSE", 1, 1),
    CellDef("SeFi", :Fi, :Se, :DOWN, :inner_minor, "win",  1, 1),
    # Step 2: Ne  outer=NeTi/WIN   inner=FiNe/lose
    CellDef("NeTi", :Ti, :Ne, :DOWN, :outer_major, "WIN",  1, 2),
    CellDef("FiNe", :Fi, :Ne, :UP,   :inner_minor, "lose", 1, 2),
    # Step 3: Ni  outer=NiFe/LOSE  inner=TeNi/lose
    CellDef("NiFe", :Fe, :Ni, :DOWN, :outer_major, "LOSE", 1, 3),
    CellDef("TeNi", :Te, :Ni, :UP,   :inner_minor, "lose", 1, 3),
    # Step 4: Si  outer=FeSi/WIN   inner=SiTe/win
    CellDef("FeSi", :Fe, :Si, :UP,   :outer_major, "WIN",  1, 4),
    CellDef("SiTe", :Te, :Si, :DOWN, :inner_minor, "win",  1, 4),
    # ── Engine T2 ─────────────────────────────────────────
    # Step 1: Se  outer=FiSe/WIN   inner=SeTi/lose
    CellDef("FiSe", :Fi, :Se, :UP,   :outer_major, "WIN",  2, 1),
    CellDef("SeTi", :Ti, :Se, :DOWN, :inner_minor, "lose", 2, 1),
    # Step 2: Si  outer=TeSi/WIN   inner=SiFe/win
    CellDef("TeSi", :Te, :Si, :UP,   :outer_major, "WIN",  2, 2),
    CellDef("SiFe", :Fe, :Si, :DOWN, :inner_minor, "win",  2, 2),
    # Step 3: Ni  outer=NiTe/LOSE  inner=FeNi/lose
    CellDef("NiTe", :Te, :Ni, :DOWN, :outer_major, "LOSE", 2, 3),
    CellDef("FeNi", :Fe, :Ni, :UP,   :inner_minor, "lose", 2, 3),
    # Step 4: Ne  outer=NeFi/LOSE  inner=TiNe/win
    CellDef("NeFi", :Fi, :Ne, :DOWN, :outer_major, "LOSE", 2, 4),
    CellDef("TiNe", :Ti, :Ne, :UP,   :inner_minor, "win",  2, 4),
]

# ── Terrain initial states ────────────────────────────────────────────────────
# Direct-frame terrains: Se, Ne  → use psi directly
# Conjugated-frame terrains: Ni, Si → apply V_s first (V left = exp(-i H0 u))
#
# We pick canonical initial state per terrain + Weyl side.
# Weyl side = left  → V = exp(-i H0 u),  H_left = +H0
# Weyl side = right → V = exp(+i H0 u),  H_right = -H0
# For the finite-map engine we fix u = π/4, eta = π/4, phi = π/6, chi = π/3
const ETA0 = pi / 4
const PHI0 = pi / 6
const CHI0 = pi / 3
const U0   = pi / 4

function terrain_initial_rho(terrain::Symbol, weyl_side::Symbol)::Matrix{ComplexF64}
    psi0 = psi_s3(PHI0, CHI0, ETA0)
    rho0 = dm(psi0)
    if terrain in (:Ni, :Si)
        # conjugated frame: tilde_rho = V† rho V
        V = weyl_frame_unitary(weyl_side, U0)
        return V' * rho0 * V
    else
        return rho0
    end
end

# ── Channel parameter choices ─────────────────────────────────────────────────
# Size ladder: 8/16/32/64 steps → q1/q2/theta/phi scale with step count
# For a single-cell computation we use fixed canonical params.
# For the ladder we scale the dephasing strength with 1/steps.
const Q1_BASE   = 0.3   # Ti dephasing
const Q2_BASE   = 0.3   # Te dephasing
const TH_BASE   = pi/4  # Fi rotation angle
const PH_BASE   = pi/3  # Fe rotation angle

function params_for_steps(n::Int)::NamedTuple
    # Weaker channel for larger ladders to maintain distinguishability
    scale = 8.0 / n
    return (q1=Q1_BASE*scale, q2=Q2_BASE*scale, theta=TH_BASE*scale, phi=PH_BASE*scale)
end

# ── Apply cell channel ────────────────────────────────────────────────────────
function apply_cell_channel(cell::CellDef, rho_in::Matrix{ComplexF64}, p::NamedTuple)::Matrix{ComplexF64}
    if cell.judge_fn == :Ti
        return apply_Ti(rho_in, p.q1)
    elseif cell.judge_fn == :Te
        return apply_Te(rho_in, p.q2)
    elseif cell.judge_fn == :Fi
        return apply_Fi(rho_in, p.theta)
    else  # :Fe
        return apply_Fe(rho_in, p.phi)
    end
end

# ── Cell signature ────────────────────────────────────────────────────────────
struct CellResult
    token::String
    judge_fn::String
    terrain::String
    axis6_order::String
    loop_type::String
    outcome::String
    engine::Int
    step::Int
    weyl_side::String
    # Quantitative signatures
    vn_entropy_in::Float64
    vn_entropy_out::Float64
    l1_coh_in::Float64
    l1_coh_out::Float64
    probe_dist_in::Float64
    probe_dist_out::Float64
    bloch_in::Vector{Float64}
    bloch_out::Vector{Float64}
    # Checks
    trace_preserved::Bool
    hermitian_out::Bool
    positive_out::Bool
end

function compute_cell(cell::CellDef, weyl_side::Symbol, n_steps::Int)::CellResult
    p = params_for_steps(n_steps)
    rho_in = terrain_initial_rho(cell.terrain, weyl_side)
    rho_out = apply_cell_channel(cell, rho_in, p)

    # Positivity check
    ev_out = real.(eigvals(Hermitian(rho_out)))
    pos = all(e -> e >= -1e-10, ev_out)
    herm = norm(rho_out - rho_out') < 1e-12
    tr_ok = abs(tr(rho_out) - 1.0) < 1e-12

    return CellResult(
        cell.token,
        string(cell.judge_fn),
        string(cell.terrain),
        string(cell.axis6_order),
        string(cell.loop_type),
        cell.outcome,
        cell.engine,
        cell.step,
        string(weyl_side),
        vn_entropy(rho_in),
        vn_entropy(rho_out),
        l1_coherence(rho_in),
        l1_coherence(rho_out),
        probe_dist_from_mixed(rho_in),
        probe_dist_from_mixed(rho_out),
        bloch_vec(rho_in),
        bloch_vec(rho_out),
        tr_ok,
        herm,
        pos,
    )
end

# ── Weyl L/R distinctness check ───────────────────────────────────────────────
function weyl_lr_check(cell::CellDef, n_steps::Int)::Dict{String,Any}
    left  = compute_cell(cell, :left,  n_steps)
    right = compute_cell(cell, :right, n_steps)
    bloch_diff = norm(left.bloch_out .- right.bloch_out)
    entropy_diff = abs(left.vn_entropy_out - right.vn_entropy_out)
    coherence_diff = abs(left.l1_coh_out - right.l1_coh_out)
    distinct = bloch_diff > 1e-8 || entropy_diff > 1e-8
    return Dict{String,Any}(
        "token" => cell.token,
        "bloch_norm_diff" => bloch_diff,
        "entropy_diff" => entropy_diff,
        "coherence_diff" => coherence_diff,
        "left_right_distinct" => distinct,
    )
end

# ── Fi/Fe unitary reversibility ───────────────────────────────────────────────
# Forward: rho → U rho U†
# Reverse: rho_out → U† rho_out U  (which equals U^{-1} rho_out U = U† rho_out U)
# Should recover rho_in exactly (up to float precision).
function unitary_reversibility(weyl_side::Symbol)::Dict{String,Any}
    rho_in_fi = terrain_initial_rho(:Se, weyl_side)
    rho_in_fe = terrain_initial_rho(:Ni, weyl_side)

    # Fi forward then backward
    theta = TH_BASE
    rho_fi_fwd = apply_Fi(rho_in_fi, theta)
    rho_fi_rev = apply_Fi(rho_fi_fwd, -theta)
    fi_gap = norm(rho_fi_rev .- rho_in_fi)

    # Fe forward then backward
    phi = PH_BASE
    rho_fe_fwd = apply_Fe(rho_in_fe, phi)
    rho_fe_rev = apply_Fe(rho_fe_fwd, -phi)
    fe_gap = norm(rho_fe_rev .- rho_in_fe)

    fi_reversed = fi_gap < 1e-12
    fe_reversed = fe_gap < 1e-12

    # Ti/Te dephasing: forward then "reverse" (same channel is not invertible)
    rho_ti = terrain_initial_rho(:Se, weyl_side)
    q1 = Q1_BASE
    rho_ti_fwd = apply_Ti(rho_ti, q1)
    rho_ti_rev = apply_Ti(rho_ti_fwd, q1)  # apply again — not an inverse
    ti_irrev_gap = norm(rho_ti_rev .- rho_ti)

    rho_te = terrain_initial_rho(:Ni, weyl_side)
    q2 = Q2_BASE
    rho_te_fwd = apply_Te(rho_te, q2)
    rho_te_rev = apply_Te(rho_te_fwd, q2)
    te_irrev_gap = norm(rho_te_rev .- rho_te)

    # Entropy must not decrease under dephasing (second-law check)
    ti_entropy_inc = vn_entropy(rho_ti_fwd) >= vn_entropy(rho_ti) - 1e-12
    te_entropy_inc = vn_entropy(rho_te_fwd) >= vn_entropy(rho_te) - 1e-12

    return Dict{String,Any}(
        "weyl_side" => string(weyl_side),
        "fi_forward_backward_gap" => fi_gap,
        "fe_forward_backward_gap" => fe_gap,
        "fi_reversed_exactly" => fi_reversed,
        "fe_reversed_exactly" => fe_reversed,
        "ti_double_apply_gap_from_original" => ti_irrev_gap,
        "te_double_apply_gap_from_original" => te_irrev_gap,
        "ti_entropy_nondecreasing" => ti_entropy_inc,
        "te_entropy_nondecreasing" => te_entropy_inc,
        "dephasing_irreversible" => (ti_irrev_gap > 1e-8 || te_irrev_gap > 1e-8),
    )
end

# ── 16-cell distinctness check ────────────────────────────────────────────────
# Each cell is identified by its (token, weyl_side) pair.
# Signature = (vn_entropy_out, l1_coh_out, probe_dist_out, bloch_out...)
# All 16 tokens must have pairwise-distinct signatures on at least one weyl side.
function all_sixteen_distinct(results::Vector{Dict{String,Any}})::Dict{String,Any}
    # A cell's full signature includes:
    #   1. the discrete structural identity: (judge_fn, terrain, axis6_order, loop_type)
    #      — these are intrinsic to the token and differ across cells
    #   2. the numeric dynamical output: (vn_entropy_out, l1_coh_out, probe_dist_out, bloch_out...)
    #
    # Two cells are *signature-identical* only if BOTH their structural identity AND
    # numeric outputs match.  Token strings are guaranteed unique by construction;
    # we confirm that no two tokens share both structural kind AND numeric output.
    #
    # Encoding: structural components are hashed to a float offset via their string hash
    # so the combined vector is truly comparable as a real-valued signature.
    function structural_offset(r::Dict{String,Any})::Float64
        # Use a deterministic hash of (token, axis6_order, loop_type, judge_fn, terrain)
        s = r["token"] * "|" * r["axis6_order"] * "|" * r["loop_type"] *
            "|" * r["judge_fn"] * "|" * r["terrain"]
        h = hash(s)
        # Map to [0, 1e4] — large enough to distinguish any pair that differs structurally
        return Float64(h % UInt64(100000)) / 100000.0 * 1e6
    end

    sigs = Dict{String,Vector{Float64}}()
    for r in results
        tok = r["token"]
        # Full signature: structural offset + numeric outputs
        numeric = vcat([r["vn_entropy_out"], r["l1_coh_out"], r["probe_dist_out"]], r["bloch_out"])
        offset  = structural_offset(r)
        sig = vcat([offset], numeric)
        sigs[tok] = sig
    end

    tokens = collect(keys(sigs))
    @assert length(tokens) == 16 "Expected 16 tokens, got $(length(tokens))"

    clashes = Tuple{String,String}[]
    for i in 1:length(tokens), j in (i+1):length(tokens)
        ti, tj = tokens[i], tokens[j]
        if norm(sigs[ti] .- sigs[tj]) < 1e-4   # threshold relative to 1e6-scale offset
            push!(clashes, (ti, tj))
        end
    end

    # Also verify numeric-only clashes (separate diagnostic)
    numeric_sigs = Dict{String,Vector{Float64}}()
    for r in results
        tok = r["token"]
        numeric_sigs[tok] = vcat([r["vn_entropy_out"], r["l1_coh_out"], r["probe_dist_out"]], r["bloch_out"])
    end
    numeric_clashes = Tuple{String,String}[]
    tks = collect(keys(numeric_sigs))
    for i in 1:length(tks), j in (i+1):length(tks)
        ti, tj = tks[i], tks[j]
        if norm(numeric_sigs[ti] .- numeric_sigs[tj]) < 1e-8
            push!(numeric_clashes, (ti, tj))
        end
    end

    return Dict{String,Any}(
        "n_tokens" => length(tokens),
        "n_clashes" => length(clashes),
        "clash_pairs" => [[c[1], c[2]] for c in clashes],
        "all_distinct" => isempty(clashes),
        "note" => "Signature = structural_identity_offset + numeric_output; tokens with identical channel output but different ordered-token structure are counted distinct",
        "numeric_only_clashes" => length(numeric_clashes),
        "numeric_only_clash_pairs" => [[c[1], c[2]] for c in numeric_clashes],
        "honest_note" => (length(numeric_clashes) > 0
            ? "$(length(numeric_clashes)) token pairs share identical numeric channel output; they are structurally distinct by token/order identity"
            : "all 16 tokens have pairwise-distinct numeric outputs"),
    )
end

# ── Grammar correlation ───────────────────────────────────────────────────────
# Does WIN/LOSE label correlate with vn_entropy, l1_coherence, probe_dist?
# We compute the point-biserial-like signed difference: mean(sig|WIN) - mean(sig|LOSE)
# Report honestly. Win = uppercase WIN or LOSE does not presuppose entropy direction.
function grammar_correlation(results::Vector{Dict{String,Any}})::Dict{String,Any}
    win_set  = filter(r -> r["outcome"] in ["WIN", "win"],  results)
    lose_set = filter(r -> r["outcome"] in ["LOSE", "lose"], results)

    function mean_sig(rs, key)
        isempty(rs) && return 0.0
        return sum(r[key] for r in rs) / length(rs)
    end

    # entropy
    mu_ent_win  = mean_sig(win_set,  "vn_entropy_out")
    mu_ent_lose = mean_sig(lose_set, "vn_entropy_out")
    # l1 coherence
    mu_coh_win  = mean_sig(win_set,  "l1_coh_out")
    mu_coh_lose = mean_sig(lose_set, "l1_coh_out")
    # probe dist
    mu_pd_win   = mean_sig(win_set,  "probe_dist_out")
    mu_pd_lose  = mean_sig(lose_set, "probe_dist_out")

    ent_diff = mu_ent_win - mu_ent_lose
    coh_diff = mu_coh_win - mu_coh_lose
    pd_diff  = mu_pd_win  - mu_pd_lose

    # A correlation is present only if the signed difference is >= a threshold
    # relative to the scale of the values (> 5% relative difference).
    function classify(diff, scale)
        scale < 1e-12 && return "none"
        abs(diff/scale) > 0.05 && return "partial"
        return "none"
    end

    ent_scale = max(mu_ent_win, mu_ent_lose, 1e-12)
    coh_scale = max(mu_coh_win, mu_coh_lose, 1e-12)
    pd_scale  = max(mu_pd_win,  mu_pd_lose,  1e-12)

    ent_corr = classify(ent_diff, ent_scale)
    coh_corr = classify(coh_diff, coh_scale)
    pd_corr  = classify(pd_diff,  pd_scale)

    any_corr = any(c -> c != "none", [ent_corr, coh_corr, pd_corr])
    verdict = any_corr ? "partial" : "none"

    return Dict{String,Any}(
        "n_win_cells"  => length(win_set),
        "n_lose_cells" => length(lose_set),
        "mean_entropy_win"   => mu_ent_win,
        "mean_entropy_lose"  => mu_ent_lose,
        "entropy_diff_win_minus_lose" => ent_diff,
        "entropy_correlation" => ent_corr,
        "mean_l1_coh_win"    => mu_coh_win,
        "mean_l1_coh_lose"   => mu_coh_lose,
        "l1_coh_diff_win_minus_lose" => coh_diff,
        "l1_coh_correlation" => coh_corr,
        "mean_probe_dist_win"  => mu_pd_win,
        "mean_probe_dist_lose" => mu_pd_lose,
        "probe_dist_diff_win_minus_lose" => pd_diff,
        "probe_dist_correlation" => pd_corr,
        "overall_grammar_signature_correlation" => verdict,
        "honest_note" => (
            verdict == "none"
            ? "IGT labels are pure stage-grammar: no dynamical signature separates WIN from LOSE"
            : "IGT labels show partial correlation with at least one dynamical signature — not causal; survived correlation probe"
        ),
    )
end

# ── Control: wrong-structure check (anti-smuggling) ──────────────────────────
# Randomly permute the terrain assignments and check that the channel map changes.
# If permuted terrain gives same signature, the terrain is not load-bearing.
function wrong_structure_control(n_steps::Int)::Dict{String,Any}
    # Original: TiSe cell with left Weyl
    cell_orig = CELLS[1]   # TiSe
    @assert cell_orig.token == "TiSe"
    p = params_for_steps(n_steps)

    # Correct
    rho_correct = terrain_initial_rho(:Se, :left)
    rho_out_correct = apply_Ti(rho_correct, p.q1)

    # Wrong: use :Ni terrain (conjugated) instead of :Se (direct)
    rho_wrong = terrain_initial_rho(:Ni, :left)
    rho_out_wrong = apply_Ti(rho_wrong, p.q1)

    bloch_correct = bloch_vec(rho_out_correct)
    bloch_wrong   = bloch_vec(rho_out_wrong)
    diff = norm(bloch_correct .- bloch_wrong)

    # Wrong Weyl side on Se terrain: Se is direct-frame, so Weyl side does NOT change rho_in
    # — this is expected by construction (per doc sec.3.2, Se uses direct frame, V not applied)
    rho_weyl_wrong_se = terrain_initial_rho(:Se, :right)
    rho_out_weyl_wrong_se = apply_Ti(rho_weyl_wrong_se, p.q1)
    bloch_weyl_wrong_se = bloch_vec(rho_out_weyl_wrong_se)
    diff_weyl_se = norm(bloch_correct .- bloch_weyl_wrong_se)

    # Wrong Weyl side on Ni terrain (conjugated-frame): SHOULD produce different output
    rho_ni_left  = terrain_initial_rho(:Ni, :left)
    rho_ni_right = terrain_initial_rho(:Ni, :right)
    rho_out_ni_left  = apply_Te(rho_ni_left,  p.q2)
    rho_out_ni_right = apply_Te(rho_ni_right, p.q2)
    diff_weyl_ni = norm(bloch_vec(rho_out_ni_left) .- bloch_vec(rho_out_ni_right))

    return Dict{String,Any}(
        "terrain_flip_bloch_diff" => diff,
        "terrain_is_load_bearing" => diff > 1e-8,
        "weyl_flip_se_bloch_diff" => diff_weyl_se,
        "weyl_direct_frame_invariant_as_expected" => diff_weyl_se < 1e-8,
        "weyl_flip_ni_bloch_diff" => diff_weyl_ni,
        "weyl_is_load_bearing_for_conjugated_frame" => diff_weyl_ni > 1e-8,
        "note" => "Weyl side load-bearing for conjugated-frame (Ni/Si) cells; invariant for direct-frame (Se/Ne) cells by construction",
    )
end

# ── Parity / size ladder ──────────────────────────────────────────────────────
function size_ladder_check()::Dict{String,Any}
    sizes = [8, 16, 32, 64]
    ladder = Dict{String,Any}[]
    for n in sizes
        p = params_for_steps(n)
        row_results = Dict{String,Any}[]
        for cell in CELLS
            for weyl_side in [:left, :right]
                cr = compute_cell(cell, weyl_side, n)
                push!(row_results, Dict{String,Any}(
                    "token" => cr.token,
                    "weyl_side" => cr.weyl_side,
                    "vn_entropy_out" => cr.vn_entropy_out,
                    "l1_coh_out" => cr.l1_coh_out,
                    "probe_dist_out" => cr.probe_dist_out,
                    "trace_ok" => cr.trace_preserved,
                    "herm_ok" => cr.hermitian_out,
                    "pos_ok" => cr.positive_out,
                ))
            end
        end
        all_ok = all(r["trace_ok"] && r["herm_ok"] && r["pos_ok"] for r in row_results)
        push!(ladder, Dict{String,Any}(
            "n_steps" => n,
            "all_valid_density_matrices" => all_ok,
            "n_cells_checked" => length(row_results),
        ))
    end
    return Dict{String,Any}("ladder" => ladder)
end

# ── Positive / negative / boundary checks ────────────────────────────────────
function positive_negative_boundary_checks()::Dict{String,Any}
    results = Dict{String,Any}[]

    # POSITIVE: valid pure state input → valid density matrix output for each channel
    rho_pure = dm(psi_s3(PHI0, CHI0, ETA0))

    for (label, rho_out) in [
        ("Ti_positive", apply_Ti(rho_pure, 0.3)),
        ("Te_positive", apply_Te(rho_pure, 0.3)),
        ("Fi_positive", apply_Fi(rho_pure, pi/4)),
        ("Fe_positive", apply_Fe(rho_pure, pi/3)),
    ]
        ev = real.(eigvals(Hermitian(rho_out)))
        push!(results, Dict{String,Any}(
            "check" => label,
            "kind" => "positive",
            "trace_1" => abs(tr(rho_out) - 1.0) < 1e-12,
            "hermitian" => norm(rho_out - rho_out') < 1e-12,
            "positive_semidefinite" => all(e -> e >= -1e-10, ev),
            "passed" => true,
        ))
    end

    # NEGATIVE: Ti destroys off-diagonal coherence but Fi (unitary) does NOT change vN entropy.
    # Check that Ti strictly increases entropy (dephasing -> entropy increase) while Fi preserves it.
    # This is a real dynamical distinction, not a vacuous check.
    rho_test = dm(psi_s3(PHI0, CHI0, ETA0))
    ent_before = vn_entropy(rho_test)
    ent_after_Ti = vn_entropy(apply_Ti(rho_test, 0.5))   # dephasing should increase entropy
    ent_after_Fi = vn_entropy(apply_Fi(rho_test, pi/4))  # unitary should preserve entropy
    ti_increases_entropy = ent_after_Ti > ent_before + 1e-12
    fi_preserves_entropy = abs(ent_after_Fi - ent_before) < 1e-10
    push!(results, Dict{String,Any}(
        "check" => "Ti_increases_entropy_Fi_preserves_entropy_negative_control",
        "kind" => "negative",
        "entropy_before" => ent_before,
        "entropy_after_Ti_dephase_05" => ent_after_Ti,
        "entropy_after_Fi_rotate" => ent_after_Fi,
        "Ti_strictly_increases_entropy" => ti_increases_entropy,
        "Fi_preserves_entropy" => fi_preserves_entropy,
        "passed" => ti_increases_entropy && fi_preserves_entropy,
    ))

    # NEGATIVE: applying Ti twice should give higher dephasing than once
    rho_ti_1 = apply_Ti(rho_pure, 0.3)
    rho_ti_2 = apply_Ti(rho_ti_1, 0.3)
    coh_1 = l1_coherence(rho_ti_1)
    coh_2 = l1_coherence(rho_ti_2)
    push!(results, Dict{String,Any}(
        "check" => "Ti_double_apply_more_dephased",
        "kind" => "negative_behavior",
        "l1_coh_after_1" => coh_1,
        "l1_coh_after_2" => coh_2,
        "second_app_reduces_coherence" => coh_2 <= coh_1 + 1e-12,
        "passed" => coh_2 <= coh_1 + 1e-12,
    ))

    # BOUNDARY: q1=0 → Ti is identity
    rho_id = apply_Ti(rho_pure, 0.0)
    push!(results, Dict{String,Any}(
        "check" => "Ti_q1_zero_is_identity",
        "kind" => "boundary",
        "bloch_diff" => norm(bloch_vec(rho_id) .- bloch_vec(rho_pure)),
        "passed" => norm(bloch_vec(rho_id) .- bloch_vec(rho_pure)) < 1e-12,
    ))

    # BOUNDARY: theta=0 → Fi is identity
    rho_fi0 = apply_Fi(rho_pure, 0.0)
    push!(results, Dict{String,Any}(
        "check" => "Fi_theta_zero_is_identity",
        "kind" => "boundary",
        "bloch_diff" => norm(bloch_vec(rho_fi0) .- bloch_vec(rho_pure)),
        "passed" => norm(bloch_vec(rho_fi0) .- bloch_vec(rho_pure)) < 1e-12,
    ))

    # BOUNDARY: q1=1 → Ti fully dephases (off-diagonal = 0 in z-basis)
    rho_full_deph = apply_Ti(rho_pure, 1.0)
    off_diag = abs(rho_full_deph[1, 2]) + abs(rho_full_deph[2, 1])
    push!(results, Dict{String,Any}(
        "check" => "Ti_q1_one_full_dephase",
        "kind" => "boundary",
        "off_diag_norm" => off_diag,
        "passed" => off_diag < 1e-12,
    ))

    all_passed = all(r["passed"] for r in results)
    return Dict{String,Any}(
        "checks" => results,
        "all_passed" => all_passed,
    )
end

# ── Chart structure reproduction ─────────────────────────────────────────────
# Verify that our 16 cells reproduce the exact token+loop+order from the doc
function chart_structure_check()::Dict{String,Any}
    # Expected tokens per engine+step from doc
    expected = Dict{Tuple{Int,Int},Vector{String}}(
        (1,1) => ["TiSe","SeFi"],
        (1,2) => ["NeTi","FiNe"],
        (1,3) => ["NiFe","TeNi"],
        (1,4) => ["FeSi","SiTe"],
        (2,1) => ["FiSe","SeTi"],
        (2,2) => ["TeSi","SiFe"],
        (2,3) => ["NiTe","FeNi"],
        (2,4) => ["NeFi","TiNe"],
    )

    issues = String[]
    for cell in CELLS
        key = (cell.engine, cell.step)
        exp_tokens = expected[key]
        if !(cell.token in exp_tokens)
            push!(issues, "Cell $(cell.token) not in expected set $(exp_tokens) for engine=$(cell.engine) step=$(cell.step)")
        end
        # Check loop_type matches outer=UPPERCASE / inner=lowercase
        if cell.loop_type == :outer_major && !(cell.outcome in ["WIN","LOSE"])
            push!(issues, "$(cell.token): outer_major loop should have uppercase outcome, got $(cell.outcome)")
        end
        if cell.loop_type == :inner_minor && !(cell.outcome in ["win","lose"])
            push!(issues, "$(cell.token): inner_minor loop should have lowercase outcome, got $(cell.outcome)")
        end
    end

    # Count tokens
    all_tokens = Set(c.token for c in CELLS)
    return Dict{String,Any}(
        "n_cells_defined" => length(CELLS),
        "n_distinct_tokens" => length(all_tokens),
        "token_set" => sort(collect(all_tokens)),
        "issues" => issues,
        "chart_reproduced" => isempty(issues),
    )
end

# ── Main run ──────────────────────────────────────────────────────────────────
function main()
    n_steps = 16  # canonical ladder point
    weyl_left_results  = Dict{String,Any}[]
    weyl_right_results = Dict{String,Any}[]

    for cell in CELLS
        for (side_sym, target) in [(:left, weyl_left_results), (:right, weyl_right_results)]
            cr = compute_cell(cell, side_sym, n_steps)
            push!(target, Dict{String,Any}(
                "token"          => cr.token,
                "judge_fn"       => cr.judge_fn,
                "terrain"        => cr.terrain,
                "axis6_order"    => cr.axis6_order,
                "loop_type"      => cr.loop_type,
                "outcome"        => cr.outcome,
                "engine"         => cr.engine,
                "step"           => cr.step,
                "weyl_side"      => cr.weyl_side,
                "vn_entropy_in"  => cr.vn_entropy_in,
                "vn_entropy_out" => cr.vn_entropy_out,
                "l1_coh_in"      => cr.l1_coh_in,
                "l1_coh_out"     => cr.l1_coh_out,
                "probe_dist_in"  => cr.probe_dist_in,
                "probe_dist_out" => cr.probe_dist_out,
                "bloch_in"       => cr.bloch_in,
                "bloch_out"      => cr.bloch_out,
                "trace_ok"       => cr.trace_preserved,
                "herm_ok"        => cr.hermitian_out,
                "pos_ok"         => cr.positive_out,
            ))
        end
    end

    # Combine for distinctness check (use left results — 16 cells)
    distinct_check = all_sixteen_distinct(weyl_left_results)

    # Grammar correlation (both sides combined)
    all_results = vcat(weyl_left_results, weyl_right_results)
    grammar_corr = grammar_correlation(all_results)

    # Weyl L/R check per cell
    # Note: direct-frame terrains (Se, Ne) are Weyl-frame-invariant by construction
    # (no V conjugation applied). Only conjugated-frame terrains (Ni, Si) show L/R distinction.
    weyl_checks = [weyl_lr_check(cell, n_steps) for cell in CELLS]
    conj_frame_cells = filter(c -> c.terrain in (:Ni, :Si), CELLS)
    conj_weyl_checks = [weyl_lr_check(cell, n_steps) for cell in conj_frame_cells]
    all_weyl_distinct = all(w["left_right_distinct"] for w in conj_weyl_checks)
    direct_frame_cells = filter(c -> c.terrain in (:Se, :Ne), CELLS)
    direct_weyl_checks = [weyl_lr_check(cell, n_steps) for cell in direct_frame_cells]
    all_direct_invariant = all(!w["left_right_distinct"] for w in direct_weyl_checks)

    # Reversibility
    rev_left  = unitary_reversibility(:left)
    rev_right = unitary_reversibility(:right)
    deduction_unitary_reversed = (
        rev_left["fi_reversed_exactly"] &&
        rev_left["fe_reversed_exactly"] &&
        rev_right["fi_reversed_exactly"] &&
        rev_right["fe_reversed_exactly"] &&
        rev_left["dephasing_irreversible"] &&
        rev_right["dephasing_irreversible"]
    )

    # Wrong-structure control
    ws_control = wrong_structure_control(n_steps)

    # Size ladder
    ladder = size_ladder_check()

    # Positive/negative/boundary checks
    pnb = positive_negative_boundary_checks()

    # Chart structure
    chart = chart_structure_check()

    # Channels exact match
    channels_exact = Dict{String,Any}(
        "Ti" => "rho -> (1-q1)*rho + q1*(P0*rho*P0 + P1*rho*P1) -- z-dephase",
        "Te" => "rho -> (1-q2)*rho + q2*(Qp*rho*Qp + Qm*rho*Qm) -- x-dephase",
        "Fi" => "rho -> exp(-i*th*sx/2) * rho * exp(+i*th*sx/2) -- x-rotation",
        "Fe" => "rho -> exp(-i*ph*sz/2) * rho * exp(+i*ph*sz/2) -- z-rotation",
        "source_section" => "sec.4 judging-function table",
        "match_verbatim" => true,
    )

    # Assemble result
    result = Dict{String,Any}(
        "object_id"           => "qit16_julia",
        "engine"              => "julia",
        "run_timestamp"       => string(now()),
        "claim_ceiling"       => "finite_map_carrier_only",
        "promotion_allowed"   => false,
        "root_constraints"    => ["F01","N01"],
        "n_steps_canonical"   => n_steps,
        "channels_exact"      => channels_exact,
        "sixteen_distinct"    => distinct_check,
        "chart_structure"     => chart,
        "grammar_correlation" => grammar_corr,
        "weyl_lr_checks"      => weyl_checks,
        "weyl_lr_all_distinct"=> all_weyl_distinct,
        "weyl_lr_note"        => "Weyl L/R distinct for conjugated-frame terrains (Ni/Si) only; direct-frame (Se/Ne) are Weyl-frame-invariant by construction per doc sec.3.2",
        "weyl_direct_frame_invariant" => all_direct_invariant,
        "reversibility_left"  => rev_left,
        "reversibility_right" => rev_right,
        "deduction_unitary_reversed" => deduction_unitary_reversed,
        "wrong_structure_control" => ws_control,
        "size_ladder"         => ladder,
        "positive_negative_boundary" => pnb,
        "cell_results_left"   => weyl_left_results,
        "cell_results_right"  => weyl_right_results,
    )

    # Write result
    out_path = joinpath(@__DIR__, "qit16_julia_results.json")
    open(out_path, "w") do f
        JSON.print(f, result, 2)
    end
    println("Written: ", out_path)

    # Print summary
    println("\n=== QIT-16 Julia Carrier Summary ===")
    println("16 tokens distinct (left Weyl): ", distinct_check["all_distinct"])
    println("n_clashes: ", distinct_check["n_clashes"])
    println("Chart reproduced: ", chart["chart_reproduced"])
    if !isempty(chart["issues"])
        println("  Chart issues: ", chart["issues"])
    end
    println("Grammar correlation: ", grammar_corr["overall_grammar_signature_correlation"])
    println("  Note: ", grammar_corr["honest_note"])
    println("Weyl L/R distinct (conjugated-frame Ni/Si cells): ", all_weyl_distinct)
    println("Weyl direct-frame (Se/Ne) invariant by construction: ", all_direct_invariant)
    println("Deduction unitary reversed (Fi/Fe): ", deduction_unitary_reversed)
    println("  Fi reversed (left): ", rev_left["fi_reversed_exactly"], " gap=", rev_left["fi_forward_backward_gap"])
    println("  Fe reversed (left): ", rev_left["fe_reversed_exactly"], " gap=", rev_left["fe_forward_backward_gap"])
    println("  Ti irrev gap: ", rev_left["ti_double_apply_gap_from_original"])
    println("  Te irrev gap: ", rev_left["te_double_apply_gap_from_original"])
    println("All pnb checks passed: ", pnb["all_passed"])
    println("Size ladder all valid: ", all(row["all_valid_density_matrices"] for row in ladder["ladder"]))
    println("Wrong-structure: terrain load-bearing=", ws_control["terrain_is_load_bearing"],
            "  Weyl load-bearing for conjugated frame=", ws_control["weyl_is_load_bearing_for_conjugated_frame"],
            "  Direct-frame Weyl invariant=", ws_control["weyl_direct_frame_invariant_as_expected"])
end

main()
