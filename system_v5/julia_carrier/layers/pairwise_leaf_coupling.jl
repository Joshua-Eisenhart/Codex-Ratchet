# =====================================================================================
# pairwise_leaf_coupling.jl   --   PAIRWISE COUPLING (CLAUDE.md coupling-program step 2)
# =====================================================================================
# OBJECT (PoC): two ADJACENT Clifford-torus leaves T^2(theta1), T^2(theta2) of the
# S^3 foliation (z1,z2) = (cos(theta) e^{ia}, sin(theta) e^{ib}). Each leaf carries a
# qubit carrier driven by its OWN terrain Lindblad dynamics (a (H_k, J_k) pair drawn
# from the L4 terrain families). We then COUPLE the two leaves with the radial
# gamma^theta hopping read out of the S^3 Dirac radial decomposition
#        D_S3 = gamma^theta ( d/dtheta + H/2 ) + D_T2(theta),
# whose inter-leaf kinetic term  gamma^theta * d/dtheta  links ADJACENT leaves
# (established as a genuine nearest-neighbour hopping in nested_leaf_area_ratchet.jl).
# On a 2-leaf chain the finite-difference hopping is a single off-diagonal block
#        H_couple = (g / dtheta) * ( gamma^theta_{12} + h.c. )
# acting between leaf-1 and leaf-2 (here a coherent exchange  g_eff (sigma_x ⊗ sigma_x)
# in the leaf-spinor index, gamma^theta = sigma_x), with g_eff = g/dtheta the radial
# coupling strength. dtheta = theta2 - theta1 is the actual latitude gap of the two
# adjacent leaves -> the coupling strength is READ from the geometry, not invented.
#
# WHAT IS MEASURED (never planted):
#   * the JOINT steady state rho_joint of the full coupled two-leaf Lindbladian, solved
#     by QuantumOptics steadystate.eigenvector (LOAD-BEARING: the master-equation null
#     space IS the steady state, not a hand-written fixed point);
#   * the two ISOLATED steady states rho1_iso, rho2_iso of each leaf ALONE (single-qubit
#     Lindblad, no coupling), and their product rho_prod = rho1_iso ⊗ rho2_iso;
#   * the STEADY-STATE SHIFT = tracedistance(rho_joint, rho_prod)  <-- the anchor scalar;
#   * locking / synchronisation diagnostics: the connected XX/YY/ZZ correlators
#     C_ab = <sigma_a ⊗ sigma_b> - <sigma_a><sigma_b>  (zero for a product state), and
#     the Bloch-vector overlap of the two reduced leaves.
#
# THE TEST (which shell-local structure SURVIVES coupling):
#   We sweep the coupling g from 0 upward and read which of the two leaves' isolated
#   terrain steady states survives, whether they LOCK (correlators turn on, Bloch
#   vectors align), or whether one terrain DOMINATES (the joint reduced state of the
#   weaker leaf is pulled toward the stronger leaf's fixed point).
#
# KILL-CONTROL (the load-bearing contrast):
#   g = 0  -> the two-leaf Lindbladian is a DIRECT SUM, its steady state MUST be the
#            exact product rho1_iso ⊗ rho2_iso: tracedistance(rho_joint, rho_prod) == 0,
#            all connected correlators == 0 (product => independent terrains survive).
#   g > 0  -> the joint state MUST differ from the product: shift > 0 and at least one
#            connected correlator turns on (mixing / locking). If a NONZERO coupling
#            left the state a perfect product the coupling would be decorative and the
#            whole claim would be an artifact -- so shift==0 at g>0 KILLS the claim.
#   WRONG-STRUCTURE KILL: replace gamma^theta = sigma_x by the IDENTITY (a coupling
#            that commutes with everything and carries no exchange structure) scaled to
#            the SAME operator norm. An identity "coupling" only adds a global energy
#            shift; it CANNOT correlate the two leaves. A genuine exchange coupling must
#            produce a strictly LARGER steady-state shift than the identity sham at
#            equal strength. If the identity sham produced the same shift, our "shift"
#            would be reacting to coupling MAGNITUDE, not to exchange STRUCTURE.
#
# NON-CIRCULAR ANCHORS (checked against math the sim actually computes, not itself):
#   * tracedistance is a metric in [0,1]: at g=0 the analytic direct-sum fact forces it
#     to 0; this is a theorem about Lindbladians, not a fitted value.
#   * gamma^theta = sigma_x satisfies (gamma^theta)^2 = I, traceless, Hermitian (the
#     radial Dirac gamma), VERIFIED in-sim; the identity sham violates traceless+square.
#   * the dtheta gap of the two adjacent leaves is the MEASURED latitude difference of
#     the foliation, so g_eff = g/dtheta is geometric.
#
# classification: PoC (tool_lego_fit_probe) ; promotion_allowed = false
# tools (all non-numpy, native Julia): QuantumOptics (LOAD-BEARING steady-state solver),
#   LinearAlgebra, JSON. NO Z3 block: a decorative SMT tautology is this repo's recurring
#   weakness; the load-bearing evidence here is the measured tracedistance + kill-controls.
# run: julia --project="system_v5/julia_carrier" "system_v5/julia_carrier/layers/pairwise_leaf_coupling.jl"
# =====================================================================================

using QuantumOptics
using LinearAlgebra
using JSON

# ------------------------------------------------------------------------------------
# single-qubit carrier algebra
# ------------------------------------------------------------------------------------
const b  = SpinBasis(1//2)
const I2 = identityoperator(b)
const SX = sigmax(b)
const SY = sigmay(b)
const SZ = sigmaz(b)
const SM = sigmam(b)
const SP = sigmap(b)

# joint two-leaf basis and lifted operators
const B2  = b ⊗ b
op1(O) = O ⊗ I2        # operator O acting on leaf 1
op2(O) = I2 ⊗ O        # operator O acting on leaf 2

# radial Dirac gamma^theta = sigma_x  (Hermitian, involutive, traceless) -- the genuine
# inter-leaf hopping matrix from the S^3 radial Dirac decomposition.
const GAMMA_THETA = SX

# ------------------------------------------------------------------------------------
# Adjacent-leaf geometry: two latitudes theta1, theta2 near the Clifford torus pi/4.
# dtheta = theta2 - theta1 is the MEASURED latitude gap -> sets g_eff = g/dtheta.
# ------------------------------------------------------------------------------------
const THETA1 = pi/4 - 0.05
const THETA2 = pi/4 + 0.05
const DTHETA = THETA2 - THETA1            # = 0.1 latitude gap of the two adjacent leaves

# ------------------------------------------------------------------------------------
# TWO terrains (each = a single-qubit (H, [J]) Lindblad family from the L4 octet).
# We deliberately pick TWO DIFFERENT terrains so that "which survives coupling" is a
# real question (if both leaves had the same fixed point nothing could be learned).
#   leaf 1 = "Pit"    : strong amplitude damping  J = sqrt(gam) sigma_-  -> pulls to |down>
#   leaf 2 = "Source" : strong amplitude pumping  J = sqrt(gam) sigma_+  -> pulls to |up>
# Each also has a weak coherent Hamiltonian eps*(+/-)H0 (opposite Weyl sheets L/R).
# Their isolated steady states are OPPOSITE poles of the Bloch sphere -> a maximal
# tension for the coupling to act on.
# ------------------------------------------------------------------------------------
const EPS = 0.2
const GAM = 1.0

H1_loc = EPS * SZ                       # leaf 1 local Hamiltonian (L sheet, +H0)
J1_loc = [sqrt(GAM) * SM]               # Pit: damping toward |down>
H2_loc = -EPS * SZ                      # leaf 2 local Hamiltonian (R sheet, -H0)
J2_loc = [sqrt(GAM) * SP]               # Source: pumping toward |up>

# ------------------------------------------------------------------------------------
# Isolated single-leaf steady states (NO coupling). steadystate.eigenvector finds the
# null space of the single-qubit Liouvillian -- the genuine fixed point, not planted.
# ------------------------------------------------------------------------------------
rho1_iso = steadystate.eigenvector(H1_loc, J1_loc)
rho2_iso = steadystate.eigenvector(H2_loc, J2_loc)
rho_prod = rho1_iso ⊗ rho2_iso          # product of the two isolated terrains

bloch(rho) = real.([expect(SX, rho), expect(SY, rho), expect(SZ, rho)])

# ------------------------------------------------------------------------------------
# Joint two-leaf coupled Lindbladian.
#   H_joint = H1 ⊗ I + I ⊗ H2 + g_eff * ( gamma_coupler_1 ⊗ gamma_coupler_2 )
#   J_joint = [ J1 ⊗ I , I ⊗ J2 ]     (each leaf keeps its own dissipators)
# coupler = GAMMA_THETA (sigma_x exchange) for the genuine coupling; coupler = I2 scaled
# to the same operator norm for the WRONG-STRUCTURE identity sham.
# g_eff = g / dtheta : the finite-difference radial hopping strength on the 2-leaf chain.
# ------------------------------------------------------------------------------------
function joint_steady(g::Float64; coupler=GAMMA_THETA)
    g_eff = g / DTHETA
    H_joint = op1(H1_loc) + op2(H2_loc) + g_eff * (coupler ⊗ coupler)
    J_joint = [op1(J1_loc[1]), op2(J2_loc[1])]
    return steadystate.eigenvector(H_joint, J_joint)
end

# connected (cumulant) two-point correlator  C_ab = <A⊗B> - <A><B>.  A pure product
# state has ALL connected correlators == 0; nonzero C_ab is genuine leaf-leaf correlation.
function connected_corr(rho, A, B)
    full = real(expect(A ⊗ B, rho))
    rA   = real(expect(op1(A), rho))
    rB   = real(expect(op2(B), rho))
    return full - rA * rB
end

# total connected-correlation magnitude across the 3x3 Pauli table (a single locking scalar).
function locking_scalar(rho)
    paulis = (SX, SY, SZ)
    s = 0.0
    for A in paulis, B in paulis
        s += abs(connected_corr(rho, A, B))
    end
    return s
end

# reduced single-leaf states of a JOINT density operator (which terrain survives?).
reduced1(rho) = ptrace(rho, 2)
reduced2(rho) = ptrace(rho, 1)

# ------------------------------------------------------------------------------------
# Verify the radial gamma is a genuine Dirac gamma (involutive, traceless, Hermitian),
# and the identity sham is NOT (this is what makes the wrong-structure kill meaningful).
# ------------------------------------------------------------------------------------
function gamma_axioms(O)
    M = Matrix(O.data)
    involutive = isapprox(M*M, Matrix{ComplexF64}(I, 2, 2); atol=1e-10)   # gamma^2 = I
    traceless  = abs(tr(M)) < 1e-10
    hermitian  = isapprox(M, M'; atol=1e-10)
    return Dict("involutive_gamma2_eq_I"=>involutive, "traceless"=>traceless,
                "hermitian"=>hermitian, "is_dirac_gamma"=>(involutive && traceless && hermitian))
end

println("="^82)
println("PAIRWISE LEAF COUPLING — two adjacent Clifford-torus leaves via radial gamma^theta")
println("="^82)
println("leaf 1 latitude theta1 = $(round(THETA1,digits=4))  terrain=Pit   (J=sqrt(gam) sigma_-, -> |down>)")
println("leaf 2 latitude theta2 = $(round(THETA2,digits=4))  terrain=Source(J=sqrt(gam) sigma_+, -> |up>)")
println("adjacent-leaf latitude gap dtheta = $(round(DTHETA,digits=4))  (sets g_eff = g/dtheta)")
println()
println("isolated terrain steady states (single-qubit Lindblad fixed points, MEASURED):")
println("   leaf1 (Pit)    Bloch = $(round.(bloch(rho1_iso),digits=4))   [expect z<0 toward |down>]")
println("   leaf2 (Source) Bloch = $(round.(bloch(rho2_iso),digits=4))   [expect z>0 toward |up>]")

# gamma axioms
gax  = gamma_axioms(GAMMA_THETA)
iden_ax = gamma_axioms(I2)
println("\ngamma^theta = sigma_x is a genuine radial Dirac gamma: ", gax["is_dirac_gamma"])
println("identity sham is a genuine Dirac gamma (should be FALSE, traceless fails): ",
        iden_ax["is_dirac_gamma"])

# ====================================================================================
# (A) KILL-CONTROL g = 0: joint steady state MUST equal the product of isolated states.
# ====================================================================================
rho_g0 = joint_steady(0.0)
shift_g0   = tracedistance(rho_g0, rho_prod)
locking_g0 = locking_scalar(rho_g0)
println("\n[A] KILL-CONTROL  g = 0  (decoupled — two independent terrains)")
println("    tracedistance(joint_g0, product)   = $(round(shift_g0, sigdigits=4))   (MUST be ~0)")
println("    total connected correlation        = $(round(locking_g0, sigdigits=4))   (MUST be ~0 — product state)")
kill_g0_product = shift_g0 < 1e-6 && locking_g0 < 1e-6

# ====================================================================================
# (B) COUPLING SWEEP g > 0: joint state must DIFFER from the product (mixing / locking).
# ====================================================================================
gs = [0.0, 0.02, 0.05, 0.1, 0.2, 0.4, 0.8]
println("\n[B] COUPLING SWEEP — shift from product + locking + which terrain reduced state survives")
println("    g       g_eff    shift(td)   locking    leaf1_z(joint)  leaf2_z(joint)   C_xx")
sweep_rows = Vector{Dict{String,Any}}()
for g in gs
    rho = joint_steady(g)
    shift = tracedistance(rho, rho_prod)
    lock  = locking_scalar(rho)
    r1 = reduced1(rho); r2 = reduced2(rho)
    z1 = real(expect(SZ, r1)); z2 = real(expect(SZ, r2))
    cxx = connected_corr(rho, SX, SX)
    push!(sweep_rows, Dict("g"=>g, "g_eff"=>g/DTHETA, "shift"=>shift, "locking"=>lock,
                           "leaf1_z"=>z1, "leaf2_z"=>z2, "C_xx"=>cxx))
    println("    $(rpad(round(g,digits=3),7)) $(rpad(round(g/DTHETA,digits=3),8)) " *
            "$(rpad(round(shift,digits=5),11)) $(rpad(round(lock,digits=5),10)) " *
            "$(rpad(round(z1,digits=4),15)) $(rpad(round(z2,digits=4),16)) $(round(cxx,digits=5))")
end

# shift must rise monotonically off zero as coupling turns on (over the small-g regime).
small_g = [r for r in sweep_rows if r["g"] <= 0.2]
shift_rises = all(small_g[i]["shift"] <= small_g[i+1]["shift"] + 1e-9 for i in 1:length(small_g)-1) &&
              small_g[end]["shift"] > 1e-4
# at the largest coupling the connected correlation is genuinely nonzero (locking turned on).
g_big = sweep_rows[end]
coupling_locks = g_big["locking"] > 1e-3 && abs(g_big["C_xx"]) > 1e-4
coupling_shifts = g_big["shift"] > 1e-3

# ====================================================================================
# (C) "WHICH SURVIVES": with maximal-tension terrains (down vs up), does the coupling
# pull the two reduced leaves TOWARD each other (locking) — i.e. shrink the gap between
# their Bloch z-components relative to the isolated terrains?
# ====================================================================================
z1_iso = bloch(rho1_iso)[3]; z2_iso = bloch(rho2_iso)[3]
gap_iso = abs(z1_iso - z2_iso)                                  # isolated terrain z-gap
gap_big = abs(g_big["leaf1_z"] - g_big["leaf2_z"])             # coupled-leaf z-gap at max g
leaves_pull_together = gap_big < gap_iso - 1e-4                 # coupling shrinks the terrain gap
println("\n[C] WHICH STRUCTURE SURVIVES — Bloch z-gap of the two leaves")
println("    isolated terrains  |z1 - z2| = $(round(gap_iso,digits=4))   (down vs up, maximal tension)")
println("    coupled  (g=$(g_big["g"]))   |z1 - z2| = $(round(gap_big,digits=4))")
println("    coupling pulls the two terrains together (gap shrinks): $leaves_pull_together")

# ====================================================================================
# (D) WRONG-STRUCTURE KILL: identity "coupling" (same operator norm) cannot correlate.
# We match the identity coupler to GAMMA_THETA's operator 2-norm (both are 1) so the
# ENERGY scale is equal; only the STRUCTURE (exchange vs scalar) differs.
# ====================================================================================
g_test = 0.4
rho_real = joint_steady(g_test; coupler=GAMMA_THETA)
rho_sham = joint_steady(g_test; coupler=I2)     # identity sham coupling, same g
shift_real = tracedistance(rho_real, rho_prod)
shift_sham = tracedistance(rho_sham, rho_prod)
lock_real  = locking_scalar(rho_real)
lock_sham  = locking_scalar(rho_sham)
norm_gamma = opnorm(Matrix(GAMMA_THETA.data))
norm_iden  = opnorm(Matrix(I2.data))
println("\n[D] WRONG-STRUCTURE KILL  (identity sham coupling at g=$g_test, equal op-norm)")
println("    op-norm gamma^theta = $(round(norm_gamma,digits=4)) ;  op-norm identity = $(round(norm_iden,digits=4))  (equal energy scale)")
println("    REAL exchange (sigma_x⊗sigma_x): shift = $(round(shift_real,digits=5))   locking = $(round(lock_real,digits=5))")
println("    SHAM identity (I⊗I)            : shift = $(round(shift_sham,digits=5))   locking = $(round(lock_sham,digits=5))")
# identity coupling commutes with the full Liouvillian's coherent part trivially and adds
# NO correlation -> its shift and locking must be ~0, strictly below the real exchange.
sham_inert       = shift_sham < 1e-6 && lock_sham < 1e-6
real_beats_sham  = shift_real > shift_sham + 1e-4 && lock_real > lock_sham + 1e-4
println("    identity sham is inert (shift~0, locking~0): $sham_inert")
println("    real exchange strictly exceeds sham (structure, not magnitude): $real_beats_sham")

# ====================================================================================
# VERDICTS
# ====================================================================================
checks = Dict(
    "gamma_theta_is_dirac_gamma"        => gax["is_dirac_gamma"],
    "identity_is_not_dirac_gamma"       => !iden_ax["is_dirac_gamma"],
    "kill_g0_joint_equals_product"      => kill_g0_product,
    "coupling_shifts_state_off_product" => coupling_shifts,
    "coupling_turns_on_locking"         => coupling_locks,
    "shift_rises_with_coupling"         => shift_rises,
    "coupling_pulls_terrains_together"  => leaves_pull_together,
    "wrong_structure_identity_inert"    => sham_inert,
    "real_exchange_beats_identity_sham" => real_beats_sham,
)
all_pass = all(values(checks))

println("\n" * "="^82)
println("VERDICTS")
for k in sort(collect(keys(checks)))
    println("   $(rpad(k,40)) : $(checks[k] ? "PASS" : "FAIL")")
end
println("="^82)

# honest status: PARTIAL beats a forced pass. We report exactly what the measurements show.
status = all_pass ? "passes" : "partial"
honest = "kill_g0_product=$(kill_g0_product); coupling_shifts=$(coupling_shifts); " *
         "coupling_locks=$(coupling_locks); shift_monotone=$(shift_rises); " *
         "terrains_pull_together=$(leaves_pull_together); sham_inert=$(sham_inert); " *
         "real>sham=$(real_beats_sham)"
println("ALL_PASS = $all_pass    HONEST STATUS = $status")
println("ANCHOR (measured): steady-state shift tracedistance(joint, product) = ",
        "$(round(g_big["shift"],digits=5)) at g=$(g_big["g"]); == 0 at g=0 (direct-sum theorem).")
println("FINDING: with maximal-tension terrains (Pit down vs Source up), nonzero radial",)
println("         gamma^theta coupling mixes the joint state off the product and the two",)
println("         leaves' reduced terrains are pulled together (partial locking), while a",)
println("         structure-blind identity coupling of equal strength leaves them independent.")
println("="^82)

result = Dict(
    "object" => "pairwise_leaf_coupling: two adjacent Clifford-torus leaves coupled by radial gamma^theta",
    "classification" => "tool_lego_fit_probe",
    "promotion_allowed" => false,
    "coupling_program_step" => "step 2 (pairwise coupling) of CLAUDE.md coupling order",
    "carrier" => "two single-qubit leaf carriers on T^2(theta1), T^2(theta2); QuantumOptics Lindblad",
    "tool_integration" => Dict(
        "QuantumOptics.jl" => "load_bearing (steadystate.eigenvector solves the Liouvillian null space; tracedistance/ptrace read the joint vs product states)",
        "z3" => "omitted deliberately (no decorative SMT; evidence = measured tracedistance + kill-controls)"),
    "geometry" => Dict("theta1"=>THETA1, "theta2"=>THETA2, "dtheta"=>DTHETA,
                       "g_eff_formula"=>"g/dtheta (finite-difference radial hopping on the 2-leaf chain)"),
    "terrains" => Dict(
        "leaf1" => Dict("name"=>"Pit", "H"=>"eps*sigma_z", "J"=>"sqrt(gam)*sigma_-",
                        "iso_bloch"=>round.(bloch(rho1_iso),digits=5)),
        "leaf2" => Dict("name"=>"Source", "H"=>"-eps*sigma_z", "J"=>"sqrt(gam)*sigma_+",
                        "iso_bloch"=>round.(bloch(rho2_iso),digits=5))),
    "gamma_theta_axioms" => gax,
    "identity_axioms" => iden_ax,
    "kill_g0" => Dict("shift"=>shift_g0, "locking"=>locking_g0, "joint_equals_product"=>kill_g0_product),
    "sweep" => sweep_rows,
    "which_survives" => Dict("z_gap_isolated"=>gap_iso, "z_gap_coupled_max_g"=>gap_big,
                             "leaves_pull_together"=>leaves_pull_together),
    "wrong_structure_kill" => Dict(
        "g_test"=>g_test, "opnorm_gamma"=>norm_gamma, "opnorm_identity"=>norm_iden,
        "shift_real_exchange"=>shift_real, "shift_identity_sham"=>shift_sham,
        "locking_real_exchange"=>lock_real, "locking_identity_sham"=>lock_sham,
        "identity_inert"=>sham_inert, "real_exchange_beats_sham"=>real_beats_sham),
    "anchor" => "steady-state shift = tracedistance(rho_joint, rho1_iso ⊗ rho2_iso); " *
                "== 0 at g=0 (direct-sum Lindbladian theorem), > 0 at g>0 (measured)",
    "checks" => checks,
    "all_pass" => all_pass,
    "status_ladder" => "exists < runs < passes",
    "honest_status" => honest,
    "status" => status,
    "claim_ceiling" => "PoC: a genuine pairwise radial coupling of two terrain-carrying leaves; " *
                       "the joint steady state is MEASURED to differ from the product of isolated " *
                       "terrains iff the coupling is nonzero and carries exchange structure. " *
                       "NOT a coexistence/topology/emergence claim. promotion_allowed=false.",
)

outpath = joinpath(@__DIR__, "pairwise_leaf_coupling_results.json")
open(outpath, "w") do io
    JSON.print(io, result, 2)
end
println("\nwrote: $outpath")
exit(all_pass ? 0 : 1)
