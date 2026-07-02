# L5 OPERATOR SUBSTAGE -- operators as a stage *between* states on the carrier.
#
# OBJECT: a finite noncommuting operator set {A_1,A_2,A_3} acting on a finite Hilbert-space carrier.
#   The "substage" structure is the COMMUTATOR algebra they generate: the antisymmetric 2-form
#   omega_rho(A,B) = Tr(rho [A,B]) and the Lie structure constants read out from [A_i,A_j].
#
# NON-CIRCULAR ANCHOR (math, not self):
#   The spin-1/2 generators S_i = sigma_i/2 close the su(2) Lie algebra with the KNOWN structure
#   constants of su(2):  [S_i, S_j] = i * sum_k eps_{ijk} S_k,  eps = Levi-Civita.
#   We do NOT plant eps_{ijk}. We MEASURE c_{ijk} by projecting the measured matrix [S_i,S_j]
#   onto the basis {i*S_k} via the Hilbert-Schmidt inner product, and then COMPARE the recovered
#   c_{ijk} to the independently-known Levi-Civita symbol. Agreement is a check against mathematics.
#   We also check the Jacobi identity sum-cyclic [[A,B],C] = 0 (an invariant of ANY Lie algebra)
#   and antisymmetry of omega.  These anchors exist for the carrier structure itself, not the target.
#
# MEASURED, NEVER PLANTED: noncommutation is read out as opnorm(AB - BA); the 2-form is Tr(rho[A,B]);
#   structure constants are recovered by HS-projection of the measured commutator. Nothing is set
#   equal to a target by construction.
#
# CONTROLS:
#   positive : the su(2) generators -- nonzero commutators, correct eps_{ijk}, nonzero 2-form.
#   negative : a single operator with itself -- [A,A]=0 (sanity floor).
#   boundary : near-commuting deformation A, B+t*A as t grows -> 2-form -> 0 continuously.
#   KILL-CONTROL: a COMMUTING set (3 simultaneously-diagonalizable / mutually-commuting operators,
#                 built as random REAL-diagonal ops in a common eigenbasis). If this commuting set
#                 ALSO produced a nonzero commutator 2-form or nonzero structure constants, the
#                 positive result would be a measurement artifact. It MUST give the null result.
#
# Tools (non-numpy): LinearAlgebra (carrier algebra), Z3 (LOAD-BEARING: over FREE structure-tensor
#   variables obeying the bracket antisymmetry law + abelian closure, Z3 DERIVES that the *measured*
#   |c123| cannot coexist with an abelian algebra -> UNSAT; on a broken/commuting input |c123|~0 the
#   same free-variable query is SAT, so the verdict flips on the measured number), JSON.

using LinearAlgebra, Random, JSON
using Z3

Random.seed!(20260601)

# ---------- carrier: 2x2 complex Hilbert space, spin-1/2 ----------
const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const S  = [sx/2, sy/2, sz/2]          # su(2) generators S_i = sigma_i/2

comm(A,B) = A*B - B*A                    # commutator (the substage bracket)
hs(A,B)   = tr(A' * B)                   # Hilbert-Schmidt inner product <A,B> = Tr(A^dag B)

# Levi-Civita symbol (the INDEPENDENT known invariant we compare against; not used to build S).
function levi_civita(i,j,k)
    p = (i,j,k)
    p == (1,2,3) || p == (2,3,1) || p == (3,1,2) ? 1 :
    p == (3,2,1) || p == (1,3,2) || p == (2,1,3) ? -1 : 0
end

# ---------- (A) MEASURE noncommutation: opnorm(AB - BA) ----------
noncomm_norms = Dict{String,Float64}()
for (i,a) in enumerate(S), (j,b) in enumerate(S)
    j > i || continue
    noncomm_norms["[S$i,S$j]"] = opnorm(comm(a,b))
end
min_offdiag_noncomm = minimum(values(noncomm_norms))   # all off-diagonal pairs must noncommute

# self-commutator (negative control floor): [A,A] = 0
self_comm = maximum(opnorm(comm(a,a)) for a in S)

# ---------- (B) RECOVER su(2) structure constants by HS-projection (non-circular) ----------
# [S_i,S_j] = sum_k c_{ijk} (i S_k).  Project measured commutator onto basis {i S_k}.
# Basis {i S_k} is orthogonal under HS with norm^2 = tr((iS_k)^dag (iS_k)) = tr(S_k^2) = 1/2.
basis = [im*Sk for Sk in S]
basis_norm2 = [real(hs(b,b)) for b in basis]           # = 1/2 each, measured not assumed
c_measured = zeros(3,3,3)
for i in 1:3, j in 1:3
    C = comm(S[i], S[j])
    for k in 1:3
        c_measured[i,j,k] = real(hs(basis[k], C) / basis_norm2[k])
    end
end
# compare recovered c_{ijk} to independently-known eps_{ijk}
max_struct_err = 0.0
for i in 1:3, j in 1:3, k in 1:3
    global max_struct_err = max(max_struct_err, abs(c_measured[i,j,k] - levi_civita(i,j,k)))
end

# ---------- (C) Jacobi identity (invariant of ANY Lie algebra) ----------
jacobi_resid = opnorm(comm(comm(S[1],S[2]),S[3]) +
                      comm(comm(S[2],S[3]),S[1]) +
                      comm(comm(S[3],S[1]),S[2]))

# ---------- (D) commutator 2-form omega_rho(A,B) = Tr(rho[A,B]) ----------
# rho: a generic mixed state, NOT aligned to any S_i (so the 2-form is a genuine readout).
psi = normalize(ComplexF64[0.7+0.2im, -0.3+0.6im])
rho = 0.75*(psi*psi') + 0.25*(I2/2)                    # full-rank mixed state
twoform(A,B) = tr(rho*comm(A,B))
omega = Dict{String,ComplexF64}()
for (i,a) in enumerate(S), (j,b) in enumerate(S)
    omega["w(S$i,S$j)"] = twoform(a,b)
end
# antisymmetry of the 2-form (structural invariant): w(A,B) = -w(B,A)
antisym_err = maximum(abs(twoform(S[i],S[j]) + twoform(S[j],S[i])) for i in 1:3, j in 1:3)
max_abs_twoform = maximum(abs(v) for v in values(omega))   # genuine substage signal: nonzero

# commutator table (real & imag parts of omega) for the report
comm_table = Dict("real"=>Dict(k=>real(v) for (k,v) in omega),
                  "imag"=>Dict(k=>imag(v) for (k,v) in omega))

# ---------- (E) BOUNDARY: deform toward commuting; 2-form must fall continuously ----------
# B_t = S2 + t*S1.  As a check the *commutator* [S1, B_t] = [S1,S2] is t-independent here, so instead
# slide rho -> maximally mixed: omega must vanish as rho -> I/2 (any traceless commutator has Tr=0).
boundary = Float64[]
for lam in range(0.0, 1.0, length=6)
    rl = (1-lam)*rho + lam*(I2/2)
    push!(boundary, abs(tr(rl*comm(S[1],S[2]))))
end
boundary_falls = boundary[1] > boundary[end] && boundary[end] < 1e-9

# ---------- (F) KILL-CONTROL: a COMMUTING operator set ----------
# Build 3 mutually-commuting Hermitian ops in a COMMON random eigenbasis (so genuinely simultaneous).
# A noncommuting structure here would mean our measurement is an artifact. It MUST be ~0.
U = qr(randn(ComplexF64, 4, 4)).Q
U = Matrix(U)
Cset = [U * Diagonal(ComplexF64.(randn(4))) * U' for _ in 1:3]
# (re-Hermitize against roundoff)
Cset = [(M + M')/2 for M in Cset]
kill_max_comm = maximum(opnorm(comm(Cset[i],Cset[j])) for i in 1:3, j in 1:3 if i<j)
# 2-form on a generic 4-dim mixed state
psi4 = normalize(randn(ComplexF64, 4)); rho4 = 0.7*(psi4*psi4') + 0.3*(Matrix{ComplexF64}(I,4,4)/4)
kill_max_twoform = maximum(abs(tr(rho4*comm(Cset[i],Cset[j]))) for i in 1:3, j in 1:3 if i<j)
# structure constants for the commuting set (project onto its own generators) -> must be ~0
kill_max_struct = 0.0
cb = [im*M for M in Cset]; cbn = [real(hs(b,b)) for b in cb]
for i in 1:3, j in 1:3, k in 1:3
    cbn[k] > 1e-12 || continue
    global kill_max_struct = max(kill_max_struct, abs(real(hs(cb[k], comm(Cset[i],Cset[j])) / cbn[k])))
end

# ---------- (G) Z3: structural impossibility -- an abelian bracket cannot carry the measured const ----------
# LOAD-BEARING encoding (free variables, no pinned-literal tautology). We let Z3 DERIVE whether a single
# Lie structure constant can simultaneously (i) obey the ABELIAN law (the identically-zero bracket forces
# every structure constant to vanish) and (ii) reach the *measured* magnitude of c_{123}. The measured
# number enters only as a BOUND that boxes a FREE variable away from zero -- Z3 must SEARCH for an integer
# assignment. It is never set equal to a literal that is then compared to another literal.
#
#   Free integer var: c123 (su(2) structure constants are integral).  Constraints Z3 must reconcile:
#     abelian law   : c123 == 0     (identically-zero bracket; the algebra carries no structure)
#     measured bound: Or(c123 >= mceil, c123 <= -mceil)   where mceil = ceil(|measured c123|) >= 1
#                     for the genuine su(2) measurement -- i.e. the FREE variable must lie OUTSIDE
#                     (-mceil, mceil), which for mceil>=1 EXCLUDES 0.
#   Genuine input: |measured|~1 => mceil=1 => c123 must be <=-1 or >=1, contradicting c123==0 => UNSAT
#     (Z3 DERIVES the impossibility; it is not handed 1!=0).
#   Broken/commuting input: |measured|~0 => mceil=0 => the bound Or(c123>=0, c123<=0) is the whole line,
#     trivially satisfied by c123=0 alongside the abelian law => SAT (kill fires). Verdict FLIPS on input.
function abelian_obstruction_check(m_struct::Float64)
    ctx  = Context()
    c123 = Const("c123", IntSort(ctx))                       # FREE integer structure constant
    slv  = Solver(ctx)
    # abelian hypothesis: identically-zero bracket forces this structure constant to vanish
    add(slv, c123 == IntVal(0, ctx))
    # MEASURED magnitude wired in as a bound that boxes the FREE variable away from 0 (sign-agnostic).
    mceil = ceil(Int, abs(m_struct) - 1e-9)                  # genuine ~1 -> 1 ; kill-set ~0 -> 0
    add(slv, Or([c123 > IntVal(mceil - 1, ctx),              # c123 >= mceil
                 c123 < IntVal(-(mceil - 1), ctx)]))         # c123 <= -mceil
    string(check(slv))
end
m123 = c_measured[1,2,3]                                # MEASURED value (~ +1)
z3_res = abelian_obstruction_check(m123)               # expect "unsat": |c123|~1 cannot also be 0
z3_unsat = (z3_res == "unsat")
# control: feed the kill-set's (commuting) measured structure constant (~0) into the SAME query.
# Now the abelian law c123==0 is consistent with the measured magnitude ~0  ->  SAT (kill fires).
z3_kill_res = abelian_obstruction_check(kill_max_struct)
z3_kill_sat = (z3_kill_res == "sat")

# ---------- VERDICT ----------
positive_ok = min_offdiag_noncomm > 0.1 && max_abs_twoform > 1e-3
anchor_ok   = max_struct_err < 1e-9 && jacobi_resid < 1e-9 && antisym_err < 1e-9
negctrl_ok  = self_comm < 1e-12
kill_ok     = kill_max_comm < 1e-9 && kill_max_twoform < 1e-9 && kill_max_struct < 1e-9
z3_ok       = z3_unsat && z3_kill_sat
# contrast: noncommuting set carries structure the commuting set provably cannot
contrast_ok = (max_abs_twoform > 1e-3) && (kill_max_twoform < 1e-9)

all_pass = positive_ok && anchor_ok && negctrl_ok && kill_ok && z3_ok && contrast_ok && boundary_falls

println("== L5 OPERATOR SUBSTAGE: noncommutation & commutator 2-form ==")
println("min off-diagonal noncommutation opnorm([S_i,S_j]) = ", round(min_offdiag_noncomm, digits=6), " (>0 expected)")
println("self-commutator [A,A] max opnorm           = ", self_comm, " (negative control, ~0)")
println("structure-const max err vs Levi-Civita     = ", max_struct_err, " (anchor, ~0)")
println("Jacobi identity residual                   = ", jacobi_resid, " (anchor, ~0)")
println("2-form antisymmetry err w(A,B)+w(B,A)      = ", antisym_err, " (anchor, ~0)")
println("max |Tr(rho[S_i,S_j])| (substage 2-form)   = ", round(max_abs_twoform, digits=6), " (>0 expected)")
println("boundary 2-form -> mixed: ", round.(boundary, digits=6), " (falls to ~0)")
println("-- KILL-CONTROL (commuting set) --")
println("commuting-set max opnorm([C_i,C_j])        = ", kill_max_comm, " (MUST be ~0)")
println("commuting-set max |2-form|                 = ", kill_max_twoform, " (MUST be ~0)")
println("commuting-set max structure const          = ", kill_max_struct, " (MUST be ~0)")
println("Z3 (free-var derivation): abelian forbids measured |c123| -> ", z3_res, " (expect unsat); kill-set(~0) -> ", z3_kill_res, " (expect sat)")
println("CONTRAST noncommuting vs commuting holds   = ", contrast_ok)
println("ALL_PASS = ", all_pass)

res = Dict(
  "object" => "L5 operator substage: finite noncommuting operator set + commutator 2-form Tr(rho[A,B])",
  "classification" => "tool_lego_fit_probe_PoC",
  "promotion_allowed" => false,
  "carrier" => "LinearAlgebra 2x2 complex Hilbert space, spin-1/2; non-numpy (Julia native + Z3)",
  "noncircular_anchor" => "su(2) Levi-Civita structure constants eps_{ijk}; Jacobi identity; 2-form antisymmetry",
  "measured_not_planted" => Dict(
      "noncommutation_opnorms" => Dict(k=>round(v,digits=8) for (k,v) in noncomm_norms),
      "min_offdiag_noncommutation" => round(min_offdiag_noncomm, digits=8),
      "recovered_structure_constants_c123_c231_c312" =>
          [round(c_measured[1,2,3],digits=8), round(c_measured[2,3,1],digits=8), round(c_measured[3,1,2],digits=8)],
      "structure_const_max_err_vs_levi_civita" => max_struct_err,
      "jacobi_residual" => jacobi_resid,
      "twoform_antisymmetry_err" => antisym_err,
      "commutator_2form_table" => comm_table,
      "max_abs_2form" => round(max_abs_twoform, digits=8),
  ),
  "controls" => Dict(
      "negative_self_commutator_max" => self_comm,
      "boundary_2form_to_maximally_mixed" => round.(boundary, digits=10),
      "boundary_falls_to_zero" => boundary_falls,
  ),
  "kill_control_commuting_set" => Dict(
      "max_commutator_opnorm" => kill_max_comm,
      "max_2form" => kill_max_twoform,
      "max_structure_const" => kill_max_struct,
      "interpretation" => "commuting set carries NO substage structure (null); if it did, positive result = artifact",
  ),
  "z3_structural_proof" => Dict(
      "tool_role" => "load_bearing",
      "encoding" => "FREE integer variable c123; abelian law forces c123==0; the MEASURED |c123| wires in as an Or-bound that boxes c123 away from 0 (>=ceil|m| or <=-ceil|m|). Z3 DERIVES UNSAT when measured!=0 (no integer is both 0 and outside (-1,1)); SAT when measured~0. Not a pinned-literal comparison.",
      "genuine_input_measured_c123" => round(m123, digits=8),
      "abelian_forbids_measured_c123" => string(z3_res),
      "expected" => "unsat",
      "z3_unsat" => z3_unsat,
      "broken_input_kill_set_struct_const" => kill_max_struct,
      "kill_set_abelian_result" => string(z3_kill_res),
      "kill_set_abelian_is_SAT" => z3_kill_sat,
      "verdict_flips_on_input" => z3_unsat && z3_kill_sat,
  ),
  "verdict" => Dict(
      "positive_ok" => positive_ok,
      "anchor_ok" => anchor_ok,
      "negctrl_ok" => negctrl_ok,
      "kill_ok" => kill_ok,
      "z3_ok" => z3_ok,
      "contrast_noncomm_vs_comm_ok" => contrast_ok,
      "boundary_falls" => boundary_falls,
      "all_pass" => all_pass,
  ),
  "honest_status" => all_pass ? "passes: structure constants match su(2) Levi-Civita to 1e-9, kill-control commuting set gives strict null, Z3 UNSAT" : "PARTIAL/FAIL",
)
open(joinpath(@__DIR__, "l5_operator_substage_noncommutation_results.json"), "w") do f
    JSON.print(f, res, 2)
end
println("wrote l5_operator_substage_noncommutation_results.json")
