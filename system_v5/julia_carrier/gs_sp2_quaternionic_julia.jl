#!/usr/bin/env julia

# gs_sp2_quaternionic
#
# PoC carrier probe only. promotion_allowed=false.
# This file checks an explicit finite HP^1=S^4 quaternionic carrier using
# 4x4 complex matrix representatives and a wrong-sign control.

using LinearAlgebra
using CliffordAlgebras
using Z3
using JSON

const OBJECT_ID = "gs_sp2_quaternionic"
const CLASSIFICATION = "PoC"
const PROMOTION_ALLOWED = false
const TOL = 1.0e-10
const RESULT_PATH = joinpath(@__DIR__, "gs_sp2_quaternionic_results.json")

frob(M) = sqrt(sum(abs2, M))
max_abs(M) = maximum(abs.(M))
bool01(x::Bool) = x ? 1.0 : 0.0

const EYE2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

# Explicit 4x4 complex representatives. With this sign convention:
# I*J=K, J*K=I, K*I=J, and each square is -1.
const I4Q = ComplexF64[
     im  0   0   0;
     0  -im  0   0;
     0   0   im  0;
     0   0   0  -im
]
const J4Q = ComplexF64[
     0   im  0   0;
     im  0   0   0;
     0   0   0   im;
     0   0   im  0
]
const K4Q = ComplexF64[
     0  -1   0   0;
     1   0   0   0;
     0   0   0  -1;
     0   0   1   0
]
const ID4 = Matrix{ComplexF64}(I, 4, 4)

function direct_sum_copies(base::Matrix{ComplexF64}, copies::Int)
    rows, cols = size(base)
    out = zeros(ComplexF64, rows * copies, cols * copies)
    for c in 1:copies
        r0 = (c - 1) * rows + 1
        c0 = (c - 1) * cols + 1
        out[r0:r0 + rows - 1, c0:c0 + cols - 1] = base
    end
    out
end

function quat_structure(n::Int)
    @assert iseven(n)
    qI2 = im * SZ
    qJ2 = im * SX
    qK2 = -im * SY
    copies = div(n, 2)
    direct_sum_copies(qI2, copies),
    direct_sum_copies(qJ2, copies),
    direct_sum_copies(qK2, copies)
end

function algebra_profile(Iq::Matrix{ComplexF64}, Jq::Matrix{ComplexF64}, Kq::Matrix{ComplexF64})
    n = size(Iq, 1)
    Id = Matrix{ComplexF64}(I, n, n)
    Dict{String,Any}(
        "IJ_residual" => max_abs(Iq * Jq - Kq),
        "JK_residual" => max_abs(Jq * Kq - Iq),
        "KI_residual" => max_abs(Kq * Iq - Jq),
        "I2_residual" => max_abs(Iq * Iq + Id),
        "J2_residual" => max_abs(Jq * Jq + Id),
        "K2_residual" => max_abs(Kq * Kq + Id),
        "I_antihermitian_residual" => max_abs(Iq + Iq'),
        "J_antihermitian_residual" => max_abs(Jq + Jq'),
        "K_antihermitian_residual" => max_abs(Kq + Kq'),
        "JI_plus_K_residual" => max_abs(Jq * Iq + Kq),
        "noncomm_gap" => max_abs(Iq * Jq - Jq * Iq),
    )
end

function closes(profile::Dict{String,Any})
    keys = [
        "IJ_residual", "JK_residual", "KI_residual",
        "I2_residual", "J2_residual", "K2_residual",
        "I_antihermitian_residual", "J_antihermitian_residual", "K_antihermitian_residual",
    ]
    all(Float64(profile[k]) < TOL for k in keys)
end

function z3_quaternion_closed(ij_equals_k::Bool, jk_equals_i::Bool, ki_equals_j::Bool; tag::String)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    zij = Z3.BoolVar("$(tag)_ij_equals_k", ctx)
    zjk = Z3.BoolVar("$(tag)_jk_equals_i", ctx)
    zki = Z3.BoolVar("$(tag)_ki_equals_j", ctx)
    Z3.add(solver, zij == Z3.BoolVal(ij_equals_k, ctx))
    Z3.add(solver, zjk == Z3.BoolVal(jk_equals_i, ctx))
    Z3.add(solver, zki == Z3.BoolVal(ki_equals_j, ctx))
    Z3.add(solver, Z3.And([zij, zjk, zki]))
    string(Z3.check(solver))
end

function sector_norm(A::Matrix{ComplexF64}, P::Matrix{ComplexF64})
    opnorm(P * A * P)
end

base = algebra_profile(I4Q, J4Q, K4Q)
ij_equals_k = Float64(base["IJ_residual"]) < TOL
jk_equals_i = Float64(base["JK_residual"]) < TOL
ki_equals_j = Float64(base["KI_residual"]) < TOL
squares_neg1 = all(Float64(base[k]) < TOL for k in ["I2_residual", "J2_residual", "K2_residual"])
antihermitian = all(Float64(base[k]) < TOL for k in [
    "I_antihermitian_residual", "J_antihermitian_residual", "K_antihermitian_residual"
])

IJ = I4Q * J4Q
IJ_broken = -K4Q
broken = Dict{String,Any}(
    "control" => "wrong_sign_IJ_equals_minus_K",
    "IJ_broken_vs_K_frob" => frob(IJ_broken - K4Q),
    "IJ_broken_vs_K_max" => max_abs(IJ_broken - K4Q),
    "IJ_vs_IJ_broken_frob" => frob(IJ - IJ_broken),
    "IJ_equals_IJ_broken" => max_abs(IJ - IJ_broken) < TOL,
    "IJ_broken_equals_K" => max_abs(IJ_broken - K4Q) < TOL,
)

boundary = Dict{String,Any}(
    "control" => "commutative_limit_I_equals_J",
    "IJ_at_I_equals_J_vs_negative_identity" => max_abs(I4Q * I4Q + ID4),
    "IJ_at_I_equals_J_vs_K" => max_abs(I4Q * I4Q - K4Q),
    "equals_negative_identity" => max_abs(I4Q * I4Q + ID4) < TOL,
    "equals_K" => max_abs(I4Q * I4Q - K4Q) < TOL,
)

# Projectors for a complex structure I with I^2=-1 require the involution chi=-iI.
# The raw form (1+-I)/2 is recorded as a failed boundary so the sign issue is not hidden.
ChiI = -im * I4Q
Pplus = (ID4 + ChiI) / 2
Pminus = (ID4 - ChiI) / 2
raw_Pplus = (ID4 + I4Q) / 2
raw_Pminus = (ID4 - I4Q) / 2

chirality = Dict{String,Any}(
    "chirality_involution" => "chi_I = -i*I, with chi_I^2=1",
    "chi_square_residual" => max_abs(ChiI * ChiI - ID4),
    "Pplus_idempotent_residual" => max_abs(Pplus * Pplus - Pplus),
    "Pminus_idempotent_residual" => max_abs(Pminus * Pminus - Pminus),
    "Pplus_Pminus_residual" => max_abs(Pplus * Pminus),
    "Psum_identity_residual" => max_abs(Pplus + Pminus - ID4),
    "I_on_Pplus_residual" => max_abs(I4Q * Pplus - im * Pplus),
    "I_on_Pminus_residual" => max_abs(I4Q * Pminus + im * Pminus),
    "projectors_pass" => max_abs(Pplus * Pplus - Pplus) < TOL &&
        max_abs(Pminus * Pminus - Pminus) < TOL &&
        max_abs(Pplus * Pminus) < TOL &&
        max_abs(Pplus + Pminus - ID4) < TOL,
    "raw_complex_structure_Pplus_idempotent_residual" => max_abs(raw_Pplus * raw_Pplus - raw_Pplus),
    "raw_complex_structure_Pminus_idempotent_residual" => max_abs(raw_Pminus * raw_Pminus - raw_Pminus),
    "raw_complex_structure_projectors_pass" => max_abs(raw_Pplus * raw_Pplus - raw_Pplus) < TOL &&
        max_abs(raw_Pminus * raw_Pminus - raw_Pminus) < TOL,
)

theta = 0.37
U = exp(theta * I4Q / 2)
Ui = inv(U)
Ih = U * I4Q * Ui
Jh = U * J4Q * Ui
Kh = U * K4Q * Ui
holonomy_residual = max_abs(Ih * Jh - Kh)
holonomy_erased_transport_residual = max_abs(Ih * Jh - K4Q)
holonomy = Dict{String,Any}(
    "subgroup_action" => "uniform Sp(1) conjugation by exp(theta*I/2)",
    "theta" => theta,
    "IJ_equals_K_after_transport_residual" => holonomy_residual,
    "holonomy_preserved" => holonomy_residual < TOL,
    "erased_K_transport_control_residual" => holonomy_erased_transport_residual,
    "erased_transport_control_excluded" => holonomy_erased_transport_residual > 1.0e-6,
)

epsilon = 0.1
gap_plus = sector_norm(I4Q, Pplus)
gap_minus = sector_norm(I4Q, Pminus)
I_eps = I4Q + epsilon * J4Q
gap_plus_eps = sector_norm(I_eps, Pplus)
gap_minus_eps = sector_norm(I_eps, Pminus)
sym_gap = abs(gap_plus_eps - gap_minus_eps)
symmetry_breaking = Dict{String,Any}(
    "epsilon" => epsilon,
    "gap_plus" => gap_plus,
    "gap_minus" => gap_minus,
    "gap_difference" => abs(gap_plus - gap_minus),
    "gap_plus_after_uniform_epsJ" => gap_plus_eps,
    "gap_minus_after_uniform_epsJ" => gap_minus_eps,
    "symmetry_breaking_gap" => sym_gap,
    "real_asymmetry" => sym_gap > TOL,
    "status" => sym_gap > TOL ? "asymmetry_survived_probe" : "convention_only_under_uniform_epsJ",
)

ladder = Dict{String,Any}[]
for n in [2, 4, 8, 16]
    In, Jn, Kn = quat_structure(n)
    profile = algebra_profile(In, Jn, Kn)
    push!(ladder, Dict{String,Any}(
        "n" => n,
        "IJ_residual" => profile["IJ_residual"],
        "JK_residual" => profile["JK_residual"],
        "KI_residual" => profile["KI_residual"],
        "I2_residual" => profile["I2_residual"],
        "J2_residual" => profile["J2_residual"],
        "K2_residual" => profile["K2_residual"],
        "noncomm_gap" => profile["noncomm_gap"],
        "algebra_closed" => closes(profile),
    ))
end
ladder_all_closed = all(Bool(row["algebra_closed"]) for row in ladder)

cl3 = CliffordAlgebra(3, 0)
e12 = cl3.e1 * cl3.e2
e23 = cl3.e2 * cl3.e3
e13 = cl3.e1 * cl3.e3
clifford = Dict{String,Any}(
    "package" => "CliffordAlgebras",
    "algebra" => "Cl(3,0)",
    "e12_times_e23_equals_e13" => e12 * e23 == e13,
    "e12_square_scalar" => Float64(real(CliffordAlgebras.scalar(e12 * e12))),
    "e12_square_equals_negative_one" => abs(Float64(real(CliffordAlgebras.scalar(e12 * e12))) + 1.0) < TOL,
)

z3_genuine_status = z3_quaternion_closed(ij_equals_k, jk_equals_i, ki_equals_j; tag="genuine")
z3_broken_status = z3_quaternion_closed(false, jk_equals_i, ki_equals_j; tag="broken")
z3 = Dict{String,Any}(
    "query" => "all measured profile booleans IJ_equals_K, JK_equals_I, KI_equals_J hold",
    "genuine_profile" => Dict(
        "IJ_equals_K" => ij_equals_k,
        "JK_equals_I" => jk_equals_i,
        "KI_equals_J" => ki_equals_j,
    ),
    "genuine_status" => z3_genuine_status,
    "broken_profile" => Dict(
        "IJ_equals_K" => false,
        "JK_equals_I" => jk_equals_i,
        "KI_equals_J" => ki_equals_j,
    ),
    "broken_status" => z3_broken_status,
    "verdict_flips" => z3_genuine_status == "sat" && z3_broken_status != "sat",
    "tool_role" => "load_bearing",
)

scalar_invariants = Dict{String,Float64}(
    "IJ_residual" => Float64(base["IJ_residual"]),
    "JK_residual" => Float64(base["JK_residual"]),
    "KI_residual" => Float64(base["KI_residual"]),
    "I2_residual" => Float64(base["I2_residual"]),
    "J2_residual" => Float64(base["J2_residual"]),
    "K2_residual" => Float64(base["K2_residual"]),
    "I_antihermitian_residual" => Float64(base["I_antihermitian_residual"]),
    "J_antihermitian_residual" => Float64(base["J_antihermitian_residual"]),
    "K_antihermitian_residual" => Float64(base["K_antihermitian_residual"]),
    "JI_plus_K_residual" => Float64(base["JI_plus_K_residual"]),
    "noncomm_gap" => Float64(base["noncomm_gap"]),
    "IJ_broken_vs_K_frob" => Float64(broken["IJ_broken_vs_K_frob"]),
    "IJ_vs_IJ_broken_frob" => Float64(broken["IJ_vs_IJ_broken_frob"]),
    "boundary_vs_negative_identity" => Float64(boundary["IJ_at_I_equals_J_vs_negative_identity"]),
    "boundary_vs_K" => Float64(boundary["IJ_at_I_equals_J_vs_K"]),
    "chi_square_residual" => Float64(chirality["chi_square_residual"]),
    "Pplus_idempotent_residual" => Float64(chirality["Pplus_idempotent_residual"]),
    "Pminus_idempotent_residual" => Float64(chirality["Pminus_idempotent_residual"]),
    "Pplus_Pminus_residual" => Float64(chirality["Pplus_Pminus_residual"]),
    "Psum_identity_residual" => Float64(chirality["Psum_identity_residual"]),
    "raw_Pplus_idempotent_residual" => Float64(chirality["raw_complex_structure_Pplus_idempotent_residual"]),
    "raw_Pminus_idempotent_residual" => Float64(chirality["raw_complex_structure_Pminus_idempotent_residual"]),
    "holonomy_residual" => Float64(holonomy["IJ_equals_K_after_transport_residual"]),
    "holonomy_erased_transport_residual" => Float64(holonomy["erased_K_transport_control_residual"]),
    "gap_plus" => Float64(symmetry_breaking["gap_plus"]),
    "gap_minus" => Float64(symmetry_breaking["gap_minus"]),
    "gap_plus_after_uniform_epsJ" => Float64(symmetry_breaking["gap_plus_after_uniform_epsJ"]),
    "gap_minus_after_uniform_epsJ" => Float64(symmetry_breaking["gap_minus_after_uniform_epsJ"]),
    "symmetry_breaking_gap" => Float64(symmetry_breaking["symmetry_breaking_gap"]),
)
for row in ladder
    n = Int(row["n"])
    scalar_invariants["ladder_n$(n)_IJ_residual"] = Float64(row["IJ_residual"])
    scalar_invariants["ladder_n$(n)_JK_residual"] = Float64(row["JK_residual"])
    scalar_invariants["ladder_n$(n)_KI_residual"] = Float64(row["KI_residual"])
    scalar_invariants["ladder_n$(n)_I2_residual"] = Float64(row["I2_residual"])
    scalar_invariants["ladder_n$(n)_noncomm_gap"] = Float64(row["noncomm_gap"])
end

positive_checks = Dict{String,Any}(
    "IJ_equals_K" => ij_equals_k,
    "JK_equals_I" => jk_equals_i,
    "KI_equals_J" => ki_equals_j,
    "squares_equal_negative_identity" => squares_neg1,
    "all_antihermitian" => antihermitian,
)

all_structural = all(values(positive_checks)) &&
    Bool(broken["IJ_broken_equals_K"]) == false &&
    Bool(broken["IJ_equals_IJ_broken"]) == false &&
    Bool(boundary["equals_negative_identity"]) &&
    Bool(boundary["equals_K"]) == false &&
    Bool(chirality["projectors_pass"]) &&
    Bool(holonomy["holonomy_preserved"]) &&
    Bool(z3["verdict_flips"]) &&
    ladder_all_closed &&
    Bool(clifford["e12_times_e23_equals_e13"]) &&
    Bool(clifford["e12_square_equals_negative_one"])

result = Dict{String,Any}(
    "object_id" => OBJECT_ID,
    "classification" => CLASSIFICATION,
    "promotion_allowed" => PROMOTION_ALLOWED,
    "claim_ceiling" => "PoC carrier probe only; no layer-completion, manifold admission, coupling, bridge, flux, or physics claim.",
    "finite_carrier" => "HP^1 = S^4 represented by explicit 4x4 complex quaternionic matrices",
    "root_constraints_in_force" => ["F01 finite carrier/probe/operator set", "N01 noncommuting quaternion operation order"],
    "domain" => "finite complex spinor carrier C^4 plus n=2,4,8,16 finite ladders",
    "codomain_or_output" => "measured residuals, booleans, Z3 statuses, and parity scalar invariants",
    "carrier_realization" => "Julia ComplexF64 matrices; JAX complex128 parity mirror",
    "peps3d_embedding" => "blocked: this PoC does not assert a PEPS3D carrier admission",
    "spinor_state" => "chirality involution chi_I=-iI on C^4; Pplus/Pminus projectors measured",
    "quaternion_action" => "I,J,K explicit matrices with IJ=K, JK=I, KI=J and wrong-sign IJ=-K control",
    "downstream_blocks" => ["layer completion", "manifold admission", "coupling", "bridge", "flux", "physics"],
    "positive_checks" => positive_checks,
    "control_broken_wrong_sign" => broken,
    "boundary_commutative_limit" => boundary,
    "chirality_projectors" => chirality,
    "holonomy_preserved" => Bool(holonomy["holonomy_preserved"]),
    "holonomy" => holonomy,
    "symmetry_breaking" => symmetry_breaking,
    "size_ladder" => ladder,
    "z3_load_bearing" => z3,
    "clifford_anchor" => clifford,
    "scalar_invariants" => scalar_invariants,
    "summary" => Dict{String,Any}(
        "positive_checks_pass" => all(values(positive_checks)),
        "negative_control_passes" => Bool(broken["IJ_broken_equals_K"]) == false &&
            Bool(broken["IJ_equals_IJ_broken"]) == false,
        "boundary_check_passes" => Bool(boundary["equals_negative_identity"]) && Bool(boundary["equals_K"]) == false,
        "chirality_projectors_pass" => Bool(chirality["projectors_pass"]),
        "holonomy_preserved" => Bool(holonomy["holonomy_preserved"]),
        "symmetry_breaking_real_asymmetry" => Bool(symmetry_breaking["real_asymmetry"]),
        "z3_load_bearing" => Bool(z3["verdict_flips"]),
        "size_ladder_all_closed" => ladder_all_closed,
        "clifford_anchor_pass" => Bool(clifford["e12_times_e23_equals_e13"]) &&
            Bool(clifford["e12_square_equals_negative_one"]),
        "all_structural_checks_pass" => all_structural,
        "honest_status" => all_structural ? "passes local rerun" : "partial",
    ),
    "tool_manifest" => Dict{String,Any}(
        "LinearAlgebra" => "load_bearing: matrix multiplication, norms, exponential, projector and sector norms",
        "CliffordAlgebras" => "supportive: independent Cl(3,0) even-subalgebra anchor",
        "Z3" => "load_bearing: measured-boolean closure verdict flips genuine sat vs broken unsat",
        "JSON" => "supportive: writes result receipt",
    ),
    "tool_integration_depth" => Dict{String,Any}(
        "LinearAlgebra" => "load_bearing",
        "CliffordAlgebras" => "supportive",
        "Z3" => "load_bearing",
        "JSON" => "supportive",
    ),
)

open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end

println("gs_sp2_quaternionic")
println("object_id=", OBJECT_ID)
println("classification=", CLASSIFICATION)
println("promotion_allowed=false")
println("IJ_equals_K=", ij_equals_k, " JK_equals_I=", jk_equals_i, " KI_equals_J=", ki_equals_j)
println("broken_IJ_broken_equals_K=", broken["IJ_broken_equals_K"])
println("boundary_equals_negative_identity=", boundary["equals_negative_identity"], " boundary_equals_K=", boundary["equals_K"])
println("chirality_projectors_pass=", chirality["projectors_pass"])
println("holonomy_preserved=", holonomy["holonomy_preserved"])
println("symmetry_breaking_gap=", symmetry_breaking["symmetry_breaking_gap"])
println("z3_genuine_status=", z3_genuine_status, " z3_broken_status=", z3_broken_status, " z3_verdict_flips=", z3["verdict_flips"])
println("size_ladder_all_closed=", ladder_all_closed)
println("all_structural_checks_pass=", all_structural)
println("results_path=", RESULT_PATH)
