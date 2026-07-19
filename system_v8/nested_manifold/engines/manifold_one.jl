#!/usr/bin/env julia
# Nested-manifold engine leg -- Julia replication of manifold_one.py.
#
# Replicates the rung-ONE tick loop (base run only: grow / propagate /
# flux / nest / lock) and compares the 30-tick entropy series to the
# committed numpy receipt (results/manifold_one/receipt.json).
#
# Package choice (recorded honestly): QuantumOptics.jl IS installed and IS
# used load-bearing -- the joint state rho_LR, the Hamiltonian, the jump
# operators, the GKSL right-hand side, ptrace, and entropy_vn all run
# through QuantumOptics operator algebra. LinearAlgebra is used only where
# algorithm parity demands the exact same numerics as the reference: the
# 6-level outer-layer Liouvillian, its Schur complement, the RK4-polynomial
# one-tick propagator, and the eigenvalue clip.
#
# Convention note (declared, load-bearing): QuantumOptics stores
# tensor(A,B).data as kron(B.data, A.data) (subsystem-1 index fastest),
# while the numpy reference uses kron(L, R) (subsystem-2 index fastest).
# The outer 6-level model addresses inner levels {0..3} in the NUMPY
# ordering, so the state is permuted into numpy ordering before the Schur
# step and permuted back after. Getting this permutation wrong blows the
# 1e-8 gate by orders of magnitude -- the gate can FAIL.
#
# Contract: max abs elementwise diff over S_L, S_R, S_LR, I, I_c,
# negativity, Phi0, flux < 1e-8 vs the numpy receipt. Float64/ComplexF64.
#
# Engine-estate rule: this process loads ONLY the Julia stack and exits.
# Claim ceiling: engine-parity probe; scratch_diagnostic;
# promotion_allowed = false; no new physics claim.

using QuantumOptics
using LinearAlgebra
using JSON

const HERE = dirname(abspath(@__FILE__))
const NUMPY_RECEIPT = joinpath(HERE, "..", "results", "manifold_one", "receipt.json")
const OUT = joinpath(HERE, "..", "results", "manifold_one_julia")

# ---- constants traced to manifold_one.py (must match exactly) ----------
const N_TICKS = 30
const TICK_DT = 0.4
const NSUB = 8
const NSUB_OUT = 8
const N_LOOP = 200
const OMEGA = 1.3
const ALPHA = 0.7
const J_XY = 0.35
const GAMMA_BASE = 0.6
const ETA1 = 0.2
const A_SCHED = [3 + ((t + 1) % 3) for t in 0:(N_TICKS - 1)]  # 4,5,3,...
const OUTER = Dict("Delta4" => 1.0, "Delta5" => 1.5, "gph" => 0.1,
                   "g" => 0.5, "g2" => 0.35, "k_out" => 0.8)

const I2m = Matrix{ComplexF64}(I, 2, 2)
const SXm = ComplexF64[0 1; 1 0]
const SYm = ComplexF64[0 -1im; 1im 0]
const SZm = ComplexF64[1 0; 0 -1]
const SMm = ComplexF64[0 1; 0 0]

const b1 = NLevelBasis(2)
const b2 = b1 ⊗ b1
op1(m) = Operator(b1, Matrix{ComplexF64}(m))
op2(mL, mR) = tensor(op1(mL), op1(mR))   # subsystem 1 = L sheet

# numpy index n = 2 iL + iR + 1  <->  QO index q = 2 iR + iL + 1
const PERM = [1, 3, 2, 4]                # PERM[n] = q

# ---- rung-A machinery ---------------------------------------------------
spinor(eta, phi, chi) = ComplexF64[exp(1im * phi) * cos(eta),
                                   exp(1im * chi) * sin(eta)]

function chi_loop(eta; phi0 = 0.3)
    return [spinor(eta, phi0, 2pi * k / N_LOOP) for k in 0:(N_LOOP - 1)]
end

function loop_holonomy(points)
    tot = 0.0
    n = length(points)
    for k in 1:n
        tot += angle(dot(points[k], points[mod1(k + 1, n)]))
    end
    return tot
end

# ---- rung-C machinery (QuantumOptics load-bearing) ---------------------
ent_bits(rho) = real(entropy_vn(rho)) / log(2)

function to_numpy_order(rho)             # QO joint operator -> 4x4 numpy-order
    D = Matrix(rho.data)
    return [D[PERM[n1], PERM[n2]] for n1 in 1:4, n2 in 1:4]
end

function from_numpy_order(R)             # 4x4 numpy-order -> QO joint operator
    D = zeros(ComplexF64, 4, 4)
    for n1 in 1:4, n2 in 1:4
        D[PERM[n1], PERM[n2]] = R[n1, n2]
    end
    return Operator(b2, D)
end

function negativity_np(R)                # on the numpy-order matrix
    PT = zeros(ComplexF64, 4, 4)
    for iL in 0:1, iR in 0:1, jL in 0:1, jR in 0:1
        PT[2iL + jR + 1, 2jL + iR + 1] = R[2iL + iR + 1, 2jL + jR + 1]
    end
    w = eigvals(Hermitian(0.5 * (PT + PT')))
    return -sum(x for x in w if x < 0; init = 0.0)
end

function cut_readouts(rho)
    S_L = ent_bits(ptrace(rho, 2))       # trace out subsystem 2 -> L kept
    S_R = ent_bits(ptrace(rho, 1))
    S_LR = ent_bits(rho)
    Ic_LR = -(S_LR - S_R)
    Ic_RL = -(S_LR - S_L)
    return Dict("S_L" => S_L, "S_R" => S_R, "S_LR" => S_LR,
                "I" => S_L + S_R - S_LR, "I_c" => Ic_LR,
                "negativity" => negativity_np(to_numpy_order(rho)),
                "Phi0" => 0.5 * Ic_LR + 0.5 * Ic_RL)
end

# ---- rung-B machinery (QuantumOptics operators) ------------------------
function build_joint_h()
    nx, nz = sin(ALPHA), cos(ALPHA)
    H_L = 0.5 * OMEGA * (nx * SXm + nz * SZm)
    return (op2(H_L, I2m) + op2(I2m, -H_L)
            + J_XY * (op2(SXm, SXm) + op2(SYm, SYm)))
end

function bank_jumps(stage, gamma)
    gamma <= 0.0 && return []
    if stage == 0
        return vcat([sqrt(gamma / 4) * op2(s, I2m) for s in (SXm, SYm, SZm)],
                    [sqrt(gamma / 4) * op2(I2m, conj.(s)) for s in (SXm, SYm, SZm)])
    elseif stage == 1
        return [sqrt(gamma) * op2(SZm, I2m), sqrt(gamma) * op2(I2m, conj.(SZm))]
    end
    return [sqrt(gamma) * op2(SMm, I2m), sqrt(gamma) * op2(I2m, conj.(SMm))]
end

function gksl_rhs(rho, H, Ls)
    d = -1im * (H * rho - rho * H)
    for L in Ls
        Ld = dagger(L)
        d += L * rho * Ld - 0.5 * (Ld * L * rho + rho * Ld * L)
    end
    return d
end

function evolve_tick(rho, H, Ls)
    dt = TICK_DT / NSUB
    for _ in 1:NSUB
        k1 = gksl_rhs(rho, H, Ls)
        k2 = gksl_rhs(rho + 0.5 * dt * k1, H, Ls)
        k3 = gksl_rhs(rho + 0.5 * dt * k2, H, Ls)
        k4 = gksl_rhs(rho + dt * k3, H, Ls)
        rho = rho + (dt / 6.0) * (k1 + 2k2 + 2k3 + k4)
        rho = 0.5 * (rho + dagger(rho))
    end
    return rho
end

# ---- rung-D machinery (explicit LinearAlgebra for algorithm parity) ----
function op6(i, j)                       # 0-based indices as in the reference
    m = zeros(ComplexF64, 6, 6)
    m[i + 1, j + 1] = 1.0
    return m
end

function liouvillian6(H, jumps)
    Id = Matrix{ComplexF64}(I, 6, 6)
    L = -1im * (kron(Id, H) - kron(transpose(H), Id))
    for K in jumps
        KdK = K' * K
        L += kron(conj.(K), K) - 0.5 * kron(Id, KdK) - 0.5 * kron(transpose(KdK), Id)
    end
    return L
end

function build_outer_schur()
    c = OUTER
    H = (c["Delta4"] * op6(4, 4) + c["Delta5"] * op6(5, 5)
         + c["g"] * (op6(3, 4) + op6(4, 3))
         + c["g2"] * (op6(0, 5) + op6(5, 0)))
    jumps = [sqrt(c["k_out"]) * op6(1, 4),
             sqrt(c["k_out"]) * op6(2, 5),
             sqrt(c["gph"]) * (op6(4, 4) - op6(5, 5))]
    L = liouvillian6(H, jumps)
    P = [i + 6j + 1 for j in 0:3 for i in 0:3]     # i fastest, as reference
    Q = [n for n in 1:36 if !(n in P)]
    L_II = L[P, P]; L_IO = L[P, Q]; L_OI = L[Q, P]; L_OO = L[Q, Q]
    L_eff = L_II - L_IO * (L_OO \ L_OI)
    h = TICK_DT / NSUB_OUT
    A = h * L_eff
    P_step = (Matrix{ComplexF64}(I, 16, 16) + A + A * A / 2.0
              + A * A * A / 6.0 + A * A * A * A / 24.0)
    return P_step^NSUB_OUT
end

function apply_outer(rho, M_tick)
    R = to_numpy_order(rho)
    v = M_tick * vec(R)                  # Julia vec = column-stacking, as ref
    r = reshape(v, 4, 4)
    r = 0.5 * (r + r')
    F = eigen(Hermitian(r))
    w = max.(F.values, 0.0)
    r = F.vectors * Diagonal(w) * F.vectors'
    r = r / real(tr(r))
    return from_numpy_order(r)
end

# ---- the tick loop (base run; drive is exact shared scalar math) -------
function run()
    class_counts = [1, 1, 1, 0, 0]
    rho0_L = 0.5 * (I2m + 0.5 * SXm + 0.3 * SYm - 0.4 * SZm)
    rho = op2(rho0_L, conj.(rho0_L))
    M_tick = build_outer_schur()
    H = build_joint_h()
    keys_ = ["dC", "flux", "S_L", "S_R", "S_LR", "I", "I_c", "negativity", "Phi0"]
    series = Dict(k => Float64[] for k in keys_)
    for t in 0:(N_TICKS - 1)
        a = A_SCHED[t + 1]
        old_total = sum(class_counts)
        class_counts = [x <= a ? old_total - class_counts[x] : 0 for x in 1:5]
        dC = log(sum(class_counts)) - log(old_total)
        stage = div(t, 10)
        gamma = GAMMA_BASE * dC / log(4)
        rho = evolve_tick(rho, H, bank_jumps(stage, gamma))
        p1L = real(Matrix(ptrace(rho, 2).data)[2, 2])
        eta2 = 0.3 + 0.4 * clamp(p1L, 0.0, 1.0)
        flux = loop_holonomy(chi_loop(ETA1)) - loop_holonomy(chi_loop(eta2))
        rho = apply_outer(rho, M_tick)
        cr = cut_readouts(rho)
        push!(series["dC"], dC)
        push!(series["flux"], flux)
        for k in ["S_L", "S_R", "S_LR", "I", "I_c", "negativity", "Phi0"]
            push!(series[k], cr[k])
        end
    end
    return series
end

function main()
    if isdir(OUT)
        println("refusing to reuse output: ", OUT); exit(2)
    end
    if !isfile(NUMPY_RECEIPT)
        println("numpy receipt missing: ", NUMPY_RECEIPT); exit(2)
    end
    mkpath(OUT)
    ref = JSON.parsefile(NUMPY_RECEIPT)["data"]["series"]

    series = run()
    gate = 1e-8
    diffs = Dict{String,Float64}()
    for k in ["S_L", "S_R", "S_LR", "I", "I_c", "negativity", "Phi0", "flux", "dC"]
        diffs[k] = maximum(abs.(series[k] .- Float64.(ref[k])))
    end
    entropy_keys = ["S_L", "S_R", "S_LR", "I", "I_c", "Phi0"]
    checks = Dict(
        "float64" => eltype(series["S_L"]) == Float64,
        "quantumoptics_used" => true,   # set by construction; see findings
        "parity_entropy_series_lt_1e-8" => all(diffs[k] < gate for k in entropy_keys),
        "parity_negativity_lt_1e-8" => diffs["negativity"] < gate,
        "parity_flux_lt_1e-8" => diffs["flux"] < gate,
        "drive_scalar_identical" => diffs["dC"] == 0.0,
        "series_complete_30" => all(length(series[k]) == N_TICKS for k in keys(series)),
    )
    findings = [
        string("package choice: QuantumOptics.jl installed and used ",
               "load-bearing (state, H, jumps, GKSL rhs, ptrace, ",
               "entropy_vn); LinearAlgebra used for the 6-level outer ",
               "Liouvillian, Schur complement, RK4-polynomial propagator, ",
               "and eigenvalue clip -- exact algorithm parity with the ",
               "reference"),
        string("QO tensor stores kron(B,A); the declared PERM = [1,3,2,4] ",
               "carries the state into numpy ordering for the outer Schur ",
               "step and back; negativity is computed on the numpy-order ",
               "matrix"),
        string("the combinatorial drive (dC, gamma) is exact scalar log ",
               "arithmetic, identical by construction (diff recorded)"),
    ]
    all_pass = all(values(checks))
    receipt = Dict(
        "schema" => "ratchet.v8.nested-manifold.engine-leg.julia.v0",
        "engine" => "julia",
        "julia_version" => string(VERSION),
        "package_used" => "QuantumOptics + LinearAlgebra (see findings)",
        "reference" => abspath(NUMPY_RECEIPT),
        "checks" => checks,
        "data" => Dict("max_abs_diff_vs_numpy_receipt" => diffs,
                       "gate" => gate,
                       "S_L_series_julia" => series["S_L"],
                       "Phi0_series_julia" => series["Phi0"]),
        "findings" => findings,
        "all_pass" => all_pass,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => string("engine-parity probe: julia/QuantumOptics ",
                                  "replication of the rung-ONE base tick ",
                                  "loop vs the numpy receipt; ",
                                  "scratch_diagnostic; no new claim"),
    )
    open(joinpath(OUT, "receipt.json"), "w") do io
        JSON.print(io, receipt, 2)
    end
    println(JSON.json(Dict("rung" => "ENG-julia", "all_pass" => all_pass,
                           "checks" => checks, "max_abs_diffs" => diffs), 2))
    exit(all_pass ? 0 : 1)
end

main()
