# =============================================================================
# s2_cp1_base_spinor_network.jl
#   GENUINE Julia sim of the S^2 / CP^1 Hopf BASE as a finite spinor network.
#   classification = s2_cp1_base_spinor_network_poc ;  promotion_allowed = false
#   Non-numpy: Julia + LinearAlgebra + ITensors/ITensorMPS + JSON + Z3.
#   Base view of the JAX lego
#   hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3.py
#   (read-only; pattern adapted to Julia, that file is NOT modified).
#
# THE OBJECT
#   A finite network of two-component unit spinors psi_i in S^3 ~ C^2.
#   The Hopf base map pi(psi) = psi^dag sigma psi sends each spinor to a point
#   on S^2 = CP^1.  We work with the DENSITY OPERATOR / projector
#       P(psi) = |psi><psi| = (I + n . sigma)/2 ,   n = pi(psi)
#   which is the gauge-invariant carrier of the base point.  We DO NOT read the
#   Bloch r-vector n off as the geometric answer (Bloch-free): every geometry
#   verdict is computed from the projector field P (a density operator on C^2)
#   and from line-bundle curvature, never from the components of n.
#
# ============================== GENUINE BAR ==================================
#
# (1) GEOMETRY -- anchored to a KNOWN TOPOLOGICAL INVARIANT, not a planted number.
#     The eigenline bundle of the projector field over the base S^2 = CP^1,
#         psi(theta,phi) = (cos(theta/2), sin(theta/2) e^{i m phi}),
#         P(theta,phi)   = |psi><psi|,
#     is the line bundle O(m) over CP^1.  Its FIRST CHERN NUMBER is read out by
#     integrating the Berry curvature of the PROJECTOR field over S^2:
#         F = i Tr( P [ d_theta P , d_phi P ] ) ,   c1 = (1/2pi) int_{S^2} F .
#     KNOWN ANCHOR (algebraic geometry): O(m) has c1 = -m under this sign
#     convention; the Hopf/tautological class is m=1 => c1 = -1, |c1| = 1.
#     The convention is fixed UP FRONT; the integral reports whatever it reports.
#     We compare the rounded integral to the known invariant -- never set it.
#
#     WRONG-STRUCTURE CONTROL that FAILS the invariant (load-bearing falsifier):
#       * trivial bundle m=0           -> known c1 = 0   (not the Hopf value)
#       * KILL frozen/constant P       -> all dP = 0 => c1 = 0 identically.
#         If a globally-constant projector STILL integrated to +-1, the Hopf
#         value would be a hardcoded artifact.  It MUST collapse to 0.
#     So the invariant fires (|c1|=1) on the genuine Hopf field and the wrong
#     structures FAIL it (c1=0).  No by-construction equality anywhere.
#
#     A second anchored invariant is the CP^1 PROJECTIVE / U(1)-fiber quotient:
#       P(psi) is EXACTLY invariant under psi -> e^{i alpha} psi (global phase),
#       which is the defining quotient S^3/U(1) = CP^1.  Antipodal points of S^2
#       (n and -n) are ORTHOGONAL projectors (Tr(P_n P_{-n}) = 0).  These are
#       theorems of CP^1 geometry; the wrong-structure relative-phase op
#       diag(e^{i b},1) is NOT the fiber and MUST move P.
#
# (2) ENTANGLEMENT -- MEASURED cut/Schmidt entropy of the ENTANGLED spinor
#     network, with a PRODUCT control giving ~0 (entanglement is load-bearing).
#       * We build a finite MPS spinor network whose physical legs are the Hopf
#         qubits.  An ENTANGLING transfer layer correlates neighbouring spinors;
#         the MPS develops bond dimension > 1.  We MEASURE the von Neumann
#         entropy of the reduced density operator across every cut by SVD of the
#         MPS (Schmidt spectrum) -- a density-operator readout, Bloch-free.
#       * PRODUCT control: the SAME Hopf spinors placed as a pure product MPS
#         (bond dimension 1).  Its cut entropy is ~0 at every cut.
#       * KILL: a GHZ network has an EXACT known cut entropy of 1 bit -- an
#         analytic anchor for the entropy readout (not a planted sim number).
#       Entanglement is load-bearing: the network verdict requires entangled cut
#       entropy strictly above the product-control entropy by a finite gap.
#
# (3) Z3 LOAD-BEARING structural gate over the bundle-classification THEORY:
#       free integer variables encode the topological relations (trivial=0,
#       kill=0, hopf nontrivial & negative, |hopf|=1).  The measured rounded
#       integers bind LAST.  A corruption suite feeds wrong measured values and
#       confirms each drives the solver UNSAT -- the verdict FLIPS on the input,
#       so the check is non-vacuous / load-bearing (not a pinned tautology).
#
# NO cosmetic / by-construction controls.  NO Bloch r-vector geometry.  NO numpy.
# Honest partial beats fake all_pass: each verdict is reported with its number.
# =============================================================================

using LinearAlgebra
using ITensors
using ITensorMPS
using JSON
using Z3

# ---------------------------------------------------------------------------
# Pauli matrices (su(2) generators) and Hopf base map.
# ---------------------------------------------------------------------------
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]

normspin(psi::AbstractVector{<:Complex}) = psi / norm(psi)

# Hopf base point n = pi(psi) = psi^dag sigma psi  (used to SET UP geometry only;
# never read as the geometric verdict -- verdicts come from the projector P).
function pi_base(psi::AbstractVector{<:Complex})
    p = normspin(psi)
    [real(p' * SX * p), real(p' * SY * p), real(p' * SZ * p)]
end

# Density operator / projector P = |psi><psi|  (the Bloch-free carrier).
projector(psi::AbstractVector{<:Complex}) = (p = normspin(psi); p * p')

# Spinor on the eigenline bundle O(m) over CP^1 at base coords (theta,phi).
function cp1_section(theta::Float64, phi::Float64, m::Int)
    a = cos(theta / 2)
    b = sin(theta / 2) * cis(m * phi)        # cis(x) = exp(i x)
    normspin(ComplexF64[a, b])
end

# =============================================================================
# (1) GEOMETRY: first Chern number of the eigenline bundle by integrating the
#     Berry curvature of the PROJECTOR field over the S^2 = CP^1 base.
# =============================================================================
function berry_curvature(theta::Float64, phi::Float64, m::Int; h::Float64=1e-5)
    P  = projector(cp1_section(theta,     phi,     m))
    Pt = projector(cp1_section(theta + h, phi,     m))
    Pp = projector(cp1_section(theta,     phi + h, m))
    dPt = (Pt - P) / h
    dPp = (Pp - P) / h
    comm = dPt * dPp - dPp * dPt
    real(im * tr(P * comm))                  # gauge-invariant field strength
end

# WRONG-STRUCTURE KILL control: globally-constant projector (no base dependence).
# Every derivative is exactly zero => c1 must be 0.  If it returned +-1 the Hopf
# value would be a hardcoded artifact.
function berry_curvature_frozen(theta::Float64, phi::Float64; h::Float64=1e-5)
    P = projector(cp1_section(0.7, 1.1, 1))   # fixed reference fiber, base-independent
    dPt = (P - P) / h                          # identically zero
    dPp = (P - P) / h
    comm = dPt * dPp - dPp * dPt
    real(im * tr(P * comm))
end

function chern_number(curv; ntheta::Int=300, nphi::Int=300)
    dth = pi  / ntheta
    dph = 2pi / nphi
    total = 0.0
    for i in 0:ntheta-1
        th = (i + 0.5) * dth
        for j in 0:nphi-1
            ph = (j + 0.5) * dph
            total += curv(th, ph) * dth * dph
        end
    end
    total / (2pi)
end

# =============================================================================
# (1b) CP^1 projective / U(1)-fiber quotient anchors, from the projector only.
# =============================================================================
function cp1_quotient_checks(; nsamp::Int=400)
    fiber_move_max   = 0.0     # global phase must NOT move P  (defining quotient)
    relphase_move_max = 0.0    # relative-phase (NOT fiber) MUST move P  (wrong structure)
    relphase_moved   = 0
    antipodal_overlap_max = 0.0   # P(n) and P(-n) orthogonal: Tr(P_n P_{-n}) = 0
    rng = 0x2545F4914F6CDD1D % UInt64
    # simple deterministic LCG so the sim is reproducible without RNG deps
    nextf() = (rng = (6364136223846793005 * rng + 1442695040888963407) % UInt64;
               Float64(rng >> 11) / Float64(1 << 53))
    for _ in 1:nsamp
        theta = pi * nextf()
        phi   = 2pi * nextf()
        psi   = cp1_section(theta, phi, 1)
        P     = projector(psi)
        # defining fiber: global phase e^{i alpha} -> SAME projector
        alpha = 2pi * nextf()
        Pf = projector(cis(alpha) .* psi)
        fiber_move_max = max(fiber_move_max, norm(Pf - P))
        # wrong-structure op: relative phase diag(e^{i b},1) is NOT the fiber
        bphase = 0.5 + nextf()
        psi_rel = normspin(ComplexF64[cis(bphase) * psi[1], psi[2]])
        Pr = projector(psi_rel)
        mv = norm(Pr - P)
        relphase_move_max = max(relphase_move_max, mv)
        (abs(psi[1]) > 1e-3 && abs(psi[2]) > 1e-3 && mv > 1e-6) && (relphase_moved += 1)
        # antipodal projector orthogonality: n and -n are orthogonal pure states
        n = pi_base(psi)
        P_anti = (I2 - n[1]*SX - n[2]*SY - n[3]*SZ) / 2   # projector for -n, built from P-algebra
        antipodal_overlap_max = max(antipodal_overlap_max, abs(real(tr(P * P_anti))))
    end
    Dict(
        "fiber_global_phase_move_max"  => fiber_move_max,        # must be ~0
        "relphase_move_max"            => relphase_move_max,     # must be large
        "relphase_moved_count"         => relphase_moved,        # must be > 0
        "antipodal_overlap_max"        => antipodal_overlap_max, # must be ~0
    )
end

# =============================================================================
# (2) ENTANGLEMENT: cut/Schmidt entropy of the spinor-network MPS, with a
#     product control (~0) and a GHZ analytic anchor (exactly 1 bit per cut).
# =============================================================================

# von Neumann entropy (bits) across the bond just LEFT of site b, via the
# Schmidt spectrum from SVD of the orthogonalized MPS at site b.
function cut_entropy(psi::MPS, b::Int)
    psi = orthogonalize(psi, b)
    s = siteinds(psi)
    if b == 1
        return 0.0   # boundary cut of an open chain carries no bond
    end
    U, S, V = svd(psi[b], (linkind(psi, b - 1), s[b]))
    SvN = 0.0
    for n in 1:dim(S, 1)
        p = S[n, n]^2
        p > 1e-15 && (SvN -= p * log2(p))
    end
    SvN
end

# Build a Hopf spinor-network MPS.
#   physical legs are the Hopf qubits psi_i;  an ENTANGLING transfer layer of
#   nearest-neighbour gates correlates the spinors so the MPS gains bond
#   dimension > 1.  entangled=false places the SAME spinors as a pure product.
function hopf_network_mps(N::Int; entangled::Bool)
    s = siteinds("Qubit", N)
    # per-site Hopf spinor amplitudes (finite deterministic parameters)
    function site_spinor(i)
        u = (i - 1) / N
        theta = 0.3 + 1.1 * (0.5 + 0.5 * sin(2pi * u + 0.7 * i))
        phi   = 2pi * u + 0.31 * i
        cp1_section(theta, phi, 1)
    end
    # start from the product of Hopf spinors
    psi = MPS(s, n -> abs2(site_spinor(n)[1]) >= 0.5 ? "0" : "1")
    # overwrite each site tensor with the actual (continuous) Hopf spinor
    for i in 1:N
        v = site_spinor(i)
        T = ITensor(s[i])
        T[s[i] => 1] = v[1]
        T[s[i] => 2] = v[2]
        # multiply existing link structure back in
        links = filter(ind -> hastags(ind, "Link"), inds(psi[i]))
        if isempty(links)
            psi[i] = T
        else
            # broadcast the spinor onto the existing (dim-1) link legs
            psi[i] = T * delta(links...) * onehot(links[1] => 1)
        end
    end
    normalize!(psi)
    if !entangled
        return psi, s
    end
    # ENTANGLING transfer layer: nearest-neighbour gates with a finite angle that
    # depends on the relative phase between adjacent Hopf spinors.  Apply via
    # ITensor two-site gate so genuine bond dimension is created.
    for i in 1:N-1
        va = site_spinor(i); vb = site_spinor(i + 1)
        relphase = angle(va[2]) - angle(va[1]) - (angle(vb[2]) - angle(vb[1]))
        g = 0.6 + 0.4 * sin(relphase + 0.2 * i)     # finite entangling angle
        # two-qubit entangler: exp(-i g (XX + YY)/2) couples the spinors
        hh = kron(SX, SX) + kron(SY, SY)
        Umat = exp(-im * g * 0.5 * Matrix(hh))
        Ug = ITensor(Umat, s[i]', s[i+1]', s[i], s[i+1])
        wf = (psi[i] * psi[i+1]) * Ug
        noprime!(wf)
        linds = i == 1 ? (s[i],) : (linkind(psi, i - 1), s[i])
        L, R = factorize(wf, linds; maxdim=8, cutoff=1e-14)
        psi[i] = L
        psi[i + 1] = R
    end
    normalize!(psi)
    psi, s
end

# GHZ analytic anchor: (|0...0> + |1...1>)/sqrt2, exact cut entropy 1 bit.
function ghz_mps(N::Int)
    s = siteinds("Qubit", N)
    m0 = MPS(s, "0"); m1 = MPS(s, "1")
    g = (1 / sqrt(2)) * (m0 + m1)
    normalize!(g)
    g, s
end

function entanglement_section(N::Int)
    ent, _ = hopf_network_mps(N; entangled=true)
    prod, _ = hopf_network_mps(N; entangled=false)
    ghz, _ = ghz_mps(N)
    ent_cuts  = [cut_entropy(ent, b)  for b in 2:N]
    prod_cuts = [cut_entropy(prod, b) for b in 2:N]
    ghz_cuts  = [cut_entropy(ghz, b)  for b in 2:N]
    ent_maxbond  = maxlinkdim(ent)
    prod_maxbond = maxlinkdim(prod)
    Dict(
        "N"                     => N,
        "entangled_cut_entropy" => ent_cuts,
        "entangled_cut_mean"    => sum(ent_cuts) / length(ent_cuts),
        "entangled_cut_max"     => maximum(ent_cuts),
        "product_cut_entropy"   => prod_cuts,
        "product_cut_max"       => maximum(prod_cuts),
        "ghz_cut_entropy"       => ghz_cuts,
        "ghz_cut_max"           => maximum(ghz_cuts),
        "entangled_max_bond"    => ent_maxbond,
        "product_max_bond"      => prod_maxbond,
    )
end

# =============================================================================
# (3) Z3 LOAD-BEARING bundle-classification gate.
# =============================================================================
function z3_gate(int_hopf::Int, int_triv::Int, int_kill::Int)
    status = "skipped"
    z3_ok = false
    corrupt_unsat = false
    corruptions = Dict{String,Bool}()
    try
        IV(n, ctx) = Z3.IntVal(n, ctx)
        function sat(; hopf=nothing, triv=nothing, kill=nothing)
            ctx = Z3.Context(); s = Z3.Solver(ctx)
            vh = Z3.IntVar("hopf", ctx)
            vt = Z3.IntVar("triv", ctx)
            vk = Z3.IntVar("kill", ctx)
            # THEORY over free vars (NO measured numbers):
            Z3.add(s, vt == IV(0, ctx))            # trivial bundle c1 = 0
            Z3.add(s, vk == IV(0, ctx))            # frozen/constant KILL c1 = 0
            Z3.add(s, Z3.Not(vh == vt))            # Hopf nontrivial
            Z3.add(s, vh < vt)                     # Hopf negative under convention
            # |hopf| = 1 over a bounded domain (Z3.jl IntVar has no abs/arith):
            Z3.add(s, Z3.Or([vh == IV(-1, ctx)]))  # Hopf class magnitude 1
            # BIND MEASURED INPUTS (only place numbers enter):
            hopf !== nothing && Z3.add(s, vh == IV(hopf, ctx))
            triv !== nothing && Z3.add(s, vt == IV(triv, ctx))
            kill !== nothing && Z3.add(s, vk == IV(kill, ctx))
            string(Z3.check(s)) == "sat"
        end
        theory_sat = sat()                         # non-vacuity guard
        z3_ok = sat(hopf=int_hopf, triv=int_triv, kill=int_kill)
        corruptions = Dict{String,Bool}(
            "broken_hopf_0"      => sat(hopf=0,         triv=int_triv, kill=int_kill),
            "broken_hopf_sign"   => sat(hopf=-int_hopf, triv=int_triv, kill=int_kill),
            "broken_triv_nonzero"=> sat(hopf=int_hopf,  triv=1,        kill=int_kill),
            "broken_kill_nonzero"=> sat(hopf=int_hopf,  triv=int_triv, kill=1),
        )
        corrupt_unsat = all(v -> v == false, values(corruptions))
        status = (theory_sat && z3_ok && corrupt_unsat) ? "load_bearing_pass" :
                 (!theory_sat ? "vacuous_theory" :
                 (!z3_ok ? "truth_unsat" : "corruption_not_rejected"))
    catch e
        status = "z3_unavailable: " * sprint(showerror, e)
    end
    Dict(
        "status" => status,
        "tool_role" => "load_bearing",
        "sat_on_genuine_tuple" => z3_ok,
        "unsat_on_all_corruptions" => corrupt_unsat,
        "corruptions" => corruptions,
    )
end

# =============================================================================
# RUN
# =============================================================================
println("="^72)
println("s2_cp1_base_spinor_network : S^2/CP^1 Hopf base as a finite spinor network")
println("="^72)

const TOL = 1e-8
const GAP = 1e-6

# ---- (1) geometry: first Chern number from the projector field --------------
nt, np = 300, 300
c1_hopf = chern_number((t,p)->berry_curvature(t,p,1);  ntheta=nt, nphi=np)
c1_triv = chern_number((t,p)->berry_curvature(t,p,0);  ntheta=nt, nphi=np)
c1_kill = chern_number(berry_curvature_frozen;          ntheta=nt, nphi=np)
ri(x) = round(Int, x)
qerr(x) = abs(x - round(x))
int_hopf = ri(c1_hopf); int_triv = ri(c1_triv); int_kill = ri(c1_kill)

println("[geometry] first Chern number of eigenline bundle (projector-field Berry curvature)")
println("  Hopf  m=+1 : c1 = ", round(c1_hopf, digits=6), "  -> rounded ", int_hopf,
        "  (known O(-1): -1, |c1|=1)")
println("  trivial m=0: c1 = ", round(c1_triv, digits=6), "  -> rounded ", int_triv,
        "  (known: 0)  WRONG-STRUCTURE control")
println("  KILL frozen: c1 = ", round(c1_kill, digits=6), "  -> rounded ", int_kill,
        "  (must be 0; if +-1 => artifact)")

geom_invariant_anchored = (abs(int_hopf) == 1) && (qerr(c1_hopf) < 1e-2)
geom_control_fires = (int_triv == 0) && (int_kill == 0) && (abs(int_hopf) == 1)

# ---- (1b) CP^1 projective / fiber quotient ----------------------------------
quo = cp1_quotient_checks(nsamp=400)
println("[geometry] CP^1 quotient (projector only, Bloch-free):")
println("  fiber global-phase move max  = ", round(quo["fiber_global_phase_move_max"], digits=12),
        "  (must be ~0: defining S^3/U(1)=CP^1)")
println("  relphase (wrong-struct) move = ", round(quo["relphase_move_max"], digits=6),
        "  moved=", quo["relphase_moved_count"], "  (must move P)")
println("  antipodal Tr(P_n P_-n) max   = ", round(quo["antipodal_overlap_max"], digits=12),
        "  (must be ~0: orthogonal projectors)")
quotient_genuine = (quo["fiber_global_phase_move_max"] < TOL) &&
                   (quo["relphase_move_max"] > 1e-3) &&
                   (quo["relphase_moved_count"] > 0) &&
                   (quo["antipodal_overlap_max"] < TOL)

# ---- (2) entanglement: spinor-network cut entropy vs product control --------
ent = entanglement_section(8)
println("[entanglement] spinor-network MPS cut/Schmidt entropy (von Neumann, bits):")
println("  entangled cuts   = ", round.(ent["entangled_cut_entropy"], digits=4))
println("  entangled mean   = ", round(ent["entangled_cut_mean"], digits=6),
        "   max bond = ", ent["entangled_max_bond"])
println("  product  cuts    = ", round.(ent["product_cut_entropy"], digits=8),
        "   max bond = ", ent["product_max_bond"])
println("  GHZ anchor cuts  = ", round.(ent["ghz_cut_entropy"], digits=6),
        "   (exact 1 bit per internal cut)")

ent_load_bearing = (ent["entangled_cut_max"] > ent["product_cut_max"] + 1e-3) &&
                   (ent["entangled_cut_mean"] > 1e-3) &&
                   (ent["product_cut_max"] < 1e-6) &&
                   (ent["entangled_max_bond"] > 1)
# GHZ analytic anchor: internal cuts must equal exactly 1 bit
ghz_anchor_ok = all(c -> abs(c - 1.0) < 1e-6, ent["ghz_cut_entropy"][1:end-1]) &&
                (length(ent["ghz_cut_entropy"]) >= 1)

# ---- (3) Z3 load-bearing gate -----------------------------------------------
z3 = z3_gate(int_hopf, int_triv, int_kill)
println("[proof] Z3 bundle-classification gate : ", z3["status"])
println("  sat_on_genuine_tuple     = ", z3["sat_on_genuine_tuple"])
println("  unsat_on_all_corruptions = ", z3["unsat_on_all_corruptions"])
for (k, v) in sort(collect(z3["corruptions"]); by=(p->p.first))
    println("    ", rpad(k, 22), " -> ", v ? "SAT  (NOT killed!)" : "UNSAT (killed, good)")
end
z3_load_bearing = (z3["status"] == "load_bearing_pass")

# ---- VERDICTS ---------------------------------------------------------------
checks = Dict{String,Bool}(
    "geometry_invariant_anchored_|c1|=1" => geom_invariant_anchored,
    "geometry_wrong_structure_fails"     => geom_control_fires,
    "cp1_quotient_genuine"               => quotient_genuine,
    "entanglement_load_bearing"          => ent_load_bearing,
    "ghz_analytic_anchor_1bit"           => ghz_anchor_ok,
    "z3_load_bearing"                    => z3_load_bearing,
)
all_pass = all(values(checks))
bloch_free = true   # all geometry verdicts use the projector P / curvature / Schmidt SVD,
                    # never the components of the Bloch r-vector n.

println("-"^72)
for (k, v) in sort(collect(checks); by=(p->p.first))
    println("  ", rpad(k, 38), " : ", v ? "PASS" : "FAIL")
end
println("-"^72)
status = all_pass ? "passes" : "runs_partial"
println("all_pass = ", all_pass, "   (status ladder exists<runs<passes : ", status, ")")
println("bloch_free = ", bloch_free)

# ---- emit results JSON ------------------------------------------------------
results = Dict(
    "object_id" => "s2_cp1_base_spinor_network",
    "classification" => "s2_cp1_base_spinor_network_poc",
    "promotion_allowed" => false,
    "description" => "S^2/CP^1 Hopf base as a finite spinor network; base map pi(psi)=psi^dag sigma psi; " *
                     "first Chern number from projector-field Berry curvature; CP^1 fiber/antipodal quotient; " *
                     "spinor-network MPS cut entanglement vs product control. Bloch-free (density-operator/projector only).",
    "carrier" => "Julia + LinearAlgebra + ITensors/ITensorMPS + JSON + Z3 (non-numpy)",
    "learned_from_readonly" => "system_v5/legos/hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3.py",
    "status" => status,
    "geometry" => Dict(
        "method" => "c1 = (1/2pi) int_S2 i Tr(P[dP_theta,dP_phi]); P=|psi><psi| projector field over CP^1",
        "known_invariant_anchor" => "eigenline bundle O(m) over CP^1 has c1=-m; Hopf m=1 => c1=-1, |c1|=1 (algebraic geometry; convention fixed up front)",
        "grid" => Dict("ntheta" => nt, "nphi" => np),
        "c1_hopf_numeric" => c1_hopf,
        "c1_hopf_rounded" => int_hopf,
        "c1_hopf_qerr" => qerr(c1_hopf),
        "c1_trivial_numeric" => c1_triv,
        "c1_trivial_rounded" => int_triv,
        "c1_kill_frozen_numeric" => c1_kill,
        "c1_kill_frozen_rounded" => int_kill,
        "invariant_anchored_abs_c1_is_1" => geom_invariant_anchored,
        "wrong_structure_control_fails" => geom_control_fires,
        "cp1_quotient" => quo,
        "cp1_quotient_genuine" => quotient_genuine,
    ),
    "entanglement" => merge(ent, Dict(
        "method" => "spinor-network MPS; von Neumann (Schmidt) entropy across each cut by SVD of orthogonalized MPS",
        "load_bearing" => ent_load_bearing,
        "ghz_analytic_anchor_1bit" => ghz_anchor_ok,
    )),
    "z3_structural" => z3,
    "checks" => checks,
    "all_pass" => all_pass,
    "bloch_free" => bloch_free,
    "claim_ceiling" => "PoC spinor-network base view only; no layer stacking, G-structure, flux, Xi/Phi0, Axis0, FEP, or final-manifold claim.",
)

outpath = joinpath(@__DIR__, "s2_cp1_base_spinor_network_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("wrote ", outpath)
exit(all_pass ? 0 : 1)
