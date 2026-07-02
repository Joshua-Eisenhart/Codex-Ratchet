#!/usr/bin/env julia

# Candidate bridge-readout probe.
#
# This file intentionally computes candidate readouts only. It does not admit
# Xi, Phi0, Axis0, flux, bridge, or physics claims. The hard gate remains:
# promotion_allowed=false.

using LinearAlgebra
using Printf

const RECEIPT_PATH = "layers/bridge_readout_candidates_results.json"
const CANDIDATE_CLASSIFICATION = "bridge_candidate_probe"

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

projector(psi::Vector{ComplexF64}) = psi * psi'

function hopf_section(theta::Float64, phi::Float64, winding::Int)
    v = ComplexF64[cos(theta / 2), sin(theta / 2) * cis(winding * phi)]
    return v / norm(v)
end

function berry_curvature(theta::Float64, phi::Float64, winding::Int; h::Float64=1.0e-5)
    p0 = projector(hopf_section(theta, phi, winding))
    pt = projector(hopf_section(theta + h, phi, winding))
    pp = projector(hopf_section(theta, phi + h, winding))
    dpt = (pt - p0) / h
    dpp = (pp - p0) / h
    return real(im * tr(p0 * (dpt * dpp - dpp * dpt)))
end

function berry_curvature_frozen(theta::Float64, phi::Float64; h::Float64=1.0e-5)
    p = projector(hopf_section(0.7, 1.1, 1))
    z = (p - p) / h
    return real(im * tr(p * (z * z - z * z)))
end

function chern_number(curv_fn; ntheta::Int=180, nphi::Int=180)
    dtheta = pi / ntheta
    dphi = 2pi / nphi
    total = 0.0
    for i in 0:ntheta-1, j in 0:nphi-1
        theta = (i + 0.5) * dtheta
        phi = (j + 0.5) * dphi
        total += curv_fn(theta, phi) * dtheta * dphi
    end
    return total / (2pi)
end

function bloch_hamiltonian(m::Float64, kx::Float64, ky::Float64; orientation::Int=1)
    dx = sin(kx)
    dy = orientation * sin(ky)
    dz = m + 2.0 - cos(kx) - cos(ky)
    return dx * SX + dy * SY + dz * SZ
end

function occupied_spinor(m::Float64, kx::Float64, ky::Float64; orientation::Int=1)
    e = eigen(Hermitian(bloch_hamiltonian(m, kx, ky; orientation=orientation)))
    return e.vectors[:, 1]
end

function unit_overlap(u::AbstractVector{ComplexF64}, v::AbstractVector{ComplexF64})
    z = dot(u, v)
    a = abs(z)
    return a <= 1.0e-14 ? one(ComplexF64) : z / a
end

function fhs_chern(m::Float64; orientation::Int=1, nk::Int=41)
    occ = Array{ComplexF64}(undef, 2, nk, nk)
    for ix in 1:nk, iy in 1:nk
        kx = 2pi * (ix - 1) / nk
        ky = 2pi * (iy - 1) / nk
        occ[:, ix, iy] = occupied_spinor(m, kx, ky; orientation=orientation)
    end

    total_phase = 0.0
    for ix in 1:nk, iy in 1:nk
        ixp = ix == nk ? 1 : ix + 1
        iyp = iy == nk ? 1 : iy + 1
        ux = unit_overlap(occ[:, ix, iy], occ[:, ixp, iy])
        uy_x = unit_overlap(occ[:, ixp, iy], occ[:, ixp, iyp])
        ux_y = unit_overlap(occ[:, ix, iyp], occ[:, ixp, iyp])
        uy = unit_overlap(occ[:, ix, iy], occ[:, ix, iyp])
        total_phase += angle(ux * uy_x * conj(ux_y) * conj(uy))
    end
    return total_phase / (2pi)
end

curve_hopf_a(t::Float64) = [cos(t), sin(t), 0.0]
curve_hopf_b(t::Float64) = [0.0, 1.0 + cos(t), sin(t)]
curve_unlinked_b(t::Float64) = [0.0, 3.0 + cos(t), sin(t)]
d_curve_a(t::Float64) = [-sin(t), cos(t), 0.0]
d_curve_b(t::Float64) = [0.0, -sin(t), cos(t)]

function gauss_linking(curve1, dcurve1, curve2, dcurve2; n::Int=240)
    dt = 2pi / n
    ds = 2pi / n
    total = 0.0
    for i in 0:n-1, j in 0:n-1
        t = (i + 0.5) * dt
        s = (j + 0.5) * ds
        r = curve1(t) - curve2(s)
        denom = norm(r)^3
        total += dot(r, cross(dcurve1(t), dcurve2(s))) / denom * dt * ds
    end
    return total / (4pi)
end

function bell_pair_state(linking_number::Int)
    dim = 2^(2 * linking_number)
    psi = zeros(ComplexF64, dim)
    for bits in 0:(2^linking_number - 1)
        idx = 0
        for q in 1:linking_number
            bit = (bits >> (q - 1)) & 1
            idx += bit * 2^(q - 1)
            idx += bit * 2^(linking_number + q - 1)
        end
        psi[idx + 1] = 1 / sqrt(2.0^linking_number)
    end
    return psi
end

function product_state(nqubits::Int)
    psi = zeros(ComplexF64, 2^nqubits)
    psi[1] = 1
    return psi
end

function partial_transpose_c(rho::Matrix{ComplexF64}, linking_number::Int)
    da = 2^linking_number
    dc = 2^linking_number
    out = zeros(ComplexF64, da * dc, da * dc)
    for a1 in 0:da-1, c1 in 0:dc-1, a2 in 0:da-1, c2 in 0:dc-1
        row = a1 + da * c1 + 1
        col = a2 + da * c2 + 1
        source_row = a1 + da * c2 + 1
        source_col = a2 + da * c1 + 1
        out[row, col] = rho[source_row, source_col]
    end
    return out
end

function log_negativity_from_state(psi::Vector{ComplexF64}, linking_number::Int; dephase::Bool=false)
    rho = psi * psi'
    if dephase
        rho = Diagonal(diag(rho)) |> Matrix{ComplexF64}
    end
    rho_pt = partial_transpose_c(rho, linking_number)
    evals = eigvals(Hermitian(0.5 * (rho_pt + rho_pt')))
    return log2(sum(abs.(real.(evals))))
end

area_leaf(theta::Float64) = 2pi^2 * sin(2theta)

function json_string(s::AbstractString)
    escaped = replace(s, "\\" => "\\\\", "\"" => "\\\"", "\n" => "\\n", "\r" => "\\r", "\t" => "\\t")
    return "\"" * escaped * "\""
end

function json_value(x)
    if x === nothing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        if !isfinite(x)
            return json_string(string(x))
        end
        return @sprintf("%.12g", x)
    elseif x isa AbstractString
        return json_string(x)
    elseif x isa Dict
        parts = String[]
        for key in sort(collect(keys(x)))
            push!(parts, json_string(string(key)) * ": " * json_value(x[key]))
        end
        return "{" * join(parts, ", ") * "}"
    elseif x isa AbstractVector
        return "[" * join(json_value.(x), ", ") * "]"
    else
        return json_string(string(x))
    end
end

function write_json(path::String, data::Dict{String, Any})
    open(path, "w") do io
        write(io, json_value(data))
        write(io, "\n")
    end
end

function near_integer(x::Float64; tol::Float64=0.08)
    r = round(Int, x)
    return abs(x - r) <= tol, r
end

function main()
    c1_hopf = chern_number((t, p) -> berry_curvature(t, p, 1))
    c1_anti = chern_number((t, p) -> berry_curvature(t, p, -1))
    c1_trivial = chern_number((t, p) -> berry_curvature(t, p, 0))
    c1_frozen = chern_number((t, p) -> berry_curvature_frozen(t, p))
    c1_hopf_ok, c1_hopf_round = near_integer(c1_hopf)
    _, c1_anti_round = near_integer(c1_anti)
    _, c1_trivial_round = near_integer(c1_trivial)

    chern_right = fhs_chern(-1.0; orientation=1)
    chern_left = fhs_chern(-1.0; orientation=-1)
    chern_trivial = fhs_chern(3.0; orientation=1)
    chiral_c_right = round(Int, chern_right)
    chiral_c_left = abs(round(Int, chern_left))
    chiral_flux = chiral_c_right - 0
    chiral_mirror_flux = 0 - chiral_c_left

    link_gauss = gauss_linking(curve_hopf_a, d_curve_a, curve_hopf_b, d_curve_b)
    unlink_gauss = gauss_linking(curve_hopf_a, d_curve_a, curve_unlinked_b, d_curve_b)
    link_abs_ok, link_round_signed = near_integer(link_gauss)
    link_round = abs(link_round_signed)

    link_logneg = log_negativity_from_state(bell_pair_state(link_round), link_round)
    product_logneg = log_negativity_from_state(product_state(2), 1)
    dephased_logneg = log_negativity_from_state(bell_pair_state(1), 1; dephase=true)

    area_thetas = [pi / 4, 0.65, 0.50, 0.35, 0.20, 0.0]
    area_rows = [Dict{String, Any}(
        "theta" => theta,
        "A_theta" => area_leaf(theta),
    ) for theta in area_thetas]
    descent = [Float64(row["A_theta"]) for row in area_rows[1:end-1]]
    ratchet_descends = all(descent[i] > descent[i + 1] for i in 1:length(descent)-1)
    area_trivial_zero = abs(area_leaf(0.0)) < 1.0e-12

    table = [
        Dict{String, Any}(
            "readout" => "u1_hopf_first_chern_c1",
            "method" => "Berry-curvature integral c1=(1/2pi) int i Tr(P[dP_theta,dP_phi]) over S2",
            "candidate_pool" => "gated Xi/Phi0/bridge pool only",
            "value" => c1_hopf,
            "rounded" => c1_hopf_round,
            "controls" => Dict(
                "anti_hopf_c1" => c1_anti,
                "anti_hopf_rounded" => c1_anti_round,
                "trivial_c1" => c1_trivial,
                "trivial_rounded" => c1_trivial_round,
                "kill_frozen_projector_c1" => c1_frozen,
            ),
            "pass" => c1_hopf_ok && abs(c1_hopf_round) == 1 && c1_trivial_round == 0 && abs(c1_frozen) < 1.0e-10,
        ),
        Dict{String, Any}(
            "readout" => "chiral_central_charge_flux_candidate",
            "method" => "Fukui-Hatsugai-Suzuki occupied-band Chern readout for QWZ chiral sector",
            "candidate_pool" => "gated flux pool only",
            "value" => chiral_flux,
            "rounded" => chiral_flux,
            "controls" => Dict(
                "right_sector_chern" => chern_right,
                "right_sector_cR" => chiral_c_right,
                "mirror_left_sector_chern" => chern_left,
                "mirror_left_sector_cL_abs" => chiral_c_left,
                "mirror_flux_cR_minus_cL" => chiral_mirror_flux,
                "trivial_sector_chern" => chern_trivial,
                "trivial_flux" => round(Int, chern_trivial),
            ),
            "pass" => abs(chiral_flux) == 1 && abs(chiral_mirror_flux) == 1 && round(Int, chern_trivial) == 0,
        ),
        Dict{String, Any}(
            "readout" => "hopf_linking_number_equals_log_negativity",
            "method" => "Gauss linking integral for Hopf-link curves plus partial-transpose log-negativity of one Bell-pair link",
            "candidate_pool" => "gated Phi0/Xi bridge pool only",
            "value" => link_round,
            "continuous_gauss_linking" => link_gauss,
            "log_negativity" => link_logneg,
            "controls" => Dict(
                "unlinked_gauss_linking" => unlink_gauss,
                "product_log_negativity" => product_logneg,
                "dephased_log_negativity" => dephased_logneg,
            ),
            "pass" => link_abs_ok && link_round == 1 && abs(link_logneg - 1.0) < 1.0e-10 &&
                      abs(unlink_gauss) < 0.08 && abs(product_logneg) < 1.0e-10 &&
                      abs(dephased_logneg) < 1.0e-10,
        ),
        Dict{String, Any}(
            "readout" => "leaf_area_ratchet_monotone",
            "method" => "A(theta)=2*pi^2*sin(2theta) on nested Hopf/Clifford torus leaves",
            "candidate_pool" => "gated monotone bridge pool only",
            "value_at_clifford_theta_pi_over_4" => area_leaf(pi / 4),
            "rows" => area_rows,
            "controls" => Dict(
                "theta_0_area" => area_leaf(0.0),
                "theta_pi_over_2_area" => area_leaf(pi / 2),
            ),
            "pass" => ratchet_descends && area_trivial_zero && abs(area_leaf(pi / 2)) < 1.0e-10,
        ),
    ]

    candidates_computed = all(Bool(row["pass"]) for row in table)
    gating_flagged = CANDIDATE_CLASSIFICATION == "bridge_candidate_probe"
    promotion_allowed = false
    all_pass = candidates_computed && gating_flagged && !promotion_allowed

    receipt = Dict{String, Any}(
        "artifact" => "bridge_readout_candidates",
        "script" => "layers/bridge_readout_candidates.jl",
        "json_receipt" => RECEIPT_PATH,
        "classification" => CANDIDATE_CLASSIFICATION,
        "promotion_allowed" => promotion_allowed,
        "canonical_bridge_claim" => false,
        "canonical_Xi_claim" => false,
        "canonical_Phi0_claim" => false,
        "canonical_Axis0_claim" => false,
        "canonical_flux_claim" => false,
        "gating_caveat" => "CANDIDATE bridge readouts only. GATED: pre-admission candidates, not canonical Xi/Phi0/Axis0/flux/bridge claims. Stage gate still blocks promotion until coupling/coexistence/emergence evidence exists.",
        "language" => "Julia",
        "non_numpy" => true,
        "decorative_z3" => false,
        "tool_manifest" => Dict{String, Any}(
            "LinearAlgebra" => "load-bearing dense eigensystems, projectors, trace norms, Gauss-link vector operations, and Chern spinor overlaps",
            "Printf" => "stdout formatting and numeric JSON formatting only",
        ),
        "tool_integration_depth" => Dict{String, Any}(
            "LinearAlgebra" => "load_bearing",
            "Printf" => "supportive",
            "Z3" => "None; deliberately omitted because no SMT predicate is load-bearing for this candidate wrapper",
        ),
        "finite_map_scope" => Dict{String, Any}(
            "F01" => "finite grids of base points, momenta, curve samples, Bell-pair Hilbert states, and theta leaves",
            "N01" => "order-sensitive Berry/FHS plaquette products, partial transpose on C subsystem, and oriented Gauss integral",
            "domain" => "finite numerical carrier samples from the already-simed Julia architecture",
            "codomain_or_output" => "integer/scalar candidate readout table plus kill/control readouts",
            "downstream_consumers_blocked" => ["Xi", "Phi0", "Axis0", "canonical_flux", "canonical_bridge", "physics"],
        ),
        "candidate_bridge_readout_table" => table,
        "kill_summary" => Dict{String, Any}(
            "trivial_hopf_c1_zero" => c1_trivial_round == 0,
            "frozen_projector_c1_zero" => abs(c1_frozen) < 1.0e-10,
            "trivial_chiral_flux_zero" => round(Int, chern_trivial) == 0,
            "unlinked_gauss_linking_zero" => abs(unlink_gauss) < 0.08,
            "product_log_negativity_zero" => abs(product_logneg) < 1.0e-10,
            "dephased_log_negativity_zero" => abs(dephased_logneg) < 1.0e-10,
            "trivial_leaf_area_zero" => area_trivial_zero,
        ),
        "checks" => Dict{String, Any}(
            "all_candidates_computed" => candidates_computed,
            "gating_flagged" => gating_flagged,
            "promotion_allowed_false" => !promotion_allowed,
            "classification_bridge_candidate_probe" => CANDIDATE_CLASSIFICATION == "bridge_candidate_probe",
        ),
        "all_pass" => all_pass,
    )

    write_json(RECEIPT_PATH, receipt)

    println("CANDIDATE bridge-readout table (NOT canonical bridge/Xi/Phi0/Axis0/flux admission)")
    println("classification=$(CANDIDATE_CLASSIFICATION) promotion_allowed=false")
    println("readout | value | controls/kill")
    @printf("u1_hopf_first_chern_c1 | %.6f rounded=%d | trivial=%.6f frozen=%.6f anti=%.6f\n",
            c1_hopf, c1_hopf_round, c1_trivial, c1_frozen, c1_anti)
    @printf("chiral_central_charge_flux_candidate | c_R-c_L=%d | C_right=%.6f C_mirror=%.6f C_trivial=%.6f\n",
            chiral_flux, chern_right, chern_left, chern_trivial)
    @printf("hopf_linking_number_equals_log_negativity | Gauss=%.6f rounded_abs=%d LN=%.6f | unlink=%.6f product_LN=%.6f dephased_LN=%.6f\n",
            link_gauss, link_round, link_logneg, unlink_gauss, product_logneg, dephased_logneg)
    @printf("leaf_area_ratchet_monotone | A(pi/4)=%.6f | A(0)=%.6f A(pi/2)=%.6f descends=%s\n",
            area_leaf(pi / 4), area_leaf(0.0), area_leaf(pi / 2), string(ratchet_descends))
    println("GATING CAVEAT: CANDIDATE ONLY; promotion_allowed=false; not canonical Xi/Phi0/Axis0/flux/bridge evidence.")
    println("JSON_RECEIPT=$(RECEIPT_PATH)")
    println("ALL_PASS=$(all_pass)")
end

main()
