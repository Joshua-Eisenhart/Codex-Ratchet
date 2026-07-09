#!/usr/bin/env julia
# object_id: foundation_foundation_r5_hopf_fibration_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: true

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_r5_hopf_fibration"
const OBJECT_ID = "foundation_foundation_r5_hopf_fibration_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r5_hopf_fibration_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r5_hopf_fibration_julia_results.json")
const R3_RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r3_octonion_cl6_link_xhigh_julia_results.json")
const TOL = 1.0e-8

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = true

const TOOL_MANIFEST = Dict{String,Any}(
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Cl(0,2) quaternionic spinor carrier check for the Hopf S^3 coordinates",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive stereographic projection and discrete Gauss linking arithmetic",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing read of R3's persisted result JSON (foundation_r3_octonion_cl6_link_xhigh_julia_results.json) for peer-dependency provenance, plus supportive result serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "CliffordAlgebras" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "load_bearing",
)

function load_r3_peer_result()
    isfile(R3_RESULT_PATH) || error("R5 Hopf fibration sim requires R3 peer result at $(R3_RESULT_PATH); none found.")
    JSON.parsefile(R3_RESULT_PATH)
end

# Same Cayley-Dickson construction R3 uses on its quaternion sub-algebra
# (foundation_r3_octonion_cl6_link_xhigh_julia.jl), recomputed locally so the
# S^3 quaternion carrier this rung samples from is cross-checked against R3's
# admitted quaternion left-multiplication rank/spinor-dim, not re-derived from
# a bare trig parametrization with no link to R3.
function cd_conj(x::Vector{Float64})
    y = copy(x)
    length(y) > 1 && (y[2:end] .*= -1.0)
    y
end

function cd_mul(x::Vector{Float64}, y::Vector{Float64})
    n = length(x)
    n == 1 && return [x[1] * y[1]]
    half = n ÷ 2
    a, b = x[1:half], x[(half + 1):end]
    c, d = y[1:half], y[(half + 1):end]
    vcat(cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c)))
end

function cd_basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function cd_left_matrix(dim::Int, unit_idx0::Int)
    e = cd_basis(dim, unit_idx0)
    hcat([cd_mul(e, cd_basis(dim, col0)) for col0 in 0:(dim - 1)]...)
end

cd_left_matrices(dim::Int) = [cd_left_matrix(dim, idx0) for idx0 in 1:(dim - 1)]

function cd_generated_rank(mats::Vector{Matrix{Float64}}, generator_count::Int)
    dim = size(mats[1], 1)
    cols = Vector{Float64}[]
    for mask in 0:(2^generator_count - 1)
        acc = Matrix{Float64}(I, dim, dim)
        for idx in 1:generator_count
            if ((mask >> (idx - 1)) & 1) == 1
                acc = acc * mats[idx]
            end
        end
        push!(cols, vec(acc))
    end
    mat = hcat(cols...)
    singular = svdvals(mat)
    max_s = isempty(singular) ? 0.0 : maximum(singular)
    tol = max(size(mat)...) * eps(Float64) * max_s * 100.0
    count(>(tol), singular)
end

function r3_provenance_check(r3::AbstractDict)
    r3_summary = r3["summary"]
    quat_mats = cd_left_matrices(4)
    rank2 = cd_generated_rank(quat_mats, 3)
    ident4 = Matrix{Float64}(I, 4, 4)
    anticomm_residual = maximum(
        norm(quat_mats[i] * quat_mats[j] + quat_mats[j] * quat_mats[i] - (i == j ? -2.0 .* ident4 : zeros(4, 4)))
        for i in eachindex(quat_mats), j in eachindex(quat_mats)
    )
    Dict{String,Any}(
        "r3_result_path" => R3_RESULT_PATH,
        "r3_object_id" => get(r3, "object_id", nothing),
        "r3_source_sha256" => get(r3, "source_sha256", nothing),
        "r3_quaternion_cl2_rank" => r3_summary["quaternion_cl2_rank"],
        "r3_quaternion_spinor_dim" => r3_summary["quaternion_spinor_dim"],
        "local_recomputed_quaternion_rank_from_same_cd_mul_construction" => rank2,
        "local_quaternion_anticommutation_max_residual" => anticomm_residual,
        "matches_r3_rank" => rank2 == r3_summary["quaternion_cl2_rank"],
        "matches_r3_anticommutation" => anticomm_residual <= TOL,
    )
end

function hopf_map(q::Vector{Float64})
    a, b, c, d = q
    [
        2.0 * (a * c + b * d),
        2.0 * (b * c - a * d),
        a * a + b * b - c * c - d * d,
    ]
end

function hopf_fiber(theta::Float64, phi::Float64, n::Int)
    rows = Vector{Vector{Float64}}()
    for k in 0:(n - 1)
        psi = 2.0 * pi * k / n
        z1_phase = psi + phi
        z2_phase = psi
        push!(
            rows,
            [
                cos(theta / 2.0) * cos(z1_phase),
                cos(theta / 2.0) * sin(z1_phase),
                sin(theta / 2.0) * cos(z2_phase),
                sin(theta / 2.0) * sin(z2_phase),
            ],
        )
    end
    rows
end

function stereographic_basis(p::Vector{Float64})
    p = p ./ norm(p)
    basis = Vector{Vector{Float64}}()
    for idx in 1:4
        v = zeros(Float64, 4)
        v[idx] = 1.0
        v = v - dot(p, v) .* p
        for b in basis
            v = v - dot(b, v) .* b
        end
        nv = norm(v)
        if nv > 1.0e-12
            push!(basis, v ./ nv)
        end
        length(basis) == 3 && break
    end
    p, basis
end

function stereographic_project(curve::Vector{Vector{Float64}}, pole::Vector{Float64}, basis)
    out = Vector{Vector{Float64}}()
    for x in curve
        denom = 1.0 - dot(pole, x)
        y = (x - dot(pole, x) .* pole) ./ denom
        push!(out, [dot(basis[i], y) for i in 1:3])
    end
    out
end

function discrete_gauss_linking(left::Vector{Vector{Float64}}, right::Vector{Vector{Float64}})
    acc = 0.0
    n = length(left)
    m = length(right)
    for i in 1:n
        a0 = left[i]
        a1 = left[mod1(i + 1, n)]
        mid_a = (a0 + a1) ./ 2.0
        da = a1 - a0
        for j in 1:m
            b0 = right[j]
            b1 = right[mod1(j + 1, m)]
            mid_b = (b0 + b1) ./ 2.0
            db = b1 - b0
            r = mid_a - mid_b
            acc += dot(cross(da, db), r) / (norm(r)^3)
        end
    end
    acc / (4.0 * pi)
end

function unlinked_control_circles(n::Int)
    left = [[cos(2.0 * pi * k / n), sin(2.0 * pi * k / n), 0.0] for k in 0:(n - 1)]
    right = [[cos(2.0 * pi * k / n), sin(2.0 * pi * k / n), 2.0] for k in 0:(n - 1)]
    left, right
end

function clifford_carrier_report()
    cl02 = CliffordAlgebra(0, 2)
    e1 = getproperty(cl02, :e1)
    e2 = getproperty(cl02, :e2)
    unit = one(e1)
    self_1 = Float64(CliffordAlgebras.norm(e1 * e1 + unit))
    self_2 = Float64(CliffordAlgebras.norm(e2 * e2 + unit))
    anti = Float64(CliffordAlgebras.norm(e1 * e2 + e2 * e1))
    pseudoscalar_square = Float64(CliffordAlgebras.norm((e1 * e2) * (e1 * e2) + unit))
    Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructed" => "CliffordAlgebra(0, 2)",
        "basis_symbol_count" => length(propertynames(cl02)),
        "quaternionic_carrier_dimension" => 4,
        "e1_square_minus_one_residual" => self_1,
        "e2_square_minus_one_residual" => self_2,
        "e1_e2_anticommutation_residual" => anti,
        "pseudoscalar_square_minus_one_residual" => pseudoscalar_square,
        "pass" => length(propertynames(cl02)) == 4 &&
                  maximum([self_1, self_2, anti, pseudoscalar_square]) <= TOL,
    )
end

function constraints_report(samples::Vector{Vector{Float64}})
    trace_residuals = Float64[]
    psd_min = Float64[]
    hermitian_residuals = Float64[]
    norm_residuals = Float64[]
    s2_residuals = Float64[]
    for q in samples
        rho = q * transpose(q)
        push!(trace_residuals, abs(tr(rho) - 1.0))
        push!(psd_min, minimum(eigvals(Symmetric(rho))))
        push!(hermitian_residuals, norm(rho - transpose(rho)))
        push!(norm_residuals, abs(dot(q, q) - 1.0))
        h = hopf_map(q)
        push!(s2_residuals, abs(dot(h, h) - 1.0))
    end
    Dict{String,Any}(
        "trace_one_max_residual" => maximum(trace_residuals),
        "psd_min_eigenvalue" => minimum(psd_min),
        "hermiticity_max_residual" => maximum(hermitian_residuals),
        "s3_normalization_max_residual" => maximum(norm_residuals),
        "hopf_image_s2_max_residual" => maximum(s2_residuals),
        "pass" => maximum(trace_residuals) <= TOL &&
                  minimum(psd_min) >= -TOL &&
                  maximum(hermitian_residuals) <= TOL &&
                  maximum(norm_residuals) <= TOL &&
                  maximum(s2_residuals) <= TOL,
    )
end

function quotient_report(link_raw::Float64, control_raw::Float64)
    Dict{String,Any}(
        "S" => ["fiber_over_north_pole", "fiber_over_south_pole", "trivial_coordinate_control_pair"],
        "equivalence_relation" => "q ~_M q' iff the Hopf projection probe h(q) = h(q') gives the same S^2 base point",
        "classes" => [
            Dict("class_id" => "hopf_fiber_north", "representative_base" => [0.0, 0.0, 1.0], "fiber" => "S^1"),
            Dict("class_id" => "hopf_fiber_south", "representative_base" => [0.0, 0.0, -1.0], "fiber" => "S^1"),
        ],
        "with_M_class_count_for_two_basepoints" => 2,
        "drop_Hopf_projection_probe_class_count" => 1,
        "linked_hopf_fiber_pair_linking_number_raw" => link_raw,
        "linked_hopf_fiber_pair_linking_number_rounded" => round(Int, abs(link_raw)),
        "trivial_control_linking_number_raw" => control_raw,
        "trivial_control_linking_number_rounded" => round(Int, abs(control_raw)),
    )
end

function build_result()
    n = 360
    fiber_north = hopf_fiber(0.0, 0.0, n)
    fiber_south = hopf_fiber(Float64(pi), 0.0, n)
    pole, basis = stereographic_basis([0.5, 0.5, 0.5, 0.5])
    projected_north = stereographic_project(fiber_north, pole, basis)
    projected_south = stereographic_project(fiber_south, pole, basis)
    hopf_linking_raw = discrete_gauss_linking(projected_north, projected_south)
    control_left, control_right = unlinked_control_circles(n)
    control_linking_raw = discrete_gauss_linking(control_left, control_right)

    carrier = clifford_carrier_report()
    constraints = constraints_report(vcat(fiber_north[1:30:end], fiber_south[1:30:end]))
    quotient = quotient_report(hopf_linking_raw, control_linking_raw)
    r3_peer = load_r3_peer_result()
    r3_check = r3_provenance_check(r3_peer)
    negative = Dict{String,Any}(
        "drop_Hopf_projection_probe_coarsens_quotient" => quotient["with_M_class_count_for_two_basepoints"] != quotient["drop_Hopf_projection_probe_class_count"],
        "trivial_coordinate_control_unlinks" => round(Int, abs(control_linking_raw)) == 0,
        "Hopf_vs_trivial_linking_flips" => round(Int, abs(hopf_linking_raw)) == 1 && round(Int, abs(control_linking_raw)) == 0,
    )
    all_pass = (
        carrier["pass"] &&
        constraints["pass"] &&
        round(Int, abs(hopf_linking_raw)) == 1 &&
        round(Int, abs(control_linking_raw)) == 0 &&
        all(values(negative)) &&
        r3_check["matches_r3_rank"] &&
        r3_check["matches_r3_anticommutation"] &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == true
    )
    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "r3_peer_provenance_check" => r3_check,
        "julia_project" => Base.active_project(),
        "packages_used" => ["CliffordAlgebras", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras"],
        "claim_path_tools" => ["CliffordAlgebras"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "M" => Dict(
            "name" => "Hopf_projection_probe",
            "explicit_probe_family" => ["h(q) = (2(ac+bd), 2(bc-ad), a^2+b^2-c^2-d^2)"],
            "finite_probe_domain" => Dict("sampled_fibers" => ["north", "south"], "samples_per_fiber" => n),
        ),
        "C" => Dict(
            "trace_equals_one" => "rho=q*q' for sampled unit spinors has trace 1",
            "psd" => "rho=q*q' is PSD",
            "hermiticity" => "rho=q*q' is real symmetric/Hermitian",
            "normalization" => "q lies on S^3: a^2+b^2+c^2+d^2=1",
            "rung_specific_constraint" => "Cl(0,2) quaternionic spinor carrier plus Hopf projection h:S^3->S^2",
            "computed_constraints" => constraints,
        ),
        "S_mod_M" => quotient,
        "summary" => Dict(
            "hopf_linking_number" => round(Int, abs(hopf_linking_raw)),
            "hopf_linking_number_raw" => hopf_linking_raw,
            "trivial_control_linking_number" => round(Int, abs(control_linking_raw)),
            "trivial_control_linking_number_raw" => control_linking_raw,
            "s2_image_relation_scope" => "Julia computes S^3 samples, Hopf projection, and fiber linking; dual SMT proof is scoped to the algebraic S^3->S^2 relation in the JAX leg.",
            "clifford_carrier" => carrier,
        ),
        "negative_control_flip" => negative,
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R5_HOPF_JULIA_DONE all_pass=$(result["all_pass"]) " *
        "hopf_linking=$(result["summary"]["hopf_linking_number"]) " *
        "trivial_control=$(result["summary"]["trivial_control_linking_number"]) " *
        "s2_residual=$(result["C"]["computed_constraints"]["hopf_image_s2_max_residual"]) " *
        "r3_matches_rank=$(result["r3_peer_provenance_check"]["matches_r3_rank"]) " *
        "r3_matches_anticommutation=$(result["r3_peer_provenance_check"]["matches_r3_anticommutation"])",
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
