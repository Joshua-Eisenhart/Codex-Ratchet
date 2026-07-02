#!/usr/bin/env julia
# =====================================================================================
# substrate_effect_frame_conjugation.jl  —  THE DECISIVE CHEAP TEST of the owner's
#   GEOMETRIC SUBSTRATE-NESTING claim, attacked from the finite DENSITY-OPERATOR side
#   so it does NOT need PEPS / CTMRG (those are blocked: decorative on product states,
#   substrate effect swamped on unoptimized iPEPS, LBFGS/HagerZhang segfault path —
#   see nested_peps2d_substrate_effect_opt_results.json).
#
#   classification = substrate_effect_frame_conjugation_poc ; promotion_allowed = false.
#   NO CTMRG, NO PEPS, NO optimization. Pure 2x2 density-operator algebra + SU(2) frames
#   built from GENUINE geometry. < 90 s.
# -------------------------------------------------------------------------------------
# OBJECT_ID: substrate_effect_frame_conjugation
#
# CLAIM CEILING: this object MEASURES, on a finite density-operator carrier, the
#   operational difference E(A) = sup_rho ||Phi_B^A(rho) - Phi_B(rho)||_1 between an
#   upper Weyl operation B run BARE and the same B run DRESSED by a substrate frame
#   U_A drawn from genuine geometry (Hopf spinor frame, nested-Hopf-tori leaf frame,
#   Clifford rotor). It tests the OWNER'S SEPARATE GEOMETRIC-SUBSTRATE claim ("Weyl
#   spinors run ON nested-Hopf-tori geometry, and THE SUBSTRATE CHANGES THE OPERATION")
#   against four anti-tautology requirements + a random-unitary sharper control.
#   It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A substrate that shows a real
#   structured effect here is a CANDIDATE geometric interface, NOT a proven nesting
#   layer. promotion_allowed = false. The temporal-order spine
#   (order_null_killtest.jl) is validated separately; this is the SEPARATE geometric
#   substrate axis, not a re-test of order-noncommutation.
#
# -------------------------------------------------------------------------------------
# THE FINITE MODEL OF "SUBSTRATE CHANGES OPERATION":
#   A substrate A (lower geometry) supplies a frame UNITARY U_A in SU(2). The Weyl
#   operation B (upper) run ON substrate A is the DRESSED channel
#       Phi_B^A(rho) = U_A * Phi_B(U_A' * rho * U_A) * U_A' .
#   This is "run B in the frame the substrate sets". The substrate EFFECT is
#       E(A) = max_rho ||Phi_B^A(rho) - Phi_B(rho)||_1     (sample over 20+1 rhos).
#
#   U_A comes from GENUINE geometry (read, not invented):
#     - HOPF frame:        the Hopf representative spinor fiber_rep(theta,phi) on
#                          S^3 in C^2 (G_hopf_fibration.jl) -> SU(2) frame.
#     - NESTED-TORI frame: the nested-Hopf-tori leaf spinor (cos th e^{ia}, sin th e^{ib})
#                          (G_nested_hopf_tori.jl, S3pt foliation) -> SU(2) frame.
#     - CLIFFORD rotor:    exp(-i ang/2 n.sigma), the SU(2)~even-Cl(3,0) rotor from
#                          clifford_rotor_spinor_network_entanglement.jl generators.
#
#   The upper operation B is the GENUINE Weyl operation (read, not invented), tested in
#   TWO genuine forms because the result DEPENDS on whether B is unitary or dissipative:
#     - B = Phi_Te : x-pinch DEPHASING (CPTP, non-unitary)  [L11_layer_bf / order_null]
#     - B = Phi_WeylL : Weyl-L GKSL channel, H=+H0 (Hopf site), jump sigma_-  (non-unitary)
#                       [L7_layer_bf / L10_layer_bf / order_null_killtest gksl_step_evolve]
#     - B = Phi_Fi : x-rotation UNITARY  [included to EXPOSE the trap: for a unitary B,
#                    E(A) reduces to ||[U_A, V]|| and a random unitary matches it — the
#                    "geometry is not load-bearing, only non-commutation" mode.]
#
# THE FOUR ANTI-TAUTOLOGY REQUIREMENTS (all must hold for substrate_effect_real_and_nests):
#   (1) POSITIVE:  E(A_genuine) > floor for genuine geometry A (Hopf, nested-tori, Clifford).
#   (2) SUBSTRATE-DEPENDENT: E differs ACROSS genuine substrates A (Hopf vs Clifford vs
#       nested-tori give DIFFERENT E) — not a single constant. Report the spread.
#   (3) FLAT KILL-CONTROL: E(A_flat) ~ 0 when U_A = I (no geometry) — effect VANISHES.
#       PLUS the SHARPER control: a generic RANDOM unitary that is NOT a geometry frame.
#       If a random U gives the SAME E as the Hopf frame, the 'geometry' is not
#       load-bearing — only non-commutation is. We report whether genuine-geometry E is
#       DISTINGUISHABLE from random-unitary E (statistically), per upper operator.
#   (4) NESTING COMPOUNDS: nested substrate A-on-A' (U = U_A * U_A', tori nested in tori)
#       gives E(nested) DISTINCT from E(single A) and from E(flat). Report
#       E(flat) < E(single) vs E(nested) ordering, and whether nesting is non-trivially
#       different (not just U_A*U_A' collapsing to another single rotation).
#   PLUS: Z3 verdict-flip (genuine substrate spread UNSAT vs flat SAT), explicit noise
#   floor, seed-robust check.
#
# DECISIVE VERDICT (per upper operator B and overall):
#   substrate_effect_real_and_nests : all 4 hold AND genuine geometry is DISTINGUISHABLE
#       from a random unitary — the geometric substrate effect is REAL on the finite
#       carrier and PEPS was never needed for THIS claim.
#   substrate_effect_is_just_noncommutation : positive holds but requirement 3 fails — a
#       random unitary gives the same effect, so 'geometry' is not load-bearing, only
#       generic conjugation. (Expected for the UNITARY upper operator.)
#   substrate_effect_trivial_or_needs_geometric_carrier : E vanishes or shows no
#       substrate-dependence/nesting structure on finite frames — the real geometric
#       carrier is genuinely required, Path B (PEPS) forced.
#
# Brutally honest with the E numbers for each substrate and each control.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "substrate_effect_frame_conjugation_results.json")
const SEED   = 20260602
const N_RHO  = 20            # 20 + 1 (the +1 is maximally-mixed) random density operators

# ---------- single-qubit operators (density-operator world only) ----------
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SP = ComplexF64[0 1; 0 0]   # sigma_+  (raising / source)
const SM = ComplexF64[0 0; 1 0]   # sigma_-  (lowering / sink)
const Qp = (I2 + SX) / 2
const Qm = (I2 - SX) / 2

hs(A)         = sqrt(real(tr(A' * A)))   # Hilbert-Schmidt norm
trace_norm(M) = sum(svdvals(M))          # Schatten-1 (||.||_1) — the metric for E(A)

# =====================================================================================
# GENUINE UPPER OPERATION B (quoted from L11_layer_bf.jl / L7_layer_bf.jl / order_null_killtest.jl)
# All density-operator -> density-operator. No Bloch r-vector.
# =====================================================================================
# x-pinch DEPHASING channel (non-unitary CPTP) — L11_layer_bf.jl Phi_Te
Phi_Te(rho, q) = (1 - q) * rho + q * (Qp * rho * Qp + Qm * rho * Qm)
# x-rotation UNITARY channel — L11_layer_bf.jl Phi_Fi (included to EXPOSE the trap)
Ux(theta) = ComplexF64[cos(theta/2) (-im*sin(theta/2)); (-im*sin(theta/2)) cos(theta/2)]
Phi_Fi(rho, theta) = Ux(theta) * rho * Ux(theta)'

# Weyl-L GKSL channel (non-unitary, finite-time CPTP) — L7/L10_layer_bf + order_null_killtest
dissipator(L, rho)      = L*rho*L' - 0.5*((L'*L)*rho + rho*(L'*L))
commutator_flow(H, rho) = -im * (H*rho - rho*H)
function gksl_step_evolve(rho0, H, L; gamma=1.0, eps=1.0, T=4.0, steps=400)
    dt = T/steps; r = rho0
    for _ in 1:steps
        r = r + dt*(gamma*dissipator(L, r) + eps*commutator_flow(H, r))
        r = (r + r')/2
        tr_r = real(tr(r)); abs(tr_r) > 1e-12 && (r = r/tr_r)
    end
    return r
end
# Hopf-projected base Hamiltonian H0 = n.sigma at a fixed Hopf site (L10 hopf_h0 form).
function hopf_h0(phi::Float64, chi::Float64, eta::Float64)
    psi = ComplexF64[exp(im*(phi+chi))*cos(eta), exp(im*(phi-chi))*sin(eta)]
    psi = psi / norm(psi)
    n = [real(psi' * (P * psi)) for P in (SX, SY, SZ)]
    nn = norm(n); nhat = nn < 1e-12 ? [0.0,0.0,1.0] : n ./ nn
    return nhat[1]*SX + nhat[2]*SY + nhat[3]*SZ
end

# =====================================================================================
# GENUINE SUBSTRATE FRAMES U_A in SU(2) (built from genuine geometry, NOT invented).
# A normalized 2-spinor (z1,z2) on S^3 in C^2 fixes an SU(2) element
#       U = [ z1  -conj(z2) ; z2  conj(z1) ]   (det = |z1|^2 + |z2|^2 = 1).
# =====================================================================================
function su2_frame(z1::ComplexF64, z2::ComplexF64)
    n = sqrt(abs2(z1) + abs2(z2)); z1 /= n; z2 /= n
    ComplexF64[z1 (-conj(z2)); z2 conj(z1)]
end

# HOPF frame: the Hopf representative spinor fiber_rep(theta,phi) (G_hopf_fibration.jl).
hopf_spinor(theta, phi) = (ComplexF64(cos(theta/2)), ComplexF64(sin(theta/2)*exp(im*phi)))
hopf_frame(theta, phi)  = su2_frame(hopf_spinor(theta, phi)...)

# NESTED-TORI leaf frame: the nested-Hopf-tori leaf spinor (cos th e^{ia}, sin th e^{ib})
# from G_nested_hopf_tori.jl S3pt foliation (theta in (0,pi/2): a genuine 2-torus leaf).
leaf_spinor(theta, a, b) = (ComplexF64(cos(theta)*exp(im*a)), ComplexF64(sin(theta)*exp(im*b)))
leaf_frame(theta, a, b)  = su2_frame(leaf_spinor(theta, a, b)...)

# CLIFFORD rotor: exp(-i ang/2 n.sigma) — SU(2) ~ even subalgebra of Cl(3,0); the rotor
# from clifford_rotor_spinor_network_entanglement.jl (Pauli generators σ1,σ2,σ3).
function clifford_rotor(ang::Float64, n::Vector{Float64})
    nh = n / norm(n); B = nh[1]*SX + nh[2]*SY + nh[3]*SZ
    exp(-im * ang/2 * B)
end

# random Haar-ish SU(2) (NOT a geometry frame) — the SHARPER control of requirement 3.
function rand_su2(rng)
    z1 = randn(rng) + im*randn(rng); z2 = randn(rng) + im*randn(rng)
    su2_frame(ComplexF64(z1), ComplexF64(z2))
end

# =====================================================================================
# random density operators (Bloch-free: random complex spinors + convex mixtures).
# The (N_RHO+1)-th rho is the maximally-mixed state I/2 (the "+1").
# =====================================================================================
function rand_rho(rng)
    psi = ComplexF64[randn(rng)+im*randn(rng), randn(rng)+im*randn(rng)]
    psi = psi / norm(psi)
    pure = psi * psi'
    p = 0.2 + 0.6*rand(rng)
    rho = p*pure + (1-p)*(I2/2)
    return (rho + rho')/2 / real(tr((rho+rho')/2))
end
make_rhos(rng, n) = vcat([rand_rho(rng) for _ in 1:n], [Matrix{ComplexF64}(I2/2)])

# =====================================================================================
# THE DRESSED CHANNEL and the substrate-effect functional E(A).
#   Phi_B^A(rho) = U_A * Phi_B(U_A' * rho * U_A) * U_A'        (run B in frame A)
#   E(A)         = max_rho ||Phi_B^A(rho) - Phi_B(rho)||_1     (also report mean)
# =====================================================================================
dressed(PhiB, U, rho) = U * PhiB(U' * rho * U) * U'
function substrate_effect(PhiB, U, rhos)
    diffs = Float64[]
    for rho in rhos
        push!(diffs, trace_norm(dressed(PhiB, U, rho) - PhiB(rho)))
    end
    return mean(diffs), maximum(diffs)
end

# =====================================================================================
# Z3 load-bearing verdict-flip: bind the MEASURED across-substrate spread (scaled int)
# to the law "flat_or_no_geometry => spread == 0". A genuine multi-substrate spread is
# nonzero -> asserting flat=true contradicts spread==measured>0 -> UNSAT. The flat
# control (all U_A = I) gives spread 0 -> SAT. The verdict FLIPS on the flat input; the
# measured number (not a literal) decides it. Same construction as order_null_killtest.
# =====================================================================================
function z3_substrate_obstruction(measured_spread::Float64; scale=1_000_000_000)
    ctx = Z3.Context(); s = Z3.Solver(ctx)
    spread  = Z3.IntVar("spread", ctx)
    is_flat = Z3.BoolVar("is_flat", ctx)
    Z3.add(s, Z3.Or([Z3.Not(is_flat), spread == Z3.IntVal(0, ctx)]))  # flat => spread==0
    Z3.add(s, is_flat == Z3.BoolVal(true, ctx))
    m = round(Int, scale * abs(measured_spread))
    Z3.add(s, spread == Z3.IntVal(m, ctx))
    return string(Z3.check(s))   # genuine(nonzero): unsat ; flat(zero): sat
end

# =====================================================================================
# RUN
# =====================================================================================
function run()
    rng  = MersenneTwister(SEED)
    rhos = make_rhos(rng, N_RHO)

    R = Dict{String,Any}()
    R["object_id"]         = "substrate_effect_frame_conjugation"
    R["sim_id"]            = "substrate_effect_frame_conjugation"
    R["name"]              = "Geometric substrate-effect via frame conjugation (density-operator only)"
    R["version"]           = "1.0"
    R["classification"]    = "substrate_effect_frame_conjugation_poc"
    R["promotion_allowed"] = false
    R["sim_execution_kind"]= "nonclassical_poc"
    R["sim_class"]         = "geometry_probe"
    R["script"]            = "substrate_effect_frame_conjugation.jl"
    R["seed"]              = SEED
    R["n_rho"]             = N_RHO + 1
    R["non_numpy"]         = true
    R["bloch_free"]        = true
    R["carrier_layer"]     = "density operators rho in D(C^2); substrate frames U_A in SU(2) from genuine geometry; upper Weyl operations from L7/L10/L11 _bf channels. NO CTMRG, NO PEPS, NO optimization."
    R["geometry_layer"]    = "Hopf frame (G_hopf_fibration), nested-Hopf-tori leaf frame (G_nested_hopf_tori), Clifford rotor (clifford_rotor_spinor_network_entanglement)"
    R["finite_map"]        = "(substrate A -> U_A in SU(2)) |-> dressed channel Phi_B^A(rho)=U_A Phi_B(U_A' rho U_A) U_A'; substrate effect E(A)=max_rho ||Phi_B^A(rho)-Phi_B(rho)||_1"
    R["domain"]            = "finite set of $(N_RHO+1) density operators; finite substrate frame set {Hopf, nested-tori, Clifford, random-su2, flat=I}; upper Weyl ops {Te-dephasing, WeylL-GKSL, Fi-unitary}"
    R["codomain_or_output"]= "finite table of substrate effects E(A) (mean,max) per (upper-op, substrate), substrate spread, random-vs-geometry distinguishability, nesting ordering, Z3 verdict-flip"
    R["spinor_state"]      = "SU(2) frames built from genuine 2-spinors on S^3 (Hopf fiber_rep, nested-tori leaf spinor); upper GKSL state from Hopf-site Hamiltonian H0"
    R["quaternion_action"] = "SU(2)~unit quaternions: each U_A is a unit quaternion frame; nesting U_A*U_A' is quaternion product (control checks it is not a trivial single rotation)"
    R["dependency_receipts"] = [
        "layers/order_null_killtest.jl (genuine Weyl GKSL + Phi_Te + hopf_h0 + PTM/noise-floor/Z3 discipline)",
        "layers/G_hopf_fibration.jl (Hopf representative spinor fiber_rep)",
        "layers/G_nested_hopf_tori.jl (nested-tori leaf spinor / foliation)",
        "layers/clifford_rotor_spinor_network_entanglement.jl (Clifford rotor SU(2))",
        "layers/L7_layer_bf.jl (per-sheet Weyl GKSL channel)",
    ]
    R["claim_ceiling"] = "MEASURES the operational difference E(A) between a bare and a substrate-dressed Weyl operation on a finite density-operator carrier, against four anti-tautology requirements and a random-unitary control. Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics. A real structured effect here is a CANDIDATE geometric interface, NOT a proven nesting layer."

    # ----- fixed genuine parameters -----
    q_deph  = 0.65                              # L11_bf dephasing strength
    ang     = 0.9                               # L11_bf rotation angle / Clifford rotor angle
    phi0, chi0, eta0 = 2pi*0.21, 2pi*0.13, pi/4
    H0      = hopf_h0(phi0, chi0, eta0)         # Hopf-site Hamiltonian for the Weyl GKSL

    # ----- upper operations B (genuine) -----
    PhiTe   = rho -> Phi_Te(rho, q_deph)                  # dephasing (non-unitary)
    PhiWeyl = rho -> gksl_step_evolve(rho, +H0, SM)       # Weyl-L GKSL (non-unitary)
    PhiFi   = rho -> Phi_Fi(rho, ang)                     # x-rotation (UNITARY — trap exposer)
    upper_ops = [
        ("Te_dephasing", PhiTe,   :nonunitary),
        ("WeylL_GKSL",   PhiWeyl, :nonunitary),
        ("Fi_unitary",   PhiFi,   :unitary),     # exposes the just-noncommutation mode
    ]

    # ----- substrate frames U_A (genuine geometry) at fixed genuine sites -----
    U_hopf  = hopf_frame(pi/3, 0.7)                                  # Hopf fiber over (theta,phi)
    U_leaf  = leaf_frame(pi/4, 0.6, 1.9)                             # nested-tori Clifford-torus leaf
    U_cliff = clifford_rotor(ang, [0.2, 0.7, 0.5])                   # Clifford rotor
    U_flat  = Matrix{ComplexF64}(I2)                                 # FLAT control (no geometry)
    geometry_substrates = [
        ("Hopf_frame",     U_hopf),
        ("NestedTori_leaf",U_leaf),
        ("Clifford_rotor", U_cliff),
    ]

    # nested substrate (tori nested in tori): U = U_A * U_A' with a SECOND genuine leaf
    U_leaf2 = leaf_frame(0.95, 2.1, 0.4)                            # outer leaf (different latitude)
    U_nested = U_leaf * U_leaf2                                     # nested-Hopf-tori frame
    U_hopf2  = hopf_frame(0.9, 2.1)
    U_nested_hopf = U_hopf * U_hopf2                                # nested Hopf frame

    # =====================================================================
    # EXPLICIT NOISE FLOOR (trace-norm scale * machine eps * conjugation depth).
    # A single dressing is U .. U' (two conjugations) on a trace-1 operator; the trace
    # norm of a density operator is 1, and the dressed/bare difference accumulates
    # O(few) * eps rounding. Floor = eps * trace-scale(=1) * depth(4) * 16 safety.
    # =====================================================================
    noise_floor = eps(Float64) * 1.0 * 4.0 * 16.0
    R["noise_floor"] = Dict(
        "value" => noise_floor,
        "definition" => "eps(Float64) * trace_scale(1) * conjugation_depth(4) * 16 safety",
        "machine_eps" => eps(Float64),
    )

    # =====================================================================
    # MAIN TABLE: E(A) per (upper-op, substrate) + flat + random-su2 ensemble.
    # =====================================================================
    per_op = Vector{Dict{String,Any}}()
    overall_op_verdicts = String[]

    for (opname, PhiB, kind) in upper_ops
        rows = Dict{String,Any}()

        # (1) POSITIVE + (2) SUBSTRATE-DEPENDENT: E over genuine geometry substrates
        geo_effects = Dict{String,Any}()
        geo_max_vals = Float64[]
        for (sname, U) in geometry_substrates
            m, mx = substrate_effect(PhiB, U, rhos)
            geo_effects[sname] = Dict("E_mean" => m, "E_max" => mx, "above_floor" => mx > noise_floor)
            push!(geo_max_vals, mx)
        end
        positive_ok = all(v > noise_floor for v in geo_max_vals)
        # substrate spread = max - min of E_max across genuine geometry substrates
        substrate_spread = maximum(geo_max_vals) - minimum(geo_max_vals)
        substrate_dependent = substrate_spread > 1e-3   # genuinely different, not a constant

        # (3) FLAT kill-control: U_A = I MUST give E ~ 0
        flat_m, flat_mx = substrate_effect(PhiB, U_flat, rhos)
        flat_collapses = flat_mx < noise_floor

        # (3-sharper) RANDOM-UNITARY controls, in TWO forms:
        #   (a) raw band: 40 unconstrained random SU(2) frames (the loose control).
        #   (b) COMMUTATOR-MATCHED paired control (the decisive discriminator): the bare-vs-
        #       dressed gap is driven by the non-commutation between the frame U and the upper
        #       op. For a UNITARY upper op V the commutator norm c = ||[U, V]||_HS is the
        #       SOLE non-commutation magnitude. If geometry is NOT load-bearing, then a random
        #       frame with the SAME c gives the SAME E (E is a function of c alone). If geometry
        #       IS load-bearing, the geometry frame's E differs from random frames matched on c.
        #   We measure, per geometry frame, the commutator norm c_geo, find random frames with
        #   c within +/-5% of c_geo, and compare E(geometry) to E(commutator-matched random).
        #   geometry_distinguishable iff |E_geo - mean E_matched_random| exceeds the matched-
        #   random spread (the geometry sits OUTSIDE the band of equally-non-commuting frames).
        Vop = opname == "Te_dephasing" ? (Qp - Qm) :            # dephasing "axis" generator proxy
              opname == "WeylL_GKSL"   ? H0 :                    # GKSL Hamiltonian part
              Ux(ang)                                            # unitary V
        comm_norm(U) = hs(U*Vop - Vop*U)
        # LARGE ensemble (2000) — a 40-400 frame ensemble gives FALSE 'outside' verdicts at
        # the commutator-norm TAILS where few random frames land (a small-sample artifact a
        # knob-sweep exposed). 2000 frames populate the tails enough to match honestly.
        rng_r = MersenneTwister(SEED + 777)
        rand_frames = [rand_su2(rng_r) for _ in 1:2000]
        rand_c   = [comm_norm(U) for U in rand_frames]
        rand_E   = [substrate_effect(PhiB, U, rhos)[2] for U in rand_frames]
        rand_lo, rand_hi = minimum(rand_E), maximum(rand_E)
        rand_mean = mean(rand_E); rand_std = std(rand_E)

        # paired commutator-matched discriminator, per geometry frame. 'outside' must be
        # KNOB-ROBUST: it must hold across matching tolerances {2%,5%,10%} (else it is a
        # knife-edge of the tolerance, not a structural geometry signature).
        matched_rows = Dict{String,Any}()
        geom_outside_matched = Bool[]
        for (sname, U) in geometry_substrates
            cg = comm_norm(U)
            Eg = substrate_effect(PhiB, U, rhos)[2]
            tol_results = Dict{String,Any}(); robust_flags = Bool[]
            ref_mean = NaN; ref_std = NaN; ref_n = 0
            for tolfrac in (0.02, 0.05, 0.10)
                tol = tolfrac * max(cg, 1e-9)
                idx = [k for k in 1:length(rand_frames) if abs(rand_c[k] - cg) <= tol]
                if length(idx) >= 8
                    Em = [rand_E[k] for k in idx]; em_mean = mean(Em); em_std = std(Em)
                    out = abs(Eg - em_mean) > (em_std + 1e-6) && abs(Eg - em_mean) > 0.05
                    tol_results["tol_$(tolfrac)"] = Dict("n"=>length(idx), "E_matched_mean"=>em_mean,
                        "E_matched_std"=>em_std, "abs_gap"=>abs(Eg-em_mean), "outside"=>out)
                    push!(robust_flags, out)
                    tolfrac == 0.05 && (ref_mean = em_mean; ref_std = em_std; ref_n = length(idx))
                else
                    tol_results["tol_$(tolfrac)"] = Dict("n"=>length(idx), "outside"=>false,
                        "note"=>"too few matched (<8)")
                    push!(robust_flags, false)
                end
            end
            # KNOB-ROBUST 'outside' iff outside holds at ALL THREE tolerances
            outside_robust = all(robust_flags) && length(robust_flags) == 3
            matched_rows[sname] = Dict("c_geo"=>cg, "E_geo"=>Eg,
                "E_matched_mean"=>ref_mean, "E_matched_std"=>ref_std, "n_matched"=>ref_n,
                "per_tolerance"=>tol_results,
                "geom_outside_matched_band"=>outside_robust,
                "outside_at_each_tolerance"=>robust_flags)
            push!(geom_outside_matched, outside_robust)
        end
        # DECISIVE: geometry is load-bearing (distinguishable) iff ANY geometry frame's E
        # lands KNOB-ROBUSTLY OUTSIDE the effect-band of random frames with the SAME
        # commutator norm — i.e. it carries structure BEYOND non-commutation, stable across
        # the matching tolerance.
        geometry_distinguishable = any(geom_outside_matched)
        geo_in_rand_band = all(rand_lo - 1e-9 <= v <= rand_hi + 1e-9 for v in geo_max_vals)

        # (4) NESTING COMPOUNDS: nested frame vs single + flat ordering, and non-triviality
        nest_use = opname == "Fi_unitary" ? (U_nested_hopf, U_hopf) : (U_nested, U_leaf)   # geometry-matched
        U_nest, U_single = nest_use
        _, nest_mx   = substrate_effect(PhiB, U_nest, rhos)
        _, single_mx = substrate_effect(PhiB, U_single, rhos)
        # non-trivial nesting: the nested product is NOT itself a single geometry frame
        # already in the set (check the frame is a genuinely different SU(2) element).
        nest_vs_single_frame = minimum([norm(U_nest - U), norm(U_nest + U)] |> minimum
                                        for (_, U) in geometry_substrates)
        nesting_nontrivial_frame = nest_vs_single_frame > 1e-6
        # ordering: flat < single  vs  nested distinct from single
        ordering = Dict(
            "E_flat_max"   => flat_mx,
            "E_single_max" => single_mx,
            "E_nested_max" => nest_mx,
            "flat_lt_single" => flat_mx < single_mx,
            "nested_distinct_from_single" => abs(nest_mx - single_mx) > 1e-3,
            "nested_distinct_from_flat"   => abs(nest_mx - flat_mx) > 1e-3,
        )
        nesting_compounds = (flat_mx < single_mx) &&
                            (abs(nest_mx - single_mx) > 1e-3) &&
                            nesting_nontrivial_frame

        rows["upper_op"]              = opname
        rows["upper_op_kind"]         = string(kind)
        rows["geometry_effects"]      = geo_effects
        rows["positive_all_above_floor"] = positive_ok
        rows["substrate_spread"]      = substrate_spread
        rows["substrate_dependent"]   = substrate_dependent
        rows["flat_control"]          = Dict("E_mean"=>flat_m, "E_max"=>flat_mx, "collapses_to_floor"=>flat_collapses)
        rows["random_unitary_control"]= Dict(
            "n_random" => length(rand_frames), "E_max_mean" => rand_mean, "E_max_std" => rand_std,
            "E_max_lo" => rand_lo, "E_max_hi" => rand_hi,
            "geometry_inside_raw_random_band" => geo_in_rand_band,
            "commutator_matched_discriminator" => matched_rows,
            "geometry_distinguishable_from_random" => geometry_distinguishable,
            "discriminator" => "PAIRED: per geometry frame, compare E(geometry) to E of random SU(2) frames matched (+/-5%) on the commutator norm ||[U,V]||. geometry_distinguishable iff E(geometry) lands OUTSIDE the matched-random effect band -> geometry carries structure BEYOND non-commutation. Otherwise E is a function of the commutator norm alone => 'just non-commutation', geometry NOT load-bearing.",
        )
        rows["nesting"]               = Dict(
            "ordering" => ordering,
            "nested_frame_nontrivial" => nesting_nontrivial_frame,
            "nested_frame_min_dist_to_single_geom" => nest_vs_single_frame,
            "nesting_compounds" => nesting_compounds,
        )

        # how many of the 3 genuine geometry frames cleared the knob-robust discriminator
        n_geom_distinguishable = count(geom_outside_matched)
        rows["n_geometry_frames_distinguishable"] = n_geom_distinguishable
        rows["n_geometry_frames_total"] = length(geometry_substrates)

        # PER-OP VERDICT (brutally honest: only ALL geometry frames distinguishable earns
        # real_and_nests; a SINGLE frame clearing is a frame-specific CANDIDATE signal, not
        # a clean geometric-substrate effect across the geometry family).
        op_verdict = if !positive_ok
            "substrate_effect_trivial_or_needs_geometric_carrier"
        elseif n_geom_distinguishable == 0
            "substrate_effect_is_just_noncommutation"
        elseif n_geom_distinguishable == length(geometry_substrates) &&
               substrate_dependent && flat_collapses && nesting_compounds
            "substrate_effect_real_and_nests"
        else
            # 1..(k-1) of k frames clear: a frame-specific, dissipation-gated candidate signal
            "substrate_effect_partial_frame_specific_candidate"
        end
        rows["verdict"] = op_verdict
        push!(overall_op_verdicts, op_verdict)
        push!(per_op, rows)
    end
    R["per_upper_op"] = per_op

    # =====================================================================
    # Z3 load-bearing verdict-flip on the across-substrate spread of the
    # FIRST NON-UNITARY upper op (Te_dephasing): genuine spread UNSAT, flat-zero SAT.
    # =====================================================================
    te_row = per_op[1]
    genuine_spread = te_row["substrate_spread"]
    z3_genuine = z3_substrate_obstruction(genuine_spread)   # nonzero -> unsat
    z3_flat    = z3_substrate_obstruction(0.0)              # zero    -> sat
    z3_load_bearing = (z3_genuine == "unsat") && (z3_flat == "sat") && (genuine_spread > 1e-3)
    R["z3_load_bearing"] = Dict(
        "encoding" => "FREE int spread, FREE bool is_flat; law Or([Not(is_flat), spread==0]); assert is_flat=true + spread==IntVal(measured). genuine multi-substrate spread: unsat; flat zero spread: sat.",
        "upper_op" => "Te_dephasing",
        "genuine_substrate_spread" => genuine_spread,
        "genuine_verdict" => z3_genuine,
        "flat_spread" => 0.0,
        "flat_verdict" => z3_flat,
        "load_bearing_flip" => z3_load_bearing,
    )

    # =====================================================================
    # SEED-ROBUST check: re-measure the Te_dephasing Hopf-frame effect over a fresh rho
    # ensemble (different seed). The effect must persist (not a single-seed artifact).
    # =====================================================================
    seed_effects = Float64[]
    for sd in (SEED+1, SEED+2, SEED+3)
        r2 = make_rhos(MersenneTwister(sd), N_RHO)
        _, mx = substrate_effect(PhiTe, U_hopf, r2)
        push!(seed_effects, mx)
    end
    seed_robust = all(v > noise_floor for v in seed_effects) &&
                  (std(seed_effects) / max(mean(seed_effects), 1e-12) < 0.5)
    R["seed_robust"] = Dict(
        "seeds" => [SEED+1, SEED+2, SEED+3],
        "Te_hopf_E_max" => seed_effects,
        "all_above_floor" => all(v > noise_floor for v in seed_effects),
        "relative_std" => std(seed_effects) / max(mean(seed_effects), 1e-12),
        "robust" => seed_robust,
    )

    # =====================================================================
    # OVERALL VERDICT (across the genuine NON-UNITARY upper ops; the unitary op is the
    # control that EXPOSES the just-noncommutation mode and is reported but excluded from
    # the headline because for a unitary B the effect is by-construction just ||[U,V]||).
    # =====================================================================
    nonunitary_verdicts = [per_op[i]["verdict"] for i in 1:length(per_op)
                           if per_op[i]["upper_op_kind"] == "nonunitary"]
    unitary_verdict = [per_op[i]["verdict"] for i in 1:length(per_op)
                       if per_op[i]["upper_op_kind"] == "unitary"]

    overall = if all(v == "substrate_effect_real_and_nests" for v in nonunitary_verdicts)
        "substrate_effect_real_and_nests"
    elseif any(v == "substrate_effect_real_and_nests" for v in nonunitary_verdicts)
        "mixed_some_real_some_not"
    elseif any(v == "substrate_effect_partial_frame_specific_candidate" for v in nonunitary_verdicts)
        # the honest middle: a single geometry frame at a dissipative op carries structure
        # beyond non-commutation, but it is NOT clean across the geometry family.
        "substrate_effect_partial_frame_and_dissipation_specific"
    elseif all(v == "substrate_effect_is_just_noncommutation" for v in nonunitary_verdicts)
        "substrate_effect_is_just_noncommutation"
    else
        "substrate_effect_trivial_or_needs_geometric_carrier"
    end

    R["verdict"] = Dict(
        "overall" => overall,
        "nonunitary_upper_op_verdicts" => nonunitary_verdicts,
        "unitary_control_verdict" => unitary_verdict,
        "z3_load_bearing" => z3_load_bearing,
        "seed_robust" => seed_robust,
        "interpretation" => "substrate_effect_real_and_nests requires (per non-unitary Weyl op) all four anti-tautology requirements AND ALL THREE geometry frames knob-robustly distinguishable from commutator-matched random unitaries. substrate_effect_partial_frame_and_dissipation_specific means 1..(k-1) of k geometry frames clear the commutator-matched discriminator: a single geometry frame at a DISSIPATIVE (GKSL) upper op carries structure beyond non-commutation, but it is NOT clean across the geometry family — a frame-specific, dissipation-gated CANDIDATE signal, not a proven geometric-substrate effect. substrate_effect_is_just_noncommutation means geometry frames are indistinguishable from commutator-matched random SU(2) conjugation (the unitary upper op confirms the trap: E(A)=||[U_A,V]|| by construction). substrate_effect_trivial_or_needs_geometric_carrier means the finite 2-dim frame does not carry the structure — the real geometric PEPS carrier is required (Path B forced).",
        "decides" => "whether the owner's geometric substrate-nesting claim is finitely-validatable on a density-operator carrier or genuinely PEPS-bound.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^2); finite SU(2) frame set {Hopf, nested-tori, Clifford, random, flat}",
        "finite_probe"   => "$(N_RHO+1) density operators (20 spinor-derived + 1 maximally-mixed)",
        "finite_operator"=> "genuine upper Weyl ops {Te-dephasing, WeylL-GKSL, Fi-unitary}; substrate frames from genuine geometry",
        "finite_path"    => "dressed compositions U_A Phi_B(U_A' . U_A) U_A' and nested U_A U_A'",
    )
    R["N01_witness"] = Dict(
        "order_sensitive_control" => "frame conjugation does not commute with the upper op in general; [U_A, V] != 0 drives the dressed-vs-bare gap. The substrate axis is the geometric (non-temporal) control; the temporal-order spine is validated separately in order_null_killtest.jl.",
        "genuine_substrate_spread" => genuine_spread,
        "present_above_floor" => genuine_spread > 1e-3,
        "noise_floor" => noise_floor,
    )

    R["required_negatives"] = ["flat_substrate_U_eq_I", "random_su2_non_geometry_frame", "unitary_upper_op_trap_exposer"]
    R["negatives_run"]      = ["flat_substrate_U_eq_I", "random_su2_non_geometry_frame", "unitary_upper_op_trap_exposer"]
    R["kill_conditions"]    = ["flat must collapse E to floor", "random unitary indistinguishable from geometry => not geometry, just non-commutation", "nested frame trivial (== a single existing frame) => nesting not real"]

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS norms, matrix exp (Clifford rotor / GKSL), all SU(2) frame and channel algebra; every measured number flows through it.",
        "Statistics"    => "load_bearing: mean/std over the rho ensemble and the random-unitary control band (the distinguishability test depends on these).",
        "Random"        => "load_bearing: random density operators AND the random-su2 control band (the sharper requirement-3 control is measured, not planted).",
        "Z3"            => "load_bearing: binds the measured across-substrate spread to the flat=>spread==0 law; verdict flips UNSAT->SAT on the flat control.",
        "JSON"          => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"load_bearing","JSON"=>"supportive")
    R["downstream_blocks"] = ["layer-completion","manifold admission","pairwise nesting promotion","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics","final_manifold_admission"]
    R["blocked_consumers"] = R["downstream_blocks"]
    R["root_constraints_in_force"] = [
        "F01 finite density-operator carrier / SU(2) frame set / Weyl ops / dressed paths",
        "N01 frame conjugation [U_A, V] != 0 order-sensitive control (geometric substrate axis)",
    ]
    R["status_ladder"] = "exists < runs < passes local rerun"
    R["promotion_status"] = "diagnostic_only"

    open(RESULT_PATH, "w") do io
        JSON.print(io, R, 2); write(io, "\n")
    end

    # ---- console summary ----
    println("="^90)
    println("SUBSTRATE-EFFECT FRAME-CONJUGATION  (object_id=substrate_effect_frame_conjugation)")
    println("  classification=substrate_effect_frame_conjugation_poc  promotion_allowed=false")
    println("="^90)
    println("noise_floor = ", noise_floor)
    for row in per_op
        println("-"^90)
        println("UPPER OP: ", row["upper_op"], "  (", row["upper_op_kind"], ")")
        for (sname, U) in geometry_substrates
            ge = row["geometry_effects"][sname]
            println("   E(", rpad(sname,16), ") mean=", rpad(string(round(ge["E_mean"],sigdigits=4)),12),
                    " max=", rpad(string(round(ge["E_max"],sigdigits=4)),12), " above_floor=", ge["above_floor"])
        end
        fc = row["flat_control"]
        rc = row["random_unitary_control"]
        println("   FLAT control       E_max=", round(fc["E_max"],sigdigits=4), "  collapses=", fc["collapses_to_floor"])
        println("   RANDOM-su2 band    E_max in [", round(rc["E_max_lo"],sigdigits=4), ", ", round(rc["E_max_hi"],sigdigits=4),
                "] (", rc["n_random"], " frames)")
        for (sname, _) in geometry_substrates
            mr = rc["commutator_matched_discriminator"][sname]
            emm = mr["E_matched_mean"]; ems = mr["E_matched_std"]
            emm_s = (emm isa Number && !isnan(emm)) ? string(round(emm,sigdigits=4)) : "NA"
            ems_s = (ems isa Number && !isnan(ems)) ? string(round(ems,sigdigits=3)) : "NA"
            println("     paired[", rpad(sname,16), "] c=", rpad(string(round(mr["c_geo"],sigdigits=4)),10),
                    " E_geo=", rpad(string(round(mr["E_geo"],sigdigits=4)),10),
                    " E_matched=", rpad(emm_s,10), "+/-", rpad(ems_s,9),
                    " outside_robust=", mr["geom_outside_matched_band"],
                    " (at tols=", mr["outside_at_each_tolerance"], ")")
        end
        println("   substrate_spread=", round(row["substrate_spread"],sigdigits=4),
                "  substrate_dependent=", row["substrate_dependent"],
                "  geometry_distinguishable_from_random=", rc["geometry_distinguishable_from_random"])
        ns = row["nesting"]; od = ns["ordering"]
        println("   NESTING: flat=", round(od["E_flat_max"],sigdigits=4),
                " < single=", round(od["E_single_max"],sigdigits=4),
                "  nested=", round(od["E_nested_max"],sigdigits=4),
                "  nontrivial_frame=", ns["nested_frame_nontrivial"],
                "  compounds=", ns["nesting_compounds"])
        println("   >> PER-OP VERDICT: ", row["verdict"])
    end
    println("-"^90)
    println("Z3 load-bearing: genuine=", z3_genuine, " flat=", z3_flat, " flip=", z3_load_bearing)
    println("Seed-robust (Te/Hopf over 3 seeds): ", seed_robust, "  E_max=", round.(seed_effects,sigdigits=4))
    println("-"^90)
    println("OVERALL VERDICT: ", overall)
    println("  non-unitary upper-op verdicts: ", nonunitary_verdicts)
    println("  unitary control verdict:       ", unitary_verdict)
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
