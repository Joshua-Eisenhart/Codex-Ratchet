# Weyl L/R sheet cover as a finite spinor network carrying entanglement.
# classification = weyl_lr_spinor_network_entanglement_poc ; promotion_allowed = false.
#
# OBJECT: a finite spinor network is covered by a LEFT-Weyl sheet (H_L = +H0) and a RIGHT-Weyl
# sheet (H_R = -H0). Two GENUINE, INDEPENDENT load-bearing receipts (no planted numbers, no
# by-construction controls, no Bloch r-vector):
#
#  (A) GEOMETRY -- anchored to a KNOWN topological invariant. Each Weyl sheet is a 2-band
#      Qi-Wu-Zhang Chern insulator H0(k) = sin kx . sx + sin ky . sy + (m+2-cos kx-cos ky) . sz.
#      The sheet's chirality invariant is the FHS (Fukui-Hatsugai-Suzuki) LATTICE CHERN NUMBER
#      computed from the OCCUPIED EIGENVECTOR (the projector P=|u><u|), integrated as a U(1) Berry
#      flux over the Brillouin zone. It comes out integer-quantized = -1. The RIGHT sheet runs
#      H_R = -H0, whose occupied band is the OTHER band, giving the OPPOSITE Chern number = +1.
#      => chirality invariant is opposite per sheet (the task), c_L + c_R = 0.
#      WRONG-STRUCTURE CONTROL: a TRIVIAL mass m_ctrl = 3.0 gives a non-inverted gap -> Chern = 0,
#      which FAILS the |C|=1 invariant. This is not a planted number: the Chern number is read off
#      a real Berry-flux loop integral and lands on a quantized integer or it does not.
#
#  (B) ENTANGLEMENT -- MEASURED, load-bearing. The finite spinor network is an ITensors MPS whose
#      sites are split into a LEFT sub-network and a RIGHT sub-network. Cross-cut entangling gates
#      braid L with R; we MEASURE the von-Neumann entanglement entropy of the L|R cut (Schmidt
#      spectrum across the bond). A PRODUCT CONTROL (identical network, cross-cut gates removed)
#      gives cut entropy ~ 0. So the entanglement across L|R is load-bearing, not decorative.
#
# BLOCH-FREE: the geometry receipt reads the occupied eigenVECTOR / projector and a Berry-phase
# loop product (spinor / density-operator level). The entanglement receipt reads a Schmidt
# spectrum of a reduced density matrix. Nowhere is a Bloch r = <sigma> 3-vector used as a readout.
#
# Carrier: Julia + LinearAlgebra + ITensors/ITensorMPS (non-numpy). JSON for emission.
# This is a PoC layer adapter, NOT the primary object. promotion_allowed = false.

using LinearAlgebra
using ITensors, ITensorMPS
import JSON

const OUT = joinpath(@__DIR__, "weyl_lr_spinor_network_entanglement_results.json")

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

# ----------------------------------------------------------------------------------------------
# (A) GEOMETRY -- FHS lattice Chern number of a Weyl sheet (Qi-Wu-Zhang 2-band model).
# H0(m,k) = sin kx . sx + sin ky . sy + (m + 2 - cos kx - cos ky) . sz.
# At m = -1 the sz mass inverts at Gamma -> a single Weyl point -> |C| = 1 (TOPOLOGICAL).
# At m =  3 the mass never inverts -> C = 0 (TRIVIAL control).
# ----------------------------------------------------------------------------------------------
function weyl_h0(m::Float64, kx::Float64, ky::Float64)
    dx = sin(kx); dy = sin(ky); dz = m + 2.0 - cos(kx) - cos(ky)
    return dx * SX + dy * SY + dz * SZ
end

"Occupied (lower-energy) eigenvector of +H0 (the LEFT-Weyl sheet's filled band)."
function occupied_left(m, kx, ky)
    e = eigen(Hermitian(weyl_h0(m, kx, ky)))
    return e.vectors[:, 1]            # lowest eigenvalue
end

"Occupied (lower-energy) eigenvector of -H0 (the RIGHT-Weyl sheet, H_R = -H0).
 Negating H swaps which band is filled => the OPPOSITE-chirality occupied state."
function occupied_right(m, kx, ky)
    e = eigen(Hermitian(-weyl_h0(m, kx, ky)))
    return e.vectors[:, 1]
end

# U(1) link variable on the Berry connection; phase only (FHS gauge-invariant construction).
function link(u::AbstractVector{ComplexF64}, v::AbstractVector{ComplexF64})
    z = dot(u, v); a = abs(z)
    return a <= 1e-14 ? one(ComplexF64) : z / a
end

"FHS lattice Chern number from an OCCUPIED-state field over the BZ (Berry flux loop integral)."
function fhs_chern(occ_fn, m; nk::Int=41)
    occ = Array{ComplexF64}(undef, 2, nk, nk)
    for ix in 1:nk, iy in 1:nk
        kx = 2pi * (ix - 1) / nk; ky = 2pi * (iy - 1) / nk
        occ[:, ix, iy] = occ_fn(m, kx, ky)
    end
    total = 0.0
    for ix in 1:nk, iy in 1:nk
        ixp = ix == nk ? 1 : ix + 1
        iyp = iy == nk ? 1 : iy + 1
        ux   = link(occ[:, ix, iy ], occ[:, ixp, iy ])
        uyx  = link(occ[:, ixp, iy], occ[:, ixp, iyp])
        uxy  = link(occ[:, ix, iyp], occ[:, ixp, iyp])
        uy   = link(occ[:, ix, iy ], occ[:, ix , iyp])
        total += angle(ux * uyx * conj(uxy) * conj(uy))   # plaquette Berry flux
    end
    return total / (2pi)
end

# ----------------------------------------------------------------------------------------------
# (B) ENTANGLEMENT -- finite spinor-network MPS, L sub-network | R sub-network cut entropy.
# Build a 2N-site spinor network: sites 1..N = LEFT sheet, N+1..2N = RIGHT sheet.
# Entangle WITHIN each sub-network, then braid ACROSS the L|R cut. Measure cut entropy.
# Product control = identical build with the cross-cut braiding gates removed.
# ----------------------------------------------------------------------------------------------
"Two-qubit entangler with chirality-dependent angles (genuine network coupling, not identity)."
function entangler(s, a, b, ang)
    # exp(-i ang (XX + 0.7 YY + 0.45 ZZ)) -- a real entangling gate on the spinor pair
    XX = kron(SX, SX); YY = kron(SY, SY); ZZ = kron(SZ, SZ)
    H = ang * (XX + 0.7 * YY + 0.45 * ZZ)
    U = exp(-im * Matrix(H))           # 4x4 unitary
    Ut = reshape(U, (2, 2, 2, 2))      # (a',b',a,b)
    return ITensor(Ut, prime(s[a]), prime(s[b]), s[a], s[b])
end

"Build the L/R spinor-network MPS. cross_cut=true braids L with R; false = product across the cut."
function build_network(N::Int; cross_cut::Bool)
    s = siteinds("Qubit", 2N)
    psi = MPS(s, "0")
    # rotate every site off |0> so spinors are generic (Hadamard-like seed)
    for q in 1:2N
        θ = 0.3 + 0.9 * (q / (2N))
        rot = ComplexF64[cos(θ/2) -sin(θ/2); sin(θ/2) cos(θ/2)]
        psi = apply(ITensor(rot, prime(s[q]), s[q]), psi)
    end
    # entangle WITHIN the left sub-network (sites 1..N) and within the right (N+1..2N)
    for sweep in 1:2, base in (1, N+1)
        for i in base:(base + N - 2)
            psi = apply(entangler(s, i, i+1, 0.6 + 0.1*i), psi; cutoff=1e-14, maxdim=64)
        end
    end
    # braid ACROSS the L|R cut (couple the last LEFT site to the first RIGHT site, and a few more)
    if cross_cut
        for k in 0:min(N-1, 3)
            a = N - k; b = N + 1 + k
            (a >= 1 && b <= 2N) || continue
            psi = apply(entangler(s, a, b, 0.8), psi; cutoff=1e-14, maxdim=64)
        end
    end
    normalize!(psi)
    return psi, s
end

"von-Neumann entanglement entropy across the bond between site b and b+1 (the L|R cut at b=N)."
function cut_entropy(psi::MPS, b::Int)
    orthogonalize!(psi, b)
    if b == 1
        U, S, V = svd(psi[b], (siteind(psi, b),))
    else
        U, S, V = svd(psi[b], (linkind(psi, b-1), siteind(psi, b)))
    end
    ent = 0.0
    for n in 1:dim(S, 1)
        p = S[n, n]^2
        p > 1e-12 && (ent -= p * log2(p))
    end
    return ent, dim(S, 1)
end

# ----------------------------------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------------------------------
println("=== Weyl L/R spinor-network entanglement PoC ===")

# (A) GEOMETRY: chirality Chern invariant per sheet + wrong-structure control.
const M_TOPO = -1.0     # inverted mass -> |C| = 1
const M_CTRL =  3.0     # trivial mass  -> C = 0   (WRONG-STRUCTURE control)

c_left       = fhs_chern(occupied_left,  M_TOPO)   # LEFT sheet  H_L = +H0
c_right      = fhs_chern(occupied_right, M_TOPO)   # RIGHT sheet H_R = -H0 (opposite band)
c_left_ctrl  = fhs_chern(occupied_left,  M_CTRL)   # trivial-mass control on the SAME machinery
c_right_ctrl = fhs_chern(occupied_right, M_CTRL)

cL = round(Int, c_left); cR = round(Int, c_right)
cLc = round(Int, c_left_ctrl); cRc = round(Int, c_right_ctrl)

println("GEOMETRY (chirality Chern invariant, FHS lattice flux):")
println("  LEFT  sheet (+H0, m=-1): C = $(round(c_left;  digits=6))  -> $cL")
println("  RIGHT sheet (-H0, m=-1): C = $(round(c_right; digits=6))  -> $cR")
println("  c_L + c_R = $(cL + cR)   (opposite chirality per sheet => sum 0)")
println("  CONTROL (trivial m=3):  LEFT C = $(round(c_left_ctrl; digits=6)) -> $cLc, " *
        "RIGHT C = $(round(c_right_ctrl; digits=6)) -> $cRc   (must be 0 => FAILS |C|=1)")

geom_topo_ok  = abs(cL) == 1 && abs(cR) == 1          # both sheets carry a |C|=1 Weyl invariant
geom_opp_ok   = cL == -cR && (cL + cR) == 0           # opposite per sheet (the task)
geom_quant_ok = abs(c_left - cL) < 1e-6 && abs(c_right - cR) < 1e-6   # genuinely integer-quantized
control_fires = abs(cLc) == 0 && abs(cRc) == 0        # wrong structure FAILS the |C|=1 invariant
control_is_diff = (abs(cLc) != abs(cL))               # control verdict differs from real verdict

# (B) ENTANGLEMENT: L|R cut entropy, entangled network vs product control.
ent_rows = []
ent_pass = true
for N in [3, 4, 6]
    psi_x, _   = build_network(N; cross_cut=true)   # L braided with R
    psi_p, _   = build_network(N; cross_cut=false)  # product across the L|R cut
    s_cut_x, schmidt_x = cut_entropy(psi_x, N)      # cut at the L|R boundary (between site N and N+1)
    s_cut_p, schmidt_p = cut_entropy(psi_p, N)
    bond_x = maxlinkdim(psi_x)
    rp = (s_cut_x > 1e-3) && (s_cut_p < 1e-9) && (schmidt_x >= 2) && (bond_x >= 2)
    global ent_pass &= rp
    push!(ent_rows, Dict(
        "N_per_sheet" => N, "n_sites" => 2N, "cut_at_bond" => N, "max_bond" => bond_x,
        "cut_entropy_entangled" => round(s_cut_x; digits=6),
        "cut_entropy_product"   => round(s_cut_p; digits=9),
        "schmidt_rank_entangled" => schmidt_x, "schmidt_rank_product" => schmidt_p,
        "pass" => rp))
    println("ENTANGLEMENT N=$N: L|R cut S(entangled)=$(round(s_cut_x;digits=4)) " *
            "vs S(product)=$(round(s_cut_p;digits=9))  bond=$bond_x schmidt=$schmidt_x  pass=$rp")
end

# also a half-chain (within-sheet) entropy as a second nonzero readout on the entangled network
psi_big, _ = build_network(6; cross_cut=true)
s_half, _ = cut_entropy(psi_big, 3)   # cut inside the LEFT sub-network
s_lr,   _ = cut_entropy(psi_big, 6)   # the L|R cut on the same network
println("ENTROPY READOUTS (N=6 entangled net): within-L-sheet cut S=$(round(s_half;digits=4)), " *
        "L|R cut S=$(round(s_lr;digits=4))")

min_cut_ent = minimum(r["cut_entropy_entangled"] for r in ent_rows)
max_prod_ent = maximum(r["cut_entropy_product"] for r in ent_rows)

# ----------------------------------------------------------------------------------------------
# GATES
# ----------------------------------------------------------------------------------------------
checks = Dict(
    # geometry receipt
    "geom_both_sheets_C1"          => geom_topo_ok,
    "geom_opposite_chirality_sum0" => geom_opp_ok,
    "geom_integer_quantized"       => geom_quant_ok,
    "geom_control_FAILS_invariant" => control_fires,
    "geom_control_verdict_differs" => control_is_diff,
    # entanglement receipt
    "entanglement_load_bearing"    => ent_pass,
    "entangled_cut_above_thresh"   => min_cut_ent > 1e-3,
    "product_cut_near_zero"        => max_prod_ent < 1e-9,
    "within_sheet_entropy_nonzero" => s_half > 1e-3,
)
all_pass = all(values(checks))

result = Dict(
    "name" => "weyl_lr_spinor_network_entanglement",
    "classification" => "weyl_lr_spinor_network_entanglement_poc",
    "promotion_allowed" => false,
    "carrier" => "Julia + LinearAlgebra + ITensors/ITensorMPS (non-numpy)",
    "bloch_free" => true,
    "bloch_free_note" => "geometry receipt reads occupied eigenVECTOR / Berry-phase loop product (projector level); " *
                         "entanglement receipt reads a Schmidt spectrum of a reduced density matrix; no <sigma> r-vector readout.",
    "claim_ceiling" => "PoC: Weyl L/R sheet cover as a finite spinor network. Geometry anchored to the FHS lattice " *
                       "Chern number (|C|=1 per sheet, opposite per sheet, c_L+c_R=0); trivial-mass control gives C=0 and " *
                       "FAILS the invariant. Entanglement: L|R cut von-Neumann entropy of the entangled spinor-network MPS " *
                       "is load-bearing -- a product control across the cut gives ~0. promotion_allowed=false; not canonical/bridge.",
    "tool_integration" => Dict(
        "LinearAlgebra" => "load_bearing (eigen, svd, Berry flux loop integral for the Chern number)",
        "ITensors/ITensorMPS" => "load_bearing (the finite spinor network MPS + L|R cut Schmidt entropy)",
        "JSON" => "supportive (emission only)",
        "Z3" => "not_used (no SMT step is load-bearing here; the invariant integrality is the proof form)"),
    "geometry" => Dict(
        "invariant" => "FHS lattice Chern number (Qi-Wu-Zhang Weyl sheet)",
        "chern_left_sheet_plusH0"  => round(c_left;  digits=6), "chern_left_int"  => cL,
        "chern_right_sheet_minusH0" => round(c_right; digits=6), "chern_right_int" => cR,
        "chirality_sum_cL_plus_cR" => cL + cR,
        "control_trivial_mass" => M_CTRL,
        "chern_left_control"  => round(c_left_ctrl;  digits=6), "chern_left_control_int"  => cLc,
        "chern_right_control" => round(c_right_ctrl; digits=6), "chern_right_control_int" => cRc),
    "entanglement" => Dict(
        "rows" => ent_rows,
        "min_cut_entropy_entangled" => round(min_cut_ent; digits=6),
        "max_cut_entropy_product"   => round(max_prod_ent; digits=12),
        "within_left_sheet_cut_entropy" => round(s_half; digits=6),
        "lr_cut_entropy_same_net" => round(s_lr; digits=6)),
    "checks" => checks,
    "all_pass" => all_pass,
)

open(OUT, "w") do io; JSON.print(io, result, 2); end

println("\n--- GATES ---")
for (k, v) in sort(collect(checks); by=first); println(rpad(k, 32), v ? "PASS" : "FAIL"); end
println("ALL_PASS = $all_pass")
println("results -> $OUT")
exit(all_pass ? 0 : 1)
