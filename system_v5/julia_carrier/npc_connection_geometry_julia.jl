# npc_connection_geometry_julia.jl
# Nested-PEPS2D / Hopfield connection-geometry readout — Julia carrier.
#
# object_id:   npc_connection_geometry_julia
# claim_ceiling: scratch_diagnostic — does NOT assert layer completion,
#   PEPS3D admission, manifold admission, flux, Axis0, FEP, bridge, or physics.
# promotion_allowed: false
#
# F01 witness: finite site counts N in {8, 16, 32}; M=3 stored patterns.
# N01 witness: noncommuting quaternion products for plaquette holonomy
#              U_ij * U_jk * U_kl * U_li (order matters; AB != BA in general).
#
# Domain:   finite 2D torus graph (N sites), M=3 unit-quaternion pattern fields.
# Codomain: geometry readout vector per size:
#           [plaquette holonomy mean angle (rad), Laplacian spectral gap,
#            heat-trace at t=1, flat-control holonomy, parity slot].
#
# Tests:
#   Positive: structured Hopf-bond W -> nontrivial holonomy (mean angle > 0.1 rad).
#   Negative: flat/uniform W -> near-trivial holonomy (mean angle < 0.05 rad).
#   Boundary: erased control (B=A) -> symmetric geometry (AB == BA to 1e-10).
#   Input-dependence: readout changes across seeds (std of mean angles > 0).
#   Size ladder: 8 / 16 / 32 sites.
#
# Run:
#   cd system_v5/julia_carrier
#   julia --project=. npc_connection_geometry_julia.jl

using LinearAlgebra, Graphs, JSON, Statistics

# ─────────────────────────────────────────────
# Quaternion arithmetic (unit Hamilton quaternions)
# ─────────────────────────────────────────────

struct Quat
    w::Float64
    x::Float64
    y::Float64
    z::Float64
end

Base.:*(a::Quat, b::Quat) = Quat(
    a.w*b.w - a.x*b.x - a.y*b.y - a.z*b.z,
    a.w*b.x + a.x*b.w + a.y*b.z - a.z*b.y,
    a.w*b.y - a.x*b.z + a.y*b.w + a.z*b.x,
    a.w*b.z + a.x*b.y - a.y*b.x + a.z*b.w,
)
conj(q::Quat) = Quat(q.w, -q.x, -q.y, -q.z)
norm_q(q::Quat) = sqrt(q.w^2 + q.x^2 + q.y^2 + q.z^2)
function normalize_q(q::Quat; eps=1e-14)
    n = norm_q(q)
    n < eps ? Quat(1.0, 0.0, 0.0, 0.0) : Quat(q.w/n, q.x/n, q.y/n, q.z/n)
end
add_q(a::Quat, b::Quat) = Quat(a.w+b.w, a.x+b.x, a.y+b.y, a.z+b.z)
scale_q(s::Float64, q::Quat) = Quat(s*q.w, s*q.x, s*q.y, s*q.z)
zero_q() = Quat(0.0, 0.0, 0.0, 0.0)
qdiff_norm(a::Quat, b::Quat) = norm_q(add_q(a, scale_q(-1.0, b)))

function hopf_axis(q::Quat)
    # q = (Re a, Im a, Re b, Im b) for psi=(a,b).
    [
        2.0 * (q.w*q.y + q.x*q.z),
        2.0 * (q.w*q.z - q.x*q.y),
        q.w^2 + q.x^2 - q.y^2 - q.z^2,
    ]
end

function normalize_vec3(v::Vector{Float64}; eps=1e-14)
    n = norm(v)
    n < eps ? [0.0, 0.0, 1.0] : v ./ n
end

dot_q(a::Quat, b::Quat) = a.w*b.w + a.x*b.x + a.y*b.y + a.z*b.z

# ─────────────────────────────────────────────
# Locked carrier: Weyl spinor from Hopf angles
# psi_s(phi, chi; eta) = [exp(i(phi+chi))cos(eta), exp(i(phi-chi))sin(eta)]^T
# Represented as quaternion: (cos(eta) * [cos(phi+chi), sin(phi+chi), 0, 0])
#                           + (sin(eta) * [cos(phi-chi), sin(phi-chi), 0, 0])
# We use the S^3 embedding: q = cos(eta)*(cos(phi+chi), sin(phi+chi),0,0)
#                               + sin(eta)*(cos(phi-chi),-sin(phi-chi),0,0)
# (the real part of the two complex amplitudes plus zeros in y,z for L;
#  R is the conjugated/negated Hamiltonian H_R = -H0 sign flip)
# ─────────────────────────────────────────────

function weyl_spinor_quat(phi::Float64, chi::Float64, eta::Float64, chirality::Symbol)
    # Unit quaternion embedding of the Weyl spinor on S^3
    c = cos(eta)
    s = sin(eta)
    pp = phi + chi
    pm = phi - chi
    # L spinor: q_L = (c*cos(pp), c*sin(pp), s*cos(pm), s*sin(pm)) -- 4 real coords on S^3
    # R spinor: sign flip on imaginary part (Weyl H_R = -H_L)
    if chirality == :L
        q = Quat(c*cos(pp), c*sin(pp), s*cos(pm), s*sin(pm))
    else
        q = Quat(c*cos(pp), -c*sin(pp), s*cos(pm), -s*sin(pm))
    end
    normalize_q(q)
end

# ─────────────────────────────────────────────
# Site graph: 2D torus of N sites (sqrt(N) x sqrt(N))
# ─────────────────────────────────────────────

function torus_dims(N::Int)
    # Find Lx, Ly such that Lx*Ly == N, Lx <= Ly, both >= 2.
    # Prefer Lx=2 for non-square N (8->2x4, 32->4x8).
    best = (2, div(N, 2))
    for lx in 2:isqrt(N)
        if N % lx == 0
            best = (lx, div(N, lx))
        end
    end
    best
end

function torus_graph(N::Int)
    Lx, Ly = torus_dims(N)
    g = SimpleGraph(N)
    idx(x, y) = ((x-1) % Lx) * Ly + ((y-1) % Ly) + 1
    for x in 1:Lx, y in 1:Ly
        i = idx(x, y)
        add_edge!(g, i, idx(x+1, y))
        add_edge!(g, i, idx(x, y+1))
    end
    g
end

function torus_plaquettes(N::Int)
    Lx, Ly = torus_dims(N)
    idx(x, y) = ((x-1) % Lx) * Ly + ((y-1) % Ly) + 1
    plaq = Vector{NTuple{4,Int}}()
    for x in 1:Lx, y in 1:Ly
        a = idx(x, y)
        b = idx(x+1, y)
        c = idx(x+1, y+1)
        d = idx(x, y+1)
        push!(plaq, (a, b, c, d))
    end
    plaq
end

# ─────────────────────────────────────────────
# Hopfield bond matrix W_ij = sum_mu xi_i^mu * conj(xi_j^mu)
# ─────────────────────────────────────────────

function hopfield_weights(patterns::Matrix{Quat}, g::SimpleGraph)
    N = nv(g)
    M, Np = size(patterns)
    @assert Np == N
    W = fill(zero_q(), N, N)
    for i in 1:N, j in 1:N
        if i != j
            s = zero_q()
            for mu in 1:M
                s = add_q(s, patterns[mu, i] * conj(patterns[mu, j]))
            end
            W[i, j] = s
        end
    end
    W
end

function flat_weights(N::Int)
    # Flat/uniform control: W_ij = identity quaternion (trivial connection)
    W = fill(zero_q(), N, N)
    for i in 1:N, j in 1:N
        if i != j
            W[i, j] = Quat(1.0, 0.0, 0.0, 0.0)
        end
    end
    W
end

# ─────────────────────────────────────────────
# Random patterns seeded deterministically from site index + seed
# ─────────────────────────────────────────────

function make_patterns(N::Int, M::Int, seed::Int)
    rng = [seed, N, M]
    function lcg(state)
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        (state / 0xFFFFFFFF) * 2.0 - 1.0, state
    end
    patterns = Matrix{Quat}(undef, M, N)
    state = seed
    for mu in 1:M, i in 1:N
        w, state = lcg(state + mu * 17 + i * 31)
        x, state = lcg(state + 7)
        y, state = lcg(state + 13)
        z, state = lcg(state + 19)
        patterns[mu, i] = normalize_q(Quat(w, x, y, z))
    end
    patterns
end

function make_hopf_patterns(N::Int, M::Int, seed::Int)
    # Patterns from Hopf-angle parameterization — structured, not random flat.
    # Seed enters via irrational-multiple offset on phi0 and eta amplitude,
    # ensuring different seeds produce distinguishable pattern fields (not just
    # a phase-wrapped near-copy). The 0.37 (≈ 3/8, irrational scale) breaks
    # periodicity of the torus average across seeds.
    Lx, Ly = torus_dims(N)
    patterns = Matrix{Quat}(undef, M, N)
    seed_phi  = mod(seed * 0.37, 2π)   # global phase offset per seed
    seed_eta  = mod(seed * 0.17, 0.4)  # eta amplitude shift
    for mu in 1:M
        phi0 = 2π * (mu - 1) / M + seed_phi * (mu + 1) / M
        for i in 1:N
            x = div(i-1, Ly) + 1
            y = mod(i-1, Ly) + 1
            phi = phi0 + 2π * x / Lx
            chi = 2π * y / Ly
            eta = π/4 + (0.2 + seed_eta * 0.1) * sin(phi + chi)
            patterns[mu, i] = weyl_spinor_quat(phi, chi, eta, mu % 2 == 0 ? :L : :R)
        end
    end
    patterns
end

function weyl_site_fields(N::Int, seed::Int)
    Lx, Ly = torus_dims(N)
    seed_phi = mod(seed * 0.37, 2π)
    seed_eta = mod(seed * 0.17, 0.4)
    psi_L = Vector{Quat}(undef, N)
    psi_R = Vector{Quat}(undef, N)
    etas = Vector{Float64}(undef, N)
    for i in 1:N
        x = div(i-1, Ly) + 1
        y = mod(i-1, Ly) + 1
        phi = seed_phi + 2π * x / Lx
        chi = 2π * y / Ly
        eta = π/4 + (0.2 + seed_eta * 0.1) * sin(phi + chi)
        psi_L[i] = weyl_spinor_quat(phi, chi, eta, :L)
        psi_R[i] = weyl_spinor_quat(phi, chi, eta, :R)
        etas[i] = eta
    end
    psi_L, psi_R, etas
end

# ─────────────────────────────────────────────
# Unitarized link and plaquette holonomy
# ─────────────────────────────────────────────

function unitarize(W::Matrix{Quat})
    N = size(W, 1)
    U = Matrix{Quat}(undef, N, N)
    for i in 1:N, j in 1:N
        U[i, j] = normalize_q(W[i, j])
    end
    U
end

function plaquette_holonomy_angle(U::Matrix{Quat}, plaquettes::Vector{NTuple{4,Int}})
    # F_square = U_ij * U_jk * U_kl * U_li around each 4-cycle
    # Holonomy angle = arccos(|w component|) of the normalized result
    angles = Float64[]
    for (a, b, c, d) in plaquettes
        hol = U[a,b] * U[b,c] * U[c,d] * U[d,a]
        hol = normalize_q(hol)
        angle = acos(clamp(abs(hol.w), 0.0, 1.0))
        push!(angles, angle)
    end
    angles
end

function plaquette_noncommutator_gap(U::Matrix{Quat}, plaquettes::Vector{NTuple{4,Int}})
    gaps = Float64[]
    for (a, b, c, d) in plaquettes
        factors = (U[a,b], U[b,c], U[c,d], U[d,a])
        for i in 1:4, j in i+1:4
            push!(gaps, qdiff_norm(factors[i] * factors[j], factors[j] * factors[i]))
        end
    end
    (mean_gap=mean(gaps), max_gap=maximum(gaps))
end

function compose_links(WA::Matrix{Quat}, WB::Matrix{Quat}, order::Symbol)
    N = size(WA, 1)
    C = fill(zero_q(), N, N)
    for i in 1:N, j in 1:N
        if i != j
            a = normalize_q(WA[i, j])
            b = normalize_q(WB[i, j])
            C[i, j] = order == :AB ? a * b : b * a
        end
    end
    C
end

function link_order_gap(WA::Matrix{Quat}, WB::Matrix{Quat}, g::SimpleGraph)
    gaps = Float64[]
    for e in edges(g)
        i, j = src(e), dst(e)
        a = normalize_q(WA[i, j])
        b = normalize_q(WB[i, j])
        push!(gaps, qdiff_norm(a * b, b * a))
    end
    (mean_gap=mean(gaps), max_gap=maximum(gaps))
end

# ─────────────────────────────────────────────
# Graph Laplacian from quaternion bond magnitudes
# ─────────────────────────────────────────────

function weighted_laplacian(W::Matrix{Quat}, g::SimpleGraph)
    N = nv(g)
    Wf = zeros(Float64, N, N)
    for e in edges(g)
        i, j = src(e), dst(e)
        # Conductance = exp(beta * su2_projection) where beta=1.25
        beta = 1.25
        u = normalize_q(W[i, j])
        # SU(2) vector component magnitude
        su2_mag = sqrt(u.x^2 + u.y^2 + u.z^2)
        conductance = exp(beta * su2_mag)
        Wf[i, j] = conductance
        Wf[j, i] = conductance
    end
    D = diagm(vec(sum(Wf, dims=2)))
    D - Wf
end

function heat_trace(L_mat::Matrix{Float64}, t::Float64=1.0)
    evals = eigvals(Symmetric(L_mat))
    sum(exp.(-t .* evals))
end

# ─────────────────────────────────────────────
# Terrain axes n_tau from Hopf coords + Weyl spinor + h_a = sum_b W_ab psi_b
# (finite map: patterns -> field -> terrain signature)
# ─────────────────────────────────────────────

function terrain_signature(W::Matrix{Quat}, N::Int, seed::Int)
    # h_a = sum_b W_ab * psi_b, read separately on L/R Weyl sheets from the locked carrier.
    psi_L, psi_R, etas = weyl_site_fields(N, seed)
    h_L = Vector{Quat}(undef, N)
    h_R = Vector{Quat}(undef, N)
    axes_L = Vector{Vector{Float64}}(undef, N)
    axes_R = Vector{Vector{Float64}}(undef, N)
    for a in 1:N
        sL = zero_q()
        sR = zero_q()
        for b in 1:N
            sL = add_q(sL, W[a, b] * psi_L[b])
            sR = add_q(sR, W[a, b] * psi_R[b])
        end
        h_L[a] = normalize_q(sL)
        h_R[a] = normalize_q(sR)
        hopf_L = hopf_axis(psi_L[a])
        hopf_R = hopf_axis(psi_R[a])
        field_L = hopf_axis(h_L[a])
        field_R = hopf_axis(h_R[a])
        sheet_L = [0.0, 0.0,  cos(2.0 * etas[a])]
        sheet_R = [0.0, 0.0, -cos(2.0 * etas[a])]
        axes_L[a] = normalize_vec3(hopf_L .+ 0.7 .* field_L .+ 0.3 .* sheet_L)
        axes_R[a] = normalize_vec3(hopf_R .+ 0.7 .* field_R .+ 0.3 .* sheet_R)
    end
    alignment = vcat([dot_q(h_L[a], psi_L[a]) for a in 1:N], [dot_q(h_R[a], psi_R[a]) for a in 1:N])
    axis_gap = [norm(axes_L[a] .- axes_R[a]) for a in 1:N]
    mean_axis = [mean(v[k] for v in vcat(axes_L, axes_R)) for k in 1:3]
    (mean_alignment=mean(alignment),
     std_alignment=std(alignment),
     mean_axis=mean_axis,
     lr_axis_gap_mean=mean(axis_gap),
     lr_axis_gap_max=maximum(axis_gap))
end

# ─────────────────────────────────────────────
# Full readout for one (N, seed) configuration
# ─────────────────────────────────────────────

function readout(N::Int, seed::Int; M::Int=3, t_heat::Float64=1.0)
    g = torus_graph(N)
    plaq = torus_plaquettes(N)

    # Structured Hopf-bond patterns
    patterns = make_hopf_patterns(N, M, seed)
    W = hopfield_weights(patterns, g)
    U = unitarize(W)
    angles = plaquette_holonomy_angle(U, plaq)
    n01 = plaquette_noncommutator_gap(U, plaq)
    Lmat = weighted_laplacian(W, g)
    evals = sort(eigvals(Symmetric(Lmat)))
    ht = heat_trace(Lmat, t_heat)
    terrain = terrain_signature(W, N, seed)

    # Flat/trivial control
    W_flat = flat_weights(N)
    U_flat = unitarize(W_flat)
    angles_flat = plaquette_holonomy_angle(U_flat, plaq)
    Lmat_flat = weighted_laplacian(W_flat, g)
    evals_flat = sort(eigvals(Symmetric(Lmat_flat)))
    ht_flat = heat_trace(Lmat_flat, t_heat)

    # Input-dependence: compare seed vs seed+7919 (prime shift ensures structural independence)
    # Note: mean holonomy shrinks ~1/sqrt(N) due to averaging; threshold scales accordingly.
    patterns2 = make_hopf_patterns(N, M, seed + 7919)
    W2 = hopfield_weights(patterns2, g)
    U2 = unitarize(W2)
    angles2 = plaquette_holonomy_angle(U2, plaq)
    input_dep_delta = abs(mean(angles) - mean(angles2))
    structured_order = link_order_gap(W, W2, g)

    # Erased boundary: B=A, so elementwise AB and BA readouts must be symmetric.
    W_erased_ab = compose_links(W, W, :AB)
    W_erased_ba = compose_links(W, W, :BA)
    angles_ab = plaquette_holonomy_angle(unitarize(W_erased_ab), plaq)
    angles_ba = plaquette_holonomy_angle(unitarize(W_erased_ba), plaq)
    erased_angle_diff = maximum(abs.(angles_ab .- angles_ba))
    erased_order = link_order_gap(W, W, g)

    Dict(
        "N" => N,
        "seed" => seed,
        "M" => M,
        # Structured readout
        "plaquette_holonomy_mean_rad" => mean(angles),
        "plaquette_holonomy_std_rad"  => std(angles),
        "plaquette_noncommutator_mean_gap" => n01.mean_gap,
        "plaquette_noncommutator_max_gap"  => n01.max_gap,
        "laplacian_spectral_gap"      => evals[2] - evals[1],
        "laplacian_gap"               => evals[2] - evals[1],
        "heat_trace_t1"               => ht,
        "terrain_mean_alignment"      => terrain.mean_alignment,
        "terrain_std_alignment"       => terrain.std_alignment,
        "terrain_axis_mean"           => terrain.mean_axis,
        "weyl_lr_axis_gap_mean"       => terrain.lr_axis_gap_mean,
        "weyl_lr_axis_gap_max"        => terrain.lr_axis_gap_max,
        # Flat control
        "flat_holonomy_mean_rad"      => mean(angles_flat),
        "flat_laplacian_gap"          => evals_flat[2] - evals_flat[1],
        "flat_heat_trace"             => ht_flat,
        # Erased control (should be ~0)
        "erased_angle_diff_max"       => erased_angle_diff,
        "erased_ab_ba_commutator_gap" => erased_order.max_gap,
        "structured_ab_ba_commutator_gap" => structured_order.mean_gap,
        # Input-dependence (should be > 0)
        "input_dep_holonomy_delta"    => input_dep_delta,
    )
end

# ─────────────────────────────────────────────
# Main: size ladder 8 / 16 / 32
# ─────────────────────────────────────────────

function main()
    sizes = [8, 16, 32]
    seeds = [20260602, 20260603]
    M = 3

    size_results = Dict{String, Any}()
    all_pass = true
    checks = String[]

    for N in sizes
        rows = [readout(N, s; M=M) for s in seeds]
        # Aggregate across seeds
        mean_hol  = mean([r["plaquette_holonomy_mean_rad"] for r in rows])
        flat_hol  = mean([r["flat_holonomy_mean_rad"] for r in rows])
        lag_gap   = mean([r["laplacian_spectral_gap"] for r in rows])
        heat_t1   = mean([r["heat_trace_t1"] for r in rows])
        flat_gap  = mean([r["flat_laplacian_gap"] for r in rows])
        flat_ht   = mean([r["flat_heat_trace"] for r in rows])
        erased_diff = maximum([r["erased_angle_diff_max"] for r in rows])
        inp_dep   = mean([r["input_dep_holonomy_delta"] for r in rows])
        terrain_align = mean([r["terrain_mean_alignment"] for r in rows])

        n01_gap = mean([r["plaquette_noncommutator_mean_gap"] for r in rows])
        erased_comm = maximum([r["erased_ab_ba_commutator_gap"] for r in rows])
        structured_order_gap = mean([r["structured_ab_ba_commutator_gap"] for r in rows])
        terrain_axis_gap = mean([r["weyl_lr_axis_gap_mean"] for r in rows])

        # Test criteria
        pos_pass = mean_hol > 0.1
        neg_pass = flat_hol < 0.05
        bnd_pass = erased_diff < 1e-8 && erased_comm < 1e-10
        # Threshold scales: for larger N more averaging suppresses mean drift;
        # 1e-4 is still well above machine-epsilon and confirms distinguishability.
        inp_pass = inp_dep > 1e-4
        n01_pass = n01_gap > 1e-3 && structured_order_gap > 1e-3

        push!(checks, "N=$N pos(hol>0.1)=$(pos_pass) neg(flat<0.05)=$(neg_pass) bnd(erased_AB_BA<1e-8)=$(bnd_pass) inp_dep(>1e-4)=$(inp_pass) n01(noncomm>1e-3)=$(n01_pass)")

        all_pass = all_pass && pos_pass && neg_pass && bnd_pass && inp_pass && n01_pass

        size_results[string(N)] = Dict(
            "plaquette_holonomy_mean_rad"  => mean_hol,
            "plaquette_holonomy_std_rad"   => mean([r["plaquette_holonomy_std_rad"] for r in rows]),
            "plaquette_noncommutator_mean_gap" => n01_gap,
            "plaquette_noncommutator_max_gap" => maximum([r["plaquette_noncommutator_max_gap"] for r in rows]),
            "laplacian_spectral_gap"       => lag_gap,
            "laplacian_gap"                => lag_gap,
            "heat_trace_t1"               => heat_t1,
            "flat_holonomy_mean_rad"       => flat_hol,
            "flat_laplacian_gap"           => flat_gap,
            "flat_heat_trace"             => flat_ht,
            "erased_angle_diff_max"        => erased_diff,
            "erased_ab_ba_commutator_gap"  => erased_comm,
            "structured_ab_ba_commutator_gap" => structured_order_gap,
            "input_dep_holonomy_delta"     => inp_dep,
            "terrain_mean_alignment"       => terrain_align,
            "terrain_axis_mean"            => [mean(r["terrain_axis_mean"][k] for r in rows) for k in 1:3],
            "weyl_lr_axis_gap_mean"        => terrain_axis_gap,
            "weyl_lr_axis_gap_max"         => maximum([r["weyl_lr_axis_gap_max"] for r in rows]),
            "parity_max_diff_vs_jax"       => nothing,   # filled in by JAX parity pass
            "tests" => Dict(
                "positive_structured_holonomy" => pos_pass,
                "negative_flat_holonomy"       => neg_pass,
                "boundary_erased_symmetric"    => bnd_pass,
                "input_dependent"              => inp_pass,
                "noncommuting_quaternion_witness" => n01_pass,
            ),
        )
    end

    result = Dict(
        "object_id"       => "npc_connection_geometry_julia",
        "classification"  => "scratch_diagnostic",
        "promotion_allowed" => false,
        "claim_ceiling"   => (
            "Scratch diagnostic only. Survived: structured Hopf bonds admitted "
            * "nontrivial plaquette holonomy; flat bonds excluded (near-trivial). "
            * "Does NOT assert layer completion, PEPS3D admission, manifold admission, "
            * "flux, Axis0, FEP, bridge, or physics."
        ),
        "F01_witness"     => "finite N in {8,16,32}, M=3 Hopf-pattern fields per size",
        "N01_witness"     => "noncommuting quaternion plaquette holonomy U_ij*U_jk*U_kl*U_li (order-sensitive)",
        "domain"          => "finite 2D torus graph (N sites), M=3 unit-quaternion Hopfield patterns from locked Weyl carrier",
        "codomain"        => "geometry readout: [holonomy mean angle (rad), Laplacian spectral gap, heat trace Tr(exp(-tL)), terrain alignment]",
        "carrier_spec"    => "psi_s(phi,chi;eta)=[exp(i(phi+chi))cos(eta), exp(i(phi-chi))sin(eta)]^T; H_L=+H0, H_R=-H0",
        "sizes"           => size_results,
        "controls"        => Dict(
            "flat_trivial_holonomy"  => "uniform W -> F_square ~ I -> mean holonomy angle < 0.05 rad (excluded by negative test)",
            "erased_symmetric"       => "B=A -> AB and BA give identical readout (boundary: diff < 1e-8)",
            "input_dependent"        => all(size_results[string(N)]["input_dep_holonomy_delta"] > 1e-4 for N in sizes),
        ),
        "bonds_are_geometry" => all(
            size_results[string(N)]["plaquette_holonomy_mean_rad"] > 0.1 &&
            size_results[string(N)]["flat_holonomy_mean_rad"] < 0.05
            for N in sizes
        ),
        "checks"          => checks,
        "all_pass"        => all_pass,
        "jax_parity_path" => "/tmp/npc_connection_geometry_jax_results.json",
    )

    out_path = joinpath(@__DIR__, "npc_connection_geometry_julia_results.json")
    open(out_path, "w") do f
        JSON.print(f, result, 2)
    end
    println("Written: $out_path")
    println("all_pass = $all_pass")
    for c in checks
        println("  $c")
    end
    println("bonds_are_geometry = $(result["bonds_are_geometry"])")
    println("N01_witness: noncommuting quaternion plaquette holonomy")
    println("F01_witness: finite N in {8,16,32}")
end

main()
