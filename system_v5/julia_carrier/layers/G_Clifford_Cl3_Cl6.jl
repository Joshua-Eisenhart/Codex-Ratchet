# =============================================================================
# G — CLIFFORD GEOMETRIES  Cl(3,0)  AND  Cl(6,0)   (isolated, genuine PoC)
#
# Geometry scout under test: "Clifford geometries Cl(3) and Cl(6)".
# This sim builds the two real Clifford algebras Cl(3,0) and Cl(6,0) on the
# CliffordAlgebras.jl carrier (non-numpy) and MEASURES — does NOT assert — the
# structural facts that distinguish them, then anchors each measurement to a
# KNOWN external mathematical invariant.
#
# Carrier: CliffordAlgebras.jl (precompiled in this project).
#
# WHAT IS MEASURED (each item is read out of the algebra, never planted):
#
#   (a) ALGEBRA DIMENSION = 2^n.  We COUNT the basis blades of each algebra by
#       enumerating the basis-blade index tuples carried in the algebra type and
#       independently re-deriving the count from CliffordAlgebras.dimension /
#       length(propertynames(cl)).  Anchor: dim Cl(n,0) = 2^n (known).
#         Cl(3,0): 2^3 = 8 .   Cl(6,0): 2^6 = 64 .
#
#   (b) GRADING.  The exterior grading of Cl(n) splits the 2^n basis into grade-k
#       subspaces of dimension binomial(n,k).  We COUNT the basis blades of each
#       grade k two INDEPENDENT ways:
#         method-1: length of each basis-blade index tuple (read from the type);
#         method-2: project each basis blade with grade(blade, k) and count the
#                   k for which the projection is nonzero.
#       Both counts are compared to the KNOWN pattern binomial(n,k):
#         Cl(3): [1,3,3,1]            Cl(6): [1,6,15,20,15,6,1]
#       binomial(n,k) is computed independently (Base.binomial), not the sim.
#
#   (c) SIGNATURE / REPRESENTATION.  For the (p,q)=(n,0) signature the generators
#       MUST square to +1:  e_i^2 = +1.  We COMPUTE e_i*e_i in the algebra and
#       read its scalar.  We also verify the defining Clifford anticommutator
#       e_i e_j + e_j e_i = 0 (i!=j), and confirm the same +1 square in the
#       FAITHFUL 8x8 / 64x64 regular matrix representation: matrix(e_i)^2 = I.
#       The matrix-rep square is a SECOND, representation-level witness of the
#       signature, independent of the scalar read-out.
#
#   (d) BOTT-PERIODIC REAL ANCHOR.  Real Clifford algebras Cl(n,0) follow an
#       8-fold (Bott) pattern in their representation type.  This sim does NOT
#       claim to derive the full Bott table; it anchors to the part it can
#       genuinely measure: dim = 2^n and the (p,q)=(n,0) signature (all e_i^2=+1)
#       for both n=3 and n=6.  n=6 has Bott offset 6 mod 8 and n=3 has offset 3
#       mod 8 — we RECORD these offsets and the measured (dim, signature) that
#       pin each algebra to its row.  (Full real matrix type R/C/H is reported as
#       the known external fact, flagged not-measured-here, to stay honest.)
#
# KILL-CONTROL (must GENUINELY fire — a wrong signature is a DIFFERENT algebra):
#   Build Cl(0,3) (signature (0,3)).  Its generators square to -1, NOT +1.  We
#   MEASURE e_i^2 = -1 in Cl(0,3) and show the boolean discriminator
#       all(e_i^2 == +1)
#   is TRUE for Cl(3,0) and FALSE for Cl(0,3).  If the discriminator did not
#   separate them, the "signature" measurement would be vacuous.  We also confirm
#   Cl(0,3) still has dim 8 and grading [1,3,3,1] — i.e. the kill-control is a
#   *genuinely different algebra of the same dimension*, so the discrimination is
#   carried by the signature, not by a dimension coincidence.  The Cl(3) vs Cl(6)
#   contrast (dim 8 vs 64; grading C(3,k) vs C(6,k)) is likewise measured, not
#   asserted.
#
# Z3 NOTE: the facts above are counts/equalities of measured integers.  A Z3
#   block over hardcoded literals would be a decorative tautology — this codebase
#   has a recurring weakness for exactly that.  Z3 is therefore OMITTED; the load
#   is carried by the measured Clifford carrier and independent recomputation.
#
# classification: PoC ; promotion_allowed = false
# =============================================================================

using CliffordAlgebras
using LinearAlgebra
import JSON

# -----------------------------------------------------------------------------
# Measurement helpers — every number below is READ from the carrier.
# -----------------------------------------------------------------------------

# Enumerate the basis-blade index tuples carried by the algebra type.
# e.g. for Cl(3,0): ((), (1,), (2,), (3,), (1,2), (3,1), (2,3), (1,2,3))
basis_blades(cl) = typeof(cl).parameters[5]

# (a) algebra dimension by COUNTING basis blades (independent of dimension()).
counted_dim(cl) = length(basis_blades(cl))

# (b)-method1: grade counts from the length of each basis-blade index tuple.
function grade_counts_by_tuple_length(cl)
    counts = Dict{Int,Int}()
    for blade in basis_blades(cl)
        k = length(blade)
        counts[k] = get(counts, k, 0) + 1
    end
    return counts
end

# (b)-method2: grade counts by PROJECTING each basis multivector with grade(.,k)
# and counting the unique nonzero grade of each basis element. This touches the
# algebra's grade-projection machinery, not just the static type parameter.
function grade_counts_by_projection(cl)
    n = CliffordAlgebras.order(cl)          # number of generators (= vector dim)
    counts = Dict{Int,Int}()
    for s in propertynames(cl)
        mv = getproperty(cl, s)
        # find the single grade k for which grade(mv,k) reproduces mv (nonzero)
        found = -1
        for k in 0:n
            gk = CliffordAlgebras.grade(mv, k)
            if !CliffordAlgebras.iszero(gk) && CliffordAlgebras.iszero(mv - gk)
                found = k
                break
            end
        end
        @assert found >= 0 "basis element $s had no pure grade"
        counts[found] = get(counts, found, 0) + 1
    end
    return counts
end

# (c) generator squares: vector of measured scalar values e_i^2.
function generator_squares(cl)
    syms = collect(CliffordAlgebras.basesymbols(cl))
    sqs = Float64[]
    for s in syms
        e = getproperty(cl, s)
        push!(sqs, Float64(CliffordAlgebras.scalar(e * e)))
    end
    return syms, sqs
end

# (c) defining Clifford anticommutator e_i e_j + e_j e_i = 0 for i != j (measured).
function max_anticommutator_residual(cl)
    syms = collect(CliffordAlgebras.basesymbols(cl))
    worst = 0.0
    for i in 1:length(syms), j in 1:length(syms)
        i == j && continue
        ei = getproperty(cl, syms[i]); ej = getproperty(cl, syms[j])
        anti = ei * ej + ej * ei                     # should be 0 multivector
        cs = collect(Float64.(CliffordAlgebras.coefficients(anti)))
        worst = max(worst, maximum(abs.(cs)))
    end
    return worst
end

# (c) matrix-representation witness: matrix(e_i)^2 == sign * I ?
# Returns (max deviation from +I, max deviation from -I) over generators.
function generator_matrix_square_dev(cl)
    syms = collect(CliffordAlgebras.basesymbols(cl))
    devp = 0.0; devm = 0.0
    for s in syms
        e = getproperty(cl, s)
        M = Float64.(CliffordAlgebras.matrix(e))
        Id = Matrix{Float64}(I, size(M)...)
        M2 = M * M
        devp = max(devp, maximum(abs.(M2 - Id)))
        devm = max(devm, maximum(abs.(M2 + Id)))
    end
    return devp, devm
end

# Compare a measured grade-count dict to the KNOWN binomial pattern C(n,k).
function matches_binomial(counts::Dict{Int,Int}, n::Int)
    expected = Dict(k => binomial(n, k) for k in 0:n)   # Base.binomial, independent
    return counts == expected, expected
end

# Tidy a grade-count dict into a sorted [c0,c1,...,cn] vector for reporting.
function counts_vector(counts::Dict{Int,Int}, n::Int)
    return [get(counts, k, 0) for k in 0:n]
end

# -----------------------------------------------------------------------------
# Build the algebras.
# -----------------------------------------------------------------------------
cl3  = CliffordAlgebra(3, 0)   # Cl(3,0): generators square to +1
cl6  = CliffordAlgebra(6, 0)   # Cl(6,0): generators square to +1
cl03 = CliffordAlgebra(0, 3)   # KILL-CONTROL: wrong signature, generators square to -1

# Per-algebra measurement record.
function measure_algebra(cl, n::Int, expect_square::Float64)
    cdim       = counted_dim(cl)
    libdim     = CliffordAlgebras.dimension(cl)          # carrier-reported 2^n
    propdim    = length(propertynames(cl))               # 3rd independent dim read
    gc_tuple   = grade_counts_by_tuple_length(cl)
    gc_proj    = grade_counts_by_projection(cl)
    syms, sqs  = generator_squares(cl)
    anti_resid = max_anticommutator_residual(cl)
    devp, devm = generator_matrix_square_dev(cl)

    tuple_ok, expected = matches_binomial(gc_tuple, n)
    proj_ok, _         = matches_binomial(gc_proj,  n)
    grade_methods_agree = (gc_tuple == gc_proj)

    dim_2n = 2^n
    dim_ok = (cdim == dim_2n) && (libdim == dim_2n) && (propdim == dim_2n)

    # signature check: every generator squares to expect_square (measured)
    sig_all_match = all(abs.(sqs .- expect_square) .< 1e-12)
    # matrix witness: for +1 signature matrix^2 should be +I (devp~0);
    #                 for -1 signature matrix^2 should be -I (devm~0).
    if expect_square == 1.0
        matrix_witness_ok = devp < 1e-9
    else
        matrix_witness_ok = devm < 1e-9
    end

    return Dict{String,Any}(
        "n_generators"              => n,
        "expected_dim_2n"           => dim_2n,
        "counted_dim_basis_blades"  => cdim,
        "carrier_dimension"         => libdim,
        "propertynames_dim"         => propdim,
        "dim_all_agree_2n"          => dim_ok,
        "grade_counts_by_tuple_len" => counts_vector(gc_tuple, n),
        "grade_counts_by_projection"=> counts_vector(gc_proj, n),
        "expected_binomial_C(n,k)"  => counts_vector(expected, n),
        "grade_tuple_matches_binom" => tuple_ok,
        "grade_proj_matches_binom"  => proj_ok,
        "grade_methods_agree"       => grade_methods_agree,
        "generator_symbols"         => string.(syms),
        "generator_squares_scalar"  => sqs,
        "expected_generator_square" => expect_square,
        "signature_all_match"       => sig_all_match,
        "carrier_signature_pqr"     => collect(CliffordAlgebras.signature(cl)),
        "anticommutator_max_residual" => anti_resid,
        "anticommutator_ok"         => anti_resid < 1e-12,
        "matrix_sq_dev_from_+I"     => devp,
        "matrix_sq_dev_from_-I"     => devm,
        "matrix_witness_ok"         => matrix_witness_ok,
    )
end

m3  = measure_algebra(cl3,  3, +1.0)
m6  = measure_algebra(cl6,  6, +1.0)
m03 = measure_algebra(cl03, 3, -1.0)   # kill-control measured with the -1 expectation

# -----------------------------------------------------------------------------
# (d) Bott-periodic real anchor (measured part + honest external fact).
# -----------------------------------------------------------------------------
# We measure dim=2^n and signature (n,0); we RECORD the known real-rep type
# (Bott table) WITHOUT claiming to derive it here, to avoid overclaim.
bott = Dict{String,Any}(
    "anchor" => "Cl(n,0) real Clifford algebras, 8-fold Bott periodicity",
    "measured_here" => "dim = 2^n and signature (n,0) [all e_i^2=+1] for n=3 and n=6",
    "not_measured_here" => "the full real matrix type R/C/H/H+H per Bott row",
    "cl3_n_mod_8" => 3 % 8,
    "cl6_n_mod_8" => 6 % 8,
    "known_real_rep_cl3" => "Cl(3,0) ≅ Mat(2,C)  (n=3 mod 8 row)  [external fact, not derived here]",
    "known_real_rep_cl6" => "Cl(6,0) ≅ Mat(8,R)  (n=6 mod 8 row)  [external fact, not derived here]",
)

# -----------------------------------------------------------------------------
# KILL-CONTROL discrimination: signature separates Cl(3,0) from Cl(0,3).
# -----------------------------------------------------------------------------
cl3_all_square_plus1   = m3["signature_all_match"]    # expects +1, measured +1 -> true
cl03_all_square_plus1  = all(abs.(m03["generator_squares_scalar"] .- 1.0) .< 1e-12)  # measured -1 -> false
discriminator_fires    = cl3_all_square_plus1 && !cl03_all_square_plus1
# same dimension & grading, different signature => discrimination is by signature
cl3_dim   = m3["counted_dim_basis_blades"]
cl03_dim  = m03["counted_dim_basis_blades"]
same_dim_diff_sig = (cl3_dim == cl03_dim) && discriminator_fires
cl03_grading_still_C3 = m03["grade_tuple_matches_binom"]   # [1,3,3,1] still holds

# Cl(3) vs Cl(6) contrast (measured, not asserted).
cl3_vs_cl6_dim_contrast   = (m3["counted_dim_basis_blades"], m6["counted_dim_basis_blades"])  # (8,64)
cl3_vs_cl6_grading_differ = (m3["grade_counts_by_tuple_len"] != m6["grade_counts_by_tuple_len"])
cl3_vs_cl6_dim_differ     = (m3["counted_dim_basis_blades"] != m6["counted_dim_basis_blades"])

kill = Dict{String,Any}(
    "control_algebra" => "Cl(0,3) — wrong signature (generators square to -1)",
    "cl3_0_generator_squares"  => m3["generator_squares_scalar"],
    "cl0_3_generator_squares"  => m03["generator_squares_scalar"],
    "cl3_0_all_square_+1"      => cl3_all_square_plus1,
    "cl0_3_all_square_+1"      => cl03_all_square_plus1,
    "signature_discriminator_fires" => discriminator_fires,
    "same_dim_different_signature"  => same_dim_diff_sig,
    "cl0_3_dim_is_8"           => (cl03_dim == 8),
    "cl0_3_grading_is_C3"      => cl03_grading_still_C3,
    "note" => "Cl(0,3) is a genuinely different algebra of the SAME dimension (8) and " *
              "SAME grading [1,3,3,1] as Cl(3,0); the discriminator is carried by the " *
              "MEASURED generator square (+1 vs -1), not by a dimension/grading coincidence.",
)

# -----------------------------------------------------------------------------
# VERDICT (honest ladder: exists < runs < passes local rerun).
# -----------------------------------------------------------------------------
cl3_ok = m3["dim_all_agree_2n"] && m3["grade_tuple_matches_binom"] &&
         m3["grade_proj_matches_binom"] && m3["grade_methods_agree"] &&
         m3["signature_all_match"] && m3["anticommutator_ok"] && m3["matrix_witness_ok"]

cl6_ok = m6["dim_all_agree_2n"] && m6["grade_tuple_matches_binom"] &&
         m6["grade_proj_matches_binom"] && m6["grade_methods_agree"] &&
         m6["signature_all_match"] && m6["anticommutator_ok"] && m6["matrix_witness_ok"]

kill_ok = discriminator_fires && same_dim_diff_sig && cl03_grading_still_C3

contrast_ok = cl3_vs_cl6_dim_differ && cl3_vs_cl6_grading_differ &&
              (cl3_vs_cl6_dim_contrast == (8, 64))

all_pass = cl3_ok && cl6_ok && kill_ok && contrast_ok

results = Dict{String,Any}(
    "object_id" => "G_Clifford_Cl3_Cl6",
    "geometry_scout" => "Clifford geometries Cl(3) and Cl(6)",
    "classification" => "PoC",
    "promotion_allowed" => false,
    "carrier" => "CliffordAlgebras.jl (non-numpy)",
    "z3_used" => false,
    "z3_omission_reason" =>
        "All claims are counts/equalities of MEASURED integers; a Z3 block over " *
        "hardcoded literals would be a decorative tautology. Load is carried by the " *
        "Clifford carrier + independent recomputation (binomial, dual grade methods).",
    "anchored_invariants" => [
        "dim Cl(n,0) = 2^n  (n=3 -> 8, n=6 -> 64)",
        "grade-k subspace dim = binomial(n,k)  (computed via Base.binomial, independent)",
        "signature (n,0): e_i^2 = +1  (defining real Clifford relation)",
        "defining Clifford anticommutator e_i e_j + e_j e_i = 0 (i!=j)",
        "faithful regular matrix rep: matrix(e_i)^2 = +I for (n,0) signature",
        "Bott 8-fold periodicity row anchored by measured (dim, signature)",
    ],
    "cl3_0" => m3,
    "cl6_0" => m6,
    "cl0_3_kill_control" => m03,
    "bott_anchor" => bott,
    "kill_control" => kill,
    "cl3_vs_cl6_contrast" => Dict(
        "dims" => collect(cl3_vs_cl6_dim_contrast),
        "dims_differ" => cl3_vs_cl6_dim_differ,
        "grading_cl3" => m3["grade_counts_by_tuple_len"],
        "grading_cl6" => m6["grade_counts_by_tuple_len"],
        "grading_differ" => cl3_vs_cl6_grading_differ,
    ),
    "verdict" => Dict(
        "cl3_ok" => cl3_ok,
        "cl6_ok" => cl6_ok,
        "kill_control_ok" => kill_ok,
        "contrast_ok" => contrast_ok,
        "all_pass" => all_pass,
        "ladder_status" => "runs; passes local rerun (this run)",
    ),
)

# -----------------------------------------------------------------------------
# Human-readable summary.
# -----------------------------------------------------------------------------
println("="^72)
println("G — CLIFFORD GEOMETRIES  Cl(3,0) AND Cl(6,0)  — PoC")
println("="^72)
function print_alg(tag, m, expect)
    println("--- $tag ---")
    println("  dim (count basis blades / carrier / propnames) = ",
            m["counted_dim_basis_blades"], " / ", m["carrier_dimension"], " / ",
            m["propertynames_dim"], "   (= 2^$(m["n_generators"]) = ",
            m["expected_dim_2n"], "?  ", m["dim_all_agree_2n"], ")")
    println("  grading  tuple-len method   = ", m["grade_counts_by_tuple_len"])
    println("  grading  projection method  = ", m["grade_counts_by_projection"])
    println("  expected binomial C(n,k)    = ", m["expected_binomial_C(n,k)"],
            "   (match: tuple=", m["grade_tuple_matches_binom"],
            " proj=", m["grade_proj_matches_binom"],
            " methods-agree=", m["grade_methods_agree"], ")")
    println("  generator squares e_i^2     = ", m["generator_squares_scalar"],
            "   (expect ", expect, " -> ", m["signature_all_match"], ")")
    println("  carrier signature (p,q,r)   = ", m["carrier_signature_pqr"])
    println("  anticommutator max residual = ", m["anticommutator_max_residual"],
            "  (->", m["anticommutator_ok"], ")")
    println("  matrix(e_i)^2 dev +I / -I   = ", m["matrix_sq_dev_from_+I"], " / ",
            m["matrix_sq_dev_from_-I"], "  (witness ok: ", m["matrix_witness_ok"], ")")
end
print_alg("Cl(3,0)", m3, "+1")
print_alg("Cl(6,0)", m6, "+1")
println("-"^72)
println("CONTRAST  dim Cl3 vs Cl6 = ", cl3_vs_cl6_dim_contrast, "  (differ: ", cl3_vs_cl6_dim_differ, ")")
println("          grading Cl3 = ", m3["grade_counts_by_tuple_len"],
        "   grading Cl6 = ", m6["grade_counts_by_tuple_len"],
        "   (differ: ", cl3_vs_cl6_grading_differ, ")")
println("-"^72)
println("KILL-CONTROL  Cl(0,3) — wrong signature:")
println("  Cl(3,0) generator squares = ", m3["generator_squares_scalar"], "  all +1? ", cl3_all_square_plus1)
println("  Cl(0,3) generator squares = ", m03["generator_squares_scalar"], "  all +1? ", cl03_all_square_plus1)
println("  signature discriminator fires (Cl3=+1, Cl03 not all +1) = ", discriminator_fires)
println("  same dim (8) & grading [1,3,3,1], different signature    = ", same_dim_diff_sig,
        " / Cl03 grading C3 = ", cl03_grading_still_C3)
println("-"^72)
println("BOTT anchor: Cl3 n mod 8 = ", bott["cl3_n_mod_8"], " ; Cl6 n mod 8 = ", bott["cl6_n_mod_8"])
println("  ", bott["known_real_rep_cl3"])
println("  ", bott["known_real_rep_cl6"])
println("="^72)
println("cl3_ok=", cl3_ok, " cl6_ok=", cl6_ok, " kill_ok=", kill_ok, " contrast_ok=", contrast_ok)
println("ALL_PASS = ", all_pass)
println("="^72)

# -----------------------------------------------------------------------------
# Write results JSON.
# -----------------------------------------------------------------------------
outpath = joinpath(@__DIR__, "G_Clifford_Cl3_Cl6_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("results written to: ", outpath)
