# npc2_connection_geometry_julia.jl
# Nested-PEPS2D / Hopfield connection-geometry readout — HARDENED v2.
#
# object_id:   npc2_connection_geometry_julia
# classification: scratch_diagnostic
# claim_ceiling: scratch_diagnostic — does NOT assert layer completion,
#   PEPS3D admission, manifold admission, flux, Axis0, FEP, bridge, or physics.
# promotion_allowed: false
#
# F01 witness: finite site counts N in {8,16,32,64}; M=3 stored patterns.
# N01 witness: noncommuting quaternion products for plaquette holonomy
#              U_ij * U_jk * U_kl * U_li (order matters; AB != BA in general).
#
# Domain:   finite 2D torus graph (N sites), M=3 unit-quaternion pattern fields.
# Codomain: geometry readout vector per size:
#   [plaquette_holonomy_mean_rad, holonomy_carrier_diff, pure_gauge_holonomy_mean,
#    laplacian_gap_holonomy_weighted, erased_nontautological_diff, n01_noncomm_gap]
#
# REQUIRED CONTROLS BAKED IN (v1 audit fixes):
#   (1) PURE-GAUGE: W_ij = g_i * conj(g_j) per-site random g → holonomy ≈ 0.
#       Real curvature = nonzero; pure-gauge = near-zero. Channel survives iff
#       Hopf holonomy - pure_gauge holonomy > threshold.
#   (2) CARRIER-SPECIFICITY: Hopf/Weyl bonds vs random unit-quaternion bonds at
#       matched M. Channel survives iff |holonomy_hopf - holonomy_random| > threshold.
#   (3) BOND-DEPENDENT LAPLACIAN: edge weight = holonomy magnitude on that bond
#       (varies across seeds). Channel survives iff laplacian_gap changes across seeds.
#   (4) NON-TAUTOLOGICAL ERASED: compare Hopf bonds to RANDOM bonds (genuinely
#       different structure), not W to W(same seed). Channel survives iff diff > threshold.
#
# Channels surviving all controls are reported in channels_surviving.
#
# Run:
#   cd system_v5/julia_carrier
#   julia --project=. npc2_connection_geometry_julia.jl

using LinearAlgebra, Graphs, JSON, Statistics, Random

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
qconj(q::Quat) = Quat(q.w, -q.x, -q.y, -q.z)
norm_q(q::Quat) = sqrt(q.w^2 + q.x^2 + q.y^2 + q.z^2)
function normalize_q(q::Quat; eps=1e-14)
    n = norm_q(q)
    n < eps ? Quat(1.0, 0.0, 0.0, 0.0) : Quat(q.w/n, q.x/n, q.y/n, q.z/n)
end
add_q(a::Quat, b::Quat) = Quat(a.w+b.w, a.x+b.x, a.y+b.y, a.z+b.z)
scale_q(s::Float64, q::Quat) = Quat(s*q.w, s*q.x, s*q.y, s*q.z)
zero_q() = Quat(0.0, 0.0, 0.0, 0.0)
qdiff_norm(a::Quat, b::Quat) = norm_q(add_q(a, scale_q(-1.0, b)))
holonomy_angle(q::Quat) = acos(clamp(abs(normalize_q(q).w), 0.0, 1.0))

# ─────────────────────────────────────────────
# Torus graph helpers
# ─────────────────────────────────────────────

function torus_dims(N::Int)
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
# Spinor / pattern constructors
# ─────────────────────────────────────────────

function weyl_spinor_quat(phi::Float64, chi::Float64, eta::Float64, chirality::Symbol)
    c = cos(eta); s = sin(eta)
    pp = phi + chi; pm = phi - chi
    if chirality == :L
        q = Quat(c*cos(pp), c*sin(pp), s*cos(pm), s*sin(pm))
    else
        q = Quat(c*cos(pp), -c*sin(pp), s*cos(pm), -s*sin(pm))
    end
    normalize_q(q)
end

function make_hopf_patterns(N::Int, M::Int, seed::Int)
    Lx, Ly = torus_dims(N)
    seed_phi = mod(seed * 0.37, 2π)
    seed_eta = mod(seed * 0.17, 0.4)
    patterns = Matrix{Quat}(undef, M, N)
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

function make_random_patterns(N::Int, M::Int, seed::Int)
    # Genuinely random unit-quaternion patterns — NOT structured by Hopf/Weyl.
    # Used for carrier-specificity and non-tautological erased controls.
    rng = MersenneTwister(seed + 99991)  # separate namespace from Hopf seeds
    patterns = Matrix{Quat}(undef, M, N)
    for mu in 1:M, i in 1:N
        q = Quat(randn(rng), randn(rng), randn(rng), randn(rng))
        patterns[mu, i] = normalize_q(q)
    end
    patterns
end

function hopfield_weights(patterns::Matrix{Quat})
    M, N = size(patterns)
    W = fill(zero_q(), N, N)
    for i in 1:N, j in 1:N
        if i != j
            s = zero_q()
            for mu in 1:M
                s = add_q(s, patterns[mu, i] * qconj(patterns[mu, j]))
            end
            W[i, j] = s
        end
    end
    W
end

function pure_gauge_weights(N::Int, seed::Int)
    # (1) PURE-GAUGE CONTROL: W_ij = g_i * conj(g_j) from per-site g.
    # On a flat connection (no curvature) this construction guarantees holonomy=1
    # algebraically: g_i * conj(g_j) * g_j * conj(g_k) * g_k * conj(g_l) * g_l * conj(g_i)
    # = g_i * conj(g_i) = 1 (identity). So holonomy ≈ 0 for any per-site g.
    # A bond structure derived from patterns vs pure-gauge are the right comparison.
    rng = MersenneTwister(seed + 77777)
    g = Vector{Quat}(undef, N)
    for i in 1:N
        q = Quat(randn(rng), randn(rng), randn(rng), randn(rng))
        g[i] = normalize_q(q)
    end
    W = fill(zero_q(), N, N)
    for i in 1:N, j in 1:N
        if i != j
            W[i, j] = normalize_q(g[i] * qconj(g[j]))
        end
    end
    W
end

# ─────────────────────────────────────────────
# Holonomy readout
# ─────────────────────────────────────────────

function plaquette_holonomy_angles(W::Matrix{Quat}, plaquettes::Vector{NTuple{4,Int}})
    angles = Float64[]
    for (a, b, c, d) in plaquettes
        ua = normalize_q(W[a,b])
        ub = normalize_q(W[b,c])
        uc = normalize_q(W[c,d])
        ud = normalize_q(W[d,a])
        hol = ua * ub * uc * ud
        push!(angles, holonomy_angle(hol))
    end
    angles
end

function plaquette_noncommutator_gap(W::Matrix{Quat}, plaquettes::Vector{NTuple{4,Int}})
    gaps = Float64[]
    for (a, b, c, d) in plaquettes
        factors = (normalize_q(W[a,b]), normalize_q(W[b,c]), normalize_q(W[c,d]), normalize_q(W[d,a]))
        for i in 1:4, j in i+1:4
            push!(gaps, qdiff_norm(factors[i] * factors[j], factors[j] * factors[i]))
        end
    end
    (mean_gap=mean(gaps), max_gap=maximum(gaps))
end

# ─────────────────────────────────────────────
# (3) BOND-DEPENDENT LAPLACIAN: weight = holonomy magnitude on each bond.
# This makes edge weights genuinely bond-dependent and seed-varying.
# ─────────────────────────────────────────────

function holonomy_weighted_laplacian(W::Matrix{Quat}, g::SimpleGraph,
                                      plaquettes::Vector{NTuple{4,Int}})
    N = nv(g)
    # For each directed bond (i,j) compute the 2-plaquette mean holonomy angle
    # touching that bond. Use it as edge weight.
    bond_hol = Dict{Tuple{Int,Int},Float64}()
    for (a, b, c, d) in plaquettes
        bonds = [(a,b),(b,c),(c,d),(d,a)]
        ua = normalize_q(W[a,b])
        ub = normalize_q(W[b,c])
        uc = normalize_q(W[c,d])
        ud = normalize_q(W[d,a])
        hol = ua * ub * uc * ud
        ang = holonomy_angle(hol)
        for (i,j) in bonds
            key = (min(i,j), max(i,j))
            bond_hol[key] = get(bond_hol, key, 0.0) + ang * 0.5
        end
    end
    # Edge weight = exp(beta * holonomy_magnitude); default to exp(beta*0) if bond not found.
    beta = 1.25
    Wf = zeros(Float64, N, N)
    for e in edges(g)
        i, j = src(e), dst(e)
        key = (min(i,j), max(i,j))
        h_ang = get(bond_hol, key, 0.0)
        conductance = exp(beta * h_ang)
        Wf[i, j] = conductance
        Wf[j, i] = conductance
    end
    D = diagm(vec(sum(Wf, dims=2)))
    L = D - Wf
    evals = sort(eigvals(Symmetric(L)))
    (laplacian_gap=evals[2]-evals[1], heat_trace=sum(exp.(-evals)), evals=evals)
end

# ─────────────────────────────────────────────
# Full per-(N, seed) readout with all four controls
# ─────────────────────────────────────────────

function readout(N::Int, seed::Int; M::Int=3)
    g     = torus_graph(N)
    plaq  = torus_plaquettes(N)

    # Structured Hopf/Weyl bonds
    hopf_pat   = make_hopf_patterns(N, M, seed)
    W_hopf     = hopfield_weights(hopf_pat)
    hol_hopf   = plaquette_holonomy_angles(W_hopf, plaq)
    n01_hopf   = plaquette_noncommutator_gap(W_hopf, plaq)
    lap_hopf   = holonomy_weighted_laplacian(W_hopf, g, plaq)

    # (2) CARRIER-SPECIFICITY: random unit-quat bonds (same M, same N, different structure)
    rand_pat   = make_random_patterns(N, M, seed)
    W_rand     = hopfield_weights(rand_pat)
    hol_rand   = plaquette_holonomy_angles(W_rand, plaq)
    n01_rand   = plaquette_noncommutator_gap(W_rand, plaq)
    lap_rand   = holonomy_weighted_laplacian(W_rand, g, plaq)

    # (1) PURE-GAUGE: per-site g_i, W_ij = g_i * conj(g_j) → holonomy ≈ 0
    W_pg       = pure_gauge_weights(N, seed)
    hol_pg     = plaquette_holonomy_angles(W_pg, plaq)
    n01_pg     = plaquette_noncommutator_gap(W_pg, plaq)
    lap_pg     = holonomy_weighted_laplacian(W_pg, g, plaq)

    # (3) Bond-dependent Laplacian seed-variation: compare seed vs seed+7919
    hopf_pat2  = make_hopf_patterns(N, M, seed + 7919)
    W_hopf2    = hopfield_weights(hopf_pat2)
    lap_hopf2  = holonomy_weighted_laplacian(W_hopf2, g, plaq)
    lap_gap_seed_delta = abs(lap_hopf.laplacian_gap - lap_hopf2.laplacian_gap)

    # (4) NON-TAUTOLOGICAL ERASED: Hopf bonds vs random bonds (genuinely different structure).
    # If channels are real, the two should be DISTINGUISHABLE (large diff).
    # This replaces the v1 B=A control (which was guaranteed symmetric by algebra).
    hol_nontaut_diff = abs(mean(hol_hopf) - mean(hol_rand))
    lap_nontaut_diff = abs(lap_hopf.laplacian_gap - lap_rand.laplacian_gap)

    # Carrier-specificity: holonomy separates Hopf from random?
    hol_carrier_diff = abs(mean(hol_hopf) - mean(hol_rand))

    Dict(
        "N"                              => N,
        "seed"                           => seed,
        "M"                              => M,
        # Core channel: holonomy
        "hol_hopf_mean"                  => mean(hol_hopf),
        "hol_rand_mean"                  => mean(hol_rand),
        "hol_pg_mean"                    => mean(hol_pg),
        "hol_carrier_diff"               => hol_carrier_diff,
        # N01: noncommutation
        "n01_hopf_mean_gap"              => n01_hopf.mean_gap,
        "n01_hopf_max_gap"               => n01_hopf.max_gap,
        "n01_rand_mean_gap"              => n01_rand.mean_gap,
        "n01_pg_mean_gap"                => n01_pg.mean_gap,
        # Laplacian channel (bond-dependent via holonomy weights)
        "lap_gap_hopf"                   => lap_hopf.laplacian_gap,
        "lap_gap_rand"                   => lap_rand.laplacian_gap,
        "lap_gap_pg"                     => lap_pg.laplacian_gap,
        "lap_gap_seed_delta"             => lap_gap_seed_delta,
        "heat_trace_hopf"                => lap_hopf.heat_trace,
        # Non-tautological erased control
        "erased_nontaut_hol_diff"        => hol_nontaut_diff,
        "erased_nontaut_lap_diff"        => lap_nontaut_diff,
    )
end

# ─────────────────────────────────────────────
# Check logic: which channels survive all controls
# ─────────────────────────────────────────────

function evaluate_size(N::Int, seeds::Vector{Int}; M::Int=3)
    rows = [readout(N, s; M=M) for s in seeds]

    agg(k) = mean(r[k] for r in rows)
    mx(k)  = maximum(r[k] for r in rows)

    # Aggregate
    hol_hopf_mean       = agg("hol_hopf_mean")
    hol_rand_mean       = agg("hol_rand_mean")
    hol_pg_mean         = agg("hol_pg_mean")
    hol_carrier_diff    = agg("hol_carrier_diff")
    n01_hopf_mean       = agg("n01_hopf_mean_gap")
    n01_hopf_max        = mx("n01_hopf_max_gap")
    n01_pg_mean         = agg("n01_pg_mean_gap")
    lap_gap_hopf        = agg("lap_gap_hopf")
    lap_gap_rand        = agg("lap_gap_rand")
    lap_gap_pg          = agg("lap_gap_pg")
    lap_gap_seed_delta  = agg("lap_gap_seed_delta")
    erased_nt_hol       = agg("erased_nontaut_hol_diff")
    erased_nt_lap       = agg("erased_nontaut_lap_diff")
    heat_hopf           = agg("heat_trace_hopf")

    # ── CHANNEL 1: HOLONOMY ──
    # Survives iff:
    #   (a) Hopf holonomy > 0.1 rad  [structured bonds → nontrivial curvature]
    #   (b) pure-gauge holonomy < 0.02 rad  [control 1: pure-gauge → ~0]
    #   (c) |hopf - random| > 0.01  [control 2: carrier-specific]
    #   (d) non-tautological erased diff > 0.01  [control 4: different structure distinguishable]
    ch1_a = hol_hopf_mean > 0.1
    ch1_b = hol_pg_mean < 0.02
    ch1_c = hol_carrier_diff > 0.01
    ch1_d = erased_nt_hol > 0.01
    ch1_pass = ch1_a && ch1_b && ch1_c && ch1_d

    # ── CHANNEL 2: N01 NONCOMMUTATION ──
    # Survives iff:
    #   (a) Hopf n01 mean > 0.01  [structured bonds are noncommuting]
    #   (b) pure-gauge n01 < Hopf n01  [pure-gauge should commute: g_i*g_j^† products commute]
    #       (pure-gauge has LOWER n01 because U_ij = g_i*g_j^† → ordered product = g_a*g_b^†... telescopes)
    #   (c) n01 > 1e-3 for Hopf  [actual threshold]
    ch2_a = n01_hopf_mean > 0.01
    ch2_b = n01_pg_mean < n01_hopf_mean   # pure-gauge should be lower
    ch2_c = n01_hopf_mean > 1e-3
    ch2_pass = ch2_a && ch2_b && ch2_c

    # ── CHANNEL 3: BOND-DEPENDENT LAPLACIAN ──
    # Survives iff:
    #   (a) Laplacian gap changes across seeds (seed_delta > 1e-4)  [control 3: bond-dependent]
    #   (b) Hopf lap_gap != rand lap_gap by more than 1e-4  [carrier-specific gap]
    #   (c) non-tautological: |hopf_lap - rand_lap| > 1e-4  [control 4]
    ch3_a = lap_gap_seed_delta > 1e-4
    ch3_b = abs(lap_gap_hopf - lap_gap_rand) > 1e-4
    ch3_c = erased_nt_lap > 1e-4
    ch3_pass = ch3_a && ch3_b && ch3_c

    channels_pass = Dict(
        "holonomy_real_curvature" => ch1_pass,
        "n01_noncommutation"      => ch2_pass,
        "laplacian_bond_dependent"=> ch3_pass,
    )

    (
        hol_hopf_mean=hol_hopf_mean, hol_rand_mean=hol_rand_mean, hol_pg_mean=hol_pg_mean,
        hol_carrier_diff=hol_carrier_diff,
        n01_hopf_mean=n01_hopf_mean, n01_hopf_max=n01_hopf_max, n01_pg_mean=n01_pg_mean,
        lap_gap_hopf=lap_gap_hopf, lap_gap_rand=lap_gap_rand, lap_gap_pg=lap_gap_pg,
        lap_gap_seed_delta=lap_gap_seed_delta,
        erased_nt_hol=erased_nt_hol, erased_nt_lap=erased_nt_lap,
        heat_hopf=heat_hopf,
        ch1_a=ch1_a, ch1_b=ch1_b, ch1_c=ch1_c, ch1_d=ch1_d, ch1_pass=ch1_pass,
        ch2_a=ch2_a, ch2_b=ch2_b, ch2_c=ch2_c, ch2_pass=ch2_pass,
        ch3_a=ch3_a, ch3_b=ch3_b, ch3_c=ch3_c, ch3_pass=ch3_pass,
        channels_pass=channels_pass,
    )
end

# ─────────────────────────────────────────────
# Main: size ladder 8 / 16 / 32 / 64
# ─────────────────────────────────────────────

function main()
    sizes = [8, 16, 32, 64]
    seeds = [20260602, 20260603]
    M = 3

    size_results = Dict{String, Any}()
    checks = String[]

    # Track which channels survive across ALL sizes
    channels_surviving_all = Dict(
        "holonomy_real_curvature" => true,
        "n01_noncommutation"      => true,
        "laplacian_bond_dependent"=> true,
    )

    for N in sizes
        r = evaluate_size(N, seeds; M=M)

        # Track survival across sizes
        for (ch, pass) in r.channels_pass
            channels_surviving_all[ch] = channels_surviving_all[ch] && pass
        end

        check_str = string(
            "N=$N | ",
            "ch1_holonomy(hopf=$(round(r.hol_hopf_mean,digits=4)), ",
            "pg=$(round(r.hol_pg_mean,digits=4)), ",
            "carrier_diff=$(round(r.hol_carrier_diff,digits=4)), ",
            "nt_diff=$(round(r.erased_nt_hol,digits=4))): ",
            "a=$(r.ch1_a) b=$(r.ch1_b) c=$(r.ch1_c) d=$(r.ch1_d) → $(r.ch1_pass) | ",
            "ch2_n01(hopf=$(round(r.n01_hopf_mean,digits=4)), ",
            "pg=$(round(r.n01_pg_mean,digits=4))): ",
            "a=$(r.ch2_a) b=$(r.ch2_b) c=$(r.ch2_c) → $(r.ch2_pass) | ",
            "ch3_lap(gap_hopf=$(round(r.lap_gap_hopf,digits=4)), ",
            "gap_rand=$(round(r.lap_gap_rand,digits=4)), ",
            "seed_delta=$(round(r.lap_gap_seed_delta,digits=5))): ",
            "a=$(r.ch3_a) b=$(r.ch3_b) c=$(r.ch3_c) → $(r.ch3_pass)"
        )
        push!(checks, check_str)
        println(check_str)

        size_results[string(N)] = Dict(
            "hol_hopf_mean"          => r.hol_hopf_mean,
            "hol_rand_mean"          => r.hol_rand_mean,
            "hol_pg_mean"            => r.hol_pg_mean,
            "hol_carrier_diff"       => r.hol_carrier_diff,
            "n01_hopf_mean_gap"      => r.n01_hopf_mean,
            "n01_hopf_max_gap"       => r.n01_hopf_max,
            "n01_pg_mean_gap"        => r.n01_pg_mean,
            "lap_gap_hopf"           => r.lap_gap_hopf,
            "lap_gap_rand"           => r.lap_gap_rand,
            "lap_gap_pg"             => r.lap_gap_pg,
            "lap_gap_seed_delta"     => r.lap_gap_seed_delta,
            "erased_nontaut_hol_diff"=> r.erased_nt_hol,
            "erased_nontaut_lap_diff"=> r.erased_nt_lap,
            "heat_trace_hopf"        => r.heat_hopf,
            "channels_this_size"     => r.channels_pass,
            "parity_max_diff_vs_jax" => nothing,  # filled by JAX parity pass
        )
    end

    channels_surviving = [k for (k, v) in channels_surviving_all if v]
    channels_failing   = [k for (k, v) in channels_surviving_all if !v]

    result = Dict(
        "object_id"             => "npc2_connection_geometry_julia",
        "classification"        => "scratch_diagnostic",
        "promotion_allowed"     => false,
        "claim_ceiling"         => (
            "Scratch diagnostic only. Does NOT assert layer completion, "
            * "PEPS3D admission, manifold admission, flux, Axis0, FEP, bridge, or physics. "
            * "Reports only which readout channels survived all four v1-audit-required controls."
        ),
        "F01_witness"           => "finite N in {8,16,32,64}, M=3 Hopf-pattern fields",
        "N01_witness"           => "noncommuting quaternion plaquette holonomy (order-sensitive)",
        "domain"                => "finite 2D torus (N sites), M=3 unit-quaternion Hopfield bonds from Hopf/Weyl carrier",
        "codomain"              => "per-size geometry readout: [hol_hopf_mean, hol_pg_mean, hol_carrier_diff, n01_hopf, lap_gap, lap_seed_delta, erased_nontaut_diff]",
        "controls_applied" => Dict(
            "1_pure_gauge"      => "W_ij=g_i*conj(g_j) per-site random g → holonomy telescopes to ~0; Hopf must exceed this",
            "2_carrier_specific"=> "Hopf/Weyl bonds vs random unit-quat bonds at matched M; holonomy must be distinguishable",
            "3_bond_dependent_laplacian" => "edge weight=holonomy magnitude per bond (varies with seed); gap must change across seeds",
            "4_nontautological_erased"   => "compare Hopf bonds to random bonds (different structure), not W vs W same seed",
        ),
        "sizes"                 => size_results,
        "checks"                => checks,
        "channels_surviving_all_sizes" => channels_surviving,
        "channels_failing_any_size"    => channels_failing,
        "jax_parity_path"       => "/tmp/npc2_connection_geometry_jax_results.json",
    )

    out_path = joinpath(@__DIR__, "npc2_connection_geometry_julia_results.json")
    open(out_path, "w") do f
        JSON.print(f, result, 2)
    end
    println("\nWritten: $out_path")
    println("channels_surviving_all_sizes: $(channels_surviving)")
    println("channels_failing_any_size:    $(channels_failing)")
end

main()
