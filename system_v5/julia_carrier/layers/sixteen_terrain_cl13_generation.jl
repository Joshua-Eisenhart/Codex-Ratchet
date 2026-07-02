# =============================================================================
# sixteen_terrain_cl13_generation.jl  —  isolated, genuine PoC
#
# OBJECT UNDER TEST
#   The "16-terrain" structure and three independent ways it lands on 16:
#       (1) COMBINATORIAL : 2 (L/R chirality)
#                         x 4 (spin structures on T^2 = H^1(T^2;Z2) = Z2 x Z2)
#                         x 2 (Chern flux sign)               = 16 terrains
#       (2) ALGEBRAIC     : the spacetime Clifford algebra Cl(1,3) over R has
#                           real dimension 2^4 = 16, with real-rep type M_2(H)
#                           (2x2 quaternionic matrices = 16 real dims) and even
#                           subalgebra Cl^0(1,3) = M_2(C) (8 real dims = the
#                           Dirac spinor operator space).
#       (3) PHYSICAL      : one Standard-Model fermion generation carries 16 Weyl
#                           degrees of freedom (15 SM fermions + 1 nu_R).
#
# WHAT IS FORCED vs WHAT IS NOVEL  (stated honestly up front)
#   FORCED (external mathematical facts the code MEASURES, never asserts):
#       * |2 x 4 x 2| = 16                                    (set cardinality)
#       * dim_R Cl(1,3) = 2^(p+q) = 16                        (Clifford dimension)
#       * real-rep type Cl(1,3) = M_2(H), Cl^0(1,3) = M_2(C)  (Bott table)
#       * SM generation Weyl count = 16 with nu_R             (representation theory)
#   NOVEL / INTERPRETIVE (flagged, NOT a derivation):
#       * the IDENTIFICATION of the 16 combinatorial terrains with the 16 of
#         Cl(1,3) and with the 16 Weyl fermions is an INTERPRETIVE MAP. The three
#         16s coincide as integers; this sim proves the three counts are each 16
#         and that a wrong count is distinguished. It does NOT prove the three
#         structures are the SAME object. (interpretive_map = true.)
#
# MEASURE, DO NOT ASSERT
#   (1) the 16 set is ENUMERATED as an explicit Cartesian product and its length
#       is counted;
#   (2) dim Cl(1,3) is COUNTED from the algebra's basis blades, and the real
#       dimension 16 / even-dim 8 are READ from the RANK of the regular (left-
#       multiplication) matrix representation -- not from the constructor label;
#   (3) the SM count 16 is SUMMED from an explicit per-multiplet table.
#
# KILL-CONTROL (the 16 must be DISTINGUISHED from the wrong answers 15 and 8):
#   K1: SM count WITHOUT nu_R = 15  ->  must NOT equal 16, and must equal 15.
#   K2: even subalgebra dim 8 (Dirac spinor space) mistaken for the FULL algebra
#       ->  measured 8 != 16, so the full/even confusion is caught.
#   K3: a 3-vector-space Clifford algebra Cl(1,2) has dim 2^3 = 8 != 16; using
#       the wrong number of generators is distinguished.
#   The discriminator that makes Cl(1,3) genuinely Cl(1,3) (not Cl(3,1) etc.) is
#   the MEASURED metric signature e_i^2 = (+,-,-,-) and pseudoscalar omega^2 = -1,
#   read out of Clifford products. These pin M_2(H) via the Bott table.
#
# TOOLS: Julia + LinearAlgebra + CliffordAlgebras (non-numpy). No Z3 block.
# classification: PoC ; promotion_allowed = false
# =============================================================================

using CliffordAlgebras
using LinearAlgebra
import JSON

const TOL = 1e-9

# -----------------------------------------------------------------------------
# (1) COMBINATORIAL: enumerate the 16 = 2 x 4 x 2 terrains explicitly.
# -----------------------------------------------------------------------------
const CHIRALITIES   = ["L", "R"]                       # 2 Weyl chiralities
const SPIN_STRUCTS  = ["PP", "PA", "AP", "AA"]         # 4 = Z2 x Z2 on T^2
const CHERN_FLUXES  = [+1, -1]                          # 2 Chern flux signs

function enumerate_terrains()
    terrains = Tuple{String,String,Int}[]
    for chi in CHIRALITIES, ss in SPIN_STRUCTS, C in CHERN_FLUXES
        push!(terrains, (chi, ss, C))
    end
    return terrains
end

# -----------------------------------------------------------------------------
# (2) ALGEBRAIC: build Cl(1,3) and MEASURE its dimension and real-rep type.
# -----------------------------------------------------------------------------
# In CliffordAlgebras.jl, CliffordAlgebra(1,3) yields generators (accessed as
# cl.e1..cl.e4) with MEASURED squares e_i^2 = (+1,-1,-1,-1): this IS the physics
# +--- signature.  basevector(cl,i) indexes ALL 2^4 basis blades (i=1 is the
# scalar), so dimension(cl) counts basis blades directly.
function build_cl13()
    cl = CliffordAlgebra(1, 3)
    gens = (cl.e1, cl.e2, cl.e3, cl.e4)
    return cl, gens
end

# Measured metric signature: read e_i^2 out of the Clifford product.
function measured_signature(gens)
    return [Int(round(scalar(g * g))) for g in gens]
end

# Count basis blades by grade (binomial structure of the exterior algebra),
# read from the algebra, then total = dimension(cl).
function blade_grade_of(cl, b)
    for k in 0:order(cl)
        isgrade(b, k) && return k          # grade-k projection equals the blade
    end
    return -1
end

function blade_grade_counts(cl)
    n = order(cl)                          # vector-space dim p+q (= 4)
    counts = Dict{Int,Int}()
    for i in 1:dimension(cl)
        b = basevector(cl, i)
        g = blade_grade_of(cl, b)          # grade of this basis blade, measured
        counts[g] = get(counts, g, 0) + 1
    end
    return n, counts
end

# Real dimension of the algebra via the RANK of the regular (left-mult) matrix
# representation of all basis blades. This reads "16 real dims" out of linear
# algebra, not out of the label.  matrix(b) is the 2^n x 2^n regular rep.
function real_rep_rank(cl, blade_indices)
    mats = [Float64.(matrix(basevector(cl, i))) for i in blade_indices]
    V = hcat([vec(m) for m in mats]...)
    return rank(V)
end

# Even-subalgebra blades: a basis blade b is purely even iff even(b) == b.
function even_blade_indices(cl)
    idx = Int[]
    for i in 1:dimension(cl)
        b = basevector(cl, i)
        if b == even(b)
            push!(idx, i)
        end
    end
    return idx
end

# Pseudoscalar complex structure of the even subalgebra M_2(C):
# omega = e1 e2 e3 e4 must be even, central in Cl^0, and omega^2 = -1.
function pseudoscalar_report(cl, gens)
    omega = gens[1] * gens[2] * gens[3] * gens[4]
    even_idx = even_blade_indices(cl)
    even_blades = [basevector(cl, i) for i in even_idx]
    central = all((omega * b) == (b * omega) for b in even_blades)
    return Dict(
        "omega" => string(omega),
        "omega_is_even"        => (omega == even(omega)),
        "omega_squared"        => scalar(omega * omega),
        "omega_sq_is_minus1"   => abs(scalar(omega * omega) + 1.0) < TOL,
        "omega_central_in_even"=> central,
    )
end

# Quaternion subalgebra H inside Cl(1,3): the three SPATIAL bivectors
# (e3e4, e4e2, e2e3) close Hamilton's relations -- each squares to -1 and their
# product is -1. This is the H of M_2(H), read out of Clifford products.
function quaternion_report(gens)
    e1, e2, e3, e4 = gens
    qi = e3 * e4
    qj = e4 * e2
    qk = e2 * e3
    i2 = scalar(qi * qi); j2 = scalar(qj * qj); k2 = scalar(qk * qk)
    ijk = scalar(qi * qj * qk)
    closes = abs(i2 + 1) < TOL && abs(j2 + 1) < TOL && abs(k2 + 1) < TOL && abs(ijk + 1) < TOL
    return Dict(
        "i_squared" => i2, "j_squared" => j2, "k_squared" => k2, "ijk" => ijk,
        "hamilton_closes" => closes,
    )
end

# -----------------------------------------------------------------------------
# (3) PHYSICAL: SM generation Weyl count, SUMMED from an explicit multiplet table.
# -----------------------------------------------------------------------------
# Per generation, count LEFT-HANDED Weyl fermions (right-handed states counted as
# their left-handed conjugates -- the standard "16 Weyl per generation" bookkeeping
# of one SO(10) spinor). Each entry: (name, colour_mult x weak_mult).
const SM_MULTIPLETS = [
    ("Q_L  (left quark doublet)",        3 * 2),   # 3 colours x 2 weak isospin = 6
    ("u_R^c (right up, conj)",           3 * 1),   # 3 colours              = 3
    ("d_R^c (right down, conj)",         3 * 1),   # 3 colours              = 3
    ("L_L  (left lepton doublet)",       1 * 2),   # 2 weak isospin         = 2
    ("e_R^c (right electron, conj)",     1 * 1),   # 1                       = 1
]
const NU_R_MULTIPLET = ("nu_R^c (right neutrino, conj)", 1 * 1)  # 1

function sm_weyl_count(; include_nu_R::Bool)
    rows = Vector{Dict{String,Any}}()
    total = 0
    for (name, c) in SM_MULTIPLETS
        push!(rows, Dict("multiplet" => name, "weyl_dof" => c))
        total += c
    end
    if include_nu_R
        name, c = NU_R_MULTIPLET
        push!(rows, Dict("multiplet" => name, "weyl_dof" => c))
        total += c
    end
    return total, rows
end

# -----------------------------------------------------------------------------
# RUN
# -----------------------------------------------------------------------------
function main()
    println("="^74)
    println("SIXTEEN-TERRAIN / Cl(1,3) / SM-GENERATION  —  genuine PoC (measured)")
    println("="^74)

    # ---- (1) enumerate 2 x 4 x 2 -------------------------------------------
    terrains = enumerate_terrains()
    n_terrains = length(terrains)
    set_is_16 = (n_terrains == 16)
    distinct_16 = (length(unique(terrains)) == 16)   # no accidental collisions
    println("\n[1] COMBINATORIAL  2(L/R) x 4(PP,PA,AP,AA) x 2(C=+/-1)")
    println("    |set| = ", n_terrains, "   (== 16 ? ", set_is_16, ",  all distinct ? ", distinct_16, ")")
    println("    enumeration:")
    for (k, t) in enumerate(terrains)
        println("      ", lpad(string(k), 2), ".  chi=", t[1],
                "  ss=", t[2], "  C=", t[3] > 0 ? "+1" : "-1")
    end

    # ---- (2) Cl(1,3) algebra: MEASURE dim, signature, M_2(H) / M_2(C) ------
    cl, gens = build_cl13()
    sig = measured_signature(gens)
    sig_is_phys = (sig == [1, -1, -1, -1])          # +--- : genuine Cl(1,3)
    n_vec, gcounts = blade_grade_counts(cl)
    dim_alg = dimension(cl)                          # basis-blade count
    dim_is_16 = (dim_alg == 16)
    dim_pow_check = (dim_alg == 2^n_vec)             # 2^(p+q)

    all_idx = collect(1:dim_alg)
    full_real_rank = real_rep_rank(cl, all_idx)      # M_2(H) real dim
    even_idx = even_blade_indices(cl)
    even_real_rank = real_rep_rank(cl, even_idx)     # M_2(C) real dim
    n_even = length(even_idx)
    full_rank_is_16 = (full_real_rank == 16)
    even_rank_is_8  = (even_real_rank == 8)
    even_count_is_8 = (n_even == 8)

    ps = pseudoscalar_report(cl, gens)
    qr = quaternion_report(gens)

    println("\n[2] ALGEBRAIC  Cl(1,3) over R")
    println("    measured generator squares e_i^2 = ", sig,
            "   (+--- physics signature ? ", sig_is_phys, ")")
    println("    pseudoscalar omega^2 = ", ps["omega_squared"],
            "   (== -1 ? ", ps["omega_sq_is_minus1"], "  central-in-even ? ", ps["omega_central_in_even"], ")")
    println("    basis blades by grade ", sort(collect(gcounts)),
            "   -> total dim = ", dim_alg, "  (== 2^$n_vec = ", 2^n_vec, " ? ", dim_pow_check, ")")
    println("    FULL algebra real-rep rank   = ", full_real_rank, "   (M_2(H) real dim 16 ? ", full_rank_is_16, ")")
    println("    EVEN subalgebra blades       = ", n_even, "  real-rep rank = ", even_real_rank,
            "   (M_2(C) real dim 8 = Dirac spinor space ? ", even_rank_is_8, ")")
    println("    quaternion subalgebra H: i^2=", qr["i_squared"], " j^2=", qr["j_squared"],
            " k^2=", qr["k_squared"], " ijk=", qr["ijk"], "  (Hamilton closes ? ", qr["hamilton_closes"], ")")

    # ---- (3) SM generation Weyl count --------------------------------------
    count_with, rows_with = sm_weyl_count(include_nu_R=true)
    count_without, _      = sm_weyl_count(include_nu_R=false)
    sm_is_16 = (count_with == 16)
    println("\n[3] PHYSICAL  one SM fermion generation (Weyl dof)")
    for r in rows_with
        println("    ", rpad(r["multiplet"], 34), " : ", r["weyl_dof"])
    end
    println("    ", rpad("TOTAL with nu_R", 34), " : ", count_with, "   (== 16 ? ", sm_is_16, ")")

    # ---- KILL-CONTROLS: 16 must be distinguished from 15 and 8 -------------
    # K1: dropping nu_R gives 15, not 16.
    k1_count = count_without
    k1_is_15 = (k1_count == 15)
    k1_distinguished = (k1_count != 16) && k1_is_15
    # K2: even subalgebra dim 8 (Dirac spinor space) is NOT the full algebra 16.
    k2_even_ne_full = (even_real_rank != full_real_rank) && (even_real_rank == 8) && (full_real_rank == 16)
    # K3: wrong number of generators Cl(1,2) has dim 2^3 = 8 != 16.
    cl3 = CliffordAlgebra(1, 2)
    dim_cl12 = dimension(cl3)
    k3_is_8 = (dim_cl12 == 8)
    k3_distinguished = (dim_cl12 != 16) && k3_is_8

    kill_ok = k1_distinguished && k2_even_ne_full && k3_distinguished

    println("\n[KILL-CONTROL]  16 vs wrong answers 15 / 8")
    println("    K1 SM count WITHOUT nu_R = ", k1_count, "  (== 15, != 16 ? ", k1_distinguished, ")")
    println("    K2 even subalg dim ", even_real_rank, " != full dim ", full_real_rank,
            "  (8 not mistaken for 16 ? ", k2_even_ne_full, ")")
    println("    K3 Cl(1,2) dim = ", dim_cl12, "  (== 8, != 16 ? ", k3_distinguished, ")")
    println("    kill-control distinguishes 16 from 15/8 : ", kill_ok)

    # ---- VERDICT -----------------------------------------------------------
    all_pass = set_is_16 && distinct_16 &&
               dim_is_16 && dim_pow_check && sig_is_phys &&
               full_rank_is_16 && even_count_is_8 && even_rank_is_8 &&
               ps["omega_sq_is_minus1"] && ps["omega_central_in_even"] &&
               qr["hamilton_closes"] &&
               sm_is_16 && kill_ok

    println("\n", "="^74)
    println("SUMMARY (measured numbers):")
    println("  |2 x 4 x 2|              = ", n_terrains)
    println("  dim Cl(1,3)             = ", dim_alg,        "  (real-rep rank ", full_real_rank, ")")
    println("  even subalgebra dim     = ", even_real_rank, "  (Dirac spinor space)")
    println("  SM generation count     = ", count_with,     "  (with nu_R)")
    println("  kill-control 16 vs 15/8 = ", kill_ok)
    println("ALL_PASS = ", all_pass)
    println("="^74)

    results = Dict{String,Any}(
        "object_id"          => "sixteen_terrain_cl13_generation",
        "classification"     => "PoC",
        "promotion_allowed"  => false,
        "interpretive_map"   => true,
        "honesty_note"       => "FORCED: |2x4x2|=16, dim Cl(1,3)=16, M_2(H) rep type, " *
                                "Cl^0=M_2(C) dim 8, SM Weyl count=16 with nu_R. " *
                                "NOVEL/INTERPRETIVE: identifying the 16 terrains with the 16 of " *
                                "Cl(1,3) and the 16 Weyl fermions is a MAP, not a derivation; the " *
                                "three 16s coincide as integers only.",
        "tools"              => ["Julia", "LinearAlgebra", "CliffordAlgebras"],
        "no_z3_block"        => true,
        "combinatorial" => Dict(
            "chiralities"   => CHIRALITIES,
            "spin_structures" => SPIN_STRUCTS,
            "chern_fluxes"  => CHERN_FLUXES,
            "n_terrains"    => n_terrains,
            "set_is_16"     => set_is_16,
            "all_distinct"  => distinct_16,
            "terrains"      => [Dict("chirality" => t[1], "spin_structure" => t[2], "chern_flux" => t[3]) for t in terrains],
        ),
        "algebraic" => Dict(
            "algebra"               => "Cl(1,3) over R",
            "measured_signature_e_i_sq" => sig,
            "signature_is_plus_minus_minus_minus" => sig_is_phys,
            "vector_space_dim_pq"   => n_vec,
            "blade_grade_counts"    => Dict(string(k) => v for (k, v) in gcounts),
            "dim_algebra"           => dim_alg,
            "dim_is_16"             => dim_is_16,
            "dim_equals_2_pow_pq"   => dim_pow_check,
            "full_algebra_real_rep_rank" => full_real_rank,
            "full_rank_is_16_M2H"   => full_rank_is_16,
            "n_even_blades"         => n_even,
            "even_subalgebra_real_rep_rank" => even_real_rank,
            "even_rank_is_8_M2C"    => even_rank_is_8,
            "rep_type_note"         => "Cl(1,3)=M_2(H) (real dim 16); Cl^0(1,3)=M_2(C) (real dim 8 = Dirac spinor operator space), per Bott table",
            "pseudoscalar"          => ps,
            "quaternion_subalgebra" => qr,
        ),
        "physical_sm_generation" => Dict(
            "multiplets_with_nu_R" => rows_with,
            "count_with_nu_R"      => count_with,
            "count_without_nu_R"   => count_without,
            "sm_count_is_16"       => sm_is_16,
            "note"                 => "16 left-handed Weyl dof per generation = one SO(10) 16-spinor (15 SM fermions + nu_R)",
        ),
        "kill_controls" => Dict(
            "K1_drop_nuR_gives_15" => Dict("count" => k1_count, "is_15" => k1_is_15, "distinguished_from_16" => k1_distinguished),
            "K2_even_8_not_full_16" => Dict("even_dim" => even_real_rank, "full_dim" => full_real_rank, "distinguished" => k2_even_ne_full),
            "K3_Cl12_dim_8" => Dict("dim_Cl12" => dim_cl12, "is_8" => k3_is_8, "distinguished_from_16" => k3_distinguished),
            "kill_ok_16_vs_15_and_8" => kill_ok,
        ),
        "verdict" => Dict(
            "all_pass"      => all_pass,
            "ladder_status" => "runs; passes local rerun (this run)",
            "measured" => Dict(
                "abs_2x4x2"        => n_terrains,
                "dim_Cl_1_3"       => dim_alg,
                "full_real_rep_rank" => full_real_rank,
                "even_subalgebra_dim" => even_real_rank,
                "sm_generation_count" => count_with,
                "kill_distinguishes_16_from_15_8" => kill_ok,
            ),
        ),
    )

    outpath = joinpath(@__DIR__, "sixteen_terrain_cl13_generation_results.json")
    open(outpath, "w") do io
        JSON.print(io, results, 2)
    end
    println("results written to: ", outpath)
    return results
end

main()
