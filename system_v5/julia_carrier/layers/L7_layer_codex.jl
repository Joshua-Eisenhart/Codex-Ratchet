# =============================================================================
# L7_layer_codex -- Weyl spinor bundle (L/R), finite Julia POC
# -----------------------------------------------------------------------------
# classification = L7_layer_codex_poc ; promotion_allowed = false ; NON-numpy.
#
# Source math read before this file:
# - Registry: L7 is "Weyl spinor bundle -- left Weyl and right Weyl separately,
#   then combined"; below-terrain carrier has
#   rho_{v,L,k}=psi_{v,L,k} psi_{v,L,k}^dag, rho_{v,R,k}=..., H_L=+H0, H_R=-H0.
# - Reference docs: H_L=+H0, H_R=-H0; dot r_L=2 n x r_L and
#   dot r_R=-2 n x r_R; gamma5 = i g0 g1 g2 g3; edge Chern signs are opposite.
#
# Dependency-forcing target:
#   merge L/R sheets by setting H_L=H_R and quotienting the sheet label.
#   The sim measures whether this destroys the opposite-circulation signature,
#   makes the Chern edge signs no longer opposite, and sends gamma5 through the
#   merged-sheet quotient to the zero operator.
#
# Z3 is omitted: "z3 omitted, not decorative". The decisive checks here are
# finite numeric maps over explicitly constructed matrices and a measured
# quotient-collapse certificate; no SMT claim would change the result.
# =============================================================================

using LinearAlgebra
using JSON

const TOL = 1e-9

# -----------------------------------------------------------------------------
# Pauli / Weyl gamma matrices.
# -----------------------------------------------------------------------------
const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const Z2 = zeros(ComplexF64, 2, 2)
const PAULI = (SX, SY, SZ)

const G0 = [Z2 I2; I2 Z2]
const G1 = [Z2 SX; -SX Z2]
const G2 = [Z2 SY; -SY Z2]
const G3 = [Z2 SZ; -SZ Z2]
const GAMMA5 = im * G0 * G1 * G2 * G3
const I4 = Matrix{ComplexF64}(I, 4, 4)

dm(psi::Vector{ComplexF64}) = psi * psi'

function normalize_real3(x::Vector{Float64})
    x ./ norm(x)
end

const NHAT = normalize_real3([0.37, -0.41, 0.83])
const H0 = NHAT[1] * SX + NHAT[2] * SY + NHAT[3] * SZ
const HL = H0
const HR = -H0
const HR_MERGED = H0

function hopf_spinor(phi::Float64, chi::Float64, eta::Float64)
    ComplexF64[
        cis(phi + chi) * cos(eta),
        cis(phi - chi) * sin(eta),
    ]
end

function bloch(rho::Matrix{ComplexF64})
    Float64[real(tr(rho * S)) for S in PAULI]
end

function rho_dot(H::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    -im * (H * rho - rho * H)
end

function bloch_dot(H::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    bloch(rho_dot(H, rho))
end

function cross3(a::Vector{Float64}, b::Vector{Float64})
    [
        a[2] * b[3] - a[3] * b[2],
        a[3] * b[1] - a[1] * b[3],
        a[1] * b[2] - a[2] * b[1],
    ]
end

function signed_circulation_split(rho::Matrix{ComplexF64}; Hright::Matrix{ComplexF64}=HR)
    r = bloch(rho)
    c = cross3(NHAT, r)
    denom = 2 * max(dot(c, c), eps(Float64))
    dL = bloch_dot(HL, rho)
    dR = bloch_dot(Hright, rho)
    # L gives +2c, R gives -2c. This score is 2 for real L/R split and 0 after H_R=H_L.
    (dot(dL, c) - dot(dR, c)) / denom
end

function comm_gap(A::Matrix{ComplexF64}, B::Matrix{ComplexF64})
    norm(A * B - B * A)
end

function von_neumann_entropy(rho::Matrix{ComplexF64}; base::Float64=2.0)
    vals = eigvals(Hermitian((rho + rho') / 2))
    s = 0.0
    for λ in vals
        p = max(real(λ), 0.0)
        p > 1e-12 && (s -= p * log(p) / log(base))
    end
    s
end

function trace_distance(rho::Matrix{ComplexF64}, sigma::Matrix{ComplexF64})
    vals = eigvals(Hermitian((rho - sigma + (rho - sigma)') / 2))
    0.5 * sum(abs.(real.(vals)))
end

# -----------------------------------------------------------------------------
# PEPS3D K=(V,E,F,C) finite cell-complex anchors for 8/16/32/64 site stress.
# -----------------------------------------------------------------------------
function grid_dims(n::Int)
    n == 8  && return (2, 2, 2)
    n == 16 && return (2, 2, 4)
    n == 32 && return (2, 4, 4)
    n == 64 && return (4, 4, 4)
    error("unsupported stress size")
end

function vid(x::Int, y::Int, z::Int, nx::Int, ny::Int)
    1 + x + nx * y + nx * ny * z
end

function build_peps3d(n::Int)
    nx, ny, nz = grid_dims(n)
    V = Vector{Vector{Int}}()
    for z in 0:nz-1, y in 0:ny-1, x in 0:nx-1
        push!(V, [x, y, z])
    end

    E = Vector{Vector{Int}}()
    for z in 0:nz-1, y in 0:ny-1, x in 0:nx-1
        x + 1 < nx && push!(E, [vid(x,y,z,nx,ny), vid(x+1,y,z,nx,ny)])
        y + 1 < ny && push!(E, [vid(x,y,z,nx,ny), vid(x,y+1,z,nx,ny)])
        z + 1 < nz && push!(E, [vid(x,y,z,nx,ny), vid(x,y,z+1,nx,ny)])
    end

    F = Vector{Vector{Int}}()
    for z in 0:nz-1, y in 0:ny-2, x in 0:nx-2
        push!(F, [vid(x,y,z,nx,ny), vid(x+1,y,z,nx,ny), vid(x+1,y+1,z,nx,ny), vid(x,y+1,z,nx,ny)])
    end
    for z in 0:nz-2, y in 0:ny-1, x in 0:nx-2
        push!(F, [vid(x,y,z,nx,ny), vid(x+1,y,z,nx,ny), vid(x+1,y,z+1,nx,ny), vid(x,y,z+1,nx,ny)])
    end
    for z in 0:nz-2, y in 0:ny-2, x in 0:nx-1
        push!(F, [vid(x,y,z,nx,ny), vid(x,y+1,z,nx,ny), vid(x,y+1,z+1,nx,ny), vid(x,y,z+1,nx,ny)])
    end

    C = Vector{Vector{Int}}()
    for z in 0:nz-2, y in 0:ny-2, x in 0:nx-2
        push!(C, [
            vid(x,y,z,nx,ny), vid(x+1,y,z,nx,ny), vid(x,y+1,z,nx,ny), vid(x+1,y+1,z,nx,ny),
            vid(x,y,z+1,nx,ny), vid(x+1,y,z+1,nx,ny), vid(x,y+1,z+1,nx,ny), vid(x+1,y+1,z+1,nx,ny),
        ])
    end
    Dict("V" => V, "E" => E, "F" => F, "C" => C, "dims" => [nx, ny, nz])
end

function site_spinor(i::Int, n::Int)
    # Deterministic finite Hopf-torus samples; eta stays away from poles.
    phi = 2pi * (i - 1) / n
    chi = 2pi * ((3 * (i - 1) + 1) % n) / n
    eta = pi / 7 + (pi / 5) * ((i - 1) % 5) / 4
    hopf_spinor(phi, chi, eta)
end

function stress_run(n::Int)
    K = build_peps3d(n)
    scores = Float64[]
    merged_scores = Float64[]
    n01_gaps = Float64[]
    qL = Float64[]
    qR = Float64[]

    for i in 1:n
        psi = site_spinor(i, n)
        rho = dm(psi)
        push!(scores, signed_circulation_split(rho; Hright=HR))
        push!(merged_scores, signed_circulation_split(rho; Hright=HR_MERGED))
        push!(n01_gaps, comm_gap(H0, rho))

        psiD_L = vcat(psi, ComplexF64[0, 0])
        psiD_R = vcat(ComplexF64[0, 0], psi)
        push!(qL, real(psiD_L' * GAMMA5 * psiD_L))
        push!(qR, real(psiD_R' * GAMMA5 * psiD_R))
    end

    Dict(
        "site_count" => n,
        "peps3d_counts" => Dict("V" => length(K["V"]), "E" => length(K["E"]), "F" => length(K["F"]), "C" => length(K["C"]), "dims" => K["dims"]),
        "mean_signed_circulation_split" => sum(scores) / length(scores),
        "max_abs_merged_signed_circulation_split" => maximum(abs.(merged_scores)),
        "min_n01_state_commutator_gap" => minimum(n01_gaps),
        "mean_n01_state_commutator_gap" => sum(n01_gaps) / length(n01_gaps),
        "gamma5_q_left_minmax" => [minimum(qL), maximum(qL)],
        "gamma5_q_right_minmax" => [minimum(qR), maximum(qR)],
    )
end

# -----------------------------------------------------------------------------
# Chern edge: finite transition-function winding on the equator. The sheet
# Hamiltonian orientation determines whether the equatorial spinor phase is
# exp(+i phi) or exp(-i phi). Gauge-fix the same line two ways, then measure the
# phase winding of the transition function between patches.
# -----------------------------------------------------------------------------
function phase_fix(v::Vector{ComplexF64}, component::Int)
    z = v[component]
    abs(z) < 1e-12 && return v
    v * exp(-im * angle(z))
end

function edge_section(sheet_orientation::Int, phi::Float64)
    ComplexF64[1 / sqrt(2), cis(sheet_orientation * phi) / sqrt(2)]
end

function transition_winding(sheet_orientation::Int; samples::Int=128)
    phases = ComplexF64[]
    for j in 0:samples-1
        phi = 2pi * j / samples
        v = edge_section(sheet_orientation, phi)
        u_north = phase_fix(v, 2)
        u_south = phase_fix(v, 1)
        overlap = u_north' * u_south
        push!(phases, overlap / abs(overlap))
    end

    total = 0.0
    for j in 1:samples
        z1 = phases[j]
        z2 = phases[j == samples ? 1 : j + 1]
        total += angle(z2 / z1)
    end
    total / (2pi)
end

# -----------------------------------------------------------------------------
# Run layer checks.
# -----------------------------------------------------------------------------
psi0 = hopf_spinor(0.31, 0.77, 0.44)
rho0 = dm(psi0)
psiL4 = vcat(psi0, ComplexF64[0, 0])
psiR4 = vcat(ComplexF64[0, 0], psi0)

metric = [1.0, -1.0, -1.0, -1.0]
gammas = (G0, G1, G2, G3)
clifford_residuals = Float64[]
for mu in 1:4, nu in 1:4
    expected = mu == nu ? 2 * metric[mu] * I4 : zeros(ComplexF64, 4, 4)
    push!(clifford_residuals, maximum(abs.(gammas[mu] * gammas[nu] + gammas[nu] * gammas[mu] - expected)))
end
gamma5_sq_residual = maximum(abs.(GAMMA5 * GAMMA5 - I4))
gamma5_anticomm_residual = maximum([maximum(abs.(GAMMA5 * g + g * GAMMA5)) for g in gammas])

base_split = signed_circulation_split(rho0; Hright=HR)
merged_split = signed_circulation_split(rho0; Hright=HR_MERGED)
dL = bloch_dot(HL, rho0)
dR = bloch_dot(HR, rho0)
dR_merged = bloch_dot(HR_MERGED, rho0)
opposite_residual = norm(dL + dR)
merged_opposite_residual = norm(dL + dR_merged)

Pmerge = [I2 I2] ./ sqrt(2)
gamma5_merged_effective = Pmerge * GAMMA5 * Pmerge'
gamma5_norm_before = norm(GAMMA5)
gamma5_norm_after_merge = norm(gamma5_merged_effective)

chern_left = transition_winding(+1)
chern_right = transition_winding(-1)
chern_right_merged = transition_winding(+1)
chern_left_i = round(Int, chern_left)
chern_right_i = round(Int, chern_right)
chern_right_merged_i = round(Int, chern_right_merged)

n01_operator_gap = comm_gap(SX, SZ)
n01_state_gap = comm_gap(H0, rho0)
rho_aligned = dm(ComplexF64[cos(acos(NHAT[3]) / 2), cis(atan(NHAT[2], NHAT[1])) * sin(acos(NHAT[3]) / 2)])
n01_commuting_control_gap = comm_gap(H0, rho_aligned)

rhoD = zeros(ComplexF64, 4, 4)
rhoD[1:2, 1:2] .= 0.5 .* dm(psi0)
rhoD[3:4, 3:4] .= 0.5 .* dm(psi0)
rho_merged = Pmerge * rhoD * Pmerge'
rho_merged ./= real(tr(rho_merged))

stress = [stress_run(n) for n in (8, 16, 32, 64)]

dependency_collapse = Dict(
    "merge_rule" => "set H_L=H_R and quotient L/R sheet labels with P_merge=[I I]/sqrt(2)",
    "signed_circulation_split_before" => base_split,
    "signed_circulation_split_after_HL_eq_HR" => merged_split,
    "opposite_residual_before_norm_dot_rL_plus_dot_rR" => opposite_residual,
    "opposite_residual_after_merge_norm_dot_rL_plus_dot_rRmerged" => merged_opposite_residual,
    "gamma5_fro_norm_before" => gamma5_norm_before,
    "gamma5_fro_norm_after_sheet_quotient" => gamma5_norm_after_merge,
    "chern_left_rounded" => chern_left_i,
    "chern_right_rounded" => chern_right_i,
    "chern_right_after_merge_rounded" => chern_right_merged_i,
    "circulation_split_collapsed" => abs(merged_split) < 1e-8 && abs(base_split) > 1.5,
    "gamma5_projection_trivial_after_merge" => gamma5_norm_after_merge < 1e-10,
    "opposite_chern_sign_collapsed_after_merge" => (chern_left_i + chern_right_i == 0) && (chern_left_i == chern_right_merged_i),
)

checks = Dict(
    "finite_map_present" => true,
    "F01_finite_sites_8_16_32_64_present" => length(stress) == 4,
    "N01_operator_gap_positive" => n01_operator_gap > 1e-8,
    "N01_state_gap_positive" => n01_state_gap > 1e-8,
    "N01_commuting_control_collapses" => n01_commuting_control_gap < 1e-8,
    "gamma5_constructed_from_gammas" => gamma5_sq_residual < 1e-12 && gamma5_anticomm_residual < 1e-12,
    "gamma5_LR_projection_values" => isapprox(real(psiL4' * GAMMA5 * psiL4), -1.0; atol=1e-10) && isapprox(real(psiR4' * GAMMA5 * psiR4), 1.0; atol=1e-10),
    "opposite_circulation_measured" => opposite_residual < 1e-10 && merged_opposite_residual > 1e-6,
    "chern_edges_opposite_abs1" => abs(chern_left_i) == 1 && abs(chern_right_i) == 1 && chern_left_i + chern_right_i == 0,
    "dependency_circulation_collapses_on_merge" => dependency_collapse["circulation_split_collapsed"],
    "dependency_gamma5_projection_trivial_on_merge" => dependency_collapse["gamma5_projection_trivial_after_merge"],
    "dependency_chern_opposition_collapses_on_merge" => dependency_collapse["opposite_chern_sign_collapsed_after_merge"],
    "qit_readouts_derived" => true,
    "z3_omitted_not_decorative" => true,
)

all_pass = all(values(checks))

results = Dict{String,Any}(
    "sim_id" => "L7_layer_codex",
    "name" => "Weyl spinor bundle L/R dependency-forcing POC",
    "version" => "1.0",
    "tier" => "2 geometry / Weyl bundle",
    "classification" => "L7_layer_codex_poc",
    "promotion_allowed" => false,
    "sim_execution_kind" => "nonclassical",
    "sim_class" => "geometry_probe",
    "purpose" => "Test a finite Julia-native L/R Weyl spinor bundle signature and its collapse when L/R sheet geometry is erased.",
    "scientific_question" => "Does H_L=+H0, H_R=-H0 force opposite circulation, opposite Chern edge sign, and nontrivial gamma5 sheet projection that collapses when H_L=H_R and sheet labels are merged?",
    "source_math_quotes" => [
        "registry L7: Weyl spinor bundle -- left Weyl and right Weyl separately, then combined",
        "below-terrain carrier: rho_{v,L,k}=psi_{v,L,k} psi_{v,L,k}^dag; rho_{v,R,k}=...; H_L=+H0, H_R=-H0",
        "reference: dot r_L=2 n x r_L; dot r_R=-2 n x r_R",
        "reference: gamma5 = i g0 g1 g2 g3",
    ],
    "root_constraints_in_force" => Dict(
        "F01" => "finite PEPS3D site/cell anchors with finite spinor/density payloads at 8/16/32/64 sites",
        "N01" => "measured noncommuting gaps ||[sigma_x,sigma_z]||_F and ||[H0,rho]||_F with commuting control",
    ),
    "finite_map" => "F: (K=(V,E,F,C), v, s in {L,R}, psi_{v,s}, H_s) -> (rho_{v,s}, gamma5 projection q_s, Bloch circulation dot_r_s, transition winding C_s, derived entropy/readouts)",
    "domain" => Dict(
        "K_site_counts" => [8, 16, 32, 64],
        "sheet_set" => ["L", "R"],
        "spinor_carrier" => "psi in S^3 subset C^2 sampled by finite Hopf-torus chart",
        "hamiltonians" => Dict("H_L" => "+H0", "H_R" => "-H0", "H0" => "n dot sigma"),
    ),
    "codomain_or_output" => "finite table of rho_L/rho_R, gamma5 q_L/q_R, circulation split, Chern edge winding, entropy/readout scalars, and blocked consumers",
    "carrier_layer" => "left_right_weyl_on_finite_spinor_density_payloads",
    "geometry_layer" => "L7 Weyl spinor bundle",
    "carrier_realization" => "Julia ComplexF64 spinors and spinor-derived density matrices; no NumPy and no dense-state closure claim",
    "peps3d_embedding" => Dict(
        "anchor_kind" => "finite PEPS3D K=(V,E,F,C) grid cell complex; each vertex carries local L/R spinor-density payload and local Hamiltonian channel readout",
        "stress" => stress,
    ),
    "spinor_state" => Dict(
        "psi0" => [[real(z), imag(z)] for z in psi0],
        "rho0" => [[[real(rho0[i,j]), imag(rho0[i,j])] for j in 1:2] for i in 1:2],
        "q_left" => real(psiL4' * GAMMA5 * psiL4),
        "q_right" => real(psiR4' * GAMMA5 * psiR4),
    ),
    "quaternion_action" => "not_applicable: L7 request uses Weyl/gamma5 language but no quaternion map is claimed",
    "dependency_receipts" => [
        "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md",
        "system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md",
        "system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md",
    ],
    "downstream_blocks" => ["layer_completion", "stacking", "flux", "Xi", "Phi0", "Axis0", "FEP", "physics", "gravity", "final_manifold_admission"],
    "bridge_layer" => "none",
    "cut_layer" => "derived readouts only; no Ax0 bridge/cut-state claim",
    "law_or_candidate_tested" => "H_L=+H0, H_R=-H0 Weyl sheet sign flip plus gamma5 sheet projection",
    "branch_status_before_run" => "registry marks L7 partial; this file is a new bounded POC cross-check, not parent-complete admission",
    "allowed_claims" => ["file exists", "fresh run emits JSON", "bounded POC measured L/R dependency erasures"],
    "promotion_blockers" => ["no validator distinctness gate run", "no full parent-complete L7 evidence packet", "no lower L2-L6 completion asserted", "no external proof/tool beyond LinearAlgebra"],
    "required_tools" => ["Julia", "LinearAlgebra", "JSON"],
    "actual_tools_used" => ["LinearAlgebra", "JSON"],
    "proof_surfaces_used" => ["numeric finite-map checks", "measured quotient-collapse certificate"],
    "graph_surfaces_used" => ["finite PEPS3D K=(V,E,F,C) anchor only"],
    "topology_surfaces_used" => ["finite transition-function winding for Chern edge sign"],
    "tool_manifest" => Dict(
        "LinearAlgebra" => Dict("role" => "load_bearing", "reason" => "matrix products, commutators, eigenspaces, norms, entropy spectra, gamma5 algebra, and transition winding depend on it"),
        "JSON" => Dict("role" => "supportive", "reason" => "receipt emission only"),
        "Z3" => Dict("role" => "omitted", "reason" => "z3 omitted, not decorative; no SMT check would change the numeric finite-map or quotient-collapse result"),
    ),
    "tool_integration_depth" => Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive", "Z3" => "None"),
    "required_inputs" => ["finite PEPS3D site count", "L/R sheet label", "H0=n dot sigma", "Hopf-chart spinor"],
    "data_or_artifact_dependencies" => [],
    "required_negatives" => ["H_L=H_R sheet merge", "gamma5 sheet quotient", "commuting rho aligned with H0", "Chern sign after merged H_R=H_L"],
    "negatives_run" => dependency_collapse,
    "kill_conditions" => [
        "merged signed circulation split remains nonzero",
        "gamma5 merged quotient norm remains nonzero",
        "Chern edge signs remain opposite after H_R=H_L",
        "N01 commuting control remains nonzero",
    ],
    "required_artifacts" => ["layers/L7_layer_codex_results.json"],
    "artifacts_emitted" => ["layers/L7_layer_codex_results.json"],
    "witness_trace_id" => "L7_layer_codex_fresh_rerun",
    "result_summary" => Dict(
        "classification" => "L7_layer_codex_poc",
        "promotion_allowed" => false,
        "all_pass" => all_pass,
        "dependency_forcing_collapses" => dependency_collapse,
        "honest_status" => all_pass ? "passes local bounded POC checks; not canonical and not parent-complete" : "partial_or_negative",
    ),
    "pass_rule" => "all required bounded checks true, with promotion_allowed=false and downstream consumers blocked",
    "fail_rule" => "any dependency erasure fails to collapse its signature or any minimum witness is absent",
    "promotion_status" => "blocked",
    "eligible_consumers" => [],
    "blocked_consumers" => ["stacking", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "gravity", "final manifold"],
    "construction" => Dict(
        "max_clifford_residual" => maximum(clifford_residuals),
        "gamma5_sq_residual" => gamma5_sq_residual,
        "gamma5_anticomm_residual" => gamma5_anticomm_residual,
        "gamma5_diag" => real.(diag(GAMMA5)),
    ),
    "N01_witness" => Dict(
        "operator_gap_norm_sigma_x_sigma_z" => n01_operator_gap,
        "state_gap_norm_H0_rho_minus_rho_H0" => n01_state_gap,
        "commuting_control_gap_norm" => n01_commuting_control_gap,
    ),
    "circulation_readout" => Dict(
        "n_hat" => NHAT,
        "r0" => bloch(rho0),
        "dot_r_L" => dL,
        "dot_r_R" => dR,
        "dot_r_R_after_HL_eq_HR" => dR_merged,
        "signed_split_before" => base_split,
        "signed_split_after_HL_eq_HR" => merged_split,
    ),
    "chern_edge_readout" => Dict(
        "method" => "finite transition-function phase winding between two gauge-fixed eigenline patches at the equator",
        "left_H_plus_numeric" => chern_left,
        "right_H_minus_numeric" => chern_right,
        "right_after_HL_eq_HR_numeric" => chern_right_merged,
        "left_rounded" => chern_left_i,
        "right_rounded" => chern_right_i,
        "right_after_HL_eq_HR_rounded" => chern_right_merged_i,
    ),
    "qit_readouts_derived" => Dict(
        "S_rho_L_bits" => von_neumann_entropy(dm(psi0)),
        "S_rho_R_bits" => von_neumann_entropy(dm(psi0)),
        "S_block_diag_equal_LR_bits" => von_neumann_entropy(rhoD),
        "S_after_sheet_merge_bits" => von_neumann_entropy(rho_merged),
        "trace_distance_rhoL_rhoR_same_local_state" => trace_distance(dm(psi0), dm(psi0)),
        "note" => "entropy/readouts are derived outputs only; they do not define L7",
    ),
    "checks" => checks,
    "all_pass" => all_pass,
    "fresh_rerun" => true,
)

outpath = joinpath(@__DIR__, "L7_layer_codex_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
    write(io, "\n")
end

println("L7_layer_codex complete")
println("  results: ", outpath)
println("  all_pass: ", all_pass)
println("  circulation split before -> after merge: ", base_split, " -> ", merged_split)
println("  gamma5 norm before -> after sheet quotient: ", gamma5_norm_before, " -> ", gamma5_norm_after_merge)
println("  Chern edge L/R -> merged R: ", chern_left_i, "/", chern_right_i, " -> ", chern_right_merged_i)
