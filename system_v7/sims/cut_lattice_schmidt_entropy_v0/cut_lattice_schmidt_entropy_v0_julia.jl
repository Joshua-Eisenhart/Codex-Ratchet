#!/usr/bin/env julia
# cut_lattice_schmidt_entropy_v0 -- JULIA leg (advanced-geometry canon arbiter).
#
# Independent recomputation of the cut lattice + Schmidt strata + per-cut entropy for n in
# {2,3,4}. Partial trace is done by explicit BIT addressing (not column-major reshape) so the
# qubit->axis convention matches the numpy/jax/torch legs exactly. Canon/arbiter role: its
# values are the reference on divergence. No peer reads.

using LinearAlgebra
using JSON

const SIM_ID = "cut_lattice_schmidt_entropy_v0"
const HERE = @__DIR__
const RESULT = joinpath(HERE, "results", SIM_ID * "_julia_results.json")
const EIG_TOL = 1e-9

# ----- bit convention (mirror numpy reshape([2]*n)): integer index i (0-based),
# axis a (0-based, a in 0..n-1) reads bit (n-1-a) of i, where bit 0 is least significant. -----
bit_of(i, n, a) = (i >> (n - 1 - a)) & 1          # value of qubit-axis a in basis index i (0-based)

# ----- cut lattice: subsets A of 0..n-1 with 0 in A and A != full -----
function cuts(n)
    out = Vector{Vector{Int}}()
    for r in 1:(n-1)
        for A in combinations_with_zero(n, r)
            push!(out, A)
        end
    end
    out
end
function combinations_with_zero(n, r)
    res = Vector{Vector{Int}}()
    function rec(start, cur)
        if length(cur) == r
            if 0 in cur
                push!(res, copy(cur))
            end
            return
        end
        for x in start:(n-1)
            push!(cur, x); rec(x + 1, cur); pop!(cur)
        end
    end
    rec(0, Int[])
    res
end

# ----- states (0-based integer index i in 0..2^n-1 -> Julia array slot i+1) -----
basisvec(n, bits) = (v = zeros(ComplexF64, 2^n); v[bits + 1] = 1.0; v)
product_state(n) = basisvec(n, 0)
function ghz(n)
    v = zeros(ComplexF64, 2^n); v[1] = 1/sqrt(2); v[end] = 1/sqrt(2); v
end
function w_state(n)
    v = zeros(ComplexF64, 2^n)
    for q in 0:(n-1)
        v[(1 << q) + 1] = 1/sqrt(n)
    end
    v
end
function bell_pair_then_zero(n)
    v = zeros(ComplexF64, 2^n)
    v[1] = 1/sqrt(2)
    v[((1 << (n - 1)) | (1 << (n - 2))) + 1] = 1/sqrt(2)
    v
end
function max_entangled_22(n)
    @assert n == 4
    v = zeros(ComplexF64, 16)
    for k in 0:3
        v[(k * 4 + k) + 1] = 0.5
    end
    v
end

ry(t) = (c = cos(t/2); s = sin(t/2); ComplexF64[c -s; s c])

function apply1(psi, n, q, U)  # q is axis index 0-based; acts on bit (n-1-q)
    out = zeros(ComplexF64, length(psi))
    shift = n - 1 - q
    for i in 0:(length(psi)-1)
        b = (i >> shift) & 1
        i0 = i & ~(1 << shift)           # bit cleared
        i1 = i0 | (1 << shift)           # bit set
        # contribute psi[i] into the rotated pair only once (process when b==0 we read both)
        if b == 0
            out[i0 + 1] += U[1,1]*psi[i0+1] + U[1,2]*psi[i1+1]
            out[i1 + 1] += U[2,1]*psi[i0+1] + U[2,2]*psi[i1+1]
        end
    end
    out
end

function apply_cz(psi, n, a, b)  # axis indices a,b 0-based
    out = copy(psi)
    sa = n - 1 - a; sb = n - 1 - b
    for i in 0:(length(psi)-1)
        if ((i >> sa) & 1) == 1 && ((i >> sb) & 1) == 1
            out[i + 1] *= -1
        end
    end
    out
end

function scramble(n)
    psi = product_state(n)
    th = [0.5 + 0.9 * q for q in 0:(n-1)]
    for q in 0:(n-1)
        psi = apply1(psi, n, q, ry(th[q + 1]))
    end
    for q in 0:(n-1)
        psi = apply_cz(psi, n, q, mod(q + 1, n))
    end
    for q in 0:(n-1)
        psi = apply1(psi, n, q, ry(0.6 + 0.5 * q))
    end
    psi ./ norm(psi)
end

# ----- partial trace by explicit bit addressing -----
# rho_A[arow+1, acol+1] = sum_{bcfg} psi[idx(arow,bcfg)] * conj(psi[idx(acol,bcfg)])
function rdm(psi, n, A)
    B = [q for q in 0:(n-1) if !(q in A)]
    dA = 2^length(A); dB = 2^length(B)
    function compose(avals, bvals)  # avals: bit per axis in A; bvals: bit per axis in B
        i = 0
        for (k, ax) in enumerate(A)
            i |= (avals[k] << (n - 1 - ax))
        end
        for (k, ax) in enumerate(B)
            i |= (bvals[k] << (n - 1 - ax))
        end
        i
    end
    bits_of(x, len) = [ (x >> (len - 1 - p)) & 1 for p in 0:(len-1) ]  # MSB-first within block
    rho = zeros(ComplexF64, dA, dA)
    for arow in 0:(dA-1), acol in 0:(dA-1)
        av_r = bits_of(arow, length(A)); av_c = bits_of(acol, length(A))
        acc = 0.0 + 0.0im
        for bcfg in 0:(dB-1)
            bv = bits_of(bcfg, length(B))
            acc += psi[compose(av_r, bv) + 1] * conj(psi[compose(av_c, bv) + 1])
        end
        rho[arow + 1, acol + 1] = acc
    end
    rho
end

function schmidt_rank(rho)
    w = real.(eigvals(Hermitian(rho)))
    count(>(EIG_TOL), w)
end
function vn_entropy(rho)
    w = real.(eigvals(Hermitian(rho)))
    w = filter(>(EIG_TOL), w)
    isempty(w) ? 0.0 : (-sum(w .* log2.(w)) + 0.0)  # +0.0 normalizes -0.0 (eigenvalue 1 -> -1*log2(1))
end
function negativity(psi, n, A)
    B = [q for q in 0:(n-1) if !(q in A)]
    dA = 2^length(A); dB = 2^length(B)
    bits_of(x, len) = [ (x >> (len - 1 - p)) & 1 for p in 0:(len-1) ]
    function idx(av, bv)
        i = 0
        for (k, ax) in enumerate(A); i |= (av[k] << (n - 1 - ax)); end
        for (k, ax) in enumerate(B); i |= (bv[k] << (n - 1 - ax)); end
        i
    end
    # full rho in (a,b) basis -> partial transpose on A
    D = dA * dB
    M = zeros(ComplexF64, D, D)  # rows/cols indexed (a*dB + b)
    for ar in 0:(dA-1), br in 0:(dB-1), ac in 0:(dA-1), bc in 0:(dB-1)
        r = ar * dB + br; c = ac * dB + bc
        M[r + 1, c + 1] = psi[idx(bits_of(ar, length(A)), bits_of(br, length(B))) + 1] *
                          conj(psi[idx(bits_of(ac, length(A)), bits_of(bc, length(B))) + 1])
    end
    # partial transpose on A subsystem: swap ar <-> ac
    MT = zeros(ComplexF64, D, D)
    for ar in 0:(dA-1), br in 0:(dB-1), ac in 0:(dA-1), bc in 0:(dB-1)
        MT[(ar*dB+br)+1, (ac*dB+bc)+1] = M[(ac*dB+br)+1, (ar*dB+bc)+1]
    end
    ev = real.(eigvals(Hermitian((MT + MT') / 2)))
    sum(abs.(filter(<(0.0), ev)))
end

function profile(psi, n)
    d = Dict{String,Dict{String,Float64}}()
    for A in cuts(n)
        key = "(" * join(string.(A), ", ") * (length(A) == 1 ? ",)" : ")")
        rho = rdm(psi, n, A)
        d[key] = Dict("S" => vn_entropy(rho), "rank" => float(schmidt_rank(rho)),
                      "neg" => negativity(psi, n, A))
    end
    d
end
round9(x) = round(x; digits = 9)
function round_profile(prof)
    Dict(k => round9(v["S"]) for (k, v) in prof)
end
maxS(prof) = maximum(v["S"] for v in values(prof))

function main()
    n_cuts = Dict(n => length(cuts(n)) for n in (2, 3, 4))

    p2 = profile(product_state(2), 2)
    b2 = profile(basisvec(2, 0) ./ sqrt(2) .+ basisvec(2, 3) ./ sqrt(2), 2)
    p3 = profile(product_state(3), 3)
    g3 = profile(ghz(3), 3)
    w3 = profile(w_state(3), 3)
    bp3 = profile(bell_pair_then_zero(3), 3)
    s3 = profile(scramble(3), 3)
    g3S = round_profile(g3); w3S = round_profile(w3)
    ghz_w_gap_n3 = maximum(abs(g3[c]["S"] - w3[c]["S"]) for c in keys(g3))

    p4 = profile(product_state(4), 4)
    g4 = profile(ghz(4), 4)
    w4 = profile(w_state(4), 4)
    m4 = profile(max_entangled_22(4), 4)
    s4 = profile(scramble(4), 4)
    g4S = round_profile(g4); w4S = round_profile(w4)
    g4_vals = sort(collect(Set(round(v; digits = 6) for v in values(g4S))))
    w4_vals = sort(collect(Set(round(v; digits = 6) for v in values(w4S))))
    n4_max_cut = maxS(m4)
    n4_max_rank = Int(maximum(v["rank"] for v in values(m4)))

    function sym_dev(psi, n)
        dev = 0.0
        full = Set(0:(n-1))
        for A in cuts(n)
            B = sort(collect(setdiff(full, Set(A))))
            dev = max(dev, abs(vn_entropy(rdm(psi, n, A)) - vn_entropy(rdm(psi, n, B))))
        end
        dev
    end
    purity_dev = max(sym_dev(ghz(3), 3), sym_dev(w_state(4), 4), sym_dev(scramble(4), 4))

    # NOT load-bearing: S_AB=0 (global pure) makes both reduce to the Schmidt symmetry identity
    # S_A==S_B, which holds for ANY correct pure-state reduction. Consistency check only.
    function mi_ic(psi, n)
        ok = true
        for A in cuts(n)
            S_A = vn_entropy(rdm(psi, n, A))
            B = sort(collect(setdiff(Set(0:(n-1)), Set(A))))
            S_B = vn_entropy(rdm(psi, n, B))
            mi = S_A + S_B; ic = S_B
            ok = ok && abs(mi - 2 * S_A) < 1e-9 && abs(ic - S_A) < 1e-9
        end
        ok
    end
    mi_ic_ok = mi_ic(ghz(3), 3) && mi_ic(w_state(3), 3) && mi_ic(w_state(4), 4)

    # A/B subsystem-orientation discriminator: catches a rho_B-instead-of-rho_A swap that the
    # entropy/rank suite is blind to (pure-state Schmidt symmetry: S_A==S_B, rank_A==rank_B).
    # On the unequal cut (|A|=1, |B|=3) of the asymmetric-marginal W4 state, rho_A must be 2x2
    # (a swap returns 8x8) AND its diagonal must equal the axis-0 single-qubit marginal computed
    # independently from |psi|^2 (0.25 on |1>, asymmetric -> not an identity). Could fail.
    function subsystem_orientation()
        psi = w_state(4)
        rho_A = rdm(psi, 4, [0])
        if size(rho_A) != (2, 2)
            return (false, NaN, NaN)
        end
        probs = abs2.(psi)
        marg_pop1 = sum(probs[i + 1] for i in 0:15 if ((i >> (4 - 1)) & 1) == 1)
        rdm_pop1 = real(rho_A[2, 2])  # |1> diagonal entry (1-based slot 2)
        ok = abs(rdm_pop1 - marg_pop1) < 1e-9 && abs(marg_pop1 - 0.25) < 1e-9
        (ok, round9(rdm_pop1), round9(marg_pop1))
    end
    orient_ok, orient_rdm_pop1, orient_marg_pop1 = subsystem_orientation()

    product_neg_max = max(maximum(v["neg"] for v in values(p2)),
                          maximum(v["neg"] for v in values(p3)),
                          maximum(v["neg"] for v in values(p4)))
    schmidt_rank_product = Int(max(maximum(v["rank"] for v in values(p2)),
                                   maximum(v["rank"] for v in values(p3)),
                                   maximum(v["rank"] for v in values(p4))))

    invariants = Dict(
        "n_cuts_n2" => n_cuts[2], "n_cuts_n3" => n_cuts[3], "n_cuts_n4" => n_cuts[4],
        "n2_product_max_S" => round9(maxS(p2)),
        "n2_bell_S_cut0" => round9(b2["(0,)"]["S"]),
        "n3_product_max_S" => round9(maxS(p3)),
        "n3_ghz_profile" => g3S, "n3_w_profile" => w3S,
        "n3_ghz_w_max_gap" => round9(ghz_w_gap_n3),
        "n3_bell_cut0_S" => round9(bp3["(0,)"]["S"]),
        "n3_bell_cut01_S" => round9(bp3["(0, 1)"]["S"]),
        "n4_ghz_uniform" => (length(g4_vals) == 1 && abs(g4_vals[1] - 1.0) < 1e-9),
        "n4_w_nonuniform" => (length(w4_vals) > 1),
        "n4_w_vals" => w4_vals,
        "n4_max_cut_S" => round9(n4_max_cut), "n4_max_cut_rank" => n4_max_rank,
        "product_negativity_max" => round9(product_neg_max),
        "ghz_negativity_cut0" => round9(g3["(0,)"]["neg"]),
        "purity_symmetry_max_dev" => round9(purity_dev),
        "scramble_S_cut0_n3" => round9(s3["(0,)"]["S"]),
        "scramble_S_cut0_n4" => round9(s4["(0,)"]["S"]),
        "schmidt_rank_product" => schmidt_rank_product,
        "w4_cut0_marginal_pop1" => orient_marg_pop1,
        "w4_cut0_rdm_pop1" => orient_rdm_pop1,
    )

    log3form = log2(3) - 2/3
    tests = Dict(
        "cut_lattice_count_n2_n3_n4" => [n_cuts[2], n_cuts[3], n_cuts[4]] == [1, 3, 7],
        "product_zero_entropy_every_cut" => (invariants["n2_product_max_S"] < 1e-9 &&
            invariants["n3_product_max_S"] < 1e-9 && invariants["schmidt_rank_product"] == 1),
        "n3_ghz_all_cuts_one" => all(abs(v - 1.0) < 1e-9 for v in values(g3S)),
        "n3_w_all_cuts_log3_form" => all(abs(v - log3form) < 1e-9 for v in values(w3S)),
        "n4_ghz_uniform_one" => invariants["n4_ghz_uniform"],
        "n4_w_nonuniform_profile" => invariants["n4_w_nonuniform"],
        "max_entangled_cut_hits_log2_dim" => abs(invariants["n4_max_cut_S"] - 2.0) < 1e-9 &&
            invariants["n4_max_cut_rank"] == 4,
        "bell_pair_full_on_cut0" => abs(invariants["n2_bell_S_cut0"] - 1.0) < 1e-9,
        "subsystem_orientation_no_AB_swap" => orient_ok,
    )
    # by-construction pure-state identities -- reported, NOT gating all_tests_pass
    by_construction_identities = Dict(
        "purity_symmetry_SA_eq_SB" => invariants["purity_symmetry_max_dev"] < 1e-9,
        "mutual_coherent_pure_identities" => mi_ic_ok,
    )
    controls = Dict(
        "product_negativity_zero" => invariants["product_negativity_max"] < 1e-9,
        "entangled_vs_separable_divergence" => (g3["(0,)"]["S"] - p3["(0,)"]["S"]) > 0.5,
        "ghz_vs_w_profile_divergence" => (invariants["n3_ghz_w_max_gap"] > 0.05 &&
            invariants["n4_w_nonuniform"]),
        "bell_pair_cut_dependence" => (abs(invariants["n3_bell_cut0_S"] - 1.0) < 1e-9 &&
            invariants["n3_bell_cut01_S"] < 1e-9),
        "scramble_moves_entropy" => (invariants["scramble_S_cut0_n3"] > 0.1 &&
            invariants["scramble_S_cut0_n4"] > 0.1),
        "max_cut_hits_ceiling" => abs(invariants["n4_max_cut_S"] - 2.0) < 1e-9,
        "ghz_negativity_nonzero" => invariants["ghz_negativity_cut0"] > 0.1,
    )
    all_tests = all(values(tests)); all_controls = all(values(controls))

    result = Dict(
        "schema" => "codex_ratchet.sim_result.v1", "sim_id" => SIM_ID,
        "classification" => "scratch_diagnostic", "promotion_allowed" => false,
        "formal_admission_allowed" => false, "engine" => "julia_linearalgebra_canon",
        "root_lineage" => Dict("F01_finite_support" => true,
            "N01_order_sensitivity" => "the cut lattice is the order-of-partition structure; per-cut entropy is a distinguishability readout S/~ over the bipartition, not a forward dynamic"),
        "source_target" => "manifold-tower L8/L9/L10 cut-lattice + Schmidt strata + per-cut entropy",
        "claim" => "the cut lattice of n-qubit pure states (n=2,3,4) admits per-cut Schmidt-rank/entropy/negativity readouts whose STATE-DEPENDENT discriminators hold and could have come out otherwise",
        "support_parameters" => Dict("n_values" => [2, 3, 4], "cut_counts" => [n_cuts[2], n_cuts[3], n_cuts[4]]),
        "invariants" => invariants, "tests" => tests,
        "by_construction_identities" => by_construction_identities, "controls" => controls,
        "all_tests_pass" => all_tests, "all_controls_pass" => all_controls,
        "ablation_outcome_delta" => Dict(
            "product_S_cut0" => round9(p3["(0,)"]["S"]),
            "ghz_S_cut0" => round9(g3["(0,)"]["S"]),
            "delta" => round9(g3["(0,)"]["S"] - p3["(0,)"]["S"])),
        "honest_scope" => Dict(
            "earns" => "independent Julia (canon) recomputation of the cut lattice / Schmidt strata / per-cut entropy discriminators via explicit bit-addressed partial trace; advanced-geometry arbiter leg, scratch ceiling",
            "does_not_earn" => "M(C), Axis0 closure, QIT engine, smooth manifold, physics; needs cross-engine agreement + fleet audit"),
        "TOOL_MANIFEST" => Dict("julia_linearalgebra" => Dict("tried" => true, "used" => true,
            "reason" => "complex state vectors, explicit bit-addressed partial trace, eigvals(Hermitian) for Schmidt rank + von Neumann entropy + partial-transpose negativity; canon arbiter")),
        "TOOL_INTEGRATION_DEPTH" => "load_bearing",
    )
    mkpath(dirname(RESULT))
    open(RESULT, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote $RESULT")
    println("all_tests_pass=$all_tests all_controls_pass=$all_controls")
    println("cuts n2/n3/n4 = $(n_cuts[2])/$(n_cuts[3])/$(n_cuts[4])")
    println("n3 GHZ $g3S  W $w3S  gap $ghz_w_gap_n3")
    println("n4 GHZ vals $g4_vals  W vals $w4_vals")
    println("n4 max cut S $n4_max_cut rank $n4_max_rank; product neg $product_neg_max  GHZ neg cut0 $(g3["(0,)"]["neg"])")
    println("scramble S cut0 n3/n4 = $(s3["(0,)"]["S"])/$(s4["(0,)"]["S"])")
    return (all_tests && all_controls) ? 0 : 1
end

exit(main())
