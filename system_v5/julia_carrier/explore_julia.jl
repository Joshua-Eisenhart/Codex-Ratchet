# explore_julia.jl
#
# object_id: codex2_max_constraint_filter_attractor_v1
# claim_ceiling: exploration_probe — promotion_allowed: false
#
# WIDE constraint-filter + attractor-convergence exploration (codex2-MAX)
#
# Root constraints:
#   F01: finite-dim + finite stages + bounded (infinite/continuum candidates die here)
#   N01: max_commutator_norm > 1e-3 (order genuinely matters; commuting sets die here)
#
# Finite map:
#   domain:   (family_type, dim, seed_index, initial_density_matrix)
#   codomain: (f01_admitted, n01_admitted, terminal_state, attractor_class)
#
# CANDIDATE FAMILIES tested:
#   (1) Random Hermitian operator pairs at dims {2,3,4,6,8}
#   (2) Random unitary dynamics
#   (3) Random Lindblad/dissipative channels
#   (4) Carrier geometries: S3/SU(2), nested Hopf, Clifford Cl(n) n=2..6, quaternions
#   (5) Random channel sets (Kraus)
#
# CONTROLS that MUST die:
#   - Commuting operator sets (die under N01)
#   - Infinite/continuum-limit candidates (die under F01)
#   - Unital-only sets (should show weaker convergence)
#
# CONVERGENCE: 100+ random initial density matrices run forward;
#   measure pairwise final-state distance, basin count, basin-overlap.
#
# CHIRAL/MOBIUS: does the attractor show a sector structure where traversing
#   one sector continuously reaches the other? Test by tracking L/R handedness
#   under the surviving dynamics.
#
# Anti-fabrication:
#   - Graveyard entries are generated from the filter; not manually curated.
#   - Controls are separate and their failure is the signal.
#   - Wrong-structure controls (commuting / unital) embedded and tracked.
#   - No hardcoded "deltas" — thresholds computed from data or set structurally.
#
# Does NOT assert: layer-completion, manifold admission, coupling,
#   bridge (rho_AB/Xi/Phi0/Axis0), flux, or physics.

using LinearAlgebra
using Random
using Statistics
using JSON
using Dates

const OBJECT_ID = "codex2_max_constraint_filter_attractor_v1"
const CLAIM_CEILING = "exploration_probe — promotion_allowed: false"
const PROMOTION_ALLOWED = false
const RESULT_PATH = joinpath(@__DIR__, "explore_julia_results.json")
const RNG_SEED = 20260604
const N_SEEDS_PER_FAMILY = 20          # >=20 as specified
const N_CONVERGENCE_TRIALS = 120       # >=100 as specified
const N_STEPS = 80                     # forward evolution steps
const F01_DIM_BOUND = 64              # anything requiring unbounded dim dies
const N01_THRESHOLD = 1.0e-3          # commutator norm threshold
const POSITIVE_MOBIUS_ASSESSMENT = "mobius_candidate: sectors connect through zero-chirality intermediate"

# Size ladder dims (where the object supports it)
const CANDIDATE_DIMS = [2, 3, 4, 6, 8]
const SIZE_LADDER = [8, 16, 32, 64]

const TOOL_MANIFEST = Dict(
    "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "all compute: filter, attractor convergence, chiral probe; removing flips all verdicts"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "matrix ops for density matrices, commutators, Hermitian/unitary checks; removing kills N01 check"),
    "Statistics" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "mean/std for attractor spread and basin statistics"),
    "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "writes reference result for JAX audit lane"),
    "Random" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "seeded RNG for reproducible random candidates; removing kills reproducibility"),
    "Dates" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "timestamps result artifact"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "Statistics" => "supportive",
    "JSON" => "supportive",
    "Random" => "load_bearing",
    "Dates" => "supportive",
)

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY: density matrix construction and validation
# ─────────────────────────────────────────────────────────────────────────────

function random_density_matrix(rng::AbstractRNG, dim::Int)
    # Bures-random density matrix via Hilbert-Schmidt sampling
    G = randn(rng, ComplexF64, dim, dim)
    rho = G * G'
    rho ./= tr(rho)
    # Enforce exact hermiticity
    (rho .+ rho') ./ 2
end

function is_valid_density_matrix(rho::Matrix{ComplexF64}; tol::Float64=1e-8)
    d = size(rho, 1)
    size(rho, 2) == d || return false
    norm(rho - rho') < tol || return false
    abs(tr(rho) - 1.0) < tol || return false
    ev = real.(eigvals(rho))
    all(ev .>= -tol) || return false
    return true
end

function dm_trace_distance(rho::Matrix{ComplexF64}, sigma::Matrix{ComplexF64})
    # Trace distance: (1/2)||rho - sigma||_1
    D = rho - sigma
    sv = svdvals(D)
    0.5 * sum(sv)
end

function random_hermitian(rng::AbstractRNG, dim::Int)
    H = randn(rng, ComplexF64, dim, dim)
    (H .+ H') ./ 2
end

function random_unitary(rng::AbstractRNG, dim::Int)
    # QR decomposition of random complex matrix → unitary
    G = randn(rng, ComplexF64, dim, dim)
    Q, R = qr(G)
    D_diag = diag(R)
    phases = D_diag ./ abs.(D_diag)
    Matrix(Q) * Diagonal(phases)
end

function commutator_norm(A::Matrix{ComplexF64}, B::Matrix{ComplexF64})
    norm(A * B .- B * A)
end

# ─────────────────────────────────────────────────────────────────────────────
# F01 CHECK: finite-dim, finite stages, bounded carrier
# ─────────────────────────────────────────────────────────────────────────────

function f01_check(dim::Int, n_ops::Int, n_steps::Int)
    # All must be finite and bounded
    dim <= F01_DIM_BOUND || return (passed=false, reason="dim=$(dim) > F01_DIM_BOUND=$(F01_DIM_BOUND)")
    dim >= 2 || return (passed=false, reason="dim < 2: degenerate carrier")
    n_ops >= 1 || return (passed=false, reason="empty operator set")
    n_steps >= 1 || return (passed=false, reason="zero steps")
    (passed=true, reason="dim=$(dim), n_ops=$(n_ops), n_steps=$(n_steps) all finite and bounded")
end

# ─────────────────────────────────────────────────────────────────────────────
# N01 CHECK: max commutator norm > threshold
# ─────────────────────────────────────────────────────────────────────────────

function n01_check(ops::Vector{Matrix{ComplexF64}})
    n = length(ops)
    n < 2 && return (passed=false, max_comm=0.0, reason="need >=2 operators")
    max_comm = 0.0
    for i in 1:n, j in (i+1):n
        c = commutator_norm(ops[i], ops[j])
        max_comm = max(max_comm, c)
    end
    if max_comm > N01_THRESHOLD
        return (passed=true, max_comm=max_comm, reason="max commutator norm=$(round(max_comm, digits=6)) > $(N01_THRESHOLD)")
    else
        return (passed=false, max_comm=max_comm, reason="max commutator norm=$(round(max_comm, digits=6)) <= $(N01_THRESHOLD): ORDER DOES NOT MATTER → killed by N01")
    end
end

# ─────────────────────────────────────────────────────────────────────────────
# DYNAMICS: apply a channel step to a density matrix
# ─────────────────────────────────────────────────────────────────────────────

function apply_unitary_channel(rho::Matrix{ComplexF64}, U::Matrix{ComplexF64})
    U * rho * U'
end

function apply_kraus_channel(rho::Matrix{ComplexF64}, kraus::Vector{Matrix{ComplexF64}})
    out = zeros(ComplexF64, size(rho)...)
    for K in kraus
        out .+= K * rho * K'
    end
    out ./= tr(out)  # renormalize
    (out .+ out') ./ 2  # enforce hermiticity
end

function evolve_state(rho0::Matrix{ComplexF64}, ops::Vector{Matrix{ComplexF64}},
                      op_type::Symbol, n_steps::Int, rng::AbstractRNG)
    rho = copy(rho0)
    for _ in 1:n_steps
        if op_type == :unitary
            U = ops[rand(rng, 1:length(ops))]
            rho = apply_unitary_channel(rho, U)
        elseif op_type == :kraus
            rho = apply_kraus_channel(rho, ops)
        elseif op_type == :lindblad_euler
            # Euler step: drho/dt = -i[H,rho] + sum_k (L_k rho L_k† - 1/2{L_k†L_k, rho})
            # ops[1] = H, ops[2:end] = L_k
            H = ops[1]; Ls = ops[2:end]
            dt = 0.05
            drho = -1im * (H * rho - rho * H)
            for L in Ls
                drho .+= L * rho * L' .- 0.5 .* (L' * L * rho .+ rho * L' * L)
            end
            rho = rho .+ dt .* drho
            tr_val = tr(rho)
            abs(tr_val) > 1e-12 && (rho ./= tr_val)
            rho = (rho .+ rho') ./ 2
            # Project to PSD if necessary
            ev, evec = eigen(Hermitian(rho))
            ev .= max.(real.(ev), 0.0)
            rho = evec * Diagonal(ComplexF64.(ev)) * evec'
            tr2 = tr(rho); abs(tr2) > 1e-12 && (rho ./= tr2)
        end
    end
    (rho .+ rho') ./ 2
end

# ─────────────────────────────────────────────────────────────────────────────
# CONVERGENCE TEST: run N_CONVERGENCE_TRIALS random initial states forward;
# measure whether they cluster into one basin.
# ─────────────────────────────────────────────────────────────────────────────

function convergence_test(ops::Vector{Matrix{ComplexF64}}, op_type::Symbol,
                          dim::Int, rng::AbstractRNG;
                          n_trials::Int=N_CONVERGENCE_TRIALS,
                          n_steps::Int=N_STEPS,
                          cluster_thresh::Float64=0.10)
    terminal_states = Vector{Matrix{ComplexF64}}()
    for _ in 1:n_trials
        rho0 = random_density_matrix(rng, dim)
        rho_final = evolve_state(rho0, ops, op_type, n_steps, rng)
        push!(terminal_states, rho_final)
    end

    # Pairwise trace distances between terminal states
    n = length(terminal_states)
    pairwise_dists = Float64[]
    for i in 1:n, j in (i+1):n
        push!(pairwise_dists, dm_trace_distance(terminal_states[i], terminal_states[j]))
    end

    mean_dist = mean(pairwise_dists)
    max_dist = maximum(pairwise_dists)
    min_dist = minimum(pairwise_dists)

    # Count distinct basins by simple threshold clustering
    labels = ones(Int, n)
    next_label = 2
    for i in 2:n
        merged = false
        for j in 1:(i-1)
            if dm_trace_distance(terminal_states[i], terminal_states[j]) < cluster_thresh
                labels[i] = labels[j]
                merged = true
                break
            end
        end
        if !merged
            labels[i] = next_label
            next_label += 1
        end
    end
    n_basins = length(unique(labels))

    # Basin fractions
    basin_counts = Dict{Int,Int}()
    for l in labels; basin_counts[l] = get(basin_counts, l, 0) + 1; end
    basin_fracs = sort([c/n for c in values(basin_counts)], rev=true)

    # Dominant basin fraction
    dominant_frac = basin_fracs[1]

    # converges_to_basin assessment
    converges_label = if n_basins == 1
        "yes_single_basin"
    elseif dominant_frac >= 0.85
        "partial_dominant_basin"
    elseif dominant_frac >= 0.50
        "partial_spread"
    else
        "scatter"
    end

    return (
        n_trials=n_trials,
        n_basins=n_basins,
        mean_pairwise_dist=round(mean_dist, digits=6),
        max_pairwise_dist=round(max_dist, digits=6),
        min_pairwise_dist=round(min_dist, digits=6),
        basin_fractions=[round(f, digits=4) for f in basin_fracs],
        dominant_basin_frac=round(dominant_frac, digits=4),
        converges_to_basin=converges_label,
        terminal_states=terminal_states,
    )
end

# ─────────────────────────────────────────────────────────────────────────────
# CHIRAL / MOBIUS TEST: does the attractor have L/R handedness structure?
# Probe by tracking whether the terminal Bloch vector (for dim=2 qubit)
# or the dominant eigenstate has a definite chirality sector.
# For higher dims, proxy via parity of eigenvalue ordering.
# ─────────────────────────────────────────────────────────────────────────────

function chiral_mobius_test(terminal_states::Vector{Matrix{ComplexF64}}, dim::Int)
    # Chirality proxy: for each terminal state, compute the "handedness"
    # as the sign of Im(tr(rho * sigma_y)) for dim=2,
    # or the parity of the dominant eigenvector phase pattern for higher dim.
    chiralities = Float64[]
    for rho in terminal_states
        if dim == 2
            # Bloch vector component ny = 2*Im(rho[2,1])
            ny = 2 * imag(rho[2, 1])
            push!(chiralities, ny)
        else
            # Proxy: sum of imaginary parts of off-diagonal elements
            imag_sum = sum(imag(rho[i,j]) for i in 1:dim, j in 1:dim if i != j)
            push!(chiralities, imag_sum)
        end
    end

    # Check if chiralities cluster into two sectors with opposite sign
    pos = count(c -> c > 1e-6, chiralities)
    neg = count(c -> c < -1e-6, chiralities)
    zero_count = length(chiralities) - pos - neg

    # Mobius-like: do both sectors connect (neither is empty)?
    both_sectors = pos > 0 && neg > 0
    # Sector balance ratio: close to 0.5 means both sectors roughly equal
    total_nonzero = pos + neg
    balance = total_nonzero > 0 ? min(pos, neg) / total_nonzero : 0.0

    # Does traversing one sector reach the other continuously?
    # Proxy: is there a continuous path in the chirality sequence through zero?
    has_zero_crossings = zero_count > 0

    chiral_label = if both_sectors && balance > 0.2
        "both_sectors_present"
    elseif both_sectors && balance <= 0.2
        "both_sectors_present_unbalanced"
    else
        "single_sector"
    end

    mobius_label = if both_sectors && has_zero_crossings
        POSITIVE_MOBIUS_ASSESSMENT
    elseif both_sectors
        "two_disconnected_sectors: no zero crossing observed"
    else
        "single_sector: no chiral handedness in attractor"
    end

    return (
        pos_sector=pos,
        neg_sector=neg,
        zero_count=zero_count,
        balance=round(balance, digits=4),
        chiral_structure=chiral_label,
        mobius_assessment=mobius_label,
        mean_chirality=round(mean(chiralities), digits=6),
        std_chirality=round(std(chiralities), digits=6),
    )
end

function has_positive_mobius_assessment(r::Dict)
    get(r, "mobius_assessment", "") == POSITIVE_MOBIUS_ASSESSMENT
end

# ─────────────────────────────────────────────────────────────────────────────
# FAMILY TESTERS
# ─────────────────────────────────────────────────────────────────────────────

# Family 1: Random Hermitian operator pairs
function test_hermitian_pairs(rng::AbstractRNG, dim::Int, n_seeds::Int)
    results = []
    for seed in 1:n_seeds
        local_rng = MersenneTwister(RNG_SEED + seed * 1000 + dim)
        A = random_hermitian(local_rng, dim)
        B = random_hermitian(local_rng, dim)
        A_c = ComplexF64.(A); B_c = ComplexF64.(B)
        ops = [A_c, B_c]
        f01 = f01_check(dim, 2, N_STEPS)
        n01 = n01_check(ops)
        push!(results, (seed=seed, dim=dim, f01=f01.passed, n01=n01.passed,
                        max_comm=n01.max_comm))
    end
    n_f01 = count(r -> r.f01, results)
    n_n01 = count(r -> r.n01, results)
    n_both = count(r -> r.f01 && r.n01, results)
    # Survivors need BOTH
    admitted = n_both > 0
    verdict = admitted ? "SURVIVED: $(n_both)/$(n_seeds) seeds admitted under F01+N01" :
                         "KILLED: no seeds admitted under F01+N01"
    killed_reason = if n_f01 < n_seeds
        "some died under F01 (dim or steps out of bounds)"
    elseif n_n01 < n_seeds
        "$(n_seeds - n_n01) seeds killed by N01 (commutator norm too small)"
    else
        "none killed"
    end
    return Dict("family" => "hermitian_pairs_dim$(dim)",
                "dim" => dim, "n_seeds" => n_seeds,
                "n_f01_pass" => n_f01, "n_n01_pass" => n_n01, "n_both_pass" => n_both,
                "admitted" => admitted,
                "verdict" => verdict,
                "killed_reason" => killed_reason,
                "sample_max_comm" => round(mean([r.max_comm for r in results]), digits=6))
end

# Family 2: Random unitary dynamics
function test_unitary_dynamics(rng::AbstractRNG, dim::Int, n_seeds::Int)
    results = []
    for seed in 1:n_seeds
        local_rng = MersenneTwister(RNG_SEED + seed * 2000 + dim)
        U1 = random_unitary(local_rng, dim)
        U2 = random_unitary(local_rng, dim)
        ops = [ComplexF64.(U1), ComplexF64.(U2)]
        f01 = f01_check(dim, 2, N_STEPS)
        n01 = n01_check(ops)
        push!(results, (seed=seed, dim=dim, f01=f01.passed, n01=n01.passed,
                        max_comm=n01.max_comm))
    end
    n_f01 = count(r -> r.f01, results)
    n_n01 = count(r -> r.n01, results)
    n_both = count(r -> r.f01 && r.n01, results)
    admitted = n_both > 0
    verdict = admitted ? "SURVIVED: $(n_both)/$(n_seeds) seeds admitted under F01+N01" :
                         "KILLED: no seeds admitted"
    return Dict("family" => "unitary_dynamics_dim$(dim)",
                "dim" => dim, "n_seeds" => n_seeds,
                "n_f01_pass" => n_f01, "n_n01_pass" => n_n01, "n_both_pass" => n_both,
                "admitted" => admitted,
                "verdict" => verdict,
                "sample_max_comm" => round(mean([r.max_comm for r in results]), digits=6))
end

# Family 3: Lindblad/dissipative dynamics
function make_lindblad_ops(rng::AbstractRNG, dim::Int)
    H = ComplexF64.(random_hermitian(rng, dim))
    # Two random Lindblad operators
    L1 = randn(rng, ComplexF64, dim, dim) .* 0.3
    L2 = randn(rng, ComplexF64, dim, dim) .* 0.3
    return [H, L1, L2]
end

function test_lindblad_dynamics(rng::AbstractRNG, dim::Int, n_seeds::Int)
    results = []
    for seed in 1:n_seeds
        local_rng = MersenneTwister(RNG_SEED + seed * 3000 + dim)
        ops = make_lindblad_ops(local_rng, dim)
        # N01 check on H and the Lindblad operators
        all_ops_for_n01 = [ops[1], ops[2]]
        f01 = f01_check(dim, length(ops), N_STEPS)
        n01 = n01_check(all_ops_for_n01)
        push!(results, (seed=seed, dim=dim, f01=f01.passed, n01=n01.passed,
                        max_comm=n01.max_comm))
    end
    n_f01 = count(r -> r.f01, results)
    n_n01 = count(r -> r.n01, results)
    n_both = count(r -> r.f01 && r.n01, results)
    admitted = n_both > 0
    verdict = admitted ? "SURVIVED: $(n_both)/$(n_seeds) seeds admitted" :
                         "KILLED: no seeds admitted"
    return Dict("family" => "lindblad_dynamics_dim$(dim)",
                "dim" => dim, "n_seeds" => n_seeds,
                "n_f01_pass" => n_f01, "n_n01_pass" => n_n01, "n_both_pass" => n_both,
                "admitted" => admitted,
                "verdict" => verdict,
                "sample_max_comm" => round(mean([r.max_comm for r in results]), digits=6))
end

# Family 4a: S3/SU(2) carrier geometry
function su2_generators(dim::Int)
    # Generalized SU(2) generators embedded in dim x dim
    Jx = zeros(ComplexF64, dim, dim)
    Jy = zeros(ComplexF64, dim, dim)
    Jz = zeros(ComplexF64, dim, dim)
    j = (dim - 1) / 2.0
    for m_idx in 1:dim
        m = j - (m_idx - 1)
        if m_idx < dim
            mp = m + 1
            val = sqrt(j*(j+1) - m*mp) / 2
            Jx[m_idx, m_idx+1] = val
            Jx[m_idx+1, m_idx] = val
            Jy[m_idx, m_idx+1] = -1im * val
            Jy[m_idx+1, m_idx] = 1im * val
        end
        Jz[m_idx, m_idx] = m
    end
    return [Jx, Jy, Jz]
end

function test_su2_geometry(rng::AbstractRNG, dim::Int, n_seeds::Int)
    gens = su2_generators(dim)
    f01 = f01_check(dim, length(gens), N_STEPS)
    n01 = n01_check(gens)
    admitted = f01.passed && n01.passed
    verdict = admitted ? "SURVIVED: SU(2) generators at dim=$(dim) admitted under F01+N01" :
                         "KILLED: SU(2) at dim=$(dim): f01=$(f01.passed), n01=$(n01.passed)"
    return Dict("family" => "su2_geometry_dim$(dim)",
                "dim" => dim, "n_seeds" => n_seeds,
                "f01_pass" => f01.passed, "n01_pass" => n01.passed,
                "admitted" => admitted,
                "verdict" => verdict,
                "n01_max_comm" => round(n01.max_comm, digits=6),
                "f01_reason" => f01.reason, "n01_reason" => n01.reason)
end

# Family 4b: Nested Hopf / quaternion
function quaternion_operator_pair(dim::Int)
    # Embed quaternion i,j operators in dim x dim via Pauli embedding
    qi = zeros(ComplexF64, dim, dim)
    qj = zeros(ComplexF64, dim, dim)
    # i = sigma_y block, j = sigma_x block
    qi[1,2] = -1im; qi[2,1] = 1im
    qj[1,2] = 1.0; qj[2,1] = 1.0
    return [qi, qj]
end

function test_quaternion_carrier(rng::AbstractRNG, dim::Int, n_seeds::Int)
    ops = quaternion_operator_pair(dim)
    f01 = f01_check(dim, 2, N_STEPS)
    n01 = n01_check(ops)
    admitted = f01.passed && n01.passed
    verdict = admitted ? "SURVIVED: quaternion i,j at dim=$(dim)" :
                         "KILLED: quaternion at dim=$(dim): n01=$(n01.passed)"
    return Dict("family" => "quaternion_carrier_dim$(dim)",
                "dim" => dim, "n_seeds" => n_seeds,
                "f01_pass" => f01.passed, "n01_pass" => n01.passed,
                "admitted" => admitted,
                "verdict" => verdict,
                "n01_max_comm" => round(n01.max_comm, digits=6))
end

# Family 4c: Clifford Cl(n) for n=2..6 (via Gamma matrix representation)
function clifford_gamma_matrices(n::Int)
    # Build Clifford algebra generators for Cl(n) via tensor products of Pauli matrices
    # Using standard recursive construction: Gamma_k in 2^floor(n/2) x 2^floor(n/2) matrices
    sigma_x = ComplexF64[0 1; 1 0]
    sigma_y = ComplexF64[0 -1im; 1im 0]
    sigma_z = ComplexF64[1 0; 0 -1]
    id2 = ComplexF64[1 0; 0 1]

    # For Cl(n), standard generators:
    # n=2: Gamma1=sigx, Gamma2=sigy
    # n=3: Gamma1=sigx x id, Gamma2=sigy x id, Gamma3=sigz x id  (no wait,
    #       Cl(3) has rep dim=2, same as Cl(2) with anticommuting)
    # We'll build via Kronecker product construction for n generators in 2^ceil(n/2) dim

    # Simple explicit construction for n=2..6
    gammas = Matrix{ComplexF64}[]
    if n == 2
        push!(gammas, sigma_x, sigma_y)
    elseif n == 3
        push!(gammas, kron(sigma_x, id2), kron(sigma_y, id2), kron(sigma_z, id2))
    elseif n == 4
        push!(gammas,
            kron(sigma_x, id2),
            kron(sigma_y, id2),
            kron(sigma_z, sigma_x),
            kron(sigma_z, sigma_y))
    elseif n == 5
        push!(gammas,
            kron(sigma_x, id2, id2),
            kron(sigma_y, id2, id2),
            kron(sigma_z, sigma_x, id2),
            kron(sigma_z, sigma_y, id2),
            kron(sigma_z, sigma_z, sigma_x))
    elseif n == 6
        push!(gammas,
            kron(sigma_x, id2, id2),
            kron(sigma_y, id2, id2),
            kron(sigma_z, sigma_x, id2),
            kron(sigma_z, sigma_y, id2),
            kron(sigma_z, sigma_z, sigma_x),
            kron(sigma_z, sigma_z, sigma_y))
    end
    gammas
end

function test_clifford_algebra(rng::AbstractRNG, n::Int, n_seeds::Int)
    try
        gammas = clifford_gamma_matrices(n)
        dim = size(gammas[1], 1)
        f01 = f01_check(dim, length(gammas), N_STEPS)
        n01 = n01_check(gammas)
        admitted = f01.passed && n01.passed
        verdict = admitted ? "SURVIVED: Cl($(n)) generators dim=$(dim) admitted under F01+N01" :
                             "KILLED: Cl($(n)) at dim=$(dim): f01=$(f01.passed), n01=$(n01.passed)"
        return Dict("family" => "clifford_cl$(n)",
                    "clifford_n" => n, "dim" => dim, "n_seeds" => n_seeds,
                    "f01_pass" => f01.passed, "n01_pass" => n01.passed,
                    "admitted" => admitted,
                    "verdict" => verdict,
                    "n01_max_comm" => round(n01.max_comm, digits=6),
                    "n_generators" => length(gammas))
    catch e
        return Dict("family" => "clifford_cl$(n)", "error" => string(e),
                    "admitted" => false, "verdict" => "ERROR: $(e)")
    end
end

# Family 5: Random Kraus channel sets
function random_kraus_channel(rng::AbstractRNG, dim::Int, n_kraus::Int)
    # Random Kraus operators with completeness constraint sum_k K_k† K_k = I
    Ks = [randn(rng, ComplexF64, dim, dim) for _ in 1:n_kraus]
    # Normalize so sum K†K ≈ I
    gram = sum(K' * K for K in Ks)
    gram_sqrt = sqrt(Hermitian(gram))
    Ks = [K / gram_sqrt for K in Ks]
    Ks
end

function test_kraus_channels(rng::AbstractRNG, dim::Int, n_seeds::Int, n_kraus::Int=3)
    results = []
    for seed in 1:n_seeds
        local_rng = MersenneTwister(RNG_SEED + seed * 5000 + dim)
        Ks = random_kraus_channel(local_rng, dim, n_kraus)
        Ks_c = [ComplexF64.(K) for K in Ks]
        # For N01, compare K1 and K2 as operators
        f01 = f01_check(dim, n_kraus, N_STEPS)
        n01 = n01_check(Ks_c[1:min(2, end)])
        push!(results, (seed=seed, f01=f01.passed, n01=n01.passed, max_comm=n01.max_comm))
    end
    n_f01 = count(r -> r.f01, results)
    n_n01 = count(r -> r.n01, results)
    n_both = count(r -> r.f01 && r.n01, results)
    admitted = n_both > 0
    verdict = admitted ? "SURVIVED: $(n_both)/$(n_seeds) kraus channel sets admitted" :
                         "KILLED: no kraus channel sets admitted"
    return Dict("family" => "kraus_channels_dim$(dim)_k$(n_kraus)",
                "dim" => dim, "n_kraus" => n_kraus, "n_seeds" => n_seeds,
                "n_f01_pass" => n_f01, "n_n01_pass" => n_n01, "n_both_pass" => n_both,
                "admitted" => admitted,
                "verdict" => verdict,
                "sample_max_comm" => round(mean([r.max_comm for r in results]), digits=6))
end

# ─────────────────────────────────────────────────────────────────────────────
# CONTROLS THAT MUST DIE
# ─────────────────────────────────────────────────────────────────────────────

# Control 1: Commuting operator sets (die under N01)
function test_commuting_control(rng::AbstractRNG, dim::Int, n_seeds::Int)
    results = []
    for seed in 1:n_seeds
        local_rng = MersenneTwister(RNG_SEED + seed * 9000 + dim)
        # Diagonal Hermitian operators always commute
        d1 = Diagonal(ComplexF64.(randn(local_rng, dim)))
        d2 = Diagonal(ComplexF64.(randn(local_rng, dim)))
        ops = [Matrix(d1), Matrix(d2)]
        n01 = n01_check(ops)
        push!(results, (seed=seed, n01=n01.passed, max_comm=n01.max_comm))
    end
    n_n01 = count(r -> r.n01, results)
    killed = n_n01 == 0
    verdict = killed ? "CORRECTLY KILLED by N01: commuting diagonal ops, max_comm near machine eps" :
                       "WARNING: commuting control NOT killed — N01 threshold issue ($(n_n01)/$(n_seeds) passed)"
    return Dict("family" => "commuting_diagonal_control_dim$(dim)",
                "is_control" => true,
                "dim" => dim, "n_seeds" => n_seeds,
                "n_n01_pass" => n_n01,
                "killed" => killed,
                "verdict" => verdict,
                "expected_verdict" => "KILLED",
                "control_check" => killed ? "PASS" : "FAIL",
                "sample_max_comm" => round(mean([r.max_comm for r in results]), digits=10))
end

# Control 2: Continuum/infinite-limit candidates (die under F01)
function test_continuum_control()
    # Simulate an infinite-dimensional candidate: dim = Inf (fail immediately)
    f01 = f01_check(typemax(Int), 1, N_STEPS)
    killed = !f01.passed
    verdict = killed ? "CORRECTLY KILLED by F01: infinite-dim candidate excluded" :
                       "WARNING: continuum control NOT killed"
    return Dict("family" => "continuum_infinite_dim_control",
                "is_control" => true,
                "dim" => typemax(Int),
                "killed" => killed,
                "verdict" => verdict,
                "expected_verdict" => "KILLED",
                "control_check" => killed ? "PASS" : "FAIL",
                "f01_reason" => f01.reason)
end

# Control 3: Unital-only channel (should admit under filter but show weaker convergence)
function test_unital_control(rng::AbstractRNG, dim::Int, n_seeds::Int)
    # Unital channel: sum K_k K_k† = I AND sum K_k† K_k = I (preserves maximally mixed)
    results = []
    for seed in 1:n_seeds
        local_rng = MersenneTwister(RNG_SEED + seed * 8000 + dim)
        # Random unitary is unital
        U1 = ComplexF64.(random_unitary(local_rng, dim))
        U2 = ComplexF64.(random_unitary(local_rng, dim))
        # Depolarizing channel: rho -> (1-p)*rho + p*I/d is unital but commutes with I
        # Just use mixture of unitaries
        ops = [U1, U2]
        f01 = f01_check(dim, 2, N_STEPS)
        n01 = n01_check(ops)
        push!(results, (f01=f01.passed, n01=n01.passed))
    end
    n_both = count(r -> r.f01 && r.n01, results)
    # Unital channels with random unitaries CAN survive filter (random unitaries don't commute)
    # but they preserve I/d, so they converge to maximally mixed, not a distinct attractor
    admitted = n_both > 0
    verdict = admitted ?
        "CONTROL: survives F01+N01 filter; not counted as survivor; convergence/chiral proxy must be read as control-only" :
        "CONTROL: not admitted by F01+N01 in this run; no kill claim beyond the measured filter result"
    return Dict("family" => "unital_random_unitary_control_dim$(dim)",
                "is_control" => true,
                "control_kind" => "unital",
                "dim" => dim, "n_seeds" => n_seeds,
                "n_filter_pass" => n_both,
                "note" => "unital channels preserve max-mixed state; attractor = I/d; weaker chiral structure expected",
                "admitted_by_filter" => admitted,
                "control_check" => admitted ? "CONTROL_SURVIVES_FILTER" : "CONTROL_FILTER_REJECTED",
                "verdict" => verdict)
end

function unital_control_convergence_test(dim::Int)
    ops_rng = MersenneTwister(RNG_SEED + 9100 + dim)
    U1 = ComplexF64.(random_unitary(ops_rng, dim))
    U2 = ComplexF64.(random_unitary(ops_rng, dim))
    kraus_ops = [U1 ./ sqrt(2.0), U2 ./ sqrt(2.0)]

    identity = Matrix{ComplexF64}(I, dim, dim)
    unital_sum = zeros(ComplexF64, dim, dim)
    trace_preserving_sum = zeros(ComplexF64, dim, dim)
    for K in kraus_ops
        unital_sum .+= K * K'
        trace_preserving_sum .+= K' * K
    end

    conv_rng = MersenneTwister(RNG_SEED + 9200 + dim)
    conv = convergence_test(kraus_ops, :kraus, dim, conv_rng)
    chiral = chiral_mobius_test(conv.terminal_states, dim)

    return Dict(
        "family" => "unital_control_dim$(dim)",
        "source_family" => "unital_random_unitary_control_dim$(dim)",
        "is_control" => true,
        "control_kind" => "unital",
        "convergence_role" => "CONTROL_unital_equal_weight_unitary_mixture",
        "op_type" => "kraus",
        "n_trials" => conv.n_trials,
        "n_basins" => conv.n_basins,
        "mean_pairwise_dist" => conv.mean_pairwise_dist,
        "max_pairwise_dist" => conv.max_pairwise_dist,
        "min_pairwise_dist" => conv.min_pairwise_dist,
        "basin_fractions_top5" => conv.basin_fractions[1:min(5,end)],
        "dominant_basin_frac" => conv.dominant_basin_frac,
        "converges_to_basin" => conv.converges_to_basin,
        "chiral_pos_sector" => chiral.pos_sector,
        "chiral_neg_sector" => chiral.neg_sector,
        "chiral_balance" => chiral.balance,
        "chiral_structure" => chiral.chiral_structure,
        "mobius_assessment" => chiral.mobius_assessment,
        "mean_chirality" => chiral.mean_chirality,
        "std_chirality" => chiral.std_chirality,
        "unital_deviation" => round(norm(unital_sum - identity), digits=10),
        "trace_preserving_deviation" => round(norm(trace_preserving_sum - identity), digits=10),
        "verdict" => "CONTROL: convergence/chiral proxy captured; excluded from survivor Mobius headline and promotion evidence"
    )
end

# ─────────────────────────────────────────────────────────────────────────────
# SIZE LADDER: test N01 and F01 at larger dims
# ─────────────────────────────────────────────────────────────────────────────

function size_ladder_test(rng::AbstractRNG)
    ladder_results = []
    for dim in SIZE_LADDER
        local_rng = MersenneTwister(RNG_SEED + dim * 100)
        # Random Hermitian pair at large dim
        A = ComplexF64.(random_hermitian(local_rng, dim))
        B = ComplexF64.(random_hermitian(local_rng, dim))
        f01 = f01_check(dim, 2, N_STEPS)
        n01 = n01_check([A, B])
        push!(ladder_results, Dict(
            "dim" => dim,
            "f01_pass" => f01.passed,
            "n01_pass" => n01.passed,
            "admitted" => f01.passed && n01.passed,
            "n01_max_comm" => round(n01.max_comm, digits=4)
        ))
    end
    ladder_results
end

# ─────────────────────────────────────────────────────────────────────────────
# MAIN RUN
# ─────────────────────────────────────────────────────────────────────────────

function run_exploration()
    println("="^72)
    println("codex2-MAX: constraint-filter + attractor-convergence exploration")
    println("object_id: $(OBJECT_ID)")
    println("="^72)

    rng = MersenneTwister(RNG_SEED)
    t_start = now()

    graveyard = Dict{String,Any}[]
    survivors = Dict{String,Any}[]
    unital_controls = Dict{String,Any}[]
    unital_control_convergence_results = Dict{String,Any}[]
    all_family_results = Dict{String,Any}[]

    println("\n--- FAMILY FILTER PASS ---")

    # ── Families 1-5 across candidate dims ────────────────────────────────────
    for dim in CANDIDATE_DIMS
        print("  Hermitian pairs dim=$(dim)... ")
        r = test_hermitian_pairs(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        if r["admitted"]
            push!(survivors, r)
            println("SURVIVED")
        else
            push!(graveyard, r)
            println("killed")
        end

        print("  Unitary dynamics dim=$(dim)... ")
        r = test_unitary_dynamics(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        if r["admitted"]
            push!(survivors, r)
            println("SURVIVED")
        else
            push!(graveyard, r)
            println("killed")
        end

        print("  Lindblad dynamics dim=$(dim)... ")
        r = test_lindblad_dynamics(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        if r["admitted"]
            push!(survivors, r)
            println("SURVIVED")
        else
            push!(graveyard, r)
            println("killed")
        end

        print("  SU(2) geometry dim=$(dim)... ")
        r = test_su2_geometry(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        if r["admitted"]
            push!(survivors, r)
            println("SURVIVED")
        else
            push!(graveyard, r)
            println("killed")
        end

        print("  Quaternion carrier dim=$(dim)... ")
        r = test_quaternion_carrier(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        if r["admitted"]
            push!(survivors, r)
            println("SURVIVED")
        else
            push!(graveyard, r)
            println("killed")
        end

        print("  Kraus channels dim=$(dim)... ")
        r = test_kraus_channels(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        if r["admitted"]
            push!(survivors, r)
            println("SURVIVED")
        else
            push!(graveyard, r)
            println("killed")
        end
    end

    # Clifford algebras Cl(n) for n=2..6
    for n in 2:6
        print("  Clifford Cl($(n))... ")
        r = test_clifford_algebra(rng, n, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        if r["admitted"]
            push!(survivors, r)
            println("SURVIVED (dim=$(get(r,"dim","?")))")
        else
            push!(graveyard, r)
            println("killed")
        end
    end

    println("\n--- CONTROLS (must die or show expected behavior) ---")

    # Controls
    for dim in [2, 4]
        r = test_commuting_control(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        println("  Commuting control dim=$(dim): $(r["control_check"])")
        push!(graveyard, r)  # Controls always in graveyard
    end

    r_cont = test_continuum_control()
    push!(all_family_results, r_cont)
    println("  Continuum control: $(r_cont["control_check"])")
    push!(graveyard, r_cont)

    for dim in [2, 4]
        r = test_unital_control(rng, dim, N_SEEDS_PER_FAMILY)
        push!(all_family_results, r)
        push!(unital_controls, r)
        println("  Unital control dim=$(dim): $(r["control_check"])")
    end

    println("\n--- SIZE LADDER (F01+N01 at dims 8,16,32,64) ---")
    ladder_results = size_ladder_test(rng)
    for lr in ladder_results
        println("  dim=$(lr["dim"]): f01=$(lr["f01_pass"]) n01=$(lr["n01_pass"]) admitted=$(lr["admitted"])")
    end

    println("\n--- CONVERGENCE TEST on survivors ---")
    # Run convergence on the best survivor families (unitary dim=2 and Lindblad dim=2)
    # We pick representative survivors for convergence test
    convergence_results = Dict{String,Any}[]

    # Convergence families: explicit tuples with fixed dims captured in closures
    convergence_families = [
        ("unitary", 2, :unitary,
            let d = 2
                rng2 -> [random_unitary(MersenneTwister(RNG_SEED + 42), d),
                         random_unitary(MersenneTwister(RNG_SEED + 43), d)]
            end),
        ("lindblad", 2, :lindblad_euler,
            let d = 2
                rng2 -> make_lindblad_ops(MersenneTwister(RNG_SEED + 44), d)
            end),
        ("unitary", 4, :unitary,
            let d = 4
                rng2 -> [random_unitary(MersenneTwister(RNG_SEED + 52), d),
                         random_unitary(MersenneTwister(RNG_SEED + 53), d)]
            end),
        ("kraus", 2, :kraus,
            let d = 2
                rng2 -> random_kraus_channel(MersenneTwister(RNG_SEED + 60), d, 3)
            end),
    ]

    for (family_type, dim, op_type, op_gen_fn) in convergence_families
        local_rng = MersenneTwister(RNG_SEED + 1001)
        ops = op_gen_fn(local_rng)
        ops_c = [ComplexF64.(o) for o in ops]
        # Check this specific instance admits
        f01_r = f01_check(dim, length(ops_c), N_STEPS)
        n01_r = n01_check(ops_c[1:min(2,end)])
        if !(f01_r.passed && n01_r.passed)
            # Skip if this instance doesn't admit
            push!(convergence_results, Dict(
                "family" => "$(family_type)_dim$(dim)",
                "skipped" => true,
                "reason" => "specific instance did not admit under F01+N01"
            ))
            continue
        end
        print("  Convergence $(family_type) dim=$(dim) ($(N_CONVERGENCE_TRIALS) trials)... ")
        conv = convergence_test(ops_c, op_type, dim, local_rng)
        chiral = chiral_mobius_test(conv.terminal_states, dim)
        push!(convergence_results, Dict(
            "family" => "$(family_type)_dim$(dim)",
            "n_trials" => conv.n_trials,
            "n_basins" => conv.n_basins,
            "mean_pairwise_dist" => conv.mean_pairwise_dist,
            "max_pairwise_dist" => conv.max_pairwise_dist,
            "min_pairwise_dist" => conv.min_pairwise_dist,
            "basin_fractions_top5" => conv.basin_fractions[1:min(5,end)],
            "dominant_basin_frac" => conv.dominant_basin_frac,
            "converges_to_basin" => conv.converges_to_basin,
            "chiral_pos_sector" => chiral.pos_sector,
            "chiral_neg_sector" => chiral.neg_sector,
            "chiral_balance" => chiral.balance,
            "chiral_structure" => chiral.chiral_structure,
            "mobius_assessment" => chiral.mobius_assessment,
            "mean_chirality" => chiral.mean_chirality,
            "std_chirality" => chiral.std_chirality,
        ))
        println("basins=$(conv.n_basins) converges=$(conv.converges_to_basin) chiral=$(chiral.chiral_structure)")
    end

    println("\n--- CONVERGENCE TEST on unital controls ---")
    for r in unital_controls
        dim = r["dim"]
        print("  CONTROL unital dim=$(dim) ($(N_CONVERGENCE_TRIALS) trials)... ")
        conv_row = unital_control_convergence_test(dim)
        push!(unital_control_convergence_results, conv_row)
        r["convergence_family"] = conv_row["family"]
        r["converges_to_basin"] = conv_row["converges_to_basin"]
        r["n_basins"] = conv_row["n_basins"]
        r["dominant_basin_frac"] = conv_row["dominant_basin_frac"]
        r["chiral_structure"] = conv_row["chiral_structure"]
        r["mobius_assessment"] = conv_row["mobius_assessment"]
        r["control_convergence_verdict"] = conv_row["verdict"]
        println("basins=$(conv_row["n_basins"]) converges=$(conv_row["converges_to_basin"]) chiral=$(conv_row["chiral_structure"]) mobius=$(conv_row["mobius_assessment"])")
    end
    append!(convergence_results, unital_control_convergence_results)

    # ── Aggregate convergence summary ─────────────────────────────────────────
    survivor_convergence_results = [r for r in convergence_results
                                    if !get(r, "skipped", false) && !get(r, "is_control", false)]
    control_convergence_results = [r for r in convergence_results
                                   if !get(r, "skipped", false) && get(r, "is_control", false)]
    all_convergence_labels = [r["converges_to_basin"] for r in survivor_convergence_results]
    all_convergence_labels_with_controls = [r["converges_to_basin"] for r in convergence_results
                                            if !get(r, "skipped", false)]
    n_single_basin = count(==("yes_single_basin"), all_convergence_labels)
    n_partial = count(l -> startswith(l, "partial"), all_convergence_labels)
    n_scatter = count(==("scatter"), all_convergence_labels)

    converges_summary = if length(all_convergence_labels) == 0
        "no_convergence_tests_ran"
    elseif n_single_basin > 0 && n_scatter == 0
        "yes: majority converge to single basin"
    elseif n_single_basin > 0
        "partial: some single-basin, some scatter"
    elseif n_partial > 0
        "partial: dominant basin but not single"
    else
        "scatter: no dominant attractor found"
    end

    # Collect all chiral results
    chiral_results = [r for r in convergence_results if !get(r,"skipped",false) && haskey(r,"chiral_structure")]
    survivor_chiral_results = [r for r in chiral_results if !get(r, "is_control", false)]
    control_chiral_results = [r for r in chiral_results if get(r, "is_control", false)]
    survivor_chiral_sector_rows = [r for r in survivor_chiral_results if
        get(r,"chiral_structure","") == "both_sectors_present" ||
        get(r,"chiral_structure","") == "both_sectors_present_unbalanced"]
    control_positive_mobius_rows = [r for r in control_chiral_results if has_positive_mobius_assessment(r)]
    survivor_mobius_summary = if isempty(survivor_chiral_sector_rows)
        "no_chiral_mobius_structure_observed: single sector in all tested survivor rows"
    elseif any(has_positive_mobius_assessment, survivor_chiral_sector_rows)
        "chiral_mobius_candidate: both sectors present with zero-crossing; further probe needed"
    else
        "both_sectors_present_no_crossing: survivor rows show two disconnected chiral sectors; not Mobius"
    end
    unital_control_mobius_summary = if isempty(control_chiral_results)
        "unital_control_chiral_test_missing"
    elseif isempty(control_positive_mobius_rows)
        "unital_controls_no_mobius_candidate: control rows recorded separately"
    elseif any(has_positive_mobius_assessment, survivor_chiral_sector_rows)
        "unital_controls_also_show_mobius_candidate: excluded from survivor headline"
    else
        "unital_control_only_mobius_candidate: control row(s) show proxy zero-crossing; excluded from survivor headline as I/d relaxation artifact"
    end
    chiral_mobius_summary = if isempty(control_positive_mobius_rows) || any(has_positive_mobius_assessment, survivor_chiral_sector_rows)
        survivor_mobius_summary
    else
        "$(survivor_mobius_summary); $(unital_control_mobius_summary)"
    end

    elapsed = now() - t_start

    family_names = [r["family"] for r in all_family_results]
    duplicate_family_names = sort([name for name in unique(family_names) if count(==(name), family_names) > 1])
    accounting_closes = length(all_family_results) == length(survivors) + length(graveyard) + length(unital_controls)

    # ── Convergence numbers (machine-readable) ────────────────────────────────
    convergence_numbers = Dict(
        "n_convergence_tested" => length(all_convergence_labels_with_controls),
        "n_survivor_convergence_tested" => length(all_convergence_labels),
        "n_control_convergence_tested" => length(control_convergence_results),
        "n_single_basin" => n_single_basin,
        "n_partial" => n_partial,
        "n_scatter" => n_scatter,
        "per_family" => [Dict("family" => r["family"],
                              "converges_to_basin" => get(r,"converges_to_basin","skipped"),
                              "n_basins" => get(r,"n_basins",-1),
                              "dominant_frac" => get(r,"dominant_basin_frac",-1.0),
                              "is_control" => get(r,"is_control",false))
                         for r in convergence_results]
    )

    # ── Parity scalars for JAX lane ───────────────────────────────────────────
    # Key scalars the JAX audit lane will recompute and compare
    parity_targets = Dict(
        "n_survivors" => length(survivors),
        "n_graveyard" => length(graveyard),
        "n_candidates_tested" => length(all_family_results),
        "n_convergence_tested" => length(all_convergence_labels_with_controls),
        "n_survivor_convergence_tested" => length(all_convergence_labels),
        "n_unital_controls" => length(unital_controls),
        "n_single_basin" => n_single_basin,
    )

    result = Dict(
        "object_id" => OBJECT_ID,
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "timestamp" => string(t_start),
        "elapsed_ms" => Dates.value(elapsed),
        "f01_definition" => "finite-dim (<=64) + finite stages + bounded carrier",
        "n01_definition" => "max_commutator_norm > 1e-3 across operator pairs",
        "n_seeds_per_family" => N_SEEDS_PER_FAMILY,
        "n_convergence_trials" => N_CONVERGENCE_TRIALS,
        "n_steps" => N_STEPS,
        "size_ladder" => SIZE_LADDER,
        "candidate_dims" => CANDIDATE_DIMS,
        "families_tested" => [r["family"] for r in all_family_results],
        "n_candidates_tested" => length(all_family_results),
        "n_unique_family_names" => length(unique(family_names)),
        "duplicate_family_names" => duplicate_family_names,
        "accounting_closes" => accounting_closes,
        "accounting_equation" => "n_candidates_tested == n_survivors + n_graveyard + n_unital_controls",
        "graveyard" => graveyard,
        "survivors" => survivors,
        "unital_controls" => unital_controls,
        "n_unital_controls" => length(unital_controls),
        "n_survivors" => length(survivors),
        "n_graveyard" => length(graveyard),
        "size_ladder_results" => ladder_results,
        "convergence_results" => convergence_results,
        "convergence_summary" => converges_summary,
        "survivor_convergence_summary" => converges_summary,
        "converges_to_basin" => converges_summary,
        "convergence_numbers" => convergence_numbers,
        "chiral_mobius_summary" => chiral_mobius_summary,
        "chiral_mobius" => chiral_mobius_summary,
        "survivor_chiral_mobius_summary" => survivor_mobius_summary,
        "unital_control_chiral_mobius_summary" => unital_control_mobius_summary,
        "parity_targets" => parity_targets,
        "tool_manifest" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "open_issues" => [
            "Size ladder at dim 8/16/32/64: convergence test not run (cost); only filter run",
            "Clifford Cl(5)/Cl(6) use dim=8 rep — convergence test would need more steps",
            "Chiral/Mobius test is a proxy (imaginary component of rho), not exact geometric handedness",
            "Lindblad Euler step can drift from PSD cone at large dt — projection used but not exact",
            "Basin threshold 0.10 is structural; sweeping the threshold would expose fragility",
            "Unital control convergence/chiral rows are controls only, not survivor evidence or promotion evidence",
            "No SMT/z3 proof layer — structural impossibility proofs not yet integrated",
        ],
    )

    open(RESULT_PATH, "w") do f
        JSON.print(f, result, 2)
    end

    println("\n--- SUMMARY ---")
    println("Candidates tested:  $(length(all_family_results))")
    println("Survivors (F01+N01): $(length(survivors))")
    println("Graveyard:          $(length(graveyard))")
    println("Unital controls:    $(length(unital_controls))")
    println("Accounting closes:  $(accounting_closes)")
    println("Convergence summary: $(converges_summary)")
    println("Chiral/Mobius:       $(chiral_mobius_summary)")
    println("\nResult written to: $(RESULT_PATH)")
    println("="^72)
end

run_exploration()
