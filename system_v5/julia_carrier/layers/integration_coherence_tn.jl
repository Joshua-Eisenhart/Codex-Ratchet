#!/usr/bin/env julia

# Integration coherence probe for the open "all legos as one dynamic tensor
# network" question.
#
# Scope:
# - one finite two-qubit tensor-network carrier:
#     chirality qubit (L/R) x Weyl spinor qubit;
# - L/R Weyl spinors are normalized C^2 spinors (S^3);
# - Spin(3)=SU(2) and the Hopf U(1) maximal-torus action act on the same spinor;
# - gamma5 is the chirality split and must commute with the even Spin action;
# - a terrain Lindblad generator acts on the density matrix;
# - a bad U(1) pairing in GL(2,C) but not SU(2) must break nesting.
#
# Classification: PoC. promotion_allowed=false. This is a finite integration
# coherence receipt, not layer completion, PEPS3D admission, or architecture
# closure.

using ITensors
using ITensorMPS
using LinearAlgebra
using JSON
using Dates

const TOL = 1.0e-10
const RECEIPT_PATH = joinpath(@__DIR__, "integration_coherence_tn_receipt.json")
const RESULTS_PATH = joinpath(@__DIR__, "integration_coherence_tn_results.json")

const I2 = Matrix{ComplexF64}(I, 2, 2)
const I3 = Matrix{Float64}(I, 3, 3)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const pauli = (sx, sy, sz)

function spinor_s3(theta::Float64, phi::Float64, chi::Float64)
    v = cis(chi) .* ComplexF64[cos(theta / 2), cis(phi) * sin(theta / 2)]
    return v / norm(v)
end

function su2_axis(axis::Vector{Float64}, theta::Float64)
    n = axis / norm(axis)
    return cos(theta / 2) .* I2 - im * sin(theta / 2) .* (n[1] * sx + n[2] * sy + n[3] * sz)
end

good_hopf_u1(phi::Float64) = ComplexF64[cis(-phi / 2) 0; 0 cis(phi / 2)]
bad_global_u1(phi::Float64) = cis(phi) .* I2

function is_unitary(U::Matrix{ComplexF64}; tol=TOL)
    residual = norm(U' * U - Matrix{ComplexF64}(I, size(U, 1), size(U, 1)))
    return (pass = residual < tol, residual = residual)
end

function is_gl2(U::Matrix{ComplexF64}; tol=TOL)
    det_abs = abs(det(U))
    return (pass = det_abs > tol, det_abs = det_abs)
end

function is_su2(U::Matrix{ComplexF64}; tol=TOL)
    un = is_unitary(U; tol=tol)
    det_residual = abs(det(U) - 1)
    return (pass = un.pass && det_residual < tol,
            unitary_residual = un.residual,
            det_residual = det_residual,
            det_value = det(U))
end

function su2_to_so3(U::Matrix{ComplexF64})
    R = zeros(Float64, 3, 3)
    for j in 1:3
        Xp = U * pauli[j] * U'
        for i in 1:3
            R[i, j] = real(0.5 * tr(pauli[i] * Xp))
        end
    end
    return R
end

function so3_z(phi::Float64)
    c = cos(phi)
    s = sin(phi)
    return [c -s 0.0; s c 0.0; 0.0 0.0 1.0]
end

function so3_axis_angle(axis::Vector{Float64}, theta::Float64)
    n = axis / norm(axis)
    K = [0.0 -n[3] n[2]; n[3] 0.0 -n[1]; -n[2] n[1] 0.0]
    return I3 + sin(theta) .* K + (1 - cos(theta)) .* (K * K)
end

function is_o3(R::Matrix{Float64}; tol=TOL)
    residual = norm(R' * R - I3)
    return (pass = residual < tol, residual = residual, det_value = det(R))
end

function is_so3(R::Matrix{Float64}; tol=TOL)
    o = is_o3(R; tol=tol)
    det_residual = abs(det(R) - 1)
    return (pass = o.pass && det_residual < tol,
            orthogonal_residual = o.residual,
            det_residual = det_residual,
            det_value = det(R))
end

function density(psi::Vector{ComplexF64})
    return psi * psi'
end

function min_eig_hermitian(A::Matrix{ComplexF64})
    H = Hermitian(0.5 .* (A + A'))
    return minimum(real.(eigvals(H)))
end

function complex_pair(z::Complex)
    return [real(z), imag(z)]
end

function rounded(x; digits=12)
    return round(Float64(real(x)); digits=digits)
end

function check_line(name::String, pass::Bool, detail="")
    println(rpad(name, 48), pass ? "PASS" : "FAIL", isempty(detail) ? "" : "  " * detail)
end

# ---------------------------------------------------------------------------
# One finite joint state: chirality qubit x Weyl spinor qubit.
# The two conditional Weyl spinors are each normalized C^2 points on S^3.
# ---------------------------------------------------------------------------
psi_L = spinor_s3(1.13, 0.41, 0.23)
psi_R = spinor_s3(0.87, -0.72, -0.19)

amp_L = sqrt(0.58)
amp_R = cis(0.37) * sqrt(0.42)
ket_L = ComplexF64[1, 0]
ket_R = ComplexF64[0, 1]
psi_joint = amp_L .* kron(ket_L, psi_L) + amp_R .* kron(ket_R, psi_R)
psi_joint ./= norm(psi_joint)

sites = siteinds("Qubit", 2)
psi_itensor = ITensor(ComplexF64, sites[1], sites[2])
for chirality in 1:2, spin in 1:2
    psi_itensor[sites[1] => chirality, sites[2] => spin] =
        psi_joint[(chirality - 1) * 2 + spin]
end
Utn, Stn, Vtn = svd(psi_itensor, sites[1])
psi_mps = MPS([Utn, Stn * Vtn])
tn_residual = norm(prod(psi_mps) - psi_itensor)

rho = density(psi_joint)
rho_trace = tr(rho)
rho_hermitian_residual = norm(rho - rho')
rho_min_eig = min_eig_hermitian(rho)

# gamma5 on the chirality qubit: L=-1, R=+1.
gamma5 = kron(ComplexF64[-1 0; 0 1], I2)
I4 = Matrix{ComplexF64}(I, 4, 4)
P_chiral_L = 0.5 .* (I4 - gamma5)
P_chiral_R = 0.5 .* (I4 + gamma5)

# A generic Spin(3)=SU(2) even action and its Hopf U(1) maximal-torus subaction.
spin_theta = 0.83
spin_axis = [0.31, -0.47, 0.82]
U_spin = su2_axis(spin_axis, spin_theta)
Spin_joint = kron(I2, U_spin)

hopf_phi = 0.61
hopf_phi_2 = -0.27
U_hopf = good_hopf_u1(hopf_phi)
U_hopf_2 = good_hopf_u1(hopf_phi_2)
Hopf_joint = kron(I2, U_hopf)

U_bad = bad_global_u1(0.73)

# ---------------------------------------------------------------------------
# Coherence checks on the common carrier.
# ---------------------------------------------------------------------------
L_norm_pass = abs(norm(psi_L) - 1) < TOL
R_norm_pass = abs(norm(psi_R) - 1) < TOL
joint_norm_pass = abs(norm(psi_joint) - 1) < TOL
tn_state_pass = tn_residual < 1.0e-10
density_pass = abs(rho_trace - 1) < TOL && rho_hermitian_residual < TOL && rho_min_eig > -TOL
gamma5_sq_residual = norm(gamma5 * gamma5 - I4)
gamma5_hermitian_residual = norm(gamma5 - gamma5')
gamma5_projector_sum_residual = norm(P_chiral_L + P_chiral_R - I4)
gamma5_projector_orth_residual = norm(P_chiral_L * P_chiral_R)
gamma5_projectors_ok =
    gamma5_sq_residual < TOL &&
    gamma5_hermitian_residual < TOL &&
    gamma5_projector_sum_residual < TOL &&
    gamma5_projector_orth_residual < TOL

spin_su2 = is_su2(U_spin)
hopf_su2 = is_su2(U_hopf)
hopf_gl2 = is_gl2(U_hopf)
bad_gl2 = is_gl2(U_bad)
bad_unitary = is_unitary(U_bad)
bad_su2 = is_su2(U_bad)

gamma5_spin_comm_residual = norm(Spin_joint * gamma5 - gamma5 * Spin_joint)
gamma5_hopf_comm_residual = norm(Hopf_joint * gamma5 - gamma5 * Hopf_joint)
gamma5_commutes_spin = gamma5_spin_comm_residual < TOL
gamma5_commutes_hopf = gamma5_hopf_comm_residual < TOL
spin_preserve_PL_residual = norm(Spin_joint * P_chiral_L - P_chiral_L * Spin_joint)
spin_preserve_PR_residual = norm(Spin_joint * P_chiral_R - P_chiral_R * Spin_joint)
spin_preserves_chirality_split = spin_preserve_PL_residual < TOL && spin_preserve_PR_residual < TOL

u1_closure_residual = norm(U_hopf * U_hopf_2 - good_hopf_u1(hopf_phi + hopf_phi_2))
u1_as_spin_z_residual = norm(U_hopf - su2_axis([0.0, 0.0, 1.0], hopf_phi))
u1_subaction_pass = hopf_gl2.pass && hopf_su2.pass && u1_closure_residual < TOL && u1_as_spin_z_residual < TOL

bad_u1_breaks_nesting = bad_gl2.pass && bad_unitary.pass && !bad_su2.pass

R_spin = su2_to_so3(U_spin)
R_hopf = su2_to_so3(U_hopf)
spin_image_so3 = is_so3(R_spin)
hopf_image_so3 = is_so3(R_hopf)
spin_so3_rodrigues_residual = norm(R_spin - so3_axis_angle(spin_axis, spin_theta))
hopf_so3_restriction_residual = norm(R_hopf - so3_z(hopf_phi))
minus_same_so3_residual = norm(su2_to_so3(-U_spin) - R_spin)

reflection = [1.0 0.0 0.0; 0.0 1.0 0.0; 0.0 0.0 -1.0]
reflection_o3 = is_o3(reflection)
reflection_not_so3 = reflection_o3.pass && det(reflection) < 0

o3_so3_nested = spin_image_so3.pass && is_o3(R_spin).pass && reflection_not_so3
so3_spin_nested = spin_image_so3.pass && spin_so3_rodrigues_residual < TOL && minus_same_so3_residual < TOL
spin_u1_nested = u1_subaction_pass && hopf_image_so3.pass && hopf_so3_restriction_residual < TOL
su2_gl2_nested = spin_su2.pass && is_gl2(U_spin).pass
nested_chain_consistent = o3_so3_nested && so3_spin_nested && spin_u1_nested && su2_gl2_nested

# Hopf-base readout: the good U(1) action is the z-axis SU(2) restriction.
function bloch(spinor::Vector{ComplexF64})
    return [real(spinor' * sx * spinor), real(spinor' * sy * spinor), real(spinor' * sz * spinor)]
end
base_before = bloch(psi_L)
base_after = bloch(U_hopf * psi_L)
base_expected = so3_z(hopf_phi) * base_before
hopf_base_rotates_as_so3 = norm(base_after - base_expected) < TOL

# Terrain Lindblad on the same density. The jump is block-diagonal by chirality:
# L branch sees sigma_z, R branch sees sigma_x. It is a finite channel/generator
# action on rho, not a terrain-layer promotion.
P_L = ComplexF64[1 0; 0 0]
P_R = ComplexF64[0 0; 0 1]
terrain_A = kron(P_L, sz) + kron(P_R, sx)
gamma = 0.2
dt = 0.1
L_jump = sqrt(gamma) .* terrain_A
drho = L_jump * rho * L_jump' - 0.5 .* (L_jump' * L_jump * rho + rho * L_jump' * L_jump)
rho_next = rho + dt .* drho

terrain_trace_residual = abs(tr(drho))
terrain_hermitian_residual = norm(drho - drho')
rho_next_trace_residual = abs(tr(rho_next) - 1)
rho_next_min_eig = min_eig_hermitian(rho_next)
terrain_nontrivial_norm = norm(rho_next - rho)
terrain_gamma5_comm_residual = norm(terrain_A * gamma5 - gamma5 * terrain_A)
terrain_density_pass =
    terrain_trace_residual < TOL &&
    terrain_hermitian_residual < TOL &&
    rho_next_trace_residual < TOL &&
    rho_next_min_eig > -TOL &&
    terrain_nontrivial_norm > 1.0e-8 &&
    terrain_gamma5_comm_residual < TOL

checks = [
    ("left_weyl_spinor_on_S3", L_norm_pass),
    ("right_weyl_spinor_on_S3", R_norm_pass),
    ("joint_two_qubit_state_normalized", joint_norm_pass),
    ("itensor_mps_joint_state_reconstructs", tn_state_pass),
    ("density_is_valid", density_pass),
    ("gamma5_projectors_ok", gamma5_projectors_ok),
    ("spin3_action_is_su2", spin_su2.pass),
    ("gamma5_commutes_with_spin3_even_action", gamma5_commutes_spin),
    ("spin3_preserves_chirality_split", spin_preserves_chirality_split),
    ("gamma5_commutes_with_hopf_u1_subaction", gamma5_commutes_hopf),
    ("u1_hopf_phase_is_su2_subaction", u1_subaction_pass),
    ("hopf_base_rotates_by_so3_z_restriction", hopf_base_rotates_as_so3),
    ("o3_so3_spin3_u1_chain_nested", nested_chain_consistent),
    ("terrain_lindblad_density_action_valid", terrain_density_pass),
    ("kill_bad_u1_not_inside_su2_breaks_nesting", bad_u1_breaks_nesting),
]

all_pass = all(last.(checks))
architecture_coheres_for_this_finite_object =
    all_pass && nested_chain_consistent && gamma5_commutes_spin && terrain_density_pass

receipt = Dict(
    "kind" => "integration_coherence_tn_receipt",
    "script" => "layers/integration_coherence_tn.jl",
    "result_path" => "layers/integration_coherence_tn_receipt.json",
    "generated_at" => string(now()),
    "classification" => "PoC",
    "promotion_status" => "diagnostic_only",
    "promotion_allowed" => false,
    "sim_execution_kind" => "nonclassical",
    "sim_class" => "integration_coherence_probe",
    "claim_ceiling" => "Finite two-qubit tensor-network integration coherence only. This tests mutual consistency of nested O3/SO3/Spin3/U1 actions, gamma5 chirality split, and one terrain Lindblad density action on one object. It is not canonical, not PEPS3D admission, not layer completion, and not architecture closure.",
    "scientific_question" => "Can the L/R Weyl spinor carrier, Hopf U(1) subaction, Spin(3)=SU(2) action, gamma5 chirality split, and terrain Lindblad density action cohere as one finite tensor-network object?",
    "root_constraints_in_force" => [
        "F01 finite carrier/probe/operator/path set: two qubit sites, finite matrices, finite density, finite subgroup checks",
        "N01 order-sensitive/control pressure: subgroup nesting and bad-U1 kill-control decide whether action composition is admissible"
    ],
    "finite_map" => "C^2_L/R Weyl spinors -> joint C^2_chirality tensor C^2_spinor state -> density rho; nested operators O3 > SO3 > Spin3=SU2 > U1 act through explicit finite matrices; terrain Lindblad maps rho to rho + dt*D(rho).",
    "domain" => Dict(
        "chirality_site" => "Qubit basis 1=L, 2=R",
        "spinor_site" => "Qubit basis for each Weyl spinor",
        "operators" => ["gamma5", "Spin3_SU2", "Hopf_U1_maximal_torus", "terrain_Lindblad_jump", "bad_global_U1_control"]
    ),
    "codomain_or_output" => "Boolean coherence receipt plus JSON metrics over the same 4-dimensional carrier.",
    "carrier_realization" => "Julia ITensors/ITensorMPS two-site MPS plus LinearAlgebra dense readout for finite operator identities.",
    "peps3d_embedding" => "blocked_not_claimed: this is a 2-site tensor-network integration PoC, not a finite PEPS3D cell/bond/face embedding.",
    "spinor_state" => Dict(
        "left_norm" => norm(psi_L),
        "right_norm" => norm(psi_R),
        "joint_norm" => norm(psi_joint),
        "left_components_re_im" => complex_pair.(psi_L),
        "right_components_re_im" => complex_pair.(psi_R)
    ),
    "quaternion_action" => "not_applicable: this probe uses the equivalent SU2 spinor matrix action directly and makes no quaternion-map claim.",
    "dependency_receipts" => [
        "layers/g_su2_spin3_double_cover_results.json",
        "layers/g_u1_hopf_bundle_chern_results.json",
        "layers/l2_weyl_chirality_gamma5_genuine_results.json",
        "layers/L4_terrain_octet_receipt.json"
    ],
    "allowed_claims" => [
        "finite PoC nesting/coherence check on one two-qubit joint tensor-network state",
        "good U1 maximal torus is a valid SU2 subaction in this convention",
        "bad generic global U1 phase breaks U1 subset SU2 nesting",
        "terrain Lindblad is a valid density action on this carrier"
    ],
    "tensor_network" => Dict(
        "sites" => 2,
        "site_dimensions" => dim.(sites),
        "mps_length" => length(psi_mps),
        "max_link_dim" => maxlinkdim(psi_mps),
        "reconstruction_residual" => tn_residual
    ),
    "gamma5_spin3" => Dict(
        "gamma5_diagonal" => [-1, -1, 1, 1],
        "gamma5_sq_residual" => gamma5_sq_residual,
        "gamma5_hermitian_residual" => gamma5_hermitian_residual,
        "projector_sum_residual" => gamma5_projector_sum_residual,
        "projector_orthogonality_residual" => gamma5_projector_orth_residual,
        "spin3_su2_unitary_residual" => spin_su2.unitary_residual,
        "spin3_su2_det_residual" => spin_su2.det_residual,
        "commutator_residual_spin3" => gamma5_spin_comm_residual,
        "commutator_residual_hopf_u1" => gamma5_hopf_comm_residual,
        "spin_preserve_PL_residual" => spin_preserve_PL_residual,
        "spin_preserve_PR_residual" => spin_preserve_PR_residual
    ),
    "u1_su2_gl2_inclusions" => Dict(
        "good_u1_in_gl2" => hopf_gl2.pass,
        "good_u1_in_su2" => hopf_su2.pass,
        "good_u1_closure_residual" => u1_closure_residual,
        "good_u1_equals_spin_z_residual" => u1_as_spin_z_residual,
        "bad_u1_in_gl2" => bad_gl2.pass,
        "bad_u1_unitary" => bad_unitary.pass,
        "bad_u1_in_su2" => bad_su2.pass,
        "bad_u1_det_re_im" => complex_pair(bad_su2.det_value),
        "break_location" => bad_u1_breaks_nesting ? "bad global phase is in GL2(C) and U(2), but det != 1 so U1 subset SU2 fails" : "bad control did not break as required"
    ),
    "reduction_chain" => Dict(
        "chain" => "O(3) > SO(3) > Spin(3)=SU(2) > U(1)",
        "o3_so3_nested" => o3_so3_nested,
        "so3_spin3_nested" => so3_spin_nested,
        "spin3_u1_nested" => spin_u1_nested,
        "su2_gl2_nested" => su2_gl2_nested,
        "spin_image_so3_det" => spin_image_so3.det_value,
        "spin_image_so3_orthogonal_residual" => spin_image_so3.orthogonal_residual,
        "spin_so3_rodrigues_residual" => spin_so3_rodrigues_residual,
        "spin_double_cover_minus_same_so3_residual" => minus_same_so3_residual,
        "hopf_so3_z_restriction_residual" => hopf_so3_restriction_residual,
        "reflection_o3_not_so3_boundary" => reflection_not_so3,
        "nested_chain_consistent" => nested_chain_consistent
    ),
    "terrain_lindblad" => Dict(
        "jump" => "sqrt(gamma) * (P_L tensor sigma_z + P_R tensor sigma_x)",
        "gamma" => gamma,
        "dt" => dt,
        "trace_drho_residual" => terrain_trace_residual,
        "drho_hermitian_residual" => terrain_hermitian_residual,
        "rho_next_trace_residual" => rho_next_trace_residual,
        "rho_next_min_eigenvalue" => rho_next_min_eig,
        "rho_next_minus_rho_norm" => terrain_nontrivial_norm,
        "terrain_gamma5_commutator_residual" => terrain_gamma5_comm_residual
    ),
    "positive" => Dict(
        "good_nested_actions_mutually_consistent" => nested_chain_consistent,
        "gamma5_commutes_with_even_spin_part" => gamma5_commutes_spin,
        "hopf_u1_is_su2_subaction" => u1_subaction_pass,
        "terrain_lindblad_valid_density_action" => terrain_density_pass
    ),
    "boundary" => Dict(
        "O3_reflection_boundary" => "reflection is in O3 but det=-1, so it is excluded by SO3 and has no even Spin3 lift in this probe",
        "global_phase_boundary" => "only center phases +/-I are also in SU2; a generic global U1 phase is not the Hopf SU2 maximal torus used here"
    ),
    "kill_control" => Dict(
        "bad_u1_not_inside_su2_breaks_nesting" => bad_u1_breaks_nesting,
        "bad_u1_det_residual_from_1" => bad_su2.det_residual
    ),
    "graveyard_companions" => [
        "decorative Z3 omitted by request and because direct finite matrix inclusion checks decide this probe",
        "generic global U1 phase in U(2) is not accepted as the SU2 Hopf subaction",
        "O3 reflection is retained only as an O3/SO3 boundary, not as an even Spin3 action"
    ],
    "nearby_variants" => [
        "replace terrain jump with a non-block-diagonal jump to test chirality-mixing failure",
        "lift the same checks to a finite PEPS3D cell carrier before any nonclassical manifold promotion",
        "sample multiple SU2 axes and U1 torus angles for a broader numerical stress receipt"
    ],
    "tool_manifest" => Dict(
        "ITensors" => "load_bearing: builds the explicit two-site tensor state carrying chirality and spinor indices",
        "ITensorMPS" => "load_bearing: SVD-factorized MPS reconstructs the same joint state",
        "LinearAlgebra" => "load_bearing: finite matrix subgroup, commutator, density, and Lindblad checks",
        "JSON" => "supportive: receipt serialization",
        "Z3" => "not_used: user requested no decorative Z3; direct finite matrix checks are decisive here"
    ),
    "tool_integration_depth" => Dict(
        "ITensors" => "load_bearing",
        "ITensorMPS" => "load_bearing",
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive"
    ),
    "promotion_blockers" => [
        "classification is PoC",
        "promotion_allowed=false",
        "single finite two-qubit object only",
        "no PEPS3D carrier admission",
        "no canonical sim template admission claimed",
        "no layer completion or architecture closure claimed"
    ],
    "eligible_consumers" => ["local follow-up integration probes that preserve classification=PoC and promotion_allowed=false"],
    "blocked_consumers" => ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "full manifold admission", "layer completion"],
    "checks" => Dict(name => pass for (name, pass) in checks),
    "architecture_coheres_for_this_finite_object" => architecture_coheres_for_this_finite_object,
    "all_pass" => all_pass
)

for outpath in (RECEIPT_PATH, RESULTS_PATH)
    open(outpath, "w") do io
        JSON.print(io, receipt, 2)
        write(io, "\n")
    end
end

println("INTEGRATION COHERENCE TN")
println("carrier: ITensors/ITensorMPS two-qubit joint state (chirality x Weyl spinor)")
println("receipt: $(RECEIPT_PATH)")
println()
for (name, pass) in checks
    detail = ""
    if name == "gamma5_commutes_with_spin3_even_action"
        detail = "residual=$(rounded(gamma5_spin_comm_residual))"
    elseif name == "u1_hopf_phase_is_su2_subaction"
        detail = "det_residual=$(rounded(hopf_su2.det_residual)), closure=$(rounded(u1_closure_residual))"
    elseif name == "o3_so3_spin3_u1_chain_nested"
        detail = "Spin_to_Rodrigues=$(rounded(spin_so3_rodrigues_residual)), hopf_to_Rz=$(rounded(hopf_so3_restriction_residual))"
    elseif name == "gamma5_projectors_ok"
        detail = "g5sq=$(rounded(gamma5_sq_residual)), PLPR=$(rounded(gamma5_projector_orth_residual))"
    elseif name == "spin3_preserves_chirality_split"
        detail = "PL=$(rounded(spin_preserve_PL_residual)), PR=$(rounded(spin_preserve_PR_residual))"
    elseif name == "terrain_lindblad_density_action_valid"
        detail = "trace_drho=$(rounded(terrain_trace_residual)), min_eig_next=$(rounded(rho_next_min_eig))"
    elseif name == "kill_bad_u1_not_inside_su2_breaks_nesting"
        detail = "bad_det_residual=$(rounded(bad_su2.det_residual))"
    end
    check_line(name, pass, detail)
end
println()
println("ARCHITECTURE_COHERES_FOR_THIS_FINITE_OBJECT: $(architecture_coheres_for_this_finite_object)")
println("BREAK_CONTROL: bad global U(1) is GL2/U2 but not SU2, so nesting breaks at U1 subset SU2 = $(bad_u1_breaks_nesting)")
println("classification: PoC")
println("promotion_allowed: false")
println("ALL_PASS = $(all_pass)")

exit(all_pass ? 0 : 1)
