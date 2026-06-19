#!/usr/bin/env julia
# object_id: geo_s1_spinor_hopf_free_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using Manifolds
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s1_spinor_hopf_free_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8
const PIN_SPEC = "geo_s1_spinor_hopf_free_v0|S1-free|chart:z1=cos(eta)exp(i(phi+chi)),z2=sin(eta)exp(i(phi-chi))|hopf=(2Re z1conj(z2),2Im z1conj(z2),|z1|^2-|z2|^2)|metric=deta^2+dphi^2+dchi^2+2cos(2eta)dphi dchi|bloch_basis=(sigma_x,-sigma_y,sigma_z)|seed_ledger=jax.random.PRNGKey[11000:n1000,20000:n10000,110000:n100000,55/56/57:clustered_control_n10000];torch.Generator.manual_seed[91000:n1000,100000:n10000,190000:n100000]|rerun=SIM_PY geo_s1_spinor_hopf_free_v0_{jax,julia,pytorch,envelope}|classification=scratch_diagnostic"

const TOOL_MANIFEST = Dict{String,Any}(
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive strict-carrier matrix arithmetic and hand metric mirror rows; Manifolds gates the S3/S2 metric/geodesic/volume claims",
    ),
    "Manifolds" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing strict-carrier Sphere(3)/Sphere(2) distance, shortest_geodesic, log/exp, and manifold_volume gates for the S3/S2 geometry rows",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side raw-value proof that sampled Hopf images stay on S2 within scaled tolerance",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization, timestamping, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "LinearAlgebra" => "supportive",
    "Manifolds" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY_HOPF = ComplexF64[0 im; -im 0]
const SZ = ComplexF64[1 0; 0 -1]
const BLOCH_BASIS = [SX, SY_HOPF, SZ]

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function spinor_from_chart(eta::Float64, phi::Float64, chi::Float64)
    ComplexF64[
        cos(eta) * exp(im * (phi + chi)),
        sin(eta) * exp(im * (phi - chi)),
    ]
end

function broken_spinor_from_chart(eta::Float64, phi::Float64, chi::Float64)
    ComplexF64[
        cos(eta) * exp(im * (phi + chi)),
        sin(eta) * exp(im * (phi + chi)),
    ]
end

function chart_roundtrip_vector(psi::Vector{ComplexF64})
    eta = atan(abs(psi[2]), abs(psi[1]))
    a1 = angle(psi[1])
    a2 = angle(psi[2])
    phi = 0.5 * (a1 + a2)
    chi = 0.5 * (a1 - a2)
    spinor_from_chart(eta, phi, chi)
end

function hopf(psi::Vector{ComplexF64})
    z1, z2 = psi[1], psi[2]
    z12 = z1 * conj(z2)
    Float64[
        2.0 * real(z12),
        2.0 * imag(z12),
        abs2(z1) - abs2(z2),
    ]
end

function density(psi::Vector{ComplexF64})
    psi * psi'
end

function bloch_from_density(rho::Matrix{ComplexF64})
    Float64[real(tr(rho * basis)) for basis in BLOCH_BASIS]
end

function density_from_bloch(r::Vector{Float64})
    0.5 .* (I2 .+ r[1] .* SX .+ r[2] .* SY_HOPF .+ r[3] .* SZ)
end

function su2_from_spinor(psi::Vector{ComplexF64})
    z1, z2 = psi[1], psi[2]
    ComplexF64[z1 -conj(z2); z2 conj(z1)]
end

function quat_from_spinor(psi::Vector{ComplexF64})
    Float64[real(psi[1]), imag(psi[1]), -real(psi[2]), imag(psi[2])]
end

function quat_mul(q::Vector{Float64}, r::Vector{Float64})
    a, b, c, d = q
    e, f, g, h = r
    Float64[
        a * e - b * f - c * g - d * h,
        a * f + b * e + c * h - d * g,
        a * g - b * h + c * e + d * f,
        a * h + b * g - c * f + d * e,
    ]
end

function spinor_from_quat(q::Vector{Float64})
    ComplexF64[q[1] + im * q[2], -q[3] + im * q[4]]
end

function unitary_from_axis_angle(axis::Vector{Float64}, angle::Float64)
    n = axis ./ norm(axis)
    generator = n[1] .* SX .+ n[2] .* SY_HOPF .+ n[3] .* SZ
    cos(angle / 2.0) .* I2 .- im * sin(angle / 2.0) .* generator
end

function so3_from_su2_action(unitary::Matrix{ComplexF64})
    cols = Vector{Float64}[]
    for i in 1:3
        e = zeros(Float64, 3)
        e[i] = 1.0
        rho = density_from_bloch(e)
        push!(cols, bloch_from_density(unitary * rho * unitary'))
    end
    hcat(cols...)
end

function midpoint_volume_s3(n::Int)
    total = 0.0
    for k in 0:(n - 1)
        eta = (pi / 2.0) * (k + 0.5) / n
        total += sin(2.0 * eta)
    end
    pi^3 * total / n
end

function midpoint_area_s2(n::Int)
    total = 0.0
    for k in 0:(n - 1)
        theta = pi * (k + 0.5) / n
        total += sin(theta)
    end
    2.0 * pi^2 * total / n
end

function manifolds_metric_receipt()
    s3 = Manifolds.Sphere(3)
    s2 = Manifolds.Sphere(2)
    p3 = [1.0, 0.0, 0.0, 0.0]
    q3 = [0.0, 1.0, 0.0, 0.0]
    p2 = [0.0, 0.0, 1.0]
    q2 = [1.0, 0.0, 0.0]
    mid3 = Manifolds.shortest_geodesic(s3, p3, q3, 0.5)
    mid2 = Manifolds.shortest_geodesic(s2, p2, q2, 0.5)
    exp2 = Manifolds.exp(s2, p2, Manifolds.log(s2, p2, q2))
    Dict{String,Any}(
        "S3" => Dict(
            "api" => "Manifolds.distance/shortest_geodesic/manifold_volume on Sphere(3)",
            "orthogonal_distance" => Manifolds.distance(s3, p3, q3),
            "orthogonal_distance_target" => pi / 2.0,
            "geodesic_midpoint" => mid3,
            "geodesic_midpoint_norm_deviation" => abs(norm(mid3) - 1.0),
            "volume" => Manifolds.manifold_volume(s3),
            "volume_target" => 2.0 * pi^2,
            "pass" => abs(Manifolds.distance(s3, p3, q3) - pi / 2.0) <= TOL &&
                abs(norm(mid3) - 1.0) <= TOL &&
                abs(Manifolds.manifold_volume(s3) - 2.0 * pi^2) <= TOL,
        ),
        "S2" => Dict(
            "api" => "Manifolds.distance/shortest_geodesic/log/exp/manifold_volume on Sphere(2)",
            "orthogonal_distance" => Manifolds.distance(s2, p2, q2),
            "orthogonal_distance_target" => pi / 2.0,
            "geodesic_midpoint" => mid2,
            "log_exp_endpoint_residual" => norm(exp2 .- q2),
            "volume" => Manifolds.manifold_volume(s2),
            "volume_target" => 4.0 * pi,
            "pass" => abs(Manifolds.distance(s2, p2, q2) - pi / 2.0) <= TOL &&
                norm(mid2 .- [sqrt(0.5), 0.0, sqrt(0.5)]) <= TOL &&
                norm(exp2 .- q2) <= TOL &&
                abs(Manifolds.manifold_volume(s2) - 4.0 * pi) <= TOL,
        ),
    )
end

function z3_exists_outside_scaled(values::Vector{Int}, target::Int, tol::Int)
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for value in values
        item = Z3.IntVal(value)
        push!(terms, Z3.Or(Z3.Expr[item > Z3.IntVal(target + tol), item < Z3.IntVal(target - tol)]))
    end
    Z3.add(solver, Z3.Or(terms))
    string(Z3.check(solver))
end

function main()
    mkpath(RESULT_DIR)
    etas = collect(range(0.04, pi / 2.0 - 0.04; length=30))
    phis = collect(range(0.0, 2.0 * pi; length=31))[1:30]
    chis = collect(range(0.0, 2.0 * pi; length=31))[1:30]
    spinors = Vector{ComplexF64}[]
    coord_hopf_max = 0.0
    chart_roundtrip_max = 0.0
    broken_chart_control_max = 0.0
    for eta in etas, phi in phis, chi in chis
        psi = spinor_from_chart(eta, phi, chi)
        push!(spinors, psi)
        h = hopf(psi)
        hc = Float64[sin(2.0 * eta) * cos(2.0 * chi), sin(2.0 * eta) * sin(2.0 * chi), cos(2.0 * eta)]
        coord_hopf_max = max(coord_hopf_max, maximum(abs.(h .- hc)))
        rt = chart_roundtrip_vector(psi)
        chart_roundtrip_max = max(chart_roundtrip_max, min(norm(psi .- rt), norm(psi .+ rt)))
        broken_chart_control_max = max(broken_chart_control_max, maximum(abs.(hopf(broken_spinor_from_chart(eta, phi, chi)) .- hc)))
    end
    norms = [abs2(psi[1]) + abs2(psi[2]) for psi in spinors]
    hopf_norms = [sum(hopf(psi) .^ 2) for psi in spinors]
    scale = 10^6
    scaled = [Int(round(value * scale)) for value in hopf_norms[1:4096]]
    z3_status = z3_exists_outside_scaled(scaled, scale, 10)

    sample_a = spinors[100]
    sample_b = spinors[1000]
    prod = su2_from_spinor(sample_a) * su2_from_spinor(sample_b)
    qprod = quat_mul(quat_from_spinor(sample_a), quat_from_spinor(sample_b))
    quat_dev = maximum(abs.(su2_from_spinor(spinor_from_quat(qprod)) .- prod))
    unitary_dev = maximum(abs.(prod' * prod .- I2))
    det_dev = abs(det(prod) - 1.0)
    base_psi = spinors[777]
    rho0 = density(base_psi)
    rot2 = unitary_from_axis_angle([0.0, 0.0, 1.0], 2.0 * pi) * base_psi
    rot4 = unitary_from_axis_angle([0.0, 0.0, 1.0], 4.0 * pi) * base_psi
    double_cover_path_rows = Dict{String,Any}[]
    for theta in range(0.0, 4.0 * pi; length=9)
        rotated = unitary_from_axis_angle([0.0, 0.0, 1.0], theta) * base_psi
        overlap = dot(base_psi, rotated)
        push!(double_cover_path_rows, Dict(
            "theta_radians" => theta,
            "theta_over_pi" => theta / pi,
            "overlap_real" => real(overlap),
            "overlap_imag" => imag(overlap),
            "spinor_distance_to_initial" => norm(rotated .- base_psi),
            "spinor_distance_to_negative_initial" => norm(rotated .+ base_psi),
            "density_deviation_from_initial" => maximum(abs.(density(rotated) .- rho0)),
        ))
    end
    double_cover = Dict{String,Any}(
        "psi_2pi_plus_initial_norm" => norm(rot2 .+ base_psi),
        "rho_2pi_return_deviation" => maximum(abs.(density(rot2) .- rho0)),
        "psi_4pi_minus_initial_norm" => norm(rot4 .- base_psi),
        "double_cover_path_rows" => double_cover_path_rows,
    )

    phase_alphas = collect(range(0.0, 2.0 * pi; length=129))[1:128]
    phase_hopf_max = 0.0
    rho_phase_max = 0.0
    keystone_max = 0.0
    for psi in spinors[1:512]
        h0 = hopf(psi)
        rho_base = density(psi)
        keystone_max = max(keystone_max, maximum(abs.(bloch_from_density(rho_base) .- h0)))
        for alpha in phase_alphas
            phased = exp(im * alpha) .* psi
            phase_hopf_max = max(phase_hopf_max, maximum(abs.(hopf(phased) .- h0)))
            rho_phase_max = max(rho_phase_max, maximum(abs.(density(phased) .- rho_base)))
        end
    end

    volume_rows = [Dict("N" => n, "method" => "stratified_midpoint_quasi_monte_carlo_over_eta_with_double-cover_factor", "estimate" => midpoint_volume_s3(n), "target" => 2.0 * pi^2, "abs_error" => abs(midpoint_volume_s3(n) - 2.0 * pi^2)) for n in (1000, 10000, 100000)]
    area_rows = [Dict("N" => n, "method" => "stratified_midpoint_quasi_monte_carlo_over_polar_angle", "estimate" => midpoint_area_s2(n), "target" => 4.0 * pi, "abs_error" => abs(midpoint_area_s2(n) - 4.0 * pi)) for n in (1000, 10000, 100000)]
    manifolds_receipt = manifolds_metric_receipt()

    commuting_rows = Dict{String,Any}[]
    wrong_max = 0.0
    for (axis, angle) in [([1.0, 2.0, 3.0], 0.17), ([-2.0, 1.0, 0.5], -0.63), ([0.25, -0.75, 1.5], 1.11)]
        unitary = unitary_from_axis_angle(axis, angle)
        rmat = so3_from_su2_action(unitary)
        max_dev = 0.0
        max_wrong = 0.0
        for psi in spinors[1:2048]
            lhs = hopf(unitary * psi)
            rhs = rmat * hopf(psi)
            wrong = rmat' * hopf(psi)
            max_dev = max(max_dev, norm(lhs .- rhs))
            max_wrong = max(max_wrong, norm(lhs .- wrong))
        end
        wrong_max = max(wrong_max, max_wrong)
        push!(commuting_rows, Dict(
            "axis" => axis ./ norm(axis),
            "angle" => angle,
            "max_deviation" => max_dev,
            "wrong_rotation_pairing_max_deviation" => max_wrong,
            "R_det_deviation" => abs(det(rmat) - 1.0),
            "R_orthogonality_deviation" => maximum(abs.(rmat' * rmat .- Matrix{Float64}(I, 3, 3))),
        ))
    end

    fiber_t = collect(range(0.0, 2.0 * pi; length=2049))[1:2048]
    fiber_bases = [spinor_from_chart(0.0, 0.0, 0.0), spinor_from_chart(pi / 4.0, 0.0, 0.0)]
    fiber_map_dev = 0.0
    fiber_length_rows = Dict{String,Any}[]
    for (idx, psi0) in enumerate(fiber_bases)
        pts = [exp(im * t) .* psi0 for t in fiber_t]
        h0 = hopf(psi0)
        for psi in pts
            fiber_map_dev = max(fiber_map_dev, maximum(abs.(hopf(psi) .- h0)))
        end
        curve_length = 0.0
        for k in 1:length(pts)
            a = pts[k]
            b = pts[mod1(k + 1, length(pts))]
            curve_length += acos(clamp(real(dot(a, b)), -1.0, 1.0))
        end
        push!(fiber_length_rows, Dict("fiber_index" => idx - 1, "length" => curve_length, "target" => 2.0 * pi, "abs_error" => abs(curve_length - 2.0 * pi)))
    end

    receipts = Dict{String,Any}(
        "G1_spinors" => Dict(
            "sample_count" => length(spinors),
            "max_norm_sq_deviation" => maximum(abs.(norms .- 1.0)),
            "chart_vector_roundtrip_max_deviation" => chart_roundtrip_max,
            "broken_chart_control_max_hopf_coordinate_deviation" => broken_chart_control_max,
            "pass" => maximum(abs.(norms .- 1.0)) <= TOL && chart_roundtrip_max <= TOL,
        ),
        "G2_s3_metric_volume" => Dict(
            "volume_convergence" => volume_rows,
            "manifolds_metric_volume_gate" => manifolds_receipt["S3"],
            "hand_metric_rows_demoted_to" => "mirror_convergence_rows",
            "pass" => volume_rows[end]["abs_error"] < 1.0e-8 && manifolds_receipt["S3"]["pass"],
        ),
        "G3_su2_structure" => Dict(
            "su2_product_unitary_max_deviation" => unitary_dev,
            "su2_product_det_max_deviation" => det_dev,
            "quaternion_product_matrix_max_deviation" => quat_dev,
            "double_cover" => double_cover,
            "pass" => unitary_dev <= TOL && det_dev <= TOL && quat_dev <= TOL && double_cover["rho_2pi_return_deviation"] <= TOL && double_cover["psi_2pi_plus_initial_norm"] <= TOL && double_cover["psi_4pi_minus_initial_norm"] <= TOL,
        ),
        "G4_hopf_map" => Dict(
            "max_unit_sphere_deviation" => maximum(abs.(hopf_norms .- 1.0)),
            "coordinate_form_max_deviation" => coord_hopf_max,
            "phase_invariance_max_deviation" => phase_hopf_max,
            "pass" => maximum(abs.(hopf_norms .- 1.0)) <= TOL && coord_hopf_max <= TOL && phase_hopf_max <= TOL,
        ),
        "G5_fibers" => Dict(
            "fiber_map_to_single_basepoint_max_deviation" => fiber_map_dev,
            "fiber_length_rows" => fiber_length_rows,
            "linking_integral_role" => "computed independently in PyTorch leg",
            "pass" => fiber_map_dev <= TOL && maximum([row["abs_error"] for row in fiber_length_rows]) < 1.0e-5,
        ),
        "G6_density_quotient" => Dict(
            "rho_phase_invariance_max_deviation" => rho_phase_max,
            "bloch_equals_hopf_max_deviation" => keystone_max,
            "receipt_label" => "exact_by_algebra_rows",
            "pass" => rho_phase_max <= TOL && keystone_max <= TOL,
        ),
        "G7_s2_base" => Dict(
            "area_convergence" => area_rows,
            "manifolds_metric_volume_geodesic_gate" => manifolds_receipt["S2"],
            "hand_metric_rows_demoted_to" => "mirror_convergence_rows",
            "commuting_square_rows" => commuting_rows,
            "max_commuting_square_deviation" => maximum([row["max_deviation"] for row in commuting_rows]),
            "wrong_rotation_pairing_control_max_deviation" => wrong_max,
            "pass" => area_rows[end]["abs_error"] < 1.0e-8 && manifolds_receipt["S2"]["pass"] && maximum([row["max_deviation"] for row in commuting_rows]) <= TOL && wrong_max > 1.0e-3,
        ),
    )
    proofs = Dict{String,Any}(
        "julia_z3_hopf_unit_sphere" => Dict(
            "solver" => "Z3.jl",
            "verdict" => z3_status,
            "scaled_integer_factor" => scale,
            "bound_sample_count" => length(scaled),
            "tolerance_int" => 10,
            "raw_scaled_min_max" => [minimum(scaled), maximum(scaled)],
            "pass" => z3_status == "unsat",
        ),
    )
    all_pass = all([record["pass"] for record in values(receipts)]) && proofs["julia_z3_hopf_unit_sphere"]["pass"]
    payload = Dict{String,Any}(
        "schema_version" => "geo_s1_spinor_hopf_free_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_authoritative_sim_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "program_receipt" => PROGRAM_RECEIPT,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "reads_peer_result" => READS_PEER_RESULT,
        "julia_project" => Base.active_project(),
        "packages_used" => ["LinearAlgebra", "Manifolds", "Z3"],
        "aligned_packages_load_bearing" => ["Manifolds", "Z3"],
        "claim_path_tools" => ["Manifolds", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "convention_pins" => Dict(
            "chart" => "z1=cos(eta)exp(i(phi+chi)), z2=sin(eta)exp(i(phi-chi))",
            "bloch_basis" => "(sigma_x,-sigma_y,sigma_z)",
            "s3_volume_chart_cover" => "factor 1/2 for the (phi,chi) double cover",
        ),
        "G_receipts" => receipts,
        "convergence_rows" => Dict(
            "G2_s3_volume" => volume_rows,
            "G7_s2_area" => area_rows,
        ),
        "convergence_ladder_rows" => Dict(
            "G2_s3_volume" => volume_rows,
            "G7_s2_area" => area_rows,
        ),
        "exact_by_algebra_rows" => Dict(
            "G6_density_quotient" => [
                Dict(
                    "row_type" => "exact_by_algebra_row",
                    "rho_phase_invariance_max_deviation" => rho_phase_max,
                    "bloch_equals_hopf_max_deviation" => keystone_max,
                    "note" => "flat machine-epsilon residual from algebraic identity checks; not a convergence ladder row.",
                ),
            ],
        ),
        "proofs" => proofs,
        "tool_calls" => [
            Dict(
                "tool" => "Manifolds",
                "qualified_api/function" => "Manifolds.distance/shortest_geodesic/log/exp/manifold_volume",
                "input_object" => "Sphere(3) and Sphere(2) orthogonal-point fixtures",
                "output_object" => manifolds_receipt,
                "positive_case" => "S3/S2 distances, geodesic midpoint/log-exp, and volumes match pinned values",
                "negative/erased_control" => "hand midpoint rows are mirrors and cannot gate without Manifolds receipt",
                "boundary_case" => "orthogonal points have distance pi/2",
                "demotion_condition" => "if Manifolds is absent or any Sphere API gate fails, S3/S2 metric rows demote to mirror-only",
                "gates" => ["all_pass", "G2_s3_metric_volume", "G7_s2_base"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "scaled sampled Hopf unit-sphere values",
                "output_object" => proofs["julia_z3_hopf_unit_sphere"],
                "positive_case" => "no sampled Hopf image lies outside the scaled tolerance",
                "negative/erased_control" => "disequality assertion must be unsat",
                "boundary_case" => "integer scaled tolerance 10 at scale 1e6",
                "demotion_condition" => "if raw values are replaced by booleans, proof is decorative",
                "gates" => ["all_pass", "G4_hopf_map", "crossover_proofs"],
            ),
        ],
        "controls" => Dict(
            "broken_chart_control_fails" => broken_chart_control_max > 1.0e-2,
            "wrong_rotation_pairing_control_fails" => wrong_max > 1.0e-3,
        ),
        "shared_scalars" => Dict(
            "hopf_unit_sphere_max_deviation" => receipts["G4_hopf_map"]["max_unit_sphere_deviation"],
            "keystone_identity_max_deviation" => receipts["G6_density_quotient"]["bloch_equals_hopf_max_deviation"],
            "s2_commuting_square_max_deviation" => receipts["G7_s2_base"]["max_commuting_square_deviation"],
            "s3_volume_final_abs_error" => volume_rows[end]["abs_error"],
            "s2_area_final_abs_error" => area_rows[end]["abs_error"],
        ),
        "all_pass" => all_pass,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH, "engine" => "julia")))
    return all_pass ? 0 : 1
end

exit(main())
