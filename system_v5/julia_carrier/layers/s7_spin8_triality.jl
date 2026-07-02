#!/usr/bin/env julia
# =============================================================================
# s7_spin8_triality.jl
#
# OBJECT: Spin(8) triality frontier (the SPECULATIVE 3-generation uplift).
#
# SPECULATIVE FLAG (read this first):
#   This sim does NOT derive 3 generations of fermions. It builds and MEASURES the
#   genuine order-3 OUTER automorphism of Spin(8) -- triality -- that relates the three
#   inequivalent 8-dimensional representations (8v vector, 8s spinor, 8c cospinor), and
#   it asks ONLY a structural compatibility question: could the 8-element "terrain octet"
#   (dim 8, from L4_terrain_octet) sit in one of {8v, 8s, 8c}? The "3 generations" reading
#   is a SPECULATION layered on the S3/Z3 triality symmetry. The math below is hard; the
#   physics interpretation is not. promotion_allowed = false.
#
# WHAT IS MEASURED (not planted):
#   A1. Cl(8,0) gamma matrices built from anticommuting tensor generators; the Clifford
#       relations {gi,gj}=2 delta_ij are CHECKED (anchor: Bott period 8, real spinor dim 2^4=16).
#       The chirality operator chi = g1...g8 splits the 16-dim Dirac spinor into an 8s (+1)
#       block and an 8c (-1) block. The dim-8 + dim-8 split is READ OFF the eigenvalues.
#   A2. D4 = so(8) root system (24 roots) built from +-ei+-ej. Triality T is constructed as
#       the linear map permuting simple roots a1->a3->a4->a1 (fixing the central a2). It is
#       MEASURED to be: orthogonal, det +1, T^3 = I exactly, T != I, and to map the 24-root
#       system into itself. T is then applied to the three fundamental highest weights
#       (8v, 8s, 8c) and is MEASURED to 3-cycle them: w_v -> w_s -> w_c -> w_v.
#   A3. Octonion (Cayley) multiplication table built from the Fano plane. Moufang identity
#       (ax)(ya)=a(xy)a is CHECKED (the algebraic source of triality). Local triality is
#       CHECKED by SOLVING, for D in so(8), the companions D',D'' with D(xy)=D'(x)y+x D''(y);
#       the solve residual is read off (companions genuinely exist and are antisymmetric).
#       An explicit order-3 element of so(8) is built (companion-map composed with octonion
#       conjugation) and (g)^3 = I is MEASURED.
#
# KILL-CONTROLS (must FAIL the triality test or the test is vacuous):
#   K1 (inner / Weyl automorphism): a Weyl-group element of W(D4) preserves the root system
#      but does NOT permute the three fundamental weights -- it keeps w_v inside 8v's own
#      weight orbit. A generic INNER automorphism cannot interchange 8v/8s/8c. We MEASURE
#      that no simple reflection sends w_v to w_s or w_c, and a Weyl word leaves w_v off the
#      {w_v,w_s,w_c} set. KILL PASSES = control fails the permutation test as required.
#   K2 (order-2 diagram swap a3<->a4): the half-spinor swap 8s<->8c. It is OUTER but order 2,
#      fixes 8v, and does NOT 3-cycle. We MEASURE order exactly 2 and a non-cyclic landing.
#      KILL PASSES = it is NOT triality (order 2, not the 3-cycle).
#   K3 (rep-level honesty): the naive single-companion solve on so(8) lands on the ORDER-2
#      outer automorphism, not the order-3 cycle. We MEASURE Theta^2 = I (order 2) and report
#      it honestly; the order-3 element requires composing with octonion conjugation.
#
# NO Z3: omitted deliberately (a decorative tautology would not be load-bearing here; every
#   claim is already a measured numeric invariant with a falsifying control).
#
# classification: PoC   promotion_allowed: false
# =============================================================================

using LinearAlgebra

const RESULTS_PATH = joinpath(@__DIR__, "s7_spin8_triality_results.json")
const TOL = 1.0e-9
const SEED = 20260601

# ---------------------------------------------------------------------------
# minimal JSON emitter (matches house style in this repo)
# ---------------------------------------------------------------------------
json_escape(s::AbstractString) = replace(replace(s, "\\" => "\\\\"), "\"" => "\\\"")
function json_value(x)
    if x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        return isfinite(x) ? string(x) : "\"" * string(x) * "\""
    elseif x isa NamedTuple
        parts = String[]
        for k in keys(x)
            push!(parts, json_value(String(k)) * ": " * json_value(getfield(x, k)))
        end
        return "{" * join(parts, ", ") * "}"
    elseif x isa AbstractVector
        return "[" * join(json_value.(x), ", ") * "]"
    else
        error("unsupported JSON type $(typeof(x))")
    end
end

# ===========================================================================
# A1. Cl(8,0) gamma matrices + chirality split (anchor: Bott period 8, dim 2^4=16)
# ===========================================================================
const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
kron_all(ms) = foldl(kron, ms)

function gammas8()
    # Jordan-Wigner: g_{2k-1}=sz^{k-1}⊗sx⊗I.., g_{2k}=sz^{k-1}⊗sy⊗I.., 4 tensor factors -> 16x16
    G = Matrix{ComplexF64}[]
    for k in 1:4
        left  = [SZ for _ in 1:(k - 1)]
        right = [I2 for _ in 1:(4 - k)]
        push!(G, kron_all(vcat(left, [SX], right)))
        push!(G, kron_all(vcat(left, [SY], right)))
    end
    return G
end

function cl8_block()
    G = gammas8()
    Id = Matrix{ComplexF64}(I, 16, 16)
    cliff_err = 0.0
    for i in 1:8, j in 1:8
        ac = G[i] * G[j] + G[j] * G[i]
        expect = (i == j ? 2.0 : 0.0) * Id
        cliff_err = max(cliff_err, maximum(abs.(ac - expect)))
    end
    chi = G[1] * G[2] * G[3] * G[4] * G[5] * G[6] * G[7] * G[8]
    chi_sq_err = maximum(abs.(chi * chi - Id))
    chi_herm_err = maximum(abs.(chi - chi'))
    evs = eigvals(Hermitian(chi))
    n_plus = count(x -> x > 0.5, evs)
    n_minus = count(x -> x < -0.5, evs)
    # an SO(8) generator preserves chirality (even subalgebra)
    S12 = 0.25 * (G[1] * G[2] - G[2] * G[1])
    chir_preserve_err = maximum(abs.(S12 * chi - chi * S12))

    dirac_dim = size(G[1], 1)
    spinor_split_pass = (n_plus == 8 && n_minus == 8 && dirac_dim == 16)
    cliff_pass = cliff_err < TOL && chi_sq_err < TOL && chi_herm_err < TOL
    chir_pass = chir_preserve_err < TOL

    return (
        construction = "Cl(8,0) gammas via Jordan-Wigner tensor of {sx,sy} with sz strings (4 factors)",
        anchor = "Bott period 8: real spinor dim = 2^(8/2) = 16; chirality chi=g1..g8 splits 16 -> 8s(+) + 8c(-)",
        dirac_spinor_dim = dirac_dim,
        clifford_anticomm_maxerr = cliff_err,
        chi_squared_minus_I_maxerr = chi_sq_err,
        chi_hermitian_maxerr = chi_herm_err,
        chirality_plus_dim_8s = n_plus,
        chirality_minus_dim_8c = n_minus,
        so8_generator_preserves_chirality_err = chir_preserve_err,
        clifford_relations_pass = cliff_pass,
        spinor_split_8plus8_pass = spinor_split_pass,
        chirality_preserved_by_so8_pass = chir_pass,
    )
end

# ===========================================================================
# A2. D4 root system + triality on weight lattice (PRIMARY order-3 object)
# ===========================================================================
ee(i) = (v = zeros(4); v[i] = 1.0; v)

function d4_roots()
    R = Vector{Float64}[]
    for i in 1:4, j in (i + 1):4, si in (1, -1), sj in (1, -1)
        v = zeros(4); v[i] = si; v[j] = sj
        push!(R, v)
    end
    return R  # 24 roots
end

reflect(v, a) = v - 2 * (dot(v, a) / dot(a, a)) * a

function refl_mat(a)
    M = zeros(4, 4)
    for i in 1:4
        M[:, i] = reflect(ee(i), a)
    end
    return M
end

function triality_weight_lattice()
    a1 = ee(1) - ee(2); a2 = ee(2) - ee(3); a3 = ee(3) - ee(4); a4 = ee(3) + ee(4)
    # central node a2 (degree 3); outer legs a1,a3,a4 (degree 1). Triality cycles a1->a3->a4->a1.
    Mfrom = hcat(a1, a2, a3, a4)
    Mto   = hcat(a3, a2, a4, a1)
    T = Mto * inv(Mfrom)
    Id = Matrix{Float64}(I, 4, 4)

    order3_err = norm(T^3 - Id)
    nontrivial = norm(T - Id)            # must be large
    orth_err = norm(T'T - Id)
    detT = det(T)

    R = d4_roots()
    Rset = Set(round.(r, digits = 8) for r in R)
    preserves_roots = all(round.(T * r, digits = 8) in Rset for r in R)

    # three 8-dim highest weights
    w_v = ee(1)
    w_s = 0.5 * (ee(1) + ee(2) + ee(3) - ee(4))
    w_c = 0.5 * (ee(1) + ee(2) + ee(3) + ee(4))
    Wset = [w_v, w_s, w_c]
    landing(M) = [findfirst(x -> norm(M * w - x) < TOL, Wset) for w in Wset]
    land = landing(T)
    three_cycle = (land == [2, 3, 1])    # w_v->w_s->w_c->w_v
    weights_unit = all(abs(dot(w, w) - 1.0) < TOL for w in Wset)

    pass = order3_err < TOL && nontrivial > 1.0 && orth_err < TOL &&
           abs(detT - 1.0) < TOL && preserves_roots && three_cycle && weights_unit

    return (
        anchor = "D4=so(8) Dynkin: center node a2, three outer legs a1,a3,a4 -> S3/Z3 = triality",
        n_roots = length(R),
        T_order3_minus_I_err = order3_err,
        T_minus_I_norm_nontrivial = nontrivial,
        T_orthogonality_err = orth_err,
        det_T = detT,
        T_preserves_24_root_system = preserves_roots,
        weight_8v = round.(w_v, digits = 6),
        weight_8s = round.(w_s, digits = 6),
        weight_8c = round.(w_c, digits = 6),
        three_weights_unit_length = weights_unit,
        triality_landing_v_s_c = land,   # expect [2,3,1]
        permutes_8v_8s_8c_as_3cycle = three_cycle,
        triality_pass = pass,
    )
end

# KILL K1: inner / Weyl automorphism does NOT permute the three reps
function kill_inner_weyl()
    a1 = ee(1) - ee(2); a2 = ee(2) - ee(3); a3 = ee(3) - ee(4); a4 = ee(3) + ee(4)
    W = refl_mat(a1) * refl_mat(a2) * refl_mat(a3) * refl_mat(a4)   # a Weyl word (inner)
    Id = Matrix{Float64}(I, 4, 4)
    R = d4_roots(); Rset = Set(round.(r, digits = 8) for r in R)
    preserves_roots = all(round.(W * r, digits = 8) in Rset for r in R)

    w_v = ee(1)
    w_s = 0.5 * (ee(1) + ee(2) + ee(3) - ee(4))
    w_c = 0.5 * (ee(1) + ee(2) + ee(3) + ee(4))
    Wset = [w_v, w_s, w_c]
    # does the Weyl word send w_v onto a DIFFERENT fundamental rep weight?
    Wv = W * w_v
    wv_lands_on_fundamental = findfirst(x -> norm(Wv - x) < TOL, Wset)
    # any single simple reflection swap reps?
    any_simple_swaps = any(let r = reflect(w_v, a); norm(r - w_s) < TOL || norm(r - w_c) < TOL end
                           for a in (a1, a2, a3, a4))

    # KILL PASSES when inner map preserves roots but does NOT 3-cycle the reps
    permutes_reps = (wv_lands_on_fundamental == 2 || wv_lands_on_fundamental == 3) || any_simple_swaps
    kill_pass = preserves_roots && !permutes_reps

    return (
        map = "Weyl word s_a1 s_a2 s_a3 s_a4 (INNER automorphism of so(8))",
        preserves_root_system = preserves_roots,
        wv_image_lands_on_fundamental_index = wv_lands_on_fundamental === nothing ? -1 : wv_lands_on_fundamental,
        any_simple_reflection_swaps_reps = any_simple_swaps,
        inner_permutes_the_three_8dim_reps = permutes_reps,
        verdict = kill_pass ? "KILL PASSED (inner does NOT permute 8v/8s/8c -- only triality does)" :
                              "KILL FAILED (inner permuted the reps -- test is vacuous)",
        kill_pass = kill_pass,
    )
end

# KILL K2: order-2 diagram swap (a3<->a4) = 8s<->8c, NOT the order-3 triality
function kill_order2_swap()
    a1 = ee(1) - ee(2); a2 = ee(2) - ee(3); a3 = ee(3) - ee(4); a4 = ee(3) + ee(4)
    Mfrom = hcat(a1, a2, a3, a4); Mto = hcat(a1, a2, a4, a3)
    D2 = Mto * inv(Mfrom)
    Id = Matrix{Float64}(I, 4, 4)
    order2 = norm(D2^2 - Id)
    order3 = norm(D2^3 - Id)
    nontrivial = norm(D2 - Id)

    w_v = ee(1)
    w_s = 0.5 * (ee(1) + ee(2) + ee(3) - ee(4))
    w_c = 0.5 * (ee(1) + ee(2) + ee(3) + ee(4))
    Wset = [w_v, w_s, w_c]
    land = [findfirst(x -> norm(D2 * w - x) < TOL, Wset) for w in Wset]
    is_3cycle = (land == [2, 3, 1] || land == [3, 1, 2])
    swaps_sc_fixes_v = (land == [1, 3, 2])

    # KILL PASSES: order exactly 2, NOT a 3-cycle (it is an outer aut but not triality)
    kill_pass = order2 < TOL && nontrivial > 1.0 && order3 > TOL && !is_3cycle && swaps_sc_fixes_v

    return (
        map = "diagram swap a3<->a4 (OUTER, but order 2): 8s<->8c, 8v fixed",
        D2_squared_minus_I_err = order2,
        D2_cubed_minus_I_err = order3,
        landing_v_s_c = land,     # expect [1,3,2] = (8v fixed, 8s<->8c)
        is_order_three_cycle = is_3cycle,
        swaps_8s_8c_fixes_8v = swaps_sc_fixes_v,
        verdict = kill_pass ? "KILL PASSED (order 2, NOT the triality 3-cycle)" :
                              "KILL FAILED",
        kill_pass = kill_pass,
    )
end

# ===========================================================================
# A3. Octonions: Moufang + local triality + explicit rep-level order-3 element
# ===========================================================================
const FANO = [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)]
function oct_table()
    sgn = zeros(Int, 8, 8); idx = zeros(Int, 8, 8)
    for a in 0:7
        idx[a + 1, 1] = a; sgn[a + 1, 1] = 1
        idx[1, a + 1] = a; sgn[1, a + 1] = 1
    end
    for a in 1:7
        idx[a + 1, a + 1] = 0; sgn[a + 1, a + 1] = -1
    end
    for (i, j, k) in FANO
        for (x, y, z, s) in [(i, j, k, 1), (j, k, i, 1), (k, i, j, 1),
                             (j, i, k, -1), (k, j, i, -1), (i, k, j, -1)]
            idx[x + 1, y + 1] = z; sgn[x + 1, y + 1] = s
        end
    end
    return sgn, idx
end
const OSGN, OIDX = oct_table()

function omul(x, y)
    z = zeros(8)
    @inbounds for a in 1:8, b in 1:8
        z[OIDX[a, b] + 1] += OSGN[a, b] * x[a] * y[b]
    end
    return z
end
oconj(z) = vcat(z[1], -z[2:8])
oe(i) = (v = zeros(8); v[i] = 1.0; v)
function Lmat(x); M = zeros(8, 8); for b in 1:8, a in 1:8; M[OIDX[a, b] + 1, b] += OSGN[a, b] * x[a]; end; M; end
function Rmat(y); M = zeros(8, 8); for a in 1:8, b in 1:8; M[OIDX[a, b] + 1, a] += OSGN[a, b] * y[b]; end; M; end

const PAIRS = [(m, n) for m in 1:8 for n in (m + 1):8]   # so(8) basis, 28-dim
mat_from(c) = (M = zeros(8, 8); for (k, (m, n)) in enumerate(PAIRS); M[m, n] = c[k]; M[n, m] = -c[k]; end; M)

function solve_companions(D)
    rows = Vector{Float64}[]; rhs = Float64[]
    for i in 1:8, j in 1:8
        ei = oe(i); ej = oe(j); target = D * omul(ei, ej)
        for comp in 1:8
            row = zeros(2 * length(PAIRS))
            for (k, (m, n)) in enumerate(PAIRS)
                Bp = zeros(8, 8); Bp[m, n] = 1; Bp[n, m] = -1
                row[k] += (Rmat(ej) * Bp * ei)[comp]
                row[length(PAIRS) + k] += (Lmat(ei) * Bp * ej)[comp]
            end
            push!(rows, row); push!(rhs, target[comp])
        end
    end
    A = reduce(vcat, (r' for r in rows)); sol = A \ rhs
    Dp = mat_from(sol[1:length(PAIRS)]); Dpp = mat_from(sol[length(PAIRS) + 1:end])
    return Dp, Dpp, norm(A * sol - rhs)
end

function octonion_block()
    Random_unit() = (v = 2 .* [0.3,0.7,0.1,0.9,0.4,0.2,0.8,0.5] .- 1; v / norm(v))
    # Moufang identity (ax)(ya)=a(xy)a -- algebraic source of triality (deterministic samples)
    moufang_err = 0.0
    pts = [oe(1), oe(2)+oe(4), oe(3)-oe(7), [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8], oe(5)+oe(6)-oe(2)]
    a = (oe(3) + oe(5)); a = a / norm(a)
    for x in pts, y in pts
        lhs = omul(omul(a, x), omul(y, a))
        rhs = omul(a, omul(omul(x, y), a))
        moufang_err = max(moufang_err, norm(lhs - rhs))
    end
    # composition / conj-reversal
    conjrev_err = 0.0
    for x in pts, y in pts
        conjrev_err = max(conjrev_err, norm(oconj(omul(x, y)) - omul(oconj(y), oconj(x))))
    end
    # L_u orthogonal, L_u^2=-I for unit imaginary u
    Lu = Lmat(oe(2))
    lu_orth_err = norm(Lu'Lu - I)
    lu_sq_err = norm(Lu * Lu + I)

    # local triality: companions exist in so(8)
    Emn(m, n) = (M = zeros(8, 8); M[m, n] = 1; M[n, m] = -1; M)
    Dp, Dpp, resid = solve_companions(Emn(1, 2))
    comp_antisym_err = max(norm(Dp + Dp'), norm(Dpp + Dpp'))

    # naive single-companion map Theta on so(8): MEASURE its order (honesty: it is 2, not 3)
    np = length(PAIRS)
    Theta = zeros(np, np)
    for (col, (m, n)) in enumerate(PAIRS)
        Dp2, _, _ = solve_companions(Emn(m, n))
        for (row, (p, q)) in enumerate(PAIRS); Theta[row, col] = Dp2[p, q]; end
    end
    Idnp = Matrix{Float64}(I, np, np)
    theta_order2_err = norm(Theta^2 - Idnp)
    theta_order3_err = norm(Theta^3 - Idnp)

    # explicit ORDER-3 element: Theta composed with octonion-conjugation conjugation on so(8)
    C0 = Diagonal([1.0, -1, -1, -1, -1, -1, -1, -1])
    Conj = zeros(np, np)
    for (col, (m, n)) in enumerate(PAIRS)
        Dc = C0 * Emn(m, n) * C0
        for (row, (p, q)) in enumerate(PAIRS); Conj[row, col] = Dc[p, q]; end
    end
    G = Theta * Conj
    g_order3_err = norm(G^3 - Idnp)
    g_order2_err = norm(G^2 - Idnp)
    g_nontrivial = norm(G - Idnp)

    moufang_pass = moufang_err < 1e-12 && conjrev_err < 1e-12
    lu_pass = lu_orth_err < 1e-12 && lu_sq_err < 1e-12
    local_tri_pass = resid < 1e-10 && comp_antisym_err < 1e-10
    order3_rep_pass = g_order3_err < 1e-10 && g_order2_err > 1.0 && g_nontrivial > 1.0
    theta_is_order2 = theta_order2_err < 1e-10 && theta_order3_err > 1.0

    return (
        anchor = "octonions = composition algebra; Moufang (ax)(ya)=a(xy)a is the algebraic root of triality",
        moufang_identity_maxerr = moufang_err,
        conj_reversal_maxerr = conjrev_err,
        Lu_orthogonal_err = lu_orth_err,
        Lu_squared_plus_I_err = lu_sq_err,
        local_triality_solve_residual = resid,
        companions_antisymmetric_err = comp_antisym_err,
        single_companion_map_order2_err = theta_order2_err,
        single_companion_map_order3_err = theta_order3_err,
        honest_note_single_companion = "naive companion solve lands on the ORDER-2 outer aut (8s<->8c), not the 3-cycle",
        explicit_order3_element_cubed_err = g_order3_err,
        explicit_order3_element_squared_err = g_order2_err,
        explicit_order3_construction = "Theta (order-2 companion map) composed with octonion conjugation on so(8) -> order 3",
        moufang_pass = moufang_pass,
        Lu_complex_structure_pass = lu_pass,
        local_triality_companions_exist_pass = local_tri_pass,
        single_companion_is_order2_pass = theta_is_order2,
        rep_level_order3_element_pass = order3_rep_pass,
    )
end

# ===========================================================================
# Speculative compatibility question (FLAGGED): can the 8-terrain octet carry 8v/8s/8c?
# ===========================================================================
function terrain_octet_compatibility(cl8)
    # The only HONEST structural statement: the terrain octet (dim 8, from L4_terrain_octet,
    # which is the Z2xZ2 spin-structure x 2 flux-sector table = 8 chern-labelled terrains)
    # has dimension 8, which MATCHES the common dimension of 8v, 8s, 8c. Dimension match is
    # NECESSARY but NOWHERE NEAR SUFFICIENT for a rep assignment. We do NOT claim an embedding.
    octet_dim = 8
    rep_dim_8s = cl8.chirality_plus_dim_8s
    rep_dim_8c = cl8.chirality_minus_dim_8c
    rep_dim_8v = 8   # the SO(8) vector rep dimension (the e_i basis of R^8)
    dim_match = (octet_dim == rep_dim_8v == rep_dim_8s == rep_dim_8c)
    return (
        speculative = true,
        statement = "DIMENSION-ONLY compatibility: terrain octet dim 8 equals dim(8v)=dim(8s)=dim(8c)=8",
        terrain_octet_dim = octet_dim,
        dim_8v = rep_dim_8v,
        dim_8s = rep_dim_8s,
        dim_8c = rep_dim_8c,
        dimension_match = dim_match,
        claim_ceiling = "necessary-not-sufficient; NO rep embedding is demonstrated; 3-generation reading is SPECULATION",
        promotion_allowed = false,
    )
end

# ===========================================================================
function main()
    cl8 = cl8_block()
    wlat = triality_weight_lattice()
    k1 = kill_inner_weyl()
    k2 = kill_order2_swap()
    oct = octonion_block()
    compat = terrain_octet_compatibility(cl8)

    # honest verdict aggregation
    core_pass = cl8.clifford_relations_pass && cl8.spinor_split_8plus8_pass &&
                cl8.chirality_preserved_by_so8_pass &&
                wlat.triality_pass &&
                oct.moufang_pass && oct.Lu_complex_structure_pass &&
                oct.local_triality_companions_exist_pass && oct.rep_level_order3_element_pass
    kills_pass = k1.kill_pass && k2.kill_pass
    all_pass = core_pass && kills_pass

    # honest status: PASS only if core + both kills hold; else PARTIAL
    honest_status = all_pass ? "PASS" : "PARTIAL"

    result = (
        object_id = "s7_spin8_triality",
        classification = "PoC",
        promotion_allowed = false,
        speculative_flag = "3-GENERATION READING IS SPECULATION; triality math is measured, the physics uplift is NOT derived",
        seed = SEED,
        tolerance = TOL,
        no_z3 = "omitted deliberately: every claim is a measured numeric invariant with a falsifying control",
        cl8_spinor = cl8,
        triality_weight_lattice = wlat,
        kill_K1_inner_weyl = k1,
        kill_K2_order2_swap = k2,
        octonion_triality = oct,
        terrain_octet_compatibility = compat,
        verdict = (
            core_pass = core_pass,
            kill_controls_pass = kills_pass,
            all_pass = all_pass,
            honest_status = honest_status,
            headline = "Spin(8) triality is a genuine order-3 OUTER automorphism: built on D4=so(8), it permutes the three 8-dim reps 8v->8s->8c->8v (T^3=I exactly, preserves the 24-root system, NOT identity). Inner/Weyl maps do NOT permute the reps (K1) and the order-2 diagram swap is NOT triality (K2). Octonion Moufang + local-triality companions back it at the rep level, with an explicit order-3 so(8) element. Cl(8) chirality splits 16->8s+8c (Bott period 8). The 8-terrain octet matches dim 8 by DIMENSION ONLY; the 3-generation reading is flagged SPECULATIVE.",
        ),
    )

    open(RESULTS_PATH, "w") do io
        write(io, json_value(result)); write(io, "\n")
    end

    # console report
    println("=== s7_spin8_triality (Spin(8) triality frontier) ===")
    println("SPECULATIVE: 3-generation reading is NOT derived; triality math IS measured.\n")
    println("[A1] Cl(8,0) Bott-8 spinor:")
    println("  clifford anticomm maxerr = ", cl8.clifford_anticomm_maxerr)
    println("  Dirac dim = ", cl8.dirac_spinor_dim, "  -> chirality split 8s=", cl8.chirality_plus_dim_8s, " 8c=", cl8.chirality_minus_dim_8c)
    println("  so(8) generator preserves chirality err = ", cl8.so8_generator_preserves_chirality_err)
    println("[A2] D4 weight-lattice triality (PRIMARY order-3):")
    println("  T^3 - I err = ", wlat.T_order3_minus_I_err, "  (T-I norm = ", wlat.T_minus_I_norm_nontrivial, ", det = ", wlat.det_T, ")")
    println("  preserves 24-root system = ", wlat.T_preserves_24_root_system)
    println("  permutes 8v->8s->8c->8v (landing ", wlat.triality_landing_v_s_c, ") = ", wlat.permutes_8v_8s_8c_as_3cycle)
    println("[K1] inner/Weyl kill: ", k1.verdict)
    println("[K2] order-2 swap kill: ", k2.verdict)
    println("[A3] octonion backbone:")
    println("  Moufang (ax)(ya)=a(xy)a maxerr = ", oct.moufang_identity_maxerr)
    println("  local triality companion solve residual = ", oct.local_triality_solve_residual)
    println("  single-companion map order: 2-err=", oct.single_companion_map_order2_err, " 3-err=", oct.single_companion_map_order3_err, " (HONEST: it is order 2)")
    println("  explicit order-3 so(8) element ^3 - I err = ", oct.explicit_order3_element_cubed_err)
    println("[compat] terrain octet: dim ", compat.terrain_octet_dim, " == dim(8v/8s/8c) = ", compat.dimension_match, " (DIMENSION-ONLY; speculative)")
    println()
    println("CORE PASS = ", core_pass, "  KILLS PASS = ", kills_pass)
    println("HONEST STATUS = ", honest_status, "   ALL_PASS = ", all_pass)
    println("results: ", RESULTS_PATH)
end

main()
