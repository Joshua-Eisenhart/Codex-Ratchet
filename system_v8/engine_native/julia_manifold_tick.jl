#!/usr/bin/env julia
# ============================================================================
# julia_manifold_tick.jl -- engine-native manifold tick loop, Julia OWNS the
# semantics (lane: julia_manifold, AUTHORITATIVE).
#
# This is NOT a numpy mirror. Conventions are declared here and owned here:
#   * inner joint ordering: QuantumOptics tensor ordering, subsystem-1 (L
#     sheet) index fastest; vec(.) is Julia column-major vec of the QO .data
#     matrix -- no foreign permutation step exists in this file.
#   * link phase: Arg<psi_k|psi_{k+1}> via Julia dot (conjugates first arg);
#     loop holonomy = sum of link phases around the closed chi-loop; flux =
#     relative holonomy across two leaves (leaf-1 at fixed eta1, leaf-2 at
#     state-pulled eta2).
#   * GKSL: QuantumOptics timeevolution.master (adaptive ODE, reltol 1e-10,
#     abstol 1e-12) evolves the joint 2-sheet state; no hand-rolled RK4.
#   * drive: Hartley dC in bits from BigInt admissible-set counts (words
#     with no "11" factor; transfer recursion c(n)=c(n-1)+c(n-2)). Counts
#     exceed typemax(Int64) from tick 0 -- BigInt is load-bearing, and the
#     recursion is cross-checked against brute-force enumeration.
#   * nesting: outer 2-level ancilla coupled to the joint state; the
#     ancilla-excited sector is Schur-eliminated on the 64x64 Liouvillian
#     (LinearAlgebra: block partition, L_eff = L_PP - L_PQ L_QQ^{-1} L_QP,
#     matrix exponential for the per-tick effective propagator).
#   * independent cut check: ITensorMPS -- purify rho_LR, build an MPS on
#     sites [L(2), R(2), A(4)], bond-cut SVD spectra give S_L and S_LR
#     independently of QuantumOptics ptrace/entropy_vn.
#
# Entropy-law checks per generator family (isolated law runs, rungB GKSL
# conventions): Spohn positivity for the unital depolarizing family
# (relative entropy to I/4 monotone down), damping monotone via relative
# entropy to the Liouvillian-null-space fixed point, unitary dS = 0 exact.
# Controls: nesting decouple (downstream must move > 1e-6), drive freeze
# (must damp), flux flatten (must kill).
#
# Claim ceiling: scratch_diagnostic; promotion_allowed = false.
# Refuses to reuse an existing output directory.
# ============================================================================

using QuantumOptics
using ITensors, ITensorMPS
using LinearAlgebra
using JSON

const HERE = dirname(abspath(@__FILE__))
const OUT = joinpath(HERE, "results", "julia_manifold")

# ---- parameters (owned here) ----------------------------------------------
const N_TICKS = 30
const TICK_DT = 0.4
const N_LOOP = 200
const OMEGA = 1.3
const ALPHA = 0.7
const J_XY = 0.35
const GAMMA_BASE = 0.6
const ETA1 = 0.2
const LEN0 = 96                    # initial admissible-word length
const STEPS = [(5, 8, 13)[mod(t, 3) + 1] for t in 0:(N_TICKS - 1)]
const OUTER = (Delta = 1.2, g = 0.5, kappa = 0.8, gph = 0.1)

const I2m = Matrix{ComplexF64}(I, 2, 2)
const I4m = Matrix{ComplexF64}(I, 4, 4)
const SXm = ComplexF64[0 1; 1 0]
const SYm = ComplexF64[0 -1im; 1im 0]
const SZm = ComplexF64[1 0; 0 -1]
const SMm = ComplexF64[0 1; 0 0]

const b1 = NLevelBasis(2)
const b2 = b1 ⊗ b1
op1(m) = Operator(b1, Matrix{ComplexF64}(m))
op2(mL, mR) = tensor(op1(mL), op1(mR))    # subsystem 1 = L sheet (fastest)
const OpT = typeof(op2(SXm, SXm))

# ---- drive: Hartley dC from BigInt admissible-set counts ------------------
# admissible set A_n = binary words of length n with no "11" factor;
# |A_n| satisfies c(n) = c(n-1) + c(n-2), c(1)=2, c(2)=3.
function no11_counts(nmax::Int)
    c = Vector{BigInt}(undef, nmax)
    c[1] = big(2); c[2] = big(3)
    for n in 3:nmax
        c[n] = c[n - 1] + c[n - 2]
    end
    return c
end

function no11_bruteforce(n::Int)   # independent enumeration, n <= 24
    cnt = big(0)
    for x in 0:(2^n - 1)
        (x & (x >> 1)) == 0 && (cnt += 1)
    end
    return cnt
end

hartley_bits(n::BigInt) = Float64(log2(BigFloat(n)))

# ---- flux: link phases / relative holonomy across two leaves --------------
spinor(eta, phi, chi) = ComplexF64[exp(1im * phi) * cos(eta),
                                   exp(1im * chi) * sin(eta)]

chi_loop(eta; phi0 = 0.3) =
    [spinor(eta, phi0, 2pi * k / N_LOOP) for k in 0:(N_LOOP - 1)]

function loop_holonomy(points)     # sum of link phases Arg<psi_k|psi_{k+1}>
    tot = 0.0
    n = length(points)
    for k in 1:n
        tot += angle(dot(points[k], points[mod1(k + 1, n)]))
    end
    return tot
end

relative_flux(eta_a, eta_b) =
    loop_holonomy(chi_loop(eta_a)) - loop_holonomy(chi_loop(eta_b))

# ---- joint 2-sheet generator (rungB conventions: right sheet = conj rep) --
function build_joint_h()
    nx, nz = sin(ALPHA), cos(ALPHA)
    H_L = 0.5 * OMEGA * (nx * SXm + nz * SZm)
    return (op2(H_L, I2m) + op2(I2m, -H_L)
            + J_XY * (op2(SXm, SXm) + op2(SYm, SYm)))
end

function bank_jumps(stage::Int, gamma::Float64)
    gamma <= 0.0 && return OpT[]
    if stage == 0        # depolarizing (unital; fixed point I/4)
        return vcat([sqrt(gamma / 4) * op2(s, I2m) for s in (SXm, SYm, SZm)],
                    [sqrt(gamma / 4) * op2(I2m, conj.(s)) for s in (SXm, SYm, SZm)])
    elseif stage == 1    # dephasing
        return [sqrt(gamma) * op2(SZm, I2m), sqrt(gamma) * op2(I2m, conj.(SZm))]
    end                  # amplitude damping
    return [sqrt(gamma) * op2(SMm, I2m), sqrt(gamma) * op2(I2m, conj.(SMm))]
end

# real GKSL solver: QuantumOptics timeevolution.master, adaptive, tight tol
function master_tick(rho::OpT, H::OpT, Ls::Vector{OpT})
    _, rhot = timeevolution.master([0.0, TICK_DT], rho, H, Ls;
                                   reltol = 1e-10, abstol = 1e-12)
    return rhot[end]
end

# ---- entropies / distances ------------------------------------------------
clip_op(rho) = begin
    R = Matrix(rho.data); R = 0.5 * (R + R')
    F = eigen(Hermitian(R)); w = max.(F.values, 0.0)
    R2 = F.vectors * Diagonal(w) * F.vectors'
    Operator(rho.basis_l, rho.basis_r, R2 / real(tr(R2)))
end

ent_bits(rho) = real(QuantumOptics.entropy_vn(clip_op(rho))) / log(2)

function relent_bits(rho, sig)   # D(rho || sig) in bits
    Fr = eigen(Hermitian(Matrix(rho.data)))
    Fs = eigen(Hermitian(Matrix(sig.data)))
    lr = [x > 1e-14 ? log(x) : 0.0 for x in Fr.values]
    ls = Fs.vectors * Diagonal(log.(max.(Fs.values, 1e-300))) * Fs.vectors'
    trho_logrho = sum(max(x, 0.0) * l for (x, l) in zip(Fr.values, lr))
    R = Matrix(rho.data)
    return (trho_logrho - real(tr(R * ls))) / log(2)
end

tracedist(a, b) =
    0.5 * sum(abs, eigvals(Hermitian(Matrix(a.data) - Matrix(b.data))))

function cut_readouts(rho)
    S_L = ent_bits(ptrace(rho, 2))        # trace out subsystem 2 -> L kept
    S_R = ent_bits(ptrace(rho, 1))
    S_LR = ent_bits(rho)
    return (S_L = S_L, S_R = S_R, S_LR = S_LR, I = S_L + S_R - S_LR)
end

# ---- GKSL Liouvillian matrix (column-stacking vec convention) -------------
# vec(H rho) = (I (x) H) vec(rho); vec(K rho K') = (conj K (x) K) vec(rho)
function liouvillian_matrix(H::Matrix{ComplexF64}, Ks::Vector{Matrix{ComplexF64}})
    d = size(H, 1)
    Id = Matrix{ComplexF64}(I, d, d)
    L = -1im * (kron(Id, H) - kron(transpose(H), Id))
    for K in Ks
        KdK = K' * K
        L += kron(conj.(K), K) - 0.5 * kron(Id, KdK) - 0.5 * kron(transpose(KdK), Id)
    end
    return L
end

# ---- nesting: outer 2-level ancilla, Schur-eliminated ---------------------
# full space = inner(4, QO joint order, fastest) (x) ancilla(2, slow):
# full matrices are kron(A_anc, B_inner).
function build_outer_schur(; g_coupling = OUTER.g)
    Pg = ComplexF64[1 0; 0 0]; Pe = ComplexF64[0 0; 0 1]
    sm_a = ComplexF64[0 1; 0 0]            # |g><e|
    sp_a = ComplexF64[0 0; 1 0]            # |e><g|
    E14 = zeros(ComplexF64, 4, 4); E14[1, 4] = 1.0   # |n=0><n=3| inner
    H = (OUTER.Delta * kron(Pe, I4m)
         + g_coupling * (kron(sp_a, E14) + kron(sm_a, E14')))
    Ks = [sqrt(OUTER.kappa) * kron(sm_a, I4m),
          sqrt(OUTER.gph) * kron(Pe - Pg, I4m)]
    L = liouvillian_matrix(H, Ks)                    # 64 x 64
    # P sector: both ancilla indices in ground; ordered so the P-subvector
    # IS the column-major vec of the inner 4x4 matrix.
    P = [n1 + 8 * n2 + 1 for n2 in 0:3 for n1 in 0:3]
    Q = [n for n in 1:64 if !(n in P)]
    L_PP = L[P, P]; L_PQ = L[P, Q]; L_QP = L[Q, P]; L_QQ = L[Q, Q]
    L_eff = L_PP - L_PQ * (L_QQ \ L_QP)              # Schur complement
    M_tick = exp(TICK_DT * L_eff)                    # LinearAlgebra expm
    tr_row = vec(I4m)'                               # trace functional
    tp_residual = maximum(abs.(tr_row * L_eff))
    return M_tick, L_eff, tp_residual
end

function apply_outer(rho::OpT, M_tick::Matrix{ComplexF64})
    v = M_tick * vec(Matrix(rho.data))
    R = reshape(v, 4, 4); R = 0.5 * (R + R')
    F = eigen(Hermitian(R))
    clipmag = max(0.0, -minimum(F.values))
    w = max.(F.values, 0.0)
    R2 = F.vectors * Diagonal(w) * F.vectors'
    return Operator(b2, R2 / real(tr(R2))), clipmag
end

# ---- ITensorMPS independent cut check -------------------------------------
# purify rho_LR -> |Psi> on [L(2), R(2), A(4)]; bond-1 cut spectrum = spec
# of rho_L, bond-2 cut spectrum = spec of rho_LR. Entropies in bits.
function mps_cut_entropies(rho::OpT)
    R = Matrix(clip_op(rho).data)
    F = eigen(Hermitian(R))
    Psi = zeros(ComplexF64, 2, 2, 4)
    for a in 1:4
        lam = max(F.values[a], 0.0)
        Psi[:, :, a] = sqrt(lam) * reshape(F.vectors[:, a], 2, 2)  # iL fastest
    end
    sL = Index(2, "L"); sR = Index(2, "R"); sA = Index(4, "A")
    M = MPS(ITensor(Psi, sL, sR, sA), [sL, sR, sA]; cutoff = 1e-15)
    ent_from_spec(p) = -sum(x > 1e-15 ? x * log2(x) : 0.0 for x in p)
    orthogonalize!(M, 1)
    _, S1, _ = ITensors.svd(M[1], (sL,))
    p1 = [real(S1[i, i]^2) for i in 1:ITensors.dim(S1, 1)]
    orthogonalize!(M, 2)
    _, S2, _ = ITensors.svd(M[2], (linkind(M, 1), sR))
    p2 = [real(S2[i, i]^2) for i in 1:ITensors.dim(S2, 1)]
    return ent_from_spec(p1 / sum(p1)), ent_from_spec(p2 / sum(p2))
end

# ---- the manifold tick loop -----------------------------------------------
function run_ticks(; freeze_drive::Bool = false, decouple_outer::Bool = false)
    counts = no11_counts(LEN0 + sum(STEPS))
    H = build_joint_h()
    M_tick, _, tp_res = build_outer_schur(
        g_coupling = decouple_outer ? 0.0 : OUTER.g)
    rho0_L = 0.5 * (I2m + 0.5 * SXm + 0.3 * SYm - 0.4 * SZm)
    rho = op2(rho0_L, conj.(rho0_L))
    ser = Dict{String, Vector{Float64}}(k => Float64[] for k in
        ["dC", "gamma", "flux", "flux_flat", "S_L", "S_R", "S_LR", "I",
         "min_eig_post_master", "trace_err_post_master", "outer_clip"])
    states = OpT[]
    len = LEN0
    for t in 0:(N_TICKS - 1)
        len_new = len + STEPS[t + 1]
        dC = freeze_drive ? 0.0 :
             hartley_bits(counts[len_new]) - hartley_bits(counts[len])
        len = len_new
        gamma = GAMMA_BASE * dC / 10.0
        stage = div(t, 10)
        rho = master_tick(rho, H, bank_jumps(stage, gamma))
        wmin = minimum(eigvals(Hermitian(Matrix(rho.data))))
        tre = abs(real(tr(rho)) - 1.0)
        p1L = real(Matrix(ptrace(rho, 2).data)[2, 2])
        eta2 = 0.3 + 0.4 * clamp(p1L, 0.0, 1.0)
        flux = relative_flux(ETA1, eta2)          # two leaves: eta1 vs eta2
        flux_flat = relative_flux(ETA1, ETA1)     # flatten control leaf
        rho, clipmag = apply_outer(rho, M_tick)
        cr = cut_readouts(rho)
        push!(ser["dC"], dC); push!(ser["gamma"], gamma)
        push!(ser["flux"], flux); push!(ser["flux_flat"], flux_flat)
        push!(ser["S_L"], cr.S_L); push!(ser["S_R"], cr.S_R)
        push!(ser["S_LR"], cr.S_LR); push!(ser["I"], cr.I)
        push!(ser["min_eig_post_master"], wmin)
        push!(ser["trace_err_post_master"], tre)
        push!(ser["outer_clip"], clipmag)
        push!(states, rho)
    end
    return ser, states, counts, tp_res
end

# ---- isolated entropy-law runs (per generator family) ---------------------
function law_runs()
    H = build_joint_h()
    rho0_L = 0.5 * (I2m + 0.5 * SXm + 0.3 * SYm - 0.4 * SZm)
    rho0 = op2(rho0_L, conj.(rho0_L))
    gam = 0.5
    out = Dict{String, Any}()

    # family U: unitary -- dS = 0 exact
    rho = rho0; S0 = ent_bits(rho); drift = 0.0
    for _ in 1:N_TICKS
        rho = master_tick(rho, H, OpT[])
        drift = max(drift, abs(ent_bits(rho) - S0))
    end
    out["U_max_dS"] = drift

    # family D: depolarizing (unital) -- Spohn: D(rho || I/4) monotone down
    mix = Operator(b2, I4m / 4)
    rho = rho0; Ls = bank_jumps(0, gam)
    Dser = [relent_bits(rho, mix)]
    for _ in 1:N_TICKS
        rho = master_tick(rho, H, Ls)
        push!(Dser, relent_bits(clip_op(rho), mix))
    end
    out["D_relent_series"] = Dser
    out["D_max_step_increase"] = maximum(diff(Dser))
    out["D_total_drop"] = Dser[1] - Dser[end]

    # family A: amplitude damping -- D(rho || rho_ss) monotone down,
    # rho_ss from the Liouvillian null space (LinearAlgebra, load-bearing)
    Ls = bank_jumps(2, gam)
    Lmat = liouvillian_matrix(Matrix(H.data),
                              [Matrix(Lop.data) for Lop in Ls])
    F = eigen(Lmat)
    null_idx = findall(x -> abs(x) < 1e-8, F.values)
    out["A_nullspace_dim"] = length(null_idx)
    v = F.vectors[:, null_idx[1]]
    Rss = reshape(v, 4, 4); Rss = 0.5 * (Rss + Rss')
    Rss = Rss / real(tr(Rss))
    Fss = eigen(Hermitian(Rss))
    Rss = Fss.vectors * Diagonal(max.(Fss.values, 0.0)) * Fss.vectors'
    rho_ss = Operator(b2, Rss / real(tr(Rss)))
    out["A_rho_ss_min_eig"] = minimum(eigvals(Hermitian(Rss)))
    rho = rho0
    Aser = [relent_bits(rho, rho_ss)]
    for _ in 1:N_TICKS
        rho = master_tick(rho, H, Ls)
        push!(Aser, relent_bits(clip_op(rho), rho_ss))
    end
    out["A_relent_series"] = Aser
    out["A_max_step_increase"] = maximum(diff(Aser))
    out["A_total_drop"] = Aser[1] - Aser[end]
    return out
end

# ---- main ------------------------------------------------------------------
function main()
    if isdir(OUT)
        println("refusing to reuse output dir: ", OUT)
        exit(2)
    end
    mkpath(OUT)

    # drive self-check: BigInt recursion vs brute-force enumeration
    cchk = no11_counts(24)
    brute_ok = all(cchk[n] == no11_bruteforce(n) for n in (12, 20))

    base, states, counts, tp_res = run_ticks()
    frz, frz_states, _, _ = run_ticks(freeze_drive = true)
    dec, _, _, _ = run_ticks(decouple_outer = true)
    laws = law_runs()

    # MPS independent cut check at mid and final base states
    mps_dL = Float64[]; mps_dLR = Float64[]
    for tk in (15, 30)
        sL_m, sLR_m = mps_cut_entropies(states[tk])
        cr = cut_readouts(states[tk])
        push!(mps_dL, abs(sL_m - cr.S_L))
        push!(mps_dLR, abs(sLR_m - cr.S_LR))
    end

    # drive-freeze damping. With gamma frozen to 0 every tick applies the
    # SAME positive trace-preserving map (unitary master + outer Schur map),
    # so the data-processing inequality predicts the successive-state trace
    # distance d_t = T(rho_t, rho_{t+1}) is monotone non-increasing, and
    # actual damping shows as strict net contraction (a unitary-only map
    # would hold the ratio at 1.0 and fail). The entropy-step metric is
    # recorded too: it oscillates (nonlinear readout of a rotating state)
    # and is NOT the gate -- kept as an honest diagnostic.
    frz_d = [tracedist(frz_states[t], frz_states[t + 1])
             for t in 1:(N_TICKS - 1)]
    frz_d_max_step_increase = maximum(diff(frz_d))
    frz_contraction_ratio = frz_d[end] / frz_d[1]
    freeze_step = [maximum(abs(frz[k][t + 1] - frz[k][t])
                           for k in ("S_L", "S_R", "S_LR"))
                   for t in 1:(N_TICKS - 1)]
    frz_first = maximum(freeze_step[1:5])
    frz_last = maximum(freeze_step[end - 4:end])

    diff_freeze = maximum(abs.(base["S_LR"] .- frz["S_LR"]))
    diff_dec = maximum(abs.(base["S_LR"] .- dec["S_LR"]))

    max_count = counts[LEN0 + sum(STEPS)]

    checks = Dict(
        # drive
        "drive_bigint_counts_exceed_int64" => max_count > big(typemax(Int64)),
        "drive_transfer_matches_bruteforce" => brute_ok,
        "drive_dC_positive_all_ticks" => all(x -> x > 0, base["dC"]),
        # entropy laws per generator family
        "lawU_unitary_dS_zero_exact" => laws["U_max_dS"] < 1e-8,
        "lawD_spohn_relent_monotone_down" => laws["D_max_step_increase"] < 1e-9,
        "lawD_drop_nontrivial" => laws["D_total_drop"] > 1e-3,
        "lawA_fixed_point_unique" => laws["A_nullspace_dim"] == 1,
        "lawA_damping_relent_monotone_down" => laws["A_max_step_increase"] < 1e-9,
        "lawA_drop_nontrivial" => laws["A_total_drop"] > 1e-3,
        # base run integrity
        "base_series_complete_30" => all(length(v) == N_TICKS for v in values(base)),
        "base_states_physical_post_master" =>
            (minimum(base["min_eig_post_master"]) > -1e-9 &&
             maximum(base["trace_err_post_master"]) < 1e-9),
        "outer_schur_trace_preserving" => tp_res < 1e-9,
        "outer_clip_small" => maximum(base["outer_clip"]) < 1e-6,
        # nesting control
        "nesting_decouple_changes_downstream_gt_1e-6" => diff_dec > 1e-6,
        # drive-freeze control
        "drive_freeze_gamma_all_zero" => all(x -> x == 0.0, frz["gamma"]),
        "drive_freeze_differs_from_base_gt_1e-6" => diff_freeze > 1e-6,
        "drive_freeze_damps_tracedist_monotone" => frz_d_max_step_increase < 1e-10,
        "drive_freeze_damps_net_contraction" => frz_contraction_ratio < 0.9,
        # flux
        "flux_nontrivial_in_base" => maximum(abs.(base["flux"])) > 1e-6 &&
            (maximum(base["flux"]) - minimum(base["flux"])) > 1e-6,
        "flux_flatten_control_kills" => maximum(abs.(base["flux_flat"])) < 1e-12,
        # independent MPS cut check
        "mps_cut_S_L_matches_lt_1e-8" => maximum(mps_dL) < 1e-8,
        "mps_cut_S_LR_matches_lt_1e-8" => maximum(mps_dLR) < 1e-8,
    )
    all_pass = all(values(checks))

    findings = [
        string("Julia owns the semantics: QO tensor ordering (L fastest) + ",
               "column-major vec used end-to-end; no numpy permutation or ",
               "cross-run parity read anywhere in this file"),
        string("QuantumOptics load-bearing: joint state, stage generators, ",
               "timeevolution.master (reltol 1e-10) per tick, ptrace, ",
               "entropy_vn -- removing it removes the dynamics"),
        string("BigInt load-bearing: admissible-set counts reach ",
               length(string(max_count)), " decimal digits (> Int64 by ",
               "construction, checked); Hartley dC computed via BigFloat log2"),
        string("LinearAlgebra owns the nesting step per the card: 64x64 ",
               "Liouvillian, Schur complement onto the ancilla-ground ",
               "sector, matrix exponential; trace-functional residual on ",
               "L_eff = ", string(tp_res)),
        string("ITensorMPS independent cut check: purified MPS bond ",
               "spectra vs QO ptrace entropies, max diffs S_L=",
               string(maximum(mps_dL)), " S_LR=", string(maximum(mps_dLR))),
        string("flux-flatten is a readout-level control (leaf-2 parameter ",
               "pinned to eta1); the nesting and drive controls are ",
               "dynamics-level controls"),
        string("honest history: a first run gated freeze-damping on the ",
               "entropy-step metric and FAILED (entropy oscillates as the ",
               "frozen state rotates through the outer channel; receipt ",
               "kept in results/julia_manifold_run1_freeze_metric_negative). ",
               "The gate now uses the successive-state trace distance, the ",
               "principled contraction observable for iterating a fixed ",
               "positive TP map; the entropy-step numbers remain recorded ",
               "as diagnostics"),
        string("outer effective map hermitized + eigenvalue-clipped + ",
               "renormalized each tick; max clip magnitude = ",
               string(maximum(base["outer_clip"]))),
    ]

    receipt = Dict(
        "schema" => "ratchet.v8.engine-native.julia-manifold-tick.v0",
        "lane" => "julia_manifold",
        "engine" => "julia",
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "packages" => Dict(
            "QuantumOptics" => "load_bearing: state/generators/master/ptrace/entropy_vn",
            "ITensors+ITensorMPS" => "load_bearing: independent MPS bond-cut entropy gate",
            "BigInt(Base)" => "load_bearing: Hartley drive counts beyond Int64",
            "LinearAlgebra" => "supportive-by-card: Schur elimination + expm on the Liouvillian matrix",
        ),
        "conventions" => Dict(
            "link_phase" => "Arg<psi_k|psi_{k+1}>, summed around closed loop",
            "flux" => "relative holonomy leaf(eta1) - leaf(eta2)",
            "vec" => "column-major vec of QO-ordered 4x4 (L index fastest)",
            "gksl" => "timeevolution.master, reltol 1e-10, abstol 1e-12",
        ),
        "checks" => checks,
        "data" => Dict(
            "base_series" => base,
            "freeze_S_LR" => frz["S_LR"],
            "decouple_S_LR" => dec["S_LR"],
            "freeze_successive_tracedist" => frz_d,
            "freeze_tracedist_max_step_increase" => frz_d_max_step_increase,
            "freeze_contraction_ratio" => frz_contraction_ratio,
            "freeze_entropy_step_first5_max_DIAGNOSTIC_ONLY" => frz_first,
            "freeze_entropy_step_last5_max_DIAGNOSTIC_ONLY" => frz_last,
            "law_runs" => laws,
            "mps_cut_diffs" => Dict("S_L" => mps_dL, "S_LR" => mps_dLR),
            "outer_schur_tp_residual" => tp_res,
            "drive_final_count_digits" => length(string(max_count)),
            "diff_base_vs_freeze_S_LR" => diff_freeze,
            "diff_base_vs_decouple_S_LR" => diff_dec,
        ),
        "findings" => findings,
        "all_pass" => all_pass,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => string("engine-native manifold tick loop, Julia-",
                                  "owned semantics; scratch_diagnostic; no ",
                                  "physics claim beyond the executed checks"),
    )
    open(joinpath(OUT, "receipt.json"), "w") do io
        JSON.print(io, receipt, 2)
    end
    println(JSON.json(Dict("lane" => "julia",
                           "file" => abspath(@__FILE__),
                           "all_pass" => all_pass,
                           "checks" => checks,
                           "findings" => findings), 2))
    exit(all_pass ? 0 : 1)
end

main()
