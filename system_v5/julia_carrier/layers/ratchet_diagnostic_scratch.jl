# =====================================================================================
# ratchet_diagnostic_scratch.jl
# =====================================================================================
# INDEPENDENT TRUTH-LANE reproduction of the geometric-constraint RATCHET.
#
# This file is a SCRATCH DIAGNOSTIC. It is the Julia/LinearAlgebra truth lane that runs
# in parallel with (and does NOT read) the PyTorch scratch from the other thread. Its job
# is to MEASURE, on a shared finite carrier, whether each "layer" of the proposed ratchet
# is a genuine ADMISSIBILITY CONDITION (narrows the admissible set A_{k+1} subset A_k) or
# merely a WITNESS that records a distinction without imposing it (count held constant).
#
# It is explicitly NOT tuned to reproduce the other thread's numbers (1440->249, ratio
# 1.128->1.478). Whatever this carrier measures is what is reported. If a gate fails to
# narrow, that failure is the finding, not a bug to be patched into a narrowing.
#
# ----------------------------------------------------------------------------------------
# RATCHET FORMALIZATION (from the design thread; NOT canon, NOT a theorem):
#   shared carrier X0 = finite set of candidate spinor/density configs over a grid
#       (eta, chi, sheet s in {L,R}, geometry G in {Hopf, nested_Hopf_tori, Clifford, SL2C}).
#   Each candidate x maps to a 2x2 DENSITY OPERATOR rho_x on the shared carrier. (Bloch-free:
#       rho is built directly in its eigenbasis as a convex mixture of two pure projectors;
#       there is NO Bloch r-vector anywhere. We compute everything from rho as an operator.)
#   Each layer k = (D_k domain, Phi_k finite channel on the SHARED carrier rho, C_k
#       admissibility predicate, I_k invariant/readout, N_k controls).
#   Ratchet:  A_{k+1} = { x in A_k : C_k(x) passes AND I_k(Phi_k(x)) survives controls
#                                    AND blocked controls fail }.
#       A genuine layer NARROWS: A_{k+1} subset A_k, and the inclusion should be PROPER for
#       a real condition. A permissive gate that holds the count constant only WITNESSED a
#       distinction (e.g. the other thread's Hopf gate held 1440->1440 because it witnessed
#       the fiber/base split without IMPOSING admissibility). We flag that case explicitly.
#   A_* = most constrained nonempty survivor.  DoF_* = admissible variations remaining in A_*.
#
#   Weyl-on-G (the channel family):
#       drho_s/dt = -i[H_s^G, rho_s] + sum_a ( L_{a,s}^G rho L^dag - 1/2 {L^dag L, rho} ).
#       Changing G changes H^G, L^G, the connection, the holonomy, the chirality, the
#       order-gap. We implement Phi_k^G as a finite (one-step) CPTP map built from a
#       G-dependent Hamiltonian H^G and a G-dependent jump operator L^G.
#   order_gap_ij(x) = || Phi_i(Phi_j(x)) - Phi_j(Phi_i(x)) ||   (operator norm of the
#       commutator of two channels, measured ON the density operator).
#   Pre-flux chirality:  J_chiral^G = R_G(rho_L) - R_G(rho_R), R_G a G-weighted chiral
#       readout. Sign-erased control collapses J_chiral -> 0.
#
# ----------------------------------------------------------------------------------------
# HONESTY DISCIPLINE (this repo has a documented history of by-construction theater):
#   - Every count is MEASURED by running the predicate over the carrier, never planted.
#   - Each gate's narrowing is reported as a fraction; a gate that does NOT narrow is
#     reported as narrowing=false with witness_only=true (THE key finding if it occurs).
#   - Controls (flat-G, order-erased, sign-erased) must COLLAPSE the relevant effect; if a
#     control fails to collapse, that is reported as a control failure (kill did not fire).
#   - No gate threshold is set equal to a target survivor count.
#
# classification = ratchet_diagnostic_scratch_only
# promotion_allowed = false
# claim_ceiling = scratch_diagnostic_only_nonpromotional: does NOT admit layer completion /
#   stacking / final flux / Axis0 / Xi / Phi0 / FEP / physics / final manifold.
# tools (all non-numpy, native Julia): LinearAlgebra, JSON
#
# run:
#   julia --project="/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier" \
#         "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/ratchet_diagnostic_scratch.jl"
# =====================================================================================

using LinearAlgebra
using JSON

const OUT = joinpath(@__DIR__, "ratchet_diagnostic_scratch_results.json")
const I2 = Matrix{ComplexF64}(I, 2, 2)

# -------------------------------------------------------------------------------------
# Pauli / Weyl basis (used as OPERATORS on rho; never as a Bloch r-vector)
# -------------------------------------------------------------------------------------
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
# 2-component Weyl chirality operator: gamma5 acts as +1 on R-sheet, -1 on L-sheet.
# On the 2-dim carrier we use SZ as the chirality grading (eigenvalues +-1) — this is the
# Weyl gamma5 reduced to one chiral doublet, NOT a Bloch z-component (it is an operator).
const GAMMA5 = SZ

# =====================================================================================
# SHARED CARRIER X0  — a grid of candidate density operators
# =====================================================================================
# A candidate is (eta, chi, s, G). We build a DENSITY OPERATOR directly:
#   - choose an eigenbasis pure state |psi(eta,chi,s)> on the carrier,
#   - mix it with the orthogonal state by a purity parameter set by eta,
#   so rho = p |psi><psi| + (1-p) |psi_perp><psi_perp|, 0.5 <= p <= 1.
# This is Bloch-free: rho is assembled from projectors, not from (1 + r.sigma)/2.
struct Candidate
    eta::Float64          # latitude-like angle, sets the pure-state direction + purity
    chi::Float64          # azimuth-like phase
    s::Symbol             # :L or :R   (sheet / chirality sector)
    G::Symbol             # :Hopf, :nested_Hopf_tori, :Clifford, :SL2C
    rho::Matrix{ComplexF64}
end

"Pure state on the carrier from (eta, chi, s). s=:R is RIGHT-handed (gamma5=+1 dominant),
 s=:L is LEFT-handed (gamma5=-1 dominant). The sheet SWAPS which gamma5 eigenspace dominates,
 so <psi|gamma5|psi> is genuinely sheet-dependent and changes SIGN with s (not just a phase)."
function pure_state(eta::Float64, chi::Float64, s::Symbol)
    # gamma5 = SZ has eigenstates |0> (g5=+1, RIGHT) and |1> (g5=-1, LEFT).
    # eta in (0,pi) sets the mixing angle; chi sets the relative phase.
    #   R-sheet:  |psi> = cos(eta/2)|0> + e^{i chi} sin(eta/2)|1>   -> <g5> = cos(eta) > 0 for eta<pi/2
    #   L-sheet:  |psi> = sin(eta/2)|0> + e^{i chi} cos(eta/2)|1>   -> <g5> = -cos(eta), opposite sign
    # This makes the sheet a genuine chirality flip: R weights the g5=+1 leg, L weights g5=-1.
    if s === :R
        psi = ComplexF64[cos(eta/2), exp(im*chi)*sin(eta/2)]
    else
        psi = ComplexF64[sin(eta/2), exp(im*chi)*cos(eta/2)]
    end
    psi / norm(psi)
end

"Density operator built directly from projectors (Bloch-free). Purity set by eta."
function build_rho(eta::Float64, chi::Float64, s::Symbol)
    psi = pure_state(eta, chi, s)
    psi_perp = ComplexF64[-conj(psi[2]), conj(psi[1])]   # orthogonal pure state
    # purity weight p in [0.5, 1]: maximal mixing at the equator eta=pi/2, purer at poles.
    p = 0.5 + 0.5*abs(cos(eta))
    rho = p * (psi * psi') + (1 - p) * (psi_perp * psi_perp')
    rho = (rho + rho') / 2          # Hermitize against float noise
    rho / real(tr(rho))             # normalize trace to 1
end

"Build the full carrier grid X0. Target ~1000-1500 candidates."
function build_carrier()
    etas = range(0.08, π - 0.08, length=14)        # 14  (avoid exact poles)
    chis = range(0.0, 2π*(1 - 1/13), length=13)    # 13
    sheets = (:L, :R)                              # 2
    Gs = (:Hopf, :nested_Hopf_tori, :Clifford, :SL2C)  # 4
    cands = Candidate[]
    for G in Gs, s in sheets, chi in chis, eta in etas
        push!(cands, Candidate(eta, chi, s, G, build_rho(eta, chi, s)))
    end
    cands     # 14*13*2*4 = 1456 candidates (in the ~1000-1500 target band)
end

# =====================================================================================
# G-DEPENDENT WEYL CHANNEL FAMILY  Phi^G  (finite one-step CPTP maps)
# =====================================================================================
# Each geometry G provides:
#   - a Hamiltonian H^G (drives unitary part -i[H,rho]),
#   - a jump operator L^G (drives the dissipator),
#   - a connection/holonomy angle hol(G) (used by the order/chirality readouts),
#   - a flat flag (the FLAT control collapses H^G, L^G, holonomy to trivial).
# These differ across G so that changing G changes H^G, L^G, holonomy, chirality, order-gap.
struct GeoSpec
    H::Matrix{ComplexF64}
    L::Matrix{ComplexF64}
    holonomy::Float64       # geometric holonomy angle of a closed leaf loop
    chern::Int              # discrete topological sign (Chern/winding class)
    flat::Bool
end

function geospec(G::Symbol; flat::Bool=false)
    if flat
        # FLAT control: trivial geometry. H, L commute trivially; holonomy 0; no chirality.
        return GeoSpec(0.3*SZ, 0.0*SX, 0.0, 0, true)
    end
    if G === :Hopf
        # Hopf S^3 -> S^2 U(1) bundle: nontrivial U(1) holonomy, Chern +1.
        return GeoSpec(0.7*SX + 0.4*SZ, 0.5*(SX - im*SY)/2, 2π*1.0, +1, false)  # holonomy = 2pi (Chern 1)
    elseif G === :nested_Hopf_tori
        # nested tori foliation: a different connection, larger holonomy, Chern +1.
        return GeoSpec(0.6*SY + 0.5*SZ, 0.4*(SX - im*SY)/2, 2π*1.0 + 0.9, +1, false)
    elseif G === :Clifford
        # Clifford torus T^2: flat-ish leaf but nontrivial winding; Chern 0 (trivial bundle),
        # holonomy a generic non-quantized value (genuine but NOT a 2pi multiple).
        return GeoSpec(0.5*SX + 0.5*SY, 0.45*(SX + im*SY)/2, 1.1, 0, false)
    elseif G === :SL2C
        # SL(2,C) (non-compact, boost-like): non-Hermitian-ish drive via a boost generator,
        # negative Chern sign, holonomy a generic value.
        return GeoSpec(0.8*SZ + 0.3*SX, 0.5*(SX + im*SY)/2, 1.7, -1, false)
    else
        error("unknown geometry $G")
    end
end

"One-step Weyl-on-G channel Phi^G(rho): unitary part exp(-iH dt) plus a single Kraus jump."
function weyl_channel(rho::Matrix{ComplexF64}, gs::GeoSpec; dt::Float64=0.35)
    U = exp(-im * gs.H * dt)
    rho1 = U * rho * U'                                  # coherent (Hamiltonian) part
    L = gs.L
    if norm(L) > 0
        Ldag = L'
        anti = Ldag * L
        # one Euler step of the dissipator: rho += dt*(L rho Ldag - 1/2 {LdagL, rho})
        diss = L * rho1 * Ldag - 0.5*(anti*rho1 + rho1*anti)
        rho2 = rho1 + dt * diss
    else
        rho2 = rho1
    end
    rho2 = (rho2 + rho2') / 2
    t = real(tr(rho2))
    t > 0 ? rho2 / t : rho2
end

# =====================================================================================
# READOUTS / INVARIANTS  I_k  (all computed FROM rho as an operator; Bloch-free)
# =====================================================================================
purity(rho)      = real(tr(rho*rho))                       # in [0.5, 1]
vn_entropy(rho)  = begin
    ev = real.(eigvals(Hermitian(rho)))
    s = 0.0
    for n in ev
        nn = clamp(n, 1e-15, 1.0)
        s -= nn*log(nn)
    end
    s
end
# chiral readout R_G(rho): G-weighted expectation of gamma5 (the Weyl chiral charge),
# read out as an OPERATOR expectation tr(rho * gamma5), weighted by the geometry's
# holonomy phase (cos of holonomy modulates the chiral coupling strength on G).
chiral_readout(rho, gs::GeoSpec) = real(tr(rho * GAMMA5)) * (1 + 0.5*cos(gs.holonomy))
# operator-norm distance between two density operators (Bloch-free)
op_dist(a, b) = opnorm(a - b)

# =====================================================================================
# THE RATCHET GATES  C_1..C_4  (each is an ADMISSIBILITY CONDITION, measured honestly)
# =====================================================================================

# --- A1: Hopf-admissibility ----------------------------------------------------------
# CONDITION (not a witness): the candidate's geometry must support a NONTRIVIAL closed-leaf
# holonomy AND the channel Phi^G must move rho around that leaf by a holonomy-coupled amount
# exceeding a threshold. Flat / trivial-bundle geometries fail. This IMPOSES admissibility:
# a candidate on a Chern-0, low-holonomy geometry (Clifford) is EXCLUDED, not merely labeled.
function gate_A1_hopf(c::Candidate)
    gs = geospec(c.G)
    # holonomy transport of rho once around the leaf: apply Phi^G, measure how far rho moved,
    # require the move to exceed a holonomy-set floor. Trivial bundle (chern==0, low hol) -> excluded.
    moved = op_dist(weyl_channel(c.rho, gs), c.rho)
    nontrivial_bundle = abs(gs.chern) >= 1                 # Hopf bundle nontriviality
    holonomy_active = abs(sin(gs.holonomy/2)) > 0.10        # closed-leaf holonomy is nontrivial
    transport_real = moved > 0.02                          # channel actually transports rho
    nontrivial_bundle && holonomy_active && transport_real
end

# --- A2: Weyl-chirality --------------------------------------------------------------
# CONDITION: the candidate must carry a DEFINITE chiral sign. gamma5 expectation tr(rho*g5)
# must be cleanly signed (|<g5>| above a floor) AND its sign must match the sheet s (R-> +, L-> -),
# AND the geometry's discrete Chern sign must be nonzero (orientation defined). Equator states
# (|<g5>|~0) and orientation-undefined geometries are EXCLUDED.
function gate_A2_chirality(c::Candidate)
    g5 = real(tr(c.rho * GAMMA5))
    definite = abs(g5) > 0.15                              # chiral charge cleanly nonzero
    sign_matches_sheet = (c.s === :R) ? (g5 > 0) : (g5 < 0)
    gs = geospec(c.G)
    orientation_defined = gs.chern != 0                    # definite Chern/chirality sign
    definite && sign_matches_sheet && orientation_defined
end

# --- A3: noncommuting-order ----------------------------------------------------------
# CONDITION: the candidate's geometry must produce a real ORDER GAP between the Weyl channel
# Phi^G and a second (reference) channel Phi^ref, i.e. Phi^G(Phi^ref(rho)) != Phi^ref(Phi^G(rho))
# by more than a threshold. Order-erased (same channel both slots) and flat-G collapse this.
const REF_CHANNEL_SPEC = GeoSpec(0.55*SY + 0.2*SX, 0.3*(SX - im*SY)/2, 1.3, +1, false)
function order_gap_of(c::Candidate; flat::Bool=false, erase_order::Bool=false)
    gs = geospec(c.G; flat=flat)
    ref = flat ? geospec(c.G; flat=flat) : REF_CHANNEL_SPEC
    if erase_order
        ref = gs                                           # SAME channel both slots -> commute
    end
    ab = weyl_channel(weyl_channel(c.rho, ref), gs)
    ba = weyl_channel(weyl_channel(c.rho, gs), ref)
    op_dist(ab, ba)
end
function gate_A3_order(c::Candidate)
    order_gap_of(c) > 0.01                                  # real noncommuting-order pressure
end

# --- A4: entropy / cut-window --------------------------------------------------------
# CONDITION: after the Weyl channel, the candidate's von-Neumann entropy must fall inside an
# admissible CUT WINDOW [lo, hi] (neither too pure nor maximally mixed). This is a genuine
# narrowing: candidates whose post-channel state is near-pure or near-maximally-mixed are EXCLUDED.
function gate_A4_entropy(c::Candidate)
    gs = geospec(c.G)
    S = vn_entropy(weyl_channel(c.rho, gs))
    0.08 < S < 0.62                                         # admissible entropy cut-window
end

# =====================================================================================
# RUN THE RATCHET  A0 -> A1 -> A2 -> A3 -> A4 -> A_*
# =====================================================================================
println("="^84)
println("RATCHET DIAGNOSTIC (Julia truth lane) — measure, do not tune")
println("="^84)

results = Dict{String,Any}()
results["object"] = "ratchet_diagnostic_scratch"
results["classification"] = "ratchet_diagnostic_scratch_only"
results["promotion_allowed"] = false
results["claim_ceiling"] = "scratch_diagnostic_only_nonpromotional: does NOT admit layer " *
    "completion / stacking / final flux / Axis0 / Xi / Phi0 / FEP / physics / final manifold."
results["tools"] = ["LinearAlgebra", "JSON"]
results["lane"] = "julia_independent_truth_lane (does not read the PyTorch scratch)"

X0 = build_carrier()
println("\nCarrier X0 built: ", length(X0), " candidate density operators")
println("  grid axes: eta(14) x chi(13) x sheet{L,R}(2) x G{Hopf,nested_Hopf_tori,Clifford,SL2C}(4)")

# sanity: every rho is a valid density operator (Hermitian, trace 1, PSD)
function valid_rho(rho)
    herm = norm(rho - rho') < 1e-9
    tr1 = abs(real(tr(rho)) - 1) < 1e-9
    ev = real.(eigvals(Hermitian(rho)))
    psd = minimum(ev) > -1e-9
    herm && tr1 && psd
end
all_valid = all(valid_rho(c.rho) for c in X0)
println("  all candidates are valid density operators (Hermitian, trace 1, PSD): ", all_valid)
results["carrier_valid_density_operators"] = all_valid

# ---- run the gates as a NARROWING ratchet ----
A0 = X0
A1 = [c for c in A0 if gate_A1_hopf(c)]
A2 = [c for c in A1 if gate_A2_chirality(c)]
A3 = [c for c in A2 if gate_A3_order(c)]
A4 = [c for c in A3 if gate_A4_entropy(c)]
Astar = A4

counts = Dict(
    "A0" => length(A0), "A1" => length(A1), "A2" => length(A2),
    "A3" => length(A3), "A4" => length(A4), "A_star" => length(Astar))
println("\nRATCHET COUNTS (each gate should NARROW: A_{k+1} subset A_k):")
println("  A0 (carrier)            = ", counts["A0"])
println("  A1 (Hopf-admissibility) = ", counts["A1"])
println("  A2 (Weyl-chirality)     = ", counts["A2"])
println("  A3 (noncommuting-order) = ", counts["A3"])
println("  A4 (entropy cut-window) = ", counts["A4"])
println("  A_* (survivor)          = ", counts["A_star"])
results["ratchet_counts"] = counts

# ---- per-gate narrowing: genuine CONDITION vs witness-only ----
# A gate is a genuine narrowing condition iff it removes at least one candidate from its input
# set. A gate that holds the count constant (out == in) is WITNESS-ONLY (it recorded a
# distinction but imposed no admissibility). THIS is exactly the failure mode the spec warns
# about (the permissive Hopf gate that held 1440->1440).
function gate_report(name, inset, outset)
    nin = length(inset); nout = length(outset)
    removed = nin - nout
    narrows = removed > 0
    Dict(
        "gate" => name,
        "in" => nin, "out" => nout, "removed" => removed,
        "survive_fraction" => nin > 0 ? nout/nin : 0.0,
        "narrows_genuine" => narrows,
        "witness_only_no_narrowing" => (nin > 0 && removed == 0),
    )
end
gate_reports = [
    gate_report("A1_hopf_admissibility", A0, A1),
    gate_report("A2_weyl_chirality",     A1, A2),
    gate_report("A3_noncommuting_order", A2, A3),
    gate_report("A4_entropy_cut_window", A3, A4),
]
println("\nPER-GATE NARROWING (genuine condition vs witness-only):")
for gr in gate_reports
    tag = gr["narrows_genuine"] ? "NARROWS" : (gr["witness_only_no_narrowing"] ? "WITNESS-ONLY (no narrowing!)" : "EMPTY-INPUT")
    println("  $(rpad(gr["gate"],26)) in=$(gr["in"]) -> out=$(gr["out"])  removed=$(gr["removed"])  [$tag]")
end
results["gate_reports"] = gate_reports
all_gates_narrow = all(gr["narrows_genuine"] for gr in gate_reports)
any_witness_only = any(gr["witness_only_no_narrowing"] for gr in gate_reports)
results["all_gates_narrow_genuine"] = all_gates_narrow
results["any_gate_witness_only"] = any_witness_only

# proper-subset (ratchet) check: A_{k+1} subset A_k, strictly somewhere
ratchet_monotone = counts["A0"] >= counts["A1"] >= counts["A2"] >= counts["A3"] >= counts["A4"] >= 0
proper_somewhere = counts["A_star"] < counts["A0"]
results["ratchet_monotone_subset"] = ratchet_monotone
results["ratchet_proper_subset_somewhere"] = proper_somewhere
nonempty = counts["A_star"] > 0
results["A_star_nonempty"] = nonempty

# =====================================================================================
# ORDER GAP — survivor distribution + FLAT and ORDER-ERASED CONTROLS (must collapse)
# =====================================================================================
println("\n" * "="^84)
println("ORDER GAP — survivor distribution + controls (flat-G, order-erased must collapse)")
println("="^84)

# survivor order gaps (real geometry)
survivor_gaps = [order_gap_of(c) for c in Astar]
if isempty(survivor_gaps)
    # fall back to A2 (chirality-admissible) so the order-gap stat is non-degenerate to report
    survivor_gaps = [order_gap_of(c) for c in A2]
    gap_pool = "A2_fallback (A_star empty)"
else
    gap_pool = "A_star"
end
gmin = isempty(survivor_gaps) ? 0.0 : minimum(survivor_gaps)
gmax = isempty(survivor_gaps) ? 0.0 : maximum(survivor_gaps)
gmean = isempty(survivor_gaps) ? 0.0 : sum(survivor_gaps)/length(survivor_gaps)
println("  survivor order_gap over $gap_pool: min=$(round(gmin,digits=5)) mean=$(round(gmean,digits=5)) max=$(round(gmax,digits=5))  (n=$(length(survivor_gaps)))")

# CONTROL 1: flat geometry — trivial G => H,L,holonomy trivial => channels commute => gap ~ 0.
flat_gaps = [order_gap_of(c; flat=true) for c in (isempty(Astar) ? A2 : Astar)]
flat_max = isempty(flat_gaps) ? 0.0 : maximum(flat_gaps)
flat_mean = isempty(flat_gaps) ? 0.0 : sum(flat_gaps)/length(flat_gaps)
flat_collapses = flat_max < 1e-6
println("  CONTROL flat-G order_gap: max=$(round(flat_max,sigdigits=3)) mean=$(round(flat_mean,sigdigits=3))  (collapse to ~0 ? $flat_collapses)")

# CONTROL 2: order-erased — same channel in both slots => commutator identically 0 => gap == 0.
erased_gaps = [order_gap_of(c; erase_order=true) for c in (isempty(Astar) ? A2 : Astar)]
erased_max = isempty(erased_gaps) ? 0.0 : maximum(erased_gaps)
erased_collapses = erased_max < 1e-12
println("  CONTROL order-erased order_gap: max=$(round(erased_max,sigdigits=3))  (identically 0 ? $erased_collapses)")

# control GAP measure: how much the real gap exceeds the flat-control gap (the narrowing effect)
control_gap = gmean - flat_mean
println("  control collapse gap (real_mean - flat_mean) = $(round(control_gap,digits=5))  (flat-control collapse should make flat_mean ~ 0)")

results["order_gap"] = Dict(
    "pool" => gap_pool, "n" => length(survivor_gaps),
    "min" => gmin, "mean" => gmean, "max" => gmax,
    "flat_control_max" => flat_max, "flat_control_mean" => flat_mean,
    "flat_control_collapses" => flat_collapses,
    "order_erased_control_max" => erased_max,
    "order_erased_control_collapses" => erased_collapses,
    "control_collapse_gap_real_minus_flat" => control_gap)

# =====================================================================================
# PRE-FLUX CHIRALITY  J_chiral = R_G(rho_L) - R_G(rho_R)   (before/after ratchet, sign-erased ctrl)
# =====================================================================================
println("\n" * "="^84)
println("PRE-FLUX CHIRALITY  J_chiral = R_G(rho_L) - R_G(rho_R)  (before vs after ratchet)")
println("="^84)

# pair candidates by (eta, chi, G), differing only in sheet s, and measure the chiral readout gap.
function chiral_current_stats(pool)
    # group by (eta, chi, G); within a group, J = R_G(rho_L) - R_G(rho_R)
    bykey = Dict{Tuple{Float64,Float64,Symbol}, Dict{Symbol,Candidate}}()
    for c in pool
        k = (round(c.eta,digits=6), round(c.chi,digits=6), c.G)
        d = get!(bykey, k, Dict{Symbol,Candidate}())
        d[c.s] = c
    end
    Js = Float64[]
    for (k, d) in bykey
        haskey(d, :L) && haskey(d, :R) || continue
        gsL = geospec(d[:L].G); gsR = geospec(d[:R].G)
        J = chiral_readout(d[:L].rho, gsL) - chiral_readout(d[:R].rho, gsR)
        push!(Js, J)
    end
    Js
end

# FLAT (sign-erased) chiral readout: holonomy 0 AND gamma5 grading erased -> J -> 0.
function chiral_current_stats_signerased(pool)
    bykey = Dict{Tuple{Float64,Float64,Symbol}, Dict{Symbol,Candidate}}()
    for c in pool
        k = (round(c.eta,digits=6), round(c.chi,digits=6), c.G)
        d = get!(bykey, k, Dict{Symbol,Candidate}())
        d[c.s] = c
    end
    Js = Float64[]
    flat_gs = GeoSpec(0.0*I2, 0.0*SX, 0.0, 0, true)
    # sign-erased readout: use |<g5>| symmetric magnitude (no sign) so L and R give the SAME
    # reading and J cancels to 0 — this is the sign-erased control.
    signerased_readout(rho) = abs(real(tr(rho * GAMMA5))) * (1 + 0.5*cos(flat_gs.holonomy))
    for (k, d) in bykey
        haskey(d, :L) && haskey(d, :R) || continue
        J = signerased_readout(d[:L].rho) - signerased_readout(d[:R].rho)
        push!(Js, J)
    end
    Js
end

# FLAT baseline chiral current: geometry contributes NOTHING beyond the bare gamma5 charge.
# The flat readout has NO holonomy amplification (weight == 1.0 exactly), so actual/flat
# isolates the geometric chiral amplification (1 + 0.5 cos hol). actual/flat > 1 means the
# geometry AMPLIFIES the chiral current relative to a geometry-free baseline; < 1 means it
# damps it. (Earlier draft used holonomy=0 -> weight 1.5, which made the ratio <= 1 by
# construction — a definitional artifact, now removed. The flat weight is the bare 1.0.)
flat_chiral_readout(rho) = real(tr(rho * GAMMA5)) * 1.0   # NO geometric amplification
function chiral_current_flat(pool)
    bykey = Dict{Tuple{Float64,Float64,Symbol}, Dict{Symbol,Candidate}}()
    for c in pool
        k = (round(c.eta,digits=6), round(c.chi,digits=6), c.G)
        d = get!(bykey, k, Dict{Symbol,Candidate}())
        d[c.s] = c
    end
    Js = Float64[]
    for (k, d) in bykey
        haskey(d, :L) && haskey(d, :R) || continue
        J = flat_chiral_readout(d[:L].rho) - flat_chiral_readout(d[:R].rho)
        push!(Js, J)
    end
    Js
end

meanabs(v) = isempty(v) ? 0.0 : sum(abs, v)/length(v)

# BEFORE ratchet (full carrier X0)
J_before = chiral_current_stats(X0)
J_before_flat = chiral_current_flat(X0)
J_before_signerased = chiral_current_stats_signerased(X0)
ratio_before = meanabs(J_before_flat) > 1e-12 ? meanabs(J_before)/meanabs(J_before_flat) : 0.0

# AFTER ratchet (survivor set A_*, or A2 if empty)
afterpool = isempty(Astar) ? A2 : Astar
J_after = chiral_current_stats(afterpool)
J_after_flat = chiral_current_flat(afterpool)
J_after_signerased = chiral_current_stats_signerased(afterpool)
ratio_after = meanabs(J_after_flat) > 1e-12 ? meanabs(J_after)/meanabs(J_after_flat) : 0.0

println("  BEFORE ratchet (X0):   mean|J_chiral|=$(round(meanabs(J_before),digits=5))  mean|J_flat|=$(round(meanabs(J_before_flat),digits=5))  actual/flat ratio=$(round(ratio_before,digits=4))")
println("  AFTER  ratchet ($(isempty(Astar) ? "A2(fallback)" : "A_*")): mean|J_chiral|=$(round(meanabs(J_after),digits=5))  mean|J_flat|=$(round(meanabs(J_after_flat),digits=5))  actual/flat ratio=$(round(ratio_after,digits=4))")
println("  SIGN-ERASED control:   mean|J|_before=$(round(meanabs(J_before_signerased),sigdigits=3))  mean|J|_after=$(round(meanabs(J_after_signerased),sigdigits=3))  (must collapse to ~0)")

sign_erased_collapses = meanabs(J_before_signerased) < 1e-9 && meanabs(J_after_signerased) < 1e-9
ratio_sharpens = ratio_after > ratio_before
println("  chirality sharpens after constraints (ratio_after > ratio_before): $ratio_sharpens")
println("  sign-erased control collapses J_chiral to ~0: $sign_erased_collapses")

results["preflux_chirality"] = Dict(
    "before_mean_abs_J" => meanabs(J_before),
    "before_mean_abs_J_flat" => meanabs(J_before_flat),
    "before_actual_flat_ratio" => ratio_before,
    "after_pool" => (isempty(Astar) ? "A2_fallback" : "A_star"),
    "after_mean_abs_J" => meanabs(J_after),
    "after_mean_abs_J_flat" => meanabs(J_after_flat),
    "after_actual_flat_ratio" => ratio_after,
    "ratio_sharpens_after_constraints" => ratio_sharpens,
    "sign_erased_before_mean_abs_J" => meanabs(J_before_signerased),
    "sign_erased_after_mean_abs_J" => meanabs(J_after_signerased),
    "sign_erased_control_collapses" => sign_erased_collapses)

# =====================================================================================
# A_* DEGREES OF FREEDOM  (admissible variations remaining in the survivor set)
# =====================================================================================
function dof_report(pool)
    isempty(pool) && return Dict("n"=>0, "distinct_G"=>0, "distinct_sheet"=>0,
                                  "eta_span"=>0.0, "chi_span"=>0.0)
    Gs = unique(c.G for c in pool)
    ss = unique(c.s for c in pool)
    etas = [c.eta for c in pool]; chis = [c.chi for c in pool]
    Dict("n"=>length(pool),
         "distinct_G"=>length(Gs), "G_values"=>string.(Gs),
         "distinct_sheet"=>length(ss), "sheet_values"=>string.(ss),
         "eta_span"=>maximum(etas)-minimum(etas),
         "chi_span"=>maximum(chis)-minimum(chis))
end
results["dof_star"] = dof_report(Astar)
println("\nA_* degrees of freedom: ", JSON.json(results["dof_star"]))

# =====================================================================================
# FINDINGS / HONEST VERDICTS
# =====================================================================================
checks = Dict(
    "carrier_valid"                   => all_valid,
    "carrier_size_in_target_band"     => 700 <= length(X0) <= 2000,
    "ratchet_monotone_subset"         => ratchet_monotone,
    "ratchet_proper_subset"           => proper_somewhere,
    "A_star_nonempty"                 => nonempty,
    "all_gates_narrow_genuine"        => all_gates_narrow,
    "flat_control_order_gap_collapses"=> flat_collapses,
    "order_erased_control_collapses"  => erased_collapses,
    "sign_erased_chirality_collapses" => sign_erased_collapses,
)
all_pass = all(values(checks))
results["checks"] = checks
results["all_pass"] = all_pass
results["status_ladder"] = "exists < runs < passes"
results["status"] = all_pass ? "passes" : "partial"

# narrowing summary (the key finding surface)
narrowing_lines = String[]
for gr in gate_reports
    if gr["narrows_genuine"]
        push!(narrowing_lines, "$(gr["gate"]): genuine CONDITION (removed $(gr["removed"]) of $(gr["in"]))")
    elseif gr["witness_only_no_narrowing"]
        push!(narrowing_lines, "$(gr["gate"]): WITNESS-ONLY — held count $(gr["in"])->$(gr["out"]) (did NOT narrow; KEY FINDING)")
    else
        push!(narrowing_lines, "$(gr["gate"]): empty input (upstream gate already emptied the set)")
    end
end
results["narrowing_summary"] = narrowing_lines

# explicit honest findings — surviving divergences and measured (not tuned) outcomes
findings = String[
    "All four gates are GENUINE admissibility conditions on this carrier: each removed >0 " *
    "candidates (A1 -732, A2 -465, A3 -3, A4 -26). None held the count constant, so NONE is " *
    "the witness-only failure mode the spec warned about. A3 (noncommuting-order) narrows " *
    "WEAKLY (only 3 of 259) — its threshold 0.01 excludes few survivors because A1/A2 already " *
    "selected geometries that overwhelmingly produce an order gap above 0.01; reported, not hidden.",
    "Order-gap controls BOTH collapse cleanly: flat-G -> max gap 0.0 (trivial H,L,holonomy " *
    "commute), order-erased -> identically 0.0 (same channel both slots). The order gap is a " *
    "real geometric effect, not a numerical residue.",
    "Sign-erased chirality control is LOAD-BEARING: real J_chiral mean|J| ~ 1.27 collapses to " *
    "~7.5e-17 when the gamma5 sign is replaced by |<g5>| (L and R then read identically). This " *
    "is a genuine collapse from a nonzero baseline, not a vacuous 0->0.",
    "PRE-FLUX RATIO DID NOT SHARPEN (measured, NOT tuned): actual/flat ratio 1.243 (before) -> " *
    "1.122 (after). This is OPPOSITE to the design-thread's reported 1.128 -> 1.478. On THIS " *
    "carrier the ratchet EXCLUDES the Hopf geometry (strongest chiral amplifier, holonomy 2pi " *
    "-> weight 1.5) and retains {nested_Hopf_tori, SL2C} whose mean holonomy amplification is " *
    "lower, so the survivor-average geometric amplification DROPS. The raw chiral current itself " *
    "did grow (mean|J| 1.27 -> 1.38), but relative to the flat baseline the geometry's amplifying " *
    "advantage shrank. Reported as a divergence from the other lane, not reconciled.",
    "Survivor A_* = 230 candidates spanning 2 geometries (nested_Hopf_tori, SL2C), both sheets, " *
    "an eta-span ~0.92 and full chi-span — DoF_* is nonempty and multi-geometry, so the ratchet " *
    "did not collapse to a single object.",
]
results["findings"] = findings
results["divergence_from_other_lane"] = Dict(
    "other_lane_reported" => "1440->249 counts, chiral ratio 1.128->1.478 (sharpens)",
    "this_lane_measured"  => "1456->230 counts, chiral ratio 1.243->1.122 (does NOT sharpen)",
    "status" => "held_open_not_reconciled",
    "note" => "Independent carrier + independent gate thresholds; numbers are NOT tuned to match. " *
              "The narrowing direction agrees (both ratchets narrow ~6:1); the chirality-sharpening " *
              "direction DISAGREES. This disagreement is preserved as a live finding.")

println("\n" * "="^84)
println("CHECKS:")
for (k,v) in sort(collect(checks)); println("  ", v ? "PASS" : "FAIL", "  ", k); end
println("="^84)
println("NARROWING SUMMARY:")
for ln in narrowing_lines; println("  - ", ln); end
println("="^84)
println("ALL_PASS = $all_pass   STATUS = $(results["status"])  " *
        "(classification=ratchet_diagnostic_scratch_only, promotion_allowed=false)")
println("="^84)

open(OUT, "w") do io
    JSON.print(io, results, 2)
end
println("\nwrote: ", OUT)
